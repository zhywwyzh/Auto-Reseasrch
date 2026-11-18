"""Optional local compatibility modules; shared code ships without task data.

Existing executors keep their original modules in a Git-ignored directory.
This does not select a task, grant authority, or weaken its scientific checks.
"""
import ast
from pathlib import Path


def source_path(filename):
    public = Path(filename).resolve()
    private = public.parents[2] / '.local/system-modules' / public.name
    return private if private.is_file() else public


def source(filename):
    return source_path(filename).read_text(encoding='utf-8')


def apply(namespace):
    public = Path(namespace['__file__']).resolve()
    private = source_path(public)
    if private == public:
        return False
    root = public.parents[2]
    if not private.resolve().is_relative_to(root) or any(
            p.is_symlink() for p in (private, *private.parents) if p.is_relative_to(root)):
        raise ValueError('Local compatibility module cannot be a symlink')
    tree = ast.parse(private.read_text(encoding='utf-8'), filename=str(private))
    # Keep one CLI entry point. Original line numbers and public path semantics
    # remain intact for task-owned paths and existing executor integrations.
    tree.body = [node for node in tree.body if not (
        isinstance(node, ast.If) and '__name__' in ast.unparse(node.test))]
    namespace['__local_source__'] = str(private)
    exec(compile(tree, str(public), 'exec'), namespace)
    return True
