"""Durable accounting fault tests; all provider metadata is synthetic."""
import json
from pathlib import Path
import sqlite3
import unittest
from unittest.mock import patch
import test_token_usage as fixtures
import token_usage as live
import usage_ledger as ledger
import ars


class UsageLedgerTests(unittest.TestCase):
    setUp = fixtures.TokenUsageTests.setUp
    operation = fixtures.TokenUsageTests.operation
    row = fixtures.TokenUsageTests.row
    session = fixtures.TokenUsageTests.session

    def test_log_rotation_and_process_restart_retain_actual_model_and_tokens(self):
        op = self.operation(failed=True, saved_thread=False)
        path = self.session()
        ledger.sync(self.store, self.index)
        path.unlink()
        for name in ('events.jsonl', 'receipt.json', 'request.json'):
            (Path(op['directory']) / name).unlink()
        result = live.describe(self.store, live.UsageIndex(self.sessions))
        self.assertEqual(result['totals']['total_tokens'], 120)
        self.assertEqual(result['models'][0]['model'], 'actual-model')
        self.assertEqual(result['persistence']['request_count'], 1)
        attempt = result['tasks'][0]['attempts'][0]
        self.assertEqual(attempt['configured_model'], 'configured-only')
        self.assertFalse(attempt['executor_success'])
        ledger.sync(self.store, live.UsageIndex(self.sessions))
        self.assertEqual(live.describe(self.store, live.UsageIndex(self.sessions))['totals']['total_tokens'], 120)

    def test_multiple_models_retries_and_failed_requests_are_saved_per_task(self):
        self.operation(failed=True)
        self.operation(thread=fixtures.B)
        self.session(rows=self.row('first', model='model-a'))
        self.session(thread=fixtures.B, rows=self.row('second', thread=fixtures.B, model='model-b', amount=200))
        ledger.sync(self.store, self.index)
        result = live.describe(self.store, self.index)
        task = result['tasks'][0]
        self.assertEqual(task['attempt_count'], 2)
        self.assertEqual({m['model']: m['total_tokens'] for m in task['model_usage']}, {'model-a': 120, 'model-b': 220})
        self.assertEqual(task['usage']['total_tokens'], 340)
        self.assertEqual(result['persistence']['request_count'], 2)

    def test_repeated_sync_and_copied_records_are_idempotent(self):
        self.operation(); self.session(); self.session(name='copy-'+fixtures.A+'.jsonl')
        for _ in range(3):
            self.assertEqual(ledger.sync(self.store, self.index)['requests'], 1)
        self.assertEqual(live.describe(self.store, self.index)['totals']['total_tokens'], 120)

    def test_conflicting_usage_is_flagged_and_cannot_rewrite_prior_cost(self):
        self.operation(); self.session()
        ledger.sync(self.store, self.index)
        self.session(rows=self.row('response', amount=9000))
        result = ledger.sync(self.store, live.UsageIndex(self.sessions))
        self.assertTrue(result['warnings'])
        self.assertEqual(live.describe(self.store, live.UsageIndex(self.sessions))['totals']['total_tokens'], 120)

    def test_missing_stays_unknown_and_requested_model_is_not_actual(self):
        self.operation(failed=True)
        ledger.sync(self.store, self.index)
        out = live.describe(self.store, self.index)
        self.assertEqual(out['missing_attempts'], 1)
        self.assertEqual(out['tasks'][0]['model_usage'], [])
        self.assertIsNone(out['tasks'][0]['attempts'][0]['usage'])
        self.assertEqual(out['tasks'][0]['attempts'][0]['configured_model'], 'configured-only')

    def test_metadata_collection_cannot_modify_scientific_or_budget_state(self):
        self.operation(); self.session()
        before, tasks = self.store.state(), self.store.tasks()
        ledger.sync(self.store, self.index)
        self.assertEqual(before, self.store.state())
        self.assertEqual(tasks, self.store.tasks())
        self.assertEqual(ledger.read(self.directory)['requests'][0]['task_id'], tasks[0]['id'])

    def test_collection_failure_does_not_stop_or_retry_research(self):
        self.operation(); before = self.store.state()
        with patch.object(ledger, 'sync', side_effect=sqlite3.OperationalError('synthetic disk failure')):
            status = ledger.safe_sync(self.store)
        self.assertFalse(status['ok'])
        self.assertEqual(before, self.store.state())
        self.assertFalse(live.describe(self.store, self.index)['persistence']['collector_ok'])

    def test_partial_jsonl_is_saved_only_when_complete(self):
        self.operation(); path = self.session()
        ledger.sync(self.store, self.index)
        extra = self.row('second', amount=200)
        with path.open('a') as f:
            f.write(json.dumps(extra[0])+'\n'+json.dumps(extra[1]))
        self.assertEqual(ledger.sync(self.store, self.index)['requests'], 1)
        with path.open('a') as f:
            f.write('\n')
        self.assertEqual(ledger.sync(self.store, self.index)['requests'], 2)
        self.assertEqual(live.describe(self.store, self.index)['totals']['total_tokens'], 340)

    def test_reservation_hook_records_requested_model_before_dispatch(self):
        operation = ars.reserve_task(self.store, self.store.tasks()[0])
        saved = ledger.read(self.directory)['operations'][operation['id']]
        self.assertEqual(saved['configured_model'], 'configured-only')
        self.assertEqual(saved['task_id'], self.store.tasks()[0]['id'])
        self.assertEqual(saved['state'], 'RESERVED')
        self.assertEqual(ledger.read(self.directory)['requests'], [])

    def test_null_usage_record_is_not_a_zero_cost_request(self):
        self.operation()
        self.session(rows=[dict(type='token_usage_record', payload=dict(response_id='empty', thread_id=fixtures.A, usage=None))])
        ledger.sync(self.store, self.index)
        result = live.describe(self.store, self.index)
        self.assertEqual(result['missing_attempts'], 1)
        self.assertEqual(result['request_count'], 0)
        self.assertTrue(result['warnings'])


if __name__ == '__main__':
    unittest.main()
