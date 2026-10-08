import { defineConfig } from "vitest/config";

// End-to-end: the TypeScript client against the real Python Gateway (stub backend).
export default defineConfig({
  test: {
    include: ["e2e/**/*.e2e.test.ts"],
    testTimeout: 30000,
    hookTimeout: 45000,
  },
});
