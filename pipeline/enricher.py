# pipeline/enricher.py
"""
Enriches each qualifying job listing using ASI:One Pro (asi1-ultra).
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

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from config.portfolio import PORTFOLIO_CONTEXT

load_dotenv()

client = OpenAI(
    api_key=os.environ["ASI_ONE_API_KEY"],
    base_url=os.environ.get("ASI_ONE_BASE_URL", "https://api.asi1.ai/v1"),
)
MODEL = os.environ.get("ASI_ONE_MODEL", "asi1-ultra")

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
