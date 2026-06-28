# scrapers/yc_startups.py
"""
Scrapes YC Work at a Startup. YC companies move fast — flag all results here
with is_yc=True for urgency scoring.
"""

import re

from scrapers.browserbase_client import bb_fetch, bb_search


def scrape_yc_startups(query: str) -> list[dict]:
    search_query = f'site:workatastartup.com {query}'
    raw_results = bb_search(search_query, num_results=20)

    jobs = []
    for result in raw_results:
        url = result.get("url", "")
        if "workatastartup.com" not in url:
            continue
        job = _fetch_yc_job(url, result)
        if job:
            jobs.append(job)
    return jobs


def _fetch_yc_job(url: str, search_result: dict) -> dict | None:
    try:
        text = bb_fetch(url, text_only=True)
    except Exception as e:
        print(f"[YC] Failed to fetch {url}: {e}")
        return None

    return {
        "source": "yc_startups",
        "url": url,
        "is_yc": True,
        "title": search_result.get("title", ""),
        "company": _extract_field(text, r"(?i)company[:\s]+([A-Za-z0-9\s]+)\n"),
        "requirements_text": text,
        "recruiter_name": "",
        "recruiter_linkedin": "",
        "posted_date": "",
        "company_stage": _extract_field(text, r"(?i)(seed|series [a-f]|pre-seed)"),
        "batch": _extract_field(text, r"(?i)(W\d{2}|S\d{2}|F\d{2})"),
    }


def _extract_field(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""
