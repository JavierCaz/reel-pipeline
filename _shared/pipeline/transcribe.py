"""Step 2 — transcribe each approved cut range on its own and place words on the cut timeline.

Why per clip: given the whole joined cut, Parakeet drifted into English after ~115 s
(CelularEscucha, 2026-10-05). Each range is cached in .cache/clip-asr/NN/ keyed by
source + in/out, so re-running after a small cut change only re-transcribes changed clips.
Writes scripts/transcript-asr.json (raw ASR); review.py applies fixes.
"""

from __future__ import annotations

import json
import subprocess

from . import common


def run() -> None:
    cuts = common.read_json("scripts/cut-map.json")["clips"]
    language = common.CONFIG.get("language", "es")
    pin = common.hyperframes_pin()
    words = []
    for cut in cuts:
        folder = common.p(f".cache/clip-asr/{cut['order']:02d}")
        folder.mkdir(parents=True, exist_ok=True)
        key = {"source": cut["source"], "in": cut["source_in"], "out": cut["source_out"], "language": language, "pin": pin}
        key_path, result_path = folder / "range.json", folder / "transcript.json"
        cached = key_path.exists() and result_path.exists() and json.loads(key_path.read_text()) == key
        if not cached:
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(common.p(cut["source"])),
                            "-ss", str(cut["source_in"]), "-t", str(cut["duration"]),
                            "-map", "0:a:0", "-ac", "1", "-ar", "16000", str(folder / "clip.wav")], check=True)
            result = subprocess.run([common.npx(), "--yes", pin, "transcribe", "clip.wav", "-d", ".", "-l", language, "--json"],
                                    cwd=folder, capture_output=True, text=True)
            if result.returncode != 0 or not result_path.exists():
                detail = (result.stdout + result.stderr).strip().splitlines()[-1:] or ["no output"]
                hint = ("the speech-to-text model is not installed: run `npm run setup` from the repo root"
                        if "whisper_unavailable" in detail[0] else "check that the clip has sound, then run the build again")
                raise SystemExit(f"Transcription of clip {cut['order']} failed ({detail[0]}): {hint}.")
            key_path.write_text(json.dumps(key))
        for word in json.loads(result_path.read_text()):
            start = round(cut["timeline_in"] + min(word["start"], cut["duration"]), 3)
            end = round(cut["timeline_in"] + min(word["end"], cut["duration"]), 3)
            words.append({"text": word["text"], "start": start, "end": max(end, start), "clip": cut["order"]})
        text = " ".join(w["text"] for w in words if w["clip"] == cut["order"])
        print(f"  {cut['order']:2}{' (cached)' if cached else ''}: {text}")
    for index, word in enumerate(words):
        word["id"] = f"w{index}"
    common.write_json("scripts/transcript-asr.json", words)
    print(f"  {len(words)} words → scripts/transcript-asr.json")
