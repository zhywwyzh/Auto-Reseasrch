#!/usr/bin/env python3
"""Compatibility entry point: verify source already managed by the main repository."""
from pathlib import Path
import subprocess
import sys

if __name__ == '__main__':
    root = Path(__file__).resolve().parents[1]
    raise SystemExit(subprocess.call([sys.executable, str(root / 'verify_sources.py'),
                                     '--group', 'ai-paper-tools']))
