#!/usr/bin/env python3
"""Archive original figure assets and math markup, without generating new content."""
from pathlib import Path
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin, urlsplit
from urllib.request import Request, urlopen
import hashlib
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'translations/fulltext'


def normalized(value):
    return re.sub(r'\s+', '', value).casefold()


def caption_key(value):
    match = re.match(r'\s*(Figure|Fig\.?|Table|Algorithm)\s*([A-Z]?\d+(?:\.\d+)*[a-z]?)\b', value, re.I)
    if not match:
        return None
    return ('figure' if match[1].lower().startswith('fig') else match[1].lower(), match[2].lower())


def source_text(node):
    node = BeautifulSoup(str(node), 'html.parser')
    for math in node.find_all('math'):
        math.replace_with(' $' + (math.get('alttext') or math.get_text(' ', strip=True)) + '$ ')
    return re.sub(r'[ \t]+', ' ', node.get_text(' ', strip=True)).strip()


def prepare(folder):
    slug = folder.name
    data = json.loads((folder / 'bilingual.json').read_text())
    source = ROOT / 'sources/fulltext' / slug
    assets = folder / 'assets'
    assets.mkdir(exist_ok=True)
    result = dict(slug=slug, math={}, visuals={}, suppress=[], original_pages={}, downloads=[])
    html_path = source / 'arxiv-fulltext.html'
    # The SurveyForge HTML is an arXiv preprint; the reader uses ACL's formal
    # PDF. Keep that version boundary by using the formal PDF's own pages.
    if html_path.exists() and slug != 'surveyforge':
        soup = BeautifulSoup(html_path.read_text(), 'html.parser')
        article = soup.find('article')
        base_url = data['source']['html']
        for math in article.find_all('math'):
            tex = math.get('alttext')
            if tex:
                result['math'][normalized(tex)] = dict(tex=tex, html=str(math))
        candidates = article.find_all('figure')
        candidates = [n for n in candidates if not n.find_parent('figure')]
        candidates += [n for n in article.select('table.ltx_equation, table.ltx_equationgroup') if not n.find_parent('figure') and not n.find_parent('table')]
        used = set()
        downloads = {}
        for node in candidates:
            cap = node.find('figcaption', recursive=False) or next((c for c in node.find_all('figcaption') if caption_key(c.get_text(' ', strip=True))), None)
            key = caption_key(cap.get_text(' ', strip=True)) if cap else None
            uid = None
            if key:
                uid = next((u['id'] for u in data['units'] if u['id'] not in used and caption_key(u['en']) == key and (u['kind'] == 'caption' or u['kind'] == 'prose')), None)
            elif node.get('id'):
                uid = next((u['id'] for u in data['units'] if u.get('anchor') == node['id']), None)
            if not uid:
                continue
            used.add(uid)
            fragment = BeautifulSoup(str(node), 'html.parser')
            for tag in fragment.select('script, style, iframe, link, figcaption'):
                tag.decompose()
            # LaTeXML sometimes puts long prompt tables inside fixed-size SVG
            # foreignObjects. Their text overflows when the surrounding reader
            # font differs. Reflow those text-only table panels as normal HTML;
            # retain actual figure SVGs and all source words/math unchanged.
            if 'ltx_table' in node.get('class', []):
                for svg in list(fragment.find_all('svg')):
                    objects = svg.find_all(lambda tag: tag.name.lower() == 'foreignobject')
                    if not objects:
                        continue
                    panels = soup.new_tag('div', attrs={'class': 'original-text-panels'})
                    for obj in objects:
                        panel = soup.new_tag('div', attrs={'class': 'original-text-panel'})
                        for child in list(obj.contents):
                            panel.append(child.extract())
                        for child in panel.select('[style]'):
                            child.attrs.pop('style', None)
                        panels.append(panel)
                    svg.replace_with(panels)
            for img in fragment.select('img, object'):
                relative = img.get('src') or img.get('data')
                if not relative:
                    continue
                url = urljoin(base_url + '/', relative) if not relative.startswith('/') else urljoin(base_url, relative)
                # arXiv embeds version-prefixed paths relative to /html/.
                if relative.startswith(data['source']['arxiv'] + '/'):
                    url = urljoin('https://arxiv.org/html/', relative)
                ext = Path(urlsplit(url).path).suffix.lower()
                if ext not in {'.png', '.jpg', '.jpeg', '.svg', '.webp', '.gif'}:
                    raise ValueError(f'Unexpected figure asset: {url}')
                name = hashlib.sha256(url.encode()).hexdigest()[:20] + ext
                downloads[url] = assets / name
                image = soup.new_tag('img', src='assets/' + name)
                image['alt'] = (cap.get_text(' ', strip=True)[:160] if cap else node.get('id', 'Original figure'))
                image['loading'] = 'lazy'
                image['decoding'] = 'async'
                img.replace_with(image)
            for tag in fragment.find_all(True):
                for attr in list(tag.attrs):
                    if attr.lower().startswith('on'):
                        del tag[attr]
                if tag.name == 'a' and tag.get('href', '').startswith('#'):
                    tag['href'] = base_url + tag['href']
            rendered = str(fragment)
            visual = dict(source_id=node.get('id', ''), html=rendered, source_url=base_url, kind='figure' if key and key[0] == 'figure' else 'original-block')
            result['visuals'][uid] = visual
            prefix = node.get('id', '')
            content = normalized(source_text(node))
            for u in data['units']:
                if u['id'] == uid or u['kind'] in {'caption', 'heading', 'page', 'frontmatter', 'reference'}:
                    continue
                anchor = u.get('anchor', '')
                inside = bool(prefix and anchor and (anchor == prefix or anchor.startswith(prefix + '.')))
                long_match = len(normalized(u['en'])) > 70 and normalized(u['en']) in content
                if inside or long_match:
                    result['suppress'].append(u['id'])

        def download(item):
            url, target = item
            if not target.exists():
                with urlopen(Request(url, headers={'User-Agent': 'Mozilla/5.0'}), timeout=90) as response:
                    content = response.read()
                    if not content:
                        raise ValueError('Empty asset: ' + url)
                    target.write_bytes(content)
            return dict(url=url, file=str(target.relative_to(folder)), sha256=hashlib.sha256(target.read_bytes()).hexdigest())
        with ThreadPoolExecutor(max_workers=6) as pool:
            result['downloads'] = list(pool.map(download, downloads.items()))

    if data['extraction'].startswith('PDF'):
        pages = data['source']['pages']
        if not all((assets / f'original-page-{n:03d}.jpg').exists() for n in range(1, pages + 1)):
            # Poppler's output padding is based on page count. Rename below to
            # one stable convention shared by all documents.
            subprocess.run(['pdftoppm', '-jpeg', '-r', '125', '-jpegopt', 'quality=85', str(source / 'original.pdf'), str(assets / 'page')], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            for path in assets.glob('page-*.jpg'):
                n = int(path.stem.split('-')[-1])
                path.rename(assets / f'original-page-{n:03d}.jpg')
        result['original_pages'] = {str(n): f'assets/original-page-{n:03d}.jpg' for n in range(1, pages + 1)}
    if slug == 'autoresearch':
        url = f'https://raw.githubusercontent.com/karpathy/autoresearch/{data["source"]["commit"]}/progress.png'
        target = assets / 'progress.png'
        if not target.exists():
            with urlopen(url, timeout=90) as response:
                target.write_bytes(response.read())
        uid = next(u['id'] for u in data['units'] if '![teaser]' in u['en'])
        result['visuals'][uid] = dict(source_id='progress.png', html='<figure><img src="assets/progress.png" alt="autoresearch progress chart" loading="lazy"></figure>', source_url=url, kind='figure')
    result['suppress'] = sorted(set(result['suppress']))
    (folder / 'visuals.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(dict(slug=slug, figures=len(result['visuals']), math=len(result['math']), assets=len(result['downloads']), original_pages=len(result['original_pages'])), ensure_ascii=False), flush=True)


def main():
    for folder in sorted(BASE.iterdir()):
        if (folder / 'bilingual.json').exists():
            prepare(folder)


if __name__ == '__main__':
    main()
