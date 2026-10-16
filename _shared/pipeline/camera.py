"""Step 3 — plan per-clip digital camera motion from emphasis words.

reel.config.json "camera": {"<clip>": {"reason": "...", "beats": [["word", "kind"], ...],
                                       "initial_scale": 1.02 (optional)}}
kind: hit (priority line, ~+0.10) | punch (~+0.065) | push (slow +0.035) | pull (-0.06) | step (lateral)
The word is matched exactly as it appears in transcript.json for that clip (punctuation included).
Clips without an entry still drift. Writes scripts/camera-moves.json (times relative to each clip).
Scale stays within 1.02-1.14 and offsets inside the cropped margin, so frame edges never show.
"""

from __future__ import annotations

from . import common

LO, HI = 1.02, 1.14
LEAD = {"hit": 0.1, "punch": 0.1, "push": 0.15, "pull": 0.1, "step": 0.06}


def clamp_pose(scale, x, y):
    scale = round(min(HI, max(LO, scale)), 3)
    limit_x = (scale - 1) * 540 * 0.7
    limit_y = (scale - 1) * 960 * 0.4
    return scale, round(max(-limit_x, min(limit_x, x)), 1), round(max(-limit_y, min(limit_y, y)), 1)


def plan_clip(n, cut, words, entry):
    duration = cut["duration"]
    side = 1 if n % 2 else -1
    scale = entry.get("initial_scale", 1.03 if n % 3 else 1.07)
    initial = dict(zip(("scale", "x", "y"), clamp_pose(scale, 0.0, 0.0)))
    state = {"scale": initial["scale"], "x": initial["x"], "y": initial["y"], "cursor": 0.08}
    moves = []

    def add(at, length, new_scale, new_x, new_y, ease):
        at = max(at, state["cursor"])
        length = min(length, duration - 0.02 - at)
        if length < 0.12:
            return
        s, x, y = clamp_pose(new_scale, new_x, new_y)
        state.update(scale=s, x=x, y=y, cursor=at + length + 0.02)
        moves.append({"at": round(at, 3), "duration": round(length, 3), "scale": s, "x": x, "y": y, "ease": ease})

    previous = None
    for text, kind in entry.get("beats", []):
        word = next((w for w in words if w["clip"] == n and w["text"] == text), None)
        if word is None:
            raise SystemExit(f"camera: clip {n} has no word '{text}' in transcript.json")
        start = max(0.08, word["start"] - cut["timeline_in"] - LEAD[kind])
        s, x, y = state["scale"], state["x"], state["y"]
        # A slow drift fills the gap before the beat; it eases back before a punch
        # (so the punch has room) and releases after one.
        if start - state["cursor"] > 0.6:
            target = s + 0.012
            if kind in ("hit", "punch"):
                target = min(target, 1.03 if kind == "hit" else 1.06)
            elif previous in ("hit", "punch"):
                target = s - 0.03
            add(state["cursor"], start - state["cursor"] - 0.02, target, x + side * 6, y - 2, "sine.inOut")
            side = -side
            s, x, y = state["scale"], state["x"], state["y"]
        previous = kind
        if kind == "hit":
            add(start, 0.26, s + 0.1, 0, y - 10, "power3.out")
        elif kind == "punch":
            add(start, 0.3, s + 0.065, x * 0.5, y - 6, "power2.out")
        elif kind == "push":
            add(start, 1.1, s + 0.035, x - side * 5, y - 4, "sine.inOut")
        elif kind == "pull":
            add(start, 0.9, s - 0.06, x + side * 8, y + 3, "power1.inOut")
        else:
            add(start, 0.25, s + 0.015, x + side * 12, y, "power2.out")
            side = -side
    if duration - 0.02 - state["cursor"] > 0.4:
        s, x, y = state["scale"], state["x"], state["y"]
        add(state["cursor"], duration - 0.02 - state["cursor"], s + (-0.02 if previous in ("hit", "punch") else 0.012),
            x + side * 6, y - 2, "sine.inOut")
    return {"reason": entry.get("reason", "drift"), "initial": initial, "moves": moves}


def run() -> None:
    cuts = common.read_json("scripts/cut-map.json")["clips"]
    words = common.read_json("scripts/transcript.json")
    plan = common.CONFIG.get("camera", {})
    clips = {str(c["order"]): plan_clip(c["order"], c, words, plan.get(str(c["order"]), {})) for c in cuts}
    common.write_json("scripts/camera-moves.json", {
        "notes": "Generated from reel.config.json 'camera'. Times are relative to each clip.",
        "clips": clips,
    })
    print(f"  {sum(len(c['moves']) for c in clips.values())} camera moves over {len(clips)} clips")
