name: Update Aibrief Feed

on:
  schedule:
    - cron: "*/5 * * * *"
  workflow_dispatch:

permissions:
  contents: write
  actions: read

concurrency:
  group: aibrief-feed
  cancel-in-progress: true

env:
  ENVIRONMENT: production
  LOG_LEVEL: INFO
  PIPELINE_INTERVAL_MINUTES: "5"
  GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
  GEMINI_MODEL: ${{ vars.GEMINI_MODEL || 'gemini-2.5-flash' }}
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
  GROQ_MODEL: ${{ vars.GROQ_MODEL || 'llama-3.3-70b-versatile' }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
  SENTRY_DSN: ${{ secrets.SENTRY_DSN }}
  ALERT_EMAIL_TO: Fmg_511@hotmail.com
  AIBRIEF_LLM_ENABLED: "true"

jobs:
  update:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: "pip"
      - name: Install package
        run: python -m pip install -e ".[dev]"
      - name: Secret scan
        run: ./scripts/secret_scan.sh
      - name: Compile
        run: python -m compileall -q aibrief scripts cli
      - name: Run tests
        env:
          AIBRIEF_LLM_ENABLED: "false"
        run: python -m pytest -q
      - name: Run Aibrief pipeline
        run: python scripts/run_pipeline.py --topic ai-agents --limit 8 --emit-html
      - name: Verify generated artifacts
        run: |
          test -s data/latest_report.json
          test -s web/data/signals.json
          test -s web/brief.html
          test -s web/health.json
          test -s web/health/index.html
      - name: Commit generated feed
        run: |
          git config user.name "aibrief-bot"
          git config user.email "aibrief-bot@example.com"
          git add data/latest_report.json web/data/signals.json web/brief.html web/health.json web/health/index.html data/usage || true
          git diff --cached --quiet && echo "No changes" && exit 0
          git commit -m "Update Aibrief feed [skip ci]"
          git push
