# TR-003：几何表征与整身运动规划综述

本目录只属于TR-003。[三课题总入口](../index.html) · [研究首页](index.html) · [编辑器工作区](TR-003-geometry-survey.code-workspace) · [最新记录](../../docs/topics/TR-003-geometry-planning-survey/README.md)。

输入：`thesis-reference/theses/zjuthesis.pdf`。王钱浩学位论文背景下的新综述；几何约束转换及保证边界。

综述证据编码、正文和解析示例归本课题；不是TR-002的新定位算法或TR-001训练实验。

内容源：`survey.json`；运行本目录 `build.py` 只生成本课题阅读页面。未来环境置于本目录 `.venv/`，数据与实验产物分别使用 `datasets/`、`runs/`，实施前确认Git忽略。当前没有因建立入口而启动研究实现或实验。

原始资料与阅读笔记在被忽略的 `thesis-reference/notes/TR-003-zjuthesis-survey`；稿件源码现位于 `papers/geometry-planning-survey`，由 `build_manuscript.py` 从同一内容源生成。共享方法论可引用，不能把其他课题结果或授权搬入本课题。

独立编辑器入口仅减少误选文件；仍共享仓库Git状态，不提供分支或进程隔离。


2026-11-11 v0.4：目标已确认《自动化学报》，用户授权直接撰写核心内容并由投稿人后续审核。[正文阅读页](manuscript.html)与[投稿核验入口](index.html#aas-rules)已分开；六篇已刊综述统计、15项官方规则与8项模板要求在研究页内。正文约9千字，实际引用32条，3表2图；来源库57条，不能当作最终系统检索纳入数。

[稿件与编译说明](../../papers/geometry-planning-survey/README.md)。XeLaTeX因系统缺ctexart.cls未编译成功；阅读PDF为浏览器排版。完整近邻对照和独立复核尚未完成，不宣称稿件已经具备投稿资格。页面源文件适用于可访问本仓库的电脑；运行主机环回地址不等于公网或跨设备入口。
