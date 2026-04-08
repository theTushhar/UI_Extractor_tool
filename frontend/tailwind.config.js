/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        bg: {
          base: "#0a0f1e",
          surface: "#111827",
          elevated: "#1a2235",
          border: "#1f2937",
          hover: "#1e2d3d",
        },
        primary: {
          DEFAULT: "#6366f1",
          light: "#818cf8",
          dark: "#4f46e5",
        },
        accent: {
          DEFAULT: "#06b6d4",
          light: "#22d3ee",
          dark: "#0891b2",
        },
        mode: {
          input: "#10b981",
          action: "#6366f1",
          output: "#f59e0b",
          unknown: "#6b7280",
        },
        score: {
          high: "#10b981",
          mid: "#f59e0b",
          low: "#ef4444",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "Fira Code", "monospace"],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-out",
        "slide-in-right": "slideInRight 0.35s ease-out",
        "slide-up": "slideUp 0.25s ease-out",
        "count-up": "countUp 0.5s ease-out",
        "pulse-soft": "pulseSoft 2s ease-in-out infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        slideInRight: {
          "0%": { opacity: "0", transform: "translateX(100%)" },
          "100%": { opacity: "1", transform: "translateX(0)" },
        },
        slideUp: {
          "0%": { opacity: "0", transform: "translateY(16px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        pulseSoft: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.7" },
        },
      },
      boxShadow: {
        card: "0 0 0 1px rgba(99, 102, 241, 0.08), 0 4px 24px rgba(0,0,0,0.4)",
        glow: "0 0 20px rgba(99, 102, 241, 0.25)",
        "glow-accent": "0 0 20px rgba(6, 182, 212, 0.25)",
      },
    },
  },
  plugins: [],
};
