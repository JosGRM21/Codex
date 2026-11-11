"""Módulo de visión por computadora para detección y extracción de diapositivas en clases."""

import math
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
from PIL import Image

from codex.utils.ffmpeg_finder import require_ffmpeg
from codex.utils.logger import logger
from codex.utils.time_format import seconds_to_hhmmss, seconds_to_tag
from codex.config import VisionConfig
from codex.core.media import MediaInspector

@dataclass
class SlideFrame:
    """Representa una diapositiva extraída con su marca de tiempo."""
    timestamp_seconds: float
    time_str: str          # Formato HH:MM:SS
    file_path: Path        # Ruta local de la imagen guardada
    tag: str               # Formato HHMMSS para nombres

def compute_image_difference(img1: Image.Image, img2: Image.Image) -> float:
    """
    Calcula la diferencia perceptual normalizada (0.0 a 1.0) entre dos imágenes.
    Redimensiona a 64x64 en escala de grises para máxima velocidad e invarianza a ruido menor.
    """
    # 64x64 escala de grises
    i1 = img1.convert("L").resize((64, 64), Image.Resampling.BILINEAR)
    i2 = img2.convert("L").resize((64, 64), Image.Resampling.BILINEAR)
    
    # Usar tobytes para compatibilidad limpia y sin advertencias en Pillow
    pixels1 = list(i1.tobytes())
    pixels2 = list(i2.tobytes())
    
    total_diff = sum(abs(p1 - p2) for p1, p2 in zip(pixels1, pixels2))
    max_possible_diff = len(pixels1) * 255.0
    return total_diff / max_possible_diff

class SlideExtractor:
    """Extrae y deduplica capturas de diapositivas de una grabación de clase."""

    def __init__(self, vision_config: Optional[VisionConfig] = None):
        self.cfg = vision_config or VisionConfig()

    def extract_slides(
        self,
        video_path: Path,
        output_dir: Path,
        sampling_interval_seconds: float = 10.0
    ) -> List[SlideFrame]:
        """
        Extrae capturas representativas de la clase descartando frames repetidos.
        
        Pasos:
        1. Extrae frames a intervalo regular (ej. cada 10s) en una carpeta temporal.
        2. Aplica deduplicación perceptual: conserva solo cuando la imagen difiere significativamente
           de la diapositiva anterior (cambio de slide en Google Meet).
        3. Renombra y almacena las diapositivas finales con su timestamp: slide_HHMMSS.png.
        """
        ffmpeg, _ = require_ffmpeg()
        output_dir.mkdir(parents=True, exist_ok=True)

        if MediaInspector.is_audio_only(video_path):
            logger.info("El archivo indicado es solo de audio. Omitiendo extracción de diapositivas.")
            return []

        temp_dir = output_dir / "_candidates_temp"
        temp_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            f"[cyan]Analizando cambios visuales y diapositivas cada {sampling_interval_seconds}s...[/cyan]"
        )

        # 1. Extracción con FFmpeg: fps = 1 / sampling_interval
        fps_expr = f"1/{sampling_interval_seconds}"
        pattern = str(temp_dir / "candidate_%05d.png")
        
        cmd = [
            ffmpeg,
            "-y",
            "-i", str(video_path),
            "-vf", f"fps={fps_expr},scale='min({self.cfg.max_width},iw)':-2",
            "-q:v", "3",
            pattern
        ]

        try:
            subprocess.run(cmd, capture_output=True, text=True, check=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error al muestrear frames con ffmpeg: {e.stderr}")
            raise RuntimeError(f"Fallo en muestreo de frames: {e.stderr}")

        candidate_files = sorted(temp_dir.glob("candidate_*.png"))
        if not candidate_files:
            logger.warning("No se extrajeron candidatos visuales del video.")
            return []

        logger.info(f"Procesando {len(candidate_files)} frames candidatos para deduplicar...")

        # 2. Deduplicación por diferencia perceptual
        slides: List[SlideFrame] = []
        last_kept_img: Optional[Image.Image] = None
        last_kept_time: float = -999.0

        for idx, frame_file in enumerate(candidate_files):
            # El tiempo correspondiente al frame candidato
            timestamp_sec = idx * sampling_interval_seconds
            
            try:
                with Image.open(frame_file) as current_img:
                    current_img.load()
                    
                    if last_kept_img is None:
                        # La primera diapositiva de la clase siempre se guarda
                        is_new_slide = True
                    else:
                        diff = compute_image_difference(last_kept_img, current_img)
                        time_since_last = timestamp_sec - last_kept_time
                        
                        # Consideramos nueva diapositiva si superó el umbral y transcurrió el intervalo mínimo
                        is_new_slide = (
                            diff >= self.cfg.diff_threshold and 
                            time_since_last >= self.cfg.min_interval_seconds
                        )

                    if is_new_slide:
                        tag = seconds_to_tag(timestamp_sec)
                        time_str = seconds_to_hhmmss(timestamp_sec)
                        final_filename = f"slide_{tag}.png"
                        final_path = output_dir / final_filename

                        # Guardar copia limpia en el directorio final
                        current_img.save(final_path, format="PNG", optimize=True)
                        
                        slides.append(SlideFrame(
                            timestamp_seconds=timestamp_sec,
                            time_str=time_str,
                            file_path=final_path,
                            tag=tag
                        ))

                        last_kept_img = current_img.copy()
                        last_kept_time = timestamp_sec

            except Exception as ex:
                logger.debug(f"Error procesando frame {frame_file.name}: {ex}")

        # Limpiar carpeta temporal de candidatos
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

        logger.info(
            f"[success]Detección de diapositivas completada:[/success] [accent]{len(slides)} diapositivas clave extraídas[/accent]"
        )
        return slides
