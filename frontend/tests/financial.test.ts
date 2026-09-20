// Financial analysis display: the report's savings, payback and cost breakdown, the recommendation card,
// and how a financial chat reply is rendered and spoken. Pure logic and static rendering only; no network.
import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import type { FinancialAnalysisResult } from '../src/types/financial.ts'
import type { RecommendationResult } from '../src/types/recommendation.ts'
import { recommendationView } from '../src/utils/recommendationView.ts'
import { renderRichText } from '../src/utils/richText.ts'
import { NOT_AVAILABLE, costSavingsView } from '../src/utils/reportView.ts'
import { stripMarkdownForSpeech } from '../src/voice/speech.ts'

const basis = {
  record_id: 'MNRE-PMSG-BENCHMARK-GENERAL-2024-02-13',
  cost_kind: 'benchmark',
  name: 'MNRE benchmark cost',
  source_name: 'Ministry of New and Renewable Energy (MNRE), Government of India',
  source_document: 'Guidelines for PM-Surya Ghar',
  source_url: 'https://example.invalid/guidelines.pdf',
  source_page: '8',
  source_section: 'clause g) Benchmark Cost',
  effective_from: '2024-02-13',
  capacity_basis: 'Per kW',
  geographic_scope: 'all States/UTs except: Assam',
  inclusions: 'Not stated in the guideline clause.',
  exclusions: 'Not stated in the guideline clause.',
  gst_treatment: 'Not stated in the guideline clause.',
  verification_status: 'verified',
  last_verified: '2026-09-20',
}

// TEST FIXTURE values shaped like the backend's response; the UI must show them, never recompute them.
const complete: FinancialAnalysisResult = {
  status: 'complete',
  reason: null,
  assessment_id: 'a',
  technology: 'solar',
  capacity_kw: 7,
  cost_status: 'available',
  gross_cost_range_inr: { low: 325000, high: 325000 },
  cost_basis: basis,
  incentive_inr: 78000,
  incentive_scheme: 'PM Surya Ghar',
  incentive_note: 'PM Surya Ghar, as calculated by the verified incentive data.',
  net_investment_range_inr: { low: 247000, high: 247000 },
  savings_status: 'available',
  annual_savings_inr: 61234.56,
  monthly_savings_inr: 5102.88,
  baseline_annual_bill_inr: 90000,
  annual_bill_after_solar_inr: 28765.44,
  annual_self_consumed_kwh: 9592.8,
  annual_surplus_generation_kwh: 100,
  tariff_name: 'TNPDCL LT-IA',
  tariff_version: 'v1',
  simple_payback_years_range: { low: 4, high: 4 },
  payback_note: 'Estimated simple payback = net investment / estimated annual savings.',
  methodology: [],
  limitations: [],
  calculation_version: 'financial-2026.1',
  calculated_at: '2026-01-01T00:00:00Z',
}

const unavailable: FinancialAnalysisResult = {
  ...complete,
  status: 'insufficient_data',
  reason: 'Neither a verified cost nor modelled savings is available for this system.',
  cost_status: 'not_available',
  gross_cost_range_inr: null,
  cost_basis: null,
  incentive_inr: null,
  incentive_scheme: null,
  net_investment_range_inr: null,
  savings_status: 'not_available',
  annual_savings_inr: null,
  monthly_savings_inr: null,
  simple_payback_years_range: null,
}

function recommendation(cost: RecommendationResult['cost_context']): RecommendationResult {
  return {
    recommendation_status: 'recommended',
    assessment_id: 'a',
    recommended_technology: 'solar',
    recommended_capacity_kw: 7,
    technical_feasibility: 'technically_feasible',
    annual_consumption_kwh: 9592.8,
    expected_annual_generation_kwh: 9968,
    coverage_percent: 103.9,
    target_coverage_percent: 100,
    target_met: true,
    reason_code: 'smallest_capacity_meeting_target',
    recommendation_reason: 'Smallest feasible size that reaches the target.',
    solar_options_evaluated: [],
    excluded_options: [],
    applicable_incentives: [
      {
        scheme_name: 'PM Surya Ghar',
        level: 'central',
        incentive_amount_inr: '78000.00',
        calculation_notes: null,
        effective_from: null,
        effective_to: null,
        source_name: null,
        source_order: null,
        source_page: null,
        verification_status: 'verified',
      },
    ],
    incentive_context: null,
    tariff_context: null,
    cost_context: cost,
    limitations: [],
    rules: [],
    recommendation_version: 'r',
    engine_versions: {},
    calculated_at: '2026-01-01T00:00:00Z',
  }
}

const availableCost: RecommendationResult['cost_context'] = {
  status: 'available',
  budget_inr: null,
  note: 'Estimated figures.',
  installed_cost_range_inr: { low: 325000, high: 325000 },
  incentive_inr: 78000,
  net_investment_range_inr: { low: 247000, high: 247000 },
  annual_savings_inr: 61234.56,
  monthly_savings_inr: 5102.88,
  simple_payback_years_range: { low: 4, high: 4 },
}

describe('report: estimated savings and payback come from the financial analysis', () => {
  it('shows the estimated annual and monthly savings exactly as the backend returned them', () => {
    const view = costSavingsView(recommendation(availableCost), complete)

    assert.equal(view.annualSavings, '₹61,235/year')
    assert.equal(view.monthlySavings, '₹5,103/month')
  })

  it('shows the estimated simple payback, as a single figure or as a range', () => {
    assert.equal(costSavingsView(null, complete).payback, '4.0 years')

    const ranged = { ...complete, simple_payback_years_range: { low: 3.2, high: 4.6 } }
    assert.equal(costSavingsView(null, ranged).payback, '3.2–4.6 years')
  })
})

describe('report: cost breakdown', () => {
  it('shows the gross cost, the verified incentive and the net investment', () => {
    const view = costSavingsView(recommendation(availableCost), complete)

    assert.equal(view.installedCost, '₹3,25,000')
    assert.deepEqual(view.incentiveLines, ['PM Surya Ghar: ₹78,000'])
    assert.equal(view.netInvestment, '₹2,47,000')
    assert.ok(view.basisNote.includes('benchmark') && view.basisNote.includes('not a vendor quote') && view.basisNote.includes('GST'))
  })

  it('keeps a cost range as a range, without inventing a midpoint', () => {
    const ranged = { ...complete, gross_cost_range_inr: { low: 300000, high: 350000 }, net_investment_range_inr: { low: 222000, high: 272000 } }
    const view = costSavingsView(null, ranged)

    assert.equal(view.installedCost, '₹3,00,000 – ₹3,50,000')
    assert.equal(view.netInvestment, '₹2,22,000 – ₹2,72,000')
  })

  it('states that financing and export income are not calculated', () => {
    assert.ok(costSavingsView(null, complete).financingNote.includes('Financing options not currently calculated'))
    assert.ok(costSavingsView(null, complete).financingNote.includes('export'))
  })
})

describe('report: unavailable states', () => {
  it('reads "Not available" for every missing value and never shows ₹0', () => {
    const view = costSavingsView(null, unavailable)

    for (const value of [view.installedCost, view.netInvestment, view.annualSavings, view.monthlySavings, view.payback]) {
      assert.equal(value, NOT_AVAILABLE)
    }
    assert.deepEqual(view.incentiveLines, [])
    assert.equal(view.basisNote, 'Neither a verified cost nor modelled savings is available for this system.')
    assert.ok(!JSON.stringify(view).includes('₹0'))
  })

  it('shows savings when only the cost is unavailable, and the cost as unavailable', () => {
    const view = costSavingsView(null, { ...unavailable, status: 'cost_unavailable', annual_savings_inr: 50000, monthly_savings_inr: 4166.67 })

    assert.equal(view.annualSavings, '₹50,000/year')
    assert.equal(view.installedCost, NOT_AVAILABLE)
    assert.equal(view.payback, NOT_AVAILABLE)
  })

  it('falls back to the recommendation while the analysis has not loaded', () => {
    assert.equal(costSavingsView(recommendation(availableCost), null).installedCost, '₹3,25,000')
    assert.equal(costSavingsView(null, null).installedCost, NOT_AVAILABLE)
  })
})

describe('recommendation card financials', () => {
  it('B: shows the cost, net investment, savings and payback from the verified result', () => {
    const view = recommendationView(recommendation(availableCost))

    assert.equal(view.costMessage, null)
    assert.deepEqual(view.financials, {
      installedCost: '₹3,25,000',
      netInvestment: '₹2,47,000',
      annualSavings: '₹61,235/year',
      monthlySavings: '₹5,103/month',
      payback: '4.0 years',
    })
  })

  it('A and C: keep the technical-recommendation message and show no financial figures', () => {
    const budget = 'A budget was provided, but verified system cost data is not available, so affordability cannot yet be calculated.'
    const withBudget = recommendationView(recommendation({ status: 'not_available', budget_inr: 300000, note: budget }))
    const withoutBudget = recommendationView(
      recommendation({ status: 'not_available', budget_inr: null, note: 'Verified system cost data is not currently available.' }),
    )

    assert.equal(withBudget.costMessage, `Technical recommendation. ${budget}`)
    assert.equal(withoutBudget.costMessage, 'Technical recommendation. Verified system cost data is not currently available.')
    assert.equal(withBudget.financials, null)
    assert.equal(withoutBudget.financials, null)
  })
})

describe('financial replies in chat', () => {
  const reply = '**Estimated cost: ₹3,25,000**\n- Estimated annual savings: **₹61,235**\n- Estimated simple payback: **4.0 years**'

  it('renders the figures in bold without the asterisks', () => {
    const html = renderToStaticMarkup(createElement('p', null, renderRichText(reply)))

    assert.ok(!html.includes('*'))
    assert.ok(html.includes('<strong class="font-semibold">Estimated cost: ₹3,25,000</strong>'))
    assert.ok(html.includes('• Estimated annual savings:'))
  })

  it('speaks the same reply as plain text with the figures intact', () => {
    const spoken = stripMarkdownForSpeech(reply)

    assert.ok(!/[*#]/.test(spoken))
    assert.ok(spoken.includes('₹3,25,000') && spoken.includes('₹61,235') && spoken.includes('4.0 years'))
  })
})
