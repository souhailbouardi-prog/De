import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

/**
 * In production, hermes_cli.web_server injects the session token into
 * index.html as it serves the SPA. In dev we're served by Vite directly,
 * so the token never gets there. This plugin reads HERMES_DASHBOARD_DEV_TOKEN
 * and injects the same shape, matching the production bootstrap so the
 * gateway client and api.ts don't need a dev-mode branch.
 */
function injectDevToken(): Plugin {
  return {
    name: "hermes-dashboard-dev-token",
    transformIndexHtml() {
      const token = process.env.HERMES_DASHBOARD_DEV_TOKEN;
      if (!token) return;
      return [
        {
          tag: "script",
          injectTo: "head",
          children: `window.__HERMES_SESSION_TOKEN__=${JSON.stringify(token)};`,
        },
      ];
    },
  };
}

export default defineConfig({
  plugins: [react(), tailwindcss(), injectDevToken()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  build: {
    outDir: "../hermes_cli/web_dist",
    emptyOutDir: true,
  },
  server: {
    proxy: {
      // REST endpoints + the /api/ws WebSocket (ws: true enables upgrade forwarding).
      "/api": {
        target: "http://127.0.0.1:9119",
        ws: true,
      },
    },
  },
});
