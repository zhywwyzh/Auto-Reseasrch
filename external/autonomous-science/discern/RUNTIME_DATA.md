# Runtime inputs versus construction sources

Evaluate the prepared worlds directly. Do not run world builders merely to install
this release: builders reconstruct benchmark conditions and can overwrite inputs.

## Included in local staging

`verification/runtime_files.csv` records each packaged file's relative path, role,
size, and SHA-256. Inputs are selected from the manifests referenced by the original
authority index, not from all experimental runs. This includes both physics tracks.
Abandoned worlds and the superseded nuclear-decay near-field run are not selected.

Task inputs, per-task metadata, evidence dossiers, grading references, required
ClinVar panel databases and the Lung prediction model/covariance are staged.
Their presence locally does not itself establish redistribution permission.
Gold files are evaluator resources and must never be mounted in the agent sandbox.

## Runtime references

ClinVar requires a GRCh38 FASTA and its `.fai` index. Both are staged under
`resources/` from the reference used locally, with checksums in the runtime index.
Set `DISCERN_HG38` to override the default `resources/hg38.fa`. This resource is
required for evaluation, not just construction; a generic GRCh38 download is not
automatically byte-identical to this reference.

The protein tasks require the ESM2 150M and 650M checkpoints and their contact
regression weights. These specific files are staged under `resources/torch/hub`;
other model caches are not included. `DISCERN_TORCH_HUB` overrides this location.
These checkpoints and the CADD panel are excluded from Git/upload selection.
Install them from their official upstream endpoints using the checksum-verified
commands in `EXTERNAL_RUNTIME.md`. They remain in the runtime index because that
index describes dependencies, not just files distributed in the repository.
Official Meta model cards label both ESM-2 models MIT licensed; CADD's own use
terms remain controlling. Other reference-resource terms are separate.

Use `DISCERN_SANDBOX_PYTHON` for the scientific Python environment. Task-specific
dependencies include pysam, Biopython, pyBigWig, Scanpy, deepTools, MACS3, and the
protein language-model dependencies where requested by the task. The original
`environment/requirements.txt` covers figure reproduction only; it is not a full
live-runtime lockfile. Linux bubblewrap isolation is required, and must fail closed.

## Link-only construction sources

Full upstream count matrices, BAM/BigWig collections, source study archives,
ThermoML source archives, and full multiyear nuclear-decay measurements are not
included merely because builders used them. Source links and terms remain in
`DATA_SOURCES_AND_LICENSES.md`. Prepared benchmark inputs derived from those sources
still require the applicable permissions and attribution.

## Release gates

Before upload: resolve redistribution terms for staged inputs (especially physics
and restricted reference resources), verify exact runtime dependencies, perform
an anonymity/credential scan, and test input loading in isolated environments.
No live agent/API execution or complete runtime certification has been performed
for this update. Historical clean-room replay validation is a separate claim.

The local Python 3.11 CPU smoke environment now passes imports and representative
input-loading checks in sealed sandboxes for all 46 selected manifests. Reproduce
with `python check_runtime_smoke.py`; see `verification/runtime_smoke.json` for
scope and per-manifest outcomes. Versions are pinned in
`environment/runtime-smoke-requirements.txt`; CPU PyTorch wheels use the official
PyTorch CPU index. This is a packaging test, not a benchmark rerun or proof that
every task's complete software workflow executes successfully.
