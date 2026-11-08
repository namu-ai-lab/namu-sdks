/**
 * The Namu API for JavaScript and TypeScript: speech recognition, speech synthesis, translation and a voice agent for
 * Hausa, Zarma and French. https://www.namuai-lab.com
 */
export { Namu, DEFAULT_BASE_URL } from "./client.ts";
export type { ClientOptions } from "./client.ts";
export {
  NamuError, APIConnectionError, APITimeoutError, APIStatusError, BadRequestError, AuthenticationError,
  PermissionDeniedError, NotFoundError, PayloadTooLargeError, UnsupportedAudioError, NothingHeardError,
  RateLimitError, QuotaExceededError, InternalServerError,
} from "./errors.ts";
export type * from "./types.ts";
export { VERSION } from "./version.ts";
