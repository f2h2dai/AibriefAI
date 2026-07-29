from __future__ import annotations

import argparse
import json

from aibrief.connectors.browser_router import lightpanda_readiness, load_browser_config


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the AIbrief Lightpanda browser route.")
    parser.add_argument("--config", default="config/browser_router.json")
    parser.add_argument("--require-binary", action="store_true")
    args = parser.parse_args()

    status = lightpanda_readiness(load_browser_config(args.config))
    print(json.dumps(status, sort_keys=True))
    if args.require_binary and not status["lightpanda_available"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
