const API_BASE_URL = import.meta.env.VITE_API_BASE_URL as string | undefined

if (!API_BASE_URL) {
  console.warn(
    'VITE_API_BASE_URL is not set. Copy frontend/.env.example to frontend/.env and set it.',
  )
}

// FastAPI's own shape for a 422 response: {"detail": [{"loc": [...], "msg": "...", "type": "..."}]}.
export interface ValidationErrorDetail {
  loc: (string | number)[]
  msg: string
  type: string
}

export class ApiError extends Error {
  status: number
  // Only populated for a 422 whose body was FastAPI's structured
  // validation-error array — lets callers show a field-specific message
  // instead of a flat string.
  validationErrors?: ValidationErrorDetail[]

  constructor(message: string, status: number, validationErrors?: ValidationErrorDetail[]) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.validationErrors = validationErrors
  }
}

// Thrown when fetch itself never got a response (server unreachable, DNS
// failure, offline) — distinguishable from ApiError so the UI can tell
// "the server said no" apart from "we couldn't reach the server at all".
export class NetworkError extends Error {
  constructor(cause: unknown) {
    super('Could not connect to the server.')
    this.name = 'NetworkError'
    this.cause = cause
  }
}

async function parseErrorBody(
  response: Response,
): Promise<{ message?: string; validationErrors?: ValidationErrorDetail[] }> {
  try {
    const data: unknown = await response.json()
    if (data && typeof data === 'object' && 'detail' in data) {
      const detail = (data as { detail: unknown }).detail
      if (typeof detail === 'string') return { message: detail }
      if (Array.isArray(detail)) {
        const validationErrors = detail.filter(
          (item): item is ValidationErrorDetail =>
            item && typeof item === 'object' && Array.isArray((item as ValidationErrorDetail).loc),
        )
        if (validationErrors.length > 0) return { validationErrors }
      }
    }
  } catch {
    // Response body wasn't JSON — fall back to the generic message.
  }
  return {}
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const baseUrl = API_BASE_URL ?? ''
  let response: Response
  try {
    response = await fetch(`${baseUrl}${path}`, init)
  } catch (cause) {
    // fetch rejects (rather than resolving with a non-ok response) only
    // when it never reached a server at all — offline, DNS failure, or
    // the backend process isn't running/listening.
    throw new NetworkError(cause)
  }

  if (!response.ok) {
    const { message, validationErrors } = await parseErrorBody(response)
    throw new ApiError(
      message ?? `Request to ${path} failed with status ${response.status}`,
      response.status,
      validationErrors,
    )
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

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
}
