import { useState, useEffect, useRef } from 'react'
import { useParams, useNavigate, useSearchParams, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Video,
  StopCircle,
  RotateCcw,
  Upload,
  CheckCircle2,
  AlertCircle,
  ShieldAlert,
} from 'lucide-react'
import { fetchApi } from '../api/client'
import { Button } from '../components/ui/Button'
import { Tag } from '../components/ui/Tag'
import { PageTransition } from '../components/PageTransition'
import { useRecorder } from '../hooks/useRecorder'

export default function Record() {
  const { attemptId } = useParams<{ attemptId: string }>()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const location = useLocation()

  const isRerecord = searchParams.get('rerecord') === 'true'
  const stepsParam = searchParams.get('steps')
  const stateStepIds = (location.state as { step_ids?: string[] } | null)?.step_ids
  const stepIdsToRerecord = stateStepIds || (stepsParam ? stepsParam.split(',') : [])

  const [challengeCode, setChallengeCode] = useState<string>('----')
  const [videoSource, setVideoSource] = useState<'live' | 'upload'>('live')
  const [uploading, setUploading] = useState<boolean>(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const {
    startRecording,
    stopRecording,
    resetRecording,
    isRecording,
    videoBlob,
    videoUrl,
    stream,
    durationSeconds,
    error: recorderError,
    isCameraDenied,
  } = useRecorder()

  const liveVideoRef = useRef<HTMLVideoElement | null>(null)
  const fileInputRef = useRef<HTMLInputElement | null>(null)

  // Attach active live stream to video element
  useEffect(() => {
    if (liveVideoRef.current && stream) {
      liveVideoRef.current.srcObject = stream
    }
  }, [stream])

  // Fetch attempt details for challenge code
  useEffect(() => {
    if (!attemptId) return

    fetchApi<{ challenge_code: string }>(`/api/attempts/${attemptId}`)
      .then((res) => {
        if (res.data?.challenge_code) {
          setChallengeCode(res.data.challenge_code)
        }
      })
      .catch(() => {
        // Fallback default
      })
  }, [attemptId])

  // Handle uploaded video file
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    resetRecording()
    setVideoSource('upload')
    setSubmitError(null)

    const url = URL.createObjectURL(file)
    setUploadedBlob(file)
    setUploadedUrl(url)
  }

  const [uploadedBlob, setUploadedBlob] = useState<Blob | null>(null)
  const [uploadedUrl, setUploadedUrl] = useState<string | null>(null)

  const activeVideoBlob = uploadedBlob || videoBlob
  const activeVideoUrl = uploadedUrl || videoUrl

  const handleRetake = () => {
    if (uploadedUrl) {
      URL.revokeObjectURL(uploadedUrl)
      setUploadedUrl(null)
      setUploadedBlob(null)
    }
    resetRecording()
    setVideoSource('live')
    setSubmitError(null)
  }

  // Submit video to backend
  const handleSubmit = async () => {
    if (!attemptId || !activeVideoBlob) return

    setUploading(true)
    setSubmitError(null)

    try {
      const formData = new FormData()

      if (isRerecord) {
        formData.append('file', activeVideoBlob, 'rerecord.webm')
        formData.append('step_ids', JSON.stringify(stepIdsToRerecord))

        const response = await fetch(`/api/attempts/${attemptId}/rerecord`, {
          method: 'POST',
          body: formData,
        })

        const result = await response.json()
        if (!result.ok) {
          throw new Error(result.error?.message || 'Failed to process re-recorded video')
        }
      } else {
        formData.append('file', activeVideoBlob, 'demonstration.mp4')

        const response = await fetch(
          `/api/attempts/${attemptId}/video?source=${videoSource}`,
          {
            method: 'POST',
            body: formData,
          }
        )

        const result = await response.json()
        if (!result.ok) {
          throw new Error(result.error?.message || 'Failed to process video')
        }
      }

      // Transition to review page
      navigate(`/review/${attemptId}`)
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Error uploading video'
      setSubmitError(msg)
    } finally {
      setUploading(false)
    }
  }

  const formatTimer = (sec: number) => {
    const m = Math.floor(sec / 60)
    const s = sec % 60
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`
  }

  return (
    <PageTransition>
      <div className="min-h-screen bg-paper flex flex-col justify-between max-w-xl mx-auto px-4 py-4 md:py-8">
        {/* Header */}
        <header className="border-b border-ink/10 pb-4 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-heading font-black text-lg text-ink">SAKSHI</span>
              <span className="text-ink/30">•</span>
              <Tag variant="accent">{isRerecord ? 'Re-record Failed Steps' : 'Video Demo'}</Tag>
            </div>
            <div className="font-mono text-xs text-ink/60">
              {isRecording ? (
                <span className="text-orange font-bold animate-pulse">RECORDING</span>
              ) : activeVideoUrl ? (
                <span className="text-ink/80">READY TO SUBMIT</span>
              ) : isCameraDenied ? (
                <span className="text-amber-600 font-semibold">UPLOAD READY</span>
              ) : (
                'CAMERA STANDBY'
              )}
            </div>
          </div>
          {isRerecord && stepIdsToRerecord.length > 0 && (
            <div className="mt-2 text-xs font-mono text-orange flex items-center gap-1.5">
              <span>Steps requiring re-recording:</span>
              <span className="font-bold underline">{stepIdsToRerecord.join(', ')}</span>
            </div>
          )}
        </header>

        {/* Video Canvas Container */}
        <main className="flex-1 flex flex-col justify-center">
          <div className="relative aspect-[4/3] w-full rounded-2xl overflow-hidden bg-black shadow-lg border border-ink/20">
            {/* 1. Preview of recorded/uploaded video */}
            {activeVideoUrl ? (
              <video
                src={activeVideoUrl}
                controls
                playsInline
                className="w-full h-full object-contain bg-black"
              />
            ) : isCameraDenied ? (
              /* 2. Fallback when Camera is Denied or Unavailable */
              <div className="relative w-full h-full bg-neutral-900 border-2 border-amber-500/40 flex flex-col items-center justify-center p-6 text-center space-y-4">
                <div className="w-16 h-16 rounded-full bg-amber-500/10 border border-amber-500/30 flex items-center justify-center text-amber-500">
                  <AlertCircle className="w-8 h-8" />
                </div>
                <div className="space-y-1.5 max-w-sm">
                  <h3 className="font-heading font-bold text-base md:text-lg text-paper">
                    Camera Access Denied or Unavailable
                  </h3>
                  <p className="font-sans text-xs text-paper/70 leading-relaxed">
                    Camera access denied or unavailable. Please upload an existing video.
                  </p>
                </div>
                <div className="rounded-lg bg-black/70 border border-orange/50 px-3 py-1.5 flex items-center gap-2">
                  <span className="text-[10px] font-mono text-orange uppercase font-bold tracking-wider">
                    CODE
                  </span>
                  <span className="font-mono text-sm font-extrabold text-paper tracking-widest">
                    {challengeCode}
                  </span>
                </div>
              </div>
            ) : (
              /* 3. Live camera feed or standby state */
              <div className="relative w-full h-full flex items-center justify-center">
                {stream ? (
                  <video
                    ref={liveVideoRef}
                    autoPlay
                    playsInline
                    muted
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <div className="text-center p-6 space-y-3">
                    <div className="w-16 h-16 rounded-full bg-white/10 flex items-center justify-center mx-auto border border-white/20">
                      <Video className="w-8 h-8 text-white/70" />
                    </div>
                    <p className="text-white/80 font-sans text-sm">
                      Press <span className="text-orange font-semibold">Start Live Recording</span> below to
                      activate camera.
                    </p>
                  </div>
                )}
              </div>
            )}

            {/* Live Challenge Code Corner Overlay (when not in denied mode) */}
            {!isCameraDenied && (
              <div className="absolute top-3 left-3 z-10">
                <div className="rounded-lg bg-black/85 backdrop-blur-md border border-orange/60 px-3 py-1.5 shadow-md flex items-center gap-2">
                  <span className="text-[10px] font-mono text-orange uppercase font-bold tracking-wider">
                    CODE
                  </span>
                  <span className="font-mono text-base font-extrabold text-paper tracking-widest">
                    {challengeCode}
                  </span>
                </div>
              </div>
            )}

            {/* Live Recording Timer Overlay */}
            {isRecording && (
              <div className="absolute top-3 right-3 z-10 flex items-center gap-2 bg-black/80 backdrop-blur-md px-3 py-1.5 rounded-full border border-red-500/50">
                <span className="w-2.5 h-2.5 rounded-full bg-red-500 animate-ping" />
                <span className="font-mono text-xs font-bold text-red-400">
                  {formatTimer(durationSeconds)}
                </span>
              </div>
            )}

            {/* Notice banner at bottom of camera */}
            {!activeVideoUrl && !isCameraDenied && (
              <div className="absolute bottom-2 inset-x-2 z-10 bg-black/75 backdrop-blur-sm rounded-lg px-3 py-1.5 text-center">
                <p className="font-mono text-[11px] text-paper/80">
                  Write <span className="text-orange font-bold">{challengeCode}</span> on paper or keep visible on screen
                </p>
              </div>
            )}
          </div>

          {/* Error messages */}
          <AnimatePresence>
            {(recorderError || submitError) && !isCameraDenied && (
              <motion.div
                initial={{ opacity: 0, y: -6 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="mt-3 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-2"
              >
                <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
                <p className="flex-1">{recorderError || submitError}</p>
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* Hidden native file input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="video/*"
          onChange={handleFileChange}
          className="hidden"
        />

        {/* Action Controls Footer */}
        <footer className="pt-4 border-t border-ink/10 space-y-3">
          {activeVideoUrl ? (
            /* Post-recording review controls */
            <div className="space-y-3">
              <div className="flex gap-3">
                <Button
                  variant="outline"
                  onClick={handleRetake}
                  disabled={uploading}
                  className="flex-1 justify-center h-12"
                >
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Retake Video
                </Button>

                <Button
                  variant="primary"
                  onClick={handleSubmit}
                  loading={uploading}
                  disabled={uploading}
                  className="flex-1 justify-center h-12 !bg-orange text-paper hover:!bg-orange/90"
                >
                  <CheckCircle2 className="w-4 h-4 mr-2" />
                  {isRerecord ? 'Submit Re-record' : 'Submit Video'}
                </Button>
              </div>

              {videoSource === 'upload' && (
                <div className="flex items-center justify-center gap-1.5 text-xs text-amber-700 font-mono">
                  <ShieldAlert className="w-3.5 h-3.5" />
                  <span>Pre-recorded upload source flagged for review</span>
                </div>
              )}
            </div>
          ) : isRecording ? (
            /* Active recording stop button */
            <div className="flex flex-col items-center gap-2">
              <Button
                variant="danger"
                onClick={stopRecording}
                className="w-full justify-center h-14 text-base font-bold shadow-lg"
              >
                <StopCircle className="w-5 h-5 mr-2 animate-pulse" />
                Stop Recording ({formatTimer(durationSeconds)})
              </Button>
              <p className="font-mono text-[11px] text-ink/50">Minimum 5s, maximum 120s</p>
            </div>
          ) : isCameraDenied ? (
            /* Camera Denied fallback: Highlight and expand Upload Existing Video */
            <div className="space-y-2.5">
              <Button
                variant="primary"
                onClick={() => fileInputRef.current?.click()}
                className="w-full justify-center h-14 text-base font-bold !bg-orange text-paper hover:!bg-orange/90 shadow-lg ring-2 ring-orange/40"
              >
                <Upload className="w-5 h-5 mr-2" />
                Upload Existing Video File
              </Button>

              <Button
                variant="outline"
                onClick={startRecording}
                className="w-full justify-center h-11 text-xs font-mono border-ink/20 text-ink/70 hover:bg-ink/5"
              >
                <RotateCcw className="w-3.5 h-3.5 mr-1.5" />
                Retry Camera Access
              </Button>
            </div>
          ) : (
            /* Standard Standby options: Live record or Upload fallback */
            <div className="space-y-2">
              <Button
                variant="primary"
                onClick={startRecording}
                className="w-full justify-center h-14 text-base font-semibold !bg-orange text-paper hover:!bg-orange/90 shadow-md"
              >
                <Video className="w-5 h-5 mr-2" />
                Start Live Recording
              </Button>

              <div className="flex items-center justify-center gap-2">
                <span className="h-px bg-ink/10 flex-1" />
                <span className="text-[11px] font-mono text-ink/40 uppercase">or</span>
                <span className="h-px bg-ink/10 flex-1" />
              </div>

              <Button
                variant="secondary"
                onClick={() => fileInputRef.current?.click()}
                className="w-full justify-center h-11 text-xs font-mono"
              >
                <Upload className="w-4 h-4 mr-2" />
                Upload Existing Video File
              </Button>
            </div>
          )}
        </footer>
      </div>
    </PageTransition>
  )
}
