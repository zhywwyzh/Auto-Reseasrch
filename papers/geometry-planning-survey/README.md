# TR-003 稿件：整身运动规划中的几何表征与约束转换综述

目标：《自动化学报》，用户于2026-11-11确认。当前为v0.4论述初稿，非可提交稿；作者、单位、基金、日期和DOI等未虚构。

主要阅读入口：[正文阅读页](../../workspaces/geometry-planning-survey/manuscript.html)；[投稿核验、样刊数据与证据卡](../../workspaces/geometry-planning-survey/index.html)。本机生成的阅读PDF在 `build/review-reading.pdf`，由浏览器打印排版，不是XeLaTeX成功编译的产物。`build/`由Git忽略。

唯一正文源为 `workspaces/geometry-planning-survey/survey.json`。不要独立修改生成的 `main.tex`；重新生成：

```sh
PYTHONNOUSERSITE=1 /usr/bin/python3 workspaces/geometry-planning-survey/plot_examples.py
python3 workspaces/geometry-planning-survey/build.py
python3 workspaces/geometry-planning-survey/build_manuscript.py
```

`aas.cls`、`picins.sty`和Euclid字体复制自仓库 `templates/acta-automatica-sinica/`；`aas.cls`与官网2026/09附件一致，未修改。原始模板和示例仍在模板目录中。本稿只引用两幅自绘图，未复制样刊原图。

具备模板所需依赖后，从本目录执行：

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=build main.tex
```

2026-11-11实际编译未通过：执行主机安装TeX Live 2022，缺少 `ctexart.cls`；模板说明为TeX Live 2026。错误日志保留在本机 `build/main.log`。此处不声称其他依赖已齐全，也不把未编译源码称为可提交稿。

现有正文含32条实际引用，3张技术比较表、2张自绘图和6个展示公式。引文元数据已核；技术结论按证据卡保留阅读深度与采用版本，元数据核验不等于全文复核。近期3篇2026预印本及cuRobo技术报告仍如实标注。没有新的机器人仿真、训练或实机结果。

当前主要缺口：最近直接近邻综述（尤其S09）的全文差异核查、代表性覆盖扩展、关键文献完整编码及独立研究者复核。部分文献只有摘要层证据，正文已限制其用途。32不是期刊要求或最终文献数量。

AI参与检索、核心论述和摘要起草、比较表、解析图脚本及排版，日期与核验过程保留在内容源。用户授权继续写作并由投稿人审核；期刊核心内容限制与2025作者承诺如实记录，不能据人工审核预先声明已经符合。未代签、未提交、未公开发布、未推送。
