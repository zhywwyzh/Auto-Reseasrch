#!/usr/bin/env python3
"""Launch an isolated, frozen-source TR-002 pilot; retain failed attempts."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid

HERE=Path(__file__).resolve().parent
TOPIC=HERE.parent.parent


def main():
    config=json.loads((HERE/'protocol.json').read_text())
    meminfo=dict(line.split(':',1) for line in Path('/proc/meminfo').read_text().splitlines())
    available=int(meminfo['MemAvailable'].split()[0])*1024
    if available < 3*1024**3: raise SystemExit('Need at least 3 GiB MemAvailable for this 2 GiB capped pilot; no applications will be stopped.')
    if shutil.disk_usage(TOPIC).free < 30*1024**3: raise SystemExit('Need 30 GiB free disk under recorded pilot policy.')
    tag=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+uuid.uuid4().hex[:6]
    out=TOPIC/'runs'/('pilot-'+tag); source=out/'source'; source.mkdir(parents=True)
    for path in HERE.iterdir():
        if path.suffix in ['.py','.jl','.json']: shutil.copy2(path,source/path.name)
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(source.iterdir())}
    image=json.loads(subprocess.check_output(['docker','image','inspect','tr002-numerics:locked']))[0]
    command=['docker','create','--name','tr002-pilot-'+tag.lower(),'--label','research.topic=TR-002',
             '--user',f'{os.getuid()}:{os.getgid()}','--cpus','2','--memory','2g','--memory-swap','2g',
             '--pids-limit','256','--network','none','--read-only','--cap-drop','ALL',
             '--security-opt','no-new-privileges','--init','--tmpfs','/tmp:rw,nosuid,size=512m,mode=1777',
             '--mount',f'type=bind,src={source},dst=/experiment,readonly',
             '--mount',f'type=bind,src={out},dst=/results',image['Id'],'python','-u','/experiment/run.py','/results']
    cid=subprocess.check_output(command).decode().strip()
    receipt={'topic':'TR-002','image_id':image['Id'],'source_sha256':hashes,'host_memavailable_bytes':available,
             'host_cpu':subprocess.check_output(['lscpu']).decode(),'host_loadavg':Path('/proc/loadavg').read_text(),
             'command':command,'container_id':cid,'scope':config['scope']}
    print('OUTPUT '+str(out),flush=True)
    try:
        inspect=json.loads(subprocess.check_output(['docker','inspect',cid]))[0]
        hc=inspect['HostConfig']
        assert hc['Memory']==hc['MemorySwap']==2*1024**3 and hc['NanoCpus']==2_000_000_000
        assert hc['ReadonlyRootfs'] and hc['NetworkMode']=='none' and not hc['Privileged']
        assert len(inspect['Mounts'])==2 and not hc.get('DeviceRequests')
        receipt['host_config']=hc
        (out/'host-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        with (out/'container.log').open('w') as log:
            result=subprocess.run(['docker','start','--attach',cid],stdout=log,stderr=subprocess.STDOUT,
                                  timeout=config['resource_policy']['container_wall_timeout_seconds'])
        state=json.loads(subprocess.check_output(['docker','inspect',cid]))[0]['State']; receipt['state']=state
        receipt['source_unchanged']=all(hashlib.sha256((source/name).read_bytes()).hexdigest()==value for name,value in hashes.items())
        (out/'host-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
        assert receipt['source_unchanged']
        if result.returncode or state['ExitCode'] or state['OOMKilled']:
            raise SystemExit('Pilot failed; all evidence retained at '+str(out))
        print((out/'status.json').read_text(),flush=True)
    finally:
        subprocess.run(['docker','rm','--force',cid],check=True,stdout=subprocess.DEVNULL)


if __name__=='__main__': main()
