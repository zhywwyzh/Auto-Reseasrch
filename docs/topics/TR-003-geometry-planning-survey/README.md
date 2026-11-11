# TR-003：面向整身运动规划的几何表征综述

2026-11-11 根据用户指定的 `thesis-reference/theses/zjuthesis.pdf` 建立。独立于 TR-001 / UCS-GenRL 与 TR-002；不修改其选题及在途工作。

主要入口：[研究方案与综述雏形](../../../workspaces/geometry-planning-survey/index.html)。

候选题名（v0.2）：**面向整身运动规划的几何表征：任务可行性、约束转换与安全保证**。

背景论文为王钱浩《基于计算几何的移动机器人整身规划研究》，170 个 PDF 物理页。用户于 2026-11-11 确认各研究章节均已有对应学术论文并完成投稿；不把“投稿”自动解释为全部录用。原文科研成果表及公开论文进一步支持第2、3、4章的对应关系，第5章各应用与论文版本仍需逐项细化。

本轮完成范围：原论文章节与成果定位、定向文献检索、部分关键全文核对、综述竞争分析、研究问题与证据编码、带引用的中文论述雏形。检索截止 2026-11-11；不是数据库穷尽检索、独立双人筛选或已完成系统综述，不含新实验结果。2026 RCSR 综述已否定“首次统一安全与部署视角”的宽泛贡献；保留更窄的几何约束转换及保证边界视角，独特性仍需后续核验。

内容源为 [survey.json](../../../workspaces/geometry-planning-survey/survey.json)，同目录 `build.py` 生成静态 HTML 与可选 Canvas，避免多份正文独立维护。执行：

```sh
python3 workspaces/geometry-planning-survey/build.py
```

阅读材料下载到 `thesis-reference/related-papers/TR-003-geometry-survey/`；原文提取、下载来源与哈希、页码索引、检索过程记录放在 `thesis-reference/notes/TR-003-zjuthesis-survey/`，均由 Git 忽略。原始输入未修改，未推送、未公开发布、未启动训练或付费模型调用。

正式投稿前必须完成：数据库检索与去重清单、核心全文编码、最近综述逐节对照、版本合并与独立复核、目标期刊及篇幅确认。后续实验仅为可选证据补强，须另行评估计划。

## 2026-11-11：继续推进至 v0.2

已将观点落实为共同轨迹空间中的可行集分析、三组代表性机制对照、失败原因与补救动作的对应关系，以及摘要和九节正文。新增可手算的 Bézier 解析案例：同一安全曲线在单段控制点包含约束下被拒绝，精确分段后可通过；这是标准性质的说明，不是新定理或实验。

当前种子库 38 条，含 10 篇既有综述。新增 2026 年制造机器人安全综述与协同变道综述，进一步收缩“首次统一可行性/安全保证”的宽泛主张。制造机器人综述全文尚未取得，其覆盖重合是当前最重要的定位核查缺口，不能将访问受限当作没有重合。C-IRIS 新增定理相关段落核对，保留“存在足够高次数”与“固定预算能认证成功”的区别。

正文、对照、图例参数仍以 `survey.json` 为内容源。`plot_examples.py` 使用 Matplotlib 生成可追踪 SVG；`build.py` 将 SVG 内嵌到 HTML 和 Canvas，使阅读入口保持无外部资源依赖。重绘解析图可执行：

```sh
PYTHONNOUSERSITE=1 /usr/bin/python3 workspaces/geometry-planning-survey/plot_examples.py
python3 workspaces/geometry-planning-survey/build.py
```

此环境默认 Python 的用户级 NumPy 与系统 Matplotlib 存在版本冲突，上述命令使用现有系统依赖，不修改全局环境。页面与关键交互验收、来源哈希和仍未完成的研究检查见同目录 `validation.json`；不把浏览器检查视为学术证据复核。
