import React from 'react'

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string
  width?: string | number
  height?: string | number
}

export const Skeleton: React.FC<SkeletonProps> = ({
  className = '',
  style,
  width,
  height,
  ...props
}) => {
  return (
    <div
      className={`animate-pulse bg-paper-2 rounded-md ${className}`}
      style={{
        width,
        height,
        ...style,
      }}
      {...props}
    />
  )
}

export default Skeleton
