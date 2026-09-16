import { BatteryCharging, Sun, Wind, Zap } from 'lucide-react'

const CHIPS = [
  { icon: Sun, className: 'left-4 top-6 sm:left-10 sm:top-10', delay: '0s', color: 'text-amber-500' },
  { icon: Wind, className: 'right-6 top-16 sm:right-14 sm:top-20', delay: '1.2s', color: 'text-sky-500' },
  {
    icon: BatteryCharging,
    className: 'left-10 bottom-10 sm:left-16 sm:bottom-14',
    delay: '0.6s',
    color: 'text-emerald-600',
  },
  { icon: Zap, className: 'right-8 bottom-6 sm:right-16 sm:bottom-10', delay: '1.8s', color: 'text-violet-500' },
]

export function EnergyVisual() {
  return (
    <div
      className="relative mx-auto h-72 w-72 sm:h-80 sm:w-80"
      role="img"
      aria-label="Illustration representing solar, wind, and battery renewable energy sources"
    >
      <div className="absolute inset-6 rounded-full bg-gradient-to-br from-emerald-300/40 via-sky-200/40 to-transparent blur-2xl" />
      <div className="absolute inset-0 rounded-full border border-slate-200" />
      <div className="absolute inset-10 rounded-full border border-dashed border-slate-200" />

      <div className="absolute inset-0 flex items-center justify-center">
        <span className="flex h-20 w-20 items-center justify-center rounded-full bg-white shadow-lg shadow-slate-200">
          <Zap className="h-9 w-9 text-emerald-600" aria-hidden="true" />
        </span>
      </div>

      {CHIPS.map(({ icon: Icon, className, delay, color }, index) => (
        <span
          key={index}
          className={`animate-float absolute flex h-14 w-14 items-center justify-center rounded-2xl bg-white shadow-md shadow-slate-200 ${className}`}
          style={{ animationDelay: delay }}
        >
          <Icon className={`h-6 w-6 ${color}`} aria-hidden="true" />
        </span>
      ))}
    </div>
  )
}
