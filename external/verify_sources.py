#!/usr/bin/env python3
"""Verify vendored public source without network access or upstream execution."""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys


def safe_path(root, name):
    parts = PurePosixPath(name)
    if not name or parts.is_absolute() or any(p in {'.', '..', '.git'} for p in parts.parts):
        raise ValueError('Invalid manifest path: ' + name)
    path = root
    for part in parts.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Source path cannot be a symlink: ' + name)
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Source path escapes the source root: ' + name)
    return path


def verify(root, group=None):
    root = Path(root)
    lock = json.loads((root / 'sources.lock.json').read_text())
    if lock.get('format') != 1 or lock.get('mode') != 'vendored-source':
        raise ValueError('Unsupported source manifest')
    failures = []
    files = total = repos = 0
    for row in lock['repositories']:
        relative = row['path']
        prefix = 'external/'
        if not relative.startswith(prefix):
            raise ValueError('Repository must be inside external/')
        relative = relative[len(prefix):]
        repo = safe_path(root, relative)
        if group and relative.split('/')[0] != group:
            continue
        repos += 1
        for entry in row['files']:
            path = safe_path(repo, entry['path'])
            if not path.is_file():
                failures.append(str(path.relative_to(root)) + ': missing')
                continue
            raw = path.read_bytes()
            files += 1
            total += len(raw)
            if hashlib.sha256(raw).hexdigest() != entry['sha256']:
                failures.append(str(path.relative_to(root)) + ': changed from recorded upstream source')
    if not repos:
        raise ValueError('No source repositories selected')
    # Scan all external directories, including ones not selected by the group.
    # Unlisted local data is allowed; independent Git management is not.
    for parent, directories, names in os.walk(root, followlinks=False):
        if '.git' in directories or '.git' in names:
            failures.append(str((Path(parent) / '.git').relative_to(root)) + ': nested Git metadata')
        directories[:] = [d for d in directories if d not in {'.git', 'node_modules', '.venv', '__pycache__'}]
    return {'repositories': repos, 'files_checked': files, 'bytes_checked': total, 'failures': failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--group', choices=['autonomous-science', 'ai-paper-tools'])
    args = parser.parse_args()
    try:
        result = verify(Path(__file__).resolve().parent, args.group)
    except (ValueError, OSError, KeyError) as exc:
        print('Source verification failed: ' + str(exc), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(bool(result['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
