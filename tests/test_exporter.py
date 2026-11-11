"""Pruebas para el exportador estructurado hacia Obsidian."""

from pathlib import Path
from codex.core.exporter import ObsidianExporter
from codex.config import AppConfig, SubjectConfig
from codex.core.vision import SlideFrame
from codex.core.bundle import LectureBundle

def test_obsidian_exporter_with_bundle(tmp_path: Path):
    vault_dir = tmp_path / "Vault"
    bundle_dir = tmp_path / "Bundle"
    slides_dir = bundle_dir / "slides"
    slides_dir.mkdir(parents=True)

    test_slide_path = slides_dir / "slide_001000.png"
    test_slide_path.write_bytes(b"\x89PNG\r\n\x1a\nfakeimage")

    slide = SlideFrame(
        timestamp_seconds=600.0,
        time_str="00:10:00",
        file_path=test_slide_path,
        tag="001000"
    )

    subject = SubjectConfig(codigo="SO-101", nombre="Sistemas Operativos", docente="Prof. Smith")

    bundle = LectureBundle(
        bundle_id="so_class_1",
        bundle_dir=bundle_dir,
        manifest_path=bundle_dir / "manifest.json",
        agent_context_path=bundle_dir / "agent_context.md",
        audio_path=None,
        slides_dir=slides_dir,
        slides=[slide],
        subject=subject,
        class_date="2026-11-05",
        metadata={}
    )
    bundle.save_manifest()

    cfg = AppConfig(
        obsidian_vault_path=vault_dir,
        notes_subfolder="Clases",
        attachments_subfolder="attachments/Codex"
    )
    exporter = ObsidianExporter(cfg)

    markdown_sample = """# Sistemas Operativos: Gestión de Memoria

## 📌 Compromisos y Tareas
- [ ] [00:10:00] Entregar laboratorio 1

## 📝 Desarrollo Cronológico
![[slide_001000.png]]
"""

    exported_file = exporter.export(
        markdown_content=markdown_sample,
        bundle=bundle,
        custom_vault_path=vault_dir
    )

    assert exported_file.exists()
    assert "2026-11-05" in exported_file.name
    assert "Gestión de Memoria" in exported_file.name

    # Verificar que el contenido se escribió correctamente
    content = exported_file.read_text(encoding="utf-8")
    assert "Sistemas Operativos: Gestión de Memoria" in content
    
    # Verificar que la diapositiva se copió a attachments/Codex
    copied_attachment = vault_dir / "attachments" / "Codex" / "slide_001000.png"
    assert copied_attachment.exists()

    # Verificar que el manifest del bundle se actualizó
    assert bundle.metadata.get("status") == "exported"
    assert bundle.metadata.get("exported_note_path") == str(exported_file)

def test_obsidian_exporter_cleans_fences(tmp_path: Path):
    cfg = AppConfig(obsidian_vault_path=tmp_path / "Vault")
    exporter = ObsidianExporter(cfg)
    subject = SubjectConfig(codigo="BD-101", nombre="Bases de Datos")

    wrapped_content = "```markdown\n# Bases de Datos: SQL y ACID\n\nContenido de la nota.\n```"
    exported = exporter.export(
        markdown_content=wrapped_content,
        subject=subject,
        class_date="2026-11-10",
        custom_vault_path=tmp_path / "Vault"
    )

    content = exported.read_text(encoding="utf-8")
    assert not content.startswith("```markdown")
    assert not content.endswith("```\n")
    assert "SQL y ACID" in content
