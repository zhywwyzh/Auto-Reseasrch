#!/usr/bin/env python3
"""Compatibility entry point: verify vendored source; never recreate submodules."""
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(subprocess.call([sys.executable, str(root / 'external/verify_sources.py'),
                                     '--group', 'autonomous-science']))
