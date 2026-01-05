"""
GitHub metadata refresh with rate-limit awareness, caching, and optional auth.

Usage:
  python tools/github_metadata_refresh.py

Behavior:
  - Reads repo URLs from ProjectMaelstrom/repo_analysis_report.json.
  - Caches metadata, ETag/Last-Modified in ProjectMaelstrom/github_cache.json
    with a TTL (default 6 hours) to minimize requests.
  - Uses conditional requests (If-None-Match / If-Modified-Since) when cached.
  - If rate limit is exhausted (remaining == 0), stops and prints next reset time.
  - Optional auth via GITHUB_TOKEN env var. Token is never logged or stored.
  - Safe to run unauthenticated; will operate in reduced mode.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Dict, Any, List

import requests

ROOT = Path(__file__).resolve().parents[1]
REPORT_PATH = ROOT / "ProjectMaelstrom" / "repo_analysis_report.json"
CACHE_PATH = ROOT / "ProjectMaelstrom" / "github_cache.json"
PLAN_PATH = ROOT / "project_integration_plan.json"
SOURCES_PATH = ROOT / "ProjectMaelstrom" / "wizard101_data_sources.json"

TTL_SECONDS = 6 * 60 * 60  # 6 hours
USER_AGENT = "wizard101-smart-trainer-metadata"
API_VER = "2022-11-28"


def utc_iso() -> str:
    return dt.datetime.utcnow().isoformat() + "Z"


def load_json(path: Path) -> Any:
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except Exception:
            return None


def save_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)


def build_session() -> requests.Session:
    sess = requests.Session()
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": API_VER,
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    sess.headers.update(headers)
    return sess


CANONICAL = [
    "https://github.com/Unity-Technologies/ml-agents",
    "https://github.com/Farama-Foundation/Gymnasium",
    "https://github.com/DLR-RM/stable-baselines3",
    "https://github.com/ray-project/ray",
    "https://github.com/deepmind/acme",
    "https://github.com/astooke/rlpyt",
    "https://github.com/DLR-RM/rl-baselines3-zoo",
    "https://github.com/openai/imitation",
    "https://github.com/opencv/opencv",
    "https://github.com/ultralytics/ultralytics",
    "https://github.com/ultralytics/yolov5",
    "https://github.com/facebookresearch/detectron2",
    "https://github.com/JaidedAI/EasyOCR",
    "https://github.com/tesseract-ocr/tesseract",
    "https://github.com/tzutalin/labelImg",
    "https://github.com/opencv/cvat",
    "https://github.com/heartexlabs/label-studio",
    "https://github.com/BoboTiG/python-mss",
    "https://github.com/AirtestProject/Airtest",
    "https://github.com/RaiMan/SikuliX1",
    "https://github.com/asweigart/pyautogui",
    "https://github.com/moses-palmer/pynput",
    "https://github.com/SerpentAI/SerpentAI",
    "https://github.com/ardamavi/Game-Bot",
    "https://github.com/botman99/ue4-unreal-automation-tool",
    "https://github.com/microsoft/agent-lightning",
    "https://github.com/michaelbianchi7/Game-AI",
    "https://github.com/recastnavigation/RecastNavigation",
    "https://github.com/networkx/networkx",
    "https://github.com/stonier/py_trees",
    "https://github.com/pytransitions/transitions",
    "https://github.com/wandb/wandb",
    "https://github.com/mlflow/mlflow",
    "https://github.com/streamlit/streamlit",
    "https://github.com/hoffstadt/DearPyGui",
    "https://github.com/PySimpleGUI/PySimpleGUI",
    "https://github.com/pyinstaller/pyinstaller",
    "https://github.com/electron-userland/electron-builder",
    "https://github.com/obsproject/obs-studio",
    "https://github.com/pallets/flask",
    "https://github.com/pytorch/vision",
    "https://github.com/google/dopamine",
    "https://github.com/danijar/dreamer",
    "https://github.com/rail-berkeley/d4rl",
    "https://github.com/vwxyzjn/cleanrl",
    "https://github.com/open-mmlab/mmdetection",
    "https://github.com/openai/CLIP",
    "https://github.com/learnables/learn2learn",
    "https://github.com/BehaviorTree/BehaviorTree.CPP",
    "https://github.com/CodeReclaimers/neat-python",
    "https://github.com/optuna/optuna",
    "https://github.com/albumentations-team/albumentations",
    "https://github.com/ffmpeg/ffmpeg",
    "https://github.com/apache/airflow",
]


def read_repo_urls() -> List[str]:
    data = load_json(REPORT_PATH) or {}
    urls = [r.get("html_url") for r in data.get("repos", []) if r.get("html_url")]
    if urls:
        return urls
    return CANONICAL


def rate_limit_status(resp: requests.Response) -> Dict[str, Any]:
    rem = resp.headers.get("X-RateLimit-Remaining")
    reset = resp.headers.get("X-RateLimit-Reset")
    limit = resp.headers.get("X-RateLimit-Limit")
    try:
        remaining = int(rem) if rem is not None else None
    except Exception:
        remaining = None
    try:
        reset_ts = int(reset) if reset is not None else None
    except Exception:
        reset_ts = None
    try:
        limit_int = int(limit) if limit is not None else None
    except Exception:
        limit_int = None
    reset_local = (
        dt.datetime.fromtimestamp(reset_ts).astimezone().isoformat()
        if reset_ts
        else None
    )
    return {
        "remaining": remaining,
        "reset_epoch": reset_ts,
        "reset_local": reset_local,
        "limit": limit_int,
    }


def should_use_cache(entry: Dict[str, Any]) -> bool:
    if not entry:
        return False
    ts = entry.get("_fetched_at")
    if not ts:
        return False
    try:
        fetched = dt.datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except Exception:
        return False
    age = (dt.datetime.utcnow() - fetched.replace(tzinfo=None)).total_seconds()
    return age < TTL_SECONDS


def fetch_repo(session: requests.Session, url: str, cache_entry: Dict[str, Any]) -> Dict[str, Any]:
    if "github.com" not in url:
        return {
            "owner": None,
            "name": None,
            "html_url": url,
            "error": "Non-GitHub entry",
        }
    owner, name = url.rstrip("/").split("/")[-2:]
    api_url = f"https://api.github.com/repos/{owner}/{name}"
    headers = {}
    if cache_entry:
        if etag := cache_entry.get("_etag"):
            headers["If-None-Match"] = etag
        if last_mod := cache_entry.get("_last_modified"):
            headers["If-Modified-Since"] = last_mod
    resp = session.get(api_url, headers=headers, timeout=15)
    rl = rate_limit_status(resp)
    if rl["remaining"] is not None and rl["remaining"] <= 0:
        # Rate limited: stop processing further
        return {"html_url": url, "error": "rate_limited", "_rate": rl}
    if resp.status_code == 304 and cache_entry:
        # Not modified; return cached content
        cached = dict(cache_entry)
        cached["_rate"] = rl
        return cached
    if resp.status_code != 200:
        return {
            "owner": owner,
            "name": name,
            "html_url": url,
            "error": f"HTTP {resp.status_code}",
            "_rate": rl,
        }
    meta = resp.json()
    desc = meta.get("description") or ""
    lic = meta.get("license") or {}
    entry = {
        "owner": owner,
        "name": name,
        "html_url": url,
        "description": meta.get("description"),
        "topics": meta.get("topics", []),
        "license": lic.get("spdx_id") or lic.get("name"),
        "stars": meta.get("stargazers_count"),
        "forks": meta.get("forks_count"),
        "open_issues": meta.get("open_issues_count"),
        "primary_language": meta.get("language"),
        "created_at": meta.get("created_at"),
        "pushed_at": meta.get("pushed_at"),
        "size_kb": meta.get("size"),
        "readme_excerpt": None,  # kept minimal to reduce calls
        "keywords": [],
        "scores": {},
        "scoring_basis": f"stars={meta.get('stargazers_count')}, activity={meta.get('pushed_at')}, desc_len={len(desc)}",
        "license_assessment": {},
        "recommendation": "study_and_extract_patterns",
        "suggested_next_steps": [],
        "_etag": resp.headers.get("ETag"),
        "_last_modified": resp.headers.get("Last-Modified"),
        "_fetched_at": utc_iso(),
        "_rate": rl,
    }
    return entry


def main() -> None:
    session = build_session()
    cache = load_json(CACHE_PATH) or {}
    urls = read_repo_urls()
    repos_out = []
    stopped_for_rate = False
    last_rate = None

    for url in urls:
        cache_entry = cache.get(url)
        if should_use_cache(cache_entry):
            entry = dict(cache_entry)
            entry["_from_cache"] = True
            repos_out.append(entry)
            continue
        entry = fetch_repo(session, url, cache_entry or {})
        last_rate = entry.get("_rate") or last_rate
        if entry.get("error") == "rate_limited":
            stopped_for_rate = True
            break
        repos_out.append(entry)
        # Respectful pacing: small sleep to avoid bursts
        time.sleep(0.3)

    # Summaries
    rec_counts = Counter([r.get("recommendation", "unknown") for r in repos_out])
    sorted_repos = sorted(
        [r for r in repos_out if isinstance(r.get("stars"), int)],
        key=lambda x: x.get("stars", 0),
        reverse=True,
    )
    summary = {
        "counts_by_recommendation": dict(rec_counts),
        "top_candidates": [r.get("html_url") for r in sorted_repos[:7]],
    }

    report = {
        "project": "Wizard101-smart-trainer-repo-analysis",
        "timestamp": utc_iso(),
        "repos": repos_out,
        "summary": summary,
    }
    save_json(REPORT_PATH, report)
    # Update cache from freshest entries
    cache_update = {r["html_url"]: r for r in repos_out if r.get("_fetched_at")}
    cache.update(cache_update)
    save_json(CACHE_PATH, cache)

    # Plan rebuild (lightweight)
    sources = load_json(SOURCES_PATH) or {}
    plan = {
        "project": "Wizard101 Smart Trainer integration plan",
        "timestamp": utc_iso(),
        "legal_ethics": {
            "status": "educational/experimental only",
            "rules": [
                "Public data or user-consented recordings only",
                "No live client/server interaction, no memory/net inspection",
                "Attribution required for third-party scripts/data",
            ],
        },
        "summary": summary,
        "data_sources_preview": sources.get("sources", [])[:5],
        "milestones_90d": [
            {"phase": "0-30d", "goals": ["Guardrails, HUD OCR baseline, catalog credits, diagnostics dashboard."]},
            {"phase": "31-60d", "goals": ["Behavior trees/FSM for SmartPlay, path graphs, build matrix, seed dataset workflow."]},
            {"phase": "61-90d", "goals": ["Optional detectors, offline RL experiments, UI polish, contributor guide."]},
        ],
    }
    save_json(PLAN_PATH, plan)

    if stopped_for_rate and last_rate:
        banner = {
            "status": "rate_limited",
            "next_retry_local": last_rate.get("reset_local"),
            "remaining": last_rate.get("remaining"),
        }
    else:
        banner = {"status": "ok", "repos_processed": len(repos_out)}
    print(json.dumps(banner, indent=2))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(1)
