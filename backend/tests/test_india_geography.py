from app.core.india_geography import (
    INDIAN_STATES,
    INDIAN_UNION_TERRITORIES,
    is_union_territory,
    normalize_state_name,
)


def test_normalizes_exact_state_name():
    assert normalize_state_name("Tamil Nadu") == "Tamil Nadu"


def test_normalizes_case_insensitively():
    assert normalize_state_name("tamil nadu") == "Tamil Nadu"
    assert normalize_state_name("KARNATAKA") == "Karnataka"


def test_normalizes_known_aliases():
    assert normalize_state_name("Orissa") == "Odisha"
    assert normalize_state_name("Pondicherry") == "Puducherry"
    assert normalize_state_name("NCT of Delhi") == "Delhi"


def test_unknown_state_returns_none_rather_than_guessing():
    assert normalize_state_name("Narnia") is None
    assert normalize_state_name(None) is None
    assert normalize_state_name("") is None


def test_union_territories_are_flagged_correctly():
    assert is_union_territory("Delhi") is True
    assert is_union_territory("Puducherry") is True
    assert is_union_territory("Tamil Nadu") is False


def test_state_and_ut_lists_do_not_overlap():
    assert set(INDIAN_STATES).isdisjoint(set(INDIAN_UNION_TERRITORIES))


def test_state_and_ut_lists_have_no_duplicates():
    assert len(INDIAN_STATES) == len(set(INDIAN_STATES))
    assert len(INDIAN_UNION_TERRITORIES) == len(set(INDIAN_UNION_TERRITORIES))
