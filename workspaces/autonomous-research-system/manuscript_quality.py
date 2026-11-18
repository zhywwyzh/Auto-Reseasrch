"""Find audit/report narration in manuscript bodies without stripping citations."""
import re
from pathlib import Path

PATTERNS = (
    r'参考原文', r'原学位论文', r'学位论文(?:中|提到|指出|给出|所述|第\s*\d)',
    r'原论文(?:提到|指出|中给出|中的定义)', r'PDF\s*页序', r'印刷页码',
    r'(?:依据|根据|遵循|按照|沿用|对照|核对)(?:原文|学位论文)',
    r'原文(?:中|的|给出|提到|定义|第|式)',
    r'前轮(?:验收|运行|稿件|实验)', r'本轮(?:调用|控制器|验收)',
    r'内部(?:评分|总评)', r'/home/[^\s{}]+', r'thesis-reference/',
    r'workspaces/[A-Za-z0-9_/-]+', r'according to the thesis',
    r'as stated in the (?:thesis|dissertation)', r'the original thesis',
)
INSTRUCTION = ('论文是独立学术论文，不是学位论文导读或执行审计报告。'
    '题目和摘要以具体研究对象、科学问题、方法或可支持的发现为中心；不要用任务边界声明、'
    '重建声明、内部状态说明充当题目或研究主题。引言说明问题、已有方法的具体缺口、本文研究设计及证据支持的认识。'
    '模型、实现、预算、回执和验收的齐备属于研究基础，不能直接列为科学贡献；贡献不足时继续研究或如实报告有研究价值的负结果，不能用声明性文字凑成论文。'
    '用“考虑如下任务”“本文定义/采用/设计/验证”等自然陈述组织研究；'
    '删除反复“参考原文/学位论文提到”的提取叙事，但保留必要学术引用、假设、适用范围与真实局限。'
    '原页码/印刷页码/本地文件路径/哈希/调用故障/内部评分放单独证据与复现记录。'
    '正确示例：“无人机的能耗由飞行和数据采集两部分组成，定义为……”。'
    '引用已有模型时采用正常文献引用，不隐去他人成果，不把历史结果改称新实验。')

TITLE_PATTERNS = (
    r'声明(?:重建|复现)', r'(?:任务|研究|稿件)(?:边界|状态|范围)声明',
    r'(?:内部执行|工程验收|运行审计)(?:报告|记录)',
    r'declared\s+reconstruction', r'(?:internal execution|run audit)\s+report',
)


def titles(text):
    """Extract balanced title macros; technical reconstruction titles are valid."""
    for match in re.finditer(r'\\(?:cntitle|entitle|title)\s*\{',text):
        start=match.end();depth=1;index=start
        while index<len(text) and depth:
            if text[index]=='{' and (index==0 or text[index-1]!='\\'):depth+=1
            if text[index]=='}' and (index==0 or text[index-1]!='\\'):depth-=1
            index+=1
        if depth==0:yield text[start:index-1]


def prose(text):
    text = re.sub(r'(?<!\\)%[^\n]*', '', text)
    return re.sub(r'\\begin\{thebibliography\}.*?\\end\{thebibliography\}',
                  lambda match: '\n' * match.group(0).count('\n'), text, flags=re.S)


def verify(path):
    root = Path(path).resolve().parent
    seen, findings = set(), []
    def inspect(file):
        file = file.resolve()
        if not file.is_relative_to(root) or len(seen) >= 256:
            raise ValueError('正文输入须属于可交付稿件目录，不能指向外部审计或原始资料')
        if file in seen:
            return
        seen.add(file)
        text = prose(file.read_text())
        for title in titles(text):
            if any(re.search(expression,title,re.I) for expression in TITLE_PATTERNS):
                raise ValueError('论文题目以任务声明或内部报告为中心；须以研究问题、方法或有证据的发现组织题目，不能仅换标题掩盖研究内容不足')
        for expression in PATTERNS:
            for match in re.finditer(expression, text, re.I):
                findings.append({'path': str(file), 'line': text[:match.start()].count('\n')+1,
                                 'phrase': match.group(0)})
        for match in re.finditer(r'\\(?:input|include)\s*\{([^}]+)\}', text):
            child = file.parent / match.group(1)
            if child.suffix != '.tex':
                child = child.with_suffix('.tex')
            inspect(child)
    inspect(Path(path))
    if findings:
        row = findings[0]
        raise ValueError('论文写作质量检查未通过：' + row['path'] + ':' + str(row['line'])
                         + ' 含导读/审计叙述“' + row['phrase'] + '”；请重写正文并保留必要引用；共'
                         + str(len(findings)) + '处')
    return {'files_checked': len(seen), 'report_narration_matches': 0,
            'citations_removed': False, 'scientific_truth_verified': False}
