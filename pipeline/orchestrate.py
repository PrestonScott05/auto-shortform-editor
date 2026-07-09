"""Run stages 1-5 across all videos (resumable). Usage:

  py -3.12 pipeline/orchestrate.py                 # all videos, all stages
  py -3.12 pipeline/orchestrate.py <id> [<id>...]  # specific videos
  py -3.12 pipeline/orchestrate.py --only s1,s2    # limit stages
  py -3.12 pipeline/orchestrate.py --force         # redo even if artifacts exist

After it finishes, review work/<id>/editplan.json, then render:
  cd render && npm run render -- <id>
"""
from __future__ import annotations

import sys

from common import list_videos, video_id_for
import s1_transcribe, s2_classify, s3_extract, s4_images, s5_editplan


def main(argv: list[str]) -> None:
    force = "--force" in argv
    only = None
    rest = []
    for a in argv:
        if a.startswith("--only"):
            only = set(a.split("=", 1)[1].split(",")) if "=" in a else None
        elif a == "--force":
            pass
        else:
            rest.append(a)

    videos = list_videos()
    if rest:
        videos = [v for v in videos if video_id_for(v) in rest or v.name in rest]
    ids = [video_id_for(v) for v in videos]
    print(f"Processing {len(videos)} video(s)")

    def run(name: str, fn):
        if only and name not in only:
            return
        print(f"\n===== {name} =====")
        fn()

    fargs = (["--force"] if force else [])
    run("s1", lambda: s1_transcribe.main([v.name for v in videos] + fargs))
    run("s2", lambda: s2_classify.main(ids + fargs))
    run("s3", lambda: s3_extract.main(ids + fargs))
    run("s4", lambda: s4_images.main(ids + fargs))
    run("s5", lambda: s5_editplan.main(ids + fargs))

    print("\nDone. Review work/<id>/editplan.json, then: cd render && npm run render -- <id>")


if __name__ == "__main__":
    main(sys.argv[1:])
