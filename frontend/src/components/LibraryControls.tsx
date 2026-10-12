import { useEffect, useState } from 'react'
import { CheckIcon, ChevronDownIcon, SearchIcon, XIcon } from 'lucide-react'
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Button } from '@/components/ui/button'
import { FILTERABLE_STATUSES, type ItemStatus } from '@/lib/api'
import { useDebounce } from '@/hooks/useDebounce'
import { cn } from 'cn'

export type Filters = {
  q: string
  status?: ItemStatus
  label?: string
}

type LibraryControlsProps = {
  filters: Filters
  onChange: (next: Filters) => void
  labels: string[]
  resultCount: number | null
}

/**
 * Search is bound to `q` and mirrored into the URL, so a search can be shared,
 * bookmarked or survived by a reload. Typing is debounced before it reaches
 * the query key; the input itself stays responsive.
 */
export function LibraryControls({ filters, onChange, labels, resultCount }: LibraryControlsProps) {
  const [draft, setDraft] = useState(filters.q)
  const debounced = useDebounce(draft, 300)

  // Keep the box in step when the URL changes from outside, such as the back
  // button or a shared link.
  useEffect(() => {
    setDraft((current) => (current === filters.q ? current : filters.q))
  }, [filters.q])

  useEffect(() => {
    if (debounced !== filters.q) onChange({ ...filters, q: debounced })
    // onChange is intentionally excluded: this effect reacts to the debounce
    // settling, not to a new callback identity.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [debounced])

  const activeFilters = [filters.status, filters.label].filter(Boolean).length

  return (
    <div className="flex flex-col gap-3 lg:flex-row lg:items-center">
      <div className="relative flex-1">
        <SearchIcon
          aria-hidden="true"
          className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
        />
        <input
          type="search"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder="Search titles, descriptions and tags"
          aria-label="Search the library"
          className={cn(
            'h-9 w-full rounded-none border border-input bg-card pr-8 pl-8 text-sm',
            'placeholder:text-muted-foreground',
            'focus-visible:border-ring focus-visible:ring-2 focus-visible:ring-ring/40 focus-visible:outline-none',
          )}
        />
        {draft ? (
          <button
            type="button"
            onClick={() => setDraft('')}
            aria-label="Clear search"
            className="absolute top-1/2 right-1.5 flex size-6 -translate-y-1/2 items-center justify-center text-muted-foreground hover:text-foreground"
          >
            <XIcon className="size-3.5" />
          </button>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <StatusFilter
          value={filters.status}
          onChange={(status) => onChange({ ...filters, status })}
        />
        <LabelFilter
          value={filters.label}
          labels={labels}
          onChange={(label) => onChange({ ...filters, label })}
        />
        {activeFilters > 0 ? (
          <Button variant="ghost" onClick={() => onChange({ q: filters.q })}>
            Clear filters
          </Button>
        ) : null}
      </div>

      <p aria-live="polite" className="sr-only">
        {resultCount === null
          ? 'Loading results'
          : `${resultCount} ${resultCount === 1 ? 'screenshot' : 'screenshots'}`}
      </p>
    </div>
  )
}

function StatusFilter({
  value,
  onChange,
}: {
  value: ItemStatus | undefined
  onChange: (status: ItemStatus | undefined) => void
}) {
  const active = value ? FILTERABLE_STATUSES.find((entry) => entry.value === value) : undefined
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" className={cn('rounded-none', active && 'border-ring')}>
          {active ? active.label : 'Any status'}
          <ChevronDownIcon data-icon="inline-end" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-56 p-0">
        <Command>
          <CommandList>
            <CommandGroup>
              <CommandItem
                onSelect={() => onChange(undefined)}
                className="rounded-none"
              >
                <CheckIcon
                  className={cn(!value && 'opacity-100', value && 'opacity-0')}
                  aria-hidden="true"
                />
                Any status
              </CommandItem>
              {FILTERABLE_STATUSES.map((entry) => (
                <CommandItem
                  key={entry.value}
                  value={entry.value}
                  onSelect={() => onChange(entry.value)}
                  className="rounded-none"
                >
                  <CheckIcon
                    className={cn(value === entry.value && 'opacity-100', value !== entry.value && 'opacity-0')}
                    aria-hidden="true"
                  />
                  {entry.label}
                </CommandItem>
              ))}
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}

/**
 * Labels come from whatever the API returned for this library. No taxonomy is
 * hardcoded, because the current one is a placeholder and a new one is planned.
 */
function LabelFilter({
  value,
  labels,
  onChange,
}: {
  value: string | undefined
  labels: string[]
  onChange: (label: string | undefined) => void
}) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" className={cn('rounded-none', value && 'border-ring')}>
          {value ? value : 'Any label'}
          <ChevronDownIcon data-icon="inline-end" />
        </Button>
      </PopoverTrigger>
      <PopoverContent align="start" className="w-64 p-0">
        <Command>
          <CommandInput placeholder="Find a label" className="rounded-none" />
          <CommandList>
            <CommandGroup>
              <CommandItem onSelect={() => onChange(undefined)} className="rounded-none">
                <CheckIcon className={cn(!value && 'opacity-100', value && 'opacity-0')} />
                Any label
              </CommandItem>
              {labels.map((label) => (
                <CommandItem
                  key={label}
                  value={label}
                  onSelect={() => onChange(label)}
                  className="rounded-none"
                >
                  <CheckIcon className={cn(value === label && 'opacity-100', value !== label && 'opacity-0')} />
                  {label}
                </CommandItem>
              ))}
            </CommandGroup>
            <CommandEmpty>No labels in this library yet.</CommandEmpty>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  )
}