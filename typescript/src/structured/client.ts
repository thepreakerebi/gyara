/**
 * High-level structured-output client (Pillar 1).
 *
 * Validates the backend's result as a safety net, so callers always get schema-valid
 * data or a clear error — never half-parsed text.
 */

import type { StructuredBackend } from "./backend.js";
import { toJsonSchema, validate } from "./schema.js";
import { type Tool, type ToolCall, toolChoiceSchema } from "./tools.js";

/** Guaranteed structured output over any {@link StructuredBackend}. */
export class Structured {
  constructor(private readonly backend: StructuredBackend) {
    if (typeof backend?.generateJson !== "function") {
      throw new TypeError("backend must implement generateJson(prompt, schema)");
    }
  }

  /** Return data for `prompt` that conforms to `schema` (a JSON Schema or Zod schema). */
  async generate<T = unknown>(prompt: string, schema: unknown): Promise<T> {
    if (typeof prompt !== "string") {
      throw new TypeError("prompt must be a string");
    }
    const jsonSchema = toJsonSchema(schema);
    const data = await this.backend.generateJson(prompt, jsonSchema);
    validate(data, jsonSchema);
    return data as T;
  }

  /** Choose one tool for `prompt` and return its validated arguments. */
  async callTool(prompt: string, tools: Tool[]): Promise<ToolCall> {
    if (typeof prompt !== "string") {
      throw new TypeError("prompt must be a string");
    }
    const schema = toolChoiceSchema(tools);
    const data = await this.backend.generateJson(prompt, schema);
    validate(data, schema);
    const chosen = data as { tool: string; arguments: Record<string, unknown> };
    return { name: chosen.tool, arguments: chosen.arguments };
  }
}
