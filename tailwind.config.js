/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        defense: {
          950: "#090D16",
          900: "#0F172A",
          850: "#1E293B",
          800: "#334155",
          700: "#475569",
          emerald: "#10B981",
          amber: "#F59E0B",
          rose: "#F43F5E",
          cyan: "#06B6D4",
        }
      }
    },
  },
  plugins: [],
}
