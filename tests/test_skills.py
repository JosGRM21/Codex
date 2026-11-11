"""Pruebas unitarias para la gestión e instalación de Skills de Agentes de IA."""

from pathlib import Path
from codex.skills import list_skills, get_skill, install_skills

def test_list_skills():
    skills = list_skills()
    skill_names = [s["name"] for s in skills]
    assert "codex-academic" in skill_names
    assert "codex-study-guide" in skill_names

    for s in skills:
        assert len(s["description"]) > 0
        assert Path(s["path"]).exists()

def test_get_skill():
    academic = get_skill("codex-academic")
    assert academic is not None
    assert academic["name"] == "codex-academic"
    assert "Obsidian" in academic["content"]
    assert "codex prepare" in academic["content"]

    none_skill = get_skill("habilidad_inventada")
    assert none_skill is None

def test_install_skills(tmp_path: Path):
    target = tmp_path / "installed_skills"
    installed = install_skills(target_dir=target)
    assert len(installed) >= 2

    for p in installed:
        assert p.exists()
        assert p.name == "SKILL.md"
        assert p.parent.name in ["codex-academic", "codex-study-guide"]
