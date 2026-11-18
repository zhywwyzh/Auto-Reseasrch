import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import subprocess

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import delivery_validation


def pdf_bytes():
    stream = b'BT /F1 12 Tf 20 100 Td (Engineering test fixture, not research) Tj ET'
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>',
               b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
               b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 150] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>',
               b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
               b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream']
    out = io.BytesIO(); out.write(b'%PDF-1.4\n'); offsets = [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(out.tell()); out.write(f'{i} 0 obj\n'.encode() + obj + b'\nendobj\n')
    xref = out.tell(); out.write(f'xref\n0 {len(offsets)}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]: out.write(f'{offset:010} 00000 n \n'.encode())
    out.write(f'trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n'.encode())
    return out.getvalue()


@unittest.skipUnless(shutil.which('pdfinfo') and shutil.which('pdftoppm'), 'Poppler required')
class DeliveryTests(unittest.TestCase):
    def test_parser_timeout_is_a_recoverable_validation_failure(self):
        with patch.object(delivery_validation.subprocess, 'run', side_effect=subprocess.TimeoutExpired('pdfinfo', 20)):
            with self.assertRaisesRegex(ValueError, '检查超时'):
                delivery_validation.verify_pdf('fixture.pdf')

    def test_pdf_is_parsed_and_actually_rendered(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'document.pdf'; p.write_bytes(pdf_bytes())
            result = delivery_validation.verify_pdf(p)
            self.assertEqual(result['pages'], 1)
            self.assertTrue(result['first_page_rendered'])

    def test_pdf_header_and_json_render_claim_cannot_pass(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'document.pdf'; p.write_bytes(b'%PDF-TEST-FIXTURE')
            with self.assertRaises(ValueError): delivery_validation.verify_pdf(p)
            p.write_text('{"rendered":true}')
            with self.assertRaises(ValueError): delivery_validation.verify_rendered_page(p)
