"""Synthetic verification lifecycle, live UI data and original gate semantics."""
import json
from pathlib import Path
import sys
import threading
import subprocess
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ars
import execution_observation
import verification_monitor as monitor


class VerificationMonitorTests(unittest.TestCase):
    def setUp(self):
        from test_platform_features import PlatformDefaultsTests
        self.fixture=PlatformDefaultsTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.directory=self.fixture.create('FUTURE-A');self.store=ars.Store(self.directory);self.addCleanup(self.store.close)
        self.operation=ars.reserve_task(self.store,self.store.tasks()[0]);self.task=self.store.tasks()[0]
        self.design=dict(title='Synthetic integrity check',object='Synthetic archive version A',scope='Only fixture members; no scientific claims',
            checks=[dict(id='members',label='逐成员完整性',criterion='按原合成协议校验七个成员'),dict(id='manifest',label='清单与原版本',criterion='原版本绑定')])

    def observe(self,o=None):return monitor.describe(self.store,ars.public_state(self.store),o or dict(jobs=[],previous_jobs=[]))

    def test_future_call_has_tracking_contract_and_live_partial_counts(self):
        request=json.loads((Path(self.operation['directory'])/'request.json').read_text())
        self.assertEqual(request['context']['verification_tracking']['version'],monitor.VERSION)
        session=monitor.plan(self.store,self.operation['id'],self.design)
        monitor.update(self.directory,session['id'],dict(summary='正在检查原成员',next_action='继续剩余成员',
            checks=[dict(id='members',status='running',detail='已读取真实合成成员',evidence='fixture/member-index.json',completed=2,total=7,unit='份')]))
        seen=self.observe()['sessions'][0]
        self.assertEqual((seen['status'],seen['checks'][0]['completed'],seen['checks'][0]['total']),('running',2,7))
        self.assertEqual(seen['authority'],'executor_report');self.assertFalse(seen['scientific_admission_inferred'])
        self.assertEqual(self.store.state()['calls'],1)

    def test_actual_controller_call_is_visible_before_return_and_returns_same_value(self):
        tracker=monitor.ControllerChecks(self.store,self.task,[self.design['checks'][0]])
        entered=threading.Event();release=threading.Event();result={};returned=[]
        def check():entered.set();release.wait(5);return result
        thread=threading.Thread(target=lambda:returned.append(tracker.check('members','逐成员完整性',check)));thread.start()
        try:
            self.assertTrue(entered.wait(5))
            self.assertEqual(monitor.read(self.directory,tracker.data['id'])['checks'][0]['status'],'running')
        finally:release.set();thread.join(5)
        self.assertIs(returned[0],result)
        record=monitor.read(self.directory,tracker.data['id'])
        self.assertEqual(record['checks'][0]['status'],'passed');self.assertIn('SHA256',record['checks'][0]['evidence'])

    def test_failure_is_preserved_and_original_exception_is_not_swallowed(self):
        tracker=monitor.ControllerChecks(self.store,self.task,[self.design['checks'][0]])
        error=ValueError('Synthetic member SHA mismatch')
        def fail():raise error
        with self.assertRaises(ValueError) as caught:tracker.check('members','逐成员完整性',fail)
        self.assertIs(caught.exception,error)
        old=monitor.read(self.directory,tracker.data['id']);self.assertEqual(old['status'],'failed')
        self.assertIn('SHA mismatch',old['checks'][0]['detail'])
        repaired=monitor.ControllerChecks(self.store,self.task,[self.design['checks'][0]])
        repaired.check('members','逐成员完整性',lambda:True)
        self.assertEqual(monitor.read(self.directory,old['id'])['status'],'failed')
        self.assertNotEqual(old['id'],repaired.data['id'])
        self.assertEqual(self.observe()['sessions'][0]['id'],repaired.data['id'])
        self.assertEqual(self.observe()['sessions'][0]['status'],'passed')
        self.assertEqual(self.store.state()['calls'],1)

    def test_observation_failure_cannot_retry_or_change_validator_return(self):
        tracker=monitor.ControllerChecks(self.store,self.task,[self.design['checks'][0]])
        sentinel=object();calls=[]
        with patch.object(monitor,'update',side_effect=OSError('Synthetic monitor disk error')):
            result=tracker.check('members','逐成员完整性',lambda:(calls.append(1),sentinel)[1])
        self.assertIs(result,sentinel);self.assertEqual(calls,[1])

    def test_non_applicable_check_is_skipped_instead_of_claiming_passed(self):
        tracker=monitor.ControllerChecks(self.store,self.task,[self.design['checks'][0]])
        self.assertIsNone(tracker.check('members','不适用的旧契约',lambda:None,skip_if_none=True))
        record=monitor.read(self.directory,tracker.data['id'])
        self.assertEqual(record['status'],'skipped');self.assertEqual(record['checks'][0]['status'],'skipped')

    def test_partial_check_failure_cannot_be_hidden_by_command_exit_zero(self):
        path=self.directory/'artifacts/jobs/verify-one';path.mkdir(parents=True)
        console=path/'console.log'
        row=dict(id='hash',label='逐成员哈希',criterion='原哈希匹配',status='failed',detail='Synthetic mismatch',evidence='fixture/index.json')
        console.write_text('ARS_CHECK='+json.dumps(row)+'\nARS_CHECK={"partial":')
        receipt=path/'receipt.json';receipt.write_text(json.dumps(dict(simulated=False,experiment_kind='acceptance',target='local',status='succeeded',exit_code=0,
            started_at=ars.now(),observed_at=ars.now(),log_path=str(console))))
        job=dict(id=path.name,kind='acceptance',source=str(receipt.relative_to(self.directory)),status='succeeded',reason='命令正常返回',
            started_at=ars.now(),observed_at=ars.now(),operation_scope='current')
        session=self.observe(dict(jobs=[job],previous_jobs=[]))['sessions'][0]
        self.assertEqual(session['status'],'failed');self.assertEqual(session['checks'][0]['status'],'passed')
        self.assertEqual(session['checks'][1]['status'],'failed');self.assertEqual(session['checks'][1]['authority'],'executor_report')

    def test_terminal_failure_cannot_be_overwritten_with_pass_and_missing_evidence_rejected(self):
        session=monitor.plan(self.store,self.operation['id'],self.design)
        row=dict(id='members',status='passed',detail='Checked fixture',evidence='尚未产生')
        with self.assertRaisesRegex(ValueError,'具体证据'):monitor.update(self.directory,session['id'],dict(checks=[row]))
        row.update(status='failed',evidence='fixture/bad.json');monitor.update(self.directory,session['id'],dict(checks=[row]))
        row.update(status='passed')
        with self.assertRaisesRegex(ValueError,'保留原核验终态'):monitor.update(self.directory,session['id'],dict(checks=[row]))

    def test_old_unknown_verification_is_not_silently_green(self):
        with self.store.tx():self.store.db.execute('UPDATE tasks SET verification=?',(ars.dump(dict(executor_diagnostic={})),))
        seen=self.observe()['sessions'][0]
        self.assertEqual(seen['status'],'unknown');self.assertEqual(len(seen['checks']),1)
        self.assertEqual(seen['authority'],'legacy_controller')

    def test_other_topic_and_path_traversal_are_rejected_and_logs_redact_secrets(self):
        other=ars.Store(self.fixture.create('FUTURE-B'));self.addCleanup(other.close)
        with self.assertRaises(ValueError):monitor.plan(other,self.operation['id'],self.design)
        session=monitor.plan(self.store,self.operation['id'],self.design)
        monitor.update(self.directory,session['id'],dict(summary='API_KEY=hidden-key',checks=[dict(id='members',status='running',detail='API_KEY=hidden-detail',evidence='fixture/source')]))
        record=monitor.log(self.directory,session['id'])
        self.assertNotIn('hidden-key',record['text']);self.assertNotIn('hidden-detail',record['text'])
        self.assertEqual(monitor.describe(other,ars.public_state(other),{})['sessions'],[])
        for session_id in ('../private','/tmp/private'):
            with self.assertRaises(ValueError):monitor.log(self.directory,session_id)

    def test_fixed_runtime_records_only_checks_that_apply_to_original_result(self):
        script='''
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import ars,runtime_entry,verification_monitor
runtime_entry.install(ars.HERE)
store=ars.Store(Path(sys.argv[2]))
try:
 result=dict(status='done',verdict='revise',summary='SYNTHETIC fixture',report='Synthetic verification only',evidence=[],memories=[],next_tasks=[])
 ars.verify_task_result(result,store,store.tasks()[0])
 rows=verification_monitor.describe(store,ars.public_state(store),{})['sessions']
 assert rows and all(r['status']=='passed' for r in rows)
 assert all(c['status']=='passed' for r in rows for c in r['checks'])
 print('fixed gate tracking: OK')
finally:store.close()
'''
        output=subprocess.run([sys.executable,'-c',script,str(Path(ars.__file__).parent),str(self.directory)],capture_output=True,text=True,timeout=30)
        self.assertEqual(output.returncode,0,output.stderr)

    def test_log_http_is_bound_to_registered_run_and_does_not_dispatch(self):
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        from urllib.request import urlopen
        from urllib.parse import urlencode
        from urllib.error import HTTPError
        import runtime_web
        session=monitor.plan(self.store,self.operation['id'],self.design)
        monitor.update(self.directory,session['id'],dict(summary='Synthetic source mismatch',checks=[dict(id='members',status='failed',detail='Original synthetic failure',evidence='fixture/index')]))
        other=ars.Store(self.fixture.create('FUTURE-B'));self.addCleanup(other.close)
        class Handler(runtime_web.RuntimeMixin,BaseHTTPRequestHandler):
            def log_message(self,*args):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch.object(runtime_web,'campaign_paths',return_value={'first':self.directory,'other':other.directory}):
                base=f'http://127.0.0.1:{server.server_port}/api/agent/verification-log?'
                result=json.load(urlopen(base+urlencode(dict(key='first',session=session['id']))))
                self.assertIn('Original synthetic failure',result['text'])
                for key,identity in [('other',session['id']),('first','../private')]:
                    with self.assertRaises(HTTPError):urlopen(base+urlencode(dict(key=key,session=identity)))
                self.assertEqual(self.store.state()['calls'],1)
        finally:server.shutdown();server.server_close();thread.join()
