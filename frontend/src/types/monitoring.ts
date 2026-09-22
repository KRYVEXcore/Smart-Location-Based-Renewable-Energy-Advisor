// Provider-agnostic monitoring data model. Anything that can report device telemetry (Modbus/SunSpec, MQTT,
// a vendor API, ...) plugs in by producing MonitoringReading[]. No such integration exists yet, so today
// there are never any readings and the UI says "No monitoring system connected".

export type ReadingStatus = 'ok' | 'warning' | 'fault' | 'offline' | 'unknown'

export interface MonitoringReading {
  device: string // stable id of the reporting device, e.g. "inverter-1"
  timestamp: string // ISO 8601 time the device took the measurement
  metric: string // one of METRIC below, or another name a provider defines
  value: number | string | boolean | null // null = the device reported nothing for this metric
  unit: string | null // e.g. "kW", "V"; shown exactly as reported
  status: ReadingStatus
  source: string // where it came from, e.g. "modbus", "mqtt", "vendor-x"
}

// The adapter contract a real telemetry integration must satisfy to plug into useMonitoringReadings()
// (see that file). `source` identifies it and should match the `source` field on the readings it
// returns. Phase 12.1: no implementation of this exists — no inverter/vendor API credentials and no
// SunSpec/Modbus-TCP-reachable device were available in this environment to build one against.
export interface MonitoringProvider {
  source: string
  fetchReadings(): Promise<MonitoringReading[]>
}

// The metrics the four monitoring cards read. Import and export, and battery charge and discharge, are
// separate metrics so no sign convention has to be guessed.
export const METRIC = {
  solarPower: 'solar_power_kw',
  solarEnergyToday: 'solar_energy_today_kwh',
  solarEnergyMonth: 'solar_energy_month_kwh',
  solarEnergyYear: 'solar_energy_year_kwh',
  solarEnergyLifetime: 'solar_energy_lifetime_kwh',
  homePower: 'home_consumption_kw',
  batteryCharge: 'battery_charge_kw',
  batteryDischarge: 'battery_discharge_kw',
  inverterStatus: 'inverter_status',
  inverterAcPower: 'inverter_ac_power_kw',
  inverterDcPower: 'inverter_dc_power_kw',
  inverterVoltage: 'inverter_voltage_v',
  inverterCurrent: 'inverter_current_a',
  inverterTemperature: 'inverter_temperature_c',
  inverterFault: 'inverter_fault',
  gridStatus: 'grid_status',
  gridImportPower: 'grid_import_kw',
  gridExportPower: 'grid_export_kw',
  gridEnergyImported: 'grid_energy_imported_kwh',
  gridEnergyExported: 'grid_energy_exported_kwh',
  gridVoltage: 'grid_voltage_v',
  gridFrequency: 'grid_frequency_hz',
} as const
