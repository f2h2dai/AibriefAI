#!/usr/bin/env sh
set -eu
pattern='AIza[0-9A-Za-z_\-]{30,}|gsk_[A-Za-z0-9_\-]{20,}'

scan_worktree() {
  grep -RInE "$pattern" . \
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
    --exclude='*.tar' || true
}

if git rev-parse --git-dir >/dev/null 2>&1; then
  if git grep -n -E "$pattern" -- . ':!*.pyc' ':!*.zip' ':!*.tar'; then
    echo "secret-like Gemini/Groq/Sentry/GitHub value found in tracked files" >&2
    exit 1
  fi
  if git log -p --all --full-history -- . | grep -E "$pattern"; then
    echo "secret-like Gemini/Groq/Sentry/GitHub value found in git history" >&2
    exit 1
  fi
  printf '%s\n' "PASS: tracked files and git history contain no configured secret values"
else
  findings="$(scan_worktree)"
  if [ -n "$findings" ]; then
    printf '%s\n' "$findings" >&2
    echo "secret-like value found in working tree" >&2
    exit 1
  fi
  printf '%s\n' "PASS: no git repository detected; working tree contains no configured secret values"
fi
