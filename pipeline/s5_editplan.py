"""Stage 5: assemble editplan.json (Remotion props) and stage the source video.

Branches by classification:
  - "tierlist" -> tier board + items (from events.json)
  - anything else -> "standard" template: pause-cut timeline + opening title card
    (from cuts.json), same captions/framing machinery, no board.

Converts seconds -> frames, and hardlinks (or copies) the source video into
render/public/<id>/source<ext> so Remotion can serve it via staticFile.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

from common import (
    CFG, ffprobe, list_videos, parse_common_args, public_dir, read_json, stage_done,
    video_id_for, videos_dir, work_dir, write_json,
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


def layout_props(layout: dict) -> dict:
    return {
        "videoScale": layout["video_scale"],
        "videoTranslateY": layout["video_translate_y"],
        "boardTopRatio": layout["board_top_ratio"],
        "captionBaselineRatio": layout["caption_baseline_ratio"],
        "showCaptions": layout.get("show_captions", True),
        "captionColor": layout.get("caption_color", "#FFFFFF"),
        "captionActiveColor": layout.get("caption_active_color", "#FFE14D"),
        "captionFont": layout.get("caption_font", "Arial Black, Arial, sans-serif"),
        "captionSize": layout.get("caption_size", 44),
    }


def build_tierlist_plan(video: Path, vid: str, fps: int, probe, transcript: dict) -> dict:
    def f(sec: float) -> int:
        return max(0, round(sec * fps))

    events = read_json(work_dir(vid) / "events.json")
    captions = [
        {
            "text": c["text"],
            "startFrame": f(c["start"]),
            "endFrame": f(c["end"]),
            "words": [{"w": w["w"], "startFrame": f(w["start"]), "endFrame": f(w["end"])} for w in c["words"]],
        }
        for c in transcript["captions"]
    ]

    slot_counter: dict[str, int] = {}
    items = []
    for it in events.get("items", []):
        tier = it["tier"]
        slot = slot_counter.get(tier, 0)
        slot_counter[tier] = slot + 1
        items.append({
            "id": it["id"], "name": it["name"], "image": it.get("image"), "tier": tier,
            "slotIndex": slot, "introFrame": f(it["introSec"]), "ratedFrame": f(it["ratedSec"]),
        })

    return {
        "videoId": vid,
        "template": "tierlist",
        "fps": fps,
        "width": probe.width,
        "height": probe.height,
        "durationInFrames": f(probe.duration),
        "backgroundSrc": stage_source(video, vid),
        "layout": layout_props(CFG["layout"]),
        "tiers": CFG["tiers"],
        "captions": captions,
        "items": items,
        "cutSegments": [],
        "titleCard": None,
    }


def build_cut_timeline(segments_sec: list[dict], fps: int):
    """Convert kept segments (source-time seconds) to frame data with cumulative timeline
    placement, plus a function mapping a source-time frame to its timeline frame (frames
    that fall in a removed pause snap forward to the next kept segment)."""
    def f(sec: float) -> int:
        return max(0, round(sec * fps))

    cuts = []
    cursor = 0
    for seg in segments_sec:
        s_f, e_f = f(seg["start"]), f(seg["end"])
        cuts.append({"sourceStartFrame": s_f, "sourceEndFrame": e_f, "timelineStartFrame": cursor})
        cursor += e_f - s_f
    total = cursor

    def map_frame(src_frame: int) -> int:
        for c in cuts:
            if c["sourceStartFrame"] <= src_frame <= c["sourceEndFrame"]:
                return c["timelineStartFrame"] + (src_frame - c["sourceStartFrame"])
            if src_frame < c["sourceStartFrame"]:
                return c["timelineStartFrame"]  # was in a pause; snap to the next kept segment
        return total  # past the last kept segment

    return cuts, total, map_frame


def build_standard_plan(video: Path, vid: str, fps: int, probe, transcript: dict) -> dict | None:
    cuts_data = read_json(work_dir(vid) / "cuts.json")
    segments = cuts_data.get("segments", [])
    if not segments:
        print(f"[s5] {vid}: no kept segments in cuts.json, skip")
        return None

    def f(sec: float) -> int:
        return max(0, round(sec * fps))

    cut_frames, total_frames, map_frame = build_cut_timeline(segments, fps)

    captions = []
    for c in transcript["captions"]:
        start_f, end_f = map_frame(f(c["start"])), map_frame(f(c["end"]))
        if end_f <= start_f:
            continue  # collapsed entirely into a removed pause
        words = []
        for w in c["words"]:
            ws, we = map_frame(f(w["start"])), map_frame(f(w["end"]))
            if we > ws:
                words.append({"w": w["w"], "startFrame": ws, "endFrame": we})
        if words:
            captions.append({"text": c["text"], "startFrame": start_f, "endFrame": end_f, "words": words})

    title_card = None
    t = cuts_data.get("title")
    if t:
        title_card = {"text": t["text"], "startFrame": 0, "endFrame": min(f(3.0), total_frames)}

    return {
        "videoId": vid,
        "template": "standard",
        "fps": fps,
        "width": probe.width,
        "height": probe.height,
        "durationInFrames": total_frames,
        "backgroundSrc": stage_source(video, vid),
        "layout": layout_props(CFG["layout_standard"]),
        "tiers": [],
        "captions": captions,
        "items": [],
        "cutSegments": cut_frames,
        "titleCard": title_card,
    }


def editplan_one(video: Path, force: bool = False) -> dict | None:
    vid = video_id_for(video)
    wd = work_dir(vid)
    out = wd / "editplan.json"
    if out.exists() and not force:
        print(f"[s5] {vid}: editplan exists, skip")
        return read_json(out)

    transcript = read_json(wd / "transcript.json")
    cls = read_json(wd / "classification.json")
    probe = ffprobe(video)
    fps = round(probe.fps)

    if cls.get("category") == "tierlist":
        plan = build_tierlist_plan(video, vid, fps, probe, transcript)
    else:
        plan = build_standard_plan(video, vid, fps, probe, transcript)
    if plan is None:
        return None

    write_json(out, plan)
    write_json(public_dir(vid) / "editplan.json", plan)  # copy Remotion actually renders
    print(f"[s5] {vid}: {plan['template']} editplan, {len(plan['items'])} items, "
          f"{len(plan['cutSegments'])} segments, {len(plan['captions'])} captions")
    return plan


def main(argv: list[str]) -> None:
    argv = parse_common_args(argv)
    force = "--force" in argv
    targets = [a for a in argv if not a.startswith("--")]
    videos = list_videos()
    if targets:
        videos = [v for v in videos if video_id_for(v) in targets or v.name in targets]
    for v in videos:
        vid = video_id_for(v)
        if not stage_done(vid, "classification.json"):
            continue
        cls = read_json(work_dir(vid) / "classification.json")
        needed = "events.json" if cls.get("category") == "tierlist" else "cuts.json"
        if not stage_done(vid, needed):
            print(f"[s5] {vid}: waiting on {needed}, skip")
            continue
        try:
            editplan_one(v, force=force)
        except Exception as e:  # noqa: BLE001 — isolate per-video so the batch continues
            print(f"[s5] {vid}: FAILED ({type(e).__name__}: {e})")


if __name__ == "__main__":
    main(sys.argv[1:])
