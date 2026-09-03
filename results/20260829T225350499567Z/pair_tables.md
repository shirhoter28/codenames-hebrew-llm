# Codemaster x guesser pair results — 20260829T225350499567Z

Laid out like Table I of Stephenson, Sidji & Ronval (`docs/previous_results_english.png`) so the Hebrew results can be read against the published English ones.

- Completed games: **1440** of 1465
- Pairs: 4 (2 codemasters x 2 guessers)

### How to read these columns

- `Mean` / `Median` / `Min` / `Std Dev` are the game length in rounds, over **completed games only**. `Mean (without loss)` is the same over won games alone — a lost game is short because it ended on the assassin, so pooling the two makes a pair that dies early look efficient.
- `Opponent` and `Civilian` are words of that role revealed per game. The English table calls the first one `Blue`; revealing one ends the turn *and* advances the opposing team, where a civilian only ends the turn.
- `Clues` is the count the codemaster commits each clue to; `Guesses` is how many the guesser actually made. Both are per round.
- `Stop Early` / `Stop Late` are over **eligible** rounds, not all rounds. A guesser may not stop before its first correct guess, so an early stop is impossible when the clue named a count of 1; counting those rounds would deflate the rate for reasons unrelated to the guesser's judgement. `Stop Late` is the bonus (count + 1) guess being taken.
- `Games` and `Rounds` are printed because our cells are not all the same size, unlike the paper's. A mean over 30 games is not the same evidence as one over 500.

## All arms pooled

Every prompt method, clue-count floor and board style averaged together. This is the row-for-row analogue of the published table.

| Model Pair (codemaster - guesser)   | Games | Rounds | Mean | Median | Min | Std Dev | Loss  | Mean (without loss) | Opponent avg(stdev) | Civilian avg(stdev) | Clues avg(stdev) | Guesses avg(stdev) | Stop Early | Stop Late |
|-------------------------------------|-------|--------|------|--------|-----|---------|-------|---------------------|---------------------|---------------------|------------------|--------------------|------------|-----------|
| gemini-2.5-flash - gemini-2.5-flash | 705   | 4815   | 6.83 | 7      | 1   | 2.68    | 38.2% | 8.19                | 2.35 (1.62)         | 1.98 (1.43)         | 2.04 (0.51)      | 1.76 (0.54)        | 3.2%       | 3.2%      |
| gemini-2.5-flash - gpt-4o-mini      | 13    | 94     | 7.23 | 8      | 2   | 3.59    | 53.8% | 10.00               | 3.08 (2.14)         | 2.77 (1.59)         | 2.00 (0.33)      | 1.76 (0.68)        | 0.0%       | 100.0%    |
| gpt-4o-mini - gemini-2.5-flash      | 12    | 83     | 6.92 | 6      | 2   | 3.26    | 75.0% | 10.67               | 2.25 (1.82)         | 1.92 (1.68)         | 1.99 (0.25)      | 1.64 (0.48)        | 3.8%       | 0.0%      |
| gpt-4o-mini - gpt-4o-mini           | 710   | 5078   | 7.15 | 7      | 1   | 3.34    | 58.0% | 8.95                | 3.17 (1.98)         | 2.64 (1.75)         | 2.05 (0.51)      | 1.82 (0.75)        | 0.1%       | 95.8%     |

## By prompt method

One table per method, each averaging over the other two factors. Every pair appears in every table.

### method = `strong_hebrew`

| Model Pair (codemaster - guesser)   | Games | Rounds | Mean | Median | Min | Std Dev | Loss  | Mean (without loss) | Opponent avg(stdev) | Civilian avg(stdev) | Clues avg(stdev) | Guesses avg(stdev) | Stop Early | Stop Late |
|-------------------------------------|-------|--------|------|--------|-----|---------|-------|---------------------|---------------------|---------------------|------------------|--------------------|------------|-----------|
| gemini-2.5-flash - gemini-2.5-flash | 351   | 2465   | 7.02 | 7      | 1   | 2.82    | 39.6% | 8.50                | 2.45 (1.70)         | 1.99 (1.48)         | 1.95 (0.38)      | 1.71 (0.52)        | 1.9%       | 3.7%      |
| gemini-2.5-flash - gpt-4o-mini      | 13    | 94     | 7.23 | 8      | 2   | 3.59    | 53.8% | 10.00               | 3.08 (2.14)         | 2.77 (1.59)         | 2.00 (0.33)      | 1.76 (0.68)        | 0.0%       | 100.0%    |
| gpt-4o-mini - gemini-2.5-flash      | 12    | 83     | 6.92 | 6      | 2   | 3.26    | 75.0% | 10.67               | 2.25 (1.82)         | 1.92 (1.68)         | 1.99 (0.25)      | 1.64 (0.48)        | 3.8%       | 0.0%      |
| gpt-4o-mini - gpt-4o-mini           | 359   | 2614   | 7.28 | 7      | 1   | 3.45    | 62.1% | 9.21                | 3.25 (2.04)         | 2.69 (1.80)         | 1.98 (0.35)      | 1.78 (0.75)        | 0.0%       | 97.3%     |

### method = `translate_pipeline`

| Model Pair (codemaster - guesser)   | Games | Rounds | Mean | Median | Min | Std Dev | Loss  | Mean (without loss) | Opponent avg(stdev) | Civilian avg(stdev) | Clues avg(stdev) | Guesses avg(stdev) | Stop Early | Stop Late |
|-------------------------------------|-------|--------|------|--------|-----|---------|-------|---------------------|---------------------|---------------------|------------------|--------------------|------------|-----------|
| gemini-2.5-flash - gemini-2.5-flash | 354   | 2350   | 6.64 | 7      | 1   | 2.51    | 36.7% | 7.89                | 2.25 (1.54)         | 1.97 (1.38)         | 2.14 (0.59)      | 1.81 (0.57)        | 4.6%       | 2.6%      |
| gpt-4o-mini - gpt-4o-mini           | 351   | 2464   | 7.02 | 7      | 1   | 3.23    | 53.8% | 8.73                | 3.10 (1.91)         | 2.60 (1.70)         | 2.13 (0.63)      | 1.86 (0.74)        | 0.1%       | 93.9%     |

## By board style

One table per board style, each averaging over the other two factors. Every pair appears in every table.

### board_style = `dual_0`

| Model Pair (codemaster - guesser)   | Games | Rounds | Mean | Median | Min | Std Dev | Loss  | Mean (without loss) | Opponent avg(stdev) | Civilian avg(stdev) | Clues avg(stdev) | Guesses avg(stdev) | Stop Early | Stop Late |
|-------------------------------------|-------|--------|------|--------|-----|---------|-------|---------------------|---------------------|---------------------|------------------|--------------------|------------|-----------|
| gemini-2.5-flash - gemini-2.5-flash | 235   | 1540   | 6.55 | 7      | 1   | 2.54    | 39.6% | 7.88                | 2.26 (1.56)         | 1.89 (1.31)         | 2.05 (0.53)      | 1.79 (0.55)        | 3.3%       | 5.2%      |
| gemini-2.5-flash - gpt-4o-mini      | 13    | 94     | 7.23 | 8      | 2   | 3.59    | 53.8% | 10.00               | 3.08 (2.14)         | 2.77 (1.59)         | 2.00 (0.33)      | 1.76 (0.68)        | 0.0%       | 100.0%    |
| gpt-4o-mini - gemini-2.5-flash      | 12    | 83     | 6.92 | 6      | 2   | 3.26    | 75.0% | 10.67               | 2.25 (1.82)         | 1.92 (1.68)         | 1.99 (0.25)      | 1.64 (0.48)        | 3.8%       | 0.0%      |
| gpt-4o-mini - gpt-4o-mini           | 237   | 1644   | 6.94 | 7      | 1   | 3.21    | 56.1% | 9.04                | 3.07 (1.91)         | 2.55 (1.70)         | 2.04 (0.51)      | 1.83 (0.75)        | 0.1%       | 95.0%     |

### board_style = `natural`

| Model Pair (codemaster - guesser)   | Games | Rounds | Mean | Median | Min | Std Dev | Loss  | Mean (without loss) | Opponent avg(stdev) | Civilian avg(stdev) | Clues avg(stdev) | Guesses avg(stdev) | Stop Early | Stop Late |
|-------------------------------------|-------|--------|------|--------|-----|---------|-------|---------------------|---------------------|---------------------|------------------|--------------------|------------|-----------|
| gemini-2.5-flash - gemini-2.5-flash | 238   | 1658   | 6.97 | 7      | 1   | 2.63    | 34.9% | 8.23                | 2.41 (1.69)         | 2.00 (1.36)         | 2.02 (0.48)      | 1.76 (0.52)        | 3.6%       | 2.7%      |
| gpt-4o-mini - gpt-4o-mini           | 239   | 1691   | 7.08 | 7      | 1   | 3.11    | 56.9% | 8.47                | 3.05 (1.88)         | 2.63 (1.69)         | 2.05 (0.49)      | 1.84 (0.75)        | 0.0%       | 96.2%     |

### board_style = `dual_100`

| Model Pair (codemaster - guesser)   | Games | Rounds | Mean | Median | Min | Std Dev | Loss  | Mean (without loss) | Opponent avg(stdev) | Civilian avg(stdev) | Clues avg(stdev) | Guesses avg(stdev) | Stop Early | Stop Late |
|-------------------------------------|-------|--------|------|--------|-----|---------|-------|---------------------|---------------------|---------------------|------------------|--------------------|------------|-----------|
| gemini-2.5-flash - gemini-2.5-flash | 232   | 1617   | 6.97 | 7      | 1   | 2.84    | 40.1% | 8.45                | 2.39 (1.61)         | 2.04 (1.60)         | 2.05 (0.51)      | 1.73 (0.55)        | 2.8%       | 1.8%      |
| gpt-4o-mini - gpt-4o-mini           | 234   | 1743   | 7.45 | 7      | 1   | 3.68    | 61.1% | 9.41                | 3.40 (2.13)         | 2.74 (1.87)         | 2.07 (0.53)      | 1.79 (0.75)        | 0.1%       | 96.3%     |
