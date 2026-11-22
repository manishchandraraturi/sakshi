import { create } from 'zustand'

export type Language = 'en' | 'hi' | 'kn'

export interface SessionState {
  language: Language
  workerToken: string | null
  workerId: string | null
  attemptId: string | null
  setLanguage: (lang: Language) => void
  setWorkerToken: (token: string | null, workerId?: string | null) => void
  setAttemptId: (attemptId: string | null) => void
  resetSession: () => void
}

export const useSessionStore = create<SessionState>((set) => ({
  language: 'en',
  workerToken: null,
  workerId: null,
  attemptId: null,
  setLanguage: (language) => set({ language }),
  setWorkerToken: (workerToken, workerId = null) => set({ workerToken, workerId }),
  setAttemptId: (attemptId) => set({ attemptId }),
  resetSession: () => set({ language: 'en', workerToken: null, workerId: null, attemptId: null }),
}))
