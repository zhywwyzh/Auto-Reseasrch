"""Explicit user removal of administrative limits, scoped and hash bound."""
import hashlib
import json
from pathlib import Path

VERSION = 'user-unrestricted-execution-v1'
INSTRUCTION = (
    '用户最新要求“改成不限制，限制没有任何意义”。本运行不设模型调用/token/累计时间、'
    '研究累计交互/更新/提交槽、修订轮数、诊断/修复/重试次数及强制执行超时上限。'
    '旧内部额度及单批强制超时已被此授权替代；修改启动器硬编码及对账逻辑后继续，无需再次申请。'
    '样本量、训练量、研究设计和评价终点依据科学问题设定，不把行政额度当作实验充分性。'
    '持续读取真实日志并诊断无进展，不机械重复同一失败。服务端明确配额恢复时刻和网络检查间隔照常遵守。'
    '所有历史消耗和失败保留；UNKNOWN先核对，不重复派发。用户停止仍有效。'
    '原服务器CPU/内存分区、任务定义、证据和完整科学验收继续适用。'
)


def unrestricted(state):
    policy = state['config'].get('execution_limits', {})
    if policy.get('mode') != VERSION:
        return False
    ref = policy['authority_source']
    path = Path(ref['path']).resolve()
    root = (Path(state['repo']) / state['config']['workspace']).resolve()
    if not path.is_relative_to(root):
        raise ValueError('不限额授权须属于当前课题')
    body = path.read_bytes()
    if hashlib.sha256(body).hexdigest() != ref['sha256']:
        raise ValueError('不限额授权哈希不匹配')
    value = json.loads(body)
    if value.get('topic') != state['topic'] or value.get('mode') != VERSION or value.get('authorized') is not True:
        raise ValueError('不限额授权课题或模式不匹配')
    return True
