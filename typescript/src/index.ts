/**
 * Gyara — a reliability layer for N-ATLAS.
 *
 * - Normalization (Pillar 2): clean Nigerian-language input and fit it to the
 *   model's 8,092-token context window. See `gyara/normalize`.
 * - Structured output (Pillar 1): guaranteed schema-valid generation and
 *   tool-calling. See `gyara/structured`.
 */

export const VERSION = "0.1.0";

export * from "./normalize/index.js";
export * from "./structured/index.js";
