#!/usr/bin/env python3
"""Render survey.json. No external dependencies or model/network calls.

python3 docs/research/ai-paper-review/build.py
python3 docs/research/ai-paper-review/build.py --canvas-source

The latter prints a self-contained Canvas view for the IDE-managed canvases
directory. survey.json is the content source; regenerate views after edits.
"""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def esc(value):
    return html.escape(str(value), quote=True)


def links(values):
    return ' · '.join(f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(label)}</a>' for label, url in values)


def webpage(data):
    policies = ''.join(f'<article><h3>{esc(x["title"])}</h3><p><b>官方政策：</b>{esc(x["fact"])}</p><p class="note"><b>解读：</b>{esc(x["implication"])}</p>{links([["官方来源", x["url"]]])}</article>' for x in data['policy'])
    entries = []
    for x in data['items']:
        entries.append(f'''<article class="entry" id="{esc(x['id'])}" data-category="{esc(x['category'])}">
<div class="meta">{esc(x['category'])} / {esc(x['venue'])}</div><h3>{esc(x['name'])}<span class="tag">{esc(x['priority'])}</span></h3>
<p>{esc(x['function'])}</p><p><b>写作价值 · 分析建议：</b>{esc(x['use'])}</p>
<details><summary>开放范围、局限与核验深度</summary><p><b>开放状态：</b>{esc(x['openness'])}</p><p><b>局限：</b>{esc(x['limits'])}</p><p class="note"><b>阅读深度：</b>{esc(x['depth'])}</p></details>
<div class="sources">{links(x['links'])}</div></article>''')
    workflow = ''.join(f'<li><h3>{esc(x["stage"])}</h3><p>{esc(x["action"])}</p><p class="note">建议产物：{esc(x["deliverable"])}</p></li>' for x in data['workflow'])
    categories = list(dict.fromkeys(x['category'] for x in data['items']))
    buttons = ''.join(f'<button type="button" data-filter="{esc(c)}" aria-pressed="false">{esc(c)}</button>' for c in categories)
    notes = ''.join(f'<li>{esc(x)}</li>' for x in data['topic_advice'])
    more = ''.join(f'<li>{links([x])}</li>' for x in data['further'])
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AI 论文评价与打分 · 检索笔记</title><style>
:root{--bg:#f5f6f3;--paper:#fff;--ink:#24332c;--muted:#59675f;--line:#d6ded8;--accent:#22664e;--soft:#eaf0eb}*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:24px}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.8 system-ui,-apple-system,"Microsoft YaHei",sans-serif}a{color:var(--accent);text-underline-offset:3px}aside{position:fixed;width:240px;inset:0 auto 0 0;padding:28px 22px;background:var(--paper);border-right:1px solid var(--line)}aside p{font-size:14px;color:var(--muted)}nav{display:grid;gap:10px;margin-top:30px}nav a{text-decoration:none}main{margin-left:240px;padding:36px 48px 70px;max-width:1370px}h1{font-size:30px;line-height:1.5;font-weight:650;margin:14px 0 20px}h2{font-size:23px;margin:0 0 16px}h3{font-size:18px;margin:0 0 9px}p{margin:8px 0}section{padding:32px 0;border-bottom:1px solid var(--line)}.meta,.note,.sources{color:var(--muted);font-size:13px}.lead{font-size:19px;max-width:950px}.notice{background:var(--soft);padding:18px 22px;margin-top:22px}.policy{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:24px}.entry{padding:24px 0;border-bottom:1px solid var(--line)}.entry:last-child{border:0}.tag{font-weight:400;font-size:12px;display:inline-block;margin-left:14px;padding:2px 8px;background:var(--soft);vertical-align:middle}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:16px 0}button,input{font:inherit;font-size:14px;border:1px solid var(--line);border-radius:4px;background:var(--paper);color:var(--ink);padding:8px 12px}button{cursor:pointer}button[aria-pressed=true]{background:var(--accent);color:white;border-color:var(--accent)}input{width:min(100%,550px)}button:focus-visible,a:focus-visible,input:focus-visible,summary:focus-visible{outline:3px solid var(--accent);outline-offset:3px}details{background:var(--paper);padding:12px 16px;margin:12px 0;border:1px solid var(--line)}summary{cursor:pointer;font-size:14px}ol,ul{padding-left:24px}li{margin-bottom:15px}.prompt{white-space:pre-wrap;background:var(--paper);border:1px solid var(--line);padding:20px;font-family:inherit}.sources{margin-top:14px;line-height:2.2}.sources a{white-space:normal}[hidden]{display:none!important}.foot{font-size:13px;color:var(--muted);margin-top:24px}@media(max-width:800px){aside{position:static;width:auto;border-right:0;border-bottom:1px solid var(--line);padding:20px}nav{display:flex;gap:15px;overflow:auto;margin-top:14px}nav a{white-space:nowrap}aside p{display:none}main{margin:0;padding:24px 20px}h1{font-size:26px}}@media print{aside,.controls,.search-label,#counter{display:none}main{margin:0;padding:0;max-width:none}body{background:white}details>*{display:block}.entry{break-inside:avoid}.sources{font-size:11px}}
</style></head><body><aside><div class="meta">RESEARCH NOTE / 2026-11-10</div><h2>论文预审参考</h2><p>开源工具、评分模板、公开研究与使用边界。</p><nav aria-label="章节导航"><a href="#start">结论与使用顺序</a><a href="#policy">官方政策</a><a href="#catalog">工作目录</a><a href="#workflow">写作流程</a><a href="#topic">UCS-GenRL 检查建议</a><a href="#prompt">预审提示词</a><a href="#evidence">核验边界</a></nav></aside><main>
<section id="start"><div class="meta">检索截至 ''' + esc(data['checked']) + ''' · 公开证据 / 未运行评审工具</div><h1>''' + esc(data['title']) + '''</h1><p class="lead">''' + esc(data['conclusion']) + '''</p><div class="notice"><b>建议先看：</b>DeepReviewer 2.0 / CMU Paper Reviewer 用于发现问题；AI Scientist 的代码用于理解评分量表；ReviewEval / CoCoReviewBench 用于判断反馈质量。<br><b>证据标签：</b>项目功能与数值为作者或官方报告；“写作价值”和下方流程为本次分析建议。</div><p class="note">''' + esc(data['scope']) + '''</p></section>
<section id="policy"><h2>确有 AI 预审与使用；不能等同于自动录用</h2><div class="policy">''' + policies + '''</div></section>
<section id="catalog"><h2>工作目录</h2><label class="search-label" for="search">按名称、功能或局限检索</label><br><input id="search" type="search" placeholder="例如：评分、许可证、相关工作、ICML"><div class="controls" aria-label="类型筛选"><button type="button" data-filter="全部" aria-pressed="true">全部</button>''' + buttons + '''</div><p id="counter" role="status" aria-live="polite"></p>''' + ''.join(entries) + '''</section>
<section id="workflow"><h2>把预审嵌入写作过程</h2><p class="note">以下为建议流程，尚未部署或执行。</p><ol>''' + workflow + '''</ol></section>
<section id="topic"><h2>面向 UCS-GenRL 的检查建议</h2><ul>''' + notes + '''</ul></section>
<section id="prompt"><h2>可直接改用的预审提示词</h2><p class="note">这是一份检查要求，不是已经验证有效的评分器；请另附目标 venue 标准和稿件版本。</p><div class="prompt">''' + esc(data['prompt']) + '''</div></section>
<section id="evidence"><h2>核验深度与待核对项</h2><p>''' + esc(data['verification']) + '''</p><p>本轮未逐篇下载和精读 PDF，因此摘要级条目未补造 PDF 页码；网页和代码的定位已在各条目注明。若后续据某项数值作研究决策，应继续核对论文正文、数据划分、评价模型和置信区间。</p><p>本页面是无外部依赖的本地静态文档，不上传稿件、不执行评审。内容唯一编辑源为 <a href="survey.json">survey.json</a>；通过 <a href="build.py">build.py</a> 同步生成 HTML 和 Canvas 视图。源码在仓库，尚未推送或公开发布。</p><h3>进一步阅读</h3><ul>''' + more + '''</ul></section>
<p class="foot">作者预审是改稿线索。具体理论正确性、实验真实性及新颖性，需要可核对的领域证据。</p></main>
<script>
const search = document.querySelector('#search');
const entries = Array.from(document.querySelectorAll('.entry'));
const buttons = Array.from(document.querySelectorAll('[data-filter]'));
let active = '全部';
function update() {
  const query = search.value.trim().toLocaleLowerCase();
  let shown = 0;
  for (const entry of entries) {
    entry.hidden = !((active === '全部' || entry.dataset.category === active) && entry.textContent.toLocaleLowerCase().includes(query));
    if (!entry.hidden) shown++;
  }
  document.querySelector('#counter').textContent = `显示 ${shown} / ${entries.length} 项`;
}
search.addEventListener('input', update);
for (const button of buttons) button.addEventListener('click', () => {
  active = button.dataset.filter;
  for (const other of buttons) other.setAttribute('aria-pressed', String(other === button));
  update();
});
update();
</script></body></html>'''


def canvas(data):
    payload = json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')
    return '''// Generated from docs/research/ai-paper-review/survey.json by build.py --canvas-source.
// Regenerate after content edits; the repository JSON is the source of truth.
import { Stack, Row, H1, H2, Text, Link, Button, Table, Divider, useHostTheme, useCanvasState } from "cursor/canvas";
const data = ''' + payload + ''';
export default function AIPaperReviewSurvey() {
  const { tokens: t } = useHostTheme();
  const [category, setCategory] = useCanvasState("paper-review-category", "写作工具");
  const [selected, setSelected] = useCanvasState("paper-review-selected", "deepreviewer");
  const categories = ["全部", ...Array.from(new Set(data.items.map(x => x.category)))];
  const shown = data.items.filter(x => category === "全部" || x.category === category);
  const item = shown.find(x => x.id === selected) || shown[0];
  return <Stack gap={22} style={{ padding: 24, maxWidth: 1280, margin: "0 auto" }}>
    <Text style={{color:t.text.secondary}}>检索截至 {data.checked} · 公开资料核验 · 未运行评审工具</Text>
    <H1>{data.title}</H1>
    <Text>{data.conclusion}</Text>
    <Row gap={24} align="start" wrap>
      <Stack gap={10} style={{flex:"1 1 350px"}}>
        <H2>建议从这里开始</H2>
        <Text>发现问题：DeepReviewer 2.0 / CMU Paper Reviewer。</Text>
        <Text>理解打分量表：AI Scientist 的评审代码。</Text>
        <Text>检验反馈质量：ReviewEval / CoCoReviewBench。</Text>
      </Stack>
      <Stack gap={10} style={{flex:"1 1 350px"}}>
        <H2>正式评审与作者预审</H2>
        {data.policy.map(p => <Stack key={p.title} gap={4}><Link href={p.url}>{p.title}</Link><Text>{p.fact}</Text></Stack>)}
      </Stack>
    </Row>
    <Divider />
    <H2>工作对照 · 选择条目查看依据</H2>
    <Row wrap gap={6}>{categories.map(c => <Button key={c} variant={category === c ? "primary" : "secondary"} onClick={() => setCategory(c)}>{c}</Button>)}</Row>
    <Table headers={["项目 / 报告", "发表或报告状态", "开放范围", "阅读建议"]} rows={shown.map(x => [<Button key={x.id} variant="ghost" onClick={() => setSelected(x.id)}>{x.name}</Button>, x.venue, x.openness, x.priority])} />
    {item && <Stack gap={10} style={{padding:20, background:t.fill.tertiary}}>
      <H2>{item.name}</H2><Text>{item.function}</Text>
      <Text>分析建议：{item.use}</Text><Text>局限：{item.limits}</Text>
      <Text style={{color:t.text.secondary}}>阅读深度：{item.depth}</Text>
      <Row wrap>{item.links.map(([label,url]) => <Link key={url} href={url}>{label}</Link>)}</Row>
    </Stack>}
    <Divider /><H2>写作过程中的使用顺序 · 建议</H2>
    {data.workflow.map((x,i) => <Stack key={x.stage} gap={5}><Text>{i+1}. {x.stage}：{x.action}</Text><Text style={{color:t.text.secondary}}>建议产物：{x.deliverable}</Text></Stack>)}
    <H2>UCS-GenRL 的重点检查 · 建议</H2>
    {data.topic_advice.map(x => <Text key={x}>{x}</Text>)}
    <H2>预审提示词</H2><Text>{data.prompt}</Text>
    <Divider /><H2>核验边界</H2><Text>{data.verification}</Text>
    <Text>分数不是录用概率；公开报告不等于开源实现。原始 PDF 未逐篇精读，未补造页码。HTML 与此页由同一份仓库 JSON 生成。</Text>
    <Row wrap>{data.further.map(([label,url]) => <Link key={url} href={url}>{label}</Link>)}</Row>
  </Stack>;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--canvas-source', action='store_true')
    args = parser.parse_args()
    data = json.loads((ROOT / 'survey.json').read_text())
    if args.canvas_source:
        print(canvas(data))
    else:
        target = ROOT / 'index.html'
        target.write_text(webpage(data), encoding='utf-8')
        print(f'Generated {target}: {len(data["items"])} entries')


if __name__ == '__main__':
    main()
