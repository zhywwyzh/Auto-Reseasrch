#!/usr/bin/env python3
"""Reject private files in every reachable commit, including outgoing pushes."""
import argparse
from pathlib import Path
import subprocess
import sys

from check_git_scope import content_violations, private_markers


def inspect(repo, revision):
    commits = subprocess.check_output(['git', '-C', str(repo), 'rev-list', revision], text=True).splitlines()
    failures = []
    seen_trees = set()
    markers = private_markers(repo)
    for commit in commits:
        message = subprocess.check_output(['git', '-C', str(repo), 'show', '-s', '--format=%B', commit], text=True)
        if any(marker in message for marker in markers):
            failures.append((commit, '<commit-message>', 'private content'))
        tree = subprocess.check_output(['git', '-C', str(repo), 'rev-parse', commit + '^{tree}'], text=True).strip()
        if tree in seen_trees:
            continue
        seen_trees.add(tree)
        listing = subprocess.check_output(['git', '-C', str(repo), 'ls-tree', '-r', '-z', commit])
        paths, entries = [], []
        for item in listing.split(b'\0'):
            if not item:
                continue
            meta, raw_name = item.split(b'\t', 1)
            mode, kind, oid = meta.decode().split()
            name = raw_name.decode()
            paths.append(name)
            if mode == '120000':
                failures.append((commit, name, 'symlink'))
            elif kind == 'blob':
                entries.append((name, oid))
        ignored = subprocess.run(['git', '-C', str(repo), 'check-ignore', '--no-index', '-z', '--stdin'],
                                 input=b''.join(p.encode() + b'\0' for p in paths), capture_output=True)
        if ignored.returncode not in (0, 1):
            raise RuntimeError(ignored.stderr.decode(errors='replace'))
        failures.extend((commit, p.decode(), 'private path') for p in ignored.stdout.split(b'\0') if p)
        failures.extend((commit, path, 'private content') for path in content_violations(repo, entries))
    return commits, failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--revision', default='HEAD')
    parser.add_argument('--pre-push', action='store_true')
    args = parser.parse_args()
    revisions = [args.revision]
    if args.pre_push:
        revisions = []
        for line in sys.stdin:
            local_ref, local_sha, remote_ref, remote_sha = line.split()
            if set(local_sha) != {'0'}:
                if not remote_ref.startswith(('refs/heads/', 'refs/tags/')):
                    print('Git push rejected: internal snapshots and notes are local-only.', file=sys.stderr)
                    return 1
                peeled = subprocess.run(['git', '-C', str(args.repo), 'rev-parse', '--verify', local_sha + '^{commit}'],
                                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                if peeled.returncode:
                    print('Git push rejected: only commit histories may be published.', file=sys.stderr)
                    return 1
                kind = subprocess.check_output(['git', '-C', str(args.repo), 'cat-file', '-t', local_sha], text=True).strip()
                if kind == 'tag':
                    annotation = subprocess.check_output(['git', '-C', str(args.repo), 'cat-file', 'tag', local_sha], text=True)
                    if any(marker in annotation for marker in private_markers(args.repo)):
                        print('Git push rejected: tag annotation contains private task content.', file=sys.stderr)
                        return 1
                normalized = ''.join(c for c in remote_ref.casefold() if c.isalnum())
                if any(''.join(c for c in marker.casefold() if c.isalnum()) in normalized
                       for marker in private_markers(args.repo)):
                    print('Git push rejected: remote reference contains a local task identifier.', file=sys.stderr)
                    return 1
                revisions.append(local_sha)
    count = 0
    for revision in set(revisions):
        commits, failures = inspect(args.repo, revision)
        count += len(commits)
        if failures:
            for commit, path, reason in failures[:40]:
                print(f'Git history rejected: {commit[:12]} {reason}: {path}', file=sys.stderr)
            return 1
    print(f'Git history OK: inspected {count} reachable commits.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
