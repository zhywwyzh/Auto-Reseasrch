"""Tiny isolated invocation worker. Contains no test inputs or expected answers."""
import json
import resource
import sys

resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (256 * 1024**2, 256 * 1024**2))
resource.setrlimit(resource.RLIMIT_FSIZE, (1024**2, 1024**2))
sys.path.insert(0, '/candidate')
import runtime_policy
import research_strategy

FUNCTIONS = {name: getattr(runtime_policy, name) for name in ('classify', 'incident', 'frontier', 'select_memory')}
FUNCTIONS.update({name: getattr(research_strategy, name) for name in ('task_guidance', 'improvement_prompt')})
request = json.load(sys.stdin)
out = [FUNCTIONS[row['function']](*row.get('args', [])) for row in request]
print(json.dumps(out, ensure_ascii=False))
