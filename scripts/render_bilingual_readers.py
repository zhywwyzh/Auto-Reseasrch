#!/usr/bin/env python3
"""Render the licensed source/translation pairs as Markdown and offline HTML."""
from pathlib import Path
import argparse
import html
import json
import re

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT/'translations/fulltext'
SLUGS=['autosurvey','openscholar','surveyforge','co-scientist','ai-scientist-v2','paperbench','astabench','epoch','autoresearch']
LABELS=['AutoSurvey','OpenScholar','SurveyForge','Co-Scientist','AI Scientist-v2','PaperBench','AstaBench','EPOCH','autoresearch']
CSS='''
:root{font-family:system-ui,"Noto Sans CJK SC","Microsoft YaHei",sans-serif;color:#20252b;background:#f4f3ef;font-size:15px;line-height:1.8}
*{box-sizing:border-box}body{margin:0}main{max-width:1360px;margin:auto;padding:36px 28px}header{border-bottom:2px solid #333;padding-bottom:24px;margin-bottom:28px}h1{font-size:27px;line-height:1.4}h2{font-size:22px;margin:36px 0 16px}h3{font-size:17px}a{color:#155b82;text-underline-offset:3px}nav{display:flex;gap:10px 18px;flex-wrap:wrap}p{margin:10px 0}.note{background:#e9e7df;padding:16px 20px;border-left:3px solid #777}.meta,.label{font-size:12px;color:#62676c}.pair{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:28px;border-top:1px solid #d7d7d2;padding:20px 0;break-inside:avoid}.cell{min-width:0;overflow-wrap:anywhere}.cell p{white-space:pre-wrap}.technical{white-space:pre-wrap;font:12px/1.8 ui-monospace,monospace;overflow:auto}.page{font-size:18px;border-bottom:2px solid #777;margin-top:40px;padding:12px 0}.review{background:#fff2d9;padding:8px 12px;font-size:13px}.summary{max-width:1000px;margin-bottom:35px}.toc{columns:2;column-gap:40px;font-size:13px}.toc a{display:block;margin:3px 0}details{margin:8px 0}.toolbar{position:sticky;top:0;background:#f4f3ef;padding:10px 0;z-index:2;border-bottom:1px solid #ddd}button{padding:6px 12px;margin:0 8px 0 0;background:#fff;border:1px solid #999;border-radius:4px;color:#20252b;cursor:pointer}body.zh-only .english{display:none}body.zh-only .pair{grid-template-columns:1fr}.index-entry{padding:22px 0;border-top:1px solid #ccc}.index-entry h2{margin:0 0 8px}
.pair,.page{scroll-margin-top:75px}
@media(max-width:800px){main{padding:20px 16px}.pair{grid-template-columns:1fr;gap:10px}.toc{columns:1}h1{font-size:23px}}
@media print{body{background:white}main{padding:0}.toolbar,nav{display:none}.pair{gap:18px}.note{background:white}a{color:inherit}details{display:block}}
'''

def e(s):return html.escape(str(s))

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--allow-partial',action='store_true');args=parser.parse_args()
    summaries={x['slug']:x for x in json.loads((ROOT/'data/fulltext-paper-summaries.json').read_text())}
    overrides=json.loads((ROOT/'data/fulltext-translation-overrides.json').read_text())['translations']
    index=[];quality=[]
    for slug,label in zip(SLUGS,LABELS):
        folder=BASE/slug;data=json.loads((folder/'bilingual.json').read_text());src=data['source'];summary=summaries[slug]
        missing=[u['id'] for u in data['units'] if u['translate'] and not u.get('zh') and u['id'] not in overrides]
        if missing and not args.allow_partial:raise ValueError(slug+' has untranslated paragraphs: '+str(len(missing)))
        title=src['title'];pdf=f'../../../sources/fulltext/{slug}/original.pdf'
        source_url='https://arxiv.org/abs/'+src['arxiv'] if 'arxiv' in src else 'https://github.com/karpathy/autoresearch/tree/'+src['commit']
        version=src.get('arxiv',src.get('commit',''))
        if src.get('source_format')=='ACL formal version':
            source_url='https://aclanthology.org/2025.acl-long.609/'
            version='ACL 2025 / 2025.acl-long.609'
        source_link=f'<a href="{e(pdf)}">原始 PDF（含原图表）</a>' if 'pages' in src else '<a href="../../../sources/fulltext/autoresearch/README.md">原始 README</a> · <a href="../../../sources/fulltext/autoresearch/program.md">原始 program.md</a>'
        source_md=f'[原始 PDF]({pdf})' if 'pages' in src else '[原始 README](../../../sources/fulltext/autoresearch/README.md) · [原始 program.md](../../../sources/fulltext/autoresearch/program.md)'
        count=sum(u['translate'] for u in data['units']);checked=sum(u['id'] in overrides for u in data['units'])
        notice='全文可提取文本的中英对照机器初译，含附录。摘要由当前助手复核，全文尚未逐段精校。作者/机构、参考文献、代码和公式按需保留原文；图内文字和复杂表格请结合原 PDF 核对。译文为非官方改编，作者未为其背书。'
        if missing:notice+=' 当前预览尚有未完成段落，不作为完成版交付。'
        prefix=f'<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(label)} · 全文中英对照</title><style>{CSS}</style></head><body><main><header><nav><a href="../index.html">全部 9 项</a><a href="bilingual.md">Markdown 版</a>{source_link}<a href="{e(source_url)}">原始来源</a></nav><h1>{e(label)} · 全文中英对照</h1><p>{e(title)}</p><p class="meta">版本：{e(version)} · 获取：{e(src["retrieved"])} · 原文许可：<a href="{e(src["licence"] if src["licence"].startswith("http") else source_url)}">{e(src["licence"])}</a></p><p class="meta">作者：{e("; ".join(html.unescape(x) for x in src.get("authors",[]))) if src.get("authors") else "Andrej Karpathy（仓库维护者）"}</p><div class="note">{e(notice)}</div><p class="meta">正文/附录文字段落：{count} · 助手复核摘要单元：{checked} · 提取方式：{e(data["extraction"])}</p></header>'
        summary_html='<section class="summary"><h2>论文总结 / Reading summary</h2><p lang="en">'+e(summary['en'])+'</p><p>'+e(summary['zh'])+'</p><ol>'+''.join('<li>'+e(p)+'</li>' for p in summary['points'])+'</ol></section>'
        toc=[];body=[];md=[f'# {label}：全文中英对照\n\n{title}\n\n版本：{version}。获取日期：{src["retrieved"]}。\n\n来源：[原始页面]({source_url}) · {source_md}\n\n原文许可：{src["licence"]}\n\n> {notice}\n\n## 论文总结 / Reading summary\n\n{summary["en"]}\n\n{summary["zh"]}\n\n']
        md += [f'{i}. {p}\n' for i,p in enumerate(summary['points'],1)]
        md.append('\n## 逐段对照正文与附录\n\n')
        flags=[];frontmatter_open=False
        for u in data['units']:
            uid=u['id'];en=u['en'];zh=overrides.get(uid,u.get('zh',''))
            status='assistant_checked_abstract' if uid in overrides else u.get('status','pending')
            if u['translate'] and uid not in overrides and u['kind']!='table':
                if re.search(r'\breplicat|\breproduc',en,re.I):zh=zh.replace('复制','复现')
                if re.search(r'\btokens?\b',en,re.I):zh=zh.replace('词条','token')
                if slug=='epoch':
                    zh=zh.replace('承认检查','准入检查').replace('估值层','赋值层')
                    if 'certificat' in en.lower():zh=zh.replace('有限证明','有限证书')
                u['zh']=zh
            if u['kind']=='table' and u['translate'] and slug in ['autosurvey','openscholar','surveyforge']:
                boundary='\n\n表内文字对照（数值与原始行列保持不变）：\n'
                if boundary in zh:
                    original,gloss=zh.split(boundary,1)
                    gloss=gloss.replace('调查问卷','综述').replace('调查研究','综述').replace('调查','综述')
                    zh=original+boundary+gloss;u['zh']=zh
            if uid in overrides:
                u['zh']=zh;u['status']=status;u['flags']=[]
            # LaTeXML's style diagnostics are not part of the published paper.
            if slug=='paperbench' and uid in ['paperbench-0001','paperbench-0002','paperbench-0003','paperbench-0004']:continue
            is_frontmatter=u['kind']=='frontmatter' and status=='retained_original'
            if is_frontmatter and not frontmatter_open:
                body.append('<details><summary>作者、机构与出版信息（原文保留）</summary>');frontmatter_open=True
            elif not is_frontmatter and frontmatter_open:
                body.append('</details>');frontmatter_open=False
            if u['kind']=='page':
                page=u['page'];text=f'原文第 {page} 页 / PDF page {page}'
                body.append(f'<div class="page" id="{e(uid)}">{text} · <a href="{e(pdf)}#page={page}">查看原页</a></div>')
                md.append(f'\n### 原文第 {page} 页\n\n[查看原页]({pdf}#page={page})\n\n');continue
            if u['kind']=='heading':toc.append((uid,en,zh))
            label_zh='中文译文' if status not in ['retained_original','pending'] else '原文保留（专名、技术内容或文献信息）' if status=='retained_original' else '未完成'
            marker='助手复核摘要' if uid in overrides else '助手校对题名' if status=='manual_title' else '机器初译' if u['translate'] else '保留原文'
            warning=u.get('flags',[]) if uid not in overrides else []
            warn_html=''
            if warning:
                flags.append(dict(id=uid,flags=warning))
                names={'formula_or_link_placeholder_missing':'译文可能遗漏公式或链接','generation_limit':'译文可能被长度上限截断','little_chinese':'译文主要保留英文，请核对是否为专名或技术内容','empty_translation':'未获得有效译文'}
                warn_html='<p class="review">待核对：'+e('；'.join(names.get(x,x) for x in warning))+'</p>'
                if u.get('missing_protected_values'):
                    warn_html+='<p class="review">请核对以下原式或链接：'+e('；'.join(u['missing_protected_values']))+'</p>'
            enclass='technical' if u['kind'] in ['table','formula','code'] else ''
            zhclass='technical' if u['kind'] in ['table','formula','code'] else ''
            paired=f'<section class="pair" id="{e(uid)}"><div class="cell english"><div class="label">{e(uid)} · English original</div><p lang="en" class="{enclass}">{e(en)}</p></div><div class="cell chinese"><div class="label">{e(label_zh)} · {marker}</div><p class="{zhclass}">{e(zh)}</p>{warn_html}</div></section>'
            if u['kind'] in ['reference','code'] and status=='retained_original':paired='<details><summary>'+e(uid+' · '+en[:100])+'</summary>'+paired+'</details>'
            body.append(paired)
            md.append(f'### {uid}\n\n**English original**\n\n'+en+'\n\n**'+label_zh+' · '+marker+'**\n\n'+(zh or '（未完成）')+'\n\n')
            if warning:md.append('待核对标记：'+', '.join(warning)+'\n\n')
        if frontmatter_open:body.append('</details>')
        (folder/'bilingual.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
        toc_html='<details><summary>章节目录（'+str(len(toc))+' 项）</summary><div class="toc">'+''.join(f'<a href="#{e(uid)}">{e(en)} / {e(zh)}</a>' for uid,en,zh in toc)+'</div></details>' if toc else ''
        toolbar='<div class="toolbar"><button onclick="document.body.classList.toggle(\'zh-only\')">切换：双语 / 仅中文</button><button onclick="window.print()">打印 / 保存 PDF</button><a href="#top">返回顶部</a></div>'
        ending='<footer><p class="meta">译文由本地 tencent/HY-MT2-1.8B 生成，模型与提示词版本保存在 bilingual.json。以上总结由当前助手编写。原文及译文许可说明见来源记录；图表原貌以 PDF 为准。</p></footer></main></body></html>'
        (folder/'bilingual.html').write_text(prefix.replace('<header>','<header id="top">',1)+summary_html+toc_html+toolbar+''.join(body)+ending)
        (folder/'bilingual.md').write_text(''.join(md))
        item=dict(slug=slug,label=label,version=version,pages=src.get('pages'),units=len(data['units']),translated_units=count,abstract_reviewed=checked,missing=len(missing),flagged=len(flags),sha256=src.get('sha256'),extraction=data['extraction'])
        index.append(item);quality.append(dict(**item,flags=flags))
        print(json.dumps(item,ensure_ascii=False),flush=True)
    index_intro='8 篇论文原文共 487 页，另含 autoresearch 的 README 与 program.md。按段对照机器初译，保留附录可提取文本；摘要已由当前助手复核，其余内容仍为待精校初稿。'
    cards=''.join(f'<section class="index-entry"><h2><a href="{e(x["slug"])}/bilingual.html">{e(x["label"])}</a></h2><p>{e(x["version"])}'+(f' · 原文 {x["pages"]} 页' if x['pages'] else ' · 工程文档')+f' · 译文单元 {x["translated_units"]} · 待核对标记 {x["flagged"]}</p><nav><a href="{e(x["slug"])}/bilingual.html">打开双语阅读版</a><a href="{e(x["slug"])}/bilingual.md">打开 Markdown 版</a></nav></section>' for x in index)
    (BASE/'index.html').write_text('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Auto Research · 全文中英对照</title><style>'+CSS+'</style></head><body><main><h1>Auto Research · 全文中英对照</h1><div class="note">'+index_intro+'</div><p>抓取日期：2026-11-09。论文原文均已核对 CC BY 4.0；autoresearch 依据仓库 README 中的 MIT 声明处理。</p>'+cards+'</main></body></html>')
    readme='# Auto Research：全文中英对照\n\n'+index_intro+'\n\n获取日期：2026-11-09。\n\n[打开双语阅读总入口](index.html)\n\n'
    for x in index:readme+=f'- **{x["label"]}**（{x["version"]}）：[逐段对照 Markdown]({x["slug"]}/bilingual.md) · [双语 HTML]({x["slug"]}/bilingual.html)\n'
    readme+='\n## 版本、许可与质量\n\n- [原文清单及 SHA-256](../../sources/fulltext/manifest.json)；各目录附 source.json 和原始 PDF。\n- OpenScholar 使用 arXiv v1 的 CC BY 版本；SurveyForge 使用 ACL 正式版。其余 arXiv 版本已固定，autoresearch 已固定 commit。\n- 原文为 CC BY 4.0 的论文允许注明来源后改编；此处译文标注为非官方 AI 初译。代码/参考文献/公式及作者机构按需保留原文。图中嵌入文字不保证已单独翻译。\n- HTML 提取与 PDF 段落重建会受到表格、换行、边注和字体编码影响。遇到技术推导、数值结论、图表或不通顺译文，请打开原 PDF 对照。\n- [质量记录](quality-report.json) 列出缺译与自动标记。无自动标记不意味着语义已经逐段验证。\n- scripts/fetch_primary_sources.py、prepare_bilingual_units.py、translate_fulltext.py、render_bilingual_readers.py 保存了可继续执行的流程。模型权重和虚拟环境没有纳入 Git。\n'
    (BASE/'README.md').write_text(readme)
    (BASE/'quality-report.json').write_text(json.dumps(dict(created='2026-11-09',status='complete machine draft' if not sum(x['missing'] for x in index) else 'partial preview',papers=quality),ensure_ascii=False,indent=2)+'\n')

if __name__=='__main__':
    main()
    # Keep the default reading outputs free of per-unit metadata labels.
    import sys
    if '--allow-partial' not in sys.argv:
        import render_readable_fulltext
        render_readable_fulltext.main([])
