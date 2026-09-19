# Documentation

**India-Based Smart Location-Based Renewable Energy Advisor.**

Architecture and API documentation lives in the root
[README.md](../README.md) as each phase adds to it — see
[Database Models](../README.md#database-models),
[API Endpoints](../README.md#api-endpoints),
[Location Intelligence](../README.md#location-intelligence-phase-3) (Phase
3's provider-agnostic geocoding/solar/wind/weather/elevation architecture,
using India-based resource data),
[India-Based Tariff & Incentive Architecture](../README.md#india-based-tariff--incentive-architecture)
(the DISCOM/tariff/incentive data model, and the incentive engine still
prepared-but-not-yet-built),
[Solar Engine (Phase 4)](../README.md#solar-engine-phase-4) (the
deterministic India-based solar generation and technical-feasibility
calculation — formulas, assumptions, units, and its explicit financial
boundary),
[Electricity Tariff Engine (Phase 5)](../README.md#electricity-tariff-engine-phase-5)
(the deterministic baseline grid-bill calculation — slab formula, DISCOM
scoping, charge-component honesty rules, and the per-state tariff-data
investigation record), and
[Incentive Engine (Phase 6)](../README.md#incentive-engine-phase-6) (the
deterministic renewable-energy incentive eligibility and calculation
engine — central/state/DISCOM separation, scheme versioning, stacking
rules, and the central/per-state incentive-data investigation record).

Real tariff and incentive data is documented in [`data-verification/`](data-verification/): the
[research log](data-verification/tariff-and-incentive-research.md) (every number traced to its official
document, page and table), the [coverage report](data-verification/coverage-report.md) and the generated
[data-quality report](data-verification/data-quality-report.md).

This folder is reserved for longer-form design documents (e.g. ADRs,
diagrams) if a future phase needs them separately from the README.
