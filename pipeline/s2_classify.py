"""Stage 2: classify the video from its transcript.

Output classification.json: { "category": "tierlist" | "other", "label": "...", "reason": "..." }
Only 'tierlist' proceeds to s3/s4; others are routed for later handling.
"""
from __future__ import annotations

import sys

from common import list_videos, read_json, stage_done, video_id_for, work_dir, write_json
from llm import ask_json

SYSTEM = (
    "You classify short-form vertical videos from their transcript. "
    "Return ONLY a JSON object: {\"category\": \"tierlist\" | \"other\", "
    "\"label\": short-kebab-label, \"reason\": one sentence}. "
    "category is 'tierlist' when the speaker rates a series of things into tiers/letters "
    "(S/A/B/C/D/F) or clearly ranks items into named buckets. Otherwise 'other' and give a "
    "descriptive label like 'top-10-ranking', 'reaction', 'story-time', 'qa'."
)


def classify_one(video_id: str, force: bool = False) -> dict:
    wd = work_dir(video_id)
    out = wd / "classification.json"
    if out.exists() and not force:
        print(f"[s2] {video_id}: classified, skip")
        return read_json(out)

    transcript = read_json(wd / "transcript.json")
    text = " ".join(w["w"] for w in transcript["words"])
    result = ask_json(SYSTEM, f"Transcript:\n{text}")
    print(f"[s2] {video_id}: {result.get('category')} / {result.get('label')}")
    write_json(out, result)
    return result


def main(argv: list[str]) -> None:
    force = "--force" in argv
    targets = [a for a in argv if not a.startswith("--")]
    ids = targets or [video_id_for(v) for v in list_videos()]
    for vid in ids:
        if not stage_done(vid, "transcript.json"):
            print(f"[s2] {vid}: no transcript yet, skip")
            continue
        try:
            classify_one(vid, force=force)
        except Exception as e:  # noqa: BLE001 — isolate per-video so the batch continues
            print(f"[s2] {vid}: FAILED ({type(e).__name__}: {e})")


if __name__ == "__main__":
    main(sys.argv[1:])
