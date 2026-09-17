"""Versioning for the incentive eligibility/calculation engine.

Like the Tariff Engine, this has no derived physical assumptions to
version — its "assumption" is the eligibility/calculation logic itself, so
a single engine version covers all of that. This is independent of
`IncentiveProgram.scheme_version`, which versions the underlying
government scheme data, not this engine's code.
"""

ENGINE_CALCULATION_VERSION = "incentive-engine-2026.1"
