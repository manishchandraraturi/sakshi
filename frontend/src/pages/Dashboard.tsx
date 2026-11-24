import { useState, useEffect } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  Award,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  Clock,
  Briefcase,
  Compass,
  Lightbulb,
  Trash2,
  AlertCircle,
  Target,
} from 'lucide-react'
import { fetchApi } from '../api/client'
import PageTransition from '../components/PageTransition'
import Seal from '../components/Seal'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Tag } from '../components/ui/Tag'
import { Skeleton } from '../components/ui/Skeleton'
import { useSessionStore } from '../store/session'

export default function Dashboard() {
  const navigate = useNavigate()
  const { workerToken, workerId, attemptId, resetSession } = useSessionStore()
  const [deleting, setDeleting] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [activeAttempt, setActiveAttempt] = useState<any>(null)

  useEffect(() => {
    if (!attemptId) return
    let isMounted = true
    setLoading(true)
    fetchApi<any>(`/api/attempts/${attemptId}`)
      .then((res) => {
        if (isMounted && res.data) {
          setActiveAttempt(res.data)
        }
      })
      .catch((err) => {
        if (isMounted) setError(err.message || 'Failed to load active assessment')
      })
      .finally(() => {
        if (isMounted) setLoading(false)
      })
    return () => {
      isMounted = false
    }
  }, [attemptId])

  // Use stored worker identity or fallback to seeded hero candidate
  const workerName = workerToken ? 'Worker' : 'Ravi Kumar'
  const currentTier = 2 // Demonstration active tier: Tier 2 Witnessed
  const currentScore = 85

  const handleDeleteData = async () => {
    const confirmed = window.confirm(
      'Are you sure you want to delete all your verification data? This will permanently remove all uploaded videos, extracted frames, and revoke any credentials issued to you.'
    )
    if (!confirmed) return

    setDeleting(true)
    try {
      if (workerId && workerToken) {
        await fetchApi(`/api/workers/${workerId}/data`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${workerToken}`,
          },
        })
      }
    } catch (err) {
      console.error('Failed to delete worker data:', err)
    } finally {
      resetSession()
      navigate('/')
    }
  }

  const ladderSteps = [
    {
      tier: 0,
      title: 'Practice & Prep',
      desc: 'Complete safety blueprint and scenario review',
      done: true,
    },
    {
      tier: 1,
      title: 'Demonstrated',
      desc: 'Pass practical video test with AI score ≥ 70%',
      done: true,
    },
    {
      tier: 2,
      title: 'Witnessed',
      desc: 'Obtain peer vouches with total trust weight ≥ 1.0',
      done: true,
      current: true,
    },
    {
      tier: 3,
      title: 'Trusted',
      desc: 'Reach weight ≥ 3.0 with Master Trainer or Contractor vouch',
      done: false,
    },
  ]

  const recentAttempts = [
    ...(activeAttempt
      ? [
          {
            id: activeAttempt.id,
            skill: (activeAttempt.skill_id || 'Trade Assessment').replace(/_/g, ' ').toUpperCase(),
            trade: 'Current Attempt',
            date: 'Today',
            status: activeAttempt.decision || activeAttempt.status,
            score: Math.round(activeAttempt.video_score || 85),
            tier: 1,
          },
        ]
      : []),
    {
      id: 'att-elec-01',
      skill: 'Socket wiring & continuity test',
      trade: 'Electrician',
      date: 'Nov 22, 2026',
      status: 'Finalized',
      score: 92,
      tier: 3,
    },
    {
      id: 'att-mason-02',
      skill: 'Brick wall alignment & plumb test',
      trade: 'Mason',
      date: 'Nov 18, 2026',
      status: 'Reviewed',
      score: 78,
      tier: 2,
    },
  ]

  return (
    <PageTransition>
      <div className="min-h-screen bg-paper flex flex-col justify-between max-w-2xl mx-auto px-4 py-4 md:py-8 space-y-6">
        {/* Header */}
        <header className="border-b border-ink/10 pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-heading font-black text-lg text-ink">SAKSHI</span>
              <span className="text-ink/30">•</span>
              <Tag variant="accent">Worker Dashboard</Tag>
            </div>
            <Link
              to="/directory"
              className="text-xs font-mono text-orange hover:underline font-semibold"
            >
              Browse Directory →
            </Link>
          </div>
        </header>

        <main className="space-y-6">
          {error && (
            <div className="p-3.5 rounded-xl bg-red-50 border border-red-200 text-xs text-red-700 flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {loading && (
            <Skeleton className="h-44 w-full rounded-2xl" />
          )}

          {/* Welcome Hero Card */}
          <Card className="p-6 bg-white border border-ink/15 shadow-sm space-y-5">
            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-[11px] font-mono text-ink/50 uppercase tracking-wider block">
                  Candidate Profile
                </span>
                <h1 className="font-heading font-black text-2xl text-ink">
                  Welcome back, {workerName}
                </h1>
                <p className="font-sans text-xs text-ink/70">
                  Electrician & Vocational Tradesperson • Trust Score: {currentScore}/100
                </p>
              </div>

              <div className="shrink-0 flex items-center gap-3">
                <Seal tier={currentTier} size={84} />
              </div>
            </div>

            <div className="pt-2 border-t border-ink/10 flex flex-wrap items-center gap-2.5">
              <Button
                variant="primary"
                onClick={() => navigate('/skill')}
                className="flex-1 min-w-[200px] justify-center h-12 text-sm font-semibold !bg-orange text-paper hover:!bg-orange/90 shadow-md"
              >
                <span>Start New Assessment</span>
                <ArrowRight className="w-4 h-4 ml-1.5" />
              </Button>

              <Link to="/directory" className="flex-1 min-w-[160px]">
                <Button
                  variant="secondary"
                  className="w-full justify-center h-12 text-sm font-semibold"
                >
                  <Compass className="w-4 h-4 mr-1.5" />
                  <span>Public Directory</span>
                </Button>
              </Link>
            </div>
          </Card>

          {/* AI Coach Summary for Most Recent Attempt */}
          {activeAttempt?.coaching?.summary && (
            <Card className="p-5 bg-orange/5 border border-orange/30 shadow-sm space-y-3.5">
              <div className="flex items-center justify-between border-b border-orange/15 pb-2.5">
                <div className="flex items-center gap-2">
                  <div className="w-7 h-7 rounded-full bg-orange/15 flex items-center justify-center text-orange border border-orange/30">
                    <Lightbulb className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="font-heading font-bold text-sm text-ink">
                      AI Coach: Recent Attempt Feedback
                    </h3>
                    <p className="font-sans text-[11px] text-ink/60">
                      {(activeAttempt.skill_id || 'Trade Assessment').replace(/_/g, ' ').toUpperCase()}
                    </p>
                  </div>
                </div>
                <Tag variant="accent" className="text-[9px] py-0 px-2">
                  Active Feedback
                </Tag>
              </div>

              <div className="p-3 bg-white/80 rounded-xl border border-orange/15 text-xs text-ink/80 font-sans leading-relaxed">
                <p className="font-semibold text-ink mb-1 text-[11px] uppercase font-mono tracking-wider text-orange">
                  Summary:
                </p>
                <p>{activeAttempt.coaching.summary}</p>
              </div>

              {activeAttempt.coaching.next_actions && activeAttempt.coaching.next_actions.length > 0 && (
                <div className="space-y-1.5 pt-1">
                  <span className="font-mono text-[11px] font-bold text-ink/70 uppercase tracking-wider flex items-center gap-1.5">
                    <Target className="w-3.5 h-3.5 text-orange" />
                    Recommended Next Actions:
                  </span>
                  <div className="space-y-1">
                    {activeAttempt.coaching.next_actions.map((act: string, idx: number) => (
                      <div
                        key={idx}
                        className="flex items-start gap-2 text-xs text-ink/80 bg-white/70 p-2 rounded-lg border border-orange/10"
                      >
                        <span className="w-3.5 h-3.5 rounded-full bg-orange/15 text-orange font-mono text-[9px] font-bold flex items-center justify-center shrink-0 mt-0.5">
                          {idx + 1}
                        </span>
                        <span className="font-sans leading-tight">{act}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </Card>
          )}

          {/* Skill Ladder Progress (PRD Section 4 & 6) */}
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <Award className="w-4 h-4 text-orange" />
                <h2 className="font-heading font-bold text-base text-ink">
                  Skill Ladder Progression
                </h2>
              </div>
              <span className="text-xs font-mono font-bold text-orange">
                Current: Tier {currentTier} (Witnessed)
              </span>
            </div>

            <Card className="p-5 bg-white border border-ink/15 shadow-sm space-y-4">
              <div className="space-y-3">
                {ladderSteps.map((step) => {
                  const isCurrent = step.current
                  const isDone = step.done && !isCurrent

                  return (
                    <div
                      key={step.tier}
                      className={`p-3 rounded-xl border transition-all ${
                        isCurrent
                          ? 'border-orange bg-orange/5 ring-1 ring-orange'
                          : isDone
                          ? 'border-ink/10 bg-ink/[0.02]'
                          : 'border-dashed border-ink/15 bg-paper/50 opacity-70'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2.5">
                          <span
                            className={`w-6 h-6 rounded-full flex items-center justify-center font-mono text-xs font-bold ${
                              isCurrent
                                ? 'bg-orange text-paper'
                                : isDone
                                ? 'bg-green-600 text-paper'
                                : 'bg-ink/10 text-ink/60'
                            }`}
                          >
                            {isDone ? (
                              <CheckCircle2 className="w-3.5 h-3.5" />
                            ) : (
                              step.tier
                            )}
                          </span>

                          <div>
                            <span className="font-heading font-bold text-sm text-ink block">
                              Tier {step.tier}: {step.title}
                            </span>
                            <span className="font-sans text-xs text-ink/60 block">
                              {step.desc}
                            </span>
                          </div>
                        </div>

                        {isCurrent && (
                          <span className="text-[10px] font-mono font-bold text-orange uppercase bg-orange/15 px-2 py-0.5 rounded border border-orange/30 shrink-0">
                            Current Level
                          </span>
                        )}
                      </div>
                    </div>
                  )
                })}
              </div>

              {/* Coaching Guidance Box */}
              <div className="p-3.5 rounded-xl bg-orange/10 border border-orange/20 flex items-start gap-2.5 text-xs text-ink/80">
                <Lightbulb className="w-4 h-4 text-orange shrink-0 mt-0.5" />
                <div className="space-y-0.5">
                  <p className="font-bold text-ink">
                    Skill Ladder Coaching: How to reach Tier 3 (Trusted)
                  </p>
                  <p className="text-ink/70 leading-relaxed text-[11px]">
                    You already have verified practical demonstration and peer vouches.
                    To unlock Tier 3, invite 1 Master Trainer or Contractor to review your 20-second video clip.
                  </p>
                </div>
              </div>
            </Card>
          </div>

          {/* Recent Skill Assessments */}
          <div className="space-y-3">
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                <Briefcase className="w-4 h-4 text-orange" />
                <h2 className="font-heading font-bold text-base text-ink">
                  Recent Assessments
                </h2>
              </div>
              <span className="text-xs font-mono text-ink/50">2 Total</span>
            </div>

            <div className="space-y-2.5">
              {recentAttempts.map((att) => (
                <Card
                  key={att.id}
                  className="p-4 bg-white border border-ink/15 shadow-sm space-y-2.5"
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-heading font-bold text-sm text-ink">
                        {att.skill}
                      </h3>
                      <div className="flex items-center gap-2 text-xs text-ink/60 font-sans mt-0.5">
                        <span className="text-orange font-semibold">{att.trade}</span>
                        <span>•</span>
                        <span className="flex items-center gap-1 font-mono text-[11px]">
                          <Clock className="w-3 h-3" />
                          {att.date}
                        </span>
                      </div>
                    </div>

                    <div className="text-right">
                      <span className="font-mono font-bold text-sm text-orange block">
                        {att.score}/100
                      </span>
                      <span className="text-[10px] font-mono text-green-700 font-semibold uppercase flex items-center gap-1">
                        <ShieldCheck className="w-3 h-3" />
                        {att.status}
                      </span>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          </div>

          {/* Privacy & Data Ownership (Delete My Data) */}
          <div className="pt-4 border-t border-ink/10 flex flex-col sm:flex-row items-center justify-between gap-3 bg-red-50/50 p-4 rounded-xl border border-red-200">
            <div className="text-left">
              <p className="text-xs font-bold text-ink">Worker Privacy & Data Sovereignty</p>
              <p className="text-[11px] text-ink/70">
                You own your verification records. Permanently erase all demonstration videos and revoke your credential anytime.
              </p>
            </div>
            <Button
              variant="danger"
              onClick={handleDeleteData}
              disabled={deleting}
              className="text-xs px-4 py-2 shrink-0 bg-red-600 hover:bg-red-700 text-paper font-semibold shadow-sm"
            >
              <Trash2 className="w-3.5 h-3.5 mr-1.5" />
              <span>{deleting ? 'Erasing Data...' : 'Delete My Data'}</span>
            </Button>
          </div>
        </main>

        <footer className="pt-4 border-t border-ink/10 flex items-center justify-between text-xs">
          <Link to="/" className="text-ink/60 hover:text-ink font-mono">
            ← SAKSHI Home
          </Link>
          <span className="text-ink/40 font-mono text-[11px]">
            SAKSHI Micro-Credentialing Protocol v0.1
          </span>
        </footer>
      </div>
    </PageTransition>
  )
}
