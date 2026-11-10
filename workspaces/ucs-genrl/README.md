# UCS-GenRL 独立设计工作区

先读[学位论文与各章介绍](thesis-guide.html)，再读[2026–2027 投稿创新性复评与改进路线](novelty-review.html)，然后进入[研究设计 Web UI](index.html)。编辑器入口：[UCS-GenRL.code-workspace](UCS-GenRL.code-workspace)。导读和复评均为单文件 HTML，可在浏览器按 Ctrl+O 打开；远程仓库需先把文件复制到浏览器所在电脑。

本工作区聚焦学位论文 4.2 的理论、实验方案与代码接口讨论；根目录 AGENTS.md 对此仍然有效。未实现研究算法、未启动训练，用户评估计划后再进入实现阶段。

在浏览器直接打开 index.html 即可阅读，无须安装前端依赖。或者从仓库根目录运行：

```sh
python3 -m http.server 18767 --bind 127.0.0.1 --directory workspaces/ucs-genrl
```

随后在同一电脑访问 http://127.0.0.1:18767/ 。远程客户端需要自己的端口转发，不默认公开托管。

- index.html：理论模型、有限样本推导、假设边界、评审问题和来源的主要文档。
- novelty-review.html：2026-11-10 最新创新性判断、三条候选路线、理论与最小实验；包含来源年份筛选，内容优先于首轮迁移探测建议，尚待用户评估。
- design/novelty-search-2026-11-10.json：定向检索范围、来源链接与阅读深度；不是系统综述或实验结果。
- thesis-guide.html：独立的研究前导读，含全文主线、五章与结论、六项方法、成果边界和原文页码；样式和脚本均内嵌，不依赖其他资产。
- assets/design-data.js：实验矩阵和接口规范的唯一数据源，由页面直接渲染；这些是设计，不是算法实现。
- assets/app.js / styles.css：阅读交互、预算/统计界限计算和排版；计算结果只用于方案讨论。
- design/decisions.json：已确认事项、建议和待评估事项的版本化记录。页面同步列出当前摘要；修改时同步维护。

页面“讨论笔记”保存在当前浏览器 localStorage，不会自动写回仓库；可下载 JSON 后再纳入设计记录。理论公式为本轮草案推导，其中使用的标准集中界不属于方法创新。更早的文献评估与总体方案继续保存在 docs/topics/TR-001-thesis-uav-crowdsensing/。
