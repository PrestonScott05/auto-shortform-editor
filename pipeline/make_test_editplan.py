"""Dev-only: build a synthetic editplan for the first video to smoke-test the renderer
without needing API keys. Stages the real source video; fabricates items + captions."""
import sys
from pathlib import Path

from common import CFG, ffprobe, list_videos, public_dir, video_id_for, write_json
from s5_editplan import stage_source

video = list_videos()[0]
vid = video_id_for(video)
probe = ffprobe(video)
fps = round(probe.fps)


def f(sec):
    return round(sec * fps)


plan = {
    "videoId": vid,
    "fps": fps,
    "width": probe.width,
    "height": probe.height,
    "durationInFrames": f(min(probe.duration, 30)),  # short for a fast test
    "backgroundSrc": stage_source(video, vid),
    "layout": {
        "videoScale": CFG["layout"]["video_scale"],
        "videoTranslateY": CFG["layout"]["video_translate_y"],
        "boardTopRatio": CFG["layout"]["board_top_ratio"],
        "captionBaselineRatio": CFG["layout"]["caption_baseline_ratio"],
    },
    "tiers": CFG["tiers"],
    "captions": [
        {"text": "this one is easily", "startFrame": f(1), "endFrame": f(3),
         "words": [{"w": "THIS", "startFrame": f(1), "endFrame": f(1.4)},
                   {"w": "ONE", "startFrame": f(1.4), "endFrame": f(1.8)},
                   {"w": "IS", "startFrame": f(1.8), "endFrame": f(2.2)},
                   {"w": "EASILY", "startFrame": f(2.2), "endFrame": f(3)}]},
    ],
    "items": [
        {"id": "item00", "name": "Example Thing A", "image": None, "tier": "S",
         "slotIndex": 0, "introFrame": f(2), "ratedFrame": f(5)},
        {"id": "item01", "name": "Example Thing B", "image": None, "tier": "C",
         "slotIndex": 0, "introFrame": f(8), "ratedFrame": f(11)},
    ],
}
out = public_dir(vid) / "editplan.json"
write_json(out, plan)
print(f"wrote {out}")
print(f"video id: {vid}")
