"""First-class agent code repair: failed task -> repair agent -> tests -> resume.

The agent edits a private source snapshot. The controller, not the agent, checks
the diff, runs frozen tests, applies the patch and releases the original task.
No new scientific acceptance, experiment budget or research job is granted.
"""
import execution_limits
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

PHASE = 'code_repair'
VERSION = 'agent-code-repair-v1'
POLICY = {'enabled': True, 'version': VERSION, 'validation_timeout_seconds': 120}
SOURCE_SUFFIXES = {'.py', '.sh', '.js', '.ts', '.tsx', '.jsx', '.json', '.toml', '.yaml', '.yml', '.md', '.html', '.css'}
SKIP = {'runs', 'datasets', '.venv', '.git', 'node_modules', '__pycache__', 'artifacts', 'build'}
CODE_SUFFIXES = {'.py', '.sh', '.js', '.ts', '.tsx', '.jsx'}


def enabled(state):
    policy = state['config'].get('code_repair', {})
    return policy.get('enabled') is True and policy.get('version') == VERSION


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sessions(store):
    return [json.loads(row[0]) for row in store.db.execute(
        "SELECT payload FROM events WHERE type='code_repair.queued' ORDER BY seq")]


def session(store, task_id):
    saved = next((r for r in reversed(sessions(store)) if r['task_id'] == task_id), None)
    if saved:
        amendments = []
        for row in store.db.execute("SELECT seq,payload FROM events WHERE type='code_repair.snapshot_amended' ORDER BY seq"):
            amendment = json.loads(row[1])
            if amendment.get('task_id') == task_id:
                saved['files'].update(amendment['added_files'])
                amendments.append({'event_seq': row[0], 'added_files': list(amendment['added_files'])})
        if amendments:
            saved['snapshot_amendments'] = amendments
    return saved


def roots(state):
    repo = Path(state['repo']).resolve()
    # A readonly research task may still have its own code repaired. Source
    # edits happen only via this separately authorized and tested transaction;
    # its researcher remains readonly and raw inputs/results are excluded.
    result = [repo / state['config']['workspace'], repo / 'workspaces/autonomous-research-system']
    return [p for p in result if p.is_dir()]


def snapshot(store, directory, controller_only=False):
    repo = Path(store.state()['repo']).resolve()
    candidate = directory / 'candidate'; candidate.mkdir(parents=True)
    files = {}; total = 0
    selected_roots = roots(store.state())
    if controller_only:
        selected_roots = [p for p in selected_roots if p == repo / 'workspaces/autonomous-research-system']
    for root in selected_roots:
        for path in sorted(root.rglob('*')):
            relative = path.relative_to(repo)
            if any(part in SKIP for part in path.relative_to(root).parts):
                continue
            if (not path.is_file() or path.is_symlink() or path.suffix not in SOURCE_SUFFIXES
                    or not path.resolve().is_relative_to(root.resolve())):
                continue
            # Copy code and its test/packaging support, not research designs,
            # datasets or accumulated prose disguised as source dependencies.
            local=path.relative_to(root)
            if path.suffix not in CODE_SUFFIXES and len(local.parts)>1 and 'tests' not in local.parts:
                continue
            size = path.stat().st_size
            if size > 5_000_000 or total + size > 50_000_000:
                raise ValueError('修复源快照超过大小限制，须定位更小的代码范围')
            target = candidate / relative; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target); total += size
            files[str(relative)] = {'sha256': digest(path), 'mode': path.stat().st_mode & 0o777,
                                    'protected': 'tests' in relative.parts or path.name.startswith('test_')
                                    or path.name in ('AGENTS.md', 'runtime_policy.py', 'research_assurance.py',
                                         'research_quality.py', 'paper_workflow.py', 'ucs_paper_profile.py',
                                         'bearing_paper_profile.py', 'manuscript_quality.py')}
    for path in (repo/'AGENTS.md', repo/'workspaces/topics.json', repo/'.gitignore',
                 repo/'scripts/check_git_scope.py'):
        if path.is_file():
            relative=path.relative_to(repo);target=candidate/relative;target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(path,target)
            files[str(relative)]={'sha256':digest(path),'mode':path.stat().st_mode & 0o777,'protected':True}
    # Tests are selected before the repair agent starts, not from its claims.
    commands = []
    for root in selected_roots:
        test_dir = candidate / root.relative_to(repo) / 'tests'
        if test_dir.is_dir() and list(test_dir.glob('test*.py')):
            commands.append([sys.executable, '-m', 'unittest', 'discover', '-s', str(test_dir), '-p', 'test*.py'])
    return {'candidate': str(candidate), 'files': files, 'validation_commands': commands,
            'original_repo': str(repo), 'source_bytes': total}


def queue(store, failed, error, category, controller_incident=None):
    """Called in the scheduler transaction, once per terminal failed operation."""
    import ars
    directory = store.directory / 'artifacts/code-repairs' / ars.uid()
    directory.mkdir(parents=True)
    saved = snapshot(store, directory, controller_only=bool(controller_incident))
    instruction = ('你是本研究任务自动触发的代码修复执行器，不是重新执行失败任务。'
        '先读取code_repair上下文的原始异常、回执、源快照和冻结验收命令。'
        '在candidate中复现错误、定位根因、实际修改代码；保留原科学目标、数据、阈值与验收器。'
        '不得编辑已有测试、受保护验证器、历史记录或candidate外的源码，不提交训练/求解/仿真。'
        '运行相关原测试并检查实际代码diff；只是重试、重新叙述错误、没有代码改动，不能报告修复完成。'
        '确认修复后done+accept，report写根因、变更路径、复现和复验。控制器将独立执行冻结测试，'
        '验证代码diff与原文件版本后应用补丁，再继续原任务；你不得自己修改原任务状态。'
        '若修复失败，继续根据新的原始报错修改代码；不要要求用户来执行常规修复。\n原始错误：' + error)
    if controller_incident:
        instruction += ('\n这是外层监督器捕获的恢复控制器异常，修复范围仅限共享系统代码。'
                        '不得改研究门槛、实验实现或原任务状态；检查固定运行副本与当前恢复内核的模块/API兼容。'
                        '固定执行端索引不得修改。故障编号：' + str(controller_incident) +
                        '\n固定执行端：' + json.dumps(store.state()['config'].get('system_runtime_pin', {}), ensure_ascii=False))
    task_id = store.add_task('自动调用 agent 修复代码：' + failed['title'], instruction, PHASE, failed['id'], dedup=not bool(controller_incident))
    if not task_id:
        raise ValueError('代码修复任务身份冲突')
    row = dict(version=VERSION, task_id=task_id, failed_task=failed['id'],
               failed_operation=failed.get('operation_id'), directory=str(directory),
               error=error, category=category, **saved)
    row['controller_incident']=controller_incident
    ars.atomic_json(directory/'session.json',row)
    ars.atomic_json(directory/'session.original.json',row)
    store.event('code_repair.queued',row)
    store.status('READY','已自动调用代码修复步骤；通过实际代码变更与测试后继续原任务')
    return True


def maybe_queue(store):
    state=store.state()
    if not enabled(state) or state['status'] not in ('READY','RUNNING','WAITING_EXTERNAL'):
        return False
    tasks=store.tasks()
    if any(t['status'] in ('PENDING','RUNNING','UNKNOWN') for t in tasks):
        return False
    import runtime_policy
    import ars
    previous=sessions(store)
    # The repair itself failed: return its real compiler/test error to the
    # repair agent and keep the candidate. Never blindly rerun the research job.
    for task in reversed(tasks):
        if task['phase'] != PHASE or task['status'] not in ('FAILED','BLOCKED'):
            continue
        error=ars.task_error(task) or '修复未通过代码与测试验收'
        if runtime_policy.classify(error) in ('provider_quota','uncertain_execution'):
            return False
        store.event('code_repair.revise',dict(task_id=task['id'],error=error,
                    previous_operation=task.get('operation_id'),research_job_resubmitted=False))
        store.db.execute("UPDATE tasks SET status='PENDING' WHERE id=?",(task['id'],))
        store.status('READY','修复 agent 接收新的验收报错，继续修改候选代码；未重试原研究任务')
        return True
    superseded=__import__('paper_workflow').superseded_problems(tasks)
    for failed in reversed(tasks):
        if failed['id'] in superseded or failed['phase']==PHASE or failed['status'] not in ('FAILED','BLOCKED'):
            continue
        if any(r['failed_task']==failed['id'] and r.get('failed_operation')==failed.get('operation_id') for r in previous):
            continue
        error=ars.task_error(failed);category=runtime_policy.classify(error)
        if category not in ('implementation','environment'):
            continue
        # An unclassified blocked scientific question is not a code failure.
        return queue(store,failed,error,category)
    incident=store.db.execute("SELECT seq,payload FROM events WHERE type='system.repair_required' ORDER BY seq DESC LIMIT 1").fetchone()
    if incident and not any(r.get('controller_incident')==incident['seq'] for r in previous):
        failure={'id':None,'title':'系统控制器','operation_id':None}
        return queue(store,failure,'控制器代码故障：'+incident['payload'],'implementation',incident['seq'])
    return False


def context(store, task):
    saved=session(store,task['id'])
    if not saved:raise ValueError('修复任务缺少控制器登记')
    # The agent reads both its request and the materialized manifest. Publish
    # the event-derived view so those two authorities cannot disagree after a
    # controller-owned test-support amendment. Keep the original immutable.
    import ars
    manifest = Path(saved['directory'])/'session.json'
    original = manifest.with_name('session.original.json')
    if not original.exists() and manifest.exists():
        ars.atomic_json(original, json.loads(manifest.read_text()))
    ars.atomic_json(manifest, saved)
    operation=store.operation(saved['failed_operation']) if saved.get('failed_operation') else None
    logs=[]
    for op in [operation,store.operation(task['operation_id']) if task.get('operation_id') else None]:
        if not op:continue
        for name in ('receipt.json','stderr.log'):
            path=Path(op['directory'])/name
            if path.is_file():
                import executor_errors
                logs.append({'path':str(path),'sha256':digest(path),
                    'text':executor_errors.redact(path.read_text(errors='replace')[-12000:])})
    error=__import__('ars').task_error(task)
    return dict(**saved, latest_validation_error=error, raw_logs=logs,
        instruction='实际编辑candidate源代码并验证；不可修改原文件、已有测试、科学门槛或重投原作业。',
        write_scope=[saved['candidate']], execution_directory=saved['candidate'])


def verify(store, task, result):
    """Controller-owned diff and real tests. A model's success claim is insufficient."""
    import ars
    if result.get('status')!='done' or result.get('verdict')!='accept':
        raise ValueError('修复 agent 尚未完成可验收代码补丁：'+result.get('summary',''))
    saved=session(store,task['id']);candidate=Path(saved['candidate']);repo=Path(saved['original_repo'])
    completed=Path(saved['directory'])/'verified-patch.json'
    if completed.exists():
        verified=json.loads(completed.read_text())
        if all(digest(repo/c['path'])==c['after'] and digest(candidate/c['path'])==c['after'] for c in verified['changes']):
            return {'gate':'code_repair_verified','code_repair':verified,'sources':[],'scientific_truth_verified':False}
        raise ValueError('已应用补丁发生后续变更，禁止重复覆盖')
    original=next((t for t in store.tasks() if t['id']==saved['failed_task']),None)
    if not saved.get('controller_incident') and (not original or original['status'] not in ('FAILED','BLOCKED') or original.get('operation_id')!=saved.get('failed_operation')):
        raise ValueError('原任务身份或执行状态已变化，拒绝应用补丁')
    changes=[]
    for name,old in saved['files'].items():
        path=candidate/name
        if not path.is_file() or path.is_symlink():raise ValueError('修复不得删除原文件或使用符号链接：'+name)
        after=digest(path)
        if after==old['sha256']:continue
        if old['protected'] or path.suffix not in CODE_SUFFIXES:
            raise ValueError('修复修改了受保护测试、验证器或非代码文件：'+name)
        if digest(repo/name)!=old['sha256']:raise ValueError('原代码已被其他执行者修改，禁止覆盖：'+name)
        changes.append({'path':name,'before':old['sha256'],'after':after})
    for path in candidate.rglob('*'):
        if path.is_symlink():raise ValueError('修复候选不得包含符号链接')
        if path.is_file() and '__pycache__' not in path.parts and str(path.relative_to(candidate)) not in saved['files']:
            raise ValueError('未登记的新文件不能自动应用：'+str(path.relative_to(candidate)))
    if not changes:raise ValueError('没有实际代码变更；重新执行或报告不算代码修复')
    commands=[[sys.executable,'-m','py_compile',*[str(candidate/c['path']) for c in changes if c['path'].endswith('.py')]]]
    if len(commands[0])==3:commands=[]
    commands+=saved['validation_commands']
    if not commands:raise ValueError('没有控制器冻结的可执行验收命令')
    results=[];directory=Path(saved['directory'])
    for index,argv in enumerate(commands):
        started=time.monotonic()
        try:
            run=subprocess.run(argv,cwd=candidate,env={**os.environ,'PYTHONNOUSERSITE':'1','PYTHONDONTWRITEBYTECODE':'1'},
                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=state_timeout(store))
        except subprocess.TimeoutExpired as exc:
            output=directory/f'validation-{task["attempt"]}-{index}.log';output.write_bytes(exc.stdout or b'')
            ars.atomic_json(directory/f'validation-{task["attempt"]}-{index}.json',dict(argv=argv,
                status='timed_out',seconds=time.monotonic()-started,log=str(output),log_sha256=digest(output)))
            raise ValueError('控制器实际复验超时；修复agent须读取'+str(output)+'并修复挂起原因') from exc
        output=directory/f'validation-{task["attempt"]}-{index}.log';output.write_bytes(run.stdout)
        record=dict(argv=argv,exit_code=run.returncode,seconds=time.monotonic()-started,
                    log=str(output),log_sha256=digest(output),simulated=False)
        results.append(record);ars.atomic_json(directory/f'validation-{task["attempt"]}-{index}.json',record)
        if run.returncode:
            raise ValueError('控制器实际复验失败：'+run.stdout.decode(errors='replace')[-1800:])
    # Check every original again after tests and before any source write.
    if store.state()['status'] in ('STOPPED_USER','STOPPED_BUDGET','COMPLETED'):
        raise ValueError('任务已经停止，候选补丁保留且不应用')
    for change in changes:
        if digest(repo/change['path'])!=change['before']:raise ValueError('复验期间原代码发生变化，禁止覆盖')
    for change in changes:
        target=repo/change['path'];temporary=target.with_name(target.name+'.repair-'+ars.uid())
        temporary.write_bytes((candidate/change['path']).read_bytes())
        temporary.chmod(saved['files'][change['path']]['mode']);os.replace(temporary,target)
    verified=dict(gate='controller_diff_and_frozen_tests',changes=changes,tests=results,
                  original_stage_accepted=False,original_job_retried=False)
    ars.atomic_json(directory/'verified-patch.json',verified)
    return {'gate':'code_repair_verified','code_repair':verified,'sources':[],'scientific_truth_verified':False}


def state_timeout(store):
    if execution_limits.unrestricted(store.state()):
        return None
    return max(1,min(600,int(store.state()['config']['code_repair'].get('validation_timeout_seconds',120))))


def accepted(store, task, verification):
    saved=session(store,task['id'])
    if saved.get('controller_incident'):
        store.event('code_repair.verified',dict(task_id=task['id'],controller_incident=saved['controller_incident'],verification=verification))
        store.status('READY','控制器代码补丁已通过复验，继续原研究调度；没有重置原实验')
        return
    original=next(t for t in store.tasks() if t['id']==saved['failed_task'])
    if original['status'] not in ('FAILED','BLOCKED') or original.get('operation_id')!=saved.get('failed_operation'):
        raise ValueError('原任务身份或执行状态已变化，不允许补丁解除其他任务')
    store.event('code_repair.verified',dict(task_id=task['id'],failed_task=original['id'],
        verification=verification,original_result=original.get('result'),original_error=__import__('ars').task_error(original)))
    store.db.execute("UPDATE tasks SET status='PENDING' WHERE id=?",(original['id'],))
    store.status('READY','agent代码补丁已通过控制器实际复验，自动继续原任务；原科学验收仍须通过')
