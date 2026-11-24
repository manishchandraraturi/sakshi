import { useEffect, useRef, useState, useCallback } from 'react'
import jsQR from 'jsqr'
import { Camera, AlertCircle, X, RefreshCw } from 'lucide-react'
import { Button } from './ui/Button'

interface QrScannerProps {
  onScan: (decodedText: string) => void
  onClose: () => void
}

export default function QrScanner({ onScan, onClose }: QrScannerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null)
  const canvasRef = useRef<HTMLCanvasElement | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const animFrameIdRef = useRef<number | null>(null)

  const [hasCameraError, setHasCameraError] = useState(false)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [isScanning, setIsScanning] = useState(true)

  const stopCamera = useCallback(() => {
    if (animFrameIdRef.current) {
      cancelAnimationFrame(animFrameIdRef.current)
      animFrameIdRef.current = null
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
    }
  }, [])

  const startCamera = useCallback(async () => {
    stopCamera()
    setHasCameraError(false)
    setErrorMessage(null)
    setIsScanning(true)

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera access is not supported in this browser.')
      }

      let stream: MediaStream
      try {
        // Prefer environment-facing camera on mobile devices
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: 'environment' } },
          audio: false,
        })
      } catch (envErr) {
        // Fallback to any available video input
        stream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: false,
        })
      }

      streamRef.current = stream

      if (videoRef.current) {
        videoRef.current.srcObject = stream
        videoRef.current.setAttribute('playsinline', 'true')
        await videoRef.current.play()
      }

      // Start scan loop
      const scanFrame = () => {
        if (!videoRef.current || !canvasRef.current) return

        const video = videoRef.current
        const canvas = canvasRef.current

        if (video.readyState === video.HAVE_ENOUGH_DATA) {
          const ctx = canvas.getContext('2d', { willReadFrequently: true })
          if (ctx) {
            canvas.width = video.videoWidth
            canvas.height = video.videoHeight
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

            const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height)
            const code = jsQR(imageData.data, imageData.width, imageData.height, {
              inversionAttempts: 'dontInvert',
            })

            if (code && code.data) {
              const scannedData = code.data.trim()
              if (scannedData) {
                stopCamera()
                setIsScanning(false)
                onScan(scannedData)
                return
              }
            }
          }
        }

        animFrameIdRef.current = requestAnimationFrame(scanFrame)
      }

      animFrameIdRef.current = requestAnimationFrame(scanFrame)
    } catch (err: any) {
      console.error('Camera initialization error:', err)
      setHasCameraError(true)
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setErrorMessage('Camera access was denied. Please allow camera permissions.')
      } else if (err.name === 'NotFoundError' || err.name === 'DevicesNotFoundError') {
        setErrorMessage('No camera device was detected on your system.')
      } else {
        setErrorMessage(err.message || 'Unable to access camera.')
      }
    }
  }, [onScan, stopCamera])

  useEffect(() => {
    startCamera()
    return () => {
      stopCamera()
    }
  }, [startCamera, stopCamera])

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/80 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="relative w-full max-w-md bg-paper rounded-2xl shadow-2xl border border-ink/20 overflow-hidden flex flex-col">
        {/* Modal Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-ink/10 bg-white">
          <div className="flex items-center gap-2">
            <Camera className="w-4 h-4 text-orange" />
            <span className="font-heading font-black text-sm text-ink">
              Scan Credential QR
            </span>
          </div>
          <button
            onClick={() => {
              stopCamera()
              onClose()
            }}
            className="p-1.5 rounded-lg text-ink/50 hover:text-ink hover:bg-ink/5 transition-colors"
            aria-label="Close Scanner"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Video / Camera Feed Viewport */}
        <div className="relative w-full aspect-square bg-ink flex items-center justify-center overflow-hidden">
          {hasCameraError ? (
            <div className="p-6 text-center space-y-4 max-w-xs text-paper">
              <div className="w-12 h-12 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center mx-auto">
                <AlertCircle className="w-6 h-6" />
              </div>
              <div className="space-y-1">
                <p className="font-semibold text-sm">Camera Unavailable</p>
                <p className="text-xs text-paper/70">{errorMessage}</p>
              </div>
              <Button
                variant="primary"
                onClick={startCamera}
                className="!bg-orange text-paper flex items-center gap-1.5 mx-auto px-4 py-2 text-xs"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span>Try Again</span>
              </Button>
            </div>
          ) : (
            <>
              <video
                ref={videoRef}
                className="w-full h-full object-cover"
                muted
                playsInline
                autoPlay
              />
              <canvas ref={canvasRef} className="hidden" />

              {/* Viewfinder Target Reticle */}
              {isScanning && (
                <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
                  {/* Subtle darkened vignette around target */}
                  <div className="w-64 h-64 border-2 border-orange/80 rounded-2xl relative shadow-[0_0_0_9999px_rgba(0,0,0,0.4)]">
                    {/* Corner Accent Markers */}
                    <div className="absolute -top-1 -left-1 w-5 h-5 border-t-4 border-l-4 border-orange rounded-tl" />
                    <div className="absolute -top-1 -right-1 w-5 h-5 border-t-4 border-r-4 border-orange rounded-tr" />
                    <div className="absolute -bottom-1 -left-1 w-5 h-5 border-b-4 border-l-4 border-orange rounded-bl" />
                    <div className="absolute -bottom-1 -right-1 w-5 h-5 border-b-4 border-r-4 border-orange rounded-br" />

                    {/* Animated Scanning Line */}
                    <div className="absolute inset-x-2 top-0 h-0.5 bg-orange shadow-[0_0_8px_#FF5500] animate-[bounce_2s_ease-in-out_infinite]" />
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Modal Footer */}
        <div className="p-4 bg-white border-t border-ink/10 text-center space-y-2">
          <p className="text-xs font-mono text-ink/70">
            Align the QR code within the frame to verify authenticity.
          </p>
          <Button
            variant="secondary"
            onClick={() => {
              stopCamera()
              onClose()
            }}
            className="w-full justify-center text-xs py-2"
          >
            Cancel
          </Button>
        </div>
      </div>
    </div>
  )
}
