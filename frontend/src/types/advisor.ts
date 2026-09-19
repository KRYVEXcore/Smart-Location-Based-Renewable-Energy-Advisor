export interface ChatMessage {
  id: number
  role: 'user' | 'assistant'
  text: string
}

export interface AdvisorOverview {
  assessment_id: string
  ai_configured: boolean
  location_label: string | null
  building_type: string
  monthly_consumption_kwh: number | null
  available: Record<string, boolean>
  suggested_questions: string[]
}

export interface AdvisorChatResponse {
  status: 'ok' | 'ai_not_configured' | 'ai_error'
  message: string | null
  error_code: string | null
  assessment_id: string
  provider: string | null
  model: string | null
}
