"""Loads a local .env file (KEY=value lines) into the environment so API keys never live in code."""
import os
from pathlib import Path

_f = Path(__file__).parent.parent / ".env"
if _f.exists():
    for _line in _f.read_text().splitlines():
        if "=" in _line and not _line.lstrip().startswith("#"):
            _k, _v = _line.split("=", 1)
            os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))
