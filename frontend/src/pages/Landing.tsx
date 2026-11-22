import { useEffect, useState } from 'react'
import { fetchApi } from '../api/client'
import type { HealthData } from '../api/types'

export default function Landing() {
  const [health, setHealth] = useState<HealthData | null>(null)
  const [loading, setLoading] = useState<boolean>(true)
  const [error, setError] = useState<boolean>(false)

  useEffect(() => {
    fetchApi<HealthData>('/api/health')
      .then((res) => {
        setHealth(res.data)
        setLoading(false)
      })
      .catch(() => {
        setError(true)
        setLoading(false)
      })
  }, [])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
      <div className="max-w-xl mx-auto space-y-8">
        <div className="inline-block px-3 py-1 text-xs font-mono tracking-widest uppercase border border-ink/20 rounded-pill bg-paper-2/80">
          {loading ? (
            'BACKEND: checking...'
          ) : error || !health ? (
            'BACKEND: offline'
          ) : (
            `BACKEND: ${health.status} / demo_mode: ${health.demo_mode}`
          )}
        </div>

        <h1 className="text-5xl md:text-7xl font-display font-extrabold tracking-tight text-ink leading-none">
          Skills, witnessed<span className="text-accent">.</span>
        </h1>

        <p className="text-lg md:text-xl font-body text-muted max-w-md mx-auto">
          AI-guided practical tests, human witnesses, and tamper-proof credentials.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
          <button className="px-6 py-3 bg-ink text-paper rounded-pill font-body font-medium hover:bg-ink-2 transition shadow-md">
            Get verified
          </button>
          <button className="px-6 py-3 border border-ink/30 text-ink rounded-pill font-body font-medium hover:border-ink transition">
            I'm a hirer
          </button>
        </div>
      </div>
    </div>
  )
}
