"""Per-campaign usage from durable request evidence and live matching metadata.

Never attributes shared chat costs to a run, mutates a campaign or calls a model.
The request-ID index includes failed/unfinished turns and compaction requests.
"""
from collections import defaultdict
import datetime as dt
import json
from pathlib import Path
import re
import sqlite3
import threading
import time

from token_audit import aggregate, usage
import usage_ledger

UUID = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}')


class UsageIndex:
    def __init__(self, root=None):
        self.root = Path(root) if root else Path.home()/'.codex/sessions'
        self.lock = threading.RLock()
        self.inventory = defaultdict(set)
        self.scanned = 0
        self.files = {}

    def _inventory(self, threads):
        if self.scanned and time.monotonic()-self.scanned < 15 and threads.issubset(self.inventory):
            return
        if self.scanned and time.monotonic()-self.scanned < 2:
            return
        found = defaultdict(set)
        for path in self.root.rglob('*.jsonl'):
            for sid in UUID.findall(path.name):
                found[sid].add(path)
        self.inventory = found
        self.scanned = time.monotonic()

    def _read(self, path):
        stat = path.stat()
        cached = self.files.get(path)
        if cached and cached['signature'] == (stat.st_ino, stat.st_size, stat.st_mtime_ns):
            return cached
        if (cached is None or cached['inode'] != stat.st_ino
                or stat.st_size < cached['offset'] or stat.st_size == cached['offset']):
            cached = dict(inode=stat.st_ino, offset=0, sid=None, model=None, turns={}, records={}, warnings=[])
        with path.open('rb') as stream:
            stream.seek(cached['offset'])
            while stream.tell() < stat.st_size:
                begin = stream.tell()
                raw = stream.readline(stat.st_size-begin)
                if not raw.endswith(b'\n'):
                    break  # Do not consume an incomplete line being appended.
                cached['offset'] = stream.tell()
                try:
                    event = json.loads(raw)
                except (ValueError, UnicodeError):
                    if '部分用量来源记录无法解析' not in cached['warnings']:
                        cached['warnings'].append('部分用量来源记录无法解析')
                    continue
                payload = event.get('payload', {})
                if event.get('type') == 'session_meta':
                    cached['sid'] = payload.get('id')
                elif event.get('type') == 'turn_context':
                    cached['model'] = payload.get('model') or cached['model']
                    if payload.get('turn_id'):
                        cached['turns'][payload['turn_id']] = cached['model']
                elif event.get('type') == 'token_usage_record':
                    rid = payload.get('response_id')
                    if not rid:
                        cached['warnings'].append('用量记录缺少请求ID，未计入该项')
                        continue
                    if not isinstance(payload.get('usage'), dict) or not any(k in payload['usage'] for k in ('input_tokens', 'output_tokens')):
                        cached['warnings'].append('请求缺少token计数，未当作零消耗')
                        continue
                    record = dict(response_id=rid,
                        thread_id=payload.get('thread_id') or cached['sid'],
                        model=payload.get('model') or cached['turns'].get(payload.get('turn_id')) or cached['model'],
                        model_basis='response_metadata' if payload.get('model') else 'turn_context',
                        usage=usage(payload.get('usage', {})), timestamp=event.get('timestamp'))
                    if rid in cached['records'] and cached['records'][rid]['usage'] != record['usage']:
                        cached['warnings'].append('同一请求的用量存在冲突，需进一步核对')
                        continue
                    cached['records'][rid] = record
        cached['signature'] = (stat.st_ino, stat.st_size, stat.st_mtime_ns)
        self.files[path] = cached
        return cached

    def records(self, threads):
        """Return only records whose saved thread ID matches this run's calls."""
        if not threads:
            return [], []
        with self.lock:
            self._inventory(threads)
            paths = set().union(*(self.inventory.get(sid, set()) for sid in threads)) if threads else set()
            found, warnings = {}, []
            for path in sorted(paths):
                try:
                    file = self._read(path)
                except OSError:
                    warnings.append('部分模型会话用量暂不可读')
                    continue
                warnings.extend(file['warnings'])
                for rid, row in file['records'].items():
                    if row['thread_id'] not in threads:
                        continue
                    if rid in found and found[rid]['usage'] != row['usage']:
                        warnings.append('同一请求的用量存在冲突，需进一步核对')
                        continue
                    found[rid] = row
            return list(found.values()), sorted(set(warnings))


INDEX = UsageIndex()


def read_receipt(folder):
    try:
        return json.loads((folder/'receipt.json').read_text())
    except (OSError, ValueError):
        return {}


def thread_for(folder, saved, receipt):
    sid = saved or receipt.get('thread_id')
    if sid:
        return sid
    # Older failed receipts did not retain the thread; the terminal stream does.
    try:
        with (folder/'events.jsonl').open() as stream:
            for index, line in enumerate(stream):
                if index > 30:
                    break
                try: event = json.loads(line)
                except ValueError: continue
                if event.get('type') == 'thread.started':
                    return event.get('thread_id')
    except OSError:
        pass
    return None


def grouped_models(rows, basis='turn_context'):
    groups = defaultdict(list)
    for row in rows:
        groups[row.get('model') or '未记录模型'].append(row['usage'])
    return [dict(model=model, basis=basis, requests=len(values), **aggregate(values))
            for model, values in sorted(groups.items())]


def sum_models(attempts):
    groups = defaultdict(list)
    for attempt in attempts:
        for model in attempt['models']:
            groups[model['model']].append(model)
    return [dict(model=model, **aggregate(values)) for model, values in sorted(groups.items())]


def describe(store, index=None, include_requests=False):
    index = index or INDEX
    state, tasks = store.state(), store.tasks()
    config = state['config']
    persisted = usage_ledger.read(store.directory)
    operations = [dict(row) for row in store.db.execute('SELECT * FROM operations ORDER BY created_at,rowid')]
    seen_threads = set()
    for op in operations:
        folder = Path(op['directory'])
        previous = persisted['operations'].get(op['id'], {})
        op['receipt'] = dict(previous.get('receipt', {}))
        op['receipt'].update({k: v for k, v in read_receipt(folder).items() if v is not None and (k != 'usage' or v)})
        op['sid'] = thread_for(folder, op.get('thread_id'), op['receipt']) or previous.get('thread_id')
        op['configured_model'] = previous.get('configured_model')
        if op['configured_model'] is None:
            try:
                op['configured_model'] = json.loads((folder/'request.json').read_text())['config'].get('model') or None
            except (OSError, ValueError, KeyError):
                pass
        if op['sid']:
            if op['sid'] in seen_threads:
                raise ValueError('同一模型会话重复关联多个操作，无法安全加总用量')
            seen_threads.add(op['sid'])
    records, warnings = index.records(seen_threads)
    saved_records = [r for r in persisted['requests'] if r['thread_id'] in seen_threads]
    records, conflicts = usage_ledger.merge_records(saved_records, records)
    warnings += persisted['warnings'] + conflicts
    by_thread = defaultdict(list)
    for row in records:
        by_thread[row['thread_id']].append(row)
    attempts, model_rows = [], []
    task_attempts = defaultdict(int)
    for op in operations:
        rows = by_thread.get(op['sid'], [])
        receipt = op['receipt']
        ledger = json.loads(op.get('usage') or '{}')
        saved_usage = receipt.get('usage') or ledger
        basis, models, requests = 'missing', [], 0
        active = op['state'] in ('RESERVED', 'DISPATCHED', 'UNKNOWN', 'CANCEL_REQUESTED')
        if rows:
            observed = aggregate(row['usage'] for row in rows)
            basis, models, requests = 'request_records', grouped_models(rows), len(rows)
        elif receipt.get('new_model_call') is False or config.get('backend') == 'mock':
            observed = usage({})
            basis = 'no_model_call' if receipt.get('new_model_call') is False else 'mock'
        elif saved_usage and any(key in saved_usage for key in ('input_tokens', 'output_tokens')):
            observed, basis = usage(saved_usage), 'executor_receipt'
            models = [dict(model='未记录实际模型', basis='receipt_only', requests=0, **observed)]
            warnings.append('部分调用仅有执行器汇总回执，可能不含压缩请求；未用当前配置冒充实际模型')
        else:
            observed = None
        task_attempts[op['task_id']] += 1
        model_rows.extend(models)
        attempts.append(dict(id=op['id'], task_id=op['task_id'], number=task_attempts[op['task_id']],
            state=op['state'], executor_success=receipt.get('success'),
            started_at=receipt.get('started_at') or op['created_at'], finished_at=receipt.get('finished_at'),
            usage=observed, source=basis, models=models, request_count=requests,
            configured_model=op['configured_model'],
            persisted_requests=sum(r.get('operation_id') == op['id'] for r in saved_records),
            pending=active, missing=observed is None and not active,
            ledger_tokens=usage(ledger)['total_tokens']))
    by_task = defaultdict(list)
    for row in attempts:
        by_task[row['task_id']].append(row)
    task_rows = []
    for task in tasks:
        ops = by_task[task['id']]
        task_rows.append(dict(id=task['id'], phase=task['phase'], title=task['title'], status=task['status'],
            attempts=ops, attempt_count=len(ops), usage=aggregate(row['usage'] for row in ops if row['usage'] is not None),
            models=sorted({m['model'] for row in ops for m in row['models']}),
            model_usage=sum_models(ops),
            missing_attempts=sum(row['missing'] for row in ops), pending_attempts=sum(row['pending'] for row in ops)))
    phase_groups = defaultdict(list)
    for row in task_rows:
        phase_groups[row['phase']].append(row)
    phases = [dict(phase=phase, tasks=len(rows), usage=aggregate(row['usage'] for row in rows),
                  models=sorted({m for row in rows for m in row['models']}),
                  attempts=sum(row['attempt_count'] for row in rows),
                  missing_attempts=sum(row['missing_attempts'] for row in rows),
                  pending_attempts=sum(row['pending_attempts'] for row in rows)) for phase, rows in phase_groups.items()]
    model_groups = defaultdict(list)
    for row in model_rows:
        model_groups[(row['model'],row['basis'])].append(row)
    models = [dict(model=model, basis=basis, usage=aggregate(rows), requests=sum(row['requests'] for row in rows))
              for (model,basis), rows in sorted(model_groups.items())]
    total = aggregate(row['usage'] for row in attempts if row['usage'] is not None)
    missing = sum(row['missing'] for row in attempts)
    pending = sum(row['pending'] for row in attempts)
    if missing:
        warnings.append(str(missing)+'次调用缺少用量记录，显示已观测下界，不按零消耗处理')
    if pending:
        warnings.append('进行中或状态待核对的调用仅计已落盘请求，尚未返回的用量未计入')
    collector = {}
    try:
        collector = json.loads((store.directory/'usage-collector-status.json').read_text())
        if collector.get('ok') is False:
            warnings.append('持久用量采集出现错误；保留已存记录，等待自动复查')
    except (OSError, ValueError):
        pass
    result = dict(version='run-token-usage-v2', available=True, topic=state['topic'], run_id=state['id'],
        sampled_at=dt.datetime.now(dt.timezone.utc).isoformat(), totals=total,
        ledger_tokens=state['tokens'], ledger_difference=total['total_tokens']-state['tokens'],
        models=models, configured_model=config.get('model') or None, tasks=task_rows, phases=phases,
        operation_count=len(attempts), request_count=sum(row['request_count'] for row in attempts),
        missing_attempts=missing, pending_attempts=pending, lower_bound=bool(missing or pending or warnings),
        persistence=dict(enabled=bool(persisted['updated_at']), updated_at=persisted['updated_at'],
                         request_count=len(saved_records), operation_count=len(persisted['operations']),
                         collector_ok=collector.get('ok')),
        warnings=sorted(set(warnings)),
        scope='仅含与本次运行操作ID绑定的调用；包含失败、重试、代码修复和上下文压缩。账本外协作未强行分摊到本运行。',
        counting='总token＝输入＋输出；缓存输入包含在输入，推理输出包含在输出，均不重复相加。',
        refresh='运行时持续保存逐请求模型与用量；页面合并账本和新增记录。采集通常每15秒更新，不触发模型调用。')
    if include_requests:
        operations_by_thread = {op['sid']: op for op in operations if op['sid']}
        task_map = {t['id']: t for t in tasks}
        result['requests'] = [dict(response_id=row['response_id'], model=row.get('model') or '未记录模型',
            model_basis=row.get('model_basis') or 'turn_context', timestamp=row.get('timestamp'), usage=row['usage'],
            operation_id=operations_by_thread[row['thread_id']]['id'],
            task_id=operations_by_thread[row['thread_id']]['task_id'],
            title=task_map[operations_by_thread[row['thread_id']]['task_id']]['title']) for row in records]
    return result


def portfolio(paths, include_demo=False):
    """Deduplicate request IDs across registered runs; metadata only, read only."""
    import ars
    requests, fallback, runs, tasks, warnings = {}, {}, [], [], []
    for key, directory in paths.items():
        store = ars.Store(directory)
        try:
            if store.state()['topic'] == 'ARS-DEMO' and not include_demo:
                continue
            report = describe(store, include_requests=True)
        except (OSError, ValueError, KeyError, TypeError, sqlite3.Error):
            warnings.append(key + '：用量尚未完成核对，未按零计入')
            continue
        finally:
            store.close()
        metadata = dict(key=key, topic=report['topic'], run_id=report['run_id'])
        runs.append(dict(metadata, **{k: report[k] for k in ('totals','models','request_count','operation_count','missing_attempts','pending_attempts','lower_bound')}))
        tasks.extend(dict(task, **metadata) for task in report['tasks'])
        warnings.extend(key + '：' + w for w in report['warnings'])
        for row in report['requests']:
            previous = requests.get(row['response_id'])
            if previous and (previous['usage'] != row['usage'] or previous['model'] != row['model']):
                warnings.append('同一请求的模型或用量存在冲突，仅保留首份记录')
            if not previous:
                requests[row['response_id']] = dict(row, **metadata)
        for task in report['tasks']:
            for attempt in task['attempts']:
                if attempt['source'] == 'executor_receipt':
                    fallback.setdefault(attempt['id'], dict(attempt, **metadata))
    # A request-level observation supersedes an older receipt of that operation.
    observed_operations = {r['operation_id'] for r in requests.values()}
    fallback = {k:v for k,v in fallback.items() if k not in observed_operations}
    groups = defaultdict(list)
    for row in requests.values():
        groups[row['model']].append(row)
    for row in fallback.values():
        groups['未记录实际模型'].append(dict(row, response_id=None))
    models = [dict(model=model, usage=aggregate(r['usage'] for r in rows),
        requests=sum(bool(r.get('response_id')) for r in rows),
        operations=len({r.get('operation_id') or r.get('id') for r in rows}),
        receipt_only=sum(not r.get('response_id') for r in rows)) for model, rows in groups.items()]
    return dict(available=True, sampled_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        totals=aggregate(r['usage'] for rows in groups.values() for r in rows),
        models=sorted(models,key=lambda m:m['usage']['total_tokens'],reverse=True), runs=runs, tasks=tasks,
        requests=sorted(requests.values(),key=lambda r:r.get('timestamp') or '',reverse=True),
        request_count=len(requests), receipt_only=len(fallback),
        missing_attempts=sum(r['missing_attempts'] for r in runs),
        pending_attempts=sum(r['pending_attempts'] for r in runs), warnings=sorted(set(warnings)),
        counting='总 token＝输入＋输出；缓存输入是输入的子集，推理输出是输出的子集，不重复相加。',
        scope='已登记研究运行的模型调用，包含历史运行、失败、重试、修复和压缩；按请求ID去重。聊天、账本外协作与系统策略优化未纳入。')


def observe(store):
    try:
        return describe(store)
    except (OSError, ValueError, TypeError, KeyError, sqlite3.Error) as exc:
        return dict(version='run-token-usage-v2', available=False,
                    ledger_tokens=store.state()['tokens'], warnings=['用量暂未完成核对，请稍后刷新；原账本保留。'])
