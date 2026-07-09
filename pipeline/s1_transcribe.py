"""Stage 1: GPU transcription with word-level timestamps.

ffmpeg extracts 16k mono wav -> faster-whisper (CUDA) -> transcript.json:
  { "language", "duration", "words":[{w,start,end}], "captions":[{text,start,end,words:[...]}] }
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from common import CFG, extract_audio, list_videos, parse_common_args, read_json, stage_done, video_id_for, work_dir, write_json


def _add_cuda_dll_dirs() -> None:
    """On Windows, expose the pip-installed nvidia CUDA DLLs (cudart/cuBLAS/cuDNN) to
    CTranslate2. PATH is prepended so transitive deps (e.g. cuBLAS -> cudart) also resolve."""
    if not sys.platform.startswith("win"):
        return
    base = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
    bindirs = [str(p) for p in base.glob("*/bin") if p.is_dir()]
    if not bindirs:
        return
    os.environ["PATH"] = os.pathsep.join(bindirs) + os.pathsep + os.environ.get("PATH", "")
    for bindir in bindirs:
        try:
            os.add_dll_directory(bindir)
        except OSError:
            pass


def chunk_captions(words: list[dict]) -> list[dict]:
    """Group words into short on-screen captions by count and silence gaps."""
    max_words = CFG["transcribe"]["max_caption_words"]
    max_gap = CFG["transcribe"]["max_caption_gap"]
    caps: list[dict] = []
    cur: list[dict] = []
    for w in words:
        if cur:
            gap = w["start"] - cur[-1]["end"]
            if len(cur) >= max_words or gap > max_gap:
                caps.append(_pack(cur))
                cur = []
        cur.append(w)
    if cur:
        caps.append(_pack(cur))
    return caps


def _pack(words: list[dict]) -> dict:
    return {
        "text": " ".join(w["w"] for w in words).strip(),
        "start": words[0]["start"],
        "end": words[-1]["end"],
        "words": words,
    }


def transcribe_one(video: Path, force: bool = False) -> dict:
    vid = video_id_for(video)
    wd = work_dir(vid)
    out = wd / "transcript.json"
    if out.exists() and not force:
        print(f"[s1] {vid}: transcript exists, skip")
        return read_json(out)

    _add_cuda_dll_dirs()
    from faster_whisper import WhisperModel  # imported lazily so orchestrator help works without torch

    wav = wd / "audio.wav"
    print(f"[s1] {vid}: extracting audio")
    extract_audio(video, wav)

    tc = CFG["transcribe"]
    print(f"[s1] {vid}: loading model {tc['model']} on {tc['device']}")
    model = WhisperModel(tc["model"], device=tc["device"], compute_type=tc["compute_type"])

    segments, info = model.transcribe(
        str(wav), language=tc["language"], vad_filter=tc["vad_filter"],
        word_timestamps=True,
    )

    words: list[dict] = []
    for seg in segments:
        for w in (seg.words or []):
            words.append({"w": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3)})
    print(f"[s1] {vid}: {len(words)} words")

    data = {
        "language": info.language,
        "duration": round(info.duration, 3),
        "words": words,
        "captions": chunk_captions(words),
    }
    write_json(out, data)
    wav.unlink(missing_ok=True)
    return data


def main(argv: list[str]) -> None:
    argv = parse_common_args(argv)
    force = "--force" in argv
    targets = [a for a in argv if not a.startswith("--")]
    videos = list_videos()
    if targets:
        videos = [v for v in videos if video_id_for(v) in targets or v.name in targets]
    for v in videos:
        transcribe_one(v, force=force)


if __name__ == "__main__":
    main(sys.argv[1:])
