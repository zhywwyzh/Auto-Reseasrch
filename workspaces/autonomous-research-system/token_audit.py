"""Read-only token accounting from saved per-response metadata, never messages.

Request usage records include failed turns and compaction requests. Ledger totals
remain a separate reconciliation column; input cache/reasoning are subsets.
"""
import argparse
from collections import Counter, defaultdict
import datetime as dt
import hashlib
import json
from pathlib import Path
import sqlite3
FIELDS = ('input_tokens', 'cached_input_tokens', 'cache_write_input_tokens', 'output_tokens', 'reasoning_output_tokens')
HISTORY = {}

def usage(raw):
    result = {k: max(0, int(raw.get(k, 0) or 0)) for k in FIELDS}
    result['total_tokens'] = result['input_tokens'] + result['output_tokens']
    return result

def aggregate(rows):
    result = Counter()
    for row in rows:
        result.update({k: row.get(k, 0) for k in FIELDS + ('total_tokens',)})
    return {k: result[k] for k in FIELDS + ('total_tokens',)}

def load_ledger(repo):
    (campaigns, operations, mapping) = ([], [], {})
    for path in sorted(repo.glob('workspaces/*/runs/ars/*/state.sqlite3')):
        db = sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)
        db.row_factory = sqlite3.Row
        try:
            db.execute('BEGIN')
            c = dict(db.execute('SELECT * FROM campaign').fetchone())
            config = json.loads(c['config'])
            campaign = {k: c[k] for k in ('topic', 'id', 'status', 'calls', 'tokens', 'created_at', 'updated_at')}
            campaign.update(backend=config.get('backend'), configured_model=config.get('model'), database=str(path.relative_to(repo)))
            campaigns.append(campaign)
            for raw in db.execute('SELECT o.*,t.phase,t.title,t.status AS task_status FROM operations o JOIN tasks t ON o.task_id=t.id ORDER BY o.created_at'):
                raw = dict(raw)
                folder = Path(raw['directory'])
                receipt_path = folder / 'receipt.json'
                receipt = json.loads(receipt_path.read_text()) if receipt_path.exists() else {}
                thread = raw['thread_id'] or receipt.get('thread_id')
                if not thread and (folder / 'events.jsonl').exists():
                    for line in (folder / 'events.jsonl').open():
                        try:
                            event = json.loads(line)
                        except ValueError:
                            continue
                        if event.get('type') == 'thread.started':
                            thread = event.get('thread_id')
                            break
                row = {k: raw[k] for k in ('id', 'task_id', 'phase', 'title', 'state', 'task_status', 'created_at')}
                row.update(topic=c['topic'], campaign=c['id'], thread_id=thread, configured_model=config.get('model'), backend=config.get('backend'), ledger_usage=usage(json.loads(raw['usage'] or '{}')), receipt_success=receipt.get('success'), receipt_usage_present=bool(receipt.get('usage')), new_model_call=receipt.get('new_model_call'), directory=str(folder.relative_to(repo)) if folder.is_relative_to(repo) else str(folder))
                operations.append(row)
                if thread:
                    if thread in mapping:
                        raise ValueError('Duplicate operation/thread identity: ' + thread)
                    mapping[thread] = row
        finally:
            db.close()
    for path in sorted(repo.glob('workspaces/autonomous-research-system/runs/evolution/operations/*/receipt.json')):
        receipt = json.loads(path.read_text())
        thread = receipt.get('thread_id')
        row = dict(id=path.parent.name, task_id=path.parent.name, phase='system_evolution', title='系统策略生成与修改', state='RECEIPT', task_status='SUCCEEDED' if receipt.get('success') else 'FAILED', created_at=receipt.get('started_at'), topic='SYSTEM', campaign='evolution', thread_id=thread, configured_model=None, backend='codex', ledger_usage=usage(receipt.get('usage', {})), receipt_success=receipt.get('success'), receipt_usage_present=bool(receipt.get('usage')), new_model_call=receipt.get('new_model_call'), directory=str(path.parent.relative_to(repo)))
        operations.append(row)
        if thread:
            if thread in mapping:
                raise ValueError('Duplicate evolution/thread identity')
            mapping[thread] = row
    return (campaigns, operations, mapping)

def collect_sessions(repo, session_root, mapped, cutoff):
    (records, sessions, sources) = ({}, {}, [])
    duplicate_records = 0
    for path in sorted(session_root.rglob('*.jsonl')):
        with path.open() as stream:
            try:
                first = json.loads(stream.readline())
            except ValueError:
                continue
            meta = first.get('payload', {})
            if first.get('type') != 'session_meta':
                continue
            (sid, cwd) = (meta.get('id'), meta.get('cwd', ''))
            related = cwd and (Path(cwd).is_relative_to(repo) or str(repo) == str(Path(cwd).resolve()))
            if not related and sid not in mapped:
                continue
            info = sessions.setdefault(sid, dict(id=sid, files=[], origin=meta.get('originator'), cwd=cwd, created_at=meta.get('timestamp'), models=[], usage_records=0))
            info['files'].append(path.name)
            source = dict(file=path.name, session_id=sid, scanned_bytes=0, last_usage_at=None)
            (models, model) = ({}, None)
            for line in stream:
                source['scanned_bytes'] += len(line.encode())
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get('timestamp', '') > cutoff:
                    continue
                payload = event.get('payload', {})
                if event.get('type') == 'turn_context':
                    model = payload.get('model') or model
                    if payload.get('turn_id'):
                        models[payload['turn_id']] = model
                if event.get('type') != 'token_usage_record':
                    continue
                rid = payload.get('response_id')
                if not rid:
                    raise ValueError('Per-request usage missing response identity: ' + path.name)
                values = usage(payload.get('usage', {}))
                if rid in records:
                    if records[rid]['usage'] != values:
                        raise ValueError('Conflicting request usage: ' + rid)
                    duplicate_records += 1
                    continue
                actual_model = models.get(payload.get('turn_id')) or model or '未记录模型'
                owner = payload.get('thread_id') or sid
                op = mapped.get(owner) or mapped.get(sid)
                bucket = op['topic'] if op else HISTORY.get(sid, 'SHARED')
                records[rid] = dict(response_id=rid, session_id=owner, model=actual_model, model_basis='turn_context' if actual_model != '未记录模型' else 'missing', topic=bucket, campaign=op['campaign'] if op else 'outside-ledger', operation_id=op['id'] if op else None, phase=op['phase'] if op else 'outside-ledger', scope='system_evolution' if op and op['phase'] == 'system_evolution' else 'ars' if op else 'outside-ledger', timestamp=event.get('timestamp'), usage=values)
                info['usage_records'] += 1
                if actual_model not in info['models']:
                    info['models'].append(actual_model)
                source['last_usage_at'] = event.get('timestamp')
            sources.append(source)
    return (list(records.values()), list(sessions.values()), sources, duplicate_records)

def audit(repo, session_root, cutoff=None):
    repo = Path(repo).resolve()
    cutoff = cutoff or dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')
    (campaigns, operations, mapping) = load_ledger(repo)
    (requests, sessions, sources, duplicates) = collect_sessions(repo, Path(session_root), mapping, cutoff)
    by_operation = defaultdict(list)
    for row in requests:
        if row['operation_id']:
            by_operation[row['operation_id']].append(row)
    missing = []
    for op in operations:
        rows = by_operation[op['id']]
        op['observed_usage'] = aggregate((r['usage'] for r in rows)) if rows else None
        op['request_count'] = len(rows)
        op['models'] = sorted({r['model'] for r in rows})
        if rows:
            op['ledger_difference'] = op['observed_usage']['total_tokens'] - op['ledger_usage']['total_tokens']
            op['usage_status'] = 'observed'
        else:
            op['ledger_difference'] = None
            op['usage_status'] = 'no_model_call' if op.get('new_model_call') is False else 'mock' if op['backend'] == 'mock' else 'missing'
            if op['usage_status'] == 'missing':
                missing.append(dict(operation_id=op['id'], topic=op['topic'], campaign=op['campaign'], phase=op['phase'], state=op['state'], receipt_success=op['receipt_success'], explanation='No per-request usage found; this is unknown usage, not proof of zero consumption.'))

    def grouped(keys):
        groups = defaultdict(list)
        for row in requests:
            groups[tuple((row[k] for k in keys))].append(row)
        return [dict(zip(keys, key), **aggregate((r['usage'] for r in rows)), requests=len(rows)) for (key, rows) in sorted(groups.items())]
    for c in campaigns:
        rows = [r for r in requests if r['topic'] == c['topic'] and r['campaign'] == c['id']]
        c['observed_usage'] = aggregate((r['usage'] for r in rows))
        c['request_count'] = len(rows)
        c['ledger_difference'] = c['observed_usage']['total_tokens'] - c['tokens']
        c['models'] = sorted({r['model'] for r in rows})
    task_groups = defaultdict(list)
    for op in operations:
        task_groups[op['topic'], op['campaign'], op['task_id']].append(op)
    tasks = []
    for ((topic, campaign, task_id), ops) in sorted(task_groups.items()):
        known = [o for o in ops if o['observed_usage'] is not None]
        tasks.append(dict(topic=topic, campaign=campaign, task_id=task_id, phase=ops[-1]['phase'], title=ops[-1]['title'], status=ops[-1]['task_status'], attempts=len(ops), observed_usage=aggregate((o['observed_usage'] for o in known)), operations_without_usage=sum((o['usage_status'] == 'missing' for o in ops)), models=sorted({m for o in ops for m in o['models']})))
    return dict(version='token-audit-v1', cutoff_utc=cutoff, generated_at=dt.datetime.now(dt.timezone.utc).isoformat(), metric='total_tokens = input_tokens + output_tokens; cached input is included in input; reasoning output is included in output', scope='Locally saved request usage for this repository/worktrees, matched to ARS operations and historical collaboration sessions. Not an invoice or complete provider account export.', totals=aggregate((r['usage'] for r in requests)), by_scope=grouped(['scope']), by_topic_scope=grouped(['topic', 'scope']), by_model_scope=grouped(['model', 'scope']), by_topic_phase=grouped(['topic', 'phase']), by_topic_model=grouped(['topic', 'model']), campaigns=campaigns, tasks=tasks, operations=operations, sessions=sessions, sources=sources, request_count=len(requests), duplicate_request_records_ignored=duplicates, operations_without_request_usage=missing, requests=requests, limitations=['Ongoing calls without a saved usage response, missing/deleted sessions, other hosts/accounts and the current chat if not locally recorded are excluded; observed totals are a lower bound.', 'Outside-ledger collaboration cannot be rigorously split into research/writing/code/review. Only registered historical topic sessions or a dedicated topic worktree are attributed; mixed system sessions stay SHARED.', 'ARS phase totals describe the assigned task stage, not semantic classification of every thought/tool action. Failed attempts and retries are retained.', 'Per-response records are deduplicated by response_id; repeated token_count cumulative snapshots are never added. Resumed files with the same session ID and distinct responses are retained.', 'Models are read from saved turn_context, rather than treating a current model setting as historical fact. No monetary conversion or quota weighting is inferred.'])
import local_extensions as _local_extensions
_local_extensions.apply(globals())
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument('--sessions', type=Path, default=Path.home() / '.codex/sessions')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cutoff', help='UTC ISO timestamp for a reproducible saved snapshot')
    args = parser.parse_args()
    result = audit(args.repo, args.sessions, args.cutoff)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('cutoff_utc', 'totals', 'by_scope', 'by_topic_scope', 'by_model_scope', 'request_count')}, ensure_ascii=False, indent=2))
