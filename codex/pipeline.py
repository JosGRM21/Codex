"""Pipeline principal que orquesta el flujo de preparación y exportación de Codex para Agentes de IA."""

import datetime
import time
from pathlib import Path
from typing import Dict, Any, Optional, Union

from codex.config import AppConfig, SubjectConfig, load_config, load_subject
from codex.core.bundle import LectureBundle, create_lecture_bundle, load_lecture_bundle
from codex.core.exporter import ObsidianExporter
from codex.utils.logger import logger, console
from rich.panel import Panel

class CodexPipeline:
    """Orquestador end-to-end de Codex orientado a Agentes de IA mediante Skills."""

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or load_config()
        self.exporter = ObsidianExporter(self.config)

    def prepare(
        self,
        media_path: Path,
        subject_name_or_code: str = "General",
        class_date: Optional[str] = None,
        custom_bundle_dir: Optional[Path] = None
    ) -> LectureBundle:
        """
        Ejecuta la fase de extracción de audio y diapositivas, y genera el bundle
        con manifest.json y agent_context.md listo para el Agente de IA.
        """
        start_time = time.time()
        media_path = Path(media_path).resolve()
        
        if not media_path.exists():
            raise FileNotFoundError(f"El archivo de medios no existe: {media_path}")

        # Fecha por defecto: fecha de modificación o hoy
        if not class_date:
            mtime = media_path.stat().st_mtime
            class_date = datetime.date.fromtimestamp(mtime).strftime("%Y-%m-%d")

        subject = load_subject(subject_name_or_code)

        console.print(Panel(
            f"[bold]Iniciando preparación de sesión con Codex para Agente de IA[/bold]\n"
            f"• Archivo: [cyan]{media_path.name}[/cyan]\n"
            f"• Materia: [accent]{subject.nombre}[/accent] ({subject.codigo})\n"
            f"• Docente: {subject.docente}\n"
            f"• Fecha: {class_date}",
            title="Codex Academic Engine",
            border_style="cyan"
        ))

        bundle = create_lecture_bundle(
            media_path=media_path,
            subject=subject,
            class_date=class_date,
            output_base_dir=custom_bundle_dir,
            config=self.config
        )

        elapsed_seconds = time.time() - start_time
        console.print(Panel(
            f"[bold green]✓ Paquete preparado para el Agente de IA ({elapsed_seconds:.1f}s)[/bold green]\n\n"
            f"• Bundle: [accent]{bundle.bundle_dir}[/accent]\n"
            f"• Contexto para Agente: [cyan]{bundle.agent_context_path.name}[/cyan]\n"
            f"• Diapositivas extraídas: {len(bundle.slides)}\n"
            f"• Skill recomendado: [bold magenta]codex-academic[/bold magenta]",
            title="Codex Bundle Listo",
            border_style="green"
        ))

        return bundle

    def export(
        self,
        bundle_or_manifest: Union[Path, str, LectureBundle],
        notes_content_or_path: Union[str, Path],
        custom_vault_path: Optional[Path] = None
    ) -> Path:
        """
        Exporta la nota generada por el Agente de IA y sus diapositivas a la bóveda de Obsidian.
        """
        if isinstance(bundle_or_manifest, LectureBundle):
            bundle = bundle_or_manifest
        else:
            bundle = load_lecture_bundle(Path(bundle_or_manifest))

        # Si notes_content_or_path es una ruta a un archivo existente, leerlo
        if isinstance(notes_content_or_path, (Path, str)):
            candidate_path = Path(notes_content_or_path)
            if candidate_path.exists() and candidate_path.is_file():
                markdown_content = candidate_path.read_text(encoding="utf-8")
            else:
                markdown_content = str(notes_content_or_path)
        else:
            markdown_content = str(notes_content_or_path)

        exported_path = self.exporter.export(
            markdown_content=markdown_content,
            bundle=bundle,
            custom_vault_path=custom_vault_path
        )

        console.print(Panel(
            f"[bold green]✓ Nota académica exportada con éxito a Obsidian[/bold green]\n\n"
            f"• Nota Obsidian: [accent]{exported_path}[/accent]\n"
            f"• Diapositivas integradas: {len(bundle.slides)}\n"
            f"• Materia: {bundle.subject.nombre}",
            title="Codex Export Finalizado",
            border_style="green"
        ))

        return exported_path

    def process(
        self,
        media_path: Path,
        subject_name_or_code: str = "General",
        class_date: Optional[str] = None,
        notes_content_or_path: Optional[Union[str, Path]] = None,
        custom_vault_path: Optional[Path] = None,
        custom_bundle_dir: Optional[Path] = None
    ) -> Dict[str, Any]:
        """
        Flujo de conveniencia: prepara el bundle y, si se proporcionan notas, las exporta a Obsidian.
        """
        bundle = self.prepare(
            media_path=media_path,
            subject_name_or_code=subject_name_or_code,
            class_date=class_date,
            custom_bundle_dir=custom_bundle_dir
        )

        if notes_content_or_path is not None:
            exported_file = self.export(
                bundle_or_manifest=bundle,
                notes_content_or_path=notes_content_or_path,
                custom_vault_path=custom_vault_path
            )
            return {
                "success": True,
                "status": "exported",
                "bundle_id": bundle.bundle_id,
                "bundle_dir": str(bundle.bundle_dir),
                "note_path": str(exported_file),
                "slides_count": len(bundle.slides),
                "subject": bundle.subject.nombre,
            }

        return {
            "success": True,
            "status": "ready_for_agent",
            "bundle_id": bundle.bundle_id,
            "bundle_dir": str(bundle.bundle_dir),
            "manifest_path": str(bundle.manifest_path),
            "agent_context_path": str(bundle.agent_context_path),
            "slides_count": len(bundle.slides),
            "subject": bundle.subject.nombre,
        }
