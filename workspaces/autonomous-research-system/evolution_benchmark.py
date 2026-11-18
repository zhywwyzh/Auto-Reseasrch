"""Fixed recovery/strategy benchmark. This measures engineering, not scientific novelty.

Expected answers stay in the trusted parent process, outside the candidate mount.
Development failures can guide changes. Holdout reports expose aggregate counts only.
"""
import hashlib
import json
from pathlib import Path
import time

import strategy_runtime

VERSION = 'ars-recovery-benchmark-v1'


def cases():
    development = [
        ('route_with_manifest', 'SCREEN输入已核验；服务器无路由，阻塞manifest已落盘', 'transport'),
        ('resource_after_route', 'SSH已可用，rootless Docker的CPU委派被拒绝', 'environment'),
        ('missing_definition', '缺学位同版本环境／评价器依据，resolve未通过', 'external_evidence'),
        ('network_report', '网络不可达；已生成JSON诊断报告', 'transport'),
        ('unknown_job', '缺少回执且无法确认执行状态', 'uncertain_execution'),
        ('missing_dependency', 'ModuleNotFoundError: scipy; manifest recorded', 'environment'),
        ('empty_artifact', '阶段产物为空：worker-stderr.log', 'artifact_contract'),
        ('source_mismatch', '摘录与真实来源不匹配', 'provenance'),
        ('new_authority', '需要用户决策：改变科学目标', 'authorization'),
        ('schema_failure', 'schema validation failed', 'artifact_contract'),
        ('assertion', 'AssertionError: checkpoint roundtrip failed', 'implementation'),
        ('budget', '授权时间仅余63秒，须补足墙钟授权', 'authorization'),
    ]
    holdout = [
        ('route_receipt', 'No route to host; manifest contains 89 verified artifacts', 'transport'),
        ('oom_with_report', 'Docker worker out of memory; JSON report saved', 'environment'),
        ('dependency_log', 'ImportError in validator; source hash checked', 'environment'),
        ('missing_original', '原始定义依据缺失，不能用工程通过替代', 'external_evidence'),
        ('job_unknown', '远端状态不明，已有日志和manifest', 'uncertain_execution'),
        ('auth_boundary', '新增授权才能改变评价目标；SSH正常', 'authorization'),
        ('transport_reset', 'Connection reset by peer; JSON report retained', 'transport'),
        ('uninstalled_solver', 'Julia尚未安装，来源清单已生成', 'environment'),
        ('source_scope', '来源超出当前课题与共用方法范围', 'provenance'),
        ('test_failure', '测试失败，已写入manifest诊断', 'implementation'),
        ('manifest', '阶段manifest需要实际产物清单', 'artifact_contract'),
        ('auth_connection', 'Permission denied (publickey,password); receipt saved', 'transport'),
    ]
    rows = []
    for split, values in [('development', development), ('holdout', holdout)]:
        rows += [{'id': name, 'split': split, 'function': 'classify', 'args': [error], 'expected': answer}
                 for name, error, answer in values]
        order = ['resolve', 'implement', 'validate', 'pilot', 'experiment', 'analyze', 'write', 'review']
        tasks = [{'id': p, 'phase': p, 'status': 'COMPLETED'} for p in order[:5]]
        if split == 'development':
            tasks.append({'id': 'rerun', 'phase': 'pilot', 'status': 'COMPLETED'})
            answer = 'experiment'
        else:
            tasks += [{'id': 'rerun', 'phase': 'validate', 'status': 'COMPLETED'},
                      {'id': 'experiment-new', 'phase': 'experiment', 'status': 'BLOCKED'}]
            answer = 'experiment-new'
        rows.append({'id': split + '_frontier', 'split': split, 'function': 'frontier', 'args': [tasks, order], 'expected': answer})
    return rows


def contract_hash():
    return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()


def evaluate(directory):
    started = time.monotonic()
    data = cases()
    requests = [{'function': r['function'], 'args': r['args']} for r in data]
    requests += [
        {'function': 'task_guidance', 'args': [{'task': {'phase': 'write'}, 'goal': '核验真实研究产物'}]},
        {'function': 'improvement_prompt', 'args': [{'parent': 'parent-version', 'failures': ['diagnosis-374'], 'files': {}}]},
        {'function': 'select_memory', 'args': [[{'text': 'banana'}, {'text': 'checkpoint restore'}, {'text': 'unrelated'}], 'checkpoint', 'restore', 1]},
        {'function': 'incident', 'args': ['SSH: No route to host; manifest 137 artifacts']},
        {'function': 'incident', 'args': ['SSH: No route to host; manifest 155 artifacts']},
        {'function': 'incident', 'args': ['Docker CPU委派被拒绝; cgroup quota']},
    ]
    error = ''
    try:
        values = strategy_runtime.invoke(directory, requests)
    except (ValueError, OSError, RuntimeError, __import__('subprocess').TimeoutExpired) as exc:
        values = [None] * len(requests); error = str(exc)[:2000]
    checks = [{**r, 'actual': values[i], 'passed': values[i] == r['expected']} for i, r in enumerate(data)]
    guidance, prompt, memory, first, repeated, different = values[len(data):]
    capability = {
        'research_guidance': isinstance(guidance, str) and 40 <= len(guidance) <= 12000,
        'self_modification_interface': isinstance(prompt, str) and 'parent-version' in prompt and 'diagnosis-374' in prompt and len(prompt) <= 200000,
        'memory_selection': memory == [1],
        'incident_stable': isinstance(first, str) and first == repeated,
        'incident_separate': isinstance(first, str) and isinstance(different, str) and first != different,
    }
    splits = {}
    for split in ('development', 'holdout'):
        selected = [r for r in checks if r['split'] == split]
        splits[split] = {'passed': sum(r['passed'] for r in selected), 'total': len(selected)}
    return {'benchmark': VERSION, 'benchmark_sha256': contract_hash(), 'source_digest': strategy_runtime.fingerprint(directory),
            'splits': splits, 'capabilities': capability, 'viable': all(capability.values()) and not error,
            'correct': sum(r['passed'] for r in checks), 'total': len(checks),
            'development_failures': [{k: r[k] for k in ('id', 'args', 'expected', 'actual')} for r in checks if r['split'] == 'development' and not r['passed']],
            'case_outcomes': {r['id']: r['passed'] for r in checks},
            'wall_seconds': time.monotonic() - started, 'error': error,
            'scope': 'isolated engineering decision replay; not end-to-end research or broad coding ability'}


def promotion(candidate, incumbent, candidate_bytes, incumbent_bytes):
    if candidate['benchmark_sha256'] != incumbent['benchmark_sha256']:
        return False, 'benchmark changed; paired evaluation required'
    if not candidate['viable']:
        return False, 'candidate lost required capabilities'
    # Paired outcomes, not just aggregate score: one fixed failure cannot buy a new regression.
    if any(passed and not candidate['case_outcomes'].get(key) for key, passed in incumbent['case_outcomes'].items()):
        return False, 'regression on a previously passing case'
    if candidate['splits']['holdout']['passed'] < candidate['splits']['holdout']['total']:
        return False, 'holdout gate not passed'
    if candidate['correct'] > incumbent['correct']:
        return True, 'more correct cases, no regression, holdout passed'
    if candidate['correct'] == incumbent['correct'] and candidate_bytes < incumbent_bytes * 0.95:
        return True, 'same correctness and capabilities with at least 5% less source'
    return False, 'no measured improvement; viable candidate retained for exploration'
