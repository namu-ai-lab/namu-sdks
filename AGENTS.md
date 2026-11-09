# namu-sdks: the official Namu API libraries

Agent map, not a manual. Truth order: the Namu API's behaviour > the tests > the code > the READMEs.

## What this repository is
`python/` publishes `namu-ai` on PyPI (`from namu import Namu`); `typescript/` publishes `namu-ai` on npm. Same
methods in both: `speech`, `transcribe`, `translate`, `converse`, `usage`, `voices`, `models`; one error class per
status; retries for network errors, `429 rate_limited` and 502/503/504 (never `quota_exceeded`). For the API's
contract, use the namu MCP server (namu plugin): `/namu:cloud`, or the tools `api_catalog` and `team_context("cloud")`.

## Commands
- Python: `cd python && pip install -e ".[dev]" && pytest`; live, free endpoints only: `NAMU_LIVE=1 pytest -m live`
- TypeScript: `cd typescript && npm ci && npm test`; live: `npm run test:live`
- Build: `cd python && python -m build && twine check dist/*`; `cd typescript && npm pack --dry-run`

## Rules
- Keep the two libraries in step: a method, argument or error class added to one is added to the other in the same PR.
- No runtime dependencies beyond `requests` (Python) and none in TypeScript; Python 3.9+, Node 18+.
- Every bug fix gets a mocked test; live tests only call endpoints that cost nothing.
- Release: bump the version in `python/src/namu/_version.py`, or in `typescript/package.json` and
  `typescript/src/version.ts`; add a CHANGELOG entry; push the tag `python-vX.Y.Z` or `js-vX.Y.Z`. `release.yml`
  publishes with trusted publishing. Never publish by hand without the owner.
- Never put a real API key in code, tests or fixtures.
