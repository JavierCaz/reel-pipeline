# Lessons learned and machine quirks

Append to this file whenever something costs time. Newest first within each section.

## Transcription

- **Parakeet drifts into English on long joined audio.** On CelularEscucha's 148 s cut it
  switched to English after ~115 s. `transcribe.py` therefore transcribes each clip range
  separately (with `-l es`), which stayed fully Spanish. (2026-10-05)
- **Whisper is not installed on this machine.** `hyperframes transcribe -e whisper` exits with
  `whisper_unavailable` and leaves the previous transcript in place. A second ASR opinion is
  not available locally; cross-check doubtful words against audio energy instead. (2026-10-05)
- **Per-clip ASR clamps word starts to 0.0** at clip starts, so ASR timing cannot verify trims.
- **Two passes disagree on short words** ("no, no" vs "no"; "puede" vs "pueda"). To check a
  doubtful word, print 50 ms RMS around it from `.cache/cut-audio.wav` or the source; a
  speech burst (> −15 dB) in an ASR gap is a missing word. Record the fix in
  `transcript_fixes.insert` and flag it for listening review.
- **Never key fixes by word id.** Re-transcribing one clip renumbered every later word and a
  merge silently ate the wrong word. Fixes are keyed by clip + ASR text. (2026-10-05)

## Boundaries

- **Excluding or adding a clip renumbers every later clip, and `build all` runs `cut` before `camera`** (Builder,
  2026-10-14): the first cut pass read the old `scripts/camera-moves.json` and failed with "Camera move exceeds clip 2".
  Delete `scripts/camera-moves.json` (generated) before rebuilding after a clip-set change; also re-key `camera`,
  `transcript_fixes`, `trim.overrides`, and `stage` by the new clip numbers. Whole false-start clips go in `trim.exclude`.

- `first_speech_start` near 0.0 means the clip starts mid-speech or with noise; listen.
- A trailing "strong" event > 1 s after the last word is usually handling noise; check the last
  word's end with a fine RMS profile and use `trim.overrides.source_out`.

## Graphics engine

- **A scene element keyed `root` hid the whole scene (Decorator, 2026-10-13).** Element ids are `{scene id}-{key}`, and the
  scene's own containers are `{scene id}-root`, `-stage`, `-bg`; a class box keyed `"root"` shared the root's id, so its
  entrance and collapse tweens faded the entire scene (panel included): it only showed while that box was visible. The
  standalone timeline looked correct; only snapshots showed it. `Scene.add` now rejects reserved keys. A duplicate id in
  `grep -o 'id="[^"]*"' src/visuals/<scene>.html | sort | uniq -d` is the quick check. Also: the engine doesn't delete
  renamed scenes' old `src/visuals/*.html`; remove stale files by hand.
- **Finding real photos without the HeyGen CLI (2026-10-13, HomeServer).** `media-use resolve --type image` needs the
  `heygen` CLI and login (not set up here). Product photos: the manufacturer's page lists its images (`curl` the page,
  `grep -oE 'src="[^"]+\.(png|jpe?g|webp)"'`); orangepi.org serves transparent PNG cutouts. Places: the Wikimedia Commons
  API, `generator=search&gsrsearch=<query> filetype:bitmap&gsrnamespace=6&prop=imageinfo&iiprop=url|size|extmetadata&iiurlwidth=1800`
  (send a User-Agent), which returns the licence (`LicenseShortName`), author (`Artist`) and a resized URL. Build a
  contact sheet with ffmpeg `xstack` to choose.
- **scenes.py runs in the engine's globals, so a loop variable can overwrite an engine helper.** `for j in ...` replaced `visuals.j` (the JSON serialiser) and the next tween failed with `TypeError: 'int' object is not callable`. Avoid one-letter names `j`; check a new top-level name with `grep -n "^def <name>\|^<name> =" visuals.py`. (2026-10-13, HomeServer)
- **Manufacturer product cutouts carry wide transparent margins** (orangepi.org PNGs were ~70 % transparent), so the object looked tiny at any box size. Crop to the alpha bounding box (PIL `getchannel("A").getbbox()`) before placing; keep the original source noted in `media/images/SOURCES.md`. (2026-10-13, HomeServer)
- **A presenter layout grows back during the last 0.8 s of its segment**, so the last element of a square scene has to land ~1 s before the segment's final word ends, or the returning face covers it. (2026-10-13, HomeServer)
- **ASCII art and the layout check (2026-10-12, IANuclear).** Multi-line ASCII at line-height 1.0 makes every
  row's glyph box overlap the next, and `content_overlap` flagged 80 pairs. `data-layout-allow-overlap` is **not
  inherited**: it has to sit on each row and each coloured run, which `s.ascii` now does. The footage ASCII shader
  (`hyperframes media-treatment`, capability `ascii`) needs `asciiColor: 0` for the palette to apply; with 1 it keeps
  source colours. Lime on the theme surface at size 0.05 read best; 0.08 lost the face.

- **`s.line` used to clip at y 760** (its SVG canvas covered only the top panel), so connectors in the lower
  frame of a presenter layout vanished. It now switches to a full-height canvas when a point is below y 740.
  Also: `T()` cannot find a phrase that spans a merged transcript token ("toma también,"); key off a
  neighbouring word instead. (2026-10-09, Adapter)

- **Website captures (SitioWeb, 2026-10-08).** Playwright from the site's repo, 390×844 viewport at
  deviceScaleFactor 2, `isMobile`; scroll the page first so lazy and reveal-on-scroll content loads.
  `astro dev` injects the dev toolbar (`astro-dev-toolbar`, a dark floating pill): hide it with
  `addStyleTag` or use a production build. Block third-party hosts (Cloudflare challenge, Hostinger)
  or `networkidle` never fires on the WordPress copy. Crop full-page captures to the part you scroll
  (≤ ~13k px; very tall images risk GPU texture limits) and keep local-URL artefacts off screen
  (WP footer showed `contacto@localhost:8089`).

- **GSAP did not render an animated `clip-path` mid-tween in the reel timeline** (it jumped to the end
  value), although the same tween worked in a minimal composition, with video, filters, and the
  shell/frame nesting. `tl.to`, `tl.fromTo` with explicit strings, and wrapper changes all failed. A
  proxy tween whose `onUpdate` writes the clip string works; `cut.py` drives the presenter crop from
  the playhead with one reel-long proxy tween (a pure function of time, so seek-safe). Probe this
  kind of issue with single-frame `snapshot --at` and a scratch edit of `index.html`. (2026-10-06)
- **Nested clip-paths for a ring didn't follow either**; the ring and hard shadow are now
  `drop-shadow` filters on the presenter, which track any clip shape. (2026-10-06)

- **Calibrate face circles on the actual footage, including camera motion.** A centered frame
  crop put Strategy's face low and left, clipping the chin. Use per-segment `stage.region`
  overrides and inspect the start, middle, and end of each hold, including emphasis punches;
  changing the crop must not move or resize the circle's on-screen target. (2026-10-06)
- **Variable-frame-rate phone clips made the cutout drift** (a ghosted double of the presenter):
  `remove-background` writes the matte at the input's average rate (28.73 fps, 141 frames vs 136 over
  4.65 s), so it ran ~5 % slow. `matte.py` now feeds it a constant-30 fps upright copy that follows the
  source timestamps, and rejects any matte whose duration differs from its source by > 1.5 frames.
  (2026-10-06)
- **`remove-background` ignores the phone rotation tag.** On a raw clip stored 1920×1080 with −90°
  it segments the sideways frame, finds no person, and writes a landscape matte with an empty alpha.
  `matte.py` transcodes an upright copy into `.cache/matte-src/` first and rejects landscape output.
  Speed: ~1.1–1.6 s per frame on CPU (clip 13, 279 frames: 435 s). (2026-10-06)
- **The check flags text placed directly on footage** (it measures against the black root, e.g.
  1.3:1). Put headings in cutout scenes on a paper card; it also reads better on a busy room. (2026-10-06)
- **Never tween `left/top/width/height`** in index.html (`gsap_non_transform_motion`). The presenter
  frame fades out, is re-placed with `tl.set`, and fades back in. (2026-10-06)

- **Hand-made HTML outside HyperFrames loses the font.** CelularEscucha's first cover (`src/cover.html`
  rendered in a plain browser) fell back to a generic monospace; HyperFrames embeds Google fonts only
  when it renders. The cover step renders through `hyperframes snapshot` for that reason. Its thin
  cursor also read as an "l" ("escuchal"); covers use a 0.5em block. JetBrains Mono at weight 800 with
  −.07em tracking measures ~0.58em per character, not 0.53. (2026-10-06)

- **`T()` searches the whole reel.** Short words ("vas", "pie", "estrategia") match an earlier
  clip and raise "outside start-end". Strategy's scenes.py defines `W(phrase)` = `T(phrase, s.start)`
  (scene-scoped); copy that pattern. Don't name it `at`: loops use `at` as a variable. (2026-10-06)
- **`s.line` ignored intermediate points** before 2026-10-06 (drew first → last); it is now a
  polyline. Two-point lines are unchanged (CelularEscucha visuals verified identical).

- The overlap / past-end checks fire most often for elements entering in the last ~0.8 s of a
  scene and for dot swarms whose staggered entrances overlap a later `move`. Retime.
- Glow on bare `s.art` icons renders as a square box; glow only cards.
- `HOT` (#ff7a59) text on `PAPER` fails the 3:1 contrast check; use `ALERT` for small text.

## HyperFrames CLI

- **Two `tl.set` at the same time can resolve in either order on a seek.** The caption track's
  hide-all set and the first cue's show-set were both at 0.000, so "Este era mi sitio" (0–0.84 s)
  never showed. Keep a show-set strictly after the matching hide (`captions.SHOW_MIN`). (2026-10-08)

- Running Studio (`preview --background`) re-serializes source HTML (adds `data-hf-id`,
  `<!DOCTYPE html>`, `attr=""`). Do not diff generated files against copies Studio has touched.
  `scripts/hf-ids.json` keeps the ids stable across rebuilds.
- `snapshot --at` with many timestamps sometimes renders the last one at a different time;
  check the frame labels in the contact sheet.
- Transition poses use `power4.in`: a snapshot 0.1 s before a cut shows almost no movement.
  Check transitions at about 0.02 s before the cut.
- `npm run check` warns `composition_file_too_large` for `index.html`; expected for 20+ clips.
- `/tmp` is RAM-backed tmpfs: always render with `--frames-cache-dir .cache/frames-cache`.
- Frame 0 of the render shows sub-compositions (captions, scenes) before their timelines apply:
  no caption and no graphics on the very first frame even when tweens start at 0. From frame 1
  (0.033 s) everything is correct. Don't build a hook that depends on frame 0. (2026-10-05)
- Bundled SFX live in `~/.claude/skills/media-use/audio/assets/sfx/` (manifest.json describes each).
  `glitch-2` hits from its first sample; use a short slice (0.35 s). `glitch-1`/`glitch-3` start
  with silence. Copy new ones into `_templates/short-template/media/audio/sfx/` and the project.

## Verifying a refactor

To prove an engine change doesn't alter a project: copy the project's previous scripts into
`.cache/oldrun/` with its `transcript-asr.json`, `hf-ids.json`, and `.cache/energy-scan.json`,
symlink `media/`, regenerate there, rebuild the project with the engine, and `diff` the
generated files. CelularEscucha's migration matched byte-for-byte except one intentional
7 ms timing improvement.

## Audio

- **Hot phone recordings need headroom (Decorator, 2026-10-13).** A diagnostic mix of the generated audio tracks peaked at +5.11 dBFS. `audio.voice_volume` / `audio.sfx_volume` (both 0–1, defaults 1) now permit uniform gain trims in the source config. Decorator uses 0.45 for voice and SFX, with music reduced proportionately from 0.2 to 0.09; the roughly 20 dB voice/music separation remains unchanged. Measure the composed mix, not just individual files. Diagnostic mono audio is review evidence, not verification of a final stereo encode.

