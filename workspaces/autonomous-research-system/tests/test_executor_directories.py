"""Registered task directories do not need a second Git repository."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ars


class PlainDirectoryExecutorTests(unittest.TestCase):
    def test_readonly_paper_and_repair_keep_their_sandbox_without_requiring_git(self):
        with tempfile.TemporaryDirectory() as folder:
            for workflow, repair, sandbox in [('readonly', False, 'read-only'),
                                              ('paper', False, 'workspace-write'),
                                              ('readonly', True, 'workspace-write')]:
                context = {'execution_workflow': {'execution_directory': folder, 'write_scope': []}}
                if repair:
                    context['code_repair'] = {'synthetic': True}
                request = {'config': {'codex_bin': 'synthetic-codex', 'workflow': workflow},
                           'context': context, 'executor_directory': folder}
                with patch.object(ars.model_routing, 'apply_argv', side_effect=lambda args, request: args):
                    argv = ars.executor_argv(request, Path(folder) / 'schema.json', Path(folder) / 'result.json')
                self.assertEqual(argv.count('--skip-git-repo-check'), 1)
                self.assertEqual(argv[argv.index('--sandbox') + 1], sandbox)
                self.assertEqual(argv[argv.index('-C') + 1], folder)
                self.assertFalse((Path(folder) / '.git').exists())
