import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";
import { loadEnv } from "vite";

function envPort(value: string | undefined, fallback: number): number {
  if (!value) {
    return fallback;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : fallback;
}

export default defineConfig(({ mode }) => {
  const repoRoot = new URL("..", import.meta.url).pathname;
  const env = loadEnv(mode, repoRoot, ["NEWS_SCRAPER_", "VITE_"]);
  const backendHost = env.NEWS_SCRAPER_BACKEND_HOST || "127.0.0.1";
  const backendPort = envPort(env.NEWS_SCRAPER_BACKEND_PORT, 8000);
  const frontendPort = envPort(env.NEWS_SCRAPER_FRONTEND_PORT, 5173);

  return {
    plugins: [react()],
    server: {
      port: frontendPort,
      proxy: {
        "/api": `http://${backendHost}:${backendPort}`
      }
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: "./src/setupTests.ts"
    }
  };
});
