import { useEffect, useState, useRef } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Mic,
  MicOff,
  Send,
  Volume2,
  Bot,
  User,
  AlertCircle,
  Sparkles,
} from 'lucide-react'
import { fetchApi } from '../api/client'
import type { InterviewResponse } from '../api/types'
import { Button } from '../components/ui/Button'
import { Tag } from '../components/ui/Tag'
import { Skeleton } from '../components/ui/Skeleton'
import { AgentLog } from '../components/AgentLog'
import { PageTransition } from '../components/PageTransition'
import { OfflineBanner } from '../components/OfflineBanner'
import { useSpeech } from '../hooks/useSpeech'
import { useNetworkStatus } from '../hooks/useNetworkStatus'
import { useSessionStore } from '../store/session'

interface ChatMessage {
  id: string
  sender: 'agent' | 'user'
  text: string
  timestamp: string
}

export default function Interview() {
  const { attemptId } = useParams<{ attemptId: string }>()
  const navigate = useNavigate()
  const isOnline = useNetworkStatus()
  const {
    language,
    cachedInterviewState,
    setCachedInterviewState,
    clearCachedInterviewState,
  } = useSessionStore()

  const {
    startListening,
    stopListening,
    isListening,
    transcript,
    isSupported: speechSupported,
    speak,
  } = useSpeech()

  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputText, setInputText] = useState<string>('')
  const [loadingInitial, setLoadingInitial] = useState<boolean>(true)
  const [evaluating, setEvaluating] = useState<boolean>(false)
  const [progress, setProgress] = useState<{ current: number; total: number }>({
    current: 1,
    total: 3,
  })
  const [error, setError] = useState<string | null>(null)
  const [agentLogs, setAgentLogs] = useState<string[]>([])

  const chatBottomRef = useRef<HTMLDivElement | null>(null)

  // Scroll to bottom when messages update
  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, evaluating, agentLogs])

  // Sync live speech transcript to inputText
  useEffect(() => {
    if (transcript) {
      setInputText(transcript)
    }
  }, [transcript])

  // Sync state to local Zustand cache
  useEffect(() => {
    if (attemptId && messages.length > 0) {
      setCachedInterviewState({
        attemptId,
        messages,
        currentQuestion: messages[messages.length - 1]?.text || null,
        progress,
        lastUpdated: Date.now(),
      })
    }
  }, [attemptId, messages, progress, setCachedInterviewState])

  // 1. Fetch first question on mount or restore from cache
  useEffect(() => {
    if (!attemptId) {
      setError('Missing attempt ID in URL')
      setLoadingInitial(false)
      return
    }

    // Restore from local cache if matches attempt
    if (
      cachedInterviewState &&
      cachedInterviewState.attemptId === attemptId &&
      cachedInterviewState.messages.length > 0
    ) {
      setMessages(cachedInterviewState.messages)
      setProgress(cachedInterviewState.progress)
      setLoadingInitial(false)
      return
    }

    let isMounted = true

    async function loadFirstQuestion() {
      try {
        setLoadingInitial(true)
        setError(null)
        const res = await fetchApi<InterviewResponse>(
          `/api/attempts/${attemptId}/interview/next`,
          {
            method: 'POST',
            body: JSON.stringify({ answer: undefined }),
          }
        )

        if (!isMounted) return

        if (res.data) {
          setProgress(res.data.progress)
          if (res.data.question) {
            const firstMsg: ChatMessage = {
              id: `q-0`,
              sender: 'agent',
              text: res.data.question,
              timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
            }
            setMessages([firstMsg])
            speak(res.data.question)
          } else if (res.data.done) {
            clearCachedInterviewState()
            navigate(`/record/${attemptId}`)
          }
        }
      } catch (err: unknown) {
        if (!isMounted) return
        const msg = err instanceof Error ? err.message : 'Failed to connect to interview session'
        setError(msg)
      } finally {
        if (isMounted) setLoadingInitial(false)
      }
    }

    loadFirstQuestion()

    return () => {
      isMounted = false
    }
  }, [attemptId, cachedInterviewState, clearCachedInterviewState, navigate, speak])

  // 2. Submit user answer
  const handleSend = async () => {
    const trimmed = inputText.trim()
    if (!trimmed || evaluating || !attemptId) return

    if (!isOnline) {
      setError('You are offline. Your answers are saved locally and will sync when you reconnect.')
      return
    }

    // Stop listening if mic was running
    if (isListening) {
      stopListening()
    }

    const userMsg: ChatMessage = {
      id: `u-${Date.now()}`,
      sender: 'user',
      text: trimmed,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    }

    setMessages((prev) => [...prev, userMsg])
    setInputText('')
    setEvaluating(true)
    setError(null)

    // Simulate progressive agent logs for feedback
    setAgentLogs([
      'Worker response received',
      'Matching against blueprint scenario expected points...',
    ])

    try {
      const timer = setTimeout(() => {
        setAgentLogs((prev) => [...prev, 'Scoring technical accuracy and safety protocol...'])
      }, 500)

      const res = await fetchApi<InterviewResponse>(
        `/api/attempts/${attemptId}/interview/next`,
        {
          method: 'POST',
          body: JSON.stringify({ answer: trimmed }),
        }
      )

      clearTimeout(timer)

      if (res.data) {
        setProgress(res.data.progress)

        if (res.data.done) {
          clearCachedInterviewState()
          setAgentLogs((prev) => [
            ...prev,
            'All scenario questions verified.',
            'Interview complete! Transitioning to video demonstration.',
          ])
          const doneMsg: ChatMessage = {
            id: `done-${Date.now()}`,
            sender: 'agent',
            text: 'Excellent work. Your scenario interview is complete! Preparing your practical video assessment...',
            timestamp: new Date().toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            }),
          }
          setMessages((prev) => [...prev, doneMsg])
          speak(doneMsg.text)

          setTimeout(() => {
            navigate(`/record/${attemptId}`)
          }, 1400)
        } else if (res.data.question) {
          const nextMsg: ChatMessage = {
            id: `q-${Date.now()}`,
            sender: 'agent',
            text: res.data.question,
            timestamp: new Date().toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            }),
          }
          setMessages((prev) => [...prev, nextMsg])
          setAgentLogs([])
          speak(res.data.question)
        }
      }
    } catch (err: unknown) {
      const isNetErr =
        !navigator.onLine ||
        (err instanceof Error &&
          (err.message.toLowerCase().includes('fetch') ||
            err.message.toLowerCase().includes('network') ||
            err.message.toLowerCase().includes('failed to fetch')))
      const msg = isNetErr
        ? 'Network lost. Please wait...'
        : err instanceof Error
        ? err.message
        : 'Error submitting answer'
      setError(msg)
      // Keep typed answer in input box so it is not lost
      setInputText(trimmed)
      // Remove optimistic message that failed to send
      setMessages((prev) => prev.filter((m) => m.id !== userMsg.id))
      setAgentLogs([])
    } finally {
      setEvaluating(false)
    }
  }

  const toggleMic = () => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <PageTransition>
      <div className="min-h-screen bg-paper flex flex-col justify-between max-w-xl mx-auto px-4 py-4 md:py-8">
        {/* Top Header */}
        <header className="border-b border-ink/10 pb-4 mb-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="font-heading font-black text-lg text-ink">SAKSHI</span>
              <span className="text-ink/30">•</span>
              <Tag variant="accent">
                AI Interview
              </Tag>
            </div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs text-ink/50 uppercase">
                {language === 'hi' ? 'हिंदी' : language === 'kn' ? 'ಕನ್ನಡ' : 'EN'}
              </span>
            </div>
          </div>

          {/* Progress dots bar */}
          <div className="mt-4 flex items-center justify-between">
            <div className="flex items-center gap-1.5">
              {Array.from({ length: Math.max(progress.total, 1) }).map((_, i) => (
                <div
                  key={i}
                  className={`h-2 rounded-full transition-all duration-300 ${
                    i < progress.current - 1
                      ? 'w-5 bg-orange'
                      : i === progress.current - 1
                      ? 'w-7 bg-orange animate-pulse'
                      : 'w-2 bg-ink/20'
                  }`}
                />
              ))}
            </div>
            <span className="font-mono text-xs text-ink/60">
              Q{progress.current} of {progress.total}
            </span>
          </div>
        </header>

        {/* Offline Network Notification */}
        <OfflineBanner className="mb-4" />

        {/* Chat Stream Area */}
        <main className="flex-1 overflow-y-auto space-y-4 pr-1 mb-4">
          {loadingInitial && (
            <div className="space-y-4 pt-4">
              <Skeleton className="h-20 w-4/5 rounded-2xl" />
              <div className="flex justify-end">
                <Skeleton className="h-12 w-2/3 rounded-2xl" />
              </div>
            </div>
          )}

          {error && (
            <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm flex items-start gap-2">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <div className="flex-1">
                <p className="font-semibold">{error}</p>
                <p className="text-xs text-red-500 mt-1">Please check connection or retry.</p>
              </div>
            </div>
          )}

          <AnimatePresence initial={false}>
            {messages.map((m) => (
              <motion.div
                key={m.id}
                initial={{ opacity: 0, y: 10, scale: 0.98 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                transition={{ duration: 0.25 }}
                className={`flex gap-2.5 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.sender === 'agent' && (
                  <div className="w-8 h-8 rounded-full bg-orange/10 border border-orange/20 flex items-center justify-center shrink-0 mt-1">
                    <Bot className="w-4 h-4 text-orange" />
                  </div>
                )}

                <div
                  className={`relative max-w-[85%] rounded-2xl px-4 py-3 shadow-sm ${
                    m.sender === 'user'
                      ? 'bg-ink text-paper rounded-br-none font-sans text-sm'
                      : 'bg-white border border-ink/10 text-ink rounded-tl-none font-sans text-sm'
                  }`}
                >
                  <p className="leading-relaxed whitespace-pre-line">{m.text}</p>
                  <div className="mt-1.5 flex items-center justify-between gap-3 text-[10px] opacity-60">
                    <span>{m.timestamp}</span>
                    {m.sender === 'agent' && (
                      <button
                        onClick={() => speak(m.text)}
                        className="hover:text-orange transition-colors flex items-center gap-1 font-mono"
                        title="Replay Audio"
                      >
                        <Volume2 className="w-3 h-3" />
                        <span>Listen</span>
                      </button>
                    )}
                  </div>
                </div>

                {m.sender === 'user' && (
                  <div className="w-8 h-8 rounded-full bg-ink/10 flex items-center justify-center shrink-0 mt-1">
                    <User className="w-4 h-4 text-ink" />
                  </div>
                )}
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Evaluating Indicator & Agent Log */}
          {evaluating && (
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              className="space-y-2 pt-2"
            >
              <div className="flex items-center gap-2 text-xs font-mono text-orange">
                <Sparkles className="w-4 h-4 animate-spin" />
                <span>SAKSHI AI is evaluating your response...</span>
              </div>
              <AgentLog lines={agentLogs} title="Agent Reasoning" />
            </motion.div>
          )}

          <div ref={chatBottomRef} />
        </main>

        {/* Input & Speech Action Area */}
        <footer className="pt-2 border-t border-ink/10">
          {/* Live Voice Indicator Banner */}
          {isListening && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: 'auto' }}
              exit={{ opacity: 0, height: 0 }}
              className="mb-2 px-3 py-2 rounded-lg bg-orange/10 border border-orange/30 flex items-center justify-between text-xs font-mono text-orange"
            >
              <div className="flex items-center gap-2">
                <span className="flex items-center gap-0.5 h-3.5">
                  <motion.span
                    className="w-1 bg-orange rounded-full"
                    animate={{ height: ['4px', '14px', '4px'] }}
                    transition={{ repeat: Infinity, duration: 0.5, ease: 'easeInOut' }}
                  />
                  <motion.span
                    className="w-1 bg-orange rounded-full"
                    animate={{ height: ['8px', '16px', '6px'] }}
                    transition={{ repeat: Infinity, duration: 0.4, delay: 0.1, ease: 'easeInOut' }}
                  />
                  <motion.span
                    className="w-1 bg-orange rounded-full"
                    animate={{ height: ['3px', '12px', '3px'] }}
                    transition={{ repeat: Infinity, duration: 0.6, delay: 0.2, ease: 'easeInOut' }}
                  />
                </span>
                <span>Listening... Speak clearly in your selected language</span>
              </div>
              <span className="text-[10px] text-orange/70">Click mic or send when done</span>
            </motion.div>
          )}

          <div className="flex items-center gap-2">
            {/* Big Mic Button with Audio Wave Visualizer */}
            {speechSupported ? (
              <button
                type="button"
                onClick={toggleMic}
                disabled={evaluating}
                className={`relative w-12 h-12 rounded-full flex items-center justify-center transition-all shrink-0 ${
                  isListening
                    ? 'bg-orange text-paper shadow-lg shadow-orange/30'
                    : 'bg-ink/5 border border-ink/20 text-ink hover:bg-ink/10'
                } ${evaluating ? 'opacity-50 cursor-not-allowed' : ''}`}
                title={isListening ? 'Stop listening' : 'Start speaking'}
              >
                {/* Pulsing ring during recording */}
                {isListening && (
                  <span className="absolute -inset-1 rounded-full border-2 border-orange animate-ping opacity-60 pointer-events-none" />
                )}

                {isListening ? (
                  <div className="flex items-center justify-center gap-1 h-5 w-5">
                    <motion.span
                      className="w-1 bg-paper rounded-full"
                      animate={{ height: ['6px', '18px', '6px'] }}
                      transition={{ repeat: Infinity, duration: 0.55, ease: 'easeInOut' }}
                    />
                    <motion.span
                      className="w-1 bg-paper rounded-full"
                      animate={{ height: ['10px', '22px', '8px', '18px'] }}
                      transition={{ repeat: Infinity, duration: 0.45, ease: 'easeInOut', delay: 0.1 }}
                    />
                    <motion.span
                      className="w-1 bg-paper rounded-full"
                      animate={{ height: ['4px', '16px', '4px'] }}
                      transition={{ repeat: Infinity, duration: 0.65, ease: 'easeInOut', delay: 0.2 }}
                    />
                  </div>
                ) : (
                  <Mic className="w-5 h-5" />
                )}
              </button>
            ) : (
              <div
                className="w-12 h-12 rounded-full bg-ink/5 border border-ink/10 flex items-center justify-center text-ink/30 shrink-0"
                title="Microphone input not supported in this browser"
              >
                <MicOff className="w-5 h-5" />
              </div>
            )}

            {/* Input field */}
            <div className="relative flex-1">
              <input
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  isListening
                    ? 'Transcribing speech...'
                    : 'Type your answer or tap mic to speak...'
                }
                disabled={evaluating}
                className="w-full h-12 px-4 rounded-xl bg-white border border-ink/20 font-sans text-sm text-ink placeholder:text-ink/40 focus:outline-none focus:border-orange focus:ring-1 focus:ring-orange shadow-sm disabled:opacity-50"
              />
            </div>

            {/* Send Button */}
            <Button
              type="button"
              onClick={handleSend}
              disabled={!inputText.trim() || evaluating}
              variant="primary"
              className="h-12 px-5 rounded-xl shrink-0 !bg-orange text-paper hover:!bg-orange/90"
            >
              <Send className="w-4 h-4 mr-1.5" />
              <span>Send</span>
            </Button>
          </div>
        </footer>
      </div>
    </PageTransition>
  )
}
