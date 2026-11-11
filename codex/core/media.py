"""Módulo para análisis de medios y extracción óptima de audio."""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
from codex.utils.ffmpeg_finder import require_ffmpeg
from codex.utils.logger import logger
from codex.config import AudioConfig

AUDIO_EXTENSIONS = {".m4a", ".mp3", ".wav", ".opus", ".flac", ".ogg", ".aac"}
VIDEO_EXTENSIONS = {".mkv", ".mp4", ".mov", ".webm", ".avi", ".ts"}

class MediaInspector:
    """Inspecciona archivos de audio y video para obtener duración y metadatos."""

    @staticmethod
    def is_audio_only(file_path: Path) -> bool:
        """Determina rápidamente por extensión si el archivo es solo de audio."""
        return file_path.suffix.lower() in AUDIO_EXTENSIONS

    @staticmethod
    def get_video_info(media_path: Path) -> Dict[str, Any]:
        """Obtiene información de duración, resolución y pistas del medio."""
        _, ffprobe = require_ffmpeg()
        cmd = [
            ffprobe,
            "-v", "error",
            "-show_entries", "format=duration,size:stream=codec_type,width,height",
            "-of", "json",
            str(media_path),
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(res.stdout)
        
        duration = float(data.get("format", {}).get("duration", 0.0))
        size_bytes = int(data.get("format", {}).get("size", 0))
        
        width = 1920
        height = 1080
        has_audio = False
        has_video = False
        
        for stream in data.get("streams", []):
            codec_type = stream.get("codec_type")
            if codec_type == "video":
                has_video = True
                width = int(stream.get("width", 1920))
                height = int(stream.get("height", 1080))
            elif codec_type == "audio":
                has_audio = True

        return {
            "duration": duration,
            "size_bytes": size_bytes,
            "width": width,
            "height": height,
            "has_audio": has_audio,
            "has_video": has_video,
        }

def extract_audio(
    media_path: Path,
    output_audio_path: Path,
    audio_cfg: Optional[AudioConfig] = None
) -> Path:
    """
    Extrae o normaliza la pista de audio optimizada para agentes de IA / ASR.
    Configuración por defecto: 16kHz, mono, 32kbps (reducción masiva de peso conservando fonética).
    """
    ffmpeg, _ = require_ffmpeg()
    cfg = audio_cfg or AudioConfig()
    
    output_audio_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Construcción de comando ffmpeg
    cmd = [
        ffmpeg,
        "-y",                        # Sobrescribir si existe
        "-i", str(media_path),
        "-vn",                       # Descartar video si existe
        "-ac", str(cfg.channels),    # Mono
        "-ar", str(cfg.sample_rate), # 16000 Hz
    ]

    # Configuración de codec y bitrate
    if cfg.codec == "libopus":
        cmd.extend(["-c:a", "libopus", "-b:a", cfg.bitrate])
    elif cfg.codec == "mp3":
        cmd.extend(["-c:a", "libmp3lame", "-b:a", cfg.bitrate])
    elif cfg.codec == "aac":
        cmd.extend(["-c:a", "aac", "-b:a", cfg.bitrate])
    else:
        # Fallback a wav PCM sin pérdida
        cmd.extend(["-c:a", "pcm_s16le"])

    cmd.append(str(output_audio_path))

    logger.info(f"[cyan]Extrayendo y normalizando pista de audio a 16kHz mono...[/cyan] ({output_audio_path.name})")
    
    try:
        subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al procesar audio con ffmpeg: {e.stderr}")
        raise RuntimeError(f"Fallo al extraer audio del medio: {e.stderr}")

    orig_size_mb = media_path.stat().st_size / (1024 * 1024)
    audio_size_mb = output_audio_path.stat().st_size / (1024 * 1024)
    logger.info(
        f"[success]Audio preparado exitosamente:[/success] {orig_size_mb:.1f} MB (original) -> [accent]{audio_size_mb:.1f} MB[/accent] (optimizado)"
    )
    return output_audio_path
