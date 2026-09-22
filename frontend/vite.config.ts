/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Em desenvolvimento o Vite repassa as chamadas da API ao FastAPI (ADR-001).
// No Docker o backend responde pelo nome do serviço; no host, pela porta local.
const api = process.env.VITE_API_ALVO ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // No compose, outros containers acessam pelo nome do serviço.
    allowedHosts: ["localhost", "frontend"],
    proxy: { "/execucoes": api, "/opcoes": api, "/health": api },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/testes/setup.ts"],
  },
});
