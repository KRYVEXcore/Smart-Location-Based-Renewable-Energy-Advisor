// Chat formatting and recommendation display logic. React elements are rendered to a
// string with react-dom/server (no DOM), so the actual output is checked. No network.
import assert from 'node:assert/strict'
import { describe, it } from 'node:test'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { renderRichText, splitBold } from '../src/utils/richText.ts'
import { recommendationView } from '../src/utils/recommendationView.ts'
import { stripMarkdownForSpeech } from '../src/voice/speech.ts'
import type { RecommendationResult } from '../src/types/recommendation.ts'

const html = (text: string) => renderToStaticMarkup(createElement('p', null, renderRichText(text)))

describe('advisor message formatting', () => {
  it('renders **bold** without showing the asterisks', () => {
    const out = html('**Capacity 1 kW** is **technically feasible**.')

    assert.equal(out, '<p><strong class="font-semibold">Capacity 1 kW</strong> is <strong class="font-semibold">technically feasible</strong>.</p>')
    assert.ok(!out.includes('*'))
  })

  it('leaves ordinary text unchanged', () => {
    assert.equal(html('Your annual use is 3,600 kWh (about 300 a month).'), '<p>Your annual use is 3,600 kWh (about 300 a month).</p>')
    assert.deepEqual(splitBold('no formatting here'), [{ text: 'no formatting here', bold: false }])
  })

  it('preserves line breaks', () => {
    const out = html('Why:\nFirst reason\n\nSecond paragraph')

    assert.equal(out, '<p>Why:\nFirst reason\n\nSecond paragraph</p>')
  })

  it('keeps list lines readable without markdown markers', () => {
    const out = html('Why:\n- **Roof** is sufficient\n* Wind is not selected\n1. Numbered stays')

    assert.equal(
      out,
      '<p>Why:\n• <strong class="font-semibold">Roof</strong> is sufficient\n• Wind is not selected\n1. Numbered stays</p>',
    )
  })

  it('shows malicious HTML as text, never as markup', () => {
    const attack = '<script>alert(1)</script> <img src=x onerror=alert(2)> **<b>x</b>**'
    const out = html(attack)

    assert.ok(!out.includes('<script'))
    assert.ok(!out.includes('<img'))
    assert.ok(!out.includes('<b>'))
    assert.ok(out.includes('&lt;script&gt;alert(1)&lt;/script&gt;'))
    assert.ok(out.includes('<strong class="font-semibold">&lt;b&gt;x&lt;/b&gt;</strong>'))
  })

  it('leaves an unmatched marker alone instead of swallowing text', () => {
    assert.equal(html('a ** b'), '<p>a ** b</p>')
  })
})

describe('recommendation replies stay speakable', () => {
  it('speaks the same reply as clean plain text', () => {
    const reply = '**Based on your assessment, I recommend a 3 kW rooftop solar system.**\n- Estimated generation: **4,288.9 kWh/year**\n# Note'

    const spoken = stripMarkdownForSpeech(reply)

    assert.ok(!/[*#]/.test(spoken))
    assert.ok(spoken.includes('3 kW rooftop solar system'))
    assert.ok(spoken.includes('4,288.9 kWh/year'))
  })
})

const recommended: RecommendationResult = {
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
  recommendation_reason: 'Smallest evaluated solar capacity that is technically feasible and reaches the 100% annual coverage target.',
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
  incentive_context: { status: 'ok', eligible_programmes: 1, note: '1 verified programme(s) apply to this system.' },
  tariff_context: null,
  cost_context: {
    status: 'not_available',
    budget_inr: null,
    note: 'Verified system cost is not currently available, so savings and payback are not calculated.',
  },
  limitations: [],
  rules: [],
  recommendation_version: 'recommendation-2026.1',
  engine_versions: {},
  calculated_at: '2026-01-01T00:00:00Z',
}

describe('recommendation card content', () => {
  it('shows the backend recommendation as labels', () => {
    const view = recommendationView(recommended)

    assert.equal(view.recommended, true)
    assert.equal(view.technologyLabel, 'Rooftop Solar')
    assert.equal(view.capacityLabel, '3 kW')
    assert.equal(view.generationLabel, '4,288.9 kWh/year')
    assert.equal(view.coverageLabel, '119.1% of annual use')
    assert.equal(view.feasibilityLabel, 'Technically feasible')
    assert.equal(view.targetNote, null)
    assert.deepEqual(view.incentiveLines, ['PM Surya Ghar: ₹78,000'])
    assert.ok(view.costMessage?.includes('not currently available'))
  })

  it('says when the target is not fully reached', () => {
    const view = recommendationView({ ...recommended, target_met: false, coverage_percent: 41.5 })

    assert.equal(view.targetNote, 'Does not fully reach the 100% target')
    assert.equal(view.coverageLabel, '41.5% of annual use')
  })

  it('shows nothing recommended when the backend recommends nothing', () => {
    const view = recommendationView({
      ...recommended,
      recommendation_status: 'insufficient_data',
      recommended_technology: null,
      recommended_capacity_kw: null,
      expected_annual_generation_kwh: null,
      coverage_percent: null,
      technical_feasibility: null,
      applicable_incentives: [],
      recommendation_reason: 'No recommendation can be made because the roof area is missing.',
    })

    assert.equal(view.recommended, false)
    assert.equal(view.capacityLabel, null)
    assert.equal(view.generationLabel, null)
    assert.equal(view.reason, 'No recommendation can be made because the roof area is missing.')
  })
})
