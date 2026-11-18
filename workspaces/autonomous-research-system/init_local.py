#!/usr/bin/env python3
"""Create missing local-only registries without overwriting data or starting jobs."""
import argparse
import datetime as dt
import json
from pathlib import Path
import subprocess


def initialize(repo):
    repo = Path(repo).resolve()
    system = repo / 'workspaces/autonomous-research-system'
    documents = {
        repo / 'workspaces/topics.json': {
            'date': dt.date.today().isoformat(), 'scope': 'Local task registry; never upload to Git.',
            'audit': 'Empty registry created by init_local.py; no task or server inferred.',
            'shared': ['docs/research/', 'templates/'], 'topics': []},
        system / 'research-goals.json': {
            'version': 'local-only-v1', 'status': 'No local tasks registered.',
            'model': '', 'initial_budget': {'max_calls': 0, 'max_seconds': 0, 'max_tokens': 0},
            'budget_note': 'Configured separately for each local task.',
            'common': 'Preserve evidence and task boundaries; verify actual results.', 'topics': []},
        system / 'execution-targets.json': {
            'version': 'local-only-v1', 'default_experiment_target': None,
            'scope': 'Local execution targets; credentials are never stored here.', 'targets': []},
        system / 'resource-allocations.json': {
            'version': 'local-only-v1', 'target': None, 'allocations': {}},
        repo / '.local/workspace-capabilities.json': {'paper_topics': []},
        repo / 'docs/research/ai-paper-review/aas-writing-samples.json': {'samples': [], 'topics': {}},
    }
    created = []
    for path, value in documents.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            # Exclusive creation also protects a concurrent user's new file.
            with path.open('x', encoding='utf-8') as output:
                json.dump(value, output, ensure_ascii=False, indent=2)
                output.write('\n')
        except FileExistsError:
            continue
        created.append(str(path.relative_to(repo)))
    for name in ('runtime.html', 'index.html', 'system.html', 'usage.html', 'journal-review.html', 'research-goals.html'):
        path = system / name
        try:
            with path.open('x', encoding='utf-8') as output:
                output.write('<!doctype html><html lang="zh-CN"><meta charset="utf-8"><title>自主研究工作台</title><body><h1>自主研究工作台</h1><p>通用平台源码不包含研究任务。请先在 ui 目录运行 npm ci 和 npm run build，然后刷新。</p></body></html>\n')
        except FileExistsError:
            continue
        created.append(str(path.relative_to(repo)))
    # Fresh clones do not inherit local Git config. Respect an existing custom
    # hooks directory; otherwise install the shared pre-commit check.
    if (repo / '.githooks/pre-commit').is_file():
        git = subprocess.run(['git', '-C', str(repo), 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True)
        if git.returncode == 0 and Path(git.stdout.strip()).resolve() == repo:
            current = subprocess.run(['git', '-C', str(repo), 'config', '--get', 'core.hooksPath'],
                                     capture_output=True, text=True)
            if current.returncode == 1:
                subprocess.run(['git', '-C', str(repo), 'config', '--local', 'core.hooksPath', '.githooks'], check=True)
    return created


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    created = initialize(args.repo)
    print(json.dumps({'created': created, 'existing_files_overwritten': 0,
                      'model_calls': 0, 'research_jobs_started': 0}, ensure_ascii=False))


if __name__ == '__main__':
    main()
