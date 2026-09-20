import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { Menu, Mic, Moon, Sun, X, Zap } from 'lucide-react'
import { useTheme } from '../../hooks/useTheme'
import { cn } from '../../utils/cn'

const NAV_LINKS = [
  { label: 'Home', to: '/' },
  { label: 'Assess', to: '/assess' },
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'Location', to: '/location' },
  { label: 'Monitoring', to: '/monitoring' },
  { label: 'AI Advisor', to: '/advisor' },
]

interface NavbarProps {
  onOpenAdvisor: () => void
}

export function Navbar({ onOpenAdvisor }: NavbarProps) {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  const { theme, toggleTheme } = useTheme()

  const linkClasses = ({ isActive }: { isActive: boolean }) =>
    cn(
      'whitespace-nowrap rounded-full px-3 py-2 text-sm font-medium transition-colors',
      isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:text-slate-900',
    )

  return (
    <header className="sticky top-0 z-30 border-b border-slate-200/80 bg-white/80 backdrop-blur-md">
      <nav className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-3">
        <NavLink to="/" className="flex items-center gap-2 font-semibold text-slate-900">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-600 text-white">
            <Zap className="h-4 w-4" aria-hidden="true" />
          </span>
          SHREA AI
        </NavLink>

        <ul className="hidden items-center gap-1 md:flex">
          {NAV_LINKS.map((link) => (
            <li key={link.to}>
              <NavLink to={link.to} className={linkClasses} end={link.to === '/'}>
                {link.label}
              </NavLink>
            </li>
          ))}
        </ul>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full text-slate-700 transition-colors hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600"
          >
            {theme === 'dark' ? <Sun className="h-5 w-5" aria-hidden="true" /> : <Moon className="h-5 w-5" aria-hidden="true" />}
          </button>
          <button
            type="button"
            onClick={onOpenAdvisor}
            className="hidden items-center gap-2 whitespace-nowrap rounded-full border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 transition-colors hover:border-emerald-300 hover:bg-emerald-50 hover:text-emerald-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 lg:inline-flex"
          >
            <Mic className="h-4 w-4" aria-hidden="true" />
            Talk to SHREA AI
          </button>
          <button
            type="button"
            onClick={() => setIsMenuOpen((open) => !open)}
            aria-expanded={isMenuOpen}
            aria-label={isMenuOpen ? 'Close menu' : 'Open menu'}
            className="inline-flex h-10 w-10 items-center justify-center rounded-full text-slate-700 hover:bg-slate-100 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 md:hidden"
          >
            {isMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>
      </nav>

      {isMenuOpen && (
        <div className="border-t border-slate-200 bg-white px-6 py-4 md:hidden">
          <ul className="flex flex-col gap-1">
            {NAV_LINKS.map((link) => (
              <li key={link.to}>
                <NavLink
                  to={link.to}
                  end={link.to === '/'}
                  onClick={() => setIsMenuOpen(false)}
                  className={({ isActive }) =>
                    cn(
                      'block rounded-lg px-3 py-2 text-sm font-medium',
                      isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-100',
                    )
                  }
                >
                  {link.label}
                </NavLink>
              </li>
            ))}
          </ul>
          <button
            type="button"
            onClick={() => {
              setIsMenuOpen(false)
              onOpenAdvisor()
            }}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-full bg-emerald-600 px-4 py-2.5 text-sm font-semibold text-white"
          >
            <Mic className="h-4 w-4" aria-hidden="true" />
            Talk to SHREA AI
          </button>
        </div>
      )}
    </header>
  )
}
