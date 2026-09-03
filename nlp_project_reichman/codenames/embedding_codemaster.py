"""Embedding codemaster (Kim et al. 2019 style).

Candidate clues are the first ``candidate_limit`` keys of the embedding table
(word2vec dumps are typically frequency-sorted). That is a Kim-style fixed
vocabulary, not a separate Hebrew frequency list and not “nearest neighbors of
targets only.” Those alternatives can be swapped later.

A (clue, target subset) is safe when::

    min similarity to intended targets > max similarity to bad words
    and min similarity to intended targets >= threshold

Default threshold is 0.4 after a small seed comparison (0.2 was too aggressive).

Bad words are remaining blue, civilian, and assassin cards.

Larger safe target sets are preferred. Among the same size, higher min-target
similarity wins. If no remaining board word is in-vocab, this raises rather
than skipping. If no safe clue exists, this raises ``RuntimeError``.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

from codenames.board import ROLE_ASSASSIN, ROLE_BLUE, ROLE_CIVILIAN, ROLE_RED
from codenames.embeddings import ConcatenatedEmbeddings, EmbeddingModel, OutOfVocabularyError
from codenames.players import Codemaster
from codenames.validity import check_clue

DEFAULT_THRESHOLD = 0.4  # chosen after comparing 0.2 / 0.4 / 0.5 / 0.6 on a few seeds
DEFAULT_CANDIDATE_LIMIT = 20_000


def looks_like_hebrew_token(word: str) -> bool:
    return any("א" <= ch <= "ת" for ch in word)


def is_safe_clue(
    min_target: float,
    max_bad: float,
    threshold: float,
) -> bool:
    """Separate from search so later experiments can change the rule."""
    return min_target > max_bad and min_target >= threshold


@dataclass(frozen=True)
class ClueChoice:
    clue: str
    targets: tuple[str, ...]
    min_target: float
    max_bad: float


def _bad_words(remaining_by_role: dict[str, list[str]]) -> list[str]:
    return (
        list(remaining_by_role.get(ROLE_BLUE, []))
        + list(remaining_by_role.get(ROLE_CIVILIAN, []))
        + list(remaining_by_role.get(ROLE_ASSASSIN, []))
    )


def choose_clue(
    model: EmbeddingModel,
    reds: list[str],
    bads: list[str],
    threshold: float = DEFAULT_THRESHOLD,
    candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
    clue_must_be_in: EmbeddingModel | None = None,
    skip_board_words: list[str] | None = None,
) -> ClueChoice:
    """Search for a safe clue. Raises if any *played* board word is OOV or none is safe.

    ``skip_board_words`` (Shir boards only): those cards stay illegal as clues
    but are left out of cosine (reds in this set still raise). Official games
    leave this unset.
    """
    if not reds:
        raise RuntimeError("No remaining red words to clue")

    skip = set(skip_board_words or ())
    skipped_reds = [word for word in reds if word in skip]
    if skipped_reds:
        raise OutOfVocabularyError(*skipped_reds)

    play_reds = [word for word in reds if word not in skip]
    play_bads = [word for word in bads if word not in skip]
    remaining = list(reds) + list(bads)
    missing = [word for word in play_reds + play_bads if not model.contains(word)]
    if missing:
        raise OutOfVocabularyError(*missing)

    remaining_set = set(remaining)
    candidates: list[str] = []
    for word in model.vocabulary(limit=candidate_limit):
        if word in remaining_set or not looks_like_hebrew_token(word):
            continue
        if clue_must_be_in is not None and not clue_must_be_in.contains(word):
            continue
        if not check_clue(word, 1, remaining).ok:
            continue
        candidates.append(word)

    if not candidates:
        raise RuntimeError("No legal candidate clues in the embedding vocabulary prefix")

    playable = play_reds + play_bads
    sims: dict[str, dict[str, float]] = {
        clue: {word: model.similarity(clue, word) for word in playable}
        for clue in candidates
    }

    for k in range(len(play_reds), 0, -1):
        best: ClueChoice | None = None
        for subset in combinations(play_reds, k):
            for clue in candidates:
                min_target = min(sims[clue][t] for t in subset)
                max_bad = max((sims[clue][b] for b in play_bads), default=-1.0)
                if not is_safe_clue(min_target, max_bad, threshold):
                    continue
                if best is None or min_target > best.min_target:
                    best = ClueChoice(clue, subset, min_target, max_bad)
        if best is not None:
            return best

    raise RuntimeError("No safe embedding clue for this board and threshold")


class EmbeddingCodemaster(Codemaster):
    name = "embedding"

    def __init__(
        self,
        embeddings: EmbeddingModel,
        threshold: float = DEFAULT_THRESHOLD,
        candidate_limit: int = DEFAULT_CANDIDATE_LIMIT,
        guesser_embeddings: EmbeddingModel | None = None,
        skip_board_words: list[str] | None = None,
    ) -> None:
        self.embeddings = embeddings
        self.guesser_embeddings = guesser_embeddings
        guesser_name = (
            guesser_embeddings.name if guesser_embeddings is not None else embeddings.name
        )
        both_concat = (
            embeddings.name == "concat"
            and guesser_embeddings is not None
            and guesser_embeddings.name == "concat"
        )
        cross = (
            guesser_embeddings is not None
            and guesser_embeddings.name != embeddings.name
        )
        if both_concat:
            self.model = "concat->concat"
        elif cross:
            self.model = f"{embeddings.name}->{guesser_name}"
        else:
            self.model = embeddings.name
        self.threshold = threshold
        self.candidate_limit = candidate_limit
        self.clue_must_be_in = guesser_embeddings if cross else None
        self.model_params = {
            "threshold": threshold,
            "candidate_limit": candidate_limit,
            "codemaster_model": embeddings.name,
            "guesser_model": guesser_name,
            "clues_restricted_to_guesser_vocab": self.clue_must_be_in is not None,
        }
        self.skip_board_words = list(skip_board_words or [])
        if self.skip_board_words:
            self.model_params["skip_board_words"] = list(self.skip_board_words)
        concat_src = embeddings if isinstance(embeddings, ConcatenatedEmbeddings) else None
        if concat_src is None and isinstance(guesser_embeddings, ConcatenatedEmbeddings):
            concat_src = guesser_embeddings
        if concat_src is not None:
            self.model_params["concat_parts"] = list(concat_src.part_names)
            self.model_params["concat_dims"] = list(concat_src.part_dims)
            self.model_params["concat_normalize_each"] = concat_src.normalize_each
        self.remaining_by_role: dict[str, list[str]] = {}
        self.last_targets: list[str] = []
        self.last_choice: ClueChoice | None = None
        self.last_targets = self.last_targets
        self.last_choice = self.last_choice

    def set_game_state(self, remaining_by_role: dict[str, list[str]]) -> None:
        self.remaining_by_role = remaining_by_role

    def get_clue(self) -> tuple[str, int]:
        choice = choose_clue(
            self.embeddings,
            reds=list(self.remaining_by_role.get(ROLE_RED, [])),
            bads=_bad_words(self.remaining_by_role),
            threshold=self.threshold,
            candidate_limit=self.candidate_limit,
            clue_must_be_in=self.clue_must_be_in,
            skip_board_words=self.skip_board_words,
        )
        self.last_choice = choice
        self.last_targets = list(choice.targets)
        self.last_targets = self.last_targets
        self.last_choice = self.last_choice
        return choice.clue, len(choice.targets)
