import { motion } from 'framer-motion'
import { ShieldCheck, ShieldAlert } from 'lucide-react'

interface VerifyBannerProps {
  isValid: boolean
  className?: string
}

export default function VerifyBanner({ isValid, className = '' }: VerifyBannerProps) {
  if (isValid) {
    return (
      <motion.div
        initial={{ opacity: 0, y: -8 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-4 rounded-2xl bg-paper border-2 border-orange/40 shadow-sm flex items-center gap-3.5 ${className}`}
      >
        <div className="w-11 h-11 rounded-xl bg-orange/15 border border-orange/30 flex items-center justify-center text-orange shrink-0">
          <ShieldCheck className="w-6 h-6" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="font-heading font-black text-sm md:text-base text-ink tracking-tight uppercase">
              Signature Valid
            </span>
            <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          </div>
          <p className="font-mono text-[11px] text-ink/70 leading-snug mt-0.5">
            Verified in-browser with TweetNaCl. Canonical JSON digest matches Ed25519 public key.
          </p>
        </div>
      </motion.div>
    )
  }

  return (
    <motion.div
      initial={{ scale: 0.95 }}
      animate={{
        x: [0, -12, 12, -8, 8, -4, 4, 0],
        scale: 1,
      }}
      transition={{ duration: 0.5, ease: 'easeInOut' }}
      className={`p-4 rounded-2xl bg-red-500/10 border-2 border-red-500 shadow-sm flex items-center gap-3.5 ${className}`}
    >
      <div className="w-11 h-11 rounded-xl bg-red-500/20 border border-red-500/40 flex items-center justify-center text-red-600 shrink-0">
        <ShieldAlert className="w-6 h-6" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="font-heading font-black text-sm md:text-base text-red-600 tracking-tight uppercase">
            Signature Invalid — Tamper Detected
          </span>
        </div>
        <p className="font-mono text-[11px] text-red-700/80 leading-snug mt-0.5">
          Data alteration detected. The payload bytes do not match the cryptographic signature.
        </p>
      </div>
    </motion.div>
  )
}
