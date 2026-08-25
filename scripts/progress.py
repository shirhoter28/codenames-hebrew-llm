"""Progress, metrics and refreshed figures for a run that is still going.

    python scripts/progress.py results/<run_id> --report

`raw.jsonl` is flushed per game and `boards.json` / `config.yaml` are written
before the first game starts, so a run can be reported on at any point. Prints
a compact status block; `--report` also regenerates report.md and figures/.

Designed to be driven on an interval, e.g. under a watcher every 2 hours.
"""

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

import yaml  # noqa: E402

def _expected_games(config: dict) -> int:
    """Denominator for the progress bar, from the run's own config.yaml.

    Read as plain YAML rather than through `load_config`: that validates a
    config for *running*, and rejects retired board styles — so a run started
    before a style was retired could not be reported on while it was still
    going, which is exactly when progress matters.
    """
    guessers = config.get("guesser_models") or [config.get("guesser_model")]
    total = (
        len(config["models"])
        * len(guessers)
        * len(config["codemaster_prompt_methods"])
        * len(config.get("count_constraints") or [None])
        * len(config["board_styles"])
        * config["n_boards"]
        * config.get("n_trials", 1)
    )
    return total


def status(run_dir: Path, refresh_report: bool = False) -> str:
    rows = [
        json.loads(line)
        for line in (run_dir / "raw.jsonl").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        return f"[{run_dir.name}] no games recorded yet"

    config = yaml.safe_load((run_dir / "config.yaml").read_text(encoding="utf-8"))
    total = _expected_games(config)
    done = len(rows)
    meta = json.loads((run_dir / "run_meta.json").read_text(encoding="utf-8"))
    workers = meta.get("max_workers", 1)

    # Throughput from wall-clock span, not summed durations: games overlap.
    # Throughput comes from a TRAILING WINDOW, not from the whole run. A resumed
    # run's earliest game may be days old and separated by an idle gap, so
    # measuring from it understates the rate and inflates the ETA for the rest
    # of the run — which is exactly when the ETA is being relied on.
    # A "leg" is a stretch of continuous work. A resumed run has several,
    # separated by however long it sat idle; averaging across the gap is what
    # produced a 434-hour ETA on a run doing 120 games/h.
    GAP_MINUTES = 15
    timed = sorted(
        (
            (
                datetime.fromisoformat(r["started_at"]),
                datetime.fromisoformat(r["started_at"])
                + timedelta(seconds=r.get("duration_s") or 0),
            )
            for r in rows if r.get("started_at")
        ),
        key=lambda pair: pair[0],
    )
    span_h = eta = None
    if timed:
        leg_start = 0
        for i in range(1, len(timed)):
            if (timed[i][0] - timed[i - 1][1]).total_seconds() > GAP_MINUTES * 60:
                leg_start = i
        recent = timed[leg_start:]
        finish = datetime.now(timezone.utc) if done < total else max(e for _, e in recent)
        span_h = (finish - min(s for s, _ in recent)).total_seconds() / 3600
        total_elapsed_h = (finish - timed[0][0]).total_seconds() / 3600
        if span_h > 0 and done < total:
            eta = datetime.now(timezone.utc) + timedelta(
                hours=(total - done) / (len(recent) / span_h)
            )

    lines = [
        f"[{run_dir.name}] {done:,}/{total:,} games ({done/total:.1%}) "
        f"at {workers} workers"
    ]
    if span_h:
        rate = len(recent) / span_h
        provisional = " ~provisional" if len(recent) < 20 else ""
        lines.append(
            f"  elapsed {total_elapsed_h:.1f} h | {rate:.1f} games/h "
            f"(this leg: {len(recent)} games{provisional}) | "
            + (f"ETA {eta:%Y-%m-%d %H:%M} UTC ({(total-done)/rate:.1f} h left)"
               if eta else "complete")
        )

    outcomes = Counter(r.get("outcome") or r.get("status") for r in rows)
    lines.append("  outcomes: " + ", ".join(f"{k} {v}" for k, v in outcomes.most_common()))

    # Anything that is not a played-out game is the thing worth catching early.
    broken = sum(v for k, v in outcomes.items()
                 if k not in ("win", "loss"))
    if broken:
        lines.append(f"  !! {broken} game(s) did not play out "
                     f"({broken/done:.1%}) — check terminal_error")

    # Codemaster compliance per constraint arm: the M4-specific risk.
    agg = defaultdict(lambda: [0, 0])
    for r in rows:
        a = agg[r.get("count_constraint") or "free"]
        a[0] += r.get("codemaster_attempts") or 0
        a[1] += r.get("codemaster_rejected") or 0
    comp = "  cm compliance: " + "  ".join(
        f"{arm}={((a[0]-a[1])/a[0] if a[0] else float('nan')):.3f}"
        for arm, a in sorted(agg.items())
    )
    lines.append(comp)

    # Per-model call latency: a model slowing down with flat rejections means
    # the provider is throttling, which otherwise reads as non-compliance.
    #
    # Scoped to the current leg AND split by prompt method. Cumulative,
    # method-pooled latency drifts as the method mix changes — translate_pipeline
    # runs ~7.6 s/call against strong_hebrew's ~4.2 — so a run moving from one
    # to the other looks exactly like a throttle. Splitting removes that.
    leg_rows = rows[-len(recent):] if timed else rows
    per = defaultdict(lambda: [0.0, 0])
    for r in leg_rows:
        key = (r.get("method"), r["model"])
        per[key][0] += r.get("duration_s") or 0
        per[key][1] += (r.get("codemaster_attempts") or 0) + (r.get("guesser_attempts") or 0)
    for method in sorted({k[0] for k in per}):
        cells = "  ".join(
            f"{m.split('/')[-1]}={(d/c if c else float('nan')):.1f}"
            for (mt, m), (d, c) in sorted(per.items()) if mt == method
        )
        lines.append(f"  s/call [{method}]: {cells}")

    if refresh_report and done >= 3:
        result = subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "report.py"), str(run_dir)],
            capture_output=True, text=True,
        )
        lines.append(
            f"  report refreshed: {run_dir}/report.md"
            if result.returncode == 0
            else f"  report FAILED: {result.stderr.strip().splitlines()[-1:]}"
        )
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--report", action="store_true",
                        help="also regenerate report.md and figures/")
    args = parser.parse_args(argv)
    print(status(args.run_dir, refresh_report=args.report), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
