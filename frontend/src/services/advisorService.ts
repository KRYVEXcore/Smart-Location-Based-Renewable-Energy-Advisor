export class AdvisorNotConnectedError extends Error {
  constructor() {
    super('AI Advisor is not connected yet. Your message was not sent to any AI service.')
    this.name = 'AdvisorNotConnectedError'
  }
}

// Integration seam for the future AI Advisor. The backend only has an
// interface for it (app/services/ai/ai_advisor_service.py) and no endpoint, so
// this rejects instead of inventing a reply. When a real endpoint exists,
// replace the body with an apiPost call and return its answer.
export async function askAdvisor(_message: string): Promise<string> {
  throw new AdvisorNotConnectedError()
}
