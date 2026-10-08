import { describe, expect, it } from "vitest";
import { z } from "zod";
import { StubBackend } from "./backend.js";
import { Structured } from "./client.js";
import { SchemaError } from "./schema.js";
import { Tool } from "./tools.js";

const transfer = z.object({ name: z.string(), amount: z.number().int() });

describe("Structured.generate", () => {
  it("returns valid data from the stub", async () => {
    const client = new Structured(new StubBackend({ name: "Chidi", amount: 5000 }));
    await expect(client.generate("Send 5k to Chidi", transfer)).resolves.toEqual({
      name: "Chidi",
      amount: 5000,
    });
  });

  it("synthesises valid data when the backend has no preset", async () => {
    const client = new Structured(new StubBackend());
    const result = await client.generate<Record<string, unknown>>("x", transfer);
    expect(Object.keys(result).sort()).toEqual(["amount", "name"]);
  });

  it("throws when backend output is invalid", async () => {
    const client = new Structured(new StubBackend({ name: "Chidi" }));
    await expect(client.generate("Send money", transfer)).rejects.toThrow(SchemaError);
  });
});

describe("Structured.callTool", () => {
  it("returns the chosen tool and arguments", async () => {
    const send = new Tool("send_money", "Send money to a contact", {
      type: "object",
      properties: { to: { type: "string" }, amount: { type: "integer" } },
      required: ["to", "amount"],
    });
    const response = { tool: "send_money", arguments: { to: "Ada", amount: 10 } };
    const client = new Structured(new StubBackend(response));
    const call = await client.callTool("Pay Ada 10", [send]);
    expect(call.name).toBe("send_money");
    expect(call.arguments).toEqual({ to: "Ada", amount: 10 });
  });
});

describe("Structured constructor", () => {
  it("rejects a backend without generateJson", () => {
    // @ts-expect-error testing runtime guard
    expect(() => new Structured({})).toThrow(TypeError);
  });
});
