"""Módulo de exportación estructurada para bóvedas (Vaults) de Obsidian."""

import re
import shutil
from pathlib import Path
from typing import Any, List, Optional, Union

from codex.core.vision import SlideFrame
from codex.config import AppConfig, SubjectConfig, load_config
from codex.utils.logger import logger

class ObsidianExporter:
    """Gestiona la exportación de notas y assets a la estructura de carpetas de Obsidian."""

    def __init__(self, app_config: Optional[AppConfig] = None):
        self.cfg = app_config or load_config()

    def export(
        self,
        markdown_content: str,
        bundle: Optional[Any] = None,
        slides: Optional[List[SlideFrame]] = None,
        subject: Optional[SubjectConfig] = None,
        class_date: Optional[str] = None,
        custom_vault_path: Optional[Path] = None
    ) -> Path:
        """
        Copia las capturas al directorio de adjuntos del Vault y guarda la nota en la carpeta de la materia.
        Acepta un LectureBundle directamente o los componentes individuales (slides, subject, class_date).
        
        Retorna:
            Path: Ruta absoluta al archivo .md generado en el Vault.
        """
        # Si se proporcionó un bundle, extraer sus propiedades
        if bundle is not None:
            # Importación local para evitar dependencia circular
            from codex.core.bundle import LectureBundle
            if isinstance(bundle, LectureBundle):
                slides = slides if slides is not None else bundle.slides
                subject = subject if subject is not None else bundle.subject
                class_date = class_date if class_date is not None else bundle.class_date

        subject = subject or SubjectConfig()
        class_date = class_date or "1970-01-01"
        slides = slides or []

        vault_path = Path(custom_vault_path or self.cfg.obsidian_vault_path).resolve()
        
        # 1. Crear directorios de destino en el Vault
        safe_subject_name = re.sub(r'[\\/*?:"<>|]', "", subject.nombre).strip()
        notes_dir = vault_path / self.cfg.notes_subfolder / safe_subject_name
        attachments_dir = vault_path / self.cfg.attachments_subfolder
        
        notes_dir.mkdir(parents=True, exist_ok=True)
        attachments_dir.mkdir(parents=True, exist_ok=True)

        # 2. Copiar capturas de diapositivas a la carpeta de adjuntos de Obsidian
        if slides:
            logger.info(f"Copiando {len(slides)} diapositivas a los adjuntos de Obsidian ({attachments_dir})...")
            for slide in slides:
                if slide.file_path.exists():
                    dest_image = attachments_dir / slide.file_path.name
                    shutil.copy2(slide.file_path, dest_image)

        # 3. Limpiar bloques de código markdown envolventes si el LLM o agente los agregó
        cleaned_content = markdown_content.strip()
        if cleaned_content.startswith("```markdown"):
            cleaned_content = cleaned_content[len("```markdown"):].strip()
        elif cleaned_content.startswith("```md"):
            cleaned_content = cleaned_content[len("```md"):].strip()
            
        if cleaned_content.endswith("```"):
            cleaned_content = cleaned_content[:-3].strip()

        # 4. Determinar nombre de archivo para la nota
        # Intentar extraer subtítulo o tema del contenido (# Materia: Tema o # Tema)
        topic_match = re.search(r"^#\s+(?:[^:]+:\s*)?(.+)$", cleaned_content, re.MULTILINE)
        if topic_match:
            raw_topic = topic_match.group(1).strip()
            safe_topic = re.sub(r'[\\/*?:"<>|]', "", raw_topic)[:60].strip()
            note_filename = f"{class_date} - {safe_topic}.md"
        else:
            note_filename = f"{class_date} - {safe_subject_name}.md"

        output_file = notes_dir / note_filename
        
        # Evitar sobreescritura accidental si ya existe agregando sufijo
        counter = 1
        while output_file.exists():
            stem = note_filename[:-3]
            output_file = notes_dir / f"{stem}_{counter}.md"
            counter += 1

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(cleaned_content + "\n")

        # 5. Si vino de un bundle, actualizar el estado del manifest
        if bundle is not None and hasattr(bundle, "metadata") and hasattr(bundle, "save_manifest"):
            bundle.metadata["status"] = "exported"
            bundle.metadata["exported_note_path"] = str(output_file)
            try:
                bundle.save_manifest()
            except Exception:
                pass

        logger.info(f"[success]Apunte guardado en Obsidian:[/success] [accent]{output_file}[/accent]")
        return output_file
