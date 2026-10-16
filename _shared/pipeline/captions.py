"""Step 5 — one caption track of short phrases from scripts/transcript.json.

reel.config.json "captions": {
  "keywords": ["micrófono", "perfil", ...],   # a few technical words get the accent (≥3 s apart)
  "accent": "#ffb08f", "accent_shadow": "#2a0d00a0",
  "box": {"left": 108, "top": 1360, "width": 864, "height": 245}, "font_size": 57,
  "font": '"Noto Sans",Arial,sans-serif', "weight": 800, "letter_spacing": "-.035em"
  "animation": "subtle" | "kinetic"  # optional; subtle preserves the original treatment
}
Phrases: ≤5 words, ≤34 characters, ≤2.25 s; break on sentence ends, commas, and pauses
>0.42 s; never end on a dangling function word; avoid one-word flashes.
Writes src/captions.html, scripts/caption-cues.json, scripts/subtitulos.srt.
"""

from __future__ import annotations

import html
import json
import re

from . import common, presets

# Spanish function words a phrase should not end on (carried into the next phrase).
WEAK = {"y", "a", "de", "que", "en", "el", "la", "los", "las", "tu", "tus", "un", "una",
        "con", "por", "para", "te", "se", "lo", "al", "del", "mi", "no", "es", "o"}


# A cue's show-set must come after the hide-all set at 0: two sets at the same time can resolve
# in either order on a seek, which hid any cue starting at 0.0 (SitioWeb, 2026-10-08).
SHOW_MIN = 0.001

def phrases(words):
    chunks, current = [], []
    for word in words:
        if current:
            gap = word["start"] - current[-1]["end"]
            chars = sum(len(item["text"]) + 1 for item in current) + len(word["text"])
            if (gap > .42 or re.search(r"[.!?…]$", current[-1]["text"])
                    or (current[-1]["text"].endswith(",") and len(current) >= 2)
                    or len(current) >= 5 or chars > 34
                    or word["end"] - current[0]["start"] > 2.25):
                chunks.append(current)
                current = []
        current.append(word)
    if current:
        chunks.append(current)
    for index in range(len(chunks) - 1):
        piece, following = chunks[index], chunks[index + 1]
        while (len(piece) > 2 and piece[-1]["text"].lower() in WEAK
               and following[0]["start"] - piece[-1]["end"] < .3
               and sum(len(w["text"]) + 1 for w in piece[-1:] + following) <= 38
               and len(following) < 6):
            following.insert(0, piece.pop())
    for index in range(len(chunks) - 1, 0, -1):
        piece, previous = chunks[index], chunks[index - 1]
        if (len(piece) == 1 and len(previous) <= 4
                and piece[-1]["end"] - previous[0]["start"] <= 2.7
                and piece[0]["start"] - previous[-1]["end"] < .32):
            previous.extend(chunks.pop(index))
    return chunks


def timestamp(seconds: float) -> str:
    ms = round(seconds * 1000)
    hours, rest = divmod(ms, 3600000)
    minutes, rest = divmod(rest, 60000)
    secs, ms = divmod(rest, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{ms:03}"


def kinetic_animations(cue: dict, index: int, word_count: int) -> list[str]:
    """Readable phrase arrivals, short word cascades, and speech-timed emphasis.

    Phrase, arrival-word, and emphasis-word transforms have separate wrappers,
    so an early spoken keyword never overwrites the entrance animation.
    """
    start, end = cue["start"], cue["end"]
    length = end - start
    root = f'#{cue["id"]}'
    line = root + " .caption-line"
    enter_duration = round(min(.23, length * .32), 3)
    exit_duration = round(min(.09, length * .16), 3)
    poses = (
        {"x": 0, "y": 26, "scale": .93, "rotation": 0},
        {"x": -26, "y": 6, "scale": .97, "rotation": -.75},
        {"x": 26, "y": 6, "scale": .97, "rotation": .75},
        {"x": 0, "y": 10, "scale": .90, "rotation": 0},
    )
    initial = {**poses[3 if cue["accent"] is not None else index % 4], "opacity": 1}
    rest = {"x": 0, "y": 0, "scale": 1, "rotation": 0, "opacity": 1}
    landing = {**rest, "duration": enter_duration, "ease": "power3.out", "immediateRender": False}
    result = [
        f'    tl.set("{root}", {{autoAlpha:1}}, {max(start, SHOW_MIN):.3f});',
        f'    tl.fromTo("{line}", {json.dumps(initial)}, {json.dumps(landing)}, {start:.3f});',
    ]
    # All words remain visible. The arrival wave resolves within about 0.23 s.
    if length >= .4:
        stagger = min(.05, .20 / max(1, word_count - 1), length * .06)
        for word_index in range(word_count):
            target = f'{line} > .caption-word:nth-child({word_index + 1})'
            frm = {"y": 16, "scale": .96}
            to = {"y": 0, "scale": 1, "duration": round(min(.17, length * .23), 3),
                  "ease": "power3.out", "immediateRender": False}
            result.append(f'    tl.set("{target}", {json.dumps(frm)}, {start:.3f});')
            result.append(f'    tl.fromTo("{target}", {json.dumps(frm)}, {json.dumps(to)}, {start + word_index * stagger:.3f});')
    if cue["accent"] is not None:
        result.append(f'    tl.set("{root} .accent-line", {{scaleX:0}}, {start:.3f});')
        at = cue["accent_at"]
        available = end - exit_duration - at
        if available >= .18:
            attack = round(min(.11, available * .35), 3)
            release = round(min(.18, available - attack), 3)
            target = root + " .accent-word .word-pop"
            result.append(f'    tl.fromTo("{target}", {{y:0,scale:1}}, '
                          f'{{y:-6,scale:1.12,duration:{attack},ease:"power3.out",immediateRender:false}}, {at:.3f});')
            result.append(f'    tl.fromTo("{target}", {{y:-6,scale:1.12}}, '
                          f'{{y:0,scale:1,duration:{release},ease:"power2.out",immediateRender:false}}, {at + attack:.3f});')
        result.append(f'    tl.fromTo("{root} .accent-line", {{scaleX:0}}, '
                      f'{{scaleX:1,duration:{min(.18, max(.04, end - at)):.3f},ease:"power3.out",immediateRender:false}}, {at:.3f});')
    departure = {"x": 0, "y": -9, "scale": 1.025, "rotation": 0, "opacity": .4,
                 "duration": exit_duration, "ease": "power2.in", "immediateRender": False}
    result.append(f'    tl.fromTo("{line}", {json.dumps(rest)}, {json.dumps(departure)}, {end - exit_duration:.3f});')
    result.append(f'    tl.set("{root}", {{autoAlpha:0}}, {end:.3f});')
    return result


def run() -> None:
    cfg = {**presets.theme(common.CONFIG)["captions"], **common.CONFIG.get("captions", {})}
    words = common.read_json("scripts/transcript.json")
    duration = common.read_json("scripts/cut-map.json")["duration"]
    if not words or any(not w["text"].strip() for w in words):
        raise ValueError("A reviewed, nonempty word transcript is required")
    if any(w["start"] < 0 or w["end"] < w["start"] for w in words):
        raise ValueError("Invalid word timing")
    accent = cfg.get("accent", "#9ce8dc")
    accent_shadow = cfg.get("accent_shadow", "#001c19a0")
    box = {"left": 108, "top": 1360, "width": 864, "height": 245, **cfg.get("box", {})}
    font_size = cfg.get("font_size", 57)
    font = cfg.get("font", '"Noto Sans",Arial,sans-serif')
    weight = cfg.get("weight", 800)
    tracking = cfg.get("letter_spacing", "-.035em")
    # Optional "plate": each phrase sits on a solid card (terminal-light), no outline or glow.
    plate = cfg.get("plate")
    plate_css = ""
    if plate:
        plate_css = (f"\n  .caption-line {{ color:{plate['color']}; -webkit-text-stroke:0; text-shadow:none;"
                     f" background:{plate['background']}; border:3px solid {plate['border']};"
                     f" box-shadow:8px 8px 0 {plate['shadow']}; padding:.18em .5em .24em; max-width:96%; }}")
    animation = cfg.get("animation", "subtle")
    if animation not in {"subtle", "kinetic"}:
        raise ValueError(f"Unknown caption animation: {animation!r}; use subtle or kinetic")
    # Optional "accent_chip": the keyword sits on a small solid card (terminal-light: paper chip, dark-green
    # text, black hard shadow) so a dark accent reads over footage. It lives inside the pop wrapper, so it
    # pops with the word; the underline wipes along the chip's bottom edge.
    chip = cfg.get("accent_chip")
    chip_css = ""
    if chip:
        target = ".accent-word .word-pop" if animation == "kinetic" else ".accent-word"
        chip_css = (f"\n  .accent-word {{ margin:0 .16em; }}"
                    f"\n  {target} {{ display:inline-block; position:relative; color:{accent}; -webkit-text-stroke:0; text-shadow:none;"
                    f" background:{chip['background']}; border:2px solid {chip['border']}; box-shadow:5px 5px 0 {chip['shadow']};"
                    f" padding:.02em .2em .1em; }}"
                    f"\n  .accent-word .accent-line {{ left:0; right:0; bottom:0; height:5px; border-radius:0; box-shadow:none; }}")
    terms = "|".join(re.escape(k) for k in cfg.get("keywords", [])) or r"(?!x)x"
    keyword = re.compile(rf"^(?:{terms})[,.!?…]*$", re.IGNORECASE)
    chunks = phrases(words)

    markup, cues = [], []
    last_accent_at = -10.0
    for index, chunk in enumerate(chunks):
        next_start = chunks[index + 1][0]["start"] if index + 1 < len(chunks) else duration
        start = max(0.0, chunk[0]["start"] - .035)
        end = min(duration, chunk[-1]["end"] + .085, next_start - .045 if index + 1 < len(chunks) else duration)
        end = max(start + .12, end)
        accent_index = None
        for word_index, word in enumerate(chunk):
            if keyword.fullmatch(word["text"]) and word["start"] - last_accent_at >= 3.0 and word["start"] < end - .24:
                accent_index, last_accent_at = word_index, word["start"]
                break
        phrase = " ".join(w["text"] for w in chunk)
        spans = []
        for word_index, word in enumerate(chunk):
            is_accent = word_index == accent_index
            klass = "caption-word accent-word" if is_accent else "caption-word"
            underline = '<i class="accent-line" aria-hidden="true"></i>' if is_accent else ""
            text = f'{html.escape(word["text"])}{underline}'
            if animation == "kinetic":
                text = f'<span class="word-pop">{text}</span>'
            spans.append(f'<span class="{klass}">{text}</span>')
        cue_id = f"caption-{index:03d}"
        markup.append(f'<div class="caption-cue" id="{cue_id}" aria-label="{html.escape(phrase, quote=True)}">'
                      f'<div class="caption-line">{" ".join(spans)}</div></div>')
        cues.append({"id": cue_id, "start": round(start, 3), "end": round(end, 3), "text": phrase, "accent": accent_index,
                     "accent_at": round(chunk[accent_index]["start"], 3) if accent_index is not None else None})

    animations = []
    for index, cue in enumerate(cues):
        if animation == "kinetic":
            animations.extend(kinetic_animations(cue, index, len(chunks[index])))
            continue
        length = cue["end"] - cue["start"]
        if index % 6 == 2:
            initial = {"x": -14, "y": 4, "scale": 1, "opacity": .68}
        elif index % 6 == 5:
            initial = {"x": 14, "y": 4, "scale": 1, "opacity": .68}
        elif cue["accent"] is not None:
            initial = {"x": 0, "y": 8, "scale": .96, "opacity": .68}
        else:
            initial = {"x": 0, "y": 14, "scale": .98, "opacity": .68}
        landing = {"x": 0, "y": 0, "scale": 1, "opacity": 1, "duration": round(min(.19, length * .42), 3),
                   "ease": "power3.out", "immediateRender": False}
        animations.append(f'    tl.set("#{cue["id"]}", {{autoAlpha:1}}, {max(cue["start"], SHOW_MIN):.3f});')
        animations.append(f'    tl.fromTo("#{cue["id"]} .caption-line", {json.dumps(initial)}, {json.dumps(landing)}, {cue["start"]:.3f});')
        animations.append(f'    tl.set("#{cue["id"]}", {{autoAlpha:0}}, {cue["end"]:.3f});')
        if cue["accent"] is not None and cue["accent_at"] + .24 < cue["end"]:
            at = cue["accent_at"]
            animations.append(f'    tl.fromTo("#{cue["id"]} .accent-word", {{y:0,scale:1}}, '
                              f'{{y:-5,scale:1.065,duration:.105,ease:"power2.out",immediateRender:false}}, {at:.3f});')
            animations.append(f'    tl.to("#{cue["id"]} .accent-word", '
                              f'{{y:0,scale:1,duration:.145,ease:"power2.out",overwrite:"auto"}}, {at + .105:.3f});')
            animations.append(f'    tl.fromTo("#{cue["id"]} .accent-line", {{scaleX:0}}, '
                              f'{{scaleX:1,duration:.18,ease:"power2.out",immediateRender:false}}, {at:.3f});')

    cid = f'{common.CONFIG["id"]}-captions'
    motion_css = ('\n  .word-pop { display:inline-block; position:relative; transform-origin:50% 80%; }'
                  if animation == "kinetic" else "")
    document = f'''<!doctype html>
<html lang="es">
<head><meta charset="utf-8"></head>
<body>
<template>
<style>
  #caption-root {{ position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }}
  .caption-cue {{ position:absolute; left:{box["left"]}px; top:{box["top"]}px; width:{box["width"]}px; height:{box["height"]}px;
    display:flex; align-items:center; justify-content:center; text-align:center; pointer-events:none;
    opacity:0; visibility:hidden; }}
  .caption-line {{ max-width:100%; color:#f8fbfb; font:{weight} {font_size}px/1.12 {font};
    letter-spacing:{tracking}; text-wrap:balance; -webkit-text-stroke:1.7px #07131a;
    paint-order:stroke fill; text-shadow:0 4px 12px #000b; transform-origin:50% 75%; }}{plate_css}
  .caption-word {{ display:inline-block; position:relative; white-space:nowrap; margin:0 .045em;
    transform-origin:50% 80%; }}
  .accent-word {{ color:{accent}; }}
  .accent-line {{ position:absolute; left:4%; right:4%; bottom:-5px; height:3px; border-radius:3px;
    background:{accent}; box-shadow:0 2px 5px {accent_shadow}; transform-origin:left center; }}{motion_css}{chip_css}
</style>
<div id="caption-root" data-composition-id="{cid}" data-width="1080" data-height="1920" data-duration="{duration:.6f}">
{chr(10).join(markup)}
</div>
<script>
  const tl = gsap.timeline({{paused:true}});
  tl.set(".caption-cue", {{autoAlpha:0}}, 0);
{chr(10).join(animations)}
  window.__timelines["{cid}"] = tl;
</script>
</template>
</body>
</html>
'''
    common.p("src").mkdir(exist_ok=True)
    common.p("src/captions.html").write_text(document)
    common.write_json("scripts/caption-cues.json", cues)
    srt = []
    for index, cue in enumerate(cues, 1):
        srt.extend((str(index), f'{timestamp(cue["start"])} --> {timestamp(cue["end"])}', cue["text"], ""))
    common.p("scripts/subtitulos.srt").write_text("\n".join(srt))
    print(f"  {len(cues)} caption phrases from {len(words)} words")
