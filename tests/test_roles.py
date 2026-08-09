from codenames_heb.roles import Codemaster, Guesser


class DummyCodemaster:
    def give_clue(self, board, required_count=None):
        return {"clue": "x", "count": 1, "intended_targets": [], "reasoning": ""}


class DummyGuesser:
    def guess(self, words, clue, count):
        return []


def test_dummy_codemaster_satisfies_protocol():
    assert isinstance(DummyCodemaster(), Codemaster)


def test_dummy_guesser_satisfies_protocol():
    assert isinstance(DummyGuesser(), Guesser)


def test_object_missing_give_clue_does_not_satisfy_codemaster_protocol():
    class NotACodemaster:
        pass

    assert not isinstance(NotACodemaster(), Codemaster)
