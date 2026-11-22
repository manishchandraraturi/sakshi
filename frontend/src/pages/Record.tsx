import { useParams, Link } from 'react-router-dom'
import { Card } from '../components/ui/Card'
import { Button } from '../components/ui/Button'
import { Tag } from '../components/ui/Tag'
import { PageTransition } from '../components/PageTransition'
import { Video, ArrowLeft } from 'lucide-react'

export default function Record() {
  const { attemptId } = useParams<{ attemptId: string }>()

  return (
    <PageTransition>
      <div className="min-h-screen bg-paper flex flex-col items-center justify-center p-6">
        <Card className="w-full max-w-md p-8 text-center space-y-6">
          <div className="flex justify-center">
            <div className="w-16 h-16 rounded-full bg-orange/10 flex items-center justify-center border border-orange/20">
              <Video className="w-8 h-8 text-orange animate-pulse" />
            </div>
          </div>

          <div className="space-y-2">
            <Tag variant="accent">
              PHASE 4 PREVIEW
            </Tag>
            <h1 className="font-heading text-2xl font-bold text-ink">Practical Video Assessment</h1>
            <p className="font-sans text-sm text-ink/70">
              Record your practical demonstration with live challenge code overlay.
            </p>
          </div>

          <div className="rounded-lg bg-ink/5 p-3 text-left font-mono text-xs text-ink/80 space-y-1">
            <div>
              <span className="text-ink/40">ATTEMPT_ID: </span>
              <span className="font-semibold text-ink">{attemptId || 'none'}</span>
            </div>
            <div>
              <span className="text-ink/40">STATUS: </span>
              <span className="text-orange font-semibold">awaiting_video</span>
            </div>
          </div>

          <div className="pt-2">
            <Link to="/">
              <Button variant="outline" className="w-full justify-center">
                <ArrowLeft className="w-4 h-4 mr-2" />
                Return to Home
              </Button>
            </Link>
          </div>
        </Card>
      </div>
    </PageTransition>
  )
}
