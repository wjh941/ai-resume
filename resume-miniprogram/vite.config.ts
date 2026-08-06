import { defineConfig } from "vite"
import uni from "@dcloudio/vite-plugin-uni"

const isVitest = process.env.VITEST === "true"

export default defineConfig({
  plugins: isVitest ? [] : [uni()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": "http://127.0.0.1:8000",
      "/downloads": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "node",
    include: ["src/tests/**/*.spec.ts"],
  },
})
