/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Sophisticated navy & coral palette
        bg: {
          main: '#0B1120',
          card: 'rgba(15, 23, 42, 0.7)',
          sidebar: 'rgba(18, 27, 47, 0.85)',
        },
        primary: {
          50: '#fef3f2',
          100: '#ffe4e1',
          200: '#fecdcb',
          300: '#fdaba4',
          400: '#fa7970',
          500: '#f15147',
          600: '#de3730',
          700: '#bc2820',
          800: '#9b241f',
          900: '#80241f',
        },
        accent: {
          coral: '#FA7970',
          teal: '#2DD4BF',
          purple: '#A78BFA',
          amber: '#FBBF24',
        },
        navy: {
          50: '#f0f4f8',
          100: '#d9e2ec',
          200: '#bcccdc',
          300: '#9fb3c8',
          400: '#829ab1',
          500: '#627d98',
          600: '#486581',
          700: '#334e68',
          800: '#243b53',
          900: '#102a43',
        }
      },
      fontFamily: {
        heading: ['Inter', 'sans-serif'],
        body: ['Inter', 'sans-serif'],
        mono: ['JetBrains Mono', 'Courier New', 'monospace'],
      },
      backdropBlur: {
        'glass': '16px',
      },
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-soft': 'pulse-soft 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        float: {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'pulse-soft': {
          '0%, 100%': { opacity: 1 },
          '50%': { opacity: 0.7 },
        }
      }
    },
  },
  plugins: [],
}