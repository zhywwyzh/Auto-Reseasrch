import React,{useEffect,useState} from 'react';
import {VStack,HStack} from '@astryxdesign/core/Layout';
import {Text,Heading} from '@astryxdesign/core/Text';
import {Table} from '@astryxdesign/core/Table';
import {Selector} from '@astryxdesign/core/Selector';
import {Button} from '@astryxdesign/core/Button';
import {LogViewer} from './LogViewer';
type Data=Record<string,any>;
const labels:Data={pending:'已登记，等待执行更新',running:'正在核验',passed:'本次检查已返回通过',failed:'核验失败',unknown:'结果未确认',skipped:'本次未执行'};
const authority:Data={controller:'控制器实际验收',legacy_controller:'既有控制器验收',job_receipt:'命令退出回执',executor_report:'执行者逐项报告',stage_report:'执行者阶段说明 · 逐项结果未接入'};
const date=(s:any)=>s?new Date(s).toLocaleString('zh-CN',{hour12:false}):'未记录';
export function VerificationPanel({s,compact=false,onOpen}:{s:Data;compact?:boolean;onOpen?:()=>void}){
 const records:Data[]=s.verification_tracking?.sessions || [];
 const [selected,setSelected]=useState(''),[logs,setLogs]=useState<Data>(),[error,setError]=useState(''),[showLog,setShowLog]=useState(false),[refresh,setRefresh]=useState(0),[live,setLive]=useState(true);
 const runKey=s.topic+'/'+s.id;
 const session=records.find(r=>r.id===selected) || records[0];
 useEffect(()=>{setSelected('');setShowLog(false);setLogs(undefined)},[runKey]);
 useEffect(()=>{setLogs(undefined);setError('')},[session?.id]);
 useEffect(()=>{
  if(compact || !showLog || !session || !['session','job'].includes(session.source))return;
  let active=true;const abort=new AbortController();
  async function read(){try{
   const path=session.source==='job'?'job-log':'verification-log';
   const query=new URLSearchParams({key:runKey,...(session.source==='job'?{job:session.job_source}:{session:session.id})});
   const r=await fetch('/api/agent/'+path+'?'+query,{signal:abort.signal});const data=await r.json();if(!r.ok)throw Error(data.error || r.status);
   if(active){setLogs(data);setError('')}
  }catch(e){if(active)setError(String(e))}}
  void read();const timer=live?setInterval(read,5000):undefined;
  return()=>{active=false;abort.abort();if(timer)clearInterval(timer)};
 },[runKey,session?.id,showLog,refresh,live,compact]);
 if(!session)return <VStack gap={3}><Heading level={compact?3:2}>核验与验收</Heading><Text>当前尚无可读取的核验记录。后续检查由控制器、作业回执或执行智能体登记；尚未记录不表示已通过。</Text></VStack>;
 const checks:Data[]=session.checks || [];
 const completed=checks.filter(c=>['passed','failed','skipped'].includes(c.status)).length;
 const failures=checks.filter(c=>c.status==='failed');
 const current=checks.find(c=>c.status==='running') || checks.find(c=>c.status==='failed') || checks.find(c=>c.status==='unknown');
 return <VStack gap={4}>
  <HStack hAlign="between" wrap="wrap" gap={3}><Heading level={compact?3:2}>核验与验收</Heading>{compact&&onOpen&&<Button label="查看核验清单、证据与日志" onClick={onOpen} />}</HStack>
  {!compact&&<Selector label="查看哪次核验" hasSearch value={session.id} onChange={setSelected} options={records.map(r=>({value:r.id,label:`${r.is_current_task?'本工作项':'历史'} · ${labels[r.status] || r.status} · ${r.title} · ${date(r.started_at)}`}))} />}
  <HStack gap={4} wrap="wrap"><Text weight="semibold">{labels[session.status] || session.status}{session.stale?' · 采集已过期':''}</Text><Text type="supporting">{authority[session.authority] || session.authority} · {session.is_current_task?'本工作项':'前序工作项记录'}</Text><Text>已返回 {completed} / {checks.length} 项{failures.length?` · 失败 ${failures.length} 项`:''}</Text></HStack>
  <Text weight="semibold">{session.title} · {current?`当前检查：${current.label}`:session.status==='pending'?'等待逐项状态更新':'已保存本次检查结果'}</Text>
  <Text>核验对象：{session.object}</Text><Text type="supporting">范围：{session.scope}</Text><Text>{session.summary}</Text>
  <Text type="supporting">开始 {date(session.started_at)} · 最近进展 {date(session.updated_at)} · 最近采集 {date(session.observed_at)}</Text>
  {current?.completed!==undefined&&<Text>当前检查实测：{current.completed.toLocaleString()} / {current.total??'分母未确定'} {current.unit || '项'}</Text>}
  {(compact?failures.slice(0,1):[]).map(c=><Text key={c.id}>失败原因：{c.detail} · 证据：{c.evidence}</Text>)}
  {!compact&&<>
   <Table data={checks} textOverflow="wrap" columns={[
    {key:'label',header:'具体检查 / 通过依据',renderCell:(c:Data)=><VStack gap={1}><Text weight="semibold">{c.label}</Text><Text type="supporting">{c.criterion}</Text></VStack>},
    {key:'status',header:'实际状态',renderCell:(c:Data)=><VStack gap={1}><Text>{labels[c.status] || c.status}</Text>{c.authority&&<Text type="supporting">{authority[c.authority]}</Text>}{c.completed!==undefined&&<Text>{c.completed.toLocaleString()} / {c.total??'未知分母'} {c.unit || '项'}</Text>}</VStack>},
    {key:'detail',header:'结果 / 原始失败',renderCell:(c:Data)=><Text>{c.detail}</Text>},
    {key:'evidence',header:'证据与版本',renderCell:(c:Data)=><Text>{c.evidence}</Text>},
   ]} />
   <Text>下一步：{session.next_action}</Text><Text type="supporting">检查返回数只描述这份清单。命令回执、执行者报告与控制器验收分别标注，阶段验收以原科学契约为准。</Text>
   {['session','job'].includes(session.source)?<Button label={showLog?'收起核验日志':'查看核验原始日志'} onClick={()=>setShowLog(v=>!v)} />:<Text type="supporting">{session.source==='stage'?'此步骤尚未接入逐项核验记录，可在“作业与日志”查看已有控制台。':'旧账本没有逐项过程日志，保留已有验收结果；新核验自动记录过程。'}</Text>}
   {error&&<Text role="alert">{error}</Text>}
   {showLog&&<LogViewer text={logs?.text || ''} title={session.title+' / 核验日志'} metadata={logs?`更新 ${date(logs.updated_at)} · ${logs.bytes.toLocaleString()} 字节`:'正在读取核验日志…'} live={live} onLiveChange={setLive} onRefresh={()=>setRefresh(v=>v+1)} />}
  </>}
 </VStack>;
}
