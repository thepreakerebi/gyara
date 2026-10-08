/**
 * Backends that turn a prompt + schema into structured data.
 *
 * {@link StubBackend} is a GPU-free stand-in for tests. {@link GatewayBackend} calls
 * the Gyara Gateway, which runs constrained decoding on N-ATLAS server-side.
 */

import type { JsonSchema } from "./schema.js";

export interface StructuredBackend {
  generateJson(prompt: string, schema: JsonSchema): unknown | Promise<unknown>;
}

/** Return a minimal value that satisfies `schema` (the subset Gyara emits). */
export function minimalInstance(schema: JsonSchema): unknown {
  if ("const" in schema) {
    return schema.const;
  }
  const enumValues = schema.enum;
  if (Array.isArray(enumValues) && enumValues.length > 0) {
    return enumValues[0];
  }
  const oneOf = schema.oneOf;
  if (Array.isArray(oneOf) && oneOf.length > 0) {
    return minimalInstance(oneOf[0] as JsonSchema);
  }
  const anyOf = schema.anyOf;
  if (Array.isArray(anyOf) && anyOf.length > 0) {
    return minimalInstance(anyOf[0] as JsonSchema);
  }

  let type = schema.type;
  if (Array.isArray(type)) {
    type = type[0];
  }
  if (type === undefined && "properties" in schema) {
    type = "object";
  }

  if (type === "object") {
    const properties = (schema.properties ?? {}) as Record<string, JsonSchema>;
    const result: Record<string, unknown> = {};
    for (const [key, sub] of Object.entries(properties)) {
      result[key] = minimalInstance(sub);
    }
    return result;
  }
  if (type === "array") {
    const count = typeof schema.minItems === "number" ? schema.minItems : 0;
    const items = (schema.items ?? { type: "string" }) as JsonSchema;
    return Array.from({ length: count }, () => minimalInstance(items));
  }
  if (type === "string") {
    return schema.default ?? "";
  }
  if (type === "integer" || type === "number") {
    return schema.default ?? 0;
  }
  if (type === "boolean") {
    return schema.default ?? false;
  }
  return null;
}

/** Deterministic backend for tests and local dev. Ignores the prompt. */
export class StubBackend implements StructuredBackend {
  constructor(private readonly response?: unknown) {}

  generateJson(_prompt: string, schema: JsonSchema): unknown {
    return this.response !== undefined ? this.response : minimalInstance(schema);
  }
}

type FetchLike = (url: string, init: RequestInit) => Promise<Response>;

export interface GatewayOptions {
  apiKey?: string;
  fetch?: FetchLike;
}

/** Calls the Gyara Gateway over HTTP; the Gateway enforces the schema server-side. */
export class GatewayBackend implements StructuredBackend {
  private readonly fetchImpl: FetchLike;

  constructor(
    private readonly baseUrl: string,
    private readonly options: GatewayOptions = {},
  ) {
    if (typeof baseUrl !== "string" || baseUrl.length === 0) {
      throw new TypeError("baseUrl must be a non-empty string");
    }
    const injected = options.fetch ?? (globalThis.fetch as FetchLike | undefined);
    if (!injected) {
      throw new TypeError("no fetch available; pass options.fetch");
    }
    this.fetchImpl = injected;
  }

  async generateJson(prompt: string, schema: JsonSchema): Promise<unknown> {
    const headers: Record<string, string> = { "content-type": "application/json" };
    if (this.options.apiKey) {
      headers.authorization = `Bearer ${this.options.apiKey}`;
    }
    const response = await this.fetchImpl(this.baseUrl, {
      method: "POST",
      headers,
      body: JSON.stringify({ prompt, schema }),
    });
    if (!response.ok) {
      throw new Error(`gateway request failed: ${response.status} ${response.statusText}`);
    }
    const payload = (await response.json()) as { data?: unknown };
    return payload.data ?? payload;
  }
}
