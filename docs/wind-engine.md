# Wind Engine (Phase 7) — India-based technical screening

> This is a preliminary software screening model, not a certified wind resource assessment or structural/site engineering assessment.

The engine estimates annual wind generation for six *candidate* turbine
capacities (0.5, 1, 2, 3, 5, 10 kW) at a location in India. It is **technical
screening only — structural/site approval is required.** It never produces a
recommendation, cost, subsidy, savings, or payback figure.

## Pipeline

```
Phase 3 LocationService.get_profile()  ->  WindResourceProfile (normalized)
        v
WindCalculationService  (app/services/wind_calculation_service.py)
        v
Wind engine  (app/engines/wind/ — pure functions, no FastAPI/DB/HTTP import)
        v
POST /api/v1/wind/calculate  ->  wind_calculation_snapshots (write-through)
```

The engine **never calls NASA POWER or any provider**; it only consumes the
Phase 3 profile. Provider, unit, period and retrieval time are carried through
to the response (`resource`).

## Resource

| Field            | Value                                                        |
| ---------------- | ------------------------------------------------------------ |
| Provider         | NASA POWER (via Phase 3), as recorded in the profile         |
| Period           | 2001-2020 monthly/annual climatology                         |
| Unit             | m/s                                                          |
| Heights in Phase 3 | 10 m (WS10M) and 50 m (WS50M)                              |
| Height used      | **10 m** (`RESOURCE_REFERENCE_HEIGHT_M`). The 50 m reading is shown but not used |

This is a regional model climatology, **not live weather** and not an
on-site measurement. There is no vertical extrapolation: a reading at another
height is never treated as 10 m (or the reverse), and hub height is not
modelled.

No US/European dataset, generic or national-average wind speed is used. If
no valid reading exists the API returns `wind_resource_unavailable` (or
`insufficient_data` if a reading exists but is unusable) — never a default
speed.

## Turbine model and power curve

A single generic reference turbine (`GENERIC_REFERENCE_TURBINE`) — a labelled
model assumption, not a manufacturer product and not a claim that such a
turbine is suitable for a home. Power is a fraction of rated capacity:

| Wind speed (m/s) | 0 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 25 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Fraction of rated | 0 | 0 | 0.0284 | 0.0752 | 0.1449 | 0.2423 | 0.3719 | 0.5383 | 0.7462 | 1 | 1 |

Cut-in 3 m/s, rated 11 m/s, cut-out 25 m/s. Output is 0 at or below cut-in and
above cut-out; between points it is linear interpolation of a cubic ramp
(deterministic, never extrapolated). The curve is validated on every use
(ascending speeds, starts at 0, fractions within 0..1 and non-decreasing,
cut-in < rated < cut-out).

## Methodology

Only mean wind speed is available, so a mean is never multiplied by
capacity. Instead the curve is integrated over a **Rayleigh distribution**
(Weibull, k = 2) whose scale is `mean / Γ(1 + 1/k)`, using 0.25 m/s bins.

- Monthly (when Phase 3 supplies all 12 months at 10 m):
  `kWh = capacity × mean_power_fraction × 24 × days × availability × electrical efficiency`
  using the same calendar day counts as the solar engine; annual = sum of months.
- Otherwise annual: `capacity × mean_power_fraction × 8760 × availability × efficiency`.
- Net capacity factor = annual / (capacity × 8760); equivalent full-load hours = annual / capacity.

## Assumptions (`wind-assumptions-2026.1`)

| Assumption | Value |
| --- | --- |
| Weibull shape k | 2.0 (Rayleigh) |
| Turbine availability | 0.95 |
| Electrical and other efficiency | 0.95 |
| Feasible: net CF at least | 0.15 |
| Marginal: net CF at least | 0.08 |

The feasibility thresholds are prototype **engineering assumptions, not
standards or regulations**. Status per candidate: `technically_feasible`,
`marginal`, `insufficient_resource`. Response-level status:
`ok`, `wind_resource_unavailable`, `location_unavailable`, `insufficient_data`.
Space is reported only as "Site-space information available" or "Site-space
requirement cannot yet be fully evaluated".

## Limitations

- Regional ~50 km-scale model value, not an anemometer measurement at the site.
- Urban and roof-level turbulence, obstacles and wake effects are not modelled
  and can materially reduce real output.
- 10 m only; hub height, air density and the real speed distribution are not modelled.
- Generic turbine; real turbines differ.
- Structural, foundation, height-restriction and permitting assessment is out of scope.
- No cost, subsidy, savings or payback (later phases).

## Tests

`test_wind_generation.py` (power curve, validation, an independent numerical
integral cross-check, determinism), `test_wind_engine.py` (statuses, resource
failures, heights, thresholds — test fixtures only, never in production code),
`test_wind_api.py` (API, validation, snapshot, cascade delete, five Indian
cities, regression checks for solar/tariff).
