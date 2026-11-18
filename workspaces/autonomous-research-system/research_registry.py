"""Create independent, local-only research topics and their first run.

Catalog writes are locked and atomic. A creation key makes retries idempotent.
Only generated private paths are accepted; no model or experiment is started.
"""
import fcntl
import hashlib
import json
from pathlib import Path
import re

import ars
import git_boundary
import model_routing


def _text(data, key, limit, required=False):
    value = data.get(key, '')
    if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
        raise ValueError(f'{key}须为文本，长度不超过{limit}，必填项不能为空')
    return value.strip()


def create(data, repo=None):
    repo = Path(repo or ars.REPO).resolve()
    allowed = {'title','goal','materials','creation_id','backend','model','model_policy','max_calls','max_seconds','task_timeout','max_tokens','submission_target','submission_target_name'}
    if set(data) - allowed:
        raise ValueError('不支持的新课题字段')
    title = _text(data, 'title', 160, True)
    goal = _text(data, 'goal', 10000, True)
    materials = _text(data, 'materials', 10000)
    creation_id = _text(data, 'creation_id', 80, True)
    if not re.fullmatch(r'[A-Za-z0-9_-]{8,80}', creation_id):
        raise ValueError('创建请求编号无效')
    options = {k: data[k] for k in ('backend','model','model_policy','max_calls','max_seconds','task_timeout','max_tokens','submission_target','submission_target_name') if k in data}
    if 'model_policy' in options:
        options['model_policy']=model_routing.normalize(options['model_policy'])
        if options['model_policy']['task_overrides']:
            raise ValueError('新课题还没有可指定模型的具体工作项')
    if options.get('backend','codex') not in ('codex','mock'):
        raise ValueError('未知执行器')
    for key, maximum in [('max_calls',1000),('max_seconds',604800),('task_timeout',7200),('max_tokens',None)]:
        value=options.get(key,0)
        if type(value) is not int or value < 0 or (maximum is not None and value > maximum):
            raise ValueError('预算参数超出范围：'+key)
    for key in ('model','submission_target','submission_target_name'):
        if key in options and not isinstance(options[key],str):
            raise ValueError('模型与投稿目标须为文本')
    ars.resolve_submission_target(options.get('submission_target','none'),options.get('submission_target_name',''),repo)
    catalog = repo / 'workspaces/topics.json'
    catalog.parent.mkdir(parents=True,exist_ok=True)
    lock = catalog.with_name('.topics.lock')
    if catalog.is_symlink() or lock.is_symlink() or catalog.parent.resolve() != repo/'workspaces':
        raise ValueError('课题登记表路径不安全')
    with lock.open('a+') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX)
        original = json.loads(catalog.read_text()) if catalog.exists() else {'topics':[]}
        entries = original.get('topics')
        if not isinstance(entries,list):
            raise ValueError('本地课题登记表格式无效')
        previous = next((r for r in entries if r.get('creation_id')==creation_id),None)
        # Same key must not silently reuse a different request.
        payload = dict(title=title,goal=goal,materials=materials,options=options)
        digest = hashlib.sha256(ars.dump(payload).encode()).hexdigest()
        if previous and previous.get('creation_digest') != digest:
            raise ValueError('创建请求编号已用于其他内容，请重新创建')
        if previous and previous.get('initial_run'):
            return {'key':previous['initial_run'],'topic':previous,'duplicate':True,'started':False}
        if previous:
            entry = previous
        else:
            number = max([int(r['id'][3:]) for r in entries if re.fullmatch(r'RS-\d+',str(r.get('id','')))]+[0])+1
            topic_id=f'RS-{number:03d}'
            entry=dict(id=topic_id,title=title,workspace='workspaces/research-'+ars.uid()[:16],
                docs='docs/topics/'+topic_id.lower()+'-'+ars.uid()[:12],paper_reserved='papers/'+topic_id.lower()+'-'+ars.uid()[:12],input=None,
                created_at=ars.now(),creation_id=creation_id,creation_digest=digest,registration_status='initializing')
        workspace=repo/entry['workspace']
        # Validate every reserved research path before writing task content.
        boundary=git_boundary.validate_registration(repo,entry,workspace/'runs/ars/initial')
        if not previous:
            workspace.mkdir(parents=True,exist_ok=False,mode=0o700)
            (repo/entry['docs']).mkdir(parents=True,exist_ok=True,mode=0o700)
            (workspace/'README.md').write_text(f"# {title}\n\n课题编号：{entry['id']}\n\n## 研究目标\n\n{goal}\n\n## 初始资料\n\n启动前完整读取本目录 initial-materials.md。资料线索须核对来源；不得据其他课题推定资源授权或结论。\n\n研究内容全部只留本地Git忽略区，不上传。\n")
            (workspace/'initial-materials.md').write_text(materials or '尚未提供初始资料；先依据目标核对资料需求。\n')
            entries.append(entry)
            ars.atomic_json(catalog,original)
        try:
            run_name='initial-'+creation_id[:48]
            directory=workspace/'runs/ars'/run_name
            if (directory/'state.sqlite3').is_file():
                # A process may exit after committing the run but before
                # recording its pointer in the catalog. Adopt that same run.
                existing=ars.Store(directory)
                try:
                    if existing.state()['topic'] != entry['id'] or existing.state()['goal'] != goal:
                        raise ValueError('原首次运行身份不匹配，保留现场')
                finally:existing.close()
            else:
                directory=ars.create_campaign(entry['id'],goal,repo=repo,name=run_name,workflow='readonly',**options)
            store=ars.Store(directory)
            try:
                with store.tx():
                    store.event('topic.registered',{'topic':entry['id'],'title':title,'git_boundary':boundary})
                    store.memory('decision','新建独立课题：启动前读取本课题README与initial-materials.md，依据研究目标形成研究计划；资料、证据和资源授权独立核对。',status='user_instruction')
            finally:store.close()
        except Exception as exc:
            entry['registration_status']='creation_failed'
            ars.atomic_json(catalog,original)
            raise ValueError('课题已登记，但首次运行创建失败；保留本地内容，使用同一请求重试。'+str(exc)) from exc
        entry.update(registration_status='ready',initial_run=entry['id']+'/'+directory.name)
        ars.atomic_json(catalog,original)
        return {'key':entry['initial_run'],'topic':entry,'duplicate':False,'started':False}
