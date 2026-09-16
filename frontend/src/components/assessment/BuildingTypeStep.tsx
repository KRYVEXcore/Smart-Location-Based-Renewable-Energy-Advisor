import { Building2, GraduationCap, Home, Landmark, Store } from 'lucide-react'
import { SelectableCard } from '../cards/SelectableCard'
import type { BuildingType } from '../../types/assessment'

const OPTIONS: { value: BuildingType; label: string; icon: typeof Home }[] = [
  { value: 'home', label: 'Home', icon: Home },
  { value: 'school', label: 'School', icon: GraduationCap },
  { value: 'office', label: 'Office', icon: Building2 },
  { value: 'shop', label: 'Shop', icon: Store },
  { value: 'small_institution', label: 'Small Institution', icon: Landmark },
]

interface BuildingTypeStepProps {
  value: BuildingType | null
  onChange: (value: BuildingType) => void
}

export function BuildingTypeStep({ value, onChange }: BuildingTypeStepProps) {
  return (
    <div>
      <h2 className="text-2xl font-bold text-slate-900">What kind of building is it?</h2>
      <p className="mt-1 text-sm text-slate-500">This shapes typical consumption patterns.</p>

      <div className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-3">
        {OPTIONS.map((option) => (
          <SelectableCard
            key={option.value}
            icon={option.icon}
            label={option.label}
            selected={value === option.value}
            onClick={() => onChange(option.value)}
          />
        ))}
      </div>
    </div>
  )
}
