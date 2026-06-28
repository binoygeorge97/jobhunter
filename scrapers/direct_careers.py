# scrapers/direct_careers.py
"""
Fetches job listings directly from company /careers pages.
These companies rarely appear on aggregators.
Uses Browserbase Fetch to get rendered page content.
"""

import re

from config.platforms import DIRECT_CAREERS_PAGES
from scrapers.browserbase_client import bb_fetch


def scrape_direct_careers() -> list[dict]:
    """Iterate all direct careers pages and extract job listings."""
    all_jobs = []
    for page_config in DIRECT_CAREERS_PAGES:
        jobs = _fetch_careers_page(page_config)
        all_jobs.extend(jobs)
        print(f"[DirectCareers] {page_config['company']}: found {len(jobs)} listings")
    return all_jobs


def _fetch_careers_page(config: dict) -> list[dict]:
    """Fetch a single careers page and extract linked job URLs."""
    try:
        text = bb_fetch(config["url"], text_only=False)
    except Exception as e:
        print(f"[DirectCareers] Failed to fetch {config['url']}: {e}")
        return []

    job_url_pattern = r'href="(https?://[^"]*(?:job|career|role|position|opening)[^"]*)"'
    job_urls = list(set(re.findall(job_url_pattern, text, re.IGNORECASE)))

    jobs = []
    for job_url in job_urls[:15]:
        job_text = ""
        try:
            job_text = bb_fetch(job_url, text_only=True)
        except Exception:
            pass

        if not job_text:
            continue

        jobs.append({
            "source": "direct_careers",
            "url": job_url,
            "company": config["company"],
            "title": _extract_title(job_text),
            "requirements_text": job_text,
            "recruiter_name": "",
            "recruiter_linkedin": "",
            "posted_date": "",
            "is_priority_company": True,
        })

    return jobs


def _extract_title(text: str) -> str:
    patterns = [
        r"(?i)^([A-Za-z\s\-/]+(?:engineer|scientist|researcher|lead|manager|analyst))",
        r"(?i)job title[:\s]+([^\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text[:500])
        if match:
            return match.group(1).strip()[:80]
    return text[:60].strip()
