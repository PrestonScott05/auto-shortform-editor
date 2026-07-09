# EditingAutomation
*work in progress*

Automated editing pipeline that turns raw talking-head tier-list videos into finished
vertical shorts. It transcribes each clip on the GPU, uses an LLM to detect what is being
rated and into which tier, pulls an image for each item, and renders a captioned video with
an animated tier board using Remotion.

Built for vertical short-form video (720x1280, 30fps). Tiers, colors, and layout are
configurable.

## What it does

- Transcribes audio on the GPU with faster-whisper (word-level timestamps).
- Classifies each video by type (tier list vs other) from the transcript.
- Extracts rating events (item name, tier, timing) with an LLM.
- Fetches one image per item from SerpAPI (Google Images) or Openverse (free, no key).
- Builds a reviewable edit plan (JSON) per video.
- Renders the final video: moved-up webcam framing, karaoke captions, a tier board with
  standard colors, and item images that animate into their tier cell when rated.

It is semi-automated on purpose. Every stage writes JSON you can inspect and fix before
rendering, so mistakes from transcription or image search can be mitigated.

## Pipeline

```
raw video -> s1 transcribe -> s2 classify -> s3 extract tiers -> s4 fetch images
          -> s5 build edit plan -> review -> render
```

Each stage is resumable and writes to `work/<id>/`. Re-run a single stage with `--only` and
`--force`.

## Requirements

- NVIDIA GPU with CUDA for transcription and NVENC encoding (developed on an RTX 4070).
- Python 3.12 (newer versions may lack prebuilt ML wheels).
- Node.js 18+ for Remotion.
- FFmpeg with NVENC support.
- API keys: Anthropic (parsing). SerpAPI is optional if you use the free Openverse source.

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd render
npm install
cd ..

copy .env.example .env.local   # then add ANTHROPIC_API_KEY and SERPAPI_KEY
```

faster-whisper runs on CTranslate2, so no PyTorch install is needed.

## Usage

Put source videos in `Videos/`, then:

```powershell
# run all stages over every video
.\.venv\Scripts\python.exe pipeline\orchestrate.py

# one video, or a subset of stages
.\.venv\Scripts\python.exe pipeline\orchestrate.py <videoId>
.\.venv\Scripts\python.exe pipeline\orchestrate.py --only=s1,s2

# point at any directory (works on the standalone stage scripts too)
.\.venv\Scripts\python.exe pipeline\orchestrate.py --videos "D:\path\to\clips"
.\.venv\Scripts\python.exe pipeline\orchestrate.py --videos "D:\path\to\clips" --only=s3,s4 --force

# review, then render
# open review/review.html and load render/public/<id>/editplan.json
cd render
npm run still  -- <id> 300   # preview a single frame
npm run render -- <id>       # final mp4 to out/<id>.mp4
```

## Adjusting framing/captions across videos

`review/review.html` has two modes:

- **Single file** — load one `render/public/<id>/editplan.json` to swap photos and tweak
  that video's caption style/framing. Download and drop it back in place.
- **Load folder (bulk)** — pick the `render/public` folder to change framing/caption
  settings (video Y, scale, board position, caption color/font/size) across every loaded
  video at once. Never touches items, images, tiers, or timings — those stay per-video.
  In Chrome/Edge it can save the files directly; otherwise it downloads a patch file to
  apply with:
  ```powershell
  .\.venv\Scripts\python.exe pipeline\apply_bulk_layout.py bulk-layout-patch.json
  ```

For scripting a single field on one video without opening a browser:
```powershell
.\.venv\Scripts\python.exe pipeline\set_layout.py <videoId> videoTranslateY=-150
```

Any of these change `render/public/<id>/editplan.json` directly — refresh Remotion Studio
(Ctrl+Shift+R) to preview. Re-running `s5_editplan.py --force` for a video regenerates its
editplan from `config.yaml`, overwriting these overrides.

## Configuration

All defaults live in `config.yaml`: tier labels and colors, whisper model, LLM model, image
source, and layout (video shift and scale, board position, caption toggle). Change a value,
re-run stage s5 with `--force`, and re-render.

## Project layout

```
pipeline/    Python stages (s1..s5), orchestrator, shared helpers
render/      Remotion project (TypeScript/React) and render scripts
review/      Local HTML tool to inspect edit plans
config.yaml  Tunable defaults
```

## Extending to other video types

Non tier-list videos are still transcribed and classified, then labeled `other`. To support
a new type, add a Remotion composition for it the same way `TierList` is built, and route it
in stage s5.

## Notes

- Video files, API keys, and build output are git-ignored.
- Keep secrets in `.env.local` (ignored), not `.env.example` (a committed template).

## License

MIT.
