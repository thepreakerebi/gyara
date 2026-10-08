import { describe, expect, it } from "vitest";
import { z } from "zod";
import { SchemaError, toJsonSchema, validate } from "./schema.js";

const transfer = z.object({ name: z.string(), amount: z.number().int() });

describe("toJsonSchema", () => {
  it("passes a plain schema object through", () => {
    const schema = { type: "object", properties: { x: { type: "integer" } } };
    expect(toJsonSchema(schema)).toBe(schema);
  });

  it("converts a Zod schema", () => {
    const schema = toJsonSchema(transfer);
    expect(schema.type).toBe("object");
    expect(Object.keys(schema.properties as object)).toEqual(["name", "amount"]);
  });

  it("rejects unsupported input", () => {
    expect(() => toJsonSchema(42)).toThrow(TypeError);
  });
});

describe("validate", () => {
  it("accepts conforming data", () => {
    expect(() => validate({ name: "Chidi", amount: 5000 }, transfer)).not.toThrow();
  });

  it("rejects a wrong type", () => {
    expect(() => validate({ name: "Chidi", amount: "lots" }, transfer)).toThrow(SchemaError);
  });

  it("rejects missing required fields", () => {
    expect(() => validate({ name: "Chidi" }, transfer)).toThrow(SchemaError);
  });
});
