import { useState, useRef, useCallback, useEffect } from 'react'

export interface UseRecorderReturn {
  startRecording: () => Promise<void>
  stopRecording: () => void
  resetRecording: () => void
  isRecording: boolean
  videoBlob: Blob | null
  videoUrl: string | null
  stream: MediaStream | null
  durationSeconds: number
  error: string | null
  isCameraDenied: boolean
}

export function useRecorder(): UseRecorderReturn {
  const [isRecording, setIsRecording] = useState<boolean>(false)
  const [videoBlob, setVideoBlob] = useState<Blob | null>(null)
  const [videoUrl, setVideoUrl] = useState<string | null>(null)
  const [stream, setStream] = useState<MediaStream | null>(null)
  const [durationSeconds, setDurationSeconds] = useState<number>(0)
  const [error, setError] = useState<string | null>(null)
  const [isCameraDenied, setIsCameraDenied] = useState<boolean>(false)

  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const chunksRef = useRef<Blob[]>([])
  const timerRef = useRef<number | null>(null)
  const streamRef = useRef<MediaStream | null>(null)

  const stopTracks = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop())
      streamRef.current = null
      setStream(null)
    }
  }, [])

  const resetRecording = useCallback(() => {
    stopTracks()
    if (videoUrl) {
      URL.revokeObjectURL(videoUrl)
    }
    setVideoBlob(null)
    setVideoUrl(null)
    setDurationSeconds(0)
    setError(null)
    setIsCameraDenied(false)
    setIsRecording(false)
  }, [stopTracks, videoUrl])

  const stopRecording = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current)
      timerRef.current = null
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop()
      } catch (err) {
        console.warn('Error stopping media recorder:', err)
      }
    }

    stopTracks()
    setIsRecording(false)
  }, [stopTracks])

  const startRecording = useCallback(async () => {
    resetRecording()
    chunksRef.current = []
    setError(null)
    setIsCameraDenied(false)

    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        throw new Error('Camera access API is not supported on this device/browser')
      }

      let userStream: MediaStream
      try {
        userStream = await navigator.mediaDevices.getUserMedia({
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'environment',
          },
          audio: true,
        })
      } catch {
        // Fallback to basic audio/video if constraints fail
        userStream = await navigator.mediaDevices.getUserMedia({
          video: true,
          audio: true,
        })
      }

      streamRef.current = userStream
      setStream(userStream)

      const mimeCandidates = [
        'video/webm;codecs=vp9,opus',
        'video/webm;codecs=vp8,opus',
        'video/webm',
        'video/mp4',
      ]
      const supportedMime =
        mimeCandidates.find((type) => MediaRecorder.isTypeSupported(type)) || ''

      const options = supportedMime ? { mimeType: supportedMime } : undefined
      const recorder = new MediaRecorder(userStream, options)

      recorder.ondataavailable = (event: BlobEvent) => {
        if (event.data && event.data.size > 0) {
          chunksRef.current.push(event.data)
        }
      }

      recorder.onstop = () => {
        const finalBlob = new Blob(chunksRef.current, {
          type: supportedMime || 'video/webm',
        })
        setVideoBlob(finalBlob)
        setVideoUrl(URL.createObjectURL(finalBlob))
      }

      mediaRecorderRef.current = recorder
      recorder.start(1000)
      setIsRecording(true)

      setDurationSeconds(0)
      timerRef.current = window.setInterval(() => {
        setDurationSeconds((prev) => prev + 1)
      }, 1000)
    } catch (err: unknown) {
      let msg = 'Camera access was denied or unavailable'
      let denied = true

      if (err instanceof DOMException || err instanceof Error) {
        msg = err.message
        const lowerName = (err.name || '').toLowerCase()
        const lowerMsg = (err.message || '').toLowerCase()
        if (
          lowerName.includes('notallowed') ||
          lowerName.includes('permission') ||
          lowerName.includes('notfound') ||
          lowerName.includes('devicesnotfound') ||
          lowerName.includes('notreadable') ||
          lowerMsg.includes('denied') ||
          lowerMsg.includes('permission') ||
          lowerMsg.includes('not allowed') ||
          lowerMsg.includes('not found') ||
          lowerMsg.includes('unavailable')
        ) {
          denied = true
        }
      }

      setIsCameraDenied(denied)
      setError(msg)
      stopTracks()
      setIsRecording(false)
    }
  }, [resetRecording, stopTracks])

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current)
      stopTracks()
      if (videoUrl) URL.revokeObjectURL(videoUrl)
    }
  }, [stopTracks, videoUrl])

  return {
    startRecording,
    stopRecording,
    resetRecording,
    isRecording,
    videoBlob,
    videoUrl,
    stream,
    durationSeconds,
    error,
    isCameraDenied,
  }
}
