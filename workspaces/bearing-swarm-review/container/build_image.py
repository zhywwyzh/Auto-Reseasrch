#!/usr/bin/env python3
"""Build the locked TR-002 environment using resource-capped Docker 28 legacy RUNs."""
import argparse
import os
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tag", default="tr002-numerics:locked")
    args = parser.parse_args()
    for path in [HERE / "requirements.lock", HERE / "julia/Manifest.toml"]:
        if not path.is_file():
            raise SystemExit(f"Missing dependency lock: {path}")
    env = dict(os.environ, DOCKER_BUILDKIT="0")
    subprocess.run(["docker", "build", "--platform=linux/amd64", "--memory=4g", "--memory-swap=4g",
                    "--cpu-period=100000", "--cpu-quota=200000", "--build-arg",
                    "RESOLVE_DEPENDENCIES=0", "--tag", args.tag, str(HERE)],
                   env=env, check=True)


if __name__ == "__main__":
    main()
