# AIbrief X Source Shadow Comparison

Generated: 2026-06-26T01:35:45Z
Run: https://github.com/f2h2dai/AibriefAI/actions/runs/28211334248

## Phase 1 - Inspect
Status: Complete
Deliverable: query parity plan + auth gap report
Gate to next phase: current production query and Birdclaw auth requirements identified.

| Item | Result |
| --- | --- |
| Production X query | AI OR agents OR LLM OR GPT OR reasoning |
| Production command order | twitter search -> opencli twitter search -> bird search |
| Birdclaw command | birdclaw discuss <query> --mode <mode> --refresh --json, then birdclaw search tweets <query> --json |
| Birdclaw OpenAI features | Disabled by empty OPENAI_API_KEY; no today/digest/inbox --score calls |
| Auth gap | Birdclaw live reads need a separate xurl OAuth2 setup or a local bird browser-cookie session. The existing TWITTER_COOKIE secret helps the production twitter-cli path, but Birdclaw docs do not treat it as a direct auth substitute. |
| Node requirement | Birdclaw package.json requires >=25.8.1 <27; workflow uses actions/setup-node@v6.4.0 with node-version 26.x |

### Query Parity Plan
| # | Kind | Handle | Query |
| --- | --- | --- | --- |
| 1 | named-account | sama | from:sama (AI OR agents OR LLM OR GPT OR reasoning) |
| 2 | named-account | karpathy | from:karpathy (AI OR agents OR LLM OR GPT OR reasoning) |
| 3 | named-account | AndrewYNg | from:AndrewYNg (AI OR agents OR LLM OR GPT OR reasoning) |
| 4 | named-account | ylecun | from:ylecun (AI OR agents OR LLM OR GPT OR reasoning) |
| 5 | named-account | demishassabis | from:demishassabis (AI OR agents OR LLM OR GPT OR reasoning) |
| 6 | named-account | OpenAI | from:OpenAI (AI OR agents OR LLM OR GPT OR reasoning) |
| 7 | named-account | AnthropicAI | from:AnthropicAI (AI OR agents OR LLM OR GPT OR reasoning) |
| 8 | named-account | GoogleDeepMind | from:GoogleDeepMind (AI OR agents OR LLM OR GPT OR reasoning) |

## Phase 2 - Design
Status: Complete
Deliverable: comparison spec + report template
Gate to next phase: dimensions defined for count, overlap, fields, latency, auth friction, and errors.

| Dimension | How it is measured |
| --- | --- |
| Signal count | Normalized public X records per source after dedupe |
| Overlap | Tweet ID first, then canonical URL, then text fingerprint |
| Unique-to-each | Source keys not found in the other source |
| Field richness | Average non-empty top-level fields plus most common field names |
| Latency | Per command elapsed milliseconds, summarized as total, median, max |
| Auth/setup friction | birdclaw auth status, xurl whoami, bird whoami, and command errors |
| Errors | Non-zero command exits with redacted stderr |

## Phase 3 - Implement
Status: Complete
Deliverable: manual-only workflow + comparison script
Gate to next phase: workflow writes this summary and commits a Markdown report without touching production feed artifacts.

| File | Role |
| --- | --- |
| .github/workflows/compare-x-sources.yml | workflow_dispatch-only shadow run |
| tools/compare_x_sources.py | standard-library collector, normalizer, comparator, report writer |
| reports/x-source-comparisons/*.md | permanent run reports created by manual workflow |

## Phase 4 - Verify
Status: Blocked
Deliverable: checklist + actual comparison results from this run
Gate to next phase: operator reviews source quality before any production migration decision.

| Check | Result |
| --- | --- |
| 8 AM / 2 PM production cron untouched | Yes - this workflow is workflow_dispatch only |
| No signals.json/live brief/ntfy writes | Yes - report-only workflow |
| Zero Birdclaw live writes | Yes - allowlist excludes compose/reply/block/mute; BIRDCLAW_DISABLE_LIVE_WRITES=1 |
| Zero new recurring cost | Yes - no schedule added |
| Birdclaw auth ready | Yes |
| Agent-Reach/twitter-cli returned records | Yes |
| Birdclaw returned records | No |

### Results
| Metric | Agent-Reach/twitter-cli | Birdclaw |
| --- | --- | --- |
| Records | 20 | 0 |
| Unique records | 20 | 0 |
| Overlap | 0 | 0 |
| Avg field count | 1.4 | 0 |
| Calls | 14 | 20 |
| Total latency ms | 47737 | 249162 |
| Median latency ms | 2936 | 473 |
| Max latency ms | 7293 | 30583 |
| Errors | 4 | 10 |

### Field Richness
| Source | Top fields |
| --- | --- |
| Agent-Reach/twitter-cli | text (20), url (8) |
| Birdclaw | No records |

### Unique Samples
#### Unique to Agent-Reach/twitter-cli

| Author | Tweet ID | URL | Text |
| --- | --- | --- | --- |
| sama |  |  | @sama (Sam Altman): We want to help all companies be secure, working with the USG and the security ecosystem. |
| sama |  |  | *The full version of GPT-5.5-Cyber is here; state of the art performance on CyberGym. |
| sama | 2069121360744550796 | https://x.com/sama/status/2069121360744550796 | *Patch The Planet and Codex Security will help solve security problems instead of just finding them. https://t.co/otyCFHJR4d 🖼️ https://pbs.twimg.com/media/HLb- |
| sama | 2067402274662744465 | https://x.com/polynoamial/status/2067402274662744465 | @sama (Sam Altman): We offer no explanation as to why Noams are so good at AI; we attribute their success, as all else, to divine benevolence. ┌─ QT @polynoamia |
| sama |  |  | @sama (Sam Altman): theUSshould lead on AI by continuing to develop the very best models, making sure they're safe, and getting cyber tools into the hands of tr |

#### Unique to Birdclaw

No records.

#### Overlap samples

No records.

### Auth / Setup Friction
| Item | Result |
| --- | --- |
| Manual setup note | Birdclaw live reads need a separate xurl OAuth2 setup or a local bird browser-cookie session. The existing TWITTER_COOKIE secret helps the production twitter-cli path, but Birdclaw docs do not treat it as a direct auth substitute. |
| birdclaw auth status | {"installed": true, "availableTransport": "local", "statusText": "xurl installed but not authenticated. local (bird) mode active.", "rawStatus": "No apps registered. Use 'xurl auth apps add' to register one."} |
| xurl_whoami_returncode | 1 |
| bird_whoami_returncode | 1 |
| xurl_whoami_error |  |
| bird_whoami_error | ⚠️ No Twitter cookies found in Safari. Make sure you are logged into x.com in Safari.<br>⚠️ Chrome cookies database not found.<br>⚠️ No Twitter cookies found in Chrome. Make sure you are logged into x.com in Chrome.<br>⚠️ Firefox cookies database not found.<br>⚠️ No Twitter cookies found in Firefox. Make sure y |

### Errors Encountered
#### Agent-Reach/twitter-cli

| Command | Exit | stderr |
| --- | --- | --- |
| twitter search 'from:sama (AI OR agents OR LLM OR GPT OR reasoning)' | 1 | WARNING twitter_cli.client: Failed to init ClientTransaction: 'NoneType' object has no attribute 'group' |
| opencli twitter search 'from:sama (AI OR agents OR LLM OR GPT OR reasoning)' | 127 | [Errno 2] No such file or directory: 'opencli' |
| opencli twitter search 'from:karpathy (AI OR agents OR LLM OR GPT OR reasoning)' | 127 | [Errno 2] No such file or directory: 'opencli' |
| opencli twitter search 'from:ylecun (AI OR agents OR LLM OR GPT OR reasoning)' | 127 | [Errno 2] No such file or directory: 'opencli' |

#### Birdclaw

| Command | Exit | stderr |
| --- | --- | --- |
| xurl whoami | 1 |  |
| bird whoami | 1 | ⚠️ No Twitter cookies found in Safari. Make sure you are logged into x.com in Safari.<br>⚠️ Chrome cookies database not found.<br>⚠️ No Twitter cookies found in Chrome. Make sure you are logged into x.com in Chrome.<br>⚠️ Firefox cookies database not found.<br>⚠️ No Twitter cookies found in Firefox. Make sure y |
| birdclaw discuss 'from:sama (AI OR agents OR LLM OR GPT OR reasoning)' --mode auto --limit 20 --max-pages 2 --refresh --json | 1 | Live tweet search failed via auto: Command failed: /bin/bash -c out="$1"; shift; exec "$@" > "$out" birdclaw-bird /tmp/birdclaw-bird-TFXYth/stdout.json /opt/hostedtoolcache/node/26.4.0/x64/bin/bird search from:sama ([REDACTED]) -n 20 --json --all --max-pages 2<br>⚠️ No Twitter cookies found in Safari.  |
| birdclaw discuss 'from:karpathy (AI OR agents OR LLM OR GPT OR reasoning)' --mode auto --limit 20 --max-pages 2 --refresh --json | 1 | Live tweet search failed via auto: Command failed: /bin/bash -c out="$1"; shift; exec "$@" > "$out" birdclaw-bird /tmp/birdclaw-bird-wyBS4Z/stdout.json /opt/hostedtoolcache/node/26.4.0/x64/bin/bird search from:karpathy ([REDACTED]) -n 20 --json --all --max-pages 2<br>⚠️ No Twitter cookies found in Safa |
| birdclaw discuss 'from:AndrewYNg (AI OR agents OR LLM OR GPT OR reasoning)' --mode auto --limit 20 --max-pages 2 --refresh --json | 1 | Live tweet search failed via auto: Command failed: /bin/bash -c out="$1"; shift; exec "$@" > "$out" birdclaw-bird /tmp/birdclaw-bird-qzxT8Y/stdout.json /opt/hostedtoolcache/node/26.4.0/x64/bin/bird search from:AndrewYNg ([REDACTED]) -n 20 --json --all --max-pages 2<br>⚠️ No Twitter cookies found in Saf |
| birdclaw discuss 'from:ylecun (AI OR agents OR LLM OR GPT OR reasoning)' --mode auto --limit 20 --max-pages 2 --refresh --json | 1 | Live tweet search failed via auto: Command failed: /bin/bash -c out="$1"; shift; exec "$@" > "$out" birdclaw-bird /tmp/birdclaw-bird-B7HvpR/stdout.json /opt/hostedtoolcache/node/26.4.0/x64/bin/bird search from:ylecun ([REDACTED]) -n 20 --json --all --max-pages 2<br>⚠️ No Twitter cookies found in Safari |
| birdclaw discuss 'from:demishassabis (AI OR agents OR LLM OR GPT OR reasoning)' --mode auto --limit 20 --max-pages 2 --refresh --json | 1 | Live tweet search failed via auto: Command failed: /bin/bash -c out="$1"; shift; exec "$@" > "$out" birdclaw-bird /tmp/birdclaw-bird-GHnKqr/stdout.json /opt/hostedtoolcache/node/26.4.0/x64/bin/bird search from:demishassabis ([REDACTED]) -n 20 --json --all --max-pages 2<br>⚠️ No Twitter cookies found in |
| birdclaw discuss 'from:OpenAI (AI OR agents OR LLM OR GPT OR reasoning)' --mode auto --limit 20 --max-pages 2 --refresh --json | 1 | Live tweet search failed via auto: Command failed: /bin/bash -c out="$1"; shift; exec "$@" > "$out" birdclaw-bird /tmp/birdclaw-bird-uPQjae/stdout.json /opt/hostedtoolcache/node/26.4.0/x64/bin/bird search from:OpenAI ([REDACTED]) -n 20 --json --all --max-pages 2<br>⚠️ No Twitter cookies found in Safari |
| birdclaw discuss 'from:AnthropicAI (AI OR agents OR LLM OR GPT OR reasoning)' --mode auto --limit 20 --max-pages 2 --refresh --json | 1 | Live tweet search failed via auto: Command failed: /bin/bash -c out="$1"; shift; exec "$@" > "$out" birdclaw-bird /tmp/birdclaw-bird-uLv6kG/stdout.json /opt/hostedtoolcache/node/26.4.0/x64/bin/bird search from:AnthropicAI ([REDACTED]) -n 20 --json --all --max-pages 2<br>⚠️ No Twitter cookies found in S |
| birdclaw discuss 'from:GoogleDeepMind (AI OR agents OR LLM OR GPT OR reasoning)' --mode auto --limit 20 --max-pages 2 --refresh --json | 1 | Live tweet search failed via auto: Command failed: /bin/bash -c out="$1"; shift; exec "$@" > "$out" birdclaw-bird /tmp/birdclaw-bird-kLvNci/stdout.json /opt/hostedtoolcache/node/26.4.0/x64/bin/bird search from:GoogleDeepMind ([REDACTED]) -n 20 --json --all --max-pages 2<br>⚠️ No Twitter cookies found i |
