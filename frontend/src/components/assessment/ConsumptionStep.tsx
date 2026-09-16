const MIN_KWH = 50
const MAX_KWH = 5000

interface ConsumptionStepProps {
  value: number
  onChange: (value: number) => void
}

export function ConsumptionStep({ value, onChange }: ConsumptionStepProps) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-900">How much electricity do you use?</h2>
      <p className="mt-1 text-sm text-slate-500">Check a recent electricity bill for this figure.</p>

      <div className="mt-8 flex flex-col items-center gap-2 rounded-2xl border border-slate-200 bg-slate-50 py-10">
        <label htmlFor="consumption-input" className="sr-only">
          Monthly electricity consumption in kilowatt-hours
        </label>
        <input
          id="consumption-input"
          type="number"
          min={0}
          value={value}
          onChange={(event) => onChange(Number(event.target.value))}
          className="w-48 bg-transparent text-center text-6xl font-bold tracking-tight text-slate-900 focus:outline-none"
        />
        <span className="text-sm font-medium uppercase tracking-wide text-slate-400">
          kWh / month
        </span>
      </div>

      <input
        type="range"
        min={MIN_KWH}
        max={MAX_KWH}
        step={10}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        aria-label="Monthly electricity consumption slider"
        className="mt-6 w-full accent-emerald-600"
      />
      <div className="mt-1 flex justify-between text-xs text-slate-400">
        <span>{MIN_KWH} kWh</span>
        <span>{MAX_KWH} kWh</span>
      </div>
    </div>
  )
}
