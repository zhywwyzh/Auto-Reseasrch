#!/usr/bin/env python3
"""Render navigation only; do not execute any research topic or its generator."""
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def render():
    data = json.loads((ROOT / 'topics.json').read_text())
    esc = lambda value: html.escape(str(value), quote=True)
    blocks = []
    for t in data['topics']:
        base = t['workspace'].removeprefix('workspaces/')
        sources = '、'.join('<code>'+esc(x)+'</code>' for x in t['sources'])
        blocks.append('<section id="'+esc(t['id'])+'"><p class="label">'+esc(t['id'])+'</p><h2>'+esc(t['title'])+'</h2><p>'+esc(t['focus'])+'</p><p>'+esc(t['boundary'])+'</p><dl>'+
            ''.join('<dt>'+label+'</dt><dd><code>'+esc(t[key])+'</code></dd>' for label,key in [('原始论文','input'),('独立设计目录','workspace'),('协作记录目录','docs'),('本地笔记目录','notes'),('稿件预留目录（不代表已创建）','paper_reserved')])+
            '<dt>内容源 / 最新状态</dt><dd>'+sources+'；以本课题README为准。</dd></dl><p class="links">'+
            '<a href="'+esc(base+'/'+t['entry'])+'">研究首页</a><a href="'+esc(base+'/'+t['latest'])+'">登记的近期设计</a><a href="../'+esc(t['docs'])+'/README.md">课题记录</a><a href="'+esc(base+'/'+t['editor'])+'">独立编辑器入口</a></p></section>')
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AutoResearch-UAV · 三课题导航</title><style>
*{box-sizing:border-box}body{margin:0;background:#f6f7f3;color:#25372f;font:16px/1.8 system-ui,sans-serif}main{max-width:1080px;margin:auto;padding:32px 24px 60px}h1{font-size:28px}h2{font-size:22px}.notice{background:#e8efe9;padding:16px 20px}.label{font-weight:700;color:#23654c}section{border-top:1px solid #cbd6cf;margin-top:30px;padding-top:16px}a{color:#23654c;text-underline-offset:4px}.links,nav{display:flex;flex-wrap:wrap;gap:12px 24px}dl{display:grid;grid-template-columns:220px 1fr;gap:8px;background:#fff;padding:20px}dt{font-weight:600}dd{margin:0;overflow-wrap:anywhere}code{font-size:14px}small{color:#52665a}a:focus-visible{outline:3px solid #ad7c30;outline-offset:3px}@media(max-width:650px){dl{grid-template-columns:1fr}dd{margin-bottom:12px}}@media print{main{padding:0}.links{display:none}}
</style></head><body><main><p><a href="../README.md">仓库说明</a> · <a href="../AGENTS.md">课题路由契约</a></p><h1>三项论文研究，三个独立入口</h1><div class="notice">'''+esc(data['scope'])+'</div><p>请选择本会话指定的原论文。相同的 index.html、build.py 或 validation.json 文件名，在不同课题目录下具有不同归属。</p><nav aria-label="选择课题">'+''.join('<a href="#'+esc(t['id'])+'">'+esc(t['id']+' · '+t['title'])+'</a>' for t in data['topics'])+'</nav>'+''.join(blocks)+'<section><h2>共用资料与边界</h2><p>论文评分、Auto Research方法和排版模板可以共用；数据、运行结果、环境和稿件按课题分别保存。原始PDF保留在原位置，不复制或移动。</p><ul>'+''.join('<li><code>'+esc(x)+'</code></li>' for x in data['shared'])+'</ul><p>'+esc(data['audit'])+'</p><small>登记日期：'+esc(data['date'])+'。单一内容源：<a href="topics.json">topics.json</a>；生成器：<a href="build-index.py">build-index.py</a>。此页面仅导航，不启动任何实验。</small></section></main></body></html>'


if __name__ == '__main__':
    (ROOT / 'index.html').write_text(render())
    print('Rendered workspaces/index.html; no topic generator executed.')
