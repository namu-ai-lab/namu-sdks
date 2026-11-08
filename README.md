# Namu SDKs

Official client libraries for the Namu API (speech recognition, speech synthesis, translation and a voice agent for
Hausa, Zarma and French), modelled on the OpenAI and ElevenLabs SDKs.

| Folder | Package | Install | Import |
| --- | --- | --- | --- |
| [`python/`](python) | `namu-ai` on PyPI | `pip install namu-ai` | `from namu import Namu` |
| [`typescript/`](typescript) | `namu-ai` on npm | `npm install namu-ai` | `import { Namu } from "namu-ai"` |

Both have the same methods as the one-file clients in the developer docs (`speech`, `transcribe`, `translate`,
`converse`, `usage`, `voices`, `models`), so code written against those clients only needs the install line changed.
On top: one error class per status, typed responses, retries with jitter, `NAMU_BASE_URL`, and a test suite.

**Status:** Python `namu-ai` 0.1.0 is [on PyPI](https://pypi.org/project/namu-ai/) (8 November 2026, published by `release.yml` with trusted publishing). The npm package waits on its first publish (see Publish: the npm account needs two-factor authentication).

## Checked

| | Python | TypeScript |
| --- | --- | --- |
| Mocked tests | 27 pass on Python 3.11 and 3.9 | 20 pass on Node 25 |
| Live tests (free endpoints, unknown-key error) | 2 pass | 2 pass |
| Package | wheel 35 KB, sdist; `twine check` passes | tarball 11 KB, 14 files, no dependencies |
| Clean install from the built file | imports, lists voices live, typed (`py.typed`) | imports, lists voices live; a TypeScript project type-checks under `nodenext` and `bundler` |

## Publish

Decided on 8 November 2026: the name `namu-ai` on both registries, Apache 2.0, the public repository
`namu-ai-lab/namu-sdks`. Publishing needs the owner's PyPI and npm accounts:

**PyPI (once):** on pypi.org, Account settings → Publishing → *Add a new pending publisher* → GitHub: project name
`namu-ai`, owner `namu-ai-lab`, repository `namu-sdks`, workflow `release.yml`, environment `pypi`. Then pushing the tag
`python-v0.1.0` publishes the package from GitHub Actions, with no token stored anywhere.

**npm (the first version by hand):** npm can only trust a workflow for a package that already exists, so the first
version is published from a terminal: `cd typescript && npm login && npm publish --access public`. npm refuses to
publish from an account without two-factor authentication: turn it on first (npmjs.com → Account → Two-Factor Authentication). Afterwards, on
npmjs.com, the package's Settings → Trusted publishing → GitHub Actions: `namu-ai-lab` / `namu-sdks` / `release.yml` /
environment `npm`; later versions then publish on the tag `js-vX.Y.Z`.

**Each later release:** bump the version (`python/src/namu/_version.py`, `typescript/package.json` and
`typescript/src/version.ts`), add a CHANGELOG entry, then `git tag python-vX.Y.Z` or `git tag js-vX.Y.Z` and
`git push --tags`. The workflow tests, checks the tag matches the version, and publishes.

## Develop

```bash
cd python && pip install -e ".[dev]" && pytest
cd typescript && npm install && npm test
```
