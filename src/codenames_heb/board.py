import random
from dataclasses import dataclass, field
from types import MappingProxyType

BOARD_SIZE = 25

ROLE_COUNTS: dict[str, int] = {
    "target": 9,
    "opponent": 8,
    "civilian": 7,
    "assassin": 1,
}

ROLE_TAGS: dict[str, str] = {
    "target": "TARGET",
    "opponent": "OPPONENT",
    "civilian": "CIVILIAN",
    "assassin": "ASSASSIN",
}

# Fraction of a board's 25 words drawn from the dual (ambiguous) pool. These are
# the levels of the experiment's independent variable: how much Hebrew lexical
# ambiguity a Codemaster has to work with. Three evenly spaced levels, so the
# dose-response curve can be tested for both a linear and a quadratic trend.
BOARD_STYLES: dict[str, float] = {
    "dual_0": 0.0,
    "dual_50": 0.5,
    "dual_100": 1.0,
}

# Styles no longer in the design but still readable. M2 and M3 ran `dual_80`;
# dropping it outright would make those boards ungeneratable and would silently
# drop their rows from `style_order`, so reports on them would quietly lose a
# quarter of the data. Retired styles can be regenerated and analysed, not
# designed into a new run.
RETIRED_BOARD_STYLES: dict[str, float] = {
    "dual_80": 0.8,
}

ALL_BOARD_STYLES: dict[str, float] = {**BOARD_STYLES, **RETIRED_BOARD_STYLES}


@dataclass(frozen=True)
class Board:
    seed: int
    words: tuple[str, ...]
    roles: MappingProxyType
    style: str | None = None
    dual_words: frozenset[str] = field(default_factory=frozenset)

    def __post_init__(self) -> None:
        object.__setattr__(self, "words", tuple(self.words))
        object.__setattr__(self, "roles", MappingProxyType(dict(self.roles)))
        object.__setattr__(self, "dual_words", frozenset(self.dual_words))

    def role_of(self, word: str) -> str:
        return self.roles[word]

    def words_with_role(self, role: str) -> list[str]:
        return [w for w in self.words if self.roles[w] == role]

    def is_dual(self, word: str) -> bool:
        return word in self.dual_words


def dual_count(style: str, seed: int) -> int:
    """How many of the 25 words come from the dual pool for this style.

    25 is odd, so dual_50 has no exact split. Alternating 12/13 by seed parity
    keeps the mean at exactly 50% across a set of boards, instead of biasing
    every single board low (or high).
    """
    exact = ALL_BOARD_STYLES[style] * BOARD_SIZE
    base = int(exact)
    return base + (1 if exact != base and seed % 2 else 0)


def generate_board(
    regular_pool: list[str],
    dual_pool: list[str],
    seed: int,
    style: str,
) -> Board:
    if style not in ALL_BOARD_STYLES:
        raise ValueError(
            f"unknown board style {style!r}; valid options are {sorted(ALL_BOARD_STYLES)}"
        )

    n_dual = dual_count(style, seed)
    n_regular = BOARD_SIZE - n_dual
    if len(dual_pool) < n_dual or len(regular_pool) < n_regular:
        raise ValueError(
            f"style {style!r} needs {n_dual} dual + {n_regular} regular words, "
            f"but pools have {len(dual_pool)} dual + {len(regular_pool)} regular"
        )

    # Seeded on (style, seed) so the same seed draws independent words for each
    # style. Must be an f-string, not a tuple: random.Random hashes str/bytes
    # deterministically but falls back to hash() for tuples, which PYTHONHASHSEED
    # randomises per process.
    rng = random.Random(f"{style}:{seed}")
    dual_words = rng.sample(dual_pool, n_dual)
    regular_words = rng.sample(regular_pool, n_regular)

    words = dual_words + regular_words
    # Without this shuffle the word order alone gives away which words are
    # ambiguous — prompts render the board in exactly this order.
    rng.shuffle(words)

    roles_flat = [role for role, count in ROLE_COUNTS.items() for _ in range(count)]
    rng.shuffle(roles_flat)

    return Board(
        seed=seed,
        words=words,
        roles=dict(zip(words, roles_flat)),
        style=style,
        dual_words=frozenset(dual_words),
    )
