#!/usr/bin/env python3
"""Lay out existing translations for reading; never invoke a translation model."""
from pathlib import Path
import argparse
import html
import json
import re
import subprocess
import tempfile
from reader_math import MathRenderer, build_cache

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'translations/fulltext'
PAPERS = dict(zip(
    ['autosurvey', 'openscholar', 'surveyforge', 'co-scientist', 'ai-scientist-v2', 'paperbench', 'astabench', 'epoch', 'autoresearch'],
    ['AutoSurvey', 'OpenScholar', 'SurveyForge', 'Co-Scientist', 'AI Scientist-v2', 'PaperBench', 'AstaBench', 'EPOCH', 'autoresearch']))
ABSTRACT_UNITS = {
    'autosurvey': 'autosurvey-0167', 'openscholar': 'openscholar-0023',
    'surveyforge': 'surveyforge-0006', 'co-scientist': 'co-scientist-0008',
    'ai-scientist-v2': 'ai-scientist-v2-0005', 'paperbench': 'paperbench-0015',
    'astabench': 'astabench-0008', 'epoch': 'epoch-0015',
}
CSS = '''
:root{color-scheme:light;font-family:"Noto Sans CJK SC","Microsoft YaHei",sans-serif;color:#252a30;background:#f3f2ee;font-size:17px;line-height:1.95}
*{box-sizing:border-box}body{margin:0}a{color:#23647b;text-underline-offset:4px}
.shell{max-width:1120px;margin:auto;display:grid;grid-template-columns:220px minmax(0,1fr);gap:44px;padding:32px 24px}
aside{position:sticky;top:24px;height:calc(100vh - 48px);overflow:auto;font-size:13px;line-height:1.65}
aside a{display:block;padding:5px 0;text-decoration:none;color:#56626b}aside .current{color:#23647b;font-weight:700}
.contents{margin-top:24px;padding-top:16px;border-top:1px solid #d9dddc}
main{min-width:0;background:#fff;padding:36px 44px}h1{font-size:28px;line-height:1.5;margin:8px 0 12px}h2{font-size:23px;line-height:1.5;margin:36px 0 16px}h3{font-size:19px;line-height:1.6;margin:26px 0 12px}
p{margin:0 0 1.15em;text-align:justify;overflow-wrap:anywhere}h1,h2,h3{overflow-wrap:anywhere;scroll-margin-top:72px}
.subtitle{color:#5d6870;font-size:15px;text-align:left}.meta,.notice{color:#68727a;font-size:12px;line-height:1.8}.notice{border-left:2px solid #c7d3d7;padding-left:12px;margin:20px 0}
details{font-size:14px}summary{cursor:pointer;color:#60737f;line-height:1.7}details p{margin-top:10px}.source{margin-top:-12px;margin-bottom:20px;font-size:13px;border-left:2px solid #e5e9e8;padding-left:12px}.source p{color:#55626a;line-height:1.8}
.frontmatter{margin:18px 0}.frontmatter .original{white-space:pre-wrap;overflow-wrap:anywhere}
.toolbar{position:sticky;top:0;z-index:2;display:flex;align-items:center;gap:14px;flex-wrap:wrap;background:#fff;border-bottom:1px solid #e1e5e5;padding:10px 0;margin:24px 0;font-size:13px}
button{font:inherit;color:#345d6c;background:#f6f8f8;border:1px solid #ccd7da;border-radius:4px;padding:5px 10px;cursor:pointer}
.caption{font-size:14px;color:#57656d;line-height:1.8;margin:18px 0}.page-anchor{display:block;scroll-margin-top:70px}
.technical{white-space:pre-wrap;overflow-wrap:anywhere;word-break:break-word;font:12px/1.8 "Noto Sans CJK SC",monospace;background:#f6f7f6;padding:14px;max-width:100%;margin:12px 0 20px}
.technical-section{margin:20px 0}.reference{font-size:12px;line-height:1.8;color:#5c666e}.quality{color:#91651c;font-size:12px}.reading-note{font-size:12px;color:#66737a;margin:24px 0}
.paper-list{padding:18px 0;border-bottom:1px solid #e2e5e4}.paper-list h2{margin:0 0 6px;font-size:22px}.paper-list p{font-size:14px;margin:4px 0}.paper-list nav{display:flex;gap:20px;font-size:14px}
footer{margin-top:40px;border-top:1px solid #ddd;padding-top:16px}.index{max-width:880px;margin:32px auto}
@media(max-width:800px){.shell{display:block;padding:12px}aside{position:static;height:auto}.library{display:flex;gap:12px;flex-wrap:wrap}.contents{display:none}main{padding:24px 20px;margin-top:16px}h1{font-size:24px}:root{font-size:16px}.index{margin:12px}}
@media print{@page{size:A4;margin:20mm 19mm}html,body{background:#fff;font-size:10.5pt;line-height:1.85}.shell{display:block;padding:0;max-width:none}aside,.toolbar,.source,.frontmatter,.screen-only{display:none!important}main{padding:0}h1{font-size:22pt}h2{font-size:15pt}h3{font-size:12pt}h1,h2,h3,summary{break-after:avoid}p{orphans:3;widows:3}.technical{font-size:8pt;background:none;border:1px solid #ddd;white-space:pre-wrap}.caption{font-size:9pt}.notice,.meta,.reading-note{font-size:8pt}a{color:inherit;text-decoration:none}.reference{font-size:8pt}.quality{font-size:8pt}footer{font-size:8pt}}
'''
CSS += '''
.katex{font-size:1.05em}.math-inline{display:inline;overflow-wrap:normal}.math-block{overflow:auto;padding:12px 0}.math-unresolved{color:#91651c;font-size:13px}.restored-math{margin:16px 0;padding:12px;border-left:2px solid #cbd9dd}
math{font-family:"Latin Modern Math","STIX Two Math",serif}.visual-original{max-width:100%;overflow:auto;margin:24px 0}.visual-original figure{margin:0}.visual-original img{display:block;max-width:100%;height:auto;margin:8px auto;cursor:zoom-in}.visual-original table{border-collapse:collapse;font-size:12px;line-height:1.6;margin:auto}.visual-original td,.visual-original th{padding:5px 7px}.visual-original td img{width:100%}.visual-original .ltx_tr:first-child{border-top:1px solid #7f8b90}.visual-original .ltx_tr:last-child{border-bottom:1px solid #7f8b90}.visual-original .ltx_font_bold{font-weight:700}.visual-original .ltx_align_center{text-align:center}.visual-original .ltx_align_right{text-align:right}.visual-original .ltx_align_left{text-align:left}.visual-original .ltx_eqn_table{width:100%}.visual-original .ltx_eqn_eqno{font-size:12px;min-width:30px}.visual-original .ltx_listing{white-space:pre-wrap;font-family:monospace}.translation-labels{margin:8px 0 20px}
.original-page{margin:20px 0;padding:14px;border:1px solid #e1e6e8;break-inside:avoid}.original-page img{display:block;max-width:100%;max-height:300px;width:auto;margin:auto;cursor:zoom-in}.original-page figcaption{font-size:12px;color:#60737f;text-align:center;margin-top:8px}.image-viewer{border:1px solid #b7c3c9;max-width:96vw;max-height:95vh;padding:16px}.image-viewer::backdrop{background:#24313cbb}.image-viewer img{display:block;max-width:90vw;height:auto;max-height:none}.image-viewer button{position:sticky;top:0;float:right}
.visual-original .ltx_listing{white-space:normal;text-align:left;font:12px/1.8 ui-monospace,monospace}.visual-original .ltx_listingline{white-space:normal;display:block;margin:4px 0;break-inside:avoid}.visual-original .ltx_tag_listingline{display:inline-block;min-width:26px;color:#66737a}
.figure-with-caption{break-inside:avoid}
.original-text-panel{border:1px solid #d8e0e3;padding:14px;margin:8px 0;font-size:13px;line-height:1.6}.original-text-panel p{margin:0 0 8px;line-height:1.6;text-align:left}.original-text-panel .ltx_minipage{max-width:100%;width:auto}.original-text-panels{max-width:100%;overflow-wrap:anywhere}
.paper-list{padding:28px 0}.paper-list .abstract-label{font-size:12px;color:#68727a;margin:18px 0 6px}.paper-list .paper-abstract{font-size:16px;line-height:1.95;margin:0 0 18px}
@media print{.visual-original{overflow:visible}.visual-original img{max-height:220mm;object-fit:contain}.original-page img{max-height:70mm}.image-viewer{display:none}footer{break-before:avoid;break-inside:avoid}}
'''


def e(s):
    # PDF extraction occasionally contains nonprinting control characters.
    clean = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', str(s))
    return html.escape('\n'.join(line.rstrip() for line in clean.split('\n')))


def text(s):
    return re.sub(r'[ \t]+', ' ', s).strip()


def heading(u):
    return text(re.sub(r'^#{1,6}\s*', '', u.get('zh') or u['en']))


def heading_level(u):
    en = re.sub(r'^#+\s*', '', u['en']).strip()
    return 3 if re.match(r'^\d+\.\d+', en) or not re.match(r'^(\d+\s|[A-Z]\s|Abstract|Summary|Introduction|Discussion|Conclusion|References|Methods|Appendix)', en, re.I) else 2


def prose_markdown(s):
    # Some translated appendix examples contain Markdown headings flattened
    # into one extraction unit. Restore their boundaries without rewriting text.
    s = re.sub(r'(?<!#)(#{2,6})\s*', r'\n\n\1 ', text(s))
    s = re.sub(r'(#{2,6} [^\n]+?)(?=\n\n#)', r'\1\n', s)
    return s.strip()


def prose_html(s, math_renderer):
    parts = []
    for block in re.split(r'\n\s*\n', prose_markdown(s)):
        # A flattened heading may share its block with prose. Keep it as a
        # subheading only when short, rather than enlarging a whole paragraph.
        match = re.match(r'^(#{2,6})\s+(.+)$', block, re.S)
        if match and len(match[2]) < 100:
            parts.append('<h3>' + math_renderer.inline(match[2]) + '</h3>')
        else:
            rendered = re.sub(r'\*\*([^*\n]+)\*\*', r'<strong>\1</strong>', math_renderer.inline(match[2] if match else block))
            rendered = re.sub(r'`([^`\n]+)`', r'<code>\1</code>', rendered)
            parts.append('<p>' + rendered + '</p>')
    return ''.join(parts)


def document(title, body):
    extra = '.shell:has(>main:only-child){display:block;max-width:880px}@media print{:root{background:#fff}@page{@bottom-center{content:counter(page);font:8pt sans-serif;color:#66737a}}}'
    katex_css = '../assets/katex/katex.min.css' if 'class="shell"' in body else 'assets/katex/katex.min.css'
    rendered = '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+e(title)+'</title><link rel="stylesheet" href="'+katex_css+'"><style>'+CSS+extra+'</style></head><body>'+body+'</body></html>'
    return '\n'.join(line.rstrip() for line in rendered.split('\n'))


def render(slug, label, overrides, math_cache):
    folder = BASE / slug
    data = json.loads((folder / 'bilingual.json').read_text())
    src = data['source']
    visual_path = folder / 'visuals.json'
    visuals = json.loads(visual_path.read_text()) if visual_path.exists() else {}
    math_renderer = MathRenderer(visuals, math_cache)
    units = [dict(u, zh=overrides.get(u['id'], u.get('zh', ''))) for u in data['units']]
    # These are LaTeXML warnings, already excluded from the previous reader.
    units = [u for u in units if not (slug == 'paperbench' and u['id'] in [f'paperbench-{i:04d}' for i in range(1, 5)])]
    title = next((u['zh'] for u in units if u.get('status') == 'manual_title'), label)
    version = src.get('arxiv', src.get('commit', ''))
    if src.get('source_format') == 'ACL formal version':
        version = 'ACL 2025 / 2025.acl-long.609'
    source_url = 'https://arxiv.org/abs/' + src['arxiv'] if 'arxiv' in src else 'https://github.com/karpathy/autoresearch/tree/' + src['commit']
    if src.get('source_format') == 'ACL formal version':
        source_url = 'https://aclanthology.org/2025.acl-long.609/'
    pdf = f'../../../sources/fulltext/{slug}/original.pdf'
    authors = '; '.join(html.unescape(x) for x in src.get('authors', [])) or 'Andrej Karpathy（仓库维护者）'
    notice = '非官方机器初译，正文尚未逐段精校。图表保留原文内容，图内英文未另行翻译；有 HTML 原文的公式按原式排版。PDF 提取版保留对应原页，点击缩略图放大核对图表与公式。'
    frontmatter = [u for u in units if u['kind'] == 'frontmatter' and u.get('status') != 'manual_title']
    header = f'<header><p class="meta">全文中文阅读 · {e(label)}</p><h1>{e(title)}</h1><p class="subtitle">{e(src["title"])}</p><p class="meta">{e(authors)}</p><p class="notice">{e(notice)}</p><p class="meta">原文版本：{e(version)} · 获取日期：{e(src["retrieved"])}</p>'
    header += f'<p class="meta screen-only"><a href="{e(source_url)}">原始来源</a> · <a href="{e(pdf) if "pages" in src else "../../../sources/fulltext/autoresearch/README.md"}">原文文件</a> · <a href="../../../output/pdf/{slug}-zh-reading.pdf">中文 PDF</a></p></header>'
    author_block = '<details class="frontmatter"><summary>作者、机构和出版信息</summary><div class="original">' + '\n'.join(e(u['en']) for u in frontmatter) + '</div></details>' if frontmatter else ''
    toolbar = '<div class="toolbar"><button id="toggle-originals" type="button">展开全部英文</button><button type="button" onclick="window.print()">打印 / 保存 PDF</button><a href="#top">回到开头</a></div>'
    md_header = f'# {title}\n\n{src["title"]}\n\n{authors}\n\n> {notice}\n\n原文版本：{version} · [原始来源]({source_url}) · [中文 PDF](../../../output/pdf/{slug}-zh-reading.pdf)\n\n'
    clean_md = [md_header]
    bilingual_md = [md_header]
    if frontmatter:
        bilingual_md.append('<details>\n<summary>作者、机构和出版信息</summary>\n\n' + '\n\n'.join(u['en'] for u in frontmatter) + '\n\n</details>\n\n')
    body = []
    print_body = []
    toc = []
    rendered_ids = []
    page = None
    for u in units:
        uid, kind, en, zh = u['id'], u['kind'], u['en'], u['zh']
        if kind == 'frontmatter':
            continue
        if kind == 'page':
            page = u['page']
            source_page = visuals.get('original_pages', {}).get(str(page))
            page_html = f'<span class="page-anchor" id="{e(uid)}"></span>'
            if source_page:
                page_html += f'<figure class="original-page"><a href="{e(source_page)}" target="_blank"><img src="{e(source_page)}" loading="lazy" alt="原文第 {page} 页：完整图表与公式"></a><figcaption>原文第 {page} 页 · 点击放大查看原图、表格和公式 · <a href="{e(pdf)}#page={page}">原始 PDF</a></figcaption></figure>'
                clean_md.append(f'[原文第 {page} 页的完整图表与公式]({source_page})\n\n')
                bilingual_md.append(f'[原文第 {page} 页的完整图表与公式]({source_page})\n\n')
            body.append(page_html)
            print_body.append(page_html)
            continue
        if uid in visuals.get('suppress', []):
            body.append(f'<span id="{e(uid)}"></span>')
            continue
        if not zh and u.get('translate'):
            raise ValueError(f'{uid}: missing translation')
        zh = zh or en
        zh, restored_math = math_renderer.restore(u, zh)
        rendered_ids.append(uid)
        # Keep original IDs and source location in disclosure, out of the prose.
        location = f' · PDF 第 {page} 页' if page else ''
        original = f'<details class="source"><summary>英文原文{location}</summary><p lang="en">{math_renderer.inline(en)}</p><small>{e(uid)}</small></details>'
        md_original = '\n<details>\n<summary>英文原文' + location + '</summary>\n\n' + en + '\n\n</details>\n\n'
        if kind == 'heading':
            level = heading_level(u)
            label_zh = heading(u)
            section = f'<h{level} id="{e(uid)}">{math_renderer.inline(label_zh)}</h{level}>'
            md = '#' * level + ' ' + label_zh + '\n\n'
            toc.append((uid, label_zh))
        elif kind in ['table', 'code', 'formula']:
            category = {'table': '表格与文字对照', 'code': '代码（保留原文）', 'formula': '公式'}[kind]
            # A reflowing block preserves extracted rows without inventing cells.
            section = f'<section class="technical-section" id="{e(uid)}"><p class="meta">{category}</p><div class="technical">{math_renderer.inline(zh)}</div></section>'
            md = f'**{category}**\n\n```text\n{zh.replace("```", "~~~")}\n```\n\n'
        elif kind == 'reference':
            section = f'<p class="reference" id="{e(uid)}">{math_renderer.inline(zh)}</p>'
            md = zh + '\n\n'
            original = '' if zh == en else original
            md_original = '' if zh == en else md_original
        elif kind in ['caption', 'figure-label']:
            section = f'<p class="caption" id="{e(uid)}">{math_renderer.inline(text(zh))}</p>'
            md = text(zh) + '\n\n'
        else:
            section = f'<section id="{e(uid)}">{prose_html(zh, math_renderer)}</section>'
            md = prose_markdown(zh) + '\n\n'
        visual = visuals.get('visuals', {}).get(uid)
        if visual:
            image_html = '<div class="visual-original">' + visual['html'] + '</div>'
            if kind in {'table', 'formula', 'figure-label', 'code'} or slug == 'autoresearch' and '![teaser]' in en:
                section = f'<section id="{e(uid)}">{image_html}</section>'
                if kind == 'table':
                    section += '<details class="translation-labels"><summary>表内文字译注</summary><div class="technical">' + math_renderer.inline(zh) + '</div></details>'
            else:
                section = '<section class="figure-with-caption">' + image_html + section + '</section>'
            md = f'[查看原图表（阅读版）](bilingual.html#{uid})\n\n' + md
        section += restored_math
        warning = u.get('flags', []) if uid not in overrides else []
        if warning:
            section += '<p class="quality">此段有自动质量标记，请结合英文核对。</p>'
        body.append(section + original)
        print_body.append(section)
        clean_md.append(md)
        bilingual_md.append(md + md_original)
    links = ''.join(f'<a class="{"current" if key == slug else ""}" href="../{key}/bilingual.html">{name}</a>' for key, name in PAPERS.items())
    toc_html = ''.join(f'<a href="#{e(uid)}">{e(name)}</a>' for uid, name in toc)
    sidebar = '<aside><a href="../index.html">全部文章</a><div class="library">' + links + '</div><nav class="contents">' + toc_html + '</nav></aside>'
    footer = '<footer><p class="meta">译文模型：tencent/HY-MT2-1.8B。版式整理不代表全文已校对。原文许可：' + e(src['licence']) + '。原文与译文逐段对应关系保存在 bilingual.json。</p></footer>'
    script = '''<dialog class="image-viewer" id="image-viewer"><button type="button">关闭</button><img alt="原图放大"></dialog><script>document.getElementById('toggle-originals').addEventListener('click',function(){const items=[...document.querySelectorAll('details.source')];const open=items.some(x=>!x.open);items.forEach(x=>x.open=open);this.textContent=open?'收起全部英文':'展开全部英文';});const viewer=document.getElementById('image-viewer');viewer.querySelector('button').onclick=()=>viewer.close();document.querySelectorAll('.visual-original img,.original-page img').forEach(img=>img.addEventListener('click',event=>{event.preventDefault();viewer.querySelector('img').src=img.src;viewer.showModal();}));viewer.addEventListener('click',event=>{if(event.target===viewer)viewer.close();});</script>'''
    (folder / 'bilingual.html').write_text(document(title, '<div class="shell">' + sidebar + '<main id="top">' + header + author_block + toolbar + ''.join(body) + footer + '</main></div>' + script))
    print_content = (header + ''.join(print_body) + footer).replace('loading="lazy"', 'loading="eager"').replace('decoding="async"', 'decoding="sync"')
    (folder / 'reading.html').write_text(document(title, '<div class="shell"><main id="top">' + print_content + '</main></div>'))
    (folder / 'bilingual.md').write_text('\n'.join(line.rstrip() for line in ''.join(bilingual_md).splitlines()) + '\n')
    (folder / 'reading.md').write_text('\n'.join(line.rstrip() for line in ''.join(clean_md).splitlines()) + '\n')
    (folder / 'render-quality.json').write_text(json.dumps(dict(restored_math_units=math_renderer.restored, appended_source_formulas=math_renderer.appended, unresolved_formulas=sorted(set(math_renderer.errors)), original_visual_blocks=len(visuals.get('visuals', {})), original_pdf_pages=len(visuals.get('original_pages', {}))), ensure_ascii=False, indent=2) + '\n')
    return dict(slug=slug, label=label, title=title, body_units=len(rendered_ids), ids=rendered_ids)


def make_pdfs():
    target = ROOT / 'output/pdf'
    target.mkdir(parents=True, exist_ok=True)
    for slug in PAPERS:
        # A dedicated profile avoids attaching to the user's running browser.
        with tempfile.TemporaryDirectory(prefix='uav-reader-chrome-') as profile:
            result = subprocess.run(['google-chrome', '--headless', '--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--no-pdf-header-footer', '--no-first-run', f'--user-data-dir={profile}', f'--print-to-pdf={target / (slug + "-zh-reading.pdf")}', (BASE / slug / 'reading.html').as_uri()], capture_output=True, text=True, timeout=120)
            if result.returncode or not (target / (slug + '-zh-reading.pdf')).exists():
                raise RuntimeError(result.stderr[-2000:])
        print(f'PDF: {slug}', flush=True)


def catalog_entry(item, overrides, summaries):
    slug = item['slug']
    if slug in ABSTRACT_UNITS:
        abstract = overrides[ABSTRACT_UNITS[slug]]
        # This source extraction unit also contains the beginning of section 1.
        # Show only the paper's abstract in the catalog.
        if slug == 'surveyforge':
            abstract = abstract.split('\n\n1 引言', 1)[0]
        label = '摘要 · 中文译文'
    else:
        abstract = summaries[slug]['zh']
        label = '文档简介'
    return (
        f'<section class="paper-list" id="{e(slug)}">'
        f'<h2><a href="{slug}/bilingual.html">{e(item["label"])}</a></h2>'
        f'<p>{e(item["title"])}</p><p class="abstract-label">{label}</p>'
        f'<p class="paper-abstract">{e(abstract)}</p>'
        f'<nav><a href="{slug}/bilingual.html">开始阅读</a>'
        f'<a href="../../output/pdf/{slug}-zh-reading.pdf">中文 PDF</a>'
        f'<a href="{slug}/reading.md">中文 Markdown</a></nav></section>'
    )


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('--pdf', action='store_true', help='Also print all nine Chinese readers as PDFs using local Chrome')
    args = parser.parse_args(argv)
    overrides = json.loads((ROOT / 'data/fulltext-translation-overrides.json').read_text())['translations']
    overrides.update(json.loads((ROOT / 'data/fulltext-visual-corrections.json').read_text())['translations'])
    math_cache = build_cache()
    report = [render(slug, label, overrides, math_cache) for slug, label in PAPERS.items()]
    intro = '8 篇论文和 autoresearch 文档。下方展示论文摘要的中文译文，autoresearch 展示文档简介。阅读全文可展开英文对照；正文仍为待精校初稿。'
    summaries = {item['slug']: item for item in json.loads((ROOT / 'data/fulltext-paper-summaries.json').read_text())}
    entries = ''.join(catalog_entry(item, overrides, summaries) for item in report)
    (BASE / 'index.html').write_text(document('Auto Research · 中文论文阅读', '<main class="index"><h1>中文论文阅读</h1><p class="subtitle">' + intro + '</p>' + entries + '</main>'))
    readme = '# 中文论文阅读\n\n' + intro + '\n\n**浏览器阅读：[打开全部文章](http://127.0.0.1:18766/) · [直接打开 AutoSurvey](http://127.0.0.1:18766/translations/fulltext/autosurvey/bilingual.html)。**\n\n这些 HTTP 地址仅适用于运行阅读服务的这台电脑。请在浏览器打开；编辑器没有 PDF 查看插件时，直接点击文件会显示源码。服务脚本为 `scripts/serve_fulltext_reader.py`，默认仅监听 `127.0.0.1:18766`，只提供论文阅读相关文件。\n\n离线阅读可选下方的中文 PDF，或中文 Markdown 预览。\n\n'
    for x in report:
        slug = x['slug']
        readme += f'- **{x["label"]}**：[中文 PDF](../../output/pdf/{slug}-zh-reading.pdf) · [中文 Markdown]({slug}/reading.md) · [可展开英文的阅读版]({slug}/bilingual.html)\n'
    readme += '\n原文文件及版本见 [原文清单](../../sources/fulltext/manifest.json)。原始译文及对应关系仍保存在各目录的 bilingual.json，自动质量标记见 [质量记录](quality-report.json)。本次仅调整阅读排版，未重新调用模型。图表原貌以原文 PDF 为准。\n'
    readme += '\n## 原图与公式\n\nHTML 来源的原图、原始表格和公式已恢复，图可点击放大，数学排版使用本地 KaTeX 0.19.1 和原文 MathML，不依赖外部 CDN。图内英文保留原样。PDF 提取版提供对应原页的可放大预览，保留图表及公式；SurveyForge 使用 ACL 正式版原页，不与 arXiv 预印本混用。\n\n各文章的 `visuals.json` 记录图资源的来源 URL、SHA-256、原文标识及对应译文单元；`render-quality.json` 记录公式补回及渲染检查。AutoSurvey 六段中的变量遗漏、位置和量纲误译依据固定版本原文修正，见 `data/fulltext-visual-corrections.json`。其余译文仍为未逐段精校的机器初稿。\n\n重新生成（不调用模型）：\n\n```sh\nnpm install --prefix .cache/reader-tools --no-audit --no-fund katex@0.19.1\npython3 scripts/prepare_reader_visuals.py\npython3 scripts/render_readable_fulltext.py --pdf\n```\n\n需要 Python 的 BeautifulSoup、系统 Poppler 和 Chrome。原始 PDF、HTML、原始译文保持不变；生成的原页 JPEG 和 PDF 不纳入 Git。\n'
    (BASE / 'README.md').write_text(readme)
    if args.pdf:
        make_pdfs()
    print(json.dumps([dict(slug=x['slug'], body_units=x['body_units']) for x in report], ensure_ascii=False))


if __name__ == '__main__':
    main()
