import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { CheckCircle2, AlertTriangle } from 'lucide-react'
import { fetchApi } from '../api/client'
import { Button } from '../components/ui/Button'
import { Tag } from '../components/ui/Tag'
import { SectionIndex } from '../components/ui/SectionIndex'
import { Skeleton } from '../components/ui/Skeleton'
import { PageTransition } from '../components/PageTransition'
import { useSessionStore } from '../store/session'
import { useTranslation } from '../i18n/t'

interface SkillStep {
  id: string
  title: string
  critical: boolean
}

interface SkillItem {
  id: string
  skill_id?: string
  name: string
  steps: SkillStep[]
}

interface TradeItem {
  trade: string
  skills: SkillItem[]
}

export default function SkillPick() {
  const navigate = useNavigate()
  const { t } = useTranslation()
  const { language, setWorkerToken, setAttemptId } = useSessionStore()

  const [trades, setTrades] = useState<TradeItem[]>([])
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<string | null>(null)
  const [activeIndex, setActiveIndex] = useState<number>(0)
  const [starting, setStarting] = useState<boolean>(false)

  useEffect(() => {
    fetchApi<TradeItem[]>('/api/skills')
      .then((res) => {
        if (res.data) {
          setTrades(res.data)
        }
        setLoading(false)
      })
      .catch((err) => {
        setError(err.message || 'Failed to load skill blueprints')
        setLoading(false)
      })
  }, [])

  const handleStartAssessment = async (skillId: string) => {
    if (starting) return
    setStarting(true)

    try {
      // 1. Generate unique device fingerprint and register worker
      const deviceFp =
        typeof crypto !== 'undefined' && crypto.randomUUID
          ? crypto.randomUUID()
          : `fp-${Date.now()}`

      const workerPayload = {
        name: 'Demo Worker',
        language: language || 'en',
        area: 'Local',
        consent: true,
        device_fp: deviceFp,
      }

      console.log('[SkillPick] 1. Registering worker:', workerPayload)

      const workerRes = await fetchApi<{ worker_id: string; token: string }>('/api/workers', {
        method: 'POST',
        body: JSON.stringify(workerPayload),
      })

      if (!workerRes.data) {
        throw new Error('Worker registration failed: No data returned from server')
      }

      const { worker_id, token } = workerRes.data
      setWorkerToken(token, worker_id)

      console.log('[SkillPick] 2. Starting attempt for skill:', skillId)

      // 2. Start attempt
      const attemptRes = await fetchApi<{
        attempt_id: string
        challenge_code: string
        checklist: unknown[]
      }>('/api/attempts', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          skill_id: skillId,
        }),
      })

      if (!attemptRes.data) {
        throw new Error('Attempt creation failed: No data returned from server')
      }

      const { attempt_id } = attemptRes.data
      setAttemptId(attempt_id)

      // 3. Navigate to interview
      navigate(`/interview/${attempt_id}`)
    } catch (err: unknown) {
      console.error('[SkillPick Error starting assessment]:', err)
      const errorData = (err as any)?.data || (err as any)?.response?.data
      if (errorData) {
        console.error('API Error Response Data:', errorData)
      }
      const message = err instanceof Error ? err.message : 'Failed to start assessment'
      alert(`Error starting assessment: ${message}`)
      setStarting(false)
    }
  }

  return (
    <PageTransition className="min-h-screen flex flex-col p-6 max-w-5xl mx-auto justify-center">
      <div className="w-full space-y-6">
        <div className="flex items-center justify-between">
          <SectionIndex index="02" title="TRADE SELECTION" />
          <Button
            variant="primary"
            onClick={() => {
              if (window.history.length > 1) {
                navigate(-1)
              } else {
                navigate('/')
              }
            }}
            className="!px-4 !py-1.5 !text-xs !h-8 font-mono rounded-pill !bg-ink text-paper hover:!bg-ink/85 shadow-sm"
          >
            Back
          </Button>
        </div>

        <div className="text-center sm:text-left space-y-2">
          <h1 className="text-4xl sm:text-5xl font-display font-extrabold text-ink tracking-tight">
            {t('pick_skill')}
            <span className="text-accent">.</span>
          </h1>
          <p className="font-body text-sm sm:text-base text-muted">{t('pick_skill_sub')}</p>
        </div>

        {loading ? (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4">
            <Skeleton className="h-80 w-full rounded-2xl" />
            <Skeleton className="h-80 w-full rounded-2xl" />
            <Skeleton className="h-80 w-full rounded-2xl" />
          </div>
        ) : error ? (
          <div className="p-8 text-center bg-paper-2 rounded-2xl border border-danger/30 space-y-4">
            <p className="text-danger font-mono text-sm">{error}</p>
            <Button variant="outline" onClick={() => window.location.reload()}>
              Retry
            </Button>
          </div>
        ) : (
          <div className="flex flex-col md:flex-row gap-4 pt-4 min-h-[460px]">
            {trades.map((item, idx) => {
              const isActive = activeIndex === idx
              const primarySkill = item.skills[0]
              const skillId = primarySkill?.skill_id || primarySkill?.id

              return (
                <motion.div
                  key={item.trade}
                  layout
                  transition={{ type: 'spring', stiffness: 260, damping: 30 }}
                  onClick={() => setActiveIndex(idx)}
                  className={`rounded-2xl border transition-all duration-300 overflow-hidden cursor-pointer flex flex-col ${
                    isActive
                      ? 'md:flex-[4] flex-1 bg-paper-2 border-ink shadow-lg p-6 sm:p-8'
                      : 'md:flex-[1] flex-none bg-paper-2/60 border-line hover:border-ink/30 p-4 sm:p-6'
                  }`}
                >
                  <AnimatePresence mode="wait">
                    {isActive ? (
                      <motion.div
                        key="active-content"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.25 }}
                        className="flex flex-col h-full justify-between space-y-6"
                      >
                        <div className="space-y-4">
                          <div className="flex items-center justify-between">
                            <Tag variant="accent">{item.trade}</Tag>
                            <span className="font-mono text-xs text-muted">
                              {primarySkill?.steps.length} {t('steps_count')} • {t('est_time')}
                            </span>
                          </div>

                          <h2 className="text-2xl sm:text-3xl font-display font-extrabold text-ink">
                            {primarySkill?.name}
                          </h2>

                          {/* Step preview list */}
                          <div className="space-y-2 pt-2 border-t border-line/70">
                            <div className="font-mono text-xs tracking-wider uppercase text-muted mb-2">
                              Verification Steps
                            </div>
                            {primarySkill?.steps.map((st, sIdx) => (
                              <div
                                key={st.id}
                                className="flex items-center gap-3 py-1.5 text-xs sm:text-sm font-body text-ink border-b border-line/40 last:border-b-0"
                              >
                                <span className="font-mono text-xs text-muted w-5">
                                  0{sIdx + 1}
                                </span>
                                <span className="flex-1 truncate">{st.title}</span>
                                {st.critical ? (
                                  <span className="flex items-center gap-1 font-mono text-[10px] text-accent uppercase">
                                    <AlertTriangle className="w-3 h-3" /> Critical
                                  </span>
                                ) : (
                                  <CheckCircle2 className="w-3.5 h-3.5 text-muted/60" />
                                )}
                              </div>
                            ))}
                          </div>
                        </div>

                        <div className="pt-4 flex items-center justify-between border-t border-line">
                          <span className="font-mono text-xs text-muted">
                            Live capture + Challenge Code
                          </span>
                          <Button
                            showArrow
                            loading={starting}
                            disabled={starting}
                            onClick={(e) => {
                              e.stopPropagation()
                              if (skillId) handleStartAssessment(skillId)
                            }}
                          >
                            {starting ? t('starting') : t('btn_start')}
                          </Button>
                        </div>
                      </motion.div>
                    ) : (
                      <motion.div
                        key="collapsed-content"
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="flex md:flex-col items-center justify-between h-full py-4 select-none"
                      >
                        <div className="font-mono text-xs text-muted hidden md:block">
                          0{idx + 1}
                        </div>
                        <div
                          className="font-display font-bold text-xl md:text-2xl text-ink tracking-tight whitespace-nowrap select-none md:-rotate-90 md:my-auto"
                          style={{ transformOrigin: 'center center' }}
                        >
                          {item.trade}
                        </div>
                        <div className="font-mono text-xs text-muted md:hidden">
                          0{idx + 1}
                        </div>
                        <div className="hidden md:block w-3" />
                      </motion.div>
                    )}
                  </AnimatePresence>
                </motion.div>
              )
            })}
          </div>
        )}
      </div>
    </PageTransition>
  )
}
