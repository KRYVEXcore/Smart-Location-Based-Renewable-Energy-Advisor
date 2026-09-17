"""Versioning for the tariff calculation engine.

Unlike the Solar Engine, this engine has no derived physical assumptions to
version (see app.engines.solar.assumptions) — its only "assumption" is the
calculation logic itself (slab formula, version-selection rule, charge
inclusion rules), so a single engine version covers all of that.
"""

ENGINE_CALCULATION_VERSION = "tariff-engine-2026.1"
