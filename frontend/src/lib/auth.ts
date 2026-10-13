/**
 * Account calls. The session lives in an httpOnly cookie the backend sets, so
 * nothing here reads, stores or sends a token: every request is plain
 * same-origin `fetch`, and the browser attaches the cookie on its own.
 *
 * The backend's OpenAPI document is generated from a running server; these types
 * are declared by hand instead because `npm run api-types` would replace the
 * whole file and the auth schema is small enough to keep stable.
 */
import { ApiError, toApiError, toTransportError } from './errors'

const BASE = '/api/v1'

export type Account = {
  id: string
  email: string
  created_at: string
}

export type AuthStatus = {
  /** How many accounts exist. Zero means nobody has signed up yet. */
  users: number
  /** Whether the API will accept a new account right now. */
  registration_open: boolean
}

type Session = {
  user: Account
  /** ISO timestamp; useful for "your session lasts until" copy, nothing more. */
  expires_at: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, init)
  } catch (cause) {
    throw toTransportError(cause)
  }
  if (!response.ok) throw await toApiError(response)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

function jsonInit(method: 'POST', body: unknown): RequestInit {
  return {
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  }
}

/**
 * `GET /auth/me` answers the only question the app needs at start-up: is there a
 * valid session cookie? A 401 is an expected answer here, not a failure, so it
 * resolves to null instead of throwing.
 */
export async function fetchAccount(): Promise<Account | null> {
  try {
    return await request<Account>('/auth/me')
  } catch (error) {
    if (error instanceof ApiError && error.isUnauthorized) return null
    throw error
  }
}

export const auth = {
  /** Unauthenticated. Drives whether the sign-in page offers "create account". */
  status: () => request<AuthStatus>('/auth/status'),

  signIn: (email: string, password: string) =>
    request<Session>('/auth/login', jsonInit('POST', { email, password })),

  createAccount: (email: string, password: string) =>
    request<Session>('/auth/register', jsonInit('POST', { email, password })),

  signOut: () => request<void>('/auth/logout', { method: 'POST' }),

  /** Revokes every session for the account, including this browser's. */
  signOutEverywhere: () => request<void>('/auth/logout-all', { method: 'POST' }),
}