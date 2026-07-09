# Auto-Editing Pipeline — Plan

Batch auto-editor for short-form vertical videos (720×1280, HEVC, 30fps).
Primary category: **tier-list** videos. Others routed after transcription.

## Decisions (locked)
- **Renderer:** Remotion (React → frames → NVENC). Best for animated image-to-tier moves.
- **Automation:** Semi-auto. Pipeline emits a reviewable `editplan.json` per video; you
  fix mistakes, then batch-render finals.
- **Images:** SerpAPI (Google Images). Free Openverse fallback included.
- **Categories:** Tier-list first; router classifies from transcript, other types added later.

## Hardware / env
- GPU: RTX 4070 Laptop (8 GB) — enough for faster-whisper `large-v3` in float16.
- ML env: **Python 3.12** (`py -3.12`). NOT 3.14 (no PyTorch wheels yet).
- Render env: Node 25 + Remotion, encodes with FFmpeg NVENC (`h264_nvenc`).

## Stages (each resumable, writes to `work/<videoId>/`)
1. **s1_transcribe** — ffmpeg extracts 16k mono wav → faster-whisper (CUDA, word timestamps)
   → `transcript.json`.
2. **s2_classify** — LLM reads transcript → `classification.json` (`tierlist` | `other:<label>`).
3. **s3_extract** *(tierlist only)* — LLM parses ordered rating events → `events.json`
   (item name, tier S/A/B/C/D, `introSec`, `ratedSec`, image search query).
4. **s4_images** — SerpAPI per item → downloads best image to `images/`, records path.
5. **s5_editplan** — merges transcript captions + events + tier/layout config, converts
   seconds→frames → `editplan.json` (Remotion props) and stages assets into `render/public/<id>/`.
6. **REVIEW** — open `review/review.html` (or edit JSON) to fix items/timings/images.
7. **render** — `npm run render -- <id>` → `out/<id>.mp4` (NVENC).

`pipeline/orchestrate.py` runs 1→5 across every video, skipping completed stages.

## editplan.json → Remotion
- **Background:** source video scaled/shifted up (`layout.videoScale`, `videoTranslateY`) so
  head+chest stay in the top half; bottom half covered by the tier board.
- **Captions:** word-level karaoke captions above the board.
- **Tier board:** bottom half, standard tiermaker colors, one row per tier.
- **Items:** appear centered when introduced (`introFrame`), spring-animate into their tier
  cell at `ratedFrame`, and stay.

## What needs the user
- `ANTHROPIC_API_KEY` (stages 2–3) and `SERPAPI_KEY` (stage 4) in `.env`.
- Review pass before final render.
- Confirm layout defaults (video shift/scale, tier set) after first sample render.
