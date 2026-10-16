"""Step 2 — apply targeted proofreading from reel.config.json "transcript_fixes".

Fixes are keyed by clip number and the ASR's original word (never by word id, which
shifts when a clip is re-transcribed). A fix whose word is absent is reported, not
silently dropped. Writes scripts/transcript.json, the timing source for every overlay.

  "transcript_fixes": {
    "replace": [[clip, "asr word", "fixed word", "why"]],
    "merge":   [[clip, ["finger", "printing,"], "fingerprinting,"]],
    "insert":  [{"clip": 3, "before": "necesita", "text": "no", "start": 14.24, "end": 14.34,
                 "previous_text": "no,", "why": "..."}]
  }
"""

from __future__ import annotations

from . import common


def run() -> None:
    fixes = common.CONFIG.get("transcript_fixes", {})
    words = [dict(w) for w in common.read_json("scripts/transcript-asr.json")]
    missing = []
    for clip, old, new, *_ in fixes.get("replace", []):
        match = next((w for w in words if w["clip"] == clip and w["text"] == old), None)
        if match:
            match["text"] = new
        else:
            missing.append(f"replace {clip}:{old}")
    for clip, parts, joined in fixes.get("merge", []):
        for index in range(len(words) - len(parts) + 1):
            window = words[index: index + len(parts)]
            if all(w["clip"] == clip and w["text"] == part for w, part in zip(window, parts)):
                window[0]["text"], window[0]["end"] = joined, window[-1]["end"]
                del words[index + 1: index + len(parts)]
                break
        else:
            missing.append(f"merge {clip}:{' '.join(parts)} (may already be joined)")
    for item in fixes.get("insert", []):
        target = next((i for i, w in enumerate(words) if w["clip"] == item["clip"] and w["text"] == item["before"]), None)
        if target is None:
            missing.append(f"insert before {item['clip']}:{item['before']}")
            continue
        if any(w["clip"] == item["clip"] and abs(w["start"] - item["start"]) < 0.05 for w in words):
            continue  # the ASR already heard this word
        if "previous_text" in item:
            words[target - 1]["text"] = item["previous_text"]
        words.insert(target, {"text": item["text"], "start": item["start"], "end": item["end"], "clip": item["clip"]})
        words[target + 1]["start"] = max(words[target + 1]["start"], item["end"])
    for index, word in enumerate(words):
        word["id"] = f"w{index}"
    common.write_json("scripts/transcript.json", words)
    for note in missing:
        print(f"  ! fix not applied: {note}")
    print(f"  {len(words)} reviewed words → scripts/transcript.json")
