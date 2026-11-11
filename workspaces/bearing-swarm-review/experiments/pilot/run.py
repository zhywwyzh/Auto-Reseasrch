"""Execute gated diagnostics then development data; retain every result and failure."""
import copy
import itertools
import json
from pathlib import Path
import select
import subprocess
import sys
import time
import traceback
import numpy as np
from scipy.spatial.transform import Rotation
import checker
import model

HERE = Path(__file__).resolve().parent
OUT = Path(sys.argv[1])
CFG = json.loads((HERE/'protocol.json').read_text())


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def selected(case, method):
    if method == 'weak': return []
    if method == 'observed': return case['edges']
    if method == 'all_pairs': return list(itertools.combinations(range(case['n']),2))
    if method == 'tree': return model.forest(case['n'],case['edges'])
    raise ValueError(method)


class Solver:
    def __init__(self):
        self.err = (OUT/'julia-stderr.log').open('w')
        self.proc = subprocess.Popen(['julia','--startup-file=no','--project=/opt/tr002-julia',str(HERE/'solver.jl')], stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,text=True,bufsize=1)
    def solve(self,case,method,precision=None):
        settings = dict(CFG['solver'])
        if precision: settings.update(eps_abs=precision,eps_rel=precision)
        request = {k:case[k] for k in ['id','n','observations']}
        request.update(method=method,strengthened=selected(case,method),settings=settings,input_sha256=checker.fingerprint(case))
        start = time.monotonic()
        self.proc.stdin.write(json.dumps(request)+'\n'); self.proc.stdin.flush()
        if not select.select([self.proc.stdout],[],[],180)[0]: raise TimeoutError('Julia response >180s; halt pilot, preserve evidence')
        line = self.proc.stdout.readline()
        if not line: raise RuntimeError('Julia closed stdout; see stderr')
        report = json.loads(line)
        if 'error' in report: raise RuntimeError(report['error'])
        report['host_roundtrip_seconds'] = time.monotonic()-start
        assert [list(x) for x in report['strengthened']] == [list(x) for x in request['strengthened']]
        return report
    def close(self):
        self.proc.stdin.close()
        try: self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired: self.proc.kill(); self.proc.wait()
        self.err.close()


def faults(case,report):
    rejected=[]
    mutations={
        'stale_input_hash':lambda x:x.update(input_sha256='invalid'),
        'nonsymmetric_M':lambda x:x['M'][0].__setitem__(1,x['M'][0][1]+1),
        'wrong_reported_objective':lambda x:x.update(objective=x['objective']+1),
        'wrong_dual_constant':lambda x:x.update(dual_objective=x['dual_objective']+1),
        'missing_hull_multiplier':lambda x:x['Z'].pop(),
        'wrong_dual_slack':lambda x:x['S'][0].__setitem__(0,x['S'][0][0]+1)}
    for name,mutate in mutations.items():
        changed=copy.deepcopy(report); mutate(changed)
        try: checker.audit(case,changed,CFG['checks'])
        except ValueError: rejected.append(name)
        else: raise AssertionError('false acceptance of '+name)
    reflection=np.array(case['truth']); reflection[0,:,2]*=-1
    try: checker.validate_rotations(reflection)
    except ValueError: rejected.append('reflected_rotation')
    else: raise AssertionError('accepted reflected rotation')
    bad=copy.deepcopy(case); bad['observations'][0]['gi']=[2.,0.,0.]
    try: checker.validate_input(bad)
    except ValueError: rejected.append('nonunit_bearing')
    else: raise AssertionError('accepted nonunit input')
    return rejected


def witness(case):
    n=case['n']; truth=np.array(case['truth']); big=np.concatenate(truth,axis=1); x0=big.T@big
    m=checker.data_matrix(case); points=np.array(case['positions'])
    assert abs(np.sum(m*x0))<1e-10
    if case['family']=='disconnected':
        alternate=truth.copy(); q=Rotation.from_rotvec([.3,-.4,.2]).as_matrix()
        alternate[2:]=q@alternate[2:]; b=np.concatenate(alternate,axis=1); x=b.T@b
    elif case['family']=='collinear':
        axis=points[0,1]-points[0,0]; axis/=np.linalg.norm(axis)
        alternate=truth.copy(); alternate[1]=Rotation.from_rotvec(axis*.8).as_matrix()@alternate[1]
        b=np.concatenate(alternate,axis=1); x=b.T@b
    else:
        b0=points[0,1]-points[0,0]; b0/=np.linalg.norm(b0)
        b1=points[1,1]-points[1,0]; b1/=np.linalg.norm(b1)
        basis=np.column_stack([b0,b1,np.cross(b0,b1)])
        h=np.array([basis.T@r for r in truth]); x=np.zeros_like(m)
        for i in range(n):
            for j in range(n): x[3*i:3*i+3,3*j:3*j+3]=h[i].T@np.diag([1.,1.,float(i==j)])@h[j]
    assert np.linalg.norm(x-x0)>0.1
    assert np.linalg.eigvalsh(x)[0]>-1e-12 and abs(np.sum(m*x))<1e-10
    if not case['unique_strong']:
        for i,j in itertools.combinations(range(n),2):
            assert np.linalg.eigvalsh(checker.hull(x[3*i:3*i+3,3*j:3*j+3]))[0]>-1e-12
    return {'alternate_zero_cost':float(np.sum(m*x)),'alternate_rank':int(np.linalg.matrix_rank(x,tol=1e-8)),
            'gram_distance':float(np.linalg.norm(x-x0)), 'strong_nonunique_witness':not case['unique_strong']}


def run_case(case,solver,records,precision=None):
    checker.validate_input(case)
    save(OUT/'cases'/(case['id']+'.json'),case)
    results=[]
    for method in CFG['methods']:
        start=time.monotonic()
        if method=='nls':
            # No ground truth passed to the optimizer.
            public={k:case[k] for k in ['n','edges','observations']}
            r,raw=model.nls(public,CFG['nls']); upper=checker.objective(case,r)
            lower=checker.weak_numeric_lower(checker.data_matrix(case),r)
            audit={'usable':raw['success'],'strict_certificate':False,'objective_candidate':upper,
                   'numeric_lower':lower,'numeric_gap':upper-lower,'gap_per_observation':(upper-lower)/len(case['observations']),
                   'relative_rotation_error_deg':checker.relative_error(r,np.array(case['truth'])) if case['family'] not in ['disconnected','collinear'] else None,'rotations':r.tolist()}
        else:
            raw=solver.solve(case,method,precision); audit=checker.audit(case,raw,CFG['checks'])
        row={'case':case['id'],'split':case['split'],'family':case['family'],'graph':case.get('graph'),
             'seed':case['seed'],'n':case['n'],'noise_degrees':case['noise_degrees'],'method':method,
             'precision':precision or CFG['solver']['eps_abs'],'wall_seconds':time.monotonic()-start,
             'observations':len(case['observations']),'audit':audit,'raw':raw}
        records.write(json.dumps(row,allow_nan=False)+'\n'); records.flush(); results.append(row)
        if case['split']=='diagnostic':
            assert audit['usable'],(case['id'],method,audit)
            assert audit['objective_candidate']<1e-4,(case['id'],method,'nonzero diagnostic objective',audit)
            if method in ['observed','all_pairs','tree'] and case['unique_strong']:
                assert audit['gram_relative_error']<CFG['checks']['gram_relative_tolerance'],(case['id'],method,audit)
    return results


def main():
    started=time.monotonic(); (OUT/'cases').mkdir(); save(OUT/'protocol.json',CFG)
    status={'status':'running','protocol':CFG['id'],'properties':checker.properties(),'diagnostics':[], 'faults':[]}
    save(OUT/'status.json',status); solver=Solver(); all_rows=[]
    try:
        warm=model.diagnostic('two_directions',2000)
        raw=solver.solve(warm,'observed'); checker.audit(warm,raw,CFG['checks'])
        status['cold_start_seconds']=raw['host_roundtrip_seconds']; status['faults']=faults(warm,raw)
        save(OUT/'warmup.json',raw)
        with (OUT/'results.jsonl').open('w') as records:
            for family,seed in itertools.product(CFG['diagnostics']['families'],CFG['diagnostics']['gauge_seeds']):
                case=model.diagnostic(family,seed); evidence=witness(case)
                all_rows.extend(run_case(case,solver,records))
                status['diagnostics'].append({'id':case['id'],'status':'passed','witness':evidence})
                save(OUT/'status.json',status); print('PASS '+case['id'],flush=True)
            status['diagnostic_gate']='passed'; save(OUT/'status.json',status)
            # Precision sensitivity on one gauge per family; separate from the 120 main runs.
            with (OUT/'precision-results.jsonl').open('w') as precision_records:
                for family in CFG['diagnostics']['families']:
                    run_case(model.diagnostic(family,2101),solver,precision_records,1e-7)
            status['precision_sensitivity']='passed: six diagnostics at 1e-7'; save(OUT/'status.json',status)
            cfg=CFG['development']; seed=cfg['world_seed_start']
            for n,kind,geometry in itertools.product(cfg['robots'],cfg['graphs'],cfg['geometries']):
                for noise in cfg['noise_degrees']:
                    case=model.development(n,kind,geometry,seed,noise,cfg)
                    all_rows.extend(run_case(case,solver,records)); print('DONE '+case['id'],flush=True)
                seed+=1
        status.update(status='completed',development_worlds=seed-CFG['development']['world_seed_start'],
                      development_logs=54,main_method_runs=len(all_rows),elapsed_seconds=time.monotonic()-started,
                      memory_peak_bytes=int(Path('/sys/fs/cgroup/memory.peak').read_text()),strict_certificate=False)
        status['methods']={}
        for method in CFG['methods']:
            rows=[x for x in all_rows if x['split']=='development' and x['method']==method]
            ok=[x for x in rows if x['audit']['usable']]
            status['methods'][method]={'attempted':len(rows),'usable':len(ok),'unusable_cases':[x['case'] for x in rows if not x['audit']['usable']],
                'wall_seconds_p50':float(np.median([x['wall_seconds'] for x in rows])),
                'wall_seconds_p95':float(np.quantile([x['wall_seconds'] for x in rows],.95)),
                'max_tail_mass':max([x['audit'].get('tail_mass',0) for x in ok],default=None),
                'max_numeric_gap_per_observation':max([x['audit']['gap_per_observation'] for x in ok],default=None)}
        save(OUT/'status.json',status)
    except BaseException as exc:
        status.update(status='failed',error=str(exc),traceback=traceback.format_exc(),elapsed_seconds=time.monotonic()-started)
        save(OUT/'status.json',status); raise
    finally: solver.close()


if __name__=='__main__': main()
