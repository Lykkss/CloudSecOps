"""
Pipeline complet : MobSF → Trivy APK → Ollama → EBIOS RM → PDF
"""
import json
import os
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session

import httpx
from core.config import settings
from models.mobile_scan import MobileScan
from models.ebios import EbiosProject, EbiosAsset, EbiosFearEvent, EbiosRiskSource, EbiosScenario

_PERM_EBIOS = {
    "READ_SMS":               ("Interception SMS",               "confidentialité", 4, "T1636.004"),
    "RECORD_AUDIO":           ("Écoute audio non consentie",     "confidentialité", 4, "T1429"),
    "CAMERA":                 ("Capture vidéo non consentie",    "confidentialité", 4, "T1512"),
    "READ_CONTACTS":          ("Exfiltration contacts",          "confidentialité", 3, "T1636.003"),
    "ACCESS_FINE_LOCATION":   ("Géolocalisation précise",        "confidentialité", 3, "T1430"),
    "READ_CALL_LOG":          ("Accès historique appels",        "confidentialité", 3, "T1636.002"),
    "SEND_SMS":               ("Envoi SMS frauduleux",           "intégrité",       3, "T1582"),
    "READ_EXTERNAL_STORAGE":  ("Accès fichiers utilisateur",     "confidentialité", 2, "T1533"),
    "WRITE_EXTERNAL_STORAGE": ("Modification fichiers",          "intégrité",       2, "T1641"),
    "INTERNET":               ("Communication réseau cachée",    "confidentialité", 2, "T1437"),
    "RECEIVE_BOOT_COMPLETED": ("Persistance au démarrage",       "disponibilité",   3, "T1402"),
    "GET_ACCOUNTS":           ("Énumération comptes",            "confidentialité", 3, "T1636.001"),
    "USE_BIOMETRIC":          ("Accès données biométriques",     "confidentialité", 4, "T1517"),
    "READ_PHONE_STATE":       ("Identification IMEI/SIM",        "confidentialité", 2, "T1420"),
}

_FINDING_MITRE = {
    "hardcoded": ("Credentials en dur",       "T1552", 4, 3),
    "crypto":    ("Chiffrement faible",        "T1600", 3, 2),
    "ssl":       ("Validation SSL désactivée", "T1557", 3, 3),
    "webview":   ("WebView injection JS",      "T1190", 4, 3),
    "debug":     ("Mode debug actif",          "T1418", 2, 2),
    "root":      ("Détection root bypassable", "T1068", 3, 2),
    "backup":    ("Backup ADB activé",         "T1005", 2, 2),
    "exported":  ("Composant Android exposé",  "T1190", 3, 3),
}

_RISK_SOURCES = [
    {"name": "Cybercriminel organisé",  "category": "criminal", "motivation": "Vol de données personnelles, fraude financière", "resources": "importantes", "pertinence": 4},
    {"name": "Développeur malveillant", "category": "insider",  "motivation": "Backdoor intentionnel, SDK malveillant",         "resources": "moyennes",    "pertinence": 2},
    {"name": "Attaquant opportuniste",  "category": "activist", "motivation": "Exploitation de vulnérabilités CVE publiées",    "resources": "faibles",     "pertinence": 3},
]


def _parse_raw(raw_json):
    if isinstance(raw_json, str):
        try: return json.loads(raw_json)
        except: return {}
    return raw_json or {}


async def _ask_ollama(prompt: str, context: str = "") -> str:
    full = f"{context}\n\n{prompt}" if context else prompt
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(
                f"{settings.OLLAMA_URL}/api/generate",
                json={"model": settings.OLLAMA_MODEL, "prompt": full, "stream": False},
            )
            r.raise_for_status()
            return r.json().get("response", "")
    except:
        return ""


async def _run_trivy_apk(apk_path: str) -> dict:
    import shutil, tempfile, zipfile
    empty = {"available": False, "critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0, "vulns": []}
    if not shutil.which("trivy"):
        return empty
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(apk_path, "r") as z:
                z.extractall(tmpdir)
            proc = await asyncio.create_subprocess_exec(
                "trivy", "fs", "--format", "json",
                "--severity", "CRITICAL,HIGH,MEDIUM,LOW", "--quiet", tmpdir,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=180)
            results = (json.loads(stdout.decode()) if stdout else {}).get("Results", [])
            crit = high = med = low = 0
            vulns = []
            order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
            for result in results:
                for v in result.get("Vulnerabilities") or []:
                    sev = v.get("Severity", "UNKNOWN").upper()
                    if sev == "CRITICAL": crit += 1
                    elif sev == "HIGH":   high += 1
                    elif sev == "MEDIUM": med  += 1
                    elif sev == "LOW":    low  += 1
                    cvss_score = None
                    for src in ["nvd", "redhat", "ghsa"]:
                        d = (v.get("CVSS") or {}).get(src, {})
                        cvss_score = d.get("V3Score") or d.get("V2Score")
                        if cvss_score: break
                    vulns.append({
                        "id": v.get("VulnerabilityID", ""),
                        "package": v.get("PkgName", ""),
                        "installed_version": v.get("InstalledVersion", ""),
                        "fixed_version": v.get("FixedVersion", ""),
                        "severity": sev,
                        "title": v.get("Title", ""),
                        "description": (v.get("Description") or "")[:250],
                        "cvss_score": cvss_score,
                        "references": (v.get("References") or [])[:2],
                        "exploit_available": bool(cvss_score and float(cvss_score) >= 7.0),
                        "published_date": (v.get("PublishedDate") or "")[:10],
                    })
            vulns.sort(key=lambda x: order.get(x["severity"], 99))
            return {"available": True, "critical": crit, "high": high, "medium": med, "low": low, "total": len(vulns), "vulns": vulns[:50]}
    except Exception as e:
        return {**empty, "error": str(e)}


async def build_full_mobile_report(
    scan: MobileScan,
    context_user: str,
    objectifs: str,
    perimetre: str,
    db: Session,
    author_id: int | None = None,
) -> dict:
    raw = _parse_raw(scan.raw_json)
    findings_raw = raw.get("findings", {}) or {}
    score = (raw.get("appsec", {}) or {}).get("security_score") or scan.security_score
    dangerous_perms = json.loads(scan.dangerous_perms) if scan.dangerous_perms else []
    trackers_list   = json.loads(scan.trackers) if scan.trackers else []

    crit = high = warn = info = 0
    findings_enriched = []
    for key, val in findings_raw.items():
        if not isinstance(val, dict): continue
        lvl = val.get("level", "info")
        if lvl == "critical": crit += 1
        elif lvl == "high":   high += 1
        elif lvl == "warning":warn += 1
        else:                 info += 1
        mitre_id = next((m for kw, (_, m, _, _) in _FINDING_MITRE.items() if kw in key.lower()), "")
        findings_enriched.append({
            "title": key, "severity": lvl,
            "description": val.get("description") or key,
            "cvss": val.get("cvss", ""), "ref": val.get("ref", ""), "mitre": mitre_id,
        })

    # Trivy scan APK
    apk_path = None
    uploads_dir = os.path.join(os.path.dirname(__file__), "..", "uploads")
    if scan.file_name and os.path.isdir(uploads_dir):
        candidate = os.path.join(uploads_dir, scan.file_name)
        if os.path.exists(candidate):
            apk_path = candidate
    trivy = await _run_trivy_apk(apk_path) if apk_path else {"available": False, "critical": 0, "high": 0, "medium": 0, "low": 0, "total": 0, "vulns": []}

    total_crit = crit + trivy.get("critical", 0)
    total_high = high + trivy.get("high", 0)

    if score is not None:
        if score < 30 or total_crit > 5:   verdict = ("DANGEREUSE",   "L'application présente des risques critiques. Utilisation fortement déconseillée.", "#c0392b")
        elif score < 50 or total_crit > 0:  verdict = ("RISQUÉE",      "Risques significatifs nécessitant corrections urgentes.", "#d68910")
        elif score < 70 or total_high > 3:  verdict = ("MODÉRÉE",      "Risques modérés. Améliorations recommandées.", "#f39c12")
        else:                                verdict = ("SÛRE",         "Niveau de sécurité satisfaisant.", "#1e8449")
    else:
        verdict = ("INDÉTERMINÉE", "Analyse incomplète.", "#666")

    ollama_context = (
        f"App: {scan.app_name} ({scan.package_name}) v{scan.version} | Score MobSF: {score}/100\n"
        f"MobSF: {crit}C {high}H {warn}W | Trivy CVE: {trivy['critical']}C {trivy['high']}H total={trivy['total']}\n"
        f"Permissions dangereuses: {len(dangerous_perms)} | Trackers: {len(trackers_list)}\n"
        f"Contexte: {context_user} | Périmètre: {perimetre} | Objectifs: {objectifs}\n"
        f"Top findings: {', '.join(list(findings_raw.keys())[:6])}\n"
        f"Top CVE: {', '.join([v['id'] for v in trivy['vulns'][:4]])}"
    )

    ollama_forensic, ollama_recommendations = await asyncio.gather(
        _ask_ollama(
            "Rédige une analyse forensique professionnelle en 4 paragraphes : "
            "1) Synthèse risque global (MobSF + Trivy CVE), "
            "2) Findings critiques et permissions — impact concret, "
            "3) Vecteurs d'attaque MITRE ATT&CK Mobile, "
            "4) Verdict final et conditions d'utilisation acceptables. Français, professionnel.",
            ollama_context
        ),
        _ask_ollama(
            "Génère 6 recommandations priorisées. Format: PRIORITÉ | ACTION | RESPONSABLE | DÉLAI\n"
            "Priorités: CRITIQUE, ÉLEVÉE, MOYENNE, FAIBLE. Français uniquement.",
            ollama_context
        ),
    )

    # EBIOS RM
    project = EbiosProject(
        name=f"EBIOS RM — {scan.app_name or scan.package_name} (#{scan.id_scan})",
        scope=perimetre or f"Application {scan.app_name} ({scan.package_name})",
        context=context_user or f"Analyse sécurité mobile #{scan.id_scan}",
        status="in_progress", id_author=author_id,
    )
    db.add(project); db.flush()

    assets_db = []
    for name, typ, desc, cl in [
        ("Données utilisateur", "information", "Contacts, SMS, localisation, photos", 4),
        (f"App {scan.app_name}", "system", f"APK {scan.package_name} v{scan.version}", 3),
        ("Infrastructure backend", "system", "API et base de données distante", 3),
        ("Authentification", "process", "Login, sessions, tokens", 4),
    ]:
        a = EbiosAsset(id_project=project.id_project, name=name, type=typ, description=desc, critical_level=cl)
        db.add(a); db.flush(); assets_db.append(a)

    fear_events_db = []
    processed = set()
    for perm_obj in dangerous_perms[:5]:
        perm = perm_obj.get("permission", "") if isinstance(perm_obj, dict) else str(perm_obj)
        short = perm.split(".")[-1]
        if short in processed: continue
        processed.add(short)
        title, impact, gravity, mitre = _PERM_EBIOS.get(short, (f"Risque {short}", "confidentialité", 2, ""))
        fe = EbiosFearEvent(id_project=project.id_project, id_asset=assets_db[0].id_asset,
                            impact=impact, description=f"{title} via {short}", gravity=gravity)
        db.add(fe); db.flush(); fear_events_db.append((fe, short, mitre))

    if trackers_list:
        fe_t = EbiosFearEvent(id_project=project.id_project, id_asset=assets_db[0].id_asset,
                              impact="confidentialité", description=f"Exfiltration via {len(trackers_list)} SDK tiers (RGPD)", gravity=3)
        db.add(fe_t); db.flush(); fear_events_db.append((fe_t, "trackers", "T1437"))

    sources_db = []
    for src in _RISK_SOURCES:
        s = EbiosRiskSource(id_project=project.id_project, **src)
        db.add(s); db.flush(); sources_db.append(s)

    main_src = sources_db[0]
    scenarios_db = []

    # Atelier 3 — stratégiques depuis permissions
    for fe, perm_key, mitre_id in fear_events_db[:4]:
        t, _, g, _ = _PERM_EBIOS.get(perm_key, (fe.description[:50], "confidentialité", 2, ""))
        sc = EbiosScenario(id_project=project.id_project, id_risk_source=main_src.id_source,
                           id_fear_event=fe.id_event, type="strategic",
                           title=f"[SR] {t}", description=f"Exploitation {perm_key} — gravité {fe.gravity}/4",
                           attack_path=json.dumps([{"step": "Permission abuse", "technique": perm_key, "mitreId": mitre_id}]),
                           likelihood=3, gravity=fe.gravity, risk_level=3*fe.gravity, treatment="reduce",
                           measures=json.dumps([f"Supprimer {perm_key} si non essentielle", "Moindre privilège", "Permission runtime Android 6+"]))
        db.add(sc); db.flush(); scenarios_db.append(sc)

    # Atelier 4 — opérationnels depuis MobSF findings
    for key, val in [(k, v) for k, v in findings_raw.items() if isinstance(v, dict) and v.get("level") in ("critical", "high")][:3]:
        mid, g, l = next(((m, gv, lk) for kw, (_, m, lk, gv) in _FINDING_MITRE.items() if kw in key.lower()), ("T1203", 3, 2))
        sc = EbiosScenario(id_project=project.id_project, id_risk_source=main_src.id_source, type="operational",
                           title=f"[SO-MobSF] {key[:60]}", description=val.get("description") or key,
                           attack_path=json.dumps([{"step": "Exploitation", "technique": key, "mitreId": mid}]),
                           likelihood=l, gravity=g, risk_level=l*g, treatment="reduce",
                           measures=json.dumps([f"Corriger: {key}", "Tests régression CI/CD"]))
        db.add(sc); db.flush(); scenarios_db.append(sc)

    # Atelier 4 — opérationnels depuis CVE Trivy
    for vuln in trivy.get("vulns", [])[:4]:
        sev = vuln["severity"]
        g = 4 if sev == "CRITICAL" else 3 if sev == "HIGH" else 2
        l = 3 if vuln.get("exploit_available") else 2
        sc = EbiosScenario(id_project=project.id_project, id_risk_source=sources_db[2].id_source, type="operational",
                           title=f"[SO-CVE] {vuln['id']} — {vuln['package']}",
                           description=f"CVE {vuln['id']} ({sev}) dans {vuln['package']} v{vuln['installed_version']}. {vuln['title']}",
                           attack_path=json.dumps([{"step": "Exploitation CVE", "technique": vuln["id"], "mitreId": "T1203",
                                                     "cvss": str(vuln.get("cvss_score", "")), "exploit": "Oui" if vuln.get("exploit_available") else "Non confirmé"}]),
                           likelihood=l, gravity=g, risk_level=l*g, treatment="reduce",
                           measures=json.dumps([f"Mettre à jour {vuln['package']} → {vuln.get('fixed_version', 'dernière version')}",
                                                "Scanner les dépendances avec Trivy", "Intégrer Trivy CI/CD mobile"]))
        db.add(sc); db.flush(); scenarios_db.append(sc)

    db.commit()

    risk_matrix = {}
    for sc in scenarios_db:
        k = f"{sc.likelihood}-{sc.gravity}"
        risk_matrix[k] = risk_matrix.get(k, 0) + 1

    recs = []
    if total_crit > 0: recs.append({"priority": "CRITIQUE", "action": f"Corriger {total_crit} vulnérabilité(s) critique(s)", "owner": "Dev", "delai": "< 24h"})
    if total_high > 0: recs.append({"priority": "ÉLEVÉE",   "action": f"Traiter {total_high} vulnérabilité(s) élevée(s)",   "owner": "SecOps", "delai": "< 7j"})
    if dangerous_perms: recs.append({"priority": "ÉLEVÉE",  "action": f"Auditer {len(dangerous_perms)} permission(s) dangereuse(s)", "owner": "Dev mobile", "delai": "< 7j"})
    if trackers_list:   recs.append({"priority": "MOYENNE", "action": f"Évaluer {len(trackers_list)} tracker(s) — RGPD", "owner": "DPO", "delai": "< 30j"})
    if trivy["total"] > 0: recs.append({"priority": "MOYENNE", "action": f"Mettre à jour {trivy['total']} dépendances vulnérables", "owner": "Dev", "delai": "< 30j"})
    recs.append({"priority": "FAIBLE", "action": "Intégrer MobSF + Trivy dans CI/CD mobile", "owner": "DevSecOps", "delai": "< 3 mois"})

    ollama_recs_parsed = []
    for line in (ollama_recommendations or "").strip().split("\n"):
        if "|" in line:
            p = [x.strip() for x in line.split("|")]
            if len(p) >= 2 and p[0]: ollama_recs_parsed.append({"priority": p[0], "action": p[1], "owner": p[2] if len(p)>2 else "—", "delai": p[3] if len(p)>3 else "—"})

    return {
        "ref": f"CSO-MOB-{scan.id_scan}-EBIOS", "date": datetime.now().strftime("%Y-%m-%d"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "context_user": context_user, "objectifs": objectifs, "perimetre": perimetre,
        "scan": {"id_scan": scan.id_scan, "app_name": scan.app_name or scan.file_name,
                 "package_name": scan.package_name, "version": scan.version,
                 "platform": scan.platform or "android",
                 "scanned_at": scan.scanned_at.strftime("%Y-%m-%d %H:%M:%S") if scan.scanned_at else "",
                 "security_score": score, "file_name": scan.file_name, "mobsf_hash": scan.mobsf_hash},
        "counts": {"critical": crit, "high": high, "warning": warn, "info": info},
        "trivy": trivy,
        "verdict": verdict[0], "verdict_desc": verdict[1], "verdict_color": verdict[2],
        "findings": findings_enriched, "dangerous_perms": dangerous_perms, "trackers": trackers_list,
        "project": {"id_project": project.id_project, "name": project.name, "scope": project.scope, "context": project.context},
        "assets":      [{"name": a.name, "type": a.type, "description": a.description, "critical_level": a.critical_level} for a in assets_db],
        "fear_events": [{"description": fe.description, "impact": fe.impact, "gravity": fe.gravity} for fe, _, _ in fear_events_db],
        "risk_sources":[{"name": s.name, "category": s.category, "motivation": s.motivation, "resources": s.resources, "pertinence": s.pertinence} for s in sources_db],
        "scenarios":   [{"title": sc.title, "type": sc.type, "description": sc.description, "likelihood": sc.likelihood, "gravity": sc.gravity, "risk_level": sc.risk_level, "treatment": sc.treatment, "attack_path": json.loads(sc.attack_path) if sc.attack_path else []} for sc in scenarios_db],
        "risk_matrix": risk_matrix,
        "ollama_forensic": ollama_forensic, "ollama_recs_parsed": ollama_recs_parsed, "ollama_available": bool(ollama_forensic),
        "recommendations": recs,
    }