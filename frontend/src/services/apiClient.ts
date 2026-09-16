const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined

if (!API_BASE_URL) {
  console.warn(
    'VITE_API_BASE_URL is not set. Copy frontend/.env.example to frontend/.env and set it.',
  )
}

export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function extractErrorMessage(response: Response): Promise<string | undefined> {
  try {
    const data: unknown = await response.json()
    if (data && typeof data === 'object' && 'detail' in data) {
      const detail = (data as { detail: unknown }).detail
      if (typeof detail === 'string') return detail
    }
  } catch {
    // Response body wasn't JSON — fall back to the generic message.
  }
  return undefined
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = API_BASE_URL ?? ''
  const response = await fetch(`${baseUrl}${path}`, init)

  if (!response.ok) {
    const detail = await extractErrorMessage(response)
    throw new ApiError(detail ?? `Request to ${path} failed with status ${response.status}`, response.status)
  }

  if (response.status === 204) {
    return undefined as T
  }

  return response.json() as Promise<T>
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path)
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
