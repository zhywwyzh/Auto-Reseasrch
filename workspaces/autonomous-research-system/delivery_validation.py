"""Independent format/render checks at paper delivery, outside evolvable strategies."""
from pathlib import Path
import re
import subprocess
import tempfile


def _run(argv, **kwargs):
    try:
        return subprocess.run(argv, **kwargs)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('PDF独立检查超时，保留原产物并按验收失败处理') from exc


def verify_pdf(path):
    path = Path(path).resolve()
    result = _run(['pdfinfo', str(path)], capture_output=True, text=True, timeout=20)
    match = re.search(r'^Pages:\s+(\d+)\s*$', result.stdout, re.M)
    if result.returncode or not match or int(match[1]) < 1:
        raise ValueError('PDF未通过独立解析，文件头不能代替可读论文：' + str(path))
    with tempfile.TemporaryDirectory(prefix='ars-pdf-check-') as temp:
        output = Path(temp) / 'page'
        rendered = _run(['pdftoppm', '-f', '1', '-l', '1', '-singlefile', '-scale-to', '800', '-png',
                                   str(path), str(output)], capture_output=True, timeout=30)
        image = output.with_suffix('.png')
        if rendered.returncode or not image.exists() or not image.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
            raise ValueError('PDF未通过控制器独立渲染：' + str(path))
    return {'pages': int(match[1]), 'first_page_rendered': True, 'scope': 'format/render verification, not scientific review'}


def verify_rendered_page(path):
    raw = Path(path).read_bytes()
    if not (raw.startswith(b'\x89PNG\r\n\x1a\n') or raw.startswith(b'\xff\xd8\xff')):
        raise ValueError('渲染页需要真实PNG/JPEG图片，JSON声明不能替代')
