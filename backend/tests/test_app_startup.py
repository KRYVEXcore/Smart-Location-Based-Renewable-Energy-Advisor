from app.core.constants import PROJECT_NAME
from app.main import app


def test_app_imports_and_exposes_expected_routes() -> None:
    assert app.title == PROJECT_NAME

    # openapi() is FastAPI's stable public surface for the resolved route
    # table, unlike the internal shape of app.routes.
    paths = app.openapi()["paths"]
    assert "/api/v1/health" in paths
