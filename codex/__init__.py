"""Codex - Motor de clases académicas con soporte para Agentes de IA mediante Skills."""

__version__ = "0.2.0"

from codex.config import AppConfig, SubjectConfig, load_config, load_subject
from codex.core.bundle import LectureBundle, create_lecture_bundle, load_lecture_bundle
from codex.core.exporter import ObsidianExporter
from codex.core.media import MediaInspector, extract_audio
from codex.core.vision import SlideExtractor, SlideFrame
from codex.pipeline import CodexPipeline
from codex.skills import list_skills, get_skill, install_skills

__all__ = [
    "AppConfig",
    "SubjectConfig",
    "load_config",
    "load_subject",
    "LectureBundle",
    "create_lecture_bundle",
    "load_lecture_bundle",
    "ObsidianExporter",
    "MediaInspector",
    "extract_audio",
    "SlideExtractor",
    "SlideFrame",
    "CodexPipeline",
    "list_skills",
    "get_skill",
    "install_skills",
]
