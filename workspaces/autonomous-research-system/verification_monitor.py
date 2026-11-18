"""Live verification records; observing a check never admits science or retries it."""
import argparse
import contextlib
import datetime as dt
import fcntl
import hashlib
import json
from pathlib import Path
import re
import threading
import time
import uuid

import execution_observation as execution
from experiment_progress import load, stamp
from experiment_monitor import write

VERSION='verification-tracking-v1'
STATES={'pending','running','passed','failed','unknown','skipped'}
INSTRUCTION=(
    '核验也是必须展示的工作，不得只写“核验中”。对来源、实验完整性、归档、数值复算、代码、稿件等每次核验，'
    '先用verification_monitor.py plan登记核验对象及版本、范围、逐项检查名称和通过依据；'
    '运行中用update持续发布当前检查项、已查数量/真实分母、原始错误、证据位置和下一步。'
    '长核验由检查器/旁路采集器主动更新，也可在job_runner控制台逐行输出ARS_CHECK=<JSON>，'
    '字段id/label/status/criterion/detail/evidence/next_action，可选completed/total/unit；'
    'status为pending/running/passed/failed/unknown/skipped，passed必须带具体证据。'
    '沿用本任务原核验门槛，不为展示额外添加科学要求；执行者报告、命令退出码和控制器验收分别展示。'
    '修复后创建新一次核验，保留旧失败；过期采集不伪造进度。只读调用保持只读，由控制器记录其验收。'
    '全部核验记录只写本任务Git忽略区，不重投UNKNOWN、不扩大授权或预算。')


def text(value,name):
    if not isinstance(value,str) or not value.strip() or len(value)>3000:raise ValueError('核验缺少或超长字段：'+name)
    return execution.redact(value)


def folder(root,session):
    if not isinstance(session,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',session):raise ValueError('无效核验记录编号')
    return execution.safe(root,Path('artifacts/telemetry/verifications')/session)


def context(store,task):
    return dict(version=VERSION,module=str(Path(__file__).resolve()),directory=str(store.directory),
        operation_id=task.get('operation_id'),instruction=INSTRUCTION,
        commands={'plan':'python3 <module> plan --directory <directory> --operation <operation_id> --input <plan.json>',
                  'update':'python3 <module> update --directory <directory> --session <返回的session> --input <update.json>'},
        plan_example=dict(title='按本任务填写具体核验',object='填写正在核验的对象及版本/哈希',scope='填写此次核验的实际范围',
            checks=[dict(id='check-one',label='填写具体检查项',criterion='填写原有通过依据')]),
        update_example=dict(summary='填写当前动作',next_action='填写下一步',checks=[dict(id='check-one',status='running',
            detail='填写实际已检查情况',evidence='填写原日志/检查结果位置或明确尚未产生',completed=2,total=None,unit='项')]))


def plan(store,operation,design,authority='executor_report'):
    import git_boundary
    git_boundary.validate_state(store.state(),store.directory)
    op=store.operation(operation)
    if not op:raise ValueError('核验必须属于本任务已有调用')
    data={k:text(design.get(k),k) for k in ('title','object','scope')}
    checks=design.get('checks')
    if not isinstance(checks,list) or not 1<=len(checks)<=100:raise ValueError('核验需要1至100项检查')
    rows=[];seen=set()
    for check in checks:
        if not isinstance(check,dict):raise ValueError('核验检查项须为对象')
        row={k:text(check.get(k),k) for k in ('id','label','criterion')}
        if row['id'] in seen:raise ValueError('核验检查项id重复')
        seen.add(row['id']);rows.append(dict(**row,status='pending',detail='尚未执行',evidence='尚未产生'))
    identity=uuid.uuid4().hex;root=folder(store.directory,identity)
    state=store.state();now=stamp(time.time())
    data.update(version=VERSION,id=identity,topic=state['topic'],run_id=state['id'],task_id=op['task_id'],operation_id=operation,
        authority=authority,checks=rows,status='pending',summary='检查项已登记，尚未开始',next_action='执行已登记的核验',
        started_at=now,updated_at=now,observed_at=now,scientific_admission_inferred=False)
    write(root/'state.json',data)
    return data


def read(root,session):
    data=load(folder(root,session)/'state.json',Path(root).resolve())
    if data.get('version')!=VERSION or data.get('id')!=session or data.get('status') not in STATES:
        raise ValueError('核验记录版本或身份不匹配')
    if not isinstance(data.get('checks'),list) or not 1<=len(data['checks'])<=100:raise ValueError('无效核验清单')
    for row in data['checks']:
        if not isinstance(row,dict) or row.get('status') not in STATES:raise ValueError('无效核验单项')
        for key in ('id','label','criterion','detail','evidence'):text(row.get(key),key)
        if 'completed' in row and (type(row['completed']) is not int or row['completed']<0):raise ValueError('无效核验计数')
    return data


def update(root,session,data):
    root=Path(root).resolve();path=folder(root,session);path.mkdir(parents=True,exist_ok=True)
    with (path/'update.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        state=read(root,session)
        changes=data.get('checks',[])
        if not isinstance(changes,list) or len(changes)>100:raise ValueError('核验更新检查项须为列表')
        indexed={c['id']:c for c in state['checks']};seen=set()
        for change in changes:
            if not isinstance(change,dict) or change.get('id') not in indexed or change['id'] in seen:raise ValueError('核验检查项身份不匹配')
            seen.add(change['id']);status=change.get('status')
            if status not in STATES:raise ValueError('无效核验状态')
            detail=text(change.get('detail'),'detail');evidence=text(change.get('evidence'),'evidence')
            row=indexed[change['id']]
            if row['status'] in ('passed','failed','skipped') and status!=row['status']:
                raise ValueError('保留原核验终态；修复后创建新核验记录，不覆盖旧失败')
            if status=='passed' and evidence in ('尚未产生','未取得','无'):raise ValueError('通过核验必须提供具体证据')
            row.update(status=status,detail=detail,evidence=evidence,updated_at=stamp(time.time()))
            if 'completed' in change:
                done,total=change['completed'],change.get('total')
                if type(done) is not int or done<0 or (total is not None and (type(total) is not int or total<=0 or done>total)):
                    raise ValueError('核验计数须为真实非负整数，分母未知填null')
                if done<row.get('completed',0):raise ValueError('同次核验的检查计数不能回退')
                row.update(completed=done,total=total,unit=text(change.get('unit'),'unit'))
        for name in ('summary','next_action'):
            if name in data:state[name]=text(data[name],name)
        values=[c['status'] for c in state['checks']]
        state['status']=('failed' if 'failed' in values else 'unknown' if 'unknown' in values else
            'passed' if all(s in ('passed','skipped') for s in values) and 'passed' in values else 'skipped' if all(s=='skipped' for s in values) else 'running' if 'running' in values else 'pending')
        state.update(updated_at=stamp(time.time()),observed_at=stamp(time.time()))
        write(path/'state.json',state)
        with (path/'console.log').open('a') as log:
            log.write(state['updated_at']+' '+json.dumps(dict(summary=state['summary'],checks=state['checks']),ensure_ascii=False)+'\n')
        return state


class ControllerChecks:
    """Only surrounds real validator calls; errors and return values are unchanged."""
    def __init__(self,store,task,checks,title='控制器阶段验收'):
        self.root=store.directory;self.data=None
        try:
            target=task['title']+' · 调用 '+task['operation_id']
            op=store.operation(task['operation_id']);result=execution.safe(store.directory,Path(op['directory'])/'result.json')
            if result.is_file() and result.stat().st_size<=500000:target+=' · 输出版本SHA256 '+hashlib.sha256(result.read_bytes()).hexdigest()
            self.data=plan(store,task['operation_id'],dict(title=title,object=target,
                scope='执行原验证器并记录返回；不代替独立科学结论',checks=checks),'controller')
        except Exception:pass  # Observability cannot prevent scientific validation.

    def publish(self,**data):
        if self.data:
            with contextlib.suppress(Exception):self.data=update(self.root,self.data['id'],data)

    def check(self,key,label,fn,skip_if_none=False):
        self.publish(summary='正在核验：'+label,next_action='等待本项原验证器返回',
            checks=[dict(id=key,status='running',detail='原验证器正在执行',evidence='最终返回证据尚未产生')])
        stop=threading.Event()
        def heartbeat():
            while not stop.wait(5):
                self.publish()  # Heartbeat only, never a fabricated check count.
        thread=threading.Thread(target=heartbeat,daemon=True);started=False
        try:thread.start();started=True
        except RuntimeError:pass
        try:
            result=fn()
        except BaseException as exc:
            stop.set()
            if started:thread.join()
            status='unknown' if isinstance(exc,(KeyboardInterrupt,SystemExit)) else 'failed'
            self.publish(summary=label+'未通过',next_action='保留原始错误，按原流程修复后复验',
                checks=[dict(id=key,status=status,detail=execution.redact(str(exc))[:3000] or type(exc).__name__,
                             evidence='控制器捕获原验证器异常：'+type(exc).__name__)])
            raise
        stop.set()
        if started:thread.join()
        try:evidence='原验证器实际返回SHA256 '+hashlib.sha256(json.dumps(result,sort_keys=True,default=str,ensure_ascii=False).encode()).hexdigest()
        except Exception:evidence='原验证器实际正常返回；返回值未能序列化为核验摘要'
        skipped=skip_if_none and result is None
        self.publish(summary=label+('本次不适用' if skipped else '已返回通过'),next_action='继续剩余核验；最终阶段结果以原控制器为准',
            checks=[dict(id=key,status='skipped' if skipped else 'passed',detail='本调用没有适用的此项契约，未额外执行检查' if skipped else '原验证器已正常返回，未新增或降低原检查标准',
                         evidence=evidence+'；日志保留时间与检查项身份')])
        return result


def log(root,session):
    state=read(root,session)
    path=folder(root,session)/'console.log'
    if path.exists():text,size,at=execution.tail(path)
    else:text,size,at='核验尚未产生逐项输出。',0,state['updated_at']
    return dict(text=execution.redact(text),bytes=size,updated_at=at,truncated=size>65536,session=state['id'])


def marker_checks(raw):
    rows={}
    for line in raw.splitlines():
        if not line.startswith('ARS_CHECK='):continue
        try:
            data=json.loads(line[len('ARS_CHECK='):])
            if not isinstance(data,dict) or data.get('status') not in STATES:continue
            row={k:text(data.get(k),k) for k in ('id','label','criterion','detail','evidence')}
            if data['status']=='passed' and row['evidence'] in ('尚未产生','未取得','无'):continue
            row['status']=data['status']
            done,total=data.get('completed'),data.get('total')
            if type(done) is int and done>=0 and (total is None or (type(total) is int and 0<total and done<=total)):
                row.update(completed=done,total=total,unit=str(data.get('unit','项')))
            rows[row['id']]=row
        except (ValueError,TypeError):continue
    return list(rows.values())[:100]


def describe(store,state,observation):
    current=(state.get('progress',{}).get('current_task') or {}).get('id');sessions=[]
    base=execution.safe(store.directory,'artifacts/telemetry/verifications')
    paths=sorted(base.glob('*/state.json'),key=lambda p:p.stat().st_mtime,reverse=True)[:48]
    for path in paths:
        try:
            data=read(store.directory,path.parent.name)
            operation=store.operation(data.get('operation_id'))
            if data.get('topic')!=state['topic'] or data.get('run_id')!=state['id'] or not operation:continue
            data['source']='session';data['is_current_task']=data['task_id']==current
            age=execution.age(data.get('observed_at'),time.time())
            data['stale']=bool(data['status']=='running' and age is not None and age>30)
            if data['stale']:
                data.update(reported_status=data['status'],status='unknown',summary='核验采集已过期；保留最后检查项，尚不能确认核验是否继续')
            if data['status'] in ('pending','running') and operation['state'] in ('FINALIZED','CANCELLED','ABANDONED'):
                data.update(reported_status=data['status'],status='unknown',summary='原调用已结束，但此核验记录未封口；保留已返回项，不能把缺项当作通过')
            sessions.append(data)
        except (ValueError,OSError,KeyError,TypeError):continue
    # Existing acceptance/compile jobs become visible immediately without
    # rewriting the task's frozen validators or claiming per-check success.
    for job in observation.get('jobs',[])+observation.get('previous_jobs',[]):
        if job['kind'] not in ('acceptance','compile'):continue
        try:
            output=execution.log(store.directory,job['source'])
            _,receipt,_=execution.receipt(store.directory,job['source'])
            rows=marker_checks(output['text'])
            status={'succeeded':'passed','failed':'failed','running':'running'}.get(job['status'],'unknown')
            check=dict(id='command_exit',label='命令执行与退出回执',criterion='取得该命令确定退出码；0仅表示命令正常返回',
                status=status,detail=job['reason'],evidence='回执 '+job['source'])
            task_id=(receipt.get('dashboard') or {}).get('task_id')
            summary=job['reason']
            if any(row['status']=='failed' for row in rows):status='failed';summary='存在逐项核验失败；命令退出回执和原始失败分别保留'
            elif any(row['status']=='unknown' for row in rows):status='unknown';summary='有检查项结果未确认；不能仅凭命令正常返回判为核验通过'
            elif status=='passed' and any(row['status'] in ('pending','running') for row in rows):
                status='unknown';summary='命令已返回，但逐项核验未保存终态'
            sessions.append(dict(id='job-'+hashlib.sha256(job['source'].encode()).hexdigest()[:20],title='独立核验作业' if job['kind']=='acceptance' else '编译核验',
                object=job['id'],scope='命令退出回执；逐项结果在有结构化输出时另列',authority='job_receipt',source='job',job_source=job['source'],
                status=status,summary=summary,next_action='按本任务协议核对逐项结果，修复后保留原失败并复验',
                checks=[check,*[dict(r,authority='executor_report') for r in rows]],
                started_at=job['started_at'],updated_at=job['observed_at'],observed_at=job['observed_at'],
                is_current_task=job['operation_scope']=='current',task_id=task_id,stale=job['status']=='unknown',scientific_admission_inferred=False))
        except (ValueError,OSError,KeyError,TypeError):continue
    # Read-only compatibility for already-running agents: reflect the exact
    # declared verification step, explicitly flagging the missing breakdown.
    dashboard=state.get('experiment_progress',{}).get('dashboard',{})
    if dashboard.get('task_id')==current and not any(s.get('task_id')==current and s.get('source')=='session' for s in sessions):
        for step in dashboard.get('steps',[]):
            if step.get('status') not in ('running','pending','unknown','failed','blocked'):continue
            if not (step.get('kind')=='verification' or re.search(r'核验|复验|核对|验收|审查|审核',str(step.get('label','')))):continue
            status={'running':'running','pending':'pending','failed':'failed'}.get(step['status'],'unknown')
            if dashboard.get('mode')=='stale' and status=='running':status='unknown'
            detail=step.get('detail') or '执行者尚未保存此核验的逐项说明'
            check=dict(id=step['id'],label=step['label'],criterion=step.get('target_basis','原任务核验协议'),status=status,
                detail=detail,evidence='实验工作项说明 · '+str(dashboard.get('operation_id',''))+'；逐项核验记录尚未接入')
            if type(step.get('completed')) is int:check.update(completed=step['completed'],total=step.get('total'),unit=step.get('unit','项'))
            sessions.append(dict(id='stage-'+hashlib.sha256((str(dashboard.get('operation_id'))+step['id']).encode()).hexdigest()[:20],
                task_id=current,operation_id=dashboard.get('operation_id'),title=step['label'],object=dashboard.get('title','本次工作项'),
                scope='执行者登记的核验步骤；没有逐项证据时不推定各项通过',authority='stage_report',source='stage',
                status=status,checks=[check],summary=detail,next_action=dashboard.get('next_action') or '等待该核验按原协议执行并登记具体结果',
                started_at=None,updated_at=dashboard.get('updated_at'),observed_at=dashboard.get('updated_at'),is_current_task=True,
                stale=dashboard.get('mode')=='stale',scientific_admission_inferred=False))
    # Old controller results retain their actual scope; no invented breakdown.
    for task in reversed(store.tasks()):
        if len(sessions)>=80:break
        if not task.get('verification'):continue
        try:
            result=json.loads(task['verification']);op=store.operation(task['operation_id']) if task.get('operation_id') else None
            if not isinstance(result,dict):continue
            if not op or any(s.get('operation_id')==op['id'] and s.get('authority')=='controller' and s.get('status') in ('passed','failed') for s in sessions):continue
            error=result.get('error');status='failed' if error else 'passed' if any(result.get(k) for k in ('gate','stage_artifacts','code_repair')) else 'unknown'
            when=op.get('finalized_at') or task['created_at']
            sessions.append(dict(id='legacy-'+op['id'],operation_id=op['id'],task_id=task['id'],title='既有控制器验收记录',object=task['title'],
                scope='账本保存的结构/来源或阶段校验；旧记录没有逐项过程时不补造',authority='legacy_controller',source='legacy',
                status=status,summary=execution.redact(str(error or '已保存控制器返回；验收范围见原账本')),
                next_action='按原阶段门槛接续；失败保留原错误',started_at=when,updated_at=when,observed_at=when,
                checks=[dict(id='saved_result',label='原账本保存的核验结果',criterion=str(result.get('gate','原阶段验证器')),
                    status=status,detail=execution.redact(str(error or '已保存原控制器返回；不推定未记录的单项核验')),
                    evidence='tasks.verification · 调用 '+op['id'])],is_current_task=task['id']==current,scientific_admission_inferred=False))
        except (ValueError,TypeError,KeyError):continue
    sessions.sort(key=lambda s:(bool(s['is_current_task']),bool(s['is_current_task'] and s['status']=='running' and not s.get('stale')),s.get('updated_at') or ''),reverse=True)
    return dict(version=VERSION,sessions=sessions,checked_at=stamp(time.time()),
        explanation='命令回执、执行者逐项报告与控制器验收分别标注；页面只读，核验状态不代替科学结论。')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['plan','update'])
    parser.add_argument('--directory',type=Path,required=True);parser.add_argument('--operation');parser.add_argument('--session');parser.add_argument('--input',type=Path,required=True)
    args=parser.parse_args()
    import ars,git_boundary
    store=ars.Store(args.directory)
    try:
        git_boundary.validate_state(store.state(),store.directory);data=load(args.input,store.directory.resolve())
        if args.action=='plan':out=plan(store,args.operation,data)
        else:
            record=read(store.directory,args.session)
            if record.get('authority')!='executor_report':raise ValueError('不能覆盖控制器核验记录')
            out=update(store.directory,args.session,data)
        print(json.dumps(dict(session=out['id'],status=out['status']),ensure_ascii=False))
    finally:store.close()


if __name__=='__main__':main()
