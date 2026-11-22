import React from 'react'

export interface SectionIndexProps {
  index: string
  title: string
  className?: string
}

export const SectionIndex: React.FC<SectionIndexProps> = ({
  index,
  title,
  className = '',
}) => {
  return (
    <div className={`w-full ${className}`}>
      <div className="w-full h-[1px] bg-line mb-3" />
      <span className="font-mono text-xs uppercase tracking-widest text-muted">
        {index} / {title}
      </span>
    </div>
  )
}

export default SectionIndex
