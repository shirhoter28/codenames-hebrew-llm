import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from codenames_heb.experiment import LLMCodemaster, LLMGuesser, load_config, run_experiment
from codenames_heb.llm_client import OpenRouterClient
from codenames_heb.words import load_word_lists

DEFAULT_CONFIG_PATH = PROJECT_ROOT / "configs" / "m1_pilot.yaml"
DEFAULT_RESULTS_DIR = PROJECT_ROOT / "results"


def main(
    config_path: Path = DEFAULT_CONFIG_PATH,
    results_dir: Path = DEFAULT_RESULTS_DIR,
    client: OpenRouterClient | None = None,
    max_workers: int | None = None,
    resume_from: Path | None = None,
) -> Path:
    # A resumed run must continue under the design it started with, so its own
    # recorded config wins over whatever path was passed on the command line.
    if resume_from is not None:
        recorded = Path(resume_from) / "config.yaml"
        if recorded.exists():
            config_path = recorded
    config = load_config(config_path)
    # `load_config` caps the value in the file, but the override never went
    # through that check — so `--max-workers 40` silently bypassed the very
    # limit the flag's help text promises.
    if max_workers is not None and max_workers > len(config.models):
        raise SystemExit(
            f"--max-workers {max_workers} exceeds the number of models "
            f"({len(config.models)}). Concurrent games are spread across models "
            f"so they hit different providers; going wider stacks requests on "
            f"one provider, which is what triggers rate limiting."
        )
    word_lists = load_word_lists()
    client = client or OpenRouterClient()

    run_dir = run_experiment(
        config=config,
        word_lists=word_lists,
        make_codemaster=lambda model, method: LLMCodemaster(
            client=client, model=model, method=method
        ),
        make_guesser=lambda model: LLMGuesser(client=client, model=model),
        results_dir=results_dir,
        config_path=config_path,
        # None falls through to the config's own value.
        max_workers=max_workers,
        resume_from=resume_from,
    )
    print(f"Results written to {run_dir}")
    return run_dir


def _parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Run a Codenames-Hebrew experiment from a config file.",
        epilog=(
            "example: python scripts/run_m1_pilot.py configs/m2_tournament.yaml"
        ),
    )
    parser.add_argument(
        "config", nargs="?", type=Path, default=DEFAULT_CONFIG_PATH,
        help=f"experiment config (default: {DEFAULT_CONFIG_PATH.name})",
    )
    parser.add_argument(
        "--results-dir", type=Path, default=DEFAULT_RESULTS_DIR,
        help="where to write results/<run_id> (default: results/)",
    )
    parser.add_argument(
        "--resume", type=Path, default=None, metavar="RUN_DIR",
        help=(
            "continue an interrupted run: replays only the games missing from "
            "its raw.jsonl and appends to it. Uses that run's own config.yaml, "
            "so the design cannot drift between legs."
        ),
    )
    parser.add_argument(
        "--max-workers", type=int, default=None,
        help=(
            "games to run concurrently, overriding the config. Capped at the "
            "number of models, because tasks are dispatched round-robin by "
            "model so concurrent games hit different providers."
        ),
    )
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = _parse_args()
    main(
        config_path=args.config,
        results_dir=args.results_dir,
        max_workers=args.max_workers,
        resume_from=args.resume,
    )
