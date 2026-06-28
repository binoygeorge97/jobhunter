# CLAUDE.md — Anti-PLC Job Hunter Agent
### Build Instructions for Claude Code

---

## What You Are Building

A one-shot Python script you run manually when you want a fresh hit list. Each run:
1. Scrapes job listings from LinkedIn, Wellfound, YC Work at a Startup, and direct company careers pages using the **Browserbase** API
2. Filters listings through a kill switch (PLC/SCADA/manufacturing keywords) and a two-tier match scorer
3. Enriches each surviving listing with **ASI:One Pro** (Fetch.ai LLM) to produce a fit score, portfolio match, and recruiter outreach hook
4. Deduplicates against any listings already seen in previous runs (so re-running never produces duplicates)
5. Outputs a ranked CSV + JSON report to `data/results/`

The owner of this agent is Binoy George — a PhD EE candidate specializing in sensor fusion, autonomous navigation, and edge ML. The agent filters OUT industrial manufacturing roles and filters FOR robotics/autonomy/edge AI roles.

---

## Tech Stack

| Layer | Tool | Install |
|---|---|---|
| Language | Python 3.11+ | — |
| Browser Automation | Browserbase Python SDK + Playwright | `pip install browserbase playwright` then `playwright install chromium` |
| LLM / Per-listing Enrichment | ASI:One Pro via `asi1-ultra` | `pip install openai` — the `openai` package is used as an HTTP client only; ASI:One exposes an OpenAI-compatible API. No OpenAI subscription required. |
| LLM / Gap Report | Anthropic Claude API via `claude-haiku-4-5` | `pip install anthropic` — used only for the one-off gap reporter. ~$10 budget is more than enough. |
| Data Output | pandas | `pip install pandas` |
| HTTP | requests | `pip install requests` |
| Env vars | python-dotenv | `pip install python-dotenv` |
| Dedup storage | Built-in json | — |

---

## Project Directory Structure

Create exactly this structure before writing any code:

```
anti_plc_job_hunter/
├── CLAUDE.md                    ← this file
├── .env                         ← secrets (never commit)
├── .env.example                 ← template (commit this)
├── .gitignore
├── requirements.txt
├── main.py                      ← entry point; run this to start the agent
│
├── config/
│   ├── __init__.py
│   ├── keywords.py              ← kill switch words, tier 1/2 match words
│   ├── platforms.py             ← search queries, target URLs per platform
│   └── portfolio.py             ← Binoy's projects for ASI:One persistent context
│
├── scrapers/
│   ├── __init__.py
│   ├── browserbase_client.py    ← thin wrapper around Browserbase Search + Fetch APIs
│   ├── linkedin.py              ← LinkedIn-specific extraction logic
│   ├── wellfound.py             ← Wellfound-specific extraction logic
│   ├── yc_startups.py           ← YC Work at a Startup extraction
│   └── direct_careers.py        ← direct company /careers page fetcher
│
├── pipeline/
│   ├── __init__.py
│   ├── kill_switch.py           ← Pass 1: eliminate manufacturing roles
│   ├── scorer.py                ← Pass 2: tier 1/2 keyword scoring
│   ├── enricher.py              ← ASI:One enrichment per surviving listing
│   └── dedup.py                 ← deduplicate against seen_jobs.json
│
├── output/
│   ├── __init__.py
│   ├── exporter.py              ← write CSV and JSON results files
│   └── gap_reporter.py          ← optional gap analysis via ASI:One (run separately)
│
└── data/
    ├── seen_jobs.json            ← auto-created on first run; prevents duplicate listings across runs
    └── results/                  ← timestamped output files land here
```

---

## Environment Variables

Create `.env.example` with these keys (no values). User fills in `.env`:

```bash
# Browserbase
BROWSERBASE_API_KEY=
BROWSERBASE_PROJECT_ID=

# ASI:One Pro (Fetch.ai)
ASI_ONE_API_KEY=
ASI_ONE_BASE_URL=https://api.asi1.ai/v1
ASI_ONE_MODEL=asi1-mini
```

Create `.gitignore`:
```
.env
data/seen_jobs.json
data/results/
__pycache__/
*.pyc
.venv/
```

---

## requirements.txt

```
browserbase>=1.0.0
playwright>=1.44.0
openai>=1.30.0
pandas>=2.0.0
requests>=2.31.0
python-dotenv>=1.0.0
```

---

## Step-by-Step Build Order

Build files in this exact order. Each step depends on the previous.

---

### STEP 1 — `config/keywords.py`

This is the brain of the filter. Build it as Python constants, not hardcoded strings elsewhere.

```python
# config/keywords.py

# ─── PASS 1: KILL SWITCH ────────────────────────────────────────────────────
# Any listing containing these words (case-insensitive) is immediately discarded.
# ⚠️ Do NOT add "CNC", "embedded C", "motor control" — Binoy has legitimate
#    projects in those areas and should NOT kill roles that involve them.

KILL_SWITCH_KEYWORDS = [
    # Classic industrial automation — always kill
    "PLC",
    "Allen-Bradley",
    "Ladder Logic",
    "SCADA",
    "DCS",                     # Distributed Control Systems (oil/gas)
    "HMI programming",         # Human-Machine Interface in factory context
    "P&ID",                    # Piping & Instrumentation Diagram (process eng.)
    "ISA-88",                  # Batch manufacturing standard
    # Manufacturing/factory operations — kill (not design)
    "plant floor",
    "shop floor",
    "Six Sigma",               # Manufacturing optimization
    "injection molding",
    "press operator",
    "machine operator",
    "production line",
]

# ─── PASS 2: MATCH SCORING ───────────────────────────────────────────────────
# Tier 1: Binoy has hardware results to back these up. Worth 3 pts each.
TIER_1_KEYWORDS = [
    "UKF",
    "Unscented Kalman",
    "Kalman Filter",
    "Sensor Fusion",
    "ROS",
    "ROS2",
    "JAX",
    "FLAX",
    "Jetson",
    "edge inference",
    "UWB",
    "Ultra-Wideband",
    "LiDAR",
    "point cloud",
    "State Space",
    "LQR",
    "MATLAB",
    "Simulink",
    "localization",
    "autonomous navigation",
]

# Tier 2: Overlapping or adjacent skills. Worth 1 pt each.
TIER_2_KEYWORDS = [
    "Python",
    "NumPy",
    "PyTorch",
    "SLAM",
    "path planning",
    "embedded systems",
    "control theory",
    "Reinforcement Learning",
    "C++",
    "EKF",
    "Extended Kalman",
    "odometry",
    "perception",
    "GNC",
    "guidance navigation control",
    "UAV",
    "UGV",
    "drone",
    "autonomous vehicle",
    "edge computing",
    "neural network",
    "S4",
    "state space model",
]

# Company bonus: add 5 pts if the company is one of these.
PRIORITY_COMPANIES = [
    "Y Combinator", "YC",
    "NASA", "JPL", "Jet Propulsion",
    "Skydio", "Shield AI", "Joby", "Joby Aviation",
    "Anduril", "Aurora", "Aurora Innovation",
    "Zipline", "Wisk", "Wisk Aero",
    "Sarcos", "Boston Dynamics",
    "Physical Intelligence", "Figure AI", "1X Technologies",
    "Reliable Robotics", "Joby", "Archer Aviation",
]

# Minimum score to include in final output
MATCH_SCORE_THRESHOLD = 6
```

---

### STEP 2 — `config/platforms.py`

```python
# config/platforms.py

# ─── SEARCH QUERY CLUSTERS ───────────────────────────────────────────────────
# Each cluster is a (label, query_string) tuple.
# These are passed to Browserbase Search API.
# Run all 5 clusters in parallel using concurrent.futures.

SEARCH_CLUSTERS = [
    (
        "state_estimation",
        '"Sensor Fusion Engineer" OR "Kalman Filter Engineer" OR "State Estimation Engineer"',
    ),
    (
        "gnc_autonomy",
        '"GNC Engineer" OR "Guidance Navigation Control" OR "Autonomy Software Engineer"',
    ),
    (
        "robot_ml",
        '"Robot Learning Engineer" OR "Reinforcement Learning robotics" OR "learned control"',
    ),
    (
        "edge_ai",
        '("Jetson" OR "edge inference" OR "TensorRT") AND ("robotics" OR "autonomous")',
    ),
    (
        "control_systems",
        '"Control Systems Engineer" AND ("autonomous" OR "robotics" OR "UAV" OR "spacecraft")',
    ),
]

# ─── DIRECT CAREERS PAGE URLS ────────────────────────────────────────────────
# These companies rarely post to aggregators. Browserbase Fetch each directly.
# Add selector hints so the scraper knows where to look for job listings.

DIRECT_CAREERS_PAGES = [
    {
        "company": "Shield AI",
        "url": "https://shield.ai/careers/",
        "listing_selector": "a[href*='/careers/']",
    },
    {
        "company": "Skydio",
        "url": "https://www.skydio.com/jobs",
        "listing_selector": "a[href*='/jobs/']",
    },
    {
        "company": "Joby Aviation",
        "url": "https://www.jobyaviation.com/careers/",
        "listing_selector": "a[href*='jobs']",
    },
    {
        "company": "Wisk Aero",
        "url": "https://wisk.aero/careers/",
        "listing_selector": "a[href*='career']",
    },
    {
        "company": "Reliable Robotics",
        "url": "https://www.reliablerobotics.com/careers",
        "listing_selector": "a[href*='job']",
    },
    {
        "company": "Sarcos Robotics",
        "url": "https://www.sarcos.com/careers/",
        "listing_selector": "a[href*='career']",
    },
    {
        "company": "Anduril",
        "url": "https://www.anduril.com/open-roles/",
        "listing_selector": "a[href*='/open-roles/']",
    },
    {
        "company": "Physical Intelligence",
        "url": "https://www.physicalintelligence.company/careers",
        "listing_selector": "a[href*='job']",
    },
]

# ─── PLATFORM BASE URLS ──────────────────────────────────────────────────────
LINKEDIN_JOBS_BASE = "https://www.linkedin.com/jobs/search/?keywords={query}&f_TP=1"
WELLFOUND_BASE = "https://wellfound.com/jobs?q={query}&role=engineer"
YC_STARTUPS_BASE = "https://www.workatastartup.com/jobs?q={query}"

# Max search result pages to scrape per cluster per platform
MAX_PAGES_PER_CLUSTER = 3
```

---

### STEP 3 — `config/portfolio.py`

This is injected into every ASI:One enrichment call as persistent context. It must never be modified by the agent at runtime — it's read-only ground truth.

```python
# config/portfolio.py

PORTFOLIO_CONTEXT = """
You are analyzing job listings for Binoy George, a PhD candidate in Electrical Engineering 
at the University of Texas at Arlington (expected Spring 2027, CGPA 3.91/4.0).

=== BINOY'S PROJECTS (use these to match against job requirements) ===

PROJECT 1 — UWB Robot Localization
  What: Trilateration algorithm for robot localization in 2D and 3D space
  How: Python + ROS, Decawave UWB sensors (hardware), tested on stationary and moving robots
  Results: <20 cm indoor localization accuracy; potential for self-driving car nav
  Best for roles requiring: localization, UWB, indoor navigation, Python/ROS, sensor hardware

PROJECT 2 — Robot Localization via Unscented Kalman Filter (UKF)
  What: Sensor fusion fusing odometry + UWB using UKF to minimize individual sensor errors
  How: MATLAB/Simulink for UKF design; Python + ROS for robot + sensor control; turtlebot2i platform
  Results: 20% reduction in robot position error vs standalone UWB; significantly reduced odometry drift
  Best for roles requiring: UKF, EKF, sensor fusion, state estimation, SLAM-adjacent, MATLAB/Simulink, ROS

PROJECT 3 — Unmanned Vehicle System (Autonomous UGV)
  What: Autonomous ground vehicle with waypoint navigation and obstacle avoidance indoors and outdoors
  Sensors: LiDAR, Ultrasonic, GPS
  How: MATLAB/Simulink for Guidance-Navigation-Control (GNC); ROS for integration; Arduino for electrical
  Results: 100% outdoor waypoint success, 75% indoor waypoint success with obstacle avoidance
  Best for roles requiring: GNC, autonomous navigation, field robotics, UGV/UAS, sensor integration

PROJECT 4 — Jetson Xavier + Raspberry Pi Integrated System
  What: Edge robotics system combining computer vision (face detection) and motor control
  How: Jetson Xavier for CV/inference; Raspberry Pi for motor control; integrated into single system
  Best for roles requiring: edge ML, embedded robotics, Jetson, perception + actuation integration

PHD RESEARCH — Edge Resource Forecasting (Dell-sponsored)
  What: Hybrid predictive framework for edge compute resource usage forecasting
  How: Markov-based stochastic process + S4 neural networks + Predictive Confidence Modeling (PCM)
  Context: Graduate Research Assistant at UTA Research Institute
  Best for roles requiring: edge AI, S4/SSM models, predictive systems, ML for systems optimization

=== BINOY'S HARD SKILLS ===
Languages: Python (NumPy, Pandas), MATLAB/Simulink, C, JAX/FLAX, PyTorch, SimPy
Technologies: Control Theory (PID, LQR), System Dynamics, State Space Modeling, 
              Sensor Fusion (Kalman Filter/UKF), Discrete Event Simulation, Queueing Theory
Hardware: Jetson Xavier, Raspberry Pi, Arduino, Decawave UWB sensors, turtlebot2i

=== WHAT BINOY IS TARGETING ===
- Robotics / Autonomous Systems / Drone / AV companies
- Research-forward startups (YC-backed, defense tech, space)
- Roles involving: state estimation, GNC, sensor fusion, edge ML, control systems
- NOT interested in: PLC, SCADA, DCS, manufacturing automation, industrial controls
"""
```

---

### STEP 4 — `scrapers/browserbase_client.py`

```python
# scrapers/browserbase_client.py
"""
Thin wrapper around Browserbase's Search API and Fetch API.
Also provides a Playwright session factory for complex pages.
"""

import os
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
    resp = requests.post(SEARCH_ENDPOINT, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    data = resp.json()
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
    resp = requests.post(FETCH_ENDPOINT, headers=HEADERS, json=payload, timeout=45)
    resp.raise_for_status()
    data = resp.json()
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
    resp = requests.post(SESSIONS_ENDPOINT, headers=HEADERS, json=payload, timeout=30)
    resp.raise_for_status()
    session = resp.json()
    return session["connectUrl"]
```

---

### STEP 5 — `scrapers/linkedin.py`

```python
# scrapers/linkedin.py
"""
Scrapes LinkedIn Jobs search results for a given query.
Returns list of raw job dicts with: title, company, url, requirements_text,
recruiter_name, recruiter_linkedin.
"""

from scrapers.browserbase_client import bb_search, bb_fetch
from config.platforms import LINKEDIN_JOBS_BASE, MAX_PAGES_PER_CLUSTER
import urllib.parse
import re


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
        "requirements_text": text,   # full text; scorer will parse it
        "recruiter_name": _extract_recruiter_name(text),
        "recruiter_linkedin": _extract_recruiter_url(text),
        "posted_date": _extract_field(text, r"(?i)posted\s+(\d+\s+\w+\s+ago|\w+\s+\d+)"),
    }


def _extract_field(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""


def _extract_recruiter_name(text: str) -> str:
    # LinkedIn often surfaces the poster in text like "Posted by Jane Smith"
    match = re.search(r"(?i)posted by\s+([A-Za-z\s]+)", text)
    return match.group(1).strip() if match else ""


def _extract_recruiter_url(text: str) -> str:
    match = re.search(r"(https://www\.linkedin\.com/in/[a-z0-9\-]+)", text)
    return match.group(1) if match else ""
```

---

### STEP 6 — `scrapers/wellfound.py`

```python
# scrapers/wellfound.py
"""
Scrapes Wellfound (AngelList Talent) for startup robotics/autonomy roles.
Wellfound often has direct founder or recruiter emails visible on listings.
"""

from scrapers.browserbase_client import bb_search, bb_fetch
import re


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
        "recruiter_name": "",   # Wellfound may have founder name in text; ASI:One will extract
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
```

---

### STEP 7 — `scrapers/yc_startups.py`

```python
# scrapers/yc_startups.py
"""
Scrapes YC Work at a Startup. YC companies move fast — flag all results here
with is_yc=True for urgency scoring.
"""

from scrapers.browserbase_client import bb_search, bb_fetch
import re


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
        "is_yc": True,                      # Always True for this scraper
        "title": search_result.get("title", ""),
        "company": _extract_field(text, r"(?i)company[:\s]+([A-Za-z0-9\s]+)\n"),
        "requirements_text": text,
        "recruiter_name": "",
        "recruiter_linkedin": "",
        "posted_date": "",
        "company_stage": _extract_field(text, r"(?i)(seed|series [a-f]|pre-seed)"),
        "batch": _extract_field(text, r"(?i)(W\d{2}|S\d{2}|F\d{2})"),  # e.g. W24, S23
    }


def _extract_field(text: str, pattern: str) -> str:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else ""
```

---

### STEP 8 — `scrapers/direct_careers.py`

```python
# scrapers/direct_careers.py
"""
Fetches job listings directly from company /careers pages.
These companies rarely appear on aggregators.
Uses Browserbase Fetch to get rendered page content.
"""

from scrapers.browserbase_client import bb_fetch
from config.platforms import DIRECT_CAREERS_PAGES
import re


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
        text = bb_fetch(config["url"], text_only=False)  # Get HTML for URL extraction
    except Exception as e:
        print(f"[DirectCareers] Failed to fetch {config['url']}: {e}")
        return []

    # Extract all job URLs from the page
    # Pattern: look for links containing "job", "career", "role", "position"
    job_url_pattern = r'href="(https?://[^"]*(?:job|career|role|position|opening)[^"]*)"'
    job_urls = list(set(re.findall(job_url_pattern, text, re.IGNORECASE)))

    jobs = []
    for job_url in job_urls[:15]:   # Cap at 15 listings per company
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
            "is_priority_company": True,   # All companies in DIRECT_CAREERS_PAGES are priority
        })

    return jobs


def _extract_title(text: str) -> str:
    # Look for common job title patterns
    patterns = [
        r"(?i)^([A-Za-z\s\-/]+(?:engineer|scientist|researcher|lead|manager|analyst))",
        r"(?i)job title[:\s]+([^\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text[:500])  # Check first 500 chars
        if match:
            return match.group(1).strip()[:80]
    return text[:60].strip()
```

---

### STEP 9 — `pipeline/kill_switch.py`

```python
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
```

---

### STEP 10 — `pipeline/scorer.py`

```python
# pipeline/scorer.py
"""
Pass 2: Score each surviving listing against Tier 1 and Tier 2 keywords.
Adds match_score and matched_keywords to each job dict.
Filters out jobs below MATCH_SCORE_THRESHOLD.
"""

from config.keywords import TIER_1_KEYWORDS, TIER_2_KEYWORDS, PRIORITY_COMPANIES, MATCH_SCORE_THRESHOLD


def score_jobs(jobs: list[dict]) -> list[dict]:
    """Score all jobs. Return only those meeting the threshold."""
    scored = []
    for job in jobs:
        job = _score_single(job)
        scored.append(job)

    # Filter by threshold
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

    # Priority company bonus
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
```

---

### STEP 11 — `pipeline/dedup.py`

```python
# pipeline/dedup.py
"""
Deduplicates job listings against previously seen jobs.
Persists state in data/seen_jobs.json.
On first run, the file does not exist — handle gracefully.
"""

import json
import hashlib
import os
from pathlib import Path

SEEN_JOBS_PATH = Path("data/seen_jobs.json")


def _load_seen() -> set[str]:
    """Load set of previously seen job hashes."""
    if not SEEN_JOBS_PATH.exists():
        return set()
    with open(SEEN_JOBS_PATH, "r") as f:
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
```

---

### STEP 12 — `pipeline/enricher.py`

This is the most important file. Each surviving job gets a full ASI:One analysis.

```python
# pipeline/enricher.py
"""
Enriches each qualifying job listing using ASI:One Pro.
For each listing, ASI:One produces:
  - match_justification: why this scored as it did
  - best_portfolio_match: which of Binoy's projects best fits
  - recruiter_hook: one-sentence outreach opener
  - urgency: HIGH or NORMAL
  - extracted_tech_stack: clean list of technologies in the role
  - company_stage: inferred if not already set
  - is_yc: boolean

Uses strict JSON output mode.
"""

import os
import json
from openai import OpenAI
from config.portfolio import PORTFOLIO_CONTEXT
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ["ASI_ONE_API_KEY"],
    base_url=os.environ.get("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1"),
)
MODEL = os.environ.get("ASI_ONE_MODEL", "asi1-mini")

ENRICHMENT_SYSTEM_PROMPT = f"""
{PORTFOLIO_CONTEXT}

You are an AI assistant that analyzes job listings for Binoy George.
You must respond ONLY with valid JSON — no preamble, no markdown fences, no explanation.
The JSON must exactly match this schema:

{{
  "match_justification": "1-2 sentences explaining why this role scored as it did, referencing specific matching keywords",
  "best_portfolio_match": "Exact project name from the portfolio context that best matches this role. Choose from: UWB Robot Localization, UKF Sensor Fusion, Autonomous UGV, Jetson+Pi Edge System, Edge Resource Forecasting PhD",
  "recruiter_hook": "One sentence (max 30 words) Binoy can paste directly into a LinkedIn message to this recruiter. It must reference a specific result from his portfolio and connect it to a visible requirement in the job description.",
  "urgency": "HIGH or NORMAL. HIGH if: YC-backed company, or posting is less than 5 days old, or company is on the priority list.",
  "extracted_tech_stack": ["array", "of", "technologies", "explicitly", "mentioned", "in", "the", "job"],
  "company_stage": "seed / series-a / series-b / series-c+ / public / unknown",
  "is_yc": true or false
}}
"""


def enrich_job(job: dict) -> dict:
    """
    Call ASI:One to enrich a single job listing.
    Adds enrichment fields to the job dict in place.
    Returns the enriched job dict.
    """
    user_message = f"""
Job Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Source: {job.get('source', 'Unknown')}
Posted: {job.get('posted_date', 'Unknown')}
Current Match Score: {job.get('match_score', 0)}
Matched Keywords: {', '.join(job.get('matched_keywords', []))}

--- FULL JOB TEXT ---
{(job.get('requirements_text') or '')[:3000]}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": ENRICHMENT_SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            max_tokens=600,
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        # Strip any accidental markdown fences
        content = content.replace("```json", "").replace("```", "").strip()
        enrichment = json.loads(content)
        job.update(enrichment)

    except json.JSONDecodeError as e:
        print(f"[Enricher] JSON parse failed for {job.get('url')}: {e}")
        job["match_justification"] = "Enrichment parse failed"
        job["recruiter_hook"] = ""
        job["urgency"] = "NORMAL"
        job["extracted_tech_stack"] = []

    except Exception as e:
        print(f"[Enricher] ASI:One call failed for {job.get('url')}: {e}")

    return job


def enrich_all_jobs(jobs: list[dict]) -> list[dict]:
    """Enrich all jobs. Processes sequentially to avoid rate limits."""
    enriched = []
    for i, job in enumerate(jobs):
        print(f"[Enricher] Enriching {i+1}/{len(jobs)}: {job.get('title')} @ {job.get('company')}")
        enriched.append(enrich_job(job))
    return enriched
```

---

### STEP 13 — `output/exporter.py`

```python
# output/exporter.py
"""
Writes final output to:
  data/results/YYYY-MM-DD_jobs.csv
  data/results/YYYY-MM-DD_jobs.json

CSV is the quick-review format (open in Excel/Sheets).
JSON is the full-fidelity format (for gap reporter and future runs).
"""

import json
import csv
from pathlib import Path
from datetime import date

RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# Columns to include in CSV (in order)
CSV_COLUMNS = [
    "urgency",
    "match_score",
    "title",
    "company",
    "company_stage",
    "is_yc",
    "best_portfolio_match",
    "match_justification",
    "recruiter_hook",
    "recruiter_name",
    "recruiter_linkedin",
    "extracted_tech_stack",
    "source",
    "posted_date",
    "url",
]


def export_results(jobs: list[dict]) -> tuple[Path, Path]:
    """
    Write CSV and JSON outputs for this run.
    Returns (csv_path, json_path).
    """
    today = date.today().isoformat()
    csv_path = RESULTS_DIR / f"{today}_jobs.csv"
    json_path = RESULTS_DIR / f"{today}_jobs.json"

    # Sort: HIGH urgency first, then by match_score descending
    sorted_jobs = sorted(
        jobs,
        key=lambda j: (0 if j.get("urgency") == "HIGH" else 1, -j.get("match_score", 0))
    )

    # Write CSV
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for job in sorted_jobs:
            # Flatten tech stack list to string for CSV
            row = dict(job)
            if isinstance(row.get("extracted_tech_stack"), list):
                row["extracted_tech_stack"] = ", ".join(row["extracted_tech_stack"])
            writer.writerow(row)

    # Write JSON (full fidelity, all fields)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sorted_jobs, f, indent=2, ensure_ascii=False)

    print(f"[Exporter] Wrote {len(sorted_jobs)} jobs")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")
    return csv_path, json_path
```

---

### STEP 14 — `output/gap_reporter.py`

```python
# output/gap_reporter.py
"""
Resume gap analysis — run this manually after a few scrape runs.
Reads all saved JSON result files, aggregates tech stack data,
and calls ASI:One to compare against Binoy's resume keywords.
Run this separately: python -m output.gap_reporter
"""

import json
import os
from pathlib import Path
from collections import Counter
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.environ["ASI_ONE_API_KEY"],
    base_url=os.environ.get("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1"),
)
MODEL = os.environ.get("ASI_ONE_MODEL", "asi1-mini")

BINOY_RESUME_KEYWORDS = [
    "Python", "NumPy", "Pandas", "MATLAB", "Simulink", "C", "JAX", "FLAX", "PyTorch", "SimPy",
    "PID", "LQR", "UKF", "Kalman Filter", "Sensor Fusion", "State Space Modeling",
    "System Dynamics", "Discrete Event Simulation", "Queueing Theory",
    "ROS", "Jetson Xavier", "Raspberry Pi", "Arduino", "UWB", "Decawave",
    "LiDAR", "GPS", "Odometry", "Trilateration",
]

RESULTS_DIR = Path("data/results")


def run_gap_report() -> str:
    """Load all saved JSON results, aggregate tech stacks, call ASI:One for gap analysis."""
    all_tech_stacks = []
    for json_file in RESULTS_DIR.glob("*_jobs.json"):
        with open(json_file) as f:
            jobs = json.load(f)
        for job in jobs:
            stacks = job.get("extracted_tech_stack", [])
            if isinstance(stacks, list):
                all_tech_stacks.extend(stacks)

    if not all_tech_stacks:
        return "No data yet. Run the agent at least once first."

    freq = Counter(all_tech_stacks)
    top_50 = freq.most_common(50)
    top_50_str = "\n".join(f"  {skill}: {count} listings" for skill, count in top_50)

    prompt = f"""
Here are the top 50 most-required technical skills across all qualifying job listings 
that Binoy's job search agent has collected:

{top_50_str}

Here are the skills currently on Binoy's resume:
{', '.join(BINOY_RESUME_KEYWORDS)}

Please produce a gap analysis in three sections:
1. STRENGTHS: Skills in both the job listings AND on his resume — he should emphasize these
2. GAPS: Skills appearing frequently in job listings but NOT on his resume — worth adding if genuine
3. DEPRIORITIZE: Skills on his resume that rarely appear in these target roles

For each item in GAPS, note whether it's a genuine gap or whether he has adjacent skills he could reframe.
Keep the response concise and actionable.
"""

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        max_tokens=800,
    )
    report = response.choices[0].message.content
    print("\n=== RESUME GAP REPORT ===\n")
    print(report)

    # Save report
    report_path = RESULTS_DIR / "gap_report_latest.txt"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nSaved to {report_path}")
    return report


if __name__ == "__main__":
    run_gap_report()
```

---

### STEP 15 — `main.py`

```python
# main.py
"""
Anti-PLC Job Hunter — one-shot script.

Usage:
  python main.py

Scrapes LinkedIn, Wellfound, YC Work at a Startup, and direct company
careers pages, filters for autonomy/robotics/edge ML roles, enriches
each surviving listing with ASI:One, and writes a ranked CSV + JSON
to data/results/YYYY-MM-DD_jobs.csv.

Run again any time you want a fresh batch. Dedup prevents re-processing
listings already seen in prior runs.
"""

import concurrent.futures
import os
from dotenv import load_dotenv

load_dotenv()

from scrapers.linkedin import scrape_linkedin
from scrapers.wellfound import scrape_wellfound
from scrapers.yc_startups import scrape_yc_startups
from scrapers.direct_careers import scrape_direct_careers
from pipeline.kill_switch import apply_kill_switch
from pipeline.scorer import score_jobs
from pipeline.dedup import filter_new_jobs
from pipeline.enricher import enrich_all_jobs
from output.exporter import export_results
from config.platforms import SEARCH_CLUSTERS


def _scrape_cluster(cluster: tuple) -> list[dict]:
    """Scrape one search cluster across all three platforms."""
    label, query = cluster
    print(f"\n[Cluster: {label}] Scraping query: {query[:60]}...")
    results = []
    results.extend(scrape_linkedin(query))
    results.extend(scrape_wellfound(query))
    results.extend(scrape_yc_startups(query))
    print(f"[Cluster: {label}] Raw results: {len(results)}")
    return results


def run_full_pipeline() -> str:
    """
    Full pipeline: scrape → deduplicate → kill switch → score → enrich → export.
    Returns a summary string.
    """
    print("\n" + "="*60)
    print("ANTI-PLC JOB HUNTER — STARTING PIPELINE")
    print("="*60)

    # ── 1. SCRAPE ────────────────────────────────────────────────
    all_raw_jobs = []

    # Run search clusters in parallel (up to 5 concurrent)
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_scrape_cluster, cluster): cluster for cluster in SEARCH_CLUSTERS}
        for future in concurrent.futures.as_completed(futures):
            try:
                results = future.result()
                all_raw_jobs.extend(results)
            except Exception as e:
                print(f"[Scraper] Cluster failed: {e}")

    # Add direct careers pages (run separately, not clustered by query)
    all_raw_jobs.extend(scrape_direct_careers())

    print(f"\n[Pipeline] Total raw listings collected: {len(all_raw_jobs)}")

    # ── 2. DEDUP ─────────────────────────────────────────────────
    # Remove jobs seen in previous runs
    new_jobs = filter_new_jobs(all_raw_jobs)

    if not new_jobs:
        print("[Pipeline] No new listings found this run. Done.")
        return "0 new listings found"

    # ── 3. KILL SWITCH ───────────────────────────────────────────
    surviving, killed = apply_kill_switch(new_jobs)

    if not surviving:
        print("[Pipeline] All new listings were killed. Done.")
        return f"0 surviving listings ({len(killed)} killed)"

    # ── 4. SCORE ─────────────────────────────────────────────────
    qualifying = score_jobs(surviving)

    if not qualifying:
        print("[Pipeline] No listings met the match score threshold. Done.")
        return f"0 qualifying listings from {len(surviving)} surviving"

    # ── 5. ENRICH ────────────────────────────────────────────────
    enriched = enrich_all_jobs(qualifying)

    # ── 6. EXPORT ────────────────────────────────────────────────
    csv_path, json_path = export_results(enriched)

    summary = (
        f"{len(enriched)} qualifying jobs | "
        f"HIGH urgency: {sum(1 for j in enriched if j.get('urgency') == 'HIGH')} | "
        f"CSV: {csv_path}"
    )

    print(f"\n{'='*60}")
    print(f"PIPELINE COMPLETE: {summary}")
    print(f"{'='*60}\n")
    return summary


if __name__ == "__main__":
    run_full_pipeline()
```

---

## Final Build Checklist for Claude Code

Run these commands in order after building all files:

```bash
# 1. Create the project and install dependencies
mkdir anti_plc_job_hunter && cd anti_plc_job_hunter
pip install -r requirements.txt
playwright install chromium

# 2. Copy .env.example to .env and fill in your keys
cp .env.example .env
# Edit .env with: BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID, ASI_ONE_API_KEY

# 3. Create the data directory
mkdir -p data/results

# 4. Test a single scraper first
python -c "from scrapers.browserbase_client import bb_search; print(bb_search('sensor fusion engineer', 3))"

# 5. Run the full pipeline
python main.py

# 6. Check the output
ls data/results/

# 7. Optional: generate the resume gap report after 2+ runs
python -m output.gap_reporter
```

---

## Data Flow Diagram

```
python main.py
    │
    ▼
run_full_pipeline()
    │
    ├─► [PARALLEL] scrape_linkedin(query) × 5 clusters ──────────┐
    ├─► [PARALLEL] scrape_wellfound(query) × 5 clusters           │
    ├─► [PARALLEL] scrape_yc_startups(query) × 5 clusters         │
    └─► scrape_direct_careers() [8 companies]                     │
                                                                   ▼
                                                    ~150-300 raw job dicts
                                                                   │
                                                    pipeline/dedup.py
                                                    (remove previously seen)
                                                                   │
                                                    pipeline/kill_switch.py
                                                    (remove PLC/SCADA/manufacturing)
                                                    ~60-80% eliminated
                                                                   │
                                                    pipeline/scorer.py
                                                    (tier 1/2 keyword scoring)
                                                    (keep score >= 6 only)
                                                                   │
                                                    pipeline/enricher.py
                                                    (ASI:One per listing)
                                                    (adds: hook, match, urgency)
                                                                   │
                                                    output/exporter.py
                                                    data/results/YYYY-MM-DD_jobs.csv
                                                    data/results/YYYY-MM-DD_jobs.json
```

---

## Notes for Claude Code

- **Do not hardcode any API keys** — always read from `.env` via `os.environ[...]`
- **All `data/` files are gitignored** — do not commit them
- **The `config/portfolio.py` PORTFOLIO_CONTEXT string is sacred** — do not modify its content during enrichment calls; it is injected read-only
- **Error handling in scrapers**: always wrap `bb_fetch` calls in try/except and return `None` on failure — a few failed fetches are acceptable; a crash is not
- **ASI:One JSON parsing**: always strip markdown fences before `json.loads()` in the enricher, as models occasionally wrap output in backticks despite instructions
- **Rate limiting**: if the Browserbase API returns 429, add `time.sleep(2)` retry logic in `browserbase_client.py`
- **First run**: `seen_jobs.json` will not exist — `dedup.py` creates it automatically
- **Wellfound and YC** may change their URL structures — if search results return 0, update the `site:` prefix in the search query
