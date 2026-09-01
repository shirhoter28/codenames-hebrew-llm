"""The document's colour identity, shared by every figure in the project.

One module so that a model wears the same colour in a run report and in the
paper. Before this existed the two figure sets assigned colours by their own
sort order, so the same hue named `llama` in one figure and `gpt-4o-mini` in
the next — the one thing a reader of a multi-figure document must be able to
rely on.

Values are the validated light-mode categorical palette; the four slots pass
the adjacent-pair CVD and normal-vision gates on the `#fcfcfb` surface. Two of
them sit below 3:1 contrast against that surface, so every figure that uses
them prints its values as text as well.
"""

from __future__ import annotations

# Categorical slots, in the order the palette defines them.
SERIES: tuple[str, ...] = ("#2a78d6", "#eb6834", "#1baf7a", "#eda100")

# Chart chrome.
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"

# Sequential blue, light -> dark, for magnitude (heatmaps).
SEQ_BLUE: tuple[str, ...] = (
    "#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b",
)

# Board style is an ordinal ladder, so it takes an ordinal ramp rather than
# categorical slots — which keeps the categorical hues meaning "model"
# everywhere. Steps clear 2:1 against the light surface.
STYLE_RAMP: tuple[str, ...] = ("#86b6ef", "#2a78d6", "#104281")

# Model identity. Keyed on the short name so `google/gemini-2.5-flash` and a
# bare `gemini-2.5-flash` land on the same colour.
MODEL_ORDER: tuple[str, ...] = (
    "gemini-2.5-flash",
    "gpt-4o-mini",
    "llama-3.3-70b-instruct",
    "qwen3.5-9b",
)

# Display names: the full id is too wide for a table cell or a tick label.
DISPLAY_NAMES = {"llama-3.3-70b-instruct": "llama-3.3-70b"}


def short_model(name) -> str:
    """`meta-llama/llama-3.3-70b-instruct` -> `llama-3.3-70b-instruct`."""
    return str(name).split("/")[-1].replace(":free", "")


def display_model(name) -> str:
    """The short name, further shortened where it is still too long to fit."""
    base = short_model(name)
    return DISPLAY_NAMES.get(base, base)


_BY_MODEL = {m: SERIES[i % len(SERIES)] for i, m in enumerate(MODEL_ORDER)}


def color_for_model(name) -> str:
    """This model's colour, the same in every figure of the project.

    Falls back to the categorical slots in first-seen order for a model not in
    `MODEL_ORDER`, so an exploratory run with a new model still plots.
    """
    return _BY_MODEL.get(short_model(name), MUTED)


def colors_for(models) -> dict:
    """A colour per model, extending the palette for anything unlisted."""
    out: dict = {}
    spare = [c for c in SERIES if c not in {_BY_MODEL[m] for m in MODEL_ORDER}]
    for m in models:
        key = short_model(m)
        if key in _BY_MODEL:
            out[m] = _BY_MODEL[key]
        else:
            out[m] = spare.pop(0) if spare else MUTED
    return out
