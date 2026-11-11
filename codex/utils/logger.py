"""Módulo de Logging estilizado con Rich para Codex."""

import logging
from rich.console import Console
from rich.logging import RichHandler
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
    "accent": "bold magenta",
})

console = Console(theme=custom_theme)

def get_logger(name: str = "codex") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = RichHandler(
            console=console,
            show_time=True,
            show_path=False,
            rich_tracebacks=True,
            markup=True
        )
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = get_logger("codex")
