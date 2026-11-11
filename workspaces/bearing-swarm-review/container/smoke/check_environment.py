"""Isolated dependency, resource-limit, IO and known-answer solver acceptance checks."""
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.linalg import eigh

destination = Path(sys.argv[1])
destination.mkdir(parents=True, exist_ok=True)
started = time.monotonic()
assert os.geteuid() != 0
expected = {"numpy": "2.2.6", "scipy": "1.15.3", "matplotlib": "3.10.3", "h5py": "3.14.0"}
versions = {k: importlib.metadata.version(k) for k in expected}
assert versions == expected
subprocess.run([sys.executable, "-m", "pip", "check"], check=True)

limits = {name: (Path("/sys/fs/cgroup") / name).read_text().strip()
          for name in ["cpu.max", "memory.max", "memory.swap.max", "pids.max"]}
assert int(limits["memory.max"]) == 4 * 1024**3
assert limits["memory.swap.max"] == "0"
quota, period = map(int, limits["cpu.max"].split())
assert quota / period == 2
assert limits["pids.max"] == "256"
mounts = [line.split() for line in Path("/proc/mounts").read_text().splitlines()]
assert any(x[1] == "/" and "ro" in x[3].split(",") for x in mounts)
assert not Path("/var/run/docker.sock").exists()
assert not Path("/dev/nvidia0").exists()

matrix = np.arange(12, dtype=np.float64).reshape(3, 4)
vector = np.array([0.25, -2, 3, 1.5], dtype=np.float64)
with h5py.File(destination / "io-check.h5", "w") as f:
    f["matrix"] = matrix
with h5py.File(destination / "io-check.h5", "r") as f:
    np.testing.assert_array_equal(f["matrix"][:], matrix)
np.testing.assert_allclose(eigh(np.array([[1., -1.], [-1., 1.]]))[0], [0., 2.], atol=1e-12)

fixture = destination / "fixture.json"
fixture.write_text(json.dumps({"matrix": matrix.tolist(), "vector": vector.tolist()}))
julia_report = destination / "julia-smoke.json"
subprocess.run(["julia", "--startup-file=no", "--project=/opt/tr002-julia",
                "/opt/tr002-smoke/check_solver.jl", str(fixture), str(julia_report)],
               check=True, timeout=240)
solver = json.loads(julia_report.read_text())
np.testing.assert_allclose(solver["matrix_vector_product"], matrix @ vector, atol=1e-12)
assert solver["julia"] == "1.11.3"
assert solver["julia_threads"] == solver["blas_threads"] == 1

fig, ax = plt.subplots(figsize=(4, 3))
ax.plot([0, 1, 2], [0, 1, 4])
ax.set(title="Environment check (not research data)", xlabel="Input", ylabel="Squared input")
fig.savefig(destination / "plot-check.svg")
plt.close(fig)
assert (destination / "plot-check.svg").stat().st_size > 100
peak = Path("/sys/fs/cgroup/memory.peak")
report = {
    "status": "passed", "scope": "environment acceptance only; no UAV experiment",
    "python": platform.python_version(), "packages": versions,
    "python_distribution_versions": dict(sorted(
        (d.metadata["Name"], d.version) for d in importlib.metadata.distributions()
        if d.metadata.get("Name"))),
    "container_os": Path("/etc/os-release").read_text(),
    "uid": os.geteuid(), "resource_limits": limits,
    "memory_peak_bytes": int(peak.read_text()) if peak.exists() else None,
    "checks": ["imports and pip dependency consistency", "cgroup limits", "non-root and readonly rootfs",
               "HDF5 roundtrip", "SciPy symmetric eigensolver", "Python/Julia matrix layout roundtrip",
               "JuMP/SCS known-answer SDP", "single Julia/BLAS thread", "headless plotting"],
    "julia": solver, "elapsed_seconds": time.monotonic() - started,
    "limits": "Runtime includes startup/JIT; this is not a latency benchmark, strict certificate, or UAV validation.",
}
(destination / "environment-smoke.json").write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps({"status": "passed", "report": str(destination / "environment-smoke.json"),
                  "objective": solver["objective"], "peak_memory_bytes": report["memory_peak_bytes"]}))
