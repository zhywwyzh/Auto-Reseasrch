"""Local compatibility retains behavior without shipping research modules."""
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import local_extensions


class LocalExtensionTests(unittest.TestCase):
    def test_empty_clone_has_no_implicit_profile_or_authority(self):
        with tempfile.TemporaryDirectory() as temporary:
            public = Path(temporary) / 'workspaces/system/sample.py'
            public.parent.mkdir(parents=True)
            public.write_text('value = "generic"\n')
            namespace = {'__file__': str(public), '__name__': 'sample', 'value': 'generic'}
            self.assertFalse(local_extensions.apply(namespace))
            self.assertEqual(namespace['value'], 'generic')

    def test_original_path_semantics_and_single_cli_entrypoint_are_preserved(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            public = root / 'workspaces/system/sample.py'
            public.parent.mkdir(parents=True)
            public.write_text('value = "generic"\n')
            private = root / '.local/system-modules/sample.py'
            private.parent.mkdir(parents=True)
            private.write_text('value = "local synthetic compatibility"\npath = __file__\nif __name__ == "__main__":\n    raise RuntimeError("must not run twice")\n')
            namespace = {'__file__': str(public), '__name__': '__main__'}
            self.assertTrue(local_extensions.apply(namespace))
            self.assertEqual(namespace['path'], str(public))
            self.assertEqual(namespace['value'], 'local synthetic compatibility')
            self.assertEqual(local_extensions.source(public), private.read_text())
            private.unlink()
            private.symlink_to(public)
            with self.assertRaisesRegex(ValueError, 'symlink'):
                local_extensions.apply(namespace)
