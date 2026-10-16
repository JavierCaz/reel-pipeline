"""Presenter mattes for "stage" cutout segments: background removal on the source clip, cached.

Runs `hyperframes remove-background` (local u2net human-segmentation model, CPU on this machine)
on each raw clip that a cutout segment uses and writes media/cutouts/<clip stem>.webm (VP9 with
alpha, --quality best). Phone clips stored landscape with a rotation tag are first transcoded
upright into .cache/matte-src/ (the segmentation model finds no person in a sideways frame and
returns an empty matte). Existing mattes are reused; delete one to regenerate it. The original
footage is untouched. Rough speed on this machine: see docs/lessons-learned.md.
"""

from __future__ import annotations

import json
import re
import subprocess
import time

from . import common


def run() -> None:
    cutouts()
    faces()


def cutouts() -> None:
    entries = [e for e in common.CONFIG.get("stage", []) if e.get("mode") == "cutout"]
    if not entries:
        print("  no cutout segments")
        return
    clips = common.read_json("scripts/cut-map.json")["clips"]
    pin = _pin()
    out_dir = common.p("media/cutouts")
    out_dir.mkdir(parents=True, exist_ok=True)
    for n in sorted({e["from"][0] for e in entries}):
        source = clips[n - 1]["source"]
        stem = source.rsplit("/", 1)[-1].rsplit(".", 1)[0]
        target = out_dir / f"{stem}.webm"
        if target.exists():
            print(f"  clip {n}: {target.name} (cached)")
            continue
        began = time.time()
        upright = common.p(f".cache/matte-src/{stem}.mp4")
        upright.parent.mkdir(parents=True, exist_ok=True)
        if not upright.exists():  # ffmpeg applies the rotation tag when transcoding
            # Phone clips are variable frame rate; the matte tool writes frames at the input's *average*
            # rate, so a VFR source gives a matte that drifts behind the footage (ghosted double).
            # A constant 30 fps copy that follows the source timestamps keeps every frame aligned.
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(common.p(source)), "-an", "-vf", f"fps={common.FPS}",
                            "-fps_mode", "cfr", "-c:v", "libx264", "-crf", "10", "-preset", "fast", "-pix_fmt", "yuv420p",
                            str(upright)], check=True)
        subprocess.run([common.npx(), "--yes", pin, "remove-background", str(upright), "-o", str(target),
                        "--quality", "best"], check=True)
        _check(target, common.p(source))
        print(f"  clip {n}: {target.name} in {time.time() - began:.0f} s")


def _duration(path) -> float:
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                                capture_output=True, text=True, check=True).stdout.strip())


def _check(target, source) -> None:
    """Fail loudly on a sideways matte or one whose timing drifts from the footage (both happened
    with phone clips: rotation tag ignored; variable frame rate re-timed)."""
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", str(target)], capture_output=True, text=True, check=True).stdout.strip()
    width, height = (int(v) for v in probe.split(",")[:2])
    if width > height:
        raise SystemExit(f"{target.name} is landscape ({width}x{height}); the source was not upright")
    drift = abs(_duration(target) - _duration(source))
    if drift > 1.5 / common.FPS:
        target.unlink()
        raise SystemExit(f"{target.name} lasts {drift:.3f} s longer/shorter than its source; it would drift out of sync")


def _pin() -> str:
    scripts = json.loads(common.p("package.json").read_text()).get("scripts", {})
    match = re.search(r"hyperframes@[\d.]+", " ".join(scripts.values()))
    return match.group(0) if match else "hyperframes"


def faces() -> None:
    """Face centre for each card/circle/square segment, so the crop is centred on the face.

    Samples three stills per segment, cuts the presenter out with the same model (image mode), and
    takes the face centre as the middle of the head band under the top of the silhouette. Writes
    scripts/stage-focus.json ({"<mode>@<start>": [x, y]} in upright frame px), cached per segment.
    A "focus": [x, y] in a stage entry overrides the measurement.
    """
    from .cut import stage_segments

    clips = common.read_json("scripts/cut-map.json")["clips"]
    segments = [seg for seg in stage_segments(common.CONFIG.get("stage", []), clips)
                if seg["mode"] in ("card", "circle", "square") and "focus" not in seg]
    path = "scripts/stage-focus.json"
    focus = common.read_json(path, {})
    tmp = common.p(".cache/face-probe")
    tmp.mkdir(parents=True, exist_ok=True)
    pin = _pin()
    for seg in segments:
        key = f"{seg['mode']}@{seg['start']:.3f}"
        if key in focus:
            continue
        points = []
        span = seg["end"] - seg["start"]
        for k, t in enumerate((seg["start"] + 0.15 * span, seg["start"] + 0.5 * span, seg["start"] + 0.85 * span)):
            clip = next(c for c in clips if c["timeline_in"] <= t < c["timeline_out"])
            at = clip["source_in"] + (t - clip["timeline_in"])
            still, matte = tmp / f"{k}.jpg", tmp / f"{k}.png"
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", f"{at:.3f}", "-i", str(common.p(clip["source"])),
                            "-frames:v", "1", "-q:v", "2", str(still)], check=True)
            subprocess.run([common.npx(), "--yes", pin, "remove-background", str(still), "-o", str(matte)], check=True,
                           capture_output=True)
            point = _head_centre(matte)
            if point:
                points.append(point)
        if points:
            focus[key] = [round(sum(p[0] for p in points) / len(points)), round(sum(p[1] for p in points) / len(points))]
            print(f"  {key}: face centre {focus[key]} from {len(points)} stills")
    common.write_json(path, focus)


def _head_centre(matte) -> tuple[int, int] | None:
    """Top of the silhouette, then the mean x of the head band and a point ~half a head below the top."""
    w, h = 270, 480  # analyse at quarter resolution (frame is 1080x1920)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(matte), "-vf", f"scale={w}:{h},format=rgba,alphaextract",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"], capture_output=True, check=True).stdout
    rows = [raw[y * w:(y + 1) * w] for y in range(h)]
    top = next((y for y, row in enumerate(rows) if sum(1 for v in row if v > 128) > 8), None)
    if top is None:
        return None
    band = [(x, y) for y in range(top, min(h, top + 75)) for x, v in enumerate(rows[y]) if v > 128]  # ~300 px of head
    cx = sum(x for x, _ in band) / len(band)
    return round(cx * 4), round((top + 55) * 4)  # face centre ≈ 220 px below the top of the hair
