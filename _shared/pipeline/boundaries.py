"""Step 1 — find strong speech at each source edge, ignoring quiet breaths and stray clicks.

Reads media/raw/*.mp4 (sorted by filename) and writes only measurements to
.cache/energy-scan.json; the edit itself is source ranges built by cut.py.
Thresholds come from reel.config.json "trim" (defaults proven on IAExplicacion).
"""

from __future__ import annotations

from array import array
import math
import subprocess
import sys

from . import common

SAMPLE_RATE = 16000
WINDOW = 320  # 20 ms
WINDOW_S = WINDOW / SAMPLE_RATE


def runs(mask: list[bool]) -> list[tuple[int, int]]:
    result, start = [], None
    for index, active in enumerate(mask + [False]):
        if active and start is None:
            start = index
        elif not active and start is not None:
            result.append((start, index))
            start = None
    return result


def duration_of(path) -> float:
    return float(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nw=1:nk=1", str(path),
    ]).decode())


def run() -> None:
    trim = common.CONFIG.get("trim", {})
    activity_db = trim.get("activity_db", -28.0)
    strong_db = trim.get("strong_db", -16.0)
    # trim.exclude: {"<file name>": "reason"} leaves whole clips out of the cut (a false start re-recorded
    # in the next clip); the file stays in media/raw and later clips are renumbered.
    exclude = trim.get("exclude", {})
    clips = sorted(c for c in common.p("media/raw").glob("*.mp4") if c.name not in exclude)
    missing = sorted(set(exclude) - {c.name for c in common.p("media/raw").glob("*.mp4")})
    if missing:
        raise SystemExit(f"trim.exclude names files not in media/raw: {', '.join(missing)}")
    for name, reason in exclude.items():
        print(f"  {name}  excluded: {reason}")
    if not clips:
        raise SystemExit("No clips in media/raw/")
    results = []
    for path in clips:
        pcm = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(path), "-vn", "-ac", "1",
                                       "-ar", str(SAMPLE_RATE), "-f", "s16le", "-"])
        samples = array("h")
        samples.frombytes(pcm)
        if sys.byteorder != "little":
            samples.byteswap()
        energies = []
        for offset in range(0, len(samples) - WINDOW + 1, WINDOW):
            block = samples[offset: offset + WINDOW]
            energies.append(sum(v * v for v in block) / (WINDOW * 32768 ** 2))
        # A five-window RMS average smooths short stops between phonemes.
        smoothed = [sum(energies[max(0, i - 2): min(len(energies), i + 3)]) / (min(len(energies), i + 3) - max(0, i - 2))
                    for i in range(len(energies))]
        db = [10 * math.log10(max(v, 1e-12)) for v in smoothed]
        active = [v > activity_db for v in db]
        initial = runs(active)
        for (_, previous_end), (next_start, _) in zip(initial, initial[1:]):
            if next_start - previous_end <= 4:
                active[previous_end:next_start] = [True] * (next_start - previous_end)
        candidates = []
        for start, end in runs(active):
            if end - start < 5:
                continue
            peak = max(db[start:end])
            candidates.append({"start": round(start * WINDOW_S, 3), "end": round(end * WINDOW_S, 3),
                               "peak_db": round(peak, 1), "strong": peak > strong_db})
        speech = [r for r in candidates if r["strong"]]
        if not speech:
            raise RuntimeError(f"No clear speech event detected in {path.name}")
        # A quiet final syllable can sit immediately after the last strong run.
        last_end = speech[-1]["end"]
        for event in candidates:
            if 0 <= event["start"] - last_end <= 0.15:
                last_end = event["end"]
        results.append({"file": path.name, "duration": duration_of(path), "first_speech_start": speech[0]["start"],
                        "last_speech_end": last_end, "events": candidates})
        print(f"  {path.name}  speech {speech[0]['start']:.2f}–{last_end:.2f}")
    common.write_json(".cache/energy-scan.json", results)
