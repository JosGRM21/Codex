"""Pruebas unitarias para los comandos de la CLI de Codex."""

from pathlib import Path
from typer.testing import CliRunner
from codex.cli import app

runner = CliRunner()

def test_cli_config_check():
    result = runner.invoke(app, ["config", "check"])
    assert result.exit_code == 0
    assert "FFmpeg" in result.stdout
    assert "Obsidian Vault" in result.stdout
    # Verificar que no menciona claves de API de Gemini
    assert "Gemini API Key" not in result.stdout

def test_cli_config_show():
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
    assert "Configuración de Codex" in result.stdout

def test_cli_subjects_list_and_info():
    list_res = runner.invoke(app, ["subjects", "list"])
    assert list_res.exit_code == 0
    assert "SO-301" in list_res.stdout
    assert "base_de_datos" in list_res.stdout

    info_res = runner.invoke(app, ["subjects", "info", "sistemas_operativos"])
    assert info_res.exit_code == 0
    assert "SO-301" in info_res.stdout

def test_cli_skills_commands():
    list_res = runner.invoke(app, ["skills", "list"])
    assert list_res.exit_code == 0
    assert "codex-academic" in list_res.stdout

    show_res = runner.invoke(app, ["skills", "show", "codex-academic"])
    assert show_res.exit_code == 0
    assert "Skill: Codex Academic Notes Engine" in show_res.stdout

def test_cli_prepare_and_export(tmp_path: Path):
    audio_source = Path("Audio, Ejercicio 2.m4a")
    if not audio_source.exists():
        return

    bundles_dir = tmp_path / "cli_bundles"
    vault_dir = tmp_path / "cli_vault"

    # 1. Prepare
    prep_res = runner.invoke(app, [
        "prepare",
        str(audio_source),
        "--subject", "base_de_datos",
        "--date", "2026-11-10",
        "--output", str(bundles_dir)
    ])
    assert prep_res.exit_code == 0
    assert "Paquete preparado para el Agente de IA" in prep_res.stdout

    # Localizar el bundle generado
    created_bundles = list(bundles_dir.iterdir())
    assert len(created_bundles) == 1
    bundle_path = created_bundles[0]

    # 2. Redactar nota simulada
    note_file = tmp_path / "draft_note.md"
    note_file.write_text("# Base de Datos: Modelo Relacional\n\nContenido de prueba.", encoding="utf-8")

    # 3. Export
    exp_res = runner.invoke(app, [
        "export",
        str(bundle_path),
        str(note_file),
        "--vault", str(vault_dir)
    ])
    assert exp_res.exit_code == 0
    assert "Nota académica exportada con éxito a Obsidian" in exp_res.stdout
