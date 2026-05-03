"""
Service de telechargement APK depuis le Play Store.
Tente plusieurs sources : APKPure, F-Droid.
Si toutes echouent, retourne une erreur claire invitant a uploader l'APK manuellement.
"""
import asyncio
import re
import tempfile
from pathlib import Path


# ── Extraction du package name ────────────────────────────────────────────

def _extract_package_name(url: str) -> str:
    """Extrait le package name depuis une URL Play Store ou App Store."""
    if "play.google.com" in url:
        match = re.search(r"id=([a-zA-Z0-9._]+)", url)
        if not match:
            raise ValueError(f"URL Play Store invalide : {url}")
        return match.group(1)
    elif "apps.apple.com" in url:
        match = re.search(r"/id(\d+)", url)
        if match:
            return f"apple_{match.group(1)}"
        raise ValueError("URL App Store invalide")
    # Accepte aussi un package name direct (ex: com.example.app)
    if re.match(r"^[a-zA-Z][a-zA-Z0-9._]+$", url):
        return url
    raise ValueError(
        "URL non reconnue. Formats acceptes : "
        "play.google.com, apps.apple.com, ou package name direct (ex: com.example.app)"
    )


def extract_package_from_url(url: str) -> str:
    """API publique — retourne le package name depuis une URL ou package name direct."""
    return _extract_package_name(url)


# ── Telechargement via apkeep ─────────────────────────────────────────────

async def _try_apkeep(package_name: str, source: str, tmpdir: str) -> list[Path]:
    """Lance apkeep avec la source donnee. Retourne la liste des APK telecharges."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "apkeep",
            "-a", package_name,
            "-d", source,
            tmpdir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
    except asyncio.TimeoutError:
        return []
    except FileNotFoundError:
        raise RuntimeError("apkeep non installe sur le serveur")

    return list(Path(tmpdir).glob("**/*.apk"))


async def download_apk_from_playstore(url: str) -> tuple[bytes, str]:
    """
    Tente de telecharger un APK depuis plusieurs sources.
    Retourne (contenu_bytes, nom_fichier).

    Sources essayees dans l'ordre :
    1. APKPure via apkeep
    2. F-Droid via apkeep (pour les apps open-source)

    Si aucune source ne fonctionne, leve une RuntimeError explicite.
    """
    package_name = _extract_package_name(url)

    # Sources a essayer dans l'ordre
    sources = ["apk-pure", "f-droid"]

    with tempfile.TemporaryDirectory() as tmpdir:
        last_error = None

        for source in sources:
            try:
                apk_files = await _try_apkeep(package_name, source, tmpdir)
                if apk_files:
                    content = apk_files[0].read_bytes()
                    filename = f"{package_name}.apk"
                    return content, filename
            except RuntimeError as e:
                # apkeep non installe — erreur critique, on remonte directement
                raise
            except Exception as e:
                last_error = str(e)
                continue

        # Aucune source n'a fonctionne
        raise RuntimeError(
            f"Impossible de telecharger automatiquement '{package_name}'. "
            f"APKPure est protege par Cloudflare et F-Droid ne contient "
            f"que les apps open-source. "
            f"Solution : telechargez l'APK manuellement depuis "
            f"https://apkpure.com/search?q={package_name} "
            f"et uploadez-le via le formulaire APK ci-dessus. "
            f"Erreur technique : {last_error or 'aucun APK trouve'}"
        )