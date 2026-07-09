"""Patch layout fields on a single video's editplan (the copy Remotion renders), so you
can tweak framing/captions and just refresh Studio to preview. Examples:

  py -3.12 pipeline/set_layout.py <id> videoTranslateY=-150
  py -3.12 pipeline/set_layout.py <id> videoTranslateY=-150 captionSize=52 boardTopRatio=0.55

This is a PER-VIDEO override written straight to render/public/<id>/editplan.json (and the
work/ copy). It does NOT touch config.yaml, and re-running `s5 --force` for this video will
overwrite it. For a change that should apply to every video, edit config.yaml instead, or
use apply_bulk_layout.py.
"""
from __future__ import annotations

import sys

from common import LAYOUT_KEYS, patch_editplan_layout


def cast(v: str):
    for fn in (int, float):
        try:
            return fn(v)
        except ValueError:
            pass
    return {"true": True, "false": False}.get(v.lower(), v)


def main(argv: list[str]) -> None:
    if len(argv) < 2 or "=" not in "".join(argv[1:]):
        raise SystemExit("usage: set_layout.py <videoId> key=value [key=value ...]\n"
                         "  e.g. set_layout.py 00b9... videoTranslateY=-150")
    vid = argv[0]
    patches = {}
    for a in argv[1:]:
        k, _, v = a.partition("=")
        patches[k] = cast(v)

    unknown = [k for k in patches if k not in LAYOUT_KEYS]
    if unknown:
        print(f"skipping unknown layout keys {unknown}; valid keys: {LAYOUT_KEYS}")

    applied = patch_editplan_layout(vid, patches)
    if not applied:
        raise SystemExit(f"no editplan found for '{vid}' (or no valid keys). Run s5 first, or check the id.")
    print(f"patched {vid} -> {applied}")
    print("Refresh the Remotion Studio tab (or reselect the composition) to preview.")


if __name__ == "__main__":
    main(sys.argv[1:])
