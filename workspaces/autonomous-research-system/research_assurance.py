"""Controller-owned study coverage and manuscript voice gates.

Coverage is checked against a pinned plan, never inferred from solver-call counts
or a model's `complete` flag. This is process assurance, not scientific review.
Existing campaigns opt in explicitly; new paper campaigns pin their plan after
pilot, before the controller schedules formal experiments.
"""
import hashlib
import json
import re
import importlib.util
from pathlib import Path
VERSION = 'complete-study-v1'
POLICY = {'version': VERSION, 'enabled': True, 'article_voice': 'standalone_research'}
INSTRUCTION = '完整研究按冻结的研究问题、样本精度依据和必要对照清单验收，不按运行过几个测试或solver_calls验收。DEV/validate/pilot仅作工程和开发证据，不能重标正式实验。pilot结束前提交study_plan角色JSON；控制器在接收pilot后锁定其SHA256，正式实验不能缩减分母。研究方案更新须明确登记，不能追认事前冻结。完整性不足时可做诊断、方法推导和独立工作，不能生成宣称完整研究的最终结果论文。正文按独立学术论文写：直接定义问题、模型、方法、推导及有证据的结果。不以“参考原文”“学位论文提到”组织论述；来源页码、公式核对、调试、版本演进放到研究记录。保留已有工作的正常引用、方法归属、复现参数及实质局限，不把已有方法改称原创。'
PLAN_CONTRACT = 'study_plan: version=complete-study-v1，topic匹配；studies非空列表。每项id、question、sample_rationale、categories、split、key_fields、protocol及input_manifest路径/SHA256；input_manifest的attempts为冻结逐项身份列表，key_fields至少含world_id；results_path为未来实际runs JSON路径，evaluation_path为独立评价记录路径；独立评价含independent_evaluation=true/results_sha256/checked_attempts及实际evidence路径与哈希。raw_record_base可登记原始逐项记录相对路径的基准目录，不改写原始记录。categories须覆盖main_comparison/ablation/robustness/scaling；额外类别由当前任务契约声明。协议stage=experiment且原始input_manifest.split与study.split一致；分割仅TEST/CONFIRM/STRESS/SCALE/CLOSED_LOOP，不能DEV/SCREEN。未冻结的必要研究以pending_design=true及具体missing登记，会阻止论文写作，不能删项冒充完成。'

def enabled(state):
    return state['config'].get('research_assurance', {}).get('enabled') is True

def required_categories(topic):
    return {'main_comparison', 'ablation', 'robustness', 'scaling'}

def load_ref(ref, resolve):
    path = resolve(ref['path'])
    if hashlib.sha256(path.read_bytes()).hexdigest() != ref.get('sha256'):
        raise ValueError('完整研究证据哈希不匹配：' + str(path))
    return json.loads(path.read_text())

def validate_plan(plan, state, resolve):
    if plan.get('version') != VERSION or plan.get('topic') != state['topic']:
        raise ValueError('完整研究计划版本或课题不匹配')
    studies = plan.get('studies', [])
    if not isinstance(studies, list) or not studies:
        raise ValueError('完整研究计划缺少必要研究清单')
    (ids, categories) = (set(), set())
    for study in studies:
        if not study.get('id') or study['id'] in ids:
            raise ValueError('完整研究计划存在缺失或重复study id')
        ids.add(study['id'])
        for field in ('question', 'sample_rationale', 'categories'):
            if not study.get(field):
                raise ValueError('完整研究计划缺少' + field)
        categories.update(study['categories'])
        if study.get('pending_design') is True:
            if not study.get('missing'):
                raise ValueError('未冻结研究必须说明具体缺口')
            continue
        if study.get('split') not in ('TEST', 'CONFIRM', 'STRESS', 'SCALE', 'CLOSED_LOOP'):
            raise ValueError('DEV/SCREEN/工程测试不能替代正式研究')
        fields = study.get('key_fields', [])
        if not isinstance(fields, list) or 'world_id' not in fields or (not study.get('results_path')) or (not study.get('evaluation_path')):
            raise ValueError('完整研究缺逐项身份、结果或独立评价路径')
        protocol = load_ref(study['protocol'], resolve)
        inputs = load_ref(study['input_manifest'], resolve)
        if protocol.get('stage') != 'experiment' or inputs.get('split') != study['split']:
            raise ValueError('原始协议/输入不是相同分割的正式实验，不能将验证数据重标TEST')
        identities(inputs.get('attempts'), fields)
    if not required_categories(state['topic']).issubset(categories):
        raise ValueError('完整研究计划缺必要主对照、消融、稳健性、规模或闭环研究')
    return plan

def identities(rows, fields):
    if not isinstance(rows, list) or not rows:
        raise ValueError('冻结逐项清单为空')
    keys = []
    for row in rows:
        if not isinstance(row, dict) or any((k not in row for k in fields)):
            raise ValueError('逐项研究身份不完整')
        keys.append(tuple((json.dumps(row[k], sort_keys=True) for k in fields)))
    if len(set(keys)) != len(keys):
        raise ValueError('逐项研究身份重复，不能增加独立样本数')
    return keys

def verify_coverage(state, directory, resolve):
    """Read immutable expected denominators independently of submitted results."""
    if not enabled(state):
        return None
    policy = state['config']['research_assurance']
    if not policy.get('plan'):
        raise ValueError('完整研究计划尚未由控制器锁定；小型验证不能准入最终论文')
    plan = validate_plan(load_ref(policy['plan'], resolve), state, resolve)
    manifest = json.loads((Path(directory) / 'artifacts/stages/experiment.json').read_text())
    if manifest.get('status') != 'passed' or manifest.get('complete') is False:
        raise ValueError('正式实验尚未通过，禁止以部分结果完成论文')
    registered = {str(resolve(a['path'])): a['sha256'] for a in manifest.get('artifacts', [])}
    checked = []
    for study in plan['studies']:
        if study.get('pending_design'):
            raise ValueError('必要研究尚未冻结或补齐：' + study['id'] + '；' + study['missing'])
        fields = study['key_fields']
        expected = identities(load_ref(study['input_manifest'], resolve)['attempts'], fields)
        result_path = resolve(study['results_path'])
        evaluation_path = resolve(study['evaluation_path'])
        for path in (result_path, evaluation_path):
            if registered.get(str(path)) != hashlib.sha256(path.read_bytes()).hexdigest():
                raise ValueError('正式结果/独立评价未登记或版本不匹配：' + str(path))
        result = json.loads(result_path.read_text())
        if result.get('synthetic_fixture') is True or result.get('split') != study['split'] or result.get('complete') is False:
            raise ValueError('正式研究结果来源或分割不匹配：' + study['id'])
        for key in ('protocol_sha256', 'input_manifest_sha256'):
            ref_key = 'protocol' if key.startswith('protocol') else 'input_manifest'
            if result.get(key) != study[ref_key]['sha256']:
                raise ValueError('正式结果未绑定冻结协议/输入：' + study['id'])
        for (key, value) in study.get('bindings', {}).items():
            if result.get(key) != value:
                raise ValueError('正式结果源码/资源版本不匹配：' + study['id'])
        runs = result.get('runs')
        if set(identities(runs, fields)) != set(expected):
            raise ValueError('正式研究逐项分母不完整：' + study['id'])
        for row in runs:
            if row.get('status') not in ('succeeded', 'completed', 'timeout', 'crashed', 'invalid', 'invalid_or_crashed', 'failed') or row.get('attempted') is False:
                raise ValueError('仍有未执行、预算截尾或状态未明项：' + study['id'])
            ref = row.get('raw_result') or row.get('receipt')
            if not ref:
                raise ValueError('逐项终态缺真实记录：' + study['id'])
            base = Path(study.get('raw_record_base', result_path.parent))
            load_ref(ref, lambda raw: resolve(str(base / raw) if not Path(raw).is_absolute() else raw))
        evaluation = json.loads(evaluation_path.read_text())
        if evaluation.get('independent_evaluation') is not True or evaluation.get('results_sha256') != registered[str(result_path)] or evaluation.get('checked_attempts') != len(expected):
            raise ValueError('缺少匹配全部尝试的独立评价：' + study['id'])
        if not evaluation.get('evidence'):
            raise ValueError('独立评价缺实际执行证据：' + study['id'])
        for ref in evaluation['evidence']:
            load_ref(ref, resolve)
        checked.append({'id': study['id'], 'attempts': len(expected), 'split': study['split']})
    return {'plan_sha256': policy['plan']['sha256'], 'studies': checked, 'scientific_truth_verified': False}
VOICE_PATTERNS = ['参考原文', '学位论文(?:中)?(?:提到|指出|给出|提出|认为|表明|描述|介绍|采用)', '原(?:文|论文|预印本)[^。\\n]{0,45}第\\s*\\d+\\s*页', '学位论文(?:中|的)?第\\s*\\d+(?:\\.\\d+)*\\s*[章节]', '原文(?:的)?式\\s*[（(]?\\d+', '(?:第一版|第二版|本轮修订|本次修复|调试过程中)']

def voice_issues(path, root=None, seen=None):
    """Follow local TeX includes; bibliography entries are attribution, not prose."""
    path = Path(path).resolve()
    root = Path(root or path.parent).resolve()
    seen = set() if seen is None else seen
    if path in seen:
        return []
    if not path.is_relative_to(root):
        raise ValueError('论文输入超出稿件目录：' + str(path))
    seen.add(path)
    (issues, bibliography) = ([], False)
    for (number, raw) in enumerate(path.read_text().splitlines(), 1):
        line = re.split('(?<!\\\\)%', raw)[0]
        if '\\begin{thebibliography}' in line:
            bibliography = True
        if not bibliography:
            for pattern in VOICE_PATTERNS:
                if re.search(pattern, line):
                    issues.append({'path': str(path), 'line': number, 'text': line.strip()})
                    break
            for included in re.findall('\\\\(?:input|include)\\{([^}]+)\\}', line):
                target = path.parent / included
                if not target.suffix:
                    target = target.with_suffix('.tex')
                issues.extend(voice_issues(target, root, seen))
        if '\\end{thebibliography}' in line:
            bibliography = False
    return issues

def source_bundle_sha256(manuscript):
    root = Path(manuscript).parent
    sources = [p for p in root.rglob('*') if p.is_file() and 'build' not in p.relative_to(root).parts and (p.suffix in ('.tex', '.bib') or p.relative_to(root).parts[0] in ('figures', 'tables'))]
    rows = [(str(p.relative_to(root)), hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(sources)]
    return hashlib.sha256(json.dumps(rows, ensure_ascii=False).encode()).hexdigest()

def verify_tool_review(document, state, directory, resolve):
    """Reuse the topic's existing review gate; never transfer old draft scores."""
    contract = state['config']['research_assurance']['tool_review_contract']
    gate_path = resolve(contract['gate']['path'])
    if hashlib.sha256(gate_path.read_bytes()).hexdigest() != contract['gate']['sha256']:
        raise ValueError('已登记全文评审门槛发生变化，不能默换工具或标准')
    spec = importlib.util.spec_from_file_location('tr002_tool_approval_gate', gate_path)
    gate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gate)
    write = json.loads((Path(directory) / 'artifacts/stages/write.json').read_text())
    manuscript = resolve(next((a['path'] for a in write['artifacts'] if a['role'] == 'manuscript')))
    pdf = resolve(next((a['path'] for a in write['artifacts'] if a['role'] == 'pdf')))
    receipt = load_ref(document['receipt'], resolve)
    review = load_ref(document['review'], resolve)
    issues = load_ref(document['issues'], resolve)
    raw_path = resolve(document['raw_report']['path'])
    if hashlib.sha256(raw_path.read_bytes()).hexdigest() != document['raw_report']['sha256']:
        raise ValueError('评审原始输出哈希不匹配')
    if receipt.get('tool') != contract['tool'] or receipt.get('tool_commit') != contract['commit']:
        raise ValueError('评审工具与已登记工具/源码版本不匹配')
    if receipt.get('source_bundle_sha256') != source_bundle_sha256(manuscript):
        raise ValueError('评审未绑定当前分节源码、引用及图表版本')
    if not review.get('verdict_quote') or review['verdict_quote'] not in raw_path.read_text():
        raise ValueError('工具认可结论无法在原始输出定位')
    outcome = gate.assess(manuscript, pdf, raw_path, receipt, review, issues)
    if not outcome['tool_accepted']:
        raise ValueError('全文评审工具尚未认可当前稿件：' + '；'.join(outcome['reasons']))
    return outcome
import local_extensions as _local_extensions
_local_extensions.apply(globals())
