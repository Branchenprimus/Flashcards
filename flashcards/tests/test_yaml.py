import io
import yaml
import pytest

from app import validate_and_normalize_decks

def test_single_deck_valid():
    src = """
title: "T"
cards:
  - q: "Q1"
    a: "A1"
  - q: "Q2"
    a: "A2"
"""
    data = yaml.safe_load(io.StringIO(src))
    decks = validate_and_normalize_decks(data)
    assert len(decks) == 1
    assert decks[0]["title"] == "T"
    assert len(decks[0]["cards"]) == 2

def test_multi_decks_valid():
    src = """
decks:
  - title: "D1"
    cards:
      - q: "Q1"
        a: "A1"
  - title: "D2"
    cards:
      - q: "Q2"
        a: "A2"
"""
    data = yaml.safe_load(io.StringIO(src))
    decks = validate_and_normalize_decks(data)
    assert len(decks) == 2
    assert {d["title"] for d in decks} == {"D1", "D2"}

@pytest.mark.parametrize("bad_src, msg_part", [
    ("{}", "single deck"),
    ("title: ''\ncards:\n  - q: x\na: y\n", "non-empty 'title'"),
    ("title: T\ncards: []\n", "non-empty 'cards'"),
    ("title: T\ncards:\n  - q: ''\n    a: A\n", "empty or missing 'q'"),
    ("title: T\ncards:\n  - q: Q\n    a: ''\n", "empty or missing 'a'"),
    ("decks: []\n", "non-empty list"),
])
def test_invalid_inputs(bad_src, msg_part):
    data = yaml.safe_load(io.StringIO(bad_src))
    with pytest.raises(ValueError) as ei:
        validate_and_normalize_decks(data)
    assert msg_part in str(ei.value)
