"""Independent floating-point audit. No output here is a rigorous certificate."""
import hashlib
import json
import numpy as np
from scipy.spatial.transform import Rotation


def fingerprint(case):
    return hashlib.sha256(json.dumps(case, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def data_matrix(case):
    rows = []
    for o in case['observations']:
        y = np.zeros(3*case['n'])
        y[3*o['i']:3*o['i']+3] = o['gi']
        y[3*o['j']:3*o['j']+3] = o['gj']
        rows.append(y)
    a = np.array(rows)
    return a.T @ a


def hull(y):
    # Construct by quaternion inverse coefficients, independent of JuMP expressions.
    q = np.zeros((4, 4))
    q[0, 0] = 1+np.trace(y)
    for a in range(3): q[a+1, a+1] = 1+2*y[a, a]-np.trace(y)
    q[0, 1:] = [y[2, 1]-y[1, 2], y[0, 2]-y[2, 0], y[1, 0]-y[0, 1]]
    q[1:, 0] = q[0, 1:]
    for a in range(3):
        for b in range(a+1, 3): q[a+1, b+1] = q[b+1, a+1] = y[a, b]+y[b, a]
    return q


def adjoint(z):
    result = np.zeros((3, 3))
    for a in range(3):
        for b in range(3):
            basis = np.zeros((3, 3)); basis[a, b] = 1
            result[a, b] = np.sum(z*(hull(basis)-np.eye(4)))
    return result


def validate_rotations(r):
    if not np.isfinite(r).all(): raise ValueError('nonfinite rotation')
    if np.max(np.abs(np.swapaxes(r, 1, 2)@r-np.eye(3))) > 1e-8: raise ValueError('nonorthogonal rotation')
    if np.max(np.abs(np.linalg.det(r)-1)) > 1e-8: raise ValueError('reflection is not SO3')


def objective(case, r):
    validate_rotations(r)
    return float(sum(np.linalg.norm(r[o['i']]@o['gi']+r[o['j']]@o['gj'])**2 for o in case['observations']))


def candidate(x, n, edges):
    # Disconnected graphs have independent gauges. Never extract every component
    # against block zero: cross-component Gram blocks can legitimately be zero.
    adjacency = [[] for _ in range(n)]
    for i, j in edges: adjacency[i].append(j); adjacency[j].append(i)
    anchors = [None]*n
    for root in range(n):
        if anchors[root] is not None: continue
        pending = [root]; anchors[root] = root
        while pending:
            for j in adjacency[pending.pop()]:
                if anchors[j] is None: anchors[j] = root; pending.append(j)
    r = []
    for i in range(n):
        a = anchors[i]
        u, _, vt = np.linalg.svd(x[3*a:3*a+3, 3*i:3*i+3])
        r.append(u @ np.diag([1, 1, np.linalg.det(u@vt)]) @ vt)
    return np.array(r)


def relative_error(r, truth):
    errors = []
    for i in range(len(r)):
        for j in range(i+1, len(r)):
            q = (r[i].T @ r[j]).T @ (truth[i].T @ truth[j])
            errors.append(Rotation.from_matrix(q).magnitude()*180/np.pi)
    return float(np.mean(errors))


def weak_numeric_lower(m, r):
    big = np.concatenate(r, axis=1); rm = big@m
    lam = np.zeros_like(m)
    for i, ri in enumerate(r):
        b = ri.T@rm[:, 3*i:3*i+3]
        lam[3*i:3*i+3, 3*i:3*i+3] = (b+b.T)/2
    ev = np.linalg.eigvalsh(m-lam)[0]
    margin = 1e-10*max(1, np.linalg.norm(m, 2))
    return float(np.trace(lam)-len(m)*max(0, -ev+margin))


def audit(case, report, cfg):
    if report.get('input_sha256') != fingerprint(case): raise ValueError('input provenance mismatch')
    if 'X' not in report: return {'usable': False, 'reason': report.get('termination', report.get('error'))}
    m = data_matrix(case); scale = max(1, np.linalg.norm(m, 2))
    mt = np.array(report['M'])
    if np.max(np.abs(mt-m)) > 1e-10*scale: raise ValueError('objective/data matrix mismatch')
    if np.max(np.abs(mt-mt.T)) > 1e-12*scale: raise ValueError('nonsymmetric M')
    x, lam, raw_s = (np.array(report[key]) for key in ['X', 'Lambda', 'S'])
    if any(not np.isfinite(a).all() for a in [x,lam,raw_s]): raise ValueError('nonfinite solver output')
    if max(np.max(np.abs(a-a.T)) for a in [x,lam,raw_s]) > 1e-8*scale: raise ValueError('nonsymmetric output')
    edges, zs = report['strengthened'], [np.array(z) for z in report['Z']]
    if len(edges) != len(zs): raise ValueError('missing hull multiplier')
    s = m-lam; repaired = m-lam
    dual = float(np.trace(lam)); repaired_dual = dual
    hull_min, z_min = 1., 1.
    for (i,j), z in zip(edges,zs):
        zi,zv = np.linalg.eigh((z+z.T)/2)
        z_min = min(z_min, zi[0]); zr = (zv*np.maximum(zi,0))@zv.T
        for target, mult in [(s,z),(repaired,zr)]:
            a = adjoint(mult)/2
            target[3*i:3*i+3,3*j:3*j+3] -= a
            target[3*j:3*j+3,3*i:3*i+3] -= a.T
        dual -= np.trace(z); repaired_dual -= np.trace(zr)
        hull_min = min(hull_min, np.linalg.eigvalsh(hull(x[3*i:3*i+3,3*j:3*j+3]))[0])
    stationarity = float(np.max(np.abs(s-raw_s)))
    if stationarity > cfg['numeric_feasibility_tolerance']*scale: raise ValueError('dual stationarity/sign/factor mismatch')
    if abs(dual-report['dual_objective']) > cfg['objective_relative_tolerance']*scale: raise ValueError('dual constant/sign mismatch')
    raw_objective = float(np.sum(m*x))
    if abs(raw_objective-report['objective']) > cfg['objective_relative_tolerance']*scale: raise ValueError('reported objective mismatch')
    eigs = np.linalg.eigvalsh(x)
    diagonal = max(np.max(np.abs(x[3*i:3*i+3,3*i:3*i+3]-np.eye(3))) for i in range(case['n']))
    feasible = bool(diagonal < cfg['numeric_feasibility_tolerance'] and eigs[0] > -cfg['numeric_feasibility_tolerance'] and hull_min > -cfg['numeric_feasibility_tolerance'])
    r = candidate(x, case['n'], case['edges']); upper = objective(case,r)
    trace_obj = float(np.sum(m*(np.concatenate(r,axis=1).T@np.concatenate(r,axis=1))))
    if abs(upper-trace_obj) > 1e-9*scale: raise ValueError('candidate residual/trace mismatch')
    smin = np.linalg.eigvalsh(repaired)[0]
    lower = float(repaired_dual-len(m)*max(0,-smin+1e-10*scale))
    if lower > upper+1e-7*scale: raise ValueError('lower exceeds feasible upper')
    truth = np.array(case['truth']); big = np.concatenate(truth,axis=1); x0 = big.T@big
    return {'usable':feasible, 'strict_certificate':False, 'objective_raw':raw_objective,
            'objective_candidate':upper,'numeric_lower':lower,'numeric_gap':upper-lower,
            'gap_per_observation':(upper-lower)/len(case['observations']),
            'minimum_eigenvalue':float(eigs[0]),'tail_mass':float(np.maximum(eigs[:-3],0).sum()),
            'numerical_rank':int(np.sum(eigs>1e-5*max(1,eigs[-1]))),
            'diagonal_error':float(diagonal),'hull_minimum':float(hull_min),'dual_multiplier_minimum':float(z_min),
            'dual_stationarity_error':stationarity, 'gram_relative_error':float(np.linalg.norm(x-x0)/np.linalg.norm(x0)),
            'relative_rotation_error_deg':relative_error(r,truth) if case['family'] not in ['disconnected','collinear'] else None,
            'rotation_identifiability':'not unique' if case['family'] in ['disconnected','collinear'] else 'not established by this numerical audit',
            'rotations':r.tolist()}


def validate_input(case):
    r = np.array(case['truth']); validate_rotations(r)
    p = np.array(case['positions']); max_chord = 2*np.sin(np.deg2rad(case['noise_degrees'])/2)
    for o in case['observations']:
        i,j,t = o['i'],o['j'],o['t']; a,b = np.array(o['gi']),np.array(o['gj'])
        if max(abs(np.linalg.norm(a)-1),abs(np.linalg.norm(b)-1))>1e-10: raise ValueError('non-unit bearing')
        direction = p[t,j]-p[t,i]; direction /= np.linalg.norm(direction)
        if max(np.linalg.norm(r[i]@a-direction),np.linalg.norm(r[j]@b+direction))>max_chord+1e-10: raise ValueError('frame/sign/noise cap mismatch')


def properties():
    rng = np.random.default_rng(491)
    for _ in range(30):
        r = Rotation.random(random_state=rng).as_matrix()
        assert np.linalg.eigvalsh(hull(r))[0] > -1e-12
        y = rng.normal(size=(3,3)); z = rng.normal(size=(4,4)); z=(z+z.T)/2
        assert abs(np.sum(z*(hull(y)-np.eye(4)))-np.sum(adjoint(z)*y)) < 1e-12
    assert np.linalg.eigvalsh(hull(np.diag([1.,1.,-1.])))[0] < -1
    return ['30 random SO3 hull feasibility checks','30 independent adjoint inner-product identities','reflection excluded by quaternion LMI']
