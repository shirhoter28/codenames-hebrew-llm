import random
from dataclasses import dataclass
from types import MappingProxyType

ROLE_COUNTS: dict[str, int] = {
    "target": 9,
    "opponent": 8,
    "civilian": 7,
    "assassin": 1,
}


@dataclass(frozen=True)
class Board:
    seed: int
    words: tuple[str, ...]
    roles: MappingProxyType

    def __post_init__(self) -> None:
        object.__setattr__(self, "words", tuple(self.words))
        object.__setattr__(self, "roles", MappingProxyType(dict(self.roles)))

    def role_of(self, word: str) -> str:
        return self.roles[word]

    def words_with_role(self, role: str) -> list[str]:
        return [w for w in self.words if self.roles[w] == role]


def generate_board(word_pool: list[str], seed: int) -> Board:
    if len(word_pool) < 25:
        raise ValueError(
            f"word_pool must have at least 25 words, got {len(word_pool)}"
        )
    rng = random.Random(seed)
    words = rng.sample(word_pool, 25)
    roles_flat = [role for role, count in ROLE_COUNTS.items() for _ in range(count)]
    rng.shuffle(roles_flat)
    roles = dict(zip(words, roles_flat))
    return Board(seed=seed, words=words, roles=roles)
