import { useQuery } from '@tanstack/react-query'
import { api, type Ready } from '@/lib/api'
import { cn } from 'cn'

const POLL_MS = 30_000

type Verdict = 'ok' | 'degraded' | 'down'

function verdictOf(ready: Ready | undefined, failed: boolean): Verdict {
  if (failed || !ready) return 'down'
  return ready.status === 'ready' ? 'ok' : 'degraded'
}

const VERDICT_TEXT: Record<Verdict, string> = {
  ok: 'Server online',
  degraded: 'Server not ready',
  down: 'Server unreachable',
}

const VERDICT_DOT: Record<Verdict, string> = {
  ok: 'bg-foreground',
  degraded: 'bg-status-deferred',
  down: 'bg-status-failed',
}

/**
 * Server status indicator without interactive popover diagnostic window.
 */
export function ServerStrip() {
  const { data, isError } = useQuery({
    queryKey: ['ready'],
    queryFn: api.ready,
    refetchInterval: POLL_MS,
    retry: 1,
  })

  const verdict = verdictOf(data, isError)

  return (
    <div
      className="flex h-8 items-center gap-2 rounded-none px-2 font-mono text-[11px] text-muted-foreground"
      aria-label={VERDICT_TEXT[verdict]}
    >
      <span aria-hidden="true" className={cn('size-1.5 rounded-full', VERDICT_DOT[verdict])} />
      {VERDICT_TEXT[verdict]}
    </div>
  )
}
