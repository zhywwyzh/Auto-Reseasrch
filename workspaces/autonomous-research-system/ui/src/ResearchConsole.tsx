// Frame adapted from Astryx incident-console: queue | 380-wide inspector.
// Keeps dashboard-progress's status band and section spacing; all data is live.
import React, {useState} from 'react';
import {Layout, LayoutHeader, LayoutContent, LayoutPanel, VStack, HStack} from '@astryxdesign/core/Layout';
import {Section} from '@astryxdesign/core/Section';
import {Text, Heading} from '@astryxdesign/core/Text';
import {Button} from '@astryxdesign/core/Button';
import {StatusDot} from '@astryxdesign/core/StatusDot';
import {TabList, Tab} from '@astryxdesign/core/TabList';
import {Table,proportional,pixel} from '@astryxdesign/core/Table';
import {Card} from '@astryxdesign/core/Card';
import {Grid} from '@astryxdesign/core/Grid';
import {Icon} from '@astryxdesign/core/Icon';
import {MetadataList, MetadataListItem} from '@astryxdesign/core/MetadataList';
import {Divider} from '@astryxdesign/core/Divider';
import {Collapsible} from '@astryxdesign/core/Collapsible';
import {Drawer, DrawerHeader} from '@astryxdesign/core/Drawer';
import {ProgressBar} from '@astryxdesign/core/ProgressBar';
import {useMediaQuery} from '@astryxdesign/core/hooks';
import {StageBoard, TaskRequirements} from './TaskWorkspace';
import {ExecutionObservation} from './ExecutionObservation';
import {VerificationPanel} from './VerificationPanel';
import {RecoveryPanel} from './RecoveryPanel';
import {RunModelRouting} from './ModelRouting';
import {TaskTokenSummary} from './ModelUsage';
import {StatusPill} from './StatusPill';

type Data=Record<string,any>;
type Props={s:Data;runKey:string;options:Data;invoke:(action:string,data:Data)=>Promise<Data>;onUsage:()=>void;progress:React.ReactNode};
const label:Data={RUNNING:'执行中',READY:'等待派发',STOPPED_USER:'已停止',STOPPED_BUDGET:'达到额度',WAITING_EXTERNAL:'等待条件',NEEDS_RECONCILIATION:'执行结果未确认',UNKNOWN:'执行结果未确认',FAILED:'失败',BLOCKED:'待处理',PENDING:'待执行',COMPLETED:'已完成',REVISION_REQUIRED:'需修订',NOT_CREATED:'尚未开始',running:'进行中',pending:'待执行',completed:'执行结束',failed:'失败',unknown:'结果未确认',blocked:'待处理'};
const date=(v:any)=>v?new Date(v).toLocaleString('zh-CN',{hour12:false}):'未记录';
const short=(value:any,length=180)=>{const s=String(value || '');return s.length>length?s.slice(0,length)+'…':s};

export function ResearchConsole({s,runKey,options,invoke,onUsage,progress}:Props) {
  const [tab,setTab]=useState('overview'),[taskId,setTaskId]=useState(''),[stepId,setStepId]=useState(''),[drawer,setDrawer]=useState(false);
  const narrow=useMediaQuery('(max-width: 1280px)');
  const p=s.progress || {},d=s.experiment_progress?.dashboard || {},o=s.execution_observation || {};
  const tasks:Data[]=s.tasks || [],stages:Data[]=p.stages || [];
  const current=tasks.find(t=>t.id===p.current_task?.id) || tasks.find(t=>t.status==='RUNNING') || tasks.at(-1);
  const selected=tasks.find(t=>t.id===taskId) || current;
  const selectedStep=d.steps?.find((r:Data)=>r.id===stepId);
  const currentStep=d.steps?.find((r:Data)=>r.id===d.current_step) || d.steps?.find((r:Data)=>r.status==='running');
  const live=!!o.agent?.process_alive;
  const stage=stages.find(r=>r.phase===current?.phase);
  const issues=tasks.filter(t=>['UNKNOWN','FAILED','BLOCKED'].includes(t.status) && !t.superseded_by && !t.recovering_by);
  const recovery=s.recovery_actions?.history?.find((r:Data)=>tasks.some(t=>t.id===r.result?.recovery_task_id && ['RUNNING','PENDING'].includes(t.status)));
  const message=o.agent_messages?.at(-1)?.text;
  const count=currentStep?.terminal ?? (Number.isInteger(currentStep?.completed) && Number.isInteger(currentStep?.failed) ? currentStep.completed+currentStep.failed : null);
  const selectTask=(id:string)=>{setTaskId(id);setStepId('');if(narrow)setDrawer(true)};
  const requireTask=(id:string)=>{setTaskId(id);setStepId('');setTab('requirements');setDrawer(false)};
  const recoverTask=(id:string)=>{setTaskId(id);setTab('recovery');setDrawer(false)};
  const inspector=<VStack gap={5}>
    <VStack gap={2}>
      <HStack gap={2} vAlign="center"><Icon icon="info" color="accent" size="sm" /><Text type="supporting">{selectedStep?'所选工作项':'执行详情'}</Text></HStack>
      <Heading level={3}>{selectedStep?.label || selected?.title || '尚未派发工作项'}</Heading>
      <HStack><StatusPill state={selectedStep?.status || selected?.status} label={label[selectedStep?.status || selected?.status] || selected?.status || '等待执行'} /></HStack>
    </VStack>
    {selectedStep?<>
      <Text>{selectedStep.detail || '等待执行者更新此工作项的具体说明。'}</Text>
      <MetadataList label={{position:'top'}}>
        <MetadataListItem label="计划依据"><Text>{selectedStep.target_basis || '尚未登记'}</Text></MetadataListItem>
        <MetadataListItem label="实测计数"><Text>{Number.isInteger(selectedStep.completed)?`${selectedStep.completed.toLocaleString()} 完成 · ${selectedStep.failed || 0} 失败`:'未接入计数'}</Text></MetadataListItem>
        <MetadataListItem label="说明更新"><Text>{date(d.updated_at)}</Text></MetadataListItem>
      </MetadataList>
    </>:<>
      <MetadataList label={{position:'top'}}>
        <MetadataListItem label="实际执行模型"><Text>{selected?.execution?`${selected.execution.backend} · ${selected.execution.model}`:'尚未派发'}</Text></MetadataListItem>
        <MetadataListItem label="调用开始"><Text>{date(selected?.execution?.started_at)}</Text></MetadataListItem>
        <MetadataListItem label="下次模型分配"><Text>{selected?.planned_model?.model || '执行器默认模型'} · {selected?.planned_model?.reason || '沿用当前策略'}</Text></MetadataListItem>
      </MetadataList>
      <HStack gap={2} wrap="wrap"><Button label="完整任务要求" onClick={()=>selected && requireTask(selected.id)} />{selected && ['UNKNOWN','FAILED','BLOCKED'].includes(selected.status) && <Button label="处理故障" variant="primary" onClick={()=>recoverTask(selected.id)} />}</HStack>
      {(selected?.error || selected?.execution?.reconciliation?.summary) && <Section variant="muted" padding={3}><Text>{selected.error || selected.execution.reconciliation.summary}</Text></Section>}
    </>}
    <Divider />
    <VStack gap={2}><Heading level={4}>下一步</Heading><Text>{d.next_action || p.next_action || '等待控制器确定后续工作。'}</Text>{d.blocker && <Text color="secondary">阻碍：{d.blocker}</Text>}</VStack>
    {message && <VStack gap={2}><Heading level={4}>执行者最新说明</Heading><Text>{short(message,260)}</Text><Button label="查看执行记录与日志" variant="ghost" onClick={()=>{setTab('jobs');setDrawer(false)}} /></VStack>}
    <Collapsible trigger="调用标识与用量" defaultIsOpen={false}><VStack gap={3} paddingBlock={3}>
      <Text as="p" style={{overflowWrap:'anywhere'}}>调用：{selected?.operation_id || '未派发'}</Text>
      <Text as="p" style={{overflowWrap:'anywhere'}}>会话：{selected?.execution?.thread_id || '尚无会话回执'}</Text>
      {selected && <TaskTokenSummary usage={s.token_usage} taskId={selected.id} />}
      <Button label="查看 Token 明细" onClick={onUsage} />
    </VStack></Collapsible>
  </VStack>;
  return <><Card padding={0}>
    <Layout height="auto" padding={0} header={<LayoutHeader padding={6} hasDivider>
      <VStack gap={4}>
        <HStack gap={3} hAlign="between" vAlign="start" wrap="wrap">
          <VStack gap={2} maxWidth="54rem">
            <HStack gap={2} vAlign="center"><StatusDot variant={live?'accent':issues.length?'warning':'neutral'} isPulsing={live} label={live?'执行进程在线':'执行状态见回执'} /><Text type="supporting">{stage?.label || '研究执行'} · {live?'执行进程在线':label[s.status] || s.status}</Text></HStack>
            <Heading level={2}>{currentStep?.label || current?.title || '等待研究工作项'}</Heading>
            <Text>{short(currentStep?.detail || d.summary || p.next_action || s.reason,220)}</Text>
          </VStack>
          <HStack gap={2} wrap="wrap"><Button label={recovery?'恢复正在进行':`故障与恢复${issues.length?' · '+issues.length:''}`} variant={issues.length?'primary':'secondary'} onClick={()=>setTab('recovery')} /><Button label="执行详情" onClick={()=>setDrawer(true)} /></HStack>
        </HStack>
        {typeof count==='number' && currentStep?.total>0 && <VStack gap={1}>
          <ProgressBar label={currentStep.label} value={count} max={currentStep.total} hasValueLabel formatValueLabel={(v,m)=>`${v.toLocaleString()} / ${m.toLocaleString()} · ${(100*v/m).toFixed(1)}%`} />
          <Text type="supporting">{currentStep.unit || '计数项'}进度 · {currentStep.status==='completed'?'该工作项已结束':'计数与工作项结束分别核对'} · 更新 {date(d.updated_at)}</Text>
        </VStack>}
        <Grid columns={{minWidth:190,max:3}} gap={3}>
          <Card variant="blue" padding={4}><VStack gap={2}><HStack gap={2} vAlign="center"><Icon icon="viewColumns" size="sm" color="blue" /><Text type="supporting">所处阶段</Text></HStack><Text weight="semibold">{stage?`${stages.indexOf(stage)+1} / ${stages.length} · ${stage.label}`:'尚未确定阶段'}</Text></VStack></Card>
          <Card padding={4}><VStack gap={2}><HStack gap={2} vAlign="center"><Icon icon="arrowsUpDown" size="sm" color="accent" /><Text type="supporting">实际执行模型</Text></HStack><Text weight="semibold">{current?.execution?.model || '尚未派发'}</Text><Text type="supporting">{o.jobs?.filter((r:Data)=>r.target==='research-server').some((r:Data)=>r.status==='running')?'服务器回执正在更新':o.jobs?.some((r:Data)=>r.target==='research-server')?'已有服务器返回记录':'暂无新的服务器观测'}</Text></VStack></Card>
          <Card padding={4}><VStack gap={2}><HStack gap={2} vAlign="center"><Icon icon="clock" size="sm" color="accent" /><Text type="supporting">最近执行输出</Text></HStack><Text weight="semibold">{date(o.agent?.last_output_at)}</Text><Text type="supporting">执行进程、日志与科学验收分别核对</Text></VStack></Card>
        </Grid>
      </VStack>
    </LayoutHeader>} content={<LayoutContent padding={0} isScrollable={false}>
    <Section padding={4} dividers={['bottom']}>
      <TabList value={tab} onChange={setTab} hasDivider={false}>
        {[['overview','执行总览'],['progress','实验进度'],['verifications','核验与验收'],['jobs','作业与日志'],['recovery','故障与恢复'],['requirements','任务要求'],['models','模型分工'],['tasks','全部工作项'],['events','运行记录']].map(([id,name])=><Tab key={id} value={id} label={name} />)}
      </TabList>
    </Section>
    <Layout height="auto" padding={0}
      content={<LayoutContent padding={0} isScrollable={false}>
        {tab==='overview' && <VStack gap={0}>
          <Section padding={6} dividers={['bottom']}><VerificationPanel s={s} compact onOpen={()=>setTab('verifications')} /></Section>
          <Section padding={6}><VStack gap={3}><HStack hAlign="between" wrap="wrap"><Heading level={3}>当前具体工作</Heading><Text type="supporting">{d.steps?.length || 0} 项已登记</Text></HStack>
            {d.steps?.length?<Table data={d.steps} hasHover textOverflow="wrap" columns={[
              {key:'label',header:'工作项',width:proportional(3,{minWidth:220}),renderCell:(r:Data)=><Text weight={r.status==='running'?'semibold':'normal'}>{r.label}</Text>},
              {key:'status',header:'状态',width:pixel(130),renderCell:(r:Data)=><StatusPill state={r.status} label={label[r.status] || r.status || '待执行'} />},
              {key:'total',header:'实测 / 计划',width:proportional(2,{minWidth:150}),renderCell:(r:Data)=><Text type="supporting">{Number.isInteger(r.completed)?`${r.completed.toLocaleString()} / ${r.total?.toLocaleString() || '未知'}`:'待接入计数'}</Text>},
              {key:'id',header:'详情',width:pixel(88),renderCell:(r:Data)=><Button label="查看" icon={<Icon icon="chevronRight" size="sm" />} variant="ghost" onClick={()=>{setStepId(r.id);if(narrow)setDrawer(true)}} />},
            ]} />:<Text color="secondary">{d.summary || '当前调用尚未登记工作项；不估算进度。'}</Text>}
          </VStack></Section>
          <Section padding={6} dividers={['bottom']}><StageBoard s={s} compact onSelect={selectTask} onRecover={recoverTask} /></Section>
        </VStack>}
        {tab==='progress' && <Section padding={6}>{progress}</Section>}
        {tab==='verifications' && <Section padding={6}><VerificationPanel s={s} /></Section>}
        {tab==='jobs' && <Section padding={6}><ExecutionObservation s={s} jobsOnly /></Section>}
        {tab==='recovery' && <Section padding={6}><RecoveryPanel s={s} runKey={runKey} invoke={invoke} focusTaskId={taskId} /></Section>}
        {tab==='requirements' && <Section padding={6}><TaskRequirements s={s} runKey={runKey} task={selected} onSelect={setTaskId} save={data=>invoke('supplement',{key:runKey,...data})} /></Section>}
        {tab==='models' && <Section padding={6}><RunModelRouting s={s} options={options.model_routing} save={(policy,default_model)=>invoke('model-policy',{key:runKey,policy,default_model})} /></Section>}
        {tab==='tasks' && <Section padding={6}><VStack gap={3}><Heading level={3}>全部工作项</Heading><Table data={tasks} hasHover textOverflow="wrap" columns={[
          {key:'title',header:'工作项',renderCell:(t:Data)=><Text>{t.title}</Text>},
          {key:'status',header:'状态',renderCell:(t:Data)=><StatusPill state={t.status} label={label[t.status] || t.status} />},
          {key:'id',header:'操作',renderCell:(t:Data)=><HStack gap={2} wrap="wrap"><Button label="任务详情" onClick={()=>requireTask(t.id)} />{['UNKNOWN','FAILED','BLOCKED'].includes(t.status) && <Button label="处理故障" onClick={()=>recoverTask(t.id)} />}</HStack>},
        ]} /></VStack></Section>}
        {tab==='events' && <Section padding={6}><VStack gap={3}><Heading level={3}>运行记录</Heading><Table data={s.events || []} textOverflow="wrap" columns={[
          {key:'created_at',header:'时间',renderCell:(r:Data)=><Text type="supporting">{date(r.created_at)}</Text>},
          {key:'type',header:'事件',renderCell:(r:Data)=><Text>{r.type}</Text>},
          {key:'payload',header:'详情',renderCell:(r:Data)=><Text as="p" style={{overflowWrap:'anywhere'}}>{typeof r.payload==='string'?r.payload:JSON.stringify(r.payload)}</Text>},
        ]} /></VStack></Section>}
      </LayoutContent>}
      end={!narrow && ['overview','tasks'].includes(tab)?<LayoutPanel width={380} padding={4} hasDivider isScrollable={false} label="执行详情">{inspector}</LayoutPanel>:undefined} />
    </LayoutContent>} /></Card>
    <Drawer isOpen={drawer} onOpenChange={setDrawer} label="执行详情" width={420} padding={0}>
      <Layout header={<DrawerHeader title="执行详情" onOpenChange={setDrawer} />} content={<LayoutContent padding={6}>{inspector}</LayoutContent>} />
    </Drawer>
  </>;
}
