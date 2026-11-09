# AstaBench：利用科学研究任务套件严格评测 AI 智能体

AstaBench: Rigorous Benchmarking of AI Agents with a Scientific Research Suite

Bragg, Jonathan; D'Arcy, Mike; Balepur, Nishant; Bareket, Dan; Dalvi, Bhavana; Feldman, Sergey; Haddad, Dany; Hwang, Jena D.; Jansen, Peter; Kishore, Varsha; Majumder, Bodhisattwa Prasad; Naik, Aakanksha; Rahamimov, Sigal; Richardson, Kyle; Singh, Amanpreet; Surana, Harshit; Tiktinsky, Aryeh; Vasu, Rosni; Wiener, Guy; Anastasiades, Chloe; Candra, Stefan; Dunkelberger, Jason; Emery, Dan; Evans, Rob; Hamada, Malachi; Huff, Regan; Kinney, Rodney; Latzke, Matt; Lochner, Jaron; Lozano-Aguilera, Ruben; Nguyen, Cecile; Rao, Smita; Tanaka, Amber; Vlahos, Brooke; Clark, Peter; Downey, Doug; Goldberg, Yoav; Sabharwal, Ashish; Weld, Daniel S.

> 非官方机器初译，正文尚未逐段精校。图表保留原文内容，图内英文未另行翻译；有 HTML 原文的公式按原式排版。PDF 提取版保留对应原页，点击缩略图放大核对图表与公式。

原文版本：2510.21652v2 · [原始来源](https://arxiv.org/abs/2510.21652v2) · [中文 PDF](../../../output/pdf/astabench-zh-reading.pdf)

[原文第 1 页的完整图表与公式](assets/original-page-001.jpg)

## 摘要

AI 智能体有望通过自动完成文献综述、复现实验、分析数据，甚至提出新的研究方向，显著改变科研生产率。如今已有众多此类智能体，从通用“深度研究”系统到 AI Scientist、AIGS 等专门科研智能体。严格评价这些智能体对于推动进展至关重要。然而，现有基准存在多方面不足：它们往往（1）缺少对核心智能体能力进行受控比较所必需的可复现工具；（2）没有考虑模型成本、工具访问权限等混杂因素；（3）没有提供用于快速构建和评价智能体的标准接口；（4）未能全面衡量科研等真实使用场景中由产品需求驱动的任务；（5）缺少足够全面的基线来识别真正进步。为此，我们提出更严格的智能体评测原则及工具，并据此构建 AstaBench。该套件全面衡量智能体开展科学研究的能力，包含覆盖整个科学发现过程和多个科学领域的 2,400 余个问题，其中许多问题受到已部署 Asta 智能体真实用户需求的启发。套件提供首个配备生产级检索工具的科学研究环境，支持受控、可复现的评价，并更好地处理混杂因素。此外，我们提供九类面向科学任务优化的 Asta 智能体及众多基线。对 22 类智能体中的 57 个具体智能体开展的广泛评价揭示了若干发现：尤其是，尽管在某些单项能力上已有实质性进展，AI 距离解决科研辅助挑战仍有较大距离。

## 1 引言

大语言模型正被越来越多地应用于复杂的现实场景。特别是，它们有望通过自动化文献审查、复现复杂实验、分析大量数据，甚至提出新的探索方向，从而彻底改变科学研究的效率。

[原文第 2 页的完整图表与公式](assets/original-page-002.jpg)

作为会议论文发表在 ICLR 2026 上

像 OpenAI 和 Google 这样的大型机构正在投资通用“深度研究”系统，以帮助包括科学家在内的所有人更高效地筛选文献。我们甚至还有针对特定科学领域的智能体，例如 AI Scientist（Lu 等，2024；Yamada 等，2025）和 AIGS（Liu 等，2024），它们专注于科学研究领域。由于存在大量不同的智能体——许多受付费限制且均以定制化方式进行评估——最终用户和 AI 开发者如何判断哪些智能体表现最佳呢？不幸的是，现有的智能体基准测试套件在作为衡量 AI 能力的通用指标时存在诸多缺陷，尤其是其在进行科学研究方面的能力（表1）。
首先，这些套件通常缺乏必要的标准任务环境与工具，无法在公平的竞争环境中对智能体进行真实、可控的对比；例如，不存在大规模、可控的文档检索工具，因此难以判断“获胜”的智能体是具备更出色的人工智能能力，还是仅仅拥有更相关的信息来源。
其次，它们未能正确考虑混杂变量；我们并不了解那些能考虑工具使用差异的智能体评估基准，仅有少数研究如 HAL（Kapoor 等，2025）才涉及成本因素，而这一点至关重要，因为即便是简单的策略（例如通过重复调用进行多数投票）也会因增加成本而提升准确率（Kapoor 等，2024）。
第三，通用智能体使用的基准测试套件接口很少实现标准化，因为套件开发者通常认为用户只会评估包含在该套件中的智能体（因此将评估与智能体结合使用是可行的，如 OpenHands (Wang et al., 2025) 或 AutoGen (Fourney et al., 2024) 所示）；或者用户只会为特定基准测试构建专用智能体（就像 HAL (Kapoor et al., 2025) 这类通用套件那样）。
对全新智能体进行全面评估通常需要耗时的操作，包括复杂的分离处理，以及手动明确那些并非为通用智能体设计的任务说明；这会损害可重复性及可控性比较。此外，这些智能体往往缺乏基于真实产品使用数据（通常由技术公司保护）的任务设置，从而让人担心较高的得分可能无法带来实际的实际效益。最后，相关基准测试套件缺乏用于正确比较的完整智能体基线数据。
因此，大多数已发表的评估仅与其他少数智能体或改进方案进行比较，难以判断所声称的改进是否真正具有实质性进展。为应对此问题，我们提出了一套基准测试原则及基于这些原则的基准测试套件，以克服上述限制，同时提供开源资源，从而实现更严格、全面的评估。具体内容包括：

• 我们制定了用于严格评估智能体性能的准则（附录A），这些准则能够解决当前智能体评估体系存在的关键缺陷。• 依据这些准则，我们推出了 AstaBench1（第3节），这是一个更为严谨的智能体评估体系，能够全面衡量科学研究水平，涵盖多种技能——包括文献理解、数据理解、规划、工具使用、编程和搜索等——该体系包含超过2400个问题，覆盖完整的科学发现过程及多个科学领域，其中许多问题基于 Asta 提供的真实用户需求，我们已部署了若干智能体供公众使用。
很容易将新的通用智能体与 AstaBench 集成，后者提供了标准化的任务接口。• AstaBench 包含强大的 Asta 环境（第 4 节），这是首个能够使用生产级搜索工具对大量科学文献进行可控且可复现评估的智能体环境。• 我们还引入了智能体评估工具包 3（第 4.2 节），该工具包能够利用 Inspect（英国人工智能安全研究所，2024）记录到的模型使用数据，通过时间不变的成本核算来定义基准测试套件和排行榜，Inspect 是一种标准的智能体评估框架，具备广泛的模型与评估兼容性。
介绍使用此工具包构建的 AstaBench 排行榜4。这是首个能够充分考虑干扰变量（如智能体使用的工具及推理成本）的智能体排行榜。

1 https://github.com/allenai/asta-bench 2 https://asta.allen.ai 3 https://github.com/allenai/agent-eval 4 https://allenai.org/asta/leaderboard

[原文第 3 页的完整图表与公式](assets/original-page-003.jpg)

作为会议论文发表在 ICLR 2026 上

表1：AstaBench在多个方面优于现有的智能体评估基准套件。它测试的是全面的科学推理能力（即涵盖多种任务类型及多个科学领域）。其许多问题都是基于实际用户对部署的Asta智能体的请求而设计的。其标准工具环境将核心智能体功能（如规划、工具调用等）与信息访问分离开来。AstaBench的评分机制能够控制诸如计算成本之类的干扰因素，且其任务采用统一格式定义，可支持通用智能体使用。
表格最后一列标题为“Cls.”，表示用于实例化前一列中列出的智能体总数（例如使用特定大语言模型）的智能体类别数量，例如 ReAct；AstaBench 包含的智能体类别比之前的基准测试工作更多。

**表格与文字对照**

```text
Relevant for all agent benchmarks
Holistic sci. Product Controlled, Scoring accounts Tasks ready for # Agents
reasoning usage-based realistic tools for confounders general agents Total Cls.
AstaBench ✓ Broad ∼ Lit. tasks ✓ Prod.-grade ✓ Costs, tools, ✓ Decoupled, 57 22
(weighted lit. corpus openness with standard
towards CS) formats
AutoGen- × No science × × × × Coupled to 7 11
Bench agent framework
BixBench ∼ Bio data × × × ∼ Non-standard 2 2
science notebook tools
BrowserGym × No science × × × ✓ Ready for 10 2
web agents
HAL ∼ Coding × × ∼ Costs × Non-standard 113 10
formats
Inspect ∼ Coding, × × × × Non-standard 18 1
Evals knowledge formats
LAB-Bench ∼ Bio × × × × Non-standard 12 3
formats
OpenHands ∼ Coding, × × ∼ Costs × Coupled to 53 6
Evals data analysis agent framework
ScienceAgent-∼ Data × × ∼ Costs × Coupled to 17 3
Bench analysis agents
Terminal- ∼ Coding × × × ✓ Ready for 33 12
Bench terminal agents
Vector Inst. × No science × × × × Non-standard 5 1
Leaderboard formats

表内文字对照（数值与原始行列保持不变）：
Relevant for all agent benchmarks → 适用于所有智能体基准测试
Holistic sci → 整体科学
Product Controlled → 产品管控
Scoring accounts Tasks ready for → 对准备就绪的任务进行评分
Agents → 智能体
reasoning usage-based realistic tools for confounders general agents Total Cls → 用于混淆因素的基于推理的实用真实工具 通用智能体 总类别
AstaBench → AstaBench
Broad → 广泛的
Lit → 文献
tasks → 任务
Prod → 产品
grade → 等级
Costs → 成本
tools → 工具
Decoupled → 解耦
weighted lit → 加权文献
corpus openness with standard → 语料库开放性及标准要求
towards CS) formats → 面向计算机科学）格式
AutoGen- → AutoGen-
No science → 没有科学
Coupled to → 与……结合
Bench agent framework → 基准智能体框架
BixBench → BixBench
Bio data → 生物数据
Non-standard → 非标准
science notebook tools → 科学笔记工具
BrowserGym → BrowserGym
Ready for → 已准备就绪
web agents → 网络智能体
HAL → HAL
Coding → 编码
formats → 格式
Inspect → 检查
Evals knowledge formats → 评估知识格式
LAB-Bench → LAB-Bench
Bio → 生物
OpenHands → OpenHands
Evals data analysis agent framework → 评估数据分析智能体框架
ScienceAgent- → 科学智能体
Data → 数据
Bench analysis agents → 基准分析智能体
Terminal- → 终端-
Bench terminal agents → 基准测试智能体
Vector Inst → 向量实例
Leaderboard formats → 排行榜格式
```

AstaBench 准确率

智能体大语言模型任务

评分标准与大语言模型评判标准工具计算成本

图1：使用 AstaBench 在控制可用工具集的情况下，对22种智能体在多种科学任务中进行了评估，例如确保每个智能体都能访问相同的科学论文集。AstaBench 排行榜不仅记录了智能体的准确率，还显示了实现该性能所需的计算量。

• 最后，我们介绍了基于智能体的基准模型 Agents Suite5（第4.3节）。这是最全面的标准化智能体套件，包含九种针对科研任务优化的Asta智能体类别以及众多基准模型。

结合使用 AstaBench 基准测试套件、智能体环境、智能体套件和排行榜，可以全面评估大语言模型智能体在科学研究辅助方面的当前水平，同时也为持续改进提供路径（图 1）。我们针对 AstaBench 开展了一系列实验，使用了包含 57 个智能体的智能体套件，这些智能体涵盖了 22 种智能体架构类型，包括如 Asta Scholar QA 和 Asta CodeScientist 这类特定任务型智能体，以及适用于 AstaBench 中各类基准测试的通用 ReAct 风格架构。我们发现，虽然……

5 https://github.com/allenai/agent-baselines

[原文第 4 页的完整图表与公式](assets/original-page-004.jpg)

作为会议论文发表在 ICLR 2026 上

在许多方面都取得了有意义的进展，但科学研究辅助工具的完善仍远未完成。第5节总结了我们的研究结果，更多细节见附录。这些发现为我们提供了当前科学研究辅助智能体的状况概览。但这仅仅是一个起点。AstaBench能够帮助社区在新型智能体设计过程中持续且系统地评估进展情况（或缺乏进展），而这一点此前难以全面实现。我们希望AstaBench能继续通过明确的目标、注重成本的性能报告以及透明的评估机制，成为未来智能体开发的重要指导工具。

2 相关工作 我们的研究涉及两个近期的研究方向：一是开发全面智能体评估方法，以测试各种由大语言模型驱动的自动化应用（有关总体综述，请参考 Yehudai 等，2025）；二是开发新的基准测试，用于衡量大语言模型的科学推理能力及其作为科学助手和智能体的应用效果（Wang 等，2023）。我们将依次讨论这两个方向。全面智能体评估 过去几年中，旨在全面评估大语言模型推理能力的基准测试与评估框架数量激增（例如，Gu 等，2025；Gao 等，2024；Habib 等，2023；Guha 等，2024）。
鉴于大语言模型驱动的自动化趋势日益凸显，近期的工作重点集中在用于评估大语言模型智能体的新基准测试与框架上。
表1列出了与AstaBench在整体或科学智能体基准领域最相关的近期研究：AutoGenBench（Fourney等，2024）、BixBench（Mitchener等，2025）、BrowserGym（Le Sellier De Chezelles等，2025）、Holistic Agent Leaderboard（HAL）（Kapoor等，2025）、Inspect Evals（英国人工智能安全研究所、Arcadia Impact及Vector Institute，2025）、Lab-Bench（Laurent等，2024）、OpenHands Evals（Wang等，2025）、ScienceAgentBench（Chen等，2025b）、Terminal-Bench（Terminal-Bench团队，2025a）以及Vector Institute Leaderboard（Vector Institute，2025）。我们针对这些研究与AstaBench进行了比较。
维度包括：整体科学推理（即关注多种任务类型及多个科学领域）；基于产品使用的任务（即涉及基于产品用例的任务）；可控且真实的工具（即提供标准、真实的工具，以便对智能体进行可控比较）；考虑混杂因素的评分标准（即评分系统地考虑了成本、可控工具使用及其他混杂因素）；通用智能体（即任务具有统一格式，支持通用型智能体）；以及智能体的数量（即总数量及不同类别的智能体数量）。
AstaBench在这些方面表现突出，这些特点对于推动科学人工智能的发展以及提升整体基准测试的严谨性至关重要（附录A）。在科学领域方面，其他智能体基准测试套件都缺乏全面性，要么任务类别有限（例如HAL仅包含编程任务），要么领域范围受限（例如LAB-Bench仅限于生物学）；而AstaBench是唯一一个在其任务中利用配套产品Asta数据的基准测试套件。尽管其重要性不言而喻，但很少有套件真正关注成本问题（HAL是个例外），也没有任何套件提供与智能体或智能体框架无关的标准工具。
虽然一些排行榜会增加所测试智能体的数量（同样以 HAL 为例），但所有排行榜所测试的智能体类别数量都远少于 AstaBench，而 AstaBench 还通过 agent-baselines Agents Suite 提供这些智能体类别的开源代码。科学基准与科学智能体 显然，强大的大语言模型的出现使得人们对基于大语言模型的科学研究相关任务方法产生了极大的兴趣。许多新的基准测试也已被开发出来，通常专注于整个研究流程中的特定子问题，包括科学编码与执行（Tian 等，2024；Lai 等，2023；Chen 等，2025a；Chan 等，2025）。
黄等，2024年），数据分析（Majumder等，2025年；Xu等，2025年），研究复现（Bogin等，2024年；Siegel等，2025年；Tang等，2025年；Kon等，2025年；Xiang等，2025年；Starace等，2025年；Zhao等，2025年；Yan等，2025年），创意与假设生成（Ruan等，2024年；Si等，2024年；Vasu等，2025年），以及文献检索与理解（Shi等，2025年；He等，2025年）等（Zhu等，2025年）。表1中的AstaBench 6智能体数量是根据2025年8月访问的实时排行榜和仓库数据得出的，同时参考了标准基准测试文献（Microsoft，2024年；ServiceNow，2025年；普林斯顿大学SAGE团队，2025年）。
ArcadiaImpact / 英国政府BEIS团队，2025年；All-Hands-AI，2025a;b；The Terminal- Bench团队，2025b）。

[原文第 5 页的完整图表与公式](assets/original-page-005.jpg)

作为会议论文发表在 ICLR 2026 上

涵盖了许多此类任务类别，并提供了迄今为止最全面的科学智能体性能评估（表1）。大语言模型能力的提升促使了众多端到端、开放式科学探索智能体的出现，包括 AI Scientist（Lu等，2024；Yamada等，2025）、Agent Lab（Schmidgall等，2025）、AIGS（Liu等，2024）以及 CodeScientist（Jansen等，2025）等（Cheng等，2025）。为了明确这一领域的情况并加速其发展，AstaBench引入了一项新的端到端任务，用于评估智能体从创意出发，最终完成研究报告和代码编写的研究项目的能力。
我们认为这项任务是对现有众多针对研究流程中更具体问题的基准测试的有用补充。

3 ASTA BENCH：全面评估智能体科研能力的基准测试套件 我们推出了 AstaBench，这是首个用于全面评估智能体进行科研能力的标准化基准测试套件。重要的是，即使科学领域不断发展，该套件依然具有可重复性，因为它配备了首个真实的、可复现的检索工具（第4节）。该套件采用了新的智能体基准测试套件接口，并通过智能体评估工具包提供时间不变的成本报告（第4.2节）。因此，AstaBench 已准备好被新的通用智能体使用，例如我们智能体基线套件中的那些智能体（第4.3节）。

AstaBench包含以下11个评估基准（详见表2，完整细节见附录E，示例输入见附录H；注意AstaBench使用了部分引用数据集的稍作修改版本）：PaperFindingBench用于测试智能体处理具有挑战性的科学搜索查询的能力。LitQA2-FullText/LitQA2-FullText-Search（Skarlinski等，2024）用于衡量智能体回答问题及在生物医学领域检索论文的能力。ScholarQA-CS2用于测试智能体回答长篇科学问题的能力。ArxivDIGESTables-Clean（Newman等，2024）用于测试智能体生成文献综述表格的能力。
SUPER-Expert（Bogin等，2024）测试了代码智能体设置并执行ML与NLP论文中所述的Python机器学习实验的能力。CORE-Bench-Hard-（Siegel等，2025）测试了智能体复现论文中的实验与分析的能力。DS-1000（Lai等，2023）测试了智能体在研究中所涉及的数据科学任务中的能力。DiscoveryBench（Majumder等，2025）则测试了智能体能否从给定数据集中自动发现并验证假设。
E2E-Bench/E2E-Bench-Hard 的测试旨在检验智能体能否完成从构思、规划、（软件）实验设计、实现、执行、分析到最终报告生成的完整研究流程。关于这些任务评分方式的详细内容可参见附录E。部分测试使用大语言模型作为评判者，根据评分标准对输出结果进行评估（如 PaperFindingBench、ScholarQA-CS2、ArxivDIGESTables-Clean、DiscoveryBench、E2E-Bench、E2E-Bench-Hard），而另一些则采用程序化评估方式（如 LitQA2-FullText、LitQA2-FullText-Search、SUPER-Expert、CORE-Bench-Hard、DS-1000）。

4 A STA E NVIRONMENT 据我们所知，Asta Environment是首个真实的、可复现的智能体科研环境。它提供标准化工具、评估工具包、排行榜以及众多智能体。

### 4.1 智能体的标准工具

Asta Environment提供了一整套用于科学研究辅助的标准工具，每个AstaBench任务都根据自身需求包含特定的工具子集（表2）。Asta Scientific Corpus是一种用于访问科学文献的工具集，它代表了首个适用于智能体的可重复使用的生产级搜索工具。这些工具可以限制输出结果为特定日期之前的论文；AstaBench利用这一功能将结果限制在基准测试创建的日期，从而防止新论文影响结果（具体任务的截止日期请参见表2）。
该片段搜索工具可以进一步限制为具有特定 ID 的论文，从而能够作为文本检索工具使用；同时，它去除了原始 CORE-Bench-Hard 中需要 GPU 的任务，详见附录 E。

[原文第 6 页的完整图表与公式](assets/original-page-006.jpg)

作为会议论文发表在 ICLR 2026 上

表2：AstaBench评估基准，涵盖四个任务类别：文献理解、代码与执行、数据分析以及端到端发现。
当与“工具”列中列出的 Asta 环境工具结合使用时，这些基准测试可以完全复现：这些工具是每个基准测试的标准配置，包括计算笔记本（代码）或 Asta 科学语料库（语料）工具，这些工具仅包含指定“日期截止日”之前的论文。（原始数据集经过筛选，以确保问题能够在该环境中得到解答。）‡ 对于 ArxivDIGESTables-Clean 项目，语料库工具仅限于使用特定论文编号进行片段搜索来解答各个问题。∗ 表示由我们创建，† 表示之前未发布。

**表格与文字对照**

```text
Name Task category Domains Test Val Tools Date Cutoff
∗
PaperFindingBench † Lit. Und. (search) CS 267 66 Corpus 2025-06-01
LitQA2-FullText-Search Lit. Und. (search) Biology 75 10 Corpus 2024-10-17
ScholarQA-CS2 ∗ † Lit. Und. (report) CS 100 100 Corpus 2025-05-01
LitQA2-FullText Lit. Und. (MC) Biology 75 10 Corpus 2024-10-17
ArxivDIGESTables-Clean ∗ Lit. Und. (table) Mixed 100 70 Snippet‡ Paper IDs
SUPER-Expert ∗ Code & Exec. CS 45 50 Code —
CORE-Bench-Hard− Code & Exec. Mixed 37 35 Code —
DS-1000 Code & Exec. CS 900 100 Code —
DiscoveryBench ∗ Data Analysis Mixed 239 25 Code —
∗
E2E-Bench † End-to-End Disc. CS 40 10 Code —
E2E-Bench-Hard ∗ † End-to-End Disc. CS 40 10 Code —

表内文字对照（数值与原始行列保持不变）：
Name Task category Domains Test Val Tools Date Cutoff → 名称 任务类别 领域 测试 验证 工具 日期截止日
PaperFindingBench → 论文发现基准
Lit → 文献
Und → Und
search) CS → 搜索) CS
Corpus → 语料库
LitQA → LitQA
FullText-Search Lit → 全文搜索文献
search) Biology → 搜索）生物学
ScholarQA-CS → ScholarQA-CS
report) CS → 报告) CS
FullText Lit → 全文文献
MC) Biology → MC) 生物学
ArxivDIGESTables-Clean → ArxivDIGESTables-Clean
table) Mixed → 表格）混合
Snippet → 片段
Paper IDs → 论文编号
SUPER-Expert → 超级专家
Code → 代码
Exec → 执行
CORE-Bench-Hard → CORE-Bench-Hard
Mixed → 混合
DS- → DS-
DiscoveryBench → DiscoveryBench
Data Analysis Mixed → 数据分析混合
E-Bench → E-Bench
End-to-End Disc → 端到端判别
E-Bench-Hard → E-Bench-Hard
```

关于这些论文的机制（适用于详细的文献分析，例如在 ArxivDIGESTables- Clean 中）。它通过 MCP（模型上下文协议）标准提供以下特定工具：snippet_search、search_papers_by_relevance、get_paper、get_paper_batch、get_citations、search_authors_by_name、get_author_papers、search_paper_by_title。计算笔记本：一个状态化的计算型（Jupyter）笔记本。该工具可以执行 Python 代码以及标准的 IPython magic 命令，如 %%writefile、%matplotlib inline 和!shell_command。Python 变量和环境在调用之间得以保持，因此该工具可用于逐步解决问题。
默认情况下，如果单个单元格的执行时间超过5分钟，该工具会向智能体返回超时消息。由于该工具需要执行代码，它运行在由框架生成的新沙箱镜像中。与其他套件相比，我们的工具具有更好的智能体兼容性。它们与智能体完全解耦，并通过MCP实现轻松集成。在我们的沙箱中执行的代码可以调用主执行环境提供的工具（例如Asta Scientific Corpus），从而能够测试代码执行智能体，例如实现CodeAct（Wang等人，2024）模式的智能体。

4.2 智能体 - 版本评估工具包与稳定化进度板

我们采用 Inspect（英国人工智能安全研究所，2024）作为实施个人智能体基准测试的框架，因为它具备广泛的模型提供方与工具兼容性、实用的日志记录与调试功能，以及不断增加的兼容评估方案（英国人工智能安全研究所、Arcadia Impact及Vector Institute，2025）。然而，Inspect 的日志仅记录模型使用情况（而非标准化金额），且缺乏用于定义具有统一评分或排行榜的基准测试套件的工具。
为了填补这一空白，我们推出了 agent-eval8 智能体排行榜工具包，该工具包在一系列 Inspect 格式基准测试之上提供了评估套件、报告功能以及排行榜模块；其特点包括：时间不变的成本计算：agent-eval 工具包根据通过 Inspect 记录的模型使用情况来计算标准化美元成本。
为了将模型使用情况与价格进行对应，我们使用了 Litellm 成本图的冻结快照，该快照由社区共同生成，能够覆盖多种模型。该模型考虑了利用缓存的智能体所享受到的缓存折扣，因为这是一种越来越被采用的优化技术（如 OpenAI 等提供商会自动提供这些折扣）；然而，我们还根据 Together AI (ther.ai/) 通用的模型规模定价方式，为定制模型补充了价格信息。

[原文第 7 页的完整图表与公式](assets/original-page-007.jpg)

作为会议论文发表在 ICLR 2026 上

它没有考虑任何与延迟相关的折扣（例如服务等级或批量处理）。
使用冻结快照可以公平地比较评估成本，即使不同评估之间的 API 价格发生变化。10 考虑混杂因素的报告：除了成本之外，智能体评估工具包和排行榜根据可重复性及控制程度，按照以下维度对智能体评估提交进行分类（完整定义见附录 B）：• 智能体开放性（智能体实现是否开源？）：开源、开放权重（✓）、开源、封闭权重（∼）、闭源且提供 API（A），或仅封闭且仅有 UI（×）• 智能体工具支持情况（智能体是否使用提供的标准工具完成任务？）：标准工具（✓）、自定义界面（∼），或完全自定义（×）
排行榜网页界面：除了基于 agent-eval CLI 的排行榜界面外（该界面目前无法向公众提供认证，适用于 AstaBench），我们还提供了 AstaBench Leaderboard11 的网页应用界面，支持外部提交（通过 Hugging Face 用户认证），并提供交互式图表和表格。

### 4.3 基于智能体的低代码智能体套件

为了能够在 AstaBench 及其他基准测试中实现全面评估并推动技术进展，我们提供了基于智能体的基线工具集 Agents Suite，该套件包含来自 16 种智能体类别的大量智能体，并具备与 Inspect 兼容的标准接口。表 3 列出了这些智能体，分为 (1) 针对科研任务优化的 Asta 智能体，以及 (2) 我们正在评估的众多基线智能体。详细描述请参见附录 F。

## 5 项实验

我们现在将展示实验结果，这些结果也被用于构建交互式 AstaBench 排行榜的基准数据。我们的实验在数月时间内进行。由于通过增加计算资源（例如使用重复处理和多数投票）可以提高得分（Dodge等人，2019），因此我们同时报告了成本与准确率数据，以及测量值的标准差。为了简洁起见，当智能体使用多种不同模型进行测试时，我们仅报告最佳结果及其他重要的数据点。所有结果以及成本与准确率关系的图表（包括显示特定成本下最佳智能体的帕累托前沿图）均见于附录 D。
某些智能体（例如 ReAct）能够尝试所有11项基准测试；另一些则仅适用于特定类别或特定基准测试。表4展示了那些能够完成所有基准测试的智能体的整体结果，以及至少能在某一类别中解决所有基准测试的智能体。出于篇幅考虑，类别和基准测试特定的结果则放在附录C中。如上所述，基于封闭权重大语言模型的智能体目前远远优于基于开放权重大语言模型的智能体。另一方面，简单地更换底层大语言模型为最新最先进的型号，并不一定能确保在 AstaBench 测试中取得成功。
作为一个例子，最新的大语言模型之一 gpt-5 在三个评估指标上有所提升，但在其他指标上则没有显著改善。实际上，gpt-5 还会降低某些专业智能体的性能。专为科学研究辅助而设计的工具可以显著帮助人工智能智能体。这一点在 Asta v0 上表现得最为明显，其得分比下一个最佳智能体 ReAct 高约 9%，后者使用 gpt-5 时的得分为 53.0%，而 Asta v0 为 44.0%。然而，这伴随着更高的开发成本以及（对于某些任务，尤其是端到端探索任务）更高的推理成本。
没有任何商业科学研究智能体能够在 AstaBench 中完成所有研究任务。表现最好的基于 API 的智能体（FutureHouse Falcon）以及最好的封闭型智能体……用于排行榜的成本图快照可能会定期更新，但我们将始终根据当前快照重新计算所有成本，以确保比较公平。11 https://allenai.org/asta/leaderboard 12 https://github.com/allenai/agent-baselines 由于部分智能体为闭源代码，无法在新输入下使用，因此评估的智能体数量略低于 22 个；不过，我们提供了基于实验获得的缓存答案来复现这些结果的方法。
14 https://allenai.org/asta/leaderboard

[原文第 8 页的完整图表与公式](assets/original-page-008.jpg)

作为会议论文发表在 ICLR 2026 上

表3：Agent-baselines智能体套件中的智能体类别，顶部部分为Asta智能体，底部部分为基准智能体。“标准”工具意味着仅使用与AstaBench任务一同提供的工具；“自定义界面”表示使用标准的日期限制搜索功能，但也可能使用额外的自定义工具；“完全自定义”则意味着工具均为自定义设计，不使用标准搜索工具。

**表格与文字对照**

```text
Name Task optimization Open- Tooling
source
Asta Paper Finder Lit. Und. (search) ✓ Yes ∼ Custom interface
Asta Scholar QA Lit. Und. (report) ✓ Yes ∼ Custom interface
Asta Scholar QA (w/ Tables) Lit. Und. (report) ✓ Yes ∼ Custom interface
Asta Table Synthesis Lit. Und. (table) ✓ Yes ∼ Custom interface
Asta Code Code & Execution ✓ Yes ∼ Custom interface
Asta DataVoyager Data Analysis ✓ Yes ∼ Custom interface
Asta Panda End-to-End Disc. ✓ Yes × Fully custom
Asta CodeScientist End-to-End Disc. ✓ Yes × Fully custom
Asta v0 Multi ✓ Yes × Fully custom
ReAct None (general) ✓ Yes ✓ Standard
Smolagents Coder None (general) ✓ Yes ∼ Custom interface
You.com Search API Lit. Und. (search) × × Fully custom
Elicit Lit. Und. (report) × × Fully custom
FutureHouse Crow Lit. Und. (report) × × Fully custom
FutureHouse Falcon Lit. Und. (report) × × Fully custom
OpenAI Deep Research Lit. Und. (report) × × Fully custom
OpenSciLM Lit. Und. (report) ✓ Yes ∼ Custom interface
Perplexity Sonar Deep Research Lit. Und. (report) × × Fully custom
SciSpace Deep Review Lit. Und. (report) × × Fully custom
STORM Lit. Und. (report) ✓ Yes × Fully custom
You.com Research API Lit. Und. (report) × × Fully custom
Faker End-to-End Disc. ✓ Yes ✓ Standard

表内文字对照（数值与原始行列保持不变）：
Name Task optimization Open- Tooling → 名称 任务优化 开放工具
source → 来源
Asta Paper Finder Lit → Asta 论文查找器软件
Und → Und
search) → 搜索）
Yes → 是
Custom interface → 自定义界面
Asta Scholar QA Lit → Asta Scholar 问答文学
report) → 报告)
Asta Scholar QA (w/ Tables) Lit → Asta Scholar QA（含表格）文学类
Asta Table Synthesis Lit → Asta 表格综合文献
table) → 表格）
Asta Code Code → Asta 代码 代码
Execution → 执行
Asta DataVoyager Data Analysis → Asta DataVoyager 数据分析
Asta Panda End-to-End Disc → Asta Panda端到端推理
Fully custom → 完全定制
Asta CodeScientist End-to-End Disc → Asta CodeScientist端到端检索
Asta v → Asta v
Multi → 多模态
ReAct None (general) → ReAct 无（通用）
Standard → 标准
Smolagents Coder None (general) → 小型智能体 编码者 无（通用）
You → 你
com Search API Lit → com 搜索 API 说明
Elicit Lit → 收集文献资料
FutureHouse Crow Lit → FutureHouse Crow Lit
FutureHouse Falcon Lit → FutureHouse Falcon 文学
OpenAI Deep Research Lit → OpenAI 深度研究文献
OpenSciLM Lit → OpenSciLM 文献
Perplexity Sonar Deep Research Lit → Perplexity Sonar 深度研究文献
SciSpace Deep Review Lit → SciSpace 深度评审文献
STORM Lit → STORM Lit
com Research API Lit → com Research API Lit
Faker End-to-End Disc → Faker端到端检测
```

**表格与文字对照**

```text
Overall Literature Understanding Efficiency Frontier
0.6 Asta Panda (claude-sonnet-4)
0.4 Asta v0 (mixture)
0.4 Asta_CodeScientist (claude-3-7-sonnet)
Score

表内文字对照（数值与原始行列保持不变）：
Overall Literature Understanding Efficiency Frontier → 整体文献理解效率边界
Asta Panda (claude-sonnet- → Asta Panda (claude-sonnet-)
Asta v → Asta v
mixture) → 混合）
Asta_CodeScientist (claude- → Asta_CodeScientist (claude-
sonnet) → 十四行诗）
Score → 评分标准
```

**表格与文字对照**

```text
Faker (gpt-4.1 )
0.2 0.2 React (claude-3-5-haiku)
React (gpt-4.1)
0.0 0.0 React (gpt-5)
10 2 10 1 100 10 2 10 1 100 React (gpt-5-mini)
Code & Execution Data Analysis React (o3)
Smolagents (gpt-4.1)
0.6 0.4 Smolagents (gpt-5)
Smolagents (gpt-5-mini)
0.4 Smolagents (llama-4-scout)
Score

表内文字对照（数值与原始行列保持不变）：
Faker (gpt- → Faker (gpt-
React (claude- → React (claude-
haiku) → 俳句
React (gpt- → React (gpt-
mini) → 迷你版
Code → 代码
Execution Data Analysis React (o → 执行数据分析 React（或）
Smolagents (gpt- → 小型智能体（GPT-）
Smolagents (llama- → 小型智能体（llama-
scout) → scout)
Score → 评分标准
```

**表格与文字对照**

```text
0.2
0.2 Asta DataVoyager (claude-sonnet-4, gpt-4o )
Asta DataVoyager (gpt-4.1 , gpt-4o )
0.0 0.0 Asta DataVoyager (gpt-5 , gpt-4o )
10 2 10 1 100 10 3 10 2 10 1 Asta DataVoyager (gpt-5 :effort=minimal, gpt-4o )
Asta DataVoyager (o3 , gpt-4o )
End-to-End Discovery Cost (USD) Asta Panda (gpt-4.1 )
React (claude-sonnet-4)
0.6 React (gpt-4o)
React (gemini-2.5-flash)
Score

表内文字对照（数值与原始行列保持不变）：
Asta DataVoyager (claude-sonnet- → Asta DataVoyager (claude-sonnet-)
gpt- → gpt-
o ) → o )
Asta DataVoyager (gpt- → Asta DataVoyager (gpt-
effort → 努力
minimal → 最小的
Asta DataVoyager (o → Asta DataVoyager（或
End-to-End Discovery Cost (USD) Asta Panda (gpt- → 端到端发现成本（美元）Asta Panda（gpt-
React (claude-sonnet- → React (claude-sonnet-)
React (gpt- → React (gpt-
React (gemini- → React（Gemini-
flash) → 闪存）
Score → 评分标准
```

**表格与文字对照**

```text
0.4 React (llama-4-scout)
Smolagents (claude-3-5-haiku)
0.2 Smolagents (claude-sonnet-4)
Smolagents (gpt-4o)
0.0 Smolagents (gemini-2.5-flash)
10 2 10 1 100 101
Cost (USD)
Figure 2: Score vs. cost analysis for overall and category results (from Tables 4, 11, 16 and 17).
Points indicate means. Points on the Pareto frontier are connected with dotted lines, representing
optimal quality-cost trade-offs for each category (Literature Understanding, Code & Execution, Data
Analysis, End-to-End Discovery). † denotes models not pinned to a date-stamped version. Note: the
x-axis (cost per answer in dollars) uses a log scale. For more detailed plots for individual categories
and benchmarks, see Appendix D.

表内文字对照（数值与原始行列保持不变）：
React (llama- → React (llama-
scout) → scout)
Smolagents (claude- → 小型智能体（claude-
haiku) → 俳句
Smolagents (claude-sonnet- → 小型智能体（claude-sonnet-
Smolagents (gpt- → 小型智能体（GPT-）
Smolagents (gemini- → 小型智能体（Gemini-
flash) → 闪存）
Cost (USD) → 成本（美元）
Figure → 图
Score vs → 得分与
cost analysis for overall and category results (from Tables → 整体及类别结果的成本分析（来自表格）
and → 并且
Points indicate means → 分数表示意义
Points on the Pareto frontier are connected with dotted lines → 帕累托前沿上的点用虚线连接
representing → 表示
optimal quality-cost trade-offs for each category (Literature Understanding → 各类别的最佳质量与成本权衡（文献理解）
Code → 代码
Execution → 执行
Data → 数据
Analysis → 分析
End-to-End Discovery) → 端到端发现
denotes models not pinned to a date-stamped version → 表示未锁定到特定版本日期的模型
Note → 注意
the → 该
x-axis (cost per answer in dollars) uses a log scale → x轴（每答案成本，以美元计）采用对数刻度
For more detailed plots for individual categories → 针对各个类别的更详细图表
and benchmarks → 以及评估标准
see Appendix D → 见附录 D
```

[原文第 9 页的完整图表与公式](assets/original-page-009.jpg)

作为会议论文发表在 ICLR 2026 上

其中一个（OpenAI Deep Research）在大语言模型文献理解方面表现良好，但无法提供全面的科学研究辅助服务。由于从完全开放到完全封闭的各种智能体整体得分普遍较低，科学研究辅助问题仍远未解决。例如：最佳开源智能体使用开放权重的大语言模型得分仅为11.1%（Smolagents Coder with Llama-4-Scout-17B- 16E-Instruct）（表4）。而最佳开源智能体使用封闭大语言模型则表现更好：得分为53.0%（Asta v0）（表4）。
虽然最佳的基于 API 的智能体（FutureHouse Falcon）和封闭型智能体（OpenAI Deep Research）在单一基准测试中的得分很高（见表 6），但在各种任务中却存在局限。Asta 排行榜的帕累托曲线揭示了不同智能体在成本与性能之间的权衡关系，提供了许多有价值的见解。最经济高效的模型是使用 gpt-5-mini 的 ReAct 模型，其得分为 32%，比表现最好的模型高出 21%（绝对值），而每个问题的成本则低了约一个数量级，仅为 0.04 美元。使用昂贵的模型来驱动通用智能体反而可能降低整体成本。
尽管与 o3 或 sonnet 相比，Gemini-Flash 和 Llama-Scout 的每个标记成本低 3 到 25 倍，但较弱的模型往往需要更多步骤或陷入循环，导致 ReAct 智能体不仅成本更高，性能也较差。令人惊讶的是，我们大多数专用智能体（Asta Scholar QA（表 6）、Asta DataVoyager（表 4）、Asta Code（表 8））在使用 GPT-5 时的表现不如使用之前版本的模型，而 ReAct 则表现得更好。对此的一种可能解释是，GPT-5 经过调整，能够很好地适应当前常见的 ReAct 风格工作流，而相比之下可能对其他工作流适应性较低。
如果这一情况确实如此，且趋势持续下去，特定应用场景中的工作流程可能会逐渐失去价值。作为 ReAct 背后的大语言模型，gpt-5 相对于 o3 的提升幅度通常较小，大多数基准测试中的提升仅达到 0% 至 5%。然而，gpt-5 在四个基准测试中取得了显著进步：在 ScholarQA-CS2 上绝对提升 13.4%（表 6），在 SUPER-Expert 上提升 24.8%（表 8），在 LitQA2- FullText-Search 上提升 25.3%（表 5），在 E2E-Bench-Hard 上提升 21.1%（表 10）。总体而言，如今的智能体在文献理解方面已经相当出色。
然而，尽管近期取得了一些进展，编程、实验执行、数据分析以及数据驱动发现仍是大语言模型科学辅助智能体面临的主要未解决问题。文献理解方面：对于文献搜索智能体而言，Asta Paper Finder是一个出色的系统，在PaperFindingBench和LitQA2-FullText-Search测试集上的得分远高于其最接近的竞争对手ReAct（见表5）。尽管如此，很明显文献查找任务远未“解决”，还需要进一步研究才能取得真正全面的结果。
对于文献问答智能体而言，我们的结果（表6）表明：（除其他因素外）：最佳模型在该类别中的表现相对较好，得分约为80%。这很可能是因为许多针对特定任务的智能体一直将文献理解作为重点研究领域（或者相反，社区也专注于文献理解，因为该类别特别适合语言模型）。Asta Scholar QA、Elicit 和 SciSpace Deep Review是这些测试中的最佳工具（在ScholarQA-CS2上均获得约85%或更高的分数，见表6）。对于这三种工具而言，较高的表现源于评估中的引用子分数。
其他外部/商业智能体也并不落后，但表现也未能显著优于最佳的 ReAct 基准模型。考虑到 ReAct 的简洁性，这一结果确实令人惊讶，同时也表明该任务具有挑战性——系统响应需要精确且涵盖相关要点，同时必要时还需引用正确的支持来源来支撑主张。对于文献综述表格生成智能体而言，我们的结果（表7）表明：即便是最优秀的模型，在这一类别中也尚未达到优异水平，召回率约为43%，这很可能是因为在该领域构建针对任务优化的智能体的努力有限。
由 GPT-5 支持的 Asta Table Synthesis 在这项任务中获胜，超越了最优秀的通用智能体。然而，由 GPT-5-mini 支持的 Asta Table Synthesis 也表现出具有竞争力的性能，其成本仅为后者的 13%。代码与执行：代码与执行问题远未解决——所有智能体在这项任务中的得分都较低，例如，除两个外，所有智能体的 SUPER-Expert 得分均低于 25%，而使用 GPT-5 的 ReAct 方式则得分为 41%

[原文第 10 页的完整图表与公式](assets/original-page-010.jpg)

作为会议论文发表在 ICLR 2026 上

gpt-5-mini的得分为37%；参见表8和表15）。因此，编码与执行仍然是辅助和自动化科学工作的主要瓶颈。使用gpt-5的效果具有高度不可预测性。令人惊讶的是，使用gpt-5运行通用ReAct智能体能显著提升其性能（相比使用其他大语言模型），而使用更定制化的Smolagents Coder智能体则会导致性能下降。一种可能的解释是，gpt-5是为常见的ReAct工作流调整的，因此对其他工作流适应性较差。数据分析：同样，自动化的数据分析与数据驱动的发现也是科学辅助智能体面临的重要且未解决的挑战。
我们看到这些智能体在应对这一基准测试时面临困难，尽管社区中的关注度有所提升，最高得分仅为 34%（表 4）。端到端发现问题：端到端发现问题仍远未得到有意义的解决。虽然平均研究步骤完成得分看起来合理（约 70%，表 10），但完成所有实验步骤的可能性几乎为零。例如，假设每个实验包含约 10 个步骤，且每个步骤的成功率为 70%，那么完成整个实验的所有步骤的成功率约为 0.710，即 3%（具体数值见表 20，最高可达 5%）。
还需要更多的工作，我们希望这些基准测试能有助于推动相关研究向这个方向发展。

## 6 结论与未来工作

总结来说，我们指出了当前智能体基准测试方法的局限性，并提出了更严谨的实施方法和工具。通过这些方法和工具，我们推出了 AstaBench——一套用于科学研究的全面基准测试套件，能够解决关键问题。AstaBench是首个包含标准环境与工具的智能体基准测试套件，可帮助进行可控的智能体比较：包括 Asta 环境，这是首个具备真实、可控搜索工具的智能体科研环境。
同时，我们还推出了基于智能体的基准测试套件——Agents Suite，这是一个标准化的智能体集合工具。我们利用该套件在 AstaBench 上进行了实验，共使用了 57 个智能体，涵盖 22 种架构类型。实验结果揭示了一些有趣的发现，最重要的是，尽管在某些具体方面取得了显著进展，但智能体人工智能仍远未能解决科研辅助的挑战。我们邀请社区成员向由我们的智能体评估工具包支持的 AstaBench 排行榜提交作品。这项工作为智能体人工智能、科研辅助以及自动化科学发现领域带来了许多令人兴奋的机遇。
我们正在积极推动 AstaBench 中的性能与成本边界突破，通过开发适用于科学研究的新型智能体技术、工具及开放模型，缩小真正开放智能体的差距。我们还提升了智能体处理复杂上下文的能力，从改进 Asta v0 的简单调度技术到应对复杂研究项目中的长期任务。我们继续研究如何优化我们的 LLM作为评判者的评分流程，尤其是针对具有挑战性的科学发现任务。我们计划开发基于最新科学知识的全新基准问题，这些问题能够抵抗污染并超出模型的训练截止日期。
我们还计划构建测试人类协作多种方面的基准测试，并扩大在生物医学等具有影响力的领域中的问题覆盖范围。最后，我们致力于持续衡量最新进展——既通过测试最新的大语言模型，也通过向基于智能体的基线模型中添加更多智能体架构来实现。

## E THICS 状态报告

我们严格遵循高标准的伦理准则。针对本研究中所呈现的所有材料，我们都进行了法律审核。用于文献理解任务的新现实场景用户查询是在获得用户同意的前提下收集的。我们还对那些被我们纳入工具包中使用的基准测试以及所采用的智能体进行了署名，并引用了相关文献。在评估现有智能体时，我们在可能的情况下与这些智能体的开发者合作，以确保评估的公平性，包括 Elicit、Future House 和 SciSpace。

[原文第 11 页的完整图表与公式](assets/original-page-011.jpg)

作为会议论文发表在 ICLR 2026 上

## 可复现性声明

我们特别注重确保该过程的可复现性；实际上，可复现性正是我们基准测试套件的核心价值主张。AstaBench 提供了所有包含的基准测试、智能体及核心基础设施的开源代码，以及所有实验报告的日志。该框架还会记录特定仓库的提交信息，包括数据相关的提交。AstaBench 中的智能体工具通过提供对相关文档语料的限制日期访问权限，从而提升可复现性。

作者贡献

各章节中的作者按字母顺序排列：

• 项目领导、框架及智能体开发：Jonathan Bragg、Mike D’Arcy
• 按任务类别的研究（基准测试与智能体）：
– 文献理解（论文发现）：Dan Bareket、Yoav Goldberg、Sigal Rahamimov、Aryeh Tiktinsky、Guy Wiener
– 文献理解（摘要与问答）：Nishant Balepur、Doug Downey、Sergey Feldman、Dany Haddad、Jena D. Hwang、Varsha Kishore、Aakanksha Naik、Amanpreet Singh、Daniel S.
Weld – 文献理解（表格生成）：* 基准测试：Aakanksha Naik * 智能体：Mike D’Arcy、Dany Haddad、Aakanksha Naik – 代码与执行：Mike D’Arcy、Kyle Richardson – 数据分析：Bodhisattwa Prasad Majumder、Harshit Surana – 端到端发现：Peter Clark、Bhavana Dalvi、Peter Jansen、Rosni Vasu • 工程方面：– 框架与排行榜数据：Chloe Anastasiades、Stefan Candra、Regan Huff、Rodney Kinney – 排行榜网络应用：Jason Dunkelberger、Dan Emery、Cecile Nguyen、Smita Rao、Amber Tanaka、Brooke Vlahos – 管理：Jaron Lochner、Smita Rao、Rob Evans • 设计：Matt Latzke • 支持与数据标注：Malachi Hamada • 产品管理：Ruben
Lozano-Aguilera • 管理、指导与建议：Peter Clark、Doug Downey、Yoav Goldberg、Ashish Sabharwal、Daniel S. Weld

大语言模型的应用：我们使用了基于人工智能的工具（如 Claude Code、Github Copilot、ChatGPT），用于分析数据结果、生成代码以填充图表和表格、识别错误及缺失参考文献，以及提供（辅助性的）写作帮助。

致谢

如果没有一个广泛且支持性的社区，这项工作就不可能完成。尤其要感谢：David Albright和Kyle Wiggers在沟通支持与有益反馈方面所做的贡献；Crystal Nam在法律支持上的帮助；Ali Farhadi和Sophie Lebrecht在富有洞察力的反馈与鼓励方面的支持；Stephen Kelman在设计支持上的协助；Inspect评估框架的创建者与维护者；我们所整合的外部数据集的创建者；以及为这些数据集及我们创建的数据集的构建做出贡献的数据工作者们。

[原文第 12 页的完整图表与公式](assets/original-page-012.jpg)

作为会议论文发表在 ICLR 2026 上

参考文献：Anirudh Ajith、Mengzhou Xia、Alexis Chevalier、Tanya Goyal、Danqi Chen 和 Tianyu Gao。《LitSearch：科学文献检索的检索基准》。发表于 EMNLP 2024 会议。网址：https://aclanthology.org/2024.emnlp-main.840/。

All-Hands-AI。OpenHands智能体中心，2025a。网址：https://github.com/All-Hands-AI/ OpenHands/tree/55d204ae1b5581b0e55ebbd6465c7e2211b26765/openhand s/agenthub。访问时间：2025-08-25。

All-Hands-AI。OpenHands评估排行榜，2025b。URL：https://docs.google.co m/spreadsheets/d/1wOUdFCMyY6Nt0AIqF705KN4JKOWgeI4wUGUP60krXXs/ed it?gid=0#gid=0。访问日期：2025-08-25。

ArcadiaImpact / 英国政府 BEIS 团队。检查评估仪表板，2025年。网址：https://inspectevalsdashboard-vv8euilv46.streamlit.app/。访问日期：2025年7月8日；该网站于2025年8月25日关闭。

Asai Akari、He Jacqueline、Shao Rulin、Shi Weijia、Singh Amanpreet、Chang Joseph Chee、Lo Kyle、Soldaini Luca、Feldman Sergey、D’Arcy Mike、Wadden David、Latzke Matt、Tian Minyang、Ji Pan、Liu Shengyan、Tong Hao、Wu Bohao、Xiong Yanyu、Zettlemoyer Luke S.、Neubig Graham、Weld Daniel S.、Downey Doug、Yih Wentau、Koh Pang Wei以及Hajishirzi Hanna。OpenScholar：利用检索增强的大语言模型整合科学文献。ArXiv，abs/2411.14199，2024年。URL https://api.semanticscholar.org/CorpusID:274166189.

Ben Bogin、Kejuan Yang、Shashank Gupta、Kyle Richardson、Erin Bransom、Peter Clark、Ashish Sabharwal 和 Tushar Khot。SUPER：基于研究库对智能体进行任务设置与执行评估。发表于 EMNLP 2024 会议。URL：https://aclanthology.org/2024.emnl p-main.702。

Jun Shern Chan, Neil Chowdhury, Oliver Jaffe, James Aung, Dane Sherburn, Evan Mays, Giulio Starace, Kevin Liu, Leon Maksin, Tejal Patwardhan, Lilian Weng 和 Aleksander Mádry. MLE-bench：在机器学习工程领域评估机器学习智能体。发表于 ICLR 2025 会议。URL：https://openreview.net/forum?id=6s5uXNWGIh.

Hui Chen, Miao Xiong, Yujie Lu, Wei Han, Ailin Deng, Yufei He, Jiaying Wu, Yibo Li, Yue Liu, 和 Bryan Hooi. MLR-Bench：在开放式机器学习研究中对智能体进行评估。arXiv:2505.19955, 2025a. URL https://arxiv.org/abs/2505.19955.

陈子如、陈世杰、宁玉婷、张谦恒、王博世、于博涛、李一飞、廖泽毅、魏晨、陆志同、Vishal Dey、薛明毅、Frazier N. Baker、Benjamin Burns、Daniel Adu-Ampratwum、黄旭辉、夏宁、高松、苏宇以及孙欢。ScienceAgentBench：针对数据驱动科学发现中的语言智能体进行严格评估的研究。发表于ICLR 2025b。URL https://openreview.net/forum?id=6z4YKr0GK6.

程俊燕、彼得·克拉克和凯尔·理查森。大语言模型的语言建模。arXiv:2506.20249，2025年。URL https://arxiv.org/abs/2506.20249.

Nick Craswell、Bhaskar Mitra、Emine Yilmaz、Daniel Fernando Campos 和 E. Voorhees。TREC 2020深度学习赛道综述。ArXiv，abs/2102.07662，2021年。URL：https://api.se manticscholar.org/CorpusId:212737158。

Jesse Dodge、Suchin Gururangan、Dallas Card、Roy Schwartz 和 Noah A. Smith。展示你的计算过程：改进了实验结果的报告方式。发表于 EMNLP，2019年。

Adam Fourney、Gagan Bansal、Hussein Mozannar、Cheng Tan、Eduardo Salinas、Erkang Zhu、Friederike Niedtner、Grace Proebsting、Griffin Bassman、Jack Gerrits、Jacob Alber、Peter Chang、Ricky Loynd、Robert West、Victor Dibia、Ahmed Awadallah、Ece Kamar、Rafah Hosn 和 Saleema Amershi。Magentic-One：一种用于解决复杂任务的通用多智能体系统。arXiv，abs/2411.04468，2024年。URL https://arxiv.org/abs/2411.04468.

[原文第 13 页的完整图表与公式](assets/original-page-013.jpg)

作为会议论文发表在 ICLR 2026 上

Leo Gao、Jonathan Tow、Baber Abbasi、Stella Biderman、Sid Black、Anthony DiPofi、Charles Foster、Laurence Golding、Jeffrey Hsu、Alain Le Noac’h、Haonan Li、Kyle McDonell、Niklas Muennighoff、Chris Ociepa、Jason Phang、Laria Reynolds、Hailey Schoelkopf、Aviya Skowron、Lintang Sutawika、Eric Tang、Anish Thite、Ben Wang、Kevin Wang以及Andy Zou。语言模型评估工具包，2024年7月。URL：https://zenodo.org/records/12608602. Yuling Gu、Oyvind Tafjord、Bailey Kuehl、Dany Haddad、Jesse Dodge及Hannaneh Hajishirzi。OLMES：语言模型评估的标准。发表于《NAACL发现论文集》，2025年。URL：https://arxiv.org/abs/2406.08446.
Etash Guha、Negin Raoff、Jean Mercat、Ryan Marten、Eric Frankel、Sedrick Keh、Sachin Grover、George Smyrnis、Trung Vu、Jon Saad-Falcon、Caroline Choi、Kushal Arora、Mike Merrill、Yichuan Deng、Ashima Suvarna、Hritik Bansal、Marianna Nezhurina、Reinhard Heckel、Seewong Oh、Tat-sunori Hashimoto、Jenia Jitsev、Yejin Choi、Vaishaal Shankar、Alex Dimakis、Mahesh Sathiamoor-thy 和 Ludwig Schmidt。《Evalchemy：一种后训练模型评估框架》，2024年11月。URL：https://github.com/mlfoundations/evalchemy/tree/ce5cea94 f9f0f61388d2234afb01d811ff4357f4。Nathan Habib、Clémentine Fourrier、Hynek Kydlíček、Thomas Wolf 和 Lewis Tunstall。
Lighteval：一种用于大语言模型评估的轻量级框架，2023年。网址：https://github.com/hugging face/lighteval/tree/126f908a323a6d36f718076c4748e212d7275cfe。作者：何一晨、黄冠华、冯培远、林元、张宇辰、李航、魏文楠。PaSa：一个用于全面学术论文搜索的大语言模型智能体。发表于ACL会议，2025年。网址：https://aclanthology.org/2025.acl-long.572/。作者：黄千、Vora Jian、梁珀西、Leskovec Jure。MLAgentBench：在机器学习实验中对语言智能体进行评估。发表于ICML会议，2024年。作者：Jansen Peter、Tafjord Oyvind、Radensky Marissa、Siangliulue Pao、Hope Tom、Dalvi Bhavana、Majumder Bodhisattwa Prasad、Weld Daniel S.、Clark Peter。
CodeScientist：基于代码实验的端到端半自动化科学发现方法。发表于《ACL Findings》，2025年。作者：Sayash Kapoor、Benedikt Stroebl、Zachary S. Siegel、Nitya Nadgir和Arvind Narayanan。重要的AI智能体。arXiv:2407.01502，2024年。URL：https://arxiv.org/abs/2407.01502. 作者：Sayash Kapoor、Benedikt Stroebl、Peter Kirgis、Franck Stéphane Ndzomga、Kangheng Liu和Arvind Narayanan。HAL：用于集中化且可复现的智能体评估的整体化智能体排行榜。https://github.com/princeton-pli/hal-harness, 2025年。
Patrick Tser Jern Kon、刘佳晨、朱新毅、丁秋伊、彭静佳、邢嘉荣、黄一博、邱一明、Jayanth Srinivasa、李美珍、Mosharaf Chowdhury、Matei Zaharia 和 Ang Chen。EXP-Bench：人工智能能否开展人工智能研究实验？arXiv:2505.24785，2025年。URL https://arxiv.org/abs/2505.24785. 赖宇航、李成希、王一明、张天毅、钟瑞奇、Luke Zettlemoyer、Wen-tau Yih、Daniel Fried、王思达和于涛。DS-1000：一个自然且可靠的数据科学代码生成基准测试。发表于ICML 2023年会议。Jon M. Laurent、Joseph D. Janizek、Michael Ruzo、Michaela M. Hinks、Michael J. Hammerling、Siddharth Narayanan、Manvitha Ponnapati、Andrew D. White和Samuel G.
Rodriques. LAB- Bench：评估大语言模型在生物学研究中的能力。arXiv:2407.10362，2024年。Thibault Le Sellier De Chezelles、Maxime Gasse、Alexandre Drouin、Massimo Caccia、Léo Boisvert、Megh Thakkar、Tom Marty、Rim Assouel、Sahar Omidi Shayegan、Lawrence Keunho Jang、Xing Han Lù、Ori Yoran、Dehan Kong、Frank F. Xu、Siva Reddy、Quentin Cappart、Graham Neubig、Ruslan Salakhutdinov、Nicolas Chapados 和 Alexandre Lacoste。用于网络智能体研究的BrowserGym生态系统。TMLR，2025年。URL：https://openreview.net/forum?id=5298fKGmv3。Zijun Liu、Kai Liu、Yiqi Zhu、Xuanyu Lei、Zonghan Yang、Zhenhe Zhang、Peng Li 和 Yang Liu。
AIGS：利用人工智能驱动的自动证伪技术生成科学成果。ArXiv，abs/2411.11910，2024年。URL：https://api.semanticscholar.org/CorpusID:274140961.

[原文第 14 页的完整图表与公式](assets/original-page-014.jpg)

作为会议论文发表在 ICLR 2026 上

Lu Chris、Lu Cong、Robert Tjarko Lange、Jakob N. Foerster、Jeff Clune 和 David Ha。人工智能科学家：迈向完全自动化的开放式科学发现。ArXiv，abs/2408.06292，2024年。

Bodhisattwa Prasad Majumder、Harshit Surana、Dhruv Agarwal、Sanchaita Hazra、Ashish Sabharwal 和 Peter Clark。利用大生成模型进行数据驱动发现。ICML，2024年。

Bodhisattwa Prasad Majumder、Harshit Surana、Dhruv Agarwal、Bhavana Dalvi Mishra、Abhi-jeetsingh Meena、Aryan Prakhar、Tirth Vora、Tushar Khot、Ashish Sabharwal 和 Peter Clark。DiscoveryBench：利用大语言模型实现数据驱动的发现研究。发表于 ICLR 2025 会议。URL：https://openreview.net/pdf?id=vyflgpwfJW.

Microsoft. AutoGen 智能体实现，2024年。URL：https://github.com/microsoft /autogen/tree/d4dd4a26ca5c9a7e29307cf2efef7ffec9bd23da/python/packages/autogen-ext/src/autogen_ext/agents。访问时间：2025-08-25。

Jordan Mitchener、Francisco Pineda、Yuxin Ye、Spyros Maniatis、Kenneth Holstein、Kam Dahlquist、James D. Braza、Andrew D. White 和 Samuel G. Rodriques。BixBench：用于计算生物学中基于大语言模型的智能体的全面基准测试。arXiv:2503.00096，2025年。URL https://arxiv.org/abs/2503.00096.

Benjamin Newman、Yoonjoo Lee、Aakanksha Naik、Pao Siangliulue、Raymond Fok、Juho Kim、Daniel S Weld、Joseph Chee Chang和Kyle Lo。ArxivDIGESTables：利用大语言模型将科学文献整合成表格。发表于EMNLP 2024年会议。URL：https://aclantholo gy.org/2024.emnlp-main.538/。

Vishakh Padmakumar、Joseph Chee Chang、Kyle Lo、Doug Downey 和 Aakanksha Naik。基于意图的表格构建与编辑：用于文献综述表格的意图感知架构生成与编辑方法。arXiv:2507.19521，2025年。

Pritika Ramu、Aparna Garimella 和 Sambaran Bandyopadhyay。这是一张糟糕的表格吗？对基于文本生成表格的评估进行更深入的分析。2024年EMNLP会议。URL：https://aclantholo gy.org/2024.emnlp-main.1239/。

Aymeric Roucher、Albert Villanova del Moral、Thomas Wolf、Leandro von Werra 和 Erik Kaunis- mäki。「smolagents」：用于构建优秀智能体系统的小型库。https://github.com/h uggingface/smolagents，2025。

Kai Ruan, Xuan Wang, Jixiang Hong, Peng Wang, Yang Liu, 和 Hao Sun. LiveIdeaBench：在最小上下文条件下评估大语言模型在科学创意生成中的发散思维能力。arXiv:2412.17596, 2024。URL https://arxiv.org/abs/2412.17596.

普林斯顿大学 SAgE 团队。HAL：整体智能体排行榜，2025年。网址：https://hal. cs.princeton.edu/#leaderboards。访问日期：2025年8月25日。

Samuel Schmidgall、Yusheng Su、Ze Wang、Ximeng Sun、Jialian Wu、Xiaodong Yu、Jiang Liu、Zicheng Liu 和 Emad Barsoum。智能体实验室：利用大语言模型智能体作为研究助手。发表于 arXiv，文章编号 abs/2501.04227，2025年。

ServiceNow。BrowserGym排行榜，2025年。URL：https://huggingface.co/spaces/ ServiceNow/browsergym-leaderboard。访问日期：2025-08-25。

邵一佳、江宇成、Theodore A. Kanell、徐彼得、Omar Khattab 和 Monica S. Lam。利用大语言模型从零开始撰写类似维基百科的文章，2024年。URL https://arxiv.org/abs/2402.14207.

施晓峰、李玉朵、柯谦、于龙斌、谢金新和周华。SPAR：基于大语言模型智能体的学者论文检索系统，用于提升学术搜索体验。arXiv:2507.15245，2025年。URL https://arxiv.org/abs/2507.15245.

程雷西、戴一阳和桥本隆。大语言模型能否生成新的研究思路？一项包含100多名NLP研究人员的大规模人类研究。arXiv预印本 arXiv:2409.04109，2024年。

[原文第 15 页的完整图表与公式](assets/original-page-015.jpg)

作为会议论文发表在 ICLR 2026 上

Zachary S. Siegel、Sayash Kapoor、Nitya Nadgir、Benedikt Stroebl和Arvind Narayanan。CORE-Bench：通过计算可复现智能体基准测试提升已发表研究的可信度。《TMLR》，2025年1月：1–31，2025年。URL：https://tmlr.org/papers/v2 025/01-2025paper.pdf。Amanpreet Singh、Joseph Chee Chang、Chloe Anastasiades、Dany Haddad、Aakanksha Naik、Amber Tanaka、Angele Zamarron、Cecile Nguyen、Jena D. Hwang、Jason Dunkleberger、Matt Latzke、Smita R Rao、Jaron Lochner、Rob Evans、Rodney Kinney、Daniel S. Weld、Doug Downey和Sergey Feldman。Ai2 Scholar QA：基于引用组织的文献综合工作。《ArXiv》，abs/2504.10861，2025年。
URL https://api.semanticscholar.org/CorpusID: 277786810. Michael D. Skarlinski, Sam Cox, Jon M. Laurent, James D. Braza, Michaela Hinks, Michael J. Hammerling, Manvitha Ponnapati, Samuel G. Rodriques, 和 Andrew D. White. 语言智能体能够实现超人级的科学知识综合能力. arXiv:2409.13740, 2024. URL https://arxiv.org/abs/2409.13740. 介绍了用于评估语言模型在科学文献研究任务中的表现的 LitQA2基准测试. Giulio Starace, Oliver Jaffe, Dane Sherburn, James Aung, Jun Shern Chan, Leon Maksin, Rachel Dias, Evan Mays, Benjamin Kinsella, Wyatt Thompson 等.
Paperbench：评估人工智能模型复现人工智能研究的能力。arXiv预印本 arXiv:2504.01848，2025年。唐佳斌、夏亮浩、李忠航、黄超。AI-Researcher：自主科学创新。arXiv:2505.18705，2025年。网址：https://arxiv.org/abs/2505.18705. The Terminal-Bench Team。Terminal-bench：终端环境中人工智能智能体的基准测试，2025年4月a版。网址：https://github.com/laude-institute/terminal-bench. The Terminal-Bench Team。Terminal-Bench排行榜，2025年b版。网址：https://tbench.ai/ 排行榜。访问日期：2025年8月25日。
Minyang Tian, Luyu Gao, Shizhuo Dylan Zhang, Xinan Chen, Cunwei Fan, Xuefei Guo, Roland Haas, Pan Ji, Kittithat Krongchon, Yao Li, Shengyan Liu, Di Luo, Yutao Ma, Hao Tong, Kha Trinh, Chenyu Tian, Zihan Wang, Bohao Wu, Yanyu Xiong, Shengzhu Yin, Minhui Zhu, Kilian Lieret, Yanxin Lu, Genglin Liu, Yufeng Du, Tianhua Tao, Ofir Press, Jamie Callan, Eliu Huerta 和 Hao Peng. SciCode：由科学家策划的研究编码基准。arXiv:2407.13168, 2024。URL https://arxiv.org/abs/2407.13168. 英国人工智能安全研究所与Arcadia Impact和Vector Institute。Inspect Evals：社区贡献的用于inspect ai的评估。https://github.com/UKGovernmentBEIS/ inspect_evals, 2025。
访问日期：2025-08-24。英国人工智能安全研究所。《AI审查：大语言模型评估框架》，2024年5月。网址：https://github.com/UKGovernmentBEIS/inspect_ai. Rosni Vasu、Chandrayee Basu、Bhavana Dalvi Mishra、Cristina Sarasua、Peter Clark和Abraham Bernstein。《HYPER：基于文献的假设生成与溯源技术》，2025年。网址：https://arxiv.org/abs/2506.12937. 向量实验室。向量评估排行榜，2025年。网址：https://huggingface.co/spa ces/vector-institute/eval-leaderboard。访问日期：2025-08-25。Hanchen Wang、Tianfan Fu、Yuanqi Du、Wenhao Gao、Kexin Huang、Ziming Liu、Payal Chandak、Shengchao Liu、Peter Van Katwyk、Andreea Deac等。
人工智能时代的科学发现。《自然》，620(7972):47–60，2023年。王星遥、陈阳毅、袁立凡、张一哲、李云珠、彭浩、季恒。可执行的代码操作能提升大语言模型智能体的性能。发表于ICML 2024年会议。王星遥、李博宣、宋玉凡、徐弗兰·F·许、唐向如、朱志成、潘佳艺、宋月琪、李博文、贾斯克拉特·辛格、霍安·H·特兰、李福强、马仁、郑明章、钱Bill、邵彦军、尼克拉斯·穆恩诺夫、张一哲、惠宾元、林俊阳、罗伯特·布伦南、彭浩、季恒、格雷厄姆·诺伊比格。OpenHands：一个面向AI软件开发者作为通用智能体的开放平台。发表于ICLR 2025年会议。URL：https://openreview.net/forum?id=OJd3ayDDoF。

[原文第 16 页的完整图表与公式](assets/original-page-016.jpg)

作为会议论文发表在 ICLR 2026 上

严正祥、严汉奇、欧阳书银、林贵和何玉兰。Scireplicate-bench：基于智能体驱动的算法复现的LLM评估基准。COLM会议论文集，2025年。

田泽·徐、卢鹏瑞、叶柳满山、胡翔坤和刘鹏飞。ResearcherBench：在科学探索前沿对深度人工智能研究系统进行评估。arXiv:2507.16280，2025年。URL https://arxiv.org/abs/2507.16280.

山田裕太郎、罗伯特·特雅尔科·朗格、卢聪、胡胜然、卢克里斯、雅各布·尼古拉斯·福斯特、杰夫·克伦和戴维·哈。《AI Scientist-v2》：通过智能体树搜索实现研讨会级自动化科学发现。ArXiv，abs/2504.08066，2025年。URL：https://api.semanticscholar. org/CorpusID:277741107。

肖岩、李瑞成、罗志明、王志模、李道阳、景立强、何凯宇、吴佩林、乔治·米哈洛普洛斯、张悦等。Lmr-bench：评估大语言模型智能体进行语言建模研究的能力。arXiv预印本 arXiv:2506.17335，2025年。

Asaf Yehudai, Lilach Eden, Alan Li, Guy Uziel, Yilun Zhao, Roy Bar-Haim, Arman Cohan 和 Michal Shmueli-Scheuer。基于大语言模型的智能体评估调查。arXiv:2503.16416，2025年。URL https://arxiv.org/abs/2503.16416.

赵宣磊、桑子琳、李宇轩、施奇、赵伟伦、王硕、张杜珍、韩旭、刘志远和孙茂松。Autoreproduce：基于论文传承的自动人工智能实验复现方法。arXiv预印本 arXiv:2505.20662，2025年。

朱坤伦、张佳勋、齐子恒、尚诺星、刘志佳、韩佩轩、苏悦、于浩飞、尤佳宣。SafeScientist：基于大语言模型智能体的风险意识科学发现研究。arXiv:2505.23559，2025年。URL https://arxiv.org/abs/2505.23559.

## 大语言模型智能体评估的若干原则

我们提出以下原则，以更严格地对智能体进行基准测试：

1. 任务集必须能够反映现实世界中的使用复杂性。为了判断智能体能否成为特定用例的有效助手，有必要测试多种相关任务。现实世界的产品使用为确定合适的任务提供了依据，但遗憾的是，此类数据通常由产品公司掌控（他们利用这些数据进行私有评估），无法提供给学术基准创建者使用。此外，为了衡量具备广泛能力的智能体的发展程度，任务集应要求执行一系列高级、通用的技能，如推理、规划、工具使用、搜索、编程和数据分析。
2
必须配备一个标准、真实且可复现的环境与工具，以便对人工智能能力进行可控比较。该环境应具有现实性，能够衡量智能体在现实世界中的行动能力。同时，环境与工具必须标准化且可复现，从而便于对不同智能体进行可控比较。目前大多数现有基准测试套件缺乏标准化工具，导致智能体开发者不得不使用不同的环境与工具，这使得难以判断性能差异是由更强大的人工智能能力还是其他改进所导致。
尤为重要的是，基准测试套件应提供标准的搜索工具，使其能够在可复现的测试阶段访问相同的文档语料库；然而，大规模优化后的搜索索引成本极高，而公开的搜索工具又无法实现可复现性；目前我们尚未发现任何此类公开、可复现且大规模可用的搜索工具。3. 报告必须考虑混杂变量——尤其是计算成本和工具使用情况。必须计入成本因素，因为即使是简单的策略，如多次重复任务并采用多数投票方式，也能通过节省资金来提高准确性（Kapoor等，2024；2025）。
控制工具使用因素对于区分由模型或智能体架构改进带来的收益与因能够优先访问专业信息源而获得的优势也是至关重要的。

[原文第 17 页的完整图表与公式](assets/original-page-017.jpg)

作为会议论文发表在 ICLR 2026 上

4. 任务接口必须实现标准化，以便实现通用智能体的集成。能够执行多种不同任务的通用智能体更有可能满足各种现实需求。不幸的是，大多数之前的基准测试套件要求通用智能体开发者为特定任务调整智能体，这会导致开发者偏见，并阻碍开发进程。

为了支持通用智能体的发展，任务接口应为尚未为测试任务专门开发的智能体提供“合理”的适配支持：完整的任务说明、任务所需的工具以及提交功能——所有这些都需采用标准格式。5. 需要具有标准接口的全面智能体基准测试，以衡量当前最先进水平。
必须提供一套完整的智能体基准数据集，以识别哪些智能体真正属于最先进的水平，并为未来的开发提供高质量的起点；然而当前的相关智能体套件却缺乏这一资源，导致大多数评估仅与其他少数智能体或评估器自身智能体的仿制方案进行对比。

## B E VALUATION T OOLKIT：O PENNESS与工具组件 智能体的开放性定义及基准测试中的智能体工具组件分类

• 智能体开放性描述了智能体实现的透明度和可复现性：– 开源、开放权重（✓）：智能体代码与机器学习模型权重均公开可用，能够实现完全端到端的可复现性。– 开源、封闭权重（∼）：智能体代码可获取，但依赖专有机器学习模型，只能部分复现该方法。– 闭源且提供API（A）：实现细节为专有信息，但可通过API访问系统，能够验证结果，但无法复现方法。– 封闭且仅支持UI（×）：既无代码访问权限，也无程序化API访问权限。• 智能体工具描述智能体的工具使用及执行环境
评估过程中的智能体表现：– 标准模式（✓）：仅使用评估环境中预定义的工具（如 Inspect 中 state.tools 所定义）。– 自定义界面（∼）：使用自定义工具来访问等效的基础环境，对于 AstaBench 而言，我们将其定义为 Asta 环境中的与任务相关的部分：* 文献任务：信息访问仅限于对 Asta 科学语料库进行日期限制的使用。* 代码任务：代码执行仅限于在已初始化了标准 Asta 环境沙箱 Dockerfile（或等效方案）的机器环境中运行的 IPython shell 中。– 完全自定义模式（×）：使用超出标准或自定义界面限制的工具。

[原文第 18 页的完整图表与公式](assets/original-page-018.jpg)

作为会议论文发表在 ICLR 2026 上

表4：能够解决所有任务的智能体的整体结果（其他结果见表11）。所报告的数值为针对基准统计数据的宏观平均值；置信区间未显示。†表示未锁定特定版本模型的模型。粗体表示该智能体在该列对上处于帕累托最优边界。

**表格与文字对照**

```text
Literature Code Data End-to-End
O T Agent Model Overall
Understanding & Execution Analysis Discovery
Score Cost Score Cost Score Cost Score Cost Score Cost
∼ × Asta v0 mixture 53.0 3.40 62.2 0.58 47.6 0.19 33.2 0.25 68.8 12.57
∼ ✓ ReAct gpt-5 44.0 0.31 54.6 0.30 55.0 0.35 30.5 0.09 36.1 0.49
∼ ✓ ReAct o3 39.4 0.16 46.8 0.35 49.3 0.19 33.7 0.04 28.0 0.07
∼ ∼ Smolagents claude-sonnet-4 38.1 1.02 42.7 0.71 39.6 1.96 28.8 0.24 41.5 1.19
Coder
∼ ∼ Smolagents gpt-5 37.5 0.13 46.0 0.12 30.9 0.10 26.7 0.08 46.5 0.22
Coder
∼ ✓ ReAct gpt-5-mini 31.6 0.04 36.5 0.05 50.5 0.05 26.9 0.01 12.6 0.03
∼ ✓ ReAct claude-3-5-haiku 21.9 0.04 36.2 0.03 22.4 0.05 24.3 0.01 4.6 0.04
✓ ∼ Smolagents llama-4-scout 11.1 0.11 20.0 0.03 3.6 0.12 20.2 0.01 0.5 0.27
Coder

表内文字对照（数值与原始行列保持不变）：
Literature Code Data End-to-End → 文献代码数据端到端处理
O T Agent Model Overall → O T 智能体模型整体情况
Understanding → 理解
Execution Analysis Discovery → 执行分析发现
Score Cost Score Cost Score Cost Score Cost Score Cost → 得分 成本 得分 成本 得分 成本 得分 成本 得分 成本 得分 成本 得分
Asta v → Asta v
mixture → 混合
ReAct gpt- → ReAct gpt-
ReAct o → ReAct 模式
Smolagents claude-sonnet- → 小型智能体 Claude-Sonnet-
Coder → 编码员
Smolagents gpt- → 小型智能体 GPT-
mini → 迷你
ReAct claude- → ReAct claude-
haiku → 俳句
Smolagents llama- → 小型智能体 llama-
scout → scout
```

表5：文献理解搜索基准测试结果（额外结果见表12）。†表示未锁定特定版本时间的模型。粗体表示该智能体在该列对上处于帕累托最优边界。

**表格与文字对照**

```text
O T Agent Model PaperFindingBench LitQA2-FullText-Search
Score Cost Score Cost
∼ ∼ Asta Paper gemini-2-flash, 39.7 ± 3.1 0.063 ± 0.005 90.7 ± 6.6 0.112 ± 0.007
Finder gpt-4o
∼ × Asta v0 mixture 37.6 ± 3.1 0.063 ± 0.005 90.7 ± 6.6 0.112 ± 0.007
∼ ✓ ReAct gpt-5 26.4 ± 3.9 0.428 ± 0.048 82.7 ± 8.6 0.389 ± 0.055
∼ ✓ ReAct o3 19.3 ± 3.7 0.518 ± 0.067 57.3 ± 11.3 0.790 ± 0.127
∼ ∼ Smolagents gpt-4.1 16.5 ± 3.5 0.080 ± 0.007 50.7 ± 11.4 0.095 ± 0.037
Coder
∼ ∼ Smolagents claude-sonnet-4 22.1 ± 3.5 0.975 ± 0.139 52.0 ± 11.4 1.100 ± 0.097
Coder
A × You.com – 7.2 ± 2.0 – 36.0 ± 10.9 –
Search API

表内文字对照（数值与原始行列保持不变）：
O T Agent Model PaperFindingBench LitQA → O T 智能体模型论文 研究发现 基准文献 QA
FullText-Search → 全文搜索
Score Cost Score Cost → 得分 成本 得分 成本
Asta Paper gemini- → Asta Paper gemini-
flash → 闪存
Finder gpt- → 查找器 GPT-
Asta v → Asta v
mixture → 混合
ReAct gpt- → ReAct gpt-
ReAct o → ReAct 模式
Smolagents gpt- → 小型智能体 GPT-
Coder → 编码员
Smolagents claude-sonnet- → 小型智能体 Claude-Sonnet-
You → 你
com → com
Search API → 搜索 API
```

支持实验结果 本部分包含第5节叙述内容的补充表格和图表。表4展示了尝试所有基准测试的智能体以及至少在一个类别中能够解决所有基准测试的智能体的整体结果。随后我们展示了特定类别的结果，包括文献理解（表5至表7）、代码与执行（表8）、数据分析（表9）以及端到端发现（表10）。关于所引用的智能体和模型的详细信息，请分别参阅表3和表22。
在表格中，“O”表示开放性，其数值分别为 ✓（开源、开放权重）、∼（开源、封闭权重）、A（闭源且提供 API）和 ×（封闭、仅包含用户界面）。“T”表示工具支持情况，其数值分别为 ✓（标准）、∼（自定义界面）和 ×（完全自定义）。这些开放性数值适用于智能体（包括所使用的模型）。“±”表示 95% 置信区间。加粗文字表示该智能体在该列对上处于帕累托最优边界。我们的研究结果揭示了若干值得注意的见解。

[原文第 19 页的完整图表与公式](assets/original-page-019.jpg)

作为会议论文发表在 ICLR 2026 上

表6：文献理解问答评估基准结果（其他结果见表13）。没有API的智能体无法在LitQA2-FT上进行评估。†表示未固定版本日期的模型。粗体表示该智能体在该列对上处于帕累托最优边界。

**表格与文字对照**

```text
O T Agent Model ScholarQA-CS2 LitQA2-FullText
Score Cost Score Cost
∼ ✓ ReAct gpt-5 79.8 ± 3.5 0.373 ± 0.034 82.7 ± 8.6 0.276 ± 0.114
∼ × Asta v0 mixture 87.7 ± 1.4 1.529 ± 0.291 70.7 ± 10.4 0.306 ± 0.093
A × FutureHouse Crow gpt-4.1-mini, 81.1 ± 1.7 0.107 ± 0.004 72.0 ± 10.2 0.065 ± 0.003
o3-mini,
gemini-2.5-flash
A × FutureHouse Falcon gpt-4.1-mini, 77.6 ± 1.3 0.403 ± 0.051 74.7 ± 9.9 0.220 ± 0.011
gemini-2.5-flash,
o3-mini
∼ ✓ ReAct o3 66.4 ± 3.0 0.275 ± 0.039 80.0 ± 9.1 0.347 ± 0.083
∼ ∼ Smolagents Coder gpt-5 68.4 ± 4.4 0.154 ± 0.014 73.3 ± 10.1 0.101 ± 0.026
A × Perplexity Sonar gemini-2.5-flash, 67.3 ± 1.2 0.416 ± 0.019 73.3 ± 10.1 0.219 ± 0.016
Deep Research sonar-deepresearch
∼ ∼ Smolagents Coder gpt-4.1 73.7 ± 2.1 0.080 ± 0.016 65.3 ± 10.8 0.035 ± 0.005
A × You.com Research – 55.0 ± 2.2 – 8.0 ± 6.2 –
API
∼ ∼ Asta Scholar QA (w/ claude-sonnet-4 87.9 ± 1.2 1.314 ± 0.281 – –
Tables)
†
∼ ∼ Asta Scholar QA gemini-2.5-flash 87.7 ± 1.4 0.126 ± 0.010 – –
∼ ∼ Asta Scholar QA claude-sonnet-4 86.2 ± 1.4 0.393 ± 0.030 – –
∼ ∼ Asta Scholar QA gpt-5† 85.9 ± 1.6 1.099 ± 0.074 – –
× × Elicit – 85.5 ± 1.6 – – –
× × SciSpace Deep claude-sonnet-4 84.6 ± 1.3 – – –
Review
∼ × STORM gpt-3.5-turbo, 78.3 ± 2.4 0.094 ± 0.002 – –
gpt-4o
A × OpenAI Deep o3-/o4-mini- 79.4 ± 1.4 1.803 ± 0.039 – –
Research deep-research,
gemini-2.5-pro
✓ ∼ OpenSciLM llama-3.1- 58.0 ± 2.6 0.004 ± 0.000 – –
openscholar-8b

表内文字对照（数值与原始行列保持不变）：
O T Agent Model ScholarQA-CS → O T 智能体模型 ScholarQA-CS
LitQA → LitQA
FullText → 全文
Score Cost Score Cost → 得分 成本 得分 成本
ReAct gpt- → ReAct gpt-
Asta v → Asta v
mixture → 混合
FutureHouse Crow gpt- → FutureHouse Crow 大语言模型
mini → 迷你
gemini- → Gemini-
flash → 闪存
FutureHouse Falcon gpt- → FutureHouse Falcon gpt-
ReAct o → ReAct 模式
Smolagents Coder gpt- → 小型智能体 编码师 GPT-
Perplexity Sonar gemini- → Perplexity Sonar  Gemini-
Deep Research sonar-deepresearch → 深度研究 sonar-deepresearch
You → 你
com Research → com Research
API → API
Asta Scholar QA (w/ claude-sonnet- → Asta Scholar QA（含 claude-sonnet-
Tables) → 表格）
Asta Scholar QA gemini- → Asta Scholar QA  gemsini-
Asta Scholar QA claude-sonnet- → Asta Scholar QA claude-sonnet-
Asta Scholar QA gpt- → Asta Scholar QA 大语言模型
Elicit → 激发
SciSpace Deep claude-sonnet- → SciSpace Deep claude-sonnet-
Review → 评审
STORM gpt- → STORM gpt-
turbo → 涡轮
gpt- → gpt-
OpenAI Deep o → OpenAI Deep o
mini- → 迷你-
Research deep-research → 研究深度研究
pro → pro
OpenSciLM llama- → OpenSciLM llama-
openscholar- → 开放学者
```

表7：文献研究 ArxivDIGESTables-Clean任务基准测试结果（其他结果见表14）。†表示未固定版本日期的模型。粗体表示该列对中的智能体处于帕累托最优边界。

**表格与文字对照**

```text
O T Agent Model ArxivDIGESTables-Clean
Score Cost
∼ × Asta v0 mixture 42.9 ± 3.7 0.517 ± 0.056
∼ ∼ Asta Table Synthesis gpt-5† 42.6 ± 3.5 1.281 ± 0.140
∼ ∼ Asta Table Synthesis gpt-5-mini† 41.7 ± 3.7 0.172 ± 0.019
∼ ✓ ReAct o3 32.9 ± 3.3 0.050 ± 0.004
∼ ∼ Smolagents Coder gpt-5 31.5 ± 3.2 0.060 ± 0.004

表内文字对照（数值与原始行列保持不变）：
O T Agent Model ArxivDIGESTables-Clean → O T 智能体模型 ArxivDIGESTables-Clean
Score Cost → 评分成本
Asta v → Asta v
mixture → 混合
Asta Table Synthesis gpt- → Asta Table Synthesis gpt-
mini → 迷你
ReAct o → ReAct 模式
Smolagents Coder gpt- → 小型智能体 编码师 GPT-
```

[原文第 20 页的完整图表与公式](assets/original-page-020.jpg)

作为会议论文发表在 ICLR 2026 上

表8：代码与执行类别结果（其他结果见表15）。†表示未锁定到特定版本时间的模型。粗体表示该智能体在该列对上处于帕累托最优边界。

**表格与文字对照**

```text
O T Agent Model SUPER-Expert CORE-Bench-Hard− DS-1000
Score Cost Score Cost Score Cost
∼ ✓ ReAct gpt-5 41.1 ± 12.9 0.589 ± 0.140 45.9 ± 16.3 0.443 ± 0.139 78.0 ± 2.7 0.021 ± 0.0009
∼ ✓ ReAct gpt-5-mini 34.6 ± 13.2 0.105 ± 0.046 45.9 ± 16.3 0.047 ± 0.014 71.0 ± 3.0 0.003 ± 0.0001
∼ ✓ ReAct o3 16.3 ± 9.6 0.369 ± 0.097 56.8 ± 16.2 0.196 ± 0.076 74.9 ± 2.8 0.010 ± 0.0007
∼ × Asta v0 mixture 19.4 ± 10.4 0.332 ± 0.057 48.6 ± 16.3 0.226 ± 0.093 74.8 ± 2.8 0.011 ± 0.0007
∼ ∼ Smolagents claude- 11.7 ± 8.0 3.559 ± 1.766 32.4 ± 15.3 2.199 ± 0.780 74.7 ± 2.8 0.114 ± 0.0079
Coder sonnet-4
∼ ∼ Smolagents gpt-5 3.6 ± 4.8 0.079 ± 0.023 13.5 ± 11.2 0.190 ± 0.106 75.7 ± 2.8 0.019 ± 0.0007
Coder
∼ ∼ Smolagents claude-3-5- 16.8 ± 9.6 0.812 ± 0.581 0.0000 0.332 ± 0.210 9.9 ± 2.0 0.024 ± 0.0103
Coder haiku
∼ ∼ Asta Code gpt-4.1 16.3 ± 9.4 0.285 ± 0.059 – – – –
∼ ∼ Asta Code gpt-5 13.5 ± 9.4 0.372 ± 0.072 – – – –

表内文字对照（数值与原始行列保持不变）：
O T Agent Model SUPER-Expert CORE-Bench-Hard → O T 智能体模型 超级专家核心测试平台
DS- → DS-
Score Cost Score Cost Score Cost → 得分 成本 得分 成本 得分 成本
ReAct gpt- → ReAct gpt-
mini → 迷你
ReAct o → ReAct 模式
Asta v → Asta v
mixture → 混合
Smolagents claude- → 小型智能体 Claude-
Coder sonnet- → 编码十四行诗
Smolagents gpt- → 小型智能体 GPT-
Coder → 编码员
Coder haiku → 编码俳句
Asta Code gpt- → Asta Code gpt-
```

表9：数据分析发现平台结果（其他结果见表16）。†表示未锁定到特定日期版本的模型。粗体表示该智能体在该列对上处于帕累托最优边界。

**表格与文字对照**

```text
O T Agent Model DiscoveryBench
Score Cost
∼ ✓ ReAct o3 33.7 ± 5.1 0.039 ± 0.004
∼ × Asta v0 mixture 33.2 ± 5.1 0.246 ± 0.071
∼ ∼ Asta DataVoyager o3† , gpt-4o† 31.1 ± 5.0 0.234 ± 0.061
∼ ✓ ReAct gpt-5 30.5 ± 4.8 0.092 ± 0.009
∼ ∼ Smolagents Coder claude-sonnet-4 28.8 ± 4.8 0.237 ± 0.019

表内文字对照（数值与原始行列保持不变）：
O T Agent Model DiscoveryBench → O T 智能体模型发现基准测试
Score Cost → 评分成本
ReAct o → ReAct 模式
Asta v → Asta v
mixture → 混合
Asta DataVoyager o → Asta DataVoyager o
gpt- → gpt-
ReAct gpt- → ReAct gpt-
Smolagents Coder claude-sonnet- → 小型智能体 编码师 claude-sonnet-
```

表10：端到端发现类别结果（其他结果见表17）。†表示未锁定特定版本日期的模型。粗体表示该列对中的智能体处于帕累托最优边界上。

**表格与文字对照**

```text
O T Agent Model E2E-Bench E2E-Bench-Hard
Score Cost Score Cost
∼ × Asta Panda claude- 70.5 ± 6.2 10.643 ± 0.717 68.2 ± 4.4 14.487 ± 1.050
sonnet-4
∼ × Asta v0 mixture 70.4 ± 6.3 10.643 ± 0.717 67.3 ± 5.3 14.487 ± 1.050
∼ × Asta claude-3-7- 65.3 ± 7.1 2.760 ± 0.510 64.5 ± 5.5 3.549 ± 0.692
CodeScientist sonnet
∼ ∼ Smolagents gpt-5 62.8 ± 9.8 0.205 ± 0.025 30.3 ± 10.5 0.232 ± 0.043
Coder
∼ ✓ ReAct claude- 52.5 ± 6.8 0.749 ± 0.072 38.9 ± 6.9 0.836 ± 0.057
sonnet-4
∼ ∼ Smolagents claude- 47.2 ± 6.1 0.873 ± 0.110 35.8 ± 7.8 1.512 ± 0.307
Coder sonnet-4
∼ ✓ Faker gpt-4.1† 39.2 ± 6.9 0.026 ± 0.001 25.4 ± 4.5 0.029 ± 0.001
∼ ✓ ReAct o3 34.9 ± 10.1 0.065 ± 0.010 21.0 ± 7.6 0.075 ± 0.019
∼ ✓ ReAct gpt-5 30.0 ± 11.9 0.403 ± 0.053 42.1 ± 11.4 0.584 ± 0.072

表内文字对照（数值与原始行列保持不变）：
O T Agent Model E → O T 智能体模型 E
E-Bench E → E-Bench E
E-Bench-Hard → E-Bench-Hard
Score Cost Score Cost → 得分 成本 得分 成本
Asta Panda claude- → Asta Panda claude-
sonnet- → 十四行诗
Asta v → Asta v
mixture → 混合
Asta claude- → Asta claude-
CodeScientist sonnet → CodeScientist 十四行诗
Smolagents gpt- → 小型智能体 GPT-
Coder → 编码员
ReAct claude- → ReAct claude-
Smolagents claude- → 小型智能体 Claude-
Coder sonnet- → 编码十四行诗
Faker gpt- → Faker gpt-
ReAct o → ReAct 模式
ReAct gpt- → ReAct gpt-
```

[原文第 21 页的完整图表与公式](assets/original-page-021.jpg)

作为会议论文发表在 ICLR 2026 上

表11：能够解决所有任务的智能体的整体结果。所报告的数值为针对基准统计数据的宏观平均值；为简洁起见，省略了成本置信区间。†表示未固定到特定版本时间的模型。

**表格与文字对照**

```text
Literature Code Data End-to-End
O T Agent Model Overall
Understanding & Execution Analysis Discovery

表内文字对照（数值与原始行列保持不变）：
Literature Code Data End-to-End → 文献代码数据端到端处理
O T Agent Model Overall → O T 智能体模型整体情况
Understanding → 理解
Execution Analysis Discovery → 执行分析发现
```

得分 成本 得分 成本 得分 成本 得分 成本 得分 成本 得分 成本 得分

**表格与文字对照**

```text
∼ ✓ ReAct claude-3-5- 21.9 ± 1.6 0.04 36.2 ± 2.3 0.03 22.4 ± 3.0 0.05 24.3 ± 4.7 0.01 4.6 ± 2.2 0.04
haiku
∼ ✓ ReAct claude- 40.1 ± 2.4 0.40 45.4 ± 2.3 0.36 46.2 ± 6.6 0.33 23.2 ± 4.1 0.13 45.7 ± 4.8 0.79
sonnet-4
∼ ✓ ReAct gpt-4.1 31.6 ± 2.3 0.20 46.4 ± 2.3 0.54 32.4 ± 5.1 0.09 30.5 ± 5.1 0.02 17.1 ± 5.0 0.14
∼ ✓ ReAct gpt-4o 16.2 ± 1.4 0.12 31.8 ± 2.2 0.15 18.3 ± 3.5 0.15 13.2 ± 3.7 0.04 1.5 ± 1.3 0.15
∼ ✓ ReAct gpt-5-mini 31.6 ± 2.7 0.04 36.5 ± 2.9 0.05 50.5 ± 7.1 0.05 26.9 ± 4.8 0.01 12.6 ± 5.6 0.03
∼ ✓ ReAct gpt-5 44.0 ± 3.0 0.31 54.6 ± 2.2 0.30 55.0 ± 7.0 0.35 30.5 ± 4.8 0.09 36.1 ± 8.3 0.49
∼ ✓ ReAct gemini-2.5- 15.3 ± 1.4 0.71 32.8 ± 3.0 0.46 26.0 ± 4.1 0.45 1.9 ± 1.7 0.10 0.5 ± 1.1 1.83
flash
✓ ✓ ReAct llama-4- 7.9 ± 1.1 0.68 19.8 ± 2.5 1.60 4.8 ± 1.9 0.10 5.9 ± 2.6 0.19 1.4 ± 1.2 0.82
scout
∼ ✓ ReAct o3 39.4 ± 2.6 0.16 46.8 ± 2.3 0.35 49.3 ± 6.3 0.19 33.7 ± 5.1 0.04 28.0 ± 6.3 0.07
∼ ∼ Smolagents claude-3-5- 12.7 ± 1.5 0.30 20.9 ± 1.9 0.05 8.9 ± 3.3 0.39 16.5 ± 4.1 0.02 4.5 ± 2.0 0.73
Coder haiku
∼ ∼ Smolagents claude- 38.1 ± 2.3 1.02 42.7 ± 2.4 0.71 39.6 ± 5.8 1.96 28.8 ± 4.8 0.24 41.5 ± 4.9 1.19
Coder sonnet-4
∼ ∼ Smolagents gpt-4.1 32.8 ± 2.4 0.32 43.9 ± 2.3 0.07 25.6 ± 5.2 0.11 28.4 ± 4.9 0.05 33.3 ± 6.0 1.07
Coder
∼ ∼ Smolagents gpt-4o 13.6 ± 1.6 0.36 22.7 ± 2.1 0.08 8.7 ± 3.1 0.64 17.8 ± 4.2 0.05 5.3 ± 2.6 0.67
Coder
∼ ∼ Smolagents gpt-5-mini 29.1 ± 2.3 0.06 38.5 ± 2.7 0.02 28.3 ± 4.0 0.09 27.7 ± 4.9 0.07 22.0 ± 6.1 0.08
Coder
∼ ∼ Smolagents gpt-5 37.5 ± 2.5 0.13 46.0 ± 2.5 0.12 30.9 ± 4.2 0.10 26.7 ± 4.7 0.08 46.5 ± 7.2 0.22
Coder
∼ ∼ Smolagents gemini-2.5- 26.4 ± 2.3 0.71 35.6 ± 2.5 0.05 16.6 ± 4.3 0.56 24.7 ± 4.7 0.02 28.6 ± 6.4 2.21
Coder flash
✓ ∼ Smolagents llama-4- 11.1 ± 1.4 0.11 20.0 ± 2.2 0.03 3.6 ± 2.4 0.12 20.2 ± 4.5 0.01 0.5 ± 0.4 0.27
Coder scout
∼ × Asta v0 mixture 53.0 ± 2.4 3.40 62.2 ± 2.0 0.58 47.6 ± 6.5 0.19 33.2 ± 5.1 0.25 68.8 ± 4.1 12.57

表内文字对照（数值与原始行列保持不变）：
ReAct claude- → ReAct claude-
haiku → 俳句
sonnet- → 十四行诗
ReAct gpt- → ReAct gpt-
mini → 迷你
ReAct gemini- → ReAct Gemini
flash → 闪存
ReAct llama- → ReAct llama-
scout → scout
ReAct o → ReAct 模式
Smolagents claude- → 小型智能体 Claude-
Coder haiku → 编码俳句
Coder sonnet- → 编码十四行诗
Smolagents gpt- → 小型智能体 GPT-
Coder → 编码员
Smolagents gemini- → 小型智能体 Gemini-
Coder flash → 编码员快闪
Smolagents llama- → 小型智能体 llama-
Coder scout → 编码 scout
Asta v → Asta v
mixture → 混合
```

D F 完整的实验结果 第5节展示了最佳智能体的结果（即使用最优基础模型的智能体），以及若干重要的额外数据点。此处我们展示了所有测试过的智能体配置的全部结果集（是第5节结果的超集）。我们还展示了得分与成本关系的图表，包括帕累托前沿图（显示特定成本下的最佳智能体）。在表格中，“O”表示开放性，对应值分别为 ✓（开源、开放权重）、∼（开源、封闭权重）和 ×（仅封闭且包含用户界面）。“T”表示工具支持，对应值分别为 ✓（标准）、∼（自定义界面）和 ×（完全自定义）。“±”表示95%置信区间。

统计方法学：所有置信区间均为 95% 置信区间，计算方式为 ±1.96 × SE，其中 SE 为标准误差。对于单个评估基准，标准误差是根据每个任务中各评估样本的方差计算得出的。对于类别级 qP 聚合结果，标准误差为 wi2 · SE2i / wi，其中 wiP 通过加权平均法进行解析性传播：SEcategory 即为任务权重（除两个 LitQA 任务权重为 0.5 外，其余均统一为 1.0）。这种传播假设任务之间相互独立，可能会略微低估不确定性。

[原文第 22 页的完整图表与公式](assets/original-page-022.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
PaperFindingBench
Efficiency Frontier
Asta Paper Finder (gemini-2-flash, gpt-4o)
0.40 Smolagents (gpt-5-mini)
Smolagents (llama-4-scout)
0.35
Asta v0 (mixture)
0.30 React (claude-3-5-haiku)
React (claude-sonnet-4)
0.25 React (gpt-4.1)
Score

表内文字对照（数值与原始行列保持不变）：
PaperFindingBench → 论文发现基准
Efficiency Frontier → 效率前沿
Asta Paper Finder (gemini- → Asta 文档查找器（Gemini-
flash → 闪存
gpt- → gpt-
Smolagents (gpt- → 小型智能体（GPT-）
mini) → 迷你版
Smolagents (llama- → 小型智能体（llama-
scout) → scout)
Asta v → Asta v
mixture) → 混合）
React (claude- → React (claude-
haiku) → 俳句
React (claude-sonnet- → React (claude-sonnet-)
React (gpt- → React (gpt-
Score → 评分标准
```

**表格与文字对照**

```text
React (gpt-4o)
0.20 React (gpt-5)
React (gpt-5-mini)
0.15 React (gemini-2.5-flash)
React (llama-4-scout)
0.10 React (o3)
Smolagents (claude-3-5-haiku)
0.05 Smolagents (claude-sonnet-4)
Smolagents (gpt-4.1)
0.00 Smolagents (gpt-4o)
10 2 10 1 100 Smolagents (gpt-5)
Smolagents (gemini-2.5-flash)
LitQA2-FullText-Search You.com Search API (no cost)
1.0

表内文字对照（数值与原始行列保持不变）：
React (gpt- → React (gpt-
mini) → 迷你版
React (gemini- → React（Gemini-
flash) → 闪存）
React (llama- → React (llama-
scout) → scout)
React (o → React（或
Smolagents (claude- → 小型智能体（claude-
haiku) → 俳句
Smolagents (claude-sonnet- → 小型智能体（claude-sonnet-
Smolagents (gpt- → 小型智能体（GPT-）
Smolagents (gemini- → 小型智能体（Gemini-
LitQA → LitQA
FullText-Search You → 全文搜索
com Search API (no cost) → com 搜索 API（无费用）
```

0.8

### 0.6 分

0.4

0.2

0.0 10 3 10 2 10 1 100 成本（美元）

图3：文献理解搜索基准测试的得分与成本分析（表12）。点表示平均值；误差条表示95%置信区间。帕累托前沿上的点用虚线连接，代表每个评估任务下的最优质量-成本权衡（PaperFindingBench、LitQA2-FullText-Search）。注意：x轴（成本）采用对数刻度。

[原文第 23 页的完整图表与公式](assets/original-page-023.jpg)

作为会议论文发表在 ICLR 2026 上

ScholarQA-CS2 效率前沿 Asta Scholar QA（无表格）（gemini-2.5-flash） Asta Scholar QA（无表格）（gpt-4o-mini） 0.8 Asta Scholar QA（o3） OpenSciLM（llama-3.1-openscholar-8b） React（gpt-5） 0.6 React（gpt-5-mini） Smolagents（gpt-4.1） Smolagents（gpt-5-mini） 得分

**表格与文字对照**

```text
Smolagents (llama-4-scout)
0.4 Asta Scholar QA (claude-sonnet-4)
Asta Scholar QA (No Tables) (claude-sonnet-4)
Asta Scholar QA (No Tables) (gpt-5 )
0.2 Asta v0 (mixture)
FutureHouse CROW (gpt-4.1-mini, o3-mini,
gemini-2.5-flash)
FutureHouse FALCON (gpt-4.1-mini, gemini-2.5-flash,
o3-mini)
0.0 OpenAI Deep Research (o3-deep-research-2025-06-26,
10 3 10 2 10 1 100 gemini-2.5-pro)
Perplexity Deep Research (gemini-2.5-flash, sonar-
LitQA2-FullText deep-research)
React (claude-3-5-haiku)
React (claude-sonnet-4)
React (gpt-4.1)
0.8 React (gpt-4o)
React (gemini-2.5-flash)
React (llama-4-scout)
0.6 React (o3)
STORM (gpt-3.5-turbo, gpt-4o)
Smolagents (claude-3-5-haiku)
Score

表内文字对照（数值与原始行列保持不变）：
Smolagents (llama- → 小型智能体（llama-
scout) → scout)
Asta Scholar QA (claude-sonnet- → Asta Scholar QA (claude-sonnet-
Asta Scholar QA (No Tables) (claude-sonnet- → Asta Scholar QA（无表格）（claude-sonnet-
Asta Scholar QA (No Tables) (gpt- → Asta Scholar QA（无表格）（gpt-
Asta v → Asta v
mixture) → 混合）
FutureHouse CROW (gpt- → FutureHouse CROW (gpt-
mini → 迷你
gemini- → Gemini-
flash) → 闪存）
FutureHouse FALCON (gpt- → FutureHouse FALCON (gpt-
flash → 闪存
mini) → 迷你版
OpenAI Deep Research (o → OpenAI 深度研究（o
deep-research- → 深度检索
pro) → pro)
Perplexity Deep Research (gemini- → Perplexity Deep Research（Gemini-）
sonar- → sonar-
LitQA → LitQA
FullText deep-research) → 全文深度检索
React (claude- → React (claude-
haiku) → 俳句
React (claude-sonnet- → React (claude-sonnet-)
React (gpt- → React (gpt-
React (gemini- → React（Gemini-
React (llama- → React (llama-
React (o → React（或
STORM (gpt- → STORM (gpt-
turbo → 涡轮
gpt- → gpt-
Smolagents (claude- → 小型智能体（claude-
Score → 评分标准
```

小型智能体（claude-sonnet-4）0.4 小型智能体（gpt-4o） 小型智能体（gpt-5） 小型智能体（gemini-2.5-flash） Elicit（无费用）0.2 SciSpace（无费用）You.com研究API（无费用）

0.0 10 2 10 1 成本（美元）

图4：文献理解问答测试集的得分与成本分析（表13）。点值表示均值；误差条表示95%置信区间。帕累托前沿上的点通过虚线连接，代表每个评估任务下的最优质量-成本权衡（ScholarQA-CS2、LitQA2-FullText）。注意：x轴（成本）采用对数刻度。†表示未固定版本日期的模型。

[原文第 24 页的完整图表与公式](assets/original-page-024.jpg)

作为会议论文发表在 ICLR 2026 上

表12：文献理解搜索基准测试结果。†表示未锁定具体版本日期的模型。

**表格与文字对照**

```text
O T Agent Model PaperFindingBench LitQA2-FullText-Search
Score Cost Score Cost
∼ ✓ ReAct claude-3-5-haiku 10.7 ± 2.6 0.061 ± 0.005 60.0 ± 11.2 0.069 ± 0.007
∼ ✓ ReAct claude-sonnet-4 20.3 ± 3.2 0.541 ± 0.025 46.7 ± 11.4 0.606 ± 0.031
∼ ✓ ReAct gpt-4.1 16.5 ± 3.2 0.867 ± 0.183 65.3 ± 10.8 0.819 ± 0.258
∼ ✓ ReAct gpt-4o 12.9 ± 3.3 0.267 ± 0.032 66.7 ± 10.7 0.328 ± 0.081
∼ ✓ ReAct gpt-5-mini 22.0 ± 3.7 0.060 ± 0.009 56.0 ± 11.3 0.118 ± 0.026
∼ ✓ ReAct gpt-5 26.4 ± 3.9 0.428 ± 0.048 82.7 ± 8.6 0.389 ± 0.055
∼ ✓ ReAct gemini-2.5-flash 6.5 ± 2.3 1.196 ± 0.214 57.3 ± 11.3 0.650 ± 0.400
✓ ✓ ReAct llama-4-scout 5.4 ± 2.2 2.816 ± 0.319 37.3 ± 11.0 4.326 ± 0.795
∼ ✓ ReAct o3 19.3 ± 3.7 0.518 ± 0.067 57.3 ± 11.3 0.790 ± 0.127
∼ ∼ Smolagents claude-3-5-haiku 4.6 ± 2.1 0.070 ± 0.011 2.7 ± 3.7 0.096 ± 0.060
Coder
∼ ∼ Smolagents claude-sonnet-4 22.1 ± 3.5 0.975 ± 0.139 52.0 ± 11.4 1.100 ± 0.097
Coder
∼ ∼ Smolagents gpt-4.1 16.5 ± 3.5 0.080 ± 0.007 50.7 ± 11.4 0.095 ± 0.037
Coder
∼ ∼ Smolagents gpt-4o 12.5 ± 3.5 0.098 ± 0.010 20.0 ± 9.1 0.105 ± 0.023
Coder
∼ ∼ Smolagents gpt-5-mini 17.2 ± 3.2 0.034 ± 0.012 48.0 ± 11.4 0.036 ± 0.010
Coder
∼ ∼ Smolagents gpt-5 20.0 ± 3.9 0.121 ± 0.012 54.7 ± 11.3 0.152 ± 0.029
Coder
∼ ∼ Smolagents gemini-2.5-flash 14.7 ± 3.4 0.044 ± 0.006 36.0 ± 10.9 0.089 ± 0.100
Coder
✓ ∼ Smolagents llama-4-scout 7.0 ± 2.9 0.013 ± 0.003 6.7 ± 5.7 0.010 ± 0.001
Coder
∼ × Asta v0 mixture 37.6 ± 3.1 0.063 ± 0.005 90.7 ± 6.6 0.112 ± 0.007
∼ ∼ Asta Paper gemini-2-flash, 39.7 ± 3.1 0.063 ± 0.005 90.7 ± 6.6 0.112 ± 0.007
Finder gpt-4o
A × You.com ? 7.2 ± 2.0 ? 36.0 ± 10.9 ?

表内文字对照（数值与原始行列保持不变）：
O T Agent Model PaperFindingBench LitQA → O T 智能体模型论文 研究发现 基准文献 QA
FullText-Search → 全文搜索
Score Cost Score Cost → 得分 成本 得分 成本
ReAct claude- → ReAct claude-
haiku → 俳句
ReAct claude-sonnet- → ReAct claude-sonnet-
ReAct gpt- → ReAct gpt-
mini → 迷你
ReAct gemini- → ReAct Gemini
flash → 闪存
ReAct llama- → ReAct llama-
scout → scout
ReAct o → ReAct 模式
Smolagents claude- → 小型智能体 Claude-
Coder → 编码员
Smolagents claude-sonnet- → 小型智能体 Claude-Sonnet-
Smolagents gpt- → 小型智能体 GPT-
Smolagents gemini- → 小型智能体 Gemini-
Smolagents llama- → 小型智能体 llama-
Asta v → Asta v
mixture → 混合
Asta Paper gemini- → Asta Paper gemini-
Finder gpt- → 查找器 GPT-
You → 你
com → com
```

搜索 API

ArxivDIGESTables-Clean 效率前沿智能体（gpt-5-mini）React（gpt-5-mini）0.4 Asta 表格合成（gpt-5-mini）Asta v0（混合模型）Asta 表格合成（claude-3-5-haiku）0.3 Asta 表格合成（claude-sonnet-4）Asta 表格合成（gemini-2.5-flash）Asta 表格合成（gemini-2.5-pro）得分

**表格与文字对照**

```text
Asta Table Synthesis (gpt-4.1)
0.2 Asta Table Synthesis (gpt-5 )
Asta Table Synthesis (llama-4-scout)
Asta Table Synthesis (o3)
React (claude-3-5-haiku)
0.1 React (claude-sonnet-4)
React (gpt-4.1)
React (gpt-4o)
React (gpt-5)
React (gemini-2.5-flash)
0.0 React (llama-4-scout)
10 3 10 2 10 1 100 React (o3)
Cost (USD) Smolagents (claude-3-5-haiku)
Smolagents (claude-sonnet-4)
Smolagents (gpt-4.1)
Smolagents (gpt-4o)
Smolagents (gpt-5)
Smolagents (gemini-2.5-flash)
Smolagents (llama-4-scout)

表内文字对照（数值与原始行列保持不变）：
Asta Table Synthesis (gpt- → Asta Table 合成（gpt-
Asta Table Synthesis (llama- → Asta 表格合成（llama-
scout) → scout)
Asta Table Synthesis (o → Asta 表格合成（o
React (claude- → React (claude-
haiku) → 俳句
React (claude-sonnet- → React (claude-sonnet-)
React (gpt- → React (gpt-
React (gemini- → React（Gemini-
flash) → 闪存）
React (llama- → React (llama-
React (o → React（或
Cost (USD) Smolagents (claude- → 成本（美元） 智能体数量（claude-
Smolagents (claude-sonnet- → 小型智能体（claude-sonnet-
Smolagents (gpt- → 小型智能体（GPT-）
Smolagents (gemini- → 小型智能体（Gemini-
Smolagents (llama- → 小型智能体（llama-
```

图5：文献理解ArxivDIGESTables-Clean基准测试的得分与成本分析（表14）。点值表示均值；误差条表示95%置信区间。帕累托前沿上的点用虚线连接，代表每个评估结果下的最优质量-成本权衡。注意：x轴（成本）采用对数刻度。†表示未固定到特定版本模型的模型。

[原文第 25 页的完整图表与公式](assets/original-page-025.jpg)

作为会议论文发表在 ICLR 2026 上

表13：文献理解问答基准测试结果。没有API的智能体无法在LitQA2-FT上进行评估。括号中的模型表示自报模型。†表示未锁定到特定版本时间的模型。

**表格与文字对照**

```text
O T Agent Model ScholarQA-CS2 LitQA2-FullText
Score Cost Score Cost
∼ ✓ ReAct claude-3-5-haiku 66.3 ± 2.8 0.019 ± 0.001 32.0 ± 10.6 0.022 ± 0.004
∼ ✓ ReAct claude-sonnet-4 78.3 ± 2.2 0.390 ± 0.019 68.0 ± 10.6 0.238 ± 0.026
∼ ✓ ReAct gpt-4.1 70.1 ± 3.2 0.733 ± 0.243 77.3 ± 9.5 0.222 ± 0.097
∼ ✓ ReAct gpt-4o 53.3 ± 3.4 0.101 ± 0.012 22.7 ± 9.5 0.046 ± 0.015
∼ ✓ ReAct gpt-5-mini 26.7 ± 7.4 0.027 ± 0.004 74.7 ± 9.9 0.075 ± 0.029
∼ ✓ ReAct gpt-5 79.8 ± 3.5 0.373 ± 0.034 82.7 ± 8.6 0.276 ± 0.114
∼ ✓ ReAct gemini-2.5-flash 52.8 ± 8.0 0.063 ± 0.026 36.0 ± 10.9 0.436 ± 0.140
✓ ✓ ReAct llama-4-scout 24.8 ± 5.1 0.588 ± 0.144 41.3 ± 11.2 0.170 ± 0.104
∼ ✓ ReAct o3 66.4 ± 3.0 0.275 ± 0.039 80.0 ± 9.1 0.347 ± 0.083
∼ ∼ Smolagents Coder claude-3-5-haiku 49.9 ± 4.4 0.042 ± 0.004 25.3 ± 9.9 0.056 ± 0.010
∼ ∼ Smolagents Coder claude-sonnet-4 72.4 ± 2.1 0.794 ± 0.052 50.7 ± 11.4 0.627 ± 0.066
∼ ∼ Smolagents Coder gpt-4.1 73.7 ± 2.1 0.080 ± 0.016 65.3 ± 10.8 0.035 ± 0.005
∼ ∼ Smolagents Coder gpt-4o 46.3 ± 4.0 0.078 ± 0.008 14.7 ± 8.1 0.050 ± 0.010
∼ ∼ Smolagents Coder gpt-5-mini 57.3 ± 5.3 0.020 ± 0.002 50.7 ± 11.4 0.015 ± 0.005
∼ ∼ Smolagents Coder gpt-5 68.4 ± 4.4 0.154 ± 0.014 73.3 ± 10.1 0.101 ± 0.026
∼ ∼ Smolagents Coder gemini-2.5-flash 63.7 ± 4.6 0.080 ± 0.044 41.3 ± 11.2 0.034 ± 0.006
✓ ∼ Smolagents Coder llama-4-scout 39.6 ± 4.8 0.008 ± 0.001 42.7 ± 11.3 0.013 ± 0.002
∼ × Asta v0 mixture 87.7 ± 1.4 1.529 ± 0.291 70.7 ± 10.4 0.306 ± 0.093
∼ ∼ Asta Scholar QA (w/ o3 88.7 ± 1.2 2.932 ± 0.408 – –
Tables)
∼ ∼ Asta Scholar QA (w/ claude-sonnet-4 87.9 ± 1.2 1.314 ± 0.281 – –
Tables)
∼ ∼ Asta Scholar QA claude-sonnet-4 86.2 ± 1.4 0.393 ± 0.030 – –
∼ ∼ Asta Scholar QA gemini-2.5- 87.7 ± 1.4 0.126 ± 0.010 – –
flash†
∼ ∼ Asta Scholar QA gpt-4o-mini 78.5 ± 1.9 0.012 ± 0.001 – –
∼ ∼ Asta Scholar QA gpt-5† 85.9 ± 1.6 1.099 ± 0.074 – –
× × Elicit – 85.5 ± 1.6 – – –
A × Perplexity Sonar Deep gemini-2.5-flash, 67.3 ± 1.2 0.416 ± 0.019 73.3 ± 10.1 0.219 ± 0.016
Research sonar-deepresearch
A × You.com Research API – 55.0 ± 2.2 – 8.0 ± 6.2 –
× × SciSpace Deep Review claude-sonnet-4 84.6 ± 1.3 – – –
✓ ∼ OpenSciLM llama-3.1- 58.0 ± 2.6 0.004 ± 0.000 – –
openscholar-8b
A × OpenAI Deep Research o3-/o4-mini- 79.4 ± 1.4 1.803 ± 0.039 – –
deep-research,
gemini-2.5-pro
A × FutureHouse Crow gpt-4.1-mini, 81.1 ± 1.7 0.107 ± 0.004 72.0 ± 10.2 0.065 ± 0.003
o3-mini,
gemini-2.5-flash
A × FutureHouse Falcon gpt-4.1-mini, 77.6 ± 1.3 0.403 ± 0.051 74.7 ± 9.9 0.220 ± 0.011
gemini-2.5-flash,
o3-mini
∼ × STORM gpt-3.5-turbo, 78.3 ± 2.4 0.094 ± 0.002 – –
gpt-4o

表内文字对照（数值与原始行列保持不变）：
O T Agent Model ScholarQA-CS → O T 智能体模型 ScholarQA-CS
LitQA → LitQA
FullText → 全文
Score Cost Score Cost → 得分 成本 得分 成本
ReAct claude- → ReAct claude-
haiku → 俳句
ReAct claude-sonnet- → ReAct claude-sonnet-
ReAct gpt- → ReAct gpt-
mini → 迷你
ReAct gemini- → ReAct Gemini
flash → 闪存
ReAct llama- → ReAct llama-
scout → scout
ReAct o → ReAct 模式
Smolagents Coder claude- → 小型智能体 编码师 claude-
Smolagents Coder claude-sonnet- → 小型智能体 编码师 claude-sonnet-
Smolagents Coder gpt- → 小型智能体 编码师 GPT-
Smolagents Coder gemini- → 小型智能体 编码神器 Gemini-
Smolagents Coder llama- → 小型智能体 编码智能体 llama-
Asta v → Asta v
mixture → 混合
Asta Scholar QA (w/ o → Asta Scholar QA（含不含）
Tables) → 表格）
Asta Scholar QA (w/ claude-sonnet- → Asta Scholar QA（含 claude-sonnet-
Asta Scholar QA claude-sonnet- → Asta Scholar QA claude-sonnet-
Asta Scholar QA gemini- → Asta Scholar QA  gemsini-
Asta Scholar QA gpt- → Asta Scholar QA 大语言模型
o-mini → o-mini
Elicit → 激发
Perplexity Sonar Deep gemini- → Perplexity Sonar Deep gemini-
Research sonar-deepresearch → 研究声纳-深度研究
You → 你
com Research API → com Research API
SciSpace Deep Review claude-sonnet- → SciSpace 深度评审 claude-sonnet-
OpenSciLM llama- → OpenSciLM llama-
openscholar- → 开放学者
OpenAI Deep Research o → OpenAI 深度研究 o
mini- → 迷你-
deep-research → 深度检索
gemini- → Gemini-
pro → pro
FutureHouse Crow gpt- → FutureHouse Crow 大语言模型
FutureHouse Falcon gpt- → FutureHouse Falcon gpt-
STORM gpt- → STORM gpt-
turbo → 涡轮
gpt- → gpt-
```

[原文第 26 页的完整图表与公式](assets/original-page-026.jpg)

作为会议论文发表在 ICLR 2026 上

表14：文献理解 ArxivDIGESTables-Clean 任务基准测试结果。

**表格与文字对照**

```text
O T Agent Model ArxivDIGESTables-Clean
Score Cost
∼ ✓ ReAct claude-3-5-haiku 21.7 ± 2.6 0.013 ± 0.001
∼ ✓ ReAct claude-sonnet-4 25.5 ± 3.1 0.069 ± 0.005
∼ ✓ ReAct gpt-4.1 27.5 ± 3.2 0.038 ± 0.004
∼ ✓ ReAct gpt-4o 16.3 ± 2.4 0.055 ± 0.005
∼ ✓ ReAct gpt-5-mini 32.1 ± 3.3 0.013 ± 0.001
∼ ✓ ReAct gpt-5 29.4 ± 3.7 0.064 ± 0.005
∼ ✓ ReAct gemini-2.5-flash 25.2 ± 3.1 0.022 ± 0.002
✓ ✓ ReAct llama-4-scout 9.5 ± 2.3 0.760 ± 0.102
∼ ✓ ReAct o3 32.9 ± 3.3 0.050 ± 0.004
∼ ∼ Smolagents Coder claude-3-5-haiku 15.0 ± 2.8 0.017 ± 0.003
∼ ∼ Smolagents Coder claude-sonnet-4 24.8 ± 2.9 0.204 ± 0.018
∼ ∼ Smolagents Coder gpt-4.1 27.2 ± 3.1 0.044 ± 0.005
∼ ∼ Smolagents Coder gpt-4o 14.6 ± 2.5 0.051 ± 0.007
∼ ∼ Smolagents Coder gpt-5-mini 30.0 ± 3.2 0.009 ± 0.001
∼ ∼ Smolagents Coder gpt-5 31.5 ± 3.2 0.060 ± 0.004
∼ ∼ Smolagents Coder gemini-2.5-flash 25.2 ± 2.8 0.021 ± 0.002
✓ ∼ Smolagents Coder llama-4-scout 8.7 ± 2.2 0.099 ± 0.087
∼ × Asta v0 mixture 42.9 ± 3.7 0.517 ± 0.056
∼ ∼ Asta Table Synthesis gpt-4.1 38.8 ± 3.5 0.347 ± 0.038
∼ ∼ Asta Table Synthesis claude-3-5-haiku 31.1 ± 3.6 0.165 ± 0.018
∼ ∼ Asta Table Synthesis claude-sonnet-4 37.2 ± 3.3 0.676 ± 0.074
∼ ∼ Asta Table Synthesis gemini-2.5-flash 34.4 ± 3.3 0.133 ± 0.015
∼ ∼ Asta Table Synthesis o3 41.6 ± 3.5 0.517 ± 0.056
∼ ∼ Asta Table Synthesis gemini-2.5-pro 35.4 ± 3.5 0.993 ± 0.158
✓ ∼ Asta Table Synthesis llama-4-scout 26.4 ± 3.3 0.025 ± 0.003
∼ ∼ Asta Table Synthesis gpt-5† 42.6 ± 3.5 1.281 ± 0.140
∼ ∼ Asta Table Synthesis gpt-5-mini† 41.7 ± 3.7 0.172 ± 0.019

表内文字对照（数值与原始行列保持不变）：
O T Agent Model ArxivDIGESTables-Clean → O T 智能体模型 ArxivDIGESTables-Clean
Score Cost → 评分成本
ReAct claude- → ReAct claude-
haiku → 俳句
ReAct claude-sonnet- → ReAct claude-sonnet-
ReAct gpt- → ReAct gpt-
mini → 迷你
ReAct gemini- → ReAct Gemini
flash → 闪存
ReAct llama- → ReAct llama-
scout → scout
ReAct o → ReAct 模式
Smolagents Coder claude- → 小型智能体 编码师 claude-
Smolagents Coder claude-sonnet- → 小型智能体 编码师 claude-sonnet-
Smolagents Coder gpt- → 小型智能体 编码师 GPT-
Smolagents Coder gemini- → 小型智能体 编码神器 Gemini-
Smolagents Coder llama- → 小型智能体 编码智能体 llama-
Asta v → Asta v
mixture → 混合
Asta Table Synthesis gpt- → Asta Table Synthesis gpt-
Asta Table Synthesis claude- → Asta 表格合成 claude-
Asta Table Synthesis claude-sonnet- → Asta Table Synthesis claude-sonnet-
Asta Table Synthesis gemini- → Asta Table Synthesis 模型：gemini-
Asta Table Synthesis o → Asta 表格合成 o
pro → pro
Asta Table Synthesis llama- → Asta Table Synthesis llama-
```

[原文第 27 页的完整图表与公式](assets/original-page-027.jpg)

作为会议论文发表在 ICLR 2026 上

表15：代码与执行类别结果。

**表格与文字对照**

```text
O T Agent Model SUPER-Expert CORE-Bench-Hard− DS-1000
Score Cost Score Cost Score Cost
∼ ✓ ReAct claude-3-5- 13.1 ± 8.3 0.077 ± 0.017 0.0000 0.077 ± 0.021 54.1 ± 3.3 0.006 ± 0.0002
haiku
∼ ✓ ReAct claude- 22.6 ± 11.1 0.448 ± 0.087 40.5 ± 16.0 0.499 ± 0.081 75.6 ± 2.8 0.044 ± 0.0020
sonnet-4
∼ ✓ ReAct gpt-4.1 11.2 ± 7.5 0.156 ± 0.069 18.9 ± 12.8 0.119 ± 0.035 67.0 ± 3.1 0.008 ± 0.0003
∼ ✓ ReAct gpt-4o 5.9 ± 6.7 0.319 ± 0.069 5.4 ± 7.4 0.124 ± 0.041 43.7 ± 3.2 0.010 ± 0.0006
∼ ✓ ReAct gpt-5-mini 34.6 ± 13.2 0.105 ± 0.046 45.9 ± 16.3 0.047 ± 0.014 71.0 ± 3.0 0.003 ± 0.0001
∼ ✓ ReAct gpt-5 41.1 ± 12.9 0.589 ± 0.140 45.9 ± 16.3 0.443 ± 0.139 78.0 ± 2.7 0.021 ± 0.0009
∼ ✓ ReAct gemini-2.5- 20.0 ± 10.7 0.875 ± 0.295 2.7 ± 5.3 0.470 ± 0.214 55.4 ± 3.2 0.019 ± 0.0032
flash
✓ ✓ ReAct llama-4- 4.7 ± 5.2 0.175 ± 0.066 0.0000 0.027 ± 0.018 9.7 ± 1.9 0.110 ± 0.0077
scout
∼ ✓ ReAct o3 16.3 ± 9.6 0.369 ± 0.097 56.8 ± 16.2 0.196 ± 0.076 74.9 ± 2.8 0.010 ± 0.0007
∼ ∼ Smolagents claude-3-5- 16.8 ± 9.6 0.812 ± 0.581 0.0000 0.332 ± 0.210 9.9 ± 2.0 0.024 ± 0.0103
Coder haiku
∼ ∼ Smolagents claude- 11.7 ± 8.0 3.559 ± 1.766 32.4 ± 15.3 2.199 ± 0.780 74.7 ± 2.8 0.114 ± 0.0079
Coder sonnet-4
∼ ∼ Smolagents gpt-4.1 7.0 ± 6.9 0.149 ± 0.166 21.6 ± 13.4 0.098 ± 0.031 48.0 ± 3.3 0.073 ± 0.0230
Coder
∼ ∼ Smolagents gpt-4o 3.9 ± 4.9 1.351 ± 0.715 5.4 ± 7.4 0.419 ± 0.410 16.8 ± 2.4 0.137 ± 0.0642
Coder
∼ ∼ Smolagents gpt-5-mini 14.2 ± 8.9 0.240 ± 0.207 5.4 ± 7.4 0.014 ± 0.004 65.2 ± 3.1 0.016 ± 0.0046
Coder
∼ ∼ Smolagents gpt-5 3.6 ± 4.8 0.079 ± 0.023 13.5 ± 11.2 0.190 ± 0.106 75.7 ± 2.8 0.019 ± 0.0007
Coder
∼ ∼ Smolagents gemini-2.5- 7.5 ± 6.0 0.796 ± 0.945 13.5 ± 11.2 0.832 ± 0.710 28.9 ± 3.0 0.044 ± 0.0127
Coder flash
✓ ∼ Smolagents llama-4- 8.1 ± 7.0 0.323 ± 0.377 0.0000 0.046 ± 0.034 2.7 ± 1.1 0.004 ± 0.0020
Coder scout
∼ × Asta v0 mixture 19.4 ± 10.4 0.332 ± 0.057 48.6 ± 16.3 0.226 ± 0.093 74.8 ± 2.8 0.011 ± 0.0007
∼ ∼ Asta Code gpt-4.1 16.3 ± 9.4 0.285 ± 0.059 – – – –
∼ ∼ Asta Code gpt-4o 5.6 ± 6.4 0.464 ± 0.113 – – – –
∼ ∼ Asta Code gpt-5 13.5 ± 9.4 0.372 ± 0.072 – – – –
∼ ∼ Asta Code gpt-5-mini 12.8 ± 9.1 0.067 ± 0.014 – – – –

表内文字对照（数值与原始行列保持不变）：
O T Agent Model SUPER-Expert CORE-Bench-Hard → O T 智能体模型 超级专家核心测试平台
DS- → DS-
Score Cost Score Cost Score Cost → 得分 成本 得分 成本 得分 成本
ReAct claude- → ReAct claude-
haiku → 俳句
sonnet- → 十四行诗
ReAct gpt- → ReAct gpt-
mini → 迷你
ReAct gemini- → ReAct Gemini
flash → 闪存
ReAct llama- → ReAct llama-
scout → scout
ReAct o → ReAct 模式
Smolagents claude- → 小型智能体 Claude-
Coder haiku → 编码俳句
Coder sonnet- → 编码十四行诗
Smolagents gpt- → 小型智能体 GPT-
Coder → 编码员
Smolagents gemini- → 小型智能体 Gemini-
Coder flash → 编码员快闪
Smolagents llama- → 小型智能体 llama-
Coder scout → 编码 scout
Asta v → Asta v
mixture → 混合
Asta Code gpt- → Asta Code gpt-
```

[原文第 28 页的完整图表与公式](assets/original-page-028.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
SUPER-Expert Efficiency Frontier
Asta Code (gpt-5-mini)
0.5 React (gpt-5)
React (gpt-5-mini)
0.4 React (o3)
Smolagents (gpt-5-mini)
0.3
Score

表内文字对照（数值与原始行列保持不变）：
SUPER-Expert Efficiency Frontier → 超级专家效率前沿
Asta Code (gpt- → Asta Code (gpt-
mini) → 迷你版
React (gpt- → React (gpt-
React (o → React（或
Smolagents (gpt- → 小型智能体（GPT-）
Score → 评分标准
```

**表格与文字对照**

```text
Asta Code (gpt-4.1)
Asta Code (gpt-4o)
0.2 Asta Code (gpt-5)
Asta v0 (mixture)
React (claude-3-5-haiku)
0.1 React (claude-sonnet-4)
React (gpt-4.1)
0.0 React (gpt-4o)
10 2 10 1 100 React (gemini-2.5-flash)
React (llama-4-scout)
CORE-Bench-Hard Smolagents (claude-3-5-haiku)
Smolagents (claude-sonnet-4)
0.7 Smolagents (gpt-4.1)
Smolagents (gpt-4o)
0.6 Smolagents (gpt-5)
Smolagents (gemini-2.5-flash)
0.5 Smolagents (llama-4-scout)
Score

表内文字对照（数值与原始行列保持不变）：
Asta Code (gpt- → Asta Code (gpt-
Asta v → Asta v
mixture) → 混合）
React (claude- → React (claude-
haiku) → 俳句
React (claude-sonnet- → React (claude-sonnet-)
React (gpt- → React (gpt-
React (gemini- → React（Gemini-
flash) → 闪存）
React (llama- → React (llama-
scout) → scout)
CORE-Bench-Hard Smolagents (claude- → CORE-Bench-Hard 大型智能体（claude-
Smolagents (claude-sonnet- → 小型智能体（claude-sonnet-
Smolagents (gpt- → 小型智能体（GPT-）
Smolagents (gemini- → 小型智能体（Gemini-
Smolagents (llama- → 小型智能体（llama-
Score → 评分标准
```

0.4 0.3 0.2 0.1 0.0 10 2 10 1 100 DS-1000 0.8

### 0.6 分

0.4

0.2

0.0 10 3 10 2 10 1 成本（美元）

图6：Code & Execution基准测试的得分与成本分析（表15）。点值表示均值；误差条表示95%置信区间。帕累托前沿上的点用虚线连接，代表每个评估项目的最优质量-成本权衡（CORE-Bench-Hard−、SUPER-Expert、DS-1000）。注意：x轴（成本）采用对数刻度。†表示未固定到特定版本时间的模型。

[原文第 29 页的完整图表与公式](assets/original-page-029.jpg)

作为会议论文发表在 ICLR 2026 上

表16：数据分析发现平台结果。

**表格与文字对照**

```text
O T Agent Model DiscoveryBench
Score Cost
∼ ✓ ReAct claude-3-5-haiku 24.3 ± 4.7 0.012 ± 0.001
∼ ✓ ReAct claude-sonnet-4 23.2 ± 4.1 0.132 ± 0.009
∼ ✓ ReAct gpt-4.1 30.5 ± 5.1 0.025 ± 0.003
∼ ✓ ReAct gpt-4o 13.2 ± 3.7 0.040 ± 0.010
∼ ✓ ReAct gpt-5-mini 26.9 ± 4.8 0.011 ± 0.001
∼ ✓ ReAct gpt-5 30.5 ± 4.8 0.092 ± 0.009
∼ ✓ ReAct gemini-2.5-flash 1.9 ± 1.7 0.101 ± 0.007
✓ ✓ ReAct llama-4-scout 5.9 ± 2.6 0.192 ± 0.021
∼ ✓ ReAct o3 33.7 ± 5.1 0.039 ± 0.004
∼ ∼ Smolagents Coder claude-3-5-haiku 16.5 ± 4.1 0.024 ± 0.007
∼ ∼ Smolagents Coder claude-sonnet-4 28.8 ± 4.8 0.237 ± 0.019
∼ ∼ Smolagents Coder gpt-4.1 28.4 ± 4.9 0.045 ± 0.018
∼ ∼ Smolagents Coder gpt-4o 17.8 ± 4.2 0.054 ± 0.004
∼ ∼ Smolagents Coder gpt-5-mini 27.7 ± 4.9 0.071 ± 0.041
∼ ∼ Smolagents Coder gpt-5 26.7 ± 4.7 0.077 ± 0.006
∼ ∼ Smolagents Coder gemini-2.5-flash 24.7 ± 4.7 0.017 ± 0.007
✓ ∼ Smolagents Coder llama-4-scout 20.2 ± 4.5 0.008 ± 0.002
∼ × Asta v0 mixture 33.2 ± 5.1 0.246 ± 0.071
∼ ∼ Asta DataVoyager gpt-4.1† , gpt-4o† 29.9 ± 5.0 0.147 ± 0.020
∼ ∼ Asta DataVoyager claude-sonnet-4, 25.7 ± 4.6 0.523 ± 0.050
gpt-4o†
∼ ∼ Asta DataVoyager o3† , gpt-4o† 31.1 ± 5.0 0.234 ± 0.061
∼ ∼ Asta DataVoyager gpt-5† :effort=minimal, 27.0 ± 4.7 0.215 ± 0.029
gpt-4o†
∼ ∼ Asta DataVoyager gpt-5† , gpt-4o† 29.6 ± 4.9 0.354 ± 0.075

表内文字对照（数值与原始行列保持不变）：
O T Agent Model DiscoveryBench → O T 智能体模型发现基准测试
Score Cost → 评分成本
ReAct claude- → ReAct claude-
haiku → 俳句
ReAct claude-sonnet- → ReAct claude-sonnet-
ReAct gpt- → ReAct gpt-
mini → 迷你
ReAct gemini- → ReAct Gemini
flash → 闪存
ReAct llama- → ReAct llama-
scout → scout
ReAct o → ReAct 模式
Smolagents Coder claude- → 小型智能体 编码师 claude-
Smolagents Coder claude-sonnet- → 小型智能体 编码师 claude-sonnet-
Smolagents Coder gpt- → 小型智能体 编码师 GPT-
Smolagents Coder gemini- → 小型智能体 编码神器 Gemini-
Smolagents Coder llama- → 小型智能体 编码智能体 llama-
Asta v → Asta v
mixture → 混合
Asta DataVoyager gpt- → Asta DataVoyager gpt-
gpt- → gpt-
Asta DataVoyager claude-sonnet- → Asta DataVoyager claude-sonnet-
Asta DataVoyager o → Asta DataVoyager o
effort → 努力
minimal → 最小的
```

**表格与文字对照**

```text
DiscoveryBench
0.40 Efficiency Frontier
Smolagents (llama-4-scout)
0.35 React (gpt-5-mini)
React (gpt-4.1)
React (o3)
0.30
Asta DataVoyager (claude-sonnet-4, gpt-4o )
0.25 Asta DataVoyager (gpt-4.1 , gpt-4o )
Asta DataVoyager (gpt-5 , gpt-4o )
Asta DataVoyager (gpt-5 :effort=minimal, gpt-4o )
Score

表内文字对照（数值与原始行列保持不变）：
DiscoveryBench → DiscoveryBench
Efficiency Frontier → 效率前沿
Smolagents (llama- → 小型智能体（llama-
scout) → scout)
React (gpt- → React (gpt-
mini) → 迷你版
React (o → React（或
Asta DataVoyager (claude-sonnet- → Asta DataVoyager (claude-sonnet-)
gpt- → gpt-
o ) → o )
Asta DataVoyager (gpt- → Asta DataVoyager (gpt-
effort → 努力
minimal → 最小的
Score → 评分标准
```

**表格与文字对照**

```text
0.20 Asta DataVoyager (o3 , gpt-4o )
Asta v0 (mixture)
0.15 React (claude-3-5-haiku)
React (claude-sonnet-4)
React (gpt-4o)
0.10 React (gpt-5)
React (gemini-2.5-flash)
0.05 React (llama-4-scout)
Smolagents (claude-3-5-haiku)
Smolagents (claude-sonnet-4)
0.00 Smolagents (gpt-4.1)
10 3 10 2 10 1 Smolagents (gpt-4o)
Cost (USD) Smolagents (gpt-5)
Smolagents (gpt-5-mini)
Smolagents (gemini-2.5-flash)

表内文字对照（数值与原始行列保持不变）：
Asta DataVoyager (o → Asta DataVoyager（或
gpt- → gpt-
o ) → o )
Asta v → Asta v
mixture) → 混合）
React (claude- → React (claude-
haiku) → 俳句
React (claude-sonnet- → React (claude-sonnet-)
React (gpt- → React (gpt-
React (gemini- → React（Gemini-
flash) → 闪存）
React (llama- → React (llama-
scout) → scout)
Smolagents (claude- → 小型智能体（claude-
Smolagents (claude-sonnet- → 小型智能体（claude-sonnet-
Smolagents (gpt- → 小型智能体（GPT-）
Cost (USD) Smolagents (gpt- → 成本（美元） 智能体数量（gpt-
mini) → 迷你版
Smolagents (gemini- → 小型智能体（Gemini-
```

图7：数据分析子基准的得分与成本分析。点值表示均值；误差条表示95%置信区间。帕累托前沿上的点用红色三角形标记，代表每个评估项目的最佳质量-成本权衡（DiscoveryBench）。†表示未锁定特定版本时间的模型。

[原文第 30 页的完整图表与公式](assets/original-page-030.jpg)

作为会议论文发表在 ICLR 2026 上

表17：端到端发现类别结果。

**表格与文字对照**

```text
O T Agent Model E2E-Bench E2E-Bench-Hard
Score Cost Score Cost
∼ ✓ ReAct claude-3-5- 4.5 ± 2.8 0.042 ± 0.011 4.8 ± 3.4 0.048 ± 0.011
haiku
∼ ✓ ReAct claude- 52.5 ± 6.8 0.749 ± 0.072 38.9 ± 6.9 0.836 ± 0.057
sonnet-4
∼ ✓ ReAct gpt-4.1 19.3 ± 7.3 0.132 ± 0.024 14.8 ± 6.8 0.139 ± 0.034
∼ ✓ ReAct gpt-4o 1.6 ± 1.7 0.157 ± 0.035 1.4 ± 1.9 0.135 ± 0.028
∼ ✓ ReAct gpt-5-mini 9.5 ± 7.6 0.030 ± 0.006 15.7 ± 8.3 0.040 ± 0.008
∼ ✓ ReAct gpt-5 30.0 ± 11.9 0.403 ± 0.053 42.1 ± 11.4 0.584 ± 0.072
∼ ✓ ReAct gemini-2.5- 0.0000 2.401 ± 1.149 1.1 ± 2.1 1.263 ± 0.672
flash
✓ ✓ ReAct llama-4- 1.9 ± 2.1 0.818 ± 0.135 0.9 ± 1.1 0.813 ± 0.144
scout
∼ ✓ ReAct o3 34.9 ± 10.1 0.065 ± 0.010 21.0 ± 7.6 0.075 ± 0.019
∼ ∼ Smolagents claude-3-5- 5.3 ± 3.1 0.946 ± 0.560 3.7 ± 2.4 0.505 ± 0.538
Coder haiku
∼ ∼ Smolagents claude- 47.2 ± 6.1 0.873 ± 0.110 35.8 ± 7.8 1.512 ± 0.307
Coder sonnet-4
∼ ∼ Smolagents gpt-4.1 36.6 ± 9.3 0.178 ± 0.146 30.0 ± 7.7 1.955 ± 1.773
Coder
∼ ∼ Smolagents gpt-4o 5.4 ± 3.9 0.473 ± 0.347 5.1 ± 3.3 0.866 ± 0.757
Coder
∼ ∼ Smolagents gpt-5-mini 22.3 ± 9.6 0.076 ± 0.114 21.6 ± 7.5 0.076 ± 0.108
Coder
∼ ∼ Smolagents gpt-5 62.8 ± 9.8 0.205 ± 0.025 30.3 ± 10.5 0.232 ± 0.043
Coder
∼ ∼ Smolagents gemini-2.5- 34.0 ± 10.2 1.877 ± 0.830 23.2 ± 7.8 2.541 ± 1.203
Coder flash
✓ ∼ Smolagents llama-4- 0.2 ± 0.3 0.283 ± 0.152 0.7 ± 0.7 0.251 ± 0.181
Coder scout
∼ × Asta v0 mixture 70.4 ± 6.3 10.643 ± 0.717 67.3 ± 5.3 14.487 ± 1.050
†
∼ ✓ Faker gpt-4.1 39.2 ± 6.9 0.026 ± 0.001 25.4 ± 4.5 0.029 ± 0.001
∼ × Asta Panda gpt-4.1† 36.6 ± 7.7 7.610 ± 1.650 39.3 ± 7.0 9.319 ± 1.243
∼ × Asta Panda claude- 70.5 ± 6.2 10.643 ± 0.717 68.2 ± 4.4 14.487 ± 1.050
sonnet-4
∼ × Asta claude-3-7- 65.3 ± 7.1 2.760 ± 0.510 64.5 ± 5.5 3.549 ± 0.692
CodeScientist sonnet

表内文字对照（数值与原始行列保持不变）：
O T Agent Model E → O T 智能体模型 E
E-Bench E → E-Bench E
E-Bench-Hard → E-Bench-Hard
Score Cost Score Cost → 得分 成本 得分 成本
ReAct claude- → ReAct claude-
haiku → 俳句
sonnet- → 十四行诗
ReAct gpt- → ReAct gpt-
mini → 迷你
ReAct gemini- → ReAct Gemini
flash → 闪存
ReAct llama- → ReAct llama-
scout → scout
ReAct o → ReAct 模式
Smolagents claude- → 小型智能体 Claude-
Coder haiku → 编码俳句
Coder sonnet- → 编码十四行诗
Smolagents gpt- → 小型智能体 GPT-
Coder → 编码员
Smolagents gemini- → 小型智能体 Gemini-
Coder flash → 编码员快闪
Smolagents llama- → 小型智能体 llama-
Coder scout → 编码 scout
Asta v → Asta v
mixture → 混合
Faker gpt- → Faker gpt-
Asta Panda gpt- → Asta Panda gpt-
Asta Panda claude- → Asta Panda claude-
Asta claude- → Asta claude-
CodeScientist sonnet → CodeScientist 十四行诗
```

[原文第 31 页的完整图表与公式](assets/original-page-031.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
E2E-Bench
0.8 Efficiency Frontier
Asta Panda (claude-sonnet-4)
0.7 Asta v0 (mixture)
Asta_CodeScientist (claude-3-7-sonnet)
Faker (gpt-4.1 )
0.6 React (gpt-5)
Smolagents (gpt-5)
0.5
Asta Panda (gpt-4.1 )
Score

表内文字对照（数值与原始行列保持不变）：
E-Bench → E-Bench
Efficiency Frontier → 效率前沿
Asta Panda (claude-sonnet- → Asta Panda (claude-sonnet-)
Asta v → Asta v
mixture) → 混合）
Asta_CodeScientist (claude- → Asta_CodeScientist (claude-
sonnet) → 十四行诗）
Faker (gpt- → Faker (gpt-
React (gpt- → React (gpt-
Smolagents (gpt- → 小型智能体（GPT-）
Asta Panda (gpt- → Asta Panda (gpt-
Score → 评分标准
```

**表格与文字对照**

```text
0.4 React (claude-3-5-haiku)
React (claude-sonnet-4)
0.3 React (gpt-4.1)
React (gpt-4o)
React (gpt-5-mini)
0.2 React (gemini-2.5-flash)
React (llama-4-scout)
0.1 React (o3)
Smolagents (claude-3-5-haiku)
0.0 Smolagents (claude-sonnet-4)
10 2 10 1 100 101 Smolagents (gpt-4.1)
Smolagents (gpt-4o)
E2E-Bench-Hard Smolagents (gpt-5-mini)
Smolagents (gemini-2.5-flash)
0.7 Smolagents (llama-4-scout)

表内文字对照（数值与原始行列保持不变）：
React (claude- → React (claude-
haiku) → 俳句
React (claude-sonnet- → React (claude-sonnet-)
React (gpt- → React (gpt-
mini) → 迷你版
React (gemini- → React（Gemini-
flash) → 闪存）
React (llama- → React (llama-
scout) → scout)
React (o → React（或
Smolagents (claude- → 小型智能体（claude-
Smolagents (claude-sonnet- → 小型智能体（claude-sonnet-
Smolagents (gpt- → 小型智能体（GPT-）
E-Bench-Hard Smolagents (gpt- → E-Bench-Hard 大语言模型智能体（GPT-）
Smolagents (gemini- → 小型智能体（Gemini-
Smolagents (llama- → 小型智能体（llama-
```

0.6 0.5 0.4 分数

0.3 0.2 0.1 0.0 10 2 10 1 100 101 成本（美元）

图8：端到端发现基准测试的得分与成本分析（表17）。点表示平均值；误差条表示95%置信区间。帕累托前沿上的点用虚线连接，代表每个评估项目的最佳质量-成本权衡（E2E-Bench、E2E-Bench-Hard）。注意：x轴（成本）采用对数刻度。†表示未固定版本日期的模型。

[原文第 32 页的完整图表与公式](assets/original-page-032.jpg)

作为会议论文发表在 ICLR 2026 上

E E 估值 E.1 简短描述

PaperFindingBench 测试了智能体处理具有挑战性的科学搜索查询的能力。给定一个文本查询字符串，任务就是返回满足该查询的论文排名列表。这一新的基准测试是我们内部文献搜索智能体（Asta Paper Finder）评估体系的子集。与仅限于语义搜索查询的现有论文查找基准不同，我们的数据集包含了元数据查询和导航查询，以及多种类型的语义查询。这些查询来自 PaperFinder15 和 OpenSciLM16 的用户日志，以及 LitSearch（Ajith 等，2024）和 PaSa（He 等，2025）数据集。
评估检索任务具有挑战性，我们选择的评估指标及其他基准测试细节详见附录 E.2。简而言之，导航查询和元数据查询根据结果集的 F1 值进行评估，而语义查询则采用估计召回率和 nDCG 的调和平均值作为评估标准。最终评估指标为各查询得分的平均值。

LitQA2-FullText/LitQA2-FullText-Search 这两个测试基准用于评估智能体在生物医学领域回答问题和检索论文的能力。它们基于LitQA2数据集（Skarlinski等，2024年），该数据集包含199道选择题，每道题都与一篇目标论文相关，而该论文的全文能够回答相应问题。为了便于使用我们标准检索工具的智能体进行公平比较，我们将原始数据集筛选为85道题目，这些题目对应的相关论文可在指定截止日期内的Asta Scientific Corpus片段搜索索引中找到（见表2）。
根据 Skarlinski 等人的研究（2024年），LitQA2-FullText 通过正确答案问题的比例来评估准确性。LitQA2-FullText-Search 则专注于检索任务，旨在找到K篇论文中恰好有一篇是问题所针对的目标论文，其评估指标为 recall@30（与 Skarlinski 等人的研究（2024年）采用的标准一致）。为了避免在计算综合宏观平均文献理解得分时重复计算该基准测试（相对于该类别中的其他基准测试），我们在宏观平均计算中给这两个评估指标分别赋予0.5的权重。更多细节和比较内容请参见附录G.2。

ScholarQA-CS2 该基准测试评估了智能体回答长篇科学问题的能力。面对诸如“推荐系统中如何通常评估多样性？”这样的复杂科学问题时，任务要求识别相关的先前研究，并撰写一份包含适当引用来源的长篇回答报告。ScholarQA-CS2 是一个新的基准测试，它基于最近的 ScholarQA-CS（Asai等人，2024年）进行改进，通过纳入真实的科学查询，并引入四个评估维度来衡量答案及其归属的覆盖率和精确度，同时采用大语言模型作为评判工具。这四个评估维度的得分平均值即为最终评估指标。更多细节请参见附录 E.3。

ArxivDIGESTables-Clean 该基准测试旨在评估智能体生成文献综述表格的能力——该表格的行为出版物，列则包含用于比较和对比一系列论文的要素。给定一组相关论文以及描述表格用途的说明（例如“大语言模型预训练基准概览”），任务要求智能体自动输出完整的文献综述表格。我们发布了一个新的基准测试，该测试基于 ArxivDIGESTables，这是 Newman 等人在 2024 年通过从 ArXiv 论文中提取文献综述表格而创建的首个高质量文献综述表格生成数据集。
我们的评估包含两项关键改进：(i) 我们从原始测试集中挑选了一小部分干净的样本；以及 (ii) 我们为该任务引入了一种端到端的评估方法。通过提示大语言模型将这些表格“展开”成陈述句来对表格进行评分。评估指标为参考表格中真实陈述句被展开生成的表格所包含的比例（由大语言模型评判者判定）。更多细节请参见附录 E.4。

超级专家 超级专家基准测试（Bogin等，2024年）（从研究仓库中设置与执行任务）旨在检验代码智能体在设置和执行机器学习与自然语言处理论文中所述的Python机器学习实验方面的能力。该测试针对的是那些常见但往往较为复杂且耗时的任务，即从文档较少的仓库中设置并运行代码 15 https://paperfinder.allen.ai/chat 16 https://openscilm.allen.ai/

[原文第 33 页的完整图表与公式](assets/original-page-033.jpg)

作为会议论文发表在 ICLR 2026 上

与已发表的论文配套执行。当收到自然语言指令以及一个 GitHub 仓库指针时（例如，要求按照某篇论文的代码在指定 URL 处训练模型），任务包括克隆该仓库、安装必要的依赖项、进行配置、运行指定的训练/评估流程，并报告结果（如模型准确率）。与其他以仓库为中心的代码执行任务不同，此处特别关注 GitHub 上资源匮乏的研究仓库——即那些研究人员在验证和扩展已有已发表成果时经常遇到的仓库。更多细节请参见附录 E.5。

CORE-Bench-Hard− CORE-Bench-Hard− 基准测试（Siegel等人，2025年）旨在评估智能体复现论文中实验与分析的能力。输入来自CodeOcean.com的“胶囊”，其中包含与论文一同发布的代码和数据，以及一套指示需使用该胶囊进行特定分析的指令（完整示例见附录H.7.1）。任务要求完成这些分析并在report.json文件中撰写答案。CORE-Bench-Hard−中的胶囊具有高度可复现性，涵盖计算机科学、社会科学和医学等多个领域，且使用Python和R编程语言。更多细节请参见附录E.6。

DS-1000 DS-1000 基准测试（Lai等人，2023年）用于评估代码模型在日常研究中所遇到的常规数据科学任务中的能力。输入是一个编程问题以及一个未完成的代码片段，智能体需补全该片段以解答问题（参见附录H.8.1中的示例）。通过将该代码片段与特定问题的测试用例进行运行来对其评分。该基准测试包含1000道题目，涉及7种Python库，这些题目最初来自StackOverflow，并经过处理以避免训练信息泄露。
我们采用了《Inspect evals》（英国人工智能安全研究所、Arcadia Impact及Vector Institute，2025年）中提供的任务实现方案，并报告了所提出代码通过目标测试案例的准确率。更多细节请参见附录 E.7。

DiscoveryBench 该 DiscoveryBench 基准测试（Majumder等人，2025年）旨在检验智能体是否能够从给定的数据集中自动发现并验证假设，并进行基于数据的分析。任务的输入是一个发现目标以及一系列数据集及其相关元数据，输出则是一个符合该目标的假设，该假设在上下文、变量和数据集所支持的关系方面具有最高的特异性。可选地，还可以输出一个推导假设的工作流程，以补充假设中已有的信息。
这是首个全面的基准测试，用于评估智能体或大语言模型在6个不同领域的数据集上执行数据分析能力——包括数据准备、基础统计分析、复杂数据转换及建模等——这些领域涵盖社会学和工程学等方向。我们从6个领域的已发表成果所提供的公开公共存储库中收集任务数据集。与数据集相关的发现目标由相关论文提供，或由人类标注得出；其中每个“金标准”输出（即假设）均经过数据分析专家严格验证。该基准测试中的表现指标为预测假设与金标准假设的一致性。
最终指标“假设匹配得分”是由三个作为评判者的大语言模型得分相乘得到的结果，用于衡量预测假设与真实假设在上下文、相关变量及其相互关系方面的契合度。更多细节请参见附录 E.8。

E2E-Bench 任务旨在测试智能体是否能够完成从构思、规划、（软件）实验设计、实现、执行、分析到撰写最终报告的全流程研究工作，即一个完整的研究周期。该任务的输入是人工智能/自然语言处理领域的研究问题以及调查该问题的详细步骤描述，输出则包括技术报告、智能体的推理记录，以及生成的任何代码或成果（如数据集）。
这是一次新发布的产品，它构成了首个与智能体无关的基准测试（即一种并非旨在凸显特定智能体优势与能力的基准测试），用于比较自动科学发现智能体。它填补了当前研究领域的空白——虽然存在许多此类智能体，如 AI Scientist（Lu等人，2024）、AgentLab（Schmidgall等人，2025）和 CodeScientist（Jansen等人，2025），但目前缺乏系统化的比较方法。实际上，为了进行更可控的系统间比较，这些问题被详细定义，因此仅对构思与规划步骤进行了有限的测试。
同时，这些问题并不像典型的机器学习编程问题那样具有明确的指导性，例如在 MLAgentBench 项目中（Huang 等，2024）。这些问题是通过机器生成与人工评审相结合的方式创建的，包含详细的任务描述以及针对具体问题的评分标准。最终得分则是基于整体大语言模型作为评判者的评估结果。

[原文第 34 页的完整图表与公式](assets/original-page-034.jpg)

作为会议论文发表在 ICLR 2026 上

基于通过对照评分标准对每个相关智能体输出（报告、代码及成果文件）进行评估所得到的三个大语言模型作为评判者的得分。更多细节请参见附录 E.9。

E2E-Bench-Hard 该任务与 E2E-Bench 类似，不同之处在于题目通常更为困难。其任务定义、评估方法、基准模型及环境均与 E2E-Bench 一致，但数据收集方式有所不同。更多细节请参见附录 E.10。

E.2 PA P E RFI N D I N GBE N C H

在基于大语言模型的大语言模型工作流兴起过程中，能够针对多种搜索条件回答具有挑战性的科学搜索问题已成为可能。然而，目前的论文评估基准大多仅涵盖少数几种搜索查询类型（例如 LitSearch (Ajith等，2024)、PaSa (He等，2025) 以及 LitQA2 数据集 (Skarlinski等，2024)）。这些基准仅关注纯语义层面的标准，未包含元数据或导航查询，也缺乏覆盖不同语义内类挑战类型的方法论流程。
PaperFindingBench 是我们内部针对文献搜索智能体（Asta Paper Finder）进行的评估子集，重点针对具有挑战性的查询进行测试（该内部评估还包含大量较简单的查询，以确保产品的稳定性并避免性能退化）。PaperFindingBench 旨在包含具有挑战性且现实性的任务（包括当前系统表现不佳的课题），并且尽可能基于真实世界的查询和信息需求。此外，它在两个维度上力求广泛性和多样性：首先，它涵盖更广泛的信息需求范围。
与那些专注于语义查询、根据内容描述来查找用户未知的论文的现有数据集不同，我们的基准测试还包含“导航式”查询，这些查询基于简短的参考信息来寻找用户已知的单一论文（“alpha-几何学论文”），以及基于多种元数据标准来定义论文集合的查询（“引用了Transformer论文的ACL 2024论文”）。多样性第二维度属于语义搜索类别，我们旨在涵盖不同类型的查询挑战。
该数据集包含了不同的类别，但并未明确说明哪些查询属于哪个类别（尽管人类可以非常容易地判断出来）。这符合我们的信念，即文献搜索智能体应该能够处理所有类型的查询，哪怕只是将它们分配给不同的子智能体即可。PaperFindingBench包含48个导航查询、43个元数据查询和242个语义查询。部分元数据查询在其标准中包含（简单的）导航查询，但目前元数据查询与语义查询之间存在严格的区分（元数据查询不涉及语义成分，反之亦然），未来版本可能会发生变化。

数据集构建 导航类查询基于 PaperFinder17 的使用日志，其中包含了在某个时间点 PaperFinder 未能找到相关结果的查询。语义类查询则来自多种来源的混合：PaperFinder 使用日志、OpenSciLM18 使用日志以及现有的文献搜索数据集：LitSearch（Ajith等人，2024年）和 PaSa（He等人，2025年）。我们首先筛选出那些对 PaperFinder 系统具有挑战性的查询子集，即那些系统判定为“完全相关”但返回结果很少或没有结果的查询，并且我们已确认（针对查询日志）或知晓（针对标注数据集）存在相关的论文。
我们随后手动检查了这些查询集合，以识别不同的挑战类型。最后，我们构建了一个包含所有挑战类型的集合，同时优先选择那些在消融实验中使用其某个组件运行 PaperFinder 后，我们发现的相关论文数量较少的查询。该集合中包含了一些我们认为存在大量相关结果的查询，以及一些我们认为仅存在少量相关结果的查询。对于许多查询而言，评估论文的相关性不能仅基于标题和摘要，而需要依据论文全文中的证据。
元数据查询：这些查询是人工设计的，旨在全面覆盖语义学者 API 的使用情况、API 之间的交互关系，以及那些可解决但未被直接支持的挑战。17 https://paperfinder.allen.ai/chat 18 https://openscilm.allen.ai/ 19 例如，这些包括多种标准、标准之间的复杂关系、使用不常见术语、使用错误的行话、寻求不属于论文主要论点内容的细节，以及提供不必要的甚至分散注意力的背景信息。

[原文第 35 页的完整图表与公式](assets/original-page-035.jpg)

作为会议论文发表在 ICLR 2026 上

通过诸如否定条件（“未引用 Transformers 论文”）这样的 API。这些查询包含属性的嵌套与递归操作，其设计灵感来自数据集中最复杂的查询，并进行了一些调整。我们重点考虑了需要结合多个 API 的查询。

评估 对检索效果的评估具有挑战性，因为理想情况下需要包含语料库中所有相关文档的“金标准”集合，而这一集合往往无法得知。对于导航查询和元数据查询而言，存在这样的金标准集合（每个元数据查询都对应一段使用 API 完全解决的 Python 代码，其结果被用作金标准集合）；而对于语义查询，则不存在完整的覆盖金标准集合，因此我们采用部分注释与基于大语言模型的判断相结合的方法。
每个查询都对应一组（可能为空）已知合适的匹配项，以及一组加权相关性标准；这些相关性标准需要由大语言模型针对论文中的证据进行逐一验证，才能判定该匹配为合适。这些单独的相关性标准是由大语言模型基于原始查询的（可能扩展后的）版本自动生成的。对于五分之一的查询，相关性标准需要由人工进行验证、修正或调整。
由于调整与修正大多非常有限，且基于大语言模型的相关性标准对于某些有人工标注数据的论文查询来说非常有效，我们认为所有相关性标准都是可靠的，尽管未来版本可能会进一步改进。由于我们的目标是评估检索效果，而非评估大语言模型处理长上下文的能力，因此我们不提供论文的全文用于相关性判断，而是要求每个结果项都与提取的证据文本相关联（该文本可来自论文本身或引用该论文的其他论文），然后将这些文本输入到大语言模型中进行相关性判断。

评分指标 我们使用两种不同的评分指标。对于已知黄金集的导航和元数据查询，我们采用结果集上的 F1 分数来评估每个查询的得分。而对于基于大语言模型判断的语义查询，我们可以计算精确率，但无法计算召回率。一个可能的指标就是被大语言模型判定为相关的返回文档数量，不过该数值是无限的，难以与 AstaBench 中的其他评分指标结合使用。因此，我们选择针对每个查询估计的集大小来计算召回率（即除以一个估算值而非确定的集大小），从而将数值限制在 0 到 1 之间。
估计的集合大小是通过使用非常宽松的阈值运行多种版本的 PaperFinder，取这些结果集合的并集，然后乘以一个介于2到10之间的系数来估算上限，从而为额外的论文留出空间（初始集合较小时可靠性较低，因此乘以更大的系数）。需要注意的是，在极端情况下，这可能导致召回数大于1。我们通过考虑经过检索调整的 recall@k 指标来限制这一情况，其中将k设为估计的集合大小（这对应于已建立的 recall@R 指标，但我们计算的是估计值减去 recall@估计值）。
计算 recall@k 分数具有双重作用：它限制了得分的范围，同时也抑制了“无用”结果的提交。我们并非通过精确度来平衡 recall@k 分数，而是通过 nDCG 来实现，因为 nDCG 能提供更相关的信号（更倾向于对相关文档进行排名而非无关文档）。nDCG 与 estimated-recall 的结合使得精确度变得多余。为了为每个单独查询提供单一分数，我们采用调和平均数（即 estimated-recall 与 nDCG 的 F1 值）将召回率和 nDCG 数值合并起来。为了为整个数据集提供统一的单一分数，我们会对所有查询的分数进行平均，而不考虑它们的类型。

工具截止日期 我们鼓励参与者使用 Asta Scientific Corpus 中提供的关键词和片段搜索功能。无论如何，我们预计所有提交内容都需遵循该工具与语料库截止日期相同的截止时间，即 2025 年 6 月 1 日。

示例输入可参见附录 H.1.1。

E.3 S C H O L A R QA-CS2

科学文献综述是科学工作流程中长期存在的组成部分，如今越来越多地通过商业及开源长文问答服务实现自动化，例如 OpenAI Deep Research、ScholarQA（Singh等人，2025）、Elicit、Perplexity、Paper QA（Skarlinski等人，2024）等。

[原文第 36 页的完整图表与公式](assets/original-page-036.jpg)

作为会议论文发表在 ICLR 2026 上

以及许多其他情况。对文献综述问题的长文回答进行评估是自然语言处理中的一个挑战性任务。对于任何一个给定问题，都存在多种可接受的长文回答；即使拥有“黄金”答案的数据集，也很难定义如何根据质量的相关维度（涵盖性、正确性、归因等）对某个回答进行评分。这一任务在科学领域尤其具有挑战性，因为评估答案需要深厚的学科专业知识，且这种专业知识可能会随时间变化。Asai等人（2024）提出了ScholarQABench，该工具包含多个数据集，用于从多个维度评估科学问答系统。
其数据集中仅有一个——即我们在研究中使用的 ScholarQA-CS——根据每个问题所需的关键要素集合来评估答案覆盖率；这些关键要素是该研究中手动标注的、用于确保答案全面性的必要要点。ScholarQA-CS的作者指出了该数据集的若干局限性，包括标注的关键要素可能受到“操纵”影响，因为它们反映了两位标注者的特定偏好，且整个评估过程依赖于启发式设定的权重指标。
在我们的新数据集中，我们收集了来自各种候选系统响应的多样化关键要素，并开发了新的大语言模型作为评判工具的方法，以评估答案相关性及提升引用评价。

评估 我们的 ScholarQA-CS2评估方法会接收一个问题的答案，并输出一个分数，该分数是四个回答质量指标的平均值：引用召回率（答案中的每一项主张是否完全由相关引用支持）、引用精确率（答案中的每一篇引用是否至少部分支持其对应的主张）、回答相关性（答案中的每一段内容是否涉及问题内容）以及回答覆盖度（答案中涵盖必要点的比例）。这四项评估均依赖大语言模型作为评判者，相关提示语请参见附录 H.3.3。
为了准确评估引用召回率和引用精确率，我们利用了许多被评估系统的一个特性：它们会提供每篇被引用文章的引文，以支持相关的主张。对于每一项主张，如果大语言模型判断认为该主张完全由其引用的内容支撑，并且包含至少一条支持性引文，则该主张的引用召回得分即为 1.0。
如果大语言模型评判者依据所引用的论文标题来评估支持程度，但缺乏相应的引文作为支撑（这种情况可能由于系统没有引文功能，或特定来源的文本因版权问题无法被系统获取），则该主张得分为 0.5。否则，该主张得分为 0。我们最终的引用检索度量值是各主张得分的平均值。为了计算引用精确率，我们依据大语言模型评判者对引文是否至少部分支持相关主张的评估结果：如果符合，该引文得分为 1（若缺乏引文则得分为 0.5），否则得分为 0。
我们最终的引用精度是这些得分按声明进行宏平均后的平均值。需要注意的是，这些引用指标无法验证所引用的文献是否真实存在，也无法证明被引用的片段确实出现在被引用的来源中。因此，在评估过程中，我们排除了那些无法获取真实文献的系统所生成的片段，因为这些系统很可能产生幻觉并获得虚高的分数。对于答案相关性方面，我们要求大语言模型评判者逐段评估答案，并要求其返回那些与查询直接无关的段落列表。
我们最终的答案相关性得分即为相关段落的比例。第四个评估指标——答案覆盖度则更为难以判断，因为不仅需要评估答案本身，还需要识别问题正确回答中必须包含的关键要素。借鉴 TREC 信息检索竞赛中的方法（Craswell 等，2021），对于每个问题，我们会从所评估的系统中收集一批候选成分，并借助大语言模型评判器对这些成分进行评估。
具体而言，对于每个评估问题，我们要求大语言模型评判者从每个系统的回答中提取关键要素，识别与这些要素相关的具体细节，并将每个要素的重要性分为“回答关键”（回答该问题必须包含的内容）或“有价值”（虽不错但非必需的内容）。随后，我们通过指示大语言模型评判者将语义相似的要素归为同一组并保留其重要性标签，来对提取的要素进行分组。这一过程最终生成了针对每个问题的特定要素分组评分标准。要素提取提示见附录 H.3.5。
评分标准中的各项指标在答案评估时用于衡量覆盖程度。对于每一个指标组，大语言模型评判者会给出0分（不符合评分标准中第20条所述的标准）。具体而言，我们参考了表3中列出的八种“长问答”系统，以及两个没有检索功能的基线大语言模型——Claude Sonnet 4.0无思考版和Google的Gemini 2.5 Pro。所有引用的报告均是在2025年6月24日截止日期之前获得的。

[原文第 37 页的完整图表与公式](assets/original-page-037.jpg)

作为会议论文发表在 ICLR 2026 上

成分），1（部分符合标准）或2（完全符合标准）。最终答案覆盖得分是各成分得分的加权平均值，成分的重要性决定了权重（“答案关键”成分的重置为“有价值”成分的两倍）。答案覆盖提示见附录 H.3.3，样本评分标准见附录 H.3.2。

数据收集 作为测试集，我们收集了 100 个由 OpenSciLM 接收的用户问题（Asai 等，2024），这些问题经过语言、质量及主题方面的筛选后保留下来（我们选取的是计算机科学领域的题目）。选择过程的详细内容见附录 E.3.1。作为开发集，我们保留了之前发布的包含 100 道题目的 ScholarQA-CS 数据集（Asai 等，2024），并采用上述相同方法更新其题目列表。

大语言模型评判者的选择 由于我们的评估以大语言模型为评判依据，我们选择了一种能够处理长输入上下文、处理长格式答案，并遵守提示中所述各种约束的大语言模型。我们选择使用 Gemini-2.5 模型。我们将 Gemini-2.5-flash 和 Gemini-2.5-pro 的性能作为第 4.3 节在 ScholarQA-CS2 上评估的优化系统任务的评判者，发现皮尔逊相关系数高达 0.995。因此，考虑到其较低的使用成本，我们采用 Gemini-2.5-flash 作为官方评判者。

对 ScholarQA-CS2 的验证我们通过测量其排序分数与专家标注者判断之间的相关性来实证验证我们的评估方法。具体而言，标注者会收到一个查询以及三个模型的答案，并被要求根据答案质量对其进行排序，同时考虑引用质量、文本相关性以及其他更主观的偏好因素，如流畅性、组织结构和结构安排。
我们对所有评估测试题目进行这种三方对比分析，从六个智能体池中随机选取答案——包括 Asta Scholar QA（含表格版）、OpenAI Deep Research、Elicit、Perplexity Sonar Deep Research、STORM，以及基于来自实际 Asta Scholar QA 的 QA 对进行优化的 Qwen3-8B 模型，并计算胜率。在系统层面，我们发现人类与模型之间的一致性处于中等水平（Kendall τ = 0.467），当排除专家存在系统性偏好偏差的 Elicit 输出后，该值显著上升至 0.800。在实例层面，对于有明确胜者的情况，整体一致性为 68.1%（τ = 0.369）。
该综合评分高于各单项指标的评分（38.7%–63.5%），这表明这些指标可能协同作用以更精准地反映人类判断——它们相互补充，抵消各自的不足，从而整体效果优于任何单一指标单独使用所能达到的效果。在评分标准验证方面，我们还探讨了从所评估系统获取候选成分这一做法可能带来的偏见问题。具体而言，我们研究了当这些系统被排除在成分提取阶段之外时，其答案覆盖得分会如何变化。
具体而言，我们选择了那些具有竞争力答案覆盖率的系统（如 Asta Scholar QA（含表格）、OpenAI Deep Research、Elicit、Perplexity Sonar Deep Research、SciSpace Deep Review），并为测试题目制定了五套不同的评分标准。每套标准对应一个系统，并从其余九个系统中选取相关指标。我们使用这些保留的评分标准重新计算答案覆盖率，并将其与完整的10个系统报告结果中的答案覆盖率进行对比。
研究结果表明，保留样本对各系统的影响存在差异：其中三个系统（Asta Scholar QA（含表格）、Elicit 和 SciSpace Deep Review）在保留样本条件下性能显著下降（平均下降 2.5 分；p <= 0.01），而另外两个系统（OpenAI Deep Research 和 Perplexity Sonar Deep Research）的下降幅度并不明显（< 1 分；p > 0.16）。随着系统数量的增加，保留样本带来的偏见程度会降低：针对 4 个系统的独立保留实验表明，所有被评估的系统平均下降 5 分。这说明在制定评分标准时纳入更多系统有助于减少偏见。
然而，还需要进一步研究以明确偏见的原因，以及如何最公平地评估那些未被用于评分标准制定的系统。

工具截止日期 我们的长文问答任务依赖于 Asta Scientific Corpus 中提供的关键词和片段搜索功能。针对该任务，这两个工具的语料库截止日期均设定为 2025 年 5 月 1 日。

示例输入可参见附录 H.3.1。

[原文第 38 页的完整图表与公式](assets/original-page-038.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
Field of Study # Papers
Computer Science 94.3%
Mathematics 21.3%
Engineering 9.1%
Medicine 5.8%
Physics 4.2%
Biology 1.3%
Other 0.8%

表内文字对照（数值与原始行列保持不变）：
Field of Study → 研究领域
Papers → 论文
Computer Science → 计算机科学
Mathematics → 数学
Engineering → 工程学
Medicine → 医学
Physics → 物理学
Biology → 生物学
Other → 其他
```

表18：ArxivDIGESTables-Clean验证集与测试集中论文的研究领域分布。请注意，一篇论文可能包含多个研究领域标签。拥有少于五篇论文的标签被归为“其他”类别，该类别包括地质学、社会学、材料科学、历史学、政治学、环境科学与化学。

E.3.1 问题选择 在此我们概述了收集100个测试集问题的流程。我们在2025年2月21日从OpenScholar获取了8K个包含三个或更多单词的随机输入问题，并利用大语言模型（Claude Sonnet 3.5）从五个维度对这些问题进行标注：语言、研究领域、清晰度、完整性及问题类型。基于生成的标注结果，我们筛选出表达明确研究请求的英语、计算机科学领域的问题，最终得到3.5K个问题。随后我们随机抽取200个样本，由四位作者手动评估其问题的清晰度、质量及回答性，从而确定最终的100个测试问题。
关于详细的提示词说明，请参见附录 H.3.4。

E.4 高级语言模型摘要工具 -C lean

数据收集 Padmakumar等人（2025）指出，ArxivDIGESTables中的实例有时存在以下问题之一：

• 通用列（如发表年份、研究重点等） • 无法恢复的列，其中包含从表格中论文全文中无法获取的信息（如数据集实例）

通用列很容易生成（性能估计过于乐观），而无法覆盖的列则无法生成（估计过于悲观）。因此，对不含这些问题的子集进行评估，能够确保我们获得真实的模型性能估计。由于自动过滤此类实例并非易事，Padmakumar等人（2025）手动整理了ArxivDIGESTables-Clean这一包含170个无问题实例的子集。我们使用该子集，随机选取100个实例作为测试集，剩余部分作为验证集。表18展示了ArxivDIGESTables-Clean中研究领域的分布。

评估 Newman等人（2024）最初提出了一种基于参考的自动化评估流程，用于文献综述表格生成任务。该流程包含两个组成部分：对生成的表格的架构（列）和值（单元格）进行评估。然而，这种分拆式评估存在两个缺点。首先，它要求执行该任务的智能体必须展示相同的组件集合（列生成与单元格值生成），而非允许在智能体设计上具备灵活性。
其次，细胞值评估是通过向智能体提供参考表中的“黄金”列集合，并判断生成的细胞值与参考表中的细胞值匹配程度来进行的。因此，这一评估环节实际上仅衡量了智能体在单篇论文中回答问题的能力。为克服这些缺点，我们开发了一种基于 TAB E VAL 方法的端到端评估方法（Ramu 等，2024）。TAB E VAL 协议首先通过将生成表格拆分成一系列自然语言原子陈述列表来实现对表格语义的表示，这一过程被称为表格展开。
然后，它对这些21种查询类型进行比较。针对这些查询，我们指示模型区分那些包含可识别请求的查询、与搜索词相似的查询，以及旨在测试智能体能力的查询（例如：“你能写吗？”或“我能说中文吗？”[原文保留]）。

[原文第 39 页的完整图表与公式](assets/original-page-039.jpg)

作为会议论文发表在 ICLR 2026 上

基于蕴含关系的度量标准，根据参考表生成的与真实陈述相关的表述。我们采用相同的方法，引导 GPT-4o 对生成的表格进行展开处理，然后以召回率的形式报告参考表中被展开生成的表格所包含的真实陈述的比例（由 GPT-4o 进行判断）。表格展开及蕴含关系评估的提示语分别见附录 H.5.2 和附录 H.5.3。

示例输入可参见附录 H.5.1。

E.5 超级专家 X 实验

任务 每个 SUPER-Expert 输入包含：(a) 一个指定要在代码仓库中执行的具体研究任务的提问（参见附录 H.6.1中的示例），(b) 需要生成的特定输出结果的说明，以及 (c) 对应的 GitHub 仓库详情。智能体的目标是下载目标仓库，完成运行仓库代码所需的所有设置与配置工作，根据任务需求修改代码中的特定内容（如数据集名称或位置），执行目标任务，最后以期望的格式报告结果。

注释 使 SUPER-Expert 任务具有挑战性的是，这些资源库缺乏完善的文档记录，每个仓库都有各自的问题集。虽然有时可以制定一个高层次的解决方案计划，但很难预测在设置和执行过程中会遇到哪些具体的错误。因此，针对这些任务的优质解决方案是由通过 Upwork 雇佣的高技能标注员完成的。他们以 Jupyter 笔记本的形式提供解决方案，这些文件也作为测试基准的一部分提供给大家。

AstaBench评估框架包含了Bogin等人（2024年）提出的两种原始划分方式：包含45个端到端问题的专家划分作为测试集，以及包含50个自动生成问题的自动划分作为开发集——这些问题是根据通过特定筛选的仓库README文件生成的。对于专家划分的评分，是通过计算生成的解决方案与标注金标准解决方案之间的精确匹配度指标来进行的（通常金标准解决方案为包含损失值等实验指标的JSON字典）。

示例输入可参见附录 H.6.1。

E.6 CORE-B ENCH-HARD −

我们包含在 AstaBench 中的 CORE-Bench-Hard− 版本在几处进行了调整：

• 原始任务包含三个难度级别（简单、中等和困难）。我们采用困难版本，通过从胶囊中移除若干文件（如运行脚本和预计算结果文件）来提升任务难度，因此智能体必须在进行分析之前自行解决如何安装和运行代码的问题。• 我们删除了需要使用 GPU 才能运行的实例，以使资源需求与其他任务保持一致。
这使得数据集缩减为 37 个样本，而非原来的 45 个。• 尽管论文中未提及，原始基准测试代码包含一份标准提示文件，其中描述了任务的一般要求及输出报告的预期格式。我们始终在任务输入中包含这些说明，以确保任务具有自包含性。• 我们在 AstaBench 中使用原始数据集的训练集作为验证集。22 https://www.upwork.com 23 https://jupyter.org 24 https://github.com/siegelz/core-bench/blob/db8a3d00c25fc30cf091f63102 03b7c715268084/benchmark/benchmark_prompts.json

[原文第 40 页的完整图表与公式](assets/original-page-040.jpg)

作为会议论文发表在 ICLR 2026 上

测试集中的研究领域分布为：14道社会科学问题（37.8%），12道医学科学问题（32.4%），以及11道计算机科学问题（29.7%）。

示例输入可参见附录 H.7.1。

E.7 DS-1000

我们使用了 Lai 等人在 2023 年提出的 DS-1000 原始版本，以及 Inspect evals 团队在 2025 年提供的任务实现方案（该方案由英国人工智能安全研究所、Arcadia Impact 和 Vector Institute 提供）。与原始测试集不同，我们从原始数据集中保留了 100 个样本用于验证和系统开发。

示例输入可参见附录 H.8.1。

E.8 DI S C O V E R YBE N C H

(Majumder等人，2024) 为数据驱动发现场景下的自动化科学发现范式提供了初步证据，在此场景中，假设的搜索与验证均可仅通过数据集来完成（即在物理实验和数据收集之后），但这一能力的具体程度仍不确定。因此，我们旨在系统地评估以下问题：当前最先进的LLM在自动化数据驱动发现方面的能力如何？
回答这个问题很困难，因为现实世界中的数据驱动发现涉及多种领域和主题，因此很难构建一个可靠的评估框架来衡量进展。我们通过对数据驱动发现的务实形式化方法来解决这一问题，即寻找特定情境下变量之间可能存在的关联，其中这些方面的描述可能并不符合数据集的语言。于是，数据驱动发现任务就会缺少其中一个组成部分，例如“城市土地利用是如何影响加泰罗尼亚地区外来植物的入侵的？”
重要的是，这种形式化方法能够利用这些方面，实现对各种现实问题进行系统且可重复的评估。

Task DiscoveryBench（Majumder等人，2025年）是一种用于发现数据驱动假设的新颖基准测试。在该基准测试中，数据驱动的发现任务定义如下：给定一个或多个任务数据集及一个发现目标，需推导出一种能够最精准地满足该目标的假设，且该假设需符合数据集所支持的上下文、变量及关系特征。可选地，还可以输出一个假设推导工作流，以补充假设中已有的信息。每个假设都必须通过数据分析工作流以编程方式（例如使用Python）进行验证。

数据收集 我们的目标在于复现研究人员为从一个或多个数据集中寻找并验证假设而进行的科学流程。我们专注于六个科学领域，在这些领域中，基于数据的研究是科学进步的基石：社会学、生物学、人文学科、经济学、工程学以及元科学。我们解决发现任务的黄金路径严格遵循各领域已发表的论文工作流。由于大多数论文被大量引用、经过同行评审，且来自该领域的顶级期刊，因此可以合理假设这些发表的工作流在科学上是有效的。DiscoveryBench中的领域分布如表19所示。

评估方法 我们通过测量预测假设与真实假设在自然语言中的一致性来评估任务性能。我们设计了一种基于模型的评估策略，以 gpt-4-preview-0125 作为评估器，该评估器基于我们对数据驱动假设的结构化形式化定义——即一个假设由上下文、变量以及变量之间的关联组成。关键在于，评估器会评估预测假设与真实假设中语言元素之间的蕴含关系或等价性，这一过程借鉴了基于大语言模型的语言蕴含技术，作为科学主张验证的自动化工具。

示例输入可参见附录 H.9.1。

[原文第 41 页的完整图表与公式](assets/original-page-041.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
Domain Percentage
Meta-science 41.8%
Sociology 24.3%
Humanities 15.9%
Biology 6.7%
Engineering 6.3%
Economics 5.0%

表内文字对照（数值与原始行列保持不变）：
Domain Percentage → 领域占比
Meta-science → 元科学
Sociology → 社会学
Humanities → 人文科学
Biology → 生物学
Engineering → 工程学
Economics → 经济学
```

表19：DiscoveryBench中领域的分布情况

**表格与文字对照**

```text
Agent Model E2E-Bench E2E-Bench-Hard
Faker gpt-4.1† 0.00 0.00
Asta CodeScientist claude-3-7-sonnet 0.05 0.03
Asta Panda claude-sonnet-4 0.00 0.03

表内文字对照（数值与原始行列保持不变）：
Agent Model E → 智能体模型 E
E-Bench E → E-Bench E
E-Bench-Hard → E-Bench-Hard
Faker gpt- → Faker gpt-
Asta CodeScientist claude- → Asta CodeScientist claude-
sonnet → 十四行诗
Asta Panda claude-sonnet- → Asta Panda claude-sonnet-
```

表20：整体端到端任务完成率（所有必要步骤均成功完成）。虽然单个步骤的完成精度相当不错（约为70%，见表10），但由于累积效应，完成所有（通常10-15个）步骤的可能性几乎为零。

E.9 E2E-B E N C H

数据与数据收集 每个示例都是人工智能/自然语言处理领域的研究任务，例如：

“检验为大语言模型设计的有效提示能否直接提升小型模型在分类任务中的性能。”

随后对执行该测试的步骤进行了详细描述。任务是通过机器生成（使用 Asta CodeScientist 的 ideator 工具）与人工审核编辑相结合的方式创建的：首先，我们收集了所有2021年及以后发表、至少拥有100次引用且可在arXiv上获取的*ACL会议论文（共288篇）。然后，ideator 工具随机选取两篇论文，利用它们通过大语言模型生成最多五个研究思路，重复此过程直至获得约400个思路，之后这些思路会自动进行简化、筛选和排序。
最终，人类专家评审员对排名靠前的方案进行了审核，剔除那些不可行或不可能的方案，并在可能的情况下进行少量修改以完善它们。前50个方案被用于构建最终数据集。

在想法生成过程中，还会自动生成针对具体示例的评分标准，以判断是否完成了所有必要的研究步骤。每个评分项均通过大语言模型作为评判者，从 ASD 输出的三个方面（报告、代码、成果）分别进行评分，从而得出总体分数。更多细节请参见附录 F.9。虽然我们主要报告平均研究步骤完成率（表 10），但表 20 则显示了整体任务完成分数（当所有评分项要求都满足时）。由于累积效应，这些总体分数几乎为零，这反映了完整端到端研究的持续挑战。

环境说明 鉴于 ASD 智能体的复杂性和时间/成本问题，ASTABench 支持基于缓存的智能体：首先，(a) 所有示例的回答都在离线阶段预先计算好；然后，(b) 运行时基于缓存的智能体只需检索已缓存的回答即可，从而能够在 ASTABench 环境中进行评分。

示例输入可参见附录 H.10.1。

E.10 E2E-B E N C H -H A R D

数据收集 我们并未使用 Asta CodeScientist 的创意生成工具，而是采用 HypER 假设生成系统（Vasu 等，2025）。HypER 首先从上述收集到的高被引 ACL 论文中识别出一项研究趋势，针对该趋势生成初步想法，随后根据相关论文片段进一步完善，以提出新颖且未被充分探索的任务。与 E2E-Bench 不同，我们不执行任务简化步骤，而是保持原样

[原文第 42 页的完整图表与公式](assets/original-page-042.jpg)

作为会议论文发表在 ICLR 2026 上

最初的提案保持不变。接下来，所提出的任务会被自动排序，并由人类专家评估者进行人工审核，他们会剔除或修正不可行的任务。最终，前50个任务被用于构建最终数据集。

示例输入可参见附录 H.11.1。

## F 智能体

我们将评估过的智能体分为两部分进行描述：(1) 我们针对科研任务优化的 Asta 智能体；以及(2) 通过该工具包可使用的众多基准智能体——包括通用型与科学专用型。

F.1 智能体系统

我们发布了九种针对科研优化的智能体类库，其中包括 Asta v0——一种能够自动识别任务类型并分配至相应特定子智能体的调度智能体。

Asta Paper Finder 是我们的论文查找智能体，旨在根据内容与元数据标准协助定位相关论文集。它由手动编码的组件构成流程，在多个关键环节涉及大语言模型的决策，同时基于大语言模型对检索到的摘要和片段进行相关性判断。从整体来看，查询会被分析并转化为结构化对象，随后被输入到执行规划器，该规划器会将分析后的查询分配到不同的工作流中，每个工作流都针对特定的论文查找需求。
每个工作流可能包含多个步骤，并生成一组经过相关性评估的论文集合，随后根据内容相关性以及查询中可能出现的其他标准（如“早期研究”、“具有影响力”等）对论文进行排序。该智能体是我们可在 Asta 中使用的实时论文查找智能体的简化版本，该版本处于冻结状态，仅支持单轮交互，不会请求澄清或拒绝查询，且仅使用 AstaBench 公共 API 中提供的工具。其详细描述见附录 F.3。

Asta Scholar QA 是一个已发表的科学类长篇问题回答系统。它由三个组件构成：用于从两个 Semantic Scholar 语料库中识别相关段落的检索模块；用于筛选所检索段落中最相关内容的重新排序器；以及用于生成包含在线引用在内的最终综合报告的多步骤大语言模型处理流程。我们在该处理流程中使用了多种大语言模型（包括 gpt-5†），并采用 claude-sonnet-4-20250514 模型获得了最佳结果。此外，我们还使用 gpt-4o-mini 和 gemini-2.5- flash-preview-05-20 模型进行了实验，以对比其性能与成本优势，并与更小型的大语言模型进行比较。
有关该系统的详细信息，请参见 Singh 等人的研究（2025年）。

Asta Scholar QA（含表格）是Asta Scholar QA的一个变体，增加了文献综述表格功能。Scholar QA系统会生成答案，每个部分要么是长段落，要么是项目及其描述列表。在后者中，对应部分还包含一张文献综述表格，用于从与查询相关的多个维度对引用的论文进行对比。表格的创建也会导致更多的LLM调用，从而增加成本。我们报告了使用claude-sonnet-4-20250514作为核心LLM时该变体的最佳结果。

Asta Table Synthesis 是一个已发表的文献综述表格生成系统。它采用两步提示流程：第一步从 Semantic Scholar 数据库中检索所有输入论文的标题和摘要，并将这些信息与表格标题一起提供给大语言模型，以便生成用于比较论文的列/方面的建议；第二步将每列重新表述为自然语言查询，并提示大语言模型根据论文全文中与该列相关的片段，为每篇论文生成单元格值。
我们在这一两步流程中使用了以下大语言模型作为核心模型：gpt-4.1、o3、gpt-5-mini†、gpt-5†、claude-3-5-haiku、claude-sonnet-4、gemini-2.5-flash-preview-05-20 gemini-2.5-pro以及llama-4-scout。有关详细内容，请参见Singh等人（2025）的研究。

[原文第 43 页的完整图表与公式](assets/original-page-043.jpg)

作为会议论文发表在 ICLR 2026 上

Asta Code是Bogin等人（2024）中基于React风格代码智能体的实现版本，最初是为SUPER-Expert评估而设计的。除了采用标准的ReACT思考-行动-观察-提交循环外，它还内置了文件编辑工具以及自定义的轨迹表示方式，有助于进行精细化的轨迹评估。这包括评估智能体是否到达了某些关键点（即轨迹中的预期点），以衡量其部分成功程度，同时还能让代码智能体在部分填充的黄金轨迹条件下运行。
虽然这些评估功能目前仅适用于 SUPER-Expert，但该求解器允许扩展其他代码任务以进行此类中间评估，并且其抽象结构使得可以实现 ReACT 之外的其他智能体工作流。

Asta DataVoyager 是一个基于角色的多智能体系统，由大语言模型驱动（Majumder等人，2024）。Asta DataVoyager 能够从语义层面理解数据集，利用现有数据进行可验证假设的编程式探索，通过调用预定义函数或生成代码片段来执行基本统计测试（如相关性和回归分析），最后通过详细分析对结果进行解读。该系统的核心组件由专门设计的智能体组成，这些智能体负责管理数据驱动发现过程中的不同环节——规划、编程与代码执行以及数据分析。
此外，为了解读分析过程中生成的图表，在生成阶段我们运行一个多模态生成模型（此处为 gpt-4o），以生成这些图表的自然语言摘要，从而让其他智能体能够将其作为额外上下文来使用。我们采用 AutoGen 框架25，该框架允许智能体根据上下文以任意顺序进行通信，而上下文则由调度智能体维护。有关详细内容，请参见 Majumder 等（2024）的研究。

Asta Panda 通过基于大语言模型的“计划与执行”循环（即“熊猫”模式）进行研究。面对一项研究任务，它首先生成自然语言计划，然后依次系统地执行每个计划步骤，最后撰写关于结果的报告。每个计划步骤都采用 ReAct/CodeAct 风格的循环来执行：先编写 Python 代码，再执行该代码，随后进行反思；如果某个步骤失败或未完成，则重新编码，或者根据结果继续下一步计划步骤。如果失败次数过多，系统会从失败的步骤重新开始计划。由于 Asta Panda 的源代码尚未集成，我们仅对缓存的结果进行评分。

Asta CodeScientist 是一个用于计算实验领域（如机器学习或自然语言处理）的自主科学发现系统（Jansen等，2025）。该系统通过对研究论文与预先指定的代码块组合进行联合遗传搜索，来实现创意构思与实验构建，这些代码块定义了研究领域的常见操作（例如调用语言模型）。由于 Asta CodeScientist 源代码尚未集成，我们仅对缓存的结果进行评分。

Asta v0 是一个调度智能体，能够自动识别任务类型，并将任务分配给相应的特定子智能体。它采用一种简单但有效的文本相似度方法，在验证集上实现了 100% 的路由准确率。一旦确定任务类型后，Asta v0 就会将控制权交给针对该任务类别的专用求解器，该求解器是根据我们的初步实验结果选择出来以取得最佳性能的。完整的路由表可参见附录 F.7。

F.2 基准智能体

对于基础智能体集合，我们提供两种通用智能体类别和 11 种针对科研优化的智能体类别：

ReAct 是一种最小可行基准求解器，用于评估大语言模型的能力，无需引入复杂的大语言模型架构或任务优化的提示词。它是一个简单的 ReAct 循环：一个聊天式大语言模型接收消息历史（最初仅包含其系统提示词（见附录 F.5）和任务实例输入），并获取工具支持后，会生成包含一定推理过程及工具调用信息的输出消息，随后工具调用的结果会被添加到消息历史中。

[原文第 44 页的完整图表与公式](assets/original-page-044.jpg)

作为会议论文发表在 ICLR 2026 上

再次调用大语言模型。这一过程持续进行，直到调用提交（答案）工具为止，此时循环结束并返回最终答案。为了防止无限循环，我们还限制智能体每个任务最多执行 100 步；实际上，智能体在达到此限制之前就会提交答案（大多数模型的执行步数平均不到 12 步）。工具的调用与响应均采用大语言模型的原生工具调用格式编写：即将工具调用 JSON 对象附加到大语言模型输出消息中，以及为响应设置特殊的工具消息类型。智能体将工具调用输出截断为最多 16,384 字节，以避免长输出导致大语言模型出现错误。

Smolagents Coder 是 smolagents 库中的参考 CodeAgent（Roucher等人，2025）。它是一个 ReAct 智能体，与 ReAct 智能体一样，每个步骤的输入都是消息历史记录；不过，Smolagents Coder 的操作以代码形式呈现，而非通过大语言模型的原生工具调用格式。先前的研究表明，基于代码的工具调用在实际应用中的表现优于其他形式（Wang等人，2024），并且它具有理论优势：可以通过引用来操作数值，还能在一步内表示诸如循环之类的逻辑结构，而大语言模型则必须在长序列的调用过程中模拟这些结构。
Smolagents Coder 被要求编写一段 Python 代码块以执行操作（提示词详情请参见附录 F.6）；该代码块在状态化的 Python 环境中运行（见第 4.1 节），且智能体的所有工具均以可调用 Python 函数形式提供。此外，智能体还可以调用 final_answer 函数来提交其最终答案。智能体的下一个输入包括代码块中最终语句的返回值以及任何打印输出，最大长度为 20,000 个字符。

You.com搜索API是一款商业化的网页与新闻搜索API，我们通过它来获取相关响应。

Elicit 是一个商业人工智能研究平台，用于从科学论文中查找、总结并提取见解，例如用于系统评价研究。Elicit 会查询 Semantic Scholar 数据库，并利用所有主要的大语言模型供应商提供的服务，提供人工智能筛选、数据提取及深度研究报告，并包含在线引用。Elicit 于 2025年3月4日决定向 ScholarQA-CS2提交作品，我们则使用离线缓存求解器处理了该作品。

FutureHouse Crow 是一个基于 PaperQA2 构建的通用智能体，能够检索文献并针对问题提供简洁的回答（Skarlinski 等，2024）。它采用 OpenAI 的 gpt-4.1-mini 和 o3-mini 作为核心大语言模型。虽然 PaperQA2 是开源的，但并未包含检索功能。因此，我们通过访问 FutureHouse 的 API 来获取 Crow 的回复。

FutureHouse Falcon 是一款闭源智能体，用于深度文献综述和假设评估，专为长文本问题回答设计。Falcon 还使用 OpenAI 的 gpt-4.1-mini 和 o3-mini 作为核心大语言模型。我们通过 FutureHouse 的 API 获取了 Falcon 的响应。

OpenAI Deep Research 是一个商业级深度研究系统，它利用网络搜索和 OpenAI 的语言模型来解答科学问题。我们通过通过 OpenAI API 向 o3-deep-research 模型提问，从而获取这些报告。

OpenSciLM 是一种基于微调后的开放模型所构建的先前发布的问答系统（Asai等，2024）。它利用 Asta Scientific Corpus 的片段与关键词搜索功能进行检索，并采用自定义的重新排序器；该论文还评估了其 RAG 流程的多种变体，此处我们则评估了公开可用的演示系统，该系统使用基于合成数据训练的开放型8B参数 Llama-3.1 模型作为基础。

Perplexity Sonar Deep Research 是一款基于 Perplexity 专有搜索系统和封闭大语言模型（Sonar）的商业深度研究系统。我们通过 Perplexity 的 API 访问 sonar-deep-research 以获取其回复。28 例如针对 OpenAI 模型：https://platform.openai.com/docs/guides/function-cal ling 29 https://futurehouse.gitbook.io/futurehouse-cookbook/futurehouse-client

[原文第 45 页的完整图表与公式](assets/original-page-045.jpg)

作为会议论文发表在 ICLR 2026 上

SciSpace Deep Review是一款商业系统，它通过多种模型在多个子任务中搜索 Semantic Scholar、AMiner 和 OpenAlex。部分模型经过微调以满足特定任务需求（例如用于相关性重新排序）。SciSpace 于 2025 年 6 月 13 日选择了向 ScholarQA-CS2 提交作品，我们使用缓存求解器处理了该提交内容。在他们的提交中，大语言模型被识别为 claude-sonnet-4-20250514，我们在表 6 中对此进行了报告。

STORM 是来自斯坦福大学的开源系统，它利用 You.com 搜索功能，针对特定主题或问题生成内容全面、类似维基百科的文章（Shao 等，2024）。在系统的各个流程中，STORM 使用 OpenAI 的 GPT-4o 和 GPT-3.5 作为大语言模型的核心组件。

You.com Research API 是一个商业级深度研究系统，运行在 You.com 的搜索及未知大语言模型上。我们通过调用 You.com 的 API 来获取其响应。

Faker是一个基准智能体，用于验证端到端发现任务的评分指标。Faker只是提示大语言模型尽可能完整地撰写报告、代码和成果文件，以模拟一项成功的研究，而实际上并不执行相关工作。

F.3 AS T A PA P E R FI N D E R

Asta PaperFinder智能体（PaperFinder）是Asta项目中的PaperFinder子组件（“PaperFinder产品”）中冻结时间后的子集。AstaBench PaperFinder遵循该产品的整体论文查找流程，但在可使用的索引和API以及可获取的论文集合方面有所不同。其某些配置选项也存在差异，且不会随时间改进。最后，与整个产品不同，它不支持多轮连续交互，仅适用于单轮场景：输入为完整的查询，输出则为排序后的匹配文档集及每篇文档的支撑证据。
PaperFinder 是一个旨在从大量科学文献中查找科学论文的系统，它能够以智能且高效的方式整合多种索引、API、搜索策略以及基于大语言模型的判断功能。它支持三种类型的查询：用于查找用户已知特定论文的导航式查询；基于内容语义描述来定位一组论文的语义式查询；以及基于元数据标准来查找论文的元数据式查询。这些类型并非完全独立，且元数据标准可能会与导航或语义标准产生交集。
它还支持“中心”“近期”或“早期”等修饰词，这些修饰词会根据元数据信息影响结果的排序。PaperFinder智能体作为一个包含手动编码步骤的流程，在多个关键环节涉及大语言模型的决策。从整体来看，查询会进入查询分析器，该工具会将查询转化为一个结构化的对象，从而反映查询的结构与语义。
经过分析的查询（包含语义相关性标准）随后被发送给执行规划器，该规划器会查看分析器的输出，并将其分配到多个子工作流中的某一个，每个子工作流都针对特定类型的搜索任务：导航式搜索、基于语义标准和潜在附加元数据查找一组论文、涉及复杂元数据标准的查询以及基于作者信息的查询。这些工作流的结果分别是一组论文以及关于每篇论文的相关性判断。
这些结果随后会被传输到排序组件中，该组件会根据用户的请求对论文进行排序，同时结合相关性得分以及其他标准如发表时间以及每篇论文的引用数量进行评估，尤其是当这一判断得到查询内容的支持时（例如，明确请求“近期”、“早期”、“经典”、“核心”、“知名”或“鲜为人知”等）。最终得到的排序结果会被返回。PaperFinder智能体则使用 AstaBench 中提供的搜索 API 来实现此功能。

F.3.1 问题分析 查询分析器基于大语言模型，能够提取查询的若干预定义属性。这些提取的属性集合源于对用户提交查询的手动分析，并会随时间逐步完善。我们发现手动编码方法在调用大语言模型的次数、令牌数量以及并行化能力方面更为高效且可靠，相比那种赋予大语言模型更多自主性的动态流程更有优势——后者允许大语言模型编写代码，从而显著影响计算流程和搜索过程。我们计划在后续版本中至少将部分组件转换为更动态的工作流程。

[原文第 46 页的完整图表与公式](assets/original-page-046.jpg)

作为会议论文发表在 ICLR 2026 上

主要覆盖对下游组件（搜索子流程和最终排序器）有用的属性，同时也包含一些目前未处理但我们希望能注意到的信息，以便告知用户某个查询条件不受支持（例如作者归属）。查询分析器通过多个并行运行的短提示实现，每个提示针对不同的小范围属性子集（从1到3个）。我们并不声称这是构建此类组件的最佳方式，但发现这种方法效果良好，且相比提取所有信息片段的长提示而言延迟更低。
查询分析器提取了以下属性：

广泛搜索与定向搜索 查询是针对特定论文（例如论文标题、“the olmo paper”、“the vaswani 2017 paper”）还是符合某些标准的论文集合？这与传统搜索查询中的“定向搜索”与“信息搜索”的区别类似。

语义标准 语义标准是对论文内容或标题的约束或要求（例如：关于X的论文、进行Y的论文）。学术科学文献检索基准中的论文几乎完全围绕这一标准展开。然而，现实中的查询可能包含其他细节，如元数据限制或其他属性，如下所述。查询分析器的主要作用就是将语义标准与其他属性分开，并将其存储在一个独立的字符串中。需要注意的是，语义标准可能非常复杂，包含许多子标准（例如：“关于X、Y和Z且不做W的论文”）。
查询分析器将这些视为一个统一标准，并将其提取为一个单一字段。对子标准的分析则会在后续进行。

相关性标准 筛选器的主要组成部分是判断每个单独候选结果的相关性。查询分析器还将语义查询分解为多个子标准（通过调用大语言模型实现），并附带每个标准的权重分数及简短描述。这些标准将用于评估各个结果的相关性。

元数据约束 简单的元数据字段（年份、时间范围、作者、会议名称、引用次数）在字段层面即可提取。对于复杂的元数据约束（嵌套式、否定式、引用其他论文等），如果存在的话，则会被转化为复杂的数据结构，这超出了本文的研究范围。

明确不支持的元数据约束 这些基于那些在我们的日志中频繁出现的元数据请求，但当前 API 和索引中并未提供相关元数据支持。目前包括作者所属机构信息（“AI2 关于语言建模的论文”）。

时效性与重要性修饰词。与元数据信息相关的常见需求，例如“重要论文”、“经典论文”、“高被引论文”、“近期论文”、“早期研究”等31

F.3.2 导航问题

具体的论文需求通过三种并行运行的策略组合来处理：

1. 语义学者标题 API。

2. 向大语言模型提问，然后利用语义学者标题 API 将答案与特定语料库 ID 关联起来。

3. 从查询中提取关键术语，搜索包含这些术语的句子，在这些句子中寻找引用信息，然后返回被引用最多的条目作为候选项。

这些策略各自会返回零个或多个结果，然后将这些结果合并后返回。

[原文第 47 页的完整图表与公式](assets/original-page-047.jpg)

作为会议论文发表在 ICLR 2026 上

图 9：PaperFinder 语义查询工作流

F.3.3 语义查询 从整体来看，该过程通过一系列检索步骤实现，每个步骤之后都包含基于大语言模型的相关性过滤步骤。每个检索步骤都会扩大前序步骤的覆盖范围，并依据前序步骤中识别出的相关文档进行优化。

初始搜索阶段。第一个检索步骤的输入是用户查询中的语义标准，这些标准由查询分析器提取得到。基于这些标准，大语言模型生成 k 种改写版本，然后将这 k + 1 个查询（改写版本和初始查询）发送到语义搜索接口。接下来，我们通过根据来源论文对返回的片段进行汇总，从片段级别过渡到论文级别。来自同一论文的所有片段会被合并为一项，代表该论文，其中这些片段按照其在论文文本中的出现顺序进行排序。
这种聚合是在查询层面进行的：所有 k + 1 个结果集中所有的片段都参与聚合，因此每个论文项可能包含来自多个来源的匹配内容。被引用的论文。对于某些查询，相当数量的匹配片段指的是其他论文（“Doe 等 2023 年指出……”）。我们提取每个片段中提到的论文集合，并将该片段与该集合中的论文关联起来。因此，每个片段可能参与多个论文项：它来源的论文以及它引用的论文。
某些论文仅包含其中的证据内容，其他论文则仅包含引用论文中的证据，还有一些则包含两者的混合内容。现在我们得到了一组与查询匹配的潜在论文，每篇都包含来自多个来源的证据片段。对于这些论文，我们还添加了论文的标题和摘要。接下来的步骤是相关性判断，通过大语言模型判断来筛选候选论文集（见下文），最终得到包含相关论文及其相关性判断的子集。我们保留与查询最相关的 m 篇有潜力的论文。我们浏览结果的顺序对效率至关重要。
我们将此问题建模为针对不同来源的多臂老虎机问题（每个查询均属于一个来源）。目前忽略了那些与元数据信息无关联的31个形容词，例如“好的论文”、“高质量的论文”、“有趣的论文”、“良好的总结”，不过其中某些形容词（“良好的总结”）在某些情况下可能会被纳入语义标准中。

[原文第 48 页的完整图表与公式](assets/original-page-048.jpg)

作为会议论文发表在 ICLR 2026 上

引用追踪。相关性判断阶段将论文按类别层级进行分组，其中高度相关为完全匹配。在此阶段，会选取前两个类别（高度相关和部分相关），并执行前向和反向引用搜索（该过程在文献中被称为“雪球法”）。在前向雪球法中，我们寻找引用该集合内论文的论文；而在反向雪球法中，则寻找被该集合内论文引用的论文。这些论文随后还将经过相关性判断。

后续查询 我们根据返回的结果提出新的查询。具体做法是选取那些被判定与查询相关、且在嵌入空间中与查询距离最大的论文子集。直观地说，这些就是处于当前搜索查询边界的相关结果。大语言模型会根据论文标题、摘要、返回的片段以及原始查询来重新构建查询。
这些数据随后按照初始搜索步骤进行处理：向基于向量的 API 发出查询，添加被引用的论文，按论文汇总结果，筛选之前步骤中已已知的论文，进行相关性判断，最后返回结果集，再与现有的结果集进行合并。

短路效应 该过程通过多次引用跟踪和后续查询进行迭代，最多持续预定轮数。在过程中，我们会记录被提交至相关性判断的论文数量，以及通过该判断的论文数量。如果找到的高相关性论文数量足够多，或者相关性判断的数量超过预定上限时，该过程就会停止。

相关性判断 相关性判断模块针对每篇被筛选的论文分别进行评估，依据其信息（标题、摘要、提取片段以及其他论文中的引用片段）来判断其相关性。相关性判断提示考虑了查询分析中识别出的各项子标准以及原始查询内容。每个子标准被分为完全相关、部分相关或无关三类。随后将这些分类结果合并，得出一个类别性的相关性判断结果（完全相关、高度相关、部分相关、无关）。

F.3.4 M 元数据查询

在语义查询之上，简单的元数据筛选（如地点、年份）作为结果集后的筛选步骤处理，或作为排序标准（如最新、高被引度）。仅涉及元数据的查询，或同时包含语义标准和复杂元数据标准的查询，首先被发送到专门的元数据检索组件，随后通过相关性判断组件进行语义匹配筛选。元数据组件通过调用大语言模型将元数据分析为结构化的工作计划，再将其传递给手动编码的执行器，后者将其转化为一系列 API 调用。

F.3.5 F 最终排名

最后，我们结合相关性判断与其他标准，基于查询分析，使用一种启发式方法，该方法会考虑引用数量、发表日期以及查询中表达的偏好（如果存在的话）。

F.4 智能体来源 代码 参考

• Asta Paper Finder32 • Asta Table Synthesis33 • Asta Scholar QA34 32 https://github.com/allenai/asta-paper-finder 33 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/arxivdigestables/asta_table_a gent.py@tables_solver 34 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/sqa/sqa.py@sqa_solver

[原文第 49 页的完整图表与公式](assets/original-page-049.jpg)

作为会议论文发表在 ICLR 2026 上

• Asta Code35 • Asta DataVoyager36 • Asta Panda（已缓存）37 • Asta CodeScientist（已缓存）38 • Asta v039 • ReAct40 • Smolagents Coder41 • Elicit（已缓存）42 • Perplexity Sonar Deep Research43 • SciSpace Deep Review（已缓存）44 • OpenSciLM（已缓存）45 • OpenAI Deep Research（已缓存）46 • FutureHouse Crow47 • FutureHouse Falcon48 35 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/code_agent/agent.py@code_agent 36 https://github.com/allenai/agent- baselines/tree/1ce836604c37da38 de2a69614800c20ca6616349/agent_baselines/solvers/datavoyager/agent.p y@datavoyager_solver 37
https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/e2e_discovery/autoasta/autoasta_cached.py@autoasta_cached_solver 38 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/e2e_discovery/codescientist/c odescientist_cached.py@codescientist_cached_solver 39 https://github.com/allenai/agent- baselines/tree/1ce836604c37da 38de2a69614800c20ca6616349/agent_baselines/solvers/asta/v0/asta.py@fewshot_textsim_router 40 https://github.com/allenai/agent- baselines/tree/1ce836604c37da38 de2a69614800c20ca6616349/agent_baselines/solvers/react/basic_agent.py@instantiated_basic_agent
41 https://github.com/allenai/agent- baselines/tree/1ce836604c37da38 de2a69614800c20ca6616349/agent_baselines/solvers/smolagents/agent. py@smolagents_coder 42 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/sqa/elicit/memorized_solver.p y@elicit_solver 43 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a 69614800c20ca6616349/agent_baselines/solvers/sqa/formatted_perplexity. py@formatted_solver 44 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de 2a69614800c20ca6616349/agent_baselines/solvers/sqa/scispace/scispace.p y@formatted_solver 45
https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/sqa/openscholar/memorized_sol ver.py@openscholar_solver 46 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/sqa/general_memorized/memoriz ed_solver.py@formatted_solver 47 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/futurehouse/futurehouse_solver. py@futurehouse_solver 48 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a69 614800c20ca6616349/agent_baselines/solvers/futurehouse/futurehouse_solver. py@futurehouse_solver

[原文第 50 页的完整图表与公式](assets/original-page-050.jpg)

作为会议论文发表在 ICLR 2026 上

• STORM49 • You.com 研究 API50 • You.com 搜索 API51 • Faker52

F.5 R 执行提示词

ReAct智能体使用InspectAI库中的基础智能体系统提示词，该提示词是在不了解AstaBench的情况下构建的。你是一名乐于助人的助手，需要提交正确的答案。你有多种功能可以帮助你找到答案。每条消息可以执行一次函数调用。在发送消息后，你会立即看到函数的执行结果。如果你需要执行多个操作，可以随时通过后续的函数调用发送更多消息。在采取行动之前先进行一些推理，说明你将使用哪些函数调用以及它们如何符合你的计划。

当您完成任务并得到答案后，调用 submit() 函数来报告它。

F.6 S M O L 智能体代码提示词

我们使用默认的 smolagents v1.17.0 系统提示词，并在描述任务时在输入用户消息中添加工具定义（注意需填入工具描述和任务提示的占位符）：

您可以在沙箱环境中使用 astabench 工具。您可以在 Python 代码中调用这些工具：{工具描述}

请记住，您有一个 `final_answer(answer: str)` 函数，必须使用该函数来返回最终答案并标记任务已完成。传递给 `final_answer` 函数的答案应为一个字符串，且需按照任务说明进行格式化；根据任务的不同，该字符串可能包含 JSON 或代码等结构化输出，此外可能还需要执行其他步骤（如编写文件），这些步骤需要在调用 `final_answer` 之后进行。

{task_prompt}

任务提示词仅仅是来自该任务的输入内容。每个可用工具在工具描述中以函数签名的形式呈现，包含工具描述及参数。例如，对于 Asta Scientific Corpus 中的 get_paper 函数，其定义为：get_paper(paper_id: str, fields: str = 'title,abstract,corpusId,authors,year,venue, citation-,→ Count,referenceCount,influentialCitationCount')

通过 ID 获取论文详情。49 https://github.com/allenai/agent- baselines/tree/1ce836604c37da38 de2a69614800c20ca6616349/agent_baselines/solvers/sqa/storm_solver. py@storm_solver 50 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de 2a69614800c20ca6616349/agent_baselines/solvers/sqa/formatted_youcom. py@formatted_solver 51 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de 2a69614800c20ca6616349/agent_baselines/solvers/search/youcom_search. py@youcom_solver 52 https://github.com/allenai/agent-baselines/tree/1ce836604c37da38de2a 69614800c20ca6616349/agent_baselines/solvers/e2e_discovery/faker/faker.p y@faker_solver

[原文第 51 页的完整图表与公式](assets/original-page-051.jpg)

作为会议论文发表在 ICLR 2026 上

参数：paper_id：需要获取的论文编号。支持以下类型的编号：<sha>——Semantic Scholar编号，例如：→ 649def34f8be52c8b66281af98ae884c09aef38b；CorpusId：<id>——Semantic Scholar数字编号，例如：→ CorpusId:215416146；DOI：<doi>——数字对象标识符，例如：→ DOI:10.18653/v1/N18-3011；ARXIV：<id>——arXiv.rg，例如：ARXIV:2106.15928；MAG：<id>——Microsoft Academic Graph，例如：MAG:112218234；ACL：<id>——Association for Computational Linguistics，例如：→ ACL:W12-3903；PMID：<id>——PubMed/Medline，例如：PMID:19872477；PMCID：<id>——PubMed Central，例如：PMCID:2323736；URL：<url>——下方网站中的任意一个的URL，例如：→ URL: https://arxiv.org/abs/2106.15928v1

字段：用于包含在响应中的逗号分隔字符串，例如“url,year,authors”。

默认值为“标题”。可用的字段包括：摘要、作者、→ 引用、研究领域、是否开放获取、期刊、发表日期、参考文献、总结摘要、网址、会议名称、年份。

返回内容：论文对象。

F.7 AS T A V 0 路由表

Asta v0的路由方法首先根据输入数据与验证集示例的（字符级）词汇重叠程度来预测任务类型。这种方法有时会导致具有相同答案格式的高度相似任务产生混淆（例如PaperFindingBench和LitQA2-FullText-Search），但由于我们仍希望将这些任务路由到同一个子智能体上，因此该方法在验证集上实现了100%的路由准确率。一旦确定任务类型后，Asta v0就会将控制权交给针对该任务类别的专用求解器，该求解器是根据我们的初步实验选择出来、预期性能最佳的。53

• 论文搜索任务（PaperFindingBench、LitQA2-FullText-Search）→ Asta Paper Finder
• 长文本问答任务（ScholarQA-CS2）→ Asta Scholar QA（含表格功能），使用 Claude-sonnet-4
• 表格生成任务（ArxivDIGESTables-Clean）→ Asta Table Synthesis，使用 o3
• 数据分析任务（DiscoveryBench）→ Asta DataVoyager，配置为 o3
• 代码仓库复现任务（SUPER-Expert）→ Asta Code，使用 gpt-4.1
• 端到端发现任务（E2E-Bench、E2E-Bench-Hard）→ Asta Panda，使用 Claude-sonnet-4
• 其他任务（DS-1000、CORE-Bench-Hard−、LitQA2-FullText）→ ReAct，使用 o3

调度器实现了一种备用机制，以便让子智能体能够选择退出：如果预测的任务类型对应的子智能体没有产生输出，Asta v0 会尝试使用下一个最相似的任务类型进行重试（最多可尝试 3 次）。

53 我们的 Asta v0 实验是在 GPT-5 发布之前进行的。由于时间限制以及 GPT-5 在许多专业求解器上的表现相对不佳，我们并未针对该工作评估 GPT-5 版本。我们还注意到，尽管最终结果显示使用 o3 的 ReAct 技术在 SUPER-Expert 性能方面优于较旧模型，但 Asta Code 仍是基于早期对较旧模型的实验而选定的。

[原文第 52 页的完整图表与公式](assets/original-page-052.jpg)

作为会议论文发表在 ICLR 2026 上

F.8 智能体对文献理解能力的验证

某些科学问答智能体无法生成符合特定架构的结构化数据。因此，我们采用这些问答智能体的纯文本输出，并通过“格式化”步骤进行处理。该格式化步骤利用大语言模型（gemini-2.5-flash）将纯文本报告拆分为多个部分，识别其中的引用内容，从而生成符合我们的SQAResponse架构的结构化输出。还有一些智能体看似具备结构化输出能力，但启用该功能后输出质量会大幅下降。针对这些智能体同样使用格式化步骤进行处理。
我们使用格式化步骤处理的智能体列表包括：You.com、Perplexity DR、OpenAI DR 以及 FuturHouse Crow 和 Falcon。对于 Asta Paper Finder 这一扩展且持续开发的智能体版本——包含用户界面及额外基础设施——正被越来越多的用户使用。在漫长的开发与实际应用过程中，我们利用内部评估集反复验证了该智能体（该评估集是现在我们发布的基准测试的超集，还包含了一些更简单的回归测试查询）。
虽然这一内部数据集并非经过验证的基准测试，但事实证明它有助于监控检索质量，并检测召回率或排序性能中的任何下降。用户对它的日益广泛使用进一步证明了智能体的有效性以及我们内部评估方法的准确性。就 LitQA2-FullText 而言，由于该任务属于选择题问答形式，我们会对 Future-House（原始 LitQA 数据集的创建者）智能体，以及 You.com 和 Perplexity DR 进行评估，原因是它们具备 API 接口可用性，且非常适合短格式问答任务。
该系统仅能以正确的选项或包含正确选项的简短描述形式以 JSON 格式进行回应，即可被视为有效。对于少量样本，我们通过向它们的用户界面聊天界面发送相同的输入提示，确保基线系统能够以要求的格式作出响应。由于 LitQA2-FullText 是原始模型的子集，因此与 (Skarlinski 等，2024) 中的结果直接对比较为困难。此外，当时 PaperQA2 使用 gpt-4-turbo 作为核心大语言模型，而基于 PaperQA2 的 FutureHouse Crow 则使用 gpt-4.1-mini。
为了确保合理性，我们对比了 PaperQA2（66.0）和 FutureHouse Crow（72.0）所报告的平均准确率结果，得出结论：使用更少的问题数量以及更先进的模型进行评估能够解释这一差异。对于 Asta Table Synthesis 项目，我们预计我们的新端到端评估指标得分大致与 Newman 等人（2024年）的报告结果处于同一水平。对于 Perplexity Sonar Deep Research 项目，我们设置了“reasoning_effort=high”和“search_context_- size=high”，以最大化模型的计算资源，从而使其在我们的数据集上获得最佳性能。
Perplexity API 还提供“search_mode”参数，可设置为“academic”以仅检索学术资料。然而在系统运行期间（2025年8月3日–7日），该功能完全禁用了网络搜索，因此我们没有设置此参数。最后，虽然我们认为可以提示 Perplexity Sonar Deep Research 从其引用的每个来源中提取引文，但该 API 并未明确返回这些片段内容；因此，我们按仅评估页面标题和 URL 的方式对模型进行评价。

F.9 最终端发现智能体的验证

为了对智能体在端到端任务中的表现进行评分与验证，E2E评分器针对每项任务使用特定的评分标准，其中列出了有效结果所需的关键要素（例如：下载正确的数据集、选择正确的基准模型等）。这些评分标准由人工注释者手动审核（并在必要时进行更新）。为了应用这些评分标准，评分器利用大语言模型作为评判工具，对智能体生成的三种类型的成果分别进行评分：生成的报告、生成的代码以及产生的成果（如数据集）。评分结果可轻松在生成的HTML页面中查看（图10）。
每个方面均根据“符合标准”（绿色）、 “不符合标准”（红色）和“无明确证据”（黄色）进行评分。只有当所有三个方面均一致且包含“符合”时，整体标准才被视为满足要求。这种三维度评估方法显著增强了评分的可靠性，尤其有助于避免误报（FP），例如报告说明进行了实验，但代码却显示并非如此；同时也有助于应对误判（FN），例如论文未提及某项标准，但代码表明该标准确实已被实现，详见表21。评分标准通过随机抽查及人工验证进行了验证，在50项评分标准项的发展集样本上，人工判断的准确率达到了92%。
失败情况包括偶尔的过度乐观评分（例如，论文仅模糊地提及了某个评分标准项，但依然

[原文第 53 页的完整图表与公式](assets/original-page-053.jpg)

作为会议论文发表在 ICLR 2026 上

图10：对单个端到端答案进行评分的图形展示。每一行代表一个不同的评分标准项，第3、4和5列分别显示生成的论文、代码和成果是否符合该评分标准项（绿色）、不符合（红色）或未知（黄色）。第6列表示3-5项是否一致（绿色）或不一致（红色），最后第7列为整体评价。总体得分是最后一列各单元格的平均值（绿色计1分，红色计0分）。

**表格与文字对照**

```text
Facets
Paper Code Artifacts
TP: Meets criterion, and met elsewhere (overall score: 1) 0.44 0.32 0.48
FP*: Meets criterion, but failed elsewhere (overall score: 0) 0.16 0.03 0.03
FN*: No evidence either way, but met elsewhere (overall score: 1) 0.03 0.16 0.00
TN: No evidence either way, and failed elsewhere (overall score: 0) 0.02 0.24 0.01
TN: Fails criterion (overall score 0) 0.35 0.26 0.48

表内文字对照（数值与原始行列保持不变）：
Facets → 不同层面
Paper Code Artifacts → 论文代码产物
Meets criterion → 符合标准
and met elsewhere (overall score → 并在其他地方出现（总得分）
but failed elsewhere (overall score → 但在其他方面失败了（总体得分）
No evidence either way → 没有任何证据支持这两种观点
but met elsewhere (overall score → 但曾在其他地方出现（总体得分）
and failed elsewhere (overall score → 并在其他领域表现不佳（总体得分）
Fails criterion (overall score → 失败标准（总体得分）
```

表21：三个维度如何结合（比例）以对端到端评分标准进行评分，特别是如何纠正基于单一维度属于假阳性（FP*）或假阴性（FN*）的项目。例如，在16%的回答中，生成的文档表明某个评分标准得到满足，但代码和/或成果却表明实际上并未满足，从而使该标准的总体得分为0，纠正了仅依赖文档所可能产生的假阳性情况。

得分为1，或细节方面存在缺陷（例如，所需的代码已实现，得分为1，但实现过程中遗漏了实验的重要概念细节）。

## 额外的实验细节与结果

G.1 实验设计

表22列出了我们在实验中使用的模型列表。

G.2 E 在完整的 LIT QA2 数据集上的评估

本部分提供了关于在 LitQA2 数据集上进行评估的更多细节。在针对我们自开发的文献搜索智能体（PaperFinder）进行评估时，我们直接将其提供问题文本，不包含选择题，也不试图将问题转化为文献查找查询格式。对于该任务，我们没有对 PaperFinder 进行任何特定任务的修改或调整。

[原文第 54 页的完整图表与公式](assets/original-page-054.jpg)

作为会议论文发表在 ICLR 2026 上

表 22：我们研究中运行的模型。模型名称与 API 调用中使用的模型标识符对应，为了完全透明，对于未提供日期标识符的模型，使用 ‡ 进行区分。

**表格与文字对照**

```text
Name Model ID Organization Open-Weight Inference Provider
gpt-3.5-turbo gpt-3.5-turbo- OpenAI × OpenAI
0125
gpt-4o-mini gpt-4o-mini OpenAI × OpenAI
gpt-4o gpt-4o-2024-08-06 OpenAI × OpenAI
gpt-4o† gpt-4o OpenAI × OpenAI
gpt-4.1 gpt-4.1-2025-04- OpenAI × OpenAI
14
gpt-4.1† gpt-4.1 OpenAI × OpenAI
gpt-4.1-mini gpt-4.1-mini OpenAI × OpenAI
gpt-5-mini gpt-5-mini-2025- OpenAI × OpenAI
08-07
gpt-5-mini† gpt-5-mini OpenAI × OpenAI
gpt-5 gpt-5-2025-08-07 OpenAI × OpenAI
gpt-5† gpt-5 OpenAI × OpenAI
o3-mini o3-mini OpenAI × OpenAI
o3 o3-2025-04-16 OpenAI × OpenAI
o3† o3 OpenAI × OpenAI
claude-3-5-haiku claude-3-5-haiku- Anthropic × Anthropic
20241022
claude-3-7-sonnet claude-3-7-sonnet- Anthropic × Anthropic
20250219
claude-sonnet-4 claude-sonnet-4- Anthropic × Anthropic
20250514
gemini-2-flash gemini-2.0-flash Google × Google Vertex AI
gemini-2.5-flash gemini-2.5-flash- Google × Google Vertex AI
preview-05-20
gemini-2.5-flash† gemini-2.5-flash Google × Google Vertex AI
gemini-2.5-pro gemini-2.5-pro Google × Google Vertex AI
sonar-deep- sonar-deep- Perplexity × Perplexity
research research
llama-4-scout Llama-4-Scout-17B- Meta ✓ Together AI
16E-Instruct
llama-3.1- llama-3.1- Meta / ✓ Self-hosted
openscholar-8b openscholar-8b Allen AI

表内文字对照（数值与原始行列保持不变）：
Name Model ID Organization Open-Weight Inference Provider → 名称 模型ID 机构 开放权重推理提供方
gpt- → gpt-
turbo gpt- → 涡轮 GPT-
turbo- OpenAI → Turbo - OpenAI
OpenAI → OpenAI
o-mini gpt- → o-mini GPT-
o-mini OpenAI → o-mini OpenAI
o gpt- → o gpt-
o OpenAI → o OpenAI
mini gpt- → 迷你 GPT-
mini OpenAI → 迷你 OpenAI
mini- → 迷你-
mini → 迷你
mini o → 迷你 O
claude- → claude-
haiku claude- → 俳句 Claude-
haiku- Anthropic → 俳句 - Anthropic
Anthropic → Anthropic
sonnet claude- → 十四行诗 Claude-
sonnet- Anthropic → sonnet- Anthropic
claude-sonnet- → claude-sonnet-
gemini- → Gemini-
flash gemini- → 闪现 Gemini-
flash Google → 闪现 Google
Google Vertex AI → Google Vertex AI
flash- Google → flash- Google
preview- → 预览版
flash → 闪存
pro gemini- → pro Gemini-
pro Google → 与谷歌合作
sonar-deep- sonar-deep- Perplexity → sonar-deep- sonar-deep- Perplexity
Perplexity → 困惑度
research research → 研究 研究
llama- → llama-
scout Llama- → scout Llama-
Scout- → Scout-
B- Meta → B- Meta
Together AI → Together AI
E-Instruct → E-Instruct
Meta / → Meta /
Self-hosted → 自托管
openscholar- → 开放学者
b openscholar- → b openscholar-
b Allen AI → b Allen AI
```

[原文第 55 页的完整图表与公式](assets/original-page-055.jpg)

作为会议论文发表在 ICLR 2026 上

由于 LitQA2被设计为全文本搜索基准测试，我们的主要结果针对的是 LitQA2-FullText-Search子集，该子集中的语料库包含所有论文的全文本。此外，我们还报告了 Skarlinski等人（2024）原始 LitQA2数据集的结果：在199个查询中，有114个仅包含摘要而非全文本，这些摘要被纳入我们的搜索索引中。表23中的结果显示，尽管 PaperFinder智能体只能获取超过一半论文的摘要，但它获得的结果与Skarlinski等人（2024）的智能体非常相似，且在包含全文本的子集中得分明显更高。

表23：LitQA2数据集全集的检索得分

**表格与文字对照**

```text
Name original-set portion full-text recall recall
percentage @30
PaperQA2 (Skarlinski et al. (2024)) full (199) 100% 69.9 62.8
PaperFinder (ours) full (199) <50% 70.3 64.3
PaperFinder (ours) LitQA2-FullText- 100% 93.3 90.7
Search Test (75)
PaperFinder (ours) LitQA2-FullText- 100% 80 80
Search Val (10)

表内文字对照（数值与原始行列保持不变）：
Name original-set portion full-text recall recall → 名称 原始集合部分 全文检索 检索
percentage → 百分比
PaperQA → PaperQA
Skarlinski et al → Skarlinski 等
full ( → 完整的（
PaperFinder (ours) full ( → 我们的 PaperFinder 全功能版本
PaperFinder (ours) LitQA → PaperFinder（ ours）LitQA
FullText- → FullText-
Search Test ( → 搜索测试（
Search Val ( → 搜索 Val（
```

评估任务示例与评分标准十分清晰且富有启发性，本节通过示例问题及评分标准，以及详细的提示词，为评估任务提供了更细致的说明。

H.1 PA P E RFI N D I N GBE N C H

H.1.1 示例问题 请查找与以下查询相关的论文：能否建议一些研究，→ 探讨在Transformer模型中基于聚类的高效注意力机制？在搜索时力求全面且高效准确，即，→ 尽可能找到大量高度相关的论文，同时注重效率。您最多可提交250篇论文。如果查询要求提供用户已知的特定论文，例如“Transformer相关论文”、“BERT相关论文”、“GPT-3相关论文”等，请尝试找到该特定论文并仅返回该论文。
这并不适用于任何以单数形式表述的“论文”或“文章”查询——这些查询可能是泛化的，应当返回多篇相关论文，例如“哪篇论文提出了一种基于变换器的生成模型用于文本生成”。

请将您的答案以 JSON 格式返回，结构如下，结果按相关性从高到低排序： ```json { "output": { "results": [ { "paper_id": "字符串；语义学者论文的 corpus_id", "markdown_evidence": "字符串；包含该论文原文内容的 Markdown 格式片段，→ 用于证明该论文与查询相关的性；该证据应简洁且仅包含支持论文相关性的必要内容" },... ] } } }

[原文第 56 页的完整图表与公式](assets/original-page-056.jpg)

作为会议论文发表在 ICLR 2026 上

**代码（保留原文）**

```text
~~~
```

H.2 L I T QA2-F U L L T E X T -S E A R C H

H.2.1 示例问题 请查找与以下查询相关的论文：活性嗅觉受体，→ 基因在小鼠嗅觉神经元中与希腊岛屿区域之间的接触程度增加了多少，→ 由什么因素导致？在搜索时力求全面且高效准确，即→ 尽可能找到大量高度相关的论文，同时注意→ 效率。您最多可提交 250 篇论文。如果查询要求提供用户已知的特定论文，例如“→ Transformer 论文”、“→ BERT 论文”、“→ GPT-3 论文”等，请尝试→ 找到该特定论文并仅返回该论文。
这并不适用于任何以单数形式表述的“论文”或“文章”查询——这些查询可能是泛化的，应当返回多篇相关论文，例如“哪篇论文提出了一种基于变换器的生成模型用于文本生成”。

请将您的答案以 JSON 格式返回，结构如下，结果按相关性从高到低排序： ```json { "output": { "results": [ { "paper_id": "字符串；语义学者论文的 corpus_id", "markdown_evidence": "字符串；包含该论文原文内容的 Markdown 格式片段，→ 用于证明该论文与查询相关的性；该证据应简洁且仅包含支持论文相关性的必要内容" },... ] } } ```

H.3 S C H O L A R QA-CS2

H.3.1 示例问题 生成一份报告，回答以下研究问题。务必在每一条陈述中添加内嵌引用。以有效的 JSON 格式返回结果，其中包含一个名为 `sections` 的键，该键值为一个章节列表，每个章节包含 `title`、`text` 和 `citations` 三个键。`citations` 中的每个条目应包含一个从参考文档中提取的 `snippets` 的 JSON 列表以及一个 `id`，且这些 `id` 必须完全出现在文本中。每个 `id` 应为文本中的内嵌引用（如适当时可使用括号或方括号包裹）。如果有可用的标题，则每个引用都应包含 `title`。
任何关于引文的额外信息都应放在 `metadata` 下。不要创建“参考文献”部分。

这是一个 `section` 示例，有助于您进行格式设置：

{ "title": "背景", "text": "卷积神经网络（CNNs）在图像分类领域取得了→最先进的结果 [1][2]。", "citations": [ {

[原文第 57 页的完整图表与公式](assets/original-page-057.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
"id": "[1]",
"snippets": [
"CNNs have become the standard for many visual tasks."
],
"title": "ImageNet Classification with Deep Convolutional
,→ Neural Networks",
"metadata": {
"authors": "Krizhevsky, A. et al.",
"year": 2012,
"arxiv": "1207.0580"
}
},
{
"id": "[2]",
"snippets": [
"Significant improvements in image recognition have been
,→ observed with CNNs."
],
"title": "Very Deep Convolutional Networks for Large-Scale
,→ Image Recognition",
"metadata": {
"authors": "Simonyan, K. & Zisserman, A.",
"year": 2014,
"arxiv": "1409.1556"
}
}
]
}

表内文字对照（数值与原始行列保持不变）：
snippets → 片段
CNNs have become the standard for many visual tasks → CNNs已成为许多视觉任务的标准方法
title → 标题
ImageNet Classification with Deep Convolutional → 使用深度卷积的 ImageNet 分类
Neural Networks → 神经网络
metadata → 元数据
authors → 作者们
Krizhevsky → Krizhevsky
et al → 等
year → 年份
arxiv → arxiv
Significant improvements in image recognition have been → 图像识别能力有了显著提升
observed with CNNs → 使用 CNN 进行观察
Very Deep Convolutional Networks for Large-Scale → 用于大规模应用的极深度卷积网络
Image Recognition → 图像识别
Simonyan → 西蒙尼扬
Zisserman → Zisserman
```

问题：除了防止过拟合之外，在深度神经网络中应用dropout还有哪些副作用（无论是否理想）？

**表格与文字对照**

```text
H.3.2 E XAMPLE RUBRIC
{
"question": "how the AI hallucination is linked to the AI bias",
"ingredients": [
{
"name": "answer_critical_0",
"criterion": "Define AI hallucination and AI bias",
"weight": 0.14285714285714285,
"examples": [
"factually incorrect, nonsensical, or misleading outputs
,→ despite appearing confident in their responses",
"when an LLM generates content that does not correspond to
,→ reality, producing outputs that are coherent and
,→ grammatically correct but factually incorrect or
,→ nonsensical",
"AI systems generate outputs that are misleading, biased, or
,→ entirely fabricated, despite appearing convincingly real",
"systematic errors or skewed outputs stemming from imbalances
,→ in training data, model architecture, or deployment
,→ context",
"an inclination or prejudice for or against a person or group,
,→ especially in a way considered unfair",
"prejudiced or unfair outcomes due to skewed training data or
,→ flawed algorithmic design"
]
},
{
"name": "answer_critical_1",
"criterion": "Explain shared root causes linking hallucination
,→ and bias, particularly training data issues",
"weight": 0.14285714285714285,
"examples": [

表内文字对照（数值与原始行列保持不变）：
E XAMPLE RUBRIC → 示例评分标准
question → 问题
how the AI hallucination is linked to the AI bias → 大语言模型幻觉现象如何与人工智能偏见相关联
ingredients → 成分
name → 名称
answer_critical_ → 回答关键问题
criterion → 标准
Define AI hallucination and AI bias → 定义人工智能幻觉与人工智能偏见
weight → 权重
examples → 示例
factually incorrect → 事实错误
nonsensical → 毫无意义
or misleading outputs → 或具有误导性的输出
despite appearing confident in their responses → 尽管他们看起来对自己的回答充满信心
when an LLM generates content that does not correspond to → 当大语言模型生成的内容与实际情况不符时
reality → 现实
producing outputs that are coherent and → 生成连贯且合理的输出
grammatically correct but factually incorrect or → 语法正确但事实错误
AI systems generate outputs that are misleading → 人工智能系统生成的输出具有误导性
biased → 偏见
entirely fabricated → 完全编造的
despite appearing convincingly real → 尽管看起来非常真实
systematic errors or skewed outputs stemming from imbalances → 由不平衡导致的系统性错误或偏差性输出
in training data → 在训练数据中
model architecture → 模型架构
or deployment → 或部署
context → 上下文
an inclination or prejudice for or against a person or group → 对某人或某个群体的支持或反对倾向
especially in a way considered unfair → 尤其是以被认为不公平的方式
prejudiced or unfair outcomes due to skewed training data or → 由于训练数据偏差导致的偏见或不公平结果
flawed algorithmic design → 有缺陷的算法设计
Explain shared root causes linking hallucination → 解释导致幻觉的共同根源
and bias → 以及偏见
particularly training data issues → 尤其是训练数据问题
```

[原文第 58 页的完整图表与公式](assets/original-page-058.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
"biased training data",
"Both originate from the inherent reliance on statistical
,→ pattern matching over true semantic understanding",
"Incomplete or biased data can lead to AI models learning
,→ incorrect patterns, resulting in hallucinations",
"Data-related hallucinations generally emerge as a byproduct of
,→ biases, misinformation, and knowledge gaps, which are
,→ fundamentally rooted in the training data",
"If the training data is biased, incomplete, or flawed, the AI
,→ model may learn incorrect patterns, leading to inaccurate
,→ predictions and hallucinations",
"Both phenomena emerge from datasets that are either incomplete,
,→ noisy, or imbalanced"
]
},
{
"name": "answer_critical_2",
"criterion": "Explain how bias directly contributes to
,→ hallucination",
"weight": 0.14285714285714285,
"examples": [
"biases manifest themselves as hallucinations in summarization
,→ tasks, leading to factually incorrect summaries",
"correlation coefficients reaching 0.81-0.83 between intrinsic
,→ bias and extrinsic hallucination rates",
"Language models may generate stereotypical or harmful content
,→ about marginalized groups when trained on internet text
,→ containing systemic biases",
"bias in medical training data leads to models generating
,→ plausible but incorrect medical information",
"If an AI model is trained on data that underrepresents certain
,→ groups or overrepresents particular viewpoints, it may
,→ generate hallucinatory content that reflects these
,→ imbalances",
"a language model might assume a nurse is female without any
,→ gender cue, hallucinating that detail based on gender-role
,→ stereotype"
]
},
{
"name": "answer_critical_3",
"criterion": "Explain how hallucination propagates and amplifies
,→ bias",
"weight": 0.14285714285714285,
"examples": [
"When an AI model hallucinates, the nonsensical or incorrect
,→ information it generates may inadvertently reveal the
,→ prejudiced assumptions it has learned from biased data",
"The very act of hallucination, being a deviation from factual
,→ grounding, can sometimes be a manifestation of the system's
,→ internal biases, where the 'made-up' information aligns
,→ with these learned prejudices",
"Confidence in Flawed Outputs: Hallucinations presented
,→ confidently by AI can reinforce existing biases",
"Data Pollution: Biased or hallucinated outputs fed back into
,→ training data create self-reinforcing cycles of inaccuracy
,→ and prejudice",
"When AI systems hallucinate, they often draw upon learned
,→ patterns and associations from their training data that
,→ include societal biases",
"AI hallucinations can amplify existing biases in the data,
,→ leading to discriminatory outcomes"
]
},
{

表内文字对照（数值与原始行列保持不变）：
biased training data → 有偏训练数据
Both originate from the inherent reliance on statistical → 两者都源于对统计数据的依赖
pattern matching over true semantic understanding → 基于真实语义理解的模式匹配
Incomplete or biased data can lead to AI models learning → 不完整或有偏的数据可能导致人工智能模型学习
incorrect patterns → 错误的模式
resulting in hallucinations → 导致幻觉的产生
Data-related hallucinations generally emerge as a byproduct of → 与数据相关的幻觉通常作为某种副产物出现
biases → 偏差
misinformation → 虚假信息
and knowledge gaps → 以及知识缺口
which are → 哪些
fundamentally rooted in the training data → 从根本上源于训练数据
If the training data is biased → 如果训练数据存在偏见
incomplete → 不完整的
or flawed → 或存在缺陷
the AI → 该人工智能
model may learn incorrect patterns → 该模型可能会学习到错误的模式
leading to inaccurate → 导致不准确的结果
predictions and hallucinations → 预测与幻觉
Both phenomena emerge from datasets that are either incomplete → 这两种现象都源自不完整的数据集
noisy → 嘈杂的
or imbalanced → 或不平衡
name → 名称
answer_critical_ → 回答关键问题
criterion → 标准
Explain how bias directly contributes to → 解释偏见如何直接导致
hallucination → 幻觉
weight → 权重
examples → 示例
biases manifest themselves as hallucinations in summarization → 偏差会在摘要过程中表现为幻觉
tasks → 任务
leading to factually incorrect summaries → 导致事实错误的摘要
correlation coefficients reaching → 相关系数达到
between intrinsic → 在内在之间
bias and extrinsic hallucination rates → 偏见与外部幻觉率
Language models may generate stereotypical or harmful content → 大语言模型可能会生成刻板或有害内容
about marginalized groups when trained on internet text → 在基于互联网文本进行训练时关于边缘化群体的研究
containing systemic biases → 包含系统性偏见
bias in medical training data leads to models generating → 医疗训练数据中的偏见导致模型产生错误输出
plausible but incorrect medical information → 看似合理但错误的医疗信息
If an AI model is trained on data that underrepresents certain → 如果人工智能模型所训练的数据中某些类别的占比不足
groups or overrepresents particular viewpoints → 分组或过度体现特定观点
it may → 它可能会
generate hallucinatory content that reflects these → 生成反映这些内容的幻觉性内容
imbalances → 不平衡
a language model might assume a nurse is female without any → 一种语言模型可能会认为护士是女性，而无需任何额外信息
gender cue → 性别提示
hallucinating that detail based on gender-role → 根据性别角色产生相关细节的幻觉
stereotype → 刻板印象
Explain how hallucination propagates and amplifies → 解释幻觉是如何传播和放大的
bias → 偏见
When an AI model hallucinates → 当人工智能模型产生幻觉时
the nonsensical or incorrect → 无意义的或错误的
information it generates may inadvertently reveal the → 它生成的信息可能会无意中泄露相关内容
prejudiced assumptions it has learned from biased data → 它从有偏数据中学到的偏见性假设
The very act of hallucination → 幻觉产生的行为本身
being a deviation from factual → 属于对事实的偏离
grounding → 定位
can sometimes be a manifestation of the system → 有时可能成为系统的表现形式
internal biases → 内部偏见
where the → 其中
made-up → 虚构的
information aligns → 信息保持一致
with these learned prejudices → 基于这些习得的偏见
Confidence in Flawed Outputs → 对错误输出的信心
Hallucinations presented → 幻觉现象出现
confidently by AI can reinforce existing biases → AI能够自信地强化现有偏见
Data Pollution → 数据污染
Biased or hallucinated outputs fed back into → 带有偏差或幻觉的输出被反馈回去
training data create self-reinforcing cycles of inaccuracy → 训练数据会形成自我强化的错误循环
and prejudice → 以及偏见
When AI systems hallucinate → 当人工智能系统产生幻觉时
they often draw upon learned → 它们经常依赖已学习的知识
patterns and associations from their training data that → 来自其训练数据的模式与关联
include societal biases → 包含社会偏见
AI hallucinations can amplify existing biases in the data → AI 幻觉会放大数据中存在的偏见
leading to discriminatory outcomes → 导致歧视性结果
```

[原文第 59 页的完整图表与公式](assets/original-page-059.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
"name": "answer_critical_4",
"criterion": "Describe the interconnected and bidirectional
,→ nature of the relationship",
"weight": 0.14285714285714285,
"examples": [
"they represent different manifestations of fundamental
,→ limitations in current AI systems",
"addressing one without the other provides incomplete
,→ solutions",
"both stem from systemic issues in data quality, model
,→ architecture, and training processes",
"AI bias manifests as hallucinations when models are trained on
,→ unrepresentative or imbalanced data and combined with
,→ specific architectural designs"
]
},
{
"name": "valuable_0",
"criterion": "Provide real-world examples demonstrating the
,→ link",
"weight": 0.07142857142857142,
"examples": [
"Healthcare Diagnostics: AI systems hallucinated symptoms for
,→ Black patients 34% more often than for white patients,
,→ correlating with underrepresentation in training data",
"Recruitment Tools: Amazon's scrapped hiring algorithm
,→ downgraded resumes containing the word 'women's' while
,→ inventing irrelevant skill requirements for male
,→ candidates",
"Mata v. Avianca legal case where ChatGPT produced nonexistent
,→ legal opinions",
"ChatGPT's 'Inner Racist' Incident where the model hallucinated
,→ a hateful rant laced with stereotypes",
"In healthcare: factual hallucinations leading to logical
,→ hallucinations and diagnostic errors that can jeopardize
,→ patient safety"
]
},
{
"name": "valuable_1",
"criterion": "Discuss mitigation strategies that address both
,→ issues",
"weight": 0.07142857142857142,
"examples": [
"data preprocessing, algorithm selection, and model
,→ evaluation",
"Training AI models on large, diverse, and high-quality
,→ datasets",
"The research community is increasingly advocating for
,→ integrated evaluation frameworks that simultaneously assess
,→ factual accuracy and fairness",
"Data deduplication, improved data curation, and augmentation
,→ to reduce memorization artifacts and balance
,→ representation",
"External fact-checking layers and retrieval-augmented
,→ generation (RAG) frameworks"
]
},
{
"name": "valuable_2",
"criterion": "Explain specific mechanisms connecting bias and
,→ hallucination",
"weight": 0.07142857142857142,
"examples": [

表内文字对照（数值与原始行列保持不变）：
name → 名称
answer_critical_ → 回答关键问题
criterion → 标准
Describe the interconnected and bidirectional → 描述其相互连接且双向的特性
nature of the relationship → 关系性质
weight → 权重
examples → 示例
they represent different manifestations of fundamental → 它们代表了基本概念的不同表现形式
limitations in current AI systems → 当前人工智能系统的局限性
addressing one without the other provides incomplete → 同时具备两者缺一不可，结果却不完整
solutions → 解决方案
both stem from systemic issues in data quality → 两者都源于数据质量的系统性问题
model → 模型
architecture → 架构
and training processes → 以及训练过程
AI bias manifests as hallucinations when models are trained on → 当模型在基于数据训练时，AI偏见会表现为幻觉现象
unrepresentative or imbalanced data and combined with → 非代表性或不平衡的数据，以及结合使用
specific architectural designs → 特定的架构设计
valuable_ → 有价值的
Provide real-world examples demonstrating the → 提供展示该功能的实际案例
link → 链接
Healthcare Diagnostics → 医疗诊断
AI systems hallucinated symptoms for → 人工智能系统虚构了症状
Black patients → 黑人患者
more often than for white patients → 比白人患者更频繁
correlating with underrepresentation in training data → 与训练数据中代表性不足现象相关联
Recruitment Tools → 招聘工具
Amazon → 亚马逊
s scrapped hiring algorithm → 被废弃的招聘算法
downgraded resumes containing the word → 包含该词的降级简历
women → 女性
while → 同时
inventing irrelevant skill requirements for male → 为男性编造无关的技能要求
candidates → 候选人
Mata v → Mata v
Avianca legal case where ChatGPT produced nonexistent → 阿维安卡航空法律案件中 ChatGPT 生成了不存在的内容
legal opinions → 法律意见
ChatGPT → ChatGPT
Inner Racist → 内部种族主义
Incident where the model hallucinated → 模型产生幻觉的事件
a hateful rant laced with stereotypes → 充满刻板印象的恶意谩骂
In healthcare → 在医疗保健领域
factual hallucinations leading to logical → 事实性幻觉导致逻辑错误
hallucinations and diagnostic errors that can jeopardize → 可能危及的幻觉与诊断错误
patient safety → 患者安全
Discuss mitigation strategies that address both → 讨论同时解决两种问题的缓解策略
issues → 问题
data preprocessing → 数据预处理
algorithm selection → 算法选择
and model → 和模型
evaluation → 评估
Training AI models on large → 在大语言模型上训练人工智能模型
diverse → 多样化的
and high-quality → 以及高质量
datasets → 数据集
The research community is increasingly advocating for → 研究界越来越倡导
integrated evaluation frameworks that simultaneously assess → 同时评估的集成评估框架
factual accuracy and fairness → 事实准确性与公平性
Data deduplication → 数据去重
improved data curation → 改进的数据整理
and augmentation → 以及增强
to reduce memorization artifacts and balance → 减少记忆痕迹并平衡
representation → 表示方式
External fact-checking layers and retrieval-augmented → 外部事实核查层与检索增强
generation (RAG) frameworks → 生成（RAG）框架
Explain specific mechanisms connecting bias and → 解释导致偏见的具体机制
hallucination → 幻觉
```

[原文第 60 页的完整图表与公式](assets/original-page-060.jpg)

作为会议论文发表在 ICLR 2026 上

“大语言模型在物体幻觉问题上面临挑战，原因在于它们过度依赖文本提示和习得的物体共现偏见”， “RLHF 容易受到人类标注者判断中固有偏见的影响”， “视觉语言模型中的物体幻觉源于与统计偏见密切相关的过度自信问题”， “模型依赖于令牌概率和习得的相关性，而非对底层知识的真正理解”， “当习得的概率分布存在偏见、不完整或过于泛化时，模型产生的输出虽然在统计上可能成立，但在事实上却错误或带有偏见”， “现代生成模型的工作方式类似于高级系统”
自动补全功能，→ 侧重于生成听起来合理的后续内容] }, { "name": "valuable_3", "criterion": "讨论对高风险领域的意义", "weight": 0.07142857142857142, "examples": [ "可能在医疗、金融和安全等关键领域导致错误的决策", "医疗领域：医疗人工智能可能会产生错误的治疗建议，同时反映针对特定群体的偏见", "法律领域：法律人工智能系统可能会伪造案例先例，从而延续系统性偏见", "医疗应用领域中，这两种现象都可能导致误诊和不适当的治疗建议", "法律和司法环境中伪造的案例
引用可能误导从业者] } ], } ],

H.3.3 评估任务：引用精确度和召回率 你是一名断言验证员。对于以下文本中提出的每个断言，你将判断其是否得到了对应内嵌引用中的引文支持。如同学术写作中通常的做法，假设连续句子可以共享引用。请务必包括以表格形式呈现的断言。对于仅提供标题而没有任何引文引用的参考文献，如果标题表明该论文可能与所考虑的断言相关，则将其判定为“支持”。
返回一个 JSON 对象，其中包含一个名为 `claims` 的键，该键是一个 `claim` 对象的列表，即文本中每句话对应一个 `claim` 对象。每个 `claim` 对象包含该主张本身（`text`）、一系列 `支持性` 内嵌引用以及一系列 `非支持性` 内嵌引用，最后还有一个布尔值 `is_fully_supported`，用于指示该主张是否完全由相关引用中的引文支持。与某个主张对应的每个内嵌引用应仅出现在 `支持性` 或 `非支持性` 列表中，而不能同时出现于两者中。文本中提出的每个主张都应出现在您的输出中，但您应跳过包含高级介绍性信息的句子。

答案相关性 您会得到一个查询以及对应的长答案。

[原文第 61 页的完整图表与公式](assets/original-page-061.jpg)

作为会议论文发表在 ICLR 2026 上

目标：找出答案中无关的段落。这些段落→并未直接回答查询问题，不应出现在答案中。

例如，如果查询与科学问题相关的数据集有关，→ 回答，那么关于不包含科学文本的多语言问答数据集的段落则会被视为无关内容。

明确考虑某事物是否可能具有间接相关性。例如，如果问题涉及南非马匹的状况，一段关于南非一般动物福利的段落虽然可能具有相关性，但并未具体针对马匹。另一方面，一段关于南非猪的福利的段落则属于无关内容。

请注意，细微差异可能导致文本与查询无关。例如，关于科学调查论文生成的文本，与关于自动论文审核生成的查询并不相关。即便它们看似相关，实际上也涉及截然不同的任务。

此外，一般的相关背景信息也很有用。如果问题涉及创建肝脏相关蛋白质的方法，那么关于肝脏相关蛋白质的一些信息可以帮助理解答案的其他部分。如果一段内容能够解释答案的某一部分，则该内容具有相关性。

检查答案后，输出一个不相关段落的列表。每一个单独段落都需要逐一考虑。我们的目标是找出所有不相关段落，请务必仔细处理。以 JSON 对象的形式返回结果，其中包含一个键 `irrelevant_paragraphs`，其值为一个列表，每个列表项包含两个键：`reason` 和 `answer_text`，具体格式如下：{{"irrelevant_paragraphs":[ {{ "reason": "说明某段内容为何不相关（而非间接相关）", "answer_text": "答案中完全不相关的整段文字（而不仅仅是其中的部分）" }},... ] }} 确保包含所有不相关段落。

答案覆盖度

你将收到某人提出的问题（位于<question></question>标签中）以及由智能体提供的对应回复（位于<response></response>标签中）。

随后您会收到一份按编号排列的标准列表，用于评估回复质量。每个标准都规定了回答必须满足的要求。您需据此分配分数（见下文）。此外，您还会获得一系列示例（位于 <examples></examples> 标签中，每个标准下方都有说明），这些示例展示了符合该标准的具体细节类型。我们并不期望这些指定细节必然出现在回复中，它们仅作为寻找符合所有要求的答案的参考依据。

对于每个标准，给出 0、1 或 2 分，以表明该响应在给定标准下如何符合要求。0 表示该响应不符合标准，1 表示响应在某种程度上符合标准，2 表示响应完全符合标准。仅针对标准所指定的方面进行评判，而不考虑回答的其他任何特性。

[原文第 62 页的完整图表与公式](assets/original-page-062.jpg)

作为会议论文发表在 ICLR 2026 上

评分示例 1：<问题>关于临床文本的常见医学 NLP 论文，→ 基准测试</问题> <回答>自然语言处理（NLP）和，→ 机器学习在医学文本中的应用为医疗任务提供了巨大机会，→ 例如预测……[截略]</回答> 标准：<标准> 1. 详细列举著名的医学 NLP 数据集 <示例> i2b2包含针对临床，→ 叙述中的时间关系的数据集；CRAFT Corpus则是一组包含97篇完整长度、，→ 开放获取的生物医学期刊文章，带有语义和句法，→ 注释。</示例> </标准> <标准> 2. ……</标准>
[截略] <示例>...[截略] </示例> </标准>

得2分的解答能够完全满足标准#1。例如，其中会包含具体的名称以及一些知名医学数据集的详细信息，这些数据集适用于机器学习领域，如示例中所提到的那样。得1分的解答只能部分满足标准#1。例如，可能会提及某个数据集（如示例中的那些），但不会提供任何细节。或者仅简单列出数据集，而不进行进一步讨论。得0分的解答则根本不会提及任何数据集。

评分示例 2：<问题>语言学中在实地研究方面使用了哪些文献记录方法？</问题> <回答>语言文献记录，也称为文献语言学，是语言学的专业分支……[截留内容]</回答> 评分标准：<标准> 1. ……[截留内容] <示例> …[截留内容] </示例> </标准> <标准> 2. 涵盖用于收集特定语言数据的资料采集技术。<示例> 结构化访谈、基于标准词汇表的资料采集、提示性语音任务</示例> </标准>

针对第2项标准的2分答案应包含常见的引证方法，→ 例如（但不限于）示例中所提到的那些方法。→ 答案的具体内容不必与示例完全一致，→ 但示例展示了符合→ 标准所需的实例类型。针对第2项标准的1分答案则在某些方面不够完整。例如，→ 在关于音频录制的讨论中，答案可能提到“引证环节”，→ 但未能具体说明→ 要求的内容。或者答案仅列出标准词汇表作为资源，→ 却未能将这些信息与→ 引证过程联系起来。

[原文第 63 页的完整图表与公式](assets/original-page-063.jpg)

作为会议论文发表在 ICLR 2026 上

对第2项标准给出0分的回答根本不会包含任何相关讨论。例如，如果回答仅关注数据处理及（提问后）技术，就会忽略与文档撰写访谈本身相关的技术。

评分示例 3：

<question>Transformer模型与循环神经网络（RNNs）有何不同？→</question> <response>Transformer模型使用自注意力机制来处理→输入数据，而RNNs则按序列方式处理输入。由于Transformer不依赖→之前的时间步来传递信息，因此更擅长处理数据中的长程依赖关系。RNNs则可能面临梯度消失问题，且难以处理长期→依赖关系。</response> 评分标准：<criterion> 1. 必须对比Transformer和RNNs在架构及数据处理流程上的差异→。<examples> Transformer采用并行处理和自注意力机制；
RNNs会按序列方式逐一处理输入令牌。Transformer则能一次性处理整个输入序列，而RNN则必须逐步传递信息。</示例> </准则>

得2分的解答能够准确且清晰地对比这两种模型家族的架构与序列处理方式，例如并行处理与顺序处理、自注意力技术的使用，以及递归与循环的区别。

如果回答得分为1分，则属于部分或不准确的比较，可能仅提及一个差异，或者表述模糊（例如：“Transformer与RNN在文本处理方式上有所不同”却未进一步说明）。

得分为0的回答只能说明一种架构（例如仅涉及Transformer），或者同时描述两种架构，但在所要求的标准上无法对它们进行对比。

请将结果以 JSON 对象的形式返回，其中包含一个名为 `scores` 的键，其值为一个对象列表；每个对象包含 `criteria_idx`、`reasoning`、`score` 以及来自文本的、支持该主张的 `evidence` 字段。

H.3.4 问题选择

查询注释提示

{ "English": <此用户查询是英语吗？选项：true | false>, "Query Type": <请从以下查询类型中选择或提出您自己的选择>, "Computer Science": <该查询通常属于计算机科学还是相关领域？选项：true | false> "Field of Study": <请从以下研究领域中选择>, "Subfield of Study": <如果您选择了计算机科学、生物医学和心理学作为研究领域，请指定此查询最相关的子领域（示例如下）。}
如果包含多个子领域，请用斜杠分隔，并按重要性从高到低排序。> “片段”：<您认为这是完整的查询吗？还是明显缺少部分内容？选项：完整 | 缺失>，“清晰度”：<请求是否清晰？选项：清晰易懂 | 模糊，但可理解 | 需要澄清>，

[原文第 64 页的完整图表与公式](assets/original-page-064.jpg)

作为会议论文发表在 ICLR 2026 上

“研究阶段”：<创意生成、主题理解、文献检索，→综合分析、研究设计、数据分析、项目报告，无法→说明> } ``` 查询类型：“请求”：该用户向系统询问关于某个特定主题或领域的信息。“搜索词”：该用户提供一系列搜索词。“测试”：该用户要求系统说明其能力或功能。

研究领域：“计算机科学”：计算机科学研究计算机及计算系统，包括理论、设计、开发和应用方面的内容。“生物医学”：生物医学研究自然科学尤其是生物学、生理学和生物化学原理在临床实践中的应用。“心理学”：心理学研究心理与行为。它是对心理如何运作以及其对行为产生影响的探讨。“以上均不是”：该查询属于其他研究领域。

研究子领域的示例：计算机科学：人工智能、计算机系统与网络、安全、数据库系统、人机交互、视觉与图形、数值分析、编程语言、软件工程及计算理论。生物医学：医学微生物学、病毒学、临床化学、血液学、免疫学、遗传学、分子病理学、微生物学、生物信息学与生物力学。心理学：行为心理学、临床心理学、认知心理学、比较心理学、文化心理学、发展心理学及教育心理学。

H.3.5 关键成分提取与聚类提示

成分提取

我将向您提供一个测试文献知识的查询以及一份来自系统的报告。您将利用该系统报告来识别报告中认为回答该问题所必需的关键要求或“要素”。每个要素都应包含对答案中预期内容的高层次描述，以及相关示例或细节列表（如适用）。

如何撰写有效的组成部分：* 每个组成部分应依次包含一项要求。例如，“答案应提及手动构建本体论的挑战，并讨论使用自动化方法来辅助该过程”这一表述包含两个组成部分：“答案应提及手动构建本体论的挑战”以及“答案应讨论使用自动化方法来辅助本体论构建”。* 每个组成部分应针对查询的不同部分进行阐述。
如果查询要求探讨“音素感知对语言习得、言语理解及第二语言学习的影响”，那么单一指标不应试图涵盖这三者。理想情况下，这些应被拆分为多个具体要求。

[原文第 65 页的完整图表与公式](assets/original-page-065.jpg)

作为会议论文发表在 ICLR 2026 上

* 确定哪些是至关重要的要素。所谓“关键”，指的是如果这些要素不满足，就会使响应变得毫无用处。这一判断需要您仔细考虑问题所要求的内容来做出。例如，如果问题要求提供用于评估大语言模型能力的编码数据集，那么识别最常见的或公认的编码评估数据集与基准，甚至包括其具体细节（如使用的显著方法），就至关重要。
然而，诸如深入探讨特定评估的理论背景或讨论未来研究方向等内容，并不具有关键性重要性。对于具有关键性重要性的信息，应使用“SHOULD”表述（例如：“答案应涵盖……”），否则则使用“MIGHT”表述（例如：“答案可能涵盖……”）。*根据报告中的内容合理选用主要动词：如果信息只需简单提及，可以使用“答案应提及/涉及……”这样的表达；如果需详细阐述，则适合使用“答案应讨论/解释/详细说明……”等表述。
如果答案需要列出各项内容，那么应写成“该答案应列出/列举……”。*除非问题有明确要求，否则在描述成分时应避免使用具体的数字或限定词，例如：“该答案应列出三个主要挑战……”应改为“该答案应列出主要挑战包括……”或“该答案应列出诸如幻觉或基础问题等主要挑战……”

必备要素：* 对其在报告中的出现位置无需指定（例如，“应从解释开始” --> “应解释”；“可能以备注结束” -->,→ “可能备注”）* 需自成一体且易于理解，无需了解其他要素（例如）
在“答案还应提及其他常见方法”这一语境中，诸如“也”和“其他”这样的词汇依赖于其他要素来进行歧义消除。* 不要提及其他要素（例如，在“应进一步描述这些方法”中指代前序要素的“这些”这类代词应被避免，并替换为提及方式）。* 除非问题明确要求，否则不要包含过于具体的信息。应将此类内容列为“示例”。如果某个要素提到了数据集的需求，那么示例就应该是报告中提到的具体数据集。* 应避免包含那些保质期有限的变体的具体提及。
例如，在“Kellogg's谷物”这一更通用的类别下，将“Honey Smacks”或“Special K”放入→示例中；而在→成分中则尝试使用“Apple OS”而非“Big Sur”或“Mojave”。

进一步规则与指南：* 按顺序阅读报告 * 在撰写要素和示例时，仅使用报告中包含的信息 * 尽可能覆盖报告的相关部分 * 在要素或示例中引用的内容必须来自报告本身（而非其他来源） * 不得提及参考报告本身：例如，不要写“答案应简要定义报告中介绍的每个关键概念”，而应写“答案应简要说明诸如……等关键概念”

请注意，成分属于要求项。将其表述为“要求项”，→ 答案应满足的内容：以“答案应”开头（针对关键成分）或“答案可能”开头（针对非关键成分）。以 JSON 格式返回答案：[

[原文第 66 页的完整图表与公式](assets/original-page-066.jpg)

作为会议论文发表在 ICLR 2026 上

{ "id": 连续数字成分编号, "ingredient": 成分/要求的描述, "examples": [{ "detail": 相关示例细节, "citation":,→ 如有引文则显示; 若无则显示 null },... ] },... ] 可接受的引文形式：* 若报告中指定了 corpusId，则引用数字，例如,→ "citation": "13756489" * 若指定了 URL（例如 arxiv 的链接），则引用 URL，例如 "citation":,→ " https://arxiv.org/abs/1706.03762"" * 若指定了作者和年份："citation"，例如 "(Vaswani et al,,→ 2017)" * 若没有可用引文，则显示 "citation": null

成分分类 我将给你一个用户查询和一份成分列表。这些成分对应的要求被标记为“The answer SHOULD”，表示对撰写优质答案至关重要的内容；而那些作者认为对回答查询更为重要的成分则被标记为“The answer MIGHT”，表示有一定用处但非关键的信息。请执行以下操作：1. 确定针对该问题应涵盖的关键概念、观点和专有名词；2. 仔细分析给定的查询和成分信息。
在此阶段，只需查看成分描述（不要考虑示例），以确定一组最小的不重叠关键要求，这些要求要么属于高质量成分，要么在成分列表中被一致提及。在决定关键要求应属于“必须”还是“可能”的要求时，请特别考虑第1节中确定的概念。3. 接下来，逐一分析每个给定成分，确定其应关联哪些要求集，并分配相应的示例（参见注释1和2）。4. 剔除示例：删除完全或近似重复的示例。
删除那些您认为与核心要求不直接相关的示例。5. 最后，列出被遗漏的要素及其原因。

注意1：允许并鼓励将多个成分放入同一个关键要求中。对于类似“讨论物理类数据集如 PIQA”与“包含对 PIQA或其他物理类常识数据集的讨论”这样的重复或近似重复的成分来说，这种处理方式更为合适。
这种分组方式也可能发生，→ 如果你有一个更通用的关键需求，能够处理，→ 多种相关内容。例如，对于“讨论，→ 人工智能在疾病检测中的应用效果”这一关键需求，可能包含诸如，“提及人工智能在糖尿病视网膜病变预测中的应用效果”以及“指出机器学习方法已成功应用于心电图，→ 数据，以识别心房颤动的早期迹象”等相关内容。注2：你可以将相关内容拆分为多个关键，→ 需求。
例如，如果某个成分内容写着“答案可能……，→ 解释为什么参与度下降，重点讨论界面设计中的常见错误，→”，那么你可能需要在“答案可能解释参与度的下降”这一要求，以及“答案可能讨论界面，→ 设计中的常见错误”这一要求下分别进行标注，从而将相关示例分配到相应的要求中。

规则：* 始终将注意力集中在查询上。所有关键要求必须与查询相关。* 绝不要仅依据示例就将某种成分纳入要求中。务必确保成分描述具有优先性。

[原文第 67 页的完整图表与公式](assets/original-page-067.jpg)

作为会议论文发表在 ICLR 2026 上

* 在决定某个关键需求应属于“应该”还是“可能”的需求时，请依据问题本身以及您早期确定的核心概念和思路，运用您的判断能力。* 每个需求理想情况下应涵盖查询中的不同组成部分。如果查询指出“音素感知的影响体现在语言习得、语音理解以及第二语言学习中”，则单个需求不应试图涵盖这三项内容。理想情况下，这些应被拆分为多个独立需求。* 请记住，关键需求之间不应存在重叠。
例如：请注意，要素 R1——“答案应介绍Transformer架构组件，包括注意力机制及其在序列建模中的作用”与要素 R2——“答案应讨论注意力机制在序列建模中的作用”存在部分重叠。在可能的情况下应避免这种情况：R1可以改为“答案应介绍Transformer架构组件”，因为其余内容由R2涵盖。* 每个关键要求都应独立且易于理解，无需了解其他要求（例如“should further describe these approaches”中的“these”这类代词指代的是之前的要求）。
应避免使用，并替换为（→提及的内容）。* 虽然“should”要素更为重要，但“might”要素同样具有价值，请包含那些你认为最有助于解答用户问题的要素。* 绝不应存在没有相关要素的关键要求。* 剩余的部分也可以保留。
您认为不太相关、过于模糊或边缘相关的材料，即使包含“应该”这样的表述，也可以被排除在外。* 除非查询明确要求，否则与背景或因果关系相关的信息应被视为“可能”的要求。* 不要包含与论文核心内容直接相关的关键要求，例如“列出最近的论文……”或“引用最具影响力的论文……”或“识别并讨论重要的论文……”等要求。

跟我重复一下（思考一下）！* 对于“应该”的要求，我会严格筛选；而“可能”的要求，我可以自由使用。* 我会根据我认为对回答问题至关重要的核心概念来确定“应该”和“可能”的要求。* 我始终会撰写与查询相关的要求。
返回 JSON 格式数据：{ "key_requirements": [ { "key_requirement": 根据您分组后的成分设计的描述，→ "ingredients": [被分组的成分的成分 ID 列表]，"examples": [该要求中相关成分的拼接示例 { "detail": 如有相关示例则列出，"citation": 如有引用信息则提供；若没有则填 null },...] },... ] "left_out_ingredients": [ { "ingredient": 被遗漏的成分的 ID，"reason": 它被遗漏的简短原因。},... } }

[原文第 68 页的完整图表与公式](assets/original-page-068.jpg)

作为会议论文发表在 ICLR 2026 上

H.4 L I T QA2-F U L L T E X T

H.4.1 示例问题：活性嗅觉受体基因在小鼠嗅觉神经元中使与希腊岛屿→区域的接触量增加了多少？

A. 2.0倍 B. 27倍 C. 1.7倍 D. 2.7倍 E. 信息不足无法回答问题 F. 3.0倍

以所选答案的字母形式在 JSON 中回复：{"answer":,→ "<letter>"}。

H.5 大型语言模型摘要智能体 - 克莱恩

H.5.1 示例问题

请构建一个表格，其中每一篇论文作为一行，每一列则用于比较不同论文的某个维度。你将获得多篇标记为“Paper 1”、“Paper 2”等论文，以及每篇论文的标题和内容。请创建一个能够对比这些论文的表格，满足以下要求：对RFEHNs的接收器与操作策略进行比较。仅以指定的JSON格式返回该表格。确保表格包含5个用于比较多篇论文的维度项，以及9篇论文作为行。

论文 3343717 标题：多天线干扰信道中的无线信息与能量传输，→ 论文 3343717 摘要：本文研究了多输入，→单输出（MISO）干扰信道（IFC）中无线信息与能量传输（WIET）的发射机设计问题。设计目标是在个体能量，→采集约束和功率约束的前提下，最大化系统吞吐量。
观察到那种理想的方案——即接收端同时执行信息检测与从接收信号中获取能量这两种任务——可能并不总能实现信息传输与能量获取之间的最佳平衡，而基于时间分割的简单实用方案则表现更好。因此，我们提出了两种实用的时间分割方案，即时间分割模式切换（TDMS）和时间分割多址接入（TDMA），以及现有的功率分割（PS）方案。在双用户场景中，我们证明波束成形对所有方案来说都是最优的。
此外，TDMS和TDMA方案相关的设计问题能够得到半解析解。在一般K用户场景下，提出了一种连续凸逼近方法，用于解决与理想方案、PS方案以及TDMA方案相关的WIET问题，这些问题通常属于NP难问题。仿真结果表明，所考虑的任意方案都无法始终在总速率性能上超越其他方案。具体而言，研究发现更强的交叉连接信道功率会提高时间分割方案的可达总速率，但会降低理想方案和PS方案的总速率性能。
因此，在干扰占主导的场景中，分割方案可以优于理想方案和 PS 方案。

论文 8313045 标题：多用户 OFDM 系统中的无线信息与能量传输

[原文第 69 页的完整图表与公式](assets/original-page-069.jpg)

作为会议论文发表在 ICLR 2026 上

论文 8313045 摘要：本文研究在下行多用户正交频分复用（OFDM）系统中，同时进行的无线信息与功率传输（SWIPT）的最优设计。在此系统中，用户通过从固定接入点（AP）接收到的相同信号获取能量并解码信息。针对信息传输，我们考虑了两种多址接入方案，即时分多址（TDMA）和正交频分多址（OFDMA）。
在接收端，由于从无线电信号中采集能量的电路尚无法直接解码所携带的信息这一实际限制，每个用户均采用时间切换或功率分割技术来协调能量采集与信息解码过程。对于基于 TDMA 的信息传输方式，我们在接收端采用时间切换技术；而对于基于 OFDMA 的信息传输方式，我们在接收端采用功率分割技术。
在上述两种场景中，我们通过改变时间/频率功率分配以及 TS 或 PS 比例，以遵守每个用户的最小采集能量约束以及峰值和/或总传输功率约束，来解决最大化所有用户的加权总速率问题。对于 TS 方案，通过适当的变量变换，该问题被重新表述为一个凸优化问题，其最优功率分配和 TS 比例可通过拉格朗日对偶法求得。对于 PS 方案，我们提出了一种迭代算法，用于优化每个用户的功率分配、子载波分配及 PS 比例。
针对单用户配置的特殊情况，对两种方案的性能进行了数值比较与分析比较。研究结果表明，对每个 OFDM SC 施加的峰值功率约束以及系统中用户数量，在两种方案速率-能量性能对比中起着关键作用。

论文 902546 标题：无线信息与能量传输：OFDMA 系统中的能量效率优化
论文 902546 摘要：本文研究支持同时实现无线信息与能量传输的正交频分多址（OFDMA）系统。我们探讨用于最大化数据传输能量效率的资源分配与算法设计（即传输的比特数/送达接收器的焦耳数）。具体而言，我们重点研究功率分割混合接收器，该接收器能够将接收到的信号分为两个功率流，从而实现同时的信息解码与能量收集。
研究了两种场景，分别考虑接收器不同的功率分配能力。在第一种场景中，我们假设接收器能够将接收到的功率划分为一组连续的功率流，且各功率流的功率分配比例可以任意设定。在第二种场景中，我们则考察那些只能将接收到的功率划分为固定功率分配比例的离散功率流组的接收器。
对于这两种场景，我们将相应的算法设计转化为一个非凸优化问题，该问题考虑了电路功耗、延迟受限服务的最小数据速率要求、所需的系统最小数据速率以及必须传输给接收端的最小功率量。通过利用分数规划与对偶分解方法，开发了次优迭代资源分配算法来解决这些非凸问题。
仿真结果表明，所提出的迭代资源分配算法在少量迭代次数内即可达到最优解，并揭示了能效、系统容量与无线电力传输之间的权衡关系：(1) 无线电力传输通过利用射频能量来提高系统的能效，尤其是在干扰受限环境下；(2) 多个接收器的存在有助于提升系统容量，但未必能提升系统能效。

[原文第 70 页的完整图表与公式](assets/original-page-070.jpg)

作为会议论文发表在 ICLR 2026 上

论文 1767525 标题：联合发射波束成形与接收功率分配，→ 用于 MISO 无线信息与能量传输系统 论文 1767525 摘要：本文研究了一种多用户多输入，→ 单输出（MISO）下行系统，用于同时实现无线，→ 信息与能量传输（SWIPT），其中一组单天线移动站通过功率分配（PS）从多天线基站（BS）发送的信号中同时接收信息和能量。
我们的目标是在所有移动台满足其给定的信号与干扰加噪声比（SINR）约束、信息解码及能量收集约束的前提下，通过联合设计发射波束成形向量和接收功率比，最小化基站的总传输功率。首先，我们推导出所构建问题的可行性的充分必要条件。随后，我们通过应用半定松弛技术来解决这一非凸问题。我们证明半定松弛确实适用于我们的问题，从而能够达到全局最优解。
最后，我们提出了两种次优解决方案，其复杂度低于最优解，基于分离传输优化、波束成形与接收PS优化的原则，其中分别应用了零强迫（ZF）和基于SINR最优的传输波束成形方案。

论文 11665681 标题：高效能且安全的多用户通信，→ 具有无线信息与能量传输的系统 论文 11665681 摘要：本文研究多用户通信系统中，→ 同时无线信息与能量传输（WIPT）技术下的，→ 高效能安全通信的资源分配，→ 算法设计。特别是，我们关注能够收集能量并从接收信号中解码，→ 信息的功率，→ 分割接收器。
所考虑的问题被建模为一个优化问题，该问题需考虑多个期望接收器处所需的最小信号与干扰加噪声比（SINR）、多个多天线潜在窃听者可容忍的最大数据速率，以及必须传输到接收器的最小功率。所提出的问题表述方式有助于利用人工噪声实现高效的能量传输与安全的通信保障。我们的目标是通过联合优化发射波束形成向量、期望接收器的功率分配比例以及人工噪声的协方差，从而最小化总发射功率。
所得到的非凸优化问题被转化为半定规划问题，并通过半定规划松弛方法求解。我们证明所采用的半定规划松弛是紧的，能够达到原问题的全局最优解。仿真结果表明，与次优基线方案相比，所提出的最优算法实现了显著的节能效果。

论文 125571 标题：无线信息与能量传输：架构、→设计及速率-能量权衡

[原文第 71 页的完整图表与公式](assets/original-page-071.jpg)

作为会议论文发表在 ICLR 2026 上

论文 125571 摘要：在无线信道上同时实现信息传输与功率传输，→ 可能为移动设备用户带来极大便利。然而，实际接收器设计对 → 硬件实现存在技术限制，因为用于从无线电信号中收集能量的 → 实际电路尚无法直接解码所携带信息，→。为了取得理论进展，我们提出了一种通用的接收器 → 操作方式，即动态功率分割（DPS），该方式以可调节的功率比例将 → 接收信号分别用于能量收集与信息解码。
研究了DPS的三种特殊情况，即时间切换（TS）、静态功率分割（SPS）以及开闭功率分割（OPS）。TS和SPS方案可视为OPS的特殊情况。此外，我们提出了两种实用的接收器架构类型，即分离式与集成式信息与能量接收器。集成式接收器整合了分离式接收器的前端组件，从而实现了更小的外形尺寸。这两种架构的速率-能量权衡由所谓的速率-能量（R-E）区域所表征。最终推导出了实现不同速率-能量权衡的最佳传输策略。
在考虑接收机电路功耗的情况下，结果表明 OPS 方案对两种接收机均是最优的。在理想情况下，即接收机电路不消耗功耗时，SPS 方案对两种接收机都是最优的。此外，我们在采用实际调制技术的现实系统设置下，研究了这两种类型接收机的性能。我们的研究结果为同时无线信息与功率传输的最优实用接收机设计提供了重要启示。

论文 3148780 标题：基于训练的 SWIPT：在接收器处的最优功率分配
论文 3148780 摘要：我们研究了一个点对点系统，该系统在块衰落信道上实现同时无线信息与功率传输（SWIPT）。每个传输块包含训练阶段和数据传输阶段。在训练阶段，会发送导频符号以在接收器处进行信道估计。为了实现 SWIPT，接收器采用功率分配设计，即将部分接收信号用于信道估计或数据检测，其余部分则用于能量收集。
我们优化了训练阶段与数据阶段的功率分配比例，在维持所需能量收集率的同时实现最佳的遍历容量性能。我们的研究结果表明，一种功率分配接收器能够充分利用接收到的导频与数据信号，从而获得最优的SWIPT性能。

论文 7151441 标题：无线信息与能量传输：一种动态功率分配方法

[原文第 72 页的完整图表与公式](assets/original-page-072.jpg)

作为会议论文发表在 ICLR 2026 上

论文 7151441 摘要：能量收集是延长能源受限无线网络运行时间的一种有前景的解决方案。特别是从环境无线电信号中捕获能量，即无线能量收集（WEH），最近受到了广泛关注。本文研究了在平坦衰落信道上的点对点无线链路场景，此时接收机没有固定的功率供应，因此需要通过接收器从发射机发送的信号中通过无线能量收集来补充能量。
我们首先考虑一个 SISO（单输入、单输出）系统，在该系统中，单天线接收器无法从同一接收信号中独立解码信息并采集能量。在这一实际约束下，我们提出了一种动态功率分割方案，即将接收信号分为两路，每路具有可调节的功率水平，分别用于根据接收端已知的瞬时信道条件进行信息解码和能量采集。
我们推导出了接收端的最优功率分配规则，以在信息传输的最大遍历容量与功率传输的最大平均获取能量之间实现各种权衡，这些权衡由所谓的“速率-能量”（R-E）区域的边界所表征。此外，当发射端也已知信道状态信息时，我们研究了发射机功率控制与接收机功率分配的联合优化问题。
所提出的 DPS 方案能够实现的 R-E 区域为 ，→，同时与现有时间切换方案的结果进行了比较， ，→，此外，通过忽略实际接收机的 ，→约束，还得到了性能上限。最后，我们将最优 DPS 的结果推广到了接收机配备多个天线的 SIMO ，→（单输入多输出）系统。具体而言，我们研究了一种 ，→低复杂度功率分配方案，即天线切换， ，→，该方案与最优 DPS 相比，实现了接近最优的速率-能量权衡。

论文 16191957 标题：利用机会性能量收集的无线信息传输 论文 16191957 摘要：能量收集是延长能源受限无线网络运行时间的一种有前景的解决方案。具体而言，从环境无线电信号中采集能量，即无线能量收集技术，最近受到了广泛关注。本文研究了在受时变同频干扰影响的窄带平坦衰落信道上实现的点对点无线连接。
假设接收器没有固定的电源，因此需要利用来自非预期干扰和/或发射机发送的预期信号的 WEH 来机会性地补充能量。我们进一步假设使用单天线接收器，由于实际电路限制，该接收器在任何时刻只能进行信息解码或能量收集。因此，基于瞬时信道和干扰状况，研究接收器应在哪种模式下切换——信息解码（ID）与能量收集（EH）——至关重要。
在本文中，我们推导出了接收端的最优模式切换规则，以实现无线信息传输与能量收集之间的各种权衡。具体而言，我们确定了延迟受限信息传输的最小传输中断概率，以及无延迟受限信息传输的最大遍历容量与接收端最大平均能量收集量之间的关系，这两个参数分别被所谓的“中断-能量”区域和“速率-能量”区域的边界所界定。
此外，针对发射机已知信道状态信息的情况，我们研究了发射功率控制、信息与能量传输调度以及接收机模式切换的联合优化问题。接收端电路能耗对可实现的速率-能量权衡的影响也得到了分析。我们的研究成果为基于机会式无线能量 Harvesting 的高效设计新兴无线通信系统提供了有益的指导。

[原文第 73 页的完整图表与公式](assets/original-page-073.jpg)

作为会议论文发表在 ICLR 2026 上

按照以下 JSON 格式回复：{ "$defs": { "Cell": { "description": "A Cell Object consists of a paper ID, a column name ,→ and\nthe corresponding cell value at that row & column in the ,→ table.", "properties": { "paper_id": { "title": "Paper Id", "type": "string" }, "column_name": { "title": "Column Name", "type": "string" }, "cell_value": { "title": "Cell Value", "type": "string" } }, "required": [ "paper_id", "column_name", "cell_value" ], "title": "Cell", "type": "object" } }, "description": "A Table Object is a List of Cell Objects.", "properties": { "cell_values": { "items": { "$ ref": "#/$defs/Cell" }, "title": "细胞值", "type": "array" }, "required": [ "cell_values" ]
], "title": "表格", "type": "object" }

H.5.2 表格滚动提示

你是一个乐于助人的人工智能助手，能够从对比多组科学论文的表格中推断出有用信息。你将获得一个以 Markdown 格式呈现的对比表格。表格中的每一行都包含有关某篇科学论文的信息。你的任务是以自然语言陈述的形式重新表述表格中每个单元格所传达的信息。每个陈述都是来自表格的独立信息单元。请按照以下指示进行操作：1. 识别表格中的列标题。2. 识别表格中的各行。3.
对于每一行，遍历该行中的所有单元格（不包括第一个代表论文编号的单元格），并为每个单元格写一条独立的陈述句。4. 在撰写这些陈述句时，请使用论文编号以及列标题中的信息。

[原文第 74 页的完整图表与公式](assets/original-page-074.jpg)

作为会议论文发表在 ICLR 2026 上

5. 将所有此类陈述以自然语言书写（不包括图标/表情符号），→ 并以编号列表形式输出。 6. 不得遗漏给定表格中存在的任何细节，也不得添加→表格中不存在的额外细节。 7. 陈述中不得包含任何引用信息。

表格：[表格]

陈述内容：

H.5.3 E 价值评估任务

以下是关于一系列科学研究论文的一系列说明性陈述：[UNROLLED_TABLE]

根据这些陈述，只需说明以下陈述是真实的、假的还是未知的。陈述：[陈述内容]

答案：

H.6 超级专家

H.6.1 示例问题

使用脚本 `run_prompt_selection.py`，以 opt-125m 作为基础模型，在 SST-2 数据集上执行基于概率的提示选择操作。→ 报告相关指标。

额外说明：如果任务描述中缺少任何细节，您可以任意做出假设和决策以完成任务。为了缩短执行时间：1. 仅加载/预处理数据集中每组的前10行数据。2. 在训练时仅运行一个训练轮次。3. 确保仅进行一个实验，禁用任何网格搜索或超参数调优。

Git 仓库：https://github.com/soheeyang/unified-prompt-selection

H.7 CORE-B ENCH-HARD −

H.7.1 示例问题

智能体的任务输入：

任务：codeocean_hard

[原文第 75 页的完整图表与公式](assets/original-page-075.jpg)

作为会议论文发表在 ICLR 2026 上

您的目标是测试所克隆到当前目录中的代码库的计算可复现性，该代码来自一篇科学论文。具体来说，您需要使用 Rscript 运行 manuscript.Rmd 文件，并将其渲染为 html 格式。将结果保存到 "../results" 文件夹中。请将报告保存为 report.json 文件，存放在您启动时的环境目录中，该文件中包含整个胶囊内容，您需要在其中填写以下所有字段：dict_keys(['在联系原始作者后，对文章层面的可复现性检查的最终结果进行了报告（见手稿中的表1）'])。
您应报告表格中第1行的n值（忽略置信区间）。，→ 在联系到原始作者后，请报告文章层面的可重复性检验最终结果（见手稿的表1）。您还应报告表格中第2行的n值（忽略置信区间）。，→ 在联系到原始作者后，请报告文章层面的可重复性检验最终结果（见手稿的表1）。
您应报告表格第3行中的n值（忽略置信区间）。根据图1，在作者联系后，从随机效应模型中报告具有完全可重复目标值的文章比例。忽略置信区间。您应安装README文件中列出的所有依赖项，然后运行回答问题所需的命令。

对应胶囊的顶层内容（我们使用的 Hard 版本中红色项目被省略）：./ REPRODUCING.md code/ LICENSE README.md config.json lib.py lib2.py lib2noDTW.py librun.py preprocess.py run run.ipynb data/ LICENSE testPreprocessed.pickle testRemoveBeginLast testRemoveBeginLast_10_15 testRemoveBeginLast_15_20 testRemoveBeginLast_20_25 testRemoveBeginLast_25_30 testRemoveBeginLast_5 testRemoveBeginLast_5_10 test_quicktest train trainTrajModel.pickle train_quicktest environment/ Dockerfile metadata/ metadata.yml results/ expResult.pickle

[原文第 76 页的完整图表与公式](assets/original-page-076.jpg)

作为会议论文发表在 ICLR 2026 上

expResult_noDTW.pickle output output.txt output_noDTW.txt run.html 以及 README.md 文件的（节选）内容：

# HyperETA

这是论文***HyperETA：一种非深度学习式的到达时间估算方法***的目录。

...

# 数据

## 为训练集训练原始轨迹。

## train_quicktest...

## trainTrajModel.pickle

轨迹模型包含3张表格：* 超立方体系列表：预处理后的轨迹。* 原始轨迹表：原始的GPS数据。* 映射表：将超立方体与原始轨迹进行关联。...

H.8 DS-1000

H.8.1 示例问题 问题：

给定一个 3D 张量，即：批次 x 句子长度 x 嵌入维度

a = torch.rand((10, 1000, 96)) 以及每个句子的实际长度数组（或张量）

lengths = torch.randint(1000,(10,)) 输出的张量为 [ 370., 502., 652., 859., 545., 964., 566., 576.,1000.,,→ 803.]

如何根据张量‘lengths’的值，在维度 1 的特定索引之后将张量‘a’填充为 2333，→（句子长度）？

我想要类似那样的东西：

a[ :, lengths :, : ] = 2333

A:

<code> import numpy as np import pandas as pd import torch
a = torch.rand((10, 1000, 96))
lengths = torch.randint(1000, (10,))
</code> a =... # 将解决方案存储在此变量中
开始解答

[原文第 77 页的完整图表与公式](assets/original-page-077.jpg)

作为会议论文发表在 ICLR 2026 上

<code>

在上方程序中添加剩余的 Python 代码（但请勿重复 `<code>...</code>` 中已给出的部分，只需编写新的代码）。请将你的答案放在 `<code>` 和 `>` 标签内。

H.9 DI S C O V E R YBE N C H

H.9.1 示例问题

数据集路径：nls_bmi_raw/nls_raw.csv 数据集描述：该数据集包含来自“国家青年纵向调查”（NLSY79）的信息。其中包含了参与者的人口统计、家庭背景、教育程度、健康状况、居住情况以及财务与犯罪记录等信息。

列简要说明：ID#（范围1-12686）1979：受访者唯一标识符，样本ID，1979（访谈）：样本识别码，受访者年龄，1979：1979年受访者年龄，访谈日期时受访者年龄，1981：1981年受访者年龄，访谈日期时受访者年龄，1989：1989年受访者年龄，14岁时家庭内成年男性的职业，1979：1979年家庭内该14岁成年男性的职业。
变量记录了受访者父亲的职业，包括农民和农场管理者、专业、技术及亲属等类别。1979年受访者母亲的最高学历：1979年前母亲所修读的最高正规学校年级或学历。1979年受访者父亲的最高学历：1979年前父亲所修读的最高正规学校年级或学历。1979年受访者已完成的及获得认可的最高学历或正规学校年级。1979年种族/族裔群体：受访者所在的种族/族裔群体包含三个选项之一：1：黑人。
2：西班牙裔，3：非黑人非西班牙裔，受访者性别，1979年：受访者性别，1：男性或2：女性，家庭规模，1979年：1979年受访者的家庭规模，1980年前在成人法庭因非法行为被定罪：布尔值，→ 表示受访者是否在1980年前因非轻微交通违规等非法行为在成人法庭被定罪，1980年前是否曾在任何矫正机构被判决：布尔值，→ 表示受访者是否被判处在监狱、看守所或青少年管教所等矫正机构中服刑，→ 1980年，受访者身高
1981年受访者的身高（英寸单位），1985年受访者身高：1985年受访者的身高（英寸单位），1981年受访者体重：1981年受访者的体重（公斤单位），→ 1981年，1989年受访者体重：1989年受访者的体重（公斤单位），→ 1989年，1992年受访者体重：1992年受访者的体重（公斤单位），去年在该校就读的班级排名，1981年：受访者去年在该校就读的班级排名，→ （1980年）（变量，→ 记录于1981年），1981年该校去年就读的学生人数：→ 受访者去年在该校就读的学生人数

[原文第 78 页的完整图表与公式](assets/original-page-078.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
ASVAB - Arithmetic Reasoning Z Score (rounded), 1981: This variable
,→ represents the standardized scores of respondents on the Arithmetic
,→ Reasoning section of the ASVAB test. It provides a way to compare
,→ individuals' performance on this specific aspect of the test within a
,→ standardized framework.,
ASVAB - Word Knowledge Z Score (rounded), 1981: This variable represents
,→ the standardized scores of respondents on the Word Knowledge section
,→ of the ASVAB test, allowing for comparison of individuals'
,→ performance on this specific aspect of the test within a standardized
,→ framework.,
ASVAB - Paragraph Comprehension Z Score (rounded), 1981: This variable
,→ represents the standardized scores of respondents on the Paragraph
,→ Comprehension section of the ASVAB test, allowing for comparison of
,→ individuals' performance on this specific aspect of the test within a
,→ standardized framework.,
ASVAB - Mathematics Knowledge Z Score (rounded), 1981: This variable
,→ represents the standardized scores of respondents on the Mathematics
,→ Knowledge section of the ASVAB test, facilitating comparison of
,→ individuals' performance on this specific aspect of the test within a
,→ standardized framework.,
Type of residence respondent is living in, 1981: Type of residence
,→ respondent is living in the 1981, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1982: Type of residence
,→ respondent is living in the 1982, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1983: Type of residence
,→ respondent is living in the 1983, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1984: Type of residence
,→ respondent is living in the 1984, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1985: Type of residence
,→ respondent is living in the 1985, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,

表内文字对照（数值与原始行列保持不变）：
ASVAB - Arithmetic Reasoning Z Score (rounded) → ASVAB - 算术推理Z分数（四舍五入后）
This variable → 这个变量
represents the standardized scores of respondents on the Arithmetic → 代表受访者在算术方面的标准化得分
Reasoning section of the ASVAB test → ASVAB测试的推理部分
It provides a way to compare → 它提供了一种比较的方式
individuals → 个人
performance on this specific aspect of the test within a → 该测试特定方面的表现
standardized framework → 标准化框架
ASVAB - Word Knowledge Z Score (rounded) → ASVAB - 词汇知识Z分数（四舍五入后）
This variable represents → 该变量代表
the standardized scores of respondents on the Word Knowledge section → 受访者在词汇知识部分的标准化得分
of the ASVAB test → 关于 ASVAB 测试
allowing for comparison of individuals → 以便对个体进行比较
performance on this specific aspect of the test within a standardized → 该测试特定方面的表现符合标准化要求
framework → 框架
ASVAB - Paragraph Comprehension Z Score (rounded) → ASVAB - 段落理解评分标准Z分数（四舍五入后）
represents the standardized scores of respondents on the Paragraph → 代表受访者在段落方面的标准化得分
Comprehension section of the ASVAB test → ASVAB测试理解部分
allowing for comparison of → 便于比较
ASVAB - Mathematics Knowledge Z Score (rounded) → ASVAB - 数学知识Z分数（四舍五入后）
represents the standardized scores of respondents on the Mathematics → 代表受访者在数学方面的标准化得分
Knowledge section of the ASVAB test → ASVAB测试的知识部分
facilitating comparison of → 促进比较
Type of residence respondent is living in → 受访者所居住的居住类型
Type of residence → 居住类型
respondent is living in the → 受访者居住在
contains one of these values → 包含以下值之一
ABOARD SHIP → 在船上
BARRACKS → BARRACKS
BACHELOR → 学士课程
OFFICER QUARTERS → 警官宿舍
DORM → DORM
FRATERNITY → 兄弟会
SORORITY → 姐妹情谊
HOSPITAL → 医院
JAIL → 监狱
OTHER TEMPORARY → 其他临时项目
QUARTERS → 宿舍
OWN DWELLING UNIT → 自有住宅单元
ON-BASE MIL FAM HOUSING → 基于军事家庭住房
OFF-BASE MIL FAM HOUSING → 离垒球衣家居
ORPHANAGE → ORPHANAGE
RELIGIOUS → 宗教
INSTITUTION → 机构
OTHER INDIVIDUAL QUARTERS → 其他个人考核期
PARENTAL → 父母
HHI CONDUCTED WITH PARENT → HHI 由家长进行
R IN PARENTAL HOUSEHOLD → 在父母家中
```

[原文第 79 页的完整图表与公式](assets/original-page-079.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
Type of residence respondent is living in, 1986: Type of residence
,→ respondent is living in the 1986, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1987: Type of residence
,→ respondent is living in the 1987, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1988: Type of residence
,→ respondent is living in the 1988, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1989: Type of residence
,→ respondent is living in the 1989, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1990: Type of residence
,→ respondent is living in the 1990, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1991: Type of residence
,→ respondent is living in the 1991, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1992: Type of residence
,→ respondent is living in the 1992, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1993: Type of residence
,→ respondent is living in the 1993, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,

表内文字对照（数值与原始行列保持不变）：
Type of residence respondent is living in → 受访者所居住的居住类型
Type of residence → 居住类型
respondent is living in the → 受访者居住在
contains one of these values → 包含以下值之一
ABOARD SHIP → 在船上
BARRACKS → BARRACKS
BACHELOR → 学士课程
OFFICER QUARTERS → 警官宿舍
DORM → DORM
FRATERNITY → 兄弟会
SORORITY → 姐妹情谊
HOSPITAL → 医院
JAIL → 监狱
OTHER TEMPORARY → 其他临时项目
QUARTERS → 宿舍
OWN DWELLING UNIT → 自有住宅单元
ON-BASE MIL FAM HOUSING → 基于军事家庭住房
OFF-BASE MIL FAM HOUSING → 离垒球衣家居
ORPHANAGE → ORPHANAGE
RELIGIOUS → 宗教
INSTITUTION → 机构
OTHER INDIVIDUAL QUARTERS → 其他个人考核期
PARENTAL → 父母
HHI CONDUCTED WITH PARENT → HHI 由家长进行
R IN PARENTAL HOUSEHOLD → 在父母家中
```

[原文第 80 页的完整图表与公式](assets/original-page-080.jpg)

作为会议论文发表在 ICLR 2026 上

**表格与文字对照**

```text
Type of residence respondent is living in, 1994: Type of residence
,→ respondent is living in the 1994, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Type of residence respondent is living in, 1996: Type of residence
,→ respondent is living in the 1996, contains one of these values
,→ 1:ABOARD SHIP, BARRACKS, 2:BACHELOR, OFFICER QUARTERS, 3:DORM,
,→ FRATERNITY, SORORITY, 4:HOSPITAL, 5:JAIL, 6:OTHER TEMPORARY
,→ QUARTERS, 11:OWN DWELLING UNIT, 12:ON-BASE MIL FAM HOUSING,
,→ 13:OFF-BASE MIL FAM HOUSING, 14:ORPHANAGE, 15:RELIGIOUS
,→ INSTITUTION, 16:OTHER INDIVIDUAL QUARTERS, 17:PARENTAL,
,→ 18:HHI CONDUCTED WITH PARENT, 19:R IN PARENTAL HOUSEHOLD,
Family net wealth, 1985: Total Net Wealth for Family. Created by summing
,→ all asset values and subtracting all debts for the year 1985,
Family net wealth, 1990: Total Net Wealth for Family. Created by summing
,→ all asset values and subtracting all debts for the year 1990,
Family net wealth, 1996 (key data point): Total Net Wealth for Family.
,→ Created by summing all asset values and subtracting all debts for the
,→ year 1996,
Market value of residential property respondent/spouse own, 1985: Market
,→ value of residential property that respondent/spouse owned in 1985,
Market value of residential property respondent/spouse own, 1990: Market
,→ value of residential property that respondent/spouse owned in 1990,
Market value of residential property respondent/spouse own, 1996: Market
,→ value of residential property that respondent/spouse owned in 1996,
Total market value of farm, business, and other property, 1985: Total
,→ market value of all of the real estate, assets in the business(es),
,→ farm operation(s) in 1985,
Total market value of farm, business, and other property, 1990: Total
,→ market value of all of the real estate, assets in the business(es),
,→ farm operation(s) in 1990,
Total market value of farm, business, and other property, 1996: Total
,→ market value of all of the real estate, assets in the business(es),
,→ farm operation(s) in 1996,
Market Value of vehicles respondent/spouse own, 1985: Total market value
,→ of all vehicles including automobiles that respondent/spouse owned in
,→ 1985,
Market Value of vehicles respondent/spouse own, 1990: Total market value
,→ of all vehicles including automobiles that respondent/spouse owned in
,→ 1990,
Market Value of vehicles respondent/spouse own, 96: Total market value of
,→ all vehicles including automobiles that respondent/spouse owned in
,→ 1996,
Total market value of items over $500, 1985: Total market value of all
,→ the other assets of the respondent that were worth more than $500 in
,→ 1985,
Total market value of items over $500, 1990: Total market value of all
,→ the other assets of the respondent that were worth more than $500 in
,→ 1990,
Total market value of items over $500, 1996: Total market value of all
,→ the other assets of the respondent that were worth more than $500 in
,→ 1996,
Total net family income, previous calendar year, 1979: Total net family
,→ income for the previous calendar year (1978) (recorded in 1979),
Total net family income, previous calendar year, 1985: Total net family
,→ income for the previous calendar year (1984) (recorded in 1985),
Total net family income, previous calendar year, 1989: Total net family
,→ income for the previous calendar year (1989) (recorded in 1989),

表内文字对照（数值与原始行列保持不变）：
Type of residence respondent is living in → 受访者所居住的居住类型
Type of residence → 居住类型
respondent is living in the → 受访者居住在
contains one of these values → 包含以下值之一
ABOARD SHIP → 在船上
BARRACKS → BARRACKS
BACHELOR → 学士课程
OFFICER QUARTERS → 警官宿舍
DORM → DORM
FRATERNITY → 兄弟会
SORORITY → 姐妹情谊
HOSPITAL → 医院
JAIL → 监狱
OTHER TEMPORARY → 其他临时项目
QUARTERS → 宿舍
OWN DWELLING UNIT → 自有住宅单元
ON-BASE MIL FAM HOUSING → 基于军事家庭住房
OFF-BASE MIL FAM HOUSING → 离垒球衣家居
ORPHANAGE → ORPHANAGE
RELIGIOUS → 宗教
INSTITUTION → 机构
OTHER INDIVIDUAL QUARTERS → 其他个人考核期
PARENTAL → 父母
HHI CONDUCTED WITH PARENT → HHI 由家长进行
R IN PARENTAL HOUSEHOLD → 在父母家中
Family net wealth → 家庭净财富
Total Net Wealth for Family → 家庭总净财富
Created by summing → 通过求和创建
all asset values and subtracting all debts for the year → 全年所有资产价值减去所有债务
key data point) → 关键数据点）
Created by summing all asset values and subtracting all debts for the → 通过将所有资产价值相加并减去所有债务来计算得出
year → 年份
Market value of residential property respondent/spouse own → 住宅房产受访者/配偶拥有的市场价值
Market → 市场
value of residential property that respondent/spouse owned in → 受访者/配偶拥有的住宅资产价值
Total market value of farm → 农场的总市场价值
business → 商业
and other property → 以及其他属性
Total → 总数
market value of all of the real estate → 所有房地产的市场价值
assets in the business(es) → 各业务中的资产
farm operation(s) in → 农场经营
Market Value of vehicles respondent/spouse own → 受访者/配偶所拥有的车辆的市场价值
Total market value → 总市场价值
of all vehicles including automobiles that respondent/spouse owned in → 所有车辆中，包括受访者/配偶拥有的汽车
Total market value of → 大语言模型的总市场价值
all vehicles including automobiles that respondent/spouse owned in → 所有车辆，包括受访者/配偶拥有的汽车
Total market value of items over → 物品的总市场价值超过
Total market value of all → 所有产品的总市场价值
the other assets of the respondent that were worth more than → 被答方的其他价值较高的资产
Total net family income → 家庭总净收入
previous calendar year → 上一日历年度
Total net family → 家庭净收入总额
income for the previous calendar year ( → 上一日历年的收入（
recorded in → 记录于
```

[原文第 81 页的完整图表与公式](assets/original-page-081.jpg)

作为会议论文发表在 ICLR 2026 上

自上次访谈以来，1989年是否有更多的资金被投入或取出于 R/spouse 储蓄账户：这是一个分类变量，表示自1989年上次访谈以来是投入还是取出更多资金。它包含四个值：1：投入更多资金，2：取出更多资金，3：无变化，4：无储蓄。受访者/配偶自1989年上次访谈以来存入储蓄的净金额：即受访者/配偶自1989年上次访谈以来存入储蓄的现金总额。受访者/配偶自1989年上次访谈以来从储蓄中取出的净金额：即受访者/配偶自1989年上次访谈以来取出的现金总额。

查询：时间偏好率的增加会导致更高的BMI吗？在最终答案中，请输出一个包含两个键的JSON格式内容：

{ 'hypothesis': 科学假设, 'workflow': 工作流程总结 }

其中，科学假设是一个自然语言假设，由提供的数据集推导得出；该假设应明确说明假设背景、所选变量以及这些变量之间的关系（如有），并包含任何统计显著性信息。请根据需要包含所有数值信息以支持该假设。

并且

工作流摘要是对从数据加载开始到最终假设形成的完整工作流的总结。

确保加载数据集以进行分析（或委托给智能体处理）。

H.10 E2E-B E N C H

H.10.1 示例问题

你是一个自主智能体，负责执行以下研究任务：→任务：

**任务定义**： ================

**名称**：simple-dag-enhancement
**简短描述**：通过简单的基于内容的边选择机制来增强静态 DAG-ERC 模型，从而提升对话中的情感识别能力。
**详细描述**：本研究通过实施一种基本的基于内容意识的边选择机制，对 DAG-ERC 模型中的静态 DAG 结构进行简化改进。我们并未开发完全动态的 DAG 构建方法，而是专注于根据话语之间的简单内容相似性指标，用少量额外边来扩充现有的静态 DAG。
这种方法在保持原始 DAG-ERC 模型的核心结构的基础上，→能够捕捉到额外的相关关联，→从而可能提升情感识别性能。

[原文第 82 页的完整图表与公式](assets/original-page-082.jpg)

作为会议论文发表在 ICLR 2026 上

**待探索的假设**：基于话语之间的内容相似性，在静态 DAG 结构上增加少量额外的边，将提升情感识别性能，相比原始静态 DAG-ERC 模型，尤其适用于那些重要的上下文关系超出直接对话历史的对话场景。

使用的指标：主要指标为加权平均 F1 分数以及情感识别领域的微平均 F1 分数（排除多数类样本），这与原始 DAG-ERC 论文中的方法一致。我们还将分析额外边的数量和分布，以了解我们的改进所带来的影响。

**基线模型**：我们将把我们的改进版 DAG-ERC与以下模型进行对比：(1) 具有静态规则的原始 DAG-ERC；以及(2) 全连接图基线模型，在该模型中所有话语都与所有之前的话语相连（受固定窗口大小限制）。**研究思路变量**：独立变量包括 DAG构建方法（原始静态 DAG、带有内容基边的改进版 DAG）、添加边的相似度阈值，以及每句话可添加的最大边数。控制变量包括特征提取方法、情感识别模型架构以及评估指标。
依赖变量为情绪识别性能。**研究思路设计**：在 DAG-ERC 模型中对静态 DAG 结构进行简单改进，通过在话语之间添加基于内容的边来提升模型性能。其目的是捕捉更多相关的连接，从而改善情绪识别效果，同时保持原模型的简洁性和高效性。**1. 数据准备**：- 使用 IEMOCAP 数据集，遵循原 DAG-ERC 论文中的预处理步骤。- 选取一小部分数据（例如 20 次对话）用于试点研究。**2.
增强型有向无环图构建**：- 从使用《→ DAG-ERC》论文中的原始规则构建的静态有向无环图开始（基于说话者身份和位置关系）。- 对于每条话语，利用如 RoBERTa 嵌入之间的余弦相似度等简单的度量方法，计算其内容与所有之前话语的内容相似性（在合理的窗口内，例如 10 条话语）。- 如果前序话语与当前话语的相似性超过阈值（例如 0.8），且前序话语在静态有向无环图中尚未连接，则添加额外的边。- 限制每条话语中额外边的数量（例如最多 3 条），以保持稀疏性。**3**
实施细节**：- 将 RoBERTa-Base 作为情感识别模型和相似度计算模型的特征提取器。- 在训练情感识别模型之前，将增强的 DAG 构建作为预处理步骤实施。- 尝试不同的相似度阈值（例如 0.7、0.8、0.9）以及最大额外边数（例如 1、3、5）。- 对于情感识别任务，直接使用未经修改的原始 DAG-ERC 模型架构。**4.
训练与评估**：- 使用增强后的 DAG 结构，在 IEMOCAP 数据集上训练模型。- 将该模型的性能与原始 DAG-ERC 模型及全连接基线模型进行对比。- 分析由该增强机制添加的额外边的数量与分布情况。

[原文第 83 页的完整图表与公式](assets/original-page-083.jpg)

作为会议论文发表在 ICLR 2026 上

- 找出具体案例，说明增强后的有向无环图为何能产生正确的 → 预测结果，而原始有向无环图却无法得出这些正确结果。**5. 输出与分析**： - 保存训练好的模型及其性能指标。 - 针对若干示例对话，生成原始有向无环图与增强后有向无环图的结构可视化图表。 - 分析额外边数量与 → 情感识别性能之间的关系。 - 研究哪种类型的对话最能从增强后的 → 有向无环图结构中获得优势。

**表格与文字对照**

```text
For the pilot experiment, implement the enhanced DAG construction
,→ approach on 20 conversations from the IEMOCAP dataset to validate the
,→ approach before scaling to the full experiment. Focus on a single
,→ similarity threshold (e.g., 0.8) and a single maximum number of
,→ additional edges (e.g., 3) for simplicity.
------ end of task definition -----
NOW: Please perform this task and produce four results:
1. A report, describing the results of your research. The report should
,→ include, among other things, the following parts: Title, Abstract,
,→ Introduction, Approach, Experiments, Results, Conclusion,
,→ References.
2. The code you wrote to perform the research.
3. A trace/log of your research. The trace should give a step-by-step
,→ description of the actions the agent (you) took, e.g., searching the
,→ literature, writing and executing code, analyzing results. The trace
,→ should also include the results of those actions, e.g., the papers
,→ found, the experimental results from code execution, etc.
4. Any other research artifacts (datasets, analyses, results, etc.) that
,→ you generated, to substantiate your report. If these artifacts (e.g.,
,→ a dataset) are large, only show part of them but enough to convey
,→ their contents.
These results will be used to assess how well you performed the task.

表内文字对照（数值与原始行列保持不变）：
For the pilot experiment → 对于试点实验
implement the enhanced DAG construction → 实施增强版有向无环图构建
approach on → 方法论
conversations from the IEMOCAP dataset to validate the → 来自 IEMOCAP 数据集的对话，用于验证
approach before scaling to the full experiment → 在全面开展实验之前进行方法探索
Focus on a single → 专注于单一目标
similarity threshold (e → 相似度阈值 (e
and a single maximum number of → 以及单个最大数量
additional edges (e → 额外边（e
for simplicity → 为了简单起见
end of task definition ----- → 任务定义结束 -----
NOW → 现在
Please perform this task and produce four results → 请完成此任务并生成四个结果
A report → 报告
describing the results of your research → 描述您的研究结果
The report should → 报告应当
include → 包括
among other things → 除其他事项外
the following parts → 以下部分
Title → 标题
Abstract → 摘要
Introduction → 引言
Approach → 方法
Experiments → 实验
Results → 结果
Conclusion → 结论
References → 参考文献
The code you wrote to perform the research → 你编写用于开展研究的代码
A trace/log of your research → 您研究的记录/日志
The trace should give a step-by-step → 该追踪应提供逐步骤的说明
description of the actions the agent (you) took → 智能体（您）所采取的行动描述
searching the → 检索
literature → 文献
writing and executing code → 编写和执行代码
analyzing results → 分析结果
The trace → 追踪记录
should also include the results of those actions → 还应包含那些行动的结果
the papers → 这些论文
found → 发现
the experimental results from code execution → 代码执行的实验结果
etc → 等等
Any other research artifacts (datasets → 其他任何研究成果（数据集）
analyses → 分析
results → 结果
that → 那个
you generated → 你生成了
to substantiate your report → 为你的报告提供依据
If these artifacts (e → 如果这些工件（e
a dataset) are large → 一个数据集）是庞大的
only show part of them but enough to convey → 仅展示其中的部分内容，但足以传达信息
their contents → 其内容
These results will be used to assess how well you performed the task → 这些结果将用于评估您完成该任务的效果
```

请以以下 JSON 结构返回您的答案（一个字典 ，→，包含一个顶层键 `results`，该键是一个字典 ，→，包含 `report`、`code`、`trace` 和 `artifacts` 这些键，格式与下方描述完全一致）： ```

{ "results": { "report"(str): <report>, "code"(list): [ {"filename"(str): <filename1>, "code"(str): <code1>}, {"filename"(str): <filename2>, "code"(str): <code2>},... ], "trace"(str): <trace>, "artifacts"(list): [ {"filename"(str): <filename1>, "artifact"(str): <artifact1>}, {"filename"(str): <filename2>, "artifact"(str): <artifact2>},... ] } } ``` 其中 <report> 是一个多行字符串，包含报告内容；<trace> 是一个多行字符串，包含智能体在完成任务过程中行为的追踪（或追踪摘要）；而 <artifacts> 则是研究产生的成果（如创建的数据集等）

[原文第 84 页的完整图表与公式](assets/original-page-084.jpg)

作为会议论文发表在 ICLR 2026 上

H.11 E2E-B E N C H -H A R D

H.11.1 示例问题

您是一个自主智能体，负责执行以下研究任务：任务定义：================ 名称：自适应推理增强 简短描述：结合基于复杂性的提示与模仿演示学习，以提升语言模型在未见任务上的泛化能力。待探索的假设：将基于复杂性的提示与模仿演示学习相结合，能够增强语言模型的泛化能力，通过动态调整推理复杂度和演示选择，从而在未见任务上获得更好的表现。

--- 关键变量：自变量：基于复杂性的提示与模仿示范学习的结合

因变量：大语言模型在未见任务上的泛化能力

对比组：四种条件：基准（标准提示）组、仅 CBP 组、仅 IDL 组以及整合组（CBP+IDL）

基线/对照组：无 CBP 或 IDL 的标准提示方法

背景/环境：复杂的多步骤推理问题

假设：基于复杂度的提示方法通过关注高复杂度理由来提升推理能力，而模仿演示学习则通过模仿行为来强化学习效果

关系类型：因果（整合“将提升”能力）

样本量：语言模型

时间范围：未指定

测量方法：主要指标：在未见任务上的准确率；次要指标：推理复杂度、演示效果以及响应质量

---

[原文第 85 页的完整图表与公式](assets/original-page-085.jpg)

作为会议论文发表在 ICLR 2026 上

详细描述：本研究探讨了基于复杂性的提示与模仿演示学习相结合的方法，以提升大语言模型在未见过的任务上的泛化能力。基于复杂性的提示涉及根据推理复杂度选择提示，引导模型通过复杂的推理链条进行思考。模仿演示学习则通过模仿人类审核策略、为新问题选择类似的示例以及基于检索到的示例重新回答来强化学习过程。
该假设认为，结合这些方法能够让模型动态调整其推理复杂度和演示选择策略，从而在未见过的任务上取得更好的表现。这种方法通过提供一种新颖的方法组合来提升模型的适应性和推理能力，从而弥补了现有研究的不足。预期的结果是，模型通过利用复杂的推理链条和有效的演示选择，在未见过的任务上会表现得更好。
这项研究具有重要意义，因为它为提升语言模型的推理能力提供了新思路，有望实现更稳健且更具适应性的人工智能系统。

--- 关键变量：[基于复杂度的提示设计]( https://www.semanticscholar.org/paper/f48e0406bfac8025b36982c94a9183968378587f): ,→ 基于复杂度的提示设计是指根据推理步骤的复杂性来选择提示。这种方法通过关注高复杂度的推理依据，能够提升模型在需要深度推理的任务中的表现。其过程包括对不同推理路径进行投票，以确定最复杂且最具信息量的路径。这些提示引导模型完成复杂的推理流程，从而确保对复杂任务的有效处理。
该变量至关重要，因为它直接影响模型处理复杂推理任务的能力，进而提升其泛化能力。

[模仿演示学习]( https://www.semanticscholar.org/paper/fdbdcc3a65dfd6f258c533fd12d58bbfcab15bc3): ,→ 模仿演示学习通过模仿人类审核策略来强化学习过程。其过程包括选择与新问题最相似的示例，并根据该示例的回答步骤进行重新回答。这种方法强调提示与演示之间的互动，通过明确的模仿来巩固学习效果。它需要一种机制来筛选相似示例并重新回答问题，从而提升模型从演示中学习的能力。
该变量至关重要，因为它通过通过模仿巩固已知知识来强化模型从示范中进行泛化的能力。

---

[原文第 86 页的完整图表与公式](assets/original-page-086.jpg)

作为会议论文发表在 ICLR 2026 上

研究思路设计：该假设将通过整合基于复杂性的提示与模仿示范学习，利用智能体能力来实现。流程始于定义一组需要复杂推理的任务。基于复杂性的提示将通过设计包含高复杂度推理链的提示来应用，这些提示将引导模型完成复杂的推理步骤，从而有效处理复杂的任务。模仿示范学习则通过开发一种机制来选择与新问题相似的示例来实施。
这涉及构建一个系统，该系统能够基于语义相似性识别相似的示例，并利用这些示例来重新回答问题，从而强化学习过程。这些方法的整合将在提示层面进行，其中基于复杂度的提示将与模仿演示策略相结合，以提升模型的推理能力。
数据流将涉及向模型输入基于复杂度的提示，并采用模仿演示机制来筛选和重新回答问题。预期的结果是，通过利用复杂的推理链和有效的演示选择，模型在未见过的任务中表现会更好。这种方法具有创新性，因为它结合了两种不同的方法来提升语言模型的推理能力，为改善人工智能系统的适应性和性能提供了新视角。

--- 评估流程：请开展一项实验，验证以下假设——将基于复杂性的提示技术与模仿示范学习相结合，能够提升大语言模型在未见过的推理任务上的泛化能力。该实验应比较四种不同的条件。

1. 基准组：无 CBP 或 IDL 的标准提示方法
2. 仅 CBP 组：仅使用基于复杂度的提示方法
3. 仅 IDL 组：仅使用模仿示范学习方法
4. 综合组（CBP+IDL）：结合两种方法的实验组

实验应包含以下组成部分：

## 数据集 使用如 2WikiMultiHopQA 这样的推理任务数据集，其中包含复杂的多步骤推理问题。该数据集应划分为训练集（60%）、验证集（20%）和测试集（20%）。测试集将作为最终评估的“未见任务”进行使用。

## 试点模式实现 实现一个全局变量 PILOT_MODE，包含三种可能的设置：MINI_PILOT、PILOT 或 FULL_EXPERIMENT。
- MINI_PILOT：使用训练集中的 10 个问题用于开发，使用验证集中的 5 个问题用于评估。
- PILOT：使用训练集中的 100 个问题用于开发，使用验证集中的 50 个问题用于评估。
- FULL_EXPERIMENT：使用整个训练集用于开发，使用整个测试集用于最终评估。

以 MINI_PILOT 开始，若成功则继续执行 PILOT。在人工验证 PILOT 结果之前，请勿运行 → FULL_EXPERIMENT。

## 基于复杂度的提示模块 实现一个模块：1. 为训练中的每个问题生成多条推理路径，→ 集合 2. 采用投票机制确定最复杂且，→ 最具信息量的推理路径

[原文第 87 页的完整图表与公式](assets/original-page-087.jpg)

作为会议论文发表在 ICLR 2026 上

3. 生成引导模型进行这些复杂推理的提示词，→ 链 4. 将这些基于复杂性的提示词存储起来以供后续使用

## 模仿演示学习系统 一种系统：1. 建立包含详细推理过程及训练集中的步骤的问答对数据库 2. 针对新问题，计算语义相似度以找出数据库中最相似的示例 3. 检索最相似的示例及其推理步骤 4. 构建包含这些示例的提示词，以引导模型回答新问题

## 综合方法（CBP+IDL）通过以下方式实现 CBP 与 IDL 的整合：1. 使用 CBP 为问题生成复杂的推理链；2. 使用 IDL 筛选具有对应推理步骤的类似示例；3. 将两者结合到一个统一的提示中，包含复杂的推理指导及类似示例；4. 实施自适应机制，根据问题的特点调整给予 CBP 与 IDL 的权重

## 评估 使用以下指标对所有四种条件进行评估：1. 主要指标：未知任务上的准确率（正确回答问题的比例） 2. 次要指标：- 推理复杂度（回复中平均推理步骤数）- 演示效果（所选示例与目标问题之间的语义相似性）- 回复质量（推理的连贯性、相关性和逻辑性），仅当适用时才使用 ROSCOE

## 统计分析 进行统计分析以判断不同条件之间的差异是否具有显著性：1. 在不同条件下进行配对 t 检验 2. 针对每次比较计算效应量（Cohen’s d） 3. 进行自举重采样以建立置信区间

## 日志记录与报告 实施全面的日志记录，包含：1. 每种条件下生成的所有提示语 2. 每个问题的模型回复 3. 每种条件的评估指标 4. 统计分析结果 5. 成功与失败案例示例

最终报告应包含：1. 各条件的结果总结 2. 不同条件之间差异的统计显著性 3. 分析综合方法何时以及为何表现更好或更差 4. 进一步改进的建议

## 实现细节 - 使用 NLTK 进行文本处理与分词 - 使用 scikit-learn 进行语义相似度计算及统计分析 - 使用大语言模型（如 GPT-4）生成回复 - 全程实施正确的错误处理与日志记录

请先以 MINI_PILOT 模式运行实验，如果成功则再切换到 PILOT 模式。未经人工验证前，请勿进行 FULL_EXPERIMENT 操作。

[原文第 88 页的完整图表与公式](assets/original-page-088.jpg)

作为会议论文发表在 ICLR 2026 上

---

------ 任务定义结束 ----- 现在：请完成此任务并生成四个成果：1. 一份报告，说明你的研究结果。该报告应包含以下部分：标题、摘要、→引言、方法、实验、结果、结论、→参考文献。2. 你用于进行研究的代码。3. 你的研究记录/日志。该记录应提供智能体（你）所采取的步骤式描述，例如检索→文献、编写与执行代码、分析结果。
记录中还应包含这些操作的结果，例如发现的论文、代码执行的实验结果等。4. 您生成的任何其他研究成果（数据集、分析、结果等），以支撑您的报告。如果这些成果较大，只需展示其中一部分即可，但必须足以体现其内容。这些结果将用于评估您完成任务的程度。

请以以下 JSON 结构返回您的答案（一个字典 ，→，包含单个顶层键 `results`，该键是一个字典 ，→，包含 `report`、`code`、`trace` 和 `artifacts` 四个键，格式与下方描述完全一致）：``` { "results": { "report"(str): <报告内容>, "code"(list): [ {"filename"(str): <filename1>, "code"(str): <code1>}, {"filename"(str): <filename2>, "code"(str): <code2>},... ], "trace"(str): <追踪信息>, "artifact"(str): [ {"filename"(str): <filename1>, "artifact"(str): <工件内容1>}, {"filename"(str): <filename2>, "artifact"(str): <工件内容2>},... ] } } ```其中 <报告> 是一个多行字符串，包含报告内容；<追踪信息> 是一个多行字符串
包含大语言模型在解决任务时智能体的行为记录（或记录摘要），而这些成果则是研究的产物（如创建的数据集等）

