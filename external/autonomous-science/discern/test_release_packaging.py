"""Small offline tests for the release adapter; no APIs or world rebuilding."""
import csv
import json
import os
import sys
from pathlib import Path
import unittest
from unittest.mock import patch
from release_paths import ROOT, relocate
import task_spec

class PackagingTests(unittest.TestCase):
    def test_sandbox_binds_literal_interpreter_target(self):
        from sandbox_seal import _py_prefixes
        if not os.path.islink(sys.executable):
            self.skipTest('interpreter is not a symlink')
        target = os.path.normpath(os.path.join(os.path.dirname(sys.executable),
                                               os.readlink(sys.executable)))
        prefix = str(Path(target).parent.parent)
        if prefix not in ('/', '/usr', '/etc'):
            self.assertIn(prefix, _py_prefixes(sys.executable))

    def test_relocation_preserves_numbers_and_source(self):
        source={'score':2.5,'eligible':True,'path':'/workspace/discern-benchmark/tracks/x','nested':[1,None]}
        result=relocate(source)
        self.assertEqual(result['score'],source['score'])
        self.assertEqual(result['nested'],source['nested'])
        self.assertEqual(result['path'],str(ROOT/'tracks/x'))
        self.assertTrue(source['path'].startswith('/workspace/'))

    def test_fasta_and_index(self):
        with patch.dict(os.environ, {'DISCERN_HG38':'/tmp/reference.fa'}):
            self.assertEqual(relocate('/data/anonymous/dna_token/hg38.fa.fai'),'/tmp/reference.fa.fai')

    def test_model_cache_environment(self):
        with patch.dict(os.environ, {'DISCERN_TORCH_HUB':'/tmp/esm/hub'}):
            self.assertEqual(relocate('/home/anonymous/.cache/torch'),'/tmp/esm')
            self.assertEqual(relocate('/home/anonymous/.cache/torch/hub'),'/tmp/esm/hub')

    def test_all_track_specs_load(self):
        with (ROOT/'verification/authority_index.csv').open() as f:
            rows=list(csv.DictReader(f))
        for track in {r['track'] for r in rows}:
            spec=task_spec.load(track)
            self.assertIn('L1',spec)
            self.assertIn('L3',spec)
            self.assertEqual(spec['models'], task_spec.MODELS)

    def test_same_reporting_directory(self):
        self.assertEqual((ROOT/'results/new_models').resolve(), (ROOT/'results/model_reports').resolve())

    def test_real_policy_tsv(self):
        with (ROOT/'SOURCE_DATA_POLICY.tsv').open() as f:
            rows=list(csv.DictReader(f,delimiter='\t'))
        self.assertEqual(len(rows),10)
        self.assertTrue(all(r.get('upstream_links') for r in rows))

if __name__=='__main__': unittest.main()
