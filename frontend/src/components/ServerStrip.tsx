import { useQuery } from '@tanstack/react-query'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
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
 * `/ready` is public, so this strip still works when the API key is wrong. It
 * is the one place the app says the backend, rather than the library, is what
 * is missing.
 */
export function ServerStrip() {
  const { data, isError } = useQuery({
    queryKey: ['ready'],
    queryFn: api.ready,
    refetchInterval: POLL_MS,
    retry: 1,
  })

  const verdict = verdictOf(data, isError)
  const components = Object.entries(data?.components ?? {})

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button
          type="button"
          className="flex h-8 items-center gap-2 rounded-none px-2 font-mono text-[11px] text-muted-foreground transition-colors hover:text-foreground"
          aria-label={`${VERDICT_TEXT[verdict]}. Open the readiness report.`}
        >
          <span aria-hidden="true" className={cn('size-1.5 rounded-full', VERDICT_DOT[verdict])} />
          {VERDICT_TEXT[verdict]}
        </button>
      </PopoverTrigger>
      <PopoverContent align="end" className="w-72">
        <p className="font-mono text-[11px] tracking-wide text-muted-foreground uppercase">
          Readiness
        </p>
        {components.length > 0 ? (
          <dl className="mt-3 flex flex-col gap-1.5">
            {components.map(([name, state]) => (
              <div key={name} className="flex items-baseline justify-between gap-4 text-sm">
                <dt className="text-muted-foreground">{name.replace(/_/g, ' ')}</dt>
                <dd
                  className={cn(
                    'font-mono text-xs',
                    state === 'ok' ? 'text-foreground' : 'text-status-failed',
                  )}
                >
                  {state}
                </dd>
              </div>
            ))}
          </dl>
        ) : (
          <p className="mt-2 text-sm text-muted-foreground">
            The backend did not answer. Start it on port 8000 and this fills in.
          </p>
        )}
      </PopoverContent>
    </Popover>
  )
}
