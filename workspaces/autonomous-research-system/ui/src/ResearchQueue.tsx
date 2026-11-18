import React from 'react';
import {VStack,HStack} from '@astryxdesign/core/Layout';
import {Text,Heading} from '@astryxdesign/core/Text';
import {Table,proportional,pixel} from '@astryxdesign/core/Table';
import {Button} from '@astryxdesign/core/Button';
import {Collapsible} from '@astryxdesign/core/Collapsible';
import {StatusPill} from './StatusPill';
type Data=Record<string,any>;
type Props={groups:Data[];history:Data[];states:Data;topics:Data[];onOpen:(key:string)=>void;onResults:(key:string)=>void;status:(key:string)=>string};
const date=(v:any)=>v?new Date(v).toLocaleString('zh-CN',{hour12:false}):'尚未启动';
export function ResearchQueue({groups,history,states,topics,onOpen,onResults,status}:Props){
  function rows(items:Data[]){return <Table data={items} textOverflow="wrap" hasHover columns={[
    {key:'topic',header:'研究课题',width:proportional(2,{minWidth:220}),renderCell:(c:Data)=><VStack gap={1}><Text weight="semibold">{topics.find(t=>t.id===c.topic)?.title || c.topic}</Text><Text type="supporting">{c.topic} · {c.id}</Text></VStack>},
    {key:'progress',header:'当前进展',width:proportional(3,{minWidth:260}),renderCell:(c:Data)=>{const s=states[c.key],p=s?.progress;const task=s?.tasks?.find((t:Data)=>t.id===p?.current_task?.id);return <VStack gap={1}><Text>{task?.title || p?.summary || '正在读取进度'}</Text><Text type="supporting">{task?.execution?.model || '尚未派发'}{s?.execution_observation?.agent?.last_output_at?' · 最近输出 '+date(s.execution_observation.agent.last_output_at):''}</Text></VStack>}},
    {key:'status',header:'运行状态',width:pixel(190),renderCell:(c:Data)=><VStack gap={2}><HStack><StatusPill state={c.status} label={status(c.status)} /></HStack><Text type="supporting">启动 {date(c.last_started_at)}</Text>{c.stopped_at && <Text type="supporting">停止 {date(c.stopped_at)} · {c.stop_reason || c.reason || '原因未记录'}</Text>}</VStack>},
    {key:'key',header:'操作',width:pixel(140),renderCell:(c:Data)=><VStack gap={2}><Button label="查看执行" onClick={()=>onOpen(c.key)} /><Button label="成果与论文" variant="ghost" onClick={()=>onResults(c.key)} /></VStack>},
  ]} />}
  return <VStack gap={6}>
    {groups.filter(g=>g.rows.length).map(g=><VStack key={g.title} gap={3}><HStack gap={3} vAlign="center"><Heading level={2}>{g.title}</Heading><Text type="supporting">{g.rows.length} 个运行</Text></HStack>{rows(g.rows)}</VStack>)}
    <Collapsible trigger={`历史运行（${history.length}）`} defaultIsOpen={false}><VStack gap={3} paddingBlock={3}><Text type="supporting">保留旧运行及停止记录，按实际启动时间排列。</Text>{history.length?rows(history):<Text>没有历史运行。</Text>}</VStack></Collapsible>
  </VStack>;
}
