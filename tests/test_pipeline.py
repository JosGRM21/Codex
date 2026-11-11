"""Pruebas para el orquestador principal CodexPipeline."""

from pathlib import Path
from codex.pipeline import CodexPipeline
from codex.config import AppConfig

def test_pipeline_prepare_and_export_audio(tmp_path: Path):
    audio_source = Path("Audio, Ejercicio 2.m4a")
    if not audio_source.exists():
        return

    vault_dir = tmp_path / "Vault"
    bundles_dir = tmp_path / "Bundles"

    cfg = AppConfig(
        obsidian_vault_path=vault_dir,
        bundles_path=bundles_dir
    )
    pipeline = CodexPipeline(cfg)

    # 1. Preparar bundle
    bundle = pipeline.prepare(
        media_path=audio_source,
        subject_name_or_code="sistemas_operativos",
        class_date="2026-11-10",
        custom_bundle_dir=bundles_dir
    )

    assert bundle.bundle_dir.exists()
    assert bundle.manifest_path.exists()
    assert bundle.agent_context_path.exists()
    assert bundle.audio_path.exists()
    assert bundle.subject.codigo == "SO-301"

    # 2. Exportar nota generada por Agente de IA
    sample_note = """# Sistemas Operativos: Hilos y Planificación

## 🧠 Conceptos Clave
> [!tip] Concepto Clave: Hilos de Ejecución
Un hilo es la unidad básica de utilización de CPU.
"""
    exported_note = pipeline.export(
        bundle_or_manifest=bundle,
        notes_content_or_path=sample_note,
        custom_vault_path=vault_dir
    )

    assert exported_note.exists()
    content = exported_note.read_text(encoding="utf-8")
    assert "Hilos y Planificación" in content
    assert "Sistemas Operativos" in str(exported_note)

def test_pipeline_process_end_to_end(tmp_path: Path):
    audio_source = Path("Audio, Ejercicio 2.m4a")
    if not audio_source.exists():
        return

    vault_dir = tmp_path / "Vault"
    bundles_dir = tmp_path / "Bundles"
    cfg = AppConfig(obsidian_vault_path=vault_dir, bundles_path=bundles_dir)
    pipeline = CodexPipeline(cfg)

    note_text = "# Sistemas Operativos: Memoria Virtual\n\nTexto de prueba."
    result = pipeline.process(
        media_path=audio_source,
        subject_name_or_code="sistemas_operativos",
        class_date="2026-11-10",
        notes_content_or_path=note_text,
        custom_vault_path=vault_dir,
        custom_bundle_dir=bundles_dir
    )

    assert result["success"] is True
    assert result["status"] == "exported"
    assert Path(result["note_path"]).exists()
