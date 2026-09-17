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
boundary), and
[Electricity Tariff Engine (Phase 5)](../README.md#electricity-tariff-engine-phase-5)
(the deterministic baseline grid-bill calculation — slab formula, DISCOM
scoping, charge-component honesty rules, and the per-state tariff-data
investigation record).

This folder is reserved for longer-form design documents (e.g. ADRs,
diagrams) if a future phase needs them separately from the README.
