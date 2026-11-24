import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Users,
  ShieldCheck,
  Briefcase,
  ArrowLeft,
  AlertCircle,
  Award,
  BarChart3,
  RefreshCw,
} from 'lucide-react'
import PageTransition from '../components/PageTransition'
import { Card } from '../components/ui/Card'
import { Tag } from '../components/ui/Tag'
import { Skeleton } from '../components/ui/Skeleton'
import { Button } from '../components/ui/Button'
import { fetchApi } from '../api/client'
import type { AnalyticsData } from '../api/types'

export default function Analytics() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadAnalytics = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await fetchApi<AnalyticsData>('/api/directory/analytics')
      if (res.data) {
        setData(res.data)
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load analytics telemetry.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadAnalytics()
  }, [])

  // Calculate totals and percentages
  const tier1 = data?.tier_distribution.tier_1 || 0
  const tier2 = data?.tier_distribution.tier_2 || 0
  const tier3 = data?.tier_distribution.tier_3 || 0
  const totalCredentials = tier1 + tier2 + tier3 || 1

  const tierStats = [
    {
      tier: 3,
      label: 'Tier 3: Trusted',
      desc: 'AI Practical Passed + Master/Employer Vouch',
      count: tier3,
      pct: Math.round((tier3 / totalCredentials) * 100),
      color: 'bg-orange',
      textColor: 'text-orange',
      badge: 'Gold Seal',
    },
    {
      tier: 2,
      label: 'Tier 2: Witnessed',
      desc: 'AI Practical Passed + 2 Peer Witness Vouches',
      count: tier2,
      pct: Math.round((tier2 / totalCredentials) * 100),
      color: 'bg-ink',
      textColor: 'text-ink',
      badge: 'Silver Seal',
    },
    {
      tier: 1,
      label: 'Tier 1: Demonstrated',
      desc: 'Autonomous AI Video Multi-Modal Verification',
      count: tier1,
      pct: Math.round((tier1 / totalCredentials) * 100),
      color: 'bg-ink/40',
      textColor: 'text-ink/70',
      badge: 'Verified',
    },
  ]

  // Sort trade distribution descending
  const trades = Object.entries(data?.trade_distribution || {})
    .map(([trade, count]) => ({
      name: trade.charAt(0).toUpperCase() + trade.slice(1),
      count,
      pct: Math.round((count / Math.max(totalCredentials, 1)) * 100),
    }))
    .sort((a, b) => b.count - a.count)

  const totalTradesCount = trades.length

  return (
    <PageTransition>
      <div className="min-h-screen bg-paper flex flex-col justify-between max-w-3xl mx-auto px-4 py-4 md:py-8 space-y-6">
        {/* Navigation & Header */}
        <header className="border-b border-ink/10 pb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-heading font-black text-lg text-ink">SAKSHI</span>
              <span className="text-ink/30">•</span>
              <Tag variant="accent">Hirer Intelligence</Tag>
            </div>
            <Link
              to="/directory"
              className="flex items-center gap-1 text-xs font-mono text-ink/60 hover:text-orange font-semibold transition-colors"
            >
              <ArrowLeft className="w-3.5 h-3.5" />
              <span>Back to Directory</span>
            </Link>
          </div>
        </header>

        <main className="space-y-6">
          {/* Title Banner */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div className="space-y-1">
              <h1 className="font-heading font-black text-2xl md:text-3xl text-ink">
                Workforce Analytics
              </h1>
              <p className="font-sans text-xs md:text-sm text-ink/70">
                Real-time cryptographic verification metrics and trade distribution across informal skilled craftspeople.
              </p>
            </div>
            <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-green-500/10 border border-green-500/20 text-green-700 text-xs font-mono font-medium self-start sm:self-auto shrink-0">
              <span className="w-2 h-2 rounded-full bg-green-600 animate-pulse" />
              <span>Live Protocol Telemetry</span>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-3">
              <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
              <div className="flex-1">
                <p className="font-bold">Error loading analytics</p>
                <p className="text-xs text-red-600 mt-0.5">{error}</p>
                <Button
                  variant="outline"
                  onClick={loadAnalytics}
                  className="mt-3 text-xs px-3 py-1.5 flex items-center gap-1.5 border-red-300 text-red-700"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Retry</span>
                </Button>
              </div>
            </div>
          )}

          {/* Loading Skeletons */}
          {loading && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Skeleton className="h-28 w-full rounded-2xl" />
                <Skeleton className="h-28 w-full rounded-2xl" />
                <Skeleton className="h-28 w-full rounded-2xl" />
              </div>
              <Skeleton className="h-64 w-full rounded-2xl" />
              <Skeleton className="h-64 w-full rounded-2xl" />
            </div>
          )}

          {/* Analytics Content */}
          {!loading && data && (
            <>
              {/* Row 1: Top 3 KPI Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                {/* KPI 1 */}
                <Card className="p-4 bg-white border border-ink/15 shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-ink/60">
                    <span className="text-xs font-mono font-semibold uppercase">Total Workers</span>
                    <div className="w-8 h-8 rounded-full bg-ink/5 flex items-center justify-center text-ink">
                      <Users className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="font-heading font-black text-3xl text-ink">
                    {data.total_workers}
                  </div>
                  <p className="text-[11px] font-mono text-ink/50">
                    Registered verified talent pool
                  </p>
                </Card>

                {/* KPI 2 */}
                <Card className="p-4 bg-white border border-ink/15 shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-ink/60">
                    <span className="text-xs font-mono font-semibold uppercase">Witness Vouches</span>
                    <div className="w-8 h-8 rounded-full bg-orange/10 flex items-center justify-center text-orange">
                      <ShieldCheck className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="font-heading font-black text-3xl text-orange">
                    {data.total_vouches}
                  </div>
                  <p className="text-[11px] font-mono text-ink/50">
                    Peer & employer attestations
                  </p>
                </Card>

                {/* KPI 3 */}
                <Card className="p-4 bg-white border border-ink/15 shadow-sm space-y-2">
                  <div className="flex items-center justify-between text-ink/60">
                    <span className="text-xs font-mono font-semibold uppercase">Active Trades</span>
                    <div className="w-8 h-8 rounded-full bg-ink/5 flex items-center justify-center text-ink">
                      <Briefcase className="w-4 h-4" />
                    </div>
                  </div>
                  <div className="font-heading font-black text-3xl text-ink">
                    {totalTradesCount}
                  </div>
                  <p className="text-[11px] font-mono text-ink/50">
                    Standardized blueprint crafts
                  </p>
                </Card>
              </div>

              {/* Row 2: Seal Tier Distribution Bar Chart */}
              <Card className="p-5 bg-white border border-ink/15 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-ink/10 pb-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <Award className="w-4 h-4 text-orange" />
                      <h2 className="font-heading font-black text-base text-ink">
                        Seal Tier Distribution
                      </h2>
                    </div>
                    <p className="text-xs text-ink/60 font-sans">
                      Breakdown of candidates by cryptographic attestation depth.
                    </p>
                  </div>
                  <span className="text-xs font-mono text-ink/50">
                    {totalCredentials} Issued Credentials
                  </span>
                </div>

                <div className="space-y-4 pt-1">
                  {tierStats.map((stat) => (
                    <div key={stat.tier} className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-ink">{stat.label}</span>
                          <span className="text-[10px] font-mono px-1.5 py-0.2 rounded bg-ink/5 text-ink/60">
                            {stat.badge}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 font-mono">
                          <span className="text-ink/60">{stat.count} candidates</span>
                          <span className={`font-bold ${stat.textColor}`}>{stat.pct}%</span>
                        </div>
                      </div>

                      {/* Bar Track & Fill */}
                      <div className="w-full h-3 rounded-full bg-ink/5 overflow-hidden">
                        <motion.div
                          className={`h-full rounded-full ${stat.color}`}
                          initial={{ width: 0 }}
                          animate={{ width: `${stat.pct}%` }}
                          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
                        />
                      </div>

                      <p className="text-[10px] text-ink/40 font-mono">
                        {stat.desc}
                      </p>
                    </div>
                  ))}
                </div>
              </Card>

              {/* Row 3: Trade Composition Bar Chart */}
              <Card className="p-5 bg-white border border-ink/15 shadow-sm space-y-4">
                <div className="flex items-center justify-between border-b border-ink/10 pb-3">
                  <div className="space-y-0.5">
                    <div className="flex items-center gap-2">
                      <BarChart3 className="w-4 h-4 text-orange" />
                      <h2 className="font-heading font-black text-base text-ink">
                        Workforce Composition by Trade
                      </h2>
                    </div>
                    <p className="text-xs text-ink/60 font-sans">
                      Verified labor market supply across certified vocational categories.
                    </p>
                  </div>
                  <span className="text-xs font-mono text-ink/50">
                    {trades.length} Categories
                  </span>
                </div>

                {trades.length === 0 ? (
                  <p className="text-xs font-mono text-ink/50 py-4 text-center">
                    No verified credentials recorded yet.
                  </p>
                ) : (
                  <div className="space-y-3 pt-1">
                    {trades.map((trade, idx) => (
                      <div key={trade.name} className="space-y-1">
                        <div className="flex items-center justify-between text-xs">
                          <span className="font-medium text-ink flex items-center gap-1.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-orange" />
                            {trade.name}
                          </span>
                          <div className="flex items-center gap-2 font-mono">
                            <span className="text-ink/60">{trade.count} verified</span>
                            <span className="font-bold text-ink">{trade.pct}%</span>
                          </div>
                        </div>

                        {/* Bar Track & Fill */}
                        <div className="w-full h-2.5 rounded-full bg-ink/5 overflow-hidden">
                          <motion.div
                            className={`h-full rounded-full ${
                              idx === 0 ? 'bg-orange' : 'bg-ink'
                            }`}
                            initial={{ width: 0 }}
                            animate={{ width: `${trade.pct}%` }}
                            transition={{ duration: 0.6, delay: idx * 0.05, ease: [0.22, 1, 0.36, 1] }}
                          />
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </Card>

              {/* Enterprise B2B Value Callout */}
              <Card className="p-4 bg-orange/5 border border-orange/20 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs">
                <div className="space-y-1">
                  <span className="font-bold text-ink block font-sans">
                    Enterprise Hirer Integration
                  </span>
                  <p className="text-ink/70 font-sans">
                    Need bulk candidate background verification or webhook integration for facility management?
                  </p>
                </div>
                <Button
                  variant="primary"
                  onClick={() => window.open('mailto:enterprise@sakshi.org', '_blank')}
                  className="!bg-orange text-paper px-4 py-2 text-xs shrink-0 shadow-sm"
                >
                  Contact Enterprise Sales
                </Button>
              </Card>
            </>
          )}
        </main>

        {/* Footer */}
        <footer className="pt-4 border-t border-ink/10 flex items-center justify-between text-xs text-ink/50 font-mono">
          <span>SAKSHI Cryptographic Trust Network</span>
          <Link to="/directory" className="text-orange hover:underline">
            Trades Directory →
          </Link>
        </footer>
      </div>
    </PageTransition>
  )
}
