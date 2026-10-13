import { useEffect, useId, useRef, useState, type FormEvent } from 'react'
import { Navigate, useLocation, useNavigate, type Location } from 'react-router-dom'
import { ThemeToggle } from '@/components/ThemeToggle'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { useAuth } from '@/lib/auth-context'
import { ApiError } from '@/lib/errors'

type Mode = 'sign-in' | 'create'

/**
 * Where to go after signing in: back to whatever protected page sent the
 * reader here, or the library. `/login` is never a valid destination.
 */
function returnPath(location: Location): string {
  const from = (location.state as { from?: string } | null)?.from
  return from && from !== '/login' ? from : '/'
}

/**
 * Sign in, or create the very first account.
 *
 * Both modes live on one page because a fresh install has exactly one person in
 * it: until the reader picks a tab, the form shows "create account" if nobody
 * has signed up yet and "sign in" otherwise. That is derived from
 * `GET /auth/status` during render rather than stored, so it corrects itself the
 * moment the status arrives or changes.
 *
 * The password is sent once and never stored, read back or logged. There is no
 * "remember me" checkbox on purpose: the session cookie is the only credential
 * and the backend sets its own lifetime.
 */
export function LoginPage() {
  const { account, isLoading, isSubmitting, status, signIn, createAccount } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [choice, setChoice] = useState<Mode | null>(null)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [error, setError] = useState<string | null>(null)
  const emailRef = useRef<HTMLInputElement>(null)
  const emailId = useId()
  const passwordId = useId()
  const confirmationId = useId()

  // Nobody has signed up yet, so create one; otherwise sign in.
  const isCreate = choice ?? status?.users === 0

  useEffect(() => {
    if (error) emailRef.current?.focus()
  }, [error])

  // A signed-in reader has no business on this page.
  if (!isLoading && account) {
    return <Navigate to={returnPath(location)} replace />
  }

  const registrationOpen = status?.registration_open ?? false
  const mismatch = isCreate && confirmation.length > 0 && confirmation !== password

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    if (isCreate && confirmation !== password) {
      setError('Those passwords do not match.')
      return
    }

    try {
      if (isCreate) {
        await createAccount(email.trim(), password)
      } else {
        await signIn(email.trim(), password)
      }
      // The provider now holds an account, so the redirect above takes over.
      navigate(returnPath(location), { replace: true })
    } catch (cause) {
      // The backend answers every failed attempt the same way, so this message
      // cannot be used to tell whether an address exists.
      if (cause instanceof ApiError) {
        setError(
          cause.isRateLimited
            ? 'Too many attempts. Wait a minute, then try again.'
            : cause.status === 401
              ? 'That email and password do not match an account.'
              : cause.message,
        )
      } else {
        setError('Could not reach the server. Check that the backend is running.')
      }
      setPassword('')
      setConfirmation('')
    }
  }

  return (
    <div className="flex min-h-dvh flex-col">
      <div className="flex items-center justify-end px-4 pt-4 sm:px-6">
        <ThemeToggle />
      </div>

      <main className="flex flex-1 items-center justify-center px-4 pb-16 sm:px-6">
        <div className="w-full max-w-sm">
          <div className="flex items-center gap-2.5 font-serif text-[17px] leading-none text-foreground">
            <span
              aria-hidden="true"
              className="block size-4 border border-foreground bg-[linear-gradient(135deg,transparent_45%,currentColor_45%,currentColor_55%,transparent_55%)]"
            />
            Curated Space
          </div>

          <h1 className="mt-8 font-serif text-3xl leading-tight tracking-tight">
            {isCreate ? 'Create your account' : 'Sign in'}
          </h1>
          <p className="mt-2 text-sm text-muted-foreground">
            {isCreate
              ? 'This library is private. One account owns the screenshots, and nothing leaves your machine without it.'
              : 'Your screenshot library is waiting.'}
          </p>

          <form onSubmit={onSubmit} noValidate className="mt-8 flex flex-col gap-5">
            <div className="flex flex-col gap-1.5">
              <label htmlFor={emailId} className="text-sm font-medium">
                Email
              </label>
              <Input
                ref={emailRef}
                id={emailId}
                name="email"
                type="email"
                autoComplete="username"
                required
                spellCheck={false}
                autoFocus
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                className="h-10 px-3"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <label htmlFor={passwordId} className="text-sm font-medium">
                Password
              </label>
              <Input
                id={passwordId}
                name="password"
                type="password"
                autoComplete={isCreate ? 'new-password' : 'current-password'}
                required
                minLength={isCreate ? 10 : undefined}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                className="h-10 px-3"
              />
              {isCreate ? (
                <p className="text-xs text-muted-foreground">
                  At least 10 characters. A short sentence you can remember beats a
                  scrambled word.
                </p>
              ) : null}
            </div>

            {isCreate ? (
              <div className="flex flex-col gap-1.5">
                <label htmlFor={confirmationId} className="text-sm font-medium">
                  Confirm password
                </label>
                <Input
                  id={confirmationId}
                  name="confirm-password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={confirmation}
                  onChange={(event) => setConfirmation(event.target.value)}
                  aria-invalid={mismatch || undefined}
                  className="h-10 px-3"
                />
                {mismatch ? (
                  <p className="text-xs text-destructive">Those passwords do not match.</p>
                ) : null}
              </div>
            ) : null}

            {error ? (
              <p role="alert" className="text-sm text-destructive">
                {error}
              </p>
            ) : null}

            <Button type="submit" disabled={isSubmitting} className="h-10 justify-center">
{isSubmitting
                ? isCreate
                  ? 'Creating account…'
                  : 'Signing in…'
                : isCreate
                  ? 'Create account'
                  : 'Sign in'}
            </Button>
          </form>

          {registrationOpen ? (
            <p className="mt-6 text-sm text-muted-foreground">
              {isCreate ? (
                <>
                  Already have an account?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setChoice('sign-in')
                      setError(null)
                    }}
                    className="text-foreground underline decoration-ring decoration-2 underline-offset-4"
                  >
                    Sign in
                  </button>
                </>
              ) : (
                <>
                  First time here?{' '}
                  <button
                    type="button"
                    onClick={() => {
                      setChoice('create')
                      setError(null)
                    }}
                    className="text-foreground underline decoration-ring decoration-2 underline-offset-4"
                  >
                    Create an account
                  </button>
                </>
              )}
            </p>
          ) : (
            <p className="mt-6 text-xs text-muted-foreground">
              This library already has an account. Ask its owner to add yours.
            </p>
          )}
        </div>
      </main>
    </div>
  )
}