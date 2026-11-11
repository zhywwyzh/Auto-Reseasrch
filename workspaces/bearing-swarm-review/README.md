# TR-002：方位角互定位与协同规划补强

本目录只属于TR-002。[三课题总入口](../index.html) · [研究首页](index.html) · [编辑器工作区](TR-002-bearing-swarm.code-workspace) · [最新记录](../../docs/topics/TR-002-bearing-swarm/README.md)。

输入：`thesis-reference/theses/博士论文.pdf`。王英建学位论文第4章；匹配arXiv:2401.07784v1。

保持bearing/里程计目标；当前先做仿真，实机后置。与UCS训练/课程分配无关。

内容源：`review.json`、`novelty.json`、`plan.json`、`research-progress.json`、`benchmark.json`；运行本目录 `build.py` 只生成本课题阅读页面。当前数值环境使用本目录 `container/` 独立 Docker 镜像，详见[构建与验收说明](container/README.md)；可选宿主虚拟环境仍只能放本目录 `.venv/`，数据与实验产物分别使用 `datasets/`、`runs/`，实施前确认Git忽略。当前没有因建立入口而启动研究实现或实验。

原始资料与阅读笔记在被忽略的 `thesis-reference/notes/TR-002-bearing-swarm`；未来稿件预留 `papers/bearing-swarm`，尚未因此创建稿件。共享方法论可引用，不能把其他课题结果或授权搬入本课题。

独立编辑器入口仅减少误选文件；仍共享仓库Git状态，不提供分支或进程隔离。

2026-11-11：已按用户要求构建容器并实际通过环境验收，详见[容器验收页面](benchmark.html#container-validation)和[结构化记录](container/validation.json)。仅运行依赖、IO、隔离检查与小型已知答案SDP，没有启动正式无人机实验。

2026-11-11 后续用户已授权启动研究实验：已实际完成[首轮旋转先导](benchmark.html#pilot-results)，代码和协议见[experiments/pilot](experiments/pilot/README.md)。这更新了此前“未启动研究实现”的状态；仅完成诊断和开发集，严格认证、平移/闭环与留出评估尚未完成。
