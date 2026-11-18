"""Optional API-first authentication for the Codex CLI executor."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
import subprocess

MODE = 'openai_api_then_chatgpt'
KEY_ENV = 'ARS_CODEX_OPENAI_API_KEY'
ENDPOINT = 'https://api.openai.com/v1'
QUOTA_CODES = {
    'insufficient_quota', 'billing_hard_limit_reached',
    'organization_usage_limit_exceeded', 'project_usage_limit_exceeded',
}
AUTH_ENV = ('OPENAI_API_KEY', 'CODEX_API_KEY', 'CODEX_ACCESS_TOKEN', 'OPENAI_BASE_URL', KEY_ENV)


def read_preset(database):
    """Read exactly one direct OpenAI preset. Never apply CC Switch globally."""
    candidates = []
    try:
        with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True, timeout=2) as connection:
            rows = connection.execute("SELECT settings_config FROM providers WHERE app_type='codex'")
            for raw, in rows:
                settings = json.loads(raw)
                config = settings.get('config')
                if not isinstance(config, str):
                    continue
                urls = re.findall(r'(?m)^\s*base_url\s*=\s*["\x27]([^"\x27]+)["\x27]', config)
                if len(urls) != 1 or urls[0].rstrip('/') != ENDPOINT:
                    continue
                auth = settings.get('auth')
                key = auth.get('OPENAI_API_KEY') if isinstance(auth, dict) else None
                if isinstance(key, str) and re.fullmatch(r'sk-[A-Za-z0-9_-]+', key):
                    candidates.append(key)
    except (OSError, sqlite3.Error, ValueError, AttributeError):
        return None, 'credential_source_unavailable'
    if len(candidates) != 1:
        return None, 'multiple_openai_api_presets' if candidates else 'no_openai_api_preset'
    return candidates[0], None


def override(argv, key, value):
    return [argv[0], '-c', key + '=' + json.dumps(value), *argv[1:]]


def api_command(argv, key, environment):
    provider = 'ars_openai_api'
    argv = override(argv, 'model_provider', provider)
    for field, value in {'name': 'OpenAI API', 'base_url': ENDPOINT,
                         'wire_api': 'responses', 'env_key': KEY_ENV}.items():
        argv = override(argv, 'model_providers.' + provider + '.' + field, value)
    argv = override(argv, 'shell_environment_policy.ignore_default_excludes', False)
    return argv, {**environment, KEY_ENV: key}


def chatgpt_command(argv, environment):
    args = override(argv, 'model_provider', 'openai')
    # Prevent a machine-level alternate endpoint from taking the official fallback.
    args = override(args, 'chatgpt_base_url', 'https://chatgpt.com/backend-api/')
    status = subprocess.run(
        [args[0], '-c', 'model_provider="openai"', 'login', 'status'],
        env=environment, capture_output=True, text=True, timeout=10, check=False,
    )
    if status.returncode or 'Logged in using ChatGPT' not in status.stdout + status.stderr:
        raise RuntimeError('Codex CLI 的 ChatGPT 登录未就绪，无法使用订阅路径')
    return args


def quota_decision(event_path, stderr_path):
    """Look only at terminal provider errors and record whether it is safe to resend."""
    code = None
    worked = False
    with event_path.open(encoding='utf-8', errors='replace') as events:
        for line in events:
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                worked = True  # The unknown output may represent executed work.
                continue
            kind = event.get('type')
            if kind in ('error', 'turn.failed'):
                error = event.get('error') or event
                code = quota_code(error) or code
            elif kind not in ('thread.started', 'turn.started'):
                worked = True
    if not code:
        with stderr_path.open('rb') as stream:
            stream.seek(max(0, stderr_path.stat().st_size - 65536))
            code = quota_code({'message': stream.read().decode(errors='replace')})
    return code, not worked


def quota_code(error):
    if not isinstance(error, dict):
        return None
    for code in (error.get('code'), error.get('type')):
        if isinstance(code, str) and code in QUOTA_CODES:
            return code
    message = error.get('message')
    if not isinstance(message, str):
        return None
    if message.strip() == 'Quota exceeded. Check your plan and billing details.':
        return 'insufficient_quota'
    # Codex CLI commonly wraps the upstream JSON in its terminal error message.
    return next((code for code in sorted(QUOTA_CODES)
                 if re.search(r'"(?:code|type)"\s*:\s*"' + code + r'"', message)), None)


def execute(argv, directory, run_cli, publish):
    """Run the selected CLI path. Only an unexecuted hard-quota rejection can be replayed."""
    environment = {k: v for k, v in os.environ.items() if k not in AUTH_ENV}
    key, reason = read_preset(Path.home() / '.cc-switch/cc-switch.db')
    record = {'mode': MODE, 'selected': None, 'reason': reason}
    run_root = directory.parent.parent
    if key:
        # A key-specific local marker allows a replacement key to take effect.
        marker = run_root / 'executor-auth-quota.json'
        fingerprint = hashlib.sha256(key.encode()).hexdigest()
        try:
            prior = json.loads(marker.read_text())
        except (OSError, ValueError):
            prior = {}
        if prior.get('credential_fingerprint') == fingerprint:
            record['reason'] = 'known_api_quota_exhausted'
        else:
            record['selected'] = 'openai_api'
            publish(directory / 'auth-route.json', record)
            api_argv, api_env = api_command(argv, key, environment)
            status = run_cli(api_argv, api_env)
            if status == 0:
                return status, record
            events, stderr = directory / 'events.jsonl', directory / 'stderr.log'
            code, no_work = quota_decision(events, stderr)
            if not code:
                return status, record
            record.update(reason=code, api_rejected=True, api_exit_code=status)
            publish(directory / 'auth-route.json', record)
            publish(marker, {
                'credential_fingerprint': fingerprint, 'code': code, 'operation': directory.name,
            })
            if not no_work or (directory / 'result.json').exists():
                return status, record
            # Copy before the normal log files are reopened so a failed fallback
            # login check still leaves the original terminal output in view.
            shutil.copyfile(events, directory / 'api-rejection.events.jsonl')
            shutil.copyfile(stderr, directory / 'api-rejection.stderr.log')
    record['selected'] = 'chatgpt'
    publish(directory / 'auth-route.json', record)
    return run_cli(chatgpt_command(argv, environment), environment), record
