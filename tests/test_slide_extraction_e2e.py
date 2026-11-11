"""Prueba de extremo a extremo de detección de cambios de diapositiva en video."""

import subprocess
from pathlib import Path
from codex.core.vision import SlideExtractor
from codex.config import VisionConfig
from codex.utils.ffmpeg_finder import require_ffmpeg

def test_slide_extractor_detects_scene_changes(tmp_path: Path):
    ffmpeg, _ = require_ffmpeg()
    video_path = tmp_path / "slides_test.mp4"
    slides_output = tmp_path / "extracted_slides"

    # Generar un video sintético con 3 colores/escenas distintas de 4 segundos cada una:
    # 0s a 4s: fondo rojo
    # 4s a 8s: fondo azul
    # 8s a 12s: fondo verde
    filter_complex = (
        "color=c=red:s=640x480:d=4[v0];"
        "color=c=blue:s=640x480:d=4[v1];"
        "color=c=green:s=640x480:d=4[v2];"
        "[v0][v1][v2]concat=n=3:v=1:a=0[outv]"
    )

    cmd = [
        ffmpeg, "-y",
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        str(video_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    assert video_path.exists()

    # Muestrear cada 2 segundos con umbral de diferencia
    cfg = VisionConfig(diff_threshold=0.1, min_interval_seconds=1.0)
    extractor = SlideExtractor(cfg)
    slides = extractor.extract_slides(video_path, slides_output, sampling_interval_seconds=2.0)

    # Debe haber detectado exactamente 3 diapositivas (roja, azul, verde)
    assert len(slides) == 3
    for s in slides:
        assert s.file_path.exists()
        assert s.file_path.name.startswith("slide_")
