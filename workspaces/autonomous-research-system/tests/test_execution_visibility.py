"""Adaptive defaults on future topic IDs; no model/SSH or real experiments."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import time
import unittest
import subprocess
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ars
import execution_observation
import execution_visibility as visibility
import experiment_jobs as jobs
import experiment_monitor as monitor
import platform_features


class AdaptiveVisibilityTests(unittest.TestCase):
    def setUp(self):
        from test_platform_features import PlatformDefaultsTests
        self.fixture=PlatformDefaultsTests();self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        self.directory=self.fixture.create('FUTURE-A')
        self.store=ars.Store(self.directory);self.addCleanup(self.store.close)
        with self.store.tx():self.store.db.execute("UPDATE tasks SET phase='pilot'")
        self.operation=ars.reserve_task(self.store,self.store.tasks()[0]);self.task=self.store.tasks()[0]
        self.folder=monitor.dashboard_folder(self.directory,self.operation['id'])
        design=visibility.example()
        design.update(kind='synthetic-batch',metrics=[dict(key='fixture_units',label='本协议检查的合成文件',unit='份',total=7,target_basis='本轮合成协议七个输入')])
        self.plan=dict(title='Synthetic seven-file check',objective='No scientific claims',observation=design,
            steps=[dict(id='verify',label='检查合成输入',unit='份',total=7,target_basis='本轮合成协议')])
        self.update=dict(summary='正在读取合成证据',current_step='verify',next_action='独立检查返回值',blocker='',
            steps=[dict(id='verify',status='running',detail='本地合成测试，无服务器或模型调用')])

    def publish(self):
        monitor.publish_plan(self.directory,self.operation['id'],self.plan)
        monitor.publish_status(self.directory,self.operation['id'],self.update)

    def test_new_call_requires_task_designed_sources_and_rules_before_job(self):
        request=json.loads((Path(self.operation['directory'])/'request.json').read_text())
        self.assertEqual(request['context']['execution_visibility']['version'],visibility.VERSION)
        self.assertTrue(request['context']['execution_workflow']['experiment_dashboard']['observation_required'])
        for key in ('sources','state_rules','reconciliation'):
            invalid=copy.deepcopy(self.plan);invalid['observation'].pop(key)
            with self.assertRaises(ValueError):monitor.publish_plan(self.directory,self.operation['id'],invalid)
        invalid=copy.deepcopy(self.plan);invalid.pop('observation')
        with self.assertRaisesRegex(ValueError,'observation'):monitor.publish_plan(self.directory,self.operation['id'],invalid)
        with self.assertRaises(FileNotFoundError):monitor.job_requirement(self.directory/'artifacts/jobs','pilot')
        self.publish()
        self.assertEqual(monitor.job_requirement(self.directory/'artifacts/jobs','pilot')['visibility_version'],visibility.VERSION)
        invalid=copy.deepcopy(self.plan);invalid['observation']['metrics'][0]['total']=3
        with self.assertRaisesRegex(ValueError,'不可覆盖'):monitor.publish_plan(self.directory,self.operation['id'],invalid)

    def test_unknown_requires_explicit_evidence_and_system_action(self):
        self.publish()
        update=copy.deepcopy(self.update);step=update['steps'][0];step['status']='unknown'
        with self.assertRaisesRegex(ValueError,'checks'):monitor.publish_status(self.directory,self.operation['id'],update)
        step['checks']=[dict(what='缺少原命令退出码',evidence='本运行原回执尚未落盘',system_action='系统检查原回执和既有产物，不重投',user_action='无需你手工处理',user_required=False)]
        monitor.publish_status(self.directory,self.operation['id'],update)
        state=ars.public_state(self.store);state['experiment_progress']=monitor.observe(self.store,state,None)
        observation=execution_observation.describe(self.store,state)
        check=next(i for i in observation['issues'] if i['kind']=='task_designed_check')
        self.assertEqual(check['what'],'缺少原命令退出码');self.assertFalse(check['user_required'])
        self.assertEqual(state['experiment_progress']['dashboard']['observation']['kind'],'synthetic-batch')

    def test_erased_or_downgraded_contract_cannot_bypass_gate(self):
        self.publish()
        requirement=self.folder/'requirement.json';data=json.loads(requirement.read_text());requirement.unlink()
        with self.assertRaisesRegex(ValueError,'不能删除'):monitor.job_requirement(self.directory/'artifacts/jobs','pilot')
        with self.assertRaisesRegex(ValueError,'不能删除'):monitor.verify(self.store,self.task)
        data.pop('visibility_version');monitor.write(requirement,data)
        with self.assertRaisesRegex(ValueError,'被降级'):monitor.verify(self.store,self.task)

    def test_new_job_cannot_reuse_stale_status_or_claim_alive_from_pid_only(self):
        self.publish()
        path=self.folder/'status.json';data=json.loads(path.read_text())
        data['updated_at']=execution_observation.stamp(time.time()-180);monitor.write(path,data)
        with self.assertRaisesRegex(ValueError,'过期说明'):
            monitor.job_requirement(self.directory/'artifacts/jobs','pilot')
        monitor.publish_status(self.directory,self.operation['id'],self.update)
        self.assertEqual(monitor.job_requirement(self.directory/'artifacts/jobs','pilot')['operation_id'],self.operation['id'])

    def test_legacy_inflight_call_keeps_contract_and_next_call_gets_new_one(self):
        requirement=self.folder/'requirement.json';data=json.loads(requirement.read_text());data.pop('visibility_version');monitor.write(requirement,data)
        request_path=Path(self.operation['directory'])/'request.json';request=json.loads(request_path.read_text())
        request['context'].pop('execution_visibility');request['context']['execution_workflow']['experiment_dashboard'].pop('observation_required');monitor.write(request_path,request)
        legacy=copy.deepcopy(self.plan);legacy.pop('observation');monitor.publish_plan(self.directory,self.operation['id'],legacy)
        monitor.publish_status(self.directory,self.operation['id'],self.update)
        self.assertIsNotNone(monitor.verify(self.store,self.task))
        self.assertFalse(monitor.prepare(self.store.state(),self.directory,self.task)['observation_required'])
        with self.store.tx():
            self.store.db.execute("UPDATE tasks SET status='COMPLETED' WHERE id=?",(self.task['id'],))
            identity=self.store.add_task('Another synthetic phase','Read synthetic data only','pilot',dedup=False)
        next_task=next(t for t in self.store.tasks() if t['id']==identity)
        operation=ars.reserve_task(self.store,next_task)
        context=json.loads((Path(operation['directory'])/'request.json').read_text())['context']
        self.assertTrue(context['execution_workflow']['experiment_dashboard']['observation_required'])

    def test_generic_local_job_is_scoped_and_readonly_is_not_upgraded(self):
        self.publish();workspace=self.fixture.root/'workspaces/future-a'
        with self.assertRaisesRegex(ValueError,'没有实验作业执行授权'):
            jobs.run_job(self.directory/'artifacts/jobs',['true'],workspace,5,'acceptance')
        # Synthetic saved-authority fixture, no agent call or real experiment.
        with self.store.tx():
            config=self.store.state()['config'];config['workflow']='paper'
            self.store.db.execute('UPDATE campaign SET config=?',(ars.dump(config),))
        command=[sys.executable,'-c','print(\'ARS_PROGRESS={"simulated":false,"counters":{"fixture_units":2}}\')']
        _,receipt=jobs.run_job(self.directory/'artifacts/jobs',command,workspace,5,'acceptance')
        self.assertEqual(receipt['status'],'succeeded')
        self.assertEqual(receipt['dashboard']['operation_id'],self.operation['id'])
        self.assertIn('fixture_units',Path(receipt['log_path']).read_text())
        for cwd,target in [(self.fixture.root/'workspaces/future-b','local'),(workspace,'research-server')]:
            with self.assertRaises(ValueError):jobs.run_job(self.directory/'artifacts/jobs',['true'],cwd,5,'acceptance',target)

    def test_metrics_follow_design_and_other_run_evidence_is_not_carried(self):
        self.publish();root=self.directory/'artifacts/jobs/synthetic';root.mkdir(parents=True)
        console=root/'console.log';console.write_text('ARS_PROGRESS='+json.dumps(dict(at=time.time(),simulated=False,counters=dict(fixture_units=2)))+'\n')
        monitor.write(root/'receipt.json',dict(simulated=False,experiment_kind='pilot',target='research-server',status='running',
            started_at=ars.now(),observed_at=ars.now(),log_path=str(console)))
        execution_observation.inventory.cache_clear()
        state=ars.public_state(self.store);state['experiment_progress']=monitor.observe(self.store,state,None)
        metric=execution_observation.describe(self.store,state)['snapshot']['counters'][0]
        self.assertEqual((metric['label'],metric['unit'],metric['total']),('本协议检查的合成文件','份',7))
        evidence=visibility.context(self.store)['previous_job_evidence'];self.assertEqual(len(evidence),1)
        other=ars.Store(self.fixture.create('FUTURE-B'));self.addCleanup(other.close)
        self.assertEqual(visibility.context(other)['previous_job_evidence'],[])

    def test_fixed_runtime_overlay_injects_latest_visibility_contract(self):
        script='''
import json,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import ars,runtime_entry,execution_visibility
runtime_entry.install(ars.HERE)
store=ars.Store(Path(sys.argv[2]))
try:
 context=ars.assemble_context(store,store.tasks()[0])
 assert context['execution_visibility']['version']==execution_visibility.VERSION
 assert context['execution_workflow']['experiment_dashboard']['observation_required'] is True
 print('fixed runtime visibility: OK')
finally:store.close()
'''
        result=subprocess.run([sys.executable,'-c',script,str(Path(ars.__file__).parent),str(self.directory)],capture_output=True,text=True,timeout=30)
        self.assertEqual(result.returncode,0,result.stderr)
        self.assertIn('fixed runtime visibility: OK',result.stdout)
