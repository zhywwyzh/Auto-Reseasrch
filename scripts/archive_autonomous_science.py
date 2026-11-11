#!/usr/bin/env python3
"""Archive only public research sources; never install or run upstream code.

Raw papers and extracted text stay under the ignored thesis-reference/ tree.
Records contain exact versions, HTTP outcomes, SHA-256 and local paths.
Existing originals are reused, never overwritten. No model/API credentials.
"""
import argparse
import concurrent.futures
import hashlib
import json
from pathlib import Path
import re
import subprocess
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
LIB = ROOT / 'docs/research/autonomous-science-2026-11-10/library'
RAW = ROOT / 'thesis-reference/related-papers/autonomous-science-2026-11-10'
NOTES = ROOT / 'thesis-reference/notes/autonomous-science-2026-11-10'


def download(url, target, pdf=False):
    if target.exists():
        raw = target.read_bytes()
        if pdf and not raw.startswith(b'%PDF-'):
            raise ValueError(f'existing file is not PDF: {target}')
        return dict(url=url, path=str(target.relative_to(ROOT)), bytes=len(raw),
                    sha256=hashlib.sha256(raw).hexdigest(), reused=True)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (AutoResearch-UAV public literature archival)'})
    with urllib.request.urlopen(req, timeout=55) as response:
        raw, resolved = response.read(), response.geturl()
    if pdf and not raw.startswith(b'%PDF-'):
        raise ValueError('HTTP response is not a PDF')
    if not pdf and any(marker in raw[:10000].lower() for marker in
                       [b'client challenge', b'checking your browser', b'verify you are human']):
        raise ValueError('challenge page; content not archived as paper')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(raw)
    return dict(url=url, resolved_url=resolved, path=str(target.relative_to(ROOT)),
                bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest(), reused=False)


def archive(paper):
    slug = paper['id']
    dest = RAW / slug
    dest.mkdir(parents=True, exist_ok=True)
    record = {k: v for k, v in paper.items() if k not in ('pdf_urls',)}
    record.update(retrieved='2026-11-10', files=[], errors=[], status='metadata-only')
    abstract = ''
    if paper.get('arxiv'):
        existing = ROOT / paper.get('existing', '')
        metadata = existing / 'arxiv-metadata.html' if paper.get('existing') else dest / 'metadata.html'
        url = 'https://arxiv.org/abs/' + paper['arxiv']
        try:
            f = download(url, metadata)
            record['files'].append(f)
            soup = BeautifulSoup(metadata.read_bytes(), 'html.parser')
            def meta(name):
                m = soup.find('meta', attrs={'name': name})
                return m.get('content', '') if m else ''
            record['title'] = meta('citation_title')
            record['authors'] = [m.get('content') for m in soup.find_all('meta', attrs={'name': 'citation_author'})]
            a = soup.select_one('blockquote.abstract')
            abstract = re.sub(r'^Abstract:\s*', '', a.get_text(' ', strip=True)) if a else ''
            licence = next((a.get('href') for a in soup.select('a[href]') if 'view license' in a.get_text(' ', strip=True).lower()), None)
            record['paper_license_url'] = licence
        except Exception as e:
            record['errors'].append({'operation': 'metadata', 'error': str(e)})
        pdf_path = existing / 'original.pdf' if paper.get('existing') else dest / 'original.pdf'
        try:
            record['files'].append(download('https://arxiv.org/pdf/' + paper['arxiv'], pdf_path, pdf=True))
        except Exception as e:
            record['errors'].append({'operation': 'pdf', 'error': str(e)})
        if not paper.get('existing'):
            try:
                record['files'].append(download('https://arxiv.org/html/' + paper['arxiv'], dest / 'fulltext.html'))
            except Exception as e:
                record['errors'].append({'operation': 'html', 'error': str(e)})
    else:
        pdf_path = dest / 'original.pdf'
        for i, url in enumerate(paper.get('pdf_urls', [])):
            try:
                record['files'].append(download(url, pdf_path, pdf=True))
                break
            except Exception as e:
                record['errors'].append({'operation': 'pdf', 'url': url, 'error': str(e)})
        if paper.get('web'):
            try:
                record['files'].append(download(paper['web'], dest / 'source-page.html'))
                s = BeautifulSoup((dest / 'source-page.html').read_bytes(), 'html.parser')
                title = s.find('meta', attrs={'name': 'citation_title'})
                record['title'] = title.get('content') if title else (s.title.get_text(' ', strip=True) if s.title else paper['title_zh'])
                a = s.select_one('#Abs1-content, .abstract, #abstract, .abstract-content')
                abstract = a.get_text(' ', strip=True) if a else ''
            except Exception as e:
                record['errors'].append({'operation': 'web', 'error': str(e)})
        if paper.get('metadata_xml_url'):
            try:
                f = download(paper['metadata_xml_url'], dest / 'pubmed.xml')
                record['files'].append(f)
                xml = ET.fromstring((dest / 'pubmed.xml').read_bytes())
                abstract = ' '.join(''.join(x.itertext()) for x in xml.findall('.//AbstractText'))
                title = xml.find('.//ArticleTitle')
                if title is not None:
                    record['title'] = ''.join(title.itertext())
            except Exception as e:
                record['errors'].append({'operation': 'public-abstract-xml', 'error': str(e)})
    if pdf_path.exists():
        txt = NOTES / slug / 'original-layout.txt'
        txt.parent.mkdir(parents=True, exist_ok=True)
        if not txt.exists():
            subprocess.run(['pdftotext', '-layout', str(pdf_path), str(txt)], check=True)
        info = subprocess.check_output(['pdfinfo', str(pdf_path)], text=True)
        record['pages'] = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
        record['status'] = 'full-paper-downloaded'
        record['extracted_text'] = str(txt.relative_to(ROOT))
        if not record.get('paper_license_url') and 'creativecommons.org/licenses/by/4.0' in txt.read_text():
            record['paper_license_url'] = 'https://creativecommons.org/licenses/by/4.0/'
            record['license_evidence'] = 'PDF extracted license statement; inspect original for full terms'
    elif record['files']:
        record['status'] = 'public-page-only'
    if abstract:
        note = NOTES / slug / 'abstract-en.txt'
        note.parent.mkdir(parents=True, exist_ok=True)
        if not note.exists():
            note.write_text(abstract + '\n')
        record['abstract_local'] = str(note.relative_to(ROOT))
    (dest / 'source.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--only', nargs='*')
    args = parser.parse_args()
    registry = json.loads((LIB / 'registry.json').read_text())
    papers = [x for x in registry['papers'] if not args.only or x['id'] in args.only]
    old = json.loads((LIB / 'sources.json').read_text()) if (LIB / 'sources.json').exists() else []
    indexed = {x['id']: x for x in old}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for record in pool.map(archive, papers):
            indexed[record['id']] = record
            print(json.dumps({k: record.get(k) for k in ['id', 'status', 'pages', 'paper_license_url', 'errors']}, ensure_ascii=False), flush=True)
    output = [indexed[x['id']] for x in registry['papers'] if x['id'] in indexed]
    (LIB / 'sources.json').write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')


if __name__ == '__main__':
    main()
