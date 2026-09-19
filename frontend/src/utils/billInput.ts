// The customer's electricity bill is the primary assessment input. Everything here is pure
// (no DOM, no network): validation, and turning what someone SAYS into a bill amount. Speech
// recognition only produces text; the app parses and validates it here, so no AI request is
// ever made to turn speech into a number.

export const MAX_MONTHLY_BILL_INR = 1_000_000
export const MAX_MONTHLY_UNITS_KWH = 500_000

const rupees = (value: number) => `₹${value.toLocaleString('en-IN')}`

export type BillValidation = { ok: true; value: number } | { ok: false; message: string }
export type UnitsValidation = { ok: true; value: number | null } | { ok: false; message: string }

// Accepts "7500", "7,500", "₹7,500", "Rs. 7500", "7500.50". Words and other characters are rejected.
function parseTypedNumber(raw: string): number | null {
  const cleaned = raw
    .trim()
    .replace(/^(₹|rs\.?|inr)\s*/i, '')
    .replace(/,/g, '')
  return /^\d+(\.\d+)?$/.test(cleaned) ? Number(cleaned) : null
}

export function validateMonthlyBill(raw: string): BillValidation {
  if (raw.trim() === '') return { ok: false, message: 'Enter your average monthly electricity bill.' }
  const value = parseTypedNumber(raw)
  if (value === null) return { ok: false, message: 'Enter the bill as a number in rupees, for example 7500.' }
  if (value <= 0) return { ok: false, message: 'The bill must be more than ₹0.' }
  if (value > MAX_MONTHLY_BILL_INR) {
    return { ok: false, message: `That amount looks too high (the maximum is ${rupees(MAX_MONTHLY_BILL_INR)} a month). Please check it.` }
  }
  return { ok: true, value }
}

// Units are optional: empty means "not provided", never zero.
export function validateOptionalUnits(raw: string): UnitsValidation {
  if (raw.trim() === '') return { ok: true, value: null }
  const value = parseTypedNumber(raw.replace(/\s*(kwh|units?)$/i, ''))
  if (value === null) return { ok: false, message: 'Enter the units as a number, for example 640.' }
  if (value <= 0) return { ok: false, message: 'Units must be more than 0.' }
  if (value > MAX_MONTHLY_UNITS_KWH) return { ok: false, message: 'That number of units looks too high. Please check it.' }
  return { ok: true, value }
}

// ---- spoken amounts -------------------------------------------------------------------------

const ONES: Record<string, number> = {
  zero: 0, one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8, nine: 9, ten: 10,
  eleven: 11, twelve: 12, thirteen: 13, fourteen: 14, fifteen: 15, sixteen: 16, seventeen: 17,
  eighteen: 18, nineteen: 19,
}
const TENS: Record<string, number> = {
  twenty: 20, thirty: 30, forty: 40, fifty: 50, sixty: 60, seventy: 70, eighty: 80, ninety: 90,
}
const SCALES: Record<string, number> = { hundred: 100, thousand: 1_000, lakh: 100_000, lakhs: 100_000, lac: 100_000 }

// "seven thousand five hundred" -> 7500. Returns null when no number can be read.
function parseNumberWords(words: string[]): number | null {
  let total = 0
  let current = 0
  let seen = false
  for (const word of words) {
    if (word === 'and' || word === 'a') continue
    if (word in ONES) {
      current += ONES[word] as number
    } else if (word in TENS) {
      current += TENS[word] as number
    } else if (word === 'hundred') {
      current = (current || 1) * 100
    } else if (word in SCALES) {
      total += (current || 1) * (SCALES[word] as number)
      current = 0
    } else {
      continue // filler such as "around", "rupees", "per", "month"
    }
    seen = true
  }
  return seen ? total + current : null
}

export function parseSpokenAmountInr(text: string): number | null {
  const lower = text.toLowerCase().replace(/(\d),(?=\d)/g, '$1').replace(/[₹,]/g, ' ').replace(/\s+/g, ' ')

  // Digits win: "7500", "7500.50", "7.5k", "1.2 lakh".
  const digits = lower.match(/(\d+(?:\.\d+)?)\s*(k|thousand|lakhs|lakh|lac)?\b/)
  if (digits) {
    const base = Number(digits[1])
    const unit = digits[2]
    const scale = unit === 'k' || unit === 'thousand' ? 1_000 : unit ? 100_000 : 1
    return base * scale
  }

  // "seven and a half thousand"
  const half = lower.match(/([a-z ]+?) and a half (thousand|lakhs|lakh|lac)/)
  if (half) {
    const whole = parseNumberWords((half[1] as string).split(' '))
    if (whole !== null) return (whole + 0.5) * (SCALES[half[2] as string] as number)
  }

  return parseNumberWords(lower.split(' '))
}

export type BillUtterance =
  | { kind: 'amount'; amount: number; confirmation: string }
  | { kind: 'invalid'; message: string }

// The spoken confirmation is fixed text: it is the application talking, not a model reply.
export function interpretBillUtterance(text: string): BillUtterance {
  const parsed = parseSpokenAmountInr(text)
  if (parsed === null) {
    return { kind: 'invalid', message: "I couldn't catch an amount. Try saying it like \"seven thousand five hundred rupees\", or type it." }
  }
  const checked = validateMonthlyBill(String(parsed))
  if (!checked.ok) return { kind: 'invalid', message: checked.message }
  return {
    kind: 'amount',
    amount: checked.value,
    confirmation: `Got it. Your average monthly electricity bill is ${rupees(checked.value)}. I'll use your location and tariff data to estimate your energy use and evaluate renewable options.`,
  }
}
