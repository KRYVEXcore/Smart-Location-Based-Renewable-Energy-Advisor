import { useState } from 'react'
import { Activity } from 'lucide-react'
import { Button } from '../components/buttons/Button'
import { Section } from '../components/layout/Section'
import { ConnectSystemDialog } from '../components/monitoring/ConnectSystemDialog'

// There is no device integration or telemetry store yet, so the only honest
// state is "nothing connected". Do not add sample readings here.
export function MonitoringPage() {
  const [isConnectOpen, setIsConnectOpen] = useState(false)

  return (
    <Section width="narrow">
      <h1 className="text-2xl font-bold text-slate-900">Live Energy Monitoring</h1>
      <div className="mt-6 flex flex-col items-center gap-3 rounded-3xl border border-dashed border-slate-300 bg-slate-50 px-6 py-14 text-center">
        <span className="flex h-12 w-12 items-center justify-center rounded-xl bg-white text-slate-400 shadow-sm">
          <Activity className="h-6 w-6" aria-hidden="true" />
        </span>
        <h2 className="text-lg font-semibold text-slate-700">No monitoring system connected</h2>
        <p className="max-w-sm text-sm text-slate-500">
          Connect your installed solar, wind, hybrid or battery system to view live performance here.
        </p>
        <Button onClick={() => setIsConnectOpen(true)} className="mt-2">
          Connect a System
        </Button>
      </div>
      <ConnectSystemDialog open={isConnectOpen} onClose={() => setIsConnectOpen(false)} />
    </Section>
  )
}
