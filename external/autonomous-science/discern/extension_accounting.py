"""Price final recorded task usage using the already-verified, dated rate cards.

No API calls. Astra uses the same conservative task-level long-context bound as
its approved leaderboard report. Do not allocate costs by total token share.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def task_usd(model, row):
    rates = json.loads((ROOT / f'results/new_models/pricing_{model}.json').read_text())
    ni = int(row.get('input_tokens', row.get('in', 0)))
    no = int(row.get('output_tokens', row.get('out', 0)))
    long = ni > rates.get('long_input_threshold', float('inf'))
    return (ni * rates['input_usd_per_mtok'] * (rates['long_input_multiplier'] if long else 1)
            + no * rates['output_usd_per_mtok'] * (rates['long_output_multiplier'] if long else 1)) / 1e6
