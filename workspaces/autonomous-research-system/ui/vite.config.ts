import { defineConfig } from "vite";
export default defineConfig({
  base: "/workspaces/autonomous-research-system/ui/dist/",
  server: { proxy: { "/api": "http://127.0.0.1:18767" } },
  build: { chunkSizeWarningLimit: 1000 },
});
