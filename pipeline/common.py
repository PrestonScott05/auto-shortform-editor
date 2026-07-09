"""Shared helpers: config, paths, video ids, ffprobe, JSON IO."""
from __future__ import annotations

import json
import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# Load .env first, then .env.local (local overrides / takes precedence).
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)

# Source-directory override: env var default, or set per-run via --videos (parse_common_args).
_VIDEOS_OVERRIDE: str | None = os.environ.get("EDITAUTO_VIDEOS_DIR")


def set_videos_dir(path: str) -> None:
    global _VIDEOS_OVERRIDE
    _VIDEOS_OVERRIDE = path


def parse_common_args(argv: list[str]) -> list[str]:
    """Strip and apply shared flags (`--videos <path>` / `--videos=<path>`); return the rest."""
    out: list[str] = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--videos" and i + 1 < len(argv):
            set_videos_dir(argv[i + 1])
            i += 2
            continue
        if a.startswith("--videos="):
            set_videos_dir(a.split("=", 1)[1])
            i += 1
            continue
        out.append(a)
        i += 1
    return out


def load_config() -> dict:
    with open(ROOT / "config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CFG = load_config()


def videos_dir() -> Path:
    if _VIDEOS_OVERRIDE:
        p = Path(_VIDEOS_OVERRIDE)
        return p if p.is_absolute() else (ROOT / p)
    return ROOT / CFG["paths"]["videos_dir"]


def work_dir(video_id: str) -> Path:
    d = ROOT / CFG["paths"]["work_dir"] / video_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def out_dir() -> Path:
    d = ROOT / CFG["paths"]["out_dir"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def public_dir(video_id: str) -> Path:
    d = ROOT / CFG["paths"]["render_public"] / video_id
    d.mkdir(parents=True, exist_ok=True)
    return d


def video_id_for(path: Path) -> str:
    """Stable id = source filename stem (already a unique hash for this set)."""
    return path.stem


def list_videos() -> list[Path]:
    d = videos_dir()
    if not d.is_dir():
        raise SystemExit(f"Videos directory not found: {d}\nSet paths.videos_dir in config.yaml or pass --videos <path>.")
    exts = {".mov", ".mp4", ".mkv", ".webm"}
    return sorted(p for p in d.iterdir() if p.suffix.lower() in exts)


# Fields on editplan.layout — framing/caption presentation, never video-specific data
# (items, images, tiers, timings). Bulk tools only ever touch these.
LAYOUT_KEYS = [
    "videoScale", "videoTranslateY", "boardTopRatio", "captionBaselineRatio",
    "showCaptions", "captionColor", "captionActiveColor", "captionFont", "captionSize",
]


def patch_editplan_layout(video_id: str, patches: dict) -> dict:
    """Apply layout-only patches to both editplan copies (public = rendered, work =
    reference). Unknown keys are silently ignored. Returns the patch actually applied
    (empty dict if no editplan exists for this video)."""
    applied: dict = {}
    for base in (public_dir(video_id), work_dir(video_id)):
        p = base / "editplan.json"
        if not p.exists():
            continue
        plan = read_json(p)
        layout = plan.setdefault("layout", {})
        ok = {k: v for k, v in patches.items() if k in LAYOUT_KEYS}
        if not ok:
            continue
        layout.update(ok)
        write_json(p, plan)
        applied = ok
    return applied


@dataclass
class Probe:
    width: int
    height: int
    fps: float
    duration: float


def ffprobe(path: Path) -> Probe:
    def q(entries: str, stream: str | None) -> list[str]:
        cmd = ["ffprobe", "-v", "error"]
        if stream:
            cmd += ["-select_streams", stream]
        cmd += ["-show_entries", entries, "-of", "default=noprint_wrappers=1:nokey=1", str(path)]
        return subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.split()

    w, h = q("stream=width,height", "v:0")[:2]
    rate = q("stream=r_frame_rate", "v:0")[0]
    num, den = rate.split("/")
    fps = float(num) / float(den)
    dur = float(q("format=duration", None)[0])
    return Probe(int(w), int(h), fps, dur)


def read_json(p: Path) -> dict:
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(p: Path, data: dict) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def stage_done(video_id: str, filename: str) -> bool:
    return (work_dir(video_id) / filename).exists()
