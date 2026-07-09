"""Stage 3 (standard path): for videos NOT classified as a tier list, find pause-based
cut points via ffmpeg silence detection and (optionally) ask the LLM for a short opening
title/hook. Writes cuts.json:

  { "segments": [{"start": 0.0, "end": 4.2}, ...],   # kept segments, seconds, source time
    "title": {"text": "...", "atSec": 0.0} | null }

Runs for every category that isn't 'tierlist' (s3_extract.py handles tierlist; this stage
skips it). This is what makes the pipeline general-purpose: any talking-head video gets
pause-cutting + a title card, independent of what it's about.
"""
from __future__ import annotations

import re
import subprocess
import sys

from common import CFG, extract_audio, list_videos, parse_common_args, read_json, stage_done, video_id_for, videos_dir, work_dir, write_json
from llm import ask_json

SILENCE_RE_START = re.compile(r"silence_start:\s*([\d.]+)")
SILENCE_RE_END = re.compile(r"silence_end:\s*([\d.]+)")

TITLE_SYSTEM = (
    "You write a short, punchy opening title/hook card (5-8 words) for a short-form "
    "vertical video, based on its transcript. Return ONLY a JSON object: "
    "{\"text\": \"...\"}. No quotes around the whole thing, no hashtags, no emoji."
)


def detect_pauses(wav_path, duration: float) -> list[tuple[float, float]]:
    cfg = CFG["cuts"]
    proc = subprocess.run(
        ["ffmpeg", "-i", str(wav_path), "-af",
         f"silencedetect=noise={cfg['silence_db']}dB:d={cfg['min_silence_sec']}",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    log = proc.stderr
    starts = [float(m) for m in SILENCE_RE_START.findall(log)]
    ends = [float(m) for m in SILENCE_RE_END.findall(log)]
    pauses = list(zip(starts, ends))
    # A silence_start with no matching silence_end means it runs to EOF.
    if len(starts) > len(ends):
        pauses.append((starts[-1], duration))
    return pauses


def pauses_to_kept_segments(pauses: list[tuple[float, float]], duration: float) -> list[tuple[float, float]]:
    pad = CFG["cuts"]["padding_sec"]
    segments: list[tuple[float, float]] = []
    cursor = 0.0
    for p_start, p_end in pauses:
        seg_end = min(p_start + pad, duration)
        if seg_end > cursor:
            segments.append((cursor, seg_end))
        cursor = max(p_end - pad, cursor)
    if cursor < duration:
        segments.append((cursor, duration))
    # Merge any segments padding caused to overlap/touch.
    merged: list[tuple[float, float]] = []
    for s, e in segments:
        if merged and s <= merged[-1][1] + 1e-6:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))
    return [(round(s, 3), round(e, 3)) for s, e in merged if e - s > 0.05]


def extract_one(video_id: str, force: bool = False) -> dict | None:
    wd = work_dir(video_id)
    out = wd / "cuts.json"
    if out.exists() and not force:
        print(f"[s3b] {video_id}: cuts exist, skip")
        return read_json(out)

    cls = read_json(wd / "classification.json")
    if cls.get("category") == "tierlist":
        print(f"[s3b] {video_id}: tierlist, handled by s3_extract, skip")
        return None

    transcript = read_json(wd / "transcript.json")
    duration = transcript["duration"]

    wav = wd / "audio_cuts.wav"
    src = next((p for p in videos_dir().iterdir() if p.stem == video_id), None)
    if src is None:
        print(f"[s3b] {video_id}: source video not found, skip")
        return None
    extract_audio(src, wav)
    pauses = detect_pauses(wav, duration)
    wav.unlink(missing_ok=True)
    segments = pauses_to_kept_segments(pauses, duration)
    print(f"[s3b] {video_id}: {len(pauses)} pause(s) -> {len(segments)} kept segment(s)")

    title = None
    if CFG["cuts"].get("add_title", True):
        text = " ".join(w["w"] for w in transcript["words"][:120])
        try:
            result = ask_json(TITLE_SYSTEM, f"Transcript (opening): {text}")
            title = {"text": result["text"], "atSec": 0.0}
        except Exception as e:  # noqa: BLE001 — title is a nice-to-have, never fail the stage over it
            print(f"[s3b] {video_id}: title generation failed ({type(e).__name__}: {e})")

    data = {"segments": [{"start": s, "end": e} for s, e in segments], "title": title}
    write_json(out, data)
    return data


def main(argv: list[str]) -> None:
    argv = parse_common_args(argv)
    force = "--force" in argv
    targets = [a for a in argv if not a.startswith("--")]
    ids = targets or [video_id_for(v) for v in list_videos()]
    for vid in ids:
        if not stage_done(vid, "classification.json"):
            print(f"[s3b] {vid}: not classified yet, skip")
            continue
        try:
            extract_one(vid, force=force)
        except Exception as e:  # noqa: BLE001 — isolate per-video so the batch continues
            print(f"[s3b] {vid}: FAILED ({type(e).__name__}: {e})")


if __name__ == "__main__":
    main(sys.argv[1:])
