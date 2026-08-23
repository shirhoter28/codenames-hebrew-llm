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

# How each board style fills its 25 slots. The value is the fraction drawn from
# the dual (ambiguous) pool; None means the style draws freely from the two
# pools combined, so its dual share is whatever the word lists imply and it
# varies board to board.
#
# `natural` is the primary condition: a board dealt the way a physical Hebrew
# deck deals one, which is the question the project is actually asking. `dual_0`
# and `dual_100` bracket it — no ambiguity at all, and nothing but ambiguity —
# so a difference at `natural` can be attributed to lexical ambiguity rather
# than merely observed alongside it.
BOARD_STYLES: dict[str, float | None] = {
    "dual_0": 0.0,
    "natural": None,
    "dual_100": 1.0,
}

# Styles no longer in the design but still readable. M1-M3 ran `dual_50` and
# `dual_80`; dropping them outright would make those boards ungeneratable and
# would silently drop their rows from `style_order`, so reports on those runs
# would quietly lose part of their data instead of erroring. Retired styles can
# be regenerated and analysed, not designed into a new run.
RETIRED_BOARD_STYLES: dict[str, float | None] = {
    "dual_50": 0.5,
    "dual_80": 0.8,
}

ALL_BOARD_STYLES: dict[str, float | None] = {**BOARD_STYLES, **RETIRED_BOARD_STYLES}

# Ladder order for tables and plot facets, ascending in ambiguity. `natural`
# sits where its pools put it (~26% dual on the current lists), between `dual_0`
# and `dual_50`. Listed explicitly rather than sorted by share because a free-
# draw style has no fixed share to sort on.
BOARD_STYLE_LADDER: tuple[str, ...] = (
    "dual_0",
    "natural",
    "dual_50",
    "dual_80",
    "dual_100",
)

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


def draws_freely(style: str) -> bool:
    """Does this style deal from the combined pool instead of a fixed split?"""
    return ALL_BOARD_STYLES[style] is None


def dual_count(style: str, seed: int) -> int:
    """How many of the 25 words come from the dual pool for this style.

    25 is odd, so a fractional style like the retired `dual_50` has no exact
    split. Alternating 12/13 by seed parity keeps the mean at exactly 50% across
    a set of boards, instead of biasing every single board low (or high).
    """
    share = ALL_BOARD_STYLES[style]
    if share is None:
        raise ValueError(
            f"style {style!r} draws freely from the combined pool, so its dual "
            f"count varies board to board; read len(board.dual_words) instead"
        )
    exact = share * BOARD_SIZE
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

    # Seeded on (style, seed) so the same seed draws independent words for each
    # style. Must be an f-string, not a tuple: random.Random hashes str/bytes
    # deterministically but falls back to hash() for tuples, which PYTHONHASHSEED
    # randomises per process.
    rng = random.Random(f"{style}:{seed}")

    if draws_freely(style):
        # One draw from the two pools combined, exactly as dealing off a shuffled
        # deck: how many ambiguous words land on the board is left to chance, and
        # is whatever the list composition implies. Nothing is being controlled
        # here, which is the point — this is the board a real game deals.
        combined = list(dual_pool) + list(regular_pool)
        if len(combined) < BOARD_SIZE:
            raise ValueError(
                f"style {style!r} needs {BOARD_SIZE} words, but the pools hold "
                f"{len(combined)} between them"
            )
        in_dual = set(dual_pool)
        words = rng.sample(combined, BOARD_SIZE)
        dual_words = [w for w in words if w in in_dual]
    else:
        n_dual = dual_count(style, seed)
        n_regular = BOARD_SIZE - n_dual
        if len(dual_pool) < n_dual or len(regular_pool) < n_regular:
            raise ValueError(
                f"style {style!r} needs {n_dual} dual + {n_regular} regular words, "
                f"but pools have {len(dual_pool)} dual + {len(regular_pool)} regular"
            )
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
