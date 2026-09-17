import type { AssessmentData } from '../../types/assessment'

type ConstraintsValue = Pick<AssessmentData, 'roofAreaSqft' | 'landAreaSqft' | 'budget' | 'needsBackup'>

export interface ConstraintsFieldErrors {
  roofAreaSqft?: string
  landAreaSqft?: string
  budget?: string
}

interface ConstraintsStepProps {
  value: ConstraintsValue
  onChange: (patch: Partial<ConstraintsValue>) => void
  errors?: ConstraintsFieldErrors
}

export function ConstraintsStep({ value, onChange, errors }: ConstraintsStepProps) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-900">A few more details</h2>
      <p className="mt-1 text-sm text-slate-500">All optional — skip anything you&apos;re unsure of.</p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <div>
          <label htmlFor="roof-area" className="mb-1.5 block text-sm font-medium text-slate-700">
            Roof area (sq ft)
          </label>
          <input
            id="roof-area"
            type="number"
            min={0}
            value={value.roofAreaSqft}
            onChange={(event) => onChange({ roofAreaSqft: event.target.value })}
            placeholder="e.g. 600"
            aria-invalid={Boolean(errors?.roofAreaSqft)}
            aria-describedby={errors?.roofAreaSqft ? 'roof-area-error' : undefined}
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          />
          {errors?.roofAreaSqft && (
            <p id="roof-area-error" role="alert" className="mt-1.5 text-xs text-red-600">
              {errors.roofAreaSqft}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="land-area" className="mb-1.5 block text-sm font-medium text-slate-700">
            Available land area (sq ft)
          </label>
          <input
            id="land-area"
            type="number"
            min={0}
            value={value.landAreaSqft}
            onChange={(event) => onChange({ landAreaSqft: event.target.value })}
            placeholder="e.g. 0"
            aria-invalid={Boolean(errors?.landAreaSqft)}
            aria-describedby={errors?.landAreaSqft ? 'land-area-error' : undefined}
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          />
          {errors?.landAreaSqft && (
            <p id="land-area-error" role="alert" className="mt-1.5 text-xs text-red-600">
              {errors.landAreaSqft}
            </p>
          )}
        </div>

        <div>
          <label htmlFor="budget" className="mb-1.5 block text-sm font-medium text-slate-700">
            Budget (₹)
          </label>
          <input
            id="budget"
            type="number"
            min={0}
            value={value.budget}
            onChange={(event) => onChange({ budget: event.target.value })}
            placeholder="e.g. 200000"
            aria-invalid={Boolean(errors?.budget)}
            aria-describedby={errors?.budget ? 'budget-error' : undefined}
            className="w-full rounded-xl border border-slate-200 px-4 py-3 text-slate-900 placeholder:text-slate-400 focus:border-emerald-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/20"
          />
          {errors?.budget && (
            <p id="budget-error" role="alert" className="mt-1.5 text-xs text-red-600">
              {errors.budget}
            </p>
          )}
        </div>

        <fieldset>
          <legend className="mb-1.5 block text-sm font-medium text-slate-700">
            Backup power needed?
          </legend>
          <div className="flex gap-2">
            {[
              { label: 'Yes', selected: value.needsBackup === true },
              { label: 'No', selected: value.needsBackup === false },
            ].map((option) => (
              <button
                key={option.label}
                type="button"
                aria-pressed={option.selected}
                onClick={() => onChange({ needsBackup: option.label === 'Yes' })}
                className={`flex-1 rounded-xl border px-4 py-3 text-sm font-semibold transition-colors ${
                  option.selected
                    ? 'border-emerald-600 bg-emerald-50 text-emerald-800'
                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
              >
                {option.label}
              </button>
            ))}
          </div>
        </fieldset>
      </div>
    </div>
  )
}
