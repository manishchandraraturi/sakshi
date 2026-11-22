import { useState, useEffect, useRef, useCallback } from 'react'
import { useSessionStore, type Language } from '../store/session'

const LANG_MAP: Record<Language, string> = {
  en: 'en-IN',
  hi: 'hi-IN',
  kn: 'kn-IN',
}

export interface UseSpeechReturn {
  startListening: () => void
  stopListening: () => void
  isListening: boolean
  transcript: string
  isSupported: boolean
  speak: (text: string) => void
}

export function useSpeech(): UseSpeechReturn {
  const { language } = useSessionStore()
  const [isListening, setIsListening] = useState<boolean>(false)
  const [transcript, setTranscript] = useState<string>('')
  const [isSupported, setIsSupported] = useState<boolean>(false)

  const recognitionRef = useRef<ISpeechRecognition | null>(null)
  const langCode = LANG_MAP[language] || 'en-IN'

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const hasSpeech = Boolean(window.SpeechRecognition || window.webkitSpeechRecognition)
      setIsSupported(hasSpeech)
    }
  }, [])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop()
      } catch {
        // Ignore errors on stopping
      }
      recognitionRef.current = null
    }
    setIsListening(false)
  }, [])

  const startListening = useCallback(() => {
    if (typeof window === 'undefined') return

    const SpeechRecognitionClass = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognitionClass) {
      setIsSupported(false)
      return
    }

    // Stop existing instance if any
    stopListening()
    setTranscript('')

    try {
      const recognition = new SpeechRecognitionClass()
      recognition.lang = langCode
      recognition.continuous = true
      recognition.interimResults = true

      recognition.onstart = () => {
        setIsListening(true)
      }

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        let fullTranscript = ''
        for (let i = 0; i < event.results.length; i++) {
          const item = event.results[i]
          if (item && item[0]) {
            fullTranscript += item[0].transcript + ' '
          }
        }
        setTranscript(fullTranscript.trim())
      }

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.warn('Speech recognition error:', event.error)
        setIsListening(false)
      }

      recognition.onend = () => {
        setIsListening(false)
      }

      recognitionRef.current = recognition
      recognition.start()
    } catch (err) {
      console.warn('Could not start speech recognition:', err)
      setIsListening(false)
    }
  }, [langCode, stopListening])

  const speak = useCallback(
    (text: string) => {
      if (typeof window === 'undefined' || !('speechSynthesis' in window)) return

      try {
        window.speechSynthesis.cancel()
        const utterance = new SpeechSynthesisUtterance(text)
        utterance.lang = langCode
        utterance.rate = 0.95
        window.speechSynthesis.speak(utterance)
      } catch (err) {
        console.warn('Speech synthesis error:', err)
      }
    },
    [langCode]
  )

  useEffect(() => {
    return () => {
      stopListening()
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel()
      }
    }
  }, [stopListening])

  return {
    startListening,
    stopListening,
    isListening,
    transcript,
    isSupported,
    speak,
  }
}
