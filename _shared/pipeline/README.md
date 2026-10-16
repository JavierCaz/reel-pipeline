# Reel pipeline engine

Generic, data-driven implementation of the workflow in `_templates/short-template/AGENTS.md`.
A project holds only **data**: `reel.config.json` (everything per reel) and `scripts/scenes.py`
(the topic's concept graphics). This folder holds the **engine**, shared by path, never copied.
It uses only the Python standard library; `ffmpeg`, `ffprobe` and `npx` (HyperFrames) must be on the PATH.

## Usage

From a project folder (`Shorts/<name>/`, created with `npm run new-reel <name>` at the repo root):

```bash
npm run build -- all          # first run: steps 1–8 (transcription ~2 min, then cached per clip)
npm run build -- rebuild      # after editing reel.config.json or scenes.py (no ASR)
npm run build -- graphics     # after editing scenes.py only
npm run build -- cut          # after changing transitions, opening, music, or trim overrides
npm run build -- matte        # presenter cutouts for stage "cutout" segments (slow; cached in media/cutouts/)
npm run build -- cover        # step 9: cover image → renders/<id>-cover.png (~20 s; not part of all/rebuild)
npm run check                 # always after a build
```

`npm run build` runs `build.py` through `scripts/py.mjs` at the repo root, which finds Python on
Windows, macOS and Linux. Single steps: `boundaries`, `cut`, `transcribe`, `review`, `camera`,
`captions`, `visuals`.

| Step | Module | Reads | Writes |
| --- | --- | --- | --- |
| 1 trim | `boundaries.py` | `media/raw/*.mp4`, `trim` | `.cache/energy-scan.json` |
| 2 join | `cut.py` | energy scan, `trim.overrides` | `scripts/cut-map.json`, `index.html`, `scripts/hf-ids.json` |
| 2 transcript | `transcribe.py` | cut map | `scripts/transcript-asr.json` (cache `.cache/clip-asr/NN/`) |
| 2 proofread | `review.py` | `transcript_fixes` | `scripts/transcript.json` |
| 3 camera | `camera.py` | `camera`, transcript | `scripts/camera-moves.json` |
| 4 transitions | `cut.py` + `presets.py` | `transitions`, `opening` | `index.html` |
| 5 captions | `captions.py` | `captions`, transcript | `src/captions.html`, `scripts/caption-cues.json`, `scripts/subtitulos.srt` |
| 6 graphics | `visuals.py` | `scripts/scenes.py`, `visuals`, transcript | `src/visuals/*.html`, `scripts/visual-scenes.json`, `scripts/visual-sfx.json` |
| 7 SFX | `presets.py`, `visuals.py` | transition/opening sounds, `s.sfx()` cues | mounted by `cut.py` |
| 8 music | `cut.py` | `music` | `index.html` |
| end card | `cut.py` | `outro` | `index.html` |
| 9 cover | `cover.py` | `cover`, `scenes.py` `cover(c)`, cut map, theme | `renders/<id>-cover.png`, `.cache/cover/` (frame.jpg, index.html) |

Generated files are overwritten on every run; never hand-edit them. Times after step 2 are
**cut-timeline seconds**: a trim change requires `all` (cached ASR keeps it fast).

**Optional audio.** The transition sounds `page-turn`, `flame`, `transition-2`, `vortex` and the `lofi` music
are not shipped (their licence does not allow redistributing the files). Put them in `_shared/sfx/` and
`_shared/music/` with the names in those folders' READMEs, then create a new reel. When a file is missing the
build prints a warning and uses the bundled `whoosh` sound instead, or leaves the music out.

## reel.config.json

| Key | Meaning |
| --- | --- |
| `id`, `visual_prefix`, `title` | composition id prefix (`<id>-rough-cut`, `<id>-captions`), scene id prefix, page title |
| `language`, `fps`, `order_note` | ASR language, frame rate, how the clip order was decided |
| `opening_title` | exact on-screen title lines from the brief (used by scene 00) |
| `trim` | `pre_roll`/`post_roll` (s), `activity_db`/`strong_db` thresholds, `overrides: {"<clip>": {"source_in"/"source_out", "reason"}}`, `exclude: {"<file name>": "reason"}` leaves whole clips out (a false start re-recorded in the next clip; later clips renumber, the file stays in `media/raw`) |
| `transcript_fixes` | `replace [[clip, asr, fixed, why]]`, `merge [[clip, [parts], joined]]`, `insert [{clip, before, text, start, end, previous_text, why}]` — keyed by clip + ASR text, never word id |
| `camera` | `{"<clip>": {"reason", "beats": [[word, kind]], "initial_scale"}}`; kinds `hit` (priority) `punch` `push` `pull` `step`; the word is matched exactly as in `transcript.json` for that clip |
| `opening` | `{"shake": true, "sound": "vortex"}` |
| `transitions` | `[{"before_clip", "kind", "sound", "note"}]`; kinds `swipe` `swipe-reverse` `zoom` `spin` `spin-zoom-in` `spin-zoom-out` `hard-cut`; sounds `page-turn` `flame` `whoosh` `transition-2` (default per kind in `presets.KIND_SOUND`) |
| `captions` | `accent_chip` `{background, border, shadow}` puts the keyword on a small card in the accent colour (terminal-light default); `plate` `{color, background, border, shadow}` puts each phrase on a solid card (opt-in); `keywords` (accented, ≥3 s apart); `animation`: `subtle` (default) or `kinetic` (varied phrase arrivals, visible word cascade, speech-timed keyword pulse, short exits). Style defaults from the theme, overridable: `accent`, `accent_shadow`, `box`, `font_size`, `font`, `weight`, `letter_spacing` |
| `visuals` | `theme`: `terminal` (default, house style), `terminal-light` (its light variant) or `glass`; the theme supplies palette, font, and caption style (`presets.THEMES`). Optional overrides: `palette` (roles below), `font`, `tints`, `panel`, `grid` (terminal cell px), `terminal` (surface/line/shadow colours) |
| `stage` | presenter layouts: `[{"mode": "square"|"card"|"circle"|"takeover"|"cutout", "from": [clip, word], "to": [clip, word], "lead", "tail", "from_clip_start", "to_clip_end", "note"}]`; optional `region: [x, y, width, height]` overrides the crop for card/circle/takeover (1080×1920 frame pixels after camera motion). Without `region`, card/circle crops centre on the face measured by `build matte` (`scripts/stage-focus.json`) or on `focus: [x, y]`. Target geometry stays in `presets.STAGE`; see `docs/visual-system.md` |
| `ascii_footage` | presenter footage as an ASCII glyph field: `[{"from": [clip, word] or [clip], "to": …, "from_clip_start", "to_clip_end", "length" (s), "lead", "tail", "ramp_in"/"ramp_out" (s), "steps" (default 6), "size" (0.04–0.15), "invert", "color", "palette" [dark, light]}]`; `"mode": "scan"` sweeps one ASCII band across the frame (keys `band`, `sweep`, `direction`, `from_y`/`to_y`, `ease`, `lines`, `slivers`) |
| `cover` | `kicker`, `title` (lines; default: opening title in two lines), `subtitle` (string or lines), `frame` (`{"clip", "at"}` source seconds, or `{"time"}` cut-timeline seconds), `frame_top` (px where the still starts, default 420). Illustration: `def cover(c)` in `scenes.py` |
| `outro` | end card after the last word: `duration` (s), `overlap` (curtain starts this long before the footage ends; ≥0.6 and needs that much quiet tail, see `trim.overrides`), `name`, `handles` [[platform, @handle]], `website`. The reel's length becomes footage + outro. Remove the key to end on the presenter |
| `audio` | Optional global gain trims: `voice_volume` and `sfx_volume`, each 0–1, default 1. Useful for hot phone recordings; original media remains untouched |
| `music` | `{"preset": "lofi", "volume": 0.2, "fade_out": 1.2}` or explicit `src` + `audible_length`; `{"preset": "none"}` or removing the key leaves the music out. Optional `intro`: `{"src", "volume", "until": "first_transition" or seconds, "crossfade": 0.8, "media_start"}` plays a separate hook track under the intro and crossfades into the bed |

Palette roles: `ink` text · `primary` main accent/lines · `accent` data/underlines/glow ·
`warm` soft highlight · `soft` secondary fill · `paper` card fill · `alert` warnings
(must pass 3:1 on paper) · `muted` secondary text · `hot` the viewer ("Tú").

## Track layout

0 footage (inside `#presenter` when `stage` is set) · 1–2 clip audio · 3 presenter cutouts · 8 transition SFX · 9 opening SFX · 11 concept visuals · 12 overlays (end card, above captions) ·
19 intro music · 20+ music parts · 30–39 visual SFX lanes (the build fails above 10 overlapping sounds) · 40 captions.

## Changing the engine

Engine changes affect every reel in `Shorts/`. After editing a module: rebuild each reel, diff its
generated files against the previous output (see "Verifying a refactor" in `docs/lessons-learned.md`),
run `npm run check`, and note the change here.

Docs: `docs/visual-system.md` (layout, scene API), `docs/editorial-rules.md`,
`docs/lessons-learned.md`.
