# Full games behind the examples

70 curated examples across 61 games, rendered whole.
The excerpt-level arguments live in [`codemaster_translation_drift.md`](codemaster_translation_drift.md) and [`guesser_behaviour.md`](guesser_behaviour.md); this is the evidence behind them.

Board key: `T` your words · `O` opponent · `-` civilian · `X` assassin.

Regenerate with `python scripts/render_examples.py results/<run_id> ...` after editing [`manifest.json`](manifest.json).

## Contents

- **Translation drift** — 16 examples
- **Root-echo clues** — 14 examples
- **Sound-paired targets** — 16 examples
- **Over-extension into the assassin** — 12 examples
- **Assassin on the first guess** — 12 examples


---

# Translation drift

## הודו: turkey → india, and the clue follows the flip

Gloss by round: {'3': 'turkey', '6': 'india'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 10 --method translate \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

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

## הודו: same flip under gpt-4o-mini, ending on the assassin

Gloss by round: {'3': 'turkey', '4': 'india'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 10 --method translate \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, translate_pipeline) vs openai/gpt-4o-mini (guesser) · board dual_100 seed 10 trial 0 · count free · loss (assassin), 4 rounds · 20260823T191234131145Z

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
| 1 | ספורט (sport) | 3 | בר, נחש, זריקה  /  bar, snake, throw | מקל [T], זריקה [T], אוכל [-] | hit_civilian |
| 2 | חיה (animal) | 3 | בר, נחש, נעל  /  bar, snake, shoe | נחש [T], אוגר [-] | hit_civilian |
| 3 | נוצה (feather) | 3 | בר, ביצה, הודו  /  bar, egg, turkey | נעל [T], בר [T], ביצה [T], צדק [-] | hit_civilian |
| 4 | מכתב (letter) | 3 | הודו, עמוד, בול  /  India, post, stamp | משפט [X] | hit_assassin |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 |
|---|---|---|---|---|
| **הודו** | turkey | turkey | turkey | India |
| **עמוד** | column | column | column | post |
| **אוגר** | hamster | hamster | hamster | gerbil |
| **מעבר** | passage | passage | passage | transition |

## מלון: melon → hotel on consecutive rounds

Gloss by round: {'1': 'melon', '2': 'hotel'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 13 --method translate \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc min2
```

### google/gemini-2.5-flash (codemaster, translate_pipeline) vs google/gemini-2.5-flash (guesser) · board dual_100 seed 13 trial 0 · count min2 · win, 11 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - זרוע | X פנים | T תפוח | O מעמד | O חלק |
| T צדק | - משפט | T מלון | T מלח | O לבנה |
| T אלף | T ירח | - אח | - קצב | O ערב |
| - גזר | T שיח | O קרן | T הודו | T קניון |
| O בול | - גר | O פה | O בוקר | - אלה |

YOUR WORDS (9): תפוח, צדק, מלון, מלח, אלף, ירח, שיח, הודו, קניון
OPPONENT (8): מעמד, חלק, לבנה, ערב, קרן, בול, פה, בוקר
CIVILIAN (7): זרוע, משפט, אח, קצב, גזר, גר, אלה
ASSASSIN (1): פנים

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | פרי (fruit) | 2 | תפוח, מלון  /  apple, melon | תפוח [T], גזר [-] | hit_civilian |
| 2 | נסיעה (travel) | 3 | מלון, קניון, הודו  /  hotel, mall, India | מלון [T], בוקר [O] | hit_opponent |
| 3 | שמימי (celestial) | 2 | ירח, הודו  /  moon, India | ירח [T], לבנה [O] | hit_opponent |
| 4 | מדינה (country) | 2 | הודו, מלח  /  india, salt | הודו [T] | stopped_early |
| 5 | טבע (nature) | 2 | קניון, שיח  /  canyon, bush | קרן [O] | hit_opponent |
| 6 | חוק (law) | 2 | צדק, מלח  /  justice, salt | משפט [-] | hit_civilian |
| 7 | חוק (law) | 3 | צדק, שיח, קניון  /  justice, bush, canyon | צדק [T], חלק [O] | hit_opponent |
| 8 | ראשית (beginning) | 2 | מלח, אלף  /  salt, thousand/alpha/ox | אלף [T] | stopped_early |
| 9 | מדבר (Desert) | 2 | מלח, קניון  /  salt, canyon/mall | קניון [T], פה [O] | hit_opponent |
| 10 | צמח (plant) | 2 | מלח, שיח  /  salt, bush | שיח [T] | stopped_early |
| 11 | תיבול (seasoning) | 1 | מלח  /  salt | מלח [T] | all_correct |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 | r9 | r10 | r11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **מעמד** | status | status | status | status | status | status | status/stand | status/stand | status/stand | status | status |
| **ערב** | evening | evening | evening | evening | evening | evening | evening/pleasant/guarantor | evening/pleasant | evening/pleasant | evening | evening/pleasant |
| **בול** | stamp | stamp | stamp | stamp | stamp | stamp | stamp | stamp/bullseye | stamp | stamp | stamp/bullet |
| **זרוע** | arm | arm | arm | arm | arm | arm | arm/sown | arm/sown | arm | arm | arm |
| **אח** | brother | brother | brother | brother | brother | brother | brother/fireplace | brother/fireplace | brother/fireplace | brother | brother/fireplace |
| **קצב** | rhythm | rhythm | rhythm | rhythm | rhythm | rhythm | rhythm/butcher | rhythm/butcher | rhythm/butcher | rhythm | rhythm/butcher |
| **גר** | lives | lives | foreigner | lives | resident | foreigner | lives/stranger | lives/resident | lives/stranger | resident | lives/stranger |
| **אלה** | goddess | goddess | goddess | these | goddess | goddess | goddess/these/club | these/goddess/oak | goddess/club | goddess | these/goddess/club |
| **פנים** | face | face | face | face | face | face | face/inside | face/inside | face/inside | face | face/inside |
| **שיח** | bush | bush | bush | bush | bush | bush | bush/discourse | bush/conversation | bush/conversation | bush |  |
| **קניון** | mall | mall | canyon | canyon | canyon | canyon | mall/canyon | canyon/mall | canyon/mall | mall |  |
| **פה** | mouth | mouth | mouth | mouth | mouth | mouth | mouth/here | mouth/here | mouth | mouth |  |
| **צדק** | justice | justice | justice | justice | justice | justice | justice | justice/Jupiter |  | justice |  |
| **מלון** | melon | hotel | hotel | melon | melon | hotel | melon/hotel | melon/hotel |  | hotel |  |
| **אלף** | thousand | thousand | thousand | thousand | thousand | thousand | thousand/alpha/ox | thousand/alpha/ox |  | thousand |  |
| **הודו** | India | India | India | india | india | india | India/they confessed | India/they thanked |  | India |  |
| **חלק** | part | part | part | part | part | part | part/smooth | part/smooth |  | smooth |  |
| **לבנה** | brick | brick | brick | brick | brick | brick | brick | brick/white (female) |  | brick |  |
| **קרן** | horn | horn | horn | horn | horn | horn | horn/fund/ray | horn/ray/fund |  | horn |  |
| **בוקר** | morning | morning | morning | morning | morning | morning | morning/cowboy | morning/cowboy |  | morning |  |
| **משפט** | sentence | sentence | sentence | sentence | sentence | sentence | sentence/trial | sentence/trial |  | sentence |  |
| **גזר** | carrot | carrot | carrot | carrot | carrot | carrot | carrot | carrot/decree |  | carrot |  |

## קניון: canyon → mall

Gloss by round: {'4': 'canyon', '8': 'mall'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 5 --method translate \
    --cm gemini-2.5-flash --guesser llama-3.3-70b-instruct --cc free
```

### google/gemini-2.5-flash (codemaster, translate_pipeline) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_100 seed 5 trial 0 · count free · win, 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O מרוצים | T מטען | O מאבק | O גזר | O ערב |
| - סוף | X לבנה | T קלע | T קש | - סמל |
| O אוגר | T אלף | T אמן | - אחוז | T מקל |
| - הודו | O מעבר | - זקן | - מטה | O קצב |
| O חפץ | T קניון | T נעל | - שר | T בסיס |

YOUR WORDS (9): מטען, קלע, קש, אלף, אמן, מקל, קניון, נעל, בסיס
OPPONENT (8): מרוצים, מאבק, גזר, ערב, אוגר, מעבר, קצב, חפץ
CIVILIAN (7): סוף, סמל, אחוז, הודו, זקן, מטה, שר
ASSASSIN (1): לבנה

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | יסוד (Foundation) | 3 | מטען, בסיס, מקל  /  cargo, base, stick | בסיס [T], מטה [-] | hit_civilian |
| 2 | נשק (weapon) | 2 | קלע, מקל  /  slingshot, stick | קלע [T], מקל [T], קש [T] | all_correct |
| 3 | מספר (number) | 2 | אלף, אמן  /  thousand, artist | מרוצים [O] | hit_opponent |
| 4 | הובלה (transport) | 2 | מטען, קניון  /  cargo, canyon | מטען [T], מעבר [O] | hit_opponent |
| 5 | התחלה (beginning) | 3 | אלף, אמן, נעל  /  thousand/alpha, artist/amen, shoe | הודו [-] | hit_civilian |
| 6 | ראשון (first) | 3 | אלף, אמן, נעל  /  thousand/aleph, artist/amen, shoe | אלף [T], אוגר [O] | hit_opponent |
| 7 | יצירה (creation) | 2 | אמן, נעל  /  artist, shoe | אמן [T], סמל [-] | hit_civilian |
| 8 | ביגוד (clothing) | 2 | קניון, נעל  /  mall, shoe | נעל [T], קניון [T] | all_correct |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 |
|---|---|---|---|---|---|---|---|---|
| **אלף** | thousand | thousand | thousand | thousand | thousand/alpha | thousand/aleph | thousand | thousand |
| **אמן** | artist | artist | artist | artist | artist/amen | artist/amen | artist | artist |
| **קניון** | mall | mall | canyon | canyon | canyon/mall | mall/canyon | mall | mall |
| **מאבק** | struggle | struggle | struggle | struggle | struggle | struggle/dust | struggle | struggle |
| **גזר** | carrot | carrot | carrot | carrot | carrot/decree | carrot/decree | carrot | carrot |
| **ערב** | evening | evening | evening | evening | evening/pleasant | evening/pleasant/guarantor | evening | evening |
| **אוגר** | hamster | hamster | hamster | hamster | hamster/hoarder | hamster/hoarder | hamster | hamster |
| **קצב** | rhythm | rhythm | rhythm | rhythm | rhythm/butcher | rhythm/butcher | rhythm | rhythm |
| **חפץ** | object | object | object | object | object/desire | object/desire | object | object |
| **אחוז** | percent | percent | percent | percent | percent | percent/held | percent | percent |
| **זקן** | old man | beard | beard | beard | old man/beard | old man/beard | old man | old man |
| **שר** | minister | minister | minister | minister | minister/sing | minister/sing | minister | minister |
| **לבנה** | brick | brick | brick | brick | brick/moon | brick/moon | brick | brick |
| **מטען** | cargo | cargo | cargo | cargo | charge/cargo |  | cargo | cargo |
| **קלע** | slingshot | slingshot | slingshot | shooter | slingshot/shooter |  | slingshot | slingshot |
| **מרוצים** | races | satisfied | races | satisfied | satisfied/races |  | satisfied | satisfied |
| **מעבר** | passage | passage | passage | passage | passage/transition |  | passage | passage |
| **הודו** | India | India | india | India | India/thanked |  | India | India |
| **מטה** | staff | staff | staff | staff | staff/down |  | staff | staff |

## אלים: violent → gods

Gloss by round: {'2': 'violent', '4': 'gods'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 27 --method translate \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, translate_pipeline) vs google/gemini-2.5-flash (guesser) · board dual_100 seed 27 trial 0 · count free · loss (assassin), 7 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T אלים | T רב | O נהג | O סרט | O בונה |
| - אולם | - מגדל | T אטום | T חג | T שחקן |
| X אלף | - כבד | - גב | O שדה | - גזר |
| O מטה | - דוד | T מקל | T מקור | O פה |
| T לבנה | O דבר | - סוף | T משפט | O צדק |

YOUR WORDS (9): אלים, רב, אטום, חג, שחקן, מקל, מקור, לבנה, משפט
OPPONENT (8): נהג, סרט, בונה, שדה, מטה, פה, דבר, צדק
CIVILIAN (7): אולם, מגדל, כבד, גב, גזר, דוד, סוף
ASSASSIN (1): אלף

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | יסוד (Element) | 3 | אטום, מקור, לבנה  /  atom, source, brick | מקור [T], לבנה [T], מגדל [-] | hit_civilian |
| 2 | פיזי (Physical) | 3 | אלים, אטום, מקל  /  violent, atom, stick | כבד [-] | hit_civilian |
| 3 | דתי (Religious) | 3 | רב, חג, משפט  /  rabbi, holiday, sentence | רב [T], חג [T] | stopped_early |
| 4 | מיתולוגיה (mythology) | 2 | אטום, אלים  /  atomic, gods | אלים [T], דוד [-] | hit_civilian |
| 5 | קטן (small) | 2 | אטום, מקל  /  atom, stick | מטה [O] | hit_opponent |
| 6 | מבנה (structure) | 2 | אטום, משפט  /  atomic, sentence | בונה [O] | hit_opponent |
| 7 | רכיב (Component) | 2 | אטום, משפט  /  atom, sentence | אטום [T], אלף [X] | hit_assassin |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 |
|---|---|---|---|---|---|---|---|
| **אלים** | gods | violent | gods | gods | violent/gods | violent | violent |
| **רב** | rabbi/much | rabbi/much | rabbi | rabbi | rabbi/many | rabbi | rabbi |
| **אטום** | atom/opaque | atom/opaque | atom | atomic | atom/sealed | atomic | atom |
| **חג** | holiday/festival | holiday | holiday | holiday | holiday/belt | holiday | holiday |
| **שחקן** | player/actor | player/actor | player | player | player/actor | player | player |
| **מקור** | source/beak | source/beak | source | source | source/beak | source | source |
| **לבנה** | brick/moon | brick/moon | brick | brick | brick/moon | brick | brick |
| **משפט** | sentence/trial | sentence/trial | sentence | sentence | sentence/trial | sentence | sentence |
| **סרט** | film/ribbon | film/ribbon | movie | film | movie/ribbon | film | movie |
| **בונה** | builder/beaver | builder | builder | builder | builds/builder | builds | builds |
| **מטה** | wand/bed/down | wand/bed/branch | staff | staff | staff/leans | staff | staff |
| **פה** | mouth/here | mouth/here | mouth | mouth | mouth/here | mouth | mouth |
| **דבר** | thing/speak/plague | thing/speak/plague | thing | thing | thing/speak | thing | thing |
| **צדק** | justice/Jupiter | justice/Jupiter | justice | justice | justice/Jupiter | justice | justice |
| **כבד** | heavy/liver | heavy/liver | heavy | heavy | heavy/liver | heavy | heavy |
| **גזר** | carrot/decree | carrot/decree | carrot | carrot | carrot/decreed | carrot | carrot |
| **דוד** | uncle/kettle | uncle/kettle | uncle | uncle | uncle/kettle | uncle | uncle |
| **אלף** | thousand/ox/to teach | thousand/ox/aleph | thousand | thousand | thousand/ox | thousand | thousand |

## אלים: gods → violent → hedged, five rounds on one target pair

Gloss by round: {'8': 'gods', '9': 'gods', '10': 'violent', '11': 'violent', '12': 'violent', '13': 'violent/gods'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 29 --method translate \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc min2
```

### google/gemini-2.5-flash (codemaster, translate_pipeline) vs google/gemini-2.5-flash (guesser) · board dual_100 seed 29 trial 0 · count min2 · loss (assassin), 14 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T פה | - מלון | O אלה | O חג | - מטר |
| - אופן | T מצרים | X גזר | T אלים | T מדבר |
| O צדק | O חבל | T אחר | T בונה | - סמל |
| T כבד | - מאבק | T כסף | T מלח | O עצם |
| O עין | - משפט | - מגדל | O זריקה | O חגים |

YOUR WORDS (9): פה, מצרים, אלים, מדבר, אחר, בונה, כבד, כסף, מלח
OPPONENT (8): אלה, חג, צדק, חבל, עצם, עין, זריקה, חגים
CIVILIAN (7): מלון, מטר, אופן, סמל, מאבק, משפט, מגדל
ASSASSIN (1): גזר

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | ארץ (Land) | 2 | מצרים, מדבר  /  Egypt, desert | מצרים [T], מגדל [-] | hit_civilian |
| 2 | סחורה (commodity) | 2 | כסף, מלח  /  money, salt | כסף [T], מלח [T] | stopped_early |
| 3 | משקל (weight) | 2 | כבד, בונה  /  heavy, builds | כבד [T], עצם [O] | hit_opponent |
| 4 | מקום (place) | 2 | מדבר, פה  /  desert, mouth | מדבר [T], מלון [-] | hit_civilian |
| 5 | גוף (body) | 2 | בונה, פה  /  builder, mouth | עין [O] | hit_opponent |
| 6 | בנה (construct) | 2 | פה, בונה  /  mouth, builder | בונה [T], משפט [-] | hit_civilian |
| 7 | נוסף (another) | 2 | פה, אחר  /  mouth, other | אחר [T], חגים [O] | hit_opponent |
| 8 | אלוהי (divine) | 2 | פה, אלים  /  mouth, gods | אלה [O] | hit_opponent |
| 9 | אלוהי (divine) | 2 | פה, אלים  /  mouth, gods | צדק [O] | hit_opponent |
| 10 | תקיפה (attack) | 2 | פה, אלים  /  mouth, violent | מאבק [-] | hit_civilian |
| 11 | כוח (force) | 2 | פה, אלים  /  mouth, violent | חבל [O] | hit_opponent |
| 12 | כוח (force) | 2 | פה, אלים  /  mouth, violent | אופן [-] | hit_civilian |
| 13 | אלוהי (Divine) | 2 | פה, אלים  /  mouth/here, violent/gods | אלים [T], חג [O] | hit_opponent |
| 14 | גוף (body) | 1 | פה  /  mouth | גזר [X] | hit_assassin |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 | r9 | r10 | r11 | r12 | r13 | r14 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **פה** | mouth/here | mouth | mouth | mouth | mouth/here | mouth | mouth | mouth | mouth | mouth | mouth | mouth | mouth/here | mouth |
| **אלים** | gods/violent | violent/gods | violent | violent | violent/gods | violent | violent | gods | gods | violent | violent | violent | violent/gods | violent |
| **חג** | holiday | holiday | holiday | holiday | holiday | holiday | holiday | holiday | holiday | holiday | holiday | holiday | holiday/belt | holiday |
| **זריקה** | throw/injection | throw/injection | throw | injection | throw/shot | throw/injection | throw | throw | throw | throw | throw | throw | throw/injection | throw |
| **מטר** | meter/rain | meter/rain | meter | meter | meter/rain | meter/rain | meter | meter | meter | meter | meter | meter | meter/rain | meter |
| **גזר** | carrot/decree/cut off | carrot/decreed | carrot | carrot | carrot/decreed | carrot/decreed | carrot | carrot | carrot | carrot | carrot | carrot | carrot/decreed | carrot |
| **אופן** | way/wheel | manner/wheel | manner | manner | manner/wheel | manner/wheel | manner | manner | manner | manner | way | manner |  | way |
| **מדבר** | desert/speaks | desert/speaks | desert | desert | desert/speaking | desert/speaking | desert | desert | desert | desert | desert |  |  | desert |
| **אחר** | other | other | other | other | other/after | other | other | other | other | other | other |  |  | other |
| **בונה** | builds | builds/builder | builds | builds | builder/builds | builder | builds | builder | builds | builds | builds |  |  | builds |
| **כבד** | heavy/liver | heavy/liver | heavy | heavy | heavy/liver | heavy/liver | heavy | heavy | heavy | heavy | heavy |  |  | heavy |
| **כסף** | money/silver | money/silver | money | money | money/silver | money/silver | money | silver | money | money | money |  |  | silver |
| **אלה** | these/goddess | these/goddess | these | these | these/goddess | these/goddess | these | goddess | these | these | these |  |  | these |
| **צדק** | justice/Jupiter | justice/Jupiter | justice | justice | justice/Jupiter | justice | justice | justice | justice | justice | justice |  |  | justice |
| **חבל** | rope/region/pity | rope/region/pity | rope | rope | rope/region | rope/region/it's a shame | rope | rope | rope | rope | rope |  |  | rope |
| **עצם** | bone/self | bone/object | bone | bone | bone/object | bone/object | bone | bone | bone | bone | bone |  |  | bone |
| **עין** | eye/spring | eye/spring | eye | eye | eye/spring | eye/spring | eye | eye | eye | eye | eye |  |  | eye |
| **מלון** | hotel | hotel | hotel | hotel | hotel | hotel | hotel | hotel | hotel | melon | hotel |  |  | hotel |
| **משפט** | sentence/trial | sentence/trial | sentence | sentence | sentence/trial | sentence/trial | sentence | sentence | sentence | sentence | sentence |  |  | sentence |

## מלח: salt → sailor, clue field moves with it

Gloss by round: {'5': 'salt', '7': 'sailor', '8': 'sailor', '9': 'sailor', '10': 'sailor'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 19 --method translate \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc min2
```

### meta-llama/llama-3.3-70b-instruct (codemaster, translate_pipeline) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_100 seed 19 trial 0 · count min2 · loss (assassin), 11 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - בוקר | - מלון | O שר | - כסף | - שפה |
| T קלע | O שדה | X אב | - בול | - קרן |
| T פה | O רב | T מלח | T מגדל | O קצב |
| T אחר | O אוגר | - מדבר | O ערב | T אולם |
| T נחש | O זריקה | T מאדים | O חגים | T נהג |

YOUR WORDS (9): קלע, פה, מלח, מגדל, אחר, אולם, נחש, מאדים, נהג
OPPONENT (8): שר, שדה, רב, קצב, אוגר, ערב, זריקה, חגים
CIVILIAN (7): בוקר, מלון, כסף, שפה, בול, קרן, מדבר
ASSASSIN (1): אב

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | בניין (building) | 3 | מגדל, אולם, פה  /  tower, hall, mouth | מגדל [T], מלון [-] | hit_civilian |
| 2 | רכב (vehicle) | 3 | קלע, נחש, נהג  /  archer, snake, driver | נהג [T], רב [O] | hit_opponent |
| 3 | אדום (red) | 3 | קלע, נחש, מאדים  /  archer, snake, Mars | אוגר [O] | hit_opponent |
| 4 | כוכב (planet) | 3 | קלע, נחש, מאדים  /  archer, snake, Mars | מאדים [T], שדה [O] | hit_opponent |
| 5 | רעל (venom) | 3 | קלע, נחש, מלח  /  archer, snake, salt | נחש [T], זריקה [O] | hit_opponent |
| 6 | פתח (opening) | 3 | קלע, פה, אולם  /  archer, mouth, hall | פה [T], שפה [-] | hit_civilian |
| 7 | חדר (room) | 3 | קלע, מלח, אולם  /  archer, sailor, hall | אולם [T], בוקר [-] | hit_civilian |
| 8 | ימי (marine) | 2 | קלע, מלח  /  archer, sailor | חגים [O] | hit_opponent |
| 9 | ימי (marine) | 2 | קלע, מלח  /  archer, sailor | שר [O] | hit_opponent |
| 10 | ים (sea) | 2 | קלע, מלח  /  archer, sailor | מלח [T], כסף [-] | hit_civilian |
| 11 | סוכן (agent) | 2 | קלע, אחר  /  archer, other | קלע [T], אב [X] | hit_assassin |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 | r9 | r10 | r11 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **פה** | mouth | mouth | mouth | mouth | mouth | mouth | here | mouth | mouth | mouth | mouth |
| **מלח** | salt | salt | salt | salt | salt | salt | sailor | sailor | sailor | sailor | salt |
| **מאדים** | Mars | Mars | Mars | Mars | Mars | mars | mars | Mars | Mars | Mars | Mars |
| **אוגר** | storekeeper | store | store | store | store | store | storekeeper | store | store | storekeeper | store |
| **ערב** | Arab | evening | evening | evening | evening | evening | evening | evening | evening | evening | evening |
| **בול** | stamp | stamp | stamp | stamp | stamp | stamp | stamp | mail | stamp | stamp | stamp |

## מטר: rain ↔ meter oscillating across five rounds

Gloss by round: {'4': 'rain', '5': 'rain', '6': 'meter/rain', '7': 'meter', '8': 'rain/meter'}

```
python scripts/show_game.py results/20260829T225350499567Z \
    --style dual_100 --seed 117 --method translate \
    --cm gemini-2.5-flash --guesser gpt-4o-mini --cc min2
```

### google/gemini-2.5-flash (codemaster, translate_pipeline) vs openai/gpt-4o-mini (guesser) · board dual_100 seed 117 trial 0 · count min2 · loss (assassin), 8 rounds · 20260829T225350499567Z

| | | | | |
|---|---|---|---|---|
| - מקור | T אלף | O מפה | T אב | - גר |
| O בוקר | - אורח | O חלק | O מוצא | - מקל |
| O אח | O צדק | T בר | X חגים | - מטען |
| T ספר | - שרת | T מטר | T מפתח | O אוגר |
| O זריקה | T משפט | T אוצר | T נהג | - ערב |

YOUR WORDS (9): אלף, אב, בר, ספר, מטר, מפתח, משפט, אוצר, נהג
OPPONENT (8): מפה, בוקר, חלק, מוצא, אח, צדק, אוגר, זריקה
CIVILIAN (7): מקור, גר, אורח, מקל, מטען, שרת, ערב
ASSASSIN (1): חגים

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | אדם (person) | 2 | אב, נהג  /  father, driver | אב [T], אורח [-] | hit_civilian |
| 2 | אותיות (letters) | 2 | אלף, ספר  /  thousand/aleph, book/count/barber | אלף [T], ספר [T], אוצר [T] | all_correct |
| 3 | דקדוק (grammar) | 2 | מפתח, משפט  /  key, sentence | משפט [T], מקור [-] | hit_civilian |
| 4 | פתוח (open) | 3 | בר, מטר, מפתח  /  bar, rain, key | מפתח [T], מפה [O] | hit_opponent |
| 5 | דרך (road) | 2 | מטר, נהג  /  rain, driver | מוצא [O] | hit_opponent |
| 6 | דרך (path) | 3 | בר, מטר, נהג  /  bar/son/grain, rain, driver | נהג [T], חלק [O] | hit_opponent |
| 7 | מידה (measure) | 2 | בר, מטר  /  bar, meter | צדק [O] | hit_opponent |
| 8 | קציר (harvest) | 2 | מטר, בר  /  rain, bar/grain | חגים [X] | hit_assassin |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 |
|---|---|---|---|---|---|---|---|---|
| **אלף** | thousand | thousand/aleph | thousand | thousand | thousand/ox/to teach | thousand/ox | thousand | thousand |
| **בר** | son/grain/clean | son/wild/field | bar | bar | son/pure/wild | bar/son/grain | bar | bar/grain |
| **ספר** | book/count/barber | book/count/barber | book | book | book/barber/to count | book/barber | book | book |
| **מטר** | meter/rain | meter/rain | meter | rain | rain | meter/rain | meter | rain/meter |
| **מפתח** | key/opener | key/developer | key | key | key | key | key | key |
| **משפט** | sentence/trial | sentence/trial | sentence | sentence | sentence/trial | sentence/trial | sentence | sentence/trial |
| **בוקר** | morning | morning/cowboy | morning | morning | morning/cowboy | morning/cowboy | morning | morning/cowboy |
| **חלק** | part/smooth | part/smooth | part | smooth | smooth/part | part/smooth | part | part/smooth |
| **מוצא** | origin/find | origin/find | origin | origin | origin/exit | origin/outcome | origin | origin/outlet |
| **אח** | brother/fireplace | brother/fireplace | brother | brother | brother/fireplace | brother/fireplace | brother | brother/fireplace |
| **צדק** | justice/Jupiter | justice/Jupiter | justice | justice | justice/Jupiter | justice/Jupiter | justice | justice/Jupiter |
| **אוגר** | hamster/hoarder | hamster/hoarder | hamster | hamster | hamster/hoarder | hamster/hoarder | hamster | hamster |
| **זריקה** | throw/injection | throw/injection | throw | throw | throw/injection | throw/injection | throw | throw/injection |
| **מקור** | source/beak | source/beak | source | source | source/beak | source/beak | source | source/beak |
| **גר** | lives/stranger | resides/stranger | lives | lives | lives/dweller | lives/stranger | lives | lives (male singular) |
| **מקל** | stick/easy | stick/cane | stick | stick | stick | stick | stick | stick/cane |
| **מטען** | cargo/charge | cargo/charge | cargo | cargo | cargo/charge | cargo/charge | cargo | cargo/charge |
| **שרת** | server | server/minister | minister | minister | minister/server | minister/server | server | server/minister |
| **ערב** | evening/pleasant/guarantor | evening/pleasant/guarantor | evening | evening | evening/pleasant/guarantor | evening/guarantor | evening | evening/pleasant |

## פה: mouth → here, clue field moves with it

Gloss by round: {'3': 'mouth', '4': 'mouth', '5': 'mouth', '6': 'here', '7': 'mouth'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 19 --method translate \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, translate_pipeline) vs openai/gpt-4o-mini (guesser) · board dual_100 seed 19 trial 0 · count free · loss (assassin), 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - בוקר | - מלון | O שר | - כסף | - שפה |
| T קלע | O שדה | X אב | - בול | - קרן |
| T פה | O רב | T מלח | T מגדל | O קצב |
| T אחר | O אוגר | - מדבר | O ערב | T אולם |
| T נחש | O זריקה | T מאדים | O חגים | T נהג |

YOUR WORDS (9): קלע, פה, מלח, מגדל, אחר, אולם, נחש, מאדים, נהג
OPPONENT (8): שר, שדה, רב, קצב, אוגר, ערב, זריקה, חגים
CIVILIAN (7): בוקר, מלון, כסף, שפה, בול, קרן, מדבר
ASSASSIN (1): אב

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | חלל (space) | 3 | נחש, מאדים, מגדל  /  archer, tower, snake | מאדים [T], מדבר [-] | hit_civilian |
| 2 | נשק (weapon) | 2 | קלע, מלח  /  sling, salt | מלח [T], קלע [T], נחש [T] | all_correct |
| 3 | עוד (extra) | 5 | פה, מגדל, אחר, אולם, נהג  /  mouth, tower, other, hall, driver | חגים [O] | hit_opponent |
| 4 | לדבר (speak) | 2 | פה, מגדל  /  mouth, tower | שפה [-] | hit_civilian |
| 5 | צליל (sound) | 3 | פה, מגדל, נהג  /  mouth, tower, driver | קצב [O] | hit_opponent |
| 6 | מקום (place) | 3 | פה, מגדל, אחר  /  here, tower, other | מלון [-] | hit_civilian |
| 7 | דיבור (speech) | 3 | פה, מגדל, אחר  /  פה, מגדל, אחר | פה [T], שר [O] | hit_opponent |
| 8 | בניין (building) | 4 | מגדל, אחר, אולם, נהג  /  tower, other, hall, driver | מגדל [T], אולם [T], אב [X] | hit_assassin |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 |
|---|---|---|---|---|---|---|---|---|
| **קלע** | archer | sling | slingshot | slingshot | slingshot | shooter | slingshot | shooter |
| **פה** | mouth | mouth | mouth | mouth | mouth | here | mouth | mouth |
| **מלח** | salt | salt | salt | salt | salt | salt | salt | sailor |
| **מאדים** | Mars | Mars | Mars | Mars | mars | Mars | Mars | Mars |
| **קצב** | butcher | butcher | butcher | butcher | butcher | rhythm | rhythm | rhythm |
| **אוגר** | hamster | hamster | hamster | hamster | hamster | gerbil | gerbil | gerbil |
| **קרן** | horn | horn | horn | fund | horn | horn | horn | horn |

## אלה: goddess → these → those

Gloss by round: {'5': 'goddess', '6': 'these', '7': 'these', '8': 'those'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 19 --method translate \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, translate_pipeline) vs openai/gpt-4o-mini (guesser) · board natural seed 19 trial 0 · count free · win, 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - נס | O קיר | - לוחם | T אחות | T בייגלה |
| T אחוז | - פיראט | T דג | O חוסר | - חוף |
| T אפריקה | T אשף | O אופק | O סיכה | T לבוש |
| O כוס | - יורה | O שורש | X מאושר | T אלה |
| T ארץ | - חצב | - רכב | O טייס | O חווה |

YOUR WORDS (9): אחות, בייגלה, אחוז, דג, אפריקה, אשף, לבוש, אלה, ארץ
OPPONENT (8): קיר, חוסר, אופק, סיכה, כוס, שורש, טייס, חווה
CIVILIAN (7): נס, לוחם, פיראט, חוף, יורה, חצב, רכב
ASSASSIN (1): מאושר

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | יבשת (continent) | 3 | אחות, דג, אפריקה  /  sister, fish, africa | אפריקה [T], ארץ [T], חוף [-] | hit_civilian |
| 2 | קסם (magic) | 3 | אשף, דג, אחות  /  sister, fish, wizard | נס [-] | hit_civilian |
| 3 | משפחה (family) | 3 | אחות, אשף, לבוש  /  sister, bagel, percent, fish, wizard, clothing, these | אחות [T], אחוז [T], חווה [O] | hit_opponent |
| 4 | אוכל (food) | 3 | בייגלה, דג, אשף  /  bagel, fish, wizard | דג [T], בייגלה [T], כוס [O] | hit_opponent |
| 5 | קסם (magic) | 3 | אשף, לבוש, אלה  /  wizard, clothing, goddess | אשף [T], טייס [O] | hit_opponent |
| 6 | ביגוד (apparel) | 2 | לבוש, אלה  /  clothing, these | לבוש [T], סיכה [O] | hit_opponent |
| 7 | קבוצה (Group) | 1 | אלה  /  These, Sister, Fish, Warrior, Land, Beach, Miracle, Wizard, Pirate | לוחם [-] | hit_civilian |
| 8 | עצים (trees) | 1 | אלה  /  those | אלה [T] | all_correct |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 |
|---|---|---|---|---|---|---|---|---|
| **אלה** | goddess | these | these | these | goddess | these | These | those |
| **בייגלה** | pretzel | bagel | bagel | bagel | pretzel | pretzel | Bagel |  |
| **דג** | fish | fish | fish | fish | fish | fish | Fish |  |
| **אשף** | wizard | wizard | wizard | wizard | wizard | wizard | Wizard |  |
| **לבוש** | clothing | clothing | clothing | clothing | clothing | clothing | Clothing |  |
| **קיר** | wall | wall | wall | wall | wall | wall | Wall |  |
| **חוסר** | lack | lack | lack | lack | lack | lack | Lack |  |
| **אופק** | horizon | horizon | horizon | horizon | horizon | horizon | Horizon |  |
| **סיכה** | pin | pin | pin | pin | pin | pin | Pin |  |
| **כוס** | cup | cup | cup | cup | cup | cup | Cup |  |
| **שורש** | root | root | root | root | root | root | Root |  |
| **טייס** | pilot | pilot | pilot | pilot | pilot | pilot | Pilot |  |
| **חווה** | farm | farm | farm | farm | farm | farm | Farm |  |
| **לוחם** | fighter | warrior | fighter | warrior | fighter | warrior | Warrior |  |
| **פיראט** | pirate | pirate | pirate | pirate | pirate | pirate | Pirate |  |
| **חצב** | bulb | bulb | bulb | bulb | digger | bulldozer | Digger |  |
| **רכב** | vehicle | vehicle | vehicle | vehicle | vehicle | vehicle | Vehicle |  |
| **מאושר** | happy | happy | happy | happy | happy | happy | Happy |  |
| **אחות** | sister | sister | sister | sister |  | sister | Sister |  |
| **אחוז** | percent | percentage | percent | percent |  | percent | Percentage |  |
| **נס** | miracle | miracle | miracle | miracle |  | miracle | Miracle |  |
| **אפריקה** | africa |  | Africa | Africa |  | Africa | Africa |  |
| **ארץ** | land |  | land | country |  | land | Land |  |
| **חוף** | beach |  | beach | beach |  | beach | Beach |  |

## מטה: staff → staff/bed → headquarters

Gloss by round: {'3': 'staff', '4': 'staff/bed', '6': 'staff', '7': 'headquarters'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 6 --method translate \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, translate_pipeline) vs google/gemini-2.5-flash (guesser) · board dual_100 seed 6 trial 0 · count free · win, 7 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T כסף | O מנוע | - חפץ | O מצרים | - שיח |
| - נעל | T קרן | T סרט | T מלח | X חגים |
| O אולם | T מטען | T מטה | O דלק | - מאושר |
| T עצם | T חול | O קצב | - קש | O חלק |
| T סוף | O ספר | - אחר | - אלה | O מטר |

YOUR WORDS (9): כסף, קרן, סרט, מלח, מטען, מטה, עצם, חול, סוף
OPPONENT (8): מנוע, מצרים, אולם, דלק, קצב, חלק, ספר, מטר
CIVILIAN (7): חפץ, שיח, נעל, מאושר, קש, אחר, אלה
ASSASSIN (1): חגים

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | בנק (bank) | 3 | סרט, כסף, סוף  /  film, money, end | כסף [T], קרן [T], מטען [T] | stopped_early |
| 2 | גמר (finish) | 2 | סרט, סוף  /  film, end | סוף [T], חלק [O] | hit_opponent |
| 3 | מקל (stick) | 2 | סרט, מטה  /  film, staff | קש [-] | hit_civilian |
| 4 | רצועה (strip) | 2 | סרט, מטה  /  film/ribbon, staff/bed | סרט [T], מצרים [O] | hit_opponent |
| 5 | חוף (beach) | 2 | מלח, חול  /  salt, sand | חול [T], מלח [T] | stopped_early |
| 6 | גוף (body) | 2 | מטה, עצם  /  staff, bone | עצם [T], חפץ [-] | hit_civilian |
| 7 | משרד (office) | 1 | מטה  /  headquarters | מטה [T] | all_correct |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 |
|---|---|---|---|---|---|---|---|
| **קרן** | horn/fund/ray | horn | horn/fund | horn/fund | horn | horn | horn/fund/ray |
| **סרט** | film/ribbon | film | film | film/ribbon | ribbon | ribbon | ribbon/movie |
| **מטען** | cargo/charge | cargo | cargo | cargo/charge | cargo | cargo | cargo/charge |
| **מטה** | rod/staff/bed | staff | staff | staff/bed | staff | staff | headquarters |
| **עצם** | bone/object | bone | bone | bone/object | bone | bone | bone/object |
| **קצב** | rhythm/butcher | rhythm | rhythm | rhythm/butcher | rhythm | rhythm | rhythm |
| **חלק** | part/smooth | part | part | part/smooth | part | part | part |
| **ספר** | book/barber | book | book | book/barber | book | book | book |
| **מטר** | meter/rain | meter | meter | meter/rain | meter | meter | meter |
| **חפץ** | object/desire | object | object | object | object | object | object/desire |
| **שיח** | bush/conversation | bush | bush | bush/conversation | bush | bush | bush |
| **מאושר** | happy/approved | happy | happy | happy/approved | happy | happy | happy |
| **אלה** | goddess/these/club | these | these | these/goddess | these | these | these |

## תור: queue ↔ turn over seven rounds, clue סדר reused on both senses

Gloss by round: {'1': 'queue', '2': 'queue', '3': 'queue', '5': 'turn', '6': 'queue', '7': 'turn', '8': 'turn'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 22 --method translate \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, translate_pipeline) vs openai/gpt-4o-mini (guesser) · board dual_0 seed 22 trial 0 · count free · loss (assassin), 9 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O אופק | T טבע | O שמן | T מיון | - ים |
| O פעמון | T תור | O מסלול | - מסך | T חיבור |
| X חופה | O רופא | O יום | T ראש | T אפריקה |
| O תולעת | T אשפה | - דרך | T פיראט | - לוחם |
| - חתול | - חריף | O סילון | T כפתור | - זמן |

YOUR WORDS (9): טבע, מיון, תור, חיבור, ראש, אפריקה, אשפה, פיראט, כפתור
OPPONENT (8): אופק, שמן, פעמון, מסלול, רופא, יום, תולעת, סילון
CIVILIAN (7): ים, מסך, דרך, לוחם, חתול, חריף, זמן
ASSASSIN (1): חופה

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | סדר (order) | 3 | טבע, תור, כפתור  /  nature, queue, button | מיון [T], דרך [-] | hit_civilian |
| 2 | סדר (order) | 3 | תור, חיבור, ראש  /  nature, queue, connection | מסלול [O] | hit_opponent |
| 3 | יבשת (continent) | 5 | אפריקה, טבע, תור, חיבור, ראש  /  nature, queue, connection, head, Africa | אפריקה [T], ים [-] | hit_civilian |
| 4 | סביבה (environment) | 2 | טבע, חיבור  /  nature, connection | טבע [T], אופק [O] | hit_opponent |
| 5 | קישור (link) | 3 | תור, חיבור, ראש  /  turn, connection, head | חיבור [T], יום [O] | hit_opponent |
| 6 | סדר (order) | 2 | תור, ראש  /  queue, head | זמן [-] | hit_civilian |
| 7 | גלגל (wheel) | 3 | תור, ראש, אשפה  /  turn, head, trash | פעמון [O] | hit_opponent |
| 8 | שליטה (control) | 3 | תור, ראש, כפתור  /  turn, head, button | ראש [T], תור [T], רופא [O] | hit_opponent |
| 9 | אוקיאנוס (ocean) | 3 | אשפה, פיראט, כפתור  /  trash, pirate, button | פיראט [T], חופה [X] | hit_assassin |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 | r9 |
|---|---|---|---|---|---|---|---|---|---|
| **תור** | queue | queue | queue | line | turn | queue | turn | turn | queue |
| **אפריקה** | Africa | Africa | Africa | Africa | Africa | Africa | Africa | africa | Africa |
| **אשפה** | garbage | garbage | garbage | trash | trash | garbage | trash | trash | trash |
| **לוחם** | warrior | fighter | fighter | fighter | fighter | warrior | fighter | fighter | warrior |
| **מיון** | classification |  | sorting | sorting | classification | sorting | sorting | sorting | sorting |
| **מסלול** | route | path | route | route |  | route | route | route | track |

## אוגר: hamster → gerbil

Gloss by round: {'1': 'hamster', '2': 'hamster', '3': 'gerbil'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 12 --method translate \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, translate_pipeline) vs openai/gpt-4o-mini (guesser) · board dual_100 seed 12 trial 0 · count free · loss (assassin), 4 rounds · 20260823T191234131145Z

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
| 1 | מכניקה (mechanics) | 3 | מנוע, אוגר, בסיס  /  engine, hamster, base | מנוע [T], קצב [T], מאבק [-] | hit_civilian |
| 2 | מלאכה (craft) | 5 | אוגר, בסיס, מעמד, מקל, חצב  /  hamster, hall, base, stand, stick, chisel | אמן [T], מעמד [T], בר [-] | hit_civilian |
| 3 | חיה (pet) | 5 | אוגר, אולם, בסיס, מקל, חצב  /  gerbil, hall, base, stick, bulb | אוגר [T], גזר [O] | hit_opponent |
| 4 | תמיכה (support) | 3 | בסיס, מקל, חצב  /  hall, base, stick, bulb | בסיס [T], חום [X] | hit_assassin |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 |
|---|---|---|---|---|
| **אוגר** | hamster | hamster | gerbil | mole |
| **חצב** | chisel | chisel | bulb | bulb |
| **מעמד** | status | stand |  | status |

## כבד: heart → liver → heavy → kidney

Gloss by round: {'4': 'liver', '10': 'heart', '17': 'liver', '19': 'kidney', '20': 'heavy'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 15 --method translate \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc free
```

### qwen/qwen3.5-9b (codemaster, translate_pipeline) vs qwen/qwen3.5-9b (guesser) · board dual_100 seed 15 trial 0 · count free · win, 21 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - מנוע | O מפה | T בול | - דוד | O מאבק |
| O חצב | - אב | - צדק | O נס | T ספר |
| - מעבר | T אלה | T משפט | X מעמד | T רב |
| T כבד | O קניון | O ירח | O גזר | T מרוצים |
| - קלע | - פנים | T רכב | T אוכל | O עמוד |

YOUR WORDS (9): בול, ספר, אלה, משפט, רב, כבד, מרוצים, רכב, אוכל
OPPONENT (8): מפה, מאבק, חצב, נס, קניון, ירח, גזר, עמוד
CIVILIAN (7): מנוע, דוד, אב, צדק, מעבר, קלע, פנים
ASSASSIN (1): מעמד

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | קוקר (קוקר) | 5 | בול, ספר, אלה, משפט, רב  /  סט, שיער, גנה, כלי, חצר | מנוע [-] | hit_civilian |
| 2 | דואר (post) | 3 | בול, ספר, אוכל  /  stamps, book, food | בול [T] | stopped_early |
| 3 | ב (sat) | 2 | מרוצים, רכב  /  book, tree, liver/organs, rabbi, car | אב [-] | hit_civilian |
| 4 | גוף (body) | 5 | ספר, משפט, רב, כבד, רכב  /  book, sentence, rabbi, liver, car | גזר [O] | hit_opponent |
| 5 | נסיעה (ride) | 3 | מרוצים, רכב, ספר  /  spider, car, bike | נס [O] | hit_opponent |
| 6 | דלק (fuel) | 2 | רכב, אוכל  /  רכב, אוכל | מאבק [O] | hit_opponent |
| 7 | רעב (hungry) | 3 | אוכל, מרוצים, רכב  /  food, satisfied, vehicle | אוכל [T] | stopped_early |
| 8 | חיבור (connection) | 4 | ספר, אלה, מרוצים, רכב  /  book, god, furious, car | משפט [T], דוד [-] | hit_civilian |
| 9 | דתי (religious) | 1 | רב  /  book, rabbi, vehicle | רב [T] | stopped_early |
| 10 | אהבה (Love) | 2 | אלה, כבד  /  God, Heart | פנים [-] | hit_civilian |
| 11 | חדר (travel) | 3 | ספר, מרוצים, רכב  /  book, which, gratified, vehicle | ספר [T] | stopped_early |
| 12 | מהיר (fast) | 2 | מרוצים, רכב  /  מרוצים, רכב | מרוצים [T], חצב [O] | hit_opponent |
| 13 | לב (heart) | 2 | כבד, רכב  /  כבד, רכב | ירח [O] | hit_opponent |
| 14 | הם (they) | 1 | אלה  /  they | צדק [-] | hit_civilian |
| 15 | נוזל (Liquid) | 3 | אלה, כבד, רכב  /  אלה, כבד, רכב | מפה [O] | hit_opponent |
| 16 | רכיבה (ride) | 1 | רכב  /  רכב | רכב [T] | stopped_early |
| 17 | כולל (include) | 2 | כבד, אלה  /  כבד, אלה | מעבר [-] | hit_civilian |
| 18 | חיל (Troop) | 1 | אלה  /  Mine | קלע [-] | hit_civilian |
| 19 | עונה (season) | 2 | אלה, כבד  /  אלה, כבד | עמוד [O] | hit_opponent |
| 20 | צפוף (dense) | 1 | כבד  /  כבד | כבד [T] | stopped_early |
| 21 | אוי (them) | 1 | אלה  /  אלה | אלה [T] | all_correct |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 | r9 | r10 | r11 | r12 | r13 | r14 | r15 | r16 | r17 | r18 | r19 | r20 | r21 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **כבד** | liver | kidney | liver/organs | liver | liver | liver | liver | heavy | liver | Heart | kidney | heavy |  | liver |  | heavy | liver |  | kidney | heavy |  |
| **רכב** | vehicle | encounter | car | car | vehicle | car | vehicle | car | vehicle | Car | vehicle | car |  | vehicle |  | vehicle |  |  |  |  |  |
| **אלה** | these |  | tree | arm | these | plague | god |  | those | God | which |  |  | they |  |  | those |  | allies |  | them |
| **מרוצים** | satisfied | motorized | sat | enemies | cars | speed | satisfied | furious | tire | Proud | gratified | fast |  | satisfied |  |  |  |  |  |  |  |
| **ספר** | book | book | book | book | book | animal | book | book | book | Book | book |  |  | book |  |  |  |  |  |  |  |
| **משפט** | sentence | sentence | sentence | sentence | sentence | first | law | sentence | law |  | sentence |  |  | law |  |  |  |  |  |  |  |
| **רב** | rabbi | rabbi | rabbi | rabbi | rabbi | senior | rabbi | rabbi | rabbi |  | rabbi |  |  | rabbi |  |  |  |  |  |  |  |
| **מאבק** | struggle |  |  | fight | struggle |  |  | struggle | struggle |  | struggle |  |  | struggle |  |  |  |  |  |  |  |
| **חצב** | reeds |  |  | louse | acnod |  |  | reeds | seashell |  | start |  |  | dye |  |  |  |  |  |  |  |
| **עמוד** | column |  |  | column | column |  |  | column | pillar |  | column |  |  | column |  |  |  |  |  |  |  |
| **דוד** | David |  |  | David | David |  |  | dawid | David |  | David |  |  | David |  |  |  |  |  |  |  |
| **מעבר** | pass |  |  | transition | passage |  |  | exit | tunnel |  | Exit |  |  | crossing |  |  |  |  |  |  |  |
| **קלע** | archer |  |  | archer | golfer |  |  | archer | archer |  | archer |  |  | gate |  |  |  |  |  |  |  |
| **פנים** | faces |  |  | face | face |  |  | faces | face |  | face |  |  | face |  |  |  |  |  |  |  |
| **מעמד** | status |  |  | status | status |  |  | status | speech |  | status |  |  | status |  |  |  |  |  |  |  |
| **בול** | stamp | stamps |  |  |  |  |  | stamping | stamp |  | stamp |  |  | stamp |  |  |  |  |  |  |  |
| **לה** |  | goddess |  |  |  |  |  |  |  |  |  | they |  |  |  |  |  |  |  | to |  |

## זריקה: shot → throw

Gloss by round: {'3': 'shot', '6': 'throw', '7': 'throw', '9': 'throw'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 5 --method translate \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, translate_pipeline) vs google/gemini-2.5-flash (guesser) · board natural seed 5 trial 0 · count free · win, 10 rounds · 20260823T191234131145Z

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
| 1 | הופעה (performance) | 2 | מופע, תיאטרון  /  show, theater | מופע [T], תיאטרון [T] | stopped_early |
| 2 | זר (foreign) | 2 | חייזר, אירופה  /  alien, Europe | פרח [O] | hit_opponent |
| 3 | זר (foreign) | 3 | חייזר, זריקה, אירופה  /  alien, shot, europe | חייזר [T], קפה [-] | hit_civilian |
| 4 | יבשת (Continent) | 2 | אירופה, חוף  /  Europe, beach | אירופה [T], חוף [T] | stopped_early |
| 5 | כוכב (star) | 1 | מזל  /  luck, constellation | קרן [O] | hit_opponent |
| 6 | פעולה (action) | 2 | זריקה, חצב  /  throw, carved | קוד [O] | hit_opponent |
| 7 | פעולה (action) | 2 | זריקה, חצב  /  throw, carve | מסע [-] | hit_civilian |
| 8 | גורל (fortune) | 2 | מחילה, מזל  /  forgiveness, luck | מזל [T], חג [-] | hit_civilian |
| 9 | שיגור (launch) | 2 | זריקה, חצב  /  throw, squill | זריקה [T], קלע [-] | hit_civilian |
| 10 | תת-קרקעי (Underground) | 2 | מחילה, חצב  /  burrow, squill | מחילה [T], חצב [T] | all_correct |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 | r9 | r10 |
|---|---|---|---|---|---|---|---|---|---|---|
| **זריקה** | shot | shot | shot | throw | throw/shot | throw | throw | throw | throw | shot |
| **מחילה** | burrow | burrow | burrow | burrow | forgiveness/burrow | forgiveness | forgiveness | forgiveness | forgiveness | burrow |
| **חצב** | squill | squill | squill | squill | carve/squill | carved | carve | carve | squill | squill |
| **כף** | spoon | spoon | spoon | spoon | spoon/palm/shore | spoon | spoon | spoon | spoon | spoon |
| **אלה** | goddess | goddess | goddess | goddess | goddess/club | goddess | goddess | goddess | goddess | club |
| **צופים** | scouts | scouts | scouts | scouts | scouts/viewers | scouts | scouts | scouts | scouts | scouts |
| **קלע** | slingshot | slingshot | slingshot | slingshot | slingshot/shooter | slingshot | slingshot | shooter | slingshot | slingshot |
| **אירופה** | Europe | Europe | europe | Europe | europe | europe | europe | europe |  | europe |
| **מזל** | luck | luck | luck | luck | luck/constellation | luck | luck | luck |  | luck |
| **קרן** | horn | horn | horn | horn | horn/ray/fund | horn | horn | horn |  | horn |
| **מסע** | journey | journey | journey | journey | journey/trip | journey | journey | journey |  | journey |

## בר: wild → son → bar

Gloss by round: {'4': 'wild/son/bar', '5': 'wild', '6': 'son', '8': 'bar/wild/son'}

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 16 --method translate \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, translate_pipeline) vs google/gemini-2.5-flash (guesser) · board natural seed 16 trial 0 · count free · win, 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - לבנה | O שנהב | T חשבון | X אשף | O אורגני |
| - טבעת | - פה | T שלג | O סירה | T פרח |
| O מלכה | T רולטה | T מחשב | T בר | T סילון |
| T צופים | - רשת | O מקל | - קרן | T כינור |
| - אור | O פחד | O שוטר | - מצרים | O אנטארקטיקה |

YOUR WORDS (9): חשבון, שלג, פרח, רולטה, מחשב, בר, סילון, צופים, כינור
OPPONENT (8): שנהב, אורגני, סירה, מלכה, מקל, פחד, שוטר, אנטארקטיקה
CIVILIAN (7): לבנה, טבעת, פה, רשת, קרן, אור, מצרים
ASSASSIN (1): אשף

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | מכונה (machine) | 2 | סילון, מחשב  /  jet, computer | מחשב [T], סילון [T] | stopped_early |
| 2 | משחק (game) | 2 | חשבון, רולטה  /  bill, roulette | רולטה [T], כינור [T] | stopped_early |
| 3 | קר (cold) | 1 | שלג  /  snow, antarctica | שלג [T], אנטארקטיקה [O] | hit_opponent |
| 4 | טבע (nature) | 2 | פרח, בר  /  flower, wild | אורגני [O] | hit_opponent |
| 5 | טבע (nature) | 2 | פרח, בר  /  flower, wild | פרח [T], קרן [-] | hit_civilian |
| 6 | נוער (youth) | 3 | חשבון, בר, צופים  /  account, son, scouts | צופים [T], מקל [O] | hit_opponent |
| 7 | מתמטיקה (math) | 1 | חשבון  /  account | חשבון [T] | stopped_early |
| 8 | פרא (wild) | 1 | בר  /  bar/wild/son | בר [T] | all_correct |

Board words glossed more than one way across rounds:

| word | r1 | r2 | r3 | r4 | r5 | r6 | r7 | r8 |
|---|---|---|---|---|---|---|---|---|
| **חשבון** | account/bill/arithmetic | bill | account | bill/account/math | bill | account | account | bill/account/arithmetic |
| **בר** | bar/wild | wild | wild | wild/son/bar | wild | son | bar | bar/wild/son |
| **צופים** | scouts/spectators | scouts | scouts | scouts | scouts | scouts | scouts | scouts |
| **לבנה** | brick/moon(white) | brick | brick | brick/moon (colloquial) | brick | brick | brick | brick/white |
| **פה** | mouth | mouth | mouth | mouth/here | mouth | mouth | mouth | mouth/here |
| **רשת** | net/web | net | net | net | net | net | net | net |
| **מצרים** | egypt/straits | egypt | egypt | Egypt | Egypt | Egypt | Egypt | Egypt |
| **אנטארקטיקה** | antarctica | antarctica | antarctica | Antarctica | Antarctica |  | Antarctica | Antarctica |
| **קרן** | horn/ray/fund | horn | horn | horn/ray/fund | horn |  | horn | horn/fund/ray |


---

# Root-echo clues

## clue מזלטוב echoes target מזל

Round 7. Clue **מזלטוב** is a surface variant of **מזל**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 1 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 1 trial 0 · count free · win, 12 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T אשפה | T ראש | T שולחן | - סדר | X אסר |
| T דבש | O סירה | - מכשפה | - סל | O מסך |
| T כיפה | T מזלג | - מעיין | - אפריקה | O דבק |
| - אולימפוס | O טייס | T עוקץ | O פצצה | - בנק |
| T לוחם | O קרצייה | T מזל | O קברן | O טעם |

YOUR WORDS (9): אשפה, ראש, שולחן, דבש, כיפה, מזלג, עוקץ, לוחם, מזל
OPPONENT (8): סירה, מסך, דבק, טייס, פצצה, קרצייה, קברן, טעם
CIVILIAN (7): סדר, מכשפה, סל, מעיין, אפריקה, אולימפוס, בנק
ASSASSIN (1): אסר

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | כוח | 2 | ראש, לוחם | כיפה [T], ראש [T], מכשפה [-] | hit_civilian |
| 2 | מתכת | 2 | אשפה, מזלג | מסך [O] | hit_opponent |
| 3 | מתכת | 2 | מזלג, אשפה | מזלג [T], דבק [O] | hit_opponent |
| 4 | דבורה | 1 | דבש | דבש [T], טעם [O] | hit_opponent |
| 5 | נשק | 2 | לוחם, עוקץ | פצצה [O] | hit_opponent |
| 6 | נשק | 2 | לוחם, עוקץ | לוחם [T], טייס [O] | hit_opponent |
| 7 | מזלטוב | 1 | מזל | מזל [T], אשפה [T] | all_correct |
| 8 | רגל | 2 | שולחן, עוקץ | סל [-] | hit_civilian |
| 9 | רגל | 2 | שולחן, עוקץ | סירה [O] | hit_opponent |
| 10 | רגל | 2 | שולחן, עוקץ | קרצייה [O] | hit_opponent |
| 11 | ריהוט | 1 | שולחן | שולחן [T] | stopped_early |
| 12 | חד | 1 | עוקץ | עוקץ [T] | all_correct |

## clue קרן echoes target חד-קרן

Round 4. Clue **קרן** is a surface variant of **חד-קרן**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 2 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 2 trial 0 · count free · loss (assassin), 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T לשון | O מחילה | - רוח-רפאים | - עכבר | T חד-קרן |
| - חריף | T מחשב | - פרח | T שן | - מיליונר |
| O גורד-שחקים | T אצטדיון | O קזינו | T כף | O חופה |
| O מעגל | X תל-אביב | T בייגלה | T חיים | O חוק |
| T הרמון | - כפתור | O תפר | O נמל | - לוויין |

YOUR WORDS (9): לשון, חד-קרן, מחשב, שן, אצטדיון, כף, בייגלה, חיים, הרמון
OPPONENT (8): מחילה, גורד-שחקים, קזינו, חופה, מעגל, חוק, תפר, נמל
CIVILIAN (7): רוח-רפאים, עכבר, חריף, פרח, מיליונר, כפתור, לוויין
ASSASSIN (1): תל-אביב

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | משחק | 2 | חיים, מחשב | מחשב [T], מיליונר [-] | hit_civilian |
| 2 | מוזיקה | 1 | הרמון | הרמון [T], חיים [T] | all_correct |
| 3 | משחק | 2 | אצטדיון, לשון | מחילה [O] | hit_opponent |
| 4 | קרן | 1 | חד-קרן | חד-קרן [T], כף [T] | all_correct |
| 5 | משחק | 1 | אצטדיון | מעגל [O] | hit_opponent |
| 6 | משחק | 1 | אצטדיון | אצטדיון [T], גורד-שחקים [O] | hit_opponent |
| 7 | פה | 1 | לשון | לשון [T], שן [T] | all_correct |
| 8 | מוזיקה | 1 | בייגלה | תל-אביב [X] | hit_assassin |

## clue אבירות echoes target אביר

Round 3. Clue **אבירות** is a surface variant of **אביר**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 4 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 4 trial 0 · count free · loss (assassin), 11 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T שבת | - גל | O חיות | O אש | T אביר |
| T צרפת | T זוהר | T שבתאי | X ציפורן | - חופה |
| - חתיכה | T כוס | O פרי | T כיפה | O כביש |
| O חוליה | O אפיקומן | - סוכה | - גמד | T טיל |
| T ציור | - מורה | O זהב | O דוב | - שוט |

YOUR WORDS (9): שבת, אביר, צרפת, זוהר, שבתאי, כוס, כיפה, טיל, ציור
OPPONENT (8): חיות, אש, פרי, כביש, חוליה, אפיקומן, זהב, דוב
CIVILIAN (7): גל, חופה, חתיכה, סוכה, גמד, מורה, שוט
ASSASSIN (1): ציפורן

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | אמנות | 2 | ציור, כיפה | ציור [T], כיפה [T] | stopped_early |
| 2 | אור | 2 | זוהר, שבת | זוהר [T], אש [O] | hit_opponent |
| 3 | אבירות | 2 | אביר, צרפת | אביר [T], אפיקומן [O] | hit_opponent |
| 4 | יין | 1 | כוס | כוס [T], גל [-] | hit_civilian |
| 5 | אירופה | 1 | צרפת | צרפת [T], חופה [-] | hit_civilian |
| 6 | ירח | 1 | שבת | זהב [O] | hit_opponent |
| 7 | לילה | 1 | שבת | שבת [T], חוליה [O] | hit_opponent |
| 8 | אשפה | 1 | טיל | חתיכה [-] | hit_civilian |
| 9 | אשפה | 1 | טיל | פרי [O] | hit_opponent |
| 10 | אשפה | 1 | טיל | חיות [O] | hit_opponent |
| 11 | אשפה | 1 | טיל | ציפורן [X] | hit_assassin |

## clue מרכזי echoes target מרכז

Round 7. Clue **מרכזי** is a surface variant of **מרכז**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 9 --method strong \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, strong_hebrew) vs openai/gpt-4o-mini (guesser) · board dual_0 seed 9 trial 0 · count free · loss (assassin), 7 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O ראש | - מזלג | O בקבוק | T גמד | T עיר |
| O מסלול | O דג | T קור | - קברן | T קנגורו |
| - קרצייה | O עץ | - שולחן | - אנגליה | T טעם |
| O ברמודה | T מקדש | - אגודל | O הלך | T תשובה |
| X תנועה | T מרכז | O בית-ספר | T אולימפוס | - כתר |

YOUR WORDS (9): גמד, עיר, קור, קנגורו, טעם, מקדש, תשובה, מרכז, אולימפוס
OPPONENT (8): ראש, בקבוק, מסלול, דג, עץ, ברמודה, הלך, בית-ספר
CIVILIAN (7): מזלג, קברן, קרצייה, שולחן, אנגליה, אגודל, כתר
ASSASSIN (1): תנועה

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | חום | 3 | קור, טעם, אולימפוס | דג [O] | hit_opponent |
| 2 | ישראלי | 2 | עיר, מרכז | עיר [T], אנגליה [-] | hit_civilian |
| 3 | טבע | 2 | גמד, קנגורו | עץ [O] | hit_opponent |
| 4 | אלים | 3 | קנגורו, אולימפוס, מקדש | אולימפוס [T], מקדש [T], כתר [-] | hit_civilian |
| 5 | חידת | 3 | טעם, תשובה, מרכז | תשובה [T], טעם [T], שולחן [-] | hit_civilian |
| 6 | קטן | 1 | גמד | גמד [T], אגודל [-] | hit_civilian |
| 7 | מרכזי | 2 | קור, מרכז | מרכז [T], תנועה [X] | hit_assassin |

## clue משחקיה echoes target משחק

Round 5. Clue **משחקיה** is a surface variant of **משחק**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 11 --method strong \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, strong_hebrew) vs google/gemini-2.5-flash (guesser) · board dual_0 seed 11 trial 0 · count free · win, 11 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O חתול | T זמן | T שטר | X עכביש | - ענק |
| T כביש | - שנהב | - כיסא | T סוכן | O טייס |
| - קול | O אש | T ברווז | - קיץ | - חשבון |
| O בית-חולים | T דינוזאור | O מרגל | O מועדון | O כדור |
| - נסיכה | T קטשופ | T בוחן | O ים | T משחק |

YOUR WORDS (9): זמן, שטר, כביש, סוכן, ברווז, דינוזאור, קטשופ, בוחן, משחק
OPPONENT (8): חתול, טייס, אש, בית-חולים, מרגל, מועדון, כדור, ים
CIVILIAN (7): ענק, שנהב, כיסא, קול, קיץ, חשבון, נסיכה
ASSASSIN (1): עכביש

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | מאובן | 1 | דינוזאור | דינוזאור [T] | stopped_early |
| 2 | מהירות | 2 | זמן, כביש | זמן [T], כביש [T] | stopped_early |
| 3 | סרט | 2 | סוכן, משחק | סוכן [T], מרגל [O] | hit_opponent |
| 4 | ביקורת | 2 | בוחן, משחק | בוחן [T], חשבון [-] | hit_civilian |
| 5 | משחקיה | 2 | משחק, ברווז | משחק [T], כדור [O] | hit_opponent |
| 6 | כסף | 1 | שטר | שטר [T] | stopped_early |
| 7 | מאכל | 2 | ברווז, קטשופ | קטשופ [T], מועדון [O] | hit_opponent |
| 8 | חי | 1 | ברווז | חתול [O] | hit_opponent |
| 9 | מים | 1 | ברווז | ים [O] | hit_opponent |
| 10 | מים | 1 | ברווז | קיץ [-] | hit_civilian |
| 11 | מים | 1 | ברווז | ברווז [T] | all_correct |

## clue משחקים echoes target משחק

Round 1. Clue **משחקים** is a surface variant of **משחק**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 11 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 11 trial 0 · count free · win, 9 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O חתול | T זמן | T שטר | X עכביש | - ענק |
| T כביש | - שנהב | - כיסא | T סוכן | O טייס |
| - קול | O אש | T ברווז | - קיץ | - חשבון |
| O בית-חולים | T דינוזאור | O מרגל | O מועדון | O כדור |
| - נסיכה | T קטשופ | T בוחן | O ים | T משחק |

YOUR WORDS (9): זמן, שטר, כביש, סוכן, ברווז, דינוזאור, קטשופ, בוחן, משחק
OPPONENT (8): חתול, טייס, אש, בית-חולים, מרגל, מועדון, כדור, ים
CIVILIAN (7): ענק, שנהב, כיסא, קול, קיץ, חשבון, נסיכה
ASSASSIN (1): עכביש

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | משחקים | 2 | משחק, בוחן | משחק [T], כדור [O] | hit_opponent |
| 2 | רחוב | 1 | כביש | כביש [T], זמן [T] | all_correct |
| 3 | מזון | 1 | קטשופ | קטשופ [T], ברווז [T] | all_correct |
| 4 | ריגול | 1 | סוכן | מרגל [O] | hit_opponent |
| 5 | ריגול | 1 | סוכן | סוכן [T], טייס [O] | hit_opponent |
| 6 | מבחן | 1 | בוחן | בוחן [T] | stopped_early |
| 7 | פרהיסטורי | 1 | דינוזאור | דינוזאור [T], ענק [-] | hit_civilian |
| 8 | נייר | 1 | שטר | נסיכה [-] | hit_civilian |
| 9 | נייר | 1 | שטר | שטר [T] | all_correct |

## clue תנוע echoes target תנועה

Round 3. Clue **תנוע** is a surface variant of **תנועה**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 27 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 27 trial 0 · count free · win, 10 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T צופים | O ריקוד | - קפה | - זהב | T מעיין |
| X מרגל | T תנועה | O גל | O צלחת | T עקרב |
| - ענק | O קזינו | T לימוזינה | O עכבר | T פצצה |
| T מצנח | - חיים | - רצפה | O נתיב | O סירה |
| O מורה | - גנב | T חלל | T כיסא | - לוחם |

YOUR WORDS (9): צופים, מעיין, תנועה, עקרב, לימוזינה, פצצה, מצנח, חלל, כיסא
OPPONENT (8): ריקוד, גל, צלחת, קזינו, עכבר, נתיב, סירה, מורה
CIVILIAN (7): קפה, זהב, ענק, חיים, רצפה, גנב, לוחם
ASSASSIN (1): מרגל

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | תעופה | 2 | מצנח, חלל | מצנח [T], סירה [O] | hit_opponent |
| 2 | רכב | 2 | לימוזינה, צופים | לימוזינה [T], רצפה [-] | hit_civilian |
| 3 | תנוע | 2 | תנועה, צופים | תנועה [T], ריקוד [O] | hit_opponent |
| 4 | מים | 2 | מעיין, צופים | גל [O] | hit_opponent |
| 5 | חללי | 2 | חלל, צופים | חלל [T], עכבר [O] | hit_opponent |
| 6 | מים | 1 | מעיין | מעיין [T], צופים [T] | all_correct |
| 7 | נשק | 1 | פצצה | פצצה [T], לוחם [-] | hit_civilian |
| 8 | נחש | 1 | עקרב | עקרב [T], נתיב [O] | hit_opponent |
| 9 | מושב | 1 | כיסא | מורה [O] | hit_opponent |
| 10 | מושב | 1 | כיסא | כיסא [T] | all_correct |

## clue חללי echoes target חלל

Round 5. Clue **חללי** is a surface variant of **חלל**, which `clue_on_board` does not reject.

_Same game as above; see the transcript there._

## clue נמלול echoes target נמל

Round 6. Clue **נמלול** is a surface variant of **נמל**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 29 --method strong \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, strong_hebrew) vs google/gemini-2.5-flash (guesser) · board dual_0 seed 29 trial 0 · count free · win, 9 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T מועדון | O בית-חולים | O מצח | T תיק | - כיסא |
| - קנטאור | T שלג | T אי | T מנוף | - עוקץ |
| O חמה | X כיפה | T נמל | O אתר | - פרסה |
| O תפר | - שוקולד | T אביר | - אור | O פירמידה |
| - כדור | O קשה | T נסיכה | T אורגני | O אוויר |

YOUR WORDS (9): מועדון, תיק, שלג, אי, מנוף, נמל, אביר, נסיכה, אורגני
OPPONENT (8): בית-חולים, מצח, חמה, אתר, תפר, פירמידה, קשה, אוויר
CIVILIAN (7): כיסא, קנטאור, עוקץ, פרסה, שוקולד, אור, כדור
ASSASSIN (1): כיפה

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | ארמון | 2 | אביר, נסיכה | נסיכה [T], אביר [T] | stopped_early |
| 2 | ים | 2 | אי, נמל | אי [T] | stopped_early |
| 3 | ארגון | 1 | מועדון | מועדון [T], אתר [O] | hit_opponent |
| 4 | טבע | 2 | שלג, אורגני | אורגני [T], קנטאור [-] | hit_civilian |
| 5 | ארבעה | 2 | מנוף, נמל | כיסא [-] | hit_civilian |
| 6 | נמלול | 1 | נמל | נמל [T] | stopped_early |
| 7 | לבן | 2 | שלג, תיק | שלג [T], מצח [O] | hit_opponent |
| 8 | משא | 2 | תיק, מנוף | תיק [T], קשה [O] | hit_opponent |
| 9 | הגבהה | 1 | מנוף | מנוף [T] | all_correct |

## clue קירות echoes target קיר

Round 9. Clue **קירות** is a surface variant of **קיר**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 4 --method strong \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, strong_hebrew) vs openai/gpt-4o-mini (guesser) · board natural seed 4 trial 0 · count free · win, 9 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O רגל | - מעיין | O פיראט | T חג | - מצח |
| T אקדח | T נייר | - גזר | O דשא | O שגרירות |
| O לוויתן | T סוכה | - קזינו | T אביר | - אוויר |
| O נהג | T מראה | O ראש | - מים | X גאון |
| T כתב | - רובוט | O אי | T תיק | T קיר |

YOUR WORDS (9): חג, אקדח, נייר, סוכה, אביר, מראה, כתב, תיק, קיר
OPPONENT (8): רגל, פיראט, דשא, שגרירות, לוויתן, נהג, ראש, אי
CIVILIAN (7): מעיין, מצח, גזר, קזינו, אוויר, מים, רובוט
ASSASSIN (1): גאון

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | חגיגה | 2 | חג, תיק | חג [T], סוכה [T], קזינו [-] | hit_civilian |
| 2 | שק | 2 | נייר, תיק | מים [-] | hit_civilian |
| 3 | קלף | 2 | כתב, תיק | נייר [T], גזר [-] | hit_civilian |
| 4 | מגן | 2 | אביר, אקדח | אביר [T], אקדח [T], שגרירות [O] | hit_opponent |
| 5 | ציור | 2 | כתב, קיר | אי [O] | hit_opponent |
| 6 | עַד | 2 | כתב, קיר | דשא [O] | hit_opponent |
| 7 | תמונה | 2 | מראה, כתב | מראה [T], רגל [O] | hit_opponent |
| 8 | דיו | 3 | כתב, תיק, קיר | כתב [T], תיק [T], ראש [O] | hit_opponent |
| 9 | קירות | 1 | קיר | קיר [T] | all_correct |

## clue רוח echoes target רוח-רפאים

Round 10. Clue **רוח** is a surface variant of **רוח-רפאים**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 6 --method strong \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, strong_hebrew) vs google/gemini-2.5-flash (guesser) · board natural seed 6 trial 0 · count free · win, 10 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T רוח-רפאים | O ים | T אירופה | O פה | - אלים |
| O כפפה | O ארנב | T סוכן | T זוהר | O טעם |
| T שוקולד | - קברן | T אגודל | O אורח | T אפריקה |
| O קש | - מוות | O מאדים | - גלידה | T מקור |
| T דם | X דבר | - אש | - מסחרית | - ברמודה |

YOUR WORDS (9): רוח-רפאים, אירופה, סוכן, זוהר, שוקולד, אגודל, אפריקה, מקור, דם
OPPONENT (8): ים, פה, כפפה, ארנב, טעם, אורח, קש, מאדים
CIVILIAN (7): אלים, קברן, מוות, גלידה, אש, מסחרית, ברמודה
ASSASSIN (1): דבר

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | יבשת | 2 | אירופה, אפריקה | אפריקה [T], אירופה [T] | stopped_early |
| 2 | גוף | 2 | סוכן, דם | פה [O] | hit_opponent |
| 3 | טבע | 2 | מקור, דם | ים [O] | hit_opponent |
| 4 | גוף | 3 | סוכן, דם, רוח-רפאים | דם [T], אגודל [T], כפפה [O] | hit_opponent |
| 5 | נצנץ | 1 | זוהר | זוהר [T] | stopped_early |
| 6 | סוד | 2 | רוח-רפאים, סוכן | סוכן [T], קברן [-] | hit_civilian |
| 7 | טרוף | 2 | רוח-רפאים, שוקולד | אלים [-] | hit_civilian |
| 8 | נביעה | 2 | מקור, רוח-רפאים | מקור [T], אש [-] | hit_civilian |
| 9 | מתוק | 1 | שוקולד | שוקולד [T], גלידה [-] | hit_civilian |
| 10 | רוח | 1 | רוח-רפאים | רוח-רפאים [T] | all_correct |

## clue רפאים echoes target רוח-רפאים

Round 3. Clue **רפאים** is a surface variant of **רוח-רפאים**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 6 --method strong \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, strong_hebrew) vs openai/gpt-4o-mini (guesser) · board natural seed 6 trial 0 · count free · win, 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T רוח-רפאים | O ים | T אירופה | O פה | - אלים |
| O כפפה | O ארנב | T סוכן | T זוהר | O טעם |
| T שוקולד | - קברן | T אגודל | O אורח | T אפריקה |
| O קש | - מוות | O מאדים | - גלידה | T מקור |
| T דם | X דבר | - אש | - מסחרית | - ברמודה |

YOUR WORDS (9): רוח-רפאים, אירופה, סוכן, זוהר, שוקולד, אגודל, אפריקה, מקור, דם
OPPONENT (8): ים, פה, כפפה, ארנב, טעם, אורח, קש, מאדים
CIVILIAN (7): אלים, קברן, מוות, גלידה, אש, מסחרית, ברמודה
ASSASSIN (1): דבר

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | מיסטיקה | 3 | רוח-רפאים, זוהר, אגודל | מוות [-] | hit_civilian |
| 2 | מתוק | 2 | שוקולד, זוהר | שוקולד [T], גלידה [-] | hit_civilian |
| 3 | רפאים | 1 | רוח-רפאים | רוח-רפאים [T], קברן [-] | hit_civilian |
| 4 | לילה | 2 | אירופה, זוהר | סוכן [T], זוהר [T], אש [-] | hit_civilian |
| 5 | קונטיננטל | 2 | אירופה, אפריקה | אירופה [T], אפריקה [T], ברמודה [-] | hit_civilian |
| 6 | דמם | 3 | אגודל, מקור, דם | דם [T], אלים [-] | hit_civilian |
| 7 | אצבע | 2 | אגודל, מקור | אגודל [T], פה [O] | hit_opponent |
| 8 | מקורות | 1 | מקור | מקור [T] | all_correct |

## clue מקורות echoes target מקור

Round 8. Clue **מקורות** is a surface variant of **מקור**, which `clue_on_board` does not reject.

_Same game as above; see the transcript there._

## clue אורות echoes target אור

Round 1. Clue **אורות** is a surface variant of **אור**, which `clue_on_board` does not reject.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 7 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board natural seed 7 trial 0 · count free · win, 9 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - אחר | T נייר | O כוח | - שורשים | - אופרה |
| T מכשפה | T אלים | T אור | O כותנה | - מצנח |
| T אצטדיון | O גנב | O דלק | - אלף | T נס |
| T סל | O הודו | - חוף | O חד-קרן | - פרסה |
| T בנק | T יוון | O ספינה | X ספר | O צדק |

YOUR WORDS (9): נייר, מכשפה, אלים, אור, אצטדיון, נס, סל, בנק, יוון
OPPONENT (8): כוח, כותנה, גנב, דלק, הודו, חד-קרן, ספינה, צדק
CIVILIAN (7): אחר, שורשים, אופרה, מצנח, אלף, חוף, פרסה
ASSASSIN (1): ספר

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | אורות | 2 | אור, אלים | אור [T], אופרה [-] | hit_civilian |
| 2 | אולימפיאדה | 2 | אלים, אצטדיון | אצטדיון [T], יוון [T], נס [T] | all_correct |
| 3 | כסף | 1 | בנק | כוח [O] | hit_opponent |
| 4 | כסף | 1 | בנק | בנק [T], נייר [T] | all_correct |
| 5 | קסם | 1 | מכשפה | מכשפה [T], אלים [T] | all_correct |
| 6 | מים | 1 | סל | ספינה [O] | hit_opponent |
| 7 | מים | 1 | סל | חוף [-] | hit_civilian |
| 8 | מעגן | 1 | סל | מצנח [-] | hit_civilian |
| 9 | מים | 1 | סל | סל [T] | all_correct |


---

# Sound-paired targets

## clue אוניברסיטה: בשר + קשר

Round 1. Targets **בשר** and **קשר** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 3 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc free
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board natural seed 3 trial 0 · count free · loss (assassin), 16 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - קטשופ | O שרשרת | T אקדח | T סוכן | O מלון |
| T עלייה | O שחקן | - קל | O לב | T בשר |
| - עכביש | X מעמד | - גל | O מאדים | O צוללן |
| O אחות | - אלה | O חלל | T בעל | T קשר |
| - עיר | - יחידה | T דלק | T עוקץ | T מדליק |

YOUR WORDS (9): אקדח, סוכן, עלייה, בשר, בעל, קשר, דלק, עוקץ, מדליק
OPPONENT (8): שרשרת, מלון, שחקן, לב, מאדים, צוללן, אחות, חלל
CIVILIAN (7): קטשופ, קל, עכביש, גל, אלה, עיר, יחידה
ASSASSIN (1): מעמד

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | אוניברסיטה | 9 | אקדח, סוכן, עלייה, בשר, בעל, קשר, דלק, עוקץ, מדליק | קטשופ [-] | hit_civilian |
| 2 | מכה | 3 | קשר, דלק, עוקץ | עוקץ [T], עכביש [-] | hit_civilian |
| 3 | שוטף | 2 | דלק, מדליק | קשר [T], צוללן [O] | hit_opponent |
| 4 | יד | 0 |  | עיר [-] | hit_civilian |
| 5 | אש | 2 | בשר, דלק | דלק [T], שרשרת [O] | hit_opponent |
| 6 | שודד | 2 | עלייה, בשר | גל [-] | hit_civilian |
| 7 | מרחץ | 1 | בשר | סוכן [T] | stopped_early |
| 8 | יורה | 1 | אקדח | קל [-] | hit_civilian |
| 9 | יורה | 2 | אקדח, מדליק | אקדח [T], אלה [-] | hit_civilian |
| 10 | קנה | 2 | עלייה, מדליק | מאדים [O] | hit_opponent |
| 11 | זן | 4 | עלייה, בשר, בעל, מדליק | חלל [O] | hit_opponent |
| 12 | עור | 1 | בעל | לב [O] | hit_opponent |
| 13 | מצה | 4 | עלייה, בשר, בעל, מדליק | מלון [O] | hit_opponent |
| 14 | שריפה | 2 | בשר, מדליק | מדליק [T], בשר [T] | stopped_early |
| 15 | מדבר | 2 | עלייה, בעל | שחקן [O] | hit_opponent |
| 16 | תאווה | 2 | עלייה, בעל | מעמד [X] | hit_assassin |

## clue חומר: ספר + תפר

Round 1. Targets **ספר** and **תפר** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 26 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board natural seed 26 trial 0 · count free · loss (assassin), 10 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T כפתור | O מטר | O כפפה | - ענק | T שנהב |
| - לבנה | X רוח | T ספר | O צל | O ירח |
| T אח | - סולם | O דשא | - מאבק | - רולטה |
| O קרח | - קיץ | O תשובה | T יוון | T תפר |
| - דבש | T אוזן-המן | T צלחת | T חווה | O נסיכה |

YOUR WORDS (9): כפתור, שנהב, ספר, אח, יוון, תפר, אוזן-המן, צלחת, חווה
OPPONENT (8): מטר, כפפה, צל, ירח, דשא, קרח, תשובה, נסיכה
CIVILIAN (7): ענק, לבנה, סולם, מאבק, רולטה, קיץ, דבש
ASSASSIN (1): רוח

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | חומר | 2 | ספר, תפר | דשא [O] | hit_opponent |
| 2 | חומר | 2 | ספר, כפתור | חווה [T], כפפה [O] | hit_opponent |
| 3 | חומר | 2 | ספר, תפר | ספר [T], דבש [-] | hit_civilian |
| 4 | חומר | 2 | שנהב, אוזן-המן | קרח [O] | hit_opponent |
| 5 | חומר | 2 | אח, תפר | מטר [O] | hit_opponent |
| 6 | חומר | 2 | כפתור, שנהב | צלחת [T], לבנה [-] | hit_civilian |
| 7 | חומר | 2 | שנהב, אוזן-המן | שנהב [T], ענק [-] | hit_civilian |
| 8 | משפחה | 1 | אח | אח [T], נסיכה [O] | hit_opponent |
| 9 | מעיל | 1 | אוזן-המן | מאבק [-] | hit_civilian |
| 10 | איבר | 1 | אוזן-המן | אוזן-המן [T], רוח [X] | hit_assassin |

## clue מקצב: קצב + חצב

Round 8. Targets **קצב** and **חצב** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 12 --method strong \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

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

## clue מגיע: קצב + חצב

Round 2. Targets **קצב** and **חצב** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 12 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc free
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board dual_100 seed 12 trial 0 · count free · loss (assassin), 17 rounds · 20260823T191234131145Z

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
| 1 | כוח | 2 | מנוע, אוגר | מנוע [T] | stopped_early |
| 2 | מגיע | 5 | אוגר, קצב, מעמד, מקל, חצב | עמוד [O] | hit_opponent |
| 3 | עורמה | 5 | אוגר, קצב, בסיס, מעמד, חצב | מאבק [-] | hit_civilian |
| 4 | בניין | 2 | בסיס, מעמד | בסיס [T] | stopped_early |
| 5 | בשר | 2 | קצב, מעמד | חול [O] | hit_opponent |
| 6 | בשר | 2 | קצב, אמן | מלח [O] | hit_opponent |
| 7 | מנחת | 1 | מקל | קצב [T] | stopped_early |
| 8 | מדרכה | 4 | אמן, מעמד, חצב, מקל | קש [O] | hit_opponent |
| 9 | משמרת | 2 | מקל, מעמד | פנים [-] | hit_civilian |
| 10 | הדס | 2 | אמן, חצב | עצם [-] | hit_civilian |
| 11 | מפעל | 2 | אמן, מקל | אוגר [T], מקל [T], בוקר [O] | hit_opponent |
| 12 | במקום | 1 | מעמד | מעמד [T] | stopped_early |
| 13 | במה | 1 | אולם | אולם [T], אלף [O] | hit_opponent |
| 14 | אבן | 2 | חצב, אמן | בר [-] | hit_civilian |
| 15 | בור | 1 | חצב | גזר [O] | hit_opponent |
| 16 | קרקע | 1 | חצב | חולצה [-] | hit_civilian |
| 17 | ריניים | 1 | חצב | חום [X] | hit_assassin |

## clue עורמה: קצב + חצב

Round 3. Targets **קצב** and **חצב** differ only in the first letter.

_Same game as above; see the transcript there._

## clue אמנות: ספר + תפר

Round 1. Targets **ספר** and **תפר** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 26 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc min2
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board natural seed 26 trial 0 · count min2 · win, 11 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T כפתור | O מטר | O כפפה | - ענק | T שנהב |
| - לבנה | X רוח | T ספר | O צל | O ירח |
| T אח | - סולם | O דשא | - מאבק | - רולטה |
| O קרח | - קיץ | O תשובה | T יוון | T תפר |
| - דבש | T אוזן-המן | T צלחת | T חווה | O נסיכה |

YOUR WORDS (9): כפתור, שנהב, ספר, אח, יוון, תפר, אוזן-המן, צלחת, חווה
OPPONENT (8): מטר, כפפה, צל, ירח, דשא, קרח, תשובה, נסיכה
CIVILIAN (7): ענק, לבנה, סולם, מאבק, רולטה, קיץ, דבש
ASSASSIN (1): רוח

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | אמנות | 2 | ספר, תפר | ספר [T], תשובה [O] | hit_opponent |
| 2 | משפחה | 2 | אח, חווה | אח [T], אוזן-המן [T], מאבק [-] | hit_civilian |
| 3 | חומר | 2 | כפתור, תפר | דשא [O] | hit_opponent |
| 4 | חומר | 2 | כפתור, תפר | חווה [T], דבש [-] | hit_civilian |
| 5 | חומר | 2 | כפתור, תפר | כפפה [O] | hit_opponent |
| 6 | חומר | 2 | כפתור, תפר | כפתור [T], תפר [T], צלחת [T] | all_correct |
| 7 | ארץ | 2 | שנהב, יוון | לבנה [-] | hit_civilian |
| 8 | ארץ | 2 | שנהב, יוון | ירח [O] | hit_opponent |
| 9 | ארץ | 2 | שנהב, יוון | ענק [-] | hit_civilian |
| 10 | ארץ | 2 | שנהב, יוון | יוון [T], קרח [O] | hit_opponent |
| 11 | שנה | 1 | שנהב | שנהב [T] | all_correct |

## clue פרנסה: ספר + תפר

Round 5. Targets **ספר** and **תפר** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 26 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc min2
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board natural seed 26 trial 0 · count min2 · loss (assassin), 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T כפתור | O מטר | O כפפה | - ענק | T שנהב |
| - לבנה | X רוח | T ספר | O צל | O ירח |
| T אח | - סולם | O דשא | - מאבק | - רולטה |
| O קרח | - קיץ | O תשובה | T יוון | T תפר |
| - דבש | T אוזן-המן | T צלחת | T חווה | O נסיכה |

YOUR WORDS (9): כפתור, שנהב, ספר, אח, יוון, תפר, אוזן-המן, צלחת, חווה
OPPONENT (8): מטר, כפפה, צל, ירח, דשא, קרח, תשובה, נסיכה
CIVILIAN (7): ענק, לבנה, סולם, מאבק, רולטה, קיץ, דבש
ASSASSIN (1): רוח

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | כוכב | 2 | יוון, שנהב | ירח [O] | hit_opponent |
| 2 | זהב | 2 | שנהב, אח | שנהב [T], דבש [-] | hit_civilian |
| 3 | הלל | 2 | חווה, כפתור | חווה [T], יוון [T] | stopped_early |
| 4 | עוגן | 2 | כפתור, ספר | לבנה [-] | hit_civilian |
| 5 | פרנסה | 3 | ספר, תפר, אח | צל [O] | hit_opponent |
| 6 | קשר | 3 | אח, תפר, כפתור | כפתור [T], מאבק [-] | hit_civilian |
| 7 | כתב | 2 | ספר, תפר | ספר [T] | stopped_early |
| 8 | חוש | 2 | אח, תפר | רוח [X] | hit_assassin |

## clue כתב: ספר + תפר

Round 7. Targets **ספר** and **תפר** differ only in the first letter.

_Same game as above; see the transcript there._

## clue ציור: קצב + חצב

Round 3. Targets **קצב** and **חצב** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_100 --seed 12 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc min2
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board dual_100 seed 12 trial 0 · count min2 · loss (assassin), 11 rounds · 20260823T191234131145Z

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
| 1 | מנהיג | 2 | קצב, בסיס | בר [-] | hit_civilian |
| 2 | יחידה | 3 | בסיס, מנוע, חצב | עמוד [O] | hit_opponent |
| 3 | ציור | 3 | קצב, חצב, אמן | מנוע [T], מאבק [-] | hit_civilian |
| 4 | קליפה | 2 | אוגר, חצב | בוקר [O] | hit_opponent |
| 5 | מבנה | 4 | אוגר, אולם, קצב, מעמד | בסיס [T], קש [O] | hit_opponent |
| 6 | guild | 2 | קצב, חצב | בול [-] | hit_civilian |
| 7 | מרחץ | 3 | אוגר, מעמד, קצב | פנים [-] | hit_civilian |
| 8 | קירות | 2 | מעמד, מקל | אלה [O] | hit_opponent |
| 9 | בניין | 2 | מעמד, קצב | מעמד [T], עצם [-] | hit_civilian |
| 10 | עץ | 3 | אמן, מקל, קצב | גזר [O] | hit_opponent |
| 11 | מעגל | 3 | אוגר, אולם, קצב | חום [X] | hit_assassin |

## clue guild: קצב + חצב

Round 6. Targets **קצב** and **חצב** differ only in the first letter.

_Same game as above; see the transcript there._

## clue ירושלים: קשר + בשר

Round 1. Targets **קשר** and **בשר** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 3 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc min3
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board natural seed 3 trial 0 · count min3 · loss (assassin), 2 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - קטשופ | O שרשרת | T אקדח | T סוכן | O מלון |
| T עלייה | O שחקן | - קל | O לב | T בשר |
| - עכביש | X מעמד | - גל | O מאדים | O צוללן |
| O אחות | - אלה | O חלל | T בעל | T קשר |
| - עיר | - יחידה | T דלק | T עוקץ | T מדליק |

YOUR WORDS (9): אקדח, סוכן, עלייה, בשר, בעל, קשר, דלק, עוקץ, מדליק
OPPONENT (8): שרשרת, מלון, שחקן, לב, מאדים, צוללן, אחות, חלל
CIVILIAN (7): קטשופ, קל, עכביש, גל, אלה, עיר, יחידה
ASSASSIN (1): מעמד

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | ירושלים | 4 | קשר, בעל, מדליק, בשר | עיר [-] | hit_civilian |
| 2 | מטרה | 8 | אקדח, סוכן, עלייה, בשר, בעל, קשר, דלק, עוקץ | קשר [T], עוקץ [T], מעמד [X] | hit_assassin |

## clue מטרה: בשר + קשר

Round 2. Targets **בשר** and **קשר** differ only in the first letter.

_Same game as above; see the transcript there._

## clue חיבור: בשר + קשר

Round 6. Targets **בשר** and **קשר** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 3 --method strong \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc min3
```

### openai/gpt-4o-mini (codemaster, strong_hebrew) vs openai/gpt-4o-mini (guesser) · board natural seed 3 trial 0 · count min3 · win, 9 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - קטשופ | O שרשרת | T אקדח | T סוכן | O מלון |
| T עלייה | O שחקן | - קל | O לב | T בשר |
| - עכביש | X מעמד | - גל | O מאדים | O צוללן |
| O אחות | - אלה | O חלל | T בעל | T קשר |
| - עיר | - יחידה | T דלק | T עוקץ | T מדליק |

YOUR WORDS (9): אקדח, סוכן, עלייה, בשר, בעל, קשר, דלק, עוקץ, מדליק
OPPONENT (8): שרשרת, מלון, שחקן, לב, מאדים, צוללן, אחות, חלל
CIVILIAN (7): קטשופ, קל, עכביש, גל, אלה, עיר, יחידה
ASSASSIN (1): מעמד

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | רשיון | 3 | אקדח, סוכן, קשר | סוכן [T], אקדח [T], מלון [O] | hit_opponent |
| 2 | משפחה | 3 | בעל, קשר, עוקץ | אחות [O] | hit_opponent |
| 3 | תאורה | 3 | מדליק, עלייה, דלק | מדליק [T], דלק [T], חלל [O] | hit_opponent |
| 4 | נישואין | 3 | בעל, קשר, עוקץ | בעל [T], לב [O] | hit_opponent |
| 5 | תעופה | 3 | עלייה, קשר, עוקץ | עלייה [T], צוללן [O] | hit_opponent |
| 6 | חיבור | 3 | בשר, קשר, עוקץ | קשר [T], שרשרת [O] | hit_opponent |
| 7 | פרי | 2 | בשר, עוקץ | בשר [T], קטשופ [-] | hit_civilian |
| 8 | דבורה | 1 | עוקץ | עכביש [-] | hit_civilian |
| 9 | עקיצה | 1 | עוקץ | עוקץ [T] | all_correct |

## clue שולחן: ספר + תפר

Round 2. Targets **ספר** and **תפר** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 26 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc min3
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board natural seed 26 trial 0 · count min3 · loss (assassin), 3 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T כפתור | O מטר | O כפפה | - ענק | T שנהב |
| - לבנה | X רוח | T ספר | O צל | O ירח |
| T אח | - סולם | O דשא | - מאבק | - רולטה |
| O קרח | - קיץ | O תשובה | T יוון | T תפר |
| - דבש | T אוזן-המן | T צלחת | T חווה | O נסיכה |

YOUR WORDS (9): כפתור, שנהב, ספר, אח, יוון, תפר, אוזן-המן, צלחת, חווה
OPPONENT (8): מטר, כפפה, צל, ירח, דשא, קרח, תשובה, נסיכה
CIVILIAN (7): ענק, לבנה, סולם, מאבק, רולטה, קיץ, דבש
ASSASSIN (1): רוח

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | ביצה | 3 | שנהב, יוון, אוזן-המן | צלחת [T] | stopped_early |
| 2 | שולחן | 4 | כפתור, ספר, תפר, יוון | סולם [-] | hit_civilian |
| 3 | בינה | 7 | כפתור, שנהב, ספר, אח, יוון, תפר, אוזן-המן | רוח [X] | hit_assassin |

## clue בינה: ספר + תפר

Round 3. Targets **ספר** and **תפר** differ only in the first letter.

_Same game as above; see the transcript there._

## clue בית: ספר + תפר

Round 1. Targets **ספר** and **תפר** differ only in the first letter.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 26 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc min3
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board natural seed 26 trial 0 · count min3 · loss (assassin), 11 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T כפתור | O מטר | O כפפה | - ענק | T שנהב |
| - לבנה | X רוח | T ספר | O צל | O ירח |
| T אח | - סולם | O דשא | - מאבק | - רולטה |
| O קרח | - קיץ | O תשובה | T יוון | T תפר |
| - דבש | T אוזן-המן | T צלחת | T חווה | O נסיכה |

YOUR WORDS (9): כפתור, שנהב, ספר, אח, יוון, תפר, אוזן-המן, צלחת, חווה
OPPONENT (8): מטר, כפפה, צל, ירח, דשא, קרח, תשובה, נסיכה
CIVILIAN (7): ענק, לבנה, סולם, מאבק, רולטה, קיץ, דבש
ASSASSIN (1): רוח

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | בית | 3 | חווה, ספר, תפר | ספר [T], סולם [-] | hit_civilian |
| 2 | בית | 3 | אח, חווה, אוזן-המן | כפתור [T], מטר [O] | hit_opponent |
| 3 | משפחה | 3 | אח, חווה, אוזן-המן | אח [T], אוזן-המן [T], מאבק [-] | hit_civilian |
| 4 | בית | 3 | חווה, שנהב, תפר | חווה [T], דשא [O] | hit_opponent |
| 5 | חומר | 3 | שנהב, תפר, צלחת | כפפה [O] | hit_opponent |
| 6 | חפץ | 3 | שנהב, תפר, צלחת | תשובה [O] | hit_opponent |
| 7 | חפץ | 3 | שנהב, תפר, צלחת | ענק [-] | hit_civilian |
| 8 | חומר | 3 | שנהב, תפר, צלחת | דבש [-] | hit_civilian |
| 9 | חומר | 3 | שנהב, תפר, צלחת | קרח [O] | hit_opponent |
| 10 | חפץ | 3 | שנהב, תפר, צלחת | שנהב [T], לבנה [-] | hit_civilian |
| 11 | חפץ | 3 | יוון, תפר, צלחת | רוח [X] | hit_assassin |


---

# Over-extension into the assassin

## clue טקסטיל solved, then the assassin

Round 4. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 17 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 17 trial 0 · count free · loss (assassin), 4 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - קשת | T אפיקומן | T פינגווין | O בוחן | T חריף |
| T חוף | - משקף | O חייזר | O סיבוב | - כוכב |
| X לבוש | T קיר | - רוח-רפאים | - שגרירות | O ברמודה |
| O אתר | - לייזר | T כותנה | O אשפה | T אי |
| T אפריקה | O חיבור | O אש | - תנועה | T מיליונר |

YOUR WORDS (9): אפיקומן, פינגווין, חריף, חוף, קיר, כותנה, אי, אפריקה, מיליונר
OPPONENT (8): בוחן, חייזר, סיבוב, ברמודה, אתר, אשפה, חיבור, אש
CIVILIAN (7): קשת, משקף, כוכב, רוח-רפאים, שגרירות, לייזר, תנועה
ASSASSIN (1): לבוש

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | ים | 2 | חוף, אי | חוף [T], אי [T], קיר [T] | all_correct |
| 2 | יבשה | 2 | אפריקה, אפיקומן | אפריקה [T], אש [O] | hit_opponent |
| 3 | עושר | 1 | מיליונר | מיליונר [T], קשת [-] | hit_civilian |
| 4 | טקסטיל | 1 | כותנה | כותנה [T], לבוש [X] | hit_assassin |

## clue טבע solved, then the assassin

Round 9. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 19 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 19 trial 0 · count free · loss (assassin), 9 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T שגרירות | - סוס | O כיסא | T ברווז | T הגירה |
| - כתר | T אקדח | O חמה | - עונש | O סדר |
| T מורה | - משטרה | - עבר | T שמן | O בחינה |
| - טיל | T גורד-שחקים | O כוח | T פרח | X קנגורו |
| T אות | O לבוש | - חוסר | O לוויין | O מכשפה |

YOUR WORDS (9): שגרירות, ברווז, הגירה, אקדח, מורה, שמן, גורד-שחקים, פרח, אות
OPPONENT (8): כיסא, חמה, סדר, בחינה, כוח, לבוש, לוויין, מכשפה
CIVILIAN (7): סוס, כתר, עונש, משטרה, עבר, טיל, חוסר
ASSASSIN (1): קנגורו

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | חינוך | 2 | מורה, אות | מורה [T], בחינה [O] | hit_opponent |
| 2 | נוף | 2 | גורד-שחקים, פרח | כיסא [O] | hit_opponent |
| 3 | נוף | 2 | גורד-שחקים, פרח | כתר [-] | hit_civilian |
| 4 | נוף | 2 | גורד-שחקים, פרח | חמה [O] | hit_opponent |
| 5 | נוף | 2 | גורד-שחקים, פרח | גורד-שחקים [T], שגרירות [T], משטרה [-] | hit_civilian |
| 6 | נוצה | 2 | ברווז, פרח | סוס [-] | hit_civilian |
| 7 | נשק | 1 | אקדח | אקדח [T], טיל [-] | hit_civilian |
| 8 | טבע | 2 | ברווז, פרח | כוח [O] | hit_opponent |
| 9 | טבע | 2 | ברווז, פרח | פרח [T], ברווז [T], קנגורו [X] | hit_assassin |

## clue נמוך solved, then the assassin

Round 9. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 20 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 20 trial 0 · count free · loss (assassin), 9 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O אולימפוס | X לבוש | - צוללן | T סיכה | T יחידה |
| - שולחן | T אתר | O מועדון | O כינור | O חלל |
| T פרק | O יום | - גשר | - מעיין | T בוחן |
| T טלסקופ | T גמד | - עבר | - רולטה | O אייל |
| T שוט | O מיטה | O פרח | T מראה | - מאלף |

YOUR WORDS (9): סיכה, יחידה, אתר, פרק, בוחן, טלסקופ, גמד, שוט, מראה
OPPONENT (8): אולימפוס, מועדון, כינור, חלל, יום, אייל, מיטה, פרח
CIVILIAN (7): צוללן, שולחן, גשר, מעיין, עבר, רולטה, מאלף
ASSASSIN (1): לבוש

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | מדע | 2 | טלסקופ, אתר | טלסקופ [T], חלל [O] | hit_opponent |
| 2 | ראי | 1 | מראה | מראה [T], אולימפוס [O] | hit_opponent |
| 3 | מבחן | 2 | בוחן, יחידה | בוחן [T], מעיין [-] | hit_civilian |
| 4 | מחלקה | 2 | יחידה, פרק | יחידה [T], מועדון [O] | hit_opponent |
| 5 | נמל | 1 | אתר | גשר [-] | hit_civilian |
| 6 | חבל | 2 | גמד, פרק | צוללן [-] | hit_civilian |
| 7 | קשר | 2 | סיכה, אתר | סיכה [T], כינור [O] | hit_opponent |
| 8 | מקום | 2 | אתר, פרק | אתר [T], מאלף [-] | hit_civilian |
| 9 | נמוך | 1 | גמד | גמד [T], לבוש [X] | hit_assassin |

## clue קסם solved, then the assassin

Round 4. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 24 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 24 trial 0 · count free · loss (assassin), 4 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - לוחם | - טייס | - צלחת | O ריקוד | O עבר |
| T נייר | X חד-קרן | - יוון | O קיץ | T צרפת |
| - סילון | O טיל | T אשף | - צופים | T שן |
| T מזלג | T שקל | - נשימה | T מעגל | O בייגלה |
| T אייל | T כינור | O בועה | O מראה | O אנגליה |

YOUR WORDS (9): נייר, צרפת, אשף, שן, מזלג, שקל, מעגל, אייל, כינור
OPPONENT (8): ריקוד, עבר, קיץ, טיל, בייגלה, בועה, מראה, אנגליה
CIVILIAN (7): לוחם, טייס, צלחת, יוון, סילון, צופים, נשימה
ASSASSIN (1): חד-קרן

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | מוזיקה | 2 | כינור, אשף | ריקוד [O] | hit_opponent |
| 2 | מוסיקה | 2 | כינור, אשף | כינור [T], נייר [T], מראה [O] | hit_opponent |
| 3 | כסף | 1 | שקל | שקל [T], קיץ [O] | hit_opponent |
| 4 | קסם | 1 | אשף | אשף [T], חד-קרן [X] | hit_assassin |

## clue נשוי solved, then the assassin

Round 8. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 3 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board natural seed 3 trial 0 · count free · loss (assassin), 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - קטשופ | O שרשרת | T אקדח | T סוכן | O מלון |
| T עלייה | O שחקן | - קל | O לב | T בשר |
| - עכביש | X מעמד | - גל | O מאדים | O צוללן |
| O אחות | - אלה | O חלל | T בעל | T קשר |
| - עיר | - יחידה | T דלק | T עוקץ | T מדליק |

YOUR WORDS (9): אקדח, סוכן, עלייה, בשר, בעל, קשר, דלק, עוקץ, מדליק
OPPONENT (8): שרשרת, מלון, שחקן, לב, מאדים, צוללן, אחות, חלל
CIVILIAN (7): קטשופ, קל, עכביש, גל, אלה, עיר, יחידה
ASSASSIN (1): מעמד

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | אש | 3 | אקדח, דלק, מדליק | אקדח [T], לב [O] | hit_opponent |
| 2 | אש | 2 | דלק, מדליק | אחות [O] | hit_opponent |
| 3 | אש | 2 | דלק, מדליק | אלה [-] | hit_civilian |
| 4 | אש | 3 | דלק, מדליק, עוקץ | שרשרת [O] | hit_opponent |
| 5 | אש | 2 | דלק, מדליק | בשר [T], סוכן [T], קשר [T] | all_correct |
| 6 | אש | 2 | דלק, מדליק | עכביש [-] | hit_civilian |
| 7 | אש | 2 | דלק, מדליק | דלק [T], מדליק [T], קל [-] | hit_civilian |
| 8 | נשוי | 1 | בעל | בעל [T], מעמד [X] | hit_assassin |

## clue ים solved, then the assassin

Round 3. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 5 --method strong \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, strong_hebrew) vs google/gemini-2.5-flash (guesser) · board natural seed 5 trial 0 · count free · loss (assassin), 3 rounds · 20260823T191234131145Z

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
| 1 | בימה | 2 | מופע, תיאטרון | תיאטרון [T], מופע [T] | stopped_early |
| 2 | חלל | 2 | חייזר, זריקה | חייזר [T], קוד [O] | hit_opponent |
| 3 | ים | 1 | חוף | חוף [T], פיראט [X] | hit_assassin |

## clue תרבות solved, then the assassin

Round 1. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 5 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

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

## clue מפלצת solved, then the assassin

Round 1. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 5 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc free
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board natural seed 5 trial 0 · count free · loss (assassin), 1 rounds · 20260823T191234131145Z

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
| 1 | מפלצת | 1 | חייזר | חייזר [T], פיראט [X] | hit_assassin |

## clue קולנוע solved, then the assassin

Round 2. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 8 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board natural seed 8 trial 0 · count free · loss (assassin), 2 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| X סוכה | O תת | O סילון | - פרסה | - פרי |
| T אות | T פרק | T מלכה | O קרן | - שיח |
| O לוויתן | O אשף | O רוח | T חג | T אנטארקטיקה |
| T בית-ספר | - בית-כנסת | T משפט | T סרט | - שורש |
| T קיץ | - לייזר | O תפר | - מרגל | O מאושר |

YOUR WORDS (9): אות, פרק, מלכה, חג, אנטארקטיקה, בית-ספר, משפט, סרט, קיץ
OPPONENT (8): תת, סילון, קרן, לוויתן, אשף, רוח, תפר, מאושר
CIVILIAN (7): פרסה, פרי, שיח, בית-כנסת, שורש, לייזר, מרגל
ASSASSIN (1): סוכה

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | לימוד | 2 | בית-ספר, משפט | בית-ספר [T], מלכה [T], לוויתן [O] | hit_opponent |
| 2 | קולנוע | 1 | סרט | סרט [T], סוכה [X] | hit_assassin |

## clue לבוש solved, then the assassin

Round 2. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 11 --method strong \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, strong_hebrew) vs openai/gpt-4o-mini (guesser) · board natural seed 11 trial 0 · count free · loss (assassin), 2 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O דם | O אלוף | - להקה | - גורד-שחקים | O שדה |
| O קטשופ | - כתב | - שגרירות | - מעמד | T חולצה |
| T פה | - מסע | T זמן | T מרכז | X רגל |
| O תולעת | T קשר | T מסלול | O קברן | O ביצה |
| O קשה | T שקל | T קזינו | - אב | T יד |

YOUR WORDS (9): חולצה, פה, זמן, מרכז, קשר, מסלול, שקל, קזינו, יד
OPPONENT (8): דם, אלוף, שדה, קטשופ, תולעת, קברן, ביצה, קשה
CIVILIAN (7): להקה, גורד-שחקים, כתב, שגרירות, מעמד, מסע, אב
ASSASSIN (1): רגל

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | מרחק | 2 | מרכז, מסלול | מרכז [T], מסלול [T], מסע [-] | hit_civilian |
| 2 | לבוש | 1 | חולצה | חולצה [T], רגל [X] | hit_assassin |

## clue אור solved, then the assassin

Round 4. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 14 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board natural seed 14 trial 0 · count free · loss (assassin), 4 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| - מצרים | - פה | O גנב | T קור | - מלאך |
| T יוון | O חמה | - שורש | T מוות | T רגל |
| T קרח | O עבר | O נהג | X חוסר | - בית-חולים |
| O תשובה | T מעבר | T שוקולד | T תל-אביב | - גורד-שחקים |
| O מסך | T יום | O דבש | O רב | - דג |

YOUR WORDS (9): קור, יוון, מוות, רגל, קרח, מעבר, שוקולד, תל-אביב, יום
OPPONENT (8): גנב, חמה, עבר, נהג, תשובה, מסך, דבש, רב
CIVILIAN (7): מצרים, פה, מלאך, שורש, בית-חולים, גורד-שחקים, דג
ASSASSIN (1): חוסר

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | קר | 2 | קור, קרח | קרח [T], קור [T] | stopped_early |
| 2 | עיר | 2 | תל-אביב, יוון | תל-אביב [T], יוון [T], מצרים [-] | hit_civilian |
| 3 | חג | 1 | יום | חמה [O] | hit_opponent |
| 4 | אור | 1 | יום | יום [T], חוסר [X] | hit_assassin |

## clue רוח solved, then the assassin

Round 6. Every intended target was already found when the guesser went on.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style natural --seed 23 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board natural seed 23 trial 0 · count free · loss (assassin), 6 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T מיטה | T מוות | O צוללן | T רשת | O הוליווד |
| - מסלול | T קטשופ | - בונה | T לונדון | - ציור |
| T מנוף | - אי | O דוב | O כדור | - סרט |
| O זכוכית | T אורגני | - אוגר | X צל | O אלה |
| T גלידה | - ריח | T סילון | O מצנח | O אביר |

YOUR WORDS (9): מיטה, מוות, רשת, קטשופ, לונדון, מנוף, אורגני, גלידה, סילון
OPPONENT (8): צוללן, הוליווד, דוב, כדור, זכוכית, אלה, מצנח, אביר
CIVILIAN (7): מסלול, בונה, ציור, אי, סרט, אוגר, ריח
ASSASSIN (1): צל

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | אוכל | 2 | קטשופ, גלידה | קטשופ [T], גלידה [T], אוגר [-] | hit_civilian |
| 2 | עיר | 1 | לונדון | לונדון [T], הוליווד [O] | hit_opponent |
| 3 | בית | 2 | מיטה, מנוף | מיטה [T], בונה [-] | hit_civilian |
| 4 | חבל | 2 | מנוף, רשת | רשת [T], כדור [O] | hit_opponent |
| 5 | רוח | 1 | סילון | ריח [-] | hit_civilian |
| 6 | רוח | 1 | סילון | סילון [T], צל [X] | hit_assassin |


---

# Assassin on the first guess

## clue גוף → נשימה

Round 7. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 0 --method strong \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, strong_hebrew) vs google/gemini-2.5-flash (guesser) · board dual_0 seed 0 trial 0 · count free · loss (assassin), 7 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T קשר | - חליל | - בית-כנסת | T מצח | T משחק |
| X נשימה | T מוסקבה | T אפיקומן | T בייגלה | O כוס |
| T ציור | O תולעת | - שבתאי | O רצפה | - מאגר |
| O ספינה | O משטרה | - מסלול | T יורה | O אצטדיון |
| O מדען | - מסוק | T לבוש | - דם | O ים |

YOUR WORDS (9): קשר, מצח, משחק, מוסקבה, אפיקומן, בייגלה, ציור, יורה, לבוש
OPPONENT (8): כוס, תולעת, רצפה, ספינה, משטרה, אצטדיון, מדען, ים
CIVILIAN (7): חליל, בית-כנסת, שבתאי, מאגר, מסלול, מסוק, דם
ASSASSIN (1): נשימה

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | איור | 1 | ציור | ציור [T] | stopped_early |
| 2 | בירה | 1 | מוסקבה | כוס [O] | hit_opponent |
| 3 | ביגוד | 1 | לבוש | לבוש [T] | stopped_early |
| 4 | מאפה | 2 | אפיקומן, בייגלה | בייגלה [T], אפיקומן [T] | stopped_early |
| 5 | בירה | 1 | מוסקבה | מוסקבה [T], ים [O] | hit_opponent |
| 6 | שעשוע | 1 | משחק | משחק [T] | stopped_early |
| 7 | גוף | 2 | מצח, קשר | נשימה [X] | hit_assassin |

## clue תקוע → נשימה

Round 7. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 0 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc free
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board dual_0 seed 0 trial 0 · count free · loss (assassin), 7 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T קשר | - חליל | - בית-כנסת | T מצח | T משחק |
| X נשימה | T מוסקבה | T אפיקומן | T בייגלה | O כוס |
| T ציור | O תולעת | - שבתאי | O רצפה | - מאגר |
| O ספינה | O משטרה | - מסלול | T יורה | O אצטדיון |
| O מדען | - מסוק | T לבוש | - דם | O ים |

YOUR WORDS (9): קשר, מצח, משחק, מוסקבה, אפיקומן, בייגלה, ציור, יורה, לבוש
OPPONENT (8): כוס, תולעת, רצפה, ספינה, משטרה, אצטדיון, מדען, ים
CIVILIAN (7): חליל, בית-כנסת, שבתאי, מאגר, מסלול, מסוק, דם
ASSASSIN (1): נשימה

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | גבעול | 2 | קשר, אפיקומן | ציור [T], אפיקומן [T] | stopped_early |
| 2 | לב | 6 | קשר, מצח, משחק, מוסקבה, בייגלה, יורה | — | guesser_failure |
| 3 | דקדקן | 2 | קשר, משחק | מצח [T], מדען [O] | hit_opponent |
| 4 | וינסלוגר | 3 | קשר, משחק, מוסקבה | קשר [T] | stopped_early |
| 5 | מוגן | 2 | משחק, בייגלה | בית-כנסת [-] | hit_civilian |
| 6 | עיר | 0 |  | מסלול [-] | hit_civilian |
| 7 | תקוע | 2 | בייגלה, יורה | נשימה [X] | hit_assassin |

## clue ירח → אסר

Round 8. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 1 --method strong \
    --cm gpt-4o-mini --guesser gpt-4o-mini --cc free
```

### openai/gpt-4o-mini (codemaster, strong_hebrew) vs openai/gpt-4o-mini (guesser) · board dual_0 seed 1 trial 0 · count free · loss (assassin), 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T אשפה | T ראש | T שולחן | - סדר | X אסר |
| T דבש | O סירה | - מכשפה | - סל | O מסך |
| T כיפה | T מזלג | - מעיין | - אפריקה | O דבק |
| - אולימפוס | O טייס | T עוקץ | O פצצה | - בנק |
| T לוחם | O קרצייה | T מזל | O קברן | O טעם |

YOUR WORDS (9): אשפה, ראש, שולחן, דבש, כיפה, מזלג, עוקץ, לוחם, מזל
OPPONENT (8): סירה, מסך, דבק, טייס, פצצה, קרצייה, קברן, טעם
CIVILIAN (7): סדר, מכשפה, סל, מעיין, אפריקה, אולימפוס, בנק
ASSASSIN (1): אסר

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | אצבע | 2 | מזלג, עוקץ | מזלג [T], דבש [T], ראש [T] | all_correct |
| 2 | קרב | 2 | לוחם, עוקץ | לוחם [T], פצצה [O] | hit_opponent |
| 3 | לילה | 2 | כיפה, מזל | סירה [O] | hit_opponent |
| 4 | ריהוט | 1 | שולחן | שולחן [T], סל [-] | hit_civilian |
| 5 | מקום | 2 | כיפה, עוקץ | סדר [-] | hit_civilian |
| 6 | ברווז | 2 | מזל, אשפה | טייס [O] | hit_opponent |
| 7 | כוכב | 2 | מזל, עוקץ | אולימפוס [-] | hit_civilian |
| 8 | ירח | 2 | מזל, כיפה | אסר [X] | hit_assassin |

## clue מוזיקה → תל-אביב

Round 8. No correct guess to anchor on; the first pick ended the game.

_Same game as above; see the transcript there._

## clue מילה → לונדון

Round 8. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 3 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 3 trial 0 · count free · loss (assassin), 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T ברווז | - לשון | T מאגר | O חתיכה | O טייס |
| - עץ | O אורגני | T שטר | O קיץ | O כפפה |
| - כוכב | T שן | T אתר | T אשף | X לונדון |
| - ראש | - חופה | T ארץ | T ים | - תולעת |
| T רובוט | - אצטדיון | O נמל | O פרח | O שוט |

YOUR WORDS (9): ברווז, מאגר, שטר, שן, אתר, אשף, ארץ, ים, רובוט
OPPONENT (8): חתיכה, טייס, אורגני, קיץ, כפפה, נמל, פרח, שוט
CIVILIAN (7): לשון, עץ, כוכב, ראש, חופה, תולעת, אצטדיון
ASSASSIN (1): לונדון

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | מים | 2 | ים, מאגר | ים [T], נמל [O] | hit_opponent |
| 2 | מים | 2 | ברווז, מאגר | חופה [-] | hit_civilian |
| 3 | מים | 2 | ברווז, מאגר | מאגר [T], ארץ [T], ברווז [T] | all_correct |
| 4 | מכונה | 2 | שטר, רובוט | רובוט [T], טייס [O] | hit_opponent |
| 5 | מקום | 2 | אתר, שטר | אתר [T], אצטדיון [-] | hit_civilian |
| 6 | מילה | 0 |  | לשון [-] | hit_civilian |
| 7 | מילה | 1 | שן | אורגני [O] | hit_opponent |
| 8 | מילה | 0 |  | לונדון [X] | hit_assassin |

## clue מלחמה → תל-אביב

Round 18. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 2 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc free
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board dual_0 seed 2 trial 0 · count free · loss (assassin), 18 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T לשון | O מחילה | - רוח-רפאים | - עכבר | T חד-קרן |
| - חריף | T מחשב | - פרח | T שן | - מיליונר |
| O גורד-שחקים | T אצטדיון | O קזינו | T כף | O חופה |
| O מעגל | X תל-אביב | T בייגלה | T חיים | O חוק |
| T הרמון | - כפתור | O תפר | O נמל | - לוויין |

YOUR WORDS (9): לשון, חד-קרן, מחשב, שן, אצטדיון, כף, בייגלה, חיים, הרמון
OPPONENT (8): מחילה, גורד-שחקים, קזינו, חופה, מעגל, חוק, תפר, נמל
CIVILIAN (7): רוח-רפאים, עכבר, חריף, פרח, מיליונר, כפתור, לוויין
ASSASSIN (1): תל-אביב

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | אנשים | 2 | חיים, שן | מחילה [O] | hit_opponent |
| 2 | תפוחה | 3 | שן, לשון, חד-קרן | חד-קרן [T], מחשב [T] | stopped_early |
| 3 | אשת | 4 | לשון, שן, אצטדיון, כף | לשון [T], כפתור [-] | hit_civilian |
| 4 | אף | 1 | שן | אצטדיון [T], פרח [-] | hit_civilian |
| 5 | דם | 3 | שן, הרמון, בייגלה | כף [T] | stopped_early |
| 6 | חג | 2 | שן, בייגלה | חופה [O] | hit_opponent |
| 7 | עלי | 4 | שן, בייגלה, חיים, הרמון | גורד-שחקים [O] | hit_opponent |
| 8 | קפה | 2 | הרמון, שן | קזינו [O] | hit_opponent |
| 9 | אוגוסט | 2 | שן, חיים | לוויין [-] | hit_civilian |
| 10 | שיניים | 3 | חיים, הרמון, שן | שן [T], תפר [O] | hit_opponent |
| 11 | משפחה | 2 | חיים, הרמון | רוח-רפאים [-] | hit_civilian |
| 12 | טופ | 3 | בייגלה, חיים, הרמון | חיים [T] | stopped_early |
| 13 | עוגן | 2 | בייגלה, הרמון | נמל [O] | hit_opponent |
| 14 | בירה | 1 | בייגלה | חוק [O] | hit_opponent |
| 15 | טוסט | 2 | בייגלה, הרמון | בייגלה [T], מיליונר [-] | hit_civilian |
| 16 | רענן | 1 | הרמון | עכבר [-] | hit_civilian |
| 17 | פסילה | 1 | הרמון | חריף [-] | hit_civilian |
| 18 | מלחמה | 1 | הרמון | תל-אביב [X] | hit_assassin |

## clue אשפה → ציפורן

Round 11. No correct guess to anchor on; the first pick ended the game.

_Same game as above; see the transcript there._

## clue פרח → ציפורן

Round 8. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 4 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc free
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board dual_0 seed 4 trial 0 · count free · loss (assassin), 8 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T שבת | - גל | O חיות | O אש | T אביר |
| T צרפת | T זוהר | T שבתאי | X ציפורן | - חופה |
| - חתיכה | T כוס | O פרי | T כיפה | O כביש |
| O חוליה | O אפיקומן | - סוכה | - גמד | T טיל |
| T ציור | - מורה | O זהב | O דוב | - שוט |

YOUR WORDS (9): שבת, אביר, צרפת, זוהר, שבתאי, כוס, כיפה, טיל, ציור
OPPONENT (8): חיות, אש, פרי, כביש, חוליה, אפיקומן, זהב, דוב
CIVILIAN (7): גל, חופה, חתיכה, סוכה, גמד, מורה, שוט
ASSASSIN (1): ציפורן

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | כוכב | 3 | שבתאי, צרפת, אביר | שבת [T], שבתאי [T], זוהר [T] | stopped_early |
| 2 | מזגן | 3 | אביר, כוס, כיפה | מורה [-] | hit_civilian |
| 3 | בחירה | 3 | ציור, כוס, כיפה | פרי [O] | hit_opponent |
| 4 | הלילה | 3 | אביר, צרפת, כוס | דוב [O] | hit_opponent |
| 5 | יבוס | 2 | אביר, כוס | כוס [T] | stopped_early |
| 6 | עמוד | 1 | ציור | גל [-] | hit_civilian |
| 7 | ממרח | 5 | אביר, צרפת, כיפה, טיל, ציור | אש [O] | hit_opponent |
| 8 | פרח | 2 | אביר, ציור | ציפורן [X] | hit_assassin |

## clue חיים → מעיין

Round 3. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 8 --method strong \
    --cm gemini-2.5-flash --guesser gemini-2.5-flash --cc free
```

### google/gemini-2.5-flash (codemaster, strong_hebrew) vs google/gemini-2.5-flash (guesser) · board dual_0 seed 8 trial 0 · count free · loss (assassin), 3 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T אביר | T חמה | O שוקולד | O גאון | X מעיין |
| - אצטדיון | O תל-אביב | O מחשב | - לבוש | T בעל |
| T דג | T גורד-שחקים | O רולטה | T זוהר | O מוות |
| T פרח | - כפתור | T פרק | - בקבוק | - טבעת |
| - מאלף | T אייל | O אולימפוס | O באר-שבע | - צלחת |

YOUR WORDS (9): אביר, חמה, בעל, דג, גורד-שחקים, זוהר, פרח, פרק, אייל
OPPONENT (8): שוקולד, גאון, תל-אביב, מחשב, רולטה, מוות, אולימפוס, באר-שבע
CIVILIAN (7): אצטדיון, לבוש, כפתור, בקבוק, טבעת, מאלף, צלחת
ASSASSIN (1): מעיין

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | שמיים | 2 | גורד-שחקים, זוהר | אולימפוס [O] | hit_opponent |
| 2 | שמיים | 2 | זוהר, גורד-שחקים | גורד-שחקים [T], חמה [T] | stopped_early |
| 3 | חיים | 2 | פרח, דג | מעיין [X] | hit_assassin |

## clue טבע → מעיין

Round 3. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 8 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 8 trial 0 · count free · loss (assassin), 3 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| T אביר | T חמה | O שוקולד | O גאון | X מעיין |
| - אצטדיון | O תל-אביב | O מחשב | - לבוש | T בעל |
| T דג | T גורד-שחקים | O רולטה | T זוהר | O מוות |
| T פרח | - כפתור | T פרק | - בקבוק | - טבעת |
| - מאלף | T אייל | O אולימפוס | O באר-שבע | - צלחת |

YOUR WORDS (9): אביר, חמה, בעל, דג, גורד-שחקים, זוהר, פרח, פרק, אייל
OPPONENT (8): שוקולד, גאון, תל-אביב, מחשב, רולטה, מוות, אולימפוס, באר-שבע
CIVILIAN (7): אצטדיון, לבוש, כפתור, בקבוק, טבעת, מאלף, צלחת
ASSASSIN (1): מעיין

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | נוף | 2 | גורד-שחקים, אייל | גורד-שחקים [T], אצטדיון [-] | hit_civilian |
| 2 | נוף | 2 | אביר, אייל | תל-אביב [O] | hit_opponent |
| 3 | טבע | 2 | דג, זוהר | מעיין [X] | hit_assassin |

## clue מלט → עכביש

Round 16. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 6 --method strong \
    --cm qwen3.5-9b --guesser qwen3.5-9b --cc free
```

### qwen/qwen3.5-9b (codemaster, strong_hebrew) vs qwen/qwen3.5-9b (guesser) · board dual_0 seed 6 trial 0 · count free · loss (assassin), 16 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O זכוכית | - יער | - בית-ספר | X עכביש | O מלכה |
| T מסחרית | - רולטה | O פינגווין | O מחילה | - חליל |
| T סדר | T רצפה | O משטרה | T לבוש | - חיים |
| T מכונית | T הרמון | O נשימה | O דרקון | - מוסקבה |
| T ארץ | T חיות | T אולימפוס | O תל-אביב | - אמריקה |

YOUR WORDS (9): מסחרית, סדר, רצפה, לבוש, מכונית, הרמון, ארץ, חיות, אולימפוס
OPPONENT (8): זכוכית, מלכה, פינגווין, מחילה, משטרה, נשימה, דרקון, תל-אביב
CIVILIAN (7): יער, בית-ספר, רולטה, חליל, חיים, מוסקבה, אמריקה
ASSASSIN (1): עכביש

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | דגים | 2 | ארץ, מכונית | מסחרית [T] | stopped_early |
| 2 | תחבורה | 3 | מכונית, סדר, רצפה | מכונית [T], חליל [-] | hit_civilian |
| 3 | גבעה | 6 | סדר, רצפה, לבוש, ארץ, חיות, אולימפוס | ארץ [T] | stopped_early |
| 4 | גובה | 1 | רצפה | זכוכית [O] | hit_opponent |
| 5 | בליטה | 1 | הרמון | מחילה [O] | hit_opponent |
| 6 | רוח | 3 | סדר, רצפה, לבוש | נשימה [O] | hit_opponent |
| 7 | כדור | 3 | הרמון, חיות, אולימפוס | חיות [T], חיים [-] | hit_civilian |
| 8 | רוקד | 1 | סדר | לבוש [T] | stopped_early |
| 9 | פרח | 3 | סדר, רצפה, הרמון | הרמון [T], מלכה [O] | hit_opponent |
| 10 | דבש | 2 | סדר, רצפה | פינגווין [O] | hit_opponent |
| 11 | לוחמה | 2 | סדר, רצפה | משטרה [O] | hit_opponent |
| 12 | עובר | 2 | סדר, רצפה | תל-אביב [O] | hit_opponent |
| 13 | נקודות | 1 | סדר | אולימפוס [T] | stopped_early |
| 14 | כניסה | 1 | רצפה | בית-ספר [-] | hit_civilian |
| 15 | סקוטה | 2 | סדר, רצפה | רולטה [-] | hit_civilian |
| 16 | מלט | 1 | רצפה | עכביש [X] | hit_assassin |

## clue ארץ → תנועה

Round 12. No correct guess to anchor on; the first pick ended the game.

```
python scripts/show_game.py results/20260823T191234131145Z \
    --style dual_0 --seed 9 --method strong \
    --cm llama-3.3-70b-instruct --guesser llama-3.3-70b-instruct --cc free
```

### meta-llama/llama-3.3-70b-instruct (codemaster, strong_hebrew) vs meta-llama/llama-3.3-70b-instruct (guesser) · board dual_0 seed 9 trial 0 · count free · loss (assassin), 12 rounds · 20260823T191234131145Z

| | | | | |
|---|---|---|---|---|
| O ראש | - מזלג | O בקבוק | T גמד | T עיר |
| O מסלול | O דג | T קור | - קברן | T קנגורו |
| - קרצייה | O עץ | - שולחן | - אנגליה | T טעם |
| O ברמודה | T מקדש | - אגודל | O הלך | T תשובה |
| X תנועה | T מרכז | O בית-ספר | T אולימפוס | - כתר |

YOUR WORDS (9): גמד, עיר, קור, קנגורו, טעם, מקדש, תשובה, מרכז, אולימפוס
OPPONENT (8): ראש, בקבוק, מסלול, דג, עץ, ברמודה, הלך, בית-ספר
CIVILIAN (7): מזלג, קברן, קרצייה, שולחן, אנגליה, אגודל, כתר
ASSASSIN (1): תנועה

| r | clue | count | intended targets | guesses | turn |
|---|---|---|---|---|---|
| 1 | הר | 2 | מרכז, אולימפוס | הלך [O] | hit_opponent |
| 2 | הר | 2 | מרכז, אולימפוס | עיר [T], מרכז [T], ראש [O] | hit_opponent |
| 3 | הר | 2 | אולימפוס, מקדש | עץ [O] | hit_opponent |
| 4 | הר | 2 | אולימפוס, מקדש | אולימפוס [T], מקדש [T], קרצייה [-] | hit_civilian |
| 5 | ארץ | 1 | קנגורו | אנגליה [-] | hit_civilian |
| 6 | אוכל | 1 | טעם | מזלג [-] | hit_civilian |
| 7 | אוכל | 1 | טעם | בקבוק [O] | hit_opponent |
| 8 | ארץ | 2 | קנגורו, טעם | אגודל [-] | hit_civilian |
| 9 | אוכל | 1 | טעם | טעם [T], תשובה [T] | all_correct |
| 10 | קרח | 1 | קור | קור [T] | stopped_early |
| 11 | יער | 1 | קנגורו | גמד [T], מסלול [O] | hit_opponent |
| 12 | ארץ | 1 | קנגורו | תנועה [X] | hit_assassin |

