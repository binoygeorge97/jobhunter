# output/gap_reporter.py
"""
Resume gap analysis — run this manually after a few scrape runs.
Reads all saved JSON result files, aggregates tech stack data,
and calls Anthropic Claude (claude-haiku-4-5) to compare against
Binoy's resume keywords.

Run separately: python -m output.gap_reporter
"""

import json
import os
from collections import Counter
from pathlib import Path

import anthropic
from dotenv import load_dotenv

load_dotenv()

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-haiku-4-5")

BINOY_RESUME_KEYWORDS = [
    "Python", "NumPy", "Pandas", "MATLAB", "Simulink", "C", "JAX", "FLAX", "PyTorch", "SimPy",
    "PID", "LQR", "UKF", "Kalman Filter", "Sensor Fusion", "State Space Modeling",
    "System Dynamics", "Discrete Event Simulation", "Queueing Theory",
    "ROS", "Jetson Xavier", "Raspberry Pi", "Arduino", "UWB", "Decawave",
    "LiDAR", "GPS", "Odometry", "Trilateration",
]

RESULTS_DIR = Path("data/results")


def run_gap_report() -> str:
    """Load all saved JSON results, aggregate tech stacks, call Claude for gap analysis."""
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

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    report = "".join(block.text for block in response.content if getattr(block, "type", None) == "text")

    print("\n=== RESUME GAP REPORT ===\n")
    print(report)

    report_path = RESULTS_DIR / "gap_report_latest.txt"
    with open(report_path, "w") as f:
        f.write(report)
    print(f"\nSaved to {report_path}")
    return report


if __name__ == "__main__":
    run_gap_report()
