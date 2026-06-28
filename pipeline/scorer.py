# pipeline/scorer.py
"""
Pass 2: Score each surviving listing against Tier 1 and Tier 2 keywords.
Adds match_score and matched_keywords to each job dict.
Filters out jobs below MATCH_SCORE_THRESHOLD.
"""

from config.keywords import (
    MATCH_SCORE_THRESHOLD,
    PRIORITY_COMPANIES,
    TIER_1_KEYWORDS,
    TIER_2_KEYWORDS,
)


def score_jobs(jobs: list[dict]) -> list[dict]:
    """Score all jobs. Return only those meeting the threshold."""
    scored = []
    for job in jobs:
        job = _score_single(job)
        scored.append(job)

    qualifying = [j for j in scored if j["match_score"] >= MATCH_SCORE_THRESHOLD]
    qualifying.sort(key=lambda j: j["match_score"], reverse=True)

    print(f"[Scorer] {len(qualifying)} qualify (score >= {MATCH_SCORE_THRESHOLD}) from {len(scored)}")
    return qualifying


def _score_single(job: dict) -> dict:
    text = (
        (job.get("title") or "") + " " +
        (job.get("requirements_text") or "")
    ).upper()

    company = (job.get("company") or "").upper()

    score = 0
    matched = []

    for kw in TIER_1_KEYWORDS:
        if kw.upper() in text:
            score += 3
            matched.append(f"{kw}(T1)")

    for kw in TIER_2_KEYWORDS:
        if kw.upper() in text:
            score += 1
            matched.append(f"{kw}(T2)")

    is_priority = job.get("is_priority_company", False) or job.get("is_yc", False)
    for co in PRIORITY_COMPANIES:
        if co.upper() in company or co.upper() in text:
            score += 5
            is_priority = True
            break

    job["match_score"] = score
    job["matched_keywords"] = matched
    job["is_priority_company"] = is_priority

    return job
