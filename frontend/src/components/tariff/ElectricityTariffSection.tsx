import { Info } from 'lucide-react'
import { SourceEvidence } from '../common/SourceEvidence'
import type { ChargeComponentName, TariffCalculationResponse } from '../../types/tariff'

interface ElectricityTariffSectionProps {
  result: TariffCalculationResponse
}

const COMPONENT_LABELS: Record<ChargeComponentName, string> = {
  energy: 'Energy charge',
  fixed: 'Fixed / service charge',
  demand: 'Demand charge',
  wheeling: 'Wheeling charge',
  tod: 'Time-of-day charge',
}

function formatInr(amount: string): string {
  const value = Number(amount)
  return Number.isFinite(value)
    ? `₹${value.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
    : `₹${amount}`
}

function EmptyState({ heading, reason }: { heading: string; reason: string | null }) {
  return (
    <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center">
      <p className="text-sm font-medium text-slate-500">{heading}</p>
      {reason && <p className="mt-1 text-xs text-slate-400">{reason}</p>}
    </div>
  )
}

export function ElectricityTariffSection({ result }: ElectricityTariffSectionProps) {
  if (result.status === 'insufficient_data') {
    return <EmptyState heading="Electricity tariff data is not available yet." reason={result.reason} />
  }

  if (result.status === 'discom_ambiguous') {
    return (
      <EmptyState
        heading="The electricity distribution company for this location could not be determined."
        reason={result.reason}
      />
    )
  }

  if (result.status === 'tariff_not_configured') {
    return (
      <EmptyState
        heading="No verified electricity tariff is configured for this location."
        reason={result.reason}
      />
    )
  }

  return (
    <div>
      <div className="flex flex-wrap items-center gap-x-6 gap-y-1 text-sm text-slate-500">
        {result.tariff && (
          <span>
            {result.tariff.tariff_name}
            {result.location?.discom_name ? ` — ${result.location.discom_name}` : ''}
          </span>
        )}
        {result.consumer_category && <span className="capitalize">{result.consumer_category.replace(/_/g, ' ')}</span>}
      </div>

      <div className="mt-5 overflow-hidden rounded-2xl border border-slate-200">
        {result.charges.map((charge) => (
          <div
            key={charge.component}
            className="flex items-center justify-between gap-4 border-b border-slate-100 px-4 py-3 last:border-b-0"
          >
            <div>
              <p className="text-sm font-medium text-slate-700">{COMPONENT_LABELS[charge.component]}</p>
              {charge.notes && <p className="mt-0.5 text-xs text-slate-400">{charge.notes}</p>}
            </div>
            <p
              className={
                charge.status === 'included' ? 'text-sm font-semibold text-slate-900' : 'text-xs text-slate-400'
              }
            >
              {charge.status === 'included' && charge.amount_inr
                ? formatInr(charge.amount_inr)
                : charge.status === 'not_included'
                  ? 'Not included'
                  : 'Not calculated'}
            </p>
          </div>
        ))}
      </div>

      <div className="mt-4 flex items-center justify-between rounded-2xl bg-slate-900 px-5 py-4 text-white">
        <span className="text-sm font-medium">Estimated monthly bill</span>
        <span className="text-lg font-bold">
          {result.estimated_monthly_bill_inr ? formatInr(result.estimated_monthly_bill_inr) : '—'}
        </span>
      </div>

      {result.is_partial_estimate && (
        <p className="mt-3 flex items-start gap-2 rounded-xl bg-amber-50 px-4 py-3 text-xs text-amber-700">
          <Info className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
          This is a partial estimate — some charge components ({result.excluded_components.join(', ').replace(/_/g, ' ')})
          could not be calculated from the data this assessment collects.
        </p>
      )}

      {result.tariff && (
        <SourceEvidence
          verificationStatus={result.tariff.verification_status}
          organisation={result.tariff.source_name}
          document={result.tariff.source_document}
          orderNumber={result.tariff.source_order_number}
          orderDate={result.tariff.source_order_date}
          page={result.tariff.source_page}
          table={result.tariff.source_table}
          section={result.tariff.source_section}
          effectiveFrom={result.tariff.effective_from}
          effectiveTo={result.tariff.effective_to}
          lastVerified={result.tariff.last_verified}
          url={result.tariff.source_url}
          notes={result.tariff.verification_notes}
        />
      )}

      <p className="mt-3 rounded-xl bg-slate-50 px-4 py-3 text-xs text-slate-500">
        This is an estimated baseline grid-electricity bill only. Solar cost, subsidies, savings, and
        payback are not part of this estimate and will be available in a later phase.
      </p>
    </div>
  )
}
