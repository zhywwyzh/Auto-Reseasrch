"""Synthetic leakage attempts must fail for both the index and old history."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import check_git_scope as scope
import check_git_history as history


class PublicationBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        self.git('init', '-q', '-b', 'main')
        self.git('config', 'user.name', 'Synthetic Test')
        self.git('config', 'user.email', 'synthetic@example.invalid')
        root = Path(__file__).resolve().parents[2]
        shutil.copyfile(root / '.gitignore', self.repo / '.gitignore')
        (self.repo / 'workspaces').mkdir()
        (self.repo / 'workspaces/topics.json').write_text(json.dumps({'topics': [
            {'id': 'EXAMPLE-PRIVATE-A', 'workspace': 'workspaces/synthetic-private-topic'}]}))
        self.stage('README.md', 'Reusable workspace source.\n')
        self.git('add', '--', '.gitignore')

    def git(self, *args, input=None):
        return subprocess.check_output(['git', '-C', str(self.repo), *args], input=input)

    def stage(self, name, text):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        self.git('add', '--', name)

    def test_task_paths_rejected_even_when_inserted_directly_into_the_index(self):
        name = 'workspaces/synthetic-private-topic/result.json'
        oid = self.git('hash-object', '-w', '--stdin', input=b'{"synthetic": true}').decode().strip()
        self.git('update-index', '--add', '--cacheinfo', '100644,' + oid + ',' + name)
        self.assertIn(name, scope.check(self.repo))

    def test_content_check_reads_staged_version_and_not_working_tree(self):
        self.stage('README.md', 'EXAMPLE-PRIVATE-A task content.\n')
        (self.repo / 'README.md').write_text('Clean disk copy cannot hide staged data.\n')
        self.assertEqual(scope.check_content(self.repo), ['README.md'])
        self.git('add', '--', 'README.md')
        (self.repo / 'README.md').write_text('EXAMPLE-PRIVATE-A local-only edit.\n')
        self.assertEqual(scope.check_content(self.repo), [])

    def test_later_clean_commit_does_not_hide_private_history(self):
        self.stage('README.md', 'EXAMPLE-PRIVATE-A synthetic leak.\n')
        self.git('commit', '-qm', 'Synthetic contaminated commit')
        self.stage('README.md', 'Reusable source only.\n')
        self.git('commit', '-qm', 'Synthetic cleanup commit')
        self.assertEqual(scope.check_content(self.repo), [])
        commits, failures = history.inspect(self.repo, 'HEAD')
        self.assertEqual(len(commits), 2)
        self.assertTrue(any(reason == 'private content' for _, _, reason in failures))

    def test_clean_new_history_passes_and_symlink_cannot_bypass_it(self):
        self.git('commit', '-qm', 'Clean synthetic root')
        self.assertEqual(history.inspect(self.repo, 'HEAD')[1], [])
        oid = self.git('hash-object', '-w', '--stdin', input=b'../private').decode().strip()
        self.git('update-index', '--add', '--cacheinfo', '120000,' + oid + ',README.md')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            scope.check_content(self.repo)

    def test_private_data_in_commit_message_is_also_rejected(self):
        self.git('commit', '-qm', 'EXAMPLE-PRIVATE-A synthetic research summary')
        self.assertTrue(any(path == '<commit-message>' for _, path, _ in history.inspect(self.repo, 'HEAD')[1]))


if __name__ == '__main__':
    unittest.main()
