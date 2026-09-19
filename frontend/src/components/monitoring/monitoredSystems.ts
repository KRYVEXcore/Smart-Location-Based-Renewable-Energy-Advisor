import { BatteryCharging, Sun, Wind, Zap } from 'lucide-react'

export const MONITORED_SYSTEMS = [
  { icon: Sun, name: 'Solar', tagline: 'Monitor current generation, daily production and system status.', gradient: 'from-amber-400 to-orange-500' },
  { icon: Wind, name: 'Wind', tagline: 'Monitor generation, production trends and system status.', gradient: 'from-sky-400 to-blue-500' },
  { icon: Zap, name: 'Hybrid', tagline: 'View combined renewable generation and system performance.', gradient: 'from-violet-400 to-fuchsia-500' },
  { icon: BatteryCharging, name: 'Battery', tagline: 'Track battery state, charge/discharge and storage status.', gradient: 'from-emerald-400 to-teal-500' },
]
