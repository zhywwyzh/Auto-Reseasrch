"""Identify deployed Python source, independently of a human release label."""
import hashlib
from pathlib import Path
import local_extensions

HERE = Path(__file__).resolve().parent


def revision():
    digest = hashlib.sha256()
    for path in sorted(HERE.glob('*.py')):
        digest.update(path.name.encode() + b'\0' + local_extensions.source_path(path).read_bytes() + b'\0')
    return digest.hexdigest()


# Captured at process import; never relabel an old process with today's source.
LOADED = revision()


def describe():
    current = revision()
    return {'loaded': LOADED, 'on_disk': current, 'matches_disk': LOADED == current}
