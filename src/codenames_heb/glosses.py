"""What English sense each codemaster assigns to an ambiguous Hebrew board word.

`translate_pipeline` asks the codemaster to translate the whole board before it
clues, and logs that `translation_map` on every round. The map is therefore a
direct read on the model's lexical choice: for a word with two live senses, it
says which one the model is playing.

The call is stateless — `build_translate_pipeline_prompt` rebuilds the board
every round — so a word is re-glossed each turn and the counts here are over
rounds, not games. That is the unit that matters: a clue is built from one
round's gloss.

`SENSES` is the hand-written part. Each entry names the two senses of a word
and the English tokens that stand for each; a gloss naming both (the model
hedged, `"heavy/liver"`) is neither side but its own category, which is the
whole reason the split is three-way and not binary.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

TRANSLATE_METHOD = "translate_pipeline"
HEBREW = re.compile(r"[֐-׿]")

# word -> (sense A label, A tokens), (sense B label, B tokens).
# Tokens are matched whole, lowercased, so "god" never matches "goddess".
SENSES: dict[str, tuple[tuple[str, tuple[str, ...]], tuple[str, ...]]] = {}
_RAW = {
    "הודו": (("India", ("india", "indian")), ("turkey", ("turkey", "thanksgiving"))),
    "כבד": (("heavy", ("heavy", "heavily")), ("liver", ("liver",))),
    "קניון": (("mall", ("mall", "shopping")), ("canyon", ("canyon", "gorge", "ravine"))),
    "אלים": (("gods", ("god", "gods", "deity", "deities")),
             ("violent", ("violent", "violence", "ruthless", "brutal"))),
    "מלון": (("hotel", ("hotel", "inn")), ("melon", ("melon", "cantaloupe"))),
    "מלח": (("salt", ("salt", "salty")), ("sailor", ("sailor", "seaman", "mariner"))),
    "אלה": (("these", ("these", "those", "that")),
            ("goddess", ("goddess", "club", "oak"))),
    "פה": (("mouth", ("mouth",)), ("here", ("here",))),
    "תור": (("turn", ("turn", "tour")), ("queue", ("queue", "line", "row"))),
    "סרט": (("movie", ("movie", "film", "cinema")), ("ribbon", ("ribbon", "tape", "band"))),
    "קל": (("easy", ("easy", "simple")), ("light", ("light",))),
    "מטר": (("meter", ("meter", "metre")), ("rain", ("rain", "downpour"))),
    "אוגר": (("hamster", ("hamster", "gerbil", "rodent")),
             ("hoarder", ("store", "storage", "hoarder", "hoard", "treasurer",
                          "saver", "accumulator", "register"))),
    "בר": (("bar", ("bar", "pub", "tavern")), ("son", ("son", "wild"))),
    "זריקה": (("throw", ("throw", "throwing", "toss")),
              ("injection", ("injection", "shot", "vaccine", "jab"))),
    "שיח": (("bush", ("bush", "shrub", "shrubbery")),
            ("conversation", ("conversation", "discourse", "dialogue", "talk", "speech"))),
    "מטה": (("staff", ("staff", "rod", "wand", "stick", "cane")),
            ("headquarters", ("headquarters", "hq", "command"))),
    "בול": (("stamp", ("stamp", "mail", "post", "postage")),
            ("bullseye", ("bullseye", "bull", "target"))),
}
SENSES.update(_RAW)

# A gloss naming neither sense. Kept as its own bucket rather than dropped: for
# some models it is most of the mass (qwen glosses אוגר as "ogre"), and a chart
# that silently renormalised it away would hide that.
UNRELATED = "unrelated"
BOTH = "both"


def _tokens(gloss: str) -> set[str]:
    return {t for t in re.split(r"[^a-z]+", gloss.lower()) if t}


def classify(word: str, gloss: str) -> str:
    """Which sense of `word` this gloss names: sense A, sense B, both, unrelated."""
    entry = SENSES.get(word)
    if entry is None:
        raise KeyError(f"{word!r} has no sense definition")
    (a_label, a_tokens), (b_label, b_tokens) = entry
    tokens = _tokens(gloss)
    has_a = bool(tokens & set(a_tokens))
    has_b = bool(tokens & set(b_tokens))
    if has_a and has_b:
        return BOTH
    if has_a:
        return a_label
    if has_b:
        return b_label
    return UNRELATED


def gloss_counts(run_dirs, words=None) -> pd.DataFrame:
    """One row per (model, word, gloss) with the number of rounds it appeared in.

    Only `translate_pipeline` games carry a translation map, so other methods
    contribute nothing. Keys that are not Hebrew board words (a model that
    answered with `{"YOUR_WORDS": [...]}` instead of a map) are skipped.
    """
    wanted = set(words) if words is not None else None
    tally: Counter = Counter()
    for run_dir in run_dirs:
        path = Path(run_dir) / "raw.jsonl"
        if not path.exists():
            continue
        with path.open() as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                game = json.loads(line)
                if game.get("method") != TRANSLATE_METHOD:
                    continue
                for rnd in game.get("rounds") or []:
                    tmap = rnd.get("translation_map")
                    if not isinstance(tmap, dict):
                        continue
                    for heb, eng in tmap.items():
                        if not isinstance(eng, str) or not HEBREW.search(heb):
                            continue
                        if wanted is not None and heb not in wanted:
                            continue
                        tally[(game["model"], heb, eng.strip().lower())] += 1
    frame = pd.DataFrame(
        [{"model": m, "word": w, "gloss": g, "n": n} for (m, w, g), n in tally.items()]
    )
    if frame.empty:
        return frame.reindex(columns=["model", "word", "gloss", "n"])
    return frame.sort_values(["word", "model", "n"], ascending=[True, True, False],
                             ignore_index=True)


def sense_shares(counts: pd.DataFrame) -> pd.DataFrame:
    """Collapse glosses to the sense split, as a share of that model's rounds."""
    rows = []
    for (model, word), group in counts.groupby(["model", "word"], sort=False):
        (a_label, _), (b_label, _) = SENSES[word]
        total = int(group["n"].sum())
        bucket: Counter = Counter()
        for gloss, n in zip(group["gloss"], group["n"]):
            bucket[classify(word, gloss)] += int(n)
        rows.append({
            "model": model, "word": word, "rounds": total,
            "sense_a": a_label, "sense_b": b_label,
            "share_a": bucket[a_label] / total,
            "share_both": bucket[BOTH] / total,
            "share_b": bucket[b_label] / total,
            "share_unrelated": bucket[UNRELATED] / total,
            "n_glosses": int(group["gloss"].nunique()),
        })
    return pd.DataFrame(rows)


def top_glosses(counts: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    """The k most frequent glosses per (model, word), with their shares."""
    rows = []
    for (model, word), group in counts.groupby(["model", "word"], sort=False):
        total = int(group["n"].sum())
        top = group.nlargest(k, "n")
        rows.append({
            "model": model, "word": word, "rounds": total,
            "n_glosses": int(group["gloss"].nunique()),
            "top": [(g, int(n), n / total) for g, n in zip(top["gloss"], top["n"])],
        })
    return pd.DataFrame(rows)
