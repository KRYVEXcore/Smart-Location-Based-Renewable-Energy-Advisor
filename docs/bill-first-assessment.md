# Bill-first customer input (Phase 10.5)

SHREA asks for what customers actually know: their **average monthly electricity bill in rupees**,
not kWh. The kWh figure the engines need is derived from that bill with the verified tariff, or
taken from units the customer chooses to enter.

## Flow

Location -> building type -> **average monthly electricity bill** -> roof/space and other constraints
-> report (recommendation, cost/savings placeholders) -> SHREA AI explains it. The bill can be typed or
spoken ("My electricity bill is around seven thousand five hundred rupees a month").

## Inputs and what is authoritative

| Customer gives | `consumption_source` | kWh used by every engine |
| --- | --- | --- |
| bill only (the normal path) | `user_bill_estimate` | an **estimate** derived from the bill (or unknown) |
| bill + optional units | `user_kwh` | the units the customer entered; the bill is kept but **not** used to overwrite them |
| units only (older assessments / direct API) | `user_kwh` | the units |

`POST /api/v1/assessments` accepts `energy.monthly_electricity_bill_inr` (> 0, at most 10,00,000) and/or
`energy.monthly_consumption_kwh`; at least one is required. The units field is an optional, collapsed
"Advanced" input. Existing kWh assessments load unchanged (migration `d8a1f3c5e7b2` adds nullable columns
and marks old rows `user_kwh`; nothing is dropped).

## How the kWh estimate is made

The bill is **not** divided by a per-unit rate: Indian bills combine slabs, fixed charges and other
components. `app/engines/tariff/bill_estimation.py` evaluates the **existing Tariff Engine** at candidate
consumption values and bisects (bounded, 80 iterations, 0.01 kWh precision) until the modelled bill matches
the entered bill within Rs 1. No tariff formula exists in the estimator. If the bill lies inside a jump of the
tariff (a fixed charge that steps up between brackets) no consumption reproduces it exactly, so a range is
returned and the midpoint used, with a limitation saying so.

Example with the verified TNPDCL LT-IA domestic tariff seeded in this project: Rs 7,500 -> about 799 kWh/month
(the Tariff Engine gives Rs 7,500.21 at that consumption).

## Tariff dependency and India specifics

The estimate uses the same resolution as the tariff calculation: coordinates -> state/UT -> DISCOM ->
consumer category (from the building type) -> the tariff version valid today. There is no national fallback.
If the location cannot be resolved, several DISCOMs match, or no verified tariff exists, nothing is estimated:
`consumption_estimate.status = "insufficient_data"` with the reason
"Bill-based consumption estimate unavailable for this location because a verified applicable tariff could not be
established (...)", and `monthly_consumption_kwh` stays `NULL`. The solar, tariff and recommendation engines then
report `insufficient_data` (consumption not known) instead of using a default. `POST /api/v1/assessments/{id}/estimate-consumption`
retries the estimate (for example after a provider hiccup or once a tariff is added); it never overwrites units the
customer entered.

## Estimated vs actual

An estimate is always labelled: "Estimated from your bill using the verified tariff - not a meter reading" (API:
`consumption_source = user_bill_estimate`, plus `consumption_estimate` with method, tariff used, range and limitations).
The dashboard leads with the bill and shows usage as `~N kWh/month`. SHREA AI receives the bill, the source and the
estimate status, is told to say "estimated" (never "actual" or a meter reading), and must not work out kWh from the bill
itself.

## Limitations

- The tariff model excludes electricity duty, taxes, surcharges, demand charges, time-of-day charges and per-kW fixed
  charges, so a real bill can be higher than the modelled one and true consumption may differ from the estimate.
- Only verified tariffs are used (currently five states' residential tariffs); elsewhere the estimate is unavailable and
  the customer can enter units instead.
- Creating a bill-first assessment now waits for location resolution (the location profile is cached afterwards).
- Cost, savings and payback are still not calculated (next phase); the report shows "Not available" for them, and
  "Financing options not currently calculated."
