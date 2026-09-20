# Financial analysis (Phase 11)

`GET /api/v1/financial-analysis/{assessment_id}` returns an **estimated** gross cost, verified incentive,
net investment, savings and simple payback for the system the Recommendation Engine chose. It is
deterministic, never calls an AI provider, and never invents a number: a value that cannot be supported is
`null` (shown as "Not available"), never `0`. SHREA AI only explains the result. Calculation version:
`financial-2026.1`.

Code: `backend/app/engines/financial/` (`engine.py`, `costs.py`), `backend/app/schemas/financial.py`,
data in `backend/app/data/costs/india/`. The recommendation's `cost_context` is filled from the same
result (`recommendation_service.py`), so there is one calculation, not two.

## Status

| status | meaning |
| --- | --- |
| `complete` | a verified cost and modelled savings both exist (payback too when savings are above zero) |
| `cost_unavailable` | no verified cost applies (for example a college); savings are still shown when they can be modelled |
| `savings_unavailable` | the cost is known but savings cannot be modelled (no verified tariff, or no 12-month generation) |
| `insufficient_data` | neither cost nor savings can be produced (also wind, which has no verified cost model) |
| `not_applicable` | there is no recommended system to analyse |

## Cost source

Only figures read from a primary official document are used.

- **Source:** Ministry of New and Renewable Energy (MNRE), *Guidelines for PM-Surya Ghar: Muft Bijli Yojana -
  Central Financial Assistance to Residential Consumers*, page 8, clause g) "Benchmark Cost".
- **URL:** <https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/07/202507081690964295.pdf>
- **Values:** Rs 50,000/kW for the first 2 kW and Rs 45,000/kW for each additional kW, effective 13 Feb 2024;
  special-category States/UTs (Uttarakhand, Himachal Pradesh, Jammu and Kashmir, Ladakh, the North-East
  including Sikkim, Andaman and Nicobar Islands, Lakshadweep): Rs 55,000 and Rs 49,500.
- **Verified:** 2026-09-20, by reading the PDF's text layer. Each record stores the source name, document, URL,
  page, section, an excerpt, effective date, capacity basis, geographic scope, inclusions, exclusions, GST
  treatment and verification date, and a record without them cannot be loaded.
- **What it is not:** a *benchmark* (the basis MNRE uses to compute assistance), not a market quote or a price
  range, so real vendor quotes vary. The clause does not state what the price includes or excludes, or how GST is
  treated; the dataset says exactly that ("Not stated in the guideline clause") rather than guessing. The guidelines
  say the benchmark will be revised at the mid-term review.
- **Scope:** residential consumers only. A college, office or shop has **no** verified cost, so `cost_status` is
  `not_available` and the recommendation shows its existing "verified cost is not available" message.
- **3 kW:** the guidelines define central assistance only up to 3 kW; for larger systems the same per-kW benchmark
  rates are applied and the result carries a limitation saying so. The exact recommended capacity is always used
  (7 kW is priced as 7 kW: 2 x 50,000 + 5 x 45,000 = Rs 3,25,000).

No other source was found that is defensible enough to add (no market range, no GST-inclusive price). If none of
the records matches, the cost is unavailable; the engine still works without cost data.

## Incentive

Taken unchanged from the existing Incentive Engine via the recommendation (`applicable_incentives`), evaluated
for the recommended technology and size, so the residential PM Surya Ghar scheme is never applied to a
non-residential building. If several eligible programmes apply and their combination is not verified, only the
largest is applied and the note says so. Net investment = gross cost - incentive, never below zero; a cost
range stays a range (both ends are kept, no midpoint).

## Savings

Not "bill / kWh". For each of the 12 months, the existing Tariff Engine gives the bill for the customer's
consumption and the bill for the consumption left after solar generation, limited to what the customer actually uses:

    saving_m = bill(consumption) - bill(consumption - min(generation_m, consumption))

The annual saving is the sum over the year and the monthly figure is one twelfth of it. Fixed charges therefore do
not count as savings, and 104% annual coverage is not 104% savings. Generation comes from the Solar Engine's
monthly figures for the recommended size; if fewer than 12 months, no verified tariff, or no consumption exists,
savings are unavailable.

## Payback

`estimated simple payback = net investment / estimated annual savings`, only when both exist and savings are above
zero. It excludes tariff escalation, maintenance savings, financing or loan costs, tax benefits, panel degradation
and any future return on investment. Nothing here is a guarantee of cost, savings, payback or future tariffs.

## Limitations

- **Export / net-metering income is not modelled.** Surplus generation is not valued at the retail tariff or at
  all (`annual_surplus_generation_kwh` is reported in kWh only).
- **Financing is not modelled.**
- Consumption is treated as the same every month; demand and time-of-day tariff components, government bill
  subsidies, taxes, duties and surcharges are not modelled (savings use the verified tariff in the dataset, the
  same one the bill-to-kWh estimate uses).
- Cost is a published benchmark, not a vendor quote; wind has no cost or savings model.
- Verified vs estimated: the cost, tariff and incentive inputs are verified data; every output is an estimate.

## SHREA AI

The advisor context has a `financial_analysis` section (the same result). The prompt tells the model to quote it
exactly, call every figure "estimated", keep ranges as ranges, say a value is not available when it is absent, and
never compute a different figure. "What will my system cost?", "What will I save?", "What is my payback?" and
"Explain my financial report" are answered from it. No extra AI call or voice system is involved.
