"""Evolvable, JSON-only decisions. Authority and acceptance live in the kernel."""
import hashlib
import re


def classify(error):
    text = error.casefold()
    if re.search(r'预算.{0,40}(?:未获(?:决定|批准|授权)|(?:尚未|未经)(?:批准|授权)|耗尽|达到上限)', text) or '实验预算须补足' in text:
        return 'authorization'
    rules = [
        ('provider_quota', ('hit your usage limit', 'usage limit reached', 'usage_limit_reached', 'rate_limit_exceeded', 'insufficient_quota', '执行器配额等待', '配额耗尽')),
        ('uncertain_execution', ('unknown', '状态不明', '未知调用', '缺少回执', '无法确认执行')),
        ('external_evidence', ('source pdf not available', 'eta normalizer missing', '原始定义依据缺失', '缺少原始定义依据', '必须由作者提供的原始', '必须由用户提供的原始', '缺学位同版本', '仍待具体依赖')),
        ('authorization', ('超出授权', '新增授权', '需要用户决定', '需要用户决策', '未经授权', '付费调用授权', '授权时间仅余')),
        ('transport', ('no route to host', '网络不可达', '无路由', '邻居解析', 'connection refused', 'connection reset', 'connection timed out', '认证前不可达', 'permission denied (publickey', 'ssh登录', 'ssh登陆', '连接失败')),
        ('environment', ('modulenotfound', 'importerror', 'not installed', 'command not found', '依赖缺失', '尚未安装', '未安装', 'cpu委派', 'cgroup', 'out of memory', 'oom', '编译失败', 'permission denied')),
        ('implementation', ('traceback', 'assertion', '测试失败', '验收失败', 'timeouterror', '超时')),
        ('artifact_contract', ('阶段产物为空', 'manifest', '阶段缺少产物', '产物哈希', '产物未通过结构', 'json', 'schema')),
        ('provenance', ('摘录', 'source', '来源', 'sha256', '哈希')),
        ('transport', ('ssh', 'connection', 'connecttimeout', '网络', '认证', '登录')),
        ('environment', ('julia', 'docker')),
    ]
    return next((kind for kind, words in rules if any(w in text for w in words)), 'unclassified')


def incident(error):
    """Normalize volatile paths/counters; different root causes have separate budgets."""
    category = classify(error)
    roots = {
        'transport': [('route', ('no route', '无路由', '邻居解析', '不可达')), ('auth', ('permission denied', '认证', '登录', '登陆')), ('timeout', ('timed out', 'timeout'))],
        'environment': [('resource', ('cgroup', 'cpu委派', '配额', 'memory', 'oom')), ('dependency', ('import', 'installed', '安装', 'not found', '依赖'))],
        'artifact_contract': [('empty', ('为空', 'empty')), ('manifest', ('manifest',)), ('schema', ('json', 'schema'))],
        'provenance': [('scope', ('范围', 'scope')), ('missing', ('不存在', 'missing')), ('mismatch', ('不匹配', 'mismatch'))],
    }
    lower = error.casefold()
    if category == 'transport' and ('controlmaster' in lower or 'control socket' in lower
                                   or ('socket' in lower and any(w in lower for w in ('不存在', '失效', 'expired')))):
        return 'transport:auth'
    root = next((name for name, words in roots.get(category, []) if any(w in lower for w in words)), None)
    if root is None:
        normalized = re.sub(r'/[^\s，；。]+|\b[0-9a-f]{16,}\b|\d+', '<value>', lower)
        root = hashlib.sha256(normalized.encode()).hexdigest()[:16]
    return category + ':' + root


def frontier(tasks, order):
    """Latest attempt of the furthest stage; resource reruns never rewind progress."""
    relevant = [(order.index(t['phase']), i, t['id']) for i, t in enumerate(tasks) if t['phase'] in order]
    return max(relevant)[2] if relevant else None


def select_memory(memories, instruction, goal, limit):
    terms = set(re.findall(r'[A-Za-z0-9_]+|[\u4e00-\u9fff]{2,4}', instruction + ' ' + goal))
    ranked = sorted(enumerate(memories), key=lambda row: (sum(t in row[1]['text'] for t in terms), -row[0]), reverse=True)
    return [i for i, _ in ranked[:limit]]
