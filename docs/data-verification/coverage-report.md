# Coverage report

As of **2026-09-19**. This report separates what the software *can* represent from what
data has actually been *verified*. It does **not** claim India is covered. Row-level detail:
[data-quality-report.md](data-quality-report.md) (generated) and
[tariff-and-incentive-research.md](tariff-and-incentive-research.md) (evidence).

## A. Architecture support

The data model, engines, API and location/DISCOM resolution support every Indian State and
Union Territory (28 States + 8 UTs). Nothing in the schema is state-specific. This is
capability only, not data.

Known engine limits that stop some real tariffs from being represented (so they are **not**
seeded rather than seeded wrongly):

- Progressive (telescopic) energy slabs only. Non-telescopic billing, where the whole month
  is billed at one bracket rate (Kerala above 250 units/month), is not supported.
- A fixed charge is billed only when it is a flat monthly or per-connection amount, taken
  from the bracket the month's consumption falls in. Per-kW/kVA/HP charges are reported
  `not_calculated` because sanctioned load is not collected.
- No demand charge, time-of-day, electricity duty, FAC, surcharge or tax.
- DISCOM resolution is state-level only, so a state with several DISCOMs is `ambiguous`.

## B. Verified tariff coverage (residential only)

| State | DISCOM scope | Versions | Usable for a location? |
|---|---|---|---|
| Tamil Nadu | TNPDCL (single DISCOM, identified) | 2025-07-01 onward | **Yes.** Approved tariff before the Government subsidy |
| Andhra Pradesh | State level (common to APSPDCL, APCPDCL, APEPDCL) | FY2026-27 only (to 2027-03-31) | **Yes**, energy charge only: the per-kW fixed charge is not billed |
| Karnataka | State level (common to all ESCOMs) | FY2025-26, FY2026-27 | **Yes**, energy charge only: the per-kW fixed charge is not billed |
| Rajasthan | State level (common to JVVNL, AVVNL, JdVVNL) | from 2025-10-01, FY2026-27 | **Yes** |
| Maharashtra | MSEDCL | FY2025-26, FY2026-27 | **Data verified, but not usable automatically**: four licensees are registered, so every Maharashtra location resolves as `ambiguous` |

Verified tariff datasets: **8 schedules** across **5 states**, one category (residential).

## C. Verified incentive coverage

| Programme | Level | Coverage |
|---|---|---|
| PM Surya Ghar: Muft Bijli Yojana, CFA to residential consumers | Central | All States and UTs, in two rows (standard rates; special-category States/UTs at higher rates). Residential only. Valid until the guideline's 2027-03-31 implementation end |

Verified incentive programmes: **1** scheme in **2** rows. State programmes verified: **0**.
DISCOM programmes verified: **0**.

## D. Unverified jurisdictions and categories

| Item | Status |
|---|---|
| Kerala tariff (KSERC order of 05.12.2024 read and understood) | Not seeded: engine cannot bill it correctly (see A) |
| Gujarat tariff (GERC schedule effective 1 April 2026 read) | Not seeded: RGP and RGP (Rural) rates differ and the app cannot tell which applies |
| Delhi, Telangana | `NOT_VERIFIED`: controlling order not identified / read |
| Non-residential tariffs (commercial, educational, public service, industrial, agriculture) for every state | `NOT_VERIFIED`: not seeded; the app cannot pick the right category without inputs it does not collect |
| Karnataka LT-2 (private educational institutions) | Not seeded: government-run colleges are billed under LT-1, and ownership is not collected |
| State incentives in Tamil Nadu, Maharashtra, Karnataka, Kerala, Rajasthan | `NOT_FOUND` in any official order, notification or agency page |
| Karnataka rooftop-solar rebate on fixed charges (Rs 25/kW/month, KERC LT-1 note (b)) | Real, but a recurring tariff rebate; not modelled as a one-time incentive |
| DISCOM incentives everywhere | `NOT_FOUND` |
| PM Surya Ghar national portal state-notification list | Host unreachable from the research environment on 2026-09-19 |

## E. Research pending (not yet attempted)

Tariff research has **not** been done for: Arunachal Pradesh, Assam, Bihar, Chhattisgarh, Goa,
Haryana, Himachal Pradesh, Jharkhand, Madhya Pradesh, Manipur, Meghalaya, Mizoram, Nagaland,
Odisha, Punjab, Sikkim, Tripura, Uttar Pradesh, Uttarakhand, West Bengal, Andaman and Nicobar
Islands, Chandigarh, Dadra and Nagar Haveli and Daman and Diu, Jammu and Kashmir, Ladakh,
Lakshadweep, Puducherry.

For all of these the API answers `tariff_not_configured` (no bill is shown, never a
placeholder or an average). State-level incentives are likewise not researched beyond the five
priority states.

## F. Things that must be re-verified

- **Tamil Nadu**: TNERC's Order 6 of 2025 provides for an inflation-based adjustment from
  1 July 2026. No such order was published as of 2026-09-19; re-check the TNERC tariff-orders
  page.
- **PM Surya Ghar**: implementation period ends 2027-03-31; an extension or new guideline
  would need a new version row.
- **Andhra Pradesh**: the schedule is for FY 2026-27 only and stops applying after 2027-03-31; the domestic rates are contingent on the State Government paying the subsidy (para 211).
- **Karnataka**: BESCOM published notice of a new tariff petition in September 2026.
- **Kerala**: the KSERC order is subject to a High Court writ outcome (WP(C) 34202 of 2024).
