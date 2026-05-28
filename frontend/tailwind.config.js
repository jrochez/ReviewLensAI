/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./src/**/*.{js,ts,jsx,tsx,mdx}'],
  theme: {
    extend: {
      colors: {
        accent: {
          DEFAULT: '#2563EB',
          hover: '#1D4ED8',
          subtle: '#EFF6FF',
        },
        surface: '#F9FAFB',
        raised: '#F3F4F6',
        border: {
          DEFAULT: '#E5E7EB',
          strong: '#D1D5DB',
        },
        text: {
          primary: '#111827',
          secondary: '#6B7280',
          disabled: '#9CA3AF',
        },
        success: { DEFAULT: '#16A34A', bg: '#F0FDF4' },
        warning: { DEFAULT: '#D97706', bg: '#FFFBEB' },
        error: { DEFAULT: '#DC2626', bg: '#FEF2F2' },
        neutral: '#6B7280',
        'scope-guard': { bg: '#F3F4F6', border: '#D1D5DB' },
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'monospace'],
      },
    },
  },
  plugins: [],
}
