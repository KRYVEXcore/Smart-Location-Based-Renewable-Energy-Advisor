export type AdvisorState = 'ready' | 'listening' | 'processing' | 'responding'

export const ADVISOR_STATE_LABELS: Record<AdvisorState, string> = {
  ready: 'Ready',
  listening: 'Listening',
  processing: 'Processing',
  responding: 'Responding',
}
