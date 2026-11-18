"""Display registered supplemental execution without changing original gates."""
import hashlib
from pathlib import Path
from urllib.parse import urlencode
import experiment_progress

def observe(directory, state, original):
    registration = state.get('config', {}).get('recovery_observation')
    if not registration or not original:
        return original
    result = {**original, 'warnings': list(original['warnings']), 'metrics': list(original['metrics'])}
    root = Path(directory).resolve()
    try:
        workspace = Path(state['repo']).resolve() / state['config']['workspace'] / 'runs/ars'
        if not root.is_relative_to(workspace) or root.name != state['id']:
            raise ValueError('补测进度运行归属不匹配')
        documents = {}
        for key in ('summary', 'progress'):
            entry = registration[key]
            path = root / entry['path']
            documents[key] = experiment_progress.load(path, root)
            if hashlib.sha256(path.read_bytes()).hexdigest() != entry['sha256']:
                raise ValueError('补测进度证据哈希不匹配')
        (summary, progress) = (documents['summary'], documents['progress'])
        budget = state['config']['recovery_budget']
        recovery = progress['recovery']
        n = summary['recovery_attempts']
        values = [n, summary['recovery_returned'], summary['recovery_rejected'], summary['recovery_pending'], summary['recovery_unknown'], summary['comparison_batches']]
        if any((type(value) is not int or value < 0 for value in values)):
            raise ValueError('补测计数无效')
        if summary['topic'] != state['topic'] or progress['topic'] != state['topic'] or budget.get('approved') is not True or (n != budget['attempts']) or (n != recovery['denominator']) or (recovery['committed'] != n) or (sum(values[1:5]) != n) or (summary['recovery_pending'] != 0) or (summary['recovery_unknown'] != 0) or (recovery['unknown'] != 0) or (recovery['running'] != 0) or (recovery['unstarted_or_not_yet_observed'] != 0) or (values[5] != recovery['verified_batches']) or (values[5] > budget['maximum_batches']) or (summary['task_status'] != 'completed_authorized_supplement') or (progress['supplemental_artifacts_finalized'] is not True):
            raise ValueError('补测计数或批准范围不一致')
        result['original_summary'] = original['summary']
        result['supplemental_execution'] = {'attempts': n, 'terminal': n, 'returned': values[1], 'rejected': values[2], 'batches': values[5], 'unknown': 0, 'source': registration['summary']['path'], 'scientific_admission_inferred': False}
        result['summary'] = '批准的补测已有终态 %s / %s（%s批）：返回候选 %s，拒收 %s。补测执行完成；科学准入与论文完成状态另行核验。' % (n, n, values[5], values[1], values[2])
        result['metrics'] += [{'key': 'supplemental_terminal', 'label': '补测已有终态 / 计划%s' % n, 'value': n}, {'key': 'supplemental_returned', 'label': '补测返回候选', 'value': values[1]}, {'key': 'supplemental_rejected', 'label': '补测拒收（保留）', 'value': values[2]}]
        result['warnings'].insert(0, '以下计数仍为原冻结账本，不能与补测直接相加或据此推断尚未补测：' + original['summary'])
        result['warnings'].append('补测采用独立执行制度；原始未知记录和实验准入状态保留，返回候选不代表科学成功。')
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        result['warnings'].append('登记的补测显示证据未通过核验；仅显示原账本，不推测补测进度。')
    return result

def links(state, observation):
    if not observation or not observation.get('supplemental_execution'):
        return []
    registration = state['config']['recovery_observation']
    return [{'label': label, 'url': '/api/agent/artifact?' + urlencode({'key': state['topic'] + '/' + state['id'], 'stage': 'supplement', 'index': index, 'sha256': registration[key]['sha256']}), 'sha256': registration[key]['sha256']} for (index, key, label) in [(0, 'summary', '补测结果摘要（执行完成，科学准入另验）'), (1, 'progress', '补测计数与原账本边界')]]

def artifact_bytes(directory, state, index, digest):
    if type(index) is not int or index not in (0, 1):
        raise ValueError('无此登记补测摘要')
    observation = observe(directory, state, {'summary': '', 'counts': None, 'metrics': [], 'warnings': []})
    if not observation.get('supplemental_execution'):
        raise ValueError('补测显示证据未通过核验')
    key = ('summary', 'progress')[index]
    entry = state['config']['recovery_observation'][key]
    path = Path(directory).resolve() / entry['path']
    experiment_progress.load(path, Path(directory).resolve())
    body = path.read_bytes()
    if digest != entry['sha256'] or hashlib.sha256(body).hexdigest() != digest:
        raise ValueError('补测产物版本校验失败')
    return ({'path': path, 'sha256': digest}, body)
import local_extensions as _local_extensions
_local_extensions.apply(globals())
