import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  CheckCircle2,
  XCircle,
  AlertTriangle,
  ArrowRight,
  RotateCcw,
  ShieldAlert,
  Sparkles,
  AlertCircle,
  RefreshCw,
  Lightbulb,
  Target,
} from 'lucide-react'
import { fetchApi } from '../api/client'
import type { AttemptResponse } from '../api/types'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Tag } from '../components/ui/Tag'
import { Skeleton } from '../components/ui/Skeleton'
import { AgentLog } from '../components/AgentLog'
import { StepList } from '../components/StepList'
import { PageTransition } from '../components/PageTransition'

const STREAMING_LOG_CANDIDATES = [
  'Ingesting practical demonstration video...',
  'Extracting timestamped video frames (768px JPEG)...',
  'Verifying challenge code presence on screen / paper...',
  'Evaluating visual step criteria against skill blueprint...',
  'Executing N1 Safety Gate verification...',
  'Calculating deterministic competence score...',
  'Synthesizing review verdict and evidence citation...',
]

export default function Review() {
  const { attemptId } = useParams<{ attemptId: string }>()
  const navigate = useNavigate()

  const [data, setData] = useState<AttemptResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [streamingLogs, setStreamingLogs] = useState<string[]>([])
  const [displayScore, setDisplayScore] = useState<number>(0)

  const logIndexRef = useRef<number>(0)

  // 1. Polling GET /api/attempts/{attemptId}
  useEffect(() => {
    if (!attemptId) {
      setError('Missing attempt ID in URL')
      return
    }

    let isCancelled = false

    const pollAttempt = async () => {
      try {
        const res = await fetchApi<AttemptResponse>(`/api/attempts/${attemptId}`)
        if (isCancelled) return

        if (res.data) {
          setData(res.data)
        }
      } catch (err: unknown) {
        if (isCancelled) return
        const msg = err instanceof Error ? err.message : 'Error polling review state'
        setError(msg)
      }
    }

    // Initial immediate fetch
    pollAttempt()

    // Interval every 1.5 seconds while analyzing
    const interval = setInterval(() => {
      pollAttempt()
    }, 1500)

    return () => {
      isCancelled = true
      clearInterval(interval)
    }
  }, [attemptId])

  // Stop polling if data status is no longer analyzing
  const isAnalyzing = !data || data.status === 'analyzing'

  // 2. Simulated log streaming during analysis
  useEffect(() => {
    if (!isAnalyzing) return

    const logTimer = setInterval(() => {
      if (logIndexRef.current < STREAMING_LOG_CANDIDATES.length) {
        const nextLog = STREAMING_LOG_CANDIDATES[logIndexRef.current]
        setStreamingLogs((prev) => [...prev, nextLog])
        logIndexRef.current += 1
      }
    }, 1200)

    return () => clearInterval(logTimer)
  }, [isAnalyzing])

  // 3. Count-up animation for video score when review finishes
  useEffect(() => {
    if (!data || data.status === 'analyzing' || data.video_score === null) return

    const targetScore = Math.round(data.video_score)
    let current = 0
    const stepTime = 15
    const steps = 30
    const increment = targetScore / steps

    const counter = setInterval(() => {
      current += increment
      if (current >= targetScore) {
        setDisplayScore(targetScore)
        clearInterval(counter)
      } else {
        setDisplayScore(Math.floor(current))
      }
    }, stepTime)

    return () => clearInterval(counter)
  }, [data])

  const decision = data?.decision?.toLowerCase()
  const isAccepted = decision === 'accept'
  const isNeedsRerecord = decision === 'needs_rerecord'
  const isRejected = decision === 'reject' || (data?.fraud_flags && data.fraud_flags.length > 0)

  return (
    <PageTransition>
      <div className="min-h-screen bg-paper flex flex-col justify-between max-w-xl mx-auto px-4 py-4 md:py-8 space-y-6">
        {/* Header */}
        <header className="border-b border-ink/10 pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-heading font-black text-lg text-ink">SAKSHI</span>
              <span className="text-ink/30">•</span>
              <Tag variant="accent">Verification Review</Tag>
            </div>
            <div className="font-mono text-xs text-ink/60 uppercase">
              {data?.status || 'Analyzing'}
            </div>
          </div>
        </header>

        {/* Error State */}
        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
            <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
            <div className="flex-1">
              <p className="font-bold">Error loading review state</p>
              <p className="text-xs text-red-600 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* State A: Analyzing / Ingestion Mode */}
        {isAnalyzing && (
          <main className="space-y-6">
            <Card className="p-6 text-center space-y-4">
              <div className="w-16 h-16 rounded-full bg-orange/10 border border-orange/30 flex items-center justify-center mx-auto">
                <Sparkles className="w-8 h-8 text-orange animate-spin" />
              </div>

              <div className="space-y-1">
                <h2 className="font-heading font-bold text-xl text-ink">
                  AI Verifying Demonstration...
                </h2>
                <p className="font-sans text-xs text-ink/60 max-w-sm mx-auto">
                  Comparing extracted video frames against visual criteria and verifying challenge code.
                </p>
              </div>

              <div className="pt-2">
                <Skeleton className="h-2 w-full rounded-full overflow-hidden">
                  <motion.div
                    className="h-full bg-orange"
                    initial={{ x: '-100%' }}
                    animate={{ x: '100%' }}
                    transition={{ repeat: Infinity, duration: 1.5, ease: 'linear' }}
                  />
                </Skeleton>
              </div>
            </Card>

            <AgentLog
              lines={streamingLogs}
              title="Autonomous Pipeline Execution"
              className="bg-white shadow-sm"
            />
          </main>
        )}

        {/* State B: Review Complete Mode */}
        {!isAnalyzing && data && (
          <main className="space-y-6">
            {/* Top Verdict Banner */}
            <Card
              className={`p-6 text-center space-y-4 ${
                isAccepted
                  ? 'border-emerald-300 bg-emerald-50/40'
                  : isNeedsRerecord
                  ? 'border-amber-300 bg-amber-50/40'
                  : 'border-red-300 bg-red-50/40'
              }`}
            >
              <div className="flex justify-center">
                {isAccepted && (
                  <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center border border-emerald-300">
                    <CheckCircle2 className="w-9 h-9 text-emerald-600" />
                  </div>
                )}
                {isNeedsRerecord && (
                  <div className="w-16 h-16 rounded-full bg-amber-100 flex items-center justify-center border border-amber-300">
                    <AlertTriangle className="w-9 h-9 text-amber-600" />
                  </div>
                )}
                {isRejected && (
                  <div className="w-16 h-16 rounded-full bg-red-100 flex items-center justify-center border border-red-300">
                    <XCircle className="w-9 h-9 text-red-600" />
                  </div>
                )}
              </div>

              <div>
                <div className="font-heading font-black text-5xl text-ink tracking-tight">
                  {displayScore}
                  <span className="text-2xl text-ink/50 font-normal">%</span>
                </div>
                <div className="font-mono text-xs uppercase tracking-wider text-ink/50 mt-1">
                  Practical Competence Score
                </div>
              </div>

              <div className="pt-1">
                <span
                  className={`inline-block font-mono text-xs font-bold uppercase tracking-widest px-3 py-1 rounded-full border ${
                    isAccepted
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : isNeedsRerecord
                      ? 'bg-amber-100 text-amber-800 border-amber-300'
                      : 'bg-red-100 text-red-800 border-red-300'
                  }`}
                >
                  {isAccepted
                    ? 'VERIFICATION ACCEPTED'
                    : isNeedsRerecord
                    ? 'RE-RECORD REQUIRED'
                    : 'ATTEMPT REJECTED'}
                </span>
                <p className="text-xs text-ink/70 font-sans mt-2 max-w-sm mx-auto">
                  {isAccepted
                    ? 'Demonstration met all safety critical and visual blueprint standards.'
                    : isNeedsRerecord
                    ? 'Critical steps were missing or unclear. Please re-record to continue.'
                    : 'Attempt failed competence threshold or triggered fraud flags.'}
                </p>
              </div>
            </Card>

            {/* Fraud Flags Alert if any */}
            {data.fraud_flags && data.fraud_flags.length > 0 && (
              <div className="p-4 rounded-xl bg-red-50 border border-red-300 space-y-2">
                <div className="flex items-center gap-2 font-bold text-sm text-red-800">
                  <ShieldAlert className="w-4 h-4 text-red-600" />
                  <span>Fraud & Integrity Warnings</span>
                </div>
                <div className="space-y-1.5 pl-6 text-xs text-red-700">
                  {data.fraud_flags.map((flag, idx) => (
                    <div key={idx} className="leading-normal font-mono">
                      <span className="font-bold">[{flag.code}]: </span>
                      <span>{flag.detail}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* AI Coach Card (Prompt 3) */}
            {(isNeedsRerecord || isRejected || data.coaching) && data.coaching && (
              <Card className="p-5 bg-orange/5 border border-orange/30 shadow-sm space-y-4">
                <div className="flex items-center gap-2.5 border-b border-orange/15 pb-3">
                  <div className="w-8 h-8 rounded-full bg-orange/10 flex items-center justify-center border border-orange/30 text-orange">
                    <Lightbulb className="w-4 h-4 text-orange" />
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <h3 className="font-heading font-bold text-sm text-ink">
                        AI Coach & Feedback
                      </h3>
                      <Tag variant="accent" className="text-[9px] py-0 px-2">
                        Guidance
                      </Tag>
                    </div>
                    <p className="font-sans text-[11px] text-ink/60">
                      Personalized guidance to improve your practical demonstration
                    </p>
                  </div>
                </div>

                <div className="p-3 bg-white/90 rounded-xl border border-orange/15 text-xs text-ink/80 font-sans leading-relaxed">
                  <p className="font-semibold text-ink mb-1 text-[11px] uppercase font-mono tracking-wider text-orange">
                    Summary:
                  </p>
                  <p>{data.coaching.summary}</p>
                </div>

                {data.coaching.next_actions && data.coaching.next_actions.length > 0 && (
                  <div className="space-y-2">
                    <span className="font-mono text-[11px] font-bold text-ink/70 uppercase tracking-wider flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-orange" />
                      Actionable Next Steps
                    </span>
                    <div className="space-y-1.5">
                      {data.coaching.next_actions.map((action, idx) => (
                        <div
                          key={idx}
                          className="flex items-start gap-2.5 text-xs text-ink/85 bg-white/80 p-2.5 rounded-lg border border-orange/10"
                        >
                          <span className="w-4 h-4 rounded-full bg-orange/15 text-orange font-mono text-[10px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                            {idx + 1}
                          </span>
                          <span className="font-sans leading-snug">{action}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </Card>
            )}

            {/* Step-by-Step Breakdown */}
            <Card className="p-5 space-y-3">
              <div className="flex items-center justify-between border-b border-ink/10 pb-2">
                <h3 className="font-heading font-bold text-sm text-ink">
                  Blueprint Criteria Verification
                </h3>
                <span className="font-mono text-xs text-ink/50">
                  {data.steps.filter((s) => s.verdict.toLowerCase() === 'pass').length}/
                  {data.steps.length} Passed
                </span>
              </div>

              <StepList steps={data.steps} tips={data.coaching?.unclear_steps_tips} />
            </Card>

            {/* Agent Reasoning Log */}
            {data.agent_log && data.agent_log.length > 0 && (
              <AgentLog
                lines={data.agent_log}
                title="AI Evaluator Decision Trail"
                className="bg-white shadow-sm"
              />
            )}
          </main>
        )}

        {/* Footer Actions */}
        {!isAnalyzing && data && (
          <footer className="pt-4 border-t border-ink/10 space-y-3">
            {isAccepted && (
              <Button
                variant="primary"
                onClick={() => navigate(`/witnesses/${attemptId}`)}
                className="w-full justify-center h-14 text-base font-semibold !bg-orange text-paper hover:!bg-orange/90 shadow-lg"
              >
                <span>Next: Invite Witnesses</span>
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            )}

            {isNeedsRerecord && (
              <Button
                variant="primary"
                onClick={() => {
                  const failedStepIds = data.steps
                    .filter((s) => s.verdict.toLowerCase() !== 'pass')
                    .map((s) => s.id)
                  const stepsParam = encodeURIComponent(failedStepIds.join(','))
                  navigate(`/record/${attemptId}?rerecord=true&steps=${stepsParam}`, {
                    state: { step_ids: failedStepIds },
                  })
                }}
                className="w-full justify-center h-14 text-base font-semibold !bg-orange text-paper hover:!bg-orange/90 shadow-lg"
              >
                <RotateCcw className="w-5 h-5 mr-2" />
                <span>Re-record Failed Steps</span>
              </Button>
            )}

            {isRejected && (
              <div className="space-y-2">
                <Button
                  variant="primary"
                  onClick={() => navigate('/skill')}
                  className="w-full justify-center h-12 text-sm font-semibold"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  <span>Start New Assessment</span>
                </Button>
              </div>
            )}
          </footer>
        )}
      </div>
    </PageTransition>
  )
}
