import { useState } from 'react'
import { INITIAL_ASSESSMENT_DATA, type AssessmentData } from '../types/assessment'

export const TOTAL_STEPS = 4

export function useAssessmentForm() {
  const [step, setStep] = useState(1)
  const [data, setData] = useState<AssessmentData>(INITIAL_ASSESSMENT_DATA)

  function updateField<K extends keyof AssessmentData>(key: K, value: AssessmentData[K]) {
    setData((prev) => ({ ...prev, [key]: value }))
  }

  function updateFields(patch: Partial<AssessmentData>) {
    setData((prev) => ({ ...prev, ...patch }))
  }

  const canContinue = step === 2 ? data.buildingType !== null : true

  function goNext() {
    if (canContinue) setStep((prev) => Math.min(prev + 1, TOTAL_STEPS))
  }

  function goBack() {
    setStep((prev) => Math.max(prev - 1, 1))
  }

  return { step, data, updateField, updateFields, canContinue, goNext, goBack }
}
