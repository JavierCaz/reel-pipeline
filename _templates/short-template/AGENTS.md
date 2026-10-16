# Educational reel production guide

Use this as the default for programming and educational talking-head reels. A newer user instruction or approved brief overrides a default. Record project-specific choices under the project brief/status below.

The process was proven on more than ten finished reels. It is implemented by the shared engine in `_shared/pipeline/`: a project holds only data, `reel.config.json` plus `scripts/scenes.py`, and runs `npm run build -- <step>`. Worked examples (data only): `_shared/examples/`. Read before starting: `_shared/pipeline/README.md`, `docs/editorial-rules.md`, `docs/visual-system.md`, `docs/lessons-learned.md`.

## Project brief

- Topic / title / series number: fill in
- On-screen opening title (exact text): fill in
- One-sentence thesis and audience: fill in
- Platform(s): TikTok, Instagram Reels, YouTube Shorts (choose)
- Language: Spanish by default
- Format: vertical 9:16, 1080×1920, 30 fps by default
- Target duration: 45–90 seconds by default; the recorded speech decides the final length
- Clip folder and approved order: fill in; identify the opening clip
- Section outline: the ideas in order (from a script, outline, or the transcript)
- References: optional visual references, palette, mascot, topic diagrams
- Music track: `_shared/music/velariomusic-lofi-relaxing-598427.mp3` unless the brief names another or says no music
- Current status / TODOs / quirks: keep current (pipeline data lives in `reel.config.json`; record only decisions and status here)

## Single-prompt mode

A single kickoff prompt (template in `README.md`) authorizes the agent to run steps 1–8 below end to end without stopping between steps. In this mode:

- Stop **before** step 1 only if the clip order is unclear, required media is missing, or the brief lacks the topic or opening title. If clips are named by timestamp, ascending filename order is the default; state it and continue.
- Do not stop between steps for approval. Instead, after each step run `npm run check`, take snapshots of representative frames into `.cache/<step>-review/`, look at them, and fix problems before moving on.
- Do not invent facts, words, or labels. When a technical term in the audio, a section boundary, or a diagram claim is uncertain, make the conservative choice, keep going, and list it under "Needs your review" in the handoff.
- Finish with one handoff: the cover PNG (step 9), a Studio preview (`npx hyperframes preview --background`, verified with `--status`), a short summary per step, the "Needs your review" list, and updated project status in `AGENTS.md`. **Do not render** until the user approves the preview.
- Apply review feedback by editing `reel.config.json` or `scripts/scenes.py` and running `npm run build -- rebuild`, then render with `npm run render`. If feedback reveals a general preference, record it in `_shared/pipeline/docs/editorial-rules.md`.

## Editorial and source rules

- Preserve the speaker's original voice and meaning. Recorded audio is the source of truth; scripts are approximate guides.
- Preserve original media in `media/raw/`. Never overwrite or destructively edit source footage. Make trims through explicit source in/out points and keep a cut map.
- Keep the supplied order. If no order is supplied, use filename or timestamp order and say so.
- Do not invent facts, code, spoken words, subtitles, diagram states, or visual assets that change the explanation. Verify technical terms against the recording.
- Named technologies, tools and brands show their official icon beside the name (user, 2026-10-13); see `docs/editorial-rules.md`.

## Production workflow

Steps follow the user's editing order. Steps 1–2 produce the cut; everything after is timed in **cut-timeline seconds**, so a cut change means regenerating transcript, captions, visuals, and SFX downstream.

0. **Setup and inventory:** `npm run new-reel <project>` from the repo root (copies the template plus the bundled and optional sounds into the reel; HyperFrames rejects `../` paths above the project root, so media must live inside it). The copy already has `package.json` (pinned `hyperframes@X.Y.Z`, `build`, and the render flag), `hyperframes.json`, the bundled SFX in `media/audio/sfx/`, a starter `reel.config.json`, and `scripts/scenes.py`. Put footage in `media/raw/`, then set `id`, `visual_prefix`, `title`, `opening_title`, and the palette in `reel.config.json`. List every clip's duration, dimensions, rotation tag, fps, and audio; phone clips are often stored 1920×1080 with a −90° rotation and must display as portrait.
1. **Trim heads and tails** (`build boundaries`, `cut`; config `trim`): measure speech edges per clip from audio energy (20 ms RMS windows, activity above −28 dB, strong speech above −16 dB peak). Cut about 80 ms before the first strong speech and 100 ms after the last, aligned to frames, so sighs, breaths, and handling noise go but soft consonants stay. Observer's manual audit found 50–90 ms pre-roll is the safe range. Keep breaths inside phrases. Fix individual edges with `trim.overrides` and give the reason.
2. **Join the clips:** assemble every clip in order as a muted `<video>` plus a separate `<audio>` with identical source ranges, and write `scripts/cut-map.json` (source in/out ↔ timeline in/out, total duration). Then transcribe each clip locally (`build transcribe`; per clip, because Parakeet drifts on long audio; cached), proofread joined words, accents, and technical terms against the audio with fixes keyed by clip and ASR word (`transcript_fixes`, `build review`), producing `scripts/transcript.json`. Map the section outline onto clip boundaries from the actual speech.
3. **Camera motion:** give every clip a purposeful push, pullback, or lateral drift, with several beats on long clips and stronger short punches on emphasis words. Scale range about 1.02–1.14, alternating direction and scale between neighbours. Protect face and hands at the tightest crop. Open clip 1 with a short decaying shake (about 1.40–1.43× covered crop, alternating offsets and small tilts, settled by about 0.7 s). Data: config `camera` (emphasis words → `hit`/`punch`/`push`/`pull`/`step`) and `opening`; `build camera` writes `scripts/camera-moves.json`.
4. **Transitions:** only at real section changes (IAExplicacion used 9 in about 3 minutes). Footage-only handoffs: the outgoing crop accelerates into the cut, the incoming one settles after it. Rotate `swipe`, `swipe-reverse`, `zoom`, `spin`, `spin-zoom-in`, `spin-zoom-out` so neighbours never repeat. No words, cards, color panels, or split screens. A brief's "hard cut" is `kind: hard-cut` with an `initial_scale` jump in `camera`. Data: config `transitions`; poses and timings live in `_shared/pipeline/presets.py`.
5. **Subtitles:** one caption track of short centered phrases (at most about 5 words, 34 characters, 2.25 s; never one-word flashes) over the presenter's lower torso inside the 80% title-safe box. Small rise/side entrances, soft dark outline, readable from the first frame. Emphasize only a few technical keywords per project with the accent color and a fine underline. Do not rewrite the speaker. Data: config `captions`; `build captions` writes `src/captions.html`, `scripts/caption-cues.json`, `scripts/subtitulos.srt`.
6. **Diagrams, animations, motion graphics:** first, an opening title over clip 1 with the exact title from the brief, cleared before clip 2. Then one concept scene per idea in the upper 45–55% of the frame, built step by step on the words that introduce each element (`T("phrase", after)` lookups in `transcript.json`), with clear entrances and exits and small explanatory motions (sorting, flow dots, gear spin, needle swing, typing dots). Before animating a scene, define its entities, actions, and results so arrows and states are accurate. Write the scenes in `scripts/scenes.py` (scene 00 is the opening title; API, layout zones, and error fixes in `_shared/pipeline/docs/visual-system.md`; example `_shared/examples/celular-escucha/scenes.py`) and run `build graphics`. The engine rejects overlapping tweens and tweens past a scene's end, so retime the beat instead of loosening the check. Brief-requested graphic transitions (collapse, merge, expand) live inside scenes. **Real images** (user, 2026-10-13): introduce real objects and places with a real photo (`s.photo`, sources and credits in `media/images/SOURCES.md`), then switch to the animated drawing; rules in `docs/editorial-rules.md` "Real images".

   **Animation-led moments (presenter layouts, config `stage`).** Part of step 6 by default: pick 2–4 moments where a diagram carries the explanation better than the face (a map, a code diagram, a multi-step flow) and let the animation lead:
   - `card`: the raw video shrinks into a floating card (bottom right) beside a large diagram. Use for examples with several elements (Strategy's map app).
   - `square` (**default face layout**, user 2026-10-08): the face in a 400 px square card (bottom **left**, user 2026-10-09: the platform buttons are on the right), cropped tight (640 px) and centred on the measured face so the chin stays in. Use whenever the graphics need most of the frame but the speaker should stay present (SitioWeb's site screenshots).
   - `circle`: the older face layout (a 340 px circle); it filled the space worse and cut the chin. Use only on request.
   - `takeover`: the animation takes the full screen and the presenter leaves. Use only when the scene genuinely fills the frame for its whole duration; a half-empty takeover feels blank (user feedback 2026-10-06: Strategy clip 9 was changed to `circle`).
   - Neighbouring moments must be contiguous (≤ 0.6 s apart) so the presenter morphs straight from one layout to the next; never grow back to full screen only to shrink again (user feedback 2026-10-06). Start the next moment on the first word of its clip when needed.
   - Keep the hook, priority lines delivered to camera, and the CTA on the full presenter. Aim for roughly 20–35 % of the runtime; a stretch longer than ~30 s without the full camera should be flagged in the handoff.
   - Scenes during a layout use the whole frame above the captions (y 150–1300) and stay clear of the square (bottom left: x 60–460, y 905–1305), card (x 620–1020, y 905–1305) or circle (x 700–1040, y 960–1300); read the resolved times from `STAGE` in `scenes.py`.
   - `npm run build -- matte` (part of `all`) measures the face centre per moment so the crop is centred; override with `"region"` or `"focus"` if a moment still looks off.
   - `cutout` (presenter matted out of the room, graphics behind them) exists in the engine but is **not used by default**: it produced visible artefacts in Strategy and the user removed it (2026-10-06). Use it only on explicit request.
   Geometry, timing, and examples: `docs/visual-system.md` "Presenter layouts"; worked example `_shared/examples/strategy/` (`stage` in its `reel.config.json`, scenes 03b–05).
7. **Sound effects:** a transition sound per handoff with its peak on the cut, rotating by kind (page turn for swipes, flame whoosh for spin-zooms, `transition-sfx-2` and whoosh for zooms) at about volume 0.3; an opening whoosh under the shake; subtle diagram SFX (pop, click, key taps, ping, chime) synced to on-screen actions with peaks about 12 dB under speech. Bundled HyperFrames SFX are copied to `media/audio/sfx/` with `CREDITS.md`. Data: `sound` in config `transitions`/`opening` (presets in `presets.py`) and `s.sfx()` / `enter(..., sfx)` calls in `scenes.py`.
8. **Background music:** the brief's track, unedited, under the whole reel at volume 0.2 (about 19 dB under the voice). If it is shorter than the reel it restarts from its beginning; only the last 1.2 s fades out. Data: config `music`. Music never masks speech.

9. **Cover image:** `npm run build -- cover` renders `renders/<id>-cover.png`: the video title (config `cover`: `kicker`, `title` lines, `subtitle`), an illustration (`def cover(c)` in `scripts/scenes.py`, drawn with the scene helpers; usually the reel's key concept), and an expressive still from the video (`cover.frame`). Details in `docs/visual-system.md`.

Then run the final check (`npm run check`), snapshot every section, transition, and the close, and hand off as described in "Single-prompt mode".

## Pipeline engine

Everything above is implemented in `_shared/pipeline/` (usage, config schema, and track layout in its `README.md`). Typical loop:

```bash
npm run build -- all        # first run, steps 1–8 (ASR cached per clip afterwards)
npm run build -- rebuild    # after editing reel.config.json or scenes.py
npm run build -- graphics   # after editing scenes.py only
npm run check
```

- Per-reel data lives only in `reel.config.json` and `scripts/scenes.py`. Everything in `index.html`, `src/`, and `scripts/*.json` is generated: never hand-edit it.
- Need something the engine lacks (a new icon, transition kind, or step)? Add it to `_shared/pipeline/` generically, rebuild and diff the reels in `Shorts/`, and note it in the engine README.
- When something costs time, add it to `_shared/pipeline/docs/lessons-learned.md`. When the user settles an editorial question, record it in `docs/editorial-rules.md`.
- Worked examples (data only, no footage): `_shared/examples/celular-escucha/scenes.py` and `_shared/examples/strategy/`.

## Visual defaults

- House style: the `terminal` theme (`visuals.theme`, the default), matching the javiercazares.dev portfolio: near-black grid-paper panel, lime `#b8ff35` as the single accent, cyan/magenta/yellow/orange secondaries, JetBrains Mono for graphics and captions, square cards with hard offset shadows, `>` prompt titles with a blinking cursor, lime blocks for priority lines. Light variant: `"theme": "terminal-light"` (the portfolio's light theme: warm paper grid, green `#356e00`, black hard shadows; captions outlined white, keywords dark green on paper chips). Brand reference: `_shared/brand/style.md`. Only override palette or fonts when the brief asks; note why in `src/visuals.design.md`. The `glass` theme is a frosted light panel with Montserrat.
- Graphics: clean typography, compact vertical diagrams, terminal cards, nodes, arrows, light humor. Avoid stock AI imagery, glowing brains, purposeless circuits or glitches, and dense diagrams. Labels are usually 1–6 words.
- Layout: presenter mostly in the lower half, graphics in the upper half, adjusted to the real framing. Keep face, hands, captions, and platform controls clear.
- Transition timing reference: outgoing move starts about 0.24–0.30 s before the cut; incoming settles over about 0.28–0.37 s; swipes about 220 px at 1.52×; zooms and spins about 1.5–1.8× and 11–15°.

## Audio defaults

- Original clip audio carries the narration and stays synchronized to its picture. Voice is always foremost.
- Background music is on by default (step 8) when `_shared/music/` has the track (see its README; without it the build leaves the music out), unless the brief says no music. Opening explosions and memes are off unless the user approves them.
- Check peaks and listen around every transition and dense SFX passage before handoff.

## Rendering

- `package.json` render script: `"render": "npx --yes hyperframes@X.Y.Z render --frames-cache-dir .cache/frames-cache"`. HyperFrames' default extracted-frame cache lives in the system temp folder (~2.3 GB for a 30-clip reel); where that folder is RAM-backed it caused swapping and stalled renders. Keep the cache on disk.
- For long reels, render with `HF_SEGMENTED_CAPTURE=true` so a failed render can continue with `--resume`. A 3-minute reel took about 18 minutes on a machine with a GPU (much longer without one); run it in the background.
- Output: `renders/<topic>-reel-final.mp4`. Verify with `ffprobe`: 1080×1920, 30 fps, H.264 + AAC, duration equal to `cut-map.json`.

## Deliverables and locations

- Source footage: `media/raw/` (read-only)
- Project images/audio: `media/images/`, `media/audio/`
- Compositions: `src/`; helpers and data: `scripts/`
- Final export: `renders/<topic>-reel-final.mp4`
- Sidecars: `scripts/transcript.json`, `scripts/subtitulos.srt`, `scripts/cut-map.json`
- Temporary/generated files and review snapshots: `.cache/`
