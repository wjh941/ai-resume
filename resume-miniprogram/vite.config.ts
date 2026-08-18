import { defineConfig, loadEnv } from "vite"
import uni from "@dcloudio/vite-plugin-uni"
import { readFileSync } from "node:fs"
import { resolve } from "node:path"

const isVitest = process.env.VITEST === "true"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  const localApiTarget =
    env.VITE_RESUME_API_URL || env.RESUME_API_URL || "http://127.0.0.1:8000"
  const premiumDashboardPath = resolve(process.cwd(), "..", "premium-dashboard.html")

  return {
    plugins: isVitest ? [] : [
      uni(),
      {
        name: "serve-premium-dashboard",
        configureServer(server) {
          server.middlewares.use("/premium-dashboard.html", (request, response, next) => {
            if (request.method !== "GET") return next()
            response.setHeader("Content-Type", "text/html; charset=utf-8")
            response.end(readFileSync(premiumDashboardPath, "utf8"))
          })
        }
      }
    ],
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
