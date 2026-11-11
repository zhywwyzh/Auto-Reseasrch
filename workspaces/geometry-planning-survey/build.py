#!/usr/bin/env python3
"""Render a local research document from one content source; no research execution.

python3 workspaces/geometry-planning-survey/build.py
python3 workspaces/geometry-planning-survey/build.py --canvas-source
"""
import html
import json
import re
import sys
import base64
from pathlib import Path

ROOT = Path(__file__).resolve().parent
D = json.loads((ROOT / 'survey.json').read_text())
REFS = {r['id']: r for r in D['references']}
FIGURES = {s['figure']: 'data:image/svg+xml;base64,' + base64.b64encode((ROOT / 'figures' / s['figure']).read_bytes()).decode()
           for s in D['sections'] if 'figure' in s}


def e(value):
    return html.escape(str(value), quote=True)


def prose(value):
    return re.sub(r'\[([RSM]\d{2})\]', lambda m: '<a class="cite" href="#ref-' + m[1] + '" title="' + e(REFS[m[1]]['title']) + '">[' + m[1] + ']</a>', e(value))


def paragraphs(items):
    return ''.join('<p>' + prose(p) + '</p>' for p in items)


def table(headers, rows):
    return '<div class="table-wrap" tabindex="0" aria-label="可横向滚动的比较表"><table><thead><tr>' + ''.join('<th scope="col">' + e(h) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + prose(c) + '</td>' for c in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def section(s, draft=False):
    sid = ('draft-' if draft else '') + s['id']
    body = paragraphs(s['paragraphs'])
    if 'figure' in s:
        body += '<figure style="margin:24px 0"><div style="overflow-x:auto" tabindex="0" aria-label="解析图，窄屏可横向滚动"><img style="display:block;width:100%;min-width:760px;height:auto" src="' + FIGURES[s['figure']] + '" alt="相同安全Bézier曲线：单段控制点包含条件拒绝，精确分成两段后通过"></div><figcaption class="status">' + prose(D['analytic_example']['caption']) + '</figcaption></figure>'
    if 'rows' in s:
        body += table(s['headers'], s['rows'])
    return '<section id="' + sid + '" class="' + ('manuscript' if draft else 'research') + '"><h2>' + e(s['title']) + '</h2>' + body + '</section>'


def webpage():
    nav = ''.join('<a href="#' + s['id'] + '">' + e(s['title'].split(' / ')[-1]) + '</a>' for s in D['sections'])
    nav += '<a href="#draft">中文综述雏形</a><a href="#references">文献与阅读深度</a><a href="#access">使用与证据边界</a>'
    groups = sorted({r['group'] for r in D['references']})
    ref_html = ''
    for r in D['references']:
        search = ' '.join(str(v) for v in r.values())
        ref_html += '<article class="ref" id="ref-' + r['id'] + '" data-group="' + e(r['group']) + '" data-level="' + r['level'] + '" data-search="' + e(search.lower()) + '"><div class="ref-meta"><span>' + r['id'] + ' · ' + e(r['group']) + '</span><span>' + r['level'] + ' · ' + e(r['year']) + '</span></div><h3><a href="' + e(r['url']) + '" target="_blank" rel="noreferrer">' + e(r['title']) + '</a></h3><p>' + e(r['status']) + '</p><p class="muted">阅读：' + e(r['read']) + '</p><p>' + e(r['note']) + '</p></article>'
    counts = {k: sum(r['id'].startswith(k) for r in D['references']) for k in ['R', 'S', 'M']}
    style = '''
    :root{color-scheme:light;--ink:#182d36;--muted:#526771;--accent:#126354;--paper:#fff;--wash:#f2f5f3;--line:#cdd9d4}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:20px}body{margin:0;background:var(--wash);color:var(--ink);font:16px/1.85 system-ui,-apple-system,"Noto Sans CJK SC",sans-serif}a{color:var(--accent);text-underline-offset:3px}a:focus-visible,button:focus-visible,select:focus-visible,input:focus-visible{outline:3px solid var(--accent);outline-offset:3px}.layout{display:grid;grid-template-columns:260px minmax(0,1fr);max-width:1600px;margin:auto}aside{position:sticky;top:0;height:100vh;overflow:auto;padding:32px 24px;border-right:1px solid var(--line)}aside strong{display:block;margin-bottom:18px}nav a{display:block;padding:7px 0;font-size:14px;text-decoration:none}nav a:hover{text-decoration:underline}main{min-width:0;padding:48px clamp(24px,5vw,82px);background:var(--paper)}header{padding:0 0 40px;border-bottom:2px solid var(--ink)}.eyebrow{font-size:12px;letter-spacing:2px;color:var(--accent);font-weight:700}h1{font-size:clamp(28px,3.2vw,44px);line-height:1.3;margin:20px 0 12px;max-width:820px}header .subtitle{font-size:23px;line-height:1.5}.english{font-size:14px;color:var(--muted);max-width:760px}.status{font-size:13px;color:var(--muted)}.verdict{font-size:18px;max-width:900px}.notice{padding:18px 22px;background:var(--wash);border-left:3px solid var(--accent);font-size:14px}.stats{display:flex;gap:36px;flex-wrap:wrap;padding:24px 0}.stats b{font-size:26px;display:block;line-height:1.4}.stats span{font-size:13px;color:var(--muted)}section{padding:34px 0;border-bottom:1px solid var(--line)}h2{font-size:23px;line-height:1.45;margin:0 0 24px}h3{font-size:17px;line-height:1.6;margin:12px 0}p{margin:14px 0}.table-wrap{overflow-x:auto;margin:24px 0}table{border-collapse:collapse;width:100%;font-size:14px;line-height:1.7;min-width:680px}th,td{text-align:left;vertical-align:top;padding:15px 14px;border-bottom:1px solid var(--line)}th{background:var(--wash);font-weight:650}td:first-child{min-width:155px;font-weight:600}td{min-width:150px}.cite{white-space:nowrap;font-size:.88em;margin:0 2px}.manuscript{max-width:920px}.manuscript p{text-align:justify}.draft-heading{padding-top:45px}.draft-heading h2{font-size:28px}.draft-links{display:flex;gap:12px 24px;flex-wrap:wrap;font-size:14px}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin:18px 0}button,input,select{font:inherit;font-size:14px;padding:9px 12px;border:1px solid var(--line);border-radius:4px;background:var(--paper);color:var(--ink)}button{cursor:pointer}button:hover{background:var(--wash)}input{flex:1;min-width:200px}.ref{padding:24px 0;border-top:1px solid var(--line)}.ref:target{background:var(--wash);outline:2px solid var(--accent);outline-offset:6px}.ref-meta{display:flex;justify-content:space-between;gap:14px;font-size:12px;color:var(--muted)}.ref p{font-size:14px;margin:7px 0}.ref[hidden]{display:none}.muted{color:var(--muted)}footer{padding-top:32px;font-size:13px;color:var(--muted)}.toplinks{display:flex;gap:16px;flex-wrap:wrap;font-size:14px;margin:22px 0}.skip{position:absolute;left:-10000px}.skip:focus{left:10px;top:10px;background:var(--paper);padding:8px;z-index:5} @media(max-width:950px){.layout{display:block}aside{position:static;height:auto;border-right:0;border-bottom:1px solid var(--line);padding:18px 24px}nav{display:flex;gap:6px 18px;flex-wrap:wrap}nav a{font-size:13px}aside strong{margin:0 0 6px}main{padding:30px 22px}.ref-meta{flex-wrap:wrap}h2{font-size:21px}}@media print{aside,.toolbar,.toplinks,.draft-links{display:none}.layout{display:block}main{padding:0}body{font-size:11pt;background:white}h1{font-size:24pt}h2{font-size:16pt}table{min-width:0;font-size:9pt}td{min-width:0}section{break-before:auto}tr,.ref{break-inside:avoid}a{color:inherit}.ref[hidden]{display:block}.table-wrap{overflow:visible}}
    '''
    script = '''
    const query=document.querySelector('#query'), group=document.querySelector('#group'), level=document.querySelector('#level');
    const refs=[...document.querySelectorAll('.ref')];
    function filter(){const q=query.value.trim().toLowerCase();let n=0;refs.forEach(r=>{r.hidden=!(r.dataset.search.includes(q)&&(!group.value||r.dataset.group===group.value)&&(!level.value||r.dataset.level===level.value));if(!r.hidden)n++});document.querySelector('#count').textContent=`显示 ${n} / ${refs.length} 条`}
    [query,group,level].forEach(el=>el.addEventListener('input',filter));
    function reset(){query.value='';group.value='';level.value='';filter()}
    document.querySelector('#reset').addEventListener('click',reset);
    document.querySelector('#print').addEventListener('click',()=>window.print());
    function revealReference(){if(location.hash.startsWith('#ref-')){reset();document.querySelector(location.hash)?.scrollIntoView()}}
    window.addEventListener('hashchange',revealReference);filter();revealReference();
    '''
    return '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>' + e(D['title']) + ' · TR-003</title><style>' + style + '</style></head><body><a class="skip" href="#main">跳至正文</a><div class="layout"><aside><strong>TR-003 / 研究阅读室</strong><div class="status">' + D['date'] + '<br>独立课题 · 未公开发布</div><nav aria-label="章节导航">' + nav + '</nav></aside><main id="main"><header><div class="eyebrow">LITERATURE SYNTHESIS / WORKING PAPER</div><h1>' + e(D['title']) + '</h1><p class="subtitle">' + e(D['subtitle']) + '</p><p class="english">' + e(D['english_title']) + '</p><p class="status">' + e(D['status']) + '</p><p class="verdict">' + e(D['verdict']) + '</p><div class="toplinks"><a href="#evidence">先看核查发现</a><a href="#draft">阅读正文雏形</a><a href="#references">查阅文献</a><button id="print" type="button">打印全文</button></div><div class="notice">' + e(D['boundary']) + '</div><div class="stats"><div><b>' + str(counts['R']) + '</b><span>领域研究及学位关联条目</span></div><div><b>' + str(counts['S']) + '</b><span>既有综述对照</span></div><div><b>' + str(counts['M']) + '</b><span>自动综述方法来源</span></div></div><p class="status">以上为当前种子库构成，并非系统检索最终纳入数。阅读深度逐条标注。</p></header>' + ''.join(section(s) for s in D['sections']) + '<div id="draft" class="draft-heading"><div class="eyebrow">DRAFT MANUSCRIPT</div><h2>中文综述雏形</h2><p class="notice">面向后续扩写的正文，不是可提交稿。引用为当前证据库ID；正式参考文献、完整检索统计及独立复核尚待补齐。引用可点击跳转至来源与阅读深度。</p><div class="draft-links">' + ''.join('<a href="#draft-' + s['id'] + '">' + e(s['title'].split('：')[0]) + '</a>' for s in D['draft']) + '</div></div>' + ''.join(section(s, True) for s in D['draft']) + '<section id="references"><h2>文献库与阅读深度</h2><p>L0 题录 · L1 摘要/引言 · L2 相关技术段落核对 · L3 全文编码并复核。当前无L3条目。引用元数据与下载本的哈希在本地阅读目录保存。</p><div class="toolbar"><input id="query" aria-label="搜索文献" placeholder="搜索标题、编号、方法或年份"><select id="group" aria-label="按主题筛选"><option value="">全部主题</option>' + ''.join('<option>' + e(g) + '</option>' for g in groups) + '</select><select id="level" aria-label="按阅读深度筛选"><option value="">全部阅读深度</option><option>L0</option><option>L1</option><option>L2</option></select><button id="reset" type="button">清除筛选</button></div><p class="status" id="count" aria-live="polite"></p>' + ref_html + '</section><section id="access"><h2>使用与证据边界</h2><p>本页为无外部依赖的静态文档；正文来自同目录survey.json，运行build.py重新生成。原PDF及下载全文仍位于Git忽略目录，不嵌入页面，也不公开发布。</p><p>本地文件入口仅适用于能够访问该文件的电脑。本机HTTP入口仅服务运行主机；远程客户端需使用自己的端口转发。此页不声称已部署公网，也不声称所有引用链接在任何网络下都可打开。</p><p>验证记录见validation.json。浏览器可用性和交互检查结果单独记录；结构检查不能替代视觉验收。内容边界：原文事实见证据卡；本轮分析见核心论证及解析案例；待验证新颖性见论文方案v0.2。解析图不属于实验结果。</p></section><footer>TR-003 · ' + D['date'] + ' · 保留TR-001和TR-002在途工作 · 本地生成，不代表推送或投稿</footer></main></div><script>' + script + '</script></body></html>'


def canvas():
    data = json.dumps(D, ensure_ascii=False).replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    return '''import { Button, H1, H2, TextInput, useCanvasState, useHostTheme } from "cursor/canvas";
const D = ''' + data + ''';
const figures: Record<string,string> = ''' + json.dumps(FIGURES) + ''';
export default function GeometryPlanningSurvey(){
 const {tokens:t}=useHostTheme();
 const [mode,setMode]=useCanvasState<string>("TR003-mode","研究方案");
 const [query,setQuery]=useCanvasState<string>("TR003-query","");
 const refs=D.references.filter(r=>JSON.stringify(r).toLowerCase().includes(query.toLowerCase()));
 const cell={padding:"12px",borderBottom:`1px solid ${t.stroke.primary}`,verticalAlign:"top" as const,textAlign:"left" as const,minWidth:155};
 function text(s:string){return s.split(/(\[[RSM]\\d{2}\])/g).map((p,i)=>{
   const id=p.slice(1,-1);const r=D.references.find(r=>r.id===id);
   return r?<a key={i} href={r.url} target="_blank" rel="noreferrer" style={{color:t.text.link}}>{p}</a>:p;
 })}
 return <main style={{padding:28,color:t.text.primary,background:t.bg.editor,lineHeight:1.85,fontSize:14}}>
 <div style={{color:t.text.secondary,fontSize:12}}>TR-003 · {D.date} · 独立课题 · 未公开发布</div>
 <H1>{D.title}</H1><p style={{fontSize:18}}>{D.subtitle}</p><p style={{color:t.text.secondary}}>{D.english_title}</p>
 <p>{D.verdict}</p><div style={{padding:16,background:t.fill.tertiary}}>{D.status}<br/>{D.boundary}</div>
 <div style={{display:"flex",gap:10,flexWrap:"wrap",margin:"24px 0"}}>{["研究方案","正文雏形","文献与深度"].map(x=><Button key={x} onClick={()=>setMode(x)}>{mode===x?"● ":""}{x}</Button>)}</div>
 {mode==="研究方案"&&D.sections.map(s=><section key={s.id} style={{padding:"22px 0",borderBottom:`1px solid ${t.stroke.primary}`}}><H2>{s.title}</H2>{s.paragraphs.map((p,i)=><p key={i}>{text(p)}</p>)}{"figure" in s&&s.figure&&<figure style={{margin:"24px 0"}}><div style={{overflowX:"auto"}} tabIndex={0} aria-label="解析图，窄屏可横向滚动"><img src={figures[s.figure]} alt="Bézier解析案例：相同曲线在分段前后通过不同的充分条件" style={{display:"block",width:"100%",minWidth:760,height:"auto"}}/></div><figcaption style={{color:t.text.secondary,fontSize:12}}>{text(D.analytic_example.caption)}</figcaption></figure>}{"rows" in s&&s.rows&&<div style={{overflowX:"auto"}}><table style={{borderCollapse:"collapse",width:"100%",fontSize:13}}><thead><tr>{s.headers?.map(h=><th key={h} style={{...cell,background:t.fill.tertiary}}>{h}</th>)}</tr></thead><tbody>{s.rows.map((row,i)=><tr key={i}>{row.map((c,j)=><td key={j} style={cell}>{text(c)}</td>)}</tr>)}</tbody></table></div>}</section>)}
 {mode==="正文雏形"&&<div style={{maxWidth:900}}><p style={{color:t.text.secondary}}>工作稿：摘要与9节正文。点击引用可查看原始来源；请在文献页同时核对阅读深度。</p>{D.draft.map(s=><section key={s.id} style={{padding:"22px 0",borderBottom:`1px solid ${t.stroke.primary}`}}><H2>{s.title}</H2>{s.paragraphs.map((p,i)=><p key={i}>{text(p)}</p>)}</section>)}</div>}
 {mode==="文献与深度"&&<section><H2>文献种子库 · {D.references.length}条</H2><p>L0题录 / L1摘要与引言 / L2相关技术段落 / L3全文编码并复核。当前无L3；不是系统检索最终纳入数。</p><TextInput value={query} onChange={setQuery} placeholder="搜索编号、方法、年份或阅读深度"/>{refs.map(r=><article key={r.id} style={{padding:"20px 0",borderBottom:`1px solid ${t.stroke.primary}`}}><div style={{color:t.text.secondary,fontSize:12}}>{r.id} · {r.group} · {r.year} · {r.level}</div><p><a href={r.url} target="_blank" rel="noreferrer" style={{color:t.text.link,fontWeight:650}}>{r.title}</a></p><p>{r.status}</p><p>阅读：{r.read}</p><p>{r.note}</p></article>)}</section>}
 <p style={{marginTop:28,color:t.text.tertiary,fontSize:12}}>唯一内容源：workspaces/geometry-planning-survey/survey.json。静态HTML与本阅读版本由同一build.py生成。本轮没有新实验、付费模型调用或公开发布。</p>
 </main>
}
'''


if __name__ == '__main__':
    # Fail early if a cited identifier has no corresponding source card.
    cited = set(re.findall(r'\[([RSM]\d{2})\]', json.dumps(D['sections'] + D['draft'], ensure_ascii=False)))
    assert cited <= REFS.keys(), cited - REFS.keys()
    assert len(REFS) == len(D['references']), 'Duplicate reference identifiers'
    if '--canvas-source' in sys.argv:
        print(canvas())
    else:
        (ROOT / 'index.html').write_text(webpage())
        print('Rendered', ROOT / 'index.html')
