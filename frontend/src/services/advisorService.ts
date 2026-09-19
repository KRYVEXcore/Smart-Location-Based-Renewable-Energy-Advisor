import { apiGet, apiPost } from './apiClient'
import type { AdvisorChatResponse, AdvisorOverview, ChatMessage } from '../types/advisor'

// The browser only ever talks to the SHREA API. The AI provider and its key
// live on the backend, which also builds the assessment context itself.
export function getAdvisorOverview(assessmentId: string): Promise<AdvisorOverview> {
  return apiGet<AdvisorOverview>(`/api/v1/advisor/overview/${assessmentId}`)
}

export function askAdvisor(
  assessmentId: string,
  message: string,
  history: Pick<ChatMessage, 'role' | 'text'>[],
): Promise<AdvisorChatResponse> {
  return apiPost<AdvisorChatResponse>('/api/v1/advisor/chat', {
    assessment_id: assessmentId,
    message,
    history: history.map(({ role, text }) => ({ role, content: text })),
  })
}
