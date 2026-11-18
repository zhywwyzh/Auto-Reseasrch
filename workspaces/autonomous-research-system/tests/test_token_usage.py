"""Synthetic live usage, failure costs, run isolation and HTTP integration."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.request import urlopen
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ars
import runtime_web
import token_usage as live

A = '11111111-1111-4111-8111-111111111111'
B = '22222222-2222-4222-8222-222222222222'


class TokenUsageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);(self.root/'workspaces').mkdir()
        (self.root/'workspaces/topics.json').write_text(json.dumps({'topics':[dict(id='EXAMPLE-ALPHA',workspace='workspaces/synthetic-alpha',docs='docs/topics/synthetic-alpha')]}))
        self.directory=ars.create_campaign('EXAMPLE-ALPHA','SYNTHETIC usage fixture',repo=self.root,workflow='readonly',backend='codex',model='configured-only')
        self.store=ars.Store(self.directory);self.addCleanup(self.store.close)
        self.sessions=self.root/'sessions';self.sessions.mkdir();self.index=live.UsageIndex(self.sessions)
        with self.store.tx():self.store.status('RUNNING')

    def operation(self, thread=A, failed=False, saved_thread=True, receipt_usage=None, no_model=False):
        with self.store.tx():
            self.store.db.execute("UPDATE tasks SET status='PENDING' WHERE id=?",(self.store.tasks()[0]['id'],))
        op=ars.reserve_task(self.store,self.store.tasks()[0]);folder=Path(op['directory'])
        receipt=dict(thread_id=thread if saved_thread else None, success=not failed,
                     usage=receipt_usage or {},started_at='2026-11-16T01:00:00+00:00')
        if no_model:receipt['new_model_call']=False
        (folder/'receipt.json').write_text(json.dumps(receipt))
        (folder/'events.jsonl').write_text(json.dumps(dict(type='thread.started',thread_id=thread))+'\n')
        with self.store.tx():
            self.store.db.execute("UPDATE operations SET state='FINALIZED',thread_id=? WHERE id=?",(thread if saved_thread else None,op['id']))
            self.store.db.execute("UPDATE tasks SET status=? WHERE id=?",('FAILED' if failed else 'COMPLETED',op['task_id']))
        return op

    def row(self, rid, thread=A, model='actual-model', amount=100):
        return [dict(type='turn_context',payload=dict(turn_id=rid,model=model)),
                dict(type='token_usage_record',timestamp='2026-11-16T01:00:00Z',payload=dict(
                    response_id=rid,thread_id=thread,turn_id=rid,
                    usage=dict(input_tokens=amount,cached_input_tokens=amount-10,output_tokens=20,reasoning_output_tokens=5)))]

    def session(self, thread=A, rows=None, name=None):
        p=self.sessions/(name or ('rollout-'+thread+'.jsonl'))
        entries=[dict(type='session_meta',payload=dict(id=thread,cwd=str(self.root)))]+(rows or self.row('response',thread))
        p.write_text(''.join(json.dumps(row)+'\n' for row in entries));return p

    def test_failed_call_recovered_from_terminal_thread_and_actual_model(self):
        self.operation(failed=True,saved_thread=False)
        self.session(rows=self.row('a',model='model-a')+self.row('b',model='model-b',amount=200))
        result=live.describe(self.store,self.index)
        self.assertEqual(result['totals']['total_tokens'],340)
        self.assertEqual(result['totals']['cached_input_tokens'],280)
        self.assertEqual({r['model'] for r in result['models']},{'model-a','model-b'})
        self.assertEqual(result['tasks'][0]['usage']['total_tokens'],340)
        self.assertFalse(result['tasks'][0]['attempts'][0]['executor_success'])
        self.assertNotIn('configured-only',{r['model'] for r in result['models']})
        self.assertNotIn('session',json.dumps(result))

    def test_append_is_incremental_partial_lines_wait_and_refresh_does_not_double_count(self):
        self.operation();p=self.session();first=live.describe(self.store,self.index)
        self.assertEqual(first['totals']['total_tokens'],120)
        extra=self.row('new',amount=200)
        with p.open('a') as out:
            out.write(json.dumps(extra[0])+'\n'+json.dumps(extra[1]))
        self.assertEqual(live.describe(self.store,self.index)['totals']['total_tokens'],120)
        with p.open('a') as out:out.write('\n')
        self.assertEqual(live.describe(self.store,self.index)['totals']['total_tokens'],340)
        self.assertEqual(live.describe(self.store,self.index)['totals']['total_tokens'],340)

    def test_retries_are_added_but_copied_response_records_are_not(self):
        self.operation(failed=True);self.operation(thread=B)
        self.session();self.session(name='copy-'+A+'.jsonl')
        self.session(thread=B,rows=self.row('second',thread=B,model='other',amount=200))
        result=live.describe(self.store,self.index)
        self.assertEqual(result['operation_count'],2)
        self.assertEqual(result['request_count'],2)
        self.assertEqual(result['totals']['total_tokens'],340)
        self.assertEqual(result['tasks'][0]['attempt_count'],2)

    def test_unbound_shared_session_is_not_charged_to_a_run(self):
        self.operation();self.session();self.session(thread=B,rows=self.row('other-run',thread=B,amount=9000))
        result=live.describe(self.store,self.index)
        self.assertEqual(result['totals']['total_tokens'],120)
        self.assertEqual(len(result['models']),1)

    def test_missing_is_unknown_and_explicit_no_model_is_zero(self):
        self.operation(failed=True)
        result=live.describe(self.store,self.index)
        self.assertEqual(result['missing_attempts'],1)
        self.assertIsNone(result['tasks'][0]['attempts'][0]['usage'])
        self.operation(thread=B,no_model=True)
        result=live.describe(self.store,self.index)
        self.assertEqual(result['missing_attempts'],1)
        self.assertEqual(result['tasks'][0]['attempts'][1]['usage']['total_tokens'],0)
        self.assertEqual(result['tasks'][0]['attempts'][1]['source'],'no_model_call')

    def test_receipt_fallback_does_not_invent_actual_model(self):
        self.operation(receipt_usage=dict(input_tokens=50,output_tokens=10))
        result=live.describe(self.store,self.index)
        self.assertEqual(result['totals']['total_tokens'],60)
        self.assertEqual(result['models'][0]['model'],'未记录实际模型')
        self.assertEqual(result['models'][0]['basis'],'receipt_only')
        self.assertEqual(result['configured_model'],'configured-only')
        self.assertTrue(result['lower_bound'])

    def test_inflight_calls_and_new_model_files_update_without_redispatch(self):
        op=self.operation();self.session()
        with self.store.tx():
            self.store.db.execute("UPDATE operations SET state='DISPATCHED' WHERE id=?",(op['id'],))
        before=live.describe(self.store,self.index)
        self.assertEqual(before['pending_attempts'],1)
        self.assertEqual(before['totals']['total_tokens'],120)
        self.operation(thread=B);self.session(thread=B,rows=self.row('new-model-call',thread=B,model='new-model',amount=200))
        # Simulate the inventory refresh interval, without sleeping or a model.
        self.index.scanned=0
        after=live.describe(self.store,self.index)
        self.assertEqual(after['totals']['total_tokens'],340)
        self.assertIn('new-model',{r['model'] for r in after['models']})
        self.assertEqual(self.store.state()['calls'],2)

    def test_api_state_and_download_are_run_scoped_and_read_only(self):
        self.operation();self.session()
        class Handler(runtime_web.RuntimeMixin,BaseHTTPRequestHandler):
            def log_message(self,*_):pass
        with patch.object(runtime_web,'campaign_paths',return_value={'EXAMPLE-ALPHA/fixture':self.directory}),patch.object(live,'INDEX',self.index):
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                base='http://127.0.0.1:'+str(server.server_address[1])+'/api/agent/'
                with urlopen(base+'usage?key=EXAMPLE-ALPHA%2Ffixture&download=1') as response:
                    result=json.load(response)
                    self.assertIn('attachment',response.headers['Content-Disposition'])
                self.assertEqual(result['totals']['total_tokens'],120)
                with patch.object(runtime_web.research_delivery,'describe',return_value={}):
                    with urlopen(base+'state?key=EXAMPLE-ALPHA%2Ffixture') as response:state=json.load(response)
                self.assertEqual(state['token_usage']['totals']['total_tokens'],120)
                self.assertEqual(state['tokens'],0)  # Original ledger untouched.
                with self.assertRaises(HTTPError):urlopen(base+'usage?key=EXAMPLE-BETA%2Fother')
                self.assertEqual(self.store.state()['calls'],1)
            finally:server.shutdown();server.server_close();thread.join()

    def test_request_details_bind_actual_models_to_response_ids(self):
        op=self.operation(failed=True)
        self.session(rows=self.row('a',model='model-a')+self.row('b',model='model-b',amount=200))
        report=live.describe(self.store,self.index,include_requests=True)
        self.assertEqual({r['model'] for r in report['requests']},{'model-a','model-b'})
        self.assertEqual({r['response_id'] for r in report['requests']},{'a','b'})
        self.assertEqual({r['operation_id'] for r in report['requests']},{op['id']})
        self.assertEqual(sum(r['usage']['total_tokens'] for r in report['requests']),report['totals']['total_tokens'])
        self.assertNotIn('requests',live.describe(self.store,self.index))

    def test_portfolio_deduplicates_requests_across_registered_runs(self):
        self.operation()
        self.session(rows=self.row('a',model='model-a')+self.row('b',model='model-b',amount=200))
        with patch.object(live,'INDEX',self.index):
            out=live.portfolio({'first':self.directory,'same-run-copy':self.directory})
        self.assertEqual(out['request_count'],2)
        self.assertEqual(out['totals']['total_tokens'],340)
        self.assertEqual({m['model'] for m in out['models']},{'model-a','model-b'})
        self.assertEqual(out['totals']['cached_input_tokens'],280)
        self.assertEqual(out['totals']['reasoning_output_tokens'],10)
        self.assertEqual(out['tasks'][0]['key'],'first')
        self.assertEqual(out['tasks'][0]['usage']['total_tokens'],340)
        self.assertEqual(out['tasks'][0]['attempt_count'],1)
        self.assertEqual(out['tasks'][0]['model_usage'][0]['model'],'model-a')
        self.assertEqual(self.store.state()['tokens'],0)

    def test_portfolio_keeps_missing_unknown_and_receipt_model_unattributed(self):
        self.operation(receipt_usage=dict(input_tokens=50,output_tokens=10))
        self.operation(thread=B)
        with patch.object(live,'INDEX',self.index):out=live.portfolio({'run':self.directory})
        self.assertEqual(out['request_count'],0)
        self.assertEqual(out['receipt_only'],1)
        self.assertEqual(out['missing_attempts'],1)
        self.assertEqual(out['models'][0]['model'],'未记录实际模型')
        self.assertEqual(out['totals']['total_tokens'],60)

    def test_overview_api_exports_models_and_request_details(self):
        self.operation();self.session()
        class Handler(runtime_web.RuntimeMixin,BaseHTTPRequestHandler):
            def log_message(self,*_):pass
        with patch.object(runtime_web,'campaign_paths',return_value={'run':self.directory}),patch.object(live,'INDEX',self.index):
            server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
            try:
                with urlopen(f'http://127.0.0.1:{server.server_port}/api/agent/usage-overview?download=1') as response:
                    out=json.load(response)
                    self.assertIn('attachment',response.headers['Content-Disposition'])
                self.assertEqual(out['request_count'],1)
                self.assertEqual(out['requests'][0]['key'],'run')
                self.assertEqual(out['tasks'][0]['key'],'run')
            finally:server.shutdown();server.server_close();thread.join()


if __name__=='__main__':unittest.main()
