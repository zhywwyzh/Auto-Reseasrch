# EPOCH：通过证据约束的搜索实现可靠发现

EPOCH: Reliable Discovery through Evidence-Governed Search

Guo, Binjie; Mo, Aisheng; Li, Ruitong; Deng, Xinle

> 非官方机器初译，正文尚未逐段精校。图表保留原文内容，图内英文未另行翻译；有 HTML 原文的公式按原式排版。PDF 提取版保留对应原页，点击缩略图放大核对图表与公式。

原文版本：2610.06986v1 · [原始来源](https://arxiv.org/abs/2610.06986v1) · [中文 PDF](../../../output/pdf/epoch-zh-reading.pdf)

<details>
<summary>作者、机构和出版信息</summary>

Binjie Guo

Affiliation:

Zhejiang University

Aisheng Mo

Affiliation:

Zhejiang University

Ruitong Li

Affiliation:

The University of Hong Kong

Xinle Deng

Affiliation:

Zhejiang University

</details>

## 摘要


<details>
<summary>英文原文</summary>

Abstract

</details>

AI 科研智能体正越来越多地用于搜索程序、数学构造和证明。然而，现有系统通常只优化评价器反馈，却没有充分约束这些反馈应如何被解释、质疑和复用。因此，有希望但脆弱的候选可能被提升为“发现”，基准改进、有限范围的证书与定理级主张也容易混为一谈。我们提出 EPOCH，一种旨在弥补这一缺口的证据约束架构。EPOCH 将明确的任务契约、类型化记忆、主动反证、准入检查和独立重跑结合为发现循环，使每个候选都依据其所支持主张的证据强度和适用范围接受评价。EPOCH 在 AlgoTune 上取得当时最优的综合表现，平均归一化得分显著高于最强基线（0.65 对 0.53），并在内部 Math14 套件上获得最高平均得分（0.57）。在正式测试重跑中，它还表现出良好的留出集行为，并在 AgentHPO 的描述性综合指标上领先。在十个发现问题中，EPOCH 带来了显著的任务特定进展，包括更好的可执行构造、优化算法、反例以及有证明支持的结果。这些进展表明，系统能够将搜索转化为数学与计算领域的具体进步。综合而言，结果提示：要让 AI 科研智能体不仅产生更强的解，还产生更可信的科学发现，证据治理是必要的一步。


<details>
<summary>英文原文</summary>

AI research agents are increasingly used to search over programs, mathematical constructions, and proofs. However, existing systems typically optimize evaluator feedback without adequately governing how that feedback is interpreted, challenged, and reused. As a result, promising but fragile candidates can be promoted as discoveries, while benchmark improvements, finite certificates, and theorem-level claims are too easily conflated. We introduce EPOCH, an evidence-governed architecture designed to close this gap. EPOCH implements an evidence-governed discovery loop by combining explicit task contracts, typed memory, active falsification, admission checks, and independent replay, so that each candidate is evaluated against the strength and scope of the claim it supports. EPOCH achieves state-of-the-art aggregate performance on AlgoTune, substantially exceeding the strongest baseline in mean normalized score (0.65 vs. 0.53), and attains the highest mean score on the internal Math14 suite (0.57). It further shows favorable held-out behavior under official-test replay and leads the descriptive aggregate on AgentHPO. Across ten discovery problems, EPOCH delivers substantial task-specific advances, including improved executable constructions, optimized algorithms, counterexamples, and proof-supported results. These advances demonstrate its ability to convert search into concrete progress across mathematical and computational domains. Together, the results suggest that evidence governance is a necessary step toward AI research agents that produce not only stronger solutions, but also more trustworthy scientific discoveries.

</details>

## 1 引言


<details>
<summary>英文原文</summary>

1 Introduction

</details>

AI研究智能体正在被越来越多地开发用于解决明确指定的任务，同时还能在代码、算法、数学和科学领域生成潜在的发现成果。近期系统已在游戏、程序合成、张量分解、几何构造、形式证明及科学筛选等领域展现了这一潜力（Silver等，2018；Schrittwieser等，2020；Li等，2022；Fawzi等，2022；Trinh等，2024；Hubert等，2025；Merchant等，2023）。FunSearch和AlphaEvolve进一步表明，由评估器引导的进化过程能够将大语言模型转化为有效的开放式搜索引擎（Romera-Paredes等，2024）；
Novikov等人，2025年）。尽管取得了这些进展，当前系统主要被设计用于生成和优化候选方案，而非构建支持发现所需的证据。一个有前景的程序、结构或猜想仅是一个起点：确认其价值可能需要识别某种机制、提出与竞争解释相对的反例、验证有限的证明，或区分实验支持的观察结果与基于证明的断言。这些支撑对象往往只是随机生成、测试和记录的。
因此，智能体可能会返回一个改进的候选方案，却未能明确说明其为何有效、有哪些证据支持它，以及这些证据如何可以再次被独立验证。因此，核心挑战在于将搜索与一种明确的流程相结合，以构建、验证和保留相关证据，从而将有潜力的候选方案转化为得到证实的发现。


<details>
<summary>英文原文</summary>

AI research agents are increasingly being developed not only to solve well-specified tasks, but also to generate candidate discoveries in code, algorithms, mathematics, and science. Recent systems have demonstrated this potential across games, program synthesis, tensor decompositions, geometric constructions, formal proofs, and scientific screening ( Silver et al., 2018 ; Schrittwieser et al., 2020 ; Li et al., 2022 ; Fawzi et al., 2022 ; Trinh et al., 2024 ; Hubert et al., 2025 ; Merchant et al., 2023 ) . FunSearch and AlphaEvolve further show that evaluator-guided evolution can transform large language models into effective engines for open-ended search ( Romera-Paredes et al., 2024 ; Novikov et al., 2025 ) . Despite this progress, current systems are primarily designed to generate and optimize candidates, rather than to construct the evidence needed to support a discovery. A promising program, construction, or conjecture is only a starting point: establishing its value may require identifying a mechanism, producing a counterexample to a competing explanation, checking a finite certificate, or distinguishing an experimentally supported observation from a proof-backed claim. These supporting objects are often generated, tested, and recorded only opportunistically. As a result, an agent may return an improved candidate without a clear account of why it works, what evidence supports it, or how that evidence can be independently revisited. The central challenge is therefore to couple search with an explicit process for constructing, challenging, and retaining the evidence that turns promising candidates into supported discoveries.

</details>

现有的智能体将生成与执行、测试或验证相结合，但并未为不同领域中的证据构建过程提供统一的规范。我们提出这样一个问题：当不同任务所需的支持性证据存在差异时，应如何制定规范以将候选者推进到保留的探索阶段？对于代码而言，这可能涉及语义检查、资源测量以及回放测试；对于代数问题，则涉及精确恒等式、构造方法或阻碍性证据；而对于定理探索，则需要具有不同范围的计算证据和形式证明。
标量奖励可以引导搜索过程找到更优质的候选方案，但仅凭它无法组织辅助证据的生成、明确主张的范围，也无法保留可能解释或质疑该主张的失败尝试。


<details>
<summary>英文原文</summary>

Existing agents combine generation with execution, testing, or verification, but they do not provide a common protocol for this evidence-construction process across domains. We ask: what protocol should govern the promotion of a candidate into a retained discovery when the required supporting evidence differs across tasks? For code, this may involve semantic checks, resource measurements, and held-out replay; for algebra, exact identities, constructions, or obstruction witnesses; and for theorem discovery, computational evidence and formal proof with distinct scopes. A scalar reward can guide a search procedure toward better candidates, but it cannot by itself organize the generation of supporting evidence, specify the scope of a claim, or preserve the failed attempts that may explain or challenge it.

</details>

我们提出了 EPOCH 模型（即基于证据约束的提案优化机制，图 1），这是一种以证据为约束的架构，将发现过程视为对明确证据库进行的受限搜索。每个任务都始于一份契约，其中规定了允许的编辑方式、适用的检查规则、资源限制以及可接受的声明范围。类型化记忆库会保存所有成功与失败的尝试结果，使得后续搜索能够复用相关证据并避免已知的失败模式。候选方案会针对其宣称的机制进行主动验证；只有其支持性证据符合任务契约时才会被接受，并且在搜索终点被冻结后，这些候选方案会再次独立进行重新评估。
与其让验证者完成验证或将有限证据提升为一般定理，EPOCH提供了一种领域通用协议，该协议将每个保留结果与其支持证据进行关联，并明确该支持的边界。


<details>
<summary>英文原文</summary>

We propose EPOCH (Evidence-conditioned Proposal Optimization through Cumulative Hypothesis-governance, Fig. 1 ), an evidence-governed architecture that frames discovery as constrained search over an explicit evidence ledger. Each task begins with a contract specifying permissible edits, applicable checks, resource limits, and the scope of admissible claims. Typed memory retains both successful and failed trials, allowing later search to reuse supporting evidence and avoid known failure modes. Candidates are actively challenged against their declared mechanisms, admitted only when their support satisfies the task contract, and independently replayed after the search endpoint is frozen. Rather than making a verifier complete or elevating finite evidence into a general theorem, EPOCH provides a domain-general protocol that aligns each retained result with its supporting evidence and makes the limits of that support explicit.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0020)

图1：EPOCH将发现搜索与明确的证据记录系统相结合。成功的实验与失败的实验都会被存入文字记忆中；失败的案例会被反馈回搜索环节以进行修正和改进（红色循环）。挑战、接受结果以及独立重试决定了候选方案是否被保留，而任务合同则规定了制约该决策的检查标准、预算和范围要求。


<details>
<summary>英文原文</summary>

Figure 1: EPOCH couples discovery search to an explicit evidence ledger. Successful and failed trials enter typed memory; failures are fed back into search for repair and refinement (red loop). Challenge, admission, and independent replay determine whether a candidate is retained, while the task contract fixes the checks, budget, and claim scope governing that decision.

</details>

我们的贡献包括：


<details>
<summary>英文原文</summary>

Our contributions are:

</details>

•


<details>
<summary>英文原文</summary>

•

</details>

基于证据的发现机制。我们提出了一种领域通用架构，在该架构中，任务约束、类型化记忆、主动证伪、声明感知接纳以及独立重放共同决定了候选解决方案如何被保留为最终结果。


<details>
<summary>英文原文</summary>

Evidence-governed discovery. We introduce a domain-general architecture in which task contracts, typed memory, active falsification, claim-aware admission, and independent replay jointly govern how candidate solutions become retained results.

</details>

•


<details>
<summary>英文原文</summary>

•

</details>

强大的探索与利用性能。EPOCH在AlgoTune上实现了最先进的综合性能，在内部Math14测试中获得了最高的平均得分，具有理想的官方测试重放表现，并在AgentHPO上处于最领先的描述性综合排名。


<details>
<summary>英文原文</summary>

Strong exploration and exploitation performance. EPOCH achieves state-of-the-art aggregate performance on AlgoTune, the highest mean score on internal Math14, favourable official-test replay behaviour, and the leading descriptive aggregate on AgentHPO.

</details>

•


<details>
<summary>英文原文</summary>

•

</details>

具有明确证据的主要发现。在十个发现问题中，EPOCH 提出了11个改进的张量边界秩上界，包括针对 $T_{\rm ss444}$ 的明确30路径构造；可复用的统一Big-centroid构造；用于23个数据中位数选择的创纪录54次比较可执行程序；用于AES的1,512门（$14.10\%$）匹配-PyZX T计数减少算法；带有完全相等分类的Lean-checked全维度超立方体行列式不等式；以及针对所提出的$H_{\beta}$系数排序的9元素反例的Lean-checked证明，并扩展至无限族。


<details>
<summary>英文原文</summary>

Major discoveries with scoped evidence. Across ten discovery problems, EPOCH delivers eleven improved tensor border-rank upper bounds, including an explicit 30-path construction for $T_{\rm ss444}$ ; a reusable uniform Big-centroid construction; a record-setting 54-comparison executable procedure for median-of-23 selection; a 1,512-gate ( $14.10\%$ ) matched-PyZX T-count reduction for AES; a Lean-checked all-dimensional hypercube determinant inequality with complete equality classification; and a Lean-checked nine-element counterexample to the proposed $H_{\beta}$ coefficient ordering, extended to an infinite family.

</details>

## 2 相关研究


<details>
<summary>英文原文</summary>

2 Related Work

</details>

### 评估器引导的搜索与发现。


<details>
<summary>英文原文</summary>

Evaluator-Guided Search and Discovery.

</details>

AlphaCode能够大规模生成程序，并根据这些程序在生成的测试输入上的表现进行筛选、聚类和重新排序；而AlphaTensor则将矩阵乘法算法的发现过程转化为对矩阵乘法张量的低秩分解的搜索（Li等人，2022；Fawzi等人，2022；Google DeepMind，2022）。FunSearch将语言模型提议与进化选择相结合，而AlphaEvolve则将评估器引导的进化方法扩展到数学和计算任务上（Romera-Paredes等人，2024；Novikov等人，2025）。
OpenEvolve、AdaEvolve和AI-Scientist进一步拓展了进化与端到端研究工作流的应用场景（OpenEvolve贡献者，2026；Cemri等，2026；Lu等，2024；Yamada等，2025）。这些系统证明了由评估器引导的搜索方式的有效性；EPOCH则通过引入证据契约来补充这些系统，该契约规定了哪些候选结果可以作为发现成果保留，其主张需要何种支持，以及被拒绝的路径如何仍可用于后续搜索。


<details>
<summary>英文原文</summary>

AlphaCode generates programs at scale and filters, clusters, and reranks them according to their behavior on generated test inputs, whereas AlphaTensor formulates matrix-multiplication algorithm discovery as a search for low-rank decompositions of the matrix-multiplication tensor ( Li et al., 2022 ; Fawzi et al., 2022 ; Google DeepMind, 2022 ) . FunSearch couples language-model proposals to evolutionary selection, and AlphaEvolve extends evaluator-guided evolution to mathematical and computational tasks ( Romera-Paredes et al., 2024 ; Novikov et al., 2025 ) . OpenEvolve, AdaEvolve, and AI-Scientist further broaden the landscape of evolutionary and end-to-end research workflows ( OpenEvolve contributors, 2026 ; Cemri et al., 2026 ; Lu et al., 2024 ; Yamada et al., 2025 ) . These systems establish the effectiveness of evaluator-guided search; EPOCH complements them by introducing an evidence contract that governs which candidates may be retained as discoveries, what support their claims require, and how rejected paths remain available for subsequent search.

</details>

### 特定领域的发现证据。


<details>
<summary>英文原文</summary>

Domain-Specific Evidence for Discovery.

</details>

AlphaGeometry将学习到的构建方法与符号推导相结合，AlphaProof会搜索可形式验证的Lean状态，而GNOME则将学习到的筛选机制与基本原理计算相耦合（Trinh等，2024；Google DeepMind，2024；Hubert等，2025；Merchant等，2023；Google DeepMind，2023）。这些领域特定的验证工具是不可或缺的，而非可以互换的。最近的AI辅助数学研究同样将模型引导的探索与专家审查相结合，在适用情况下还采用形式验证，同时能够区分提示性证据与已确立的数学命题（Anthropic，2026；OpenAI，2026）。
因此，EPOCH并不试图用统一的真理得分来替代专业验证；而是将领域特定的输出如何支持发现过程标准化。输入凭证将保留的结果与产生其证据的检查项绑定；三值门将候选对象分为被支持、被反驳和未解决三类；独立的重放测试则对搜索循环之外的固定样本进行验证。最终得到的是一个可重放的承认记录，其中明确说明了进行了哪些检查、获得了什么结果，以及现有证据允许提出何种主张。


<details>
<summary>英文原文</summary>

AlphaGeometry combines learned construction with symbolic deduction, AlphaProof searches formally checkable Lean states, and GNoME couples learned screening to first-principles calculations ( Trinh et al., 2024 ; Google DeepMind, 2024 ; Hubert et al., 2025 ; Merchant et al., 2023 ; Google DeepMind, 2023 ) . Their domain-specific validators are essential rather than interchangeable. Recent AI-assisted mathematical studies likewise combine model-guided exploration with expert scrutiny and, where applicable, formal verification, while distinguishing suggestive evidence from established mathematical claims ( Anthropic, 2026 ; OpenAI, 2026 ) . EPOCH therefore does not seek to replace specialist validation with a universal truth score; instead, it standardizes how domain-specific outputs support discovery. Typed receipts bind a retained result to the checks that produced its evidence, three-valued gates distinguish supported, refuted, and unresolved candidates, and independent replay tests frozen artifacts outside the search loop. The result is a replayable admission record that specifies what was checked, what outcome was obtained, and which claim the available evidence permits.

</details>

## 3 基于证据的发现


<details>
<summary>英文原文</summary>

3 Evidence-Governed Discovery

</details>

我们围绕三个决策来安排该协议：什么属于可接受的终点，证据如何影响后续的提案，以及通过独立重放可以得出什么结论。


<details>
<summary>英文原文</summary>

We organize the protocol around three decisions: what counts as an admissible endpoint, how evidence changes subsequent proposals, and what may be claimed after independent replay.

</details>

### 3.1 任务合同与可接受的终点


<details>
<summary>英文原文</summary>

3.1 Task contract and admissible endpoints

</details>

任务合同为：公共与终端数据视图、评估指标、资源预算、可编辑成果空间以及允许的声明范围。候选方案具有目标及证据包；而一项声明则明确说明了结果所断言的内容。终点选择工作正在进行中


<details>
<summary>英文原文</summary>

A task contract is $\mathcal{C}=(D_{\rm pub},D_{\rm term},E,B,A,S)$ : public and terminal data views, evaluators, resource budget, editable artifact space, and allowed claim scope. A candidate $c$ has objective $q_{\mathcal{C}}(c)$ and evidence bundle $\xi$ ; a claim $\sigma$ states what the result asserts. Endpoint selection is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0037)

**表格与文字对照**

```text
| $\begin{gathered}(c^{*},\xi^{*},\sigma^{*})\in\arg\max_{c,\xi,\sigma}\ q_{\mathcal{C}}(c)\\
\begin{aligned} \text{s.t.}\quad&c\in A,\quad u_{j}(c,\xi)\leq B_{j},\\
&\operatorname{Correct}_{E}(c;\xi)=1,\quad\operatorname{Challenge}(c;\xi)=1,\\
&\operatorname{Replay}_{E}(c;\xi)=1,\quad\operatorname{Supports}(\xi,\sigma)=1,\quad\operatorname{Scope}(\sigma)\subseteq S.\end{aligned}\end{gathered}$ | | (1)

表内文字对照（数值与原始行列保持不变）：
begin → 开始
gathered → 收集了
sigma → sigma
arg → arg
max_ → max_
mathcal → mathcal
aligned → 对齐
text → 文本
quad → quad
in A → 在 A 中
quad u_ → quad u_
xi) → xi)
leq B_ → ≤ B_
operatorname → \operatorname
Correct → 正确
Challenge → 挑战
Replay → 重放
Supports → 支持
sigma) → sigma)
Scope → 范围
subseteq S → 子集 S
end → 结束
```


<details>
<summary>英文原文</summary>

| $\begin{gathered}(c^{*},\xi^{*},\sigma^{*})\in\arg\max_{c,\xi,\sigma}\ q_{\mathcal{C}}(c)\\
\begin{aligned} \text{s.t.}\quad&c\in A,\quad u_{j}(c,\xi)\leq B_{j},\\
&\operatorname{Correct}_{E}(c;\xi)=1,\quad\operatorname{Challenge}(c;\xi)=1,\\
&\operatorname{Replay}_{E}(c;\xi)=1,\quad\operatorname{Supports}(\xi,\sigma)=1,\quad\operatorname{Scope}(\sigma)\subseteq S.\end{aligned}\end{gathered}$ | | (1)

</details>

最大化过程仅针对在注册运行过程中生成的提案进行，包括提供的经过验证的备用方案。它并非所有程序或证明的全局最优解。Gates的取值属于 $\{1,0,\bot\}$ 范围，其中 $\bot$ 表示未解决的证据；只有 1 个被允许纳入。


<details>
<summary>英文原文</summary>

The maximization ranges only over proposals generated within the registered run, including a verified fallback when supplied. It is not a global optimum over all programs or proofs. Gates take values in $\{1,0,\bot\}$ , where $\bot$ denotes unresolved evidence; only 1 permits admission.

</details>

### 3.2 证据记忆、证伪与阶段控制


<details>
<summary>英文原文</summary>

3.2 Evidence memory, falsification, and phase control

</details>

在步骤 $t$ 中，状态为 $s_{t}=(c_{t}^{*},M_{t},z_{t},b_{t})$：现任者、仅可追加的内存、阶段以及剩余资源。提案策略会产生


<details>
<summary>英文原文</summary>

At step $t$ , the state is $s_{t}=(c_{t}^{*},M_{t},z_{t},b_{t})$ : incumbent, append-only memory, phase, and remaining resources. The proposal policy emits

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0041)

**表格与文字对照**

```text
| $a_{t}=(c_{t},H_{t},\widehat{\delta}_{t},R_{t},F_{t})\sim\pi_{\theta}(\cdot\mid\mathcal{C},\mathcal{V}(M_{t}),z_{t},b_{t}),$ | | (2)

表内文字对照（数值与原始行列保持不变）：
widehat → widehat
delta → delta
sim → 模拟
pi_ → pi_
theta → theta
cdot → ·at
mid → 中间
mathcal → mathcal
```


<details>
<summary>英文原文</summary>

| $a_{t}=(c_{t},H_{t},\widehat{\delta}_{t},R_{t},F_{t})\sim\pi_{\theta}(\cdot\mid\mathcal{C},\mathcal{V}(M_{t}),z_{t},b_{t}),$ | | (2)

</details>

包含候选方案、假设、预测结果、证据参考以及预期反驳因素。有限视角 $\mathcal{V}(M_{t})$ 能够展示相关的先前证据，而无需重新编写记录。每个观察结果都记录着相关物及评估者的哈希值、得分、正确性、资源使用情况、失败原因及拒绝理由。因此，科学上的失败可能会限制后续的提案，而基础设施事件则可以在不表现为对方法的反驳证据的情况下触发有限的恢复机制。


<details>
<summary>英文原文</summary>

containing a candidate, hypothesis, predicted effect, evidence references, and intended falsifier. The bounded view $\mathcal{V}(M_{t})$ exposes relevant prior evidence without rewriting the ledger. Each observation records artifact and evaluator hashes, score, correctness, resource use, failure attribution, and rejection reason. Scientific failure can therefore constrain a later proposal, whereas an infrastructure incident can trigger bounded recovery without masquerading as evidence against the method.

</details>

一项挑战针对所指定的机制，而非仅仅重复目标。例如语义边界输入、代数系数不匹配、共核证明、反例搜索或证明义务等。通过有限挑战仅能确保其宣称的覆盖性。控制器在探索、优化、恢复和最终确定之间选择；这并不意味着存在未报告的优化调度方案。如果 $\mathcal{A}_{t}$ 中包含适用门通过候选项，则保留的端点满足 $c_{t}^{*}\in\arg\max_{c\in\mathcal{A}_{t}}q_{\mathcal{C}}(c)$ 要求。
通过经过验证的回退机制，这实现了协议级安全不变性，而非超出评估器覆盖范围的正确性。


<details>
<summary>英文原文</summary>

A challenge targets the stated mechanism rather than merely repeating the objective. Examples include semantic boundary inputs, an algebraic coefficient mismatch, a cokernel witness, counterexample search, or a proof obligation. Passing a finite challenge supports only its declared coverage. The controller chooses among explore, refine, recover, and finalize; it does not imply an unreported learned optimal schedule. If $\mathcal{A}_{t}$ contains candidates whose applicable gates pass, the retained endpoint satisfies $c_{t}^{*}\in\arg\max_{c\in\mathcal{A}_{t}}q_{\mathcal{C}}(c)$ . With a verified fallback, this gives a protocol-level safety invariant, not correctness beyond evaluator coverage.

</details>

### 3.3 重放与声明密封


<details>
<summary>英文原文</summary>

3.3 Replay and claim sealing

</details>

终端回放仅对选定的端点进行评估，无法再用于重新选择。一个密封的结果会绑定合同、端点、账本、证据、索赔及范围。


<details>
<summary>英文原文</summary>

Terminal replay evaluates a frozen selected endpoint and cannot feed back into selection. A sealed result binds the contract, endpoint, ledger, evidence, claim, and scope:

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0046)

**表格与文字对照**

```text
| $\operatorname{Seal}=h(\mathcal{C},c^{*},M_{T},\xi^{*},\sigma^{*},S).$ | | (3)

表内文字对照（数值与原始行列保持不变）：
operatorname → \operatorname
Seal → 封条
mathcal → mathcal
sigma → sigma
```


<details>
<summary>英文原文</summary>

| $\operatorname{Seal}=h(\mathcal{C},c^{*},M_{T},\xi^{*},\sigma^{*},S).$ | | (3)

</details>

独立实现可以重构语义，而无需重新运行相同的检查器。对于数学输出，该包将有限计算、一般论证、形式核心和缺失桥梁区分开来。


<details>
<summary>英文原文</summary>

Independent implementations may reconstruct semantics rather than rerun the same checker. For mathematical outputs, the bundle distinguishes finite computation, general argument, formal kernel, and missing bridge.

</details>

## 4 评估


<details>
<summary>英文原文</summary>

4 Evaluation

</details>

我们首先比较各端点的质量及保留行为，然后分析组件移除情况以及不同任务中的性能分布。第5节的发现审计提出了一个独立问题：这一过程会产生哪些可复用对象和有限断言？


<details>
<summary>英文原文</summary>

We first compare endpoint quality and held-out behavior, then examine component removals and the distribution of performance across tasks. The discovery audit in Section 5 asks a separate question: what reusable objects and bounded claims emerge from this process?

</details>

### 4.1 基准测试与需求规格


<details>
<summary>英文原文</summary>

4.1 Benchmarks and Estimands

</details>

我们在三种互补的测试环境中对 EPOCH 进行了评估：用于约束性算法搜索的 AlgoTune，用于具有精确端点检查器的多样化数学任务的 Math14，以及六个用于组件消融的 AgentHPOBench 任务（AlgoTune 贡献者，2026；OpenMOSS，2026）。在固定为12个任务的 AlgoTune 子集中，五种方法获得相同的48次语义调用预算，并使用三个初始版本进行运行；我们报告了各任务的平均得分及其宏平均值。为了检验搜索时间上的优势是否能迁移到开发数据之外，我们冻结每个符合条件的最终程序，然后在32个之前未使用的官方测试输入上重新运行，无需进一步的搜索或调整。
此重放功能会重新执行正确性检查及新鲜处理计时。Math14 会对14项数学任务的性能进行评估，而 AgentHPO 则能明确 EPOCH 各组件的贡献程度。完整的任务级结果、种子数据、测量值及统计方法均载于补充材料中。


<details>
<summary>英文原文</summary>

We evaluate EPOCH in three complementary settings: AlgoTune for constrained algorithmic search, Math14 for diverse mathematical objectives with exact endpoint checkers, and six AgentHPOBench tasks for component ablations ( AlgoTune contributors, 2026 ; OpenMOSS, 2026 ) . On a frozen 12-task AlgoTune subset, five methods receive the same budget of 48 semantic calls and are run with three seeds; we report mean task scores and their macro-average. To test whether search-time gains transfer beyond development data, we freeze each eligible final program and replay it, without further search or adaptation, on 32 previously unused official test inputs. This replay reruns correctness checks and fresh-process timing. Math14 evaluates performance across 14 mathematical tasks, whereas AgentHPO isolates the contribution of EPOCH’s individual components. Full task-level results, seeds, measurements, and statistical procedures are provided in the Supplement.

</details>

### 4.2 搜索性能与留存鲁棒性


<details>
<summary>英文原文</summary>

4.2 Search Performance and Held-Out Robustness

</details>

EPOCH达到了最高的AlgoTune开发均值（表1），达到0.65，并比最强的基准模型AdaEvolve高出$22.60\%$ 。它还比AI-Scientist变体和OpenEvolve高出$24.80\%$到$30.90\%$的差距，从而在评估的方法中确立了最强的综合性能。这一优势在保留的官方测试重放中同样体现：在终点固定且无需进一步搜索或调整的情况下，EPOCH对所有四个基准模型都有正向的平均效果。最大公共子图保留了$+0.48$的归一化分数优势，而Convolve2D则具有$+0.24$的优势，不过NMF则变为$-0.27$。
最大的开发收益出现在 Convolve2D、最大公共子图、Robertson ODE、NMF 以及 zeta-zero 计数方面，这反映了在基准测试协议下针对评估可执行端点的任务特定改进。


<details>
<summary>英文原文</summary>

EPOCH achieves the highest AlgoTune development mean (Table 1 ), reaching 0.65 and surpassing the strongest baseline, AdaEvolve, by $22.60\%$ . It also exceeds both AI-Scientist variants and OpenEvolve by margins ranging from $24.80\%$ to $30.90\%$ , establishing the strongest aggregate performance among the evaluated methods. This advantage extends to the held-out official-test replay: after endpoints are frozen and evaluated without further search or adaptation, EPOCH has positive mean effects against all four baselines. Maximum common subgraph retains a $+0.48$ normalized-score advantage and Convolve2D a $+0.24$ advantage, although NMF reverses to $-0.27$ . The largest development gains occur on Convolve2D, maximum common subgraph, Robertson ODE, NMF, and zeta-zero count, reflecting task-specific improvements to the evaluated executable endpoints under the benchmark protocol.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0054)

表1：AlgoTune得分。开发阶段每种方法使用12项任务和3个种子数据；重放效应阶段使用7项官方测试任务。得分越高越好。相对收益是相对于指定方法的开发得分来衡量的。重放效应以标准化得分单位表示为EPOCH减去指定基线值；开发得分和重放效应列则使用不同的终点人群。


<details>
<summary>英文原文</summary>

Table 1: AlgoTune scores. Development uses 12 tasks and three seeds per method; replay effects use seven official-test tasks. Higher scores are better. Relative gain is measured against the named method’s development score. Replay effects are EPOCH minus the named baseline in normalized-score units; the development and replay columns use distinct endpoint populations.

</details>

在 Math14 测试集（表 2）中，EPOCH 获得了最高的平均得分 0.57，优于所有评估的基线模型。其相对改进幅度从 OpenEvolve 的 $0.60\%$ 到 AI-Scientist v1 的 $10.90\%$，表明 EPOCH 基于证据的搜索架构能够有效从可执行的优化任务迁移到多种数学目标。


<details>
<summary>英文原文</summary>

On Math14 (Table 2 ), EPOCH achieves the highest mean score of 0.57, outperforming every evaluated baseline. Its relative improvement ranges from $0.60\%$ over OpenEvolve to $10.90\%$ over AI-Scientist v1, demonstrating that EPOCH’s evidence-governed search architecture transfers effectively from executable optimization to diverse mathematical objectives.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0057)

表2：Math14在14个目标上的内部转移得分。得分越高越好；相对收益是相对于指定的基准值来衡量的。


<details>
<summary>英文原文</summary>

Table 2: Math14 internal transfer scores over 14 objectives. Higher scores are better; relative gains are measured against the named baseline.

</details>

### 4.3 组件贡献与任务级权衡


<details>
<summary>英文原文</summary>

4.3 Component contributions and task-level trade-offs

</details>

虽然主要评估基准是针对完整系统进行的，但六个 AgentHPOBench 任务使我们能够分离出 EPOCH 各主要组件的贡献。由于这些任务使用不同的指标，因此任务级别的原始得分仍是最主要的评估结果。为了进行描述性的跨任务比较，我们会在每个任务内部对任务级别的平均值进行归一化处理，以反映该任务指标是最大化还是最小化。


<details>
<summary>英文原文</summary>

Whereas the main benchmarks compare complete systems, six AgentHPOBench tasks allow us to isolate the contributions of EPOCH ’s major components. Because these tasks use heterogeneous metrics, task-level raw scores remain the primary results. For descriptive cross-task comparison, we normalize each task-level mean $z_{tv}$ within its task, accounting for whether the task metric is maximized or minimized:

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0061)

**表格与文字对照**

```text
| $N_{tv}=100\frac{z_{tv}-\min_{v^{\prime}}z_{tv^{\prime}}}{\max_{v^{\prime}}z_{tv^{\prime}}-\min_{v^{\prime}}z_{tv^{\prime}}},\qquad\bar{N}_{v}=\frac{1}{6}\sum_{t}N_{tv}.$ | | (4)

表内文字对照（数值与原始行列保持不变）：
frac → 分数
min_ → 最小值
prime → 主要
max_ → max_
qquad → qquad
bar → 酒吧
sum_ → sum_
```


<details>
<summary>英文原文</summary>

| $N_{tv}=100\frac{z_{tv}-\min_{v^{\prime}}z_{tv^{\prime}}}{\max_{v^{\prime}}z_{tv^{\prime}}-\min_{v^{\prime}}z_{tv^{\prime}}},\qquad\bar{N}_{v}=\frac{1}{6}\sum_{t}N_{tv}.$ | | (4)

</details>

因此，$\bar{N}_{v}$总结了每种变体的在六个任务中的相对表现，并未将其原生指标混为一谈。


<details>
<summary>英文原文</summary>

Thus, $\bar{N}_{v}$ summarizes the relative performance of each variant across the six tasks without conflating their native metrics.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0063)

表3：对六个 AgentHPOBench任务的消融实验。完整epoch的描述性标准化均值最高。移除任何组件后，该均值分别降低了13.17–55.59分。W/T/L表示完整epoch在任务层面的记录与各消融实验的对比情况。


<details>
<summary>英文原文</summary>

Table 3: Ablations on six AgentHPOBench tasks. Full EPOCH achieves the highest descriptive normalized mean. Removing any component reduces this mean by 13.17–55.59 points. W/T/L denotes the task-level record of Full EPOCH against each ablation in the paired report.

</details>

整个阶段不仅达到了最高的标准化均值（表3），还获得了最佳的任务平均排名（1.67）。移除记忆功能会使标准化均值下降13.17分，而移除证明接受、反驳或阶段控制则分别导致更大的下降幅度，分别为37.28分、41.75分和55.59分。配对比较同样表明，完整系统优于所有消融实验，包括与没有证明接受功能的变体相比取得了6/0/0的成绩。
无记忆版本在 ART 和 ModernBERT 任务上表现更好，这与探索与利用的权衡机制一致：无约束提议有助于对单个任务进行短期调优，而记忆功能则通过保存证据并引导搜索避开之前失败的区域，从而提升整体性能。这一模式凸显了 EPOCH 各组件之间的互补作用，而非单一任务层面的统一效应。这些总体发现也得到了独立验证：AlgoTune 和 Math14 对完整架构进行了端到端评估，而案例研究结果则通过特定任务的证书和重放实验得到证实。
总体而言，整个架构在最广泛的任务范围内都能展现出最出色的性能。


<details>
<summary>英文原文</summary>

Full EPOCH achieves both the highest normalized mean (Table 3 ) and the best mean task rank (1.67). Removing memory lowers the normalized mean by 13.17 points, while removing proof admission, falsification, or phase control produces larger reductions of 37.28, 41.75, and 55.59 points, respectively. The paired comparisons likewise favor the complete system over every ablation, including a 6/0/0 record against the variant without proof admission. The no-memory variant performs better on ART and ModernBERT, consistent with an exploration–exploitation trade-off: unconstrained proposals can benefit short-horizon tuning on individual tasks, whereas memory improves performance across the broader suite by preserving evidence and steering search away from previously unsuccessful regions. This pattern highlights the complementary roles of EPOCH’s components rather than a uniform per-task effect. The broader findings are supported independently: AlgoTune and Math14 evaluate the complete architecture end to end, while the case-study results are established through task-specific certificates and replay. Overall, the complete architecture achieves the strongest performance across the broadest range of tasks.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0066)

图2：AgentHPOBench不同变体的性能权衡。a，完整阶段获得最高的归一化均值，而无内存变体则获得最高的最小任务得分；虚线段连接了那些非支配的变体。b，完整阶段与无内存变体之间13.17点归一化均值差距的任务级分解。各项贡献相加即为总差距。


<details>
<summary>英文原文</summary>

Figure 2: Performance trade-offs across AgentHPOBench ablations. a , Full EPOCH achieves the highest normalized mean, whereas the no-memory variant attains the highest minimum task score; the dashed segment connects the observed nondominated variants. b , Task-level decomposition of the 13.17-point normalized-mean gap between Full EPOCH and the no-memory variant. Contributions sum to the aggregate gap.

</details>

### 从平均性能到任务覆盖度。


<details>
<summary>英文原文</summary>

From average performance to task coverage.

</details>

性能表现测试了整体收益是否能够贯穿所有任务，而非仅来自少数异常值。在 AlgoTune 实验中，EPOCH 在十二项任务中的五项上得分至少为 $0.60$，而任何基线模型最多仅在一项任务上达到此分数。在 AgentHPOBench 实验中，它在六项任务中的三项上达到了至少 $80$ 的归一化分数，而任何消融实验最多仅能在两项任务上达到此水平。因此，完整系统的优势不仅体现在平均分数上，还体现在对高性能任务的广泛覆盖能力上。


<details>
<summary>英文原文</summary>

Performance profiles test whether aggregate gains extend across tasks rather than arising from a small number of outliers. On AlgoTune, EPOCH scores at least $0.60$ on five of twelve tasks, compared with at most one task for any baseline. On AgentHPOBench, it reaches a normalized score of at least $80$ on three of six tasks, compared with at most two for any ablation. The advantage of the complete system therefore extends beyond its mean score to broader coverage of high-performing tasks.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0069)

图3：实证性能曲线，$P_{v}(\tau)=|\{t:s_{tv}\geq\tau\}|/T$，显示了采用变体$v$的任务中达到阈值$\tau$的比例。曲线越陡峭，表示在某一性能水平下覆盖范围越广。左图为十二个AlgoTune开发任务；右图为六个AgentHPOBench任务，这些任务的得分按方程（4）中的方式进行了归一化处理。各面板使用不同的评分尺度。


<details>
<summary>英文原文</summary>

Figure 3: Empirical performance profiles, $P_{v}(\tau)=|\{t:s_{tv}\geq\tau\}|/T$ , showing the fraction of tasks on which variant $v$ reaches threshold $\tau$ . Higher curves indicate broader coverage at a given performance level. Left, twelve AlgoTune development tasks. Right, six AgentHPOBench tasks, using task-level means normalized as in Eq. (4). The panels use different score scales.

</details>

## 5 从搜索到发现：案例研究


<details>
<summary>英文原文</summary>

5 From Search to Discovery: Case Studies

</details>

基准测试结果证明了 EPOCH 的搜索性能；接下来我们将探讨该搜索所产生的发现。以下十个案例研究涵盖了可执行优化、算法构建、形式化陈述及反例，展示了 EPOCH 如何将候选生成与任务特定证据相结合。图 4 展示了四个具有代表性的结果，表 4 则总结了保留结果、相关支持证据以及各项主张的范围。我们首先讨论可执行的构造与修复方法，然后转向形式化结果与反例；完整的推导过程详见补充材料。


<details>
<summary>英文原文</summary>

The benchmark results establish EPOCH’s search performance; we next examine the discoveries that this search produces. The following ten case studies span executable optimization, algorithmic construction, formal statements, and counterexamples, illustrating how EPOCH couples candidate generation with task-specific evidence. Figure 4 highlights four representative outcomes, while Table 4 summarizes the retained results, their supporting evidence, and the scope of each claim. We begin with executable constructions and repair, and then turn to formal results and counterexamples; complete derivations are provided in the supplementary.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0072)

图4：从左到右为四个发现案例。Hyperfactor在输出中复用同一个因子，从而降低了电路成本。中位数包含11个较小元素和11个较大元素；分支修复方法可得出比较界限。全立方体支持则产生严格不等式；面支持则产生等式（填充顶点：正权重）。H-beta违反了所提出的系数排序规则。示意图并非电路或决策树形式；表4记录了证据边界。


<details>
<summary>英文原文</summary>

Figure 4: Four discovery cases, left to right. Hyperfactor reuses one factor across outputs, reducing circuit cost. The median has eleven smaller and eleven larger elements; branch repair yields the comparison bound. Full cube support gives a strict inequality; facet support gives equality (filled vertices: positive weight). H-beta violates the proposed coefficient ordering. Schematics are not emitted circuits or decision trees; Table 4 records evidence boundaries.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0073)

表4：已记录的发现结果及其证据范围。


<details>
<summary>英文原文</summary>

Table 4: Documented discovery outcomes and their evidential scope.

</details>

### 5.1 建设性发现与算法优化


<details>
<summary>英文原文</summary>

5.1 Constructive Discoveries and Algorithmic Optimization

</details>

### 特征-双张量传输。


<details>
<summary>英文原文</summary>

Characteristic-two tensor transfer.

</details>

低边界秩分解是快速双线性算法的基本构建模块：每种显式构造都能提供降低代数复杂度的具体证明。一个主要难点在于有理分解在归约到特征为二的情况下可能会崩溃，从而无法直接在目标域中使用。EPOCH 将这一障碍转化为一种建设性搜索信号：它提取出不兼容的系数约束，利用这些约束的证例来选择一个新的退化图，并寻找一个有效的特征为二的替代方案。
在审计过程中，该方法将全部43个直接适用的公式转移过来，涵盖了24个坐标不同的目标，从而得出11个改进的边界界限。特别地，它发现了一种用于$T_{\rm ss444}$的30路径构造方法，并建立了$\brank(T_{\rm ss444})\leq 30$。这一成果在简单转移无法奏效的情况下提供了明确的低复杂度分解方案，进一步扩展了用于代数复杂度分析与快速算法设计的构建工具集。


<details>
<summary>英文原文</summary>

Low-border-rank decompositions are fundamental building blocks for fast bilinear algorithms: each explicit construction provides a concrete certificate of reduced algebraic complexity. A central difficulty is that rational decompositions can collapse after reduction to characteristic two, preventing their direct use over the target field. EPOCH turns this obstruction into a constructive search signal: it extracts the incompatible coefficient constraints, uses their witnesses to select a new degeneration chart, and searches for a valid characteristic-two replacement. Across the audit, this procedure transfers all 43 directly applicable formulas and covers 24 coordinate-distinct targets, yielding eleven improved border bounds. In particular, it discovers a 30-path construction for $T_{\rm ss444}$ , establishing $\brank(T_{\rm ss444})\leq 30$ . The result contributes explicit low-complexity decompositions in a regime where naïve transfer fails, expanding the constructive toolkit available for algebraic-complexity and fast-algorithm design.

</details>

### 统一大重心构建方法。


<details>
<summary>英文原文</summary>

Uniform Big-centroid construction.

</details>

当大重心构造能够跨越多个维度时，其价值尤为显著：与孤立的分解不同，这种统一的家族结构可以作为用于渐近边界秩和代数复杂性分析的可复用对象。EPOCH 能够发现这样的家族结构，并从一个可复用的左逆恒等式中推导出显式的 $q+u_{1}$ -项构造，其中 $q=\prod_{s=2}^{d}u_{s}$ ，而非通过重复的环境线性求解来实现。所得公式适用于所有指定的参数和域范围，用一种跨维度通用的构造替代了一系列特定实例的搜索过程。
从单个示例向明确可扩展的家族结构的转变，为研究相关的复杂度界限以及开发后续的基于质心张量结构提供了具体的基础。


<details>
<summary>英文原文</summary>

Big-centroid constructions are particularly valuable when they extend across a family of dimensions: unlike an isolated decomposition, a uniform family can serve as a reusable object for asymptotic border-rank and algebraic-complexity analysis. EPOCH discovers such a family, deriving an explicit $q+u_{1}$ -term construction, where $q=\prod_{s=2}^{d}u_{s}$ , from a reusable left-inverse identity rather than repeated ambient linear solves. The resulting formula applies throughout the stated parameter and field regimes, replacing a sequence of instance-specific searches with a single dimension-general construction. This shift from individual examples to an explicit scalable family provides a concrete foundation for studying the associated complexity bounds and for developing subsequent centroid-based tensor constructions.

</details>

### 改进了23值中位数选择方法。


<details>
<summary>英文原文</summary>

Improved median-of-23 selection.

</details>

中位数选择是比较复杂度中的一个基本问题，经典的 Hadian–Sobel 构造为 23 个元素的中位数选择提供了 55 次比较的上界（Hadian & Sobel, 1969）。EPOCH 通过将超预算执行路径视为可复用的反例来改进这一基准测试：它将 1,454 个复杂案例划分为十六种修复策略，从而减少了剩余的额外比较次数。最终得到的可执行决策过程的最坏情况成本最多为 54 次比较，这建立了 $V_{12}(23)\leq 54$ 标准，并将经典上界提高了一次比较。
这一结果表明，基于失败的搜索能够显著改善长期使用的精确选择构建基准测试。


<details>
<summary>英文原文</summary>

Median selection is a fundamental problem in comparison complexity, and the classical Hadian–Sobel construction gives a 55-comparison upper bound for selecting the median of 23 elements ( Hadian & Sobel, 1969 ) . EPOCH improves on this benchmark by treating over-budget execution paths as reusable counterexamples: it organizes 1,454 difficult cases into sixteen repair policies that eliminate the remaining excess comparisons. The resulting executable decision procedure has worst-case cost at most 54 comparisons, establishing $V_{12}(23)\leq 54$ and improving the classical bound by one comparison. This result demonstrates that failure-guided search can produce a concrete improvement to a long-standing constructive benchmark in exact selection.

</details>

### 可逆电路因子共享。


<details>
<summary>英文原文</summary>

Reversible circuit factor sharing.

</details>

T门是容错量子计算中的关键资源，因此减少T门数量成为可逆电路优化中的核心目标（Kissinger & van de Wetering, 2020）。在评估的AES构造中，常见的中间因子会为多个输出分别独立计算，从而产生大量的冗余非Clifford成本。EPOCH能够识别这些因子，并重新构建电路，使每个因子仅计算一次，然后在相关输出之间共享，最后不再计算。图5展示了这一机制，并表明相对节省量随着因子使用次数的增加而提高。
在匹配的 PyZX 合成下，所得到的电路将 T 计数从 10,746 减少至 9,234，从而消除了 1,512 个 T 门，并将非克利福德成本降低为 $14.10\%$，同时保留了所有 256 种输入-输出情况并恢复每一个辅助单元。这一结果在所述的库和合成模型下，为具有密码学相关性的可逆电路提供了显著的资源节省。


<details>
<summary>英文原文</summary>

T gates are a dominant resource in fault-tolerant quantum computation, making T-count reduction a central objective in reversible-circuit optimization ( Kissinger & van de Wetering, 2020 ) . In the evaluated AES construction, common intermediate factors are computed independently for multiple outputs, introducing substantial redundant non-Clifford cost. EPOCH identifies these factors and restructures the circuit so that each is computed once, shared across the relevant outputs, and subsequently uncomputed. Figure 5 illustrates this mechanism and shows how the relative saving increases with the number of factor uses. Under matched PyZX synthesis, the resulting circuit reduces the T-count from 10,746 to 9,234, eliminating 1,512 T gates and lowering the non-Clifford cost by $14.10\%$ , while preserving all 256 input-output cases and restoring every ancilla. This result provides a substantial resource reduction for a cryptographically relevant reversible circuit under the stated library and synthesis model.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0085)

图 5：因子共享及其成本缩放。共享因子仅计算一次，在多个 $k$ 输出中重复使用后再次被取消计算。以开启成本为 $c$、每次使用成本为 $u$ 为例，相对节省量为 $(k-1)c/[k(c+u)]$，且随着使用次数的增加而上升。伪代码保留了输入数据，并恢复了辅助组件。


<details>
<summary>英文原文</summary>

Figure 5: Factor sharing and its cost scaling. A shared factor is computed once, reused across $k$ outputs, and then uncomputed. With opening cost $c$ and per-use cost $u$ , the relative saving is $(k-1)c/[k(c+u)]$ and increases with the number of uses. The pseudocode preserves the input and restores the ancilla.

</details>

### 5.2 数学发现


<details>
<summary>英文原文</summary>

5.2 Mathematical Discoveries

</details>

剩余的案例包括经过验证的一般陈述、明确的反例，以及具有未闭合证明桥梁的定理候选者。


<details>
<summary>英文原文</summary>

The remaining cases distinguish a checked general statement, an explicit counterexample, and theorem candidates with open proof bridges.

</details>

## 具有等号特征的尖锐超立方体不等式。


<details>
<summary>英文原文</summary>

A sharp hypercube inequality with equality characterization.

</details>

让 $w_{v}\geq 0$ 为顶点 $v\in\{0,1\}^{d}$ 分配权重，让 $W=\sum_{v}w_{v}$ 和 $m_{i,b}=\sum_{v_{i}=b}w_{v}$ 分别表示坐标 $b$ 下 $i$ 面上的质量。对于绝对仿射单纯形行列式的不排序加权和 $\operatorname{SD}(w)$，EPOCH 予以确定


<details>
<summary>英文原文</summary>

Let $w_{v}\geq 0$ assign weights to the vertices $v\in\{0,1\}^{d}$ , let $W=\sum_{v}w_{v}$ , and let $m_{i,b}=\sum_{v_{i}=b}w_{v}$ denote the mass on the $b$ -facet in coordinate $i$ . For the unordered weighted sum $\operatorname{SD}(w)$ of absolute affine simplex determinants, EPOCH establishes

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0090)

**表格与文字对照**

```text
| $\operatorname{SD}(w)W^{d-1}\leq\prod_{i=1}^{d}m_{i,0}m_{i,1}.$ | | (5)

表内文字对照（数值与原始行列保持不变）：
operatorname → \operatorname
w)W → w)W
leq → leq
prod_ → prod_
```


<details>
<summary>英文原文</summary>

| $\operatorname{SD}(w)W^{d-1}\leq\prod_{i=1}^{d}m_{i,0}m_{i,1}.$ | | (5)

</details>

对于 $d\geq 3$ ，当且仅当所有质量都支撑在某一面上时，等式才成立。因此，坐标边缘量严格限制了全局行列式量，并决定了其简并性。将这一有限多项式定理与源几何陈述联系起来，仍需要所述的归一化桥梁（Averkov等人，2026）。


<details>
<summary>英文原文</summary>

For $d\geq 3$ , equality holds exactly when all mass is supported on a facet. Thus coordinate marginals sharply bound the global determinant quantity and characterize its degeneracies. Relating this finite-polynomial theorem to the source geometric statement still requires the stated normalization bridge ( Averkov et al., 2026 ) .

</details>

## 对 $H_{\beta}$ 前置加载的可靠反例。


<details>
<summary>英文原文</summary>

A stable counterexample to $H_{\beta}$ front-loading.

</details>

所提出的五级 $H_{\beta}$ 前置加载特性需要 $h_{2}^{\beta}\geq h_{3}^{\beta}$。EPOCH 发现了一个由九个元素构成的拟阵


<details>
<summary>英文原文</summary>

The proposed rank-five $H_{\beta}$ front-loading property requires $h_{2}^{\beta}\geq h_{3}^{\beta}$ . EPOCH discovers a nine-element matroid with

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0094)

**表格与文字对照**

```text
| $H_{0}=(1,9,27,27,9,1),\qquad H_{\beta}=(1,9,31,32,9,1),$ | | (6)

表内文字对照（数值与原始行列保持不变）：
qquad H_ → qquad H_
beta → beta
```


<details>
<summary>英文原文</summary>

| $H_{0}=(1,9,27,27,9,1),\qquad H_{\beta}=(1,9,31,32,9,1),$ | | (6)

</details>

因此，$h_{2}^{\beta}-h_{3}^{\beta}=-1$直接反驳了该排序。一种两行主扩展机制在每一个非负扩展次数下都保留该缺陷，从而产生无限多组结果，同时使相邻的猜想无法解决（Sinclair，2026）。


<details>
<summary>英文原文</summary>

and hence $h_{2}^{\beta}-h_{3}^{\beta}=-1$ , directly refuting the ordering. A two-line principal-extension mechanism preserves the defect for every nonnegative extension count, producing an infinite family while leaving neighboring conjectures unresolved ( Sinclair, 2026 ) .

</details>

### 额外的数学结果与验证边界。


<details>
<summary>英文原文</summary>

Additional Mathematical Results and Verification Boundaries.

</details>

另外四位候选人涉及三状态核、Full Perazzo排序、海森堡极限（Kammeyer，2026）以及在线嵌入渐近性（Altschuler等，2026）。表4总结了他们的验证核心内容及剩余的桥梁理论：边界证明、插值与排序论证、表示限制以及递归渐近性。详细内容请参阅补充材料。


<details>
<summary>英文原文</summary>

Four further candidates concern a three-state kernel, Full Perazzo ranks, a Heisenberg limit ( Kammeyer, 2026 ) , and online-embedding asymptotics ( Altschuler et al., 2026 ) . Table 4 summarizes their verified cores and the remaining bridges: boundary certificates, interpolation and rank arguments, representation limits, and recurrence asymptotics. Full details appear in the supplement.

</details>

## 6 讨论与局限性


<details>
<summary>英文原文</summary>

6 Discussion and Limitations

</details>

这些基准测试与工具集进一步支持了上述结论。综合收益分析表明，合同、类型化内存、证伪、接受与重放能够引导搜索过程；而具体案例则展示了如何通过失败转化为修复策略，以及验证机制如何将候选方案转化为有特定范围的研究成果。这种证据体系对于结合代码、符号推理、仿真和形式化方法的 AI4Math 与 AI4Science 工作流尤为重要。


<details>
<summary>英文原文</summary>

The benchmarks and portfolio support complementary conclusions. Aggregate gains show that contracts, typed memory, falsification, admission, and replay can guide search, while the cases show how failures become repair strategies and verification turns candidates into scoped research artifacts. This evidence discipline is particularly relevant to AI4Math and AI4Science workflows combining code, symbolic reasoning, simulation, and formal methods.

</details>

两个限制条件定义了未来的发展方向。首先，需要更大规模的配对评估，并采用固定的预算与全面的资源核算机制。其次，尽管 EPOCH 能够明确证据缺失问题，但并未完全解决所有问题；专业人员的声明仍需进行外部审核、陈述一致性检查及优先级评估。将该协议扩展到模拟实验、数据库、科学仪器以及专家互动领域，仍是一个重要的研究方向。


<details>
<summary>英文原文</summary>

Two limitations define the next frontier. First, larger paired evaluations with fixed budgets and comprehensive resource accounting are needed. Second, although EPOCH makes evidential gaps explicit, it does not resolve them all; specialist claims still require external review, statement alignment, and priority assessment. Extending the protocol to simulations, experiments, databases, scientific instruments, and expert interaction remains an important direction.

</details>

## 7 结论


<details>
<summary>英文原文</summary>

7 Conclusion

</details>

EPOCH 将人工智能研究智能体从候选生成器重新定义为基于证据引导的搜索系统。通过结合类型化记忆、主动证伪、承认机制与独立重放技术，EPOCH 能够将成功、失败及修复后的搜索路径转化为包含明确支持证据的保留结果。
在十个探索问题中，这一过程带来了具体的进展：11个改进的张量边界界限，一个可将AES可逆电路中的1,512-T门数量减少的电路设计，一种包含54次比较的23值中位数算法，该算法提升了经典的55次比较Hadian–Sobel界限（Hadian & Sobel, 1969），一项具有等式特性的全维度超立方体不等式，以及一族能够反驳所提出的$H_{\beta}$前置加载特性的理论模型。
结合在 AlgoTune 上的最先进汇总结果以及在 Math14 和 AgentHPO 上领先的表现，这些成果表明基于证据的搜索不仅能优化基准分数，还能产生具有实际意义的算法和数学发现。


<details>
<summary>英文原文</summary>

EPOCH reframes AI research agents from candidate generators into systems for evidence-guided discovery. By combining typed memory, active falsification, admission, and independent replay, EPOCH turns successful, failed, and repaired search trajectories into retained results with explicit supporting evidence. Across ten discovery problems, this process yields concrete advances: eleven improved tensor border bounds, a 1,512-T-gate reduction in an AES reversible circuit, a 54-comparison median-of-23 procedure that improves the classical 55-comparison Hadian–Sobel bound ( Hadian & Sobel, 1969 ) , a sharp all-dimensional hypercube inequality with an equality characterization, and an infinite family refuting the proposed $H_{\beta}$ front-loading property. Together with state-of-the-art aggregate results on AlgoTune and leading performance on Math14 and AgentHPO, these outcomes show that evidence-governed search can do more than optimize benchmark scores: it can generate substantive algorithmic and mathematical discoveries.

</details>

### 人工智能使用声明


<details>
<summary>英文原文</summary>

AI Use Statement

</details>

使用生成式 AI 工具协助润色文稿，以及开发候选程序、结构、数学论证和证明。作者对所有 AI 辅助成果进行了审查。可执行结果通过特定任务评估器和独立重放进行验证；有限数学结论通过精确或穷举计算进行核实；正式结果则在必要时在 Lean 中进行了检查。作者对最终文本、结论、代码和数学成果承担全部责任。


<details>
<summary>英文原文</summary>

Generative AI tools were used to assist with manuscript polishing and with the development of candidate programs, constructions, mathematical arguments, and proofs. The authors reviewed all AI-assisted outputs. Executable results were checked through task-specific evaluators and independent replay; finite mathematical claims were verified by exact or exhaustive computation; and formal results were checked in Lean where indicated. The authors take full responsibility for the final text, claims, code, and mathematical artifacts.

</details>

### 可复现性声明


<details>
<summary>英文原文</summary>

Reproducibility Statement

</details>

补充材料提供了用于审核和复现我们报告结果所需的信息。在实证评估方面，它记录了冻结实施状态、任务组与数据分割方式、模型及种子标识、搜索预算、正确性与计时流程、端点选择与保留重放协议以及任务级结果。对于发现案例，则包含详细的推导过程、精确或全面验证流程、形式化范围、未完成的证明义务以及记录好的重放接口。
所有声明均受限于相应证据所确立的范围；特别是，有限证书和形式验证核函数不会被作为用于证明更广泛结果的依据来呈现。


<details>
<summary>英文原文</summary>

The supplementary material provides the information needed to audit and reproduce our reported results. For the empirical evaluations, it records frozen implementation status, task cohorts and data splits, model and seed identifiers, search budgets, correctness and timing procedures, endpoint-selection and held-out replay protocols, and task-level results. For the discovery cases, it includes detailed derivations, exact or exhaustive verification procedures, formalization scopes, outstanding proof obligations, and documented replay interfaces. All claims are restricted to the scope established by the corresponding evidence; in particular, finite certificates and formally verified kernels are not presented as establishing broader results.

</details>

## 参考文献


<details>
<summary>英文原文</summary>

References

</details>

AlgoTune contributors (2026) AlgoTune contributors. AlgoTune: Official task repository, 2026. URL https://github.com/oripress/AlgoTune . Pinned task and data revisions are reported in the supplementary
material; accessed September 17, 2026.

Altschuler et al. (2026) Dylan J. Altschuler, Quentin Dubroff, and Konstantin Tikhomirov. Online permutation embedding: Optimal stopping and scaling laws. arXiv preprint arXiv:2608.19050 , 2026. URL https://arxiv.org/abs/2608.19050 .

Anthropic (2026) Anthropic. Learning more about Claude’s mathematical capabilities, August
2026. URL https://www.anthropic.com/research/riemann-zeta . Primary research announcement, August 10; revised August 13, 2026.
Reports a lower bound for the proportion of critical-line zeros, not a proof
of the Riemann hypothesis. Accessed September 18, 2026.

Averkov et al. (2026) Gennadiy Averkov, Katherina von Dichter, and Ivan Soprunov. On the log-submodularity for zonoids: from mixed volume inequalities
to the hypercube. arXiv preprint arXiv:2608.14909 , 2026. URL https://arxiv.org/abs/2608.14909 .

Cemri et al. (2026) Mert Cemri, Shubham Agrawal, Akshat Gupta, Shu Liu, Audrey Cheng, Qiuyang Mang,
Ashwin Naren, Lutfi Eren Erdogan, Koushik Sen, Matei Zaharia, Alex Dimakis,
and Ion Stoica. AdaEvolve: Adaptive LLM driven zeroth-order optimization. arXiv preprint arXiv:2602.20133 , 2026. URL https://arxiv.org/abs/2602.20133 .

Dörrer et al. (2025) Josua Dörrer, Konrad Gendle, Johanna Betz, Julius von Smercek, Andreas
Steding, and Florian Stober. Exact lower bounds for the number of comparisons in selection. In 23rd International Symposium on Experimental Algorithms (SEA
2025) , 2025. doi: 10.4230/LIPIcs.SEA.2025.16 . URL https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.SEA.2025.16 .

Fawzi et al. (2022) Alhussein Fawzi et al. Discovering faster matrix multiplication algorithms with
reinforcement learning. Nature , 610:47–53, 2022. doi: 10.1038/s41586-022-05172-4 . URL https://doi.org/10.1038/s41586-022-05172-4 .

Google DeepMind (2022) Google DeepMind. AlphaTensor: Published algorithms and verification artifacts, 2022. URL https://github.com/google-deepmind/alphatensor . Accessed September 18, 2026.

Google DeepMind (2023) Google DeepMind. Materials discovery: GNoME research artifacts, 2023. URL https://github.com/google-deepmind/materials_discovery . Accessed September 18, 2026.

Google DeepMind (2024) Google DeepMind. AlphaGeometry: Code and model artifacts, 2024. URL https://github.com/google-deepmind/alphageometry . Accessed September 18, 2026.

Hadian & Sobel (1969) Abdollah Hadian and Milton Sobel. Selecting the $t$ -th largest using binary errorless comparisons. Technical Report Technical Report 121, School of Statistics,
University of Minnesota, 1969. URL https://hdl.handle.net/11299/199105 .

Hubert et al. (2025) Thomas Hubert et al. Olympiad-level formal mathematical reasoning with reinforcement
learning. Nature , 2025. doi: 10.1038/s41586-025-09833-y . URL https://www.nature.com/articles/s41586-025-09833-y .

Kammeyer (2026) Holger Kammeyer. A counterexample to the determinant approximation conjecture. arXiv preprint arXiv:2609.15567 , 2026. URL https://arxiv.org/abs/2609.15567 .

Kassabov et al. (2026) Martin Kassabov, J. M. Landsberg, Victor Souza, and Philip Speegle. Disjoint and nearly disjoint sums of matrix multiplication tensors
and their centroids. arXiv preprint arXiv:2608.27434 , 2026. URL https://arxiv.org/abs/2608.27434 .

Kissinger & van de Wetering (2020) Aleks Kissinger and John van de Wetering. Reducing T-count with the ZX-calculus. Physical Review A , 102(2):022406, 2020. doi: 10.1103/PhysRevA.102.022406 .

Li et al. (2022) Yujia Li et al. Competition-level code generation with AlphaCode. Science , 378:1092–1097, 2022. doi: 10.1126/science.abq1158 . URL https://arxiv.org/abs/2203.07814 .

Lu et al. (2024) Chris Lu et al. The AI Scientist: Towards fully automated open-ended scientific
discovery. arXiv preprint arXiv:2408.06292 , 2024. URL https://arxiv.org/abs/2408.06292 .

Merchant et al. (2023) Amil Merchant, Simon Batzner, Samuel S. Schoenholz, Muratahan Aykol, Gowoon
Cheon, and Ekin Dogus Cubuk. Scaling deep learning for materials discovery. Nature , 624:80–85, 2023. doi: 10.1038/s41586-023-06735-9 . URL https://www.nature.com/articles/s41586-023-06735-9 .

Novikov et al. (2025) Alexander Novikov et al. AlphaEvolve: A coding agent for scientific and algorithmic
discovery. arXiv preprint arXiv:2506.13131 , 2025. URL https://arxiv.org/abs/2506.13131 .

OpenAI (2026) OpenAI. On the Navier–Stokes millennium prize problem, September 2026. URL https://openai.com/index/navier-stokes-solution/ . Primary research announcement, September 8, 2026, with linked
mathematical writeup and Lean formalization. Smooth-forcing formulations C
and D. Accessed September 18, 2026.

OpenEvolve contributors (2026) OpenEvolve contributors. OpenEvolve: Open-source evolutionary program optimization, 2026. URL https://github.com/algorithmicsuperintelligence/openevolve . Pinned experimental revision is reported in the supplementary
material; accessed September 17, 2026.

OpenMOSS (2026) OpenMOSS. AgentHPOBench: A benchmark for evaluating llm agents as sequential
hyperparameter optimizers, 2026. URL https://github.com/OpenMOSS/AgentHPOBench . Official task repository; accessed September 17, 2026.

Romera-Paredes et al. (2024) Bernardino Romera-Paredes et al. Mathematical discoveries from program search with large language
models. Nature , 625:468–475, 2024. doi: 10.1038/s41586-023-06924-6 . URL https://doi.org/10.1038/s41586-023-06924-6 .

Schrittwieser et al. (2020) Julian Schrittwieser, Ioannis Antonoglou, Thomas Hubert, et al. Mastering Atari, Go, chess and shogi by planning with a learned
model. Nature , 588:604–609, 2020. doi: 10.1038/s41586-020-03051-4 . URL https://arxiv.org/abs/1911.08265 .

Silver et al. (2018) David Silver, Thomas Hubert, Julian Schrittwieser, et al. A general reinforcement learning algorithm that masters chess, shogi,
and Go through self-play. Science , 362(6419):1140–1144, 2018. doi: 10.1126/science.aar6404 . URL https://doi.org/10.1126/science.aar6404 .

Sinclair (2026) Thomas Sinclair. The radial derivative on the graded Möbius algebra. arXiv preprint arXiv:2608.18519 , 2026. URL https://arxiv.org/abs/2608.18519 .

Trinh et al. (2024) Trieu H. Trinh, Yuhuai Wu, Quoc V. Le, He He, and Thang Luong. Solving olympiad geometry without human demonstrations. Nature , 625:476–482, 2024. doi: 10.1038/s41586-023-06747-5 . URL https://www.nature.com/articles/s41586-023-06747-5 .

Yamada et al. (2025) Yutaro Yamada et al. The AI Scientist-v2: Workshop-level automated scientific discovery
via agentic tree search. arXiv preprint arXiv:2504.08066 , 2025. URL https://arxiv.org/abs/2504.08066 .

## 附录 A 证据清单与报告规范


<details>
<summary>英文原文</summary>

Appendix A Evidence Inventory and Reporting Conventions

</details>

该补充材料对原始版本、官方重放、机制诊断及记录下来的发现结果进行了区分。在所有注册的开发矩阵中，EPOCH的平均得分最高（0.65），而最强大的基线版本仅为0.53。在官方重放测试中，其对所有四个基线的平均效果均为正向，最大任务级收益约为0.48。在AgentHPO上，整个系统的标准化平均得分为77.48——比最强大的组件移除变体高出13.17分——且所有六个报告任务中的证明通过率均良好。
该发现系列还包含精确张量构造、电路简化、有限反例以及形式化核函数。本补充材料的其余部分将说明这些优势是如何产生的，以及每个数学结论是如何被确立的。


<details>
<summary>英文原文</summary>

This supplement distinguishes among original runs, the official replay, mechanism diagnostics, and documented discovery artifacts. Across the registered development matrix, EPOCH achieves the highest mean score (0.65), compared with 0.53 for the strongest baseline. In the official replay, its mean effect is positive against all four baselines, with a maximum task-level gain of approximately 0.48. On AgentHPO, the full system attains a normalized mean score of 77.48—13.17 points above the strongest component-removal variant—and proof admission is favorable on all six reported tasks. The discovery portfolio further contributes exact tensor constructions, circuit reductions, finite counterexamples, and formal kernels. The remainder of this supplement explains how these advantages arise and how each mathematical conclusion is established.

</details>

### 如何阅读图表。


<details>
<summary>英文原文</summary>

How to read the figures.

</details>

基准测试图表还原了所提供的汇总数据。电路和证明图解释了各元素的依赖关系；它们并非额外的测量结果。图 S9 – S11 中的曲线是对明确表述的公式进行的验证，其中假设与证明状态均被保留。这些曲线不应被视为对这些公式的独立确认。精确的数值结果则保留在相邻的表格中。


<details>
<summary>英文原文</summary>

Benchmark plots reproduce the supplied aggregate records. Circuit and proof diagrams explain dependencies; they are not additional measured results. Curves in Figures S9 – S11 are evaluations of the explicitly stated formulas, with hypotheses and proof status preserved. They should not be counted as independent confirmation of those formulas. Exact numerical results remain in the adjacent tables.

</details>

### A.1 预注册评估方案与可重复性控制措施


<details>
<summary>英文原文</summary>

A.1 Pre-registered Evaluation Protocol and Reproducibility Controls

</details>

所有对比系统、适配器、任务定义及官方数据在评估前均被冻结。注册的主训练计划使用了模型标签 DeepSeek-V4-Flash，以及种子编号 2026081901、2026081902 和 2026081903。


<details>
<summary>英文原文</summary>

All compared systems, adapters, task definitions, and official data were frozen before evaluation. The registered main schedule used the model label DeepSeek-V4-Flash and seeds 2026081901 , 2026081902 , and 2026081903 .

</details>

AlgoTune 公开搜索使用前八组官方训练数据、一个可编辑的任务本地程序、原始正确性验证器，以及 48 个语义调用上限。定时运行则通过全新进程进行，每个公开实例包含一次预热阶段和三次测量重复实验。官方重放则使用前 32 组测试数据用于预定的原始终点。


<details>
<summary>英文原文</summary>

AlgoTune public search uses the first eight official train rows, a single editable task-local program, the original correctness verifier, and a 48-semantic-call ceiling. Timing runs in a fresh process with one warmup and three measured repetitions per public instance. Official replay uses the first 32 test rows for scheduled original endpoints.

</details>

### A.2 评估指标与比较规范


<details>
<summary>英文原文</summary>

A.2 Evaluation Metrics and Comparison Conventions

</details>

对于完整的任务 $t$ 和方法 $m$，令 $q_{tms}$ 为其冻结后的标准化评估分数。开发任务的均值为 $\bar{q}_{tm}=|S|^{-1}\sum_{s\in S}q_{tms}$，与基线模型的跨任务效应为 $b$。平衡开发矩阵包含 $|S|=3$、$|T|=12$。官方重放则采用针对报告中的官方重放样本群的类似效应。开发恢复与原始重放并不使用相同的终点人群。


<details>
<summary>英文原文</summary>

For a complete task $t$ and method $m$ , let $q_{tms}$ be its frozen normalized evaluator score. The development task mean is $\bar{q}_{tm}=|S|^{-1}\sum_{s\in S}q_{tms}$ , and the cross-task effect against baseline $b$ is $|T|^{-1}\sum_{t}(\bar{q}_{t,\textsc{EPOCH}}-\bar{q}_{tb})$ . The balanced development matrix has $|S|=3$ , $|T|=12$ . Official replay uses the analogous effect on the reported official-replay cohort. Development recovery and original replay do not share an identical endpoint population.

</details>

对于异构智能体HPO指标，将 higher-is-better 指标记为 $d_{t}=1$，将 lower-is-better 指标记为 $d_{t}=-1$。任务级指标为


<details>
<summary>英文原文</summary>

For heterogeneous AgentHPO metrics, let $d_{t}=1$ for higher-is-better metrics and $d_{t}=-1$ for lower-is-better metrics. Task-level means are

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0146)

**表格与文字对照**

```text
| $\bar{y}_{tv}=\frac{1}{|S_{tv}|}\sum_{s\in S_{tv}}y_{tvs}.$ | | (S1)

表内文字对照（数值与原始行列保持不变）：
bar → 酒吧
frac → 分数
sum_ → sum_
in S_ → 在 S_中
tvs → 电视设备
```


<details>
<summary>英文原文</summary>

| $\bar{y}_{tv}=\frac{1}{|S_{tv}|}\sum_{s\in S_{tv}}y_{tvs}.$ | | (S1)

</details>

配对效应采用共享评估调度方式 $P_{tb}=S_{t,\textsc{EPOCH}}\cap S_{tb}$ ：


<details>
<summary>英文原文</summary>

A paired effect uses the shared evaluation schedule $P_{tb}=S_{t,\textsc{EPOCH}}\cap S_{tb}$ :

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0148)

**表格与文字对照**

```text
| $\delta_{tb}=\frac{1}{|P_{tb}|}\sum_{s\in P_{tb}}d_{t}(y_{t,\textsc{EPOCH},s}-y_{tbs}).$ | | (S2)

表内文字对照（数值与原始行列保持不变）：
delta_ → delta_
frac → 分数
sum_ → sum_
in P_ → 在 P_中
textsc → 文本集
EPOCH → EPOCH
tbs → TBS
```


<details>
<summary>英文原文</summary>

| $\delta_{tb}=\frac{1}{|P_{tb}|}\sum_{s\in P_{tb}}d_{t}(y_{t,\textsc{EPOCH},s}-y_{tbs}).$ | | (S2)

</details>

提供的成对报告分别给出了W/T/L和符号检验结果，与任务级均值分开呈现。


<details>
<summary>英文原文</summary>

The supplied paired report gives W/T/L and sign-test results separately from task-level means.

</details>

## 附录 B 数据集构建、任务选择与数据分割


<details>
<summary>英文原文</summary>

Appendix B Dataset Construction, Task Selection, and Data Splits

</details>

本部分区分了四个容易混淆的对象：基准测试的原生数据、本次研究所指定的任务子集、搜索过程中可获得的公开观测结果，以及用于端点评估的终端观测结果。所提供的工件并不描述新的众包数据集，而是锁定了现有基准测试库中的任务子集与视图。表 S1展示了相应的分析单元。


<details>
<summary>英文原文</summary>

This section distinguishes four objects that are easy to conflate: a benchmark’s native data, the task subset registered for this study, the public observations available during search, and the terminal observations reserved for endpoint evaluation. The supplied artifacts do not describe a newly crowdsourced dataset. Rather, they freeze task subsets and views from existing benchmark repositories. Table S1 gives the resulting analysis units.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0152)

表 S1：构建与拆分摘要。“Cell”表示一项任务-方法-种子执行。证书案例不被视为采样基准行。


<details>
<summary>英文原文</summary>

Table S1: Construction and split summary. “Cell” denotes one task–method–seed execution. Certificate cases are not treated as sampled benchmark rows.

</details>

### B.1 任务队列与评估数据分离


<details>
<summary>英文原文</summary>

B.1 Task Cohort and Evaluation Data Separation

</details>

实验样本集包含表 S1 中列出的十二项任务：仿射变换、可通信性测试、Convolve2D、zeta-零计数、循环独立集、实特征值、FFT卷积、最大公共子图、NMF、Robertson ODE、实多项式和SVM。提供的记录表明该样本集属于一个固定的基准子集。


<details>
<summary>英文原文</summary>

The experimental cohort comprises the twelve-task schedule reported in Table S1 : affine transform, communicability, Convolve2D, zeta-zero count, cyclic independent set, real eigenvalues, FFT convolution, maximum common subgraph, NMF, Robertson ODE, real polynomial, and SVM. The supplied record identifies this set as a frozen benchmark subset.

</details>

对于每个任务，检索范围仅限于官方训练数据的前八行。这些行可能会影响代码提案、公开正确性反馈以及端点选择。官方测试数据的前32行仅用于已选原始端点的计划重试；其结果不会反馈到该端点的搜索历史中。如果测试失败导致产生新的提案，所生成的成果属于独立实验，不得作为原保留重试的一部分进行报告。
行顺序和成员关系遵循表 S1中记录的冻结官方数据修订方案；未报告任何重新排序、分层或交叉验证操作。


<details>
<summary>英文原文</summary>

For each task, search is restricted to the first eight rows of the official training data. These rows may influence code proposals, public correctness feedback, and endpoint selection. The first 32 rows of the official test data are reserved exclusively for scheduled replay of the already selected original endpoint; their outcomes are not fed back into that endpoint’s search history. If a test failure prompts a new proposal, the resulting artifact constitutes a separate experiment and must not be reported as part of the original held-out replay. Row order and membership follow the frozen official-data revision documented in Table S1; no reshuffling, stratification, or cross-validation is reported.

</details>

### B.2 Math14 套件构建与分阶段评估


<details>
<summary>英文原文</summary>

B.2 Math14 Suite Construction and Staged Evaluation

</details>

Math14 是一个项目冻结的十四项数学目标集合。其注册设计构成了一个平衡的因子矩阵，包含 $14\times 5\times 3=210$ 个单元，分别对应十四项目标、五种系统变体以及每项系统对对应的三颗种子。该集合是分阶段构建和评估的：首先确定目标列表、系统变体、种子安排和评估规则；然后按照注册方案完成可执行单元；最后在汇总分析之前将结果记录固定下来。


<details>
<summary>英文原文</summary>

Math14 is a project-frozen suite of fourteen mathematical objectives. Its registered design forms a balanced factorial matrix of $14\times 5\times 3=210$ cells, corresponding to fourteen objectives, five compared systems, and three registered seeds per objective–system pair. The suite was assembled and evaluated in stages: the objective list, system variants, seed schedule, and evaluation rules were fixed first; executable cells were then completed under the registered protocol; and the resulting records were frozen before aggregate analysis.

</details>

### B.3 智能体 HPO 任务与本地评估分割方式


<details>
<summary>英文原文</summary>

B.3 AgentHPO Tasks and Native Evaluation Splits

</details>

所报道的 AgentHPO消融分析涵盖了完整的 EPOCH 系统以及针对内存、虚假检测器、证据接受机制和相位控制器四种组件移除变体。所研究的六种环境涉及不同的领域：游戏式强化学习（ART 2048）、自然语言推理（ModernBERT MNLI）、噪声图学习（NoisyGL Cora）、半监督面部年龄回归（RankUp UTKFace）、长时段时间序列预测（SparseTSF ETTm1）以及表格回归（TabM California）。
他们的目标指标分别是胜率、分类准确率、节点分类准确率、平均绝对误差（MAE）、均方误差（MSE）和均方根误差（RMSE）。每个环境的原生优化方向均得到保留。


<details>
<summary>英文原文</summary>

The reported AgentHPO ablation analysis covers the full EPOCH system and four component-removal variants targeting memory, the falsifier, proof admission, and the phase controller. The six reported environments span heterogeneous domains: game-playing reinforcement learning (ART 2048), natural-language inference (ModernBERT MNLI), noisy graph learning (NoisyGL Cora), semi-supervised facial-age regression (RankUp UTKFace), long-horizon time-series forecasting (SparseTSF ETTm1), and tabular regression (TabM California). Their target metrics are, respectively, win rate, classification accuracy, node-classification accuracy, mean absolute error (MAE), mean squared error (MSE), and root mean squared error (RMSE). Each environment’s native optimization direction is preserved.

</details>

### B.4 发现案例证据是如何构建的


<details>
<summary>英文原文</summary>

B.4 How discovery-case evidence is constructed

</details>

数学和算法案例并未使用统计性训练/测试分割方法。每个案例都从固定的问题陈述、比较对象、可编辑对象以及断言边界开始。搜索过程可以检查公开的代数恒等式、来源构造或有限实例；一旦被采纳，所选对象便需承担严格的验证义务。证据按四个不可互换的层次结构进行构建：


<details>
<summary>英文原文</summary>

The mathematical and algorithmic cases do not use a statistical train/test split. Each begins with a frozen problem statement, comparator, editable object, and claim boundary. Search may inspect public algebraic identities, source constructions, or finite instances; admission then binds the selected object to exact verification obligations. Evidence is constructed in four noninterchangeable layers:

</details>

1.


<details>
<summary>英文原文</summary>

1.

</details>

语义重构：根据目标的定义独立重建它（例如张量坐标、AES真值表或选择排名）。


<details>
<summary>英文原文</summary>

Semantic reconstruction: rebuild the target independently from its definition (for example, tensor coordinates, AES truth tables, or selection ranks).

</details>

2.


<details>
<summary>英文原文</summary>

2.

</details>

精确或全面的重放：在声明为有限的情况下，对所定义的有限宇宙中的每一个坐标或每个成员进行核查。


<details>
<summary>英文原文</summary>

Exact or exhaustive replay: check every coordinate or every member of the declared finite universe when the claim is finite.

</details>

3.


<details>
<summary>英文原文</summary>

3.

</details>

突变控制：破坏因子、系数、门限、递归项或证书字段，要求验证者拒绝该修改。


<details>
<summary>英文原文</summary>

Mutation controls: corrupt a factor, coefficient, gate, recurrence term, or certificate field and require the verifier to reject it.

</details>

4.


<details>
<summary>英文原文</summary>

4.

</details>

正式或分析性桥梁：证明连接被验证的有限对象与所陈述定理的可复用蕴含关系，同时列出所有剩余的源特定或表示特定桥梁。


<details>
<summary>英文原文</summary>

Formal or analytic bridge: prove the reusable implication connecting the checked finite object to the stated theorem, while listing any remaining source-specific or representation-specific bridge.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0171)

图 S1：从命题定义到最终定理桥梁的证据构建过程。精确重放确立了所声明的有限对象；变异控制测试对选定错误的敏感度；只有最终的桥梁才将这些事实转化为所陈述的数学命题。该图是逻辑性的，而非实验计数。


<details>
<summary>英文原文</summary>

Figure S1: Evidence construction from claim definition to the final theorem bridge. Exact replay establishes the declared finite object; mutation controls test sensitivity to selected errors; only the final bridge transfers those facts to the stated mathematical claim. The diagram is logical, not a count of experiments.

</details>

发现的示例可以指导搜索过程，但所提出的陈述是由重放领域决定的，而非取决于有多少探索性示例成功。因此，有限穷尽证书和抽样数值检验在第 I 至 K 节中被赋予不同的标签。


<details>
<summary>英文原文</summary>

Discovery examples may guide the search, but the admitted statement is determined by the replay domain, not by how many exploratory examples happened to succeed. A finite exhaustive certificate and a sampled numerical check therefore receive different labels throughout Sections I – K .

</details>

### 有限证书充分性。


<details>
<summary>英文原文</summary>

Finite-certificate sufficiency.

</details>

设 $U$ 为某个命题所指定的有限宇宙，设 $C$ 为被认可的候选对象，设 $P(C,u)$ 为需要为每个 $u\in U$ 建立的语义属性。假设一个独立的构造器不遗漏或重复地枚举 $U$，而一个准确可靠的校验器在 $P(C,u)$ 成立时才会返回真。


<details>
<summary>英文原文</summary>

Let $U$ be the finite universe named by a claim, let $C$ be the admitted candidate, and let $P(C,u)$ be the semantic property to be established for every $u\in U$ . Suppose an independent constructor enumerates $U$ without omission or duplication, and a sound exact checker returns true exactly when $P(C,u)$ holds. Then

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0175)

**表格与文字对照**

```text
| $\left(|\widehat{U}|=|U|\ \wedge\ \widehat{U}=U\ \wedge\ \bigwedge_{u\in\widehat{U}}P(C,u)\right)\Longrightarrow\forall u\in U,\ P(C,u).$ | | (S3)

表内文字对照（数值与原始行列保持不变）：
left( → 左（
widehat → widehat
wedge → 楔形物
bigwedge_ → 大楔形符号
P(C → P(C
right) → 正确)
Longrightarrow → Longrightarrow
forall u → 对所有 u
in U → 在 U 中
```


<details>
<summary>英文原文</summary>

| $\left(|\widehat{U}|=|U|\ \wedge\ \widehat{U}=U\ \wedge\ \bigwedge_{u\in\widehat{U}}P(C,u)\right)\Longrightarrow\forall u\in U,\ P(C,u).$ | | (S3)

</details>

### 证明。


<details>
<summary>英文原文</summary>

Proof.

</details>

采用任意的 $u\in U$。独立枚举的完整性可得到 $u\in\widehat{U}$，而该元素的被接受检查器结果则得到 $P(C,u)$。由于 $u$是任意的，因此普遍有限性结论随之成立。检查器的正确性以及等式关系 $\widehat{U}=U$是前提，而非大量通过次数的结果；变异控制机制可能会暴露出正确性的缺陷，但无法仅凭这些前提本身来证明正确性。∎


<details>
<summary>英文原文</summary>

Take arbitrary $u\in U$ . Completeness of the independent enumeration gives $u\in\widehat{U}$ , and the accepted checker result for that element gives $P(C,u)$ . Since $u$ was arbitrary, the universal finite claim follows. Soundness of the checker and equality $\widehat{U}=U$ are premises, not consequences of a large pass count; mutation controls can expose violations of soundness but cannot prove those premises by themselves.
∎

</details>

### B.5 排除、去重和污染控制措施


<details>
<summary>英文原文</summary>

B.5 Exclusions, deduplication, and contamination controls

</details>

任务-方法-种子键在基准矩阵中仅被计数一次。因传输失败导致的重试仍保留相同的键和来源信息；端点重放不会成为新的观测结果。正确但无改进性的提案仍保留由冻结规则选定的端点。错误的提案会被记录为被拒绝的试验，当合同规定时，可用的已验证替代方案则作为方法结果。在案例研究中，坐标对称性和同构简化可能会压缩搜索范围，但在纳入之前，报告的覆盖度会重新扩展至完整的声明范围。


<details>
<summary>英文原文</summary>

A task–method–seed key is counted once in a benchmark matrix. Retries caused by transport failure retain the same key and provenance; endpoint replays do not become new observations. Correct but non-improving proposals retain the endpoint selected by the frozen rule. Incorrect proposals are recorded as rejected trials, and an available verified fallback remains the method outcome when the contract provides one. In case studies, coordinate symmetries and isomorphism reductions may compress a search, but reported coverage is expanded back to the full declared universe before admission.

</details>

## 附录 C 实验配置与执行细节


<details>
<summary>英文原文</summary>

Appendix C Experimental Configuration and Execution Details

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0181)

表 S2汇总了那些分散在所提供的审计文件中的设置。


<details>
<summary>英文原文</summary>

Table S2 consolidates the settings that are otherwise distributed across the supplied audit documents.

</details>

表 S2：可从提供的工件中恢复的冻结执行配置。


<details>
<summary>英文原文</summary>

Table S2: Frozen execution configuration recoverable from the supplied artifacts.

</details>

### C.1 常见的执行生命周期


<details>
<summary>英文原文</summary>

C.1 Common execution lifecycle

</details>

每个已注册单元都从特定方法的冻结修订版本及相同的任务合同开始。执行者在模型交互之前记录初始产物及验证结果。在干预点 $t$ 处，该方法仅接收公共任务视图及其变体允许的信息。提案必须被解析为预期的架构，并保持在可编辑区域内。候选执行方案随后记录正确性、目标值、资源使用情况以及任何任务特定的挑战。EPOCH 还记录证据引用、反驳结果、阶段及接受状态。即使被拒绝，该事件仍会被追加。


<details>
<summary>英文原文</summary>

Every registered cell begins from the method-specific frozen revision and the same task contract. The runner records the initial artifact and verifier result before model interaction. At intervention $t$ , the method receives only the public task view and the information permitted by its variant. A proposal must parse into the expected schema and stay within the editable surface. Candidate execution then records correctness, objective value, resource use, and any task-specific challenge. EPOCH additionally records evidence references, falsifier outcome, phase, and admission status. The event is appended even when rejected.

</details>

端点替换与提案评估是分开进行的。如果正确性或其他必要条件未满足，较高的公开得分无法替代已验证的现有端点。在预算边界处，运行器会对选中的端点及其证据根进行序列化处理。计划中的重放会以干净的过程精确重建这种序列化结果。重放结果与搜索记录相关联，但不会重新编写该记录。这一生命周期也解释了哪些部分被移除：每次移除都改变了提案或接纳接口的某个声明部分，而并非只是在分析过程中隐藏某列数据。


<details>
<summary>英文原文</summary>

Endpoint replacement is separate from proposal evaluation. A higher public score cannot replace a verified incumbent if correctness or another required gate fails. At the budget boundary, the runner serializes the selected endpoint and its evidence root. Scheduled replay reconstructs precisely this serialization in a clean process. The replay result is linked to, but does not rewrite, the search record. This lifecycle also explains the ablations: each removal changes a declared part of the proposal or admission interface, rather than merely hiding a column during analysis.

</details>

### C.2 AlgoTune与Math14的评估细节


<details>
<summary>英文原文</summary>

C.2 Evaluation Details for AlgoTune and Math14

</details>

对于每个公开的 AlgoTune 实例，在计时之前先进行正确性评估。计时是在一次预热运行后使用全新进程进行的，并根据基准测试的固定评估器对三次测量结果进行汇总。任务级指标是通过首先对三个已注册的种子进行平均计算得出的，之后所有任务均获得相同的权重。


<details>
<summary>英文原文</summary>

For each public AlgoTune instance, correctness is evaluated before timing. Timing is measured in a fresh process after one warmup run and aggregated across three measured repetitions according to the benchmark’s frozen evaluator. Task-level means are computed by first averaging the three registered seeds, after which all tasks receive equal weight.

</details>

Math14 报告了每个目标特定评估器返回的项目归一化端点得分。验证状态与方法失败是分开记录的：即使方法失败，仍可能保留任务定义的备用得分。


<details>
<summary>英文原文</summary>

Math14 reports the project-normalized endpoint score returned by each objective-specific evaluator. Verification status is recorded separately from method failure: a failed method may still retain a task-defined fallback score.

</details>

### C.3 智能体 HPO 评估细节


<details>
<summary>英文原文</summary>

C.3 AgentHPO evaluation details

</details>

AgentHPO 保留了原始任务单元：胜率与准确率得到最大化，而均方误差（MAE）、均方误差（MSE）和均方根误差（RMSE）则被最小化。注册的配对报告对每种“完整 vs 移除”差异进行了定位，使得正结果优先于完整 EPOCH，在冻结平局规则下则收敛至特定任务方向，并在非平局任务中采用精确的双侧符号检验。


<details>
<summary>英文原文</summary>

AgentHPO preserves raw task units: win rate and accuracy are maximized, whereas MAE, MSE, and RMSE are minimized. The registered paired report orients each full-versus-removal difference so that positive favors full EPOCH, collapses to a task direction under its frozen tie rule, and applies an exact two-sided sign test across non-tied tasks.

</details>

行为诊断是根据追踪事件而非端点得分来计算的。证据引用率用于判断某个决策是否引用了非基准先前的事件；重复配置率用于判断输出的配置是否与基准配置或同一单元中的早期配置完全一致；拒绝率记录为 admitted=false。另一种宏观报告则对每个任务进行汇总，然后对六个任务进行平均计算。


<details>
<summary>英文原文</summary>

Behavior diagnostics are computed from trace events rather than endpoint scores. Evidence-reference rate asks whether a decision cites a nonbaseline prior event; duplicate-configuration rate asks whether the emitted configuration exactly matches the baseline or an earlier configuration in the same cell; rejection rate records admitted=false . The alternative macro report aggregates within each task and then averages six tasks equally.

</details>

## 附录 D 详细架构与证据协议


<details>
<summary>英文原文</summary>

Appendix D Detailed Architecture and Evidence Protocol

</details>

本部分将主文本合同转化为协议级操作。数学符号定义了需要保留和验证的量值，而实现细节则明确了架构通过何种具体设置来维护其不变量。


<details>
<summary>英文原文</summary>

This section translates the main-text contract into protocol-level operations. The mathematical notation defines the quantities to preserve and verify, while the implementation details specify the concrete settings through which the architecture enforces its invariants.

</details>

### D.1 研究任务作为可执行的合同


<details>
<summary>英文原文</summary>

D.1 The research task as an executable contract

</details>

任务不仅仅是一个目标函数，它还指定了初始产物、可编辑范围、允许的观察结果、正确性条件、资源限制以及终点规则。对于代码任务而言，该产物可能是一个具有固定输入/输出接口的函数的 Python 实现；对于张量任务，则可能是一组一阶路径的列表以及一个目标坐标生成器；对于数学陈述，则包括相关假设以及用于证明结论的任何有限或形式化证据的含义。如果没有这种周边约束，高分数仅能适用于修改问题，而无法真正解决问题。


<details>
<summary>英文原文</summary>

A task is more than an objective function. It specifies an initial artifact, editable scope, allowed observations, correctness conditions, resource limits, and an endpoint rule. For a code task, the artifact may be a Python implementation of a function with a fixed input/output interface. For a tensor task, it may be a list of rank-one paths and a target-coordinate generator. For a mathematical statement, it includes the hypotheses and the meaning of any finite or formal evidence used to justify the conclusion. Without this surrounding contract, a high score is compatible with changing the problem rather than solving it.

</details>

公众视角和终端视角具有不同的作用。公共实例可以影响提案的生成过程。终端视角只能在指定的协议下对选定的端点进行评估。如果使用官方测试反馈来生成新的候选方案，那么该候选方案属于新的搜索实验；并非原始端点的重复调用。同样，证书验证器在搜索过程中可能会明确指出失败坐标，而保留的基准评估则不得默默成为额外的优化循环。


<details>
<summary>英文原文</summary>

The public view and terminal view have different roles. Public instances can influence proposal generation. A terminal view can evaluate the selected endpoint only under the declared protocol. If official test feedback is used to generate a new candidate, that candidate belongs to a new search experiment; it is not the original endpoint’s replay. Similarly, a certificate verifier may expose a precise failed coordinate during search, whereas a held-out benchmark evaluation must not silently become an additional optimization loop.

</details>

资源包同时具有会计和归属语义。候选执行会消耗任务资源；提案生成则会消耗语义调用及相关模型资源。如果某个候选方案超出了有效的注册时间限制，则违反了方法契约。由于所需设备不可用而无法启动的评估器则会产生不同的状态。在决定该单元是否有得分或采用回退方案之前，实验必须确定是哪一方出现了问题。当比较具有不同调度模式的方法时，这种区别尤为重要。


<details>
<summary>英文原文</summary>

A resource envelope has both accounting and attribution semantics. Candidate execution consumes task resources; proposal generation consumes semantic calls and associated model resources. A candidate that exceeds a valid registered time limit has failed within the method contract. An evaluator that cannot launch because a required device is unavailable creates a different state. The experiment must identify which boundary failed before deciding whether the cell has a score, or a fallback. This distinction is particularly consequential when comparing methods with different orchestration patterns.

</details>

### D.2 证据记录与生成过程中暴露的信息


<details>
<summary>英文原文</summary>

D.2 Evidence records and information exposed to generation

</details>

该事件应独立于模型的叙述进行解释。它能明确指出具体的可执行或符号化候选方案、评估版本以及输入版本；度量指标和正确性字段则记录不同的结果；而归因说明为何该结果可以使用或不可使用。证据引用指向这一不可改变的事件，而非像“之前的尝试有效”这样的可变的自然语言表述。因此，后续声明可以追溯到特定的观察结果，而无需在论文中列出存储层面的标识符。


<details>
<summary>英文原文</summary>

An event should be interpretable independently of the model’s narrative. It identifies the exact executable or symbolic candidate, evaluator version, and input version; metric and correctness fields record different outcomes; and attribution explains why the result can or cannot be used. An evidence reference points to this immutable event, not to a mutable natural-language statement such as “the previous attempt worked.” A subsequent claim can therefore be traced back to a specific observation without printing storage-level identifiers in the paper.

</details>

有限内存视图是对更长的证据历史的一种投影。这种投影可以包含成功的尝试、被拒绝的提议、基准观测结果以及相关的反例，而无需完整再现整个记录。这一区别很重要，因为上下文窗口摘要可能会遗漏某些细节，而底层记录却仍保留这些细节。该架构的可审计性主张涉及完整记录的保存与稳定标识符的保留，而非声称模型总是能接收到所有历史事件。


<details>
<summary>英文原文</summary>

The bounded memory view is a projection of a longer evidence history. A projection can contain successful trials, rejected proposals, baseline observations, and relevant counterexamples without reproducing an entire transcript. This distinction matters because a context-window summary may omit details while the underlying record still retains them. The architecture’s auditability claim concerns preservation of the full record and stable identifiers, not an assertion that the model always receives every historical event.

</details>

一个有效的提案至少包含四个可解释的组成部分。其假设描述了旨在实现目标改进的机制；预期效果指明了方向或可观察到的变化；证据引用则指出了支持该干预措施的早期观察结果；反证则明确了应拒绝该机制的条件。例如，更快速的卷积实现可能会在矩形形状上预测出相同的零填充线性卷积；即使时序有所改善，环绕不匹配仍属于反证。代数提升可能预测出特定的系数关系；而单一语义坐标的不匹配则反驳了该提案。


<details>
<summary>英文原文</summary>

A useful proposal has at least four interpretable parts. Its hypothesis describes the mechanism intended to improve the objective. Its expected effect states the direction or observable change. Its evidence references identify earlier observations supporting the intervention. Its falsifier specifies a condition under which the mechanism should be rejected. For example, a faster convolution implementation may predict identical zero-padded linear convolution on rectangular shapes; a wraparound mismatch is a falsifier even when timing improves. An algebraic lift may predict a specified coefficient identity; a single mismatching semantic coordinate refutes that proposal.

</details>

证据即使不是积极的也能发挥作用。张量图障碍会排除整个局部表示。边界输入失败则能揭示优化过程中遗漏了哪些不变性。修复后的解析器事件可以解释为何某种方法看似无法产生候选解。这些观察结果应被归类为不同的类型，因为它们意味着不同的后续操作。若将所有内容都视为低奖励，则既会丢失科学信息，也会失去对评估过程本身进行诊断的能力。


<details>
<summary>英文原文</summary>

Evidence can be useful without being positive. A tensor-chart obstruction excludes an entire local representation. A failure at a boundary input shows which invariant an optimization omitted. A repaired parser incident explains why a method appeared to produce no candidates. These observations should be stored with different types because they imply different next actions. Treating them all as low rewards loses both scientific information and the ability to diagnose the evaluation itself.

</details>

### D.3 作为三值决策模型的认可


<details>
<summary>英文原文</summary>

D.3 Admission as a three-valued decision

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0205)

图 S2：EPOCH的三值准入门限。通过的提案会增加经验证的收益；失败的提案则保留现有的主导者，并贡献一个反驳证据；未解决的检查则将该声明保持为待处理状态。这种分离机制使 EPOCH能够从不利证据中学习，同时保护已验证的结果。


<details>
<summary>英文原文</summary>

Figure S2: EPOCH’s three-valued admission gate. Passing proposals add verified gains; failed proposals retain the correct incumbent and contribute a falsifier; unresolved checks preserve the claim as pending. This separation lets EPOCH learn from adverse evidence while protecting an already verified endpoint.

</details>

图 S2 明确了这三个结果。保留率取决于相关门控的组合，而非其状态的数值平均值。


<details>
<summary>英文原文</summary>

Figure S2 makes the three outcomes explicit. Retention depends on the conjunction of the applicable gates, not a numerical average of their statuses.

</details>

对于每一个适用的门控 $g$ ，需写出 $g(c)\in\{\mathsf{pass},\mathsf{fail},\mathsf{unresolved}\}$ 。只有当所有要求的门控均通过时，合取才视为通过。任何被证明的契约违反情况将导致录取失败。若基础设施事件导致必要的检查无法进行，则录取问题将无法解决；这既不能证明候选正确性，也不能证明候选错误性。这为主文本录取谓词提供了操作形式。


<details>
<summary>英文原文</summary>

For each applicable gate $g$ , write $g(c)\in\{\mathsf{pass},\mathsf{fail},\mathsf{unresolved}\}$ . Conjunction passes only if every required gate passes. Any demonstrated contract violation fails admission. An infrastructure incident that prevents a required check leaves admission unresolved; it does not establish either candidate correctness or candidate incorrectness. This gives an operational form to the main-text admission predicate.

</details>

这些门控在逻辑上具有异质性。解析检查所提出的实体是否可以被理解。范围检查确保变更仍属于任务范畴。预算检查强制执行候选者的资源约束。正确性检查任务语义是否符合要求。挑战测试所声明的弱点或不利情况。重放检查所选对象的可复现性。


<details>
<summary>英文原文</summary>

The gates are logically heterogeneous. Parsing checks that the proposed artifact can be interpreted. Scope checks that changes remain within the task. Budget checks enforce the candidate’s resource contract. Correctness checks the task semantics. Challenges test declared weak points or adverse cases. Replay checks reproducibility of the selected object.

</details>

一个基准搜索端点和一个定理陈述可能需要不同的最终验证条件。代码端点可以在已注册的验证实例上被认定为正确，但未必能在所有输入下都被视为普遍正确。通过符号方式检验的多项式恒等式可以支持其代数假设所涵盖的所有数值。针对 1,600 个坐标的有限证书可以支持整个有限张量恒等式，因为这些坐标涵盖了目标对象。相同数量的采样随机矩阵则具有不同的证据意义。


<details>
<summary>英文原文</summary>

A benchmark search endpoint and a theorem statement may require different final gates. A code endpoint can be admitted as correct on the registered validation instances without being admitted as universally correct on all inputs. A polynomial identity checked symbolically can support all values covered by its algebraic hypotheses. A finite certificate for 1,600 coordinates can support the whole finite tensor identity because those coordinates span the target object. The same number of sampled random matrices would have a different evidential meaning.

</details>

因此，证明接纳中的“proof”一词指的是所需的论证，而非某种证明技术。Lean 收据可以是一个非常强大的终端对象，但前提是正式陈述已与具体的候选者和任务相关联。相反，一个完备的可执行验证器可以在没有 Lean 翻译的情况下完全确立一个有限属性。


<details>
<summary>英文原文</summary>

The word “proof” in proof admission therefore refers to the required justification, not to one proof technology. A Lean receipt can be a very strong terminal object, but only if the formal statement has been connected to the concrete candidate and task. Conversely, an exhaustive executable verifier can completely establish a finite property without a Lean translation.

</details>

### D.4 协议级发现循环


<details>
<summary>英文原文</summary>

D.4 Protocol-level discovery loop

</details>

以下伪代码展示了决策顺序，并未添加未记录的搜索启发式方法。


<details>
<summary>英文原文</summary>

The following pseudocode exposes the sequence of decisions without adding an unreported search heuristic.

</details>

输入：冻结合同、提供的初始验证备用方案、资源账本以及空的仅追加试验历史记录。初始化操作：记录基准数据、其验证凭证及资源使用情况。在允许干预的情况下：使用已注册的控制器选择当前阶段。构建有限证据视图并提交提案。验证其架构、可编辑范围及所需证据字段。评估正确性、目标及适用挑战。在决定得分资格前标注失败原因。将候选方案、观察结果及门限理由添加到历史记录中。仅在接纳及比较规则允许时替换端点。
最终确认：重新构建并重复执行所选的具体内容。签署：明确最终声明、范围、合同、历史记录及重复执行凭证。


<details>
<summary>英文原文</summary>

Input: frozen contract, initial verified fallback when supplied, resource ledger, and empty append-only trial history. Initialize: record the baseline, its verification receipt, and its resource use. While an intervention remains allowed: Choose the current phase using the registered controller. Construct the bounded evidence view and request a proposal. Validate its schema, editable scope, and required evidence fields. Evaluate correctness, objective, and the applicable challenge. Attribute failures before deciding score eligibility. Append the candidate, observations, and gate reasons to history. Replace the endpoint only if admission and the comparison rule permit. Finalize: reconstruct and replay the exact selected artifact. Seal: bind the final claim, scope, contract, history, and replay receipts.

</details>

伪代码刻意将评估者的观察结果与端点替换区分开来。某个候选方案虽然具有信息价值，却仍不符合替换的资格。


<details>
<summary>英文原文</summary>

The pseudocode deliberately separates evaluator observations from endpoint replacement. A candidate can be informative and still be ineligible for replacement.

</details>

### D.5 端点安全与来源不变性


<details>
<summary>英文原文</summary>

D.5 Endpoint safety and provenance invariants

</details>

假设基准值根据合同 $\mathcal{C}$ 得到验证，且每次端点替换都需要所有相关条件均满足。根据干预次数的归纳推理，保留的端点始终在该合同下拥有有效的确认记录。在基础步骤中，这就是已注册的基准值。在后续步骤中，失败的或未解决的候选方案不会替代它，而被认可的替换方案则拥有自己的确认记录。这种不变性解释了为何具有误导性的公开得分不必破坏端点的准确性。


<details>
<summary>英文原文</summary>

Suppose the baseline is verified under contract $\mathcal{C}$ and every endpoint replacement requires all applicable gates to pass. By induction on the number of interventions, the retained endpoint always has a passing receipt under that contract. At the base step this is the registered baseline. At a later step, a failed or unresolved candidate does not replace it, while an admitted replacement has its own passing receipt. This invariant explains why a misleading public score need not corrupt the endpoint.

</details>

该不变性具有有意的相对性。如果正确性检查器遗漏了某类输入，即使通过的端点在其注册的覆盖范围内表现良好，也可能在外部环境中失败。如果检查器本身存在错误，该不变性所保证的是协议合规性，而非外部事实。正因如此，该产物必须保留评估者的身份，且独立的语义重构能够提供超出重复执行同一检查器所能获得的信息。


<details>
<summary>英文原文</summary>

The invariant is intentionally relative. If the correctness checker misses a class of inputs, a passing endpoint may still fail outside its registered coverage. If the checker itself is wrong, the invariant establishes protocol compliance rather than external truth. This is why the artifact must preserve the evaluator identity and why independent semantic reconstruction provides information beyond repeated execution of the same checker.

</details>

仅可追加的历史记录带来了第二个不变量。新事件将历史从 $M_{t}$ 扩展至 $(M_{t},e_{t+1})$；它不会改变早期事件的候选对象或归属。


<details>
<summary>英文原文</summary>

Append-only history gives a second invariant. A new event extends the history from $M_{t}$ to $(M_{t},e_{t+1})$ ; it does not change the candidate or attribution of earlier events.

</details>

声明密封仅增加了一个约束性不变式，而非正确性定理。如果候选者、评估器、输入或声明文本发生变化，存档记录必须生成一个独立的版本。这一版本化规则并不验证任何定理；它仅确保记录不会悄然转移到其他声明或工件上。


<details>
<summary>英文原文</summary>

Claim sealing adds a binding invariant rather than a theorem of correctness. If the candidate, evaluator, inputs, or claim text changes, the archival record must create a distinct version. This versioning rule does not validate a theorem; it only ensures that a receipt cannot silently migrate to a different claim or artifact.

</details>

### D.6 证伪、重复及阶段变化


<details>
<summary>英文原文</summary>

D.6 Falsification, duplicates, and phase changes

</details>

重复配置可能表明有意义的复现、偶然的重复，或未能纳入证据。AgentHPO追踪指标统计与先前发射配置的相同情况，但本身无法区分这些原因。因此，较低的重复率是一种操作信号，而非科学效率的独立衡量标准。在确定性陷阱中，预期的重复行为由设计决定；而在外部任务中，终点结果才是解读该行为的必要依据。


<details>
<summary>英文原文</summary>

A repeated configuration can indicate useful replication, accidental repetition, or a failure to incorporate evidence. The AgentHPO trace metric counts equality with an earlier emitted configuration; it does not by itself distinguish those motivations. Consequently, a lower repetition rate is an operational signal, not a standalone measure of scientific efficiency. In the deterministic traps, the intended repeated behavior is specified by construction; in external tasks, endpoint outcomes remain necessary to interpret it.

</details>

验证者与常规正确性测试的不同之处在于其针对的是提案的机制。因子共享提案必须保持 ANF 覆盖性并返回辅助信息；证书压缩提案必须保留所有所表示的案例；推测的不等式必须在退化和等式情形下仍然成立。同样的挑战既能发现科学缺陷，也能为下一个提案提供有用的输入。


<details>
<summary>英文原文</summary>

A falsifier differs from an ordinary correctness test by being directed at the proposal’s mechanism. A factor-sharing proposal must preserve ANF coverage and return ancillas; a certificate compression proposal must preserve all represented cases; a conjectured inequality must survive degenerate and equality regimes. The same challenge can discover a scientific failure and produce a useful input for the next proposal.

</details>

阶段变化决定了这些观察结果如何影响搜索过程。探索阶段会寻求截然不同的假设。优化阶段则致力于支持这些假设的机制。最终阶段会停止搜索，转而专注于重放和声明范围。


<details>
<summary>英文原文</summary>

Phase changes organize how these observations affect search. Exploration seeks materially different hypotheses. Refinement invests in supported mechanisms. Finalization stops search and concentrates on replay and claim scope.

</details>

### D.7 独立重放与可信边界


<details>
<summary>英文原文</summary>

D.7 Independent replay and trusted boundaries

</details>

重放独立性包含多个层次。过程独立性能够以纯净的过程重新构建相同的候选对象。实现独立性则使用其他程序来重建数学或可执行目标。表示独立性采用不同的计算模型，例如乘法矩阵范数与结果阵，或者一种不可约有限域模型与另一种模型。形式化反思则将选定的有限条件纳入证明助手中。这些层次可以是互补的，而非可互换的。


<details>
<summary>英文原文</summary>

Replay independence has several levels. Process independence reconstructs the same candidate in a clean process. Implementation independence reconstructs the mathematical or executable target using another program. Representation independence uses a different computational model, such as multiplication-matrix norms versus resultants, or one irreducible finite-field model versus another. Formal reflection moves selected finite checks into a proof assistant. These levels can be complementary rather than interchangeable.

</details>

强大的重放包使得接口清晰明确：具体的输入对象、输出语句、不变的约束条件、失败代码以及资源边界。例如，QASM真值表重放会检查生成的电路；它不会验证优化器的全局最小性声明。Lean行列式核会证明由特征多项式假设所推导出的命题；但它并不提供表示论假设。穷举图目录遍历会验证所有列出的记录；但它无法证明该目录包含所有可能的图。


<details>
<summary>英文原文</summary>

A strong replay package makes the interfaces explicit: exact input object, output statement, invariant checked, failure code, and resource boundary. For example, a QASM truth-table replay checks an emitted circuit; it does not verify the optimizer’s claim of global minimality. A Lean determinant kernel proves an implication from a characteristic-polynomial hypothesis; it does not supply the representation-theoretic hypothesis. An exhaustive graph-catalogue pass verifies every listed record; it does not prove the catalogue contains every possible graph.

</details>

这种分层视角也是补充目录的阅读方式。每个条目都明确指出了数学对象及最有力的保留陈述，并区分了构造性分析、穷尽性有限检验、解析论证以及形式核心内容。那些在局部上已完备但在全局上尚未解决的结果，在其边界得到保留时仍具有实用价值。


<details>
<summary>英文原文</summary>

This layered view is also how the supplementary catalogue should be read. Each entry identifies the mathematical object and the strongest retained statement, then distinguishes construction, exhaustive finite checks, analytic arguments, and formal kernels. Results that are locally complete but globally unresolved remain useful evidence when their boundary is preserved.

</details>

## 附录 E：AlgoTune 性能提升背后的工程终点


<details>
<summary>英文原文</summary>

Appendix E Engineering Endpoints Behind the AlgoTune Gains

</details>

这些案例将基准性能提升与可实施的机制联系起来。它们未被计入四个新的算法发现候选方案中，因为核心数值和图算法属于成熟技术。它们的作用在于表明高公开得分对应着可识别的任务解决策略，并记录用于验证这些策略的控制方法。


<details>
<summary>英文原文</summary>

These cases connect benchmark gains to executable mechanisms. They are not counted among the four new algorithmic discovery candidates, because the core numerical and graph algorithms are established techniques. Their role is to show that high public scores correspond to recognizable task-solving strategies and to document the controls used to check them.

</details>

### E.1 Convolve2D：通用零填充实 FFT


<details>
<summary>英文原文</summary>

E.1 Convolve2D: generic zero-padded real FFT

</details>

保留的 Convolve2D 端点通过通用的零填充实 FFT 卷积来替代相关的直接计算。零填充必须避免循环混叠，且输出切片必须与任务的形状约定一致。即使转换速度更快且能返回包裹或偏移的结果，如果无法满足语义契约，则仍会失败。


<details>
<summary>英文原文</summary>

The retained Convolve2D endpoint replaces the relevant direct computation with a generic zero-padded real FFT convolution. Zero padding must prevent circular aliasing, and the output slice must match the task’s shape convention. A faster transform that returns a wrapped or shifted result would fail the semantic contract even if its timing is favorable.

</details>

提供的审计记录显示了六种形状控制机制及低于 $9\times 10^{-16}$ 的相应误差值。公开得分从 0.5 提升至 1.0。这些检查能够支持测试中的形状家族和数值容差相关的注册端点；它们并未使 FFT 卷积成为一种新算法。AdaEvolve 后来也提出了一种简洁的通用解决方案，完整的开发表中包含与 AdaEvolve 相类似的 Convolve2D 功能。在提供的任务效果表中，针对该基准线的官方重放优势相应地为零。


<details>
<summary>英文原文</summary>

The supplied audit records six shape controls and relative error below $9\times 10^{-16}$ . The public score moves from 0.5 to 1.0. These checks support the registered endpoint on the tested shape family and numerical tolerance; they do not make FFT convolution a new algorithm. AdaEvolve also later produced a clean generic solution, and the complete development table has a Convolve2D tie with AdaEvolve. The official-replay advantage against that baseline is correspondingly zero in the supplied task-effect table.

</details>

### E.2 Robertson 常微分方程：选择合适的刚性求解器


<details>
<summary>英文原文</summary>

E.2 Robertson ODE: selecting an appropriate stiff solver

</details>

Robertson 端点使用具有任务适配容差限制的 LSODA 算法。其机制是针对刚性系统选择求解器与容差参数，而非发明新的积分方法。正确性取决于与任务要求的解精度及守恒行为是否一致，而不仅仅取决于能否更快地返回轨迹。


<details>
<summary>英文原文</summary>

The Robertson endpoint uses LSODA with task-appropriate tolerances. The mechanism is solver and tolerance selection for the stiff system, rather than invention of a new integration method. Correctness depends on agreement with the task’s solution accuracy and conservation behavior, not merely on returning a trajectory more quickly.

</details>

六个速率/时间范围控制参数显示总误差低于 $2\times 10^{-12}$，最大误差低于 $7.2\times 10^{-8}$。公开得分从 0.5 提升至 1.0。


<details>
<summary>英文原文</summary>

Six rate/time-horizon controls report mass error below $2\times 10^{-12}$ and maximum error below $7.2\times 10^{-8}$ . The public score moves from 0.5 to 1.0.

</details>

### E.3 最大公共子图：关联图与位集团搜索


<details>
<summary>英文原文</summary>

E.3 Maximum common subgraph: association graph and bitset clique search

</details>

保留的实现方案通过关联图实现了兼容的顶点匹配，并利用位集运算解决了相应的团问题。关键性的正确性接口在于团与有效公共子图映射之间的对应关系：邻接性和注入性限制必须与原始任务要求一致。基于已建立的关联图与 Bron–Kerbosch 理论，该算法基础得以确立。


<details>
<summary>英文原文</summary>

The retained implementation represents compatible vertex matches through an association graph and solves the corresponding clique problem with bitset operations. The correctness-critical interface is the correspondence between cliques and valid common-subgraph mappings: adjacency and injectivity restrictions must agree with the original task. Established association-graph and Bron–Kerbosch ideas supply the algorithmic basis.

</details>

提供的独立验证包括 145 次针对尺寸为 8 的情况的最佳比较实验。公开得分从 0.5 的基础值提升至 1.0，且官方重放在所有基准情况下都保持了显著的积极任务效果。这些证据支持在基准协议下所采用的实现方案是有效的。


<details>
<summary>英文原文</summary>

The supplied independent checks include 145 optimum comparisons through size eight. The public score reaches 1.0 from a 0.5 baseline, and official replay retains a large positive task effect against every baseline. The evidence supports a successful implementation choice under the benchmark contract.

</details>

### E.4 NMF与zeta-零计数：任务特定优化的适用范围


<details>
<summary>英文原文</summary>

E.4 NMF and zeta-zero count: scope of task-specific optimization

</details>

NMF的开发平均值为0.70，而zeta-zero计数的平均值为0.68。它们经过评估者检验的分数以任务级别呈现，有助于EPOCH在整体发展方面取得优异成绩。


<details>
<summary>英文原文</summary>

NMF has development mean 0.70, while zeta-zero count has mean 0.68. Their evaluator-checked scores are reported at the task level and contribute to EPOCH’s strong aggregate development result.

</details>

## 附录 F AlgoTune 开发与官方回放


<details>
<summary>英文原文</summary>

Appendix F AlgoTune Development and Official Replay

</details>

### F.1 开发覆盖度与综合效果


<details>
<summary>英文原文</summary>

F.1 Development Coverage and Aggregate Effects

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0243)

表 S3 总结了完整的开发矩阵。每种方法贡献了 36 个评估单元，对应十二项任务和三个已注册种子。EPOCH 获得了最高的平均归一化分数，为 0.65，而最强大的基线模型仅为 0.53。


<details>
<summary>英文原文</summary>

Table S3 summarizes the complete development matrix. Each method contributes 36 evaluated cells, corresponding to twelve tasks and three registered seeds. EPOCH achieves the highest mean normalized score, 0.65, compared with 0.53 for the strongest baseline.

</details>

表 S3：完整的描述性开发覆盖情况。


<details>
<summary>英文原文</summary>

Table S3: Complete descriptive development coverage.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0246)

表 S4 区分了所提供的原始报告效果与基于完整开发矩阵计算出的效果。在两种汇总结果中，EPOCH 对每一个基线均具有正向平均效应。胜/平/负情况进一步表明，总体优势因任务不同而有所差异，并非源于统一的改进。


<details>
<summary>英文原文</summary>

Table S4 distinguishes the supplied original reported effects from effects computed over the complete development matrix. EPOCH has a positive mean effect against every baseline under both summaries. The win/tie/loss profiles further indicate that the aggregate advantage varies across tasks rather than arising from a uniform improvement.

</details>

表 S4：不同的 AlgoTune 开发总结。原始报告的效果数据来自另一组样本的汇总结果，而完整的开发效果以及胜/平/负次数则基于整个开发矩阵进行计算。


<details>
<summary>英文原文</summary>

Table S4: Distinct AlgoTune development summaries. Original reported effects are supplied aggregates from a separate cohort, whereas complete development effects and win/tie/loss counts are computed over the complete development matrix.

</details>

### F.2 官方重放任务效果


<details>
<summary>英文原文</summary>

F.2 Official-Replay Task Effects

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0250)

图 S3展示了所研究的任务级官方重放效果。EPOCH在最大公共子图和Convolve2D任务上获得了最大的可迁移收益，并且在特征值计算方面也表现出一致的积极效果。这些收益超过了对NMF的负面影响，使得相对于所有基线模型而言，均呈现出积极的平均重放效果。由此得出的结果表明，存在显著的任务特定改进，而非所有任务都出现统一的变化。


<details>
<summary>英文原文</summary>

Figure S3 presents the reported task-level official-replay effects. EPOCH achieves its largest transferable gains on maximum common subgraph and Convolve2D, together with consistent positive effects on eigenvalue computation. These gains outweigh the reversal on NMF, yielding a positive mean replay effect against every baseline. The resulting profile reflects substantial task-specific improvements rather than a uniform shift across all tasks.

</details>

图 S3：使用原始冻结端点所报告的官方重放任务效果。每个数值均为 EPOCH 得分减去对应基线得分的结果，保留三位小数；带符号零则保留达到零时的效果方向。最大的增益出现在最大公共子图和 Convolve2D 上，而 NMF 则表现出一致的反向变化。


<details>
<summary>英文原文</summary>

Figure S3: Reported official-replay task effects using the original frozen endpoints. Each value is the score of EPOCH minus that of the corresponding baseline, rounded to three decimal places; signed zeros preserve the direction of effects that round to zero. The largest gains occur on maximum common subgraph and Convolve2D, while NMF exhibits a consistent reversal.

</details>

## 附录 G Math14 评估与迁移


<details>
<summary>英文原文</summary>

Appendix G Math14 Evaluation and Transfer

</details>

Math14是一个项目冻结的套件，包含十四项数学目标，通过五种方法和三种注册种子进行评估，最终形成了一种平衡的$14\times 5\times 3=210$细胞结构。每个目标都通过其任务特定的评估器来报告项目归一化的终点得分。


<details>
<summary>英文原文</summary>

Math14 is a project-frozen suite of fourteen mathematical objectives evaluated across five methods and three registered seeds, yielding a balanced design of $14\times 5\times 3=210$ cells. Each objective reports a project-normalized endpoint score through its task-specific evaluator.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0255)

表 S5：Math14 综合结果。


<details>
<summary>英文原文</summary>

Table S5: Aggregate Math14 results.

</details>

EPOCH获得了最高的Math14综合得分，平均值为0.57。其两两对战结果分别为：对AI-Scientist v1为7胜4平3负，对AI-Scientist v2为7胜5平2负，对OpenEvolve为4胜3平7负，对AdaEvolve为5胜3平6负。尽管任务层面的对比结果参差不齐，但EPOCH在多个目标上的较大优势使其整体平均值最为突出。下面的发现成果列表展示了支撑这些已记录结果的具体构造、反例、简化证明及推导过程。


<details>
<summary>英文原文</summary>

EPOCH achieves the highest aggregate Math14 score, with a mean of 0.57. Its pairwise win/tie/loss records are 7/4/3 against AI-Scientist v1, 7/5/2 against AI-Scientist v2, 4/3/7 against OpenEvolve, and 5/3/6 against AdaEvolve. Although the task-level comparisons are mixed, EPOCH’s larger gains on several objectives produce the strongest overall mean. The discovery portfolio below presents the exact constructions, counterexamples, reductions, and proofs underlying documented outcomes.

</details>

## 附录 H 智能体 HP O 的消融与机制行为研究


<details>
<summary>英文原文</summary>

Appendix H AgentHPO Ablation and Mechanism Behavior

</details>

### H.1 剔除实验结果


<details>
<summary>英文原文</summary>

H.1 Ablation Results

</details>

所报道的 AgentHPO分析涵盖了整个系统及其四种组件移除变体的六项任务。


<details>
<summary>英文原文</summary>

The reported AgentHPO analysis covers six tasks across the full system and its four component-removal variants.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0261)

表 S6：原生任务指标的任务级均值。Full、M、F、P 和 C 分别表示完整周期、无内存、无伪造样本、无证据接受以及无阶段控制器。MAE、MSE 和 RMSE 分别表示平均绝对误差、均方误差和均方根误差。


<details>
<summary>英文原文</summary>

Table S6: Task-level means on the native task metrics. Full, M, F, P, and C denote full EPOCH , no memory, no falsifier, no proof admission, and no phase controller, respectively. MAE, MSE, and RMSE denote mean absolute error, mean squared error, and root mean squared error.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0263)

表 S7：完整系统与各组件移除变体的任务级对比结果。W/T/L 表示完整阶段中任务级的胜场数、平局数和负场数。


<details>
<summary>英文原文</summary>

Table S7: Paired task-level comparisons between the full system and each component-removal variant. W/T/L denotes the number of task-level wins, ties, and losses for full EPOCH .

</details>

整个系统在所有六个任务中均优于无证明接纳版本，在六个任务中的五个任务中则优于无相位控制器版本。此外，它在无记忆和无反证版本的两个任务类别中均取得了四项胜利。这些比较表明，证明接纳和相位控制是最具持续优势的组件，而记忆和反证的效果则在不同环境中差异较大。


<details>
<summary>英文原文</summary>

The full system outperforms the no-proof-admission variant on all six tasks and the no-phase-controller variant on five of six tasks. It also records four task-level wins against both the no-memory and no-falsifier variants. These comparisons identify proof admission and phase control as the most consistently beneficial components, while the effects of memory and falsification vary more strongly across environments.

</details>

### H.2 观测到的机制行为


<details>
<summary>英文原文</summary>

H.2 Observed Mechanism Behavior

</details>

基于先验证据的引用是一种决策，其evidence_refs中包含大于零的标识符，其中标识符零用于基准观测值。重复配置是指与基准或同一任务种子运行中的早期配置相同的新_config。接纳拒绝对应于admitted=false。


<details>
<summary>英文原文</summary>

A prior-evidence citation is a decision whose evidence_refs includes an identifier greater than zero, with identifier zero reserved for the baseline observation. A repeated configuration is a new_config identical to the baseline or to an earlier configuration within the same task-seed run. Admission rejection corresponds to admitted=false .

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0268)

表 S8：机制与行为的匹配比较。差异以百分比点（pp）表示，表现良好的任务表明与对应组件的预期行为一致。


<details>
<summary>英文原文</summary>

Table S8: Matched mechanism-behavior comparisons. Differences are reported in percentage points (pp), and favorable tasks indicate agreement with the intended behavior of the corresponding component.

</details>

记忆机制使先前证据的使用量增加了 37.50 个百分点。否定者、证明承认模块和阶段控制器分别减少了重复配置，而证明承认则在所有六个任务中均导致选择性拒绝。综合来看，这些模式表明这些组件既影响用于生成提案的信息，也影响控制其接受与推进的机制。


<details>
<summary>英文原文</summary>

Memory increases the use of prior evidence by 37.50 percentage points. The falsifier, proof-admission module, and phase controller each reduce repeated configurations, while proof admission introduces selective rejection across all six tasks. Together, these patterns show that the components influence both the information used to generate proposals and the mechanisms governing their acceptance and progression.

</details>

## 附录一 四个算法发现案例


<details>
<summary>英文原文</summary>

Appendix I Four Algorithmic Discovery Cases

</details>

以下是具有不同预算和验证层的已记录研究成果。边界秩记为 $\brank$，普通张量秩为 $R$，Waring 秩为 $R_{\mathrm{W}}$。一般构造仅在其证书所要求的领域、可逆性及非零分母条件下进行说明。外部记录优先级则属于另一个独立问题。


<details>
<summary>英文原文</summary>

The following are documented research outcomes with heterogeneous budgets and verification layers. Border rank is denoted $\brank$ , ordinary tensor rank $R$ , and Waring rank $R_{\mathrm{W}}$ . General constructions are stated only under the field, invertibility, and nonzero-denominator conditions required by their certificates. External record priority remains a separate question.

</details>

每个证明都以链条形式进行组织，而非单一的、无差异的“已验证”标签。以下小节分别介绍了相关方程、构造方法、穷举计数、篡改测试以及未解决的关联问题。它们的共同覆盖范围和剩余桥梁与数学案例一起在表 S9 中进行了总结。


<details>
<summary>英文原文</summary>

Each proof is organized as a chain rather than a single undifferentiated “verified” label. The following subsections give the equations, constructions, exhaustive counts, corruption tests, and unresolved links. Their common coverage and remaining bridges are summarized together with the mathematical cases in Table S9 .

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0274)

表 S9：跨案例证据覆盖情况与剩余定理桥梁。


<details>
<summary>英文原文</summary>

Table S9: Cross-case evidence coverage and remaining theorem bridges.

</details>

### I.1 反向2-算术传递与阻碍引导的Hasse提升


<details>
<summary>英文原文</summary>

I.1 Reverse 2-adic transfer and obstruction-guided Hasse lifting

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0277)

图 S4：基于证据引导的逆向传递过程。(a) 在每一个活跃的哈塞序列中，精确的线性求解要么安装一个射影子，要么返回一个可检验的共核障碍。因此，改变的图表可能会得到不同的解。(b) 提供的 ss444 证书具有系数支持权重 $(0,0,64,314,291,190,96)$。虚线将第二阶的验证目标系数与更高阶项分开。


<details>
<summary>英文原文</summary>

Figure S4: Reverse transfer as an evidence-guided construction. (a) At each active Hasse order, an exact linear solve either installs a jet or returns a checkable cokernel obstruction. A changed chart may then yield a different solve. (b) The supplied ss444 certificate has coefficient support weights $(0,0,64,314,291,190,96)$ . The dashed line separates the verified target coefficient at order two from higher-order terms.

</details>

图 S4 将代数控制回路与具体的系数分布联系起来。


<details>
<summary>英文原文</summary>

Figure S4 links the algebraic control loop to the concrete coefficient profile.

</details>

### 问题与机制。


<details>
<summary>英文原文</summary>

Problem and mechanism.

</details>

一种合理的秩 - $r$ 张量分解可能无法直接通过模2运算进行简化，因为其因子在分母中包含2的幂。假设清除第一模式的分母后，得到的因子为整数因子


<details>
<summary>英文原文</summary>

A rational rank- $r$ tensor decomposition can fail to reduce directly modulo two because its factors contain powers of two in their denominators. Suppose clearing the first-mode denominators gives integral factors satisfying

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0281)

**表格与文字对照**

```text
| $\sum_{q=1}^{r}A_{q}\otimes V_{q}\otimes W_{q}=2T.$ | | (S4)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
otimes V_ → 《otimes》V_
otimes W_ → 《otimes》W_
```


<details>
<summary>英文原文</summary>

| $\sum_{q=1}^{r}A_{q}\otimes V_{q}\otimes W_{q}=2T.$ | | (S4)

</details>

对 Segre 求和参数化进行模二运算后，会得到一个零纤维点 $p=((a_{q},b_{q},c_{q}))$。其微分为


<details>
<summary>英文原文</summary>

Reduction modulo two yields a zero-fiber point $p=((a_{q},b_{q},c_{q}))$ of the Segre-sum parametrization. Its differential is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0283)

**表格与文字对照**

```text
| $d\Phi_{p}(\dot{a},\dot{b},\dot{c})=\sum_{q}(\dot{a}_{q}\otimes b_{q}\otimes c_{q}+a_{q}\otimes\dot{b}_{q}\otimes c_{q}+a_{q}\otimes b_{q}\otimes\dot{c}_{q}).$ | | (S5)

表内文字对照（数值与原始行列保持不变）：
Phi_ → Phi_
dot → 点
sum_ → sum_
otimes b_ → otimes b_
otimes c_ → otimes c_
otimes → otimes
```


<details>
<summary>英文原文</summary>

| $d\Phi_{p}(\dot{a},\dot{b},\dot{c})=\sum_{q}(\dot{a}_{q}\otimes b_{q}\otimes c_{q}+a_{q}\otimes\dot{b}_{q}\otimes c_{q}+a_{q}\otimes b_{q}\otimes\dot{c}_{q}).$ | | (S5)

</details>

如果 $T\bmod 2$ 位于该图像中，则因子路径满足要求


<details>
<summary>英文原文</summary>

If $T\bmod 2$ lies in this image, the factor paths satisfy

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0285)

**表格与文字对照**

```text
| $\sum_{q}(a_{q}+\varepsilon\dot{a}_{q})\otimes(b_{q}+\varepsilon\dot{b}_{q})\otimes(c_{q}+\varepsilon\dot{c}_{q})=\varepsilon T\pmod{\varepsilon^{2}}.$ | | (S6)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
varepsilon → ε
dot → 点
otimes(b_ → otimes(b_
otimes(c_ → otimes(c_
varepsilon T → ε T
pmod → pmod
```


<details>
<summary>英文原文</summary>

| $\sum_{q}(a_{q}+\varepsilon\dot{a}_{q})\otimes(b_{q}+\varepsilon\dot{b}_{q})\otimes(c_{q}+\varepsilon\dot{c}_{q})=\varepsilon T\pmod{\varepsilon^{2}}.$ | | (S6)

</details>

扩展产品证明了这一断言，并给出了 $\brank_{\overline{\mathbb{F}}_{2}}(T)\leq r$。机械化核算子证明了交换环上的一阶展开。算术约简和具体张量绑定仍然是通用恒等式之外的明确要求。


<details>
<summary>英文原文</summary>

Expanding the product proves the assertion and gives $\brank_{\overline{\mathbb{F}}_{2}}(T)\leq r$ . A mechanized kernel proves the first-order expansion over a commutative ring. The arithmetic reduction and concrete tensor binding remain explicit obligations outside the generic identity.

</details>

### 高阶搜索。


<details>
<summary>英文原文</summary>

Higher-order search.

</details>

不同的赋值层次需要哈塞射。该算法会安装低阶系数，构建剩余的线性切线映射，并检验残差是否属于其像内。若失败则会产生一个具有 $\omega$ 的共核泛函 $\omega(\mathrm{residual})=1$，从而限制图表或支撑集的变换。所有保留的系数都会被完全重新使用。这样，一次失败的提升尝试就转化为一个可重复使用的代数障碍。


<details>
<summary>英文原文</summary>

Different valuation strata require Hasse jets. The algorithm installs lower-order coefficients, builds the remaining linear tangent map, and tests the residual for membership in its image. Failure produces a cokernel functional $\omega$ with $\omega(\mathrm{residual})=1$ , which constrains a change of chart or support. All retained coefficients are replayed exactly. This converts an unsuccessful lifting attempt into a reusable algebraic obstruction.

</details>

统一分母，并为每个项分配其激活高度。对于每种系数顺序，减去已由低层喷射器固定的贡献值。在可行的情况下求解精确的线性残差方程；否则保留一个分离共核证据并修改图表。完成喷射器构建后，在纳入之前重新计算所有系数和张量坐标。


<details>
<summary>英文原文</summary>

Clear denominators and assign each term its activation height. For each coefficient order, subtract contributions already fixed by lower jets. Solve the exact linear residual equation when feasible; otherwise retain a separating cokernel witness and revise the chart. After completing the jets, replay every coefficient and tensor coordinate before admission.

</details>

### 旗舰证书。


<details>
<summary>英文原文</summary>

Flagship certificate.

</details>

对于两个对称矩阵相乘的 $10\times 10\times 16$ 结构张量，有 30 条一阶多项式路径满足要求


<details>
<summary>英文原文</summary>

For the $10\times 10\times 16$ structure tensor of multiplying two symmetric $4\times 4$ matrices, 30 rank-one polynomial paths satisfy

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0292)

**表格与文字对照**

```text
| $\sum_{q=1}^{30}A_{q}(\varepsilon)\otimes B_{q}(\varepsilon)\otimes C_{q}(\varepsilon)=\varepsilon^{2}T_{\mathrm{ss444}}\pmod{\varepsilon^{3}}.$ | | (S7)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
varepsilon) → ε)
otimes B_ → 《otimes》B_
otimes C_ → 《otimes》C_
varepsilon → ε
mathrm → mathrm
pmod → pmod
```


<details>
<summary>英文原文</summary>

| $\sum_{q=1}^{30}A_{q}(\varepsilon)\otimes B_{q}(\varepsilon)\otimes C_{q}(\varepsilon)=\varepsilon^{2}T_{\mathrm{ss444}}\pmod{\varepsilon^{3}}.$ | | (S7)

</details>

赋值层的大小分别为 4/13/13。一阶映射的秩为 68，二阶系统的秩为 328。已知的二阶非线性贡献的权重为 234。截断系数权重为 $(0,0,64)$；完整多项式权重为 $(0,0,64,314,291,190,96)$。目标在 1,600 个环境坐标中包含 64 个非零坐标。自动化证书会检查所有环境坐标和语义目标，并拒绝损坏的因子数据。


<details>
<summary>英文原文</summary>

The valuation strata have sizes 4/13/13. The first-order map has rank 68 and the second-order system rank 328. The known second-order nonlinear contribution has weight 234. Truncated coefficient weights are $(0,0,64)$ ; full polynomial weights are $(0,0,64,314,291,190,96)$ . The target has 64 nonzero coordinates among 1,600 ambient coordinates. The mechanized certificate checks all ambient coordinates and the semantic target, and rejects corrupted factor data.

</details>

在 86 个扫描到的有理公式中，有 43 个可直接应用，且全部 43 个都能进行迁移，涉及 24 个坐标不同的目标以及 45,242 个独立重放的坐标。内部报告了 11 项严格的边界改进，包括 $\brank(T_{\mathrm{st444}})\leq 20$。分母为可应用的公式，并非所有扫描到的公式。Bini 插值方法给出了保留的标量计数上限


<details>
<summary>英文原文</summary>

Across 86 scanned rational formulas, 43 are directly applicable and all 43 transfer, spanning 24 coordinate-distinct targets and 45,242 independently replayed coordinates. Eleven strict border improvements are reported internally, including $\brank(T_{\mathrm{st444}})\leq 20$ . The denominator is applicable formulas, not all scanned formulas. Bini interpolation gives the retained scalar-count bound

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0295)

**表格与文字对照**

```text
| $R(T_{\mathrm{ss444}}^{\otimes N})\leq(4N+1)30^{N}.$ | | (S8)

表内文字对照（数值与原始行列保持不变）：
R(T_ → R(T_
mathrm → mathrm
otimes N → 《otimes》N
leq( → leq(
```


<details>
<summary>英文原文</summary>

| $R(T_{\mathrm{ss444}}^{\otimes N})\leq(4N+1)30^{N}.$ | | (S8)

</details>

该模型在 $32^{N}$ 阶段首先击败了 $N=92$；保留的扩展域下降模型在 $N=170$ 阶段产生交叉现象。这两个数值均不是运行时间基准测试。


<details>
<summary>英文原文</summary>

It first beats $32^{N}$ at $N=92$ in that model; the retained extension-field descent model gives a crossover at $N=170$ . Neither number is a runtime benchmark.

</details>

### I.1.1 系数级推导与阻碍证明


<details>
<summary>英文原文</summary>

I.1.1 Coefficient-level derivation and obstruction certificates

</details>

为便于理解，将三线性因子路径写作 $a(\varepsilon)=a_{0}+\varepsilon a_{1}+\varepsilon^{2}a_{2}+\cdots$，$b,c$ 同理。一维路径中 $k$ 阶的系数为


<details>
<summary>英文原文</summary>

For clarity, write a trilinear factor path as $a(\varepsilon)=a_{0}+\varepsilon a_{1}+\varepsilon^{2}a_{2}+\cdots$ , and similarly for $b,c$ . The coefficient of order $k$ in a rank-one path is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0299)

**表格与文字对照**

```text
| $[\varepsilon^{k}](a\otimes b\otimes c)=\sum_{i+j+\ell=k}a_{i}\otimes b_{j}\otimes c_{\ell}.$ | | (S9)

表内文字对照（数值与原始行列保持不变）：
varepsilon → ε
otimes b → otimes b
otimes c) → otimes c)
sum_ → sum_
ell → ell
otimes b_ → otimes b_
otimes c_ → otimes c_
```


<details>
<summary>英文原文</summary>

| $[\varepsilon^{k}](a\otimes b\otimes c)=\sum_{i+j+\ell=k}a_{i}\otimes b_{j}\otimes c_{\ell}.$ | | (S9)

</details>

在一级阶中，恰好出现三个项，构成了 Segre 微分方程。在二级阶中，涉及新的第二射线的项与该射线呈线性关系，而第一射线的乘积则已为人所知。因此，每个提升阶段都分为一个已知的非线性贡献项和一个精确的线性残差问题。这种分解是结构性的，而非对系数方程的近似处理。


<details>
<summary>英文原文</summary>

At order one, exactly three terms occur, giving the Segre differential. At order two, the terms involving a new second jet are linear in that jet, while products of first jets are already known. This is why each lifting stage separates into a known nonlinear contribution and an exact linear residual problem. The decomposition is structural, not an approximation to the coefficient equations.

</details>

假设某个阶段在有限域上要求得到 $Lx=r$。如果不存在解，则行约化可以生成满足 $\omega$ 但 $\omega L=0$ 的函数式 $\omega r\neq 0$；在适用情况下可将其重新缩放为 $\omega r=1$。任何人都可以通过乘法验证该证明。这证明了当前残差位于活跃切线图像之外。然而，这并不能证明该张量没有所需阶数的分解，因为新的基点、图表、支撑或更高阶的假设会改变 $L$ 甚至可能是 $r$。


<details>
<summary>英文原文</summary>

Suppose a stage asks for $Lx=r$ over a finite field. If no solution exists, row reduction can produce a functional $\omega$ satisfying $\omega L=0$ but $\omega r\neq 0$ ; rescale to $\omega r=1$ when applicable. Anyone can verify this witness by multiplication. It proves that the current residual is outside the active tangent image. It does not prove that the tensor has no decomposition of the desired rank, since a new base point, chart, support, or higher-order ansatz changes $L$ and possibly $r$ .

</details>

这种区分是搜索循环的核心。智能体会排除特定的局部方案族，并限制后续的表示形式。它不能被作为全局张量秩下界来接受。反复延长求解器超时时间无法在相同的图表内解决精确的cokernel障碍；改变图表则是一种数学上不同的干预方式。


<details>
<summary>英文原文</summary>

This distinction is central to the search loop. A witness excludes a precise local proposal family and can constrain the next representation. It cannot be admitted as a global tensor-rank lower bound. Repeatedly increasing a solver timeout would not resolve an exact cokernel obstruction within the same chart; changing the chart is a mathematically different intervention.

</details>

### I.1.2 从截断身份到边界上界


<details>
<summary>英文原文</summary>

I.1.2 From a truncated identity to a border upper bound

</details>

让完整的多项式一阶求和值为 $F(\varepsilon)$，并假设系数验证成立


<details>
<summary>英文原文</summary>

Let the full polynomial rank-one sum be $F(\varepsilon)$ and suppose coefficient verification establishes

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0305)

**表格与文字对照**

```text
| $F(\varepsilon)=\varepsilon^{h}T+\varepsilon^{h+1}E_{1}+\cdots+\varepsilon^{h+e}E_{e}.$ | | (S10)

表内文字对照（数值与原始行列保持不变）：
varepsilon) → ε)
varepsilon → ε
cdots → ……
```


<details>
<summary>英文原文</summary>

| $F(\varepsilon)=\varepsilon^{h}T+\varepsilon^{h+1}E_{1}+\cdots+\varepsilon^{h+e}E_{e}.$ | | (S10)

</details>

对于非零的 $\varepsilon$，重新缩放后的张量 $\varepsilon^{-h}F(\varepsilon)$ 的秩最多等于路径数量，因为标量可以被合并到每个项的其中一个因子中。当 $\varepsilon$ 在形式或代数上趋于零时，其极限值为 $T$。这给出了所讨论闭包的边界上界，但并未说明 $T$ 本身是否在没有极限参数的情况下也具有相同长度的秩分解。


<details>
<summary>英文原文</summary>

For nonzero $\varepsilon$ , the rescaled tensor $\varepsilon^{-h}F(\varepsilon)$ has rank at most the number of paths, because the scalar can be absorbed into one factor of each term. As $\varepsilon$ tends formally or algebraically to zero, its limit is $T$ . This supplies the border upper bound over the stated closure. It says nothing about whether $T$ itself has a rank decomposition of that same length without a limiting parameter.

</details>

对于张量幂次 $N$，误差程度最多为 $eN$。在 $eN+1$ 合适的场点进行插值可恢复幂次缩放表达式的常数系数，从而得到保留的 $(eN+1)r^{N}$ 精确化模式。插值点的可用性和扩展域下降的成本必须分别考虑。ss444结果使用 $e=4$，得到 $(4N+1)30^{N}$；后续的尾部消除情况虽能改善 $e$，但未必改变 $r$。


<details>
<summary>英文原文</summary>

For a tensor power $N$ , the error degree is at most $eN$ . Interpolating at $eN+1$ suitable field points recovers the constant coefficient of the powered rescaled expression, giving the retained $(eN+1)r^{N}$ exactification pattern. Availability of interpolation points and extension-field descent costs must be accounted for separately. The ss444 result uses $e=4$ , yielding $(4N+1)30^{N}$ ; the later tail-elimination cases improve $e$ without necessarily changing $r$ .

</details>

### I.1.3 语义重构与阴性对照


<details>
<summary>英文原文</summary>

I.1.3 Semantic reconstruction and negative controls

</details>

证书必须根据预期的矩阵运算进行验证，而不只是基于来自同一优化器的张量。独立路径通过输入/输出矩阵元素重建运算张量，解码官方有理因子，并针对这些语义对每个系数进行验证。这样就能将因子解析、目标构建和多项式展开区分为可能的错误来源。


<details>
<summary>英文原文</summary>

A certificate must be checked against the intended matrix operation, not only against a tensor imported from the same optimizer. The independent route reconstructs the operation tensor from input/output matrix entries, decodes the official rational factors, and checks every coefficient against those semantics. This separates factor parsing, target construction, and polynomial expansion as possible error sources.

</details>

ss444系数权重提供了实用的简洁诊断工具，但仅依靠权重无法证明身份：两个不同的张量可能具有相同的非零坐标数量。因此，录取流程采用完整的1,600个坐标比较方式，而权重仅作为支持计数摘要使用。一位比特损坏测试能够体现所选因素误差的影响，它补充了完整的坐标验证方法，而非取代它。


<details>
<summary>英文原文</summary>

The ss444 coefficient weights are useful compact diagnostics, but weights alone cannot prove identity: two different tensors can have the same number of nonzero coordinates. Admission therefore uses the full 1,600-coordinate comparison, with the weights serving only as a support-count summary. The one-bit corruption test demonstrates sensitivity to a chosen factor error. It complements, rather than replaces, the complete coordinate proof.

</details>

### I.2 Hyperfactor与跨输出AES共享机制


<details>
<summary>英文原文</summary>

I.2 Hyperfactor and cross-output AES sharing

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0313)

图 S5：因子共享机制及示例性成本模型。伪代码保持 $x$ 不变，将其计算为零辅助值中的因子，再重复使用该因子，最后取消计算。如果计算/取消计算成本为 $c$，每次使用成本为 $u>0$，则单独使用成本为 $k(c+u)$，共享使用成本为 $c+ku$。所绘制的相对节省量为 $(k-1)c/[k(c+u)]$，对应整数 $k$。这个简化的模型并未针对 AES 测量数据进行拟合，且忽略了分配、路由以及因子依赖的使用成本；它并非实际发射的电路。


<details>
<summary>英文原文</summary>

Figure S5: Factor-sharing mechanism and an illustrative cost model. The pseudocode keeps $x$ unchanged, computes a factor into a zero ancilla, reuses it, and uncomputes it. If compute/uncompute costs $c$ and each use costs $u>0$ , separate uses cost $k(c+u)$ and shared uses cost $c+ku$ . The plotted relative saving is $(k-1)c/[k(c+u)]$ , for integer $k$ . This simplified surface is not fitted to AES measurements and ignores allocation, routing, and factor-dependent use costs; it is not the emitted circuit.

</details>

图 S5解释了为何跨输出因子选择会改变计算/非计算成本。其模型仅关注重复次数与启动到使用成本比率；从10,746个T门降至9,234个T门所实现的AES效率提升，属于独立的匹配测量结果，并非基于该指标进行校准的单一数值。组件身份、调度安排以及完整电路均需要各自进行验证。


<details>
<summary>英文原文</summary>

Figure S5 explains why cross-output factor selection can change compute/uncompute cost. Its model isolates reuse count and the opening-to-use cost ratio; the recorded AES reduction from 10,746 to 9,234 T gates is a separate matched measurement, not a point calibrated on that surface. The identity, schedule, and complete circuit each require their own checks.

</details>

### 优化问题。


<details>
<summary>英文原文</summary>

Optimization problem.

</details>

让 $G$ 为残差群，$F$ 为冻结因子库。开启因子 $f$ 的代价为 $c_{f}$；将其分配给残差 $g$ 的代价为 $r_{gf}$。求解


<details>
<summary>英文原文</summary>

Let $G$ be residual groups and $F$ the frozen factor library. Opening factor $f$ costs $c_{f}$ ; assigning residual $g$ to it costs $r_{gf}$ . Solve

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0317)

**表格与文字对照**

```text
| $\min_{x,y}\sum_{f}c_{f}y_{f}+\sum_{g,f}r_{gf}x_{gf},\qquad\sum_{f}x_{gf}=1,\quad x_{gf}\leq y_{f},\quad x_{gf},y_{f}\in\{0,1\}.$ | | (S11)

表内文字对照（数值与原始行列保持不变）：
min_ → 最小值
sum_ → sum_
qquad → qquad
quad x_ → quad x_
leq y_ → leq y_
```


<details>
<summary>英文原文</summary>

| $\min_{x,y}\sum_{f}c_{f}y_{f}+\sum_{g,f}r_{gf}x_{gf},\qquad\sum_{f}x_{gf}=1,\quad x_{gf}\leq y_{f},\quad x_{gf},y_{f}\in\{0,1\}.$ | | (S11)

</details>

选定的因子被计算到辅助模块中，用于重复生成指定输出，随后不再计算。布尔核为 $(a\wedge h)\oplus(b\wedge h)=(a\oplus b)\wedge h$，与其输出族提升功能一同实现自动化。电路等价性需要额外的执行检查。


<details>
<summary>英文原文</summary>

A selected factor is computed into an ancilla, reused for assigned outputs, and uncomputed. The Boolean kernel is $(a\wedge h)\oplus(b\wedge h)=(a\oplus b)\wedge h$ , mechanized together with its output-family lifting. Circuit equivalence requires additional execution checks.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0319)

表 S10：冻结表示与成本模型下的 AES T-counts。最后两行采用了相同的 PyZX 后处理步骤。


<details>
<summary>英文原文</summary>

Table S10: AES T-counts under the frozen representation and cost model. The last two rows share the same PyZX post-processing pass.

</details>

该构造包含了1,013个ANF项，包含37个重复的非零成本因子，在所报告的PyZX之前的电路中使用了1,528个CCX门和23个量子比特。HiGHS与独立的SCIP实现在固定电荷目标上达成一致。一个独立的验证器能够重构AES逆变换和仿射输出ANF，检查精确单项式覆盖情况，并通过QASM模拟所有256种输入，同时验证辅助资源的恢复情况。移除一个CCX门属于负控制操作。经过匹配后处理可节省1,512个T门；与冻结对基线进行的比较则可节省15,190个T门。


<details>
<summary>英文原文</summary>

The construction covers 1,013 ANF occurrences, shares 37 repeated nonzero-cost factors, and uses 1,528 CCX gates and 23 qubits in the reported pre-PyZX circuit. HiGHS and an independent SCIP implementation agree on the fixed-charge objective. An independent verifier reconstructs AES inversion and affine-output ANFs, checks exact monomial coverage, and simulates all 256 inputs through QASM while checking ancilla restoration. Removing a CCX is a negative control. Matched post-processing saves 1,512 T gates; the comparison against the frozen pair baseline saves 15,190 T gates.

</details>

独立优化回放、ANF重建以及电路接收在注册结构方面达成一致。最优性仅适用于注册因子库和成本模型。全局AES电路的最优性、路由、深度以及噪声硬件性能尚未确定。


<details>
<summary>英文原文</summary>

The independent optimization replay, ANF reconstruction, and circuit receipt agree on the registered construction. Optimality applies only to the registered factor library and cost model. Global AES circuit optimality, routing, depth, and noisy hardware performance are not established.

</details>

### I.2.1 为什么任意维度的共享与配对匹配有所不同


<details>
<summary>英文原文</summary>

I.2.1 Why arbitrary-arity sharing differs from pair matching

</details>

一种成对优化器考虑同时共享两个残差表达式。对于三个或更多组来说具有益处的因素，在每一个局部选定的对中可能无利可图，但当其整体组的启动成本仅支付一次时则仍可能盈利。二元变量 $y_{f}$ 代表这种全局激活决策，而 $x_{gf}$ 变量则用于分配残差使用量。它们的耦合关系能够捕捉到仅靠独立残差选择无法体现的成本。


<details>
<summary>英文原文</summary>

A pairwise optimizer considers sharing between two residual expressions at a time. A factor that benefits three or more groups can be unprofitable in every locally selected pair and still profitable when its opening cost is paid only once for the whole group. The binary variable $y_{f}$ represents this global activation decision, while the $x_{gf}$ variables assign residual use. Their coupling captures a cost that cannot be represented by independent residual choices alone.

</details>

对于用于 $k\geq 2$ 输出的某个因素，令 $c>0$ 为其注册的计算-非计算成本，$u>0$ 为每输出使用成本。另外还有独立实现成本 $k(c+u)$，而法律共享调度成本则为 $c+ku$。


<details>
<summary>英文原文</summary>

For a factor used in $k\geq 2$ outputs, let $c>0$ be its registered compute–uncompute cost and $u>0$ the per-output use cost. Separate realization costs $k(c+u)$ , whereas a legal shared schedule costs $c+ku$ . Hence

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0326)

**表格与文字对照**

```text
| $k(c+u)-(c+ku)=(k-1)c>0,\qquad\frac{k(c+u)-(c+ku)}{k(c+u)}=\frac{(k-1)c}{k(c+u)}.$ | | (S12)

表内文字对照（数值与原始行列保持不变）：
k(c → k(c
u)-(c → u)-(c
ku) → ku)
qquad → qquad
frac → 分数
```


<details>
<summary>英文原文</summary>

| $k(c+u)-(c+ku)=(k-1)c>0,\qquad\frac{k(c+u)-(c+ku)}{k(c+u)}=\frac{(k-1)c}{k(c+u)}.$ | | (S12)

</details>

这证明了当所有使用过程中同一因素始终存在，且最终逆计算能够恢复辅助组件时，示意图所声称的节省效果是否成立。但这并不表明该因素在语义上存在于这些输出中，也不表明路由过程能保持相同的成本；这些是独立的证明义务。


<details>
<summary>英文原文</summary>

This establishes the saving claimed by the schematic whenever the same factor remains live across all uses and the final inverse computation restores the ancilla. It does not establish that a factor is semantically common to those outputs or that routing preserves the same cost; those are separate certificate obligations.

</details>

该优化模型还能区分逻辑共享与可逆执行。经典表达式有向无环图可能重复使用某个值，而无需说明临时存储如何恢复。可逆电路则必须包含因子的计算、使其可再次使用的使用过程，以及将临时寄存器恢复至初始值的逆计算步骤。因此，启动成本 $c_{f}$ 包含了已注册的计算/取消计算开销。如果忽略逆计算，模型就会优化错误的成本关系。


<details>
<summary>英文原文</summary>

The optimization model also distinguishes logical sharing from reversible execution. A classical expression DAG may reuse a value without specifying how temporary storage is restored. A reversible circuit must include the computation of the factor, the uses that leave it available, and the inverse computation returning the temporary register to its initial value. The opening cost $c_{f}$ therefore includes the registered compute/uncompute expense. A model that omits the inverse computation would optimize the wrong cost contract.

</details>

### I.2.2 根据选定的任务构建电路


<details>
<summary>英文原文</summary>

I.2.2 Constructing a circuit from a selected assignment

</details>

对于每个打开的因子，使用已注册的因子实现在指定的辅助模块上构建其值。按照预定的顺序对分配的输出执行针对残差的特殊控制操作。由于因子寄存器被用作控制手段，且其输入数据在合同约束下仍然可用，因此执行反向因子计算以重置该辅助模块。随后将生成的调度信息转换为 QASM 格式，并作为完整的电路进行验证。


<details>
<summary>英文原文</summary>

For each opened factor, construct its value on a designated ancilla using the registered factor implementation. Apply the residual-specific controlled operations to the assigned outputs in the scheduled order. Because the factor register is used as a control and its input data remain available under the contract, run the inverse factor computation to reset that ancilla. The emitted schedule is then translated to QASM and checked as a complete circuit.

</details>

此流程需要超过一个最优整数规划目标。任务分配必须符合预期的ANF出现情况；每个出现情况都必须按照表示法的取消约定进行处理；控制依赖关系必须合法；且未计算过程必须保持输出结果不变。求解器可能正确，而调度生成器却错误。独立的ANF和QASM层分别处理这些不同的接口问题。


<details>
<summary>英文原文</summary>

This procedure requires more than an optimal integer-program objective. The assignment must correspond to the intended ANF occurrences; every occurrence must be accounted for under the representation’s cancellation convention; control dependencies must be legal; and uncomputation must preserve outputs. A solver can be correct while the schedule generator is wrong. The independent ANF and QASM layers address these different interfaces.

</details>

该布尔恒等式可通过两元素布尔环的分配律得出。对于比特而言，XOR相当于加法，AND则相当于乘法，即$(a+b)h=ah+bh$。在每个输出索引处应用该恒等式可以说明存在共享的代数因子。该正式恒等式并未包含完整的辅助电路安排，也未将每个CCX完全分解为T门，因此完整电路和成本检查仍然是分开进行的。


<details>
<summary>英文原文</summary>

The Boolean identity follows by distributivity in the two-element Boolean ring. For bits, XOR is addition and AND is multiplication, so $(a+b)h=ah+bh$ . Applying the identity at each output index justifies shared algebraic factors. The formal identity does not encode the entire ancilla schedule or a decomposition of every CCX into T gates, which is why the full-circuit and cost checks remain separate.

</details>

### I.2.3 解读成本对比


<details>
<summary>英文原文</summary>

I.2.3 Interpreting the cost comparisons

</details>

第一项比较结果为25,886与10,696个T门，反映了从冻结对基线状态过渡到共享构建模式的综合影响。中间的12,362值表明，在独立输出Hyperfactor优化之后，通过交叉输出合并还额外减少了1,666个T门。对应的PyZX比较结果则揭示了同一后处理阶段下共享与独立模式的差异：10,746与9,234，相差1,512。


<details>
<summary>英文原文</summary>

The first comparison, 25,886 to 10,696 T gates, measures the combined effect of moving from the frozen pair baseline to the shared construction. The intermediate 12,362 value reveals an additional reduction of 1,666 T gates from cross-output merging after independent-output Hyperfactor optimization. The matched PyZX comparison isolates a shared-versus-independent contrast under the same post-processing pass: 10,746 versus 9,234, a difference of 1,512.

</details>

这些数值不应被合并视为同一项干预措施的测量结果。匹配后的后处理比较提供了最明确的证据，表明在那种特定优化器之后，共享仍然具有优势。较大的成对基线差异反映了构建方式的更广泛变化。两者均无法确立所有 AES 电路中最小的 T 计数，因为因子库、辅助预算、合成基础以及允许的安排决定了搜索空间的范围。


<details>
<summary>英文原文</summary>

These numbers should not be combined as if they were measurements of the same single intervention. The matched post-processing comparison provides the cleanest evidence that sharing remains advantageous after that specific optimizer. The larger pair-baseline difference reflects a broader change of construction. Neither establishes minimal T count among all AES circuits, because the factor library, ancilla budget, synthesis basis, and permitted schedules delimit the search space.

</details>

最后，对所有 256 种输入进行枚举对于该注册的八位输入合同来说是完全充分的。它验证了该合同下所实现的真值表和辅助恢复机制。它并未直接测量路由开销、物理架构下的深度，或噪声环境下的行为表现。该研究的贡献在于提供了可验证的电路构造方法以及固定模型下的成本比较。


<details>
<summary>英文原文</summary>

Finally, enumerating all 256 inputs is exhaustive for the registered eight-bit input contract. It checks the implemented truth table and ancilla restoration under that contract. It does not directly measure routing overhead, depth under a physical architecture, or behavior under noise. The contribution is a verifiable circuit construction and a cost comparison in a fixed model.

</details>

### I.3 全参数大重心构建器


<details>
<summary>英文原文</summary>

I.3 All-parameter Big-centroid constructor

</details>

对于 $d\geq 3$ 和有序维度 $u_{1}\leq\cdots\leq u_{d}$，设定 $q=\prod_{s=2}^{d}u_{s}$。选择具有非零元素的全列秩矩阵 $V^{(s)}\in\mathbb{F}^{u_{s}\times u_{1}}$ 以及左逆矩阵 $L^{(s)}V^{(s)}=I$。这一存在性条件是构造契约的一部分；有限的域测试集合并不能证明其在所有小域上都存在。


<details>
<summary>英文原文</summary>

For $d\geq 3$ and ordered dimensions $u_{1}\leq\cdots\leq u_{d}$ , set $q=\prod_{s=2}^{d}u_{s}$ . Choose full-column-rank matrices $V^{(s)}\in\mathbb{F}^{u_{s}\times u_{1}}$ with nonzero entries and left inverses $L^{(s)}V^{(s)}=I$ . This existence condition is part of the construction contract; a finite set of field tests does not prove existence over every small field.

</details>

对于 $J=(j_{2},\ldots,j_{d})$，首先定义第一模式坐标 $a_{J}(t)=\prod_{s=2}^{d}V^{(s)}_{j_{s},t}$。模式 $i\geq 2$ 的扰动使用


<details>
<summary>英文原文</summary>

For $J=(j_{2},\ldots,j_{d})$ , define first-mode coordinates $a_{J}(t)=\prod_{s=2}^{d}V^{(s)}_{j_{s},t}$ . The perturbation for mode $i\geq 2$ uses

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0340)

**表格与文字对照**

```text
| $\frac{L^{(i)}_{t,j_{i}}}{\prod_{s\geq 2,\,s\neq i}V^{(s)}_{j_{s},t}}.$ | | (S13)

表内文字对照（数值与原始行列保持不变）：
frac → 分数
prod_ → prod_
geq → geq
neq i → 不等于 i
```


<details>
<summary>英文原文</summary>

| $\frac{L^{(i)}_{t,j_{i}}}{\prod_{s\geq 2,\,s\neq i}V^{(s)}_{j_{s},t}}.$ | | (S13)

</details>

对 $j_{i}$ 进行求和后得到 $\sum_{j}L^{(i)}_{t,j}V^{(i)}_{j,t^{\prime}}=\delta_{tt^{\prime}}$。因此，目标线性坐标会带上所需的系数，而不需要的坐标则被抵消。减去 $u_{1}$ 常数校正张量后，便得到了一个 $q+u_{1}$ 一阶退化项。保留的展平下限与所提到的 Big-centroid 家族中的 $q+u_{1}$ 一致。


<details>
<summary>英文原文</summary>

Summing over $j_{i}$ yields $\sum_{j}L^{(i)}_{t,j}V^{(i)}_{j,t^{\prime}}=\delta_{tt^{\prime}}$ . Thus target linear coordinates appear with the required coefficients and unwanted coordinates cancel. Subtracting $u_{1}$ constant correction tensors yields a $q+u_{1}$ -term first-order degeneration. The retained flattening lower bound matches $q+u_{1}$ in the stated Big-centroid family.

</details>

通用机械化一阶核证明了常数消项与切线系数恒等式。构建器会分别检查矩阵逆、分母及坐标。提供的审计记录包含 390 个参数/字段控制项以及 278,904 个精确恒等式，其中包括奇素数字段以及用于测试的 $\mathrm{GF}(2^{k})$ 的 $k\geq 2$。在 $(2,2,2,3)$ 上的 $\mathbb{F}_{5}$ 示例包含 14 个项、30,184 个环境坐标，以及度数为 0–4 的支持权重 $(0,44,288,240,64)$。


<details>
<summary>英文原文</summary>

The generic mechanized first-order kernel proves constant cancellation and the tangent coefficient identity. The constructor separately checks matrix inverses, denominators, and coordinates. The supplied audit records 390 parameter/field controls and 278,904 exact identities, including odd prime fields and $\mathrm{GF}(2^{k})$ for tested $k\geq 2$ . The $(2,2,2,3)$ example over $\mathbb{F}_{5}$ has 14 terms, 30,184 ambient coordinates, and degree-0–4 support weights $(0,44,288,240,64)$ .

</details>

在给定假设下，结果是一个具有独立精确验证器的符号构造器，而非矩阵乘法指数方面的改进。相关的张量中心点理论提供了相关背景（Kassabov等，2026）。


<details>
<summary>英文原文</summary>

The result is a symbolic constructor with an independent exact verifier under the stated assumptions, not an improvement in the matrix-multiplication exponent. Related tensor-centroid theory supplies context ( Kassabov et al., 2026 ) .

</details>

### I.3.1 左逆恒等式作为证书生成器


<details>
<summary>英文原文</summary>

I.3.1 The left-inverse identity as a certificate generator

</details>

构建器的主要操作是局部抵消。固定模式为 $i$，以及除 $j_{i}$ 之外的所有索引。将扰动系数与基础坐标因子相乘，可以消除被固定模式中的所有分母。剩余的求和式等于 $L^{(i)}V^{(i)}$ 中的一个元素。当前两个模式标签相同时，该值等于一；否则为零。因此，同一个小矩阵恒等式既能够选择所需的坐标，又能抵消不需要的坐标。


<details>
<summary>英文原文</summary>

The constructor’s core operation is local cancellation. Fix mode $i$ and all indices except $j_{i}$ . Multiplying the perturbation coefficient by the base-coordinate factors cancels every denominator from the modes held fixed. The remaining sum over $j_{i}$ is exactly an entry of $L^{(i)}V^{(i)}$ . It equals one when the two first-mode labels coincide and zero otherwise. Thus the same small-matrix identity both selects desired coordinates and annihilates undesired ones.

</details>

这比为每个维度元组独立求解完整的环境切线系统更具信息量。后者只能验证一个实例，却无法揭示该实例为何有效。左逆构造揭示了一种维度参数化的代数机制，并生成了可验证性依赖于矩阵乘积、非零分母检查及坐标展开的证词。其有效性并不取决于某个异常有利的数值种子。


<details>
<summary>英文原文</summary>

This is more informative than solving the full ambient tangent system independently for each dimension tuple. The latter can certify one instance but hides why the instance works. The left-inverse construction exposes a dimension-parametric algebraic mechanism and emits witnesses whose validation reduces to matrix products, nonzero-denominator checks, and coordinate expansion. Its usefulness is not tied to one unusually favorable numerical seed.

</details>

该 $q$ 基础路径会贡献一个常数项。保留的构造方式将该常数项表示为 $u_{1}$ 修正张量，因此加上它们的负值可得到零常数系数。规定的阶一扰动则最终得到目标结果。这就是 $q+u_{1}$ 项数的原因；它并非通过数值拟合得出。需要匹配的展平方法才能确保该界限在该家族中处于最小状态。


<details>
<summary>英文原文</summary>

The $q$ base paths contribute a constant term. The retained construction expresses that constant as $u_{1}$ correction tensors, so adding their negatives produces zero constant coefficient. The prescribed first-order perturbations then yield the target. This is the reason for the $q+u_{1}$ term count; it is not inferred from a numerical fit. The matching flattening argument is needed to call the bound minimal within the stated family.

</details>

具体来说，令 $\mathrm{Flat}(T)$ 为 Big-centroid 张量的注册线性展平形式。秩为一的张量可映射为至多秩为一的矩阵，因此子加性性使得对于任意秩至多为 $\operatorname{rank}\mathrm{Flat}(T^{\prime})\leq r$ 的张量 $T^{\prime}$，都有 $r$。在特化条件下，矩阵秩是上半连续的；因此对于所有边界秩至多为 $r$ 的张量也成立相同不等式。一旦证明所展示的块结构具有


<details>
<summary>英文原文</summary>

Concretely, let $\mathrm{Flat}(T)$ be the registered linear flattening of the Big-centroid tensor. A rank-one tensor maps to a matrix of rank at most one, so subadditivity gives $\operatorname{rank}\mathrm{Flat}(T^{\prime})\leq r$ for every tensor $T^{\prime}$ of rank at most $r$ . Matrix rank is upper semicontinuous under specialization; hence the same inequality holds for every tensor of border rank at most $r$ . Once the displayed block structure is shown to have

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0349)

**表格与文字对照**

```text
| $\operatorname{rank}\mathrm{Flat}(T)=q+u_{1},$ | | (S14)

表内文字对照（数值与原始行列保持不变）：
operatorname → \operatorname
rank → 排名
mathrm → mathrm
Flat → 扁平
```


<details>
<summary>英文原文</summary>

| $\operatorname{rank}\mathrm{Flat}(T)=q+u_{1},$ | | (S14)

</details>

因此，$\brank(T)\geq q+u_{1}$。一阶构造给出了反向不等式，从而得出等式。剩下的任务就是证明在所给定的字段假设下块秩恒等式具有一致性；仅检查有限多个参数元组是不足以满足要求的。


<details>
<summary>英文原文</summary>

it follows that $\brank(T)\geq q+u_{1}$ . The first-order construction gives the reverse inequality, and therefore equality. The remaining obligation is to prove that block-rank identity uniformly under the stated field hypotheses; checking finitely many parameter tuples alone would not suffice.

</details>

### I.3.2 领域假设与小领域控制


<details>
<summary>英文原文</summary>

I.3.2 Field assumptions and small-field controls

</details>

包含除法运算的公式只有在其分母不为零时才具有意义。因此，构造者需要提供实际的系数矩阵及其左逆矩阵，而无需仅仅声称应存在合适的矩阵。在有限域中，矩阵存在性步骤需要一种考虑域特性的构造方法。特征为零的插值公式无法自动被约简到某个素数模下，因为该素数会使不同的参数消失或使分母变为零。


<details>
<summary>英文原文</summary>

A formula containing division is meaningful only when its denominators are nonzero. The constructor therefore supplies the actual coefficient matrices and their left inverses rather than merely stating that suitable matrices should exist. In finite fields, the matrix-existence step needs a field-aware construction. A characteristic-zero interpolation formula cannot automatically be reduced modulo a prime that collapses distinct parameters or makes denominators vanish.

</details>

所提供的来源声称，在奇素数域及至少二阶的二进制扩展域上存在统一的字段构造。其390个控制项和278,904个恒等式为该实现提供了有限的审计依据。通用的一阶Lean核心并未形式化这一完整的存在性定理。在本手稿中，显式的左逆假设被保留在展示的构造中，以便不会将一般的代数蕴含与独立的存在性和实例化层混淆起来。


<details>
<summary>英文原文</summary>

The supplied source claims a uniform field construction over odd prime fields and binary extension fields of degree at least two. Its 390 controls and 278,904 identities provide a finite audit of the implementation. The generic first-order Lean kernel does not formalize this full existence theorem. In this manuscript the explicit left-inverse hypotheses are retained in the displayed construction so that the general algebraic implication is not confused with the separate existence and instantiation layer.

</details>

该示例中的30,184个环境坐标表明另一个区别：稀疏目标可能需要检查大量零坐标。支持权重$(0,44,288,240,64)$按次数总结了多项式路径，但完整的验证必须确认这些系数具体出现在何处。如果正确的目标权重与错误的坐标分配不一致，则无法实现预期的张量退化。


<details>
<summary>英文原文</summary>

The example’s 30,184 ambient coordinates illustrate another distinction: a sparse target can require checking many zero coordinates. Support weights $(0,44,288,240,64)$ summarize the polynomial path by degree, but complete verification must check where those coefficients occur. A correct target weight with an incorrect coordinate assignment would not establish the intended tensor degeneration.

</details>

### I.3.3 结果的算法与数学作用


<details>
<summary>英文原文</summary>

I.3.3 Algorithmic and mathematical roles of the result

</details>

作为算法结果，Big-centroid 是一个确定性生成器，能够从维度元组及允许字段中产生因子路径和可验证有效载荷。作为数学结果，其正确性源于矩阵恒等式、常数抵消以及扁平化下界所构成的符号性蕴含关系。这些角色虽有关联但并不相同：没有实现的通用证明无法生成可执行的程序代码，而有限实现的测试若缺乏通用论证则无法确定所有参数。


<details>
<summary>英文原文</summary>

As an algorithmic result, Big-centroid is a deterministic generator producing factor paths and a checkable payload from a dimension tuple and an admitted field. As a mathematical result, its correctness is a symbolic implication from the matrix identities, constant cancellation, and flattening lower bound. These roles are related but not identical: a general proof without an implementation does not provide an executable artifact, while finite implementation tests without the general argument do not establish all parameters.

</details>

后来发展的对称 Full Perazzo案例采用了不同的插值组织方式，并包含额外的 Waring-秩和几何结论。我们保持这两个案例的独立性，以避免将同一公式重复计数作为无关证据。它们都展示了从模式观察到明确构建的共通过程，但其目标、假设和下限论证则有所不同。


<details>
<summary>英文原文</summary>

The symmetric Full Perazzo case developed later uses a different interpolation organization and has additional Waring-rank and geometric conclusions. We keep the two case identities distinct to avoid counting one formula twice as unrelated evidence. They demonstrate a shared transition from pattern observation to explicit construction, but their targets, assumptions, and lower-bound arguments differ.

</details>

### I.4 在54次比较中23的平均值


<details>
<summary>英文原文</summary>

I.4 Median-of-23 in 54 comparisons

</details>

让 $V_{i}(n)$ 表示选出 $i$ 个完全有序元素中第 $n$ 小的元素所需的最小最坏情况比较次数。保留的候选者为 $V_{12}(23)\leq 54$。所提供的比较点是一个包含 55 次比较的 Hadian–Sobel 构造；外部选择-文献综述与证书过程是分开进行的（Dörrer等人，2025）。


<details>
<summary>英文原文</summary>

Let $V_{i}(n)$ denote the minimum worst-case comparisons needed to select the $i$ th smallest of $n$ distinct totally ordered elements. The retained candidate is $V_{12}(23)\leq 54$ . The supplied comparison point is a 55-comparison Hadian–Sobel construction; external selection-literature review remains separate from the certificate ( Dörrer et al., 2025 ) .

</details>

早期本地候选方案因需要 56 次比较的路径而被证伪。保留的构建方式解决了这些失败问题，通过偏序集结构对超预算边界进行分类，并生成与预算相关的后续结果。具体的路径分解方式为


<details>
<summary>英文原文</summary>

An early local candidate was falsified by paths requiring 56 comparisons. The retained construction freezes those failures, classifies the over-budget frontier by poset structure, and synthesizes budget-specific continuations. The exact path decomposition is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0361)

**表格与文字对照**

```text
| $1{,}439{,}190{,}016=1{,}427{,}981{,}824+11{,}208{,}192.$ | | (S15)
```


<details>
<summary>英文原文</summary>

| $1{,}439{,}190{,}016=1{,}427{,}981{,}824+11{,}208{,}192.$ | | (S15)

</details>

第一个成分已经符合预算 54。其余的实例构成 1,454 个类别：


<details>
<summary>英文原文</summary>

The first summand already fits budget 54. The remaining occurrences form 1,454 classes:

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0363)

表 S11：修复后的中位数边界。每个基础深度加上延续预算之和为 54。


<details>
<summary>英文原文</summary>

Table S11: Repaired median frontier. Every base depth plus continuation budget equals 54.

</details>

调度器执行冻结的 Median-17 基础策略，在所选中位数基础上添加六个新项，并调用七项前缀策略。如果三个新项位于所选项下方，则返回该项；否则选择相关侧边，构建剩余偏序集，移除超出目标排名的元素，对状态进行规范重命名，并执行减少预算的剩余有向图算法。十六种策略覆盖各类别。


<details>
<summary>英文原文</summary>

The dispatcher runs the frozen median-17 base strategy, inserts six new items relative to the selected median, and invokes a seven-item prefix policy. If three new items lie below the selected item, it returns that item. Otherwise it selects the relevant side, constructs the residual poset, removes elements certified outside the target rank, canonically relabels the state, and executes a budget-decreasing residual DAG. Sixteen policies cover the classes.

</details>

所报告的 Lean 层包括传递位掩码插入、叶节点的等级语义、保持等级的移除/减少操作、双射重标记、特殊索引零的保留，以及良基策略终止。它们还会对 4,100 个前缀节点、9,200 个剩余节点、84,894 次转移、类计数以及全局路径运算进行检查。负面控制会破坏等级递减、重标记、剩余等级、已求解叶节点、类覆盖及语义保护机制。


<details>
<summary>英文原文</summary>

The reported Lean layers cover transitive bitmask insertion, rank semantics of leaves, rank-preserving removal/reduction, bijective relabeling, preservation of distinguished index zero, and well-founded policy termination. They also check 4,100 prefix nodes, 9,200 residual nodes, 84,894 transfers, class counts, and global path arithmetic. Negative controls corrupt rank decrements, relabeling, residual ranks, solved leaves, class coverage, and semantic guards.

</details>

仍有两个关键桥梁有待建立：针对每个具体的 V279 状态，确定普通顺序准则的每一个字段的具体值；并将生成的统计结果与关于 23 项内容的正式决策树相结合。因此，该结果只是一个内部精确计算的上限候选方案，而非完全形式化的定理或证明，以说明 54 是最优解。


<details>
<summary>英文原文</summary>

Two headline bridges remain: instantiating every field of the common-order criterion for each concrete V279 state, and binding the generated census to a formal decision tree on 23 items. Therefore the result is an internal exact-computation upper-bound candidate, not a fully formalized theorem or a proof that 54 is optimal.

</details>

### I.4.1 决策树正确性与路径计数算法的比较


<details>
<summary>英文原文</summary>

I.4.1 Decision-tree correctness versus path-count arithmetic

</details>

路径计数并非决策树正确性的证明。每个比较分支必须表示相应的序关系，每个终端返回必须在该序关系所涵盖的所有全序中具有所要求的排名，且每次分发操作必须保持目标排名。只有在这些语义条件被应用于枚举的状态之后，全局计数才具有意义。


<details>
<summary>英文原文</summary>

A path count is not a decision-tree correctness proof. Every comparison branch must represent the corresponding order relation, every terminal return must have the requested rank in every total order extending that relation, and every dispatch must preserve the target rank. The global count becomes meaningful only after these semantic conditions are attached to the enumerated states.

</details>

将残差状态表示为 $(P,r,b)$ ，其中 $P$ 为当前比较偏序集，$r$ 为请求的零基排名，$b$ 为剩余的比较预算。递归定义 $\mathcal{C}(P,r,b)$：当其返回的元素在 $P$ 的每一个线性扩展中都具有 $r$ 排名时，该叶节点才有效；当内部比较中的不可比 $x,y$ 满足两个子状态均通过对应关系扩展 $P$ 且预算不超过 $b-1$ 时，该比较也有效。随后基于 $b$ 的归纳推理可得出结果


<details>
<summary>英文原文</summary>

Write a residual state as $(P,r,b)$ , where $P$ is the current comparison poset, $r$ the requested zero-based rank, and $b$ the remaining comparison budget. Define $\mathcal{C}(P,r,b)$ recursively: a leaf is valid when its returned element has rank $r$ in every linear extension of $P$ ; an internal comparison of incomparable $x,y$ is valid when both child states extend $P$ by the corresponding relation and satisfy $\mathcal{C}$ with budget at most $b-1$ . Induction on $b$ then gives

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0371)

**表格与文字对照**

```text
| $\mathcal{C}(P,r,b)\Longrightarrow\text{every total order extending $P$ reaches a correct leaf in at most $b$ comparisons}.$ | | (S16)

表内文字对照（数值与原始行列保持不变）：
mathcal → mathcal
Longrightarrow → Longrightarrow
text → 文本
every total order extending → 所有扩展全序集
reaches a correct leaf in at most → 最多达到正确的结果
comparisons → 比较
```


<details>
<summary>英文原文</summary>

| $\mathcal{C}(P,r,b)\Longrightarrow\text{every total order extending $P$ reaches a correct leaf in at most $b$ comparisons}.$ | | (S16)

</details>

基础情况是叶节点的通用排名条件。对于归纳步骤，每个全序恰好满足 $x<y$ 或 $y<x$ 中的一种，因此执行流程会进入对应的子节点；其预算较小，而归纳假设则保证了正确性与终止性。因此，语义定理依赖于子节点状态的有效性及叶节点排名，而非枚举路径的数量。


<details>
<summary>英文原文</summary>

The base case is the universal-rank condition at a leaf. For the inductive step, every total order satisfies exactly one of $x<y$ or $y<x$ , so execution enters the matching child; its budget is smaller, and the induction hypothesis supplies correctness and termination. Thus the semantic theorem depends on child-state validity and leaf ranks, not on the number of enumerated paths.

</details>

剩余问题可以通过一个有限偏序集和目标秩来表示。移除被判定为低于目标的元素会降低目标秩；移除被判定为高于目标的元素则会使秩保持不变。规范重标记仅在保持顺序约束并正确传递所选项目和目标的情况下才有效。这些简单规则解释了为何秩降低和重标记错误是重要的负面控制因素：任何错误都可能保持图的大小和节点数量不变，同时改变选择过程。


<details>
<summary>英文原文</summary>

A residual problem can be represented by a finite poset and a target rank. Removing an element certified below the target decrements the target rank; removing an element certified above it leaves the rank unchanged. Canonical relabeling is valid only when it is a bijection preserving order constraints and transporting the selected item and target correctly. These simple rules explain why rank-decrement and relabel corruptions are important negative controls: either mistake can preserve graph sizes and node counts while changing the selection problem.

</details>

对于剩余预算为 $b$ 的策略节点，每个比较子节点必须拥有更低的预算，且其状态必须延续父节点的比较结果。已解决的叶节点必须满足注册的排名标准。基于预算的归纳过程可验证剩余策略的终止性与正确性。提供的 Lean 框架集化了这些语义要素以及大量生成的策略库；它不允许遗漏剩余的具体普查绑定义务。


<details>
<summary>英文原文</summary>

For a policy node with remaining budget $b$ , each comparison child must have a smaller budget, and its state must extend the parent’s comparison outcome. A solved leaf must satisfy the registered rank criterion. Induction on the budget then verifies termination and correctness of the residual policy. The supplied Lean stack formalizes these semantic ingredients and a large generated policy library; it does not allow the remaining concrete census-binding obligations to be omitted.

</details>

### I.4.2 为什么分类会压缩困难领域边界


<details>
<summary>英文原文</summary>

I.4.2 Why classification compresses the difficult frontier

</details>

11,208,192次修复实例并不需要如此多的单独合成策略。许多剩余状态在有效的简化和重新标记后都是等价的。将它们压缩为1,454个类别，则会使策略设计问题大大简化。不过，调度员证书仍必须涵盖每一个原始实例，并验证其被分配到相应类别的运输过程。


<details>
<summary>英文原文</summary>

The 11,208,192 repaired occurrences do not require that many separately synthesized strategies. Many residual states are equivalent after valid reduction and relabeling. Compressing them into 1,454 classes exposes a much smaller policy-design problem. The dispatcher certificate must nevertheless account for every original occurrence and verify the transport into its assigned class.

</details>

三个基础深度组展示了资源限制如何构成。深度32允许进行22次比较的延续；深度33允许21次；深度34允许20次。每个组合都受到54的约束。15,422和1,017个类别数量之和为1,454，它们的出现次数则构成了修复后的边界。这些等式用于验证覆盖率和算术关系；它们并不确立单个类别转换的语义含义，后者需单独检查。


<details>
<summary>英文原文</summary>

The three base-depth groups show how the resource bound composes. Depth 32 allows a 22-comparison continuation; depth 33 allows 21; depth 34 allows 20. Each composition is bounded by 54. The 15, 422, and 1,017 class counts sum to 1,454, and their occurrences sum to the repaired frontier. These equalities audit coverage and arithmetic; they do not establish the semantics of a single class transfer, which is checked separately.

</details>

十六个可复用策略代表了进一步的压缩层级。它们并不等同于十六个原始任务实例，其生成的有向无环图节点也不是独立的实验。该贡献在于普查方法、保持等价性的简化方法、小型策略库以及经过验证的调度映射的结合。每一层都消除了独立重放所面临的不同障碍。


<details>
<summary>英文原文</summary>

Sixteen reusable policies are a further level of compression. They are not equivalent to sixteen original task instances, and their generated DAG nodes are not independent experiments. The contribution is the combination of a census, equivalence-preserving reduction, a small policy library, and a verified dispatch map. Each layer removes a different obstacle to independent replay.

</details>

## 附录 J 六个数学发现案例


<details>
<summary>英文原文</summary>

Appendix J Six Mathematical Discovery Cases

</details>

本部分将这六项数学发现以明确的陈述形式呈现，并包含相应的假设、构造、下界、等式条件以及分析完善步骤。精确的有限证书能够处理复杂的代数展开，而下面的文字论证则提供了可复用的定理桥梁。最终得到的是一份以证明为导向的说明，阐述了 EPOCH 所发现的内容以及各项结论之间的推导关系。


<details>
<summary>英文原文</summary>

This section presents the six mathematical discoveries as explicit statements with their hypotheses, constructions, lower bounds, equality conditions, and analytic completion steps. Exact finite certificates handle the large algebraic expansions, while the written arguments below supply the reusable theorem bridges. The result is a proof-oriented account of what EPOCH discovered and how each conclusion follows.

</details>

每个论点的逻辑核心均直接在其子节中表述，因此身份、有限计数、分析极限或形式定理无法被随意替代。表 S9 展示了不同案例间的对比情况，未重复这些推导过程。


<details>
<summary>英文原文</summary>

The logical spine of each argument is stated directly in its subsection so that an identity, finite census, analytic limit, or formal theorem cannot silently substitute for another. Table S9 gives the cross-case comparison without repeating those derivations.

</details>

### J.1 超立方体行列式不等式与等式分类


<details>
<summary>英文原文</summary>

J.1 Hypercube determinant inequality and equality classification

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0383)

图 S6：超立方体不等式的精确两参数切片。在三维空间中，取独立的坐标质量分别为 $(p,q,1/2)$ 和 $W=1$。该图展示了 $10^{3}$ 倍的松弛量 $G=\prod_{i}m_{i,0}m_{i,1}-\operatorname{SD}(w)$。直接展开可得 $G=[p(1-p)q(1-q)]^{2}/4$：在内部为正，在边界为零，而支撑点位于某个面内。这一公式推导出的切片体现了“全权重、全维度”定理。


<details>
<summary>英文原文</summary>

Figure S6: An exact two-parameter slice of the Hypercube inequality. In dimension three take independent coordinate masses $(p,q,1/2)$ , so $W=1$ . The plot shows $10^{3}$ times the slack $G=\prod_{i}m_{i,0}m_{i,1}-\operatorname{SD}(w)$ . Direct expansion gives $G=[p(1-p)q(1-q)]^{2}/4$ : positive in the interior and zero on the boundary, where support lies in a facet. This formula-derived slice illustrates the all-weight, all-dimensional theorem.

</details>

图 S6 对多项式陈述及其等式条件进行了几何性解读。支持图展示了假设而非实验样本结果。对于该产品权重片段，对 $\binom{8}{4}=70$ 无序顶点子集的精确展开即得到所显示的松弛多项式。在 $p=q=1/2$ 处，两边分别为 $15/1024$ 和 $16/1024$。我们在 $p,q\in\{0,1/4,1/2,3/4,1\}$ 的 25 点网格上用有理数运算进行了展开验证；这仅是视觉上的一致性检查，并非对所报告的 Lean 证明的新执行。下面的一般陈述并不假设产品权重。


<details>
<summary>英文原文</summary>

Figure S6 provides a geometric reading of the polynomial statement and its equality condition. The support drawings illustrate the hypotheses rather than sample experimental outcomes. For this product-weight slice, an exact expansion over the $\binom{8}{4}=70$ unordered vertex subsets gives the displayed slack polynomial. At $p=q=1/2$ , the two sides are $15/1024$ and $16/1024$ . We checked the expansion with rational arithmetic on the 25-point grid $p,q\in\{0,1/4,1/2,3/4,1\}$ ; this is a consistency check of the visual, not a new execution of the reported Lean proof. The general statement below does not assume product weights.

</details>

令 $w_{v}\geq 0$ 代表 $v\in\{0,1\}^{d}$、$W=\sum_{v}w_{v}$ 和 $m_{i,b}=\sum_{v:v_{i}=b}w_{v}$。通过明确定义无序行列式多项式来表述


<details>
<summary>英文原文</summary>

Let $w_{v}\geq 0$ for $v\in\{0,1\}^{d}$ , $W=\sum_{v}w_{v}$ , and $m_{i,b}=\sum_{v:v_{i}=b}w_{v}$ . Define the unordered determinant polynomial explicitly by

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0386)

**表格与文字对照**

```text
| $\operatorname{SD}(w)=\sum_{\begin{subarray}{c}U\subseteq\{0,1\}^{d}\\
|U|=d+1\end{subarray}}\left|\det\begin{pmatrix}1&\cdots&1\\
v_{0}&\cdots&v_{d}\end{pmatrix}\right|\prod_{v\in U}w_{v},$ | | (S17)

表内文字对照（数值与原始行列保持不变）：
operatorname → \operatorname
sum_ → sum_
begin → 开始
subarray → 子数组
subseteq → 子集
end → 结束
left → 左侧
det → 检测
pmatrix → p矩阵
cdots → ……
right → 正确
prod_ → prod_
in U → 在 U 中
```


<details>
<summary>英文原文</summary>

| $\operatorname{SD}(w)=\sum_{\begin{subarray}{c}U\subseteq\{0,1\}^{d}\\
|U|=d+1\end{subarray}}\left|\det\begin{pmatrix}1&\cdots&1\\
v_{0}&\cdots&v_{d}\end{pmatrix}\right|\prod_{v\in U}w_{v},$ | | (S17)

</details>

其中绝对决定因子使得 $U=\{v_{0},\ldots,v_{d}\}$ 的排序无关紧要。所保留的有限多项式定理是


<details>
<summary>英文原文</summary>

where the absolute determinant makes the ordering of $U=\{v_{0},\ldots,v_{d}\}$ immaterial. The retained finite-polynomial theorem is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0388)

**表格与文字对照**

```text
| $\operatorname{SD}(w)W^{d-1}\leq\prod_{i=1}^{d}m_{i,0}m_{i,1}\qquad(d\geq 1).$ | | (S18)

表内文字对照（数值与原始行列保持不变）：
operatorname → \operatorname
w)W → w)W
leq → leq
prod_ → prod_
qquad(d → qquad(d
geq → geq
```


<details>
<summary>英文原文</summary>

| $\operatorname{SD}(w)W^{d-1}\leq\prod_{i=1}^{d}m_{i,0}m_{i,1}\qquad(d\geq 1).$ | | (S18)

</details>

对于 $d\geq 3$，当且仅当至少有一个面质量为零时，两者相等。对于 $d=1$，$W^{0}$ 被解释为多项式常数 1，包括 $W=0$。


<details>
<summary>英文原文</summary>

For $d\geq 3$ , equality holds exactly when at least one facet mass is zero. For $d=1$ , $W^{0}$ is interpreted as the polynomial constant 1, including $W=0$ .

</details>

### 证明机制。


<details>
<summary>英文原文</summary>

Proof mechanism.

</details>

如果满足 $W>0$，则将其归一化为一个立方体值随机向量 $X$。设 $\Delta$ 为独立抽取的样本 $d+1$ 的仿射行列式。


<details>
<summary>英文原文</summary>

If $W>0$ , normalize to a cube-valued random vector $X$ . Let $\Delta$ be the affine determinant of $d+1$ independent draws. Then

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0392)

**表格与文字对照**

```text
| $\operatorname{SD}(w)=\frac{W^{d+1}}{(d+1)!}\mathbb{E}|\Delta|,\qquad\mathbb{E}\Delta^{2}=(d+1)!\det\Cov(X).$ | | (S19)

表内文字对照（数值与原始行列保持不变）：
operatorname → \operatorname
frac → 分数
mathbb → \mathbb
Delta → Delta
qquad → qquad
det → 检测
Cov(X) → Cov(X)
```


<details>
<summary>英文原文</summary>

| $\operatorname{SD}(w)=\frac{W^{d+1}}{(d+1)!}\mathbb{E}|\Delta|,\qquad\mathbb{E}\Delta^{2}=(d+1)!\det\Cov(X).$ | | (S19)

</details>

完整性保证了 $|\Delta|\leq\Delta^{2}$ 的性质，而正半定义性和哈达玛不等式则确保了其特性


<details>
<summary>英文原文</summary>

Integrality gives $|\Delta|\leq\Delta^{2}$ , while positive semidefiniteness and Hadamard’s inequality give

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0394)

**表格与文字对照**

```text
| $\det\Cov(X)\leq\prod_{i}\operatorname{Var}(X_{i})=W^{-2d}\prod_{i}m_{i,0}m_{i,1}.$ | | (S20)

表内文字对照（数值与原始行列保持不变）：
det → 检测
Cov(X) → Cov(X)
leq → leq
prod_ → prod_
operatorname → \operatorname
Var → 变量
```


<details>
<summary>英文原文</summary>

| $\det\Cov(X)\leq\prod_{i}\operatorname{Var}(X_{i})=W^{-2d}\prod_{i}m_{i,0}m_{i,1}.$ | | (S20)

</details>

结合这些性质并恢复一致性即可证明该不等式。$W=0$情形是显而易见的。要得到等式关系，需要具有正概率元组上的行列式以及对角协方差的$\{0,\pm 1\}$条件。所提供的形式化证明排除了所有面质量均为正的同时成立等式的情况，采用了有理主元变换、整数清零以及两级分离构造方法。当某个面为零时，支撑域被限制在一个超平面上，从而直接得出等式关系。


<details>
<summary>英文原文</summary>

Combining the identities and restoring homogeneity proves the inequality. The $W=0$ case is immediate. Equality requires determinants in $\{0,\pm 1\}$ on positive-probability tuples and diagonal covariance. The supplied formal proof excludes simultaneous equality with all facet masses positive for $d\geq 3$ , using rational pivots, integer clearing, and a two-level separating construction. A zero facet confines the support to a hyperplane and gives equality directly.

</details>

所报道的 Lean 4.19 链证明了有限多项式不等式与等式特征描述，并排除了错误的等式变异情况。与 Averkov 等人在 2026 年提出的几何猜想之间的关系，仍需要完整的区域/混合体积桥梁以及外部陈述一致性审查；我们不会盲目地将多项式结果推广到所有几何公式中。


<details>
<summary>英文原文</summary>

The reported Lean 4.19 chain proves the finite-polynomial inequality and equality characterization, including rejection of an incorrect equality mutation. The relation to the geometric conjecture of Averkov et al. (2026) still requires the complete zonoid/mixed-volume bridge and external statement-alignment review; we do not silently promote the polynomial result to every geometric formulation.

</details>

### J.1.1 推导行列式二阶矩恒等式


<details>
<summary>英文原文</summary>

J.1.1 Deriving the determinant second-moment identity

</details>

设 $Z=(1,X^{\top})^{\top}$ 和 $Z_{0},\ldots,Z_{d}$ 为两个独立的副本。将仿射行列式表示为这些列构成的矩阵的行列式。对其进行平方展开后，会得到一个关于排列的双重求和。由于独立性，每一项都可以分解为第二矩矩阵 $G=\mathbb{E}[ZZ^{\top}]$ 的矩阵元素。对排列求和项进行重新组合后便得到结果


<details>
<summary>英文原文</summary>

Let $Z=(1,X^{\top})^{\top}$ and let $Z_{0},\ldots,Z_{d}$ be independent copies. Write the affine determinant as the determinant of the matrix with these columns. Expanding its square produces a double sum over permutations. Independence lets each term factor into entries of the second-moment matrix $G=\mathbb{E}[ZZ^{\top}]$ . Regrouping the permutation sums yields

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0399)

**表格与文字对照**

```text
| $\mathbb{E}\det(Z_{0},\ldots,Z_{d})^{2}=(d+1)!\det G.$ | | (S21)

表内文字对照（数值与原始行列保持不变）：
mathbb → \mathbb
det(Z_ → det(Z_
ldots → ……
det G → det G
```


<details>
<summary>英文原文</summary>

| $\mathbb{E}\det(Z_{0},\ldots,Z_{d})^{2}=(d+1)!\det G.$ | | (S21)

</details>

该块矩阵具有如下形式


<details>
<summary>英文原文</summary>

The block matrix has the form

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0401)

**表格与文字对照**

```text
| $G=\begin{pmatrix}1&\mu^{\top}\\
\mu&\mathbb{E}[XX^{\top}]\end{pmatrix},\qquad\mu=\mathbb{E}X.$ | | (S22)

表内文字对照（数值与原始行列保持不变）：
begin → 开始
pmatrix → p矩阵
top → 顶级
mathbb → \mathbb
end → 结束
qquad → qquad
```


<details>
<summary>英文原文</summary>

| $G=\begin{pmatrix}1&\mu^{\top}\\
\mu&\mathbb{E}[XX^{\top}]\end{pmatrix},\qquad\mu=\mathbb{E}X.$ | | (S22)

</details>

通过 Schur 补数减去平均贡献后得到 $\det G=\det(\mathbb{E}[XX^{\top}]-\mu\mu^{\top})=\det\Cov(X)$。这样便无需进行特定维度的多项式展开，即可建立所陈述的等式关系。


<details>
<summary>英文原文</summary>

Subtracting the mean contribution through the Schur complement gives $\det G=\det(\mathbb{E}[XX^{\top}]-\mu\mu^{\top})=\det\Cov(X)$ . This establishes the stated identity without requiring a dimension-specific polynomial expansion.

</details>

从有序随机样本转换为无序单纯形多项式时，也存在一个精确的重数。具有重复顶点的元组对行列式贡献为零。每个 $(d+1)$ 个元素的顶点集都出现在具有相等绝对行列式和乘积权重的 $(d+1)!$ 种排序中，因此必须将其除以该阶乘值；若忽略这一操作，将会改变定理的归一化特性。随后，$W$ 的幂次能够恢复度为 $2d$ 的齐次不等式性质。


<details>
<summary>英文原文</summary>

The conversion from the ordered random sample to the unordered simplex polynomial also has a precise multiplicity. Tuples with repeated vertices contribute zero determinant. Each $(d+1)$ -element vertex set appears in $(d+1)!$ orders with equal absolute determinant and product weight. Dividing by this factorial is therefore required; omitting it would alter the theorem’s normalization. The powers of $W$ then restore the degree- $2d$ homogeneous inequality.

</details>

### J.1.2 平等要求两种同时存在的刚性特征


<details>
<summary>英文原文</summary>

J.1.2 Equality requires two simultaneous rigidities

</details>

当所有正概率行列式的绝对值均为零或一时，整体性步骤是尖锐的。相关协方差矩阵满足哈达玛不等式等式条件时，协方差步骤也是尖锐的。如果面质量为零，支撑集位于一个坐标超平面上，因此所有全维行列式均消失，两边也均为零。


<details>
<summary>英文原文</summary>

The integrality step is sharp exactly when every positive-probability determinant has absolute value zero or one. The covariance step is sharp when the relevant covariance matrix satisfies the equality condition of Hadamard’s inequality. If a facet mass is zero, the support lies in a coordinate hyperplane, so all full-dimensional determinants vanish and both sides are zero.

</details>

困难的方向在于：当所有方面质量在至少三维空间中为正时，排除相等性。第一个不等式限制了支撑集的仿射行列式，而第二个不等式则限制了其混合矩。单独满足任一条件也无法排除许多非退化分布。正式的等式论证通过所给出的有理枢点和分离器构造将它们联系起来。这是一个独立的证明部分，并非仅因写出协方差不等式就能自动得出的结果。


<details>
<summary>英文原文</summary>

The difficult direction is excluding equality when all facet masses are positive in dimension at least three. The first inequality constrains affine determinants of the support, while the second constrains its mixed moments. Neither condition alone excludes many nondegenerate distributions. The formal equality argument connects them through the supplied rational-pivot and separator construction. This is a separate proof component, not an automatic corollary of writing down the covariance inequality.

</details>

低维情况被特意排除在分类的所述 $d\geq 3$ 范围之外。该不等式适用于所有正维度，但在一维和二维中，等号可能具有不同的结构。保留维度限定词可避免真正的普遍不等式变成过度泛化的等号陈述。


<details>
<summary>英文原文</summary>

The low-dimensional cases are deliberately outside the stated $d\geq 3$ iff classification. The inequality holds for all positive dimensions, but equality can have a different structure in dimensions one and two. Preserving the dimension qualifier prevents a true general inequality from carrying an overgeneralized equality statement.

</details>

### J.1.3 形式化陈述对齐与几何解释


<details>
<summary>英文原文</summary>

J.1.3 Formal statement alignment and geometric interpretation

</details>

Lean 结果检验了由立方体顶点、权重和行列式系数构成的有限多项式。该几何问题涉及区域体与混合体积公式。即使有限不等式是核心代数障碍，要将形式化定理转化为外部几何命题，仍需进行精确的约化、标准化及假设验证。证明助手无法完成这一转换，仅仅因为两种讨论都使用了“超立方体”这个词。


<details>
<summary>英文原文</summary>

The Lean result checks a finite polynomial built from cube vertices, weights, and determinant coefficients. The source geometric question involves zonoids and mixed-volume formulations. Even if the finite inequality is the central algebraic obstruction, transferring the formal theorem to an external geometric claim requires the exact reduction, its normalization, and its hypotheses. A proof assistant cannot fill that bridge merely because both discussions use the word “Hypercube.”

</details>

因此，该案例具有两个显著优势：一是不等式的简短且可复用的证明机制；二是包含等式在内的有限命题的完整形式化链条。其剩余的外部机制则是对齐与优先级机制，而非未经验证的有限多项式计算。这种状态与后续分析案例中仅使用核心元素的形式化方法有显著不同。


<details>
<summary>英文原文</summary>

This case therefore has two distinct strengths: a short reusable proof mechanism for the inequality, and a reported complete formal chain for the finite statement including equality. Its remaining external gate is alignment and priority, rather than an unproved finite polynomial calculation. That status differs substantially from the kernel-only formalizations in the later analytic cases.

</details>

### J.2 H-beta 前置加载：九个元素的反例


<details>
<summary>英文原文</summary>

J.2 H-beta front-loading: a nine-element counterexample

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0412)

图 S7：H-beta反例及其家族机制。(a) 精确给出的分级尺寸显示中间系数从 $(27,27)$ 变为 $(31,32)$，违反了已注册的前置加载不等式。(b) 在保留的家族公式中进行减法运算后，每个 $h_{2}^{\beta}-h_{3}^{\beta}=-1$ 对应得到 $a,d\geq 0$；所绘制的参数范围正是这一关系的体现，并非对无限家族的完整实验验证。


<details>
<summary>英文原文</summary>

Figure S7: The H-beta counterexample and its family mechanism. (a) Exact supplied graded dimensions show the middle coefficients changing from $(27,27)$ to $(31,32)$ , violating the registered front-loading inequality. (b) Subtraction in the retained family formula gives $h_{2}^{\beta}-h_{3}^{\beta}=-1$ for every $a,d\geq 0$ ; the plotted parameter range is an illustration of that identity, not an exhaustive experimental verification of the infinite family.

</details>

图 S7 说明了为什么该反例在结构上具有持久性：两个中间系数都通过相同的扩展项增长，从而保留了一个单位缺陷。


<details>
<summary>英文原文</summary>

Figure S7 shows why the counterexample is structurally persistent: both middle coefficients grow by the same extension term, preserving a one-unit defect.

</details>

对于注册的五级会议，测试的前置加载条件为 $h_{2}^{\beta}\geq h_{3}^{\beta}$ 。保留的简单九元素矩阵结构为 $M195313$


<details>
<summary>英文原文</summary>

For the registered rank-five convention, the tested front-loading condition is $h_{2}^{\beta}\geq h_{3}^{\beta}$ . The retained simple nine-element matroid $M195313$ has

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0415)

**表格与文字对照**

```text
| flat-layer counts | $\displaystyle=(1,9,32,49,27,1),$ | $\displaystyle\#\text{bases}$ | $\displaystyle=67,$ | | (S23)
 | $\displaystyle H_{0}$ | $\displaystyle=(1,9,27,27,9,1),$ | $\displaystyle H_{\beta}$ | $\displaystyle=(1,9,31,32,9,1),$ | | (S24)
 | $\displaystyle H_{\beta}-H_{0}$ | $\displaystyle=(0,0,4,5,0,0).$ | | (S25)

表内文字对照（数值与原始行列保持不变）：
flat-layer counts → 单层计数
displaystyle → \displaystyle
text → 文本
bases → 基础
displaystyle H_ → \displaystyle H_
beta → beta
```


<details>
<summary>英文原文</summary>

| flat-layer counts | $\displaystyle=(1,9,32,49,27,1),$ | $\displaystyle\#\text{bases}$ | $\displaystyle=67,$ | | (S23)
 | $\displaystyle H_{0}$ | $\displaystyle=(1,9,27,27,9,1),$ | $\displaystyle H_{\beta}$ | $\displaystyle=(1,9,31,32,9,1),$ | | (S24)
 | $\displaystyle H_{\beta}-H_{0}$ | $\displaystyle=(0,0,4,5,0,0).$ | | (S25)

</details>

因此为 $h_{2}^{\beta}-h_{3}^{\beta}=-1$，相应的差向量缺陷也为 $-1$。在将此计算与 Sinclair (2026) 的猜想联系起来时，必须明确匹配源代码的微分度约定；该反例并不能反驳相关的对数凹性陈述。


<details>
<summary>英文原文</summary>

Thus $h_{2}^{\beta}-h_{3}^{\beta}=-1$ , and the corresponding difference-vector defect is also $-1$ . The source’s differential-degree conventions must be matched explicitly when relating this computation to the conjectures of Sinclair (2026) ; the counterexample does not refute adjacent log-concavity statements.

</details>

八级循环平面决定了所有 512 个子集等级。验证链会检查等级归一化、单调性、所有子模度不等式、简单性、平面与覆盖关系，以及 67 个基的独立重构。精确有理原子空间和 $D_{\beta}$ 覆盖矩阵通过列空间递归产生分级维度。禁用 $D_{\beta}$ 会导致维度变化并被拒绝。具体的有限陈述由两个独立构建的机械化程序报告。


<details>
<summary>英文原文</summary>

Eight ranked cyclic flats determine all 512 subset ranks. The verification chain checks rank normalization, monotonicity, all submodularity inequalities, simplicity, flats and covers, and an independent reconstruction of the 67 bases. Exact rational atom spaces and $D_{\beta}$ cover matrices produce the graded dimensions through column-space recursion. Disabling $D_{\beta}$ changes the dimensions and is rejected. The concrete finite statement is reported in two independently structured mechanized developments.

</details>

两条循环二阶直线上的主要延伸部分会产生参数 $a,d\geq 0$，并保留原有公式


<details>
<summary>英文原文</summary>

Principal extensions along two cyclic rank-two lines produce parameters $a,d\geq 0$ with retained formula

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0419)

**表格与文字对照**

```text
| $\begin{split}H_{\beta}=\big(&1,9+a+d,31+6(a+d)+ad,\\
&32+6(a+d)+ad,9+a+d,1\big).\end{split}$ | | (S26)

表内文字对照（数值与原始行列保持不变）：
begin → 开始
split → 分割
beta → beta
big( → big(
big) → 大型）
end → 结束
```


<details>
<summary>英文原文</summary>

| $\begin{split}H_{\beta}=\big(&1,9+a+d,31+6(a+d)+ad,\\
&32+6(a+d)+ad,9+a+d,1\big).\end{split}$ | | (S26)

</details>

该中间缺陷在整个家族中始终存在 $-1$。两种完全一致的实现方式支持该家族公式，而具体的 Lean 反例并未涉及这一点。


<details>
<summary>英文原文</summary>

The middle defect remains $-1$ throughout the family. Two exact implementations support the family formula, which is not covered by the concrete Lean counterexample.

</details>

### J.2.1 从组合对象到希尔伯特级数反例


<details>
<summary>英文原文</summary>

J.2.1 From a combinatorial object to a Hilbert-series counterexample

</details>

反例从一个拟阵开始，而不是从任意提出的系数序列开始。如果某个违反前置加载的序列是由应用于有效拟阵的径向构造产生的，那么该序列才具有相关性。因此，验证者首先使用子集秩函数，在构建分级算子之前先检验拟阵公理。对于包含九个元素的基集来说，512个子集域是完备的。


<details>
<summary>英文原文</summary>

The counterexample begins with a matroid, not with an arbitrary proposed coefficient sequence. A sequence violating front-loading is relevant only if it is produced by the radial construction applied to a valid matroid. The verifier therefore starts with the subset-rank function and checks the matroid axioms before building the graded operators. The 512-subset domain is exhaustive for a nine-element ground set.

</details>

排名标准化、单调性与次模性具有不同的作用。标准化用于修正空集排名和基本边界；单调性用于控制包含关系；次模性则确保排名函数具备所需的交换结构。根据既定规则，简单性要求排除循环和并行元素。独立基重建机制可验证所得到的组合对象与所报告的67个基一致，而不仅仅与缓存的平面列表一致。


<details>
<summary>英文原文</summary>

Rank normalization, monotonicity, and submodularity serve different purposes. Normalization fixes the empty-set rank and basic bounds; monotonicity controls inclusions; submodularity ensures the rank function has the required exchange structure. Simplicity excludes loops and parallel elements under the stated convention. The independent basis reconstruction checks that the resulting combinatorial object agrees with the reported 67 bases rather than only with a cached list of flats.

</details>

代数阶段构建有理原子空间及径向降低算子。其精确的列空间递归运算可计算维度，这些维度为整数，但可能会受到某个遗漏的算子或错误的覆盖关系的影响。在奇点附近使用浮点秩估计是不恰当的。精确的有理算术与形式化有限计算能够支持所展示的 $H_{0}$、$H_{\beta}$及其差值。


<details>
<summary>英文原文</summary>

The algebraic stage builds rational atom spaces and the radial lowering operator. Its exact column-space recursion computes dimensions, which are integers but can be sensitive to a single omitted operator or an incorrect cover relation. Floating rank estimates near singularity would be inappropriate here. Exact rational arithmetic and the formal finite calculation support the displayed $H_{0}$ , $H_{\beta}$ , and their difference.

</details>

### J.2.2 哪个猜想性质不成立？


<details>
<summary>英文原文</summary>

J.2.2 Which conjectural property fails?

</details>

注册的中等比较值为 $31\geq 32$，比实际值少1。在差异向量中，相应的数值为4和5，两者也相差1。这两个数值缺陷不应被合并为“希尔伯特级数的所有拟议 positivity 性质均不成立”这样的结论。一个序列可以违反前置加载或对称性相关的比较规则，同时仍保持对数凹性。


<details>
<summary>英文原文</summary>

The registered middle comparison is $31\geq 32$ , which is false by one. In the difference vector the analogous entries are four and five, also separated by one. These two numerical defects should not be collapsed into a claim that every proposed positivity property of the Hilbert series fails. A sequence can violate a front-loading or symmetry-related comparison while remaining log-concave.

</details>

对于具体的 $H_{\beta}$，相邻的对数凹性检查包括 $9^{2}>1\cdot 31$、$31^{2}>9\cdot 32$、$32^{2}>31\cdot 9$ 和 $9^{2}>32\cdot 1$。因此，所提供的系数本身能够区分失败的中间比较项与对数凹性项。外部来源使用微分度语言，因此该规范与本文中系数索引之间的映射仍需进行明确的对齐处理。


<details>
<summary>英文原文</summary>

For the concrete $H_{\beta}$ , the neighboring log-concavity checks include $9^{2}>1\cdot 31$ , $31^{2}>9\cdot 32$ , $32^{2}>31\cdot 9$ , and $9^{2}>32\cdot 1$ . Thus the supplied coefficients themselves separate the failed middle comparison from log-concavity. The external source uses differential-degree language, so the map between that convention and the coefficient indexing in this manuscript remains an explicit alignment requirement.

</details>

### J.2.3 为何无限家族会增加信息


<details>
<summary>英文原文</summary>

J.2.3 Why the infinite family adds information

</details>

撰写 $s=a+d$ 。扩展族公式中的中间项分别为 $31+6s+ad$ 和 $32+6s+ad$ 。通过相减可以消除所有参数依赖的贡献，最终得到 $-1$ 。因此，该缺陷在注册的主要扩展下具有结构稳定性。这比单一异常目录项更能证明其失效机制。


<details>
<summary>英文原文</summary>

Write $s=a+d$ . The middle entries of the extension-family formula are $31+6s+ad$ and $32+6s+ad$ . Subtracting cancels every parameter-dependent contribution and leaves $-1$ . The defect is therefore structurally stable under the registered principal extensions. This is stronger evidence about the failure mechanism than a single exceptional catalogue entry.

</details>

这个两参数公式是通过归纳法从扩展增量中推导出来的。将 $a$ 增加一，会使系数向量发生变化


<details>
<summary>英文原文</summary>

The two-parameter formula follows inductively from the extension increments. Increasing $a$ by one changes the coefficient vector by

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0431)

**表格与文字对照**

```text
| $(0,1,6+d,6+d,1,0),$ | | (S27)
```


<details>
<summary>英文原文</summary>

| $(0,1,6+d,6+d,1,0),$ | | (S27)

</details>

当将 $d$ 增加一时，其变化量为 $(0,1,6+a,6+a,1,0)$ 。从 $H_{\beta}(0,0)=(1,9,31,32,9,1)$ 开始，对第一个递推式进行 $a$ 次运算，对第二个进行 $d$ 次运算后可得


<details>
<summary>英文原文</summary>

while increasing $d$ by one changes it by $(0,1,6+a,6+a,1,0)$ . Starting from $H_{\beta}(0,0)=(1,9,31,32,9,1)$ , summing the first recurrence $a$ times and the second $d$ times gives

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0433)

**表格与文字对照**

```text
| $H_{\beta}(a,d)=\bigl(1,9+a+d,31+6(a+d)+ad,32+6(a+d)+ad,9+a+d,1\bigr).$ | | (S28)

表内文字对照（数值与原始行列保持不变）：
beta → beta
bigl( → bigl(
bigr) → bigr)
```


<details>
<summary>英文原文</summary>

| $H_{\beta}(a,d)=\bigl(1,9+a+d,31+6(a+d)+ad,32+6(a+d)+ad,9+a+d,1\bigr).$ | | (S28)

</details>

两个中间坐标在每次扩展步骤中都会获得完全相同的增量，因此它们之间的差值是一个不变量 $-1$ 。这证明了一旦从基阵构造中建立了主要扩展递归，其持久性便得以确立。


<details>
<summary>英文原文</summary>

Both middle coordinates receive exactly the same increment at every extension step, so their difference is the invariant $-1$ . This proves persistence once the principal-extension recurrences are established from the matroid construction.

</details>

该族公式及其构造与具体的九元素案例具有不同的证据要求。必须证明每一个允许的扩展都能产生所声称的拟阵结构，并且径向希尔伯特计算符合所提出的公式。具体的Lean定理并未对这些扩展参数进行量化。该论文将该族公式归因于所提供的精确实现和书面论证，而有限反例则保留完整的形式化地位。


<details>
<summary>英文原文</summary>

The family formula and its construction are nevertheless different evidence obligations from the concrete nine-element case. One must show that every permitted extension produces the claimed matroid structure and that the radial Hilbert computation obeys the stated formulas. The concrete Lean theorem does not quantify over these extension parameters. The manuscript attributes the family to the supplied exact implementations and written argument, while reserving full formal status for the finite counterexample.

</details>

### J.3 用于可逆三状态核的非负函数


<details>
<summary>英文原文</summary>

J.3 A nonnegative functional for reversible three-state kernels

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0437)

图 S8：三态功能性的边界到内部证明。精确有理图表与谱尾部确保了边界正性；混合恒等式和非负偶数迹则将其推广至内部区域。这两个分支共同在已注册的可逆三态域上建立了 $K(W)\geq 0$。


<details>
<summary>英文原文</summary>

Figure S8: Boundary-to-interior proof of the three-state functional. Exact rational charts and the spectral tail establish boundary positivity; the mixing identity and nonnegative even traces lift it through the interior. Together the two branches establish $K(W)\geq 0$ on the registered reversible three-state domain.

</details>

图 S8将两种证明接口分开。这种分解方式使得在保持其分析覆盖义务可见的同时，能够检查大型精确证书。


<details>
<summary>英文原文</summary>

Figure S8 separates the two proof interfaces. This decomposition makes it possible to inspect large exact certificates while keeping their analytic coverage obligations visible.

</details>

设 $J$ 为一个对称的非负 $3\times 3$ 耦合结构，其总质量等于一，且各行和均为正数 $\pi_{i}$ 。定义 $P_{ij}=J_{ij}/\pi_{i}$ 和 $A=P-\mathbf{1}\pi^{\top}$ 。所保留的定理为


<details>
<summary>英文原文</summary>

Let $J$ be a symmetric nonnegative $3\times 3$ coupling of total mass one with positive row sums $\pi_{i}$ . Define $P_{ij}=J_{ij}/\pi_{i}$ and $A=P-\mathbf{1}\pi^{\top}$ . The retained theorem is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0440)

**表格与文字对照**

```text
| $\begin{split}K(J)={}&2\sum_{i,j}\frac{J_{ij}}{\pi_{j}^{2}}(A^{3})_{ij}(A^{5})_{ij}+13\tr(A^{8})\\
&+16\tr(A^{4})^{2}+252\tr(A^{6})\geq 0.\end{split}$ | | (S29)

表内文字对照（数值与原始行列保持不变）：
begin → 开始
split → 分割
K(J) → K(J)
sum_ → sum_
frac → 分数
pi_ → pi_
tr(A → tr(A)
geq → geq
end → 结束
```


<details>
<summary>英文原文</summary>

| $\begin{split}K(J)={}&2\sum_{i,j}\frac{J_{ij}}{\pi_{j}^{2}}(A^{3})_{ij}(A^{5})_{ij}+13\tr(A^{8})\\
&+16\tr(A^{4})^{2}+252\tr(A^{6})\geq 0.\end{split}$ | | (S29)

</details>

对于严格正性的 $J$ 和非恒定归一化核 $W_{ij}=J_{ij}/(\pi_{i}\pi_{j})$，所保留的命题仍为严格正性。源文献中的相关 sharp-10 稳定性结果适用于其居中秩一型及可聚合族；在此处未在其完整的函数定义下进行推广。


<details>
<summary>英文原文</summary>

For strictly positive $J$ and nonconstant normalized kernel $W_{ij}=J_{ij}/(\pi_{i}\pi_{j})$ , the retained claim is strict positivity. Related sharp-10 stability results in the source material apply to its centered rank-one and lumpable families; they are not generalized here without their full functional definitions.

</details>

### 混合减少。


<details>
<summary>英文原文</summary>

Mixing reduction.

</details>

让 $m=\min_{ij}W_{ij}$ 和 $\lambda=1-m$ 成立。对于 $\lambda>0$ ，写出 $W=(1-\lambda)+\lambda W_{0}$ ，其中 $W_{0}$ 是非负的，且包含一个零项，并且具有相同的加权归一化。确切的等式关系为


<details>
<summary>英文原文</summary>

Let $m=\min_{ij}W_{ij}$ and $\lambda=1-m$ . For $\lambda>0$ , write $W=(1-\lambda)+\lambda W_{0}$ , where $W_{0}$ is nonnegative with a zero entry and the same weighted normalization. The exact identity is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0444)

**表格与文字对照**

```text
| $\begin{split}K(W)={}&\lambda^{9}K(W_{0})+(1-\lambda)\lambda^{8}\{15\tr(A_{0}^{8})+16\tr(A_{0}^{4})^{2}\}\\
&+252(\lambda^{6}-\lambda^{9})\tr(A_{0}^{6}).\end{split}$ | | (S30)

表内文字对照（数值与原始行列保持不变）：
begin → 开始
split → 分割
K(W) → K(W)
lambda → lambda
K(W_ → K(W_
lambda) → lambda)
tr(A_ → tr(A_
end → 结束
```


<details>
<summary>英文原文</summary>

| $\begin{split}K(W)={}&\lambda^{9}K(W_{0})+(1-\lambda)\lambda^{8}\{15\tr(A_{0}^{8})+16\tr(A_{0}^{4})^{2}\}\\
&+252(\lambda^{6}-\lambda^{9})\tr(A_{0}^{6}).\end{split}$ | | (S30)

</details>

这里 $K(W)$ 表示通过其标准化核函数表达的耦合函数。可逆性使得谱为实数，因此偶数幂次轨迹均为非负值。常数核端点则单独处理。机械式混合核函数验证了这一闭合论证及端点代数性质。


<details>
<summary>英文原文</summary>

Here $K(W)$ denotes the coupling functional expressed through its normalized kernel. Reversibility makes the spectrum real, so the even-power traces are nonnegative. The constant-kernel endpoint is handled separately. The mechanized mixing kernel verifies this closure argument and endpoint algebra.

</details>

### 边界证书。


<details>
<summary>英文原文</summary>

Boundary certificate.

</details>

对于零对角边界图，在指定图选择后使用齐次参数 $(0,x,y,u,1-u,z)$，以及 $x=u^{2}(r+s)^{2}$、$y=(1-u)^{2}s^{2}$。进行设置


<details>
<summary>英文原文</summary>

For the zero-diagonal boundary chart, use homogeneous parameters $(0,x,y,u,1-u,z)$ with $x=u^{2}(r+s)^{2}$ , $y=(1-u)^{2}s^{2}$ after the stated chart choice. Set

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0448)

**表格与文字对照**

```text
| $L=2u(1-u)s(r+s),\qquad U=u(1-u)((r+s)^{2}+s^{2}).$ | | (S31)

表内文字对照（数值与原始行列保持不变）：
u)s(r → u)s(r
qquad U → qquad U
u)((r → u)((r
```


<details>
<summary>英文原文</summary>

| $L=2u(1-u)s(r+s),\qquad U=u(1-u)((r+s)^{2}+s^{2}).$ | | (S31)

</details>

对于 $0\leq z\leq L$，一个包含 62,151 项的多项式证书使用 4,478 次精确配对来吸收 3,583 个负单项式。对于 $L\leq z\leq U$，一个包含 29,864 项的源多项式转化为 141,621 个正非零系数。$z\geq U$ 的谱尾部则使用


<details>
<summary>英文原文</summary>

For $0\leq z\leq L$ , a 62,151-term polynomial certificate uses 4,478 exact pairings to absorb 3,583 negative monomials. For $L\leq z\leq U$ , a 29,864-term source polynomial transforms to 141,621 positive nonzero coefficients. The $z\geq U$ spectral tail uses

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0450)

**表格与文字对照**

```text
| $K\geq 250\tr(A^{6})+15\tr(A^{8})+16\tr(A^{4})^{2}\geq 0.$ | | (S32)

表内文字对照（数值与原始行列保持不变）：
geq → geq
tr(A → tr(A)
```


<details>
<summary>英文原文</summary>

| $K\geq 250\tr(A^{6})+15\tr(A^{8})+16\tr(A^{4})^{2}\geq 0.$ | | (S32)

</details>

不同的实现方式在同质化、替换、坐标排序以及变换方面存在差异。破坏配对或谱系数的情况将被拒绝。这里的图表讨论仅作为证明大纲；所提供的完整边界包包含全部案例覆盖，包括其余的边界配置。草案中并未嵌入这些完整的证书文件。


<details>
<summary>英文原文</summary>

Independent implementations vary homogenization, substitution, coordinate ordering, and transforms. Corrupting pairings or a spectral coefficient is rejected. The chart discussion here is a proof outline; the supplied exact boundary package carries the full case coverage, including remaining boundary configurations. The draft does not have those complete certificate files embedded.

</details>

该结果涉及三种状态，而非任意的图灵机或任意状态二阶核。大型有理边界证书仍属于完整的 Lean 反射范畴之外。


<details>
<summary>英文原文</summary>

The result concerns three states, not arbitrary graphons or arbitrary-state rank-two kernels. Large rational boundary certificates remain outside full Lean reflection.

</details>

### J.3.1 可逆性与谱非负性


<details>
<summary>英文原文</summary>

J.3.1 Reversibility and spectral nonnegativity

</details>

让 $D=\operatorname{diag}(\pi)$ 。可逆性使得 $DP=P^{\top}D$ ，因此 $D^{1/2}PD^{-1/2}$ 是对称的。中心化矩阵 $A=P-\mathbf{1}\pi^{\top}$ 也类似于对称矩阵。其特征值为实数，对于每一个正整数 $r$ ， $\tr(A^{2r})$ 是非负偶数次幂之和。这就是混合与尾部论证所使用的谱输入。


<details>
<summary>英文原文</summary>

Let $D=\operatorname{diag}(\pi)$ . Reversibility gives $DP=P^{\top}D$ , so $D^{1/2}PD^{-1/2}$ is symmetric. The centered matrix $A=P-\mathbf{1}\pi^{\top}$ is similar to a symmetric matrix as well. Its eigenvalues are real, and for every positive integer $r$ , $\tr(A^{2r})$ is the sum of nonnegative even powers. This is the spectral input used by the mixing and tail arguments.

</details>

归一化值 $W_{ij}=J_{ij}/(\pi_{i}\pi_{j})$ 满足 $\sum_{j}\pi_{j}W_{ij}=1$ 的要求。因此，最小项 $m$ 不得超过一。从每个项中减去 $m$ 后再除以 $1-m$，当 $m<1$ 时便得到另一个具有零项的非负归一化核。当 $m=1$ 时，加权行归一化会强制生成常数核，该情况作为终点处理，而非通过除以零的方式解决。


<details>
<summary>英文原文</summary>

The normalization $W_{ij}=J_{ij}/(\pi_{i}\pi_{j})$ satisfies $\sum_{j}\pi_{j}W_{ij}=1$ . Hence the minimum entry $m$ cannot exceed one. Subtracting $m$ from every entry and dividing by $1-m$ when $m<1$ gives another nonnegative normalized kernel with a zero entry. When $m=1$ , weighted row normalization forces the constant kernel, which is handled as the endpoint rather than through division by zero.

</details>

在混合状态下，中心化算子按 $A=\lambda A_{0}$ 进行缩放。因此，在 $K$ 中的大多数项都按其矩阵阶数进行缩放。包含 $J_{ij}$ 的项则分为常数核贡献和 $W_{0}$ 贡献两部分，从而产生公式中的八阶和九阶分量。追踪这些阶数可以解释为何错误的系数或指数会使闭合论证失效。


<details>
<summary>英文原文</summary>

Under the mixture $W=(1-\lambda)+\lambda W_{0}$ , the centered operator scales as $A=\lambda A_{0}$ . Most terms in $K$ therefore scale by their matrix degree. The term containing $J_{ij}$ separates into a constant-kernel contribution and a $W_{0}$ contribution, producing the degree-eight and degree-nine pieces in the exact formula. Tracking these degrees explains why an incorrect coefficient or exponent would invalidate the closure argument.

</details>

### J.3.2 严格性与有限的图密度桥梁


<details>
<summary>英文原文</summary>

J.3.2 Strictness and the limited graph-density bridge

</details>

对于完全正的非常数核，即 $0<\lambda<1$ 和 $A_{0}\neq 0$。与对称矩阵的相似性意味着 $\tr(A_{0}^{6})>0$。由于 $\lambda^{6}(1-\lambda^{3})>0$ 的作用，最后的混合项严格为正。一旦边界非负性得到确认，便可推导出严格的内部正性。这是一个精确的充分条件链，而非依赖于采样内部点的数值正性。


<details>
<summary>英文原文</summary>

For a fully positive nonconstant kernel, $0<\lambda<1$ and $A_{0}\neq 0$ . Similarity to a symmetric matrix implies $\tr(A_{0}^{6})>0$ . The last mixing term is then strictly positive because $\lambda^{6}(1-\lambda^{3})>0$ . Once boundary nonnegativity is established, this yields strict interior positivity. This is a precise sufficient chain, not an appeal to numerical positivity at sampled interior points.

</details>

所提供的来源将 $K$ 与用于 $K_{5,5}-C_{10}$ 图密度展开中的特定系数相关联。该系数的非负性并不必然意味着整个图密度差异在所有核上也是非负的。sharp-10 结果利用了以中心化秩一或可聚合族为基的额外结构。该论文保留了这一边界，以避免将完整的三状态系数定理推广到一般的 Sidorenko理论。


<details>
<summary>英文原文</summary>

The supplied source relates $K$ to a particular coefficient in a graph-density expansion for $K_{5,5}-C_{10}$ . Nonnegativity of that coefficient is not automatically nonnegativity of the whole graph-density difference on every kernel. The sharp-10 results use additional structure on centered rank-one or lumpable families. The manuscript preserves this boundary to avoid promoting a complete three-state coefficient theorem into general Sidorenko.

</details>

### J.3.3 确切的正性证明必须包含哪些内容


<details>
<summary>英文原文</summary>

J.3.3 What an exact positivity certificate must establish

</details>

合理的证明需满足三项独立要求。首先，在仅清除图表中已知为正数的分母后，从原始函数式中重构出正确的分子。其次，证明该图表及其不等式关系能够覆盖指定的边界区域。第三，精确展开所提出的非负块，并说明它们的总和等于该分子。若通过错误的代换产生的多项式中的系数为正，则无法验证该定理。


<details>
<summary>英文原文</summary>

A rational certificate has three independent obligations. First, reconstruct the correct numerator from the original functional after clearing only denominators known to be positive in the chart. Second, prove the chart and its inequalities cover the assigned boundary region. Third, expand the proposed nonnegative blocks exactly and show that their sum equals that numerator. Positive coefficients in a polynomial produced by an incorrect substitution would not establish the theorem.

</details>

所提供的边界证明将零非对角面与零对角面分开处理，同时涵盖有界代数区域和无界谱尾部。之前提到的具体尺寸仅针对零对角分支，而非所有面。下限阈值 $L$ 和上限阈值 $U$ 在注册的非负图表中满足 $U-L=u(1-u)r^{2}\geq 0$ 条件，因此中间区间是有序的。在 $u=0,1$ 及其他退化分母情况下，必须通过分支收缩来处理，而非直接删除。


<details>
<summary>英文原文</summary>

The supplied boundary proof separates zero-off-diagonal and zero-diagonal faces, then treats bounded algebraic regions and an unbounded spectral tail. The detailed sizes quoted earlier concern the zero-diagonal branch, not every face. The lower threshold $L$ and upper threshold $U$ satisfy $U-L=u(1-u)r^{2}\geq 0$ in the registered nonnegative chart, so the middle interval is well ordered. Coverage at $u=0,1$ and other degenerate denominators must be handled by the branch contract rather than silently removed.

</details>

加权配对与Bernstein变换只有在完全重构之后才能成为有效证明。浮点优化可能发现具有积极意义的非负块系数；合理化操作则可能会改变其身份或正性属性。独立展开与删除配对控制检验能够准确识别从数值提议到精确对象的这种转变过程。这些大分支证明的完整Lean反射分析仍处于领先水平。


<details>
<summary>英文原文</summary>

Weighted pairings and Bernstein transformations are certificates only after exact reconstruction. Floating optimization may find promising nonnegative block coefficients; rationalization can change identities or positivity. The independent expansion and deleted-pairing control check precisely this transition from a numerical proposal to an exact object. Full Lean reflection of these large branch certificates is still outstanding.

</details>

### J.4 对称大重心排名与完整佩拉佐排名


<details>
<summary>英文原文</summary>

J.4 Symmetric Big-centroid and Full Perazzo ranks

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0465)

图 S9：在代数闭包特征零域上保留完整的 Perazzo 公式所产生的结果，标记为 $q=\binom{n+d-2}{d-1}$。 (a) 从普通秩到边界秩的比率 $dq/(q+n)$ 随着 $d$ 的增长趋近于度 $n$（虚线表示）。 (b) 对于三次多项式，这些公式分别给出了不同的边界秩和普通秩增长情况。曲线是根据所提出的候选公式计算得出的，并非独立测量的秩；其有效性取决于该构造及下限论证的合理性。


<details>
<summary>英文原文</summary>

Figure S9: Consequences of the retained Full Perazzo formulas over an algebraically closed characteristic-zero field, with $q=\binom{n+d-2}{d-1}$ . (a) The ordinary-to-border ratio $dq/(q+n)$ approaches the degree $d$ (dashed lines) as $n$ grows. (b) For cubics, the formulas give distinct border and ordinary rank growth. Curves are calculated from the stated candidate formulas, not independently measured ranks; their validity depends on the construction and matching lower-bound arguments.

</details>

图 S9展示了两种不同排名证明所导致的量化差异。边界退化与普通排名分解不能被视为同一个对象。


<details>
<summary>英文原文</summary>

Figure S9 visualizes the quantitative gap that the two different rank proofs imply. The border degeneration and the ordinary-rank decomposition cannot be counted as the same object.

</details>

在特征为零的代数闭域上，取 $n\geq 2$、$d\geq 3$ 以及


<details>
<summary>英文原文</summary>

Over an algebraically closed field of characteristic zero, take $n\geq 2$ , $d\geq 3$ , and

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0468)

**表格与文字对照**

```text
| $q=\binom{n+d-2}{d-1},\qquad B_{n,d}(X,Y)=\sum_{|\alpha|=d-1}X_{\alpha}Y^{\alpha}.$ | | (S33)

表内文字对照（数值与原始行列保持不变）：
binom → binom
qquad B_ → qquad B_
sum_ → sum_
alpha → alpha
```


<details>
<summary>英文原文</summary>

| $q=\binom{n+d-2}{d-1},\qquad B_{n,d}(X,Y)=\sum_{|\alpha|=d-1}X_{\alpha}Y^{\alpha}.$ | | (S33)

</details>

保留的排名公式是


<details>
<summary>英文原文</summary>

The retained rank formulas are

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0470)

**表格与文字对照**

```text
| $\brank(B_{n,d})=\brank_{\mathrm{W}}(B_{n,d})=q+n,\qquad R_{\mathrm{W}}(B_{n,d})=dq.$ | | (S34)

表内文字对照（数值与原始行列保持不变）：
brank(B_ → brank(B_)
brank_ → brank_
mathrm → mathrm
qquad R_ → qquad R_
```


<details>
<summary>英文原文</summary>

| $\brank(B_{n,d})=\brank_{\mathrm{W}}(B_{n,d})=q+n,\qquad R_{\mathrm{W}}(B_{n,d})=dq.$ | | (S34)

</details>

在表示中区分了普通张量边界秩和对称 Waring 边界秩；共享的上界源于对称退化，同时也有相应的扁平化下界。


<details>
<summary>英文原文</summary>

Ordinary tensor border rank and symmetric Waring border rank are distinguished in the notation; the shared upper bound follows from a symmetric degeneration, with a matching flattening lower bound.

</details>

### 柯西-星型插值。


<details>
<summary>英文原文</summary>

Cauchy-star interpolation.

</details>

选择两两不同的标量 $c_{1},\ldots,c_{n},t_{1},\ldots,t_{n+d-2}$ 。设置 $g(z)=\prod_{i}(z-c_{i})$、$p(z)=\prod_{j}(z-t_{j})$ 和 $A_{j}(Z)=\sum_{i}Z_{i}/(t_{j}-c_{i})$。对于 $(n-1)$ 索引中的某个 $I$-子集 $t$，进行定义


<details>
<summary>英文原文</summary>

Choose pairwise distinct scalars $c_{1},\ldots,c_{n},t_{1},\ldots,t_{n+d-2}$ . Set $g(z)=\prod_{i}(z-c_{i})$ , $p(z)=\prod_{j}(z-t_{j})$ , and $A_{j}(Z)=\sum_{i}Z_{i}/(t_{j}-c_{i})$ . For an $(n-1)$ -subset $I$ of the $t$ indices, define

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0474)

**表格与文字对照**

```text
| $(v_{I})_{i}=\frac{\prod_{j\in I}(c_{i}-t_{j})}{g^{\prime}(c_{i})},\quad\ell_{I}(Y)=\sum_{i}(v_{I})_{i}Y_{i},\quad H_{I}(Z)=\prod_{j\notin I}A_{j}(Z).$ | | (S35)

表内文字对照（数值与原始行列保持不变）：
frac → 分数
prod_ → prod_
in I → 在 I 中
prime → 主要
quad → quad
ell_ → ell_
sum_ → sum_
quad H_ → quad H_
notin I → notin I
```


<details>
<summary>英文原文</summary>

| $(v_{I})_{i}=\frac{\prod_{j\in I}(c_{i}-t_{j})}{g^{\prime}(c_{i})},\quad\ell_{I}(Y)=\sum_{i}(v_{I})_{i}Y_{i},\quad H_{I}(Z)=\prod_{j\notin I}A_{j}(Z).$ | | (S35)

</details>

部分分式法


<details>
<summary>英文原文</summary>

Partial fractions give

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0476)

**表格与文字对照**

```text
| $\sum_{i}\frac{(v_{I})_{i}}{z-c_{i}}=\frac{\prod_{j\in I}(z-t_{j})}{g(z)}.$ | | (S36)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
frac → 分数
z-c_ → z-c_
prod_ → prod_
in I → 在 I 中
z-t_ → z-t_
g(z) → g(z)
```


<details>
<summary>英文原文</summary>

| $\sum_{i}\frac{(v_{I})_{i}}{z-c_{i}}=\frac{\prod_{j\in I}(z-t_{j})}{g(z)}.$ | | (S36)

</details>

因此，$H_{I}(v_{J})=0$ 适用于 $I\neq J$，而 $H_{I}(v_{I})\neq 0$ 则如此。$q$ 构成了 $\ell_{I}^{d-1}$ 的基础。结合 $f_{i}=p(c_{i})/g^{\prime}(c_{i})$ 和 $\lambda_{I}=(-1)^{d-1}/H_{I}(v_{I})$，所保留的插值公式成立。


<details>
<summary>英文原文</summary>

Hence $H_{I}(v_{J})=0$ for $I\neq J$ , while $H_{I}(v_{I})\neq 0$ . The $q$ powers $\ell_{I}^{d-1}$ form a basis. With $f_{i}=p(c_{i})/g^{\prime}(c_{i})$ and $\lambda_{I}=(-1)^{d-1}/H_{I}(v_{I})$ , the retained interpolation identity is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0478)

**表格与文字对照**

```text
| $\sum_{I}\lambda_{I}\ell_{I}(Y)^{d}=\sum_{i}f_{i}Y_{i}^{d}.$ | | (S37)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
lambda_ → lambda_
ell_ → ell_
```


<details>
<summary>英文原文</summary>

| $\sum_{I}\lambda_{I}\ell_{I}(Y)^{d}=\sum_{i}f_{i}Y_{i}^{d}.$ | | (S37)

</details>

求解线性形式的一阶系数恒等式 $\delta_{I}(X)$


<details>
<summary>英文原文</summary>

Solving the first-order coefficient identity for linear forms $\delta_{I}(X)$ yields

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0480)

**表格与文字对照**

```text
| $B_{n,d}=\lim_{\varepsilon\to 0}\varepsilon^{-1}\left[\sum_{I}\lambda_{I}(\ell_{I}+\varepsilon\delta_{I})^{d}-\sum_{i}f_{i}Y_{i}^{d}\right].$ | | (S38)

表内文字对照（数值与原始行列保持不变）：
lim_ → lim_
varepsilon → ε
left → 左侧
sum_ → sum_
lambda_ → lambda_
ell_ → ell_
delta_ → delta_
right → 正确
```


<details>
<summary>英文原文</summary>

| $B_{n,d}=\lim_{\varepsilon\to 0}\varepsilon^{-1}\left[\sum_{I}\lambda_{I}(\ell_{I}+\varepsilon\delta_{I})^{d}-\sum_{i}f_{i}Y_{i}^{d}\right].$ | | (S38)

</details>

这些独立的 $q$ 派生项与独立的 $X_{\alpha}$ 派生项具有互补性等级：前者属于纯粹度范畴，而后者则包含不同的术语。


<details>
<summary>英文原文</summary>

The $q$ independent $X_{\alpha}$ derivatives and $n$ independent $Y_{i}$ derivatives give catalecticant rank $q+n$ : the former lie in pure $Y$ degree, while the latter contain distinct $X_{(d-1)e_{i}}Y_{i}^{d-2}$ terms.

</details>

### 普通华林等级。


<details>
<summary>英文原文</summary>

Ordinary Waring rank.

</details>

保留的 Schur–Kneser 论证适用于 $F=\sum_{i}X_{i}Q_{i}(Y)+G(Y)$，并得出 $R_{\mathrm{W}}(F)\geq d\rho$，其中 $\rho=\dim\operatorname{span}\{Q_{i}\}$。它利用了消失的二阶 $X$ 导数、按坐标分组的乘积空间的正交性、同时稳定化块，以及每个块中的 Kneser 维数限制。对于 Full Perazzo，则为 $\rho=q$。相应的上界将每个二元切形式分解为


<details>
<summary>英文原文</summary>

The retained Schur–Kneser argument for $F=\sum_{i}X_{i}Q_{i}(Y)+G(Y)$ gives $R_{\mathrm{W}}(F)\geq d\rho$ , where $\rho=\dim\operatorname{span}\{Q_{i}\}$ . It uses vanishing second $X$ derivatives, orthogonality of coordinatewise product spaces, simultaneous stabilizer blocks, and a Kneser dimension bound in each block. For Full Perazzo, $\rho=q$ . The matching upper bound decomposes each binary tangent form as

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0484)

**表格与文字对照**

```text
| $WL^{d-1}=\sum_{j=1}^{d}\mu_{j}(L+t_{j}W)^{d}$ | | (S39)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
mu_ → mu_
```


<details>
<summary>英文原文</summary>

| $WL^{d-1}=\sum_{j=1}^{d}\mu_{j}(L+t_{j}W)^{d}$ | | (S39)

</details>

在相应的时刻方程下。一种机械式二元切线核证明了特征为零域上的代数恒等式；它并未形式化完整的Schur–Kneser下界链，也无法自动保证所有插值假设。对于固定的$dq/(q+n)\to d$，所得到的比率$d$则导致了该族中更小的通用线性去偏差系数的存在障碍。仍需进行外部代数几何及优先级审查；并不声称能实现完全的边界-VSP分类。


<details>
<summary>英文原文</summary>

under the corresponding moment equations. A mechanized binary-tangent kernel proves that algebraic identity over a characteristic-zero field; it does not formalize the full Schur–Kneser lower-bound chain or guarantee every interpolation hypothesis automatically. The resulting ratio $dq/(q+n)\to d$ for fixed $d$ gives the stated obstruction to a smaller universal linear debordering coefficient on this family. External algebraic-geometric and priority review remains necessary; full border-VSP classification is not claimed.

</details>

### J.4.1 为什么插值族具有恰好所需的规模


<details>
<summary>英文原文</summary>

J.4.1 Why the interpolation family has exactly the required size

</details>

存在 $\binom{n+d-2}{n-1}=q$ 个大小为 $I$ 的子集 $n-1$ ，其维度与 $d-1$ 变量中齐次度 $n$ 形式的维度相匹配。每个 $H_{I}$ 还具有 $d-1$ 度，因为其乘积包含 $d-1$ 个被省略的 $t$ 索引。因此，对角评估矩阵 $H_{I}(v_{J})$ 体现了插值效应，而不仅仅是提供众多候选线性形式。


<details>
<summary>英文原文</summary>

There are $\binom{n+d-2}{n-1}=q$ subsets $I$ of size $n-1$ , matching the dimension of homogeneous degree- $d-1$ forms in $n$ variables. Each $H_{I}$ also has degree $d-1$ , because its product contains $d-1$ omitted $t$ indices. The diagonal evaluation matrix $H_{I}(v_{J})$ therefore witnesses interpolation rather than merely supplying many candidate linear forms.

</details>

如果 $I\neq J$ 的大小相等，则 $J$ 中的某些索引在 $I$ 中不存在。该索引出现在定义 $H_{I}$ 的乘积中，而部分分式恒等式使得相应的因子在 $v_{J}$ 处消失。在对角线上，两两不同的参数条件阻止了必要因子的消失。这就解释了非对角线上为零的模式以及对角线上的非零值，无需依赖有限的符号示例。


<details>
<summary>英文原文</summary>

If $I\neq J$ have equal size, some index in $J$ is absent from $I$ . That index occurs in the product defining $H_{I}$ , and the partial-fraction identity makes the corresponding factor vanish at $v_{J}$ . On the diagonal, the pairwise-distinct parameter condition prevents the necessary factors from vanishing. This explains the off-diagonal zero pattern and the nonzero diagonal without relying on a finite symbolic example.

</details>

$\ell_{I}^{d-1}$的基础性质使得$X_{\alpha}Y^{\alpha}$目标可以在第$d$次的幂的正切范数中表达。随后，常数恒等式便消除了度为零的部分。该域必须支持用于正切构造的标量运算和度因子；因此，所展示的Waring命题是在零特征下得出的，而非随意转移到小特征下。


<details>
<summary>英文原文</summary>

The basis property of $\ell_{I}^{d-1}$ lets the $X_{\alpha}Y^{\alpha}$ target be expressed in the tangent span of the $d$ th powers. The constant identity then cancels the degree-zero part. The field must allow the scalar operations and degree factors used in the tangent construction; the displayed Waring statement is therefore made in characteristic zero rather than casually transferred to small characteristic.

</details>

### J.4.2 扁平化下界与普通秩是不同的概念


<details>
<summary>英文原文</summary>

J.4.2 Flattening lower bound and ordinary rank are different arguments

</details>

$B_{n,d}$的第一导数空间具有 $q+n$维数。关于 $X$变量的导数涵盖了 $Y$中所有度数为 $d-1$的单项式。关于 $Y$变量的导数具有正 $X$度数，并通过上述指定的特殊项相互独立。这两个子空间的维度不同，且仅存在平凡交集。秩为一的对称张量最多贡献一个维度到这种展平过程中，因此该维度给出了一个边界秩的下界。


<details>
<summary>英文原文</summary>

The first derivative space of $B_{n,d}$ has dimension $q+n$ . Derivatives with respect to the $X$ variables span all degree- $d-1$ monomials in $Y$ . Derivatives with respect to the $Y$ variables have positive $X$ degree and are independent through the distinguished terms specified above. The two subspaces have different $X$ degrees and intersect trivially. A rank-one symmetric tensor contributes at most one dimension to this flattening, so the dimension gives a border-rank lower bound.

</details>

该下界无法产生更大的普通 Waring 秩 $dq$。普通秩需要更强的乘积空间论证。在任何提出的分解中，$X$变量中的消失二阶导数会产生系数向量按坐标排列的乘积之间的代数关系。保留的 Schur–Kneser 证明通过稳定器块来组织这些关系，并汇总由此产生的块下界。其依赖关系和等式假设需要专业验证；仅二元切线恒等式本身无法确立该下界。


<details>
<summary>英文原文</summary>

That lower bound does not produce the larger ordinary Waring rank $dq$ . Ordinary rank needs the stronger product-space argument. In any proposed decomposition, vanishing second derivatives in the $X$ variables creates algebraic relations among coordinatewise products of coefficient vectors. The retained Schur–Kneser proof organizes these relations by stabilizer blocks and sums the resulting block lower bounds. Its dependencies and equality hypotheses require specialist verification; the binary tangent identity alone cannot establish the lower bound.

</details>

高级普通等级构造采用不同的计数方式：每个 $q$ 切线单项式都用 $d$ 次幂表示，从而产生 $dq$ 项。将这一明确的上界与独立的下界进行匹配后可得等式关系。区分这两种证明方式，可避免将边界构造误认为是长度为 $q+n$ 的有限精确分解。


<details>
<summary>英文原文</summary>

The upper ordinary-rank construction uses a different count: each of the $q$ tangent monomials is expressed using $d$ powers, yielding $dq$ terms. Matching this explicit upper bound with the independent lower bound yields equality. Distinguishing the two proofs prevents the border construction from being mistaken for a finite exact decomposition of length $q+n$ .

</details>

### J.4.3 二元切线恒等式与去边界化解释


<details>
<summary>英文原文</summary>

J.4.3 Binary tangent identity and debordering interpretation

</details>

扩展所提出的模块


<details>
<summary>英文原文</summary>

Expanding a proposed block gives

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0496)

**表格与文字对照**

```text
| $\sum_{j}\mu_{j}(L+t_{j}W)^{d}=\sum_{k=0}^{d}\binom{d}{k}L^{d-k}W^{k}\sum_{j}\mu_{j}t_{j}^{k}.$ | | (S40)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
mu_ → mu_
binom → binom
d-k → d-k
```


<details>
<summary>英文原文</summary>

| $\sum_{j}\mu_{j}(L+t_{j}W)^{d}=\sum_{k=0}^{d}\binom{d}{k}L^{d-k}W^{k}\sum_{j}\mu_{j}t_{j}^{k}.$ | | (S40)

</details>

为了获得 $WL^{d-1}$，其矩必须满足 $d\sum_{j}\mu_{j}t_{j}=1$，并且使所有其他相关矩消失。Lean 核心根据提供的矩条件来验证这一蕴含关系。选择合适的权重和参数是一个独立的代数构造，并非该蕴含关系的直接结果。


<details>
<summary>英文原文</summary>

To obtain $WL^{d-1}$ , its moments must satisfy $d\sum_{j}\mu_{j}t_{j}=1$ and make every other relevant moment vanish. The Lean kernel checks this implication from the supplied moment conditions. Existence of a suitable choice of weights and parameters is a separate algebraic construction, not a consequence of the implication alone.

</details>

在代数闭域且特征为零的情况下，该存在性可以明确表述。设 $\zeta$ 为第 $d$ 个本原单位根，并令 $t_{j}=\zeta^{j}$ 和 $\mu_{j}=\zeta^{-j}/d^{2}$ 分别对应于 $0\leq j<d$。单位根的正交性决定了……


<details>
<summary>英文原文</summary>

Over an algebraically closed characteristic-zero field, that existence can be written explicitly. Let $\zeta$ be a primitive $d$ th root of unity and set $t_{j}=\zeta^{j}$ and $\mu_{j}=\zeta^{-j}/d^{2}$ for $0\leq j<d$ . Orthogonality of roots of unity gives

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0499)

**表格与文字对照**

```text
| $\sum_{j=0}^{d-1}\mu_{j}t_{j}^{k}=\frac{1}{d^{2}}\sum_{j=0}^{d-1}\zeta^{j(k-1)}=\begin{cases}1/d,&k=1,\\
0,&0\leq k\leq d,\ k\neq 1.\end{cases}$ | | (S41)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
mu_ → mu_
frac → 分数
zeta → ζ
j(k- → j(k-
begin → 开始
cases → 案例
leq k → leq k
leq d → leq d
neq → 不等
end → 结束
```


<details>
<summary>英文原文</summary>

| $\sum_{j=0}^{d-1}\mu_{j}t_{j}^{k}=\frac{1}{d^{2}}\sum_{j=0}^{d-1}\zeta^{j(k-1)}=\begin{cases}1/d,&k=1,\\
0,&0\leq k\leq d,\ k\neq 1.\end{cases}$ | | (S41)

</details>

在二项式展开中替换后结果完全正确


<details>
<summary>英文原文</summary>

Substitution into the binomial expansion leaves exactly

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0501)

**表格与文字对照**

```text
| $WL^{d-1}=\frac{1}{d^{2}}\sum_{j=0}^{d-1}\zeta^{-j}(L+\zeta^{j}W)^{d}.$ | | (S42)

表内文字对照（数值与原始行列保持不变）：
frac → 分数
sum_ → sum_
zeta → ζ
```


<details>
<summary>英文原文</summary>

| $WL^{d-1}=\frac{1}{d^{2}}\sum_{j=0}^{d-1}\zeta^{-j}(L+\zeta^{j}W)^{d}.$ | | (S42)

</details>

因此，每个二元切线块都具有明确的 $d$ -项华林分解。将该恒等式应用于 $q$ 个独立的切线块后，便得到 $R_{\mathrm{W}}(B_{n,d})\leq dq$ 的结果，在最终的普通秩步骤中不存在插值限制。


<details>
<summary>英文原文</summary>

Thus every binary tangent block has an explicit $d$ -term Waring decomposition. Applying the identity to the $q$ independent tangent blocks gives $R_{\mathrm{W}}(B_{n,d})\leq dq$ with no interpolation limit in this final ordinary-rank step.

</details>

对于匹配下界，将假定分解写为 $F=\sum_{s=1}^{r}L_{s}^{d}$，并将每个 $L_{s}$ 拆分为其 $X$ 和 $Y$ 部分。所有第二个 $X$ 导数的消失意味着，对于所有 $X$ -方向 $a,b$，


<details>
<summary>英文原文</summary>

For the matching lower bound, write a putative decomposition as $F=\sum_{s=1}^{r}L_{s}^{d}$ and split each $L_{s}$ into its $X$ and $Y$ parts. The vanishing of every second $X$ derivative gives, for all $X$ -directions $a,b$ ,

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0504)

**表格与文字对照**

```text
| $\sum_{s=1}^{r}a(L_{s})b(L_{s})L_{s}^{d-2}=0.$ | | (S43)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
a(L_ → a(L_
b(L_ → b(L_)
```


<details>
<summary>英文原文</summary>

| $\sum_{s=1}^{r}a(L_{s})b(L_{s})L_{s}^{d-2}=0.$ | | (S43)

</details>

前几个$X$派生项覆盖了由形式$q$生成的$Q_{\alpha}(Y)=Y^{\alpha}$维空间。将相等的$Y$方向分组为稳定器块后，所呈现的二次关系便转化为对坐标乘积子空间的正交性约束。源Schur–Kneser引理规定每个块的上界为其对$d$贡献的维度乘以$\operatorname{span}\{Q_{\alpha}\}$倍；将各块相加后得到$r\geq dq$。结合显式的单位根构造，这一过程在引理所提出的特征零假设下完成了$R_{\mathrm{W}}(B_{n,d})=dq$的推导。


<details>
<summary>英文原文</summary>

The first $X$ derivatives span the $q$ -dimensional space generated by the forms $Q_{\alpha}(Y)=Y^{\alpha}$ . Grouping equal $Y$ -directions into stabilizer blocks turns the displayed quadratic relations into orthogonality constraints on coordinatewise-product subspaces. The source Schur–Kneser lemma bounds each block by $d$ times the dimension it contributes to $\operatorname{span}\{Q_{\alpha}\}$ ; summing the blocks yields $r\geq dq$ . Together with the explicit root-of-unity construction, this closes $R_{\mathrm{W}}(B_{n,d})=dq$ under the lemma’s stated characteristic-zero hypotheses.

</details>

对于固定的 $d\geq 3$，$q$ 作为 $d-1$ 次多项式在 $n$ 上增长，因此为 $n/q\to 0$。由此可推得 $dq/(q+n)\to d$。其含义是：针对特定家族的障碍，使得无法用系数低于 $d$ 的普通 Waring 分解来普遍替换边界分解。这并不能区分所有最小极限支撑结构。辅助目录中的非 CB 边界反例表明，这种更强的几何推理是错误的。


<details>
<summary>英文原文</summary>

For fixed $d\geq 3$ , $q$ grows as a polynomial of degree $d-1$ in $n$ , so $n/q\to 0$ . Consequently $dq/(q+n)\to d$ . The interpretation is a family-specific obstruction to universally replacing border decompositions by ordinary Waring decompositions with a coefficient below $d$ . It does not classify every minimal limiting support. The non-CB boundary counterexample in the auxiliary catalogue illustrates why that stronger geometric inference would be false.

</details>

### J.5 海森堡行列式限制与链依赖性


<details>
<summary>英文原文</summary>

J.5 Heisenberg determinant limits and chain dependence

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0508)

图 S10：Heisenberg 极限候选值的公式级示意图 $m=2$ 。(a) 每个点代表一个不同的奇素数主链对应的 $2^{1/(p+1)}$ 值；虚线为无限的 Fuglede–Kadison 行列式，值为 2。(b) 相应的对数缺陷为 $p\log(2)/(p+1)$ 。线条仅用于连接选定的素数参数，作为视觉指引。这些均为候选极限值，并非有限的 $q$ 测量值或数值收敛测试。


<details>
<summary>英文原文</summary>

Figure S10: Formula-level illustration of the Heisenberg limit candidate at $m=2$ . (a) Each point is $2^{1/(p+1)}$ for a different odd-prime principal chain; the dashed line is the infinite Fuglede–Kadison determinant, 2. (b) The corresponding log defect is $p\log(2)/(p+1)$ . Lines connect selected prime parameters only as visual guides. These are candidate limiting values, not finite- $q$ measurements or a numerical convergence test.

</details>

图 S10展示了所声称的链式依赖关系，但并未对那些小的有限决定因子进行外推处理。要确定每个极限值，仍然需要统一的数据包估计。


<details>
<summary>英文原文</summary>

Figure S10 exposes the claimed chain dependence without extrapolating the small finite determinant controls. Establishing each limit still requires uniform packet estimates.

</details>

在整数海森堡群中，对于整数 $A_{m}=1-ma+mb$ 设定为 $m\geq 2$。对于有限主商 $q=p^{i}$，当有限行列式非零时，通过 $D_{q}(A_{m})=|\det A_{m,q}|^{1/q^{3}}$ 定义所报告的归一化。在包含奇素数 $p$ 的保留主链假设下，候选极限为


<details>
<summary>英文原文</summary>

In the integer Heisenberg group, set $A_{m}=1-ma+mb$ for integer $m\geq 2$ . For finite principal quotients at $q=p^{i}$ , define the reported normalization by $D_{q}(A_{m})=|\det A_{m,q}|^{1/q^{3}}$ when the finite determinant is nonzero. Under the retained principal-chain hypotheses with odd prime $p$ , the candidate limit is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0511)

**表格与文字对照**

```text
| $D_{q}(A_{m})\longrightarrow m^{1/(p+1)},$ | | (S44)

表内文字对照（数值与原始行列保持不变）：
longrightarrow m → 转向 m
```


<details>
<summary>英文原文</summary>

| $D_{q}(A_{m})\longrightarrow m^{1/(p+1)},$ | | (S44)

</details>

而所引用的无限 Fuglede–Kadison行列式为 $m$。对数缺陷为 $p\log m/(p+1)$。指定的 $(p,m)=(3,2)$ 特例给出 $2^{1/4}$。这被作为 Kammeyer（2026）的行列式近似反例的精确极限后续研究呈现，而非对该原始反例的重新发现。


<details>
<summary>英文原文</summary>

whereas the cited infinite Fuglede–Kadison determinant is $m$ . The logarithmic defect is $p\log m/(p+1)$ . The designated $(p,m)=(3,2)$ special case gives $2^{1/4}$ . This is presented as an exact-limit follow-up to the determinant-approximation counterexample of Kammeyer (2026) , not as rediscovery of that original counterexample.

</details>

### 有限表示包。


<details>
<summary>英文原文</summary>

Finite representation packets.

</details>

对于精确的中心顺序 $d\mid q$，应放置 $n=q/d$。不可约包具有维度 $d$ 和参数 $(u,v)\in\mu_{n}^{2}$，并需进行常规表示维度检查


<details>
<summary>英文原文</summary>

For exact central order $d\mid q$ , put $n=q/d$ . Irreducible packets have dimension $d$ and parameters $(u,v)\in\mu_{n}^{2}$ , with regular-representation dimension check

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0515)

**表格与文字对照**

```text
| $\sum_{d\mid q}\varphi(d)n^{2}d^{2}=q^{3}.$ | | (S45)

表内文字对照（数值与原始行列保持不变）：
sum_ → sum_
mid q → 中间 q
varphi(d)n → φ(d)n
```


<details>
<summary>英文原文</summary>

| $\sum_{d\mid q}\varphi(d)n^{2}d^{2}=q^{3}.$ | | (S45)

</details>

对于奇数阶数据包，$T=\rho(a)-\rho(b)$的量子二项式与迹恒等式可得到$T^{d}=(u-v)I$及反向特征多项式，从而得出


<details>
<summary>英文原文</summary>

For odd-order packets, the quantum-binomial and trace identities for $T=\rho(a)-\rho(b)$ give $T^{d}=(u-v)I$ and the reverse characteristic polynomial, yielding

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0517)

**表格与文字对照**

```text
| $\det(I-mT)=1-m^{d}(u-v).$ | | (S46)

表内文字对照（数值与原始行列保持不变）：
det(I-mT) → det(I-mT)
u-v) → u-v)
```


<details>
<summary>英文原文</summary>

| $\det(I-mT)=1-m^{d}(u-v).$ | | (S46)

</details>

机械化有限包核证明了从反特征多项式到该行列式恒等式的推导关系。表示分类、重数、包假设以及完整的结果乘积均位于该核之外。


<details>
<summary>英文原文</summary>

The mechanized finite-packet kernel proves the implication from the reverse characteristic polynomial to this determinant identity. Representation classification, multiplicities, packet hypotheses, and the complete resultant product remain external to that kernel.

</details>

### 限制机制与控制措施。


<details>
<summary>英文原文</summary>

Limit mechanism and controls.

</details>

完整的伽罗瓦包会合并所有中心顺序。小型的 $d$ 使用非零整数范数作为下界；大型的 $d$ 则采用主项主导性和根零间距方法。统一的标准化误差估计随后提供了所声称的极限值。这些分析性估计是一个必要的证明层；仅有限的行列式一致性并不能确保收敛性。


<details>
<summary>英文原文</summary>

Complete Galois packets combine all central orders. Small $d$ use a nonzero integer norm for a lower bound; large $d$ use main-term dominance and root-of-unity spacing. Uniform normalized error estimates then supply the asserted limit. These analytic estimates are a necessary proof layer; finite determinant agreement alone does not establish convergence.

</details>

直接整数矩阵及其对应的控制项包括 $(q,m)=(3,2),(3,3),(5,2),(9,2),(2,2),(4,2),(6,2),(8,2)$，其中最大矩阵维数为 729。在偶数控制项 $(2,2)$ 处，行列式分别为 1,729 和 $-735$；为此需要采用绝对行列式约定。偶数控制项需遵循相应的数据包规则，而非对奇数阶恒等式的未经检验扩展。后续链式分类、非收敛构造以及共尾恢复声明仍属于这一专业研究领域；当前论文并未将其视为额外的独立发现。


<details>
<summary>英文原文</summary>

Direct integer matrices and resultant controls include $(q,m)=(3,2),(3,3),(5,2),(9,2),(2,2),(4,2),(6,2),(8,2)$ , with largest matrix dimension 729. The determinant is 1,729 at $(3,2)$ and $-735$ at the even control $(2,2)$ , requiring an absolute-determinant convention. Even controls use their appropriate packet rules, not an unchecked extension of the odd-order identity. Follow-up chain classifications, nonconvergence constructions, and cofinal recovery claims remain within this specialist research line; the current manuscript does not treat them as additional independent discoveries.

</details>

### J.5.1 常规表示式的重数与行列式乘积


<details>
<summary>英文原文</summary>

J.5.1 Regular-representation multiplicities and determinant products

</details>

该有限商数的阶为 $q^{3}$。其正则表示包含每一个不可约表示，且重数等于其维数。因此，在重构完整行列式时，不可约包行列式必须乘以相应的重数。恒等式 $\sum_{d\mid q}\varphi(d)n^{2}d^{2}=q^{3}$ 可确保维数正确，但完整的重构还必须保证包元素既未被遗漏也未被重复。


<details>
<summary>英文原文</summary>

The finite quotient has order $q^{3}$ . Its regular representation contains each irreducible representation with multiplicity equal to its dimension. Therefore an irreducible packet determinant must be raised to that multiplicity when reconstructing the full determinant. The identity $\sum_{d\mid q}\varphi(d)n^{2}d^{2}=q^{3}$ checks the dimension accounting, but a complete reconstruction must also ensure that the packets are neither omitted nor duplicated.

</details>

针对精确中心顺序的包序列 $\mathcal{P}_{d}$ 和 $d$、$\Delta_{d,u,v}=1-m^{d}(u-v)$ 进行写作，常规行列式具有乘积形式


<details>
<summary>英文原文</summary>

Writing $\mathcal{P}_{d}$ for the packets of exact central order $d$ and $\Delta_{d,u,v}=1-m^{d}(u-v)$ , the regular determinant has the product form

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0525)

**表格与文字对照**

```text
| $|\det A_{m,q}|=\prod_{d\mid q}\prod_{(u,v)\in\mathcal{P}_{d}}|\Delta_{d,u,v}|^{d}.$ | | (S47)

表内文字对照（数值与原始行列保持不变）：
det A_ → det A_
prod_ → prod_
mid q → 中间 q
mathcal → mathcal
Delta_ → Delta_
```


<details>
<summary>英文原文</summary>

| $|\det A_{m,q}|=\prod_{d\mid q}\prod_{(u,v)\in\mathcal{P}_{d}}|\Delta_{d,u,v}|^{d}.$ | | (S47)

</details>

因此其标准化对数为


<details>
<summary>英文原文</summary>

Consequently its normalized logarithm is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0527)

**表格与文字对照**

```text
| $\log D_{q}(A_{m})=\frac{1}{q^{3}}\sum_{d\mid q}d\sum_{(u,v)\in\mathcal{P}_{d}}\log|1-m^{d}(u-v)|.$ | | (S48)

表内文字对照（数值与原始行列保持不变）：
log D_ → log D_
frac → 分数
sum_ → sum_
mid q → 中间 q
mathcal → mathcal
log → 日志
u-v) → u-v)
```


<details>
<summary>英文原文</summary>

| $\log D_{q}(A_{m})=\frac{1}{q^{3}}\sum_{d\mid q}d\sum_{(u,v)\in\mathcal{P}_{d}}\log|1-m^{d}(u-v)|.$ | | (S48)

</details>

该公式明确指出了极限证明必须控制的因素：数据包的重复次数、主要的贡献来源，以及由于 $u-v$ 与 $m^{-d}$ 可能接近而产生的对数误差。


<details>
<summary>英文原文</summary>

This formula identifies exactly what the limit proof must control: packet multiplicities, the main $d\log m$ contribution, and the logarithmic error caused by possible proximity of $u-v$ to $m^{-d}$ .

</details>

标量身份 $\det(I-mT)=1-m^{d}(u-v)$ 能大幅简化每个数据包。它本身并不决定特定 $(d,u,v)$ 出现的频率。因此，数据包代数和表示分类被列为独立的验证层。错误的重复次数虽能保留每个数据包的身份，却会产生错误的归一化有限行列式和限制指数。


<details>
<summary>英文原文</summary>

The scalar identity $\det(I-mT)=1-m^{d}(u-v)$ simplifies each packet dramatically. It does not itself determine how frequently a given $(d,u,v)$ occurs. This is why packet algebra and representation classification are listed as separate verification layers. Incorrect multiplicities can preserve each packet identity while giving the wrong normalized finite determinant and limiting exponent.

</details>

反向特征多项式很方便，因为它能够直接编码 $\det(I-zT)$。如果它等于 $1-cz^{d}$，代入 $z=m$ 即可证明数据包公式。Lean 内核将这种代数蕴含形式化。量子二项式关系以及消失的下部迹是其在注册表示族中对应假设的数学途径；为了完整证明该定理，这些仍需在形式上建立联系。


<details>
<summary>英文原文</summary>

The reverse characteristic polynomial is convenient because it encodes $\det(I-zT)$ directly. If it equals $1-cz^{d}$ , substituting $z=m$ proves the packet formula. The Lean kernel formalizes this algebraic implication. The quantum-binomial relation and vanishing lower traces are the mathematical route to its hypothesis in the registered representation family; they remain to be connected formally for the full theorem.

</details>

### J.5.2 为什么精确的有限控制无法确立极限


<details>
<summary>英文原文</summary>

J.5.2 Why exact finite controls do not establish the limit

</details>

在 $q\leq 9$ 测试中，直接整数决定因子与结果因子就数据包重构、符号处理及归一化问题达成了协议。它无法证明收敛性，即 $i\to\infty$ 。一个极限公式需要一种适用于所有数据包及链条中所有级别的误差估计方法。以 $1-m^{d}(u-v)$ 形式的因子在取对数后几乎消除误差的情况尤为关键。


<details>
<summary>英文原文</summary>

Agreement between direct integer determinants and resultants at $q\leq 9$ tests packet reconstruction, signs, and normalization in concrete cases. It cannot prove convergence as $i\to\infty$ . A limiting formula needs an error estimate that remains valid over all packets and all levels in the chain. Near-cancellation in factors of the form $1-m^{d}(u-v)$ is especially relevant after taking logarithms.

</details>

保留的证明将数据包划分为大小不同的中心项。小阶数下的完全伽罗瓦乘积为非零整数，从而得出一个下限，而孤立的小复因子无法得到该下限。在大阶数下，主导项以及单位根之间的间距决定了归一化误差。截断条件和均匀估计是解析证明的一部分，并非为了适应有限行列式值而选取的参数。


<details>
<summary>英文原文</summary>

The retained proof divides the packets into small and large central orders. Complete Galois products at small orders are nonzero integers, giving a lower bound that would not be available for an isolated small complex factor. At large orders, dominant terms and spacing among roots of unity control the normalized error. The cutoff and uniform estimates are part of the analytic proof, not parameters chosen to fit the finite determinant values.

</details>

更明确地，选择一个截止值 $D=D(q)$，并在 $D\to\infty$ 和 $D=o(q)$ 处进行操作。对于 $d\leq D$，在取对数之前将每个Galois轨道合并起来。所得整数范数不为零，可防止单个接近零的复因子产生不可控制的负贡献；归一化后，小阶贡献的总和为 $o(q^{3})$。对于 $d>D$，进行因子分解


<details>
<summary>英文原文</summary>

More explicitly, choose a cutoff $D=D(q)$ with $D\to\infty$ and $D=o(q)$ . For $d\leq D$ , combine every Galois orbit before taking logarithms. Nonvanishing of the resulting integer norm prevents an individual near-zero complex factor from producing an uncontrolled negative contribution; the total small-order contribution is $o(q^{3})$ after normalization. For $d>D$ , factor

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0535)

**表格与文字对照**

```text
| $1-m^{d}(u-v)=m^{d}(u-v)\left(1-\frac{1}{m^{d}(u-v)}\right).$ | | (S49)

表内文字对照（数值与原始行列保持不变）：
u-v) → u-v)
left( → 左（
frac → 分数
right) → 正确)
```


<details>
<summary>英文原文</summary>

| $1-m^{d}(u-v)=m^{d}(u-v)\left(1-\frac{1}{m^{d}(u-v)}\right).$ | | (S49)

</details>

第一个因子提供 $d\log m$ 加上单位根项 $\log|u-v|$。间距估计在完整数据包求和后控制后者，而 $m^{-d}$ 使得最后一个对数项在远离配对零模式的情况下可以均匀求和。根据保留的包计数引理， $\log m$ 的系数收敛至 $1/(p+1)$，且每次残差和在除以 $o(1)$ 后均为 $q^{3}$。因此进行指数运算后得到 $D_{q}(A_{m})\to m^{1/(p+1)}$。


<details>
<summary>英文原文</summary>

The first factor supplies $d\log m$ plus the root-of-unity term $\log|u-v|$ . The spacing estimate controls the latter after complete packet summation, while $m^{-d}$ makes the last logarithm uniformly summable away from the paired zero modes. Under the retained packet-counting lemma, the coefficient of $\log m$ converges to $1/(p+1)$ and every residual sum is $o(1)$ after division by $q^{3}$ . Exponentiating therefore gives $D_{q}(A_{m})\to m^{1/(p+1)}$ .

</details>

对所声称的极限取对数后得到 $(\log m)/(p+1)$，而无限行列式的对数则为 $\log m$。两者的差值为 $p\log m/(p+1)$。这一基本结论使得缺陷的大小变得明确，但并不能替代收敛性论证。它还强调了链式依赖关系：不同的商链可能具有不同的数据包分布，或者没有极限。


<details>
<summary>英文原文</summary>

Taking logarithms of the claimed limit gives $(\log m)/(p+1)$ , while the infinite determinant has logarithm $\log m$ . Their difference is $p\log m/(p+1)$ . This elementary consequence makes the size of the defect explicit but does not replace the convergence argument. It also emphasizes chain dependence: a different quotient chain may have a different packet distribution and a different limit or no limit.

</details>

### J.5.3 符号约定与专业审核


<details>
<summary>英文原文</summary>

J.5.3 Sign conventions and specialist review

</details>

负偶数级行列式 $-735$ 是一种有用的校验方法。用于与正Fuglede–Kadison行列式进行比较的归一化行列式，必须采用已注册的绝对或适当的奇异值约定。若直接将奇数阶包络公式直接应用于偶数级测试而未调整其假设条件，则属于另一种错误。该论文明确列出了偶数级对照数据，以便能够发现此类约定错误。


<details>
<summary>英文原文</summary>

The negative even-level determinant $-735$ is a useful convention check. A normalized determinant intended to compare with a positive Fuglede–Kadison determinant must use the registered absolute or appropriate singular-value convention. Copying the odd-order packet formula into an even-level test without adjusting its hypotheses would be a separate error. The manuscript reports the even controls precisely to make such convention failures visible.

</details>

该来源反例表明了行列式近似方法的失效。精确的极限与链分类是后续结果，需要通过独立的算子代数分析来研究。尽管正式的行列式恒等式提供了大量可复用证据，但主要的分析挑战却存在于该恒等式本身之外。


<details>
<summary>英文原文</summary>

The source counterexample demonstrates the failure of determinant approximation. The exact limit and chain classifications are subsequent results that call for an independent operator-algebraic analysis. Although the formal determinant identity provides substantial and reusable evidence, the principal analytical challenge lies beyond the identity itself.

</details>

### J.6 在线排列嵌入：交替家族渐近性


<details>
<summary>英文原文</summary>

J.6 Online permutation embedding: alternating-family asymptotics

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0542)

图 S11：交替族扩展的分析结构。(a) 关键方程 $\sinh(2u_{*})-2u_{*}=1$ 决定了 $a=\cosh^{2}(u_{*})/4$ 和对数系数。(b) 所绘制的量仅为从 $b\log(k)/k$ 到 $\beta(\operatorname{Alt}_{k})/k^{2}$ 的显式修正项 $b=\sinh^{2}(u_{*})/6$；未归一化展开式中未知的剩余项 $O(k)$ 并未绘制出来。这些均为公式示例，与所报告的 Arb 动态规划检验无关。


<details>
<summary>英文原文</summary>

Figure S11: Analytic structure of the alternating-family expansion. (a) The critical equation $\sinh(2u_{*})-2u_{*}=1$ determines $a=\cosh^{2}(u_{*})/4$ and the logarithmic coefficient. (b) The plotted quantity is only the explicit correction $b\log(k)/k$ to $\beta(\operatorname{Alt}_{k})/k^{2}$ , where $b=\sinh^{2}(u_{*})/6$ ; the unknown $O(k)$ remainder in the unnormalized expansion is not plotted. These are formula illustrations, separate from the reported Arb dynamic-programming checks.

</details>

图 S11 将标量临界点与对数项的尺度联系起来。图中并未绘制新的动态规划结果，也未断言交替族具有全局最优性。


<details>
<summary>英文原文</summary>

Figure S11 connects the scalar critical point to the scale of the logarithmic term. It does not plot new dynamic-programming observations or assert global optimality of the alternating family.

</details>

让 $\operatorname{Alt}_{k}$ 表示交替递增族，而 $\beta$ 则是源在线嵌入问题的目标（Altschuler等人，2026）。让 $u_{*}>0$ 解决 $\sinh(2u_{*})-2u_{*}=1$ 。保留的渐近候选解为


<details>
<summary>英文原文</summary>

Let $\operatorname{Alt}_{k}$ denote the alternating increasing family and $\beta$ the objective of the source online embedding problem ( Altschuler et al., 2026 ) . Let $u_{*}>0$ solve $\sinh(2u_{*})-2u_{*}=1$ . The retained asymptotic candidate is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0545)

**表格与文字对照**

```text
| $\frac{\beta(\operatorname{Alt}_{k})}{k^{2}}\longrightarrow\frac{\cosh^{2}u_{*}}{4}\approx 0.49.$ | | (S50)

表内文字对照（数值与原始行列保持不变）：
frac → 分数
beta( → beta(
operatorname → \operatorname
Alt → Alt
longrightarrow → 转向
cosh → 双曲余弦
approx → 约
```


<details>
<summary>英文原文</summary>

| $\frac{\beta(\operatorname{Alt}_{k})}{k^{2}}\longrightarrow\frac{\cosh^{2}u_{*}}{4}\approx 0.49.$ | | (S50)

</details>

更确切地说，对于奇偶常数 $C_{0},C_{1}$，


<details>
<summary>英文原文</summary>

More precisely, for parity constants $C_{0},C_{1}$ ,

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0547)

**表格与文字对照**

```text
| $\begin{split}\sqrt{\beta(\operatorname{Alt}_{k})}={}&\frac{\cosh u_{*}}{2}k+\frac{\sinh^{2}u_{*}}{6\cosh u_{*}}\log k+C_{k\bmod 2}+o(1),\\
\beta(\operatorname{Alt}_{k})={}&\frac{\cosh^{2}u_{*}}{4}k^{2}+\frac{\sinh^{2}u_{*}}{6}k\log k+O(k).\end{split}$ | | (S51)

表内文字对照（数值与原始行列保持不变）：
begin → 开始
split → 分割
sqrt → 根号
beta( → beta(
operatorname → \operatorname
Alt → Alt
frac → 分数
cosh u_ → cosh u_
sinh → sinh
log k → log k
bmod → bmod
cosh → 双曲余弦
O(k) → O(k)
end → 结束
```


<details>
<summary>英文原文</summary>

| $\begin{split}\sqrt{\beta(\operatorname{Alt}_{k})}={}&\frac{\cosh u_{*}}{2}k+\frac{\sinh^{2}u_{*}}{6\cosh u_{*}}\log k+C_{k\bmod 2}+o(1),\\
\beta(\operatorname{Alt}_{k})={}&\frac{\cosh^{2}u_{*}}{4}k^{2}+\frac{\sinh^{2}u_{*}}{6}k\log k+O(k).\end{split}$ | | (S51)

</details>

### 重复机制。


<details>
<summary>英文原文</summary>

Recurrence mechanism.

</details>

交替树根分裂为一个单元素节点和一个大小为 $k-2$ 的交替子树，从而得到 $S_{k}=\Phi(S_{k-2})$ 对于 $S_{k}=\sqrt{\beta(\operatorname{Alt}_{k})}$。保留的贝尔曼残差扩展为


<details>
<summary>英文原文</summary>

The alternating-tree root splits into one singleton and an alternating subtree of size $k-2$ , giving $S_{k}=\Phi(S_{k-2})$ for $S_{k}=\sqrt{\beta(\operatorname{Alt}_{k})}$ . The retained Bellman-residual expansion is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0550)

**表格与文字对照**

```text
| $P_{1,s^{2}}(u)=\sinh(2u)-2u-\frac{8\sinh^{3}u}{3s}+O(s^{-2}).$ | | (S52)

表内文字对照（数值与原始行列保持不变）：
sinh( → sinh(
u)- → u)-
frac → 分数
sinh → sinh
O(s → O(s
```


<details>
<summary>英文原文</summary>

| $P_{1,s^{2}}(u)=\sinh(2u)-2u-\frac{8\sinh^{3}u}{3s}+O(s^{-2}).$ | | (S52)

</details>

根条件产生 $u_{s}=u_{*}+2\sinh(u_{*})/(3s)+O(s^{-2})$，因此


<details>
<summary>英文原文</summary>

The root condition yields $u_{s}=u_{*}+2\sinh(u_{*})/(3s)+O(s^{-2})$ , and hence

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0552)

**表格与文字对照**

```text
| $\Phi(s)-s=\cosh u_{*}+\frac{\sinh^{2}u_{*}}{6s}+O(s^{-2}).$ | | (S53)

表内文字对照（数值与原始行列保持不变）：
Phi(s)-s → Phi(s)-s
cosh u_ → cosh u_
frac → 分数
sinh → sinh
O(s → O(s
```


<details>
<summary>英文原文</summary>

| $\Phi(s)-s=\cosh u_{*}+\frac{\sinh^{2}u_{*}}{6s}+O(s^{-2}).$ | | (S53)

</details>

按每个奇偶类进行求和后便得到线性和对数项。这一步骤需要在贝尔曼展开中实现统一的误差控制，这超出了正式的代数核心范围。


<details>
<summary>英文原文</summary>

Summation along each parity class gives the linear and logarithmic terms. This step requires uniform error control in the Bellman expansion, beyond the formal algebraic kernel.

</details>

使用 $x=e^{-2u}$，变分目标变为 $H(u)=(1+2u)\coth(u)/8$。其导数具有 $\sinh(2u)-2u-1$ 的符号，从而产生唯一的最小化器 $u_{*}$ 和 $H(u_{*})=\cosh^{2}u_{*}/4$。一个机械式标量核函数证明了关键方程重写及系数归一化过程。根的唯一性以及递归渐近性质并不包含在该范围内。


<details>
<summary>英文原文</summary>

With $x=e^{-2u}$ , the variational objective becomes $H(u)=(1+2u)\coth(u)/8$ . Its derivative has the sign of $\sinh(2u)-2u-1$ , giving a unique minimizer $u_{*}$ and $H(u_{*})=\cosh^{2}u_{*}/4$ . A mechanized scalar kernel proves the critical-equation rewrite and coefficient normalization. Root uniqueness and recurrence asymptotics are not included in that scope.

</details>

两个向外圆化的 Arb 动态程序确保了冻结有限问题下交替族结构的有限最优性，对应 $k\leq 5000$。所报告的有限二阶估计值均约为 0.11，且接近精确表达式 $\sinh^{2}(u_{*})/(6\cosh(u_{*}))\approx 0.11$（即 $\sqrt{\beta}$ 中的对数系数）；而 $k\log k$ 中的 $\beta$ 系数则等于 $\sinh^{2}(u_{*})/6\approx 0.16$。这种一致性将有限动态程序与解析展开联系起来。


<details>
<summary>英文原文</summary>

Two outward-rounded Arb dynamic programs support finite optimality of the alternating family within the frozen finite problem for $k\leq 5000$ . The reported finite second-order estimates both round to 0.11 and approach the exact expression $\sinh^{2}(u_{*})/(6\cosh(u_{*}))\approx 0.11$ , the logarithmic coefficient in $\sqrt{\beta}$ ; the $k\log k$ coefficient in $\beta$ is instead $\sinh^{2}(u_{*})/6\approx 0.16$ . This agreement links the finite dynamic programs to the analytic expansion.

</details>

### J.6.1 关键方程及其唯一正解


<details>
<summary>英文原文</summary>

J.6.1 The critical equation and its unique positive solution

</details>

为 $f(u)=\sinh(2u)-2u-1$ 定义 $u\geq 0$ 。然后针对 $f(0)=-1$ 分别定义 $f(u)\to\infty$、$f^{\prime}(u)=2\cosh(2u)-2>0$ 和 $u>0$ 。因此，连续性和严格单调性恰好给出一个正根。这个基础论证在此为书面推导形式；所提供的 Lean 内核仅用于说明关键恒等式和系数归一化过程。


<details>
<summary>英文原文</summary>

Define $f(u)=\sinh(2u)-2u-1$ for $u\geq 0$ . Then $f(0)=-1$ , $f(u)\to\infty$ , and $f^{\prime}(u)=2\cosh(2u)-2>0$ for $u>0$ . Thus continuity and strict monotonicity give exactly one positive root. This elementary argument is a written derivation here; the supplied Lean kernel is reported only for the critical identity and coefficient normalization.

</details>

对于 $H(u)=(1+2u)\coth(u)/8$ ，差异化带来了优势


<details>
<summary>英文原文</summary>

For $H(u)=(1+2u)\coth(u)/8$ , differentiation gives

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0559)

**表格与文字对照**

```text
| $H^{\prime}(u)=\frac{\sinh(2u)-2u-1}{8\sinh^{2}u}.$ | | (S54)

表内文字对照（数值与原始行列保持不变）：
prime → 主要
frac → 分数
sinh( → sinh(
u)- → u)-
sinh → sinh
```


<details>
<summary>英文原文</summary>

| $H^{\prime}(u)=\frac{\sinh(2u)-2u-1}{8\sinh^{2}u}.$ | | (S54)

</details>

分母在 $u>0$ 处为正，因此 $H$ 在 $u_{*}$ 之前减小，在之后增加。在根处为 $1+2u_{*}=2\sinh u_{*}\cosh u_{*}$，通过替换可得 $H(u_{*})=\cosh^{2}u_{*}/4$。这连接了标量方程、变分最小化器以及主导缩放系数。


<details>
<summary>英文原文</summary>

The denominator is positive for $u>0$ , so $H$ decreases before $u_{*}$ and increases after it. At the root, $1+2u_{*}=2\sinh u_{*}\cosh u_{*}$ , and substitution yields $H(u_{*})=\cosh^{2}u_{*}/4$ . This connects the scalar equation, the variational minimizer, and the leading scaling coefficient.

</details>

### J.6.2 从递推关系中提取对数修正项


<details>
<summary>英文原文</summary>

J.6.2 Extracting the logarithmic correction from the recurrence

</details>

让 $a=\cosh u_{*}$ 和 $b=\sinh^{2}u_{*}/6$。已注册的扩展形式为 $S_{k}-S_{k-2}=a+b/S_{k-2}+O(S_{k-2}^{-2})$。在任一奇偶类上，设置 $x_{j}=S_{2j+\eta}$。然后


<details>
<summary>英文原文</summary>

Let $a=\cosh u_{*}$ and $b=\sinh^{2}u_{*}/6$ . The registered expansion has the form $S_{k}-S_{k-2}=a+b/S_{k-2}+O(S_{k-2}^{-2})$ . On either parity class, set $x_{j}=S_{2j+\eta}$ . Then

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0563)

**表格与文字对照**

```text
| $x_{j+1}-x_{j}=a+\frac{b}{x_{j}}+O(x_{j}^{-2}).$ | | (S55)

表内文字对照（数值与原始行列保持不变）：
frac → 分数
O(x_ → O(x_
```


<details>
<summary>英文原文</summary>

| $x_{j+1}-x_{j}=a+\frac{b}{x_{j}}+O(x_{j}^{-2}).$ | | (S55)

</details>

一旦递归关系建立起来，倒数项在求和中贡献了 $(b/a)\log j$。二次误差是可求和的。在均匀扩展假设下，控制 $1/x_{j}$ 与 $1/(aj)$ 之间的差值可将结果优化至 $x_{j}=aj+(b/a)\log j+C_{\eta}+o(1)$。


<details>
<summary>英文原文</summary>

Once the recurrence establishes $x_{j}\sim aj$ , the reciprocal term contributes $(b/a)\log j$ on summation. The quadratic error is summable. Controlling the difference between $1/x_{j}$ and $1/(aj)$ refines the result to $x_{j}=aj+(b/a)\log j+C_{\eta}+o(1)$ under the uniform expansion hypotheses.

</details>

以下是详细汇总步骤。递推关系首先给出了所有大语言模型的常数 $c_{1},c_{2}>0$，其中 $c_{1}j\leq x_{j}\leq c_{2}j$ 对应于 $j$，通过求和 $x_{j}=aj+O(\log j)$ 可得 $b/x_{j}+O(x_{j}^{-2})$。因此


<details>
<summary>英文原文</summary>

Here is the summation step in detail. The recurrence first gives constants $c_{1},c_{2}>0$ with $c_{1}j\leq x_{j}\leq c_{2}j$ for all large $j$ , hence $x_{j}=aj+O(\log j)$ by summing $b/x_{j}+O(x_{j}^{-2})$ . Therefore

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0566)

**表格与文字对照**

```text
| $\frac{1}{x_{j}}=\frac{1}{aj}+O\!\left(\frac{\log j}{j^{2}}\right).$ | | (S56)

表内文字对照（数值与原始行列保持不变）：
frac → 分数
left( → 左（
log j → 日志 j
right) → 正确)
```


<details>
<summary>英文原文</summary>

| $\frac{1}{x_{j}}=\frac{1}{aj}+O\!\left(\frac{\log j}{j^{2}}\right).$ | | (S56)

</details>

定义 $y_{j}=x_{j}-aj-(b/a)\log j$ 。使用


<details>
<summary>英文原文</summary>

Define $y_{j}=x_{j}-aj-(b/a)\log j$ . Using

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0568)

**表格与文字对照**

```text
| $\log(j+1)-\log j=\frac{1}{j}+O(j^{-2}),$ | | (S57)

表内文字对照（数值与原始行列保持不变）：
log(j → log(j
log j → 日志 j
frac → 分数
O(j → O(j
```


<details>
<summary>英文原文</summary>

| $\log(j+1)-\log j=\frac{1}{j}+O(j^{-2}),$ | | (S57)

</details>

该递推关系给出 $y_{j+1}-y_{j}=O((\log j)/j^{2})$ 。这些增量的序列绝对收敛，因此 $y_{j}$ 收敛于一个与奇偶性相关的常数 $C_{\eta}$ 。这证明了


<details>
<summary>英文原文</summary>

the recurrence gives $y_{j+1}-y_{j}=O((\log j)/j^{2})$ . The series of these increments converges absolutely, so $y_{j}$ converges to a parity-dependent constant $C_{\eta}$ . This proves

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0570)

**表格与文字对照**

```text
| $x_{j}=aj+\frac{b}{a}\log j+C_{\eta}+o(1)$ | | (S58)

表内文字对照（数值与原始行列保持不变）：
frac → 分数
log j → 日志 j
eta → eta
```


<details>
<summary>英文原文</summary>

| $x_{j}=aj+\frac{b}{a}\log j+C_{\eta}+o(1)$ | | (S58)

</details>

采用统一一步扩展方法，而非通过数值拟合来推导对数项。


<details>
<summary>英文原文</summary>

from the uniform one-step expansion, rather than inferring the logarithmic term from numerical fitting.

</details>

回到 $k$，得到 $S_{k}=(a/2)k+(b/a)\log k+C_{k\bmod 2}+o(1)$，其中依赖奇偶性的常数会吸收固定的对数偏移。平方运算产生交叉项 $b\,k\log k$，而平方对数与常数的相互作用则表现为 $O(k)$。这恰好恢复了显示展开式中 $\sinh^{2}u_{*}/6$ 的系数 $\beta$。


<details>
<summary>英文原文</summary>

Returning to $k$ gives $S_{k}=(a/2)k+(b/a)\log k+C_{k\bmod 2}+o(1)$ , with the parity-dependent constants absorbing fixed logarithmic shifts. Squaring produces the cross term $b\,k\log k$ , while the squared logarithm and constant interactions are $O(k)$ . This recovers exactly the coefficient $\sinh^{2}u_{*}/6$ in the displayed expansion for $\beta$ .

</details>

该推导明确了哪些部分属于形式代数，哪些部分需要渐近控制。临界值简化是一个有限恒等式。统一建立贝尔曼残差展开，选择适当的根分支，证明 $S_{k}\to\infty$，并求和误差是分析学中的任务。这些任务不能仅通过检查 Lean 中的系数恒等式来完成。


<details>
<summary>英文原文</summary>

The derivation clarifies which parts are formal algebra and which parts require asymptotic control. The critical-value simplification is a finite identity. Establishing the Bellman residual expansion uniformly, selecting the appropriate root branch, proving $S_{k}\to\infty$ , and summing errors are analytic obligations. They cannot be discharged merely by checking the coefficient identity in Lean.

</details>

### J.6.3 有限最优性、家族渐近性以及全局极值性


<details>
<summary>英文原文</summary>

J.6.3 Finite optimality, family asymptotics, and global extremality

</details>

Arb计算通过5000时间步长解决了冻结的有限优化问题，采用向外舍入方式，使数值比较能够被验证为区间。这两种实现方法降低了共享动态规划误差的可能性。它们在有限范围内的一致性并不能说明交替族在更大的规模下是全局最优的。


<details>
<summary>英文原文</summary>

The Arb calculations address the frozen finite optimization problem through horizon 5,000, using outward rounding so that numerical comparisons are certified as intervals. The two implementations reduce the chance of a shared dynamic-programming error. Their agreement on a finite range does not show that the alternating family is globally optimal at every larger size.

</details>

该渐近性陈述涉及交替族本身。即便能完全证明该族的递推关系及其极限，也无法证明不存在其他族具有更小的极限目标。全局极值问题需要针对所有允许的排列或树结构建立比较原理。该论文将这三个层面区分开来：有限的认证比较、该族的解析展开，以及尚未解决的全族极值主张。


<details>
<summary>英文原文</summary>

The asymptotic statement concerns the alternating family itself. Even a complete proof of that family recurrence and its limit would not establish that no other family has a smaller limiting objective. The global extremal question requires a comparison principle over all allowed permutations or trees. The manuscript keeps these three levels distinct: finite certified comparisons, the family’s analytic expansion, and the unresolved all-family extremality claim.

</details>

接近 $\sinh^{2}(u_{*})/(6\cosh(u_{*}))\approx 0.11$ 的二阶有限估计属于 $\sqrt{\beta}$ 尺度下的一致性检验。独立的系数 $\sinh^{2}(u_{*})/6\approx 0.16$ 则属于 $\beta$ 尺度。保留精确的符号表达式与两位小数的近似值，可避免这两个系数被混淆。


<details>
<summary>英文原文</summary>

The second-order finite estimates approaching $\sinh^{2}(u_{*})/(6\cosh(u_{*}))\approx 0.11$ are consistency checks at the $\sqrt{\beta}$ scale. The separate coefficient $\sinh^{2}(u_{*})/6\approx 0.16$ belongs to the $\beta$ scale. Keeping the exact symbolic expressions alongside two-decimal approximations prevents those two coefficients from being conflated.

</details>

## 附录 K 辅助结果：精确分类、减少量及障碍


<details>
<summary>英文原文</summary>

Appendix K Auxiliary Results: Exact Classifications, Reductions, and Obstructions

</details>

本节的十三个辅助组包含二十五项具体化的结果，这些结果丰富了支撑性研究库。它们不被视为额外的独立4+6类成功案例。这些包括有限分类、无限家族候选项、验证改进、来源表修正以及负面局部障碍等。这些陈述是从提供的研究档案中复现并整理出来的。如果该档案中未完全定义特定来源的标注方式，则保持原有的来源惯例，并注明进行独立专业评估所需的额外定义。


<details>
<summary>英文原文</summary>

The thirteen auxiliary groups in this section comprise twenty-five scoped results that expand the supporting research inventory. They are not counted as additional independent 4+6 headline successes. They include finite classifications, infinite-family candidates, verification improvements, source-table corrections, and negative local obstructions. The statements are reproduced and organized from the supplied research dossier. When source-specific notation is not fully defined in that dossier, the statement retains its source convention and identifies the additional definition needed for standalone specialist assessment.

</details>

### K.1 精确的 k-SSD高度与唯一的极值点


<details>
<summary>英文原文</summary>

K.1 Exact k-SSD heights and unique extremizers

</details>

对于正整数 $k$ -SSD 集合 $A=\{a_{1},\ldots,a_{n}\}$，所有与 $\sum_{i}c_{i}a_{i}$ 相关的和 $c_{i}\in\{0,\ldots,k\}$ 都是不同的。按照所给定的规则，高度由最大的生成器决定，而 $h_{k}(n)$ 则使该高度最小。通过枚举系数和即可轻松验证候选上界；而精确的最小值则需要排除所有更小的可行生成器元组；唯一性要求还需证明没有其他元组能达到该最小值。


<details>
<summary>英文原文</summary>

For a positive-integer $k$ -SSD set $A=\{a_{1},\ldots,a_{n}\}$ , all sums $\sum_{i}c_{i}a_{i}$ with $c_{i}\in\{0,\ldots,k\}$ are distinct. In the supplied convention, the height is the largest generator, and $h_{k}(n)$ minimizes that height. A candidate upper bound is easy to certify by enumerating coefficient sums. An exact minimum requires excluding every smaller admissible generator tuple; uniqueness additionally requires showing that no other tuple attains the minimum.

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0582)

表 S12：双验证的四生成器 k-SSD结果。


<details>
<summary>英文原文</summary>

Table S12: Dual-verified four-generator k-SSD results.

</details>

这两种验证方法采用签名差边界和转换不相交枚举技术。它们的一致性涵盖了较低切片和极值器唯一性问题，而不仅仅是所显示集合的有效性。所提供的比较器构造分别得到高度 121、211 和 337。这些属于有限的改进措施，而非通用的高度计算公式。


<details>
<summary>英文原文</summary>

The two verification routes use signed-difference frontiers and translate-disjointness enumeration. Their agreement covers lower slices and extremizer uniqueness, not merely validity of the displayed sets. The supplied comparator construction gives heights 121, 211, and 337, respectively. These are scoped finite improvements, not an all- $k$ height formula.

</details>

主要搜索结果还显示，在 37,759,246,033 次第五值测试后，具有独特极限值的智能体出现了 $h_{4}(5)=442$。其独立的 Z3 下限排除机制已超时。该结果必须保持为“主要完整”状态，而非“双重验证”状态。超时并未否定候选者，只是阻止了更强的独立排除状态。这一记录说明了为何构建过程、下限排除以及唯一性需要分别记录凭证。


<details>
<summary>英文原文</summary>

The primary search also reports $h_{4}(5)=442$ with unique extremizer $\{344,417,427,433,442\}$ after 37,759,246,033 fifth-value tests. Its independent Z3 lower exclusion timed out. This result must remain primary-complete rather than dual-verified. The timeout does not falsify the candidate; it prevents the stronger independent-exclusion status. This entry illustrates why construction, lower-bound exclusion, and uniqueness need separately recorded receipts.

</details>

### K.2 直径为六和七的四元素集合


<details>
<summary>英文原文</summary>

K.2 Four-element sumsets of diameter six and seven

</details>

让 $hA$ 表示由 $h$ 中恰好 $A$ 个元素按重复方式相加所构成的集合，并定义 $R(h,4)=\{|hA|:A\subset\mathbb{Z},\ |A|=4\}$。保留的六维分类规则指出，对于 $h\geq 4$，


<details>
<summary>英文原文</summary>

Let $hA$ denote the set of sums of exactly $h$ elements of $A$ , with repetition, and define $R(h,4)=\{|hA|:A\subset\mathbb{Z},\ |A|=4\}$ . The retained diameter-six classification states that for $h\geq 4$ ,

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0588)

**表格与文字对照**

```text
| $R(h,4)\cap[5h+2,7h-6]=\begin{cases}\varnothing,&h=4,\\
\{6h-3,6h-1\},&h=5,6,\\
\{6h-3,6h-1,6h+1\},&h\geq 7.\end{cases}$ | | (S59)

表内文字对照（数值与原始行列保持不变）：
R(h → R(h
cap → 帽子
begin → 开始
cases → 案例
varnothing → 空集合
geq → geq
end → 结束
```


<details>
<summary>英文原文</summary>

| $R(h,4)\cap[5h+2,7h-6]=\begin{cases}\varnothing,&h=4,\\
\{6h-3,6h-1\},&h=5,6,\\
\{6h-3,6h-1,6h+1\},&h\geq 7.\end{cases}$ | | (S59)

</details>

该证明可简化为仿射归一化直径公式，并验证了五个反射代表体的精确互补恒等式。仿射归一化去除了平移和共同缩放效应，而反射则能识别等价的端点模式。


<details>
<summary>英文原文</summary>

The proof reduces to affine-normalized diameter six and verifies exact complement identities for five reflection representatives. Affine normalization removes translation and common scaling, while reflection identifies equivalent endpoint patterns.

</details>

直径七的区域在 $h\geq 6$ 方面具有...


<details>
<summary>英文原文</summary>

The diameter-seven region has, for $h\geq 6$ ,

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0591)

**表格与文字对照**

```text
| $R(h,4)\cap[6h+2,8h-9]=\begin{cases}\{7h-4,7h-3\},&h=6,\\
\{7h-5,7h-4,7h-3,7h-2\},&7\leq h\leq 9,\\
\{7h-5,7h-4,7h-3,7h-2,7h+1\},&h\geq 10.\end{cases}$ | | (S60)

表内文字对照（数值与原始行列保持不变）：
R(h → R(h
cap → 帽子
begin → 开始
cases → 案例
leq h → leq h
leq → leq
geq → geq
end → 结束
```


<details>
<summary>英文原文</summary>

| $R(h,4)\cap[6h+2,8h-9]=\begin{cases}\{7h-4,7h-3\},&h=6,\\
\{7h-5,7h-4,7h-3,7h-2\},&7\leq h\leq 9,\\
\{7h-5,7h-4,7h-3,7h-2,7h+1\},&h\geq 10.\end{cases}$ | | (S60)

</details>

九位标准化反射代表涵盖了这一第二次缩减过程。独立的普雷斯伯格查询用于验证任意性的归纳步骤。对200个对象的有限检查属于控制手段，并非导致这些陈述适用于所有更大范围的原因。重要的证据链在于结构直径的缩小、一系列标准化的形式列表，以及针对每个形式的符号归纳。这些特定分类窗口的外部优先级则保持独立。


<details>
<summary>英文原文</summary>

Nine normalized reflection representatives cover this second reduction. Independent Presburger queries verify the arbitrary- $h$ induction steps. Finite checks through 200 are controls, not the reason the statements quantify over every larger $h$ . The important evidence chain is structural diameter reduction, a finite list of normalized forms, and symbolic induction on each form. External priority for these exact classification windows remains separate.

</details>

### K.3 Rajagopal 在 h+k 处的有限边界最多为十三


<details>
<summary>英文原文</summary>

K.3 Rajagopal finite boundary through h+k at most thirteen

</details>

采用源约定 $R(h,k)=\{|hA|:A\subset\mathbb{Z},\ |A|=k\}$，保留的构建性验证涵盖了所有以 $k>h$ 为元素的已注册对 $h+k\leq 13$。新的边界是


<details>
<summary>英文原文</summary>

Using the source convention $R(h,k)=\{|hA|:A\subset\mathbb{Z},\ |A|=k\}$ , the retained constructive verification covers all registered pairs $k>h$ with $h+k\leq 13$ . The new boundary is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0595)

**表格与文字对照**

```text
| $\displaystyle R(4,9)$ | $\displaystyle=[33,495]\setminus\{34,35,38\},$ | | (S61)
 | $\displaystyle R(5,8)$ | $\displaystyle=[36,792]\setminus\{37,38,39,42,43,47\},$ | | (S62)
 | $\displaystyle R(6,7)$ | $\displaystyle=[37,924]\setminus\{38,39,40,41,44,45,46,50,51,56\}.$ | | (S63)

表内文字对照（数值与原始行列保持不变）：
displaystyle R( → \displaystyle R(
displaystyle → \displaystyle
setminus → 排除
```


<details>
<summary>英文原文</summary>

| $\displaystyle R(4,9)$ | $\displaystyle=[33,495]\setminus\{34,35,38\},$ | | (S61)
 | $\displaystyle R(5,8)$ | $\displaystyle=[36,792]\setminus\{37,38,39,42,43,47\},$ | | (S62)
 | $\displaystyle R(6,7)$ | $\displaystyle=[37,924]\setminus\{38,39,40,41,44,45,46,50,51,56\}.$ | | (S63)

</details>

边界搜索产生了 460, 751 和 878 个见证者。它们的总和为 2,089；这就是新的边界层计数，与整体库存中 2,814 个见证者在整个注册范围内的数值不同。一个独立程序会重新计算所有 2,089 个边界见证者的总和，并排除重复元素的错误。


<details>
<summary>英文原文</summary>

The boundary search emits 460, 751, and 878 witnesses. Their sum is 2,089; this is the new boundary-layer count, distinct from the broader inventory’s 2,814 witnesses across its registered range. An independent program reconstructs the sumsets of all 2,089 boundary witnesses and rejects duplicate-element corruptions.

</details>

存在证明建立了所有包含的值。要证明被省略的值是不可能的，需要分别满足精确的区间闭合条件以及来源排除论证。文件报告了完整的有限验证过程，但原始证据目录和排除证书并未包含在此手稿中。该命题是一个有限边界定理，而非全参数猜想的证明。本条目表明，保留建设性证据比仅使用可能基数表更有价值。


<details>
<summary>英文原文</summary>

Existence witnesses establish every included value. Exact interval closure and the source’s exclusion argument are separately needed to establish that omitted values are impossible. The dossier reports the full finite verification, but the raw witness catalogue and exclusion certificates are not embedded in this manuscript. The claim is a finite boundary theorem, not a proof of the all-parameter conjecture. This entry demonstrates the value of retaining constructive witnesses instead of a table of possible cardinalities alone.

</details>

### K.4 Lonely Runner单替换分类法


<details>
<summary>英文原文</summary>

K.4 Lonely Runner single-replacement classifications

</details>

对于具有被删除速度 $r=4$ 或 $r=5$ 的源材料单替换速度系列，保留的分类结果并未出现超出已发布的多替换机制范围的零星紧密案例。在 $r=5$ 减少过程中，恰好有 46 对候选对保留为 $11\leq n\leq 20$。它们的精确 Breakpoint-Lemma 评估结果符合 $\operatorname{LR}>1/n$ 要求。


<details>
<summary>英文原文</summary>

For the source’s single-replacement speed families with deleted speed $r=4$ or $r=5$ , the retained classification finds no sporadic tight cases outside the published multiple-replacement mechanism. In the $r=5$ reduction, exactly 46 candidate pairs remain with $11\leq n\leq 20$ . Their exact Breakpoint-Lemma evaluations satisfy $\operatorname{LR}>1/n$ .

</details>

最小的保留余量为 $1/42$，在源参数 $(n,w)=(14,14)$ 下以 $\operatorname{LR}=2/21$ 实现；实际上为 $2/21-1/14=1/42$。这一计算是对所提出的余量进行内部一致性检验。替换族的定义以及这些 46 对实例涵盖其非多重情况的证据，仍属于该定理的假设与归约包的一部分。


<details>
<summary>英文原文</summary>

The smallest retained margin is $1/42$ , attained at the source parameters $(n,w)=(14,14)$ with $\operatorname{LR}=2/21$ ; indeed $2/21-1/14=1/42$ . This arithmetic is an internal consistency check on the stated margin. The source definition of the replacement family and the proof that these 46 pairs exhaust its non-multiple cases remain part of the theorem’s hypotheses and reduction package.

</details>

将有限的残差分类与已建立的多种案例相结合，便得到了所陈述的固定结果。仅依靠有限计算无法得出该结果，没有这种简化就不可行。该分类方法也无法解决一般的“孤独跑者”猜想。那个尚未解决的14个跑者求解方向被记录在负面记录中，不应与这一被认可的固定替换家族混淆。


<details>
<summary>英文原文</summary>

Combining the finite residual classification with the established multiple case gives the stated fixed- $r=5$ result. The finite computations alone would not imply it without that reduction. Neither classification resolves the general Lonely Runner conjecture. The separate unresolved 14-runner solver direction appears in the negative ledger and must not be confused with this admitted fixed-replacement family.

</details>

### K.5 适用于 10p 和 11p 阶的傅里叶主非奇点


<details>
<summary>英文原文</summary>

K.5 Fourier principal nonsingularity for orders 10p and 11p

</details>

源提升定理将两个主要参数的傅里叶非奇点族简化为精确的分圆范数数据。对于阶为 $11p$ 的情况，保留的异常支持数为 $\{3,11,23,67,199,419\}$，而总范数分解则为


<details>
<summary>英文原文</summary>

The source lifting theorem reduces two prime-parameter Fourier nonsingularity families to exact cyclotomic norm data. For order $11p$ , the retained exception support is $\{3,11,23,67,199,419\}$ and the aggregate norm factorization is

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0604)

**表格与文字对照**

```text
| $3^{220}11^{28160}23^{1100}67^{220}199^{220}419^{220}.$ | | (S64)
```


<details>
<summary>英文原文</summary>

| $3^{220}11^{28160}23^{1100}67^{220}199^{220}419^{220}.$ | | (S64)

</details>

因此，在源定理的可接受性假设下，对于该支持范围之外的素数，所陈述的次要非奇异性结论仍然成立；187阶也被包含在内。对于$10p$阶，支持度为$\{2,3,5,11,31\}$，指数分别为$(5120,120,5120,240,80)$，而130阶也被包含在内。


<details>
<summary>英文原文</summary>

Thus the stated principal-minor nonsingularity conclusion holds for primes outside that support under the source theorem’s admissibility hypotheses; order 187 is included. For order $10p$ , the support is $\{2,3,5,11,31\}$ with exponents $(5120,120,5120,240,80)$ , and order 130 is included.

</details>

通过 Bareiss 消元方法计算乘法矩阵行列式，在保留的枚举过程中，所有 2,048 个 11 阶子集和 1,024 个 10 阶子集中的独立结果一致。这些独立的表示有助于检测归一化或分圆算术错误。若范数支持中存在异常素数，则无法得出充分的提升结论；不应自动将其视为已证明的奇异情况。


<details>
<summary>英文原文</summary>

Multiplication-matrix determinants computed by Bareiss elimination and independent resultants agree over all 2,048 order-11 subsets and 1,024 order-10 subsets in the retained enumeration. Their independent representations help detect normalization or cyclotomic arithmetic errors. An exceptional prime in the norm support means the sufficient lifting conclusion is unavailable there; it should not automatically be described as a proved singular case.

</details>

### K.6 ERG(3,8)：循环谱与因子临界性


<details>
<summary>英文原文</summary>

K.6 ERG(3,8): cycle spectrum and factor-criticality

</details>

在冻结的 477,142 条记录目录的完整性与正确性得到满足的前提下，所有被列出的无三角形、27个顶点的图，其独立数不超过七，均具有从4到27的所有长度的循环，且属于因子临界图。所谓因子临界性，是指删除任意一个顶点后，剩余图仍具有完美匹配，在此情况下共有13条边。


<details>
<summary>英文原文</summary>

Conditional on completeness and correctness of the frozen 477,142-record catalogue, every listed triangle-free 27-vertex graph with independence number at most seven has cycles of every length from 4 through 27 and is factor-critical. Here factor-criticality means that deleting any vertex leaves a graph with a perfect matching, consisting of 13 edges in this case.

</details>

主要处理步骤构建循环和顶点删除匹配关系。独立处理步骤采用通用的循环枚举方法以及定义在 $\mathbb{F}_{2147483647}$ 上的斜 Tutte 矩阵。秩为 26 且具有全支持核的斜 Tutte 矩阵在奇数阶斜设置中能够产生非零的主协因子，这证明了根据检验定理所要求的顶点删除匹配条件。有限域证明是非零性的证据，而非因匹配搜索失败而得出的推论。


<details>
<summary>英文原文</summary>

The primary pass constructs cycles and vertex-deleted matchings. The independent pass uses generic cycle enumeration and a skew Tutte matrix over $\mathbb{F}_{2147483647}$ . Rank 26 with a full-support kernel gives the required nonvanishing principal cofactors in the odd-order skew setting, which certifies the vertex-deleted matching condition under the checker theorem. The finite-field certificate is a witness of nonvanishing, not an inference from a failed search for a matching.

</details>

### K.7 Kasami APN计数身份，当n等于十四时


<details>
<summary>英文原文</summary>

K.7 Kasami APN counting identity at n equal to fourteen

</details>

对于符合要求的 $k$，结合 $\gcd(k,14)=1$，所保留的有限结果验证了源 NSUCRYPTO 计数性质在 Kasami 幂 $F(x)=x^{4^{k}-2^{k}+1}$ 对 $\mathrm{GF}(2^{14})$ 上的适用性。Frobenius 对称性将新的代表性计算简化为 $k=3$ 和 $k=5$。


<details>
<summary>英文原文</summary>

For admissible $k$ with $\gcd(k,14)=1$ , the retained finite result verifies the source NSUCRYPTO counting identity for the Kasami power $F(x)=x^{4^{k}-2^{k}+1}$ over $\mathrm{GF}(2^{14})$ . Frobenius symmetry reduces the new representative computations to $k=3$ and $k=5$ .

</details>

两种不同的不可约多项式域模型各自能验证每个代表样本中的16,382个允许值，从而在源符号中产生32,764个精确身份。两种导数图像均包含8,192个元素以及两点纤维，而所报告的Walsh支持集大小为3,088。


<details>
<summary>英文原文</summary>

Two different irreducible-polynomial field models check 16,382 admissible $\rho$ values per representative, giving 32,764 exact identities $Z(\rho)=0$ in the source notation. Both derivative images have 8,192 elements with two-point fibers, and the reported Walsh support has size 3,088.

</details>

定义 $Z$ 的公式以及对称性约化是源问题的一部分，必须作为独立证书发布内容包含在内。目前的证据将有限验证边界从 $n\leq 13$ 扩展至 $n=14$。它并未建立任意性的 $n$ 计数定理或新的通用 APN 构造。该工作展示了在新参数边界下的精确有限代数，并具备与表示无关的验证机制。


<details>
<summary>英文原文</summary>

The formula defining $Z$ and the symmetry reduction are part of the source problem and must be included with a standalone certificate release. The present evidence extends a finite verified boundary from $n\leq 13$ to $n=14$ . It does not establish an arbitrary- $n$ counting theorem or a new general APN construction. The work illustrates exact finite algebra at a new parameter boundary with representation-independent checks.

</details>

### K.8 ReLU MAX8 证书压缩与子集-配置动态规划


<details>
<summary>英文原文</summary>

K.8 ReLU MAX8 certificate compression and subset-profile dynamic programming

</details>

从公开的四模板 MAX6证书开始，本地附件搜索包含 676 个原始候选项、127 个图同构类以及 125 个精确函数列。经过保留后的组合生成了一个 25 模板的三度 MAX8身份。源代码的公开 69 模板证书扩展为 515,488 个对称第二层原子，而保留的证书则使用 187,460 个原子：这相当于减少了 63.63%，并实现了 2.75 倍的压缩。


<details>
<summary>英文原文</summary>

Starting from the public four-template MAX6 certificate, the local attachment search contains 676 raw candidates, 127 graph-isomorphism classes, and 125 exact function columns. The retained combination yields a 25-template degree-three MAX8 identity. The source’s public 69-template certificate expands to 515,488 symmetric second-layer atoms, whereas the retained certificate uses 187,460: a reported 63.63% reduction and 2.75-fold compression.

</details>

完整的 $8!$ 排列枚举与子集-配置动态规划逐项一致。动态规划根据足以用于证书评估的配置来聚合排列，因此其正确性需要证明聚合后的转换能够保留所有被评估的贡献。对于完整有限实例的一致性验证，可检验其相对于暴力枚举的简化效果。


<details>
<summary>英文原文</summary>

Full $8!$ permutation enumeration and subset-profile dynamic programming agree term by term. The dynamic program aggregates permutations according to profiles sufficient for the certificate evaluation, so its correctness requires proving that aggregated transitions preserve every evaluated contribution. Agreement on a complete finite instance checks that reduction against brute-force enumeration.

</details>

相同的通用验证器会对公共 MAX N 证书进行验证，从而将最大重放次数从约14.6亿种排列减少至7177万次转换。这既提升了验证效率，也实现了证书压缩。


<details>
<summary>英文原文</summary>

The same generic verifier checks public MAX N certificates for $5\leq N\leq 10$ , reducing the largest replay from approximately 1.46 billion permutations to 71.77 million transitions. This is a verification-efficiency result as well as a compressed certificate.

</details>

### K.9 AES CNOT 帕累托清理


<details>
<summary>英文原文</summary>

K.9 AES CNOT Pareto cleanup

</details>

一个独立的本地重写工作从包含 44 个托福利门和 197 个CNOT门的 20 量子比特AES电路开始。两对相同的CNOT门可以穿过中间的门进行交换并相互抵消，最终得到 193 个CNOT门，同时保留所有 44 个托福利门。保留下来的两个交换窗口分别覆盖第22和第23个门，而独立验证器会检查证书中记录的所有47次中间交换。


<details>
<summary>英文原文</summary>

A separate local rewrite begins with the source 20-qubit AES circuit containing 44 Toffoli gates and 197 CNOT gates. Two identical CNOT pairs can commute through intervening gates and cancel, giving 193 CNOT gates while preserving all 44 Toffolis. The two retained commutation windows span 22 and 23 gates, and the independent verifier checks all 47 intervening commutations recorded by the certificate.

</details>

所有 256 种输入情况均通过独立真值表检验。这验证了在已注册的输入与辅助协议下的有限电路转换有效性。这是一项适度的帕累托改进：一种门类型数量减少，而主要的托福利计数保持不变。它与 Hyperfactor交叉输出构造不同，不应将其视为对 T 计数节省的额外贡献，因为这两种变化实际上是针对同一基准进行的。


<details>
<summary>英文原文</summary>

All 256 input cases pass the independent truth-table check. This validates the finite circuit transformation under the registered input and ancilla contract. It is a modest Pareto improvement: one gate type decreases while the dominant Toffoli count stays fixed. It is distinct from the Hyperfactor cross-output construction and should not be added to its T-count savings as though both changes were applied to the same baseline.

</details>

独立的、详尽的单删除和10,920个双删除/一次插入仿射图无法降低四位逆变换的八个Toffoli数量。这些搜索负样本仅表明在探索的重写邻域中不存在此类情况，它们并非全局的Toffoli下界。


<details>
<summary>英文原文</summary>

Separate exhaustive single-delete and 10,920 two-delete/one-insert affine charts do not reduce the eight-Toffoli count of the four-bit inverse. Those search negatives prove only absence within the explored rewrite neighborhoods. They are not a global Toffoli lower bound.

</details>

### K.10 用于迁移张量的因子级尾部消除


<details>
<summary>英文原文</summary>

K.10 Factorwise tail elimination for transferred tensors

</details>

对于 st333，EPOCH 发现了一个保留的优化器，其中十个一阶项中的每一项都存在一个消失的导数模式，从而消除了三次导数乘积。对所有 $3^{10}=59{,}049$ 模式进行穷尽搜索后，共找到 1,536 种可行的实现方式；所选路径的系数权重为 $(0,18,8,0)$。


<details>
<summary>英文原文</summary>

For st333, EPOCH identified a retained optimizer in which one derivative mode vanishes in each of ten rank-one terms, eliminating the cubic derivative product. An exhaustive search over all $3^{10}=59{,}049$ mode patterns found 1,536 admissible realizations; the selected path has coefficient weights $(0,18,8,0)$ and gives

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0624)

**表格与文字对照**

```text
| $R(T^{\otimes N})\leq(N+1)10^{N}.$ | | (S65)

表内文字对照（数值与原始行列保持不变）：
R(T → R(T
otimes N → 《otimes》N
leq(N → leq(N
```


<details>
<summary>英文原文</summary>

| $R(T^{\otimes N})\leq(N+1)10^{N}.$ | | (S65)

</details>

在所提供的标量计数模型中，与精确等级为11的递归方式的交叉程度从 $N=48$ 降低至 $N=39$，而与显式基场递归方式的交叉程度则从 $N=90$ 降低至 $N=81$。


<details>
<summary>英文原文</summary>

Under the supplied scalar-count model, this lowers the crossover with exact rank-11 recursion from $N=48$ to $N=39$ , and the crossover with explicit base-field recursion from $N=90$ to $N=81$ .

</details>

同样的机制也适用于 ss333 和 35项 st555 结构。对于 st555，系数权重变为 $(0,75,922,0)$，从而将所报告的两个交叉阈值从 $(41,78)$ 提升至 $(33,70)$。本次会议展示了 EPOCH 如何将关于边界结构的结构性观察转化为可量化的精度开销降低效果。


<details>
<summary>英文原文</summary>

The same mechanism transfers to ss333 and to the 35-term st555 construction. For st555, the coefficient weights become $(0,75,922,0)$ , improving the two reported crossover thresholds from $(41,78)$ to $(33,70)$ . This session shows how EPOCH can convert a structural observation about a border construction into a measurable reduction in exactification overhead.

</details>

### K.11 八阶 Smale 缩小


<details>
<summary>英文原文</summary>

K.11 Degree-eight Smale reductions

</details>

EPOCH 利用 Grace–Walsh–Szegő 定理，将最近临界点问题转化为单位圆盘上的单变量多项式问题。随后精确的 Schur 和 Sturm 证明则得以建立


<details>
<summary>英文原文</summary>

EPOCH reduced the nearest-critical-point problem to a one-variable polynomial problem on the unit disk using the Grace–Walsh–Szegő theorem. Exact Schur and Sturm certificates then establish

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0629)

**表格与文字对照**

```text
| $\left|\frac{P(b)}{b}\right|>\frac{433}{5000}\approx 0.09,$ | | (S66)

表内文字对照（数值与原始行列保持不变）：
left → 左侧
frac → 分数
P(b) → P(b)
right → 正确
approx → 约
```


<details>
<summary>英文原文</summary>

| $\left|\frac{P(b)}{b}\right|>\frac{433}{5000}\approx 0.09,$ | | (S66)

</details>

这使得在相同归一化条件下，第八阶的相应一般度估计值提高了约 $4.31$ 倍。


<details>
<summary>英文原文</summary>

which improves the corresponding general-degree estimate at degree eight by a factor of approximately $4.31$ under the same normalization.

</details>

该分析还分离出了多关键点情况，并证明了严格的界限


<details>
<summary>英文原文</summary>

The analysis also isolates the multiple-critical-point case and proves the sharp bound

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0632)

**表格与文字对照**

```text
| $\left|\frac{P(b)}{b}\right|\geq\frac{1}{8},$ | | (S67)

表内文字对照（数值与原始行列保持不变）：
left → 左侧
frac → 分数
P(b) → P(b)
right → 正确
geq → geq
```


<details>
<summary>英文原文</summary>

| $\left|\frac{P(b)}{b}\right|\geq\frac{1}{8},$ | | (S67)

</details>

通过 $[1-(1-z)^{8}]/8$ 实现相等性。该会话结合了经典约化与精确区域验证，从而得出更严格的数值界限，并给出更清晰的结构描述，用于处理任何剩余的反例。


<details>
<summary>英文原文</summary>

with equality attained by $[1-(1-z)^{8}]/8$ . The session combines a classical reduction with exact region certification, yielding both a stronger numerical bound and a sharper structural description of any remaining counterexample.

</details>

### K.12 一个有限集上的不公平多项式族


<details>
<summary>英文原文</summary>

K.12 A cofinite unfair-trinomial family

</details>

EPOCH 将有限递归模式转化为参数统一的阻碍。对于每一个满足 $k\geq 3{,}000{,}001$ < $\gcd(k,3)=1$ 的整数 $k\geq 3{,}000{,}001$ 以及每一个 $0<a<1$ ，没有非零系数且系数为非负数的多项式能够进行相乘运算


<details>
<summary>英文原文</summary>

EPOCH turned a finite recurrence pattern into a parameter-uniform obstruction. For every integer $k\geq 3{,}000{,}001$ with $\gcd(k,3)=1$ and every $0<a<1$ , no nonzero polynomial with nonnegative coefficients can multiply

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0636)

**表格与文字对照**

```text
| $1+ax^{3}+x^{k}$ | | (S68)
```


<details>
<summary>英文原文</summary>

| $1+ax^{3}+x^{k}$ | | (S68)

</details>

转化为一个系数均属于 $\{0,1\}$ 的多项式。


<details>
<summary>英文原文</summary>

into a polynomial whose coefficients all belong to $\{0,1\}$ .

</details>

该证明将递归关系划分为三个剩余类，并通过投影收缩、接缝估计、反周期 theta 核以及终端递归来控制所得到的负二项式包。精确的符号与有理重演验证了整个过程中使用的代数恒等式。此案例展示了 EPOCH 识别计算模式、确定其背后的机制，并将其推广为无限族的公理化定理的能力。


<details>
<summary>英文原文</summary>

The proof organizes the recurrence into three residue classes and controls the resulting negative-binomial packets through projective contraction, seam estimates, an antiperiodic theta kernel, and a terminal recurrence. Exact symbolic and rational replays verify the algebraic identities used throughout. This case illustrates EPOCH’s capacity to recognize a computational pattern, identify the mechanism behind it, and promote it to an explicit theorem for an infinite family.

</details>

### K.13 具有出色的稳定性及精确的无循环混合曲线


<details>
<summary>英文原文</summary>

K.13 Sharp stability and an exact loopless mixing curve

</details>

对于无环三态可逆碱基 $W_{0}$，令 $W_{t}=(1-t)+tW_{0}$ 对应 $0\leq t\leq 1$，再令 $H=K_{5,5}-C_{10}$。EPOCH 得出了精确的不等式


<details>
<summary>英文原文</summary>

For the loopless three-state reversible base $W_{0}$ , let $W_{t}=(1-t)+tW_{0}$ for $0\leq t\leq 1$ , and let $H=K_{5,5}-C_{10}$ . EPOCH obtained the exact inequality

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0641)

**表格与文字对照**

```text
| $t(H,W_{t})\geq c(t)\,t(C_{4},W_{t})^{5},\qquad c(t)=\frac{2h(t)}{(8+t^{4})^{5}},$ | | (S69)

表内文字对照（数值与原始行列保持不变）：
t(H → t(H)
geq c(t) → geq c(t)
t(C_ → t(C_
qquad c(t) → qquad c(t)
frac → 分数
h(t) → h(t)
```


<details>
<summary>英文原文</summary>

| $t(H,W_{t})\geq c(t)\,t(C_{4},W_{t})^{5},\qquad c(t)=\frac{2h(t)}{(8+t^{4})^{5}},$ | | (S69)

</details>

其中


<details>
<summary>英文原文</summary>

where

</details>

[查看原图表（阅读版）](bilingual.html#epoch-0643)

**表格与文字对照**

```text
| $\displaystyle h(t)={}$ | $\displaystyle 16384+10240t^{4}+7680t^{6}-1280t^{7}+5760t^{8}-3200t^{9}$ |
 | | $\displaystyle+2656t^{10}-1440t^{11}+440t^{12}-60t^{13}-t^{15}.$ | | (S70)

表内文字对照（数值与原始行列保持不变）：
displaystyle h(t) → \displaystyle h(t)
displaystyle → \displaystyle
```


<details>
<summary>英文原文</summary>

| $\displaystyle h(t)={}$ | $\displaystyle 16384+10240t^{4}+7680t^{6}-1280t^{7}+5760t^{8}-3200t^{9}$ |
 | | $\displaystyle+2656t^{10}-1440t^{11}+440t^{12}-60t^{13}-t^{15}.$ | | (S70)

</details>

该比例从 $1$ 增加到 $34/27$，在均匀三角形处恰好等于 $t>0$，直至所指定的缩放和重新命名规则为止。


<details>
<summary>英文原文</summary>

The ratio increases from $1$ to $34/27$ , with equality for $t>0$ precisely at the uniform triangle, up to the stated scaling and relabelling convention.

</details>

全局单调性通过6,615个正序伯恩斯坦控制、13,140个正比控制以及14个正控制构成的降低导数证书得到验证。补充的尖锐稳定性论证则由31,765个有理非负块体现。本次会议展示了EPOCH能够将大型精确证书整理为包含尖锐等式情况的透明定量定理的能力。


<details>
<summary>英文原文</summary>

Global monotonicity is certified by 6,615 positive ordered Bernstein controls, 13,140 positive ratio controls, and a reduced derivative certificate with 14 positive controls. A complementary sharp-stability argument is represented by 31,765 rational nonnegative blocks. This session demonstrates EPOCH’s ability to organize a large exact certificate into a transparent quantitative theorem with a sharp equality case.

</details>

在这些会议中，EPOCH的优势不在于执行的计算量，而在于将搜索结果转化为可复用的数学结构：优化的构造、精确不等式、统一的参数表述以及可独立重新使用的证明。


<details>
<summary>英文原文</summary>

Across these sessions, the advantage of EPOCH is not the volume of computations performed, but the conversion of search output into reusable mathematical structure: optimized constructions, exact inequalities, uniform parameter arguments, and independently replayable certificates.

</details>

