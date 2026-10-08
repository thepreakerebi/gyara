import { describe, expect, it } from "vitest";
import { NATLAS_CONTEXT_LIMIT, TokenBudget } from "./tokens.js";

const wordEncoder = (text: string): number[] =>
  text.split(/\s+/).filter((w) => w.length > 0).map((_, i) => i);

const charEncoder = (text: string): number[] =>
  [...text].filter((c) => !/\s/.test(c)).map((c) => c.codePointAt(0) ?? 0);

describe("TokenBudget", () => {
  it("defaults to the N-ATLAS context limit", () => {
    expect(new TokenBudget(wordEncoder).limit).toBe(NATLAS_CONTEXT_LIMIT);
    expect(NATLAS_CONTEXT_LIMIT).toBe(8092);
  });

  it("counts and fits with a reservation", () => {
    const budget = new TokenBudget(wordEncoder, 5);
    expect(budget.count("a b c")).toBe(3);
    expect(budget.fits("a b c", 2)).toBe(true);
    expect(budget.fits("a b c d", 2)).toBe(false);
  });

  it("reports per-word and per-char ratios", () => {
    const report = new TokenBudget(charEncoder, 100).report("omo");
    expect(report.words).toBe(1);
    expect(report.tokens).toBe(3);
    expect(report.tokensPerWord).toBe(3);
    expect(report.tokensPerChar).toBe(1);
  });

  it("handles empty text in the report", () => {
    const report = new TokenBudget(charEncoder).report("");
    expect(report.tokens).toBe(0);
    expect(report.tokensPerWord).toBe(0);
  });

  it("truncates on word boundaries", () => {
    const budget = new TokenBudget(wordEncoder, 3);
    expect(budget.truncate("a b c d e f")).toBe("a b c");
    expect(budget.truncate("a b")).toBe("a b");
  });

  it("chunks with and without overlap", () => {
    const budget = new TokenBudget(wordEncoder, 2);
    expect(budget.chunk("a b c d e")).toEqual(["a b", "c d", "e"]);
    expect(budget.chunk("a b c d", 2, 1)).toEqual(["a b", "b c", "c d"]);
  });

  it("makes progress when a single word exceeds the budget", () => {
    const budget = new TokenBudget(charEncoder, 2); // "ccc" is 3 tokens
    expect(budget.chunk("a ccc b")).toEqual(["a", "ccc", "b"]);
  });

  it("returns an empty array for blank text", () => {
    expect(new TokenBudget(wordEncoder).chunk("   ")).toEqual([]);
  });

  it("validates the constructor", () => {
    // @ts-expect-error testing runtime guard
    expect(() => new TokenBudget("nope")).toThrow(TypeError);
    expect(() => new TokenBudget(wordEncoder, 0)).toThrow(RangeError);
  });
});
