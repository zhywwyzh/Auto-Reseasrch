# AutoResearch-UAV

面向无人机探索、导航与具身智能的 Auto Research 研究仓库。

本仓库于 2026-11-05 从研究对话中建立，独立于 `DiffAgent2-Exploration`。当前包含研究路线、文献地图和交互面板源码；尚未实现科研 Agent，也未开展本项目的仿真或实机实验。

## 当前仓库契约

仓库工作遵循 [AGENTS.md](AGENTS.md)。当前聚焦本地学位论文 `thesis-reference/theses/3120215520_答辩修改后论文0830.pdf` 第 4.2 节 UCS-GenRL 的学术论文化。用户已确认该节尚无论文和代码，其他方法节已有论文与开源；当前只讨论研究计划，待用户评估后再开展实现和实验。

- `thesis-reference/`：本地学位论文、相关论文和阅读笔记，整体由 Git 忽略。
- [自动化学报 LaTeX 模板](templates/acta-automatica-sinica/README.md)：已从用户提供的 ZIP 解压，位于可上传目录。
- `papers/<课题名>/`：后续按需创建的稿件目录，从模板副本开展写作。

当前课题：[TR-001：第 4.2 节论文化可行性](docs/topics/TR-001-thesis-uav-crowdsensing/README.md)。阅读[论文方案与大纲](docs/topics/TR-001-thesis-uav-crowdsensing/paper-feasibility-plan.md)、[代码与实验讨论稿](docs/topics/TR-001-thesis-uav-crowdsensing/experiment-design.md)及[经典与近期文献评估](docs/topics/TR-001-thesis-uav-crowdsensing/literature-review.md)。

**当前研究进展：** [方向 B：回训如何改变课程价值](workspaces/ucs-genrl/direction-b-study.html)，含解析反例、最近邻审查和拟议最小判别协议；未启动训练。

**阅读第0步：** [学位论文导读——全篇主线与各章介绍](workspaces/ucs-genrl/thesis-guide.html)。操作者先了解原文，再评估研究方案。

**本轮深度研究：** [课程分配、理论与实验方案](workspaces/ucs-genrl/curriculum-deep-research.html)。暂按方向 2 主线、方向 3 验证推进；已补查原代码差异及 2026 强近邻，创新仍待验证，未启动实现或训练。

**最新研究约定（2026-11-10）：** [维持原任务定义的创新设计](workspaces/ucs-genrl/direction-a-assessment.html#original-task)。保留原 UCS 语义与 D/F/η/χ；分别审查任务编辑与跨任务课程分配，组合泛化作为共同强验证并保留独立成文可能。原文已有多指标反馈，不把它重新列为创新；充电必要性降为辅助分析。尚未开始实现或实验；背景与方向 A 历史反证保留在同页。

**理论与实验设计工作区：** [Web UI 主入口](workspaces/ucs-genrl/index.html) · [编辑器工作区](workspaces/ucs-genrl/UCS-GenRL.code-workspace) · [启动与文件说明](workspaces/ucs-genrl/README.md)。后续理论推导、实验矩阵及代码接口优先在此维护；当前仍处于设计讨论，尚未启动研究实现。

## 研究目标

基于领域文献、已有导航系统及失败日志，提出可证伪假设、选择实验、实现候选改进，并通过独立重跑判断结论是否成立。

优先从纯几何探索中的 frontier 排序、视点选择或失败恢复切入；之后扩展到语义目标搜索、VLN 和 Orin-NX 部署。

## 材料入口

- [AI 自主科研与论文撰写：截至 2026-11-10 的进展与证据边界](docs/research/autonomous-science-2026-11-10/index.html)
- [对应资料集：16项中文译读、13份原文PDF与11个固定提交的代码／资料库](docs/research/autonomous-science-2026-11-10/library/index.html)
- [指定 8 篇论文及 autoresearch 文档的中文阅读目录（PDF / Markdown）](translations/fulltext/README.md)
- [全文阅读总入口（HTML，中文正文，可展开英文）](translations/fulltext/index.html)
- [抓取原文、版本、许可及校验和](sources/fulltext/manifest.json)
- [研究方案与执行路线](docs/research-plan.md)
- [26 项参考工作及当前用途](docs/references.md)
- [中英对照阅读包与时效性复核（原 20 项＋新增 6 项）](docs/literature-bilingual-2026-11-05.md)
- [结构化文献阅读卡数据](data/literature-reading-2026-11-05.json)
- [中英对照交互面板源码](artifacts/auto-research-bilingual-reading.tsx)
- [本次研究对话历史（含参考图片）](history/auto-research-conversation.md)
- [完整交互面板源码](artifacts/auto-research-uav-roadmap.tsx)
- [打开独立工作区](AutoResearch-UAV.code-workspace)

交互面板保留了完整的五个页面：路线、文献地图、流水线、研究设计、执行计划。

## 在当前电脑打开交互面板

新的工作区面板位于：

`/home/zhywwyzh/.cursor/projects/home-zhywwyzh-workspace-AutoResearch-UAV/canvases/auto-research-uav-roadmap.canvas.tsx`

面板依赖宿主提供的 `cursor/canvas`，不是独立网页。仓库中的 `.tsx` 文件是可版本管理的完整源码副本；其他电脑可将它保存到对应工作区的受管 canvases 目录，并使用 `.canvas.tsx` 后缀打开。

新增的中英对照阅读面板位于同一目录的 `auto-research-bilingual-reading.canvas.tsx`，可按文献选择阅读，也可查看版本与时效性判断。阅读包包含原文短句翻译及原创英文释义/中文对照，不是全文翻译；核查范围见阅读包开头。

## 已知研究条件

- 方向：无人机、Agent、探索导航、大模型与具身智能。
- 已有基础：类似 EGO-Planner、VLN-AN 的工作；具体版本与基线尚待确认。
- 设备：搭载 Orin-NX 的四旋翼、单卡 4070 Ti SUPER、少量 H20 和 A100。
- 验证要求：可复现仿真、端侧测量和实机实验。
- 人员：尚未确定；16 周路线按约两名主要参与者估算。

## 迁移范围

仅迁移本次研究材料。没有复制原项目的代码、模型、数据、密钥或实验产物。

完整面板中的历史案例链接保留为原始来源引用，指向原工作区的既有文档；阅读本研究方案不依赖这些文件。原工作区及其原面板保留原样。后续研究文件应写入本仓库。

远程仓库：[zhywwyzh/Auto-Reseasrch](https://github.com/zhywwyzh/Auto-Reseasrch)。本地资料、缓存和环境按 `.gitignore` 排除。

## Codex 会话副本

已通过 Codex 原生 `thread/fork` 将研究对话复制到本工作目录，包含研究路线、仓库迁移和指标优化的已完成对话。副本名称：**Auto Research 方法论研究（独立工作区副本）**。原会话保留在原工作区。

继续副本：

```sh
codex resume 01a1ab84-5d5e-71a1-b554-43696abb24e3 -C /home/zhywwyzh/workspace/AutoResearch-UAV
```

复制回执见 [session-copy.json](history/session-copy.json)。Markdown 对话记录保存用户和助手的可见消息及参考图片；原生副本用于继续会话。
