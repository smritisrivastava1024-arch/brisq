import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Minimalist Beige/Brown Theme Colors
        background: '#FAF8F5', // Soft warm beige
        surface: '#FFFFFF',    // Crisp white
        'surface-lighter': '#F5F2EB', // Slightly darker beige
        
        primary: '#5C4033',    // Dark brown
        'primary-hover': '#422E25', // Darker brown
        secondary: '#8B7355',  // Lighter brown
        accent: '#D4A373',     // Warm accent
        
        'text-main': '#2C2621', // Very dark brown/off-black
        'text-muted': '#7E736A', // Mid-brown
        'text-dim': '#A0968E',   // Grey-brown
        
        // Status Colors (Muted Pastels for minimalist look)
        success: '#829C8B', // Muted sage green
        danger: '#B37D7D',  // Muted brick red
        warning: '#C4A47C', // Muted tan/ochre
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      boxShadow: {
        'sm': '0 1px 2px rgba(92, 64, 51, 0.05)',
        'md': '0 4px 6px -1px rgba(92, 64, 51, 0.05), 0 2px 4px -1px rgba(92, 64, 51, 0.03)',
        'lg': '0 10px 15px -3px rgba(92, 64, 51, 0.05), 0 4px 6px -2px rgba(92, 64, 51, 0.03)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
} satisfies Config
