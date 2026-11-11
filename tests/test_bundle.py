"""Pruebas unitarias para el empaquetado de sesiones (bundles) de Agentes de IA."""

import json
from pathlib import Path
from codex.core.bundle import LectureBundle, create_lecture_bundle, load_lecture_bundle
from codex.core.vision import SlideFrame
from codex.config import AppConfig, SubjectConfig

def test_lecture_bundle_to_dict_and_save(tmp_path: Path):
    bundle_dir = tmp_path / "bundle_test"
    bundle_dir.mkdir()
    manifest_path = bundle_dir / "manifest.json"
    context_path = bundle_dir / "agent_context.md"
    slides_dir = bundle_dir / "slides"
    slides_dir.mkdir()

    slide_file = slides_dir / "slide_000100.png"
    slide_file.write_bytes(b"\x89PNG\r\n\x1a\nfake")

    slide = SlideFrame(
        timestamp_seconds=60.0,
        time_str="00:01:00",
        file_path=slide_file,
        tag="000100"
    )

    subject = SubjectConfig(
        codigo="CS-101",
        nombre="Algoritmos y Estructuras",
        docente="Dra. Turing",
        tags=["algoritmos", "cs"]
    )

    bundle = LectureBundle(
        bundle_id="2026-11-10_cs_101_test",
        bundle_dir=bundle_dir,
        manifest_path=manifest_path,
        agent_context_path=context_path,
        audio_path=bundle_dir / "audio" / "lecture.opus",
        slides_dir=slides_dir,
        slides=[slide],
        subject=subject,
        class_date="2026-11-10",
        metadata={"media_info": {"duration": 3600.0}}
    )

    # 1. Guardar manifest
    bundle.save_manifest()
    assert manifest_path.exists()

    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["bundle_id"] == "2026-11-10_cs_101_test"
    assert data["slides_count"] == 1
    assert data["subject"]["codigo"] == "CS-101"

    # 2. Guardar contexto para Agente
    bundle.save_agent_context()
    assert context_path.exists()
    context_text = context_path.read_text(encoding="utf-8")
    assert "Algoritmos y Estructuras" in context_text
    assert "slide_000100.png" in context_text
    assert "codex-academic" in context_text

    # 3. Cargar desde disco
    loaded = load_lecture_bundle(bundle_dir)
    assert loaded.bundle_id == bundle.bundle_id
    assert loaded.subject.codigo == "CS-101"
    assert len(loaded.slides) == 1
    assert loaded.slides[0].time_str == "00:01:00"

def test_load_lecture_bundle_from_manifest_file(tmp_path: Path):
    bundle_dir = tmp_path / "bundle_manifest_test"
    bundle_dir.mkdir()
    manifest_path = bundle_dir / "manifest.json"

    data = {
        "version": "1.0",
        "bundle_id": "test_bundle",
        "class_date": "2026-11-10",
        "subject": {
            "codigo": "MAT-201",
            "nombre": "Cálculo",
            "docente": "Prof. Newton",
            "tags": ["matematicas"]
        },
        "slides": []
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(data, f)

    loaded = load_lecture_bundle(manifest_path)
    assert loaded.bundle_id == "test_bundle"
    assert loaded.subject.nombre == "Cálculo"
