import { useCallback, useEffect, useRef, useState } from 'react'
import { useInfiniteQuery, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  api,
  type AcceptedItem,
  type Item,
  type ItemListResponse,
  type ItemPatch,
  type ItemQuery,
} from '@/lib/api'
import { ApiError } from '@/lib/errors'

export const itemKeys = {
  all: ['items'] as const,
  lists: () => [...itemKeys.all, 'list'] as const,
  list: (query: Omit<ItemQuery, 'cursor'>) => [...itemKeys.lists(), query] as const,
  detail: (id: string) => [...itemKeys.all, 'detail', id] as const,
}

/** Flattened cursor pages. `next_cursor` is null on the last page. */
export function useInfiniteItems(query: Omit<ItemQuery, 'cursor'>) {
  return useInfiniteQuery({
    queryKey: itemKeys.list(query),
    queryFn: ({ pageParam }) =>
      api.listItems({ ...query, limit: query.limit ?? 24, cursor: pageParam }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (last: ItemListResponse) => last.next_cursor ?? undefined,
  })
}

/**
 * While an item is still in flight the detail view keeps up with it, so a
 * freshly uploaded or requeued screenshot turns over to its real state without
 * the reader having to reopen it. A settled item stops polling.
 */
export function useItem(id: string | undefined) {
  return useQuery({
    queryKey: itemKeys.detail(id ?? ''),
    queryFn: () => api.getItem(id as string),
    enabled: Boolean(id),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status === 'pending' || status === 'processing' ? 1000 : false
    },
    retry: (count, error) => !(error instanceof ApiError && error.isNotFound) && count < 2,
  })
}

const TERMINAL = new Set(['ready', 'failed', 'deferred'])

/**
 * Polls one item until it reaches a terminal state. Backoff starts at 800ms
 * and is capped at 4s; after `giveUpAfterMs` the poll stops and the caller
 * shows a still-processing state instead of spinning forever.
 */
export function useItemStatusPoll(id: string, options?: { initialDelayMs?: number; maxDelayMs?: number; giveUpAfterMs?: number }) {
  const initialDelayMs = options?.initialDelayMs ?? 800
  const maxDelayMs = options?.maxDelayMs ?? 4000
  const giveUpAfterMs = options?.giveUpAfterMs ?? 60_000

  const [item, setItem] = useState<Item | null>(null)
  const [gaveUp, setGaveUp] = useState(false)
  const [error, setError] = useState<ApiError | null>(null)

  // Every restart of a poll is driven by this token, so a manual refresh can
  // begin a fresh attempt without remounting the card.
  const [attempt, setAttempt] = useState(0)
  const timerRef = useRef<number | null>(null)

  const refresh = useCallback(() => {
    setGaveUp(false)
    setItem(null)
    setAttempt((value) => value + 1)
  }, [])

  // Derived rather than stored, so a poll restart never has to write it back.
  const settled =
    gaveUp || error !== null || (item !== null && TERMINAL.has(item.status))

  useEffect(() => {
    let cancelled = false
    let delay = initialDelayMs
    const startedAt = Date.now()

    const stop = () => {
      if (timerRef.current !== null) {
        window.clearTimeout(timerRef.current)
        timerRef.current = null
      }
    }

    const tick = async () => {
      if (cancelled) return
      try {
        const next = await api.getItem(id)
        if (cancelled) return
        setItem(next)
        setError(null)

        if (TERMINAL.has(next.status)) {
          stop()
          return
        }
        if (Date.now() - startedAt >= giveUpAfterMs) {
          setGaveUp(true)
          stop()
          return
        }
        delay = Math.min(Math.round(delay * 1.6), maxDelayMs)
      } catch (cause) {
        if (cancelled) return
        if (cause instanceof ApiError && cause.isNotFound) {
          setError(cause)
          stop()
          return
        }
        // A single dropped poll is not a failure; keep the same delay.
        if (Date.now() - startedAt >= giveUpAfterMs) {
          setGaveUp(true)
          stop()
          return
        }
      }
      timerRef.current = window.setTimeout(() => void tick(), delay)
    }

    void tick()

    return () => {
      cancelled = true
      stop()
    }
  }, [id, attempt, initialDelayMs, maxDelayMs, giveUpAfterMs])

  return { item, error, gaveUp, settled, refresh }
}

/**
 * Reanalyze writes the item back to pending immediately, so the cached item is
 * updated in place and the detail view starts showing the in-flight state.
 */
export function useReanalyze() {
  const queryClient = useQueryClient()
  return useMutation<AcceptedItem, ApiError, string>({
    mutationFn: (id: string) => api.reanalyze(id),
    onSuccess: (accepted, id) => {
      queryClient.setQueryData(itemKeys.detail(id), (previous: Item | undefined) =>
        previous ? { ...previous, status: accepted.status, error_code: null } : previous,
      )
      void queryClient.invalidateQueries({ queryKey: itemKeys.lists() })
    },
  })
}

/**
 * Cached list data comes in two shapes in this app: an infinite query holds
 * `{ pages, pageParams }`, and a single page holds `{ items, next_cursor }`.
 * Both are rewritten in place so an optimistic edit reaches every grid the
 * reader might have open.
 */
function mapItemsInCache(
  cache: unknown,
  id: string,
  transform: (item: Item) => Item,
): unknown {
  if (!cache || typeof cache !== 'object') return cache
  const value = cache as { pages?: ItemListResponse[]; items?: Item[] }

  if (Array.isArray(value.pages)) {
    return {
      ...value,
      pages: value.pages.map((page) => ({
        ...page,
        items: page.items.map((item) => (item.id === id ? transform(item) : item)),
      })),
    }
  }
  if (Array.isArray(value.items)) {
    return { ...value, items: value.items.map((item) => (item.id === id ? transform(item) : item)) }
  }
  return cache
}

/**
 * Optimistic correction with rollback. The previous snapshot is restored if the
 * PATCH is refused, which happens while an analysis owns the item.
 */
export function usePatchItem(id: string) {
  const queryClient = useQueryClient()
  const detailKey = itemKeys.detail(id)

  return useMutation<Item, ApiError, ItemPatch>({
    mutationFn: (patch: ItemPatch) => api.patchItem(id, patch),
    onMutate: async (patch) => {
      await queryClient.cancelQueries({ queryKey: detailKey })
      const previousDetail = queryClient.getQueryData<Item>(detailKey)
      const previousLists = queryClient.getQueriesData<unknown>({ queryKey: itemKeys.lists() })

      const apply = (item: Item): Item => ({
        ...item,
        ...(patch.title !== undefined ? { title: patch.title } : {}),
        ...(patch.tags !== undefined ? { tags: patch.tags ?? [] } : {}),
        ...(patch.labels !== undefined ? { labels: patch.labels ?? {} } : {}),
        user_corrected: true,
      })

      if (previousDetail) {
        queryClient.setQueryData(detailKey, apply(previousDetail))
      }
      for (const [key, page] of previousLists) {
        const next = mapItemsInCache(page, id, apply)
        if (next !== page) queryClient.setQueryData(key, next)
      }

      return { previousDetail, previousLists }
    },
    onError: (_error, _patch, context) => {
      const rollback = context as
        | { previousDetail: Item | undefined; previousLists: [readonly unknown[], unknown][] }
        | undefined
      if (!rollback) return
      if (rollback.previousDetail) queryClient.setQueryData(detailKey, rollback.previousDetail)
      for (const [key, page] of rollback.previousLists) {
        if (page) queryClient.setQueryData(key, page)
      }
    },
    onSuccess: (item) => {
      queryClient.setQueryData(detailKey, item)
      void queryClient.invalidateQueries({ queryKey: itemKeys.lists() })
    },
  })
}

export function useDeleteItem() {
  const queryClient = useQueryClient()
  return useMutation<void, ApiError, string>({
    mutationFn: (id: string) => api.deleteItem(id),
    onSuccess: (_result, id) => {
      queryClient.removeQueries({ queryKey: itemKeys.detail(id) })
      void queryClient.invalidateQueries({ queryKey: itemKeys.lists() })
    },
  })
}
