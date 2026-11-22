import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import {
  Copy,
  Check,
  Share2,
  ShieldCheck,
  ArrowRight,
  AlertCircle,
  Loader2,
  CheckCircle2,
} from 'lucide-react'
import PageTransition from '../components/PageTransition'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Tag } from '../components/ui/Tag'
import { Skeleton } from '../components/ui/Skeleton'
import { fetchApi } from '../api/client'
import type { WitnessInvite, CredentialResponse } from '../api/types'

export default function Witnesses() {
  const { attemptId } = useParams<{ attemptId: string }>()
  const navigate = useNavigate()

  const [invites, setInvites] = useState<WitnessInvite[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null)
  const [isFinalizing, setIsFinalizing] = useState(false)

  // Fetch or generate 3 witness invite links
  useEffect(() => {
    if (!attemptId) return

    let isMounted = true

    async function loadInvites() {
      try {
        setLoading(true)
        setError(null)
        const res = await fetchApi<WitnessInvite[]>(
          `/api/attempts/${attemptId}/witnesses`,
          {
            method: 'POST',
            body: JSON.stringify({ count: 3 }),
          }
        )
        if (isMounted && res.data) {
          setInvites(res.data)
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to generate witness invites.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadInvites()

    return () => {
      isMounted = false
    }
  }, [attemptId])

  const handleCopy = (url: string, index: number) => {
    navigator.clipboard.writeText(url)
    setCopiedIndex(index)
    setTimeout(() => {
      setCopiedIndex(null)
    }, 2500)
  }

  const handleShareWhatsApp = (url: string) => {
    const text = encodeURIComponent(
      `Hello! Please vouch for my practical skill assessment on SAKSHI: ${url}`
    )
    window.open(`https://wa.me/?text=${text}`, '_blank', 'noopener,noreferrer')
  }

  const handleFinalize = async () => {
    if (!attemptId || isFinalizing) return

    try {
      setIsFinalizing(true)
      setError(null)
      const res = await fetchApi<CredentialResponse>(
        `/api/attempts/${attemptId}/finalize`,
        { method: 'POST' }
      )
      if (res.data?.credential_id) {
        navigate(`/credential/${res.data.credential_id}`)
      } else {
        throw new Error('Credential issued without valid ID.')
      }
    } catch (err: any) {
      setError(err.message || 'Failed to finalize assessment.')
      setIsFinalizing(false)
    }
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
              <Tag variant="accent">Witness Network</Tag>
            </div>
            <div className="font-mono text-xs text-ink/60 uppercase">
              Phase 3 of 3
            </div>
          </div>
        </header>

        <main className="space-y-6">
          {/* Headline & Explanation */}
          <div className="space-y-2">
            <h1 className="font-heading font-black text-2xl md:text-3xl text-ink">
              Invite Skill Witnesses
            </h1>
            <p className="font-sans text-sm text-ink/70 leading-relaxed">
              Share one-time links with trainers, employers, or fellow craftspeople who have seen you work.
              Their vouches add cryptographic weight and unlock higher credential tiers.
            </p>
          </div>

          {/* Tier Milestones Guidance Card */}
          <Card className="p-4 bg-orange/5 border border-orange/20 space-y-3">
            <div className="flex items-center gap-2 text-orange font-bold text-sm">
              <ShieldCheck className="w-5 h-5 shrink-0" />
              <span>Trust Graph Weight Rules</span>
            </div>
            <div className="grid grid-cols-2 gap-2 text-xs font-mono text-ink/80 pt-1">
              <div className="p-2 rounded bg-paper/60 border border-orange/15">
                <span className="font-bold text-orange block">Tier 2: Witnessed</span>
                <span>Requires total weight ≥ 1.0 (e.g. 1 peer vouch)</span>
              </div>
              <div className="p-2 rounded bg-paper/60 border border-orange/15">
                <span className="font-bold text-orange block">Tier 3: Trusted</span>
                <span>Requires weight ≥ 3.0 + Trainer/Employer vouch</span>
              </div>
            </div>
          </Card>

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-bold">Notice</p>
                <p className="text-xs text-red-600 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Loading Skeleton */}
          {loading && (
            <div className="space-y-4">
              <Skeleton className="h-28 w-full rounded-2xl" />
              <Skeleton className="h-28 w-full rounded-2xl" />
              <Skeleton className="h-28 w-full rounded-2xl" />
            </div>
          )}

          {/* Invite Links List */}
          {!loading && invites.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-ink/60 uppercase px-1">
                <span>Single-Use Verification Links</span>
                <span>{invites.length} Available</span>
              </div>

              {invites.map((invite, index) => {
                const isCopied = copiedIndex === index
                const suggestedRole =
                  index === 0
                    ? 'Recommended: Senior Trainer or Master Craftsman'
                    : index === 1
                    ? 'Recommended: Contractor or Employer'
                    : 'Recommended: Peer Tradesperson'

                return (
                  <Card
                    key={invite.token}
                    className="p-4 bg-paper border border-ink/10 shadow-sm space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-ink/5 border border-ink/15 text-ink font-mono text-xs font-bold flex items-center justify-center">
                          {index + 1}
                        </span>
                        <span className="font-mono text-xs font-semibold text-ink">
                          Invite #{index + 1}
                        </span>
                      </div>
                      <span className="text-[11px] font-sans text-orange font-medium">
                        {suggestedRole}
                      </span>
                    </div>

                    <div className="p-2.5 rounded-lg bg-ink/5 border border-ink/10 font-mono text-xs text-ink/80 truncate select-all">
                      {invite.url}
                    </div>

                    <div className="flex items-center gap-2 pt-1">
                      <Button
                        variant="secondary"
                        onClick={() => handleCopy(invite.url, index)}
                        className="flex-1 justify-center h-10 text-xs font-semibold"
                      >
                        {isCopied ? (
                          <>
                            <Check className="w-4 h-4 mr-1 text-green-600" />
                            <span className="text-green-600">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="w-4 h-4 mr-1 text-ink/70" />
                            <span>Copy Link</span>
                          </>
                        )}
                      </Button>

                      <Button
                        variant="secondary"
                        onClick={() => handleShareWhatsApp(invite.url)}
                        className="flex-1 justify-center h-10 text-xs font-semibold !bg-[#25D366]/10 !text-[#128C7E] !border-[#25D366]/30 hover:!bg-[#25D366]/20"
                      >
                        <Share2 className="w-4 h-4 mr-1" />
                        <span>WhatsApp</span>
                      </Button>
                    </div>
                  </Card>
                )
              })}
            </div>
          )}
        </main>

        {/* Footer Actions */}
        <footer className="pt-4 border-t border-ink/10 space-y-3">
          <div className="flex items-center gap-2 text-xs text-ink/60 px-1">
            <CheckCircle2 className="w-4 h-4 text-orange shrink-0" />
            <span>
              You can issue your credential now. Additional vouches received later will update your trust score automatically.
            </span>
          </div>

          <Button
            variant="primary"
            onClick={handleFinalize}
            disabled={isFinalizing || loading}
            className="w-full justify-center h-14 text-base font-semibold !bg-orange text-paper hover:!bg-orange/90 shadow-lg"
          >
            {isFinalizing ? (
              <>
                <Loader2 className="w-5 h-5 mr-2 animate-spin" />
                <span>Computing Tiers & Signing Credential...</span>
              </>
            ) : (
              <>
                <span>Finalize & Get Digital Credential</span>
                <ArrowRight className="w-5 h-5 ml-2" />
              </>
            )}
          </Button>
        </footer>
      </div>
    </PageTransition>
  )
}
