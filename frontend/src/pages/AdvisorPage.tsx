import { Section } from '../components/layout/Section'
import { AdvisorChat } from '../components/advisor/AdvisorChat'

export function AdvisorPage() {
  return (
    <Section width="narrow">
      <div className="flex h-[70vh] min-h-[440px] flex-col rounded-3xl border border-slate-200 bg-white">
        <AdvisorChat className="flex-1" />
      </div>
    </Section>
  )
}
