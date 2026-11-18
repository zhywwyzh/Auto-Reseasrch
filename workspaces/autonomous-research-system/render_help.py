#!/usr/bin/env python3
"""Render the local README as a UTF-8 HTML guide, without external packages."""
from html import escape
from pathlib import Path
import re
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent
TOKEN = re.compile(r'`([^`]+)`|\*\*(.+?)\*\*|\[([^\]]+)\]\(([^\s)]+)\)|<(https?://[^>]+)>')


def link(label, href):
    parsed = urlsplit(href)
    if parsed.scheme not in ('', 'https', 'http') or href.startswith('//'):
        return escape(label)
    return '<a href="' + escape(href, quote=True) + '">' + escape(label) + '</a>'


def inline(text):
    parts, end = [], 0
    for match in TOKEN.finditer(text):
        parts.append(escape(text[end:match.start()]))
        code, strong, label, href, url = match.groups()
        if code is not None:
            parts.append('<code>' + escape(code) + '</code>')
        elif strong is not None:
            parts.append('<strong>' + inline(strong) + '</strong>')
        else:
            parts.append(link(label or url, href or url))
        end = match.end()
    parts.append(escape(text[end:]))
    return ''.join(parts)


def render_help(text, raw_href='README.md?raw=1'):
    blocks, headings, paragraph = [], [], []
    list_kind, code_lines = None, None

    def flush_paragraph():
        if paragraph:
            blocks.append('<p>' + inline(' '.join(paragraph)) + '</p>')
            paragraph.clear()

    def close_list():
        nonlocal list_kind
        if list_kind:
            blocks.append('</' + list_kind + '>')
            list_kind = None

    for line in text.splitlines():
        if code_lines is not None:
            if line.startswith('```'):
                blocks.append('<pre><code>' + escape('\n'.join(code_lines)) + '</code></pre>')
                code_lines = None
            else:
                code_lines.append(line)
            continue
        if line.startswith('```'):
            flush_paragraph()
            close_list()
            code_lines = []
            continue
        heading = re.match(r'^(#{1,3})\s+(.+)$', line)
        item = re.match(r'^(?:([-*])\s+|\d+\.\s+)(.+)$', line)
        if heading:
            flush_paragraph()
            close_list()
            level, title = len(heading[1]), heading[2]
            anchor = 'section-' + str(len(headings))
            headings.append((level, anchor, title))
            blocks.append(f'<h{level} id="{anchor}">' + inline(title) + f'</h{level}>')
        elif item:
            flush_paragraph()
            kind = 'ul' if item[1] else 'ol'
            if list_kind != kind:
                close_list()
                blocks.append('<' + kind + '>')
                list_kind = kind
            blocks.append('<li>' + inline(item[2]) + '</li>')
        elif not line.strip():
            flush_paragraph()
            close_list()
        else:
            close_list()
            paragraph.append(line.strip())
    flush_paragraph()
    close_list()
    if code_lines is not None:
        blocks.append('<pre><code>' + escape('\n'.join(code_lines)) + '</code></pre>')
    nav = ''.join('<a href="#' + anchor + '">' + escape(title) + '</a>' for level, anchor, title in headings if level > 1)
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>自动研究智能体 · 使用说明</title><style>
    :root{--ink:#16373c;--muted:#52646b;--bg:#f4f5f1;--line:#d2dcd9;--accent:#146269}*{box-sizing:border-box}html{scroll-padding-top:24px;scroll-behavior:smooth}body{margin:0;background:var(--bg);color:var(--ink);font:16px/1.85 system-ui,"Noto Sans CJK SC",sans-serif;overflow-wrap:anywhere}a{color:var(--accent);text-underline-offset:4px}aside{position:fixed;inset:0 auto 0 0;width:244px;padding:30px 24px;background:var(--ink);color:#e4efeb;overflow:auto}aside h2{font-size:21px;margin:10px 0 24px}aside a{display:block;padding:7px 0;color:#d7e8e1;text-decoration:none;font-size:14px}aside nav{margin:24px 0;border-top:1px solid #54706d;padding-top:16px}main{margin-left:244px;max-width:1400px;padding:40px 5vw 80px}h1{font-size:30px;line-height:1.5;margin:14px 0 28px}h2{font-size:23px;margin:40px 0 16px;padding-top:22px;border-top:1px solid var(--line)}h3{font-size:19px}p{margin:12px 0 18px}li{margin:8px 0}code{font:14px/1.75 ui-monospace,monospace;background:#e8eeeb;padding:2px 5px;border-radius:3px}pre{padding:20px;background:#e8eeeb;max-width:100%;overflow:auto;white-space:pre;font-size:14px;border:1px solid var(--line)}pre code{padding:0;background:none}footer,.meta{font-size:13px;color:var(--muted)}footer{margin-top:36px;border-top:1px solid var(--line);padding-top:20px}a:focus-visible{outline:3px solid var(--accent);outline-offset:3px}@media(max-width:800px){aside{position:static;width:auto;padding:20px 24px}aside h2{margin:0 0 10px}aside nav{display:flex;flex-wrap:wrap;gap:0 20px;margin-bottom:0}main{margin:0;padding:26px 22px 50px}h1{font-size:26px}}@media print{aside{display:none}main{margin:0;padding:0}pre{white-space:pre-wrap;overflow-wrap:anywhere}h2{break-after:avoid}}
    </style></head><body><aside><h2>智能体使用说明</h2><a href="/workspaces/autonomous-research-system/runtime.html">返回操作台</a><a href="/workspaces/autonomous-research-system/index.html">系统设计与汇报图</a><nav aria-label="使用说明章节">''' + nav + '''</nav></aside><main><p class="meta">使用指南 · UTF-8 HTML · 与仓库README同源</p>''' + ''.join(blocks) + '<footer>本页由README.md生成。<a href="' + escape(raw_href, quote=True) + '">查看Markdown源文件</a></footer></main></body></html>'


def build_help():
    output = ROOT / 'usage.html'
    output.write_text(render_help((ROOT / 'README.md').read_text(encoding='utf-8')), encoding='utf-8')
    return output


if __name__ == '__main__':
    print(build_help())
