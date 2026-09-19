# Tariff and incentive research log (Phase 6.7)

Verification date: **2026-09-19**. Rule applied throughout: real data > no data > fake data.
A number is `VERIFIED` only when it was read from a primary official document
(regulator order, DISCOM publication, government/ministry document) and the exact page/table
is recorded. Search-engine snippets, calculators, blogs and news were used only to locate an
official document; no number below comes from them.

Statuses: `VERIFIED`, `PENDING_REVIEW`, `EXPIRED`, `SUPERSEDED`, `NOT_VERIFIED`, `NOT_FOUND`.
"Seeded" means a row exists in `electricity_tariffs` / `incentive_programs`.

Every source PDF below was downloaded and read locally (text layer, or rendered to an image and
read visually where the PDF has no text layer). The SHA-256 prefix and byte size let a reviewer
confirm they are looking at the same file.

---

## A. Tariffs

### A1. Tamil Nadu — TNPDCL — LT Tariff I-A (Domestic) — VERIFIED, seeded

| Field | Value |
|---|---|
| Jurisdiction / DISCOM | Tamil Nadu / TNPDCL (Tamil Nadu Power Distribution Corporation Ltd) |
| Category | LT Tariff I-A: Domestic, multi-tenements, old age homes, handlooms -> `residential` |
| Programme version | `TN-TNPDCL-LT-IA-2025.07` |
| Effective | from **2025-07-01**, open ended (no superseding order found) |
| Source organisation | Tamil Nadu Electricity Regulatory Commission (TNERC) |
| Document | Suo-motu Order No. 6 of 2025 dated 30-06-2025, "Determination of Tariff for Distribution for FY 2025-26" (effective from 01-07-2025) |
| Official URL | https://www.tnerc.tn.gov.in/Orders/files/TO-Order%20No6300620252111.pdf |
| Page / table | section 3.2.2 "Low Tension Tariff I-A", printed page 34 (PDF page 34) |
| File | SHA-256 `efc5a4600d4319bc...`, 1,082,004 bytes |
| Rates (paise/kWh, per month bands) | 0-200: 495; 201-250: 665; 251-300: 880; 301-400: 995; 401-500: 1105; 501 and above: 1215. Fixed charge (Rs per kW per month): Nil |
| Cross-check 1 | TNPDCL's own tariff page (https://www.tnpdcl.org/en/tnpdcl/billing-services/schedules-tariff/, "Last Updated: Sept. 8, 2026") links this same order as the tariff order (`.../static/tnpdcl/assets/files/tariff/2025/TO062025/TO62025.pdf`). The DISCOM's file is byte-identical to the regulator's (same SHA-256). |
| Cross-check 2 | TNERC Order No. 4 of 2026 dated 27-04-2026 ("Provisional Tariff Subsidy Order for FY 2026-27", https://www.tnerc.tn.gov.in/Orders/files/TO-Order%20No%20280420261156.pdf), pages 7-9, restates the approved domestic energy charges "with effect from 01-07-2025" as 495/665/880/995/1105/1215 paise, and (page 4, para 3(12)(a)) records the State Government's commitment of "No tariff hike to the Domestic consumers (LT IA)". |
| Currentness check | The order says (page 34) that FY 2026-27 tariff "shall undergo an inflation based adjustment ... effective from 01st July of 2026". As of 2026-09-19 no revised order appears on TNERC's tariff-orders page (newest entry 01/06/2026), TNPDCL still links Order 6 of 2025 as the tariff order, and TNERC Order 5 of 2026 (26-05-2026) still uses the 4.95 rate for the 01-07-2026 to 30-09-2026 period. Treated as current; **re-verify if TNERC publishes an inflation-adjustment order.** |
| Important caveat | These are the **approved tariff** rates. Under TNERC Order 4 of 2026 the Government of Tamil Nadu pays a per-unit subsidy, so the amount a household pays is lower (for example the first 100 units per two months are free). The tariff engine does not model that subsidy; it is recorded in `verification_notes` and shown to the user. Electricity duty/tax is levied in addition "in accordance with the Government of Tamil Nadu stipulations" (Order 6 of 2025, clause 3.2.1(m)); no rate is stated in the order, so it is not modelled. |
| Status | **VERIFIED** |

### A2. Maharashtra — MSEDCL — LT I(B) Residential — VERIFIED, seeded (two versions)

| Field | Value |
|---|---|
| Jurisdiction / DISCOM | Maharashtra / MSEDCL (Maharashtra State Electricity Distribution Co. Ltd) |
| Category | LT I(B): LT - Residential -> `residential` |
| Versions | `MH-MSEDCL-LT-IB-FY2025-26` (2025-07-01 to 2026-03-31); `MH-MSEDCL-LT-IB-FY2026-27` (from 2026-04-01) |
| Source organisation | Maharashtra Electricity Regulatory Commission (MERC), published on MSEDCL's tariff page |
| Controlling document | Order in Case No. 75 of 2025 dated **25 March 2026** ("post remand proceedings") |
| Official URL | https://www.mahadiscom.in/wp-content/uploads/2026/07/Tariff-Order_Case-No.-75-of-2025-dated-25th-March-2026.pdf (linked from https://www.mahadiscom.in/en/consumer/tariff-details/) |
| Page / table | "Summary of LT Tariff for FY 2025-26, effective from 1 July, 2025": printed page 94. "Summary of LT Tariff for FY 2026-27, effective from 1 April, 2026": printed page 95. Effective-date reasoning: para 26.5-26.8, page 88-89 |
| File | SHA-256 `5b1111fa8a7d8f3c...`, 2,015,990 bytes |
| FY 2025-26 (Rs/kWh) | fixed Rs 130/connection/month; 1-100: energy 4.28 + wheeling 1.47; 101-300: 11.10 + 1.47; 301-500: 15.38 + 1.47; above 500: 17.68 + 1.47 |
| FY 2026-27 (Rs/kWh) | fixed Rs 130/connection/month; 1-100: energy 3.96 + wheeling 1.60; 101-300: 10.80 + 1.60; 301-500: 15.03 + 1.60; above 500: 17.53 + 1.60. Three-phase charges Rs 435/connection/month |
| Supersession check | MYT Order (Case 217 of 2024, 28-03-2025) was stayed; review order of 25-06-2025 revised tariff from 1 July 2025; the Bombay High Court set that review order aside on 3-11-2025 and the Supreme Court remanded (17-11-2025, 9-02-2026). The 25-03-2026 order is the post-remand order; para 26.8 confirms the tariff "is made effective from 1 July 2025" and that FY 2025-26 tariff "is the same" as the earlier order. It is the newest MERC order for MSEDCL on the MSEDCL and MERC sites as of 2026-09-19. |
| Cross-check | MERC's earlier review order (Case 75 of 2025, 25-06-2025, https://www.mahadiscom.in/consumer/wp-content/uploads/2025/06/Order_Case-No.75-of-2025.pdf, SHA-256 `1fe4743ba3c0736f...`) prints identical LT I(B) rows for FY 2025-26 (page 52) and FY 2026-27 (page 53). Two separate regulator orders agree. |
| Billing method | Residential consumers are billed on a telescopic tariff (MERC Case 217 of 2024, para 2.4.5, page 62, recording MSEDCL's submission). This matches the engine. |
| Rounding note | The order prints the FY 2025-26 first-slab total variable charge as 5.74 although 4.28 + 1.47 = 5.75. Energy and wheeling are stored separately as printed; the engine sums them, so the estimate differs by at most Rs 0.01/kWh from the printed total. |
| Not included | Fixed charge is single-phase (three-phase adds Rs 435; phase is not collected). Electricity duty, FAC and taxes are not modelled. |
| DISCOM resolution | MSEDCL does not serve all of Maharashtra (Mumbai is also served by BEST, Adani Electricity Mumbai and Tata Power-D). The location resolver works at state level only, so Maharashtra locations resolve as **`ambiguous`** and the MSEDCL schedule is reported as blocked, never guessed. Needs district-level licence-area data to improve. |
| Status | **VERIFIED** (data). Applies only when the DISCOM is identified as MSEDCL. |

### A3. Karnataka — all ESCOMs — LT-1 Domestic — VERIFIED, seeded (two versions)

| Field | Value |
|---|---|
| Jurisdiction / DISCOM | Karnataka / common tariff for BESCOM, MESCOM, CESC, HESCOM, GESCOM (state-level row) |
| Category | LT-1 Domestic -> `residential` |
| Versions | `KA-ESCOMS-LT1-FY2025-26` (2025-04-01 to 2026-03-31); `KA-ESCOMS-LT1-FY2026-27` (from 2026-04-01) |
| Source organisation | Karnataka Electricity Regulatory Commission (KERC) |
| Controlling document | Combined Tariff Order 2025 for ESCOMs dated 27.03.2025 (control period FY2025-26 to FY2027-28); Annexure 9 "Tariff Schedule LT-1" |
| Official URL | https://kerc.karnataka.gov.in/uploads/96731743148968.pdf (listed on https://kerc.karnataka.gov.in/143/tariff-order-2025/en); approved-charges table https://kerc.karnataka.gov.in/uploads/85821743074692.pdf, page 1 |
| Page / table | LT-1 schedule: PDF page 550 (printed 534). Effective-date clause: order paragraph 2, printed page 260. Uniform tariff across ESCOMs: Chapter 6, page 197 |
| File | SHA-256 `d84997a4f7195b5c...`, 21,755,322 bytes |
| Rates | FY2025-26: energy 580 paise/kWh (single slab), fixed Rs 145 per kW of sanctioned load per month. FY2026-27: energy 580 paise/kWh, fixed Rs 150 per kW per month. (FY2027-28: 575 paise, Rs 160/kW, approved but **not seeded** because it is not yet effective.) |
| Effective | Order para 2: "shall come into effect from 1st April-2025 for FY2025-26, 1st April-2026 for FY2026-27 ... and would remain in force until further orders" |
| Cross-check | BESCOM's own "Electricity Tariff-2026 to 2028" (https://bescom.karnataka.gov.in/uploads/media_to_upload1775021662.pdf, SHA-256 `5a7302cf7144b782...`), printed page 16, prints the same LT-1 schedule. |
| Amendments checked | Corrigendum dated 26.05.2025 (does not touch LT-1); Review Petition 8/2025 order dated 03.03.2026 (revises LT-4a, LT-3a, LT-5, HT-2a, HT-2b only, not LT-1). BESCOM has published a notice of a *new tariff petition* (September 2026); a petition does not change the tariff in force. |
| Fixed charge | Per kW of **sanctioned load**, which this app does not collect. Stored with basis `inr_per_kw_per_month` and reported as `not_calculated`; it is never converted into a flat monthly amount. |
| Not seeded | LT-2 (private educational institutions/hospitals): KERC bills government-run colleges under LT-1 and private ones under LT-2, and ownership is not collected, so it cannot be applied safely. |
| Status | **VERIFIED** |

### A4. Rajasthan — all three DISCOMs — LT-1 General Domestic — VERIFIED, seeded (two versions)

| Field | Value |
|---|---|
| Jurisdiction / DISCOM | Rajasthan / one common schedule for JVVNL, AVVNL and JdVVNL (state-level row) |
| Category | Domestic category (LT-1) General Domestic 1-4 -> `residential` |
| Versions | `RJ-DISCOMS-LT1-FY2025-26-H2` (2025-10-01 to 2026-03-31); `RJ-DISCOMS-LT1-FY2026-27` (from 2026-04-01) |
| Source organisation | Rajasthan Electricity Regulatory Commission (RERC) |
| Documents | Petition Nos. 2378/2025, 2379/2025, 2380/2025, order dated **30.03.2026** (FY 2026-27); Petition Nos. 2303/2025, 2304/2025, 2305/2025, order dated 03.10.2025 (FY 2025-26) |
| Official URL | https://rerc.rajasthan.gov.in/rerc-user-files/tariff-orders (documents open through the "View" button; rows 6 and 19 of the list) |
| Page / table | FY 2026-27: Annexure C "Approved Tariff for FY 2026-27", PDF page 333 of 342; effective-date clause 5.9.18, page 231. FY 2025-26: Annexure C, PDF page 274-275; clause 4.7.12 (PDF page 170) |
| Files | FY 2026-27 SHA-256 `db1676cb949f381e...` (5,040,566 bytes); FY 2025-26 `9d3eace2e934a9ba...` (4,588,698 bytes) |
| Rates | Energy: first 50 units Rs 4.75; 51-150 Rs 6.00; 151-500 Rs 7.00; above 500 Rs 7.50 per unit per month. Fixed charge is set by the consumption bracket: up to 150 units Rs 150; up to 300 Rs 300; up to 500 Rs 500; above 500 Rs 800 per connection per month |
| Effective | 5.9.18: "This tariff order shall come into force from 01.04.2026 and remain in force till the next tariff order". 4.7.12: "shall come into force from 01.10.2025" |
| Note | The "Existing Tariff" column of the FY 2026-27 order equals its approved column, i.e. rates are unchanged from 01.10.2025. The tariff in force before 01.10.2025 has no stated effective date in these documents and is **not seeded**. |
| Not modelled | BPL / Astha card small-domestic tariff (needs card status). Slabs are split at 300 units so the per-bracket fixed charge can be expressed; both halves carry the same official rate. |
| Cross-check | The FY 2025-26 order's "Approved Tariff" column and the FY 2026-27 order's "Existing Tariff" column agree. No DISCOM website copy could be opened (energy.rajasthan.gov.in returns a generic shell). |
| Status | **VERIFIED** |

### A5. Kerala — KSEB — LT-1 Domestic — verified data, **NOT SEEDED** (engine limitation)

KSERC Order dated 05.12.2024 in OP No. 18/2023 (https://kseb.in/uploads/Subsubmenu/Latest%20Tariff%20Orders0912202411:17:56.pdf, SHA-256 `b44c477acdd63b00...`) approves the schedule for 05.12.2024 to 31.03.2027. Domestic energy charges are telescopic up to 250 units/month and **non-telescopic** above (the whole month billed at one bracket rate), and the fixed charge depends on the monthly consumption bracket. The engine only supports progressive slabs, so seeding it would compute wrong bills for consumption above 250 units. Status: **NOT SEEDED - PENDING_REVIEW** until the engine supports non-telescopic billing.

### A6. Other states / UTs

Not researched in this phase: Andhra Pradesh, Arunachal Pradesh, Assam, Bihar, Chhattisgarh, Goa, Gujarat, Haryana, Himachal Pradesh, Jharkhand, Madhya Pradesh, Manipur, Meghalaya, Mizoram, Nagaland, Odisha, Punjab, Sikkim, Telangana, Tripura, Uttar Pradesh, Uttarakhand, West Bengal and all Union Territories. Status **NOT_VERIFIED**; no rows exist for them.

### A7. Non-residential categories

Commercial, educational and other tariff categories were **not** seeded for any state. Each state uses different category definitions (Karnataka's LT-1/LT-2 split above, Rajasthan's NDS types, Maharashtra's kW-band categories, Tamil Nadu's LT V) and the assessment does not collect the fields (sanctioned load, ownership) needed to pick one. No residential rate is ever reused for a college or shop.

---

## B. Incentives

### B1. PM Surya Ghar: Muft Bijli Yojana - CFA to residential consumers - VERIFIED, seeded (two rows)

| Field | Value |
|---|---|
| Level / consumer | Central / residential only |
| Source organisation | Ministry of New and Renewable Energy (MNRE), Government of India |
| Controlling document | "Guidelines for PM-Surya Ghar: Muft Bijli Yojana - Central Financial Assistance to Residential Consumers" (OM No. 318/17/2024-GCRT dated 07.06.2024, published 02.07.2024) |
| Official URL | https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2024/07/202407021768035484.pdf (listed at https://mnre.gov.in/en/notice/operational-guidelines-for-implementation-of-the-component-central-financial-assistance-to-residential-consumers-of-pm-surya-ghar-muft-bijli-yojana/) |
| File | SHA-256 `2de9b3faf765c18b...`, 1,284,739 bytes, 57 pages |
| CFA structure | Clause 5(e), page 5, and 5(h) "Effective CFA", page 6: first 2 kWp Rs 30,000/kWp; 3rd kWp Rs 18,000/kWp; nothing beyond 3 kWp (example iii: a 6 kW system gets Rs 78,000). Special-category States/UTs (Uttarakhand, Himachal Pradesh, J&K, Ladakh, the North-East States including Sikkim, A&N, Lakshadweep): Rs 33,000 and Rs 19,800 per kWp (clause 5(g)-(h), page 6) |
| Eligibility | Clause 5(d), page 5: no CFA to non-residential segments (government, commercial, industrial). Clause 5(m): domestic-content modules required. Clause 5(o): CFA only once per installation. Clause 5(k): CFA is by module DC capacity |
| Implementation period | Clause 2(d), page 3: "till 31st March, 2027". Applications from 13 February 2024 (clause 2(c)) |
| Stacking | Clause 5(i), page 7: State/UT governments "may supplement the CFA provided by the central government ... with an additional subsidy". Central + state is therefore recorded as combinable; DISCOM combinability is not stated and is left unverified |
| Amendment checked | MNRE Office Memorandum No. 318/140/2024-GCRT Part (1) dated 13.02.2025 (https://cdnbbsr.s3waas.gov.in/s3716e1b8c6cd17b771da77391355749f3/uploads/2025/02/202502141369282676.pdf, SHA-256 `b37787b2001b67d1...`): clarifies that ground-mounted elevated installations are allowed. **It does not change any CFA amount.** No other amendment to the CFA rates was found on MNRE's PM Surya Ghar document list. |
| 2026 status | PIB press release of 24 Mar 2026 (https://www.pib.gov.in/PressReleasePage.aspx?PRID=2244670&reg=48&lang=2) confirms MNRE "is implementing" the scheme, aimed at one crore households "by FY 2026-27", 26,19,879 installations and Rs 17,967.53 crore CFA disbursed to 19.03.2026. It does not restate amounts. The scheme is therefore not marked expired. The row's `effective_to` is the guideline's own 2027-03-31 implementation end; a later extension would be added as a new version. |
| Cross-check | Tamil Nadu's DISCOM (TNPDCL) publishes a "Subsidy Structure of PM-Surya Ghar Scheme" (https://www.tnpdcl.org/static/tnpdcl/assets/files/pmsuryaghar/annuxure3.pdf, SHA-256 `7debb41c3812c56e...`): 1 kW Rs 30,000, 2 kW Rs 60,000, 3 kW and above Rs 78,000. Matches the MNRE rates. |
| Derived value | The special-category maximum (2 x 33,000 + 19,800 = Rs 85,800) is **not stated** in the guideline, so it is not stored as `maximum_amount`; the slab calculation produces it. The base maximum Rs 78,000 is stated in the guideline (example iii) and is stored. |
| Special-category membership | The guideline lists categories, not names. "States in the North East" is applied as the eight NE States (Arunachal Pradesh, Assam, Manipur, Meghalaya, Mizoram, Nagaland, Tripura, Sikkim). |
| Status | **VERIFIED** |

### B2. State incentives (Tamil Nadu, Maharashtra, Karnataka, Kerala, Rajasthan) - NOT_FOUND / NOT SEEDED

Official pages read on 2026-09-19 and what they contain:

| State | Official pages read | Finding |
|---|---|---|
| Tamil Nadu | TNPDCL PM Surya Ghar page and documents; tn.gov.in search | Only the central scheme is described. The earlier TEDA subsidy is defunct. A state top-up announced in the 2026-27 revised budget could not be found in any order, notification or agency page. **NOT_FOUND** |
| Maharashtra | Energy Department PM Surya Ghar page; MEDA grid-connected rooftop page | Central scheme only; no state amount stated. **NOT_FOUND** |
| Karnataka | KREDL and ESCOM rooftop pages | Only the historic MNRE Phase-II "Soura Gruha" scheme is described; no current state amount. **NOT_FOUND**. (KERC LT-1 note (b): a Rs 25/kW/month fixed-charge rebate for rooftop-solar homes up to 10 kW. It is a recurring tariff rebate, not a one-time incentive, so it is **not modelled**.) |
| Kerala | KSEB e-Kiran "Subsidy Scheme" downloads; ANERT solar page | Lists empanelled developers and price lists, states no subsidy amount. **NOT_FOUND** |
| Rajasthan | RRECL rooftop notice (rendered and read) | A 2021 public notice about the old MNRE Phase-II 40%/20% scheme; not a current state incentive. **NOT_FOUND** |

Other unread sources: the national portal host `solarrooftop.pmsuryaghar.gov.in` was not reachable from the research environment on 2026-09-19 (connection failure), so its state-notification list could not be checked.

### B3. DISCOM incentives

None found in an official DISCOM source. Net metering, vendor empanelment and the DISCOM incentives *paid to DISCOMs* under PM Surya Ghar are not consumer incentives and are not seeded.

---

## C. Records deliberately not created

- No average or national tariff, no assumed subsidy, no placeholder rows for states not researched.
- Kerala tariff (engine limitation), Karnataka LT-2 (ownership unknown), all non-residential categories.
- FY2027-28 Karnataka tariff (future dated).
- Rajasthan tariff before 01.10.2025 (effective date not stated in the documents read).
