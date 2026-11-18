# Reviewer environment

The recorded DISCERN artifact and paper-output reproduction utilities use a
small Python environment.

Validated release-construction runtime:

- CPython 3.13.5
- Linux x86_64

Install the reviewer dependencies from the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r environment/requirements.txt
```

The requirements file is intentionally minimal rather than a development
environment `pip freeze`. It contains only third-party distributions imported
by the reviewer-facing aggregation, verification, table, and figure scripts.

Repository-local helper modules are shipped in the repository root and do not
require separate installation.

For commands used to regenerate the frozen paper artifacts, see
`REPRODUCIBILITY.md`.
