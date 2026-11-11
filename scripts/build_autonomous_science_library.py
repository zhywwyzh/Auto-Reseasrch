#!/usr/bin/env python3
"""Render the curated collection; offline, with no model calls.

Tracked: Chinese reading guide, provenance and code commit records.
Ignored: original papers, raw English extracts and local bilingual readers.
Do not turn a private raw original into a tracked redistribution by rendering.
"""
import hashlib
import html
import json
import os
from pathlib import Path
import re
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'docs/research/autonomous-science-2026-11-10/library'
NOTES = ROOT / 'thesis-reference/notes/autonomous-science-2026-11-10'


def read(name):
    return json.loads((LIB / name).read_text())


def esc(s):
    return html.escape(str(s), quote=True)


def relative(origin, target):
    return quote(os.path.relpath(target, origin), safe='/')


def link(url, title):
    return f'<a href="{esc(url)}">{esc(title)}</a>'


def css():
    base = (LIB.parent / 'index.html').read_text()
    style = re.search(r'<style>(.*?)</style>', base, re.S).group(1)
    return style + '''
    .library-entry{padding:28px 0;border-bottom:1px solid var(--line)}
    .library-entry h2{font-size:23px}.reading{max-width:1000px}
    .translation{background:var(--paper);border:1px solid var(--line);padding:18px 22px;line-height:1.95}
    .references{font-size:13px;color:var(--muted)}.pill{display:inline-block;background:var(--soft);padding:3px 8px;margin:2px 6px 2px 0;font-size:12px}
    .meta-row{display:flex;gap:10px;flex-wrap:wrap;margin:12px 0}.terms{font-size:14px;display:flex;gap:8px;flex-wrap:wrap}
    .term{border:1px solid var(--line);padding:5px 9px;background:var(--paper)}
    .english{white-space:pre-wrap;font-size:15px;line-height:1.9}.stat{font-size:23px;font-weight:650}
    .commit{font-family:monospace;font-size:12px;overflow-wrap:anywhere}code{overflow-wrap:anywhere;font-size:13px}
    pre{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--paper);border:1px solid var(--line);padding:18px}a{overflow-wrap:anywhere}
    .repo-row th{min-width:140px}.repo-row td{min-width:150px}.repo-row td:last-child{min-width:230px}
    @media print{.library-entry{break-inside:auto}.translation{break-inside:avoid}.library-entry[hidden]{display:block!important}}
    '''


def shell(title, body, nav):
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><style>{css()}</style></head><body>
    <aside><div class="eyebrow">AUTONOMOUS SCIENCE / LIBRARY</div><strong>记录、译读与源码</strong><p class="small extra">2026-11-10 固定版本资料集<br>原文事实 / 译文 / 分析分开</p><nav aria-label="资料导航">{nav}</nav></aside><main>{body}</main></body></html>'''


def selected_english(paper, source):
    slug = paper['id']
    dest = NOTES / slug
    dest.mkdir(parents=True, exist_ok=True)
    if slug == 'autodna':
        text = (ROOT / 'external/autonomous-science/autodna/README.md').read_text()
        a = text.index('AutoDNA is a comprehensive')
        intro = text[a:text.index('\n\n', a)]
        a = text.index('## System Overview')
        b = text.index('## 🏗', a)
        return intro + '\n\n' + text[a:b].strip()
    if slug == 'mombot':
        text = (ROOT / 'external/autonomous-science/mombot-software/README.md').read_text()
        a = text.index('This repository contains')
        first = text[a:text.index('\n\n', a)]
        a = text.index('This software was used')
        one_sentence = text[a:text.index('Across n=', a)].strip()
        a = text.index('**Hardware note:**')
        b = text.index('## System Architecture')
        return first + '\n\n' + one_sentence + '\n\n' + text[a:b].strip()
    if slug == 'autoresearch':
        text = (ROOT / 'external/autonomous-science/autoresearch/README.md').read_text()
        a = text.index('The idea:')
        b = text.index('## Quick start')
        return text[a:b].strip()
    if source.get('abstract_local'):
        text = (ROOT / source['abstract_local']).read_text().strip()
        if slug == 'omniscientist':
            return text[:text.index('We introduce OmniScientist')].strip()
        if slug == 'alphaevolve':
            return text[:text.index('Using an evolutionary approach')].strip()
        return text
    if slug == 'ai-scientist-nature':
        text = (ROOT / source['extracted_text']).read_text().split('\f')[0]
        start = text.index('The automation of science is a long-standing ambition')
        stop = text.index('autonomous systems could greatly accelerate scientific discovery.', start)
        return ' '.join(text[start:stop + len('autonomous systems could greatly accelerate scientific discovery.')].split())
    return ''


def main():
    registry, notes = read('registry.json'), read('reading-notes.json')
    sources = {p['id']: p for p in read('sources.json')}
    repos = {p['id']: p for p in read('repositories.json')}
    readings = {p['id']: p for p in notes['items']}
    entries, audit = [], []
    for paper in registry['papers']:
        slug = paper['id']
        note, source = readings[slug], sources[slug]
        repo = repos.get(paper.get('repo'))
        en = selected_english(paper, source)
        english_file = NOTES / slug / 'translation-source-en.txt'
        if en:
            # This is a generated selection, not an original input file.
            english_file.write_text(en + '\n')
        original_pdf = next((ROOT / f['path'] for f in source.get('files', []) if f['path'].endswith('.pdf')), None)
        local_dir = NOTES / slug
        local_file = local_dir / 'bilingual.html'
        origin = 'https://arxiv.org/abs/' + paper['arxiv'] if paper.get('arxiv') else paper['web']
        links = [link(origin, '原始论文 / 官方文档')]
        if paper.get('doi'):
            links.append(link('https://doi.org/' + paper['doi'], '正式 DOI'))
        if original_pdf:
            links.append(link(relative(LIB, original_pdf), f'本机原文 PDF · {source["pages"]}页'))
        links.append(link(relative(LIB, local_file), '本机中英对照'))
        if paper.get('existing'):
            previous = ROOT / 'translations/fulltext' / slug / 'bilingual.html'
            if previous.exists():
                links.append(link(relative(LIB, previous), '既有全文译稿（未重译）'))
        if repo:
            links.append(link(repo['url'].removesuffix('.git'), '官方代码 / 发布资料'))
        refs = ''.join(f'<li><b>{esc(r["section"])}</b><br>{esc(r["locator"])} · {esc(r["source_kind"])}</li>' for r in note['references'])
        methods = ''.join(f'<li>{esc(p)}</li>' for p in note['method_zh'])
        limits = ''.join(f'<li>{esc(p)}</li>' for p in note['limits_zh'])
        terms = ''.join(f'<span class="term">{esc(en_term)} → {esc(zh_term)}</span>' for en_term, zh_term in note['terms'])
        code = ''
        if repo:
            points = ' · '.join(link(relative(LIB, ROOT / repo['path'] / p), p) for p in note['code_entrypoints'])
            code = f'<p class="small"><b>本机代码入口：</b>{points}</p><p class="commit">固定提交 {esc(repo.get("commit", "未取得"))}</p>'
        form = f'<div class="notice"><b>方法表示与条件：</b>{esc(note["formula"])}</div>' if note.get('formula') else ''
        content = f'''<div class="meta-row"><span class="pill">{esc(paper.get('arxiv', paper.get('doi', '官方文档')))}</span><span class="pill">原作者报告，未运行实验</span></div>
        <h2>{esc(paper['title_zh'])}</h2><p class="small">{esc(source.get('title', ''))}</p>
        <h3>中文翻译</h3><p class="small">{esc(note['translation_kind'])}</p><div class="translation">{esc(note['abstract_zh'])}</div>
        <h3>核心方法 · 原创译解</h3><ol>{methods}</ol>{form}
        <h3>局限与证据边界</h3><ul>{limits}</ul>
        <p><b>开放范围：</b>{esc(note['open_status'])}</p>{code}
        <details><summary>术语与来源定位</summary><div class="terms">{terms}</div><ul class="references">{refs}</ul><p class="small">论文许可：{esc(source.get('paper_license_url') or '见原文页面；本轮未建立统一改编许可')}。页序绑定所列版本，不能与其他版本混用。</p></details>
        <div class="sources">{' · '.join(links)}</div>'''
        entries.append(f'<article class="library-entry reading" id="{esc(slug)}" data-repo="{esc(paper.get("repo", "none"))}">{content}</article>')
        bilingual = f'''<section><div class="eyebrow">本机研究资料 / LOCAL READING</div><h1>{esc(paper['title_zh'])}</h1>
        <p class="notice">{esc(note['translation_kind'])}。译文与原文按此范围对照；核心方法另有原创译解。不是整篇论文的逐段翻译。此页位于Git忽略目录，没有公开发布。</p>
        <h2>中文译文</h2><div class="translation">{esc(note['abstract_zh'])}</div>
        <details open><summary>原文对照 · {esc(paper.get('arxiv', '固定提交的官方文档'))}</summary><div class="english">{esc(en)}</div></details>
        <p class="small">{link(origin,'原始来源')} · {link(relative(local_dir,LIB / 'index.html')+'#'+slug,'返回方法与开放范围')}</p></section>
        <section><h2>方法译解</h2><ol>{methods}</ol>{form}<h2>局限</h2><ul>{limits}</ul><ul class="references">{refs}</ul></section>'''
        local_file.write_text(shell(paper['title_zh'] + ' · 中英对照', bilingual,
                                    link(relative(local_dir, LIB / 'index.html'), '资料总入口')))
        if not en:
            raise ValueError('missing original translation source: ' + slug)
        audit.append({'id':slug, 'translation_kind':note['translation_kind'],
                      'original_en_sha256':hashlib.sha256(en.encode()).hexdigest(),
                      'translation_zh_sha256':hashlib.sha256(note['abstract_zh'].encode()).hexdigest(),
                      'english_chars':len(en), 'chinese_chars':len(note['abstract_zh']),
                      'local_reader':str(local_file.relative_to(ROOT)), 'independently_reproduced':False})
    pdf_count = sum(x.get('status') == 'full-paper-downloaded' for x in sources.values())
    total_pages = sum(x.get('pages', 0) for x in sources.values())
    stats = f'''<div class="three"><div class="path"><div class="stat">{len(entries)} 项</div>中文译读及证据记录</div><div class="path"><div class="stat">{pdf_count} 份 / {total_pages} 页</div>本机完整PDF，含2份复用原件</div><div class="path"><div class="stat">{len(repos)} 个</div>固定提交的公开代码／资料库</div></div>'''
    rows = []
    for repo in repos.values():
        licence_links = ' · '.join(link(relative(LIB, ROOT / repo['path'] / f['path']), f['path']) for f in repo.get('license_files', []))
        if not licence_links:
            licence_links = link(relative(LIB, ROOT / repo['path'] / 'README.md'), 'README声明或缺失记录')
        rows.append(f'''<tr class="repo-row"><th>{link(repo['url'].removesuffix('.git'), repo['id'])}</th><td>{esc(repo.get('license_name', '未核验'))}<br>{licence_links}</td><td>{esc(repo['scope'])}</td><td><code>{esc(repo['path'])}</code><div class="commit">{esc(repo.get('commit','未取得'))}</div><div class="small">{esc(repo.get('commit_date',''))}</div></td></tr>''')
    notices = '''<div class="notice"><b>本轮翻译范围：</b>11篇摘要全文翻译；AutoDNA与MOMbot采用官方代码文档概述译文，autoresearch为项目文档译文；OmniScientist与AlphaEvolve为摘要选段翻译和方法译解。没有将这些标成全文论文译本。Co-Scientist和AI Scientist-v2的既有全文初稿保留原入口，没有重新翻译。</div>
    <div class="notice warning"><b>拉取不等于实现或复现：</b>没有安装上游依赖、运行上游代码、训练模型或调用付费API。公开代码中还包括带用途限制、许可证未明确、仅公开验证产物等不同情况。下表按当前固定提交区分。</div>'''
    body = f'''<section id="collection"><div class="eyebrow">资料集 / 2026-11-10</div><h1>AI自主科研：中文译读与固定版本源码</h1><p class="lead">对应上一轮代表性进展，补齐论文原件、方法说明、来源定位与实际可获取的代码。</p>{stats}{notices}
    <p class="small">{link('../index.html','返回进展综述')} · {link('registry.json','资料注册表')} · {link('sources.json','原件校验和与抓取结果')} · {link('repositories.json','代码提交与许可记录')} · {link('reading-notes.json','中文译读可编辑源')}</p></section>
    <section id="reading"><h2>中文译读</h2><div class="tools"><label>按标题、术语或方法查找<input id="query" type="search" placeholder="例如：树搜索、假设、溯因、复现…"></label><label>代码范围<select id="repo-filter"><option value="all">全部</option><option value="fetched">有已拉取的对应代码／资料</option><option value="none">尚未核验到对应系统源码</option></select></label><button id="reset" type="button">重置</button><span id="count" class="count" role="status" aria-live="polite"></span></div>{''.join(entries)}<p id="empty" hidden>没有匹配条目，可重置筛选。</p></section>
    <section id="code"><h2>固定提交与开放范围</h2><p>子模块保留上游来源与许可证，主仓库保存提交指针。代码工作区已稀疏检出，排除论文PDF、媒体、运行日志、权重与大文件；Git对象库可能仍保留首次拉取时已传输的对象。DISCERN未下载LFS载荷。</p><div class="scroll"><table><thead><tr><th>上游项目</th><th>实际许可证据</th><th>覆盖范围</th><th>本机位置与提交</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div></section>
    <section id="boundaries"><h2>原文、翻译和Git边界</h2><ul><li>论文原件在<code>thesis-reference/related-papers/autonomous-science-2026-11-10/</code>；原始英文、提取文本与本机中英对照在<code>thesis-reference/notes/autonomous-science-2026-11-10/</code>，这些路径整体被Git忽略。</li><li>13份完整PDF共{total_pages}页，包含复用的Co-Scientist和AI Scientist-v2。MOMbot保存了完整HTML，但PDF端点返回429；AutoDNA保存PubMed公开摘要，期刊全文未获取。autoresearch是项目文档，没有对应论文PDF。</li><li>主仓库可跟踪中文译读、来源元数据、许可证证据、构建脚本、子模块配置与固定提交。原图、原始论文和大数据不因此进入主仓库上传范围。</li><li>论文、代码、数据的许可证分别记录；根目录代码许可证不自动覆盖论文或第三方数据。来源比较是阅读记录，不是法律意见或对所有文件的许可审计。</li><li>“作者报告”不等于独立复验；“方法译解”是本轮原创解释；“已拉取”只说明取得代码或公开产物，不表示环境可运行或数值已复现。</li></ul></section>
    <section id="maintain"><h2>维护与重新获取</h2><p>在仓库根目录运行。以下命令只抓取资料、核对提交并生成阅读页面；不会执行上游科研代码。</p><pre><code>GIT_LFS_SKIP_SMUDGE=1 git submodule update --init --depth 1 -- external/autonomous-science
python3 scripts/fetch_autonomous_science_repos.py
python3 scripts/archive_autonomous_science.py
python3 scripts/build_autonomous_science_library.py</code></pre><p class="small">首次恢复子模块默认检出可能包含上游原始附件；随后第二条命令恢复本资料集的稀疏检出。当前子模块未递归初始化上游嵌套子模块。没有提交或推送本轮改动。</p></section>
    <script>const items=[...document.querySelectorAll('.library-entry')],q=document.getElementById('query'),f=document.getElementById('repo-filter');function filter(){{let n=0;for(const e of items){{const match=e.textContent.toLowerCase().includes(q.value.trim().toLowerCase())&&(f.value==='all'||(f.value==='none'?e.dataset.repo==='none':e.dataset.repo!=='none'));e.hidden=!match;if(match)n++;}}document.getElementById('count').textContent=`显示 ${{n}} / ${{items.length}} 项`;document.getElementById('empty').hidden=n>0;}}q.addEventListener('input',filter);f.addEventListener('change',filter);document.getElementById('reset').addEventListener('click',()=>{{q.value='';f.value='all';filter();}});filter();</script>'''
    nav = ''.join(link(h, t) for h, t in [('#collection','资料与翻译范围'),('#reading','中文译读'),('#code','源码与许可证'),('#boundaries','原件与Git边界'),('#maintain','维护方式'),('../index.html','返回进展综述')])
    (LIB / 'index.html').write_text(shell('AI自主科研 · 译读与开源资料库', body, nav))
    (LIB / 'translation-audit.json').write_text(json.dumps({'checked':'2026-11-10','method':'本会话翻译；未调用外部翻译服务或付费模型API','full_paper_translation':False,'items':audit}, ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'readings':len(entries),'pdfs':pdf_count,'pages':total_pages,'repositories':len(repos),'bilingual_readers':len(audit)},ensure_ascii=False))


if __name__ == '__main__':
    main()
