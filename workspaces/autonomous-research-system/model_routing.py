"""Deterministic, user-configured model routing at operation reservation.

Model choice is engineering configuration, never a scientific/resource grant.
Existing requests remain immutable; no automatic expensive-model escalation.
"""
import copy
import hashlib
import json
import re

VERSION = 'stage-model-routing-v1'
ROLES = {
    'exploration': ('创新探索与文献判断', 'high'),
    'design': ('方案与协议设计', 'high'),
    'engineering': ('代码实现与修改', 'standard'),
    'execution': ('按方案执行与实验', 'standard'),
    'analysis': ('证据分析与结论推导', 'high'),
    'writing': ('论文写作与整合', 'high'),
    'review': ('独立批判与论文点评', 'high'),
}
PHASE_ROLES = {
    'plan':'design','resolve':'exploration','investigate':'exploration','candidate':'design',
    'implement':'engineering','prepare_implementation':'engineering','code_repair':'engineering',
    'validate':'execution','pilot':'execution','experiment':'execution',
    'analyze':'analysis','write':'writing','synthesize':'writing','critic':'review','paper_review':'review',
}
PHASE_LABELS = {'plan':'研究计划','resolve':'创新与问题定义','investigate':'资料探索','candidate':'候选方案',
    'implement':'代码实现','prepare_implementation':'实现准备','code_repair':'代码修复','validate':'验证执行',
    'pilot':'先导实验','experiment':'正式实验','analyze':'分析','write':'论文写作','synthesize':'报告整合',
    'critic':'独立批判','paper_review':'论文终审'}


def model_name(value):
    if not isinstance(value,str) or (value and not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/+\-]{0,199}',value)):
        raise ValueError('模型标识须为不超过200位的字母、数字及 . _ : / + -，不能包含空白或命令参数')
    return value


def normalize(raw):
    if raw is None:
        return {'version':VERSION,'enabled':False,'profiles':{},'phase_profiles':{},'phase_overrides':{},'task_overrides':{}}
    if not isinstance(raw,dict) or set(raw)-{'version','enabled','profiles','phase_profiles','phase_overrides','task_overrides'}:
        raise ValueError('模型分配配置格式无效')
    if raw.get('version',VERSION)!=VERSION or type(raw.get('enabled',False)) is not bool:
        raise ValueError('模型分配版本或开关无效')
    result=normalize(None);result['enabled']=raw.get('enabled',False)
    for name in ('profiles','phase_profiles','phase_overrides','task_overrides'):
        values=raw.get(name,{})
        if not isinstance(values,dict) or len(values)>1000:
            raise ValueError('模型分配映射无效：'+name)
        for key,value in values.items():
            if not isinstance(key,str) or not key or len(key)>100:
                raise ValueError('模型分配目标无效')
            if name=='profiles' and key not in ('high','standard'):
                raise ValueError('未知模型档位')
            if name in ('phase_profiles','phase_overrides') and key not in PHASE_ROLES:
                raise ValueError('未知模型分配阶段')
            if name=='phase_profiles':
                if value not in ('high','standard','default','custom'):
                    raise ValueError('阶段工作档位须为高性能、中等性能、默认或单独模型')
                result[name][key]=value
                continue
            result[name][key]=model_name(value)
    for phase,profile in result['phase_profiles'].items():
        if profile=='custom' and not result['phase_overrides'].get(phase):
            raise ValueError('单独指定模型的阶段必须填写模型标识：'+PHASE_LABELS[phase])
    return result


def select(config,task):
    policy=normalize(config.get('model_policy'))
    phase=task['phase'];role=PHASE_ROLES.get(phase)
    recommended=ROLES[role][1] if role else None
    profile=policy['phase_profiles'].get(phase,recommended)
    selected=config.get('model') or ''
    basis='默认模型';rule='default'
    if policy['enabled']:
        choices=[(policy['task_overrides'].get(task['id']),'task_override','工作项单独指定'),
                 (policy['phase_overrides'].get(phase),'phase_override','阶段单独指定'),
                 (policy['profiles'].get(profile) if profile in ('high','standard') else None,'profile',
                  ('阶段自行选择的' if phase in policy['phase_profiles'] else '阶段建议的')+('高性能' if profile=='high' else '中等性能')+'档位')]
        for value,rule_name,label in choices:
            if value:
                selected,basis,rule=value,label,rule_name;break
    return {'version':VERSION,'model':selected,'phase':phase,'role':role,'profile':profile,'recommended_profile':recommended,
            'rule':rule,'reason':basis if selected else '继承执行器本机默认模型',
            'policy_sha256':hashlib.sha256(json.dumps(policy,sort_keys=True).encode()).hexdigest()}


def bind_request(request):
    task=request['context']['task']
    assignment=select(request['config'],task)
    request['config']=copy.deepcopy(request['config'])
    request['config']['model']=assignment['model']
    request['model_assignment']=assignment
    request['context']['model_assignment']=assignment
    return request


def apply_argv(argv,request):
    # Chosen request model, not mutable campaign settings, owns this invocation.
    args=[];index=0
    while index<len(argv):
        value=argv[index]
        if value=='--model':index+=2;continue
        if value.startswith('--model='):index+=1;continue
        args.append(value);index+=1
    if request['config'].get('model'):args+=['--model',request['config']['model']]
    return args


def save(store,raw,default_model=None):
    import ars
    policy=normalize(raw)
    task_ids={t['id'] for t in store.tasks()}
    if set(policy['task_overrides'])-task_ids:
        raise ValueError('模型分配包含其他运行或不存在的工作项')
    if default_model is not None:model_name(default_model)
    with store.tx():
        config=store.state()['config'];before=config.get('model_policy')
        config['model_policy']=policy
        if default_model is not None:config['model']=default_model
        store.db.execute('UPDATE campaign SET config=?',(ars.dump(config),))
        store.event('model_policy.updated',{'previous':before,'policy':policy,'default_model':config.get('model'),
                    'effective':'next reservation only; existing requests unchanged'})
    return {'policy':policy,'default_model':config.get('model'),'effective':'下一次新调用起生效，已派发请求保持原模型'}


def describe(store,out):
    config=out['config']
    out['model_policy']=normalize(config.get('model_policy'))
    for task in out['tasks']:
        task['planned_model']=select(config,task)
    out['model_routes']=[dict(label=PHASE_LABELS[phase],**select(config,{'id':'','phase':phase}))
                         for phase in PHASE_ROLES]
    return out


def options():
    return {'version':VERSION,'roles':{k:dict(label=v[0],profile=v[1]) for k,v in ROLES.items()},
            'phases':[dict(phase=p,label=PHASE_LABELS[p],role=r,profile=ROLES[r][1]) for p,r in PHASE_ROLES.items()]}
