import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { AlertCircleIcon, LogOutIcon, RefreshCwIcon } from 'lucide-react'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { api, type UsageWindow } from '@/lib/api'
import { useAuth } from '@/lib/auth-context'

/**
 * Everything about the reader that is not the library itself: who is signed in,
 * how to leave, and what the analysis has cost so far.
 *
 * Usage used to live in its own top-level page, which made a single table look
 * like a top-level destination. It is a property of the account, so it belongs
 * here. The route is deep-linkable, so old `/usage` links still land somewhere
 * sensible.
 */
export function SettingsPage() {
  const { account, isSubmitting, signOut, signOutEverywhere } = useAuth()
  const [pendingEverywhere, setPendingEverywhere] = useState(false)

  const { data, isPending, isError, error, refetch, isFetching } = useQuery({
    queryKey: ['usage'],
    queryFn: api.usage,
    retry: 1,
  })

  return (
    <div className="mx-auto flex w-full max-w-3xl flex-col gap-10 px-4 py-8 sm:px-6 sm:py-10">
      <header className="flex flex-col gap-2">
        <h1 className="font-serif text-2xl text-balance sm:text-3xl">Settings</h1>
        <p className="max-w-prose text-sm text-muted-foreground">
          The account this library belongs to, and what its analysis has cost so far.
        </p>
      </header>

      <Separator decorative />

      <section aria-labelledby="settings-account" className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <h2
            id="settings-account"
            className="font-mono text-[11px] tracking-wide text-muted-foreground uppercase"
          >
            Account
          </h2>
          <p className="max-w-prose text-sm text-muted-foreground">
            This app has no passwords to reset and no profile to edit. Signing out is the whole of
            it.
          </p>
        </div>

        <dl className="flex flex-col border-t border-border">
          <Row label="Email" value={account?.email ?? '—'} />
          <Row label="Member since" value={account ? formatDate(account.created_at) : '—'} />
        </dl>

        {/* Kept apart from the read-only facts: leaving is not a preference. */}
        <div className="flex flex-col items-start gap-3 border-t border-border pt-4">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant="outline"
              disabled={isSubmitting || pendingEverywhere}
              onClick={() => {
                void signOut()
              }}
            >
              <LogOutIcon data-icon="inline-start" aria-hidden="true" />
              Sign out
            </Button>
            <Button
              variant="outline"
              disabled={isSubmitting || pendingEverywhere}
              onClick={() => {
                setPendingEverywhere(true)
                void signOutEverywhere().finally(() => setPendingEverywhere(false))
              }}
            >
              Sign out everywhere
            </Button>
          </div>
          <p className="max-w-prose text-xs text-muted-foreground">
            The session is a cookie with a month of life. On a shared machine, signing out of this
            browser is not enough — sign out everywhere revokes every session for the account.
          </p>
        </div>
      </section>

      <Separator decorative />

      <section aria-labelledby="settings-usage" className="flex flex-col gap-4">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex flex-col gap-1.5">
            <h2
              id="settings-usage"
              className="font-mono text-[11px] tracking-wide text-muted-foreground uppercase"
            >
              Usage
            </h2>
            <p className="max-w-prose text-sm text-muted-foreground">
              What this library has cost in analysis time. Costs are estimates computed from
              published token prices, not a bill.
            </p>
          </div>
          <Button
            variant="ghost"
            size="sm"
            disabled={isFetching}
            onClick={() => void refetch()}
            className="shrink-0"
          >
            <RefreshCwIcon data-icon="inline-start" aria-hidden="true" />
            Refresh
          </Button>
        </div>

        <p className="sr-only" role="status" aria-live="polite">
          {isFetching ? 'Refreshing usage' : ''}
        </p>

        {isError && error ? (
          <Alert variant="destructive">
            <AlertCircleIcon aria-hidden="true" />
            <AlertTitle>Usage could not be read</AlertTitle>
            <AlertDescription className="flex flex-col items-start gap-3">
              <span>{error.message}</span>
              <Button variant="outline" size="sm" onClick={() => void refetch()}>
                <RefreshCwIcon data-icon="inline-start" aria-hidden="true" />
                Try again
              </Button>
            </AlertDescription>
          </Alert>
        ) : null}

        {isPending ? (
          <div className="flex flex-col gap-4" aria-hidden="true">
            {[0, 1].map((index) => (
              <div key={index} className="flex flex-col gap-2">
                <Skeleton className="h-3 w-24 rounded-none" />
                <Skeleton className="h-24 rounded-none" />
              </div>
            ))}
          </div>
        ) : data ? (
          <div className="flex flex-col gap-8">
            <Window title="Today" window={data.today} />
            <Window title="Last 7 days" window={data.last_7_days} />
          </div>
        ) : null}
      </section>
    </div>
  )
}

function Window({ title, window: usage }: { title: string; window: UsageWindow }) {
  const unknown = usage.unknown_cost_models ?? []
  const hitRate = Math.round(usage.cache_hit_rate * 100)

  return (
    <section aria-label={title} className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-4">
        <h3 className="font-mono text-[11px] tracking-wide text-muted-foreground uppercase">
          {title}
        </h3>
        {/* The one number people come here for, so it leads. */}
        <p className="font-mono text-base tabular-nums text-foreground">
          {formatCost(usage.est_cost_usd)}
        </p>
      </div>

      <dl className="flex flex-col border-t border-border">
        <Row label="Analysis runs" value={formatInt(usage.calls)} />
        <Row label="Sent to the provider" value={formatInt(usage.provider_calls)} />
        <Row label="Answered from cache" value={formatInt(usage.cache_hits)} />
        <Row label="Cache hit rate" value={`${hitRate}%`} meter={hitRate} />
        <Row label="Failed" value={formatInt(usage.failed_calls)} />
        <Row label="Prompt tokens" value={formatInt(usage.prompt_tokens)} />
        <Row label="Output tokens" value={formatInt(usage.output_tokens)} />
        <Row label="Thinking tokens" value={formatInt(usage.thinking_tokens)} />
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
  meter,
}: {
  label: string
  value: string
  /** 0-100, drawn as a hairline bar so the ratio is readable without colour. */
  meter?: number
}) {
  return (
    <div className="flex items-baseline justify-between gap-6 border-b border-border py-2 last:border-b-0">
      <dt className="min-w-0 text-sm break-words text-muted-foreground">{label}</dt>
      <dd className="flex min-w-0 items-center gap-3">
        {meter === undefined ? null : (
          <span aria-hidden="true" className="hidden h-px w-16 bg-border sm:block">
            <span className="block h-px bg-foreground" style={{ width: `${meter}%` }} />
          </span>
        )}
        <span className="font-mono text-sm break-words tabular-nums text-foreground">{value}</span>
      </dd>
    </div>
  )
}

const COST = new Intl.NumberFormat(undefined, {
  style: 'currency',
  currency: 'USD',
  minimumFractionDigits: 4,
  maximumFractionDigits: 4,
})

function formatInt(value: number): string {
  return value.toLocaleString()
}

/** A cost is not a bill, so the fraction is fixed rather than rounded away. */
function formatCost(value: number): string {
  return COST.format(value)
}

/** Date only: a member-since line does not need a clock. */
function formatDate(value: string): string {
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return date.toLocaleDateString(undefined, { dateStyle: 'medium' })
}