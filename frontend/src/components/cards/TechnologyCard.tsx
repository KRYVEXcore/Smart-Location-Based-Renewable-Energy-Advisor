import type { LucideIcon } from 'lucide-react'

interface TechnologyCardProps {
  icon: LucideIcon
  name: string
  tagline: string
  gradient: string
}

export function TechnologyCard({ icon: Icon, name, tagline, gradient }: TechnologyCardProps) {
  return (
    <div className="group rounded-2xl border border-slate-200 bg-white p-6 transition-all hover:-translate-y-1 hover:shadow-lg hover:shadow-slate-200/60">
      <span
        className={`flex h-12 w-12 items-center justify-center rounded-xl bg-gradient-to-br ${gradient} text-white`}
      >
        <Icon className="h-6 w-6" aria-hidden="true" />
      </span>
      <h3 className="mt-4 font-semibold text-slate-900">{name}</h3>
      <p className="mt-1 text-sm text-slate-500">{tagline}</p>
    </div>
  )
}
