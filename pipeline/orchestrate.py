"""Run stages 1-5 over a directory of videos (resumable). Usage:

  py -3.12 pipeline/orchestrate.py                       # all videos in the configured dir
  py -3.12 pipeline/orchestrate.py <id> [<id>...]        # specific videos
  py -3.12 pipeline/orchestrate.py --videos "D:\\clips"   # point at any directory
  py -3.12 pipeline/orchestrate.py --only s3,s3b,s4      # run only certain stages
  py -3.12 pipeline/orchestrate.py --only=s5 --force     # redo even if artifacts exist

--videos and --only work on the standalone stage scripts too (e.g. s4_images.py).

After it finishes, review work/<id>/editplan.json, then render:
  cd render && npm run render -- <id>
"""
from __future__ import annotations

import sys

from common import list_videos, parse_common_args, video_id_for
import s1_transcribe, s2_classify, s3_extract, s3_standard, s4_images, s5_editplan


def main(argv: list[str]) -> None:
    argv = parse_common_args(argv)  # applies --videos, returns the rest
    force = "--force" in argv
    only = None
    rest = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--force":
            i += 1
        elif a == "--only" and i + 1 < len(argv):
            only = set(argv[i + 1].split(","))
            i += 2
        elif a.startswith("--only="):
            only = set(a.split("=", 1)[1].split(","))
            i += 1
        else:
            rest.append(a)
            i += 1

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
    run("s3", lambda: s3_extract.main(ids + fargs))     # tierlist videos
    run("s3b", lambda: s3_standard.main(ids + fargs))   # everything else: pause-cuts + title
    run("s4", lambda: s4_images.main(ids + fargs))
    run("s5", lambda: s5_editplan.main(ids + fargs))

    print("\nDone. Review work/<id>/editplan.json, then: cd render && npm run render -- <id>")


if __name__ == "__main__":
    main(sys.argv[1:])
