---
name: codex-study-guide
description: Genera guías de estudio para exámenes, tarjetas de repaso activo (flashcards) y cuestionarios de autoevaluación a partir de clases procesadas con Codex en Obsidian.
---

# Skill: Codex Study Guide Generator 📚

Este skill le permite a un Agente de IA analizar las notas de clase y diapositivas generadas con Codex en una bóveda de Obsidian para crear material de estudio y repaso activo de alto rendimiento.

---

## Cuándo Usar Este Skill
Usa este skill cuando:
- El usuario solicite preparar un examen o parcial de una materia procesada con Codex.
- Quieras generar un resumen de conceptos clave y advertencias docentes.
- Quieras crear tarjetas de memoria (flashcards) en formato compatible con Obsidian Spaced Repetition o Anki.

---

## Flujo de Trabajo

### Paso 1: Localizar los Apuntes de la Materia
Consulta las notas generadas en el Vault de Obsidian (`Clases/<Materia>/`) o el bundle correspondiente en `.codex_bundles/`.

### Paso 2: Generar el Material de Estudio
Crea un nuevo documento de estudio con las siguientes 3 secciones:

1. **Hoja de Trucos / Resumen de Examen (Exam Cheat Sheet):**
   - Tabla o lista de todas las advertencias marcadas con `> [!warning] Pista de Examen`.
   - Formulario de ecuaciones matemáticas y teoremas con notación LaTeX.
   - Definiciones rigurosas de los `> [!tip] Concepto Clave`.

2. **Tarjetas de Repaso Activo (Flashcards):**
   Formato de una o dos líneas para plugins de Obsidian Flashcards:
   ```markdown
   ¿Qué es la condición de carrera en Sistemas Operativos? #flashcard
   Es una situación en la que varios procesos acceden y manipulan datos compartidos concurrentemente, y el resultado depende del orden de ejecución.
   ```

3. **Cuestionario de Autoevaluación:**
   - 5 preguntas conceptuales y prácticas.
   - Respuestas explicadas al final con referencia cruzada al minuto de la clase donde se explicó.

### Paso 3: Guardar en la Bóveda
Guarda la guía en la bóveda de Obsidian bajo:
`Clases/<Materia>/Guías de Estudio/AAAA-MM-DD - Guía de Examen - <Tema>.md`
