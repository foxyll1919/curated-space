import { useEffect, useRef } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import { Separator } from '@/components/ui/separator'
import { ThemeToggle } from '@/components/ThemeToggle'
import { ServerStrip } from '@/components/ServerStrip'
import { AccountMenu } from '@/components/AccountMenu'
import { cn } from 'cn'

/** Only one top-level destination: settings is reached through the account menu. */
const NAV = [{ to: '/', label: 'Library', end: true }]

export function AppShell({ children }: { children: React.ReactNode }) {
  const { pathname } = useLocation()
  const mainRef = useRef<HTMLElement>(null)
  const isFirstRender = useRef(true)

  /**
   * A page change is announced by moving focus into the new page, otherwise a
   * screen reader keeps reading the previous one and the back button still seems
   * pressed. Skipped on the first render so opening the app does not steal focus.
   */
  useEffect(() => {
    if (isFirstRender.current) {
      isFirstRender.current = false
      return
    }
    mainRef.current?.focus()
  }, [pathname])

  return (
    <div className="flex min-h-dvh flex-col">
      {/* The header sits above everything, so this is the only way past it. */}
      <a
        href="#main"
        className="sr-only rounded-none focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-30 focus:border focus:border-border focus:bg-background focus:px-3 focus:py-2 focus:text-sm focus:text-foreground"
      >
        Skip to content
      </a>

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
              const active = entry.end ? pathname === entry.to : pathname.startsWith(entry.to)
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

      {/* `scroll-mt` keeps a focused element clear of the sticky header. */}
      <main id="main" ref={mainRef} tabIndex={-1} className="flex-1 scroll-mt-14">
        {children}
      </main>
    </div>
  )
}