# AutoResearch-UAV

面向无人机探索、导航与具身智能的 Auto Research 研究仓库。

本仓库于 2026-11-05 从研究对话中建立，独立于 `DiffAgent2-Exploration`。当前包含研究路线、文献地图和交互面板源码；尚未实现科研 Agent，也未开展本项目的仿真或实机实验。

## 研究目标

基于领域文献、已有导航系统及失败日志，提出可证伪假设、选择实验、实现候选改进，并通过独立重跑判断结论是否成立。

优先从纯几何探索中的 frontier 排序、视点选择或失败恢复切入；之后扩展到语义目标搜索、VLN 和 Orin-NX 部署。

## 材料入口

- [研究方案与执行路线](docs/research-plan.md)
- [20 项参考工作及阅读用途](docs/references.md)
- [本次研究对话历史（含参考图片）](history/auto-research-conversation.md)
- [完整交互面板源码](artifacts/auto-research-uav-roadmap.tsx)
- [打开独立工作区](AutoResearch-UAV.code-workspace)

交互面板保留了完整的五个页面：路线、文献地图、流水线、研究设计、执行计划。

## 在当前电脑打开交互面板

新的工作区面板位于：

`/home/zhywwyzh/.cursor/projects/home-zhywwyzh-workspace-AutoResearch-UAV/canvases/auto-research-uav-roadmap.canvas.tsx`

面板依赖宿主提供的 `cursor/canvas`，不是独立网页。仓库中的 `.tsx` 文件是可版本管理的完整源码副本；其他电脑可将它保存到对应工作区的受管 canvases 目录，并使用 `.canvas.tsx` 后缀打开。

## 已知研究条件

- 方向：无人机、Agent、探索导航、大模型与具身智能。
- 已有基础：类似 EGO-Planner、VLN-AN 的工作；具体版本与基线尚待确认。
- 设备：搭载 Orin-NX 的四旋翼、单卡 4070 Ti SUPER、少量 H20 和 A100。
- 验证要求：可复现仿真、端侧测量和实机实验。
- 人员：尚未确定；16 周路线按约两名主要参与者估算。

## 迁移范围

仅迁移本次研究材料。没有复制原项目的代码、模型、数据、密钥或实验产物。

完整面板中的历史案例链接保留为原始来源引用，指向原工作区的既有文档；阅读本研究方案不依赖这些文件。原工作区及其原面板保留原样。后续研究文件应写入本仓库。

当前仓库仅在本地初始化，没有创建或连接远程仓库。

## Codex 会话副本

已通过 Codex 原生 `thread/fork` 将研究对话复制到本工作目录，包含研究路线、仓库迁移和指标优化的已完成对话。副本名称：**Auto Research 方法论研究（独立工作区副本）**。原会话保留在原工作区。

继续副本：

```sh
codex resume 01a1ab84-5d5e-71a1-b554-43696abb24e3 -C /home/zhywwyzh/workspace/AutoResearch-UAV
```

复制回执见 [session-copy.json](history/session-copy.json)。Markdown 对话记录保存用户和助手的可见消息及参考图片；原生副本用于继续会话。
