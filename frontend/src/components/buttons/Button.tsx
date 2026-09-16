import type { AnchorHTMLAttributes, ButtonHTMLAttributes } from 'react'
import { Link, type LinkProps } from 'react-router-dom'
import { cn } from '../../utils/cn'

type Variant = 'primary' | 'secondary' | 'ghost'
type Size = 'md' | 'lg'

const VARIANT_STYLES: Record<Variant, string> = {
  primary:
    'bg-emerald-600 text-white shadow-sm shadow-emerald-600/20 hover:bg-emerald-700 active:bg-emerald-800',
  secondary:
    'bg-white text-slate-900 border border-slate-200 hover:border-slate-300 hover:bg-slate-50',
  ghost: 'text-slate-600 hover:text-slate-900 hover:bg-slate-100',
}

const SIZE_STYLES: Record<Size, string> = {
  md: 'px-4 py-2.5 text-sm',
  lg: 'px-6 py-3.5 text-base',
}

const BASE_STYLES =
  'inline-flex items-center justify-center gap-2 rounded-full font-semibold transition-colors duration-150 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-emerald-600 disabled:cursor-not-allowed disabled:opacity-50'

interface CommonProps {
  variant?: Variant
  size?: Size
  className?: string
}

type ButtonAsButton = CommonProps &
  ButtonHTMLAttributes<HTMLButtonElement> & { to?: undefined; href?: undefined }

type ButtonAsLink = CommonProps & LinkProps & { to: string; href?: undefined }

type ButtonAsAnchor = CommonProps &
  AnchorHTMLAttributes<HTMLAnchorElement> & { href: string; to?: undefined }

type ButtonProps = ButtonAsButton | ButtonAsLink | ButtonAsAnchor

export function Button({ variant = 'primary', size = 'md', className, ...props }: ButtonProps) {
  const classes = cn(BASE_STYLES, VARIANT_STYLES[variant], SIZE_STYLES[size], className)

  if ('to' in props && props.to !== undefined) {
    const { to, ...linkProps } = props
    return <Link to={to} className={classes} {...linkProps} />
  }

  if ('href' in props && props.href !== undefined) {
    const { href, ...anchorProps } = props
    return <a href={href} className={classes} {...anchorProps} />
  }

  const { type = 'button', ...buttonProps } = props as ButtonAsButton
  return <button type={type} className={classes} {...buttonProps} />
}
