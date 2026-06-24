# Birdclaw Import For AIbrief

Birdclaw stays local. Do not put a Birdclaw SQLite database, X archive, cookies, DMs, likes, bookmarks, or private backup repo in GitHub Actions.

AIbrief can read a sanitized local export from:

```text
private/birdclaw-export.json
```

That folder is ignored by Git.

## Recommended Local Export

Run Birdclaw locally, then export public tweet-like records only:

```bash
mkdir -p private
birdclaw search tweets '"Grok Gov" OR "Grok Gov Model" OR "Project Maven" OR Pentagon OR "Operation Epic Fury" OR Iran OR munitions OR targeting' --hide-low-quality --limit 100 --json > private/birdclaw-export.json
```

Then test the breaking monitor locally:

```bash
BIRDCLAW_EXPORT_PATH=private/birdclaw-export.json BREAKING_SOURCE_FOCUS=x python -m aibrief.breaking_monitor
```

On Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force private
birdclaw search tweets '"Grok Gov" OR "Grok Gov Model" OR "Project Maven" OR Pentagon OR "Operation Epic Fury" OR Iran OR munitions OR targeting' --hide-low-quality --limit 100 --json > private\birdclaw-export.json
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
