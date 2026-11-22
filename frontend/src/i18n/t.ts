import { useSessionStore } from '../store/session'
import en from './en.json'
import hi from './hi.json'
import kn from './kn.json'

const translations: Record<string, Record<string, string>> = {
  en,
  hi,
  kn,
}

export function useTranslation() {
  const language = useSessionStore((state) => state.language)

  const t = (key: string, fallback?: string): string => {
    const dict = translations[language] || translations.en
    return dict[key] ?? translations.en[key] ?? fallback ?? key
  }

  return { t, language }
}
