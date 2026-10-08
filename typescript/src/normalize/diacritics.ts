/**
 * Diacritic restoration for Nigerian languages.
 *
 * Ships a deterministic baseline: a dictionary restorer that maps an undiacritized
 * word to its canonical diacritized form from a supplied lexicon. The `Restorer`
 * interface lets a learned restorer drop in later without changing call sites.
 */

import { stripDiacritics } from "./text.js";

export interface Restorer {
  restore(text: string): string;
}

// A word is a run of letters plus their combining marks; punctuation is preserved.
const WORD = /\p{L}[\p{L}\p{M}]*/gu;

function matchCase(source: string, target: string): string {
  if (source === source.toUpperCase() && source !== source.toLowerCase()) {
    return target.toUpperCase();
  }
  const first = source[0];
  if (first && first === first.toUpperCase() && first !== first.toLowerCase()) {
    return target.charAt(0).toUpperCase() + target.slice(1);
  }
  return target;
}

/**
 * Baseline restorer backed by a lexicon of canonical diacritized forms.
 *
 * Lookups are accent- and case-insensitive; the input word's capitalisation is
 * preserved. Pass the lexicon values as the canonical (diacritized) spellings.
 */
export class DictionaryRestorer implements Restorer {
  private readonly map = new Map<string, string>();

  constructor(lexicon: Record<string, string> | Map<string, string>) {
    const values =
      lexicon instanceof Map ? [...lexicon.values()] : Object.values(lexicon ?? {});
    for (const value of values) {
      if (typeof value !== "string" || value.length === 0) {
        throw new TypeError("lexicon values must be non-empty strings");
      }
      const key = stripDiacritics(value).toLowerCase();
      if (!this.map.has(key)) {
        this.map.set(key, value);
      }
    }
  }

  get size(): number {
    return this.map.size;
  }

  restore(text: string): string {
    if (typeof text !== "string") {
      throw new TypeError("text must be a string");
    }
    return text.replace(WORD, (word) => {
      const canonical = this.map.get(stripDiacritics(word).toLowerCase());
      return canonical ? matchCase(word, canonical) : word;
    });
  }
}
