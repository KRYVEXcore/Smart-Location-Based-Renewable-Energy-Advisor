"""Validation for the seed data in backend/app/data/. Pure functions and
Pydantic models only: no database access, so the same checks run in the
seed scripts, the data-quality report and the test-suite.
"""
