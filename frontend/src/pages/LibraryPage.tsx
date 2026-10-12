import { useCallback, useMemo, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { useSearchParams } from 'react-router-dom'
import { AlertCircleIcon, CompassIcon, RefreshCwIcon, SearchXIcon } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ItemCard } from '@/components/ItemCard'
import { MasonryItem } from '@/components/MasonryItem'
import { InfiniteScrollSentinel, PendingCard } from '@/components/PendingCard'
import { LibraryControls, type Filters } from '@/components/LibraryControls'
import { UploadSurface } from '@/components/UploadSurface'
import { isItemStatus, labelEntries, type Item, type ItemStatus } from '@/lib/api'
import { itemRatio } from '@/lib/ratio'
import { itemKeys, useInfiniteItems } from '@/hooks/useItems'
import { placeholderItem, type UploadJob } from '@/hooks/useUpload'

const SKELETON_COUNT = 10
const GRID_CLASSES =
  'grid grid-cols-1 gap-x-4 gap-y-0 [grid-auto-rows:8px] sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5'

function readFilters(params: URLSearchParams): Filters {
  const q = params.get('q') ?? ''
  const status = params.get('status')
  const label = params.get('label')
  return {
    q,
    ...(status && isItemStatus(status) ? { status: status as ItemStatus } : {}),
    ...(label ? { label } : {}),
  }
}

export function LibraryPage() {
  const [params, setParams] = useSearchParams()
  const queryClient = useQueryClient()
  const filters = useMemo(() => readFilters(params), [params])

  /**
   * Screenshots accepted in this session, held locally until the server list
   * catches up. They render above everything else, in the order they arrived.
   */
  const [justSaved, setJustSaved] = useState<Map<string, Item>>(new Map())

  const query = useMemo(
    () => ({ q: filters.q, status: filters.status, label: filters.label }),
    [filters.q, filters.status, filters.label],
  )

  const { data, isPending, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInfiniteItems(query)

  const pages = data?.pages
  const serverItems = useMemo(() => (pages ?? []).flatMap((page) => page.items), [pages])

  /**
   * Labels for the filter menu are gathered from what the backend has actually
   * returned so far. Nothing is assumed about the taxonomy.
   */
  const labels = useMemo(() => {
    const found = new Set<string>()
    for (const item of serverItems) {
      for (const [, value] of labelEntries(item)) found.add(value)
    }
    return [...found].sort((a, b) => a.localeCompare(b))
  }, [serverItems])

  const onChange = useCallback(
    (next: Filters) => {
      const updated = new URLSearchParams()
      if (next.q) updated.set('q', next.q)
      if (next.status) updated.set('status', next.status)
      if (next.label) updated.set('label', next.label)
      setParams(updated, { replace: true })
    },
    [setParams],
  )

  const onAccepted = useCallback(
    (job: UploadJob) => {
      const item = placeholderItem(job)
      if (!item) return
      setJustSaved((current) => new Map(current).set(item.id, item))
      void queryClient.invalidateQueries({ queryKey: itemKeys.lists() })
    },
    [queryClient],
  )

  const onResolved = useCallback(
    (item: Item) => {
      setJustSaved((current) => {
        if (!current.has(item.id)) return current
        const next = new Map(current)
        next.delete(item.id)
        return next
      })
      void queryClient.invalidateQueries({ queryKey: itemKeys.lists() })
    },
    [queryClient],
  )

  /**
   * A card that polled for a full minute without settling is handed back to the
   * server list, where the item keeps its own still-processing state.
   */
  const onGaveUp = useCallback(
    (id: string) => {
      setJustSaved((current) => {
        if (!current.has(id)) return current
        const next = new Map(current)
        next.delete(id)
        return next
      })
      void queryClient.invalidateQueries({ queryKey: itemKeys.lists() })
    },
    [queryClient],
  )

  const optimistic = [...justSaved.values()]
  const optimisticIds = new Set(optimistic.map((item) => item.id))
  const visible = [...optimistic, ...serverItems.filter((item) => !optimisticIds.has(item.id))]
  const total = visible.length

  const filtering = filters.q !== '' || filters.status !== undefined || filters.label !== undefined
  const showEmptyLibrary = !isPending && !isError && total === 0 && !filtering
  const showNoMatches = !isPending && !isError && total === 0 && filtering

  return (
    <div className="mx-auto flex w-full max-w-[1600px] flex-col gap-6 px-4 py-6 sm:px-6 lg:px-8">
      <UploadSurface onAccepted={onAccepted} />

      <LibraryControls
        filters={filters}
        onChange={onChange}
        labels={labels}
        resultCount={isPending ? null : total}
      />

      {isError && error ? (
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertTitle>The library could not be loaded</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            <span>{error.message}</span>
            <Button variant="outline" size="sm" onClick={() => void queryClient.invalidateQueries()}>
              <RefreshCwIcon data-icon="inline-start" />
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      ) : null}

      {isPending ? <GridSkeleton /> : null}

      {showEmptyLibrary ? <EmptyLibrary /> : null}
      {showNoMatches ? <NoMatches filters={filters} onClear={() => onChange({ q: '' })} /> : null}

      {visible.length > 0 ? (
        <ul className={GRID_CLASSES} aria-label="Saved screenshots">
          {visible.map((item) => (
            <MasonryItem key={item.id} ratio={itemRatio(item)}>
              {optimisticIds.has(item.id) ? (
                <PendingCard item={item} onResolved={onResolved} onGaveUp={onGaveUp} />
              ) : (
                <ItemCard item={item} />
              )}
            </MasonryItem>
          ))}
          <InfiniteScrollSentinel
            hasMore={Boolean(hasNextPage)}
            busy={Boolean(isFetchingNextPage)}
            onLoadMore={() => void fetchNextPage()}
          />
        </ul>
      ) : null}
    </div>
  )
}

function GridSkeleton() {
  return (
    <ul className={GRID_CLASSES} aria-hidden="true">
      {Array.from({ length: SKELETON_COUNT }, (_, index) => (
        <MasonryItem key={index} ratio={index % 3 === 0 ? 1.8 : index % 3 === 1 ? 0.75 : 1.2}>
          <div className="flex h-full flex-col overflow-hidden rounded-none border border-border bg-card">
            <Skeleton className="min-h-0 flex-1 rounded-none bg-muted" />
            <div className="flex shrink-0 flex-col justify-center gap-2 border-t border-border p-2.5">
              <Skeleton className="h-4 w-4/5 rounded-none" />
              <Skeleton className="h-3 w-2/5 rounded-none" />
            </div>
          </div>
        </MasonryItem>
      ))}
    </ul>
  )
}

function EmptyLibrary() {
  return (
    <div className="flex flex-col items-start gap-3 border-t border-border py-16">
      <CompassIcon className="size-6 text-muted-foreground" aria-hidden="true" />
      <p className="font-serif text-xl text-foreground">Nothing saved yet</p>
      <p className="max-w-prose text-sm text-muted-foreground">
        Drop a screenshot above, paste one straight from the clipboard, or pick files. Each one is
        stored on your own machine and given a title, a description and tags.
      </p>
    </div>
  )
}

function NoMatches({ filters, onClear }: { filters: Filters; onClear: () => void }) {
  return (
    <div className="flex flex-col items-start gap-3 border-t border-border py-16">
      <SearchXIcon className="size-6 text-muted-foreground" aria-hidden="true" />
      <p className="font-serif text-xl text-foreground">No screenshots match</p>
      <p className="max-w-prose text-sm text-muted-foreground">
        {filters.q ? (
          <>
            Nothing matches <span className="text-foreground">{filters.q}</span>. Terms are matched
            together, so all of them have to appear.
          </>
        ) : (
          'No screenshots match these filters.'
        )}
      </p>
      <Button variant="outline" onClick={onClear} className="mt-1">
        Clear search and filters
      </Button>
    </div>
  )
}