// Bill-first input: validation, spoken amounts, the payload sent to the API, and how the
// dashboard/report present derived values. Pure logic only: no DOM, no network.
import assert from 'node:assert/strict'
import { afterEach, describe, it } from 'node:test'
import { INITIAL_ASSESSMENT_DATA, type AssessmentData } from '../src/types/assessment.ts'
import type { AssessmentResponse } from '../src/types/assessmentApi.ts'
import { toAssessmentCreatePayload } from '../src/utils/assessmentMapper.ts'
import {
  interpretBillUtterance,
  parseSpokenAmountInr,
  validateMonthlyBill,
  validateOptionalUnits,
} from '../src/utils/billInput.ts'
import { NOT_AVAILABLE, costSavingsView, energyView } from '../src/utils/reportView.ts'
import type { RecommendationResult } from '../src/types/recommendation.ts'

describe('monthly bill validation', () => {
  it('accepts plain, comma and rupee-symbol amounts', () => {
    for (const raw of ['7500', '7,500', '₹7,500', 'Rs. 7500', ' 7500 ']) {
      assert.deepEqual(validateMonthlyBill(raw), { ok: true, value: 7500 }, raw)
    }
    assert.deepEqual(validateMonthlyBill('7500.50'), { ok: true, value: 7500.5 })
  })

  it('rejects zero, negative, words, letters and empty input with a clear message', () => {
    const cases: [string, string][] = [
      ['', 'Enter your average monthly electricity bill.'],
      ['0', 'The bill must be more than ₹0.'],
      ['-500', 'Enter the bill as a number in rupees, for example 7500.'],
      ['seven thousand', 'Enter the bill as a number in rupees, for example 7500.'],
      ['75oo', 'Enter the bill as a number in rupees, for example 7500.'],
    ]
    for (const [raw, message] of cases) assert.deepEqual(validateMonthlyBill(raw), { ok: false, message }, raw)
  })

  it('rejects an unrealistically large amount', () => {
    const result = validateMonthlyBill('10000000')

    assert.equal(result.ok, false)
    assert.ok(!result.ok && result.message.includes('too high'))
    assert.equal(validateMonthlyBill('1000000').ok, true)
  })

  it('keeps units optional: empty means not provided, never zero', () => {
    assert.deepEqual(validateOptionalUnits(''), { ok: true, value: null })
    assert.deepEqual(validateOptionalUnits('640'), { ok: true, value: 640 })
    assert.deepEqual(validateOptionalUnits('640 kWh'), { ok: true, value: 640 })
    assert.equal(validateOptionalUnits('0').ok, false)
    assert.equal(validateOptionalUnits('lots').ok, false)
  })
})

describe('speaking the bill', () => {
  const originalFetch = globalThis.fetch
  afterEach(() => {
    globalThis.fetch = originalFetch
  })

  it('reads spoken amounts', () => {
    const cases: [string, number][] = [
      ['my electricity bill is around seven thousand five hundred rupees a month', 7500],
      ['7500', 7500],
      ['rupees 7,500', 7500],
      ['twelve thousand', 12000],
      ['seven and a half thousand', 7500],
      ['two thousand three hundred and fifty', 2350],
      ['one lakh', 100000],
      ['7.5k', 7500],
      ['about 3 thousand', 3000],
    ]
    for (const [text, amount] of cases) assert.equal(parseSpokenAmountInr(text), amount, text)
    assert.equal(parseSpokenAmountInr('I am not sure what it is'), null)
  })

  it('does not mistake units for thousands', () => {
    assert.equal(parseSpokenAmountInr('7500 kwh'), 7500)
  })

  it('turns a sentence into a validated amount and a fixed confirmation, with no request of any kind', () => {
    globalThis.fetch = () => {
      throw new Error('speech must never trigger a network or AI request')
    }

    const outcome = interpretBillUtterance('My electricity bill is around seven thousand five hundred rupees a month.')

    assert.equal(outcome.kind, 'amount')
    assert.ok(outcome.kind === 'amount' && outcome.amount === 7500)
    assert.ok(
      outcome.kind === 'amount' &&
        outcome.confirmation ===
          "Got it. Your average monthly electricity bill is ₹7,500. I'll use your location and tariff data to estimate your energy use and evaluate renewable options.",
    )
  })

  it('validates what was said before it can fill the field', () => {
    const huge = interpretBillUtterance('fifty lakh rupees')
    const nonsense = interpretBillUtterance('hello there')

    assert.equal(huge.kind, 'invalid')
    assert.ok(huge.kind === 'invalid' && huge.message.includes('too high'))
    assert.equal(nonsense.kind, 'invalid')
  })
})

const base: AssessmentData = {
  ...INITIAL_ASSESSMENT_DATA,
  latitude: 13.08,
  longitude: 80.27,
  locationQuery: 'Chennai, Tamil Nadu, India',
  buildingType: 'home',
}

describe('assessment payload', () => {
  it('sends the bill and no invented kWh', () => {
    const payload = toAssessmentCreatePayload({ ...base, monthlyBillInr: '7,500' })

    assert.deepEqual(payload.energy, { monthly_electricity_bill_inr: 7500 })
    assert.ok(!('monthly_consumption_kwh' in payload.energy))
  })

  it('keeps both values when the customer also enters units', () => {
    const payload = toAssessmentCreatePayload({ ...base, monthlyBillInr: '7500', monthlyUnitsKwh: '640' })

    assert.deepEqual(payload.energy, { monthly_electricity_bill_inr: 7500, monthly_consumption_kwh: 640 })
  })

  it('refuses to build a payload from an invalid bill', () => {
    assert.throws(() => toAssessmentCreatePayload({ ...base, monthlyBillInr: '' }), /Enter your average monthly electricity bill/)
    assert.throws(() => toAssessmentCreatePayload({ ...base, monthlyBillInr: 'seven thousand' }), /number in rupees/)
    assert.throws(() => toAssessmentCreatePayload({ ...base, monthlyBillInr: '7500', monthlyUnitsKwh: '0' }), /more than 0/)
  })

  it('starts empty: there is no default bill or consumption', () => {
    assert.equal(INITIAL_ASSESSMENT_DATA.monthlyBillInr, '')
    assert.equal(INITIAL_ASSESSMENT_DATA.monthlyUnitsKwh, '')
  })
})

const energy = (patch: Partial<AssessmentResponse['energy']>): AssessmentResponse['energy'] => ({
  id: 'e',
  monthly_consumption_kwh: 799.4,
  annual_consumption_kwh: null,
  monthly_electricity_bill_inr: 7500,
  consumption_source: 'user_bill_estimate',
  consumption_estimate: null,
  ...patch,
})

describe('dashboard: the bill leads and usage is labelled as derived', () => {
  it('shows the bill, then usage marked as an estimate', () => {
    const view = energyView(energy({}))

    assert.equal(view.billLabel, '₹7,500')
    assert.equal(view.usageLabel, '~799 kWh/month')
    assert.equal(view.usageKind, 'estimated')
    assert.ok(view.usageNote.includes('Estimated') && view.usageNote.includes('not a meter reading'))
  })

  it('shows units the customer entered without the estimate marker', () => {
    const view = energyView(energy({ consumption_source: 'user_kwh', monthly_consumption_kwh: 640 }))

    assert.equal(view.usageLabel, '640 kWh/month')
    assert.equal(view.usageKind, 'entered')
    assert.ok(!view.usageLabel?.startsWith('~'))
  })

  it('reports an unavailable estimate honestly instead of showing a number', () => {
    const reason =
      'Bill-based consumption estimate unavailable for this location because a verified applicable tariff could not be established.'
    const view = energyView(
      energy({
        monthly_consumption_kwh: null,
        consumption_estimate: {
          status: 'insufficient_data',
          reason,
          monthly_bill_inr: 7500,
          estimated_monthly_consumption_kwh: null,
          range_low_kwh: null,
          range_high_kwh: null,
          match: null,
          method: 'm',
          tariff_name: null,
          tariff_version: null,
          limitations: [],
        },
      }),
    )

    assert.equal(view.usageKind, 'unavailable')
    assert.equal(view.usageLabel, null)
    assert.equal(view.usageNote, reason)
    assert.equal(view.billLabel, '₹7,500')
  })

  it('never shows a zero for a missing bill', () => {
    assert.equal(energyView(energy({ monthly_electricity_bill_inr: null })).billLabel, NOT_AVAILABLE)
  })
})

describe('report: cost, savings and payback are only shown when a deterministic source exists', () => {
  const recommendation = {
    applicable_incentives: [
      { scheme_name: 'PM Surya Ghar', incentive_amount_inr: '78000.00' },
    ],
    cost_context: { note: 'Verified system cost is not currently available, so savings and payback are not calculated.' },
  } as unknown as RecommendationResult

  it('says "Not available" for everything the financial engine will provide', () => {
    const view = costSavingsView(recommendation)

    for (const value of [view.installedCost, view.netInvestment, view.annualSavings, view.monthlySavings, view.payback]) {
      assert.equal(value, NOT_AVAILABLE)
    }
    assert.deepEqual(view.incentiveLines, ['PM Surya Ghar: ₹78,000'])
    assert.equal(view.financingNote, 'Financing options not currently calculated.')
  })

  it('handles a missing recommendation safely with no fake zeros', () => {
    const view = costSavingsView(null)
    const shown = JSON.stringify(view)

    assert.deepEqual(view.incentiveLines, [])
    assert.equal(view.installedCost, NOT_AVAILABLE)
    assert.ok(!/₹0\b/.test(shown) && !/"0"/.test(shown))
  })
})
