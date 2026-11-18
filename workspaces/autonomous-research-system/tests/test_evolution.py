"""Actual sandbox execution, paired evaluation, lineage and crash/receipt recovery."""
import contextlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import ars
import evolution
import evolution_benchmark as benchmark
import strategy_runtime as strategy


@unittest.skipUnless(shutil.which('bwrap'), 'bubblewrap required')
class EvolutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.archive = evolution.Archive(self.root / 'archive'); self.addCleanup(self.archive.close)
        self.archive.configure(max_calls=2, timeout=30)
        self.initial = self.archive.register(HERE, origin='fixture-baseline')
        self.archive.promote(self.initial['id'], initial=True)

    def candidate(self, change):
        target = self.root / ars.uid(); target.mkdir()
        for name in strategy.FILES:
            text = (HERE / name).read_text()
            (target / name).write_text(change(name, text))
        return target

    def test_actual_sandbox_benchmark_and_capabilities(self):
        result = self.initial['evaluation']
        self.assertTrue(result['viable'], result)
        self.assertEqual(result['correct'], result['total'])
        self.assertTrue(all(result['capabilities'].values()))

    def test_candidate_cannot_read_host_or_evaluator(self):
        secret = self.root / 'should-not-be-readable'; secret.write_text('private')
        for destination in (str(secret), str(HERE / 'evolution_benchmark.py'), '/etc/passwd'):
            candidate = self.candidate(lambda name, text: text + ('\nopen(' + repr(destination) + ').read()\n' if name == 'runtime_policy.py' else ''))
            result = benchmark.evaluate(candidate)
            self.assertFalse(result['viable'])
            self.assertIn('No such file', result['error'])

    def test_regression_is_archived_but_never_deployed(self):
        candidate = self.candidate(lambda name, text: text + ('\ndef classify(error):\n    return "transport"\n' if name == 'runtime_policy.py' else ''))
        version = self.archive.register(candidate, self.initial['id'], 'test-regression')
        self.assertTrue(version['viable'])  # open-ended archive retains viable stepping stones
        result = self.archive.promote(version['id'])
        self.assertFalse(result['promoted'])
        self.assertEqual(self.archive.active()['id'], self.initial['id'])
        self.assertEqual(version['parent'], self.initial['id'])

    def test_tampered_version_and_changed_evaluator_rejected(self):
        version_dir = self.archive.root / 'versions' / self.initial['id']
        (version_dir / 'runtime_policy.py').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'modified'):
            self.archive.version(self.initial['id'])
        with patch.object(benchmark, 'contract_hash', return_value='changed'):
            with self.assertRaisesRegex(ValueError, 'evaluator changed'):
                self.archive.reserve()

    def test_parent_guidance_drives_next_generation(self):
        marker = 'PARENT-SELF-MODIFICATION-MARKER'
        source = self.candidate(lambda name, text: text + ('\n_old = improvement_prompt\ndef improvement_prompt(context):\n    return ' + repr(marker) + ' + _old(context)\n' if name == 'research_strategy.py' else ''))
        parent = self.archive.register(source, self.initial['id'], 'fixture-parent')
        op = self.archive.reserve(parent=parent['id'])
        request = ars.read_json(self.archive.root / 'operations' / op / 'request.json')
        self.assertIn(marker, request['prompt'])
        self.assertEqual(request['parent'], parent['id'])
        self.assertNotIn('route_receipt', request['prompt'])  # hidden split never supplied

    def test_unknown_not_redispatched_and_budget_never_reset(self):
        op = self.archive.reserve()
        self.archive.reconcile()
        row = self.archive.db.execute('SELECT * FROM operations WHERE id=?', (op,)).fetchone()
        self.assertEqual(row['state'], 'UNKNOWN')
        with self.assertRaisesRegex(ValueError, 'reconciled'):
            self.archive.reserve()
        self.assertEqual(self.archive.config()[1], 1)
        with self.assertRaisesRegex(ValueError, 'Already initialized'):
            self.archive.configure()

    def test_late_receipt_recovered_once_and_bad_files_rejected(self):
        op = self.archive.reserve(); self.archive.reconcile()
        directory = self.archive.root / 'operations' / op
        ars.atomic_json(directory / 'receipt.json', {'id': op, 'success': True, 'usage': {'input_tokens': 123}})
        ars.atomic_json(directory / 'result.json', {'hypothesis': 'illegal file', 'files': {'../ars.py': 'pass'}})
        self.archive.reconcile(); self.archive.reconcile()
        self.assertEqual(self.archive.db.execute('SELECT state FROM operations WHERE id=?', (op,)).fetchone()[0], 'FAILED')
        self.assertEqual(self.archive.config()[1], 1)
        self.assertFalse((self.archive.root / 'operations/ars.py').exists())

    def test_manual_to_autonomous_lineage_and_rollback(self):
        # Smaller equivalent source validates real promotion/rollback; label is a fixture.
        import ast
        def simplify(name, text):
            tree = ast.parse(text)
            for node in ast.walk(tree):
                if isinstance(node, (ast.Module, ast.FunctionDef)) and node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str):
                    node.body.pop(0)
            return ast.unparse(tree) + '\n'
        candidate = self.candidate(simplify)
        op = self.archive.reserve(parent=self.initial['id']); directory = self.archive.root / 'operations' / op
        ars.atomic_json(directory / 'receipt.json', {'id': op, 'success': True, 'usage': {}})
        ars.atomic_json(directory / 'result.json', {'hypothesis': 'fixture simplification', 'files': {n: (candidate / n).read_text() for n in strategy.FILES}})
        self.archive.reconcile()
        version = self.archive.version(op)
        self.assertEqual(version['parent'], self.initial['id'])
        self.assertEqual(version['origin'], 'autonomous-model')
        if self.archive.active()['id'] == op:
            self.archive.rollback('fixture rollback')
            self.assertEqual(self.archive.active()['id'], self.initial['id'])
        # Test promotion evidence independently even if AST formatting didn't save 5%.
        accepted, _ = benchmark.promotion(version['evaluation'], self.initial['evaluation'], 90, 100)
        self.assertTrue(accepted)

    def test_stop_retains_budget_and_blocks_next_call(self):
        self.archive.stop()
        self.assertIsNone(self.archive.reserve())
        self.assertEqual(self.archive.config()[1], 0)


if __name__ == '__main__': unittest.main()
