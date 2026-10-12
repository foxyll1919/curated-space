/**
 * The backend returns one error envelope for the whole API:
 *
 *   { "error": { "code": string, "message": string, "request_id": string | null } }
 *
 * The OpenAPI document does not declare this shape, so it is defined here
 * rather than generated. `request_id` is echoed in the `X-Request-Id` response
 * header on every response, which is the fallback when the body omits it.
 */
type ErrorEnvelope = {
  error?: {
    code?: unknown
    message?: unknown
    request_id?: unknown
  }
}

export const FALLBACK_ERROR_CODE = 'network_error'

export class ApiError extends Error {
  readonly status: number
  readonly code: string
  readonly requestId: string | null

  constructor(init: { status: number; code: string; message: string; requestId: string | null }) {
    super(init.message)
    this.name = 'ApiError'
    this.status = init.status
    this.code = init.code
    this.requestId = init.requestId
  }

  /** Uploads are limited to 10 per 60s; the client queues instead of hammering. */
  get isRateLimited(): boolean {
    return this.status === 429 || this.code === 'rate_limited'
  }

  get isNotFound(): boolean {
    return this.status === 404 || this.code === 'not_found'
  }

  /** The item cannot be corrected or requeued while the pipeline owns it. */
  get isConflict(): boolean {
    return this.status === 409 || this.code === 'conflict'
  }

  /** The backend is reachable but refusing the key we hold. */
  get isUnauthorized(): boolean {
    return this.status === 401 || this.code === 'unauthorized'
  }
}

function headerRequestId(response: Response): string | null {
  return response.headers.get('X-Request-Id')
}

/**
 * Turn any non-2xx response, or a transport failure, into an ApiError. Nothing
 * in the UI ever reads a raw Response or a rejected fetch.
 */
export async function toApiError(response: Response): Promise<ApiError> {
  let code = 'http_error'
  let message = 'The request could not be completed.'
  let requestId = headerRequestId(response)

  try {
    const body: unknown = await response.json()
    if (body && typeof body === 'object' && 'error' in body) {
      const error = (body as ErrorEnvelope).error
      if (error && typeof error.code === 'string') code = error.code
      if (error && typeof error.message === 'string' && error.message) message = error.message
      if (error && typeof error.request_id === 'string') requestId = error.request_id
    }
  } catch {
    // A proxy or an upstream crash can answer with HTML. The status code and
    // the request id header are still usable, so keep them.
  }

  return new ApiError({ status: response.status, code, message, requestId })
}

export function toTransportError(cause: unknown): ApiError {
  const message =
    cause instanceof DOMException && cause.name === 'AbortError'
      ? 'The request was cancelled.'
      : 'Could not reach the server. Check that the backend is running.'
  return new ApiError({ status: 0, code: FALLBACK_ERROR_CODE, message, requestId: null })
}