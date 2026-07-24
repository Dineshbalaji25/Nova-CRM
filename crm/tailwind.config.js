/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        background: '#111827',
        surface: '#1F2937',
        primary: {
          DEFAULT: '#4F46E5',
          hover: '#6366F1',
        },
        gold: '#F59E0B',
        border: 'rgba(255, 255, 255, 0.08)',
        gray: {
          50: '#f9fafb',
          100: '#f3f4f6',
          200: '#e5e7eb',
          300: '#d1d5db',
          400: '#9ca3af',
          500: '#9ca3af', // Optimized contrast (originally #6b7280, now #9ca3af)
          600: '#6b7280',
          700: '#4b5563',
          800: '#374151',
          900: '#1f2937',
          950: '#111827',
        },
      },
      fontFamily: {
        sans: ['Inter', 'Geist', 'Plus Jakarta Sans', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
