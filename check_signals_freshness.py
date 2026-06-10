from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from aibrief.cli import main

if __name__ == "__main__":
    args = ["analyze"] + sys.argv[1:]
    raise SystemExit(main(args))
