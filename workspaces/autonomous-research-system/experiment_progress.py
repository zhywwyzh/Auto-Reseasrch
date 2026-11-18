"""Task-scoped progress readers. Raw counters do not certify scientific success."""
import datetime as dt
import json
import math
import os
from pathlib import Path
import time
MAX_BYTES = 8 * 1024 ** 2
MAX_FILES = 256
MAX_LEDGER_BYTES = 64 * 1024**2
METRICS = {'environment_steps': '实际环境交互', 'accepted_samples': '接纳样本', 'discarded_samples': '丢弃样本', 'evaluation_steps': '评价交互', 'optimizer_calls': '优化器更新'}

def stamp(value):
    return dt.datetime.fromtimestamp(value, dt.timezone.utc).isoformat()

def load(path, root, maximum_bytes=MAX_BYTES):
    path = Path(path)
    resolved = path.resolve()
    if path.is_symlink() or not resolved.is_relative_to(root.resolve()):
        raise ValueError('进度证据越出本次运行目录')
    current = path
    while current != root:
        if current.is_symlink():
            raise ValueError('进度证据包含符号链接')
        current = current.parent
    if path.stat().st_size > maximum_bytes:
        raise ValueError('进度证据超出读取上限')
    raw = path.read_bytes()
    if len(raw) > maximum_bytes:
        raise ValueError('进度证据超出读取上限')

    def invalid(_):
        raise ValueError('进度证据含非有限数值')
    value = json.loads(raw, parse_constant=invalid)
    if not isinstance(value, dict):
        raise ValueError('进度证据必须为对象')
    return value

def count(value):
    return value if type(value) is int and value >= 0 else None

def observe(directory, state, now=None):
    root = Path(directory).resolve()
    workspace = (Path(state['repo']) / state['config']['workspace']).resolve()
    if not root.is_relative_to(workspace / 'runs/ars'):
        return None
    path = root / 'telemetry/progress.json'
    if not path.is_file():
        return None
    data = load(path, root)
    if data.get('topic') != state['topic'] or data.get('run_id') != state['id']:
        raise ValueError('进度归属与当前任务不匹配')
    modified = path.stat().st_mtime
    sampled = time.time() if now is None else now
    counters = data.get('counters', {})
    if not counters or any(count(v) is None for k,v in counters.items() if k in METRICS):
        raise ValueError('进度计数无效')
    stale = sampled - modified > 30
    return {'topic': state['topic'], 'sampled_at': stamp(sampled), 'source_at': stamp(modified),
            'mode': 'stale' if stale else 'live', 'scope': data.get('scope', 'unknown'),
            'source': 'telemetry/progress.json', 'summary': '最近真实计数；科学验收另行核对。',
            'metrics': [{'key': k, 'label': label, 'value': counters[k]} for k,label in METRICS.items() if k in counters],
            'counts': None, 'validation_status': 'unknown', 'warnings': [], 'eta_seconds': None}

def publish(directory, state, counters, scope, planned_accepted_samples=None):
    if scope not in ('engineering_only', 'research_training'):
        raise ValueError('需要明确计数范围')
    root = Path(directory).resolve()
    workspace = (Path(state['repo']) / state['config']['workspace']).resolve()
    if not root.is_relative_to(workspace / 'runs/ars'):
        raise ValueError('进度路径越出本课题')
    values = {key: count(value) for key,value in counters.items() if key in METRICS}
    if not values or any((value is None for value in values.values())):
        raise ValueError('计数须为实际非负整数')
    path = root / 'telemetry/progress.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {'topic': state['topic'], 'run_id': state['id'], 'schema_version': 1, 'counters': values, 'scope': scope, 'updated_at': stamp(time.time()), 'simulated': False}
    if planned_accepted_samples is not None:
        data['planned_accepted_samples'] = planned_accepted_samples
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False) + '\n')
    temp.replace(path)
    return str(path)
import local_extensions as _local_extensions
_local_extensions.apply(globals())
