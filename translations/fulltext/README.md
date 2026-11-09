# Auto Research：全文中英对照

8 篇论文原文共 487 页，另含 autoresearch 的 README 与 program.md。按段对照机器初译，保留附录可提取文本；摘要已由当前助手复核，其余内容仍为待精校初稿。

获取日期：2026-11-09。

[打开双语阅读总入口](index.html)

- **AutoSurvey**（2406.10252v2）：[逐段对照 Markdown](autosurvey/bilingual.md) · [双语 HTML](autosurvey/bilingual.html)
- **OpenScholar**（2411.14199v1）：[逐段对照 Markdown](openscholar/bilingual.md) · [双语 HTML](openscholar/bilingual.html)
- **SurveyForge**（ACL 2025 / 2025.acl-long.609）：[逐段对照 Markdown](surveyforge/bilingual.md) · [双语 HTML](surveyforge/bilingual.html)
- **Co-Scientist**（2502.18864v2）：[逐段对照 Markdown](co-scientist/bilingual.md) · [双语 HTML](co-scientist/bilingual.html)
- **AI Scientist-v2**（2504.08066v1）：[逐段对照 Markdown](ai-scientist-v2/bilingual.md) · [双语 HTML](ai-scientist-v2/bilingual.html)
- **PaperBench**（2504.01848v3）：[逐段对照 Markdown](paperbench/bilingual.md) · [双语 HTML](paperbench/bilingual.html)
- **AstaBench**（2510.21652v2）：[逐段对照 Markdown](astabench/bilingual.md) · [双语 HTML](astabench/bilingual.html)
- **EPOCH**（2610.06986v1）：[逐段对照 Markdown](epoch/bilingual.md) · [双语 HTML](epoch/bilingual.html)
- **autoresearch**（228791fb499afffb54b46200aca536f79142f117）：[逐段对照 Markdown](autoresearch/bilingual.md) · [双语 HTML](autoresearch/bilingual.html)

## 版本、许可与质量

- [原文清单及 SHA-256](../../sources/fulltext/manifest.json)；各目录附 source.json 和原始 PDF。
- OpenScholar 使用 arXiv v1 的 CC BY 版本；SurveyForge 使用 ACL 正式版。其余 arXiv 版本已固定，autoresearch 已固定 commit。
- 原文为 CC BY 4.0 的论文允许注明来源后改编；此处译文标注为非官方 AI 初译。代码/参考文献/公式及作者机构按需保留原文。图中嵌入文字不保证已单独翻译。
- HTML 提取与 PDF 段落重建会受到表格、换行、边注和字体编码影响。遇到技术推导、数值结论、图表或不通顺译文，请打开原 PDF 对照。
- [质量记录](quality-report.json) 列出缺译与自动标记。无自动标记不意味着语义已经逐段验证。
- scripts/fetch_primary_sources.py、prepare_bilingual_units.py、translate_fulltext.py、render_bilingual_readers.py 保存了可继续执行的流程。模型权重和虚拟环境没有纳入 Git。
