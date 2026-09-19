import pytest

from app.core.config import Settings


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("postgres://u:p@host:5432/db", "postgresql+psycopg2://u:p@host:5432/db"),
        ("postgresql://u:p@host:5432/db", "postgresql+psycopg2://u:p@host:5432/db"),
        ("postgresql+psycopg2://u:p@host:5432/db", "postgresql+psycopg2://u:p@host:5432/db"),
        ("sqlite:///./test.db", "sqlite:///./test.db"),
    ],
)
def test_database_url_is_normalised_to_psycopg2_driver(raw: str, expected: str) -> None:
    assert Settings(database_url=raw).database_url == expected
