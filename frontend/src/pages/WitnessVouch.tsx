import { useEffect, useState, type FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import {
  Play,
  CheckCircle2,
  AlertCircle,
  Loader2,
  ShieldCheck,
  UserCheck,
  Eye,
  Briefcase,
  Clock,
  Sparkles,
} from 'lucide-react'
import PageTransition from '../components/PageTransition'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Tag } from '../components/ui/Tag'
import { Skeleton } from '../components/ui/Skeleton'
import { fetchApi } from '../api/client'
import type { WitnessPageData, VouchResponse } from '../api/types'

export default function WitnessVouch() {
  const { token } = useParams<{ token: string }>()

  const [pageData, setPageData] = useState<WitnessPageData | null>(null)
  const [loading, setLoading] = useState(true)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [submittedVouch, setSubmittedVouch] = useState<VouchResponse | null>(null)

  // Form State
  const [witnessName, setWitnessName] = useState('')
  const [role, setRole] = useState<'peer' | 'trainer' | 'employer' | 'customer'>('peer')
  const [instituteCode, setInstituteCode] = useState('')
  const [seenInPerson, setSeenInPerson] = useState(true)
  const [knownYears, setKnownYears] = useState('1-3')
  const [wouldHire, setWouldHire] = useState(true)
  const [verdict, setVerdict] = useState<'yes' | 'needs_work'>('yes')
  const [isPlaying, setIsPlaying] = useState(false)

  // Fetch witness review page data
  useEffect(() => {
    if (!token) return

    let isMounted = true

    async function loadData() {
      try {
        setLoading(true)
        setError(null)
        const res = await fetchApi<WitnessPageData>(`/api/w/${token}`)
        if (isMounted && res.data) {
          setPageData(res.data)
        }
      } catch (err: any) {
        if (isMounted) {
          setError(
            err.code === 'INVITE_ALREADY_USED'
              ? 'This witness link has already been used to record a vouch.'
              : err.message || 'Verification link is invalid or expired.'
          )
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadData()

    return () => {
      isMounted = false
    }
  }, [token])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!token || submitting) return

    try {
      setSubmitting(true)
      setError(null)

      // Generate a client device fingerprint for anti-collusion
      const clientDeviceFp = `fp_browser_${window.navigator.userAgent.replace(/\s+/g, '').slice(0, 16)}`

      const res = await fetchApi<VouchResponse>(`/api/w/${token}/vouch`, {
        method: 'POST',
        body: JSON.stringify({
          witness_name: witnessName.trim() || 'Anonymous Witness',
          role,
          institute_code: instituteCode.trim() || undefined,
          seen_in_person: seenInPerson,
          known_years_bucket: knownYears,
          would_hire: wouldHire,
          verdict,
          device_fp: clientDeviceFp,
        }),
      })

      if (res.data) {
        setSubmittedVouch(res.data)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to submit vouch.')
    } finally {
      setSubmitting(false)
    }
  }

  // --- Success State ---
  if (submittedVouch) {
    return (
      <PageTransition>
        <div className="min-h-screen bg-paper flex flex-col justify-center items-center max-w-md mx-auto px-4 py-8">
          <Card className="p-8 text-center space-y-5 bg-white border border-ink/10 shadow-lg w-full">
            <div className="w-16 h-16 rounded-full bg-green-50 border border-green-200 text-green-600 flex items-center justify-center mx-auto">
              <CheckCircle2 className="w-8 h-8" />
            </div>

            <div className="space-y-2">
              <h1 className="font-heading font-black text-2xl text-ink">
                Vouch Recorded!
              </h1>
              <p className="font-sans text-sm text-ink/70">
                Thank you for witnessing {pageData?.worker_first_name || 'the candidate'}'s work.
                Your vouch has been cryptographically attached to their credential.
              </p>
            </div>

            <div className="p-4 rounded-xl bg-ink/5 border border-ink/10 font-mono text-xs text-ink/80 space-y-1 text-left">
              <div className="flex justify-between">
                <span>Vouch ID:</span>
                <span className="font-bold">{submittedVouch.vouch_id.slice(0, 8)}...</span>
              </div>
              <div className="flex justify-between">
                <span>Calculated Weight:</span>
                <span className="font-bold text-orange">{submittedVouch.weight.toFixed(2)}x</span>
              </div>
              <div className="flex justify-between">
                <span>Status:</span>
                <span className="font-bold text-green-700 capitalize">{submittedVouch.status}</span>
              </div>
            </div>

            <p className="text-[11px] text-ink/40 font-mono">
              You may now close this page.
            </p>
          </Card>
        </div>
      </PageTransition>
    )
  }

  return (
    <PageTransition>
      <div className="min-h-screen bg-paper flex flex-col justify-between max-w-xl mx-auto px-4 py-4 md:py-8 space-y-6">
        {/* Header */}
        <header className="border-b border-ink/10 pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-heading font-black text-lg text-ink">SAKSHI</span>
              <span className="text-ink/30">•</span>
              <Tag variant="accent">Peer Verification</Tag>
            </div>
            <div className="font-mono text-xs text-ink/60 uppercase">
              No Login Required
            </div>
          </div>
        </header>

        {/* Error / Invalid Token Screen */}
        {error && !pageData && (
          <main className="space-y-6">
            <Card className="p-6 text-center space-y-4 bg-white border border-red-200">
              <div className="w-12 h-12 rounded-full bg-red-50 text-red-600 flex items-center justify-center mx-auto">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <h2 className="font-heading font-bold text-lg text-ink">
                  Unable to Open Verification Link
                </h2>
                <p className="font-sans text-xs text-ink/60">{error}</p>
              </div>
            </Card>
          </main>
        )}

        {/* Loading Screen */}
        {loading && (
          <main className="space-y-4">
            <Skeleton className="h-44 w-full rounded-2xl" />
            <Skeleton className="h-32 w-full rounded-2xl" />
            <Skeleton className="h-40 w-full rounded-2xl" />
          </main>
        )}

        {/* Verification Form */}
        {!loading && pageData && (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Candidate Header */}
            <div className="space-y-1">
              <div className="flex items-center gap-2 text-xs font-mono text-orange uppercase font-semibold">
                <UserCheck className="w-4 h-4" />
                <span>Witness Vouch Request</span>
              </div>
              <h1 className="font-heading font-black text-2xl md:text-3xl text-ink">
                Vouch for {pageData.worker_first_name}
              </h1>
              <p className="font-sans text-xs md:text-sm text-ink/70">
                Skill assessed: <strong className="text-ink">{pageData.skill}</strong>
              </p>
            </div>

            {/* Video Demonstration Player */}
            <Card className="overflow-hidden bg-ink text-paper border-0 shadow-md">
              <div
                className="relative aspect-video bg-neutral-900 flex flex-col items-center justify-center cursor-pointer group"
                onClick={() => setIsPlaying(!isPlaying)}
              >
                <div className="w-14 h-14 rounded-full bg-paper/20 backdrop-blur-sm border border-paper/40 flex items-center justify-center group-hover:scale-110 transition-transform">
                  <Play className="w-6 h-6 text-paper ml-1" />
                </div>
                <div className="absolute bottom-3 left-3 right-3 flex items-center justify-between text-[11px] font-mono text-paper/70">
                  <span>{isPlaying ? 'Demo Clip Playing' : 'Click to Watch Demonstration'}</span>
                  <span className="bg-ink/70 px-2 py-0.5 rounded">0:30 • Verified</span>
                </div>
              </div>
              <div className="p-3 bg-neutral-950 flex items-center justify-between text-xs text-paper/80 font-mono">
                <span className="truncate">{pageData.skill}</span>
                <span className="text-orange flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5" />
                  AI Reviewed
                </span>
              </div>
            </Card>

            {/* Step Checklist Verified */}
            {pageData.steps && pageData.steps.length > 0 && (
              <Card className="p-4 bg-paper border border-ink/10 space-y-3">
                <div className="text-xs font-mono text-ink/60 uppercase font-semibold">
                  Steps Demonstrated on Camera
                </div>
                <ul className="space-y-2">
                  {pageData.steps.map((st, i) => (
                    <li key={st.id || i} className="flex items-start gap-2 text-xs text-ink/80">
                      <CheckCircle2 className="w-4 h-4 text-green-600 shrink-0 mt-0.5" />
                      <span>{st.title}</span>
                    </li>
                  ))}
                </ul>
              </Card>
            )}

            {/* Question 1: Role */}
            <div className="space-y-2">
              <label className="text-xs font-mono font-semibold text-ink uppercase flex items-center gap-1.5">
                <Briefcase className="w-4 h-4 text-orange" />
                1. Your Role / Relationship
              </label>
              <div className="grid grid-cols-2 gap-2">
                {[
                  { id: 'peer', label: 'Peer Tradesperson', sub: 'Fellow Worker (1.0x)' },
                  { id: 'trainer', label: 'Senior Trainer', sub: 'Master Craftsman (1.5x)' },
                  { id: 'employer', label: 'Employer / Contractor', sub: 'Hirer (1.2x)' },
                  { id: 'customer', label: 'Client / Customer', sub: 'Homeowner (0.8x)' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setRole(item.id as any)}
                    className={`p-3 rounded-xl border text-left transition-all ${
                      role === item.id
                        ? 'border-orange bg-orange/10 text-ink shadow-sm ring-1 ring-orange'
                        : 'border-ink/15 bg-paper hover:bg-ink/5 text-ink/70'
                    }`}
                  >
                    <div className="font-bold text-xs">{item.label}</div>
                    <div className="text-[10px] text-ink/50 mt-0.5">{item.sub}</div>
                  </button>
                ))}
              </div>

              {(role === 'trainer' || role === 'employer') && (
                <div className="p-3 bg-white border border-orange/40 rounded-xl space-y-1.5 animate-fadeIn">
                  <label className="text-[11px] font-mono font-semibold text-ink uppercase flex items-center justify-between">
                    <span>Institute / Verification Code</span>
                    <span className="text-[10px] text-ink/40 font-normal">e.g. SAKSHI2026</span>
                  </label>
                  <input
                    type="text"
                    placeholder="Enter code (e.g. SAKSHI2026)"
                    value={instituteCode}
                    onChange={(e) => setInstituteCode(e.target.value)}
                    className="w-full px-3 py-2 bg-paper border border-ink/20 rounded-lg text-xs font-mono focus:outline-none focus:ring-1 focus:ring-orange"
                  />
                  <p className="text-[10px] text-ink/50">
                    Trainer & employer weights require verification code or existing credential; unverified defaults to peer weight.
                  </p>
                </div>
              )}
            </div>

            {/* Question 2: In-Person Observation */}
            <div className="space-y-2">
              <label className="text-xs font-mono font-semibold text-ink uppercase flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-orange" />
                2. Have you seen them do this work in person?
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setSeenInPerson(true)}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    seenInPerson
                      ? 'border-orange bg-orange/10 text-ink font-bold ring-1 ring-orange'
                      : 'border-ink/15 bg-paper text-ink/70'
                  }`}
                >
                  <span className="text-xs">Yes, In Person (Full Weight)</span>
                </button>
                <button
                  type="button"
                  onClick={() => setSeenInPerson(false)}
                  className={`p-3 rounded-xl border text-center transition-all ${
                    !seenInPerson
                      ? 'border-orange bg-orange/10 text-ink font-bold ring-1 ring-orange'
                      : 'border-ink/15 bg-paper text-ink/70'
                  }`}
                >
                  <span className="text-xs">By Reputation Only</span>
                </button>
              </div>
            </div>

            {/* Question 3: Known Duration */}
            <div className="space-y-2">
              <label className="text-xs font-mono font-semibold text-ink uppercase flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-orange" />
                3. How long have you known their work?
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { id: '<1', label: 'Under 1 yr' },
                  { id: '1-3', label: '1 - 3 yrs' },
                  { id: '3+', label: '3+ yrs' },
                ].map((item) => (
                  <button
                    key={item.id}
                    type="button"
                    onClick={() => setKnownYears(item.id)}
                    className={`p-2.5 rounded-xl border text-center text-xs transition-all ${
                      knownYears === item.id
                        ? 'border-orange bg-orange/10 font-bold text-ink ring-1 ring-orange'
                        : 'border-ink/15 bg-paper text-ink/70'
                    }`}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Question 4: Would Hire */}
            <div className="space-y-2">
              <label className="text-xs font-mono font-semibold text-ink uppercase">
                4. Would you hire or recommend them for paid work?
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setWouldHire(true)}
                  className={`p-3 rounded-xl border text-center text-xs transition-all ${
                    wouldHire
                      ? 'border-orange bg-orange/10 font-bold text-ink ring-1 ring-orange'
                      : 'border-ink/15 bg-paper text-ink/70'
                  }`}
                >
                  Yes, Recommend
                </button>
                <button
                  type="button"
                  onClick={() => setWouldHire(false)}
                  className={`p-3 rounded-xl border text-center text-xs transition-all ${
                    !wouldHire
                      ? 'border-orange bg-orange/10 font-bold text-ink ring-1 ring-orange'
                      : 'border-ink/15 bg-paper text-ink/70'
                  }`}
                >
                  Unsure / Neutral
                </button>
              </div>
            </div>

            {/* Question 5: Overall Verdict */}
            <div className="space-y-2">
              <label className="text-xs font-mono font-semibold text-ink uppercase">
                5. Vouch Verdict
              </label>
              <div className="grid grid-cols-2 gap-2">
                <button
                  type="button"
                  onClick={() => setVerdict('yes')}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    verdict === 'yes'
                      ? 'border-green-600 bg-green-50 text-green-900 font-bold ring-1 ring-green-600'
                      : 'border-ink/15 bg-paper text-ink/70'
                  }`}
                >
                  <div className="text-xs font-bold">Looks Good (Vouch)</div>
                  <div className="text-[10px] text-green-700 mt-0.5">Adds verification trust weight</div>
                </button>
                <button
                  type="button"
                  onClick={() => setVerdict('needs_work')}
                  className={`p-3 rounded-xl border text-left transition-all ${
                    verdict === 'needs_work'
                      ? 'border-amber-600 bg-amber-50 text-amber-900 font-bold ring-1 ring-amber-600'
                      : 'border-ink/15 bg-paper text-ink/70'
                  }`}
                >
                  <div className="text-xs font-bold">Needs Work</div>
                  <div className="text-[10px] text-amber-700 mt-0.5">Private feedback to worker</div>
                </button>
              </div>
            </div>

            {/* Optional Witness Name */}
            <div className="space-y-1.5">
              <label className="text-xs font-mono font-semibold text-ink uppercase">
                Your Full Name
              </label>
              <input
                type="text"
                value={witnessName}
                onChange={(e) => setWitnessName(e.target.value)}
                placeholder="e.g. Master Suresh Contractor"
                className="w-full px-3 py-2.5 rounded-xl border border-ink/20 bg-paper text-xs text-ink focus:outline-none focus:border-orange font-sans"
              />
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs">
                {error}
              </div>
            )}

            {/* Submit Vouch Button */}
            <div className="pt-2">
              <Button
                variant="primary"
                type="submit"
                disabled={submitting}
                className="w-full justify-center h-14 text-base font-semibold !bg-orange text-paper hover:!bg-orange/90 shadow-lg"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                    <span>Signing & Recording Vouch...</span>
                  </>
                ) : (
                  <>
                    <ShieldCheck className="w-5 h-5 mr-2" />
                    <span>Confirm & Sign Vouch</span>
                  </>
                )}
              </Button>
            </div>
          </form>
        )}
      </div>
    </PageTransition>
  )
}
