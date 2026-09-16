import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { Section } from '../components/layout/Section'
import { ProgressBar } from '../components/assessment/ProgressBar'
import { LocationStep } from '../components/assessment/LocationStep'
import { BuildingTypeStep } from '../components/assessment/BuildingTypeStep'
import { ConsumptionStep } from '../components/assessment/ConsumptionStep'
import { ConstraintsStep } from '../components/assessment/ConstraintsStep'
import { useAssessmentForm, TOTAL_STEPS } from '../hooks/useAssessmentForm'
import { createAssessment } from '../services/assessmentService'
import { toAssessmentCreatePayload } from '../utils/assessmentMapper'

const STEP_LABELS = ['Location', 'Building type', 'Energy use', 'Constraints']

export function AssessmentPage() {
  const navigate = useNavigate()
  const { step, data, updateField, updateFields, canContinue, goNext, goBack } = useAssessmentForm()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  async function handleContinue() {
    if (step < TOTAL_STEPS) {
      goNext()
      return
    }

    if (!data.buildingType) {
      setSubmitError('Please go back and select a building type.')
      return
    }

    setSubmitError(null)
    setIsSubmitting(true)
    try {
      const assessment = await createAssessment(toAssessmentCreatePayload(data))
      navigate(`/dashboard/${assessment.id}`)
    } catch {
      setSubmitError('Could not save assessment. Please check your internet connection and try again.')
      setIsSubmitting(false)
    }
  }

  return (
    <Section width="narrow">
      <ProgressBar current={step} total={TOTAL_STEPS} label={STEP_LABELS[step - 1] ?? ''} />

      <div className="mt-10 rounded-3xl border border-slate-200 bg-white p-6 sm:p-10">
        {step === 1 && (
          <LocationStep
            value={{ locationQuery: data.locationQuery, latitude: data.latitude, longitude: data.longitude }}
            onChange={updateFields}
          />
        )}
        {step === 2 && (
          <BuildingTypeStep
            value={data.buildingType}
            onChange={(value) => updateField('buildingType', value)}
          />
        )}
        {step === 3 && (
          <ConsumptionStep
            value={data.monthlyConsumptionKwh}
            onChange={(value) => updateField('monthlyConsumptionKwh', value)}
          />
        )}
        {step === 4 && <ConstraintsStep value={data} onChange={updateFields} />}

        {submitError && (
          <p role="alert" className="mt-6 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
            {submitError}
          </p>
        )}

        <div className="mt-10 flex items-center justify-between border-t border-slate-100 pt-6">
          <button
            type="button"
            onClick={goBack}
            disabled={step === 1 || isSubmitting}
            className="flex items-center gap-1.5 rounded-full px-4 py-2.5 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-0"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            Back
          </button>
          <button
            type="button"
            onClick={handleContinue}
            disabled={!canContinue || isSubmitting}
            className="flex items-center gap-1.5 rounded-full bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                Saving…
              </>
            ) : (
              <>
                {step === TOTAL_STEPS ? 'View Summary' : 'Continue'}
                <ChevronRight className="h-4 w-4" aria-hidden="true" />
              </>
            )}
          </button>
        </div>
      </div>
    </Section>
  )
}
