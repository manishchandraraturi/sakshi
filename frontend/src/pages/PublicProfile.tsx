import { useEffect, useState, useMemo } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Download,
  AlertCircle,
  Copy,
  Check,
  Calendar,
  MapPin,
  FileCode,
  Bug,
  RotateCcw,
} from 'lucide-react'
import PageTransition from '../components/PageTransition'
import Seal from '../components/Seal'
import VerifyBanner from '../components/VerifyBanner'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Tag } from '../components/ui/Tag'
import { Skeleton } from '../components/ui/Skeleton'
import { fetchApi } from '../api/client'
import { verifyCredential } from '../utils/verify'

interface CredentialDetail {
  credential_id: string
  attempt_id: string
  worker_id: string
  skill_id: string
  tier: number
  trust_score: number
  payload: {
    cred_id: string
    worker_name: string
    area: string
    trade: string
    skill: string
    tier: number
    trust_score: number
    issued_at: string
    valid_until?: string
    evidence_sha256: string
    witness_count: number
    [key: string]: any
  }
  signature: string
  pubkey: string
  issued_at: string
  revoked: boolean
}

export default function PublicProfile() {
  const { id } = useParams<{ id: string }>()

  const [cred, setCred] = useState<CredentialDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  // Live Demo Tamper Toggle
  const [isTampered, setIsTampered] = useState(false)

  useEffect(() => {
    if (!id) return

    let isMounted = true

    async function loadCredential() {
      try {
        setLoading(true)
        setError(null)
        const res = await fetchApi<CredentialDetail>(`/api/credentials/${id}`)
        if (isMounted && res.data) {
          setCred(res.data)
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Unable to load public credential.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadCredential()

    return () => {
      isMounted = false
    }
  }, [id])

  // Active payload (either genuine or tampered with by 1 character for demo)
  const activePayload = useMemo(() => {
    if (!cred?.payload) return null
    if (!isTampered) return cred.payload

    // Tamper with data: alter 1 letter of the candidate's name
    const originalName = cred.payload.worker_name || 'Worker'
    const tamperedName =
      originalName.length > 2
        ? originalName.slice(0, 1) + 'X' + originalName.slice(2)
        : originalName + 'X'

    return {
      ...cred.payload,
      worker_name: tamperedName,
    }
  }, [cred, isTampered])

  // In-browser verification execution via tweetnacl
  const isSignatureValid = useMemo(() => {
    if (!activePayload || !cred?.signature || !cred?.pubkey) {
      return false
    }
    return verifyCredential(activePayload, cred.signature, cred.pubkey)
  }, [activePayload, cred])

  const copyCredId = () => {
    if (!id) return
    navigator.clipboard.writeText(id)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const tierNames: Record<number, string> = {
    0: 'Needs Retry',
    1: 'Demonstrated',
    2: 'Witnessed',
    3: 'Trusted',
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
              <Tag variant="accent">Public Profile</Tag>
            </div>
            <div className="font-mono text-xs text-ink/60 uppercase">
              Hirer Verification
            </div>
          </div>
        </header>

        <main className="space-y-6">
          {error && (
            <Card className="p-6 text-center space-y-3 bg-white border border-red-200">
              <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
              <h2 className="font-heading font-bold text-lg text-ink">
                Credential Not Found
              </h2>
              <p className="text-xs text-ink/60">{error}</p>
            </Card>
          )}

          {loading && (
            <div className="space-y-4">
              <Skeleton className="h-16 w-full rounded-2xl" />
              <Skeleton className="h-64 w-full rounded-2xl" />
              <Skeleton className="h-32 w-full rounded-2xl" />
            </div>
          )}

          {!loading && cred && activePayload && (
            <>
              {/* 1. In-Browser Verification Banner */}
              <VerifyBanner isValid={isSignatureValid} />

              {/* 2. Interactive Live Tamper Demo Controls */}
              <Card className="p-3.5 bg-ink/5 border border-ink/10 flex items-center justify-between gap-3">
                <div className="flex items-center gap-2 text-xs">
                  <Bug className="w-4 h-4 text-orange shrink-0" />
                  <span className="font-mono text-ink/80 text-[11px]">
                    {isTampered ? (
                      <span className="text-red-600 font-bold">
                        Tamper Active: Name modified to "{activePayload.worker_name}"
                      </span>
                    ) : (
                      <span>Tamper Demo: Test client-side Ed25519 verification</span>
                    )}
                  </span>
                </div>

                <Button
                  variant={isTampered ? 'primary' : 'secondary'}
                  onClick={() => setIsTampered(!isTampered)}
                  className={`h-8 px-3 text-xs font-semibold whitespace-nowrap shrink-0 ${
                    isTampered
                      ? '!bg-ink text-paper'
                      : '!bg-orange/10 !text-orange !border-orange/30 hover:!bg-orange/20'
                  }`}
                >
                  {isTampered ? (
                    <>
                      <RotateCcw className="w-3.5 h-3.5 mr-1" />
                      <span>Restore Clean</span>
                    </>
                  ) : (
                    <>
                      <Bug className="w-3.5 h-3.5 mr-1" />
                      <span>Tamper with Data</span>
                    </>
                  )}
                </Button>
              </Card>

              {/* 3. Hero Credential Card with Animated Seal */}
              <Card className="p-6 bg-white border border-ink/15 shadow-md space-y-6 relative overflow-hidden">
                <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5">
                  {/* Drawing Seal Badge */}
                  <div className="shrink-0">
                    <Seal tier={cred.tier} size={128} />
                  </div>

                  <div className="space-y-1.5 text-center sm:text-left flex-1 min-w-0">
                    <div className="flex items-center justify-center sm:justify-start gap-2">
                      <span className="text-[11px] font-mono text-ink/50 uppercase tracking-wider">
                        Verified Tradesperson
                      </span>
                      {isTampered && (
                        <span className="text-[10px] font-mono font-bold bg-red-100 text-red-700 px-1.5 py-0.5 rounded">
                          MODIFIED
                        </span>
                      )}
                    </div>

                    <h1 className="font-heading font-black text-2xl text-ink truncate">
                      {activePayload.worker_name}
                    </h1>

                    <div className="flex items-center justify-center sm:justify-start gap-1.5 text-xs text-orange font-semibold font-sans">
                      <span>{activePayload.trade}</span>
                      <span>•</span>
                      <span>{activePayload.skill}</span>
                    </div>

                    <div className="flex items-center justify-center sm:justify-start gap-1 text-xs text-ink/60 font-sans">
                      <MapPin className="w-3.5 h-3.5 text-ink/40" />
                      <span>{activePayload.area}</span>
                    </div>
                  </div>
                </div>

                {/* Score & Tier Breakdown Grid */}
                <div className="grid grid-cols-2 gap-3 pt-2">
                  <div className="p-3 rounded-xl bg-ink/5 border border-ink/10">
                    <span className="text-[11px] font-mono text-ink/50 uppercase block">
                      Verification Tier
                    </span>
                    <span className="font-heading font-black text-lg text-ink block mt-0.5">
                      Tier {cred.tier}: {tierNames[cred.tier]}
                    </span>
                    <span className="text-[10px] text-ink/60 font-mono">
                      {activePayload.witness_count} peer vouches
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-ink/5 border border-ink/10">
                    <span className="text-[11px] font-mono text-ink/50 uppercase block">
                      Trust Score
                    </span>
                    <span className="font-heading font-black text-lg text-orange block mt-0.5">
                      {Math.round(cred.trust_score)} / 100
                    </span>
                    <span className="text-[10px] text-ink/60 font-mono">
                      Deterministic proof
                    </span>
                  </div>
                </div>

                {/* N2 Credential Freshness & Validity Date */}
                {activePayload.valid_until && (
                  <div className="p-3 rounded-xl bg-orange/5 border border-orange/20 flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1.5 text-ink/80 font-mono">
                      <Calendar className="w-4 h-4 text-orange shrink-0" />
                      <span>Valid until:</span>
                    </div>
                    <span className="font-mono font-bold text-orange">
                      {new Date(activePayload.valid_until).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric',
                      })}
                    </span>
                  </div>
                )}

                {/* Cryptographic Proof Details */}
                <div className="space-y-2 pt-2 border-t border-ink/10 font-mono text-xs">
                  <div className="flex items-center justify-between text-[11px] text-ink/50">
                    <span className="flex items-center gap-1">
                      <FileCode className="w-3.5 h-3.5" />
                      Evidence SHA-256
                    </span>
                    <span className="truncate max-w-[200px] select-all">
                      {activePayload.evidence_sha256}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-ink/50">
                    <span>Ed25519 Pubkey</span>
                    <span className="truncate max-w-[200px] select-all">
                      {cred.pubkey}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-[11px] text-ink/50">
                    <span>Signature</span>
                    <span className="truncate max-w-[200px] select-all">
                      {cred.signature.slice(0, 32)}...
                    </span>
                  </div>
                </div>
              </Card>

              {/* Action Buttons: Download Card & Share */}
              <div className="space-y-3">
                <a
                  href={`/api/credentials/${cred.credential_id}/card.png`}
                  download={`sakshi_credential_${cred.credential_id.slice(0, 8)}.png`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <Button
                    variant="primary"
                    className="w-full justify-center h-14 text-base font-semibold !bg-orange text-paper hover:!bg-orange/90 shadow-lg"
                  >
                    <Download className="w-5 h-5 mr-2" />
                    <span>Download WhatsApp Share Card (PNG)</span>
                  </Button>
                </a>

                <div className="flex items-center justify-between px-1">
                  <button
                    onClick={copyCredId}
                    className="flex items-center gap-1 text-xs font-mono text-ink/50 hover:text-ink"
                  >
                    {copied ? (
                      <Check className="w-3.5 h-3.5 text-green-600" />
                    ) : (
                      <Copy className="w-3.5 h-3.5" />
                    )}
                    <span>Copy ID: {cred.credential_id.slice(0, 8)}...</span>
                  </button>

                  <Link to="/" className="text-xs text-orange font-semibold hover:underline">
                    SAKSHI Protocol Home →
                  </Link>
                </div>
              </div>
            </>
          )}
        </main>
      </div>
    </PageTransition>
  )
}
