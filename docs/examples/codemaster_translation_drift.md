# Translate-pipeline: the codemaster re-translates the board every round

Runs `20260823T191234131145Z` (M4) and `20260829T225350499567Z` (M5).
Each codemaster call is stateless — `build_translate_pipeline_prompt` rebuilds the
whole board and asks for a fresh `translation_map` — so the English gloss of a
Hebrew board word is re-drawn every round, with no memory of the previous one.

## 1. הודו: turkey → india, and the clue follows the flip

**הודו** — google/gemini-2.5-flash (cm) / google/gemini-2.5-flash (guesser) · board `dual_100` seed 10 · game win

translation by round: `{'3': 'turkey', '6': 'india'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 3 | חיה | animal | נחש, ביצה, הודו | snake, egg, Turkey | נחש (target), ביצה (target), אוגר (civilian) | hit_civilian |
| 6 | ארץ | country | בר, הודו | bar, India | הודו (target), בר (target) | all_correct |

## 2. הודו: same flip under gpt-4o-mini, ending on the assassin

**הודו** — openai/gpt-4o-mini (cm) / openai/gpt-4o-mini (guesser) · board `dual_100` seed 10 · game loss

translation by round: `{'3': 'turkey', '4': 'india'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 3 | נוצה | feather | בר, ביצה, הודו | bar, egg, turkey | נעל (target), בר (target), ביצה (target), צדק (civilian) | hit_civilian |
| 4 | מכתב | letter | הודו, עמוד, בול | India, post, stamp | משפט (assassin) | hit_assassin |

## 3. מלון: melon → hotel on consecutive rounds

**מלון** — google/gemini-2.5-flash (cm) / google/gemini-2.5-flash (guesser) · board `dual_100` seed 13 · game win

translation by round: `{'1': 'melon', '2': 'hotel'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 1 | פרי | fruit | תפוח, מלון | apple, melon | תפוח (target), גזר (civilian) | hit_civilian |
| 2 | נסיעה | travel | מלון, קניון, הודו | hotel, mall, India | מלון (target), בוקר (opponent) | hit_opponent |

## 4. קניון: canyon → mall

**קניון** — google/gemini-2.5-flash (cm) / meta-llama/llama-3.3-70b-instruct (guesser) · board `dual_100` seed 5 · game win

translation by round: `{'4': 'canyon', '8': 'mall'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 4 | הובלה | transport | מטען, קניון | cargo, canyon | מטען (target), מעבר (opponent) | hit_opponent |
| 8 | ביגוד | clothing | קניון, נעל | mall, shoe | נעל (target), קניון (target) | all_correct |

## 5. אלים: violent → gods

**אלים** — google/gemini-2.5-flash (cm) / google/gemini-2.5-flash (guesser) · board `dual_100` seed 27 · game loss

translation by round: `{'2': 'violent', '4': 'gods'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 2 | פיזי | Physical | אלים, אטום, מקל | violent, atom, stick | כבד (civilian) | hit_civilian |
| 4 | מיתולוגיה | mythology | אטום, אלים | atomic, gods | אלים (target), דוד (civilian) | hit_civilian |

## 6. אלים: gods → violent → hedged, five rounds on one target pair

**אלים** — google/gemini-2.5-flash (cm) / google/gemini-2.5-flash (guesser) · board `dual_100` seed 29 · game loss

translation by round: `{'8': 'gods', '9': 'gods', '10': 'violent', '11': 'violent', '12': 'violent', '13': 'violent/gods'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 8 | אלוהי | divine | פה, אלים | mouth, gods | אלה (opponent) | hit_opponent |
| 9 | אלוהי | divine | פה, אלים | mouth, gods | צדק (opponent) | hit_opponent |
| 10 | תקיפה | attack | פה, אלים | mouth, violent | מאבק (civilian) | hit_civilian |
| 11 | כוח | force | פה, אלים | mouth, violent | חבל (opponent) | hit_opponent |
| 12 | כוח | force | פה, אלים | mouth, violent | אופן (civilian) | hit_civilian |
| 13 | אלוהי | Divine | פה, אלים | mouth/here, violent/gods | אלים (target), חג (opponent) | hit_opponent |

## 7. מלח: salt → sailor, clue field moves with it

**מלח** — meta-llama/llama-3.3-70b-instruct (cm) / meta-llama/llama-3.3-70b-instruct (guesser) · board `dual_100` seed 19 · game loss

translation by round: `{'5': 'salt', '7': 'sailor', '8': 'sailor', '9': 'sailor', '10': 'sailor'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 5 | רעל | venom | קלע, נחש, מלח | archer, snake, salt | נחש (target), זריקה (opponent) | hit_opponent |
| 7 | חדר | room | קלע, מלח, אולם | archer, sailor, hall | אולם (target), בוקר (civilian) | hit_civilian |
| 8 | ימי | marine | קלע, מלח | archer, sailor | חגים (opponent) | hit_opponent |
| 9 | ימי | marine | קלע, מלח | archer, sailor | שר (opponent) | hit_opponent |
| 10 | ים | sea | קלע, מלח | archer, sailor | מלח (target), כסף (civilian) | hit_civilian |

## 8. מטר: rain ↔ meter oscillating across five rounds

**מטר** — google/gemini-2.5-flash (cm) / openai/gpt-4o-mini (guesser) · board `dual_100` seed 117 · game loss

translation by round: `{'4': 'rain', '5': 'rain', '6': 'meter/rain', '7': 'meter', '8': 'rain/meter'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 4 | פתוח | open | בר, מטר, מפתח | bar, rain, key | מפתח (target), מפה (opponent) | hit_opponent |
| 5 | דרך | road | מטר, נהג | rain, driver | מוצא (opponent) | hit_opponent |
| 6 | דרך | path | בר, מטר, נהג | bar/son/grain, rain, driver | נהג (target), חלק (opponent) | hit_opponent |
| 7 | מידה | measure | בר, מטר | bar, meter | צדק (opponent) | hit_opponent |
| 8 | קציר | harvest | מטר, בר | rain, bar/grain | חגים (assassin) | hit_assassin |

## 9. פה: mouth → here, clue field moves with it

**פה** — openai/gpt-4o-mini (cm) / openai/gpt-4o-mini (guesser) · board `dual_100` seed 19 · game loss

translation by round: `{'3': 'mouth', '4': 'mouth', '5': 'mouth', '6': 'here', '7': 'mouth'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 3 | עוד | extra | פה, מגדל, אחר, אולם, נהג | mouth, tower, other, hall, driver | חגים (opponent) | hit_opponent |
| 4 | לדבר | speak | פה, מגדל | mouth, tower | שפה (civilian) | hit_civilian |
| 5 | צליל | sound | פה, מגדל, נהג | mouth, tower, driver | קצב (opponent) | hit_opponent |
| 6 | מקום | place | פה, מגדל, אחר | here, tower, other | מלון (civilian) | hit_civilian |
| 7 | דיבור | speech | פה, מגדל, אחר | פה, מגדל, אחר | פה (target), שר (opponent) | hit_opponent |

## 10. אלה: goddess → these → those

**אלה** — openai/gpt-4o-mini (cm) / openai/gpt-4o-mini (guesser) · board `natural` seed 19 · game win

translation by round: `{'5': 'goddess', '6': 'these', '7': 'these', '8': 'those'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 5 | קסם | magic | אשף, לבוש, אלה | wizard, clothing, goddess | אשף (target), טייס (opponent) | hit_opponent |
| 6 | ביגוד | apparel | לבוש, אלה | clothing, these | לבוש (target), סיכה (opponent) | hit_opponent |
| 7 | קבוצה | Group | אלה | These, Sister, Fish, Warrior, Land, Beach, Miracle, Wizard, Pirate | לוחם (civilian) | hit_civilian |
| 8 | עצים | trees | אלה | those | אלה (target) | all_correct |

## 11. מטה: staff → staff/bed → headquarters

**מטה** — google/gemini-2.5-flash (cm) / google/gemini-2.5-flash (guesser) · board `dual_100` seed 6 · game win

translation by round: `{'3': 'staff', '4': 'staff/bed', '6': 'staff', '7': 'headquarters'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 3 | מקל | stick | סרט, מטה | film, staff | קש (civilian) | hit_civilian |
| 4 | רצועה | strip | סרט, מטה | film/ribbon, staff/bed | סרט (target), מצרים (opponent) | hit_opponent |
| 6 | גוף | body | מטה, עצם | staff, bone | עצם (target), חפץ (civilian) | hit_civilian |
| 7 | משרד | office | מטה | headquarters | מטה (target) | all_correct |

## 12. תור: queue ↔ turn, seven rounds, clue "סדר" reused on both senses

**תור** — openai/gpt-4o-mini (cm) / openai/gpt-4o-mini (guesser) · board `dual_0` seed 22 · game loss

translation by round: `{'1': 'queue', '2': 'queue', '3': 'queue', '5': 'turn', '6': 'queue', '7': 'turn', '8': 'turn'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 1 | סדר | order | טבע, תור, כפתור | nature, queue, button | מיון (target), דרך (civilian) | hit_civilian |
| 2 | סדר | order | תור, חיבור, ראש | nature, queue, connection | מסלול (opponent) | hit_opponent |
| 3 | יבשת | continent | אפריקה, טבע, תור, חיבור, ראש | nature, queue, connection, head, Africa | אפריקה (target), ים (civilian) | hit_civilian |
| 5 | קישור | link | תור, חיבור, ראש | turn, connection, head | חיבור (target), יום (opponent) | hit_opponent |
| 6 | סדר | order | תור, ראש | queue, head | זמן (civilian) | hit_civilian |
| 7 | גלגל | wheel | תור, ראש, אשפה | turn, head, trash | פעמון (opponent) | hit_opponent |
| 8 | שליטה | control | תור, ראש, כפתור | turn, head, button | ראש (target), תור (target), רופא (opponent) | hit_opponent |

## 13. אוגר: hamster → gerbil

**אוגר** — openai/gpt-4o-mini (cm) / openai/gpt-4o-mini (guesser) · board `dual_100` seed 12 · game loss

translation by round: `{'1': 'hamster', '2': 'hamster', '3': 'gerbil'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 1 | מכניקה | mechanics | מנוע, אוגר, בסיס | engine, hamster, base | מנוע (target), קצב (target), מאבק (civilian) | hit_civilian |
| 2 | מלאכה | craft | אוגר, בסיס, מעמד, מקל, חצב | hamster, hall, base, stand, stick, chisel | אמן (target), מעמד (target), בר (civilian) | hit_civilian |
| 3 | חיה | pet | אוגר, אולם, בסיס, מקל, חצב | gerbil, hall, base, stick, bulb | אוגר (target), גזר (opponent) | hit_opponent |

## 14. כבד: heart → liver → heavy → kidney (qwen)

**כבד** — qwen/qwen3.5-9b (cm) / qwen/qwen3.5-9b (guesser) · board `dual_100` seed 15 · game win

translation by round: `{'4': 'liver', '10': 'heart', '17': 'liver', '19': 'kidney', '20': 'heavy'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 4 | גוף | body | ספר, משפט, רב, כבד, רכב | book, sentence, rabbi, liver, car | גזר (opponent) | hit_opponent |
| 10 | אהבה | Love | אלה, כבד | God, Heart | פנים (civilian) | hit_civilian |
| 17 | כולל | include | כבד, אלה | כבד, אלה | מעבר (civilian) | hit_civilian |
| 19 | עונה | season | אלה, כבד | אלה, כבד | עמוד (opponent) | hit_opponent |
| 20 | צפוף | dense | כבד | כבד | כבד (target) | stopped_early |

## 15. זריקה: shot → throw

**זריקה** — google/gemini-2.5-flash (cm) / google/gemini-2.5-flash (guesser) · board `natural` seed 5 · game win

translation by round: `{'3': 'shot', '6': 'throw', '7': 'throw', '9': 'throw'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 3 | זר | foreign | חייזר, זריקה, אירופה | alien, shot, europe | חייזר (target), קפה (civilian) | hit_civilian |
| 6 | פעולה | action | זריקה, חצב | throw, carved | קוד (opponent) | hit_opponent |
| 7 | פעולה | action | זריקה, חצב | throw, carve | מסע (civilian) | hit_civilian |
| 9 | שיגור | launch | זריקה, חצב | throw, squill | זריקה (target), קלע (civilian) | hit_civilian |

## 16. בר: wild → son → bar

**בר** — google/gemini-2.5-flash (cm) / google/gemini-2.5-flash (guesser) · board `natural` seed 16 · game win

translation by round: `{'4': 'wild/son/bar', '5': 'wild', '6': 'son', '8': 'bar/wild/son'}`

| r | clue (he) | en_clue | intended targets | en_targets | guesses | turn |
|---|---|---|---|---|---|---|
| 4 | טבע | nature | פרח, בר | flower, wild | אורגני (opponent) | hit_opponent |
| 5 | טבע | nature | פרח, בר | flower, wild | פרח (target), קרן (civilian) | hit_civilian |
| 6 | נוער | youth | חשבון, בר, צופים | account, son, scouts | צופים (target), מקל (opponent) | hit_opponent |
| 8 | פרא | wild | בר | bar/wild/son | בר (target) | all_correct |


---

## Across games and boards: the default sense is model-specific

Share of all rounds in which each model glossed the word each way (top 3 senses;
`a/b` means the model hedged both senses in one string).

| word | qwen3.5-9b | gemini-2.5-flash | gpt-4o-mini | llama-3.3-70b-instruct |
|---|---|---|---|---|
| הודו | **45** distinct: india 80%, turkey 6%, thank 4% | **28** distinct: india 71%, india/thanked 9%, turkey 6% | **3** distinct: india 94%, turkey 6%, thanksgiving 0% | **6** distinct: india 94%, turkey 5%, thanks 1% |
| כבד | **37** distinct: liver 66%, heavy 20%, liver/heavy 4% | **10** distinct: heavy 53%, heavy/liver 36%, liver 7% | **2** distinct: heavy 73%, liver 27% | **2** distinct: liver 96%, heavy 4% |
| קניון | **18** distinct: mall 95%, shopping mall 1%, canyon 0% | **7** distinct: mall 64%, mall/canyon 22%, canyon 8% | **3** distinct: mall 65%, canyon 35%, shopping mall 0% | **2** distinct: canyon 55%, mall 45% |
| אלים | **41** distinct: gods 80%, deities 3%, violent 2% | **8** distinct: violent 72%, gods 19%, violent/gods 6% | **9** distinct: gods 53%, violent 44%, deities 1% | **11** distinct: gods 90%, ruthless 5%, ruler 2% |
| מלון | **9** distinct: hotel 98%, 旅館 0%, hotel/five_men 0% | **5** distinct: hotel 86%, hotel/melon 9%, melon 3% | **3** distinct: hotel 96%, melon 4%, source 0% | **1** distinct: hotel 100% |
| מלח | **10** distinct: salt 98%, sea 0%, salt/seashore 0% | **5** distinct: salt 89%, sailor 7%, salt/sailor 2% | **5** distinct: salt 98%, war 1%, sailor 0% | **2** distinct: salt 99%, sailor 1% |
| אלה | **182** distinct: goddess 10%, these 9%, that 8% | **27** distinct: goddess 59%, these 16%, goddess/club 8% | **29** distinct: these 72%, goddess 20%, those 2% | **5** distinct: these 74%, goddess 25%, pine 1% |
| פה | **36** distinct: mouth 70%, here 22%, face 2% | **6** distinct: mouth 84%, mouth/here 15%, here/mouth 1% | **2** distinct: mouth 95%, here 5% | **2** distinct: mouth 81%, here 19% |
| תור | **59** distinct: turn 54%, shift 12%, queue 10% | **20** distinct: turn 49%, turn/queue 19%, queue 16% | **19** distinct: queue 53%, line 23%, turn 18% | **14** distinct: turn 55%, queue 16%, tour 10% |
| סרט | **27** distinct: film 51%, movie 33%, tape 6% | **20** distinct: ribbon 28%, film 26%, film/ribbon 17% | **5** distinct: movie 59%, film 36%, ribbon 3% | **2** distinct: movie 77%, film 23% |
| קל | **37** distinct: light 75%, easy 17%, light/easy 1% | **6** distinct: easy 74%, easy/light 21%, light 2% | **2** distinct: easy 78%, light 22% | **2** distinct: light 93%, easy 7% |
| מטר | **21** distinct: meter 94%, metre 1%, meter/rain 1% | **13** distinct: meter 70%, meter/rain 25%, rain 2% | **4** distinct: meter 97%, goal 2%, target 0% | **8** distinct: rain 81%, target 18%, meter 0% |
| אוגר | **343** distinct: ogre 15%, squirrel 5%, saver 5% | **10** distinct: hamster 80%, hamster/hoarder 20%, hamster / hoarder 0% | **18** distinct: hamster 68%, gerbil 23%, guinea pig 6% | **31** distinct: store 67%, treasurer 19%, hog 5% |
| בר | **46** distinct: bar 85%, gate 1%, barrier 1% | **71** distinct: son 27%, bar 24%, wild 12% | **7** distinct: bar 97%, wild 1%, son 1% | **7** distinct: son 48%, bar 42%, pure 4% |
| חצב | **269** distinct: reeds 10%, reed 7%, thistle 3% | **79** distinct: squill 26%, carved 16%, carve 11% | **61** distinct: bulb 78%, chisel 5%, bulbul 3% | **14** distinct: quarry 81%, carve 6%, dig 6% |
| אפיקומן | **124** distinct: epicurean 13%, waiter 6%, epicure 3% | **6** distinct: afikoman 99%, afikoman (matzah) 0%, afikoman (opponent) 0% | **5** distinct: afikoman 83%, afikomen 16%, aphikoman 0% | **7** distinct: afikoman 90%, afikomen 5%, aphikomen 2% |

### Widest disagreement, all models pooled

| word | rounds | distinct glosses | top glosses |
|---|---|---|---|
| חצב | 4177 | 394 | bulb (1060), quarry (934), squill (355), carved (226), carve (209) |
| אוגר | 6466 | 377 | hamster (2914), store (1094), gerbil (454), hamster/hoarder (387), treasurer (315) |
| קרצייה | 2564 | 319 | tick (1654), crustacean (175), crust (76), crayon (35), crayfish (30) |
| אוזן-המן | 2092 | 255 | hamantaschen (674), hamantashen (187), earphone (166), haman's ear (148), hamantash (115) |
| אלה | 5804 | 223 | these (2801), goddess (1984), goddess/club (153), these/goddess (134), goddess/these (68) |
| אסר | 2869 | 193 | forbid (691), forbade (676), prison (445), prisoner (263), prohibit (196) |
| גר | 2515 | 190 | live (644), lives (497), alien (173), resident (167), sojourn (129) |
| מרוצים | 4094 | 185 | races (1785), satisfied (1052), racing (326), satisfied/races (230), happy (219) |
| מטה | 4689 | 185 | staff (3669), headquarters (90), wand (78), staff/bed (72), rod (58) |
| קלע | 2735 | 143 | slingshot (844), archer (408), sling (329), shooter (229), slingshot/shooter (221) |
| אפיקומן | 1928 | 136 | afikoman (1563), afikomen (130), epicurean (26), waiter (12), aphikomen (9) |
| תת | 2178 | 121 | sub (1170), under (322), bottom (152), breast (84), teat (77) |
| בר | 3684 | 121 | bar (2126), son (785), wild (172), wild/son/bar (49), son/wild/pure/grain (44) |
| סילון | 2064 | 113 | jet (1779), cyclone (27), beam (18), gale (16), jet stream (15) |
| לבנה | 3449 | 111 | brick (1819), moon (695), white (495), brick/moon (183), brick/white (35) |
| כדור-עף | 2657 | 106 | volleyball (2346), ball (49), satellite (33), frisbee (18), rocket (14) |
| אלף | 4908 | 101 | thousand (3950), ox (233), thousand/ox (224), aleph (98), thousand/aleph (53) |
| שוט | 2561 | 100 | whip (1964), baton (105), stick (82), shot (49), oar (48) |
| פרסה | 1895 | 100 | hoof (997), horseshoe (571), horseshoe/hoof (63), fin (60), mare (27) |
| תור | 2489 | 94 | turn (1038), queue (661), line (182), turn/queue (148), tour (72) |
| שרת | 2937 | 82 | server (1973), minister (229), serve (212), served (126), minister/server (74) |
| שר | 3858 | 81 | minister (3306), minister/sing (117), minister/sang (63), singer (39), sang (36) |
| חבל | 3595 | 77 | rope (3197), rope/region (130), rope/region/pity (118), cord (21), rope/harm (16) |
| מדליק | 1919 | 74 | cool (764), igniter (338), lighting (145), lighter (130), cool/lights up (113) |
| מעמד | 4341 | 74 | status (3505), status/stand (344), stand (240), platform (42), position (27) |

---

## Root-echo clues: the validator only catches exact matches

`clue_on_board` rejects a clue identical to a board word. It does not catch a clue
that is a *morphological variant* of one — and Hebrew makes those cheap to produce.
A clue that shares a stem with its own target is a free point taken by breaking the
spirit of the rule, and the guesser takes the bait almost every time.

2,857 of 85,495 clues (3.3%) are a literal substring or superstring of some word on
their own board. Where that word is one of the intended targets, the guesser picks it
in 56–79% of turns.

| codemaster / method | clues | root-echo | echoes a target | guesser took it |
|---|---|---|---|---|
| llama-3.3-70b-instruct / `strong_hebrew` | 8001 | 6.7% | 3.4% | 56.1% |
| gpt-4o-mini / `strong_hebrew` | 13963 | 4.6% | 3.6% | 78.9% |
| gemini-2.5-flash / `strong_hebrew` | 12975 | 3.3% | 2.2% | 68.9% |
| gpt-4o-mini / `translate_pipeline` | 13099 | 2.9% | 1.6% | 64.8% |
| llama-3.3-70b-instruct / `translate_pipeline` | 8031 | 2.7% | 1.8% | 69.4% |
| gemini-2.5-flash / `translate_pipeline` | 12495 | 2.5% | 1.4% | 61.7% |
| qwen3.5-9b / `translate_pipeline` | 8221 | 2.3% | 1.2% | 63.7% |
| qwen3.5-9b / `strong_hebrew` | 8710 | 1.7% | 0.8% | 55.9% |

**The rate splits by method.** Going through English roughly halves it for three
of the four models — llama 6.7% → 2.7%, gpt-4o-mini 4.6% → 2.9%, gemini 3.3% → 2.5%
(qwen is the exception, 1.7% → 2.3%). Choosing the clue in English and translating it
back breaks the surface-form attraction that pulls a Hebrew-native codemaster toward a
variant of a word already on the board. That is a concrete mechanism for the
translate advantage, distinct from general English competence.

### Examples

| clue | echoed target | codemaster | method | board | guesses |
|---|---|---|---|---|---|
| **מזלטוב** | מזל | llama-3.3-70b-instruct | `strong_hebrew` | dual_0 s1 | מזל (target), אשפה (target) |
| **קרן** | חד-קרן | llama-3.3-70b-instruct | `strong_hebrew` | dual_0 s2 | חד-קרן (target), כף (target) |
| **אבירות** | אביר | llama-3.3-70b-instruct | `strong_hebrew` | dual_0 s4 | אביר (target), אפיקומן (opponent) |
| **מרכזי** | מרכז | gpt-4o-mini | `strong_hebrew` | dual_0 s9 | מרכז (target), תנועה (assassin) |
| **משחקיה** | משחק | gemini-2.5-flash | `strong_hebrew` | dual_0 s11 | משחק (target), כדור (opponent) |
| **משחקים** | משחק | llama-3.3-70b-instruct | `strong_hebrew` | dual_0 s11 | משחק (target), כדור (opponent) |
| **תנוע** | תנועה | llama-3.3-70b-instruct | `strong_hebrew` | dual_0 s27 | תנועה (target), ריקוד (opponent) |
| **חללי** | חלל | llama-3.3-70b-instruct | `strong_hebrew` | dual_0 s27 | חלל (target), עכבר (opponent) |
| **נמלול** | נמל | gemini-2.5-flash | `strong_hebrew` | dual_0 s29 | נמל (target) |
| **קירות** | קיר | gpt-4o-mini | `strong_hebrew` | natural s4 | קיר (target) |
| **רוח** | רוח-רפאים | gemini-2.5-flash | `strong_hebrew` | natural s6 | רוח-רפאים (target) |
| **רפאים** | רוח-רפאים | gpt-4o-mini | `strong_hebrew` | natural s6 | רוח-רפאים (target), קברן (civilian) |
| **מקורות** | מקור | gpt-4o-mini | `strong_hebrew` | natural s6 | מקור (target) |
| **אורות** | אור | llama-3.3-70b-instruct | `strong_hebrew` | natural s7 | אור (target), אופרה (civilian) |
