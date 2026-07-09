"""Stage 5: assemble editplan.json (Remotion props) and stage the source video.

Merges transcript captions + tier events + config layout/colors, converts seconds->frames,
and hardlinks (or copies) the source video into render/public/<id>/source<ext> so Remotion
can serve it via staticFile.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from common import (
    CFG, ffprobe, list_videos, public_dir, read_json, stage_done, video_id_for,
    videos_dir, work_dir, write_json,
)


def stage_source(video: Path, video_id: str) -> str:
    dest = public_dir(video_id) / f"source{video.suffix.lower()}"
    if not dest.exists():
        try:
            import os
            os.link(video, dest)  # hardlink: no extra disk on same volume
        except OSError:
            shutil.copy2(video, dest)
    return f"{video_id}/{dest.name}"


def editplan_one(video: Path, force: bool = False) -> dict | None:
    vid = video_id_for(video)
    wd = work_dir(vid)
    out = wd / "editplan.json"
    if out.exists() and not force:
        print(f"[s5] {vid}: editplan exists, skip")
        return read_json(out)

    transcript = read_json(wd / "transcript.json")
    cls = read_json(wd / "classification.json")
    if cls.get("category") != "tierlist":
        print(f"[s5] {vid}: category {cls.get('label')} has no tierlist template yet, skip")
        return None

    events = read_json(wd / "events.json")
    probe = ffprobe(video)
    fps = round(probe.fps)

    def f(sec: float) -> int:
        return max(0, round(sec * fps))

    layout = CFG["layout"]
    captions = [
        {
            "text": c["text"],
            "startFrame": f(c["start"]),
            "endFrame": f(c["end"]),
            "words": [
                {"w": w["w"], "startFrame": f(w["start"]), "endFrame": f(w["end"])}
                for w in c["words"]
            ],
        }
        for c in transcript["captions"]
    ]

    # Assign a horizontal slot per tier in the order items are rated.
    slot_counter: dict[str, int] = {}
    items = []
    for it in events.get("items", []):
        tier = it["tier"]
        slot = slot_counter.get(tier, 0)
        slot_counter[tier] = slot + 1
        items.append({
            "id": it["id"],
            "name": it["name"],
            "image": it.get("image"),
            "tier": tier,
            "slotIndex": slot,
            "introFrame": f(it["introSec"]),
            "ratedFrame": f(it["ratedSec"]),
        })

    plan = {
        "videoId": vid,
        "fps": fps,
        "width": probe.width,
        "height": probe.height,
        "durationInFrames": f(probe.duration),
        "backgroundSrc": stage_source(video, vid),
        "layout": {
            "videoScale": layout["video_scale"],
            "videoTranslateY": layout["video_translate_y"],
            "boardTopRatio": layout["board_top_ratio"],
            "captionBaselineRatio": layout["caption_baseline_ratio"],
            "showCaptions": layout.get("show_captions", True),
        },
        "tiers": CFG["tiers"],
        "captions": captions,
        "items": items,
    }
    write_json(out, plan)
    # A copy under public makes it easy to load in the Remotion studio / review UI.
    write_json(public_dir(vid) / "editplan.json", plan)
    print(f"[s5] {vid}: editplan with {len(items)} items, {len(captions)} captions")
    return plan


def main(argv: list[str]) -> None:
    force = "--force" in argv
    targets = [a for a in argv if not a.startswith("--")]
    videos = list_videos()
    if targets:
        videos = [v for v in videos if video_id_for(v) in targets or v.name in targets]
    for v in videos:
        if not stage_done(video_id_for(v), "events.json"):
            continue
        try:
            editplan_one(v, force=force)
        except Exception as e:  # noqa: BLE001 — isolate per-video so the batch continues
            print(f"[s5] {video_id_for(v)}: FAILED ({type(e).__name__}: {e})")


if __name__ == "__main__":
    main(sys.argv[1:])
