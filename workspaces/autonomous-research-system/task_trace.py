"""Local task instructions, execution identity and durable user supplements.

A saved requirement is not proof that an executor read or satisfied it. Delivery
is evidenced by the immutable request plus the operation.dispatched ledger event.
"""
import hashlib
import json
import datetime as dt
from functools import lru_cache
from pathlib import Path


def fingerprint(item):
    fields = {k: item.get(k, '') for k in ('title', 'instruction', 'scope', 'target')}
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def saved(store):
    items = []
    for row in store.db.execute("SELECT payload,created_at FROM events WHERE type='supplement.saved' ORDER BY seq"):
        item = json.loads(row['payload'])
        items.append(dict(item, created_at=row['created_at'], legacy=False))
    # Old UI wrote a task and a memory, but had no supplement receipt. Preserve
    # that evidence, including duplicate-click memories, without modifying it.
    seen = set()
    tasks = store.tasks()
    for row in store.db.execute("SELECT id,text,created_at FROM memories WHERE text LIKE '用户补充：%' ORDER BY rowid"):
        instruction = row['text'][len('用户补充：'):]
        if instruction in seen:
            continue
        seen.add(instruction)
        task = next((t for t in tasks if t['instruction'] == instruction), None)
        item = {'id': 'legacy-' + (task['id'] if task else row['id']),
                'title': task['title'] if task else '历史补充', 'instruction': instruction,
                'scope': 'campaign', 'target': '', 'legacy': True,
                'created_at': task['created_at'] if task else row['created_at'],
                'legacy_task_id': task['id'] if task else None,
                'queued_phase': task['phase'] if task else None,
                'task_status': task['status'] if task else None}
        item['sha256'] = fingerprint(item)
        items.append(item)
    return sorted(items, key=lambda i: i['created_at'])


def save(store, data):
    import ars
    if any(not isinstance(data.get(k, ''), str) for k in ('title', 'instruction', 'scope', 'target')):
        raise ValueError('补充标题、正文与范围必须是文本')
    item = {k: str(data.get(k, '')).strip() for k in ('title', 'instruction', 'scope', 'target')}
    if not item['title'] or len(item['title']) > 240 or not item['instruction'] or len(item['instruction']) > 10000:
        raise ValueError('补充标题须为1–240字，正文须为1–10000字')
    if item['scope'] not in ('campaign', 'phase', 'task'):
        raise ValueError('请选择补充适用范围')
    if item['scope'] == 'campaign':
        item['target'] = ''
    elif item['scope'] == 'phase' and item['target'] not in ars.PHASES:
        raise ValueError('不存在的研究阶段')
    elif item['scope'] == 'task' and not any(t['id'] == item['target'] for t in store.tasks()):
        raise ValueError('不存在的目标任务')
    item['sha256'] = fingerprint(item)
    with store.tx():
        existing = next((x for x in saved(store) if x['sha256'] == item['sha256']), None)
        if existing:
            return {'supplement': existing, 'duplicate': True}
        item['id'] = ars.uid()
        store.event('supplement.saved', item)
    return {'supplement': next(x for x in saved(store) if x['id'] == item['id']), 'duplicate': False}


def context(store, task):
    if task['phase'] == 'code_repair':
        return []  # Keep isolated engineering repair scope unchanged.
    return [{k: item[k] for k in ('id', 'title', 'instruction', 'scope', 'target', 'sha256')}
            for item in saved(store) if item['scope'] == 'campaign' or
            (item['scope'] == 'phase' and item['target'] == task['phase']) or
            (item['scope'] == 'task' and item['target'] == task['id'])]


@lru_cache(maxsize=256)
def _read(path, mtime, size):
    if size > 8_000_000:
        return {}
    try:
        data = json.loads(Path(path).read_text())
        if not isinstance(data, dict):
            return {}
        if path.endswith('/request.json'):
            ctx = data.get('context', {})
            return {'backend': data.get('config', {}).get('backend'),
                    'model': data.get('config', {}).get('model'),
                    'model_assignment': data.get('model_assignment'),
                    'supplements': ctx.get('user_supplements', []),
                    'memory': [m.get('text') for m in ctx.get('memory', []) if str(m.get('text', '')).startswith('用户补充：')],
                    'task': ctx.get('task', {})}
        return data
    except (OSError, ValueError, TypeError):
        return {}


def read_local(store, path):
    path = Path(path)
    try:
        if path.is_symlink() or not path.resolve().is_relative_to(store.directory.resolve()):
            return {}
        stat = path.stat()
        return _read(str(path), stat.st_mtime_ns, stat.st_size)
    except OSError:
        return {}


def reconciliation(store, operation, receipt, child, supervisor):
    """Describe missing execution evidence without accepting or retrying work."""
    import ars
    directory = Path(operation['directory'])
    def metadata(name):
        path = directory / name
        try:
            if path.is_symlink() or not path.resolve().is_relative_to(store.directory.resolve()):
                return {'exists': False}
            stat = path.stat()
            return {'exists': True, 'bytes': stat.st_size,
                    'updated_at': dt.datetime.fromtimestamp(stat.st_mtime, dt.timezone.utc).isoformat()}
        except OSError:
            return {'exists': False}
    files = {name: metadata(name) for name in ('receipt.json', 'result.json', 'events.jsonl')}
    result = read_local(store, directory / 'result.json')
    process_alive = any(bool(p and ars.same_process(p)) for p in (child, supervisor))
    receipt_ok = receipt.get('operation_id') == operation['id'] and type(receipt.get('success')) is bool
    result_ok = bool(result.get('status'))
    checks = [
        {'id': 'receipt', 'label': '原调用最终回执', 'state': 'recorded' if receipt_ok else 'missing',
         'detail': ('已记录成功回执' if receipt.get('success') else '已记录失败回执') if receipt_ok else
                   '回执文件无法读取或身份不匹配' if files['receipt.json']['exists'] else 'receipt.json 尚未生成',
         'condition': '取得与原调用编号一致、包含真实终态的回执；失败回执须保留并处理'},
        {'id': 'result', 'label': '执行者最终结果', 'state': 'recorded' if result_ok else 'missing',
         'detail': '已保存结构化结果，尚待控制器验收' if result_ok else
                   'result.json 为空' if files['result.json'].get('bytes') == 0 else
                   '结果文件无法解析或缺少最终状态' if files['result.json']['exists'] else 'result.json 尚未生成',
         'condition': '保存原调用结构化结果，再由控制器独立核对产物与阶段门槛'},
        {'id': 'process', 'label': '原执行进程与监督进程', 'state': 'alive' if process_alive else 'unconfirmed',
         'detail': '至少一个原进程身份仍匹配；不能据此判定工作完成' if process_alive else '两个原进程身份均未匹配到活动进程；退出原因尚未确认',
         'condition': '核对原进程、残留作业及已保存产物，确认不会重复派发'},
    ]
    missing = [x['detail'] for x in checks[:2] if x['state'] == 'missing']
    return {'operation_id': operation['id'], 'summary': '；'.join(missing) or '原调用终态与控制器账本尚未完成对账',
            'checks': checks, 'files': files, 'process_alive': process_alive,
            'last_output_at': files['events.jsonl'].get('updated_at') if files['events.jsonl'].get('bytes') else None,
            'next_action': '先核对原调用回执、最终结果和残留作业；复用已保存产物，由恢复流程接续，禁止盲目重投',
            'resume_condition': '原调用未知状态已依据真实证据消解，并由控制器独立复验；科学阶段仍按原门槛验收'}


def describe(store, out):
    import ars
    supplements = saved(store)
    dispatched = {json.loads(r['payload']).get('operation_id') for r in store.db.execute("SELECT payload FROM events WHERE type='operation.dispatched'")}
    executions = {}
    delivery = {s['id']: [] for s in supplements}
    for row in store.db.execute('SELECT * FROM operations ORDER BY created_at'):
        op = dict(row); directory = Path(op['directory'])
        request = read_local(store, directory / 'request.json')
        receipt = read_local(store, directory / 'receipt.json')
        child = read_local(store, directory / 'child.json')
        supervisor = read_local(store, directory / 'supervisor.json')
        is_dispatched = op['id'] in dispatched
        executions[op['task_id']] = {
            'operation_id': op['id'], 'backend': request.get('backend') or out['config']['backend'],
            'model': request.get('model') or ('执行器默认模型' if request else out['config'].get('model', '未指定')),
            'identity_source': 'request' if request else 'configuration',
            'model_assignment': request.get('model_assignment'),
            'state': op['state'], 'dispatched': is_dispatched,
            'process_alive': bool(child and ars.same_process(child)),
            'thread_id': op.get('thread_id') or receipt.get('thread_id'),
            'started_at': receipt.get('started_at') or op['created_at'],
            'finished_at': op.get('finalized_at'),
        }
        if op['state'] == 'UNKNOWN':
            executions[op['task_id']]['reconciliation'] = reconciliation(store, op, receipt, child, supervisor)
        attached = request.get('supplements', [])
        for item in supplements:
            included = any(x.get('id') == item['id'] and fingerprint(x) == item['sha256'] for x in attached)
            legacy_included = item['legacy'] and (
                '用户补充：' + item['instruction'] in request.get('memory', []) or
                (request.get('task', {}).get('id') == item.get('legacy_task_id') and
                 request.get('task', {}).get('instruction') == item['instruction']))
            if included or legacy_included:
                delivery[item['id']].append({'operation_id': op['id'], 'task_id': op['task_id'],
                    'created_at': op['created_at'], 'dispatched': is_dispatched,
                    'method': 'dedicated_context' if included else 'legacy_request'})
    originals = {t['id']: t for t in store.tasks()}
    for task in out['tasks']:
        original = originals[task['id']]
        task.update(instruction=original['instruction'], created_at=original['created_at'], parent=original['parent'], execution=executions.get(task['id']))
    out['supplements'] = [dict(item, deliveries=delivery[item['id']],
        delivery_status='dispatched' if any(x['dispatched'] for x in delivery[item['id']]) else
        'prepared' if delivery[item['id']] else 'saved') for item in reversed(supplements)]
    return out
