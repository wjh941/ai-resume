import { defineConfig } from "vite"

export default defineConfig({
  test: {
    environment: "node",
    include: ["src/tests/**/*.spec.ts"],
  },
})
