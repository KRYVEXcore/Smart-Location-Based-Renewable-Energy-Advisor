import { useState, type PropsWithChildren } from 'react'
import { useLocation } from 'react-router-dom'
import { Navbar } from '../components/navigation/Navbar'
import { Footer } from '../components/layout/Footer'
import { FloatingAdvisorButton } from '../components/advisor/FloatingAdvisorButton'
import { AdvisorPanel } from '../components/advisor/AdvisorPanel'

// The floating button would sit over the wizard's Continue/Submit buttons and the
// chat input on these pages, and both are reachable from the navbar instead.
const PAGES_WITHOUT_FLOATING_BUTTON = ['/assess', '/advisor']

export function MainLayout({ children }: PropsWithChildren) {
  const [isAdvisorOpen, setIsAdvisorOpen] = useState(false)
  const { pathname } = useLocation()

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar onOpenAdvisor={() => setIsAdvisorOpen(true)} />
      <main className="flex-1">{children}</main>
      <Footer />
      {!PAGES_WITHOUT_FLOATING_BUTTON.includes(pathname) && (
        <FloatingAdvisorButton onClick={() => setIsAdvisorOpen(true)} />
      )}
      <AdvisorPanel open={isAdvisorOpen} onClose={() => setIsAdvisorOpen(false)} />
    </div>
  )
}
