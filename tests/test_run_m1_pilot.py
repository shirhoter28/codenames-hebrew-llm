import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from run_m1_pilot import main  # noqa: E402


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def complete_json(self, model, system_prompt, user_prompt, max_retries=1):
        self.calls.append((model, system_prompt, user_prompt))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_main_wires_config_and_client_into_a_single_run(tmp_path):
    config_path = tmp_path / "tiny.yaml"
    config_path.write_text(
        "models: [dummy/model]\n"
        "codemaster_prompt_methods: [strong_hebrew]\n"
        "guesser_model: dummy/guesser\n"
        "board_style: standard\n"
        "n_boards: 1\n"
        "n_trials: 1\n",
        encoding="utf-8",
    )
    # "קשת" is a word actually placed on the board generated for this config
    # (word_pool from the real data + seed=0, deterministic); the brief's
    # original placeholder "ירח" is a valid dual word but isn't selected onto
    # this particular board, which raises a KeyError in Board.role_of.
    codemaster_json = {
        "clue": "בדיקה_קליט_ייחודי",
        "count": 1,
        "intended_targets": ["קשת"],
        "reasoning": "r",
    }
    guesser_json = {"guesses": ["קשת"]}
    fake_client = FakeClient([codemaster_json, guesser_json])
    results_dir = tmp_path / "results"

    run_dir = main(config_path=config_path, results_dir=results_dir, client=fake_client)

    assert (run_dir / "raw.jsonl").exists()
    assert (run_dir / "metrics.csv").exists()
    lines = (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    # 1 codemaster call + 1 guesser call
    assert len(fake_client.calls) == 2
