from sqlalchemy.engine import Engine

from app.database.connection import Base, SessionLocal, engine


def test_sqlalchemy_engine_initializes_from_settings() -> None:
    assert isinstance(engine, Engine)


def test_session_factory_is_bound_to_the_engine() -> None:
    session = SessionLocal()
    try:
        assert session.bind is engine
    finally:
        session.close()


def test_declarative_base_is_available_for_future_models() -> None:
    assert hasattr(Base, "metadata")
