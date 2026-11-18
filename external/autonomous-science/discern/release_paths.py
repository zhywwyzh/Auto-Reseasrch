"""Resolve archived anonymous paths without changing recorded artifacts on disk."""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def relocate(value):
    if isinstance(value, dict):
        return {k: relocate(v) for k, v in value.items()}
    if isinstance(value, list):
        return [relocate(v) for v in value]
    if isinstance(value, tuple):
        return tuple(relocate(v) for v in value)
    if not isinstance(value, str):
        return value
    value = value.replace('/workspace/discern-benchmark', str(ROOT))
    value = value.replace('/data/anonymous/dna_token/hg38.fa',
        os.environ.get('DISCERN_HG38', str(ROOT / 'resources/hg38.fa')))
    value = value.replace('/home/anonymous/.cache/torch/hub',
        os.environ.get('DISCERN_TORCH_HUB', str(ROOT / 'resources/torch/hub')))
    value = value.replace('/home/anonymous/.cache/torch',
        str(Path(os.environ.get('DISCERN_TORCH_HUB', str(ROOT / 'resources/torch/hub'))).parent))
    # A release environment supplies its own interpreter. No private venv is required.
    if value.startswith(('/workspace/', '/home/anonymous/', '/data/anonymous/')) and value.endswith('/bin/python'):
        return os.environ.get('DISCERN_SANDBOX_PYTHON', sys.executable)
    return value
