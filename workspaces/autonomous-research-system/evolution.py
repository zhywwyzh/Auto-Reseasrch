#!/usr/bin/env python3
"""DGM-inspired archive + autoresearch-style fixed evaluation and promotion.

The outer kernel never evaluates its own promises as evidence. Candidate code runs
in a filesystem/network sandbox. The selected parent's strategy constructs the
next mutation request. All model calls and failed candidates remain in the ledger.
"""
import argparse
import contextlib
import fcntl
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import sqlite3
import subprocess
import sys
import time

import ars
import evolution_benchmark as benchmark
import strategy_runtime as strategy

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE / 'runs/evolution'
SCHEMA = {'type': 'object', 'additionalProperties': False,
          'required': ['hypothesis', 'files'], 'properties': {
              'hypothesis': {'type': 'string'},
              'files': {'type': 'object', 'additionalProperties': False, 'required': list(strategy.FILES),
                        'properties': {name: {'type': 'string'} for name in strategy.FILES}}}}


def source_size(directory):
    return sum((Path(directory) / name).stat().st_size for name in strategy.FILES)


class Archive:
    def __init__(self, root=DEFAULT_ROOT):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in ('versions', 'operations'):
            (self.root / name).mkdir(exist_ok=True)
        self.db = sqlite3.connect(self.root / 'archive.sqlite3', timeout=20, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          PRAGMA journal_mode=WAL;
          CREATE TABLE IF NOT EXISTS versions(id TEXT PRIMARY KEY,parent TEXT,digest TEXT,origin TEXT,
            hypothesis TEXT,evaluation TEXT,viable INTEGER,bytes INTEGER,created_at TEXT);
          CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY,parent TEXT,state TEXT,created_at TEXT,receipt TEXT);
          CREATE TABLE IF NOT EXISTS events(seq INTEGER PRIMARY KEY,type TEXT,payload TEXT,created_at TEXT);
          CREATE TABLE IF NOT EXISTS settings(id INTEGER PRIMARY KEY CHECK(id=1),config TEXT,calls INTEGER DEFAULT 0);
        ''')

    def close(self):
        self.db.close()

    @contextlib.contextmanager
    def lock(self):
        with (self.root / 'controller.lock').open('a+') as f:
            try:
                fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise ValueError('System improvement controller is already running')
            yield

    def event(self, kind, value):
        self.db.execute('INSERT INTO events(type,payload,created_at) VALUES(?,?,?)', (kind, ars.dump(value), ars.now()))

    def config(self):
        row = self.db.execute('SELECT * FROM settings').fetchone()
        if row is None:
            raise ValueError('Initialize the improvement budget first')
        return json.loads(row['config']), row['calls']

    def configure(self, max_calls=2, timeout=300, model='', auto_promote=True):
        if type(max_calls) is not int or max_calls < 1 or type(timeout) is not int or timeout < 1:
            raise ValueError('System optimization requires a positive explicit call cap and timeout')
        cfg = {'max_calls': max_calls, 'timeout': timeout, 'model': model,
               'codex_bin': shutil.which('codex'), 'auto_promote': auto_promote,
               'benchmark_sha256': benchmark.contract_hash(), 'stopped': False}
        if self.db.execute('SELECT 1 FROM settings').fetchone():
            raise ValueError('Already initialized; budget is never silently reset')
        self.db.execute('INSERT INTO settings(id,config) VALUES(1,?)', (ars.dump(cfg),))
        self.event('initialized', cfg)

    def version(self, ident):
        row = self.db.execute('SELECT * FROM versions WHERE id=?', (ident,)).fetchone()
        if row is None:
            raise ValueError('Unknown version')
        out = dict(row); out['evaluation'] = json.loads(out['evaluation'])
        directory = self.root / 'versions' / ident
        if strategy.fingerprint(directory) != out['digest']:
            raise ValueError('Archived source was modified')
        return out

    def active(self):
        p = self.root / 'active.json'
        if not p.exists():
            return None
        release = ars.read_json(p)
        version = self.version(release['version'])
        if release['digest'] != version['digest']:
            raise ValueError('Release digest mismatch')
        return version

    def register(self, directory, parent=None, origin='manual', hypothesis='', ident=None):
        if parent:
            self.version(parent)
        digest = strategy.fingerprint(directory)
        ident = ident or ars.uid()
        if self.db.execute('SELECT 1 FROM versions WHERE id=?', (ident,)).fetchone():
            return self.version(ident)
        target = self.root / 'versions' / ident
        target.mkdir(exist_ok=True)
        for name in strategy.FILES:
            raw = (Path(directory) / name).read_bytes()
            compile(raw, name, 'exec')
            (target / name).write_bytes(raw)
        evaluation = benchmark.evaluate(target)
        ars.atomic_json(target / 'evaluation.json', evaluation)
        self.db.execute('INSERT INTO versions VALUES(?,?,?,?,?,?,?,?,?)',
                        (ident, parent, digest, origin, hypothesis, ars.dump(evaluation), int(evaluation['viable']), source_size(target), ars.now()))
        self.event('candidate.evaluated', {'version': ident, 'parent': parent, 'origin': origin,
                                        'correct': evaluation['correct'], 'total': evaluation['total'], 'viable': evaluation['viable']})
        return self.version(ident)

    def promote(self, ident, initial=False):
        candidate = self.version(ident)
        incumbent = self.active()
        cfg, _ = self.config()
        if cfg['benchmark_sha256'] != benchmark.contract_hash():
            raise ValueError('Frozen evaluator changed; start a new benchmark campaign')
        # Re-evaluate the exact candidate and incumbent immediately before deployment.
        evaluation = benchmark.evaluate(self.root / 'versions' / ident)
        if incumbent:
            old = benchmark.evaluate(self.root / 'versions' / incumbent['id'])
            accepted, reason = benchmark.promotion(evaluation, old, candidate['bytes'], incumbent['bytes'])
        else:
            accepted = initial and evaluation['viable']
            reason = 'initial measured baseline; no improvement claimed'
        if not accepted:
            self.event('candidate.retained', {'version': ident, 'reason': reason})
            return {'promoted': False, 'reason': reason}
        release = {'version': ident, 'digest': candidate['digest'], 'parent': candidate['parent'],
                   'previous': incumbent['id'] if incumbent else None, 'deployed_at': ars.now(),
                   'benchmark_sha256': benchmark.contract_hash(), 'reason': reason}
        ars.atomic_json(self.root / 'active.json', release)
        self.event('release.promoted', release)
        return {'promoted': True, **release}

    def rollback(self, reason):
        release = ars.read_json(self.root / 'active.json')
        previous = release.get('previous')
        if not previous:
            raise ValueError('No previous release available')
        version = self.version(previous)
        restored = {'version': previous, 'digest': version['digest'], 'parent': version['parent'],
                    'previous': None, 'deployed_at': ars.now(), 'reason': reason,
                    'benchmark_sha256': benchmark.contract_hash()}
        ars.atomic_json(self.root / 'active.json', restored)
        self.event('release.rolled_back', {'from': release['version'], **restored})
        return restored

    def choose_parent(self):
        rows = [dict(r) for r in self.db.execute('SELECT * FROM versions WHERE viable=1 ORDER BY created_at')]
        if not rows:
            raise ValueError('No viable parent with self-modification capability')
        weights = []
        for row in rows:
            evaluation = json.loads(row['evaluation'])
            children = self.db.execute('SELECT COUNT(*) FROM versions WHERE parent=?', (row['id'],)).fetchone()[0]
            weights.append((0.05 + evaluation['correct'] / evaluation['total']) / (1 + children))
        return random.choices(rows, weights=weights, k=1)[0]['id']

    def reserve(self, feedback=None, parent=None):
        cfg, calls = self.config()
        if cfg['stopped'] or calls >= cfg['max_calls']:
            return None
        if cfg['benchmark_sha256'] != benchmark.contract_hash():
            raise ValueError('Frozen evaluator changed')
        if self.db.execute("SELECT 1 FROM operations WHERE state IN ('RESERVED','RUNNING','UNKNOWN')").fetchone():
            raise ValueError('An existing model operation must be reconciled first')
        parent = parent or self.choose_parent()
        version = self.version(parent)
        source = self.root / 'versions' / parent
        context = {'parent': parent, 'hypothesis': version['hypothesis'],
                   'files': {name: (source / name).read_text() for name in strategy.FILES},
                   'failures': version['evaluation']['development_failures'],
                   'capabilities': version['evaluation']['capabilities'], 'incidents': feedback or [],
                   'scope': 'Improve general recovery, stage ordering, memory retrieval and your own improvement guidance.'}
        prompt = strategy.invoke(source, [{'function': 'improvement_prompt', 'args': [context]}])[0]
        if not isinstance(prompt, str) or not 40 <= len(prompt) <= 200000:
            raise ValueError('Parent lost self-modification prompt interface')
        ident = ars.uid(); opdir = self.root / 'operations' / ident; opdir.mkdir()
        ars.atomic_json(opdir / 'request.json', {'id': ident, 'parent': parent, 'config': cfg, 'prompt': prompt})
        self.db.execute('BEGIN IMMEDIATE')
        try:
            # Recheck inside the reservation transaction, preserving all failed/unknown costs.
            latest, used = self.config()
            if latest['stopped'] or used >= latest['max_calls']:
                self.db.rollback(); return None
            self.db.execute('INSERT INTO operations VALUES(?,?,?,?,NULL)', (ident, parent, 'RESERVED', ars.now()))
            self.db.execute('UPDATE settings SET calls=calls+1')
            self.event('model.reserved', {'operation': ident, 'parent': parent, 'call_slot': used + 1})
            self.db.commit()
        except BaseException:
            self.db.rollback(); raise
        return ident

    def reconcile(self):
        for row in self.db.execute("SELECT * FROM operations WHERE state IN ('RESERVED','RUNNING','UNKNOWN')").fetchall():
            opdir = self.root / 'operations' / row['id']
            if (opdir / 'receipt.json').exists():
                receipt = ars.read_json(opdir / 'receipt.json')
                if receipt.get('id') != row['id']:
                    raise ValueError('Mutation receipt identity mismatch')
                status = 'FAILED'
                if receipt.get('success'):
                    try:
                        result = ars.read_json(opdir / 'result.json')
                        if set(result) != {'hypothesis', 'files'} or set(result['files']) != set(strategy.FILES):
                            raise ValueError('Candidate output outside allowed strategy surface')
                        generated = opdir / 'candidate'; generated.mkdir(exist_ok=True)
                        for name, text in result['files'].items():
                            if not isinstance(text, str) or len(text.encode()) > 160000:
                                raise ValueError('Candidate source invalid')
                            (generated / name).write_text(text)
                        if strategy.fingerprint(generated) == self.version(row['parent'])['digest']:
                            raise ValueError('No source change; unchanged output is not self-modification')
                        version = self.register(generated, row['parent'], 'autonomous-model', result['hypothesis'], row['id'])
                        status = 'EVALUATED'
                        cfg, _ = self.config()
                        if cfg['auto_promote'] and not cfg['stopped'] and self.active()['id'] != version['id']:
                            self.promote(version['id'])
                    except (ValueError, SyntaxError, OSError, TypeError, KeyError) as exc:
                        receipt['rejection'] = str(exc)
                self.db.execute('UPDATE operations SET state=?,receipt=? WHERE id=?', (status, ars.dump(receipt), row['id']))
                self.event('model.finalized', {'operation': row['id'], 'state': status, 'receipt': receipt})
            elif any(ars.same_process(ars.read_json(opdir / name)) for name in ('supervisor.json', 'child.json') if (opdir / name).exists()):
                self.db.execute("UPDATE operations SET state='RUNNING' WHERE id=?", (row['id'],))
            else:
                self.db.execute("UPDATE operations SET state='UNKNOWN' WHERE id=?", (row['id'],))
                self.event('model.unknown', {'operation': row['id'], 'automatic_redispatch': False})

    def run(self, iterations=1, feedback=None):
        if not 1 <= iterations <= 20:
            raise ValueError('iterations must be between 1 and 20')
        with self.lock():
            self.reconcile()
            for _ in range(iterations):
                if self.db.execute("SELECT 1 FROM operations WHERE state IN ('RUNNING','UNKNOWN','RESERVED')").fetchone():
                    break
                ident = self.reserve(feedback)
                if ident is None:
                    break
                opdir = self.root / 'operations' / ident
                try:
                    self.db.execute('BEGIN IMMEDIATE')
                    try:
                        cfg, _ = self.config()
                        if cfg['stopped']:
                            ars.atomic_json(opdir / 'receipt.json', {'id': ident, 'success': False, 'error': 'Stopped before dispatch; reserved slot retained'})
                            self.db.commit(); self.reconcile(); break
                        child = subprocess.Popen([sys.executable, str(HERE / 'evolution.py'), '--root', str(self.root), '_activity', '--operation', ident],
                                                 stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
                        ars.atomic_json(opdir / 'supervisor.json', ars.process_identity(child.pid))
                        self.db.execute("UPDATE operations SET state='RUNNING' WHERE id=?", (ident,))
                        self.db.commit()
                    except BaseException:
                        self.db.rollback(); raise
                except OSError as exc:
                    ars.atomic_json(opdir / 'receipt.json', {'id': ident, 'success': False, 'error': str(exc)})
                while not (opdir / 'receipt.json').exists():
                    cfg, _ = self.config()
                    if cfg['stopped']:
                        ars.stop_activity(opdir); break
                    if child.poll() is not None:
                        break
                    time.sleep(0.2)
                self.reconcile()
        return self.status()

    def stop(self):
        cfg, _ = self.config(); cfg['stopped'] = True
        self.db.execute('UPDATE settings SET config=?', (ars.dump(cfg),))
        for row in self.db.execute("SELECT id FROM operations WHERE state IN ('RUNNING','RESERVED')"):
            ars.stop_activity(self.root / 'operations' / row['id'])
        self.event('user.stopped', {'budget_retained': True})

    def status(self):
        cfg, calls = self.config()
        versions = []
        for row in self.db.execute('SELECT * FROM versions ORDER BY created_at'):
            v = dict(row); v['evaluation'] = json.loads(v['evaluation']); versions.append(v)
        return {'config': cfg, 'calls': calls, 'active': self.active(), 'versions': versions,
                'operations': [dict(r) for r in self.db.execute('SELECT id,parent,state,created_at,receipt FROM operations')],
                'events': [dict(r) for r in self.db.execute('SELECT * FROM events ORDER BY seq DESC LIMIT 30')]}


def activity(root, ident):
    directory = Path(root) / 'operations' / ident
    request = ars.read_json(directory / 'request.json'); cfg = request['config']
    ars.atomic_json(directory / 'supervisor.json', ars.process_identity(os.getpid()))
    if (directory / 'receipt.json').exists():
        return
    receipt = {'id': ident, 'success': False, 'started_at': ars.now(), 'usage': {}, 'thread_id': None}
    started = time.monotonic()
    try:
        ars.atomic_json(directory / 'schema.json', SCHEMA)
        argv = [cfg['codex_bin'], '-c', 'approval_policy="never"', 'exec', '--sandbox', 'read-only', '--json',
                '--skip-git-repo-check', '--output-schema', str(directory / 'schema.json'),
                '--output-last-message', str(directory / 'result.json'), '-C', str(directory)]
        if cfg['model']:
            argv += ['--model', cfg['model']]
        argv += ['-']
        with (directory / 'events.jsonl').open('w') as out, (directory / 'stderr.log').open('w') as err:
            child = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=out, stderr=err, text=True)
            ars.atomic_json(directory / 'child.json', ars.process_identity(child.pid))
            try:
                child.communicate('Return only the required JSON with complete source files.\n' + request['prompt'], timeout=cfg['timeout'])
            except subprocess.TimeoutExpired:
                child.terminate()
                try:
                    child.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    child.kill(); child.wait()
                raise RuntimeError('System modification call timed out; call slot retained')
        if child.returncode:
            raise RuntimeError('System modification executor exit ' + str(child.returncode))
        if not (directory / 'result.json').exists():
            raise ValueError('No structured mutation result')
        receipt['success'] = True
    except Exception as exc:
        receipt['error'] = str(exc)[:2000]
    finally:
        if (directory / 'events.jsonl').exists():
            for line in (directory / 'events.jsonl').open():
                try:
                    event = json.loads(line)
                except ValueError:
                    continue
                if event.get('type') == 'turn.completed': receipt['usage'] = event.get('usage', {})
                if event.get('type') == 'thread.started': receipt['thread_id'] = event.get('thread_id')
        receipt.update(finished_at=ars.now(), wall_seconds=time.monotonic() - started)
        ars.atomic_json(directory / 'receipt.json', receipt)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root', type=Path, default=DEFAULT_ROOT)
    sub = p.add_subparsers(dest='command', required=True)
    init = sub.add_parser('init'); init.add_argument('--max-calls', type=int, default=2); init.add_argument('--timeout', type=int, default=300); init.add_argument('--model', default='')
    init.add_argument('--source', type=Path, default=HERE)
    run = sub.add_parser('run'); run.add_argument('--iterations', type=int, default=1); run.add_argument('--feedback', type=Path)
    sub.add_parser('status'); sub.add_parser('stop'); sub.add_parser('reconcile')
    register = sub.add_parser('register'); register.add_argument('--source', type=Path, required=True); register.add_argument('--parent'); register.add_argument('--hypothesis', default='Manual bootstrap improvement')
    promote = sub.add_parser('promote'); promote.add_argument('--version', required=True)
    rollback = sub.add_parser('rollback'); rollback.add_argument('--reason', required=True)
    worker = sub.add_parser('_activity'); worker.add_argument('--operation', required=True)
    args = p.parse_args()
    if args.command == '_activity':
        activity(args.root, args.operation); return
    archive = Archive(args.root)
    try:
        if args.command == 'init':
            with archive.lock():
                if not benchmark.evaluate(args.source)['viable']:
                    raise ValueError('Initial strategy failed isolated evaluation; budget not initialized')
                archive.configure(args.max_calls, args.timeout, args.model)
                initial = archive.register(args.source, hypothesis='Measured initial policy', origin='bootstrap')
                archive.promote(initial['id'], initial=True)
            out = archive.status()
        elif args.command == 'run': out = archive.run(args.iterations, ars.read_json(args.feedback) if args.feedback else None)
        elif args.command == 'stop': archive.stop(); out = archive.status()
        else:
            with archive.lock():
                if args.command == 'register': out = archive.register(args.source, args.parent, hypothesis=args.hypothesis)
                elif args.command == 'promote': out = archive.promote(args.version)
                elif args.command == 'rollback': out = archive.rollback(args.reason)
                elif args.command == 'reconcile': archive.reconcile(); out = archive.status()
                else: out = archive.status()
        print(json.dumps(out, ensure_ascii=False, indent=2))
    finally:
        archive.close()


if __name__ == '__main__':
    main()
