"""The UI build is public code; task directories remain inaccessible."""
from pathlib import Path
import json
import sqlite3
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import serve
import runtime_web


class LifecycleTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.row_factory = sqlite3.Row
        self.addCleanup(self.db.close)
        self.db.execute('CREATE TABLE events(seq INTEGER PRIMARY KEY, type TEXT, payload TEXT, created_at TEXT)')
        self.current = {'created_at': '2026-01-01T00:00:00+00:00', 'status': 'STOPPED_USER', 'reason': 'legacy user stop'}

    def state(self):
        return self.current

    def event(self, kind, at, **payload):
        self.db.execute('INSERT INTO events(type,payload,created_at) VALUES(?,?,?)', (kind, json.dumps(payload), at))

    def test_legacy_stop_is_unknown_and_updated_time_is_not_start_time(self):
        self.event('campaign.status', '2026-01-02', status='RUNNING')
        self.event('campaign.status', '2026-01-03', status='STOPPED_USER')
        self.event('report.updated', '2026-01-10')
        out = runtime_web.campaign_lifecycle(self)
        self.assertEqual(out['last_started_at'], '2026-01-02')
        self.assertEqual(out['stopped_at'], '2026-01-03')
        self.assertIsNone(out['stop_source'])
        self.assertIn('无法区分', out['stop_reason'])

    def test_explicit_stop_and_controller_restart_are_recorded(self):
        self.event('campaign.status', '2026-01-02', status='RUNNING')
        self.event('controller.started', '2026-01-04')
        self.event('campaign.status', '2026-01-05', status='STOPPED_USER')
        self.event('campaign.stop_requested', '2026-01-05', source='web')
        out = runtime_web.campaign_lifecycle(self)
        self.assertEqual(out['last_started_at'], '2026-01-04')
        self.assertEqual(out['stop_source'], 'web')

    def test_prior_stop_does_not_explain_new_legacy_stop(self):
        self.event('campaign.status', '2026-01-02', status='STOPPED_USER')
        self.event('campaign.stop_requested', '2026-01-02', source='web')
        self.event('campaign.status', '2026-01-03', status='RUNNING')
        self.event('campaign.status', '2026-01-04', status='STOPPED_USER')
        self.assertIsNone(runtime_web.campaign_lifecycle(self)['stop_source'])

    def test_unstarted_is_not_presented_as_started(self):
        self.current['status'] = 'READY'
        out = runtime_web.campaign_lifecycle(self)
        self.assertIsNone(out['last_started_at'])
        self.assertIsNone(out['stopped_at'])

    def test_latest_per_topic_uses_launch_dates_not_report_updates(self):
        rows = [dict(key='old', topic='T1', created_at='2026-01-01', last_started_at='2026-01-02', updated_at='2026-01-30'),
                dict(key='new', topic='T1', created_at='2026-01-03', last_started_at='2026-01-04', updated_at='2026-01-04'),
                dict(key='unstarted', topic='T2', created_at='2026-01-05', last_started_at=None)]
        ordered = runtime_web.order_campaigns(rows)
        self.assertEqual([r['key'] for r in ordered], ['unstarted', 'new', 'old'])
        self.assertEqual([r['is_latest_run'] for r in ordered], [True, True, False])


class AstryxRoutesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.ui = self.root / 'workspaces/autonomous-research-system/ui'
        (self.ui / 'dist/assets').mkdir(parents=True)
        (self.ui / 'dist/index.html').write_text('<html>synthetic Astryx build</html>')
        (self.ui / 'dist/assets/app.js').write_text('/* synthetic bundle */')
        (self.ui / 'package.json').write_text('{"private":true}')
        (self.ui.parent / 'runtime.html').write_text('legacy fixture')
        self.patch = patch.object(serve, 'REPO', self.root)
        self.patch.start(); self.addCleanup(self.patch.stop)
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), serve.Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.stop)
        self.base = 'http://127.0.0.1:' + str(self.server.server_port)

    def stop(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()

    def test_existing_entrypoints_render_unified_build_and_legacy_remains_readable(self):
        for page in ('runtime.html', 'system.html', 'index.html', 'usage.html', 'journal-review.html', 'research-goals.html'):
            with urlopen(self.base + serve.PREFIX + page) as response:
                self.assertIn(b'Astryx build', response.read())
                self.assertIn('text/html', response.headers['Content-Type'])
        self.assertEqual(urlopen(self.base + serve.PREFIX + 'runtime.html?legacy=1').read(), b'legacy fixture')

    def test_only_built_assets_are_exposed_and_symlinks_cannot_escape(self):
        with urlopen(self.base + serve.PREFIX + 'ui/dist/assets/app.js') as response:
            self.assertIn(b'bundle', response.read())
        outside = self.root / 'private.js'; outside.write_text('private fixture')
        (self.ui / 'dist/assets/escape.js').symlink_to(outside)
        for path in ('ui/package.json', 'ui/dist/assets/escape.js', 'ui/dist/assets/', 'ui/dist/../package.json'):
            with self.assertRaises(HTTPError) as error:
                urlopen(self.base + serve.PREFIX + path)
            self.assertEqual(error.exception.code, 404)

    def test_missing_build_keeps_operational_fallback(self):
        (self.ui / 'dist/index.html').unlink()
        self.assertEqual(urlopen(self.base + serve.PREFIX + 'runtime.html').read(), b'legacy fixture')
