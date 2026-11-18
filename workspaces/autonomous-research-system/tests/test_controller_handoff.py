"""Synthetic controller-owned repair through the ordinary campaign worker."""
import json
from pathlib import Path
import sys
import textwrap

from runtime_fixtures import RuntimeFixtures
import ars
import code_repair


ORIGINAL = """def check(rows):
    for entry in rows:
        if entry.get('status') not in ('succeeded', 'invalid'):
            raise ValueError('terminal')
        if entry['status'] != 'succeeded':
            if not entry.get('reason'):
                raise ValueError('reason')
            continue
        if entry['score'] < 0:
            raise ValueError('score')
"""
GUARD = (" and not (entry.get('status') == 'failed' and entry.get('reason') and "
         "entry.get('failure_class') == 'scientific_outcome' and entry.get('attempted') is not False)")
FIXED = ORIGINAL.replace("'invalid'):", "'invalid')" + GUARD + ":")


class ControllerHandoffTests(RuntimeFixtures):
    def setUp(self):
        super().setUp()
        topic = dict(id='EXAMPLE-TRANSFER', workspace='workspaces/example', docs='docs/example')
        (self.root/'workspaces/topics.json').write_text(json.dumps({'topics': [topic]}))
        (self.root/topic['workspace']).mkdir()
        system = self.root/'workspaces/autonomous-research-system'
        self.source = system/'synthetic_profile.py'
        self.source.write_text(ORIGINAL)
        self.cli = self.root/'fixture-cli'
        self.directory = ars.create_campaign(topic['id'], 'Synthetic saved-result revalidation',
            repo=self.root, backend='codex', codex_bin=str(self.cli))
        self.campaigns.append(self.directory)
        self.store = ars.Store(self.directory)
        self.addCleanup(self.store.close)
        with self.store.tx():
            self.store.db.execute("UPDATE tasks SET phase='synthesize'")
        self.artifact = self.directory/'artifacts/controller-handoff.json'
        self.artifact.write_text(json.dumps(dict(blocker_kind='controller_write_scope_required',
            target=str(self.source), expected_current_source_sha256=code_repair.digest(self.source))))
        self.blocked = dict(status='blocked', verdict='unresolved', report='Fixture contract conflict',
            summary='Controller must apply a compatibility change', next_tasks=[], memories=[],
            evidence=[dict(kind='local_file', source=str(self.artifact), excerpt='controller_write_scope_required', locator='blocker_kind')])

    def test_background_worker_dispatches_and_resumes_original(self):
        (self.source.parent/'tests').mkdir()
        (self.source.parent/'tests/test_domain.py').write_text(textwrap.dedent("""
            import unittest, sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
            from synthetic_profile import check
            class Frozen(unittest.TestCase):
                def test_recorded_failure(self):
                    check([dict(status='failed', reason='recorded', failure_class='scientific_outcome')])
                def test_unknown_rejected(self):
                    with self.assertRaises(ValueError):
                        check([dict(status='unknown')])
        """))
        self.cli.write_text('#!'+sys.executable+'\n'+textwrap.dedent(f"""
            import json, sys, runpy
            from pathlib import Path
            if '--version' in sys.argv:
                print('fixture'); sys.exit()
            ctx = json.loads(sys.stdin.read().split('以下是控制器提供的上下文：\\n',1)[1])
            out = dict(status='done', verdict='accept', report='Synthetic verification', summary='Verified',
                       evidence=[], memories=[], next_tasks=[])
            if ctx['task']['phase']=='code_repair':
                saved=ctx['code_repair']
                (Path(saved['candidate'])/saved['handoff']['target']).write_text({FIXED!r})
            else:
                try:
                    runpy.run_path({str(self.source)!r})['check']([dict(status='failed', reason='recorded',
                        failure_class='scientific_outcome')])
                except ValueError:
                    out={self.blocked!r}
            Path(sys.argv[sys.argv.index('--output-last-message')+1]).write_text(json.dumps(out))
            print(json.dumps(dict(type='turn.completed', usage={{}})))
        """))
        self.cli.chmod(0o700)
        result = ars.run_campaign(self.directory)
        self.assertEqual(result['status'], 'COMPLETED', result['reason'])
        self.assertEqual(result['calls'], 3)
        task, repair = self.store.tasks()
        self.assertEqual((task['attempt'], repair['phase']), (2, 'code_repair'))
        record = json.loads(repair['verification'])['code_repair']
        self.assertEqual(len(record['changes']), 1)
        self.assertEqual(len(record['tests']), 2)
        self.assertFalse(record['original_stage_accepted'])
        self.assertEqual(self.source.read_text(), FIXED)

    def test_handoff_scope_and_digest(self):
        verification = ars.verify_result(self.blocked, self.store.state())
        task = dict(verification=json.dumps(verification))
        self.assertIsNotNone(code_repair.controller_handoff(self.store, task))
        self.source.write_text(ORIGINAL+'\n')
        self.assertIsNone(code_repair.controller_handoff(self.store, task))
        self.source.write_text(ORIGINAL)
        self.artifact.write_text(self.artifact.read_text()+'\n')
        self.assertIsNone(code_repair.controller_handoff(self.store, task))
        outside = self.root/'controller-handoff.json'
        outside.write_bytes(self.artifact.read_bytes())
        verification['sources'][0].update(source=str(outside), sha256=code_repair.digest(outside))
        self.assertIsNone(code_repair.controller_handoff(self.store, dict(verification=json.dumps(verification))))

    def test_legacy_cited_patch_is_routed_before_readonly_retry(self):
        path = self.artifact.with_name('compatibility.patch')
        path.write_text('--- '+str(self.source)+'\n+++ '+str(self.source)+'\n@@ -1 +1 @@\n-a\n+b\n')
        self.blocked['summary'] = 'schema mismatch'
        self.blocked['evidence'][0].update(source=str(path), excerpt='@@ -1 +1 @@')
        verification = ars.verify_result(self.blocked, self.store.state())
        with self.store.tx():
            self.store.db.execute("UPDATE tasks SET status='BLOCKED', result=?, verification=?",
                (ars.dump(self.blocked), ars.dump(verification)))
            self.store.status('RUNNING')
        ars.advance(self.store)
        task = self.store.tasks()[-1]
        self.assertEqual(task['phase'], 'code_repair')
        handoff = code_repair.session(self.store, task['id'])['handoff']
        self.assertEqual(handoff['evidence_sha256'], code_repair.digest(path))
        self.assertFalse(code_repair.maybe_queue(self.store))

    def test_diagnosed_defect_leaves_diagnosis_even_without_new_file(self):
        task = self.store.tasks()[0]
        self.blocked['summary'] = '已有兼容补丁，执行器仍然无法修复'
        with self.store.tx():
            self.store.db.execute("UPDATE tasks SET status='BLOCKED', result=?, verification=?",
                (ars.dump(self.blocked), ars.dump({})))
            self.store.status('RUNNING')
            self.store.event('self_repair.queued', dict(task_id=task['id'], category='unclassified'))
            self.assertTrue(code_repair.maybe_queue(self.store))
        repair = self.store.tasks()[-1]
        self.assertEqual(code_repair.session(self.store, repair['id'])['category'], 'diagnosed_implementation')
        self.assertFalse(code_repair.repaired_since_diagnosis(self.store, task))
        with self.store.tx():
            self.store.event('code_repair.verified', dict(failed_task=task['id']))
        self.assertTrue(code_repair.repaired_since_diagnosis(self.store, task))

    def test_compatibility_cannot_remove_checks_or_accept_unknown(self):
        for candidate in [FIXED.replace(' < 0', ' < -100'), FIXED.replace("'failed'", "'unknown'"),
                          FIXED.replace("and entry.get('reason')", ''), ORIGINAL.replace('raise ValueError', 'return')]:
            self.assertFalse(code_repair.compatible_failure_guard(ORIGINAL, candidate))
