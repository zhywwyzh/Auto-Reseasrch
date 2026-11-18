"""User-configured phase routing, immutable dispatch and controlled CLI calls."""
import json
from pathlib import Path
import subprocess
import sys
import unittest
import threading
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from urllib.request import Request,urlopen
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ars
import model_routing as routing
import research_registry
import usage_ledger
import runtime_web

POLICY={'enabled':True,'profiles':{'high':'synthetic-high','standard':'synthetic-medium'}}

class ModelRoutingTests(unittest.TestCase):
    def setUp(self):
        from runtime_fixtures import RuntimeFixtures as RuntimeTests
        self.fixture=RuntimeTests();self.fixture.setUp();self.addCleanup(self.fixture.tearDown)
        self.directory=self.fixture.create(model='synthetic-default',model_policy=POLICY)
        self.store=ars.Store(self.directory);self.addCleanup(self.store.close)

    def test_phase_roles_and_unknown_future_phase_fallback(self):
        cfg=self.store.state()['config']
        for phase in ('resolve','candidate','plan','analyze','write','paper_review','critic'):
            self.assertEqual(routing.select(cfg,dict(id='task',phase=phase))['model'],'synthetic-high')
        for phase in ('implement','code_repair','validate','pilot','experiment','prepare_implementation'):
            self.assertEqual(routing.select(cfg,dict(id='task',phase=phase))['model'],'synthetic-medium')
        self.assertEqual(routing.select(cfg,dict(id='task',phase='future-phase'))['model'],'synthetic-default')

    def test_specific_task_then_phase_then_profile_then_default_priority(self):
        cfg=self.store.state()['config'];cfg['model_policy']={**POLICY,'phase_overrides':{'implement':'phase-model'},'task_overrides':{'one':'task-model'}}
        self.assertEqual(routing.select(cfg,dict(id='one',phase='implement'))['model'],'task-model')
        self.assertEqual(routing.select(cfg,dict(id='two',phase='implement'))['model'],'phase-model')
        cfg['model_policy']['phase_overrides']['implement']=''
        self.assertEqual(routing.select(cfg,dict(id='two',phase='implement'))['model'],'synthetic-medium')
        cfg['model_policy']['profiles']={}
        self.assertEqual(routing.select(cfg,dict(id='two',phase='implement'))['model'],'synthetic-default')
        cfg['model']='';self.assertEqual(routing.select(cfg,dict(id='two',phase='implement'))['model'],'')

    def test_phase_profiles_are_choices_not_fixed_roles(self):
        cfg=self.store.state()['config']
        cfg['model_policy']={**POLICY,'phase_profiles':{'plan':'standard','implement':'high','paper_review':'default'}}
        plan=routing.select(cfg,dict(id='one',phase='plan'))
        self.assertEqual(plan['model'],'synthetic-medium')
        self.assertEqual(plan['recommended_profile'],'high')
        self.assertEqual(plan['profile'],'standard')
        self.assertEqual(routing.select(cfg,dict(id='two',phase='implement'))['model'],'synthetic-high')
        self.assertEqual(routing.select(cfg,dict(id='three',phase='paper_review'))['model'],'synthetic-default')

    def test_custom_phase_requires_model_and_task_override_still_wins(self):
        with self.assertRaisesRegex(ValueError,'必须填写模型'):
            routing.normalize({**POLICY,'phase_profiles':{'plan':'custom'}})
        with self.assertRaises(ValueError):routing.normalize({**POLICY,'phase_profiles':{'plan':'invalid'}})
        cfg=self.store.state()['config']
        cfg['model_policy']={**POLICY,'phase_profiles':{'plan':'custom'},'phase_overrides':{'plan':'third-model'},'task_overrides':{'one':'task-only'}}
        self.assertEqual(routing.select(cfg,dict(id='one',phase='plan'))['model'],'task-only')
        self.assertEqual(routing.select(cfg,dict(id='two',phase='plan'))['model'],'third-model')

    def test_chosen_phase_profile_is_frozen_in_request_and_persisted(self):
        routing.save(self.store,{**POLICY,'phase_profiles':{'plan':'standard'}})
        op=ars.reserve_task(self.store,self.store.tasks()[0])
        path=Path(op['directory'])/'request.json';before=path.read_bytes();request=json.loads(before)
        self.assertEqual(request['config']['model'],'synthetic-medium')
        self.assertEqual(request['model_assignment']['profile'],'standard')
        argv=ars.executor_argv(request,Path('schema.json'),Path('result.json'))
        self.assertEqual(argv[argv.index('--model')+1],'synthetic-medium')
        routing.save(self.store,{**POLICY,'phase_profiles':{'plan':'high'}})
        self.assertEqual(path.read_bytes(),before)
        self.assertEqual(self.store.state()['config']['model_policy']['phase_profiles']['plan'],'high')
        self.assertEqual(ars.public_state(self.store)['tasks'][0]['planned_model']['model'],'synthetic-high')

    def test_save_affects_only_future_reservations_not_inflight_request(self):
        op=ars.reserve_task(self.store,self.store.tasks()[0]);path=Path(op['directory'])/'request.json';original=path.read_bytes()
        calls=self.store.state()['calls'];state=self.store.state()['status']
        receipt=routing.save(self.store,{'enabled':True,'profiles':{'high':'changed-high','standard':'changed-mid'}},'changed-default')
        self.assertIn('下一次',receipt['effective']);self.assertEqual(path.read_bytes(),original)
        self.assertEqual(self.store.state()['calls'],calls);self.assertEqual(self.store.state()['status'],state)
        task=self.store.tasks()[0];self.assertEqual(json.loads(original)['config']['model'],'synthetic-high')
        with self.store.tx():self.store.db.execute("UPDATE tasks SET status='PENDING' WHERE id=?",(task['id'],))
        second=ars.reserve_task(self.store,task)
        self.assertEqual(ars.read_json(Path(second['directory'])/'request.json')['config']['model'],'changed-high')
        public=ars.public_state(self.store)
        self.assertEqual(public['tasks'][0]['planned_model']['model'],'changed-high')
        self.assertEqual(public['tasks'][0]['execution']['model'],'changed-high')

    def test_legacy_single_model_and_invalid_routing_do_not_escalate(self):
        self.assertEqual(routing.select({'model':'legacy'},dict(id='x',phase='paper_review'))['model'],'legacy')
        for invalid in [{'enabled':'yes'},{'enabled':True,'profiles':{'high':'--model=oops'}},{'profiles':{'high':'model x'}},{'phase_overrides':{'unknown':'x'}},{'profiles':{'super':'x'}}]:
            with self.assertRaises(ValueError):routing.normalize(invalid)
        with self.assertRaises(ValueError):routing.save(self.store,{**POLICY,'task_overrides':{'foreign':'model'}})
        self.assertEqual(self.store.state()['config']['model'],'synthetic-default')

    def test_argv_contains_exact_reserved_model_once(self):
        op=ars.reserve_task(self.store,self.store.tasks()[0]);request=ars.read_json(Path(op['directory'])/'request.json')
        args=ars.executor_argv(request,Path('schema.json'),Path('output.json'))
        self.assertEqual(args.count('--model'),1);self.assertEqual(args[args.index('--model')+1],'synthetic-high')
        args=routing.apply_argv(args+['--model=stale'],request)
        self.assertEqual(args.count('--model'),1);self.assertNotIn('--model=stale',args)
        saved=usage_ledger.read(self.directory)
        self.assertEqual(saved['operations'][op['id']]['configured_model'],'synthetic-high')

    def test_actual_local_executor_receives_different_models_by_phase(self):
        binary=self.fixture.root/'controlled-codex'
        binary.write_text('''#!/usr/bin/env python3
import json,pathlib,sys,uuid
prompt=sys.stdin.read();context=json.loads(prompt.split('以下是控制器提供的上下文：\\n',1)[1]);source=context['sources'][0]
model=sys.argv[sys.argv.index('--model')+1]
output=pathlib.Path(sys.argv[sys.argv.index('--output-last-message')+1])
output.with_name('captured-argv.json').write_text(json.dumps(sys.argv))
result={'status':'done','summary':'Synthetic '+model,'report':'Local controlled executor only','verdict':'accept','evidence':[{'kind':'local_file','source':source['path'],'excerpt':source['text'][:20],'locator':'fixture'}],'memories':[],'next_tasks':[]}
output.write_text(json.dumps(result));print(json.dumps({'type':'thread.started','thread_id':str(uuid.uuid4())}));print(json.dumps({'type':'turn.completed','usage':{'input_tokens':7,'output_tokens':3}}))
''');binary.chmod(0o755)
        self.fixture.change_config(self.directory,backend='codex',codex_bin=str(binary))
        captured=[]
        for phase in ('plan','implement','critic'):
            with self.store.tx():
                self.store.db.execute("UPDATE tasks SET status='PENDING',phase=? WHERE id=?",(phase,self.store.tasks()[0]['id']))
            op=ars.reserve_task(self.store,self.store.tasks()[0]);ars.activity(op['directory'])
            args=ars.read_json(Path(op['directory'])/'captured-argv.json');captured.append(args[args.index('--model')+1])
            self.assertTrue(ars.read_json(Path(op['directory'])/'receipt.json')['success'])
        self.assertEqual(captured,['synthetic-high','synthetic-medium','synthetic-high'])

    def test_fixed_legacy_executor_uses_routing_overlay(self):
        script='''
import sys,json
sys.path.insert(0,sys.argv[1]);import ars,runtime_entry
original=ars.reserve_task
def legacy(store,task):
    op=original(store,task)
    path=ars.Path(op['directory'])/'request.json';request=ars.read_json(path)
    request.pop('model_assignment',None);request['config']['model']='stale-model'
    request['context'].pop('model_assignment',None);ars.atomic_json(path,request);return op
ars.reserve_task=legacy
runtime_entry.install(ars.HERE)
s=ars.Store(sys.argv[2])
try:
    op=ars.reserve_task(s,s.tasks()[0]);request=ars.read_json(ars.Path(op['directory'])/'request.json')
    assert request['config']['model']=='synthetic-high'
    assert request['model_assignment']['profile']=='high'
finally:s.close()
'''
        result=subprocess.run([sys.executable,'-c',script,str(ars.HERE),str(self.directory)],capture_output=True,text=True,timeout=20)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_independent_new_research_persists_routing_policy(self):
        result=research_registry.create(dict(title='Synthetic routing study',goal='Inspect synthetic input',creation_id='synthetic-policy-new',backend='mock',model_policy=POLICY),self.fixture.root)
        topic=result['topic'];directory=self.fixture.root/topic['workspace']/'runs/ars'/result['key'].split('/')[1]
        store=ars.Store(directory);self.addCleanup(store.close)
        self.assertEqual(store.state()['config']['model_policy']['profiles']['standard'],'synthetic-medium')
        self.assertEqual(ars.public_state(store)['tasks'][0]['planned_model']['model'],'synthetic-high')
        self.assertEqual(store.state()['calls'],0)

    def test_http_policy_update_on_stopped_run_is_persistent_without_start(self):
        ars.stop_campaign(self.directory)
        before=self.store.state()
        class Handler(runtime_web.RuntimeMixin,BaseHTTPRequestHandler):
            def log_message(self,*a):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch.object(runtime_web,'campaign_paths',return_value={'fixture':self.directory}):
                req=Request(f'http://127.0.0.1:{server.server_port}/api/agent/model-policy',data=json.dumps(dict(key='fixture',policy=POLICY,default_model='changed-base')).encode(),headers={'Content-Type':'application/json','X-ARS-Token':runtime_web.TOKEN})
                response=json.load(urlopen(req))
                self.assertEqual(response['policy']['profiles']['standard'],'synthetic-medium')
            self.assertEqual(self.store.state()['status'],'STOPPED_USER')
            self.assertEqual(self.store.state()['calls'],before['calls'])
            self.assertEqual(self.store.state()['config']['max_calls'],before['config']['max_calls'])
        finally:server.shutdown();server.server_close();thread.join()
