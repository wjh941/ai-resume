import { existsSync, rmSync } from "node:fs"
import { resolve } from "node:path"
import { defineConfig, loadEnv, type Plugin } from "vite"
import uni from "@dcloudio/vite-plugin-uni"

const isVitest = process.env.VITEST === "true"

// H5 专用静态页（独立 HTML 工作台）只应出现在 H5 产物中；
// 小程序主包按目录整体上传，这些文件属于纯死重（约占主包 48%）。
const H5_ONLY_PUBLIC_ASSETS = ["premium-dashboard.html", "dashboard-report-tier.js"]

function stripH5OnlyPublicAssets(): Plugin {
  let outDir = ""
  return {
    name: "strip-h5-only-public-assets",
    apply: "build",
    enforce: "post",
    configResolved(config) {
      outDir = resolve(config.root, config.build.outDir)
    },
    closeBundle() {
      if (process.env.UNI_PLATFORM !== "mp-weixin") return
      for (const name of H5_ONLY_PUBLIC_ASSETS) {
        const target = resolve(outDir, name)
        if (existsSync(target)) rmSync(target)
      }
    },
  }
}

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  const localApiTarget =
    env.VITE_RESUME_API_URL || env.RESUME_API_URL || "http://127.0.0.1:8000"
  return {
    plugins: isVitest ? [] : [uni(), stripH5OnlyPublicAssets()],
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
