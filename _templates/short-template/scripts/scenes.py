"""Concept scenes for this reel — executed by _shared/pipeline/visuals.py.

Every name (Scene, T, clip_start/clip_end, OPENING_TITLE, palette constants, icons,
helpers) comes from the engine; API and layout rules: _shared/pipeline/docs/visual-system.md.
Worked example with 18 scenes: _shared/examples/celular-escucha/scenes.py.

Rules of thumb:
- One idea per scene; build it element by element on the word that introduces it: T("phrase", after).
- Keep content in y ≈ 180–680 px. Headings at y=196. Priority lines get one big simple banner.
- If the engine raises an overlap or past-the-end error, retime the beat; never loosen the check.
"""
# flake8: noqa  (names are provided by the engine namespace)

# 00 — HOOK over clip 1 (house style): a terminal window powers on, the exact title from
# reel.config.json "opening_title" decodes, glitches, and gets a cursor; the subtitle types in.
# To play the clip's story inside the window afterwards, pass compress_at=<time> (the title
# shrinks into a header) and add elements below it. Worked example: _shared/examples/celular-escucha/scenes.py scene 00.
s = Scene("00-titulo", 0, clip_end(1) - 0.02, decor=((1000, 34, "pearl"),), panel="instant")
s.window("win", 50, 96, 980, 566, "~/" + common.CONFIG["id"], 0.0)
if OPENING_TITLE:
    s.hook_title(OPENING_TITLE[0], OPENING_TITLE[1] if len(OPENING_TITLE) > 1 else None, t=0.22, x=110, y=240)

# 01 — next idea. Example:
# s = Scene("01-idea", clip_start(2) - 0.02, T("next section first words") - 0.04)
# s.heading("Short heading", T("keyword"))
# icon_card(s, "a", "Label", i_phone(), 110, 300)
# s.enter("a", T("word") - 0.12, "up", "pop")


# ANIMATION-LED MOMENTS — when config "stage" shrinks the presenter (square — the default face layout — card, or circle) or hands over the frame
# (takeover), the scene may use y ≈ 150–1300 and must avoid the square (bottom left: x 60–460, y 905–1305), card (x 620–1020, y 905–1305) or circle
# (x 700–1040, y 960–1300). STAGE lists the resolved moments: [{mode, start, end, clip}].
# Worked example: _shared/examples/strategy/scenes.py scenes 03b–05.

# COVER — static illustration for the cover image (step 9, `npm run build -- cover`). Draw the reel's key
# concept with the usual helpers in stage coordinates, y ≈ 780–1250; it renders in its final state.
# Worked example: _shared/examples/strategy/scenes.py.
# def cover(c):
#     icon_card(c, "a", "Label", i_phone(), 420, 860, 240, 220)
