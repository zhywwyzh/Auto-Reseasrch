"""Vendored sources must remain verifiable without independent Git repositories."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location(
    'verify_sources', Path(__file__).resolve().parents[2] / 'external/verify_sources.py')
sources = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sources)


class VendoredSourcesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'autonomous-science/synthetic-source'
        self.repo.mkdir(parents=True)
        raw = b'print("synthetic source")\n'
        self.source = self.repo / 'main.py'
        self.source.write_bytes(raw)
        lock = {'format': 1, 'mode': 'vendored-source', 'repositories': [{
            'path': 'external/autonomous-science/synthetic-source',
            'files': [{'path': 'main.py', 'sha256': hashlib.sha256(raw).hexdigest()}]}]}
        (self.root / 'sources.lock.json').write_text(json.dumps(lock))

    def test_clean_source_needs_no_git_metadata(self):
        result = sources.verify(self.root, 'autonomous-science')
        self.assertEqual(result['failures'], [])
        self.assertEqual(result['files_checked'], 1)

    def test_changed_and_missing_source_are_reported(self):
        self.source.write_text('modified\n')
        self.assertIn('changed', sources.verify(self.root)['failures'][0])
        self.source.unlink()
        self.assertIn('missing', sources.verify(self.root)['failures'][0])

    def test_nested_git_file_and_directory_are_rejected(self):
        marker = self.repo / '.git'
        marker.write_text('gitdir: somewhere\n')
        self.assertIn('nested Git', sources.verify(self.root)['failures'][0])
        marker.unlink()
        marker.mkdir()
        self.assertIn('nested Git', sources.verify(self.root)['failures'][0])

    def test_paths_cannot_escape_or_follow_symlinks(self):
        for name in ['../private', '/private', '.git/config']:
            with self.assertRaises(ValueError):
                sources.safe_path(self.root, name)
        (self.repo / 'link').symlink_to(self.source)
        with self.assertRaises(ValueError):
            sources.safe_path(self.repo, 'link')

    def test_missing_group_cannot_silently_pass(self):
        with self.assertRaisesRegex(ValueError, 'No source repositories'):
            sources.verify(self.root, 'ai-paper-tools')

    def test_review_tools_share_the_same_main_repository_manifest(self):
        external = self.root / 'combined/external'
        external.mkdir(parents=True)
        review = external.parent / 'paper-review-ai/upstream/synthetic-review'
        review.mkdir(parents=True)
        raw = b'print("synthetic review tool")\n'
        (review / 'main.py').write_bytes(raw)
        lock = {'format': 1, 'mode': 'vendored-source', 'repositories': [{
            'path': 'paper-review-ai/upstream/synthetic-review',
            'files': [{'path': 'main.py', 'sha256': hashlib.sha256(raw).hexdigest()}]}]}
        (external / 'sources.lock.json').write_text(json.dumps(lock))
        result = sources.verify(external, 'paper-review-ai')
        self.assertEqual(result['files_checked'], 1)
        self.assertEqual(result['failures'], [])


if __name__ == '__main__':
    unittest.main()
