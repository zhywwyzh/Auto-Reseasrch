"""Recovery-kernel exceptions must enqueue an agent, not just emit heartbeats."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import ars
import code_repair
import supervisor_faults


class SupervisorFaultTests(unittest.TestCase):
    def test_outer_fault_is_a_deduplicated_repair_task_without_research_dispatch(self):
        with tempfile.TemporaryDirectory() as name:
            repo=Path(name);system=repo/'workspaces/autonomous-research-system';system.mkdir(parents=True)
            (repo/'workspaces/topics.json').write_text(json.dumps({'topics':[]}))
            (system/'kernel.py').write_text('def sample(): return 1\n')
            directory=ars.create_campaign('ARS-DEMO','SYNTHETIC outer recovery failure',repo=repo,backend='mock')
            store=ars.Store(directory)
            try:
                with store.tx():
                    cfg=store.state()['config'];cfg['code_repair']=dict(code_repair.POLICY)
                    store.db.execute('UPDATE campaign SET config=?',(ars.dump(cfg),))
                    store.db.execute("UPDATE tasks SET status='COMPLETED',result=?,verification=?",(ars.dump(dict(status='done',verdict='revise',summary='fixture',report='fixture',next_tasks=[],memories=[],evidence=[])),ars.dump({'gate':'structure_and_source_correspondence'})))
                    store.status('WAITING_EXTERNAL','fixture scheduler failure')
                error="AttributeError: module 'research_continuation' has no attribute 'submission_limit'"
                first=supervisor_faults.capture(directory,error)
                second=supervisor_faults.capture(directory,error)
                self.assertEqual(first['action'],'repair_agent_queued')
                self.assertEqual(first['task_id'],second['task_id'])
                self.assertEqual(store.state()['calls'],0)
                self.assertEqual(sum(t['phase']==code_repair.PHASE for t in store.tasks()),1)
                self.assertIn('submission_limit',store.tasks()[-1]['instruction'])
                self.assertTrue(store.db.execute("SELECT 1 FROM events WHERE type='system.repair_required'").fetchone())
            finally:store.close()

    def test_old_pin_does_not_supply_a_stale_management_module_to_new_kernel(self):
        with tempfile.TemporaryDirectory() as name:
            repo=Path(name);(repo/'workspaces').mkdir()
            (repo/'workspaces/topics.json').write_text(json.dumps({'topics':[]}))
            directory=ars.create_campaign('ARS-DEMO','SYNTHETIC API compatibility',repo=repo,backend='mock')
            pin=repo/'old-runtime';pin.mkdir()
            for source in HERE.glob('*.py'):
                shutil.copyfile(source,pin/source.name)
            # The real deployed failure was an old module lacking this API.
            # Copying today's module into the fake pin would miss that failure.
            (pin/'research_continuation.py').write_text("VERSION='old-pin-without-submission-limit'\n")
            original=hashlib.sha256((pin/'research_continuation.py').read_bytes()).hexdigest()
            script='''import sys,json
from pathlib import Path
sys.path.insert(0,sys.argv[1])
import runtime_entry
runtime_entry.install(Path(sys.argv[2]))
import research_continuation
print(json.dumps({'guard_module':research_continuation.__file__,
 'guard_present':callable(getattr(research_continuation,'submission_limit',None))}))
'''
            output=subprocess.run([sys.executable,'-c',script,str(HERE),str(pin)],capture_output=True,text=True,check=True)
            result=json.loads(output.stdout)
            self.assertTrue(result['guard_present'],'new recovery API is missing in legacy pin overlay')
            self.assertEqual(Path(result['guard_module']).resolve(),HERE/'research_continuation.py')
            self.assertEqual(hashlib.sha256((pin/'research_continuation.py').read_bytes()).hexdigest(),original)


if __name__=='__main__':unittest.main()
