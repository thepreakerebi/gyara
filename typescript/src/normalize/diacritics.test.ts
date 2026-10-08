import { describe, expect, it } from "vitest";
import { DictionaryRestorer } from "./diacritics.js";

const LEXICON = { omo: "ọmọ", yoruba: "Yorùbá", sango: "Ṣàngó" };

describe("DictionaryRestorer", () => {
  it("restores a known word", () => {
    expect(new DictionaryRestorer(LEXICON).restore("omo")).toBe("ọmọ");
  });

  it("preserves surrounding punctuation and spacing", () => {
    expect(new DictionaryRestorer(LEXICON).restore("Awon omo, nko?")).toBe("Awon ọmọ, nko?");
  });

  it("preserves the case pattern", () => {
    const r = new DictionaryRestorer(LEXICON);
    expect(r.restore("Omo")).toBe("Ọmọ");
    expect(r.restore("YORUBA")).toBe("YORÙBÁ");
  });

  it("matches regardless of input diacritics", () => {
    expect(new DictionaryRestorer(LEXICON).restore("ọmọ")).toBe("ọmọ");
  });

  it("leaves unknown words untouched", () => {
    expect(new DictionaryRestorer(LEXICON).restore("hello world")).toBe("hello world");
  });

  it("accepts a Map and exposes size", () => {
    const r = new DictionaryRestorer(new Map([["omo", "ọmọ"]]));
    expect(r.size).toBe(1);
  });

  it("rejects empty lexicon values", () => {
    expect(() => new DictionaryRestorer({ k: "" })).toThrow(TypeError);
  });
});
