import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, XCircle, HelpCircle, ChevronDown, Image as ImageIcon } from 'lucide-react'
import type { StepResult } from '../api/types'
import { Tag } from './ui/Tag'

interface StepListProps {
  steps: StepResult[]
  className?: string
}

export function StepList({ steps, className = '' }: StepListProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null)

  if (!steps || steps.length === 0) {
    return (
      <div className="py-4 text-center text-sm font-mono text-ink/50">
        No step verification results available.
      </div>
    )
  }

  const toggleExpand = (id: string) => {
    setExpandedId((prev) => (prev === id ? null : id))
  }

  return (
    <div className={`divide-y divide-ink/10 ${className}`}>
      {steps.map((step, index) => {
        const isExpanded = expandedId === step.id
        const verdict = step.verdict.toLowerCase()

        return (
          <div key={step.id} className="py-3.5 first:pt-1 last:pb-1">
            <div
              onClick={() => toggleExpand(step.id)}
              className="flex items-start justify-between gap-3 cursor-pointer group select-none"
            >
              {/* Left: Index + Status Icon + Title */}
              <div className="flex items-start gap-3 flex-1 min-w-0">
                <span className="font-mono text-xs text-ink/40 font-semibold pt-0.5 w-5">
                  {String(index + 1).padStart(2, '0')}
                </span>

                <div className="pt-0.5 shrink-0">
                  {verdict === 'pass' && (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                  )}
                  {verdict === 'fail' && (
                    <XCircle className="w-5 h-5 text-red-600" />
                  )}
                  {verdict === 'unclear' && (
                    <HelpCircle className="w-5 h-5 text-amber-500" />
                  )}
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-sans font-semibold text-sm text-ink group-hover:text-orange transition-colors">
                      {step.title || step.id}
                    </span>

                    {step.safety_critical && (
                      <Tag variant="danger" className="text-[9px] py-0 px-2">
                        Safety Critical
                      </Tag>
                    )}
                    {!step.safety_critical && step.critical && (
                      <Tag variant="accent" className="text-[9px] py-0 px-2">
                        Critical
                      </Tag>
                    )}
                  </div>

                  {step.note && (
                    <p className="text-xs text-ink/70 font-sans mt-1 leading-normal line-clamp-2">
                      {step.note}
                    </p>
                  )}
                </div>
              </div>

              {/* Right: Verdict Badge + Chevron */}
              <div className="flex items-center gap-2 shrink-0">
                <span
                  className={`font-mono text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${
                    verdict === 'pass'
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : verdict === 'fail'
                      ? 'bg-red-50 text-red-700 border-red-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  }`}
                >
                  {verdict}
                </span>

                <ChevronDown
                  className={`w-4 h-4 text-ink/40 transition-transform duration-200 ${
                    isExpanded ? 'rotate-180 text-ink' : ''
                  }`}
                />
              </div>
            </div>

            {/* Expandable Evidence Details */}
            <AnimatePresence>
              {isExpanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="overflow-hidden"
                >
                  <div className="mt-2.5 ml-8 pl-3 border-l-2 border-orange/40 bg-ink/[0.02] p-2.5 rounded-r-lg space-y-2 text-xs">
                    {step.note && (
                      <div>
                        <span className="font-mono text-[10px] uppercase text-ink/50 font-semibold block">
                          Evaluator Note:
                        </span>
                        <p className="text-ink/80 font-sans mt-0.5">{step.note}</p>
                      </div>
                    )}

                    <div className="flex flex-wrap items-center gap-4 text-[11px] font-mono text-ink/60">
                      <div>
                        <span>Confidence: </span>
                        <span className="font-bold text-ink">
                          {Math.round((step.confidence || 0) * 100)}%
                        </span>
                      </div>

                      {step.evidence_frames && step.evidence_frames.length > 0 && (
                        <div className="flex items-center gap-1.5">
                          <ImageIcon className="w-3.5 h-3.5 text-orange" />
                          <span>
                            Evidence Frames: [{step.evidence_frames.join(', ')}]
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )
      })}
    </div>
  )
}
