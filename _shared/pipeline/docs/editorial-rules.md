# Editorial rules

Decisions an agent otherwise has to guess. Items marked **(default — confirm)** were judgment
calls made on CelularEscucha (2026-10-05) and have not yet been confirmed by the user; change
them here once you decide, and remove the marker. A newer user instruction or a project's
approved brief always wins.

## Speech vs. script

- The recording is authoritative. Captions are verbatim speech (proofread for spelling,
  accents, joined words); never substitute the script's wording.
- On-screen labels and titles follow the **speech** when it differs from the brief's
  `on_screen_text` (CelularEscucha: "Construyen un perfil", not the brief's "modelo de ti").
  **(default — confirm)**
- The opening title is the exact title from the brief, even if not spoken.
- Brief `on_screen_text` for a concept the speaker never said is left out
  (CelularEscucha dropped "¿Cómo te reconocen sin cookies?"). **(default — confirm)**
- Anglicisms keep a readable Spanish spelling of what was said ("skipeas"). **(default — confirm)**

## Clip order and trims

- No explicit order: ascending filename timestamp; say so in the handoff.
- Retakes or false starts inside a clip: flag them; do not cut inside a clip without approval.
- Non-speech sounds after the last word (handling, stop-recording clicks) are trimmed through
  `trim.overrides`, leaving a short quiet beat (~0.4 s) on the final clip. **(default — confirm)**

## Graphics content

- Illustrative examples are allowed when the speaker implies a category but names no instances,
  as long as they are clearly generic (CelularEscucha: "Café / Tecnología" interest bars, a
  product list "Cafetera, Audífonos, Tenis, Libro"). List every invented example under
  "Needs your review". **(default — confirm)**
- Probabilities are shown as bars without exact percentages unless the speaker says a number.
- Sensitive claims follow the brief's accuracy notes (e.g. never imply microphone abuse is
  impossible: use "Técnicamente posible", "No necesariamente").
- **Official icons for named technologies** (user, 2026-10-13, HomeServer; replaces "text pills only"): whenever the
  speaker names a technology, tool, service or brand that has a recognisable icon (Linux, Docker, Jellyfin, Netflix,
  Google, ChatGPT…), show its official mark next to the name in the illustration: `logo(src)` wherever an icon goes
  (`s.card(icon=)`, `row_card`, `s.art`). Resolve with `npx hyperframes media-use resolve --type logo --entity <name>`
  (official SVG, never redrawn or recoloured), copy to `media/images/<name>-logo.svg`, list it in `SOURCES.md` and the
  handoff. Generic concepts without a brand (redes, servidor, calendario) keep the house icons. If only a favicon
  resolves, skip the logo (or use the real product photo) rather than upscale it.
- **A character for the AI** (user, 2026-10-12, IANuclear): when a reel talks about AI, one robot pet (engine `i_robot`)
  stands for it in every scene where the AI acts (chat replies, rockets, networks, takeovers, angel/devil). Avoid
  text-only stand-ins like an "IA" box: show it visually.

## Real images (user, 2026-10-13, HomeServer)

- Introduce real objects and places with a **real image** (`s.photo`): the speaker's hardware on the line that names it,
  a real data centre for "centros de datos". The user liked this and asked for it in the engine.
- After the introduction the object becomes its **animated drawing** (an engine icon, e.g. `i_sbc` for the board) for
  diagrams, labels and motion; bring the photo back for a recap or the CTA if it helps.
- Sources, in order: the user's own photo; the manufacturer's official product image (transparent cutouts work best);
  freely licensed photos from Wikimedia Commons (prefer public domain / CC0 / CC BY over CC BY-SA). Never AI-generated
  stand-ins for a real object. Avoid photos where identifiable people are the subject.
- Record every image in the project's `media/images/SOURCES.md` (file, source URL, author, licence, edits) and give CC BY
  photos an on-image `credit` ("Foto: Autor · CC BY 2.0"); list them in the handoff.

## Pacing and emphasis

- Priority lines: a camera `hit`, one big simple graphic held ≥ 1.5 s, no competing elements.
  If the line comes at the very end of a scene, start the graphic on an earlier word of the
  same sentence rather than shortening it. **(default — confirm)**
- Footage transitions only at real section changes; a brief's "hard cut" is honoured as a
  hard cut with a camera scale jump.
- Brief-requested graphic transitions (collapse, merge, ad-expand, zoom-out to a crowd) are
  built inside the concept scenes, not as footage effects.
- Target duration is advisory: if the recorded speech runs long (CelularEscucha: 147 s vs. a
  120–130 s estimate), keep the speech and report the difference; do not speed up or cut lines
  without approval. **(default — confirm)**

## Presenter layouts (animation-led moments)

Settled on Strategy (2026-10-06):
- Use them by default in 2–4 places where a diagram carries the explanation; `card` for multi-element
  examples, `circle` for diagrams that need most of the frame, `takeover` only when the scene fills
  the frame for its whole duration (a half-empty takeover was changed to `circle`).
- Consecutive moments morph directly (card → circle); never return to full screen only to shrink
  again right after.
- Crops are centred on the measured face (`build matte`); the move into and out of a layout is the
  staged 0.8 s transition (crop leads, then the move), never a hard snap.
- No presenter cutout (matte above the graphics) unless the user asks: it showed visible artefacts and
  was removed from Strategy.
- **`square` is the default face layout** (user, 2026-10-08, SitioWeb): a 400 px square card cropped tight on the
  measured face. It fills the space beside tall graphics better than the circle and doesn't cut the chin.
  Use `circle` only on request; `card` (chest-up) for multi-element examples.
- **The square sits bottom left** (user, 2026-10-09, Adapter): the platforms' like/comment/share buttons
  cover the right edge. Graphics beside it go on the right.
- Keep the hook, direct-to-camera priority lines, and the CTA on the full presenter. **(default — confirm)**
- Flag in the handoff any stretch longer than ~30 s without the full camera. **(default — confirm)**

## Handoff

- The "Needs your review" list always includes: uncertain words (with clip and time),
  trim overrides, invented examples, brief items left out, and audio levels that have not been
  listened to.

## ASCII art (user, 2026-10-12, IANuclear)

- ASCII art only where the drawing itself is worth seeing in ASCII (the mushroom-cloud bomb). Charts, bars,
  diagrams, icons, and networks stay in the house style (cards, SVG icons, lines): in ASCII they felt cheap and
  less clear.
- No block-letter (`ascii_banner`) titles: the user disliked the square-glyph headlines.
- The footage ASCII filter (`ascii_footage`) is an opening device only: one scan band sweeps the first clip
  (`"mode": "scan"`), like tuning in. No tune-out at the end and no mid-reel ASCII footage (user, 2026-10-12).

## Living elements (user, 2026-10-12, IANuclear)

- Important elements never sit still once they are on screen. The eye in IANuclear's clips 9–10 is the reference:
  it hovers, blinks, leans into its moves, its pupil darts and re-locks on its target, and a sight line locks
  on and snaps. Give every key element (characters, the pet, the main icon of a scene, network nodes, question
  marks, warnings) idle life between its scripted beats: hover, breathe, wobble, blink, glance, data flowing.
- Life is subtle and never fights a beat: use the engine's `hover`/`breathe`/`wobble`/`loop`/`robot_life`, which
  only fill the time after an element's own tweens. Text blocks stay still enough to read.

## Captions

- Captions are outlined white text in every theme; the user rejected paper caption plates (white
  boxes around whole phrases) on 2026-10-06. In `terminal-light`, keywords use the theme's dark green
  on a small paper chip (user request 2026-10-06); in `terminal`, lime with an underline.

## Still undecided (ask the user, then record here)

- What do you check first in a preview, and what feedback do you give most often?
- Preferred caption style variations per series? Max caption length?
- How much on-screen text is too much for one scene?
- Should the CTA end on a branded outro or the presenter?
