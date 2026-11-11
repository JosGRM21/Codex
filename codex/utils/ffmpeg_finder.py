"""Localizador robusto para los binarios de FFmpeg y FFprobe."""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple

def find_ffmpeg_binaries() -> Tuple[Optional[str], Optional[str]]:
    """
    Busca los ejecutables de ffmpeg y ffprobe en el sistema.
    Revisa PATH, variables de entorno de Windows y rutas estándar de WinGet / Scoop / Chocolatey.
    
    Retorna:
        Tuple[Optional[str], Optional[str]]: Rutas a (ffmpeg, ffprobe) o None si no se encuentran.
    """
    # 1. Probar shutil.which directamente
    ffmpeg_cmd = shutil.which("ffmpeg")
    ffprobe_cmd = shutil.which("ffprobe")
    if ffmpeg_cmd and ffprobe_cmd:
        return ffmpeg_cmd, ffprobe_cmd

    # 2. Rutas comunes en Windows
    candidate_dirs = []
    
    # WinGet packages
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        winget_dir = Path(local_app_data) / "Microsoft" / "WinGet" / "Packages"
        if winget_dir.exists():
            for p in winget_dir.glob("**/bin/ffmpeg.exe"):
                candidate_dirs.append(p.parent)

    # Chocolatey & Scoop
    program_data = os.environ.get("ProgramData")
    if program_data:
        candidate_dirs.append(Path(program_data) / "chocolatey" / "bin")
    user_profile = os.environ.get("USERPROFILE")
    if user_profile:
        candidate_dirs.append(Path(user_profile) / "scoop" / "shims")

    for c_dir in candidate_dirs:
        c_ffmpeg = c_dir / ("ffmpeg.exe" if os.name == "nt" else "ffmpeg")
        c_ffprobe = c_dir / ("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if c_ffmpeg.exists():
            ffmpeg_cmd = str(c_ffmpeg)
            ffprobe_cmd = str(c_ffprobe) if c_ffprobe.exists() else str(c_ffmpeg.with_name("ffprobe.exe"))
            return ffmpeg_cmd, ffprobe_cmd

    return ffmpeg_cmd, ffprobe_cmd

def require_ffmpeg() -> Tuple[str, str]:
    """Retorna las rutas a ffmpeg y ffprobe o lanza RuntimeError con instrucciones de instalación."""
    ffmpeg, ffprobe = find_ffmpeg_binaries()
    if not ffmpeg:
        raise RuntimeError(
            "No se encontró FFmpeg en el sistema. "
            "Por favor asegúrate de instalarlo con: 'winget install Gyan.FFmpeg.Essentials' "
            "o añadir su carpeta 'bin' al PATH del sistema."
        )
    return ffmpeg, ffprobe or ffmpeg
