"""Default, task-adapted observability contract. No execution or new authority.

An agent designs sources and interpretation for its own protocol. The platform
validates that design and renders it; textual rules are not scientific proof.
"""
from pathlib import Path

VERSION = 'adaptive-execution-visibility-v1'
INSTRUCTION = (
    '每次调用都须自行判断本工作项需要展示的进展，复用本系统看板及已有证据，不等用户询问。'
    '先读原任务、有效补充、已有进度设计、原作业回执和日志；接续任务先核对原作业，不重新做已完成工作。'
    '实验开始前按照本轮协议自适应设计工作项、指标名称/单位/分母及依据、观测来源、更新频率、'
    '运行/结束/失败/未知的判定依据，以及未知状态的检查清单和系统处理动作。'
    '训练展示种子、更新、样本或评价计数；批次展示方法/分路及终态；传输展示字节和完整性；'
    '核验展示已检查项、剩余项、原错误和复验结果。按实际任务选用或自行设计，不固定套用这些类型。'
    '长作业在启动前接入控制台或只读采集器，约5秒持续更新；job_runner保留日志、心跳和退出回执。'
    '支持控制台逐行输出ARS_PROGRESS={"at":UTC秒,"simulated":false,"counters":{"自定义指标键":真实整数}}；'
    '指标名称和单位使用observation.metrics登记。计数不是科学验收，心跳/耗时/日志增长不是完成比例。'
    '待核对必须写清缺什么、证据在哪里、系统接下来检查什么、是否真需用户决定。'
    '通常由系统处理原回执、进程、服务器采样和原日志；只有缺少明确授权/必要外部输入才请求用户决定。'
    '监控故障不能重投UNKNOWN或中断健康实验；失败须保留原错误并自动修复、独立复验后接续。'
    '不得修改冻结实验来接监控；优先使用旁路采集。只在本任务Git忽略区存放设计、日志、状态和采集器；'
    '本要求不扩大本调用的文件权限、科学契约、设备授权、模型策略和预算。只读调用保持只读。'
)


def example():
    """Agents replace this example with task-specific sources and rules."""
    return {
        'kind': 'custom',
        'sources': [{'id': 'console', 'kind': 'job_console', 'location': 'job_runner生成的本次作业console.log',
                     'purpose': '改为当前协议中需要采集的具体输出', 'update_interval_seconds': 5}],
        'metrics': [{'key': 'completed_units', 'label': '改为本任务实际工作量', 'unit': '项',
                     'total': None, 'target_basis': '待本轮协议确定；未知不估算百分比'}],
        'state_rules': {'running': '实际作业回执持续更新，并有本轮工作项的输出',
                        'completed': '改为本任务结束所需的真实终态与完整性证据；科学验收另列',
                        'failed': '原命令返回失败或本任务检查报告明确失败，保留原始错误',
                        'unknown': '缺退出回执、采集过期或证据冲突；不猜测服务器停止或完成'},
        'reconciliation': {'owner': 'system', 'checks': ['原命令退出回执', '原作业身份与最新日志', '按本任务协议检查缺失证据'],
                           'action': '核对已有结果，自动修复采集或执行故障，独立复验后接续；UNKNOWN不重投',
                           'requires_user_when': '确实缺少本任务有效授权或不可替代的外部输入时，说明具体缺项'}}


def _text(value, name):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        raise ValueError('观测设计缺少或超长字段：' + name)


def validate(design):
    if not isinstance(design, dict):
        raise ValueError('须根据本任务设计observation：来源、指标、状态依据及系统核对动作')
    _text(design.get('kind'), 'kind')
    sources = design.get('sources')
    if not isinstance(sources, list) or not 1 <= len(sources) <= 50:
        raise ValueError('观测设计需要1至50个具体来源')
    ids = set()
    for row in sources:
        if not isinstance(row, dict):raise ValueError('观测来源须为对象')
        for key in ('id', 'kind', 'location', 'purpose'):_text(row.get(key), key)
        if row['id'] in ids:raise ValueError('观测来源id重复')
        ids.add(row['id'])
        interval = row.get('update_interval_seconds')
        if interval is not None and (type(interval) is not int or not 1 <= interval <= 3600):
            raise ValueError('观测更新间隔须为1至3600秒或null（仅结束时产生的回执）')
    metrics = design.get('metrics')
    if not isinstance(metrics, list) or len(metrics) > 40:raise ValueError('指标须为最多40项的列表；无可计数量可留空')
    keys = set()
    for metric in metrics:
        if not isinstance(metric, dict):raise ValueError('指标须为对象')
        for key in ('key', 'label', 'unit', 'target_basis'):_text(metric.get(key), key)
        if metric['key'] in keys:raise ValueError('指标key重复')
        keys.add(metric['key'])
        total = metric.get('total')
        if total is not None and (type(total) is not int or total <= 0):raise ValueError('指标分母须为正整数或null')
    rules = design.get('state_rules')
    if not isinstance(rules, dict):raise ValueError('缺少本任务的状态判定依据')
    for key in ('running', 'completed', 'failed', 'unknown'):_text(rules.get(key), 'state_rules.' + key)
    check = design.get('reconciliation')
    if not isinstance(check, dict) or check.get('owner') != 'system':raise ValueError('常规状态核对必须由system承担')
    for key in ('action', 'requires_user_when'):_text(check.get(key), 'reconciliation.' + key)
    if not isinstance(check.get('checks'), list) or not 1 <= len(check['checks']) <= 30:raise ValueError('须列出具体核对清单')
    for value in check['checks']:_text(value, 'reconciliation.checks')
    return design


def context(store):
    import execution_observation
    root = store.directory.resolve()
    previous = []
    import time
    for reference in execution_observation.inventory(str(root), int(time.time() // 5)):
        try:
            _, data, console = execution_observation.receipt(root, reference)
            previous.append(dict(receipt=reference, log=str(console.relative_to(root)),
                status=data.get('status'), target=data.get('target'), started_at=data.get('started_at'),
                observed_at=data.get('observed_at') or data.get('finished_at')))
            if len(previous) >= 8:break
        except (OSError, ValueError, TypeError):continue
    return dict(version=VERSION, instruction=INSTRUCTION, previous_job_evidence=previous,
                renderer='平台已有实验看板；设计是JSON数据，不能执行任务提交的HTML或脚本',
                log_protocol='ARS_PROGRESS=<单行JSON，at为UTC秒，simulated为false，counters为实测非负整数>',
                observation_example=example(), module=str(Path(__file__).resolve()))
