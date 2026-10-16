#!/usr/bin/env python3
"""Reel pipeline CLI. Run from a project folder (or pass --project).

  npm run build -- <step> ...           (package.json runs this file through ../../scripts/py.mjs)
  python ../../_shared/pipeline/build.py <step> [<step> ...]

Steps (in pipeline order):
  boundaries   1  measure speech edges        → .cache/energy-scan.json
  cut          2  cut map + index.html        → scripts/cut-map.json, index.html
  transcribe   2  per-clip Spanish ASR        → scripts/transcript-asr.json (cached per clip)
  review       2  apply transcript_fixes      → scripts/transcript.json
  camera       3  emphasis-word camera plan   → scripts/camera-moves.json
  captions     5  caption track               → src/captions.html, caption-cues.json, subtitulos.srt
  visuals      6  scenes.py → sub-compositions→ src/visuals/*.html, visual-scenes.json, visual-sfx.json
  matte        6  presenter cutouts for "stage"  → media/cutouts/<clip>.webm (cached; slow, CPU)
  cover        9  title + illustration + frame → renders/<id>-cover.png (config "cover", scenes.py cover(c))
Aliases:
  all          every step, then cut again to mount everything
  rebuild      review camera captions visuals cut   (after editing config or scenes.py; no ASR)
  graphics     visuals cut                           (after editing scenes.py only)
Transitions (4), opening, SFX (7), and music (8) are mounted by `cut` from reel.config.json.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from pipeline import common  # noqa: E402

ORDER = ["boundaries", "cut", "transcribe", "review", "camera", "captions", "visuals"]
ALIASES = {
    "all": ORDER + ["matte", "cut"],
    "rebuild": ["review", "camera", "captions", "visuals", "cut"],
    "graphics": ["visuals", "cut"],
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("steps", nargs="+", help="steps or aliases")
    parser.add_argument("--project", default=".", help="project folder (default: current directory)")
    args = parser.parse_args()
    steps = [s for step in args.steps for s in ALIASES.get(step, [step])]
    unknown = [s for s in steps if s not in ORDER + ["matte", "cover"]]
    if unknown:
        parser.error(f"unknown step(s): {', '.join(unknown)}")
    project = Path(args.project)
    if not (project / "reel.config.json").exists():
        parser.error(f"no reel.config.json in {project.resolve()}: run this from a reel folder in Shorts/")
    common.load(project)
    for step in steps:
        print(f"▸ {step}")
        module = importlib.import_module(f"pipeline.{step}")
        module.run()
    print("Done. Next: npm run check")


if __name__ == "__main__":
    main()
