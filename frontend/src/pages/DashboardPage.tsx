import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import {
  AlertTriangle,
  BatteryCharging,
  Gauge,
  Loader2,
  MapPin,
  PiggyBank,
  Sun,
  TrendingUp,
  Wind,
  Zap,
} from 'lucide-react'
import { Button } from '../components/buttons/Button'
import { Section } from '../components/layout/Section'
import { MetricCard } from '../components/metrics/MetricCard'
import { ComparisonCard } from '../components/cards/ComparisonCard'
import { LocationIntelligenceSection } from '../components/location/LocationIntelligenceSection'
import { SolarAnalysisSection } from '../components/solar/SolarAnalysisSection'
import { ElectricityTariffSection } from '../components/tariff/ElectricityTariffSection'
import { getAssessment } from '../services/assessmentService'
import { ApiError } from '../services/apiClient'
import { useLocationProfile } from '../hooks/useLocationProfile'
import { useSolarCalculation } from '../hooks/useSolarCalculation'
import { useTariffCalculation } from '../hooks/useTariffCalculation'
import type { AssessmentResponse } from '../types/assessmentApi'

const COMPARISON_TECHNOLOGIES = [
  { icon: Sun, name: 'Solar', gradient: 'from-amber-400 to-orange-500' },
  { icon: Wind, name: 'Wind', gradient: 'from-sky-400 to-blue-500' },
  { icon: Zap, name: 'Hybrid', gradient: 'from-violet-400 to-fuchsia-500' },
  { icon: BatteryCharging, name: 'Battery', gradient: 'from-emerald-400 to-teal-500' },
]

type LoadState = 'empty' | 'loading' | 'ready' | 'error'

export function DashboardPage() {
  const { assessmentId } = useParams<{ assessmentId: string }>()
  // Remounts DashboardContent fresh whenever the id changes, so loading
  // state can be derived at initialization instead of reset from an effect.
  return <DashboardContent key={assessmentId ?? 'empty'} assessmentId={assessmentId} />
}

function DashboardContent({ assessmentId }: { assessmentId: string | undefined }) {
  const [assessment, setAssessment] = useState<AssessmentResponse | null>(null)
  const [loadState, setLoadState] = useState<LoadState>(assessmentId ? 'loading' : 'empty')
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const { profile, status: profileStatus, fetchProfile } = useLocationProfile()
  const { result: solarResult, status: solarStatus, runCalculation } = useSolarCalculation()
  const { result: tariffResult, status: tariffStatus, runCalculation: runTariffCalculation } = useTariffCalculation()

  useEffect(() => {
    if (!assessmentId) return

    let cancelled = false

    getAssessment(assessmentId)
      .then((data) => {
        if (cancelled) return
        setAssessment(data)
        setLoadState('ready')
      })
      .catch((error: unknown) => {
        if (cancelled) return
        setErrorMessage(
          error instanceof ApiError && error.status === 404
            ? 'This assessment could not be found.'
            : 'Unable to load assessment. Please check your internet connection.',
        )
        setLoadState('error')
      })

    return () => {
      cancelled = true
    }
  }, [assessmentId])

  useEffect(() => {
    if (assessment?.location.latitude != null && assessment.location.longitude != null) {
      fetchProfile(assessment.location.latitude, assessment.location.longitude)
    }
  }, [assessment, fetchProfile])

  useEffect(() => {
    // Waits for the location-intelligence fetch above to settle first. Both
    // effects would otherwise race the same backend location cache with two
    // concurrent, independent provider calls for the same coordinate — for a
    // flaky upstream provider that can return a successful result to one and
    // a transient failure to the other, showing contradictory data in the
    // same page. Sequencing also avoids a redundant external API call.
    const hasCoordinates = assessment?.location.latitude != null && assessment.location.longitude != null
    const locationSettled = !hasCoordinates || profileStatus === 'ready' || profileStatus === 'error'

    if (assessment && locationSettled) {
      runCalculation(assessment.id)
      runTariffCalculation(assessment.id)
    }
  }, [assessment, profileStatus, runCalculation, runTariffCalculation])

  if (loadState === 'empty') {
    return (
      <Section width="narrow" className="text-center">
        <h1 className="text-2xl font-bold text-slate-900">No assessment yet</h1>
        <p className="mt-2 text-slate-500">
          Complete the energy assessment to see your results here.
        </p>
        <Button to="/assess" className="mt-6">
          Start Energy Assessment
        </Button>
      </Section>
    )
  }

  if (loadState === 'loading') {
    return (
      <Section width="narrow" className="flex flex-col items-center text-center">
        <Loader2 className="h-6 w-6 animate-spin text-emerald-600" aria-hidden="true" />
        <p className="mt-3 text-sm text-slate-500">Loading assessment…</p>
      </Section>
    )
  }

  if (loadState === 'error') {
    return (
      <Section width="narrow" className="text-center">
        <AlertTriangle className="mx-auto h-8 w-8 text-amber-500" aria-hidden="true" />
        <h1 className="mt-3 text-2xl font-bold text-slate-900">{errorMessage}</h1>
        <Button to="/assess" className="mt-6">
          Start a new assessment
        </Button>
      </Section>
    )
  }

  if (!assessment) return null

  const hasCoordinates = assessment.location.latitude != null && assessment.location.longitude != null

  return (
    <Section>
      <span className="text-xs font-semibold uppercase tracking-wide text-emerald-700">
        Energy Assessment
      </span>
      <div className="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-sm text-slate-500">
        <span className="flex items-center gap-1.5">
          <MapPin className="h-4 w-4" aria-hidden="true" />
          {assessment.location.formatted_address || 'Location not provided'}
        </span>
        <span className="flex items-center gap-1.5">
          <Sun className="h-4 w-4" aria-hidden="true" />
          {profile?.solar?.annual_value != null
            ? `${profile.solar.annual_value.toFixed(2)} ${profile.solar.unit} solar resource`
            : 'Solar resource — see Location Intelligence below'}
        </span>
      </div>

      <div className="mt-6 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          icon={Gauge}
          label="Monthly consumption"
          value={assessment.energy.monthly_consumption_kwh.toString()}
          unit="kWh"
        />
        <MetricCard icon={Zap} label="Recommended capacity" pendingLabel="Awaiting recommendation engine" />
        <MetricCard icon={PiggyBank} label="Estimated savings" pendingLabel="Awaiting financial engine" />
        <MetricCard icon={TrendingUp} label="Payback period" pendingLabel="Awaiting financial engine" />
      </div>

      <h2 className="mt-12 text-xl font-bold text-slate-900">Location intelligence</h2>
      {!hasCoordinates && (
        <div className="mt-5 flex flex-col items-start gap-3 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-slate-500">
            This assessment doesn&apos;t have saved coordinates, so resource data can&apos;t be
            looked up automatically.
          </p>
          <Button to="/location" variant="secondary">
            Look up a location
          </Button>
        </div>
      )}
      {hasCoordinates && profileStatus === 'loading' && (
        <div className="mt-5 flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          Retrieving location intelligence…
        </div>
      )}
      {hasCoordinates && profileStatus === 'error' && (
        <p className="mt-5 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
          Location found, but resource data is unavailable right now.
        </p>
      )}
      {hasCoordinates && profile && (
        <div className="mt-5">
          <LocationIntelligenceSection profile={profile} />
        </div>
      )}

      <h2 className="mt-12 text-xl font-bold text-slate-900">Solar analysis</h2>
      {!hasCoordinates && (
        <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
          This assessment doesn&apos;t have saved coordinates, so solar analysis can&apos;t be
          calculated automatically.
        </div>
      )}
      {hasCoordinates && solarStatus === 'loading' && (
        <div className="mt-5 flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          Calculating solar system options…
        </div>
      )}
      {hasCoordinates && solarStatus === 'error' && (
        <p className="mt-5 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
          Solar analysis is unavailable right now. Please check your internet connection.
        </p>
      )}
      {hasCoordinates && solarResult && (
        <div className="mt-5">
          <SolarAnalysisSection result={solarResult} />
        </div>
      )}

      <h2 className="mt-12 text-xl font-bold text-slate-900">Electricity tariff</h2>
      {!hasCoordinates && (
        <div className="mt-5 rounded-2xl border border-dashed border-slate-300 bg-slate-50 p-6 text-center text-sm text-slate-500">
          This assessment doesn&apos;t have saved coordinates, so an electricity tariff can&apos;t be
          looked up automatically.
        </div>
      )}
      {hasCoordinates && tariffStatus === 'loading' && (
        <div className="mt-5 flex items-center gap-2 text-sm text-slate-500">
          <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
          Looking up the applicable electricity tariff…
        </div>
      )}
      {hasCoordinates && tariffStatus === 'error' && (
        <p className="mt-5 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
          Electricity tariff lookup is unavailable right now. Please check your internet connection.
        </p>
      )}
      {hasCoordinates && tariffResult && (
        <div className="mt-5">
          <ElectricityTariffSection result={tariffResult} />
        </div>
      )}

      <h2 className="mt-12 text-xl font-bold text-slate-900">Technology comparison</h2>
      <div className="mt-5 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {COMPARISON_TECHNOLOGIES.map((tech) => (
          <ComparisonCard key={tech.name} {...tech} />
        ))}
      </div>
    </Section>
  )
}
