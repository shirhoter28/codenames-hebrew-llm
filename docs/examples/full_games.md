# Appendix: complete games

Regenerate or browse any of these with:

```
python scripts/show_game.py results/<run_id> --style dual_100 --seed 10 \
    --method translate --cm gemini --guesser gemini --cc free [--md]
python scripts/show_game.py results/<run_id> --list --style natural --seed 5
```

Board key: `T` your words · `O` opponent · `-` civilian · `X` assassin.

## Drift case in full: הודו glossed *Turkey* in round 3 and *India* in round 6

The clue follows the gloss both times — חיה (animal) then ארץ (country). Note also
עמוד drifting pillar→page→pillar and חום brown→fever→heat on the same board.

### google/gemini-2.5-flash (codemaster, translate_pipeline) vs google/gemini-2.5-flash (guesser) · board dual_100 seed 10 trial 0 · count free · win, 6 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O תפוח | T בר | - כבד | - צדק | - אוכל |
| O אוצר | - שפה | T נחש | O חום | T זריקה |
| T ביצה | T הודו | - מוצא | T נעל | T עמוד |
| X משפט | T מקל | O גזר | O מטר | - אוגר |
| O מאושר | O סמל | - מעבר | T בול | O עין |

YOUR WORDS (9): בר, נחש, זריקה, ביצה, הודו, נעל, עמוד, מקל, בול
OPPONENT (8): תפוח, אוצר, חום, גזר, מטר, מאושר, סמל, עין
CIVILIAN (7): כבד, צדק, אוכל, שפה, מוצא, אוגר, מעבר
ASSASSIN (1): משפט

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | מוט (rod) | 2 | בר, מקל  /  bar, stick | מקל [T], עמוד [T] | stopped_early |
| 2 | דואר (mail) | 2 | נעל, בול  /  shoe, stamp | בול [T], סמל [O] | hit_opponent |
| 3 | חיה (animal) | 3 | נחש, ביצה, הודו  /  snake, egg, Turkey | נחש [T], ביצה [T], אוגר [-] | hit_civilian |
| 4 | ספורט (sport) | 2 | בר, זריקה  /  bar, throw | זריקה [T], מטר [O] | hit_opponent |
| 5 | רגל (foot) | 2 | בר, נעל  /  son/bar/pure, shoe | נעל [T], מוצא [-] | hit_civilian |
| 6 | ארץ (country) | 2 | בר, הודו  /  bar, India | הודו [T], בר [T] | all_correct |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 |
|---|---|---|---|---|---|---|
| **בר** | bar | bar | bar | bar | son/bar/pure | bar |
| **זריקה** | shot | throw | throw | throw | throw/injection | throw/injection |
| **ביצה** | egg | egg | egg | egg | egg/swamp | egg |
| **הודו** | turkey | Turkey | Turkey | India | India/thanked | India |
| **עמוד** | pillar | page | pillar | pillar | pillar/page | page/pillar |
| **מקל** | stick | stick | stick | stick | stick/cane | stick |
| **בול** | stamp | stamp | stamp | stamp | stamp | stamp/bullseye |
| **חום** | brown/fever | heat | heat | brown | brown/fever/heat | brown/heat |
| **גזר** | carrot | carrot | carrot | carrot | carrot/decreed | carrot |
| **מטר** | meter/rain | meter | meter | meter | meter/rain | meter/rain |
| **מאושר** | happy | happy | happy | happy | happy/approved | happy |
| **סמל** | symbol | symbol | symbol | symbol | symbol/emblem | symbol |
| **עין** | eye | eye | eye | eye | eye/spring | eye |
| **כבד** | heavy/liver | liver | liver | heavy | heavy/liver | heavy/liver |
| **צדק** | justice | justice | justice | justice | justice/Jupiter | justice |
| **שפה** | language/lip | language | language | language | language/lip | language/lip |
| **מוצא** | origin | origin | origin | origin | origin/found | origin/finds |
| **אוגר** | hamster | hamster | hamster | hamster | hamster/hoarder | hamster |
| **מעבר** | passage | passage | passage | passage | passage/beyond | passage/transition |
| **משפט** | sentence/trial | sentence | sentence | sentence | sentence/trial | sentence/trial |

## Root-echo in full: clue מקצב for target קצב

The clue is the target with a מ- prefix. `clue_on_board` passes it because the strings
are not identical. חצב is dragged along on sound alone — see the sound section below.

### openai/gpt-4o-mini (codemaster, strong_hebrew) vs openai/gpt-4o-mini (guesser) · board dual_100 seed 12 trial 0 · count free · loss (assassin), 12 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O אלה | T מנוע | - בר | O בוקר | X חום |
| T אוגר | O גזר | T אולם | T קצב | O אלף |
| - פנים | O קש | - עצם | O עמוד | - מאבק |
| T בסיס | T מעמד | - בול | O מלח | O חול |
| - חולצה | T מקל | T חצב | - שפה | T אמן |

YOUR WORDS (9): מנוע, אוגר, אולם, קצב, בסיס, מעמד, מקל, חצב, אמן
OPPONENT (8): אלה, בוקר, גזר, אלף, קש, עמוד, מלח, חול
CIVILIAN (7): בר, פנים, עצם, מאבק, בול, חולצה, שפה
ASSASSIN (1): חום

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | יוצר | 2 | אמן, מעמד | אמן [T], מאבק [-] | hit_civilian |
| 2 | חג | 2 | מנוע, אוגר | בר [-] | hit_civilian |
| 3 | כלי | 2 | מנוע, מקל | מנוע [T], מקל [T], בסיס [T] | all_correct |
| 4 | חכם | 2 | קצב, מעמד | שפה [-] | hit_civilian |
| 5 | חדר | 2 | אולם, מעמד | אולם [T], פנים [-] | hit_civilian |
| 6 | חג | 2 | אוגר, קצב | חולצה [-] | hit_civilian |
| 7 | עכבר | 1 | אוגר | אוגר [T], גזר [O] | hit_opponent |
| 8 | מקצב | 3 | קצב, מעמד, חצב | קצב [T], מלח [O] | hit_opponent |
| 9 | שלטון | 2 | מעמד, חצב | עמוד [O] | hit_opponent |
| 10 | מערכת | 2 | מעמד, חצב | בוקר [O] | hit_opponent |
| 11 | כוח | 2 | מעמד, חצב | עצם [-] | hit_civilian |
| 12 | סרגל | 2 | מעמד, חצב | חום [X] | hit_assassin |

## Over-extension in full: every intended target found, then the assassin

Round 1 is the whole game: clue תרבות for two words, the guesser finds both, then
guesses פיראט — the assassin — with nothing left to justify it.

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board natural seed 5 trial 0 · count free · loss (assassin), 1 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T חייזר | T זריקה | O קוד | O קרן | - מסע |
| O כף | - קפה | X פיראט | T אירופה | T מחילה |
| T מופע | T תיאטרון | T חוף | O אלה | - צופים |
| - חג | - קלע | O בית-ספר | - אחר | - חייל |
| T חצב | O פנדה | T מזל | O מיטה | O פרח |

YOUR WORDS (9): חייזר, זריקה, אירופה, מחילה, מופע, תיאטרון, חוף, חצב, מזל
OPPONENT (8): קוד, קרן, כף, אלה, בית-ספר, פנדה, מיטה, פרח
CIVILIAN (7): מסע, קפה, צופים, חג, קלע, אחר, חייל
ASSASSIN (1): פיראט

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | תרבות | 2 | תיאטרון, מופע | תיאטרון [T], מופע [T], פיראט [X] | hit_assassin |

