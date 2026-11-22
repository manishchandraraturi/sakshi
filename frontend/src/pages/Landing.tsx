import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { fetchApi } from '../api/client'
import type { HealthData } from '../api/types'
import { Button } from '../components/ui/Button'
import { Tag } from '../components/ui/Tag'
import { PageTransition } from '../components/PageTransition'
import { useTranslation } from '../i18n/t'

export default function Landing() {
  const navigate = useNavigate()
  const { t } = useTranslation()
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
    <PageTransition className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
      <div className="max-w-2xl mx-auto space-y-8">
        <Tag>
          {loading ? (
            'BACKEND: checking...'
          ) : error || !health ? (
            'BACKEND: offline'
          ) : (
            `BACKEND: ${health.status} / demo_mode: ${health.demo_mode}`
          )}
        </Tag>

        <h1 className="text-5xl sm:text-6xl md:text-8xl font-display font-extrabold tracking-tight text-ink leading-[0.92]">
          Skills, witnessed<span className="text-accent">.</span>
        </h1>

        <p className="text-base sm:text-lg md:text-xl font-body text-muted max-w-lg mx-auto">
          {t('landing_subtitle')}
        </p>

        {/* Mono stat row */}
        <div className="inline-flex flex-wrap items-center justify-center gap-2 sm:gap-4 py-2 px-4 rounded-pill bg-paper-2/70 border border-line text-[11px] sm:text-xs font-mono text-muted tracking-widest uppercase">
          <span>{t('stat_layers')}</span>
          <span className="text-accent">•</span>
          <span>{t('stat_languages')}</span>
          <span className="text-accent">•</span>
          <span>{t('stat_paper')}</span>
        </div>

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center pt-2">
          <Button showArrow onClick={() => navigate('/start')}>
            {t('btn_get_verified')}
          </Button>
          <Button variant="outline" onClick={() => navigate('/directory')}>
            {t('btn_im_hirer')}
          </Button>
        </div>
      </div>
    </PageTransition>
  )
}
