# Hebrew wordpools

Local snapshots of the project spreadsheet so board construction does not
depend on a live Google Sheet.

Labels are the **second column** of both tabs, not “this file is the regular
tab.” Rebuild with `python scripts/rebuild_wordpools.py`.

| File | Role |
|---|---|
| `source_regular_tab.csv` | Spreadsheet tab “רגילות” (tagged `r` / `s` / `d`) |
| `source_dual_tab.csv` | Spreadsheet tab “כפל משמעות” (tagged `r` / `s` / `d`) |
| `regular.csv` | All words tagged `r` or `s` (both tabs; first occurrence wins) |
| `dual.csv` | All words tagged `d` (both tabs; first occurrence wins) |

`union` is not a file. `load_wordpool("union")` is regular first, then dual
(the two derived lists are disjoint).

Column: `מילה` (UTF-8). Keep Hebrew text exactly.

Source sheet: [Google Sheet](https://docs.google.com/spreadsheets/d/1npshOihxsJO9_40kI74IUexP3f9_wGJG9Kx7MTVJZco)

Embedding games do **not** edit these CSVs. For comparable boards across
Word2Vec and fastText, sample the **intersection** in-vocab subset at run
time (`--intersect-with`) and log a separate label.
