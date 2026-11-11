#!/usr/bin/env python3
"""Render the research review, without network, models or research execution.

python3 workspaces/bearing-swarm-review/build.py
python3 workspaces/bearing-swarm-review/build.py --canvas-source > <managed-canvas>
"""
import html
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
D = json.loads((ROOT / 'review.json').read_text())
D['followup'] = json.loads((ROOT / 'novelty.json').read_text())
D['plan'] = json.loads((ROOT / 'plan.json').read_text())
D['progress'] = json.loads((ROOT / 'research-progress.json').read_text())
D['benchmark'] = json.loads((ROOT / 'benchmark.json').read_text())
if (ROOT / 'container/validation.json').is_file():
    D['container'] = json.loads((ROOT / 'container/validation.json').read_text())
if (ROOT / 'experiments/results/summary.json').is_file():
    D['pilot'] = json.loads((ROOT / 'experiments/results/summary.json').read_text())


def e(x):
    return html.escape(str(x), quote=True)


def paragraphs(items):
    return ''.join('<p>'+e(x)+'</p>' for x in items)


def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+e(h)+'</th>' for h in headers)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+e(c)+'</td>' for c in row)+'</tr>' for row in rows)+'</tbody></table></div>'


def section(key, title, body):
    return '<section id="'+key+'"><h2>'+title+'</h2>'+body+'</section>'


def webpage():
    s = []
    s.append(section('benchmark-link','最新 / 实验协议与 benchmark','<p><a href="benchmark.html">查看受控评测、公开数据审计、强基线、样本划分及可靠性门槛</a>。已启动旋转子问题先导；<a href="benchmark.html#pilot-results">查看实际结果、失败和边界</a>。下方预审为此前阶段记录，不能当作最新执行状态。</p>'))
    s.append(section('plan-link','详细补强计划','<p>按当前候选决策继续：<a href="plan.html">打开阶段计划、待证理论、实验规格与去留标准</a>。该计划区分当前设计工作与实施获准后的实验。</p>'))
    f = D['followup']
    follow = '<div class="notice">'+e(f['conclusion'])+'</div>'+paragraphs([f['scope']])
    follow += '<h3>本轮判断</h3>'+paragraphs(f['takeaways'])
    follow += table(['需要区分的性质','定义','不能替代的结论'],f['distinctions'])
    for x in f['analysis']:
        follow += '<article><p class="meta">'+e(x['id']+' · '+x['status'])+'</p><h3>'+e(x['title'])+'</h3><p>'+e(x['source'])+'</p><details><summary>查看解析推导及适用边界</summary>'+paragraphs(x['steps'])+'</details></article>'
    follow += '<h3>三个方向的当前决策</h3>'
    for x in f['routes']:
        follow += '<article id="route-'+e(x['id'])+'"><h3>'+e(x['id']+' / '+x['title'])+'</h3><div class="notice">'+e(x['decision'])+'</div>'
        follow += ''.join('<p><b>'+label+'：</b>'+e(x[k])+'</p>' for k,label in [('inherited','继承与边界'),('overlap','已被近邻覆盖'),('claim','尚待证明的新主张'),('design','设计方案')])
        follow += '<details><summary>待证理论、最低对照与停止条件</summary>'+paragraphs(x['theory'])+''.join('<p><b>'+label+'：</b>'+e(x[k])+'</p>' for k,label in [('minimum','最小实验'),('kill','否决条件'),('fallback','降级方案')])+'</details></article>'
    follow += '<h3>补充实验：先隔离机制，再验证闭环收益</h3>'+table(['阶段','对照设计','判别证据'],f['experiments'])+paragraphs([f['statistics']])
    follow += '<h3>创新准入门槛与 Auto Research</h3>'+paragraphs([f['autoresearch']])+table(['门槛','要求','未通过时'],f['gates'])
    follow += '<h3>本轮新增精读与近邻核查</h3>'
    for x in f['literature']:
        follow += '<article><h3><a href="'+e(x['url'])+'" target="_blank" rel="noopener noreferrer">'+e(x['name'])+'</a></h3><p class="meta">'+e(x['status']+' · '+x['depth'])+'</p><p>'+e(x['effect'])+'</p></article>'
    follow += '<h3>优先论文的收敛方案</h3>'+paragraphs(f['paper_plan'])
    follow += '<h3>尚未完成的事项</h3>'+paragraphs(f['limits'])+'<p>本节内容源：<a href="novelty.json">novelty.json</a>。下方保留首轮评审记录；候选优先级以本节为准。</p>'
    s.append(section('novelty','00 / '+e(f['title']),follow))
    s.append(section('identity', '01 / 研究对象与章节对应', table(['对象','核查结果'],D['identity'])+table(['学位章节','定位','对应论文','覆盖与边界'],D['mapping'])))
    s.append(section('scores', '02 / 按仓库方案评分', paragraphs([D['rubric']['source'],D['rubric']['method']])+table(['维度','暂定分数','依据'],D['rubric']['scores'])+'<h3>值得保留的基础</h3>'+paragraphs(D['strengths'])))
    issues = '<label for="filter">筛选评审问题：</label><select id="filter"><option value="all">全部问题</option><option value="P0">P0 · 理论准入</option><option value="P1">P1 · 证据与论证</option></select><p id="count" role="status" aria-live="polite"></p>'
    labels = [('where','原文位置'),('claim','原文主张'),('evidence','核查依据'),('derivation','分析 / 推导'),('impact','为何重要'),('fix','最小修正'),('uncertainty','不确定性')]
    for x in D['issues']:
        issues += '<article class="issue" data-level="'+x['level']+'"><p class="meta">'+e(x['id']+' · '+x['level']+' · '+x['kind'])+'</p><h3>'+e(x['title'])+'</h3><p>'+e(x['where'])+'</p><p><b>依据：</b>'+e(x['evidence'])+'</p><details><summary>展开推导、影响与修正建议</summary>'+''.join('<p><b>'+label+'：</b>'+e(x[k])+'</p>' for k,label in labels if k not in ['where','evidence'])+'</details></article>'
    s.append(section('issues','03 / 核心问题及证据',issues))
    lit = '<p>'+e(D['novelty_boundary'])+'</p>'
    for x in D['literature']:
        lit += '<article><h3><a href="'+e(x['url'])+'" target="_blank" rel="noopener noreferrer">'+e(x['name'])+'</a></h3><p class="meta">'+e(x['year']+' · '+x['depth'])+'</p><p>'+e(x['comparison'])+'</p></article>'
    s.append(section('literature','04 / 最近邻与新颖性边界',lit))
    cand=''
    for x in D['candidates']:
        cand += '<article><p class="meta">'+e(x['id']+' · '+x['decision'])+'</p><h3>'+e(x['title'])+'</h3>'+''.join('<p><b>'+label+'：</b>'+e(x[k])+'</p>' for k,label in [('question','研究问题'),('mechanism','机制'),('theory','待证理论'),('formula','数学目标 / 状态'),('nearest','近邻'),('falsifier','停止条件'),('minimum','最小验证')])+'</article>'
    s.append(section('design','05 / 首轮创新候选记录 · 当前决策见第二轮',cand))
    s.append(section('experiments','06 / 实验补充与统计计划',table(['实验','优先级','控制与对照','验收证据'],D['experiments'])+'<div class="notice">'+e(D['statistics'])+'</div>'))
    s.append(section('auto','07 / Auto Research 的实际使用与后续流程',table(['方法来源','执行状态','本课题用法'],D['autoresearch'])+'<p>方法依据：<a href="../../docs/topics/TR-001-thesis-uav-crowdsensing/methodology.md">仓库既有执行规程</a>；借用流程，不复制原课题任务定义。</p>'))
    s.append(section('outline','08 / 建议论文结构', '<ol>'+''.join('<li>'+e(x)+'</li>' for x in D['outline'])+'</ol>'))
    s.append(section('next','09 / 下一步与核验范围',paragraphs(D['next'])+'<div class="notice">'+e(D['verification'])+'</div><p>内容源：首轮 <a href="review.json">review.json</a>、第二轮 <a href="novelty.json">novelty.json</a>；生成脚本：<a href="build.py">build.py</a>。静态页面无网络请求、无模型调用，不上传材料。Canvas视图从同一JSON生成。</p><p>论文入口：<a href="https://arxiv.org/abs/2401.07784">公开预印本</a> · <a href="../../thesis-reference/theses/博士论文.pdf#page=109">本地学位PDF（仅文件齐全的本机）</a> · <a href="../../docs/research/ai-paper-review/index.html">仓库论文评价方案</a></p>'))
    nav=''.join('<a href="#'+key+'">'+title+'</a>' for key,title in [('novelty','最新：创新补强'),('route-C1','C1 认证与运动'),('route-C2','C2 窗口调度'),('route-C3','C3 工程支撑'),('identity','对象与章节'),('scores','暂定评分'),('issues','核心问题'),('literature','首轮相关工作'),('design','首轮候选记录'),('experiments','首轮实验方案'),('auto','Auto Research'),('outline','论文大纲'),('next','下一步与边界')])
    css='''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:#f6f7f3;color:#25372f;font:16px/1.85 system-ui,-apple-system,"Microsoft YaHei",sans-serif}aside{position:fixed;inset:0 auto 0 0;width:224px;background:#fff;border-right:1px solid #d7dfd9;padding:28px 22px;overflow:auto}nav{display:grid;gap:10px;margin-top:25px}a{color:#23654c;text-underline-offset:4px}nav a{text-decoration:none}main{margin-left:224px;max-width:1500px;padding:38px 46px 70px}h1{font-size:30px;line-height:1.5;max-width:1000px}h2{font-size:23px}h3{font-size:18px;line-height:1.6}p{margin:10px 0}.meta{font-size:13px;color:#5b6e62}.lead{font-size:19px}.notice{background:#e8efe9;border-left:3px solid #23654c;padding:16px 20px;margin:20px 0}section{border-top:1px solid #d7dfd9;padding:28px 0}article{padding:20px 0;border-bottom:1px solid #d7dfd9}article:last-child{border:0}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px;margin:16px 0;background:#fff}th,td{text-align:left;vertical-align:top;padding:12px 14px;border-bottom:1px solid #d7dfd9}th{background:#e8efe9}td:first-child{min-width:130px}td{min-width:110px}details{background:#fff;border:1px solid #d7dfd9;padding:12px 18px;margin:15px 0}summary{cursor:pointer;font-weight:600}button,select{font:inherit;font-size:14px;background:#fff;border:1px solid #bac9bd;border-radius:4px;padding:7px 12px;color:#25372f}button{cursor:pointer}.top{display:flex;justify-content:space-between;gap:15px;align-items:center}li{margin:15px 0}a:focus-visible,button:focus-visible,summary:focus-visible,select:focus-visible{outline:3px solid #ad7c30;outline-offset:3px}[hidden]{display:none!important}@media(max-width:850px){aside{position:static;width:auto;padding:20px}nav{display:flex;flex-wrap:wrap;gap:10px 18px;margin-top:12px}main{margin:0;padding:24px 20px}h1{font-size:26px}}@media print{aside,button,select,label,#count{display:none}main{margin:0;padding:0}body{background:#fff}details>*{display:block}.scroll{overflow:visible}table{font-size:11px}section{break-before:auto}}'''
    js='''const f=document.querySelector('#filter');function update(){let n=0;document.querySelectorAll('.issue').forEach(x=>{x.hidden=f.value!=='all'&&x.dataset.level!==f.value;if(!x.hidden)n++});document.querySelector('#count').textContent=`当前显示 ${n} 项评审问题`}f.addEventListener('change',update);update();document.querySelector('#expand').addEventListener('click',()=>{const all=[...document.querySelectorAll('details')];const open=all.some(x=>!x.open);all.forEach(x=>x.open=open);document.querySelector('#expand').textContent=open?'收起全部证据':'展开全部证据'})'''
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(D['title'])+'</title><style>'+css+'</style></head><body><aside><p class="meta">TR-002 / '+e(D['date'])+'</p><h2>论文预审</h2><p>事实、推导与研究假设分别记录</p><nav aria-label="章节导航">'+nav+'</nav></aside><main><div class="top"><span class="meta">预审历史与研究设计 · 最新执行状态见先导结果</span><button id="expand">展开全部证据</button></div><h1>'+e(D['title'])+'</h1><p class="lead">'+e(D['conclusion'])+'</p><div class="notice">'+e(D['boundary'])+'</div><p class="meta">'+e(D['scope'])+'</p>'+''.join(s)+'<script>'+js+'</script></main></body></html>'


def planpage():
    p = D['plan']
    q = D['progress']
    progress = '<div class="notice">'+e(q['summary'])+'</div>'+table(['阶段','状态','具体进展'],q['status'])+paragraphs(q['contract'])
    for x in q['proofs']:
        progress += '<article id="'+e(x['id'])+'"><p class="meta">'+e(x['id']+' · '+x['kind'])+'</p><h3>'+e(x['title'])+'</h3><p><b>假设：</b>'+e(x['assumptions'])+'</p><p><b>命题：</b>'+e(x['statement'])+'</p><details><summary>展开证明、来源及适用边界</summary><ol>'+''.join('<li>'+e(step)+'</li>' for step in x['proof'])+'</ol><p><b>边界：</b>'+e(x['boundary'])+'</p><p><b>来源：</b>'+e(x['source'])+'</p></details></article>'
    progress += table(['决策','对象','依据'],q['decisions'])+'<h3>下一项研究工作</h3>'+paragraphs(q['next'])
    progress += '<h3>本轮近邻与阅读深度</h3>'+''.join('<p><a href="'+e(x['url'])+'" target="_blank" rel="noopener noreferrer">'+e(x['title'])+'</a> — '+e(x['depth'])+'</p>' for x in q['sources'])+'<div class="notice">'+e(q['validation'])+'</div><p>进展内容源：<a href="research-progress.json">research-progress.json</a>。下方是阶段计划，不能把计划项目当成完成记录。</p>'
    parts = [section('benchmark-link','最新 / 详细实验协议','<p><a href="benchmark.html">打开 benchmark 注册表、实验矩阵、强基线和统计协议</a>。该协议细化下方粗略实验/样本建议；<a href="benchmark.html#pilot-results">最新实际先导结果</a>单独记录，原计划中的“尚未实施”为历史状态。</p>'),section('progress','00 / '+e(q['title']),progress),section('contract','01 / 研究目标与固定条件',paragraphs([p['target']])+paragraphs(p['fixed'])+table(['层次','主张','需要的证据'],p['claims']))]
    stages = table(['阶段','建议投入','进入条件'],[[x['id']+' '+x['title'],x['effort'],x['dependency']] for x in p['stages']])
    for x in p['stages']:
        stages += '<article id="'+e(x['id'])+'"><p class="meta">'+e(x['id']+' · '+x['effort'])+'</p><h3>'+e(x['title'])+'</h3><p><b>依赖：</b>'+e(x['dependency'])+'</p><details open><summary>具体工作与验收</summary><ol>'+''.join('<li>'+e(t)+'</li>' for t in x['tasks'])+'</ol>'+''.join('<p><b>'+label+'：</b>'+e(x[k])+'</p>' for k,label in [('deliverable','阶段交付'),('pass','通过标准'),('stop','未通过时')])+'</details></article>'
    parts.append(section('stages','02 / 分阶段执行与去留',stages))
    b=p['bridge_test']
    parts.append(section('theory','03 / 待证理论与优先反证',table(['定理工作包','待解决问题','创新门槛','优先检查'],p['theory'])+'<h3>'+e(b['title'])+'</h3><p class="meta">'+e(b['status'])+'</p>'+paragraphs([b['assumptions'],b['argument'],b['consequence']])))
    parts.append(section('method','04 / 方法流程与接口规格',table(['步骤','动作','边界'],p['algorithm'])+table(['接口','字段','约束'],p['interfaces'])))
    parts.append(section('baselines','05 / 必须保留的强基线',table(['基线','定义','公平比较要求'],p['baselines'])))
    parts.append(section('experiments','06 / 实验与指标',table(['实验','场景/变量','验收证据','执行条件'],p['experiments'])+table(['指标','定义','不能混淆'],p['metrics'])))
    parts.append(section('budget','07 / 时间、样本与预算',paragraphs(p['budget'])+table(['建议时段','工作','交付'],p['first_ten_days'])))
    parts.append(section('branches','08 / C2与C3的进入条件',table(['分支','具体工作','停止/边界'],p['branches'])))
    parts.append(section('paper','09 / 论文结构与证据对应',table(['章节','内容','写作边界'],p['paper'])))
    sources=''.join('<p><a href="'+e(x['url'])+'" target="_blank" rel="noopener noreferrer">'+e(x['title'])+'</a> — '+e(x['note'])+'</p>' for x in p['sources'])
    parts.append(section('sources','10 / 来源与执行边界',sources+'<div class="notice">'+e(p['limits'])+'</div><p>内容源：<a href="plan.json">plan.json</a>；生成器：<a href="build.py">build.py</a>；<a href="index.html#novelty">前轮创新核查与解析推导</a>；<a href="validation.json">交付验证记录</a>。所有阶段均为计划，没有新增实验结果。</p>'))
    nav=''.join('<a href="#'+key+'">'+label+'</a>' for key,label in [('progress','最新：研究进展'),('D0','证书重推'),('D2','生成树条件'),('D4','带噪粗界'),('contract','目标与范围'),('stages','阶段与验收'),('theory','待证理论'),('method','方法与接口'),('baselines','强基线'),('experiments','实验与指标'),('budget','时间与预算'),('branches','C2 / C3分支'),('paper','论文结构'),('sources','来源与边界')])
    css='''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:#f6f7f3;color:#25372f;font:16px/1.8 system-ui,-apple-system,"Microsoft YaHei",sans-serif}aside{position:fixed;inset:0 auto 0 0;width:220px;background:#fff;border-right:1px solid #d7dfd9;padding:24px;overflow:auto}nav{display:grid;gap:10px}a{color:#23654c;text-underline-offset:4px}nav a{text-decoration:none}main{margin-left:220px;max-width:1450px;padding:34px 42px 70px}h1{font-size:28px;line-height:1.5}h2{font-size:22px}h3{font-size:18px}.meta{font-size:13px;color:#5b6e62}.notice{background:#e8efe9;border-left:3px solid #23654c;padding:16px;margin:18px 0}section{border-top:1px solid #d7dfd9;padding:24px 0}article{padding:20px 0;border-bottom:1px solid #d7dfd9}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px;background:#fff;margin:16px 0}th,td{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #d7dfd9;min-width:120px}th{background:#e8efe9}details{padding:12px 18px;background:#fff;border:1px solid #d7dfd9}summary{font-weight:600;cursor:pointer}li{margin:12px 0}a:focus-visible,summary:focus-visible{outline:3px solid #ad7c30;outline-offset:3px}@media(max-width:850px){aside{position:static;width:auto}nav{display:flex;flex-wrap:wrap;gap:10px 16px}main{margin:0;padding:24px 18px}}@media print{aside{display:none}main{margin:0;padding:0}body{background:#fff}.scroll{overflow:visible}table{font-size:11px}}'''
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(p['title'])+'</title><style>'+css+'</style></head><body><aside><p class="meta">TR-002 / '+e(p['date'])+'</p><h2>补强执行计划</h2><p><a href="index.html">返回证据评审</a></p><nav aria-label="计划章节">'+nav+'</nav></aside><main><p class="meta">详细研究设计 · 已启动旋转先导，其他阶段按实际记录</p><h1>'+e(p['title'])+'</h1><p>'+e(p['summary'])+'</p><div class="notice">'+e(p['status'])+'</div>'+''.join(parts)+'</main></body></html>'


def benchmarkpage():
    b = D['benchmark']
    sections = [section('readiness','01 / 当前就绪状态',table(['部分','状态','依据'],b['readiness'])),section('questions','02 / 要回答的问题与否决条件',table(['问题','实验设计','判据'],b['questions']))]
    z = b.get('simulation_resources')
    if z:
        body = '<div class="notice">'+e(z['status'])+'</div><p>'+e(z['conclusion'])+'</p>'
        for key,title,headers in [('dataset_layers','要构建的测试集',['层次','规模','内容']),('instance_contract','一个数据实例包含什么',['部分','规格']),('environments','分阶段的软件环境',['环境','配置','边界']),('hardware','硬件建议：规划值，尚未测性能',['阶段','建议','依据与限制']),('host_snapshot','当前执行主机只读盘点',['项目','检查结果'])]:
            body += '<h3 id="env-'+key+'">'+title+'</h3>'+table(headers,z[key])
        body += '<h3>存储、时间预算与实施顺序</h3>'+paragraphs(z['budget'])
        body += '<h3>搭建前拟定的环境验收要求</h3>'+table(['项目','验收要求'],z['acceptance'])
        body += '<h3>官方来源与核查边界</h3>'+''.join('<p><a href="'+e(x['url'])+'">'+e(x['title'])+'</a> — '+e(x['note'])+'</p>' for x in z['sources'])
        sections.insert(0,section('simulation-resources','搭建前设计 / '+e(z['title']),body))
    c = b.get('configuration_assessment')
    if c:
        body = '<div class="notice">'+e(c['conclusion'])+'</div><p>'+e(c['status'])+'</p>'
        for key,title,headers in [('decisions','首轮配置决策',['项目','提案','条件']),('software','软件与隔离',['部分','配置','核查边界']),('baseline_audit','强基线源码审查：适配必须处理的问题',['问题','源码事实','本项目要求']),('solver_proposal','求解精度与限时',['项目','提议设置','解释']),('host_recheck','本轮机器复核：瞬时观察',['项目','观察','限制']),('resource_gates','资源与扩容判据',['阶段','判据','说明']),('budget_scenarios','运行预算：算术情景，未执行',['配额','调用数','累计时长情景'])]:
            body += '<h3 id="config-'+key+'">'+title+'</h3>'+table(headers,c[key])
        body += '<p>'+e(c['budget_boundary'])+'</p><details><summary>搭建前候选Python依赖元数据（当时未安装）</summary>'
        for x in c['package_candidates']:
            body += '<p><a href="'+e(x['metadata_url'])+'">'+e(x['package']+' '+x['candidate_version'])+'</a>；Python '+e(x['requires_python'])+'；cp310/Linux x86_64 wheel已在元数据中找到；'+e(x['status'])+'</p>'
        body += '</details><h3>下一步</h3>'+paragraphs(c['next_steps'])
        body += '<h3>来源与阅读深度</h3>'+''.join('<p><a href="'+e(x['url'])+'">'+e(x['title'])+'</a> — '+e(x['note'])+'</p>' for x in c['sources'])
        sections.insert(0,section('configuration-assessment','搭建前评估 / '+e(c['title']),body))
    v = D.get('container')
    if v:
        body = '<div class="notice">'+e(v['conclusion'])+'</div><p>'+e(v['scope'])+'</p>'
        body += '<h3>实际环境与隔离检查</h3>'+table(['项目','实测/核查记录'],v['environment'])
        body += '<h3>已执行的环境验收</h3>'+table(['检查','结果'],v['checks'])
        body += '<h3>结果边界</h3>'+paragraphs(v['limitations'])
        body += '<p>构建与复测：<a href="container/README.md">容器说明</a> · <a href="container/build_image.py">构建脚本</a> · <a href="container/run_smoke.py">验收脚本</a> · <a href="container/Dockerfile">Dockerfile</a> · <a href="container/validation.json">实际验收记录</a>。</p>'
        sections.insert(0,section('container-validation','最新 / 容器环境验收（'+e(v['date'])+'）',body))
    p = D.get('pilot')
    if p:
        count = p['counts']
        body = '<div class="notice">已实际完成首轮旋转子问题实验；不是留出评测，也未验证新方法创新。'+e(count['diagnostic_cases'])+'个解析诊断、'+e(count['development_worlds'])+'个开发世界／'+e(count['development_logs'])+'条日志、'+e(count['main_method_runs'])+'次主配置运行，另有'+e(count['precision_repeat_runs'])+'次复查。</div>'
        body += '<p>8类故障注入被拒绝。弱SDP有3次TIME_LIMIT，均保留。所有270次开发运行均返回通过本轮浮点可行性检查的候选，但这不等于全部收敛，更不是严格认证。</p>'
        body += '<h3>本批结果对研究方向的影响</h3>'+paragraphs([
            '16个可辨识平面诊断中，弱SDP的前三特征值之外尾谱约1至3；观测边、全对和生成树加强均在预设容差内恢复真值Gram。该结果支持解析动机，但加强约束和生成树仍是现成强基线。',
            str(len(p['rank3_reflection_cases']))+'个开发实例中，弱SDP数值秩为3、状态为OPTIMAL，却含接近−1行列式的相对块；投影到SO(3)后代价明显增大。不能把秩3和求解器状态当作原SO(3)问题的全局证书。这里是自建基线及其舍入结果，不是原作者完整算法复现。',
            'D5探索性分析：36条含噪日志分别评价生成树和观测边两种加强，共72个界计算；有效尾谱界为'+str(p['d5_exploratory']['informative_noisy_records'])+'。这是“下界图不连通或上界不小于tr(X)”的判据，说明该粗界在本批输入上没有信息，不代表定位必然失败。',
            '加强约束、生成树和几何初始化NLS在本批输入上的误差接近。下一步优先研究更有用的含噪界与真正超出这些基线的决策机制；当前不支持新方法优越性声明。'])
        body += '<figure><img src="experiments/results/pilot-results.svg" alt="先导开发集平均相对旋转误差与平面诊断Gram尾谱" style="width:100%;max-width:1100px"><figcaption>真实先导数据；18个世界跨噪声配对，平均值易受弱SDP舍入离群点影响。未作显著性检验。</figcaption></figure>'
        names = {'weak':'弱SDP','observed':'观测边加强','all_pairs':'全对加强','tree':'生成树加强','nls':'几何初始化NLS'}
        body += '<h3>开发集描述性结果</h3>'+table(['噪声上界/度','方法','数值可行/尝试','世界内平均相对旋转误差再跨世界平均/度','每观测数值gap中位数'],[[r['noise_degrees'],names[r['method']],str(r['usable'])+'/'+str(r['attempted']),format(r['mean_pair_rotation_error_deg'],'.6g'),format(r['median_gap_per_observation'],'.3g')] for r in p['strata']])
        body += '<h3>修订与资源</h3><p>v1断图提取实现出错并停止，原始失败保留；v2改为分连通分量处理，读取开发集前重跑全部诊断。主运行耗时约'+format(p['runtime']['elapsed_seconds'],'.1f')+'秒，cgroup峰值内存约'+format(p['runtime']['memory_peak_bytes']/1024**2,'.1f')+' MiB。2 CPU／2 GiB、单worker、无GPU；共享宿主负载，因此不据此声称算法实时性或正式速度优势。</p>'
        body += '<h3>必须保留的边界</h3>'+paragraphs(p['limitations'])
        body += '<p><a href="experiments/pilot/README.md">实验与复测说明</a> · <a href="experiments/pilot/protocol.json">先导协议v2</a> · <a href="experiments/results/summary.json">结果、哈希与逐项界记录</a> · <a href="experiments/results/pilot-results.png">PNG图</a>。完整数据与矩阵保存在本课题被忽略的runs目录，不上传原始资料。</p>'
        sections.insert(0,section('pilot-results','最新 / 首轮真实研究实验（TR002-PILOT-001）',body))
    registry = ''
    for x in b['registry']:
        title = e(x['id']+' / '+x['name'])
        if x.get('url'):
            title = '<a href="'+e(x['url'])+'">'+title+'</a>'
        registry += '<article id="'+e(x['id'])+'"><h3>'+title+'</h3><p class="meta">'+e(x['type'])+'</p><p><b>核验状态：</b>'+e(x['status'])+'</p><p>'+e(x['use'])+'</p><details><summary>适用范围与准入条件</summary><p>'+e(x['gate'])+'</p></details></article>'
    sections.append(section('registry','03 / benchmark 注册表',registry))
    for key,title,headers in [('fixed_log','04 / 固定日志：数据、噪声与划分',['项目','规格']),('baselines','05 / 必须保留的强基线',['编号','方法','公平性与状态']),('closed_loop','06 / 闭环因子实验',['项目','规格与待冻结项']),('metrics','07 / 指标及声明边界',['指标','定义与边界'])]:
        sections.append(section(key,title,table(headers,b[key])))
    sections.append(section('checker','08 / 独立认证检查器','<ol>'+''.join('<li>'+e(x)+'</li>' for x in b['checker'])+'</ol>'))
    sections.append(section('statistics','09 / 统计与可复现性','<ol>'+''.join('<li>'+e(x)+'</li>' for x in b['statistics'])+'</ol>'))
    sections.append(section('stress','09a / 压力测试、消融与实测边界',table(['类别','规格'],b['stress'])))
    sections.append(section('manifest','09b / 可复现 manifest',table(['记录','必要字段'],b['manifest'])))
    sections.append(section('gates','10 / 开跑与结论准入门槛',table(['门槛','验收内容','失败处理'],b['gates'])+paragraphs(b['next'])))
    versions = ''.join('<p><a href="'+e(x['url'])+'">'+e(x['repo'])+'</a><br><code>'+e(x['commit'])+'</code><br>'+e(x['status'])+'</p>' for x in b['code_versions'])
    sources = ''.join('<p><a href="'+e(x['url'])+'">'+e(x['title'])+'</a> — '+e(x['depth'])+'</p>' for x in b['sources'])
    sections.append(section('sources','11 / 来源、版本与阅读深度','<p>检索与版本核查截止 '+e(b['date'])+'；文献新颖性审阅另见研究计划，投稿/修回前需更新。</p>'+versions+sources+'<p>内容源：<a href="benchmark.json">benchmark.json</a>；<a href="build.py">生成脚本</a>；<a href="validation.json">页面验证记录</a>。先导生成器与整理结果已在本课题experiments目录；完整运行数据仍在Git忽略的runs目录，未对外发布。</p>'))
    nav = ''.join('<a href="#'+key+'">'+label+'</a>' for key,label in [('configuration-assessment','搭建前配置评估'),('config-baseline_audit','基线源码差异'),('config-resource_gates','资源与扩容判据'),('simulation-resources','仿真环境与设备'),('env-dataset_layers','测试集结构'),('env-hardware','硬件建议'),('env-host_snapshot','前轮本机盘点'),('readiness','就绪状态'),('questions','问题与判据'),('registry','benchmark 注册表'),('fixed_log','固定日志与样本'),('baselines','强基线'),('closed_loop','闭环归因'),('metrics','指标边界'),('checker','独立证书检查'),('statistics','统计规则'),('stress','压力与实测'),('manifest','复现清单'),('gates','可靠性门槛'),('sources','来源与版本')])
    if v:
        nav = '<a href="#container-validation">最新：容器环境验收</a>' + nav
    if p:
        nav = '<a href="#pilot-results">最新：真实先导实验</a>' + nav
    css = '''*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:#f6f7f3;color:#25372f;font:16px/1.8 system-ui,-apple-system,"Microsoft YaHei",sans-serif}aside{position:fixed;inset:0 auto 0 0;width:240px;padding:24px;background:#fff;border-right:1px solid #d7dfd9;overflow:auto}nav{display:grid;gap:9px}a{color:#23654c;text-underline-offset:4px}main{margin-left:240px;max-width:1440px;padding:32px 40px 70px}h1{font-size:28px;line-height:1.5}h2{font-size:22px}h3{font-size:18px}.meta{font-size:13px;color:#5b6e62}.notice{background:#e8efe9;padding:18px;border-left:3px solid #23654c}section{padding:24px 0;border-top:1px solid #d7dfd9}article{padding:16px 0;border-bottom:1px solid #d7dfd9}.scroll{overflow:auto}table{width:100%;border-collapse:collapse;font-size:14px;background:#fff}th,td{padding:12px;text-align:left;vertical-align:top;border-bottom:1px solid #d7dfd9;min-width:120px}th{background:#e8efe9}details{padding:10px 16px;background:#fff;border:1px solid #d7dfd9}summary{cursor:pointer;font-weight:600}li{margin:14px 0}code{overflow-wrap:anywhere}a:focus-visible,summary:focus-visible{outline:3px solid #ad7c30;outline-offset:3px}@media(max-width:850px){aside{position:static;width:auto}nav{display:flex;flex-wrap:wrap;gap:10px 16px}main{margin:0;padding:22px 18px}}@media print{aside{display:none}main{margin:0;padding:0}.scroll{overflow:visible}table{font-size:11px}}'''
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(b['title'])+'</title><style>'+css+'</style></head><body><aside><p class="meta">TR-002 / '+e(b['date'])+'</p><h2>实验设计</h2><p><a href="index.html">返回评审</a> · <a href="plan.html">研究计划</a></p><nav aria-label="实验协议章节">'+nav+'</nav></aside><main><p class="meta">'+e(b['version'])+'</p><h1>'+e(b['title'])+'</h1><div class="notice">'+e(b['summary'])+'</div><p>'+e(b['scope'])+'</p>'+''.join(sections)+'</main></body></html>'


def canvas():
    return '''// Generated by workspaces/bearing-swarm-review/build.py from review.json, novelty.json and plan.json.
import { Stack, Row, H1, H2, Text, Link, Button, Table, Divider, useCanvasState, useHostTheme } from "cursor/canvas";
const d = '''+json.dumps(D,ensure_ascii=False).replace('<','\\u003c')+''';
export default function BearingSwarmReview() {
 const {tokens:t}=useHostTheme();
 const [selected,setSelected]=useCanvasState("TR002-review-issue","R1");
 const item=d.issues.find(x=>x.id===selected)||d.issues[0];
 const [phase,setPhase]=useCanvasState("TR002-plan-phase","P0");
 const stage=d.plan.stages.find(x=>x.id===phase)||d.plan.stages[0];
 return <Stack gap={20} style={{padding:24,maxWidth:1300,margin:"0 auto"}}>
 <Text style={{color:t.text.secondary}}>TR-002 · {d.date} · 作者侧预审历史 / 最新执行状态见实验页面</Text>
 <H1>{d.title}</H1><Text>{d.conclusion}</Text>
 <Text style={{background:t.fill.tertiary,padding:16}}>{d.boundary}</Text>
 <H2>{d.benchmark.title}</H2><Text>{d.benchmark.version}</Text><Text>{d.benchmark.summary}</Text>
 <Table headers={["部分","状态","依据"]} rows={d.benchmark.readiness}/>
 <Link href="/home/zhywwyzh/workspace/AutoResearch-UAV/workspaces/bearing-swarm-review/benchmark.html">详细协议：benchmark、基线、样本划分与可靠性门槛</Link><Divider/>
 <H2>{d.progress.title}</H2><Text>{d.progress.summary}</Text><Table headers={["阶段","状态","实际进展"]} rows={d.progress.status}/>
 {d.progress.proofs.map(x=><Stack key={x.id} gap={6}><H2>{x.id} · {x.title}</H2><Text>{x.kind}</Text><Text>假设：{x.assumptions}</Text><Text>{x.statement}</Text><Text>边界：{x.boundary}</Text></Stack>)}
 <Text>{d.progress.validation}</Text><Link href="/home/zhywwyzh/workspace/AutoResearch-UAV/workspaces/bearing-swarm-review/plan.html#progress">完整证明草稿与本轮研究记录</Link><Divider/>
 <H2>{d.plan.title}</H2><Text>{d.plan.summary}</Text><Text>{d.plan.status}</Text>
 <Row wrap gap={8}>{d.plan.stages.map(x=><Button key={x.id} variant={phase===x.id?"primary":"secondary"} onClick={()=>setPhase(x.id)}>{x.id} · {x.title}</Button>)}</Row>
 <H2>{stage.title}</H2><Text>{stage.effort}</Text><Text>依赖：{stage.dependency}</Text>{stage.tasks.map(x=><Text key={x}>{x}</Text>)}<Text>交付：{stage.deliverable}</Text><Text>通过：{stage.pass}</Text><Text>停止或收窄：{stage.stop}</Text>
 <H2>待证理论与实验规格</H2><Table headers={["工作包","待证问题","创新门槛","反证"]} rows={d.plan.theory}/><Table headers={["实验","场景","证据","条件"]} rows={d.plan.experiments}/>
 <H2>建议的前10个工作日</H2><Table headers={["时段","工作","交付"]} rows={d.plan.first_ten_days}/><Text>{d.plan.limits}</Text>
 <Link href="/home/zhywwyzh/workspace/AutoResearch-UAV/workspaces/bearing-swarm-review/plan.html">完整详细计划：基线、指标、接口、预算与论文结构</Link>
 <Divider/>
 <H2>{d.followup.title}</H2><Text>{d.followup.conclusion}</Text><Text>{d.followup.scope}</Text>
 {d.followup.takeaways.map(x=><Text key={x}>{x}</Text>)}
 <Table headers={["性质","定义","边界"]} rows={d.followup.distinctions}/>
 {d.followup.analysis.map(x=><Stack key={x.id} gap={8}><H2>{x.title}</H2><Text>{x.status}</Text><Text>{x.source}</Text>{x.steps.map(y=><Text key={y}>{y}</Text>)}</Stack>)}
 <H2>当前候选与否决条件</H2>{d.followup.routes.map(x=><Stack key={x.id} gap={8}><H2>{x.title}</H2><Text>{x.decision}</Text><Text>近邻：{x.overlap}</Text><Text>待证主张：{x.claim}</Text><Text>{x.design}</Text>{x.theory.map(y=><Text key={y}>{y}</Text>)}<Text>最小实验：{x.minimum}</Text><Text>否决：{x.kill}</Text></Stack>)}
 <H2>新实验判别与创新门槛</H2><Table headers={["阶段","设计","证据"]} rows={d.followup.experiments}/><Text>{d.followup.statistics}</Text><Table headers={["门槛","要求","否决"]} rows={d.followup.gates}/><Text>{d.followup.autoresearch}</Text>
 <H2>新增近邻</H2>{d.followup.literature.map(x=><Stack key={x.name} gap={4}><Link href={x.url}>{x.name}</Link><Text>{x.status} · {x.depth}</Text><Text>{x.effect}</Text></Stack>)}
 <H2>优先论文方案</H2>{d.followup.paper_plan.map(x=><Text key={x}>{x}</Text>)}
 {d.followup.limits.map(x=><Text key={x}>{x}</Text>)}
 <Divider/><H2>首轮评审记录：研究对象</H2><Table headers={["对象","核查结果"]} rows={d.identity}/>
 <H2>评分与依据</H2><Text>{d.rubric.source}</Text><Text>{d.rubric.method}</Text>
 <Table headers={["维度","暂定评分","理由"]} rows={d.rubric.scores}/>
 <Divider/><H2>逐项核查 · 点击查看</H2><Row wrap gap={8}>{d.issues.map(x=><Button key={x.id} variant={selected===x.id?"primary":"secondary"} onClick={()=>setSelected(x.id)}>{x.id} · {x.level}</Button>)}</Row>
 <H2>{item.title}</H2><Text>{item.kind}</Text><Text>{item.where}</Text><Text>{item.evidence}</Text><Text>推导：{item.derivation}</Text><Text>影响：{item.impact}</Text><Text>修正：{item.fix}</Text><Text>不确定性：{item.uncertainty}</Text>
 <Divider/><H2>首轮候选记录 · 当前决策见第二轮</H2>{d.candidates.map(x=><Stack key={x.id} gap={8}><H2>{x.title}</H2><Text>{x.decision}</Text><Text>{x.question}</Text><Text>{x.mechanism}</Text><Text>{x.theory}</Text><Text>{x.formula}</Text><Text>停止条件：{x.falsifier}</Text></Stack>)}
 <Divider/><H2>实验补充</H2><Table headers={["实验","优先级","控制与对照","验收"]} rows={d.experiments}/><Text>{d.statistics}</Text>
 <H2>相关工作与阅读深度</H2><Text>{d.novelty_boundary}</Text>{d.literature.map(x=><Stack key={x.name} gap={4}><Link href={x.url}>{x.name}</Link><Text>{x.year} · {x.depth}</Text><Text>{x.comparison}</Text></Stack>)}
 <H2>Auto Research 使用记录</H2><Table headers={["方法","状态","实际用法"]} rows={d.autoresearch}/>
 <H2>论文大纲</H2>{d.outline.map(x=><Text key={x}>{x}</Text>)}<H2>下一步</H2>{d.next.map(x=><Text key={x}>{x}</Text>)}<Text>{d.verification}</Text>
 <Link href="/home/zhywwyzh/workspace/AutoResearch-UAV/workspaces/bearing-swarm-review/index.html">仓库完整静态评审页</Link>
 </Stack>;
}
'''


if __name__ == '__main__':
    if '--canvas-source' in sys.argv:
        print(canvas())
    else:
        (ROOT/'index.html').write_text(webpage())
        (ROOT/'plan.html').write_text(planpage())
        (ROOT/'benchmark.html').write_text(benchmarkpage())
        print('Rendered index.html, plan.html and benchmark.html')
