# India tariff seed data

This directory is where genuinely verified official electricity tariff data
is checked in, one JSON file per DISCOM/state schedule, loaded into
`electricity_tariffs` by [`backend/scripts/seed_tariffs.py`](../../../../scripts/seed_tariffs.py).
It intentionally contains **no real tariff data yet** — see the investigation
record below.

## File format

One file per tariff schedule, at `india/<state-slug>/<tariff_version>.json`:

```json
{
  "state": "Tamil Nadu",
  "union_territory": null,
  "discom_short_code": null,
  "consumer_category": "residential",
  "tariff_version": "EXAMPLE-DOMESTIC-2026.1",
  "tariff_name": "EXAMPLE Domestic (LT-IA) Tariff",
  "effective_from": "2026-01-01",
  "effective_to": null,
  "source_url": "https://example.invalid/official-tariff-order",
  "source_document": "EXAMPLE Tariff Order No. 0 of 2026",
  "source_name": "EXAMPLE State Electricity Regulatory Commission",
  "last_verified": "2026-01-01",
  "slabs": [
    { "slab_min_kwh": 0, "slab_max_kwh": 100, "energy_charge_inr_per_kwh": 0.00, "fixed_charge_inr": null },
    { "slab_min_kwh": 100, "slab_max_kwh": null, "energy_charge_inr_per_kwh": 0.00, "fixed_charge_inr": null }
  ]
}
```

`discom_short_code` is resolved against the existing `discoms` table
(`null` means a state-level tariff with no specific DISCOM). `slabs` must
start at 0, be contiguous, and have exactly one final slab with
`slab_max_kwh: null` — see `app.engines.tariff.validation` for the exact
rules enforced at calculation time.

[`schema_example.json`](schema_example.json) uses the `.example.json`-style
naming (excluded from the loader's `*.json` glob by living outside any
`<state-slug>/` folder) so it is never mistaken for real data.

## Investigation record (Phase 5)

Per this project's explicit rule — **prefer NO DATA over FAKE DATA** — a
state's tariff is only seeded here once its exact slabs, rates, and charges
have been confirmed by reading an actual official source (a state
Electricity Regulatory Commission, an official DISCOM tariff page, or an
official tariff order/notification). A commercial bill-calculator site,
blog, or aggregator is never treated as the authoritative source, even when
it is useful for locating the real one.

Five states were investigated for this phase, as required. None could be
confidently verified within this phase's tooling, so **all five remain
unconfigured** — no `ElectricityTariff` rows exist for them:

| State | Official source(s) located | Why not seeded |
|---|---|---|
| Tamil Nadu | TNERC tariff orders page (`tnerc.tn.gov.in/TariffOrders.aspx`); a tariff order PDF only available via a third-party mirror | The mirrored PDF is compressed/encoded and could not be read as text; the only readable slab figures found were from secondary commercial sites (SolarQuarter, Adyar Times, tristarenergy.in), which this project's rules exclude as an authoritative source |
| Maharashtra | MERC (`merc.gov.in`) MYT order press note PDF; MSEDCL's own tariff schedule PDF (`mahadiscom.in`) | Same PDF-readability limitation; the specific per-slab rates found in search results trace back to commercial calculator sites, not a direct read of the MERC/MSEDCL PDF text |
| Karnataka | KERC tariff-orders page (`kerc.karnataka.gov.in`); BESCOM's own tariff page (`bescom.karnataka.gov.in`) | Only page listings were reachable, not the underlying order document text; rate figures in search results again trace to commercial aggregator sites |
| Kerala | KSERC's own document store (`erckerala.org`), including a document titled "Schedule of Tariff and Terms and Conditions for Retail Supply" | The PDF is a scanned/compressed document that could not be extracted as readable text with the tooling available in this phase |
| Rajasthan | RERC tariff-orders page (`rerc.rajasthan.gov.in`); JVVNL's own tariff order PDF (`cescrajasthan.co.in`) | Same PDF-readability limitation; slab figures in search results trace to commercial calculator sites, not a direct read of the RERC/JVVNL order |

In every case, a real official source was located, but this phase's tooling
could not extract a complete, exact slab table from it with enough
confidence to store as authoritative data — and the numbers that were
readable came from commercial aggregator sites this project's rules
explicitly exclude as a source of record. Populating any of these five
states is future work: someone with direct access to the primary PDF (or a
cleaner text extraction of it) can add a JSON file here following the
format above, citing the exact order number and page/clause it came from in
`source_document`.

Until then, `POST /api/v1/tariffs/calculate` correctly reports
`tariff_not_configured` for all locations in these (and any other)
states — this is the intended, honest behavior, not a bug.
