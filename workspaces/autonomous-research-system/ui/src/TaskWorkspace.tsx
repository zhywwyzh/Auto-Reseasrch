import {TaskTokenSummary} from './ModelUsage';
import {StatusPill} from './StatusPill';
import React, {useEffect, useState} from 'react';
import {VStack, HStack} from '@astryxdesign/core/Layout';
import {Grid} from '@astryxdesign/core/Grid';
import {Text, Heading} from '@astryxdesign/core/Text';
import {Button} from '@astryxdesign/core/Button';
import {StatusDot} from '@astryxdesign/core/StatusDot';
import {Table,proportional,pixel} from '@astryxdesign/core/Table';
import {Collapsible} from '@astryxdesign/core/Collapsible';
import {Selector} from '@astryxdesign/core/Selector';
import {TextInput} from '@astryxdesign/core/TextInput';
import {TextArea} from '@astryxdesign/core/TextArea';
import {ProgressBar} from '@astryxdesign/core/ProgressBar';

type Data = Record<string, any>;
const date = (v: any) => v ? new Date(v).toLocaleString('zh-CN', {hour12: false}) : '无记录';
const labels: Record<string,string> = {COMPLETED:'已完成',RUNNING:'执行中',PENDING:'待执行',FAILED:'失败',BLOCKED:'待处理',UNKNOWN:'执行结果未确认',NOT_CREATED:'尚未开始',REVISION_REQUIRED:'需修订',EXECUTION_ENDED:'执行已结束'};
const stateLabel = (t: Data, s: Data) => t.status === 'RUNNING' && s.status.startsWith('STOPPED_') ? '已停止' : labels[t.status] || t.status;
const agent = (e?: Data) => e ? `${e.backend === 'codex' ? 'Codex' : e.backend} · ${e.model || '默认模型'}` : '尚未分配调用';
const scopeLabel = (item: Data, s: Data) => item.scope === 'campaign' ? '整个研究的后续调用' : item.scope === 'phase' ? `阶段：${s.progress?.stages?.find((r: Data) => r.phase === item.target)?.label || item.target}` : `工作项：${s.tasks?.find((t: Data) => t.id === item.target)?.title || item.target}`;

export function ExecutionFocus({s, task}: {s: Data; task?: Data}) {
  const e = task?.execution;
  const live = s.status === 'RUNNING' && task?.status === 'RUNNING' && e?.process_alive;
  const anyLive = s.status === 'RUNNING' && s.tasks?.some((t:Data)=>t.status==='RUNNING' && t.execution?.process_alive);
  const executionLabel = s.status.startsWith('STOPPED_') ? '当前没有执行中的智能体 · 研究已停止' : s.status==='COMPLETED' ? '本轮流程已结束 · 当前无执行调用' : anyLive ? '执行智能体在线' : s.status==='READY' ? '研究已就绪 · 等待派发' : '未确认活跃执行进程 · 具体缺项见执行证据';
  const series = s.experiment_progress?.series?.[0];
  return <VStack gap={4}>
    <HStack gap={3} vAlign="center" wrap="wrap">
      <StatusDot variant={anyLive ? 'accent' : 'neutral'} label={executionLabel} isPulsing={!!anyLive} />
      <Heading level={3}>{executionLabel}</Heading>
    </HStack>
    <Grid columns={{minWidth: 240, max: 3}} gap={6}>
      <VStack gap={2}>
        <Text type="supporting">{live ? '正在执行的智能体' : '所选工作项的最近执行者'}</Text>
        <Heading level={3}>{agent(e)}</Heading>
        <Text type="supporting">{e?.identity_source === 'request' ? '身份取自本次实际调用请求' : '尚无可核验的调用请求'}</Text>
        <Text type="supporting">下次分配：{task?.planned_model?.model || '执行器默认模型'} · {task?.planned_model?.reason}</Text>
      </VStack>
      <VStack gap={2}>
        <Text type="supporting">具体工作项</Text>
        <Text weight="semibold">{task?.title || '尚未创建工作项'}</Text>
        {task && <Text type="supporting">{stateLabel(task,s)} · 第 {task.attempt || 0} 次调用</Text>}
      </VStack>
      <VStack gap={2}>
        <Text type="supporting">调用与会话</Text>
        <Text type="supporting" style={{overflowWrap:'anywhere'}}>调用：{e?.operation_id || '尚未派发'}</Text>
        <Text type="supporting">启动：{date(e?.started_at)}</Text>
        <Text type="supporting" style={{overflowWrap:'anywhere'}}>会话：{e?.thread_id || '尚无会话回执'}</Text>
      </VStack>
    </Grid>
    {task && <TaskTokenSummary usage={s.token_usage} taskId={task.id} />}
    {series?.counts?.total > 0 && Number.isFinite(series.counts.terminal) && !series.planned_only ? <VStack gap={2}>
      <ProgressBar label={`${series.label} · 最近实验快照`} value={series.counts.terminal} max={series.counts.total} hasValueLabel formatValueLabel={(v,m)=>`${v.toLocaleString()} / ${m.toLocaleString()} · ${(v/m*100).toFixed(1)}%`} />
      <Text type="supporting">采样：{date(series.source_at)} · 回合结束数包含失败，实验验收另行核对。</Text>
    </VStack> : <Text type="supporting">最近实验记录：{s.experiment_progress?.summary || '尚无实验计数记录'}</Text>}
  </VStack>;
}

export function StageBoard({s, onSelect, onRecover, compact=false}: {s: Data; onSelect: (id: string) => void; onRecover?: (id: string) => void; compact?:boolean}) {
  const stages = (s.progress?.stages || []).map((r: Data, i: number) => {
    const tasks = [...(s.tasks || [])].reverse().filter((t:Data)=>t.phase===r.phase);
    const latest = [...tasks].filter((t:Data)=>t.execution).sort((a:Data,b:Data)=>(b.execution.started_at || '').localeCompare(a.execution.started_at || ''))[0];
    const current = tasks.find((t:Data)=>t.status==='RUNNING') || tasks.find((t:Data)=>t.status==='UNKNOWN' && !t.superseded_by && !t.recovering_by);
    return {...r,order:i+1,task:current || latest || tasks[0],pending:tasks.filter((t:Data)=>t.status==='PENDING').length};
  });
  const unknown = (s.tasks || []).filter((t:Data)=>t.status==='UNKNOWN' && !t.superseded_by && !t.recovering_by);
  const recovery = s.recovery_control || {};
  const dashboard = s.experiment_progress?.dashboard;
  return <VStack gap={4}>
    <Heading level={3}>阶段执行台账</Heading>
    {!compact && <Text type="supporting">每行对应一个研究阶段。执行者来自该阶段最近一次真实调用；任务详情中可查看完整指令。</Text>}
    <Table data={stages} textOverflow="wrap" hasHover columns={[
      {key:'phase',header:'研究阶段',width:proportional(2,{minWidth:220}),renderCell:(r:Data)=><Text weight="semibold">{r.order}. {r.label}</Text>},
      {key:'status',header:'阶段状态',renderCell:(r:Data)=><VStack gap={2}><HStack><StatusPill state={r.status === 'RUNNING' && s.status.startsWith('STOPPED_')?'STOPPED_USER':r.status} label={r.status === 'RUNNING' && s.status.startsWith('STOPPED_') ? '停在此阶段' : labels[r.status] || r.status} /></HStack>{r.status==='UNKNOWN' && <Text type="supporting">{r.task?.execution?.reconciliation?.summary || r.task?.error || '原调用终态尚未核实；具体缺项见下方核对详情'}</Text>}</VStack>},
      ...(!compact?[
      {key:'task',header:'当前 / 最近执行的工作项',renderCell:(r:Data)=><VStack gap={1}><Text>{r.task?.title || '尚未创建'}</Text>{r.task && <Text type="supporting">{stateLabel(r.task,s)}{r.pending ? ` · 另有 ${r.pending} 项待执行` : ''}</Text>}</VStack>},
      {key:'executor',header:'执行智能体 / 模型',renderCell:(r:Data)=><VStack gap={1}><Text type="supporting">最近：{agent(r.task?.execution)}</Text><Text type="supporting">下次：{r.task?.planned_model?.model || '执行器默认模型'}</Text></VStack>},
      {key:'tokens',header:'此工作项 Token',renderCell:(r:Data)=><Text>{s.token_usage?.tasks?.find((t:Data)=>t.id===r.task?.id)?.usage?.total_tokens?.toLocaleString('zh-CN') ?? (r.task ? '未记录' : '—')}</Text>},
      {key:'started',header:'调用时间',renderCell:(r:Data)=><Text type="supporting">{date(r.task?.execution?.started_at)}</Text>},
      ]:[]),
      {key:'open',header:'任务与处置',width:pixel(124),renderCell:(r:Data)=>r.task ? <VStack gap={2}><Button label="任务详情" variant="ghost" onClick={()=>onSelect(r.task.id)} />{onRecover && ['UNKNOWN','FAILED','BLOCKED'].includes(r.task.status) && <Button label="处理故障" onClick={()=>onRecover(r.task.id)} />}</VStack> : <Text>—</Text>},
    ]} />
    {(compact?[]:unknown).map((t:Data)=>{
      const check=t.execution?.reconciliation;
      return <VStack key={t.id} gap={3}>
        <Heading level={4}>待核对详情：{t.title}</Heading>
        <Text>{check?.summary || t.error || s.reason || '缺少可读取的原调用诊断'}</Text>
        <Text type="supporting">当前动作：{recovery.action==='waiting_for_receipt' ? '监督器轮询原回执；尚未恢复执行，也未派发新研究作业。' : recovery.reason || s.progress?.next_action || '尚无恢复动作记录'}</Text>
        <Text type="supporting">最近检查：{date(recovery.checked_at)} · 下次检查：{date(recovery.next_check_at)} · 原调用最近输出：{date(check?.last_output_at)}</Text>
        {!!check?.checks?.length && <Table data={check.checks} textOverflow="wrap" columns={[
          {key:'label',header:'具体核对什么',renderCell:(r:Data)=><Text weight="semibold">{r.label}</Text>},
          {key:'detail',header:'目前查到的证据',renderCell:(r:Data)=><Text>{r.detail}</Text>},
          {key:'condition',header:'核对通过的条件',renderCell:(r:Data)=><Text type="supporting">{r.condition}</Text>},
        ]} />}
        {dashboard?.operation_id===t.operation_id && <VStack gap={2}>
          <Text weight="semibold">该调用最近保存的工作进展（{date(dashboard.updated_at)}）</Text>
          <Text>{dashboard.summary}</Text>
          {(dashboard.steps || []).filter((r:Data)=>r.status!=='completed').map((r:Data)=><Text key={r.id} type="supporting">{r.label}：{r.detail || labels[r.status] || r.status}</Text>)}
          <Text type="supporting">这是停止前保存的进展，不能据此认定当前仍在执行。</Text>
        </VStack>}
        <Text>恢复条件：{check?.resume_condition || '取得原调用的真实终态并完成独立复验，不能仅因等待时间增加而放行。'}</Text>
        <Text type="supporting">接续方式：{check?.next_action || s.progress?.next_action}</Text>
        <HStack gap={3} wrap="wrap"><Text type="supporting" style={{overflowWrap:'anywhere'}}>原调用：{t.operation_id || '未记录'}</Text><Button label="查看该调用完整任务" onClick={()=>onSelect(t.id)} /></HStack>
      </VStack>;
    })}
  </VStack>;
}

export function TaskRequirements({s, runKey, task, onSelect, save}: {s:Data; runKey:string; task?:Data; onSelect:(id:string)=>void; save:(data:Data)=>Promise<Data>}) {
  const draftKey = 'ars-supplement-draft:' + runKey;
  const [draft,setDraft] = useState<Data>(()=>{try{return JSON.parse(sessionStorage.getItem(draftKey) || '{}')}catch{return {}}});
  const [busy,setBusy] = useState(false), [notice,setNotice] = useState(''), [error,setError] = useState('');
  const [savedLocal,setSavedLocal] = useState<Data[]>([]), [selected,setSelected] = useState('');
  useEffect(()=>{sessionStorage.setItem(draftKey,JSON.stringify(draft))},[draft,draftKey]);
  const field = (k:string,v:string)=>setDraft((p)=>({...p,[k]:v}));
  const items = [...savedLocal,...(s.supplements || [])].filter((x,i,all)=>all.findIndex(y=>y.id===x.id)===i);
  const item = items.find(x=>x.id===selected) || items[0];
  async function submit() {
    if(busy)return;
    setBusy(true);setError('');setNotice('正在保存…');
    const scopeValue = draft.scope || 'campaign';
    const [scope,...target] = scopeValue.split(':');
    try {
      const out = await save({title:draft.title,instruction:draft.instruction,scope,target:target.join(':')});
      const receipt = {...out.supplement,delivery_status:'saved',deliveries:[]};
      // Prefer the subsequent server read for delivery evidence.
      setSavedLocal(prev=>[receipt,...prev.filter(x=>x.id!==receipt.id)]);
      setSelected(receipt.id);setDraft({});
      setNotice(`${out.duplicate ? '已存在相同补充，未重复保存' : '保存成功'} · 编号 ${receipt.id} · ${date(receipt.created_at)}`);
    }catch(e){setError(String(e));setNotice('保存失败，输入已保留。')}finally{setBusy(false)}
  }
  useEffect(()=>{setSavedLocal(prev=>prev.filter(x=>!(s.supplements || []).some((y:Data)=>y.id===x.id)))},[s.supplements]);
  return <VStack gap={6}>
    <Selector label="查看原始任务" value={task?.id || ''} options={(s.tasks || []).map((t:Data)=>({value:t.id,label:`${stateLabel(t,s)} · ${t.title}`}))} onChange={onSelect} />
    <Grid columns={{minWidth:340,max:2}} gap={8}>
      <VStack gap={4}>
        <Heading level={3}>这个工作项原本要做什么</Heading>
        <Text weight="semibold">{task?.title || '未选择任务'}</Text>
        <Text as="p" style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{task?.instruction || '没有可读取的原始指令。'}</Text>
        <Text type="supporting">创建：{date(task?.created_at)} · 任务编号 {task?.id}</Text>
        {task?.summary && <VStack gap={2}><Heading level={4}>此工作项返回的结果</Heading><Text>{task.summary}</Text><Text type="supporting">阶段核验：{labels[task.gate_status] || task.gate_status || '未核验'}</Text></VStack>}
        {task?.error && <Text>核验或执行问题：{task.error}</Text>}
        <Collapsible trigger="完整研究目标与原始约束" defaultIsOpen={false}>
          <VStack gap={3} paddingBlock={3}>
            <Text as="p" style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{s.goal}</Text>
            {(Array.isArray(s.constraints) ? s.constraints : [s.constraints]).filter(Boolean).map((c:any,i:number)=><Text key={i}>{typeof c==='string' ? c : JSON.stringify(c)}</Text>)}
          </VStack>
        </Collapsible>
      </VStack>
      <VStack gap={4}>
        <Heading level={3}>补充要求或资料</Heading>
        <Text type="supporting">保存到本研究，之后符合适用范围的调用会单独携带。保存不会启动研究，也不会改写已经发出的调用。</Text>
        <Selector label="在哪些任务中使用" value={draft.scope || 'campaign'} isDisabled={busy} onChange={v=>field('scope',v)} options={[
          {value:'campaign',label:'整个研究的后续调用'},
          ...(s.progress?.stages || []).map((r:Data)=>({value:'phase:'+r.phase,label:'仅阶段：'+r.label})),
          ...(s.tasks || []).map((t:Data)=>({value:'task:'+t.id,label:'仅工作项：'+t.title})),
        ]} />
        <TextInput label="标题" value={draft.title || ''} onChange={v=>field('title',v)} isDisabled={busy} />
        <TextArea label="补充正文" value={draft.instruction || ''} onChange={v=>field('instruction',v)} isDisabled={busy} />
        <Button label={busy ? '正在保存…' : '保存补充要求'} variant="primary" isDisabled={busy || !draft.title?.trim() || !draft.instruction?.trim()} onClick={submit} />
        {notice && <Text role="status" style={{overflowWrap:'anywhere'}}>{notice}</Text>}
        {error && <Text role="alert">{error}</Text>}
      </VStack>
    </Grid>
    <VStack gap={4}>
      <Heading level={3}>已保存的补充（{items.length}）</Heading>
      <Text type="supporting">“已进入调用”表示请求中确实包含该补充，不等于智能体已理解或落实。落实情况需核对对应任务结果。</Text>
      {items.length ? <Table data={items} textOverflow="wrap" hasHover columns={[
        {key:'title',header:'补充内容',renderCell:(r:Data)=><Text weight="semibold">{r.title}</Text>},
        {key:'scope',header:'适用范围',renderCell:(r:Data)=><Text>{scopeLabel(r,s)}</Text>},
        {key:'created_at',header:'保存时间',renderCell:(r:Data)=><Text type="supporting">{date(r.created_at)}</Text>},
        {key:'delivery_status',header:'携带证据',renderCell:(r:Data)=><Text>{r.delivery_status==='dispatched' ? '已进入调用上下文' : r.delivery_status==='prepared' ? '已加入请求，尚未派发' : '已保存，尚无调用携带记录'}</Text>},
        {key:'id',header:'查看',renderCell:(r:Data)=><Button label="查看补充" onClick={()=>setSelected(r.id)} />},
      ]} /> : <Text>本研究暂无已保存的补充。输入草稿还不等于保存成功。</Text>}
      {item && <VStack gap={3} maxWidth="64rem">
        <Heading level={4}>{item.title}</Heading>
        <Text as="p" style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{item.instruction}</Text>
        <Text type="supporting" style={{overflowWrap:'anywhere'}}>保存编号：{item.id} · 内容校验：{item.sha256}</Text>
        {item.legacy && <Text type="supporting">旧版还为这条补充创建了工作项：{labels[item.task_status] || item.task_status || '无关联任务'}，排入 {s.progress?.stages?.find((r:Data)=>r.phase===item.queued_phase)?.label || item.queued_phase || '未指定阶段'}。正文中的阶段要求仍须遵守；后续研究调用会独立携带这条补充。</Text>}
        {(item.deliveries || []).map((r:Data)=><HStack key={r.operation_id} gap={3} wrap="wrap"><Text type="supporting" style={{overflowWrap:'anywhere'}}>{date(r.created_at)} · {r.dispatched ? '已派发' : '请求已准备'} · 调用 {r.operation_id}</Text><Button label="查看对应工作项" onClick={()=>onSelect(r.task_id)} /></HStack>)}
      </VStack>}
    </VStack>
  </VStack>;
}
