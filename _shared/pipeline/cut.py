"""Steps 2, 3, 4, 7, 8 — assemble index.html from measured boundaries and generated data.

Inputs: .cache/energy-scan.json (boundaries.py), reel.config.json (trim overrides,
transitions, opening, music), and — when present — scripts/camera-moves.json,
scripts/visual-scenes.json, scripts/visual-sfx.json, src/captions.html.
Outputs: index.html, scripts/cut-map.json (authoritative source in/out ↔ timeline),
scripts/hf-ids.json (keeps Studio data-hf-id values stable across regenerations).

Track layout (one element kind per track):
  0 footage · 1–2 clip audio (alternating) · 8 transition SFX · 9 opening SFX
  3 presenter cutouts (alpha video above the graphics) · 11 concept visuals · 12 overlays (end card, above captions)
  19 intro music · 20+ music parts · 30–39 visual SFX lanes · 40 captions

Presenter layouts ("stage"): all footage sits in #presenter, which can shrink into a floating card or
circle, or leave the frame (takeover) over a full-frame #backdrop; "cutout" overlays an alpha matte of
the presenter (media/cutouts/, `build matte`) above the graphics so elements can sit behind them.
"""

from __future__ import annotations

import html
import json
import math
import re

from . import common, presets



def _sound(name):
    """A sound preset; a named preset whose file is missing (optional downloads) falls back to the bundled whoosh."""
    sfx = presets.sound(name)
    if isinstance(name, str) and not common.p(sfx["src"]).exists():
        print(f"  warning: {sfx['src']} not found; using the bundled whoosh (see _shared/sfx/README.md)")
        sfx = presets.sound("whoosh")
    return sfx

def run() -> None:
    cfg = common.CONFIG
    fps = common.FPS
    rid = cfg["id"]
    audio_cfg = cfg.get("audio", {})
    voice_gain = float(audio_cfg.get("voice_volume", 1))
    sfx_gain = float(audio_cfg.get("sfx_volume", 1))
    if not (0 <= voice_gain <= 1 and 0 <= sfx_gain <= 1):
        raise ValueError("audio.voice_volume and audio.sfx_volume must be between 0 and 1")
    scan = common.read_json(".cache/energy-scan.json")
    trim = cfg.get("trim", {})
    pre, post = trim.get("pre_roll", 0.08), trim.get("post_roll", 0.10)
    overrides = trim.get("overrides", {})
    camera = common.read_json("scripts/camera-moves.json", {"clips": {}})["clips"]
    transitions = cfg.get("transitions", [])
    opening = cfg.get("opening", {"shake": True, "sound": "vortex"})

    index_path = common.p("index.html")
    existing_html = index_path.read_text() if index_path.exists() else ""
    hf_ids = common.read_json("scripts/hf-ids.json", {})
    for tag in re.findall(r"<(?:div|video|audio)\b[^>]*>", existing_html):
        element_id = re.search(r'\sid="([^"]+)"', tag)
        hf_id = re.search(r'\sdata-hf-id="([^"]+)"', tag)
        if element_id and hf_id:
            hf_ids[element_id.group(1)] = hf_id.group(1)
    common.write_json("scripts/hf-ids.json", hf_ids)

    def hf(element_id: str) -> str:
        value = hf_ids.get(element_id)
        return f' data-hf-id="{html.escape(value, quote=True)}"' if value else ""

    # --- cut map -------------------------------------------------------------
    cuts = []
    timeline_frame = 0
    for index, source in enumerate(scan, 1):
        source_frames = common.frame_floor(source["duration"])
        # A short handle keeps quiet consonants while removing nonverbal edge audio.
        override = overrides.get(str(index), {})
        in_frame = max(0, common.frame_floor(override.get("source_in", source["first_speech_start"] - pre)))
        out_frame = min(source_frames, common.frame_ceil(override.get("source_out", source["last_speech_end"] + post)))
        if out_frame - in_frame < 15:
            raise ValueError(f"Unsafe range in {source['file']}")
        cuts.append({
            "order": index,
            "source": f"media/raw/{source['file']}",
            "source_duration": source["duration"],
            "source_in": round(in_frame / fps, 6),
            "source_out": round(out_frame / fps, 6),
            "timeline_in": round(timeline_frame / fps, 6),
            "timeline_out": round((timeline_frame + out_frame - in_frame) / fps, 6),
            "duration": round((out_frame - in_frame) / fps, 6),
            "first_strong_speech_start": source["first_speech_start"],
            "last_speech_end": source["last_speech_end"],
            "review": override.get("reason", "energy-based boundary; listen for any clipped soft consonant or retained breath"),
        })
        timeline_frame += out_frame - in_frame
    footage = timeline_frame / fps
    total = footage
    outro_cfg = cfg.get("outro")
    outro = None
    if outro_cfg:
        # The end card's curtain starts just before the last frame of footage and the reel
        # extends by the card's duration (the card covers the frame, so no footage is needed).
        start = round(footage - outro_cfg.get("overlap", 0.6), 3)  # covered (0.54 s) before footage ends
        total = round(common.frame_ceil(start + outro_cfg.get("duration", 4.5)) / fps, 6)
        outro = {"start": start, "duration": round(total - start, 6)}
    common.write_json("scripts/cut-map.json", {
        "order": cfg.get("order_note", "ascending filename timestamp"),
        "source_rule": "all originals remain untouched in media/raw",
        "analysis": f"20 ms RMS windows; 100 ms smoothing; strong speech above {trim.get('strong_db', -16.0)} dB peak; "
                    f"{int(pre * 1000)} ms pre-roll and {int(post * 1000)} ms post-roll; {fps} fps frame alignment",
        "duration": round(total, 6),
        "footage_duration": round(footage, 6),
        **({"outro": outro} if outro else {}),
        "clips": cuts,
    })

    stage = stage_segments(cfg.get("stage", []), cuts)
    cutouts = [seg for seg in stage if seg["mode"] == "cutout"]
    cutout_clips = {seg["clip"] for seg in cutouts}

    # --- footage, clip audio, camera ------------------------------------------
    media = []
    motion = ["    const tl = gsap.timeline({ paused: true });"]
    ascii_grading, ascii_initial, ascii_motion, ascii_scan = ascii_footage(cfg.get("ascii_footage", []), cuts, hf)
    for cut in cuts:
        n = cut["order"]
        source = html.escape(cut["source"], quote=True)
        attrs = (f'data-start="{cut["timeline_in"]:.6f}" data-duration="{cut["duration"]:.6f}" '
                 f'data-media-start="{cut["source_in"]:.6f}"')
        grading = ""
        if n in ascii_grading:
            grading = (f' data-color-grading="{html.escape(json.dumps(ascii_grading[n]), quote=True)}"'
                       f' style="--hf-color-grading-ascii: {ascii_initial.get(n, 0)}"')
        media.append(
            f'    <div{hf(f"handoff-{n:02d}")} id="handoff-{n:02d}" class="transition-shell">\n'
            f'      <div{hf(f"frame-{n:02d}")} id="frame-{n:02d}" class="shot-frame" data-layout-allow-overflow>\n'
            f'        <video{hf(f"shot-{n:02d}")} id="shot-{n:02d}" class="clip footage" src="{source}" {attrs}{grading} '
            'data-track-index="0" muted playsinline></video>\n'
            + ascii_scan.get(n, "") +
            '      </div></div>\n'
            f'    <audio{hf(f"shot-{n:02d}-audio")} id="shot-{n:02d}-audio" src="{source}" {attrs} '
            f'data-track-index="{1 + n % 2}" data-volume="{voice_gain:g}"></audio>')
        treatment = camera.get(str(n))
        if not treatment:
            continue
        initial = dict(treatment["initial"], transformOrigin="50% 50%")
        selector = f"#frame-{n:02d}" + (f", #cutframe-{n:02d}" if n in cutout_clips else "")
        motion.append(f'    tl.set("{selector}", {json.dumps(initial)}, {cut["timeline_in"]:.6f});')
        for move in treatment["moves"]:
            if move["at"] < 0 or move["at"] + move["duration"] > cut["duration"] + 1e-4:
                raise ValueError(f"Camera move exceeds clip {n}; rerun the camera step after a cut change")
            pose = {key: move[key] for key in ("scale", "x", "y", "ease", "duration")}
            pose["immediateRender"] = False
            motion.append(f'    tl.to("{selector}", {json.dumps(pose)}, {cut["timeline_in"] + move["at"]:.6f});')

    # --- opening shake ---------------------------------------------------------
    if opening.get("shake", True):
        poses = presets.OPENING_SHAKE
        keys = ("x", "y", "scale", "rotation")
        motion.append(f'    tl.set("#handoff-01", {json.dumps({k: poses[0][k] for k in keys})}, 0);')
        for previous, pose in zip(poses, poses[1:]):
            if not previous["at"] < pose["at"] < cuts[0]["duration"]:
                raise ValueError("Opening shake keyframes must increase within the first clip")
            motion.append(
                f'    tl.to("#handoff-01", {json.dumps({**{k: pose[k] for k in keys}, "duration": round(pose["at"] - previous["at"], 6), "ease": pose.get("ease", "none"), "overwrite": "auto"})}, '
                f'{previous["at"]:.6f});')

    # --- section transitions (footage-only handoffs) ---------------------------
    kinds = [t["kind"] for t in transitions if t.get("kind") != "hard-cut"]
    for a, b in zip(kinds, kinds[1:]):
        if a == b:
            print(f"  ! neighbouring transitions repeat '{a}'")
    handoff_sfx = []
    n = 0
    for transition in transitions:
        before = transition["before_clip"]
        if not 2 <= before <= len(cuts):
            raise ValueError(f"Invalid section boundary: {before}")
        if transition["kind"] == "hard-cut":
            continue  # a deliberate hard cut; camera-moves gives the scale jump
        if transition["kind"] not in presets.TRANSITIONS:
            raise ValueError(f"Unknown transition kind '{transition['kind']}'")
        n += 1
        seam = cuts[before - 1]["timeline_in"]
        out_pose, in_pose, out_d, in_d = presets.TRANSITIONS[transition["kind"]]
        settled = {"x": 0, "y": 0, "rotation": 0, "scale": 1}
        motion.append(
            f'    tl.fromTo("#handoff-{before - 1:02d}", {json.dumps(settled)}, '
            f'{json.dumps({**out_pose, "duration": out_d, "ease": "power4.in", "immediateRender": False})}, {seam - out_d:.6f});')
        motion.append(
            f'    tl.fromTo("#handoff-{before:02d}", {json.dumps(in_pose)}, '
            f'{json.dumps({**settled, "duration": in_d, "ease": "power4.out", "immediateRender": False})}, {seam:.6f});')
        sound = transition.get("sound", presets.KIND_SOUND[transition["kind"]])
        if sound:
            sfx = _sound(sound)
            handoff_sfx.append((f"transition-sfx-{n:02d}", sfx, max(0.0, seam - sfx["peak"]), 8))
    motion.extend(ascii_motion)
    stage_html, stage_css = stage_layers(stage, cuts, motion, hf)
    motion.append(f'    window.__timelines["{rid}-rough-cut"] = tl;')
    if opening.get("sound"):
        sfx = _sound(opening["sound"])
        handoff_sfx.insert(0, ("opening-sfx", sfx, sfx.get("start", 0.0), 9))
    transition_audio = [
        f'    <audio{hf(eid)} id="{eid}" src="{sfx["src"]}" data-start="{start:.6f}" '
        f'data-duration="{sfx["duration"]:.6f}" data-media-start="{sfx.get("media_start", 0):.6f}" '
        f'data-track-index="{track}" data-volume="{sfx["volume"] * sfx_gain}"></audio>'
        for eid, sfx, start, track in handoff_sfx]

    # --- captions and concept visuals ------------------------------------------
    caption_host = ""
    if common.p("src/captions.html").exists():
        caption_host = (
            f'    <div{hf("captions-host")} id="captions-host" class="clip" '
            f'data-composition-id="{rid}-captions" data-composition-src="src/captions.html" '
            f'data-start="0" data-duration="{total:.6f}" data-track-index="40" '
            'data-track-kind="captions" data-width="1080" data-height="1920"></div>')
    visual_hosts = [
        f'    <div{hf(scene["id"] + "-host")} id="{scene["id"]}-host" class="clip '
        f'{"overlay-host" if scene.get("layer") == "overlay" else "visual-host"}" '
        f'data-composition-id="{scene["id"]}" data-composition-src="{scene["src"]}" '
        f'data-start="{scene["start"]:.6f}" data-duration="{scene["duration"]:.6f}" data-track-index="{scene.get("track", 11)}" '
        'data-track-kind="graphics" data-width="1080" data-height="1920"></div>'
        for scene in common.read_json("scripts/visual-scenes.json", [])]
    sfx_audio = [
        f'    <audio{hf(cue["id"])} id="{cue["id"]}" src="{cue["src"]}" data-start="{cue["start"]:.6f}" '
        f'data-duration="{cue["duration"]:.6f}" data-track-index="{cue["track"]}" data-volume="{cue["volume"] * sfx_gain}"></audio>'
        for cue in common.read_json("scripts/visual-sfx.json", [])]

    # --- background music: unedited, restarts from its beginning, last part fades -
    music_audio = []
    music = cfg.get("music")
    if music and music.get("preset") == "none":
        music = None
    if music:
        base = presets.MUSIC.get(music.get("preset", ""), {})
        music = {**base, **music}
        if not common.p(music["src"]).exists():
            print(f"  warning: {music['src']} not found; the reel has no music (see _shared/music/README.md)")
            music = None
    if music:
        start, part = 0.0, 1

        def lane(points):
            return html.escape(json.dumps({"version": 1, "lanes": [{"target": "volume", "points": points}]}), quote=True)
        intro = music.get("intro")
        if intro:
            # A separate hook track under the intro section, crossfading into the main bed at the
            # first footage transition (or at an explicit "until" time in seconds).
            until = intro.get("until", "first_transition")
            if until == "first_transition":
                seams = [cuts[t["before_clip"] - 1]["timeline_in"] for t in transitions if t["kind"] != "hard-cut"]
                until = seams[0] if seams else cuts[0]["timeline_out"]
            cross = intro.get("crossfade", 0.8)
            end = min(total, until + cross / 2, intro.get("audible_length", 1e9))
            vol = intro["volume"]
            music_audio.append(
                f'    <audio{hf("music-intro")} id="music-intro" src="{intro["src"]}" data-start="0.000000" '
                f'data-duration="{end:.6f}" data-media-start="{intro.get("media_start", 0):.6f}" data-track-index="19" '
                f'data-automation="{lane([{"t": 0, "v": vol}, {"t": round(end - cross, 3), "v": vol}, {"t": round(end, 3), "v": 0}])}"></audio>')
            start = max(0.0, end - cross)
        while start < total - 1e-6:
            length = min(music["audible_length"], total - start)
            points = [{"t": 0, "v": music["volume"]}]
            if intro and part == 1:
                points = [{"t": 0, "v": 0}, {"t": intro.get("crossfade", 0.8), "v": music["volume"]}]
            if start + length >= total - 1e-6:
                points += [{"t": round(length - music.get("fade_out", 1.2), 3), "v": music["volume"]}, {"t": round(length, 3), "v": 0}]
            automation = lane(points)
            eid = f"music-{part:02d}"
            music_audio.append(
                f'    <audio{hf(eid)} id="{eid}" src="{music["src"]}" data-start="{start:.6f}" '
                f'data-duration="{length:.6f}" data-media-start="0" data-track-index="{19 + part}" data-automation="{automation}"></audio>')
            start += length
            part += 1

    document = f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=1080,height=1920">
  <title>{html.escape(cfg.get("title", rid))} — reel</title>
  <script src="https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"></script>
  <style>
    * {{ box-sizing: border-box; }}
    html, body {{ margin: 0; width: 100%; height: 100%; background: #000; overflow: hidden; }}
    #root {{ position: relative; width: 100%; height: 100%; overflow: hidden; background: #000; }}
    .transition-shell {{ position: absolute; inset: 0; width: 100%; height: 100%; overflow: hidden; transform-origin: 50% 50%; }}
    .shot-frame {{ position: absolute; inset: 0; width: 100%; height: 100%; transform-origin: 50% 50%; }}
    video.footage {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; }}
    #captions-host {{ position: absolute; inset: 0; width: 100%; height: 100%; z-index: 20; pointer-events: none; }}
    .visual-host {{ position: absolute; inset: 0; width: 100%; height: 100%; z-index: 15; pointer-events: none; }}
    .overlay-host {{ position: absolute; inset: 0; width: 100%; height: 100%; z-index: 30; pointer-events: none; }}
{stage_css}  </style>
</head>
<body>
  <div{hf("root")} id="root" data-composition-id="{rid}-rough-cut" data-start="0" data-width="1080" data-height="1920" data-duration="{total:.6f}">
{stage_html["before"]}{chr(10).join(media)}
{stage_html["after"]}{chr(10).join(visual_hosts)}
{chr(10).join(music_audio)}
{chr(10).join(transition_audio)}
{chr(10).join(sfx_audio)}
{caption_host}
  </div>
  <script>
{chr(10).join(motion)}
  </script>
</body>
</html>
"""
    index_path.write_text(document)
    print(f"  {len(cuts)} clips, {total:.3f} s → index.html, scripts/cut-map.json")


# --- presenter layouts ---------------------------------------------------------------
# Channel-sync interference for ascii_footage scans (fractions of the sweep).
# Slivers: (delay, duration factor, height px, horizontal shift px) — thin ASCII slices out of register.
SCAN_SLIVERS = ((0.10, 0.75, 18, 14), (0.28, 1.15, 10, -18), (0.18, 0.95, 26, 8))
# Lines: (delay, duration factor, height px, opacity, start offset px) — thin flickering scan lines.
SCAN_LINES = ((0.00, 0.70, 2, 0.85, -60), (0.06, 0.85, 1, 0.6, -140), (0.14, 1.15, 3, 0.7, -20), (0.04, 1.35, 1, 0.5, -220),
              (0.20, 0.95, 2, 0.75, -90), (0.30, 1.25, 1, 0.55, -30), (0.12, 0.60, 1, 0.65, -180), (0.25, 1.05, 2, 0.6, -110))


def ascii_footage(entries: list, cuts: list, hf=lambda element_id: "") -> tuple[dict, dict, list, dict]:
    """Config "ascii_footage": moments where the presenter footage turns into an ASCII glyph field
    (HyperFrames' procedural ASCII shader, `data-color-grading` on the clip's <video>), stepping in and
    back out through the animatable `--hf-color-grading-ascii` value (0 = untouched footage).
    Entry: {"from": [clip, word] or [clip], "to": [clip, word] or [clip], "from_clip_start", "to_clip_end",
    "length" (s from the start, instead of a "to" word), "lead", "tail", "ramp_in", "ramp_out" (s; 0 = none),
    "steps", "size", "invert", "color", "palette"}. A moment that starts at its clip's first frame with
    ramp_in 0 starts fully ASCII (inline initial value: a "tune in"); ramp_out 0 with to_clip_end holds it
    to the clip's last frame (a "tune out"). Defaults: lime glyphs on the theme surface (palette
    [surface bg, primary]), size 0.05, colour from the palette (color 0), ramps 0.3 s in 6 steps.
    mode "scan": instead of treating the whole clip, a horizontal band of ASCII glyphs sweeps over the
    footage once (a second, ASCII-treated copy of the clip seen through a moving window, with a lime scan
    line on its leading edge); the rest stays untouched. Keys: "band" (px, default 300), "sweep" (s, default
    1.2), "direction" ("down" | "up"), "from_y"/"to_y" (band top at the start/end, px; default off-frame to off-frame), "lines" (thin flickering
    scan lines, up to 8) and "slivers" (thin ASCII slices out of horizontal register, up to 3): channel-sync interference, plus from/lead and the look keys above. Lives inside the clip's
    frame, so it follows camera motion.
    Returns ({clip: grading}, {clip: initial value}, timeline lines, {clip: extra frame HTML}).
    Clips without an entry are unchanged."""
    words = common.read_json("scripts/transcript.json", [])
    if not entries or not words:
        return {}, {}, [], {}
    theme = presets.theme(common.CONFIG)
    palette = [theme.get("surface", {}).get("bg", "#000000"), theme["palette"]["primary"]]

    def find(clip, text, edge):
        for word in words:
            if word.get("clip") == clip and word["text"] == text:
                return word[edge]
        raise ValueError(f"ascii_footage: word {text!r} not found in clip {clip}")

    grading, initial, lines, spans, scans = {}, {}, [], [], {}
    for entry in entries:
        if entry.get("mode") == "scan":
            n = entry["from"][0]
            cut = cuts[n - 1]
            if entry.get("from_clip_start") or len(entry["from"]) < 2:
                start = round(cut["timeline_in"] + entry.get("lead", 0.0), 3)
            else:
                start = round(max(cut["timeline_in"], find(n, entry["from"][1], "start") - entry.get("lead", 0.1)), 3)
            band, sweep = entry.get("band", 300), entry.get("sweep", 1.2)
            if start + sweep > cut["timeline_out"] + 1e-3:
                raise ValueError(f"ascii_footage: scan {entry} runs past clip {n}")
            if n in scans:
                raise ValueError(f"ascii_footage: clip {n} has two scans")
            g = {"effects": {"ascii": 1, "asciiSize": entry.get("size", 0.05), "asciiInvert": entry.get("invert", 0),
                             "asciiColor": entry.get("color", 0)},
                 "palette": entry.get("palette", palette)}
            down = entry.get("direction", "down") == "down"
            y0, y1 = (-band, 1920) if down else (1920, -band)
            y0, y1 = entry.get("from_y", y0), entry.get("to_y", y1)   # e.g. start under an overlay that covers the top
            ease = entry.get("ease", "power1.inOut")
            color = palette[1] if "palette" not in entry else entry["palette"][-1]
            out = []

            def ascii_window(wid, height, t0, dur, ty0, ty1, track, x_shift=0, edge=None, wease=ease):
                """A moving window onto an ASCII-treated copy of the clip: the outer div travels, the inner
                one travels back so the copy stays registered with the footage (x_shift: lost h-sync)."""
                at_media = cut["source_in"] + (t0 - cut["timeline_in"])
                edge_html = (f'          <div style="position:absolute;left:0;{edge};width:1080px;height:4px;background:{color};'
                             f'box-shadow:0 0 18px {color},0 0 44px {color}"></div>\n') if edge else ""
                out.append(
                    f'        <div{hf(wid)} id="{wid}" class="ascii-scan" style="position:absolute;left:0;top:0;width:1080px;height:{height}px;'
                    f'overflow:hidden;pointer-events:none;transform:translateY({ty0}px)">\n'
                    f'          <div{hf(wid + "-in")} id="{wid}-in" style="position:absolute;left:{x_shift}px;top:0;width:1080px;height:1920px;'
                    f'transform:translateY({-ty0}px)">\n'
                    f'            <video{hf(wid + "-video")} id="{wid}-video" class="clip footage" src="{html.escape(cut["source"], quote=True)}" '
                    f'data-start="{t0:.6f}" data-duration="{dur + 0.1:.6f}" data-media-start="{at_media:.6f}" '
                    f'data-color-grading="{html.escape(json.dumps(g), quote=True)}" style="--hf-color-grading-ascii: 1" '
                    f'data-track-index="{track}" muted playsinline></video>\n'
                    f'          </div>\n{edge_html}        </div>\n')
                lines.append(f'    tl.fromTo("#{wid}", {{"y": {ty0}}}, {{"y": {ty1}, "duration": {dur}, "ease": "{wease}", "immediateRender": false}}, {t0:.3f});')
                lines.append(f'    tl.fromTo("#{wid}-in", {{"y": {-ty0}}}, {{"y": {-ty1}, "duration": {dur}, "ease": "{wease}", "immediateRender": false}}, {t0:.3f});')

            sid = f"scan-{n:02d}"
            ascii_window(sid, band, start, sweep, y0, y1, 4, edge=f"top:{band - 3}px" if down else "top:-1px")
            # Channel-sync interference: thin ASCII slivers out of horizontal register and thin flickering
            # scan lines, each at its own delay and speed (fixed patterns: deterministic).
            span = y1 - y0
            for k, (delay, factor, height, shift) in enumerate(SCAN_SLIVERS[:entry.get("slivers", 0)]):
                t0 = round(start + delay * sweep, 3)
                dur = round(sweep * factor, 3)
                if t0 + dur > cut["timeline_out"]:
                    continue
                ascii_window(f"{sid}-s{k}", height, t0, dur, y0 + band * 0.5, y1, 5 + k, x_shift=shift, wease="none")
            for k, (delay, factor, height, alpha, offset) in enumerate(SCAN_LINES[:entry.get("lines", 0)]):
                lid = f"{sid}-l{k}"
                t0 = round(start + delay * sweep, 3)
                dur = round(sweep * factor, 3)
                ly0 = y0 + band + offset if down else y0 - offset
                ly1 = y1 + band if down else y1
                out.append(f'        <div{hf(lid)} id="{lid}" style="position:absolute;left:0;top:0;width:1080px;height:{height}px;'
                           f'background:{color};opacity:0;box-shadow:0 0 {6 + height * 4}px {color};pointer-events:none;'
                           f'transform:translateY({ly0}px)"></div>\n')
                lines.append(f'    tl.fromTo("#{lid}", {{"y": {ly0}}}, {{"y": {ly1}, "duration": {dur}, "ease": "none", "immediateRender": false}}, {t0:.3f});')
                lines.append(f'    tl.set("#{lid}", {{"opacity": {alpha}}}, {t0:.3f});')
                flick = 0.06 + (k % 3) * 0.025
                reps = int(dur / flick) - 1
                reps -= 0 if reps % 2 else 1
                if reps >= 1:
                    lines.append(f'    tl.fromTo("#{lid}", {{"opacity": {alpha}}}, {{"opacity": {round(alpha * 0.2, 2)}, "duration": {flick:.3f}, '
                                 f'"ease": "steps(1)", "repeat": {reps}, "yoyo": true, "immediateRender": false}}, {t0 + 0.001:.3f});')
                lines.append(f'    tl.set("#{lid}", {{"opacity": 0}}, {t0 + dur:.3f});')
            scans[n] = "".join(out)
            continue
        c1, c2 = entry["from"][0], entry.get("to", entry["from"])[0]
        if entry.get("from_clip_start"):
            start = round(cuts[c1 - 1]["timeline_in"] + entry.get("lead", 0.0), 3)
        else:
            start = round(max(cuts[c1 - 1]["timeline_in"], find(c1, entry["from"][1], "start") - entry.get("lead", 0.1)), 3)
        if "length" in entry:
            end = round(start + entry["length"], 3)
        elif entry.get("to_clip_end"):
            end = round(cuts[c2 - 1]["timeline_out"], 3)
        else:
            end = round(min(cuts[c2 - 1]["timeline_out"], find(c2, entry["to"][1], "end") + entry.get("tail", 0.1)), 3)
        end = min(end, round(cuts[c2 - 1]["timeline_out"], 3))
        ramp = entry.get("ramp", 0.3)
        ramp_in, ramp_out = entry.get("ramp_in", ramp), entry.get("ramp_out", ramp)
        ease = f'steps({entry.get("steps", 6)})'
        if end - start < ramp_in + ramp_out + 0.1:
            raise ValueError(f"ascii_footage: {entry} is too short for its ramps")
        if any(start < b and a < end for a, b in spans):
            raise ValueError(f"ascii_footage: {entry} overlaps another moment")
        spans.append((start, end))
        g = {"effects": {"ascii": 1, "asciiSize": entry.get("size", 0.05), "asciiInvert": entry.get("invert", 0),
                         "asciiColor": entry.get("color", 0)},
             "palette": entry.get("palette", palette)}
        for n in range(c1, c2 + 1):
            if grading.setdefault(n, g) != g:
                raise ValueError(f"ascii_footage: clip {n} has two different ASCII settings")
            cut = cuts[n - 1]
            # The value is a CSS property on each <video>; every clip in the span ramps in step.
            on, off = max(start, cut["timeline_in"]), min(end, cut["timeline_out"])
            sel = f"#shot-{n:02d}"
            if on - cut["timeline_in"] < 1e-3 and (ramp_in == 0 or on - start > 1e-3):
                initial[n] = 1  # fully ASCII from the clip's first frame (authored inline, not a frame-zero set)
            elif on - start < 1e-3 and ramp_in > 0:
                lines.append(f'    tl.fromTo("{sel}", {{"--hf-color-grading-ascii": 0}}, {{"--hf-color-grading-ascii": 1, '
                             f'"duration": {ramp_in}, "ease": "{ease}", "immediateRender": false}}, {start:.3f});')
            else:
                lines.append(f'    tl.set("{sel}", {{"--hf-color-grading-ascii": 1}}, {on:.3f});')
            if end - off < 1e-3 and ramp_out > 0:
                lines.append(f'    tl.fromTo("{sel}", {{"--hf-color-grading-ascii": 1}}, {{"--hf-color-grading-ascii": 0, '
                             f'"duration": {ramp_out}, "ease": "{ease}", "immediateRender": false}}, {end - ramp_out:.3f});')
    return grading, initial, lines, scans


def stage_segments(entries: list, cuts: list) -> list[dict]:
    """Resolve "stage" entries ({"from": [clip, word], "to": [clip, word], "mode"}) to cut-timeline times.
    Words match transcript.json exactly (as for camera beats). Without a transcript yet, returns []."""
    words = common.read_json("scripts/transcript.json", [])
    if not entries or not words:
        return []

    def find(clip, text, edge):
        for word in words:
            if word.get("clip") == clip and word["text"] == text:
                return word[edge]
        raise ValueError(f"stage: word {text!r} not found in clip {clip}")

    segments = []
    for entry in entries:
        mode = entry["mode"]
        if mode != "cutout" and mode not in presets.STAGE:
            raise ValueError(f"stage: unknown mode {mode!r}; use square, card, circle, takeover, cutout")
        (c1, w1), (c2, w2) = entry["from"], entry["to"]
        start = round(max(cuts[c1 - 1]["timeline_in"], find(c1, w1, "start") - entry.get("lead", 0.2)), 3)
        end = round(min(cuts[c2 - 1]["timeline_out"], find(c2, w2, "end") + entry.get("tail", 0.15)), 3)
        if entry.get("from_clip_start"):
            start = round(cuts[c1 - 1]["timeline_in"] + entry.get("lead", 0.0), 3)
        if entry.get("to_clip_end"):
            end = round(cuts[c2 - 1]["timeline_out"], 3)
        if end - start < 1.0:
            raise ValueError(f"stage: segment {entry} is shorter than 1 s")
        if mode == "cutout" and c1 != c2:
            raise ValueError("stage: a cutout segment must stay inside one clip")
        segments.append({**entry, "mode": mode, "start": start, "end": end, "clip": c1})
    segments.sort(key=lambda seg: seg["start"])
    layouts = [seg for seg in segments if seg["mode"] != "cutout"]
    for a, b in zip(layouts, layouts[1:]):
        if b["start"] < a["end"] - 1e-3:
            raise ValueError(f"stage: segments overlap at {b['start']}")
    return segments


def _rgba(hex_color: str, alpha: float) -> str:
    h = hex_color.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


def _crop_numbers(x, y, w, h, r) -> list[float]:
    return [round(y, 2), round(1080 - x - w, 2), round(1920 - y - h, 2), round(x, 2), round(r, 2)]


def _filter(ring: float, off: float, ring_color: str, shadow: str) -> str:
    """Accent ring (four hard drop-shadows around the cropped shape) plus the hard offset shadow.
    The same five functions at every pose, so the filter interpolates."""
    rings = " ".join(f"drop-shadow({dx * ring:.2f}px {dy * ring:.2f}px 0px {ring_color})"
                     for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
    return f"{rings} drop-shadow({off:.2f}px {off:.2f}px 0px {shadow})"


def _pose(mode: str, region=None, colors=("#000", "#000")) -> dict:
    """Layout pose: #presenter transform + filter (ring and shadow) and the media crop. The crop is in
    frame pixels; ring and shadow are divided by the scale so they land at a constant screen size.
    Full frame is the same shapes at identity values, so every property tweens."""
    ring_color, shadow = colors
    if mode == "full":
        return {"move": {"x": 0, "y": 0, "scale": 1, "opacity": 1, "filter": _filter(0, 0, ring_color, shadow)},
                "crop": _crop_numbers(0, 0, 1080, 1920, 0)}
    g = presets.STAGE[mode]
    region = g["region"] if region is None else region
    if (not isinstance(region, (list, tuple)) or len(region) != 4
            or any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v)
                   for v in region)):
        raise ValueError("stage: region must be [x, y, width, height] in 1080×1920 frame pixels")
    rx, ry, rw, rh = region
    if rx < 0 or ry < 0 or rw <= 0 or rh <= 0 or rx + rw > 1080 or ry + rh > 1920:
        raise ValueError("stage: region must fit inside the 1080×1920 frame")
    if g["round"] and rw != rh:
        raise ValueError("stage: circle/takeover region must be square")
    tx, ty, tw = g["target"]
    k = tw / rw
    radius = rw / 2 if g["round"] else 0
    return {"move": {"x": round(tx - rx * k, 2), "y": round(ty - ry * k, 2), "scale": round(k, 5),
                     "opacity": 0 if g.get("hidden") else 1,
                     "filter": _filter(presets.STAGE_RING / k, presets.STAGE_SHADOW / k, ring_color, shadow)},
            "crop": _crop_numbers(rx, ry, rw, rh, radius)}


def _focus_region(mode: str, focus) -> list[int]:
    """The preset region shifted so the face centre lands where the preset assumes it (presets.STAGE
    "focus"), clamped inside the frame."""
    g = presets.STAGE[mode]
    rx, ry, rw, rh = g["region"]
    fx, fy = g.get("focus", (rx + rw / 2, ry + rh / 2))
    x = round(min(max(0, rx + focus[0] - fx), 1080 - rw))
    y = round(min(max(0, ry + focus[1] - fy), 1920 - rh))
    return [x, y, rw, rh]


def stage_layers(stage: list, cuts: list, motion: list, hf) -> tuple[dict, str]:
    """Wrap the footage in #presenter, add the backdrop/frame/cutout layers, and append the layout tweens."""
    if not stage:
        return {"before": "", "after": ""}, ""  # no layouts: index.html stays byte-identical
    theme = presets.theme(common.CONFIG)
    pal = {**theme["palette"], **common.CONFIG.get("visuals", {}).get("palette", {})}
    surface = theme.get("surface", {})
    bg = surface.get("bg", pal["paper"])
    minor, major = surface.get("grid_minor", pal["soft"]), surface.get("grid_major", pal["soft"])
    shadow = surface.get("shadow", pal["ink"])
    grid = common.CONFIG.get("visuals", {}).get("grid", 32)
    css = f"""    #presenter {{ position: absolute; inset: 0; width: 100%; height: 100%; z-index: 10; transform-origin: 0 0; }}
    #presenter-body {{ position: absolute; inset: 0; transform-origin: 50% 50%; }}

    #presenter-media {{ position: absolute; inset: 0; overflow: hidden; }}
    #backdrop {{ position: absolute; inset: 0; width: 100%; height: 100%; z-index: 5; opacity: 0;
      background: linear-gradient({major} 2px,transparent 2px) -1px -1px/{grid * 4}px {grid * 4}px,
        linear-gradient(90deg,{major} 2px,transparent 2px) -1px -1px/{grid * 4}px {grid * 4}px,
        linear-gradient({minor} 1px,transparent 1px) -1px -1px/{grid}px {grid}px,
        linear-gradient(90deg,{minor} 1px,transparent 1px) -1px -1px/{grid}px {grid}px, {bg}; }}
    .cutout-shell {{ z-index: 17; pointer-events: none; }}
"""
    before = (f'  <div{hf("backdrop")} id="backdrop"></div>\n'
              f'  <div{hf("presenter")} id="presenter"><div{hf("presenter-body")} id="presenter-body">'
              f'<div{hf("presenter-media")} id="presenter-media">\n')
    # #presenter carries transform + filter (ring, shadow); #presenter-media carries the crop.
    after = ["  </div></div></div>"]

    # Cutouts: the presenter's alpha matte, on the same camera moves, above the graphics.
    cutout_fx = []
    if any(seg["mode"] == "cutout" for seg in stage):  # the background wash exists only for cutouts
        css += (f"    #cutout-wash {{{{ position: absolute; inset: 0; z-index: 12; opacity: 0; pointer-events: none;\n"
                f"      background: linear-gradient(180deg, {_rgba(bg, .62)} 0%, {_rgba(bg, .34)} 38%, {_rgba(bg, 0)} 58%, "
                f"{_rgba(pal['ink'], .38)} 100%); }}}}\n").replace("{{", "{").replace("}}", "}")
        before = f'  <div{hf("cutout-wash")} id="cutout-wash"></div>\n' + before
    for seg in (seg for seg in stage if seg["mode"] == "cutout"):
        cut = cuts[seg["clip"] - 1]
        n = cut["order"]
        stem = cut["source"].rsplit("/", 1)[-1].rsplit(".", 1)[0]
        matte = f"media/cutouts/{stem}.webm"
        if not common.p(matte).exists():
            raise SystemExit(f"Missing {matte}; run `npm run build -- matte` first")
        start, end = seg["start"], seg["end"]
        transitions = {t["before_clip"] for t in common.CONFIG.get("transitions", []) if t["kind"] != "hard-cut"}
        if (n in transitions and start < cut["timeline_in"] + 0.4) or (n + 1 in transitions and end > cut["timeline_out"] - 0.35):
            raise ValueError(f"stage: cutout in clip {n} must stay clear of its footage transitions")
        media_start = cut["source_in"] + (start - cut["timeline_in"])
        # Background treatment: blur + dim the room and fade in the wash; both clear before the matte
        # ends so a blurred copy of the presenter is never left without the sharp one on top.
        bgc = presets.CUTOUT_BACKGROUND
        sharp = {"filter": "blur(0px) brightness(1)", "scale": 1}
        soft = {"filter": f"blur({bgc['blur']}px) brightness({bgc['brightness']})", "scale": bgc["scale"]}
        clear_at = round(end - bgc["out"], 3)
        cutout_fx.append(f'    tl.fromTo("#presenter-body", {json.dumps(sharp)}, {json.dumps({**soft, "duration": bgc["in"], "ease": "power2.out", "immediateRender": False})}, {start:.3f});')
        cutout_fx.append(f'    tl.fromTo("#presenter-body", {json.dumps(soft)}, {json.dumps({**sharp, "duration": bgc["out"], "ease": "power2.in", "immediateRender": False})}, {clear_at:.3f});')
        cutout_fx.append(f'    tl.fromTo("#cutout-wash", {{"opacity": 0}}, {{"opacity": 1, "duration": {bgc["in"]}, "ease": "power2.out", "immediateRender": false}}, {start:.3f});')
        cutout_fx.append(f'    tl.fromTo("#cutout-wash", {{"opacity": 1}}, {{"opacity": 0, "duration": {bgc["out"]}, "ease": "power2.in", "immediateRender": false}}, {clear_at:.3f});')
        after.append(
            f'  <div{hf(f"cutshell-{n:02d}")} id="cutshell-{n:02d}" class="transition-shell cutout-shell">'
            f'<div{hf(f"cutframe-{n:02d}")} id="cutframe-{n:02d}" class="shot-frame" data-layout-allow-overflow>'
            f'<video{hf(f"cutout-{n:02d}")} id="cutout-{n:02d}" class="clip footage" src="{matte}" '
            f'data-start="{start:.6f}" data-duration="{end - start:.6f}" data-media-start="{media_start:.6f}" '
            f'data-track-index="3" muted playsinline></video></div></div>')

    # Layouts: tween #presenter (transform + clip-path), its frame, and the backdrop between modes.
    d = presets.STAGE_MOVE
    layouts = [seg for seg in stage if seg["mode"] != "cutout"]
    measured = common.read_json("scripts/stage-focus.json", {})  # face centres from the matte step
    changes = []
    for i, seg in enumerate(layouts):
        region = seg.get("region")  # an explicit region wins; otherwise centre the preset on the face
        focus = seg.get("focus") or measured.get(f"{seg['mode']}@{seg['start']:.3f}")
        if region is None and focus and seg["mode"] in ("card", "circle", "square"):
            region = _focus_region(seg["mode"], focus)
        changes.append((seg["start"], seg["mode"], region))
        nxt = layouts[i + 1] if i + 1 < len(layouts) else None
        if not nxt or nxt["start"] - seg["end"] > 0.6:
            changes.append((round(seg["end"] - d, 3), "full", None))
    # Shrinking: the crop leads (corners round off), then the presenter scales and travels with its
    # ring and shadow (both in the filter, so they follow the shape at every frame). Growing back: the move leads, then the crop opens. The backdrop eases in and out.
    colors = (pal["primary"], shadow)
    full = _pose("full", None, colors)

    motion.append(f'    tl.set("#presenter", {json.dumps({"filter": full["move"]["filter"]})}, 0);')
    scenes_on_track = [sc for sc in common.read_json("scripts/visual-scenes.json", []) if sc.get("layer", "graphics") == "graphics"]
    previous_pose = full
    crops = []
    previous = "full"
    for at, mode, region in changes:
        pose = _pose(mode, region, colors)
        growing = mode == "full"
        crop_at, move_at = (at + d * 0.3, at) if growing else (at, at + d * 0.15)
        crop = {"duration": round(d * 0.7, 3), "ease": "power2.inOut", "immediateRender": False}
        move = {**pose["move"], "duration": round(d * 0.85, 3), "ease": "power3.inOut", "immediateRender": False}
        crops.append({"at": round(crop_at, 3), "d": crop["duration"], "ease": crop["ease"],
                      "a": previous_pose["crop"], "b": pose["crop"]})
        motion.append(f'    tl.fromTo("#presenter", {json.dumps({"filter": previous_pose["move"]["filter"]})}, '
                      f'{json.dumps(move)}, {move_at:.3f});')
        if previous == "full":
            motion.append(f'    tl.to("#backdrop", {{"opacity": 1, "duration": 0.4, "ease": "power1.out", "immediateRender": false}}, {at:.3f});')
        if growing:
            motion.append(f'    tl.to("#backdrop", {{"opacity": 0, "duration": 0.3, "ease": "power1.in", "immediateRender": false}}, {at + d - 0.3:.3f});')
            # Growing back, the presenter passes over the layout's graphics (z 16 > visuals 15, < captions 20)
            # until that scene has ended, so its cards never sit in front of the face (SitioWeb, 2026-10-08).
            ends = [sc["start"] + sc["duration"] for sc in scenes_on_track if sc["start"] <= at < sc["start"] + sc["duration"]]
            motion.append(f'    tl.set("#presenter", {{"zIndex": 16}}, {at:.3f});')
            motion.append(f'    tl.set("#presenter", {{"zIndex": 10}}, {max([at + d] + ends):.3f});')
        previous, previous_pose = mode, pose
    motion.extend(cutout_fx)
    # The crop is computed from the playhead by one reel-long driver tween: GSAP's own clip-path
    # interpolation did not render mid-tween in this timeline (2026-10-06), and a pure function of
    # time stays seek-safe for the renderer.
    span = round(cuts[-1]["timeline_out"], 3)
    motion.append(f"""    const presenterCrops = {json.dumps(crops)};
    const presenterMedia = document.getElementById("presenter-media");
    const cropDriver = {{ t: 0 }};
    tl.fromTo(cropDriver, {{ t: 0 }}, {{ t: {span}, duration: {span}, ease: "none", immediateRender: true, onUpdate() {{
      const t = cropDriver.t;
      let v = {json.dumps(full["crop"])};
      for (const c of presenterCrops) {{
        if (t < c.at) break;
        const p = Math.min(1, (t - c.at) / c.d), k = gsap.parseEase(c.ease)(p);
        v = c.a.map((x, i) => x + (c.b[i] - x) * k);
      }}
      presenterMedia.style.clipPath = `inset(${{v[0]}}px ${{v[1]}}px ${{v[2]}}px ${{v[3]}}px round ${{v[4]}}px)`;
    }} }}, 0);""")
    if stage:
        common.write_json("scripts/stage.json", [{k: seg[k] for k in ("mode", "start", "end", "clip")} for seg in stage])
    return {"before": before, "after": "\n".join(after) + "\n"}, css
