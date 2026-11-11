#!/usr/bin/env python3
"""Fetch pinned public upstream submodules, without executing upstream code.

Only this collection's .gitmodules entries and gitlinks are staged by git itself.
No commit, push, dependency installation, LFS smudge, training or agent execution.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'docs/research/autonomous-science-2026-11-10/library'


def run(*args, cwd=ROOT, **kw):
    return subprocess.check_output(list(args), cwd=cwd, text=True, **kw).strip()


def sparse_source_checkout(dest, files):
    """Keep code and small documents; do not alter a dirty upstream worktree."""
    if run('git', 'status', '--porcelain', cwd=dest):
        return {'applied': False, 'reason': 'dirty worktree preserved'}
    patterns = ['/*']
    suffixes = ['pdf', 'png', 'jpg', 'jpeg', 'gif', 'mp4', 'webm', 'zip', 'tar',
                'gz', 'pt', 'pth', 'ckpt', 'safetensors', 'onnx', 'log', 'inopkg', 'projectarchive']
    patterns.extend('!*.' + s for s in suffixes)
    large = []
    for name in files:
        path = dest / name
        if path.is_file() and path.stat().st_size > 5 * 1024 * 1024:
            large.append(name)
    # Escape gitignore metacharacters for exact large-file exclusions.
    def escaped(name):
        return ''.join('\\' + c if c in '\\*?[]!# ' else c for c in name)
    patterns.extend('!/' + escaped(name) for name in large)
    subprocess.run(['git', 'sparse-checkout', 'set', '--no-cone', '--stdin'],
                   input='\n'.join(patterns) + '\n', text=True, cwd=dest, check=True)
    return {'applied': True, 'excluded_binary_suffixes': suffixes,
            'excluded_large_files': len(large), 'large_file_limit_bytes': 5 * 1024 * 1024,
            'note': 'Git history may contain already-transferred blobs; sparse checkout only limits the worktree. LFS payloads were never fetched.'}


def main():
    registry = json.loads((LIB / 'registry.json').read_text())
    records = []
    for repo in registry['repositories']:
        relative = 'external/autonomous-science/' + repo['id']
        dest = ROOT / relative
        record = {**repo, 'path': relative, 'retrieved': '2026-11-10'}
        try:
            if not (dest / '.git').exists():
                print('Fetching ' + repo['id'], flush=True)
                env = dict(os.environ, GIT_LFS_SKIP_SMUDGE='1', GIT_TERMINAL_PROMPT='0')
                subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', 'submodule', 'add', '--depth', '1', '--', repo['url'], relative], cwd=ROOT, env=env, check=True, timeout=240)
            origin = run('git', 'remote', 'get-url', 'origin', cwd=dest)
            if origin.rstrip('/').removesuffix('.git') != repo['url'].rstrip('/').removesuffix('.git'):
                raise ValueError('existing checkout origin differs; left unchanged')
            record['commit'] = run('git', 'rev-parse', 'HEAD', cwd=dest)
            record['commit_date'] = run('git', 'show', '-s', '--format=%cI', 'HEAD', cwd=dest)
            record['status'] = 'fetched-pinned-submodule'
            files = run('git', 'ls-files', cwd=dest).splitlines()
            record['sparse_checkout'] = sparse_source_checkout(dest, files)
            licences = [p for p in files if '/' not in p and p.upper().startswith(('LICENSE', 'LICENCE', 'COPYING'))]
            record['license_files'] = []
            for name in licences:
                content = (dest / name).read_bytes()
                record['license_files'].append({'path': name, 'sha256': hashlib.sha256(content).hexdigest(), 'excerpt': content[:250].decode(errors='replace')})
            record['license_status'] = 'root-license-present-needs-scope-review' if licences else 'no-root-license-found-not-assumed-open-source'
            text = '\n'.join((dest / n).read_text(errors='replace') for n in licences)
            if 'The AI Scientist Source Code License' in text:
                record.update(license_name='The AI Scientist Source Code License 1.0',
                              license_status='source-available-custom-use-restrictions')
            elif 'Apache License' in text and 'Version 2.0' in text:
                record.update(license_name='Apache-2.0', license_status='standard-open-source-code-license')
            elif 'MIT License' in text:
                record.update(license_name='MIT', license_status='standard-open-source-code-license')
            else:
                readme = dest / 'README.md'
                if readme.exists() and '\n## License\n\nMIT' in readme.read_text(errors='replace'):
                    record.update(license_name='MIT (README declaration; no standalone LICENSE)',
                                  license_status='readme-license-declaration-only')
                else:
                    record['license_name'] = 'Not established for whole repository'
            if repo['id'] == 'discern':
                record['license_scope_note'] = 'Author code MIT; datasets and runtime resources have mixed terms. See THIRD_PARTY_NOTICES.md.'
            if repo['id'] == 'mombot-software':
                record['license_scope_note'] = 'Actual root LICENSE is MIT; README still contains an outdated no-license placeholder.'
            pointers = []
            for name in files:
                path = dest / name
                if path.is_file() and path.stat().st_size < 1024:
                    if path.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'):
                        pointers.append(name)
            record['lfs_pointer_count'] = len(pointers)
            record['lfs_note'] = 'LFS payloads were not fetched; pointers are not usable datasets or weights.'
            record['tracked_files'] = len(files)
            record['worktree_bytes'] = sum((dest / p).stat().st_size for p in files if (dest / p).is_file())
            print(json.dumps({k: record.get(k) for k in ['id', 'commit', 'license_status', 'tracked_files', 'worktree_bytes', 'lfs_pointer_count']}, ensure_ascii=False), flush=True)
        except Exception as exc:
            record['status'] = 'fetch-failed'
            record['error'] = str(exc)
            print(json.dumps({'id': repo['id'], 'error': str(exc)}, ensure_ascii=False), flush=True)
        records.append(record)
        (LIB / 'repositories.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
