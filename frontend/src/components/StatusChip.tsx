import { cn } from 'cn'
import { Badge } from '@/components/ui/badge'
import type { ItemStatus } from '@/lib/api'

/**
 * Every state gets a designed chip, and each one carries a word, so colour is
 * never the only signal. `classifier_score` is deliberately absent from this
 * component: it is a classifier margin, not a probability, and is never shown
 * as a percentage or a confidence.
 */
const STATUS_CHIP: Record<
  ItemStatus,
  { label: string; className: string; dot: string; pulse: boolean }
> = {
  pending: {
    label: 'Pending',
    className: 'text-status-pending border-status-pending/30 bg-status-pending/8',
    dot: 'bg-status-pending',
    pulse: true,
  },
  processing: {
    label: 'Processing',
    className: 'text-status-pending border-status-pending/30 bg-status-pending/8',
    dot: 'bg-status-pending',
    pulse: true,
  },
  ready: {
    label: 'Analyzed',
    className: 'text-muted-foreground border-border bg-transparent',
    dot: 'bg-foreground',
    pulse: false,
  },
  deferred: {
    label: 'Saved, not analyzed',
    className: 'text-status-deferred border-status-deferred/35 bg-status-deferred/8',
    dot: 'bg-status-deferred',
    pulse: false,
  },
  failed: {
    label: 'Failed',
    className: 'text-status-failed border-status-failed/35 bg-status-failed/8',
    dot: 'bg-status-failed',
    pulse: false,
  },
}

export function StatusChip({
  status,
  className,
}: {
  status: ItemStatus
  className?: string
}) {
  const chip = STATUS_CHIP[status]
  return (
    <Badge
      variant="outline"
      className={cn(
        'h-5 gap-1.5 rounded-none px-1.5 font-mono text-[10px] font-normal tracking-wide',
        chip.className,
        className,
      )}
    >
      <span
        aria-hidden="true"
        className={cn('size-1.5 rounded-full', chip.dot, chip.pulse && 'animate-pulse')}
      />
      {chip.label}
    </Badge>
  )
}

