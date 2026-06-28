# pipeline/kill_switch.py
"""
Pass 1: Remove any listing that contains manufacturing/industrial keywords.
Returns (kept: list[dict], killed: list[dict]) for logging purposes.
"""

from config.keywords import KILL_SWITCH_KEYWORDS


def apply_kill_switch(jobs: list[dict]) -> tuple[list[dict], list[dict]]:
    """
    Filter jobs through the kill switch.
    Returns (surviving_jobs, killed_jobs).
    """
    kept = []
    killed = []

    for job in jobs:
        text_to_check = (
            (job.get("title") or "") + " " +
            (job.get("requirements_text") or "")
        ).upper()

        triggered_by = None
        for keyword in KILL_SWITCH_KEYWORDS:
            if keyword.upper() in text_to_check:
                triggered_by = keyword
                break

        if triggered_by:
            job["kill_reason"] = triggered_by
            killed.append(job)
        else:
            kept.append(job)

    print(f"[KillSwitch] {len(kept)} kept, {len(killed)} killed from {len(jobs)} total")
    return kept, killed
