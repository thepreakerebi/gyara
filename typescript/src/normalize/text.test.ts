import { describe, expect, it } from "vitest";
import { normalizeText, stripDiacritics } from "./text.js";

describe("normalizeText", () => {
  it("collapses horizontal whitespace but keeps paragraphs", () => {
    expect(normalizeText("Bawo   ni\t\tani?\n\n\n\nMo wa daadaa  ")).toBe(
      "Bawo ni ani?\n\nMo wa daadaa",
    );
  });

  it("strips zero-width characters", () => {
    expect(normalizeText("o​mo﻿")).toBe("omo");
  });

  it("composes combining marks via NFC", () => {
    const out = normalizeText("ọ");
    expect(out).toBe("ọ".normalize("NFC"));
    expect([...out]).toHaveLength(1);
  });

  it("rejects non-strings", () => {
    // @ts-expect-error testing runtime guard
    expect(() => normalizeText(123)).toThrow(TypeError);
  });
});

describe("stripDiacritics", () => {
  it("reduces to ASCII base letters", () => {
    expect(stripDiacritics("Yorùbá")).toBe("Yoruba");
    expect(stripDiacritics("ọmọ")).toBe("omo");
    expect(stripDiacritics("Ṣàngó")).toBe("Sango");
  });
});
