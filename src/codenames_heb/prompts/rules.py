GAME_RULES = """Codenames is a word-based game of language understanding and communication.
Board: 25 Hebrew words. A hidden key assigns each word one of four roles:
TARGET (your words), OPPONENT, CIVILIAN, or ASSASSIN.
Standard distribution: 9 TARGET, 8 OPPONENT, 7 CIVILIAN, 1 ASSASSIN.
Only the Codemaster knows this key; the Guesser does not.

The Codemaster gives a clue: one Hebrew word plus a number. The clue must
be semantically related to the TARGET words it's meant for, must be a
single Hebrew word, and must not derive from, or be derived from, any
word on the board. The clue number must be >= 0.

The Guesser selects words one at a time based on which is most associated
with the clue; each selection's true role is revealed immediately. The
Guesser must guess at least once, and may guess up to one more than the
clue's number (e.g. a clue of 2 allows up to 3 guesses) — except when the
number is 0, where there is no limit. Guessing stops the moment a
non-TARGET word is selected, or the Guesser may stop voluntarily after
the first guess.

The team wins by finding all TARGET words; it loses immediately if the
Guesser ever selects the ASSASSIN word."""
