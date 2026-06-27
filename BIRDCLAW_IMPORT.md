# Birdclaw Import For AIbrief

Birdclaw stays local. Do not put a Birdclaw SQLite database, X archive, cookies, DMs, likes, bookmarks, or private backup repo in GitHub Actions.

AIbrief can read a sanitized local export from:

```text
private/birdclaw-export.json
```

That folder is ignored by Git.

## Recommended Local Export

Use the one-command local bridge:

```bash
python tools/run_birdclaw_import.py
```

On Windows PowerShell:

```powershell
python .\tools\run_birdclaw_import.py
```

It runs Birdclaw locally, writes a private sanitized export, then refreshes
`web/data/breaking_status.json` in website-only X mode. The default query is
tuned for public X intel around Grok Gov, Project Maven, Pentagon/DoD,
Operation Epic Fury, Iran, munitions, and AI targeting.

If Birdclaw is not installed globally, the runner will try `pnpm dlx
birdclaw@0.8.5`. If X auth is missing, log in to `x.com` in Chrome/Firefox/Safari
or configure Birdclaw/xurl locally, then run the same command again.

## Manual Local Export

Run Birdclaw locally, then export public tweet-like records only:

```bash
mkdir -p private
birdclaw search tweets '"Grok Gov" OR "Grok Gov Model" OR "Project Maven" OR Pentagon OR DoD OR "Department of Defense" OR "Operation Epic Fury" OR Iran OR munitions OR targeting OR "AI targeting" OR "target selection" OR "military operations"' --hide-low-quality --limit 100 --json > private/birdclaw-export.json
```

Then test the breaking monitor locally:

```bash
BIRDCLAW_EXPORT_PATH=private/birdclaw-export.json BREAKING_SOURCE_FOCUS=x python -m aibrief.breaking_monitor
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force private
birdclaw search tweets '"Grok Gov" OR "Grok Gov Model" OR "Project Maven" OR Pentagon OR DoD OR "Department of Defense" OR "Operation Epic Fury" OR Iran OR munitions OR targeting OR "AI targeting" OR "target selection" OR "military operations"' --hide-low-quality --limit 100 --json > private\birdclaw-export.json
$env:BIRDCLAW_EXPORT_PATH = "private\birdclaw-export.json"
$env:BREAKING_SOURCE_FOCUS = "x"
python -m aibrief.breaking_monitor
```

## Safety Rules

- AIbrief reads JSON or JSONL only.
- DM/direct-message collections are skipped.
- Records must include public X/Twitter URLs, or enough public tweet metadata to build one.
- Missing or malformed exports are ignored with a warning.
- Nothing from `private/` is committed or deployed.

## GitHub Actions

The scheduled GitHub workflow does not install or run Birdclaw. Birdclaw is a local memory layer; GitHub Actions still uses the existing public/sanitized sources and classifier gate.
