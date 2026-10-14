import { Navigate, Outlet, RouterProvider, createBrowserRouter, useLocation } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AppShell } from '@/components/AppShell'
import { LibraryPage } from '@/pages/LibraryPage'
import { ItemPage } from '@/pages/ItemPage'
import { LoginPage } from '@/pages/LoginPage'
import { SettingsPage } from '@/pages/SettingsPage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { AuthProvider } from '@/hooks/useAuth'
import { useAuth } from '@/lib/auth-context'
import { isApiError } from '@/lib/api'

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
 * Gate for the signed-in part of the app.
 *
 * While the "who am I" request is in flight nothing is rendered, so the library
 * never flashes before the cookie turns out to be expired. The attempted path
 * travels along in router state and the sign-in page returns to it afterwards.
 */
function RequireAccount() {
  const { isLoading, account } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return (
      <div className="flex min-h-dvh items-center justify-center">
        <span className="text-sm text-muted-foreground">Checking your session…</span>
      </div>
    )
  }

  if (account === null) {
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
  const { isLoading, account } = useAuth()
  if (!isLoading && account) return <Navigate to="/" replace />
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
      <AuthProvider>
        <TooltipProvider>
          <RouterProvider router={router} />
          <Toaster position="bottom-right" />
        </TooltipProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}