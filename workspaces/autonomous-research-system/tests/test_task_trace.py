import json
from pathlib import Path
import sys
import subprocess
import threading
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ars
import task_trace
import runtime_web


class TaskTraceTests(unittest.TestCase):
    def setUp(self):
        from runtime_fixtures import RuntimeFixtures as RuntimeTests
        self.fixture = RuntimeTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.tearDown)
        self.directory = self.fixture.create()
        self.store = ars.Store(self.directory)
        self.addCleanup(self.store.close)
        self.data = dict(title='Synthetic requirement', instruction='At writing, verify the original experiment source; never invent evidence.', scope='campaign', target='')

    def test_save_is_persistent_idempotent_and_does_not_start_or_add_tasks(self):
        ars.stop_campaign(self.directory)
        before = self.store.state()
        count = len(self.store.tasks())
        first = task_trace.save(self.store, self.data)
        again = task_trace.save(self.store, self.data)
        self.assertFalse(first['duplicate'])
        self.assertTrue(again['duplicate'])
        self.assertEqual(first['supplement']['id'], again['supplement']['id'])
        self.assertEqual(self.store.state()['status'], 'STOPPED_USER')
        self.assertEqual(self.store.state()['calls'], before['calls'])
        self.assertEqual(len(self.store.tasks()), count)
        other = ars.Store(self.directory)
        try: self.assertEqual(task_trace.saved(other)[0]['instruction'], self.data['instruction'])
        finally: other.close()

    def test_scope_and_context_bypass_memory_selection(self):
        task = self.store.tasks()[0]
        global_item = task_trace.save(self.store,self.data)['supplement']
        phase_item = task_trace.save(self.store,dict(self.data,scope='phase',target='write'))['supplement']
        task_item = task_trace.save(self.store,dict(self.data,scope='task',target=task['id']))['supplement']
        with self.store.tx():
            for n in range(70): self.store.memory('decision','unrelated synthetic item '+str(n))
        ctx = ars.assemble_context(self.store,task)
        self.assertEqual({r['id'] for r in ctx['user_supplements']},{global_item['id'],task_item['id']})
        future = dict(task,id='future',phase='write')
        self.assertEqual({r['id'] for r in task_trace.context(self.store,future)}, {global_item['id'],phase_item['id']})
        self.assertEqual(task_trace.context(self.store,dict(task,phase='code_repair')),[])

    def test_invalid_scope_rejected_without_writing(self):
        for data in [dict(self.data,scope='unknown'),dict(self.data,scope='task',target='missing'),dict(self.data,scope='phase',target='missing'),dict(self.data,instruction=''),dict(self.data,instruction=None)]:
            with self.assertRaises(ValueError):task_trace.save(self.store,data)
        self.assertEqual(task_trace.saved(self.store),[])

    def test_legacy_executor_overlay_preserves_dedicated_supplements(self):
        item = task_trace.save(self.store,self.data)['supplement']
        script = '''
import sys
sys.path.insert(0,sys.argv[1])
import ars,runtime_entry
original=ars.assemble_context
def legacy(store,task):
    out=original(store,task)
    out.pop('user_supplements',None)
    return out
ars.assemble_context=legacy
runtime_entry.install(ars.HERE)
s=ars.Store(sys.argv[2])
try:
    context=ars.assemble_context(s,s.tasks()[0])
    assert context['user_supplements'][0]['id']==sys.argv[3]
    assert s.state()['calls']==0
finally:s.close()
'''
        result=subprocess.run([sys.executable,'-c',script,str(ars.HERE),str(self.directory),item['id']],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_legacy_duplicate_memories_show_one_saved_item(self):
        with self.store.tx():
            task_id = self.store.add_task(self.data['title'],self.data['instruction'])
            self.store.memory('decision','用户补充：'+self.data['instruction'],status='user_instruction')
            self.store.memory('decision','用户补充：'+self.data['instruction'],status='user_instruction')
        out = task_trace.describe(self.store,ars.public_state(self.store))
        self.assertEqual(len(out['supplements']),1)
        item = out['supplements'][0]
        self.assertEqual(item['legacy_task_id'],task_id)
        self.assertEqual(item['delivery_status'],'saved')
        self.assertEqual(item['task_status'],'PENDING')

    def test_delivery_requires_exact_request_and_dispatch_evidence(self):
        item = task_trace.save(self.store,self.data)['supplement']
        task = self.store.tasks()[0]
        op = ars.reserve_task(self.store,task)
        out = task_trace.describe(self.store,ars.public_state(self.store))
        self.assertEqual(out['supplements'][0]['delivery_status'],'prepared')
        with self.store.tx(): self.store.event('operation.dispatched',{'operation_id':op['id']})
        out = task_trace.describe(self.store,ars.public_state(self.store))
        self.assertEqual(out['supplements'][0]['delivery_status'],'dispatched')
        self.assertEqual(out['tasks'][0]['instruction'],task['instruction'])
        self.assertEqual(out['tasks'][0]['execution']['backend'],'mock')
        path = Path(op['directory'])/'request.json'
        request = json.loads(path.read_text())
        request['context']['user_supplements'][0]['instruction']='altered after save'
        ars.atomic_json(path,request)
        out = task_trace.describe(self.store,ars.public_state(self.store))
        self.assertEqual(out['supplements'][0]['delivery_status'],'saved')
        self.assertEqual(out['supplements'][0]['sha256'],item['sha256'])

    def test_request_identity_uses_actual_configuration_not_latest_setting(self):
        task = self.store.tasks()[0]
        op = ars.reserve_task(self.store,task)
        self.fixture.change_config(self.directory,backend='codex',model='different-later-model')
        out = task_trace.describe(self.store,ars.public_state(self.store))
        self.assertEqual(out['tasks'][0]['execution']['backend'],'mock')
        self.assertEqual(out['tasks'][0]['execution']['identity_source'],'request')
        self.assertFalse(out['tasks'][0]['execution']['process_alive'])

    def test_unknown_call_explains_missing_receipt_empty_result_and_process(self):
        task = self.store.tasks()[0]
        op = ars.reserve_task(self.store,task)
        (Path(op['directory'])/'result.json').write_text('')
        with self.store.tx():
            self.store.db.execute("UPDATE operations SET state='UNKNOWN' WHERE id=?",(op['id'],))
            self.store.db.execute("UPDATE tasks SET status='UNKNOWN' WHERE id=?",(task['id'],))
        out = task_trace.describe(self.store,ars.public_state(self.store))
        check = out['tasks'][0]['execution']['reconciliation']
        self.assertIn('receipt.json 尚未生成',check['summary'])
        self.assertIn('result.json 为空',check['summary'])
        self.assertFalse(check['process_alive'])
        self.assertEqual([r['state'] for r in check['checks']],['missing','missing','unconfirmed'])
        self.assertEqual(self.store.tasks()[0]['status'],'UNKNOWN')
        self.assertFalse((Path(op['directory'])/'receipt.json').exists())

    def test_recorded_failure_is_evidence_not_successful_acceptance(self):
        task = self.store.tasks()[0]
        op = ars.reserve_task(self.store,task)
        receipt = {'operation_id':op['id'],'success':False,'error':'synthetic failure'}
        ars.atomic_json(Path(op['directory'])/'result.json',{'status':'done'})
        check = task_trace.reconciliation(self.store,op,receipt,{}, {})
        self.assertEqual(check['checks'][0]['state'],'recorded')
        self.assertIn('失败',check['checks'][0]['detail'])
        self.assertIn('尚待控制器验收',check['checks'][1]['detail'])
        self.assertEqual(self.store.tasks()[0]['status'],'RUNNING')

    def test_unknown_call_is_current_ahead_of_older_blocked_task(self):
        old = self.store.tasks()[0]
        with self.store.tx():
            self.store.db.execute("UPDATE tasks SET status='BLOCKED' WHERE id=?",(old['id'],))
            current = self.store.add_task('Synthetic missing receipt','Reconcile original call','investigate')
            self.store.db.execute("UPDATE tasks SET status='UNKNOWN' WHERE id=?",(current,))
        self.assertEqual(ars.public_state(self.store)['progress']['current_task']['id'],current)

    def test_http_save_returns_durable_receipt_without_starting_task(self):
        class Handler(runtime_web.RuntimeMixin, BaseHTTPRequestHandler):
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch.object(runtime_web,'campaign_paths',return_value={'fixture':self.directory}):
                url=f'http://127.0.0.1:{server.server_port}/api/agent/supplement'
                body=json.dumps(dict(self.data,key='fixture')).encode()
                request=Request(url,data=body,headers={'Content-Type':'application/json','X-ARS-Token':runtime_web.TOKEN})
                result=json.load(urlopen(request))
                self.assertEqual(result['supplement']['instruction'],self.data['instruction'])
                self.assertEqual(self.store.state()['calls'],0)
                self.assertEqual(task_trace.saved(self.store)[0]['id'],result['supplement']['id'])
        finally:server.shutdown();server.server_close();thread.join()
