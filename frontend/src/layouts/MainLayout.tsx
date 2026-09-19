import { useState, type PropsWithChildren } from 'react'
import { useLocation, useMatch } from 'react-router-dom'
import { Navbar } from '../components/navigation/Navbar'
import { Footer } from '../components/layout/Footer'
import { FloatingAdvisorButton } from '../components/advisor/FloatingAdvisorButton'
import { AdvisorPanel } from '../components/advisor/AdvisorPanel'

const isAdvisorPage = (pathname: string) => pathname === '/advisor' || pathname.startsWith('/advisor/')

export function MainLayout({ children }: PropsWithChildren) {
  const [isAdvisorOpen, setIsAdvisorOpen] = useState(false)
  const { pathname } = useLocation()
  // The chat is tied to the assessment whose dashboard (or advisor page) is open.
  const dashboardMatch = useMatch('/dashboard/:assessmentId')
  const advisorMatch = useMatch('/advisor/:assessmentId')
  const assessmentId = dashboardMatch?.params.assessmentId ?? advisorMatch?.params.assessmentId ?? null

  // One chat only: on the advisor page the navbar button focuses it instead of opening a second one.
  function openAdvisor() {
    if (isAdvisorPage(pathname)) document.getElementById('advisor-chat-input')?.focus()
    else setIsAdvisorOpen(true)
  }

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar onOpenAdvisor={openAdvisor} />
      <main className="flex-1">{children}</main>
      <Footer />
      {/* The floating button would sit over the wizard's Continue/Submit buttons and the chat input. */}
      {pathname !== '/assess' && !isAdvisorPage(pathname) && <FloatingAdvisorButton onClick={openAdvisor} />}
      <AdvisorPanel open={isAdvisorOpen} assessmentId={assessmentId} onClose={() => setIsAdvisorOpen(false)} />
    </div>
  )
}
