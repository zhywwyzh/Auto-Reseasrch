"""All dependencies are ordinary files and all task folders share one boundary."""
import importlib.util
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
import check_git_layout
import check_git_scope

spec = importlib.util.spec_from_file_location('layout_git_boundary', ROOT / 'workspaces/autonomous-research-system/git_boundary.py')
boundary = importlib.util.module_from_spec(spec)
spec.loader.exec_module(boundary)


class SingleRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        shutil.copyfile(ROOT / '.gitignore', self.repo / '.gitignore')

    def test_one_main_repository_with_ignored_task_is_valid(self):
        task = self.repo / 'workspaces/synthetic-private-task'
        task.mkdir(parents=True)
        (task / 'results.json').write_text('{"synthetic":true}')
        self.assertTrue(check_git_layout.inspect(self.repo)['passed'])
        self.assertTrue(boundary._assert_private(task, 'workspace', set())['ignored'])

    def test_empty_placeholder_has_no_history_but_metadata_and_pointers_are_rejected(self):
        task = self.repo / 'workspaces/synthetic-private-task'
        task.mkdir(parents=True)
        marker = task / '.git'
        marker.mkdir()
        self.assertTrue(check_git_layout.inspect(self.repo)['passed'])
        self.assertTrue(boundary._assert_private(task, 'workspace', set())['ignored'])
        (marker / 'HEAD').write_text('ref: refs/heads/synthetic\n')
        self.assertFalse(check_git_layout.inspect(self.repo)['passed'])
        with self.assertRaisesRegex(ValueError, '独立Git'):
            boundary._assert_private(task, 'workspace', set())
        (marker / 'HEAD').unlink()
        marker.rmdir()
        marker.write_text('gitdir: missing-local-metadata\n')
        self.assertFalse(check_git_layout.inspect(self.repo)['passed'])

    def test_valid_nested_task_repository_is_rejected(self):
        task = self.repo / 'workspaces/synthetic-private-task'
        subprocess.run(['git', 'init', '-q', str(task)], check=True)
        with self.assertRaisesRegex(ValueError, '嵌套Git'):
            boundary._assert_private(task, 'workspace', set())

    def test_gitlink_cannot_bypass_the_ordinary_file_policy(self):
        subprocess.run(['git', '-C', str(self.repo), 'update-index', '--add', '--cacheinfo',
                        '160000,' + '1' * 40 + ',external/synthetic-source'], check=True)
        self.assertEqual(check_git_layout.inspect(self.repo)['gitlinks'], ['external/synthetic-source'])
        with self.assertRaisesRegex(ValueError, 'submodules'):
            check_git_scope.check_content(self.repo)

    def test_former_execution_directory_with_auxiliary_files_is_not_a_git_repository(self):
        with tempfile.TemporaryDirectory() as temporary:
            plain = Path(temporary)
            cache = plain / '.git/editor-cache'
            cache.mkdir(parents=True)
            (cache / 'state.json').write_text('{"synthetic":true}')
            result = boundary._assert_private(plain, 'checkout.workspace', set())
            self.assertFalse(result['git'])

    def test_external_execution_repository_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            outside = Path(temporary)
            subprocess.run(['git', 'init', '-q', str(outside)], check=True)
            info = {'id': 'SYNTHETIC-A', 'workspace': 'workspaces/private-example',
                    'docs': 'docs/topics/private-example'}
            with self.assertRaisesRegex(ValueError, '独立Git'):
                boundary.validate_registration(self.repo, info,
                    self.repo / info['workspace'] / 'runs/example', checkout=outside)


if __name__ == '__main__':
    unittest.main()
