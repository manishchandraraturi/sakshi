import React from 'react'
import { motion, HTMLMotionProps } from 'framer-motion'
import { ArrowRight } from 'lucide-react'

export interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children: React.ReactNode
  variant?: 'primary' | 'secondary' | 'outline' | 'danger'
  showArrow?: boolean
  loading?: boolean
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  showArrow = false,
  loading = false,
  className = '',
  disabled,
  ...props
}) => {
  const baseStyles =
    'relative inline-flex items-center justify-center font-body font-medium rounded-pill px-6 py-3 transition-colors duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed select-none'

  const variantStyles = {
    primary: 'bg-ink text-paper hover:bg-ink-2 shadow-sm',
    secondary: 'bg-paper-2 text-ink hover:bg-paper border border-line',
    outline: 'border border-ink/30 text-ink hover:border-ink bg-transparent',
    danger: 'bg-danger text-paper hover:opacity-90',
  }[variant]

  return (
    <motion.button
      whileHover={disabled || loading ? undefined : { y: -4 }}
      whileTap={disabled || loading ? undefined : { y: 0 }}
      transition={{ duration: 0.15, ease: [0.22, 1, 0.36, 1] }}
      className={`${baseStyles} ${variantStyles} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      <span className="inline-flex items-center gap-2">
        {children}
        {showArrow && !loading && (
          <motion.span
            className="inline-block"
            initial={{ x: 0 }}
            whileHover={{ x: 6 }}
            transition={{ duration: 0.2 }}
          >
            <ArrowRight className="w-4 h-4 ml-1" />
          </motion.span>
        )}
      </span>
      {loading && (
        <span className="absolute bottom-1.5 left-6 right-6 h-[2px] bg-accent/80 rounded-full animate-pulse" />
      )}
    </motion.button>
  )
}

export default Button
