/** Nigerian-language normalization and token budgeting for N-ATLAS (Pillar 2). */

export { normalizeText, stripDiacritics } from "./text.js";
export type { NormalizationForm, NormalizeOptions } from "./text.js";
export { DictionaryRestorer } from "./diacritics.js";
export type { Restorer } from "./diacritics.js";
export { TokenBudget, NATLAS_CONTEXT_LIMIT } from "./tokens.js";
export type { Encoder, TokenReport } from "./tokens.js";
