import { METRIC, type MonitoringReading } from '../types/monitoring.ts'

// Turns actual device readings into what the monitoring cards show. Pure and DOM-free so it can be tested.
// Rules: a value is only ever shown if a device reported it; a missing metric is "Not available" (null here),
// never a zero; and nothing is estimated, derived or defaulted. The Solar Engine's estimates never enter here.

export const NOT_CONNECTED_MESSAGE = 'No monitoring system connected'
// A device that has not reported for this long is treated as offline and its old values are not shown as live.
export const STALE_AFTER_MS = 5 * 60 * 1000

export type CardState = 'not_connected' | 'offline' | 'online'
export type BadgeTone = 'ok' | 'warning' | 'fault' | 'muted'

export interface Badge {
  label: string
  tone: BadgeTone
}

export interface MetricView {
  key: string
  label: string
  value: string | null // null = "Not available"
}

export interface CardView {
  state: CardState
  badge: Badge
  message: string | null // the not-connected / offline explanation
  metrics: MetricView[]
  lastUpdate: string | null
  devices: string[]
  sources: string[]
}

export interface FlowView {
  state: CardState
  badge: Badge
  message: string | null
  solar: string | null
  solarActive: boolean
  home: string | null
  grid: { value: string | null; direction: 'import' | 'export' | 'idle' | null }
  battery: { value: string | null; direction: 'charging' | 'discharging' | 'idle' | null } | null // null = no battery data
  lastUpdate: string | null
  devices: string[]
  sources: string[]
}

interface Sample extends MonitoringReading {
  time: number
}

const formatTime = (time: number) => new Intl.DateTimeFormat('en-IN', { dateStyle: 'medium', timeStyle: 'short' }).format(time)

// The newest usable reading of each requested metric. A reading with no valid time cannot be shown as current.
function latest(readings: MonitoringReading[], metrics: readonly string[]): Map<string, Sample> {
  const out = new Map<string, Sample>()
  for (const reading of readings) {
    if (!metrics.includes(reading.metric)) continue
    const time = Date.parse(reading.timestamp)
    if (!Number.isFinite(time)) continue
    const seen = out.get(reading.metric)
    if (!seen || time > seen.time) out.set(reading.metric, { ...reading, time })
  }
  return out
}

const newest = (samples: Map<string, Sample>): Sample | null =>
  [...samples.values()].reduce<Sample | null>((best, sample) => (best === null || sample.time > best.time ? sample : best), null)

function stateOf(samples: Map<string, Sample>, now: number): CardState {
  const last = newest(samples)
  if (last === null) return 'not_connected'
  return last.status === 'offline' || now - last.time > STALE_AFTER_MS ? 'offline' : 'online'
}

function badgeOf(state: CardState, samples: Map<string, Sample>): Badge {
  if (state === 'not_connected') return { label: 'Not connected', tone: 'muted' }
  if (state === 'offline') return { label: 'Offline', tone: 'warning' }
  const statuses = [...samples.values()].map((sample) => sample.status)
  if (statuses.includes('fault')) return { label: 'Fault', tone: 'fault' }
  if (statuses.includes('warning')) return { label: 'Warning', tone: 'warning' }
  return { label: 'Online', tone: 'ok' }
}

// A reported value with its reported unit, or null when there is nothing displayable.
function formatValue(sample: Sample): string | null {
  const { value, unit } = sample
  if (typeof value === 'number') {
    return Number.isFinite(value) ? `${value.toLocaleString('en-IN', { maximumFractionDigits: 2 })}${unit ? ` ${unit}` : ''}` : null
  }
  if (typeof value === 'string') return value.trim() === '' ? null : value
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return null
}

const formatFault = (sample: Sample): string | null =>
  typeof sample.value === 'boolean' ? (sample.value ? 'Fault' : 'No fault') : formatValue(sample)

const numberOf = (sample: Sample | undefined): number | null =>
  sample && typeof sample.value === 'number' && Number.isFinite(sample.value) ? sample.value : null

interface Field {
  metric: string
  label: string
  format?: (sample: Sample) => string | null
}

const SOLAR_FIELDS: Field[] = [
  { metric: METRIC.solarPower, label: 'Current power' },
  { metric: METRIC.solarEnergyToday, label: 'Today' },
  { metric: METRIC.solarEnergyMonth, label: 'This month' },
  { metric: METRIC.solarEnergyYear, label: 'This year' },
  { metric: METRIC.solarEnergyLifetime, label: 'Lifetime' },
]

const INVERTER_FIELDS: Field[] = [
  { metric: METRIC.inverterStatus, label: 'Status' },
  { metric: METRIC.inverterAcPower, label: 'AC power' },
  { metric: METRIC.inverterDcPower, label: 'DC power' },
  { metric: METRIC.inverterVoltage, label: 'Voltage' },
  { metric: METRIC.inverterCurrent, label: 'Current' },
  { metric: METRIC.inverterTemperature, label: 'Temperature' },
  { metric: METRIC.inverterFault, label: 'Fault state', format: formatFault },
]

const GRID_FIELDS: Field[] = [
  { metric: METRIC.gridStatus, label: 'Grid status' },
  { metric: METRIC.gridImportPower, label: 'Import power' },
  { metric: METRIC.gridExportPower, label: 'Export power' },
  { metric: METRIC.gridEnergyImported, label: 'Imported energy' },
  { metric: METRIC.gridEnergyExported, label: 'Exported energy' },
  { metric: METRIC.gridVoltage, label: 'Voltage' },
  { metric: METRIC.gridFrequency, label: 'Frequency' },
]

const FLOW_METRICS = [
  METRIC.solarPower,
  METRIC.homePower,
  METRIC.gridImportPower,
  METRIC.gridExportPower,
  METRIC.batteryCharge,
  METRIC.batteryDischarge,
]

const unique = (values: string[]) => [...new Set(values)]

function cardOf(readings: MonitoringReading[], fields: Field[], notConnected: string, now: number, withLastCommunication = false): CardView {
  const samples = latest(readings, fields.map((field) => field.metric))
  const state = stateOf(samples, now)
  const last = newest(samples)
  const lastUpdate = last ? formatTime(last.time) : null
  const base = { state, badge: badgeOf(state, samples), lastUpdate, devices: unique([...samples.values()].map((s) => s.device)), sources: unique([...samples.values()].map((s) => s.source)) }
  if (state === 'not_connected') return { ...base, message: notConnected, metrics: [], devices: [], sources: [] }

  const live = state === 'online'
  const metrics: MetricView[] = fields.map((field) => {
    const sample = samples.get(field.metric)
    return { key: field.metric, label: field.label, value: live && sample ? (field.format ?? formatValue)(sample) : null }
  })
  // The last time the device was heard from is a fact even when it is offline.
  if (withLastCommunication) metrics.push({ key: 'last_communication', label: 'Last communication', value: lastUpdate })
  return { ...base, message: live ? null : `Device offline. Live values are hidden. Last communication: ${lastUpdate}.`, metrics }
}

export function energyFlowView(readings: MonitoringReading[], now: number): FlowView {
  const samples = latest(readings, FLOW_METRICS)
  const state = stateOf(samples, now)
  const live = state === 'online'
  const last = newest(samples)
  const shown = (metric: string) => {
    const sample = live ? samples.get(metric) : undefined
    return sample ? formatValue(sample) : null
  }
  const power = (metric: string) => (live ? numberOf(samples.get(metric)) : null)

  const gridImport = power(METRIC.gridImportPower)
  const gridExport = power(METRIC.gridExportPower)
  const gridDirection = gridImport !== null && gridImport > 0 ? 'import' : gridExport !== null && gridExport > 0 ? 'export' : gridImport !== null || gridExport !== null ? 'idle' : null
  const charge = power(METRIC.batteryCharge)
  const discharge = power(METRIC.batteryDischarge)
  const batteryDirection = charge !== null && charge > 0 ? 'charging' : discharge !== null && discharge > 0 ? 'discharging' : charge !== null || discharge !== null ? 'idle' : null
  const hasBattery = samples.has(METRIC.batteryCharge) || samples.has(METRIC.batteryDischarge)
  const solar = power(METRIC.solarPower)

  return {
    state,
    badge: badgeOf(state, samples),
    message: state === 'not_connected' ? NOT_CONNECTED_MESSAGE : live ? null : `Device offline. Live values are hidden. Last communication: ${formatTime(last!.time)}.`,
    solar: shown(METRIC.solarPower),
    solarActive: solar !== null && solar > 0,
    home: shown(METRIC.homePower),
    grid: { value: gridDirection === 'export' ? shown(METRIC.gridExportPower) : shown(METRIC.gridImportPower) ?? shown(METRIC.gridExportPower), direction: gridDirection },
    battery: hasBattery ? { value: batteryDirection === 'discharging' ? shown(METRIC.batteryDischarge) : shown(METRIC.batteryCharge) ?? shown(METRIC.batteryDischarge), direction: batteryDirection } : null,
    lastUpdate: last ? formatTime(last.time) : null,
    devices: unique([...samples.values()].map((sample) => sample.device)),
    sources: unique([...samples.values()].map((sample) => sample.source)),
  }
}

export function monitoringViews(readings: MonitoringReading[], now: number = Date.now()) {
  return {
    flow: energyFlowView(readings, now),
    solar: cardOf(readings, SOLAR_FIELDS, NOT_CONNECTED_MESSAGE, now),
    inverter: cardOf(readings, INVERTER_FIELDS, 'Solar inverter not connected', now, true),
    grid: cardOf(readings, GRID_FIELDS, 'Grid monitoring not connected', now),
  }
}
