"""Regenerate current eight-model result figures and leaderboard numeric rows.

No regrading, API calls, source-world rebuilding, or original-table overwrites.
Uses finalized score/usage exports. The conditional Fable L2 row uses the
published five-track meta summary, not raw grades or fallback-replay estimates.
Historical six-model scripts remain available separately under reproduction/.
"""
import collections
import csv
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
OUT = ROOT / 'results/current_reproduction'
PROFILE = ROOT / 'Scientific Working Style Profile Draft'


def read(name):
    with (ROOT / name).open() as f: return list(csv.DictReader(f))


def load(name):
    return json.loads((ROOT / name).read_text())


def level_stats(values):
    return {'mean': statistics.mean(values),
            'sd': statistics.stdev(values) if len(values) > 1 else None,
            'tracks': len(values)}


def table():
    levels = [r for r in read('results/fig_data_levels_8models.csv') if not r['family']]
    usage = read('results/efficiency_by_model_8models.csv')
    token = {r['model']: r for r in read('results/token_efficiency_8models.csv')}
    assert len(levels) == 192 and len(usage) == 8
    rows = []
    for e in usage:
        model = e['model']
        stages = {}
        for level in ('L1', 'L2', 'L3'):
            values = [float(r['score']) * 100 / 3 for r in levels
                      if r['model'] == model and r['level'] == level]
            assert len(values) == 8
            stages[level] = level_stats(values)
        overall = float(e['score_chain_pct'])  # finalized hierarchical score
        total = int(e['total'])
        assert total == int(token[model]['total_tokens'])
        assert int(e['calls']) == int(token[model]['agent_api_calls'])
        rows.append(dict(model=model, kind='evaluated', stages=stages,
                         overall=overall, tokens_million=total / 1e6,
                         quality_per_million_tokens=overall / (total / 1e6),
                         usd_per_task=float(e['usd_per_assigned_task']),
                         usd_per_quality_point=float(e['usd_per_quality_point']),
                         agent_api_calls=int(e['calls'])))
    replay = load('results/model_reports/FALLBACK_REPLAY_claude-fable-5_to_claude-opus-5.json')
    costs = load('results/model_reports/FABLE_COST_claude-fable-5_and_opus-replay.json')
    rollup = load('results/model_reports/ROLLUP_claude-fable-5.json')
    c = costs['fable_to_opus_replay']
    rows.append(dict(model='claude-fable-5_to_claude-opus-5', kind='fallback_replay',
                     stages={level: dict(mean=replay['summary'][level]['mean_pct'],
                                        sd=replay['summary'][level]['sample_sd_pct'], tracks=8)
                             for level in ('L1', 'L2', 'L3')},
                     overall=c['quality_chain'], tokens_million=c['total_tokens'] / 1e6,
                     quality_per_million_tokens=c['quality_chain'] / (c['total_tokens'] / 1e6),
                     usd_per_task=c['usd_per_assigned_task'],
                     usd_per_quality_point=c['usd_per_quality_point'],
                     agent_api_calls=costs['direct_fable']['calls'] + costs['opus_fallback_increment']['calls']))
    rows.sort(key=lambda r: r['overall'], reverse=True)
    stages = {}
    for level, total in [('L1', 79), ('L2', 102), ('L3', 22)]:
        answers = [r for r in replay['cells'][level] if r['source'] == 'fable_answer']
        by_track = collections.defaultdict(list)
        for r in answers: by_track[r['track']].append(r['score'] * 100 / 3)
        if level == 'L2':
            meta = rollup['scores_hierarchical']['L2_meta']
            values = [v['conditional'] * 100 / 3 for v in meta['per_track'].values()]
            stages[level] = level_stats(values)
            stages[level]['mean'] = meta['conditional_answered_only'] * 100 / 3
            stages[level]['scope'] = 'published five-track conditional meta summary'
        else:
            stages[level] = level_stats([statistics.mean(v) for v in by_track.values()])
        stages[level]['coverage_pct'] = 100 * len(answers) / total
    c = costs['direct_fable']
    rows.append(dict(model='claude-fable-5', kind='conditional_not_ranked', stages=stages,
                     overall=None, tokens_million=c['total_tokens'] / 1e6,
                     quality_per_million_tokens=None, usd_per_task=c['usd_per_assigned_task'],
                     usd_per_quality_point=None, agent_api_calls=c['calls']))
    (OUT / 'table1_numeric.json').write_text(json.dumps(rows, indent=2) + '\n')
    flat = []
    for row in rows:
        r = {k: v for k, v in row.items() if k != 'stages'}
        for level, s in row['stages'].items():
            r.update({level + '_' + k: s.get(k) for k in ('mean', 'sd', 'coverage_pct')})
        flat.append(r)
    with (OUT / 'table1_numeric.csv').open('w') as f:
        w = csv.DictWriter(f, fieldnames=list(flat[0])); w.writeheader(); w.writerows(flat)
    return rows


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (ROOT / 'results/figures').mkdir(parents=True, exist_ok=True)
    (PROFILE / 'outputs/8models/figures').mkdir(parents=True, exist_ok=True)
    sources = [ROOT / 'results' / n for n in (
        'fig_data_levels_8models.csv', 'fig_data_l1_8models.csv', 'fig_data_l2_8models.csv',
        'fig_data_l3_8models.csv', 'efficiency_by_model_8models.csv', 'token_efficiency_8models.csv')]
    sources += list((PROFILE / 'outputs/8models/data').glob('*.csv'))
    sources += [ROOT / 'results/figures' / n for n in (
        'F03_chain_landscape_8models.csv', 'F06_prior_to_yield_8models.csv')]
    sources += [ROOT / 'results/model_reports' / n for n in (
        'ROLLUP_claude-fable-5.json', 'FALLBACK_REPLAY_claude-fable-5_to_claude-opus-5.json',
        'FABLE_COST_claude-fable-5_and_opus-replay.json')]
    digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    before = {str(p.relative_to(ROOT)): digest(p) for p in sources}
    rows = table()
    sys.path.insert(0, str(PROFILE))
    # Font caches contain machine-local paths and are not release artifacts.
    with tempfile.TemporaryDirectory(prefix='discern_plot_cache_') as cache:
        old_cache = os.environ.get('MPLCONFIGDIR')
        os.environ['MPLCONFIGDIR'] = cache
        try:
            import build_overview_stage_merged as merged
            import build_results_reframe_figures as figures
            merged.main()
            figures.states()
            figures.stability()
        finally:
            if old_cache is None: os.environ.pop('MPLCONFIGDIR', None)
            else: os.environ['MPLCONFIGDIR'] = old_cache
    assert before == {str(p.relative_to(ROOT)): digest(p) for p in sources}
    report = dict(passed=True, scope='current result Figures 3–5 and Table 1 numerical rows',
                  model_rows=len(rows), api_calls=0, source_sha256=before,
                  note='Uses finalized exports, not a raw-transcript regrade. PDF bytes may vary with plotting-library versions.')
    (ROOT / 'verification/current_reproduction.json').write_text(json.dumps(report, indent=2) + '\n')
    print('PASS: 10 table rows; result Figures 3–5; source inputs unchanged.')


if __name__ == '__main__': main()
