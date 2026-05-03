"""
Service de téléchargement APK via APKPure.
"""
import asyncio
import re
import tempfile
from pathlib import Path


def _extract_package_name(url: str) -> str:
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
    raise ValueError("URL non reconnue - Play Store ou App Store uniquement")


def extract_package_from_url(url: str) -> str:
    return _extract_package_name(url)


async def download_apk_from_playstore(url: str) -> tuple[bytes, str]:
    package_name = _extract_package_name(url)

    with tempfile.TemporaryDirectory() as tmpdir:
        proc = await asyncio.create_subprocess_exec(
            "apkeep",
            "-a", package_name,
            "-d", "apk-pure",
            tmpdir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)

        apk_files = list(Path(tmpdir).glob("**/*.apk"))
        if not apk_files:
            raise RuntimeError(
                f"Aucun APK trouve pour {package_name}. "
                f"stdout={stdout.decode()[:200]} stderr={stderr.decode()[:200]}"
            )

        content = apk_files[0].read_bytes()
        return content, f"{package_name}.apk"