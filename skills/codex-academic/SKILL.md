---
name: codex-academic
description: Transcribe y sintetiza grabaciones de clases universitarias (OBS, Google Meet, Zoom) en apuntes estructurados para Obsidian con callouts, tareas, fórmulas en LaTeX y diapositivas vinculadas mediante Codex.
---

# Skill: Codex Academic Notes Engine 🎓

Este skill le permite a un Agente de IA procesar grabaciones de clases académicas (video o audio), analizar el material visual y fonético, y generar apuntes universitarios estructurados de alto rendimiento para **Obsidian**.

---

## Cuándo Usar Este Skill
Usa este skill cuando:
- El usuario te solicite procesar una grabación de clase (ej. *"Toma la clase de Sistemas Operativos grabada con OBS y genera los apuntes"*).
- Quieras sintetizar o estructurar notas a partir de un archivo de video o audio con diapositivas.
- Quieras validar y exportar apuntes limpios directamente a la bóveda de Obsidian del usuario.

---

## Flujo de Trabajo del Agente (Paso a Paso)

### Paso 1: Preparar el Bundle de Sesión con Codex
Ejecuta la CLI de Codex para inspeccionar el medio, extraer la pista de audio optimizada (16kHz mono) y detectar cambios de diapositiva:

```bash
codex prepare "<ruta_al_video_o_audio>" --subject <nombre_o_codigo_materia> [--date AAAA-MM-DD]
```

**Resultado generado por Codex:**
Crea un paquete de trabajo en `.codex_bundles/<id_sesion>/` con:
- `manifest.json`: Metadatos técnicos, duración, asignaturas y lista de diapositivas con marcas de tiempo.
- `agent_context.md`: Instrucciones consolidadas y plantilla de la clase.
- `audio/lecture.opus`: Pista de audio optimizada para escucha y transcripción.
- `slides/slide_HHMMSS.png`: Capturas de pantalla deduplicadas correspondientes a cada cambio de diapositiva.

### Paso 2: Inspeccionar el Material
1. Lee `manifest.json` y `agent_context.md` en la carpeta del bundle para conocer los metadatos de la materia y la lista de diapositivas capturadas.
2. Revisa las imágenes en `slides/` (analiza diagramas, código en pantalla, fórmulas y títulos de diapositiva).
3. Analiza la pista de audio o su contenido fonético para transcribir y sintetizar las explicaciones del docente.

### Paso 3: Sintetizar los Apuntes para Obsidian
Redacta el contenido en Markdown siguiendo estrictamente estas pautas académicas:

1. **Frontmatter YAML:**
```yaml
---
materia: "<Nombre Asignatura>"
codigo: "<Código>"
fecha: YYYY-MM-DD
docente: "<Nombre Docente>"
estado: procesado
tags: [<tags_de_la_materia>]
---
```

2. **Título Principal:**
`# <Materia>: <Tema Central de la Sesión>`

3. **📌 Compromisos, Tareas y Avisos Administrativos:**
Extrae avisos de parciales, tareas, fechas de entrega y condiciones especiales:
`- [ ] [HH:MM:SS] Descripción de la asignación (Fecha límite: ...)`

4. **🧠 Conceptos Fundamentales y Advertencias de Examen:**
Utiliza los callouts nativos de Obsidian:
- `> [!tip] Concepto Clave: [Concepto]` definición y relevancia teórica.
- `> [!warning] Pista de Examen: [Punto enfatizado]` cuando el docente señale aspectos críticos o errores comunes.
- `> [!example] Demostración Práctica` ejemplos, demostraciones o casos prácticos.

5. **📝 Desarrollo Cronológico y Conceptual de la Clase:**
Organizado en bloques cronológicos con marca de tiempo:
`### [HH:MM:SS] [Subtema tratado]`
- **Vinculación Visual Obligatoria:** En el minuto exacto donde el profesor introduce o explica una diapositiva capturada, inserta su imagen con sintaxis de Obsidian: `![[slide_HHMMSS.png]]`.
- Describe los esquemas o código visibles en la diapositiva en correlación con el discurso oral.
- Escribe las fórmulas matemáticas en LaTeX (KaTeX: `$formula$` en línea o `$$formula$$` en bloque).
- Resalta fragmentos de código con el bloque correspondiente (`python`, `c`, `sql`, etc.).

6. **📜 Transcripción Indexada por Intervalos:**
Citas textuales o resumen fiel de lo expresado cada 2-3 minutos:
`> [HH:MM:SS] Texto transcrito o cita relevante...`

### Paso 4: Exportar a Obsidian
Guarda el borrador generado en `<bundle_dir>/notes.md` y ejecuta:

```bash
codex export "<bundle_dir>" "<bundle_dir>/notes.md"
```

Codex:
1. Validará el documento.
2. Copiará automáticamente todas las imágenes de diapositivas a la carpeta de adjuntos de Obsidian (`attachments/Codex/`).
3. Ubicará el apunte en la carpeta de la asignatura dentro de la bóveda (`Clases/<Materia>/AAAA-MM-DD - <Tema>.md`).
4. Actualizará el estado en `manifest.json` a `exported`.

### Paso 5: Confirmar al Usuario
Informa la finalización indicando la ruta del apunte generado en Obsidian, un breve resumen de los temas tratados y los compromisos detectados.
