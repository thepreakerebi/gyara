import { describe, expect, it } from "vitest";
import { SchemaError, validate } from "./schema.js";
import { Tool, toolChoiceSchema } from "./tools.js";

const send = new Tool("send_money", "Send money to a contact", {
  type: "object",
  properties: { to: { type: "string" }, amount: { type: "integer" } },
  required: ["to", "amount"],
});
const check = new Tool("check_balance", "Check the account balance", {
  type: "object",
  properties: {},
});

describe("Tool", () => {
  it("rejects an invalid name", () => {
    expect(() => new Tool("send money", "x", {})).toThrow();
  });
  it("rejects a blank description", () => {
    expect(() => new Tool("x", "  ", {})).toThrow();
  });
});

describe("toolChoiceSchema", () => {
  it("validates a correct call", () => {
    const schema = toolChoiceSchema([send, check]);
    expect(() =>
      validate({ tool: "send_money", arguments: { to: "Ada", amount: 10 } }, schema),
    ).not.toThrow();
    expect(() => validate({ tool: "check_balance", arguments: {} }, schema)).not.toThrow();
  });

  it("ties arguments to the chosen tool", () => {
    const schema = toolChoiceSchema([send, check]);
    expect(() => validate({ tool: "send_money", arguments: {} }, schema)).toThrow(SchemaError);
    expect(() =>
      validate({ tool: "send_money", arguments: { to: "Ada", amount: "lots" } }, schema),
    ).toThrow(SchemaError);
  });

  it("rejects an unknown tool", () => {
    const schema = toolChoiceSchema([send]);
    expect(() => validate({ tool: "ghost", arguments: {} }, schema)).toThrow(SchemaError);
  });

  it("rejects empty and duplicate tool lists", () => {
    expect(() => toolChoiceSchema([])).toThrow();
    expect(() => toolChoiceSchema([send, send])).toThrow();
  });
});
