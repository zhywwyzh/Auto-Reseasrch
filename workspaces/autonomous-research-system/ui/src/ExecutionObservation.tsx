import React,{useEffect,useRef,useState} from 'react';
import {VStack,HStack} from '@astryxdesign/core/Layout';
import {Grid} from '@astryxdesign/core/Grid';
import {Text,Heading} from '@astryxdesign/core/Text';
import {Button} from '@astryxdesign/core/Button';
import {Table} from '@astryxdesign/core/Table';
import {Collapsible} from '@astryxdesign/core/Collapsible';
import {LogViewer} from './LogViewer';
type Data=Record<string,any>;
const date=(v:any)=>v?new Date(v).toLocaleString('zh-CN',{hour12:false}):'未记录';
const status:Data={running:'回执持续更新',succeeded:'命令返回成功',failed:'命令返回失败',unknown:'退出状态或回执未确认'};
const kinds:Data={pilot:'先导实验',comparison:'对照实验',acceptance:'独立核验 / 采集',compile:'文档编译'};
function JobLog({runKey,reference}:{runKey:string;reference:string}){
 const [data,setData]=useState<Data>(),[error,setError]=useState(''),[refresh,setRefresh]=useState(0),[live,setLive]=useState(true);
 const lastRead=useRef('');
 useEffect(()=>{setData(undefined);setError('')},[runKey,reference]);
 useEffect(()=>{let active=true;const abort=new AbortController();
  async function read(){try{const r=await fetch('/api/agent/job-log?'+new URLSearchParams({key:runKey,job:reference}),{signal:abort.signal});const result=await r.json();if(!r.ok)throw Error(result.error || r.status);if(active){setData(result);setError('')}}catch(e){if(active)setError(String(e))}}
  const requestKey=JSON.stringify([runKey,reference,refresh]);
  if(live || requestKey!==lastRead.current){lastRead.current=requestKey;void read()}
  const timer=live?setInterval(read,5000):undefined;return()=>{active=false;abort.abort();if(timer)clearInterval(timer)};
 },[runKey,reference,refresh,live]);
 return <VStack gap={3}>
  {error&&<Text role="alert">{error}</Text>}
  <LogViewer text={data?.text || ''} title={reference.split('/').at(-2) + ' / console.log'} live={live} onLiveChange={setLive} onRefresh={()=>setRefresh(v=>v+1)} metadata={data?`更新 ${date(data.updated_at)} · ${data.bytes.toLocaleString()} 字节${data.truncated?' · 显示末尾64 KiB':''}`:'正在读取作业日志…'} />
 </VStack>;
}
export function ExecutionObservation({s,compact=false,jobsOnly=false}:{s:Data;compact?:boolean;jobsOnly?:boolean}){
 const o=s.execution_observation;
 const runKey=s.topic+'/'+s.id;
 const [selected,setSelected]=useState<string|null>(null),[showAll,setShowAll]=useState(false);
 useEffect(()=>{setSelected(null);setShowAll(false)},[runKey]);
 if(!o)return <Text>正在读取执行证据与日志…</Text>;
 const snapshot=o.snapshot,agent=o.agent;
 const jobs=o.jobs || [],remote=jobs.filter((j:Data)=>j.target==='research-server');
 const previous=o.previous_jobs || [],allJobs=[...jobs,...previous];
 const initialJobs=jobs.length?jobs:previous;
 const selectedRef=selected || '';
 const issues=(o.issues||[]).filter((i:Data)=>i.kind!=='historical_failure');
 const failures=(o.issues||[]).filter((i:Data)=>i.kind==='historical_failure');
 const dashboard=s.experiment_progress?.dashboard;
 const currentStep=dashboard?.steps?.find((r:Data)=>r.id===dashboard.current_step) || dashboard?.steps?.find((r:Data)=>r.status==='running');
 const messages=o.agent_messages || [];
 if(compact)return <VStack gap={2}>
  <Text type="supporting">{agent?.process_alive?'执行进程在线':agent?.operation_id?'执行进程未确认':'尚未派发调用'} · {remote.some((j:Data)=>j.status==='running')?'服务器回执在更新':remote.length?'已有服务器回执':'暂无新的服务器观测'}</Text>
  {issues[0] && <Text type="supporting">{issues[0].subject}：{issues[0].what}</Text>}
 </VStack>;
 return <VStack gap={5}>
  {!jobsOnly && <>
  <Heading level={3}>执行证据与具体待处理项</Heading>
  {currentStep&&<VStack gap={2}><Text weight="semibold">{dashboard.mode==='stale'?'最近记录的工作':'当前工作'}：{currentStep.label}</Text><Text>{currentStep.detail}</Text><Text type="supporting">记录于 {date(dashboard.updated_at)}{dashboard.mode==='stale'?' · 说明已过期，实际执行状态以下方回执与日志为准':''}</Text></VStack>}
  <Grid columns={{minWidth:230,max:3}} gap={5}>
   <VStack gap={2}><Text type="supporting">执行智能体</Text><Text weight="semibold">{agent?.process_alive===true?'本地执行进程在线':agent?.process_alive===false?'本地执行进程已退出':agent?.operation_id?'尚无可核对的执行进程身份':'当前没有执行调用'}</Text><Text type="supporting">最近输出：{date(agent?.last_output_at)}</Text><Text type="supporting">{agent?.receipt_present?'已有最终回执':agent?.operation_id?'本次调用尚无最终回执':'尚未派发'}</Text></VStack>
   <VStack gap={2}><Text type="supporting">服务器作业观测</Text><Text weight="semibold">{remote.some((j:Data)=>j.status==='running')?'服务器命令回执在更新':snapshot?'已有服务器实测计数':remote.length?'已有服务器命令返回记录':'当前未取得新的服务器命令观测'}</Text><Text type="supporting">{snapshot?'计数截至 '+date(snapshot.updated_at):remote[0]?'最近回执 '+date(remote[0].observed_at):'下方保留已知快照；不根据本地进程猜测服务器状态'}</Text></VStack>
   <VStack gap={2}><Text type="supporting">是否需要你处理</Text><Text weight="semibold">{o.user_required?'有明确待决定事项，见下方':'无需你手工核对或重新提交实验'}</Text><Text type="supporting">{issues.length?'存在系统待处理项，逐项说明如下':'当前未登记需人工处理的事项'}</Text></VStack>
  </Grid>
  {snapshot&&<VStack gap={3}>
   <Heading level={3}>服务器日志中的实际进展</Heading>
   <HStack gap={5} wrap="wrap">{snapshot.counters.map((r:Data)=><Text key={r.key}><strong>{r.label}</strong> {r.value.toLocaleString()}{r.unit?' '+r.unit:''}</Text>)}</HStack>
   {!!snapshot.workers?.length&&<Table data={snapshot.workers} textOverflow="wrap" columns={[
    {key:'identity',header:'来源 / 种子 / 分路',renderCell:(r:Data)=><Text weight="semibold">{r.identity}</Text>},
    {key:'counters',header:'最近实际计数',renderCell:(r:Data)=><Text>{r.counters.map((c:Data)=>`${c.label} ${c.value.toLocaleString()}${c.unit?' '+c.unit:''}`).join(' · ')}</Text>},
    {key:'updated_at',header:'采集时间',renderCell:(r:Data)=><Text>{date(r.updated_at)}</Text>},
   ]} />}
   <Text type="supporting">来自作业控制台的结构化输出，不表示阶段验收通过。没有可核对的计划分母时仅展示实测计数。</Text>
  </VStack>}
  {!!issues.length&&<VStack gap={3}>
   <Heading level={3}>“待核对”具体指什么</Heading>
   {(compact?issues.slice(0,2):issues).map((r:Data,i:number)=><VStack key={i} gap={2}>
    <Text weight="semibold">{r.subject}</Text><Text>{r.what}</Text>{r.evidence&&<Text type="supporting">证据：{r.evidence}</Text>}<Text>系统处理：{r.system_action}</Text><Text type="supporting">你的操作：{r.user_action}</Text>
   </VStack>)}
  </VStack>}
  </>}
  {!compact&&<>
   {dashboard?.observation&&<Collapsible trigger="本任务的进度采集与判定设计" defaultIsOpen={false}><VStack gap={3} paddingBlock={3}>
    <Text type="supporting">执行智能体依据当前协议设计；平台按设计展示。判定说明和进度计数不代替独立科学验收。</Text>
    <Table data={dashboard.observation.sources} textOverflow="wrap" columns={[
     {key:'purpose',header:'采集什么',renderCell:(r:Data)=><Text>{r.purpose}</Text>},
     {key:'location',header:'观测来源',renderCell:(r:Data)=><Text>{r.location}</Text>},
     {key:'update_interval_seconds',header:'更新频率',renderCell:(r:Data)=><Text>{r.update_interval_seconds?`${r.update_interval_seconds} 秒`:'结束时产生回执'}</Text>},
    ]} />
    {Object.entries(dashboard.observation.state_rules).map(([state,rule])=><Text key={state}><strong>{({running:'运行依据',completed:'结束依据',failed:'失败依据',unknown:'未知依据'} as Data)[state] || state}：</strong>{String(rule)}</Text>)}
    <Text>系统核对：{dashboard.observation.reconciliation.checks.join(' → ')}</Text>
    <Text>{dashboard.observation.reconciliation.action}</Text>
   </VStack></Collapsible>}
   <VStack gap={3}><Heading level={3}>实际作业与控制台日志</Heading>
    {!jobs.length&&!!previous.length&&<Text>本次调用尚无新的作业回执。以下保留前序作业日志，不能据此判断本次调用仍在计算。</Text>}
    {allJobs.length?<Table data={showAll?allJobs:initialJobs.slice(0,5)} hasHover textOverflow="wrap" columns={[
     {key:'id',header:'作业 / 位置',renderCell:(j:Data)=><VStack gap={1}><Text>{j.operation_scope==='previous'?'前序作业 · ':''}{j.target==='research-server'?'服务器':'本地'} · {kinds[j.kind] || j.kind}</Text><Text type="supporting" style={{overflowWrap:'anywhere'}}>{j.id}</Text></VStack>},
     {key:'status',header:'确认到哪里',renderCell:(j:Data)=><VStack gap={1}><Text weight="semibold">{status[j.status] || j.status}</Text><Text type="supporting">{j.reason}</Text></VStack>},
     {key:'observed_at',header:'最近回执 / 日志',renderCell:(j:Data)=><VStack gap={1}><Text type="supporting">回执 {date(j.observed_at)}</Text><Text type="supporting">日志 {date(j.log_updated_at)} · {j.log_bytes.toLocaleString()} 字节</Text></VStack>},
     {key:'source',header:'原始输出',renderCell:(j:Data)=><Button label="查看作业日志" onClick={()=>setSelected(j.source)} />},
    ]} />:<Text>该调用尚无可读取的作业回执；不能据此推定服务器正在计算或已经停止。</Text>}
    {allJobs.length>Math.min(initialJobs.length,5)&&<Button label={showAll?'收起较早作业':`查看较早作业（${allJobs.length-Math.min(initialJobs.length,5)}）`} onClick={()=>setShowAll(v=>!v)} />}
    {selectedRef&&<VStack gap={3}><HStack hAlign="between" wrap="wrap"><Text weight="semibold" style={{overflowWrap:'anywhere'}}>控制台：{allJobs.find((j:Data)=>j.source===selectedRef)?.operation_scope==='previous'?'前序作业 · ':''}{allJobs.find((j:Data)=>j.source===selectedRef)?.id || selectedRef}</Text><Button label="关闭日志" onClick={()=>setSelected('')} /></HStack><JobLog runKey={runKey} reference={selectedRef} /></VStack>}
    {!!failures.length&&<Collapsible trigger={`历史失败记录（${failures.length}）`} defaultIsOpen={false}><VStack gap={3} paddingBlock={3}>{failures.map((r:Data,i:number)=><VStack key={i} gap={2}><Text weight="semibold">{r.subject}</Text><Text>{r.what}</Text><Text type="supporting">{r.system_action}</Text></VStack>)}</VStack></Collapsible>}
   </VStack>
   {!!messages.length&&<Collapsible trigger="执行智能体最近的公开说明" defaultIsOpen={true}><VStack gap={3} paddingBlock={3}>
    <Text type="supporting">以下是智能体向用户输出的说明，属于执行者报告；服务器原始输出与科学核验分别保留。事件没有独立时间戳，最近事件文件更新于 {date(agent?.last_output_at)}。</Text>
    {messages.map((m:Data,i:number)=><Text key={i} as="p" style={{whiteSpace:'pre-wrap',overflowWrap:'anywhere'}}>{m.text}</Text>)}
   </VStack></Collapsible>}
  </>}
 </VStack>;
}
