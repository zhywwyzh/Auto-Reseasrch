"""Discover generated research outputs per registered topic and run manifest.

Downloads bind the run, manifest entry and SHA256. Private inputs and whole run
directories are never served. Task adapters are local extensions.
"""
import hashlib
import json
import math
from html import escape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlencode, urlsplit, unquote

def allowed_file(repo, path):
    return False
PUBLIC_ROLES = {'write': {'manuscript', 'pdf', 'web_reader', 'rendered_page', 'figure', 'figure_asset', 'change_log', 'construction_supplement'}, 'paper_review': {'manuscript', 'pdf', 'web_reader', 'review', 'scorecard', 'reproducibility', 'benchmark_index', 'claim_evidence', 'AI_use_record', 'rendered_page', 'figure', 'numeric_table', 'web_report', 'issue_closure', 'verification', 'source_recheck', 'official_policy_check'}, 'analyze': {'analysis_record', 'analysis_source', 'claim_evidence', 'figure', 'assumption_sensitivity', 'numeric_table'}, 'pilot': {'results'}, 'experiment': {'results'}}
SUFFIXES = {'.html', '.md', '.json', '.tex', '.pdf', '.svg', '.png', '.csv'}
PRIVATE = {'.venv', 'datasets', 'private', 'thesis-reference', 'operations', 'executor', 'telemetry'}

def _json(path):
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError, TypeError):
        return {}

def _topic(repo, state):
    return next((row for row in _json(repo / 'workspaces/topics.json').get('topics', []) if row['id'] == state['topic']), None)

def run_directory(repo, state):
    repo = Path(repo).resolve()
    topic = _topic(repo, state)
    if not topic or Path(state['id']).name != state['id'] or state['id'] in ('.', '..'):
        return None
    workspace = (repo / topic['workspace']).resolve()
    if not workspace.is_relative_to(repo):
        return None
    directory = workspace / 'runs/ars' / state['id']
    if directory.is_symlink() or not directory.resolve().is_relative_to(workspace):
        return None
    return directory

def artifacts(repo, state):
    """Inventory identities; hash actual bytes when shown or downloaded."""
    repo = Path(repo).resolve()
    directory = run_directory(repo, state)
    if directory is None:
        return []
    topic = _topic(repo, state)
    roots = [(directory / 'artifacts').resolve()]
    if not roots[0].is_relative_to(directory.resolve()):
        return []
    if topic.get('paper_reserved'):
        root = (repo / topic['paper_reserved']).resolve()
        if root.is_relative_to(repo):
            roots.append(root)
    entries = []
    for (stage, roles) in PUBLIC_ROLES.items():
        manifest_path = directory / 'artifacts/stages' / (stage + '.json')
        if manifest_path.is_symlink() or not manifest_path.resolve().is_relative_to(roots[0]):
            continue
        manifest = _json(manifest_path)
        if manifest.get('topic') != state['topic'] or manifest.get('stage') != stage or manifest.get('status') != 'passed':
            continue
        items = manifest.get('artifacts', [])
        if not isinstance(items, list):
            continue
        for (index, item) in enumerate(items):
            if not isinstance(item, dict):
                continue
            try:
                path = Path(item['path'])
                path = (repo / path).resolve() if not path.is_absolute() else path.resolve()
                reader_asset = stage == 'write' and item['role'] == 'supporting_evidence' and (path.suffix.lower() in {'.svg', '.png'})
                if item['role'] not in roles and (not reader_asset) or path.suffix.lower() not in SUFFIXES or PRIVATE.intersection(path.parts) or (not any((path.is_relative_to(root) for root in roots))):
                    continue
                entries.append({**item, 'path': path, 'stage': stage, 'index': index})
            except (KeyError, ValueError, TypeError):
                continue
    reader_dirs = {entry['path'].parent for entry in entries if entry['role'] == 'web_reader'}
    return [entry for entry in entries if entry['role'] != 'supporting_evidence' or entry['path'].parent in reader_dirs]

def verified(entry):
    try:
        return entry['path'].is_file() and entry['path'].stat().st_size > 0 and (hashlib.sha256(entry['path'].read_bytes()).hexdigest() == entry['sha256'])
    except (OSError, KeyError):
        return False

def _latest(entries, role):
    return next((entry for entry in reversed(entries) if entry['role'] == role), None)

def _score(entry, entries):
    if not entry or not verified(entry):
        return None
    data = _json(entry['path'])
    (manuscript, pdf) = (_latest(entries, 'manuscript'), _latest(entries, 'pdf'))
    overall = data.get('overall')
    if not manuscript or not verified(manuscript) or data.get('manuscript_sha256') != manuscript['sha256'] or (data.get('pdf_sha256') and (not pdf or not verified(pdf) or data['pdf_sha256'] != pdf['sha256'])) or (data.get('score_kind') != 'internal_draft_review') or (data.get('not_peer_review') is not True) or (type(overall) not in (int, float)) or (not math.isfinite(overall)) or (not 1 <= overall <= 10):
        return None
    return data

def artifact_bytes(repo, state, stage, index, digest):
    """Resolve a registered output; clients cannot supply filesystem paths."""
    entries = artifacts(repo, state)
    entry = next((row for row in entries if row['stage'] == stage and row['index'] == index), None)
    if not entry or entry.get('sha256') != digest or (not verified(entry)):
        raise ValueError('产物不存在、未获准展示或版本校验失败')
    if entry['role'] == 'scorecard' and _score(entry, entries) is None:
        raise ValueError('评分未绑定当前稿件版本，暂不提供下载')
    body = entry['path'].read_bytes()
    if hashlib.sha256(body).hexdigest() != digest:
        raise ValueError('产物读取期间已变更，请刷新')
    return (entry, body)

def _url(state, entry, download=False):
    return '/api/agent/artifact?' + urlencode({'key': state['topic'] + '/' + state['id'], 'stage': entry['stage'], 'index': entry['index'], 'sha256': entry['sha256'], **({'download': '1'} if download else {})})

def reader_bytes(repo, state, entry, body):
    """Resolve reader dependencies through the same manifest and hash boundary.

    Stored files remain byte-for-byte unchanged. Unregistered local links lose
    their navigation target rather than exposing run directories or inputs.
    """
    registered = {row['path']: row for row in artifacts(repo, state) if verified(row)}

    class Reader(HTMLParser):

        def __init__(self):
            super().__init__(convert_charrefs=False)
            self.parts = []

        def tag(self, tag, attrs, close):
            rewritten = []
            for (key, value) in attrs:
                if key in ('href', 'src') and value and (not value.startswith('#')):
                    url = urlsplit(value)
                    if not url.scheme and (not url.netloc):
                        target = (Path(repo) / unquote(url.path).lstrip('/') if url.path.startswith('/') else entry['path'].parent / unquote(url.path)).resolve()
                        dependency = registered.get(target)
                        if not dependency or (dependency['role'] == 'scorecard' and _score(dependency, list(registered.values())) is None):
                            continue
                        value = _url(state, dependency) + ('#' + url.fragment if url.fragment else '')
                rewritten.append(' ' + key + ('="' + escape(value, quote=True) + '"' if value is not None else ''))
            self.parts.append('<' + tag + ''.join(rewritten) + close)

        def handle_starttag(self, tag, attrs):
            self.tag(tag, attrs, '>')

        def handle_startendtag(self, tag, attrs):
            self.tag(tag, attrs, '/>')

        def handle_endtag(self, tag):
            self.parts.append('</' + tag + '>')

        def handle_data(self, data):
            self.parts.append(data)

        def handle_entityref(self, name):
            self.parts.append('&' + name + ';')

        def handle_charref(self, name):
            self.parts.append('&#' + name + ';')

        def handle_comment(self, data):
            self.parts.append('<!--' + data + '-->')

        def handle_decl(self, decl):
            self.parts.append('<!' + decl + '>')
    reader = Reader()
    reader.feed(body.decode('utf-8'))
    reader.close()
    return ''.join(reader.parts).encode('utf-8')

def _bound_review(review, manuscript, pdf):
    return bool(manuscript and pdf and verified(manuscript) and verified(pdf) and (review.get('manuscript_sha256') == manuscript['sha256']) and (review.get('pdf_sha256') == pdf['sha256']))

def describe(repo, state):
    entries = artifacts(repo, state)
    if not entries:
        return None
    (good, warnings) = ([], [])
    for entry in entries:
        if verified(entry):
            good.append(entry)
        else:
            warnings.append(entry['stage'] + '/' + entry['role'] + '：文件缺失或哈希不一致，链接已隐藏。')
    (manuscript, pdf) = (_latest(good, 'manuscript'), _latest(good, 'pdf'))
    review_entry = _latest(good, 'review')
    review = _json(review_entry['path']) if review_entry else {}
    bound_review = _bound_review(review, manuscript, pdf)
    score_entry = _latest(good, 'scorecard')
    score = _score(score_entry, entries)
    if score_entry and score is None:
        warnings.append('内部评分尚未绑定当前稿件版本，分数及评分链接已隐藏。')
    links = []
    labels = {'pdf': '阅读论文 PDF', 'manuscript': 'LaTeX 正文源码', 'web_reader': '中文初稿网页', 'scorecard': '内部评分与问题清单', 'review': '全文终审记录', 'claim_evidence': '论文主张与证据', 'web_report': '全文复评与交付报告', 'issue_closure': '修订意见处理', 'verification': '交付核验记录', 'change_log': '全文修改记录', 'assumption_sensitivity': '研究假设敏感性', 'analysis_record': '结果分析'}
    revision = state.get('config', {}).get('research_contract') == 'artifact-revision-v1'
    if revision:
        labels['web_reader'] = '阅读本轮修订全文'
    for role in ('web_reader', 'pdf', 'manuscript', 'web_report', 'scorecard', 'review', 'issue_closure', 'verification', 'change_log', 'analysis_record', 'claim_evidence', 'assumption_sensitivity'):
        entry = _latest(good, role)
        if not entry or (role == 'scorecard' and score is None):
            continue
        links.append({'label': labels[role], 'url': _url(state, entry), 'sha256': entry['sha256']})
        if role == 'pdf':
            links.append({'label': '下载论文 PDF', 'url': _url(state, entry, True), 'sha256': entry['sha256']})
    for entry in good:
        if entry['role'] == 'results':
            links.append({'label': '正式对照结果' if entry['stage'] == 'experiment' else '先导诊断结果', 'url': _url(state, entry), 'sha256': entry['sha256']})
    figures = []
    for entry in good:
        if entry['role'] == 'figure' and entry['path'].suffix.lower() == '.png':
            if entry['path'].name not in {row['label'] for row in figures}:
                figures.append({'label': entry['path'].name, 'url': _url(state, entry), 'sha256': entry['sha256']})
    pending = []
    for issue in (score or review).get('issues', review.get('critical_issues', [])):
        if isinstance(issue, dict) and '已修复' not in str(issue.get('severity', '')):
            text = issue.get('problem') or issue.get('claim') or issue.get('issue_id')
            if text:
                pending.append(str(text))
        elif isinstance(issue, str):
            pending.append(issue)
    findings = []
    for phase in ('analyze', 'experiment', 'pilot'):
        task = next((task for task in reversed(state.get('tasks', [])) if task['phase'] == phase and task['status'] == 'COMPLETED'), None)
        if task and task.get('summary'):
            findings.append({'stage': phase, 'text': task['summary']})
            break
    complete = bool(manuscript and pdf and score and (review.get('verdict') == 'accept') and (review.get('full_manuscript_read') is True) and (review.get('blocking_issues') == []))
    revision_complete = bool(revision and state['status'] == 'COMPLETED' and bound_review and (review.get('full_manuscript_read') is True) and all((any((t.get('phase') == phase and t.get('status') == 'COMPLETED' for t in state.get('tasks', []))) for phase in ('write', 'paper_review'))))
    assessment = None
    rubric = review.get('rubric')
    if bound_review and isinstance(review.get('dimensions'), list) and all((isinstance(row, dict) for row in review['dimensions'])) and isinstance(rubric, dict) and rubric.get('scale'):
        assessment = {key: review.get(key) for key in ('dimensions', 'overall', 'overall_reason', 'reviewer')}
        assessment['scale'] = rubric['scale']
    return {'label': '本轮修订稿与全文复评已完成' if revision_complete else '初稿与内部评分已生成' if complete else '初稿已生成，审查或评分待完成' if manuscript and pdf else '阶段结果已生成，完整初稿待完成', 'execution_label': '本轮执行已结束' if state['status'] == 'COMPLETED' else '本轮执行尚未结束', 'summary': (review.get('readiness', {}).get('bounded_revision_deliverable') if revision_complete else None) or review.get('scope') or '根据本次运行的已登记产物自动展示，见下方结果与文件。', 'scope': '流程完成、内部评分和科学贡献分别记录；本界面不将内部审查通过认定为科学成功或可投稿。', 'pending': pending, 'submission_ready': False, 'scientific_truth_verified': False, 'links': links, 'figures': figures, 'findings': findings, 'warnings': warnings, 'score': {key: score.get(key) for key in ('overall', 'dimensions', 'overall_reason', 'rubric_version', 'model', 'manuscript_version', 'evaluation_scope', 'excluded_dimensions', 'not_comparable_to_prior_overall')} if score else None, 'review_assessment': assessment, 'complete_artifacts': complete or revision_complete, 'source_at': state.get('updated_at'), 'source_note': '依据：本运行各阶段产物清单与文件 SHA256；状态更新时间 '}
import local_extensions as _local_extensions
_local_extensions.apply(globals())
