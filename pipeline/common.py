"""Shared helpers: config, paths, video ids, ffprobe, JSON IO."""
from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
# Load .env first, then .env.local (local overrides / takes precedence).
load_dotenv(ROOT / ".env")
load_dotenv(ROOT / ".env.local", override=True)


def load_config() -> dict:
    with open(ROOT / "config.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


CFG = load_config()


def videos_dir() -> Path:
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
    exts = {".mov", ".mp4", ".mkv", ".webm"}
    return sorted(p for p in videos_dir().iterdir() if p.suffix.lower() in exts)


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
