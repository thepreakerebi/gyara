/**
 * Tool definitions for structured tool-calling.
 *
 * {@link toolChoiceSchema} builds a single schema whose `oneOf` branches tie each
 * tool name to its own argument schema, so a tool call is correct by construction.
 */

import { toJsonSchema, type JsonSchema } from "./schema.js";

const IDENTIFIER = /^[A-Za-z_][A-Za-z0-9_]*$/;

/** A callable the model may choose, with a schema for its arguments. */
export class Tool {
  constructor(
    readonly name: string,
    readonly description: string,
    readonly parameters: unknown,
  ) {
    if (typeof name !== "string" || !IDENTIFIER.test(name)) {
      throw new Error(`tool name must be a valid identifier, got ${JSON.stringify(name)}`);
    }
    if (typeof description !== "string" || description.trim().length === 0) {
      throw new Error("tool description must be a non-empty string");
    }
  }

  /** The arguments schema as a JSON Schema object. */
  get parametersSchema(): JsonSchema {
    return toJsonSchema(this.parameters);
  }
}

/** The model's choice: a tool name and its validated arguments. */
export interface ToolCall {
  name: string;
  arguments: Record<string, unknown>;
}

/** Build a JSON Schema that admits exactly one valid tool call. */
export function toolChoiceSchema(tools: Tool[]): JsonSchema {
  if (tools.length === 0) {
    throw new Error("tools must be a non-empty array");
  }
  const names = tools.map((t) => t.name);
  if (new Set(names).size !== names.length) {
    throw new Error("tool names must be unique");
  }

  const oneOf = tools.map((tool) => ({
    type: "object",
    properties: {
      tool: { const: tool.name },
      arguments: tool.parametersSchema,
    },
    required: ["tool", "arguments"],
    additionalProperties: false,
  }));
  return { oneOf };
}
