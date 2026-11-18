"""Versioned research and self-modification guidance; no budget or gate authority."""
import json


def task_guidance(context):
    phase = context.get('task', {}).get('phase', '')
    guidance = (
        '持续推进当前阶段的实际产物。先检查已有成功回执和源码版本，复用匹配产物；'
        '错误须读取原始日志，提出可检验原因，修复后执行同一验收。'
        '每次实验记录假设、固定评价、预算、实际结果以及保留/淘汰/失败决定。'
        '将工程故障、科学否决、外部证据依赖分别写清；继续没有依赖阻塞的工作。'
        '已有有效用户授权优先于旧只读阶段描述。状态未知的作业先核对回执和进程。'
    )
    if phase in ('analyze', 'write', 'review'):
        guidance += '结果覆盖完整失败分母；所有数字回链真实产物。论文包括负结果、限制与尚未证明的主张。'
    return guidance


def improvement_prompt(context):
    return (
        '修改你当前版本的执行策略，使它在固定验收下更可靠。'
        '根据开发集失败和真实故障摘要提出一个具体假设，只返回允许的文件完整内容。'
        '保留所有公开函数签名和自身生成下一轮改进提示的能力；代码仅用Python标准库。'
        '科学目标、评价器、预算、凭据、运行账本及部署内核不在修改范围。'
        '不要猜测或硬编码测试答案，不读取其他目录，不启动其他模型。'
        '若所有可见案例已通过，改进一般性或简化实现并说明理由；不保证候选会被启用。'
        '\n当前父版本、文件与开发反馈：\n' + json.dumps(context, ensure_ascii=False)
    )
