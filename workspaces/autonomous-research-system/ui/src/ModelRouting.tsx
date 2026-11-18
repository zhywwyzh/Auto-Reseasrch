import React,{useState} from 'react';
import {VStack,HStack} from '@astryxdesign/core/Layout';
import {Grid} from '@astryxdesign/core/Grid';
import {Text,Heading} from '@astryxdesign/core/Text';
import {Selector} from '@astryxdesign/core/Selector';
import {TextInput} from '@astryxdesign/core/TextInput';
import {Button} from '@astryxdesign/core/Button';
import {Table} from '@astryxdesign/core/Table';
import {Collapsible} from '@astryxdesign/core/Collapsible';
type Data=Record<string,any>;
export const emptyModelPolicy=()=>({version:'stage-model-routing-v1',enabled:false,profiles:{},phase_profiles:{},phase_overrides:{},task_overrides:{}});
export function ModelRoutingFields({policy,onChange,defaultModel,onDefault,options,tasks=[],disabled=false}:{policy:Data;onChange:(p:Data)=>void;defaultModel:string;onDefault:(v:string)=>void;options?:Data;tasks?:Data[];disabled?:boolean}){
 const [task,setTask]=useState('');
 const phases=options?.phases || [];
 const mapping=(key:string,id:string,value:string)=>onChange({...policy,[key]:{...(policy[key]||{}),[id]:value}});
 const choice=(r:Data)=>policy.phase_overrides?.[r.phase]?'custom':policy.phase_profiles?.[r.phase] || 'recommended';
 function setChoice(r:Data,value:string){
  const profiles={...(policy.phase_profiles||{})},overrides={...(policy.phase_overrides||{})};
  if(value==='recommended')delete profiles[r.phase];else profiles[r.phase]=value;
  if(value!=='custom')delete overrides[r.phase];
  onChange({...policy,phase_profiles:profiles,phase_overrides:overrides});
 }
 function preview(r:Data){const tier=policy.phase_profiles?.[r.phase] || r.profile;return policy.phase_overrides?.[r.phase] || ((tier==='high'||tier==='standard')?policy.profiles?.[tier]:'') || defaultModel || '执行器默认模型'}
 return <VStack gap={4}>
  <Heading level={3}>模型与阶段分工</Heading>
  <Selector label="模型分配方式" value={policy.enabled?'staged':'single'} isDisabled={disabled} onChange={v=>onChange({...policy,enabled:v==='staged'})} options={[{value:'single',label:'整个运行使用默认模型'},{value:'staged',label:'按研究阶段分配多个模型'}]} />
  <TextInput label="默认模型（留空继承执行器默认）" value={defaultModel} onChange={onDefault} isDisabled={disabled} />
  {policy.enabled&&<>
   <Grid columns={{minWidth:260,max:2}} gap={5}>
    <TextInput label="高性能模型" placeholder="填写当前执行器可用的模型标识" value={policy.profiles?.high||''} onChange={v=>mapping('profiles','high',v)} isDisabled={disabled} />
    <TextInput label="中等性能模型" placeholder="填写用于代码与执行工作的模型标识" value={policy.profiles?.standard||''} onChange={v=>mapping('profiles','standard',v)} isDisabled={disabled} />
   </Grid>
   <Text type="supporting">每个阶段都可以自行选择档位或单独模型。建议分工只是初始值；未填写的档位回退到默认模型。</Text>
   <Button label="恢复全部阶段的建议分工" isDisabled={disabled} onClick={()=>onChange({...policy,phase_profiles:{},phase_overrides:{}})} />
   <Table data={phases} hasHover textOverflow="wrap" columns={[
    {key:'phase',header:'流程阶段',renderCell:(r:Data)=><Text>{r.label}</Text>},
    {key:'profile',header:'选择工作档位',renderCell:(r:Data)=><Selector label={r.label+'工作档位'} value={choice(r)} onChange={v=>setChoice(r,v)} isDisabled={disabled} options={[
      {value:'recommended',label:`使用建议（${r.profile==='high'?'高性能':'中等性能'}）`},
      {value:'high',label:'高性能'}, {value:'standard',label:'中等性能'},
      {value:'default',label:'使用默认模型'}, {value:'custom',label:'单独指定模型'},
    ]} />},
    {key:'model',header:'将用于新调用的模型',renderCell:(r:Data)=>choice(r)==='custom'?<TextInput label={r.label+'单独模型'} value={policy.phase_overrides?.[r.phase]||''} onChange={v=>mapping('phase_overrides',r.phase,v)} placeholder="填写该阶段使用的模型标识" isDisabled={disabled} />:<Text weight="semibold">{preview(r)}</Text>},
   ]} />
   {!!tasks.length&&<Collapsible trigger="单独指定某个工作项" defaultIsOpen={false}>
    <VStack gap={4} paddingBlock={3}>
     {!!tasks.length&&<Selector label="覆盖哪个工作项" value={task} onChange={setTask} options={[{value:'',label:'选择工作项'},...tasks.map((t:Data)=>({value:t.id,label:t.title}))]} isDisabled={disabled} />}
     {task&&<TextInput label="该工作项单独使用的模型" value={policy.task_overrides?.[task]||''} onChange={v=>mapping('task_overrides',task,v)} description="工作项指定优先于阶段指定；只影响后续新调用。留空恢复阶段规则。" isDisabled={disabled} />}
    </VStack>
   </Collapsible>}
  </>}
 </VStack>;
}
export function RunModelRouting({s,options,save}:{s:Data;options?:Data;save:(policy:Data,model:string)=>Promise<Data>}){
 const [policy,setPolicy]=useState<Data>(s.model_policy||emptyModelPolicy()),[model,setModel]=useState(s.config?.model||'');
 const [busy,setBusy]=useState(false),[notice,setNotice]=useState(''),[error,setError]=useState('');
 async function submit(){setBusy(true);setError('');try{const receipt=await save(policy,model);setPolicy(receipt.policy);setModel(receipt.default_model||'');setNotice('模型分配已保存。'+receipt.effective)}catch(e){setError(String(e));}finally{setBusy(false)}}
 return <VStack gap={5}>
  <Text>为本次研究的流程配置执行模型。保存后从下一次新调用生效；不会启动研究、重投在途调用或改变预算。</Text>
  <ModelRoutingFields policy={policy} onChange={setPolicy} defaultModel={model} onDefault={setModel} options={options} tasks={s.tasks} disabled={busy} />
  <Button label={busy?'正在保存模型分配…':'保存模型分配'} variant="primary" isDisabled={busy} onClick={submit} />
  {notice&&<Text role="status">{notice}</Text>}{error&&<Text role="alert">{error}</Text>}
  <Heading level={3}>当前工作项的后续调用分配</Heading>
  <Table data={s.tasks || []} textOverflow="wrap" columns={[
   {key:'title',header:'工作项',renderCell:(t:Data)=><Text>{t.title}</Text>},
   {key:'planned',header:'下一次新调用模型',renderCell:(t:Data)=><Text>{t.planned_model?.model||'执行器默认模型'}</Text>},
   {key:'reason',header:'分配依据',renderCell:(t:Data)=><Text type="supporting">{t.planned_model?.reason||'默认'}</Text>},
   {key:'actual',header:'最近调用使用的模型',renderCell:(t:Data)=><Text type="supporting">{t.execution?.model||'尚未派发'}</Text>},
  ]} />
 </VStack>;
}
