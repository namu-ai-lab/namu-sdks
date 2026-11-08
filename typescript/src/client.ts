import { APIConnectionError, APITimeoutError, AuthenticationError, NamuError, errorFor } from "./errors.ts";
import type { AudioInput, ConverseTurn, Language, Model, SpeechFormat, Transcription, Translation, Usage, Voice, VoiceInfo } from "./types.ts";
import { VERSION } from "./version.ts";

export const DEFAULT_BASE_URL = "https://api.namuai-lab.com";
const RETRY = new Set([429, 502, 503, 504]);

export interface ClientOptions {
  /** Your secret key (`namu_sk_...`). Defaults to the `NAMU_API_KEY` environment variable. */
  apiKey?: string;
  /** Defaults to `NAMU_BASE_URL`, then https://api.namuai-lab.com. */
  baseUrl?: string;
  /** Milliseconds to wait for an answer. Generous by default (5 minutes): a model waking up can take a minute. */
  timeoutMs?: number;
  /** Retries for network errors, 429 rate_limited and 502/503/504 (never quota_exceeded or other 4xx). Default 3. */
  maxRetries?: number;
  /** A fetch implementation, for runtimes without a global fetch or for tests. */
  fetch?: typeof fetch;
}

type Body = { json?: unknown; form?: Record<string, AudioInput | string | undefined> };

const env = (name: string): string | undefined =>
  (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env?.[name];
const sleep = (ms: number) => new Promise<void>((resolve) => setTimeout(resolve, ms));

/**
 * A client for the Namu API: speech recognition, speech synthesis, translation and a voice agent for Hausa, Zarma
 * and French. Server-side only: the key must never reach a browser or a mobile app.
 *
 *   import { Namu } from "namu-ai";
 *   const namu = new Namu();                       // reads NAMU_API_KEY
 *   const audio = await namu.speech("Sannu da zuwa!", { voice: "nadia", format: "mp3" });
 */
export class Namu {
  readonly baseUrl: string;
  readonly timeoutMs: number;
  readonly maxRetries: number;
  readonly #apiKey?: string;
  readonly #fetch: typeof fetch;

  constructor(options: ClientOptions = {}) {
    this.#apiKey = options.apiKey ?? env("NAMU_API_KEY");
    this.baseUrl = (options.baseUrl ?? env("NAMU_BASE_URL") ?? DEFAULT_BASE_URL).replace(/\/+$/, "");
    this.timeoutMs = options.timeoutMs ?? 300_000;
    this.maxRetries = Math.max(0, options.maxRetries ?? 3);
    const f = options.fetch ?? globalThis.fetch;
    if (!f) throw new NamuError("No fetch available: use Node 18+ or pass { fetch }.");
    this.#fetch = f.bind(globalThis);
  }

  /** Speak `text` (up to 2,000 characters). Returns the audio: WAV (24 kHz mono, default), MP3 or Ogg Opus. */
  async speech(text: string, opts: { voice?: Voice; language?: Language; format?: SpeechFormat } = {}): Promise<ArrayBuffer> {
    const json: Record<string, unknown> = { text, voice: opts.voice ?? "nadia", format: opts.format ?? "wav" };
    if (opts.language) json.language = opts.language;
    return (await this.#request("POST", "/v1/speech", { json })).arrayBuffer();
  }

  /** Write down what was said. `language` (default `ha`) is not detected: send the one you expect. */
  async transcribe(audio: AudioInput, opts: { language?: Language } = {}): Promise<Transcription> {
    return (await this.#request("POST", "/v1/transcribe", { form: { file: audio, language: opts.language ?? "ha" } })).json();
  }

  /** Translate Hausa ⇄ French, from text or from audio. `source` defaults to the other language from `target`. */
  async translate(input: { text: string } | { audio: AudioInput }, opts: { target?: "ha" | "fr"; source?: "ha" | "fr"; includeAudio?: boolean } = {}): Promise<Translation> {
    const target = opts.target ?? "fr";
    if ("text" in input) {
      return (await this.#request("POST", "/v1/translate", { json: { text: input.text, target, include_audio: Boolean(opts.includeAudio), ...(opts.source ? { source: opts.source } : {}) } })).json();
    }
    return (await this.#request("POST", "/v1/translate", { form: { file: input.audio, target, source: opts.source, include_audio: opts.includeAudio ? "true" : undefined } })).json();
  }

  /** One turn with the voice agent, in Hausa (research preview; the key needs the converse scope). */
  async converse(audio: AudioInput, opts: { sessionId?: string; persona?: string } = {}): Promise<ConverseTurn> {
    return (await this.#request("POST", "/v1/converse", { form: { file: audio, persona: opts.persona ?? "nadia", session_id: opts.sessionId } })).json();
  }

  /** Audio seconds used this calendar month (UTC) and the allowance. Free: counts nothing. */
  async usage(): Promise<Usage> {
    return (await this.#request("GET", "/v1/usage")).json();
  }

  /** The voices `speech` can use. No key needed. */
  async voices(): Promise<VoiceInfo[]> {
    return (await (await this.#request("GET", "/v1/voices", {}, false)).json()).data;
  }

  /** The models, their endpoints, languages and status. No key needed. */
  async models(): Promise<Model[]> {
    return (await (await this.#request("GET", "/v1/models", {}, false)).json()).data;
  }

  async #request(method: string, path: string, body: Body = {}, auth = true): Promise<Response> {
    const headers: Record<string, string> = { Accept: "application/json", "User-Agent": `namu-js/${VERSION}` };
    if (auth) {
      if (!this.#apiKey) throw new AuthenticationError("Set NAMU_API_KEY or pass { apiKey }.", { status: 401, type: "missing_api_key" });
      headers.Authorization = `Bearer ${this.#apiKey}`;
    }
    for (let attempt = 0; ; attempt++) {
      let res: Response;
      try {
        res = await this.#fetch(this.baseUrl + path, { method, headers: { ...headers, ...contentType(body) }, body: encode(body), signal: AbortSignal.timeout(this.timeoutMs) });
      } catch (cause) {
        const timedOut = (cause as Error)?.name === "TimeoutError";
        const error = timedOut
          ? new APITimeoutError(`No answer within ${this.timeoutMs / 1000} s.`, { cause })
          : new APIConnectionError(`Could not reach the Namu API: ${(cause as Error)?.name ?? "error"}.`, { cause });
        if (attempt >= this.maxRetries) throw error;
        await sleep(delay(attempt, null));
        continue;
      }
      if (res.ok) return res;
      const error = await apiError(res);
      if (!RETRY.has(res.status) || error.type === "quota_exceeded" || attempt >= this.maxRetries) throw error;
      await sleep(delay(attempt, res.headers.get("Retry-After")));
    }
  }
}

function contentType(body: Body): Record<string, string> {
  return body.json !== undefined ? { "Content-Type": "application/json" } : {};
}

function encode(body: Body): BodyInit | undefined {
  if (body.json !== undefined) return JSON.stringify(body.json);
  if (!body.form) return undefined;
  const form = new FormData();
  for (const [key, value] of Object.entries(body.form)) {
    if (value === undefined) continue;
    if (typeof value === "string") form.append(key, value);
    else form.append(key, value instanceof Blob ? value : new Blob([value as BlobPart]), "audio");
  }
  return form;
}

function delay(attempt: number, retryAfter: string | null): number {
  const seconds = retryAfter === null ? NaN : Number(retryAfter);
  if (Number.isFinite(seconds)) return Math.min(Math.max(seconds, 0), 60) * 1000;
  return Math.min(2 ** attempt, 16) * 1000 * (0.75 + Math.random() / 2); // 1, 2, 4 … seconds, with jitter
}

async function apiError(res: Response) {
  const requestId = res.headers.get("X-Request-Id") ?? undefined;
  const text = await res.text().catch(() => "");
  try {
    const { error } = JSON.parse(text) as { error: { type?: string; message?: string; request_id?: string } };
    return errorFor(res.status, error.type || "http_error", error.message ?? "", error.request_id || requestId);
  } catch {
    return errorFor(res.status, "http_error", text.slice(0, 200), requestId);
  }
}
