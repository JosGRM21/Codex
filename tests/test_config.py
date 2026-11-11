"""Pruebas unitarias para la carga y validación de configuración."""

from pathlib import Path
from codex.config import load_config, load_subject, list_subjects, AppConfig, SubjectConfig

def test_load_default_config():
    cfg = load_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.audio.sample_rate == 16000
    assert cfg.audio.channels == 1
    assert cfg.vision.scene_threshold > 0
    assert cfg.bundles_path is not None
    # Verificar que no existen atributos de API de Gemini
    assert not hasattr(cfg, "gemini_model")
    assert not hasattr(cfg, "gemini_api_key")

def test_list_and_load_subjects():
    subjects = list_subjects()
    assert "sistemas_operativos" in subjects
    assert "base_de_datos" in subjects

    so = load_subject("sistemas_operativos")
    assert isinstance(so, SubjectConfig)
    assert so.codigo == "SO-301"
    assert "sistemas-operativos" in so.tags
    assert so.docente == "Profesor Principal"

def test_load_unknown_subject_fallback():
    subj = load_subject("Física Cuántica")
    assert subj.nombre == "Física Cuántica"
    assert len(subj.codigo) > 0
