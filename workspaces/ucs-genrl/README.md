# UCS-GenRL 独立设计工作区

**最新详细设计（2026-11-11）：** [第一轮实验规范](experiment-specification.html)含原文/代码静态差异、精确配额、快照和随机流、接口及验收；[唯一设计源](design/implementation-specification.json)，由[文档生成器](design/render-implementation-specification.py)生成页面。短阶段20k草案修订为20,480接纳样本；实际环境交互另计，旧预算保留为历史。按用户最新指令继续设计，正式实施或执行训练实验前等待指令。未执行研究代码。

**第一轮实验准备：** [准备包](theory-experiment-design.html#preparation)列出材料缺口、R0定义、可选R1-P、独立确认和字段字典；[结构化清单](design/first-round-preparation.json)。均待评审，未启动实施。

**2026-11-11 理论与实验设计：** [完整配额的迁移收益测量与预算条件](theory-experiment-design.html)给出T1–T7条件公式、候选B-M、近邻反证和R0–R3实验。全部为拟议设计；旧方案按日期保留，研究实现与训练未启动。

**2026-11-11 价值评估：** [按已引入的 Auto Research 成果审查论文方向](direction-b-study.html#value-review)。方向 B 明确保留为有限诊断主线；明确原 4.2 已有回训反馈，新问题是候选贡献识别与全成本分配。尚未确立新方法效果或可投稿性。

**当前方向 B 深入研究（2026-11-10）：** [回训如何改变课程价值](direction-b-study.html)。用户已指示沿该方向继续；本轮完成解析分解、近邻及代码只读审查、三层随机性与预算协议。尚无新训练结果。下列入口保留前轮研究历史。

前轮整合入口：[4.2 论文化研究评审](research-review.html)，覆盖四项研究交付与自动科研决策记录；未启动研究实现或实验。

**2026-11-10 深度研究更新：** 该轮入口为[课程分配深度研究](curriculum-deep-research.html)，暂按方向 2 为方法主线、方向 3 为组合泛化验证。已补充公开代码与原文差异、GradAlign/PGB/ULEE 等 2026 近邻、固定原任务回训后收益定义及分阶段实验；主次未视为最终选择，创新尚待验证。下方早期路线与实验编号保留为历史讨论，不自动执行。

先读[学位论文与各章介绍](thesis-guide.html)，再读[2026–2027 投稿创新性复评](novelty-review.html)及最新的[原任务内创新设计与历史评估](direction-a-assessment.html#original-task)，然后进入[研究设计 Web UI](index.html)。编辑器入口：[UCS-GenRL.code-workspace](UCS-GenRL.code-workspace)。上述阅读页均为单文件 HTML，可在浏览器按 Ctrl+O 打开；远程仓库需先把文件复制到浏览器所在电脑。

本工作区聚焦学位论文 4.2 的理论、实验方案与代码接口讨论；根目录 AGENTS.md 对此仍然有效。未实现研究算法、未启动训练，用户评估计划后再进入实现阶段。

最新用户约定：优先维持原任务定义，并在其内部拓展创新。当前阅读[原任务内的创新设计](direction-a-assessment.html#original-task)：任务编辑与跨任务课程分配分别审查，组合泛化作为共同强验证并保留独立成文可能；资源依赖判据降为辅助。该页保留的旧 P0–P4 不是当前已确定执行方案。

在浏览器直接打开 index.html 即可阅读，无须安装前端依赖。或者从仓库根目录运行：

```sh
python3 -m http.server 18767 --bind 127.0.0.1 --directory workspaces/ucs-genrl
```

随后在同一电脑访问 http://127.0.0.1:18767/ 。远程客户端需要自己的端口转发，不默认公开托管。

- index.html：理论模型、有限样本推导、假设边界、评审问题和来源的主要文档。
- direction-a-assessment.html：第六版当前约定与原任务内创新候选（新增方向 2 / 3 深化）；新增 MRACL 等比较，明确原多指标反馈属于继承内容。后半部保留第四版方向 A 的理论反证与历史实验讨论，均未执行。
- novelty-review.html：同日上一版创新性复评、三条候选路线；包含来源年份筛选。方向 A 的最新判断以 direction-a-assessment.html 为准。
- design/novelty-search-2026-11-10.json：定向检索范围、来源链接与阅读深度；不是系统综述或实验结果。
- thesis-guide.html：独立的研究前导读，含全文主线、五章与结论、六项方法、成果边界和原文页码；样式和脚本均内嵌，不依赖其他资产。
- assets/design-data.js：实验矩阵和接口规范的唯一数据源，由页面直接渲染；这些是设计，不是算法实现。
- assets/app.js / styles.css：阅读交互、预算/统计界限计算和排版；计算结果只用于方案讨论。
- design/decisions.json：已确认事项、建议和待评估事项的版本化记录。页面同步列出当前摘要；修改时同步维护。

页面“讨论笔记”保存在当前浏览器 localStorage，不会自动写回仓库；可下载 JSON 后再纳入设计记录。理论公式为本轮草案推导，其中使用的标准集中界不属于方法创新。更早的文献评估与总体方案继续保存在 docs/topics/TR-001-thesis-uav-crowdsensing/。
