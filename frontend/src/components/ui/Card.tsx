import React from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'

export interface CardProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode
  variant?: 'paper' | 'ink'
  hoverLift?: boolean
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'paper',
  hoverLift = true,
  className = '',
  ...props
}) => {
  const variantStyles = {
    paper: 'bg-paper-2 text-ink border-line',
    ink: 'bg-ink-2 text-paper border-ink-3',
  }[variant]

  return (
    <motion.div
      whileHover={hoverLift ? { y: -4 } : undefined}
      transition={{ duration: 0.2, ease: [0.22, 1, 0.36, 1] }}
      className={`rounded-2xl border p-6 md:p-8 shadow-sm transition-shadow ${variantStyles} ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  )
}

export default Card
