import { useEffect, useState, type ReactNode } from 'react'
import { Activity, ArrowDown, ArrowLeft, ArrowRight, BatteryCharging, Cpu, House, Minus, Sun, Zap, type LucideIcon } from 'lucide-react'
import type { MonitoringReading } from '../../types/monitoring'
import { cn } from '../../utils/cn'
import { monitoringViews, type Badge, type CardView, type FlowView } from '../../utils/monitoringView'
import { NOT_AVAILABLE } from '../../utils/reportView'

// Actual device telemetry only. Nothing on these cards is estimated, derived or defaulted: a value the device did
// not report reads "Not available", and with no monitoring system connected the cards say so.

const BADGE_STYLES: Record<Badge['tone'], string> = {
  ok: 'bg-emerald-50 text-emerald-700',
  warning: 'bg-amber-50 text-amber-700',
  fault: 'bg-red-50 text-red-600',
  muted: 'bg-slate-100 text-slate-500',
}

function StatusBadge({ badge }: { badge: Badge }) {
  return <span className={cn('shrink-0 rounded-full px-2.5 py-1 text-xs font-semibold', BADGE_STYLES[badge.tone])}>{badge.label}</span>
}

interface CardShellProps {
  icon: LucideIcon
  title: string
  subtitle?: string
  badge: Badge
  className?: string
  children: ReactNode
}

function CardShell({ icon: Icon, title, subtitle, badge, className, children }: CardShellProps) {
  return (
    <div className={cn('min-w-0 rounded-2xl border border-slate-200 bg-white p-5', className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex min-w-0 items-center gap-2.5">
          <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100 text-slate-500">
            <Icon className="h-4 w-4" aria-hidden="true" />
          </span>
          <div className="min-w-0">
            <p className="break-words text-sm font-semibold text-slate-900">{title}</p>
            {subtitle && <p className="break-words text-xs text-slate-400">{subtitle}</p>}
          </div>
        </div>
        <StatusBadge badge={badge} />
      </div>
      <div className="mt-4">{children}</div>
    </div>
  )
}

function EmptyState({ message }: { message: string }) {
  return (
    <p className="rounded-xl border border-dashed border-slate-300 bg-slate-50 px-4 py-5 text-center text-sm text-slate-500">{message}</p>
  )
}

function OfflineNote({ message }: { message: string }) {
  return <p className="mb-3 break-words rounded-xl bg-amber-50 px-3 py-2.5 text-xs text-amber-700">{message}</p>
}

function Provenance({ view, showLastUpdate = true }: { view: Pick<CardView, 'devices' | 'sources' | 'lastUpdate'>; showLastUpdate?: boolean }) {
  const parts = [
    view.devices.length > 0 ? `Device: ${view.devices.join(', ')}` : null,
    view.sources.length > 0 ? `Source: ${view.sources.join(', ')}` : null,
    showLastUpdate && view.lastUpdate ? `Last update: ${view.lastUpdate}` : null,
  ].filter(Boolean)
  return parts.length > 0 ? <p className="mt-3 break-words text-xs text-slate-400">{parts.join(' · ')}</p> : null
}

function MetricTiles({ metrics }: { metrics: CardView['metrics'] }) {
  return (
    <dl className="grid grid-cols-2 gap-2">
      {metrics.map((metric) => (
        <div key={metric.key} className="min-w-0 rounded-xl border border-slate-100 bg-slate-50 px-3 py-2">
          <dt className="break-words text-[11px] uppercase tracking-wide text-slate-400">{metric.label}</dt>
          <dd className={cn('mt-0.5 break-words text-sm', metric.value === null ? 'font-medium text-slate-300' : 'font-semibold text-slate-900')}>
            {metric.value ?? NOT_AVAILABLE}
          </dd>
        </div>
      ))}
    </dl>
  )
}

function FlowNode({ icon: Icon, label, value, note }: { icon: LucideIcon; label: string; value: string | null; note?: string | null }) {
  return (
    <div className="flex min-w-0 flex-col items-center gap-1 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-emerald-50 text-emerald-600 sm:h-12 sm:w-12">
        <Icon className="h-5 w-5" aria-hidden="true" />
      </span>
      <span className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label}</span>
      <span className={cn('break-words text-xs sm:text-sm', value === null ? 'font-medium text-slate-300' : 'font-bold text-slate-900')}>
        {value ?? NOT_AVAILABLE}
      </span>
      {note && <span className="text-[11px] text-slate-400">{note}</span>}
    </div>
  )
}

function FlowArrow({ Icon, active }: { Icon: LucideIcon; active: boolean }) {
  return <Icon className={cn('h-5 w-5 shrink-0', active ? 'text-emerald-500' : 'text-slate-300')} aria-hidden="true" />
}

const FLOW_COLUMNS = 'grid grid-cols-[1fr_auto_1fr_auto_1fr] items-center gap-1.5 sm:gap-3'

function EnergyFlowCard({ view, className }: { view: FlowView; className?: string }) {
  const { grid, battery } = view
  const gridArrow = grid.direction === 'export' ? ArrowRight : grid.direction === 'import' ? ArrowLeft : Minus
  return (
    <CardShell icon={Activity} title="Live energy flow" subtitle="Solar → Home → Grid, with battery" badge={view.badge} className={className}>
      {view.state === 'not_connected' ? (
        <EmptyState message={view.message ?? ''} />
      ) : (
        <>
          {view.message && <OfflineNote message={view.message} />}
          <div className={FLOW_COLUMNS}>
            <FlowNode icon={Sun} label="Solar" value={view.solar} />
            <FlowArrow Icon={ArrowRight} active={view.solarActive} />
            <FlowNode icon={House} label="Home" value={view.home} />
            <FlowArrow Icon={gridArrow} active={grid.direction === 'import' || grid.direction === 'export'} />
            <FlowNode
              icon={Zap}
              label="Grid"
              value={grid.value}
              note={grid.direction === 'import' ? 'Importing' : grid.direction === 'export' ? 'Exporting' : null}
            />
          </div>
          {battery && (
            <div className={cn(FLOW_COLUMNS, 'mt-2')}>
              <div className="col-start-3 flex flex-col items-center gap-2">
                <FlowArrow Icon={ArrowDown} active={battery.direction === 'charging' || battery.direction === 'discharging'} />
                <FlowNode
                  icon={BatteryCharging}
                  label="Battery"
                  value={battery.value}
                  note={battery.direction === 'charging' ? 'Charging' : battery.direction === 'discharging' ? 'Discharging' : null}
                />
              </div>
            </div>
          )}
          <Provenance view={view} />
        </>
      )}
    </CardShell>
  )
}

function MetricCard({
  icon,
  title,
  subtitle,
  view,
  showLastUpdate,
  footer,
  className,
}: {
  icon: LucideIcon
  title: string
  subtitle?: string
  view: CardView
  showLastUpdate?: boolean
  footer?: ReactNode
  className?: string
}) {
  return (
    <CardShell icon={icon} title={title} subtitle={subtitle} badge={view.badge} className={className}>
      {view.state === 'not_connected' ? (
        <EmptyState message={view.message ?? ''} />
      ) : (
        <>
          {view.message && <OfflineNote message={view.message} />}
          <MetricTiles metrics={view.metrics} />
          <Provenance view={view} showLastUpdate={showLastUpdate} />
        </>
      )}
      {footer}
    </CardShell>
  )
}

interface LiveMonitoringSectionProps {
  readings: MonitoringReading[]
  // The Solar Engine's yearly estimate, shown only as a clearly labelled estimate, never as monitored generation.
  estimatedAnnualKwh?: number | null
  // Phase 12.2: readings are simulated fixture data for the SIH demo, never real telemetry. Must stay
  // clearly labelled whenever true.
  isDemo?: boolean
}

export function LiveMonitoringSection({ readings, estimatedAnnualKwh, isDemo = false }: LiveMonitoringSectionProps) {
  // Re-evaluates staleness while devices report, so a device that stops reporting turns Offline.
  const [now, setNow] = useState(() => Date.now())
  const hasReadings = readings.length > 0
  useEffect(() => {
    if (!hasReadings) return
    const timer = window.setInterval(() => setNow(Date.now()), 30_000)
    return () => window.clearInterval(timer)
  }, [hasReadings])

  const views = monitoringViews(readings, now)

  return (
    <div>
      {isDemo ? (
        <p className="inline-flex items-center gap-2 rounded-full bg-amber-100 px-3 py-1.5 text-xs font-bold uppercase tracking-wide text-amber-800">
          DEMO DATA — SIMULATED, not from a real device
        </p>
      ) : (
        <p className="text-sm text-slate-500">Actual device telemetry only. Nothing here is estimated.</p>
      )}
      <div className="mt-4 grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <EnergyFlowCard view={views.flow} className="md:col-span-2 lg:col-span-3" />
        <MetricCard
          icon={Sun}
          title="Solar generation"
          subtitle="Actual monitored generation"
          view={views.solar}
          footer={
            estimatedAnnualKwh != null && (
              <p className="mt-3 break-words rounded-xl bg-slate-50 px-3 py-2 text-xs text-slate-500">
                <span className="font-semibold text-slate-600">Estimated, not monitored:</span> about{' '}
                {Math.round(estimatedAnnualKwh).toLocaleString('en-IN')} kWh/year from the Solar Engine. This is a calculation, not a meter reading.
              </p>
            )
          }
        />
        <MetricCard icon={Cpu} title="Solar inverter" view={views.inverter} showLastUpdate={false} />
        <MetricCard icon={Zap} title="Grid monitoring" view={views.grid} />
      </div>
    </div>
  )
}
