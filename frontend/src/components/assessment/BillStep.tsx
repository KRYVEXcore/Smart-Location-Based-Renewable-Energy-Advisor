import { Info, Mic, Square } from 'lucide-react'
import { useVoiceBillInput } from '../../hooks/useVoiceBillInput'

interface BillStepProps {
  bill: string
  units: string
  onBillChange: (value: string) => void
  onUnitsChange: (value: string) => void
  billError?: string
  unitsError?: string
}

// Bill first: customers know what they pay, not their kWh. Units are an optional, collapsed
// advanced field; when given they are used as-is and the bill is kept alongside them.
export function BillStep({ bill, units, onBillChange, onUnitsChange, billError, unitsError }: BillStepProps) {
  const voice = useVoiceBillInput((amount) => onBillChange(String(amount)))

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-900">What is your average monthly electricity bill?</h2>
      <p className="mt-1 text-sm text-slate-500">
        Enter the average amount you normally pay for electricity each month.
      </p>

      <div className="mt-8 flex flex-col items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-10">
        <label htmlFor="bill-input" className="sr-only">
          Average monthly electricity bill in rupees
        </label>
        <div className="flex items-baseline gap-1">
          <span className="text-4xl font-bold text-slate-400" aria-hidden="true">
            ₹
          </span>
          <input
            id="bill-input"
            type="text"
            inputMode="decimal"
            autoComplete="off"
            placeholder="7500"
            value={bill}
            onChange={(event) => onBillChange(event.target.value)}
            aria-invalid={Boolean(billError)}
            aria-describedby={billError ? 'bill-error' : undefined}
            className="w-48 bg-transparent text-center text-5xl font-bold tracking-tight text-slate-900 placeholder:text-slate-300 focus:outline-none sm:text-6xl"
          />
        </div>
        <span className="text-sm font-medium uppercase tracking-wide text-slate-400">per month</span>

        {voice.supported && (
          <button
            type="button"
            onClick={voice.listening ? voice.stop : voice.start}
            aria-label={voice.listening ? 'Stop listening' : 'Say your bill amount'}
            aria-pressed={voice.listening}
            className={
              'mt-3 inline-flex items-center gap-2 rounded-full border px-4 py-2 text-sm font-semibold transition-colors focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 ' +
              (voice.listening
                ? 'animate-pulse border-emerald-600 bg-emerald-50 text-emerald-700'
                : 'border-slate-200 bg-white text-slate-600 hover:border-emerald-300 hover:text-emerald-700')
            }
          >
            {voice.listening ? <Square className="h-3.5 w-3.5" aria-hidden="true" /> : <Mic className="h-4 w-4" aria-hidden="true" />}
            {voice.listening ? 'Listening… tap to stop' : 'Say it instead'}
          </button>
        )}
      </div>

      {billError && (
        <p id="bill-error" role="alert" className="mt-3 text-sm text-red-600">
          {billError}
        </p>
      )}
      <div role="status" aria-live="polite">
        {voice.confirmation && <p className="mt-3 break-words text-sm text-emerald-700">{voice.confirmation}</p>}
        {voice.message && <p className="mt-3 break-words text-sm text-amber-700">{voice.message}</p>}
      </div>

      <details className="mt-6 rounded-2xl border border-slate-200 px-4 py-3" open={units !== '' || Boolean(unitsError)}>
        <summary className="cursor-pointer text-sm font-medium text-slate-600">
          Advanced: I know the units on my bill (optional)
        </summary>
        <label htmlFor="units-input" className="mt-3 block text-sm font-medium text-slate-700">
          Units consumed (optional)
        </label>
        <div className="mt-1 flex items-center gap-2">
          <input
            id="units-input"
            type="text"
            inputMode="decimal"
            autoComplete="off"
            placeholder="e.g. 640"
            value={units}
            onChange={(event) => onUnitsChange(event.target.value)}
            aria-invalid={Boolean(unitsError)}
            aria-describedby="units-help"
            className="w-40 rounded-xl border border-slate-200 px-3 py-2 text-base text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          />
          <span className="text-sm text-slate-500">kWh / month (1 unit = 1 kWh)</span>
        </div>
        <p id="units-help" className="mt-2 flex items-start gap-2 text-xs text-slate-500">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          You can enter the units shown on your electricity bill for a more accurate assessment. If you do, they
          are used instead of an estimate from your bill.
        </p>
        {unitsError && (
          <p role="alert" className="mt-2 text-sm text-red-600">
            {unitsError}
          </p>
        )}
      </details>
    </div>
  )
}
