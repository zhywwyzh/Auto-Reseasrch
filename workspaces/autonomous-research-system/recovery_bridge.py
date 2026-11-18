#!/usr/bin/env python3
"""Apply the current recovery control to an unchanged, hash-pinned executor.

Only recovery policy is overlaid. Scientific workflow/verifiers, model argv and
research code come from the saved runtime. Existing activities are never killed.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sqlite3
import sys

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def tick(directory):
    directory = Path(directory).resolve()
    db = sqlite3.connect(f'file:{directory}/state.sqlite3?mode=ro', uri=True)
    try:
        cfg = json.loads(db.execute('SELECT config FROM campaign').fetchone()[0])
    finally:
        db.close()
    pin = cfg['system_runtime_pin']
    root = Path(pin['code_root']).resolve()
    index = Path(pin['index']['path'])
    if hashlib.sha256(index.read_bytes()).hexdigest() != pin['index']['sha256']:
        raise ValueError('独立执行端版本索引不匹配')
    for name, digest in json.loads(index.read_text())['files'].items():
        source = (root / name).resolve()
        if not source.is_relative_to(root) or hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise ValueError('独立执行端代码发生漂移：' + name)
    # Pin takes precedence for all scientific definitions and validators. Load
    # only these explicit recovery modules from the current deployed system.
    import runtime_entry
    runtime_entry.install(root)
    control = load('recovery_control')
    result = control.reconcile_once(directory)
    result['executor_code_root'] = str(root)
    result['recovery_code_root'] = str(HERE)
    result['pinned_scientific_code_unchanged'] = True
    return result


if __name__ == '__main__':
    print(json.dumps(tick(sys.argv[1]), ensure_ascii=False))
