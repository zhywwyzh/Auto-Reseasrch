"""Evaluate whether real, current and adequately grounded tool review can close a loop.

This validates provenance and workflow conditions, not scientific truth. A model
score or a report-generation success alone cannot accept a manuscript.
"""
from pathlib import Path
import hashlib


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assess(manuscript, pdf, raw_report, receipt, review, issues):
    reasons=[]
    if receipt.get('status')!='succeeded': reasons.append('评审工具尚无真实成功回执')
    if receipt.get('mode') not in {'full_tool_review','full_local_tool_review'}:
        reasons.append('当前运行仅为诊断或内部预审，不具备最终验收范围')
    for key,path in [('manuscript_sha256',manuscript),('pdf_sha256',pdf),('raw_report_sha256',raw_report)]:
        if not Path(path).is_file() or receipt.get(key)!=sha(path): reasons.append(key+'不匹配，须对当前产物重新评审')
    if not receipt.get('tool') or not receipt.get('model') or not receipt.get('prompt_sha256'):
        reasons.append('缺实际工具、模型或冻结提示词标识')
    coverage=review.get('coverage',{})
    if not all(coverage.get(k) is True for k in ['full_manuscript','key_evidence','relevant_work']):
        reasons.append('全文、关键证据或相关工作未完整覆盖')
    if review.get('verdict')!='accept' or not review.get('verdict_quote'):
        reasons.append('工具未给出有原文依据的明确认可结论')
    if any(i.get('severity') in {'critical','major'} and i.get('status')!='verified_closed' for i in issues):
        reasons.append('仍有尚未复验关闭的关键或实质问题')
    # An issue resolved by evidence needs a concrete record. Deleting a row does
    # not validate the scientific claim; the full history is stored by the caller.
    if any(i.get('status')=='verified_closed' and not i.get('evidence') for i in issues):
        reasons.append('问题关闭缺少修订、证明或实验依据')
    return {'tool_accepted':not reasons,'reasons':reasons,'scientific_truth_verified':False,
            'publication_or_submission_approved':False}
