/**
 * Deterministic text normalization for Nigerian-language input to N-ATLAS.
 *
 * Pure and dependency-free: Unicode normalization, zero-width stripping, and
 * whitespace cleanup, which are common sources of degraded model output.
 */

export type NormalizationForm = "NFC" | "NFKC" | "NFD" | "NFKD";

export interface NormalizeOptions {
  form?: NormalizationForm;
  collapseWhitespace?: boolean;
  stripZeroWidth?: boolean;
}

const ZERO_WIDTH = /[​‌‍⁠﻿]/g;
const HORIZONTAL_WS = /[^\S\n]+/g;
const MULTI_NEWLINE = /\n{3,}/g;
const COMBINING_MARKS = /\p{M}+/gu;

/** Return a cleaned copy of `text` (NFC, no zero-width chars, tidy whitespace). */
export function normalizeText(text: string, options: NormalizeOptions = {}): string {
  if (typeof text !== "string") {
    throw new TypeError("text must be a string");
  }
  const { form = "NFC", collapseWhitespace = true, stripZeroWidth = true } = options;

  let out = text.normalize(form);
  if (stripZeroWidth) {
    out = out.replace(ZERO_WIDTH, "");
  }
  if (collapseWhitespace) {
    out = out.replace(HORIZONTAL_WS, " ").replace(MULTI_NEWLINE, "\n\n");
    out = out
      .split("\n")
      .map((line) => line.trim())
      .join("\n")
      .trim();
  }
  return out;
}

/** Remove all combining marks, reducing text to ASCII base letters ("Yorùbá" -> "Yoruba"). */
export function stripDiacritics(text: string): string {
  if (typeof text !== "string") {
    throw new TypeError("text must be a string");
  }
  return text.normalize("NFD").replace(COMBINING_MARKS, "");
}
