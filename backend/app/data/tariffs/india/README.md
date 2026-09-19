# India tariff seed data

Verified electricity tariff schedules, one JSON file per schedule at
`<state-slug>/<tariff_version>.json`, loaded into `electricity_tariffs` by
`python -m scripts.seed_tariffs` (or `scripts.seed_all`). Every file is
validated first (`app.data_validation`); if any file fails, nothing is
written.

The evidence for every number is in
[`docs/data-verification/tariff-and-incentive-research.md`](../../../../../docs/data-verification/tariff-and-incentive-research.md);
what is and is not covered is in
[`coverage-report.md`](../../../../../docs/data-verification/coverage-report.md).

## Current contents

| Folder | Schedules | DISCOM scope |
|---|---|---|
| `tamil_nadu/` | `TN-TNPDCL-LT-IA-2025.07` | TNPDCL |
| `andhra_pradesh/` | `AP-DISCOMS-LT-I-A-FY2026-27` | state level (all three DISCOMs) |
| `maharashtra/` | `MH-MSEDCL-LT-IB-FY2025-26`, `MH-MSEDCL-LT-IB-FY2026-27` | MSEDCL |
| `karnataka/` | `KA-ESCOMS-LT1-FY2025-26`, `KA-ESCOMS-LT1-FY2026-27` | state level (all ESCOMs) |
| `rajasthan/` | `RJ-DISCOMS-LT1-FY2025-26-H2`, `RJ-DISCOMS-LT1-FY2026-27` | state level (all DISCOMs) |

Residential only. **No other State/UT has a file**, and none may be added without a verified source.
Kerala was verified but is deliberately not seeded (its non-telescopic billing cannot be represented).

## File format

```json
{
  "state": "Tamil Nadu",
  "union_territory": null,
  "discom_short_code": "TNPDCL",
  "consumer_category": "residential",
  "tariff_version": "TN-TNPDCL-LT-IA-2025.07",
  "tariff_name": "...",
  "effective_from": "2025-07-01",
  "effective_to": null,
  "fixed_charge_basis": "inr_per_kw_per_month",
  "verification_status": "verified",
  "active": true,
  "source": {
    "name": "Tamil Nadu Electricity Regulatory Commission (TNERC)",
    "url": "https://www.tnerc.tn.gov.in/...pdf",
    "document": "Suo-motu Order No. 6 of 2025 ...",
    "order_number": "Suo-motu Order No. 6 of 2025",
    "order_date": "2025-06-30",
    "page": "34 (PDF page 34 of 53)",
    "table": "3.2.2 Low Tension Tariff I-A ...",
    "section": "Chapter 3, clause 3.2.2",
    "excerpt": "the quoted figures as printed in the document",
    "last_verified": "2026-09-19"
  },
  "verification_notes": "cross-checks, supersession check, caveats",
  "slabs": [
    { "slab_min_kwh": 0, "slab_max_kwh": 200, "energy_charge_inr_per_kwh": 4.95, "fixed_charge_inr": 0 },
    { "slab_min_kwh": 200, "slab_max_kwh": null, "energy_charge_inr_per_kwh": 6.65, "fixed_charge_inr": 0 }
  ]
}
```

Rules enforced by the loader and the tests:

- A `verified` record needs a complete source: organisation, official `https` URL (regulator, ministry,
  government or official DISCOM host, see `app.data_validation.official_sources`), document, order number,
  page, a table or section, the quoted excerpt, and `last_verified`. Commercial calculators, blogs and news
  sites are rejected.
- An unverified record must be `active: false` and is never used for a bill.
- Numbers are parsed as `Decimal`, never float. Rates are `energy_charge_inr_per_kwh` (convert paise exactly:
  495 paise = 4.95).
- Slabs start at 0, are contiguous, and only the last has `slab_max_kwh: null`. Do not round or merge the
  regulator's boundaries; splitting a slab is only acceptable when needed to express a per-bracket fixed
  charge, and must be explained in `verification_notes`.
- `fixed_charge_basis` is required whenever a fixed charge is given: `inr_per_month`,
  `inr_per_connection_per_month`, `inr_per_kw_per_month`, `inr_per_kva_per_month` or `inr_per_hp_per_month`.
  Only the first two are billed; a per-kW/kVA/HP charge is reported `not_calculated`.
  A fixed charge may differ per slab: the bill uses the slab that the month's total consumption falls in.
- `wheeling_charge_inr_per_kwh` is stored separately from the energy charge.
- Versions are never overwritten: a new order gets a new `tariff_version` with its own effective dates and the
  old file stays. Overlapping effective periods for the same state/DISCOM/category are rejected.
- `discom_short_code` must exist in `../../discoms/india/discoms.json` for that state. Use `null` (state
  level) only when the official document makes one schedule common to every DISCOM in the state.

Seeding is an idempotent upsert on (state/UT, DISCOM, category, version, slab minimum). It never deletes a
row; a slab dropped from a file is deactivated.

## Adding a new state

1. Find the current regulator order and any later amendment, corrigendum or superseding order.
2. Read the exact table in the primary document (render the PDF page if it has no text layer).
3. Cross-check against the DISCOM's own publication where possible.
4. Add the JSON file with the full source locator, run `python -m scripts.data_quality_report`, and add the
   evidence to the research log.

If the number cannot be established with confidence, do not add a file.
