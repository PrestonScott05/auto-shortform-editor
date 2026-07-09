"""Apply a bulk layout patch to every video's editplan (or a chosen subset). Layout-only:
framing (video Y/scale, board position) and caption style — never items/images/tiers.

Intended to consume the JSON exported by review.html's "Load folder" bulk mode, but any
{ "layout": {...} } file works. Usage:

  py -3.12 pipeline/apply_bulk_layout.py bulk-layout-patch.json                # all videos
  py -3.12 pipeline/apply_bulk_layout.py bulk-layout-patch.json <id> [<id>...] # a subset
  py -3.12 pipeline/apply_bulk_layout.py bulk-layout-patch.json --videos "D:\\clips"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from common import LAYOUT_KEYS, list_videos, parse_common_args, patch_editplan_layout, video_id_for


def main(argv: list[str]) -> None:
    argv = parse_common_args(argv)
    if not argv:
        raise SystemExit(
            "usage: apply_bulk_layout.py <patch.json> [<id> ...] [--videos <dir>]"
        )
    patch_path = Path(argv[0])
    ids = argv[1:]

    data = json.loads(patch_path.read_text(encoding="utf-8"))
    patches = data.get("layout", {})
    if not patches:
        raise SystemExit(f"no 'layout' patches found in {patch_path}")

    unknown = [k for k in patches if k not in LAYOUT_KEYS]
    if unknown:
        print(f"skipping unknown layout keys {unknown}; valid keys: {LAYOUT_KEYS}")

    targets = ids or [video_id_for(v) for v in list_videos()]
    print(f"Applying {patches} to {len(targets)} video(s)")
    changed = 0
    for vid in targets:
        applied = patch_editplan_layout(vid, patches)
        if applied:
            changed += 1
            print(f"  {vid}: {applied}")
        else:
            print(f"  {vid}: no editplan found, skipped")

    print(f"\nDone. {changed}/{len(targets)} editplans updated. Refresh Remotion Studio (Ctrl+Shift+R) to preview.")


if __name__ == "__main__":
    main(sys.argv[1:])
