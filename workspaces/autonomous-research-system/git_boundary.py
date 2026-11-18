"""Require local research task paths to remain outside every Git upload index."""
import json
from pathlib import Path
import subprocess
import sys

VERSION = 'local-research-only-v1'
INSTRUCTION = (
    '本任务及其后续任务的全部研究内容只写入本地Git忽略区，包括代码、设计、原始资料、'
    '实验、结果、报告、稿件、审稿、授权和任务配置。不得把研究内容移入系统源码、公共文档或规则目录。'
    '只有可复用的智能系统实现、公共规则和通用工具可以进入Git；系统目录不是任务内容的上传豁免区。'
    '不得强制添加、提交或推送研究内容。修复系统代码时也不能把实际任务数据写进公共源码或测试。'
)


def _git_root(directory):
    directory = Path(directory).resolve()
    while not directory.is_dir():
        if directory.parent == directory:
            return None
        directory = directory.parent
    result = subprocess.run(['git', '-C', str(directory), 'rev-parse', '--show-toplevel'],
                            capture_output=True, text=True)
    return Path(result.stdout.strip()).resolve() if result.returncode == 0 else None


def _assert_private(path, label, owners):
    path = Path(path).resolve()
    owner = _git_root(path.parent if path.is_file() else path)
    if owner is None:
        return {'label': label, 'path': str(path), 'git': False}
    relative = str(path.relative_to(owner))
    ignored = subprocess.run(['git', '-C', str(owner), 'check-ignore', '--no-index', '--', relative],
                             capture_output=True, text=True)
    if ignored.returncode != 0:
        raise ValueError('研究任务路径必须位于Git忽略区：' + label + ' = ' + str(path))
    tracked = subprocess.run(['git', '-C', str(owner), 'ls-files', '-z', '--', relative],
                             capture_output=True, check=True).stdout
    if tracked:
        raise ValueError('研究任务路径仍有Git跟踪文件；须只取消索引跟踪并保留本地文件：' + str(path))
    # Reject partial allowlists that ignore a directory marker but permit code,
    # manuscript or data below it. These paths need not exist for check-ignore.
    if label in ('run_directory', 'workspace', 'docs', 'paper_reserved', 'notes',
                 'checkout.workspace', 'checkout.docs', 'checkout.paper_reserved') or path.is_dir():
        for suffix in ('.py', '.json', '.tex', '.md', '.csv', '.pdf'):
            name = '__ars_scope_probe__' + suffix
            probe = str((path / name).relative_to(owner))
            check = subprocess.run(['git', '-C', str(owner), 'check-ignore', '--no-index', '--', probe],
                                   capture_output=True)
            if check.returncode != 0:
                raise ValueError('任务目录没有完整覆盖后续研究文件的Git忽略规则：' + str(path))
    owners.add(owner)
    return {'label': label, 'path': str(path), 'git': True, 'ignored': True, 'tracked': False}


def validate_registration(repo, info, directory, checkout=None):
    """Read-only gate before creating a task, starting it or reserving a call.

    Temporary/non-Git software fixtures cannot upload anything and retain their
    test behavior. Real Git repositories must pass both ignore and index checks.
    Symlinks are resolved so an ignored alias cannot target public source files.
    """
    repo = Path(repo).resolve()
    owners = set()
    checks = [_assert_private(directory, 'run_directory', owners)]
    if info.get('id') != 'ARS-DEMO':
        required = ('workspace', 'docs')
        for key in required:
            if not isinstance(info.get(key), str) or not info[key]:
                raise ValueError('任务缺少本地研究路径登记：' + key)
        names = required + ('paper_reserved', 'input', 'notes')
        for key in names:
            if info.get(key):
                checks.append(_assert_private(repo / info[key], key, owners))
        for key in ('entry', 'latest', 'editor'):
            if info.get(key):
                checks.append(_assert_private(repo / info['workspace'] / info[key], key, owners))
        for value in info.get('sources', []):
            checks.append(_assert_private(repo / info['workspace'] / value, 'source', owners))
        if checkout:
            tree = Path(checkout).resolve()
            for key in ('workspace', 'docs', 'paper_reserved'):
                if info.get(key):
                    checks.append(_assert_private(tree / info[key], 'checkout.' + key, owners))
    checker = Path(__file__).resolve().parents[2] / 'scripts/check_git_scope.py'
    for owner in sorted(owners):
        result = subprocess.run([sys.executable, str(checker), '--repo', str(owner)],
                                capture_output=True, text=True)
        if result.returncode:
            raise ValueError('Git上传边界检查未通过：' + str(owner) + '\n' + (result.stderr or result.stdout))
    return {'version': VERSION, 'task_content_upload': False, 'paths': checks,
            'git_repositories_checked': [str(p) for p in sorted(owners)]}


def validate_state(state, directory):
    repo = Path(state['repo'])
    catalog = repo / 'workspaces/topics.json'
    info = next((row for row in json.loads(catalog.read_text()).get('topics', [])
                 if row.get('id') == state['topic']), {}) if catalog.exists() else {}
    info = {**info, 'id': state['topic'], **{key: state['config'][key]
            for key in ('workspace', 'docs', 'input') if key in state['config']}}
    return validate_registration(repo, info, directory, state['config'].get('implementation_checkout'))
