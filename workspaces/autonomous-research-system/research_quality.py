"""Frozen study coverage and manuscript admission, not scientific truth certification."""
import datetime as dt
import hashlib
import json
from pathlib import Path

VERSION = 'research-completion-v1'
COMPONENTS = {'baselines', 'ablations', 'sensitivity', 'replication', 'generalization'}
INSTRUCTION = '''工程验收、DEV和小先导不能充当完整正式实验。正式TEST前准备experiment_design：version=research-completion-v1、topic/run_id、study_kind=formal_experiment、mode、protocol_sha256、questions、sample_size、components、groups、planned_runs。questions每项含id/estimand/primary_endpoint/claim_scope。sample_size含independent_unit、planned_n、unit_ids、rationale及DEV证据dev_evidence(path/sha256)。components含baselines/ablations/sensitivity/replication/generalization，每项applicable/group_ids；不适用给scope_reason，基线/重复不能免。groups含id/purpose。planned_runs每项run_id/group_id/independent_id/method/split=TEST/minimum_work及code_sha256/config_sha256与匹配的code_ref/config_ref(path/sha256，真实代码包/源码身份清单与配置文件)；训练模式minimum_work须给source_updates/optimizer_calls，数量由学习曲线冻结。
在执行TEST前调用主仓库research_quality.py freeze --campaign 运行目录 --design 设计JSON --protocol 正式协议JSON，登记真实控制器冻结时间。此命令不运行实验或模型。不能事后登记已见TEST。结果runs逐项对应同名身份和版本，含work、execution_receipt(path/sha256)、evidence(path/sha256)、metrics，失败附reason/failure_class。真实计算回执类别comparison；传输、工程验收、pilot和未知状态不能代替。不能只留下少数验证记录或删除未执行组。数值失败仅在设计预定且真实执行、证据齐全时作为失败结果。
experiment_completion含version/status=complete、design_sha256/protocol_sha256/results_sha256、remaining_run_ids=[]，以及adequacy.precision/learning_health/claim_coverage，每项status=met及evidence(path/sha256)。非训练learning_health可有理由not_applicable。精度或学习健康未满足时继续有效预注册研究，不得勾选完成冒充证据。analyze另交analysis_provenance，绑定experiment_completion_sha256/results_sha256及recomputation_evidence。write和终审重新核对正式实验及分析版本。
正文写成独立学术论文：研究问题、模型、方法、理论、实验、结果和结论自洽；不频繁叙述“参考原文”“学位论文提到”，不把页码、路径、哈希、调用/故障/内部评分等审计内容放正文。必要学术引用、假设、研究范围和局限须保留；不隐去来源或将旧结果冒充新实验。溯源记录单独保留。'''


def enabled(config):
    return (config.get('workflow') == 'paper'
            and config.get('research_quality', {}).get('version') == VERSION
            and config.get('delivery_contract') != 'legacy-fixture')


def timestamp(value):
    try:
        parsed = dt.datetime.fromisoformat(value)
        if parsed.tzinfo is not None:
            return parsed
    except (TypeError, ValueError):
        pass
    raise ValueError('实验完整性清单需要带时区的时间')


class Reader:
    def __init__(self, resolve):
        self.resolve, self.cache = resolve, {}

    def bound(self, ref, structured=False):
        path = self.resolve(ref['path'])
        key = (str(path), ref.get('sha256'))
        if key not in self.cache:
            body = path.read_bytes()
            if not body or hashlib.sha256(body).hexdigest() != ref.get('sha256'):
                raise ValueError('实验完整性证据缺失或哈希不匹配：' + str(path))
            self.cache[key] = body
        if structured:
            data = json.loads(self.cache[key])
            if not isinstance(data, dict):
                raise ValueError('实验完整性证据须为JSON对象')
            return data
        return self.cache[key]

    def evidence(self, refs):
        if not isinstance(refs, list) or not refs:
            raise ValueError('实验完整性判断缺少实际证据')
        for ref in refs:
            self.bound(ref)


def validate_design(design, state):
    if (design.get('version') != VERSION or design.get('study_kind') != 'formal_experiment'
            or design.get('topic') != state['topic'] or design.get('run_id') != state['id']):
        raise ValueError('正式实验设计的版本/课题/运行/实验层次不匹配')
    expected_mode = state['config']['research_quality'].get('study_mode')
    if expected_mode and design.get('mode') != expected_mode:
        raise ValueError('正式实验不能改写研究类型以绕过学习充分性要求')
    questions = design.get('questions', [])
    if not isinstance(questions, list) or not questions or not all(
            all(row.get(key) for key in ('id', 'estimand', 'primary_endpoint', 'claim_scope'))
            for row in questions):
        raise ValueError('正式实验缺研究问题、估计对象或主终点')
    sample = design.get('sample_size', {})
    minimum = state['config']['research_quality'].get('minimum_independent_units', 2)
    n, units = sample.get('planned_n'), sample.get('unit_ids', [])
    if (type(n) is not int or n < minimum or not sample.get('independent_unit')
            or not sample.get('rationale') or len(units) != n or len(set(units)) != n
            or not sample.get('dev_evidence')):
        raise ValueError('样本量缺充分性依据或独立单位，验证回合不能替代独立重复')
    groups = design.get('groups', [])
    if (not groups or len({row.get('id') for row in groups}) != len(groups)
            or not all(row.get('id') and row.get('purpose') for row in groups)):
        raise ValueError('实验组身份/目的缺失或重复')
    ids = {row['id'] for row in groups}
    components = design.get('components', {})
    if not COMPONENTS.issubset(components):
        raise ValueError('正式实验缺必要对照/消融/敏感性/复验/泛化覆盖')
    for key in COMPONENTS:
        row = components[key]
        if row.get('applicable') is True:
            if not row.get('group_ids') or not set(row['group_ids']).issubset(ids):
                raise ValueError('实验组件未对应实际计划组：' + key)
        elif row.get('applicable') is not False or key in ('baselines', 'replication') or not row.get('scope_reason'):
            raise ValueError('不能无依据免除实验组件：' + key)
    runs = design.get('planned_runs', [])
    if (not runs or len({row.get('run_id') for row in runs}) != len(runs)
            or not all(row.get('run_id') and row.get('group_id') in ids
                and row.get('independent_id') in units and row.get('method')
                and row.get('split') == 'TEST' and row.get('minimum_work')
        and row.get('code_sha256') and row.get('config_sha256')
        and row.get('code_ref') and row.get('config_ref') for row in runs)):
        raise ValueError('计划须逐运行列明组/独立单位/方法/TEST/工作量/版本')
    for row in runs:
        if any(row[key + '_sha256'] != row[key + '_ref'].get('sha256') for key in ('code', 'config')):
            raise ValueError('代码与配置身份必须绑定真实来源文件')
        work = row['minimum_work']
        if any(type(value) is not int or value < 0 for value in work.values()) or not any(work.values()):
            raise ValueError('实验工作量下限不能是空值、布尔值或全零')
        if design.get('mode') == 'training' and not all(work.get(key, 0) > 1 for key in ('source_updates', 'optimizer_calls')):
            raise ValueError('不能用一次来源更新或一次训练冒充充分学习')
    for group in ids:
        if {row['independent_id'] for row in runs if row['group_id'] == group} != set(units):
            raise ValueError('实验组缺预定独立重复：' + group)


def artifact(directory, phase, role):
    manifest = json.loads((Path(directory) / 'artifacts/stages' / (phase + '.json')).read_text())
    if manifest.get('status') != 'passed':
        raise ValueError('实验阶段尚未通过，不能进入论文写作')
    rows = [row for row in manifest['artifacts'] if row['role'] == role]
    if len(rows) != 1:
        raise ValueError('阶段缺少唯一完整性产物：' + role)
    return rows[0]


def verify_experiment(state, directory, resolve, db):
    read = Reader(resolve)
    refs = {role: artifact(directory, 'experiment', role) for role in
            ('protocol', 'results', 'experiment_design', 'experiment_completion')}
    read.bound(refs['protocol'], True)
    design = read.bound(refs['experiment_design'], True)
    results = read.bound(refs['results'], True)
    completion = read.bound(refs['experiment_completion'], True)
    validate_design(design, state)
    if design.get('protocol_sha256') != refs['protocol']['sha256']:
        raise ValueError('实验设计未绑定当前正式协议')
    registration = next((json.loads(row[0]) for row in db.execute(
        "SELECT payload FROM events WHERE type='experiment.design_frozen' ORDER BY seq DESC")
        if json.loads(row[0]).get('design_sha256') == refs['experiment_design']['sha256']
        and json.loads(row[0]).get('protocol_sha256') == refs['protocol']['sha256']), None)
    if not registration:
        raise ValueError('正式TEST前未在控制器冻结设计，不能事后补登记已见结果')
    frozen_at = timestamp(registration['registered_at'])
    read.evidence(design['sample_size']['dev_evidence'])
    for row in design['planned_runs']:
        read.bound(row['code_ref'])
        read.bound(row['config_ref'])
    if (completion.get('version') != VERSION or completion.get('status') != 'complete'
            or completion.get('remaining_run_ids') != []
            or any(completion.get(key + '_sha256') != refs[role]['sha256'] for key, role in
                   [('design', 'experiment_design'), ('protocol', 'protocol'), ('results', 'results')])):
        raise ValueError('实验仍不完整或审计未绑定当前设计/结果')
    actual = results.get('runs', [])
    by_id = {row.get('run_id'): row for row in actual}
    planned = {row['run_id']: row for row in design['planned_runs']}
    if len(by_id) != len(actual) or set(by_id) != set(planned):
        raise ValueError('正式实验逐运行分母与冻结计划不一致；不能删组或只保留几条验证记录')
    for key, plan in planned.items():
        row = by_id[key]
        for field in ('group_id', 'independent_id', 'method', 'split', 'code_sha256', 'config_sha256'):
            if row.get(field) != plan[field]:
                raise ValueError('运行身份/版本不匹配：' + key + '/' + field)
        receipt = read.bound(row['execution_receipt'], True)
        target = state['config']['research_quality'].get('experiment_target')
        if (receipt.get('experiment_kind') != 'comparison' or receipt.get('simulated') is not False
                or (target and receipt.get('target') != target)
                or receipt.get('status') not in ('succeeded', 'failed')
                or timestamp(receipt['started_at']) < frozen_at or not receipt.get('finished_at')):
            raise ValueError('工程/先导/本机/未知或冻结前回执不能替代正式实验：' + key)
        argv = receipt.get('argv', [])
        if not argv or Path(str(argv[0])).name in {'scp', 'rsync', 'cat', 'ls', 'stat', 'sha256sum'}:
            raise ValueError('文件传输/检查回执不能代替真实计算：' + key)
        read.bound({'path': receipt['log_path'], 'sha256': receipt['log_sha256']})
        read.evidence(row.get('evidence'))
        if row.get('status') == 'succeeded':
            if receipt.get('status') != 'succeeded' or receipt.get('exit_code') != 0:
                raise ValueError('成功实验缺真实成功计算回执：' + key)
        elif (row.get('status') not in design.get('allowed_failure_outcomes', [])
                or row.get('failure_class') != 'scientific_outcome' or not row.get('reason')):
            raise ValueError('未执行、基础设施故障或未预定失败不能冒充完成：' + key)
        work = row.get('work', {})
        if any(type(work.get(name)) is not int or work[name] < minimum
               for name, minimum in plan['minimum_work'].items()):
            raise ValueError('实际学习/运行工作量未达冻结计划：' + key)
    for key in ('precision', 'learning_health', 'claim_coverage'):
        item = completion.get('adequacy', {}).get(key, {})
        if (item.get('status') == 'not_applicable' and key == 'learning_health'
                and design.get('mode') != 'training' and item.get('reason')):
            continue
        if item.get('status') != 'met':
            raise ValueError('实验充分性仍未满足：' + key)
        read.evidence(item.get('evidence'))
    return {'planned_runs': len(planned), 'completed_runs': len(actual),
            'independent_units': design['sample_size']['planned_n'],
            'completion_sha256': refs['experiment_completion']['sha256'],
            'results_sha256': refs['results']['sha256'], 'scientific_truth_verified': False}


def verify_analysis(state, directory, resolve, db):
    summary = verify_experiment(state, directory, resolve, db)
    read = Reader(resolve)
    audit = read.bound(artifact(directory, 'analyze', 'analysis_provenance'), True)
    if (audit.get('experiment_completion_sha256') != summary['completion_sha256']
            or audit.get('results_sha256') != summary['results_sha256']):
        raise ValueError('分析未绑定最新完整正式实验，不能拿旧验证图表写新论文')
    read.evidence(audit.get('recomputation_evidence'))
    return summary


def freeze(directory, design_path, protocol_path):
    import ars
    import paper_workflow
    store = ars.Store(directory)
    try:
        state = store.state()
        if not enabled(state['config']) or state['status'] != 'RUNNING' or not any(
                row['status'] == 'RUNNING' and row['phase'] in ('pilot', 'experiment') for row in store.tasks()):
            raise ValueError('仅正在运行且已授权的先导/正式阶段可登记设计')
        resolve = lambda raw: paper_workflow._artifact_path(raw, state)
        design_path, protocol_path = resolve(str(design_path)), resolve(str(protocol_path))
        design_body, protocol_body = design_path.read_bytes(), protocol_path.read_bytes()
        design = json.loads(design_body)
        validate_design(design, state)
        design_sha = hashlib.sha256(design_body).hexdigest()
        protocol_sha = hashlib.sha256(protocol_body).hexdigest()
        if design.get('protocol_sha256') != protocol_sha:
            raise ValueError('设计的协议版本不匹配')
        read = Reader(resolve)
        read.evidence(design['sample_size']['dev_evidence'])
        for row in design['planned_runs']:
            read.bound(row['code_ref']); read.bound(row['config_ref'])
        with store.tx():
            if store.state()['status'] != 'RUNNING':
                raise ValueError('运行状态已改变，不登记新实验')
            previous = next((json.loads(row[0]) for row in store.db.execute(
                "SELECT payload FROM events WHERE type='experiment.design_frozen'")
                if json.loads(row[0]).get('design_sha256') == design_sha), None)
            if previous:
                return previous
            receipt = {'design_sha256': design_sha, 'protocol_sha256': protocol_sha,
                       'registered_at': ars.now(), 'planned_runs': len(design['planned_runs'])}
            frozen = store.directory / 'artifacts/frozen-experiments' / design_sha
            frozen.mkdir(parents=True, exist_ok=False)
            (frozen / 'design.json').write_bytes(design_body)
            (frozen / 'protocol.json').write_bytes(protocol_body)
            ars.atomic_json(frozen / 'registration.json', receipt)
            store.event('experiment.design_frozen', receipt)
        return receipt
    finally:
        store.close()


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['freeze'])
    parser.add_argument('--campaign', required=True)
    parser.add_argument('--design', required=True)
    parser.add_argument('--protocol', required=True)
    args = parser.parse_args()
    print(json.dumps(freeze(args.campaign, args.design, args.protocol), ensure_ascii=False))
