/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './app/**/*.{js,jsx,ts,tsx}',
    './components/**/*.{js,jsx,ts,tsx}',
  ],
  presets: [require('nativewind/preset')],
  theme: {
    extend: {
      colors: {
        primary: '#0a192f',
        'primary-light': '#112240',
        accent: '#64ffda',
        'accent-dark': '#4cd6b0',
        surface: '#1d3461',
        'text-primary': '#ccd6f6',
        'text-secondary': '#8892b0',
        'text-muted': '#495670',
        success: '#64ffda',
        warning: '#ffd166',
        error: '#ff6b6b',
      },
    },
  },
  plugins: [],
};
