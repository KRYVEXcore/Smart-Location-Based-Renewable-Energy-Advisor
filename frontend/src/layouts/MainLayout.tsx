import { useState, type PropsWithChildren } from 'react'
import { Navbar } from '../components/navigation/Navbar'
import { Footer } from '../components/layout/Footer'
import { FloatingAdvisorButton } from '../components/advisor/FloatingAdvisorButton'
import { AdvisorPanel } from '../components/advisor/AdvisorPanel'

export function MainLayout({ children }: PropsWithChildren) {
  const [isAdvisorOpen, setIsAdvisorOpen] = useState(false)

  return (
    <div className="flex min-h-screen flex-col bg-white">
      <Navbar onOpenAdvisor={() => setIsAdvisorOpen(true)} />
      <main className="flex-1">{children}</main>
      <Footer />
      <FloatingAdvisorButton onClick={() => setIsAdvisorOpen(true)} />
      <AdvisorPanel open={isAdvisorOpen} onClose={() => setIsAdvisorOpen(false)} />
    </div>
  )
}
