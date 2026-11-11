"""Render the research DESIGN document. Does not import or run research code."""
import hashlib
import html
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "implementation-specification.json"
TARGET = HERE.parent / "experiment-specification.html"


def esc(value):
    return html.escape(str(value))


def table(headers, rows):
    return '<div class="scroll"><table><thead><tr>' + ''.join('<th>' + esc(h) + '</th>' for h in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + esc(v) + '</td>' for v in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def render():
    raw = SOURCE.read_bytes()
    d = json.loads(raw)
    c = d['config']
    sha = hashlib.sha256(raw).hexdigest()
    nav = ''.join('<a href="#' + esc(s['id']) + '">' + esc(s['title']) + '</a>' for s in d['sections'])
    blocks = []
    for s in d['sections']:
        body = ''.join('<p>' + esc(p) + '</p>' for p in s['paragraphs'])
        if s['id'] == 'audit':
            body += '<label class="filter">查找证据 <input id="audit-filter" type="search" placeholder="例如：覆盖度、奖励、步数"></label><p id="audit-count" aria-live="polite"></p>'
            for a in d['audit']:
                body += '<details class="audit"><summary>' + esc(a['id'] + ' · ' + a['topic']) + '</summary><p><b>原文：</b>' + esc(a['thesis']) + '</p><p><b>源码位置：</b>' + esc(a['code_locator']) + '</p><p><b>静态发现：</b>' + esc(a['finding']) + '</p><p><b>设计处置：</b>' + esc(a['decision']) + '</p><small>' + esc(a['type']) + '</small></details>'
        elif s['id'] == 'protocol':
            body += table(['配额', 'E01 / E02 / E03 / E04：每批轨迹数', '每短阶段接纳样本数'], [(k, ' / '.join(map(str, v)), ' / '.join(str(n * 20 * 32) for n in v)) for k, v in c['quotas'].items()])
            body += '<details><summary>配置全文：含明确的未决项</summary><pre>' + esc(json.dumps(c, ensure_ascii=False, indent=2)) + '</pre></details>'
        elif s['id'] == 'interfaces':
            body += table(['设计接口', '输入', '输出', '不可违反的条件'], [(x['name'], x['input'], x['output'], x['invariants']) for x in d['interfaces']])
        elif s['id'] == 'budget':
            body += table(['阶段', '筛选接纳样本', '确认接纳样本上界', '取得主快照', '评价交互上界', '接纳训练＋评价上界'], [(s['id'], f"{s['screen_consumed']:,}", f"{s['confirmation_consumed_upper']:,}", f"{s['warmup_consumed']:,}", f"{s['evaluation_steps_upper']:,}", f"{s['consumed_plus_eval_upper']:,}") for s in c['stages']])
            body += '<pre>短阶段：32条轨迹/批 × 20步/轨迹 × 32更新 = 20,480接纳样本。\n筛选：S × C × (K+1) × 2重复 × (h+a)。\n确认：最多 S × C × 3个不同配额 × 2重复 × (h+a)。\n评价：筛选每分支2次、确认每分支1次；每次最多1×10×400转移。\n实际生成训练步 = 已接纳样本 + 生成但未接纳的交互（包括排空/失败）。\n真实总成本需加R0、失败/重跑及其他项目支出，不能拿上表作运行硬上限。</pre>'
        elif s['id'] == 'acceptance':
            body += table(['编号', '验收对象', '通过标准', '当前状态'], [(q['id'], q['test'], q['pass'], q['status']) for q in d['acceptance']])
            body += '<div class="note"><strong>当前停机位置：设计交付。</strong>用户下一次明确指令前，不编写研究实现、不安装研究运行环境、不触发环境step、优化器更新或付费模型调用。文档生成与页面验证不属于研究实验。</div>'
        blocks.append('<section id="' + esc(s['id']) + '"><h2>' + esc(s['title']) + '</h2>' + body + '</section>')
    css = '''
:root{--bg:#fcfcf8;--ink:#20332f;--muted:#61726b;--line:#d7dfd8;--soft:#edf3ed;--accent:#17634e}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.8 system-ui,"Noto Sans CJK SC",sans-serif}aside{position:fixed;inset:0 auto 0 0;width:260px;overflow:auto;background:var(--soft);padding:28px 22px;border-right:1px solid var(--line)}main{margin-left:260px;max-width:1400px;padding:32px 4vw 70px}h1{font-size:30px;line-height:1.5}h2{font-size:23px}nav a{display:block;padding:6px 0;text-decoration:none}a{color:var(--accent);overflow-wrap:anywhere}p{margin:12px 0}section{border-top:1px solid var(--line);padding-top:28px;margin-top:32px}small,.eyebrow,footer{font-size:13px;color:var(--muted)}.eyebrow{letter-spacing:.06em}.note{background:var(--soft);border-left:3px solid var(--accent);padding:16px 20px}.toolbar{display:flex;gap:10px;flex-wrap:wrap}button,input{font:inherit;color:inherit;border:1px solid var(--line);background:white;padding:8px 12px;max-width:100%}button,summary{cursor:pointer}button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid #a57531;outline-offset:2px}.scroll{overflow-x:auto}table{width:100%;border-collapse:collapse;font-size:14px}td,th{padding:12px;vertical-align:top;text-align:left;border-bottom:1px solid var(--line)}th{background:var(--soft)}details{border-bottom:1px solid var(--line);padding:14px 0}summary{font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;padding:16px;background:var(--soft);font:13px/1.8 ui-monospace,monospace}code{overflow-wrap:anywhere}.filter{display:flex;gap:12px;align-items:center;flex-wrap:wrap}footer{margin-top:35px;overflow-wrap:anywhere}[hidden]{display:none!important}@media(max-width:860px){aside{position:static;width:auto}nav{display:flex;gap:5px 16px;flex-wrap:wrap}main{margin:0;padding:20px 16px}h1{font-size:26px}table{min-width:720px}}@media print{aside,.toolbar,.filter,#audit-count{display:none}main{margin:0;padding:0}body{font-size:11px}.scroll{overflow:visible}table{min-width:0;font-size:10px}details[hidden]{display:block!important}}
'''
    js = '''
const audits=[...document.querySelectorAll('.audit')],input=document.querySelector('#audit-filter');
function filter(){const q=input.value.trim().toLowerCase();audits.forEach(d=>d.hidden=!d.textContent.toLowerCase().includes(q));document.querySelector('#audit-count').textContent=`显示 ${audits.filter(d=>!d.hidden).length} / ${audits.length} 条静态核验；不是运行验收结果。`}
input.addEventListener('input',filter);filter();
document.querySelector('#expand').onclick=()=>{const ds=[...document.querySelectorAll('details:not([hidden])')],v=ds.some(d=>!d.open);ds.forEach(d=>d.open=v)};
document.querySelector('#print').onclick=()=>window.print();let before=[];
window.addEventListener('beforeprint',()=>{before=[...document.querySelectorAll('details')].map(d=>({open:d.open,hidden:d.hidden}));document.querySelectorAll('details').forEach(d=>{d.open=true;d.hidden=false})});
window.addEventListener('afterprint',()=>document.querySelectorAll('details').forEach((d,i)=>{if(before[i]){d.open=before[i].open;d.hidden=before[i].hidden}}));
'''
    out = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="design-source-sha256" content="' + sha + '"><title>UCS-GenRL · 第一轮详细实验规范</title><style>' + css + '</style></head><body><aside><div class="eyebrow">TR-001 / DESIGN ONLY</div><h2>第一轮详细<br>实验规范</h2><p>2026-11-11<br><small>设计已整理 · 执行锁定</small></p><nav>' + nav + '</nav><hr><a href="theory-experiment-design.html#preparation">前轮准备与理论</a><br><a href="thesis-guide.html">论文导读</a><br><a href="index.html">工作区</a></aside><main><div class="toolbar"><button id="expand">展开 / 收起说明</button><button id="print">打印</button><a href="design/implementation-specification.json" download>下载设计源 JSON</a></div><h1>从可讨论方案，到可核验的实验规范</h1><p class="note">只完成静态研究和设计。尚未解决的定义显式保留；没有执行研究代码、训练、仿真或付费调用。</p>' + ''.join(blocks) + '<footer>唯一设计源：design/implementation-specification.json<br>由design/render-implementation-specification.py生成；修改设计源后重新生成页面。<br>源文件SHA256：' + sha + '<br>原论文与源码详细证据保持本地忽略边界。</footer><script>' + js + '</script></main></body></html>'
    TARGET.write_text(out)
    print('Generated design document:', TARGET)


if __name__ == '__main__':
    render()
