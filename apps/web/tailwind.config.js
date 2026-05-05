/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bean: {
          50: "#fbf6f1",
          100: "#f3e7d8",
          500: "#a16a4a",
          700: "#5b3522",
          900: "#1f0f08",
        },
      },
      fontFamily: {
        display: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
