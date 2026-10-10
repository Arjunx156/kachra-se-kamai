/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        leaf: { DEFAULT: '#1F5F3F', 50: '#EEF5F0', 100: '#D5E8DC', 200: '#A9CFB7', 600: '#1F5F3F', 700: '#17482F', 800: '#103322' },
        marigold: { DEFAULT: '#F2A900', 50: '#FEF6E0', 100: '#FDEBB8', 600: '#C98C00', 700: '#8F6400' },
        slate: { DEFAULT: '#334155' },
        cream: { DEFAULT: '#FAF7F0', 200: '#F1EBDD', 300: '#E6DDC8' },
        clay: { DEFAULT: '#C2410C', 50: '#FDEEE6', 600: '#C2410C', 700: '#9A3412' },
        compost: { DEFAULT: '#8B6B4A', 50: '#F4EEE7' },
      },
      fontFamily: {
        display: ['"Baloo 2"', 'system-ui', 'sans-serif'],
        sans: ['Mukta', 'system-ui', 'sans-serif'],
      },
      boxShadow: {
        card: '0 1px 2px rgba(51,65,85,0.06), 0 4px 16px rgba(51,65,85,0.06)',
      },
    },
  },
  plugins: [],
}
