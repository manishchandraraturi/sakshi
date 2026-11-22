import { motion } from 'framer-motion'

interface SealProps {
  tier: number
  size?: number
  className?: string
}

export default function Seal({ tier, size = 160, className = '' }: SealProps) {
  const tierLabels: Record<number, string> = {
    0: 'NEEDS RETRY',
    1: 'DEMONSTRATED',
    2: 'WITNESSED',
    3: 'TRUSTED',
  }

  const label = tierLabels[tier] || 'VERIFIED'
  const isHighTier = tier >= 2

  return (
    <motion.div
      initial={{ scale: 0.75, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{
        type: 'spring',
        stiffness: 240,
        damping: 18,
        delay: 0.1,
      }}
      className={`relative inline-flex items-center justify-center ${className}`}
      style={{ width: size, height: size }}
    >
      <svg
        viewBox="0 0 160 160"
        width={size}
        height={size}
        className="w-full h-full select-none"
      >
        {/* Outer subtle shadow/glow */}
        <circle
          cx="80"
          cy="80"
          r="74"
          fill="#0A0A0A"
          stroke="#FF7A1A"
          strokeWidth="1.5"
          strokeOpacity="0.3"
        />

        {/* Decorative Dashed Ring */}
        <circle
          cx="80"
          cy="80"
          r="68"
          fill="none"
          stroke="#FF7A1A"
          strokeWidth="1.5"
          strokeDasharray="4 3"
          strokeOpacity="0.6"
        />

        {/* Primary Animated Drawing Ring */}
        <motion.circle
          cx="80"
          cy="80"
          r="60"
          fill="none"
          stroke="#FF7A1A"
          strokeWidth="3.5"
          strokeLinecap="round"
          initial={{ pathLength: 0, rotate: -90 }}
          animate={{ pathLength: 1, rotate: 270 }}
          transition={{
            duration: 1.2,
            ease: [0.16, 1, 0.3, 1], // snappy easeOutExpo
          }}
          style={{ originX: '80px', originY: '80px' }}
        />

        {/* Inner Solid Seal Plate */}
        <circle
          cx="80"
          cy="80"
          r="54"
          fill="#171717"
          stroke="#FF7A1A"
          strokeWidth="1"
          strokeOpacity="0.4"
        />

        {/* Top Arc Text Guide or Small Header */}
        <text
          x="80"
          y="50"
          textAnchor="middle"
          fill="#FF7A1A"
          fontSize="9"
          fontWeight="700"
          letterSpacing="2"
          className="font-mono uppercase select-none"
        >
          SAKSHI SEAL
        </text>

        {/* Big Tier Number in Center (Syne Font) */}
        <text
          x="80"
          y="88"
          textAnchor="middle"
          fill="#F6F3EC"
          fontSize="36"
          fontWeight="900"
          className="font-heading select-none"
          style={{ fontFamily: 'Syne, sans-serif' }}
        >
          {tier}
        </text>

        {/* Bottom Tier Title */}
        <text
          x="80"
          y="110"
          textAnchor="middle"
          fill={isHighTier ? '#FF7A1A' : '#F6F3EC'}
          fontSize="8.5"
          fontWeight="800"
          letterSpacing="1.5"
          className="font-mono uppercase select-none"
        >
          {label}
        </text>

        {/* Decorative Stars / Dots for Tier 3 */}
        {tier === 3 && (
          <>
            <circle cx="50" cy="80" r="2" fill="#FF7A1A" />
            <circle cx="110" cy="80" r="2" fill="#FF7A1A" />
          </>
        )}
      </svg>
    </motion.div>
  )
}
