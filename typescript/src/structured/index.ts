/** Guaranteed structured output and tool-calling for N-ATLAS (Pillar 1). */

export { Structured } from "./client.js";
export {
  StubBackend,
  GatewayBackend,
  minimalInstance,
} from "./backend.js";
export type { StructuredBackend, GatewayOptions } from "./backend.js";
export { Tool, toolChoiceSchema } from "./tools.js";
export type { ToolCall } from "./tools.js";
export { SchemaError, toJsonSchema, validate } from "./schema.js";
export type { JsonSchema } from "./schema.js";
