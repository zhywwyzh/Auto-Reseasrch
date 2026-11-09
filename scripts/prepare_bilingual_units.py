#!/usr/bin/env python3
"""Prepare source-aligned translation units without silently summarizing prose."""
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag
import hashlib
import json
import re
import pdfplumber

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'sources' / 'fulltext'
OUT = ROOT / 'translations' / 'fulltext'

def clean(text):
    return re.sub(r'[ \t]+', ' ', text.replace('\u00ad','').replace('\ufb01','fi').replace('\ufb02','fl')).strip()

def is_code(s):
    return bool(re.search(r'(?m)^\s*(?:def |class |import |from \w+ import|```|uv run|pip install|git clone|curl |#include)',s))

def html_units(path):
    soup = BeautifulSoup(path.read_text(), 'lxml')
    article = soup.find('article')
    for math in article.find_all('math'):
        math.replace_with(' $' + (math.get('alttext') or math.get_text(' ',strip=True)) + '$ ')
    for tag in article.find_all(['script','style','nav']):tag.decompose()
    units=[]
    def add(kind,text,anchor=''):
        s=clean(text)
        if s:units.append(dict(kind=kind,en=s,anchor=anchor))
    def walk(node):
        if isinstance(node,NavigableString):
            if str(node).strip():add('prose',str(node))
            return
        if not isinstance(node,Tag):return
        classes=set(node.get('class',[]))
        name=node.name
        anchor=node.get('id','')
        if name in ['h1','h2','h3','h4','h5','h6']:
            add('heading',node.get_text(' ',strip=True),anchor);return
        if 'ltx_bibitem' in classes:
            add('reference',node.get_text(' ',strip=True),anchor);return
        if name=='table':
            rows=[' | '.join(clean(c.get_text(' ',strip=True)) for c in r.find_all(['td','th'],recursive=False)) for r in node.find_all('tr')]
            add('table','\n'.join(rows),anchor);return
        if name=='pre' or 'ltx_listing' in classes:
            text=node.get_text('\n',strip=False)
            add('code' if is_code(text) else 'prose',text,anchor);return
        if 'ltx_equation' in classes or 'ltx_equationgroup' in classes:
            add('formula',node.get_text(' ',strip=True),anchor);return
        if name=='p' or name=='figcaption':
            add('caption' if name=='figcaption' else 'prose',node.get_text(' ',strip=True),anchor);return
        if name=='img':
            alt=node.get('alt','').strip()
            if alt:add('figure-label',alt,anchor)
            return
        # Unstructured strings are grouped at their original container boundary.
        pending=[]
        for child in node.children:
            if isinstance(child,NavigableString):
                if str(child).strip():pending.append(str(child))
            else:
                if pending:add('prose',' '.join(pending),anchor);pending=[]
                walk(child)
        if pending:add('prose',' '.join(pending),anchor)
    walk(article)
    return units,'arXiv HTML (headings, paragraphs, captions, tables and appendices)'

def split_layout(text):
    text=text.replace('\u00ad','')
    # Preserve the source paragraph boundaries, including first-line indentation.
    text=re.sub(r'(?<=[.!?:])\n {6,}(?=[A-Za-z])','\n\n',text)
    blocks=[]
    for part in re.split(r'\n\s*\n',text):
        lines=part.splitlines()
        if not lines:continue
        table=sum(bool(re.search(r'\S {3,}\S',line)) for line in lines)>=3
        s='\n'.join(line.strip() for line in lines) if table else ' '.join(line.strip() for line in lines)
        s=clean(re.sub(r'([A-Za-z])-\s*\n\s*([a-z])',r'\1\2',s))
        if s and not re.fullmatch(r'\d+',s):blocks.append(('table' if table else 'prose',s))
    return blocks

def pdf_units(folder,slug):
    units=[];in_refs=False
    if slug=='surveyforge':
        pages=[]
        with pdfplumber.open(folder/'original.pdf') as doc:
            for i,page in enumerate(doc.pages):
                # ACL uses two columns. Its first-page title/author band spans both.
                start=196 if i==0 else 28
                top=page.crop((0,0,page.width,start)).extract_text(layout=True,x_tolerance=1.2) if i==0 else ''
                left=page.crop((0,start,page.width/2,page.height-20)).extract_text(layout=True,x_tolerance=1.2)
                right=page.crop((page.width/2,start,page.width,page.height-20)).extract_text(layout=True,x_tolerance=1.2)
                pages.append('\n\n'.join([top or '',left or '',right or '']))
    else:
        pages=(folder/'original-layout.txt').read_text().split('\f')[:-1]
        if slug=='ai-scientist-v2':
            # Included generated manuscripts have large diagonal watermarks and
            # marginal reviewer comments. Keep comments separate from body text.
            with pdfplumber.open(folder/'original.pdf') as doc:
                for i,page in enumerate(doc.pages):
                    if any(c.get('size',0)>30 for c in page.chars):
                        filtered=page.filter(lambda c:c.get('object_type')!='char' or c.get('size',0)<=30)
                        body=filtered.crop((74,0,499,page.height)).extract_text(layout=True,x_tolerance=1.2) or ''
                        left=filtered.crop((0,0,74,page.height)).extract_text(layout=True,x_tolerance=1.2) or ''
                        right=filtered.crop((499,0,page.width,page.height)).extract_text(layout=True,x_tolerance=1.2) or ''
                        pages[i]='\n\n'.join([body,'Margin comments (left):\n'+left,'Margin comments (right):\n'+right])
    for i,text in enumerate(pages,1):
        units.append(dict(kind='page',en=f'PDF page {i}',page=i))
        for kind,s in split_layout(text):
            heading=len(s)<150 and (s.lower() in ['summary','abstract','introduction','discussion','conclusion','conclusions','references','bibliography','methods','supplementary information'] or bool(re.match(r'^(?:\d+(?:\.\d+)*\.?|[A-Z]\.?)\s+[A-Z][A-Za-z ,:()/-]+$',s)))
            if s.lower() in ['references','bibliography']:in_refs=True
            elif heading or re.match(r'^(?:Appendix|Supplementary|Extended Data)',s,re.I):in_refs=False
            if in_refs and not heading:kind='reference'
            elif heading:kind='heading'
            elif is_code(s):kind='code'
            units.append(dict(kind=kind,en=s,page=i))
    return units,'PDF text; paragraph reconstruction with page anchors (ACL columns separated)'

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=json.loads((BASE/'manifest.json').read_text())
    for paper in manifest:
        slug=paper['slug'];folder=BASE/slug
        if slug=='autoresearch':
            units=[]
            for filename in ['README.md','program.md']:
                units.append(dict(kind='heading',en=filename,anchor=filename))
                code=False
                for part in re.split(r'\n\s*\n',(folder/filename).read_text()):
                    if not part.strip():continue
                    kind='code' if is_code(part) or code else 'heading' if re.match(r'^#{1,6} ',part) else 'prose'
                    if part.count('```')%2:code=not code
                    units.append(dict(kind=kind,en=part.strip(),anchor=filename))
            extraction='Pinned README.md and program.md'
        elif slug not in ['surveyforge','ai-scientist-v2'] and (folder/'arxiv-fulltext.html').exists():
            units,extraction=html_units(folder/'arxiv-fulltext.html')
        else:units,extraction=pdf_units(folder,slug)
        if slug=='ai-scientist-v2':
            for n,u in enumerate(units[:-1]):
                if u['en'].startswith('AI is increasingly') and units[n+1]['en'].startswith('generated peer-review'):
                    first=re.sub(r'arXiv:\S+\s+\[[^]]+\]\s+\d+\s+\w+\s+\d{4}', '', u['en']).rstrip()
                    u['en']=first+units[n+1]['en'] if first.endswith('-') else first+' '+units[n+1]['en']
                    u['en']=u['en'].replace('Th e A I Sc i e n t i s t - v 2','The AI Scientist-v2')
                    del units[n+1]
                    break
        for n,u in enumerate(units,1):
            u['id']=f'{slug}-{n:04d}'
            u['sha256']=hashlib.sha256(u['en'].encode()).hexdigest()
            u['translate']=u['kind'] not in ['code','formula','reference','page'] and bool(re.search(r'[A-Za-z]{3}',u['en']))
        result=dict(source=paper,extraction=extraction,units=units,translation_status='prepared, not translated')
        dest=OUT/slug;dest.mkdir(exist_ok=True)
        (dest/'units.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
        print(slug,'units',len(units),'translate',sum(u['translate'] for u in units),'words',sum(len(u['en'].split()) for u in units),flush=True)

if __name__=='__main__':main()
