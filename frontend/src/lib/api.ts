import type { components } from './api-types'
import { ApiError, toApiError, toTransportError } from './errors'

export type ItemResponse = components['schemas']['ItemResponse']

/**
 * The generated contract leaves `status`, `tags` and `labels` optional because
 * the OpenAPI document does not mark them required. Everything the interface
 * relies on is non-optional here: `normalizeItem` fills the gaps once, in the
 * API layer, so no component has to defend against a missing array.
 *
 * A status outside the five documented states is treated as `failed`, which is
 * the only remaining terminal state, so every card still has a designed state.
 */
export type Item = Omit<ItemResponse, 'status' | 'tags' | 'labels'> & {
  status: ItemStatus
  tags: string[]
  labels: Record<string, string>
}

export function normalizeItem(raw: ItemResponse): Item {
  return {
    ...raw,
    status: isItemStatus(raw.status) ? raw.status : 'failed',
    tags: raw.tags ?? [],
    labels: raw.labels ?? {},
  }
}

export type ItemListResponse = Omit<components['schemas']['ItemListResponse'], 'items'> & {
  items: Item[]
}
export type AcceptedItem = components['schemas']['AcceptedItem']
export type ItemPatch = components['schemas']['ItemPatch']
export type Usage = components['schemas']['UsageResponse']
export type UsageWindow = components['schemas']['UsageWindow']
export type Ready = components['schemas']['ReadyResponse']
export type Health = components['schemas']['HealthResponse']
export type ImageInfo = components['schemas']['ImageInfo']

/**
 * The backend documents five item states. `pending` and `processing` are the
 * two in-flight states; the rest are terminal.
 */
export const ITEM_STATUSES = ['pending', 'processing', 'ready', 'failed', 'deferred'] as const
export type ItemStatus = (typeof ITEM_STATUSES)[number]

const TERMINAL_STATUSES: ReadonlySet<string> = new Set<ItemStatus>(['ready', 'failed', 'deferred'])
export function isTerminalStatus(status: string): boolean {
  return TERMINAL_STATUSES.has(status)
}

export function isItemStatus(value: string): value is ItemStatus {
  return (ITEM_STATUSES as readonly string[]).includes(value)
}

/** Statuses a person can filter by. In-flight states are still filterable. */
export const FILTERABLE_STATUSES: readonly { value: ItemStatus; label: string }[] = [
  { value: 'ready', label: 'Analyzed' },
  { value: 'pending', label: 'Pending' },
  { value: 'processing', label: 'Processing' },
  { value: 'deferred', label: 'Saved, not analyzed' },
  { value: 'failed', label: 'Failed' },
]

const BASE = '/api/v1'

export type ItemQuery = {
  q?: string
  status?: ItemStatus
  label?: string
  limit?: number
  cursor?: string
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

/** Only sent when a JSON body is present; multipart relies on the browser boundary. */
function jsonInit(method: 'PATCH', body: unknown): RequestInit {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }
}

export function buildItemSearchParams(query: ItemQuery): URLSearchParams {
  const params = new URLSearchParams()
  if (query.q) params.set('q', query.q)
  if (query.status) params.set('status', query.status)
  if (query.label) params.set('label', query.label)
  if (query.limit) params.set('limit', String(query.limit))
  if (query.cursor) params.set('cursor', query.cursor)
  return params
}

export const api = {
  health: () => request<Health>('/health'),

  ready: () => request<Ready>('/ready'),

  usage: () => request<Usage>('/usage'),

  listItems: async (query: ItemQuery = {}) => {
    const page = await request<components['schemas']['ItemListResponse']>(
      `/items?${buildItemSearchParams(query).toString()}`,
    )
    return { ...page, items: page.items.map(normalizeItem) }
  },

  getItem: async (id: string) => normalizeItem(await request<ItemResponse>(`/items/${encodeURIComponent(id)}`)),

  /**
   * Returns 202 immediately with the item id; analysis happens in the
   * background. Content-Type is deliberately not set so the browser can add the
   * multipart boundary itself.
   */
  upload: (file: File, skipAnalysis: boolean) => {
    const form = new FormData()
    form.append('file', file, file.name)
    if (skipAnalysis) form.append('skip_analysis', 'true')
    return request<AcceptedItem>('/items', { method: 'POST', body: form })
  },

  reanalyze: (id: string) =>
    request<AcceptedItem>(`/items/${encodeURIComponent(id)}/reanalyze`, { method: 'POST' }),

  patchItem: async (id: string, patch: ItemPatch) =>
    normalizeItem(
      await request<ItemResponse>(`/items/${encodeURIComponent(id)}`, jsonInit('PATCH', patch)),
    ),

  deleteItem: (id: string) => request<void>(`/items/${encodeURIComponent(id)}`, { method: 'DELETE' }),

  /**
   * The dev-server proxy attaches the API key, so the browser can load the
   * sanitized PNG straight from this same-origin URL.
   */
  imageUrl: (id: string) => `${BASE}/items/${encodeURIComponent(id)}/image`,
}

/**
 * The backend may attach a single legacy category label. It is rendered as a
 * plain chip and nothing more: the taxonomy is being replaced, so no label set
 * is hardcoded and no list of labels is hardcoded in this client.
 */
export function labelEntries(item: Pick<Item, 'labels'>): [string, string][] {
  return Object.entries(item.labels ?? {})
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError
}