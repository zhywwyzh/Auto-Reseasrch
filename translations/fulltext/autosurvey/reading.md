# AutoSurvey：大语言模型能够自动撰写综述

AutoSurvey: Large Language Models Can Automatically Write Surveys

Wang, Yidong; Guo, Qi; Yao, Wenjin; Zhang, Hongbo; Zhang, Xin; Wu, Zhen; Zhang, Meishan; Dai, Xinyu; Zhang, Min; Wen, Qingsong; Ye, Wei; Zhang, Shikun; Zhang, Yue

> 非官方机器初译，正文尚未逐段精校。图表保留原文内容，图内英文未另行翻译；有 HTML 原文的公式按原式排版。PDF 提取版保留对应原页，点击缩略图放大核对图表与公式。

原文版本：2406.10252v2 · [原始来源](https://arxiv.org/abs/2406.10252v2) · [中文 PDF](../../../output/pdf/autosurvey-zh-reading.pdf)

## 摘要

本文提出 AutoSurvey，一种快速且组织有序的方法，用于在人工智能等迅速发展的领域自动撰写全面的文献综述。传统综述写作面临信息数量庞大且内容复杂的挑战，因此需要高效的综述方法。尽管大语言模型（LLM）为这一过程的自动化带来了希望，上下文窗口限制、参数化知识约束以及评价基准缺乏等问题仍然存在。AutoSurvey 通过一套系统流程应对这些挑战，其中包括初始检索与大纲生成、由专门的大语言模型起草各小节、整合与完善，以及严格的评价和迭代。我们的贡献包括一套完整的综述生成方案、一种可靠的评价方法，以及验证 AutoSurvey 有效性的实验。相关资源已开放：https://github.com/AutoSurveys/AutoSurvey 。

## 1 引言

[查看原图表（阅读版）](bilingual.html#autosurvey-0170)

图1：展示了2019年至2024年间arXiv上与大语言模型相关的论文（a）和文献综述（b）数量的增长趋势，并附有T-SNE可视化图。2024年的数据截至4月，红色条柱表示全年的预测数量。尽管文献综述的数量迅速增加，但可视化图表显示仍存在缺乏全面综述的领域。T-SNE图中各簇的研究主题是通过GPT-4生成的，以反映其主要研究领域。这些研究空白簇可以通过AutoSurvey进行处理，成本为1.2美元，每篇文献综述需3分钟时间（成本分析见附录7）。
关于使用大语言模型进行情感识别的示例调查见附录 F。

文献综述提供了重要的学术资源，能够全面概述最新的研究进展、凸显当前趋势并指明未来的研究方向[1, 2, 3, 4]。然而，撰写这类文献综述越来越具有挑战性，尤其是在包含大语言模型（LLM）的快速发展的人工智能领域[5, 6, 7, 8]。图1(a)展示了一个重要趋势：仅2024年前四个月，就有超过4,000篇论文在标题或摘要中包含“大语言模型”这一关键词，并被提交至arXiv平台。
这种激增现象凸显了一个重要的学术问题：新信息的快速积累往往超过了全面学术综述与综合处理的能力，这进一步强调了需要更高效的方法来整合不断增加的文献。此外，如图1(b)所示，尽管文献综述的数量迅速增加，但由于数据量庞大且复杂，传统由人类撰写的文献综述的撰写难度却日益增大，这仍是一个重大挑战。
这一挑战体现在许多领域缺乏全面的文献综述（图1(c)），这阻碍了知识传递，也使得新研究人员难以有效处理大量可用的信息。

大语言模型的出现[ 7, 9 ]为应对这些挑战提供了有前景的途径。这些模型在大量文本语料库上训练后，即使在长上下文场景中也能展现出理解与生成类人文本的卓越能力[ 10, 11, 12 ]。尽管取得了这些进展，但将大语言模型应用于文献综述的生成仍面临诸多挑战。首先，上下文窗口限制：由于处理窗口有限，大语言模型在输出长度方面存在固有的约束[ 13, 14, 15, 16, 17 ]。
尽管包括 GPT-4 和 Claude 3 在内的多种先进大语言模型能够处理超过 10 万个词符的输入，但其输出长度仍限制在不到 8 千个词符以内（GPT-4 的输出长度为 8 千，Claude 3 的输出长度为 4 千）。撰写一份全面的文献综述通常需要阅读数百篇论文，所需的输入规模远远超出了最先进模型的处理能力。此外，一份高质量的文献综述本身也包含数万个词符的内容，因此直接利用大语言模型生成如此庞大的内容是非常具有挑战性的。
其次，参数化知识限制：仅依赖大语言模型内部的知识，不足以生成需要全面且准确的参考文献的文献综述[18, 19, 20]。大语言模型可能会基于错误甚至不存在的“幻觉”参考文献生成内容。此外，这些模型无法纳入训练数据中未包含的最新研究，从而限制了其生成的文献综述的广度和深度。第三，缺乏评估基准：在生成完成后，缺乏用于评估大语言模型输出质量的可靠指标。
依赖人工审核进行质量评估不仅资源消耗巨大，还缺乏可扩展性[ 21, 22, 23 ]。这成为大语言模型在学术综合领域广泛应用的重大障碍，因为准确性和可靠性方面的严格标准至关重要。

为应对这些挑战，我们提出了 AutoSurvey：一种高效且结构清晰的文献综述方法。具体而言，AutoSurvey 的主要创新包括：逻辑性并行生成——AutoSurvey 采用两阶段生成方式，能够高效并行生成调查内容。首先，多个大语言模型同时工作以生成详细大纲；随后，从这些独立大纲中合成出最终的综合大纲，为内容开发提供明确的框架。之后，根据该大纲并行生成调查的每个子部分，从而显著加快了整个流程。
为克服分段生成阶段带来的潜在过渡与一致性问题，AutoSurvey 整合了系统化的修订阶段。在初始并行生成之后，每个部分都会经过全面修订与润色，从而确保流畅的过渡与更高的文档整体一致性。随后，各部分会被无缝合并，形成结构紧凑、条理清晰的最终文档。实时知识更新：AutoSurvey 采用检索增强生成（RAG）方法实现了实时知识更新机制[ 24, 25, 26 ]。该功能确保文献综述的每一个方面都反映最新的研究成果。
当用户输入文献综述主题时，AutoSurvey 利用 RAG 系统检索最新的相关论文，从而生成结构清晰且内容详实的大纲。在撰写子章节时，系统会动态引入与当前内容相关的新研究文章。这种方式能够确保引用信息保持最新，并使文献综述内容与该领域的最新进展保持一致，从而显著提升文献综述的准确性和深度。多大语言模型作为评判器评估：AutoSurvey 采用多大语言模型作为评判器的策略，利用大语言模型作为评判器的方法进行文本评估[ 22, 21, 23 ]。
该方法利用多个大语言模型生成初始评估指标，这些模型会处理大量高质量文献综述数据。随后由人类专家对这些指标进行优化，以确保其精确性并符合学术标准。Multi-LLM-as-Judge方法从两个主要维度对生成内容进行评估：(1) 引用质量，即验证所呈现信息的准确性与可靠性，包含召回率和精确度两个子指标；(2) 内容质量，包括覆盖度（评估主题涵盖范围）、结构（评价逻辑组织与连贯性）以及相关性（确保与主题核心一致）。
通过利用多个大语言模型，该策略能够减少偏见，确保评估的均衡与全面，同时坚守严格的学术标准。

不同文献综述长度（8k、16k、32k 和 64k 个词元）下的大量实验结果表明，AutoSurvey 始终能够获得较高的引用量和内容质量得分。在 64k 个词元时，AutoSurvey 的引用质量达到 82.25% 的召回率与 77.41% 的精确率，优于简单的基于 RAG 的大语言模型（分别为 68.79% 和 61.97%），并接近人类表现水平（分别为 86.33% 和 77.78%）。在内容质量方面，64k 个词元时 AutoSurvey 的覆盖度得分为 4.73，结构得分为 4.33，相关性得分为 4.86，与人类表现水平（分别为 5.00、4.66 和 5.00）非常接近。
在较短长度（8k、16k和32k令牌）下，AutoSurvey在所有指标上仍保持出色的性能。此外，Spearman的rho值表明大语言模型给出的排名与人类专家给出的排名之间存在中等程度的正相关性。混合模型组合达到了最高的相关性为0.5429，说明其与人类偏好高度一致。这些结果进一步证明了我们的多大语言模型评分机制的有效性，为不同长度的文献综述提供了可靠的判断依据。

综上所述，据我们所知，AutoSurvey是首个探索大语言模型智能体在撰写长篇学术文献综述中的潜力的系统。它提出了与人类偏好相一致的文献综述评估标准，为未来的相关研究提供了宝贵的参考依据。

## 2 方法论

[查看原图表（阅读版）](bilingual.html#autosurvey-0177)

图2：用于生成全面调查的大语言模型自动调查流程。

在本节中，我们介绍了 AutoSurvey 用于自动化生成全面文献综述的方法论。我们的方法通过四个不同的阶段逐步推进——初始检索与大纲生成、子章节撰写、整合与优化，以及严格评估与迭代。每个阶段都经过精心设计，旨在解决与文献综述创建相关的特定问题，从而提升最终文献综述文档的效率和质量。AutoSurvey 的伪代码可参见算法1。

[查看原图表（阅读版）](bilingual.html#autosurvey-0179)

算法1 AutoSurvey：利用大语言模型进行自动化调查创建。

### 初始检索与大纲生成

该过程从初始检索与大纲生成阶段开始。通过基于嵌入的检索技术，AutoSurvey 扫描出版物数据库，找出与指定文献综述主题 $T$ 最相关的论文。这一阶段对于确保文献综述基于最相关且最新的研究至关重要。随后，检索到的出版物 $P_{\text{init}}$ 被用于生成结构化大纲 $O$，以全面覆盖主题，并在逻辑上组织综述。为给各小节的写作提供更详细的指导，大纲不仅包含各小节的标题，还包含简短描述。这些描述传达各小节的核心思想，有助于明确整篇综述的内容与方向。由于此阶段检索到的相关论文很多，$P_{\text{init}}$ 的总长度往往超过大语言模型的上下文窗口。为应对这一问题，论文按上下文窗口大小随机划分，用于生成多个大纲；模型再将这些大纲整合为最终的综合大纲。最后，整篇综述的大纲 $O$ 表示为 $O=\text{Outline}(T,P_{\text{init}}).$

### 小节 起草

有了结构化大纲之后，进入小节撰写阶段。专门的大语言模型并行撰写大纲中的各个部分。这既加快了撰写过程，也使各节内容具体而集中，并遵循大纲设定的主题边界。撰写每个小节时，使用该小节的子大纲 $O_{i}$ 检索必要的相关参考论文 $P_{\text{sec}}$，以提供更贴合小节核心思想的信息。写作过程中，模型需要引用所提供的参考论文来支持生成的内容。生成内容中的参考文献会被提取并映射到对应的 arXiv 论文（详见附录 B）。第 $i_{th}$ 个小节 $S_{i}$ 可表示为：$S_{i}=\text{Draft}(O_{i},P_{\text{sec}}).$

### 整合与优化

撰写阶段结束后，分别优化每个小节 $S_{i}$，以提高可读性、消除冗余并确保叙述连贯。优化后的小节 $R_{i}$ 随后合并为一份完整文档 $F$，这对于保持整篇综述的逻辑性和连贯性至关重要。优化过程中，模型根据局部上下文（考虑前后小节）润色每个小节，以改善可读性、消除冗余并增强连贯性。此外，模型还需检查内容中参考文献引用的正确性，并纠正引用错误。该过程表示为：$F=\text{Merge}(R_{1},R_{2},\ldots,R_{n}),\text{where}\ R_{i}=\text{Refine}(S_{i}).$

### 严格的评估与迭代

最后阶段包含严格的评估与迭代过程，其中通过多大语言模型作为评判者的策略对文献综述进行评估。该评估从多个方面对文献综述进行严格审查。从此次评估中获得的见解用于指导进一步的优化，确保文献综述符合最高学术标准。在 $N$ 候选作品中选出最佳文献综述。AutoSurvey 的最终输出为 $F_{\text{best}}=\text{Evaluate}(\{F_{1},F_{2},\ldots,F_{N}\}).$

此处所阐述的方法论——从初始数据检索到复杂的多维度评估——确保 AutoSurvey 能够利用先进的大语言模型技术，有效应对不断发展的研究领域中文献综述创作的复杂性问题。

## 3 个实验

### 设置

我们进行了全面的实验，以评估 AutoSurvey 的性能，并将其与用于撰写文献综述的传统方法进行对比。在 AutoSurvey 的撰写阶段，我们使用了 Claude-3-Haiku，该模型以速度快且成本效益高著称，能够处理 200K 个令牌的数据。在评估过程中，我们结合了 GPT-4、Claude-3-Haiku 和 Gemini-1.5-Pro 三种工具。具体使用的模型包括 gpt-4-0125-preview、claude-3-haiku-20240307 以及 Gemini-1.5-pro-preview。评估涵盖了以下关键性能指标：

•

综述生成速度：为估计人类撰写一篇文档所需的时间，我们使用包含以下参数的数学模型：$L$ 为文档长度，$E$ 为专家人数，$M$ 为每位专家的写作速度，$T_{r}$ 为研究与数据收集的准备时间，$T_{w}$ 为实际写作时间，其中 $T_{w}=\frac{L}{E\times M}$；$T_{e}$ 为编辑与修改时间，其中 $T_{e}=\frac{1}{2}T_{w}$。假设理想情况下 $E=10$（10 名专家）、$M=2000$ token/小时、$T_{r}=5$ 小时，且 $T_{e}=\frac{1}{2}T_{w}$，则总时间 $Time$ 计算如下：

[查看原图表（阅读版）](bilingual.html#autosurvey-0195)

**表格与文字对照**

```text
| $Time=T_{r}+T_{w}+T_{e}=T_{r}+\frac{L}{E\times M}+\frac{1}{2}\times\frac{L}{E\times M}.$ | | (1)

表内文字对照（数值与原始行列保持不变）：
Time → 时间
frac → 分数
times M → times M
times → 次数
```

对于基于 RAG 的大语言模型生成和 AutoSurvey 功能，我们会统计所有 API 调用的时间。速度以 $Speed=\frac{1}{Time(\text{hours})}$ 为单位进行计算。

•

引用质量：借鉴文献 [27]，该指标评估综述中引用的准确性与相关性。假设从综述中提取出的主张集合为 $C=\{c_{1},c_{2},\ldots\}$，该指标利用自然语言推断（NLI）模型 $h$，判断主张 $c_{i}$ 是否受到其参考文献 $\text{Ref}_{i}=\{r_{i_{1}},r_{i_{2}},\ldots\}$ 的支持，其中每个 $r_{i_{k}}$ 代表一篇被引用的论文。$h(c_{i},\text{Ref}_{i})=1$ 表示参考文献支持该主张，否则为 $h(c_{i},\text{Ref}_{i})=0$。详见附录 C。引用质量包含两个子指标：

–

引用回忆度：用于衡量生成文本中的所有陈述是否均得到所引用的段落充分支持，其计算方式为

[查看原图表（阅读版）](bilingual.html#autosurvey-0201)

**表格与文字对照**

```text
| $\text{Recall}=\frac{\sum_{i=1}^{|C|}h(c_{i},\text{Ref}_{i})}{|C|}.$ | | (2)

表内文字对照（数值与原始行列保持不变）：
text → 文本
Recall → 回忆
frac → 分数
sum_ → sum_
h(c_ → h(c_
Ref → 参考
```

–

引用精确率：识别无关引用，确保给出的引用与论述相关，并直接支持相应主张。在给出精确率公式之前，先定义函数 $g$：$g(c_{i},r_{i_{k}})=(h(c_{i},\{r_{i_{k}}\})=1)\cup(h(c_{i},\text{Ref}_{i}\setminus\{r_{i_{k}}\})=0)$，用于衡量论文 $r_{i_{k}}$ 是否与主张 $c_{i}$ 相关。精确率为：

[查看原图表（阅读版）](bilingual.html#autosurvey-0204)

**表格与文字对照**

```text
| $\text{Precision}=\frac{\sum_{i=1}^{|C|}\sum_{k=1}^{|\text{Ref}_{i}|}h(c_{i},\text{Ref}_{i})\cap g(c_{i},r_{i_{k}})}{\sum_{i=1}^{|C|}|\text{Ref}_{i}|}.$ | | (3)

表内文字对照（数值与原始行列保持不变）：
text → 文本
Precision → 精确度
frac → 分数
sum_ → sum_
Ref → 参考
h(c_ → h(c_
cap g(c_ → cap g(c_
```

•

内容质量：这是一个用于评估文献综述质量的综合指标，包含三个子指标。每个子指标由大语言模型根据5分制评分标准进行评判，该标准由人类专家调整以符合学术要求。请注意，详细的评分标准详见表1。

–

覆盖度：评估该调查在多大程度上涵盖了该主题的所有方面。

–

结构：评估各部分的逻辑组织与连贯性。

–

相关性：衡量内容与研究主题的契合程度。

[查看原图表（阅读版）](bilingual.html#autosurvey-0213)

表1：内容质量标准。

### 基线模型

我们将 AutoSurvey 与由人类专家撰写的文献综述（从 Arxiv 中收集）以及基于简单 RAG 的大语言模型在 20 个不同的计算机科学主题以及 LLM 领域的 20 个不同主题上进行了比较（见表 6）。对于基于简单 RAG 的大语言模型，我们首先设定标题和文献综述长度要求，然后逐步引导模型撰写内容直至完成。需要注意的是，我们为该模型提供的参考文献数量与 AutoSurvey 相同。

对于 AutoSurvey 项目，我们使用来自 arXiv 的 530,000 篇计算机科学论文语料库作为检索数据库。在初步撰写阶段，我们检索与给定主题相关的 1200 篇论文，并以 30,000 个词元为窗口大小将其划分为多个部分。此时，模型为每个部分生成一份大纲，并仅基于论文摘要将这些大纲合并成最终的综合大纲。该大纲预先设定了 8 个章节数量。在子章节的撰写过程中，模型根据大纲以及基于子章节描述检索到的 60 篇论文，重点针对每篇论文的主体部分（前 1,500 个词元）生成具体的子章节。
在反思与优化阶段，会向该模型提供相同的参考论文，以确保一致性和准确性。迭代次数 N 设定为 2。请注意，用于评估的人类写作文献在检索过程中会被排除在外。有关实现细节的更多信息，请参见附录 B，提示词则放在附录 F 中。

### 主要结果

[查看原图表（阅读版）](bilingual.html#autosurvey-0219)

表2：基于简单RAG的大语言模型生成、人工写作与自动文献综述的结果。注意，自动文献综述及基于简单RAG的大语言模型生成均使用Claude-haiku作为写作者。另外，用于评估的人工写作文献综述在检索过程中被排除在外。

我们关于人类写作、基于简单 RAG 的大语言模型生成以及 AutoSurvey 在生成学术文献综述方面的实验结果总结在表 2 中。主要发现包括：

•

在速度方面，AutoSurvey 明显优于人类写作和基于 RAG 的大语言模型生成方式。例如，对于包含 64k 个令牌的文献综述，AutoSurvey 每小时可完成 73.59 篇文献综述，而人类写作仅能完成 0.07 篇，基于 RAG 的大语言模型生成则只能完成 12.56 篇，这凸显了长上下文生成在速度上存在的巨大差距。

•

与简单的基于 RAG 的大语言模型生成方式相比，AutoSurvey 的引用质量更高，其表现接近人类写作水平。对于包含 8k 个token的文献综述，AutoSurvey 的引用召回率和精确率分别达到 82.48 和 77.42，优于基于 RAG 的简单大语言模型生成方式（分别为 78.14 和 71.92）。虽然人类写作的表现最优，但我们的结果在不同长度的研究中也接近人类水平。

•

AutoSurvey在内容质量方面表现卓越，在16k个标记的文献综述中平均得分为4.60。其在覆盖广度上达到4.66，结构完整性达到4.33，相关性达到4.86，既符合人类写作水平，也优于基于RAG的大语言模型生成结果。

实验表明，AutoSurvey在质量与效率之间实现了平衡优化。它能够在显著降低时间成本的前提下，达到接近人类水平的覆盖度、相关性和引用质量。虽然人类写作在结构及整体质量上仍具有优势，但AutoSurvey的效率和性能使其成为生成学术文献综述的有力替代方案。尽管基于RAG的通用大语言模型效果不错，但在多个关键方面仍不如人类写作和AutoSurvey，因此作为三种方法之一，其在生成高质量学术文献综述时最不受青睐，尤其是在大纲缺失的情况下，其结构表现也较差。

### Meta评估

为了验证我们的评估方法与人工评估的一致性，我们开展了包含人类专家与自动化评估系统的元评估实验。人类专家对生成的文献综述对进行评判，以判断哪一份更为优秀。这一过程被称为“哪一份更好”测试，是评估的黄金标准。我们将我们的评估方法所做出的判断与人类专家的判断进行了对比。具体而言，我们向专家提供了与我们评估中相同的评分标准作为参考。
专家对生成的20篇文献综述进行了排序，我们利用斯皮尔曼等级相关系数将这些排序与大语言模型生成的排序进行比较，以衡量人类评估与大语言模型评估之间的一致性。

[查看原图表（阅读版）](bilingual.html#autosurvey-0231)

图3：Spearman rho值反映了大语言模型给出的排名与人类专家排名之间的相关程度。注意，A值超过0.3表示正相关，超过0.5则表示强正相关。

本次元评估的结果显示在图3中。表格中展示了斯皮尔曼rho值，用于反映各大语言模型给出的排名与人类专家给出的排名之间的相关程度。斯皮尔曼rho值表明，大语言模型提供的排名与人类专家给出的排名之间存在中等程度的正相关关系，其中混合模型所呈现的相关性最高，为0.5429。这些结果表明，我们的评估方法与人类偏好高度一致，能够作为人类判断的可靠替代指标。

### 剔除研究

为了评估不同组件对 AutoSurvey 性能的影响，我们进行了消融研究，系统地删除了关键组件：检索机制、反射阶段以及迭代次数。此外，我们还评估了使用不同基础大语言模型的影响，以证明即使使用像 Claude-haiku 这样性能稍差的模型，AutoSurvey 的性能仍与人工生成的文献综述相当。

[查看原图表（阅读版）](bilingual.html#autosurvey-0235)

表3：去除不同组件后的 AutoSurvey 删减研究结果。

表3表明，移除检索机制会显著降低引用质量，这凸显了其在确保准确且相关参考文献方面的重要性。缺乏反思阶段会对整体内容质量产生轻微影响，尤其是在结构和连贯性方面。

[查看原图表（阅读版）](bilingual.html#autosurvey-0238)

表4：使用不同基础大语言模型撰写者的 AutoSurvey 性能表现。

表4展示了使用不同大语言模型作为基础写作工具时AutoSurvey的表现情况。结果表明，三种大语言模型（GPT-4、Claude-haiku和Gemini-1.5-Pro）都表现良好，其中GPT-4在整体内容质量方面略优于其他模型。重要的是，即便使用性能稍差的Claude-haiku，AutoSurvey的表现仍与人类标准相媲美。

[查看原图表（阅读版）](bilingual.html#autosurvey-0241)

图4：迭代对AutoSurvey性能的影响。

图4展示了不同迭代次数对AutoSurvey性能的影响。结果表明，将迭代次数从1增加到5时，整体内容质量会略有提升，但超过第二次迭代后收益便逐渐减少。

为了评估所生成的文献综述能否提供有用的信息以丰富知识，我们设计了50道关于5个主题的选择题。这些题目主要涉及与文献相关的知识，例如识别哪篇论文提出了特定方法。我们在以下条件下比较了Claude模型的准确性：(1) 直接选择答案而不提供任何参考材料；(2) 能够访问由基于RAG的LLM生成的32k条文献综述；(3) 能够访问由AutoSurvey生成的32k条文献综述；(4) 可以参考通过选项获取的20篇论文（总计30k个标记）中的内容（上限值，直接检索答案）。

[查看原图表（阅读版）](bilingual.html#autosurvey-0244)

表5：不同参考文献下的性能表现。

结果见表5，我们发现提供与主题相关的材料可以有效提高回答的准确性。提供与选项相关的文献可视为性能的上限（73.60%）。与直接回答相比，AutoSurvey的准确率提高了9.2%，且比使用基于RAG的大语言模型生成的文献进行调查时高出2.4%。这表明我们的方法能够有效提供主题知识。

总结来说，消融实验凸显了检索机制与反思阶段在 AutoSurvey 中的关键作用。此外，使用不同的大语言模型作为基础生成器以及调整迭代次数也会对性能产生影响。尽管如此，AutoSurvey 在不同配置下仍能保持良好的表现，展现了其稳健性和高效性。

## 4 相关研究

### 长文本生成

大语言模型有效处理与生成长文本的能力是一个关键挑战，因为需要在较长的文本段落中保持连贯性和逻辑性[28, 29, 30, 31]。一些研究尝试通过采用不同的位置编码技术来直接扩展上下文窗口来应对这一挑战[32, 33]。然而，修改位置编码策略需要重新训练模型，这成本较高。另一种解决方案是采用增强式记忆技术。
RecurrentGPT [ 34 ] 通过利用自然语言提示来存储之前的上下文信息，模拟 RNN 的递归机制，从而能够生成任意长度的文本。Temp-Lora [ 35 ] 则通过将上下文信息嵌入到临时 Lora 模块中并在生成过程中逐步更新该模块，而非依赖庞大的上下文窗口，从而实现长文本生成。这些方法有效地建立了令牌之间的关联并保持了上下文理解能力，但仍然存在长生成时间的问题。
为了进一步加速生成过程，人们广泛探索了分层建模技术，以捕捉长文本固有的层次结构特性[ 36, 37 ]。尽管这种方法效率较高，却忽略了文本的长期依赖关系，可能导致内容质量下降[ 38 ]。为克服这些缺陷，AutoSurvey同样采用分层生成范式，通过构建结构清晰的大纲来提供指导，并优化生成内容以提升质量。

### 自动写作

由于人工写作的高成本，自动化写作近年来吸引了大量研究关注。与主要致力于训练模型生成语言连贯文本的传统方法[39, 40]相比，大语言模型的出现为自动化写作带来了新的可能性，使人们对忠实性、逻辑结构、风格及伦理等更广泛方面给予了更多关注[41, 42, 43, 44]。例如，检索增强生成技术有助于生成带有引用依据的论点[27, 45]。
IRP框架[46]通过迭代执行内容规划、事实检索和改写操作来生成说明性文本，从而确保信息的准确性与风格一致性。许多研究致力于大纲的构建，以优化生成内容的结构。PaperRobot[47]通过逐步编写关键要素来生成论文摘要。STORM[20]则基于多轮wiki页面相关问答过程设计出完善的大纲，从而促进类似wiki的文章生成。这些方法仅在较短文本（<4k）中得到了探索。相比之下，Autosurvey在生成长文本（64k）方面表现出有效性，尤其适用于学术评论场景。

## 5 局限性

除了直接使用召回率和精确率来评估引文外，我们还进行了人工分析，从而能够更全面地了解引文的质量。我们检查了100条无依据的声明及其对应的参考文献，发现这些错误主要属于三类：(1) 不一致；(2) 误解；(3) 过度概括。不一致是指两者之间的关联被错误建立，例如出现无关的引文；误解则发生在声明与来源存在关联，但声明却错误地反映了该来源的信息。
当某个主张将原始材料的结论推广到超出支持范围的更广阔语境时，就会出现过度泛化现象。在三种错误类型中，过度泛化占比最高（51%），表明大语言模型在写作时仍严重依赖其参数化知识。误解占比较小（10%），说明大语言模型在大多数情况下能够理解参考文献的内容，从而避免提出与参考文献严重偏离的主张。

不一致性（39%）：一个例子是，在所引用的文献并未提出 GDPR 的情况下，却引用了“通用数据保护条例（GDPR）”。

误解（10%）：一个例子是声称“上下文学习使得大语言模型仅通过依赖少量示例即可适应新任务，无需任何参数更新或微调”，该观点基于一篇专注于元上下文学习的文献，且该文献也提到了上下文学习的局限性。

泛化过度（51%）：一个例子是“上下文学习也可以从其他学习范式的进步中受益，例如多任务学习”，该观点基于一篇讨论多任务少样本学习的文献，但并未明确说明其对上下文学习的影响。

在三种错误类型中，过度泛化所占比例最高（51%），表明大语言模型在写作时仍严重依赖其参数化知识。误解所占比例较小（10%），说明大语言模型在大多数情况下能够理解参考文献的内容，不会生成与参考文献严重偏离的论断。关于潜在的额外社会影响及伦理问题，详见附录E。

## 6 结论

在本文中，我们介绍了 AutoSurvey 这一创新方法，该方法利用大语言模型来自动化完成全面的文献综述工作。通过包含初始检索、大纲生成、并行子章节撰写、整合及严格评估等系统性步骤，AutoSurvey 解决了上下文窗口限制和参数化知识约束等关键问题。我们的实验表明，AutoSurvey 显著优于简单的基于 RAG 的大语言模型生成方式，在内容与引用质量方面与人类表现相当，同时效率也极高。
这一进展为合成研究文献提供了可扩展且有效的解决方案，为人工智能等快速发展的领域中的研究人员提供了宝贵的工具。

## 参考文献

[1] Samira Pouyanfar, Saad Sadiq, Yilin Yan, Haiman Tian, Yudong Tao, Maria Presa Reyes, Mei-Ling Shyu, Shu-Ching Chen, and Sundaraja S Iyengar. A survey on deep learning: Algorithms, techniques, and applications. ACM Computing Surveys (CSUR) , 51(5):1–36, 2018.

[2] Yupeng Chang, Xu Wang, Jindong Wang, Yuan Wu, Linyi Yang, Kaijie Zhu, Hao Chen, Xiaoyuan Yi, Cunxiang Wang, Yidong Wang, et al. A survey on evaluation of large language models. ACM Transactions on Intelligent Systems and Technology , 2023.

[3] Wayne Xin Zhao, Kun Zhou, Junyi Li, Tianyi Tang, Xiaolei Wang, Yupeng Hou, Yingqian Min, Beichen Zhang, Junjie Zhang, Zican Dong, et al. A survey of large language models. arXiv preprint arXiv:2303.18223 , 2023.

[4] Salman Khan, Muzammal Naseer, Munawar Hayat, Syed Waqas Zamir, Fahad Shahbaz Khan, and Mubarak Shah. Transformers in vision: A survey. ACM computing surveys (CSUR) , 54(10s):1–41, 2022.

[5] Yann LeCun, Yoshua Bengio, and Geoffrey Hinton. Deep learning. nature , 521(7553):436–444, 2015.

[6] Ian Goodfellow, Yoshua Bengio, and Aaron Courville. Deep learning . MIT press, 2016.

[7] Josh Achiam, Steven Adler, Sandhini Agarwal, Lama Ahmad, Ilge Akkaya, Florencia Leoni Aleman, Diogo Almeida, Janko Altenschmidt, Sam Altman, Shyamal Anadkat, et al. Gpt-4 technical report. arXiv preprint arXiv:2303.08774 , 2023.

[8] Alexander Kirillov, Eric Mintun, Nikhila Ravi, Hanzi Mao, Chloe Rolland, Laura Gustafson, Tete Xiao, Spencer Whitehead, Alexander C Berg, Wan-Yen Lo, et al. Segment anything. In Proceedings of the IEEE/CVF International Conference on Computer Vision , pages 4015–4026, 2023.

[9] Hugo Touvron, Thibaut Lavril, Gautier Izacard, Xavier Martinet, Marie-Anne Lachaux, Timothée Lacroix, Baptiste Rozière, Naman Goyal, Eric Hambro, Faisal Azhar, et al. Llama: Open and efficient foundation language models. arXiv preprint arXiv:2302.13971 , 2023.

[10] Shouyuan Chen, Sherman Wong, Liangjian Chen, and Yuandong Tian. Extending context window of large language models via positional interpolation. arXiv preprint arXiv:2306.15595 , 2023.

[11] Yukang Chen, Shengju Qian, Haotian Tang, Xin Lai, Zhijian Liu, Song Han, and Jiaya Jia. Longlora: Efficient fine-tuning of long-context large language models. In The Twelfth International Conference on Learning Representations , 2023.

[12] Weizhi Wang, Li Dong, Hao Cheng, Xiaodong Liu, Xifeng Yan, Jianfeng Gao, and Furu Wei. Augmenting language models with long-term memory. Advances in Neural Information Processing Systems , 36, 2024.

[13] Nelson F Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. Lost in the middle: How language models use long contexts. Transactions of the Association for Computational Linguistics , 12:157–173, 2024.

[14] Jean Kaddour, Joshua Harris, Maximilian Mozes, Herbie Bradley, Roberta Raileanu, and Robert McHardy. Challenges and applications of large language models. arXiv preprint arXiv:2307.10169 , 2023.

[15] Freda Shi, Xinyun Chen, Kanishka Misra, Nathan Scales, David Dohan, Ed H Chi, Nathanael Schärli, and Denny Zhou. Large language models can be easily distracted by irrelevant context. In International Conference on Machine Learning , pages 31210–31227. PMLR, 2023.

[16] Dacheng Li, Rulin Shao, Anze Xie, Ying Sheng, Lianmin Zheng, Joseph Gonzalez, Ion Stoica, Xuezhe Ma, and Hao Zhang. How long can context length of open-source llms truly promise? In NeurIPS 2023 Workshop on Instruction Tuning and Instruction Following , 2023.

[17] Tianle Li, Ge Zhang, Quy Duc Do, Xiang Yue, and Wenhu Chen. Long-context llms struggle with long in-context learning. arXiv preprint arXiv:2404.02060 , 2024.

[18] Cunxiang Wang, Xiaoze Liu, Yuanhao Yue, Xiangru Tang, Tianhang Zhang, Cheng Jiayang, Yunzhi Yao, Wenyang Gao, Xuming Hu, Zehan Qi, et al. Survey on factuality in large language models: Knowledge, retrieval and domain-specificity. arXiv preprint arXiv:2310.07521 , 2023.

[19] Ziwei Ji, Nayeon Lee, Rita Frieske, Tiezheng Yu, Dan Su, Yan Xu, Etsuko Ishii, Ye Jin Bang, Andrea Madotto, and Pascale Fung. Survey of hallucination in natural language generation. ACM Computing Surveys , 55(12):1–38, 2023.

[20] Yijia Shao, Yucheng Jiang, Theodore A. Kanell, Peter Xu, Omar Khattab, and Monica S. Lam. Assisting in Writing Wikipedia-like Articles From Scratch with Large Language Models. In Proceedings of the 2024 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers) , 2024.

[21] Yidong Wang, Zhuohao Yu, Zhengran Zeng, Linyi Yang, Cunxiang Wang, Hao Chen, Chaoya Jiang, Rui Xie, Jindong Wang, Xing Xie, Wei Ye, Shikun Zhang, and Yue Zhang. Pandalm: An automatic evaluation benchmark for llm instruction tuning optimization. 2024.

[22] Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric Xing, et al. Judging llm-as-a-judge with mt-bench and chatbot arena. Advances in Neural Information Processing Systems , 36, 2024.

[23] Zhuohao Yu, Chang Gao, Wenjin Yao, Yidong Wang, Wei Ye, Jindong Wang, Xing Xie, Yue Zhang, and Shikun Zhang. Kieval: A knowledge-grounded interactive evaluation framework for large language models. 2024.

[24] Yunfan Gao, Yun Xiong, Xinyu Gao, Kangxiang Jia, Jinliu Pan, Yuxi Bi, Yi Dai, Jiawei Sun, and Haofen Wang. Retrieval-augmented generation for large language models: A survey. arXiv preprint arXiv:2312.10997 , 2023.

[25] Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, et al. Retrieval-augmented generation for knowledge-intensive nlp tasks. Advances in Neural Information Processing Systems , 33:9459–9474, 2020.

[26] Zhengbao Jiang, Frank F Xu, Luyu Gao, Zhiqing Sun, Qian Liu, Jane Dwivedi-Yu, Yiming Yang, Jamie Callan, and Graham Neubig. Active retrieval augmented generation. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing , pages 7969–7992, 2023.

[27] Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. Enabling large language models to generate text with citations. In Proceedings of the 2023 Conference on Empirical Methods in Natural Language Processing , 2023.

[28] Bowen Tan, Zichao Yang, Maruan Al-Shedivat, Eric P. Xing, and Zhiting Hu. Progressive generation of long text with pretrained language models. In Kristina Toutanova, Anna Rumshisky, Luke Zettlemoyer, Dilek Hakkani-Tür, Iz Beltagy, Steven Bethard, Ryan Cotterell, Tanmoy Chakraborty, and Yichao Zhou, editors, Proceedings of the 2021 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, NAACL-HLT 2021, Online, June 6-11, 2021 , pages 4313–4324. Association for Computational Linguistics, 2021.

[29] Yushi Bai, Xin Lv, Jiajie Zhang, Hongchang Lyu, Jiankai Tang, Zhidian Huang, Zhengxiao Du, Xiao Liu, Aohan Zeng, Lei Hou, Yuxiao Dong, Jie Tang, and Juanzi Li. Longbench: A bilingual, multitask benchmark for long context understanding. CoRR , abs/2308.14508, 2023.

[30] Zican Dong, Tianyi Tang, Junyi Li, Wayne Xin Zhao, and Ji-Rong Wen. BAMBOO: A comprehensive benchmark for evaluating long text modeling capacities of large language models. CoRR , abs/2309.13345, 2023.

[31] Jiaqi Li, Mengmeng Wang, Zilong Zheng, and Muhan Zhang. Loogle: Can long-context language models understand long contexts? CoRR , abs/2311.04939, 2023.

[32] Peter Shaw, Jakob Uszkoreit, and Ashish Vaswani. Self-attention with relative position representations. In Marilyn A. Walker, Heng Ji, and Amanda Stent, editors, Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, NAACL-HLT, New Orleans, Louisiana, USA, June 1-6, 2018, Volume 2 (Short Papers) , pages 464–468. Association for Computational Linguistics, 2018.

[33] Xing Wang, Zhaopeng Tu, Longyue Wang, and Shuming Shi. Self-attention with structural position representations. In Kentaro Inui, Jing Jiang, Vincent Ng, and Xiaojun Wan, editors, Proceedings of the 2019 Conference on Empirical Methods in Natural Language Processing and the 9th International Joint Conference on Natural Language Processing, EMNLP-IJCNLP 2019, Hong Kong, China, November 3-7, 2019 , pages 1403–1409. Association for Computational Linguistics, 2019.

[34] Wangchunshu Zhou, Yuchen Eleanor Jiang, Peng Cui, Tiannan Wang, Zhenxin Xiao, Yifan Hou, Ryan Cotterell, and Mrinmaya Sachan. Recurrentgpt: Interactive generation of (arbitrarily) long text. arXiv preprint arXiv:2305.13304 , 2023.

[35] Y Wang, D Ma, and D Cai. With greater text comes greater necessity: Inference-time training helps long text generation. arXiv preprint arXiv:2401.11504 , 2024.

[36] Angela Fan, Mike Lewis, and Yann Dauphin. Hierarchical neural story generation. arXiv preprint arXiv:1805.04833 , 2018.

[37] Jeff Wu, Long Ouyang, Daniel M Ziegler, Nisan Stiennon, Ryan Lowe, Jan Leike, and Paul Christiano. Recursively summarizing books with human feedback. arXiv preprint arXiv:2109.10862 , 2021.

[38] Yapei Chang, Kyle Lo, Tanya Goyal, and Mohit Iyyer. Booookscore: A systematic exploration of book-length summarization in the era of llms. arXiv preprint arXiv:2310.00785 , 2023.

[39] Woon Sang Cho, Pengchuan Zhang, Yizhe Zhang, Xiujun Li, Michel Galley, Chris Brockett, Mengdi Wang, and Jianfeng Gao. Towards coherent and cohesive long-form text generation. arXiv preprint arXiv:1811.00511 , 2018.

[40] Antoine Bosselut, Asli Celikyilmaz, Xiaodong He, Jianfeng Gao, Po-Sen Huang, and Yejin Choi. Discourse-aware neural rewards for coherent text generation. arXiv preprint arXiv:1805.03766 , 2018.

[41] Wenxuan Zhou, Sheng Zhang, Hoifung Poon, and Muhao Chen. Context-faithful prompting for large language models. arXiv preprint arXiv:2303.11315 , 2023.

[42] Jinxin Liu, Shulin Cao, Jiaxin Shi, Tingjian Zhang, Lei Hou, and Juanzi Li. Probing structured semantics understanding and generation of language models via question answering. arXiv preprint arXiv:2401.05777 , 2024.

[43] Chiyu Zhang, Honglong Cai, Yuexin Wu, Le Hou, Muhammad Abdul-Mageed, et al. Distilling text style transfer with self-explanation from llms. arXiv preprint arXiv:2403.01106 , 2024.

[44] Patrick Schramowski, Cigdem Turan, Nico Andersen, Constantin A Rothkopf, and Kristian Kersting. Large pre-trained language models contain human-like biases of what is right and wrong to do. Nature Machine Intelligence , 4(3):258–268, 2022.

[45] Jacob Menick, Maja Trebacz, Vladimir Mikulik, John Aslanides, Francis Song, Martin Chadwick, Mia Glaese, Susannah Young, Lucy Campbell-Gillingham, Geoffrey Irving, et al. Teaching language models to support answers with verified quotes. arXiv preprint arXiv:2203.11147 , 2022.

[46] Nishant Balepur, Jie Huang, and Kevin Chen-Chuan Chang. Expository text generation: Imitate, retrieve, paraphrase. arXiv preprint arXiv:2305.03276 , 2023.

[47] Qingyun Wang, Lifu Huang, Zhiying Jiang, Kevin Knight, Heng Ji, Mohit Bansal, and Yi Luan. Paperrobot: Incremental draft generation of scientific ideas. arXiv preprint arXiv:1905.07870 , 2019.

[48] Zach Nussbaum, John X. Morris, Brandon Duderstadt, and Andriy Mulyar. Nomic embed: Training a reproducible long context text embedder, 2024.

## 附录 A 主题详情及人类写作文献综述

我们从大语言模型领域的不同主题中选取了20篇文献综述。在筛选过程中，我们同时考虑了主题的涵盖范围以及这些文献在谷歌学术上的引用次数。这些文献综述的基本信息列于表6中。

[查看原图表（阅读版）](bilingual.html#autosurvey-0312)

表6：文献综述表

## 附录 B 实现细节

我们采用了 nomic-embed-text-v1.5 [ 48 ] 模型，该模型是 RAG 应用中最常用的嵌入模型。为了构建我们的数据库，我们会存储每篇论文的标题和摘要的嵌入向量。由于上下文窗口长度为 8k，比任何单个摘要都要长，因此我们直接对原始文本进行嵌入处理，无需分块。在生成过程中，系统会根据摘要检索相关论文，并根据与查询的相似度对它们进行排序。在生成子章节内容时，模型需要写出需要引用引用的对应论文标题。生成完成后，每个标题会被作为查询进行嵌入，并映射到数据库中最近的论文标题。
这种方法使大语言模型能够利用自身的参数知识生成无参考文献的引文，同时确保这些引文的真实性。在调用 API 时，我们默认设置温度值为 1 及其他参数。即使使用相同的参数，生成的文献综述的最终长度也会有所不同。因此，长度为 8k 到 16k 的论文被归类为 8k 类别，而长度为 16k 到 32k 的论文则被归类为 16k 类别，依此类推。

## 附录 C 评估细节

在引用质量方面，我们将包含至少一条引用的句子定义为一个主张，并从生成的文献综述中提取所有主张。在人工评估环节，我们邀请了三名博士生参与，他们均具有撰写大语言模型相关文献综述的经验。我们为他们提供了相同的评分标准及具体指标的说明，要求他们依据这些标准进行评分，最终生成的文献综述排名则根据总得分确定。

## 附录 D 成本分析

我们在表7中展示了生成32k个token的文献综述所需的平均标记数，以及使用不同大语言模型的成本。

[查看原图表（阅读版）](bilingual.html#autosurvey-0320)

表7：AutoSurvey的成本

## 附录 E 社会影响与伦理考量

通过整合各种专业数据库，我们的方法能够生成不同领域的学术文献综述，从而可能填补现有评论中的空白。然而，由于该方法依赖于大语言模型的性能，因此不可避免地存在引用错误。因此，生成的文献综述内容仅用于参考之用。参与评估过程的所有人员均为自愿参与，并获得了充足的报酬。我们实验中使用的所有数据均来自 arXiv，且允许用于非商业用途。

## 附录 F 在 AutoSurvey 中使用的提示词

⬇ ROUGH_OUTLINE_PROMPT = ’’ ’ 您需要撰写一篇关于 [主题] 的全面学术文献综述。您获得了以下与该主题相关的论文列表：--- [论文列表] --- 您需要根据这些论文起草一个大纲。该大纲应包含标题及多个部分。每个部分后需附有一句简短说明，指出该部分应写什么内容。大纲需具有全面性，并包含 [部分编号] 个部分。请以以下格式返回：<format> 标题：[文献综述标题] 第1部分：[第1部分的名称] 描述1：[第1段文字描述]... 第K部分：[第K部分的名称] 描述K：[第K段文字描述] </format>
大纲：’ ’’ SUBSECTION_OUTLINE_PROMPT = ’’ ’ 你需要撰写一篇关于[主题]的文献综述。你已制定如下大纲：--- [整体大纲] --- 该大纲包含标题及多个部分。每个部分后都附有一句简短说明，用于指出该部分应写的内容。你需要丰富[部分名称]部分的内容。[部分名称]的描述：[部分描述]。你需要根据整体大纲生成包含多个子部分的框架。每个子部分后也附有一句简短说明，用于指出该子部分应写的内容。这些文献提供了参考文献：--- [文献列表] --- 请以<格式>的形式返回大纲。
小节 1：[小节 1 名称] 描述 1：[小节 1 的内容] …… 小节 K：[小节 K 名称] 描述 K：[小节 K 的内容] </format> 仅返回大纲，不提供其他信息： ’ ’’ MERGING_OUTLINE_PROMPT = ’’ ’ 你需要撰写一篇关于 [主题] 的文献综述。下面提供了一些作为候选的大纲列表： --- [大纲列表] --- 每个大纲包含标题及多个部分。每个部分后都附有一句简短的句子，说明该部分应写什么内容。你需要基于这些提供的大纲生成最终大纲，使最终大纲能够全面反映该主题的见解并更加逻辑清晰。
按以下格式返回内容：<format> 标题：[文献综述标题] 第1节：[第1节名称] 描述1：[第1段文字描述]... 第K节：[第K节名称] 描述K：[第K段文字描述] </format> 仅返回最终大纲，不提供其他任何信息： ’ ’’ SUBSECTION_WRITING_PROMPT = ’’ ’ 你需要撰写一篇关于[主题]的全面性文献综述。你已制定如下整体大纲：--- [整体大纲]--- 以下是可供参考的论文列表：--- [论文列表]--- 现在你需要撰写[子章节名称]的内容。该子章节应写什么内容的详细要求见此描述：
--- [DESCRIPTION] --- 请遵循以下要求：1. 该小节建议包含超过 [WORD NUM] 个单词的内容。2. 在撰写基于上述特定论文的句子时，请以 ’ [] ’ 格式引用“paper_title”以支持你的内容。以下是文献综述中引用论文的简要指南：--- 1. 总结研究内容：在总结现有文献时引用来源。2. 使用特定概念或数据：讨论特定理论、模型或数据时提供引用。3. 使用成熟方法：在文献综述中引用所采用方法的创造者。4. 支持论点：引用支持你结论的来源。
以及论据。--- 仅返回您为子章节[ SUBSECTION NAME ]所撰写的超过[ WORD NUM ]字的内容，不要包含其他信息：’’ ’ CITATION_REFLECTION_PROMPT = ’ ’’ 您希望撰写一篇关于[ TOPIC ]的全面文献综述。以下是用于引用的论文列表：--- [ PAPER LIST ] --- 您已编写了子章节：--- [ SUBSECTION ] --- 基于上述特定论文的句子后面会加上“paper_title”的引用，格式为“[]”。例如‘the emergence of large language models (LLMs) [PaLM: Scaling language modeling with pathways]’。以下是文献综述中何时引用论文的简要指南：--- 1. 总结
研究：在总结现有文献时需注明出处。2. 使用特定概念或数据：讨论特定理论、模型或数据时需提供引用。3. 使用成熟方法：在文献综述中需注明所采用方法的提出者。4. 支持论点：引用能够支撑你的结论和论点的来源。--- 现在你需要检查本小节中“paper_title”的引用是否正确。如果引用无法支持你所写的句子，请修改 ’ [] ’ 中的 paper_title 或将其删除。除引用外，不要更改其他任何内容。仅返回引用正确的小节：’ ’’ COHERENCY_REFINEMENT_PROMPT = ’’ ’ 你
想要撰写一篇全面且完整的文献综述。现在你需要协助完善其中一个小节，以提升该文献综述的连贯性。你已获得该小节的内容以及之前和后续的小节内容。之前的小节：--- [PREVIOUS] --- 后续小节：--- [FOLLOWING] --- 需要完善的小节：--- [SUBSECTION] --- 请完善该小节，增强其连贯性，并确保它能更流畅地与之前和后续小节相衔接。请记住，要保留该小节的全部核心信息，不要修改句后括号内的任何引用内容！！！仅返回完整内容
不含其他信息的该小节精炼内容：’ ’’

⬇ # 基于大语言模型的情感识别综合文献综述

## 1. 情感识别与大语言模型简介 情感识别是情感计算领域一个关键且活跃的研究方向，其目标是使机器能够理解、解读并回应人类情绪[1]。情绪在人类认知、决策和社交互动中起着基础性作用[2]，而自动识别与解读情绪的能力具有广泛的应用前景，包括医疗保健、教育、娱乐以及人机交互等领域[3]。情感识别的重要性在诸多实际场景中都表现得十分明显
全球应用。在医疗保健领域，情绪识别可用于监测患者心理健康、提供个性化治疗以及改善医患沟通 [4]。在教育领域，情绪识别有助于识别学生的参与度和挫败感水平，从而打造能够满足个人需求的自适应学习环境 [5]。在娱乐产业中，情绪识别可用于分析观众反应，并调整内容以引发预期的情感反应 [6]。尽管情绪识别具有显著优势，但该领域仍面临诸多阻碍其广泛应用和实施的挑战 [7]。其中主要挑战之一是……
情绪固有的复杂性和主观性因人而异、因文化而异、因情境而异[8]。情绪通常通过多种方式表达，包括面部表情、声音信号、肢体语言以及生理信号，整合这些不同的信息来源是一个重大挑战[9]。此外，高质量、多样化且带有注释的情绪数据集的获取也是该领域长期存在的难题[10]。许多现有数据集在规模上有限、缺乏多样性，或者存在不一致或主观的情绪标注，这可能导致偏见以及情绪识别模型的泛化能力较差[11]。...


### 1.1 情感识别背景


### 1.2 大语言模型及其能力


### 1.3 大语言模型中的情感表示


### 1.4 使用大语言模型的多模态情感识别


###

## 2. 使用大语言模型进行情感识别的技术与方法


### 2.1 在情感数据集上对大语言模型进行微调


### 2.2 基于大语言模型的情感识别提示方法


### 2.3 将大语言模型与其他模态结合用于多模态情感识别


###

## 3. 提升基于大语言模型的情感识别效果


### 3.1 数据增强以提高情感识别性能


### 3.2 情感识别的提示工程设计


### 3.3 整合外部知识以改进情感识别


###

## 4. 挑战、局限与伦理问题
考虑因素

### 4.1 模型偏差与幻觉


### 4.2 可解释性


### 4.3 伦理考量


## 5. 应用与未来方向


### 5.1 辅助机器人技术


### 5.2 心理健康评估


### 5.3 客户服务与用户体验


### 5.4 符号推理与长尾情绪


### 5.5 稳健评估框架


## 参考文献 [1] 大规模异构多媒体数据情感计算文献综述 [2] 对话中的情绪识别：研究挑战、数据集与最新进展 [3] 情感计算综合综述：挑战、趋势、应用与未来方向 [4] 情感计算
医疗领域最新趋势、应用、挑战及未来方向 [5] 无需传感器的情感检测：一项系统文献综述 [6] 情感视频内容分析：十年回顾与新视角 [7] 多模态情感识别：基础理论与方法 [8] 情感表征的模糊世界 [9] 基于层次化注意力策略与词级对齐的多模态情感分析 [10] 表情、情感及动作单元识别：Aff-Wild2、多任务学习与ArcFace技术 [11] 用于视频情感分类的特征维度降维：一项比较研究

