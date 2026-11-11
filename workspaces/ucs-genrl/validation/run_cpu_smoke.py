"""Bounded acceptance probe against read-only upstream; not an RL benchmark."""
import copy
import hashlib
import json
import os
import pathlib
import pickle
import random
import resource
import sys
import time
import traceback

START = time.monotonic()
OUT = pathlib.Path('/run')
REPORT = {'protocol': 'TR001-CPU-SMOKE-v1', 'status': 'running',
          'gpu_used': False, 'paid_model_calls': 0, 'checks': {},
          'environment_steps': 0, 'learner_consumed_samples': 0,
          'optimizer_calls': 0, 'limitations': [
              'Single synchronous collector, batch=1, CPU only.',
              'Original candidate config, not thesis-definition equivalence.',
              'No curriculum, B-CF, convergence or comparative efficacy test.',
              'Restore checks cover Python environment/RNG and fixed-batch learner variables; not asynchronous queues or TF sampler RNG.']}


def save_report():
    REPORT['wall_seconds'] = time.monotonic() - START
    REPORT['process_peak_rss_mib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    (OUT / 'result.json').write_text(json.dumps(REPORT, indent=2, ensure_ascii=False, allow_nan=False))


def check(name, condition, detail=None):
    REPORT['checks'][name] = {'passed': bool(condition), 'detail': detail}
    save_report()
    if not condition:
        raise AssertionError(name)


def main():
    import numpy as np
    import tensorflow as tf
    import pkg_resources
    sys.path.insert(0, '/upstream')
    # Avoid passing harness CLI flags to upstream absl flags.
    sys.argv = [sys.argv[0]]
    import experiment as ex
    from agent import ResNetLSTMAgent, AgentOutput
    from environments import StepOutput, StepOutputInfo
    from mcs_envs.gym_base.data_collection_1 import Env
    nest = tf.contrib.framework.nest
    seed = 20261111
    random.seed(seed)
    np.random.seed(seed)
    tf.set_random_seed(seed)
    REPORT['versions'] = {p: pkg_resources.get_distribution(p).version for p in
                          ['tensorflow', 'numpy', 'dm-sonnet', 'tensorflow-probability', 'trfl', 'gym']}
    REPORT['source_sha256'] = {p: hashlib.sha256((pathlib.Path('/upstream') / p).read_bytes()).hexdigest()
                               for p in ['agent.py', 'experiment.py', 'vtrace.py', 'utils.py',
                                         'mcs_envs/gym_base/data_collection_1.py',
                                         'mcs_envs/env_setting/env_setting_1.py']}
    ex.FLAGS.batch_size = 1
    ex.FLAGS.unroll_length = 20
    # Retain upstream learning-rate horizon; do not collapse it to smoke length.
    REPORT['learner_settings'] = {k: getattr(ex.FLAGS, k) for k in
                                 ['batch_size', 'unroll_length', 'learning_rate', 'total_environment_frames',
                                  'reward_clipping', 'pc_cost', 'discounting', 'num_players']}
    env = Env()
    obs = env.reset()
    check('observation_shape', obs.shape == (80, 80, 3), list(obs.shape))
    check('two_players_25_actions', env.n == 2 and all(a.n == 25 for a in env.action_space))
    REPORT['candidate_configuration'] = {k: env.sg.V[k] for k in
                                       ['MAP_X', 'MAP_Y', 'MAX_ENERGY', 'ALPHA', 'FACTOR', 'NUM_UAV']}
    rng = np.random.RandomState(seed + 1)

    def step(actions, target=env):
        result = target.step(actions, indicator=[0] * target.n)
        REPORT['environment_steps'] += 1
        o, r, done, info, indicator = result
        assert o.shape == (80, 80, 3) and np.isfinite(o).all() and np.isfinite(r)
        assert np.isfinite(target.energy).all() and np.min(target.energy) >= -1e-5
        assert np.max(target.energy) <= target.maxenergy + 1e-5
        assert np.min(target.mapmatrix) >= -1e-5
        return result

    # Zero-denominator behavior is observed, not silently repaired.
    with np.errstate(invalid='ignore', divide='ignore'):
        raw_reset = [env.collection_fairness, env.efficiency]
    REPORT['reset_metric_finite'] = [bool(np.isfinite(v)) for v in raw_reset]
    for _ in range(80):
        _, _, done, _, _ = step(rng.randint(0, 25, size=2))
        if done:
            env.reset()
    check('environment_80_steps_finite', True)
    amounts = env._mapmatrix - env.mapmatrix
    denom = len(amounts) * np.sum(amounts ** 2)
    if denom > 0:
        expected_f = float(np.sum(amounts) ** 2 / denom)
        check('absolute_collection_jain_matches', np.isclose(expected_f, env.collection_fairness), expected_f)
    else:
        REPORT['checks']['absolute_collection_jain_matches'] = {'passed': None, 'detail': 'No collection; undefined.'}

    # Persist and reload a Python environment + RNG snapshot; replay the same actions.
    with (OUT / 'environment-snapshot.pkl').open('wb') as f:
        pickle.dump((env, rng.get_state()), f, protocol=4)
    def replay(target):
        records = []
        for _ in range(10):
            a = rng.randint(0, 25, size=2)
            o, r, d, _, _ = step(a, target)
            records.append((o.copy(), float(r), bool(d), target.energy.copy()))
            if d:
                target.reset()
        return records
    reference = replay(env)
    with (OUT / 'environment-snapshot.pkl').open('rb') as f:
        restored, rng_state = pickle.load(f)  # only this harness's own local file
    rng.set_state(rng_state)
    repeated = replay(restored)
    check('environment_rng_disk_restore', all(np.array_equal(a, b) for x, y in zip(reference, repeated)
                                             for a, b in zip(x, y)))

    def ph(dtype, shape, name):
        return tf.placeholder(dtype, shape, name)
    def env_ph(prefix, shape):
        info = StepOutputInfo(ph(tf.float32, shape, prefix+'return'), ph(tf.int32, shape, prefix+'steps'),
                              ph(tf.float32, shape, prefix+'raw_return'), ph(tf.int32, shape, prefix+'raw_steps'))
        return StepOutput(ph(tf.float32, shape, prefix+'reward'), info,
                          ph(tf.bool, shape, prefix+'done'), ph(tf.float32, shape+[80, 80, 3], prefix+'obs'))
    learner = ResNetLSTMAgent(25, num_players=2)
    single_env = env_ph('actor_', [1])
    last_action = ph(tf.int32, [1, 2], 'last_action')
    core = nest.map_structure(lambda x: ph(tf.float32, x.shape.as_list(), 'core'), learner.initial_state(1))
    single_output, single_core = learner((last_action, single_env), core)
    batch_env = env_ph('batch_', [21, 1])
    batch_output = AgentOutput(*[ph(t.dtype, [21] + t.shape.as_list(), 'batch_'+name)
                                 for name, t in zip(AgentOutput._fields, single_output)])
    batch_core = nest.map_structure(lambda x: ph(tf.float32, x.shape.as_list(), 'batch_core'), core)
    global_step = tf.train.get_or_create_global_step()
    _, _, update = ex.build_learner(learner, batch_core, batch_env, batch_output, global_step)
    variables = tf.global_variables()
    saver = tf.train.Saver(var_list=variables)
    config = tf.ConfigProto(device_count={'GPU': 0}, intra_op_parallelism_threads=2,
                            inter_op_parallelism_threads=1)
    REPORT['parameter_count'] = int(sum(np.prod(v.shape.as_list()) for v in tf.trainable_variables()))
    REPORT['global_variable_count'] = len(variables)
    REPORT['resource_scope'] = 'Single Python process RSS; CPU only; excludes Docker image/build.'

    def mapping(placeholders, values):
        return dict(zip(nest.flatten(placeholders), nest.flatten(values)))
    def zero_info():
        return StepOutputInfo(np.zeros(1, np.float32), np.zeros(1, np.int32),
                              np.zeros(1, np.float32), np.zeros(1, np.int32))
    def env_value(o, r=0., d=True):
        return StepOutput(np.array([r], np.float32), zero_info(), np.array([d], bool), o[None].astype(np.float32))
    def sample(logits, action_rng):
        logits = logits.reshape(2, 25).astype(np.float64)
        p = np.exp(logits - logits.max(axis=1, keepdims=True))
        p /= p.sum(axis=1, keepdims=True)
        return np.array([[action_rng.choice(25, p=row) for row in p]], np.int32)

    def assert_finite_loss_log():
        losses = (OUT / 'loss_debug.txt').read_text().lower()
        assert 'nan' not in losses and 'inf' not in losses, 'Non-finite upstream loss'

    with tf.Session(config=config) as session:
        session.run(tf.global_variables_initializer())
        session.run(tf.local_variables_initializer())
        before = session.run(tf.trainable_variables())
        obs = env.reset()
        current_env = env_value(obs)
        current_core = session.run(learner.initial_state(1))
        previous = AgentOutput(*[np.zeros(t.shape.as_list(), t.dtype.as_numpy_dtype) for t in single_output])
        action_rng = np.random.RandomState(seed + 2)
        counters = []
        training_started = time.monotonic()
        for iteration in range(3):
            first_core = copy.deepcopy(current_core)
            env_records, output_records = [current_env], [previous]
            for _ in range(20):
                feed = mapping((single_env, last_action, core), (current_env, previous.action, current_core))
                # Exclude TF's stateful sampler; sample the same categorical distribution with saved RNG.
                policy, baseline, q_aux, current_core = session.run(
                    (single_output.policy, single_output.baseline, single_output.q_aux, single_core), feed)
                assert np.isfinite(policy).all() and np.isfinite(baseline).all() and np.isfinite(q_aux).all()
                actions = sample(policy, action_rng)
                previous = AgentOutput(actions, policy, baseline, q_aux)
                obs, reward, done, _, _ = step(actions[0])
                if done:
                    obs = env.reset()
                current_env = env_value(obs, reward, done)
                env_records.append(current_env)
                output_records.append(previous)
            batch_values = nest.map_structure(lambda *xs: np.stack(xs), *env_records)
            action_values = nest.map_structure(lambda *xs: np.stack(xs), *output_records)
            cached_feed = mapping((batch_env, batch_output, batch_core), (batch_values, action_values, first_core))
            count = int(session.run(update, cached_feed))
            REPORT['optimizer_calls'] += 1
            REPORT['learner_consumed_samples'] += 20
            assert_finite_loss_log()
            counters.append(count)
            assert all(np.isfinite(v).all() for v in session.run(variables))
            save_report()
        REPORT['collection_and_three_updates_seconds'] = time.monotonic() - training_started
        after = session.run(tf.trainable_variables())
        check('trainable_parameters_changed', any(not np.array_equal(a, b) for a, b in zip(before, after)))
        REPORT['upstream_global_steps_after_updates'] = counters
        REPORT['counter_interpretation'] = 'Upstream global_step includes optimizer increment plus consumed samples; never use it as exact environment count.'
        saver.save(session, str(OUT / 'learner'))
        saved_values = session.run(variables)
        session.run(update, cached_feed)
        REPORT['optimizer_calls'] += 1
        REPORT['learner_consumed_samples'] += 20
        assert_finite_loss_log()
        reference_variables = session.run(variables)
        assert all(np.isfinite(v).all() for v in reference_variables)

    # Restore into a fresh session, so this is not merely undoing in-memory assignments.
    with tf.Session(config=config) as session:
        saver.restore(session, str(OUT / 'learner'))
        restored_values = session.run(variables)
        check('all_global_variables_restored', all(np.array_equal(a, b) for a, b in zip(saved_values, restored_values)))
        session.run(update, cached_feed)
        REPORT['optimizer_calls'] += 1
        REPORT['learner_consumed_samples'] += 20
        assert_finite_loss_log()
        replay_values = session.run(variables)
        assert all(np.isfinite(v).all() for v in replay_values)
        max_error = max(float(np.max(np.abs(a.astype(np.float64) - b.astype(np.float64))))
                        for a, b in zip(reference_variables, replay_values))
        check('fixed_batch_update_replayed', max_error <= 1e-6, {'max_abs_error': max_error, 'tolerance': 1e-6})
    losses = (OUT / 'loss_debug.txt').read_text().lower()
    check('loss_log_finite', 'nan' not in losses and 'inf' not in losses)
    check('budget_exact', REPORT['environment_steps'] == 160 and
          REPORT['learner_consumed_samples'] == 100 and REPORT['optimizer_calls'] == 5)
    REPORT['checkpoint_bytes'] = sum(p.stat().st_size for p in OUT.glob('learner*'))
    REPORT['status'] = 'passed'


try:
    main()
except Exception as error:
    REPORT['status'] = 'failed'
    REPORT['error'] = repr(error)
    REPORT['traceback'] = traceback.format_exc()
    traceback.print_exc()
    sys.exit(1)
finally:
    save_report()
