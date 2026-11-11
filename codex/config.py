"""Módulo de configuración y carga de perfiles de materias para Codex."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import yaml

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

class AudioConfig(BaseModel):
    sample_rate: int = 16000
    channels: int = 1
    codec: str = "libopus"
    bitrate: str = "32k"
    extension: str = ".opus"

class VisionConfig(BaseModel):
    scene_threshold: float = 0.05
    min_interval_seconds: float = 5.0
    diff_threshold: float = 0.08
    max_width: int = 1920

class WatcherConfig(BaseModel):
    debounce_seconds: int = 8
    video_extensions: List[str] = [".mkv", ".mp4", ".mov", ".webm", ".m4a", ".mp3", ".wav"]

class AppConfig(BaseModel):
    obsidian_vault_path: Path = Path.home() / "Documents" / "Obsidian" / "Universidad"
    notes_subfolder: str = "Clases"
    attachments_subfolder: str = "attachments/Codex"
    obs_recordings_path: Path = Path.home() / "Videos"
    bundles_path: Path = Path(".codex_bundles")
    audio: AudioConfig = Field(default_factory=AudioConfig)
    vision: VisionConfig = Field(default_factory=VisionConfig)
    watcher: WatcherConfig = Field(default_factory=WatcherConfig)

class SubjectConfig(BaseModel):
    codigo: str = "GEN-101"
    nombre: str = "General"
    docente: str = "Docente"
    tags: List[str] = ["universidad", "clase"]

def get_config_path() -> Path:
    """Ruta al archivo config.yaml."""
    return BASE_DIR / "config.yaml"

def get_subjects_dir() -> Path:
    """Ruta a la carpeta de perfiles de asignaturas."""
    return BASE_DIR / "subjects"

def get_bundles_dir(config: Optional[AppConfig] = None) -> Path:
    """Ruta a la carpeta donde se almacenan los bundles de sesión."""
    cfg = config or load_config()
    p = cfg.bundles_path
    if not p.is_absolute():
        p = BASE_DIR / p
    return p

def load_config(custom_path: Optional[Path] = None) -> AppConfig:
    """Carga la configuración desde config.yaml o valores por defecto."""
    path = custom_path or get_config_path()
    data: Dict[str, Any] = {}
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            loaded = yaml.safe_load(f)
            if loaded:
                data = loaded

    # Resolver rutas
    if "obsidian_vault_path" in data and isinstance(data["obsidian_vault_path"], str):
        data["obsidian_vault_path"] = Path(data["obsidian_vault_path"])
    if "obs_recordings_path" in data and isinstance(data["obs_recordings_path"], str):
        data["obs_recordings_path"] = Path(data["obs_recordings_path"])
    if "bundles_path" in data and isinstance(data["bundles_path"], str):
        data["bundles_path"] = Path(data["bundles_path"])

    return AppConfig(**data)

def list_subjects() -> List[str]:
    """Lista los identificadores de materias disponibles en subjects/."""
    subjects_dir = get_subjects_dir()
    if not subjects_dir.exists():
        return []
    return [p.stem for p in subjects_dir.glob("*.yaml") if p.stem != "template"]

def load_subject(name_or_code: str) -> SubjectConfig:
    """
    Carga el perfil de una asignatura por nombre de archivo o código.
    Si no existe, retorna una configuración genérica.
    """
    subjects_dir = get_subjects_dir()
    slug = name_or_code.lower().strip().replace(" ", "_").replace("-", "_")
    target_file = subjects_dir / f"{slug}.yaml"
    
    if target_file.exists():
        with open(target_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
            return SubjectConfig(**data)

    # Buscar por coincidencia interna de código o nombre
    if subjects_dir.exists():
        for p in subjects_dir.glob("*.yaml"):
            if p.stem == "template":
                continue
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
                    if data.get("codigo", "").lower() == slug or data.get("nombre", "").lower() == name_or_code.lower():
                        return SubjectConfig(**data)
            except Exception:
                continue

    # Fallback genérico
    return SubjectConfig(nombre=name_or_code, codigo=slug.upper()[:6])
