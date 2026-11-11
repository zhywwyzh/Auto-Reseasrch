#!/usr/bin/env python3
"""Run TR-002 environment acceptance only, without mounting any other topic."""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import uuid

HERE = Path(__file__).resolve().parent
TOPIC = HERE.parent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--image", default="tr002-numerics:locked")
    args = parser.parse_args()
    tag = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:6]
    output = TOPIC / "runs" / ("container-smoke-" + tag)
    output.mkdir(parents=True)
    image = json.loads(subprocess.check_output(["docker", "image", "inspect", args.image]))[0]
    image_id = image["Id"]
    name = "tr002-smoke-" + tag.lower()
    command = ["docker", "create", "--name", name, "--label", "research.topic=TR-002",
               "--user", f"{os.getuid()}:{os.getgid()}", "--cpus", "2",
               "--memory", "4g", "--memory-swap", "4g", "--pids-limit", "256",
               "--network", "none", "--read-only", "--cap-drop", "ALL",
               "--security-opt", "no-new-privileges", "--init",
               "--tmpfs", "/tmp:rw,nosuid,size=512m,mode=1777",
               "--mount", f"type=bind,src={output},dst=/results",
               image_id]
    cid = subprocess.check_output(command).decode().strip()
    try:
        config = json.loads(subprocess.check_output(["docker", "inspect", cid]))[0]
        hc = config["HostConfig"]
        assert hc["NetworkMode"] == "none" and hc["ReadonlyRootfs"]
        assert not hc["Privileged"] and not hc.get("DeviceRequests")
        assert hc["Memory"] == hc["MemorySwap"] == 4 * 1024**3
        assert hc["NanoCpus"] == 2_000_000_000
        assert hc["PidsLimit"] == 256
        assert len(config["Mounts"]) == 1
        assert config["Mounts"][0]["Source"] == str(output)
        assert config["Mounts"][0]["Destination"] == "/results"
        with (output / "container.log").open("w") as log:
            attached = subprocess.run(["docker", "start", "--attach", cid], stdout=log,
                                      stderr=subprocess.STDOUT, timeout=360)
        state = json.loads(subprocess.check_output(["docker", "inspect", cid]))[0]["State"]
        receipt = {"topic": "TR-002", "scope": "environment acceptance; no UAV experiment",
                   "image_id": image_id, "image_size_bytes": image["Size"],
                   "container_id": cid, "command": command, "limits": {
                       "cpu_quota": 2, "memory_bytes": hc["Memory"], "swap_bytes": 0,
                       "network": "none", "readonly_rootfs": True, "pids": 256},
                   "state": state, "runtime_log": "container.log"}
        (output / "host-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
        assert attached.returncode == state["ExitCode"] == 0, (output / "container.log").read_text()
        assert not state["OOMKilled"]
        report = json.loads((output / "environment-smoke.json").read_text())
        assert report["status"] == "passed"
        print(json.dumps({"status": "passed", "output": str(output), "image_id": image_id,
                          "peak_memory_bytes": report["memory_peak_bytes"]}))
    finally:
        # This invocation owns this exact container; never remove other projects' resources.
        subprocess.run(["docker", "rm", "--force", cid], check=True, stdout=subprocess.DEVNULL)


if __name__ == "__main__":
    main()
