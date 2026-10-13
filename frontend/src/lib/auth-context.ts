/**
 * The auth context object and its hook, kept apart from the provider component
 * so this module exports no components and React Fast Refresh stays honest.
 */
import { createContext, useContext } from 'react'
import type { Account, AuthStatus } from '@/lib/auth'

export const accountKey = ['auth', 'account'] as const
export const authStatusKey = ['auth', 'status'] as const

export type AuthContextValue = {
  account: Account | null
  /** True while the first "who am I" request is still in flight. */
  isLoading: boolean
  /** Unauthenticated. Decides whether to render the shell or the sign-in page. */
  isSignedIn: boolean
  status: AuthStatus | undefined
  /** Live while a sign-in, account-creation or sign-out request is running. */
  isSubmitting: boolean
  signIn: (email: string, password: string) => Promise<Account>
  createAccount: (email: string, password: string) => Promise<Account>
  signOut: () => Promise<void>
  signOutEverywhere: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext)
  if (context === null) {
    throw new Error('useAuth must be used inside <AuthProvider>')
  }
  return context
}