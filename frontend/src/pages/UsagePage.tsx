import { useQuery } from '@tanstack/react-query'
import { AlertCircleIcon, RefreshCwIcon } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { api, type UsageWindow } from '@/lib/api'

export function UsagePage() {
  const { data, isPending, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['usage'],
    queryFn: api.usage,
    retry: 1,
  })

  if (isError && error) {
    return (
      <div className="mx-auto w-full max-w-3xl px-4 py-8 sm:px-6">
        <Alert variant="destructive">
          <AlertCircleIcon />
          <AlertTitle>Usage could not be read</AlertTitle>
          <AlertDescription className="flex flex-col items-start gap-3">
            <span>{error.message}</span>
            <Button variant="outline" size="sm" onClick={() => void refetch()}>
              <RefreshCwIcon data-icon="inline-start" />
              Try again
            </Button>
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-8 px-4 py-8 sm:px-6">
      <header className="flex flex-col gap-2">
        <h1 className="font-serif text-2xl">Usage</h1>
        <p className="max-w-prose text-sm text-muted-foreground">
          What this library has cost in analysis time so far. Costs are estimates computed from
          published token prices, not a bill.
        </p>
      </header>

      {isPending ? (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 8 }, (_, index) => (
            <Skeleton key={index} className="h-9 rounded-none" />
          ))}
        </div>
      ) : data ? (
        <div className="flex flex-col gap-8">
          <Window title="Today" window={data.today} />
          <Separator decorative />
          <Window title="Last 7 days" window={data.last_7_days} />
          <p className="text-xs text-muted-foreground" aria-live="polite">
            {isFetching ? 'Refreshing.' : ''}
          </p>
        </div>
      ) : null}
    </div>
  )
}

function Window({ title, window: usage }: { title: string; window: UsageWindow }) {
  const unknown = usage.unknown_cost_models ?? []
  const hitRate = Math.round(usage.cache_hit_rate * 100)

  return (
    <section className="flex flex-col gap-3">
      <h2 className="font-mono text-[11px] tracking-wide text-muted-foreground uppercase">
        {title}
      </h2>
      <dl className="flex flex-col">
        <Row label="Analysis runs" value={formatInt(usage.calls)} />
        <Row label="Sent to the provider" value={formatInt(usage.provider_calls)} />
        <Row label="Answered from cache" value={formatInt(usage.cache_hits)} />
        <Row label="Cache hit rate" value={`${hitRate}%`} />
        <Row label="Failed" value={formatInt(usage.failed_calls)} />
        <Row label="Prompt tokens" value={formatInt(usage.prompt_tokens)} />
        <Row label="Output tokens" value={formatInt(usage.output_tokens)} />
        <Row label="Thinking tokens" value={formatInt(usage.thinking_tokens)} />
        <Row label="Estimated cost" value={`$${usage.est_cost_usd.toFixed(4)}`} emphasis />
      </dl>
      {unknown.length > 0 ? (
        <p className="text-xs text-status-deferred">
          No published price for {unknown.join(', ')}, so the estimate leaves those calls out.
        </p>
      ) : null}
    </section>
  )
}

function Row({
  label,
  value,
  emphasis,
}: {
  label: string
  value: string
  emphasis?: boolean
}) {
  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-border py-2 last:border-b-0">
      <dt className="text-sm text-muted-foreground">{label}</dt>
      <dd className={emphasis ? 'font-mono text-base text-foreground' : 'font-mono text-sm text-foreground'}>
        {value}
      </dd>
    </div>
  )
}

function formatInt(value: number): string {
  return value.toLocaleString()
}