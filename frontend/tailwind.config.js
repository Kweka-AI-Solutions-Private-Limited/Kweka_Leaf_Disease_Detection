/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        cream: {
          50: '#fcfaf7',
          100: '#f8f4ed',
          200: '#f3ebe0',
          300: '#e8dccb',
          400: '#d4c2aa',
        },
        brand: {
          50: '#fff6f0',
          100: '#fdeade',
          500: '#e07238',
          600: '#d96b27',
          700: '#b85119',
          800: '#8a3b11',
        },
        warmgray: {
          50: '#f9f8f6',
          100: '#f1eee9',
          200: '#e5e0d8',
          300: '#d1c9bd',
          400: '#a3998b',
          500: '#787168',
          600: '#575149',
          700: '#403b35',
          800: '#2b2723',
          900: '#1c1917',
        },
        reject: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fca5a5',
          300: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
        }
      },
      fontFamily: {
        sans: ['Plus Jakarta Sans', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
