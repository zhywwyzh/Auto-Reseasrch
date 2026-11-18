"""Frozen-safe prior-probe cache I/O, shared by every tracks/*/L3/prior_probe.py.

    from probe_cache_io import load_cache, save_cache
    cache = load_cache(RUN)          # frozen cache + this run's overlay entries, merged
    ...                              # probe; cache[f"{model}|{key}"] = {...}
    save_cache(RUN, cache)           # writes the cache; if it is a FROZEN read-only artifact, writes only the
                                     # NEW keys to results/new_models/probe_cache_overlay.json under the run's
                                     # repo-relative key -- the exact namespace grade_l3.py reads.

WHY (2026-09-05): scrna's cache is -r--r--r-- (frozen 2026-08-11). The scrna probe wrote to it directly and
crashed with PermissionError AFTER paying for the probes, losing them; every other track had its own copy of
the save logic, so the fix would have had to be made seven times. A new model must be able to run every
probe without anyone remembering which caches are frozen.
"""
import json, os

_REPO = os.path.dirname(os.path.abspath(__file__))
OVERLAY = os.path.join(_REPO, "results", "new_models", "probe_cache_overlay.json")


def _key(run_dir):
    return os.path.relpath(os.path.abspath(run_dir), _REPO).replace(os.sep, "/")


def _cache_path(run_dir):
    return os.path.join(run_dir, "prior_probe_cache.json")


def load_cache(run_dir):
    p = _cache_path(run_dir)
    cache = json.load(open(p)) if os.path.exists(p) else {}
    if os.path.exists(OVERLAY):
        for k, v in (json.load(open(OVERLAY)).get(_key(run_dir)) or {}).items():
            cache.setdefault(k, v)
    return cache


def save_cache(run_dir, cache):
    """Returns the path actually written."""
    p = _cache_path(run_dir)
    os.makedirs(run_dir, exist_ok=True)
    try:
        json.dump(cache, open(p, "w"), indent=1)
        return p
    except PermissionError:
        frozen = json.load(open(p)) if os.path.exists(p) else {}
        new = {k: v for k, v in cache.items() if k not in frozen}
        allo = json.load(open(OVERLAY)) if os.path.exists(OVERLAY) else {}
        allo.setdefault(_key(run_dir), {}).update(new)
        os.makedirs(os.path.dirname(OVERLAY), exist_ok=True)
        json.dump(allo, open(OVERLAY, "w"), indent=1)
        print(f"[probe_cache_io] {p} is frozen (read-only); wrote {len(new)} new entr{'y' if len(new)==1 else 'ies'} "
              f"to overlay under {_key(run_dir)!r}: {', '.join(sorted(new)) or '-'}")
        return OVERLAY
