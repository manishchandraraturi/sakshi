import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type Language = 'en' | 'hi' | 'kn'

export interface CachedChatMessage {
  id: string
  sender: 'agent' | 'user'
  text: string
  timestamp: string
}

export interface CachedInterviewState {
  attemptId: string
  messages: CachedChatMessage[]
  currentQuestion: string | null
  progress: { current: number; total: number }
  lastUpdated: number
}

export interface SessionState {
  language: Language
  workerToken: string | null
  workerId: string | null
  attemptId: string | null
  cachedInterviewState: CachedInterviewState | null
  setLanguage: (lang: Language) => void
  setWorkerToken: (token: string | null, workerId?: string | null) => void
  setAttemptId: (attemptId: string | null) => void
  setCachedInterviewState: (cached: CachedInterviewState | null) => void
  clearCachedInterviewState: () => void
  resetSession: () => void
}

export const useSessionStore = create<SessionState>()(
  persist(
    (set) => ({
      language: 'en',
      workerToken: null,
      workerId: null,
      attemptId: null,
      cachedInterviewState: null,
      setLanguage: (language) => set({ language }),
      setWorkerToken: (workerToken, workerId = null) => set({ workerToken, workerId }),
      setAttemptId: (attemptId) => set({ attemptId }),
      setCachedInterviewState: (cachedInterviewState) => set({ cachedInterviewState }),
      clearCachedInterviewState: () => set({ cachedInterviewState: null }),
      resetSession: () =>
        set({
          language: 'en',
          workerToken: null,
          workerId: null,
          attemptId: null,
          cachedInterviewState: null,
        }),
    }),
    {
      name: 'sakshi-session-storage',
    }
  )
)
