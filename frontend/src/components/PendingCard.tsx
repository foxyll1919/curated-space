import { useEffect, useRef } from 'react'
import { RefreshCwIcon } from 'lucide-react'
import type { Item } from '@/lib/api'
import { MASONRY_CAPTION_PX } from '@/components/MasonryItem'
import { StatusChip } from '@/components/StatusChip'
import { Button } from '@/components/ui/button'
import { useItemStatusPoll } from '@/hooks/useItems'
import { cn } from 'cn'

type PendingCardProps = {
  item: Item
  /** Called once the poll settles, so the owner can swap in the real item. */
  onResolved: (item: Item) => void
  onGaveUp: (id: string) => void
}

/**
 * The card shown for a screenshot the moment the backend accepts it. It keeps
 * its own gentle poll so the card turns over to its real state without waiting
 * for the grid to refetch.
 */
export function PendingCard({ item, onResolved, onGaveUp }: PendingCardProps) {
  const { item: polled, gaveUp, settled, refresh } = useItemStatusPoll(item.id)
  const notified = useRef(false)

  useEffect(() => {
    if (!settled || notified.current) return
    notified.current = true
    if (polled) onResolved(polled)
    else if (gaveUp) onGaveUp(item.id)
  }, [settled, polled, gaveUp, item.id, onResolved, onGaveUp])

  return (
    <div className="flex h-full flex-col overflow-hidden rounded-none border border-border bg-card">
      {gaveUp ? (
        <div className="flex min-h-0 flex-1 items-center justify-center p-4">
          <div className="flex flex-col items-center gap-3 text-center">
            <p className="text-sm font-medium text-foreground">Still processing</p>
            <p className="text-sm text-muted-foreground">
              This one is taking longer than a minute. It is saved either way.
            </p>
            <Button variant="outline" onClick={refresh}>
              <RefreshCwIcon data-icon="inline-start" />
              Check again
            </Button>
          </div>
        </div>
      ) : (
        <div className="cs-shimmer min-h-0 flex-1 bg-muted" role="status">
          <span className="sr-only">Saving this screenshot.</span>
        </div>
      )}
      <CardFooter status={item.status} />
    </div>
  )
}

function CardFooter({ status }: { status: Item['status'] }) {
  return (
    <div
      className="flex shrink-0 flex-col justify-between gap-1.5 border-t border-border px-2.5 py-2"
      style={{ height: MASONRY_CAPTION_PX }}
    >
      <p className="line-clamp-2 font-serif text-[15px] leading-snug text-muted-foreground">
        Reading the screenshot
      </p>
      <div className="flex flex-wrap items-center gap-1.5">
        <StatusChip status={status} />
      </div>
    </div>
  )
}

/**
 * Loads the next cursor page when a sentinel near the end scrolls into view.
 * The observer is disconnected once the backend stops offering a cursor.
 */
export function InfiniteScrollSentinel({
  hasMore,
  onLoadMore,
  busy,
}: {
  hasMore: boolean
  onLoadMore: () => void
  busy: boolean
}) {
  const ref = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const node = ref.current
    if (!node || !hasMore) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) onLoadMore()
      },
      { rootMargin: '600px 0px' },
    )
    observer.observe(node)
    return () => observer.disconnect()
  }, [hasMore, onLoadMore])

  if (!hasMore) return null

  return (
    <div ref={ref} className={cn('col-span-full flex justify-center py-8')}>
      {busy ? <p className="text-sm text-muted-foreground">Loading more</p> : null}
    </div>
  )
}