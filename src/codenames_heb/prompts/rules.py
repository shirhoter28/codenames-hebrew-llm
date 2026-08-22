GAME_RULES = """Codenames is a word-based game of language understanding and communication.
Board: 25 Hebrew words. A hidden key assigns each word one of four roles:
TARGET (your words), OPPONENT, CIVILIAN, or ASSASSIN.
Standard distribution: 9 TARGET, 8 OPPONENT, 7 CIVILIAN, 1 ASSASSIN.
Only the Codemaster knows this key; the Guesser does not.

The Codemaster gives a clue: one Hebrew word plus a number. The clue must
be semantically related to the TARGET words it's meant for, must be a
single Hebrew word, and must not derive from any
word on the board, and any word on the board must not derive from the clue.
The clue number must be >= 0 and must equal exactly the number of words the
Codemaster names as its intended targets for that clue — no more, no fewer.

The Guesser selects words one at a time. Each guess is submitted
individually and its true role is revealed immediately, to both players,
before the next guess is made. The Guesser must guess at least once. After
a correct (TARGET) guess, the Guesser may choose to guess again — up to one
more guess than the clue's number in total (e.g. a clue of 2 allows up to 3
guesses; a clue of 0 means no limit) — or may stop voluntarily. Guessing
stops immediately, without a choice, the moment a non-TARGET word is
selected.

Play proceeds in rounds: the Codemaster gives a clue, the Guesser guesses
against it as above, then the Codemaster gives the next clue against the
updated board. Revealed words (and their true role) stay visible to both
players for the rest of the game; only never-guessed words remain hidden.

The team wins by finding all TARGET words. It loses immediately if the
Guesser ever selects the ASSASSIN word. Every OPPONENT word the Guesser
selects is handed to the opposing team, so the team also loses if all
OPPONENT words end up revealed — at that point the opposing team has all
of its words and wins."""
