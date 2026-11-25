import { SignIn, SignUp, useUser } from '@clerk/react'
import { useState } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { ThemeToggle } from '@/components/ThemeToggle'

/**
 * Where to go after signing in: back to whatever protected page sent the
 * reader here, or the library. `/login` is never a valid destination.
 */
function returnPath(from: string | undefined): string {
  return from && from !== '/login' ? from : '/'
}

export function LoginPage() {
  const { isSignedIn, isLoaded } = useUser()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from
  const [mode, setMode] = useState<'sign-in' | 'sign-up'>('sign-in')

  // A signed-in reader has no business on this page.
  if (isLoaded && isSignedIn) {
    return <Navigate to={returnPath(from)} replace />
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <div className="flex items-center justify-end px-4 pt-4 sm:px-6">
        <ThemeToggle />
      </div>

      <main className="flex flex-1 items-center justify-center px-4 pb-16 sm:px-6">
        <div className="flex w-full max-w-sm flex-col gap-6">
          <div className="flex items-center gap-2.5 font-serif text-[17px] leading-none text-foreground">
            <span
              aria-hidden="true"
              className="block size-4 border border-foreground bg-[linear-gradient(135deg,transparent_45%,currentColor_45%,currentColor_55%,transparent_55%)]"
            />
            Curated Space
          </div>

          <div className="flex items-center justify-center">
            {mode === 'sign-in' ? (
              <SignIn
                routing="hash"
                fallbackRedirectUrl={returnPath(from)}
                signUpUrl="/login"
              />
            ) : (
              <SignUp
                routing="hash"
                fallbackRedirectUrl={returnPath(from)}
                signInUrl="/login"
              />
            )}
          </div>

          <p className="text-center text-sm text-muted-foreground">
            {mode === 'sign-in' ? (
              <>
                First time here?{' '}
                <button
                  type="button"
                  onClick={() => setMode('sign-up')}
                  className="font-medium text-foreground underline decoration-ring decoration-2 underline-offset-4"
                >
                  Create an account
                </button>
              </>
            ) : (
              <>
                Already have an account?{' '}
                <button
                  type="button"
                  onClick={() => setMode('sign-in')}
                  className="font-medium text-foreground underline decoration-ring decoration-2 underline-offset-4"
                >
                  Sign in
                </button>
              </>
            )}
          </p>
        </div>
      </main>
    </div>
  )
}
