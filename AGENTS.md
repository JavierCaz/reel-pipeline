# Content workspace

## Workspace map

- `Shorts/<project>/` contains one short-form video project (a reel). Create one with `npm run new-reel <Name>` from the repo root.
- `_shared/` contains the pipeline engine, the brand style, worked examples, and the optional music and sound downloads. Reuse shared files by path; do not duplicate them into projects.
- `_templates/short-template/` contains the starting structure and production guidance for educational reels.
- `_shared/pipeline/` is the reel pipeline engine (steps 1–9), shared by path. Projects hold only `reel.config.json` and `scripts/scenes.py` and run `npm run build -- <step>`. Its `docs/` hold the visual system and scene API, editorial rules, and lessons learned; read them before editing a reel.
- `_shared/examples/` holds the data of two finished reels (`reel.config.json` + `scenes.py`, no footage): `celular-escucha` (18 concept scenes, the main worked example) and `strategy` (presenter layouts and the light theme). Read them; do not run them.
- `scripts/` holds the cross-platform helpers: `setup.mjs` (`npm run setup`), `new-reel.mjs` (`npm run new-reel <Name>`), and `py.mjs` (finds Python on Windows, macOS and Linux for `npm run build`).

## Instruction layers

This file is the source of truth for the workspace; `CLAUDE.md` files only point here. Each layer refines the one above it, and a newer user instruction overrides all of them:

1. This file: workspace map, reel defaults, naming rules, tooling.
2. `_templates/short-template/AGENTS.md`: the production workflow, single-prompt mode, and visual/audio/render defaults; `_shared/pipeline/README.md` and `docs/` refine it with the engine, scene API, editorial rules, and lessons learned.
3. `Shorts/<project>/AGENTS.md`: project brief, decisions, build pipeline, and **current status**. Read it before working in a project.

## Who you are working with

The user may not be technical. Explain what you are doing in plain language, avoid jargon in the handoff, and give exact commands to copy when the user has to run something. Never ask the user to edit code; edit `reel.config.json` and `scripts/scenes.py` yourself from their feedback.

## Tooling: HyperFrames

Reels are HyperFrames projects: HTML compositions animated with GSAP and rendered to MP4.

- Invoke the HyperFrames skills before writing or editing compositions (`npm run setup` installs them). `/hyperframes` routes requests; `/hyperframes-core` defines the composition contract (`data-start`, `class="clip"`, one paused timeline on `window.__timelines`, deterministic logic only). Each project's `hyperframes.json` names its `authoringSkill`.
- Run these inside a project folder:

  ```bash
  npm run build -- all|rebuild|graphics  # regenerate the reel from reel.config.json + scripts/scenes.py
  npm run check                          # lint + runtime + layout + motion + contrast; run after every build
  npm run render                         # render to MP4 (final: renders/<topic>-reel-final.mp4); only after user approval
  npx hyperframes preview --background   # agent-safe Studio preview; verify with --status, stop with --stop
  npx hyperframes snapshot . -o .cache/<review> --at <t1,t2,...>   # still frames for review
  npx hyperframes transcribe ...         # local word-level transcription
  ```

- Project scripts pin an exact `hyperframes@X.Y.Z` so renders are reproducible. Do not bump the pin unless the user asks.
- Compositions are generated: edit `reel.config.json` or `scripts/scenes.py` and run `npm run build -- rebuild`; hand edits to generated HTML are overwritten. Generic improvements go into `_shared/pipeline/` (rebuild and diff the reels in `Shorts/` afterwards).
- `renders/`, `.cache/`, `.thumbnails/`, `.waveform-cache/`, and `.hyperframes/preview|backup` are generated and gitignored.

## Defaults for educational reels

Treat these as starting defaults, never as constraints over a newer user instruction or an approved project brief:

- Spanish narration by default (set `language` in `reel.config.json` for another language); TikTok, Instagram Reels, and YouTube Shorts; vertical 9:16, 1080×1920 at 30 fps; target 45–90 seconds.
- Preserve the original spoken performance. The recorded audio is authoritative; scripts and outlines are approximate. Verify technical terms and uncertain words against the audio.
- Keep original media intact. Make edits through source in/out ranges and preserve clip order as explicitly supplied. If order is unclear, infer from filenames/timestamps and confirm the opening clip before committing to the sequence; in single-prompt mode, timestamp order is accepted, so state it and continue.
- Do not invent facts, code, spoken words, explanatory labels, or visual assets that could change the topic's meaning. Ask or flag uncertainty.
- Visual style: the house "terminal" look (dark grid paper, lime `#b8ff35`, JetBrains Mono, hard shadows); see `_shared/brand/style.md`. New reels get it from the template. Its light variant (`visuals.theme: "terminal-light"`) is available when the brief or user asks for it; use another look only when the brief asks.
- Keep captions and graphics readable on a phone, inside the platform safe area, and clear of faces and controls. Use motion to clarify speech, not as decoration.
- For talking-head reels, default to near-continuous digital camera motion when the footage is otherwise static: give each clip a purposeful push, pullback, or lateral drift, use stronger short punches at selected emphasis beats, and vary direction and scale so the movement does not feel repetitive. Protect the face and hands at the tightest crop; use smooth, seek-safe framing animation rather than constant abrupt zooms.
- At real narrative section changes, default to footage-only transitions: move the outgoing crop into the cut, then let the incoming crop settle. Vary a small set of left/right swipes, zooms, short spins, and spin plus zoom in/out so the handoffs do not repeat mechanically. Keep each fast, the frame covered, and the face readable. Do not add transition words, title cards, color panels, or split-screen slides unless the user asks. Preserve audio timing and source ranges.
- Background music is on by default (`music.preset: "lofi"` at volume 0.2) when the user has downloaded it (see `_shared/music/README.md`); without it the build leaves the music out. Opening explosions and memes are off by default; use a meme only when the user approves it. Keep voice foremost; never let effects cover speech.
- Animation-led moments are part of the default edit: in 2–4 places where a diagram explains better than the face, the raw video shrinks into a floating card or a face square, or the animation takes the full screen (`stage` in `reel.config.json`; guidance in the template's step 6). Keep the hook and CTA on the full presenter. The presenter cutout effect is off unless the user asks for it.
- Every reel also gets a cover image (step 9, `npm run build -- cover` → `renders/<id>-cover.png`): title, an illustration in the reel's visual language, and a frame of the video.
- A single kickoff prompt (template in `_templates/short-template/README.md`) runs the whole workflow to a Studio preview without stopping between steps; review happens once at that preview, then feedback, then the final render. Without that prompt, review in short milestones.

## File and naming rules

- Keep original footage in `media/raw/` and treat it as read-only; use `media/images/` and `media/audio/` for project-only assets.
- Keep composition and media paths required by the chosen tool. Move active files only with all references updated and a successful render check.
- Put compositions in `src/` and helper scripts in `scripts/` when the renderer supports those paths; generated exports go in `renders/`, temporary output in `.cache/`.
- Use lowercase, hyphen-separated names for new reusable assets. Keep meaningful source filenames when their timestamps or provenance matter.
- Create new top-level workspace folders only when there is a clear workspace-level need.

## Starting a reel

Run `npm run new-reel <ProjectName>` from the repo root. It copies the template to `Shorts/<ProjectName>` and copies the HyperFrames sound effects and any optional music/sounds into its `media/audio/` (copies, not links, so it works on every OS). If the user left their clips somewhere else, copy them into `media/raw/`. Fill in its `AGENTS.md` with the topic, title/series number, one-sentence thesis, audience, platform, target length, approved clip order, visual references, and project-specific decisions. Inventory media before editing and preserve the source files.
