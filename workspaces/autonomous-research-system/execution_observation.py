"""Explain execution uncertainty from local receipts and mirrored job logs.

Read-only: no SSH, model call, process signal, reconciliation or job submission.
Agent commentary, process receipts and scientific evidence stay separate.
"""
import datetime as dt
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re
import time


LABELS={'environment_steps':'环境交互','accepted_samples':'接纳训练样本','discarded_samples':'丢弃样本',
        'evaluation_steps':'评价交互','optimizer_calls':'优化器调用','source_updates':'来源更新',
        'completed':'已结束','failed':'失败','total':'计划总量'}


def redact(text):
    text=re.sub(r'(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]+','[REDACTED]',text)
    text=re.sub(r'(?i)(authorization["\x27]?\s*[:=]|api[_ -]?key["\x27]?\s*[=:]|password["\x27]?\s*[=:]|access[_-]?token["\x27]?\s*[=:])[^\n]+',r'\1 [REDACTED]',text)
    text=re.sub(r'(?i)(--(?:password|token|api-key)\s+)\S+',r'\1[REDACTED]',text)
    return text


def safe(root,path):
    root=Path(root).resolve();path=Path(path)
    if not path.is_absolute():path=root/path
    if not path.resolve().is_relative_to(root) or any(p.is_symlink() for p in [path,*path.parents] if p!=root and p.is_relative_to(root)):
        raise ValueError('日志或回执路径越界/符号链接')
    return path


def stamp(value):
    return dt.datetime.fromtimestamp(value,dt.timezone.utc).isoformat()


def age(value,now):
    try:return max(0,now-dt.datetime.fromisoformat(value).timestamp())
    except (ValueError,TypeError):return None


def receipt(root,reference):
    # Only job receipts under artifacts may disclose a console. Never request,
    # credential, original-input or model reasoning files selected by a URL.
    relative=Path(reference)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts or relative.parts[0]!='artifacts' or relative.name!='receipt.json':
        raise ValueError('需要本运行已登记作业的回执引用')
    path=safe(root,relative)
    if path.stat().st_size>256000:raise ValueError('作业回执过大')
    data=json.loads(path.read_text())
    if not isinstance(data,dict):raise ValueError('作业回执格式无效')
    if data.get('simulated') is not False or data.get('experiment_kind') not in ('acceptance','pilot','comparison','compile'):
        raise ValueError('不是实验作业回执')
    value=data.get('log_path')
    if value is not None and not isinstance(value,str):raise ValueError('作业日志路径格式无效')
    log=safe(root,value or path.with_name('console.log'))
    if log.parent.resolve()!=path.parent.resolve() or log.name!='console.log':raise ValueError('日志未绑定回执所在作业目录')
    return path,data,log


def tail(path,maximum=65536):
    size=path.stat().st_size
    with path.open('rb') as stream:
        offset=max(0,size-maximum);stream.seek(offset);raw=stream.read(maximum)
    if offset and b'\n' in raw:raw=raw.split(b'\n',1)[1]
    return raw.decode(errors='replace'),size,stamp(path.stat().st_mtime)


def log(root,reference):
    path,data,console=receipt(root,reference)
    text,size,updated=tail(console)
    return dict(job=reference,text=redact(text),bytes=size,updated_at=updated,
                truncated=size>65536,status=data.get('status'),exit_code=data.get('exit_code'),
                target=data.get('target'),source=str(console.relative_to(Path(root).resolve())))


@lru_cache(maxsize=32)
def inventory(root,bucket):
    root=Path(root);paths=[]
    for i,path in enumerate((root/'artifacts').rglob('receipt.json')):
        if i>=4096:break
        try:paths.append((path.stat().st_mtime,str(path.relative_to(root))))
        except OSError:pass
    return [p for _,p in sorted(paths,reverse=True)[:96]]


def counters(data):
    if not isinstance(data,dict):return []
    return [dict(key=k,label=LABELS.get(k,k),value=v) for k,v in data.items()
            if isinstance(k,str) and type(v) is int and v>=0][:40]


def job_process(data):
    """A PID alone cannot identify a job (especially for old receipts)."""
    import ars
    identity=data.get('child_process')
    if not isinstance(identity,dict) or not {'pid','start_ticks','pgid'}<=identity.keys():
        # Absence is conclusive even for a legacy PID; presence is not, since
        # the number may now belong to an unrelated process.
        pid=data.get('pid')
        if type(pid) is int and pid>0 and not (Path('/proc')/str(pid)).exists():return False
        return None
    return ars.same_process(identity)


def snapshots(raw,reference,log_at,now):
    for line in reversed(raw.splitlines()):
        # Both a platform marker and existing structured aggregate lines work.
        match=re.match(r'(?:ARS_PROGRESS|AGGREGATE_PROGRESS)=(\{.*\})\s*$',line)
        if not match:continue
        try:
            data=json.loads(match[1])
            if not isinstance(data,dict) or data.get('simulated') is not False or not isinstance(data.get('counters'),dict):continue
            at=data.get('at')
            observed=stamp(at) if type(at) in (int,float) and 0<=at<=now+5 else log_at
            workers=[]
            for row in (data.get('sources') or [])[:100]:
                if not isinstance(row,dict):continue
                snapshot=row.get('snapshot',{})
                if not isinstance(snapshot,dict):continue
                workers.append(dict(identity=str(row.get('identity','未记录')),counters=counters(snapshot.get('counters',{})),
                    updated_at=stamp(snapshot['updated_at']) if type(snapshot.get('updated_at')) in (int,float) and 0<=snapshot['updated_at']<=now+5 else observed))
            return dict(counters=counters(data['counters']),workers=workers,updated_at=observed,
                age_seconds=age(observed,now),scope=data.get('scope'),completed_workers=data.get('completed_workers'),failed_workers=data.get('failed_workers'),
                source_job=reference,line_sha256=hashlib.sha256(line.encode()).hexdigest(),scientific_admission_inferred=False)
        except (ValueError,TypeError,KeyError,OverflowError):continue
    return None


def agent_trace(store,task):
    import ars
    if not task or not task.get('operation_id'):return {},[]
    operation=store.operation(task['operation_id'])
    root=safe(store.directory,operation['directory']);path=root/'events.jsonl'
    messages=[]
    if path.exists():
        text,_,at=tail(path,384000)
        for line in text.splitlines():
            try:event=json.loads(line)
            except ValueError:continue
            if not isinstance(event,dict):continue
            item=event.get('item',{})
            if isinstance(item,dict) and item.get('type')=='agent_message' and isinstance(item.get('text'),str):
                messages.append(dict(text=redact(item['text'])[:3000],observed_at=at))
    identities=[]
    for name in ('child.json','supervisor.json'):
        p=root/name
        if p.exists():
            try:
                value=ars.read_json(p)
                if isinstance(value,dict) and {'pid','start_ticks','pgid'}<=value.keys():identities.append(value)
            except ValueError:pass
    return dict(operation_id=operation['id'],operation_state=operation['state'],
                receipt_present=(root/'receipt.json').is_file(),process_alive=any(ars.same_process(x) for x in identities) if identities else None,
                started_at=operation['created_at'],last_output_at=stamp(path.stat().st_mtime) if path.exists() else None),messages[-6:]


def describe(store,state,now=None):
    now=time.time() if now is None else now
    p=state.get('progress',{});current=p.get('current_task',{}) or {}
    task=next((t for t in store.tasks() if t['id']==current.get('id')),None)
    agent,messages=agent_trace(store,task)
    jobs=[];previous_jobs=[];issues=[];snapshot=None
    for reference in inventory(str(store.directory.resolve()),int(now//5)):
        try:
            path,data,console=receipt(store.directory,reference)
            current=not agent or (data.get('started_at','')>=agent['started_at'] and
                (data.get('dashboard') or {}).get('operation_id') in (None,agent['operation_id']))
            if (current and len(jobs)>=12) or (not current and len(previous_jobs)>=6):continue
            observed=data.get('observed_at') or data.get('finished_at') or stamp(path.stat().st_mtime)
            seconds=age(observed,now)
            status=data.get('status','unknown');reason='';process_alive=job_process(data)
            if status=='running' and seconds is not None and seconds>30:
                status='unknown'
                location='本地命令' if data.get('target')=='local' else '服务器命令'
                reason=f'{location}回执已 {int(seconds)} 秒未更新，缺最终退出状态'
                if process_alive is True:
                    reason+='；已核对本地子进程身份仍在线，但回执采集未更新'
                elif process_alive is False:
                    reason+='；原本地子进程已退出，不能继续显示为执行中'
                else:
                    reason+='；旧回执缺进程启动身份，不能单凭PID判断是否仍在执行'
                if data.get('target')=='research-server':reason+='；本地连接进程状态不代表远端计算状态'
            elif status=='unknown':reason=data.get('error') or '执行器未取得命令的确定退出状态；远端是否完成需核对原输出'
            elif status=='failed':reason=data.get('error') or f"命令失败，退出码 {data.get('exit_code')}；查看日志末尾的原始错误"
            elif status=='running':reason='命令作业回执持续更新；以下日志与计数反映最近实际输出'
            else:reason=f"命令已返回，退出码 {data.get('exit_code')}；不等于科学验收通过"
            raw='';size=0;log_at=None;log_error=''
            try:raw,size,log_at=tail(console)
            except OSError as exc:log_error=type(exc).__name__+'：日志文件暂不可读'
            sample=snapshots(raw,reference,log_at or observed,now) if current and data.get('target')=='research-server' else None
            if sample and (snapshot is None or sample['updated_at']>snapshot['updated_at']):snapshot=sample
            job=dict(id=path.parent.name,source=reference,kind=data['experiment_kind'],target=data.get('target'),
                status=status,reason=redact(str(reason)),process_alive=process_alive,operation_scope='current' if current else 'previous',started_at=data.get('started_at'),observed_at=observed,
                log_updated_at=log_at,log_bytes=size,log_error=log_error,exit_code=data.get('exit_code'),
                elapsed_seconds=data.get('wall_seconds'),preview=redact('\n'.join(raw.splitlines()[-8:]))[-4000:])
            if not current:
                previous_jobs.append(job)
                continue
            jobs.append(job)
            if status in ('unknown','failed'):
                historical=status=='failed'
                issues.append(dict(subject=('保留的失败记录：' if historical else '缺少退出回执：')+path.parent.name,kind='historical_failure' if historical else 'job_receipt',what=redact(str(reason)),
                    system_action='保留原错误供修复与复验对照；这条历史失败本身不表示当前任务已停止' if historical else '对照此作业原日志、退出回执及服务器观测处理；未知结果禁止重复提交',user_action='由系统处理，无需你手工判断或重投',user_required=False,source=reference))
            if len(jobs)>=12 and len(previous_jobs)>=6:break
        except (OSError,ValueError,TypeError,KeyError):continue
    if agent and not agent['receipt_present'] and agent['process_alive'] is not True and agent['operation_state'] in ('UNKNOWN','DISPATCHED'):
        issues.insert(0,dict(subject='执行智能体最终回执',kind='agent_receipt',
            what=('本地智能体进程已退出' if agent['process_alive'] is False else '尚无可核对的本地执行进程身份')+'，但原调用没有最终回执；其远端作业是否结束与此不同，需要分别核对',
            system_action='控制器正在检查原回执。目前未确认该调用的执行进程在线；尚不能确认其最终结果，不能将等待回执写成实验仍在计算',
            user_action='由系统核对原调用和已有作业证据；不需要你手工运行 resolve 或重新提交实验',user_required=False,source=agent['operation_id']))
    d=state.get('experiment_progress',{}).get('dashboard',{})
    design=d.get('observation') or {}
    if snapshot:
        metrics={m['key']:m for m in design.get('metrics',[]) if isinstance(m,dict) and 'key' in m}
        for values in [snapshot['counters'],*[worker['counters'] for worker in snapshot['workers']]]:
            for value in values:
                metric=metrics.get(value['key'])
                if metric:
                    value.update({k:metric[k] for k in ('label','unit','total','target_basis') if k in metric})
    for step in d.get('steps',[]):
        if step.get('status') not in ('unknown','failed','blocked'):continue
        for check in step.get('checks',[]):
            if not isinstance(check,dict):continue
            issues.append(dict(subject=step['label'],kind='task_designed_check',what=redact(str(check.get('what',''))),
                evidence=redact(str(check.get('evidence',''))),system_action=redact(str(check.get('system_action',''))),
                user_action=redact(str(check.get('user_action',''))),user_required=check.get('user_required') is True))
    if d.get('mode') in ('awaiting_design','invalid'):
        issues.append(dict(subject='实验进度说明',kind='dashboard',what='执行端尚未登记本次具体进度设计' if d['mode']=='awaiting_design' else '当前看板身份或证据校验失败，未采用其计数',system_action='执行智能体须发布与本次调用绑定的设计及说明；下方独立保留原作业日志',user_action='系统展示/采集问题，无需你手工核对科学结果',user_required=False))
    elif d.get('mode')=='stale':
        issues.append(dict(subject='智能体进度说明',kind='stale_description',what='智能体写入的阶段说明已过期；服务器日志与命令回执可能仍在更新',system_action='分别读取下方命令回执、原始日志和实测计数，不以说明更新时间推定服务器停止',user_action='无需人工处理',user_required=False))
    decision=p.get('pending_decision')
    if decision:
        issues.append(dict(subject='明确的授权决定',kind='decision',what=decision.get('label','执行端已登记需要决定的事项'),system_action='查看对应任务中具体待决定项，已授权范围内的独立工作可继续',user_action=decision.get('label','需要你对已列明事项作决定'),user_required=True))
    return dict(checked_at=stamp(now),agent=agent,agent_messages=messages,jobs=jobs,previous_jobs=previous_jobs,snapshot=snapshot,issues=issues,
        user_required=any(x['user_required'] for x in issues),
        explanation='服务器命令执行、智能体说明和科学验收分别展示；日志来自已有作业输出，读取页面不发起SSH、模型或实验。')
