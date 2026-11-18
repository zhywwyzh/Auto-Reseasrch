"""Read-only release audit, including compressed data and BAM program headers.

Reports filenames, never matched credentials or identity strings. Account names
are supplied at execution time and are not saved. No scan can prove absence of
all unknown identities or secrets. Git's file selection excludes ignored caches.
"""
import argparse
import collections
import gzip
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tarfile
import zipfile

ROOT=Path(__file__).resolve().parent
TEXT={'.json','.csv','.tsv','.md','.txt','.py','.sh','.yaml','.yml','.toml','.xml','.html'}
KEYS=re.compile(rb'(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}|hf_[A-Za-z0-9]{25,}|AKIA[A-Z0-9]{16}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--check-name',action='append',required=True)
    args=ap.parse_args();names=[v.encode() for v in args.check_name]
    paths=sorted(set(subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()))
    hits=collections.defaultdict(set);errors=[];counts=collections.Counter()
    def check(b,label,secret=False):
        if any(n in b for n in names):hits['identity'].add(label)
        if secret and KEYS.search(b):hits['credential_candidate'].add(label)
    def stream(f,label,secret=False):
        tail=b''
        while True:
            b=f.read(8*1024*1024)
            if not b:break
            check(tail+b,label,secret);tail=b[-256:]
    for rel in paths:
        p=ROOT/rel
        if p.is_symlink():
            if not p.resolve().is_relative_to(ROOT):hits['external_symlink'].add(rel)
            continue
        if not p.is_file():continue
        counts['files']+=1;counts['raw_bytes']+=p.stat().st_size
        with p.open('rb') as f:stream(f,rel,p.suffix in TEXT)
        try:
            if rel.endswith(('.tar.gz','.tgz')):
                counts['tar_archives']+=1
                with tarfile.open(p,'r:gz') as tf:
                    for m in tf:
                        counts['tar_members']+=1
                        check(str((m.name,m.uname,m.gname,m.pax_headers)).encode(),rel+'::metadata')
                        if m.isfile():
                            with tf.extractfile(m) as f:stream(f,rel+'::member',True)
            elif p.suffix=='.gz':
                counts['gzip_files']+=1
                with gzip.open(p,'rb') as f:stream(f,rel+'::decoded',True)
            elif p.suffix in ('.zip','.xlsx','.pt') and zipfile.is_zipfile(p):
                counts['zip_containers']+=1
                with zipfile.ZipFile(p) as z:
                    for m in z.infolist():
                        check(m.filename.encode()+m.comment,rel+'::metadata')
                        # Inspect document metadata and serialized model metadata;
                        # raw tensor storage is not deserialized or executed.
                        if m.filename.startswith(('docProps/','xl/')) or m.filename.endswith('.pkl'):
                            with z.open(m) as f:stream(f,rel+'::embedded',True)
            elif p.suffix=='.bam':
                import pysam
                counts['bam_headers']+=1
                with pysam.AlignmentFile(p,'rb',check_sq=False) as f:check(str(f.header).encode(),rel+'::header',True)
        except Exception as e:errors.append({'path':rel,'error':type(e).__name__})
    reviewed=[]
    # Confirmed false positives: GA4GH VRS allele IDs use URL-safe hashes that
    # can contain strings resembling provider token prefixes. Do not redact data.
    vcf='tracks/clinvar_acmg/L2/l2/resources/gnomad.panel.vcf.gz'
    candidate=vcf+'::decoded'
    if candidate in hits.get('credential_candidate',set()):
        h=hashlib.sha256()
        with (ROOT/vcf).open('rb') as f:
            for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
        if h.hexdigest()=='52457ffbe4d4d1b79e94ce874791b425752532adac95641f5a4438e89d8afdca':
            verified=True; count=0
            with gzip.open(ROOT/vcf,'rb') as f:
                for line in f:
                    if not KEYS.search(line):continue
                    fields=line.rstrip().split(b'\t')
                    if line.startswith(b'#') or len(fields)<8:
                        verified=False;break
                    if any(KEYS.search(v) for i,v in enumerate(fields) if i!=7):
                        verified=False;break
                    for value in fields[7].split(b';'):
                        if KEYS.search(value):
                            count+=1
                            if not value.startswith(b'VRS_Allele_IDs='):verified=False
            if verified and count:
                hits['credential_candidate'].remove(candidate)
                reviewed.append({'path':vcf,'reason':'matches confined to VRS_Allele_IDs in checksum-verified VCF','matching_fields':count,'sha256':h.hexdigest()})
    hits={k:v for k,v in hits.items() if v}
    config={}
    for key,expected in [('user.name','Anonymous'),('user.email','anonymous@example.com')]:
        v=subprocess.run(['git','config','--get',key],cwd=ROOT,capture_output=True,text=True).stdout.strip()
        config[key]=v==expected
    report={'scope':'current release worktree, not remote history or unknown identities',
        'counts':dict(counts),'findings':{k:sorted(v) for k,v in hits.items()},
        'reviewed_false_positives':reviewed,
        'inspection_errors':errors,'anonymous_commit_configuration':config}
    (ROOT/'verification/identity_audit.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if hits or errors or not all(config.values()):raise SystemExit(1)

if __name__=='__main__':main()
