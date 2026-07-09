"""Stage 3: extract ordered tier-rating events from a tier-list transcript.

Output events.json: { "tiers":[labels...], "items":[ {
   "id", "name", "tier", "introSec", "ratedSec", "query" } ] }

introSec = when the item is first introduced/shown; ratedSec = when the tier is assigned.
query = concise image-search query for the thing.
"""
from __future__ import annotations

import sys

from common import CFG, list_videos, read_json, stage_done, video_id_for, work_dir, write_json
from llm import ask_json

SYSTEM = (
    "You extract tier-list rating events from a timestamped transcript. "
    "The transcript is a list of words with start/end seconds. "
    "Identify each distinct THING the speaker rates and the tier they assign it. "
    "Return ONLY a JSON object with keys 'tiers' and 'items'.\n"
    "'tiers' = the ordered list of tier labels actually used (subset/superset of {allowed}).\n"
    "'items' = array, in the order rated, each: {\n"
    "  'name': the thing's display name,\n"
    "  'tier': one letter from the allowed tiers,\n"
    "  'introSec': seconds when the thing is first mentioned/introduced,\n"
    "  'ratedSec': seconds when the tier is stated (must be >= introSec),\n"
    "  'query': a concise, unambiguous image-search query for the thing }.\n"
    "Use the word timestamps to set introSec/ratedSec accurately. Skip asides that are not rated."
)


def extract_one(video_id: str, force: bool = False) -> dict | None:
    wd = work_dir(video_id)
    out = wd / "events.json"
    if out.exists() and not force:
        print(f"[s3] {video_id}: events exist, skip")
        return read_json(out)

    cls = read_json(wd / "classification.json")
    if cls.get("category") != "tierlist":
        print(f"[s3] {video_id}: not a tierlist ({cls.get('label')}), skip")
        return None

    transcript = read_json(wd / "transcript.json")
    allowed = [t["label"] for t in CFG["tiers"]]
    # Compact word stream: "word@start" keeps tokens small but timed.
    stream = " ".join(f"{w['w']}@{w['start']}" for w in transcript["words"])
    system = SYSTEM.format(allowed=allowed)
    result = ask_json(system, f"Allowed tiers: {allowed}\nWords (word@startSec):\n{stream}")

    items = result.get("items", [])
    for i, it in enumerate(items):
        it["id"] = f"item{i:02d}"
        it["introSec"] = float(it.get("introSec", 0.0))
        it["ratedSec"] = max(float(it.get("ratedSec", it["introSec"])), it["introSec"])
    result["items"] = items
    print(f"[s3] {video_id}: {len(items)} rated items")
    write_json(out, result)
    return result


def main(argv: list[str]) -> None:
    force = "--force" in argv
    targets = [a for a in argv if not a.startswith("--")]
    ids = targets or [video_id_for(v) for v in list_videos()]
    for vid in ids:
        if not stage_done(vid, "classification.json"):
            print(f"[s3] {vid}: not classified yet, skip")
            continue
        extract_one(vid, force=force)


if __name__ == "__main__":
    main(sys.argv[1:])
