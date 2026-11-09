#!/usr/bin/env python3
"""Index the main local thesis by physical PDF page using Poppler."""
import hashlib
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "thesis-reference/theses/3120215520_答辩修改后论文0830.pdf"
OUTPUT = ROOT / "thesis-reference/notes/thesis-uav-crowdsensing"


def main():
    if not SOURCE.is_file():
        raise SystemExit(f"Missing local source: {SOURCE}")
    info = subprocess.run(
        ["pdfinfo", str(SOURCE)], check=True, capture_output=True, text=True
    ).stdout
    match = re.search(r"^Pages:\s+(\d+)\s*$", info, re.MULTILINE)
    if not match:
        raise SystemExit("Cannot determine the physical PDF page count")
    count = int(match[1])
    digest = hashlib.sha256(SOURCE.read_bytes()).hexdigest()

    def extract(number):
        result = subprocess.run(
            ["pdftotext", "-f", str(number), "-l", str(number), "-layout", str(SOURCE), "-"],
            check=True, capture_output=True, text=True,
        )
        # This PDF contains form feeds within pages. Splitting one full-text
        # extraction on form feeds would incorrectly turn 166 pages into 202.
        text = result.stdout.replace("\f", "").strip()
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        label = lines[-1] if lines and re.fullmatch(r"[IVXLCDM]+|\d+", lines[-1]) else None
        return {
            "pdf_page": number, "printed_page": label, "text": text,
            "warnings": list(dict.fromkeys(result.stderr.strip().splitlines())),
        }

    with ThreadPoolExecutor(max_workers=6) as pool:
        pages = list(pool.map(extract, range(1, count + 1)))
    if hashlib.sha256(SOURCE.read_bytes()).hexdigest() != digest:
        raise SystemExit("Source changed during extraction; index not written")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    index = {
        "source": str(SOURCE.relative_to(ROOT)), "sha256": digest, "page_count": count,
        "extraction": "pdftotext -layout per physical PDF page; embedded form feeds removed within page",
        "pages": pages,
    }
    (OUTPUT / "source-pages.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / "source-layout.txt").write_text(
        "\n\n".join(f'===== PDF {p["pdf_page"]}; printed {p["printed_page"]} =====\n{p["text"]}' for p in pages),
        encoding="utf-8",
    )
    print(f"Indexed {count} physical pages; {sum(bool(p['warnings']) for p in pages)} pages have extraction warnings.")
    print(f"Local output: {OUTPUT}")


if __name__ == "__main__":
    main()
