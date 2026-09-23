import type { MonitoringReading } from '../types/monitoring.ts'
import { DEMO_READINGS } from '../utils/demoMonitoringProvider.ts'

const NO_READINGS: MonitoringReading[] = []

// There is no device integration or telemetry store yet, so with demoMode off there are never any
// readings, and the monitoring cards honestly say nothing is connected. This is the single place a real
// MonitoringProvider (see types/monitoring.ts) would plug in: none is connected (Phase 12.1 found no
// inverter/vendor API credentials and no SunSpec/Modbus-TCP-reachable device in this environment — see
// that phase's report). demoMode (Phase 12.2) is presentation-only, for the SIH demo: it swaps in fixture
// readings clearly tagged source: 'demo' so they are never mistaken for real telemetry, and it never
// touches production assessment calculations (the Solar Engine estimate passed separately to
// LiveMonitoringSection). Do not add sample or estimated readings to the non-demo path.
export function useMonitoringReadings(demoMode = false): MonitoringReading[] {
  return demoMode ? DEMO_READINGS : NO_READINGS
}
