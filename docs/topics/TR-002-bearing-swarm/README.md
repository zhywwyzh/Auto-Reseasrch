# TR-002：方位角互定位与可认证主动规划

2026-11-11 根据用户新指令建立，独立于 TR-001 / UCS-GenRL。

主要阅读入口：[论文预审与补强方案](../../../workspaces/bearing-swarm-review/index.html)。

2026-11-11 用户进一步明确：先完成仿真实验，再考虑实机。最新规格为[仿真测试集、环境和硬件](../../../workspaces/bearing-swarm-review/benchmark.html#simulation-resources)，保存在 `benchmark.json` 的 `simulation_resources` 中。已盘点当前执行主机，提出数值环境→轻量闭环→可选SITL的顺序；未安装依赖、运行求解器或启动实验。实机/公开数据条目保留作后续背景，不作为本轮前置条件。

最新实验入口：[实验协议与 benchmark 注册表](../../../workspaces/bearing-swarm-review/benchmark.html)，单一内容源为 [benchmark.json](../../../workspaces/bearing-swarm-review/benchmark.json)。2026-11-11 已细化固定日志/闭环对照、强基线、公开数据适用性、数据划分、独立证书检查与统计门槛。协议版本0.1尚未冻结：自建 benchmark 未实现，公开实测数据尚未接入，可靠性未完成先导验证。不得将样本配额、数值阈值或原论文结果表述为本项目已验证结果。此页优先于旧计划中的粗略实验与样本建议。

最新实际进展：[P0/P1研究记录与证明草稿](../../../workspaces/bearing-swarm-review/plan.html#progress)，来源为 [research-progress.json](../../../workspaces/bearing-swarm-review/research-progress.json)。已开始证书重推和无噪选择性加强分析，形成D0–D5手工推导稿；尚未独立复核，不认领原创或实验验证。P0/P1仅部分完成，创新准入尚未通过。

详细执行入口：[分阶段补强计划](../../../workspaces/bearing-swarm-review/plan.html)，内容源为 [plan.json](../../../workspaces/bearing-swarm-review/plan.json)。包括P0–P5阶段、理论卡片、强基线、实验指标、接口、预算、C2/C3分支及论文证据对应。所有时间与样本量均为计划；尚未启动研究实现或实验。用同一 `build.py` 生成三个阅读页面及Canvas视图。

内容源：首轮 [review.json](../../../workspaces/bearing-swarm-review/review.json)，第二轮 [novelty.json](../../../workspaces/bearing-swarm-review/novelty.json)；用同目录 `build.py` 生成静态 HTML，`--canvas-source` 输出 IDE Canvas 源码。修改内容后重新生成，避免多份分析漂移。

当前对象是王英建《基于方位角的多无人机互定位与协同规划研究》第4章，对应候选预印本 [arXiv:2401.07784v1](https://arxiv.org/abs/2401.07784v1)。作者及章节内容已核对，确切投稿版本、目标 venue 与审稿意见仍待用户补充。暂未接受的状态依据用户2026-11-11说明，不推断曾被正式拒稿或具体原因。

本轮完成文献阅读、页码定位、手工数学核查与研究计划；没有运行外部评审系统、付费模型、研究实验或实现。主要发现是局部扰动分解的对称性矛盾、条件保证的边界，以及独立贡献的实验归因缺口。详细证据、分项评分、候选及停止条件以Web页面为准。

原学位论文保留在 `thesis-reference/theses/博士论文.pdf`。下载的预印本位于 `thesis-reference/related-papers/TR-002-bearing-swarm/`，全文提取、物理页索引和页图位于 `thesis-reference/notes/TR-002-bearing-swarm/`，均遵循Git忽略边界。

2026-11-11 第二轮已补充强近邻与解析反证：两条不平行方位足以唯一确定 SO(3) 相对旋转，但原 O(3)/Gram 松弛仍可出现反射与高秩最优解，严格谱裕量可以为零。这是限定条件下的解析核查，不是新的实验或已确认原创定理。2025 ICCV 已有更强的手性约束，2024 T-RO 已有自动紧化与信息矩阵联系，2026 也有退化认证和 BPE 新工作，均作为必须回应的近邻。

当前优先级：C1 收窄到保持原目标的认证方式与观测运动联合选择；C2 仅在解决观测退出与重观测延迟的保证后保留；C3 暂作工程支撑。页面已给出逐方向理论门槛、最小强基线、否决条件、实验归因和论文收敛方案，不预先保证每条方向都能独立发表。

继续工作顺序：补全版本核对与关键证明修复 → 写清现成强松弛的直接适配及剩余理论差额 → 用户评估实验计划 → 再进入实现与实验 → 独立复验。文献检索与设计可继续，不必等待审稿意见才能推进；缺少实际审稿材料时不能认定真实未录用原因。
