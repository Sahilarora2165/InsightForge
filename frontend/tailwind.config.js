/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: 'class',
  theme: {
    extend: {
      fontFamily: {
        sans: ['Geist', 'Inter', 'system-ui', 'sans-serif'],
        mono: ['Geist Mono', 'JetBrains Mono', 'monospace'],
      },
      colors: {
        // InsightForge pitch black/white palette
        ink: {
          DEFAULT: '#000000',
          950: '#0a0a0a',
          900: '#111111',
          800: '#1a1a1a',
          700: '#222222',
          600: '#2a2a2a',
          500: '#333333',
          400: '#555555',
          300: '#888888',
          200: '#aaaaaa',
          100: '#cccccc',
          50:  '#f5f5f5',
        },
        snow: {
          DEFAULT: '#ffffff',
          900: '#f9f9f9',
          800: '#f3f3f3',
          700: '#eeeeee',
          600: '#e5e5e5',
          500: '#d4d4d4',
        },
        // Accent — single accent color only
        accent: {
          DEFAULT: '#ffffff',
          dim:     'rgba(255,255,255,0.6)',
          subtle:  'rgba(255,255,255,0.08)',
          border:  'rgba(255,255,255,0.12)',
        },
      },
      animation: {
        'fade-in':   'fadeIn 0.2s ease-out forwards',
        'fade-up':   'fadeUp 0.3s ease-out forwards',
        'slide-in':  'slideIn 0.2s ease-out forwards',
        'shimmer':   'shimmer 1.8s linear infinite',
        'count-up':  'countUp 0.6s ease-out forwards',
      },
      keyframes: {
        fadeIn:  { from: { opacity: '0' },                              to: { opacity: '1' } },
        fadeUp:  { from: { opacity: '0', transform: 'translateY(8px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        slideIn: { from: { opacity: '0', transform: 'translateX(-8px)' }, to: { opacity: '1', transform: 'translateX(0)' } },
        shimmer: { '0%': { backgroundPosition: '-200% 0' }, '100%': { backgroundPosition: '200% 0' } },
        countUp: { from: { opacity: '0', transform: 'translateY(6px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
      },
    },
  },
  plugins: [require('@tailwindcss/typography')],
}