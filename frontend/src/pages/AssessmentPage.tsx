import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'
import { Section } from '../components/layout/Section'
import { ProgressBar } from '../components/assessment/ProgressBar'
import { LocationStep } from '../components/assessment/LocationStep'
import { BuildingTypeStep } from '../components/assessment/BuildingTypeStep'
import { ConsumptionStep } from '../components/assessment/ConsumptionStep'
import { ConstraintsStep } from '../components/assessment/ConstraintsStep'
import { ReviewStep } from '../components/assessment/ReviewStep'
import { useAssessmentForm, TOTAL_STEPS } from '../hooks/useAssessmentForm'
import { createAssessment } from '../services/assessmentService'
import { ApiError, NetworkError, type ValidationErrorDetail } from '../services/apiClient'
import { toAssessmentCreatePayload } from '../utils/assessmentMapper'

const STEP_LABELS = ['Location', 'Building type', 'Energy use', 'Constraints', 'Review']

interface FieldErrors {
  location?: string
  buildingType?: string
  consumption?: string
  roofAreaSqft?: string
  landAreaSqft?: string
  budget?: string
}

function mapValidationErrors(errors: ValidationErrorDetail[]): { fieldErrors: FieldErrors; firstStep: number } {
  const fieldErrors: FieldErrors = {}
  let firstStep = TOTAL_STEPS

  for (const err of errors) {
    const path = err.loc.map(String).join('.')
    if (path.includes('location') && !fieldErrors.location) {
      fieldErrors.location = err.msg
      firstStep = Math.min(firstStep, 1)
    } else if (path.includes('building') && !fieldErrors.buildingType) {
      fieldErrors.buildingType = err.msg
      firstStep = Math.min(firstStep, 2)
    } else if (path.includes('monthly_consumption_kwh')) {
      fieldErrors.consumption = err.msg
      firstStep = Math.min(firstStep, 3)
    } else if (path.includes('roof_area_sqft')) {
      fieldErrors.roofAreaSqft = err.msg
      firstStep = Math.min(firstStep, 4)
    } else if (path.includes('land_area_sqft')) {
      fieldErrors.landAreaSqft = err.msg
      firstStep = Math.min(firstStep, 4)
    } else if (path.includes('budget_inr')) {
      fieldErrors.budget = err.msg
      firstStep = Math.min(firstStep, 4)
    }
  }

  return { fieldErrors, firstStep }
}

export function AssessmentPage() {
  const navigate = useNavigate()
  const { step, data, updateField, updateFields, canContinue, goNext, goBack, goToStep } = useAssessmentForm()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({})

  function handleBack() {
    goBack()
  }

  function handleContinue() {
    setSubmitError(null)
    goNext()
  }

  async function handleSubmit() {
    if (!data.buildingType) {
      setSubmitError('Please go back and select a building type.')
      goToStep(2)
      return
    }

    setSubmitError(null)
    setFieldErrors({})
    setIsSubmitting(true)
    try {
      const assessment = await createAssessment(toAssessmentCreatePayload(data))
      navigate(`/dashboard/${assessment.id}`)
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.status === 422 && error.validationErrors && error.validationErrors.length > 0) {
          const { fieldErrors: mapped, firstStep } = mapValidationErrors(error.validationErrors)
          setFieldErrors(mapped)
          setSubmitError('Please check the highlighted assessment details.')
          goToStep(firstStep)
        } else if (error.status >= 500) {
          setSubmitError('Something went wrong while saving your assessment. Please try again.')
        } else if (error.status === 404) {
          setSubmitError('Something went wrong while saving your assessment. Please try again.')
        } else {
          setSubmitError('Please check the highlighted assessment details.')
        }
      } else if (error instanceof NetworkError) {
        setSubmitError('Could not connect to the server. Check your connection and try again.')
      } else {
        setSubmitError('Something went wrong while saving your assessment. Please try again.')
      }
      setIsSubmitting(false)
    }
  }

  return (
    <Section width="narrow">
      <ProgressBar current={step} total={TOTAL_STEPS} label={STEP_LABELS[step - 1] ?? ''} />

      <div className="mt-10 rounded-3xl border border-slate-200 bg-white p-6 sm:p-10">
        {step === 1 && (
          <LocationStep
            value={{
              locationQuery: data.locationQuery,
              latitude: data.latitude,
              longitude: data.longitude,
              locationCity: data.locationCity,
              locationState: data.locationState,
              locationCountry: data.locationCountry,
            }}
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
            error={fieldErrors.consumption}
          />
        )}
        {step === 4 && (
          <ConstraintsStep
            value={data}
            onChange={updateFields}
            errors={{
              roofAreaSqft: fieldErrors.roofAreaSqft,
              landAreaSqft: fieldErrors.landAreaSqft,
              budget: fieldErrors.budget,
            }}
          />
        )}
        {step === 5 && <ReviewStep data={data} onEditStep={goToStep} />}

        {submitError && (
          <p role="alert" className="mt-6 rounded-xl bg-amber-50 px-4 py-3 text-sm text-amber-700">
            {submitError}
          </p>
        )}

        <div className="mt-10 flex items-center justify-between border-t border-slate-100 pt-6">
          <button
            type="button"
            onClick={handleBack}
            disabled={step === 1 || isSubmitting}
            className="flex items-center gap-1.5 rounded-full px-4 py-2.5 text-sm font-semibold text-slate-600 transition-colors hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-0"
          >
            <ChevronLeft className="h-4 w-4" aria-hidden="true" />
            Back
          </button>
          {step < TOTAL_STEPS ? (
            <button
              type="button"
              onClick={handleContinue}
              disabled={!canContinue}
              className="flex items-center gap-1.5 rounded-full bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Continue
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          ) : (
            <button
              type="button"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="flex items-center gap-1.5 rounded-full bg-emerald-600 px-6 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />
                  Saving assessment…
                </>
              ) : (
                'Submit Assessment'
              )}
            </button>
          )}
        </div>
      </div>
    </Section>
  )
}
