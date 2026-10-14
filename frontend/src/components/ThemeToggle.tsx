import { MoonIcon, SunIcon } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'

const STORAGE_KEY = 'curated-space-theme'

/** Kept in step with --background in index.css; the browser UI is told, not asked. */
const THEME_COLOR: Record<Theme, string> = { light: '#f2f2f1', dark: '#101112' }

type Theme = 'light' | 'dark'

function currentTheme(): Theme {
  return document.documentElement.classList.contains('dark') ? 'dark' : 'light'
}

export function ThemeToggle() {
  // The inline script in index.html has already applied the class before first
  // paint, so reading it during the first render is accurate.
  const [theme, setTheme] = useState<Theme>(currentTheme)

  function toggle() {
    const next = currentTheme() === 'dark' ? 'light' : 'dark'
    document.documentElement.classList.toggle('dark', next === 'dark')
    document.documentElement.classList.toggle('light', next === 'light')
    document
      .querySelector('meta[name="theme-color"]')
      ?.setAttribute('content', THEME_COLOR[next])
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // A browser with storage blocked still gets the toggle; it just will not
      // survive a reload.
    }
    setTheme(next)
  }

  return (
    <Button
      variant="ghost"
      size="icon"
      onClick={toggle}
      aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      {theme === 'dark' ? <MoonIcon /> : <SunIcon />}
    </Button>
  )
}