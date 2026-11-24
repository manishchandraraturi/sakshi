import { WifiOff } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useNetworkStatus } from '../hooks/useNetworkStatus'

interface OfflineBannerProps {
  message?: string
  className?: string
}

export function OfflineBanner({
  message = 'You are offline. Your answers are saved locally and will sync when you reconnect.',
  className = '',
}: OfflineBannerProps) {
  const isOnline = useNetworkStatus()

  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ opacity: 0, y: -16 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -16 }}
          transition={{ duration: 0.25 }}
          className={`w-full bg-amber-600 text-paper px-4 py-2.5 rounded-xl flex items-center justify-center gap-2.5 text-xs font-semibold shadow-md border border-amber-700/30 ${className}`}
        >
          <WifiOff className="w-4 h-4 shrink-0 animate-pulse text-amber-200" />
          <span className="leading-snug">{message}</span>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default OfflineBanner
