import { Section } from '../components/layout/Section'
import { AdvisorExperience } from '../components/advisor/AdvisorExperience'

export function AdvisorPage() {
  return (
    <Section width="narrow">
      <div className="rounded-3xl border border-slate-200 bg-white">
        <AdvisorExperience />
      </div>
    </Section>
  )
}
