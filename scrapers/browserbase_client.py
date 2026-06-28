# scrapers/browserbase_client.py
"""
Thin wrapper around Browserbase's Search API and Fetch API.
Also provides a Playwright session factory for complex pages.
"""

import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

BB_API_KEY = os.environ["BROWSERBASE_API_KEY"]
BB_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"]

SEARCH_ENDPOINT = "https://www.browserbase.com/v1/search"
FETCH_ENDPOINT = "https://www.browserbase.com/v1/fetch"
SESSIONS_ENDPOINT = "https://www.browserbase.com/v1/sessions"

HEADERS = {
    "X-BB-API-Key": BB_API_KEY,
    "Content-Type": "application/json",
}

MAX_RETRIES = 3
RATE_LIMIT_BACKOFF_SECONDS = 2


def _post_with_retry(endpoint: str, payload: dict, timeout: int) -> dict:
    """POST with retry on HTTP 429 (rate limit)."""
    last_exc: Exception | None = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(endpoint, headers=HEADERS, json=payload, timeout=timeout)
            if resp.status_code == 429:
                wait = RATE_LIMIT_BACKOFF_SECONDS * (2 ** attempt)
                print(f"[Browserbase] 429 rate-limited; sleeping {wait}s (attempt {attempt + 1}/{MAX_RETRIES})")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            return resp.json()
        except requests.RequestException as e:
            last_exc = e
            if attempt == MAX_RETRIES - 1:
                raise
            time.sleep(RATE_LIMIT_BACKOFF_SECONDS * (2 ** attempt))
    if last_exc:
        raise last_exc
    raise RuntimeError(f"Exhausted retries for {endpoint}")


def bb_search(query: str, num_results: int = 10) -> list[dict]:
    """
    Call Browserbase Search API.
    Returns list of {title, url, snippet} dicts.
    Raises on HTTP error.
    """
    payload = {
        "query": query,
        "results": num_results,
    }
    data = _post_with_retry(SEARCH_ENDPOINT, payload, timeout=30)
    return data.get("results", [])


def bb_fetch(url: str, text_only: bool = True) -> str:
    """
    Call Browserbase Fetch API to get rendered page content.
    Returns the page text (or HTML if text_only=False).
    """
    payload = {
        "url": url,
        "text": text_only,
    }
    data = _post_with_retry(FETCH_ENDPOINT, payload, timeout=45)
    return data.get("text", "") or data.get("html", "")


def create_bb_session() -> str:
    """
    Create a Browserbase browser session for Playwright automation.
    Returns the session connect URL.
    Use this for pages that require more complex interaction (pagination, auth).
    """
    payload = {
        "projectId": BB_PROJECT_ID,
        "browserSettings": {
            "fingerprint": {"browsers": ["chrome"], "devices": ["desktop"]},
        },
    }
    session = _post_with_retry(SESSIONS_ENDPOINT, payload, timeout=30)
    return session["connectUrl"]
