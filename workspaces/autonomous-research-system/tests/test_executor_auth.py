import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import executor_auth as auth


class ExecutorAuthTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / 'operations' / 'first'
        self.directory.mkdir(parents=True)
        self.calls = []
        self.events = [{'type': 'thread.started'}, {'type': 'turn.started'},
                       {'type': 'turn.failed', 'error': {'message': 'Quota exceeded. Check your plan and billing details.'}}]

    def publish(self, path, record):
        path.write_text(json.dumps(record))

    def fake_cli(self, argv, env):
        api = auth.KEY_ENV in env
        self.calls.append((api, argv))
        assert 'sk-fixture' not in ' '.join(argv)
        events = self.events if api else [{'type': 'turn.completed'}]
        (self.directory / 'events.jsonl').write_text(''.join(json.dumps(event) + '\n' for event in events))
        (self.directory / 'stderr.log').write_text('')
        return 1 if api else 0

    def execute(self, key='sk-fixture', reason=None):
        with patch.object(auth, 'read_preset', return_value=(key, reason)), \
                patch.object(auth, 'chatgpt_command', side_effect=lambda argv, _: argv):
            return auth.execute(['codex', 'exec', '--model', 'model-x', '-'],
                                self.directory, self.fake_cli, self.publish)

    def test_quota_before_execution_falls_back_once_and_retains_rejection(self):
        code, routing = self.execute()
        self.assertEqual(code, 0)
        self.assertEqual([api for api, _ in self.calls], [True, False])
        self.assertEqual(routing['selected'], 'chatgpt')
        self.assertEqual(routing['reason'], 'insufficient_quota')
        self.assertIn('Quota exceeded.', (self.directory / 'api-rejection.events.jsonl').read_text())
        self.directory = self.root / 'operations' / 'second'
        self.directory.mkdir()
        _, routing = self.execute()
        self.assertEqual(routing['reason'], 'known_api_quota_exhausted')
        self.assertEqual([api for api, _ in self.calls], [True, False, False])

    def test_quota_after_a_tool_action_is_not_replayed(self):
        self.events.insert(2, {'type': 'item.completed', 'item': {'type': 'command_execution'}})
        code, routing = self.execute()
        self.assertEqual((code, routing['selected']), (1, 'openai_api'))
        self.assertEqual([api for api, _ in self.calls], [True])
        self.assertTrue((self.root / 'executor-auth-quota.json').is_file())

    def test_rate_limit_and_missing_key_are_distinguished(self):
        self.events[-1]['error'] = {'code': 'rate_limit_exceeded', 'message': '429'}
        self.assertEqual(self.execute()[0], 1)
        self.assertFalse((self.root / 'executor-auth-quota.json').exists())
        self.assertEqual(self.execute(key=None, reason='no_openai_api_preset')[1]['selected'], 'chatgpt')
        self.assertEqual([api for api, _ in self.calls], [True, False])

    def test_only_a_unique_direct_openai_preset_is_read(self):
        database = self.root / 'fixture.db'
        with sqlite3.connect(database) as db:
            db.execute('CREATE TABLE providers(app_type, settings_config)')
            for url in ('https://example.org/v1', auth.ENDPOINT):
                db.execute('INSERT INTO providers VALUES (?,?)', ('codex', json.dumps({
                    'config': f'base_url = "{url}"', 'auth': {'OPENAI_API_KEY': 'sk-fixture'},
                })))
        self.assertEqual(auth.read_preset(database), ('sk-fixture', None))


if __name__ == '__main__':
    unittest.main()
