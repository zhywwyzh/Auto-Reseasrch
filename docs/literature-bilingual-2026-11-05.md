# Auto Research 文献中英对照阅读包与时效性复核

复核日期：2026-11-05。范围：原清单 20 项资料，新增 6 项近期工作，共 26 项。资料包括论文、基准和工程仓库，不把它们一律称为论文。

2026-11-09 更新：指定的 8 篇论文和 autoresearch 文档的 [全文中英对照初译](../translations/fulltext/README.md) 已独立提供。下面这份材料保留为概览阅读卡，英文释义仍不是原文摘要。

## 内容边界

- **原文短句与翻译**：每项保留一个短引文，中文为该短句的翻译，原始位置标在条目中。
- **英文释义与中文对照**：英文为本项目重新撰写的核心内容释义，中文为对应翻译；不是原论文摘要，也不是全文翻译。
- **方法与证据**：基于此次核对的摘要、版本记录、正式发表元数据或作者说明；没有逐篇完成全文精读与实验复现。
- **局限、时效性判断和项目用途**：是本次研究分析，不是论文作者的原话。
- Nature 两个链接本次直达出现跳转限制；OpenScholar 结合预印本与出版方索引核对，AI Scientist 综合版结合前次可读内容与本次出版方索引核对。未声称重新完成全文审计。
- 旧文献结果、作者自报收益、代码公开与独立复现分别看待；未检查全部仓库的依赖、commit 和可执行性。

## 对此前阅读路线的修正

此前清单适合作为入门地图，但作为当前前沿路线不够完整；不能用“这些都是经典”解释所有早期条目的保留。当前将资料分成方法基础、历史对照、核心更新、近期候选、工程入口和领域基线。

1. **旧实验成绩最容易失效。** 旧模型的能力、成本和排名不应直接当成当前能力上限。
2. **工程实现可能失效。** 需要检查模型 API、依赖、上下文管理和仓库状态，未检查时标为未确认。
3. **方法是否过时需受控比较。** 强模型可能使某些复杂流程失去价值，但发布日期本身不能证明它们无效。
4. **评价问题往往更持久。** 引用是否支持主张、是否公平比较、是否独立重跑仍需要解决。
5. **正式发表新不等于方法新。** OpenScholar 的 2026 正式版不应被当作完全不同于 2024 预印本的新范式；AI Scientist 系列也不能重复计为独立验证。
6. **新预印本不自动更可靠。** 近期候选需检查对照、代码、预算和证据，不能因日期新就当作最强方法。

## 建议的阅读次序

- 综述主线：22 SurveyLens → 23 Bloom-Eval → 21 SurGE → 02 OpenScholar → 24 SurveyGraph；01 AutoSurvey 和 03 SurveyForge 用作历史流程对照。
- 科研闭环：26 Into the Unknown → 10 AstaBench → 11 PAPERBENCHX → 25 EvoScientist → 13 EPOCH → 06 Co-Scientist 最新版；04/05 用来理解研究谱系，07 用于记忆设计。
- 工程起步：08 autoresearch，阅读其受限实验循环，再适配自己的仿真任务。
- 无人机文献：15–20 单独作为实验领域资料；它们不是 Auto Research 方法先进性的证据。

## 维护方式

每月按研究问题检索近期方法与评测，每次正式实验开始和投稿前再更新一次。记录首发、最新修订、正式发表、检索日期、采用的模型版本和代码 commit。维护工作是否自动运行需另行安排，本次没有建立定时任务。

## 逐项阅读卡

### 01. AutoSurvey

**英文题名：** AutoSurvey: Large Language Models Can Automatically Write Surveys

**中文题名：** AutoSurvey：大语言模型能够自动撰写综述

**来源：** [原始页面](https://papers.nips.cc/paper_files/paper/2024/hash/d07a9fc7da2e2ec0574c38d5f504d105-Abstract-Conference.html)

**首发记录：** 2024。**本次采用/核对版本：** NeurIPS 2024 正式版。

**分类与用途：** 文献综合 / 历史对照。保留流程基线；不再承担当前最优方法的角色。

**原文短句：**

> initial retrieval and outline generation

**短句翻译：** 初始检索与大纲生成。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** AutoSurvey divides survey writing into retrieval, outline planning, section drafting, and revision. It is useful for understanding how a large writing task becomes a sequence of smaller tasks with supporting literature.

**中文对照：** AutoSurvey 将综述写作拆为检索、大纲规划、分节起草和修订。它有助于理解如何将大型写作任务分解成由文献支持的较小任务序列。

**方法总结：** 先收集领域材料再组织结构，按小节生成并整合，配套评价与迭代。

**验证证据：** NeurIPS 2024 论文提供方法和实验；本次未重跑代码，不能据此断言其在当前模型上仍占优。

**局限与时效性判断：** 早期上下文限制与模型能力会影响设计。不要直接沿用旧提示词、模型排名或质量分数。

**对本项目的建议：** 在同一批无人机论文与同一基础模型上复现其流程，作为历史对照；补读 21–24。

### 02. OpenScholar

**英文题名：** OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs

**中文题名：** OpenScholar：利用检索增强语言模型综合科学文献

**来源：** [原始页面](https://arxiv.org/abs/2411.14199)；[补充原始来源](https://www.nature.com/articles/s41586-025-10072-4)

**首发记录：** 2024-11-21。**本次采用/核对版本：** Nature 论文版 2026-02-04；arXiv 仍为 2024 v1。

**分类与用途：** 文献综合 / 方法基础。保留证据检索与综合方法；优先核对正式版，旧排行榜只作历史记录。

**原文短句：**

> synthesizing citation-backed responses

**短句翻译：** 综合生成有引用支持的回答。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** OpenScholar retrieves relevant scientific passages and uses them to construct cited answers. Its main lesson is that literature access and evidence grounding must be evaluated separately from a model's ability to write fluent explanations.

**中文对照：** OpenScholar 检索相关科学文献片段，并据此构建带引用的回答。其主要启示是：文献获取和证据支撑应与模型撰写流畅解释的能力分别评价。

**方法总结：** 大规模学术检索、证据片段与反馈迭代结合；ScholarQABench 用于评价科学文献问答。

**验证证据：** 核对预印本摘要及 Nature 正式版元数据。两个版本的数据口径应各自引用，不混用；本次未做全文版本差异审计。

**局限与时效性判断：** 历史 GPT-4o 对比不代表 2026 年模型能力；长答案问答也不等于完整综述。

**对本项目的建议：** 为每条无人机研究结论保存证据位置，区分引用存在与引用支持该结论。

### 03. SurveyForge / SurveyBench

**英文题名：** SurveyForge: On the Outline Heuristics, Memory-Driven Generation, and Multi-dimensional Evaluation for Automated Survey Writing

**中文题名：** SurveyForge：自动综述写作中的大纲启发式、记忆驱动生成与多维评价

**来源：** [原始页面](https://aclanthology.org/2025.acl-long.609/)

**首发记录：** 2025-03-06。**本次采用/核对版本：** ACL 2025 正式版（2025-07）。

**分类与用途：** 文献综合 / 历史对照。纠正此前仅标为预印本的记录；保留大纲和记忆基线，补充新评价。

**原文短句：**

> outline quality and citation accuracy

**短句翻译：** 大纲质量和引用准确性。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** SurveyForge uses existing survey structures and retrieved papers to plan and write a review. SurveyBench separates reference, outline, and content assessment, making it easier to diagnose why a generated survey is weak.

**中文对照：** SurveyForge 利用已有综述的结构及检索论文来规划和撰写综述。SurveyBench 分别评价参考文献、大纲和内容，便于定位生成综述质量不佳的原因。

**方法总结：** 参考人工大纲的组织方式，由学术导航与记忆检索支持内容生成和修订。

**验证证据：** 论文使用包含 100 篇人工综述的 SurveyBench；报告优于当时的 AutoSurvey 等对照。

**局限与时效性判断：** 不能把当时的胜率当作现在的最优结论；模仿人工大纲也可能限制新的分类方式。

**对本项目的建议：** 分别评价结构、证据与综合深度；使用 SurveyLens、Bloom-Eval 扩展评价。

### 04. The AI Scientist-v2

**英文题名：** The AI Scientist-v2: Workshop-Level Automated Scientific Discovery via Agentic Tree Search

**中文题名：** AI Scientist-v2：通过智能体树搜索实现工作坊水平的自动科学发现

**来源：** [原始页面](https://arxiv.org/abs/2504.08066)

**首发记录：** 2025-04-10。**本次采用/核对版本：** arXiv v1；另有 2026 年系列综合论文。

**分类与用途：** 科研闭环 / 历史对照。保留实验树搜索入门；正式比较需加入近期闭环系统。

**原文短句：**

> eliminates the reliance on human-authored code templates

**短句翻译：** 消除对人工编写代码模板的依赖。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** AI Scientist-v2 organizes research as a search over experimental implementations, connecting hypotheses, code execution, analysis, and manuscript writing. It demonstrates an end-to-end workflow, while its workshop results provide limited evidence about general research quality.

**中文对照：** AI Scientist-v2 将研究组织为对实验实现的搜索，连接假设、代码执行、分析与论文写作。它展示了端到端流程，但工作坊评审结果对普遍科研质量的证明范围有限。

**方法总结：** 实验管理 Agent 调度渐进式树搜索，并通过视觉语言反馈改进图表。

**验证证据：** 作者报告向 ICLR workshop 提交三份自主生成稿件，其中一份达到录用标准。

**局限与时效性判断：** 三个案例不能说明稳定产出主会论文；是否运行了实验与论断是否正确仍需独立核验。

**对本项目的建议：** 借鉴候选分支与实验状态管理，不沿用其论文评分替代无人机指标。

### 05. AI Scientist / Nature 综合版

**英文题名：** Towards end-to-end automation of AI research

**中文题名：** 迈向 AI 研究的端到端自动化

**来源：** [原始页面](https://www.nature.com/articles/s41586-026-10265-5)

**首发记录：** 2026-03-25（正式论文）。**本次采用/核对版本：** Nature 651, 914–919 (2026)。

**分类与用途：** 科研闭环 / 方法基础。作为 AI Scientist 系列综合阅读入口；与 v2 按同一研究谱系处理。

**原文短句：**

> Only one of three submissions was accepted

**短句翻译：** 三份投稿中只有一份被录用。

**引文位置：** 出版方索引所示正文片段。

**英文释义（自行撰写，非原文摘要）：** This paper brings together template-based and more open-ended AI research workflows. It helps compare levels of automation, but a publication about an AI scientist is different from a paper produced by that scientist.

**中文对照：** 这篇论文综合讨论基于模板和更开放的 AI 科研流程，有助于比较自动化程度。但研究 AI 科学家的论文，与 AI 科学家自身产出的论文，是不同的评价对象。

**方法总结：** 贯通想法生成、实验、分析、写作和审稿，并比较不同模型与计算投入。

**验证证据：** 正式出版日期已核对；本次全文直达受站点跳转影响，使用出版方索引与前次已核对内容，未重新精读全文。

**局限与时效性判断：** Nature 出版的是系统研究；不能说该系统自主产出了这篇 Nature 论文。

**对本项目的建议：** 厘清“系统论文”“系统产物”“外部验证”三个层级，避免混为成功证据。

### 06. Co-Scientist

**英文题名：** Accelerating scientific discovery with Co-Scientist

**中文题名：** 借助 Co-Scientist 加速科学发现

**来源：** [原始页面](https://arxiv.org/abs/2502.18864v2)

**首发记录：** 2025-02-26。**本次采用/核对版本：** 2026-06-29 v2；页面标注 Nature 2026。

**分类与用途：** 科研闭环 / 核心更新。应读 2026 修订版；不能仅按 2025 首发判断其时效性。

**原文短句：**

> a tournament evolution process for self-improving hypotheses generation

**短句翻译：** 通过锦标赛式演化改进假设生成的过程。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** Co-Scientist repeatedly generates, critiques, ranks, and revises hypotheses in response to a research objective. Its biomedical validations illustrate why hypothesis selection should eventually connect to external experiments rather than remain an internal debate.

**中文对照：** Co-Scientist 围绕研究目标反复生成、批评、排序和修订假设。其生物医学验证说明，假设筛选最终应连接外部实验，而不能停留在系统内部讨论。

**方法总结：** 异步多 Agent 协作与锦标赛演化，增加推理时计算以改进候选假设。

**验证证据：** 作者在药物再利用、靶点与耐药机制等应用中验证，并报告部分体外实验。

**局限与时效性判断：** 生物医学案例不能直接证明无人机适用性；内部排名也不是实际实验收益。

**对本项目的建议：** 让多个候选解释接受相同实验检验，记录排名与最终复验结果是否一致。

### 07. Kosmos

**英文题名：** Kosmos: An AI Scientist for Autonomous Discovery

**中文题名：** Kosmos：面向自主发现的 AI 科学家

**来源：** [原始页面](https://arxiv.org/abs/2511.02824v2)

**首发记录：** 2025-11-04。**本次采用/核对版本：** 2025-11-05 v2。

**分类与用途：** 科研闭环 / 方法基础。保留长期研究记忆案例；与 EvoScientist 等近期工作比较。

**原文短句：**

> a structured world model

**短句翻译：** 结构化世界模型。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** Kosmos connects literature search and data analysis through shared structured research state. Here, world model refers to organized scientific knowledge and findings, not necessarily a learned physical simulator for robot control.

**中文对照：** Kosmos 通过共享的结构化研究状态连接文献检索与数据分析。这里的世界模型指组织起来的科学知识与发现，并不必然是机器人控制中的学习式物理仿真器。

**方法总结：** 围绕目标与数据交替检索、提出假设、运行分析，并保存支持报告的文献或代码来源。

**验证证据：** 论文报告多个领域案例；其效率换算主要来自合作研究者评价，不能当作统一受控生产率结论。

**局限与时效性判断：** 报告可追溯不意味着所有陈述正确；其研究记忆也不能直接替代导航世界模型。

**对本项目的建议：** 建立假设、实验、负结果之间的研究记忆，而不是把所有日志塞进上下文。

### 08. karpathy/autoresearch

**英文题名：** autoresearch: AI agents running research on single-GPU nanochat training automatically

**中文题名：** autoresearch：让 AI 智能体自动开展单 GPU 训练实验

**来源：** [原始页面](https://github.com/karpathy/autoresearch)

**首发记录：** README 说明日期为 2026-03。**本次采用/核对版本：** 仓库页面核对于 2026-11-05；未固定 commit。

**分类与用途：** 科研闭环 / 工程入口。保留作轻量闭环入口；它不是同行评审论文。

**原文短句：**

> keeps or discards, and repeats

**短句翻译：** 保留或丢弃，然后重复。

**引文位置：** 作者项目页或 README 正文。

**英文释义（自行撰写，非原文摘要）：** The repository gives an agent a constrained training experiment and a fixed evaluation metric. The agent changes code, runs a short training cycle, and keeps or rejects the result, providing a compact example of automated empirical search.

**中文对照：** 这个仓库为 Agent 提供受限训练实验和固定评价指标。Agent 修改代码、运行短训练周期并保留或拒绝结果，构成紧凑的自动经验搜索示例。

**方法总结：** README 区分固定准备/评价文件、Agent 可修改训练文件和人编写的研究指令；每次训练预算五分钟。

**验证证据：** 作者仓库说明了工程循环；没有将其作为科研新颖性的同行评审证据。

**局限与时效性判断：** 同一验证指标反复优化可能过拟合；代码可运行不等于发现新知识。

**对本项目的建议：** 借鉴受限修改和结果日志，把训练指标换成固定仿真评价，并独立留出终验集。

### 09. PaperBench

**英文题名：** PaperBench: Evaluating AI's Ability to Replicate AI Research

**中文题名：** PaperBench：评价 AI 复现 AI 研究的能力

**来源：** [原始页面](https://arxiv.org/abs/2504.01848v3)

**首发记录：** 2025-04-02。**本次采用/核对版本：** 2025-04-07 v3。

**分类与用途：** 评测 / 方法基础。保留任务拆解和评分设计；废止将原始模型分数当作当前能力上限。

**原文短句：**

> replicate 20 ICML 2024 Spotlight and Oral papers from scratch

**短句翻译：** 从零复现 20 篇 ICML 2024 Spotlight 和 Oral 论文。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** PaperBench evaluates whether agents can turn research papers into working implementations and experiments. Its hierarchical rubrics make partial progress observable, but partial implementation scores must not be confused with complete scientific reproduction.

**中文对照：** PaperBench 评价 Agent 能否将论文转化为可运行实现和实验。分层评分标准让部分进展可见，但部分实现得分不能等同于完整的科学复现。

**方法总结：** 与论文作者协作定义细粒度任务，并检验自动评分器。

**验证证据：** 论文包含 20 篇研究、8,316 个可评分子任务；历史模型成绩属于当时的配置。

**局限与时效性判断：** 复现任务不直接衡量原创发现；应重新运行当前模型并检查评分器误差。

**对本项目的建议：** 将无人机复现拆为环境、关键机制、结果重现及结论支持四层。

### 10. AstaBench

**英文题名：** AstaBench: Rigorous Benchmarking of AI Agents with a Scientific Research Suite

**中文题名：** AstaBench：利用科学研究任务套件严格评测 AI 智能体

**来源：** [原始页面](https://arxiv.org/abs/2510.21652v2)；[补充原始来源](https://allenai.org/blog/astabench-update-spring-2026)

**首发记录：** 2025-10-24。**本次采用/核对版本：** 2026-04-21 v2；ICLR 2026。

**分类与用途：** 评测 / 核心更新。保留为受控评测核心；排行榜是时点数据，不作为永久排名。

**原文短句：**

> model cost and tool access

**短句翻译：** 模型成本与工具访问权限。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** AstaBench evaluates scientific agents across literature, coding, analysis, and discovery tasks. Its emphasis on standardized tools and costs helps distinguish improvements in agent design from advantages caused by better models or extra resources.

**中文对照：** AstaBench 跨文献、编码、分析和发现任务评价科研 Agent。它强调标准化工具和成本，有助于区分 Agent 设计改进与更强模型、更多资源带来的优势。

**方法总结：** 统一科学工具环境、任务接口和多类基线；覆盖 2,400 余个问题。

**验证证据：** v2 与 ICLR 2026 状态已核对；官方 2026-04-30 更新另报告新模型评测。

**局限与时效性判断：** 综合分数掩盖任务差异；尚不能直接预测无人机研究能力。

**对本项目的建议：** 冻结工具权限、文献时间范围和预算，分别报告各研究子任务表现。

### 11. PAPERBENCHX

**英文题名：** PAPERBENCHX: Can AI Reproduce Science Across Disciplines?

**中文题名：** PAPERBENCHX：AI 能否跨学科复现科学研究？

**来源：** [原始页面](https://arxiv.org/abs/2610.39744)

**首发记录：** 2026-10-29。**本次采用/核对版本：** 2026-10-29 v1 预印本。

**分类与用途：** 评测 / 近期候选。优先读重跑评分机制；新结果仍需独立复核。

**原文短句：**

> score only regenerated evidence

**短句翻译：** 仅对重新生成的证据评分。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** PAPERBENCHX asks agents to reconstruct experiments using domain-specific scientific environments. Submissions are rerun and judged on regenerated evidence, making the distinction between plausible reports and reproducible results central to evaluation.

**中文对照：** PAPERBENCHX 要求 Agent 使用领域科学环境重建实验。提交物需重新运行，并按重新生成的证据评分，因此评价重点是区分看似合理的报告与可复现结果。

**方法总结：** 覆盖 93 项任务、12 个研究方向，使用领域环境和专家标准。

**验证证据：** 作者报告最优配置仅有约 14% 任务达到其 90% 完整复现阈值；不能换算成所有科研任务成功率。

**局限与时效性判断：** 新近预印本；任务和计算预算与无人机实验未必匹配。

**对本项目的建议：** 候选必须在干净环境中重跑，再读取日志评分，不接受报告自述成绩。

### 12. Can LLMs Generate Novel Research Ideas?

**英文题名：** Can LLMs Generate Novel Research Ideas? A Large-Scale Human Study with 100+ NLP Researchers

**中文题名：** 大语言模型能否提出新颖研究想法？一项涉及百余位 NLP 研究者的人类研究

**来源：** [原始页面](https://proceedings.iclr.cc/paper_files/paper/2025/hash/ea94957d81b1c1caf87ef5319fa6b467-Abstract-Conference.html)

**首发记录：** 2024-09-06。**本次采用/核对版本：** ICLR 2025 正式版。

**分类与用途：** 评测 / 方法基础。纠正仅列预印本的记录；保留盲评设计，不沿用旧能力判断。

**原文短句：**

> slightly weaker on feasibility

**短句翻译：** 在可行性方面略弱。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** This study compares human and AI research proposals using expert blind reviews. It separates perceived novelty from feasibility, showing why an attractive idea should be evaluated again after implementation and experimentation.

**中文对照：** 该研究通过专家盲评比较人类与 AI 的研究提案，并区分感知到的新颖性与可行性。这说明一个吸引人的想法仍应在实现和实验后再次评价。

**方法总结：** 招募百余位 NLP 研究者生成与盲审想法，控制比较中的混杂。

**验证证据：** 在该设置中 AI 想法被评为更新颖、可行性略弱；它没有证明 AI 全流程科研优于人类。

**局限与时效性判断：** 基于文本提案的偏好受呈现与评审影响；也不能外推到无人机。

**对本项目的建议：** 新颖性、可实现性、实验价值分开打分，再跟踪这些评分能否预测实际结果。

### 13. EPOCH

**英文题名：** EPOCH: Reliable Discovery through Evidence-Governed Search

**中文题名：** EPOCH：通过证据约束的搜索实现可靠发现

**来源：** [原始页面](https://arxiv.org/abs/2610.06986)

**首发记录：** 2026-10-04。**本次采用/核对版本：** 2026-10-04 v1 预印本。

**分类与用途：** 科研闭环 / 近期候选。与拟议课题高度相关；作为最近邻检查对象，不先验认定有效。

**原文短句：**

> active falsification, admission checks, and independent replay

**短句翻译：** 主动反证、准入检查和独立重跑。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** EPOCH adds explicit rules for how search results become accepted claims. It combines evidence tracking, falsification, and replay so that a promising score is not automatically treated as a scientific discovery.

**中文对照：** EPOCH 明确规定搜索结果如何成为被接受的主张。它结合证据追踪、反证和重跑，避免自动把有希望的分数当作科学发现。

**方法总结：** 任务契约、类型化记忆、反证、主张准入与独立重放构成闭环。

**验证证据：** 作者在算法优化和数学等任务上报告收益；本次未复现实验，不将作者的最优主张视为独立确认。

**局限与时效性判断：** 无需再以“加入证据审核”为创新；计算任务验证器也未必适合噪声较大的机器人任务。

**对本项目的建议：** 研究条件化证据和实验选择的额外价值，并在固定预算下与这种机制对照。

### 14. Sound Agentic Science Requires Adversarial Experiments

**英文题名：** Sound Agentic Science Requires Adversarial Experiments

**中文题名：** 可靠的智能体科学需要对抗性实验

**来源：** [原始页面](https://arxiv.org/abs/2604.22080v2)

**首发记录：** 2026-04-23。**本次采用/核对版本：** 2026-05-20 v2；ICLR 2026 workshop。

**分类与用途：** 评测 / 方法基础。保留研究设计原则；不将立场论文当作充分性能证据。

**原文短句：**

> A fluent explanation or a significant result on a single dataset is not verification.

**短句翻译：** 流畅的解释或单一数据集上的显著结果，并不构成验证。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** The paper argues that agents should search for ways a claim can fail. This reframes scientific assistance from constructing persuasive narratives toward designing challenges that expose weak assumptions and selective analysis.

**中文对照：** 论文主张让 Agent 主动寻找主张可能失败的方式，从而将科研辅助的重心由构造有说服力的叙述转向设计能暴露薄弱假设与选择性分析的检验。

**方法总结：** 提出以反证优先的标准评价 Agent 辅助产生的科学主张。

**验证证据：** 属于方法论与立场性质的 workshop 论文；不能以其观点替代你的受控实验。

**局限与时效性判断：** “做反证”本身已经是现有原则；还需量化其收益和额外成本。

**对本项目的建议：** 每个候选附带失败预测，且记录淘汰了多少无效改进、误拒了多少有效改进。

### 15. EGO-Planner

**英文题名：** EGO-Planner: An ESDF-free Gradient-based Local Planner for Quadrotors

**中文题名：** EGO-Planner：一种无需 ESDF 的四旋翼梯度式局部规划器

**来源：** [原始页面](https://arxiv.org/abs/2008.08835v2)

**首发记录：** 2020-08-20。**本次采用/核对版本：** 2020-12-07 v2；RA-L 2021。

**分类与用途：** 无人机 / 领域基线。因你的系统基础而保留；从 Auto Research 前沿清单中分离。

**原文短句：**

> only extract necessary obstacle information

**短句翻译：** 只提取必要的障碍信息。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** EGO-Planner avoids maintaining a full signed distance field for local trajectory optimization. It uses obstacle information relevant to the current trajectory, providing an efficient planning component rather than a complete autonomous exploration system.

**中文对照：** EGO-Planner 避免为局部轨迹优化维护完整的有符号距离场，而使用与当前轨迹相关的障碍信息。它提供的是高效规划组件，而非完整自主探索系统。

**方法总结：** 利用碰撞轨迹与无碰撞引导路径构造碰撞代价，并调整时间分配与轨迹。

**验证证据：** 论文包含基准和实机实验；仅说明当时设置下的方法表现。

**局限与时效性判断：** 局部规划与全局探索、语义导航是不同任务；旧方法也不应自动认定为现今最强基线。

**对本项目的建议：** 在研究高层决策时固定它，减少同时修改多层系统引入的混杂。

### 16. FUEL

**英文题名：** FUEL: Fast UAV Exploration Using Incremental Frontier Structure and Hierarchical Planning

**中文题名：** FUEL：利用增量前沿结构和分层规划实现快速无人机探索

**来源：** [原始页面](https://github.com/HKUST-Aerial-Robotics/FUEL)

**首发记录：** 2021（正式版年份）。**本次采用/核对版本：** RA-L 2021；仓库提供后续多机工作链接。

**分类与用途：** 无人机 / 领域基线。保留几何探索参照；不作为科研 Agent 方法论文。

**原文短句：**

> maintains crucial information for exploration planning incrementally

**短句翻译：** 以增量方式维护探索规划所需的关键信息。

**引文位置：** 作者项目页或 README 正文。

**英文释义（自行撰写，非原文摘要）：** FUEL maintains frontier information and plans exploration at several levels, from coverage routes to viewpoints and trajectories. It supplies a concrete exploration architecture against which research-generated changes can be tested.

**中文对照：** FUEL 维护前沿信息，并从覆盖路径、视点到轨迹多个层级规划探索。它为检验科研系统生成的改动提供了具体的探索架构。

**方法总结：** 增量 Frontier Information Structure 与分层路径、视点、轨迹规划。

**验证证据：** 作者仓库对应 RA-L 2021 论文，并报告当时的比较结果；本次未测当前环境。

**局限与时效性判断：** 历史倍数提升不适用于新平台；必须统一传感器、地图和运动条件。

**对本项目的建议：** 用于组织探索决策任务及对照，但修改模块边界要与已有系统对齐。

### 17. FlightBench

**英文题名：** FlightBench: Benchmarking Learning-based Methods for Ego-vision-based Quadrotors Navigation

**中文题名：** FlightBench：第一视角四旋翼导航中学习式方法的基准评测

**来源：** [原始页面](https://arxiv.org/abs/2406.05687v3)

**首发记录：** 2024-06-09。**本次采用/核对版本：** 2025-05-19 v3；页面关联 RA-L 2025 DOI。

**分类与用途：** 无人机 / 领域基线。补齐最新版本与正式发表关联；保留场景难度和公平比较思路。

**原文短句：**

> sharp corners or view occlusion

**短句翻译：** 急转角或视野遮挡。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** FlightBench compares learned and optimization-based navigation methods across scenarios with different difficulty factors. Its value for this project is the evaluation design: overall averages alone can hide systematic failures in particular geometries.

**中文对照：** FlightBench 在具有不同难度因素的场景中比较学习式与优化式导航方法。对本项目的价值在于评价设计：总体平均值可能掩盖特定几何条件下的系统性失败。

**方法总结：** 定义场景难度因素，结合多指标、仿真以及全文版本中报告的硬件验证进行比较。

**验证证据：** v3 报告学习式方法在速度与推理上有优势，但在急转弯和遮挡条件下仍有困难。

**局限与时效性判断：** 这些是被测方法的结论，不是所有学习式导航的永久结论；不直接评价语言任务。

**对本项目的建议：** 把场景族与难度作为实验选择变量，报告分组失败而不只报总体分数。

### 18. OpenUAV / UAV-Need-Help

**英文题名：** Towards Realistic UAV Vision-Language Navigation: Platform, Benchmark, and Methodology

**中文题名：** 迈向真实的无人机视觉语言导航：平台、基准与方法

**来源：** [原始页面](https://proceedings.iclr.cc/paper_files/paper/2025/hash/15ce8e7afe5ee95bad56e3b9be28d3d1-Abstract-Conference.html)

**首发记录：** 2025（本次核对正式版）。**本次采用/核对版本：** ICLR 2025 正式版。

**分类与用途：** 无人机 / 领域基线。保留 UAV 语义导航任务入口；平台版本与新方法需另行核对。

**原文短句：**

> provides varying levels of guidance information

**短句翻译：** 提供不同程度的引导信息。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** This work adapts vision-language navigation to aerial movement and realistic control through a platform, task data, and navigation method. Its assistance-based search task is different from both geometric coverage and simple local collision avoidance.

**中文对照：** 这项工作通过平台、任务数据和导航方法，使视觉语言导航更贴近空中运动与真实控制。其带辅助信息的搜索任务不同于几何覆盖，也不同于简单的局部避障。

**方法总结：** OpenUAV 平台、目标导向数据、UAV-Need-Help 搜索任务与多模态分层轨迹生成。

**验证证据：** 正式版介绍约 12k 轨迹数据；报告方法相对当时基线的收益及与人类表现的差距。

**局限与时效性判断：** 不同指导信息会改变任务难度；不能跨设置直接比较成功率。

**对本项目的建议：** 在几何探索闭环稳定后引入，固定辅助信息、传感器与动作接口。

### 19. VLN on the Fly

**英文题名：** VLN on the Fly: An Onboard Vision-Language Navigation Stack for Aerial Robots

**中文题名：** VLN on the Fly：面向空中机器人的机载视觉语言导航系统

**来源：** [原始页面](https://vln-on-the-fly.github.io/)

**首发记录：** 2026。**本次采用/核对版本：** 作者项目页标注 IMAV 2026。

**分类与用途：** 无人机 / 近期候选。因 Orin NX 与 EGO 组合而优先检查；新近不代表覆盖了所有任务。

**原文短句：**

> using an external motion-capture system

**短句翻译：** 使用外部动作捕捉系统。

**引文位置：** 作者项目页或 README 正文。

**英文释义（自行撰写，非原文摘要）：** The system combines onboard visual-language object grounding with depth-based goal estimation and local planning. It is directly relevant to an Orin NX platform, but its motion-capture experiments establish a narrower capability than general outdoor autonomy.

**中文对照：** 该系统结合机载视觉语言目标定位、基于深度的目标位置估计和局部规划，与 Orin NX 平台直接相关。但其动捕实验支持的能力范围比一般室外自主飞行更窄。

**方法总结：** 视觉语言模块选择图像区域，深度生成三维目标，EGO-Planner 规划，控制策略执行。

**验证证据：** 作者页面报告室内有/无障碍飞行，视觉语言与规划运行于 Orin NX，定位使用外部动捕。

**局限与时效性判断：** 当前视野与深度范围有限；不能把它视作完整未知环境长程搜索解法。

**对本项目的建议：** 借鉴模块接口与目标核验，将定位来源和机载/站端计算分别列入对照条件。

### 20. LightVLN

**英文题名：** LightVLN: Efficient Aerial Vision-and-Language Navigation with Compact Memory and History-Guided Local Aggregation

**中文题名：** LightVLN：利用紧凑记忆与历史引导局部聚合实现高效空中视觉语言导航

**来源：** [原始页面](https://arxiv.org/abs/2610.05024)

**首发记录：** 2026-10-04。**本次采用/核对版本：** 2026-10-04 v1 预印本。

**分类与用途：** 无人机 / 近期候选。保留端侧效率参考；正式实验前检查代码和可重现性。

**原文短句：**

> real-to-sim hardware-in-the-loop (HIL) evaluation

**短句翻译：** 从真实硬件接入仿真的硬件在环（HIL）评价。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** LightVLN reduces observation tokens and stores compact visual history to lower navigation computation. Its deployment evidence concerns onboard-compute hardware-in-the-loop evaluation, which should be distinguished from unrestricted physical flight experiments.

**中文对照：** LightVLN 通过减少观测 token 和保存紧凑视觉历史降低导航计算。其部署证据属于机载计算的硬件在环评价，应与真实自由飞行实验区分。

**方法总结：** 小型语言骨干、单 token 历史帧表示，以及由历史和指令条件化的局部聚合。

**验证证据：** 作者报告 OpenFly、AerialVLN-S 数据集结果以及 Orin NX 16GB 的 HIL 性能。

**局限与时效性判断：** 数据集与 HIL 结果不能证明你现有飞行系统上的闭环收益。

**对本项目的建议：** 比较端到端时延、内存与任务表现；不只比较模型推理频率。

### 21. SurGE

**英文题名：** SurGE: A Benchmark and Evaluation Framework for Scientific Survey Generation

**中文题名：** SurGE：科学综述生成的基准与评价框架

**来源：** [原始页面](https://arxiv.org/abs/2508.15658v5)

**首发记录：** 2025-08-21。**本次采用/核对版本：** 2026-05-02 v5。

**分类与用途：** 文献综合 / 核心更新。新增；作为检索与生成联合评价的主要参考之一。

**原文短句：**

> comprehensiveness, citation accuracy, structural organization, and content quality

**短句翻译：** 全面性、引用准确性、结构组织和内容质量。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** SurGE evaluates survey generation as both literature retrieval and synthesis. Topic descriptions, expert surveys, reference sets, and a large paper corpus provide a more explicit task setup than evaluating generated text in isolation.

**中文对照：** SurGE 同时评价综述生成中的文献检索与综合。主题说明、专家综述、参考文献集合和大型论文库，使任务设置比单独评价生成文本更加明确。

**方法总结：** 将主题、人工综述及引用集作为测试实例，配合百万级论文库和四维评价。

**验证证据：** v5 日期已核对；作者比较多种方法并报告仍存在明显能力差距。

**局限与时效性判断：** 参考综述不是唯一正确答案；引用覆盖需要结合相关性和新增文献考虑。

**对本项目的建议：** 将无人机综述的检索覆盖与生成质量分别测量，再观察误差如何传播。

### 22. SurveyLens

**英文题名：** SurveyLens: A Discipline-Aware Benchmark for Automatic Survey Generation

**中文题名：** SurveyLens：面向学科差异的自动综述生成基准

**来源：** [原始页面](https://aclanthology.org/2026.emnlp-main.2616/)

**首发记录：** 2026-02（预印本）。**本次采用/核对版本：** EMNLP 2026 正式版（2026-10）。

**分类与用途：** 文献综合 / 核心更新。新增；优先于仅用通用写作评分的评价方案。

**原文短句：**

> reference coverage and relevance remain a shared bottleneck

**短句翻译：** 参考文献覆盖与相关性仍是共同瓶颈。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** SurveyLens evaluates whether survey systems meet the standards of different research disciplines. It combines discipline-sensitive criteria with comparison to human surveys, showing that strong performance in one style of survey need not generalize everywhere.

**中文对照：** SurveyLens 评价综述系统是否满足不同研究学科的标准。它结合学科相关标准与人工综述对照，说明在某种综述风格上表现好未必能泛化到所有领域。

**方法总结：** 1,000 篇人工综述、10 个学科；学科评价标准与参考对齐构成双重评价。

**验证证据：** 正式版比较 11 个系统，发现不同范式各有所长，文献覆盖与相关性仍有不足。

**局限与时效性判断：** 学科权重仍需人工校准；跨学科结果不能直接给出 UAV 专题的最佳系统。

**对本项目的建议：** 为机器人综述增加运动假设、传感器、算力和实验证据等领域评价维度。

### 23. Bloom-Eval

**英文题名：** Bloom-Eval: A Hierarchical Evaluation Benchmark for Automatic Survey Generation Based on Bloom's Taxonomy

**中文题名：** Bloom-Eval：基于布鲁姆分类学的自动综述生成分层评价基准

**来源：** [原始页面](https://aclanthology.org/2026.acl-long.1315/)

**首发记录：** 2026（本次核对正式版）。**本次采用/核对版本：** ACL 2026 正式版（2026-07）。

**分类与用途：** 文献综合 / 核心更新。新增；用于区分格式组织与知识综合能力。

**原文短句：**

> proficient format organizers

**短句翻译：** 熟练的格式组织者。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** Bloom-Eval evaluates survey quality through multiple cognitive levels rather than presentation alone. It favors deterministic checks where possible and reserves model-based assessment for harder qualities, encouraging clearer separation between organization and understanding.

**中文对照：** Bloom-Eval 从多个认知层级评价综述质量，而不只关注呈现。它尽可能采用确定性检查，对更难的能力再使用模型评价，以更清晰地区分组织形式与理解能力。

**方法总结：** 采用六层评价，结合确定性算法与 GRADE 方法，面向跨学科材料。

**验证证据：** 论文构建三千余篇论文的数据集；作者认为被测系统的知识整合能力落后于格式组织能力。

**局限与时效性判断：** 这不是所有系统都缺乏理解的普遍证明；复杂维度仍要检查与专家的一致性。

**对本项目的建议：** 让综述评分关注比较、条件解释、矛盾与研究缺口，不奖励篇幅本身。

### 24. SurveyGraph

**英文题名：** SurveyGraph: Generating Academic Surveys via Methods-Entity Knowledge Graphs

**中文题名：** SurveyGraph：通过方法实体知识图谱生成学术综述

**来源：** [原始页面](https://arxiv.org/abs/2610.31317)

**首发记录：** 2026-10-22。**本次采用/核对版本：** arXiv v1；作者页面标注 EMNLP 2026 Findings 接收。

**分类与用途：** 文献综合 / 近期候选。新增；结构化证据选题的重要最近邻，须核查图关系质量。

**原文短句：**

> follow-on, competition, and shared-resource relations

**短句翻译：** 后续发展、竞争与共享资源关系。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** SurveyGraph organizes papers around relationships between methods and uses that structure during retrieval and writing. It is relevant to evidence-based survey design, but the graph's own relations must also be checked rather than assumed correct.

**中文对照：** SurveyGraph 围绕方法之间的关系组织论文，并在检索和写作时利用这些结构。它与证据驱动综述设计相关，但图中关系本身也需要核查，不能默认正确。

**方法总结：** 方法实体图支持核心论文发现、检索、混合大纲和带证据检查的综合。

**验证证据：** 作者报告同预算检索、关系标注和生成句子审核；明确部分跨系统比较并非相同后端的端到端对照。

**局限与时效性判断：** 图结构不自动等于事实；部分支持和充分支持应分别统计。

**对本项目的建议：** 比较“适用条件关系”是否比普通方法关系带来额外价值，而非仅提出用图谱。

### 25. EvoScientist

**英文题名：** EvoScientist: Towards Multi-Agent Evolving AI Scientists for End-to-End Scientific Discovery

**中文题名：** EvoScientist：迈向用于端到端科学发现的多智能体演化 AI 科学家

**来源：** [原始页面](https://arxiv.org/abs/2603.08127v2)；[补充原始来源](https://github.com/EvoScientist/EvoScientist)

**首发记录：** 2026-03-09。**本次采用/核对版本：** 2026-10-05 v2 预印本。

**分类与用途：** 科研闭环 / 核心更新。新增；作为持续记忆与研究闭环的近期实现候选。

**原文短句：**

> persistent memory and self-evolution

**短句翻译：** 持久记忆与自我演化。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** EvoScientist separates idea generation, implementation, and experience management. It stores lessons from successful and failed attempts so later research can reuse strategies, offering a direct comparison point for systems that learn across experiments.

**中文对照：** EvoScientist 将想法生成、实现和经验管理分开。它保存成功与失败尝试中的经验，使后续研究能复用策略，因此可作为跨实验学习系统的直接比较对象。

**方法总结：** 研究者、工程师、演化管理者三类 Agent；分别保存想法记忆与实验记忆。

**验证证据：** v2 报告想法评价和代码执行方面的提升；官方仓库已核对，尚未安装或复现。

**局限与时效性判断：** 更高执行成功率不等于有效发现更多；记忆也可能传播错误或跨任务泄漏。

**对本项目的建议：** 用留出研究任务检验经验迁移，并消融失败记忆和成功记忆的作用。

### 26. Into the Unknown

**英文题名：** Into the Unknown: Benchmarking AI agents on open scientific research problems

**中文题名：** Into the Unknown：在开放科学研究问题上评测 AI 智能体

**来源：** [原始页面](https://arxiv.org/abs/2610.19159)

**首发记录：** 2026-10-13。**本次采用/核对版本：** 2026-10-13 v1；在审预印本。

**分类与用途：** 评测 / 近期候选。新增；与你的“已有成果后续研究”需求最直接相关。

**原文短句：**

> None of the 135 submissions satisfies all the conditions

**短句翻译：** 135 份提交中没有一份满足全部条件。

**引文位置：** 原始来源摘要。

**英文释义（自行撰写，非原文摘要）：** The benchmark gives agents an existing paper and an unpublished follow-up direction. Domain scientists define necessary conditions without supplying a reference solution, allowing evaluation of open research and consistency between claims and recorded work.

**中文对照：** 该基准向 Agent 提供已有论文和未发表的后续方向。领域科学家定义必要条件而不提供参考解，从而评价开放研究，以及主张与实际记录工作的一致性。

**方法总结：** 由领域研究者提供后续问题和必要条件，评价研究产物并检查证据完整性。

**验证证据：** 作者在 15 个方向、9 个 Agent 的 135 份提交中报告无完整通过，114 份未通过其诚信检查。

**局限与时效性判断：** 只适用于这批任务、配置和标准；不能据此外推所有 AI 科研都失败。

**对本项目的建议：** 把你的已有导航成果转成开放后续研究任务，先写必要条件和证据核验规则。
