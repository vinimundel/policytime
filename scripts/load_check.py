"""Measure two concurrent HTTP requests without treating cached latency as generation latency."""

import argparse
import json
import math
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx


def ask(client: httpx.Client, url: str, payload: dict) -> dict:
    started = time.perf_counter()
    response = client.post(f"{url.rstrip('/')}/api/ask", json=payload)
    elapsed = (time.perf_counter() - started) * 1000
    body = response.json()
    return {
        "status_code": response.status_code,
        "elapsed_ms": elapsed,
        "cached": body.get("run", {}).get("cached"),
        "mode": body.get("run", {}).get("mode"),
        "outcome": body.get("result", {}).get("status"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", required=True)
    parser.add_argument("--cases", type=Path, default=Path("evaluation/cases.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--interval", type=float, default=15, help="Seconds between request pairs")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Output already exists; preserve prior measurements.")
    if args.interval < 15:
        parser.error("Use at least 15 seconds between pairs to respect public rate limits.")
    cases = [json.loads(line) for line in args.cases.read_text().splitlines() if line.strip()]
    inputs = [case["input"] for case in cases if case["split"] == "development"]
    rows = []
    with httpx.Client(timeout=35) as client, ThreadPoolExecutor(max_workers=2) as pool:
        # Readiness warms connection setup, without adding a cached answer to this sample.
        client.get(f"{args.url.rstrip('/')}/readyz").raise_for_status()
        for offset in range(0, len(inputs), 2):
            pending = [
                pool.submit(ask, client, args.url, item) for item in inputs[offset : offset + 2]
            ]
            rows.extend(future.result() for future in pending)
            if offset + 2 < len(inputs):
                time.sleep(args.interval)
    uncached = sorted(
        row["elapsed_ms"] for row in rows if row["status_code"] == 200 and row["cached"] is False
    )
    p95 = uncached[math.ceil(len(uncached) * 0.95) - 1] if uncached else None
    report = {
        "concurrency": 2,
        "requests": rows,
        "uncached_p95_ms": p95,
        "limitations": (
            "Small mixed-outcome HTTP sample. Cache hits and errors excluded from latency "
            "percentile and retained in rows. Inspect answer-only latency separately "
            "before claiming a generation SLO."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(args.output)


if __name__ == "__main__":
    main()
