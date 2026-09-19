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
  return {
    installedCost: NOT_AVAILABLE,
    incentiveLines,
    netInvestment: NOT_AVAILABLE,
    annualSavings: NOT_AVAILABLE,
    monthlySavings: NOT_AVAILABLE,
    payback: NOT_AVAILABLE,
    basisNote:
      recommendation?.cost_context.note ??
      'Verified system cost is not currently available, so savings and payback are not calculated.',
    financingNote: 'Financing options not currently calculated.',
  }
}
