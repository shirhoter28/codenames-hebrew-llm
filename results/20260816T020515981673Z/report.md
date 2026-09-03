# Codenames-Hebrew results — 20260816T020515981673Z

- Games: **24** (22 completed, 2 not completed)
- Rounds: **198**
- Models: meta-llama/llama-3.3-70b-instruct, openai/gpt-4o-mini, qwen/qwen3.5-9b
- Prompt methods: strong_hebrew, translate_pipeline
- Guesser: meta-llama/llama-3.3-70b-instruct
- Board styles: unspecified

### How to read these numbers

- Win/loss rates and game length cover **completed games only**. Games that ended because a model could not produce a legal clue are reported separately as a completion rate; scoring them as losses would confuse a formatting failure with a bad clue.
- Games end only by finding all 9 targets or by hitting the assassin, so `%loss` is close to `1 - %win`, and **game length is confounded with outcome** — a short game is an efficient win or an early death. Length is therefore also reported separately for wins and for losses.
- SE is `sd / sqrt(n)` at the natural unit (games for game metrics, rounds for round metrics). Proportions also carry a Wilson 95% interval, because at small n a Wald SE of 0 at p=0 or p=1 reads as false certainty.
- Round-level SEs treat rounds within a game as independent. They are not, so those SEs are optimistic.

### Stop taxonomy

The logged `turn_outcome` cannot answer the early-stop question: it records both *stopping short of* the codemaster's count and *stopping at* it after declining the bonus guess as `stopped_early`. Only the first is an early stop. Rounds are therefore reclassified as:

| class | meaning |
|---|---|
| `early_stop_true` | stopped before reaching the count — **the early stop** |
| `stopped_at_quota` | reached the count and declined the bonus guess (correct play) |
| `miss_before_quota` | guessed wrong before reaching the count |
| `miss_on_bonus_guess` | reached the count, took the bonus guess, got it wrong |
| `bonus_taken_correct` | reached the count, took the bonus guess, got it right |
| `game_won_midround` | round ended because the 9th target fell — not a choice |
| `guesser_failure` / `no_quota` | guesser exhausted retries / clue had count 0 |

Rates are computed over eligible rounds only. A guesser may not stop before its first correct guess, so an early stop is impossible when `count = 1`; including those rounds in the denominator would deflate the rate for reasons unrelated to the guesser's judgement.

## Game outcomes — by model

`loss_rate` and `length_*` cover completed games; `completion_rate` is the share of games that played out at all. `win_rate` is `1 - loss_rate` by construction, so only the loss rate carries an SE and a Wilson interval (`loss_lo` / `loss_hi`).

| model                             | n_games | n_completed | completion_rate | win_rate | loss_rate | loss_se | loss_lo | loss_hi | length_mean | length_se | length_win_mean | length_win_se | n_win | length_loss_mean | length_loss_se | n_loss | targets_found_mean | targets_found_se |
|-----------------------------------|---------|-------------|-----------------|----------|-----------|---------|---------|---------|-------------|-----------|-----------------|---------------|-------|------------------|----------------|--------|--------------------|------------------|
| meta-llama/llama-3.3-70b-instruct | 8       | 8           | 1.000           | 0.125    | 0.875     | 0.125   | 0.529   | 0.978   | 8.375       | 1.375     | 5.000           | —             | 1.000 | 8.857            | 1.487          | 7      | 6.250              | 0.996            |
| openai/gpt-4o-mini                | 8       | 8           | 1.000           | 0.125    | 0.875     | 0.125   | 0.529   | 0.978   | 8.625       | 1.034     | 7.000           | —             | 1.000 | 8.857            | 1.164          | 7      | 6.750              | 0.701            |
| qwen/qwen3.5-9b                   | 8       | 6           | 0.750           | 0.000    | 1.000     | 0.000   | 0.610   | 1.000   | 8.500       | 1.628     | —               | —             | —     | 8.500            | 1.628          | 6      | 5.000              | 0.730            |

## Game outcomes — by model x prompt method

`loss_rate` and `length_*` cover completed games; `completion_rate` is the share of games that played out at all. `win_rate` is `1 - loss_rate` by construction, so only the loss rate carries an SE and a Wilson interval (`loss_lo` / `loss_hi`).

| model                             | method             | n_games | n_completed | completion_rate | win_rate | loss_rate | loss_se | loss_lo | loss_hi | length_mean | length_se | length_win_mean | length_win_se | n_win | length_loss_mean | length_loss_se | n_loss | targets_found_mean | targets_found_se |
|-----------------------------------|--------------------|---------|-------------|-----------------|----------|-----------|---------|---------|---------|-------------|-----------|-----------------|---------------|-------|------------------|----------------|--------|--------------------|------------------|
| meta-llama/llama-3.3-70b-instruct | strong_hebrew      | 4       | 4           | 1.000           | 0.000    | 1.000     | 0.000   | 0.510   | 1.000   | 9.500       | 1.500     | —               | —             | —     | 9.500            | 1.500          | 4      | 7.000              | 0.913            |
| meta-llama/llama-3.3-70b-instruct | translate_pipeline | 4       | 4           | 1.000           | 0.250    | 0.750     | 0.250   | 0.301   | 0.954   | 7.250       | 2.394     | 5.000           | —             | 1.000 | 8.000            | 3.215          | 3      | 5.500              | 1.848            |
| openai/gpt-4o-mini                | strong_hebrew      | 4       | 4           | 1.000           | 0.250    | 0.750     | 0.250   | 0.301   | 0.954   | 8.500       | 1.323     | 7.000           | —             | 1.000 | 9.000            | 1.732          | 3      | 6.750              | 1.315            |
| openai/gpt-4o-mini                | translate_pipeline | 4       | 4           | 1.000           | 0.000    | 1.000     | 0.000   | 0.510   | 1.000   | 8.750       | 1.797     | —               | —             | —     | 8.750            | 1.797          | 4      | 6.750              | 0.750            |
| qwen/qwen3.5-9b                   | strong_hebrew      | 4       | 3           | 0.750           | 0.000    | 1.000     | 0.000   | 0.439   | 1.000   | 10.000      | 2.000     | —               | —             | —     | 10.000           | 2.000          | 3      | 5.667              | 0.882            |
| qwen/qwen3.5-9b                   | translate_pipeline | 4       | 3           | 0.750           | 0.000    | 1.000     | 0.000   | 0.439   | 1.000   | 7.000       | 2.646     | —               | —             | —     | 7.000            | 2.646          | 3      | 4.333              | 1.202            |

## Game outcomes — by board style

`loss_rate` and `length_*` cover completed games; `completion_rate` is the share of games that played out at all. `win_rate` is `1 - loss_rate` by construction, so only the loss rate carries an SE and a Wilson interval (`loss_lo` / `loss_hi`).

| board_style | n_games | n_completed | completion_rate | win_rate | loss_rate | loss_se | loss_lo | loss_hi | length_mean | length_se | length_win_mean | length_win_se | n_win | length_loss_mean | length_loss_se | n_loss | targets_found_mean | targets_found_se |
|-------------|---------|-------------|-----------------|----------|-----------|---------|---------|---------|-------------|-----------|-----------------|---------------|-------|------------------|----------------|--------|--------------------|------------------|
| unspecified | 24      | 22          | 0.917           | 0.091    | 0.909     | 0.063   | 0.722   | 0.975   | 8.500       | 0.729     | 6.000           | 1.000         | 2     | 8.750            | 0.778          | 20     | 6.091              | 0.488            |

## Game outcomes — by model x board style

`loss_rate` and `length_*` cover completed games; `completion_rate` is the share of games that played out at all. `win_rate` is `1 - loss_rate` by construction, so only the loss rate carries an SE and a Wilson interval (`loss_lo` / `loss_hi`).

| model                             | board_style | n_games | n_completed | completion_rate | win_rate | loss_rate | loss_se | loss_lo | loss_hi | length_mean | length_se | length_win_mean | length_win_se | n_win | length_loss_mean | length_loss_se | n_loss | targets_found_mean | targets_found_se |
|-----------------------------------|-------------|---------|-------------|-----------------|----------|-----------|---------|---------|---------|-------------|-----------|-----------------|---------------|-------|------------------|----------------|--------|--------------------|------------------|
| meta-llama/llama-3.3-70b-instruct | unspecified | 8       | 8           | 1.000           | 0.125    | 0.875     | 0.125   | 0.529   | 0.978   | 8.375       | 1.375     | 5.000           | —             | 1.000 | 8.857            | 1.487          | 7      | 6.250              | 0.996            |
| openai/gpt-4o-mini                | unspecified | 8       | 8           | 1.000           | 0.125    | 0.875     | 0.125   | 0.529   | 0.978   | 8.625       | 1.034     | 7.000           | —             | 1.000 | 8.857            | 1.164          | 7      | 6.750              | 0.701            |
| qwen/qwen3.5-9b                   | unspecified | 8       | 6           | 0.750           | 0.000    | 1.000     | 0.000   | 0.610   | 1.000   | 8.500       | 1.628     | —               | —             | —     | 8.500            | 1.628          | 6      | 5.000              | 0.730            |

## Game outcomes — by model x method x board style

`loss_rate` and `length_*` cover completed games; `completion_rate` is the share of games that played out at all. `win_rate` is `1 - loss_rate` by construction, so only the loss rate carries an SE and a Wilson interval (`loss_lo` / `loss_hi`).

| model                             | method             | board_style | n_games | n_completed | completion_rate | win_rate | loss_rate | loss_se | loss_lo | loss_hi | length_mean | length_se | length_win_mean | length_win_se | n_win | length_loss_mean | length_loss_se | n_loss | targets_found_mean | targets_found_se |
|-----------------------------------|--------------------|-------------|---------|-------------|-----------------|----------|-----------|---------|---------|---------|-------------|-----------|-----------------|---------------|-------|------------------|----------------|--------|--------------------|------------------|
| meta-llama/llama-3.3-70b-instruct | strong_hebrew      | unspecified | 4       | 4           | 1.000           | 0.000    | 1.000     | 0.000   | 0.510   | 1.000   | 9.500       | 1.500     | —               | —             | —     | 9.500            | 1.500          | 4      | 7.000              | 0.913            |
| meta-llama/llama-3.3-70b-instruct | translate_pipeline | unspecified | 4       | 4           | 1.000           | 0.250    | 0.750     | 0.250   | 0.301   | 0.954   | 7.250       | 2.394     | 5.000           | —             | 1.000 | 8.000            | 3.215          | 3      | 5.500              | 1.848            |
| openai/gpt-4o-mini                | strong_hebrew      | unspecified | 4       | 4           | 1.000           | 0.250    | 0.750     | 0.250   | 0.301   | 0.954   | 8.500       | 1.323     | 7.000           | —             | 1.000 | 9.000            | 1.732          | 3      | 6.750              | 1.315            |
| openai/gpt-4o-mini                | translate_pipeline | unspecified | 4       | 4           | 1.000           | 0.000    | 1.000     | 0.000   | 0.510   | 1.000   | 8.750       | 1.797     | —               | —             | —     | 8.750            | 1.797          | 4      | 6.750              | 0.750            |
| qwen/qwen3.5-9b                   | strong_hebrew      | unspecified | 4       | 3           | 0.750           | 0.000    | 1.000     | 0.000   | 0.439   | 1.000   | 10.000      | 2.000     | —               | —             | —     | 10.000           | 2.000          | 3      | 5.667              | 0.882            |
| qwen/qwen3.5-9b                   | translate_pipeline | unspecified | 4       | 3           | 0.750           | 0.000    | 1.000     | 0.000   | 0.439   | 1.000   | 7.000       | 2.646     | —               | —             | —     | 7.000            | 2.646          | 3      | 4.333              | 1.202            |

## Round metrics — by model

`ambition` = words the codemaster commits one clue to (`count`); `yield` = targets that clue actually bought; `yield_ratio` = yield / ambition. `intended_*` compare the words aimed at with the words hit; `n_lucky_mean` counts targets found that were *not* aimed at. `early_stop_rate` and `bonus_take_rate` are over their eligible rounds only — `n_*_eligible` gives those denominators.

| model                             | n_rounds | ambition_mean | ambition_se | yield_mean | yield_se | yield_ratio_mean | yield_ratio_se | intended_recall_mean | intended_recall_se | intended_precision_mean | intended_precision_se | intended_jaccard_mean | intended_jaccard_se | n_lucky_mean | early_stop_rate | early_stop_se | n_early_stop_eligible | bonus_take_rate | bonus_take_se | n_bonus_eligible |
|-----------------------------------|----------|---------------|-------------|------------|----------|------------------|----------------|----------------------|--------------------|-------------------------|-----------------------|-----------------------|---------------------|--------------|-----------------|---------------|-----------------------|-----------------|---------------|------------------|
| meta-llama/llama-3.3-70b-instruct | 67       | 1.567         | 0.061       | 0.746      | 0.109    | 0.522            | 0.071          | 0.366                | 0.055              | 0.719                   | 0.066                 | 0.326                 | 0.051               | 0.239        | 0.000           | 0.000         | 17                    | 1.000           | 0.000         | 24               |
| openai/gpt-4o-mini                | 69       | 2.072         | 0.069       | 0.783      | 0.103    | 0.391            | 0.053          | 0.319                | 0.041              | 0.877                   | 0.042                 | 0.297                 | 0.040               | 0.145        | 0.000           | 0.000         | 34                    | 1.000           | 0.000         | 13               |
| qwen/qwen3.5-9b                   | 62       | 2.484         | 0.134       | 0.597      | 0.099    | 0.298            | 0.055          | 0.129                | 0.027              | 0.549                   | 0.086                 | 0.116                 | 0.025               | 0.274        | 0.000           | 0.000         | 22                    | 1.000           | 0.000         | 8                |

## Round metrics — by model x prompt method

`ambition` = words the codemaster commits one clue to (`count`); `yield` = targets that clue actually bought; `yield_ratio` = yield / ambition. `intended_*` compare the words aimed at with the words hit; `n_lucky_mean` counts targets found that were *not* aimed at. `early_stop_rate` and `bonus_take_rate` are over their eligible rounds only — `n_*_eligible` gives those denominators.

| model                             | method             | n_rounds | ambition_mean | ambition_se | yield_mean | yield_se | yield_ratio_mean | yield_ratio_se | intended_recall_mean | intended_recall_se | intended_precision_mean | intended_precision_se | intended_jaccard_mean | intended_jaccard_se | n_lucky_mean | early_stop_rate | early_stop_se | n_early_stop_eligible | bonus_take_rate | bonus_take_se | n_bonus_eligible |
|-----------------------------------|--------------------|----------|---------------|-------------|------------|----------|------------------|----------------|----------------------|--------------------|-------------------------|-----------------------|-----------------------|---------------------|--------------|-----------------|---------------|-----------------------|-----------------|---------------|------------------|
| meta-llama/llama-3.3-70b-instruct | strong_hebrew      | 38       | 1.474         | 0.082       | 0.737      | 0.134    | 0.539            | 0.091          | 0.421                | 0.074              | 0.833                   | 0.073                 | 0.393                 | 0.071               | 0.158        | 0.000           | 0.000         | 9                     | 1.000           | 0.000         | 15               |
| meta-llama/llama-3.3-70b-instruct | translate_pipeline | 29       | 1.690         | 0.087       | 0.759      | 0.183    | 0.500            | 0.114          | 0.293                | 0.080              | 0.548                   | 0.112                 | 0.239                 | 0.069               | 0.345        | 0.000           | 0.000         | 8                     | 1.000           | 0.000         | 9                |
| openai/gpt-4o-mini                | strong_hebrew      | 34       | 2.000         | 0.112       | 0.794      | 0.157    | 0.412            | 0.081          | 0.353                | 0.066              | 0.917                   | 0.047                 | 0.331                 | 0.063               | 0.118        | 0.000           | 0.000         | 15                    | 1.000           | 0.000         | 7                |
| openai/gpt-4o-mini                | translate_pipeline | 35       | 2.143         | 0.083       | 0.771      | 0.136    | 0.371            | 0.068          | 0.286                | 0.050              | 0.842                   | 0.067                 | 0.264                 | 0.049               | 0.171        | 0.000           | 0.000         | 19                    | 1.000           | 0.000         | 6                |
| qwen/qwen3.5-9b                   | strong_hebrew      | 30       | 2.267         | 0.197       | 0.567      | 0.133    | 0.331            | 0.088          | 0.083                | 0.032              | 0.346                   | 0.119                 | 0.072                 | 0.028               | 0.367        | 0.000           | 0.000         | 9                     | 1.000           | 0.000         | 5                |
| qwen/qwen3.5-9b                   | translate_pipeline | 32       | 2.688         | 0.176       | 0.625      | 0.147    | 0.268            | 0.068          | 0.172                | 0.042              | 0.738                   | 0.104                 | 0.156                 | 0.040               | 0.188        | 0.000           | 0.000         | 13                    | 1.000           | 0.000         | 3                |

## Round metrics — by board style

`ambition` = words the codemaster commits one clue to (`count`); `yield` = targets that clue actually bought; `yield_ratio` = yield / ambition. `intended_*` compare the words aimed at with the words hit; `n_lucky_mean` counts targets found that were *not* aimed at. `early_stop_rate` and `bonus_take_rate` are over their eligible rounds only — `n_*_eligible` gives those denominators.

| board_style | n_rounds | ambition_mean | ambition_se | yield_mean | yield_se | yield_ratio_mean | yield_ratio_se | intended_recall_mean | intended_recall_se | intended_precision_mean | intended_precision_se | intended_jaccard_mean | intended_jaccard_se | n_lucky_mean | early_stop_rate | early_stop_se | n_early_stop_eligible | bonus_take_rate | bonus_take_se | n_bonus_eligible |
|-------------|----------|---------------|-------------|------------|----------|------------------|----------------|----------------------|--------------------|-------------------------|-----------------------|-----------------------|---------------------|--------------|-----------------|---------------|-----------------------|-----------------|---------------|------------------|
| unspecified | 198      | 2.030         | 0.059       | 0.712      | 0.060    | 0.407            | 0.035          | 0.275                | 0.026              | 0.733                   | 0.038                 | 0.250                 | 0.024               | 0.217        | 0.000           | 0.000         | 73                    | 1.000           | 0.000         | 45               |

## Round metrics — by model x board style

`ambition` = words the codemaster commits one clue to (`count`); `yield` = targets that clue actually bought; `yield_ratio` = yield / ambition. `intended_*` compare the words aimed at with the words hit; `n_lucky_mean` counts targets found that were *not* aimed at. `early_stop_rate` and `bonus_take_rate` are over their eligible rounds only — `n_*_eligible` gives those denominators.

| model                             | board_style | n_rounds | ambition_mean | ambition_se | yield_mean | yield_se | yield_ratio_mean | yield_ratio_se | intended_recall_mean | intended_recall_se | intended_precision_mean | intended_precision_se | intended_jaccard_mean | intended_jaccard_se | n_lucky_mean | early_stop_rate | early_stop_se | n_early_stop_eligible | bonus_take_rate | bonus_take_se | n_bonus_eligible |
|-----------------------------------|-------------|----------|---------------|-------------|------------|----------|------------------|----------------|----------------------|--------------------|-------------------------|-----------------------|-----------------------|---------------------|--------------|-----------------|---------------|-----------------------|-----------------|---------------|------------------|
| meta-llama/llama-3.3-70b-instruct | unspecified | 67       | 1.567         | 0.061       | 0.746      | 0.109    | 0.522            | 0.071          | 0.366                | 0.055              | 0.719                   | 0.066                 | 0.326                 | 0.051               | 0.239        | 0.000           | 0.000         | 17                    | 1.000           | 0.000         | 24               |
| openai/gpt-4o-mini                | unspecified | 69       | 2.072         | 0.069       | 0.783      | 0.103    | 0.391            | 0.053          | 0.319                | 0.041              | 0.877                   | 0.042                 | 0.297                 | 0.040               | 0.145        | 0.000           | 0.000         | 34                    | 1.000           | 0.000         | 13               |
| qwen/qwen3.5-9b                   | unspecified | 62       | 2.484         | 0.134       | 0.597      | 0.099    | 0.298            | 0.055          | 0.129                | 0.027              | 0.549                   | 0.086                 | 0.116                 | 0.025               | 0.274        | 0.000           | 0.000         | 22                    | 1.000           | 0.000         | 8                |

## Round metrics — by model x method x board style

`ambition` = words the codemaster commits one clue to (`count`); `yield` = targets that clue actually bought; `yield_ratio` = yield / ambition. `intended_*` compare the words aimed at with the words hit; `n_lucky_mean` counts targets found that were *not* aimed at. `early_stop_rate` and `bonus_take_rate` are over their eligible rounds only — `n_*_eligible` gives those denominators.

| model                             | method             | board_style | n_rounds | ambition_mean | ambition_se | yield_mean | yield_se | yield_ratio_mean | yield_ratio_se | intended_recall_mean | intended_recall_se | intended_precision_mean | intended_precision_se | intended_jaccard_mean | intended_jaccard_se | n_lucky_mean | early_stop_rate | early_stop_se | n_early_stop_eligible | bonus_take_rate | bonus_take_se | n_bonus_eligible |
|-----------------------------------|--------------------|-------------|----------|---------------|-------------|------------|----------|------------------|----------------|----------------------|--------------------|-------------------------|-----------------------|-----------------------|---------------------|--------------|-----------------|---------------|-----------------------|-----------------|---------------|------------------|
| meta-llama/llama-3.3-70b-instruct | strong_hebrew      | unspecified | 38       | 1.474         | 0.082       | 0.737      | 0.134    | 0.539            | 0.091          | 0.421                | 0.074              | 0.833                   | 0.073                 | 0.393                 | 0.071               | 0.158        | 0.000           | 0.000         | 9                     | 1.000           | 0.000         | 15               |
| meta-llama/llama-3.3-70b-instruct | translate_pipeline | unspecified | 29       | 1.690         | 0.087       | 0.759      | 0.183    | 0.500            | 0.114          | 0.293                | 0.080              | 0.548                   | 0.112                 | 0.239                 | 0.069               | 0.345        | 0.000           | 0.000         | 8                     | 1.000           | 0.000         | 9                |
| openai/gpt-4o-mini                | strong_hebrew      | unspecified | 34       | 2.000         | 0.112       | 0.794      | 0.157    | 0.412            | 0.081          | 0.353                | 0.066              | 0.917                   | 0.047                 | 0.331                 | 0.063               | 0.118        | 0.000           | 0.000         | 15                    | 1.000           | 0.000         | 7                |
| openai/gpt-4o-mini                | translate_pipeline | unspecified | 35       | 2.143         | 0.083       | 0.771      | 0.136    | 0.371            | 0.068          | 0.286                | 0.050              | 0.842                   | 0.067                 | 0.264                 | 0.049               | 0.171        | 0.000           | 0.000         | 19                    | 1.000           | 0.000         | 6                |
| qwen/qwen3.5-9b                   | strong_hebrew      | unspecified | 30       | 2.267         | 0.197       | 0.567      | 0.133    | 0.331            | 0.088          | 0.083                | 0.032              | 0.346                   | 0.119                 | 0.072                 | 0.028               | 0.367        | 0.000           | 0.000         | 9                     | 1.000           | 0.000         | 5                |
| qwen/qwen3.5-9b                   | translate_pipeline | unspecified | 32       | 2.688         | 0.176       | 0.625      | 0.147    | 0.268            | 0.068          | 0.172                | 0.042              | 0.738                   | 0.104                 | 0.156                 | 0.040               | 0.188        | 0.000           | 0.000         | 13                    | 1.000           | 0.000         | 3                |

## Stop behaviour — counts and shares

| model                             | board_style | n_rounds | miss_before_quota | miss_on_bonus_guess | bonus_taken_correct | game_won_midround | miss_before_quota_share | miss_on_bonus_guess_share | bonus_taken_correct_share | game_won_midround_share |
|-----------------------------------|-------------|----------|-------------------|---------------------|---------------------|-------------------|-------------------------|---------------------------|---------------------------|-------------------------|
| meta-llama/llama-3.3-70b-instruct | unspecified | 67       | 41                | 17                  | 7                   | 2                 | 0.612                   | 0.254                     | 0.104                     | 0.030                   |
| openai/gpt-4o-mini                | unspecified | 69       | 55                | 10                  | 3                   | 1                 | 0.797                   | 0.145                     | 0.043                     | 0.014                   |
| qwen/qwen3.5-9b                   | unspecified | 62       | 54                | 6                   | 2                   | 0                 | 0.871                   | 0.097                     | 0.032                     | 0.000                   |

## Compliance and retries

Per-*call* compliance. A model that only produces a legal clue after several corrective retries is less reliable than one that gets it right first time, even at an equal win rate.

| model                             | n_games | codemaster_compliance_rate_mean | codemaster_compliance_rate_se | guesser_compliance_rate_mean | guesser_compliance_rate_se | codemaster_call_failures_mean | total_api_calls_mean | rejection_reasons                                                                                      |
|-----------------------------------|---------|---------------------------------|-------------------------------|------------------------------|----------------------------|-------------------------------|----------------------|--------------------------------------------------------------------------------------------------------|
| meta-llama/llama-3.3-70b-instruct | 8       | 0.821                           | 0.070                         | 0.937                        | 0.033                      | 0.000                         | 26.000               | targets_not_on_board: 13, json_parse: 11, guess_not_available: 6, clue_on_board: 1                     |
| openai/gpt-4o-mini                | 8       | 0.818                           | 0.042                         | 0.962                        | 0.021                      | 0.000                         | 26.625               | clue_on_board: 13, guess_not_available: 6, targets_not_on_board: 4, json_parse: 1                      |
| qwen/qwen3.5-9b                   | 8       | 0.532                           | 0.097                         | 0.906                        | 0.036                      | 0.250                         | 28.875               | json_parse: 42, targets_not_on_board: 13, guess_not_available: 11, clue_on_board: 5, count_mismatch: 1 |

## How large should the next run be? — per design cell

Projected from this run's own within-cell variance. `games_per_cell` = `n_boards x n_trials` for each (model, method, board_style) cell. `*_ci_halfwidth` is the 95% interval half-width; `mdd_*` is the smallest cell-to-cell difference detectable at alpha=0.05 with 80% power; `api_calls_total` prices the whole run. This is the **most pessimistic** view — a cell holds model, method and board style all fixed, so it is answering 'can I compare two single cells?', which is rarely the question.

| games_per_cell | n_cells | games_total | win_rate_ci_halfwidth | game_length_ci_halfwidth | mdd_win_rate | mdd_game_length | api_calls_total |
|----------------|---------|-------------|-----------------------|--------------------------|--------------|-----------------|-----------------|
| 5              | 6       | 30          | 0.268                 | 3.261                    | 0.543        | 6.593           | 825.000         |
| 10             | 6       | 60          | 0.190                 | 2.306                    | 0.384        | 4.662           | 1650.000        |
| 20             | 6       | 120         | 0.134                 | 1.631                    | 0.271        | 3.296           | 3300.000        |
| 40             | 6       | 240         | 0.095                 | 1.153                    | 0.192        | 2.331           | 6600.000        |

## How large should the next run be? — per comparison

The same projection for the comparisons actually of interest, each of which collapses over the other two factors and so pools far more games per arm. Size the run from this table: pick the comparison that has to come out conclusive, find the smallest `games_per_cell` whose `mdd_win_rate` is below the effect you care about, then read the cost off the per-cell table above.

| comparison                            | levels | games_per_cell | games_per_arm | mdd_win_rate | mdd_game_length |
|---------------------------------------|--------|----------------|---------------|--------------|-----------------|
| model (collapsing the other factors)  | 3      | 5              | 10.000        | 0.384        | 4.662           |
| model (collapsing the other factors)  | 3      | 10             | 20.000        | 0.271        | 3.296           |
| model (collapsing the other factors)  | 3      | 20             | 40.000        | 0.192        | 2.331           |
| model (collapsing the other factors)  | 3      | 40             | 80.000        | 0.136        | 1.648           |
| method (collapsing the other factors) | 2      | 5              | 15.000        | 0.313        | 3.806           |
| method (collapsing the other factors) | 2      | 10             | 30.000        | 0.221        | 2.691           |
| method (collapsing the other factors) | 2      | 20             | 60.000        | 0.157        | 1.903           |
| method (collapsing the other factors) | 2      | 40             | 120.000       | 0.111        | 1.346           |

## Figures

### outcome composition

![01_outcome_composition](figures/01_outcome_composition.png)

### game length

![02_game_length](figures/02_game_length.png)

### ambiguity ladder

![03_ambiguity_ladder](figures/03_ambiguity_ladder.png)

### stop behaviour

![04_stop_behaviour](figures/04_stop_behaviour.png)

### intended overlap

![05_intended_overlap](figures/05_intended_overlap.png)

### ambition vs yield

![06_ambition_vs_yield](figures/06_ambition_vs_yield.png)
