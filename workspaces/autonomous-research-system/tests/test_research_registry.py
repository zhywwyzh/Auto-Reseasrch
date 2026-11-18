"""Independent-topic creation, boundary enforcement and retry-safe HTTP setup."""
import concurrent.futures
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.request import Request,urlopen

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import ars
import research_registry as registry
import runtime_web
import task_trace
import usage_ledger


class ResearchRegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.repo=Path(self.temp.name)
        self.payload=dict(title='Synthetic independent question',goal='Research only synthetic source evidence.',materials='Synthetic input A; no real equipment granted.',creation_id='synthetic-creation-key',backend='mock')

    def test_creates_real_new_topic_and_run_from_empty_catalog(self):
        out=registry.create(self.payload,self.repo)
        row=out['topic'];self.assertEqual(row['id'],'RS-001')
        self.assertFalse(out['started'])
        workspace=self.repo/row['workspace']
        self.assertEqual((workspace/'initial-materials.md').read_text(),self.payload['materials'])
        store=ars.Store(workspace/'runs/ars'/out['key'].split('/')[1]);self.addCleanup(store.close)
        self.assertEqual(store.state()['status'],'READY')
        self.assertEqual(store.state()['calls'],0)
        self.assertEqual(store.state()['goal'],self.payload['goal'])
        self.assertEqual(store.state()['config']['workflow'],'readonly')
        self.assertTrue(usage_ledger.read(store.directory)['updated_at'])
        context=ars.assemble_context(store,store.tasks()[0])
        self.assertTrue(context['platform_features']['scoped_supplements'])
        self.assertTrue(any('initial-materials.md' in src['text'] for src in context['sources']))
        with patch.object(ars,'REPO',self.repo):
            self.assertIn(out['key'],runtime_web.campaign_paths())

    def test_double_click_is_idempotent_and_content_changes_rejected(self):
        first=registry.create(self.payload,self.repo)
        second=registry.create(self.payload,self.repo)
        self.assertEqual(first['key'],second['key']);self.assertTrue(second['duplicate'])
        self.assertEqual(len(json.loads((self.repo/'workspaces/topics.json').read_text())['topics']),1)
        with self.assertRaises(ValueError):registry.create(dict(self.payload,title='Different request'),self.repo)

    def test_concurrent_new_research_gets_unique_ids_and_isolated_materials(self):
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
            result=list(pool.map(lambda n:registry.create(dict(self.payload,title=f'Synthetic {n}',materials=f'Only topic {n}',creation_id=f'synthetic-key-{n}'),self.repo),range(2)))
        self.assertEqual(len({r['topic']['id'] for r in result}),2)
        self.assertEqual(len({r['topic']['workspace'] for r in result}),2)
        self.assertEqual({(self.repo/r['topic']['workspace']/'initial-materials.md').read_text() for r in result},{'Only topic 0','Only topic 1'})

    def test_validation_failure_does_not_create_topic(self):
        for data in [dict(self.payload,title=''),dict(self.payload,max_calls=-1),dict(self.payload,creation_id='../escape'),dict(self.payload,workspace='public'),dict(self.payload,materials=3)]:
            with self.assertRaises(ValueError):registry.create(data,self.repo)
        self.assertFalse((self.repo/'workspaces/topics.json').exists())

    def test_git_boundary_protects_research_paths_before_writes(self):
        subprocess.run(['git','init','-q',str(self.repo)],check=True)
        (self.repo/'.gitignore').write_text('/workspaces/\n/docs/\n/papers/\n')
        out=registry.create(self.payload,self.repo)
        for path in [self.repo/out['topic']['workspace'],self.repo/out['topic']['docs']]:
            result=subprocess.run(['git','-C',str(self.repo),'check-ignore',str(path)],capture_output=True)
            self.assertEqual(result.returncode,0)
        other=self.repo/'disallowed';other.mkdir()
        subprocess.run(['git','init','-q',str(other)],check=True)
        with self.assertRaisesRegex(ValueError,'Git忽略区'):registry.create(self.payload,other)
        self.assertFalse((other/'workspaces/topics.json').exists())

    def test_initial_run_failure_preserves_registration_and_retries_same_topic(self):
        with patch.object(ars,'create_campaign',side_effect=ValueError('synthetic setup failure')):
            with self.assertRaisesRegex(ValueError,'保留本地内容'):registry.create(self.payload,self.repo)
        rows=json.loads((self.repo/'workspaces/topics.json').read_text())['topics']
        self.assertEqual(rows[0]['registration_status'],'creation_failed')
        out=registry.create(self.payload,self.repo)
        self.assertEqual(out['topic']['id'],rows[0]['id'])
        self.assertEqual(len(json.loads((self.repo/'workspaces/topics.json').read_text())['topics']),1)

    def test_adopts_initial_run_if_catalog_commit_was_interrupted(self):
        out=registry.create(self.payload,self.repo)
        path=self.repo/'workspaces/topics.json';catalog=json.loads(path.read_text())
        catalog['topics'][0].pop('initial_run');catalog['topics'][0]['registration_status']='initializing';path.write_text(json.dumps(catalog))
        again=registry.create(self.payload,self.repo)
        self.assertEqual(again['key'],out['key'])
        self.assertEqual(len(list((self.repo/out['topic']['workspace']/'runs/ars').iterdir())),1)

    def test_http_creates_independent_topic_without_using_existing_id(self):
        class Handler(runtime_web.RuntimeMixin,BaseHTTPRequestHandler):
            def log_message(self,*a):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        try:
            with patch.object(ars,'REPO',self.repo):
                req=Request(f'http://127.0.0.1:{server.server_port}/api/agent/create-research',data=json.dumps(self.payload).encode(),headers={'Content-Type':'application/json','X-ARS-Token':runtime_web.TOKEN})
                with urlopen(req) as response:
                    out=json.load(response);self.assertEqual(response.status,201)
            self.assertTrue(out['key']);self.assertEqual(out['topic']['title'],self.payload['title']);self.assertFalse(out['started'])
        finally:server.shutdown();server.server_close();thread.join()
