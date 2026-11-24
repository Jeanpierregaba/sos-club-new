import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { paraglideVitePlugin } from "@inlang/paraglide-js";

import { OPTIONS_PARAGLIDE } from "./src/lib/langues-config";

export default defineConfig({
  plugins: [react(), paraglideVitePlugin(OPTIONS_PARAGLIDE)],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test/setup.ts"],
    include: ["src/**/*.{test,spec}.{ts,tsx}"],
  },
  resolve: {
    alias: { "@": path.resolve(__dirname, "./src") },
  },
});
