# Guesser behaviour: compliance, stopping, and what misses are made of

Runs `20260823T191234131145Z` (M4) and `20260829T225350499567Z` (M5), both prompt
methods pooled. The guesser is asked for one word at a time and may stop only after
at least one correct guess (`experiment.py:192`), so every turn that ends in a miss is
a turn the model chose to continue.

The guesser is never shown reasoning fields — only `guess_sequence` is logged — so
everything below is inferred from the guesses themselves.

> **Every example below is rendered in full — board, all rounds, per-round gloss — in [`full_games.md`](full_games.md).**
> Each carries the `scripts/show_game.py` command that reproduces it. To add one, append to
> [`manifest.json`](manifest.json) and run `python scripts/render_examples.py results/<run_id> ...`.

## 1. Compliance

`attempts` counts retries, so the rate is length-independent. `illegal guess` is
`guess_not_available`: a word that is not on the board, or is already revealed.

| guesser | attempts | rejected | illegal guesses | hard failures |
|---|---|---|---|---|
| gemini-2.5-flash | 50,669 | **1.79%** | 901 | 17 |
| gpt-4o-mini | 50,708 | 8.20% | 4,154 | 46 |
| llama-3.3-70b | 31,655 | 14.11% | 3,914 | 185 |
| qwen3.5-9b | 41,020 | **16.90%** | 6,650 | 33 |

A tenfold spread. The dominant failure is not malformed JSON — it is naming a word that
is not available, which means the model is not tracking the board state it was given.

## 2. Stopping is the sharpest behavioural split in the whole grid

| guesser | all_correct | stopped_early | hit_civilian | hit_opponent | hit_assassin |
|---|---|---|---|---|---|
| gemini-2.5-flash | 7.3% | **17.3%** | 32.3% | 37.1% | 6.0% |
| qwen3.5-9b | 2.9% | **26.1%** | 29.9% | 34.6% | 6.5% |
| gpt-4o-mini | 9.1% | **1.3%** | 37.7% | 44.2% | 7.7% |
| llama-3.3-70b | 6.9% | **1.1%** | 39.2% | 43.8% | 8.6% |

gemini and qwen use the stop action; gpt-4o-mini and llama effectively do not. Measured
against the turns where stopping was legal (≥1 correct guess already banked):

| guesser | turns with the option | pressed on and missed | …already had every intended target |
|---|---|---|---|
| qwen3.5-9b | 10,449 | **38.0%** | 2.6% |
| gemini-2.5-flash | 18,884 | 65.1% | 1.7% |
| gpt-4o-mini | 16,788 | 84.1% | **10.6%** |
| llama-3.3-70b | 9,009 | **85.3%** | **9.0%** |

The last column is the damning one. For gpt-4o-mini and llama, roughly one in ten of
their over-extensions happens when the guesser has *already found every word the
codemaster was pointing at* — the clue was fully solved and the model kept guessing
anyway. For gemini and qwen that is under 3%. The higher assassin rate for the two
non-stopping models follows directly.

### The extreme case: 209 turns ended on the assassin after every intended target was already in hand

gpt-4o-mini 131, llama 55, gemini 13, qwen 10.

| codemaster / guesser | board | clue | count | targets | guesses |
|---|---|---|---|---|---|
| llama-3.3-70b-instruct / llama-3.3-70b-instruct | dual_0 s17 r4 | **טקסטיל** | 1 | כותנה | כותנה (target), לבוש (assassin) |
| llama-3.3-70b-instruct / llama-3.3-70b-instruct | dual_0 s19 r9 | **טבע** | 2 | ברווז, פרח | פרח (target), ברווז (target), קנגורו (assassin) |
| llama-3.3-70b-instruct / llama-3.3-70b-instruct | dual_0 s20 r9 | **נמוך** | 1 | גמד | גמד (target), לבוש (assassin) |
| llama-3.3-70b-instruct / llama-3.3-70b-instruct | dual_0 s24 r4 | **קסם** | 1 | אשף | אשף (target), חד-קרן (assassin) |
| llama-3.3-70b-instruct / llama-3.3-70b-instruct | natural s3 r8 | **נשוי** | 1 | בעל | בעל (target), מעמד (assassin) |
| gemini-2.5-flash / gemini-2.5-flash | natural s5 r3 | **ים** | 1 | חוף | חוף (target), פיראט (assassin) |
| llama-3.3-70b-instruct / llama-3.3-70b-instruct | natural s5 r1 | **תרבות** | 2 | תיאטרון, מופע | תיאטרון (target), מופע (target), פיראט (assassin) |
| qwen3.5-9b / qwen3.5-9b | natural s5 r1 | **מפלצת** | 1 | חייזר | חייזר (target), פיראט (assassin) |
| llama-3.3-70b-instruct / llama-3.3-70b-instruct | natural s8 r2 | **קולנוע** | 1 | סרט | סרט (target), סוכה (assassin) |
| gpt-4o-mini / gpt-4o-mini | natural s11 r2 | **לבוש** | 1 | חולצה | חולצה (target), רגל (assassin) |
| llama-3.3-70b-instruct / llama-3.3-70b-instruct | natural s14 r4 | **אור** | 1 | יום | יום (target), חוסר (assassin) |
| llama-3.3-70b-instruct / llama-3.3-70b-instruct | natural s23 r6 | **רוח** | 1 | סילון | סילון (target), צל (assassin) |

Read the second row: the clue was טבע for two words, the guesser found both, and then
guessed קנגורו — the assassin — for no reason the clue supports. The game was already
won for that turn.

## 3. Misses are not drawn to ambiguous words

The natural hypothesis is that ambiguous (dual-list) words act as decoys. They barely do.

The baseline matters. A wrong guess can only land on a hidden **non-target** word, so
that — not all 25 board words, and not every word still available — is the pool to score
against. `dual_100` boards are 100% dual by construction and `dual_0` boards are 0%, so
`natural` is the only style where the test has any power at all.

| guesser | wrong guesses (`natural`) | observed dual | chance | lift | ratio |
|---|---|---|---|---|---|
| gemini-2.5-flash | 6,716 | 28.7% | 27.1% | +1.6 | 1.059 |
| llama-3.3-70b | 5,184 | 27.7% | 26.8% | +0.9 | 1.033 |
| gpt-4o-mini | 7,723 | 27.5% | 28.0% | −0.6 | 0.980 |
| qwen3.5-9b | 5,544 | 26.3% | 27.8% | −1.5 | 0.947 |

Pooled, the effect is nil. What survives is the *ordering*, and it runs the opposite way
to the decoy story: the strongest guesser is the one drawn to ambiguous words and the
weakest is drawn away from them. A model has to have the second sense available before
it can be misled by it — qwen is not resisting ambiguity, it is failing to see it.

So whatever ambiguity costs the team, it is not paid by the guesser being baited. It is
paid earlier, in the clue the codemaster was able to construct.

## 4. Assassin on the first guess of a turn

3,275 turns. qwen 1,096, gpt-4o-mini 813, llama 697, gemini 669. These are pure
clue failures — the guesser had no correct guess to anchor on and went straight to the
one word that ends the game.

| codemaster / method / guesser | board | clue | count | intended targets | assassin taken |
|---|---|---|---|---|---|
| gemini-2.5-flash / `strong_hebrew` / gemini-2.5-flash | dual_0 s0 r7 | **גוף** | 2 | מצח, קשר | נשימה |
| qwen3.5-9b / `strong_hebrew` / qwen3.5-9b | dual_0 s0 r7 | **תקוע** | 2 | בייגלה, יורה | נשימה |
| gpt-4o-mini / `strong_hebrew` / gpt-4o-mini | dual_0 s1 r8 | **ירח** | 2 | מזל, כיפה | אסר |
| llama-3.3-70b-instruct / `strong_hebrew` / llama-3.3-70b-instruct | dual_0 s2 r8 | **מוזיקה** | 1 | בייגלה | תל-אביב |
| llama-3.3-70b-instruct / `strong_hebrew` / llama-3.3-70b-instruct | dual_0 s3 r8 | **מילה** | 0 |  | לונדון |
| qwen3.5-9b / `strong_hebrew` / qwen3.5-9b | dual_0 s2 r18 | **מלחמה** | 1 | הרמון | תל-אביב |
| llama-3.3-70b-instruct / `strong_hebrew` / llama-3.3-70b-instruct | dual_0 s4 r11 | **אשפה** | 1 | טיל | ציפורן |
| qwen3.5-9b / `strong_hebrew` / qwen3.5-9b | dual_0 s4 r8 | **פרח** | 2 | אביר, ציור | ציפורן |
| gemini-2.5-flash / `strong_hebrew` / gemini-2.5-flash | dual_0 s8 r3 | **חיים** | 2 | פרח, דג | מעיין |
| llama-3.3-70b-instruct / `strong_hebrew` / llama-3.3-70b-instruct | dual_0 s8 r3 | **טבע** | 2 | דג, זוהר | מעיין |
| qwen3.5-9b / `strong_hebrew` / qwen3.5-9b | dual_0 s6 r16 | **מלט** | 1 | רצפה | עכביש |
| llama-3.3-70b-instruct / `strong_hebrew` / llama-3.3-70b-instruct | dual_0 s9 r12 | **ארץ** | 1 | קנגורו | תנועה |

## 5. Lucky hits: targets the codemaster was not pointing at

Guesses that landed on a team word the codemaster had *not* listed in
`intended_targets`, as a share of all correct guesses:

| guesser | correct guesses | unintended | share |
|---|---|---|---|
| gemini-2.5-flash | 24,977 | 3,049 | 12.2% |
| gpt-4o-mini | 23,276 | 3,837 | 16.5% |
| llama-3.3-70b | 12,567 | 2,505 | 19.9% |
| qwen3.5-9b | 12,408 | 2,759 | 22.2% |

Between an eighth and a fifth of correct guesses are not the ones the clue was built
for, and the weaker the guesser the larger that share. Worth remembering when reading
`target_recovery_rate`: it credits the team for words the clue did not earn.

