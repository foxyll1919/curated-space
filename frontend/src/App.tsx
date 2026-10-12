import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Outlet, RouterProvider, createBrowserRouter } from 'react-router-dom'
import { Toaster } from '@/components/ui/sonner'
import { TooltipProvider } from '@/components/ui/tooltip'
import { AppShell } from '@/components/AppShell'
import { LibraryPage } from '@/pages/LibraryPage'
import { ItemPage } from '@/pages/ItemPage'
import { UsagePage } from '@/pages/UsagePage'
import { NotFoundPage } from '@/pages/NotFoundPage'
import { isApiError } from '@/lib/api'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 15_000,
      retry: (failureCount, error) => {
        // A 404 or a refused key will not fix itself, so it is not retried.
        if (isApiError(error) && (error.isNotFound || error.isUnauthorized)) return false
        return failureCount < 2
      },
    },
  },
})

const router = createBrowserRouter([
  {
    path: '/',
    element: (
      <AppShell>
        <Outlet />
      </AppShell>
    ),
    children: [
      { index: true, element: <LibraryPage /> },
      { path: 'usage', element: <UsagePage /> },
      { path: 'item/:id', element: <ItemPage /> },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
])

export function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <RouterProvider router={router} />
        <Toaster position="bottom-right" />
      </TooltipProvider>
    </QueryClientProvider>
  )
}