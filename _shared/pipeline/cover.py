"""Step 9 — cover image: the video title, an illustration, and a frame of the video.

Layout (2026-10-06): a terminal window over the whole
frame; the title in stepped sizes (first line ink, the rest in the accent, a block cursor); a muted
subtitle; a concept illustration drawn with the reel's own scene API; and a still of the presenter
filling the lower half, fading into the theme surface under the grid.

Config (reel.config.json "cover", all optional):
  "title":    ["Tu celular", "no te", "escucha"]   lines; default: opening_title split in two
  "kicker":   "Patrones de Diseño #4"               small line above the title
  "subtitle": "no lo necesita para leer tu mente"   string or list of lines
  "frame":    {"clip": 3, "at": 2.5}                source seconds inside that clip, or {"time": cut-timeline s}
  "frame_top": 420                                  where the still starts (px); the face should land ~1300–1700
Illustration: define `def cover(c):` in scripts/scenes.py and draw with the usual helpers
(c.card, icon_card, row_card, pill, c.line, c.text, c.art, ...) in stage coordinates, inside
y ≈ 780–1250. Elements render in their final state (no timeline), so avoid c.decode.

Writes .cache/cover/ (frame.jpg, index.html) and renders/<id>-cover.png via `hyperframes snapshot`
(same deterministic font embedding as the reel).
"""

from __future__ import annotations

import html
import json
import re
import shutil
import subprocess

from . import common

W_INNER = 844  # title column width inside the window


def _title_lines(cfg: dict) -> list[str]:
    if cfg.get("title"):
        return list(cfg["title"])
    title = " ".join(common.CONFIG.get("opening_title", [])) or common.CONFIG.get("title", "")
    words = title.split()
    if len(words) < 2:
        return [title]
    splits = [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]
    return list(min(splits, key=lambda p: max(len(p[0]), len(p[1]))))


def _frame_source(cfg: dict) -> tuple[str, float]:
    clips = common.read_json("scripts/cut-map.json")["clips"]
    frame = cfg.get("frame", {})
    if "time" in frame:
        t = float(frame["time"])
        clip = next((c for c in clips if c["timeline_in"] <= t < c["timeline_out"]), clips[-1])
        return clip["source"], clip["source_in"] + (t - clip["timeline_in"])
    clip = clips[int(frame.get("clip", 1)) - 1]
    at = frame.get("at", (clip["source_in"] + clip["source_out"]) / 2)
    return clip["source"], float(at)


def _hyperframes_pin() -> str:
    scripts = json.loads(common.p("package.json").read_text()).get("scripts", {})
    match = re.search(r"hyperframes@[\d.]+", " ".join(scripts.values()))
    return match.group(0) if match else "hyperframes"


def run() -> None:
    from . import visuals as V  # theme tokens, CSS, icons, and the Scene API

    cfg = common.CONFIG.get("cover", {})
    out = common.p(".cache/cover")
    out.mkdir(parents=True, exist_ok=True)

    # 1. The video still (ffmpeg applies the phone's rotation tag).
    source, at = _frame_source(cfg)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", str(common.p(source)), "-frames:v", "1",
                    "-vf", "scale=1080:-2", "-q:v", "2", str(out / "frame.jpg")], check=True)

    # 2. The illustration: scenes.py may define cover(c); its elements render in their final state.
    path = common.p("scripts/scenes.py")
    namespace = V.__dict__
    exec(compile(path.read_text(), str(path), "exec"), namespace)
    canvas = V.Scene("cover", 0, V.DURATION, decor=(), panel="none")
    V.scenes.remove(canvas)
    if callable(namespace.get("cover")):
        namespace["cover"](canvas)
    art = "\n".join(canvas.parts)
    # Project images in the illustration (s.shot screenshots) are copied next to the cover page
    # under the same relative path, since it renders from .cache/cover/.
    for rel in set(re.findall(r'<img [^>]*src="([^":]+)"', art)):
        (out / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(common.p(rel), out / rel)

    # 3. Theme surface.
    if V.TERMINAL:
        T = V._T
        bg, line, line_strong, shadow = T["bg"], T["line"], T["line_strong"], T["shadow"]
        accent_shadow, minor, major, bar = T["accent_shadow"], T["grid_minor"], T["grid_major"], T["panel2"]
    else:
        bg, line, line_strong, shadow = V.PAPER, V.LINE, V.LINE, V.INK
        accent_shadow, minor, major, bar = V.INK, V.LINE, V.LINE, V.PAPER
    r, g, b = (int(bg[i:i + 2], 16) for i in (1, 3, 5))
    rgba = lambda a: f"rgba({r},{g},{b},{a})"  # noqa: E731
    grid = 32

    # 4. Title: stepped sizes like the reference (first line smaller, last line largest), fit to the column.
    lines = _title_lines(cfg)
    caps = [172] if len(lines) == 1 else [130] + [142] * (len(lines) - 2) + [172]
    title_html = []
    for n, (text, cap) in enumerate(zip(lines, caps)):
        last = n == len(lines) - 1
        em = len(text) * 0.58 + (0.62 if last else 0)  # measured weight-800 advance with -.07em tracking, plus the cursor
        size = round(min(cap, W_INNER / em))
        color = V.INK if (n == 0 and len(lines) > 1) else V.PRIMARY
        cursor = '<i class="cursor"></i>' if last else ""
        title_html.append(f'<span style="font-size:{size}px;color:{color}">{html.escape(text)}{cursor}</span>')
    kicker = cfg.get("kicker")
    kicker_html = f'<p class="kicker">{html.escape(kicker)}</p>' if kicker else ""
    subtitle = cfg.get("subtitle")
    if isinstance(subtitle, str):
        subtitle = [subtitle]
    subtitle_html = ("<p class=\"subtitle\">" + "".join(f"<span>{html.escape(s)}</span>" for s in subtitle) + "</p>") if subtitle else ""
    frame_top = int(cfg.get("frame_top", 420))
    window_title = "~/" + common.CONFIG["id"]

    doc = f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=1080,height=1920">
<title>{html.escape(common.CONFIG.get("title", ""))} — cover</title>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
<style>
* {{ box-sizing:border-box; }}
html, body {{ margin:0; width:1080px; height:1920px; overflow:hidden; background:{bg}; }}
{V.CSS}
#cover {{ position:relative; width:1080px; height:1920px; overflow:hidden; background:{bg}; color:{V.INK}; font-family:"{V.FONT}",monospace; }}
.photo {{ position:absolute; left:0; top:{frame_top}px; width:1080px; height:1920px; object-fit:cover; object-position:50% 0; opacity:.85; }}
.fade {{ position:absolute; inset:0; background:linear-gradient(180deg,{rgba(1)} 0%,{rgba(.98)} 35%,{rgba(.88)} 50%,{rgba(.5)} 65%,{rgba(.25)} 82%,{rgba(.85)} 100%); }}
.grid {{ position:absolute; inset:0; opacity:.65;
  background:linear-gradient({major} 2px,transparent 2px) -1px -1px/{grid * 4}px {grid * 4}px,
    linear-gradient(90deg,{major} 2px,transparent 2px) -1px -1px/{grid * 4}px {grid * 4}px,
    linear-gradient({minor} 1px,transparent 1px) -1px -1px/{grid}px {grid}px,
    linear-gradient(90deg,{minor} 1px,transparent 1px) -1px -1px/{grid}px {grid}px;
  mask-image:linear-gradient(#000 0%,#000 50%,rgba(0,0,0,.2) 75%,transparent 100%);
  -webkit-mask-image:linear-gradient(#000 0%,#000 50%,rgba(0,0,0,.2) 75%,transparent 100%); }}
.window {{ position:absolute; left:62px; top:128px; width:956px; height:1636px; border:2px solid {line_strong};
  box-shadow:8px 8px 0 {shadow}; background:{rgba(.1)}; }}
.bar {{ height:48px; border-bottom:2px solid {line_strong}; display:flex; align-items:center; gap:12px; padding:0 16px;
  background:{bar}; font-size:24px; font-weight:600; letter-spacing:.02em; color:{V.MUTED}; }}
.bar span {{ flex:1; }}
.bar .glyph {{ display:block; width:13px; height:13px; background:{V.PRIMARY}; flex:none; }}
.bar .controls {{ display:flex; gap:6px; }}
.bar .controls i {{ display:grid; place-items:center; width:23px; height:23px; border:2px solid {line_strong}; font-style:normal; font-size:17px; line-height:1; }}
.head {{ position:absolute; left:117px; top:226px; width:{W_INNER}px; }}
.kicker {{ margin:0 0 26px; font-size:34px; font-weight:600; letter-spacing:.02em; color:{V.MUTED}; white-space:nowrap; }}
.kicker::before {{ content:"> "; color:{V.PRIMARY}; }}
h1 {{ margin:0; font-weight:800; letter-spacing:-.07em; line-height:1.03; }}
h1 > span {{ display:block; white-space:nowrap; }}
.cursor {{ display:inline-block; width:.5em; height:.72em; margin-left:.12em; background:{V.PRIMARY}; vertical-align:baseline; }}
.subtitle {{ margin:36px 0 0; font-size:45px; font-weight:600; letter-spacing:-.06em; line-height:1.2; color:{V.MUTED}; }}
.subtitle span {{ display:block; }}
.art {{ position:absolute; inset:0; }}
.dot {{ position:absolute; left:968px; top:69px; width:22px; height:22px; background:{V.PRIMARY}; box-shadow:4px 4px 0 {accent_shadow}; transform:rotate(-7deg); }}
.square {{ position:absolute; left:63px; top:1815px; width:38px; height:38px; border:2px solid {line_strong}; transform:rotate(10deg); }}
</style>
</head>
<body>
<div id="cover" data-composition-id="cover" data-start="0" data-width="1080" data-height="1920" data-duration="1">
  <img class="photo" src="frame.jpg" alt="">
  <div class="fade"></div>
  <div class="grid"></div>
  <div class="dot"></div>
  <section class="window">
    <header class="bar"><i class="glyph"></i><span>{html.escape(window_title)}</span><div class="controls"><i>_</i><i>□</i><i>×</i></div></header>
  </section>
  <div class="head">{kicker_html}<h1>{"".join(title_html)}</h1>{subtitle_html}</div>
  <div class="art v-stage" style="position:absolute;left:0;top:0">{art}</div>
  <div class="square"></div>
</div>
<script>
window.__timelines = window.__timelines || {{}};
window.__timelines["cover"] = gsap.timeline({{ paused: true }});
</script>
</body>
</html>
"""
    (out / "index.html").write_text(doc)

    # 5. Render with HyperFrames (deterministic fonts, same renderer as the reel).
    shot = out / "shot"
    shutil.rmtree(shot, ignore_errors=True)
    subprocess.run([common.npx(), "--yes", _hyperframes_pin(), "snapshot", str(out), "-o", str(shot), "--at", "0.5"],
                   check=True, capture_output=True)
    png = next(shot.glob("frame-*.png"))
    target = common.p(f"renders/{common.CONFIG['id']}-cover.png")
    target.parent.mkdir(exist_ok=True)
    shutil.copy(png, target)
    print(f"  cover → {target.relative_to(common.PROJECT)} (frame {source} @ {at:.2f}s)")
