import { BatteryCharging, MapPin, Settings2, Sun, TrendingUp, Wind, Zap } from 'lucide-react'
import { Button } from '../components/buttons/Button'
import { Section } from '../components/layout/Section'
import { TechnologyCard } from '../components/cards/TechnologyCard'
import { EnergyVisual } from '../components/visualizations/EnergyVisual'

const TECHNOLOGIES = [
  { icon: Sun, name: 'Solar', tagline: 'Rooftop or ground-mounted PV', gradient: 'from-amber-400 to-orange-500' },
  { icon: Wind, name: 'Wind', tagline: 'Small-scale turbines', gradient: 'from-sky-400 to-blue-500' },
  { icon: Zap, name: 'Hybrid', tagline: 'Solar + wind, combined', gradient: 'from-violet-400 to-fuchsia-500' },
  { icon: BatteryCharging, name: 'Battery', tagline: 'Storage & backup', gradient: 'from-emerald-400 to-teal-500' },
]

const STEPS = [
  { icon: MapPin, label: 'Share your location & building' },
  { icon: Settings2, label: 'Deterministic engines size your system' },
  { icon: TrendingUp, label: 'Compare cost, savings & payback' },
]

export function HomePage() {
  return (
    <>
      <Section className="grid items-center gap-10 pt-16 sm:pt-24 lg:grid-cols-2 lg:gap-12">
        <div className="text-center lg:text-left">
          <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-100 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-emerald-700">
            Phase 1 — Foundation
          </span>
          <h1 className="mt-5 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
            Smarter energy decisions for your building.
          </h1>
          <p className="mt-4 text-lg text-slate-500">
            Analyze your location, energy use and renewable options in one place.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center lg:justify-start">
            <Button to="/assess" size="lg">
              Start Energy Assessment
            </Button>
            <Button href="#how-it-works" size="lg" variant="secondary">
              Explore how it works
            </Button>
          </div>
        </div>
        <EnergyVisual />
      </Section>

      <Section>
        <div className="flex items-end justify-between">
          <h2 className="text-xl font-bold text-slate-900">Technologies</h2>
        </div>
        <div className="mt-5 grid grid-cols-2 gap-4 lg:grid-cols-4">
          {TECHNOLOGIES.map((tech) => (
            <TechnologyCard key={tech.name} {...tech} />
          ))}
        </div>
      </Section>

      <Section id="how-it-works" className="bg-slate-50">
        <h2 className="text-xl font-bold text-slate-900">How it works</h2>
        <div className="mt-6 grid gap-4 sm:grid-cols-3">
          {STEPS.map((step, index) => (
            <div key={step.label} className="rounded-2xl border border-slate-200 bg-white p-6">
              <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-slate-900 text-sm font-semibold text-white">
                {index + 1}
              </span>
              <span className="mt-4 flex items-center gap-2 font-medium text-slate-800">
                <step.icon className="h-5 w-5 text-emerald-600" aria-hidden="true" />
                {step.label}
              </span>
            </div>
          ))}
        </div>
      </Section>
    </>
  )
}
