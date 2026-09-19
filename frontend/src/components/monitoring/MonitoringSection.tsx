import { useState } from 'react'
import { TechnologyCard } from '../cards/TechnologyCard'
import { Button } from '../buttons/Button'
import { Section } from '../layout/Section'
import { ConnectSystemDialog } from './ConnectSystemDialog'
import { MONITORED_SYSTEMS } from './monitoredSystems'

const CAPABILITIES = [
  'Live and daily generation',
  'Monthly generation and historical trends',
  'System status and alerts',
  'Battery state of charge, charging and discharging',
  'Renewable contribution',
]

// Static illustration only. These figures are not measurements from any
// system and must stay labelled as an example.
const PREVIEW_TILES = [
  { label: 'Solar', value: '4.8 kW', note: 'Generating' },
  { label: 'Wind', value: '1.2 kW', note: 'Generating' },
  { label: 'Battery', value: '78%', note: 'Charge' },
  { label: 'Today', value: '28.4 kWh', note: 'Generation' },
]

export function MonitoringSection() {
  const [isConnectOpen, setIsConnectOpen] = useState(false)

  return (
    <Section id="monitoring">
      <div className="grid items-center gap-10 lg:grid-cols-2 lg:gap-12">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wide text-emerald-700">Live Energy Monitoring</span>
          <h2 className="mt-2 text-2xl font-bold text-slate-900 sm:text-3xl">Monitor Your Existing Renewable System</h2>
          <p className="mt-3 text-slate-500">
            Already have a renewable energy system? Connect it to SHREA AI and track its performance from one place.
          </p>
          <p className="mt-4 text-sm font-medium text-slate-700">When connected, supported monitoring data can include:</p>
          <ul className="mt-2 space-y-1 text-sm text-slate-500">
            {CAPABILITIES.map((item) => (
              <li key={item} className="flex gap-2">
                <span aria-hidden="true" className="text-emerald-600">
                  •
                </span>
                {item}
              </li>
            ))}
          </ul>
          <div className="mt-6 flex flex-col gap-3 sm:flex-row">
            <Button size="lg" onClick={() => setIsConnectOpen(true)}>
              Connect a System
            </Button>
            <Button to="/monitoring" size="lg" variant="secondary">
              Open monitoring
            </Button>
          </div>
        </div>

        <div className="min-w-0 rounded-3xl border border-dashed border-slate-300 bg-slate-50 p-5" role="group" aria-label="Example dashboard, not real data">
          <div className="flex items-center justify-between gap-3">
            <span className="text-sm font-semibold text-slate-700">Example dashboard</span>
            <span className="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">UI Preview</span>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {PREVIEW_TILES.map((tile) => (
              <div key={tile.label} className="min-w-0 rounded-2xl border border-slate-200 bg-white p-4">
                <p className="text-xs uppercase tracking-wide text-slate-400">{tile.label}</p>
                <p className="mt-1 text-xl font-bold text-slate-400">{tile.value}</p>
                <p className="text-xs text-slate-400">{tile.note}</p>
              </div>
            ))}
          </div>
          <p className="mt-3 text-xs text-slate-500">Illustrative values only. Not from a real system.</p>
        </div>
      </div>

      <div className="mt-10 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {MONITORED_SYSTEMS.map((system) => (
          <TechnologyCard key={system.name} {...system} />
        ))}
      </div>

      <ConnectSystemDialog open={isConnectOpen} onClose={() => setIsConnectOpen(false)} />
    </Section>
  )
}
