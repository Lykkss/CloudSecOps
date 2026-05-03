"""
Service de téléchargement APK depuis le Play Store.
Utilise apkeep (outil Rust) pour télécharger les APK sans compte Google.
"""
import asyncio
import os
import re
import shutil
import tempfile
from pathlib import Path


def _extract_package_name(url: str) -> str:
    """Extrait le package name depuis une URL Play Store."""
    match = re.search(r"id=([a-zA-Z0-9._]+)", url)
    if not match:
        raise ValueError(f"URL Play Store invalide : {url}")
    return match.group(1)


def _is_apkeep_installed() -> bool:
    return shutil.which("apkeep") is not None


async def download_apk_from_playstore(url: str) -> tuple[bytes, str]:
    """
    Télécharge un APK depuis le Play Store.
    Retourne (contenu_bytes, nom_fichier).
    """
    package_name = _extract_package_name(url)

    if not _is_apkeep_installed():
        raise RuntimeError("apkeep non installé — lancer: cargo install apkeep")

    with tempfile.TemporaryDirectory() as tmpdir:
        proc = await asyncio.create_subprocess_exec(
            "apkeep",
            "-a", package_name,
            "-d", "google-play",
            tmpdir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"apkeep erreur : {stderr.decode()}")

        apk_files = list(Path(tmpdir).glob("**/*.apk"))
        if not apk_files:
            raise RuntimeError(f"Aucun APK trouvé pour {package_name}")

        apk_path = apk_files[0]
        content = apk_path.read_bytes()
        filename = f"{package_name}.apk"

        return content, filename


def extract_package_from_url(url: str) -> str:
    """Retourne le package name depuis une URL Play Store ou App Store."""
    if "play.google.com" in url:
        return _extract_package_name(url)
    elif "apps.apple.com" in url:
        match = re.search(r"/id(\d+)", url)
        if match:
            return f"apple_{match.group(1)}"
        raise ValueError("URL App Store invalide")
    raise ValueError("URL non reconnue — Play Store ou App Store uniquement")