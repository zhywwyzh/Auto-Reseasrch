"""Read terminal executor errors, not reasoning, and honor provider retry times."""
import datetime as dt
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo


def redact(text):
    text = re.sub(r'sk-[A-Za-z0-9_-]+', '[REDACTED]', text)
    return re.sub(r'(?i)(authorization:|api[_ -]?key\s*[=:]|password\s*[=:])[^\n]+',
                  r'\1 [REDACTED]', text)[:1800]


def quota_error(text):
    return any(term in text.casefold() for term in (
        'hit your usage limit', 'usage limit reached', 'usage_limit_reached',
        'rate_limit_exceeded', 'insufficient_quota', 'billing_hard_limit_reached',
        'organization_usage_limit_exceeded', 'project_usage_limit_exceeded',
        'quota exceeded. check your plan and billing details.', '配额耗尽', '额度用尽'))


def retry_time(text, observed_at, timezone='Asia/Shanghai'):
    """CLI dates use the host locale; record this inference instead of hiding it."""
    observed = dt.datetime.fromisoformat(observed_at)
    if observed.tzinfo is None:
        raise ValueError('error observation time must have a timezone')
    match = re.search(r'try again at\s+([A-Za-z]{3})\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\s+(\d{1,2}):(\d{2})\s*([AP]M)', text, re.I)
    if match:
        month, day, year, hour, minute, ampm = match.groups()
        parsed = dt.datetime.strptime(f'{month} {day} {year} {hour}:{minute} {ampm.upper()}', '%b %d %Y %I:%M %p')
        due = parsed.replace(tzinfo=ZoneInfo(timezone)).astimezone(dt.timezone.utc) + dt.timedelta(seconds=60)
        # A stale reset message must not cause a rapid retry loop.
        if due > observed:
            return due.isoformat(), 'provider_date_host_timezone_inferred'
    return (observed + dt.timedelta(hours=1)).isoformat(), 'bounded_one_hour_backoff_no_future_provider_date'


def diagnose(directory, observed_at, timezone='Asia/Shanghai'):
    directory = Path(directory)
    messages = []
    stream = directory / 'events.jsonl'
    if stream.exists():
        with stream.open() as source:
            for line in source:
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get('type') == 'error' and isinstance(event.get('message'), str):
                    messages.append(event['message'])
                elif event.get('type') == 'turn.failed':
                    error = event.get('error', {})
                    if isinstance(error, dict) and isinstance(error.get('message'), str):
                        messages.append(error['message'])
    stderr = directory / 'stderr.log'
    if not messages and stderr.exists():
        messages.append(stderr.read_text(errors='replace')[-1800:])
    message = redact('\n'.join(dict.fromkeys(text for text in messages if text.strip())))
    out = {'message': message, 'source': 'terminal_error_events_or_stderr'}
    if quota_error(message):
        due, basis = retry_time(message, observed_at, timezone)
        out.update(category='provider_quota', retry_after=due, retry_time_basis=basis)
    return out


def maybe_resume(store, current_time=None):
    """Called under worker.lock: wake once per failed operation, never a job retry."""
    state = store.state()
    if (state['status'] != 'WAITING_EXTERNAL'
            or not state['config'].get('self_repair', {}).get('enabled')):
        return False
    tasks = store.tasks()
    if any(task['status'] in ('PENDING', 'RUNNING', 'UNKNOWN') for task in tasks):
        return False
    if any(state['config'].get(limit, 0) > 0 and state[used] >= state['config'][limit]
           for used, limit in [('calls', 'max_calls'), ('tokens', 'max_tokens'), ('active_seconds', 'max_seconds')]):
        return False
    now = current_time or dt.datetime.now(dt.timezone.utc)
    latest = {task['phase']: task for task in tasks}
    for task in reversed(list(latest.values())):
        if task['status'] != 'FAILED':
            continue
        verification = json.loads(task.get('verification') or '{}')
        error = verification.get('executor_diagnostic', {})
        if not error and task.get('operation_id'):
            operation = store.operation(task['operation_id'])
            directory = Path(operation['directory']) if operation else None
            if directory and directory.resolve().is_relative_to((store.directory / 'operations').resolve()):
                receipt_path = directory / 'receipt.json'
                if receipt_path.exists():
                    receipt = json.loads(receipt_path.read_text())
                    observed = receipt.get('finished_at') or operation['finalized_at']
                    candidate = diagnose(directory, observed)
                    if candidate.get('category') == 'provider_quota':
                        with store.tx():
                            previous = verification.copy()
                            verification.update(error='执行器配额耗尽：' + candidate['message'],
                                                executor_diagnostic=candidate)
                            store.db.execute('UPDATE tasks SET verification=? WHERE id=?',
                                             (json.dumps(verification, ensure_ascii=False), task['id']))
                            store.event('executor.diagnostic_recovered', {'task_id': task['id'],
                                'operation_id': task['operation_id'], 'previous_verification': previous,
                                'diagnostic': candidate, 'raw_files_unchanged': True})
                            store.status('WAITING_EXTERNAL', '执行器配额等待，自动接续时刻：' + candidate['retry_after'])
                        error = candidate
        if error.get('category') != 'provider_quota':
            continue
        due = dt.datetime.fromisoformat(error['retry_after'])
        if now < due:
            return False
        marker = {'task_id': task['id'], 'operation_id': task['operation_id']}
        prior = store.db.execute("SELECT payload FROM events WHERE type='executor.quota_resume'").fetchall()
        if any(all(json.loads(row[0]).get(k) == value for k, value in marker.items()) for row in prior):
            continue
        with store.tx():
            store.event('executor.quota_resume', {**marker, 'retry_after': error['retry_after'],
                        'budgets_unchanged': True, 'research_job_resubmitted': False})
            store.db.execute("UPDATE tasks SET status='PENDING' WHERE id=?", (task['id'],))
            store.status('READY', '已到执行器配额可重试时刻，恢复原阶段；先核对回执与远端作业')
        return True
    return False
