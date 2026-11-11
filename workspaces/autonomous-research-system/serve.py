#!/usr/bin/env python3
"""Serve this design and its figures on loopback; no research execution."""
import argparse
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit
from runtime_web import RuntimeMixin

REPO = Path(__file__).resolve().parents[2]
PREFIX = '/workspaces/autonomous-research-system/'
ALLOWED = {PREFIX + name for name in (
    'index.html', 'runtime.html', 'README.md', 'design.json', 'history-audit.json',
    'replay-cases.json', 'validation.json', 'runtime-validation.json',
    'figures/system-overview.svg', 'figures/system-overview.png',
)} | {
    '/workspaces/index.html', '/workspaces/topics.json', '/README.md', '/AGENTS.md',
    '/workspaces/ucs-genrl/README.md',
    '/workspaces/bearing-swarm-review/README.md',
    '/workspaces/geometry-planning-survey/README.md',
}


class Handler(RuntimeMixin, SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO), **kwargs)

    def send_head(self):
        path = unquote(urlsplit(self.path).path)
        if path == '/':
            self.send_response(302)
            self.send_header('Location', PREFIX + 'runtime.html')
            self.end_headers()
            return None
        if path not in ALLOWED:
            self.send_error(404)
            return None
        resolved = (REPO / path.lstrip('/')).resolve()
        if not resolved.is_relative_to(REPO):
            self.send_error(404)
            return None
        return super().send_head()

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=18767)
    args = parser.parse_args()
    ThreadingHTTPServer(('127.0.0.1', args.port), Handler).serve_forever()


if __name__ == '__main__':
    main()
