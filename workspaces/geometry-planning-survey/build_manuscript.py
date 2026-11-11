#!/usr/bin/env python3
"""Generate an anonymous review draft from survey.json; never fabricates authors.
Run with Python, then XeLaTeX twice from papers/geometry-planning-survey.
"""
import json,re,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parent
REPO=ROOT.parents[1]
OUT=REPO/'papers/geometry-planning-survey'
D=json.loads((ROOT/'survey.json').read_text())
REFS={r['id']:r for r in D['references']}
OUT.mkdir(parents=True,exist_ok=True)
for name in ['aas.cls','picins.sty','Euclid.ttf','Euclid-Bold.ttf']:
    target=OUT/name
    original=REPO/'templates/acta-automatica-sinica'/name
    if target.exists():
        assert target.read_bytes()==original.read_bytes(), 'Do not overwrite modified template dependency: '+name
    else:shutil.copyfile(original,target)
(OUT/'figures').mkdir(exist_ok=True)
for s in D['draft']:
    if 'figure'in s:shutil.copyfile(ROOT/'figures'/s['figure'].replace('.svg','.pdf'),OUT/'figures'/s['figure'].replace('.svg','.pdf'))


def escape(t):
    for a,b in [('\\',r'\textbackslash{}'),('&',r'\&'),('%',r'\%'),('$',r'\$'),('#',r'\#'),('_',r'\_'),('{',r'\{'),('}',r'\}')]:t=t.replace(a,b)
    mapping={'Γ':r'$\Gamma$','ε':r'$\epsilon$','φ':r'$\phi$','×':r'$\times$','−':r'$-$','²':r'$^2$','≤':r'$\leq$','≥':r'$\geq$','—':'---','–':'--','‑':'-','−':'-'}
    for a,b in mapping.items():t=t.replace(a,b)
    for token in ['F_R','F_E','S_B']:
        t=t.replace(token.replace('_',r'\_'),'$'+token+'$')
    return t

def prose(t):
    return ''.join(r'\cite{'+part[1:-1]+'}'if re.fullmatch(r'\[[RSMJ]\d{2}\]',part)else escape(part)for part in re.split(r'(\[[RSMJ]\d{2}\])',t))

abstract=D['draft'][0]['paragraphs'][0]
lines=[r'\documentclass{aas}',r'\setsansfont[Extension = .ttf, BoldFont = *-Bold]{Euclid}',r'\usepackage{xurl}',r'\Urlmuskip=0mu plus 2mu',r'\setlength{\emergencystretch}{2em}',r'\hypersetup{pdftitle={'+escape(D['title'])+r'},pdfauthor={},pdfsubject={AI辅助论述初稿，未投稿}}',r'\begin{document}',r'\cntitle{'+escape(D['title'])+'}',r'\cnauthor{}',r'\cnabstract{'+escape(abstract)+'}',r'\cnkeyword{'+escape('; '.join(D['keywords_cn']))+'}',r'\entitle{'+escape(D['english_title'])+'}',r'\enauthor{}',r'\enabstract{'+escape(D['abstract_en'])+'}',r'\enkeyword{'+escape('; '.join(D['keywords_en']))+'}',r'\cnaddress{}',r'\enaddress{}',r'\doi{}',r'\cstr{}',r'\makeatletter',r'\let\caddress\@empty',r'\let\aas@enaddress\@empty',r'\let\aas@doi\@empty',r'\let\aas@cstr\@empty',r'\makeatother',r'\maketitle',r'\pagestyle{plain}\thispagestyle{plain}',r'\noindent\textbf{审阅版 v0.4（2026-11-11）}\quad '+escape('AI辅助形成的论述初稿，尚未投稿。已核验题录、相关技术段落与解析图；最近综述全文对照及独立编码尚未完成。')+r'\par\medskip']
for s in D['draft'][1:]:
    if s['id']!='intro':lines.append(r'\section{'+escape(re.sub(r'^\d+\s*','',s['title']))+'}')
    for i,p in enumerate(s['paragraphs']):
        lines += [prose(p),'']
        for k,eq in enumerate(s.get('equations',[])):
            where=s.get('equation_after',[len(s['paragraphs'])-1]*len(s.get('equations',[])))[k]
            if where==i:lines += [r'\begin{equation}',eq['tex'],r'\end{equation}']
    if 'figure'in s:
        fname=s['figure'].replace('.svg','.pdf')
        cap=re.sub(r'^图\d+\s*','',s['caption'])
        lines += [r'\begin{figure*}[t]',r'\centering',r'\includegraphics[width=.96\textwidth]{figures/'+fname+'}',r'\bicaption{'+escape(cap)+'}{'+escape(re.sub(r'^Fig\. \d+\s*','',s['caption_en']))+'}',r'\end{figure*}']
    if 'rows'in s:
        n=len(s['headers']);width=(.97-.018*n)/n
        cols=''.join(r'>{\raggedright\arraybackslash}p{'+f'{width:.3f}'+r'\textwidth}'for _ in range(n))
        lines += [r'\begin{table*}[t]',r'\centering',r'\bicaption{'+escape(re.sub(r'^表\d+\s*','',s['table_caption']))+'}{'+escape(re.sub(r'^Table \d+\s*','',s['table_caption_en']))+'}',r'\small\setlength{\tabcolsep}{3pt}',r'\begin{tabular}{'+cols+'}',r'\toprule',' & '.join(escape(x)for x in s['headers'])+r'\\',r'\midrule']
        for row in s['rows']:lines.append(' & '.join(prose(x)for x in row)+r'\\')
        lines += [r'\bottomrule',r'\end{tabular}',r'\end{table*}']
lines += [r'\section*{写作与资料说明（审阅版）}',escape('本稿使用Codex辅助检索、核心论述及中英文摘要起草、比较表编写、解析图绘制与排版，使用日期为2026年11月11日。精确底层模型版本尚未独立核验。助手进行了题录、相关技术段落、公式和图表的自查；该过程不等同于独立人工复核。期刊现行AI条款、作者承诺及其他投稿材料已另行整理，本文不据人工审核预先宣称符合全部投稿条件。作者、单位和基金信息未填写。'),r'\begin{thebibliography}{99}']
for rid in D['manuscript_references']:
    r=REFS[rid];b=r['bibliography'];aa=b['authors'];authors='; '.join(aa[:6])+('; et al.'if len(aa)>6 else'')
    tail=b['year']+(', '+b['volume']if b.get('volume')else'')+('('+b['issue']+')'if b.get('issue')else'')+(': '+b['pages']if b.get('pages')else'')
    text=authors+'. '+r['title']+'. '+b['venue']+', '+tail+'.'
    lines.append(r'\bibitem{'+rid+'} '+escape(text)+(r' DOI: \url{'+b['doi']+'}.'if b.get('doi')else r' \url{'+b['url']+'}.'))
lines += [r'\end{thebibliography}',r'\end{document}']
(OUT/'main.tex').write_text('\n'.join(lines)+'\n')
print('Generated',OUT/'main.tex')
