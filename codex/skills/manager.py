"""Gestor de skills de Agentes de IA para Codex."""

import re
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

from codex.utils.logger import logger

SKILLS_DEFINITIONS_DIR = Path(__file__).resolve().parent / "definitions"

def _parse_frontmatter(file_path: Path) -> Dict[str, Any]:
    """Extrae y parsea el frontmatter YAML de un archivo SKILL.md."""
    if not file_path.exists():
        return {}
    
    content = file_path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        return {"name": file_path.parent.name, "description": ""}
    
    parts = content.split("---", 2)
    if len(parts) >= 3:
        frontmatter_text = parts[1]
        try:
            data = yaml.safe_load(frontmatter_text) or {}
            data["content"] = parts[2].strip()
            return data
        except Exception:
            pass
    return {"name": file_path.parent.name, "description": "", "content": content}

def list_skills() -> List[Dict[str, Any]]:
    """
    Lista todos los skills disponibles en Codex.
    """
    skills = []
    if not SKILLS_DEFINITIONS_DIR.exists():
        return skills

    for skill_folder in sorted(SKILLS_DEFINITIONS_DIR.iterdir()):
        skill_file = skill_folder / "SKILL.md"
        if skill_folder.is_dir() and skill_file.exists():
            info = _parse_frontmatter(skill_file)
            skills.append({
                "name": info.get("name", skill_folder.name),
                "description": info.get("description", "").strip(),
                "path": str(skill_file),
                "folder": str(skill_folder),
            })
    return skills

def get_skill(name: str) -> Optional[Dict[str, Any]]:
    """
    Obtiene los detalles y contenido completo de un skill por su nombre.
    """
    target = name.strip().lower()
    for skill_info in list_skills():
        if skill_info["name"].lower() == target:
            skill_file = Path(skill_info["path"])
            content = skill_file.read_text(encoding="utf-8")
            return {
                "name": skill_info["name"],
                "description": skill_info["description"],
                "path": skill_info["path"],
                "content": content,
            }
    return None

def install_skills(
    target_dir: Optional[Path] = None,
    overwrite: bool = True
) -> List[Path]:
    """
    Instala los skills de Codex en el directorio de trabajo (por defecto .agents/skills).
    Retorna la lista de rutas de skills instalados.
    """
    if target_dir is None:
        target_dir = Path.cwd() / ".agents" / "skills"
    else:
        target_dir = Path(target_dir).resolve()

    target_dir.mkdir(parents=True, exist_ok=True)
    installed_paths = []

    for s_info in list_skills():
        source_folder = Path(s_info["folder"])
        dest_folder = target_dir / source_folder.name

        if dest_folder.exists() and not overwrite:
            logger.info(f"Skill ya existente (omitido): {dest_folder}")
            continue

        shutil.copytree(source_folder, dest_folder, dirs_exist_ok=True)
        installed_paths.append(dest_folder / "SKILL.md")
        logger.info(f"[success]Skill instalado:[/success] [accent]{dest_folder}[/accent]")

    return installed_paths
