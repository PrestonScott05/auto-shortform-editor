"""Stage 4: fetch one image per rated item and stage it for Remotion.

Downloads to render/public/<id>/images/<itemId>.<ext> and records 'image' (staticFile path)
plus 'imageQuery' back into events.json.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import requests

from common import CFG, list_videos, public_dir, read_json, stage_done, video_id_for, work_dir, write_json

UA = {"User-Agent": "Mozilla/5.0 (auto-editing-pipeline)"}


def serpapi_image(query: str) -> str | None:
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        raise SystemExit("SERPAPI_KEY not set. Add to .env, or set images.engine: openverse in config.yaml.")
    r = requests.get(
        "https://serpapi.com/search.json",
        params={"engine": "google_images", "q": query, "api_key": key, "num": 10},
        timeout=CFG["images"]["timeout_sec"],
    )
    r.raise_for_status()
    for img in r.json().get("images_results", []):
        url = img.get("original") or img.get("thumbnail")
        if url:
            return url
    return None


def openverse_image(query: str) -> str | None:
    """Free CC-licensed fallback; no API key required."""
    r = requests.get(
        "https://api.openverse.org/v1/images/",
        params={"q": query, "page_size": 5, "license_type": "commercial"},
        headers=UA, timeout=CFG["images"]["timeout_sec"],
    )
    r.raise_for_status()
    for res in r.json().get("results", []):
        if res.get("url"):
            return res["url"]
    return None


def find_image_url(query: str) -> str | None:
    engine = CFG["images"]["engine"]
    if engine == "serpapi":
        return serpapi_image(query)
    return openverse_image(query)


def download(url: str, dest_noext: Path) -> Path | None:
    try:
        r = requests.get(url, headers=UA, timeout=CFG["images"]["timeout_sec"], stream=True)
        r.raise_for_status()
    except Exception as e:  # noqa: BLE001
        print(f"        download failed: {e}")
        return None
    ctype = r.headers.get("content-type", "")
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}.get(
        ctype.split(";")[0].strip(), ".jpg"
    )
    dest = dest_noext.with_suffix(ext)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    return dest


def images_one(video_id: str, force: bool = False) -> None:
    wd = work_dir(video_id)
    events_path = wd / "events.json"
    if not events_path.exists():
        print(f"[s4] {video_id}: no events, skip")
        return
    events = read_json(events_path)
    img_dir = public_dir(video_id) / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    for it in events.get("items", []):
        if it.get("image") and not force:
            continue
        query = it.get("query") or it["name"]
        print(f"[s4] {video_id}: '{query}'")
        try:
            url = find_image_url(query)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"        search failed: {e}")
            url = None
        if not url:
            print("        no image found")
            continue
        dest = download(url, img_dir / it["id"])
        if dest:
            it["image"] = f"{video_id}/images/{dest.name}"  # relative to render/public
            it["imageSource"] = url
    write_json(events_path, events)


def main(argv: list[str]) -> None:
    force = "--force" in argv
    targets = [a for a in argv if not a.startswith("--")]
    ids = targets or [video_id_for(v) for v in list_videos()]
    for vid in ids:
        if not stage_done(vid, "events.json"):
            continue
        images_one(vid, force=force)


if __name__ == "__main__":
    main(sys.argv[1:])
