import { defineConfig, loadEnv } from "vite"
import vue from "@vitejs/plugin-vue"

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "")
  const apiTarget = env.VITE_API_BASE_URL || "http://127.0.0.1:8000"

  return {
    plugins: [vue()],
    build: {
      rollupOptions: {
        output: {
          // 把不常变动的框架与图标库拆成独立 chunk：业务迭代重新发版后，
          // 用户浏览器仍能命中这两块的长期缓存，二次访问显著提速。
          manualChunks: {
            "vendor-vue": ["vue"],
            "vendor-icons": ["lucide-vue-next"],
          },
        },
      },
    },
    server: {
      host: "127.0.0.1",
      port: 5174,
      strictPort: true,
      proxy: {
        "/api": apiTarget,
        "/downloads": apiTarget,
        "/health": apiTarget,
      },
    },
  }
})
