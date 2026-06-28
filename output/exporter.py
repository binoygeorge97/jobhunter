# output/exporter.py
"""
Writes final output to:
  data/results/YYYY-MM-DD_jobs.csv
  data/results/YYYY-MM-DD_jobs.json

CSV is the quick-review format (open in Excel/Sheets).
JSON is the full-fidelity format (for gap reporter and future runs).
"""

import csv
import json
from datetime import date
from pathlib import Path

RESULTS_DIR = Path("data/results")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

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

    sorted_jobs = sorted(
        jobs,
        key=lambda j: (0 if j.get("urgency") == "HIGH" else 1, -j.get("match_score", 0))
    )

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for job in sorted_jobs:
            row = dict(job)
            if isinstance(row.get("extracted_tech_stack"), list):
                row["extracted_tech_stack"] = ", ".join(row["extracted_tech_stack"])
            writer.writerow(row)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(sorted_jobs, f, indent=2, ensure_ascii=False)

    print(f"[Exporter] Wrote {len(sorted_jobs)} jobs")
    print(f"  CSV:  {csv_path}")
    print(f"  JSON: {json_path}")
    return csv_path, json_path
