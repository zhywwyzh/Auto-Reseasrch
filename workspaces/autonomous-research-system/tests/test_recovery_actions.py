import json
from pathlib import Path
import sys
import subprocess
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ars
import recovery_actions as actions


class RecoveryActionTests(unittest.TestCase):
    def setUp(self):
        from runtime_fixtures import RuntimeFixtures as RuntimeTests
        self.fixture=RuntimeTests(); self.fixture.setUp(); self.addCleanup(self.fixture.tearDown)
        self.directory=self.fixture.create()
        self.store=ars.Store(self.directory); self.addCleanup(self.store.close)
        task=self.store.tasks()[0]
        self.op=ars.reserve_task(self.store, task)
        with self.store.tx():
            self.store.db.execute("UPDATE tasks SET status='UNKNOWN' WHERE id=?", (task['id'],))
            self.store.db.execute("UPDATE operations SET state='UNKNOWN' WHERE id=?", (self.op['id'],))
            self.store.status('NEEDS_RECONCILIATION', 'Synthetic missing receipt')
        self.task=self.store.tasks()[0]
        self.record=dict(id=ars.uid(),task_id=task['id'],operation_id=self.op['id'],action='recover',label='修复并接续',title=task['title'],state='queued',steps=[])
        actions.root(self.directory).mkdir(parents=True)

    def test_recovery_retains_original_bytes_and_cost_then_queues_same_stage_child(self):
        source=Path(self.op['directory'])/'request.json'; original=source.read_bytes()
        calls=self.store.state()['calls']
        with patch.object(actions,'live_commands',return_value=[]):
            result=actions.recover(self.store,self.task,self.record)
        child=next(t for t in self.store.tasks() if t['id']==result['recovery_task_id'])
        self.assertEqual(child['parent'],self.task['id'])
        self.assertEqual(child['phase'],self.task['phase'])
        self.assertEqual(child['status'],'PENDING')
        self.assertIn('禁止重复提交未知或已完成的实验',child['instruction'])
        self.assertIn('本地Git忽略区',child['instruction'])
        self.assertEqual(source.read_bytes(),original)
        self.assertFalse((source.parent/'receipt.json').exists())
        self.assertEqual(self.store.state()['calls'],calls)
        self.assertEqual(self.store.operation(self.op['id'])['state'],'ABANDONED')
        self.assertEqual(self.store.tasks()[0]['status'],'FAILED')
        self.assertEqual(actions.priority(self.store,child),0)
        self.assertEqual(result['new_experiments_submitted'],0)

    def test_live_original_executor_blocks_recovery_without_mutation(self):
        ars.atomic_json(Path(self.op['directory'])/'child.json',{'pid':123})
        with patch.object(ars,'same_process',return_value=True):
            with self.assertRaisesRegex(ValueError,'仍在运行'):
                actions.recover(self.store,self.task,self.record)
        self.assertEqual(self.store.operation(self.op['id'])['state'],'UNKNOWN')
        self.assertEqual(len(self.store.tasks()),1)

    def test_live_command_blocks_recovery_even_if_agent_is_gone(self):
        with patch.object(actions,'live_commands',return_value=[{'job':'synthetic-receipt','pid':123}]):
            with self.assertRaisesRegex(ValueError,'原命令仍在运行'):
                actions.recover(self.store,self.task,self.record)
        self.assertEqual(self.store.tasks()[0]['status'],'UNKNOWN')

    def test_arrived_receipt_requires_original_acceptance_not_abandonment(self):
        ars.atomic_json(Path(self.op['directory'])/'receipt.json',{'operation_id':self.op['id'],'success':False})
        with self.assertRaisesRegex(ValueError,'原回执已到达'):
            actions.recover(self.store,self.task,self.record)
        self.assertEqual(self.store.operation(self.op['id'])['state'],'UNKNOWN')

    def test_inspect_produces_durable_explanation_without_call_or_state_change(self):
        record=dict(self.record,action='inspect')
        ars.atomic_json(actions.root(self.directory)/(record['id']+'.json'),record)
        calls=self.store.state()['calls']
        with patch.object(actions,'live_commands',return_value=[]):
            actions.work(self.directory,record['id'])
        out=actions.describe(self.store)['history'][0]
        self.assertEqual(out['state'],'completed')
        self.assertIn('receipt.json 尚未生成',out['detail'])
        self.assertEqual(out['result']['new_model_calls'],0)
        self.assertEqual(self.store.state()['calls'],calls)
        self.assertEqual(self.store.tasks()[0]['status'],'UNKNOWN')

    def test_stale_operation_is_rejected_before_launch(self):
        with self.assertRaisesRegex(ValueError,'调用已变化'):
            actions.submit(self.directory,{'action':'recover','task_id':self.task['id'],'operation_id':'stale'})

    def test_duplicate_click_returns_existing_action_without_second_worker(self):
        ars.atomic_json(actions.root(self.directory)/(self.record['id']+'.json'),self.record)
        # Keep the process-launch assertion isolated from Git's own subprocess.
        with patch.object(actions.git_boundary,'validate_state',return_value={}), patch.object(subprocess,'Popen') as launch:
            out=actions.submit(self.directory,{'action':'recover','task_id':self.task['id'],'operation_id':self.op['id']})
        self.assertTrue(out['duplicate'])
        self.assertEqual(out['operation']['id'],self.record['id'])
        launch.assert_not_called()

    def test_user_stop_is_respected_by_queued_repair(self):
        ars.atomic_json(actions.root(self.directory)/(self.record['id']+'.json'),self.record)
        with self.store.tx():self.store.status('STOPPED_USER','Synthetic explicit stop')
        actions.work(self.directory,self.record['id'])
        record=actions.describe(self.store)['history'][0]
        self.assertEqual(record['state'],'failed')
        self.assertIn('明确停止',record['detail'])
        self.assertEqual(self.store.state()['status'],'STOPPED_USER')
        self.assertEqual(self.store.operation(self.op['id'])['state'],'UNKNOWN')

    def test_operation_log_is_allowlisted_and_redacts_error_credentials(self):
        folder=Path(self.op['directory'])
        (folder/'events.jsonl').write_text(json.dumps({'item':{'id':'c','type':'command_execution','status':'failed','command':'python check.py','aggregated_output':'ValueError: bad input','exit_code':1}})+'\n')
        (folder/'stderr.log').write_text('api_key=sk-private-test\n')
        result=actions.operation_log(self.store,self.op['id'])
        self.assertEqual(result['commands'][0]['exit_code'],1)
        self.assertIn('ValueError',result['commands'][0]['output'])
        self.assertNotIn('sk-private',result['stderr'])
        with self.assertRaises(ValueError):actions.operation_log(self.store,'../../secrets')


if __name__=='__main__':unittest.main()
