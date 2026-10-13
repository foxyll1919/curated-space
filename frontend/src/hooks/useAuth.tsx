/**
 * Session state for the whole app.
 *
 * There is no token in JavaScript to keep in sync: the provider asks the backend
 * who the session cookie belongs to, and every mutation replaces that answer.
 * A 401 anywhere else in the app means the cookie expired or was revoked, so the
 * API layer announces it on a window event and this provider drops to signed
 * out, which sends the reader back to the sign-in page.
 */
import { useCallback, useEffect, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { auth, fetchAccount, type Account } from '@/lib/auth'
import { AuthContext, accountKey, authStatusKey } from '@/lib/auth-context'
import { UNAUTHORIZED_EVENT } from '@/lib/api'

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  const accountQuery = useQuery({
    queryKey: accountKey,
    queryFn: fetchAccount,
    // A 401 resolves to null rather than throwing, so this never needs a retry
    // and is only refetched when something invalidates it on purpose.
    staleTime: Infinity,
    retry: false,
  })

  const statusQuery = useQuery({
    queryKey: authStatusKey,
    queryFn: auth.status,
    staleTime: 60_000,
    retry: false,
  })

  /**
   * Everything except the account itself is dropped when the session changes.
   * Otherwise signing in as someone else would render the previous account's
   * screenshots from cache for a frame.
   */
  const endSession = useCallback(() => {
    queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'auth' })
    queryClient.setQueryData(accountKey, null)
    void queryClient.invalidateQueries({ queryKey: authStatusKey })
  }, [queryClient])

  const adoptSession = useCallback(
    (account: Account) => {
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'auth' })
      queryClient.setQueryData(accountKey, account)
      void queryClient.invalidateQueries({ queryKey: authStatusKey })
    },
    [queryClient],
  )

  // Any request that comes back 401 means this session is no longer valid, so the
  // app returns to the sign-in page instead of rendering empty grids.
  useEffect(() => {
    window.addEventListener(UNAUTHORIZED_EVENT, endSession)
    return () => window.removeEventListener(UNAUTHORIZED_EVENT, endSession)
  }, [endSession])

  const signInMutation = useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const session = await auth.signIn(email, password)
      adoptSession(session.user)
      return session.user
    },
  })

  const createAccountMutation = useMutation({
    mutationFn: async ({ email, password }: { email: string; password: string }) => {
      const session = await auth.createAccount(email, password)
      adoptSession(session.user)
      return session.user
    },
  })

  const signOutMutation = useMutation({
    mutationFn: async () => {
      await auth.signOut()
      endSession()
    },
  })

  const signOutEverywhereMutation = useMutation({
    mutationFn: async () => {
      await auth.signOutEverywhere()
      endSession()
    },
  })

  const account = accountQuery.data ?? null

  return (
    <AuthContext.Provider
      value={{
        account,
        isLoading: accountQuery.isLoading,
        isSignedIn: account !== null,
        status: statusQuery.data,
        isSubmitting:
          signInMutation.isPending ||
          createAccountMutation.isPending ||
          signOutMutation.isPending,
        signIn: (email, password) => signInMutation.mutateAsync({ email, password }),
        createAccount: (email, password) => createAccountMutation.mutateAsync({ email, password }),
        signOut: () => signOutMutation.mutateAsync(),
        signOutEverywhere: () => signOutEverywhereMutation.mutateAsync(),
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}