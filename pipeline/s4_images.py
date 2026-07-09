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


def serpapi_candidates(query: str) -> list[str]:
    key = os.environ.get("SERPAPI_KEY")
    if not key:
        raise SystemExit("SERPAPI_KEY not set. Add to .env.local, or set images.engine: openverse in config.yaml.")
    r = requests.get(
        "https://serpapi.com/search.json",
        params={"engine": "google_images", "q": query, "api_key": key, "num": 10},
        timeout=CFG["images"]["timeout_sec"],
    )
    r.raise_for_status()
    urls = []
    for img in r.json().get("images_results", []):
        url = img.get("original") or img.get("thumbnail")
        if url:
            urls.append(url)
    return urls


def openverse_candidates(query: str) -> list[str]:
    """Free CC-licensed fallback; no API key required."""
    r = requests.get(
        "https://api.openverse.org/v1/images/",
        params={"q": query, "page_size": 10, "license_type": "commercial"},
        headers=UA, timeout=CFG["images"]["timeout_sec"],
    )
    r.raise_for_status()
    return [res["url"] for res in r.json().get("results", []) if res.get("url")]


def find_candidates(query: str) -> list[str]:
    engine = CFG["images"]["engine"]
    return serpapi_candidates(query) if engine == "serpapi" else openverse_candidates(query)


def download(url: str, dest_noext: Path) -> Path | None:
    try:
        r = requests.get(url, headers=UA, timeout=CFG["images"]["timeout_sec"], stream=True)
        r.raise_for_status()
    except Exception as e:  # noqa: BLE001
        print(f"        download failed: {e}")
        return None
    ctype = r.headers.get("content-type", "").split(";")[0].strip().lower()
    if not ctype.startswith("image/"):
        print(f"        rejected: not an image ({ctype or 'unknown'})")
        return None
    ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp", "image/gif": ".gif"}.get(
        ctype, ".jpg"
    )
    dest = dest_noext.with_suffix(ext)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(8192):
            f.write(chunk)
    # Reject tiny/placeholder files (error pages, 1x1 trackers).
    if dest.stat().st_size < 2048:
        print(f"        rejected: too small ({dest.stat().st_size} bytes)")
        dest.unlink(missing_ok=True)
        return None
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
            candidates = find_candidates(query)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001
            print(f"        search failed: {e}")
            candidates = []
        # Try candidates in order until one downloads as a valid image.
        for url in candidates:
            dest = download(url, img_dir / it["id"])
            if dest:
                it["image"] = f"{video_id}/images/{dest.name}"  # relative to render/public
                it["imageSource"] = url
                break
        else:
            it["image"] = None
            print("        no usable image found")
    write_json(events_path, events)


def main(argv: list[str]) -> None:
    force = "--force" in argv
    targets = [a for a in argv if not a.startswith("--")]
    ids = targets or [video_id_for(v) for v in list_videos()]
    for vid in ids:
        if not stage_done(vid, "events.json"):
            continue
        try:
            images_one(vid, force=force)
        except SystemExit:
            raise
        except Exception as e:  # noqa: BLE001 — isolate per-video so the batch continues
            print(f"[s4] {vid}: FAILED ({type(e).__name__}: {e})")


if __name__ == "__main__":
    main(sys.argv[1:])
