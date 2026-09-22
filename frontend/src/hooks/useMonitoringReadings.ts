import type { MonitoringReading } from '../types/monitoring.ts'

const NO_READINGS: MonitoringReading[] = []

// There is no device integration or telemetry store yet, so there are never any readings, and the
// monitoring cards honestly say nothing is connected. This is the single place a real MonitoringProvider
// (see types/monitoring.ts) would plug in: none is connected (Phase 12.1 found no inverter/vendor API
// credentials and no SunSpec/Modbus-TCP-reachable device in this environment — see that phase's report).
// Do not add sample or estimated readings here.
export function useMonitoringReadings(): MonitoringReading[] {
  return NO_READINGS
}
