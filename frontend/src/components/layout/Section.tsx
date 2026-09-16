import type { PropsWithChildren } from 'react'
import { cn } from '../../utils/cn'

const WIDTH_STYLES = {
  default: 'max-w-6xl',
  narrow: 'max-w-2xl',
} as const

interface SectionProps extends PropsWithChildren {
  id?: string
  className?: string
  width?: keyof typeof WIDTH_STYLES
}

export function Section({ id, className, width = 'default', children }: SectionProps) {
  return (
    <section id={id} className={cn('mx-auto w-full px-6 py-16 sm:py-20', WIDTH_STYLES[width], className)}>
      {children}
    </section>
  )
}
