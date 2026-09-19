import { Pencil } from 'lucide-react'
import type { AssessmentData } from '../../types/assessment'
import { BUILDING_TYPE_OPTIONS } from '../../types/assessment'
import { validateMonthlyBill, validateOptionalUnits } from '../../utils/billInput'

interface ReviewStepProps {
  data: AssessmentData
  onEditStep: (step: number) => void
}

function formatOptionalNumber(value: string, unit: string): string {
  return value.trim() === '' ? 'Not provided' : `${Number(value).toLocaleString('en-IN')} ${unit}`
}

function Row({
  label,
  value,
  onEdit,
}: {
  label: string
  value: string
  onEdit: () => void
}) {
  return (
    <div className="flex items-center justify-between gap-4 border-b border-slate-100 py-4 last:border-b-0">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">{label}</p>
        <p className="mt-0.5 text-sm font-medium text-slate-900">{value}</p>
      </div>
      <button
        type="button"
        onClick={onEdit}
        className="flex shrink-0 items-center gap-1 rounded-full px-3 py-1.5 text-xs font-semibold text-slate-500 hover:bg-slate-100 hover:text-slate-700"
      >
        <Pencil className="h-3.5 w-3.5" aria-hidden="true" />
        Edit
      </button>
    </div>
  )
}

export function ReviewStep({ data, onEditStep }: ReviewStepProps) {
  const buildingLabel =
    BUILDING_TYPE_OPTIONS.find((option) => option.value === data.buildingType)?.label ?? 'Not selected'
  const locationLabel = data.locationQuery || 'Not selected'
  const billCheck = validateMonthlyBill(data.monthlyBillInr)
  const unitsCheck = validateOptionalUnits(data.monthlyUnitsKwh)

  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-900">Review your assessment</h2>
      <p className="mt-1 text-sm text-slate-500">
        Check these values before submitting — this is exactly what will be saved.
      </p>

      <div className="mt-6 rounded-2xl border border-slate-200 px-5">
        <Row label="Location" value={locationLabel} onEdit={() => onEditStep(1)} />
        <Row label="Building" value={buildingLabel} onEdit={() => onEditStep(2)} />
        <Row
          label="Monthly electricity bill"
          value={billCheck.ok ? `₹${billCheck.value.toLocaleString('en-IN')}` : 'Not entered'}
          onEdit={() => onEditStep(3)}
        />
        <Row
          label="Units (optional)"
          value={
            unitsCheck.ok && unitsCheck.value !== null
              ? `${unitsCheck.value.toLocaleString('en-IN')} kWh/month`
              : 'Not provided — usage will be estimated from your bill'
          }
          onEdit={() => onEditStep(3)}
        />
        <Row label="Roof area" value={formatOptionalNumber(data.roofAreaSqft, 'sq ft')} onEdit={() => onEditStep(4)} />
        <Row label="Land area" value={formatOptionalNumber(data.landAreaSqft, 'sq ft')} onEdit={() => onEditStep(4)} />
        <Row
          label="Budget"
          value={data.budget.trim() === '' ? 'Not provided' : `₹${Number(data.budget).toLocaleString('en-IN')}`}
          onEdit={() => onEditStep(4)}
        />
        <Row label="Backup power" value={data.needsBackup ? 'Yes' : 'No'} onEdit={() => onEditStep(4)} />
      </div>
    </div>
  )
}
