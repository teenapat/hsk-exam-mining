import type { Config } from "tailwindcss";

export default {
  darkMode: ["class"],
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        background: "#070b14",
        panel: "#101827",
        panelMuted: "#111c2f",
        border: "#24324a",
        text: "#e2e8f0",
        textMuted: "#93a4c3",
        primary: "#3b82f6",
        success: "#22c55e",
        warning: "#f59e0b",
        danger: "#ef4444"
      },
      boxShadow: {
        glow: "0 0 0 1px rgba(59,130,246,0.3), 0 12px 40px rgba(15,23,42,0.45)"
      }
    }
  },
  plugins: []
} satisfies Config;

