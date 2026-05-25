"""
Génère automatiquement un ForensicReport + un projet EBIOS RM complet
(5 ateliers) depuis un rapport JSON MobSF.
Inspiré de EBIOS RM Pro v5 (Cyber-Autopsie).
"""
import json
from sqlalchemy.orm import Session

from models.report import ForensicReport
from models.ebios import (
    EbiosProject, EbiosAsset, EbiosFearEvent,
    EbiosRiskSource, EbiosScenario,
)

# ── Mapping permission dangereuse → (titre ER, impact CIA, gravité) ──────────
_PERM_MAP = {
    "READ_SMS":              ("Interception SMS",              "confidentialité", 4),
    "RECORD_AUDIO":          ("Écoute audio non consentie",    "confidentialité", 4),
    "CAMERA":                ("Capture vidéo non consentie",   "confidentialité", 4),
    "READ_CONTACTS":         ("Exfiltration contacts",         "confidentialité", 3),
    "ACCESS_FINE_LOCATION":  ("Géolocalisation précise",       "confidentialité", 3),
    "READ_CALL_LOG":         ("Accès historique appels",       "confidentialité", 3),
    "SEND_SMS":              ("Envoi SMS frauduleux",           "intégrité",       3),
    "READ_EXTERNAL_STORAGE": ("Accès fichiers utilisateur",    "confidentialité", 2),
    "WRITE_EXTERNAL_STORAGE":("Modification fichiers",         "intégrité",       2),
    "INTERNET":              ("Communication réseau cachée",   "confidentialité", 2),
    "RECEIVE_BOOT_COMPLETED":("Persistance au démarrage",      "disponibilité",   3),
    "GET_ACCOUNTS":          ("Énumération comptes utilisateur","confidentialité", 3),
    "USE_BIOMETRIC":         ("Accès données biométriques",    "confidentialité", 4),
    "READ_PHONE_STATE":      ("Identification IMEI/SIM",       "confidentialité", 2),
}

# ── Mapping finding critique → scénario opérationnel MITRE ATT&CK ──────────
_FINDING_TO_MITRE = {
    "hardcoded":    {"step": "Collecte credentials", "technique": "Hardcoded Credentials", "mitreId": "T1552"},
    "crypto":       {"step": "Chiffrement faible",   "technique": "Weak Cryptography",     "mitreId": "T1600"},
    "ssl":          {"step": "MitM possible",         "technique": "Adversary-in-the-Middle","mitreId": "T1557"},
    "webview":      {"step": "Injection JS WebView",  "technique": "Exploit Public App",    "mitreId": "T1190"},
    "debug":        {"step": "Debug actif",           "technique": "Software Discovery",    "mitreId": "T1518"},
    "root":         {"step": "Détection root bypass", "technique": "Exploitation for PE",   "mitreId": "T1068"},
    "backup":       {"step": "Extraction backup ADB", "technique": "Data from Local System","mitreId": "T1005"},
    "exported":     {"step": "Composant exposé",      "technique": "Exploit Public App",    "mitreId": "T1190"},
}

# ── Sources de risque EBIOS (Atelier 2) selon profil app ────────────────────
_RISK_SOURCES = [
    {
        "name":       "Cybercriminel organisé",
        "category":   "criminal",
        "motivation": "Lucratif — vol de données personnelles, revente sur darknet",
        "resources":  "importantes",
        "pertinence": 3,
    },
    {
        "name":       "Développeur malveillant / Supply chain",
        "category":   "insider",
        "motivation": "Insertion de SDK malveillant ou backdoor dans l'application",
        "resources":  "moyennes",
        "pertinence": 2,
    },
    {
        "name":       "Attaquant opportuniste",
        "category":   "activist",
        "motivation": "Exploitation de vulnérabilités publiques connues",
        "resources":  "faibles",
        "pertinence": 3,
    },
]


def _sev_map(level: str) -> str:
    return {"critical": "critical", "high": "high", "warning": "medium", "info": "low"}.get(level, "low")


def generate_forensic_report(
    scan_id: int,
    app_name: str,
    package_name: str,
    raw_json: str,
    db: Session,
    author_id: int | None = None,
) -> ForensicReport:
    """Parse le JSON MobSF → crée un ForensicReport complet en base."""
    data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json

    findings_raw = data.get("findings", {}) or {}
    perms_raw    = data.get("permissions", {}) or {}
    trackers_raw = data.get("trackers", {}) or {}
    trackers     = trackers_raw.get("trackers", []) if isinstance(trackers_raw, dict) else []
    score        = (data.get("appsec", {}) or {}).get("security_score")

    # ── Findings ──────────────────────────────────────────────────────────────
    findings = []

    for key, val in findings_raw.items():
        if not isinstance(val, dict):
            continue
        findings.append({
            "title":       key,
            "severity":    _sev_map(val.get("level", "info")),
            "description": val.get("description") or val.get("title") or key,
            "evidence":    val.get("cvss") or val.get("ref") or "",
        })

    for perm, val in perms_raw.items():
        if isinstance(val, dict) and val.get("status") == "dangerous":
            short = perm.split(".")[-1]
            title, _, _ = _PERM_MAP.get(short, (f"Permission dangereuse : {short}", "confidentialité", 2))
            findings.append({
                "title":       f"Permission : {short}",
                "severity":    "high",
                "description": val.get("description", title),
                "evidence":    "AndroidManifest.xml",
            })

    for t in trackers:
        findings.append({
            "title":       f"Tracker : {t.get('name', 'Inconnu')}",
            "severity":    "medium",
            "description": f"SDK tiers {t.get('name')} détecté — risque RGPD",
            "evidence":    t.get("url", ""),
        })

    # ── Recommandations ───────────────────────────────────────────────────────
    crit = sum(1 for f in findings if f["severity"] == "critical")
    high = sum(1 for f in findings if f["severity"] == "high")

    recs = []
    if crit:
        recs.append({"priority": "immediate",   "action": f"Corriger {crit} vulnérabilité(s) critique(s) avant tout déploiement", "owner": "Dev"})
    if high:
        recs.append({"priority": "short_term",  "action": f"Traiter {high} finding(s) élevé(s) sous 7 jours", "owner": "SecOps"})
    if trackers:
        recs.append({"priority": "short_term",  "action": f"Auditer {len(trackers)} tracker(s) — conformité RGPD", "owner": "DPO"})
    recs.append({"priority": "long_term", "action": "Intégrer MobSF dans la CI/CD (scan automatique à chaque release)", "owner": "DevSecOps"})

    # ── Score → niveau de risque ───────────────────────────────────────────
    if score is not None:
        risk = "CRITIQUE" if score < 40 else "ÉLEVÉ" if score < 60 else "MOYEN" if score < 80 else "FAIBLE"
    else:
        risk = "INDÉTERMINÉ"

    summary = (
        f"Analyse automatique MobSF — {app_name or package_name}\n"
        f"Score sécurité : {score}/100 — Risque global : {risk}\n"
        f"{len(findings)} finding(s) : {crit} critique(s), {high} élevé(s)\n"
        f"{len(trackers)} tracker(s) tiers — "
        f"{sum(1 for p,v in perms_raw.items() if isinstance(v,dict) and v.get('status')=='dangerous')} permission(s) dangereuse(s)"
    )

    report = ForensicReport(
        title=f"Rapport forensique — {app_name or package_name}",
        status="draft",
        executive_summary=summary,
        findings=json.dumps(findings),
        recommendations=json.dumps(recs),
        id_author=author_id,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def generate_ebios_project(
    scan_id: int,
    app_name: str,
    package_name: str,
    raw_json: str,
    db: Session,
    author_id: int | None = None,
) -> EbiosProject:
    """
    Génère un projet EBIOS RM complet (5 ateliers) depuis un scan MobSF.
    Atelier 1 : biens valorisés + événements redoutés
    Atelier 2 : sources de risque
    Atelier 3 & 4 : scénarios stratégiques + opérationnels (MITRE ATT&CK)
    Atelier 5 : mesures de sécurité (dans chaque scénario)
    """
    data = json.loads(raw_json) if isinstance(raw_json, str) else raw_json

    findings_raw = data.get("findings", {}) or {}
    perms_raw    = data.get("permissions", {}) or {}
    trackers_raw = data.get("trackers", {}) or {}
    trackers     = trackers_raw.get("trackers", []) if isinstance(trackers_raw, dict) else []
    score        = (data.get("appsec", {}) or {}).get("security_score")

    # ── Atelier 1 — Projet + Biens valorisés ─────────────────────────────────
    project = EbiosProject(
        name=f"EBIOS RM — {app_name or package_name} (scan #{scan_id})",
        scope=f"Application mobile {app_name} ({package_name})",
        context=(
            f"Analyse automatique issue du scan MobSF #{scan_id}. "
            f"Score sécurité : {score}/100. "
            f"Référentiel : ANSSI EBIOS RM 2018 + MITRE ATT&CK Mobile."
        ),
        status="in_progress",
        id_author=author_id,
    )
    db.add(project)
    db.flush()

    # Biens valorisés (Atelier 1 — BV)
    assets_map = {}
    bv_defs = [
        ("Données utilisateur",      "information", "Contacts, SMS, localisation, photos", 4),
        ("Application mobile",        "system",      f"APK {package_name}",                 3),
        ("Infrastructure backend",    "system",      "API et base de données distante",      3),
        ("Authentification",          "process",     "Mécanisme de login et sessions",       4),
    ]
    for name, typ, desc, crit in bv_defs:
        asset = EbiosAsset(
            id_project=project.id_project,
            name=name, type=typ, description=desc, critical_level=crit,
        )
        db.add(asset)
        db.flush()
        assets_map[name] = asset

    # Événements redoutés (Atelier 1 — ER) depuis permissions dangereuses
    fear_events_created = []
    processed_perms = set()

    for perm, val in perms_raw.items():
        if not (isinstance(val, dict) and val.get("status") == "dangerous"):
            continue
        short = perm.split(".")[-1]
        if short in processed_perms:
            continue
        processed_perms.add(short)

        title, impact_cia, gravity = _PERM_MAP.get(short, (f"Risque permission {short}", "confidentialité", 2))
        asset = assets_map.get("Données utilisateur")
        fe = EbiosFearEvent(
            id_project=project.id_project,
            id_asset=asset.id_asset if asset else None,
            impact=impact_cia,
            description=f"{title} via permission {short} : {val.get('description', '')}",
            gravity=gravity,
        )
        db.add(fe)
        db.flush()
        fear_events_created.append((fe, short))

    # ER depuis trackers
    if trackers:
        tracker_names = ", ".join(t.get("name", "?") for t in trackers[:4])
        fe_tracker = EbiosFearEvent(
            id_project=project.id_project,
            id_asset=assets_map["Données utilisateur"].id_asset,
            impact="confidentialité",
            description=f"Exfiltration données via SDK tiers : {tracker_names}",
            gravity=3,
        )
        db.add(fe_tracker)
        db.flush()
        fear_events_created.append((fe_tracker, "trackers"))

    # ── Atelier 2 — Sources de risque ─────────────────────────────────────────
    sources_created = []
    for src_def in _RISK_SOURCES:
        src = EbiosRiskSource(id_project=project.id_project, **src_def)
        db.add(src)
        db.flush()
        sources_created.append(src)

    # ── Ateliers 3 & 4 — Scénarios stratégiques + opérationnels ──────────────
    main_source = sources_created[0]  # Cybercriminel = source principale

    # Scénario stratégique par événement redouté
    for fe, perm_key in fear_events_created[:4]:  # max 4 scénarios
        title_er, impact_cia, gravity = _PERM_MAP.get(
            perm_key,
            (fe.description[:50] if fe.description else "Scénario", "confidentialité", 2)
        )
        strat = EbiosScenario(
            id_project=project.id_project,
            id_risk_source=main_source.id_source,
            id_fear_event=fe.id_event,
            type="strategic",
            title=f"[SR] {title_er}",
            description=(
                f"Source de risque '{main_source.name}' ciblant le bien '{fe.impact}' "
                f"via {perm_key}. Gravité : {fe.gravity}/4."
            ),
            attack_path=json.dumps([]),
            likelihood=2,
            gravity=fe.gravity,
            risk_level=2 * fe.gravity,
            treatment="reduce",
            measures=json.dumps([
                f"Supprimer la permission {perm_key} si non essentielle",
                "Implémenter le principe de moindre privilège",
                "Valider les permissions à l'exécution (Android 6+)",
            ]),
        )
        db.add(strat)

    # Scénarios opérationnels depuis findings critiques/élevés (Atelier 4 — MITRE)
    crit_findings = [
        (k, v) for k, v in findings_raw.items()
        if isinstance(v, dict) and v.get("level") in ("critical", "high")
    ]

    for key, val in crit_findings[:5]:  # max 5 scénarios opérationnels
        # Chercher une correspondance MITRE
        mitre_match = None
        key_lower = key.lower()
        for keyword, mitre in _FINDING_TO_MITRE.items():
            if keyword in key_lower:
                mitre_match = mitre
                break

        attack_path = [mitre_match] if mitre_match else [{
            "step": "Exploitation", "technique": key, "mitreId": "T1203"
        }]

        oper = EbiosScenario(
            id_project=project.id_project,
            id_risk_source=main_source.id_source,
            type="operational",
            title=f"[SO] {key[:80]}",
            description=val.get("description") or val.get("title") or key,
            attack_path=json.dumps(attack_path),
            likelihood=3 if val.get("level") == "critical" else 2,
            gravity=4 if val.get("level") == "critical" else 3,
            risk_level=12 if val.get("level") == "critical" else 6,
            treatment="reduce",
            measures=json.dumps([
                f"Corriger la vulnérabilité : {key}",
                "Mettre à jour les dépendances impactées",
                "Ajouter un test de régression sécurité dans la CI/CD",
            ]),
        )
        db.add(oper)

    db.commit()
    db.refresh(project)
    return project
