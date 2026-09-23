import { METRIC, type MonitoringProvider, type MonitoringReading } from '../types/monitoring.ts'

// Fixture readings for the SIH demo only. Every reading carries source: 'demo' so the UI can show a
// "DEMO DATA — SIMULATED" banner and so these values can never be mistaken for real telemetry (see
// useMonitoringReadings.ts and LiveMonitoringSection.tsx). Implements MonitoringProvider (types/monitoring.ts)
// as a worked example of the seam a real integration (SunSpec/Modbus, MQTT, a vendor API) would fill.
export const DEMO_READINGS: MonitoringReading[] = (() => {
  const timestamp = new Date().toISOString()
  const reading = (device: string, metric: string, value: MonitoringReading['value'], unit: string | null): MonitoringReading => ({
    device,
    timestamp,
    metric,
    value,
    unit,
    status: 'ok',
    source: 'demo',
  })
  return [
    reading('demo-inverter', METRIC.solarPower, 3.8, 'kW'),
    reading('demo-inverter', METRIC.solarEnergyToday, 18.2, 'kWh'),
    reading('demo-inverter', METRIC.solarEnergyMonth, 410, 'kWh'),
    reading('demo-inverter', METRIC.solarEnergyYear, 4820, 'kWh'),
    reading('demo-inverter', METRIC.solarEnergyLifetime, 15230, 'kWh'),
    reading('demo-meter', METRIC.homePower, 2.1, 'kW'),
    reading('demo-inverter', METRIC.inverterStatus, 'Generating', null),
    reading('demo-inverter', METRIC.inverterAcPower, 3.7, 'kW'),
    reading('demo-inverter', METRIC.inverterDcPower, 3.9, 'kW'),
    reading('demo-inverter', METRIC.inverterVoltage, 238.4, 'V'),
    reading('demo-inverter', METRIC.inverterCurrent, 15.5, 'A'),
    reading('demo-inverter', METRIC.inverterTemperature, 42, '°C'),
    reading('demo-inverter', METRIC.inverterFault, false, null),
    reading('demo-meter', METRIC.gridStatus, 'Exporting', null),
    reading('demo-meter', METRIC.gridImportPower, 0, 'kW'),
    reading('demo-meter', METRIC.gridExportPower, 1.7, 'kW'),
    reading('demo-meter', METRIC.gridEnergyImported, 1240, 'kWh'),
    reading('demo-meter', METRIC.gridEnergyExported, 3860, 'kWh'),
    reading('demo-meter', METRIC.gridVoltage, 231.2, 'V'),
    reading('demo-meter', METRIC.gridFrequency, 50.02, 'Hz'),
  ]
})()

export const demoMonitoringProvider: MonitoringProvider = {
  source: 'demo',
  fetchReadings: () => Promise.resolve(DEMO_READINGS),
}
