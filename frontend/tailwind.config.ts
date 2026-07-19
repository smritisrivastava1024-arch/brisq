import type { Config } from 'tailwindcss'

export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Auralis Dark Theme Colors
        background: '#0B0F19', // Deep obsidian
        surface: '#111827',    // Slate 900
        'surface-lighter': '#1F2937', // Slate 800
        primary: '#8B5CF6',    // Violet 500
        'primary-hover': '#7C3AED', // Violet 600
        secondary: '#0EA5E9',  // Sky 500
        accent: '#F43F5E',     // Rose 500
        'text-main': '#F9FAFB', // Gray 50
        'text-muted': '#9CA3AF', // Gray 400
        'text-dim': '#6B7280',   // Gray 500
        
        // Status Colors
        success: '#10B981', // Emerald 500
        danger: '#EF4444',  // Red 500
        warning: '#F59E0B', // Amber 500
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'Consolas', 'monospace'],
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'glass-gradient': 'linear-gradient(145deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%)',
        'primary-gradient': 'linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%)',
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.1)',
        'glow': '0 0 20px rgba(139, 92, 246, 0.3)',
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
} satisfies Config
