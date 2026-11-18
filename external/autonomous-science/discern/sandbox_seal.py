"""Sealed execution for the benchmark sandbox (addresses review point #1: the information boundary).

The agent's `run_python` code runs inside a bubblewrap (`bwrap`) namespace that can see ONLY:
  - a per-world working directory (writable) holding the world's input + allowed docs,
  - the Python interpreter prefixes (read-only), and required analysis software/models (read-only),
  - a private /tmp, /proc, /dev.
Everything else is invisible and there is NO network. So an agent CANNOT reach the manifest, the golden
TWAS truth, the graders, or any sibling world — the claimed boundary is now enforced by the OS, not by
"we didn't observe them looking."

Usage (per world):
    work, in_path = make_world_dir(agent_input, docs=[...])      # isolated dir with only allowed files
    out, ok = run_sealed(PY, header + code, work, timeout,
                         ro_paths=[software, model_db, cov])      # extra read-only mounts (TWAS)
The world's input is COPIED into `work`; point the sandbox header's read at `in_path`. Anything the agent
writes lands in `work` (persist it there for grading; it is not under the results tree's view).
"""
import os, sys, shutil, subprocess, tempfile, functools

BWRAP = shutil.which("bwrap")


def make_world_dir(input_path, docs=(), parent=None):
    """Create an isolated dir containing ONLY the world input + allowed docs (no sibling worlds).
    Returns (work_dir, sandbox_input_path). `parent` (if given) is where the dir is created so the
    artifacts persist for grading; else a fresh tmp dir."""
    work = tempfile.mkdtemp(prefix="gwsbx_", dir=parent) if parent else tempfile.mkdtemp(prefix="gwsbx_")
    base = os.path.basename(input_path)
    dst = os.path.join(work, base)
    if input_path and os.path.exists(input_path):
        if os.path.isdir(input_path):
            shutil.copytree(input_path, dst)
        else:
            shutil.copy2(input_path, dst)
    for d in docs:
        if d and os.path.exists(d):
            shutil.copy2(d, os.path.join(work, os.path.basename(d)))
    return work, dst


@functools.lru_cache(maxsize=8)
def _py_prefixes(py):
    """Interpreter prefixes to bind read-only so `py` + its site-packages import inside the sandbox.
    We keep BOTH the literal paths reported by the interpreter (e.g. /home/anonymous/miniconda3) and the
    realpath (e.g. /data/anonymous/miniconda3): the venv's symlink chain may resolve through either alias,
    and each destination path must exist inside the sealed namespace."""
    paths = []
    try:
        out = subprocess.run([py, "-c",
              "import sys;print(sys.prefix);print(sys.base_prefix);print(sys.executable)"],
              capture_output=True, text=True, timeout=30).stdout.split()
        for p in out:
            if not p:
                continue
            paths.append(p)                                     # literal (as the interpreter reports it)
            paths.append(os.path.realpath(p))                   # and its realpath alias
        paths.append(os.path.dirname(os.path.dirname(os.path.realpath(py))))
        # uv/venv launchers can name a literal interpreter alias that differs
        # from both sys.base_prefix and realpath(py). Bind that exact prefix too
        # so the launcher resolves, without exposing its enclosing home/cache.
        link = os.path.abspath(py)
        visited = set()
        while os.path.islink(link) and link not in visited:
            visited.add(link)
            target = os.readlink(link)
            link = os.path.normpath(os.path.join(os.path.dirname(link), target))
            paths.append(os.path.dirname(os.path.dirname(link)))
    except Exception:
        paths = [sys.prefix, sys.base_prefix, os.path.realpath(sys.base_prefix)]
    seen, keep = set(), []
    for p in paths:
        if p and p not in seen and os.path.isdir(p) and p not in ("/usr", "/etc", "/"):
            seen.add(p); keep.append(p)
    return tuple(keep)


def run_sealed(py, code, work_dir, timeout, ro_paths=(), env_extra=None):
    """Run the full program string `code` with interpreter `py`, sealed to `work_dir` + read-only
    interpreter/tool mounts. No network. Returns (stdout_or_error, ok)."""
    if not BWRAP:                                    # fail closed: refuse to run unsealed
        return "[sandbox_seal] bwrap not available -- refusing to run unsealed.", False
    args = [BWRAP, "--die-with-parent", "--unshare-all", "--new-session",
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp"]
    for p in ("/usr", "/etc", "/bin", "/sbin", "/lib", "/lib64", "/opt"):
        if os.path.exists(p):
            args += ["--ro-bind", p, p]
    # bind interpreter prefixes at their LITERAL paths (both /home and /data aliases), and tool/model
    # read-only mounts at both their literal and realpath locations so symlinked paths resolve.
    ro = list(_py_prefixes(py))
    for x in ro_paths:
        if x:
            ro += [x, os.path.realpath(x)]
    seen = set()
    for rp in ro:
        if rp and rp not in seen and os.path.exists(rp) and rp not in ("/usr", "/etc", "/", "/home", "/data"):
            args += ["--ro-bind", rp, rp]; seen.add(rp)
    args += ["--bind", work_dir, work_dir, "--chdir", work_dir]
    path_env = (env_extra or {}).get("PATH", "") + (":" if env_extra and env_extra.get("PATH") else "") \
               + f"{os.path.dirname(py)}:/usr/bin:/bin"
    args += ["--clearenv",
             "--setenv", "PATH", path_env,
             "--setenv", "HOME", work_dir,
             "--setenv", "TMPDIR", "/tmp",
             "--setenv", "MPLBACKEND", "Agg",
             "--setenv", "LANG", "C.UTF-8", "--setenv", "LC_ALL", "C.UTF-8"]
    for k, v in (env_extra or {}).items():
        if k != "PATH":
            args += ["--setenv", k, str(v)]
    args += [py, "-c", code]
    try:
        r = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        out = (r.stdout or "")[-4500:]
        if r.returncode != 0:
            return (out + "\n[error]\n" + (r.stderr or "")[-900:]), False
        return (out or "(no output)"), True
    except subprocess.TimeoutExpired:
        return "(timeout)", False
