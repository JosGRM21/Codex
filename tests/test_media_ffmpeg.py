"""Pruebas de integración con FFmpeg y extracción de medios."""

import subprocess
from pathlib import Path
from codex.utils.ffmpeg_finder import require_ffmpeg, find_ffmpeg_binaries
from codex.core.media import MediaInspector, extract_audio
from codex.config import AudioConfig

def test_find_ffmpeg():
    ffmpeg, ffprobe = require_ffmpeg()
    assert Path(ffmpeg).exists()
    assert Path(ffprobe).exists()

def test_audio_extraction_with_synthetic_video(tmp_path: Path):
    ffmpeg, _ = require_ffmpeg()
    video_path = tmp_path / "test_synth.mp4"
    audio_output = tmp_path / "test_audio.opus"

    # Generar un video sintético de 2 segundos con audio sinusoidal
    cmd = [
        ffmpeg, "-y",
        "-f", "lavfi", "-i", "testsrc=duration=2:size=320x240:rate=10",
        "-f", "lavfi", "-i", "sine=frequency=1000:duration=2",
        "-c:v", "libx264", "-c:a", "aac",
        str(video_path)
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    assert video_path.exists()

    # Inspeccionar video
    info = MediaInspector.get_video_info(video_path)
    assert info["duration"] >= 1.5
    assert info["has_audio"] is True
    assert info["width"] == 320
    assert info["height"] == 240

    # Extraer audio
    audio_cfg = AudioConfig(sample_rate=16000, channels=1, codec="libopus", bitrate="32k", extension=".opus")
    extracted = extract_audio(video_path, audio_output, audio_cfg)
    assert extracted.exists()
    assert extracted.stat().st_size > 0
