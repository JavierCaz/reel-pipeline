# Brand style — "terminal" (house style)

Source: the dark theme of the javiercazares.dev portfolio. Adopted for reels on 2026-10-05. The reel engine implements
it as `visuals.theme: "terminal"` (`_shared/pipeline/presets.py` THEMES + `visuals.py`).

| Token | Value | Use in reels |
| --- | --- | --- |
| Background | `#080a08` (panel `#0c0f0c`, `#0a0c09`) | graphics panel, cards |
| Grid paper | minor `#10140f`, major `#1a2117` every 4 cells | panel background (32 px cells at 1080 wide) |
| Text | `#efefe8`, secondary `#c0c6b6` / `#a1a99a` | labels, titles |
| Lines | `#343a30`, strong `#4f5847` | card borders, rules |
| Accent | lime `#b8ff35` (shadow `#52742a`) | prompts, cursor, highlights, priority blocks, caption keywords |
| Secondary | cyan `#00e5ff`, magenta `#ff4fd8`, yellow `#ffd500`, orange `#ff7a1a`, blue `#3d7bff` | data, warnings, the viewer ("Tú" = orange) |
| Type | JetBrains Mono, tight tracking (−.05 to −.1em on titles), uppercase tracked kickers | all graphics and captions |
| Shape | square corners, 1–2 px borders, hard offset shadow `8px 8px 0 #22281d` | cards, pills, tiles |
| Motifs | `> prompt`, `$ command`, blinking block cursor, window bars, status squares | titles, decor |

## Light variant — "terminal-light"

Source: the portfolio's light theme. Added for reels on 2026-10-06 as `visuals.theme: "terminal-light"`;
same motifs, light tokens. Worked example: `_shared/examples/strategy/`.

| Token | Value | Use in reels |
| --- | --- | --- |
| Background | `#f2f1ea` (panel `#fbfaf5`, `#e9e8df`) | graphics panel, cards, end card |
| Grid paper | minor `#e6e5dc`, major `#d9d8cc` | panel background |
| Text | `#0d100c`, muted `#5c6356` | labels, titles |
| Lines | `#c4c6b8`, strong `#8f9585` | card borders, rules |
| Accent | green `#356e00`, paper text `#f2f1ea` on green fills | prompts, cursor, priority blocks, caption keywords |
| Secondary (text-safe) | cyan `#007886` (portfolio `#007f8f`, darkened for AA), yellow `#8a6d00`, magenta `#852970`, orange text `#853f0e` | data, warnings, the viewer label; fills keep orange `#ff7a1a` |
| Tints | green `#dfe6d3`, yellow `#ebe6d3` (14 % of the accent on paper; 20 % failed AA) | accent and warm cards |
| Shape | hard black shadow `8px 8px 0 #0d100c`; green shadow is also black | cards, pills, tiles |
| Captions | outlined white JetBrains Mono (paper plates were rejected 2026-10-06); keywords in green `#356e00` on a paper chip `#fbfaf5`, 2 px black border, `5px 5px 0` black shadow, green underline wiping along its base | readable over footage; the chip pops with the word |

To change the house style, update this file and `presets.THEMES["terminal"]` /
`["terminal-light"]`, rebuild active reels, and review snapshots.
