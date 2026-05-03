import pytest

from chatbot.tools.obfuscate import MAP_OF_TERMS, replace_terms_in_text


@pytest.fixture
def tiny_map() -> dict[str, str]:
    return {
        "Black Circle": "Yellow Square",
        "Black Road": "Dark Highway",
        "Black": "Z",
        "Brand": "Jon",
        "Amber": "Yander",
        "Eric": "Kripke",
        "Corwin": "Pavel",
        "Avalon": "Azaron",
    }


def test_not_inside_longer_word(tiny_map: dict[str, str]) -> None:
    assert replace_terms_in_text("Brandon walked", tiny_map) == "Brandon walked"
    assert replace_terms_in_text("preOrder state", tiny_map) == "preOrder state"


def test_case_sensitive(tiny_map: dict[str, str]) -> None:
    assert replace_terms_in_text("amber glow", tiny_map) == "amber glow"
    assert replace_terms_in_text("Amber glow", tiny_map) == "Yander glow"


def test_punctuation_preserved_after_term(tiny_map: dict[str, str]) -> None:
    assert replace_terms_in_text("Hi, Amber!", tiny_map) == "Hi, Yander!"
    assert replace_terms_in_text("Amber, yes.", tiny_map) == "Yander, yes."
    assert replace_terms_in_text("Eric's dungeon", tiny_map) == "Kripke's dungeon"
    assert replace_terms_in_text("Corwin's son", tiny_map) == "Pavel's son"


def test_whole_words_only_spaces_and_quotes(tiny_map: dict[str, str]) -> None:
    assert replace_terms_in_text('title="Eric" ok', tiny_map) == 'title="Kripke" ok'
    assert replace_terms_in_text("Meet Brand tonight.", tiny_map) == "Meet Jon tonight."


def test_multiword_terms_longest_first(tiny_map: dict[str, str]) -> None:
    assert (
        replace_terms_in_text("The Black Circle met", tiny_map)
        == "The Yellow Square met"
    )
    assert (
        replace_terms_in_text("The Black Road met", tiny_map) == "The Dark Highway met"
    )
    assert replace_terms_in_text("A Black hole", tiny_map) == "A Z hole"


def test_underscore_separators_like_wiki_slug(tiny_map: dict[str, str]) -> None:
    """'_' не считается частью имени — подстрочко «Amber» в slug заменяется."""
    assert (
        replace_terms_in_text("Chronicles_of_Amber.json", tiny_map)
        == "Chronicles_of_Yander.json"
    )


def test_hyphen_apostrophe_term_from_real_map() -> None:
    m = dict(MAP_OF_TERMS)
    assert "Notr Na'th" in replace_terms_in_text("Seen in Tir-na Nog'th once.", m)


def test_ty_iga_boundary() -> None:
    m = dict(MAP_OF_TERMS)
    assert replace_terms_in_text("About Ty'iga here.", m) == "About Tigana here."


def test_plural_replacement() -> None:
    m = dict(MAP_OF_TERMS)
    assert (
        replace_terms_in_text("in the shadow Avalons his name", m)
        == "in the shadow Azarons his name"
    )


def test_possessive_case_replacement() -> None:
    m = dict(MAP_OF_TERMS)
    assert replace_terms_in_text("Brand's son", m) == "Jon's son"
