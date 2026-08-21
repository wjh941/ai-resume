import { defineConfig, loadEnv } from "vite"
import uni from "@dcloudio/vite-plugin-uni"

const isVitest = process.env.VITEST === "true"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  const localApiTarget =
    env.VITE_RESUME_API_URL || env.RESUME_API_URL || "http://127.0.0.1:8000"
  return {
    plugins: isVitest ? [] : [uni()],
    publicDir: "public",
    server: {
      host: "127.0.0.1",
      port: 5186,
      strictPort: true,
      proxy: {
        "/api": localApiTarget,
        "/downloads": localApiTarget,
        "/health": localApiTarget,
      },
    },
    test: {
      environment: "node",
      include: ["src/tests/**/*.spec.ts"],
    },
  }
})
