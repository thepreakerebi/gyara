/**
 * Tokenizer-aware context budgeting for N-ATLAS's 8,092-token window.
 *
 * Decode-free: it needs only an encoder (`string -> token ids`), so the same logic
 * runs with the real N-ATLAS tokenizer or a fake encoder in tests.
 */

/** Published N-ATLAS context length (tokens). */
export const NATLAS_CONTEXT_LIMIT = 8092;

export type Encoder = (text: string) => ArrayLike<number>;

export interface TokenReport {
  characters: number;
  words: number;
  tokens: number;
  tokensPerWord: number;
  tokensPerChar: number;
}

function words(text: string): string[] {
  return text.split(/\s+/).filter((w) => w.length > 0);
}

/** Measure and fit text against a token budget using an injected encoder. */
export class TokenBudget {
  private readonly encode: Encoder;
  readonly limit: number;

  constructor(encode: Encoder, limit: number = NATLAS_CONTEXT_LIMIT) {
    if (typeof encode !== "function") {
      throw new TypeError("encode must be a function");
    }
    if (!Number.isInteger(limit) || limit <= 0) {
      throw new RangeError("limit must be a positive integer");
    }
    this.encode = encode;
    this.limit = limit;
  }

  /** Number of tokens `text` encodes to. */
  count(text: string): number {
    return this.encode(text).length;
  }

  /** Whether `text` fits, leaving `reserved` tokens free for the response. */
  fits(text: string, reserved = 0): boolean {
    if (reserved < 0) {
      throw new RangeError("reserved must be >= 0");
    }
    return this.count(text) <= this.limit - reserved;
  }

  /** Per-word and per-char token ratios for `text`. */
  report(text: string): TokenReport {
    const wordCount = words(text).length;
    const chars = text.length;
    const tokens = this.count(text);
    return {
      characters: chars,
      words: wordCount,
      tokens,
      tokensPerWord: wordCount ? tokens / wordCount : 0,
      tokensPerChar: chars ? tokens / chars : 0,
    };
  }

  /** Trim `text` on word boundaries so it fits within `maxTokens` (default: the limit). */
  truncate(text: string, maxTokens: number = this.limit): string {
    if (maxTokens <= 0) {
      throw new RangeError("maxTokens must be positive");
    }
    if (this.count(text) <= maxTokens) {
      return text;
    }
    const kept: string[] = [];
    for (const word of words(text)) {
      if (this.count([...kept, word].join(" ")) > maxTokens) {
        break;
      }
      kept.push(word);
    }
    return kept.join(" ");
  }

  /** Split `text` into word-aligned chunks that each fit `maxTokens`. */
  chunk(text: string, maxTokens: number = this.limit, overlapWords = 0): string[] {
    if (maxTokens <= 0) {
      throw new RangeError("maxTokens must be positive");
    }
    if (overlapWords < 0) {
      throw new RangeError("overlapWords must be >= 0");
    }
    const all = words(text);
    if (all.length === 0) {
      return [];
    }

    const chunks: string[] = [];
    let start = 0;
    while (start < all.length) {
      let end = start;
      const kept: string[] = [];
      while (end < all.length) {
        const next = all[end] as string;
        if (this.count([...kept, next].join(" ")) > maxTokens) {
          break;
        }
        kept.push(next);
        end += 1;
      }
      if (kept.length === 0) {
        // A single word exceeds the budget; emit it alone to make progress.
        chunks.push(all[start] as string);
        start += 1;
        continue;
      }
      chunks.push(kept.join(" "));
      if (end >= all.length) {
        break;
      }
      start = Math.max(end - overlapWords, start + 1);
    }
    return chunks;
  }
}
