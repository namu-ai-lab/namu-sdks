# Namu API for JavaScript and TypeScript

Speech recognition, speech synthesis, translation and a voice agent for **Hausa, Zarma and French**. No dependencies;
runs on Node 18+, Deno, Bun and Cloudflare Workers.

```bash
npm install namu-ai
```

```typescript
import { writeFile, readFile } from "node:fs/promises";
import { Namu } from "namu-ai";

const namu = new Namu(); // reads NAMU_API_KEY

const audio = await namu.speech("Sannu da zuwa! Muna farin cikin jin muryarku.", { voice: "nadia", format: "mp3" });
await writeFile("welcome.mp3", Buffer.from(audio));

const { text } = await namu.transcribe(await readFile("welcome.mp3"), { language: "ha" });
```

Get a key at [namuai-lab.com/account/keys](https://www.namuai-lab.com/account/keys). **Server-side only**: never import
this package in browser or React Native code, where the key would travel with it. During the beta every account gets 30
minutes of audio a month, free.

## Usage

```typescript
// Text to speech: nadia (Hausa), mouhamad (Zarma and Hausa), fr (French); wav, mp3 or opus
const opus = await namu.speech("Fofo! Mate ni go?", { voice: "mouhamad", language: "dje", format: "opus" });

// Speech to text: a Blob, ArrayBuffer, Uint8Array or Buffer; ha, dje or fr (not detected: say which)
const result = await namu.transcribe(await readFile("voice-note.ogg"), { language: "ha" });

// Translation, Hausa ⇄ French, from text or speech, optionally spoken back (base64 WAV)
const fr = await namu.translate({ text: "Ina kwana? Yau za a yi zafi sosai." }, { source: "ha", target: "fr" });
const spoken = await namu.translate({ audio: await readFile("question.ogg") }, { source: "ha", includeAudio: true });

// Voice agent (research preview; the key needs the converse scope)
const turn = await namu.converse(await readFile("hello.ogg"), { sessionId: "demo-42" });

// Account and catalogue
await namu.usage();   // { month_audio_seconds_used, month_audio_seconds_limit }
await namu.voices();  // no key needed
await namu.models();
```

Every response is typed: `Transcription`, `Translation`, `ConverseTurn`, `Usage`, `VoiceInfo`, `Model`.

## Errors

```typescript
import { NamuError, QuotaExceededError, BadRequestError } from "namu-ai";

try {
  await namu.speech(text);
} catch (err) {
  if (err instanceof QuotaExceededError) { /* this month's allowance is used */ }
  else if (err instanceof BadRequestError) console.error(err.type, err.message);
  else if (err instanceof NamuError) console.error(err.status, err.type, err.requestId);
  else throw err;
}
```

| Class | Status | `type` |
| --- | --- | --- |
| `BadRequestError` | 400 | `invalid_request`, `invalid_json`, `missing_text`, `missing_file`, `empty_audio`, `unknown_voice`, `unsupported_language`, `unsupported_pair`, `unknown_persona` |
| `AuthenticationError` | 401 | `missing_api_key`, `invalid_api_key`, `key_revoked` |
| `PermissionDeniedError` | 403 | `insufficient_scope`, `account_paused` |
| `PayloadTooLargeError` | 413 | `payload_too_large`, `audio_too_long`, `text_too_long` |
| `UnsupportedAudioError` | 415 | `unsupported_audio` |
| `NothingHeardError` | 422 | `nothing_heard` |
| `RateLimitError` / `QuotaExceededError` | 429 | `rate_limited` / `quota_exceeded` |
| `InternalServerError` | 5xx | `internal_error`, `upstream_error`, `upstream_timeout`, ... |
| `APIConnectionError` / `APITimeoutError` | none | the API could not be reached, or did not answer in time |

## Retries and timeouts

Network errors, `429 rate_limited` and `502`/`503`/`504` are retried up to 3 times, after `Retry-After` or 1, 2, 4
seconds (with jitter); `quota_exceeded` and other 4xx never are. The default timeout is 5 minutes: the first request
after a quiet spell can take a minute while a model wakes up.

```typescript
const namu = new Namu({ timeoutMs: 120_000, maxRetries: 5 });
```

| Option | Environment | Default |
| --- | --- | --- |
| `apiKey` | `NAMU_API_KEY` | none |
| `baseUrl` | `NAMU_BASE_URL` | `https://api.namuai-lab.com` |
| `timeoutMs` | | 300000 |
| `maxRetries` | | 3 |
| `fetch` | | `globalThis.fetch` |

## Data

Speech to text and text to speech run on Namu's own models. Translation and the voice agent's replies are written by
Google Gemini through OpenRouter, which receives the text they work on. Namu keeps usage records, not your audio or
text.

## Development

```bash
npm install
npm test                 # builds, then runs the mocked tests
npm run test:live        # the free endpoints of the real API
```

Licensed under Apache 2.0.
