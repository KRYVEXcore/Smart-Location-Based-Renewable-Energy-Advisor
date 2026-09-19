import { BadgeCheck, ExternalLink, ShieldAlert } from 'lucide-react'

export interface SourceEvidenceProps {
  verificationStatus: string | null
  organisation: string | null
  document?: string | null
  orderNumber: string | null
  orderDate?: string | null
  page: string | null
  table?: string | null
  section?: string | null
  effectiveFrom: string | null
  effectiveTo: string | null
  lastVerified: string | null
  url: string | null
  notes?: string | null
}

const STATUS_LABEL: Record<string, string> = {
  verified: 'Verified against an official source',
  pending_review: 'Pending review',
  expired: 'Expired',
  superseded: 'Superseded',
  unavailable: 'Unavailable',
}

function Row({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null
  return (
    <div className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
      <dt className="w-36 shrink-0 text-slate-400">{label}</dt>
      <dd className="min-w-0 break-words text-slate-600">{value}</dd>
    </div>
  )
}

// Shows exactly where a displayed number comes from, so a reviewer can find
// it in the official document: organisation, order, page, table/section,
// effective period, verification date and a link to the official source.
export function SourceEvidence(props: SourceEvidenceProps) {
  const verified = props.verificationStatus === 'verified'
  const Icon = verified ? BadgeCheck : ShieldAlert

  return (
    <details className="mt-4 rounded-2xl border border-slate-200 px-4 py-3 text-xs">
      <summary className="flex cursor-pointer list-none items-center gap-2 font-medium text-slate-600">
        <Icon
          className={`h-4 w-4 ${verified ? 'text-emerald-600' : 'text-amber-600'}`}
          aria-hidden="true"
        />
        {STATUS_LABEL[props.verificationStatus ?? ''] ?? 'Verification status unknown'}
        <span className="font-normal text-slate-400">— source and effective dates</span>
      </summary>

      <dl className="mt-3 space-y-1.5">
        <Row label="Source" value={props.organisation} />
        <Row label="Document" value={props.document} />
        <Row label="Order / notification" value={props.orderNumber} />
        <Row label="Order date" value={props.orderDate} />
        <Row label="Page" value={props.page} />
        <Row label="Table" value={props.table} />
        <Row label="Section" value={props.section} />
        <Row
          label="Effective"
          value={props.effectiveFrom ? `${props.effectiveFrom} – ${props.effectiveTo ?? 'until further orders'}` : null}
        />
        <Row label="Last verified" value={props.lastVerified} />
      </dl>

      {props.notes && <p className="mt-3 rounded-lg bg-slate-50 px-3 py-2 text-slate-500">{props.notes}</p>}

      {props.url && (
        <a
          href={props.url}
          target="_blank"
          rel="noreferrer"
          className="mt-3 inline-flex items-center gap-1 font-medium text-emerald-700 hover:underline"
        >
          Official source <ExternalLink className="h-3 w-3" aria-hidden="true" />
        </a>
      )}
    </details>
  )
}
