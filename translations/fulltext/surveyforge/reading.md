# SurveyForge：自动综述写作中的大纲启发式、记忆驱动生成与多维评价

SurveyForge: On the Outline Heuristics, Memory-Driven Generation, and Multi-dimensional Evaluation for Automated Survey Writing

Yan, Xiangchao; Feng, Shiyang; Yuan, Jiakang; Xia, Renqiu; Wang, Bin; Zhang, Bo; Bai, Lei

> 非官方机器初译，正文尚未逐段精校。图表保留原文内容，图内英文未另行翻译；有 HTML 原文的公式按原式排版。PDF 提取版保留对应原页，点击缩略图放大核对图表与公式。

原文版本：ACL 2025 / 2025.acl-long.609 · [原始来源](https://aclanthology.org/2025.acl-long.609/) · [中文 PDF](../../../output/pdf/surveyforge-zh-reading.pdf)

[原文第 1 页的完整图表与公式](assets/original-page-001.jpg)

## 摘要

综述论文在科学研究中发挥着重要作用，尤其是在研究出版物迅速增长的背景下。近来，研究者开始使用大语言模型自动生成综述，以提高效率。然而，大语言模型生成的综述与人工综述之间仍存在显著的质量差距，特别体现在大纲质量和引用准确性方面。为缩小这些差距，我们提出 SURVEYFORGE：它首先分析人工大纲的逻辑结构，并参考检索到的领域相关文章生成大纲。随后，借助学术导航智能体从记忆中检索到的高质量论文，SURVEYFORGE 自动生成并完善文章内容。为了进行全面评价，我们还构建了 SurveyBench，其中包含 100 篇人工撰写的综述，用于胜率比较，并从参考文献、大纲和内容质量三个维度评价 AI 生成的综述。实验表明，SURVEYFORGE 能够优于 AutoSurvey 等先前工作。

1 引言
随着科学技术迅速发展，发表的研究论文数量呈指数式增长，人工智能（AI）等快速演进领域尤其如此。文献的快速增长使研究者越来越难以深入了解某个特定研究领域。综述论文能够系统整合已有研究，全面介绍特定领域的发展和趋势，因此已成为科研周期的重要起点。然而，传统人工综述写作要求研究者查阅大量文章，［句子在后续原文中继续］。

页脚中的作者贡献、通讯作者标识及会议出版信息保留原文，完整信息见原 PDF。

/datasets/U4R/文献综述

寻找草稿，制定关于参与学术相关参考文献的文献综述文章写作的大纲大纲

((cc)) OOuuttlliinnee 宽度

宽度：• 过宽 → 内容无关 • 过窄 → 覆盖不足 深度：• 过深 → 细节过多 • 过浅 → 分析不足

计算语言学（第1卷：长文），第12444–12465页 计算语言学讨论 宽高 ((bb)) RReeffeerreenncceess rreelleevvaanntt rreeffeerreenncceess rreeffeerreenncceess ccoovveerreedd bbyy AAII ccoorree rreeffeerreenncceess •• RReeffeerreenncceess ccoovveerreedd bbyy AAII mmaayy ccoonnttaaiinn iirrrreelleevvaanntt oonneess •• RReeffeerreenncceess ccoovveerreedd bbyy AAII mmaayy iinncclluuddee oonneess tthhaatt aarree rreellaatteedd bbuutt nnoott ccoorree ttoo tthhee ffiieelldd yevruS detareneG-IA ni segnellahC ((aa)) TThhee RReegguullaarr PPrroocceessss ooff WWrriittiinngg aann AAccaaddeemmiicc SSuurrvveeyy PPaappeerr 图1：与……相比
由人类撰写的文献综述与由人工智能生成的文献综述面临两个主要挑战。首先，在大纲方面，这些文献往往缺乏连贯的逻辑性和合理的结构安排。其次，在参考文献方面，它们通常无法包含真正相关且具有影响力的学术成果。这一过程耗时较长，且难以及时掌握该领域的最新进展。受大语言模型（LLM）在性能与能力上的显著进步所启发（Achiam等，2023；Anthropic，2024；Touvron等，2023；Cai等，2024），研究人员开始利用这些模型自动进行文献审查并生成文献综述论文。
作为大语言模型，GPT-Researcher（Assafelovic，2023）根据从多个在线学术数据库中检索到的与主题相关的文章摘要生成文献综述。为了识别与综述主题更相关的文献，AutoSurvey（Wang等人，2024c）基于arXiv构建本地文献数据库，为每篇文献建立向量索引，并同时生成各子章节的内容。为了进一步使大语言模型生成的内容写作风格与人类风格保持一致，OpenScholar（Asai等人，2024）提出了一个大规模科学文献数据集，并对该数据集进行了微调，共包含444篇文献

[原文第 2 页的完整图表与公式](assets/original-page-002.jpg)

基于该数据集的大语言模型被用于构建专门用于回答科学问题的模型。这些自动生成文献综述的方法大多遵循传统的学术文献综述写作流程：从文献检索开始，到大纲撰写，最终完成学术写作，如图1所示。然而，尽管上述方法取得了令人满意的效果，仍存在若干重大挑战。首先，人工智能生成的文献综述结构往往缺乏连贯性，且组织混乱。例如，如图所示。
1. 现有研究可能在宽度与深度方面存在结构失衡问题，例如章节划分过于详细或关键主题覆盖不足。其次，由人工智能生成的文献综述往往未能引用重要的相关文献，从而降低了综述的整体深度与价值。如图1所示，它们可能引用无关文献，而忽视该领域的重要贡献。最后，对人工智能生成的文献综述的评估主要依赖大语言模型，仅关注长篇内容的整体质量。这种方法

缺乏对大纲质量、参考文献相关性及结构连贯性等关键方面的细致分析。此外，由于缺乏客观评估标准，难以建立统一的质量基准，也无法有效比较不同方法。为应对上述挑战，我们提出了一种用于生成文献综述的自动化框架——SURVEYFORGE，该框架包含两个阶段：大纲生成与内容生成。
在第一阶段中，SURVEYFORGE采用启发式学习方法，利用人类撰写的文献与结构模式来生成语义丰富且条理清晰的大纲。在第二阶段中，一个基于记忆的学者导航智能体配合时间感知重新排序引擎，对每个小节进行高质量文献的检索。

然后，将各章节的内容整合并完善，形成一篇连贯且全面的文献综述。

此外，我们构建了 SurveyBench 这一多维基准测试平台，以有助于对自动化文献综述生成系统进行系统的评估。

大量结果凸显了其独特的优势

在多个维度上，SURVEYFORGE均表现出优异表现，包括能够生成结构合理的大纲、检索高质量且高度相关的参考文献，以及生成连贯、全面的内容。SURVEYFORGE不仅提供了可量化的成果

在这些领域取得了进步，同时也展现了其在连接人工智能生成与人工撰写文献综述之间的差距方面的卓越能力。这些发现凸显了它作为自动化文献综述生成强大框架的潜力，为该领域的质量与可靠性设定了新的标准。
我们的贡献可以总结如下。• 我们提出了 SURVEYFORGE，这是一种用于生成高质量学术文献综述的新颖自动化框架。• 我们提出了一种启发式大纲生成方法以及一种基于记忆的学者导航智能体，二者结合可确保结构合理的文献综述框架与高质量的内容生成。• 为了便于客观评估，我们建立了 SurveyBench 综合基准测试，该测试包含可用于衡量大纲质量、参考文献质量和内容质量的量化指标。

质量。

2 相关研究：自主科学发现。随着大语言模型的发展（Achiam等，2023；An-

Thropic, 2024；Chen等人，2024a），越来越多的研究人员开始探索大语言模型在自主科学发现方面的潜力（Xia等人，2024b；Li等人，2024；Xia等人，2024a；Huang等人，2024；Ghafarollahi和Buehler，2024；Chen等人，2024b）。多项研究（Li等人，2024；Hu等人，2024a；Kumar等人，2024；Wang等人，2024b；Su等人，2024）致力于利用大语言模型实现新的科学概念生成。例如，COI-Agent（Li等人，2024）提出了一种创新的链式结构文献组织框架。
SCIPIP（Wang等人，2024b）提出了一种混合方法，结合基于文献的生成与头脑风暴式生成，从而提升生成思路的新颖性与可行性。除了这些具体应用之外，研究人员还开发了用于科学发现的综合系统。AI-Scientist（Lu等人，2024）设计了一个涵盖思路生成、实验设计与论文写作的完整流程。最近，Dolphin（Yuan等人，2025）开发了一种由大语言模型驱动的闭环框架，以提高科学研究的自动化水平。

自动化文献综述生成。随着科学论文的迅速增多，研究人员追踪特定领域的发展变得日益困难。早期方法 445

[原文第 3 页的完整图表与公式](assets/original-page-003.jpg)

输入 T M La u n lt g i u m a o g d e a M l L o a d r e g ls e 具身人工智能

第一阶段：大纲生成论文主题文献综述数据库数据库

RAG 大语言模型

论文大纲优化与内容优化原始参考文献综述检查……最终生存报告数据库调查启发式大纲生成主题RAG相关论文相关文献综述C A h b T u s i n t t r l k e a - c 1 t……C A h b T u s i n t t r l k e a - c N t L O e u v t e li l n -1 e……L O e u v t e li l n -1 e大语言模型大纲一级版本I. 引言……II. 方法V. 评估III. 数据集VI. 应用……VIII.
结论 RAG 相关文献 相关文献综述 S A e b c T s t i t t i r l o e a n c - t I …Sec A ti b T To s i n t t r l - e a V c I t II O A ut L li L ne … O A ut L li L ne repaP esabataD 数据库文献综述 LLM-Parallel 大纲 二级 S S u e b c s t e i c o t n io -I n S S u u S b b e s s c e e t c c i t t o i i o o n n n -I 2 2 I.. 1 2 S S u u S b b e s s c e e t c c i t t o i i o o n n n - I 3 3 I.. 1 2 I … S S e u c b t s io ec n t - i V on II 图2：SURVEYFORGE的概述。框架与内容写作。
在大纲生成阶段，通过利用与主题相关的文献来构建结构合理的大纲；内容写作阶段，由大语言模型根据记忆功能对每个小节进行导航，而大语言模型则生成各部分的内容，从而形成连贯且全面的文献综述。（Hoang和Kan，2010；Hu和Wan，2014；Jha等，2015；Chen和Zhuge，2019）主要依赖内容模型来选择和整理论文中的句子，往往导致输出结果缺乏一致性且难以阅读。Sun等人（Sun和Zhuge，2019）引入了一种模板树结构，该结构基于节点递归生成内容，从而提升了连贯性，但仍具有局限性。
认识到需要更灵活且连贯的解决方案，大语言模型的出现为增强自动化文献综述生成提供了新机遇。

研究人员开始利用大语言模型来促进高效的文献理解与综述工作（Wang等，2024c；Hu等，2024b）。Zhu等（Zhu等，2023）提出了一种用于文献综述的层级目录生成新任务，并提供了相应的语义与结构评估指标，但该方法仅适用于基于固定参考文献的大纲生成。AutoSurvey（Wang等，2024c）提出了一种基于大语言模型的两阶段综述生成方法，但未能关注人类学术写作风格及关键参考文献的分析，而这些因素对于生成高质量的文献综述至关重要。
随后，HiReview（Hu等，2024b）引入了一种基于分类体系的框架，用于分层探索文献关系，从而提升大语言模型对不同文献间关联的理解能力。然而，该框架仅依赖现有文献综述中的2跳引用网络而非常见被引用的论文，这限制了其更广泛的应用范围。3 方法 在本节中，我们提出SURVEYFORGE这一基于大语言模型的新型框架，用于自动处理124

**表格与文字对照**

```text
Topic SANA: Scholar Navigation Agent
AI for Science ... Outline
I. Introduction
Paper II. Method
Stage 2: Content Generation Database 2 2 . . 1 2 M Pr o e d -t a r l a it i y n e e d n c L o L d M er
2.3 Instruction Tuning
Paper Outline Parallel MemoryPaperI L d itera P t a u p r er e Id III. T I r V ai . n D i … n a g ta S s t e r t ategy
MetaData …MetaData V. Evaluation
Title Title VI. Applications
Content Content VIII. Conclusion
SANA
LLM-Parallel Subqueries
…
Combination Outline 2 Q . 1 1 : M U o n d im al o it d y a e l n fe c a o t d u e r r e extraction
using pre-trained models
Q2: Modality-specific adapters
Literature a Q n 3 d : p A r l o i j g e n c i t n io g n a l n a d y e sy rs n chronizing
& Evaluatio R n aw Survey MemoryP M T C a i o t e p l n t e e a te r D I n d a t ta … P M T C a i o t e p l n t e e a te r D I n d a t ta d 2 Q Q i . 1 2 2 ff : : e P D E r r e n e e n c c - t t o o r m d d a e e i o n r r d - - e D a o d l n e i … t L l c i y e o L s L d M e L r M L s LMs
Reference
Outline
n v a e l y Benchmark Content Sub-queries Content Reference
ework consists of two main stages: Outline Generation
, SURVEYFORGE utilizes heuristic learning to generate
ature and structural patterns from existing surveys. In the
ation Agent (SANA) retrieves high-quality literature for
subsection. Finally, the content is synthesized and refined
retrieving relevant literature and generating comprehensive survey papers. As shown in Fig. 2, our
framework consists of two main stages: outline generation stage and content writing stage. The outline
generation stage leverages both research papers and
existing survey structures through a heuristic learning mechanism, producing academically structured
outlines. The content generation stage employs a
memory-driven scholar navigation agent with key
paper retrieval strategy to synthesize the content of
the survey. Finally, we propose a benchmark SurveyBench for automated survey generation tasks.
The details are elaborated in Sec. 3.1, Sec. 3.2 and
Sec. 3.3, respectively.
3.1 Heuristic Outline Generation
The outline of a survey paper is crucial as it defines
the logical organization and knowledge structure
of the entire work. While LLMs excel at generating textual content, they often fall short in crafting well-structured survey outlines. Common issues include a lack of hierarchical depth, insufficient theoretical grounding, and a tendency toward
report-like structures rather than scholarly frameworks. These limitations can be attributed to the
limited understanding of academic writing conventions and the organizational principles underlying
survey design. To address these challenges, we
propose a top-down heuristic learning approach,
enabling LLMs to understand the established theoretical frameworks and organizational paradigms
from human-written survey outlines. Our approach
is underpinned by two domain-specific knowledge
bases: a Research Paper Database, which encodes
446

表内文字对照（数值与原始行列保持不变）：
Topic SANA → 主题分析
Scholar Navigation Agent → 学者导航智能体
AI for Science → 科学领域的人工智能
Outline → 大纲
Introduction → 引言
Paper II → 论文二
Method → 方法
Stage → 阶段
Content Generation Database → 内容生成数据库
M Pr o e d -t a r l a it i y n e e d n c L o L d M er → M Pr o e d -t a r l a it i y n e e d n c L o L d M er
Instruction Tuning → 指令调优
Paper Outline Parallel MemoryPaperI L d itera P t a u p r er e Id III → 文献综述大纲 并行内存 论文一 逻辑迭代过程 作者 III
T I r V ai → T I r V ai
n D i → n D i
n a g ta S s t e r t ategy → n a g ta S s t e r t ategy
MetaData → 元数据
MetaData V → 元数据 V
Evaluation → 评估
Title Title VI → 标题 第六条款
Applications → 应用
Content Content VIII → 内容 内容VIII
Conclusion → 结论
SANA → SANA
LLM-Parallel Subqueries → 大语言模型并行子查询
Combination Outline → 组合大纲
M U o n d im al o it d y a e l n fe c a o t d u e r r e extraction → M U o n d im al o it d y a e l n fe c a o t d u e r r e 提取
using pre-trained models → 使用预训练模型
Modality-specific adapters → 特定模态适配器
Literature a Q n → 文献综述 Q n
p A r l o i j g e n c i t n io g n a l n a d y e sy rs n chronizing → p A r l o i j g e n c i t n io g n a l n a d y e syrs n 时间确认
Evaluatio R n aw Survey MemoryP M T C a i o t e p l n t e e a te r D I n d a t ta → 评估研究文献综述 记忆能力 技术参数 应用案例
P M T C a i o t e p l n t e e a te r D I n d a t ta d → P M T C a i o t e p l n t e e a te r D 数据
Q Q i → Q Q i
e P D E r r e n e e n c c - t t o o r m d d a e e i o n r r d - - e D a o d l n e i → e P D E r r e n e e n c c - t t o o r m d d a e e i o n r r d - - e D a o d l n e i
t L l c i y e o L s L d M e L r M L s LMs → t L l c i y e o L s L d M e L r M L s LMs
Reference → 参考文献
n v a e l y Benchmark Content Sub-queries Content Reference → n v a e l y 基准测试内容子查询 内容参考
ework consists of two main stages → 工作包含两个主要阶段
Outline Generation → 大纲生成
SURVEYFORGE utilizes heuristic learning to generate → SURVEYFORGE利用启发式学习来生成
ature and structural patterns from existing surveys → 来自现有文献的文论与结构模式
In the → 在……中
ation Agent (SANA) retrieves high-quality literature for → 智能体（SANA）通过检索功能获取高质量文献
subsection → 小节
Finally → 最后
the content is synthesized and refined → 内容经过合成与优化处理
retrieving relevant literature and generating comprehensive survey papers → 检索相关文献并撰写全面的文献综述
As shown in Fig → 如图所示
our → 我们的
framework consists of two main stages → 该框架由两个主要阶段组成
outline generation stage and content writing stage → 大纲生成阶段与内容写作阶段
The outline → 大纲
generation stage leverages both research papers and → 生成阶段同时利用研究论文和
existing survey structures through a heuristic learning mechanism → 通过启发式学习机制构建现有的文献综述结构
producing academically structured → 生成具有学术结构的内容
outlines → 大纲
The content generation stage employs a → 内容生成阶段采用一种
memory-driven scholar navigation agent with key → 基于记忆的学者导航智能体及关键要素
paper retrieval strategy to synthesize the content of → 用于整合内容的文献检索策略
the survey → 该文献综述
we propose a benchmark SurveyBench for automated survey generation tasks → 我们提出了一种用于自动化文献综述任务的基准测试工具 SurveyBench
The details are elaborated in Sec → 具体细节在第 Sec 节中详述
Sec → 章节
and → 并且
respectively → 分别
Heuristic Outline Generation → 启发式大纲生成
The outline of a survey paper is crucial as it defines → 文献综述的大纲至关重要，因为它定义了
the logical organization and knowledge structure → 逻辑性组织与知识结构
of the entire work → 在整个研究工作中
While LLMs excel at generating textual content → 虽然大语言模型在生成文本内容方面表现出色
they often fall short in crafting well-structured survey outlines → 它们在制定结构合理的文献综述大纲方面往往难以达到预期效果
Common issues include a lack of hierarchical depth → 常见问题包括缺乏层级深度
insufficient theoretical grounding → 理论基础不足
and a tendency toward → 以及一种倾向
report-like structures rather than scholarly frameworks → 类似报告的结构，而非学术框架
These limitations can be attributed to the → 这些限制可以归因于……
limited understanding of academic writing conventions and the organizational principles underlying → 对学术写作规范及其背后的组织原则理解有限
survey design → 文献综述设计
To address these challenges → 为了应对这些挑战
propose a top-down heuristic learning approach → 提出一种自上而下的启发式学习方法
enabling LLMs to understand the established theoretical frameworks and organizational paradigms → 使大语言模型能够理解既定的理论框架与组织范式
from human-written survey outlines → 从人类撰写的文献综述大纲开始
Our approach → 我们的方法
is underpinned by two domain-specific knowledge → 以两种领域特定知识为基础
bases → 基础
a Research Paper Database → 一篇研究论文数据库
which encodes → 哪种编码方式
```

[原文第 4 页的完整图表与公式](assets/original-page-004.jpg)

算法1：SURVEYFORGE
输入：调查主题T；研究论文数据库R；文献综述大纲数据库S D D
输出：最终调查文档F
/* 大纲生成 */
检索与T相关的论文和大纲：R、S；
P P 生成一级大纲i及查询Q i；
O { } 对每一个一级大纲i，继续检索与Q i相关的相关论文和大纲：

**表格与文字对照**

```text
P
Ri ,
P
Si ;
Generate second-level outline ij and queries
O
q ij ;
{ }
Store
P
Ri as memory M i;
Store R as overall memory M;
P
/* Content Generation */
foreach subsection O ij in parallel do
Decompose query q ij into sub-queries q ijk
{ }
using M i;
Initialize L ij ;
← ∅
foreach sub-query q ijk do
Retrieve papers L using q and M;
ijk ijk
L ij L ij L ijk ;
← ∪
Rerank and select top papers Lreranked;
ij
Generate content C ij for O ij using Lr i e j ranked;
Merge contents { C ij } to form draft F draft ;
Refine F to produce final document F ;
draft
return F ;
domain knowledge, and a Survey Outline Database,
which captures established structural patterns (details provided in Appendix. A.1). As shown in
Algorithm 1, the framework begins with crossdatabase knowledge fusion, retrieving relevant papers and outlines for the given topic T from and
R
D
. This process identifies key thematic areas and
S
D
their interrelations, generating the first-level outline augmented with semantic queries Q that
i i
O
specify the scope and focus of each heading. For
each section , we recursively retrieves relevant
i
O
materials ( , ) and generates second-level
P
Ri
P
Si
outlines with sub-queries q . Finally, these
ij ij
O
headings and their associated queries are systematically merged to construct a academically rigorous
and comprehensive survey outline, serving as a
foundation for subsequent content generation.
3.2 Memory-Driven Content Generation
The memory-driven content generation stage consists of two primary steps: literature retrieval and
parallel content creation. These steps are performed
sequentially by the proposed Scholar NAvigation
Agent (SANA) and the LLM, respectively. A detailed explanation of each step is provided below.
124

表内文字对照（数值与原始行列保持不变）：
Generate second-level outline ij and queries → 生成二级大纲 ij 及查询语句
q ij → q ij
Store → 商店
Ri as memory M i → Ri作为记忆模块M i
Store R as overall memory M → 将 R 存储为整体内存 M
Content Generation → 内容生成
foreach subsection O ij in parallel do → 并行地对每个子小节 O ij 进行处理
Decompose query q ij into sub-queries q ijk → 将查询 q ij 分解为子查询 q ijk
using M i → 使用 M i
Initialize L ij → 初始化 L ij
foreach sub-query q ijk do → 对每个子查询 q ijk 进行遍历
Retrieve papers L using q and M → 使用 q 和 M 检索 L 篇论文
ijk ijk → ijk ijk
L ij L ij L ijk → L ij L ij L ijk
Rerank and select top papers Lreranked → 重新排序并选择顶级论文
Generate content C ij for O ij using Lr i e j ranked → 使用 Lr i e j 排序方法生成 O ij 对应的 C ij 内容
Merge contents → 合并内容
C ij → C ij
to form draft F draft → 形成草案 F 的初稿
Refine F to produce final document F → 完善 F，以生成最终文档 F
draft → 草稿
return F → 返回 F
domain knowledge → 领域知识
and a Survey Outline Database → 以及一份文献综述大纲数据库
which captures established structural patterns (details provided in Appendix → 该模型能够捕捉到已确立的结构模式（详见附录）
As shown in → 如所示
Algorithm → 算法
the framework begins with crossdatabase knowledge fusion → 该框架以跨数据库知识融合为起点
retrieving relevant papers and outlines for the given topic T from and → 从相关来源中检索与主题 T 相关的文献及大纲
This process identifies key thematic areas and → 该过程会识别关键主题领域
their interrelations → 它们的相互关联
generating the first-level outline augmented with semantic queries Q that → 生成了附加了语义查询 Q 的第一级大纲
i i → i i
specify the scope and focus of each heading → 明确每个章节的范围与重点
For → 对于
each section → 每个部分
we recursively retrieves relevant → 我们递归地进行相关信息的检索
materials ( → 材料（
and generates second-level → 并生成二级内容
outlines with sub-queries q → 包含子查询 q的大纲
Finally → 最后
these → 这些
ij ij → ij ij
headings and their associated queries are systematically merged to construct a academically rigorous → 标题及其相关查询被系统地合并，以构建出具有学术严谨性的内容
and comprehensive survey outline → 以及全面的文献综述大纲
serving as a → 作为……的角色
foundation for subsequent content generation → 后续内容生成的基础
Memory-Driven Content Generation → 基于记忆的内容生成
The memory-driven content generation stage consists of two primary steps → 基于记忆的内容生成阶段包含两个主要步骤
literature retrieval and → 文献检索与
parallel content creation → 并行内容创作
These steps are performed → 这些步骤被执行
sequentially by the proposed Scholar NAvigation → 按照所提出的 Scholar NAvigation 的顺序进行
Agent (SANA) and the LLM → 智能体（SANA）与大语言模型
respectively → 分别
A detailed explanation of each step is provided below → 每个步骤的详细说明如下提供
```

3.2.1 SANA：学者导航智能体 为了确保生成的文献综述中参考文献的质量和数量，我们提出了一种具备记忆与重新排序功能的学者导航智能体（SANA），旨在帮助在不同的生成阶段实现文献检索。SANA包含三个模块：子查询记忆模块（MS）、检索记忆模块（MR）以及时间感知重新排序引擎（TRE）。子查询记忆模块通过将复杂查询分解为较小的子查询来分解查询，从而实现更精准的文献检索。
现有的查询分解方法（Fan等人，2024）大多通过简单的提示词和大语言模型实现。然而，这些方法需要对提示词进行精细调整以适配不同任务，且可能导致分解后的子查询与原始查询之间存在显著的语义差异

**表格与文字对照**

```text
query, which could potentially degrade the quality of the references in the AI-generated surveys.
Therefore, we incorporate the memory mechanism
into the query decomposition process of SANA to
enhance the effectiveness of sub-queries. Specifically, as described in Sec. 3.1, when generating the
first-level outline O , a set of literature is rei
P
Ri
trieved by Retrieval-Augmented Generation (RAG).
In the MS module, SANA takes the literature
P
Ri
as memory M , the original query consists of the
i
titles t and descriptions d of each subsection:
Oij Oij
q = [d , t ]. (1)
ij Oij Oij
To achieve query decomposition, q and M are
ij i
used together as part of the instruction to prompt
the LLM to decompose q into multiple subij
queries q :
ijk
q = LLM(q , M ). (2)
ijk ij i
Finally, the sub-query q is used in the subsequent
ijk
MR module to retrieve literature related to the subsection O .
ij
Memory for Retrieval. The effectiveness of content generation heavily depends on the quality of
retrieved information. Traditional retrieval methods (Lewis et al., 2020; Gao et al., 2023), which
typically query the entire literature database ,
R
D
are often inefficient and lack contextual focus, particularly in generating complex, multi-section documents. These methods treat each section as an
isolated unit, failing to account for the global structure and thematic coherence of the document. This
447

表内文字对照（数值与原始行列保持不变）：
query → 查询
which could potentially degrade the quality of the references in the AI-generated surveys → 这可能会降低人工智能生成的文献综述中参考文献的质量
Therefore → 因此
we incorporate the memory mechanism → 我们引入了记忆机制
into the query decomposition process of SANA to → 进入 SANA 的查询分解过程
enhance the effectiveness of sub-queries → 提升子查询的有效性
Specifically → 具体来说
as described in Sec → 如第 Sec 节所述
when generating the → 在生成时
first-level outline O → 一级大纲 O
a set of literature is rei → 一组文献为 rei
trieved by Retrieval-Augmented Generation (RAG) → 通过检索增强生成（RAG）技术获取
In the MS module → 在 MS 模块中
SANA takes the literature → SANA 对相关文献进行了研究
as memory M → 作为记忆模块 M
the original query consists of the → 原始查询由……组成
titles t and descriptions d of each subsection → 每个小节的标题 t 和描述 d
Oij Oij → Oij Oij
ij Oij Oij → ij Oij Oij
To achieve query decomposition → 为了实现查询分解
q and M are → q 和 M 是
ij i → ij i
used together as part of the instruction to prompt → 作为提示指令的一部分共同使用
the LLM to decompose q into multiple subij → 用于将 q 分解为多个子 ij 的大语言模型
queries q → 查询 q
ijk → ijk
LLM(q → 大语言模型(q)
M ) → M )
ijk ij i → ijk ij i
Finally → 最后
the sub-query q is used in the subsequent → 子查询 q 在后续步骤中被使用
MR module to retrieve literature related to the subsection O → 用于检索与子章节 O 相关的文献的 MR 模块
Memory for Retrieval → 检索记忆
The effectiveness of content generation heavily depends on the quality of → 内容生成的效果在很大程度上取决于其质量
retrieved information → 检索到的信息
Traditional retrieval methods (Lewis et al → 传统检索方法（Lewis等人）
Gao et al → 高等人
which → 哪个
typically query the entire literature database → 通常会查询整个文献数据库
are often inefficient and lack contextual focus → 往往效率低下且缺乏上下文关注
particularly in generating complex → 尤其是在生成复杂内容时
multi-section documents → 多部分文档
These methods treat each section as an → 这些方法将每个部分视为一个独立单元
isolated unit → 独立单元
failing to account for the global structure and thematic coherence of the document → 未能考虑该文献的全球结构与主题连贯性
This → 这
```

[原文第 5 页的完整图表与公式](assets/original-page-005.jpg)

导致冗余或无关的检索行为，并限制生成内容的整体连贯性。

为了克服这些限制，我们将记忆机制融入 SANA 的检索过程中，以弥合大纲生成与内容生成阶段之间的差距。具体而言，在 MS 模块中，SANA 将整个大纲相关的文献作为记忆 M。根据每个子查询 q 与记忆 M 中文献之间的嵌入相似性，为章节 O 的每个子查询找到最相关的文献 L ijk。随后，所检索到的文献 L 会被重新排序，并在接下来的 TRE 模块中被选中用于内容生成——即时间感知重排序引擎。
重新排序在提升检索信息的质量与相关性方面起着重要作用。现有方法（Glass等人，2022；Xiao等人，2023）通常采用先进的评分机制来衡量查询与文档之间的文本相关性。

然而，这种表面层面的语义匹配可能难以全面反映出版物的学术影响与质量。此外，论文的发表时间对于判断其在特定领域中的影响与重要性具有至关重要意义。因此，分析同一研究领域中不同时间期的论文，对于识别该研究领域内的高质量贡献至关重要。对于同一时期发表的论文，存在多种指标可以衡量其影响与质量，例如引用次数、Essential Science Indicators（ESI）等（Clarivate，2024）。
其中，引用次数作为一种补充质量指标，能够反映研究工作的学术影响与认可度。为了克服纯语义匹配的局限性以及不同质量指标所存在的时间偏差问题，我们提出了一种时间感知重新排序引擎，该引擎整合了文本相关性、引用影响力及发表时间因素。

这种方法不仅确保了检索到的文献的主题相关性，还保证了其学术质量，同时能够平衡地呈现既有研究与新兴研究。

具体而言，基于 ijk 嵌入相似度筛选出的文献 L 根据发表日期被划分为多个组 L = n G，每个组覆盖两年时间范围。对于每一组 g，高被引文献以 top-k 的方式被保留作为 SANA 的最终输出，且所需保留的文献数量不超过 124 篇

每个小组所保留的参数为：n g k = | | K, (3) g L Oij ijk | |，其中 K 是一个超参数，表示用于生成各小节内容的参考文献数量。3.2.2 并行生成与优化由于大语言模型最大上下文长度和推理速度的限制，各章节的内容会并行生成，以缩短生成时间并确保生成的文献综述长度。然而，由于各章节的生成过程是独立的，不同章节的内容中可能存在重复或冗余现象。
因此，我们采用大语言模型来执行优化阶段，该阶段旨在对通过并行生成各章节内容后拼接而成的原始文献综述进行完善。3.3 多维度评估基准 由于缺乏标准化评估基准，对人工智能生成的文献综述进行评估具有挑战性。现有方法主要依赖大语言模型的自动评分，但存在局限性：它们可能无法充分评估关键文献覆盖情况，且严重依赖内部模型判断，缺乏客观指标。
为应对这些挑战，我们推出了 SurveyBench 这一全面的评估基准，以及 SAM（文献综述评估指标）这一多维度的评估体系。SurveyBench 包含约 100 篇由人类撰写的文献综述论文，涵盖 10 个不同的主题，由博士级别的研究人员精心筛选，以确保主题连贯性和学术严谨性。对于每个主题 t，我们选取了其中一份质量最高的文献综述 S 作为与 AI 生成的文献综述 Sˆ 进行对比的参考。该评估基准构建过程的详细内容请参见附录 A.2。
SAM系列通过三个核心组件整合了客观指标、专家知识及多维标准：SAM-R——参考质量评估。一份全面且相关的参考文献列表对于高质量的文献综述至关重要。基于Survey-Bench，我们为每个主题提取一组参考资料，作为该领域基础知识的可靠基准。为了衡量参考资料的质量，我们定义了SAM指标，该指标能够量化AI生成的文献综述Sˆ i 448中各参考资料之间的重叠程度

[原文第 6 页的完整图表与公式](assets/original-page-006.jpg)

并且：i R R SAM (Sˆ ) = | Sˆ i ∩ R i |, (4) R i R | Sˆ i|，其中 R 是 Sˆ 中的参考文献集合。更高的 Sˆ i i 值表明对主题 t 的关键文献的覆盖更为充分。i SAM-O：大纲质量评估。该模块用于评估人工智能生成的文献综述的结构质量。结构合理且逻辑连贯的大纲对于内容组织和可读性至关重要。我们采用一个从 0 O 到 100 的单一综合分数 SAM 来评估大纲，得分越高表示质量越好。

评估工作由大语言模型按照附录 A.9 中描述的详细标准进行。

SAM-C：内容质量评估。最终指标从三个维度衡量生成文献综述的质量：结构（SAMstruct）、内容相关性（SAMrel）和覆盖范围（SAMcov）。以高质量文献综述 S 作为参考，我们计算整体内容的平均得分：

SAMstruct + SAMrel + SAMcov 平均值 = C C C. C 3 (5) 评分范围从 0 到 100，数值越高表示性能越好。大语言模型在参考 S 的同时对这些标准进行评估，以确保其符合专家级标准。4 实验 4.1 实验设置 评估数据集。为了评估我们提出方法的性能，我们在计算机科学领域基于 arXiv 仓库构建了一个专门的基准数据集。如第 3.3 节所述，我们手动选取了约 100 篇不同主题的人类撰写的文献综述论文，并从中选出一篇质量最高的文献综述，用于与人工智能生成的文献综述进行直接对比。
实施细节。为了建立对比基准，我们采用了 AutoSurvey（Wang等人，2024c）这一用于自动生成文献综述的先进系统。此外，我们从 arXiv 的计算机科学科学领域收集了一个大规模数据集，包含约 600,000 篇研究论文和 20,000 篇综述文章。我们提取关键元数据以构建检索向量数据库，包括所有论文的标题、摘要以及 124 篇大纲

在综述文章中。为确保公平比较，我们将检索数据库的时间线与 AutoSurvey 保持一致。在实验评估过程中，我们在大纲生成阶段检索了1,500篇候选论文，在每个章节写作阶段则分别检索了60篇相关论文，实验设置与 AutoSurvey 相同。在文献综述的生成过程中，我们独立使用两个大语言模型：Claude-3-haiku-20240307 和 GPT-4o-mini-2024-07-18。每个模型针对10个预定义的主题生成文献综述，每个主题进行10次独立试验，因此每个模型共产生100份输出结果。
这些试验的平均表现被计算出来，以确保结果稳定可靠。除了闭源模型外，我们还对开源模型Deepseek-v3（Liu等人，2024年）进行了实验，结果令人印象深刻，详见附录A.5。为了进行评估，我们采用了更先进的模型GPT-4o-2024-08-06和Claude-3.5-sonnet-20241022，以对人工智能生成的大纲及文献综述内容进行评估，从而确保评估的严谨性与可靠性

其质量评估。4.2 主要结果

如表1所示，我们从参考质量、大纲质量及内容质量等多个维度评估了SURVEYFORGE的性能，并将其与基准Au- toSurvey进行了对比。结果表明，SURVEY- FORGE在所有方面均取得了显著提升，展现了其作为先进自动化文献综述生成框架的潜力。此外，我们对SU- VEYFORGE框架的成本进行了分析，结果显示生成64k个token的概述成本低于0.50美元，详细的成本分解数据见附录A.6。关于参考质量的结果。
在参考文献质量方面，SURVEYFORGE在两个关键指标上均优于Auto-Survey：输入覆盖度用于衡量检索到的文献相关性，参考文献覆盖度则用于评估文献综述中的参考文献与专家筛选的基准之间的匹配程度。具体而言，使用Claude-3时，输入覆盖度得分从0.12提升到了0.22

Haiku 与 GPT-4o mini 的得分在 0.07 到 0.20 之间。同样，两种模型的 Reference Coverage 得分分别从 0.23 提升至 0.40，从 0.20 提升至 0.42，表明 SURVEYFORGE 能够检索并生成 449 篇以上的参考文献

[原文第 7 页的完整图表与公式](assets/original-page-007.jpg)

参考质量方法模型输入协变量参考协变量

人类撰写内容 - - 0.6294 AutoSurvey Claude-3-Haiku 0.1153 0.2341 SURVEYFORGE Claude-3-Haiku 0.2231 0.3960 AutoSurvey GPT-4o mini 0.0665 0.2035 SURVEYFORGE GPT-4o mini 0.2018 0.4236 表1：SURVEYFORGE与AutoSurvey（SAM）在三个方面的比较：Reference（SAM-R），大纲表示输入文献的覆盖程度，用于衡量重叠度；“Reference Cov.”则表示参考文献、文献综述及基准文献的覆盖程度。

**表格与文字对照**

```text
Outline C
Methods
Score Win Rate Comparat
AutoSurvey (Wang et al., 2024c) 27.00% 25
SURVEYFORGE 73.00% 75
Table 2: Win-rate comparison of automatic and human eva
reflects the win rate based on individual LLM-scores, wh
before determining the higher-scoring one. "Comparative
where the LLM directly compares two articles side-byrepresents the win rate derived from expert human evalua
 / / 0  E D V H G  ( Y D O X D W L R Q  / / 0  E D V H G  ( Y D O X D W L R Q
 0 X O W L  $ J H Q W  R I  / / 0 V  0 X O W L  $ J H Q W  R I  / / 0 V
 *  '  H  0  L  Q  I  H  R  I  U  G  X  D  H  V  W  L  O  R  V  L Y  Q  H  ' H W    H  '  F    W  2  L R  E  Q  M    H  L Q  F    W  $ '  *  '  H  0  L  Q  I  H  R  I  U  G  X  D  H  V  W  L  O  R  V  L Y  Q  H  ' H W    H  '  F    W  2  L R  E  Q  M    H  L Q  F    W  $ '
         
 1  1  H  *  W  H  U  Z  D  X  R  U  S  D  U  K  N  O  V                  '  6    S  *  O D  D  W  X  W  V  L  V  Q  L  J  D Q  1  1  H  *  W  H  U  Z  D  X  R  U  S  D  U  K  N  O  V                    '  6    S  *  O D  D  W  X  W  V  L  V  Q  L  J  D Q
 + D O O X F L Q D W L R Q  9 L V L R Q  + D O O X F L Q D W L R Q  9 L V L R Q
 L Q  / / 0 V  7 U D Q V I R U P H U V  L Q  / / 0 V  7 U D Q V I R U P H U V
 / D U  0  J  X  0  H  O    W  R  /  L  G  P  D  H  Q  R  O  J  G  V  X  D  D  O  J H  5 $  / /  *  0   I  V  R U  $  6 X  X  U  W  Y  R  H  6  \  X  )  U  R  Y  U  H  J  \  H  / D U  0  J  X  0  H  O    W  R  /  L  G  P  D  H  Q  R  O  J  G  V  X  D  D  O  J H  5 $  / /  *  0   I  V  R U  $  6  +  X  X  X  U  W  P  Y  R  D  H  6  Q  \  X  )  U  R  Y  U  H  J  \  H
(a) (b)
 / / 0  E D V H G  ( Y D O X D W L R Q  / / 0  E D V H G  ( Y D O X D W L R Q
 0 X O W L  $ J H Q W  R I  / / 0 V  0 X O W L  $ J H Q W  R I  / / 0 V
 *  '  H  0  L  Q  I  H  R  I  U  G  X  D  H  V  W  L  O  R  V  L Y  Q  H  ' H W    H  '  F    W  2  L R  E  Q  M    H  L Q  F    W  $ '  *  '  H  0  L  Q  I  H  R  I  U  G  X  D  H  V  W  L  O  R  V  L Y  Q  H  ' H W    H  '  F    W  2  L R  E  Q  M    H  L Q  F    W  $ '
 1  1  H  *  W  H  U  Z  D  X  R  U  S  D  U  K  N  O  V           
    '  6  
   S    *  O D  D  W  X  W  V  L  V  Q  L  J  D Q  1  1  H  *  W  H  U  Z  D  X  R  U  S  D  U  K  N  O  V            '  6      S    *  O D  D  W  X  W  V  L  V  Q  L  J  D Q
 + D O O X F L Q D W L R Q  9 L V L R Q  + D O O X F L Q D W L R Q  9 L V L R Q
 L Q  / / 0 V  7 U D Q V I R U P H U V  L Q  / / 0 V  7 U D Q V I R U P H U V
 / D U  0  J  X  0  H  O    W  R  /  L  G  P  D  H  Q  R  O  J  G  V  X  D  D  O  J H  5 $  / /  *  0   I  V  R U  $  6  +  X  X  X  U  W  P  Y  R  D  H  6  Q  \  X  )  U  R  Y  U  H  J  \  H  / D U  0  J  X  0  H  O    W  R  /  L  G  P  D  H  Q  R  O  J  G  V  X  D  D  O  J H  5 $  / /  *  0   I  V  R U  $  6 X  X  U  W  Y  R  H  6  \  X  )  U  R  Y  U  H  J  \  H
(c) (d)
Figure 3: Evaluation results on SurveyBench. Evaluation results of (a) Input Coverage, (b) Reference Coverage, (c) Outline Quality, and (d) Content Quality.

表内文字对照（数值与原始行列保持不变）：
Outline C → 大纲 C
Methods → 方法
Score Win Rate Comparat → 得分胜率对比
AutoSurvey (Wang et al → AutoSurvey（王等）
SURVEYFORGE → SURVEYFORGE
Table → 表格
Win-rate comparison of automatic and human eva → 自动与人工 Eva 的胜率对比
reflects the win rate based on individual LLM-scores → 反映了基于各个大语言模型得分的胜率
before determining the higher-scoring one → 在确定得分更高者之前
Comparative → 比较研究
where the LLM directly compares two articles side-byrepresents the win rate derived from expert human evalua → 其中，大语言模型直接对两篇文献进行并列比较，从而得出由专家人类评估所得到的胜率
a) (b) → a) (b)
c) (d) → c) (d)
Figure → 图
Evaluation results on SurveyBench → SurveyBench上的评估结果
Evaluation results of (a) Input Coverage → (a) 输入覆盖率的评估结果
b) Reference Coverage → b) 参考文献覆盖情况
c) Outline Quality → c) 大纲质量
and (d) Content Quality → 以及 (d) 内容质量
```

更具相关性，也更符合专家预期。值得注意的是，高质量的人工撰写的文献综述达到了0.63的参考覆盖得分，这进一步验证了我们提出的参考评估数据库的可靠性，它为参考质量提供了可靠的基准。

大纲质量结果。在大纲质量方面，研究结果表明，与 AutoSurvey 相比，SURVEYFORGE 生成的大纲更具逻辑性、全面性，且更接近人类水平的表现（Wang 等，2024c）。使用 Claude-3-Haiku 时，大纲质量得分从 82.25 提升至 86.58，而 GPT-4o mini 的得分则达到 124

**表格与文字对照**

```text
Content Quality
Outline Quality
Structure Relevance Coverage Avg
87.62 - - - -
82.18 72.83 76.44 72.35 73.87
86.85 73.82 79.62 75.59 76.34
83.10 74.66 74.16 76.33 75.05
86.62 77.10 76.94 77.15 77.06
y (Wang et al., 2024c) using Survey Assessment Metrics
e (SAM-O) and Content quality (SAM-C). "Input Cov."
lap between retrieved papers and benchmark references,
, evaluating the alignment between cited references of the
Comparison Content Comparison
tive Win Rate Human Eval Score Win Rate Human Eval
5.00% 26.00% 31.00% 30.00%
5.00% 74.00% 69.00% 70.00%
aluations on outline and content quality. "Score Win Rate"
here the LLM assigns separate score to each survey paper
e Win Rate" is derived from LLM pairwise comparisons,
-side and decides which one is superior. "Human Eval"
ations.
Method Heuristic Learning Demonstration Outline Outline Quality
AutoSurvey - 81.78
×
SURVEYFORGE ✓ From random surveys 84.58
SURVEYFORGE ✓ From related surveys 86.67
Table 3: Ablation study for outline generation. "Demonstration Outline" means the source of outlines used for
heuristic learning.
similar improvement from 83.10 to 86.62. These
advancements are driven by the proposed fewshot heuristic learning method, which leverages
expert-curated examples from the Survey Outline
Database to guide the LLMs in producing wellstructured and domain-relevant outlines.
Results on Content Quality. For content quality,
SURVEYFORGE achieves consistent improvements
across all three evaluation dimensions: structure,
relevance, and coverage. The average content quality score increases from 73.87 to 76.34 (Claude-3-
Haiku) and 75.05 to 77.06 (GPT-4o mini). These
results confirm that SURVEYFORGE generates content that is better organized, more relevant, and
more comprehensive, effectively addressing the
critical aspects of the target domain.
As shown in Fig. 3, SURVEYFORGE demonstrates substantial improvements over the baseline AutoSurvey across all key evaluation metrics.
Although not yet matching the quality of expertcrafted surveys, SURVEYFORGE significantly narrows the gap, highlighting its potential as a powerful tool for automated survey generation.
4.3 Comparison with Human Evaluation

表内文字对照（数值与原始行列保持不变）：
Content Quality → 内容质量
Outline Quality → 大纲质量
Structure Relevance Coverage Avg → 结构相关性覆盖度平均值
y (Wang et al → y（王等）
c) using Survey Assessment Metrics → c) 使用文献综述评估指标
e (SAM-O) and Content quality (SAM-C) → e (SAM-O) 与内容质量 (SAM-C)
Input Cov → 输入特征
lap between retrieved papers and benchmark references → 检索到的文献与基准参考文献之间的差距
evaluating the alignment between cited references of the → 评估所引用的参考文献之间的一致性
Comparison Content Comparison → 内容对比
tive Win Rate Human Eval Score Win Rate Human Eval → 人类评估中的胜率得分
aluations on outline and content quality → 关于大纲与内容质量的讨论
Score Win Rate → 得分胜率
here the LLM assigns separate score to each survey paper → 在这里，大语言模型为每篇文献综述分配不同的分数
e Win Rate → 胜率
is derived from LLM pairwise comparisons → 源自大语言模型成对比较结果
side and decides which one is superior → 进行比较并决定哪一个更优
Human Eval → 人类评估
ations → 方法
Method Heuristic Learning Demonstration Outline Outline Quality → 方法 启发式学习 演示大纲 大纲 质量
AutoSurvey - → 自动文献综述 -
SURVEYFORGE → SURVEYFORGE
From random surveys → 来自随机文献综述
From related surveys → 来自相关文献综述
Table → 表格
Ablation study for outline generation → 大纲生成方法的剔除研究
Demonstration Outline → 演示大纲
means the source of outlines used for → 指用于编写大纲的来源
heuristic learning → 启发式学习
similar improvement from → 类似的改进
These → 这些
advancements are driven by the proposed fewshot heuristic learning method → 进展得益于所提出的少样本启发式学习方法
which leverages → 利用……的机制
expert-curated examples from the Survey Outline → 来自文献综述大纲的专家筛选示例
Database to guide the LLMs in producing wellstructured and domain-relevant outlines → 用于指导大语言模型生成结构合理且与领域相关的大纲的数据库
Results on Content Quality → 内容质量结果
For content quality → 针对内容质量
SURVEYFORGE achieves consistent improvements → SURVEYFORGE 实现了持续的改进
across all three evaluation dimensions → 在所有三个评估维度上
structure → 结构
relevance → 相关性
and coverage → 以及覆盖范围
The average content quality score increases from → 平均内容质量得分上升
Claude- → Claude-
Haiku) and → 俳句）和
GPT- → GPT-
o mini) → o mini)
results confirm that SURVEYFORGE generates content that is better organized → 结果证实，SURVEYFORGE生成的内容结构更为清晰
more relevant → 更相关
and → 并且
more comprehensive → 更全面的
effectively addressing the → 有效解决该问题
critical aspects of the target domain → 目标领域的关键方面
As shown in Fig → 如图所示
SURVEYFORGE demonstrates substantial improvements over the baseline AutoSurvey across all key evaluation metrics → SURVEYFORGE在所有关键评估指标上均显著优于基准的AutoSurvey
Although not yet matching the quality of expertcrafted surveys → 尽管尚未达到专家精心撰写的文献综述的质量水平
SURVEYFORGE significantly narrows the gap → SURVEYFORGE 显著缩小了差距
highlighting its potential as a powerful tool for automated survey generation → 强调其作为自动化文献综述生成强大工具的潜力
Comparison with Human Evaluation → 与人类评估的对比
```

为了验证我们的自动化评估系统，我们将其性能与专家评估结果进行对比——450

[原文第 8 页的完整图表与公式](assets/original-page-008.jpg)

**表格与文字对照**

```text
Components Reference Quality
MR MS TRE Input Cov. Reference Cov.
- - - 0.1119 0.2340
✓ - - 0.1694 0.2730
✓ ✓ - 0.1781 0.2984
✓ - ✓ 0.1997 0.3542
✓ ✓ ✓ 0.2224 0.3971
Table 4: Ablation study for content generation. We
perform ablation on three components of SANA module:

表内文字对照（数值与原始行列保持不变）：
Components Reference Quality → 组件参考质量
MR MS TRE Input Cov → MR MS TRE 输入特征
Reference Cov → 参考文献目录
Table → 表格
Ablation study for content generation → 内容生成方法的剔除研究
perform ablation on three components of SANA module → 对 SANA 模块的三个组件进行消融实验
```

MR代表检索记忆模型，MS代表子查询记忆模型，TRE代表时间感知重新排序引擎。

使用来自 Claude-3-haiku-20240307 的 100 条输出内容，针对 10 个主题进行分析（详细信息请参考附录 A.2 和附录 A.4）。我们采用胜率框架，将 SURVEYFORGE 和 AutoSurvey 的匿名结果（Wang 等，2024c）呈现给 20 位计算机科学领域的博士专家。这些专家是根据评估主题精心挑选的，并在相关领域拥有深厚的专业知识。

如表2所示，在大纲质量方面，自动化系统的得分胜率达到73.00%，对比胜率达到75.00%，与人工评估的胜率非常接近

74.00%。这种一致性证明了该系统的稳健评分逻辑。在内容质量方面，SURVEY-FORGE自动系统的得分胜率为69.00%，与人类专家的得分率70.00%非常接近。此外，我们还进行了科恩kappa系数一致性实验，结果显示自动化系统与人工评估之间存在高度一致性，详见附录A.4。总之，无论是大纲还是内容质量，自动化系统都与人工评估结果吻合良好，这验证了其作为手动评估可靠替代方案的有效性。

4.4 消融研究 为了更清楚地了解所提出的 SURVEYFORGE 框架中各个组件的作用，我们进行了全面的消融研究。在消融实验中，我们使用 Claude-3- haiku-20240307 针对相同的10个主题生成文献综述，每个主题进行3次独立实验，以在保持一致性的同时确保统计可靠性。

计算效率。具体而言，我们分析了学者导航智能体模块中的内存机制、子查询分解与重新排序策略，以及使用文献综述大纲数据库在大纲 124 中的影响

生成过程。消融实验的结果分别展示在表3和表4中。关于大纲生成的分析：表3揭示了启发式学习方法对大纲质量的影响。仅基于检索到的研究论文而无需结构指导来生成大纲的基线方法得分为81.78分，这表明缺乏组织性提示会限制大纲的连贯性和逻辑性。为解决这一问题，我们首先引入了一种利用随机文献综述中的大纲作为参考的启发式方法。这些代表文献综述写作常见模式的通用大纲使得分提升到了84.58分。
这表明了结构提示的有效性，即使无需针对目标领域进行定制。最后，我们检索出特定领域的大纲，既提供了结构指导，又实现了与目标领域的主题对齐。因此，大纲质量得分显著提升至 86.67，表明特定领域的结构提示在生成连贯且相关的大纲方面具有关键作用。内容生成分析。基于表 4中呈现的实验结果，可以

观察到随着 SANA 所获取文献的质量提升，文献综述中引用的参考文献质量也相应提高。这一观察结果凸显了在内容生成阶段使用 SANA 进行高质量文献检索的重要性。具体而言，将记忆机制整合到查询分解与检索过程中，能显著提升文献质量。这种提升得益于更全面的子查询语义的融入，以及与子查询更为匹配的检索范围。
此外，时间感知重新排序引擎能够确保筛选出高质量论文，从而形成更全面且均衡的参考文献集。

5 结论与展望 我们介绍了 SURVEYFORGE这一自动化框架，该框架利用启发式大纲生成和基于记忆的内容生成技术来生成高质量文献综述。我们还引入了一种多维评估基准，以全面评估文献综述的质量。SURVEY-FORGE的性能显著优于以往的方法。

在多种评估指标上。我们希望能够降低那些涉足陌生领域的研究人员的学习难度，从而提供便利，进而促进跨学科与跨领域知识的整合与发展。451

[原文第 9 页的完整图表与公式](assets/original-page-009.jpg)

局限性 尽管 SURVEYFORGE 在生成结构化且高质量的文献综述方面表现优异，但如附录 A.3 所述，它也存在固有的局限性。虽然大语言模型在总结现有文献方面表现出色，但在分析与多种来源之间的关联并进行综合处理时却面临挑战，通常缺乏人类创作作品所具有的批判性思维与原创性，这限制了其反映现实的能力。

搜索趋势或提供前瞻性见解。

此外，大语言模型的幻觉现象也会影响内容和引用信息的准确性。未来的研究可以致力于开发更有效的方法，以更好地捕捉参考文献之间的关联，从而提升生成内容的逻辑连贯性、深度及学术价值。

伦理声明 本研究致力于开发一种自动文献综述生成框架，旨在帮助研究人员高效总结现有文献。所提出的方法基于公开可用的数据集和研究论文，确保符合版权和知识产权法律要求。虽然该框架旨在提升人类专业水平，但我们鼓励用户使用它

对生成的输出进行严格评估，确保其符合伦理研究规范，并消除任何潜在缺陷，如偏见或不完整的总结。致谢

该研究得到了上海人工智能实验室的支持，该实验室是上海市政府委托的本地项目、上海市科技重大专项以及上海之星计划（项目编号：23QD1401000）的资助。

参考文献：Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyamal Anadkat 等. 2023. GPT-4技术报告。

arXiv预印本 arXiv:2303.08774。

Anthropic。2024。Claude 3 模型系列：Opus、sonnet、haiku。网址：

https://www-cdn.anthropic.com/ de8ba9b01c9ab7cbabf5c33b80b7bbc618857627/ Model_Card_Claude_3.pdf. 124

Asai Akari, He Jacqueline, Shao Rulin, Shi Weijia, Singh Amanpreet, Chang Joseph Chee, Lo Kyle, Soldaini Luca, Feldman Sergey, D’arcy Mike 等. 2024. Openscholar：利用检索增强的大语言模型整合科学文献. arXiv预印本 arXiv:2411.14199. Assafelovic. 2023. gpt-researcher. 网址：https://github.com/assafelovic/gpt-researcher. Cai Zheng, Cao Maosong, Chen Haojiong, Chen Kai, Chen Keyu, Chen Xin, Chen Xun, Chen Zehui, Chen Zhi, Chu Pei 等. 2024. Internlm2技术报告. arXiv预印本 arXiv:2403.17297. Chen Jingqiang 和 Zhuge Hai. 2019. 通过总结引用自动生成相关工作.
《并发与计算：实践与经验》，31(3):e4261。陈哲、王伟云、田浩、叶生龙、高张伟、崔尔飞、童文文、胡孔志、罗加平、马正等。2024a。我们离 GPT-4v 还有多远？通过开源工具缩小与商业多模态模型的差距。arXiv 预印本 arXiv:2404.16821。陈子如、陈世杰、宁玉婷、张千恒、王博石、于波涛、李一飞、廖泽毅、陆晨伟、卢志同等。2024b。Scienceagentbench：针对数据驱动科学发现的语言智能体严格评估方法。arXiv 预印本 arXiv:2410.05080。Clarivate。2024。核心科学指标：了解基础知识。
URL: https://clarivate.libguides. com/esi。文奇·范、丁玉娟、宁亮波、王世杰、李恒云、尹大伟、Chua Tat-Seng、李庆。2024。关于RAG与LLM的文献综述：迈向检索增强型大语言模型。载于第30届ACM SIGKDD知识发现与数据挖掘会议论文集，第6491–6501页。高云凡、熊云、高新宇、贾康祥、潘金柳、毕玉西、戴毅、孙家伟、王浩峰。2023。大语言模型的检索增强生成技术：一项综述。arXiv预印本arXiv:2312.10997。Alireza Ghafarollahi和Markus J Buehler。2024。
Scia-gents：通过多智能体智能图推理实现科学发现自动化。arXiv预印本 arXiv:2409.05556。作者：Michael Glass、Gaetano Rossiello、Md Faisal Mahbub Chowdhury、Ankita Naik、Pengshan Cai 和 Alfio Gliozzo。2022年。Re2G：检索、重新排序、生成。载于《2022年北美计算语言学协会人类语言技术会议论文集》，美国西雅图，第2701–2715页。计算语言学协会。452

[原文第 10 页的完整图表与公式](assets/original-page-010.jpg)

Cong Duy Vu Hoang 和 Min-Yen Kan. 2010. 迈向自动化的相关工作总结方法研究. 载于 Coling 2010：海报会议，第 427–435 页. Xiang Hu, Hongyu Fu, Jinge Wang, Yifeng Wang, Zhikun Li, Renjun Xu, Yu Lu, Yaochu Jin, Lili Pan 和 Zhenzhong Lan. 2024a. Nova：一种迭代规划与搜索方法，用于提升大语言模型生成创意的新颖性与多样性. arXiv 预印本 arXiv:2410.14255. Yue Hu 和 Xiaojun Wan. 2014. 科学论文中相关工作章节的自动生成：一种优化方法. 载于 2014 年自然语言处理实证方法会议（EMNLP）论文集，第 1624–1633 页.

胡云通、李卓峰、张正、陈玲、Raasikh Kanjiani、赵博新和赵亮。2024b。Hireview：基于层次分类法的自动文献综述生成。arXiv预印本 arXiv:2410.03761。黄谦、Jian Vora、Percy Liang和Jure Leskovec。2024。Mlagentbench：针对机器学习实验的语言智能体评估。发表于第四十一届国际机器学习会议。

Rahul Jha、Catherine Finegan-Dollak、Ben King、Reed Coke 和 Dragomir Radev。2015。用于文献综述生成的内容模型：基于事实信息的评估。载于《第53届计算语言学协会年会与第7届国际自然语言处理联合会议论文集（第1卷：长文）》，第441–450页。

Sandeep Kumar, Tirthankar Ghosal, Vinayak Goyal, 和 Asif Ekbal. 2024. 大语言模型能否解锁新的科学研究思路？arXiv预印本 arXiv:2409.06185. Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rottäschel 等. 2020. 用于知识密集型自然语言处理任务的检索增强生成方法。《神经信息处理系统进展》，33:9459–9474。

Long Li, Weiwen Xu, Jiayan Guo, Ruochen Zhao, Xinx-uan Li, Yuqian Yuan, Boqiang Zhang, Yuming Jiang, Yifei Xin, Ronghao Dang等. 2024. 思想链：

利用大语言模型智能体彻底革新新想法开发的研究。arXiv预印本 arXiv:2410.13185。

李泽汉、张欣、张彦超、龙丁坤、谢鹏军和张美山。2023。基于多阶段对比学习的通用文本嵌入方法。arXiv预印本 arXiv:2308.03281。

刘爱新、裴峰、薛冰、王冰轩、吴伯超、卢成达、赵成刚、邓成奇、张晨宇、阮崇等. 2024.

Deepseek-v3技术报告。arXiv预印本，arXiv:2412.19437。124

Lu Chris, Lu Cong, Lange Robert Tjarko, Fo- erster Jakob, Clune Jeff, Ha David. 2024. 《AI科学家：迈向完全自动化的开放式科学发现》。ArXiv, abs/2408.06292。Su Haoyang, Chen Renqi, Tang Shixiang, Zheng Xinzhe, Li Jingzhe, Yin Zhenfei, Ouyang Wanli, Dong Nanqing. 2024. “两个大脑胜过一个：多智能体系统具有提升科学创意生成的潜力”。arXiv预印本 arXiv:2410.09403。Sun Xiaoping, Zhuge Hai. 2019. 基于模板树的自动生成文献综述。发表于2019年第15届语义、知识与网格国际会议（SKG），第89–96页。IEEE。
Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar 等. 2023. Llama：开放且高效的基础语言模型. arXiv 预印本 arXiv:2302.13971. Bin Wang, Chao Xu, Xiaomeng Zhao, Linke Ouyang, Fan Wu, Zhiyuan Zhao, Rui Xu, Kaiwen Liu, Yuan Qu, Fukai Shang 等. 2024a. Mineru：用于精确文档内容提取的开源解决方案. arXiv 预印本 arXiv:2409.18839. Wenxiao Wang, Lihui Gu, Liye Zhang, Yunxiang Luo, Yi Dai, Chen Shen, Liang Xie, Binbin Lin, Xiaofei He, Jieping Ye. 2024b.
Scipip：一种基于大语言模型的科学论文创意提出工具。arXiv预印本 arXiv:2410.23166。王一东、郭奇、姚文金、张洪波、张欣、吴振、张美山、戴新宇、张敏、文青松等。2024c。Autosurvey：大语言模型能够自动撰写文献综述。arXiv预印本 arXiv:2406.10252。夏仁秋、毛松、严祥超、周宏斌、张波、彭浩阳、皮佳浩、傅道成、吴文杰、叶汉成等。2024a。Docgenome：用于训练和测试多模态大语言模型的开放大规模科学文档基准数据集。arXiv预印本 arXiv:2406.11633。
夏仁秋、张波、叶汉成、严翔超、刘奇、周洪斌、陈志军、杜敏、施博天、闫俊志等。2024b。Chartx与chartvlm：用于复杂图表推理的多功能基准与基础模型。arXiv预印本 arXiv:2402.12185。肖世涛、刘正、张培田、尼克拉斯·穆恩诺霍夫。2023。C-pack：用于推进通用中文嵌入的打包资源。预印本，arXiv:2309.07597。袁佳康、严翔超、施博天、陈涛、欧阳万利、张波、白雷、乔宇、周博文。2025。Dolphin：通过思考、实践与反馈实现的闭环开放式自动研究。arXiv预印本 arXiv:2501.03916。453

[原文第 11 页的完整图表与公式](assets/original-page-011.jpg)

Kun Zhu、Xiaocheng Feng、Xiachong Feng、Yingsheng Wu 和 Bing Qin。2023。文献综述的层次化目录生成：一个基准测试。arXiv预印本 arXiv:2304.03512。

[原文第 12 页的完整图表与公式](assets/original-page-012.jpg)

## 附录 由于手稿的页面限制，我们从以下几个方面提供更多细节和可视化内容：

• A.1节：数据库构建。

• A.2节：SurveyBench的详细内容。• A.3节：关于生成文献综述与人工撰写的文献综述的讨论。

• A.4节：人类评估细节及评分者一致性分析。

• A.5节：使用开源模型的额外实验。 • A.6节：时间与经济成本的详细情况。

• A.7节：定性结果。

• A.8节：生成的文献综述示例。

• 第 A.9节：使用的提示词。A.1 数据库构建

为确保人工智能生成的文献综述的质量与相关性，我们构建了两个关键数据库：

研究论文数据库与文献综述大纲数据库，包含约600,000篇研究论文和20,000篇综述文章，共同作为内容生成与结构指导的基础。研究论文数据库包含与该文献综述主题相关的研究论文标题及摘要，而文献综述大纲数据库则包含从已发表的文献综述论文中提取的标题、摘要及大纲内容。具体而言，我们使用MinerU（Wang等人，2024a）从文献综述文章语料库中提取内容，并通过基于规则的提取技术分离出层级大纲，包括章节和小节标题。
然而，由于不同文献在格式与结构上的差异，自动提取过程可能会引入噪声。为解决这一问题，我们采用 Claude-3.5-sonnet-20241022 来优化并规范所提取的大纲，从而确保结构和格式的一致性。

利用该文献综述大纲数据库

为此，我们向大语言模型提供高质量、由专家精心编写的大纲示例，以指导其生成过程。此外，我们使用 gte-large-en-v1.5 嵌入模型 124 对这些文档进行编码

(Li等人，2023)，它能够捕捉语义关系，并支持基于相似性的高效检索。这种结构化专家示例与语义编码的结合，为大纲生成和内容检索提供了稳健的基础。

A.2 SurveyBench的详细情况 为了构建SurveyBench，我们选择了表5中计算机科学领域中的10个热门主题。这些主题涵盖了多模态学习、语言模型、计算机视觉和自主系统等各种前沿领域。针对每个主题，由20位研究人员组成的小组精心筛选了高质量、由人类撰写的文献综述。这些研究人员均拥有博士学位，并在上述10个计算机科学领域的热门主题方面具有丰富的专业经验。这种严格的筛选过程确保了主题上的高度契合性，并保证了纳入了权威且相关的文献综述。
此外，我们评估指标的开发（如 SAM-O 和 SAM-C）是受顶级计算机领域的同行评审指南所启发

科学期刊。然而，我们观察到传统的评审标准往往严重依赖评审者的隐性知识与经验，这使得其在自动化评估系统中实施变得困难。为了克服这一局限，我们将这些高级评审指南系统地分解为更具体、可量化的组成部分，以便由大语言模型进行可靠评估，同时保持与专家人工评审的一致性。
例如，在我们的大纲评估标准中，诸如“主题组织”这样的抽象概念被分解为具体的可评估要素，如“主题独特性”（检查是否存在重复主题、内容重叠）和“结构平衡性”（考察章节的构建与比例）。这种细化的方法是通过与具有至少两年顶级计算机科学期刊审稿经验的研究人员讨论而形成的，能够使得不同文献综述中的自动评估更加一致且可靠，同时保留学术同行评审的基本质量标准。这些经过精心筛选的文献综述主要被发表出来

在过去两年内选取这些文献，以确保其时效性与相关性。从每篇选定的文献综述中提取引用的参考文献，为每个主题建立独立的参考文献数据库，从而形成涵盖455篇的综合性参考文献集

[原文第 13 页的完整图表与公式](assets/original-page-013.jpg)

**表格与文字对照**

```text
Topic Ref Num Selected S
Multimodal Large Language Models 912 A Survey
Evaluation of Large Language Models 714 A Survey
3D Object Detection in Autonomous Driving 441 3D Object
Vision Transformers 563 A Survey
Hallucination in Large Language Models 500 Siren’s So
Generative Diffusion Models 994 A Survey
3D Gaussian Splatting 330 A Survey
LLM-based Multi-Agent 823 A Survey
Graph Neural Networks 670 Graph Ne
Retrieval-Augmented Generation for Large Language Models 608 Retrieval-
Table 5: Overview of selected topics and the representati
we show the total number of unique references (Ref Num
selected high-quality surveys that serve as our evaluation
from 330 to 994 references per topic, as detailed in
Table 5. Furthermore, to facilitate robust content
evaluation,we identify the highest-quality survey
for each topic to serve as the evaluation reference,
with these selected surveys demonstrating significant impact through their citation counts (ranging
from 128 to 1,690 citations). SurveyBench provides a comprehensive and reliable foundation for
assessing the quality of AI-generated surveys, ensuring both reference coverage and content relevance are rigorously evaluated.

表内文字对照（数值与原始行列保持不变）：
Topic Ref Num Selected S → 主题参考编号 已选项数
Multimodal Large Language Models → 多模态大语言模型
A Survey → 文献综述
Evaluation of Large Language Models → 大语言模型的评估
D Object Detection in Autonomous Driving → 自动驾驶中的物体检测
D Object → D 对象
Vision Transformers → 视觉Transformer
Hallucination in Large Language Models → 大语言模型的幻觉现象
Siren → Siren
s So → s 所以
Generative Diffusion Models → 生成式扩散模型
D Gaussian Splatting → D 高斯拼贴法
LLM-based Multi-Agent → 基于大语言模型的多智能体系统
Graph Neural Networks → 图神经网络
Graph Ne → 图神经网络
Retrieval-Augmented Generation for Large Language Models → 大语言模型的检索增强生成技术
Retrieval- → 检索-
Table → 表格
Overview of selected topics and the representati → 选定主题概述及代表性内容
we show the total number of unique references (Ref Num → 我们展示了独特参考文献的总数量（参考文献编号）
selected high-quality surveys that serve as our evaluation → 精选的高质量文献综述作为我们的评估依据
from → 从
references per topic → 每个主题的参考文献数量
as detailed in → 如文中所述
Furthermore → 此外
to facilitate robust content → 为了促进稳健的内容生成
evaluation → 评估
we identify the highest-quality survey → 我们确定了最高质量的文献综述
for each topic to serve as the evaluation reference → 每个主题均作为评估参考依据
with these selected surveys demonstrating significant impact through their citation counts (ranging → 这些精选的文献综述通过引用数量显示出显著影响（范围
citations) → 引用)
SurveyBench provides a comprehensive and reliable foundation for → SurveyBench 提供了全面且可靠的基础
assessing the quality of AI-generated surveys → 评估人工智能生成的文献综述的质量
ensuring both reference coverage and content relevance are rigorously evaluated → 严格评估参考文献覆盖率和内容相关性两者
```

A.3 关于生成式文献综述与人工撰写的文献综述的讨论

我们对 SURVEYFORGE 的广泛评估表明其能够在自动生成文献综述方面发挥重要作用，但分析结果显示存在若干根本性的挑战，需要进一步研究。

通过对生成的文献综述进行系统分析，我们发现了当前系统的两个主要局限。第一个局限在于学术分析的深度不足。虽然该系统能够有效提取并整理各篇论文的信息，但在建立多篇文献之间的深刻关联方面存在不足。具体而言，该系统在时间性创新及方法论演变模式的比较分析方面能力有限，往往只能提供机械式的参考文献列表，而无法生成专家撰写的文献综述所具有的深入综合内容。
这一限制主要源于准确识别核心文献以及构建深层逻辑关系所面临的挑战

长格式知识处理过程中的关系构建。第二个挑战涉及内容与引用准确性问题。尽管我们采用了多种验证机制，该系统仍出现……

**表格与文字对照**

```text
Survey Title Citation
on Multimodal Large Language Models 979
on Evaluation of Large Language Models 1690
t Detection for Autonomous Driving: A Comprehensive Survey 172
of Visual Transformers 405
ong in the AI Ocean: A Survey on Hallucination in Large Language Models 808
on Generative Diffusion Models 367
on 3D Gaussian Splatting 128
on Large Language Model Based Autonomous Agents 765
eural Networks: Taxonomy, Advances, and Trends 129
-Augmented Generation for Large Language Models: A Survey 953
ive surveys in our evaluation benchmark. For each topic,
m) collected from SurveyBench, and the citation count of
references.
Evaluation Pair Aspect κ
LLM vs. Human Outline 0.7177
LLM vs. Human Content 0.6462
Human Cross-Validation Outline 0.7921
Human Cross-Validation Content 0.7098
Table 6: Inter-rater agreement between LLM and human
evaluations. κ means the Cohen’s kappa coefficient.
sionally produces inaccurate citations or academic
claims, potentially affecting the survey’s reliability. This remains a critical area for improvement in
automated survey generation systems.
To address these limitations, future work could
focus on developing comprehensive knowledge
association networks through core entity extraction and citation graph construction, which may
enhance the system’s capability to identify deep
inter-publication connections.

表内文字对照（数值与原始行列保持不变）：
Survey Title Citation → 文献综述标题引用
on Multimodal Large Language Models → 关于多模态大语言模型
on Evaluation of Large Language Models → 关于大语言模型的评估
t Detection for Autonomous Driving → 自动驾驶检测
A Comprehensive Survey → 全面文献综述
of Visual Transformers → 关于视觉Transformer
ong in the AI Ocean → AI海洋中的研究
A Survey on Hallucination in Large Language Models → 大语言模型中幻觉现象的文献综述
on Generative Diffusion Models → 关于生成式扩散模型
D Gaussian Splatting → D 高斯拼贴法
on Large Language Model Based Autonomous Agents → 关于基于大语言模型的自主智能体
eural Networks → 神经网
Taxonomy → 分类学
Advances → 进展
and Trends → 及趋势
Augmented Generation for Large Language Models → 大语言模型的增强生成技术
A Survey → 文献综述
ive surveys in our evaluation benchmark → 我在我们的评估基准中进行了文献综述
For each topic → 对于每个主题
m) collected from SurveyBench → m) 从 SurveyBench 中收集
and the citation count of → 以及引用次数
references → 参考文献
Evaluation Pair Aspect → 评估配对维度
LLM vs → 大语言模型与大语言模型
Human Outline → 人类大纲
Human Content → 人类内容
Human Cross-Validation Outline → 人类交叉验证大纲
Human Cross-Validation Content → 人类交叉验证内容
Table → 表格
Inter-rater agreement between LLM and human → 大语言模型与人类评估者之间的一致性
evaluations → 评估
means the Cohen → 指科恩指标
s kappa coefficient → skappa系数
sionally produces inaccurate citations or academic → 在撰写时会产生不准确的引用或学术内容
claims → 声明
potentially affecting the survey → 可能影响文献综述
s reliability → s 可靠性
This remains a critical area for improvement in → 这仍然是需要改进的关键领域
automated survey generation systems → 自动化文献综述生成系统
To address these limitations → 为了解决这些限制问题
future work could → 未来的工作可能
focus on developing comprehensive knowledge → 专注于构建全面的知识体系
association networks through core entity extraction and citation graph construction → 通过核心实体提取和引文图构建建立关联网络
which may → 可能
enhance the system → 提升系统性能
s capability to identify deep → 识别深层的能力
inter-publication connections → 跨期刊关联
```

A.4 人类评估细节及评分者一致性

针对所选10个核心主题的人类评估工作，我们从多个知名机构中招募了20位计算机科学领域的博士专家，其中包括几所QS排名前50的大学以及国内著名的研究机构。这些专家的选拔遵循严格的标准，以确保其专业能力和资质。所有评估人员均拥有计算机科学或相关领域的博士学位，且每位专家在其负责评估的特定领域至少发表过一篇同行评审论文。此外，所有入选的专家均为各自领域活跃的研究人员。为了维持评估的质量和一致性，

每位专家都收到了一份全面的评估指南手册，与我们的大语言模型评估系统所使用的手册完全相同，从而确保所有评估者都遵循一致的评估标准。在正式评估之前，我们进行了456次培训

[原文第 14 页的完整图表与公式](assets/original-page-014.jpg)

会议旨在让专家熟悉评估标准和评分标准。评估过程采用双盲方式进行，以尽量减少潜在偏见。关于报酬，专家按每小时50美元的标准获得报酬，与他们的专业水平相称。每份文献综述的平均评估时间约为1-3小时，以确保评估的全面与可靠。

为了进一步验证评估系统的可靠性，我们进一步进行了Cohen’s kappa系数实验，以衡量自动评估与人工评估之间的评分者一致性，以及不同人工注释者之间的评分者一致性。具体而言，如表6所示，我们对10个不同研究主题下的100篇生成的文献综述进行了系统评估。我们以Cohen’s kappa系数作为评估指标，该指标涵盖了两个核心维度：

大纲与内容。在大纲维度上，基于这100篇文献综述的评估结果，大语言模型评估与人类评估之间的kappa系数达到了0.7177，表明两者存在显著一致性

两者之间。同时，人类评估者之间的交叉验证kappa系数为0.7921。如此高的一致性不仅证明了人类评估的可靠性，也印证了我们自动化评估方法的有效性。在内容维度上，基于相同的样本量，大语言模型评估与人类评估之间的kappa系数为0.6462，而人类评估者之间的交叉验证kappa系数为0.7098。这些结果表明，即使在评估超长文本内容的更复杂任务中，我们的评估框架依然表现出良好的一致性。

A.5 使用开源模型的额外实验 为了验证我们框架的通用性，我们使用最先进的开源语言模型 DeepSeek-v3（Liu等，2024）进行了额外实验。如表7所示，实验结果表明其在所有评估指标上均具有可标记性能。具体而言，DeepSeek-v3在输入方面表现良好

覆盖率为 0.2554，参考覆盖率为 0.4553，在文献覆盖度评估中优于其他基线模型。在大纲质量评估中，DeepSeek-v3 得分为 87.42，不仅超过其他模型，还达到了 124

在由人类撰写的文献综述所设定的基准上表现优异（87.62）。此外，在内容质量结构、相关性和覆盖度这三个维度上，DeepSeek-v3分别获得了79.20、80.17和81.07的得分，平均得分为80.15，优于其他对比模型。这些实证结果不仅证实了我们方法的有效性，还证明了其适用于开源模型。值得注意的是，DeepSeek-v3（Liu等人，2024）在较低的运行成本下（每篇文献综述0.43）表现出更出色的性能（$0.37 per survey) compared to GPT-4o-mini ($ 0.43）。
这种进步对自动化研究工具与方法的可持续发展具有重大意义。

A.6 时间与经济成本详情

SURVEYFORGE框架能够生成长度约为64k个token的完整文献综述，其质量与人工撰写的文献综述相当。生成过程平均需要2.37M个token的输入数据，并产生0.13M个token的输出结果。以GPT-4-mini-2024-07-18为例，其经济成本仅为0.43美元。从时间效率来看，整个框架在大约10分钟内即可完成生成（请注意，实际耗时可能因API速率限制而有所不同）。这些指标表明，SURVEYFORGE框架使研究人员能够以极低的成本高效获取领域知识。

A.7 定性结果

在本节中，我们进行定性比较，以证明所提出的框架在生成具有学术结构的文献综述大纲方面的有效性。具体而言，如图4所示，我们将我们方法生成的大纲与基线方法生成的大纲进行了对比。基线大纲存在若干明显问题。首先，章节与子章节的逻辑组织往往不够理想，层次深度和连贯性有限。此外，还存在将单个研究或论文视为独立子章节的倾向，导致内容碎片化

以及过于细碎的结构。此外，还经常出现重复内容，类似或重叠的主题出现在多个章节中，这降低了清晰度，也破坏了大纲的逻辑连贯性。457

[原文第 15 页的完整图表与公式](assets/original-page-015.jpg)

参考质量方法模型输入协变量参考协变量

人类撰写内容 - - 0.6294 SURVEYFORGE Claude-3-Haiku 0.2231 0.3960 SURVEYFORGE GPT-4o mini 0.2018 0.4236 SURVEYFORGE Deepseek-v3 0.2554 0.4553 表7：开源与……的对比 相比之下，我们框架生成的大纲能够有效解决这些问题。通过采用启发式学习方法并融入领域特定的结构模式，我们的方法能够生成结构清晰、符合学术写作标准的大纲。所生成的大纲具有明确的层次结构、主题连贯性以及相关主题的合理分组，为全面且逻辑清晰的文献综述提供了坚实的基础。

A.8 生成的文献综述示例 如图5所示，我们展示了SURV-VEFORGE生成的文献综述示例，更完整的示例可访问https://anonymous.4open.science/ r/survey_example-7C37/。具体而言，通过……

为了撰写该文献综述，我们发现 SURVEYFORGE不仅能基于逻辑结构总结特定学术领域的知识，还能为一些潜在的研究方向提供有价值的见解与建议。
例如，由 SURVEYFORGE 撰写的文献综述《多模态大语言模型全面综述：进展、挑战与未来方向》中第8节详细探讨了多模态大语言模型（MLLMs）的几种潜在未来技术路径，如可扩展性提升、跨模态交互与整合以及高效训练与推理解决方案。此外，该文献综述还提出了对过度使用 MLLMs 所引发的伦理与社会影响的问题关注，包括其对性别、种族、民族及社会经济地位等问题可能产生的影响。
此外，SURVEYFORGE 还列出了大语言模型的多种应用场景，包括由人工智能驱动的智能体、交互式系统、增强现实（AR），以及医疗和教育等特定领域。

此外，SURVEYFORGE进一步分析了将大语言模型应用于这些实际场景时需要解决的挑战。例如，需要解决计算限制问题，以及应对依赖这些系统的隐私问题 124

内容质量 大纲 质量结构 相关性 覆盖度 平均得分 87.62 - - - - 86.85 73.82 79.62 75.59 76.34 86.62 77.10 76.94 77.15 77.06 87.42 79.20 80.17 81.07 80.15 基于 SurveyBench 上的闭源模型，需要在大量数据的基础上建立稳健的数据管理框架，并获取用户同意。

A.9 提示词使用 本部分概述了 SURVEYFORGE 中使用的关键提示词，包括用于大纲生成、内容撰写和评估的提示词。大纲生成提示词包含两个核心要素：人类撰写的文献综述结构以及该主题相关的文献资料。该提示词确保生成的大纲符合学术规范，章节标题与研究主题保持一致，在保持各章节逻辑关联的同时避免重复。内容生成提示词则指导大语言模型撰写文献综述的各个部分，要求其具备相应的写作能力

生成的内容需有相关文献的引用支持，并明确长度限制以确保清晰与精准。对于评估用提示词，我们依据大纲和内容共同制定评估规则。在大纲评估方面，大语言模型被要求从主题独特性、结构平衡性、层级清晰度及逻辑组织性等方面进行评分，每个方面的总分即为大纲的整体得分。在内容评估方面，我们参考人类撰写的文献综述：大语言模型首先浏览同主题的人类文献以建立背景信息，然后再对人工智能生成的内容进行评估。
这种方法将评估基于成熟的学术写作实践，从而提升了评估的可靠性。

[原文第 16 页的完整图表与公式](assets/original-page-016.jpg)

大语言模型在文献综述中的应用

大语言模型相关综述 1. 视觉变换器简介 1.1 视觉变换器简介 1.2 从变换器到视觉变换器 1.3 视觉变换器的架构 1.4 视觉变换器的优势与局限 2. 视觉变换器架构与进展 2.1 双视觉变换器（Dual-ViT） 2.2 SpectFormer 2.3 FcaFormer 2.4 现代图像深度网络中的变换器与卷积机制解析 2.5 ViTALiTy 2.6 UniNeXt 3. 视觉变换器的应用与基准测试 3.1 图像分类 3.2 目标检测 3.3 语义分割 3.4 视频理解 3.5 多模态任务 4
视觉变换器的效率与优化 4.1 视觉变换器的模型压缩技术 4.2 基于硬件的视觉变换器优化 4.3 视觉变换器的高效训练策略 5 视觉变换器的鲁棒性与可解释性 5.1 对抗攻击的鲁棒性 5.2 分布偏移的处理 5.3 可视化与可解释性 6 视觉变换器的预训练与迁移学习 6.1 视觉变换器的自监督学习 6.2 视觉变换器的知识蒸馏 6.3 视觉变换器的迁移学习与微调 7
未来趋势与挑战 7.1 视觉变换器与其他深度学习方法的融合 7.2 基于视觉变换器的自监督与无监督学习 7.3 将视觉变换器扩展到其他模态 多模态大语言模型：一项全面综述 1 多模态大语言模型简介 1.1 多模态大语言模型的兴起与重要性 1.2 多模态建模方法 1.3 多模态大语言模型的应用与应用场景 1.4 多模态大语言模型的挑战与局限性 1.5 伦理考量与安全问题 1.6 未来的研究方向
结论 2 多模态数据集与基准测试 2.1 多模态数据集与基准测试 2.2 SEED-Bench-2——多模态大语言模型基准测试 2.3 Charting New Territories——探索多模态大语言模型的地理与地理空间能力 2.4 多模态数据集与基准测试——文献综述 2.5 超越文本——通过多API基准测试揭示大语言模型的多模态能力 2.6 MME——多模态大语言模型综合评估基准 2.7 MLLM-as-a-Judge——使用视觉语言基准测试评估多模态大语言模型-as-a-Judge 2.8 MULTI——包含文本与图像的多模态理解排行榜 3 架构改进与训练
策略 3.1 架构组件 3.2 训练策略 3.3 特定模态编码器 3.4 联合表示学习 3.5 多模态融合 3.6 预训练目标 4 应用与用例 4.1 医疗应用 4.2 教育与培训 4.3 可访问性与包容性 4.4 多模态生物医学研究 4.5 伦理与负责任开发 5 挑战与限制 5.1 多模态幻觉 5.2 跨模态对齐 5.3 可解释性 5.4 评估与基准测试 5.5 缓解策略 5.6 伦理考量 5.7 未来方向与结论 6 伦理考量与安全性 6.1 偏见、隐私与用户同意 6.2 潜在问题
针对滥用和恶意使用场景 6.3 透明度与可解释性 6.4 环境与社会影响 6.5 治理与监管框架 6.6 未来挑战与研究方向 7 未来方向与结论 7.1 多模态大语言模型的变革潜力 7.2 新兴趋势与创新应用 7.3 应对挑战与缓解局限性 7.4 负责任开发与伦理考量 7.5 迈向通用人工智能 图4：不同文献综述大纲的对比 基准结构较为零散，而组织良好的大纲则更为清晰。124

大语言模型在文献综述中的应用

大语言模型视觉变换器的全面综述 1. 引言 2. 视觉变换器架构 2.1 原始视觉变换器 2.2 混合视觉变换器架构 2.3 高效轻量级视觉变换器 2.4 多尺度与分层视觉变换器 3. 视觉变换器训练与优化 3.1 预训练和迁移学习技术 3.2 视觉变换器的数据增强方法 3.3 视觉变换器训练的正则化技术 3.4 视觉变换器的高效训练与微调策略 3.5 解决视觉变换器训练中的挑战 3.6 视觉变换器训练的新兴趋势 4.
视觉Transformer应用 4.1 图像分类与识别 4.2 目标检测、分割及实例分割 4.3 视频理解任务 4.4 多模态与跨模态应用 5. 视觉Transformer的可解释性 5.1 注意力机制的可视化与解读 5.2 对学习到的表示进行探索与分析 5.3 生成人类可理解的解释说明 5.4 可解释性的挑战与机遇 6
高效且可扩展的视觉Transformer 6.1 高效视觉Transformer的架构创新 6.2 令牌减少与稀疏化技术 6.3 硬件感知优化与加速技术 6.4 量化与精度降低技术 6.5 高效训练与微调策略 6.6 基准测试与部署考量 7
结论：关于多模态大语言模型的全面文献综述 1 引言 2 多模态模型架构与学习框架 2.1 多模态模型架构 2.2 多模态学习框架 2.3 多模态推理与解释 2.4 多模态对齐与模式连接 2.5 高效多模态模型设计 3 多模态预训练与数据集 3.1 多模态预训练目标与任务 3.2 大规模多模态数据集 3.3 多模态数据预处理与表示 3.4 多模态数据增强与合成 3.5 多模态预训练策略与技术 4 大语言模型评估
与基准测试 4.1 多模态任务分类体系与评估套件 4.2 评估指标及其对大语言模型评估的适用性 4.3 现有大语言模型评估方法的挑战与局限 4.4 构建稳健且通用的大语言模型评估框架的策略 4.5 迈向标准化与自动化的大语言模型评估 4.6 多模态大语言模型的新兴评估前沿 5 多模态应用与案例研究 5.1 多模态语言生成 5.2 多模态理解与推理 5.3 以多模态任务为导向的应用 5.4 新兴多模态领域及新应用 6 局限性与未来研究方向 6.1 大语言模型的局限性
多模态理解与推理能力 6.2 大语言模型训练与部署中的可扩展性与计算效率挑战 6.3 推进多模态知识表示与推理的发展 6.4 提升大语言模型的泛化能力与少样本学习能力 6.5 将大语言模型与其他人工智能系统结合以实现全面的多模态智能 7 结论：基准方法（左）与我们提出的框架（右）。我们的方法能够提供更全面、更系统的结果 459

[原文第 17 页的完整图表与公式](assets/original-page-017.jpg)

SSuurrvveeyy PPaappeerr GGeenneerraa

图5：由 SURVE science/r/survey_example-7C37/生成的文献综述示例，用于更多自动生成内容

aatteedd bbyy SSuurrvveeyyFFoorrggee

EYFORGE。请参考 https://anonymous.4open. 生成的结果。

[原文第 18 页的完整图表与公式](assets/original-page-018.jpg)

生成

大纲：

SUBSECTION_OUTLINE_WITH_SURVEY_PROMPT = ''' 作为人工智能领域的专家，请撰写一份全面的大纲。您已制定了以下整体大纲：--- [整体大纲] --- 您需要丰富 **[章节名称]** 部分的内容，该部分被描述为：**[章节** 主要任务：通过确定内容的重要性和复杂度，为 **[章节名称]** 制定一个全面的框架）。
每个小节应重点介绍提供的**资源**：1. **一份包含标题、摘要及发表日期的 [RAG NUM] 篇相关论文列表 --- [论文列表] --- 2. **人类研究的标题、摘要、前两部分大纲及发表时间 --- [文献综述列表] --- *注意：* 这些文献综述可能并非直接围绕**[主题]**展开。
只有我们这类由人类撰写的学术文献综述论文才具有典型性。**如何使用提供的资源：** - 利用相关论文确定核心主题与最新进展，并 - 参考人类撰写的文献综述以了解典型结构以及 **[主题]** 和 **[章节名称]**。 - 整合两种来源的信息以形成全面且最新的内容 - 在编写大纲时优先关注最新进展与新兴趋势 **指南：** 1. **相关性：** 每个小节必须与 **[章节名称]** 相关 2. **原创性：** 从人类撰写的文献综述中汲取灵感以指导结构安排 3. **逻辑顺序：** 按逻辑顺序排列各小节，形成循序渐进的体系
子小节与其要点之间不存在重叠，4. **灵活性**：子小节的数量应由实际情况决定，应优先实现全面覆盖，而非严格遵循固定数量。5. **独立性**：每个子小节都应包含**具有信息价值的描述**，这些描述不得重复且需与子小节内容相契合，数量则应根据该部分的实际范围进行调整。每个要点都应具备信息价值的描述。**输出格式：** <format> 子小节 1：[子小节1名称] 描述 1：[子小节1的信息性描述] 1. [子小节2中关键方面或子领域的信息性描述]...
第2小节：[第2节名称] 描述2：[第2节的信息性描述] 1. [第...节的关键方面或子领域的信息性描述] 第K节：[第K节名称] 描述K：[第K节的信息性描述] 1. [第2节的关键方面或子领域的第一关键方面或子领域的信息性描述] <br> 注意：小节数量（K）应适合内容主题，并为详细内容的创作提供明确的指导。

仅返回大纲，不提供其他信息：''' 内容：您需要在 [主题] 章节下撰写子部分“[子部分名称]”。作为杰出的专家，请提供融合学术内容的内容。您的文献综述整体大纲如下：\n --- [整体大纲] --- 124

离子提示词

关于**[主题]**的文献综述。

[描述说明]** 应设置适当数量的子章节（通常为3-6个），并根据内容特点进行调整，并随后附上说明性描述。

本部分的日期：**

可能与[主题]相关的书面文献综述。

用于理解逻辑结构、写作风格和学术表达方式

**[章节名称]**中的重要概念。使用学术化的表达，但请确保你的大纲具有原创性，并针对该章节量身定制当前框架。同时需提及基础概念，并与相关描述保持一致。注意避免抄袭，确保思路连贯递进。必须呈现该章节的不同方面，符合**[章节名称]**的内容要求。虽然包含3-6个小节，且每个小节中不超过3个子领域要点，但这些要点无需保持一致性。
你可以添加或代表该章节的关键方面或子领域，随后是 1]

2] N 2]

K]

**[章节名称]**的内容。确保描述具体，包含关键内容

n “[章节名称]”——一篇具有顶尖水平且内容全面的文献综述，包含创新性的见解。

[原文第 19 页的完整图表与公式](assets/original-page-019.jpg)

以下是作为参考文献的论文列表：\n --- [论文列表] --- <指令> 现在，请专注于撰写“[子章节名称 [词数] 字”子章节的内容。子章节重点：--- [描述] --- 核心要求：1. 内容结构——以对子章节范围的简洁概述开始；保持逻辑连贯性并运用清晰的过渡句；以综合分析与未来方向作为结尾；平衡内容的广度和深度。2
学术分析——对不同方法进行对比分析——评估其优势、局限与权衡——识别新兴趋势与挑战——精确呈现技术细节——在必要时包含方程式或正式定义 3. 引用规范——应尽可能引用与“[子章节]”相关的相关文献 t——注意“论文标题”必须采用‘[]’格式才能出现。——请记住，只能引用上述提供的论文，且仅引用一次。——整合：用相关引用支持核心观点——示例：“林等人”
[论文标题1] 已经表明……进一步的研究 [论文编号4]
关键见解——应整合信息而非简单总结——应揭示不同方法之间的关联——应强调实际意义——应提出创新观点或未来研究方向——应以实证证据支持论点——全程保持学术语气 质量指标：- 体现深入的技术理解力- 提供新颖的见解与分析- 保持客观的学术语气- 呈现连贯的叙事逻辑- 通过引用支持所有核心论点 请记住，您工作的质量应反映所期望的标准——论证得到充分支持的程度以及您的见解对学术界具有价值，取决于本小节的质量。
</instruction> 请以如下格式提供“[SUBSECTION NAME]”子节的内容：<format> [子节内容] </format> 仅返回超过 [WORD NUM] 字的文本，因为您的写作提供了全面且深入的分析，符合高学术水平要求，具有深刻的分析深度，并对该领域具有潜在的贡献价值。

在回复的开头不要重复该子章节标题。开始 d ''' 124

“ME]”位于“[SECTION NAME]”之下。您撰写的内容必须多于

[关于名称]”。以‘[]’格式呈现“文献标题”，以支撑你的内容。一旦提及“文献标题”，必须将其包含在‘[]’内。他“文献标题”！！！title2; paper_title3] 确认……

顶级学术出版物中的 d。你的分析应当全面，你的社区。以你作为领先专家的声誉来对待这项任务

无其他信息的子节[子节名称]，确保其符合上述标准。您的作品将根据该子节的内容直接进行学术评估。

[原文第 20 页的完整图表与公式](assets/original-page-020.jpg)

评估

大纲：

任务：作为一位严谨的学术评估者，针对{主题}进行评估，以确定其能否作为高质量学术综述论文的大纲。

评估主题：{ai_outline} <指令> 您的任务是对所生成的文献综述大纲进行评估。评估重点：**仅关注大纲质量**。大纲评估标准（共100分）：1. 主题独特性（30分）——各章节/小节中无重复主题；每章内容均具有唯一性；不存在冗余的“未来展望”或“结论”部分；相关主题之间区分明确。2. 结构平衡性（30分）——主要内容的各小节数量分布合理；无明显发展不足的章节；无过度详细以至于主导整个大纲的章节；小节数量的差异应与主题重要性相符。3.
层级清晰度（20分） - 清晰的父子关系 - 各章节角色对应的合适主题层级 - 符合学术惯例的逻辑细分 - 在适当情况下保持一致的粒度
逻辑结构（20分）——遵循学术规范的自然主题推进——各章节间关系清晰——主题分组连贯——内容流与章节功能匹配合理 评分等级：90-100：卓越——无内容重复——结构平衡完美——层级分明——逻辑流畅 70-79：合格 60-69：薄弱——存在部分主题重复——明显冗余——结构略显不均匀——章节比例失衡——仅维持基本层级——层级不清——逻辑基础——主题推进不佳 内容覆盖：**任务**：作为专业文献综述评估员，对{主题}相关的人类撰写参考文献进行评估。**注意**：
人类撰写的评论仅作为参考 p **覆盖质量定义：** 覆盖质量指所涵盖相关概念的全面性、深度及广度，以及相应的关注程度 人类撰写评论（参考）：--- {human_review} --- 用于评估的生成评论：--- {ai_review} --- 124

n 提示词

人工智能生成的大纲质量如何。你需要判断其是否合格

真实评论。

章节数量/复杂度

80-89分：优秀——内容重叠极少——结构整体平衡——层次结构良好——逻辑连贯清晰
低于60分：较差——重复内容较多——结构严重失衡——层次关系混乱——无逻辑结构——仅具备生成文献综述的**覆盖质量**

作为参考标准而非绝对标准。文献综述中主题处理的平衡性，包括对每个领域的重视程度。

[原文第 21 页的完整图表与公式](assets/original-page-021.jpg)

**覆盖度评估标准（总分为100分）：** 1. **主题全面性（35分）** - 涵盖的关键主题范围 - 对新兴领域的涉及程度 - 关键概念的识别 评分指南：- 30-35：涵盖全面且包含新兴主题 - 20-29：覆盖良好但存在轻微缺失 - 0-19：存在重大遗漏或严重空白 3. **内容平衡性（30分）** - 主题的比例覆盖情况 - 重点分配的合理性 - 空间的逻辑安排 评分指南：- 25-30：整体覆盖均衡 - 15-24：总体平衡但存在轻微问题 - 0-14：存在显著不平衡问题 **评分要求：** - 优先追求准确性而非保守性 - 避免
“安全”的中等范围得分无法反映真实质量——每个得分必须体现精确的表现水平，而非范围平均值——使用完整的评分范围（0-100）——基于与人类参考标准的客观对比来设定基础分数——承认最佳实践可能会随时间发展**输出格式**：仅返回一个数值得分（0-100）。
无额外评论 ''' 内容相关性：**任务：** 作为专业文献综述评估员，仅针对{主题}领域的人类撰写参考文献进行评估。**注意：** 人类撰写的评价仅作为参考依据。**相关性质量定义：** 文献综述中的相关性质量指共同信息以及讨论重点对**参考材料**关键方面的覆盖程度与深度。**参考材料：** 人类撰写评价（参考文献）：--- {人类评价} --- 用于评估的生成评价：--- {AI评价} --- **相关性评估标准（总分为100分）：** 1. **主题匹配度（35分）** - 核心方面的覆盖情况 - 与研究重点的契合度 - 相关讨论的深度
评分指南：- 30-35：与内容全面性高度契合 - 20-29：契合度良好但存在少量不足 - 0-19：严重不匹配或存在重大缺陷 3. **信息重点（30分）** - 专注于关键点 - 无无关内容 - 有目的的内容选择 评分指南：- 25-30：聚焦明确且偏差极小 - 15-24：聚焦合理但包含部分无关内容 - 0-14：聚焦不佳或偏差过大 124

2. **讨论深度（35分）** – 概念分析的详细程度 – 核心论点的构建 – 解释的全面性 评分指南： - 30-35：各主题均具有卓越的深度 - 20-29：深度良好但存在一定差异 - 0-19：处理方式始终较为肤浅

ty。评分完全基于实际表现，而非设定“舒适区间”的评分标准（例如，20-29岁年龄段得分为25）

ntary。

生成文献综述的**相关性质量**，不应作为绝对标准来比较。

内容与所指定的主题一致，所包含的主题内容也符合要求。

2. **内容适宜性（35分）** – 示例与证据的相关性 – 讨论的精确性 – 与主题核心的关联度 评分指南： - 30-35分：高度相关且讨论精确 – 20-29分：基本相关但存在轻微不一致 – 0-19分：包含多个不相关元素或精确度不足

[原文第 22 页的完整图表与公式](assets/original-page-022.jpg)

**评分要求：** - 优先注重准确性而非保守性 - 避免使用无法反映真实质量的“安全”中等分数 - 每个分数必须体现精确的表现水平，而非范围平均值 - 使用完整的评分区间（0-100） - 基于与人类参考标准的客观对比来设定基础分数 - 承认最佳实践可能会随时间发展而变化 **输出格式：** 仅返回一个数值分数（0-100）。不添加任何额外说明 ''' 内容结构： **任务：** 作为专业文献综述评估员，仅针对{主题}领域的人类撰写参考文献进行评估。

注意：人工撰写的评论仅作为参考点，**结构质量定义**：文献综述中的结构质量指其组织方式、观点之间的关联方式以及主题的发展情况。**参考资料**：人工撰写评论（参考）：--- {human_review} --- 用于评估的生成评论：--- {ai_review} --- **结构评估标准（共100分）**：1. **逻辑连贯性与组织性（35分）** - 观点的逐步发展 - 概念间的有效过渡 - 清晰的论证脉络 评分指南：- 30-35分：逻辑连贯性极佳，过渡自然 - 20-29分：整体逻辑合理，存在轻微不足
流程问题 - 0-19：严重的组织问题 2. **层级结构（35分）** - 章节/子章节安排 - 主题层级清晰度 - 内部连贯性 评分指南： - 30-35分：结构清晰，有助于理解 - 20-29分：结构基本合理但存在一些不一致性 - 0-19分：层级组织混乱 3. **格式与呈现（30分）** - 标题/子标题使用 - 学术格式一致性 - 视觉呈现方式 评分指南： - 25-30分：格式统一且专业规范 - 15-24分：存在轻微格式不一致 - 0-14分：存在严重格式问题 **评分要求：** - 应优先注重准确性而非保守性 - 避免给出“安全”的中等分数
那些无法反映真实质量的分数——每个分数必须体现精确的表现水平，而非区间平均值——使用完整的评分范围（0-100）——基于与人类参考标准的客观对比来设定基础分数——承认最佳实践可能会发生变化**输出格式**：仅返回一个数值分数（0-100）。不要添加任何额外说明 124

ty。评分完全基于实际表现，而非设定“舒适区间”的评分标准（例如，20-29岁年龄段得分为25）

ntary。

生成的文献综述的**结构质量**如何

并非绝对标准。

数量、逻辑流程以及信息呈现方式。它涵盖了如何组织内容，以及整体结构如何促进对内容的理解

ns

ty。评分完全基于实际表现，而非设定“舒适区间”的评分标准（例如，20-29岁年龄段得分为25）

ntary。

