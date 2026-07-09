# EditingAutomation
*work in progress*

Automated editing pipeline for short-form vertical video. It transcribes each clip on the
GPU, classifies it, and routes it to the right template:

- **Tier list videos** — an animated tier board with standard colors, items that fly into
  their tier cell when rated, and a picture for each item.
- **Everything else** — pause-cut editing (silence between takes/thinking is trimmed out),
  an opening title card, and karaoke captions.

Both templates share moved-up webcam framing and word-level captions, rendered with
Remotion. A local dashboard ties the whole thing together: pick video files, run the
pipeline, open the result in an editor, save, then open it in Remotion Studio — no file
browser required.

## Quick start

```powershell
cd server
npm install
npm start
```
Open **http://localhost:4000**. Add video files, select rows, click **Run pipeline on
selected**, watch the log, then **Open Editor** on a finished row and **Open Remotion
Studio** to preview/render.

## What it does

- Transcribes audio on the GPU with faster-whisper (word-level timestamps).
- Classifies each video (tier list vs. everything else) from the transcript.
- **Tier list path** — extracts rating events (item, tier, timing) with an LLM, fetches an
  image per item (DuckDuckGo, free, no key), and builds an animated tier board.
- **Standard path** — detects pauses via ffmpeg silence detection and cuts them out, asks
  the LLM for a short opening title/hook.
- Builds a reviewable edit plan (JSON) per video either way.
- Renders the final video with Remotion: moved-up webcam framing, karaoke captions, and
  the template-specific overlay (tier board, or title card + cuts).

It is semi-automated on purpose. Every stage writes JSON you can inspect and fix before
rendering, so mistakes from transcription, tier parsing, or cut detection can be corrected.

## Pipeline

```
raw video -> s1 transcribe -> s2 classify -+-> s3  extract tiers  -+-> s4 fetch images -+
                                            +-> s3b detect cuts+title -----------------> +-> s5 build edit plan -> review -> render
```

s3 runs for tier-list videos, s3b for everything else; each skips videos that aren't its
type. Every stage is resumable and writes to `work/<id>/`. Re-run a single stage with
`--only` and `--force`.

## Requirements

- NVIDIA GPU with CUDA for transcription and NVENC encoding (developed on an RTX 4070).
- Python 3.12 (newer versions may lack prebuilt ML wheels).
- Node.js 18+ for Remotion and the dashboard server.
- FFmpeg with NVENC support.
- API key: Anthropic (tier parsing, titles). Image search defaults to free/no-key
  DuckDuckGo.

## Setup

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd render
npm install
cd ..\server
npm install
cd ..

copy .env.example .env.local   # then add ANTHROPIC_API_KEY (and SERPAPI_KEY if you switch image engines)
```

faster-whisper runs on CTranslate2, so no PyTorch install is needed.

## Usage

### Dashboard (recommended)

```powershell
cd server
npm start
```
`http://localhost:4000` lists every video in `Videos/` with per-stage status. From there:
- **Add video files** — uploads land in `Videos/`, no manual copying.
- Select rows (or none, for "all"), pick stages / force, **Run pipeline on selected** — a
  live log streams below.
- **Open Editor** — opens `review/review.html` pre-loaded for that video; edit and **Save**
  writes straight back to disk (this only works when the editor is served by the
  dashboard, not opened as a raw file).
- **Open Remotion Studio** — launches Studio and opens it in a new tab.

### Command line

```powershell
# run all stages over every video
.\.venv\Scripts\python.exe pipeline\orchestrate.py

# one video, or a subset of stages
.\.venv\Scripts\python.exe pipeline\orchestrate.py <videoId>
.\.venv\Scripts\python.exe pipeline\orchestrate.py --only=s1,s2

# point at any directory (works on the standalone stage scripts too)
.\.venv\Scripts\python.exe pipeline\orchestrate.py --videos "D:\path\to\clips"
.\.venv\Scripts\python.exe pipeline\orchestrate.py --videos "D:\path\to\clips" --only=s3,s4 --force

# render
cd render
npm run still  -- <id> 300   # preview a single frame
npm run render -- <id>       # final mp4 to out/<id>.mp4
```

## Adjusting framing/captions across videos

`review/review.html` (open directly, or via the dashboard's Open Editor) has two modes:

- **Single file** — edit one video's photos, tiers, caption style, and framing. **Save**
  writes back through the dashboard server; **Download** is the offline fallback.
- **Bulk** — "Load all videos" (via the dashboard) or "Load folder" (local disk) to change
  framing/caption settings (video Y, scale, board position, caption color/font/size)
  across every loaded video at once. Never touches items, images, tiers, cuts, or
  timings — those stay per-video. Falls back to a downloadable patch file if the
  dashboard server isn't reachable:
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

All defaults live in `config.yaml`: tier labels/colors, whisper model, LLM model, image
source, pause-cut sensitivity (`cuts:`), and layout for both templates (`layout:` for tier
list, `layout_standard:` for everything else). Change a value, re-run stage s5 with
`--force`, and re-render.

## Project layout

```
pipeline/    Python stages (s1, s2, s3/s3b, s4, s5), orchestrator, shared helpers
render/      Remotion project (TypeScript/React) and render scripts
review/      Editplan editor (single-video and bulk)
server/      Local dashboard tying pipeline + editor + Remotion Studio together
config.yaml  Tunable defaults
```

## Adding another template

Classification already routes videos into two buckets. To add a third: give `s2_classify`
a new category, add an extraction stage for it (like `s3_standard.py`), branch for it in
`s5_editplan.py`, and add a Remotion component alongside `TierListVideo`/`StandardVideo`,
dispatched from `render/src/VideoRoot.tsx`.

## Notes

- Video files, API keys, and build output are git-ignored.
- Keep secrets in `.env.local` (ignored), not `.env.example` (a committed template).

## License

MIT.
