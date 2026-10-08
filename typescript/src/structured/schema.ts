/**
 * JSON Schema handling for structured output.
 *
 * Accepts either a plain JSON Schema object or a Zod schema (converted with
 * `zod-to-json-schema`), and validates data with Ajv.
 */

import { createRequire } from "node:module";
import type { Ajv, Options } from "ajv";
import { zodToJsonSchema } from "zod-to-json-schema";

// Ajv ships CommonJS; load it through require so the class resolves correctly under
// NodeNext ESM (a default/named import of a CJS class is unreliable here).
const AjvCtor = createRequire(import.meta.url)("ajv") as unknown as {
  new (options?: Options): Ajv;
};

export type JsonSchema = Record<string, unknown>;

/** Thrown when data does not conform to its schema. */
export class SchemaError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "SchemaError";
  }
}

function isZodSchema(value: unknown): boolean {
  return (
    typeof value === "object" &&
    value !== null &&
    "_def" in value &&
    typeof (value as { safeParse?: unknown }).safeParse === "function"
  );
}

/** Return a JSON Schema object for `schema` (a plain schema object or a Zod schema). */
export function toJsonSchema(schema: unknown): JsonSchema {
  if (isZodSchema(schema)) {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return zodToJsonSchema(schema as any) as JsonSchema;
  }
  if (typeof schema === "object" && schema !== null && !Array.isArray(schema)) {
    return schema as JsonSchema;
  }
  throw new TypeError("schema must be a JSON Schema object or a Zod schema");
}

const ajv = new AjvCtor({ strict: false, allErrors: false });

/** Validate `data` against `schema`; return void or throw {@link SchemaError}. */
export function validate(data: unknown, schema: unknown): void {
  const jsonSchema = toJsonSchema(schema);
  const check = ajv.compile(jsonSchema);
  if (!check(data)) {
    throw new SchemaError(ajv.errorsText(check.errors));
  }
}
