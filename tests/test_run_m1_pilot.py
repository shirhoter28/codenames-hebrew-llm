import json
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


def test_main_wires_config_and_client_into_a_single_run(tmp_path, mocker):
    mocker.patch("codenames_heb.experiment.time.sleep")  # games make several LLM calls
    config_path = tmp_path / "tiny.yaml"
    config_path.write_text(
        "models: [dummy/model]\n"
        "codemaster_prompt_methods: [strong_hebrew]\n"
        "guesser_model: dummy/guesser\n"
        "board_styles: [dual_50]\n"
        "n_boards: 1\n"
        "n_trials: 1\n",
        encoding="utf-8",
    )
    # "קרן" (target) and "יחידה" (assassin) are words actually placed on the
    # board generated for this config (real word lists + seed=0 + dual_50,
    # deterministic). Guessing the assassin immediately ends the game in one
    # round, keeping this a simple smoke test of main()'s wiring rather than
    # a full game simulation.
    codemaster_json = {
        "clue": "בדיקה_קליט_ייחודי",
        "count": 1,
        "intended_targets": ["קרן"],
        "reasoning": "r",
    }
    guess_json = {"action": "guess", "word": "יחידה"}
    fake_client = FakeClient([codemaster_json, guess_json])
    results_dir = tmp_path / "results"

    run_dir = main(config_path=config_path, results_dir=results_dir, client=fake_client)

    assert (run_dir / "raw.jsonl").exists()
    assert (run_dir / "metrics.csv").exists()
    lines = (run_dir / "raw.jsonl").read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    row = json.loads(lines[0])
    assert row["outcome"] == "loss"
    # 1 codemaster call + 1 guess (the assassin, ending the game immediately)
    assert len(fake_client.calls) == 2
