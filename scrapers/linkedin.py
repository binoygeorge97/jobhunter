# scrapers/linkedin.py
"""
Scrapes LinkedIn Jobs search results for a given query.
Returns list of raw job dicts with: title, company, url, requirements_text,
recruiter_name, recruiter_linkedin.
"""

import re

from scrapers.browserbase_client import bb_fetch, bb_search


def scrape_linkedin(query: str) -> list[dict]:
    """
    Use Browserbase Search to find LinkedIn job URLs, then Fetch each one.
    LinkedIn blocks direct scraping; Browserbase proxy + CAPTCHA solving handles this.
    """
    search_query = f'site:linkedin.com/jobs/view {query}'
    raw_results = bb_search(search_query, num_results=25)

    jobs = []
    for result in raw_results:
        url = result.get("url", "")
        if "linkedin.com/jobs/view" not in url:
            continue
        job = _fetch_linkedin_job(url)
        if job:
            jobs.append(job)

    return jobs


def _fetch_linkedin_job(url: str) -> dict | None:
    """Fetch a single LinkedIn job page and extract structured data."""
    try:
        text = bb_fetch(url, text_only=True)
    except Exception as e:
        print(f"[LinkedIn] Failed to fetch {url}: {e}")
        return None

    if not text or len(text) < 100:
        return None

    return {
        "source": "linkedin",
        "url": url,
        "title": _extract_field(text, r"(?i)(.*?)\s*\|\s*LinkedIn"),
        "company": _extract_field(text, r"(?i)at\s+([A-Za-z0-9\s\.\-]+)\s*\|"),
        "requirements_text": text,
        "recruiter_name": _extract_recruiter_name(text),
        "recruiter_linkedin": _extract_recruiter_url(text),
        "posted_date": _extract_field(text, r"(?i)posted\s+(\d+\s+\w+\s+ago|\w+\s+\d+)"),
    }


def _extract_field(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def _extract_recruiter_name(text: str) -> str:
    match = re.search(r"(?i)posted by\s+([A-Za-z\s]+)", text)
    return match.group(1).strip() if match else ""


def _extract_recruiter_url(text: str) -> str:
    match = re.search(r"(https://www\.linkedin\.com/in/[a-z0-9\-]+)", text)
    return match.group(1) if match else ""
