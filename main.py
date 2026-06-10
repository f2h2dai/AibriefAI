name: Monitor Aibrief Freshness

on:
  schedule:
    - cron: "*/5 * * * *"
  workflow_dispatch:

permissions:
  contents: read

jobs:
  freshness:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Verify signals.json freshness
        run: python scripts/check_signals_freshness.py --path web/data/signals.json --max-age-seconds 900
