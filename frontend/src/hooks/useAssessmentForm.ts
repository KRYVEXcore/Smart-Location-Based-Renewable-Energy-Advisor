import { useState } from 'react'
import { INITIAL_ASSESSMENT_DATA, type AssessmentData } from '../types/assessment'
import { validateMonthlyBill, validateOptionalUnits } from '../utils/billInput'

export const TOTAL_STEPS = 5

export function useAssessmentForm() {
  const [step, setStep] = useState(1)
  const [data, setData] = useState<AssessmentData>(INITIAL_ASSESSMENT_DATA)

  function updateField<K extends keyof AssessmentData>(key: K, value: AssessmentData[K]) {
    setData((prev) => ({ ...prev, [key]: value }))
  }

  function updateFields(patch: Partial<AssessmentData>) {
    setData((prev) => ({ ...prev, ...patch }))
  }

  // Step 1 requires an actual confirmed coordinate, not just typed text —
  // a location "label" with no usable latitude/longitude would silently
  // reach later steps with nothing for Phase 3+ to resolve.
  const canContinue =
    step === 1
      ? data.latitude !== null && data.longitude !== null
      : step === 2
        ? data.buildingType !== null
        : step === 3
          ? validateMonthlyBill(data.monthlyBillInr).ok && validateOptionalUnits(data.monthlyUnitsKwh).ok
          : true

  function goNext() {
    if (canContinue) setStep((prev) => Math.min(prev + 1, TOTAL_STEPS))
  }

  function goBack() {
    setStep((prev) => Math.max(prev - 1, 1))
  }

  function goToStep(target: number) {
    setStep(Math.min(Math.max(target, 1), TOTAL_STEPS))
  }

  return { step, data, updateField, updateFields, canContinue, goNext, goBack, goToStep }
}
