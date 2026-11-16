/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: '#0d5c56', // deep teal (sea/coast)
          dark: '#083c38',
          light: '#167d75',
        },
        agri: {
          DEFAULT: '#2e7d32', // leaf green
          dark: '#1b5e20',
          light: '#4caf50',
        },
        warning: {
          DEFAULT: '#d97706', // warm amber
          light: '#f59e0b',
        },
        danger: {
          DEFAULT: '#dc2626', // signal red
          light: '#ef4444',
        }
      },
      fontFamily: {
        sans: ['Inter', 'Noto Sans Oriya', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
