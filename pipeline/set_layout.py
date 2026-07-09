"""Patch layout fields on a single video's editplan (the copy Remotion renders), so you
can tweak framing/captions and just refresh Studio to preview. Examples:

  py -3.12 pipeline/set_layout.py <id> videoTranslateY=-150
  py -3.12 pipeline/set_layout.py <id> videoTranslateY=-150 captionSize=52 boardTopRatio=0.55

This is a PER-VIDEO override written straight to render/public/<id>/editplan.json (and the
work/ copy). It does NOT touch config.yaml, and re-running `s5 --force` for this video will
overwrite it. For a change that should apply to every video, edit config.yaml instead.
"""
from __future__ import annotations

import sys

from common import public_dir, read_json, work_dir, write_json


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

    touched = 0
    for base in (public_dir(vid), work_dir(vid)):
        p = base / "editplan.json"
        if not p.exists():
            continue
        plan = read_json(p)
        layout = plan.setdefault("layout", {})
        unknown = [k for k in patches if k not in layout]
        if unknown:
            print(f"skipping unknown layout keys {unknown}; valid keys: {sorted(layout)}")
        applied = {k: v for k, v in patches.items() if k in layout}
        if not applied:
            continue
        layout.update(applied)
        write_json(p, plan)
        touched += 1
        print(f"patched {p} -> {applied}")
    if not touched:
        raise SystemExit(f"no editplan found for '{vid}'. Run s5 first, or check the id.")
    print("Refresh the Remotion Studio tab (or reselect the composition) to preview.")


if __name__ == "__main__":
    main(sys.argv[1:])
