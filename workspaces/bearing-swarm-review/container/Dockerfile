# TR-002 numerical environment only. No repository, PDFs, host credentials or datasets.
FROM julia:1.11.3-bookworm@sha256:7e62d80dc9847456c44e7c7205e79d4eff5d807417ca391390b5d21eca40a485 AS julia_runtime
FROM python:3.10-slim-bookworm@sha256:5be5aaecb962a41567bc8041f1e9e3432cb085b037fe057f9a562630b2e4b370
COPY --from=julia_runtime /usr/local/julia /usr/local/julia
ENV PATH="/usr/local/julia/bin:${PATH}" \
    JULIA_DEPOT_PATH=/opt/julia-depot \
    JULIA_PROJECT=/opt/tr002-julia \
    JULIA_NUM_THREADS=1 \
    JULIA_NUM_PRECOMPILE_TASKS=1 \
    JULIA_PKG_PRECOMPILE_AUTO=0 \
    OPENBLAS_NUM_THREADS=1 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    PYTHONNOUSERSITE=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MPLCONFIGDIR=/tmp/matplotlib
# Only the explicit bootstrap build resolves versions. The default requires lock files.
ARG RESOLVE_DEPENDENCIES=0
COPY requirements.* /opt/tr002-python/
RUN if [ "$RESOLVE_DEPENDENCIES" = 1 ]; then \
      python -m pip install --no-cache-dir --only-binary=:all: --report /opt/python-install-report.json -r /opt/tr002-python/requirements.in; \
    else \
      python -m pip install --no-cache-dir --only-binary=:all: --require-hashes --report /opt/python-install-report.json -r /opt/tr002-python/requirements.lock; \
    fi
COPY julia/ /opt/tr002-julia/
RUN if [ "$RESOLVE_DEPENDENCIES" != 1 ]; then test -s /opt/tr002-julia/Manifest.toml; fi \
    && julia --startup-file=no --project=/opt/tr002-julia -e 'using Pkg; Pkg.instantiate(); Pkg.precompile()'
COPY smoke/ /opt/tr002-smoke/
ENV JULIA_DEPOT_PATH=/tmp/julia:/opt/julia-depot HOME=/tmp
USER 10001:10001
WORKDIR /tmp
CMD ["python", "/opt/tr002-smoke/check_environment.py", "/results"]
