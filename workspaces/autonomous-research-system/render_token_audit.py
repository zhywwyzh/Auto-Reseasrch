"""Render an offline, metadata-only token snapshot; no model/service calls."""
import argparse
import hashlib
import json
from pathlib import Path


def public_data(source):
    keys = ('version','cutoff_utc','generated_at','metric','scope','totals','by_scope','by_topic_scope',
            'by_model_scope','by_topic_phase','by_topic_model','campaigns','tasks',
            'request_count','duplicate_request_records_ignored','operations_without_request_usage','limitations')
    data = {k: source[k] for k in keys}
    data['inventory'] = dict(sessions=len(source['sessions']), operations=len(source['operations']),
        tasks=len(source['tasks']), files=len(source['sources']),
        operation_usage_status={k:sum(o['usage_status']==k for o in source['operations'])
            for k in sorted({o['usage_status'] for o in source['operations']})})
    data['reconciliation'] = dict(ledger_tokens=sum(c['tokens'] for c in source['campaigns']),
        ars_observed_tokens=sum(r['total_tokens'] for r in source['by_scope'] if r['scope']=='ars'))
    data['reconciliation']['difference'] = data['reconciliation']['ars_observed_tokens']-data['reconciliation']['ledger_tokens']
    return data


def render(data):
    payload = json.dumps(data,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>自动研究系统 Token 用量核算</title><style>
    *{box-sizing:border-box}body{margin:0;background:#f5f6f3;color:#173a3f;font:15px/1.75 system-ui,sans-serif}main{max-width:1500px;margin:auto;padding:32px 5vw 70px}h1{font-size:28px}h2{font-size:21px;margin-top:32px}a{color:#126970}.muted{color:#56696b}.stats{display:grid;grid-template-columns:repeat(3,1fr);gap:24px;margin:30px 0}.stats b{display:block;font-size:25px}.note{padding:16px 20px;background:#e8efeb;border-left:3px solid #126970}.filters{display:flex;gap:16px;flex-wrap:wrap;margin:20px 0}select,input{font:inherit;padding:8px;border:1px solid #b6c8c6;background:white;max-width:100%}.scroll{overflow:auto;max-height:680px;border:1px solid #d0dcda;background:white}table{border-collapse:collapse;width:100%;font-size:14px}th,td{padding:10px 14px;border-bottom:1px solid #dce4e1;text-align:left;white-space:nowrap}th{background:#eaf0ec;position:sticky;top:0}td.num{text-align:right;font-variant-numeric:tabular-nums}footer{margin-top:28px}.bars{display:grid;gap:10px;margin:20px 0}.barrow{display:grid;grid-template-columns:110px 1fr 150px;gap:16px;align-items:center}.barrow i{display:block;background:#28787c;height:14px}.chartCaption{font-size:13px;color:#56696b}button{font:inherit;padding:8px 12px;background:#e7efeb;color:inherit;border:1px solid #b6c8c6;cursor:pointer}@media(max-width:650px){main{padding:20px}.stats{grid-template-columns:1fr;gap:10px}.barrow{grid-template-columns:80px 1fr 105px}}
    </style></head><body><main><a href="runtime.html">返回研究操作台</a><h1>自动研究系统 · Token 用量核算</h1><p id="cutoff" class="muted"></p><div class="stats" id="stats"></div>
    <div class="note">总量＝输入＋输出。缓存输入已含在输入中，推理输出已含在输出中，均不重复相加。失败、重试及上下文压缩的逐请求记录计入；这是本地可核验的已观测下界，不是费用账单，也不是论文完成后的预测总量。</div>
    <h2>各课题累计用量</h2><div id="topics" class="scroll"></div><div id="bars" class="bars"></div><p class="chartCaption">总 token 按课题比较。横轴：token；纵轴：课题。共享会话未强行分摊。来源：ARS账本、逐请求用量与已登记协作会话；统计截止时间见页首。</p>
    <h2>实际使用模型</h2><div id="models" class="scroll"></div>
    <h2>阶段、任务与运行明细</h2><div class="filters"><label>课题 <select id="topic"><option value="all">全部课题</option></select></label><label>明细层级 <select id="view"><option value="stages">研究阶段</option><option value="tasks">逐任务（含所有尝试）</option><option value="runs">逐运行与账本差额</option></select></label><label>筛选 <input id="search" placeholder="任务名、阶段或运行编号"></label></div><div id="details" class="scroll"></div>
    <h2>统计完整性与差额</h2><p id="reconcile"></p><p id="inventory" class="muted"></p><div id="missing" class="scroll"></div><p>无逐请求用量的调用保持“未知”，不因错误或空回执推断为零。另有明确标记“不产生新模型调用”的前台实验，以及mock验收，分别计零模型token。</p><ul id="limits"></ul>
    <footer><a href="token-audit-2026-11-16.json" download>下载结构化统计 JSON</a> · 本页为固定快照，后台研究可能继续产生用量。未导出对话全文、推理或凭据。</footer></main><script type="application/json" id="data">''' + payload + '''</script><script>
    const D=JSON.parse(document.querySelector('#data').textContent);const fmt=n=>Number(n).toLocaleString('zh-CN');const phases={resolve:'定义与研究设计',candidate:'候选研究',implement:'代码实现与修改',prepare_implementation:'独立代码准备',validate:'实现验收与修复',pilot:'DEV／先导与修复',experiment:'正式实验',analyze:'结果分析',write:'论文写作',paper_review:'论文评价',plan:'研究计划',investigate:'资料研究',critic:'批判复核',synthesize:'阶段报告','outside-ledger':'账本外协作（无法拆阶段）',system_evolution:'系统自优化'};
    const name=x=>({SHARED:'共享／未分摊协作',SYSTEM:'系统自优化','ARS-DEMO':'系统连通性验收'})[x]||x;
    const table=(id,headers,rows)=>{const box=document.getElementById(id);box.replaceChildren();box.hidden=!rows.length;if(!rows.length)return;const t=document.createElement('table'),h=document.createElement('thead'),tr=document.createElement('tr');headers.forEach(x=>{const cell=document.createElement('th');cell.textContent=x;tr.append(cell)});h.append(tr);t.append(h);const b=document.createElement('tbody');rows.forEach(row=>{const tr=document.createElement('tr');row.forEach(x=>{const td=document.createElement('td');td.textContent=typeof x==='number'?fmt(x):x;if(typeof x==='number')td.className='num';tr.append(td)});b.append(tr)});t.append(b);box.append(t)};
    document.querySelector('#cutoff').textContent='统计截止：'+new Date(D.cutoff_utc).toLocaleString('zh-CN',{timeZone:'Asia/Shanghai',hour12:false})+'（北京时间） · '+fmt(D.request_count)+' 个去重请求';
    [['全部已观测 token',D.totals.total_tokens],['ARS自动流程 token',D.reconciliation.ars_observed_tokens],['缓存输入／输入占比',(100*D.totals.cached_input_tokens/D.totals.input_tokens).toFixed(2)+'%']].forEach(([label,value])=>{const box=document.createElement('div'),b=document.createElement('b'),text=document.createElement('span');b.textContent=typeof value==='number'?fmt(value):value;text.textContent=label;box.append(b,text);document.querySelector('#stats').append(box)});
    const topics=[...new Set(D.by_topic_scope.map(r=>r.topic))].sort();const summary=topics.map(topic=>{const xs=D.by_topic_scope.filter(r=>r.topic===topic);const get=scope=>xs.filter(r=>r.scope===scope).reduce((a,r)=>a+r.total_tokens,0);return[name(topic),get('ars'),get('outside-ledger'),get('system_evolution'),xs.reduce((a,r)=>a+r.total_tokens,0)]});table('topics',['课题','ARS流程','账本外协作','系统自优化','合计 token'],summary);
    const max=Math.max(...summary.map(r=>r[4]));summary.sort((a,b)=>b[4]-a[4]).forEach(r=>{const row=document.createElement('div');row.className='barrow';const label=document.createElement('span'),track=document.createElement('div'),bar=document.createElement('i'),v=document.createElement('span');label.textContent=r[0];v.textContent=fmt(r[4]);bar.style.width=(r[4]/max*100)+'%';track.append(bar);row.append(label,track,v);document.querySelector('#bars').append(row)});
    const models=[...new Set(D.by_model_scope.map(r=>r.model))];table('models',['模型（实际turn_context）','输入 token','其中缓存输入','输出 token','其中推理输出','合计 token'],models.map(model=>{const rs=D.by_model_scope.filter(r=>r.model===model);const sum=k=>rs.reduce((a,r)=>a+r[k],0);return[model,sum('input_tokens'),sum('cached_input_tokens'),sum('output_tokens'),sum('reasoning_output_tokens'),sum('total_tokens')]}));
    topics.forEach(topic=>{const o=document.createElement('option');o.value=topic;o.textContent=name(topic);document.querySelector('#topic').append(o)});
    function update(){const topic=document.querySelector('#topic').value,view=document.querySelector('#view').value,q=document.querySelector('#search').value.toLowerCase();const keep=r=>(topic==='all'||r.topic===topic)&&JSON.stringify(r).toLowerCase().includes(q);let headers,rows;
    if(view==='tasks'){headers=['课题','运行','阶段','任务','状态','尝试数','输入','缓存输入','输出','已观测合计','模型'];rows=D.tasks.filter(keep).sort((a,b)=>b.observed_usage.total_tokens-a.observed_usage.total_tokens).map(r=>[r.topic,r.campaign,phases[r.phase]||r.phase,r.title,r.status,r.attempts,r.observed_usage.input_tokens,r.observed_usage.cached_input_tokens,r.observed_usage.output_tokens,r.operations_without_usage?fmt(r.observed_usage.total_tokens)+'＋未知':r.observed_usage.total_tokens,r.models.join(' / ')||'无新模型／未记录']);}
    else if(view==='runs'){headers=['课题','运行','状态','操作槽位','原账本 token','逐请求 token','漏计差额','模型'];rows=D.campaigns.filter(keep).map(r=>[r.topic,r.id,r.status,r.calls,r.tokens,r.observed_usage.total_tokens,r.ledger_difference,r.models.join(' / ')||r.backend]);}
    else{headers=['课题','阶段','请求数','输入 token','缓存输入','输出 token','合计 token'];rows=D.by_topic_phase.filter(keep).sort((a,b)=>b.total_tokens-a.total_tokens).map(r=>[name(r.topic),phases[r.phase]||r.phase,r.requests,r.input_tokens,r.cached_input_tokens,r.output_tokens,r.total_tokens]);}table('details',headers,rows)}
    ['topic','view','search'].forEach(id=>document.getElementById(id).addEventListener(id==='search'?'input':'change',update));update();
    document.querySelector('#reconcile').textContent='ARS原账本 '+fmt(D.reconciliation.ledger_tokens)+' token；逐请求核对 '+fmt(D.reconciliation.ars_observed_tokens)+' token；补识别差额 '+fmt(D.reconciliation.difference)+' token。差额来自失败/中断调用未写最终usage、以及上下文压缩等请求。未修改原账本。';document.querySelector('#inventory').textContent=fmt(D.inventory.sessions)+' 个会话，'+fmt(D.inventory.operations)+' 条操作记录，'+fmt(D.inventory.tasks)+' 个任务。'+fmt(D.operations_without_request_usage.length)+' 条模型操作缺逐请求用量。';
    table('missing',['课题','运行','阶段','操作ID','状态'],D.operations_without_request_usage.map(r=>[r.topic,r.campaign,phases[r.phase]||r.phase,r.operation_id,r.state]));
    const limits=['统计是截至快照时刻的已发生用量，不是尚未完成论文的最终成本。','账本外协作仅能对已登记专题会话或独立worktree归属课题，混合系统会话保留为共享，无法严格拆成写作/代码/评价。','未落本地记录的当前对话、其他主机/账号及缺失记录不在统计内；模型名按历史上下文读取，不从当前配置倒推。','token包含反复读取的上下文，并非唯一文本字数；缓存命中和推理输出分别为输入、输出的子集，不能重复相加或直接推算账单。'];limits.forEach(x=>{const li=document.createElement('li');li.textContent=x;document.querySelector('#limits').append(li)});
    </script></body></html>'''


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',type=Path)
    parser.add_argument('--directory',type=Path,default=Path(__file__).resolve().parent)
    args=parser.parse_args(); data=public_data(json.loads(args.source.read_text()))
    body=json.dumps(data,ensure_ascii=False,indent=2)+'\n'
    (args.directory/'token-audit-2026-11-16.json').write_text(body)
    (args.directory/'token-audit-2026-11-16.html').write_text(render(data))
    print(json.dumps(dict(total_tokens=data['totals']['total_tokens'],json_sha256=hashlib.sha256(body.encode()).hexdigest(),cutoff=data['cutoff_utc'])))
