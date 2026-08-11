from __future__ import annotations

import argparse
import html
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from statistics import mean

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.metrics import percentile


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Render the six-panel dashboard from JSONL logs")
    parser.add_argument("--logs", type=Path, default=REPO_ROOT / "data" / "logs.jsonl")
    parser.add_argument(
        "--output",
        type=Path,
        default=REPO_ROOT / "submission" / "evidence" / "dashboard-runtime.html",
    )
    args = parser.parse_args()

    records = [
        json.loads(line)
        for line in args.logs.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    config = yaml.safe_load((REPO_ROOT / "config" / "dashboard.yaml").read_text(encoding="utf-8"))
    dashboard = config["dashboard"]
    latest = max((_timestamp(row["ts"]) for row in records), default=datetime.now(timezone.utc))
    start = latest - timedelta(minutes=dashboard["time_range_minutes"])
    window = [row for row in records if _timestamp(row["ts"]) >= start]
    responses = [row for row in window if row.get("event") == "response_sent"]
    requests = [row for row in window if row.get("event") == "request_received"]
    failures = [row for row in window if row.get("event") == "request_failed"]

    latencies = [int(row["latency_ms"]) for row in responses if row.get("latency_ms") is not None]
    costs = [float(row["cost_usd"]) for row in responses if row.get("cost_usd") is not None]
    quality = [float(row["quality_score"]) for row in responses if row.get("quality_score") is not None]
    tokens_in = sum(int(row.get("tokens_in") or 0) for row in responses)
    tokens_out = sum(int(row.get("tokens_out") or 0) for row in responses)
    error_rate = (len(failures) / len(requests) * 100) if requests else 0.0
    duration_minutes = max((latest - start).total_seconds() / 60, 1)

    values = {
        "latency": f"P50 {percentile(latencies, 50):.0f} · P95 {percentile(latencies, 95):.0f} · P99 {percentile(latencies, 99):.0f}",
        "traffic": f"{len(requests)} requests · {len(requests) / duration_minutes:.2f}/min",
        "errors": f"{error_rate:.2f}% · {len(failures)} failures",
        "cost": f"${sum(costs):.4f} total",
        "tokens": f"{tokens_in:,} input · {tokens_out:,} output",
        "quality": f"{mean(quality):.3f} average" if quality else "0.000 average",
    }

    cards = []
    for panel in dashboard["panels"]:
        threshold = panel["threshold"]
        cards.append(
            f"""
            <section class="card" id="{html.escape(panel['id'])}">
              <div class="eyebrow">{html.escape(panel['id'].upper())}</div>
              <h2>{html.escape(panel['title'])}</h2>
              <div class="value">{html.escape(values[panel['id']])}</div>
              <div class="threshold">SLO: {html.escape(str(threshold['aggregation']))}
                {html.escape(str(threshold['operator']))} {html.escape(str(threshold['value']))}
                {html.escape(panel['unit'])}</div>
              <code>{html.escape(panel['query'])}</code>
            </section>
            """.strip()
        )

    generated = datetime.now(timezone.utc).isoformat(timespec="seconds")
    body = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>{html.escape(dashboard['title'])}</title>
<style>
*{{box-sizing:border-box}} body{{margin:0;background:#08111f;color:#e7eefb;font-family:Segoe UI,Arial,sans-serif}}
main{{max-width:1360px;margin:auto;padding:36px}} header{{display:flex;justify-content:space-between;align-items:end;margin-bottom:24px}}
h1{{font-size:34px;margin:0 0 8px}} .meta,.eyebrow{{color:#8fa6c8;font-size:13px;letter-spacing:.08em}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}} .card{{min-height:245px;padding:22px;border:1px solid #263b59;border-radius:16px;background:linear-gradient(145deg,#101e32,#0b1728);box-shadow:0 14px 30px #03081280}}
h2{{font-size:18px;margin:10px 0 28px}} .value{{font-size:27px;font-weight:700;color:#63e6be;margin-bottom:24px}}
.threshold{{display:inline-block;background:#162b45;border:1px solid #315477;border-radius:999px;padding:7px 11px;color:#b9d5f4;font-size:12px}}
code{{display:block;margin-top:18px;color:#8fa6c8;font-size:11px;white-space:normal;line-height:1.5}}
.source{{margin-top:22px;color:#7187a7;font-size:12px}} @media(max-width:900px){{.grid{{grid-template-columns:1fr}}}}
</style></head><body><main>
<header><div><h1>{html.escape(dashboard['title'])}</h1><div class="meta">Runtime dashboard · real JSONL data</div></div>
<div class="meta">Last {dashboard['time_range_minutes']} min · refresh {dashboard['refresh_seconds']}s<br>{generated}</div></header>
<div class="grid">{''.join(cards)}</div>
<div class="source">Source: data/logs.jsonl · {len(window)} records · {len(responses)} completed responses</div>
</main></body></html>"""
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(body, encoding="utf-8")
    print(f"Dashboard rendered: {args.output}")
    print(f"Records in window: {len(window)}; responses: {len(responses)}")


if __name__ == "__main__":
    main()
