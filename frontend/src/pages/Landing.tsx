import { useEffect, useState } from 'react'
import { fetchApi } from '../api/client'
import type { HealthData } from '../api/types'
import { Button } from '../components/ui/Button'
import { Tag } from '../components/ui/Tag'

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
        <Tag>
          {loading ? (
            'BACKEND: checking...'
          ) : error || !health ? (
            'BACKEND: offline'
          ) : (
            `BACKEND: ${health.status} / demo_mode: ${health.demo_mode}`
          )}
        </Tag>

        <h1 className="text-5xl md:text-7xl font-display font-extrabold tracking-tight text-ink leading-none">
          Skills, witnessed<span className="text-accent">.</span>
        </h1>

        <p className="text-lg md:text-xl font-body text-muted max-w-md mx-auto">
          AI-guided practical tests, human witnesses, and tamper-proof credentials.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-4">
          <Button showArrow>Get verified</Button>
          <Button variant="outline">I'm a hirer</Button>
        </div>
      </div>
    </div>
  )
}
