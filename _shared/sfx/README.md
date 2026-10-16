# Transition sounds (optional)

The pipeline ships with ~20 sound effects (pops, clicks, typing, whooshes) that `npm run setup`
copies from the HyperFrames skills. Four extra transition sounds make the cuts richer. They are
**not included**: they come from Pixabay, whose licence lets you use them in your videos for free but
not redistribute the files. Download them yourself (free account), keep the exact file names, and
save them in this folder:

| File name (keep it exactly) | Used for | Pixabay ID | Where to find it |
| --- | --- | --- | --- |
| `creatorshome-turn-a-page-336933.mp3` | swipe transitions | 336933 | [search "turn a page"](https://pixabay.com/sound-effects/search/turn%20a%20page/) |
| `soundreality-whoosh-flame-388763.mp3` | spin + zoom transitions | 388763 | [search "whoosh flame"](https://pixabay.com/sound-effects/search/whoosh%20flame/) |
| `oxidvideos-transition-sfx-2-409073.mp3` | spin transitions | 409073 | [search "transition sfx"](https://pixabay.com/sound-effects/search/transition%20sfx/) |
| `soundreality-whoosh-vortex-2-388197.mp3` | the opening of every reel | 388197 | [search "whoosh vortex"](https://pixabay.com/sound-effects/search/whoosh%20vortex/) |

Pixabay download names start with the creator and end in the sound's ID, so you can check you have
the right one. Any file that is missing is replaced by the bundled whoosh, with a
`warning: … not found` line in the build output. After adding files, create new reels with
`npm run new-reel`; existing reels keep the sounds they were created with.
