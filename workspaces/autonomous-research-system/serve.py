"""Serve the workspace locally or on a network with connection-code access."""
import argparse
import io
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit, parse_qs
from runtime_web import RuntimeMixin
from render_help import render_help
import research_delivery
import workspace_access
REPO = Path(__file__).resolve().parents[2]
PREFIX = '/workspaces/autonomous-research-system/'
ALLOWED = {PREFIX + name for name in ('index.html', 'runtime.html', 'system.html', 'system-sources.json', 'system-validation.json', 'usage.html', 'research-goals.html', 'research-goals.json', 'journal-review.html', 'README.md', 'design.json', 'history-audit.json', 'replay-cases.json', 'validation.json', 'runtime-validation.json', 'shared-delivery-validation-2026-11-14.json', 'paper-quality-validation-2026-11-16.json', 'token-audit-2026-11-16.html', 'token-audit-2026-11-16.json', 'figures/system-overview.svg', 'figures/system-overview.png')} | {'/workspaces/index.html', '/workspaces/topics.json', '/README.md', '/AGENTS.md', '/docs/research/ai-paper-review/aas-review-profile.json'}

class Handler(RuntimeMixin, SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(REPO), **kwargs)

    def public_shell(self):
        path = unquote(urlsplit(self.path).path)
        return parse_qs(urlsplit(self.path).query).get('legacy') != ['1'] and (path == '/' or path in {PREFIX + name for name in ('runtime.html', 'system.html', 'index.html', 'usage.html', 'research-goals.html', 'journal-review.html')} or path.startswith(PREFIX + 'ui/dist/'))

    def do_GET(self):
        if workspace_access.handle_access(self, public=self.public_shell()):
            super().do_GET()

    def do_HEAD(self):
        if workspace_access.handle_access(self, public=self.public_shell()):
            super().do_HEAD()

    def do_POST(self):
        if workspace_access.handle_access(self):
            super().do_POST()

    def send_head(self):
        path = unquote(urlsplit(self.path).path)
        ui_root = REPO / 'workspaces/autonomous-research-system/ui/dist'
        ui_entry = ui_root / 'index.html'
        ui_pages = {PREFIX + name for name in ('runtime.html', 'system.html', 'index.html', 'usage.html', 'research-goals.html', 'journal-review.html')}
        legacy = parse_qs(urlsplit(self.path).query).get('legacy') == ['1']
        if path in ui_pages and (not legacy) and ui_entry.is_file():
            body = ui_entry.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            return io.BytesIO(body)
        if path.startswith(PREFIX + 'ui/dist/'):
            asset = REPO / path.lstrip('/')
            if asset.resolve().is_relative_to(ui_root.resolve()) and asset.is_file() and (not any((p.is_symlink() for p in [asset, *asset.parents] if p.is_relative_to(ui_root)))) and (asset.suffix in ('.html', '.js', '.css', '.woff', '.woff2')):
                return super().send_head()
            self.send_error(404)
            return None
        if path == '/':
            self.send_response(302)
            self.send_header('Location', PREFIX + 'runtime.html')
            self.end_headers()
            return None
        if path not in ALLOWED and (not research_delivery.allowed_file(REPO, path)):
            self.send_error(404)
            return None
        resolved = (REPO / path.lstrip('/')).resolve()
        if not resolved.is_relative_to(REPO):
            self.send_error(404)
            return None
        raw = parse_qs(urlsplit(self.path).query).get('raw') == ['1']
        if path == PREFIX + 'README.md' and (not raw):
            self.send_response(302)
            self.send_header('Location', PREFIX + 'usage.html')
            self.end_headers()
            return None
        if path.endswith('.md') and (not raw) and resolved.is_file():
            body = render_help(resolved.read_text(encoding='utf-8'), path + '?raw=1').encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            return io.BytesIO(body)
        return super().send_head()

    def guess_type(self, path):
        mime = 'text/plain' if Path(path).suffix.lower() == '.md' else super().guess_type(path)
        if mime.startswith('text/') or mime in ('application/json', 'image/svg+xml'):
            return mime + '; charset=utf-8'
        return mime

    def end_headers(self):
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Cache-Control', 'no-cache')
        super().end_headers()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--port', type=int, default=18767)
    parser.add_argument('--host', default='127.0.0.1', help='默认本机；填写0.0.0.0开放网络连接，远程浏览器须输入连接码')
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), Handler)
    if not workspace_access.is_loopback(args.host):
        server.workspace_access = workspace_access.WorkspaceAccess.load(REPO / '.local/workbench-access.json')
    server.serve_forever()
import local_extensions as _local_extensions
_local_extensions.apply(globals())
if __name__ == '__main__':
    main()
