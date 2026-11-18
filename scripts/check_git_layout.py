#!/usr/bin/env python3
"""Require one repository; dependencies are files and tasks are ignored folders."""
import argparse
import json
import os
from pathlib import Path
import subprocess


def inspect(repo):
    repo = Path(repo).resolve()
    nested = []
    empty = []
    for parent, directories, files in os.walk(repo, followlinks=False):
        if Path(parent) != repo and ('.git' in directories or '.git' in files):
            marker = Path(parent) / '.git'
            name = str(marker.relative_to(repo))
            # Empty protected directories carry no repository or history.
            if marker.is_dir() and not marker.is_symlink() and not any(marker.iterdir()):
                empty.append(name)
            else:
                nested.append(name)
        directories[:] = [name for name in directories if name not in
                          {'.git', 'node_modules', '.venv', 'venv', '__pycache__', '.cache'}]
    index = subprocess.check_output(['git', '-C', str(repo), 'ls-files', '--stage', '-z'])
    links = [item.split(b'\t', 1)[1].decode() for item in index.split(b'\0')
             if item.startswith(b'160000 ')]
    listing = subprocess.check_output(['git', '-C', str(repo), 'worktree', 'list', '--porcelain'], text=True)
    worktrees = [line[9:] for line in listing.splitlines() if line.startswith('worktree ')]
    return {'nested_git': nested, 'empty_git_placeholders': empty,
            'gitlinks': links, 'worktrees': worktrees,
            'passed': not nested and not links and len(worktrees) == 1}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    result = inspect(args.repo)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return int(not result['passed'])


if __name__ == '__main__':
    raise SystemExit(main())
