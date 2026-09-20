// The Recommendation Card's cost message across the three financial states. Pure logic only.
import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import type { RecommendationResult } from '../src/types/recommendation.ts'
import { recommendationView } from '../src/utils/recommendationView.ts'
import { NOT_AVAILABLE, costSavingsView } from '../src/utils/reportView.ts'

// The backend's own wording (see engines/recommendation/assumptions.py).
const BUDGET_NOTE =
  'A budget was provided, but verified system cost data is not available, so affordability cannot yet be calculated.'
const NO_COST_NOTE = 'Verified system cost data is not currently available.'

function result(cost: Partial<RecommendationResult['cost_context']> & { note: string }): RecommendationResult {
  return {
    recommendation_status: 'recommended',
    assessment_id: 'a',
    recommended_technology: 'solar',
    recommended_capacity_kw: 3,
    technical_feasibility: 'technically_feasible',
    annual_consumption_kwh: 3600,
    expected_annual_generation_kwh: 4288.9,
    coverage_percent: 119.1,
    target_coverage_percent: 100,
    target_met: true,
    reason_code: 'smallest_capacity_meeting_target',
    recommendation_reason: 'Smallest feasible size that reaches the target.',
    solar_options_evaluated: [],
    excluded_options: [],
    applicable_incentives: [],
    incentive_context: null,
    tariff_context: null,
    cost_context: { status: 'not_available', budget_inr: null, ...cost },
    limitations: [],
    rules: [],
    recommendation_version: 'r',
    engine_versions: {},
    calculated_at: '2026-01-01T00:00:00Z',
  }
}

const stateA = result({ budget_inr: 300000, note: BUDGET_NOTE })
const stateC = result({ budget_inr: null, note: NO_COST_NOTE })
// A future verified financial analysis fills these in; nothing here is computed by the UI.
const stateB = result({
  status: 'available',
  budget_inr: 300000,
  note: '',
  installed_cost_range_inr: { low: 180000, high: 210000 },
  net_investment_range_inr: { low: 102000, high: 132000 },
  annual_savings_inr: 84000,
  monthly_savings_inr: 7000,
  incentive_inr: 78000,
  simple_payback_years_range: { low: 1.4, high: 1.4 },
})

describe('cost message on the recommendation card', () => {
  it('A: budget provided, cost unavailable -> the exact technical-recommendation message (not an error)', () => {
    const view = recommendationView(stateA)

    assert.equal(
      view.costMessage,
      'Technical recommendation. A budget was provided, but verified system cost data is not available, so affordability cannot yet be calculated.',
    )
    assert.equal(view.financials, null)
  })

  it('B: verified cost available -> real financial values shown and the unavailable message hidden', () => {
    const view = recommendationView(stateB)

    assert.equal(view.costMessage, null)
    assert.deepEqual(view.financials, {
      installedCost: '₹1,80,000 – ₹2,10,000',
      netInvestment: '₹1,02,000 – ₹1,32,000',
      annualSavings: '₹84,000/year',
      monthlySavings: '₹7,000/month',
      payback: '1.4 years',
    })
  })

  it('C: no budget, cost unavailable -> the shorter limitation without any budget wording', () => {
    const view = recommendationView(stateC)

    assert.equal(view.costMessage, 'Technical recommendation. Verified system cost data is not currently available.')
    assert.ok(!view.costMessage?.includes('budget'))
  })

  it('the recommendation stays visible in every financial state', () => {
    for (const state of [stateA, stateB, stateC]) {
      const view = recommendationView(state)

      assert.equal(view.recommended, true)
      assert.equal(view.technologyLabel, 'Rooftop Solar')
      assert.equal(view.capacityLabel, '3 kW')
      assert.equal(view.generationLabel, '4,288.9 kWh/year')
    }
  })

  it('never fabricates affordability or figures while cost is unavailable', () => {
    for (const state of [stateA, stateC]) {
      const view = recommendationView(state)
      const report = costSavingsView(state)

      assert.equal(view.financials, null)
      assert.ok(!/\d/.test(view.costMessage ?? ''))
      for (const value of [report.installedCost, report.netInvestment, report.annualSavings, report.monthlySavings, report.payback]) {
        assert.equal(value, NOT_AVAILABLE)
      }
    }
  })

  it('a single missing verified value reads "Not available", never zero', () => {
    const partial = result({ status: 'available', note: '', annual_savings_inr: 84000 })
    const view = recommendationView(partial)

    assert.equal(view.financials?.annualSavings, '₹84,000/year')
    assert.equal(view.financials?.installedCost, NOT_AVAILABLE)
    assert.equal(view.financials?.payback, NOT_AVAILABLE)
  })

  it('the dashboard cost section reports available values only when verified', () => {
    const report = costSavingsView(stateB)

    assert.equal(report.installedCost, '₹1,80,000 – ₹2,10,000')
    assert.equal(report.payback, '1.4 years')
    assert.equal(report.basisNote, 'Based on verified India-based cost and incentive data.')
  })
})
