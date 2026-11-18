"""Synthetic local revision contracts, not manuscript/scientific validation."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import ars
import paper_workflow as paper


class RevisionWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.repo = Path(self.temp.name); self.workspace = self.repo/'workspaces/example-revision'
        self.workspace.mkdir(parents=True)
        info = {'id':'RS-714', 'workspace':'workspaces/example-revision',
                'docs':'docs/topics/example-revision', 'paper_reserved':'papers/example-revision'}
        (self.repo/'workspaces/topics.json').write_text(json.dumps({'topics':[info]}))
        self.validator=self.workspace/'validate.py'
        self.validator.write_text('import json\nprint(json.dumps({"passed": True, "scope":"synthetic"}))\n')
        self.spec=self.workspace/'contract.json'
        self.spec.write_text(json.dumps({'version':'artifact-revision-v1', 'topic':'RS-714',
            'paper_root':'papers/example-revision/draft', 'validator':str(self.validator),
            'constraints':'Synthetic revision only; no experiments.',
            'stages':[{'phase':p,'title':p,'instruction':'Synthetic artifact '+p,'roles':['record']}
                      for p in ['resolve','investigate','write','paper_review']]}))

    def campaign(self, **kw):
        directory=ars.create_campaign('RS-714','Synthetic revision',repo=self.repo,workflow='paper',
            revision_spec=self.spec,name='fixture',**kw)
        store=ars.Store(directory);self.addCleanup(store.close);return store

    def manifest(self, store, phase):
        path=store.directory/'artifacts'/(phase+'.json');path.write_text('{"synthetic":true}')
        manifest=paper.manifest_path(store.directory,phase);manifest.parent.mkdir(exist_ok=True)
        manifest.write_text(json.dumps({'topic':'RS-714','stage':phase,'status':'passed','artifacts':[
            {'role':'record','path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}]}))
        return manifest,path

    def test_custom_topic_full_stage_chain_and_scope(self):
        store=self.campaign()
        self.assertNotIn('research_quality',store.state()['config'])
        self.assertNotIn('UCS',str(store.state()['constraints']))
        for phase in ['resolve','investigate','write','paper_review']:
            task=store.tasks()[-1];self.assertEqual(task['phase'],phase)
            context=paper.context(store.state(),store.directory,phase)
            self.assertIn(str(self.repo/'papers/example-revision/draft'),context['write_scope'])
            with self.assertRaises(FileNotFoundError):paper.verify_stage(store.state(),store.directory,phase)
            self.manifest(store,phase)
            check=paper.verify_stage(store.state(),store.directory,phase)
            result=dict(status='done',verdict='accept',summary='Synthetic only',report='Fixture',evidence=[],memories=[],next_tasks=[])
            with store.tx():ars.accept_task_result(store,task,'synthetic',result,{'stage_artifacts':check})
            paper.advance(store)
        self.assertEqual(store.state()['status'],'COMPLETED')

    def test_frozen_validator_and_artifact_tampering_rejected(self):
        store=self.campaign();manifest,path=self.manifest(store,'resolve')
        path.write_text('changed')
        with self.assertRaisesRegex(ValueError,'哈希'):paper.verify_stage(store.state(),store.directory,'resolve')
        self.manifest(store,'resolve');self.validator.write_text('print("changed")')
        with self.assertRaisesRegex(ValueError,'验收器已改变'):paper.verify_stage(store.state(),store.directory,'resolve')

    def test_validator_failure_and_other_topic_artifact_rejected(self):
        self.validator.write_text('import sys\nsys.exit("synthetic validator failure")')
        store=self.campaign();manifest,path=self.manifest(store,'resolve')
        with self.assertRaisesRegex(ValueError,'synthetic validator failure'):paper.verify_stage(store.state(),store.directory,'resolve')
        outside=self.repo/'papers/another/payload.json';outside.parent.mkdir(parents=True);outside.write_text('{}')
        data=json.loads(manifest.read_text());data['artifacts'][0].update(path=str(outside),sha256=hashlib.sha256(outside.read_bytes()).hexdigest());manifest.write_text(json.dumps(data))
        with self.assertRaisesRegex(ValueError,'范围'):paper.verify_stage(store.state(),store.directory,'resolve')

    def test_explicit_write_authorization_required(self):
        with self.assertRaises(ValueError):ars.create_campaign('RS-714','Synthetic',repo=self.repo,revision_spec=self.spec)
        with self.assertRaises(ValueError):self.campaign(backend='mock')
        directory=ars.create_campaign('RS-714','Read-only fixture',repo=self.repo,name='read')
        store=ars.Store(directory);self.addCleanup(store.close)
        self.assertFalse(paper.enabled(store.state()['config']))


if __name__=='__main__':unittest.main()
