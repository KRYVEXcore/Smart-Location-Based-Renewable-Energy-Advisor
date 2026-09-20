import type { AssessmentResponse } from '../types/assessmentApi.ts'
import type { FinancialAnalysisResult, Range } from '../types/financial.ts'
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

// A range is shown as a range; a single verified figure (low == high) is shown once, never as a made-up span.
const rupeeRange = (value: Range | null | undefined) =>
  !value ? NOT_AVAILABLE : value.low === value.high ? inr(value.low) : `${inr(value.low)} – ${inr(value.high)}`
const amount = (value: number | null | undefined, suffix = '') => (value == null ? NOT_AVAILABLE : `${inr(value)}${suffix}`)
const yearsRange = (value: Range | null | undefined) =>
  !value
    ? NOT_AVAILABLE
    : value.low === value.high
      ? `${value.low.toFixed(1)} years`
      : `${value.low.toFixed(1)}–${value.high.toFixed(1)} years`

// The financial fields the recommendation's cost_context and the financial-analysis result share.
export interface FinancialFields {
  installed_cost_range_inr?: Range | null
  net_investment_range_inr?: Range | null
  annual_savings_inr?: number | null
  monthly_savings_inr?: number | null
  simple_payback_years_range?: Range | null
}

// Backend values only. A single missing value reads "Not available"; nothing is calculated here.
export function financialLabels(fields: FinancialFields) {
  return {
    installedCost: rupeeRange(fields.installed_cost_range_inr),
    netInvestment: rupeeRange(fields.net_investment_range_inr),
    annualSavings: amount(fields.annual_savings_inr, '/year'),
    monthlySavings: amount(fields.monthly_savings_inr, '/month'),
    payback: yearsRange(fields.simple_payback_years_range),
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

// Values come from the backend's Financial Analysis Engine (the financial-analysis endpoint; the
// recommendation's cost_context is the fallback while it is not loaded). Verified incentives come from the
// Incentive Engine via the recommendation.
export function costSavingsView(
  recommendation: RecommendationResult | null,
  financial: FinancialAnalysisResult | null = null,
): CostSavingsView {
  const incentiveLines =
    financial?.incentive_inr != null && financial.incentive_scheme
      ? [`${financial.incentive_scheme}: ${inr(financial.incentive_inr)}`]
      : (recommendation?.applicable_incentives ?? []).map((incentive) =>
          incentive.incentive_amount_inr
            ? `${incentive.scheme_name}: ${inr(Number(incentive.incentive_amount_inr))}`
            : incentive.scheme_name,
        )
  const fields: FinancialFields | null = financial
    ? {
        installed_cost_range_inr: financial.gross_cost_range_inr,
        net_investment_range_inr: financial.net_investment_range_inr,
        annual_savings_inr: financial.annual_savings_inr,
        monthly_savings_inr: financial.monthly_savings_inr,
        simple_payback_years_range: financial.simple_payback_years_range,
      }
    : (recommendation?.cost_context ?? null)
  const labels = fields ? financialLabels(fields) : null
  const basis = financial?.cost_basis
  return {
    installedCost: labels?.installedCost ?? NOT_AVAILABLE,
    incentiveLines,
    netInvestment: labels?.netInvestment ?? NOT_AVAILABLE,
    annualSavings: labels?.annualSavings ?? NOT_AVAILABLE,
    monthlySavings: labels?.monthlySavings ?? NOT_AVAILABLE,
    payback: labels?.payback ?? NOT_AVAILABLE,
    basisNote: basis
      ? `Cost is an estimate from the ${basis.source_name} benchmark (effective ${basis.effective_from}), not a vendor quote. GST: ${basis.gst_treatment}`
      : recommendation?.cost_context.status === 'available'
        ? 'Based on verified India-based cost and incentive data.'
        : (financial?.reason ?? recommendation?.cost_context.note ?? 'Verified system cost data is not currently available.'),
    financingNote: 'Financing options not currently calculated. Surplus (export) generation is not valued. All figures are estimates.',
  }
}
