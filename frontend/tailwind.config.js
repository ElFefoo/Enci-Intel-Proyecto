/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        teal: {
          50:  '#f0fafa',
          100: '#cceeee',
          600: '#01696f',
          700: '#01696f',
          800: '#0c4e54',
        },
      },
    },
  },
  plugins: [],
}
