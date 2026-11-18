"""Opt-in local artifact revision contracts, independent of topic identifiers.

The controller pins a task-owned validator; artifact checks do not certify science.
Legacy read-only and experimental profiles retain their existing contracts.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import git_boundary

VERSION = 'artifact-revision-v1'
PHASES = {'resolve', 'investigate', 'analyze', 'write', 'paper_review'}


def enabled(config):
    return config.get('workflow') == 'paper' and config.get('research_contract') == VERSION


def prepare(repo, info, raw):
    repo = Path(repo).resolve()
    workspace = (repo / info['workspace']).resolve()
    path = (repo / raw).resolve()
    if not path.is_relative_to(workspace) or not path.is_file():
        raise ValueError('修订契约必须在本课题本地工作区')
    owners = set()
    git_boundary._assert_private(path, 'revision_spec', owners)
    spec = json.loads(path.read_text())
    if spec.get('version') != VERSION or spec.get('topic') != info['id']:
        raise ValueError('修订契约版本或课题不匹配')
    stages = spec.get('stages', [])
    names = [s.get('phase') for s in stages]
    if (not stages or len(stages) != len(set(names)) or set(names) - PHASES
            or names[0] != 'resolve' or names[-1] != 'paper_review'):
        raise ValueError('修订阶段须从resolve到paper_review且不重复')
    for s in stages:
        if not s.get('title') or not s.get('instruction') or not s.get('roles'):
            raise ValueError('修订阶段缺少指令或产物角色')
    paper = (repo / spec['paper_root']).resolve()
    reserved = (repo / info['paper_reserved']).resolve()
    if not paper.is_relative_to(reserved):
        raise ValueError('修订稿必须在本课题稿件目录')
    validator = (repo / spec['validator']).resolve()
    if not validator.is_relative_to(workspace) or not validator.is_file():
        raise ValueError('修订验收器必须来自当前课题')
    git_boundary._assert_private(paper, 'paper_reserved', owners)
    git_boundary._assert_private(validator, 'revision_validator', owners)
    return {'spec': spec, 'source': str(path),
            'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'validator_sha256': hashlib.sha256(validator.read_bytes()).hexdigest()}


def stages(config):
    return {s['phase']: (s['title'], s['instruction']) for s in config['revision_workflow']['spec']['stages']}


def context(state, directory, phase):
    repo = Path(state['repo'])
    spec = state['config']['revision_workflow']['spec']
    stage = next(s for s in spec['stages'] if s['phase'] == phase)
    return {'workflow': VERSION, 'stage': phase, 'stage_order': list(stages(state['config'])),
            'manifest_path': str(Path(directory)/'artifacts/stages'/(phase+'.json')),
            'required_artifact_roles': stage['roles'], 'artifact_contracts': spec.get('artifact_contracts', {}),
            'write_scope': [str(repo/state['config']['workspace']), str(repo/state['config']['docs']), str(repo/spec['paper_root'])],
            'contract': spec['constraints']+' '+git_boundary.INSTRUCTION,
            'revision_spec': spec, 'validator_sha256': state['config']['revision_workflow']['validator_sha256']}


def verify(state, directory, phase):
    if state['config']['backend'] != 'codex':
        raise ValueError('修订产物不能由模拟执行器准入')
    from paper_workflow import _artifact_path, manifest_path
    config = state['config']; binding = config['revision_workflow']; spec = binding['spec']
    validator = _artifact_path(spec['validator'], state)
    if hashlib.sha256(validator.read_bytes()).hexdigest() != binding['validator_sha256']:
        raise ValueError('修订验收器已改变，不能自行降低冻结验收')
    manifest = json.loads(manifest_path(directory, phase).read_text())
    if manifest.get('topic') != state['topic'] or manifest.get('stage') != phase or manifest.get('status') != 'passed':
        raise ValueError('修订manifest身份/阶段/状态不匹配')
    rows = manifest.get('artifacts')
    if not isinstance(rows, list) or not 0 < len(rows) <= 1024:
        raise ValueError('修订manifest需要真实产物清单')
    checked = []
    for row in rows:
        p = _artifact_path(row['path'], state)
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        if not p.stat().st_size or digest != row.get('sha256'):
            raise ValueError('修订产物为空或哈希不匹配：'+str(p))
        checked.append({**row, 'path': str(p)})
    required = set(next(s for s in spec['stages'] if s['phase'] == phase)['roles'])
    if not required.issubset({r['role'] for r in rows}):
        raise ValueError('修订产物角色不足：'+str(sorted(required)))
    completed = subprocess.run([sys.executable, str(validator), '--campaign', str(directory), '--phase', phase],
                               cwd=state['repo'], capture_output=True, text=True, timeout=60)
    receipt = {'argv': completed.args, 'exit_code': completed.returncode,
               'stdout': completed.stdout, 'stderr': completed.stderr, 'validator_sha256': binding['validator_sha256']}
    target = Path(directory)/'artifacts/validation'; target.mkdir(parents=True, exist_ok=True)
    (target/(phase+'.json')).write_text(json.dumps(receipt, ensure_ascii=False, indent=2)+'\n')
    if completed.returncode:
        raise ValueError('冻结修订验收器未通过：'+(completed.stderr or completed.stdout)[-3000:])
    report = json.loads(completed.stdout)
    if report.get('passed') is not True:
        raise ValueError('冻结修订验收器未返回passed=true')
    return {'artifacts': checked, 'validator': receipt, 'scope': 'artifact-and-task-contract-check; not independent scientific endorsement'}
