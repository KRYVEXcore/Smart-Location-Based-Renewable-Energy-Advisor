# India incentive seed data

This directory is where genuinely verified official renewable-energy
incentive programmes are checked in, one JSON file per scheme version,
loaded into `incentive_programs` by
[`backend/scripts/seed_incentives.py`](../../../../scripts/seed_incentives.py).
It intentionally contains **no real incentive data yet** — see the
investigation record below.

## Directory layout

```
backend/app/data/incentives/india/
    central/            Central Government schemes (e.g. PM Surya Ghar)
    states/
        tamil_nadu/
        maharashtra/
        karnataka/
        kerala/
        rajasthan/
    discom/              DISCOM-specific schemes, one subfolder per DISCOM
```

Only the subfolders that actually hold a verified scheme file should
exist — an empty state folder is not created "for completeness"; see
[No false national coverage claim](#no-false-national-coverage-claim) below.

## File format

One file per scheme *version*, at
`<central|states/<state-slug>|discom/<discom-slug>>/<scheme_version>.json`:

```json
{
  "scheme_name": "EXAMPLE Central Rooftop Solar Scheme",
  "scheme_version": "EXAMPLE-CENTRAL-2026.1",
  "description": "One paragraph, plain language.",
  "level": "central",
  "incentive_type": "central_financial_assistance",
  "state": null,
  "union_territory": null,
  "discom_short_code": null,
  "consumer_category": "residential",
  "technology": "solar",
  "min_system_size_kw": null,
  "max_system_size_kw": 3,
  "subsidy_type": "slab_based",
  "subsidy_value": null,
  "percentage_value": null,
  "maximum_amount": 78000,
  "calculation_rules": {
    "slabs": [
      { "capacity_min_kw": 0, "capacity_max_kw": 2, "rate_inr_per_kw": 0 },
      { "capacity_min_kw": 2, "capacity_max_kw": 3, "rate_inr_per_kw": 0 }
    ]
  },
  "eligibility_rules": { "requires_fields": [] },
  "application_requirements": null,
  "stacking_rules": { "combinable_with_levels": ["state", "discom"] },
  "effective_from": "2026-01-01",
  "effective_to": null,
  "verification_status": "verified",
  "source_name": "EXAMPLE Ministry / Agency",
  "source_url": "https://example.invalid/official-guideline",
  "source_document": "EXAMPLE Guideline No. 0 of 2026",
  "last_verified": "2026-01-01",
  "active": true
}
```

`discom_short_code` resolves against the existing `discoms` table (`null`
for central/state-wide schemes). `subsidy_type` selects which of
`subsidy_value` / `percentage_value` / `calculation_rules` the engine
reads — see
[`app/engines/incentive/calculator.py`](../../../engines/incentive/calculator.py)
for the exact schema each type expects.
[`schema_example.json`](schema_example.json) carries this same shape with
an explanatory `_comment` and is never loaded by the seed script (it only
scans `central/*.json`, `states/<slug>/*.json`, and `discom/<slug>/*.json`).

## Why no cost-basis (percentage / benchmark-cost) scheme can be fully calculated today

This application does not collect a verified installation cost anywhere —
`BuildingConstraints.budget_inr` is the user's own aspirational budget, not
a vendor quotation, and no later phase has added one yet. A `percentage`
or `benchmark_cost_based` scheme is therefore always reported
`insufficient_information` by the engine, honestly, rather than computed
against an invented cost. `fixed_amount`, `per_kw`, and `slab_based`
schemes (which depend only on capacity) can be calculated in full.

## Investigation record (Phase 6)

Per this project's explicit rule — **prefer NO DATA over FAKE DATA** — a
scheme is only seeded here once its exact rates, capacity limits, and
conditions have been confirmed by reading an actual official source (MNRE,
a state renewable-energy nodal agency, a state government department, or
an official gazette/notification/circular). A commercial solar-installer
site, EPC blog, or aggregator is never treated as the authoritative
source, even when it is useful for locating the real one.

### Central

**PM Surya Ghar: Muft Bijli Yojana** (Central Sector Scheme, MNRE) —
**not seeded; unconfigured.** Official sources were located: a PIB
(Press Information Bureau) press release announcing Cabinet approval, an
official MNRE guidelines PDF hosted on the government's own CDN
(`cdnbbsr.s3waas.gov.in`), the MNRE "Grid Connected Rooftop Solar
Programme" page, and the `pmsuryaghar.gov.in` national portal itself. None
could be read as extractable, confidently-quotable text with the tooling
available in this phase: the PIB page returned an HTTP 403, the MNRE
guidelines PDF is image/font-encoded rather than text-extractable, the
MNRE programme page only links out to the same unreadable PDFs for its
actual CFA figures, and the national portal is a JavaScript-rendered
application whose static HTML carries no content. Multiple secondary
sources (commercial solar-EPC and calculator sites) consistently describe
a ₹30,000/kW rate for the first 2 kW and ₹18,000/kW for the third kW,
capped at ₹78,000 for systems ≥3 kW, residential-only — this is plausible
and worth using as a starting point for manual verification, but it was
not read directly from the primary document in this session and is
therefore not stored as authoritative data here.

### States

Five states were investigated, as required. **None have a verified
programme configured:**

| State | What was found | Why not seeded |
|---|---|---|
| Tamil Nadu | TEDA's prior state-level rooftop solar subsidy (offered ~2022) is confirmed **defunct** — TEDA merged into the Tamil Nadu Green Energy Corporation in 2024. A **new** state scheme was reported as announced in the state's Revised Budget 2026-27 (5 August 2026, ₹50 crore allocated), in convergence with PM Surya Ghar | The new scheme is too recent for an official notification/government-order document to have been located and read in this phase — exactly the "don't assume an old scheme is still current, and don't assume a just-announced one is fully specified yet" case this project's rules anticipate |
| Maharashtra | MEDA (Maharashtra Energy Development Agency) administers a state top-up alongside the central CFA; a Generation-Based Incentive for exported units is also mentioned | Only found via commercial blog sources describing MEDA's programme, not a direct read of a MEDA/state government notification |
| Karnataka | KREDL (Karnataka Renewable Energy Development Ltd) is the nodal agency; a state top-up subsidy is mentioned | Only found via commercial blog sources, not a direct read of a KREDL/state notification |
| Kerala | ANERT (Agency for Non-conventional Energy and Rural Technology) is confirmed as Kerala's State Implementation Agency for PM Surya Ghar (a structural fact, not a separate subsidy) | No distinct, officially-sourced Kerala-specific state subsidy amount was found beyond the central scheme |
| Rajasthan | RRECL (Rajasthan Renewable Energy Corporation Ltd) is the nodal agency; a "Mukhyamantri Nishulk Bijli Yojana" top-up is mentioned | Only found via a commercial blog source, not a direct read of an RRECL/state notification |

### DISCOM

No DISCOM-specific renewable-energy incentive (as opposed to a tariff
concept like net metering, which is Phase 5/7 territory, not an
incentive) was found described in an official, directly-read DISCOM
document during this phase. Unconfigured.

### Summary

Zero `IncentiveProgram` rows exist in production as of Phase 6. This is
the intended, honest outcome given what could be confidently verified —
not a bug. `POST /api/v1/incentives/evaluate` correctly returns an empty
`programmes` list (or, for a technology/category with no schemes at all,
`"calculation_status": "no_programmes_found"`) for every real location
today.

## No false national coverage claim

The architecture (models, migration, engine, API, DISCOM/state
resolution) supports **every** Indian state and union territory — nothing
about the schema is state-specific. That is architecture coverage, not
data coverage:

- **States/UTs architecturally supported:** all 28 states + 8 union
  territories (same list as `app.core.india_geography`, reused unchanged).
- **Verified incentive datasets configured:** none.
- **Unconfigured:** all states and union territories, including the five
  investigated above.

Populating any state, or the central PM Surya Ghar scheme, is future
work: someone with direct access to the primary PDF/notification (or a
cleaner text extraction of it) can add a JSON file here following the
format above, citing the exact document and clause it came from in
`source_document`, and set `verification_status: "verified"` only once
that direct read has actually happened.
