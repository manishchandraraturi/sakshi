import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  MapPin,
  Filter,
  ArrowRight,
  ShieldCheck,
  AlertCircle,
  Briefcase,
  Users,
  QrCode,
  BarChart3,
} from 'lucide-react'
import PageTransition from '../components/PageTransition'
import Seal from '../components/Seal'
import QrScanner from '../components/QrScanner'
import { Button } from '../components/ui/Button'
import { Card } from '../components/ui/Card'
import { Tag } from '../components/ui/Tag'
import { Skeleton } from '../components/ui/Skeleton'
import { fetchApi } from '../api/client'
import type { DirectoryItem } from '../api/types'

export default function Directory() {
  const navigate = useNavigate()

  const [workers, setWorkers] = useState<DirectoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Filter states
  const [selectedTrade, setSelectedTrade] = useState<string>('')
  const [selectedArea, setSelectedArea] = useState<string>('')
  const [showScanner, setShowScanner] = useState<boolean>(false)

  const handleScan = (scannedData: string) => {
    setShowScanner(false)
    const match = scannedData.match(/\/c\/([a-zA-Z0-9_-]+)/)
    if (match && match[1]) {
      navigate(`/c/${match[1]}`)
    } else if (scannedData.startsWith('http://') || scannedData.startsWith('https://')) {
      try {
        const url = new URL(scannedData)
        if (url.pathname.startsWith('/c/')) {
          navigate(url.pathname)
        } else {
          window.location.href = scannedData
        }
      } catch {
        navigate(`/c/${scannedData}`)
      }
    } else {
      navigate(`/c/${scannedData}`)
    }
  }

  useEffect(() => {
    let isMounted = true

    async function loadDirectory() {
      try {
        setLoading(true)
        setError(null)

        const queryParams = new URLSearchParams()
        if (selectedTrade) queryParams.set('trade', selectedTrade)
        if (selectedArea) queryParams.set('area', selectedArea)

        const queryString = queryParams.toString()
        const endpoint = queryString ? `/api/directory?${queryString}` : '/api/directory'

        const res = await fetchApi<DirectoryItem[]>(endpoint)
        if (isMounted && res.data) {
          setWorkers(res.data)
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.message || 'Failed to load directory.')
        }
      } finally {
        if (isMounted) setLoading(false)
      }
    }

    loadDirectory()

    return () => {
      isMounted = false
    }
  }, [selectedTrade, selectedArea])

  const tierNames: Record<number, string> = {
    0: 'Needs Retry',
    1: 'Demonstrated',
    2: 'Witnessed',
    3: 'Trusted',
  }

  return (
    <PageTransition>
      <div className="min-h-screen bg-paper flex flex-col justify-between max-w-2xl mx-auto px-4 py-4 md:py-8 space-y-6">
        {/* Header */}
        <header className="border-b border-ink/10 pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-heading font-black text-lg text-ink">SAKSHI</span>
              <span className="text-ink/30">•</span>
              <Tag variant="accent">Trades Directory</Tag>
            </div>
            <div className="flex items-center gap-3">
              <Link
                to="/analytics"
                className="text-xs font-mono text-ink/70 hover:text-orange font-semibold flex items-center gap-1 transition-colors"
              >
                <BarChart3 className="w-3.5 h-3.5 text-orange" />
                <span className="hidden sm:inline">Hirer Analytics</span>
              </Link>
              <span className="text-ink/20 hidden sm:inline">|</span>
              <Link
                to="/dashboard"
                className="text-xs font-mono text-orange hover:underline font-semibold"
              >
                Worker Dashboard →
              </Link>
            </div>
          </div>
        </header>

        <main className="space-y-6">
          {/* Title & Introduction */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="space-y-1.5">
              <h1 className="font-heading font-black text-2xl md:text-3xl text-ink">
                Verified Tradespeople
              </h1>
              <p className="font-sans text-xs md:text-sm text-ink/70">
                Browse skilled craftspeople with Ed25519 tamper-proof credentials, AI-verified tests,
                and peer-reviewed vouches.
              </p>
            </div>
            <div className="flex items-center gap-2 self-start sm:self-auto shrink-0 flex-wrap">
              <Link to="/analytics">
                <Button
                  variant="secondary"
                  className="flex items-center gap-1.5 px-3 py-2 text-xs border border-ink/20 text-ink hover:bg-ink/5"
                >
                  <BarChart3 className="w-3.5 h-3.5 text-orange" />
                  <span>View Analytics</span>
                </Button>
              </Link>
              <Button
                variant="primary"
                onClick={() => setShowScanner(true)}
                className="!bg-orange text-paper flex items-center gap-2 shadow-sm px-3.5 py-2 text-xs"
              >
                <QrCode className="w-4 h-4" />
                <span>Scan QR</span>
              </Button>
            </div>
          </div>

          {/* QR Scanner Modal */}
          {showScanner && (
            <QrScanner
              onScan={handleScan}
              onClose={() => setShowScanner(false)}
            />
          )}

          {/* Filter Dropdowns Bar */}
          <Card className="p-3.5 bg-white border border-ink/15 shadow-sm space-y-3">
            <div className="flex items-center gap-2 text-xs font-mono font-semibold text-ink/70 uppercase">
              <Filter className="w-3.5 h-3.5 text-orange" />
              <span>Filter Verified Workers</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
              {/* Trade Selector */}
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-ink/60 uppercase">Trade</label>
                <select
                  value={selectedTrade}
                  onChange={(e) => setSelectedTrade(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-ink/20 bg-paper text-xs text-ink focus:outline-none focus:border-orange font-sans cursor-pointer"
                >
                  <option value="">All Trades</option>
                  <option value="Electrician">Electrician</option>
                  <option value="Mason">Mason</option>
                  <option value="Plumber">Plumber</option>
                </select>
              </div>

              {/* Area Selector */}
              <div className="space-y-1">
                <label className="text-[11px] font-mono text-ink/60 uppercase">Area / City</label>
                <select
                  value={selectedArea}
                  onChange={(e) => setSelectedArea(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl border border-ink/20 bg-paper text-xs text-ink focus:outline-none focus:border-orange font-sans cursor-pointer"
                >
                  <option value="">All Areas</option>
                  <option value="Bangalore South">Bangalore South</option>
                  <option value="Bangalore North">Bangalore North</option>
                  <option value="Delhi West">Delhi West</option>
                </select>
              </div>
            </div>
          </Card>

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-bold">Error loading directory</p>
                <p className="text-xs text-red-600 mt-1">{error}</p>
              </div>
            </div>
          )}

          {/* Loading Skeleton */}
          {loading && (
            <div className="space-y-3">
              <Skeleton className="h-28 w-full rounded-2xl" />
              <Skeleton className="h-28 w-full rounded-2xl" />
              <Skeleton className="h-28 w-full rounded-2xl" />
            </div>
          )}

          {/* Worker Cards Grid */}
          {!loading && workers.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between text-xs font-mono text-ink/60 uppercase px-1">
                <span>Verified Candidates</span>
                <span>{workers.length} Results</span>
              </div>

              {workers.map((worker) => (
                <Card
                  key={worker.credential_id}
                  onClick={() => navigate(`/c/${worker.credential_id}`)}
                  className="p-4 bg-white border border-ink/15 shadow-sm hover:shadow-md hover:border-orange/60 transition-all cursor-pointer group space-y-3"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-start gap-3.5">
                      {/* Mini Seal representation */}
                      <div className="shrink-0 pt-0.5">
                        <Seal tier={worker.tier} size={64} />
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <h2 className="font-heading font-bold text-lg text-ink group-hover:text-orange transition-colors">
                            {worker.name}
                          </h2>
                          <span className="text-[11px] font-mono font-bold px-2 py-0.5 rounded-full bg-orange/10 text-orange border border-orange/20">
                            Tier {worker.tier} • {tierNames[worker.tier]}
                          </span>
                        </div>

                        <div className="flex items-center gap-1.5 text-xs text-ink/70 font-sans">
                          <Briefcase className="w-3.5 h-3.5 text-orange" />
                          <span>{worker.trade}</span>
                          <span>•</span>
                          <span className="truncate max-w-[220px]">{worker.skill}</span>
                        </div>

                        <div className="flex items-center gap-1 text-xs text-ink/50 font-sans">
                          <MapPin className="w-3.5 h-3.5" />
                          <span>{worker.area}</span>
                        </div>
                      </div>
                    </div>

                    <div className="text-right shrink-0">
                      <span className="text-[10px] font-mono text-ink/40 uppercase block">
                        Trust Score
                      </span>
                      <span className="font-heading font-black text-xl text-orange">
                        {Math.round(worker.trust_score)}
                      </span>
                      <span className="text-[10px] font-mono text-ink/50 block">/ 100</span>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-ink/10 flex items-center justify-between text-xs font-mono text-ink/60">
                    <div className="flex items-center gap-1 text-[11px] text-green-700">
                      <ShieldCheck className="w-3.5 h-3.5" />
                      <span>Signature Valid</span>
                    </div>

                    <div className="flex items-center gap-1 text-orange group-hover:translate-x-0.5 transition-transform font-semibold text-xs">
                      <span>View Credential</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          )}

          {/* Empty State */}
          {!loading && workers.length === 0 && (
            <Card className="p-8 text-center space-y-3 bg-white border border-ink/15">
              <Users className="w-10 h-10 text-ink/30 mx-auto" />
              <h2 className="font-heading font-bold text-base text-ink">
                No Verified Workers Found
              </h2>
              <p className="font-sans text-xs text-ink/60 max-w-sm mx-auto">
                No workers match the selected trade or area. Try resetting the filters or check back later as new candidates are verified.
              </p>
              <Button
                variant="secondary"
                onClick={() => {
                  setSelectedTrade('')
                  setSelectedArea('')
                }}
                className="h-9 px-4 text-xs font-semibold"
              >
                Reset Filters
              </Button>
            </Card>
          )}
        </main>

        <footer className="pt-4 border-t border-ink/10 flex items-center justify-between text-xs">
          <Link to="/" className="text-ink/60 hover:text-ink font-mono">
            ← SAKSHI Home
          </Link>
          <Link to="/start" className="text-orange hover:underline font-semibold font-mono">
            Start Your Own Assessment →
          </Link>
        </footer>
      </div>
    </PageTransition>
  )
}
