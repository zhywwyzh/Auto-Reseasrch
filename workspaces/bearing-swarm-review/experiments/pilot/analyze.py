"""Descriptive pilot report, not a significance test or strict certificate."""
import collections
import hashlib
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import checker
import model

RUN=Path(sys.argv[1]); OUT=Path(sys.argv[2]); OUT.mkdir(exist_ok=True)
status=json.loads((RUN/'status.json').read_text())
assert status['status']=='completed'
records=[json.loads(x) for x in (RUN/'results.jsonl').read_text().splitlines()]
development=[x for x in records if x['split']=='development']
groups=collections.defaultdict(list)
for row in records: groups[row['case']].append(row)
nesting=[]
for case,rows in groups.items():
    methods={r['method']:r for r in rows}
    for lower,higher in [('weak','tree'),('tree','observed'),('observed','all_pairs')]:
        a,b=methods[lower],methods[higher]
        if not a['audit']['usable'] or not b['audit']['usable']:continue
        # Stronger primal value need not be monotone to machine precision.
        delta=b['audit']['objective_raw']-a['audit']['objective_raw']
        tolerance=1e-4*max(1,np.linalg.norm(np.array(a['raw']['M']),2))
        if delta < -tolerance: nesting.append({'case':case,'pair':[lower,higher],'difference':delta,'tolerance':tolerance})
assert not nesting,nesting

strata=[]
for noise in [0,1,3]:
    for method in ['weak','observed','all_pairs','tree','nls']:
        rows=[x for x in development if x['method']==method and x['noise_degrees']==noise]
        valid=[x for x in rows if x['audit']['usable']]
        strata.append({'noise_degrees':noise,'method':method,'attempted':len(rows),'usable':len(valid),
            'mean_pair_rotation_error_deg':float(np.mean([r['audit']['relative_rotation_error_deg'] for r in valid])) if valid else None,
            'median_gap_per_observation':float(np.median([r['audit']['gap_per_observation'] for r in valid])) if valid else None,
            'median_tail_mass':float(np.median([r['audit'].get('tail_mass',0) for r in valid])) if valid and method!='nls' else None})

# Exploratory evaluation of the previously derived D5 sufficient bound.
# This uses only measured directions and the generator's declared noise cap.
bound_records=[]
for path in sorted((RUN/'cases').glob('dev-*.json')):
    case=json.loads(path.read_text()); n=case['n']; xi=2*np.sin(np.deg2rad(case['noise_degrees'])/2)
    degrees=np.zeros(n); weights={}
    for i,j in case['edges']:
        obs=[o for o in case['observations'] if o['i']==i and o['j']==j]
        a=np.array([o['gi'] for o in obs]); values=np.linalg.eigvalsh(a.T@a)
        weights[i,j]=max(0.,sum(values[:2])-4*len(obs)*xi)
        degrees[i]+=len(obs); degrees[j]+=len(obs)
    beta=4*max(degrees)*xi
    for mode,edges in [('tree',model.forest(n,case['edges'])),('observed',case['edges'])]:
        laplacian=np.zeros((n,n))
        for i,j in edges:
            w=weights[i,j]; laplacian[i,i]+=w;laplacian[j,j]+=w;laplacian[i,j]-=w;laplacian[j,i]-=w
        connectivity=float(np.linalg.eigvalsh(laplacian)[1])
        bound=12*n*beta/connectivity if connectivity>1e-10 else None
        bound_records.append({'case':case['id'],'noise_degrees':case['noise_degrees'],'mode':mode,'lambda2_lower':connectivity,
                              'beta':float(beta),'tail_bound':float(bound) if bound is not None else None,'trace':3*n,'informative':bool(bound is not None and bound<3*n)})

fig,axes=plt.subplots(1,2,figsize=(10,4),layout='constrained')
methods=['weak','observed','all_pairs','tree','nls']
for method in methods:
    rows=[r for r in strata if r['method']==method]
    axes[0].plot([r['noise_degrees'] for r in rows],[r['mean_pair_rotation_error_deg'] for r in rows],marker='o',label=method)
axes[0].set(xlabel='Bearing noise cap (degrees)',ylabel='Mean pairwise rotation error (degrees)',title='Development only: 18 paired worlds')
axes[0].legend(fontsize=8)
for method in methods[:-1]:
    rows=[r for r in records if r['split']=='diagnostic' and r['method']==method and 'collinear' not in r['case'] and 'disconnected' not in r['case']]
    axes[1].scatter([methods.index(method)]*len(rows),[r['audit']['tail_mass'] for r in rows],alpha=.5,label=method)
axes[1].set(xticks=range(4),xticklabels=methods[:-1],ylabel='Gram eigenvalue mass beyond top 3',title='16 identifiable planar diagnostics')
fig.suptitle('TR002-PILOT-001: numerical diagnostics, no novelty or significance claim',fontsize=11)
fig.savefig(OUT/'pilot-results.svg'); fig.savefig(OUT/'pilot-results.png',dpi=140); plt.close(fig)
weak_reflections=[]
for row in development:
    if row['method']!='weak' or 'X' not in row['raw']: continue
    x=np.array(row['raw']['X'])
    dets=[float(np.linalg.det(x[:3,3*i:3*i+3])) for i in range(row['n'])]
    if min(dets)<-.9 and row['audit']['numerical_rank']==3:
        weak_reflections.append({'case':row['case'],'termination':row['raw']['termination'],
            'anchor_block_determinants':dets,'sdp_objective':row['audit']['objective_raw'],
            'so3_candidate_objective':row['audit']['objective_candidate'],
            'pair_rotation_error_deg':row['audit']['relative_rotation_error_deg']})
summary={'id':'TR002-PILOT-001','date':'2026-11-11','status':'completed','protocol_version':2,
         'run_directory':Path(next(x for x in json.loads((RUN/'host-receipt.json').read_text())['command'] if x.startswith('type=bind,src=') and x.endswith('dst=/results')).split('src=',1)[1].split(',dst=',1)[0]).name,'counts':{'diagnostic_cases':len(status['diagnostics']),'development_worlds':status['development_worlds'],
            'development_logs':status['development_logs'],'main_method_runs':status['main_method_runs'],'precision_repeat_runs':30,'faults_rejected':len(status['faults'])},
         'runtime':{'elapsed_seconds':status['elapsed_seconds'],'memory_peak_bytes':status['memory_peak_bytes'],'cold_start_seconds':status['cold_start_seconds']},
         'methods':status['methods'],'strata':strata,'nesting_violations':nesting,
         'rank3_reflection_cases':weak_reflections,
         'timeouts':[{'case':r['case'],'method':r['method'],'numeric_gap':r['audit']['numeric_gap']} for r in development if r['raw'].get('termination')=='TIME_LIMIT'],
         'termination_counts':dict(collections.Counter(r['raw'].get('termination','NLS_SUCCESS' if r['raw'].get('success') else 'NLS_FAILURE') for r in development)),
         'planar_diagnostics':{m:{'cases':len(v:=[r for r in records if r['split']=='diagnostic' and r['method']==m and 'collinear' not in r['case'] and 'disconnected' not in r['case']]),
             'tail_mass_min':min(r['audit']['tail_mass'] for r in v),'tail_mass_max':max(r['audit']['tail_mass'] for r in v),
             'max_gram_relative_error':max(r['audit']['gram_relative_error'] for r in v)} for m in methods[:-1]},
         'd5_exploratory':{'interpretation':'Exploratory descriptive check of D5, not preregistered hypothesis testing or a proof. eta=0 theoretical optimal-solution bound; no claim that numerical solver output is exact SDP optimum.',
             'noisy_records':len(noisy:=[r for r in bound_records if r['noise_degrees']>0]),
             'informative_noisy_records':sum(r['informative'] for r in noisy),'records':bound_records},
         'source_sha256':json.loads((RUN/'host-receipt.json').read_text())['source_sha256'],
         'evidence_sha256':{name:hashlib.sha256((RUN/name).read_bytes()).hexdigest() for name in ['protocol.json','status.json','results.jsonl','precision-results.jsonl','host-receipt.json']},
         'image_id':json.loads((RUN/'host-receipt.json').read_text())['image_id'],
         'analysis_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
         'limitations':['Only rotation subproblem, exact rotation odometry and synchronized paired bearings; no translation, FoV, collisions, closed-loop or real flight.',
            '18 development worlds, one per stratum; noise variants are paired, not 54 independent worlds; no held-out evaluation or significance claim.',
            'All PSD/duality checks are floating-point; no interval verification or rigorous global-optimality certificates.',
            'NLS is one geometry-initialized run, not full multi-start or temporal warm-start B4; no method-superiority conclusion.',
            'Only SCS backend tested; precision reruns are not independent-solver replication.',
            '15-second SCS limit and 150 NLS evaluation limit are diagnostic settings; complete 60-second end-to-end budget enforcement and fair timing remain pending.',
            'CPU shared with host; timings descriptive only. No novel selector implemented; tree and convex-hull constraints are baselines.',
            'v1 failed on disconnected-graph extraction; all failed evidence retained and all diagnostics rerun after component-aware fix.']}
(OUT/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
print(json.dumps({'status':'analyzed','strata':strata,'d5_informative':summary['d5_exploratory']['informative_noisy_records'],'noisy_bound_records':len(noisy)},indent=2))
