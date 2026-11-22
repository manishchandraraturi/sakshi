import { motion } from 'framer-motion'

interface AgentLogProps {
  lines: string[]
  className?: string
  title?: string
}

export function AgentLog({ lines, className = '', title }: AgentLogProps) {
  if (!lines || lines.length === 0) return null

  return (
    <div
      className={`rounded-lg border border-ink/10 bg-ink/[0.03] p-3 font-mono text-xs text-ink/80 ${className}`}
    >
      {title && (
        <div className="mb-2 flex items-center gap-1.5 text-[10px] font-semibold uppercase tracking-wider text-ink/40">
          <span className="h-1.5 w-1.5 rounded-full bg-orange animate-pulse" />
          {title}
        </div>
      )}
      <div className="space-y-1.5">
        {lines.map((line, index) => (
          <motion.div
            key={`${index}-${line.slice(0, 10)}`}
            initial={{ opacity: 0, x: -4 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.2, delay: index * 0.05 }}
            className="flex items-start gap-1.5 leading-relaxed"
          >
            <span className="text-orange select-none font-bold">{'>'}</span>
            <span className="text-ink/90">{line}</span>
          </motion.div>
        ))}
      </div>
    </div>
  )
}
