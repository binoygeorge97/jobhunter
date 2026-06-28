# pipeline/dedup.py
"""
Deduplicates job listings against previously seen jobs.
Persists state in data/seen_jobs.json.
On first run, the file does not exist — handle gracefully.
"""

import hashlib
import json
from pathlib import Path

SEEN_JOBS_PATH = Path("data/seen_jobs.json")


def _load_seen() -> set[str]:
    """Load set of previously seen job hashes."""
    if not SEEN_JOBS_PATH.exists():
        return set()
    with open(SEEN_JOBS_PATH) as f:
        data = json.load(f)
    return set(data.get("seen_hashes", []))


def _save_seen(seen: set[str]) -> None:
    """Persist the seen set to disk."""
    SEEN_JOBS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SEEN_JOBS_PATH, "w") as f:
        json.dump({"seen_hashes": list(seen)}, f, indent=2)


def _job_hash(job: dict) -> str:
    """Unique fingerprint for a job: company + title hash."""
    raw = f"{job.get('company', '').lower().strip()}|{job.get('title', '').lower().strip()}"
    return hashlib.md5(raw.encode()).hexdigest()


def filter_new_jobs(jobs: list[dict]) -> list[dict]:
    """
    Remove jobs already seen in previous runs.
    Returns only NEW jobs.
    Also updates the seen_jobs.json with this run's hashes.
    """
    seen = _load_seen()
    new_jobs = []

    for job in jobs:
        h = _job_hash(job)
        if h not in seen:
            new_jobs.append(job)
            seen.add(h)

    _save_seen(seen)
    print(f"[Dedup] {len(new_jobs)} new jobs from {len(jobs)} total (skipped {len(jobs) - len(new_jobs)} seen)")
    return new_jobs
