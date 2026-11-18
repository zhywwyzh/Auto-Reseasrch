"""Read experiment ledgers by evidence identity, independently of stage admission.

Task-specific labels and extra ledger references belong in the local campaign
configuration. New result ledgers are also discovered from controller-verified
completed tasks, so the reader does not stay pinned to an older experiment.
"""
import copy
import hashlib
import json
from pathlib import Path
import time

import experiment_progress

_CACHE = {}
TERMINAL = {'completed', 'succeeded', 'timeout', 'invalid', 'crashed',
            'invalid_or_crashed', 'failed'}


def apply_active_status(state):
    """Present a live dispatched task even during a controller READY checkpoint.

    Preserve the recorded state; this only updates the reader's response and
    cannot start, recover, stop or accept any task.
    """
    progress = state.get('progress', {})
    if (state.get('config', {}).get('experiment_observations', {}).get('enabled') is True
            and state.get('status') == 'READY'
            and (progress.get('current_task') or {}).get('status') == 'RUNNING'
            and (progress.get('activity') or {}).get('process_alive') is True):
        state['recorded_status'] = state['status']
        state['status'] = 'RUNNING'


def summarize(data):
    attempts, rows = data.get('attempt_manifest'), data.get('runs')
    if data.get('synthetic_fixture') is True or data.get('split') in ('DEV', 'SCREEN', 'SYNTHETIC'):
        raise ValueError('工程或先导数据不作为正式实验轮次')
    if data.get('executed') is not True or not data.get('benchmark_id'):
        raise ValueError('没有实际执行的实验身份')
    if not isinstance(attempts, list) or not attempts or not isinstance(rows, list):
        raise ValueError('缺少逐项计划和账本')
    fields = ['world_id', 'episode_id', 'case_id', 'method', 'policy', 'input_sha256']
    fields = [key for key in fields if all(key in row for row in attempts)]
    if 'world_id' not in fields or not any(key in fields for key in ('method', 'policy', 'episode_id')):
        raise ValueError('逐项身份不足')
    def identity(row):
        return tuple(json.dumps(row[key], sort_keys=True) for key in fields)
    expected, observed = [identity(r) for r in attempts], [identity(r) for r in rows]
    if (len(set(expected)) != len(expected) or len(set(observed)) != len(observed)
            or not set(observed).issubset(set(expected))):
        raise ValueError('逐项身份重复或越出计划')
    counts = dict(total=len(attempts), terminal=0, returned=0, failed=0,
                  unknown=0, pending=len(attempts)-len(rows), running=0)
    for row in rows:
        status = row.get('status')
        if row.get('started') == 'unknown_at_stop' or row.get('individual_cost_unknown') is True:
            counts['unknown'] += 1
        elif row.get('attempted') is False or status in ('not_started', 'budget_stopped', 'pending'):
            counts['pending'] += 1
        elif status in TERMINAL:
            counts['terminal'] += 1
            counts['returned' if status in ('completed', 'succeeded') else 'failed'] += 1
        elif status == 'running':
            counts['running'] += 1
        else:
            counts['unknown'] += 1
    assert sum(counts[k] for k in ('terminal', 'unknown', 'pending', 'running')) == counts['total']
    result = {'benchmark_id': data['benchmark_id'], 'counts': counts,
              'percent': round(100 * counts['terminal'] / counts['total'], 1),
              'execution_complete': counts['terminal'] == counts['total'],
              'worlds': len({r['world_id'] for r in attempts}),
              'logs': len({r['case_id'] for r in attempts}) if 'case_id' in fields else None,
              'methods': len({r.get('method', r.get('policy')) for r in attempts}),
              'split': data.get('split'), 'scientific_admission_inferred': False}
    if rows and all(type(row.get('true_success')) is bool for row in rows):
        result['goal_achieved'] = sum(row['true_success'] for row in rows)
        result['goal_not_achieved'] = len(rows) - result['goal_achieved']
    return result


def read_ledger(directory, reference, topic):
    root = Path(directory).resolve()
    path = Path(reference['path'])
    path = path if path.is_absolute() else root / path
    resolved = path.resolve()
    if not resolved.is_relative_to(root / 'artifacts') or path.is_symlink():
        raise ValueError('实验账本越出本次产物目录')
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError('实验账本包含符号链接')
        current = current.parent
    info = path.stat()
    cache_key = (str(resolved), reference['sha256'], info.st_ino, info.st_size, info.st_mtime_ns)
    if cache_key in _CACHE:
        return copy.deepcopy(_CACHE[cache_key])
    if info.st_size > experiment_progress.MAX_LEDGER_BYTES:
        raise ValueError('账本超出读取上限')
    raw = path.read_bytes()
    if len(raw) > experiment_progress.MAX_LEDGER_BYTES or hashlib.sha256(raw).hexdigest() != reference['sha256']:
        raise ValueError('实验账本哈希不匹配')
    data = json.loads(raw)
    if data.get('topic') != topic:
        raise ValueError('实验账本课题不匹配')
    result = summarize(data)
    result.update(source=str(resolved.relative_to(root)), sha256=reference['sha256'],
                  source_at=experiment_progress.stamp(info.st_mtime))
    if len(_CACHE) >= 32:
        _CACHE.clear()
    _CACHE[cache_key] = result
    return copy.deepcopy(result)


def read_plan(directory, reference, topic):
    root = Path(directory).resolve()
    path = root / reference['path']
    data = experiment_progress.load(path, root)
    if (not path.resolve().is_relative_to(root / 'artifacts')
            or hashlib.sha256(path.read_bytes()).hexdigest() != reference['sha256']
            or data.get('topic') != topic or not data.get('benchmark_id')):
        raise ValueError('实验计划身份或哈希不匹配')
    total = data[reference['total_field']]
    if type(total) is not int or total <= 0:
        raise ValueError('计划没有明确分母')
    return {'benchmark_id': data['benchmark_id'], 'label': reference['label'],
            'rank': reference.get('rank', 0), 'planned_only': True,
            'counts': {'total': total}, 'percent': None, 'execution_complete': False,
            'worlds': data.get(reference.get('worlds_field', 'physical_worlds')),
            'logs': None, 'methods': len(data.get(reference.get('methods_field', 'policies'), [])),
            'note': '设计已登记；当前尚无已核验执行账本。计划数量不代表已经运行。',
            'source': str(path.relative_to(root)), 'sha256': reference['sha256'],
            'source_at': experiment_progress.stamp(path.stat().st_mtime),
            'scientific_admission_inferred': False}


def read_snapshot(directory, reference, topic):
    """Consume a receipt-bound observation; browser refresh never starts SSH."""
    root = Path(directory).resolve()
    def bound(entry):
        path = Path(entry['path'])
        path = path if path.is_absolute() else root / path
        data = experiment_progress.load(path, root)
        if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('快照来源哈希不匹配')
        return data, path
    configuration, _ = bound(reference['configuration'])
    plan = read_plan(root, reference['plan'], topic)
    folder = root / reference['directory']
    if not folder.resolve().is_relative_to(root / 'artifacts') or folder.is_symlink():
        raise ValueError('快照目录越出本轮产物')
    candidates = sorted(folder.glob('*.json'), key=lambda path: path.stat().st_mtime_ns, reverse=True)
    if not candidates:
        raise ValueError('尚无服务器快照')
    path = candidates[0]
    document = experiment_progress.load(path, root)
    receipt, _ = bound(document['receipt'])
    if (receipt.get('status') != 'succeeded' or receipt.get('exit_code') != 0
            or receipt.get('target') != reference['target']):
        raise ValueError('服务器观察回执未成功')
    log, _ = bound({'path': receipt['log_path'], 'sha256': receipt['log_sha256']})
    snapshot = document['snapshot']
    guard = snapshot['guard']
    if (snapshot != log or snapshot['phase'] != configuration['phase']
            or guard['phase'] != configuration['phase'] or guard['topic'] != topic
            or configuration['topic'] != topic or guard['source'] != configuration['source_directory']
            or guard['image'] != configuration['image_id']
            or configuration['benchmark_id'] != plan['benchmark_id']
            or guard['expected_episodes'] != plan['counts']['total']
            or configuration['expected_episodes'] != plan['counts']['total']):
        raise ValueError('快照未绑定登记的执行身份')
    lanes = snapshot['lanes']
    if len(lanes) != configuration['workers']:
        raise ValueError('快照缺少执行通道')
    terminal, started, expected = 0, 0, 0
    for lane in lanes.values():
        n, starts, total = lane['terminals'], lane['starts'], lane['status']['expected']
        if any(type(value) is not int for value in (n, starts, total)) or not 0 <= n <= starts <= total:
            raise ValueError('快照计数无效')
        terminal += n; started += starts; expected += total
    if expected != plan['counts']['total']:
        raise ValueError('通道分母与冻结计划不一致')
    sampled = snapshot['observed_at']
    if not isinstance(sampled, (int, float)) or sampled > time.time() + 5:
        raise ValueError('快照采集时间无效')
    age = max(0, time.time() - sampled)
    return {**plan, 'planned_only': False, 'observed_only': True,
            'counts': {'total': expected, 'terminal': terminal, 'returned': None, 'failed': None,
                       'unknown': None, 'pending': expected-terminal, 'running': 0,
                       'started': started, 'open': started-terminal},
            'percent': round(100 * terminal / expected, 1), 'execution_complete': False,
            'note': '服务器只读快照；成功、失败和证据完整性等待逐项评价。' + ('快照已超过两分钟，当前状态待核对。' if age > 120 else ''),
            'snapshot_stale': age > 120, 'source': str(path.relative_to(root)),
            'source_at': experiment_progress.stamp(sampled),
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'rank': reference.get('rank', plan['rank'])}


def observe(store, state, original):
    if original is None:
        return original
    config = state.get('config', {}).get('experiment_observations', {})
    if config.get('enabled') is not True:
        return original
    labels = config.get('labels', {})
    references = []
    # Only completed, source-checked tasks can introduce a new observed ledger.
    # A same-named newer file or a model's summary cannot replace its bytes.
    for rank, task in enumerate(store.tasks()):
        if task.get('status') != 'COMPLETED' or task.get('phase') != 'experiment':
            continue
        verification = json.loads(task.get('verification') or '{}')
        for ref in verification.get('sources', []):
            path = Path(ref.get('source', ''))
            if ref.get('status') == 'source_match_only' and path.name.endswith('results.json'):
                references.append({'path': str(path), 'sha256': ref['sha256'],
                                   'label': task['title'], 'rank': rank, 'required': False})
    references += [{**entry, 'required': True} for entry in config.get('ledgers', [])]
    series, warnings = {}, []
    for ref in references:
        try:
            row = read_ledger(store.directory, ref, state['topic'])
            key = row['benchmark_id']
            row.update(label=labels.get(key, {}).get('label', ref.get('label', key)),
                       note=labels.get(key, {}).get('note', ''), rank=ref.get('rank', 0))
            if key not in series or row['rank'] > series[key]['rank']:
                series[key] = row
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            if ref.get('required'):
                warnings.append('一轮登记实验的账本未通过核验，已隐藏其计数；未使用旧计数代替。')
    live_warnings = []
    for reference in config.get('snapshots', []):
        try:
            planned = read_plan(store.directory, reference['plan'], state['topic'])
            if planned['benchmark_id'] in series:
                continue  # A verified final ledger supersedes old observations.
            row = read_snapshot(store.directory, reference, state['topic'])
            series[row['benchmark_id']] = row
            if row['snapshot_stale']:
                live_warnings.append('服务器快照已超过两分钟；保留最后计数，当前远端状态待核对。')
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            live_warnings.append('服务器快照尚未通过来源核验，暂不推测执行数。')
    for reference in config.get('plans', []):
        try:
            row = read_plan(store.directory, reference, state['topic'])
            if row['benchmark_id'] not in series:
                series[row['benchmark_id']] = row
            elif series[row['benchmark_id']]['counts']['total'] != row['counts']['total']:
                warnings.append('新账本与登记计划分母不一致，不展示缩减后的完成比例。')
                series[row['benchmark_id']] = row
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            warnings.append('一项登记的后续实验计划未通过核验，不推测其分母或执行数。')
    if not series:
        return {**original, 'warnings': list(original['warnings']) + warnings}
    result = {**original, 'warnings': list(original['warnings']) + warnings,
              'metrics': list(original['metrics'])}
    result['series'] = sorted(series.values(), key=lambda row: row['rank'], reverse=True)
    result['live_warnings'] = live_warnings
    latest = result['series'][0]
    counts = latest['counts']
    if latest.get('planned_only'):
        result['summary'] = '%s：计划 %s 项，执行账本尚未接入。' % (latest['label'], counts['total'])
        completed = next((row for row in result['series'] if not row.get('planned_only')), None)
        if completed:
            result['summary'] += ' 最近一轮：%s，已有终态 %s / %s。' % (
                completed['label'], completed['counts']['terminal'], completed['counts']['total'])
    elif latest.get('observed_only'):
        result['summary'] = '%s：服务器已记录终态 %s / %s（%s%%）；采集时间 %s。' % (
            latest['label'], counts['terminal'], counts['total'], latest['percent'], latest['source_at'])
    else:
        result['summary'] = '%s：已有终态 %s / %s（%s%%）；待形成终态 %s，未知 %s。' % (
            latest['label'], counts['terminal'], counts['total'], latest['percent'],
            counts['pending'] + counts['running'], counts['unknown'])
    status_labels = {'NOT_CREATED': '尚未开始', 'RUNNING': '进行中',
                     'REVISION_REQUIRED': '待修订', 'BLOCKED': '待处理',
                     'PENDING': '待执行', 'READY': '待执行'}
    result['remaining_work'] = [stage['label'] + '：' + status_labels.get(stage['status'], stage['status'])
                                for stage in state.get('progress', {}).get('stages', [])
                                if stage['status'] != 'COMPLETED']
    result['original_summary'] = original.get('original_summary', original['summary'])
    result['overall_percent'] = None
    result['overall_note'] = '各轮执行比例分别计算；不相加冒充独立样本，也不作为完整研究或论文的完成比例。'
    return result
