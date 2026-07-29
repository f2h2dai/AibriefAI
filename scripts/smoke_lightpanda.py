#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aibrief.connectors.browser_router import BrowserExecutionError, fetch_public_page


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a real public-page Lightpanda smoke test.")
    parser.add_argument("--url", default="https://example.com/")
    parser.add_argument("--contains", default="Example Domain")
    args = parser.parse_args()

    try:
        result = fetch_public_page(args.url, fallback_fetcher=None)
    except BrowserExecutionError as exc:
        print(json.dumps({"status": "error", "reason": str(exc)}, sort_keys=True))
        return 1

    if result.backend != "lightpanda" or result.fallback_used:
        print(json.dumps({"status": "error", "reason": "Lightpanda was not the active backend"}, sort_keys=True))
        return 1
    if args.contains and args.contains.casefold() not in result.content.casefold():
        print(json.dumps({"status": "error", "reason": "expected page content was missing"}, sort_keys=True))
        return 1

    print(
        json.dumps(
            {
                "backend": result.backend,
                "content_chars": len(result.content),
                "fallback_used": result.fallback_used,
                "status": "ok",
                "url": result.url,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
