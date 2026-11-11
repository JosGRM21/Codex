"""Módulo para empaquetado de sesiones académicas (bundles) e insumos para Agentes de IA."""

import datetime
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Any, List, Optional

from codex.config import AppConfig, SubjectConfig, load_config
from codex.core.media import MediaInspector, extract_audio
from codex.core.vision import SlideExtractor, SlideFrame
from codex.utils.logger import logger
from codex.utils.time_format import seconds_to_hhmmss

@dataclass
class LectureBundle:
    """Representa el paquete de trabajo de una clase académica para ser procesado por un Agente de IA."""
    bundle_id: str
    bundle_dir: Path
    manifest_path: Path
    agent_context_path: Path
    audio_path: Optional[Path]
    slides_dir: Path
    slides: List[SlideFrame]
    subject: SubjectConfig
    class_date: str
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la información del bundle para manifest.json."""
        slides_data = [
            {
                "timestamp_seconds": s.timestamp_seconds,
                "time_str": s.time_str,
                "tag": s.tag,
                "filename": s.file_path.name,
                "relative_path": f"slides/{s.file_path.name}",
            }
            for s in self.slides
        ]

        audio_rel_path = (
            f"audio/{self.audio_path.name}"
            if self.audio_path and self.audio_path.exists()
            else None
        )

        return {
            "version": "1.0",
            "bundle_id": self.bundle_id,
            "created_at": self.metadata.get("created_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
            "class_date": self.class_date,
            "subject": self.subject.model_dump(),
            "media_info": self.metadata.get("media_info", {}),
            "audio": {
                "file": audio_rel_path,
                "absolute_path": str(self.audio_path) if self.audio_path else None,
            },
            "slides_count": len(self.slides),
            "slides": slides_data,
            "status": self.metadata.get("status", "ready_for_agent"),
            "exported_note_path": self.metadata.get("exported_note_path"),
        }

    def save_manifest(self) -> Path:
        """Escribe o actualiza el manifest.json en el directorio del bundle."""
        data = self.to_dict()
        with open(self.manifest_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return self.manifest_path

    def generate_agent_context(self) -> str:
        """
        Genera el contenido de agent_context.md con todas las instrucciones,
        metadatos y especificaciones de formato que el Agente de IA necesita.
        """
        duration_sec = self.metadata.get("media_info", {}).get("duration", 0.0)
        duration_str = seconds_to_hhmmss(duration_sec)
        tags_str = ", ".join(self.subject.tags)

        slides_lines = []
        if self.slides:
            for s in self.slides:
                slides_lines.append(
                    f"| `{s.time_str}` | `![[{s.file_path.name}]]` | `{s.file_path.name}` |"
                )
            slides_table = "\n".join(slides_lines)
        else:
            slides_table = "_No se detectaron diapositivas visuales (sesión solo de audio o sin cambios de pantalla)._"

        audio_ref = f"`{self.audio_path.name}`" if self.audio_path else "_No disponible_"

        context_md = f"""# Contexto de Clase Académica para Agente de IA

Este documento ha sido preparado por **Codex** para que un Agente de IA (utilizando el skill `codex-academic`) procese los medios y sintetice apuntes universitarios estructurados para Obsidian.

---

## 1. Metadatos de la Sesión
- **Asignatura:** {self.subject.nombre} ({self.subject.codigo})
- **Docente:** {self.subject.docente}
- **Fecha:** {self.class_date}
- **Duración Estimada:** {duration_str}
- **Pista de Audio Optimizada:** {audio_ref}
- **Diapositivas Extraídas:** {len(self.slides)} capturas clave

---

## 2. Diapositivas Detectadas (con marcas de tiempo)
| Timestamp | Sintaxis de Inserción Obsidian | Archivo en `slides/` |
|---|---|---|
{slides_table}

---

## 3. Instrucciones y Estructura Estricta para Obsidian

Como Agente de IA, tu tarea es analizar el audio y las diapositivas de la sesión para generar un apunte académico completo en Markdown puro con la siguiente estructura:

### A. Frontmatter YAML
```yaml
---
materia: "{self.subject.nombre}"
codigo: "{self.subject.codigo}"
fecha: {self.class_date}
docente: "{self.subject.docente}"
estado: procesado
tags: [{tags_str}]
---
```

### B. Título Principal
`# {self.subject.nombre}: [Título descriptivo del tema abordado en clase]`

### C. 📌 Compromisos, Tareas y Avisos de Evaluación
Detecta anuncios de parciales, entregas, lecturas obligatorias o prácticas de laboratorio:
- `- [ ] [HH:MM:SS] Descripción del compromiso (Fecha límite / condición)`

### D. 🧠 Conceptos Clave y Advertencias de Examen
Utiliza callouts nativos de Obsidian:
- `> [!tip] Concepto Clave: [Nombre]` seguido de la definición formal y relevancia.
- `> [!warning] Pista de Examen: [Punto enfatizado]` para alertas explícitas del docente.
- `> [!example] Demostración Práctica` para ejemplos o código desarrollado.

### E. 📝 Desarrollo Cronológico y Conceptual
Organiza las secciones temáticas cronológicamente:
`### [HH:MM:SS] [Subtema]`
- Vinculación visual: En el minuto donde se discute cada diapositiva, inserta la imagen: `![[slide_HHMMSS.png]]`.
- Utiliza fórmulas matemáticas en LaTeX (KaTeX: `$formula$` o `$$formula$$`).
- Bloques de código con resaltado de sintaxis si aplica.

### F. 📜 Transcripción o Citas Textuales Indexadas
Párrafos o citas representativas cada 2-3 minutos:
`> [HH:MM:SS] Explicación textual o resumen fiel...`

---

## 4. Finalización y Exportación

Una vez redactado el apunte en un archivo (por ejemplo `{self.bundle_dir.name}/apuntes.md`), ejecuta:
```bash
codex export "{self.bundle_dir}" "{self.bundle_dir / 'apuntes.md'}"
```
Codex validará la nota, copiará automáticamente las diapositivas referenciadas a la carpeta de adjuntos de Obsidian y guardará la nota final en la ruta correspondiente de la materia.
"""
        return context_md.strip() + "\n"

    def save_agent_context(self) -> Path:
        """Escribe agent_context.md en el directorio del bundle."""
        content = self.generate_agent_context()
        with open(self.agent_context_path, "w", encoding="utf-8") as f:
            f.write(content)
        return self.agent_context_path

def create_lecture_bundle(
    media_path: Path,
    subject: SubjectConfig,
    class_date: str,
    output_base_dir: Optional[Path] = None,
    config: Optional[AppConfig] = None
) -> LectureBundle:
    """
    Procesa un archivo de video/audio de clase y crea el paquete estructurado (bundle)
    listo para que un Agente de IA lo analice mediante skills.
    """
    cfg = config or load_config()
    media_path = Path(media_path).resolve()
    
    if not media_path.exists():
        raise FileNotFoundError(f"El archivo de medios no existe: {media_path}")

    # Identificador seguro y limpio
    safe_slug = re.sub(r'[^a-zA-Z0-9_-]', '_', subject.codigo.lower())
    clean_stem = re.sub(r'[^a-zA-Z0-9_-]', '_', media_path.stem)
    bundle_id = f"{class_date}_{safe_slug}_{clean_stem}"

    # Directorio base de bundles
    base_dir = output_base_dir or cfg.bundles_path
    if not base_dir.is_absolute():
        base_dir = Path.cwd() / base_dir

    bundle_dir = base_dir / bundle_id
    audio_dir = bundle_dir / "audio"
    slides_dir = bundle_dir / "slides"

    bundle_dir.mkdir(parents=True, exist_ok=True)
    audio_dir.mkdir(parents=True, exist_ok=True)
    slides_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = bundle_dir / "manifest.json"
    agent_context_path = bundle_dir / "agent_context.md"

    # 1. Inspección técnica de medios
    media_info = MediaInspector.get_video_info(media_path)
    media_info["source_path"] = str(media_path)
    media_info["filename"] = media_path.name

    # 2. Extracción de audio optimizado (16kHz mono)
    audio_output = audio_dir / f"lecture{cfg.audio.extension}"
    extract_audio(media_path, audio_output, cfg.audio)

    # 3. Extracción y deduplicación de diapositivas
    slide_extractor = SlideExtractor(cfg.vision)
    slides = slide_extractor.extract_slides(media_path, slides_dir)

    metadata = {
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "media_info": media_info,
        "status": "ready_for_agent",
    }

    bundle = LectureBundle(
        bundle_id=bundle_id,
        bundle_dir=bundle_dir,
        manifest_path=manifest_path,
        agent_context_path=agent_context_path,
        audio_path=audio_output,
        slides_dir=slides_dir,
        slides=slides,
        subject=subject,
        class_date=class_date,
        metadata=metadata,
    )

    bundle.save_manifest()
    bundle.save_agent_context()

    logger.info(
        f"[success]Bundle para Agente de IA generado:[/success] [accent]{bundle_dir}[/accent]"
    )
    return bundle

def load_lecture_bundle(bundle_dir_or_manifest: Path) -> LectureBundle:
    """Carga un LectureBundle existente a partir de su carpeta o archivo manifest.json."""
    p = Path(bundle_dir_or_manifest).resolve()
    if p.is_dir():
        manifest_file = p / "manifest.json"
    else:
        manifest_file = p
        p = manifest_file.parent

    if not manifest_file.exists():
        raise FileNotFoundError(f"No se encontró manifest.json en: {p}")

    with open(manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    subject = SubjectConfig(**data.get("subject", {}))
    class_date = data.get("class_date", "1970-01-01")
    bundle_id = data.get("bundle_id", p.name)
    agent_context_path = p / "agent_context.md"

    # Reconstruir diapositivas
    slides_dir = p / "slides"
    slides = []
    for s_item in data.get("slides", []):
        img_path = p / s_item.get("relative_path", f"slides/{s_item.get('filename')}")
        slides.append(SlideFrame(
            timestamp_seconds=float(s_item.get("timestamp_seconds", 0.0)),
            time_str=s_item.get("time_str", "00:00:00"),
            file_path=img_path,
            tag=s_item.get("tag", "000000")
        ))

    # Reconstruir audio
    audio_info = data.get("audio", {})
    audio_path = None
    if audio_info.get("file"):
        audio_path = p / audio_info["file"]
    elif audio_info.get("absolute_path"):
        audio_path = Path(audio_info["absolute_path"])

    metadata = {
        "created_at": data.get("created_at"),
        "media_info": data.get("media_info", {}),
        "status": data.get("status", "ready_for_agent"),
        "exported_note_path": data.get("exported_note_path"),
    }

    return LectureBundle(
        bundle_id=bundle_id,
        bundle_dir=p,
        manifest_path=manifest_file,
        agent_context_path=agent_context_path,
        audio_path=audio_path,
        slides_dir=slides_dir,
        slides=slides,
        subject=subject,
        class_date=class_date,
        metadata=metadata,
    )
