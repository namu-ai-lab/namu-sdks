// The built client (dist/) against a fake fetch. Nothing here touches the network.
import { test } from "node:test";
import assert from "node:assert/strict";
import {
  Namu, NamuError, APIConnectionError, APITimeoutError, AuthenticationError, BadRequestError, InternalServerError,
  NothingHeardError, PayloadTooLargeError, PermissionDeniedError, QuotaExceededError, RateLimitError,
  UnsupportedAudioError, VERSION,
} from "../dist/index.js";

const KEY = "namu_sk_" + "a".repeat(43);
const json = (status, body, headers = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", ...headers } });
const apiErr = (status, type, extra = {}) => json(status, { error: { type, message: "why", request_id: "r1" } }, extra);

/** A fake fetch that answers from a list and records every call. */
function fake(...answers) {
  const calls = [];
  const fn = async (url, init) => {
    calls.push({ url, init });
    const next = answers.shift();
    if (next instanceof Error) throw next;
    return typeof next === "function" ? next() : next;
  };
  return { fn, calls };
}
const client = (f, opts = {}) => new Namu({ apiKey: KEY, fetch: f.fn, maxRetries: 3, ...opts });

// Retries wait 1–4 s; tests run with Retry-After: 0 or maxRetries where it matters.

test("speech sends JSON and returns the audio", async () => {
  const f = fake(new Response(new Uint8Array([79, 103, 103, 83]), { status: 200, headers: { "X-Audio-Seconds": "2.4" } }));
  const audio = await client(f).speech("Fofo! Mate ni go?", { voice: "mouhamad", language: "dje", format: "opus" });
  assert.deepEqual([...new Uint8Array(audio)], [79, 103, 103, 83]);
  const { url, init } = f.calls[0];
  assert.equal(url, "https://api.namuai-lab.com/v1/speech");
  assert.deepEqual(JSON.parse(init.body), { text: "Fofo! Mate ni go?", voice: "mouhamad", format: "opus", language: "dje" });
  assert.equal(init.headers.Authorization, `Bearer ${KEY}`);
  assert.equal(init.headers["Content-Type"], "application/json");
  assert.equal(init.headers["User-Agent"], `namu-js/${VERSION}`);
});

test("speech defaults to nadia and wav", async () => {
  const f = fake(new Response(new Uint8Array([1])));
  await client(f).speech("Sannu");
  assert.deepEqual(JSON.parse(f.calls[0].init.body), { text: "Sannu", voice: "nadia", format: "wav" });
});

test("transcribe sends multipart from bytes, buffers and blobs", async () => {
  for (const audio of [new Uint8Array([1, 2]), Buffer.from([1, 2]), new Blob([new Uint8Array([1, 2])]), new Uint8Array([1, 2]).buffer]) {
    const f = fake(json(200, { model: "speech-recognition", text: "sannu", language: "ha", audio_seconds: 2 }));
    const out = await client(f).transcribe(audio, { language: "dje" });
    assert.equal(out.text, "sannu");
    const form = f.calls[0].init.body;
    assert.ok(form instanceof FormData);
    assert.equal(form.get("language"), "dje");
    assert.equal((await form.get("file").arrayBuffer()).byteLength, 2);
    assert.equal(f.calls[0].init.headers["Content-Type"], undefined); // fetch sets the multipart boundary
  }
});

test("translate text and audio", async () => {
  const f = fake(json(200, { model: "translation", text: "y" }), json(200, { model: "translation", text: "z", audio: "UklGRg==" }));
  const c = client(f);
  await c.translate({ text: "Ina kwana?" }, { source: "ha", target: "fr" });
  assert.deepEqual(JSON.parse(f.calls[0].init.body), { text: "Ina kwana?", target: "fr", include_audio: false, source: "ha" });
  await c.translate({ audio: new Uint8Array([1]) }, { target: "ha", includeAudio: true });
  const form = f.calls[1].init.body;
  assert.equal(form.get("target"), "ha");
  assert.equal(form.get("include_audio"), "true");
  assert.equal(form.get("source"), null);
});

test("converse sends the session id", async () => {
  const f = fake(json(200, { model: "voice-agent", reply: "Lafiya lau", audio: "UklGRg==" }));
  const turn = await client(f).converse(new Uint8Array([1]), { sessionId: "s1" });
  assert.equal(turn.reply, "Lafiya lau");
  assert.equal(f.calls[0].init.body.get("session_id"), "s1");
  assert.equal(f.calls[0].init.body.get("persona"), "nadia");
});

test("voices and models need no key; usage does", async () => {
  const f = fake(json(200, { data: [{ id: "nadia" }] }), json(200, { data: [{ id: "speech-synthesis", status: "beta" }] }));
  const keyless = new Namu({ apiKey: "", fetch: f.fn });
  assert.deepEqual((await keyless.voices()).map((v) => v.id), ["nadia"]);
  assert.equal((await keyless.models())[0].status, "beta");
  assert.equal(f.calls[0].init.headers.Authorization, undefined);
  await assert.rejects(keyless.usage(), (e) => e instanceof AuthenticationError && e.type === "missing_api_key" && f.calls.length === 2);
});

test("environment variables", () => {
  process.env.NAMU_BASE_URL = "https://example.test/";
  try {
    assert.equal(new Namu({ apiKey: KEY, fetch: async () => json(200, {}) }).baseUrl, "https://example.test");
  } finally {
    delete process.env.NAMU_BASE_URL;
  }
});

for (const [status, type, Cls] of [
  [400, "unknown_voice", BadRequestError], [401, "invalid_api_key", AuthenticationError],
  [403, "insufficient_scope", PermissionDeniedError], [413, "text_too_long", PayloadTooLargeError],
  [415, "unsupported_audio", UnsupportedAudioError], [422, "nothing_heard", NothingHeardError],
  [429, "quota_exceeded", QuotaExceededError], [500, "internal_error", InternalServerError],
]) {
  test(`${status} ${type} → ${Cls.name}, not retried`, async () => {
    const f = fake(apiErr(status, type));
    await assert.rejects(client(f).speech("x"), (e) =>
      e instanceof Cls && e instanceof NamuError && e.status === status && e.type === type && e.requestId === "r1" && e.name === Cls.name);
    assert.equal(f.calls.length, 1);
  });
}

test("rate_limited is retried after Retry-After", async () => {
  const f = fake(apiErr(429, "rate_limited", { "Retry-After": "0" }), new Response(new Uint8Array([1])));
  await client(f).speech("x");
  assert.equal(f.calls.length, 2);
});

test("rate_limited is a RateLimitError, not QuotaExceededError", async () => {
  const f = fake(apiErr(429, "rate_limited"));
  await assert.rejects(client(f, { maxRetries: 0 }).speech("x"), (e) => e instanceof RateLimitError && !(e instanceof QuotaExceededError));
});

test("upstream errors are retried, then given up", async () => {
  const answers = Array.from({ length: 2 }, () => apiErr(502, "upstream_error", { "Retry-After": "0" }));
  const f = fake(...answers);
  await assert.rejects(client(f, { maxRetries: 1 }).speech("x"), InternalServerError);
  assert.equal(f.calls.length, 2);
});

test("an error without a JSON body keeps the gateway's request id", async () => {
  const f = fake(new Response("Service Unavailable", { status: 503, headers: { "X-Request-Id": "gw-1" } }));
  await assert.rejects(client(f, { maxRetries: 0 }).speech("x"), (e) => e instanceof InternalServerError && e.type === "http_error" && e.requestId === "gw-1");
});

test("network errors and timeouts", async () => {
  const down = fake(new TypeError("fetch failed"));
  await assert.rejects(client(down, { maxRetries: 0 }).speech("x"), (e) => e instanceof APIConnectionError && !(e instanceof APITimeoutError) && e.cause instanceof TypeError);
  const slow = fake(Object.assign(new Error("timed out"), { name: "TimeoutError" }));
  await assert.rejects(client(slow, { maxRetries: 0 }).speech("x"), APITimeoutError);
});
