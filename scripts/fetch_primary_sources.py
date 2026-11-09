#!/usr/bin/env python3
"""Fetch the eight requested papers and the autoresearch documentation."""
from pathlib import Path
import concurrent.futures
import hashlib
import html
import json
import re
import subprocess
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'sources' / 'fulltext'
ITEMS = [
    ('autosurvey', '2406.10252v2', None),
    ('openscholar', '2411.14199v1', None),
    ('surveyforge', '2503.04629v1', 'https://aclanthology.org/2025.acl-long.609.pdf'),
    ('co-scientist', '2502.18864v2', None),
    ('ai-scientist-v2', '2504.08066v1', None),
    ('paperbench', '2504.01848v3', None),
    ('astabench', '2510.21652v2', None),
    ('epoch', '2610.06986v1', None),
]

def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (academic reading; source archival)'})
    with urllib.request.urlopen(request, timeout=90) as response:
        return response.read(), response.geturl()

def paper(item):
    name, version, official = item
    dest = OUT / name
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / 'source.json').exists() and (dest / 'original.pdf').exists():
        return json.loads((dest / 'source.json').read_text())
    abstract, _ = fetch('https://arxiv.org/abs/' + version)
    (dest / 'arxiv-metadata.html').write_bytes(abstract)
    text = abstract.decode()
    def meta(field):
        match = re.search(r'<meta name="' + field + r'" content="([^"]+)', text)
        return html.unescape(match.group(1)) if match else ''
    license_match = re.search(r'<a[^>]+href="([^"]+)"[^>]*>\s*(?:<[^>]*>\s*)*view license', text, re.I)
    license_url = license_match.group(1) if license_match else ''
    pdf_url = official or 'https://arxiv.org/pdf/' + version
    pdf, resolved = fetch(pdf_url)
    if not pdf.startswith(b'%PDF-'):
        raise ValueError('Invalid PDF: ' + name)
    (dest / 'original.pdf').write_bytes(pdf)
    if official:
        license_page, _ = fetch('https://aclanthology.org/2025.acl-long.609/')
        (dest / 'publication-metadata.html').write_bytes(license_page)
        if 'creativecommons.org/licenses/by/4.0/' not in license_page.decode():
            raise ValueError('ACL licence not found')
        license_url = 'https://creativecommons.org/licenses/by/4.0/'
    if 'creativecommons.org/licenses/by/4.0/' not in license_url:
        raise ValueError('Adaptation licence not confirmed: ' + name + ' ' + license_url)
    html_status = 'unavailable'
    try:
        article, article_url = fetch('https://arxiv.org/html/' + version)
        if b'ltx_document' in article:
            (dest / 'arxiv-fulltext.html').write_bytes(article)
            html_status = article_url
    except Exception as exc:
        html_status = type(exc).__name__
    subprocess.run(['pdftotext', '-layout', str(dest / 'original.pdf'), str(dest / 'original-layout.txt')], check=True)
    subprocess.run(['pdftotext', '-raw', str(dest / 'original.pdf'), str(dest / 'original-raw.txt')], check=True)
    info = subprocess.check_output(['pdfinfo', str(dest / 'original.pdf')], text=True)
    pages = int(re.search(r'^Pages:\s+(\d+)', info, re.M).group(1))
    record = dict(slug=name, arxiv=version, title=meta('citation_title'), authors=re.findall(r'<meta name="citation_author" content="([^"]+)', text), pdf_url=pdf_url, resolved_pdf_url=resolved, licence=license_url, source_format='ACL formal version' if official else 'arXiv pinned version', html=html_status, pages=pages, sha256=hashlib.sha256(pdf).hexdigest(), retrieved='2026-11-09')
    (dest / 'source.json').write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
    return record

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for result in pool.map(paper, ITEMS):
            records.append(result)
            print(json.dumps({k:result[k] for k in ['slug','pages','licence','html']}, ensure_ascii=False), flush=True)
    refs = subprocess.check_output(['git', 'ls-remote', 'https://github.com/karpathy/autoresearch.git', 'refs/heads/master'], text=True)
    commit = refs.split()[0]
    dest = OUT / 'autoresearch'
    dest.mkdir(exist_ok=True)
    docs = []
    for name in ['README.md', 'program.md']:
        url = 'https://raw.githubusercontent.com/karpathy/autoresearch/' + commit + '/' + name
        content, _ = fetch(url)
        (dest / name).write_bytes(content)
        docs.append(dict(file=name, url=url, sha256=hashlib.sha256(content).hexdigest()))
    if 'MIT' not in (dest / 'README.md').read_text():
        raise ValueError('README MIT declaration not found')
    item = dict(slug='autoresearch', title='autoresearch README and program.md', commit=commit, licence='MIT (README declaration; no separate LICENSE file assumed)', documents=docs, retrieved='2026-11-09')
    (dest / 'source.json').write_text(json.dumps(item, indent=2) + '\n')
    records.append(item)
    (OUT / 'manifest.json').write_text(json.dumps(records, ensure_ascii=False, indent=2) + '\n')
    print('Saved complete source manifest.', flush=True)

if __name__ == '__main__':
    main()
