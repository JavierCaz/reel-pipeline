"""Named presets so reel.config.json can say "zoom" or "page-turn" instead of raw numbers.

Transition poses (proven on the first finished reels): the outgoing crop
accelerates into the cut (power4.in), the incoming crop settles after it (power4.out).
"""

TRANSITIONS = {
    # kind: (outgoing pose, incoming pose, outgoing duration, incoming duration)
    "swipe": ({"x": -220, "y": -18, "scale": 1.52, "rotation": -2.2}, {"x": 220, "y": 18, "scale": 1.52, "rotation": 2.2}, 0.24, 0.29),
    "swipe-reverse": ({"x": 220, "y": -18, "scale": 1.52, "rotation": 2.2}, {"x": -220, "y": 18, "scale": 1.52, "rotation": -2.2}, 0.24, 0.29),
    "zoom": ({"x": 0, "y": -96, "scale": 1.67, "rotation": 0}, {"x": 0, "y": 84, "scale": 1.50, "rotation": 0}, 0.26, 0.31),
    "spin": ({"x": -120, "y": -24, "scale": 1.57, "rotation": -11}, {"x": 120, "y": 24, "scale": 1.57, "rotation": 11}, 0.27, 0.33),
    "spin-zoom-in": ({"x": -135, "y": -28, "scale": 1.80, "rotation": -15}, {"x": 85, "y": 18, "scale": 1.38, "rotation": 5}, 0.30, 0.28),
    "spin-zoom-out": ({"x": 85, "y": -18, "scale": 1.38, "rotation": 5}, {"x": -135, "y": 28, "scale": 1.80, "rotation": -15}, 0.24, 0.37),
}

# Transition / opening sounds. `peak` is the offset of the loudest moment, placed on the cut.
SOUNDS = {
    "page-turn": {"src": "media/audio/shared-sfx/creatorshome-turn-a-page-336933.mp3", "peak": 0.06, "duration": 0.9, "volume": 0.3},
    "flame": {"src": "media/audio/shared-sfx/soundreality-whoosh-flame-388763.mp3", "media_start": 0.5, "peak": 0.25, "duration": 0.8, "volume": 0.25},
    "whoosh": {"src": "media/audio/sfx/whoosh.mp3", "peak": 0.15, "duration": 0.57, "volume": 0.3},
    "transition-2": {"src": "media/audio/shared-sfx/oxidvideos-transition-sfx-2-409073.mp3", "peak": 0.15, "duration": 1.1, "volume": 0.45},
    "vortex": {"src": "media/audio/shared-sfx/soundreality-whoosh-vortex-2-388197.mp3", "start": 0.0, "media_start": 0.15, "duration": 1.85, "volume": 0.3},
}

# Default sound per transition kind (rotate so neighbours differ; config may override).
KIND_SOUND = {"swipe": "page-turn", "swipe-reverse": "page-turn", "zoom": "whoosh",
              "spin": "transition-2", "spin-zoom-in": "flame", "spin-zoom-out": "flame"}

# Opening shake over clip 1: covered 1.40-1.43x crop, alternating offsets and tilts, settled by 0.68 s.
OPENING_SHAKE = [
    {"at": 0.0, "x": -52, "y": 22, "scale": 1.4, "rotation": -4.5},
    {"at": 0.08, "x": 64, "y": -26, "scale": 1.43, "rotation": 5.2, "ease": "none"},
    {"at": 0.16, "x": -50, "y": 17, "scale": 1.37, "rotation": -4.1, "ease": "none"},
    {"at": 0.24, "x": 42, "y": -15, "scale": 1.32, "rotation": 3.4, "ease": "none"},
    {"at": 0.33, "x": -29, "y": 10, "scale": 1.25, "rotation": -2.5, "ease": "none"},
    {"at": 0.43, "x": 18, "y": -7, "scale": 1.19, "rotation": 1.6, "ease": "none"},
    {"at": 0.54, "x": -8, "y": 3, "scale": 1.1, "rotation": -0.7, "ease": "power1.out"},
    {"at": 0.68, "x": 0, "y": 0, "scale": 1, "rotation": 0, "ease": "power3.out"},
]

MUSIC = {
    "lofi": {"src": "media/audio/shared-music/velariomusic-lofi-relaxing-598427.mp3", "audible_length": 143.5},
}


def sound(name_or_dict):
    if isinstance(name_or_dict, dict):
        return name_or_dict
    if name_or_dict not in SOUNDS:
        raise SystemExit(f"Unknown sound preset '{name_or_dict}'. Known: {', '.join(SOUNDS)}")
    return dict(SOUNDS[name_or_dict])

# Visual themes: palette + font for concept graphics and the matching caption style.
# A reel picks one with reel.config.json "visuals.theme"; any palette/font/caption key in
# the config overrides the theme default. "terminal" is the house style (javiercazares.dev portfolio);
# "terminal-light" is its light variant (same motifs, the portfolio's light tokens).
THEMES = {
    "terminal": {
        "palette": {"ink": "#efefe8", "primary": "#b8ff35", "accent": "#00e5ff", "warm": "#ffd500", "soft": "#2a3326",
                    "paper": "#0c0f0c", "alert": "#ff4fd8", "muted": "#a1a99a", "hot": "#ff7a1a"},
        "font": "JetBrains Mono",
        "captions": {"accent": "#b8ff35", "accent_shadow": "#52742a", "font": '"JetBrains Mono",monospace',
                     "weight": 800, "letter_spacing": "-.06em", "font_size": 52},
        # Terminal family: surface tokens from the portfolio's :root (src/styles/global.css).
        "family": "terminal",
        "surface": {"bg": "#080a08", "panel": "#0c0f0c", "panel2": "#0a0c09", "line": "#343a30", "line_strong": "#4f5847",
                    "shadow": "#22281d", "accent_shadow": "#52742a", "grid_minor": "#10140f", "grid_major": "#1a2117",
                    "tint_accent": "#10170a", "tint_warm": "#151300"},
    },
    # Light variant of the house style: the portfolio's :root[data-theme="light"] tokens. Warm paper,
    # near-black ink, lime darkened to #356e00 (paper-coloured text on green fills), black hard shadows,
    # secondaries darkened for text like the portfolio's color-mix(group 52%, #000).
    "terminal-light": {
        "palette": {"ink": "#0d100c", "primary": "#356e00", "accent": "#007886", "warm": "#8a6d00", "soft": "#e9e8df",
                    "paper": "#fbfaf5", "alert": "#852970", "muted": "#5c6356", "hot": "#ff7a1a"},
        "font": "JetBrains Mono",
        # Captions sit on footage: outlined white text (paper plates were rejected 2026-10-06); keywords in the
        # theme's dark green on a paper chip with a black hard shadow (user request 2026-10-06).
        "captions": {"accent": "#356e00", "accent_shadow": "#0d100c", "font": '"JetBrains Mono",monospace',
                     "weight": 800, "letter_spacing": "-.06em", "font_size": 52,
                     "accent_chip": {"background": "#fbfaf5", "border": "#0d100c", "shadow": "#0d100c"}},
        "family": "terminal",
        "surface": {"bg": "#f2f1ea", "panel": "#fbfaf5", "panel2": "#e9e8df", "line": "#c4c6b8", "line_strong": "#8f9585",
                    "shadow": "#0d100c", "accent_shadow": "#0d100c", "grid_minor": "#e6e5dc", "grid_major": "#d9d8cc",
                    "tint_accent": "#dfe6d3", "tint_warm": "#ebe6d3", "hot_text": "#853f0e"},
    },
    "glass": {
        "palette": {"ink": "#182040", "primary": "#5b4cf0", "accent": "#2fc4d4", "warm": "#ffb08f", "soft": "#c9c3ff",
                    "paper": "#f6f7fb", "alert": "#e0533d", "muted": "#5d6584", "hot": "#ff7a59"},
        "font": "Montserrat",
        "captions": {"accent": "#9ce8dc", "accent_shadow": "#001c19a0", "font": '"Noto Sans",Arial,sans-serif',
                     "weight": 800, "letter_spacing": "-.035em", "font_size": 57},
    },
}


def theme(config: dict) -> dict:
    name = config.get("visuals", {}).get("theme", "terminal")
    if name not in THEMES:
        raise SystemExit(f"Unknown visuals.theme '{name}'. Known: {', '.join(THEMES)}")
    return THEMES[name]


# Presenter layouts (reel.config.json "stage"). Geometry in stage px for the house recording setup
# (chest-up, face ≈ x 330–750, y 760–1280). `region` is the part of the frame kept (x, y, w, h);
# `target` is where it lands (x, y, w); `round` makes the kept square a circle. `focus`: the face
# centre the region assumes; `build matte` measures the real one per segment (scripts/stage-focus.json)
# and the region is shifted onto it unless the stage entry sets its own "region".
# Graphics stay clear of the target and of the captions (y ≥ 1360) while a layout is active.
STAGE = {
    "card":     {"region": (140, 600, 800, 800), "target": (620, 905, 400), "round": False, "focus": (540, 960)},
    "circle":   {"region": (240, 660, 600, 600), "target": (700, 960, 340), "round": True, "focus": (540, 960)},
    # Default face layout (user 2026-10-08, SitioWeb): a square card cropped tight on the face — fills the space
    # beside tall graphics better than the circle and keeps the chin. Face at ~45 % from the crop top.
    # Bottom LEFT (user 2026-10-09, Adapter): the platforms' like/comment/share buttons sit on the right edge.
    "square":   {"region": (220, 690, 640, 640), "target": (60, 905, 400), "round": False, "focus": (540, 977)},
    "takeover": {"region": (240, 660, 600, 600), "target": (530, 1100, 20), "round": True, "hidden": True},
}
STAGE_MOVE = 0.8   # seconds for the presenter to move between layouts (crop leads, then the move)
STAGE_RING = 6     # accent ring around a card/circle, screen px
STAGE_SHADOW = 12  # hard shadow offset, screen px
# Cutout moments: the room behind the presenter blurs, dims, and gets a theme-coloured wash so the
# matte (sharp, above the graphics) stands out. The slight scale hides the blur's soft frame edges.
CUTOUT_BACKGROUND = {"blur": 10, "brightness": 0.88, "scale": 1.03, "in": 0.4, "out": 0.35}
