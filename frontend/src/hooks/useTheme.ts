import { useCallback, useState } from 'react'

export type Theme = 'light' | 'dark'

const STORAGE_KEY = 'shrea-theme'

// index.html applies the saved theme (or the system one on a first visit) before the first paint,
// so this only reads it back and handles the toggle.
export function useTheme() {
  const [theme, setTheme] = useState<Theme>(() => (document.documentElement.classList.contains('dark') ? 'dark' : 'light'))

  const toggleTheme = useCallback(() => {
    const next: Theme = theme === 'dark' ? 'light' : 'dark'
    const root = document.documentElement
    root.classList.add('theme-transition') // lets the colours fade only during the switch (see index.css)
    root.classList.toggle('dark', next === 'dark')
    window.setTimeout(() => root.classList.remove('theme-transition'), 350)
    try {
      localStorage.setItem(STORAGE_KEY, next)
    } catch {
      // Storage can be blocked (private mode); the choice then just isn't remembered.
    }
    setTheme(next)
  }, [theme])

  return { theme, toggleTheme }
}
