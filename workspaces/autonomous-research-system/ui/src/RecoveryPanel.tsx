import React, {useEffect, useState} from 'react';
import {VStack, HStack} from '@astryxdesign/core/Layout';
import {Text, Heading} from '@astryxdesign/core/Text';
import {Button} from '@astryxdesign/core/Button';
import {Selector} from '@astryxdesign/core/Selector';
import {Table} from '@astryxdesign/core/Table';
import {Collapsible} from '@astryxdesign/core/Collapsible';
import {LogViewer} from './LogViewer';

type Data = Record<string, any>;
const date=(v:any)=>v?new Date(v).toLocaleString('zh-CN',{hour12:false}):'未记录';
const states:Data={UNKNOWN:'执行结果未确认',FAILED:'失败',BLOCKED:'阻塞',RUNNING:'运行中',PENDING:'待执行',queued:'已登记',running:'处理中',completed:'操作完成',failed:'操作失败',interrupted:'操作中断'};

export function RecoveryPanel({s,runKey,invoke,focusTaskId}:{s:Data;runKey:string;invoke:(action:string,data:Data)=>Promise<Data>;focusTaskId?:string}) {
  const issues=(s.tasks || []).filter((t:Data)=>['UNKNOWN','FAILED','BLOCKED'].includes(t.status) && !t.superseded_by);
  const history=s.recovery_actions?.history || [];
  const [selected,setSelected]=useState(''),[busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[error,setError]=useState('');
  const [log,setLog]=useState<Data>(),[showLog,setShowLog]=useState(false);
  const tracked=history.find((r:Data)=>s.tasks?.some((t:Data)=>t.id===r.result?.recovery_task_id && ['PENDING','RUNNING','UNKNOWN'].includes(t.status)));
  const task=issues.find((t:Data)=>t.id===selected) || issues.find((t:Data)=>t.id===tracked?.task_id) || issues.find((t:Data)=>t.status==='UNKNOWN') || issues.find((t:Data)=>t.status==='FAILED') || issues[0];
  const active=s.recovery_actions?.active;
  const latest=history.find((r:Data)=>r.task_id===task?.id) || history[0];
  const childId=latest?.result?.recovery_task_id;
  const child=s.tasks?.find((t:Data)=>t.id===childId);
  const repairing=!!task?.recovering_by || (latest?.task_id===task?.id && child && ['PENDING','RUNNING','UNKNOWN'].includes(child.status));
  const diagnosis=task?.execution?.reconciliation || history.find((r:Data)=>r.task_id===task?.id && r.result?.execution?.reconciliation)?.result.execution.reconciliation;
  useEffect(()=>{if(focusTaskId && issues.some((t:Data)=>t.id===focusTaskId)){setSelected(focusTaskId);setShowLog(false)}},[focusTaskId]);
  useEffect(()=>{setLog(undefined);setShowLog(false)},[task?.id,runKey]);
  async function act(action:string) {
    if(busy || !task)return;
    setBusy(true);setError('');setNotice('正在登记操作…');
    try {
      const out=await invoke('recovery-action',{key:runKey,action,task_id:task.id,operation_id:task.operation_id});
      setNotice(`${out.duplicate?'已有恢复操作，未重复提交':'已登记'}：${out.operation.label} · 操作编号 ${out.operation.id}`);
    }catch(e){setError(String(e));setNotice('')}
    finally{setBusy(false)}
  }
  async function readLog(operationId=task?.operation_id) {
    if(!operationId)return;
    setShowLog(true);setError('');
    try{
      const r=await fetch('/api/agent/operation-log?'+new URLSearchParams({key:runKey,operation:operationId}));
      const out=await r.json();if(!r.ok)throw Error(out.error || r.status);setLog(out);
    }catch(e){setError(String(e))}
  }
  if(!issues.length && !history.length)return null;
  return <VStack gap={4} paddingBlock={4}>
    <HStack hAlign="between" wrap="wrap" gap={3}>
      <Heading level={2}>故障与恢复</Heading>
      <Text type="supporting">{active?'恢复操作正在执行，进展自动刷新':child?`恢复工作项：${states[child.status] || child.status}`:issues.length?`${issues.length} 项需要处置`:'最近恢复记录'}</Text>
    </HStack>
    {task && <>
      <Selector label="选择要处理的失败 / 待核对工作项" value={task.id} onChange={setSelected} options={issues.map((t:Data)=>({value:t.id,label:`${t.recovering_by?'修复中':states[t.status]} · ${t.title}`}))} />
      <Text weight="semibold">阻点：{diagnosis?.summary || task.error || task.summary || s.reason || '尚无可读取的失败说明，点击立即核对'}。</Text>
      <Text>当前动作：{active?.detail || (child?`控制器正在处理恢复工作项「${child.title}」，状态：${states[child.status] || child.status}`:s.recovery_control?.action==='waiting_for_receipt'?'监督器只在轮询原回执，没有恢复执行。可以在这里发起修复并接续。':s.recovery_control?.reason || '尚未发起恢复操作')}</Text>
      <Text type="supporting">最近检查：{date(s.recovery_control?.checked_at)} · 原调用最近执行输出：{date(diagnosis?.last_output_at)}。检查时间更新不代表修复已经推进。</Text>
      <HStack gap={3} wrap="wrap">
        <Button label={busy?'正在提交…':'立即核对'} isDisabled={busy || !!active} onClick={()=>act('inspect')} />
        <Button label="查看原始错误与执行日志" isDisabled={!task.operation_id || busy} onClick={()=>readLog()} />
        <Button label={repairing?'修复正在进行':'修复并接续'} variant="primary" isDisabled={busy || !!active || !!repairing} onClick={()=>act('recover')} />
        <Button label="复验已有产物" isDisabled={busy || !!active || !!repairing || task.status!=='FAILED'} onClick={()=>act('revalidate')} />
        <Button label="停止本运行" variant="destructive" isDisabled={busy || s.status==='STOPPED_USER'} onClick={async()=>{setBusy(true);try{await invoke('stop',{key:runKey});setNotice('已请求停止本运行，原始记录保留')}catch(e){setError(String(e))}finally{setBusy(false)}}} />
      </HStack>
      <Text type="supporting">立即核对只读取证据；复验已有产物只重新验收失败产物。修复并接续会通过控制器调用当前阶段配置的模型，先复用结果和检查点，保留原失败、调用消耗及未知实验，不盲目重投。</Text>
      {task.status!=='FAILED' && <Text type="supporting">回执缺失由系统核对；上方按钮可手动触发一次检查或修复。“复验已有产物”仅适用于已返回结果但验收失败的工作项。</Text>}
    </>}
    {notice && <Text role="status">{notice}</Text>}
    {error && <Text role="alert">{error}</Text>}
    {latest && <VStack gap={2}>
      <Text weight="semibold">最近操作：{latest.label} · {states[latest.state] || latest.state}</Text>
      <Text>{latest.detail}</Text>
      <Text type="supporting">更新于 {date(latest.updated_at)} · 操作编号 {latest.id}</Text>
      {!!latest.result?.rejected_tasks?.length && latest.result.rejected_tasks.map((r:Data)=><Text key={r.task_id}>仍未通过：{r.error}</Text>)}
      {child && <Text>恢复工作项：{child.title} · {states[child.status] || child.status} · {child.summary || child.error || '执行结果尚未返回，下面的执行证据会持续更新'}</Text>}
      {child?.operation_id===s.execution_observation?.agent?.operation_id && !!s.execution_observation?.agent_messages?.length && <Text as="p" style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>执行者最新说明：{s.execution_observation.agent_messages.at(-1).text}</Text>}
      {child?.operation_id && <HStack><Button label="查看恢复执行日志" onClick={()=>readLog(child.operation_id)} /></HStack>}
    </VStack>}
    {showLog && <VStack gap={3}>
      <HStack hAlign="between" gap={3} wrap="wrap"><Heading level={3}>调用错误与执行日志</Heading><HStack gap={2}><Button label="刷新日志" onClick={()=>readLog(log?.operation_id || task?.operation_id)} /><Button label="关闭日志" onClick={()=>setShowLog(false)} /></HStack></HStack>
      {log?<>
        <Text type="supporting">最近输出：{date(log.updated_at)} · 显示最近公开说明、命令和输出末尾。</Text>
        {log.stderr && <LogViewer title="stderr.log" text={log.stderr} />}
        {log.commands?.map((c:Data,i:number)=><Collapsible key={i} trigger={`命令 ${i+1} · ${c.state || '未返回'} · 退出码 ${c.exit_code ?? '未知'}`} defaultIsOpen={i===log.commands.length-1}>
          <VStack gap={2} paddingBlock={3}><LogViewer title={`命令 ${i+1} / output.log`} text={`${c.command}\n\n${c.output || '该命令未保存输出；不能据此判定成功。'}`} /></VStack>
        </Collapsible>)}
        {!log.commands?.length && <Text>原调用尚无可读取的公开命令输出；最终回执与结果状态见上方。</Text>}
      </>:<Text>正在读取原调用日志…</Text>}
    </VStack>}
    {!!history.length && <Collapsible trigger="恢复操作记录与执行步骤" defaultIsOpen={!!active}>
      <VStack gap={3} paddingBlock={3}>
        <Table data={history.slice(0,10)} textOverflow="wrap" columns={[
          {key:'label',header:'操作 / 工作项',renderCell:(r:Data)=><VStack gap={1}><Text weight="semibold">{r.label}</Text><Text type="supporting">{r.title}</Text></VStack>},
          {key:'state',header:'实际结果',renderCell:(r:Data)=><VStack gap={1}><Text>{states[r.state] || r.state}</Text><Text type="supporting">{r.detail}</Text></VStack>},
          {key:'steps',header:'执行步骤',renderCell:(r:Data)=><VStack gap={1}>{(r.steps || []).map((step:Data,i:number)=><Text key={i} type="supporting">{date(step.at)} · {step.detail}</Text>)}</VStack>},
        ]} />
      </VStack>
    </Collapsible>}
  </VStack>;
}
