import { useEffect } from 'react'
import { Navigate, Outlet, RouterProvider, createBrowserRouter, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useAuth as useClerkAuth } from '@clerk/react'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AppShell } from '@/components/AppShell'
import { LibraryPage } from '@/pages/LibraryPage'
import { ItemPage } from '@/pages/ItemPage'
import { LoginPage } from '@/pages/LoginPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { AskPage } from '@/pages/AskPage'
import { isApiError, setAuthTokenGetter } from '@/lib/api'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      retry: (failureCount, error) => {
        // A 404 or a refused session will not fix itself, so it is not retried.
        if (isApiError(error) && (error.isNotFound || error.isUnauthorized)) return false
        return failureCount < 2
      },
    },
  },
})

/**
 * Keeps the API layer in sync with the current Clerk session JWT
 * so every background request sends Authorization: Bearer <token>.
 */
function AuthSync() {
  const { getToken } = useClerkAuth()
  useEffect(() => {
    setAuthTokenGetter(getToken)
  }, [getToken])
  return null
}

/**
 * Gate for the signed-in part of the app.
 *
 * While Clerk's session is still loading, renders a minimal checking state.
 * Once loaded, redirects unauthenticated visitors to /login.
 */
function RequireAccount() {
  const { isLoaded, isSignedIn } = useClerkAuth()
  const location = useLocation()

  if (!isLoaded) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <span className="text-sm text-muted-foreground">Checking your session…</span>
      </div>
    )
  }

  if (!isSignedIn) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return (
    <AppShell>
      <Outlet />
    </AppShell>
  )
}

/** Keeps a signed-in reader away from the sign-in page. */
function RedirectIfSignedIn() {
  const { isLoaded, isSignedIn } = useClerkAuth()
  if (isLoaded && isSignedIn) return <Navigate to="/" replace />
  return <LoginPage />
}

const router = createBrowserRouter([
  {
    path: '/login',
    element: <RedirectIfSignedIn />,
  },
  {
    path: '/',
    element: <RequireAccount />,
    children: [
      { index: true, element: <LibraryPage /> },
      { path: 'ask', element: <AskPage /> },
      { path: 'settings', element: <SettingsPage /> },
      // Usage is now a section of settings, so old links land on the section
      // that replaced it instead of a dead end.
      { path: 'usage', element: <Navigate to="/settings" replace /> },
      { path: 'item/:id', element: <ItemPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthSync />
      <TooltipProvider>
        <RouterProvider router={router} />
        <Toaster position="bottom-right" />
      </TooltipProvider>
    </QueryClientProvider>
  )
}
