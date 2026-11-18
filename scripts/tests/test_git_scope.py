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
        (self.repo / 'external').mkdir()
        shutil.copyfile(root / 'external/.gitignore', self.repo / 'external/.gitignore')
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

    def test_external_source_allowlist_keeps_new_task_files_private(self):
        self.stage('external/README.md', 'Reviewed public source documentation.\n')
        self.assertEqual(scope.check(self.repo), [])
        name = 'external/autonomous-science/autoresearch/new-private-task.py'
        oid = self.git('hash-object', '-w', '--stdin', input=b'private_result = 1\n').decode().strip()
        self.git('update-index', '--add', '--cacheinfo', '100644,' + oid + ',' + name)
        self.assertIn(name, scope.check(self.repo))

    def test_external_allowlist_does_not_exempt_private_content(self):
        self.stage('external/README.md', 'EXAMPLE-PRIVATE-A local task result.\n')
        self.assertEqual(scope.check_content(self.repo), ['external/README.md'])

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

    def test_internal_checkpoint_references_cannot_be_pushed(self):
        self.git('commit', '-qm', 'Clean synthetic root')
        oid = self.git('rev-parse', 'HEAD').decode().strip()
        result = subprocess.run([sys.executable, history.__file__, '--repo', str(self.repo), '--pre-push'],
                                input=f'refs/internal/checkpoint {oid} refs/internal/checkpoint {"0" * 40}\n',
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn('local-only', result.stderr)

    def test_tag_annotation_and_raw_tree_cannot_export_private_payloads(self):
        self.git('commit', '-qm', 'Clean synthetic root')
        self.git('tag', '-a', 'v-test', '-m', 'EXAMPLE-PRIVATE-A synthetic annotation')
        objects = [(self.git('rev-parse', 'v-test').decode().strip(), 'refs/tags/v-test'),
                   (self.git('rev-parse', 'HEAD^{tree}').decode().strip(), 'refs/heads/test-tree')]
        for oid, reference in objects:
            result = subprocess.run([sys.executable, history.__file__, '--repo', str(self.repo), '--pre-push'],
                                    input=f'{reference} {oid} {reference} {"0" * 40}\n', text=True, capture_output=True)
            self.assertEqual(result.returncode, 1)


if __name__ == '__main__':
    unittest.main()
