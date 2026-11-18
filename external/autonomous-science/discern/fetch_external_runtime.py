"""Fetch optional runtime references from their owners, never rebuild task worlds.

Downloads go to a caller-selected directory. Existing files are not overwritten.
ESM files are checked against the frozen runtime SHA-256 index; CADD is compared
as decompressed text because BGZF compression can differ between library versions.
No credential is required or read by this script.
"""
import argparse
import csv
import gzip
import hashlib
import importlib.util
from pathlib import Path
import tempfile
import urllib.request

ROOT = Path(__file__).resolve().parent
CADD_TEXT_SHA256 = 'e29cca63dad543179ced50314016f942b747a7b49b484ee153759bff3a5abd7b'


def digest(path, compressed=False):
    opener = gzip.open if compressed else open
    h = hashlib.sha256()
    with opener(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def fetch_esm(dest):
    indexed = {r['path']: r for r in csv.DictReader(
        (ROOT / 'verification/runtime_files.csv').open())}
    dest.mkdir(parents=True, exist_ok=True)
    for model in ('esm2_t30_150M_UR50D', 'esm2_t33_650M_UR50D'):
        for suffix, folder in (('.pt', 'models'), ('-contact-regression.pt', 'regression')):
            name = model + suffix
            expected = indexed['resources/torch/hub/checkpoints/' + name]['sha256']
            out = dest / name
            if out.exists():
                if digest(out) != expected:
                    raise RuntimeError('Existing file does not match frozen checksum: ' + name)
                print('VERIFIED ' + name, flush=True)
                continue
            url = 'https://dl.fbaipublicfiles.com/fair-esm/' + folder + '/' + name
            with tempfile.TemporaryDirectory(prefix='.esm-fetch-', dir=dest) as tmp:
                stage = Path(tmp) / name
                urllib.request.urlretrieve(url, stage)
                if digest(stage) != expected:
                    raise RuntimeError('Upstream file does not match frozen checksum: ' + name)
                stage.replace(out)
            print('FETCHED AND VERIFIED ' + name, flush=True)


def fetch_cadd(dest, accept):
    if not accept:
        raise SystemExit('Review https://cadd.bihealth.org/download and pass --accept-cadd-terms.')
    dest.mkdir(parents=True, exist_ok=True)
    out = dest / 'cadd.panel.tsv.gz'
    if out.exists() or Path(str(out) + '.tbi').exists():
        raise SystemExit('Use an empty output directory; existing CADD files are not overwritten.')
    builder = ROOT / 'tracks/clinvar_acmg/L2/build_l2_resources.py'
    spec = importlib.util.spec_from_file_location('cadd_builder', builder)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Run in a temporary cwd so htslib cannot leave its downloaded remote index
    # in the release root. Only the selected CADD subset and its index are kept.
    import os
    original = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='.cadd-fetch-', dir=dest) as tmp:
        tmp = Path(tmp).resolve()
        try:
            os.chdir(tmp)
            module.subset_cadd(str(tmp / out.name))
        finally:
            os.chdir(original)
        if digest(tmp / out.name, True) != CADD_TEXT_SHA256:
            raise RuntimeError('Reconstructed CADD text differs from frozen reference')
        for suffix in ('', '.tbi'):
            (tmp / (out.name + suffix)).replace(Path(str(out) + suffix))
    print('FETCHED CADD panel; upstream use terms still apply.', flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('resource', choices=['esm', 'cadd'])
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--accept-cadd-terms', action='store_true')
    args = parser.parse_args()
    dest = args.output.resolve()
    if args.resource == 'esm':
        fetch_esm(dest)
    else:
        fetch_cadd(dest, args.accept_cadd_terms)


if __name__ == '__main__':
    main()
