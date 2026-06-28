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

from dotenv import load_dotenv

load_dotenv()

from config.platforms import SEARCH_CLUSTERS
from output.exporter import export_results
from pipeline.dedup import filter_new_jobs
from pipeline.enricher import enrich_all_jobs
from pipeline.kill_switch import apply_kill_switch
from pipeline.scorer import score_jobs
from scrapers.direct_careers import scrape_direct_careers
from scrapers.linkedin import scrape_linkedin
from scrapers.wellfound import scrape_wellfound
from scrapers.yc_startups import scrape_yc_startups


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
    print("\n" + "=" * 60)
    print("ANTI-PLC JOB HUNTER — STARTING PIPELINE")
    print("=" * 60)

    # ── 1. SCRAPE ────────────────────────────────────────────────
    all_raw_jobs = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_scrape_cluster, cluster): cluster for cluster in SEARCH_CLUSTERS}
        for future in concurrent.futures.as_completed(futures):
            try:
                results = future.result()
                all_raw_jobs.extend(results)
            except Exception as e:
                print(f"[Scraper] Cluster failed: {e}")

    all_raw_jobs.extend(scrape_direct_careers())

    print(f"\n[Pipeline] Total raw listings collected: {len(all_raw_jobs)}")

    # ── 2. DEDUP ─────────────────────────────────────────────────
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

    print(f"\n{'=' * 60}")
    print(f"PIPELINE COMPLETE: {summary}")
    print(f"{'=' * 60}\n")
    return summary


if __name__ == "__main__":
    run_full_pipeline()
