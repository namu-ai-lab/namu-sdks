// Against the real API, only what costs nothing: NAMU_LIVE=1 node --test test/live.test.mjs (after npm run build).
import { test } from "node:test";
import assert from "node:assert/strict";
import { Namu, AuthenticationError } from "../dist/index.js";

const live = process.env.NAMU_LIVE === "1";

test("voices and models", { skip: !live && "set NAMU_LIVE=1" }, async () => {
  const c = new Namu({ apiKey: "" });
  const voices = new Set((await c.voices()).map((v) => v.id));
  for (const v of ["nadia", "mouhamad", "fr"]) assert.ok(voices.has(v));
  const models = Object.fromEntries((await c.models()).map((m) => [m.id, m]));
  assert.deepEqual(Object.keys(models).sort(), ["speech-recognition", "speech-synthesis", "translation", "voice-agent"]);
  assert.deepEqual([...models["speech-recognition"].languages].sort(), ["dje", "fr", "ha"]);
});

test("an unknown key is refused with a request id", { skip: !live && "set NAMU_LIVE=1" }, async () => {
  const c = new Namu({ apiKey: "namu_sk_" + "0".repeat(43), maxRetries: 0 });
  await assert.rejects(c.speech("Sannu"), (e) => e instanceof AuthenticationError && e.type === "invalid_api_key" && Boolean(e.requestId));
});
