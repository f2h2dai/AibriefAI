#!/usr/bin/env sh
set -eu
if command -v gitleaks >/dev/null 2>&1; then
  exec gitleaks detect --source . --config .gitleaks.toml --redact --verbose
fi
if command -v docker >/dev/null 2>&1; then
  exec docker run --rm -v "$PWD:/repo" zricethezav/gitleaks:latest detect --source /repo --config /repo/.gitleaks.toml --redact --verbose
fi
printf '%s\n' "gitleaks and docker unavailable; running strict local fallback scan" >&2
if grep -RInE "AIza[0-9A-Za-z_-]{30,}|gsk_[A-Za-z0-9_-]{20,}" . \
  --binary-files=without-match \
  --exclude-dir=.git \
  --exclude-dir=.aibrief \
  --exclude-dir=__pycache__ \
  --exclude-dir=.pytest_cache \
  --exclude-dir=.mypy_cache \
  --exclude-dir=.ruff_cache \
  --exclude-dir=.venv \
  --exclude='*.pyc' \
  --exclude='*.zip' \
  --exclude='*.tar'; then
  echo "Gemini/Groq secret-like value found" >&2
  exit 1
fi
printf '%s\n' "PASS: fallback secret scan found no Gemini/Groq secrets"
