# Reel Pipeline

Record your clips; one prompt edits the reel. An editing workflow where [Claude Code](https://claude.com/claude-code) and [HyperFrames](https://hyperframes.heygen.com) turn raw talking-head clips into a finished vertical reel (1080×1920): trimmed silences, camera motion, transitions, subtitles, animated diagrams, sound effects, music, an end card and a cover image. You review a preview and approve; nothing is rendered before that.

**New to the terminal?** Follow the step-by-step guide (PDF): [English](https://javiercazares.dev/guides/reel-pipeline-guide-en.pdf) · [Español](https://javiercazares.dev/guides/reel-pipeline-guide-es.pdf). The story behind it: [javiercazares.dev/projects/reel-pipeline](https://javiercazares.dev/projects/reel-pipeline/).

## Quick start

You need Node.js 22+, Python 3.10+, FFmpeg and Claude Code (a Claude plan that includes it).

```bash
npm run setup                   # checks your computer, installs the HyperFrames skills
npm run new-reel MyFirstReel    # creates Shorts/MyFirstReel
# copy your clips into Shorts/MyFirstReel/media/raw/, then start Claude Code here:
claude
```

Paste the kickoff prompt from [`_templates/short-template/README.md`](_templates/short-template/README.md) (Spanish and English versions), fill in the brackets, and wait for the preview.

Music and four transition sounds are optional downloads (licence reasons): see [`_shared/music/README.md`](_shared/music/README.md) and [`_shared/sfx/README.md`](_shared/sfx/README.md).

## What's inside

| Path | What it is |
| --- | --- |
| `_shared/pipeline/` | the engine (Python, standard library only): one module per editing step, plus its docs |
| `_templates/short-template/` | what every new reel starts from, including the production guide the agent follows |
| `_shared/examples/` | the data of two finished reels (config and scenes, no footage), as worked examples |
| `Shorts/` | your reels |
| `scripts/` | `setup`, `new-reel`, and the Python launcher used by `npm run build` |

## License

MIT for the code and docs in this repository (see `LICENSE`). Sound effects copied by `npm run setup` come from the HyperFrames skills under the Pixabay Content License; optional music and sounds are downloaded by you from Pixabay.
