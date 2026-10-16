# Short project starter

Create a reel from the repo root with `npm run new-reel <ProjectName>`: it copies this folder to `Shorts/<ProjectName>` together with the sound effects (and any optional music you downloaded). Then add the clips to `media/raw/`, and let the agent fill in `AGENTS.md` and `reel.config.json`. The pipeline engine lives in `_shared/pipeline/` (`npm run build -- all`); the project only holds `reel.config.json` and `scripts/scenes.py`. The template already carries the HyperFrames config (`package.json` with the pinned version, `hyperframes.json`). Update this starter when a workflow has been proven in a real project.

## Single-prompt kickoff

Put the clips in the reel's `media/raw/` folder (or anywhere, and give the path), fill in the brackets, and paste the prompt into Claude Code opened at the repo root. Delete optional lines you don't need. The agent runs all eight steps (trim, join, camera motion, transitions, subtitles, diagrams with animation-led moments, SFX, music) plus the cover image, then stops at a Studio preview for your review. It renders only after you approve.

### Español

```text
Crea un nuevo reel en Shorts/<NombreProyecto> (con `npm run new-reel <NombreProyecto>` si aún no existe)
y ejecuta el flujo completo en modo de un solo prompt (pasos 1–8 de _templates/short-template/AGENTS.md).

- Clips: Shorts/<NombreProyecto>/media/raw (orden: por nombre de archivo / <orden explícito>)
- Tema: <tema>
- Título en pantalla (exacto): "<título>"
- Tesis en una frase: <idea principal>
- Público: <audiencia>
- Plataforma: <Instagram Reels / TikTok / YouTube Shorts>
- Duración objetivo: <p. ej. 60–90 s>
- Secciones / guion aproximado: <lista de ideas en orden, o pega aquí tu guion>
- Estilo visual: <opcional; por defecto el estilo "terminal" oscuro. "terminal-light" para el claro, u otras referencias>
- Música: <"la de siempre" (lofi, si la descargaste) o "sin música">
- Final: mi nombre es <tu nombre>, mis redes son <@usuario en Instagram/TikTok…> y mi sitio es <sitio, opcional>
- Notas: <términos técnicos difíciles, cosas que evitar>
- Momentos clave: <frases que deben tener más énfasis, opcional>
- Momentos de animación: <opcional: partes donde la animación debe ser protagonista; si se omite, el agente elige 2–4>

Al terminar, abre el preview de Studio y dame la lista de puntos a revisar. No renderices hasta que lo apruebe.
```

### English

```text
Create a new reel in Shorts/<ProjectName> (with `npm run new-reel <ProjectName>` if it doesn't exist yet)
and run the whole workflow in single-prompt mode (steps 1–8 of _templates/short-template/AGENTS.md).

- Clips: Shorts/<ProjectName>/media/raw (order: by file name / <explicit order>)
- Language of the narration: English
- Topic: <topic>
- On-screen title (exact): "<title>"
- One-sentence thesis: <main idea>
- Audience: <audience>
- Platform: <Instagram Reels / TikTok / YouTube Shorts>
- Target length: <e.g. 60–90 s>
- Sections / rough script: <list of ideas in order, or paste your script here>
- Visual style: <optional; dark "terminal" style by default, "terminal-light" for the light one, or other references>
- Music: <"the usual" (lofi, if you downloaded it) or "no music">
- End card: my name is <your name>, my handles are <@handle on Instagram/TikTok…> and my site is <site, optional>
- Notes: <hard technical terms, things to avoid>
- Key moments: <phrases that need extra emphasis, optional>
- Animation moments: <optional: parts where the animation should lead; if omitted, the agent picks 2–4>

When you finish, open the Studio preview and give me the list of things to review. Don't render until I approve.
```
