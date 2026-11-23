import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { SectionIndex } from '../components/ui/SectionIndex'
import { PageTransition } from '../components/PageTransition'
import { Button } from '../components/ui/Button'
import { Language as LangType, useSessionStore } from '../store/session'
import { useTranslation } from '../i18n/t'

interface LanguageOption {
  code: LangType
  label: string
  sub: string
  fontClass?: string
}

const LANGUAGES: LanguageOption[] = [
  { code: 'en', label: 'English', sub: 'Practical test in English' },
  { code: 'hi', label: 'हिन्दी', sub: 'हिंदी में व्यावहारिक परीक्षण', fontClass: 'font-display' },
  { code: 'kn', label: 'ಕನ್ನಡ', sub: 'ಕನ್ನಡದಲ್ಲಿ ಪ್ರಾಯೋಗಿಕ ಪರೀಕ್ಷೆ', fontClass: 'font-display' },
]

export default function Language() {
  const navigate = useNavigate()
  const { setLanguage, language: currentLang } = useSessionStore()
  const { t } = useTranslation()

  const handleSelect = (code: LangType) => {
    setLanguage(code)
    navigate('/skill')
  }

  return (
    <PageTransition className="min-h-screen flex flex-col items-center justify-center p-6 text-center">
      <div className="max-w-lg w-full mx-auto space-y-8">
        <div className="flex items-center justify-between">
          <SectionIndex index="01" title="LANGUAGE" />
          <Button
            variant="primary"
            onClick={() => {
              if (window.history.length > 1) {
                navigate(-1)
              } else {
                navigate('/')
              }
            }}
            className="!px-4 !py-1.5 !text-xs !h-8 font-mono rounded-pill !bg-ink text-paper hover:!bg-ink/85 shadow-sm"
          >
            Back
          </Button>
        </div>

        <div className="space-y-3">
          <h1 className="text-4xl sm:text-5xl font-display font-extrabold text-ink tracking-tight">
            {t('choose_language')}
            <span className="text-accent">.</span>
          </h1>
          <p className="font-body text-sm sm:text-base text-muted max-w-sm mx-auto">
            {t('choose_language_sub')}
          </p>
        </div>

        {/* 3 big pill cards */}
        <div className="space-y-4 pt-2">
          {LANGUAGES.map((lang) => {
            const isSelected = currentLang === lang.code
            return (
              <motion.button
                key={lang.code}
                onClick={() => handleSelect(lang.code)}
                whileHover={{ y: -4 }}
                whileTap={{ y: 0 }}
                transition={{ duration: 0.15, ease: [0.22, 1, 0.36, 1] }}
                className={`w-full py-5 px-6 rounded-pill border text-left flex items-center justify-between transition-all duration-200 cursor-pointer ${
                  isSelected
                    ? 'bg-ink text-paper border-ink shadow-md'
                    : 'bg-paper-2/80 text-ink border-line hover:border-ink/40 hover:bg-paper-2'
                }`}
              >
                <div>
                  <div className={`text-2xl font-bold leading-none ${lang.fontClass || 'font-body'}`}>
                    {lang.label}
                  </div>
                  <div
                    className={`text-xs mt-1 font-mono tracking-wider ${
                      isSelected ? 'text-paper/70' : 'text-muted'
                    }`}
                  >
                    {lang.sub}
                  </div>
                </div>
                <div
                  className={`w-6 h-6 rounded-full border flex items-center justify-center text-xs font-mono ${
                    isSelected ? 'border-accent bg-accent text-ink font-bold' : 'border-line text-transparent'
                  }`}
                >
                  ✓
                </div>
              </motion.button>
            )
          })}
        </div>
      </div>
    </PageTransition>
  )
}
