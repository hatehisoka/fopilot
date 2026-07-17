import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// /api проксі-таргет: локально це http://localhost:8000, у docker compose —
// http://backend:8000 (внутрішнє DNS-ім'я, доступне dev-серверу в контейнері,
// але не браузеру). Тому браузер завжди ходить на /api свого origin.
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const target = env.VITE_API_PROXY_TARGET || "http://localhost:8000";
  return {
    plugins: [react()],
    server: {
      host: true,
      port: 5173,
      proxy: {
        "/api": {
          target,
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ""),
        },
      },
    },
  };
});
