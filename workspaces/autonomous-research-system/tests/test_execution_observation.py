"""Synthetic log observability and uncertainty explanation; no remote calls."""
import json
from pathlib import Path
import sys
import threading
import time
import unittest
from unittest.mock import patch
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from urllib.request import urlopen
from urllib.error import HTTPError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ars
import execution_observation as observe
import runtime_web


class ExecutionObservationTests(unittest.TestCase):
    def setUp(self):
        from runtime_fixtures import RuntimeFixtures as RuntimeTests
        self.fixture=RuntimeTests();self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.directory=self.fixture.create()
        self.store=ars.Store(self.directory);self.addCleanup(self.store.close)
        self.operation=ars.reserve_task(self.store,self.store.tasks()[0])
        self.job=self.directory/'artifacts/jobs/synthetic-one';self.job.mkdir(parents=True)
        self.console=self.job/'console.log';self.console.write_text('Starting synthetic fixture\n')
        self.receipt=self.job/'receipt.json';self.reference=str(self.receipt.relative_to(self.directory))
        self.data=dict(status='running',simulated=False,experiment_kind='pilot',target='research-server',started_at=ars.now(),observed_at=ars.now(),log_path=str(self.console),exit_code=None)
        self.save()
        observe.inventory.cache_clear()
    def save(self):self.receipt.write_text(json.dumps(self.data))
    def state(self):
        s=ars.public_state(self.store)
        s['experiment_progress']={'dashboard':{'mode':'stale'}}
        return s

    def test_structured_console_counts_are_visible_without_fake_percentage(self):
        item=dict(at=time.time(),simulated=False,scope='synthetic',counters=dict(environment_steps=123,optimizer_calls=4),sources=[dict(identity='seed-A',snapshot=dict(counters=dict(optimizer_calls=4),updated_at=time.time()))])
        self.console.write_text('AGGREGATE_PROGRESS='+json.dumps(item)+'\nAGGREGATE_PROGRESS={"unfinished":')
        before=self.store.state()['calls']
        result=observe.describe(self.store,self.state())
        self.assertEqual(result['snapshot']['counters'][0]['value'],123)
        self.assertEqual(result['snapshot']['workers'][0]['identity'],'seed-A')
        self.assertNotIn('percent',result['snapshot'])
        self.assertFalse(result['user_required'])
        self.assertEqual(self.store.state()['calls'],before)

    def test_unknown_agent_explains_exact_missing_receipt_without_manual_resolve(self):
        with self.store.tx():
            self.store.db.execute("UPDATE tasks SET status='UNKNOWN' WHERE id=?",(self.operation['task_id'],))
            self.store.db.execute("UPDATE operations SET state='UNKNOWN' WHERE id=?",(self.operation['id'],))
        result=observe.describe(self.store,self.state())
        issue=next(i for i in result['issues'] if i['kind']=='agent_receipt')
        self.assertIn('最终回执',issue['subject'])
        self.assertFalse(issue['user_required'])
        self.assertIn('由系统',issue['user_action'])
        self.assertFalse(result['agent']['receipt_present'])

    def test_stale_job_and_failed_job_are_explained_separately(self):
        self.data['observed_at']=observe.stamp(time.time()-100);self.save()
        result=observe.describe(self.store,self.state())
        self.assertEqual(result['jobs'][0]['status'],'unknown')
        self.assertIn('未更新',result['jobs'][0]['reason'])
        self.data.update(status='failed',exit_code=7,error='synthetic import failure');self.save()
        result=observe.describe(self.store,self.state())
        self.assertEqual(result['jobs'][0]['exit_code'],7)
        self.assertIn('synthetic import failure',result['jobs'][0]['reason'])

    def test_local_console_cannot_be_misrepresented_as_server_counts(self):
        self.data['target']='local';self.save()
        self.console.write_text('ARS_PROGRESS='+json.dumps(dict(simulated=False,at=time.time(),counters=dict(completed=3)))+'\n')
        self.assertIsNone(observe.describe(self.store,self.state())['snapshot'])

    def test_stale_local_receipt_uses_process_identity_without_claiming_remote_state(self):
        self.data.update(target='local',observed_at=observe.stamp(time.time()-100),
                         child_process=dict(pid=12345,start_ticks='1',pgid=12345));self.save()
        with patch.object(ars,'same_process',return_value=False):
            job=observe.describe(self.store,self.state())['jobs'][0]
        self.assertFalse(job['process_alive'])
        self.assertIn('原本地子进程已退出',job['reason'])
        self.assertNotIn('远端',job['reason'])
        with patch.object(ars,'same_process',return_value=True):
            job=observe.describe(self.store,self.state())['jobs'][0]
        self.assertTrue(job['process_alive'])
        self.assertEqual(job['status'],'unknown')
        self.assertIn('回执采集未更新',job['reason'])
        import os
        self.data.pop('child_process');self.data['pid']=os.getpid();self.save()
        with patch.object(ars,'same_process',side_effect=AssertionError('Never trust PID only')):
            job=observe.describe(self.store,self.state())['jobs'][0]
        self.assertIsNone(job['process_alive'])
        self.data['pid']=999999999;self.save()
        self.assertFalse(observe.describe(self.store,self.state())['jobs'][0]['process_alive'])

    def test_previous_operation_logs_remain_available_without_becoming_current_counts(self):
        self.data['started_at']=observe.stamp(time.time()-1000);self.save()
        self.console.write_text('ARS_PROGRESS='+json.dumps(dict(simulated=False,at=time.time(),counters=dict(environment_steps=42)))+'\n')
        result=observe.describe(self.store,self.state())
        self.assertEqual(result['jobs'],[])
        self.assertEqual(result['previous_jobs'][0]['source'],self.reference)
        self.assertEqual(result['previous_jobs'][0]['operation_scope'],'previous')
        self.assertIsNone(result['snapshot'])
        self.assertIn('ARS_PROGRESS=',observe.log(self.directory,self.reference)['text'])

    def test_historical_failure_is_not_presented_as_current_stop(self):
        self.data.update(status='failed',exit_code=9);self.save()
        issue=next(i for i in observe.describe(self.store,self.state())['issues'] if i['kind']=='historical_failure')
        self.assertIn('历史失败',issue['system_action'])
        self.assertFalse(issue['user_required'])

    def test_observation_is_available_for_non_preconfigured_topics(self):
        with self.store.tx():
            self.store.db.execute("UPDATE campaign SET topic='RS-SYNTHETIC-OBSERVATION'")
        self.console.write_text('ARS_PROGRESS='+json.dumps(dict(simulated=False,at=time.time(),counters=dict(environment_steps=27)))+'\n')
        result=observe.describe(self.store,self.state())
        self.assertEqual(result['snapshot']['counters'][0]['value'],27)
        self.assertEqual(result['jobs'][0]['source'],self.reference)

    def test_only_public_agent_messages_are_exposed(self):
        p=Path(self.operation['directory'])/'events.jsonl'
        p.write_text('\n'.join(json.dumps(e) for e in [dict(item=dict(type='reasoning',text='PRIVATE_REASONING')),dict(item=dict(type='agent_message',text='Public current progress'))])+'\n')
        result=observe.describe(self.store,self.state())
        self.assertEqual(result['agent_messages'][0]['text'],'Public current progress')
        self.assertNotIn('PRIVATE_REASONING',json.dumps(result))

    def test_log_tail_is_bounded_redacted_and_cannot_escape_receipt_binding(self):
        path='artifacts/closed-task-readonly-diagnosis/jobs/console.log'
        self.assertEqual(observe.redact(path),path)
        self.assertNotIn('sk-secret-key',observe.redact('Bearer sk-secret-key'))
        self.console.write_text(('old line\n'*20000)+'API_KEY=hidden-value\n{"password": "hidden-password"}\n--token hidden-token\nlast useful line\n')
        result=observe.log(self.directory,self.reference)
        self.assertTrue(result['truncated']);self.assertIn('last useful line',result['text'])
        for secret in ('hidden-value','hidden-password','hidden-token'):self.assertNotIn(secret,result['text'])
        for reference in ('../receipt.json','operations/x/request.json',str(self.receipt)):
            with self.assertRaises(ValueError):observe.log(self.directory,reference)
        self.data['log_path']=str(self.directory/'private.txt');self.save()
        with self.assertRaises(ValueError):observe.log(self.directory,self.reference)
        self.data['log_path']=str(self.console);self.save()
        target=self.job/'original.log';self.console.rename(target);self.console.symlink_to(target)
        with self.assertRaises(ValueError):observe.log(self.directory,self.reference)

    def test_unknown_task_takes_precedence_over_historical_blocker(self):
        with self.store.tx():
            self.store.db.execute("UPDATE tasks SET status='BLOCKED' WHERE id=?",(self.operation['task_id'],))
            unknown=self.store.add_task('Synthetic missing-call task','Read original evidence only',dedup=False)
            self.store.db.execute("UPDATE tasks SET status='UNKNOWN' WHERE id=?",(unknown,))
        self.assertEqual(ars.public_state(self.store)['progress']['current_task']['id'],unknown)

    def test_http_job_log_reads_only_matching_run_artifact(self):
        class Handler(runtime_web.RuntimeMixin,BaseHTTPRequestHandler):
            def log_message(self,*a):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            from urllib.parse import urlencode
            with patch.object(runtime_web,'campaign_paths',return_value={'future':self.directory}):
                base=f'http://127.0.0.1:{server.server_port}/api/agent/job-log?'
                result=json.load(urlopen(base+urlencode(dict(key='future',job=self.reference))))
                self.assertIn('Starting synthetic fixture',result['text'])
                for key,job in [('other',self.reference),('future','../private')]:
                    with self.assertRaises(HTTPError):urlopen(base+urlencode(dict(key=key,job=job)))
        finally:server.shutdown();server.server_close();thread.join()
