FROM tensorflow/tensorflow:1.15.5-py3@sha256:181ff142e73ed8efe350f49288c7b0f5681fde66534a76d8de4fc75d4e30d571
ENV PYTHONDONTWRITEBYTECODE=1 MPLBACKEND=Agg OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=1 TF_CPP_MIN_LOG_LEVEL=2
COPY requirements.in /tmp/ucs-requirements.in
COPY environment.freeze.txt /tmp/ucs-constraints.txt
RUN python -m pip install --no-cache-dir -c /tmp/ucs-constraints.txt -r /tmp/ucs-requirements.in && python -m pip check
WORKDIR /run
