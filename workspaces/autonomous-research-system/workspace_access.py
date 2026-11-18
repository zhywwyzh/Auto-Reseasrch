"""Direct workspace access. Credentials and sessions never enter Git."""
import hashlib
import hmac
from http.cookies import SimpleCookie, CookieError
import ipaddress
import json
import os
from pathlib import Path
import secrets
import socket
import time
from urllib.parse import urlsplit

COOKIE = 'ars_workspace_session'
SESSION_SECONDS = 30 * 24 * 60 * 60


def is_loopback(address):
    try:
        return ipaddress.ip_address(address).is_loopback
    except ValueError:
        return address == 'localhost'


def host_allowed(handler):
    """Accept our actual destination IP, never arbitrary DNS Host headers."""
    try:
        value = handler.headers.get('Host', '')
        parsed = urlsplit('http://' + value)
        if parsed.netloc != value or parsed.path or parsed.username or parsed.password:
            return False
        host = parsed.hostname
        port = parsed.port or 80
        if port != handler.server.server_port:
            return False
        if host in ('127.0.0.1', 'localhost', '::1'):
            return True
        return (getattr(handler.server, 'workspace_access', None) is not None
                and ipaddress.ip_address(host) == ipaddress.ip_address(handler.connection.getsockname()[0]))
    except (ValueError, TypeError):
        return False


def local_request(handler):
    try:
        host = urlsplit('http://' + handler.headers.get('Host', '')).hostname
        return is_loopback(handler.client_address[0]) and is_loopback(host or '')
    except ValueError:
        return False


def same_origin(handler):
    origin = handler.headers.get('Origin')
    return origin is None or origin in {
        'http://' + handler.headers.get('Host', ''),
        'https://' + handler.headers.get('Host', ''),
    }


class WorkspaceAccess:
    def __init__(self, key):
        if not isinstance(key, str) or len(key) < 32:
            raise ValueError('工作空间连接码至少需要32个字符')
        self.key = key

    @classmethod
    def load(cls, filename):
        path = Path(filename)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        except FileExistsError:
            pass
        else:
            with os.fdopen(fd, 'w') as stream:
                json.dump({'access_key': secrets.token_urlsafe(32)}, stream)
                stream.write('\n')
        path.chmod(0o600)
        return cls(json.loads(path.read_text())['access_key'])

    def session(self):
        body = str(int(time.time())) + '.' + secrets.token_urlsafe(16)
        signature = hmac.new(self.key.encode(), body.encode(), hashlib.sha256).hexdigest()
        return body + '.' + signature

    def authenticated(self, handler):
        if local_request(handler):
            return True
        try:
            cookie = SimpleCookie(handler.headers.get('Cookie', ''))
            value = cookie[COOKIE].value
            created, nonce, signature = value.split('.')
            age = time.time() - int(created)
            expected = hmac.new(self.key.encode(), (created + '.' + nonce).encode(), hashlib.sha256).hexdigest()
            return 0 <= age <= SESSION_SECONDS and hmac.compare_digest(signature, expected)
        except (CookieError, KeyError, ValueError):
            return False

    def connection_info(self, handler):
        local = local_request(handler)
        result = {'authenticated': self.authenticated(handler), 'local': local,
                  'remote_enabled': True, 'address': handler.headers.get('Host', '')}
        if local:
            result['access_key'] = self.key
            result['addresses'] = local_addresses(handler.server.server_port)
        return result


def local_addresses(port):
    """Discover direct addresses for display only; never persist a server list."""
    import subprocess
    addresses = set()
    try:
        data = json.loads(subprocess.check_output(['ip', '-j', '-4', 'address', 'show'], timeout=2))
        for interface in data:
            if interface.get('ifname', '').startswith(('docker', 'br-', 'veth', 'cni', 'flannel', 'Meta')):
                continue
            for entry in interface.get('addr_info', []):
                if entry.get('scope') == 'global':
                    addresses.add(entry['local'])
    except (OSError, ValueError, subprocess.SubprocessError):
        try:
            addresses.update(row[4][0] for row in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET))
        except OSError:
            pass
    return ['http://' + address + ':' + str(port) for address in sorted(addresses) if not is_loopback(address)]


def handle_access(handler, public=False):
    """Guard both static research artifacts and runtime APIs before dispatch."""
    if not host_allowed(handler):
        handler.runtime_json(403, {'error': '工作空间地址不匹配'})
        return False
    access = getattr(handler.server, 'workspace_access', None)
    path = urlsplit(handler.path).path
    if path == '/api/agent/connection' and handler.command == 'GET':
        info = access.connection_info(handler) if access else {
            'authenticated': local_request(handler), 'local': local_request(handler),
            'remote_enabled': False, 'address': handler.headers.get('Host', ''),
        }
        handler.runtime_json(200, info)
        return False
    if path == '/api/agent/connect' and handler.command == 'POST':
        if access is None or not same_origin(handler):
            handler.runtime_json(403, {'error': '该工作空间未开放远程连接或请求来源不匹配'})
            return False
        try:
            size = int(handler.headers.get('Content-Length', '0'))
            if size <= 0 or size > 2048 or handler.headers.get('Content-Type', '').split(';')[0] != 'application/json':
                raise ValueError('无效的连接请求')
            data = json.loads(handler.rfile.read(size))
            key = data.get('access_key', '') if isinstance(data, dict) else ''
            if not isinstance(key, str) or not hmac.compare_digest(key.encode(), access.key.encode()):
                handler.runtime_json(401, {'error': '连接码不正确，请向目标工作空间的所有者获取连接码'})
                return False
        except (ValueError, UnicodeError):
            handler.runtime_json(400, {'error': '无效的连接请求'})
            return False
        handler.send_response(200)
        handler.send_header('Content-Type', 'application/json; charset=utf-8')
        handler.send_header('Set-Cookie', f'{COOKIE}={access.session()}; Path=/; HttpOnly; SameSite=Strict; Max-Age={SESSION_SECONDS}')
        handler.send_header('Content-Length', '22')
        handler.end_headers()
        handler.wfile.write(b'{"authenticated":true}')
        return False
    if public or (access.authenticated(handler) if access else local_request(handler)):
        return True
    handler.runtime_json(401, {'error': '请先输入目标工作空间的连接码', 'authentication_required': True})
    return False
