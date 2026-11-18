"""Cross-topic default integration, using future topic IDs and synthetic inputs."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ars
import experiment_monitor as monitor
import platform_features
import runtime_web
import task_trace
import token_usage
import usage_ledger
import execution_visibility


class PlatformDefaultsTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        topics=[]
        for topic,folder in [('FUTURE-A','future-a'),('FUTURE-B','future-b')]:
            workspace=self.root/'workspaces'/folder;workspace.mkdir(parents=True)
            (workspace/'README.md').write_text('SYNTHETIC future topic; no scientific claims.')
            topics.append(dict(id=topic,workspace='workspaces/'+folder,docs='docs/'+folder))
        (self.root/'workspaces/topics.json').write_text(json.dumps({'topics':topics}))
        self.directories=[]

    def create(self,topic='FUTURE-A',backend='codex'):
        directory=ars.create_campaign(topic,'SYNTHETIC generic requirement',repo=self.root,backend=backend,name='future-default',model='synthetic-model')
        self.directories.append(directory)
        return directory

    def test_future_topic_defaults_survive_creation_without_special_configuration(self):
        directory=self.create();store=ars.Store(directory);self.addCleanup(store.close)
        self.assertEqual(store.state()['config']['platform_features'],platform_features.describe())
        self.assertTrue(usage_ledger.read(directory)['updated_at'])
        item=task_trace.save(store,dict(title='Synthetic supplement',instruction='Apply only within existing authorization.',scope='campaign'))['supplement']
        op=ars.reserve_task(store,store.tasks()[0])
        request=json.loads((Path(op['directory'])/'request.json').read_text())
        self.assertEqual(request['context']['user_supplements'][0]['id'],item['id'])
        self.assertTrue(request['context']['platform_features']['request_model_tokens'])
        self.assertEqual(request['context']['execution_visibility']['version'], execution_visibility.VERSION)
        state=ars.public_state(store)
        self.assertTrue(state['tasks'][0]['instruction'])
        self.assertEqual(state['tasks'][0]['execution']['model'],'synthetic-model')
        self.assertEqual(state['supplements'][0]['delivery_status'],'prepared')
        self.assertFalse(state['platform_features']['scientific_authority_changed'])

    def test_unknown_topic_dashboard_works_without_paper_workflow(self):
        directory=self.create();store=ars.Store(directory);self.addCleanup(store.close)
        with store.tx():store.db.execute("UPDATE tasks SET phase='pilot'")
        operation=ars.reserve_task(store,store.tasks()[0])
        task=store.tasks()[0]
        request=json.loads((Path(operation['directory'])/'request.json').read_text())
        self.assertEqual(request['context']['execution_workflow']['experiment_dashboard']['operation_id'],operation['id'])
        self.assertIn('不训练',request['context']['constraints'][2])
        monitor.publish_plan(directory,operation['id'],dict(title='Synthetic read-only progress',objective='Test rendering only',observation=execution_visibility.example(),steps=[dict(id='inspect',label='Inspect synthetic evidence',unit='files',total=None,target_basis='Unknown count')]))
        monitor.publish_status(directory,operation['id'],dict(summary='Inspecting fixture',current_step='inspect',next_action='Report findings',steps=[dict(id='inspect',status='running',detail='Synthetic only')]))
        state=ars.public_state(store)
        observed=monitor.observe(store,state,None)
        self.assertEqual(observed['dashboard']['title'],'Synthetic read-only progress')
        self.assertIsNone(observed['dashboard']['steps'][0]['total'])
        self.assertIn('pilot',{r['phase'] for r in state['progress']['stages']})
        self.assertIsNotNone(monitor.verify(store,task))

    def test_legacy_run_inherits_features_without_rewriting_scientific_configuration(self):
        directory=self.create();store=ars.Store(directory);self.addCleanup(store.close)
        with store.tx():
            config=store.state()['config'];config.pop('platform_features')
            store.db.execute('UPDATE campaign SET config=?',(ars.dump(config),))
        original=store.state()['config']
        before=store.state()['calls']
        context=ars.assemble_context(store,store.tasks()[0])
        state=ars.public_state(store)
        self.assertEqual(context['platform_features'],platform_features.describe())
        self.assertEqual(state['platform_features'],platform_features.describe())
        self.assertEqual(store.state()['config'],original)
        self.assertEqual(store.state()['calls'],before)

    def test_new_topic_registration_drives_discovery_and_isolation(self):
        first=self.create('FUTURE-A');second=self.create('FUTURE-B')
        a=ars.Store(first);b=ars.Store(second);self.addCleanup(a.close);self.addCleanup(b.close)
        task_trace.save(a,dict(title='Only A',instruction='SYNTHETIC A content',scope='campaign'))
        self.assertEqual(task_trace.context(b,b.tasks()[0]),[])
        with patch.object(ars,'REPO',self.root):
            paths=runtime_web.campaign_paths()
        self.assertIn('FUTURE-A/future-default',paths)
        self.assertIn('FUTURE-B/future-default',paths)
        portfolio=token_usage.portfolio(paths)
        self.assertEqual({r['topic'] for r in portfolio['runs']},{'FUTURE-A','FUTURE-B'})
        self.assertEqual(portfolio['request_count'],0)

    def test_new_non_specialized_topic_completes_mock_pipeline_with_usage_persistence(self):
        directory=self.create(backend='mock')
        result=ars.run_campaign(directory)
        self.assertEqual(result['status'],'COMPLETED')
        self.assertTrue(result['platform_features']['executor_identity'])
        self.assertTrue(all(t['instruction'] and t['execution'] for t in result['tasks']))
        persisted=usage_ledger.read(directory)
        self.assertEqual(len(persisted['operations']),4)
        self.assertEqual(persisted['requests'],[])
        self.assertEqual(result['calls'],4)
