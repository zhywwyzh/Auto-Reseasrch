#!/usr/bin/env python3
"""Reject tracked/staged files outside the public Git allowlist, even after add -f."""
import argparse
import json
from pathlib import Path
import subprocess
import sys


def private_markers(repo):
    """Markers come from ignored local registration, never from public code."""
    repo = Path(repo)
    markers = set()
    catalog = repo / 'workspaces/topics.json'
    if catalog.is_file():
        for row in json.loads(catalog.read_text()).get('topics', []):
            for field in ('id', 'workspace', 'docs', 'paper_reserved', 'input'):
                value = row.get(field)
                if isinstance(value, str) and len(value) >= 5:
                    markers.add(value)
                    if field in ('workspace', 'paper_reserved'):
                        markers.add(Path(value).name)
    extra = repo / '.local/git-private-markers.json'
    if extra.is_file():
        values = json.loads(extra.read_text())
        if not isinstance(values, list) or any(not isinstance(v, str) or len(v) < 5 for v in values):
            raise ValueError('Local private marker configuration is invalid')
        markers.update(values)
    targets = repo / 'workspaces/autonomous-research-system/execution-targets.json'
    if targets.is_file():
        def endpoints(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key in ('host', 'hostname', 'remote_root') and isinstance(item, str) and len(item) >= 5:
                        markers.add(item)
                    endpoints(item)
            elif isinstance(value, list):
                for item in value:
                    endpoints(item)
        endpoints(json.loads(targets.read_text()))
    access = repo / '.local/workbench-access.json'
    if access.is_file():
        key = json.loads(access.read_text()).get('access_key')
        if isinstance(key, str) and len(key) >= 16:
            markers.add(key)
    return sorted(markers)


def content_violations(repo, entries):
    """Read Git blobs, including staged versions that differ from disk."""
    markers = [m.encode() for m in private_markers(repo)]
    if not markers:
        return []
    blocked = []
    seen = {}
    for name, oid in entries:
        if oid not in seen:
            raw = subprocess.check_output(['git', '-C', str(repo), 'cat-file', 'blob', oid])
            seen[oid] = any(marker in raw for marker in markers)
        if seen[oid]:
            blocked.append(name)
    return blocked


def check_content(repo):
    listing = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '--stage', '-z'])
    entries = []
    for item in listing.split(b'\0'):
        if not item:
            continue
        meta, name = item.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        if stage != '0':
            raise ValueError('Unmerged index cannot be published')
        if mode == '120000':
            raise ValueError('Public source cannot contain a symlink: ' + name.decode())
        if mode == '160000':
            raise ValueError('Nested repositories/submodules cannot be published: ' + name.decode())
        entries.append((name.decode(), oid))
    return content_violations(repo, entries)


def check(repo):
    repo = Path(repo)
    listing = subprocess.run(['git', '-C', str(repo), 'ls-files', '-z'], check=True, capture_output=True).stdout
    if not listing:
        return []
    paths = [item.decode('utf-8', errors='surrogateescape') for item in listing.split(b'\0') if item]
    probes = {}
    for name in paths:
        # A legacy index can contain children of a directory later replaced by
        # a local symlink. Git refuses check-ignore on those child pathspecs.
        # Check the link itself and still report every indexed child as private.
        parts = Path(name).parts
        probes[name] = name
        for index in range(1, len(parts)):
            parent = Path(*parts[:index])
            if (repo / parent).is_symlink():
                probes[name] = str(parent)
                break
    encoded = b''.join(name.encode('utf-8', errors='surrogateescape') + b'\0' for name in dict.fromkeys(probes.values()))
    result = subprocess.run(['git', '-C', str(repo), 'check-ignore', '--no-index', '-z', '--stdin'],
                            input=encoded, capture_output=True)
    if result.returncode not in (0, 1):
        raise RuntimeError(result.stderr.decode(errors='replace').strip())
    ignored = {item.decode('utf-8', errors='surrogateescape') for item in result.stdout.split(b'\0') if item}
    return [name for name in paths if probes[name] in ignored]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    blocked = check(args.repo)
    if blocked:
        print('Git scope rejected: local task/private files are still tracked or staged:', file=sys.stderr)
        for path in blocked:
            print('  ' + path, file=sys.stderr)
        print('Remove them from the index with git rm --cached; preserve local files.', file=sys.stderr)
        return 1
    contents = check_content(args.repo)
    if contents:
        print('Git scope rejected: staged source embeds local task identifiers, paths or session metadata:', file=sys.stderr)
        for path in contents:
            print('  ' + path, file=sys.stderr)
        return 1
    print('Git scope OK: no ignored paths or registered private task content in the index.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
