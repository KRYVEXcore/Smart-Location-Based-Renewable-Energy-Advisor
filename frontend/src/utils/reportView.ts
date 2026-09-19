import type { AssessmentResponse } from '../types/assessmentApi.ts'
import type { RecommendationResult } from '../types/recommendation.ts'

// Display logic for the customer report. Pure and DOM-free so it can be tested. It only
// formats values the backend returned: a field with no deterministic source says
// "Not available" - never a zero, a guess or a placeholder number.

export const NOT_AVAILABLE = 'Not available'

const inr = (value: number) => `₹${value.toLocaleString('en-IN', { maximumFractionDigits: 0 })}`

export interface EnergyView {
  billLabel: string
  usageLabel: string | null
  // The same figure split for a metric card (big number, small unit).
  usageValue: string | null
  usageUnit: string | null
  usageKind: 'estimated' | 'entered' | 'unavailable'
  usageNote: string
}

// Bill first; usage second, and clearly labelled as derived when it is an estimate.
export function energyView(energy: AssessmentResponse['energy']): EnergyView {
  const billLabel = energy.monthly_electricity_bill_inr !== null ? inr(energy.monthly_electricity_bill_inr) : NOT_AVAILABLE
  const kwh = energy.monthly_consumption_kwh

  if (energy.consumption_source === 'user_bill_estimate') {
    if (kwh === null) {
      return {
        billLabel,
        usageLabel: null,
        usageValue: null,
        usageUnit: null,
        usageKind: 'unavailable',
        usageNote:
          energy.consumption_estimate?.reason ??
          'Usage could not be estimated from your bill because a verified applicable tariff could not be established.',
      }
    }
    const estimate = energy.consumption_estimate
    const range =
      estimate?.range_low_kwh != null && estimate.range_high_kwh != null
        ? ` (between ${Math.round(estimate.range_low_kwh)} and ${Math.round(estimate.range_high_kwh)} kWh)`
        : ''
    return {
      billLabel,
      usageLabel: `~${Math.round(kwh).toLocaleString('en-IN')} kWh/month`,
      usageValue: `~${Math.round(kwh).toLocaleString('en-IN')}`,
      usageUnit: 'kWh/month',
      usageKind: 'estimated',
      usageNote: `Estimated from your bill using the verified tariff${range} - not a meter reading.`,
    }
  }

  return {
    billLabel,
    usageLabel: kwh !== null ? `${kwh.toLocaleString('en-IN')} kWh/month` : null,
    usageValue: kwh !== null ? kwh.toLocaleString('en-IN') : null,
    usageUnit: kwh !== null ? 'kWh/month' : null,
    usageKind: 'entered',
    usageNote: 'Units you entered.',
  }
}

type CostContext = RecommendationResult['cost_context']

const range = (value: { low: number; high: number } | null | undefined) =>
  value ? `${inr(value.low)} – ${inr(value.high)}` : NOT_AVAILABLE
const amount = (value: number | null | undefined, suffix = '') => (value == null ? NOT_AVAILABLE : `${inr(value)}${suffix}`)

// Real financial values, only when a verified analysis exists. A single missing value reads "Not available".
export function financialLabels(cost: CostContext) {
  const available = cost.status === 'available'
  return {
    installedCost: available ? range(cost.installed_cost_range_inr) : NOT_AVAILABLE,
    netInvestment: available ? range(cost.net_investment_range_inr) : NOT_AVAILABLE,
    annualSavings: available ? amount(cost.annual_savings_inr, '/year') : NOT_AVAILABLE,
    monthlySavings: available ? amount(cost.monthly_savings_inr, '/month') : NOT_AVAILABLE,
    payback:
      available && cost.simple_payback_years != null ? `${cost.simple_payback_years.toFixed(1)} years` : NOT_AVAILABLE,
  }
}

export interface CostSavingsView {
  installedCost: string
  incentiveLines: string[]
  netInvestment: string
  annualSavings: string
  monthlySavings: string
  payback: string
  basisNote: string
  financingNote: string
}

// There is no Financial Analysis Engine yet, so cost, net investment, savings and payback are
// "Not available". Verified incentives come from the recommendation (Incentive Engine output).
export function costSavingsView(recommendation: RecommendationResult | null): CostSavingsView {
  const incentiveLines = (recommendation?.applicable_incentives ?? []).map((incentive) =>
    incentive.incentive_amount_inr
      ? `${incentive.scheme_name}: ${inr(Number(incentive.incentive_amount_inr))}`
      : incentive.scheme_name,
  )
  const labels = recommendation ? financialLabels(recommendation.cost_context) : null
  return {
    installedCost: labels?.installedCost ?? NOT_AVAILABLE,
    incentiveLines,
    netInvestment: labels?.netInvestment ?? NOT_AVAILABLE,
    annualSavings: labels?.annualSavings ?? NOT_AVAILABLE,
    monthlySavings: labels?.monthlySavings ?? NOT_AVAILABLE,
    payback: labels?.payback ?? NOT_AVAILABLE,
    basisNote:
      recommendation?.cost_context.status === 'available'
        ? 'Based on verified India-based cost and incentive data.'
        : (recommendation?.cost_context.note ?? 'Verified system cost data is not currently available.'),
    financingNote: 'Financing options not currently calculated.',
  }
}
