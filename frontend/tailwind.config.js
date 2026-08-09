/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          DEFAULT: "#0a0a0b",
          panel: "#111114",
          card: "#16161a",
          hover: "#1c1c22",
        },
        border: {
          DEFAULT: "#232328",
          strong: "#2e2e36",
        },
        ink: {
          DEFAULT: "#f4f4f5",
          muted: "#a1a1aa",
          subtle: "#71717a",
        },
        accent: {
          DEFAULT: "#3b82f6",
          hover: "#2563eb",
          subtle: "#1e3a8a",
        },
      },
      boxShadow: {
        card: "0 1px 2px rgba(0,0,0,.3), 0 4px 12px rgba(0,0,0,.15)",
      },
      fontFamily: {
        sans: [
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "Segoe UI",
          "Inter",
          "Roboto",
          "sans-serif",
        ],
      },
    },
  },
  plugins: [],
};
