"""
Scan Trivy sur un fichier APK décompressé.
Lance trivy fs sur le répertoire extrait de l'APK.
"""
import asyncio
import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path


async def scan_apk_with_trivy(apk_path: str) -> list[dict]:
    """
    Décompresse l'APK et lance trivy fs dessus.
    Retourne la liste des CVE trouvées (format Trivy Results[]).
    """
    # Vérifier que trivy est disponible
    if not shutil.which("trivy"):
        return []

    with tempfile.TemporaryDirectory() as tmpdir:
        # Décompresser l'APK (c'est un ZIP)
        try:
            with zipfile.ZipFile(apk_path, "r") as z:
                z.extractall(tmpdir)
        except Exception:
            return []

        # Lancer trivy fs
        try:
            result = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    "trivy", "fs",
                    "--format", "json",
                    "--severity", "CRITICAL,HIGH,MEDIUM,LOW",
                    "--quiet",
                    tmpdir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=120,
            )
            stdout, stderr = await asyncio.wait_for(result.communicate(), timeout=120)
            raw = json.loads(stdout.decode()) if stdout else {}
            return raw.get("Results", [])
        except Exception:
            return []


def parse_trivy_results(results: list[dict]) -> dict:
    """
    Parse les résultats Trivy et retourne un dict structuré.
    """
    crit = high = med = low = 0
    vulns = []

    for result in results:
        for v in result.get("Vulnerabilities") or []:
            sev = v.get("Severity", "UNKNOWN").upper()
            if sev == "CRITICAL": crit += 1
            elif sev == "HIGH":   high += 1
            elif sev == "MEDIUM": med  += 1
            elif sev == "LOW":    low  += 1

            # CVSS score
            cvss_score = None
            cvss_data = v.get("CVSS", {})
            for source in ["nvd", "redhat"]:
                if source in cvss_data:
                    cvss_score = cvss_data[source].get("V3Score") or cvss_data[source].get("V2Score")
                    if cvss_score:
                        break

            vulns.append({
                "id":                v.get("VulnerabilityID", ""),
                "package":           v.get("PkgName", ""),
                "installed_version": v.get("InstalledVersion", ""),
                "fixed_version":     v.get("FixedVersion", ""),
                "severity":          sev,
                "title":             v.get("Title", ""),
                "description":       (v.get("Description", "") or "")[:300],
                "cvss_score":        cvss_score,
                "references":        v.get("References", [])[:3],
                "exploit_available": bool(v.get("CVSS")),  # heuristique
                "published_date":    v.get("PublishedDate", "")[:10] if v.get("PublishedDate") else "",
            })

    # Tri par sévérité
    order = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4}
    vulns.sort(key=lambda x: order.get(x["severity"], 99))

    return {
        "critical": crit,
        "high":     high,
        "medium":   med,
        "low":      low,
        "total":    len(vulns),
        "vulns":    vulns,
        "available": True,
    }


def trivy_not_available() -> dict:
    return {
        "critical": 0, "high": 0, "medium": 0, "low": 0,
        "total": 0, "vulns": [], "available": False,
    }