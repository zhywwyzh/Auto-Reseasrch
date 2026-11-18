"""Fresh shared runtime has no built-in research protocol or authorization."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import ars
import experiment_progress
import init_local


@unittest.skipIf(hasattr(ars, '__local_source__'), 'Fresh-clone checks run without local compatibility modules')
class PublicRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        shutil.copyfile(HERE.parents[1] / '.gitignore', self.root / '.gitignore')
        init_local.initialize(self.root)
        self.info = {'id': 'EXAMPLE-ALPHA', 'workspace': 'workspaces/synthetic-alpha',
                     'docs': 'docs/topics/synthetic-alpha', 'paper_reserved': 'papers/synthetic-alpha'}
        (self.root / 'workspaces/topics.json').write_text(json.dumps({'topics': [self.info]}))
        workspace = self.root / self.info['workspace']
        workspace.mkdir()
        (workspace / 'README.md').write_text('Synthetic fixture only; no device or scientific permission.\n')

    def test_independent_readonly_task_completes_without_any_model_or_equipment(self):
        directory = ars.create_campaign(self.info['id'], 'Inspect synthetic fixture only.',
                                        repo=self.root, backend='mock')
        result = ars.run_campaign(directory)
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['calls'], 4)

    def test_paper_workflow_has_no_default_scientific_protocol(self):
        with self.assertRaisesRegex(ValueError, '私有契约'):
            ars.create_campaign(self.info['id'], 'Synthetic paper workflow',
                                repo=self.root, workflow='paper', backend='codex')

    def test_progress_belongs_to_the_registered_task_and_never_means_scientific_acceptance(self):
        directory = self.root / self.info['workspace'] / 'runs/ars/synthetic-run'
        directory.mkdir(parents=True)
        state = {'repo': str(self.root), 'topic': self.info['id'], 'id': directory.name,
                 'config': {'workspace': self.info['workspace']}}
        experiment_progress.publish(directory, state, {'environment_steps': 3}, 'engineering_only')
        observed = experiment_progress.observe(directory, state)
        self.assertEqual(observed['metrics'][0]['value'], 3)
        self.assertEqual(observed['validation_status'], 'unknown')
        with self.assertRaisesRegex(ValueError, '归属'):
            experiment_progress.observe(directory, {**state, 'topic': 'EXAMPLE-BETA'})
