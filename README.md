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

**Status: not published.** Nothing is on PyPI or npm yet. The names, licence and publishing need the founder's decision.

## Checked

| | Python | TypeScript |
| --- | --- | --- |
| Mocked tests | 27 pass on Python 3.11 and 3.9 | 20 pass on Node 25 |
| Live tests (free endpoints, unknown-key error) | 2 pass | 2 pass |
| Package | wheel 35 KB, sdist; `twine check` passes | tarball 11 KB, 14 files, no dependencies |
| Clean install from the built file | imports, lists voices live, typed (`py.typed`) | imports, lists voices live; a TypeScript project type-checks under `nodenext` and `bundler` |

## Decisions before publishing

1. **Names.** `namu` is taken on both registries by unrelated projects (a Korean programming-language package on PyPI,
   a tree widget on npm). `namu-ai` is free on both today. Alternatives: `namu-sdk`, `namuai`, or a scoped
   `@namu-ai/sdk` on npm (needs an npm organisation named `namu-ai`). Changing the name is one line in each package file.
2. **Licence.** Apache 2.0 is in place (what OpenAI's SDKs use; it includes a patent grant). MIT (what ElevenLabs uses)
   is the other usual choice.
3. **Where the code lives.** A public GitHub repository (for example `namu-ai-lab/namu-sdks`) lets developers read the
   code and lets CI publish with provenance. It is not created yet.

## Publish (once decided)

The workflows in `.github/workflows/` test both packages on every push, and publish only when a version tag is pushed,
using trusted publishing (no tokens stored in GitHub):

1. Create the public repository and push this folder to it.
2. **PyPI:** on pypi.org, Account → Publishing → add a pending trusted publisher: project `namu-ai`, owner
   `namu-ai-lab`, repository `namu-sdks`, workflow `release.yml`, environment `pypi`.
3. **npm:** create the npm account or organisation that will own `namu-ai`; on npmjs.com add a trusted publisher for the
   repository and workflow `release.yml` (or create an automation token and store it as the `NPM_TOKEN` secret).
4. Tag and push: `git tag python-v0.1.0 && git push --tags` publishes Python; `git tag js-v0.1.0` publishes npm.
5. Update the developer docs: on the SDK pages, replace "copy namu.py" with `pip install namu-ai` / `npm install
   namu-ai`, and add the release to the changelog.

To publish by hand instead: `cd python && python -m build && twine upload dist/*`, and `cd typescript && npm publish`.

## Develop

```bash
cd python && pip install -e ".[dev]" && pytest
cd typescript && npm install && npm test
```
