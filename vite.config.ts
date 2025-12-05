import { defineConfig, Plugin } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { createServer } from "./server";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    proxy: {
      "/api": {
        target:
          "0afc14b4-a602-41fd-b6d9-5093e1392d11-00-2ergle1nzcrwb.pike.replit.dev:8000",
        changeOrigin: true,
        secure: false, // 👈 ignore cert issues
      },
    },
    watch: {
      usePolling: true,
    },
    host: "0.0.0.0",
    port: 5000,
    allowedHosts: [
      "c94fd538-4553-4c81-9e4a-ee591eadfebc-00-3tm0zpl8m3mzx.spock.repl.co",
      "1534e4c1-a23f-4c1b-b31e-e237be812a57-00-1urwepnccdrhg.pike.replit.dev",
      "*",
      "c94fd538-4553-4c81-9e4a-ee591eadfebc-00-3tm0zpl8m3mzx.spock.replit.dev",
      "localhost",
      "http://172.31.109.130:5000/",
      "172.31.109.130",
      "172.31.109.130:5000",
      "0afc14b4-a602-41fd-b6d9-5093e1392d11-00-2ergle1nzcrwb.pike.replit.dev",
    ],
    strictPort: true,
    hmr: {
      clientPort: 5000,
    },
    fs: {
      allow: ["./client", "./shared"],
      deny: [".env", ".env.*", "*.{crt,pem}", "**/.git/**", "server/**"],
    },
  },
  build: {
    outDir: "dist/spa",
  },
  plugins: [react(), expressPlugin()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./client"),
      "@shared": path.resolve(__dirname, "./shared"),
    },
  },
}));

function expressPlugin(): Plugin {
  return {
    name: "express-plugin",
    apply: "serve", // Only apply during development (serve mode)
    configureServer(server) {
      const app = createServer();

      // Add Express app as middleware to Vite dev server
      server.middlewares.use(app);
    },
  };
}
