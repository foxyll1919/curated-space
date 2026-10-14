import { useState } from 'react'
import { Link } from 'react-router-dom'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { Button } from '@/components/ui/button'
import { useAuth } from '@/lib/auth-context'

/**
 * The signed-in account, and the way out of it.
 *
 * Settings lives here rather than in the top bar: it is the account's own
 * business, not a top-level destination, so it stays out of the way until
 * asked for.
 *
 * "Sign out everywhere" exists because the session is a cookie with a month of
 * life: on a shared machine, signing out of this browser is not enough.
 */
export function AccountMenu() {
  const { account, isSubmitting, signOut, signOutEverywhere } = useAuth()
  const [pendingEverywhere, setPendingEverywhere] = useState(false)

  if (account === null) return null

  const initial = account.email.slice(0, 1).toUpperCase()

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="ghost" size="icon" aria-label="Account" className="font-mono text-xs">
          {initial}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-60">
        <DropdownMenuLabel className="font-normal">
          <span className="block text-sm">Signed in</span>
          <span className="block truncate text-xs text-muted-foreground">{account.email}</span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link to="/settings">Settings</Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          disabled={isSubmitting}
          onSelect={() => {
            void signOut()
          }}
        >
          Sign out
        </DropdownMenuItem>
        <DropdownMenuItem
          disabled={pendingEverywhere}
          onSelect={() => {
            setPendingEverywhere(true)
            void signOutEverywhere().finally(() => setPendingEverywhere(false))
          }}
        >
          Sign out everywhere
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}