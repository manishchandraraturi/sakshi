import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import {
  Award,
  ShieldCheck,
  CheckCircle2,
  Clock,
  MapPin,
  AlertCircle,
  Copy,
  Check,
  FileText,
} from 'lucide-react'
import PageTransition from '../components/PageTransition'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Tag } from '../components/ui/Tag'
import { Skeleton } from '../components/ui/Skeleton'
import { fetchApi } from '../api/client'

interface CredentialData {
  credential_id: string;
  attempt_id: string;
  worker_id: string;
  skill_id: string;
  tier: number;
  trust_score: number;
  payload: {
    cred_id: string;
    worker_name: string;
    area: string;
    trade: string;
    skill: string;
    tier: number;
    trust_score: number;
    issued_at: string;
    evidence_sha256: string;
    witness_count: number;
  };
  signature: string;
  pubkey: string;
  issued_at: string;
  revoked: boolean;
}

export default function Credential() {
  const { id } = useParams<{ id: string }>()

  const [cred, setCred] = useState<CredentialData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!id) return

    let isMounted = true

    async function loadCredential() {
      try {
        setLoading(true)
        setError(null)
        const res = await fetchApi<CredentialData>(`/api/credentials/${id}`)
        if (isMounted && res.data) {
          setCred(res.data)
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Credential not found.')
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
              <Tag variant="accent">Digital Credential</Tag>
            </div>
            <div className="font-mono text-xs text-green-700 bg-green-50 px-2 py-0.5 rounded border border-green-200 font-semibold flex items-center gap-1">
              <ShieldCheck className="w-3.5 h-3.5" />
              Ed25519 Signed
            </div>
          </div>
        </header>

        <main className="space-y-6">
          {error && (
            <Card className="p-6 text-center space-y-3 bg-white border border-red-200">
              <AlertCircle className="w-8 h-8 text-red-600 mx-auto" />
              <h2 className="font-heading font-bold text-lg text-ink">
                Error Loading Credential
              </h2>
              <p className="text-xs text-ink/60">{error}</p>
            </Card>
          )}

          {loading && (
            <div className="space-y-4">
              <Skeleton className="h-64 w-full rounded-2xl" />
              <Skeleton className="h-32 w-full rounded-2xl" />
            </div>
          )}

          {!loading && cred && (
            <>
              {/* Issued Celebration Banner */}
              <div className="text-center space-y-2">
                <div className="w-14 h-14 rounded-full bg-orange/10 border border-orange/30 text-orange flex items-center justify-center mx-auto">
                  <Award className="w-8 h-8" />
                </div>
                <h1 className="font-heading font-black text-2xl md:text-3xl text-ink">
                  Credential Issued!
                </h1>
                <p className="font-sans text-xs md:text-sm text-ink/60">
                  Cryptographically anchored, tamper-proof proof of vocational skill.
                </p>
              </div>

              {/* Main Credential Card */}
              <Card className="p-6 bg-white border border-ink/15 shadow-md space-y-5 relative overflow-hidden">
                <div className="absolute top-0 right-0 w-32 h-32 bg-orange/5 rounded-bl-full pointer-events-none" />

                <div className="flex items-start justify-between">
                  <div>
                    <span className="text-[11px] font-mono text-ink/50 uppercase tracking-wider block">
                      Tradesperson
                    </span>
                    <h2 className="font-heading font-bold text-xl text-ink">
                      {cred.payload.worker_name}
                    </h2>
                    <div className="flex items-center gap-1 text-xs text-ink/60 font-sans mt-0.5">
                      <MapPin className="w-3.5 h-3.5 text-orange" />
                      <span>{cred.payload.area}</span>
                    </div>
                  </div>

                  <div className="text-right">
                    <span className="text-[11px] font-mono text-ink/50 uppercase tracking-wider block">
                      Verified Tier
                    </span>
                    <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-orange text-paper font-heading font-bold text-sm shadow-sm mt-1">
                      <ShieldCheck className="w-4 h-4" />
                      <span>Tier {cred.tier}: {tierNames[cred.tier] || 'Verified'}</span>
                    </div>
                  </div>
                </div>

                <div className="p-4 rounded-xl bg-ink/5 border border-ink/10 space-y-2">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-ink/60 font-mono">Assessed Skill:</span>
                    <span className="font-bold text-ink">{cred.payload.skill}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-ink/60 font-mono">Trade:</span>
                    <span className="font-semibold text-ink">{cred.payload.trade}</span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-ink/60 font-mono">Trust Score:</span>
                    <span className="font-mono font-bold text-orange text-sm">
                      {Math.round(cred.trust_score)} / 100
                    </span>
                  </div>
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-ink/60 font-mono">Witness Vouches:</span>
                    <span className="font-semibold text-ink">{cred.payload.witness_count} recorded</span>
                  </div>
                </div>

                {/* Cryptographic Signature Snippet */}
                <div className="space-y-1.5 font-mono text-[11px]">
                  <div className="flex justify-between text-ink/50">
                    <span>Ed25519 Signature</span>
                    <span className="text-green-700 font-semibold flex items-center gap-1">
                      <CheckCircle2 className="w-3 h-3" />
                      Valid
                    </span>
                  </div>
                  <div className="p-2 rounded bg-ink/5 border border-ink/10 text-ink/70 break-all select-all font-mono text-[10px]">
                    {cred.signature.slice(0, 48)}...
                  </div>
                </div>

                <div className="pt-2 border-t border-ink/10 flex items-center justify-between text-xs text-ink/50 font-mono">
                  <button
                    onClick={copyCredId}
                    className="flex items-center gap-1 hover:text-ink text-left"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-green-600" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>ID: {cred.credential_id.slice(0, 8)}...</span>
                  </button>
                  <div className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>{new Date(cred.issued_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </Card>

              {/* Actions: View Public Profile & Download Share Card */}
              <div className="space-y-3 pt-2">
                <Link to={`/c/${cred.credential_id}`} className="block">
                  <Button
                    variant="primary"
                    className="w-full justify-center h-14 text-base font-semibold !bg-orange text-paper hover:!bg-orange/90 shadow-lg"
                  >
                    <ShieldCheck className="w-5 h-5 mr-2" />
                    <span>View Public Profile & Verify Signature</span>
                  </Button>
                </Link>

                <a
                  href={`/api/credentials/${cred.credential_id}/card.png`}
                  download={`sakshi_card_${cred.credential_id.slice(0, 8)}.png`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <Button
                    variant="secondary"
                    className="w-full justify-center h-12 text-sm font-semibold !bg-ink/5 hover:!bg-ink/10"
                  >
                    <span>Download WhatsApp Share Card (PNG)</span>
                  </Button>
                </a>

                <a
                  href={`/api/credentials/${cred.credential_id}/pdf`}
                  download={`credential_${cred.credential_id}.pdf`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  <Button
                    variant="secondary"
                    className="w-full justify-center h-12 text-sm font-semibold !bg-ink/5 hover:!bg-ink/10 border border-ink/15 text-ink"
                  >
                    <FileText className="w-4 h-4 mr-2 text-orange" />
                    <span>Download PDF Certificate</span>
                  </Button>
                </a>
              </div>
            </>
          )}
        </main>

        <footer className="pt-4 border-t border-ink/10">
          <Link to="/">
            <Button variant="secondary" className="w-full justify-center h-11 text-xs font-semibold">
              Return to Sakshi Home
            </Button>
          </Link>
        </footer>
      </div>
    </PageTransition>
  )
}
