"""Measurement generation and SO(3) baseline. Ground truth never enters the optimizer."""
import itertools
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation


def project(a):
    u, _, vt = np.linalg.svd(a)
    return u @ np.diag([1., 1., np.linalg.det(u @ vt)]) @ vt


def forest(n, edges):
    parent = list(range(n))
    def find(i):
        while parent[i] != i:
            i = parent[i]
        return i
    selected = []
    for i, j in edges:
        a, b = find(i), find(j)
        if a != b:
            selected.append([i, j]); parent[b] = a
    return selected


def graph(n, kind):
    if kind == 'dense': return list(itertools.combinations(range(n), 2))
    edges = [(i, i+1) for i in range(n-1)]
    if kind == 'cycle': edges.append((0, n-1))
    return sorted(edges)


def cap_noise(v, degrees, rng):
    if degrees == 0: return v.copy()
    c = rng.uniform(np.cos(np.deg2rad(degrees)), 1., len(v))
    az = rng.uniform(0., 2*np.pi, len(v))
    axis = np.eye(3)[np.argmin(np.abs(v), axis=1)]
    tangent = np.cross(v, axis); tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    second = np.cross(v, tangent)
    return c[:, None]*v + np.sqrt(1-c*c)[:, None]*(np.cos(az)[:, None]*tangent + np.sin(az)[:, None]*second)


def observations(n, edges, positions, rotations, noise, seed):
    rng = np.random.default_rng(seed)
    rows = []
    for i, j in edges:
        delta = positions[:, j] - positions[:, i]
        distances = np.linalg.norm(delta, axis=1)
        if np.min(distances) < 1e-8: raise ValueError('coincident robots; reject and record, never resample')
        directions = delta / distances[:, None]
        gi0 = directions @ rotations[i]
        gj0 = -directions @ rotations[j]
        gi, gj = cap_noise(gi0, noise, rng), cap_noise(gj0, noise, rng)
        for k, (a, b) in enumerate(zip(gi, gj)):
            rows.append({'i': i, 'j': j, 't': k, 'gi': a.tolist(), 'gj': b.tolist()})
    return rows


def diagnostic(family, seed):
    n = 2 if family in ['two_directions', 'collinear'] else 4
    edges = graph(n, 'dense')
    if family == 'strengthened_tree': edges = graph(n, 'tree')
    if family == 'bridge': edges = [(0, 1), (0, 2), (1, 2), (2, 3)]
    if family == 'disconnected': edges = [(0, 1), (2, 3)]
    rng = np.random.default_rng(seed)
    rotations = Rotation.random(n, random_state=rng).as_matrix()
    global_rotation = Rotation.random(random_state=rng).as_matrix()
    directions = np.array([[1., 0, 0], [0, 1., 0]]) @ global_rotation.T
    if family == 'collinear': directions[1] = directions[0]
    positions = directions[:, None, :] * (1 + np.arange(n))[None, :, None]
    return {'id': f'diag-{family}-{seed}', 'split': 'diagnostic', 'family': family,
            'seed': seed, 'n': n, 'edges': edges, 'noise_degrees': 0,
            'observations': observations(n, edges, positions, rotations, 0, seed),
            'truth': rotations.tolist(), 'positions': positions.tolist(),
            'unique_strong': family not in ['disconnected', 'collinear']}


def development(n, kind, geometry, seed, degrees, cfg):
    rng = np.random.default_rng(seed)
    points = rng.normal(size=(cfg['control_points'], n, 3))
    points[:, :, 0] += np.arange(n)[None, :]*2.5
    points[:, :, 2] *= {'planar': 0., 'near_planar': .02, 'spatial': 1.}[geometry]
    old, new = np.linspace(0, 1, len(points)), np.linspace(0, 1, cfg['samples'])
    positions = np.stack([np.stack([np.interp(new, old, points[:, i, a]) for a in range(3)], axis=1) for i in range(n)], axis=1)
    rotations = Rotation.random(n, random_state=rng).as_matrix()
    edges = graph(n, kind)
    # Same random stream across noise levels pairs the noise directions by world.
    return {'id': f'dev-{seed}-{degrees}deg', 'split': 'development', 'family': geometry,
            'graph': kind, 'seed': seed, 'n': n, 'edges': edges, 'noise_degrees': degrees,
            'observations': observations(n, edges, positions, rotations, degrees, seed+100000),
            'truth': rotations.tolist(), 'positions': positions.tolist(),
            'control_points': points.tolist(), 'unique_strong': degrees == 0}


def measurement_initialization(n, edges, obs):
    rotations = [None]*n
    tree = forest(n, edges)
    relative = {}
    for i, j in tree:
        rows = [o for o in obs if (o['i'], o['j']) == (i, j)]
        gi, gj = np.array([o['gi'] for o in rows]), np.array([o['gj'] for o in rows])
        relative[i, j] = project(-gi.T @ gj)
    for root in range(n):
        if rotations[root] is not None: continue
        rotations[root] = np.eye(3)
        changed = True
        while changed:
            changed = False
            for (i, j), q in relative.items():
                if rotations[i] is not None and rotations[j] is None:
                    rotations[j] = rotations[i] @ q; changed = True
                elif rotations[j] is not None and rotations[i] is None:
                    rotations[i] = rotations[j] @ q.T; changed = True
    return np.array(rotations)


def nls(case, cfg):
    n, obs = case['n'], case['observations']
    initial = measurement_initialization(n, case['edges'], obs)
    ii = np.array([o['i'] for o in obs]); jj = np.array([o['j'] for o in obs])
    gi = np.array([o['gi'] for o in obs]); gj = np.array([o['gj'] for o in obs])
    def unpack(x):
        return np.concatenate([np.eye(3)[None], Rotation.from_rotvec(x.reshape(-1, 3)).as_matrix()])
    def residual(x):
        r = unpack(x)
        return (np.einsum('kij,kj->ki', r[ii], gi)+np.einsum('kij,kj->ki', r[jj], gj)).ravel()
    x = Rotation.from_matrix(initial[1:]).as_rotvec().ravel()
    fit = least_squares(residual, x, max_nfev=cfg['max_nfev'], ftol=cfg['ftol'], xtol=cfg['xtol'], gtol=cfg['gtol'])
    return unpack(fit.x), {'success': bool(fit.success), 'nfev': int(fit.nfev), 'message': fit.message, 'initial_objective': float(residual(x) @ residual(x))}
