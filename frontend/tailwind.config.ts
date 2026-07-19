import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        'ink-navy': '#141B2E',
        'parchment': '#EDE7D9',
        'parchment-dim': '#DCD4C0',
        'signal-gold': '#C99A3B',
        'verdigris': '#4C7A5E',
        'rust': '#B4483D',
        'ink-navy-80': 'rgba(20, 27, 46, 0.8)',
      },
      fontFamily: {
        display: ['Fraunces', 'serif'],
        body: ['IBM Plex Sans', 'sans-serif'],
        mono: ['IBM Plex Mono', 'monospace'],
      },
      borderRadius: {
        ledger: '6px',
      }
    },
  },
  plugins: [],
} satisfies Config
