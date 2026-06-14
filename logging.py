from __future__ import annotations

import importlib.util
import sys
import sysconfig
from pathlib import Path

_stdlib_logging = Path(sysconfig.get_paths()["stdlib"]) / "logging" / "__init__.py"
_spec = importlib.util.spec_from_file_location(
    __name__,
    _stdlib_logging,
    submodule_search_locations=[str(_stdlib_logging.parent)],
)

if _spec is None or _spec.loader is None:
    raise ImportError("could not load stdlib logging module")

_spec.loader.exec_module(sys.modules[__name__])
