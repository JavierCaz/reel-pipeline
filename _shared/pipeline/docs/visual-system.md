# Visual system and scene API

How concept graphics are laid out and written in `scripts/scenes.py`. Worked example:
`_shared/examples/celular-escucha/scenes.py` (18 scenes).

## Frame zones (1080×1920, presenter recorded chest-up, phone portrait)

| Zone | y (px) | Use |
| --- | --- | --- |
| Platform top UI | 0–150 | nothing important |
| Graphics panel | 0–735 | frosted panel; fades out from ~580 px |
| Scene content | ~180–680 | headings at y=196 (52 px; 44–48 px for long lines), content 290–660 |
| Face | ~770–1200 | never covered; at the tightest crop (1.14×) the hair line rises to ~740 px |
| Captions | 1360–1605 (box 108–972 wide) | presenter's lower torso, inside the 80 % title-safe box |
| Platform bottom UI | ~1650–1920 | nothing important |

These numbers come from the recording setup shared by IAExplicacion and CelularEscucha
(same desk, camera position, and chest-up framing). **Calibrate on new footage:** before step 6, extract one
frame per few clips (`ffmpeg -ss 3 -i clip.mp4 -frames:v 1 -vf scale=360:-1 f.jpg`) and confirm
the face top stays below ~740 px at 1.14×. If the setup changes, update this table and the
`visuals.panel`/caption `box` in the config.

Horizontal: content between x≈60 and 1020. Two-column layouts use ~110–490 and ~590–970.
Compact vertical or 2×N grids read better than wide horizontal chains.

## Themes (`visuals.theme`)

| Theme | Look | Used by |
| --- | --- | --- |
| `terminal` (**default, house style**) | from the javiercazares.dev portfolio: near-black quadrille grid paper, lime `#b8ff35` as the single accent (cyan/magenta/yellow/orange as secondary group colours), JetBrains Mono, square corners, 2 px rules, hard offset shadows (`8px 8px 0`), `> prompt` titles with a blinking block cursor, lime banner blocks for priority lines | CelularEscucha (adopted 2026-10-05) |
| `terminal-light` | the portfolio's light theme: warm paper grid `#f2f1ea`, ink `#0d100c`, green `#356e00` (paper text on green fills), black hard shadows; captions outlined white with dark-green keywords on paper chips; same motifs as `terminal` (`TERMINAL` is true for both) | added 2026-10-06; reference `Shorts/Strategy/.cache/light-review/` |
| `glass` | frosted light panel, soft gradients, rounded cards, Montserrat | IAExplicacion-style; CelularEscucha first pass |

Write scenes with theme tokens instead of literal colours so they work in both themes:
`SURFACE` (bright fill inside icons/bubbles), `TRACK` (empty bar/placeholder), `CARD_SHADOW`,
`DOT_SHADOW`, `LINE` (quiet rules), `ON_FILL` (marks on bright fills), `HOT_TEXT` (text in the
viewer's colour), `FONT`. Theme defaults (palette, font, captions) live in `presets.THEMES`; the brand reference is `_shared/brand/style.md`. Terminal palette: ink `#efefe8`, primary `#b8ff35`,
accent `#00e5ff`, warm `#ffd500`, soft `#2a3326`, paper `#0c0f0c`, alert `#ff4fd8`, muted `#a1a99a`,
hot `#ff7a1a`; captions in JetBrains Mono 52 px with lime accent.

## Opening hook (scene 00)

The first ~2 s must stop the scroll. House pattern (template default, refined on CelularEscucha):

1. `panel="instant"` + `s.window(..., 0.0)`: a lime CRT line opens the terminal window at frame 1.
2. `s.hook_title(...)`: the exact title decodes (0.2–1.2 s), glitches with a bass hit on lock, a
   cursor blinks; the subtitle types in (~1.3–1.8 s). Hold the full title until ~2.3 s.
3. `compress_at≈2.3`: the title becomes a header and the clip's spoken story plays inside the
   window, one beat per phrase (CelularEscucha: conversation + voice meter → time warp with streaks
   and a rolling window clock → phone + ad → link line on "relacionada").
4. Keep SFX ≥ 11 dB under the voice (typing 0.5, glitch-2 0.12 for a 0.35 s slice, impact 0.08).

## End card (outro)

Built by the engine from config `outro` (template default carries the handles and website): a lime
curtain then a grid-paper sheet sweep up (covered in 0.54 s), `$ whoami` types, the name decodes,
one row per handle slides in (platform name as text, no logos), and the website lands as a lime
button with a blinking cursor; music fades under it. It runs on track 12 above captions, so the
last panel scene should end at `OUTRO_START + 0.6` (CelularEscucha scene 17).

## Presenter layouts (config `stage`)

Moments where the animation is the main element. Each entry: `{"mode", "from": [clip, word], "to":
[clip, word]}` (words as in `transcript.json`; optional `lead`/`tail` seconds, `from_clip_start`,
`to_clip_end`). Scenes read the resolved times from `STAGE` (`[{mode, start, end, clip}]`).

| Mode | Presenter | Free area for graphics |
| --- | --- | --- |
| `card` | 800×800 chest-up crop → 400×400 card at (620, 905), accent border + hard shadow | everything except x 620–1020, y 905–1305 |
| `square` (**default face layout**) | 640×640 face crop (face ~45 % from the top) → 400 px square at (60, 905), **bottom left** (the platforms' like/comment/share buttons are on the right; user 2026-10-09), accent border + hard shadow | everything except x 60–460, y 905–1305 |
| `circle` | 600×600 face crop → 340 px circle at (700, 960); on request only (cuts the chin) | everything except x 700–1040, y 960–1300 |
| `takeover` | leaves the frame (shrinks into a circle and fades) | the whole frame above the captions (y 150–1300) |
| `cutout` | **opt-in only** (removed from Strategy after visible artefacts): full frame; an alpha matte (`build matte`) is layered above the graphics | the room behind the presenter: text/cards there are occluded by the head/body |

For `card`, `circle`, and `takeover`, each entry may override `region: [x, y, width, height]`
in the 1080×1920 frame after its camera motion. This changes the crop while preserving the
on-screen target position and width. Circle/takeover regions must be square. Calibrate on the
actual footage at several times, including camera punches; leave room for both hair and chin.
Strategy's clips 6 and 10 use different regions because the presenter is left of frame center.

Card and circle crops are centred on the face: `npm run build -- matte` samples three stills per
segment, cuts the presenter out, and stores the head centre in `scripts/stage-focus.json` (delete an
entry to re-measure). An entry's `"region": [x, y, w, h]` (square for circles) or `"focus": [x, y]`
overrides it. The presenter moves between layouts in 0.8 s (`presets.STAGE_MOVE`): shrinking, the crop leads (corners
round off, `power2.inOut`, 70 % of the move) and the scale/travel follows 0.12 s later (`power3.inOut`);
growing back, the move leads and the crop opens after it. The accent ring (`STAGE_RING` 6 px) and the
hard shadow (`STAGE_SHADOW` 12 px) are drop-shadow filters, so they follow the shape through the whole
move at a constant screen size; the backdrop eases in over 0.4 s. Adjacent segments (≤ 0.6 s apart)
morph straight from one layout to the next (circle ↔ card). A full-frame grid `#backdrop` shows behind a shrunk
presenter. Growing back to full frame, the presenter passes in front of the graphics (z 16) until that scene ends. Captions stay at y 1360–1605 in every mode, so keep graphics above y ≈ 1300.
During a cutout the room behind the presenter blurs (10 px), dims (0.88), scales 1.03 (hides the
blur's soft frame edges), and a theme wash fades in (`#cutout-wash`: surface tint at the top, ink
toward the bottom, under the graphics); both ease in over 0.4 s and clear 0.35 s before the matte ends.
Tune in `presets.CUTOUT_BACKGROUND`. Cutout scenes use `panel="none"` (graphics sit on the real room) and must end when the cutout ends,
or the graphics would cover the presenter; a cutout must stay ≥ 0.4 s clear of footage transitions.
Matting cost ~1.1–1.3 s per frame on the original machine's CPU (a 9 s clip ≈ 6 min); mattes are cached in
`media/cutouts/`. Worked example: `_shared/examples/strategy/` (2026-10-06: circle, card, circle; takeover and cutout were tried and replaced). When to use each mode: template step 6 and `docs/editorial-rules.md`.

## Cover image (step 9)

`npm run build -- cover` → `renders/<id>-cover.png` (1080×1920). Layout:
terminal window over the whole frame; optional `> kicker`; the
title in stepped sizes (first line ink, the rest in the accent; one line = accent) ending in a solid
block cursor; a muted subtitle; the illustration in y ≈ 780–1250; the video still from `frame_top`
(default 420) fading into the theme surface under the grid, face around y 1300–1700.

The illustration is `def cover(c):` in `scenes.py`, drawn with the normal helpers in stage
coordinates. It renders in the final state (no timeline): use cards, icons, lines, text, pills;
avoid `c.decode` (its slots need the timeline). Pick an expressive still (`frame`) — a smile or an
emphasis beat — and keep the title to 1–3 short lines. Strategy (2026-10-06) is the first example.

## Design rules

- **Real images** (user, 2026-10-13, HomeServer): when the speaker introduces a real object or place (their hardware, a data centre), show a real photo with `s.photo`; once it is introduced, switch to the house-style drawing (an engine icon) for diagrams and animation. See `docs/editorial-rules.md` "Real images".
- One idea per scene; build it element by element on the words that introduce it.
- Labels of 1–6 words, from the speech. Text ≥ 24 px; prefer 28–40 px.
- Priority lines (`agent_notes.priority_moments` in a brief) get **one** large, simple element
  (`s.banner`, or a two-line title) held ≥ 1.5 s, plus a camera `hit`.
- The viewer is always one consistent icon/color (`HOT`, label in `HOT_TEXT`); other people use `PRIMARY`/`ACCENT`.
- Named technologies and brands show their official icon (`logo(src)`, editorial rules). No stock AI imagery, glowing brains,
  surveillance clichés, or purposeless circuits.
- Contrast: never hard-code colours; use palette roles and theme tokens so a scene works in every theme. In `glass`, small text uses `ALERT`, not `HOT`, on `PAPER` (the check flags < 3:1).
- Glow (`glow=True`, `s.glow`) only on cards (`s.card`, `icon_card`, `row_card`, `s.add` with `v-card`);
  on bare `s.art` icons it shows as a square box.

## Scene API (names available in scenes.py)

Timing: `T("phrase", after=0)` → start time of the spoken phrase (accent- and punctuation-
insensitive); pass `after` when the phrase repeats. `clip_start(n)`, `clip_end(n)`,
`OPENING_TITLE`, `DURATION`.

`s = Scene(slug, start, end, decor=((x, y, "pearl"|"capsule"|"cube"), ...), panel="slide"|"instant")`; use `panel="instant"` for the opening hook so the panel is up on the first frames. Scenes must
not overlap; consecutive scenes (gap ≤ 0.4 s) share the panel without re-entering it. Slugs
`NN-name` become `src/visuals/NN-name.html`. The last scene holds to the end of the reel.

Create (hidden until entered):

| Method | Notes |
| --- | --- |
| `s.text(key, label, x, y, w, h, size, weight, color, cls="v-head" for left-aligned)` | |
| `s.card(key, label, x, y, w, h, tint, size, icon=svg, icon_h, color, pill, style)` | tints: `glass` `accent` `warm` `soft` `paper` `ink` |
| `s.tile(...)`, `s.art(key, svg, x, y, w, h)`, `s.add(key, x, y, w, h, inner_html, cls, style, origin=)` | |
| `icon_card`, `row_card`, `pill`, `bar` (+ `key-fill` scaleX), `dot`, `ring`, `scatter(n, cx, cy, rx, ry, seed)` | module helpers taking `s` first |
| `s.heading(label, t, size=52)` | creates **and** enters, with an underline (`heading`, `heading-line`) |
| `s.banner(key, label, t, y, h, size, others=[keys to fade])` | creates and enters a big tile; for priority lines |
| `s.line(key, points, t, color, width, head, duration, curve)` | stage coordinates (any y up to 1920); creates and draws; without `curve`, every point is a vertex (polyline, e.g. a route along streets); `s.exit(key)` also removes its arrowhead |
| `s.travel(key, points, t, duration, color)` | a dot flowing along a connector |
| `s.strike(key, x1, y1, x2, y2, t)` | red strike-through with error SFX |
| `s.window(key, x, y, w, h, title, t, crt=True)` | portfolio-style terminal window (bar, lime glyph, controls, hard shadow); CRT power-on from a bright line |
| `s.decode(key, text, x, y, size, t, color, start_text=, cursor_at=, steps=, stagger=, glyphs=)` | slot-roll "decrypt" text (monospace); `start_text` rolls from another string (clock 14:02 → 19:47); returns lock time |
| `s.typewrite(key, label, x, y, size, t, cps)` | character-by-character reveal; returns end time |
| `s.glitch(key, t, strength)` | cyan/magenta RGB split + jitter on the element, `glitch-2` hit |
| `s.levels(key, x, y, w, h, n, t, until)` | live audio meter (bouncing bars) |
| `s.shot(key, src, x, y, w, h, title, at=0, bar=40, origin_x=50)` | screenshot (project-relative path) in a terminal window; `at` = source-image px at the top. Keep images ≤ ~13k px tall (crop full-page captures) |
| `s.photo(key, src, x, y, w, h=None, frame=None\|"card"\|"window", title, bar, fit="contain"\|"cover", trim=True, zoom, focus, credit)` | a **real image** (project-relative path): a product cutout (transparent PNG; `trim` crops its transparent margins so the object fills the box, and a bare cutout gets a hard drop shadow that follows its outline) or a photograph (`frame="window"` with a `title`, `fit="cover"`). `h=None` keeps the aspect. `zoom` > 1 leaves room to pan; `credit` prints an attribution line on the image (CC BY). Works in `cover(c)` too |
| `logo(src)` | an official brand mark (SVG from `media-use resolve --type logo`) as an icon: pass it as `icon=` to `s.card`/`row_card` or to `s.art` |
| `s.pan(key, t, duration, ease, x=, y=, scale=)` | Ken Burns move of a photo inside its frame (only the given properties move): slow pans over a room, push-ins on an emphasis word |
| `s.scroll(key, t, to, duration, ease, scale=)` | scroll a shot to source-image px `to`; `scale` zooms anchored at the window top / `origin_x` |
| `s.ascii(key, art, x, y, size, t, color, colors={char: colour}, reveal, duration, line, upward)` | multi-line ASCII art (dedented, untracked monospace); reveals `rows`, `decode` (glyph noise in the art's shape, then the art), `scan`, `wipe` (left→right, per column: charts, bars), `fade`; `upward` = bottom row first. Returns `{end, w, h}`. Width = cols × 0.6 × size. Bars: a `"█" * n` ascii whose `-in` clipPath is tweened (`inset(0% X% 0% 0%)`, stepped). In `cover(c)` use `reveal="rows"` (decode's noise layer would show) |
| `s.ascii_anim(key, frames, x, y, size, t, until, fps)` | frame-flip ASCII animation (runners, blinking warnings, typing dots); frames share a row count |
| `ascii_banner(text)` | 5-row block-font text for `s.ascii`; **not for titles** (user disliked it, see editorial rules) |
| `s.hook_title(title, subtitle, t, x, y, compress_at=, header=)` | the opening title sequence: balanced two-line decode (2nd line lime), glitch + bass hit on lock, blinking cursor, typed subtitle; `compress_at` shrinks it into a header so the clip's story can play below |

Animate:

| Method | Notes |
| --- | --- |
| `s.enter(key, t, kind, sfx, rest, gain)` | kinds `up` `down` `left` `right` `pop` `stamp` `tilt` `drop` `rise` `wipe` `grow` `fade` |
| `s.exit(key, t, kind)` | `up` `down` `left` `right` `shrink` `fade`; anything not exited leaves automatically at the scene end |
| `s.move(key, t, dur, ease, **props)` / `s.inner(key, ...)` | outer transform / inner element (use inner for wiggles and pulses) |
| `s.pulse(key, t, amount, sfx, glow)`, `s.glow(key, t, until)`, `s.dim(keys, t, opacity)`, `s.float(key, t, until)` | |
| `s.tw(selector, t, dur, ease, **props)` / `s.set(selector, **props)` | raw seek-safe tween / initial state, e.g. on SVG parts `s.sub(key, part)` or `f"#{s.id}-..."` |
| `s.sfx(t, kind, gain)` | `pop` `click` `click-soft` `ping` `sparkle` `whoosh-short` `whoosh` `typing` `key-press` `error` `impact-bass-1` `chime` `notification` |

Life (house style since 2026-10-12; call at the end of a scene, after its beats). Each schedules a seek-safe
yoyo loop only after the target's own tweens on that property, compresses into a short remaining window, and
ends at rest before the scene's exits:

| Method | Notes |
| --- | --- |
| `s.hover(key, t, until, dy, period)` | inner-layer float |
| `s.breathe(key, t, until, amount, period)` | inner scale pulse |
| `s.wobble(key, t, until, deg, period)` | inner rocking rotation |
| `s.loop(selector, t, until, period, ease, **offsets)` | any target/part: offsets add to the current value (scale-type props multiply), e.g. `s.loop(s.sub("nuke", "glow"), t, end, 0.32, opacity=-0.55)` |
| `s.robot_life(key, t, until, blink, look, antenna, core, arms, phase)` | i_robot pets: blinks, glance, antenna bob, chest-light pulse, arm sway; `phase` desynchronises two pets |

When you `move` an element to opacity 0 as its own exit (e.g. an ad-expand), call
`s.live.remove(key)` so the automatic end-of-scene exit doesn't tween it again.

Icons (`i_*`, 100×100 unless noted): user/person, phone, mic, waves(p), cup, espresso, eye,
skip, heart, follow, search, cursor, cart, play, server, audio(p), gear(p), doc, globe, target,
megaphone, check, question, clock, repeat, box, book, pot, headphones, shoe, form, thought,
browser (160×120), fingerprint, comment, iceberg (300×200), walk, bus, car, pin, card (payment),
sort, tag (discount) — the last seven added for Strategy (2026-10-06); sbc(p, 200×162: the Orange Pi-style board), router(p), laptop, rack(p, 60×120), calendar(p), film, cloud, sun, moon, bolt, hand(skin, p; 200×300 open palm for scale: palm ≈ 120 units ≈ 85 mm, size it so the object keeps its real proportion) (HomeServer, 2026-10-13); plug, socket, adapter (Adapter, 2026-10-09); code, building, shield, health, flask, missile (IANuclear, 2026-10-12); robot (the AI pet: `i_robot(p, mood, halo, wings, horns, tail)`), rocket(p), computer(taken), mushroom(p, 200×200), flag("us"|"cn"), and `ai_overlay(visor, antenna, glow)` to put the pet's visor/antenna on any icon; `i_eye(p)` has a movable `-pupil`. lock(p, fill; `-shackle` opens with y −14), scale(p, 200×160; `-beam`, `-pan-l`, `-pan-r`), officer(fill), photo (PrivacidadEsconder, 2026-10-14). PC parts (Builder, 2026-10-14): tower(p, gamer; 160×220, parts `-cpu -ram -ssd -gpu -fan -led` to assemble a PC part by part), cpu, ram, gpu(p), ssd, fan(p), hardhat, clipboard(p). `p` ids animated sub-parts
(`f"#{s.id}-au-b{i}"`). Add new icons to `visuals.py` (they become available to every reel).

## Timing errors and how to fix them

The engine refuses unsafe timelines. Retime; never loosen the check.

- `time X outside start-end` → the word belongs to another scene, or a phrase repeats:
  pass `after=` to `T`, or move the scene boundary (keep neighbouring scenes in sync).
- `tween ... runs past scene end` → the element enters within ~0.8 s of the scene end;
  enter earlier (on an earlier word) or use a shorter kind (`fade` 0.3 s, `pop` 0.5 s).
  Remember the automatic exit needs ~0.36 s after the last tween.
- `overlapping <prop> tweens` → an entrance and a move overlap; start the move after
  the entrance ends (enter durations: up/down 0.45, left/right 0.42, pop 0.5, stamp 0.3,
  tilt 0.54, drop 0.62, grow 0.6, fade 0.3).

## Review loop

After `npm run build -- graphics`: `npm run check`, then
`npx hyperframes snapshot . -o .cache/<review> --at t1,t2,...` at the middle and the
fullest moment of each scene, and read the contact sheets. Look for overlaps between
pills and cards, text near the panel fade, and glow boxes on bare icons.
