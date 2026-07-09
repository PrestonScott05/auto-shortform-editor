# EditingAutomation — auto tier-list video editor

Batch pipeline that turns raw talking-head tier-list clips into edited verticals with an
S-tier board, moved-up framing, karaoke captions, and internet images that animate into
their tier cell when rated. See [PLAN.md](PLAN.md) for the design.

## One-time setup

### 1. Python 3.12 ML env (transcription + LLM parsing)
faster-whisper runs on CTranslate2 (CUDA) — no PyTorch needed.
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
GPU transcription needs the NVIDIA cuBLAS + cuDNN libraries on PATH. If you hit a
`cublas`/`cudnn` load error, `pip install nvidia-cublas-cu12 nvidia-cudnn-cu12` (already
in requirements) supplies them.

### 2. Keys
```powershell
copy .env.example .env
# edit .env: ANTHROPIC_API_KEY (stages 2-3), SERPAPI_KEY (stage 4)
```
No SerpAPI key? Set `images.engine: openverse` in `config.yaml` (free, CC-licensed).

### 3. Remotion renderer
```powershell
cd render
npm install
cd ..
```

## Run

```powershell
# transcribe -> classify -> extract tiers -> fetch images -> build editplans (all videos)
.\.venv\Scripts\python.exe pipeline\orchestrate.py

# or one video, or a subset of stages:
.\.venv\Scripts\python.exe pipeline\orchestrate.py 00b94dc772574d0492d2b96f9d4b0125
.\.venv\Scripts\python.exe pipeline\orchestrate.py --only=s1,s2
```

Artifacts land in `work/<id>/` (transcript, classification, events, editplan) and assets in
`render/public/<id>/`.

## Review (semi-auto)

Open `review/review.html` in a browser and load a `render/public/<id>/editplan.json` to
sanity-check items, tiers, timings, and images. Fix the JSON (or re-run a stage with
`--force`) before rendering. You can also preview live:
```powershell
cd render && npm run studio     # opens Remotion Studio; pick the TierList composition
```

## Render finals

```powershell
cd render
npm run still  -- <id> 300      # quick PNG preview of one frame
npm run render -- <id>          # full mp4 -> out/<id>.mp4 (GPU encode)
```

## Layout tuning
Edit `layout:` in `config.yaml` (video shift/scale, board position, caption height), then
re-run stage s5 (`--only=s5 --force`) and re-render. Tier set/colors also live there.

## Other categories
Non-tier-list videos get a `classification.json` with `category: other` and a label but no
template yet. Collect the labels after a first pass, then add per-category Remotion
compositions the same way `TierList` is built.
