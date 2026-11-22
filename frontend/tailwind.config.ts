import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          DEFAULT: '#0A0A0A',
          2: '#171717',
          3: '#2A2A2A',
        },
        paper: {
          DEFAULT: '#F6F3EC',
          2: '#EDE9DF',
        },
        accent: {
          DEFAULT: '#FF7A1A',
        },
        danger: {
          DEFAULT: '#B42318',
        },
        muted: {
          DEFAULT: '#6B6B66',
          dark: '#A3A39B',
        },
        line: {
          DEFAULT: 'rgba(10, 10, 10, 0.10)',
          dark: 'rgba(246, 243, 236, 0.14)',
        },
      },
      fontFamily: {
        display: ['Syne', 'Noto Sans Devanagari', 'Noto Sans Kannada', 'system-ui', 'sans-serif'],
        body: ['"Space Grotesk"', 'Noto Sans Devanagari', 'Noto Sans Kannada', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      borderRadius: {
        xl2: '28px',
        '2xl': '28px',
        lg: '28px',
        md: '18px',
        sm: '12px',
        pill: '999px',
      },
    },
  },
  plugins: [],
} satisfies Config
