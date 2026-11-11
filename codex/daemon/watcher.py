"""Daemon de monitoreo con Watchdog para detección automática de grabaciones de OBS."""

import os
import time
from pathlib import Path
from typing import Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from codex.config import AppConfig, load_config
from codex.pipeline import CodexPipeline
from codex.utils.logger import logger, console

class OBSFileHandler(FileSystemEventHandler):
    """Manejador de eventos que detecta cuando OBS termina de escribir un archivo de video."""

    def __init__(self, pipeline: CodexPipeline, config: AppConfig, default_subject: str = "General"):
        super().__init__()
        self.pipeline = pipeline
        self.config = config
        self.default_subject = default_subject
        self.processing_files: Set[Path] = set()

    def on_created(self, event):
        if not event.is_directory:
            self._handle_possible_video(Path(event.src_path))

    def on_modified(self, event):
        if not event.is_directory:
            self._handle_possible_video(Path(event.src_path))

    def _handle_possible_video(self, file_path: Path):
        ext = file_path.suffix.lower()
        if ext not in self.config.watcher.video_extensions:
            return

        if file_path in self.processing_files:
            return

        # Ignorar archivos temporales incompletos
        if ".part" in file_path.name or ".crdownload" in file_path.name:
            return

        self.processing_files.add(file_path)
        logger.info(f"[cyan]Grabación detectada de OBS:[/cyan] {file_path.name}")
        logger.info("Esperando estabilización de tamaño para asegurar fin de grabación...")

        # Esperar a que OBS termine de escribir
        if self._wait_for_file_ready(file_path):
            try:
                logger.info(f"[accent]Iniciando preparación de bundle para Agente de IA:[/accent] {file_path.name}")
                bundle = self.pipeline.prepare(
                    media_path=file_path,
                    subject_name_or_code=self.default_subject
                )
                logger.info(
                    f"[bold green]✓ Sesión lista para ser procesada por el Agente de IA:[/bold green]\n"
                    f"  Bundle: {bundle.bundle_dir}\n"
                    f"  Contexto: {bundle.agent_context_path}\n"
                    f"  Activa el skill 'codex-academic' para redactar los apuntes."
                )
            except Exception as e:
                logger.error(f"Error preparando video {file_path.name}: {e}")
            finally:
                self.processing_files.discard(file_path)
        else:
            self.processing_files.discard(file_path)

    def _wait_for_file_ready(self, file_path: Path) -> bool:
        """
        Monitorea el archivo hasta que el tamaño no cambie durante debounce_seconds
        y el archivo pueda abrirse sin bloqueo exclusivo de OBS.
        """
        debounce = self.config.watcher.debounce_seconds
        last_size = -1
        stable_count = 0
        max_attempts = 120  # 120 * 2s = 4 minutos máx de espera de estabilización

        for _ in range(max_attempts):
            if not file_path.exists():
                return False

            try:
                current_size = file_path.stat().st_size
                if current_size > 0 and current_size == last_size:
                    stable_count += 1
                else:
                    stable_count = 0
                    last_size = current_size

                # Si el peso no ha variado en varios checks consecutivos
                if stable_count >= max(1, (debounce // 2)):
                    # Probar si el archivo se puede abrir en modo lectura exclusivo
                    with open(file_path, "rb") as f:
                        f.seek(0, os.SEEK_END)
                    logger.info("[success]Grabación de OBS completada y desbloqueada.[/success]")
                    return True

            except (PermissionError, IOError):
                # OBS aún tiene el archivo abierto para escritura
                stable_count = 0

            time.sleep(2)

        logger.warning(f"Tiempo de espera de estabilización excedido para {file_path.name}")
        return False

def start_watcher(
    watch_dir: Optional[Path] = None,
    subject: str = "General",
    config: Optional[AppConfig] = None
):
    """Inicia el servicio daemon de monitoreo de grabaciones."""
    cfg = config or load_config()
    target_dir = Path(watch_dir or cfg.obs_recordings_path).resolve()
    target_dir.mkdir(parents=True, exist_ok=True)

    pipeline = CodexPipeline(cfg)
    event_handler = OBSFileHandler(pipeline, cfg, default_subject=subject)
    
    observer = Observer()
    observer.schedule(event_handler, str(target_dir), recursive=False)
    observer.start()

    console.print(f"[bold green]Daemon Codex Watcher activo[/bold green] monitoreando: [accent]{target_dir}[/accent]")
    console.print(f"Asignatura predeterminada: [cyan]{subject}[/cyan]")
    console.print("Al detectar el fin de una grabación, Codex creará automáticamente el bundle para el Agente de IA.")
    console.print("Presiona Ctrl+C para detener el servicio.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Deteniendo servicio de monitoreo Codex...[/yellow]")
        observer.stop()
    observer.join()
