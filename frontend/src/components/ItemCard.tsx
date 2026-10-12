import { memo } from 'react'
import { Link } from 'react-router-dom'
import { api, labelEntries, type Item } from '@/lib/api'
import { MASONRY_CAPTION_PX } from '@/components/MasonryItem'
import { StatusChip } from '@/components/StatusChip'
import { cn } from 'cn'

function ItemCardInner({ item }: { item: Item }) {
  const inFlight = item.status === 'pending' || item.status === 'processing'
  const labels = labelEntries(item)
  const title = item.title ?? 'Untitled screenshot'

  return (
    <Link
      to={`/item/${item.id}`}
      aria-label={inFlight ? `${title}, still being analyzed` : title}
      className={cn(
        'group flex h-full flex-col overflow-hidden rounded-none border border-border bg-card',
        'transition-[border-color,box-shadow] duration-150',
        'hover:border-foreground/25 hover:shadow-[0_2px_16px_-8px_rgb(0_0_0/0.35)]',
        'focus-visible:border-ring',
      )}
    >
      <div className="min-h-0 flex-1 overflow-hidden bg-muted">
        {inFlight ? (
          <div className="cs-shimmer size-full" role="status">
            <span className="sr-only">This screenshot is still being analyzed.</span>
          </div>
        ) : (
          <img
            src={api.imageUrl(item.id)}
            alt={title}
            loading="lazy"
            decoding="async"
            className="size-full object-contain"
          />
        )}
      </div>

      <div
        className="flex shrink-0 flex-col justify-between gap-1.5 border-t border-border px-2.5 py-2"
        style={{ height: MASONRY_CAPTION_PX }}
      >
        <p className="line-clamp-2 font-serif text-[15px] leading-snug text-foreground">
          {inFlight ? 'Reading the screenshot' : title}
        </p>
        <div className="flex flex-wrap items-center gap-1.5">
          <StatusChip status={item.status} />
          {labels.map(([name, value]) => (
            <span
              key={name}
              title={`${name}: ${value}`}
              className="rounded-none border border-border px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground"
            >
              {value}
            </span>
          ))}
          {item.tags.slice(0, 2).map((tag) => (
            <span key={tag} className="truncate text-[11px] text-muted-foreground">
              {tag}
            </span>
          ))}
          {item.tags.length > 2 ? (
            <span className="text-[11px] text-muted-foreground/70">+{item.tags.length - 2}</span>
          ) : null}
        </div>
      </div>
    </Link>
  )
}

export const ItemCard = memo(ItemCardInner)