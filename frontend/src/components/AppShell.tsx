import { NavLink, useLocation } from 'react-router-dom'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/ThemeToggle'
import { ServerStrip } from '@/components/ServerStrip'
import { AccountMenu } from '@/components/AccountMenu'
import { cn } from 'cn'

const NAV = [
  { to: '/', label: 'Library', end: true },
  { to: '/usage', label: 'Usage', end: false },
]

export function AppShell({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation()

  return (
    <div className="flex min-h-dvh flex-col">
      <header className="sticky top-0 z-20 border-b border-border bg-background/85 backdrop-blur-sm">
        <div className="mx-auto flex h-14 w-full max-w-[1600px] items-center gap-4 px-4 sm:px-6 lg:px-8">
          <NavLink
            to="/"
            className="flex shrink-0 items-center gap-2.5 font-serif text-[17px] leading-none text-foreground"
          >
            <span
              aria-hidden="true"
              className="block size-4 border border-foreground bg-[linear-gradient(135deg,transparent_45%,currentColor_45%,currentColor_55%,transparent_55%)]"
            />
            Curated Space
          </NavLink>

          <nav aria-label="Main" className="flex items-center gap-1">
            {NAV.map((entry) => {
              const active = entry.end
                ? pathname === entry.to
                : pathname.startsWith(entry.to)
              return (
                <NavLink
                  key={entry.to}
                  to={entry.to}
                  aria-current={active ? 'page' : undefined}
                  className={cn(
                    'rounded-none px-2 py-1 text-sm transition-colors',
                    active
                      ? 'text-foreground underline decoration-ring decoration-2 underline-offset-[6px]'
                      : 'text-muted-foreground hover:text-foreground',
                  )}
                >
                  {entry.label}
                </NavLink>
              )
            })}
          </nav>

          <div className="ml-auto flex items-center gap-1">
            <ServerStrip />
            <ThemeToggle />
            <AccountMenu />
          </div>
        </div>
      </header>

      <Separator decorative />

      <main className="flex-1">{children}</main>
    </div>
  )
}
