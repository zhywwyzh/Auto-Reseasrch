"""Reusable synthetic runtime fixtures; no scientific task or device."""
import contextlib, json, shutil, sys, tempfile, time, unittest
from pathlib import Path
HERE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(HERE))
import ars

class RuntimeFixtures(unittest.TestCase):

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'workspaces/autonomous-research-system').mkdir(parents=True)
        (self.root / 'workspaces/autonomous-research-system/README.md').write_text('自动研究系统：这是用于测试的本地来源。\n')
        shutil.copyfile(HERE / 'submission-targets.json', self.root / 'workspaces/autonomous-research-system/submission-targets.json')
        (self.root / 'AGENTS.md').write_text('保持课题隔离，不得编造研究结论。\n')
        (self.root / 'workspaces/topics.json').write_text(json.dumps({'topics': []}))
        self.campaigns = []

    def tearDown(self):
        for directory in self.campaigns:
            with contextlib.suppress(Exception):
                s = ars.Store(directory)
                for row in s.db.execute('SELECT directory FROM operations'):
                    ars.stop_activity(row[0])
                s.close()
        self.temp.cleanup()

    def create(self, **kwargs):
        directory = self.root / ('campaign-' + str(len(self.campaigns)))
        out = ars.create_campaign('ARS-DEMO', '检查研究方向与来源', directory=directory, repo=self.root, backend=kwargs.pop('backend', 'mock'), **kwargs)
        self.campaigns.append(out)
        return out

    def change_config(self, directory, **kwargs):
        s = ars.Store(directory)
        with s.tx():
            config = s.state()['config']
            config.update(kwargs)
            s.db.execute('UPDATE campaign SET config=?', (ars.dump(config),))
        s.close()

    def wait(self, predicate, seconds=10):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            value = predicate()
            if value:
                return value
            time.sleep(0.03)
        self.fail('等待运行状态超时')
