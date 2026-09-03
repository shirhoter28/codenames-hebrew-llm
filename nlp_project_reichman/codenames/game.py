"""Single-team Codenames game loop.

Only the red Codemaster and Guesser act. Play continues until all 9 red cards
are found (win) or the assassin is guessed (loss). Selecting a blue or civilian
card ends the current turn.

Stephenson et al. single-team score: number of turns if the team wins, else 25.
That scoring is recorded for later comparison; dummy games are not reported.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

from codenames.validity import (
    FALLBACK_CLUE,
    FALLBACK_CLUE_NUM,
    MAX_INVALID_CLUES,
    VALIDITY_VERSION,
    check_clue,
)
from codenames.board import (
    BLUE_COUNT,
    RED_COUNT,
    ROLE_ASSASSIN,
    ROLE_BLUE,
    ROLE_CIVILIAN,
    ROLE_RED,
    Board,
)
from codenames.players import Codemaster, Guesser

LOSS_SCORE = 25
MAX_TURNS = 25
OUTCOME_WIN = "win"
OUTCOME_ASSASSIN = "assassin"
OUTCOME_BLUE_CLEARED = "blue_cleared"


@dataclass
class GuessRecord:
    word: str
    role: str
    correct: bool


@dataclass
class InvalidClueAttempt:
    clue: str
    clue_num: int
    reason: str
    raw_response: str | None = None


@dataclass
class TurnRecord:
    turn: int
    clue: str
    clue_num: int
    guesses: list[GuessRecord] = field(default_factory=list)
    invalid_clue_attempts: list[InvalidClueAttempt] = field(default_factory=list)
    used_clue_fallback: bool = False
    prompt: str | None = None
    raw_response: str | None = None
    parsed_targets: list[str] | None = None
    remaining_red: list[str] | None = None
    min_target: float | None = None
    max_bad: float | None = None


@dataclass
class GameResult:
    mode: str
    seed: int
    wordpool: str
    codemaster: str
    guesser: str
    board_words: list[str]
    key_grid: list[str]
    turns: list[TurnRecord]
    outcome: str
    num_turns: int
    red_revealed: int
    blue_revealed: int
    civilian_revealed: int
    assassin_revealed: bool
    score: int
    finished_at: str
    validity_version: str = VALIDITY_VERSION
    prompt_version: str | None = None
    model: str | None = None
    model_params: dict | None = None

    def to_dict(self) -> dict:
        return asdict(self)


class SingleTeamGame:
    def __init__(
        self,
        board: Board,
        codemaster: Codemaster,
        guesser: Guesser,
        do_print: bool = True,
    ) -> None:
        self.board = board
        self.codemaster = codemaster
        self.guesser = guesser
        self.do_print = do_print
        self.revealed = [False] * len(board.words)

    def remaining_words(self) -> list[str]:
        return [w for w, done in zip(self.board.words, self.revealed) if not done]

    def remaining_by_role(self) -> dict[str, list[str]]:
        by_role = {
            ROLE_RED: [],
            ROLE_BLUE: [],
            ROLE_CIVILIAN: [],
            ROLE_ASSASSIN: [],
        }
        for word, role, done in zip(self.board.words, self.board.key_grid, self.revealed):
            if not done:
                by_role[role].append(word)
        return by_role

    def _print(self, text: str = "") -> None:
        if self.do_print:
            print(text)

    def _reveal(self, word: str) -> str:
        index = self.board.words.index(word)
        if self.revealed[index]:
            raise ValueError(f"Word already revealed: {word}")
        self.revealed[index] = True
        return self.board.key_grid[index]

    def _counts(self) -> tuple[int, int, int, bool]:
        red = blue = civilian = 0
        assassin = False
        for role, done in zip(self.board.key_grid, self.revealed):
            if not done:
                continue
            if role == ROLE_RED:
                red += 1
            elif role == ROLE_BLUE:
                blue += 1
            elif role == ROLE_CIVILIAN:
                civilian += 1
            elif role == ROLE_ASSASSIN:
                assassin = True
        return red, blue, civilian, assassin

    def _request_valid_clue(
        self, remaining: list[str]
    ) -> tuple[str, int, list[InvalidClueAttempt], bool]:
        attempts: list[InvalidClueAttempt] = []
        for _ in range(MAX_INVALID_CLUES):
            raw_clue, raw_num = self.codemaster.get_clue()
            checked = check_clue(raw_clue, raw_num, remaining)
            if checked.ok:
                return checked.clue, checked.clue_num, attempts, False
            attempts.append(
                InvalidClueAttempt(
                    clue=str(raw_clue),
                    clue_num=raw_num,
                    reason=checked.reason,
                    raw_response=getattr(self.codemaster, "last_raw_response", None),
                )
            )
            self.codemaster.notify_invalid(checked.reason)
            self._print(f"  Invalid clue ({raw_clue!r}, {raw_num}): {checked.reason}")
        self._print(
            f"  Too many invalid clues; using fallback ({FALLBACK_CLUE!r}, {FALLBACK_CLUE_NUM})"
        )
        return FALLBACK_CLUE, FALLBACK_CLUE_NUM, attempts, True

    def run(self) -> GameResult:
        self._print(self.board.format_codemaster_view())
        self._print()
        turn_records: list[TurnRecord] = []
        outcome: str | None = None

        while outcome is None and len(turn_records) < MAX_TURNS:
            remaining_roles = self.remaining_by_role()
            remaining = self.remaining_words()
            self.codemaster.set_game_state(remaining_roles)
            clue, clue_num, invalid_attempts, used_fallback = self._request_valid_clue(
                remaining
            )
            turn_index = len(turn_records) + 1
            choice = getattr(self.codemaster, "last_choice", None)
            record = TurnRecord(
                turn=turn_index,
                clue=clue,
                clue_num=clue_num,
                invalid_clue_attempts=invalid_attempts,
                used_clue_fallback=used_fallback,
                prompt=getattr(self.codemaster, "last_prompt", None),
                raw_response=getattr(self.codemaster, "last_raw_response", None),
                parsed_targets=list(getattr(self.codemaster, "last_targets", None) or [])
                or None,
                remaining_red=list(remaining_roles.get(ROLE_RED, [])),
                min_target=getattr(choice, "min_target", None),
                max_bad=getattr(choice, "max_bad", None),
            )

            self._print(f"--- Turn {turn_index} ---")
            self._print(f"Clue: ({clue}, {clue_num})")
            self._print(f"Remaining: {self.remaining_words()}")

            self.guesser.set_clue(clue, clue_num)
            must_guess = True
            while must_guess or self.guesser.keep_guessing():
                must_guess = False
                remaining = self.remaining_words()
                self.guesser.set_board(remaining)
                guess = self.guesser.get_answer()
                if guess not in remaining:
                    raise ValueError(f"Guess {guess!r} is not a remaining board word")

                role = self._reveal(guess)
                correct = role == ROLE_RED
                record.guesses.append(GuessRecord(word=guess, role=role, correct=correct))
                self._print(f"  Guess: {guess} -> {role}")

                red, blue, _, assassin = self._counts()
                if assassin:
                    outcome = OUTCOME_ASSASSIN
                    break
                if red >= RED_COUNT:
                    outcome = OUTCOME_WIN
                    break
                if blue >= BLUE_COUNT:
                    outcome = OUTCOME_BLUE_CLEARED
                    break
                if not correct:
                    break

                max_guesses = 10**9 if clue_num == 0 else clue_num + 1
                if len(record.guesses) >= max_guesses:
                    break

            turn_records.append(record)
            self._print()

        if outcome is None:
            raise RuntimeError(f"Game exceeded {MAX_TURNS} turns without finishing")

        red, blue, civilian, assassin = self._counts()
        score = turn_records[-1].turn if outcome == OUTCOME_WIN else LOSS_SCORE
        result = GameResult(
            mode="single_team",
            seed=self.board.seed,
            wordpool=self.board.wordpool,
            codemaster=self.codemaster.name,
            guesser=self.guesser.name,
            board_words=list(self.board.words),
            key_grid=list(self.board.key_grid),
            turns=turn_records,
            outcome=outcome,
            num_turns=len(turn_records),
            red_revealed=red,
            blue_revealed=blue,
            civilian_revealed=civilian,
            assassin_revealed=assassin,
            score=score,
            finished_at=datetime.now(timezone.utc).isoformat(),
            prompt_version=getattr(self.codemaster, "prompt_version", None),
            model=getattr(self.codemaster, "model", None),
            model_params=getattr(self.codemaster, "model_params", None),
        )
        self._print(f"Outcome: {outcome}  turns={result.num_turns}  score={score}")
        return result
