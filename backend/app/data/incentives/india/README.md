# India incentive seed data

Verified renewable-energy incentive programmes, one JSON file per scheme *version*, loaded into
`incentive_programs` by `python -m scripts.seed_incentives` (or `scripts.seed_all`). Every file is validated
first (`app.data_validation`); if any file fails, nothing is written.

Evidence for every number:
[`docs/data-verification/tariff-and-incentive-research.md`](../../../../../docs/data-verification/tariff-and-incentive-research.md).
Coverage: [`coverage-report.md`](../../../../../docs/data-verification/coverage-report.md).

## Directory layout

```
central/          Central Government schemes
states/<state>/   State/UT schemes (none verified yet)
discom/<discom>/  DISCOM schemes (none verified yet)
```

## Current contents

| File | Scheme | Notes |
|---|---|---|
| `central/PMSG-CFA-2024.02-STANDARD.json` | PM Surya Ghar: Muft Bijli Yojana, CFA to residential consumers | Rs 30,000/kW for the first 2 kW, Rs 18,000 for the 3rd kW, nothing beyond 3 kW (max Rs 78,000). Applies everywhere except the special-category States/UTs |
| `central/PMSG-CFA-2024.02-SPECIAL-CATEGORY.json` | Same scheme, special-category States/UTs | Rs 33,000/kW and Rs 19,800; applies only in Uttarakhand, Himachal Pradesh, Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Sikkim, Tripura, Jammu and Kashmir, Ladakh, Andaman and Nicobar Islands, Lakshadweep |

**No state or DISCOM programme is seeded**: none could be verified in an official document (see the research
log, section B2).

## File format

Same rules as [`../../tariffs/india/README.md`](../../tariffs/india/README.md) for `source`,
`verification_status`, `verification_notes`, Decimal numbers, official hosts and versioning. Fields:

```json
{
  "scheme_name": "...",
  "scheme_version": "PMSG-CFA-2024.02-STANDARD",
  "description": "...",
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
  "calculation_rules": { "slabs": [ { "capacity_min_kw": 0, "capacity_max_kw": 2, "rate_inr_per_kw": 30000 } ] },
  "eligibility_rules": { "requires_fields": [], "excluded_states": ["Sikkim"] },
  "application_requirements": { "apply_through_national_portal": true },
  "stacking_rules": { "combinable_with_levels": ["state"] },
  "effective_from": "2024-02-13",
  "effective_to": "2027-03-31",
  "verification_status": "verified",
  "active": true,
  "source": { "name": "...", "url": "...", "document": "...", "order_number": "...", "order_date": "...",
              "page": "...", "table": "...", "section": "...", "excerpt": "...", "last_verified": "2026-09-19" },
  "verification_notes": "..."
}
```

- `max_system_size_kw` caps the capacity that counts toward the amount (a 6 kW system still gets the 3 kW
  entitlement); it does not make a larger system ineligible.
- The amount is calculated from `calculation_rules`, never hard-coded in Python.
- **Regional variants** of one scheme are separate rows with the same `scheme_name`. Which one applies is
  decided by `eligibility_rules`: `applies_only_to_states`, `applies_only_to_union_territories`,
  `excluded_states`, `excluded_union_territories` (see `app.engines.incentive.scope`). The dataset check
  rejects two overlapping versions that both apply in the same region.
- `stacking_rules` records only what an official document states. Missing rules mean "not verified", never
  "combinable".
- `percentage` and `benchmark_cost_based` schemes are always `insufficient_information` because the app collects
  no verified installation cost. `fixed_amount`, `per_kw` and `slab_based` are calculated in full.
- An expired version (`effective_to` in the past) is reported `scheme_expired`, never silently dropped and never
  applied. A scheme extended by a later order gets a new version row; the old one is kept.

Seeding is an idempotent upsert on (scheme_name, level, technology, scheme_version); no row is ever deleted.

## What is not a subsidy

Net metering, vendor empanelment, DISCOM incentives paid *to DISCOMs*, and recurring tariff rebates (for
example Karnataka's Rs 25/kW/month fixed-charge rebate for rooftop-solar homes) are not one-time consumer
incentives and are not seeded as such.
