# Codex: Academic Notes Engine 🎓 (Soporte para Agentes de IA mediante Skills)

**Codex** es un motor de procesamiento multimodal para estudiantes universitarios diseñado específicamente para trabajar en conjunto con **Agentes de IA** (como Google Antigravity, Claude Code, Cursor, etc.) a través de **Skills**.

A diferencia de los sistemas tradicionales que dependen de llamadas a APIs externas de modelos con claves de API y costos asociados, **Codex opera de forma local y limpia**: realiza el análisis de medios (audio y detección de diapositivas), empaqueta el contexto académico para el agente y exporta los apuntes resultantes estructurados en formato **Markdown para Obsidian**.

---

## ⚡ Flujo de Trabajo con Agentes de IA

```
[Grabación OBS / Google Meet / Zoom (Video o Audio)]
                     │
                     ▼
             [Codex Prepare / Watcher]
                     │
         ┌───────────┴───────────┐
         ▼                       ▼
    FFmpeg Audio          Visión Perceptual
  (16kHz mono Opus)      (Detección de Diapositivas)
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
           [Lecture Session Bundle]
   ├── manifest.json      (Metadatos técnicos y marcas de tiempo)
   ├── agent_context.md   (Instrucciones estructuradas para el Agente)
   ├── audio/lecture.opus (Pista de voz optimizada)
   └── slides/slide_*.png (Capturas deduplicadas con timestamps)
                     │
                     ▼
      [Agente de IA (Vía Skill: codex-academic)]
   (Transcribe, sintetiza y redacta la nota académica para Obsidian)
                     │
                     ▼
             [Codex Export]
   (Valida notas, traslada adjuntos e inserta en la Bóveda de Obsidian)
                     │
                     ▼
          [Bóveda de Obsidian]
   ├── Notas:   Vault/Clases/<Materia>/YYYY-MM-DD - Tema.md
   └── Slides:  Vault/attachments/Codex/slide_HHMMSS.png
```

---

## 🚀 Requisitos e Instalación

### 1. Requisitos del Sistema
- **Python 3.10+** (probado en Python 3.13)
- **FFmpeg** (detectado automáticamente por Codex)
- **Un Agente de IA** (ej. Antigravity, Claude Code, etc.) que use skills

> [!NOTE]
> Codex **no requiere claves de API de modelos ni peticiones de red**. Toda la inferencia es realizada directamente por tu Agente de IA preferido utilizando los skills provistos.

### 2. Instalación en Entorno Virtual
```bash
# Crear entorno virtual
python -m venv .venv

# Activar en Windows PowerShell
.\.venv\Scripts\Activate.ps1

# Instalar dependencias y CLI de Codex en modo editable
pip install -e . pytest
```

### 3. Configuración de Rutas (`config.yaml`)
Abre `config.yaml` y define la ruta a tu bóveda de Obsidian y carpeta de grabaciones:
```yaml
# Ruta a tu Vault de Obsidian
obsidian_vault_path: "C:/Users/TuUsuario/Documents/Obsidian/Universidad"

# Subcarpetas en el Vault
notes_subfolder: "Clases"
attachments_subfolder: "attachments/Codex"

# Carpeta donde OBS guarda las grabaciones (.mkv, .mp4, etc.)
obs_recordings_path: "C:/Users/TuUsuario/Videos"

# Carpeta donde se generan los bundles para los agentes
bundles_path: ".codex_bundles"
```

---

## 🤖 Skills para Agentes de IA

Codex incluye especificaciones de skills compatibles con los estándares de agentes (`SKILL.md`):

1. **`codex-academic`:**
   Guía al Agente de IA paso a paso para inspeccionar el bundle preparado, analizar las diapositivas y el audio, redactar los apuntes con callouts, tareas, LaTeX y vincular visualmente las diapositivas en los minutos correspondientes.
2. **`codex-study-guide`:**
   Guía al agente para generar hojas de trucos para exámenes, tarjetas de repaso activo (flashcards) y cuestionarios de autoevaluación basados en las clases registradas.

### Instalar Skills en tu Workspace
Para que los agentes descubran automáticamente las capacidades de Codex:
```bash
# Instala los skills en .agents/skills/ del proyecto
codex skills install
```

---

## 💻 Uso de la CLI

### 1. Diagnóstico del Sistema
Comprueba que FFmpeg, rutas de Obsidian y los skills estén listos:
```bash
codex config check
```

### 2. Preparar una Clase para el Agente
Extrae audio, detecta diapositivas y crea el paquete de trabajo para el Agente:
```bash
codex prepare "C:/Videos/clase_so.mkv" --subject sistemas_operativos
```
Esto generará una carpeta en `.codex_bundles/<id_sesion>/` con todo lo necesario para que el Agente de IA proceda.

### 3. Exportar los Apuntes del Agente a Obsidian
Una vez que el Agente de IA redacte la nota en Markdown:
```bash
codex export ".codex_bundles/<id_sesion>" ".codex_bundles/<id_sesion>/notes.md"
```
Codex:
- Copia las diapositivas a `attachments/Codex/`.
- Inserta la nota en `Clases/<Materia>/YYYY-MM-DD - Tema.md`.
- Actualiza el estado del paquete a `exported`.

### 4. Modo Daemon Automático (Watcher)
Deja el daemon en ejecución en segundo plano mientras asistes a tu clase. Al pulsar **"Detener grabación" en OBS**, Codex detectará que el archivo se cerró y creará automáticamente el paquete listo para el Agente:
```bash
codex watch --subject sistemas_operativos
```

### 5. Administrar Asignaturas y Skills
```bash
# Listar asignaturas disponibles
codex subjects list

# Ver metadatos de una materia
codex subjects info sistemas_operativos

# Listar skills de Agentes de IA
codex skills list

# Ver contenido de un skill
codex skills show codex-academic
```

---

## 📓 Formato de los Apuntes en Obsidian

La estructura que el skill `codex-academic` guía al agente a producir incluye:
1. **Frontmatter YAML:**
   ```yaml
   ---
   materia: "Sistemas Operativos"
   codigo: "SO-301"
   fecha: 2026-11-05
   docente: "Prof. Rodríguez"
   estado: procesado
   tags: [universidad, ingenieria, sistemas-operativos]
   ---
   ```
2. **Callouts nativos de Obsidian:**
   - `> [!tip] Concepto Clave`
   - `> [!warning] Pista de Examen`
   - `> [!example] Demostración Práctica`
3. **Checklists de Compromisos y Tareas:**
   - `- [ ] [00:42:15] Entrega del laboratorio de semáforos (Fecha límite: 12 de Noviembre)`
4. **Diapositivas y Pizarras Vinculadas:**
   - Se incrustan como `![[slide_HHMMSS.png]]` exactamente en el momento temporal donde el profesor las discutió.
5. **Fórmulas Matemáticas en LaTeX:**
   - `$E = mc^2$` o bloques `$$...$$`.
6. **Transcripción / Citas Indexadas:**
   - Marcas de tiempo cada 2-3 minutos (`> [00:03:00] ...`).

---

## 🧪 Pruebas Automatizadas

El proyecto cuenta con una suite completa de pruebas unitarias y de integración (FFmpeg, visión perceptual, bundles, exportador, skills y CLI):
```bash
pytest -v
```
