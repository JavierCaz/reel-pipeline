"""Step 6 (+7) — narration-timed concept visuals and their sound effects.

Library for scene files. A project's scripts/scenes.py is executed in this module's
namespace, so it can use Scene, T, the palette constants, icons, and helpers directly.
Each scene is a sub-composition in src/visuals/<slug>.html above the presenter; every
element enters on the word that introduces it (T("phrase", after) looks the time up in
scripts/transcript.json). Outputs scripts/visual-scenes.json and scripts/visual-sfx.json,
which cut.py mounts. API reference: _shared/pipeline/docs/visual-system.md.

Seek-safe by construction: every tween is an explicit fromTo with tracked state, and
the Scene class refuses overlapping tweens on the same property or tweens past a
scene's end. When it raises, retime the beat; do not loosen the check.
"""
from __future__ import annotations

import html
import json
import math
import re
import textwrap
import unicodedata

from . import common, presets

P = common.PROJECT
OUT = P / "src/visuals"
OUT.mkdir(parents=True, exist_ok=True)
WORDS = common.read_json("scripts/transcript.json")
_CUTMAP = common.read_json("scripts/cut-map.json")
DURATION = _CUTMAP["duration"]                                   # includes the outro tail
OUTRO_START = _CUTMAP.get("outro", {}).get("start", DURATION)    # where the end card's curtain starts
T = common.make_T(WORDS)
CUTS = common.read_json("scripts/cut-map.json")["clips"]
OPENING_TITLE = common.CONFIG.get("opening_title", [])  # exact on-screen title lines from the brief
from .cut import stage_segments  # noqa: E402
STAGE = stage_segments(common.CONFIG.get("stage", []), CUTS)  # presenter layouts: [{mode, start, end, clip}]


def clip_start(n: int) -> float:
    """Timeline start of clip n (1-based)."""
    return CUTS[n - 1]["timeline_in"]


def clip_end(n: int) -> float:
    """Timeline end of clip n (1-based)."""
    return CUTS[n - 1]["timeline_out"]
_V = common.CONFIG.get("visuals", {})
PREFIX = common.CONFIG["visual_prefix"]

# Palette (reel.config.json "visuals.palette"). Semantic roles:
#   INK text · PRIMARY main accent/lines · ACCENT data/underlines/glow · WARM soft highlight
#   SOFT secondary fill · PAPER card/ivory fill · ALERT warnings (contrast-safe on PAPER)
#   MUTED secondary text · HOT the viewer ("Tú") and hot accents
_THEME = presets.theme(common.CONFIG)  # defaults for "visuals.theme"; config keys override them
_PAL = {**_THEME["palette"], **_V.get("palette", {})}
INK, PRIMARY, ACCENT, WARM, SOFT, PAPER = (_PAL[k] for k in ("ink", "primary", "accent", "warm", "soft", "paper"))
ALERT, MUTED, HOT = _PAL["alert"], _PAL["muted"], _PAL["hot"]
FONT = _V.get("font", _THEME["font"])


def rgb(hex_color: str) -> str:
    h = hex_color.lstrip("#")
    return ",".join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))


SHADOW = f"0px 0px 0px 0px rgba({rgb(ACCENT)},0), 0px 14px 30px 0px rgba({rgb(INK)},0.16)"
GLOW = f"0px 0px 0px 7px rgba({rgb(ACCENT)},0.95), 0px 18px 36px 0px rgba({rgb(INK)},0.24)"
# Card fills. Hand-tuned per palette; override any of them in "visuals.tints".
TINTS = {
    "glass": "linear-gradient(135deg,rgba(255,255,255,.62),rgba(240,242,252,.5) 58%,rgba(222,226,255,.48))",
    "accent": "linear-gradient(135deg,rgba(236,252,255,.82),rgba(150,226,236,.62) 62%,rgba(190,222,240,.6))",
    "warm": "linear-gradient(135deg,rgba(255,244,236,.8),rgba(255,201,176,.7) 62%,rgba(255,214,200,.62))",
    "soft": "linear-gradient(135deg,rgba(244,246,255,.8),rgba(186,199,255,.68) 62%,rgba(205,214,255,.6))",
    "paper": "linear-gradient(135deg,rgba(255,255,255,.86),rgba(244,243,237,.8))",
    "ink": f"linear-gradient(135deg,#2b3566,{INK})",
    **_V.get("tints", {}),
}
# The frosted upper panel (0-735 px, fades out from 79%).
PANEL = _V.get("panel", "linear-gradient(135deg,rgba(236,238,250,.92),rgba(221,225,246,.86) 65%,rgba(212,232,242,.76))")

CSS = """
.v-stage{position:absolute;left:0;top:0;width:1080px;height:1920px;pointer-events:none;color:%(ink)s;font-family:"%(font)s",sans-serif}
.v-el{position:absolute;box-sizing:border-box}
.v-in{position:absolute;inset:0;box-sizing:border-box}
.v-in svg{display:block;width:100%%;height:100%%;overflow:visible}
.v-bg{background:%(panel)s;
  backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);mask-image:linear-gradient(#000 0%%,#000 79%%,transparent 100%%);
  -webkit-mask-image:linear-gradient(#000 0%%,#000 79%%,transparent 100%%)}
.v-light{position:absolute;inset:0;background:linear-gradient(118deg,transparent 12%%,rgba(255,255,255,.22) 34%%,transparent 53%%)}
.v-text{display:flex;align-items:center;justify-content:center;text-align:center;font-weight:750;line-height:1.12;letter-spacing:-.03em}
.v-head{justify-content:flex-start;text-align:left;font-weight:900;letter-spacing:-.05em;white-space:nowrap}
.v-card{border-radius:26px;border:2px solid rgba(255,255,255,.78);
  box-shadow:0px 0px 0px 0px rgba(%(accent)s,0),0px 14px 30px 0px rgba(%(ink_rgb)s,.16);overflow:hidden}
.v-card::before{content:"";position:absolute;inset:0;border-radius:24px;pointer-events:none;
  box-shadow:inset 0 2px 1px rgba(255,255,255,.65),inset 0 -2px 1px rgba(186,199,255,.22)}
.v-pill{border-radius:999px}
.v-tile{border-radius:32px;border:2px solid rgba(232,234,255,.75);color:%(ink)s;font-weight:900;letter-spacing:-.06em;
  box-shadow:0px 0px 0px 0px rgba(%(accent)s,0),0px 22px 46px 0px rgba(0,0,0,.2)}
.v-tile::before{content:"";position:absolute;inset:0;border-radius:30px;box-shadow:inset 0 2px 1px rgba(255,255,255,.5),inset 0 -2px 1px rgba(186,199,255,.25)}
.v-icon-label{position:absolute;left:0;right:0;bottom:12px;text-align:center;font-weight:750;letter-spacing:-.03em}
.v-dot{border-radius:50%%}
.v-pearl{border-radius:50%%;background:radial-gradient(circle at 30%% 23%%,#ffecdf 0%%,rgba(255,192,159,.85) 20%%,rgba(207,149,159,.35) 64%%,rgba(255,224,214,.6) 100%%);
  border:1px solid rgba(255,238,224,.55);box-shadow:9px 16px 28px rgba(0,0,0,.14)}
.v-capsule{border-radius:24px;background:linear-gradient(150deg,rgba(224,229,255,.6),rgba(164,180,252,.22));border:2px solid rgba(220,232,255,.6);
  box-shadow:inset 0 3px 9px rgba(255,255,255,.22),0 15px 25px rgba(0,0,0,.1)}
.v-cube{border-radius:13px;background:linear-gradient(145deg,rgba(%(accent)s,.5),rgba(%(accent)s,.1));border:2px solid rgba(200,244,250,.6);
  box-shadow:inset 3px 3px 8px rgba(237,255,249,.16),0 12px 20px rgba(0,0,0,.1)}
""" % {"ink": INK, "font": FONT, "panel": PANEL, "accent": rgb(ACCENT), "ink_rgb": rgb(INK)}

# Theme-level tokens used by helpers and scenes (glass values reproduce the original look).
THEME = _V.get("theme", "terminal")
TERMINAL = _THEME.get("family") == "terminal"   # terminal and terminal-light share the motifs
TILE_BG = "linear-gradient(135deg,rgba(246,247,255,.6),rgba(201,195,255,.4) 58%,rgba(170,232,240,.4))"
SURFACE = "#fff"                      # bright fill inside icons/bubbles
TRACK = "rgba(24,32,64,.12)"          # empty part of bars and placeholder lines
DOT_SHADOW = "0 3px 8px rgba(24,32,64,.18)"
CARD_SHADOW = "0 12px 26px rgba(24,32,64,.16)"
LINE = "#c9c3ff"                      # quiet rules (heading underline in terminal theme)
ON_FILL = INK                         # marks drawn on bright fills (check, ?, play, pupil)
HOT_TEXT = ALERT                      # text in the viewer's colour (HOT fails contrast on light panels)
DEVICE = (INK, 0)                     # phone body fill, outline width
WIN_BG, BAR_BG, WIN_BORDER = "rgba(255,255,255,.35)", "rgba(255,255,255,.6)", "rgba(255,255,255,.78)"
MONO_ADVANCE = 0.54                   # JetBrains Mono advance (0.6em) with -.06em tracking; slot width per character
MARK = "#fff"                         # small highlight marks (eye glint, follow +)

if TERMINAL:
    # Terminal / quadrille look from the javiercazares.dev portfolio: near-black grid paper, one lime
    # accent, square corners, 1-2 px rules, hard offset shadows, monospace, block cursor.
    _T = {**_THEME["surface"], **_V.get("terminal", {})}   # dark or light surface tokens (presets.THEMES)
    SHADOW = f"0px 0px 0px 0px rgba({rgb(PRIMARY)},0), 8px 8px 0px 0px rgba({rgb(_T['shadow'])},1)"
    GLOW = f"0px 0px 0px 4px rgba({rgb(PRIMARY)},1), 8px 8px 0px 0px rgba({rgb(_T['accent_shadow'])},1)"
    TINTS = {
        "glass": f"{_T['panel']};border-color:{_T['line_strong']}",
        "accent": f"{_T['tint_accent']};border-color:{PRIMARY}",
        "warm": f"{_T['tint_warm']};border-color:{WARM}",
        "soft": f"{_T['panel2']};border-color:{_T['line']}",
        "paper": f"{_T['panel']};border-color:{_T['line_strong']}",
        "ink": f"{INK};border-color:{INK};color:{_T['bg']}",
        **_V.get("tints", {}),
    }
    TILE_BG = f"{PRIMARY}"
    SURFACE = _T["panel"]
    TRACK = _T["shadow"]
    DOT_SHADOW = f"2px 2px 0 {_T['shadow']}"
    CARD_SHADOW = f"6px 6px 0 {_T['shadow']}"
    LINE = _T["line_strong"]
    ON_FILL = _T["bg"]
    HOT_TEXT = _T.get("hot_text", HOT)
    DEVICE = (_T["panel2"], 5)
    WIN_BG, BAR_BG, WIN_BORDER = f"rgba({rgb(_T['panel'])},.78)", _T["panel2"], _T["line_strong"]
    MARK = _T["bg"]
    grid = _V.get("grid", 32)
    PANEL = _V.get("panel", (
        f"linear-gradient({_T['grid_major']} 2px,transparent 2px) -1px -1px/{grid * 4}px {grid * 4}px,"
        f"linear-gradient(90deg,{_T['grid_major']} 2px,transparent 2px) -1px -1px/{grid * 4}px {grid * 4}px,"
        f"linear-gradient({_T['grid_minor']} 1px,transparent 1px) -1px -1px/{grid}px {grid}px,"
        f"linear-gradient(90deg,{_T['grid_minor']} 1px,transparent 1px) -1px -1px/{grid}px {grid}px,"
        f"rgba({rgb(_T['bg'])},.95)"))
    CSS = """
.v-stage{position:absolute;left:0;top:0;width:1080px;height:1920px;pointer-events:none;color:%(ink)s;font-family:"%(font)s",monospace}
.v-stage *{border-radius:0 !important}
.v-el{position:absolute;box-sizing:border-box}
.v-in{position:absolute;inset:0;box-sizing:border-box}
.v-in svg{display:block;width:100%%;height:100%%;overflow:visible}
.v-bg{background:%(panel)s;
  mask-image:linear-gradient(#000 0%%,#000 79%%,transparent 100%%);-webkit-mask-image:linear-gradient(#000 0%%,#000 79%%,transparent 100%%)}
.v-light{position:absolute;inset:0;background:linear-gradient(90deg,transparent 30%%,rgba(%(primary)s,.035) 45%%,transparent 60%%)}
.v-text{display:flex;align-items:center;justify-content:center;text-align:center;font-weight:600;line-height:1.12;letter-spacing:-.05em}
.v-head{justify-content:flex-start;text-align:left;font-weight:700;letter-spacing:-.07em;white-space:nowrap}
.v-card{border:2px solid %(line_strong)s;box-shadow:%(shadow)s;overflow:hidden}
.v-pill{}
.v-tile{border:2px solid %(primary_hex)s;color:%(bg)s;font-weight:800;letter-spacing:-.08em;box-shadow:0px 0px 0px 0px rgba(%(primary)s,0),10px 10px 0px 0px %(accent_shadow)s}
.v-icon-label{position:absolute;left:0;right:0;bottom:12px;text-align:center;font-weight:600;letter-spacing:-.04em}
.v-dot{}
.v-in.v-pearl{inset:12px;background:%(primary_hex)s;box-shadow:3px 3px 0 %(accent_shadow)s}
.v-capsule{border:2px solid %(line)s;background:linear-gradient(90deg,%(primary_hex)s 0 10px,transparent 10px)}
.v-cube{border:2px solid %(line_strong)s;background:transparent}
.v-kicker{font-size:22px;font-weight:600;letter-spacing:.07em;text-transform:uppercase;color:%(muted)s;white-space:nowrap}
""" % {"ink": INK, "font": FONT, "panel": PANEL, "primary": rgb(PRIMARY), "primary_hex": PRIMARY, "bg": _T["bg"],
       "line": _T["line"], "line_strong": _T["line_strong"], "shadow": SHADOW, "accent_shadow": _T["accent_shadow"],
       "muted": MUTED}

# Terminal motifs (decode slots, cursors) work in every theme.
CSS += """
.v-slot{display:inline-block;position:relative;height:var(--lh);vertical-align:top;clip-path:inset(0 -50% 0 -50%)}
.v-strip{position:absolute;left:0;top:0;width:100%}
.v-slot b{display:block;height:var(--lh);line-height:var(--lh);text-align:center;font-weight:inherit}
.v-cursor{position:absolute;left:8%;top:14%;width:84%;height:72%}
"""

DEFAULTS = {"x": 0, "y": 0, "scale": 1, "scaleX": 1, "scaleY": 1, "rotation": 0, "opacity": 1,
            "rotationY": 0, "rotationX": 0, "boxShadow": SHADOW}
NON_STATE = {"repeat", "yoyo", "transformOrigin", "transformPerspective", "svgOrigin"}

# Peak-normalised gains: effects peak roughly 12 dB below speech.
SFX = {
    "pop": (0.72, 0.26), "click": (0.37, 0.30), "click-soft": (0.37, 0.24), "ping": (1.32, 0.34),
    "sparkle": (1.8, 0.18), "whoosh-short": (0.57, 0.18), "whoosh": (0.57, 0.16), "typing": (1.5, 0.5),
    "key-press": (0.4, 0.34), "error": (1.62, 0.85), "impact-bass-1": (2.12, 0.12), "chime": (2.5, 0.42),
    "notification": (2.46, 0.22), "glitch-2": (0.35, 0.12),
}

scenes: list["Scene"] = []
sounds: list[dict] = []


def j(value) -> str:
    return json.dumps(value, ensure_ascii=False)


class Scene:
    def __init__(self, slug: str, start: float, end: float, decor=((60, 612, "pearl"), (918, 150, "capsule")),
                 panel: str = "slide", track: int = 11, layer: str = "graphics"):
        """panel: how the graphics panel appears when the scene opens it: "slide", "instant"
        (visible on the first frame — use for the opening hook), or "none" (no panel; full-frame
        overlays). track/layer: scenes on another track may overlap the panel scenes;
        layer "overlay" sits above captions (end cards)."""
        self.slug, self.start, self.end = slug, round(start, 3), round(min(end, DURATION), 3)
        self.id = f"{PREFIX}-{slug}"
        self.parts: list[str] = []
        self.js: list[str] = []
        self.state: dict[str, dict] = {}
        self.busy: dict[tuple, list] = {}
        self.live: list[str] = []
        self.decor = decor
        self.panel = panel
        self.track, self.layer = track, layer
        self.count = 0
        scenes.append(self)

    # --- timing -----------------------------------------------------------
    def local(self, t: float) -> float:
        if not (self.start - 1e-6 <= t <= self.end + 1e-6):
            raise ValueError(f"{self.slug}: time {t} outside {self.start}-{self.end}")
        return round(t - self.start, 3)

    def sel(self, key: str) -> str:
        return f"#{self.id}-{key}"

    # --- seek-safe tween primitives ----------------------------------------
    def set(self, target: str, **props):
        self.js.append(f"tl.set({j(target)},{j(props)},0);")
        self.state.setdefault(target, {}).update({k: v for k, v in props.items() if k not in NON_STATE})

    def tw(self, target: str, t: float, duration: float, ease: str = "power2.inOut", **to):
        state = self.state.setdefault(target, {})
        start = self.local(t)
        span = duration * (to.get("repeat", 0) + 1)
        if start + span > self.end - self.start + 0.02:
            raise ValueError(f"{self.slug}: tween on {target} at {t} runs past scene end")
        frm = {}
        for prop, value in to.items():
            if prop in NON_STATE:
                continue
            frm[prop] = state.get(prop, DEFAULTS.get(prop))
            if frm[prop] is None:
                raise ValueError(f"{self.slug}: no start value for {prop} on {target}")
            for a, b in self.busy.setdefault((target, prop), []):
                if start < b - 1e-3 and a < start + span - 1e-3:
                    raise ValueError(f"{self.slug}: overlapping {prop} tweens on {target} at {t}")
            self.busy[(target, prop)].append((start, start + span))
        options = {**to, "duration": duration, "ease": ease, "immediateRender": False}
        self.js.append(f"tl.fromTo({j(target)},{j(frm)},{j(options)},{start:.3f});")
        returns = to.get("yoyo") and to.get("repeat", 0) % 2 == 1
        if not returns:
            state.update({k: v for k, v in to.items() if k not in NON_STATE})

    def sfx(self, t: float, kind: str, gain: float | None = None):
        self.local(t)
        length, default_gain = SFX[kind]
        sounds.append({"at": round(t, 3), "kind": kind, "length": length,
                       "volume": round(default_gain if gain is None else gain, 3), "scene": self.slug})

    # --- elements -----------------------------------------------------------
    def add(self, key: str, x, y, w, h, inner="", cls="", style="", z=None, origin=None):
        # The scene's own containers use these ids; reusing one makes element tweens hit the whole scene.
        if key in ("root", "stage", "bg", "bg-light") or (key.startswith("decor") and key[5:].isdigit()):
            raise ValueError(f"{self.slug}: key {key!r} is reserved for the scene container; rename it")
        zs =f"z-index:{z};" if z is not None else ""
        self.parts.append(
            f'<div id="{self.id}-{key}" class="v-el" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;{zs}">'
            f'<div id="{self.id}-{key}-in" class="v-in {cls}" style="{style}">{inner}</div></div>')
        init = {"opacity": 0}
        if origin:
            init["transformOrigin"] = origin
        self.set(self.sel(key), **init)
        return key

    ENTER = {
        "up": ({"y": 40}, 0.45, "power3.out"),
        "down": ({"y": -40}, 0.45, "power3.out"),
        "left": ({"x": -105}, 0.42, "expo.out"),
        "right": ({"x": 105}, 0.42, "expo.out"),
        "pop": ({"scale": 0.35, "rotation": -8}, 0.5, "back.out(1.7)"),
        "stamp": ({"scale": 1.9, "rotation": 14}, 0.3, "power4.out"),
        "tilt": ({"x": 150, "y": -35, "scale": 1.25, "rotation": 14}, 0.54, "back.out(1.1)"),
        "drop": ({"y": -170}, 0.62, "bounce.out"),
        "rise": ({"scaleY": 0}, 0.5, "back.out(1.3)"),
        "wipe": ({"scaleX": 0}, 0.45, "power3.out"),
        "grow": ({"scale": 0.15}, 0.6, "back.out(1.2)"),
        "fade": ({}, 0.3, "power1.out"),
    }

    def enter(self, key, t, kind="up", sfx=None, rest=None, gain=None):
        offset, duration, ease = self.ENTER[kind]
        target = self.sel(key)
        state = self.state[target]
        rest = rest or {}
        start_pose = {**{k: rest.get(k, DEFAULTS[k]) for k in ("x", "y", "scale", "rotation")}}
        for k, v in offset.items():
            start_pose[k] = (rest.get(k, DEFAULTS[k]) + v) if k in ("x", "y") else v
        start_pose = {k: v for k, v in start_pose.items() if state.get(k, DEFAULTS[k]) != v or k in offset}
        self.js.append(f"tl.set({j(target)},{j(start_pose)},0);")
        state.update(start_pose)
        end_pose = {k: rest.get(k, DEFAULTS[k]) for k in start_pose}
        if kind == "tilt":
            end_pose["rotation"] = rest.get("rotation", -6)
        self.tw(target, t, duration, ease, opacity=1, **end_pose)
        if key not in self.live:
            self.live.append(key)
        if sfx:
            self.sfx(t, sfx, gain)
        return key

    EXIT = {
        "up": ({"y": -40}, 0.3, "power2.in"),
        "down": ({"y": 60}, 0.3, "power2.in"),
        "left": ({"x": -90}, 0.3, "power3.in"),
        "right": ({"x": 90}, 0.3, "power3.in"),
        "shrink": ({"scale": 0.5}, 0.28, "power2.in"),
        "fade": ({}, 0.25, "power1.in"),
    }

    def exit(self, key, t, kind="up"):
        offset, duration, ease = self.EXIT[kind]
        target = self.sel(key)
        state = self.state[target]
        props = {"opacity": 0}
        for k, v in offset.items():
            props[k] = state.get(k, DEFAULTS[k]) + v if k in ("x", "y") else state.get(k, 1) * v
        self.tw(target, t, duration, ease, **props)
        if key in self.live:
            self.live.remove(key)
        if key + "-cursor" in self.live:  # a terminal heading's cursor leaves with it
            self.exit(key + "-cursor", t, "fade")
        if key + "-head" in self.live:  # a line's arrowhead leaves with it
            self.exit(key + "-head", t, kind if kind in ("fade", "up", "down") else "fade")

    def move(self, key, t, duration=0.5, ease="power3.inOut", **props):
        self.tw(self.sel(key), t, duration, ease, **props)

    def inner(self, key, t, duration=0.4, ease="power2.inOut", **props):
        self.tw(self.sel(key) + "-in", t, duration, ease, **props)

    def pulse(self, key, t, amount=1.1, sfx=None, glow=False):
        self.inner(key, t, 0.17, "power2.out", scale=amount, repeat=1, yoyo=True)
        if glow:
            self.inner(key, t, 0.22, "power2.out", boxShadow=GLOW)
            if t + 1.1 < self.end - 0.36:
                self.inner(key, t + 0.75, 0.35, "power2.inOut", boxShadow=SHADOW)
        if sfx:
            self.sfx(t, sfx)

    def glow(self, key, t, until=None):
        self.inner(key, t, 0.22, "power2.out", boxShadow=GLOW)
        if until:
            self.inner(key, until, 0.3, "power2.inOut", boxShadow=SHADOW)

    def dim(self, keys, t, opacity=0.32):
        for key in keys:
            self.move(key, t, 0.35, "power2.out", opacity=opacity)

    def float(self, key, t, until, dy=-9, rot=2.0):
        n = max(1, int((until - t) / 1.3))
        n = n if n % 2 == 1 else n - 1 if n > 1 else 1
        duration = (until - t) / (n + 1)
        self.inner(key, t, duration, "sine.inOut", y=dy, rotation=rot, repeat=n, yoyo=True)

    # --- life: idle motion that fills the gaps (user 2026-10-12: "keep this in our animation style") ----
    # Important elements never sit still: they hover, breathe, blink, glance. These helpers schedule
    # seek-safe yoyo loops only AFTER the target's own tweens on the same property, so they never fight
    # an entrance, a move, or a scripted beat. Call them at the end of a scene, after its beats.
    def _after(self, target, prop):
        """Absolute time when the last tween on (target, prop) ends (the scene start if none)."""
        return self.start + max((b for _, b in self.busy.get((target, prop), [])), default=0.0)

    def _free(self, target, prop, a, b):
        return all(not (a - self.start < y - 1e-3 and x < b - self.start - 1e-3) for x, y in self.busy.get((target, prop), []))

    def loop(self, target, t, until, period, ease="sine.inOut", **offsets):
        """Yoyo `target` between its current values and current + offsets from t until `until`."""
        t = max([t] + [self._after(target, k) + 0.02 for k in offsets])
        until = min(until, self.end - 0.38)
        legs = int((until - t) / period)
        legs -= legs % 2                  # an even number of legs ends at rest
        if legs < 2:                      # a late arrival in a short window: one quicker cycle if it fits
            if until - t < 0.6:
                return
            legs, period = 2, round((until - t) / 2, 3)
        state = self.state.setdefault(target, {})
        to = {}
        for k, d in offsets.items():
            base = state.get(k, DEFAULTS.get(k, 0))
            to[k] = round(base * d if k in ("scale", "scaleX", "scaleY") else base + d, 3)
            state.setdefault(k, base)
        self.tw(target, round(t, 3), period, ease, repeat=legs - 1, yoyo=True, **to)

    def hover(self, key, t, until=None, dy=-8, period=0.9):
        """A gentle float on the element's inner layer (like a drone)."""
        self.loop(self.sel(key) + "-in", t, until or self.end, period, y=dy)

    def breathe(self, key, t, until=None, amount=1.035, period=1.1):
        """A slow scale pulse on the inner layer (a card or icon that is "on")."""
        self.set(self.sel(key) + "-in", transformOrigin="50% 50%")
        self.loop(self.sel(key) + "-in", t, until or self.end, period, scale=amount)

    def wobble(self, key, t, until=None, deg=4, period=0.7):
        """A small rocking rotation on the inner layer (question marks, warnings)."""
        self.loop(self.sel(key) + "-in", t, until or self.end, period, rotation=deg)

    def robot_life(self, key, t, until=None, blink=True, look=True, antenna=True, core=True, arms=True, phase=0.0):
        """Idle life for an i_robot pet (parts eyes, ant, core, arm-l, arm-r): blinks every ~1.8 s, a glance
        to the side, an antenna/halo bob, a pulsing chest light, a slight arm sway. Each part only moves
        where it is free; `phase` offsets the rhythm so two pets don't blink in unison."""
        until = min(until or self.end, self.end - 0.38)
        sub = lambda part: self.sub(key, part)  # noqa: E731
        if blink:
            at = t + 0.7 + phase
            while at + 0.16 < until:
                if self._free(sub("eyes"), "scaleY", at, at + 0.16):
                    self.tw(sub("eyes"), round(at, 3), 0.08, "power1.inOut", scaleY=0.1, repeat=1, yoyo=True)
                at += 1.7 + (0.35 if int((at - t) * 10) % 2 else 0.0)
        if look:
            self.loop(sub("eyes"), t + 1.1 + phase, until, 0.55, "power2.inOut", x=3)
        if antenna:
            self.loop(sub("ant"), t + 0.2 + phase / 2, until, 0.45, y=-2.5)
        if core:
            self.loop(sub("core"), t + 0.3, until, 0.6, scale=1.25)
        if arms:
            self.loop(sub("arm-l"), t + 0.4 + phase, until, 0.8, rotation=8)
            self.loop(sub("arm-r"), t + 0.8 + phase, until, 0.8, rotation=-8)

    def sub(self, key, part) -> str:
        return f"#{self.id}-{key}-{part}"

    # --- composed pieces ----------------------------------------------------
    def text(self, key, label, x, y, w, h, size=34, weight=None, color=INK, cls="", style=""):
        fw = f"font-weight:{weight};" if weight else ""
        if TERMINAL and "v-head" in cls:  # left-aligned titles get the `>` prompt
            body = f'<span style="color:{PRIMARY}">&gt;</span>&nbsp;{html.escape(label)}'
            return self.add(key, x, y, w, h, body, f"v-text {cls}", f"font-size:{size}px;color:{color};{fw}{style}")
        return self.add(key, x, y, w, h, html.escape(label), f"v-text {cls}", f"font-size:{size}px;color:{color};{fw}{style}")

    def card(self, key, label, x, y, w, h, tint="glass", size=34, icon=None, icon_h=None, color=INK, pill=False, style=""):
        body = html.escape(label) if label else ""
        if icon:
            ih = icon_h or (h * (0.58 if label else 0.78))
            pad = 14 if label else (h - ih) / 2
            body = (f'<div style="position:absolute;left:0;right:0;top:{pad}px;height:{ih}px;display:flex;justify-content:center">'
                    f'<div style="width:{ih}px;height:{ih}px">{icon}</div></div>')
            if label:
                body += f'<div class="v-icon-label" style="font-size:{size}px">{html.escape(label)}</div>'
        cls = "v-card v-text" + (" v-pill" if pill else "")
        return self.add(key, x, y, w, h, body, cls, f"background:{TINTS[tint]};font-size:{size}px;color:{color};{style}")

    def tile(self, key, label, x, y, w, h, size=120, tint="glass"):
        bg = TILE_BG if tint == "glass" else TINTS[tint]
        return self.add(key, x, y, w, h, html.escape(label), "v-tile v-text", f"background:{bg};font-size:{size}px;padding-bottom:4px")

    def art(self, key, svg, x, y, w, h, **kw):
        return self.add(key, x, y, w, h, svg, **kw)

    def heading(self, label, t, x=110, y=196, size=52, key="heading", underline=True):
        if TERMINAL:
            return self._terminal_heading(label, t, x, y, size, key, underline)
        width = min(860, int(len(label) * size * 0.6) + 20)
        self.text(key, label, x, y, width, 72, size, cls="v-head")
        self.enter(key, t, "left")
        if underline:
            self.line(key + "-line", [(x + 4, y + 78), (x + width * 0.72, y + 80)], t + 0.35, color=ACCENT, width=4, opacity=0.8, head=False)
        return key

    def line(self, key, points, t, color=PRIMARY, width=5, opacity=1.0, head=True, duration=0.45, curve=None):
        (x1, y1), (x2, y2) = points[0], points[-1]
        # Without a curve, every point is a vertex (a polyline); two points give a straight segment.
        d = f"M{x1} {y1} " + (f"Q{curve[0]} {curve[1]} {x2} {y2}" if curve else " ".join(f"L{x} {y}" for x, y in points[1:]))
        # The canvas covers the top panel; lines reaching the lower frame (presenter layouts) get the full height.
        canvas_h = 1920 if max(y for _, y in list(points) + ([curve] if curve else [])) > 740 else 760
        body = (f'<svg viewBox="0 0 1080 {canvas_h}"><path id="{self.id}-{key}-path" d="{d}" pathLength="1" fill="none" stroke="{color}" '
                f'stroke-width="{width}" stroke-linecap="round" stroke-dasharray="1" stroke-opacity="{opacity}"/></svg>')
        self.add(key, 0, 0, 1080, canvas_h, body)
        path = self.sub(key, "path")
        self.set(path, strokeDashoffset=1)
        self.tw(self.sel(key), t, 0.05, "none", opacity=1)
        self.tw(path, t, duration, "power2.out", strokeDashoffset=0)
        self.live.append(key)
        if head:
            fx, fy = curve if curve else points[-2]
            angle = math.degrees(math.atan2(y2 - fy, x2 - fx))
            hk = key + "-head"
            self.add(hk, x2 - 13, y2 - 13, 26, 26,
                     f'<svg viewBox="0 0 26 26"><path d="M6 4L22 13L6 22Z" fill="{color}" fill-opacity="{opacity}"/></svg>')
            self.set(self.sel(hk), rotation=round(angle, 1))
            self.enter(hk, t + duration - 0.12, "fade", rest={"rotation": round(angle, 1)})
        return key

    def travel(self, key, points, t, duration=0.6, color=PRIMARY, size=16):
        """A dot that runs along a polyline and vanishes, showing flow along a connector."""
        x0, y0 = points[0]
        self.add(key, x0 - size / 2, y0 - size / 2, size, size, "", "v-dot",
                 f"background:{color};box-shadow:0 0 0 5px rgba(47,196,212,.35)")
        self.tw(self.sel(key), t, 0.08, "none", opacity=1)
        seg = duration / (len(points) - 1)
        for i, (px, py) in enumerate(points[1:]):
            self.tw(self.sel(key), t + i * seg, seg, "none" if 0 < i < len(points) - 2 else "power1.inOut", x=px - x0, y=py - y0)
        self.tw(self.sel(key), t + duration, 0.1, "power1.in", opacity=0)

    def strike(self, key, x1, y1, x2, y2, t, sfx="error"):
        self.line(key, [(x1, y1), (x2, y2)], t, color=ALERT, width=9, head=False, duration=0.3)
        if sfx:
            self.sfx(t, sfx)

    def _terminal_heading(self, label, t, x, y, size, key, underline):
        """`> label█` — lime prompt, monospace label, blinking block cursor (seek-safe steps)."""
        advance = size * 0.53  # JetBrains Mono advance (0.6em) minus .07em tracking
        text_w = (len(label) + 2) * advance
        width = min(900, int(text_w) + 30)
        body = f'<span style="color:{PRIMARY}">&gt;</span>&nbsp;{html.escape(label)}'
        self.add(key, x, y, width, 72, body, "v-text v-head", f"font-size:{size}px;color:{INK}")
        self.enter(key, t, "left")
        cursor = key + "-cursor"
        self.add(cursor, x + min(text_w, width - 20) + 8, y + 12, round(size * 0.5), 48, "", "", f"background:{PRIMARY}")
        self.enter(cursor, t + 0.3, "fade")
        self._blink(self.sel(cursor) + "-in", t + 0.75)
        if underline:
            self.line(key + "-line", [(x, y + 80), (x + width, y + 80)], t + 0.35, color=LINE, width=2, head=False)
        return key

    # --- terminal motifs (house style; usable in any theme) ------------------
    def _blink(self, selector, start, period=0.53):
        """Seek-safe block-cursor blink from `start` until just before the scene's exits."""
        repeats = int((self.end - 0.45 - start) / period) - 1
        repeats -= 0 if repeats % 2 else 1  # odd: ends visible, so exits stay continuous
        if repeats >= 1:
            self.tw(selector, start, period, "steps(1)", opacity=0, repeat=repeats, yoyo=True)

    def window(self, key, x, y, w, h, title, t, bar=44, crt=True, sfx=None, gain=None):
        """Portfolio-style terminal window: bar with lime glyph, title, and controls; hard shadow.
        crt=True powers it on like a CRT (a bright line that opens vertically)."""
        glyph = round(bar * 0.28)
        controls = "".join(f'<i style="display:grid;place-items:center;width:{bar - 22}px;height:{bar - 22}px;'
                           f'border:2px solid {WIN_BORDER};font-style:normal;font-size:{round(bar * 0.36)}px;line-height:1">{c}</i>'
                           for c in ("_", "□", "×"))
        inner = (f'<div style="position:absolute;left:0;right:0;top:0;height:{bar}px;background:{BAR_BG};border-bottom:2px solid {WIN_BORDER};'
                 f'display:flex;align-items:center;gap:12px;padding:0 14px 0 16px;color:{MUTED};font-size:{round(bar * 0.5)}px;'
                 f'font-weight:600;letter-spacing:.02em;white-space:nowrap">'
                 f'<i style="display:block;width:{glyph}px;height:{glyph}px;background:{PRIMARY};flex:0 0 auto"></i>'
                 f'<span style="flex:1">{html.escape(title)}</span><span style="display:flex;gap:6px">{controls}</span></div>')
        self.add(key, x, y, w, h, inner, "v-card", f"background:{WIN_BG}", origin="50% 50%")
        if not crt:
            return self.enter(key, t, "fade", sfx, gain=gain)
        line = key + "-crt"
        self.add(line, x, y + h / 2 - 3, w, 6, "", "",
                 f"background:{PRIMARY};box-shadow:0 0 24px {PRIMARY},0 0 70px {PRIMARY}", origin="50% 50%")
        self.set(self.sel(line), scaleX=0.25)
        if t <= 0.001:
            self.set(self.sel(line), opacity=1)  # visible on the very first frame
        else:
            self.tw(self.sel(line), t, 0.03, "none", opacity=1)
        self.tw(self.sel(line), t, 0.12, "power3.out", scaleX=1)
        self.tw(self.sel(line), t + 0.14, 0.26, "power2.in", opacity=0, scaleY=0.2)
        self.set(self.sel(key), scaleY=0.012)
        self.tw(self.sel(key), t + 0.1, 0.04, "none", opacity=1)
        self.tw(self.sel(key), t + 0.1, 0.34, "expo.out", scaleY=1)
        self.live.append(key)
        if sfx:
            self.sfx(t, sfx, gain)
        return key

    def shot(self, key, src, x, y, w, h, title, at=0, bar=40, origin_x=50):
        """A screenshot (project-relative path, e.g. a tall full-page capture) in a terminal window
        frame: bar with the lime glyph and `title` (a URL or path), the image filling the width and
        clipped to the window. `at` = source-image pixel shown at the top. Hidden until entered;
        move it with s.scroll(). origin_x: horizontal zoom anchor in % of the image width."""
        from PIL import Image
        iw, ih = Image.open(P / src).size
        vw = w - 4
        glyph = round(bar * 0.28)
        img = f"{self.id}-{key}-img"
        inner = (f'<div style="position:absolute;left:0;right:0;top:0;height:{bar}px;background:{BAR_BG};border-bottom:2px solid {WIN_BORDER};'
                 f'display:flex;align-items:center;gap:10px;padding:0 14px;color:{MUTED};font-size:{round(bar * 0.5)}px;'
                 f'font-weight:600;white-space:nowrap;overflow:hidden">'
                 f'<i style="display:block;width:{glyph}px;height:{glyph}px;background:{PRIMARY};flex:0 0 auto"></i>'
                 f'<span>{html.escape(title)}</span></div>'
                 f'<div style="position:absolute;left:0;right:0;top:{bar}px;bottom:0;overflow:hidden">'
                 f'<img id="{img}" src="{html.escape(src)}" alt="" data-layout-allow-overflow style="position:absolute;left:0;top:0;display:block;'
                 f'width:{vw}px;height:{round(ih * vw / iw, 2)}px;max-width:none"></div>')
        self.add(key, x, y, w, h, inner, "v-card", f"background:{WIN_BG}", origin="50% 50%")
        self._shots = getattr(self, "_shots", {})
        self._shots[key] = vw / iw
        self.set("#" + img, transformOrigin=f"{origin_x}% 0%", y=round(-at * vw / iw, 2))
        return key

    def scroll(self, key, t, to, duration=1.2, ease="power2.inOut", scale=None):
        """Scroll a shot so source-image pixel `to` sits at the window top; `scale` zooms in
        (anchored at the shot's origin_x and the window top) for readable details."""
        k = self._shots[key]
        img = f"#{self.id}-{key}-img"
        s = scale if scale is not None else self.state.get(img, {}).get("scale", 1)
        props = {"y": round(-to * k * s, 2)}
        if scale is not None:
            props["scale"] = scale
        self.tw(img, t, duration, ease, **props)

    def photo(self, key, src, x, y, w, h=None, frame=None, title="", bar=40, fit="contain", trim=True,
              zoom=1.0, focus=(0.5, 0.5), credit=None):
        """A real image (project-relative path): a product cutout (transparent PNG) or a photograph.
        trim: crop a cutout's transparent margins (alpha bounding box) so the object fills the box.
        h=None: height from the visible region's aspect (plus the bar for a window).
        frame: None (bare; a cutout gets a hard drop shadow that follows its outline) | "card" (border and
        hard shadow) | "window" (terminal window bar with `title`). fit: "contain" | "cover".
        zoom > 1 enlarges the image inside its frame so s.pan() has room; focus = (fx, fy), the point of
        the region kept centred. credit: small attribution line on the image (CC BY photos).
        Hidden until entered; the <img> is `{key}-img` (s.pan moves it)."""
        from PIL import Image
        with Image.open(P / src) as im:
            iw, ih = im.size
            box = (0, 0, iw, ih)
            if trim and im.mode in ("RGBA", "LA", "P"):
                alpha = im.convert("RGBA").getchannel("A").point(lambda v: 255 if v > 8 else 0)
                box = alpha.getbbox() or box
        l, t, r, b = box
        rw, rh = r - l, b - t
        top = bar if frame == "window" else 0
        if h is None:
            h = round(w * rh / rw) + top
        vw, vh = w, h - top
        k = (min if fit == "contain" else max)(vw / rw, vh / rh) * zoom
        dw, dh = rw * k, rh * k

        def place(view, size, f):
            if size <= view:
                return (view - size) / 2
            return min(0.0, max(view - size, view / 2 - f * size))

        left, up = place(vw, dw, focus[0]), place(vh, dh, focus[1])
        img = f"{self.id}-{key}-img"
        cutout = box != (0, 0, iw, ih) or (frame is None and src.lower().endswith(".png"))
        shadow = _T["shadow"] if TERMINAL else "rgba(24,32,64,.28)"
        drop = f"filter:drop-shadow(10px 10px 0 {shadow});" if frame is None and cutout else ""
        inner = ""
        if frame == "window":
            glyph = round(bar * 0.28)
            inner += (f'<div style="position:absolute;left:0;right:0;top:0;height:{bar}px;background:{BAR_BG};border-bottom:2px solid {WIN_BORDER};'
                      f'display:flex;align-items:center;gap:10px;padding:0 14px;color:{MUTED};font-size:{round(bar * 0.5)}px;'
                      f'font-weight:600;white-space:nowrap;overflow:hidden">'
                      f'<i style="display:block;width:{glyph}px;height:{glyph}px;background:{PRIMARY};flex:0 0 auto"></i>'
                      f'<span>{html.escape(title)}</span></div>')
        inner += (f'<div style="position:absolute;left:0;right:0;top:{top}px;bottom:0;overflow:hidden;{drop}">'
                  f'<img id="{img}" src="{html.escape(src)}" alt="" data-layout-allow-overflow style="position:absolute;display:block;max-width:none;'
                  f'left:{round(left - l * k, 2)}px;top:{round(up - t * k, 2)}px;width:{round(iw * k, 2)}px;height:{round(ih * k, 2)}px"></div>')
        if credit:
            inner += (f'<div style="position:absolute;right:8px;bottom:6px;padding:2px 8px;background:rgba(0,0,0,.55);color:#e8e8e2;'
                      f'font-size:15px;font-weight:600;letter-spacing:.02em;white-space:nowrap">{html.escape(credit)}</div>')
        cls, style = ("v-card", f"background:{WIN_BG}") if frame else ("", "")
        self.add(key, x, y, w, h, inner, cls, style, origin="50% 50%")
        self.set("#" + img, transformOrigin="50% 50%")
        return key

    def pan(self, key, t, duration=2.0, ease="sine.inOut", x=None, y=None, scale=None):
        """Move a photo's image inside its frame (Ken Burns): x/y in screen px from its start, scale
        around the image centre; only the given properties move. Give the photo zoom > 1 (or
        fit="cover" with spare image) so the frame stays covered."""
        props = {k: v for k, v in (("x", x), ("y", y), ("scale", scale)) if v is not None}
        self.tw(f"#{self.id}-{key}-img", t, duration, ease, **props)

    def decode(self, key, text, x, y, size, t, color=INK, scramble=None, start_text=None, stagger=0.035,
               roll=0.34, steps=6, weight=800, cursor_at=None, glyphs="#$%&*+=?/<>01ABCDEFGHKMNPRSTVXZ",
               sfx=None, gain=None, origin="0% 0%"):
        """Slot-roll "decrypt" text: every character rolls through glyphs and locks, left to right.
        start_text: roll from this text instead of from blank (e.g. a clock 14:02 → 19:47; equal
        characters stay still). cursor_at: add a blinking block cursor after the text at that time.
        Returns the time the last character locks."""
        adv = round(size * MONO_ADVANCE, 2)
        lh = round(size * 1.1)
        scramble = scramble or ACCENT
        seed = sum(ord(c) * (i + 1) for i, c in enumerate(self.id + key)) % 2147483647 or 7
        parts, strips = [], []
        for i, ch in enumerate(text):
            first = start_text[i] if start_text else None
            if ch == " " or first == ch:
                glyph = "&nbsp;" if ch == " " else html.escape(ch)
                parts.append(f'<span class="v-slot" style="width:{adv}px"><b style="color:{color}">{glyph}</b></span>')
                continue
            seq = [first] if first is not None else []
            while len(seq) < steps:
                seed = (seed * 1103515245 + 12345) % 2147483648
                seq.append(glyphs[seed % len(glyphs)])
            glyph_html = "".join(f'<b style="color:{color if (first is not None and k == 0) else scramble}">{html.escape(g)}</b>'
                                 for k, g in enumerate(seq)) + f'<b style="color:{color}">{html.escape(ch)}</b>'
            sid = f"{self.id}-{key}-s{i}"
            parts.append(f'<span class="v-slot" style="width:{adv}px"><span id="{sid}" class="v-strip">{glyph_html}</span></span>')
            strips.append((sid, i))
        if cursor_at is not None:
            parts.append(f'<span class="v-slot" style="width:{adv}px"><i id="{self.id}-{key}-cur" class="v-cursor" '
                         f'style="background:{PRIMARY}"></i></span>')
        width = round(adv * (len(text) + (1 if cursor_at is not None else 0))) + 4
        body = (f'<div style="--lh:{lh}px;font-size:{size}px;font-weight:{weight};color:{color};white-space:nowrap;'
                f'line-height:{lh}px;letter-spacing:0">{"".join(parts)}</div>')
        self.add(key, x, y, width, lh, body, origin=origin)
        self.enter(key, t, "fade")
        locked = t
        for n, (sid, i) in enumerate(strips):
            at = t + n * stagger
            if start_text is None:
                self.set("#" + sid, opacity=0)
                self.tw("#" + sid, at, 0.02, "none", opacity=1)
            self.tw("#" + sid, at, roll, f"steps({steps})", y=-steps * lh)
            locked = at + roll
        if cursor_at is not None:
            cur = f"#{self.id}-{key}-cur"
            self.set(cur, opacity=0)
            self.tw(cur, cursor_at, 0.02, "none", opacity=1)
            self._blink(cur, cursor_at + 0.4)
        if sfx:
            self.sfx(t, sfx, gain)
        return round(locked, 3)

    def typewrite(self, key, label, x, y, size, t, cps=60, color=INK, weight=600, sfx=None, gain=None):
        """Monospace text revealed one character at a time (seek-safe stepped clip). Returns end time."""
        n = len(label)
        lh = round(size * 1.25)
        body = (f'<div id="{self.id}-{key}-tx" style="position:absolute;left:0;top:0;white-space:nowrap;font-size:{size}px;'
                f'font-weight:{weight};color:{color};letter-spacing:{MONO_ADVANCE - 0.6:.2f}em;line-height:{lh}px">{html.escape(label)}</div>')
        self.add(key, x, y, round(n * size * MONO_ADVANCE) + 8, lh, body)
        tx = f"#{self.id}-{key}-tx"
        self.set(tx, clipPath="inset(0% 100% 0% 0%)")
        self.enter(key, t, "fade")
        self.tw(tx, t, n / cps, f"steps({n})", clipPath="inset(0% 0% 0% 0%)")
        if sfx:
            self.sfx(t, sfx, gain)
        return round(t + n / cps, 3)

    def glitch(self, key, t, strength=10, frames=5, frame=0.045, sfx="glitch-2", gain=None):
        """RGB-split jitter (cyan/magenta text shadows + x offsets) on an element's inner layer."""
        target = self.sel(key) + "-in"
        a, b = rgb(ACCENT), rgb(ALERT)

        def shadow(d, o):
            return f"{-d}px 0px 0px rgba({a},{o}), {d}px 0px 0px rgba({b},{o})"
        if "textShadow" not in self.state.get(target, {}):
            self.set(target, textShadow=shadow(0, 0))
        pattern = [(-1, 1, .9), (1, -.7, .8), (-.6, .8, .9), (.8, -.4, .6), (-.3, .5, .4)]
        for k in range(frames):
            dx, sh, o = pattern[k % len(pattern)]
            self.tw(target, t + k * frame, frame, "steps(1)", x=round(dx * strength, 1),
                    textShadow=shadow(round(sh * strength, 1), o))
        self.tw(target, t + frames * frame, frame, "steps(1)", x=0, textShadow=shadow(0, 0))
        if sfx:
            self.sfx(t, sfx, gain)

    def levels(self, key, x, y, w, h, n, t, until, color=PRIMARY, gap=0.35):
        """A live audio meter: n bars bouncing (seek-safe yoyo) from t until `until`."""
        bw = w / n
        bars = "".join(f'<i id="{self.id}-{key}-b{i}" style="position:absolute;left:{i * bw + bw * gap / 2:.1f}px;top:0;'
                       f'width:{bw * (1 - gap):.1f}px;height:100%;background:{color};transform-origin:50% 50%"></i>' for i in range(n))
        self.add(key, x, y, w, h, bars)
        self.enter(key, t, "fade")
        for i in range(n):
            sel = f"#{self.id}-{key}-b{i}"
            self.set(sel, scaleY=round(0.12 + ((i * 37) % 10) / 60, 3))
            period = 0.16 + ((i * 53) % 7) * 0.025
            start = t + ((i * 29) % 5) * 0.03
            repeats = int((until - start) / period) - 1
            repeats -= 0 if repeats % 2 else 1
            if repeats >= 1:
                self.tw(sel, start, period, "sine.inOut", scaleY=round(min(1, 0.45 + ((i * 71) % 11) / 20), 3),
                        repeat=repeats, yoyo=True)
        return key

    def hook_title(self, title, subtitle=None, t=0.2, x=110, y=220, max_size=104, width=860,
                   compress_at=None, header=(110, 165), header_scale=0.4):
        """Opening title: the title decodes in (split into two balanced lines, the second in the accent
        colour), glitches on lock, gets a blinking cursor; the subtitle types in underneath.
        compress_at: shrink the title into a header at `header` and drop the subtitle.
        Returns {"locked", "subtitle_end", "header_bottom"}."""
        words = title.split()
        lines = [title]
        if len(words) > 1:
            splits = [(" ".join(words[:i]), " ".join(words[i:])) for i in range(1, len(words))]
            lines = list(min(splits, key=lambda p: (max(len(p[0]), len(p[1])), -len(p[1]))))
        size = round(min(max_size, width / ((max(len(line) for line in lines) + 1) * MONO_ADVANCE)))
        lh = round(size * 1.1) + 4
        at, locked = t, t
        for n, line in enumerate(lines):
            last = n == len(lines) - 1
            lock = at + (len(line.replace(" ", "")) - 1) * 0.033 + 0.34
            locked = self.decode(f"title{n}", line, x, y + n * lh, size, at, stagger=0.033,
                                 color=PRIMARY if (last and len(lines) > 1) else INK,
                                 cursor_at=lock if last else None, sfx="typing" if n == 0 else None, gain=0.5)
            at += 0.28
        for n in range(len(lines)):
            self.glitch(f"title{n}", locked + 0.02, sfx="glitch-2" if n == 0 else None)
        self.sfx(locked + 0.02, "impact-bass-1", 0.08)
        sub_end = None
        if subtitle:
            sub_size = round(min(40, width / (len(subtitle) * MONO_ADVANCE)))
            sub_end = self.typewrite("subtitle", subtitle, x, y + len(lines) * lh + 26, sub_size, locked + 0.14,
                                     cps=70, color=MUTED)
        header_bottom = None
        if compress_at is not None:
            if subtitle:
                self.exit("subtitle", compress_at - 0.1, "fade")
            for n in range(len(lines)):
                self.move(f"title{n}", compress_at, 0.55, "power3.inOut", x=header[0] - x,
                          y=round(header[1] + n * lh * header_scale - (y + n * lh), 1), scale=header_scale)
            header_bottom = round(header[1] + len(lines) * lh * header_scale)
        return {"locked": locked, "subtitle_end": sub_end, "header_bottom": header_bottom}

    # --- ASCII art (added 2026-10-12, IANuclear) ------------------------------
    ASCII_ADVANCE = 0.6   # JetBrains Mono advance at letter-spacing 0 (ASCII art must not be tracked)

    def _ascii_rows(self, art):
        """A string is dedented and trimmed of blank edge lines; a list of rows is used as is, so layers
        (e.g. a flickering fire layer over a drawing) keep the drawing's columns and rows."""
        rows = list(art) if isinstance(art, (list, tuple)) else textwrap.dedent(art).strip("\n").split("\n")
        width = max(len(r) for r in rows)
        return [r.ljust(width) for r in rows], width

    def _ascii_html(self, row, color, colors):
        """One row as HTML: runs of characters coloured by `colors` {char: colour} (others: `color`)."""
        out, run, run_color = [], "", None
        for ch in row:
            c = (colors or {}).get(ch, color)
            if c != run_color and run:
                out.append(f'<span data-layout-allow-overlap style="color:{run_color}">{html.escape(run)}</span>')
                run = ""
            run, run_color = run + ch, c
        if run:
            out.append(f'<span data-layout-allow-overlap style="color:{run_color}">{html.escape(run)}</span>')
        return "".join(out)

    def ascii(self, key, art, x, y, size, t, color=PRIMARY, colors=None, reveal="rows", duration=0.6,
              line=1.0, weight=700, glyphs="#%&*+=?/<>01$@", sfx=None, gain=None, origin="50% 50%", upward=False):
        """Multi-line ASCII art in monospace (no tracking, `white-space:pre`), hidden until `t`.
        reveal: "rows" (rows appear top to bottom over `duration`), "decode" (every row first shows
        glyph noise in the art's shape, then resolves, top to bottom), "scan" (stepped top-down wipe),
        "wipe" (stepped left-to-right wipe, one step per column: charts, bars), "fade".
        upward=True reverses "rows"/"decode" (bottom row first: a cloud rising, a tower building). colors: {char: colour} to paint parts (e.g. {"#": WARM}). line: line-height in em.
        Returns {"end": time the art is complete, "w": px width, "h": px height}."""
        rows, cols = self._ascii_rows(art)
        lh = round(size * line, 2)
        w, h = round(cols * size * self.ASCII_ADVANCE) + 2, round(lh * len(rows))
        seed = sum(ord(c) * (i + 1) for i, c in enumerate(self.id + key)) % 2147483647 or 7
        body = []
        for i, row in enumerate(rows):
            body.append(f'<div id="{self.id}-{key}-r{i}" data-layout-allow-overlap style="position:absolute;left:0;top:{i * lh}px">'
                        f'{self._ascii_html(row, color, colors)}</div>')
            if reveal == "decode":
                noise = []
                for ch in row:
                    seed = (seed * 1103515245 + 12345) % 2147483648
                    noise.append(ch if ch == " " else glyphs[seed % len(glyphs)])
                body.append(f'<div id="{self.id}-{key}-n{i}" data-layout-allow-overlap style="position:absolute;left:0;top:{i * lh}px;color:{ACCENT}">'
                            f'{html.escape("".join(noise))}</div>')
        inner = (f'<div style="position:absolute;inset:0;font-size:{size}px;line-height:{lh}px;font-weight:{weight};'
                 f'letter-spacing:0;white-space:pre;font-family:\'{FONT}\',monospace">{"".join(body)}</div>')
        self.add(key, x, y, w, h, inner, origin=origin)
        n = len(rows)
        step = duration / max(n, 1)
        end = t + duration
        if reveal in ("rows", "decode"):
            for i in range(n):
                at = round(t + ((n - 1 - i) if upward else i) * step, 3)
                row = f"#{self.id}-{key}-r{i}"
                self.set(row, opacity=0)
                if reveal == "rows":
                    self.tw(row, at, 0.02, "none", opacity=1)
                    continue
                hold = 0.12
                noise = f"#{self.id}-{key}-n{i}"
                self.set(noise, opacity=0)
                self.tw(noise, at, 0.02, "none", opacity=1)
                self.tw(noise, at + hold, 0.02, "none", opacity=0)
                self.tw(row, at + hold, 0.02, "none", opacity=1)
            end = t + (n - 1) * step + (0.14 if reveal == "decode" else 0.02)
            self.enter(key, t, "fade")
        elif reveal == "scan":
            wrap = f"#{self.id}-{key}-in"
            self.set(wrap, clipPath="inset(0% 0% 100% 0%)")
            self.enter(key, t, "fade")
            self.tw(wrap, t, duration, f"steps({n})", clipPath="inset(0% 0% 0% 0%)")
        elif reveal == "wipe":
            wrap = f"#{self.id}-{key}-in"
            self.set(wrap, clipPath="inset(0% 100% 0% 0%)")
            self.enter(key, t, "fade")
            self.tw(wrap, t, duration, f"steps({cols})", clipPath="inset(0% 0% 0% 0%)")
        else:
            self.enter(key, t, "fade")
            end = t + 0.3
        if sfx:
            self.sfx(t, sfx, gain)
        return {"end": round(end, 3), "w": w, "h": h}

    def ascii_anim(self, key, frames, x, y, size, t, until, fps=8, color=PRIMARY, colors=None, line=1.0,
                   weight=700, enter="fade"):
        """Frame-flip ASCII animation (a fire, a spinner, a blinking light): `frames` are strings with
        the same row count, cycled at `fps` from t until `until` (one stepped tween, seek-safe).
        Returns {"w", "h"}."""
        parsed = [self._ascii_rows(f) for f in frames]
        n_rows = len(parsed[0][0])
        if any(len(r) != n_rows for r, _ in parsed):
            raise ValueError(f"{self.slug}: ascii_anim frames need the same row count")
        cols = max(c for _, c in parsed)
        lh = round(size * line, 2)
        fh = lh * n_rows
        w, h = round(cols * size * self.ASCII_ADVANCE) + 2, round(fh)
        cells = parsed + [parsed[0]]  # the strip ends on a copy of frame 0 so every cycle wraps cleanly
        body = "".join(f'<div style="position:absolute;left:0;top:{k * fh}px">'
                       + "".join(f'<div data-layout-allow-overlap style="height:{lh}px">{self._ascii_html(r.ljust(cols), color, colors)}</div>' for r in rows)
                       + "</div>" for k, (rows, _) in enumerate(cells))
        strip = f"{self.id}-{key}-strip"
        inner = (f'<div style="position:absolute;inset:0;overflow:hidden;font-size:{size}px;line-height:{lh}px;'
                 f'font-weight:{weight};letter-spacing:0;white-space:pre;font-family:\'{FONT}\',monospace">'
                 f'<div id="{strip}" style="position:absolute;left:0;top:0;width:100%">{body}</div></div>')
        self.add(key, x, y, w, h, inner)
        self.enter(key, t, enter)
        nf = len(frames)
        period = nf / fps
        cycles = int((until - t) / period)
        if cycles >= 1:
            self.tw("#" + strip, t, period, f"steps({nf})", y=-round(nf * fh, 2), repeat=cycles - 1)
        return {"w": w, "h": h}

    def banner(self, key, label, t, y=330, h=150, size=86, w=None, others=None, sfx="sparkle"):
        width = w or min(900, int(len(label) * size * 0.6) + 90)
        x = (1080 - width) // 2
        for other in others or ():
            self.exit(other, t - 0.25, "fade")
        self.tile(key, label, x, y, width, h, size)
        self.enter(key, t, "tilt", sfx=sfx, rest={"rotation": -3})
        if not TERMINAL:  # the hard offset shadow carries the terminal banner
                self.line(key + "-line", [(x + 30, y + h + 22), (x + width - 30, y + h + 18)], t + 0.42, color=ACCENT, width=5, head=False)
        return key

    # --- output -------------------------------------------------------------
    def finish(self, enter_bg: bool, exit_bg: bool):
        dur = round(self.end - self.start, 3)
        # Content leaves just before the scene ends, newest first.
        leave = self.end - 0.36
        for i, key in enumerate(reversed(list(self.live))):
            target = self.sel(key)
            busy = max((b for (sel, _), spans in self.busy.items() if sel == target for _, b in spans), default=0)
            at = max(leave + min(i, 6) * 0.012, self.start + busy + 0.01)
            self.exit(key, round(at, 3), "up")
        bg, light = self.sel("bg"), self.sel("bg") + "-light"
        bg_html = (f'<div id="{self.id}-bg" class="v-el v-bg" style="left:0;top:0;width:1080px;height:735px;transform-origin:50% 0%">'
                   f'<div id="{self.id}-bg-light" class="v-light"></div></div>')
        bg_js = []
        if enter_bg and self.panel != "instant":
            bg_js.append(f'tl.fromTo("{bg}",{{y:-205,scaleY:.66,opacity:0}},{{y:0,scaleY:1,opacity:1,duration:.48,ease:"power4.out",immediateRender:false}},0);')
            bg_js.insert(0, f'tl.set("{bg}",{{y:-205,scaleY:.66,opacity:0}},0);')
        if exit_bg:
            bg_js.append(f'tl.fromTo("{bg}",{{y:0,opacity:1}},{{y:-110,opacity:0,duration:.42,ease:"power3.in",immediateRender:false}},{dur - 0.44:.3f});')
        bg_js.append(f'tl.fromTo("{light}",{{x:-170,opacity:0}},{{x:100,opacity:1,duration:{dur / 2:.3f},ease:"sine.inOut",immediateRender:false}},0);')
        bg_js.append(f'tl.fromTo("{light}",{{x:100,opacity:1}},{{x:260,opacity:0,duration:{dur / 2:.3f},ease:"sine.inOut",immediateRender:false}},{dur / 2:.3f});')
        decor_html = []
        for n, (dx, dy, kind) in enumerate(self.decor or ()):
            size = {"pearl": (40, 40), "capsule": (100, 32), "cube": (42, 42)}[kind]
            did = f"{self.id}-decor{n}"
            decor_html.append(f'<div id="{did}" class="v-el" style="left:{dx}px;top:{dy}px;width:{size[0]}px;height:{size[1]}px">'
                              f'<div id="{did}-in" class="v-in v-{kind}"></div></div>')
            at = 0.18 + n * 0.14
            drift = (14 if n % 2 else -16, -14 if n % 2 else 12, 18 if n % 2 else -14)
            bg_js.append(f'tl.fromTo("#{did}",{{y:30,scale:.6,opacity:0}},{{y:0,scale:1,opacity:1,duration:.65,ease:"power3.out",immediateRender:false}},{at:.3f});')
            bg_js.insert(0, f'tl.set("#{did}",{{y:30,scale:.6,opacity:0}},0);')
            bg_js.append(f'tl.fromTo("#{did}-in",{{x:0,y:0,rotation:0}},{{x:{drift[0]},y:{drift[1]},rotation:{drift[2]},duration:{max(dur - 0.9, 0.5):.3f},ease:"sine.inOut",immediateRender:false}},{at:.3f});')
            bg_js.append(f'tl.fromTo("#{did}",{{y:0,scale:1,opacity:1}},{{y:-45,scale:.85,opacity:0,duration:.3,ease:"power2.in",immediateRender:false}},{dur - 0.4:.3f});')
        if self.panel == "none":
            bg_html = ""
            bg_js = [line for line in bg_js if f'"{bg}"' not in line and f'"{light}"' not in line]
        doc = f"""<!doctype html>
<html lang="es">
<head><meta charset="utf-8"></head>
<body>
<template>
<style>
#{self.id}-root{{position:absolute;inset:0;width:100%;height:100%;overflow:hidden;pointer-events:none}}
{CSS}
</style>
<div id="{self.id}-root" data-composition-id="{self.id}" data-width="1080" data-height="1920" data-duration="{dur:.3f}">
<div id="{self.id}-stage" class="v-stage">
{bg_html}
{''.join(decor_html)}
{chr(10).join(self.parts)}
</div>
</div>
<script>
const tl = gsap.timeline({{paused:true}});
{chr(10).join(bg_js)}
{chr(10).join(self.js)}
window.__timelines["{self.id}"] = tl;
</script>
</template>
</body>
</html>
"""
        (OUT / f"{self.slug}.html").write_text(doc)
        return {"id": self.id, "src": f"src/visuals/{self.slug}.html", "start": self.start, "duration": dur,
                "track": self.track, "layer": self.layer}




# ============================================================================
# Icons (100×100 view boxes unless noted). `p` prefixes ids of animated parts.
# ============================================================================
def svg(body, vb="0 0 100 100"):
    return f'<svg viewBox="{vb}" aria-hidden="true">{body}</svg>'


def person(fill=SOFT, cx=50, cy=0, s=1.0):
    r = 16 * s
    return (f'<circle cx="{cx}" cy="{cy + 34 * s}" r="{r}" fill="{fill}" stroke="{INK}" stroke-width="3"/>'
            f'<path d="M{cx - 28 * s} {cy + 88 * s}Q{cx - 28 * s} {cy + 58 * s} {cx} {cy + 58 * s}Q{cx + 28 * s} {cy + 58 * s} {cx + 28 * s} {cy + 88 * s}Z" '
            f'fill="{fill}" stroke="{INK}" stroke-width="3"/>')


def i_user(fill=SOFT):
    return svg(person(fill))


def i_phone():
    return svg(f'<rect x="6" y="2" width="88" height="166" rx="16" fill="{DEVICE[0]}" stroke="{INK}" stroke-width="{DEVICE[1]}"/>'
               f'<rect x="13" y="16" width="74" height="138" rx="8" fill="{PAPER}"/>'
               f'<rect x="38" y="7" width="24" height="4" rx="2" fill="#3b4570"/>', "0 0 100 170")


def i_mic(fill=SOFT):
    return svg(f'<rect x="36" y="8" width="28" height="48" rx="14" fill="{fill}" stroke="{INK}" stroke-width="3.5"/>'
               f'<path d="M24 44Q24 70 50 70Q76 70 76 44" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
               f'<path d="M50 70V86M34 88H66" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')


def i_waves(p, color=PRIMARY):
    arcs = []
    for i, r in enumerate((62, 92, 122)):
        dx, dy = r * 0.55, r * 0.8
        arcs.append(f'<g id="{p}-w{i}" opacity=".9">'
                    f'<path d="M{150 - dx} {100 - dy}A{r} {r} 0 0 0 {150 - dx} {100 + dy}" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round"/>'
                    f'<path d="M{150 + dx} {100 - dy}A{r} {r} 0 0 1 {150 + dx} {100 + dy}" fill="none" stroke="{color}" stroke-width="7" stroke-linecap="round"/></g>')
    return svg("".join(arcs), "0 0 300 200")


def i_cup():
    return svg(f'<path d="M22 40H72V66Q72 84 52 84H42Q22 84 22 66Z" fill="{PAPER}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M72 48Q86 48 86 58Q86 68 72 68" fill="none" stroke="{INK}" stroke-width="4"/>'
               f'<path d="M38 30Q32 22 38 14M54 30Q48 22 54 14" fill="none" stroke="{MUTED}" stroke-width="3.5" stroke-linecap="round"/>'
               f'<rect x="26" y="44" width="42" height="8" rx="4" fill="#8a5a3c" opacity=".75"/>')


def i_espresso():
    return svg(f'<rect x="14" y="10" width="72" height="22" rx="7" fill="{INK}"/>'
               f'<rect x="18" y="32" width="64" height="54" rx="6" fill="{SOFT}" stroke="{INK}" stroke-width="3.5"/>'
               f'<rect x="36" y="34" width="28" height="10" rx="3" fill="{INK}"/>'
               f'<path d="M40 60H60V72Q60 78 54 78H46Q40 78 40 72Z" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>'
               f'<rect x="10" y="86" width="80" height="6" rx="3" fill="{INK}"/>'
               f'<circle cx="74" cy="21" r="4" fill="{HOT}"/>')


def i_eye(p=None):
    """p: id prefix; the iris/pupil group becomes `{p}-pupil` (move it to make the eye look around)."""
    pupil = (f'<circle cx="50" cy="50" r="17" fill="{PRIMARY}"/><circle cx="50" cy="50" r="7" fill="{ON_FILL}"/>'
             f'<circle cx="56" cy="44" r="4" fill="{MARK}"/>')
    if p:
        pupil = f'<g id="{p}-pupil">{pupil}</g>'
    return svg(f'<path d="M8 50Q50 12 92 50Q50 88 8 50Z" fill="{PAPER}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>' + pupil)


def i_skip():
    return svg(f'<rect x="8" y="18" width="84" height="64" rx="16" fill="{SOFT}" stroke="{INK}" stroke-width="3.5"/>'
               f'<path d="M34 36L54 50L34 64Z" fill="{INK}"/><rect x="58" y="36" width="7" height="28" rx="2" fill="{INK}"/>')


def i_heart():
    return svg(f'<path d="M50 84L18 52Q6 38 16 24Q30 10 50 30Q70 10 84 24Q94 38 82 52Z" fill="{WARM}" stroke="{ALERT}" stroke-width="4" stroke-linejoin="round"/>')


def i_follow():
    return svg(person(ACCENT, 40, 4, 0.9) + f'<circle cx="76" cy="30" r="15" fill="{PRIMARY}"/><path d="M76 22V38M68 30H84" stroke="{MARK}" stroke-width="4" stroke-linecap="round"/>')


def i_search():
    return svg(f'<circle cx="42" cy="42" r="24" fill="{PAPER}" stroke="{INK}" stroke-width="6"/><path d="M60 60L84 84" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>')


def i_cursor():
    return svg(f'<path d="M30 14L30 78L46 62L58 88L70 82L58 57L80 56Z" fill="{PAPER}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')


def i_cart():
    return svg(f'<path d="M8 18H22L32 64H78L88 32H28" fill="none" stroke="{INK}" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/>'
               f'<path d="M30 32H86L78 60H34Z" fill="{ACCENT}" opacity=".55"/><circle cx="38" cy="80" r="7" fill="{INK}"/><circle cx="72" cy="80" r="7" fill="{INK}"/>')


def i_play():
    return svg(f'<circle cx="50" cy="50" r="40" fill="{ACCENT}" stroke="{INK}" stroke-width="3.5"/><path d="M42 33L68 50L42 67Z" fill="{ON_FILL}"/>')


def i_server():
    rows = "".join(f'<rect x="14" y="{12 + i * 27}" width="72" height="22" rx="6" fill="{SOFT}" stroke="{INK}" stroke-width="3"/>'
                   f'<circle cx="28" cy="{23 + i * 27}" r="4" fill="{ACCENT}"/><rect x="40" y="{20 + i * 27}" width="36" height="6" rx="3" fill="{INK}" opacity=".5"/>' for i in range(3))
    return svg(rows)


def i_audio(p):
    heights = (18, 40, 62, 34, 70, 46, 24, 52, 30)
    bars = "".join(f'<rect id="{p}-b{i}" x="{8 + i * 9.5}" y="{50 - h / 2}" width="6" height="{h}" rx="3" fill="{PRIMARY}"/>' for i, h in enumerate(heights))
    return svg(bars)


def i_gear(p):
    teeth = "".join(f'<rect x="44" y="6" width="12" height="16" rx="3" fill="{PRIMARY}" transform="rotate({a} 50 50)"/>' for a in range(0, 360, 45))
    return svg(f'<g id="{p}-gear">{teeth}<circle cx="50" cy="50" r="30" fill="{PRIMARY}"/><circle cx="50" cy="50" r="13" fill="{PAPER}"/></g>')


def i_doc():
    lines = "".join(f'<rect x="28" y="{40 + i * 12}" width="{40 - (i % 2) * 12}" height="6" rx="3" fill="{MUTED}"/>' for i in range(3))
    return svg(f'<path d="M22 10H60L78 28V90H22Z" fill="{PAPER}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
               f'<path d="M60 10V28H78" fill="{SOFT}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>{lines}')


def i_globe():
    return svg(f'<circle cx="50" cy="50" r="38" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>'
               f'<path d="M12 50H88M50 12Q30 50 50 88M50 12Q70 50 50 88" fill="none" stroke="{PRIMARY}" stroke-width="3.5"/>')


def i_target():
    return svg(f'<circle cx="50" cy="50" r="38" fill="{PAPER}" stroke="{INK}" stroke-width="4"/><circle cx="50" cy="50" r="24" fill="{WARM}" stroke="{INK}" stroke-width="3"/>'
               f'<circle cx="50" cy="50" r="10" fill="{HOT}"/>')


def i_megaphone():
    return svg(f'<path d="M14 40H32L72 18V82L32 60H14Z" fill="{WARM}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M30 60L36 84H48L44 62" fill="{PAPER}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
               f'<path d="M82 38Q90 50 82 62" fill="none" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')


def i_check(fill=ACCENT):
    return svg(f'<circle cx="50" cy="50" r="40" fill="{fill}" stroke="{INK}" stroke-width="3"/><path d="M30 51L44 64L71 35" fill="none" stroke="{ON_FILL}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/>')


def i_question(fill=WARM):
    return svg(f'<circle cx="50" cy="50" r="40" fill="{fill}" stroke="{INK}" stroke-width="3"/><text x="50" y="67" text-anchor="middle" font-family="{FONT},sans-serif" font-weight="900" font-size="50" fill="{ON_FILL}">?</text>')


def i_clock():
    return svg(f'<circle cx="50" cy="50" r="38" fill="{PAPER}" stroke="{INK}" stroke-width="4"/><path d="M50 50V28M50 50L66 58" stroke="{INK}" stroke-width="5" stroke-linecap="round"/><circle cx="50" cy="50" r="5" fill="{PRIMARY}"/>')


def i_repeat():
    return svg(f'<path d="M24 44Q24 26 44 26H72" fill="none" stroke="{PRIMARY}" stroke-width="7" stroke-linecap="round"/><path d="M66 16L78 26L66 36Z" fill="{PRIMARY}"/>'
               f'<path d="M76 56Q76 74 56 74H28" fill="none" stroke="{PRIMARY}" stroke-width="7" stroke-linecap="round"/><path d="M34 64L22 74L34 84Z" fill="{PRIMARY}"/>')


def i_box():
    return svg(f'<path d="M50 10L86 28V72L50 90L14 72V28Z" fill="{WARM}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M14 28L50 46L86 28M50 46V90" fill="none" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')


def i_book():
    return svg(f'<path d="M50 24Q34 14 12 18V80Q34 76 50 86Q66 76 88 80V18Q66 14 50 24Z" fill="{PAPER}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M50 24V86" stroke="{INK}" stroke-width="3.5"/><path d="M22 36H40M22 48H40M60 36H78M60 48H78" stroke="{MUTED}" stroke-width="3.5" stroke-linecap="round"/>')


def i_pot():
    return svg(f'<path d="M18 40H82V70Q82 84 68 84H32Q18 84 18 70Z" fill="{SOFT}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<rect x="12" y="32" width="76" height="10" rx="5" fill="{INK}"/><path d="M8 52H18M82 52H92" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>'
               f'<path d="M40 24Q36 16 40 8M58 24Q54 16 58 8" fill="none" stroke="{MUTED}" stroke-width="3.5" stroke-linecap="round"/>')


def i_headphones():
    return svg(f'<path d="M18 62V50Q18 18 50 18Q82 18 82 50V62" fill="none" stroke="{INK}" stroke-width="6"/>'
               f'<rect x="12" y="56" width="20" height="30" rx="8" fill="{SOFT}" stroke="{INK}" stroke-width="3.5"/><rect x="68" y="56" width="20" height="30" rx="8" fill="{SOFT}" stroke="{INK}" stroke-width="3.5"/>')


def i_shoe():
    return svg(f'<path d="M10 72V44Q22 42 30 34L46 52Q64 56 82 60Q92 64 90 76H10Z" fill="{ACCENT}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M10 76H90" stroke="{INK}" stroke-width="5" stroke-linecap="round"/><path d="M34 46L28 54M40 50L34 58" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')


def i_form():
    rows = "".join(f'<rect x="20" y="{30 + i * 18}" width="22" height="5" rx="2.5" fill="{MUTED}"/><rect x="46" y="{26 + i * 18}" width="36" height="12" rx="4" fill="{SURFACE}" stroke="{MUTED}" stroke-width="2"/>' for i in range(3))
    return svg(f'<rect x="10" y="8" width="80" height="86" rx="10" fill="{PAPER}" stroke="{INK}" stroke-width="3.5"/><rect x="20" y="14" width="40" height="6" rx="3" fill="{INK}"/>{rows}')


def i_thought():
    return svg(f'<path d="M30 70Q8 70 10 52Q8 34 28 34Q32 14 54 18Q72 8 84 26Q100 34 92 54Q96 72 74 72Z" fill="{SURFACE}" stroke="{INK}" stroke-width="3.5"/>'
               f'<circle cx="26" cy="84" r="6" fill="{SURFACE}" stroke="{INK}" stroke-width="3"/><circle cx="14" cy="94" r="3.5" fill="{SURFACE}" stroke="{INK}" stroke-width="2.5"/>', "0 0 100 100")


def i_browser():
    dots = "".join(f'<circle cx="{16 + i * 10}" cy="15" r="3.5" fill="{c}"/>' for i, c in enumerate((HOT, WARM, ACCENT)))
    return svg(f'<rect x="4" y="4" width="152" height="112" rx="12" fill="{SURFACE}" stroke="{INK}" stroke-width="3.5"/>'
               f'<path d="M4 26H156" stroke="{INK}" stroke-width="3"/>{dots}<rect x="48" y="10" width="96" height="10" rx="5" fill="{PAPER}" stroke="{MUTED}" stroke-width="1.5"/>', "0 0 160 120")


def i_fingerprint():
    arcs = "".join(f'<path d="M{50 - r} {58}Q{50 - r} {58 - r * 1.3} 50 {58 - r * 1.3}Q{50 + r} {58 - r * 1.3} {50 + r} {58}V{58 + r * 0.6}" '
                   f'fill="none" stroke="{PRIMARY}" stroke-width="4" stroke-linecap="round"/>' for r in (8, 16, 24, 32))
    return svg(arcs)


def i_comment():
    return svg(f'<path d="M12 20Q12 10 24 10H76Q88 10 88 22V58Q88 70 76 70H40L22 86V70Q12 70 12 58Z" fill="{SOFT}" stroke="{INK}" stroke-width="3.5"/>'
               f'<rect x="28" y="30" width="44" height="6" rx="3" fill="{INK}"/><rect x="28" y="44" width="30" height="6" rx="3" fill="{INK}" opacity=".6"/>')


def i_iceberg():
    return svg(f'<path d="M0 74H300" stroke="{PRIMARY}" stroke-width="4" stroke-dasharray="10 8"/>'
               f'<path d="M120 74L140 40L152 46L166 22L182 74Z" fill="{SURFACE}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M110 80L190 80L236 128L210 176L150 196L88 170L70 124Z" fill="{SOFT}" opacity=".55" stroke="{INK}" stroke-width="3" stroke-dasharray="8 7" stroke-linejoin="round"/>',
               "0 0 300 200")


def i_walk(fill=SOFT):
    return svg(f'<circle cx="54" cy="16" r="10" fill="{fill}" stroke="{INK}" stroke-width="3.5"/>'
               f'<path d="M50 30L42 58M42 58L54 72L52 92M42 58L30 74L20 90M48 36L30 46L24 60M48 36L62 50L76 54" '
               f'fill="none" stroke="{INK}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>')


def i_bus():
    return svg(f'<rect x="12" y="12" width="76" height="70" fill="{WARM}" stroke="{INK}" stroke-width="4"/>'
               f'<rect x="20" y="22" width="60" height="26" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>'
               f'<path d="M50 22V48" stroke="{INK}" stroke-width="3"/>'
               f'<circle cx="26" cy="64" r="5" fill="{INK}"/><circle cx="74" cy="64" r="5" fill="{INK}"/>'
               f'<rect x="20" y="82" width="12" height="10" fill="{INK}"/><rect x="68" y="82" width="12" height="10" fill="{INK}"/>')


def i_car():
    return svg(f'<path d="M10 70V54L22 50L32 30H68L80 50L90 54V70Z" fill="{ACCENT}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M36 36H48V50H28ZM54 36H64L72 50H54Z" fill="{PAPER}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>'
               f'<circle cx="28" cy="72" r="10" fill="{INK}"/><circle cx="72" cy="72" r="10" fill="{INK}"/>'
               f'<circle cx="28" cy="72" r="4" fill="{MUTED}"/><circle cx="72" cy="72" r="4" fill="{MUTED}"/>')


def i_pin(fill=HOT):
    return svg(f'<path d="M50 94Q18 56 18 38Q18 8 50 8Q82 8 82 38Q82 56 50 94Z" fill="{fill}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<circle cx="50" cy="38" r="12" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>')


def i_card():
    return svg(f'<rect x="8" y="22" width="84" height="56" fill="{SOFT}" stroke="{INK}" stroke-width="4"/>'
               f'<rect x="8" y="34" width="84" height="10" fill="{INK}"/><rect x="18" y="56" width="22" height="12" fill="{WARM}"/>'
               f'<rect x="50" y="60" width="32" height="5" fill="{MUTED}"/>')


def i_sort():
    bars = "".join(f'<rect x="{12 + i * 20}" y="{84 - h}" width="14" height="{h}" fill="{PRIMARY if i == 3 else SOFT}" stroke="{INK}" stroke-width="3"/>'
                   for i, h in enumerate((22, 38, 54, 72)))
    return svg(bars + f'<path d="M14 92H90" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>')


def i_tag():
    return svg(f'<path d="M50 10H88V48L48 88L12 52Z" fill="{WARM}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<circle cx="72" cy="26" r="6" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>'
               f'<text x="47" y="62" text-anchor="middle" font-family="{FONT},sans-serif" font-weight="900" font-size="26" fill="{ON_FILL}" transform="rotate(-45 47 54)">%</text>')


def i_plug():
    """Charger plug, side view, flat blades pointing right (Adapter)."""
    return svg(f'<path d="M0 50H16" stroke="{INK}" stroke-width="6" stroke-linecap="round"/>'
               f'<rect x="14" y="26" width="46" height="48" fill="{SOFT}" stroke="{INK}" stroke-width="4"/>'
               f'<rect x="60" y="33" width="34" height="8" fill="{INK}"/><rect x="60" y="59" width="34" height="8" fill="{INK}"/>')


def i_socket():
    """Wall socket with two round holes (Adapter): a different shape from i_plug's flat blades."""
    return svg(f'<rect x="12" y="8" width="76" height="84" fill="{SOFT}" stroke="{INK}" stroke-width="4"/>'
               f'<circle cx="50" cy="50" r="28" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>'
               f'<circle cx="38" cy="50" r="7" fill="{INK}"/><circle cx="62" cy="50" r="7" fill="{INK}"/>')


def i_adapter(fill=PRIMARY):
    """Travel adapter, side view: flat slots on the left (takes i_plug), round pins on the right (fits i_socket)."""
    return svg(f'<rect x="20" y="22" width="52" height="56" fill="{fill}" stroke="{INK}" stroke-width="4"/>'
               f'<rect x="20" y="33" width="16" height="8" fill="{PAPER}"/><rect x="20" y="59" width="16" height="8" fill="{PAPER}"/>'
               f'<rect x="70" y="30" width="26" height="13" rx="6.5" fill="{INK}"/><rect x="70" y="57" width="26" height="13" rx="6.5" fill="{INK}"/>')


def i_code():
    """A code window: bar plus `</>` (IANuclear, 2026-10-12)."""
    return svg(f'<rect x="10" y="16" width="80" height="68" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>'
               f'<path d="M10 30H90" stroke="{INK}" stroke-width="3"/><circle cx="19" cy="23" r="2.5" fill="{PRIMARY}"/>'
               f'<path d="M38 46L28 57L38 68M62 46L72 57L62 68M54 42L46 72" fill="none" stroke="{PRIMARY}" stroke-width="5" '
               f'stroke-linecap="round" stroke-linejoin="round"/>')


def i_building(fill=SOFT):
    """An office building (companies)."""
    win = "".join(f'<rect x="{x}" y="{y}" width="10" height="10" fill="{ACCENT}"/>' for y in (26, 42, 58) for x in (32, 45, 58))
    return svg(f'<rect x="22" y="12" width="56" height="76" fill="{fill}" stroke="{INK}" stroke-width="4"/>{win}'
               f'<rect x="43" y="72" width="14" height="16" fill="{INK}"/><path d="M10 88H90" stroke="{INK}" stroke-width="4"/>')


def i_shield(fill=PRIMARY):
    """A shield with a check (safety, security)."""
    return svg(f'<path d="M50 10L84 22V48Q84 74 50 90Q16 74 16 48V22Z" fill="{fill}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M34 50L46 62L67 38" fill="none" stroke="{ON_FILL}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/>')


def i_health(fill=ALERT):
    """A medical cross (health)."""
    return svg(f'<path d="M38 12H62V38H88V62H62V88H38V62H12V38H38Z" fill="{fill}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')


def i_flask():
    """A lab flask with liquid (laboratories)."""
    return svg(f'<path d="M40 12V40L16 82Q13 88 20 88H80Q87 88 84 82L60 40V12" fill="{PAPER}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M29 60H71L81 80Q83 84 78 84H22Q17 84 19 80Z" fill="{ACCENT}"/>'
               f'<path d="M34 12H66" stroke="{INK}" stroke-width="4" stroke-linecap="round"/>'
               f'<circle cx="44" cy="72" r="3" fill="{ON_FILL}"/><circle cx="56" cy="66" r="2.5" fill="{ON_FILL}"/>')


def i_missile(fill=MUTED):
    """A missile (military weapons): body, nose, fins; no flame."""
    return svg(f'<path d="M50 8Q64 22 62 44V76H38V44Q36 22 50 8Z" fill="{fill}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M38 58L24 76V88L38 80ZM62 58L76 76V88L62 80Z" fill="{ALERT}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
               f'<path d="M44 76V90H56V76" fill="{INK}"/><path d="M40 34H60" stroke="{INK}" stroke-width="3"/>')


def i_robot(p=None, fill=None, eyes=None, mood="neutral", halo=False, horns=False, wings=False, tail=False,
            arms=None, arm_stripes=None, hair=None, collar=None, badge=None, flag=None):
    """The robot pet (an AI character; IANuclear 2026-10-12). Boxy head with a dark visor, antenna,
    chest light, arms, feet. mood: neutral (round eyes), happy (^ ^ eyes and a smile), evil (slanted
    eyes, flat mouth). halo/wings: angel; horns/tail: devil (halo and horns replace the antenna).
    Costume (to dress the pet as a team, e.g. a country): arms (arm fill), arm_stripes (colour of three
    stripes across each arm), hair (colour of a combed-over swoop that replaces the antenna), collar
    (a mandarin collar at the neck), badge (fill of a round chest badge that replaces the chest light;
    lay a logo over it at x 39–61 %, y 66–88 % of the icon box), flag ("us" | "cn": a small flag on a pole
    held in the left hand, trailing behind a runner; part `{p}-flag` to wave it, origin at the pole top).
    p: id prefix; parts `{p}-eyes`, `{p}-ant`, `{p}-core`, `{p}-arm-l`, `{p}-arm-r` (wave an arm with
    rotation; blink the eyes with scaleY)."""
    fill = fill or SOFT
    eyes = eyes or (ALERT if mood == "evil" else PRIMARY)
    pid = (lambda part: f' id="{p}-{part}"') if p else (lambda part: "")
    out = []
    if wings:
        for sx in (1, -1):
            out.append(f'<path transform="translate({100 if sx < 0 else 0} 0) scale({sx} 1)" d="M28 70Q6 58 3 78Q12 76 10 86Q20 82 28 86Z" '
                       f'fill="{PAPER}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>')
    if tail:
        out.append(f'<path d="M70 88Q92 94 90 74" fill="none" stroke="{ALERT}" stroke-width="3.5" stroke-linecap="round"/>'
                   f'<path d="M84 74L96 72L88 62Z" fill="{ALERT}"/>')
    if halo:
        out.append(f'<ellipse cx="50" cy="8" rx="18" ry="5" fill="none" stroke="{WARM}" stroke-width="4"{pid("ant")}/>')
    elif horns:
        out.append(f'<g{pid("ant")}><path d="M26 22L18 4L36 18Z" fill="{ALERT}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
                   f'<path d="M74 22L82 4L64 18Z" fill="{ALERT}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/></g>')
    elif not hair:
        out.append(f'<path d="M50 18V9" stroke="{INK}" stroke-width="3.5"/><circle cx="50" cy="7" r="5" fill="{ACCENT}" stroke="{INK}" stroke-width="2.5"{pid("ant")}/>')
    for side, x in (("l", 14), ("r", 76)):
        stripes = "".join(f'<path d="M{x + 1} {70 + i * 5}H{x + 9}" stroke="{arm_stripes}" stroke-width="2.2"/>' for i in range(3)) if arm_stripes else ""
        out.append(f'<g{pid("arm-" + side)}><rect x="{x}" y="66" width="10" height="20" rx="5" fill="{arms or fill}" stroke="{INK}" stroke-width="3"/>{stripes}</g>')
    out.append(f'<rect x="33" y="90" width="11" height="7" rx="2" fill="{INK}"/><rect x="56" y="90" width="11" height="7" rx="2" fill="{INK}"/>')
    out.append(f'<rect x="27" y="63" width="46" height="29" rx="8" fill="{fill}" stroke="{INK}" stroke-width="3.5"/>'
               + (f'<circle cx="50" cy="77" r="12" fill="{badge}" stroke="{INK}" stroke-width="2.5"{pid("core")}/>' if badge else
                  f'<circle cx="50" cy="77" r="5.5" fill="{PRIMARY}" stroke="{INK}" stroke-width="2"{pid("core")}/>'))
    out.append(f'<rect x="44" y="58" width="12" height="6" fill="{INK}"/>')
    if collar:
        out.append(f'<path d="M36 59H64V67L52 66L50 69L48 66L36 67Z" fill="{collar}" stroke="{INK}" stroke-width="2.2" stroke-linejoin="round"/>')
    out.append(f'<rect x="11" y="31" width="9" height="16" rx="3" fill="{fill}" stroke="{INK}" stroke-width="3"/>'
               f'<rect x="80" y="31" width="9" height="16" rx="3" fill="{fill}" stroke="{INK}" stroke-width="3"/>')
    out.append(f'<rect x="18" y="18" width="64" height="42" rx="12" fill="{fill}" stroke="{INK}" stroke-width="3.5"/>'
               f'<rect x="25" y="25" width="50" height="25" rx="8" fill="{ON_FILL}" stroke="{INK}" stroke-width="2.5"/>')
    if mood == "happy":
        e = (f'<path d="M33 41Q39 31 45 41M55 41Q61 31 67 41" fill="none" stroke="{eyes}" stroke-width="4.5" stroke-linecap="round"/>')
        mouth = f'<path d="M42 53Q50 58 58 53" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
    elif mood == "evil":
        e = f'<path d="M32 33L47 39L33 44Z" fill="{eyes}"/><path d="M68 33L53 39L67 44Z" fill="{eyes}"/>'
        mouth = f'<path d="M41 54L45 56L50 54L55 56L59 54" fill="none" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>'
    else:
        e = f'<rect x="34" y="32" width="10" height="12" rx="4" fill="{eyes}"/><rect x="56" y="32" width="10" height="12" rx="4" fill="{eyes}"/>'
        mouth = f'<path d="M43 54H57" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>'
    out.append(f'<g{pid("eyes")}>{e}</g>{mouth}')
    if hair:
        out.append(f'<path d="M15 33Q11 13 38 10Q66 5 88 17Q79 15 72 18Q85 21 86 31Q76 21 54 21Q31 20 21 34Z" fill="{hair}" '
                   f'stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"{pid("ant")}/>')
    if flag:   # drawn last: the pole runs from the left hand, diagonally up past the head, flag trailing left
        out.append(f'<path d="M19 86L4 6" stroke="{INK}" stroke-width="3.5" stroke-linecap="round"/>'
                   f'<g{pid("flag")}>{_flag_body(flag, -36, 4, 40, 25, 2)}</g>'
                   f'<circle cx="19" cy="82" r="5" fill="{arms or fill}" stroke="{INK}" stroke-width="2.5"/>')
    return svg("".join(out))


def ai_overlay(visor, antenna=None, glow=(), eyes=None):
    """Robot features to lay over another 100×100 icon (an object taken over by the AI): a dark visor
    with two eyes at visor=(x, y, w[, h]), an antenna whose ball sits at antenna=(x, y), and glowing
    dots glow=[(x, y, r)] (headlights, lamps). Use as a second s.art on top of the icon."""
    eyes = eyes or PRIMARY
    x, y, w = visor[:3]
    h = visor[3] if len(visor) > 3 else max(10, round(w * 0.36))
    ew, eh = max(4, round(w * 0.16)), max(4, round(h * 0.5))
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{h / 2.6:.1f}" fill="{ON_FILL}" stroke="{PRIMARY}" stroke-width="2.5"/>',
           f'<rect x="{x + w * 0.22:.1f}" y="{y + (h - eh) / 2:.1f}" width="{ew}" height="{eh}" rx="2" fill="{eyes}"/>',
           f'<rect x="{x + w * 0.78 - ew:.1f}" y="{y + (h - eh) / 2:.1f}" width="{ew}" height="{eh}" rx="2" fill="{eyes}"/>']
    if antenna:
        ax, ay = antenna
        out.append(f'<path d="M{ax} {ay + 4}V{ay + 12}" stroke="{PRIMARY}" stroke-width="3"/><circle cx="{ax}" cy="{ay}" r="4.5" fill="{PRIMARY}" stroke="{INK}" stroke-width="2"/>')
    out += [f'<circle cx="{gx}" cy="{gy}" r="{gr}" fill="{PRIMARY}" stroke="{INK}" stroke-width="2"/>' for gx, gy, gr in glow]
    return svg("".join(out))


def i_rocket(p=None):
    """A rocket pointing up, with the robot pet's eyes in the porthole. p: `{p}-flame` (flicker it)."""
    fid = f' id="{p}-flame"' if p else ""
    return svg(f'<g{fid}><path d="M41 66Q50 99 59 66Z" fill="{WARM}"/><path d="M45 66Q50 86 55 66Z" fill="{HOT}"/></g>'
               f'<path d="M33 46L17 70L33 66Z" fill="{HOT}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
               f'<path d="M67 46L83 70L67 66Z" fill="{HOT}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
               f'<path d="M50 5Q71 24 68 64H32Q29 24 50 5Z" fill="{PAPER}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<rect x="40" y="62" width="20" height="6" fill="{MUTED}" stroke="{INK}" stroke-width="2.5"/>'
               f'<circle cx="50" cy="35" r="11" fill="{ON_FILL}" stroke="{INK}" stroke-width="3"/>'
               f'<rect x="44" y="32" width="4" height="6" rx="1.5" fill="{PRIMARY}"/><rect x="52" y="32" width="4" height="6" rx="1.5" fill="{PRIMARY}"/>')


def i_computer(taken=False):
    """A desktop computer; taken=True: the robot pet's eyes on a dark screen and a lime outline (the AI is in it)."""
    line = PRIMARY if taken else INK
    screen = (f'<rect x="17" y="21" width="66" height="38" fill="{ON_FILL}"/>'
              f'<rect x="34" y="31" width="9" height="13" rx="3" fill="{PRIMARY}"/><rect x="57" y="31" width="9" height="13" rx="3" fill="{PRIMARY}"/>'
              f'<path d="M42 51H58" stroke="{PRIMARY}" stroke-width="3" stroke-linecap="round"/>') if taken else \
             (f'<rect x="17" y="21" width="66" height="38" fill="{SOFT}"/>'
              f'<path d="M24 31H60M24 40H70M24 49H50" stroke="{MUTED}" stroke-width="3.5" stroke-linecap="round"/>')
    return svg(f'<rect x="10" y="14" width="80" height="52" rx="4" fill="{PAPER}" stroke="{line}" stroke-width="4"/>{screen}'
               f'<path d="M42 66L38 82H62L58 66" fill="{PAPER}" stroke="{line}" stroke-width="3.5" stroke-linejoin="round"/>'
               f'<rect x="28" y="82" width="44" height="6" fill="{line}"/>')


def i_mushroom(p=None):
    """A nuclear mushroom cloud in the flat house style (200×200 view box). p: parts `{p}-base`, `{p}-stem`,
    `{p}-collar`, `{p}-cap`, `{p}-glow` for a staged rise (stem scaleY from the bottom, cap rising and growing)."""
    pid = (lambda part: f' id="{p}-{part}"') if p else (lambda part: "")
    def puffs(circles, fill, stroke=True):
        # outlined circles first, then fill-only copies on top, so only the outer silhouette keeps a stroke
        a = "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{fill}" stroke="{INK}" stroke-width="4"/>' for x, y, r in circles) if stroke else ""
        return a + "".join(f'<circle cx="{x}" cy="{y}" r="{r - 2}" fill="{fill}"/>' for x, y, r in circles)
    base = [(44, 176, 18), (70, 168, 22), (100, 164, 24), (130, 168, 22), (156, 176, 18), (100, 182, 20)]
    cap = [(64, 66, 28), (100, 52, 36), (136, 66, 28), (80, 86, 24), (120, 86, 24), (100, 80, 26)]
    hi = [(100, 50, 22), (68, 64, 15), (132, 64, 15)]
    return svg(f'<circle cx="100" cy="68" r="62" fill="{WARM}" opacity=".18"{pid("glow")}/>'
               f'<g{pid("base")}>{puffs(base, MUTED)}</g>'
               f'<path d="M86 166Q80 128 90 98H110Q120 128 114 166Z" fill="{WARM}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"{pid("stem")}/>'
               f'<ellipse cx="100" cy="124" rx="30" ry="9" fill="{HOT}" stroke="{INK}" stroke-width="3.5"{pid("collar")}/>'
               f'<g{pid("cap")}>{puffs(cap, HOT)}{puffs(hi, WARM, stroke=False)}</g>', "0 0 200 200")


def _star(cx, cy, r, fill):
    pts = []
    for i in range(10):
        a = math.radians(-90 + i * 36)
        rr = r if i % 2 == 0 else r * 0.42
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}" fill="{fill}"/>'


def _flag_body(code, x0, y0, w, h, stroke=3):
    """A simplified national flag in its official colours inside (x0, y0, w, h): "us", "cn"."""
    if code == "us":
        sh = h / 13
        body = "".join(f'<rect x="{x0}" y="{y0 + i * sh:.2f}" width="{w}" height="{sh + 0.05:.2f}" fill="{"#b22234" if i % 2 == 0 else "#ffffff"}"/>'
                       for i in range(13))
        cw, ch = w * 0.44, sh * 7
        body += f'<rect x="{x0}" y="{y0}" width="{cw:.2f}" height="{ch:.2f}" fill="#3c3b6e"/>'
        r = max(0.5, h * 0.022)
        body += "".join(f'<circle cx="{x0 + cw * (0.09 + c * 0.17 + (0.085 if row % 2 else 0)):.2f}" cy="{y0 + ch * (0.12 + row * 0.155):.2f}" '
                        f'r="{r:.2f}" fill="#ffffff"/>' for row in range(6) for c in range(5 if row % 2 else 6))
    elif code == "cn":
        u = h / 20   # the flag's 30×20 construction grid
        body = (f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="#de2910"/>' + _star(x0 + 5 * u, y0 + 5 * u, 3 * u, "#ffde00")
                + "".join(_star(x0 + sx * u, y0 + sy * u, u, "#ffde00") for sx, sy in ((10, 2), (12, 4), (12, 7), (10, 9))))
    else:
        raise ValueError(f"flag: unknown code {code!r}")
    return body + f'<rect x="{x0}" y="{y0}" width="{w}" height="{h}" fill="none" stroke="{INK}" stroke-width="{stroke}"/>'


def i_flag(code):
    """Simplified national flags in their official colours (100×100 box, flag 100×58): "us", "cn"."""
    return svg(_flag_body(code, 0, 21, 100, 58))


def logo(src):
    """An official brand mark (project-relative SVG/PNG from `media-use resolve --type logo`), usable wherever an
    i_* icon goes: s.card(icon=), row_card, s.art. Shown as is, never recoloured or redrawn."""
    return f'<img src="{html.escape(src)}" alt="" style="display:block;width:100%;height:100%;object-fit:contain">'


_PCB, _PCB_TRACE, _METAL, _CHIP, _GOLD ="#1f5fbf", "#4f8fea", "#c8ccd2", "#1c2026", "#d9a93a"


def _pid(p, part):
    return f' id="{p}-{part}"' if p else ""


def i_sbc(p=None):
    """A single-board computer from above, modelled on the Orange Pi 5 Plus (200×160 view box): blue PCB,
    metal ports on the top edge, SoC, RAM, M.2 slot, GPIO header, status LED. Board colours are the real
    object's (like i_flag). p: parts `{p}-soc`, `{p}-led`, `{p}-ports`, `{p}-gpio`."""
    holes = "".join(f'<circle cx="{x}" cy="{y}" r="5.5" fill="{_GOLD}" stroke="{INK}" stroke-width="1.5"/>'
                    f'<circle cx="{x}" cy="{y}" r="2.2" fill="{_CHIP}"/>' for x, y in ((20, 50), (166, 50), (20, 140), (166, 140)))
    traces = (f'<path d="M72 92H84M72 104H84M134 80H146M134 96H146M108 118V134M118 118V128H150" fill="none" '
              f'stroke="{_PCB_TRACE}" stroke-width="2" stroke-linecap="round" opacity=".8"/>')
    ports = (f'<g{_pid(p, "ports")}>'
             f'<rect x="26" y="6" width="50" height="38" rx="2" fill="{_METAL}" stroke="{INK}" stroke-width="2.5"/>'
             f'<path d="M39 16V34M51 16V34M63 16V34" stroke="#8d939c" stroke-width="3"/>'
             + "".join(f'<rect x="{x}" y="10" width="14" height="30" rx="2" fill="{_METAL}" stroke="{INK}" stroke-width="2.5"/>'
                       f'<rect x="{x + 4}" y="15" width="6" height="18" fill="{_CHIP}"/>' for x in (86, 104, 122))
             + f'<rect x="146" y="6" width="34" height="38" rx="2" fill="{_METAL}" stroke="{INK}" stroke-width="2.5"/>'
             f'<rect x="152" y="14" width="22" height="8" fill="{_CHIP}"/><rect x="152" y="28" width="22" height="8" fill="{_CHIP}"/></g>')
    chips = (f'<rect x="34" y="62" width="40" height="12" rx="1.5" fill="{_CHIP}"/>'
             f'<rect x="44" y="86" width="26" height="22" rx="2" fill="{_CHIP}"/><rect x="44" y="114" width="26" height="22" rx="2" fill="{_CHIP}"/>'
             f'<rect x="138" y="62" width="22" height="22" rx="2" fill="{_CHIP}"/>'
             f'<g{_pid(p, "soc")}><rect x="86" y="70" width="50" height="50" rx="3" fill="{_METAL}" stroke="{INK}" stroke-width="2.5"/>'
             f'<rect x="93" y="77" width="36" height="36" rx="2" fill="#e4e7ea"/>'
             f'<path d="M99 90H123M99 98H117" stroke="#8d939c" stroke-width="3" stroke-linecap="round"/></g>')
    gpio = (f'<g{_pid(p, "gpio")}><rect x="178" y="52" width="14" height="90" rx="2" fill="{_CHIP}"/>'
            + "".join(f'<circle cx="{182 + (i % 2) * 6}" cy="{57 + (i // 2) * 7}" r="1.8" fill="{_GOLD}"/>' for i in range(26))
            + "</g>")
    bottom = (f'<rect x="56" y="146" width="20" height="12" rx="5" fill="{_METAL}" stroke="{INK}" stroke-width="2"/>'
              f'<rect x="88" y="138" width="28" height="22" rx="2" fill="{_METAL}" stroke="{INK}" stroke-width="2"/>'
              f'<circle cx="140" cy="150" r="7" fill="{_CHIP}" stroke="{INK}" stroke-width="2"/>')
    led = f'<circle{_pid(p, "led")} cx="34" cy="128" r="4.5" fill="{PRIMARY}" stroke="{INK}" stroke-width="1.5"/>'
    return svg(f'<rect x="8" y="24" width="186" height="128" rx="8" fill="{_PCB}" stroke="{INK}" stroke-width="3"/>'
               + holes + traces + chips + gpio + led + bottom + ports, "0 0 200 162")


def i_hand(skin="#e2ad8c", p=None):
    """An open hand, palm up, fingers pointing up (200×300 view box), for real-world scale next to an object.
    Palm centre ≈ (100, 175), palm width ≈ 120 units (an adult palm ≈ 85 mm). p: parts `{p}-fingers`, `{p}-thumb`."""
    crease = "#b9805f"
    fingers = "".join(f'<rect x="{x}" y="{y}" width="{w}" height="{150 - y}" rx="{w / 2}" fill="{skin}" stroke="{INK}" stroke-width="3"/>'
                      for x, y, w in ((40, 44, 26), (69, 24, 27), (99, 34, 26), (128, 64, 22)))
    return svg(f'<path d="M64 226L56 300H144L136 226Z" fill="{skin}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
               f'<g{_pid(p, "fingers")}>{fingers}</g>'
               f'<g{_pid(p, "thumb")}><rect x="22" y="136" width="30" height="82" rx="15" fill="{skin}" stroke="{INK}" stroke-width="3" '
               f'transform="rotate(-30 52 214)"/></g>'
               f'<path d="M40 128Q38 118 50 118H150Q160 118 158 132L154 214Q150 238 124 240H76Q48 238 44 214Z" '
               f'fill="{skin}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
               f'<rect x="43" y="110" width="105" height="40" fill="{skin}"/>'
               f'<path d="M58 150Q100 140 146 152M54 182Q90 170 120 196M76 214Q110 206 140 176" fill="none" stroke="{crease}" '
               f'stroke-width="2.5" stroke-linecap="round" opacity=".8"/>', "0 0 200 300")


def i_router(p=None):
    """A home router with two antennas; p: four front LEDs `{p}-led0`…`{p}-led3`."""
    leds = "".join(f'<circle{_pid(p, f"led{i}")} cx="{30 + i * 12}" cy="66" r="3.5" fill="{PRIMARY if i else ACCENT}"/>' for i in range(4))
    return svg(f'<path d="M26 50L18 14M74 50L82 14" stroke="{INK}" stroke-width="4.5" stroke-linecap="round"/>'
               f'<circle cx="18" cy="13" r="4" fill="{INK}"/><circle cx="82" cy="13" r="4" fill="{INK}"/>'
               f'<rect x="8" y="50" width="84" height="32" rx="7" fill="{SOFT}" stroke="{INK}" stroke-width="3.5"/>{leds}'
               f'<rect x="18" y="82" width="10" height="5" fill="{INK}"/><rect x="72" y="82" width="10" height="5" fill="{INK}"/>')


def i_laptop():
    return svg(f'<rect x="18" y="20" width="64" height="44" rx="3" fill="{PAPER}" stroke="{INK}" stroke-width="3.5"/>'
               f'<rect x="24" y="26" width="52" height="32" fill="{SOFT}"/>'
               f'<path d="M30 36H60M30 44H68M30 52H50" stroke="{MUTED}" stroke-width="3" stroke-linecap="round"/>'
               f'<path d="M8 70H92L86 80H14Z" fill="{SOFT}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
               f'<path d="M14 64H86V70H14Z" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>')


def i_rack(p=None):
    """A data-centre server rack (60×120 view box): eight units with status LEDs; p: `{p}-led0`…`{p}-led7`."""
    units = "".join(f'<rect x="10" y="{10 + i * 13}" width="40" height="9" rx="1.5" fill="{SOFT}"/>'
                    f'<circle{_pid(p, f"led{i}")} cx="15" cy="{14.5 + i * 13}" r="2" fill="{PRIMARY if i % 3 else ACCENT}"/>'
                    f'<rect x="22" y="{13 + i * 13}" width="22" height="3" rx="1.5" fill="{MUTED}" opacity=".6"/>' for i in range(8))
    return svg(f'<rect x="4" y="3" width="52" height="114" rx="3" fill="{PAPER}" stroke="{INK}" stroke-width="3"/>{units}', "0 0 60 120")


def i_calendar(p=None):
    """A calendar page; p: `{p}-event` (an event bar in the grid, hidden until shown) and `{p}-day` (today)."""
    cells = "".join(f'<rect x="{20 + (i % 4) * 16}" y="{46 + (i // 4) * 13}" width="12" height="9" rx="1.5" fill="{MUTED}" opacity=".45"/>'
                    for i in range(12))
    return svg(f'<rect x="12" y="20" width="76" height="70" rx="6" fill="{PAPER}" stroke="{INK}" stroke-width="3.5"/>'
               f'<path d="M12 26Q12 20 18 20H82Q88 20 88 26V38H12Z" fill="{PRIMARY}"/>'
               f'<path d="M32 12V28M68 12V28" stroke="{INK}" stroke-width="5" stroke-linecap="round"/>{cells}'
               f'<rect{_pid(p, "day")} x="52" y="59" width="12" height="9" rx="1.5" fill="{WARM}"/>'
               f'<rect{_pid(p, "event")} x="20" y="72" width="60" height="10" rx="3" fill="{ACCENT}"/>')


def i_film():
    """A film frame with a play mark (a media library)."""
    holes = "".join(f'<rect x="{x}" y="{24 + i * 14}" width="6" height="7" rx="1" fill="{INK}"/>' for x in (19, 75) for i in range(4))
    return svg(f'<rect x="12" y="16" width="76" height="68" rx="5" fill="{SOFT}" stroke="{INK}" stroke-width="3.5"/>{holes}'
               f'<rect x="30" y="22" width="40" height="56" rx="2" fill="{PAPER}"/><path d="M44 38L60 50L44 62Z" fill="{PRIMARY}"/>')


def i_cloud():
    return svg(f'<path d="M28 76Q10 76 10 60Q10 45 26 44Q28 24 48 24Q64 24 70 38Q90 36 90 56Q90 76 70 76Z" '
               f'fill="{PAPER}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>')


def i_sun():
    rays = "".join(f'<rect x="47" y="6" width="6" height="14" rx="3" fill="{WARM}" transform="rotate({a} 50 50)"/>' for a in range(0, 360, 45))
    return svg(f'{rays}<circle cx="50" cy="50" r="20" fill="{WARM}" stroke="{INK}" stroke-width="3"/>')


def i_moon():
    return svg(f'<path d="M62 14A36 36 0 1 0 86 62A28 28 0 1 1 62 14Z" fill="{PAPER}" stroke="{WARM}" stroke-width="4" stroke-linejoin="round"/>'
               f'<circle cx="80" cy="22" r="3" fill="{WARM}"/><circle cx="90" cy="38" r="2" fill="{WARM}"/>')


def i_bolt():
    return svg(f'<path d="M56 6L22 56H46L40 94L78 40H54Z" fill="{WARM}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>')


def i_lock(p=None, fill=PRIMARY):
    """A padlock (privacy, protection). p: `{p}-shackle` (move it y −14 to open the lock, back to 0 to close it)
    and `{p}-hole` (the keyhole). Added for PrivacidadEsconder (2026-10-14)."""
    return svg(f'<path{_pid(p, "shackle")} d="M31 48V33Q31 13 50 13Q69 13 69 33V48" fill="none" stroke="{INK}" stroke-width="9" stroke-linecap="round"/>'
               f'<rect x="17" y="44" width="66" height="48" rx="7" fill="{fill}" stroke="{INK}" stroke-width="4"/>'
               f'<g{_pid(p, "hole")}><circle cx="50" cy="63" r="7" fill="{ON_FILL}"/><path d="M46.5 66H53.5L52 79H48Z" fill="{ON_FILL}"/></g>')


def i_scale(p=None):
    """A balance scale (200×160 view box), for weighing two sides. p: `{p}-beam` (rotate it about its pivot
    with transformOrigin "100px 34px" (svgOrigin) to tip the scale), `{p}-pan-l` / `{p}-pan-r` (the hanging pans; move
    them in y with the tip: about −1.2 px per degree for the rising side, +1.2 for the falling one in view-box units).
    Added for PrivacidadEsconder (2026-10-14)."""
    def pan(side, x):
        return (f'<g{_pid(p, "pan-" + side)}><path d="M{x} 36L{x - 22} 96M{x} 36L{x + 22} 96" stroke="{INK}" stroke-width="2.5"/>'
                f'<path d="M{x - 30} 96H{x + 30}Q{x + 26} 116 {x} 116Q{x - 26} 116 {x - 30} 96Z" fill="{WARM}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/></g>')
    return svg(f'<path d="M70 152H130L120 140H80Z" fill="{SOFT}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
               f'<rect x="96" y="30" width="8" height="112" fill="{MUTED}" stroke="{INK}" stroke-width="2.5"/>'
               f'{pan("l", 30)}{pan("r", 170)}'
               f'<g{_pid(p, "beam")}><rect x="26" y="31" width="148" height="7" rx="3.5" fill="{PRIMARY}" stroke="{INK}" stroke-width="2.5"/>'
               f'<circle cx="30" cy="34.5" r="5" fill="{INK}"/><circle cx="170" cy="34.5" r="5" fill="{INK}"/></g>'
               f'<circle cx="100" cy="34" r="9" fill="{WARM}" stroke="{INK}" stroke-width="3"/>', "0 0 200 160")


def i_photo():
    """A photo print: frame, sun and hills (photos, a camera roll). Added for PrivacidadEsconder (2026-10-14)."""
    return svg(f'<rect x="10" y="18" width="80" height="64" rx="6" fill="{PAPER}" stroke="{INK}" stroke-width="3.5"/>'
               f'<circle cx="34" cy="38" r="8" fill="{WARM}"/>'
               f'<path d="M14 76L38 52L54 66L66 56L86 76Z" fill="{PRIMARY}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>')


def i_officer(fill=ACCENT):
    """An authority figure: a person with a peaked cap and a badge (customs agents, an authority).
    Added for PrivacidadEsconder (2026-10-14)."""
    return svg(person(fill) +
               f'<path d="M30 24Q50 6 70 24L72 30H28Z" fill="{SOFT}" stroke="{INK}" stroke-width="3" stroke-linejoin="round"/>'
               f'<path d="M26 30H74Q72 36 50 36Q28 36 26 30Z" fill="{INK}"/>'
               f'<path d="M62 66L70 70V78Q70 84 62 88Q54 84 54 78V70Z" fill="{WARM}" stroke="{INK}" stroke-width="2.5" stroke-linejoin="round"/>')


# --- PC parts (Builder, 2026-10-14). One semantic colour per part, kept by i_tower's parts:
# CPU = ACCENT, RAM = PRIMARY, GPU = ALERT, storage = WARM, cooling = HOT.
def i_cpu(fill=None, p=None):
    """A processor chip from above: pins on four sides, die in the middle. Added for Builder (2026-10-14)."""
    fill = fill or ACCENT
    pins = "".join(f'<rect x="{30 + i * 12}" y="10" width="6" height="12" fill="{INK}"/><rect x="{30 + i * 12}" y="78" width="6" height="12" fill="{INK}"/>'
                   f'<rect x="10" y="{30 + i * 12}" width="12" height="6" fill="{INK}"/><rect x="78" y="{30 + i * 12}" width="12" height="6" fill="{INK}"/>'
                   for i in range(4))
    return svg(f'{pins}<rect x="20" y="20" width="60" height="60" rx="4" fill="{fill}" stroke="{INK}" stroke-width="4"/>'
               f'<rect{_pid(p, "die")} x="36" y="36" width="28" height="28" fill="{ON_FILL}"/>')


def i_ram(fill=None):
    """A memory stick: chips on a coloured PCB, gold contacts and the key notch. Added for Builder (2026-10-14)."""
    fill = fill or PRIMARY
    chips = "".join(f'<rect x="{15 + i * 19}" y="38" width="13" height="16" fill="{ON_FILL}"/>' for i in range(4))
    teeth = "".join(f'<rect x="{12 + i * 6}" y="64" width="3.5" height="8" fill="{_GOLD}"/>' for i in range(13) if i != 7)
    return svg(f'<path d="M8 30H92V64H8Z" fill="{fill}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>{chips}{teeth}')


def i_gpu(fill=None, p=None):
    """A graphics card from the side: shroud with two fans, a colour stripe, PCIe contacts and the bracket.
    p: `{p}-fan0`, `{p}-fan1` (spin with svgOrigin at their centres 32 48 / 66 48). Added for Builder (2026-10-14)."""
    fill = fill or ALERT

    def fan(i, cx):
        blades = "".join(f'<path d="M{cx} 48L{cx + 4} 37Q{cx + 9} 41 {cx + 6} 46Z" fill="{fill}" transform="rotate({a} {cx} 48)"/>' for a in range(0, 360, 72))
        return (f'<circle cx="{cx}" cy="48" r="14" fill="{SOFT}" stroke="{INK}" stroke-width="2.5"/>'
                f'<g{_pid(p, f"fan{i}")}>{blades}</g><circle cx="{cx}" cy="48" r="3.5" fill="{INK}"/>')
    return svg(f'<rect x="88" y="24" width="6" height="48" fill="{MUTED}" stroke="{INK}" stroke-width="2"/>'
               f'<rect x="8" y="28" width="80" height="40" rx="4" fill="{PAPER}" stroke="{INK}" stroke-width="3.5"/>'
               f'<rect x="8" y="28" width="80" height="6" fill="{fill}"/>{fan(0, 32)}{fan(1, 66)}'
               f'<rect x="20" y="68" width="44" height="7" fill="{_GOLD}" stroke="{INK}" stroke-width="1.5"/>')


def i_ssd(fill=None):
    """An M.2 SSD: a slim stick with two chips, edge contacts on the left and the screw notch on the right.
    Added for Builder (2026-10-14)."""
    fill = fill or WARM
    teeth = "".join(f'<rect x="6" y="{40 + i * 5}" width="7" height="3" fill="{_GOLD}"/>' for i in range(4))
    return svg(f'<path d="M12 36H86A6 6 0 0 1 86 64H12Z" fill="{fill}" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
               f'{teeth}<rect x="22" y="42" width="24" height="16" fill="{ON_FILL}"/><rect x="52" y="42" width="18" height="16" fill="{ON_FILL}"/>'
               f'<circle cx="86" cy="50" r="4" fill="{PAPER}" stroke="{INK}" stroke-width="2"/>')


def i_fan(fill=None, p=None):
    """A case fan (cooling): square frame, five blades, hub. p: `{p}-blades` (spin it with svgOrigin "50 50").
    Added for Builder (2026-10-14)."""
    fill = fill or HOT
    blades = "".join(f'<path d="M50 50L58 20Q72 26 70 42Z" fill="{fill}" stroke="{INK}" stroke-width="2" stroke-linejoin="round" '
                     f'transform="rotate({a} 50 50)"/>' for a in range(0, 360, 72))
    holes = "".join(f'<circle cx="{x}" cy="{y}" r="4" fill="{SOFT}" stroke="{INK}" stroke-width="1.5"/>' for x, y in ((18, 18), (82, 18), (18, 82), (82, 82)))
    return svg(f'<rect x="8" y="8" width="84" height="84" rx="8" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>{holes}'
               f'<circle cx="50" cy="50" r="36" fill="{SOFT}" stroke="{INK}" stroke-width="2.5"/>'
               f'<g{_pid(p, "blades")}>{blades}</g><circle cx="50" cy="50" r="9" fill="{INK}"/>')


def i_tower(p=None, gamer=False):
    """A desktop PC tower with a side window (160×220 view box): the parts sit on the motherboard in their
    part colours (i_cpu, i_ram, i_gpu, i_ssd, i_fan). p: `{p}-cpu`, `{p}-ram`, `{p}-gpu`, `{p}-ssd`, `{p}-fan`
    (hide them and enter one by one to assemble the PC), `{p}-led`. gamer=True: a lime glow inside the window
    and a third front fan. Added for Builder (2026-10-14)."""
    glow = (f'<rect x="20" y="20" width="92" height="180" fill="none" stroke="{PRIMARY}" stroke-width="3" opacity=".7"/>' if gamer else "")
    fans = ((133, 74), (133, 112), (133, 150)) if gamer else ((133, 92), (133, 132))
    fan = "".join(f'<circle cx="{x}" cy="{y}" r="11" fill="{SOFT}" stroke="{HOT}" stroke-width="3"/>'
                  + "".join(f'<path d="M{x} {y}L{x + 2} {y - 8}Q{x + 6} {y - 6} {x + 5} {y - 2}Z" fill="{HOT}" transform="rotate({a} {x} {y})"/>'
                            for a in (0, 120, 240))
                  + f'<circle cx="{x}" cy="{y}" r="2.5" fill="{INK}"/>' for x, y in fans)
    return svg(f'<rect x="8" y="8" width="144" height="204" rx="8" fill="{PAPER}" stroke="{INK}" stroke-width="4"/>'
               f'<rect x="18" y="18" width="96" height="184" fill="{SOFT}" stroke="{INK}" stroke-width="2"/>{glow}'
               f'<rect x="26" y="26" width="80" height="120" fill="{MUTED}" opacity=".22"/>'
               f'<rect x="18" y="162" width="96" height="40" fill="{MUTED}" opacity=".3"/>'
               f'<circle{_pid(p, "led")} cx="133" cy="28" r="5" fill="{PRIMARY}" stroke="{INK}" stroke-width="1.5"/>'
               f'<path d="M124 44H142" stroke="{LINE}" stroke-width="3"/>'
               f'<g{_pid(p, "fan")}>{fan}</g>'
               f'<g{_pid(p, "cpu")}><rect x="36" y="38" width="34" height="34" rx="2" fill="{ACCENT}" stroke="{INK}" stroke-width="2.5"/>'
               f'<rect x="45" y="47" width="16" height="16" fill="{ON_FILL}"/></g>'
               f'<g{_pid(p, "ram")}><rect x="80" y="34" width="7" height="46" fill="{PRIMARY}" stroke="{INK}" stroke-width="2"/>'
               f'<rect x="92" y="34" width="7" height="46" fill="{PRIMARY}" stroke="{INK}" stroke-width="2"/></g>'
               f'<g{_pid(p, "ssd")}><rect x="36" y="84" width="46" height="10" rx="2" fill="{WARM}" stroke="{INK}" stroke-width="2"/></g>'
               f'<g{_pid(p, "gpu")}><rect x="24" y="106" width="86" height="26" rx="2" fill="{PAPER}" stroke="{INK}" stroke-width="2.5"/>'
               f'<rect x="24" y="106" width="86" height="5" fill="{ALERT}"/>'
               f'<circle cx="48" cy="121" r="8" fill="{SOFT}" stroke="{INK}" stroke-width="1.5"/>'
               f'<circle cx="84" cy="121" r="8" fill="{SOFT}" stroke="{INK}" stroke-width="1.5"/></g>', "0 0 160 220")


def i_hardhat(fill=None):
    """A construction hard hat (building, the Builder pattern). Added for Builder (2026-10-14)."""
    fill = fill or WARM
    return svg(f'<path d="M20 66Q20 28 50 26Q80 28 80 66Z" fill="{fill}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
               f'<path d="M42 27V54H58V27" fill="none" stroke="{INK}" stroke-width="3.5" stroke-linejoin="round"/>'
               f'<rect x="8" y="64" width="84" height="12" rx="6" fill="{fill}" stroke="{INK}" stroke-width="4"/>')


def i_clipboard(fill=None, p=None):
    """A clipboard with a numbered checklist (a recipe, a predefined sequence of steps). p: `{p}-check0..2`
    (the check marks). Added for Builder (2026-10-14)."""
    fill = fill or PRIMARY
    rows = "".join(f'<rect x="26" y="{34 + i * 18}" width="10" height="10" fill="none" stroke="{INK}" stroke-width="2.5"/>'
                   f'<path{_pid(p, f"check{i}")} d="M26 {38 + i * 18}L31 {44 + i * 18}L40 {31 + i * 18}" fill="none" stroke="{fill}" '
                   f'stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
                   f'<rect x="44" y="{36 + i * 18}" width="{30 - (i % 2) * 8}" height="6" rx="3" fill="{MUTED}"/>' for i in range(3))
    return svg(f'<rect x="16" y="14" width="68" height="80" rx="6" fill="{PAPER}" stroke="{INK}" stroke-width="3.5"/>'
               f'<rect x="36" y="8" width="28" height="14" rx="3" fill="{SOFT}" stroke="{INK}" stroke-width="3"/>{rows}')

# ============================================================================
# ASCII block font (5 rows) for big ASCII headlines: ascii_banner("LLEGAR") → art for s.ascii().
# ============================================================================
_BLOCK = {
    "A": ["▄▀▀▄", "█  █", "█▀▀█", "█  █", "▀  ▀"], "B": ["█▀▀▄", "█  █", "█▀▀▄", "█  █", "▀▀▀ "],
    "C": ["▄▀▀▀", "█   ", "█   ", "█   ", " ▀▀▀"], "D": ["█▀▀▄", "█  █", "█  █", "█  █", "▀▀▀ "],
    "E": ["█▀▀▀", "█   ", "█▀▀ ", "█   ", "▀▀▀▀"], "F": ["█▀▀▀", "█   ", "█▀▀ ", "█   ", "▀   "],
    "G": ["▄▀▀▀", "█   ", "█ ▀█", "█  █", " ▀▀▀"], "H": ["█  █", "█  █", "█▀▀█", "█  █", "▀  ▀"],
    "I": ["▀█▀", " █ ", " █ ", " █ ", "▀▀▀"], "J": ["  ▀█", "   █", "   █", "█  █", " ▀▀ "],
    "K": ["█  █", "█ █ ", "██  ", "█ █ ", "▀  ▀"], "L": ["█   ", "█   ", "█   ", "█   ", "▀▀▀▀"],
    "M": ["█▄ ▄█", "█ ▀ █", "█   █", "█   █", "▀   ▀"], "N": ["█▄  █", "█ █ █", "█  ██", "█   █", "▀   ▀"],
    "O": ["▄▀▀▄", "█  █", "█  █", "█  █", " ▀▀ "], "P": ["█▀▀▄", "█  █", "█▀▀ ", "█   ", "▀   "],
    "Q": ["▄▀▀▄", "█  █", "█  █", "█ ▀▄", " ▀▀ ▀"], "R": ["█▀▀▄", "█  █", "█▀▀▄", "█  █", "▀  ▀"],
    "S": ["▄▀▀▀", "█   ", " ▀▀▄", "   █", "▀▀▀ "], "T": ["▀█▀", " █ ", " █ ", " █ ", " ▀ "],
    "U": ["█  █", "█  █", "█  █", "█  █", " ▀▀ "], "V": ["█   █", "█   █", "▀▄ ▄▀", " █ █ ", "  ▀  "],
    "W": ["█   █", "█   █", "█ █ █", "█▄▀▄█", "▀   ▀"], "X": ["█  █", "▀▄▄▀", " ██ ", "▄▀▀▄", "▀  ▀"],
    "Y": ["█   █", "▀▄ ▄▀", "  █  ", "  █  ", "  ▀  "], "Z": ["▀▀▀█", "  ▄▀", " █  ", "▄▀  ", "▀▀▀▀"],
    "0": ["▄▀▀▄", "█ ▄█", "█▀ █", "█  █", " ▀▀ "], "1": ["▄█", " █", " █", " █", "▀▀"],
    "?": ["▄▀▀▄", "   █", "  ▀ ", "  ▄ ", "  ▀ "], "¿": [" ▀  ", " ▀  ", "▄▀  ", "█  ▄", " ▀▀ "],
    "!": ["█", "█", "█", "▄", "▀"], ".": [" ", " ", " ", " ", "▀"], " ": ["  ", "  ", "  ", "  ", "  "],
}


def ascii_banner(text: str, gap: int = 1) -> str:
    """`text` in the 5-row block font (A–Z, 0, 1, ? ¿ ! . and space; accents dropped)."""
    plain = unicodedata.normalize("NFD", text.upper())
    plain = "".join(c for c in plain if unicodedata.category(c) != "Mn")
    rows = ["", "", "", "", ""]
    for c in plain:
        glyph = _BLOCK[c]
        width = max(len(g) for g in glyph)
        for i in range(5):
            rows[i] += glyph[i].ljust(width) + " " * gap
    return "\n".join(r.rstrip() for r in rows)


def icon_card(s, key, label, icon, x, y, w=190, h=160, tint="glass", size=28):
    return s.card(key, label, x, y, w, h, tint, size, icon=icon, icon_h=round(h * 0.5))


def row_card(s, key, label, icon, x, y, w, h=96, tint="glass", size=36, extra=""):
    """A horizontal card: icon on the left, label, optional extra HTML on the right."""
    ih = h - 26
    body = (f'<div style="position:absolute;left:16px;top:13px;width:{ih}px;height:{ih}px">{icon}</div>'
            f'<div class="v-text" style="position:absolute;left:{ih + 34}px;right:12px;top:0;bottom:0;font-size:{size}px;'
            f'font-weight:850;justify-content:flex-start;white-space:nowrap">{html.escape(label)}</div>{extra}')
    return s.add(key, x, y, w, h, body, "v-card", f"background:{TINTS[tint]}")


def bar(s, key, x, y, w, h=16, color=PRIMARY):
    """A probability bar: track plus a fill element whose scaleX animates."""
    s.add(key, x, y, w, h, f'<div style="position:absolute;inset:0;border-radius:{h}px;background:{TRACK}"></div>')
    s.add(key + "-fill", x, y, w, h, "", "", f"border-radius:{h}px;background:{color}", origin="0% 50%")
    s.set(s.sel(key + "-fill"), scaleX=0.02)
    return key


def dot(s, key, x, y, size=18, color=PRIMARY):
    return s.add(key, x - size / 2, y - size / 2, size, size, "", "v-dot", f"background:{color};box-shadow:{DOT_SHADOW}")


def ring(s, key, x, y, w, h, color=PRIMARY):
    return s.add(key, x, y, w, h, "", "", f"border-radius:50%;border:5px dashed {color};background:rgba(91,76,240,.07)")


def pill(s, key, label, x, y, w, h=70, tint="glass", size=32, color=INK):
    return s.card(key, label, x, y, w, h, tint, size, pill=True, color=color)


# Deterministic scatter positions (no randomness in compositions).
def scatter(n, cx, cy, rx, ry, seed=1):
    points = []
    for i in range(n):
        a = (i * 137.508 + seed * 31) % 360
        r = 0.45 + 0.55 * (((i * 7919 + seed * 104729) % 1000) / 1000)
        points.append((round(cx + math.cos(math.radians(a)) * rx * r), round(cy + math.sin(math.radians(a)) * ry * r)))
    return points


# ============================================================================
# Output
# ============================================================================
def finish_all() -> None:
    manifest = []
    for track in sorted({scene.track for scene in scenes}):
        lane = [scene for scene in scenes if scene.track == track]  # neighbours share a track
        for i, scene in enumerate(lane):
            prev_gap = scene.start - lane[i - 1].end if i else 99
            next_gap = lane[i + 1].start - scene.end if i + 1 < len(lane) else 99
            if prev_gap < -1e-3:
                raise ValueError(f"{scene.slug} overlaps the previous scene")
            last = i + 1 == len(lane)
            if last:
                scene.live.clear()  # the last scene on a track holds to its end
            # A neighbour without a panel (cutout scenes) counts as a gap: the panel slides in/out.
            prev_bare = i > 0 and lane[i - 1].panel == "none"
            next_bare = not last and lane[i + 1].panel == "none"
            manifest.append(scene.finish(enter_bg=prev_gap > 0.4 or prev_bare, exit_bg=(next_gap > 0.4 or next_bare) and not last))
    manifest.sort(key=lambda m: (m["start"], m["track"]))

    sounds.sort(key=lambda x: x["at"])
    # Soften rapid repeats of the same effect so bursts read as one gesture.
    last_at: dict[str, float] = {}
    for sound in sounds:
        if sound["at"] - last_at.get(sound["kind"], -9) < 0.5:
            sound["volume"] = round(sound["volume"] * 0.7, 3)
        last_at[sound["kind"]] = sound["at"]
    sfx_out = []
    lanes: list[float] = []
    for n, sound in enumerate(sounds, 1):
        end = sound["at"] + sound["length"]
        lane = next((k for k, free in enumerate(lanes) if free <= sound["at"]), None)
        if lane is None:
            lanes.append(0)
            lane = len(lanes) - 1
        lanes[lane] = end
        sound["track"] = 30 + lane
        sfx_out.append({"id": f"sfx-{n:03d}", "src": f"media/audio/sfx/{sound['kind']}.mp3", "start": sound["at"],
                        "duration": round(min(sound["length"], DURATION - sound["at"]), 3), "volume": sound["volume"],
                        "track": sound["track"], "kind": sound["kind"], "scene": sound["scene"]})
    common.write_json("scripts/visual-scenes.json", manifest)
    common.write_json("scripts/visual-sfx.json", sfx_out)
    if len(lanes) > 10:
        raise ValueError(f"{len(lanes)} simultaneous SFX lanes; tracks 30-39 allow 10. Thin out overlapping sounds.")
    print(f"  {len(manifest)} scenes, {len(sfx_out)} sound effects")


def build_outro() -> None:
    """End card from reel.config.json "outro": a lime curtain and a grid-paper sheet sweep up over
    the last frame, then `$ whoami`, the name (decoded), one row per social handle, and the website
    as a lime button with a blinking cursor. Platform names are text (no logos)."""
    cfg = common.CONFIG.get("outro")
    if not cfg:
        return
    t0 = OUTRO_START
    s = Scene("99-outro", t0, DURATION, decor=(), panel="none", track=12, layer="overlay")
    solid = _T["bg"] if TERMINAL else PAPER
    for key, delay, style in (("curtain", 0.0, f"background:{PRIMARY}"),
                              ("sheet", 0.12, f"background:{PANEL};background-color:{solid}")):
        s.add(key, 0, 0, 1080, 1920, "", "", style)
        s.set(s.sel(key), y=1920, opacity=1)
        s.tw(s.sel(key), t0 + delay, 0.42, "power3.inOut", y=0)
    s.sfx(t0, "whoosh")
    x, top, width = 90, cfg.get("top", 430), 820
    t = t0 + 0.5
    s.typewrite("who", "$ whoami", x, top, 40, t, cps=26, color=MUTED, sfx="key-press", gain=0.3)
    name = cfg.get("name", "")
    size = round(min(100, width / ((len(name) + 1) * MONO_ADVANCE)))
    s.decode("name", name, x, top + 64, size, t + 0.3, color=INK, stagger=0.03, sfx="typing", gain=0.45)
    rule_y = top + 64 + round(size * 1.1) + 26
    s.add("rule", x, rule_y, width, 3, "", "", f"background:{LINE}", origin="0% 50%")
    s.enter("rule", t + 0.75, "wipe")
    handles = cfg.get("handles", [])
    row_y = rule_y + 50
    for i, (platform, handle) in enumerate(handles):
        body = (f'<div style="position:absolute;left:26px;right:20px;top:0;bottom:0;display:flex;align-items:center;gap:22px;white-space:nowrap">'
                f'<i style="display:block;width:14px;height:14px;background:{PRIMARY};flex:0 0 auto"></i>'
                f'<span style="width:230px;font-size:26px;font-weight:600;letter-spacing:.12em;color:{MUTED}">{html.escape(platform.upper())}</span>'
                f'<span style="font-size:50px;font-weight:700;letter-spacing:-.04em;color:{INK}">{html.escape(handle)}</span></div>')
        s.add(f"h{i}", x, row_y + i * 128, width, 108, body, "v-card", f"background:{TINTS['glass']}")
        s.enter(f"h{i}", t + 0.95 + i * 0.13, "left", "click-soft" if i % 2 == 0 else "click", gain=0.2)
    web = cfg.get("website")
    if web:
        web_y = row_y + len(handles) * 128 + 34
        web_w = round(len(web) * 50 * MONO_ADVANCE) + 150
        body = (f'<div style="position:absolute;left:30px;top:0;bottom:0;display:flex;align-items:center;gap:18px;white-space:nowrap;'
                f'font-size:50px;font-weight:800;letter-spacing:-.04em;color:{ON_FILL}">{html.escape(web)}'
                f'<span id="{s.id}-web-cur" style="display:block;width:26px;height:46px;background:{ON_FILL}"></span></div>')
        shadow = _T["accent_shadow"] if TERMINAL else INK
        s.add("web", x, web_y, web_w, 112, body, "", f"background:{PRIMARY};box-shadow:10px 10px 0 {shadow}")
        t_web = t + 0.95 + len(handles) * 0.13 + 0.25
        s.enter("web", t_web, "stamp", "ping", rest={"rotation": -2})
        s._blink(f"#{s.id}-web-cur", t_web + 0.5)


def run() -> None:
    """Execute the project's scripts/scenes.py in this namespace, then write all outputs."""
    path = common.p("scripts/scenes.py")
    if not path.exists():
        raise SystemExit("Missing scripts/scenes.py (copy the template's starter).")
    exec(compile(path.read_text(), str(path), "exec"), globals())
    build_outro()
    finish_all()
