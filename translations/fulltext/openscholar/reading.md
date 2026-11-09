# OpenScholar：利用检索增强语言模型综合科学文献

OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs

Asai, Akari; He, Jacqueline; Shao, Rulin; Shi, Weijia; Singh, Amanpreet; Chang, Joseph Chee; Lo, Kyle; Soldaini, Luca; Feldman, Sergey; D'arcy, Mike; Wadden, David; Latzke, Matt; Tian, Minyang; Ji, Pan; Liu, Shengyan; Tong, Hao; Wu, Bohao; Xiong, Yanyu; Zettlemoyer, Luke; Neubig, Graham; Weld, Dan; Downey, Doug; Yih, Wen-tau; Koh, Pang Wei; Hajishirzi, Hannaneh

> 非官方机器初译，正文尚未逐段精校。图表保留原文内容，图内英文未另行翻译；有 HTML 原文的公式按原式排版。PDF 提取版保留对应原页，点击缩略图放大核对图表与公式。

原文版本：2411.14199v1 · [原始来源](https://arxiv.org/abs/2411.14199v1) · [中文 PDF](../../../output/pdf/openscholar-zh-reading.pdf)

## 摘要

科学进步依赖研究者综合不断增长的文献的能力。语言模型（LM）能否帮助科学家完成这一任务？我们提出 OpenScholar，一种专门的检索增强语言模型：它从 4,500 万篇开放获取论文中识别相关片段，并综合生成有引用支持的回答。为评价 OpenScholar，我们建立了 ScholarQABench——首个大规模、多领域的文献检索基准，包含计算机科学、物理学、神经科学和生物医学领域的 2,967 个专家编写的问题和 208 个长篇回答。在 ScholarQABench 上，尽管 OpenScholar-8B 是规模更小的开放模型，其正确性仍分别比 GPT-4o 和 PaperQA2 高出 5% 和 7%。GPT-4o 编造引用的比例为 78%–90%，而 OpenScholar 的引用准确性达到与人类专家相当的水平。OpenScholar 的数据存储、检索器和自反馈推理循环也能改善现成语言模型：例如，OpenScholar-GPT4o 使 GPT-4o 的正确性提高了 12%。在人类评价中，相对于专家撰写的回答，专家选择 OpenScholar-8B 和 OpenScholar-GPT4o 回答的比例分别为 51% 和 70%，而 GPT-4o 的相应比例为 32%。我们开放了全部代码、模型、数据存储、数据以及公开演示。

**表格与文字对照**

```text
Demo | | openscholar.allen.ai/
Blog | | allenai.org/blog/openscholar
OpenScholar code | | github.com/AkariAsai/OpenScholar
ScholarBench code | | github.com/AkariAsai/ScholarBench
Checkpoints, Data, Index | | OpenScholar/openscholar-v1
Expert Evaluation | | AkariAsai/OpenScholar_ExpertEval

表内文字对照（数值与原始行列保持不变）：
Demo → 演示
openscholar → 开放学者
allen → 艾伦
ai/ → 人工智能/
Blog → 博客
allenai → allenai
org/blog/openscholar → org/blog/openscholar
OpenScholar code → OpenScholar 代码
github → github
com/AkariAsai/OpenScholar → com/AkariAsai/OpenScholar
ScholarBench code → ScholarBench 代码
com/AkariAsai/ScholarBench → com/AkariAsai/ScholarBench
Checkpoints → 检查点
Data → 数据
Index → 索引
OpenScholar/openscholar-v → OpenScholar/openscholar-v
Expert Evaluation → 专家评估
AkariAsai/OpenScholar_ExpertEval → AkariAsai/OpenScholar_ExpertEval
```

[查看原图表（阅读版）](bilingual.html#openscholar-0026)

图1：（顶部）OpenScholar概述：OpenScholar由专门的数据存储库、检索器及大语言模型组成，通过结合检索的自我反馈推理机制来逐步优化回答。（中间）ScholarQABench概述：ScholarQABench包含2,200个来自多个科学领域的专家编写的问题，我们针对ScholarQABench引入了自动评估与人工评估方案。（底部）自动评估与人工评估结果：实验结果表明ScholarQABench具有显著效果，而经过我们训练的8B或GPT4o版本的OpenScholar表现优于其他系统，在人工评估中超过50%的时间都优于专家系统。

## 1 引言

整合科学文献中的知识对于发现新的研究方向、完善研究方法以及支持基于证据的决策至关重要。然而，每年发表的论文数量庞大，使得研究人员难以及时获取最新信息。有效的整合工作需要精确的检索、准确的归属标注以及对当前文献的实时访问能力。尽管大语言模型在辅助研究人员方面具有潜力，但它们也面临诸多挑战，包括幻觉现象（Mallen等，2023；Mishra等，2024）、依赖过时的预训练数据（Kasai等，2023）以及缺乏透明的归属标注机制。
例如，在需要引用最新文献的任务中，我们的实验中 GPT-4 在计算机科学和生物医学等领域有 78-90% 的案例中伪造了引用内容。

另一方面，基于检索增强的大语言模型（Lewis等，2020；Guu等，2020）通过在推理阶段整合检索到的外部知识来源，能够缓解许多问题，从而推动文献搜索与合成系统的发展（Agarwal等，2024；Zheng等，2024；Skarlinski等，2024）。然而，许多此类系统依赖于黑盒式API或通用大语言模型，这些模型既未针对文献合成进行优化，也未能与适合科学领域使用的开放、领域特定的检索数据存储库（即经过处理的语料库及相应的检索索引）结合使用。
此外，针对科学文献整合的评估工作十分有限，通常依赖单一学科的小规模人工评估（Agarwal等，2024；Zheng等，2024），或采用简单的任务如选择题回答（Skarlinski等，2024）。

为了填补这些空白，我们提出了 OpenScholar（图1顶部），这是一种先进的检索增强型大语言模型，拥有专门的文献数据存储库以及基于科学文献训练的检索器。在推理过程中，OpenScholar会检索相关段落，并通过迭代自我反馈生成机制来优化其输出结果。我们还训练了新的高效8B大语言模型。为了评估 OpenScholar 的有效性，我们引入了 ScholarQABench（图1中间部分），这是一个专门设计的基准测试工具，旨在实现真实且可重复的开放式科学问题回答评估。

OpenScholar（第2节）使用我们的新版 OpenScholar - DataStore（OSDS），该数据库包含来自 Semantic Scholar的4500万篇开放获取论文以及2.37亿个对应的段落嵌入数据。据我们所知，这是科学领域最大的开源数据存储库。OpenScholar首先通过检索器和重新排序器从 OSDS 中检索段落，随后由大语言模型对这些检索到的段落进行整合，以生成带有引用信息的回复。OpenScholar通过自然语言反馈不断优化其输出结果，从而提升质量并自适应地纳入补充信息。
该流程还被用于为更小、更高效的模型生成大规模、高质量的训练数据。我们从采样的数据存储段落中生成合成查询和指令，将其输入到 OpenScholar 系统中，并利用中间和最终输出来训练开放 8B 模型、OpenScholar -8B 模型以及检索模型。

ScholarQABench（第3节）是一个用于评估模型理解与整合现有研究能力的基准测试。与那些假设答案仅存在于单一文献中的先前基准测试不同（例如科学事实核查研究；Wadden等，2020；Skarlinski等，2024），许多现实场景需要识别多篇相关文献，并生成包含准确引用信息的长篇输出内容。为了应对这些挑战，我们整理了一组2,967个文献综合问题以及208篇由专家撰写的长篇回答，这些回答涉及计算机科学、物理学、生物医学和神经科学四个科学领域。
这些回复由拥有三年以上经验且在该领域有相关出版成果的博士学生和博士后研究人员撰写。平均而言，每一条回复的撰写时间约为一小时。我们还引入了一种多维度评估方案，结合自动化指标与人工评估，以衡量引用准确性、事实正确性、内容覆盖度、连贯性及整体质量。这种多维度方法能够确保自动和人工驱动的评估都具有稳健性和可重复性。

我们在 ScholarQABench上对具有和缺乏检索功能的专有及开源模型（如 GPT4o、Llama 3.1 8B、70B），以及像 PaperQA2 这样的专用系统（Skarlinski等，2024年）进行了评估（第4节）。虽然 GPT4o 表现出良好的整体性能，但在引用准确性和覆盖率方面存在不足，常常产生不准确或不存在的引用。OpenScholar 则优于仅基于语言模型的流程和带有检索增强的流程，甚至超过了专有及开源系统。
值得注意的是，使用完全开源的检查点模型，OpenScholar在基于专有大语言模型的PaperQA2（Skarlinski等，2024）以及Perplexity Pro等生产系统中均取得了6%和10%的性能提升。此外，OpenScholar采用更小、更高效的检索器显著降低了成本。将OpenScholar与GPT4o结合使用后，其正确性也比单独使用GPT4o提升了12%。OpenScholar流程还能提升现成的大语言模型性能，例如，当以GPT-4o作为底层模型时，OpenScholar-GPT4o的正确率相比单独使用GPT-4o提升了12%。

除了在 ScholarQABench 上的自动评估外，我们还邀请了来自计算机科学、物理学和生物医学领域的16位专家进行了详细评估（第5节）。这些专家对 OpenScholar 的输出与 ScholarQABench 中针对文献综合查询的108份专家撰写回复进行了成对及细致评估。当 OpenScholar 与 GPT-4o 以及我们训练的8B模型结合使用时，其表现始终优于专家撰写的回复，分别获得了70%和51%的胜率。
相比之下，没有检索功能的 GPT-4o在信息覆盖度方面存在不足，其帮助程度低于人类专家，对人类回复的回应成功率仅为 31%。这凸显了 OpenScholar 生成的输出更为全面、结构清晰，且有助于文献整合。这些研究结果表明，OpenScholar 产生的高质量输出不仅与专家撰写的答案具有竞争力，在某些情况下甚至更胜一筹，尤其是在信息覆盖度和组织性方面。

OpenScholar -8B 是一种开放式的检索增强型大语言模型，它无需依赖专有大语言模型或检索系统，能够利用科学文献领域中最大的数据存储库之一。我们发布了完整的 OpenScholar 生态系统，包括代码、训练好的检索模型、模型检查点、数据存储库、ScholarQABench 基准测试、专家评估工具以及公开演示平台。

## 2 OpenScholar：用于整合科学文献的大语言模型与检索增强技术

OpenScholar（详见图2）是一种基于检索增强的大语言模型，旨在为各种关于科学文献的信息查询提供可靠且高质量的回复。

### 任务构建。

针对一个科学查询 $x$，任务在于识别相关的文献，综合其研究结论，并生成能够有效解答该查询的回应 $y$。该回应应附带一组引用信息 $\mathbf{C}={c_{1},c_{2},\ldots,c_{K}}$，其中每个引用 $c_{i}$ 都对应一篇现有的科学论文。$\mathbf{C}$ 中的每个 $c_{i}$ 均来自科学文献的特定段落，应按照科学写作的标准做法，以在线引用形式呈现，并与相关文本片段相关联。
这些引用使得研究人员能够将输出结果追溯到原始文献，从而确保透明性和可验证性。

### OpenScholar 概述

为确保能够检索到相关文献并生成高质量输出，ScholarQABench由三个关键组件构成：数据存储系统、检索器以及大语言模型生成器。在标准的检索增强推理流程中，整个过程始于基于输入查询的语义相关性，从大规模已发表科学论文语料库中检索一组段落——这些段落作为下一步的上下文。
该生成器大语言模型 $\mathcal{G}$ 随后会结合检索到的段落 $\mathbf{P}$ 和输入查询 $x$，生成输出 $y$以及相应的引用信息 $\mathbf{C}$。从形式上看，这一过程可以表示为：

[查看原图表（阅读版）](bilingual.html#openscholar-0042)

**表格与文字对照**

```text
| $y,\mathbf{C}=\mathcal{G}(x,\mathcal{R}(x,\mathbf{D})),$ |

表内文字对照（数值与原始行列保持不变）：
mathbf → mathbf
mathcal → mathcal
```

其中，每个 $c_{i}$ 在 $\mathbf{C}$ 中对应 $\mathbf{P}$ 中的特定段落。在 OpenScholar 系统中（图 1），我们利用了专为科学领域设计的多种专用组件：OpenScholar - DataStore $\mathbf{D}$、OpenScholar - Retriever/- Reranker 以及大语言模型，从而能够灵活使用现成的大语言模型（如 GPT4o）或我们新训练的 OpenScholar -LM。我们开发了基于自我反馈的检索增强推理机制，以提升可靠性与引用准确性。

OpenScholar - DataStore (OSDS) 是一个包含4500万篇科学论文的数据库，我们基于该数据库构建嵌入向量。我们在科学数据上训练 OpenScholar - Retriever 和 OpenScholar - Reranker，这些模型会将最关键的段落传递给生成器（第2.1节）。随后，我们采用基于检索的迭代自反馈推理机制：大语言模型首先使用特定参数生成初始草案，然后通过基于检索的自反馈机制逐步优化其输出（第2.2节）。我们利用这一流程生成高质量训练数据（第2.3节），从而能够训练出能产生更高质量输出和更精准引用的专业大语言模型。

[查看原图表（阅读版）](bilingual.html#openscholar-0046)

图2：OpenScholar推理（上）与训练（下）的详细概述。在推理过程中，给定输入$x$后，OpenScholar首先使用检索器从专用数据存储库中识别相关论文（OpenScholar -Datastore），然后利用重新排序器对检索到的文档进行优化和筛选，选出前$N$篇文档。这些检索结果随后被传递给大语言模型，该模型生成（1）初始响应$y_{0}$和（2）自我反馈$f_{1}$。通过整合自身的反馈，大语言模型会反复迭代优化其输出，直至达到预定义的次数。
随后，大语言模型(1)生成初始响应 $y_{0}$，(2)对初始输出进行自我反馈，然后(3)将反馈 $f_{i}$ 纳入其中以生成更新后的响应 $y_{1}$。该大语言模型重复此过程直至所有反馈都被整合完毕。为了训练一个规模较小但性能相当的8B大语言模型，我们采用这种推理阶段流程生成高质量训练数据，随后进行数据筛选与混合处理。

### 2.1 OpenScholar 检索管道

图2（左上角）展示了我们的检索流程，包括一个数据存储系统 $\mathbf{D}$、一个双编码器检索器 $\theta_{\text{bi}}$ 以及一个交叉编码器重排序器 $\theta_{\text{cross}}$。我们首先使用 $\mathbf{D}$ 和 $\theta_{\text{bi}}$ 以及外部 API 选择初始候选段落，随后通过 $N$ 对这些段落进行优化和筛选，最终选出最相关的 $\theta_{\text{cross}}$ 段落。

### 收集科学论文以构建数据存储库。

虽然以往的研究通常仅使用少量论文，例如 2023-2024 年的 arXiv 论文（Zheng 等，2024），但拥有多样化的论文集合对于提升模型生成的质量与覆盖范围至关重要（Shao 等，2024）。为此，我们采用 peS2o（Soldaini 等，2024）作为检索来源，该数据集包含来自 S2ORC 的开放获取学术论文（Lo 等，2020）。我们基于 peS2o v3 构建数据仓库，其中包含了截至 2024 年 10 月的 4500 万篇论文。
2 2 2 在评估方面，我们使用 peS2o v2 作为主要基准，该数据集包含截至 2023 年 1 月的文献，因为我们的模型和基准是在 v3 版本整理之前构建的。依据先前的研究（Shao等人，2024），我们将每篇文献的主要文本划分为独立的 250 词文本块（通过空白字符确定），并将文献标题与每个文本块拼接起来，从而生成 $\mathbf{D}$ 格式的文本段落。我们的数据存储包含 2.34 亿个文本段落。据我们所知，这是最大的开源科学文献数据存储库。

### 检索初始段落。

我们从三个来源检索段落：(1) 使用训练好的检索器对 peS2o 数据存储进行检索；(2) 根据搜索关键词，通过 Semantic Scholar API 获取论文的公开摘要（Kinney 等，2023）；(3) 使用原始查询 $x$ 通过网络搜索引擎检索到的论文中的公开文本。对于第 (1) 项，我们首先使用段落双编码器 $\theta_{\text{bi}}$ 以 $\mathbf{D}$ 格式生成每个段落的嵌入向量，该编码器可在离线状态下将文本块（如查询或段落）转换为密集向量（Karpukhin 等，2020）。现成的检索模型通常在领域外场景中表现不佳（Thakur 等，2021）。
为了克服这些限制，我们通过以无监督方式持续在 peS2o 数据存储上预训练 Contriever（Izacard等，2022），从而提升特定领域的检索性能（详情见附录 C.1）。在推理过程中，我们使用 $\theta_{\text{bi}}$ 对查询进行编码，并通过最近邻搜索（Karpukhin等，2020）获取前 100 篇相关段落。对于第（2）项，我们首先使用生成式 LLM从查询中生成关键词 $x$，随后利用 Semantic Scholar 搜索 API，根据引用次数对这些关键词对应的前 10 篇论文进行排序后进行检索。
这种方法解决了 Semantic Scholar API 的一个缺陷，即无法有效处理长且类似问题的搜索查询。对于第(3)项研究，我们利用 You.com 检索 API 获取前10个搜索结果，并将搜索范围限制在 ArXiv 和 PubMed 等学术平台上。如果论文为开放获取，我们会提取其全文并纳入候选库；否则，仅包含其摘要。

### 重新排序并确定最优秀的段落。

在初始阶段之后，我们每次查询都能收集到超过100条甚至上千条相关段落。然而，由于查询与段落之间存在深度交互，由双编码器检索到的段落可能包含无用的上下文信息，因为这些内容是分别编码的（Asai等，2023）。向大语言模型输入大量可能包含无关内容的文档，即使使用最先进的模型也会导致效率与性能问题（Liu等，2024；Xu等，2023a）。为了克服这些挑战，我们使用了一个交叉编码器重排序器（Nogueira & Cho，2019；Xiao等，2023），其标记为$\theta_{\text{cross}}$。
对于每个候选段落，跨编码器重排序器会共同编码输入查询与各个段落之间的相关性得分，然后利用该得分对段落进行排序。为了训练适用于科学领域的 $\theta_{\text{cross}}$，我们使用 Llama 3 70B Instruct 生成的合成数据对 BGE-重排序器（Xiao等人，2023）进行微调。具体而言，我们基于 peS2o 的摘要随机生成查询，并检索前10个段落。随后，Llama 3 70B Instruct 为这些段落分配1到5的相关性得分，其中4或5分视为正面得分，1或2分视为负面得分。得分为3的段落则被排除。
关于 $\theta_{\text{cross}}$ 训练的更多细节见附录 C.2。在重新排序及确定前 $N$ 篇目时，我们还实施了额外的元过滤机制，包括：(1) 每篇论文的篇目数量限制为三篇；(2) 将标准化引用次数纳入交叉编码器预测的相关度得分中。

### 2.2 推理：基于检索增强自反馈的迭代生成

在标准的检索增强生成（RAG；Lewis等，2020；Ram等，2023）中，生成器大语言模型接收原始输入 $x$，并检索到前 $N$ 个段落 $\mathbf{P}$，进而生成输出 $y_{0}$。尽管这种一步式生成方法适用于问题回答等任务（Mallen等，2023），但可能导致无依据的断言（Liu等，2023）或因信息缺失而产生的不完整输出（Asai等，2024；Jiang等，2023）。
为应对这些挑战，在 OpenScholar 中我们引入了一种包含自我反馈的迭代生成方法，该过程包含三个步骤：(1) 生成初始响应与反馈，以输出初始草稿 $y_{0}$ 以及一组相关反馈 $y_{0}$ ；(2) 通过额外的检索进行迭代优化，利用反馈改进 $y_{0}$ ；(3) 引用验证。详细内容请参阅附录。

### 初始响应与反馈生成。

给定输入 $x$ 和检索到的段落 $\mathbf{P}$，生成器大语言模型首先生成初始回应 $y_{0}$，并在 $\mathbf{P}$ 中设置与对应段落相关的引用标记。在生成完 $y_{0}$ 后，该模型会在 $y_{0}$ 和 $\mathbf{F}={f_{1},f_{2},\ldots,f_{T}}$ 上生成一组反馈内容，旨在优化初始回应，其中每一条反馈 $f_{t}$ 都是描述潜在改进的自然语言句子。尽管模型可以生成任意数量的反馈（$T$），但我们设定了最多三条反馈句子的上限，以实现高效的推理过程。
与依赖预定义反馈信号集的先前研究（Asai等，2024）不同，我们的方法使大语言模型能够针对回复的多个方面生成灵活的自然语言反馈，例如组织性、完整性或所需补充信息。如果反馈序列识别出缺失内容（例如：“答案仅包含QA任务上的实证结果。请添加其他任务类型的结果。”），大语言模型还会根据第2.1节中的流程生成检索查询以进行额外检索。

### 迭代优化。

我们随后对反馈进行迭代处理，以逐步优化输出结果。如果反馈表明需要进一步的检索，则使用查询内容进行额外段落的检索，并将这些段落添加到初始输出中，最终生成最终的文本。虽然每次收到反馈都可以重新生成输出，但这样做会引入额外的延迟。经验表明，反馈往往具有多样性，能够涵盖生成的多个不同方面。因此，依次整合初始输出的反馈仍然有效。
该大语言模型使用之前的输出 $y_{k-1}$、检索到的段落 $\mathbf{P}$，以及任何新检索到的段落，来生成更新后的输出 $y_{k}$。这一过程不断重复，直到所有反馈问题都得到解决，最终在指定时间步长 $T$ 下产生最终输出 $y_{T}$。

### 引用验证。

最后，我们指示大语言模型验证 $y_{t}$ 中的引用情况。具体而言，该模型会确保所有具有引用价值的陈述——即需要依据支撑的科学主张——都能通过检索到的段落中的参考文献得到充分支持。如果某些陈述缺乏适当的引用，大语言模型会进行事后补充，以确保这些具有引用价值的陈述有相应的段落作为支撑。在我们的处理流程中，我们不会删除那些没有具有引用价值的陈述的句子。

### 2.3 训练：通过推理管道生成高质量合成数据

由于缺乏针对此问题的训练数据，构建能够有效整合科学文献的强大大语言模型具有挑战性。尽管有一些用于训练科学领域大语言模型的资源（Wadden等，2024），但大多数任务并不需要开放检索机制，且均为单篇论文相关任务。因此，该领域的大部分先前研究（Skarlinski等，2024）依赖于专有大语言模型，这给可复现性和推理成本带来了困难。

我们利用推理阶段流程通过自我反馈机制合成高质量训练数据，从而使得最终模型能够在无需进行自我反馈过程的情况下，更擅长生成高质量输出（图2底部）。

### 问题和回答生成。

我们的数据生成过程包含三个步骤：首先，从 $\mathbf{D}$ 中选取被引用最多的文献；其次，根据这些文献的摘要生成信息查询；最后，利用 OpenScholar 推理阶段管道生成高质量回复。我们使用 LLama 3.1 70B 模型进行数据生成（Dubey 等，2024）。具体而言，我们首先从 peS2o 数据集中抽取100万篇论文的摘要，并提取这些被检索文献的元数据，如发表年份或引用次数。
然后我们随机选取了10,000篇2017年之后发表的论文，接着引导大语言模型根据每篇摘要生成文献综述问题或信息查询需求，这些问题可能需要多篇论文才能解答。接下来，我们使用OpenScholar流程生成最终输出$y_{T}$，同时还会生成反馈$\mathbf{F}$和初始输出等中间结果。

### 数据筛选。

尽管大语言模型具有高效性和可扩展性，但合成数据也可能存在幻觉、重复写作或指令遵循能力有限等问题（Li等，2024c）。为解决这些问题，我们引入了两步数据过滤机制：成对过滤与评分标准过滤，并使用与数据生成相同的大语言模型。在成对过滤过程中，我们对比模型输出的质量——$y_{T}$（最终步骤的输出）与$y_{0}$（初始输出），并保留被判定为质量更高的输出。我们发现，由于多次迭代后的过度编辑或冗余现象，约20%的情况下更倾向于选择$y_{0}$而非$y_{T}$。
我们随后在五个等级范围内，从组织结构和事实准确性及引用精度两个方面对所选回答的质量进行评估。有效的模型输出必须在这两个类别中均达到4.5或更高的分数，我们将那些输出不符合此要求的实例排除在外。更多细节请参见附录。

### 数据混合与训练。

基于这一合成训练流程，我们生成了三种类型的训练数据：答案生成 $(x\rightarrow y)$、反馈生成 $(y_{0}\rightarrow\mathbf{F})$ 以及反馈整合 $(y_{t-1},f_{t}\rightarrow y_{t})$。我们发现，在训练过程中同时使用最终输出与中间输出有助于较小的大语言模型学会生成更有效的反馈。我们进一步将这种合成训练数据与现有的通用领域指令调整数据（Ivison等，2023）及科学领域指令调整数据（Wadden等，2024）进行融合，确保 50% 的训练数据来自科学领域，而剩余 50% 则来自通用领域数据。
我们还基于 peS2o 中抽样的摘要数据生成合成事实验证及布尔式问答数据。为此，我们按引用次数对论文进行排序，选取前 100,000 篇论文。关于数据混合与训练的更多细节，请参见附录 C.3。数据混合完成后，我们在大规模合成训练数据上训练生成器 LLM。随后，我们在生成的训练数据上训练 Llama 3.1 8B Instruct。

## 3 ScholarQABench：由博士专家标注的现实化文献综述评估基准

### 挑战与概述。

先前关于构建大语言模型以综合科学文献的研究，要么采用小规模、单一领域的人工评估方法（Agarwal等，2024；Zheng等，2024），要么使用过于简化的选择题问答模式（Skarlinski等，2024）。构建高质量的文献综述基准数据存在两个主要挑战：首先，创建此类数据集需要大量资源，因为需要博士级别的领域专业知识和研究经验，尤其是对真实问题及高质量答案进行标注时。
其次，即使拥有高质量数据，要可靠地评估长文本自然语言回答仍然面临重大挑战，尤其是在专家领域（Xu等，2023b；Xu等，2024）。这与其他科学过程的评估基准不同，例如自动化实验代码生成，后者更容易获得更明确的评估标准，如Pass@1（Si等，2024）。

为了填补这些空白，我们引入了 ScholarQABench 这一基准测试工具，该工具支持多种科学文献综合任务形式，包括封闭式分类、选择题以及长文生成，如表1所示。我们采用了三个现有的单篇论文数据集，随后构建了用于计算机科学、生物医学、物理学和神经科学领域的高质量、专家标注数据集（第3.1节）。我们还建立了可靠的自动评估流程（第3.2节）。表1列出了 ScholarQABench 中的任务列表，图3则展示了评估流程的示例及整体概况。

[查看原图表（阅读版）](bilingual.html#openscholar-0077)

表1：ScholarQABench概述。前三行展示了从先前数据集中提取的单篇论文数据集；后四行则是我们通过招募博士级别专家构建的新数据集。回答∗表示该数据集仅包含问题，而回答†则表示答案将依据人工标注的评分标准进行评估。评估列对应第3.2节中的多维度评估方式。“多篇论文”列则表明任务是否需要使用多篇论文来作答。LLM和Expert分别指由评估大语言模型LLM（即Prometheus；Kim等人，2024a）和人类专家进行的细粒度评估。

### 3.1 数据整理

ScholarQABench旨在评估大语言模型在自动化科学文献综述方面的能力。其筛选过程由三个关键因素指导：任务多样性：ScholarQABench包含多种输入输出格式的任务；学科多样性：与通常仅关注计算机科学等单一学科的先前研究不同，ScholarQABench涵盖了四个科学领域；多篇论文任务的纳入：与仅针对已预先选定的单篇论文进行研究的先前工作不同，所有任务都需要从完整的开放获取论文全文集合中检索数据（第3.1.1节）
以及四个数据集特别要求对多个检索到的论文进行推理分析（第3.1.2节）。

### 3.1.1 单篇论文任务

对于单篇论文任务，我们筛选并调整了现有的常用单篇论文数据集。图15展示了单篇论文任务的示例；更多细节见附录B.2。

### SciFact。

SciFact（Wadden等，2020）是一个包含1.4K篇由专家撰写的生物医学领域科学论断的数据集，这些论断与带有标签和解释说明的现有PubMed论文摘要中的黄金证据相对应。我们包含了被标记为“支持”（正确）或“矛盾”（错误）的验证集查询，并删除了原始黄金证据，将任务重新设计为二元检索任务，即系统需要从大量论文中识别出相关的论文。

### PubMedQA。

PubMedQA（Jin等，2019）包含来自PubMed论文摘要的由专家标注的（是/否/可能）问答数据。与SciFact类似，我们仅保留带有“是”或“否”标签的数据样本，并丢弃原始摘要段落，从而将任务构建为一种开放检索模式。

### QASA。

QASA（Lee等人，2023年）是一个单一的文献综述QA数据集，包含问题回答对，需要针对人工智能与机器学习领域的科学文章进行推理。我们评估模型能否充分回答关于目标文献的详细问题。虽然原始数据集包含三个子任务（答案选择、理由生成及答案组合）以及端到端QA机制，但我们基于端到端QA设置来评估模型的性能。

[查看原图表（阅读版）](bilingual.html#openscholar-0089)

图3：ScholarQA-CS示例及评估概览。ScholarQA-CS包含100道问题，以及平均4.4份专家编写的评分标准作为评估依据。我们的ScholarQABench评估流程会考量正确性与引用精度等指标。

### 3.1.2 多篇论文任务

单篇论文的封闭集任务或许能够提供可靠的评估结果。然而，它们可能无法反映现实场景——在现实场景中，复杂的开放式问题会独立于现有论文被提出，并需要跨多篇论文的检索与推理。目前很少有数据集（Xu等人，2024；Malaviya等人，2023）涉及包含真实查询的多篇论文设置，且大多数缺乏可靠的评估流程或人工编写的参考文献。我们通过整理三个由专家标注的新长格式问答数据集来填补这一空白，以应对这些具有挑战性的场景（详情见附录B.2）。此外，我们的多篇论文任务涵盖了四个科学领域。

### ScholarQA-CS

我们招募了该领域的博士专家——包括教授、博士后研究员和研究科学家——收集了来自多个计算机科学学科的100个问题以及每个问题的详细答案评分标准。这些注释者的任务是撰写需要结合多篇研究论文才能解答的文献综述问题，问题主题涵盖网络、算法、物联网、人工智能和人机交互等领域。
然后，针对每个问题，另外两位注释者通过网络搜索，制定了一份评分标准，其中列出了正确回答的关键要素及其重要性等级（“必须包含”与“理想包含”），并提供了各要素的相关来源引用。注释者被要求在任务初期阶段不使用任何大语言模型服务。在初步网络搜索之后，注释者会以随机顺序看到来自四种大语言模型服务的相应回复（Claude 3.5 Sonnet、GPT-4o、Perplexity Pro以及基于Claude 3.5的未发表RAG原型），以便他们能够修改自己的评分标准。
平均而言，每个问题都包含 4.4 个关键要素，且每个要素都有 4.4 条引用支持。

为了衡量一致性，我们让两位注释者为随机选取的10道问题样本分别制定评分标准。随后，使用自动化方法对注释者所接触的4种大语言模型服务的回答进行评分，每套评分标准对应一次计算。最后，我们计算了各题得分之间的皮尔逊相关系数并取平均值。由于评分标准注释任务具有主观性，我们在得分中同时纳入了通用标准和不纳入的情况，结果分别为79.3和59.5。图3展示了一个示例，更多示例及详细内容见附录E.2。

### ScholarQA-Bio、ScholarQA-Neuro

我们进一步收集了2,759个由专家撰写的生物医学与神经科学领域的文献综述问题，这些专家均为相关领域拥有博士学位的研究科学家和工程师。标注人员被要求从自己的专业领域中选择论文，并根据对这些论文的解析，提出生物医学科学家可能提出的复杂科学问题。我们针对生物成像、遗传学、微生物学及神经调节等不同领域分别收集了相关问题。由于标注成本较高，我们仅专注于对这些问题进行整理与筛选。
完整说明与示例可在附录 6 和 E.3 中找到。

### ScholarQA-Multi.

最后，我们收集了108个文献综述问题以及由专家撰写的带有引用信息的答案，这些内容涉及四个领域：计算机科学（人工智能/机器学习、人机交互）、生物医学（生物成像、遗传学）、物理学（天体物理、光子学、生物物理学）。所有注释工作由拥有相应领域三年以上研究经验且有多篇第一作者论文的博士学生或博士后科学家完成。我们要求他们提出与最新文献相关的问题，并利用通过搜索找到的相关论文来撰写这些问题的解答。
我们的标注人员被要求不得使用任何基于大语言模型的系统，如 ChatGPT，并且只能使用常规搜索工具（例如 Google 搜索）或文献搜索系统（例如 Semantic Scholar）。表 14 展示了所收集的问题与答案的统计数据，各主题的分布情况见图 6(a)，同时还有每个主题的平均标注时间。我们在附录 E.4 中提供了几个示例。平均而言，每位标注人员处理每个实例需要 56 分钟。

### 3.2 指标与评估方案

我们开发了一种多维度自动评估流程，以实现可重复且高效的评估工作，从而补充专家评估的作用。我们的评估结果大纲见图3。

### 正确性（Corr）。

正确性指标用于衡量模型生成的答案与人工标注的参考内容之间的重叠或匹配程度。该指标仅适用于包含人工标注答案的任务。对于给定固定答案类别的短格式生成任务，即 SciFact 和 PubMedQA，我们采用准确率作为正确性指标。对于 QASA，我们遵循 Lee 等（2023）的研究方法，使用 ROUGE-L 作为评估指标。对于 ScholarQA-CS，我们开发了一种新的长格式评估流程，该流程采用专家标注的评分标准，每个评分标准包含两个维度：通用维度（占得分的 40%）和标注驱动维度（占 60%）。
一般标准包括长度、专业水平、引用次数和摘录内容的评估，而基于注释的标准则涉及对注释者所确定的特定关键要素的考察。GPT4o-turbo会对每个标准进行评分，然后计算加权总和以得出最终得分。更多细节见附录B.3.1。

### 引用准确性（Cite）。

对文献综述问题的长文回答进行评估需要引用准确性：大语言模型应正确标注所有具有引用价值的陈述所对应的相关证据。在 ScholarQABench 中，所有系统生成的输出都包含与推理过程中提供的段落相连接的引用编号（例如 [1]、[2]）。借鉴之前的研究（Gao等人，2023；Liu等人，2023），我们测量了引用精确度和召回率。具体而言，我们检查每个具有引用价值的陈述是否拥有适当的引用，以及这些引用是否能够支持该陈述（引用召回率，Cite-r）。
对于每一条引用，我们进一步验证其相关性和必要性——即该引用是否支持相关陈述，以及删除该引用是否会影响其余引用的完整性（引用精确性，Cite -p）。最后，我们还计算了引用F1值（Cite -F1），并将其作为衡量引用准确性的主要指标。由于引用准确性无需金标准参考答案或评分标准，因此我们在所有任务中均采用这一评估方法。

### 内容质量与结构（大语言模型，专家）。

我们进一步定义了除了“相关度”或“引用量”之外用于评估生成答案的关键指标。具体而言，我们考察了与问题的相关性（Rel）、话题覆盖度（如所讨论论文的多样性）以及深度（如细节的充分性），还有组织结构与写作流畅性（Org）。这些指标很难用标准指标来衡量。由于大语言模型能够有效遵循详细的评估评分标准（Zheng等，2023a；Kim等，2024a），我们采用Prometheus v2（Kim等，2024a）根据定义的评分标准分配五级评分，并采用相同的框架进行人工评估。在人工评估中，我们还进一步考察了整体实用性（Use）。
此评估的完整说明见附录 B.3。正如先前研究所示，当没有黄金参考答案时，大语言模型的可靠性较低（Kim等人，2024b），因此本次评估仅适用于包含人类标注参考答案的任务，即ScholarQA-Multi。我们分析了人类评估与模型评估在细致方面的一致性（附录 D.2），发现模型的评估结果往往与人类的排名一致，尤其是在组织和覆盖度方面具有更高的相关性。

## 4 实验与结果

### 4.1 实验细节

### 模型。

首先，我们评估了开放版与专有版大语言模型，包括 Llama 3.1（8B、70B）和 GPT-4o（gpt-4o-2024-05-13）。在这种设置下，每个大语言模型独立生成答案，无需外部检索，并提供一份引用的文献标题列表。为了进行评估，我们核实所生成的文献标题是否存在；如果存在，则检索其对应的摘要作为引用。对于多篇文献任务，我们还对其他专有系统进行了评估：Perplexity Pro、5 5 5 https://www.perplexity.ai/。实验采用了付费订阅版本。
请注意，Perplexity Search没有API接口，因此我们使用selenium工具包从界面中获取其最终预测结果。由于此原因，我们无法检索到其引用信息。而PaperQA2（Skarlinski等人，2024年）是一种同时进行的文献综述智能体系统，它使用GPT4o进行重新排序、摘要生成和答案生成。我们使用了他们的官方代码库。由于PaperQA2不公开其检索语料库，且需要离线下载PDF文件，所以我们下载了由我们的检索管道及Semantic Scholar API推荐的论文的PDF文件。
与 PaperQA2 不同，我们无法获取私有或受许可保护的文献，这可能会在一定程度上限制我们复现研究的有效性。然后，我们使用 OpenScholar-DataStore (+OSDS) 对模型进行评估，在该系统中我们检索出排名前 $N$ 的段落，并将其与原始输入拼接后输入模型。最后，我们利用自定义的推理时间管道以及训练好的 8B 模型（OS-8B）、Llama 3.1 70B 和 GPT4o（OS-70B、OS-GPT4o）来评估我们提出的 OpenScholar 模型。

### OpenScholar 的详细信息。

我们采用 peS2o v2 作为默认数据存储系统。不同数据存储方式的影响在附录 D.1 中进行了分析。在 OpenScholar 中的 $\theta_{\text{bi}}$ 和 $\theta_{\text{cross}}$ 部分，我们使用经过训练的双编码器和交叉编码器模型，分别包含 1.1 亿和 3.4 亿参数。我们将从网络搜索和 Semantic Scholar 中检索的论文数量上限设定为 10 篇。对于生成式 LLM，我们将温度参数设为 0.7，并将响应生成的最大令牌数限制为 3,000，反馈生成的最大令牌数限制为 1,000，同时使用 vllm 包以加快推理速度。我们使用 torchtune 在 13 万个训练样本上训练了两个周期的 Llama 3.1 8B 模型。
更多细节见附录 C。对于所有模型，我们在单篇论文任务中设置输入给生成式大语言模型的段落数为五段，在多篇论文任务中则设置为十段。除了 SciFact 和 PubMed 外，未提供少样本演示，而在这些领域我们提供了单样本演示。

### 4.2 结果

[查看原图表（阅读版）](bilingual.html#openscholar-0114)

表2展示了主要基准模型的多个方面的得分情况。总体而言，OpenScholar表现处于顶尖水平，其性能显著优于GPT4o及其标准RAG版本，也远超如PaperQA2（Skarlinski等，2024）这样的专业文献综述系统。

### 单篇论文任务。

在单篇论文任务中，OpenScholar始终优于其他模型。如表2所示，OS-8B和OS-70B在最终Corr和Cite指标上，无论是否进行检索增强，均优于Llama 3.1 8B和70B。OS-70B甚至在PubMedQA和QASA任务中与GPT4o相当或表现更优。

表2：ScholarQABench的结果。CS、Multi、Bio和Neu分别代表Scholar-CS、ScholarQA-Multi、ScholarQA-Bio和ScholarQA-Neuro。Corr表示正确率指标（PubMedQA和SciFact的准确率，QASA的ROUGE-L值，ScholarQA-CS的整体得分），Cite表示引用F1值。LLM表示根据Prometheus（Kim等人，2024a）研究预测的Org（组织）、Rel（相关性）、Cov（覆盖度）的平均得分。∗PaperQA2基于GPT4o构建，其定价取决于推理过程中使用的PDF文件数量。
对于 8B 和 70B 模型的成本，虽然评估是在本地机器上进行的，但我们是根据 Together.ai 的定价来估算成本的。∗∗ 我们使用了 Perplexity Pro 工具（需要每月支付 20 美元的订阅费），并将该费用除以 9,000，即 Pro 订阅下允许的最大查询数量。由于 Perplexity 界面不提供每篇引用的片段内容，因此我们无法评估其引用准确性。

[查看原图表（阅读版）](bilingual.html#openscholar-0120)

表3：计算机科学与生物医学领域虚假论文的统计数据。我们的分析显示，在缺乏检索机制的LLM预测中，存在大量不存在的被引用论文，这是OpenScholar中未出现的问题。

### 多篇论文任务。

OpenScholar -8B、70B以及GPT4o（OS-8B、OS-70B和OS-GPT4o）在多篇文献处理任务中表现出优异性能。具体而言，OS-GPT4o在Scholar-CS Corr任务中比GPT4o本身提升了12.7分，比标准RAG方案提升了5.3分。当与训练过的OS-8B结合使用时，OpenScholar的表现显著优于使用现成Llama 3.1 8B的流程，充分展现了特定领域训练的优势。此外，OpenScholar -8B的表现也大幅超过了GPT4o、Perplexity Pro或PaperQA2等专有系统——这些系统使用GPT4o模型进行段落重新排序、摘要生成和答案生成。
值得注意的是，通过利用高效的检索流程以及轻量级双编码器、跨编码器和内部模型，OpenScholar -8B与OpenScholar -GPT4o能够大幅降低成本——其成本比PaperQA2低数个数量级——同时仍保持高性能。

### 参数化大语言模型的局限性。

在单篇论文和多篇论文任务中，我们观察到非检索增强基线模型表现不佳，而检索几乎总能提升性能；缺乏检索功能的模型往往难以生成正确的引用信息，在多篇论文任务中的覆盖范围也较为有限。如表3所示，实际存在的被引用论文比例极低。尤其值得注意的是，尽管GPT4o和Llama等模型能够生成合理的参考文献列表，但我们发现78-98%的被引用论文都是虚构的，这一问题在生物医学领域更为严重。
即使引文指向真实的论文，大多数引文也未能得到相应摘要的支撑，导致引用准确率几乎为零。

我们还观察到，这类模型生成的回答覆盖范围也较为有限。在 Scholar-Multi平台上，非检索模型（Llama 3.1 8B、70B以及GPT4o）的平均得分与检索增强模型相比始终显著较低。这种差异主要源于其 Cov得分低得多：例如，Llama 3.1 8B的Cov得分为3.45，而Llama 3.1 8B + OSDS（一种标准的RAG基线模型）将其提升至4.01。这些结果表明，在科学领域，仅依赖模型的参数化知识尤其困难，尤其是对于较小的大语言模型而言。

### 4.3 分析

(a) 对 OpenScholar 不同组件的剔除实验。

(b) Scholar-CS 上排名前 N 的消融实验（Corr）。

(c) Scholar-CS 上的前 N 名消融实验（Cite-F1）

[查看原图表（阅读版）](bilingual.html#openscholar-0131)

图4：OpenScholar分析：(a) 基于不同底层大语言模型，对OpenScholar训练与推理关键组件的消融研究。(b) 前N篇文档：分析不同上下文块数量对最终下游任务影响的研究。我们使用OpenScholar 8B和Llama 3.1 8B，以引用准确率和多文档问答任务的正确性作为最终模型性能评估指标。

### 剔除研究。

我们进行了各种消融实验，以评估 OpenScholar 中各个组件的有效性（包括推理和训练）。具体而言，我们去除了所有的推理阶段流程，包括重新排序、反馈和归因机制；对于 OS-8B 模型，我们还去除了训练过程，直接使用 Llama3-8B 模型而不进行任何额外训练。

如图4(a)所示，移除这些组件显著影响了模型输出的整体正确性和引用准确性。值得注意的是，移除重排序模块导致两种模型的性能都大幅下降。在GPT4o中移除反馈回路后，性能出现明显下降，这表明更强大的模型能从自我反馈机制中获得巨大收益，这与Madaan等人（2023）的研究结果一致；而在我们训练的8B模型中，这种机制仅导致有限的性能下降。此外，事后归因评估的移除对引用准确性和最终输出正确性都产生了负面影响，这凸显了确保模型验证其输出的重要性。
经过训练的大语言模型与普通 OS-8B 模型之间的显著性能差距表明，利用高质量、特定领域的数据进行进一步训练是构建高效、任务专用大语言模型的关键。在后续分析中，我们证明训练对大语言模型有效利用更多上下文的能力有着显著影响，同时又能保持引用准确性。

### 上下文段落数量。

我们分析了上下文段落数量的变化对模型性能的影响。具体而言，我们使用训练好的8B模型和Llama 3.1 8B，在Standard RAG和OpenScholar环境中进行了实验，并在Scholar-CS上评估了生成准确性和引用准确性。图4 (b)(c)展示了实验结果。尽管Llama 3.1被训练为能够处理并接受高达128K个令牌的上下文长度，但我们发现当上下文规模超过一定限度后，其性能会下降。虽然将最高$N$上下文窗口从5扩展至10确实能提升模型的准确性得分，但进一步扩展反而会降低准确性和引用准确性。
这表明，尽管大语言模型能够处理大量文本，但在没有专门训练的情况下，它们可能难以有效利用这些文本，尤其是对于较小的模型而言。

相比之下，我们训练好的8B模型在长达$N=20$的段落中仍保持良好的性能。我们还发现，像Llama 3.1 70B这样更大的模型对上下文长度的增加更为稳健。在引用准确性方面，如图4 (c)所示，Llama 3.1 8B的准确率迅速下降，引用F1值低至10，而我们的8B大语言模型和Llama 70B的引用F1值均保持在约40左右，尽管它们也出现了一定的性能下降。

## 5 专家评估

为了补充自动评估结果，并更全面地了解 OpenScholar 的效果与局限性，我们进行了人工评估。本研究涉及超过 100 个文献综述问题及 15 多名参与者，包括博士学生、研究科学家以及相关领域专家教授。最终共收集了超过 400 份针对人类与模型回答的细致专家评估意见。

### 5.1 人类评估设计

### 针对人类专家的评估。

对于人类评估，我们使用了来自 ScholarQA-Multi 的 108 对问题与答案对，这些内容由专家撰写。我们对这些问题运行了三种模型，以生成带有引用信息的答案：GPT4o（无外部检索）、使用 GPT4o 作为生成器的 OpenScholar（OS-GPT4o），以及使用我们训练的 8B 模型的 OpenScholar（OS-8B）。随后，让专业标注员对模型生成的答案与人类撰写的答案进行对比评估。

每次评估都包括一个问题、一个模型生成的答案以及一个人写的答案。专家注释者随后会对每个答案进行细致评估，并给出两者之间的偏好判断。在细致评估中，我们采用第3节中描述的五级评估标准（Cov、Org、Rel），注释者使用相同的评分标准对模型和人类答案进行评分。对于实用性指标（Use），注释者会在1到5的等级范围内打分，我们将其划分为三类：无用（1-2）、中性（3）和有用（4-5）。随后我们计算属于“有用”类别的答案所占的比例。
在成对偏好评估中，标注者可以选择其中一个答案，或如果认为两个答案质量相同，则标记为“平局”。此外，专家也可提供解释说明为何一个答案优于另一个答案。

### 用于回答撰写的大语言模型专家注释者。

负责问答内容标注的专家智能体共有12名博士学生及博士后研究人员，他们均来自美国各研究机构，拥有至少三年的研究经验，并在各自领域的相关期刊或会议上发表了多篇论文。这些标注专家的专业领域涵盖计算机科学（自然语言处理、计算机视觉、人机交互）、物理学（天体物理与光子学/光学）以及生物医学（神经科学、生物成像）等领域，我们会根据问题所属的专业领域来分配标注任务。平均而言，我们向每位专家支付35至40美元的费用。

### 用于评估的大语言模型专家注释员。

来自三个领域的共16位专家注释员参与了我们的评估工作，其中12位还参与了答案的生成。所有专家注释员的资质与撰写答案的人员一致。为了尽可能减少潜在偏见，我们通过将评估任务分配给不同的专家小组，确保注释员不会对自己提出的问题的回复进行评估。根据可用人员情况，每个案例由1至3位专家注释员进行审核。使用配对比较并处理平局时，不同注释员之间的一致性为0.68；采用放宽方法并合并平局时，一致性为0.70。
平均而言，每位专家每个实例需要花费五分钟进行评估，并获得25–35美元的报酬。

[查看原图表（阅读版）](bilingual.html#openscholar-0149)

表4：人类评估结果。根据我们的详细指导与评分标准，在四个方面上使用五点量表对细节层面的评价进行评估。括号中的数值表示相对性能差异；(+)表示模型表现更优，(-)表示人类表现更优。

### 5.2 人类评估结果

[查看原图表（阅读版）](bilingual.html#openscholar-0152)

图5：细粒度评估结果。得分分布分别为：1) GPT4o（最高分），OpenScholar 8B版本（中等水平），OpenScholar 结合 GPT4o 与人工干预的版本（最低分）。

### 人类评估结果。

表4展示了每个评估维度的平均得分，以及与人类回答相比的胜率。图5则展示了使用Llama 3 8B和GPT4o的人类、GPT4o及OpenScholar模型的得分分布。值得注意的是，OS-GPT4o和我们的OS-8B版本在超过50%的情况下都优于人类答案，其优势主要源于能够提供更广泛、更深入的信息（覆盖度；Cov）。相比之下，缺乏检索功能的GPT4o在不到35%的情况下仅获得少量胜率，其整体实用性也远低于人类及其他两个模型的回答。
这些结果表明，即使对于最先进的模型而言，整合并回答科学文献综述问题仍是一项具有挑战性的任务，这与我们在 ScholarQABench 上的研究结果一致。总体而言，OpenScholar -GPT4o 和 OpenScholar -8B 在分别 80% 和 72% 的查询中被评为“有用”。

虽然较小的 8B 大语言模型版本的 OpenScholar 已经能够替代人类专家，但 8B 模型的输出在条理性和流畅性方面仍不如当前最先进的基于私有大语言模型的 OpenScholar。我们发现 GPT4o 能更有效地整合反馈，通常能生成更长且更流畅的输出内容，因此与 8B 版本的 OpenScholar 以及人类相比，其组织性得分明显更高。

### 长度控制对模型回答的影响。

虽然我们发现模型输出往往比人类输出更受青睐，但一个潜在的干扰因素是其输出长度存在显著差异——OpenScholar-GPTo 的输出长度是人类写作答案的 2.4 倍，而 OpenScholar-8B 则长达 2.0 倍，这可能会影响人类的判断（Dubois 等，2024）。为了了解输出长度的影响，我们进行了一项控制实验：针对随机选取的 50 道问题，我们让 OpenScholar-GPT4o 生成较短版本的回答，通过提示 GPT4o 对字数在 300 字以内的回答进行总结来实现。
因此，我们收集了平均约 333 字的 OpenScholar 回答，这一长度与人类回答的平均长度相近。随后进行了相同的人类评估，对细致且全面的回答进行了评价。平均而言，缩短后的 GPT4o 在组织性方面得分为 4.5，在覆盖度方面为 4.6，在相关性方面也为 4.6。在 75% 的查询中，缩短后的 OpenScholar -GPT4o 回答与专家答案相当或更优。实验结果表明，该模型的出色表现并非仅仅源于 OpenScholar 回答长度的增加。
此外，人类注释者的说明通常提到，通过添加更多细节，缩短后的 OpenScholar 结果及人类回答都可以得到改进，这表明 300 字的限制可能会限制这些回答的实用性。

### 关于人类对成对解释的解释行为的分析。

我们随机选取了59个样本，这些样本包含自由形式的成对偏好说明，并进行了手动分析以识别影响整体偏好的因素。具体而言，我们检查了这些说明是否涉及以下四个类别中的一个或多个：组织结构、相关性、覆盖范围和引用。前三个类别与细致的人机评估标准相符，而引用类别则还考虑了被引用的论文的质量（例如，系统是否包含了该领域的重要代表性论文）。
我们的分析显示，在成对决策中，分别有12%、23%、29%和9%的解释将组织性、相关性、覆盖率和引用量视为关键因素。这表明，在人类评估回答质量的过程中，覆盖率起着至关重要的作用，注释者通常更青睐模型生成的答案，因为后者具有更广泛的信息覆盖率和深度。然而，注释者也指出，模型提供的引用内容可以改进，他们提到所推荐的文献有时已过时或不如更具代表性的研究相关。附录15展示了示例解释。

## 6 相关研究

### 科学大语言模型。

科学型大语言模型已应用于多个领域，包括生物医学（Phan等，2021；Yuan等，2022；Luo等，2022）、医学（Singhal等，2023a；Gu等，2024；Tan等，2023；Singhal等，2023b）、生物医学（Zhang等，2024b；Fang等，2024；Li等，2024a）、地球科学（Feng等，2023）、天文学（Nguyen等，2023）以及多学科科学（Shaikh等，2023）。部分模型如SciGLM（Zhang等，2024a）和UniSmart（Chi等，2024）则旨在通过单一模型覆盖多种科学领域。
最近有多项研究表明，强大的通用大语言模型在科学任务中也能展现出强大的能力，例如医疗问题解答（AI4Science & Quantum, 2023；Singhal等，2023a）、化学实验（Zheng等，2023b）以及应用力学领域（Brodnik等，2023）。然而，语言模型依赖于其参数中存储的信息，这导致其输出中频繁出现幻觉现象（Li等，2024b）。

### 大语言模型助力科学家工作。

近期研究还探讨了大语言模型在协助科学家完成各类科学操作方面的能力，包括生成新的研究思路（Baek等，2024；Yang等，2023）以及自动生成实验代码（Huang等，2023；Tian等，2024）。然而，我们的工作则专注于对文献综述进行标准化评估，并开发自动化方法以处理与最新研究相关的问题——这些任务对于科学研究来说至关重要，同时也具有很大的挑战性。
多项同时进行的研究尝试使用专有大语言模型与外部 API（如 Semantic Scholar API）来构建检索增强流程，用于科学文献综述智能体（Agarwal等，2024；Skarlinski等，2024；Wang等，2024）。尽管这些研究和我们的研究都探讨了检索增强大语言模型在自动化文献合成方面的潜力，但以往的研究通常依赖专有且黑盒式的系统，且评估范围有限，往往仅采用小规模人工评估或简单的测试方式，例如选择题问答形式。
相比之下，我们的研究引入了包含自动化指标的全面基准测试，进行了涉及三个科学领域专家的用户研究，并开发了训练专用开放模型的新方法。OpenScholar的表现显著优于以往提出的系统，在五个领域也优于人类专家。

### 科学文献理解基准测试。

已有多项研究开发了评估大语言模型理解科学文献能力的基准测试。以往的数据集如 SciFact（Wadden等，2020）、QASPER（Dasigi等，2021）和 QASA（Lee等，2023）主要针对单篇论文场景，其中回答查询所需的信息都包含于预先选定的单篇论文中。然而在现实场景中，专家通常需要整合多篇论文中的信息来回答问题。为了填补这一空白，ScholarQABench引入了新标注任务，这些任务要求对多篇论文进行综合推理。
还有科学总结任务，例如 Multi-XScience（Lu等人，2020年）项目，其中模型被提供多篇论文，要求生成摘要，通常基于这些论文中的相关工作部分。然而，在本研究中，我们关注那些无法提前指定相关论文的场景，这使得任务更具挑战性。最近，Xu等人（2024年）引入了KIWI数据集，该数据集包含200道问题以及由先进大语言模型生成且经过人类验证或编辑的答案，主要聚焦于自然语言处理领域。KIWI还提供了一组模型必须考虑的相关论文。
虽然 KIWI 和 ScholarQABench 都包含多篇文献及信息检索任务，但 ScholarQABench 还包含人工撰写的答案和自动评估流程。相比之下，KIWI 则更侧重人工评估，其参考答案主要由模型生成。

## 7 结论

为了进一步研究能够助力科学进展的大语言模型相关系统，我们引入了 OpenScholar 和 ScholarQABench，这两个工具可以帮助应对复杂且不断增长的科学文献综述任务。作为一种基于检索增强的系统，OpenScholar 利用开放的检查点大语言模型和训练好的检索模型来逐步优化科学成果，从而解决幻觉现象和引用准确性等问题。而新型大规模基准测试 ScholarQABench 则提供了一种标准化的方法，用于评估不同科学领域中的文献综述自动化水平。
在使用 ScholarQABench 进行的评估中，OpenScholar 取得了显著改进，其表现优于现有的系统，包括 GPT-4o 以及同期的专有系统 PaperQA2。我们在三个科学领域进行的专家评估表明，当 ScholarQABench 与完全开放检查点模型及开放访问数据存储相结合时，其生成的答案比专家标注员每小时需花费一小时的答案更有帮助，且覆盖范围也大幅扩大。使用我们训练的 8B 模型和 GPT4o 的 OpenScholar 在针对人类生成答案的测试中分别获得了 51% 和 70% 的正确率。
我们开源了 OpenScholar 代码、数据、模型检查点、数据存储以及 ScholarQABench，并提供了公开演示版本，以支持和加速未来的研究工作。

### 局限性

在本节中，我们指出了本研究的若干局限性。需要指出的是，我们并不声称基于大语言模型的系统能够完全实现科学文献的自动化合成。为了推动该领域的研究发展，我们正在向社区发布 ScholarQABench 和 OpenScholar 工具。

### ScholarQABench 的局限性。

ScholarQABench 存在若干局限性。首先，由于需要耗费成本与时间来聘请专家标注员——这些人员通常拥有博士学位或正在相关领域攻读学位——包含人工回答的评估数据集规模相对较小（例如，CS-LFQA 的数据集为 110 条，专家撰写的答案数据集为 108 条）。这种有限的数据集可能会引入统计波动，并因标注员的特定专业背景而产生潜在偏差。为了支持未来在扩大 ScholarQABench 规模与范围方面的研究，我们将其数据及标注流程开源共享。

其次，我们的自动评估流程可能并不总能准确反映生成内容的质量。例如，在 Scholar-CS 中，我们采用启发式确定的权重机制来整合各种要素（如长度、摘录、评分标准项）。此外，我们发现标注者通常在评分标准中要求特定类型的辅助信息——背景说明、详细阐述及挑战点——尽管这些方面未必是回答问题的必要条件。
在我们的实验中发现，大语言模型能够熟练生成背景信息，这使其比那些直接回答查询但无法满足评分标准所有要求的系统具有优势。此外，未来的系统或许可以利用评分标准中的风格偏见，被引导去处理更多评分标准要素，而无需提升答案质量。尽管我们仔细分析了最终得分与人类专家评估之间的关联，但在确定应强调哪些方面以及如何汇总这些得分方面仍有改进空间。
此外，我们对引用精确度和召回率的评估是在句子层面进行的，但我们发现一些没有直接引用的句子往往由相邻句子中的引用支持。因此，我们的精确度和召回率指标可能过于严格，从而可能低估了真实的引用准确性。我们还注意到，我们的注释是在特定时间采集的（Scholar-CS为2024年7月，Scholar-Multi为2024年9月），可能无法反映后续的科学发展情况。使用我们评估基准的研究人员应忽略这些日期之后发表的论文，以便进行公平比较。

最后，ScholarQABench主要聚焦于计算机科学、生物医学和物理学领域，没有来自社会科学或其他工程与科学学科的研究案例。我们认识到，我们的研究结果可能无法完全适用于其他领域，尤其是那些获取论文数据较为受限的领域。

### OpenScholar 的局限性。

正如相关章节所讨论的，尽管 OpenScholar 在 ScholarQABench 测试及人工评估中表现优异，但我们的专业注释者发现了若干局限性。尽管存在这些问题，我们认为 OpenScholar 仍然是支持人类专家的重要工具。

首先，正如我们的专家注释者所指出的，OpenScholar 在某些查询下无法始终检索到最具代表性或相关的论文。通过引入额外信息，如引用网络或出版时间等元数据来改进检索方法，可以显著提升其性能。OpenScholar 的输出可能包含事实错误或不具依据的信息，尤其是在基于 8B 模型的版本中，该模型在遵循指令和获取科学知识方面能力有限。未来的研究可以探索进一步训练以改进 OpenScholar-8B 的效果。
同时，尽管 OpenScholar-GPT4o 具有竞争力，但它依赖自研的 GPT4o API，而该 API 可能会随时间发展变化，因此难以完全复现实验结果。在推理过程中，OpenScholar 不会使用受许可保护的文献。目前正在就如何确保检索增强型大语言模型中的数据使用公平展开讨论，我们将如何合理融合受版权保护的内容问题留待后续研究解决。

我们鼓励未来的研究解决这些局限性问题，并继续改进基于大语言模型的科学文献综述系统。

### 我们人工评估过程的局限性。

在我们的人类评估中，注释者对涵盖性、相关性、组织性和实用性等方面进行了细致评估，而引用精确度和召回率等其他因素则被单独评估。因此，在评估实用性或成对偏好时，注释者可能更关注文章的整体质量，而未能仔细审查事实准确性或引用精度。关于引用精度、有效性和事实性的详细人类分析，我们留待后续研究进行。

我们的评估工作由16名博士学生和博士后专业人士完成，我们努力使他们的专业背景与所评估的主题相匹配。然而，由于研究通常需要深厚的领域知识，标注人员可能无法准确捕捉其专业领域之外问题的更细微差异。此外，这些评估基于涵盖三个科学领域的108个问题，因此研究结果可能无法完全适用于其他领域或学科。

### 作者贡献

作者的贡献总结如下：

•

项目负责人：浅井明

•

项目构思：Aisa Akari、Yih Wen-tau、Koh Pang Wei、Hajishirzi Hannaneh

•

OpenScholar 开发项目：浅井明、石伟佳、邵瑞林、何杰

•

OpenScholar 公开演示开发：Amanpreet Singh、Joseph Chee Cheng、Akari Asai、Rulin Shao、Doug Downey、Matt Latzke

•

peS2o 构建方法：Luca Soldaini、Kyle Lo

•

数据存储库（peS2o 索引）构建：邵瑞林、何杰、浅井明

•

关于纸质许可的法律讨论：Kyle Lo、Luca Soldaini、Doug Downey、Pang Wei Koh、Amanpreet Singh、Akari Asai

•

OpenScholar -LM 训练：浅井明、石伟佳

•

OpenScholar -检索器训练与评估：Asai Akari、He Jacqueline、Shao Rulin

•

ScholarQABench 设计与构思：Akari Asai、Pang Wei Koh、David Wadden、Doug Downey、Kyle Lo、Weijia Shi、Amanpreet Singh、Sergey Feldman、Dan Weld

•

ScholarQABench 集合（单篇论文任务）：浅井明

•

ScholarQABench评估流程设计与开发：浅井明

•

ScholarQA -CS 数据集收集与评估：Doug Downey、Amanpreet Singh、Sergey Feldman、Dan Weld、Mike D’arcy

•

ScholarQA -多数据集版本：浅井明、田敏阳、邵润林、何杰琳、施伟佳、季攀、刘胜岩、童浩、吴博浩、熊燕宇

•

ScholarQA -神经与生物领域合集：道格·道尼

•

结果与代码库：Asai Akari、Jacqueline He、Shao Rulin、Shi Weijia、Amanpreet Singh

•

人类评估设计：浅井明、潘伟科、格雷厄姆·诺伊比格

•

人类评估界面开发与监督研究：浅井明、田民阳

•

文稿撰写：Akari Asai、Jacqueline He、Doug Downey、Amanpreet Singh、Kyle Lo、Pang Wei Koh

•

OpenScholar 公开演示测试：所有人

•

文稿编辑：所有人

•

建议：Pang Wei Koh、Hannaneh Hajishirzi、Doug Downey、Wen-tau Yih、Graham Neubig、Dan Weld、Luke Zettlemoyer

### 致谢

我们感谢那些专业标注人员在整理高质量数据方面提供的帮助，也感谢 Ai2 Annotation 团队的 Jenna Sparks在管理与监督数据收集过程方面所做出的贡献。我们感谢 Yizhong Wang在开发人类评估界面方面的协助；Hamish Ivison提供了我们在 OpenScholar 8B 训练中使用的 Tulu v3 指令调整数据的早期版本；Seungone Kim在 Prometheus 评估工作上的帮助。我们感谢 Jena Hwang对评估数据局限性进行分析的工作。对于公共演示方面的协助，我们感谢 Chloe Anastasiades、Crystal Nam、Sophie Lebrecht、Taira Anderson和Will Smith。
我们感谢方远徐、Eunsol Choi、Aran Komatsuzaki、Sean Welleck、项跃、陈彤、Vijay Viswanathan、Shannon Shen以及H2lab和Neulab学生团队的成员们就该项目进行的富有成效的讨论，以及对我们人类评估实验的反馈。PWK由新加坡国家研究基金会和新加坡数字发展与信息部国家人工智能小组在AI访问教授计划下支持（授予编号AIVP-2024-001）。这项工作部分由AA在UW-Meta AI导师计划中完成。

## 参考文献

Agarwal et al. (2024) Shubham Agarwal, Issam H Laradji, Laurent Charlin, and Christopher Pal. Litllm: A toolkit for scientific literature review. arXiv preprint arXiv:2402.01788 , 2024. URL https://arxiv.org/abs/2402.01788 .

AI4Science & Quantum (2023) Microsoft Research AI4Science and Microsoft Azure Quantum. The impact of large language models on scientific discovery: a preliminary study using gpt-4. arXiv preprint arXiv:2311.07361 , 2023. URL https://arxiv.org/abs/2311.07361 .

Asai & Choi (2021) Akari Asai and Eunsol Choi. Challenges in information-seeking QA: Unanswerable questions and paragraph retrieval. In ACL , 2021. URL https://aclanthology.org/2021.acl-long.118 .

Asai et al. (2023) Akari Asai, Timo Schick, Patrick Lewis, Xilun Chen, Gautier Izacard, Sebastian Riedel, Hannaneh Hajishirzi, and Wen-tau Yih. Task-aware retrieval with instructions. In Findings of the Association for Computational Linguistics , 2023. URL https://aclanthology.org/2023.findings-acl.225 .

Asai et al. (2024) Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, and Hannaneh Hajishirzi. Self-RAG: Learning to retrieve, generate, and critique through self-reflection. In ICLR , 2024. URL https://openreview.net/forum?id=hSyW5go0v8 .

Azerbayev et al. (2024) Zhangir Azerbayev, Hailey Schoelkopf, Keiran Paster, Marco Dos Santos, Stephen Marcus McAleer, Albert Q. Jiang, Jia Deng, Stella Biderman, and Sean Welleck. Llemma: An open language model for mathematics. In ICLR , 2024. URL https://openreview.net/forum?id=4WnqRR915j .

Baek et al. (2024) Jinheon Baek, Sujay Kumar Jauhar, Silviu Cucerzan, and Sung Ju Hwang. Researchagent: Iterative research idea generation over scientific literature with large language models. arXiv preprint arXiv:2404.07738 , 2024. URL https://arxiv.org/abs/2404.07738 .

Brodnik et al. (2023) Neal R. Brodnik, Samuel Carton, Caelin Muir, Satanu Ghosh, Doug Downey, McLean P. Echlin, Tresa M. Pollock, and Samantha Daly. Perspective: Large Language Models in Applied Mechanics. Journal of Applied Mechanics , 2023. URL https://doi.org/10.1115/1.4062773 .

Chi et al. (2024) Chenglei Chi, Qiaozi Cheng, Zheng Wen, Rongzhe Lin, Chunyang Wen, Zhaowei Wang, Cuiling Gao, Jian Zhang, Xu Jiang, Jian Yin, et al. Uni-SMART: Universal science multimodal analysis and research transformer. arXiv preprint arXiv:2403.10301 , 2024. URL https://arxiv.org/abs/2403.10301 .

Choi et al. (2018) Eunsol Choi, He He, Mohit Iyyer, Mark Yatskar, Wen-tau Yih, Yejin Choi, Percy Liang, and Luke Zettlemoyer. QuAC: Question answering in context. In EMNLP , Brussels, Belgium, 2018. Association for Computational Linguistics. URL https://aclanthology.org/D18-1241 .

Dasigi et al. (2021) Pradeep Dasigi, Kyle Lo, Iz Beltagy, Arman Cohan, Noah A. Smith, and Matt Gardner. A dataset of information-seeking questions and answers anchored in research papers. In NAACL , 2021. URL https://aclanthology.org/2021.naacl-main.365 .

Dubey et al. (2024) Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Amy Yang, Angela Fan, et al. The llama 3 herd of models. arXiv preprint arXiv:2407.21783 , 2024. URL https://arxiv.org/abs/2407.21783 .

Dubois et al. (2024) Yann Dubois, Balázs Galambosi, Percy Liang, and Tatsunori B Hashimoto. Length-controlled alpacaeval: A simple way to debias automatic evaluators. In COLM , 2024. URL https://openreview.net/forum?id=CybBmzWBX0 .

Fang et al. (2024) Ziheng Fang, Guangxu Wang, Jinsung Xu, Yifeng Cai, Jingya Wang, Qicheng Qiu, Ruixuan Zhang, Xiaofeng Chen, Jinna Wang, Jiayi Dong, et al. Biomedgpt: A unified and generalist biomedical generative pre-trained transformer for vision, language, and knowledge reasoning tasks. arXiv preprint arXiv:2403.18421 , 2024. URL https://arxiv.org/abs/2305.17100 .

Feng et al. (2023) Qiang Feng, Yuxi Li, Jintao Zou, Zhiwei Li, Zhiqiang Ding, Chao Zhang, Qinyan Zhang, Xueqi Hu, Weihao Peng, Xiangyu Meng, et al. K2: A foundation language model for geoscience knowledge understanding and generation. arXiv preprint arXiv:2306.05064 , 2023.

Gao et al. (2023) Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. Enabling large language models to generate text with citations. arXiv preprint arXiv:2305.14627 , 2023. URL https://arxiv.org/abs/2305.14627 .

Gu et al. (2024) Xiaodan Gu, Zhen Wang, Zhengliang Shi, Hongyan Li, Xiaoye Chen, and Dehong Cheng. Me-llama: Foundation model for medical language understanding and generation. arXiv preprint arXiv:2402.12749 , 2024. URL https://arxiv.org/abs/2402.12749 .

Guu et al. (2020) Kelvin Guu, Kenton Lee, Zora Tung, Panupong Pasupat, and Mingwei Chang. Retrieval augmented language model pre-training. In International Conference on Machine Learning , 2020. URL https://dl.acm.org/doi/pdf/10.5555/3524938.3525306 .

Huang et al. (2023) Qian Huang, Jian Vora, Percy Liang, and Jure Leskovec. Mlagentbench: Evaluating language agents on machine learning experimentation. In International Conference on Machine Learning , 2023. URL https://api.semanticscholar.org/CorpusID:263671541 .

Ivison et al. (2023) Hamish Ivison, Yizhong Wang, Valentina Pyatkin, Nathan Lambert, Matthew Peters, Pradeep Dasigi, Joel Jang, David Wadden, Noah A Smith, Iz Beltagy, et al. Camels in a changing climate: Enhancing lm adaptation with tulu 2. arXiv preprint arXiv:2311.10702 , 2023. URL https://arxiv.org/abs/2311.10702 .

Izacard et al. (2022) Gautier Izacard, Mathilde Caron, Lucas Hosseini, Sebastian Riedel, Piotr Bojanowski, Armand Joulin, and Edouard Grave. Unsupervised dense information retrieval with contrastive learning. TMLR , 2022. URL https://openreview.net/forum?id=jKN1pXi7b0 .

Jiang et al. (2023) Zhengbao Jiang, Frank F Xu, Luyu Gao, Zhiqing Sun, Qian Liu, Jane Dwivedi-Yu, Yiming Yang, Jamie Callan, and Graham Neubig. Active retrieval augmented generation. In ACL , 2023. URL https://aclanthology.org/2023.emnlp-main.495/ .

Jin et al. (2019) Qiao Jin, Bhuwan Dhingra, Zhengping Liu, William Cohen, and Xinghua Lu. PubMedQA: A dataset for biomedical research question answering. In EMNLP-IJCNLP , 2019. URL https://aclanthology.org/D19-1259 .

Karpukhin et al. (2020) Vladimir Karpukhin, Barlas Oğuz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, and Wen-tau Yih. Dense passage retrieval for open-domain question answering. In EMNLP , 2020. URL https://aclanthology.org/2020.emnlp-main.550/ .

Kasai et al. (2023) Jungo Kasai, Keisuke Sakaguchi, Yoichi Takahashi, Ronan Le Bras, Akari Asai, Xinyan Yu, Dragomir Radev, Noah A Smith, Yejin Choi, and Kentaro Inui. RealTime QA: What’s the answer right now? In NeurIPS (Datasets and Benchmarks) , 2023. URL https://openreview.net/forum?id=HfKOIPCvsv&noteId=YNFU7iQmxA .

Kim et al. (2024a) Seungone Kim, Jamin Shin, Yejin Cho, Joel Jang, Shayne Longpre, Hwaran Lee, Sangdoo Yun, Seongjin Shin, Sungdong Kim, James Thorne, and Minjoon Seo. Prometheus: Inducing fine-grained evaluation capability in language models. In ICLR , 2024a. URL https://openreview.net/forum?id=8euJaTveKw .

Kim et al. (2024b) Seungone Kim, Juyoung Suk, Ji Yong Cho, Shayne Longpre, Chaeeun Kim, Dongkeun Yoon, Guijin Son, Yejin Cho, Sheikh Shafayat, Jinheon Baek, et al. The biggen bench: A principled benchmark for fine-grained evaluation of language models with language models. arXiv preprint arXiv:2406.05761 , 2024b. URL https://arxiv.org/abs/2406.05761 .

Kinney et al. (2023) Rodney Michael Kinney, Chloe Anastasiades, Russell Authur, Iz Beltagy, Jonathan Bragg, Alexandra Buraczynski, Isabel Cachola, Stefan Candra, Yoganand Chandrasekhar, Arman Cohan, Miles Crawford, Doug Downey, Jason Dunkelberger, Oren Etzioni, Rob Evans, Sergey Feldman, Joseph Gorney, David W. Graham, F.Q. Hu, Regan Huff, Daniel King, Sebastian Kohlmeier, Bailey Kuehl, Michael Langan, Daniel Lin, Haokun Liu, Kyle Lo, Jaron Lochner, Kelsey MacMillan, Tyler Murray, Christopher Newell, Smita Rao, Shaurya Rohatgi, Paul L Sayre, Zejiang Shen, Amanpreet Singh, Luca Soldaini, Shivashankar Subramanian, A. Tanaka, Alex D Wade, Linda M. Wagner, Lucy Lu Wang, Christopher Wilhelm, Caroline Wu, Jiangjiang Yang, Angele Zamarron, Madeleine van Zuylen, and Daniel S. Weld. The semantic scholar open data platform. ArXiv , abs/2301.10140, 2023. URL https://arxiv.org/abs/2301.10140 .

Lee et al. (2023) Yoonjoo Lee, Kyungjae Lee, Sunghyun Park, Dasol Hwang, Jaehyeon Kim, Hong-in Lee, and Moontae Lee. QASA: advanced question answering on scientific articles. In ICML , 2023. URL https://proceedings.mlr.press/v202/lee23n.html .

Lewis et al. (2020) Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, and Douwe Kiela. Retrieval-augmented generation for knowledge-intensive nlp tasks. In NeurIPS , 2020. URL https://proceedings.neurips.cc/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf .

Li et al. (2024a) Junfeng Li, Junjie Gao, Siru Zhang, Yiwen Wang, Xinhang Yan, Hongyan Liu, Shiping Yang, Jie Qiao, and Qian Zhan. BioMistral: A collection of open-source pretrained large language models for biomedicine. In Findings of ACL , 2024a. URL https://aclanthology.org/2024.findings-acl.348/ .

Li et al. (2024b) Junyi Li, Jie Chen, Ruiyang Ren, Xiaoxue Cheng, Xin Zhao, Jian-Yun Nie, and Ji-Rong Wen. The dawn after the dark: An empirical study on factuality hallucination in large language models. In Lun-Wei Ku, Andre Martins, and Vivek Srikumar (eds.), Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) , pp. 10879–10899, Bangkok, Thailand, August 2024b. Association for Computational Linguistics. URL https://aclanthology.org/2024.acl-long.586 .

Li et al. (2024c) Ming Li, Yong Zhang, Shwai He, Zhitao Li, Hongyu Zhao, Jianzong Wang, Ning Cheng, and Tianyi Zhou. Superfiltering: Weak-to-strong data filtering for fast instruction-tuning. In ACL , 2024c. URL https://aclanthology.org/2024.acl-long.769 .

Liu et al. (2023) Nelson F Liu, Tianyi Zhang, and Percy Liang. Evaluating verifiability in generative search engines. In Findings of EMNLP , 2023. URL https://aclanthology.org/2023.findings-emnlp.467/ .

Liu et al. (2024) Nelson F Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. Lost in the middle: How language models use long contexts. TACL , 2024. URL https://aclanthology.org/2024.tacl-1.9/ .

Lo et al. (2020) Kyle Lo, Lucy Lu Wang, Mark Neumann, Rodney Kinney, and Daniel Weld. S2ORC: The semantic scholar open research corpus. In ACL , 2020. URL https://aclanthology.org/2020.acl-main.447 .

Loshchilov & Hutter (2019) Ilya Loshchilov and Frank Hutter. Decoupled weight decay regularization. In ICLR , 2019. URL https://openreview.net/forum?id=Bkg6RiCqY7 .

Lu et al. (2020) Yao Lu, Yue Dong, and Laurent Charlin. Multi-xscience: A large-scale dataset for extreme multi-document summarization of scientific articles. In EMNLP , 2020. URL https://aclanthology.org/2020.emnlp-main.648/ .

Luo et al. (2022) Renqian Luo, Liai Sun, Yingce Xie, Zhiting Jiang, Yangbin Gu, Kun Shi, Dejia Xiong, Sheng He, Zhen Xu, and Tao Qin. Biogpt: Generative pre-trained transformer for biomedical text generation and mining. Briefings in Bioinformatics , 2022. URL https://academic.oup.com/bib/article/23/6/bbac409/6713511 .

Madaan et al. (2023) Aman Madaan, Niket Tandon, Prakhar Gupta, Skyler Hallinan, Luyu Gao, Sarah Wiegreffe, Uri Alon, Nouha Dziri, Shrimai Prabhumoye, Yiming Yang, et al. Self-refine: Iterative refinement with self. Feedback , 2023. URL https://arxiv.org/abs/2303.17651 .

Malaviya et al. (2023) Chaitanya Malaviya, Subin Lee, Sihao Chen, Elizabeth Sieber, Mark Yatskar, and Dan Roth. Expertqa: Expert-curated questions and attributed answers. arXiv preprint arXiv:2309.07852 , 2023. URL https://arxiv.org/abs/2309.07852 .

Mallen et al. (2023) Alex Mallen, Akari Asai, Victor Zhong, Rajarshi Das, Daniel Khashabi, and Hannaneh Hajishirzi. When not to trust language models: Investigating effectiveness of parametric and non-parametric memories. In ACL , 2023. URL https://aclanthology.org/2023.acl-long.546 .

Mishra et al. (2024) Abhika Mishra, Akari Asai, Vidhisha Balachandran, Yizhong Wang, Graham Neubig, Yulia Tsvetkov, and Hannaneh Hajishirzi. Fine-grained hallucination detection and editing for language models. In COLM , 2024. URL https://openreview.net/forum?id=dJMTn3QOWO .

Nguyen et al. (2023) Tuan Dung Nguyen, Yuan-Sen Ting, Ioana Ciuca, Charles O’Neill, Ze-Chang Sun, Maja Jabłońska, Sandor Kruk, Ernest Perkowski, Jack Miller, Jason Jason Jingsh Li, Josh Peek, Kartheik Iyer, Tomasz Rozanski, Pranav Khetarpal, Sharaf Zaman, David Brodrick, Sergio J. Rodriguez Mendez, Thang Bui, Alyssa Goodman, Alberto Accomazzi, Jill Naiman, Jesse Cranney, Kevin Schawinski, and Roberta Raileanu. AstroLLaMA: Towards specialized foundation models in astronomy. In Proceedings of the Second Workshop on Information Extraction from Scientific Publications , 2023. URL https://aclanthology.org/2023.wiesp-1.7 .

Nogueira & Cho (2019) Rodrigo Nogueira and Kyunghyun Cho. Passage re-ranking with bert. arXiv preprint arXiv:1901.04085 , 2019. URL https://arxiv.org/abs/1901.04085 .

Panickssery et al. (2024) Arjun Panickssery, Samuel R. Bowman, and Shi Feng. LLM evaluators recognize and favor their own generations. In NeurIPS , 2024. URL https://openreview.net/forum?id=4NJBV6Wp0h .

Phan et al. (2021) Long N Phan, James T Anibal, Hieu Tran, Shaurya Chanana, Erol Bahadroglu, Alec Peltekian, and Grégoire Altan-Bonnet. Scifive: a text-to-text model for biomedical literature. arXiv preprint arXiv:2106.03598 , 2021. URL https://arxiv.org/abs/2106.03598 .

Ram et al. (2023) Ori Ram, Yoav Levine, Itay Dalmedigos, Dor Muhlgay, Amnon Shashua, Kevin Leyton-Brown, and Yoav Shoham. In-context retrieval-augmented language models. TACL , 2023. URL https://aclanthology.org/2023.tacl-1.75/ .

Shaikh et al. (2023) Shishir G Shaikh, Jaideep Ramachandran, Varnith Nanda, Benjamin Lunt, Miltiadis Allamanis, Daman Sharma, Sebastien Bubeck, and Prateek Jain. Darwin: Data analytics and reasoning with large language models for science. arXiv preprint arXiv:2308.13565 , 2023. URL https://arxiv.org/abs/2308.13565 .

Shao et al. (2024) Rulin Shao, Jacqueline He, Akari Asai, Weijia Shi, Tim Dettmers, Sewon Min, Luke Zettlemoyer, and Pang Wei Koh. Scaling retrieval-based language models with a trillion-token datastore. In The Thirty-eighth Annual Conference on Neural Information Processing Systems , 2024. URL https://openreview.net/forum?id=iAkhPz7Qt3 .

Si et al. (2024) Chenglei Si, Diyi Yang, and Tatsunori Hashimoto. Can llms generate novel research ideas? a large-scale human study with 100+ nlp researchers. arXiv preprint arXiv:2409.04109 , 2024. URL https://arxiv.org/abs/2409.04109 .

Singhal et al. (2023a) Karan Singhal, Shekoofeh Azizi, Tao Tu, S Sara Mahdavi, Jason Wei, Hyung Won Chung, Nathan Scales, Ajay Tanwani, Heather Cole-Lewis, Stephen Pfohl, et al. Large language models encode clinical knowledge. Nature , 2023a. URL https://www.nature.com/articles/s41586-023-06291-2 .

Singhal et al. (2023b) Zeming Singhal, Charles Sutton, Adam Mottram, Owain Lavelle, Iz Beltagy, Leonardo Neves, Kyle Lo, Stephanie Hyland, Michael Wainwright, Alexander Wettig, et al. MEDITRON-70B: Scaling medical pretraining for large language models. arXiv preprint arXiv:2311.16079 , 2023b. URL https://arxiv.org/abs/2311.16079 .

Skarlinski et al. (2024) Michael D. Skarlinski, Sam Cox, Jon M. Laurent, James D. Braza, Michaela Hinks, Michael J. Hammerling, Manvitha Ponnapati, Samuel G. Rodriques, and Andrew D. White. Language agents achieve superhuman synthesis of scientific knowledge. preprint , 2024. URL https://paper.wikicrow.ai .

Soldaini et al. (2024) Luca Soldaini, Rodney Kinney, Akshita Bhagia, Dustin Schwenk, David Atkinson, Russell Authur, Ben Bogin, Khyathi Chandu, Jennifer Dumas, Yanai Elazar, et al. Dolma: An open corpus of three trillion tokens for language model pretraining research. In ACL , 2024. URL https://aclanthology.org/2024.acl-long.840/ .

Tan et al. (2023) Cheng Tan, Miao Huang, Xianxin Huang, Qian Fu, and Bo Wu. PMC-LLaMA: Further finetuning llama on medical papers. arXiv preprint arXiv:2304.14454 , 2023. URL https://arxiv.org/abs/2304.14454 .

Thakur et al. (2021) Nandan Thakur, Nils Reimers, Andreas Rücklé, Abhishek Srivastava, and Iryna Gurevych. BEIR: A heterogeneous benchmark for zero-shot evaluation of information retrieval models. In NeurIPS (Datasets and Benchmarks) , 2021. URL https://openreview.net/forum?id=wCu6T5xFjeJ .

Tian et al. (2024) Minyang Tian, Luyu Gao, Shizhuo Dylan Zhang, Xinan Chen, Cunwei Fan, Xuefei Guo, Roland Haas, Pan Ji, Kittithat Krongchon, Yao Li, et al. Scicode: A research coding benchmark curated by scientists. arXiv preprint arXiv:2407.13168 , 2024. URL https://arxiv.org/abs/2407.13168 .

Wadden et al. (2020) David Wadden, Shanchuan Lin, Kyle Lo, Lucy Lu Wang, Madeleine van Zuylen, Arman Cohan, and Hannaneh Hajishirzi. Fact or fiction: Verifying scientific claims. In EMNLP , 2020. URL https://aclanthology.org/2020.emnlp-main.609 .

Wadden et al. (2024) David Wadden, Kejian Shi, Jacob Morrison, Aakanksha Naik, Shruti Singh, Nitzan Barzilay, Kyle Lo, Tom Hope, Luca Soldaini, Shannon Zejiang Shen, et al. Sciriff: A resource to enhance language model instruction-following over scientific literature. arXiv preprint arXiv:2406.07835 , 2024. URL https://arxiv.org/abs/2406.07835 .

Wang et al. (2024) Yidong Wang, Qi Guo, Wenjin Yao, Hongbo Zhang, Xin Zhang, Zhen Wu, Meishan Zhang, Xinyu Dai, Min zhang, Qingsong Wen, Wei Ye, Shikun Zhang, and Yue Zhang. AutoSurvey: Large language models can automatically write surveys. In NeurIPS , 2024. URL https://openreview.net/forum?id=FExX8pMrdT .

Xiao et al. (2023) Shitao Xiao, Zheng Liu, Peitian Zhang, Niklas Muennighoff, Defu Lian, and Jian-Yun Nie. C-pack: Packaged resources to advance general chinese embedding, 2023. URL https://arxiv.org/abs/2309.07597 .

Xu et al. (2023a) Fangyuan Xu, Weijia Shi, and Eunsol Choi. RECOMP: Improving retrieval-augmented lms with compression and selective augmentation, 2023a. URL https://arxiv.org/abs/2310.04408 .

Xu et al. (2023b) Fangyuan Xu, Yixiao Song, Mohit Iyyer, and Eunsol Choi. A critical evaluation of evaluations for long-form question answering. In ACL , 2023b. URL https://aclanthology.org/2023.acl-long.181 .

Xu et al. (2024) Fangyuan Xu, Kyle Lo, Luca Soldaini, Bailey Kuehl, Eunsol Choi, and David Wadden. KIWI: A dataset of knowledge-intensive writing instructions for answering research questions. In Findings of ACL , 2024. URL https://aclanthology.org/2024.findings-acl.770 .

Yang et al. (2023) Zonglin Yang, Xinya Du, Junxian Li, Jie Zheng, Soujanya Poria, and E. Cambria. Large language models for automated open-domain scientific hypotheses discovery. In ACL , 2023. URL https://api.semanticscholar.org/CorpusID:261557055 .

Yuan et al. (2022) Hongyi Yuan, Zheng Yuan, Ruyi Gan, Jiaxing Zhang, Yutao Xie, and Sheng Yu. BioBART: Pretraining and evaluation of a biomedical generative language model. In The 21st Workshop on Biomedical Language Processing (BioNLP) , May 2022. URL https://aclanthology.org/2022.bionlp-1.9 .

Yue et al. (2023) Xiang Yue, Boshi Wang, Ziru Chen, Kai Zhang, Yu Su, and Huan Sun. Automatic evaluation of attribution by large language models. In Findings of EMNLP , 2023. URL https://aclanthology.org/2023.findings-emnlp.307 .

Zhang et al. (2024a) Dan Zhang, Ziniu Hu, Sining Zhoubian, Zhengxiao Du, Kaiyu Yang, Zihan Wang, Yisong Yue, Yuxiao Dong, and Jie Tang. Sciinstruct: a self-reflective instruction annotated dataset for training scientific language models. In NeurIPS (Datasets and Benchmarks Track) , 2024a. URL https://openreview.net/forum?id=LC1QAqhePv .

Zhang et al. (2024b) Yuqi Zhang, Zihao Zhao, Lanqing Hu, Shuai Wang, Penghui Jiao, Min Leng, Yuzhi Liu, Guotong Li, Chengming Xu, Chenhui Lin, et al. BioMedGPT: Open multimodal generative pre-trained transformer for biomedicine. Nature Medicine , 2024b. URL https://www.nature.com/articles/s41591-024-03185-2 .

Zheng et al. (2023a) Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric Xing, Hao Zhang, Joseph E. Gonzalez, and Ion Stoica. Judging LLM-as-a-judge with MT-bench and chatbot arena. In NeurIPS (Datasets and Benchmarks Track) , 2023a. URL https://openreview.net/forum?id=uccHPGDlao .

Zheng et al. (2024) Yuxiang Zheng, Shichao Sun, Lin Qiu, Dongyu Ru, Cheng Jiayang, Xuefeng Li, Jifan Lin, Binjie Wang, Yun Luo, Renjie Pan, et al. Openresearcher: Unleashing ai for accelerated scientific research. arXiv preprint arXiv:2408.06941 , 2024. URL https://arxiv.org/abs/2408.06941 .

Zheng et al. (2023b) Zhiling Zheng, Zichao Rong, Nakul Rampal, Christian Borgs, Jennifer T Chayes, and Omar M Yaghi. A gpt-4 reticular chemist for guiding mof discovery. Angewandte Chemie International Edition , 2023b. URL https://arxiv.org/abs/2306.14915 .

## 附录

## 附录 A 已发布的成果

我们发布了一组成果以推动后续研究：

**表格与文字对照**

```text
Demo | | openscholar.allen.ai/
OpenScholar | | github.com/AkariAsai/OpenScholar
ScholarBenchQA | | github.com/AkariAsai/ScholarBench
OpenScholar-8B LM | | OpenScholar/OpenScholar_Llama-3.1-8B
OpenScholar-Retriever | | OpenScholar/OpenScholar_Retriever
OpenScholar-Reranker | | OpenScholar/OpenScholar_Reranker
OpenScholar-DataStore-V2 | | OpenScholar/OpenScholar-DataStore-V2
OpenScholar-DataStore-V3 | | OpenScholar/OpenScholar-DataStore-V3
ScholarBench (Data) | | OpenScholar/ScholarBench
OpenScholar (Training Data) | | OpenScholar/OS_Train_Data
Expert Evaluation | | AkariAsai/OpenScholar_ExpertEval

表内文字对照（数值与原始行列保持不变）：
Demo → 演示
openscholar → 开放学者
allen → 艾伦
ai/ → 人工智能/
OpenScholar → OpenScholar
github → github
com/AkariAsai/OpenScholar → com/AkariAsai/OpenScholar
ScholarBenchQA → ScholarBenchQA
com/AkariAsai/ScholarBench → com/AkariAsai/ScholarBench
OpenScholar- → OpenScholar-
B LM → 大语言模型
OpenScholar/OpenScholar_Llama- → OpenScholar/OpenScholar_Llama-
OpenScholar-Retriever → OpenScholar-检索器
OpenScholar/OpenScholar_Retriever → OpenScholar/OpenScholar_Retriever
OpenScholar-Reranker → OpenScholar-Reranker
OpenScholar/OpenScholar_Reranker → OpenScholar/OpenScholar_Reranker
OpenScholar-DataStore-V → OpenScholar-数据存储-系统
OpenScholar/OpenScholar-DataStore-V → OpenScholar/OpenScholar-DataStore-V
ScholarBench (Data) → ScholarBench（数据）
OpenScholar/ScholarBench → OpenScholar/ScholarBench
OpenScholar (Training Data) → OpenScholar（训练数据）
OpenScholar/OS_Train_Data → OpenScholar/OS训练数据
Expert Evaluation → 专家评估
AkariAsai/OpenScholar_ExpertEval → AkariAsai/OpenScholar_ExpertEval
```

## 附录 B：关于 ScholarQABench的更多细节

### B.1 ScholarQABench的目标

ScholarQABench 有两个关键原则：它应作为文献综述的现实性基准，同时也是一个可复现且多维度的评估流程。

### 大语言模型文献综述的现实性基准（第3.1节）。

ScholarQABench整合了来自两个关键来源的任务：(i) 经过筛选和改编的现有数据集，这些数据集与文献综合任务相关且由科学家标注；以及 (ii) 四个新的数据集，这些数据集由四个科学领域的博士专家标注，反映了真实的文献综述场景，例如来自多篇论文的信息整合。ScholarQABench中的任务需要不同的输出格式和学科领域。

对于多篇论文任务，我们要求专家注释者提出信息寻求问题——即那些他们真正希望得到解答的问题，而非已经知道答案或可以通过单篇论文中的小文本片段得到解答的问题（Asai & Choi, 2021；Choi et al., 2018）。我们发现这种方法对于筛选出现实科学家可能提出的真实问题至关重要。
这些问题通常更为详细且具有情境性（例如：“我计划使用 GPT4o 生成合成训练数据，并使用 GPT4o 过滤噪声数据，但我担心在这种情况下 GPT4o 不会过滤模型，因为它可能会倾向于自身生成的内容”），需要细致、长篇的回答，而非简单的是/否或选择题形式的回应。我们收集了人类撰写的答案或评分标准，以确保评估的可靠性，而不是像 Xu et al. (2024) 和 Malaviya et al. (2023) 那样依赖最先进的专有 LLM 生成的答案。
虽然这些专有模型功能强大，但仍然存在一些局限性，例如缺乏领域知识导致的幻觉、偏见以及信息快速变化等问题，因此无法与新型模型进行一致的评估。此外，以模型生成的答案作为参考可能会不公平地偏向同一系列的模型，从而引入潜在的评估偏差（Panickssery等，2024）。为避免这些问题，我们为 ScholarQA-CS 和 ScholarQA-Multi 筛选了由专家撰写的答案。

### 可复现的多面评估流程（第3.2节）。

由于 ROUGE 等传统基于相似度的评估指标与人类判断之间的相关性较低（Xu 等，2023b；Malaviya 等，2023），专家领域长文本生成任务的评估通常依赖于小规模至中规模的专家标注数据（Zheng 等，2024；Singhal 等，2023a；Si 等，2024）。尽管专家人工评估具有价值（如第5节所述），但雇佣标注人员需要高昂成本，且难以重复实施。
为了克服这些限制，我们引入了自动化评估流程，从引用准确性或覆盖度等关键方面全面评估长文本生成结果的质量。

### B.2 数据整理细节

### B.2.1 单篇论文任务修改的详细内容

### SciFact。

SciFact（Wadden等，2020）是一个包含1.4K个由专家撰写的生物医学领域科学论断的数据集，这些论断均配有带有标签和解释的基于证据的摘要。原始任务包含三个子任务——段落选择、句子选择和标签预测——这些任务基于5,000篇摘要的集合进行设计。然而，我们将其重新设计为开放检索标签预测任务，模型中仅接收查询信息，必须从4000万条文本中预测出相应的标签。我们排除了被标记为“信息不足”的查询，仅保留被标记为“支持”（正确）或“矛盾”（错误）的实例。

### PubMedQA。

我们利用了 PubMedQA（Jin等人，2019年）数据集，该数据集包含1000条由专家标注的“是/否/可能”类型的PubMed论文摘要问答数据。与SciFact类似，我们保留了带有“是”或“否”标签的实例，并丢弃原始摘要段落，从而将任务设定为一种开放式设置。

### QASA。

QASA（Lee等人，2023年）是一个单一的文献综述QA数据集，包含1,798对新的问题回答对，这些问题需要针对AI和ML领域的科学文章进行推理。我们评估模型能否充分回答关于目标文献的详细问题。虽然该数据集包含三个子任务（答案选择、理性生成和答案组合）以及端到端的全栈QA形式，但我们仍基于全栈QA来评估模型的性能。

### B.2.2 多篇论文任务的数据收集细节

### 招募注释员。

在数据整理方面，我们通过 UpWork 及跨机构渠道招募专业标注员，确保他们符合以下标准：(1) 拥有博士学位或正在攻读相关博士学位；(2) 在该领域拥有超过三年的研究经验；(3) 在目标领域发表过相关论文。总计我们招募了超过 20 名标注员，包括博士生、博士后研究员、教授及研究科学家，涵盖目标领域多个论文类别。

### 注释说明。

[查看原图表（阅读版）](bilingual.html#openscholar-0328)

表5列出了我们用于收集 ScholarQA-CS评分标准的标注说明；表6则展示了针对 ScholarQA-Bio和ScholarQA-Neuro的标注员所需的标注指南。表7则给出了针对 ScholarQA-Multi的标注员指示。

•

•

1.

2.

表5：ScholarQA-CS注释说明：提供给专家注释者的指导方针，用于生成ScholarQA-CS问题的关键要素。

[查看原图表（阅读版）](bilingual.html#openscholar-0358)

表6：ScholarQA-Bio，神经科学注释说明：我们向专家注释者提供的用于撰写生物医学问题的指导方针。本文中的示例问题是在GPT的协助下编写的。

[查看原图表（阅读版）](bilingual.html#openscholar-0380)

表7：ScholarQAMulti注释说明：提供给专家注释者的注释问题和答案的标注指南。

### ScholarQA-Multi 中人工撰写的问答统计情况

[查看原图表（阅读版）](bilingual.html#openscholar-0382)

图6(a)展示了各主题的分布情况，图6(b)则显示了专家在标注不同主题的答案时平均花费的时间（以秒为单位）。平均而言，标注者每标注一个答案至少需要30分钟，而某些主题如物理学的标注者则需要超过1小时（约5,000秒）才能完成一次标注。这表明即使对于领域专家来说，这项任务也极其耗时且具有挑战性。

(a) 专家标注答案的主题分布

(b) 每个受试者的平均实例标注时间（秒）。

图6：人类撰写的答案分析：(a) 展示了各主题下的实例分布，以及(b) 展示了每个主题的每个实例平均标注时间。

### B.3 评估指标详情

### B.3.1 ScholarQA-CS 校正评估

对于 ScholarQA-CS 项目，我们采用专家标注的评分标准来评估生成的答案。每个评分标准包含两个维度——通用指标（占得分的 40%）和标注驱动指标（占 60%）。通用指标涵盖长度、专业水平、引用次数及摘录内容方面的评估，而标注驱动指标则通过 0 到 1 的评分体系，衡量标注者所识别的每个具体关键要素及其相关引文在答案中的出现程度。每个必须包含的要素被认为比可选要素重要两倍，但同一类型的不同要素之间则没有区分。
采用大语言模型作为评判者（Zheng等，2023a），针对每个标准进行评分，然后按权重计算各标准的总和以得出最终得分。该评分机制强调引文和摘录的完整性，因此，如我们的实验所示，缺乏其中任一要素的系统即便在其余标准上得分较高，也往往表现不佳。

[查看原图表（阅读版）](bilingual.html#openscholar-0390)

表8：写作质量评估方案。我们定义了三个由人类专家和大语言模型共同评估的细致维度。除此之外，专家还需判断这些回答是否有用。

### B.3.2 内容质量与结构安排

评估方面的概述见表8。我们采用相关性、覆盖率和组织性这三个指标进行自动评估。我们发现现有的评估智能体大语言模型在评估整体实用性方面存在困难，且往往过于乐观。

### 评估说明与评分标准。

我们在表10、表11、表12和表13中分别展示了标注者的评分标准，这些标准涉及组织性、覆盖范围、相关性以及整体实用性。

### Prometheus 配置。

在评估方面，我们结合了 Prometheus BGB（Kim等人，2024b）（prometheus-eval/prometheus-bgb-8x7b-v2.0）和 Prometheus v2（Kim等人，2024a）（https://huggingface.co/prometheus-eval/prometheus-8x7b-v2.0）。我们发现 Prometheus BGB 通常表现良好，但在 Rel 任务上有时会给出远高于人类评估的得分，尤其是针对 GPT4o。因此，我们将 Prometheus BGB 用于 Org 和 Cov 任务，将 Prometheus v2 用于相关性任务。我们使用人工撰写的答案作为金标准参考，这能提升 Prometheus 与人类评估的关联度。我们将这些模型与 vllm 结合使用。
按照默认设置，我们将新令牌的最大数量设定为 512，top- $p$ 为 0.95，温度设定为 0.01。

### B.3.3 引用准确性

为了评估引用准确性，我们使用了 osunlp/attrscore-flan-t5-xl（Yue等，2023），该模型是在多种归因任务上训练的 FLAN-T5-XL。我们遵循 Gao等（2023）提出的引用精确率和召回率计算方法，并在句子层面计算引用精确率和召回率。我们将字符数少于50的句子排除在外，因为这些句子通常是不需要引用的段落或子标题。我们采用 Yue等（2023）提供的原始引用评估指南，如表9所示。

[查看原图表（阅读版）](bilingual.html#openscholar-0402)

表9：引文评估的评估指令。如果某项主张有提供的参考文献作为支持，我们就会向大语言模型发出引用提示。该指令改编自Yue等人（2023）的研究。

## 附录 C 关于 OpenScholar 的更多细节

### C.1 训练科学型生物编码器 $\theta_{\rm bi}$

对于 $\theta_{\text{bi}}$ ，我们采用 Izacard 等人在 2022 年提出的无监督训练方法，在 peS2o 版本 2、CCNews 和 Proofpile2（Azerbayev 等，2024）数据的混合数据集上，以 4,096 的批量大小和 0.00005 的学习率，对 Contriever 双编码器进行持续预训练，共进行 500k 步。我们从 Contriever 中初始化模型检查点。

### C.2 训练科学交叉编码器 $\theta_{\rm cross}$

得分超过3分的段落被标记为正面，而得分低于3分的段落则被标记为负面。最后，根据这一流程选出前$N$段落，并将这些高分段落$\mathbf{P}$提交给生成器LLM。对于$\theta_{\text{cross}}$部分，我们在新创建的训练数据上使用6e-5的学习率进行5个周期의 BGE-large重排序器微调。

### C.3 生成器训练细节 $\mathcal{G}$

### 训练数据统计信息。

[查看原图表（阅读版）](bilingual.html#openscholar-0410)

图7展示了训练数据分布。“Tulu”表示来自Ivison等人（2023年）的通用领域指令调整数据，而SciRIFF（Wadden等人，2024年）中的数据则代表来自SciRIFF的任务特定数据。对于这两个数据集，我们都确保不包含任何用于评估的数据，即PubMedQA、SciFact和QASA的数据。总计共有130,135个训练样本。

图7：生成器训练数据分布。我们混合了多种不同的训练数据来训练我们的8B大语言模型。

### 训练超参数。

对于 OS-8B 模型，我们以 Llama 3.1 8B Instruct（Dubey 等，2024）的模型检查点作为初始值。我们使用 torchtune 7 7 7 https://github.com/pytorch/torchtune 进行训练。

我们分别使用 5e-6 和 1e-4 的学习率对这两个模型进行两个轮次的训练，最大上下文长度为 10k，批量大小为 1，梯度累积步长为 2，并使用 bf16 算子。我们采用 AdamW（Loshchilov & Hutter, 2019）作为优化器。

[查看原图表（阅读版）](bilingual.html#openscholar-0429)

表10：组织的评估评分标准。评估说明及用于评估组织的五点评分标准。

[查看原图表（阅读版）](bilingual.html#openscholar-0466)

表11：覆盖度评估评分标准。评估说明及用于评估覆盖度的五分制评分标准。

[查看原图表（阅读版）](bilingual.html#openscholar-0479)

表12：相关性评估评分标准。评估说明及用于评估相关性的五分制评分标准。

[查看原图表（阅读版）](bilingual.html#openscholar-0492)

表13：整体有用性的评估评分标准。评估说明及用于衡量整体实用性的五点评分标准。

[查看原图表（阅读版）](bilingual.html#openscholar-0494)

图8：人类评估注释界面。

[查看原图表（阅读版）](bilingual.html#openscholar-0496)

图9：人类评估注释界面。

## 附录 D 更多分析

### D.1 peS2o v2与v3的对比

[查看原图表（阅读版）](bilingual.html#openscholar-0499)

图10：ScholarQA-CS中检索到的前20篇论文的发表年份分布。该图表明，通过将数据存储从peS2o v2更新为更新的peS2o v3（包含截至2024年10月的论文），我们的密集检索模型能够成功检索到更多近期的论文。

在本节中，我们对 OpenScholar 中使用的数据存储进行了简要分析。图 10 展示了针对相同的 ScholarQA-CS 查询，从 peS2o v2 和 v3 两个数据存储中检索到的前 20 篇文献的分布情况。需要注意的是，我们的检索模型是在 peS2o v2 数据上训练的。虽然我们的模型并未直接在新的 v3 数据存储上训练，但我们发现它在测试时能够持续从较新的数据存储中检索到相关文献，因此获得了大量来自 2023 - 2024 年的文献。

### D.2 关于专家评估的进一步分析

### 对人类和模型生成的答案进行自动评估。

[查看原图表（阅读版）](bilingual.html#openscholar-0504)

表14：人类撰写的回答统计。与人类相比，这些模型倾向于生成更长的回复，并引用更多的文献。作为参考，我们在人类评估查询中使用了未进行检索的 GPT4o。

表14提供了人类回答与OpenScholar生成回答的基本统计信息，详细列出了平均长度、引用的论文数量以及各项评估指标的得分。我们观察到，与模型生成的输出相比，人类的回答通常更短，引用的论文也较少。虽然一项相关研究使用大语言模型对人工撰写的回答进行标准化处理以控制混杂因素（Si等，2024），但在我们的人类评估中仍保留了原始的人类回答和模型生成的回答，并进行了深入分析以了解这些差异如何影响人类的偏好。

我们对自动化评估流程进行了测试，该流程包括对人类和模型生成的答案的引用精度、召回率及写作质量进行评估。研究结果表明，OS-8B的引用精度与专家水平相当甚至更高，而OS-GPT4o在引用准确性方面表现稍差。尽管PaperQA2的引用精度高于OS-8B或人类专家，但其答案通常较为简短，引用的论文数量也较少，因此覆盖范围有限。

### 对专家对成对偏好解释的定性分析。

[查看原图表（阅读版）](bilingual.html#openscholar-0508)

表15展示了专家对成对偏好方面的解释。

表15：偏好说明。

(a) GPT4 回答

(b) Llama 3 8B

[查看原图表（阅读版）](bilingual.html#openscholar-0515)

图11：Prometheus与人类在流畅性方面的一致性。

(a) GPT4 回答

(b) Llama 3 8B

[查看原图表（阅读版）](bilingual.html#openscholar-0520)

图 12：Prometheus与人类在相关性方面的一致性。

(a) GPT4 回答

(b) Llama 3 8B

[查看原图表（阅读版）](bilingual.html#openscholar-0525)

图13：Prometheus与人类在覆盖范围上的一致性。

(a) GPT4 回答

(b) Llama 3 8B

[查看原图表（阅读版）](bilingual.html#openscholar-0530)

图14：Prometheus与人类在整体实用性方面的共识程度。

### 人类与作为评判者的大语言模型之间的协议。

[查看原图表（阅读版）](bilingual.html#openscholar-0533)

表16：人类评估与Prometheus评估在“人类”及OpenScholar（GPT4o）回答方面的一致性。我们发现，在采用黄金答案的情况下，Prometheus的评估在某些方面往往与专家评估一致。

我们还研究了人类评估与大语言模型评估之间的匹配程度，以评估回复的细致质量。具体而言，我们以人类注释作为金标准，评估了评估器大语言模型的准确性及平均绝对误差（即 prometheus-eval/prometheus-bgb-8x7b-v2.0）。表16展示了相关结果。

图12、图13和图14展示了人类预测与Prometheus预测之间的混淆矩阵。混淆现象通常发生在相邻类别之间（例如4与5），而评估智能体LLM则很少出现负类别（低于3）与正类别之间的混淆。总体而言，在组织和覆盖度方面，Prometheus的相关性较弱，准确率约为50%，且经常出现相邻类别之间的差异（例如给4分和给5分）。
当我们比较各方面的平均得分差异时，根据人类评估者大语言模型和评估大语言模型的预测，在相关性、覆盖率和整体实用性方面，绝对差异小于 -0.2，各模型的排名也保持不变。

### 模型与专家撰写的答案对比。

表17、表18、表19、表20、表21展示了模型及专家撰写的答案以及由专家评估的得分。

[查看原图表（阅读版）](bilingual.html#openscholar-0539)

表17：人类与模型答案的对比（光子学）。

[查看原图表（阅读版）](bilingual.html#openscholar-0541)

表18：人类与模型答案的对比（生物医学领域）。在原始评估中，我们随机排列了模型顺序，并对回答进行了匿名处理以排除任何偏见。在本分析中，我们将匿名化的模型编号替换为其对应的实际名称。

[查看原图表（阅读版）](bilingual.html#openscholar-0543)

表19：人类与模型答案的对比（计算机科学）。在原始评估中，我们随机化了模型的排序，并对回答进行了匿名处理以排除任何偏见。对于本次分析，我们将匿名处理的模型编号替换为其实际名称。

[查看原图表（阅读版）](bilingual.html#openscholar-0545)

表20：人类与模型答案的对比（计算机科学）。在原始评估中，我们随机化了模型的排序，并对回复进行了匿名处理以排除任何偏见。对于本次分析，我们将匿名化的模型ID替换为其对应的实际名称。

[查看原图表（阅读版）](bilingual.html#openscholar-0547)

表21：人类与模型答案的对比（光子学领域）。在原始评估中，我们随机化了模型的排序，并对回答进行了匿名处理以排除任何偏见。对于本次分析，我们将匿名化的模型编号替换为其实际名称。

## 附录 E scholarQABench 示例

在本节中，我们将展示包含在 ScholarQABench 中的示例实例。

### E.1 单篇论文任务

[查看原图表（阅读版）](bilingual.html#openscholar-0551)

图15展示了单篇论文任务中的示例。

图15：ScholarQABench中的单任务示例。

### E.2 ScholarQA -CS

[查看原图表（阅读版）](bilingual.html#openscholar-0554)

表22展示了来自ScholarQA-CS的一个示例。

(a) 来自 ScholarQA-CS 的示例问题及对应的关键要素注释。

(b) 针对“最重要的”关键要素之一所引用的支持性引文，这些引文来自学术文献综述与提供给注释者的原始文件的组合。

表22：来自 ScholarQA-CS的标注示例，以及相关的关键要素和支持性引文。我们将这些要素和引文作为评估学术问答系统的评分标准。

### E.3 ScholarQA-Bio

[查看原图表（阅读版）](bilingual.html#openscholar-0561)

表23展示了几条由专家标注的生物医学查询，以及提供给标注人的相关文献以供参考。

表23：学者简介查询示例。“启发式文献”指用于帮助专家注释者提出问题的文献。

### E.4 ScholarQA-Multi

图16、图17、图18、图19和图20展示了来自不同领域的专家注释示例。

[查看原图表（阅读版）](bilingual.html#openscholar-0566)

图 16：ScholarBench 示例（生物领域）。

[查看原图表（阅读版）](bilingual.html#openscholar-0567)

图17：ScholarQA-Multi的一个示例。

[查看原图表（阅读版）](bilingual.html#openscholar-0568)

图 18：ScholarQA-Multi 的一个示例。

[查看原图表（阅读版）](bilingual.html#openscholar-0569)

图19：ScholarQA-Multi的一个示例。

[查看原图表（阅读版）](bilingual.html#openscholar-0570)

图 20：ScholarQA-Multi 的一个示例。

