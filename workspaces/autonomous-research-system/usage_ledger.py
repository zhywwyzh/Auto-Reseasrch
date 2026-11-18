"""Durable per-task model usage. Metadata only; never dispatches research work.

The sidecar database keeps request-level evidence after provider log rotation.
It does not rewrite the original reservation, cost, or scientific task ledger.
"""
import argparse
import datetime as dt
import fcntl
import json
import os
from pathlib import Path
import signal
import sqlite3
import time

VERSION = 'task-model-usage-v2'
FILENAME = 'usage.sqlite3'


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def read(directory):
    path = Path(directory) / FILENAME
    empty = dict(operations={}, requests=[], warnings=[], updated_at=None)
    if not path.exists():
        return empty
    db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=2)
    db.row_factory = sqlite3.Row
    try:
        db.execute('BEGIN')
        operations = {r['id']: json.loads(r['payload']) for r in db.execute('SELECT * FROM usage_operations')}
        requests = []
        for row in db.execute('SELECT * FROM usage_requests ORDER BY rowid'):
            item = dict(row)
            item['usage'] = json.loads(item.pop('usage_json'))
            requests.append(item)
        meta = db.execute("SELECT value FROM metadata WHERE key='updated_at'").fetchone()
        return dict(operations=operations, requests=requests,
                    warnings=[r[0] for r in db.execute('SELECT message FROM usage_warnings')],
                    updated_at=meta[0] if meta else None)
    finally:
        db.close()


def merge_records(saved, fresh):
    records, warnings = {}, []
    for row in [*saved, *fresh]:
        key = row['response_id']
        old = records.get(key)
        if old and (old['usage'] != row['usage'] or old['thread_id'] != row['thread_id']
                    or (old.get('model') and row.get('model') and old['model'] != row['model'])):
            warnings.append('同一请求的模型或用量存在冲突；保留先前记录，需核对')
            continue
        if not old or (not old.get('model') and row.get('model')):
            records[key] = row
    return list(records.values()), warnings


def sync(store, index=None):
    import token_usage
    from token_audit import usage
    index = index or token_usage.INDEX
    saved = read(store.directory)
    tasks = {t['id']: t for t in store.tasks()}
    operations, threads = [], {}
    for raw in store.db.execute('SELECT * FROM operations ORDER BY created_at,rowid'):
        op = dict(raw)
        previous = saved['operations'].get(op['id'], {})
        folder = Path(op['directory'])
        receipt = token_usage.read_receipt(folder)
        sid = token_usage.thread_for(folder, op.get('thread_id'), receipt) or previous.get('thread_id')
        if sid and sid in threads and threads[sid] != op['id']:
            raise ValueError('同一模型会话关联多个操作；拒绝错误分摊')
        if sid:
            threads[sid] = op['id']
        try:
            cfg = json.loads((folder / 'request.json').read_text())['config']
        except (OSError, ValueError, KeyError):
            cfg = {}
        # Never use today's campaign model as yesterday's actual/configured model.
        historical = {k: receipt[k] for k in ('success', 'usage', 'new_model_call', 'started_at', 'finished_at') if k in receipt}
        fallback = json.loads(op.get('usage') or '{}')
        if not historical.get('usage') and fallback:
            historical['usage'] = fallback
        retained = dict(previous.get('receipt', {}))
        retained.update({k: v for k, v in historical.items() if v is not None and (k != 'usage' or v)})
        task = tasks[op['task_id']]
        operations.append(dict(id=op['id'], task_id=op['task_id'], phase=task['phase'], title=task['title'],
            state=op['state'], thread_id=sid, configured_model=cfg.get('model') or previous.get('configured_model'),
            backend=cfg.get('backend') or previous.get('backend'), receipt=retained,
            created_at=op['created_at'], recorded_at=now()))
    records, warnings = index.records(set(threads))
    records, conflicts = merge_records(saved['requests'], records)
    warnings += conflicts
    path = store.directory / FILENAME
    db = sqlite3.connect(path, timeout=2)
    try:
        db.execute('PRAGMA journal_mode=WAL')
        db.executescript('''
            CREATE TABLE IF NOT EXISTS usage_operations(id TEXT PRIMARY KEY, task_id TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS usage_requests(response_id TEXT PRIMARY KEY, operation_id TEXT NOT NULL,
                task_id TEXT NOT NULL, thread_id TEXT NOT NULL, model TEXT, model_basis TEXT,
                usage_json TEXT NOT NULL, timestamp TEXT, recorded_at TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS usage_request_operation ON usage_requests(operation_id);
            CREATE TABLE IF NOT EXISTS usage_warnings(message TEXT PRIMARY KEY);
            CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY,value TEXT);
        ''')
        by_id = {op['id']: op for op in operations}
        with db:
            for op in operations:
                db.execute('INSERT INTO usage_operations VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET payload=excluded.payload',
                           (op['id'], op['task_id'], json.dumps(op, ensure_ascii=False)))
            for row in records:
                op_id = threads.get(row['thread_id'])
                if not op_id:
                    continue
                normalized = usage(row['usage'])
                existing = db.execute('SELECT operation_id,model,usage_json FROM usage_requests WHERE response_id=?',
                                      (row['response_id'],)).fetchone()
                if existing:
                    if (existing[0] != op_id or json.loads(existing[2]) != normalized
                            or (existing[1] and row.get('model') and existing[1] != row['model'])):
                        warnings.append('同一请求的模型或用量存在冲突；保留先前记录，需核对')
                    elif not existing[1] and row.get('model'):
                        db.execute('UPDATE usage_requests SET model=?,model_basis=? WHERE response_id=?',
                                   (row['model'], row.get('model_basis', 'turn_context'), row['response_id']))
                    continue
                db.execute('INSERT INTO usage_requests VALUES(?,?,?,?,?,?,?,?,?)',
                    (row['response_id'], op_id, by_id[op_id]['task_id'], row['thread_id'], row.get('model'),
                     row.get('model_basis', 'turn_context'), json.dumps(normalized), row.get('timestamp'), now()))
            for warning in set(warnings):
                db.execute('INSERT OR IGNORE INTO usage_warnings VALUES(?)', (warning,))
            db.execute("INSERT INTO metadata VALUES('updated_at',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (now(),))
            db.execute("INSERT INTO metadata VALUES('version',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value", (VERSION,))
        return dict(version=VERSION, operations=len(operations),
                    requests=db.execute('SELECT COUNT(*) FROM usage_requests').fetchone()[0], warnings=sorted(set(warnings)))
    finally:
        db.close()


def safe_sync(store):
    import ars
    import executor_errors
    try:
        result = sync(store)
        status = dict(ok=True, at=now(), **result)
    except Exception as exc:
        status = dict(ok=False, at=now(), error=executor_errors.redact(str(exc)))
    # A usage collection failure must never cancel or redispatch research work.
    try:
        ars.atomic_json(store.directory / 'usage-collector-status.json', status)
    except OSError:
        pass
    return status


def campaigns(repo):
    repo = Path(repo).resolve()
    catalog = json.loads((repo / 'workspaces/topics.json').read_text())
    roots = [repo / 'workspaces/autonomous-research-system']
    roots += [repo / row['workspace'] for row in catalog['topics']]
    for root in roots:
        for path in (root / 'runs/ars').glob('*/state.sqlite3'):
            if not path.is_symlink() and path.resolve().is_relative_to(root.resolve()):
                yield path.parent


def collect(repo):
    import ars
    import executor_errors
    out = []
    for directory in campaigns(repo):
        store = None
        try:
            store = ars.Store(directory)
            store.db.execute('PRAGMA query_only=ON')
            state = store.state()
            out.append(dict(topic=state['topic'], run_id=state['id'], **safe_sync(store)))
        except Exception as exc:
            out.append(dict(run_id=directory.name, ok=False, at=now(), error=executor_errors.redact(str(exc))))
        finally:
            if store:
                store.close()
    return out


def main():
    import ars
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['collect', 'serve'])
    parser.add_argument('--repo', type=Path, default=ars.REPO)
    args = parser.parse_args()
    if args.command == 'collect':
        print(json.dumps(collect(args.repo), ensure_ascii=False))
        return
    root = args.repo / 'workspaces/autonomous-research-system/runs/usage-collector'
    root.mkdir(parents=True, exist_ok=True)
    with (root / 'service.lock').open('a+') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        stopping = False
        def stop(*_):
            nonlocal stopping
            stopping = True
        signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
        ars.atomic_json(root / 'process.json', ars.process_identity(os.getpid()))
        while not stopping:
            ars.atomic_json(root / 'status.json', dict(at=now(), campaigns=collect(args.repo)))
            for _ in range(75):
                if stopping:
                    break
                time.sleep(.2)


if __name__ == '__main__':
    main()
