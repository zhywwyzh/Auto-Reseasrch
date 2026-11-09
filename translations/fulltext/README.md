# 中文论文阅读

8 篇论文和 autoresearch 文档。下方展示论文摘要的中文译文，autoresearch 展示文档简介。阅读全文可展开英文对照；正文仍为待精校初稿。

**浏览器阅读：[打开全部文章](http://127.0.0.1:18766/) · [直接打开 AutoSurvey](http://127.0.0.1:18766/translations/fulltext/autosurvey/bilingual.html)。**

这些 HTTP 地址仅适用于运行阅读服务的这台电脑。请在浏览器打开；编辑器没有 PDF 查看插件时，直接点击文件会显示源码。服务脚本为 `scripts/serve_fulltext_reader.py`，默认仅监听 `127.0.0.1:18766`，只提供论文阅读相关文件。

离线阅读可选下方的中文 PDF，或中文 Markdown 预览。

- **AutoSurvey**：[中文 PDF](../../output/pdf/autosurvey-zh-reading.pdf) · [中文 Markdown](autosurvey/reading.md) · [可展开英文的阅读版](autosurvey/bilingual.html)
- **OpenScholar**：[中文 PDF](../../output/pdf/openscholar-zh-reading.pdf) · [中文 Markdown](openscholar/reading.md) · [可展开英文的阅读版](openscholar/bilingual.html)
- **SurveyForge**：[中文 PDF](../../output/pdf/surveyforge-zh-reading.pdf) · [中文 Markdown](surveyforge/reading.md) · [可展开英文的阅读版](surveyforge/bilingual.html)
- **Co-Scientist**：[中文 PDF](../../output/pdf/co-scientist-zh-reading.pdf) · [中文 Markdown](co-scientist/reading.md) · [可展开英文的阅读版](co-scientist/bilingual.html)
- **AI Scientist-v2**：[中文 PDF](../../output/pdf/ai-scientist-v2-zh-reading.pdf) · [中文 Markdown](ai-scientist-v2/reading.md) · [可展开英文的阅读版](ai-scientist-v2/bilingual.html)
- **PaperBench**：[中文 PDF](../../output/pdf/paperbench-zh-reading.pdf) · [中文 Markdown](paperbench/reading.md) · [可展开英文的阅读版](paperbench/bilingual.html)
- **AstaBench**：[中文 PDF](../../output/pdf/astabench-zh-reading.pdf) · [中文 Markdown](astabench/reading.md) · [可展开英文的阅读版](astabench/bilingual.html)
- **EPOCH**：[中文 PDF](../../output/pdf/epoch-zh-reading.pdf) · [中文 Markdown](epoch/reading.md) · [可展开英文的阅读版](epoch/bilingual.html)
- **autoresearch**：[中文 PDF](../../output/pdf/autoresearch-zh-reading.pdf) · [中文 Markdown](autoresearch/reading.md) · [可展开英文的阅读版](autoresearch/bilingual.html)

原文文件及版本见 [原文清单](../../sources/fulltext/manifest.json)。原始译文及对应关系仍保存在各目录的 bilingual.json，自动质量标记见 [质量记录](quality-report.json)。本次仅调整阅读排版，未重新调用模型。图表原貌以原文 PDF 为准。

## 原图与公式

HTML 来源的原图、原始表格和公式已恢复，图可点击放大，数学排版使用本地 KaTeX 0.19.1 和原文 MathML，不依赖外部 CDN。图内英文保留原样。PDF 提取版提供对应原页的可放大预览，保留图表及公式；SurveyForge 使用 ACL 正式版原页，不与 arXiv 预印本混用。

各文章的 `visuals.json` 记录图资源的来源 URL、SHA-256、原文标识及对应译文单元；`render-quality.json` 记录公式补回及渲染检查。AutoSurvey 六段中的变量遗漏、位置和量纲误译依据固定版本原文修正，见 `data/fulltext-visual-corrections.json`。其余译文仍为未逐段精校的机器初稿。

重新生成（不调用模型）：

```sh
npm install --prefix .cache/reader-tools --no-audit --no-fund katex@0.19.1
python3 scripts/prepare_reader_visuals.py
python3 scripts/render_readable_fulltext.py --pdf
```

需要 Python 的 BeautifulSoup、系统 Poppler 和 Chrome。原始 PDF、HTML、原始译文保持不变；生成的原页 JPEG 和 PDF 不纳入 Git。
