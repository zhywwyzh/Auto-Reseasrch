# 自动化学报 LaTeX 模板

此目录保存用户提供模板的解压原件，纳入 Git。模板中的示例文章不代表本项目稿件。

## 来源与完整性

- 本地源文件：`thesis-reference/自动化学报LaTeX模板.zip`（源 ZIP 由 Git 忽略）。
- 解压日期：2026-11-09。
- ZIP SHA-256：`0b4c5efd7ca5ece2617977475acee18a47ceb307788154b632974aa43a60b162`。
- 原包共 14 个文件，解压时已逐文件校验与 ZIP 内容一致；本 README 为仓库新增说明。
- 这是用户提供的版本，本次未联网核验是否为期刊最新模板。

## 使用方式

主要入口是 `main.tex`，文档类为 `aas.cls`。字体、`picins.sty`、EPS 及附带的 PDF 均是原包资源，保留在同一目录。

模板自带的 `LaTeX 排版注意事项.md` 注明使用 TeX Live 2026，且不要修改 `aas.cls`；`main.tex` 指定使用 XeLaTeX。

开展具体稿件任务时，将本目录复制到 `papers/<课题名>/`，在稿件副本中修改 `main.tex` 和论文所需资源，保留此处模板供对照。作者、基金、DOI、录用信息和示例图文均需按实际情况处理。

在稿件副本目录中可使用以下命令编译：

```sh
latexmk -xelatex -interaction=nonstopmode -halt-on-error main.tex
```

本次仅完成模板解压与文件一致性校验，未执行 LaTeX 编译。后续修改稿件时需要编译并检查生成 PDF。
