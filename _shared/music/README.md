# Music (optional)

Reels play a quiet background track when this folder has it. The track is **not included** in the
repo: it comes from Pixabay, whose licence lets you use it in your videos for free but not
redistribute the file itself. Download it yourself (free account), keep the exact file name, and
save it in this folder:

| File name (keep it exactly) | What it is | Where to find it |
| --- | --- | --- |
| `velariomusic-lofi-relaxing-598427.mp3` | "Lofi Relaxing" by velariomusic, Pixabay ID 598427 | [pixabay.com/music/search/lofi relaxing](https://pixabay.com/music/search/lofi%20relaxing/) |

Pixabay download names end in the track's ID, so check that it ends in `598427` before saving.

Without the file, the build prints `warning: … not found; the reel has no music` and the reel simply
has no music. To use another track, save it here and ask the agent to use it (`music.src` and
`music.audible_length` in `reel.config.json`). After adding files, create new reels with
`npm run new-reel`; existing reels keep the sounds they were created with.
