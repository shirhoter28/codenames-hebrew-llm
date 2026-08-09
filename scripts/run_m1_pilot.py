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
) -> Path:
    config = load_config(config_path)
    word_pool = load_word_lists().all
    client = client or OpenRouterClient()

    run_dir = run_experiment(
        config=config,
        word_pool=word_pool,
        make_codemaster=lambda model, method: LLMCodemaster(
            client=client, model=model, method=method
        ),
        make_guesser=lambda model: LLMGuesser(client=client, model=model),
        results_dir=results_dir,
    )
    print(f"Results written to {run_dir}")
    return run_dir


if __name__ == "__main__":
    main()
