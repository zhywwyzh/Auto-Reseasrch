#!/usr/bin/env python3
"""Serve the existing paper readers on loopback; expose no other repo files."""
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
import argparse

ROOT = Path(__file__).resolve().parents[1]
SLUGS = {
    'autosurvey', 'openscholar', 'surveyforge', 'co-scientist',
    'ai-scientist-v2', 'paperbench', 'astabench', 'epoch', 'autoresearch',
}


def permitted(path):
    parts = path.strip('/').split('/')
    if any(part in {'.', '..'} for part in parts):
        return False
    if path.startswith('/translations/fulltext/assets/katex/'):
        return Path(path).suffix.lower() in {'.css', '.woff2', '.woff', '.ttf', '.txt'}
    if len(parts) == 5 and parts[:2] == ['translations', 'fulltext'] and parts[2] in SLUGS and parts[3] == 'assets':
        return Path(parts[4]).suffix.lower() in {'.png', '.jpg', '.jpeg', '.svg', '.webp', '.gif'}
    if len(parts) == 3 and parts[:2] == ['translations', 'fulltext']:
        return parts[2] in {'index.html', 'README.md', 'quality-report.json'}
    if len(parts) == 4 and parts[:2] == ['translations', 'fulltext']:
        return parts[2] in SLUGS and parts[3] in {
            'bilingual.html', 'reading.html', 'bilingual.md', 'reading.md',
        }
    if len(parts) == 4 and parts[:2] == ['sources', 'fulltext']:
        return parts[2] in SLUGS and parts[3] in {'original.pdf', 'README.md', 'program.md'}
    if len(parts) == 3 and parts[:2] == ['output', 'pdf']:
        return parts[2] in {slug + '-zh-reading.pdf' for slug in SLUGS}
    return False


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def send_head(self):
        path = unquote(urlsplit(self.path).path)
        if path == '/':
            self.send_response(302)
            self.send_header('Location', '/translations/fulltext/index.html')
            self.end_headers()
            return None
        if not permitted(path):
            self.send_error(404)
            return None
        resolved = (ROOT / path.lstrip('/')).resolve()
        if not resolved.is_relative_to(ROOT):
            self.send_error(404)
            return None
        return super().send_head()

    def guess_type(self, path):
        mime = super().guess_type(path)
        if mime.startswith('text/'):
            return mime + '; charset=utf-8'
        return mime

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-cache')
        if urlsplit(self.path).path.endswith('.pdf'):
            self.send_header('Content-Disposition', 'inline')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=18766)
    args = parser.parse_args()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    print(f'Paper reader (this computer only): http://127.0.0.1:{args.port}/', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
