#!/usr/bin/env python3
"""Verify the shared source snapshot; never clone another Git repository."""
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(subprocess.call([sys.executable, str(root / 'external/verify_sources.py'),
                                     '--group', 'paper-review-ai']))
