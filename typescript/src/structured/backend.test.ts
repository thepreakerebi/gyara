import { describe, expect, it, vi } from "vitest";
import { GatewayBackend, minimalInstance, StubBackend } from "./backend.js";
import { validate } from "./schema.js";
import { Tool, toolChoiceSchema } from "./tools.js";

describe("StubBackend", () => {
  it("returns a preset response", () => {
    const backend = new StubBackend({ name: "Ada", amount: 10 });
    expect(backend.generateJson("x", {})).toEqual({ name: "Ada", amount: 10 });
  });
});

describe("minimalInstance", () => {
  it("covers scalar types and const/enum", () => {
    expect(minimalInstance({ type: "string" })).toBe("");
    expect(minimalInstance({ type: "integer" })).toBe(0);
    expect(minimalInstance({ type: "boolean" })).toBe(false);
    expect(minimalInstance({ const: "x" })).toBe("x");
    expect(minimalInstance({ enum: ["a", "b"] })).toBe("a");
  });

  it("builds a schema-valid object", () => {
    const schema = {
      type: "object",
      properties: { name: { type: "string" }, amount: { type: "integer" } },
      required: ["name", "amount"],
    };
    expect(() => validate(minimalInstance(schema), schema)).not.toThrow();
  });

  it("satisfies a tool-choice schema", () => {
    const tool = new Tool("send_money", "Send money", {
      type: "object",
      properties: { to: { type: "string" } },
      required: ["to"],
    });
    const schema = toolChoiceSchema([tool]);
    const instance = minimalInstance(schema) as { tool: string };
    expect(() => validate(instance, schema)).not.toThrow();
    expect(instance.tool).toBe("send_money");
  });

  it("respects minItems", () => {
    expect(minimalInstance({ type: "array", items: { type: "string" }, minItems: 2 })).toEqual([
      "",
      "",
    ]);
  });
});

describe("GatewayBackend", () => {
  it("posts prompt and schema and returns data", async () => {
    const fetchMock = vi.fn(async (_url: string, _init: RequestInit) =>
      new Response(JSON.stringify({ data: { ok: true } }), { status: 200 }),
    );
    const backend = new GatewayBackend("https://gw.test/v1", { fetch: fetchMock, apiKey: "k" });
    const result = await backend.generateJson("hi", { type: "object" });

    expect(result).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledOnce();
    const [url, init] = fetchMock.mock.calls[0]!;
    expect(url).toBe("https://gw.test/v1");
    expect((init.headers as Record<string, string>).authorization).toBe("Bearer k");
    expect(JSON.parse(init.body as string)).toEqual({ prompt: "hi", schema: { type: "object" } });
  });

  it("throws on a non-ok response", async () => {
    const fetchMock = vi.fn(async (_url: string, _init: RequestInit) =>
      new Response("nope", { status: 500 }),
    );
    const backend = new GatewayBackend("https://gw.test", { fetch: fetchMock });
    await expect(backend.generateJson("x", {})).rejects.toThrow(/gateway request failed/);
  });

  it("requires a non-empty baseUrl", () => {
    expect(() => new GatewayBackend("", { fetch: vi.fn() })).toThrow(TypeError);
  });
});
