import contextlib
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import ars


class RuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'workspaces/autonomous-research-system').mkdir(parents=True)
        (self.root / 'workspaces/autonomous-research-system/README.md').write_text('自动研究系统：这是用于测试的本地来源。\n')
        (self.root / 'AGENTS.md').write_text('保持课题隔离，不得编造研究结论。\n')
        (self.root / 'workspaces/topics.json').write_text(json.dumps({'topics': [{'id':'TR-002','workspace':'workspaces/bearing-swarm-review','docs':'docs/topics/TR-002-bearing-swarm'}]}))
        self.campaigns = []

    def tearDown(self):
        for directory in self.campaigns:
            with contextlib.suppress(Exception):
                s = ars.Store(directory)
                for row in s.db.execute('SELECT directory FROM operations'):
                    ars.stop_activity(row[0])
                s.close()
        self.temp.cleanup()

    def create(self, **kwargs):
        directory = self.root / ('campaign-' + str(len(self.campaigns)))
        out = ars.create_campaign('ARS-DEMO', '检查研究方向与来源', directory=directory, repo=self.root, backend=kwargs.pop('backend','mock'), **kwargs)
        self.campaigns.append(out)
        return out

    def change_config(self, directory, **kwargs):
        s = ars.Store(directory)
        with s.tx():
            config = s.state()['config']; config.update(kwargs)
            s.db.execute('UPDATE campaign SET config=?', (ars.dump(config),))
        s.close()

    def wait(self, predicate, seconds=10):
        until = time.monotonic() + seconds
        while time.monotonic() < until:
            value = predicate()
            if value:
                return value
            time.sleep(.03)
        self.fail('等待运行状态超时')

    def test_full_autonomous_pipeline_and_memory(self):
        directory = self.create()
        result = ars.run_campaign(directory)
        self.assertEqual(result['status'], 'COMPLETED')
        self.assertEqual(result['calls'], 4)
        self.assertEqual([t['phase'] for t in result['tasks']], ['plan','investigate','critic','synthesize'])
        self.assertGreaterEqual(result['memory_count'], 4)
        self.assertIn('不是科学研究结果', (directory/'artifacts/report.md').read_text())

    def test_budget_survives_restart(self):
        d = self.create(max_calls=2)
        self.assertEqual(ars.run_campaign(d)['status'], 'STOPPED_BUDGET')
        ars.resume_campaign(d)
        state = ars.run_campaign(d)
        self.assertEqual(state['calls'], 2)
        self.assertEqual(state['status'], 'STOPPED_BUDGET')

    def test_failed_attempts_count_and_retry_is_bounded(self):
        d = self.create(max_calls=3, max_retries=1)
        self.change_config(d,mock_failures=10)
        state = ars.run_campaign(d)
        self.assertEqual(state['calls'], 3)
        self.assertEqual(state['tasks'][0]['attempt'], 2)
        self.assertEqual(state['tasks'][0]['status'], 'FAILED')

    def test_false_excerpt_is_not_admitted(self):
        d = self.create(max_calls=1,max_retries=0)
        self.change_config(d,mock_invalid=True)
        state = ars.run_campaign(d)
        self.assertEqual(state['tasks'][0]['status'], 'FAILED')
        self.assertEqual(state['memory_count'], 1)
        s=ars.Store(d)
        self.assertIn('摘录',s.db.execute('SELECT text FROM memories').fetchone()[0]);s.close()

    def test_cross_topic_and_symlink_sources_rejected(self):
        d = self.create();s=ars.Store(d)
        p=self.root/'secret.txt';p.write_text('other topic')
        link=self.root/'workspaces/autonomous-research-system/link.txt';link.symlink_to(p)
        for source in (str(p),str(link)):
            with self.assertRaises(ValueError):ars.allowed_source(source,s.state())
        s.close()

    def test_receipt_recovery_and_idempotent_commit(self):
        d=self.create();s=ars.Store(d)
        op=ars.reserve_task(s,s.tasks()[0]);ars.activity(op['directory'])
        self.assertTrue(ars.finalize_operation(s,op))
        self.assertFalse(ars.finalize_operation(s,op))
        self.assertEqual(s.state()['calls'],1);s.close()
        self.assertEqual(ars.run_campaign(d)['calls'],4)

    def test_receipt_after_controller_death_is_recovered(self):
        d=self.create();s=ars.Store(d)
        op=ars.reserve_task(s,s.tasks()[0]);ars.activity(op['directory']);s.close()
        state=ars.run_campaign(d)
        self.assertEqual(state['status'],'COMPLETED')
        self.assertEqual(state['tasks'][0]['attempt'],1)
        self.assertEqual(state['calls'],4)

    def test_unknown_operation_is_not_retried_implicitly(self):
        d=self.create();s=ars.Store(d);op=ars.reserve_task(s,s.tasks()[0]);s.close()
        state=ars.run_campaign(d)
        self.assertEqual(state['status'],'NEEDS_RECONCILIATION')
        self.assertEqual(state['calls'],1)
        ars.resume_campaign(d)
        state=ars.run_campaign(d)
        self.assertEqual(state['calls'],1)
        s=ars.Store(d);ars.resolve_unknown(s,op['id'],'retry');s.close()
        self.assertEqual(ars.run_campaign(d)['calls'],5)

    def test_duplicate_worker_rejected(self):
        d=self.create()
        with (d/'worker.lock').open('a+') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(ValueError):ars.run_campaign(d)
        s=ars.Store(d);self.assertEqual(s.state()['calls'],0);s.close()

    def test_stop_between_reservation_and_dispatch_does_not_call_executor(self):
        d=self.create();s=ars.Store(d);op=ars.reserve_task(s,s.tasks()[0])
        ars.stop_campaign(d)
        self.assertIsNone(ars.dispatch_operation(s,op))
        self.assertEqual(s.operation(op['id'])['state'],'CANCELLED')
        self.assertFalse((Path(op['directory'])/'supervisor.json').exists())
        self.assertEqual(s.state()['calls'],1);s.close()

    def test_stale_fence_rejected(self):
        d=self.create();s=ars.Store(d);op=ars.reserve_task(s,s.tasks()[0]);ars.activity(op['directory'])
        with s.tx():s.db.execute('UPDATE tasks SET fence=fence+1')
        with self.assertRaises(ValueError):ars.finalize_operation(s,op)
        self.assertEqual(s.db.execute('SELECT state FROM operations').fetchone()[0],'RESERVED');s.close()

    def test_real_controller_crash_leaves_activity_recoverable(self):
        d=self.create();self.change_config(d,mock_delay=.4)
        worker=subprocess.Popen([sys.executable,str(HERE/'ars.py'),'run','--campaign',str(d)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def live_operation():
            s=ars.Store(d)
            rows=[dict(x) for x in s.db.execute("SELECT * FROM operations WHERE state='DISPATCHED'")];s.close()
            return rows and (Path(rows[0]['directory'])/'supervisor.json').exists()
        self.wait(live_operation);worker.kill();worker.wait()
        state=ars.run_campaign(d)
        self.assertEqual(state['status'],'COMPLETED');self.assertEqual(state['tasks'][0]['attempt'],1)
        self.assertEqual(state['calls'],4)

    def test_stop_resume_cancels_without_resetting_budget(self):
        d=self.create();self.change_config(d,mock_delay=.6)
        worker=subprocess.Popen([sys.executable,str(HERE/'ars.py'),'run','--campaign',str(d)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def dispatched():
            s=ars.Store(d);out=s.db.execute("SELECT COUNT(*) FROM operations WHERE state='DISPATCHED'").fetchone()[0];s.close();return out
        self.wait(dispatched);ars.stop_campaign(d);worker.wait(timeout=10)
        ars.resume_campaign(d);state=ars.run_campaign(d)
        self.assertEqual(state['status'],'COMPLETED');self.assertEqual(state['calls'],5)

    def test_watchdog_automatically_recovers_killed_controller(self):
        d=self.create();self.change_config(d,mock_delay=.4)
        started=ars.start_campaign(d)
        self.assertTrue(started['started'])
        def dispatched():
            s=ars.Store(d);n=s.db.execute("SELECT COUNT(*) FROM operations WHERE state='DISPATCHED'").fetchone()[0];s.close()
            return n and (d/'worker.json').exists()
        self.wait(dispatched)
        identity=ars.read_json(d/'worker.json');self.assertTrue(ars.same_process(identity))
        os.kill(identity['pid'],signal.SIGKILL)
        def completed():
            s=ars.Store(d);out=s.state()['status'];s.close();return out=='COMPLETED'
        self.wait(completed,15)
        s=ars.Store(d);self.assertEqual(s.state()['calls'],4)
        self.assertEqual(s.tasks()[0]['attempt'],1)
        self.assertEqual(s.db.execute("SELECT COUNT(*) FROM events WHERE type='controller.restarted'").fetchone()[0],1)
        s.close()

    def test_shape_rejects_additional_fields_and_invalid_memory(self):
        d=self.create();s=ars.Store(d);op=ars.reserve_task(s,s.tasks()[0]);ars.activity(op['directory'])
        value=ars.read_json(Path(op['directory'])/'result.json');value['rewrite_goal']='outside scope'
        with self.assertRaises(ValueError):ars.verify_result(value,s.state())
        value.pop('rewrite_goal');value['memories']=[{'kind':'verified_scientific_fact','text':'unverified'}]
        with self.assertRaises(ValueError):ars.verify_result(value,s.state())
        s.close()

    def test_history_import_only_visible_matching_topic_and_deduplicates(self):
        d=self.create();s=ars.Store(d)
        with s.tx():s.db.execute("UPDATE campaign SET topic='TR-002'")
        sessions=self.root/'sessions';sessions.mkdir()
        thread=next(iter(ars.HISTORY_TOPICS['TR-002']))
        records=[{'type':'session_meta','payload':{'cwd':str(self.root),'id':thread}}, {'timestamp':'2026-11-11T00:00:00Z','type':'response_item','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':'先仿真，实机后置'}]}}, {'type':'response_item','payload':{'type':'reasoning','text':'DO_NOT_IMPORT_REASONING'}}, {'type':'response_item','payload':{'type':'message','role':'assistant','content':[{'type':'output_text','text':'DO_NOT_TREAT_AS_FACT'}]}}]
        for name in ('first.jsonl','continuation.jsonl'):(sessions/name).write_text('\n'.join(ars.dump(x) for x in records))
        self.assertEqual(ars.import_history(s,sessions)['imported'],1)
        self.assertEqual(ars.import_history(s,sessions)['imported'],0)
        row=dict(s.db.execute('SELECT * FROM memories').fetchone());self.assertEqual(row['text'],'先仿真，实机后置')
        self.assertEqual(row['status'],'historical_candidate_not_authorization');s.close()

    def test_codex_adapter_with_fake_executable_and_usage(self):
        binary=self.root/'fake-codex'
        binary.write_text('''#!/usr/bin/env python3
import sys,json,pathlib,uuid
prompt=sys.stdin.read();context=json.loads(prompt.split('以下是控制器提供的上下文：\\n',1)[1]);source=context['sources'][0]
out={'status':'done','summary':'adapter result','report':'controlled adapter test, not scientific evidence','verdict':'accept','evidence':[{'kind':'local_file','source':source['path'],'excerpt':source['text'][:20],'locator':'test'}],'memories':[],'next_tasks':[]}
pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(out))
print(json.dumps({'type':'thread.started','thread_id':uuid.uuid4().hex}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':7,'output_tokens':3}}))
''');binary.chmod(0o755)
        d=self.create(backend='codex',codex_bin=str(binary));state=ars.run_campaign(d)
        self.assertEqual(state['status'],'COMPLETED');self.assertEqual(state['tokens'],40)
        s=ars.Store(d);self.assertEqual(s.db.execute('SELECT COUNT(thread_id) FROM operations').fetchone()[0],4);s.close()


if __name__=='__main__':unittest.main(verbosity=2)
