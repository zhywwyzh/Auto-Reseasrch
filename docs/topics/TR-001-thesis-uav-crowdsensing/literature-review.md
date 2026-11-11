# 第 4.2 节的经典与近期研究：证据和差异评估

**方向 B 后续研究（2026-11-10）：** [回训价值深入研究](../../../workspaces/ucs-genrl/direction-b-study.html)已补充收益分解、近邻反证、三层随机性与修订预算；用户已指示沿 B 继续研究。具体协议见该页，本文保留此前方案背景；研究实现及实验尚未启动。

**当前整合评审（2026-11-10）：** [4.2 论文化研究评审](../../../workspaces/ucs-genrl/research-review.html)统一覆盖四项交付，并记录自动科研方法的实际执行、C01–C07 反证决策、2026 新近邻、原文核对与成本口径。课程分配仍为条件候选，尚未定题或启动实现；下文作为已有技术与历史记录保留。

**2026-11-10 深度研究更新：** 当前评审入口为[课程分配深度研究](../../../workspaces/ucs-genrl/curriculum-deep-research.html)，暂按方向 2 为方法主线、方向 3 为组合泛化验证。已补充公开代码与原文差异、GradAlign/PGB/ULEE 等 2026 近邻、固定原任务回训后收益定义及分阶段实验；主次未视为最终选择，创新尚待验证。下方早期路线与实验编号保留为历史讨论，不自动执行。

**方向 2 / 3 增量论证：** 补读 CAMRL 作者版 §III-A/B、Per-Context Reverse Curricula v2（2026-10-11）§2–3，以及 CoDE（2021）、CompoSuite（2022）的出版方摘要，连同 TAC/ATLAS 限定新颖性。4.3 PDF 111–112 已有价值归一化与辅助探索，课程贡献需在保留它们后辨别；组合泛化需控制难度并区分原任务回训、零样本和少样本适应。具体比较与来源见[方向 2 / 3 深化](../../../workspaces/ucs-genrl/direction-a-assessment.html#directions-2-3)。未运行实验。

**维持原定义后的增量核查：** 原 PDF 104–106 已包含多指标反馈及薄弱指标补训，不能把这些当成新增贡献。新查 MRACL（AAAI 2026，DOI 10.1609/aaai.v40i44.41101）的出版方元数据与摘要，已涉及多维奖励空间课程；直连受限，尚未核验完整方法。重查 EnvGen、TAC 作者文稿；当前优先候选是原定义内的任务编辑与效果归因，具体边界见[最新讨论](../../../workspaces/ucs-genrl/direction-a-assessment.html#original-task)。

**同日后续评估：** 最新推荐以[方向 A 立项前评估](../../../workspaces/ucs-genrl/direction-a-assessment.html)为准。新增 RM-guided self-paced RL（UAI 2023）、AGCL（ICAPS 2023）、ATLAS（AAAI 2026，预印本始于 2025）和 TBTCL（作者机构页标注待发表于 NeurIPS 2026）；阅读深度与限制见该页来源卡。收缩“必须充电”硬筛选的贡献，保留资源权衡与课程失配作为待检验问题；没有运行实验。

**2026-11-10 定向复评已完成：** 最新增量来源、阅读深度与判断见[创新性复评 Web UI](../../../workspaces/ucs-genrl/novelty-review.html#sources)，检索清单见[JSON](../../../workspaces/ucs-genrl/design/novelty-search-2026-11-10.json)。补入 PAC、2026 UAV 路径/能耗/多机覆盖课程，以及此前遗漏的 CACL、SCG、轨迹约束课程、CP-DRL 等；EnvGen、TAC、TRACE、Trainee-to-Trainer 的阅读推进到关键方法段。下文保留首轮卡片的实际阅读日期，不把旧摘要卡误写成已完成全文审计。第 E 节的组合机制现降为待讨论工具，最新推荐与边界以复评为准。

检索日期：2026-11-09。用途：选题可行性评估，不是已完成的系统综述。以下只以论文作者、出版方、官方会议/期刊或作者机构页面作为技术依据。预印本不按同行评审结论处理；摘要支持问题和机制的初筛，不能支持完整复现或排除所有细节重合。作者声称的性能不作为本项目已验证结果。

阅读深度分为“原文关键方法”“出版方/作者摘要”“检索返回的出版方正文片段”。没有读到完整实现的来源，不声称已核验代码、许可证或可运行性。论文题名所示年份与正式出版年份不同时注明实际页面信息。

评估口径更新于 2026-11-10：目标为 2026–2027 年投稿，2026 年相关工作属于新颖性审查的必要范围，不能因晚于学位论文而排除。经典工作用于判断基本机制，近期最近邻用于判断新稿的新增贡献，预印本单独标明证据状态。原 4.2 与候选扩展机制接受同一标准。此处日期更新不表示完成了新一轮检索；选题定稿、投稿及修回前需重新检索，并核对可能改变贡献主张的全文、版本与代码。

## A. 经典课程学习与无监督环境设计

**C01 — ALP-GMM。** Portelas 等，*Teacher Algorithms for Curriculum Learning of Deep RL in Continuously Parameterized Environments*，CoRL / PMLR 100，2020。依据：出版方摘要。使用绝对学习进展选择连续参数化环境，是判断 LLM 是否优于非语言自适应任务采样的必要参照。其可借鉴点是环境参数教师；移植时需要统一任务空间与反馈口径。[原始页面](https://proceedings.mlr.press/v100/portelas20a.html)

**C02 — PAIRED。** Dennis 等，*Emergent Complexity and Zero-shot Transfer via Unsupervised Environment Design*，2020 预印本。依据：作者摘要。以策略间后悔值设计环境，提示“难”与“可学”需要区分。它不是 LLM 方法，增加对抗策略的成本也要入账。[原始页面](https://arxiv.org/abs/2012.02096)

**C03 — PLR。** Jiang、Grefenstette、Rocktäschel，*Prioritized Level Replay*，ICML 2021。依据：出版方摘要。任务重放的优先级选择为“必须新生成环境吗”提供竞争性解释；需区分重放已有任务和拓展参数空间。[原始页面](https://proceedings.mlr.press/v139/jiang21b.html)

**C04 — Replay-Guided Adversarial Environment Design。** NeurIPS 2021。依据：出版方/作者摘要。将环境设计与重放结合；用于判断生成器与任务选择是否被混为一项贡献。[原始页面](https://arxiv.org/abs/2110.02439)

**C05 — ACCEL。** Parker-Holder 等，*Evolving Curricula with Regret-Based Environment Design*，ICML 2022。依据：出版方摘要。已有基于后悔值的环境演化路线，不能把“迭代变异环境”单独写成创新。[原始页面](https://proceedings.mlr.press/v162/parker-holder22a.html)

**C06 — PORTAL。** Wu 等，*PORTAL: Automatic Curricula Generation for Multiagent Reinforcement Learning*，AAAI 2024；另有 AAMAS 2023 extended abstract。依据：出版方 PDF 的方法片段及 AAMAS 方法概述。按学习难度与目标任务相关性选课程，并使用共享语义特征促进迁移。这里的相关性代理不能被误写成与本方案完全相同的“成对训练后实测净收益”；但目标迁移导向的课程原则已经存在。后续优先核对其完整选择公式和成本。[AAAI PDF](https://ojs.aaai.org/index.php/AAAI/article/download/29524/30870)；[AAMAS 原文](https://www.ifaamas.org/Proceedings/aamas2023/pdfs/p2460.pdf)

## B. LLM 生成环境与课程：直接机制近邻

**L01 — EnvGen。** Zala 等，*EnvGen: Generating and Adapting Environments via LLMs for Training Embodied Agents*，2024；本轮阅读 arXiv v2（2024-07-12）。依据：全文中的引言、§2 方法及实验设计概述。生成配置→子环境 RL→原环境训练→弱技能反馈，与 4.2 的四步循环在框架层面高度接近。原验证域为 Crafter、Heist，与 UCS 不同。它是首要基线与创新边界；不能把框架相似升级成对学位论文来源或学术不端的判断。[原文](https://arxiv.org/html/2403.12014v2)

**L02 — Eurekaverse。** Liang 等，*Environment Curriculum Generation via Large Language Models*，第 8 届 CoRL，PMLR 270，页面出版年份 2025。依据：出版方摘要。以代码形式生成渐进、可学习且多样的环境，在四足跑酷中验证。它限制“渐进环境生成＋多样性”这一宽泛创新说法；不能将其机器人地形结果直接用于证明无人机采集有效。[原始页面](https://proceedings.mlr.press/v270/liang25a.html)

**L03 — CurricuLLM。** *Automatic Task Curricula Design for Learning Complex Robot Skills using Large Language Models*，arXiv 2024，v2 2025-04；作者提供 ICRA 2025 版本。依据：作者摘要。LLM 设计子任务课程，涉及任务/奖励程序。需区分“改任务与奖励”和本计划“固定评价规则、只改环境参数”，但固定评价器主要保障有效比较，不能单独作为算法创新。[arXiv](https://arxiv.org/abs/2409.18382)；[作者版 PDF](https://hybrid-robotics.berkeley.edu/publications/ICRA2025_CurricuLLM.pdf)

**L04 — TRACE。** Kang 等，*TRACE: Capability-Targeted Agentic Training*，arXiv v2，2026-07-02。依据：v2 作者摘要。对比成功与失败轨迹、识别能力缺口、生成对应环境、训练能力适配器。原对象为语言代理服务/软件任务，不是无人机控制；但“失败诊断＋针对性补训”已存在，不能忽略这一近邻。[原始页面](https://arxiv.org/abs/2604.05336v2)

**L05 — From Trainee to Trainer。** Chen 等，*LLM-Designed Training Environment for RL with Multi-Agent Reasoning*，arXiv，2026-06-16。依据：作者摘要。根据失败轨迹、上下文和环境统计修改下一阶段配置；提出 MAPF-FrozenLake。与本计划的配置生成和失败证据高度相关；其策略是 LLM，多智能体推理测试床不能直接等同 UCS。应核对是否已有与本方案相同的候选接受/迁移测量。[原始页面](https://arxiv.org/abs/2606.17682)

**L06 — TAC。** Yang 等，*Transferability for General Reasoning: An Automated Curriculum for Multi-Domain RLVR*，arXiv v2，2026-06-27。依据：作者摘要。用学习信号和梯度几何估计跨领域迁移，调度训练域。其迁移感知思路是本候选的关键反证；任务域、梯度代理与成对小步实际探测不同，差异是否有价值需实证，不能只改术语。[原始页面](https://arxiv.org/abs/2606.25178v2)

**L07 — GenEnv。** *Difficulty-Aligned Co-Evolution Between LLM Agents and Environment Simulators*，arXiv，2025-12-22。依据：作者摘要及官方会议 PDF 元信息。关注语言代理与环境模拟器的难度对齐；作为“难度对齐不是新机制”的相邻证据，不直接作为 UAV 定量基线。本轮不依第三方页面的会议标签判断版本。[原始页面](https://arxiv.org/abs/2512.19682)

**L08 — Structured Parametric Environments。** Ray，*Curriculum Generation under Structured Parametric Environments for Robust Navigation Policies*，arXiv v1，2026-08-09。依据：作者摘要。非 LLM 的参数化环境课程，涉及导航任务、环境参数调整及分布变化控制。用于提醒最新比较不能只有 LLM；仍为预印本，未复现作者优势主张。[原始页面](https://arxiv.org/abs/2608.08545)

**L09 — Environments as Scaffold。** Yuan 等，*Enriching Feedback to Bootstrap Self-Evolving Agents in Long-Horizon Tasks*，arXiv v1，2026-09-08。依据：作者摘要。通过环境反馈支撑长时域代理学习；与本方案场景不同，用于区分改变反馈和改变环境参数，属于拓展阅读而非首轮强制复现。[原始页面](https://arxiv.org/abs/2609.08404)

## C. 无人机课程、群体感知与约束迁移

**U01 — UAV AoI 与 EPC。** Seong、Jo、Shin，*Age of information minimization in UAV-assisted data harvesting networks by multi-agent deep reinforcement curriculum learning*，Expert Systems with Applications 255，124379，2024。依据：检索返回的出版方摘要/引言片段；直接打开曾返回 403。将 Evolutionary Population Curriculum 用于 UAV 数据采集与 AoI，考虑能量等约束。比普通 UAV 视觉导航更接近本课题，应优先补读方法全文。它否定“首次将课程用于多 UAV 数据采集”的宽泛说法，不能仅据摘要确定是否存在同样的生成/准入机制。[DOI](https://doi.org/10.1016/j.eswa.2024.124379)

**U02 — 充电预算约束多任务群体感知。** Sun 等，*Multi-Task-Oriented UAV Crowd Sensing with Charging Budget Constraint*，MobiHoc 2024，351–360。依据：检索返回的 ACM 摘要；直接访问曾返回 403。多任务约束 MARL 联合移动、感知与充电，摘要报告对未见任务的理论分析和纽约城市事件数据实验。它是场景与证据强度近邻，不是已确认的 LLM 课程论文。不能将能量约束与跨任务泛化单独列为未有人解决的问题。[DOI](https://doi.org/10.1145/3641512.3686367)

**U03 — SA-GCS。** *Semantic-Aware Gaussian Curriculum Scheduling for UAV Vision-Language Navigation*，arXiv v1，2025-08-01。依据：作者摘要及 HTML 方法概述。语义难度与课程采样面向 CityNav 视觉语言导航；与 UCS 的状态、目标、策略不同。作为 UAV 课程相邻方法，不把导航成功率与采集率直接比较。页面对开源时态表述不一致，本轮没有验证代码可用性。[原文](https://arxiv.org/html/2508.00390v1)

**U04 — Deadline-sensitive IoT 数据采集。** Mondal 等，*Deep reinforcement learning based multi-UAV assisted data collection for deadline-sensitive IoT networks*，Physical Communication，2025，102880。依据：出版方摘要。涉及能量、异质数据需求与期限，结合数据采集点选择及 MAPPO 轨迹优化。用于设计有现实含义的期限/能源压力测试，不把其任务自动等同学位论文。[DOI](https://doi.org/10.1016/j.phycom.2025.102880)

**U05 — 2026 UAV 图强化学习数据采集。** *AoI-minimal trajectory planning and data collection in UAVs crowdsensing by graph reinforcement learning*，Computer Networks，2026-03。依据：检索返回的出版方摘要/正文片段；正文未完整取得。其合成轨迹/模型辅助训练提示样本效率还要与非课程机制区分。当前只作为领域最新进展线索，完整算法与基线资格待全文核验。[出版方页面](https://www.sciencedirect.com/science/article/pii/S138912862600068X)

**U06 — 2026 无线供能群体感知。** *Low-Latency and Sustainable Data Collection for Wireless-Powered Multi-UAV Mobile Crowdsensing Through Resource Allocation*，IEEE TVT，机构页面标注 2026-08-28 online。依据：作者所属机构成果摘要。涉及无线供能、带宽/功率与轨迹等耦合资源分配。用于判断 TMC 路线需要多强的系统约束证据；不是生成式课程的同问题算法，当前不强制实现。[作者机构记录](https://scholars.cityu.edu.hk/en/publications/low-latency-and-sustainable-data-collection-for-wireless-powered-/)；[DOI](https://doi.org/10.1109/TVT.2026.3728432)

## D. Auto Research 方法怎样实际帮助本课题

这一层用于管理研究过程，不是 UCS 算法的原创模块。已有仓库全文阅读包继续使用；本轮重点更新以下来源。

**R01 — EPOCH，2026-10-04。** 依据：作者摘要及已有本地阅读材料。采用任务合同、证据分型、主动反证和独立重跑。落实为：用户确认/原文事实/外部来源/候选假设分开；找到 EnvGen、TRACE、TAC 后主动收缩贡献；把“有曲线”与“支持因果/泛化主张”分开。[来源](https://arxiv.org/abs/2610.06986)

**R02 — EvoScientist v2，2026-10-05。** 依据：作者摘要。采用持续记录可行方向和失败原因的思想。本轮更新旧发表状态并保留历史假设，避免下次再次寻找不存在的 4.2 源代码。没有部署其多智能体系统。[来源](https://arxiv.org/abs/2603.08127v2)

**R03 — Fork-and-Flush，2026-10-05。** 依据：作者摘要。原工作通过刷新上下文和分支搜索避免困在相似想法中。本轮只借鉴“允许另起竞争路线”的审查原则：工程化原框架、迁移准入、删除 LLM 的经典课程三种解释都保留。没有启动其并行代理或把其效果数字迁移到本项目。[来源](https://arxiv.org/abs/2610.07447)

**R04 — OpenScholar、Co-Scientist、autoresearch、PaperBench/AstaBench。** 继续采用已有[规程](methodology.md)：来源支持的阅读、提出与批判候选、冻结评价器与预算、按环境/算法/数值/结论分层复验。当前实际完成的是研究设计和证据核验，执行闭环必须等待用户评估计划。原系统的性能不构成该 UAV 方法有效的证据。

## E. 当前贡献审查结论

不保留为独立创新：LLM 生成环境、反馈反思、一般失败诊断、课程难度调度、目标迁移感知、单独加入能量约束。这些均有相关先例。

保留为**待评估的具体组合机制**：围绕采集—充电—多机协同的任务依赖，限定候选干预范围，用成对、计成本的实际目标迁移探测决定准入，并研究其何时优于相关性/难度代理。不能仅凭尚未找到同名论文宣布创新；需要与 C06、L01、L02、L04–L06、U01–U02 做全文逐机制比较。

最值得优先补读：EnvGen 附录与公开实现；PORTAL 的选择公式；UAV-EPC 的扩展策略；TRACE/From Trainee to Trainer 的候选筛选细节；TAC 的迁移估计；MobiHoc 2024 的约束及未见任务定义。代码只读核验不等于获准启动实验。

## F. 检索覆盖与未覆盖部分

本轮组合检索方向包括 LLM environment generation / adaptive curricula / UAV crowdsensing / multi-agent curriculum / target transfer / energy constraints，追溯经典 UED，并补检 2025–2026 的环境生成与 Auto Research。代表性实际检索式：

- `UAV crowdsensing large language model curriculum reinforcement learning environment generation 2025 2026`
- `UAV mobile crowdsensing multi task reinforcement learning energy data collection 2024 2025 2026 curriculum`
- `"PORTAL" "Automatic Curricula Generation" transfer gain`
- `"Transferability for General Reasoning" arxiv`
- `"Age of information minimization" "curriculum" "EPC"`
- 精确题名及 arXiv/出版方链接核验。

使用日期/版本是为了控制证据时效，不表示检索穷尽至当日全部论文。部分出版方全文受访问限制，代码可运行性未验证；本轮没有系统遍历所有引文网络、中文数据库或完成数值复现。上述限制不妨碍否定已被直接近邻覆盖的宽泛主张，但使“完整新颖性成立”仍然悬而未决。
