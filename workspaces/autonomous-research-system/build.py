#!/usr/bin/env python3
"""Render the research-system design. No network, agent calls, or research jobs."""
import hashlib
import html
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
esc = lambda x: html.escape(str(x), quote=True)


def load(name):
    return json.loads((ROOT / name).read_text())


def paras(values):
    return ''.join('<p>' + esc(x) + '</p>' for x in values)


def items(values):
    return '<ul>' + ''.join('<li>' + esc(x) + '</li>' for x in values) + '</ul>'


def table(headers, rows):
    return '<div class="table-wrap"><table><thead><tr>' + ''.join('<th scope="col">' + esc(h) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + esc(c) + '</td>' for c in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def section(key, title, content, lead=''):
    return '<section id="' + key + '"><p class="eyebrow">' + key.upper() + '</p><h2>' + title + '</h2>' + ('<p class="lead">' + esc(lead) + '</p>' if lead else '') + content + '</section>'


def render_figure(d):
    f=d['report_figure']
    ink,muted,accent,line,paper,wash='#16373c','#50656a','#146269','#ccd9d5','#f7f8f4','#e5eeea'
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080" role="img" aria-labelledby="title desc">',
         '<title id="title">'+esc(f['title'])+'</title><desc id="desc">六步研究闭环连接持久研究记忆，由方向保持、执行恢复和课题隔离共同支撑。设计方案，未部署。</desc>',
         '<defs><marker id="arrow" markerWidth="10" markerHeight="10" refX="8" refY="5" orient="auto-start-reverse"><path d="M1,1 L9,5 L1,9" fill="none" stroke="'+accent+'" stroke-width="1.8"/></marker></defs>',
         '<rect width="1920" height="1080" fill="'+paper+'"/>',
         '<g font-family="Noto Sans CJK SC, sans-serif">']

    def text(x,y,value,size=22,color=ink,weight=400,anchor='start'):
        svg.append(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" font-weight="{weight}" text-anchor="{anchor}">{esc(value)}</text>')

    def rect(x,y,w,h,fill=paper,stroke=line,r=8):
        svg.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>')

    def arrow(x1,y1,x2,y2):
        svg.append(f'<path d="M{x1},{y1} L{x2},{y2}" fill="none" stroke="{accent}" stroke-width="2.5" marker-end="url(#arrow)"/>')

    text(80,90,f['title'],42,weight=700)
    text(80,139,f['subtitle'],23,muted)
    rect(1510,112,330,43,wash,wash,5);text(1675,141,f['status'],20,accent,500,'middle')
    text(80,207,'研究任务闭环',18,accent,600)
    for i,n in enumerate(f['pipeline']):
        x=80+i*300;dark=i==2
        rect(x,235,260,200,accent if dark else '#ffffff',accent if dark else line)
        text(x+24,271,'0'+str(i+1),17,'#c6e5e0' if dark else muted,500)
        text(x+24,317,n['title'],27,'#ffffff' if dark else ink,600)
        for j,t in enumerate(n['lines']):text(x+24,365+j*33,t,19,'#e2f2ee' if dark else muted)
        if i<5:arrow(x+270,335,x+289,335)
    arrow(210,535,210,448);text(232,493,'状态驱动下一步',19,accent)
    arrow(510,535,510,448);text(532,493,'按任务读取',19,accent)
    arrow(1410,448,1410,535);text(1432,493,'验收与结论入账',19,accent)
    rect(80,550,1760,205,wash,line)
    text(112,599,f['memory_title'],29,accent,600)
    text(112,642,f['memory_subtitle'],22,muted)
    text(1808,598,'事件账本 / 当前投影 / 证据依赖图',19,muted,400,'end')
    for i,name in enumerate(f['memory_types']):
        x=112+i*244
        if i:svg.append(f'<path d="M{x-16},682 L{x-16},716" stroke="{line}" stroke-width="2"/>')
        text(x,707,name,24,ink,500)
    text(80,806,'支撑长期运行的三项机制',18,accent,600)
    for i,c in enumerate(f['controls']):
        x=80+i*600
        svg.append(f'<path d="M{x},826 L{x+550},826" stroke="{line}" stroke-width="2"/>')
        text(x,866,c['title'],26,accent,600)
        for j,t in enumerate(c['lines']):text(x,909+j*34,t,21,muted)
    svg.append(f'<path d="M80,985 L1840,985" stroke="{line}" stroke-width="1.5"/>')
    text(80,1025,f['takeaway'],24,ink,600)
    text(80,1061,'ARS-DESIGN-001 · 2026-11-11 · 模块与流程均为设计；方法来源与证据边界见配套HTML说明。',16,muted)
    svg.append('</g></svg>')
    return '\n'.join(svg)+'\n'


def render_html(d, audit, replay, digest):
    nav = [('diagram','汇报说明图'),('overview','设计结论'),('architecture','系统架构'),('memory','记忆与方向'),('history','历史与初始化'),('workflow','研究闭环'),('recovery','执行与恢复'),('interfaces','接口与存储'),('acceptance','验收与演练'),('roadmap','实施顺序'),('sources','来源与边界')]
    body = section('overview','研究可以持续，会话可以替换',paras(d['summary']) + '<div class="notice">' + esc(d['meta']['status']) + '。' + esc(d['meta']['non_goals']) + '</div><h3>必须守住的八项约定</h3>' + table(['约定','执行规则'],[[x['id']+' · '+x['title'],x['rule']] for x in d['invariants']]))
    figure='<figure class="report-figure"><a href="figures/system-overview.svg" target="_blank" rel="noopener" aria-label="新窗口查看系统说明图"><img src="figures/system-overview.svg" width="1920" height="1080" alt="六步研究任务闭环连接持久研究记忆；由方向保持、执行恢复、课题隔离三项机制支撑。设计方案，未部署。"></a><figcaption>16:9汇报图。点击可单独查看；图中模块与流程均为设计，不表示系统已部署。</figcaption></figure><p class="figure-downloads"><a href="figures/system-overview.png" download>下载高清PNG · 3840×2160</a><a href="figures/system-overview.svg" download>下载可编辑SVG</a></p><p>汇报讲解：系统先把研究目标与边界写成契约，再由短会话完成具体任务。经过独立验收的产物、证据和失败原因写入持久记忆，驱动下一轮任务；会话更换不会重新定义研究方向。</p>'
    body=section('diagram','一张图说明长期研究如何持续',figure)+body
    layers = '<div class="flow" aria-label="系统数据流">用户指令 → 契约与调度 → 上下文组装 → 研究执行器 → 工具/实验 → 独立验收 → 事件账本<br>事件账本 → 当前投影与记忆索引 → 下一任务 / 阅读界面</div>'
    for i,x in enumerate(d['layers'],1):
        layers += '<article class="layer"><div class="number">0'+str(i)+'</div><div><h3>'+esc(x['name'])+'</h3><p>'+esc(x['purpose'])+'</p>'+items(x['components'])+'<p class="meta">输入：'+esc(x['input'])+'<br>输出：'+esc(x['output'])+'</p><p class="boundary">'+esc(x['boundary'])+'</p></div></article>'
    body += section('architecture','六层架构，单课题单写者',layers,'第一版可用一个执行器顺序承担不同角色。系统耐久性由控制平面与账本提供，多智能体数量本身不是目标。')
    memory = table(['记忆类型','保存什么','怎样更新','何时读取'],[[x['name'],x['content'],x['write'],x['read']] for x in d['memory']['classes']])
    memory += '<details><summary>共同字段：来源、时间、版本与依赖</summary><pre>'+esc(', '.join(d['memory']['common_fields']))+'</pre></details><h3>每轮如何读取</h3>'+items(d['memory']['retrieval'])+'<h3>如何更新、纠错和重开路线</h3>'+items(d['memory']['updates'])
    body += section('memory','记得目标，也记得为何放弃',memory,'外部长期记忆与本轮上下文分开；摘要可以重写，有效约束和原始证据不能随摘要消失。')
    hist = '<div class="stats">'+''.join('<div><strong>'+str(audit[k])+'</strong><span>'+label+'</span></div>' for k,label in [('rollout_files','匹配会话文件'),('distinct_session_ids','不同会话ID'),('visible_user_records','非空可见用户记录'),('compacted_records','压缩事件记录')])+'</div><p class="meta">来源：本机匹配仓库 cwd 的只读会话快照；审计时间 '+esc(audit['audited_at_utc'])+'。这些不是独立实验数或模型调用数。</p>'
    hist += '<p>'+esc(d['history_import']['role'])+'</p><ol>'+''.join('<li>'+esc(x)+'</li>' for x in d['history_import']['steps'])+'</ol><p class="boundary">'+esc(d['history_import']['privacy'])+'</p><details><summary>审计口径与覆盖限制</summary>'+paras([audit['discovery'],audit['counting']])+items(audit['limits'])+'</details><p><a href="history-audit.json">审计清单、文件快照哈希与记录数</a></p>'
    body += section('history','用真实历史建立研究记忆',hist,'历史尤其适合恢复“当时为何如此决策”，并构造不泄漏未来答案的记忆验收。它不自动证明历史助手的结论正确。')
    w=d['workflow']
    work = table(['阶段','做什么','退出条件'],[[x['name'],x['work'],x['exit']] for x in w['research_phases']])+'<h3>研究阶段与运行状态分开</h3>'+table(['运行状态','含义'],w['runtime_states'])+'<p>'+esc(w['selection'])+'</p><h3>三个课题的接入快照</h3>'
    for x in w['topic_tracks']:
        work += '<article><h4>'+esc(x['topic'])+' · <a href="'+esc(x['source'])+'">当前源记录</a></h4>'+paras([x['snapshot'],x['contract'],x['next']])+'</article>'
    work += '<p class="meta">'+esc(w['snapshot_note'])+'</p><h3>每轮检查是否仍在推进原问题</h3>'+items(w['alignment_review'])+'<p>'+esc(w['claim_states'])+'</p><h3>不同研究类型使用不同协议</h3>'+paras([w['survey_track'],w['theory_track']])
    body += section('workflow','把研究推进变成有退出条件的任务',work)
    recover='<h3>一次研究任务的完整生命周期</h3><ol>'+''.join('<li>'+esc(x)+'</li>' for x in d['episode']['steps'])+'</ol>'+paras([d['episode']['partial_commit'],d['episode']['cancellation']])+'<h3>长时运行需要的执行机制</h3>'+table(['问题','设计'],[[x['name'],x['design']] for x in d['reliability']])
    body += section('recovery','恢复时先查发生过什么',recover,'任务重放只重建状态。外部调用与训练是否已经发生，必须用持久回执和 operation_id 核对。')
    inter=table(['接口草案','职责'],d['interfaces']['services'])+'<h3>TaskEnvelope / TaskResult</h3><p>以下为接口示例，DEMO标识和版本号不是研究运行或真实预算。输出结构校验不等于科学正确。</p>'
    for key in ['task_envelope','task_result']:
        inter+='<details><summary>'+esc(key)+'</summary><pre>'+esc(json.dumps(d['interfaces'][key],ensure_ascii=False,indent=2))+'</pre></details>'
    inter+='<h3>Codex接入边界</h3>'+items(d['interfaces']['codex_adapter'])+'<h3>存储与目录</h3>'+items(d['interfaces']['storage'])
    body+=section('interfaces','控制器接收证据，不接受越权状态覆盖',inter)
    accept='<p class="notice">'+esc(d['acceptance']['status'])+'</p>'
    accept+=table(['验收轨道','协议','评价'],[[x['name'],x['protocol'],x['metrics']] for x in d['acceptance']['tracks']])+'<h3>拟议准入门槛</h3>'+items(d['acceptance']['proposed_gates'])
    accept+='<h3>恢复流程演练</h3><p>选择一个预写案例，逐步查看应执行的协议。此交互没有调用模型、控制器或实验。</p><div class="controls"><label for="topic">课题筛选</label><select id="topic"><option value="all">全部</option><option>shared</option><option>TR-001</option><option>TR-002</option><option>TR-003</option></select><label for="case">案例</label><select id="case"></select></div><article class="scenario"><p id="case-kind" class="meta"></p><h4 id="case-title"></h4><p id="case-trigger"></p><ol id="case-steps"></ol><div class="controls"><button id="next-step" type="button">下一步</button><button id="reset-step" type="button">重置演练</button></div><p id="case-expected" class="boundary"></p><p id="case-wrong"></p><details><summary>验收字段与来源定位</summary><p id="case-checks"></p><pre id="case-refs"></pre></details></article><p class="meta">'+esc(replay['split_policy'])+'</p><p><a href="replay-cases.json">全部'+str(len(replay['cases']))+'个案例的结构化源</a></p>'
    body+=section('acceptance','先证明会恢复，再验证会研究',accept)
    body+=section('roadmap','从最小可恢复内核逐步接入',table(['阶段','交付','准入'],[[x['stage'],x['deliverable'],x['gate']] for x in d['roadmap']])+'<h3>上线前待确定的参数</h3>'+items(d['open_decisions'])+'<p>'+esc(d['acceptance']['freshness'])+'</p>')
    sources='<p>'+esc(d['meta']['evidence_boundary'])+'</p>'
    for s in d['sources']:
        sources+='<article class="source"><h3>'+esc(s['id'])+' · <a href="'+esc(s['url'])+'">'+esc(s['name'])+'</a></h3><p class="meta">'+esc(s['version'])+'<br>阅读深度：'+esc(s['depth'])+'</p><p>采用：'+esc(s['take'])+'</p><p>边界：'+esc(s['limit'])+'</p>'+(('<p><a href="'+esc(s['code_url'])+'">固定提交代码</a></p>') if s.get('code_url') else '')+'</article>'
    sources+='<p>本页的架构组合、接口、参数与验收门槛为本轮设计，不是上述来源已经验证的本仓库系统效果。检索截止：'+esc(d['meta']['search_cutoff'])+'。</p>'
    body+=section('sources','前沿方法、经典基线与阅读边界',sources)
    css='''
    :root{--ink:#16252a;--muted:#52646b;--paper:#f4f5f1;--line:#d2dcd9;--accent:#155e63;--wash:#e8efec;--nav:#16373c}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:22px}body{margin:0;background:var(--paper);color:var(--ink);font:16px/1.8 system-ui,-apple-system,"Noto Sans CJK SC",sans-serif}a{color:var(--accent);text-underline-offset:4px}aside{position:fixed;inset:0 auto 0 0;width:252px;background:var(--nav);color:#e6f1ed;padding:32px 24px;overflow:auto}aside a{color:#d2e5df;text-decoration:none;display:block;padding:6px 0;font-size:14px}aside h2{font-size:21px;line-height:1.6;margin:14px 0}aside .meta{color:#b1cbc5}main{max-width:1440px;margin-left:252px;padding:46px 5vw 72px}header{padding:0 0 32px;border-bottom:1px solid var(--line)}h1{font-size:36px;line-height:1.4;margin:14px 0}h2{font-size:26px;line-height:1.5;margin:6px 0 20px}h3{font-size:19px;margin:24px 0 8px}h4{font-size:17px;margin:18px 0 8px}p{margin:9px 0 15px}li{margin:9px 0}section{padding:40px 0 44px;border-bottom:1px solid var(--line)}.eyebrow{font-size:12px;letter-spacing:.15em;color:var(--muted)}aside .eyebrow{color:#b1cbc5}.lead{font-size:18px;max-width:900px;color:var(--muted)}.meta{font-size:13px;color:var(--muted)}.notice,.boundary{padding:15px 18px;background:var(--wash);border-left:3px solid var(--accent)}.flow{background:var(--nav);color:#e6f1ed;padding:24px;font-size:17px;line-height:2}.layer{display:grid;grid-template-columns:48px 1fr;gap:18px;padding:24px 0;border-bottom:1px solid var(--line)}.layer h3{margin-top:0}.number{font-size:23px;color:var(--accent)}.table-wrap{overflow:auto;border:1px solid var(--line)}table{width:100%;border-collapse:collapse;font-size:14px;min-width:630px}th,td{padding:14px 16px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{background:var(--wash);font-weight:600}td:first-child{min-width:136px}tr:last-child td{border-bottom:0}.stats{display:flex;gap:0;flex-wrap:wrap;border-bottom:1px solid var(--line);padding-bottom:20px}.stats div{flex:1;min-width:140px}.stats strong{font-size:30px;display:block;color:var(--accent)}.stats span{font-size:13px;color:var(--muted)}details{padding:12px 0}summary{cursor:pointer;color:var(--accent)}pre{font:13px/1.7 ui-monospace,monospace;white-space:pre-wrap;overflow-wrap:anywhere;background:var(--wash);padding:16px;max-height:480px;overflow:auto}.controls{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:14px 0}select,button{font:inherit;font-size:14px;padding:9px 12px;border:1px solid var(--line);background:#fff;color:var(--ink);max-width:100%;border-radius:3px}button{cursor:pointer}button:disabled{cursor:default;opacity:.5}.scenario{padding:18px 22px;border:1px solid var(--line)}.scenario h4{margin-top:6px}.done{color:var(--ink)}.pending{color:#758787}.current{font-weight:650;color:var(--accent)}.source{padding:8px 0 18px;border-bottom:1px solid var(--line)}footer{font-size:12px;color:var(--muted);padding-top:24px;overflow-wrap:anywhere}a:focus-visible,button:focus-visible,select:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:3px}@media(max-width:850px){aside{position:static;width:auto;padding:20px 24px}aside nav{display:flex;flex-wrap:wrap;gap:4px 20px}aside h2{margin:5px 0}main{margin:0;padding:30px 22px}h1{font-size:28px}.layer{grid-template-columns:32px 1fr;gap:8px}}@media print{aside,.controls{display:none}main{margin:0;padding:0}section{break-inside:auto}details{display:block}h2,h3{break-after:avoid}.notice{border:1px solid var(--line)}html{scroll-behavior:auto}}
    '''
    css += 'body{overflow-wrap:anywhere}.layer>div{min-width:0}.table-wrap{max-width:100%}.report-figure{margin:18px 0}.report-figure img{display:block;width:100%;height:auto;border:1px solid var(--line)}figcaption{font-size:13px;color:var(--muted);margin-top:10px}.figure-downloads{display:flex;flex-wrap:wrap;gap:12px 24px}'
    jsdata=json.dumps(replay['cases'],ensure_ascii=False).replace('<','\\u003c')
    js='''
    const cases=CASE_DATA;const topic=document.getElementById('topic'),picker=document.getElementById('case');let shown=0;
    function selected(){return cases.find(c=>c.id===picker.value)}
    function render(){const c=selected();if(!c)return;document.getElementById('case-kind').textContent=c.id+' · '+c.origin+' · '+c.topic+' · 设计演练，未执行';document.getElementById('case-title').textContent=c.title;document.getElementById('case-trigger').textContent=c.trigger;document.getElementById('case-steps').replaceChildren(...c.steps.map((s,i)=>{const li=document.createElement('li');li.textContent=s;li.className=i<shown?'done':i===shown?'current':'pending';return li}));document.getElementById('case-expected').textContent='预期行为：'+c.expected;document.getElementById('case-wrong').textContent='应阻止的行为：'+c.wrong;document.getElementById('case-checks').textContent='待验收字段：'+c.checks.join(' / ');document.getElementById('case-refs').textContent=c.refs.length?JSON.stringify(c.refs,null,2):'本例为拟议故障场景，未声称来自真实事故。';document.getElementById('next-step').disabled=shown>=c.steps.length;document.getElementById('next-step').textContent=shown>=c.steps.length?'已展开全部协议步骤':'下一步（'+shown+'/'+c.steps.length+'）'}
    function filter(){picker.replaceChildren(...cases.filter(c=>topic.value==='all'||c.topic===topic.value).map(c=>{const o=document.createElement('option');o.value=c.id;o.textContent=c.id+' · '+c.title;return o}));shown=0;render()}
    topic.addEventListener('change',filter);picker.addEventListener('change',()=>{shown=0;render()});document.getElementById('next-step').addEventListener('click',()=>{shown++;render()});document.getElementById('reset-step').addEventListener('click',()=>{shown=0;render()});filter();
    '''.replace('CASE_DATA',jsdata)
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="description" content="基于前沿方法与真实Codex历史的长期全自动研究系统设计；未部署。"><title>长期全自动研究系统 · 设计与验收</title><style>'+css+'</style></head><body><aside><p class="eyebrow">AUTORESEARCH / SYSTEM DESIGN</p><h2>长期研究<br>记忆与恢复</h2><p class="meta">2026-11-11 · 设计v1<br>共用基础设施，研究分别归属</p><a href="runtime.html">打开智能体操作台</a><nav aria-label="章节导航">'+''.join('<a href="#'+k+'">'+str(i).zfill(2)+' '+v+'</a>' for i,(k,v) in enumerate(nav,1))+'</nav><hr><a href="../index.html">三课题入口</a><a href="design.json">结构化设计源</a><a href="README.md">构建与状态说明</a></aside><main><header><p class="eyebrow">DURABLE RESEARCH, REPLACEABLE SESSIONS</p><h1>'+esc(d['meta']['title'])+'</h1><p class="lead">'+esc(d['meta']['subtitle'])+'</p><p class="meta">'+esc(d['meta']['scope'])+'<br>本页为完整系统设计；可运行的v0.1程序请从操作台进入。</p></header>'+body+'<footer>单一设计源：design.json；案例：replay-cases.json；历史审计：history-audit.json。生成输入SHA-256：'+digest+'。本页面可直接离线打开，未公开发布。</footer><script>'+js+'</script></main></body></html>'


def main():
    d,a,r=load('design.json'),load('history-audit.json'),load('replay-cases.json')
    digest=hashlib.sha256(b''.join((ROOT / p).read_bytes() for p in ['design.json','history-audit.json','replay-cases.json'])).hexdigest()
    (ROOT / 'figures').mkdir(exist_ok=True)
    (ROOT / 'figures/system-overview.svg').write_text(render_figure(d))
    subprocess.run(['node', str(ROOT / 'render-figure.cjs')], check=True)
    (ROOT / 'index.html').write_text(render_html(d,a,r,digest))
    print(json.dumps({'generated':['index.html','figures/system-overview.svg','figures/system-overview.png','figures/manifest.json'],'input_sha256':digest},ensure_ascii=False))


if __name__=='__main__':
    main()
