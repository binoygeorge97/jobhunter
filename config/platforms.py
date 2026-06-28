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
