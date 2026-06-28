# scrapers/wellfound.py
"""
Scrapes Wellfound (AngelList Talent) for startup robotics/autonomy roles.
Wellfound often has direct founder or recruiter emails visible on listings.
"""

import re

from scrapers.browserbase_client import bb_fetch, bb_search


def scrape_wellfound(query: str) -> list[dict]:
    """Search Wellfound for a query, return structured job dicts."""
    search_query = f'site:wellfound.com/jobs {query} engineer'
    raw_results = bb_search(search_query, num_results=20)

    jobs = []
    for result in raw_results:
        url = result.get("url", "")
        if "wellfound.com" not in url:
            continue
        job = _fetch_wellfound_job(url, result)
        if job:
            jobs.append(job)
    return jobs


def _fetch_wellfound_job(url: str, search_result: dict) -> dict | None:
    try:
        text = bb_fetch(url, text_only=True)
    except Exception as e:
        print(f"[Wellfound] Failed to fetch {url}: {e}")
        return None

    if not text or len(text) < 100:
        return None

    return {
        "source": "wellfound",
        "url": url,
        "title": search_result.get("title", "").replace(" | Wellfound", "").strip(),
        "company": _extract_company(text, url),
        "requirements_text": text,
        "recruiter_name": "",
        "recruiter_linkedin": "",
        "posted_date": _extract_field(text, r"(?i)posted\s+(\d+\s+\w+\s+ago)"),
        "company_stage": _extract_field(text, r"(?i)(seed|series [a-f]|pre-seed|growth)"),
        "equity_range": _extract_field(text, r"(\d+\.?\d*%\s*–\s*\d+\.?\d*%)"),
    }


def _extract_company(text: str, url: str) -> str:
    match = re.search(r"wellfound\.com/company/([a-z0-9\-]+)", url)
    if match:
        return match.group(1).replace("-", " ").title()
    match = re.search(r"(?i)at\s+([A-Za-z0-9\s\.\-]+)\n", text)
    return match.group(1).strip() if match else ""


def _extract_field(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""
