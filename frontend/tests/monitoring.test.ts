// Live Monitoring: what the four cards show for no device, live telemetry, missing metrics and an offline device.
// Pure view logic; no network and no DOM.
import assert from 'node:assert/strict'
import { readFileSync } from 'node:fs'
import { describe, it } from 'node:test'
import { useMonitoringReadings } from '../src/hooks/useMonitoringReadings.ts'
import { METRIC, type MonitoringProvider, type MonitoringReading, type ReadingStatus } from '../src/types/monitoring.ts'
import { NOT_CONNECTED_MESSAGE, STALE_AFTER_MS, monitoringViews } from '../src/utils/monitoringView.ts'

const NOW = Date.parse('2026-09-20T10:00:00Z')
const FRESH = '2026-09-20T09:59:30Z'

function reading(
  metric: string,
  value: MonitoringReading['value'],
  unit: string | null,
  extra: { device?: string; timestamp?: string; status?: ReadingStatus; source?: string } = {},
): MonitoringReading {
  return { device: 'dev-1', timestamp: FRESH, metric, value, unit, status: 'ok', source: 'test-source', ...extra }
}

const LIVE: MonitoringReading[] = [
  reading(METRIC.solarPower, 4.8, 'kW', { device: 'inverter-1' }),
  reading(METRIC.solarEnergyToday, 22.4, 'kWh'),
  reading(METRIC.solarEnergyMonth, 480, 'kWh'),
  reading(METRIC.solarEnergyYear, 3900.5, 'kWh'),
  reading(METRIC.solarEnergyLifetime, 12000, 'kWh'),
  reading(METRIC.homePower, 2.1, 'kW', { device: 'meter-1' }),
  reading(METRIC.batteryCharge, 1.2, 'kW', { device: 'battery-1' }),
  reading(METRIC.batteryDischarge, 0, 'kW', { device: 'battery-1' }),
  reading(METRIC.inverterStatus, 'Running', null, { device: 'inverter-1' }),
  reading(METRIC.inverterAcPower, 4.6, 'kW', { device: 'inverter-1' }),
  reading(METRIC.inverterDcPower, 4.8, 'kW', { device: 'inverter-1' }),
  reading(METRIC.inverterVoltage, 231, 'V', { device: 'inverter-1' }),
  reading(METRIC.inverterCurrent, 20, 'A', { device: 'inverter-1' }),
  reading(METRIC.inverterTemperature, 41.5, '°C', { device: 'inverter-1' }),
  reading(METRIC.inverterFault, false, null, { device: 'inverter-1' }),
  reading(METRIC.gridStatus, 'Connected', null, { device: 'meter-1' }),
  reading(METRIC.gridImportPower, 0, 'kW', { device: 'meter-1' }),
  reading(METRIC.gridExportPower, 2.7, 'kW', { device: 'meter-1' }),
  reading(METRIC.gridEnergyImported, 1234.5, 'kWh', { device: 'meter-1' }),
  reading(METRIC.gridEnergyExported, 987.1, 'kWh', { device: 'meter-1' }),
  reading(METRIC.gridVoltage, 230.4, 'V', { device: 'meter-1' }),
  reading(METRIC.gridFrequency, 50.01, 'Hz', { device: 'meter-1' }),
]

const value = (card: { metrics: { key: string; value: string | null }[] }, metric: string) =>
  card.metrics.find((item) => item.key === metric)?.value

describe('no monitoring system connected', () => {
  it('says so on every card and shows no value', () => {
    const views = monitoringViews([], NOW)

    assert.equal(views.flow.message, 'No monitoring system connected')
    assert.equal(views.solar.message, 'No monitoring system connected')
    assert.equal(views.inverter.message, 'Solar inverter not connected')
    assert.equal(views.grid.message, 'Grid monitoring not connected')
    for (const card of [views.flow, views.solar, views.inverter, views.grid]) {
      assert.equal(card.state, 'not_connected')
      assert.equal(card.badge.label, 'Not connected')
    }
    for (const card of [views.solar, views.inverter, views.grid]) assert.deepEqual(card.metrics, [])
    assert.deepEqual([views.flow.solar, views.flow.home, views.flow.grid.value, views.flow.battery], [null, null, null, null])
  })

  it('has no readings today (no integration exists) and no numbers anywhere in the view', () => {
    assert.deepEqual(useMonitoringReadings(), [])
    assert.ok(!/\d/.test(JSON.stringify(monitoringViews(useMonitoringReadings(), NOW))))
    assert.equal(NOT_CONNECTED_MESSAGE, 'No monitoring system connected')
  })
})

describe('live telemetry', () => {
  const views = monitoringViews(LIVE, NOW)

  it('renders the solar generation figures with the units the device reported', () => {
    assert.equal(views.solar.state, 'online')
    assert.equal(views.solar.badge.label, 'Online')
    assert.equal(value(views.solar, METRIC.solarPower), '4.8 kW')
    assert.equal(value(views.solar, METRIC.solarEnergyToday), '22.4 kWh')
    assert.equal(value(views.solar, METRIC.solarEnergyMonth), '480 kWh')
    assert.equal(value(views.solar, METRIC.solarEnergyYear), '3,900.5 kWh')
    assert.equal(value(views.solar, METRIC.solarEnergyLifetime), '12,000 kWh')
  })

  it('renders the inverter card including the fault state and last communication', () => {
    assert.equal(value(views.inverter, METRIC.inverterStatus), 'Running')
    assert.equal(value(views.inverter, METRIC.inverterAcPower), '4.6 kW')
    assert.equal(value(views.inverter, METRIC.inverterDcPower), '4.8 kW')
    assert.equal(value(views.inverter, METRIC.inverterVoltage), '231 V')
    assert.equal(value(views.inverter, METRIC.inverterCurrent), '20 A')
    assert.equal(value(views.inverter, METRIC.inverterTemperature), '41.5 °C')
    assert.equal(value(views.inverter, METRIC.inverterFault), 'No fault')
    assert.match(value(views.inverter, 'last_communication') ?? '', /2026/)
  })

  it('renders the grid card', () => {
    assert.equal(value(views.grid, METRIC.gridStatus), 'Connected')
    assert.equal(value(views.grid, METRIC.gridImportPower), '0 kW') // a reported zero is a real value
    assert.equal(value(views.grid, METRIC.gridExportPower), '2.7 kW')
    assert.equal(value(views.grid, METRIC.gridEnergyImported), '1,234.5 kWh')
    assert.equal(value(views.grid, METRIC.gridEnergyExported), '987.1 kWh')
    assert.equal(value(views.grid, METRIC.gridVoltage), '230.4 V')
    assert.equal(value(views.grid, METRIC.gridFrequency), '50.01 Hz')
  })

  it('renders the energy flow with the direction of grid and battery power', () => {
    assert.equal(views.flow.solar, '4.8 kW')
    assert.equal(views.flow.solarActive, true)
    assert.equal(views.flow.home, '2.1 kW')
    assert.deepEqual(views.flow.grid, { value: '2.7 kW', direction: 'export' })
    assert.deepEqual(views.flow.battery, { value: '1.2 kW', direction: 'charging' })
    assert.deepEqual(views.flow.devices.sort(), ['battery-1', 'inverter-1', 'meter-1'])
    assert.deepEqual(views.flow.sources, ['test-source'])
  })

  it('shows the grid as importing, and a battery discharging, from the reported figures', () => {
    const flow = monitoringViews(
      [reading(METRIC.gridImportPower, 1.4, 'kW'), reading(METRIC.gridExportPower, 0, 'kW'), reading(METRIC.batteryCharge, 0, 'kW'), reading(METRIC.batteryDischarge, 0.8, 'kW')],
      NOW,
    ).flow

    assert.deepEqual(flow.grid, { value: '1.4 kW', direction: 'import' })
    assert.deepEqual(flow.battery, { value: '0.8 kW', direction: 'discharging' })
  })

  it('shows the worst reported status as the badge', () => {
    const warn = monitoringViews([reading(METRIC.inverterAcPower, 4, 'kW'), reading(METRIC.inverterTemperature, 80, '°C', { status: 'warning' })], NOW)
    const fault = monitoringViews([reading(METRIC.inverterAcPower, 0, 'kW', { status: 'fault' }), reading(METRIC.inverterFault, 'E-102', null, { status: 'fault' })], NOW)

    assert.deepEqual(warn.inverter.badge, { label: 'Warning', tone: 'warning' })
    assert.deepEqual(fault.inverter.badge, { label: 'Fault', tone: 'fault' })
    assert.equal(value(fault.inverter, METRIC.inverterFault), 'E-102')
  })
})

describe('missing metrics', () => {
  it('reads "Not available" (null), never a zero, for a metric the device did not report', () => {
    const views = monitoringViews([reading(METRIC.solarPower, 3.2, 'kW')], NOW)

    assert.equal(views.solar.state, 'online')
    assert.equal(value(views.solar, METRIC.solarPower), '3.2 kW')
    for (const metric of [METRIC.solarEnergyToday, METRIC.solarEnergyMonth, METRIC.solarEnergyYear, METRIC.solarEnergyLifetime]) {
      assert.equal(value(views.solar, metric), null)
    }
    // Other cards have no data of their own, so they stay "not connected" rather than borrowing solar's.
    assert.equal(views.inverter.state, 'not_connected')
    assert.equal(views.grid.state, 'not_connected')
    // The flow has no home, grid or battery data and derives none.
    assert.equal(views.flow.home, null)
    assert.deepEqual(views.flow.grid, { value: null, direction: null })
    assert.equal(views.flow.battery, null)
  })

  it('treats null, NaN, infinite and blank values as not reported', () => {
    const views = monitoringViews(
      [
        reading(METRIC.solarPower, null, 'kW'),
        reading(METRIC.solarEnergyToday, Number.NaN, 'kWh'),
        reading(METRIC.solarEnergyMonth, Number.POSITIVE_INFINITY, 'kWh'),
        reading(METRIC.solarEnergyYear, '   ', 'kWh'),
      ],
      NOW,
    )

    for (const metric of [METRIC.solarPower, METRIC.solarEnergyToday, METRIC.solarEnergyMonth, METRIC.solarEnergyYear]) {
      assert.equal(value(views.solar, metric), null)
    }
  })

  it('shows the battery only when battery data exists', () => {
    assert.equal(monitoringViews([reading(METRIC.solarPower, 1, 'kW')], NOW).flow.battery, null)
    assert.notEqual(monitoringViews([reading(METRIC.batteryCharge, 1, 'kW')], NOW).flow.battery, null)
  })
})

describe('device offline', () => {
  const stale = new Date(NOW - STALE_AFTER_MS - 60_000).toISOString()

  it('shows Offline and hides the old values when a device stops reporting', () => {
    const views = monitoringViews(
      [reading(METRIC.solarPower, 4.8, 'kW', { timestamp: stale }), reading(METRIC.inverterAcPower, 4.6, 'kW', { timestamp: stale }), reading(METRIC.gridImportPower, 1, 'kW', { timestamp: stale })],
      NOW,
    )

    for (const card of [views.solar, views.inverter, views.grid, views.flow]) {
      assert.equal(card.state, 'offline')
      assert.deepEqual(card.badge, { label: 'Offline', tone: 'warning' })
      assert.match(card.message ?? '', /Device offline/)
    }
    assert.ok(views.solar.metrics.every((metric) => metric.value === null))
    assert.equal(views.flow.solar, null)
    assert.match(value(views.inverter, 'last_communication') ?? '', /2026/) // the last contact is still a fact
  })

  it('is offline when a device reports the offline status, even with a fresh timestamp', () => {
    const views = monitoringViews([reading(METRIC.inverterStatus, 'Unreachable', null, { status: 'offline' })], NOW)

    assert.equal(views.inverter.state, 'offline')
    assert.ok(views.inverter.metrics.filter((metric) => metric.key !== 'last_communication').every((metric) => metric.value === null))
  })

  it('comes back online when a fresh reading arrives', () => {
    const views = monitoringViews([reading(METRIC.solarPower, 4.8, 'kW', { timestamp: stale }), reading(METRIC.solarPower, 5.1, 'kW')], NOW)

    assert.equal(views.solar.state, 'online')
    assert.equal(value(views.solar, METRIC.solarPower), '5.1 kW')
  })
})

describe('no fake values', () => {
  it('ignores a reading without a valid time instead of showing it as current', () => {
    const views = monitoringViews([reading(METRIC.solarPower, 4.8, 'kW', { timestamp: 'not a time' })], NOW)

    assert.equal(views.solar.state, 'not_connected')
    assert.deepEqual(views.solar.metrics, [])
  })

  it('never fills a gap from another metric, an older reading or an estimate', () => {
    const views = monitoringViews([reading(METRIC.solarPower, 4.8, 'kW'), reading(METRIC.gridExportPower, 2.7, 'kW')], NOW)

    assert.equal(views.flow.home, null) // not "solar - export"
    assert.equal(value(views.solar, METRIC.solarEnergyToday), null) // not "power x hours"
    assert.equal(views.flow.battery, null)
  })

  it('uses only the readings it is given (the Solar Engine estimate is never an input)', () => {
    assert.equal(monitoringViews.length <= 2, true)
    assert.ok(!JSON.stringify(monitoringViews([], NOW)).includes('kWh/year'))
  })
})

describe('adapter interface (Phase 12.1: no real source is connected yet)', () => {
  it('useMonitoringReadings() still returns no readings with nothing connected', () => {
    assert.deepEqual(useMonitoringReadings(), [])
  })

  it('a real telemetry integration can satisfy MonitoringProvider without changing the model', async () => {
    // TEST FIXTURE ONLY, not a real device: proves the interface is actually implementable end to end
    // (source id in, MonitoringReading[] out) — no such implementation is wired into the app.
    const fixtureProvider: MonitoringProvider = {
      source: 'test-vendor',
      fetchReadings: () => Promise.resolve([{ device: 'inverter-1', timestamp: new Date().toISOString(), metric: METRIC.solarPower, value: 2.1, unit: 'kW', status: 'ok', source: 'test-vendor' }]),
    }

    const readings = await fixtureProvider.fetchReadings()

    assert.equal(readings.length, 1)
    assert.equal(readings[0].source, fixtureProvider.source)
    assert.equal(readings[0].metric, METRIC.solarPower)
  })
})

describe('responsive layout', () => {
  const source = readFileSync(new URL('../src/components/monitoring/LiveMonitoringSection.tsx', import.meta.url), 'utf8')

  // The layout itself is checked in a real browser at 375, 768 and 1280 px; this guards against regressions.
  it('is a single column that widens with the screen and has no fixed pixel widths', () => {
    assert.match(source, /grid gap-4 md:grid-cols-2 lg:grid-cols-3/)
    assert.match(source, /min-w-0/)
    assert.match(source, /break-words/)
    assert.ok(!/\b(?:min-|max-)?(?:w|h)-\[\d+(?:px|rem)\]/.test(source), 'no arbitrary fixed widths')
    assert.ok(!/style=\{\{[^}]*width/.test(source), 'no inline widths')
  })
})
