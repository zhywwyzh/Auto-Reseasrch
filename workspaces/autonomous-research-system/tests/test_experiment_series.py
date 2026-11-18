import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import time
from types import SimpleNamespace
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import experiment_series as series


class SeriesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / 'artifacts').mkdir()
        self.path = self.root / 'artifacts/results.json'
        attempts = [dict(world_id='world'+str(i), case_id='case'+str(i), method='method', input_sha256=str(i)) for i in range(3)]
        self.data = dict(topic='TOPIC', executed=True, benchmark_id='new-benchmark',
                         attempt_manifest=attempts, runs=[{**row, 'status':'completed'} for row in attempts])
        self.ref = self.put(self.data)
        self.tasks = [dict(title='新实验', phase='experiment', status='COMPLETED', verification=json.dumps(
            {'sources':[dict(source=str(self.path), sha256=self.ref['sha256'], status='source_match_only')]}))]
        self.store = SimpleNamespace(directory=self.root, tasks=lambda:self.tasks)
        self.state = dict(topic='TOPIC', config={'experiment_observations':{'enabled':True}})
        self.original = dict(summary='旧轮次 2/2', counts={'total':2, 'unknown':1}, metrics=[], warnings=[])

    def put(self, data):
        self.path.write_text(json.dumps(data))
        return {'path':str(self.path), 'sha256':hashlib.sha256(self.path.read_bytes()).hexdigest()}

    def tearDown(self):
        self.temp.cleanup()

    def test_new_verified_result_updates_progress_without_manual_count_registration(self):
        original = copy.deepcopy(self.original)
        out = series.observe(self.store, self.state, self.original)
        self.assertEqual(out['series'][0]['counts']['terminal'],3)
        self.assertIn('3 / 3',out['summary'])
        self.assertFalse(out['series'][0]['scientific_admission_inferred'])
        self.assertIsNone(out['overall_percent'])
        self.assertEqual(self.original,original)

    def test_unknown_failure_and_nonattempt_are_not_success(self):
        self.data['runs'][0]['status']='crashed'
        self.data['runs'][1].update(status='unresolved', individual_cost_unknown=True)
        self.data['runs'][2]['attempted']=False
        out = series.summarize(self.data)
        self.assertEqual(out['counts'],dict(total=3,terminal=1,returned=0,failed=1,unknown=1,pending=1,running=0))
        self.assertFalse(out['execution_complete'])

    def test_missing_records_remain_pending_and_duplicates_rejected(self):
        self.data['runs'].pop()
        self.assertEqual(series.summarize(self.data)['counts']['pending'],1)
        self.data['runs'].append(self.data['runs'][0])
        with self.assertRaises(ValueError):series.summarize(self.data)

    def test_changed_bytes_or_unfinished_task_cannot_promote_counts(self):
        self.path.write_text('{}')
        out = series.observe(self.store,self.state,self.original)
        self.assertNotIn('series',out)
        self.tasks[0]['status']='RUNNING'
        self.assertNotIn('series',series.observe(self.store,self.state,self.original))

    def test_synthetic_or_development_results_rejected(self):
        self.data['synthetic_fixture']=True
        with self.assertRaises(ValueError):series.summarize(self.data)
        self.data.pop('synthetic_fixture');self.data['split']='SCREEN'
        with self.assertRaises(ValueError):series.summarize(self.data)

    def test_symlink_or_cross_topic_or_unregistered_campaign_rejected(self):
        target=self.path.with_name('target.json');self.path.rename(target);self.path.symlink_to(target)
        with self.assertRaises(ValueError):series.read_ledger(self.root,self.ref,'TOPIC')
        self.path.unlink();target.rename(self.path)
        with self.assertRaises(ValueError):series.read_ledger(self.root,self.ref,'OTHER')
        self.state['config']={}
        self.assertIs(series.observe(self.store,self.state,self.original),self.original)

    def test_live_task_status_is_visible_without_changing_recorded_state(self):
        self.state.update(status='READY',progress=dict(current_task={'status':'RUNNING'},activity={'process_alive':True}))
        series.apply_active_status(self.state)
        self.assertEqual(self.state['status'],'RUNNING')
        self.assertEqual(self.state['recorded_status'],'READY')
        self.state.update(status='READY',progress=dict(current_task={'status':'RUNNING'},activity={'process_alive':False}))
        series.apply_active_status(self.state)
        self.assertEqual(self.state['status'],'READY')

    def test_registered_plan_is_not_zero_measured_results_or_a_completed_experiment(self):
        path=self.root/'artifacts/plan.json'
        path.write_text(json.dumps(dict(topic='TOPIC',benchmark_id='new-benchmark',episodes=7)))
        ref=dict(path='artifacts/plan.json',sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 total_field='episodes',label='后续计划',rank=10)
        self.state['config']['experiment_observations']['plans']=[ref]
        self.tasks.clear()
        out=series.observe(self.store,self.state,self.original)
        self.assertTrue(out['series'][0]['planned_only'])
        self.assertNotIn('terminal',out['series'][0]['counts'])
        self.assertIsNone(out['series'][0]['percent'])
        # A smaller result denominator must not silently erase the larger plan.
        self.tasks.append(dict(title='新实验',phase='experiment',status='COMPLETED',verification=json.dumps(
            {'sources':[dict(source=str(self.path),sha256=self.ref['sha256'],status='source_match_only')]})))
        out=series.observe(self.store,self.state,self.original)
        self.assertTrue(out['series'][0]['planned_only'])
        self.assertTrue(any('分母' in warning for warning in out['warnings']))

    def test_live_snapshot_requires_receipt_and_identity_and_does_not_infer_success(self):
        def save(name, data):
            path=self.root/'artifacts'/name
            path.parent.mkdir(exist_ok=True,parents=True)
            path.write_text(json.dumps(data))
            return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
        plan=save('plan.json',dict(topic='TOPIC',benchmark_id='live',episodes=3,physical_worlds=1,policies=['a']))
        plan.update(label='新执行',total_field='episodes',rank=10)
        configuration=save('configuration.json',dict(topic='TOPIC',phase='phase',source_directory='/srv/fixture',
            image_id='image',benchmark_id='live',expected_episodes=3,workers=1))
        snapshot=dict(observed_at=time.time(),phase='phase',guard=dict(phase='phase',topic='TOPIC',
            source='/srv/fixture',image='image',expected_episodes=3),
            lanes={'0':dict(terminals=1,starts=2,status={'expected':3})})
        log=save('log.json',snapshot)
        receipt=save('receipt.json',dict(status='succeeded',exit_code=0,target='worker-host',
            log_path=log['path'],log_sha256=log['sha256']))
        save('observations/latest.json',dict(receipt=receipt,snapshot=snapshot))
        reference=dict(configuration=configuration,plan=plan,target='worker-host',directory='artifacts/observations')
        out=series.read_snapshot(self.root,reference,'TOPIC')
        self.assertEqual(out['counts']['terminal'],1)
        self.assertEqual(out['counts']['open'],1)
        self.assertIsNone(out['counts']['returned'])
        self.assertIsNone(out['counts']['unknown'])
        self.assertFalse(out['execution_complete'])
        Path(log['path']).write_text('{}')
        with self.assertRaises(ValueError):series.read_snapshot(self.root,reference,'TOPIC')


if __name__=='__main__':unittest.main()
