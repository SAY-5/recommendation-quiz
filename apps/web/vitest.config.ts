import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/tests/setup.ts"],
    css: false,
    exclude: ["node_modules", "src/tests/e2e/**", "tests/e2e/**"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary"],
      // Coverage gate scopes to the unit-tested layers (components + lib).
      // Pages are exercised end-to-end via Playwright (see CI e2e job).
      include: ["src/components/**/*.{ts,tsx}", "src/lib/**/*.ts"],
      exclude: [
        "src/main.tsx",
        "src/vite-env.d.ts",
        "src/tests/**",
        "src/**/*.d.ts",
      ],
      thresholds: {
        lines: 75,
        functions: 75,
        branches: 75,
        statements: 75,
      },
    },
  },
});
