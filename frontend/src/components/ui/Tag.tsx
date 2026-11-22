import React from 'react'

export interface TagProps extends React.HTMLAttributes<HTMLSpanElement> {
  children: React.ReactNode
  variant?: 'default' | 'accent' | 'danger' | 'muted'
}

export const Tag: React.FC<TagProps> = ({
  children,
  variant = 'default',
  className = '',
  ...props
}) => {
  const variantStyles = {
    default: 'border-line text-ink bg-paper-2/60',
    accent: 'border-accent/40 text-accent bg-accent/5',
    danger: 'border-danger/40 text-danger bg-danger/5',
    muted: 'border-line text-muted bg-transparent',
  }[variant]

  return (
    <span
      className={`inline-flex items-center font-mono text-[11px] uppercase tracking-widest px-3 py-1 rounded-pill border select-none ${variantStyles} ${className}`}
      {...props}
    >
      {children}
    </span>
  )
}

export default Tag
