import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        cream: '#FAF7F2',
        parchment: '#EDE0CC',
        ink: '#2C2317',
        amber: '#C17E3C',
        sienna: '#8B3A1A',
        panel: '#FDF5EB',
      },
      fontFamily: {
        lora: ['var(--font-lora)', 'Georgia', 'serif'],
        nunito: ['var(--font-nunito)', 'system-ui', 'sans-serif'],
      },
      keyframes: {
        progress: {
          '0%': { width: '4%' },
          '100%': { width: '95%' },
        },
      },
      animation: {
        '[progress_60s_linear_forwards]': 'progress 60s linear forwards',
      },
    },
  },
  plugins: [],
}

export default config
