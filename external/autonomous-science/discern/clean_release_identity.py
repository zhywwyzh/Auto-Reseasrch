"""Redact identifying metadata, with backups outside the release and invariants.

No scores, scientific observations, alignment records, or archive member payloads
are changed. Pass account names at execution time; they are not saved in the log.
This is not a substitute for redistribution review or a complete secret audit.
"""
import argparse
import copy
import csv
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

ROOT = Path(__file__).resolve().parent

def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''): h.update(block)
    return h.hexdigest()

def tar_payload(path):
    result=[]
    with tarfile.open(path,'r:gz') as tf:
        for m in tf:
            h=hashlib.sha256()
            if m.isfile():
                with tf.extractfile(m) as f:
                    for b in iter(lambda:f.read(1024*1024),b''): h.update(b)
            result.append((m.name,m.type.decode(),m.size,m.mode,m.linkname,h.hexdigest()))
    return result

def bam_payload(path):
    import pysam
    h=hashlib.sha256(); count=0
    with pysam.AlignmentFile(path,'rb',check_sq=False) as f:
        refs=list(zip(f.references,f.lengths))
        for record in f.fetch(until_eof=True):
            h.update(record.to_string().encode()+b'\n'); count+=1
    return {'alignments':count,'records_sha256':h.hexdigest(),'references':refs}

def numeric_tree(x):
    if isinstance(x,dict): return {k:numeric_tree(v) for k,v in x.items()}
    if isinstance(x,list): return [numeric_tree(v) for v in x]
    return '<text>' if isinstance(x,str) else x

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--redact-name',action='append',required=True)
    ap.add_argument('--backup-dir',type=Path,required=True)
    args=ap.parse_args()
    backup=args.backup_dir.resolve()
    if backup.is_relative_to(ROOT): raise SystemExit('Backups must be outside release')
    backup.mkdir(parents=True,exist_ok=True)
    names=args.redact_name
    def redact(s):
        for name in names: s=s.replace(name,'anonymous')
        return s
    def preserve(p):
        dst=backup/p.relative_to(ROOT)
        if dst.exists(): raise RuntimeError('Refusing to overwrite an existing backup')
        dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    ledger=ROOT/'verification/identity_cleanup.json'
    log=json.loads(ledger.read_text()) if ledger.exists() else []
    def record(p,before,kind,proof):
        log.append({'path':str(p.relative_to(ROOT)),'before_sha256':before,
                    'after_sha256':sha(p),'kind':kind,'invariant':proof})
        ledger.write_text(json.dumps(log,indent=2)+'\n')
    paths=sorted(set(subprocess.check_output(
        ['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()))
    for rel in paths:
        p=ROOT/rel
        if p.is_symlink() or not p.is_file():continue
        if p.suffix in {'.json','.py','.txt','.md','.csv','.tsv','.sh','.xml','.yaml','.yml'}:
            try: original=p.read_text()
            except UnicodeError:continue
            clean=redact(original)
            if clean==original:continue
            if p.suffix=='.json':
                obj=json.loads(original)
                def redact_values(x):
                    if isinstance(x,dict):return {k:redact_values(v) for k,v in x.items()}
                    if isinstance(x,list):return [redact_values(v) for v in x]
                    return redact(x) if isinstance(x,str) else x
                cleaned=redact_values(obj)
                if obj==cleaned:continue
                assert numeric_tree(obj)==numeric_tree(cleaned)
                clean=json.dumps(cleaned,indent=1,ensure_ascii=False)+'\n'
            before=sha(p);preserve(p);p.write_text(clean)
            record(p,before,'text_identity_redaction','structure and non-string values unchanged')
        elif rel.endswith(('.tar.gz','.tgz')):
            with tarfile.open(p,'r:gz') as tf:
                dirty=any(any(n in str((m.uname,m.gname,m.pax_headers)) for n in names) for m in tf)
            if not dirty:continue
            proof=tar_payload(p);before=sha(p);preserve(p)
            with tempfile.TemporaryDirectory(prefix='discern_tar_') as tmp:
                out=Path(tmp)/'clean.tar.gz'
                with tarfile.open(p,'r:gz') as src,out.open('wb') as raw:
                    with gzip.GzipFile(filename='',mode='wb',fileobj=raw,mtime=0) as gz:
                        with tarfile.open(fileobj=gz,mode='w',format=tarfile.PAX_FORMAT) as dst:
                            for m in src:
                                clean=copy.copy(m);clean.uid=clean.gid=0
                                clean.uname=clean.gname='anonymous'
                                clean.pax_headers={k:redact(v) for k,v in m.pax_headers.items()
                                    if k not in ('uid','gid','uname','gname')}
                                if m.isfile():
                                    with src.extractfile(m) as f:dst.addfile(clean,f)
                                else:dst.addfile(clean)
                assert tar_payload(out)==proof,'Archive payload changed'
                shutil.copyfile(out,p)
            record(p,before,'archive_ownership',{'member_count':len(proof),
                'payload_manifest_sha256':hashlib.sha256(json.dumps(proof).encode()).hexdigest()})
        elif p.suffix=='.bam':
            import pysam
            with pysam.AlignmentFile(p,'rb',check_sq=False) as f:header=str(f.header)
            clean=redact(header)
            if clean==header:continue
            before=sha(p);proof=bam_payload(p);preserve(p)
            index=Path(str(p)+'.bai'); index_before=sha(index) if index.exists() else None
            if index.exists():preserve(index)
            with tempfile.TemporaryDirectory(prefix='discern_bam_') as tmp:
                out=Path(tmp)/'clean.bam'
                with pysam.AlignmentFile(p,'rb',check_sq=False) as src:
                    with pysam.AlignmentFile(out,'wb',text=clean) as dst:
                        for alignment in src.fetch(until_eof=True):dst.write(alignment)
                assert bam_payload(out)==proof,'Alignment payload changed'
                pysam.index(str(out))
                shutil.copyfile(out,p);shutil.copyfile(str(out)+'.bai',index)
            record(p,before,'bam_program_header',proof)
            record(index,index_before,'rebuilt_bam_index','index rebuilt for header-redacted BAM')
    # Update only inventory fingerprints; scores and adjudication tables untouched.
    inventory=ROOT/'verification/runtime_files.csv'
    with inventory.open() as f: rows=list(csv.DictReader(f))
    changed={r['path'] for r in log}
    for row in rows:
        if row['path'] in changed:
            p=ROOT/row['path'];row['sha256']=sha(p);row['bytes']=p.stat().st_size
    with inventory.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['path','role','bytes','sha256'],lineterminator='\n')
        w.writeheader();w.writerows(rows)
    print(json.dumps({'logged_changes':len(log),'kinds':{k:sum(r['kind']==k for r in log)
        for k in sorted({r['kind'] for r in log})}},indent=2))

if __name__=='__main__':main()
