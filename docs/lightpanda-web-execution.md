# Lightpanda Web Execution Layer

AIbrief uses Lightpanda as the preferred browser for public, deterministic extraction and navigation. Chromium remains the compatibility fallback while Lightpanda is beta. Existing API, RSS, GitHub, Hacker News, arXiv, Reddit, and logged-in X connectors remain unchanged.

## Routing

```text
BrowserRouter
|-- Lightpanda: public extraction, crawling, navigation, PandaScript replay
|-- Chromium: authentication, form submission, file upload, unsupported sites
`-- Dedicated X connector: logged-in X sessions and cookies
```

The source of truth is `config/browser_router.json`. The implementation is `aibrief/connectors/browser_router.py`. Failure, unsupported APIs, timeout, or an empty response invokes the configured Chromium callback.

## Runtime deployment

The GitHub Actions runtime installs the stable Lightpanda `0.3.6` Linux release through `scripts/install_lightpanda.py`. The installer:

- obtains release metadata from the official `lightpanda-io/browser` GitHub repository;
- selects the runner architecture;
- requires a GitHub-published SHA-256 digest or checksum asset;
- verifies cached and newly downloaded binaries before execution;
- runs `lightpanda version`;
- exports only `LIGHTPANDA_BIN` through `GITHUB_ENV`.

`actions/cache@v5` keeps the verified binary between runs. `scripts/smoke_lightpanda.py` then fetches a real public page through `BrowserRouter` and fails unless the active backend is Lightpanda.

Render remains a static host for `web/`. The browser runs in GitHub Actions during collection and validation; no browser server or MCP endpoint is exposed publicly.

## Security defaults

- `--obey-robots` is always used for Lightpanda fetches.
- Private, loopback, link-local, and non-global IP ranges are blocked. DNS answers are checked immediately before execution.
- URL credentials are rejected.
- X and Twitter URLs stay on the dedicated X connector.
- Authentication, form submission, and file upload route to Chromium.
- The child process receives a minimal environment. API keys, cookies, topics, and tokens are not forwarded.
- `LIGHTPANDA_DISABLE_TELEMETRY=true` and `LIGHTPANDA_DISABLE_CORE_DUMP=1` are forced.
- Localhost is disabled by default.

## Programmatic use

```python
from aibrief.connectors.browser_router import fetch_public_page

result = fetch_public_page(
    "https://example.com/research",
    task="extract",
    fallback_fetcher=chromium_fetch,
)
print(result.backend, result.content)
```

The fallback callback is required when a caller needs guaranteed browser execution. A missing or failing Lightpanda binary without a fallback fails explicitly.

## Deterministic PandaScripts

1. Use `lightpanda agent` in a controlled development session to discover a public-source flow.
2. Review the generated JavaScript and remove credentials, form submissions, downloads, and private URLs.
3. Save the reviewed script under `skills/lightpanda/`.
4. Replay it with `run_pandascript(...)`. Runtime replay receives no model API keys.
5. Keep Chromium coverage for the same source until repeated production observations show Lightpanda is stable.

PandaScripts outside `skills/lightpanda/` are rejected. Do not commit cookies, local storage, session IDs, private URLs, or extracted personal data.

## Verification

```bash
python3 scripts/install_lightpanda.py \
  --version 0.3.6 \
  --destination "$RUNNER_TEMP/lightpanda/0.3.6/lightpanda" \
  --github-env "$GITHUB_ENV"
python3 scripts/check_lightpanda.py --require-binary
python3 scripts/smoke_lightpanda.py
python3 -m unittest \
  tests.test_browser_router \
  tests.test_capability_registry \
  tests.test_install_lightpanda \
  -v
```

Expected: the installer reports `status: ready`, readiness reports `lightpanda_available: true`, the smoke test reports `backend: lightpanda`, and guarded actions still route away from it.

## Rollback

1. Set `lightpanda.enabled` to `false` in `config/browser_router.json`.
2. Keep `fallback_backend` as `chromium`.
3. Remove the Lightpanda install and smoke steps from the workflows.
4. Re-run the browser-router tests.

Rollback does not require changing X, API, feed-generation, Render, or notification credentials.
