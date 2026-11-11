"""Interfaz de línea de comandos (CLI) principal para Codex orientada a Agentes de IA."""

from pathlib import Path
from typing import Optional
import typer
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from codex.config import load_config, list_subjects, load_subject, get_bundles_dir
from codex.pipeline import CodexPipeline
from codex.daemon.watcher import start_watcher
from codex.utils.ffmpeg_finder import find_ffmpeg_binaries
from codex.utils.logger import console
from codex.skills import list_skills, get_skill, install_skills

app = typer.Typer(
    name="codex",
    help="Codex: Motor de clases universitarias con soporte para Agentes de IA mediante skills hacia Obsidian",
    add_completion=False,
)

subjects_app = typer.Typer(name="subjects", help="Gestión de perfiles de materias y metadatos")
skills_app = typer.Typer(name="skills", help="Gestión e instalación de skills para Agentes de IA")
config_app = typer.Typer(name="config", help="Gestión y diagnóstico de configuración")

app.add_typer(subjects_app, name="subjects")
app.add_typer(skills_app, name="skills")
app.add_typer(config_app, name="config")

@app.command(name="prepare")
def prepare_command(
    media_path: Path = typer.Argument(..., help="Ruta al archivo de video o audio grabado por OBS / Meet"),
    subject: str = typer.Option("General", "--subject", "-s", help="Nombre o código de la asignatura (ej: sistemas_operativos)"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Fecha de la clase en formato YYYY-MM-DD (por defecto fecha de archivo o hoy)"),
    output: Optional[Path] = typer.Option(None, "--output", "-o", help="Directorio destino para el bundle"),
):
    """Extrae audio y diapositivas y prepara el paquete (bundle) con manifest y contexto para el Agente de IA."""
    cfg = load_config()
    pipeline = CodexPipeline(cfg)
    try:
        pipeline.prepare(
            media_path=media_path,
            subject_name_or_code=subject,
            class_date=date,
            custom_bundle_dir=output
        )
    except Exception as e:
        console.print(f"[bold red]Error durante la preparación:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command(name="export")
def export_command(
    bundle_path: Path = typer.Argument(..., help="Ruta a la carpeta del bundle o a su manifest.json"),
    notes_file: Path = typer.Argument(..., help="Ruta al archivo Markdown (.md) redactado por el Agente de IA"),
    vault: Optional[Path] = typer.Option(None, "--vault", "-v", help="Ruta alternativa a la bóveda de Obsidian"),
):
    """Valida y exporta la nota redactada por el Agente de IA e integra sus diapositivas en Obsidian."""
    cfg = load_config()
    pipeline = CodexPipeline(cfg)
    try:
        pipeline.export(
            bundle_or_manifest=bundle_path,
            notes_content_or_path=notes_file,
            custom_vault_path=vault
        )
    except Exception as e:
        console.print(f"[bold red]Error durante la exportación:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command(name="process")
def process_command(
    media_path: Path = typer.Argument(..., help="Ruta al archivo de video o audio"),
    subject: str = typer.Option("General", "--subject", "-s", help="Nombre o código de la asignatura"),
    date: Optional[str] = typer.Option(None, "--date", "-d", help="Fecha de la clase en formato YYYY-MM-DD"),
    notes: Optional[Path] = typer.Option(None, "--notes", "-n", help="Ruta a nota ya redactada para exportar inmediatamente"),
    vault: Optional[Path] = typer.Option(None, "--vault", "-v", help="Ruta alternativa a la bóveda de Obsidian"),
):
    """Prepara el bundle de la clase y, si se proporcionan notas, las exporta a Obsidian."""
    cfg = load_config()
    pipeline = CodexPipeline(cfg)
    try:
        pipeline.process(
            media_path=media_path,
            subject_name_or_code=subject,
            class_date=date,
            notes_content_or_path=notes,
            custom_vault_path=vault
        )
    except Exception as e:
        console.print(f"[bold red]Error en el procesamiento:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command(name="watch")
def watch_command(
    folder: Optional[Path] = typer.Option(None, "--folder", "-f", help="Carpeta a monitorear donde OBS guarda las grabaciones"),
    subject: str = typer.Option("General", "--subject", "-s", help="Asignatura predeterminada para las clases detectadas"),
):
    """Inicia el daemon de monitoreo para empaquetar automáticamente las grabaciones al terminar OBS."""
    cfg = load_config()
    try:
        start_watcher(watch_dir=folder, subject=subject, config=cfg)
    except Exception as e:
        console.print(f"[bold red]Error en el daemon de monitoreo:[/bold red] {e}")
        raise typer.Exit(code=1)

# --- Subcomandos de Subjects ---

@subjects_app.command(name="list")
def list_subjects_command():
    """Lista las asignaturas registradas y sus datos clave."""
    subjects = list_subjects()
    if not subjects:
        console.print("[yellow]No se encontraron asignaturas en subjects/[/yellow]")
        return

    table = Table(title="Asignaturas Registradas en Codex", border_style="cyan")
    table.add_column("Slug / ID", style="bold cyan")
    table.add_column("Código", style="green")
    table.add_column("Nombre de la Materia", style="white")
    table.add_column("Docente", style="yellow")
    table.add_column("Tags", style="magenta")

    for s_name in subjects:
        sub = load_subject(s_name)
        table.add_row(s_name, sub.codigo, sub.nombre, sub.docente, ", ".join(sub.tags))

    console.print(table)

@subjects_app.command(name="info")
def info_subject_command(
    subject_id: str = typer.Argument(..., help="Identificador o código de la materia (ej: sistemas_operativos)")
):
    """Muestra los detalles y metadatos de una materia."""
    sub = load_subject(subject_id)
    console.print(Panel(
        f"[bold cyan]{sub.nombre}[/bold cyan] ({sub.codigo})\n"
        f"• Docente: {sub.docente}\n"
        f"• Tags: {', '.join(sub.tags)}",
        title=f"Perfil de Asignatura: {sub.codigo}",
        border_style="cyan"
    ))

# --- Subcomandos de Skills ---

@skills_app.command(name="list")
def list_skills_command():
    """Lista los skills para Agentes de IA provistos por Codex."""
    skills = list_skills()
    if not skills:
        console.print("[yellow]No se encontraron skills registrados en Codex.[/yellow]")
        return

    table = Table(title="Skills para Agentes de IA en Codex", border_style="cyan")
    table.add_column("Nombre del Skill", style="bold magenta")
    table.add_column("Descripción", style="white")
    table.add_column("Ruta SKILL.md", style="dim")

    for s in skills:
        table.add_row(s["name"], s["description"][:80] + "...", s["path"])

    console.print(table)
    console.print("\n[dim]Usa 'codex skills show <nombre>' para ver las instrucciones completas.[/dim]")

@skills_app.command(name="show")
def show_skill_command(
    skill_name: str = typer.Argument(..., help="Nombre del skill (ej: codex-academic)")
):
    """Muestra el contenido e instrucciones completas de un skill."""
    skill = get_skill(skill_name)
    if not skill:
        console.print(f"[bold red]Skill '{skill_name}' no encontrado.[/bold red]")
        raise typer.Exit(code=1)

    console.print(Panel(Markdown(skill["content"]), title=f"Skill: {skill['name']}", border_style="magenta"))

@skills_app.command(name="install")
def install_skills_command(
    target: Optional[Path] = typer.Option(None, "--target", "-t", help="Directorio destino (por defecto .agents/skills)")
):
    """Instala los skills de Codex en el workspace actual para que los Agentes de IA los descubran automáticamente."""
    try:
        installed = install_skills(target_dir=target)
        console.print(f"[bold green]✓ {len(installed)} skills instalados con éxito:[/bold green]")
        for p in installed:
            console.print(f"  • [accent]{p.parent.name}[/accent] -> {p}")
        console.print("\n[dim]Los Agentes de IA (Antigravity, Claude, etc.) ahora pueden usar estos skills.[/dim]")
    except Exception as e:
        console.print(f"[bold red]Error al instalar skills:[/bold red] {e}")
        raise typer.Exit(code=1)

# --- Subcomandos de Configuración ---

@config_app.command(name="check")
def check_config_command():
    """Diagnostica las dependencias del sistema, rutas de Obsidian y soporte de skills."""
    cfg = load_config()
    table = Table(title="Diagnóstico del Sistema Codex", border_style="cyan")
    table.add_column("Componente", style="bold")
    table.add_column("Estado", style="bold")
    table.add_column("Detalle", style="white")

    # 1. FFmpeg
    ffmpeg_bin, ffprobe_bin = find_ffmpeg_binaries()
    if ffmpeg_bin:
        table.add_row("FFmpeg", "[green]OK[/green]", ffmpeg_bin)
    else:
        table.add_row("FFmpeg", "[red]NO ENCONTRADO[/red]", "Instalar con winget install Gyan.FFmpeg.Essentials")

    # 2. Obsidian Vault
    if cfg.obsidian_vault_path.exists():
        table.add_row("Obsidian Vault", "[green]EXISTE[/green]", str(cfg.obsidian_vault_path))
    else:
        table.add_row("Obsidian Vault", "[yellow]CREARÁ EN PRIMER USO[/yellow]", str(cfg.obsidian_vault_path))

    # 3. Carpeta de Grabaciones OBS
    if cfg.obs_recordings_path.exists():
        table.add_row("Carpeta OBS", "[green]EXISTE[/green]", str(cfg.obs_recordings_path))
    else:
        table.add_row("Carpeta OBS", "[yellow]NO EXISTE[/yellow]", str(cfg.obs_recordings_path))

    # 4. Carpeta de Bundles para Agentes
    bundles_dir = get_bundles_dir(cfg)
    table.add_row("Bundles IA", "[green]LISTO[/green]", str(bundles_dir))

    # 5. Skills de Agentes
    skills = list_skills()
    table.add_row("Skills Registrados", "[green]OK[/green]", f"{len(skills)} skills ({', '.join(s['name'] for s in skills)})")

    console.print(table)

@config_app.command(name="show")
def show_config_command():
    """Muestra la configuración activa de Codex."""
    cfg = load_config()
    console.print(Panel(
        f"• Vault Obsidian: [accent]{cfg.obsidian_vault_path}[/accent]\n"
        f"• Subcarpeta Notas: {cfg.notes_subfolder}\n"
        f"• Subcarpeta Adjuntos: {cfg.attachments_subfolder}\n"
        f"• Carpeta OBS: [accent]{cfg.obs_recordings_path}[/accent]\n"
        f"• Carpeta Bundles IA: [accent]{get_bundles_dir(cfg)}[/accent]\n"
        f"• Audio: {cfg.audio.codec} @ {cfg.audio.sample_rate}Hz mono {cfg.audio.bitrate}\n"
        f"• Detección Diapositivas: diff_threshold={cfg.vision.diff_threshold}, min_interval={cfg.vision.min_interval_seconds}s",
        title="Configuración de Codex",
        border_style="cyan"
    ))

if __name__ == "__main__":
    app()
