import { defineConfig } from "vitest/config";

// Unit tests only. The cross-language e2e test (needs the Python venv) runs via
// `npm run test:e2e` with its own config.
export default defineConfig({
  test: {
    include: ["src/**/*.test.ts"],
  },
});
