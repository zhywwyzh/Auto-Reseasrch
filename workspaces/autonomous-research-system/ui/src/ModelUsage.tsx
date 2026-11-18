import React,{useState,useEffect} from 'react';
import {VStack,HStack} from '@astryxdesign/core/Layout';
import {Grid} from '@astryxdesign/core/Grid';
import {Text,Heading} from '@astryxdesign/core/Text';
import {TextInput} from '@astryxdesign/core/TextInput';
import {Table} from '@astryxdesign/core/Table';
import {Selector} from '@astryxdesign/core/Selector';
import {Button} from '@astryxdesign/core/Button';
import {Collapsible} from '@astryxdesign/core/Collapsible';
type Data=Record<string,any>;
const num=(x:any)=>typeof x==='number'?x.toLocaleString('zh-CN'):'未记录';
const date=(v:any)=>v?new Date(v).toLocaleString('zh-CN',{hour12:false}):'未记录';
const fields=[['input_tokens','输入'],['cached_input_tokens','其中缓存输入'],['output_tokens','输出'],['reasoning_output_tokens','其中推理输出'],['total_tokens','已观测总 Token']];
export function ModelUsage({runs,initialScope="all"}:{runs:Data[];initialScope?:string}){
 const [scope,setScope]=useState(initialScope),[model,setModel]=useState('all'),[data,setData]=useState<Data>(),[error,setError]=useState(''),[taskPage,setTaskPage]=useState(0),[taskQuery,setTaskQuery]=useState(''),[page,setPage]=useState(0),[revision,setRevision]=useState(0);
 const endpoint=scope==='all'?'/api/agent/usage-overview':'/api/agent/usage?key='+encodeURIComponent(scope);
 useEffect(()=>{
  const controller=new AbortController();let busy=false;
  setData(undefined);setError('');
  async function refresh(){
   if(busy)return;busy=true;
   try{const r=await fetch(endpoint,{signal:controller.signal});if(!r.ok)throw Error('用量读取失败 '+r.status);const value=await r.json();if(!controller.signal.aborted){setData(value);setError('')}}catch(e){if(!controller.signal.aborted)setError(String(e))}finally{busy=false}
  }
  void refresh();const timer=setInterval(refresh,15000);return()=>{controller.abort();clearInterval(timer)};
 },[endpoint,revision]);
 useEffect(()=>{setPage(0);setTaskPage(0)},[model,scope]);
 useEffect(()=>setTaskPage(0),[taskQuery]);
 const models=data?.models || [], selected=models.filter((m:Data)=>model==='all'||m.model===model);
 const totals=model==='all'?data?.totals:Object.fromEntries(fields.map(([f])=>[f,selected.reduce((n:number,m:Data)=>n+(m.usage?.[f]||0),0)]));
 const requests=(data?.requests || []).filter((r:Data)=>model==='all'||r.model===model).sort((a:Data,b:Data)=>(b.timestamp||'').localeCompare(a.timestamp||''));
 const pages=Math.max(1,Math.ceil(requests.length/50));
 const taskRows=(data?.tasks || []).filter((t:Data)=>(model==='all'||t.models?.includes(model))&&[t.title,t.key].join(' ').toLowerCase().includes(taskQuery.toLowerCase())).map((t:Data)=>({...t,displayUsage:model==='all'?t.usage:t.model_usage?.find((m:Data)=>m.model===model)}));
 const runRows=(scope==='all'?data?.runs || []:[]).map((r:Data)=>({...r,displayUsage:model==='all'?r.totals:r.models.filter((m:Data)=>m.model===model).reduce((a:Data,m:Data)=>Object.fromEntries(fields.map(([f])=>[f,(a[f]||0)+(m.usage?.[f]||0)])),{})}));
 const topicRows=Object.values(runRows.reduce((groups:Data,r:Data)=>{
   const group=groups[r.topic] ||= {topic:r.topic,runs:0,usage:{},request_count:0,missing:0,pending:0};
   group.runs++;group.request_count+=r.request_count;group.missing+=r.missing_attempts;group.pending+=r.pending_attempts;
   fields.forEach(([f])=>group.usage[f]=(group.usage[f]||0)+(r.displayUsage?.[f]||0));return groups;
 },{})) as Data[];
 const usageColumns=fields.map(([f,label])=>({key:f,header:label,renderCell:(r:Data)=><Text>{num((r.displayUsage || r.usage)?.[f])}</Text>}));
 return <VStack gap={6}>
  <HStack gap={4} wrap="wrap" hAlign="between">
   <VStack gap={2}><Heading level={2}>任务与模型 Token 消耗</Heading><Text type="supporting">研究调用按实际记录的模型归属；未记录实际模型的回执单独保留。</Text></VStack>
   <HStack gap={3} wrap="wrap"><Button label="刷新用量" onClick={()=>setRevision(v=>v+1)} /><Button label="导出完整用量 JSON" href={endpoint+(endpoint.includes('?')?'&':'?')+'download=1'} /></HStack>
  </HStack>
  <HStack gap={4} wrap="wrap">
   <Selector label="统计范围" value={scope} onChange={v=>{setScope(v);setModel('all')}} options={[{value:'all',label:'所有研究运行（含历史）'},...runs.filter(r=>r.topic!=='ARS-DEMO').map(r=>({value:r.key,label:r.topic+' / '+r.id}))]} />
   <Selector label="模型筛选" value={model} onChange={setModel} options={[{value:'all',label:'全部模型'},...[...new Set(models.map((m:Data)=>m.model))].map(m=>({value:String(m),label:String(m)}))]} />
  </HStack>
  {error&&<Text role="alert">{error}</Text>}
  {!data?<Text role="status">正在核对各模型的用量记录…</Text>:<>
   <Grid columns={{minWidth:170,max:5}} gap={5}>{fields.map(([f,label])=><VStack key={f} gap={2}><Text type="supporting">{label}</Text><Heading level={3}>{num(totals?.[f])}</Heading></VStack>)}</Grid>
   <Text type="supporting">{data.counting}</Text>
   <Text type="supporting">{data.scope} 最近核对：{date(data.sampled_at)} · 每15秒自动更新。</Text>
   <HStack gap={5} wrap="wrap"><Text>已记录模型请求：{num(data.request_count)}</Text><Text>缺少用量的调用：{num(data.missing_attempts)}</Text><Text>进行中或待核对的调用：{num(data.pending_attempts)}</Text></HStack>
   {(data.missing_attempts>0 || data.pending_attempts>0) && <Text>上述用量为已观测下界；缺失和未落盘的 token 尚未计入。</Text>}
   {scope==='all'&&<>
    <VStack gap={3}>
     <Heading level={3}>各课题累计消耗</Heading>
     <Text type="supporting">包含各课题所有历史运行；明细中的模型筛选同时作用于下方 token 分项。</Text>
     <Table data={topicRows} hasHover textOverflow="wrap" columns={[
      {key:'topic',header:'课题',renderCell:(r:Data)=><Text weight="semibold">{r.topic}</Text>},
      {key:'runs',header:'运行次数',renderCell:(r:Data)=><Text>{r.runs}</Text>},
      ...usageColumns,
      {key:'missing',header:'用量缺口',renderCell:(r:Data)=><Text type="supporting">缺失 {r.missing} · 待核对 {r.pending}</Text>},
     ]} />
    </VStack>
    <VStack gap={3}>
     <Heading level={3}>各研究运行消耗</Heading>
     <Table data={runRows} hasHover textOverflow="wrap" columns={[
      {key:'key',header:'研究运行',renderCell:(r:Data)=><Button label={r.key} onClick={()=>setScope(r.key)} />},
      {key:'models',header:'已记录模型',renderCell:(r:Data)=><Text>{r.models.map((m:Data)=>m.model).join('、')||'未记录'}</Text>},
      ...usageColumns,
      {key:'operation_count',header:'智能体调用 / 模型请求',renderCell:(r:Data)=><Text>{num(r.operation_count)} / {num(r.request_count)}</Text>},
     ]} />
    </VStack>
   </>}
   <VStack gap={3}>
    <Heading level={3}>模型用量账目</Heading>
    <Table data={selected} hasHover textOverflow="wrap" columns={[
     {key:'model',header:'实际模型',renderCell:(m:Data)=><Text weight="semibold">{m.model}</Text>},
     {key:'requests',header:'已记录模型请求数',renderCell:(m:Data)=><Text>{num(m.requests)}</Text>},
     ...fields.map(([f,label])=>({key:f,header:label,renderCell:(m:Data)=><Text>{num(m.usage?.[f])}</Text>})),
    ]} />
    {models.length===1&&<Text type="supporting">当前统计范围只观测到上述一种模型；新增模型调用会自动分行累计。</Text>}
   </VStack>
   <VStack gap={3}>
    <Heading level={3}>各工作项消耗</Heading>
    <Text type="supporting">工作项累计包含该项的失败、重试与修复调用。尚未派发显示0；缺失用量单独标出。</Text>
    <TextInput label="搜索工作项消耗" placeholder="任务名称或运行编号" value={taskQuery} onChange={setTaskQuery} />
    <Table data={taskRows.slice(taskPage*10,taskPage*10+10)} hasHover textOverflow="wrap" columns={[
     {key:'title',header:'具体任务 / 所属运行',renderCell:(r:Data)=><VStack gap={1}><Text weight="semibold">{r.title}</Text><Text type="supporting">{r.key || data.topic+' / '+data.run_id}</Text></VStack>},
     {key:'models',header:'实际模型',renderCell:(r:Data)=><Text type="supporting">{r.models?.join('、')||'尚无模型记录'}</Text>},
     ...usageColumns,
     {key:'attempt_count',header:'智能体调用',renderCell:(r:Data)=><Text>{num(r.attempt_count)}</Text>},
     {key:'missing',header:'用量缺口',renderCell:(r:Data)=><Text type="supporting">缺失 {r.missing_attempts} · 待核对 {r.pending_attempts}</Text>},
    ]} />
    <HStack gap={3} wrap="wrap"><Button label="上一页工作项" isDisabled={!taskPage} onClick={()=>setTaskPage(v=>v-1)} /><Text>第 {taskPage+1} / {Math.max(1,Math.ceil(taskRows.length/10))} 页 · 共 {taskRows.length} 个工作项</Text><Button label="下一页工作项" isDisabled={(taskPage+1)*10>=taskRows.length} onClick={()=>setTaskPage(v=>v+1)} /></HStack>
   </VStack>
   <VStack gap={3}>
    <Heading level={3}>逐请求 Token 记录</Heading>
    <Text type="supporting">一个智能体工作项会发出多次模型请求。以下每行是一条有独立请求编号的用量记录；仅有汇总回执的调用计入账目，但无法拆成逐请求行。</Text>
    <Table data={requests.slice(page*50,page*50+50)} hasHover textOverflow="wrap" columns={[
     {key:'timestamp',header:'时间 / 请求编号',renderCell:(r:Data)=><VStack gap={1}><Text>{date(r.timestamp)}</Text><Text type="supporting" style={{overflowWrap:'anywhere'}}>{r.response_id}</Text></VStack>},
     {key:'model',header:'模型 / 归属',renderCell:(r:Data)=><VStack gap={1}><Text weight="semibold">{r.model}</Text><Text type="supporting">{r.topic || data.topic} · {r.title}</Text><Text type="supporting">{r.model_basis==='response_metadata'?'响应元数据':'调用上下文记录'}</Text></VStack>},
     ...fields.map(([f,label])=>({key:f,header:label,renderCell:(r:Data)=><Text>{num(r.usage?.[f])}</Text>})),
    ]} />
    {!requests.length&&<Text>该范围暂无可展开的逐请求用量记录。</Text>}
    <HStack gap={3} wrap="wrap"><Button label="上一页" isDisabled={!page} onClick={()=>setPage(v=>v-1)} /><Text>第 {page+1} / {pages} 页 · 共 {num(requests.length)} 条 · 每页50条</Text><Button label="下一页" isDisabled={page+1>=pages} onClick={()=>setPage(v=>v+1)} /></HStack>
   </VStack>
   {!!data.warnings?.length&&<Collapsible trigger={`用量记录待核对事项（${data.warnings.length}）`} defaultIsOpen={false}><VStack gap={3} paddingBlock={3}>{data.warnings.map((w:string,i:number)=><Text key={i}>{w}</Text>)}</VStack></Collapsible>}
  </>}
 </VStack>;
}

export function TaskTokenSummary({usage,taskId}:{usage?:Data;taskId?:string}){
 const task=taskId?usage?.tasks?.find((t:Data)=>t.id===taskId):undefined;
 const value=taskId?task?.usage:usage?.totals;
 const missing=taskId?task?.missing_attempts:usage?.missing_attempts;
 const pending=taskId?task?.pending_attempts:usage?.pending_attempts;
 return <VStack gap={2}>
  <Text weight="semibold">{taskId?'此工作项':'本次研究运行'}累计 Token：{value?num(value.total_tokens):'正在读取'}</Text>
  {value&&<Text type="supporting">输入 {num(value.input_tokens)}（含缓存 {num(value.cached_input_tokens)}） · 输出 {num(value.output_tokens)}（含推理 {num(value.reasoning_output_tokens)}）</Text>}
  <Text type="supporting">智能体调用 {num(taskId?task?.attempt_count:usage?.operation_count)}{!taskId?` · 已记录模型请求 ${num(usage?.request_count)}`:''}{missing||pending?` · 缺失 ${missing||0} · 待核对 ${pending||0}，合计为已观测下界`:''}</Text>
 </VStack>;
}
