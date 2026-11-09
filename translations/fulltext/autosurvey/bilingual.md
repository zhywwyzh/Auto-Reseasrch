# AutoSurvey：大语言模型能够自动撰写综述

AutoSurvey: Large Language Models Can Automatically Write Surveys

Wang, Yidong; Guo, Qi; Yao, Wenjin; Zhang, Hongbo; Zhang, Xin; Wu, Zhen; Zhang, Meishan; Dai, Xinyu; Zhang, Min; Wen, Qingsong; Ye, Wei; Zhang, Shikun; Zhang, Yue

> 非官方机器初译，正文尚未逐段精校。图表保留原文内容，图内英文未另行翻译；有 HTML 原文的公式按原式排版。PDF 提取版保留对应原页，点击缩略图放大核对图表与公式。

原文版本：2406.10252v2 · [原始来源](https://arxiv.org/abs/2406.10252v2) · [中文 PDF](../../../output/pdf/autosurvey-zh-reading.pdf)

<details>
<summary>作者、机构和出版信息</summary>

Yidong Wang

†

†

thanks:

Equal contribution. yidongwang37@gmail.com, qguo@smail.nju.edu.cn; Yidong Wang did this work during his internship at Squirrel AI.

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Qi Guo

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Wenjin Yao

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Hongbo Zhang

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Xin Zhang

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Zhen Wu

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Meishan Zhang

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Xinyu Dai

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Min Zhang

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Qingsong Wen

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Wei Ye

†

†

thanks:

Correspondence to: wye@pku.edu.cn, zhangsk@pku.edu.cn, zhangyue@westlake.edu.cn.

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Shikun Zhang

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

Yue Zhang

Affiliation:

1

Westlake University,

2

Peking University,

3

Nanjing University,

4

Harbin Institute of Technology,
Shenzhen,

5

Squirrel AI

</details>

## 摘要


<details>
<summary>英文原文</summary>

Abstract

</details>

本文提出 AutoSurvey，一种快速且组织有序的方法，用于在人工智能等迅速发展的领域自动撰写全面的文献综述。传统综述写作面临信息数量庞大且内容复杂的挑战，因此需要高效的综述方法。尽管大语言模型（LLM）为这一过程的自动化带来了希望，上下文窗口限制、参数化知识约束以及评价基准缺乏等问题仍然存在。AutoSurvey 通过一套系统流程应对这些挑战，其中包括初始检索与大纲生成、由专门的大语言模型起草各小节、整合与完善，以及严格的评价和迭代。我们的贡献包括一套完整的综述生成方案、一种可靠的评价方法，以及验证 AutoSurvey 有效性的实验。相关资源已开放：https://github.com/AutoSurveys/AutoSurvey 。


<details>
<summary>英文原文</summary>

This paper introduces AutoSurvey, a speedy and well-organized methodology for automating the creation of comprehensive literature surveys in rapidly evolving fields like artificial intelligence. Traditional survey paper creation faces challenges due to the vast volume and complexity of information, prompting the need for efficient survey methods. While large language models (LLMs) offer promise in automating this process, challenges such as context window limitations, parametric knowledge constraints, and the lack of evaluation benchmarks remain. AutoSurvey addresses these challenges through a systematic approach that involves initial retrieval and outline generation, subsection drafting by specialized LLMs, integration and refinement, and rigorous evaluation and iteration. Our contributions include a comprehensive solution to the survey problem, a reliable evaluation method, and experimental validation demonstrating AutoSurvey’s effectiveness. We open our resources at https://github.com/AutoSurveys/AutoSurvey .

</details>

## 1 引言


<details>
<summary>英文原文</summary>

1 Introduction

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0170)

图1：展示了2019年至2024年间arXiv上与大语言模型相关的论文（a）和文献综述（b）数量的增长趋势，并附有T-SNE可视化图。2024年的数据截至4月，红色条柱表示全年的预测数量。尽管文献综述的数量迅速增加，但可视化图表显示仍存在缺乏全面综述的领域。T-SNE图中各簇的研究主题是通过GPT-4生成的，以反映其主要研究领域。这些研究空白簇可以通过AutoSurvey进行处理，成本为1.2美元，每篇文献综述需3分钟时间（成本分析见附录7）。
关于使用大语言模型进行情感识别的示例调查见附录 F。


<details>
<summary>英文原文</summary>

Figure 1 : Depicting growth trends from 2019 to 2024 in the number of LLMs-related papers (a) and surveys (b) on arXiv, accompanied by a T-SNE visualization. The data for 2024 is up to April, with a red bar representing the forecasted numbers for the entire year. While the number of surveys is increasing rapidly, the visualization reveals areas where comprehensive surveys are still lacking, despite the overall growth in survey numbers. The research topics of the clusters in the T-SNE plot are generated using GPT-4 to describe their primary focus areas. These clusters of research voids can be addressed using AutoSurvey at a cost of $1.2 (cost analysis in Appendix 7 ) and 3 minutes per survey. An example survey focused on Emotion Recognition using LLMs is in Appendix F .

</details>

文献综述提供了重要的学术资源，能够全面概述最新的研究进展、凸显当前趋势并指明未来的研究方向[1, 2, 3, 4]。然而，撰写这类文献综述越来越具有挑战性，尤其是在包含大语言模型（LLM）的快速发展的人工智能领域[5, 6, 7, 8]。图1(a)展示了一个重要趋势：仅2024年前四个月，就有超过4,000篇论文在标题或摘要中包含“大语言模型”这一关键词，并被提交至arXiv平台。
这种激增现象凸显了一个重要的学术问题：新信息的快速积累往往超过了全面学术综述与综合处理的能力，这进一步强调了需要更高效的方法来整合不断增加的文献。此外，如图1(b)所示，尽管文献综述的数量迅速增加，但由于数据量庞大且复杂，传统由人类撰写的文献综述的撰写难度却日益增大，这仍是一个重大挑战。
这一挑战体现在许多领域缺乏全面的文献综述（图1(c)），这阻碍了知识传递，也使得新研究人员难以有效处理大量可用的信息。


<details>
<summary>英文原文</summary>

Survey papers provide essential academic resources, offering comprehensive overviews of recent research developments, highlighting ongoing trends, and identifying future directions [ 1 , 2 , 3 , 4 ] . However, crafting these surveys is increasingly challenging, especially in the fast-paced domain of Artificial Intelligence including large language models(LLMs) [ 5 , 6 , 7 , 8 ] . Figure 1(a) illustrates a significant trend: in just the first four months of 2024 alone, over 4,000 papers containing the phrase "Large Language Model" in their titles or abstracts were submitted to arXiv. This surge highlights a critical academic issue: the rapid accumulation of new information often outpaces the capacity for comprehensive scholarly review and synthesis, emphasizing the growing need for more efficient methods to synthesize the expanding literature. Moreover, as depicted in Figure 1(b) , while the number of survey papers has rapidly increased, the growing difficulty of producing traditional human-authored survey papers—due to the sheer volume and complexity of data—remains a significant challenge. This challenge is evidenced by the lack of comprehensive surveys in many fields (Figure 1(c) ), which hinders knowledge transfer and makes it difficult for new researchers to efficiently navigate the vast amount of available information.

</details>

大语言模型的出现[ 7, 9 ]为应对这些挑战提供了有前景的途径。这些模型在大量文本语料库上训练后，即使在长上下文场景中也能展现出理解与生成类人文本的卓越能力[ 10, 11, 12 ]。尽管取得了这些进展，但将大语言模型应用于文献综述的生成仍面临诸多挑战。首先，上下文窗口限制：由于处理窗口有限，大语言模型在输出长度方面存在固有的约束[ 13, 14, 15, 16, 17 ]。
尽管包括 GPT-4 和 Claude 3 在内的多种先进大语言模型能够处理超过 10 万个词符的输入，但其输出长度仍限制在不到 8 千个词符以内（GPT-4 的输出长度为 8 千，Claude 3 的输出长度为 4 千）。撰写一份全面的文献综述通常需要阅读数百篇论文，所需的输入规模远远超出了最先进模型的处理能力。此外，一份高质量的文献综述本身也包含数万个词符的内容，因此直接利用大语言模型生成如此庞大的内容是非常具有挑战性的。
其次，参数化知识限制：仅依赖大语言模型内部的知识，不足以生成需要全面且准确的参考文献的文献综述[18, 19, 20]。大语言模型可能会基于错误甚至不存在的“幻觉”参考文献生成内容。此外，这些模型无法纳入训练数据中未包含的最新研究，从而限制了其生成的文献综述的广度和深度。第三，缺乏评估基准：在生成完成后，缺乏用于评估大语言模型输出质量的可靠指标。
依赖人工审核进行质量评估不仅资源消耗巨大，还缺乏可扩展性[ 21, 22, 23 ]。这成为大语言模型在学术综合领域广泛应用的重大障碍，因为准确性和可靠性方面的严格标准至关重要。


<details>
<summary>英文原文</summary>

The advent of LLMs [ 7 , 9 ] presents a promising avenue for addressing these challenges. These models, trained on extensive text corpora, demonstrate remarkable capabilities in understanding and generating human-like text, even in long-context scenarios [ 10 , 11 , 12 ] . Despite these advancements, the practical application of LLMs to survey generation is fraught with challenges. Firstly, context window limitations : LLMs encounter inherent restrictions in output length due to limited processing windows [ 13 , 14 , 15 , 16 , 17 ] . While several advanced large models, including GPT-4 and Claude 3, support inputs exceeding 100k tokens, their output is still limited to fewer than 8k tokens (the output length of GPT-4 is 8k, and the output length of Claude 3 is 4k). Writing a comprehensive survey typically requires reading hundreds of papers, resulting in input sizes far beyond the capacity of even the most advanced models. Moreover, a well-written survey itself spans tens of thousands of tokens, making it highly challenging to generate such extensive content directly with large models.
Secondly, parametric knowledge constraints : Sole reliance on an LLM’s internal knowledge is insufficient for producing surveys that require comprehensive and accurate references [ 18 , 19 , 20 ] . LLMs may generate content based on inaccuracies or even non-existent “hallucinated” references. Moreover, these models cannot incorporate the latest studies not included in their training data, which limits the breadth and depth of the surveys they generate. Thirdly, the lack of evaluation benchmark: after production, reliable metrics to evaluate the quality of outputs from LLMs are lacking. Relying on human review for quality assessment is not only resource-intensive but also lacks scalability [ 21 , 22 , 23 ] . This presents a significant obstacle to the widespread adoption of LLMs for academic synthesis, where rigorous standards of accuracy and reliability are paramount.

</details>

为应对这些挑战，我们提出了 AutoSurvey：一种高效且结构清晰的文献综述方法。具体而言，AutoSurvey 的主要创新包括：逻辑性并行生成——AutoSurvey 采用两阶段生成方式，能够高效并行生成调查内容。首先，多个大语言模型同时工作以生成详细大纲；随后，从这些独立大纲中合成出最终的综合大纲，为内容开发提供明确的框架。之后，根据该大纲并行生成调查的每个子部分，从而显著加快了整个流程。
为克服分段生成阶段带来的潜在过渡与一致性问题，AutoSurvey 整合了系统化的修订阶段。在初始并行生成之后，每个部分都会经过全面修订与润色，从而确保流畅的过渡与更高的文档整体一致性。随后，各部分会被无缝合并，形成结构紧凑、条理清晰的最终文档。实时知识更新：AutoSurvey 采用检索增强生成（RAG）方法实现了实时知识更新机制[ 24, 25, 26 ]。该功能确保文献综述的每一个方面都反映最新的研究成果。
当用户输入文献综述主题时，AutoSurvey 利用 RAG 系统检索最新的相关论文，从而生成结构清晰且内容详实的大纲。在撰写子章节时，系统会动态引入与当前内容相关的新研究文章。这种方式能够确保引用信息保持最新，并使文献综述内容与该领域的最新进展保持一致，从而显著提升文献综述的准确性和深度。多大语言模型作为评判器评估：AutoSurvey 采用多大语言模型作为评判器的策略，利用大语言模型作为评判器的方法进行文本评估[ 22, 21, 23 ]。
该方法利用多个大语言模型生成初始评估指标，这些模型会处理大量高质量文献综述数据。随后由人类专家对这些指标进行优化，以确保其精确性并符合学术标准。Multi-LLM-as-Judge方法从两个主要维度对生成内容进行评估：(1) 引用质量，即验证所呈现信息的准确性与可靠性，包含召回率和精确度两个子指标；(2) 内容质量，包括覆盖度（评估主题涵盖范围）、结构（评价逻辑组织与连贯性）以及相关性（确保与主题核心一致）。
通过利用多个大语言模型，该策略能够减少偏见，确保评估的均衡与全面，同时坚守严格的学术标准。


<details>
<summary>英文原文</summary>

In response to these challenges, we introduce AutoSurvey: a speedy and well-organized methodology for conducting comprehensive literature surveys. Specifically, AutoSurvey’s primary innovations include: logical parallel generation : AutoSurvey employs a two-stage generation approach to parallelly generate survey content efficiently. Initially, multiple LLMs work concurrently to create detailed outlines. A final, comprehensive outline is then synthesized from these individual outlines, setting a clear framework for content development. Subsequently, each subsection of the survey is generated in parallel and guided by the outline, which significantly accelerates the process. To overcome potential transition and consistency issues due to segmented generation phases, AutoSurvey integrates a systematic revision phase. After the initial parallel generation, each section undergoes thorough revision and polishing, ensuring smooth transitions and enhanced overall document consistency. The sections are then seamlessly merged to produce a cohesive and well-organized final document. Real-time knowledge update : AutoSurvey incorporates a Real-time Knowledge Update mechanism using a Retrieval-Augmented Generation (RAG) approach [ 24 , 25 , 26 ] . This feature ensures that every aspect of the survey reflects the most current studies. When a survey topic is input by the user, AutoSurvey leverages the RAG system to retrieve the latest relevant papers, forming the basis for generating a structured and informed outline. During subsection writing, the system dynamically pulls in new research articles relevant to the specific content under development. This approach ensures that citations are current and the survey content is aligned with the latest developments in the field, significantly enhancing the accuracy and depth of the literature review. Muti-LLM-as-judge evaluation : AutoSurvey employs the Multi-LLM-as-Judge strategy, leveraging the LLM-as-Judge method for text evaluation [ 22 , 21 , 23 ] . This approach generates initial evaluation metrics using multiple large language models, which process a substantial corpus of high-quality surveys. These metrics are refined by human experts to ensure precision and adherence to academic standards. The Multi-LLM-as-Judge method assesses generated content across two main dimensions: (1) Citation Quality, verifying the accuracy and reliability of the information presented, with sub-indicators for Recall and Precision. (2) Content Quality, consisting of Coverage (assessing the extent of topic encapsulation), Structure (evaluating logical organization and coherence), and Relevance (ensuring alignment with the main topic). By utilizing multiple LLMs, this strategy minimizes bias and ensures a balanced and comprehensive assessment, upholding rigorous academic standards.

</details>

不同文献综述长度（8k、16k、32k 和 64k 个词元）下的大量实验结果表明，AutoSurvey 始终能够获得较高的引用量和内容质量得分。在 64k 个词元时，AutoSurvey 的引用质量达到 82.25% 的召回率与 77.41% 的精确率，优于简单的基于 RAG 的大语言模型（分别为 68.79% 和 61.97%），并接近人类表现水平（分别为 86.33% 和 77.78%）。在内容质量方面，64k 个词元时 AutoSurvey 的覆盖度得分为 4.73，结构得分为 4.33，相关性得分为 4.86，与人类表现水平（分别为 5.00、4.66 和 5.00）非常接近。
在较短长度（8k、16k和32k令牌）下，AutoSurvey在所有指标上仍保持出色的性能。此外，Spearman的rho值表明大语言模型给出的排名与人类专家给出的排名之间存在中等程度的正相关性。混合模型组合达到了最高的相关性为0.5429，说明其与人类偏好高度一致。这些结果进一步证明了我们的多大语言模型评分机制的有效性，为不同长度的文献综述提供了可靠的判断依据。


<details>
<summary>英文原文</summary>

Extensive experimental results across different survey lengths (8k, 16k, 32k, and 64k tokens) demonstrate that AutoSurvey consistently achieves high citation and content quality scores. At 64k tokens, AutoSurvey achieves 82.25% recall and 77.41% precision in citation quality, outperforming naive RAG-based LLMs (68.79% recall and 61.97% precision) and approaching human performance (86.33% recall and 77.78% precision). In content quality at 64k tokens, AutoSurvey scores 4.73 in coverage, 4.33 in structure, and 4.86 in relevance, closely aligning with human performance (5.00, 4.66, and 5.00 respectively). At shorter lengths (8k, 16k, and 32k tokens), AutoSurvey also maintains strong performance across all metrics. Furthermore, the Spearman’s rho values indicate a moderate positive correlation between the rankings provided by the LLMs and those given by human experts. The mixture of models achieves the highest correlation at 0.5429, indicating a strong alignment with human preferences. These results reinforce the effectiveness of our multi-LLM scoring mechanism, providing a reliable proxy for human judgment across varying survey lengths.

</details>

综上所述，据我们所知，AutoSurvey是首个探索大语言模型智能体在撰写长篇学术文献综述中的潜力的系统。它提出了与人类偏好相一致的文献综述评估标准，为未来的相关研究提供了宝贵的参考依据。


<details>
<summary>英文原文</summary>

In conclusion, to the best of our knowledge, AutoSurvey is the first system to explore the potential of large model agents in writing extensive academic surveys. It proposes evaluation criteria for surveys that align with human preferences, providing a valuable reference for future related research.

</details>

## 2 方法论


<details>
<summary>英文原文</summary>

2 Methodology

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0177)

图2：用于生成全面调查的大语言模型自动调查流程。


<details>
<summary>英文原文</summary>

Figure 2 : The AutoSurvey Pipeline for Generating Comprehensive Surveys.

</details>

在本节中，我们介绍了 AutoSurvey 用于自动化生成全面文献综述的方法论。我们的方法通过四个不同的阶段逐步推进——初始检索与大纲生成、子章节撰写、整合与优化，以及严格评估与迭代。每个阶段都经过精心设计，旨在解决与文献综述创建相关的特定问题，从而提升最终文献综述文档的效率和质量。AutoSurvey 的伪代码可参见算法1。


<details>
<summary>英文原文</summary>

In this section, we describe the methodology employed by AutoSurvey to automate the creation of comprehensive literature surveys. Our approach systematically progresses through four distinct phases—Initial Retrieval and Outline Generation, Subsection Drafting, Integration and Refinement, and Rigorous Evaluation and Iteration. Each phase is meticulously designed to address specific challenges associated with survey creation, thereby enhancing the efficiency and quality of the resulting survey document. The pseudo code of AutoSurvey can be found at Algorithm 1 .

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0179)

算法1 AutoSurvey：利用大语言模型进行自动化调查创建。


<details>
<summary>英文原文</summary>

Algorithm 1 AutoSurvey : Automated Survey Creation Using LLMs.

</details>

### 初始检索与大纲生成


<details>
<summary>英文原文</summary>

Initial Retrieval and Outline Generation

</details>

该过程从初始检索与大纲生成阶段开始。通过基于嵌入的检索技术，AutoSurvey 扫描出版物数据库，找出与指定文献综述主题 $T$ 最相关的论文。这一阶段对于确保文献综述基于最相关且最新的研究至关重要。随后，检索到的出版物 $P_{\text{init}}$ 被用于生成结构化大纲 $O$，以全面覆盖主题，并在逻辑上组织综述。为给各小节的写作提供更详细的指导，大纲不仅包含各小节的标题，还包含简短描述。这些描述传达各小节的核心思想，有助于明确整篇综述的内容与方向。由于此阶段检索到的相关论文很多，$P_{\text{init}}$ 的总长度往往超过大语言模型的上下文窗口。为应对这一问题，论文按上下文窗口大小随机划分，用于生成多个大纲；模型再将这些大纲整合为最终的综合大纲。最后，整篇综述的大纲 $O$ 表示为 $O=\text{Outline}(T,P_{\text{init}}).$


<details>
<summary>英文原文</summary>

The process begins with the Initial Retrieval and Outline Generation phase. Utilizing an embedding-based retrieval technique, AutoSurvey scans a database of publications to identify papers most pertinent to the specified survey topic $T$ . This phase is crucial for ensuring that the survey is grounded in the most relevant and recent research. The retrieved publications $P_{\text{init}}$ are then used to generate a structured outline $O$ , which ensures comprehensive coverage of the topic and logical structuring of the survey. To provide more detailed guidance for writing subsections, the outline generation includes not only titles for each subsection but also brief descriptions. These descriptions convey the main idea of each subsection, aiding in the overall clarity and direction of the survey. Given the extensive amount of relevant papers extracted during this stage, the total length of $P_{\text{init}}$ often exceeds the context window size of the LLM. To address this, papers are randomly divided according to the LLM’s context window size, resulting in the creation of multiple outlines. The model then consolidates these outlines to form the final comprehensive outline. Finally, the outline $O$ of the entire survey is represented as $O=\text{Outline}(T,P_{\text{init}}).$

</details>

### 小节 起草


<details>
<summary>英文原文</summary>

Subsection Drafting

</details>

有了结构化大纲之后，进入小节撰写阶段。专门的大语言模型并行撰写大纲中的各个部分。这既加快了撰写过程，也使各节内容具体而集中，并遵循大纲设定的主题边界。撰写每个小节时，使用该小节的子大纲 $O_{i}$ 检索必要的相关参考论文 $P_{\text{sec}}$，以提供更贴合小节核心思想的信息。写作过程中，模型需要引用所提供的参考论文来支持生成的内容。生成内容中的参考文献会被提取并映射到对应的 arXiv 论文（详见附录 B）。第 $i_{th}$ 个小节 $S_{i}$ 可表示为：$S_{i}=\text{Draft}(O_{i},P_{\text{sec}}).$


<details>
<summary>英文原文</summary>

With the structured outline in place, the Subsection Drafting phase commences. During this phase, specialized LLMs draft each section of the outline in parallel. This method not only accelerates the drafting process but also ensures detailed and focused content generation for each survey section, adhering to the thematic boundaries established by the outline. When writing the content of each subsection, the sub-outline $O_{i}$ of that subsection will be used to retrieve the necessary relevant reference papers $P_{\text{sec}}$ to provide information that aligns more closely with the main idea of the subsection. During the writing process, the model is required to cite the provided reference papers to support the generated content. The references in the generated content will be extracted and mapped to the corresponding arXiv papers (see Appendix B for details). The $i_{th}$ subsection $S_{i}$ can be expressed as: $S_{i}=\text{Draft}(O_{i},P_{\text{sec}}).$

</details>

### 整合与优化


<details>
<summary>英文原文</summary>

Integration and Refinement

</details>

撰写阶段结束后，分别优化每个小节 $S_{i}$，以提高可读性、消除冗余并确保叙述连贯。优化后的小节 $R_{i}$ 随后合并为一份完整文档 $F$，这对于保持整篇综述的逻辑性和连贯性至关重要。优化过程中，模型根据局部上下文（考虑前后小节）润色每个小节，以改善可读性、消除冗余并增强连贯性。此外，模型还需检查内容中参考文献引用的正确性，并纠正引用错误。该过程表示为：$F=\text{Merge}(R_{1},R_{2},\ldots,R_{n}),\text{where}\ R_{i}=\text{Refine}(S_{i}).$


<details>
<summary>英文原文</summary>

Following the drafting phase, each section $S_{i}$ is individually refined to enhance readability, eliminate redundancies, and ensure a seamless narrative. The refined sections $R_{i}$ are then merged into a cohesive document $F$ , which is essential for maintaining a logical flow and coherence throughout the survey. During the refinement process, the model needs to polish each subsection based on the local context (considering the previous and following subsections) to improve readability, eliminate redundancies, and enhance coherency. Additionally, the model is required to check the correctness of the cited references in the content and correct any errors in the citations. This procedure can be represented by: $F=\text{Merge}(R_{1},R_{2},\ldots,R_{n}),\text{where}\ R_{i}=\text{Refine}(S_{i}).$

</details>

### 严格的评估与迭代


<details>
<summary>英文原文</summary>

Rigorous Evaluation and Iteration

</details>

最后阶段包含严格的评估与迭代过程，其中通过多大语言模型作为评判者的策略对文献综述进行评估。该评估从多个方面对文献综述进行严格审查。从此次评估中获得的见解用于指导进一步的优化，确保文献综述符合最高学术标准。在 $N$ 候选作品中选出最佳文献综述。AutoSurvey 的最终输出为 $F_{\text{best}}=\text{Evaluate}(\{F_{1},F_{2},\ldots,F_{N}\}).$


<details>
<summary>英文原文</summary>

The final phase involves a rigorous evaluation and iteration process, where the survey document is assessed through a Multi-LLM-as-Judge strategy. This evaluation critically examines the survey in several aspects. The insights gained from this evaluation are used to guide further refinements, ensuring the survey meets the highest academic standards. The best survey is chosen from $N$ candidates. The final output of AutoSurvey is $F_{\text{best}}=\text{Evaluate}(\{F_{1},F_{2},\ldots,F_{N}\}).$

</details>

此处所阐述的方法论——从初始数据检索到复杂的多维度评估——确保 AutoSurvey 能够利用先进的大语言模型技术，有效应对不断发展的研究领域中文献综述创作的复杂性问题。


<details>
<summary>英文原文</summary>

The methodology outlined here—from initial data retrieval to sophisticated multi-faceted evaluation—ensures that AutoSurvey effectively addresses the complexities of survey creation in evolving research fields using advanced LLM technologies.

</details>

## 3 个实验


<details>
<summary>英文原文</summary>

3 Experiments

</details>

### 设置


<details>
<summary>英文原文</summary>

Setup

</details>

我们进行了全面的实验，以评估 AutoSurvey 的性能，并将其与用于撰写文献综述的传统方法进行对比。在 AutoSurvey 的撰写阶段，我们使用了 Claude-3-Haiku，该模型以速度快且成本效益高著称，能够处理 200K 个令牌的数据。在评估过程中，我们结合了 GPT-4、Claude-3-Haiku 和 Gemini-1.5-Pro 三种工具。具体使用的模型包括 gpt-4-0125-preview、claude-3-haiku-20240307 以及 Gemini-1.5-pro-preview。评估涵盖了以下关键性能指标：


<details>
<summary>英文原文</summary>

We conduct comprehensive experiments to evaluate the performance of AutoSurvey, comparing it against traditional methods for generating survey papers. For the drafting phase of AutoSurvey, we utilize Claude-3-Haiku, known for its speed and cost-effectiveness, capable of handling 200K tokens. For evaluations, we employ a combination of GPT-4, Claude-3-Haiku, and Gemini-1.5-Pro 1 1 1 Specifically, we use gpt-4-0125-preview, claude-3-haiku-20240307 and Gemini-1.5-pro-preview. . The evaluation covers the following key performance metrics:

</details>

•


<details>
<summary>英文原文</summary>

•

</details>

综述生成速度：为估计人类撰写一篇文档所需的时间，我们使用包含以下参数的数学模型：$L$ 为文档长度，$E$ 为专家人数，$M$ 为每位专家的写作速度，$T_{r}$ 为研究与数据收集的准备时间，$T_{w}$ 为实际写作时间，其中 $T_{w}=\frac{L}{E\times M}$；$T_{e}$ 为编辑与修改时间，其中 $T_{e}=\frac{1}{2}T_{w}$。假设理想情况下 $E=10$（10 名专家）、$M=2000$ token/小时、$T_{r}=5$ 小时，且 $T_{e}=\frac{1}{2}T_{w}$，则总时间 $Time$ 计算如下：


<details>
<summary>英文原文</summary>

Survey Creation Speed : To estimate the time it takes for humans to write a document, we use a mathematical model with the following parameters: $L$ (the length of the document), $E$ (the number of experts), $M$ (the writing speed of each expert), $T_{r}$ (the preparation time for research and data collection), $T_{w}$ (the actual writing time, $T_{w}=\frac{L}{E\times M}$ ), and $T_{e}$ (the editing and revision time, $T_{e}=\frac{1}{2}T_{w}$ ). Assuming an ideal situation where $E=10$ , $M=2000$ tokens/hour, $T_{r}=5$ hours, and $T_{e}=\frac{1}{2}T_{w}$ , the total time $Time$ is calculated as:

</details>

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


<details>
<summary>英文原文</summary>

| $Time=T_{r}+T_{w}+T_{e}=T_{r}+\frac{L}{E\times M}+\frac{1}{2}\times\frac{L}{E\times M}.$ | | (1)

</details>

对于基于 RAG 的大语言模型生成和 AutoSurvey 功能，我们会统计所有 API 调用的时间。速度以 $Speed=\frac{1}{Time(\text{hours})}$ 为单位进行计算。


<details>
<summary>英文原文</summary>

For naive RAG-based LLM generation and AutoSurvey, we count all the time of API calls. The speed is calculated as $Speed=\frac{1}{Time(\text{hours})}$ .

</details>

•


<details>
<summary>英文原文</summary>

•

</details>

引用质量：借鉴文献 [27]，该指标评估综述中引用的准确性与相关性。假设从综述中提取出的主张集合为 $C=\{c_{1},c_{2},\ldots\}$，该指标利用自然语言推断（NLI）模型 $h$，判断主张 $c_{i}$ 是否受到其参考文献 $\text{Ref}_{i}=\{r_{i_{1}},r_{i_{2}},\ldots\}$ 的支持，其中每个 $r_{i_{k}}$ 代表一篇被引用的论文。$h(c_{i},\text{Ref}_{i})=1$ 表示参考文献支持该主张，否则为 $h(c_{i},\text{Ref}_{i})=0$。详见附录 C。引用质量包含两个子指标：


<details>
<summary>英文原文</summary>

Citation Quality : Adopted from [ 27 ] , this metric assesses the accuracy and relevance of citations in the survey. Assuming a set of claims $C=\{c_{1},c_{2},\ldots\}$ extracted from the survey, the metric utilizes an NLI model $h$ to decide whether a claim $c_{i}$ is supported by its references $\text{Ref}_{i}=\{r_{i_{1}},r_{i_{2}},\ldots\}$ , where each $r_{i_{k}}$ represents one paper cited. $h(c_{i},\text{Ref}_{i})=1$ means that the references can support the claim, and $h(c_{i},\text{Ref}_{i})=0$ otherwise. Refer to Appendix C for more details. Citation quality encompasses two sub-metrics:

</details>

–


<details>
<summary>英文原文</summary>

–

</details>

引用回忆度：用于衡量生成文本中的所有陈述是否均得到所引用的段落充分支持，其计算方式为


<details>
<summary>英文原文</summary>

Citation Recall : Measures whether all statements in the generated text are fully supported by the cited passages, which is calculated as

</details>

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


<details>
<summary>英文原文</summary>

| $\text{Recall}=\frac{\sum_{i=1}^{|C|}h(c_{i},\text{Ref}_{i})}{|C|}.$ | | (2)

</details>

–


<details>
<summary>英文原文</summary>

–

</details>

引用精确率：识别无关引用，确保给出的引用与论述相关，并直接支持相应主张。在给出精确率公式之前，先定义函数 $g$：$g(c_{i},r_{i_{k}})=(h(c_{i},\{r_{i_{k}}\})=1)\cup(h(c_{i},\text{Ref}_{i}\setminus\{r_{i_{k}}\})=0)$，用于衡量论文 $r_{i_{k}}$ 是否与主张 $c_{i}$ 相关。精确率为：


<details>
<summary>英文原文</summary>

Citation Precision : Identifies irrelevant citations, ensuring that the provided citations are pertinent and directly support the statements. Before listing the formula for precision, a function $g$ is defined as $g(c_{i},r_{i_{k}})=(h(c_{i},\{r_{i_{k}}\})=1)\cup(h(c_{i},\text{Ref}_{i}\setminus\{r_{i_{k}}\})=0)$ , which measures whether the paper $r_{i_{k}}$ is related to the claim $c_{i}$ . The precision is

</details>

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


<details>
<summary>英文原文</summary>

| $\text{Precision}=\frac{\sum_{i=1}^{|C|}\sum_{k=1}^{|\text{Ref}_{i}|}h(c_{i},\text{Ref}_{i})\cap g(c_{i},r_{i_{k}})}{\sum_{i=1}^{|C|}|\text{Ref}_{i}|}.$ | | (3)

</details>

•


<details>
<summary>英文原文</summary>

•

</details>

内容质量：这是一个用于评估文献综述质量的综合指标，包含三个子指标。每个子指标由大语言模型根据5分制评分标准进行评判，该标准由人类专家调整以符合学术要求。请注意，详细的评分标准详见表1。


<details>
<summary>英文原文</summary>

Content Quality : An overarching metric evaluating the excellence of the written survey, encompassing three sub-indicators. Each sub-indicator is judged by LLMs according to a 5-point rubric, calibrated by human experts to meet academic standards. Note that the detailed scoring criteria are provided in Table 1 .

</details>

–


<details>
<summary>英文原文</summary>

–

</details>

覆盖度：评估该调查在多大程度上涵盖了该主题的所有方面。


<details>
<summary>英文原文</summary>

Coverage : Assesses the extent to which the survey encapsulates all aspects of the topic.

</details>

–


<details>
<summary>英文原文</summary>

–

</details>

结构：评估各部分的逻辑组织与连贯性。


<details>
<summary>英文原文</summary>

Structure : Evaluates the logical organization and coherence of each section.

</details>

–


<details>
<summary>英文原文</summary>

–

</details>

相关性：衡量内容与研究主题的契合程度。


<details>
<summary>英文原文</summary>

Relevance : Measures how well the content aligns with the research topic.

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0213)

表1：内容质量标准。


<details>
<summary>英文原文</summary>

Table 1 : Content Quality Criteria.

</details>

### 基线模型


<details>
<summary>英文原文</summary>

Baselines

</details>

我们将 AutoSurvey 与由人类专家撰写的文献综述（从 Arxiv 中收集）以及基于简单 RAG 的大语言模型在 20 个不同的计算机科学主题以及 LLM 领域的 20 个不同主题上进行了比较（见表 6）。对于基于简单 RAG 的大语言模型，我们首先设定标题和文献综述长度要求，然后逐步引导模型撰写内容直至完成。需要注意的是，我们为该模型提供的参考文献数量与 AutoSurvey 相同。


<details>
<summary>英文原文</summary>

We compare AutoSurvey with surveys authored by human experts (collected from Arxiv) and naive RAG-based LLMs across 20 different computer science topics across 20 different topics in the field of LLMs (see Table 6 ). For the naive RAG-based LLMs, we begin with a title and a survey length requirement, then iteratively prompt the model to write the content until completion. Note that we also provide the model with the same number of reference papers with AutoSurvey.

</details>

对于 AutoSurvey 项目，我们使用来自 arXiv 的 530,000 篇计算机科学论文语料库作为检索数据库。在初步撰写阶段，我们检索与给定主题相关的 1200 篇论文，并以 30,000 个词元为窗口大小将其划分为多个部分。此时，模型为每个部分生成一份大纲，并仅基于论文摘要将这些大纲合并成最终的综合大纲。该大纲预先设定了 8 个章节数量。在子章节的撰写过程中，模型根据大纲以及基于子章节描述检索到的 60 篇论文，重点针对每篇论文的主体部分（前 1,500 个词元）生成具体的子章节。
在反思与优化阶段，会向该模型提供相同的参考论文，以确保一致性和准确性。迭代次数 N 设定为 2。请注意，用于评估的人类写作文献在检索过程中会被排除在外。有关实现细节的更多信息，请参见附录 B，提示词则放在附录 F 中。


<details>
<summary>英文原文</summary>

For AutoSurvey, we utilize a corpus of 530,000 computer science papers from arXiv as the retrieval database. During the initial drafting stage, we retrieve 1200 papers relevant to the given topic and split them into several chunks with a window size of 30,000 tokens. The model generates an outline for each chunk and merges these outlines into a final comprehensive outline, using only the abstracts of the papers at this stage. The outline predetermines the number of sections as 8. For subsection drafting, the models generate specific sections using the outline and 60 papers retrieved based on the subsection descriptions, focusing on the main body of each paper (up to the first 1,500 tokens). During the reflection and polishing stage, the same reference papers are provided to the model to ensure consistency and accuracy. The iteration number N is set to 2. Note that human writing surveys used for evaluation are excluded during the retrieval process. For more details of implementations, see Appendix B , and the prompts are presented in Appendix F .

</details>

### 主要结果


<details>
<summary>英文原文</summary>

Main Results

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0219)

表2：基于简单RAG的大语言模型生成、人工写作与自动文献综述的结果。注意，自动文献综述及基于简单RAG的大语言模型生成均使用Claude-haiku作为写作者。另外，用于评估的人工写作文献综述在检索过程中被排除在外。


<details>
<summary>英文原文</summary>

Table 2 : Results of naive RAG-based LLM generation, Human writing and AutoSurvey. Note that AutoSurvey and naive RAG-based LLM generation both use Claude-haiku as the writer. Note that human writing surveys used for evaluation are excluded during the retrieval process.

</details>

我们关于人类写作、基于简单 RAG 的大语言模型生成以及 AutoSurvey 在生成学术文献综述方面的实验结果总结在表 2 中。主要发现包括：


<details>
<summary>英文原文</summary>

The results of our experiments comparing human writing, naive RAG-based LLM generation, and AutoSurvey for generating academic surveys are summarized in Table 2 . The key findings are:

</details>

•


<details>
<summary>英文原文</summary>

•

</details>

在速度方面，AutoSurvey 明显优于人类写作和基于 RAG 的大语言模型生成方式。例如，对于包含 64k 个令牌的文献综述，AutoSurvey 每小时可完成 73.59 篇文献综述，而人类写作仅能完成 0.07 篇，基于 RAG 的大语言模型生成则只能完成 12.56 篇，这凸显了长上下文生成在速度上存在的巨大差距。


<details>
<summary>英文原文</summary>

AutoSurvey significantly outperforms both human writing and naive RAG-based LLM generation in terms of speed. For instance, AutoSurvey achieves a speed of 73.59 surveys per hour for a 64k-token survey, compared to 0.07 for human writing and 12.56 for naive RAG-based LLM generation, highlighting the larger gap in speed for longer context generation.

</details>

•


<details>
<summary>英文原文</summary>

•

</details>

与简单的基于 RAG 的大语言模型生成方式相比，AutoSurvey 的引用质量更高，其表现接近人类写作水平。对于包含 8k 个token的文献综述，AutoSurvey 的引用召回率和精确率分别达到 82.48 和 77.42，优于基于 RAG 的简单大语言模型生成方式（分别为 78.14 和 71.92）。虽然人类写作的表现最优，但我们的结果在不同长度的研究中也接近人类水平。


<details>
<summary>英文原文</summary>

AutoSurvey demonstrates superior citation quality compared to naive RAG-based LLM generation, with performance close to human writing. For an 8k-token survey, AutoSurvey achieves citation recall and precision scores of 82.48 and 77.42, respectively, surpassing naive RAG-based LLM generation (78.14 recall, 71.92 precision). While human writing achieves the best performance, ours is close to human’s across different lengths.

</details>

•


<details>
<summary>英文原文</summary>

•

</details>

AutoSurvey在内容质量方面表现卓越，在16k个标记的文献综述中平均得分为4.60。其在覆盖广度上达到4.66，结构完整性达到4.33，相关性达到4.86，既符合人类写作水平，也优于基于RAG的大语言模型生成结果。


<details>
<summary>英文原文</summary>

AutoSurvey excels in content quality, scoring 4.60 on average for a 16k-token survey. It achieves 4.66 for coverage, 4.33 for structure, and 4.86 for relevance, matching human writing and surpassing naive RAG-based LLM generation.

</details>

实验表明，AutoSurvey在质量与效率之间实现了平衡优化。它能够在显著降低时间成本的前提下，达到接近人类水平的覆盖度、相关性和引用质量。虽然人类写作在结构及整体质量上仍具有优势，但AutoSurvey的效率和性能使其成为生成学术文献综述的有力替代方案。尽管基于RAG的通用大语言模型效果不错，但在多个关键方面仍不如人类写作和AutoSurvey，因此作为三种方法之一，其在生成高质量学术文献综述时最不受青睐，尤其是在大纲缺失的情况下，其结构表现也较差。


<details>
<summary>英文原文</summary>

The experiments indicate that AutoSurvey provides a balanced trade-off between quality and efficiency. It achieves near-human levels of coverage, relevance, and citation quality while maintaining a significantly lower time cost. While human writing still leads in structure and overall quality, the efficiency and performance of AutoSurvey make it a compelling alternative for generating academic surveys. Naive RAG-based LLM, though effective, falls short in several key areas compared to both human writing and AutoSurvey, making it the least preferred method among the three for generating high-quality academic surveys, particularly in terms of structure, due to the lack of outline.

</details>

### Meta评估


<details>
<summary>英文原文</summary>

Meta Evaluation

</details>

为了验证我们的评估方法与人工评估的一致性，我们开展了包含人类专家与自动化评估系统的元评估实验。人类专家对生成的文献综述对进行评判，以判断哪一份更为优秀。这一过程被称为“哪一份更好”测试，是评估的黄金标准。我们将我们的评估方法所做出的判断与人类专家的判断进行了对比。具体而言，我们向专家提供了与我们评估中相同的评分标准作为参考。
专家对生成的20篇文献综述进行了排序，我们利用斯皮尔曼等级相关系数将这些排序与大语言模型生成的排序进行比较，以衡量人类评估与大语言模型评估之间的一致性。


<details>
<summary>英文原文</summary>

To verify the consistency between our evaluation method and human evaluation, we conduct a meta-evaluation involving human experts and our automated evaluation system. Human experts judge pairs of generated surveys to determine which one is superior. This process, referred to as a "which one is better" game, serves as the golden standard for evaluation. We compare the judgments made by our evaluation method against those made by human experts. Specifically, we provide the experts with the same scoring criteria used in our evaluation for reference. The experts rank the generated 20 surveys, and we compare these rankings with those generated by LLM using Spearman’s rank correlation coefficient to measure consistency between human and LLM evaluations.

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0231)

图3：Spearman rho值反映了大语言模型给出的排名与人类专家排名之间的相关程度。注意，A值超过0.3表示正相关，超过0.5则表示强正相关。


<details>
<summary>英文原文</summary>

Figure 3 : Spearman’s rho values indicating the degree of correlation between rankings given by LLMs and human experts. Note that A value over 0.3 indicates a positive correlation and over 0.5 indicates a strong positive correlation.

</details>

本次元评估的结果显示在图3中。表格中展示了斯皮尔曼rho值，用于反映各大语言模型给出的排名与人类专家给出的排名之间的相关程度。斯皮尔曼rho值表明，大语言模型提供的排名与人类专家给出的排名之间存在中等程度的正相关关系，其中混合模型所呈现的相关性最高，为0.5429。这些结果表明，我们的评估方法与人类偏好高度一致，能够作为人类判断的可靠替代指标。


<details>
<summary>英文原文</summary>

The results of this meta-evaluation are presented in Figure 3 . The table shows the Spearman’s rho values, indicating the degree of correlation between the rankings given by each LLM and the human experts. The Spearman’s rho values indicate a moderate positive correlation between the rankings provided by the LLMs and those given by the human experts, with the mixture of models achieving the highest correlation at 0.5429. These results suggest that our evaluation method aligns well with human preferences, providing a reliable proxy for human judgment.

</details>

### 剔除研究


<details>
<summary>英文原文</summary>

Ablation study

</details>

为了评估不同组件对 AutoSurvey 性能的影响，我们进行了消融研究，系统地删除了关键组件：检索机制、反射阶段以及迭代次数。此外，我们还评估了使用不同基础大语言模型的影响，以证明即使使用像 Claude-haiku 这样性能稍差的模型，AutoSurvey 的性能仍与人工生成的文献综述相当。


<details>
<summary>英文原文</summary>

To assess the impact of various components on the performance of AutoSurvey, we conduct an ablation study by systematically removing key components: the retrieval mechanism, the reflection phase, and iterations. Additionally, we evaluate the influence of using different base LLMs to demonstrate that even with a less optimal LLM like Claude-haiku, AutoSurvey’s performance remains comparable to human-generated surveys.

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0235)

表3：去除不同组件后的 AutoSurvey 删减研究结果。


<details>
<summary>英文原文</summary>

Table 3 : Ablation study results for AutoSurvey with different components removed.

</details>

表3表明，移除检索机制会显著降低引用质量，这凸显了其在确保准确且相关参考文献方面的重要性。缺乏反思阶段会对整体内容质量产生轻微影响，尤其是在结构和连贯性方面。


<details>
<summary>英文原文</summary>

Table 3 demonstrates that removing the retrieval mechanism significantly degrades citation quality, highlighting its critical role in ensuring accurate and relevant references. The absence of the reflection phase slightly impacts the overall content quality, particularly in structure and coherence.

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0238)

表4：使用不同基础大语言模型撰写者的 AutoSurvey 性能表现。


<details>
<summary>英文原文</summary>

Table 4 : Performance of AutoSurvey with different base LLM writers.

</details>

表4展示了使用不同大语言模型作为基础写作工具时AutoSurvey的表现情况。结果表明，三种大语言模型（GPT-4、Claude-haiku和Gemini-1.5-Pro）都表现良好，其中GPT-4在整体内容质量方面略优于其他模型。重要的是，即便使用性能稍差的Claude-haiku，AutoSurvey的表现仍与人类标准相媲美。


<details>
<summary>英文原文</summary>

Table 4 shows the performance of AutoSurvey when using different LLMs as the base writer. The results indicate that all three LLMs (GPT-4, Claude-haiku, and Gemini-1.5-Pro) perform well, with GPT-4 slightly outperforming the others in terms of overall content quality. Importantly, even with the less optimal Claude-haiku, AutoSurvey’s performance remains competitive with human standards.

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0241)

图4：迭代对AutoSurvey性能的影响。


<details>
<summary>英文原文</summary>

Figure 4 : Impact of Iteration on AutoSurvey Performance.

</details>

图4展示了不同迭代次数对AutoSurvey性能的影响。结果表明，将迭代次数从1增加到5时，整体内容质量会略有提升，但超过第二次迭代后收益便逐渐减少。


<details>
<summary>英文原文</summary>

Figure 4 presents the effect of different iteration counts on the performance of AutoSurvey. The results show that increasing the number of iterations from 1 to 5 leads to a slight improvement in overall content quality, with diminishing returns after the second iteration.

</details>

为了评估所生成的文献综述能否提供有用的信息以丰富知识，我们设计了50道关于5个主题的选择题。这些题目主要涉及与文献相关的知识，例如识别哪篇论文提出了特定方法。我们在以下条件下比较了Claude模型的准确性：(1) 直接选择答案而不提供任何参考材料；(2) 能够访问由基于RAG的LLM生成的32k条文献综述；(3) 能够访问由AutoSurvey生成的32k条文献综述；(4) 可以参考通过选项获取的20篇论文（总计30k个标记）中的内容（上限值，直接检索答案）。


<details>
<summary>英文原文</summary>

To assess whether the generated survey can provide useful information to enrich the knowledge, we created 50 multiple-choice questions about 5 topics. These questions primarily involve knowledge related to literature, such as identifying which paper proposed a particular method. We compared the accuracy of the Claude model under the following conditions: (1) directly chooses the answer without providing any reference materials, (2) has access to a 32k survey generated by naive RAG-based LLMs, (3) has access to a 32k survey generated by AutoSurvey, and (4) can refer to 20 papers (30k tokens in total) retrieved using the options provided (Upper-bound, directly retrieving the answers).

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0244)

表5：不同参考文献下的性能表现。


<details>
<summary>英文原文</summary>

Table 5 : Performances given different references.

</details>

结果见表5，我们发现提供与主题相关的材料可以有效提高回答的准确性。提供与选项相关的文献可视为性能的上限（73.60%）。与直接回答相比，AutoSurvey的准确率提高了9.2%，且比使用基于RAG的大语言模型生成的文献进行调查时高出2.4%。这表明我们的方法能够有效提供主题知识。


<details>
<summary>英文原文</summary>

The results are shown in Table 5 and we find providing topic-related materials can effectively improve the accuracy of answers. Providing option-related papers can be considered an upper bound for performance (73.60%). AutoSurvey improves accuracy by 9.2% compared to directly answering and is 2.4% higher than using naive RAG-based LLM-generated surveys. This demonstrates that our method can effectively provide topic knowledge.

</details>

总结来说，消融实验凸显了检索机制与反思阶段在 AutoSurvey 中的关键作用。此外，使用不同的大语言模型作为基础生成器以及调整迭代次数也会对性能产生影响。尽管如此，AutoSurvey 在不同配置下仍能保持良好的表现，展现了其稳健性和高效性。


<details>
<summary>英文原文</summary>

In summary, the ablation study underscores the critical role of the retrieval mechanism and reflection phase in AutoSurvey. Furthermore, the performance is influenced by using different LLMs as the base writer and varying the iteration count. Nevertheless, AutoSurvey consistently performs well across various configurations, showcasing its robustness and efficiency.

</details>

## 4 相关研究


<details>
<summary>英文原文</summary>

4 Related Work

</details>

### 长文本生成


<details>
<summary>英文原文</summary>

Long-form Text Generation

</details>

大语言模型有效处理与生成长文本的能力是一个关键挑战，因为需要在较长的文本段落中保持连贯性和逻辑性[28, 29, 30, 31]。一些研究尝试通过采用不同的位置编码技术来直接扩展上下文窗口来应对这一挑战[32, 33]。然而，修改位置编码策略需要重新训练模型，这成本较高。另一种解决方案是采用增强式记忆技术。
RecurrentGPT [ 34 ] 通过利用自然语言提示来存储之前的上下文信息，模拟 RNN 的递归机制，从而能够生成任意长度的文本。Temp-Lora [ 35 ] 则通过将上下文信息嵌入到临时 Lora 模块中并在生成过程中逐步更新该模块，而非依赖庞大的上下文窗口，从而实现长文本生成。这些方法有效地建立了令牌之间的关联并保持了上下文理解能力，但仍然存在长生成时间的问题。
为了进一步加速生成过程，人们广泛探索了分层建模技术，以捕捉长文本固有的层次结构特性[ 36, 37 ]。尽管这种方法效率较高，却忽略了文本的长期依赖关系，可能导致内容质量下降[ 38 ]。为克服这些缺陷，AutoSurvey同样采用分层生成范式，通过构建结构清晰的大纲来提供指导，并优化生成内容以提升质量。


<details>
<summary>英文原文</summary>

The ability to effectively process and generate long-form text is a critical challenge for large language models (LLMs) due to the need to maintain coherence and logical flow over extended passages of text [ 28 , 29 , 30 , 31 ] . Several works try to address the challenge by directly extending the context window with different Positional Encoding Techniques [ 32 , 33 ] . However, modifying position encoding strategies requires retraining the model, which is costly. Another solution is using memory-augmented techniques. RecurrentGPT [ 34 ] enables the generation of arbitrarily long texts by simulating the recurrence mechanism of RNNs using natural language prompts to store previous contextual information. Temp-Lora [ 35 ] enables long text generation by embedding context information into a temporary Lora module updated progressively during generation rather than relying on an extensive context window. These methods effectively establish relationships among tokens and maintain contextual understanding, but still face the issue of long generation times. To further accelerate the generation process, Hierarchical Modeling Techniques have been explored extensively to capture the inherent hierarchical nature of long-form text [ 36 , 37 ] . Despite such efficiency, it ignores the long dependency of text and may degrade the content quality [ 38 ] . To tackle the drawbacks, AutoSurvey, similarly using a Hierarchical generation paradigm, creates a well-organized outline for guidance and refines the generated content to improve the quality.

</details>

### 自动写作


<details>
<summary>英文原文</summary>

Automatic Writing

</details>

由于人工写作的高成本，自动化写作近年来吸引了大量研究关注。与主要致力于训练模型生成语言连贯文本的传统方法[39, 40]相比，大语言模型的出现为自动化写作带来了新的可能性，使人们对忠实性、逻辑结构、风格及伦理等更广泛方面给予了更多关注[41, 42, 43, 44]。例如，检索增强生成技术有助于生成带有引用依据的论点[27, 45]。
IRP框架[46]通过迭代执行内容规划、事实检索和改写操作来生成说明性文本，从而确保信息的准确性与风格一致性。许多研究致力于大纲的构建，以优化生成内容的结构。PaperRobot[47]通过逐步编写关键要素来生成论文摘要。STORM[20]则基于多轮wiki页面相关问答过程设计出完善的大纲，从而促进类似wiki的文章生成。这些方法仅在较短文本（<4k）中得到了探索。相比之下，Autosurvey在生成长文本（64k）方面表现出有效性，尤其适用于学术评论场景。


<details>
<summary>英文原文</summary>

Due to the high costs associated with manual writing, automated writing has attracted substantial research interest in recent years. Compared to traditional methods, which primarily focus on training models to generate linguistically coherent text [ 39 , 40 ] , the emergency of large language models (LLMs) has opened up new possibilities for automated writing, drawing more attention to broader aspects like faithfulness, logical structure, style, and ethics [ 41 , 42 , 43 , 44 ] . For example, Retrieval-Augmented Generation techniques are useful for generating claims with citations [ 27 , 45 ] . IRP framework [ 46 ] generates expository text by iteratively performing content planning, fact retrieval, and paraphrasing to ensure factuality and stylistic consistency. Several works focus on the outline creation to improve the structure of generated content. PaperRobot [ 47 ] incrementally writes key elements to generate a paper abstract. STORM [ 20 ] designs a refined outline based on multiple rounds of wiki-page-related Q&A to facilitate wiki-like article generations. These methods have only been explored in shorter texts (<4k). In contrast, Autosurvey shows its effectiveness in generating long content (64k), with a focus on academic reviews.

</details>

## 5 局限性


<details>
<summary>英文原文</summary>

5 Limitation

</details>

除了直接使用召回率和精确率来评估引文外，我们还进行了人工分析，从而能够更全面地了解引文的质量。我们检查了100条无依据的声明及其对应的参考文献，发现这些错误主要属于三类：(1) 不一致；(2) 误解；(3) 过度概括。不一致是指两者之间的关联被错误建立，例如出现无关的引文；误解则发生在声明与来源存在关联，但声明却错误地反映了该来源的信息。
当某个主张将原始材料的结论推广到超出支持范围的更广阔语境时，就会出现过度泛化现象。在三种错误类型中，过度泛化占比最高（51%），表明大语言模型在写作时仍严重依赖其参数化知识。误解占比较小（10%），说明大语言模型在大多数情况下能够理解参考文献的内容，从而避免提出与参考文献严重偏离的主张。


<details>
<summary>英文原文</summary>

In addition to directly using recall and precision to evaluate citations, we also perform a manual analysis, providing a more comprehensive view of the citation quality. We examine 100 unsupported claims and their corresponding references and find that the errors mainly fall into three categories: (1) Misalignment, (2) Misinterpretation, and (3) Overgeneralization. Misalignment occurs when the connection between them is incorrectly made, such as an irrelevant citation. Misinterpretation happens when the claim and source are related, but the claim incorrectly represents the information from the source. Overgeneralization occurs when a claim extends the conclusions of the source material to a broader context than is supported. Among the three types of errors, overgeneralization accounts for the largest proportion (51%), indicating that LLMs still rely heavily on their parametric knowledge for writing. Misinterpretation has a small proportion (10%), suggesting that LLMs are capable of understanding the content of the references in most cases, avoiding the creation of claims that significantly deviate from the references.

</details>

不一致性（39%）：一个例子是，在所引用的文献并未提出 GDPR 的情况下，却引用了“通用数据保护条例（GDPR）”。


<details>
<summary>英文原文</summary>

Misalignment (39%) : An example is citing the "General Data Protection Regulation (GDPR)" in a context where the referenced paper does not propose GDPR but merely mentions it in the content.

</details>

误解（10%）：一个例子是声称“上下文学习使得大语言模型仅通过依赖少量示例即可适应新任务，无需任何参数更新或微调”，该观点基于一篇专注于元上下文学习的文献，且该文献也提到了上下文学习的局限性。


<details>
<summary>英文原文</summary>

Misinterpretation (10%) : An example is claiming that "In-context learning allows LLMs to adapt to new tasks by simply conditioning on a few demonstration examples, without the need for any parameter updates or fine-tuning," based on a paper that focuses on meta-out-of-context learning and mentions the limitations of in-context learning.

</details>

泛化过度（51%）：一个例子是“上下文学习也可以从其他学习范式的进步中受益，例如多任务学习”，该观点基于一篇讨论多任务少样本学习的文献，但并未明确说明其对上下文学习的影响。


<details>
<summary>英文原文</summary>

Overgeneralization (51%) : An example is that "in-context learning can also benefit from advancements in other learning paradigms, such as multi-task learning," based on a paper that discusses multi-task few-shot learning but does not explicitly address its influence on in-context learning.

</details>

在三种错误类型中，过度泛化所占比例最高（51%），表明大语言模型在写作时仍严重依赖其参数化知识。误解所占比例较小（10%），说明大语言模型在大多数情况下能够理解参考文献的内容，不会生成与参考文献严重偏离的论断。关于潜在的额外社会影响及伦理问题，详见附录E。


<details>
<summary>英文原文</summary>

Among the three types of errors, overgeneralization accounts for the largest proportion (51%), indicating that LLMs still rely heavily on their parametric knowledge for writing. Misinterpretation has a small proportion (10%), suggesting that LLMs are capable of understanding the content of the references in most cases, avoiding the creation of claims that significantly deviate from the references. Additional potential societal impact and ethical considerations are discussed in Appendix E .

</details>

## 6 结论


<details>
<summary>英文原文</summary>

6 Conclusion

</details>

在本文中，我们介绍了 AutoSurvey 这一创新方法，该方法利用大语言模型来自动化完成全面的文献综述工作。通过包含初始检索、大纲生成、并行子章节撰写、整合及严格评估等系统性步骤，AutoSurvey 解决了上下文窗口限制和参数化知识约束等关键问题。我们的实验表明，AutoSurvey 显著优于简单的基于 RAG 的大语言模型生成方式，在内容与引用质量方面与人类表现相当，同时效率也极高。
这一进展为合成研究文献提供了可扩展且有效的解决方案，为人工智能等快速发展的领域中的研究人员提供了宝贵的工具。


<details>
<summary>英文原文</summary>

In this paper, we introduce AutoSurvey, a novel methodology leveraging large language models to automate the creation of comprehensive literature surveys. AutoSurvey addresses key challenges such as context window limitations and parametric knowledge constraints through a systematic approach involving initial retrieval, outline generation, parallel subsection drafting, integration, and rigorous evaluation. Our experiments show that AutoSurvey significantly outperforms naive RAG-based LLM generation and matches human performance in content and citation quality, while also being highly efficient. This advancement offers a scalable and effective solution for synthesizing research literature, providing a valuable tool for researchers in rapidly evolving fields like artificial intelligence.

</details>

## 参考文献


<details>
<summary>英文原文</summary>

References

</details>

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


<details>
<summary>英文原文</summary>

Appendix A Detail of Topics and Human-writing Surveys

</details>

我们从大语言模型领域的不同主题中选取了20篇文献综述。在筛选过程中，我们同时考虑了主题的涵盖范围以及这些文献在谷歌学术上的引用次数。这些文献综述的基本信息列于表6中。


<details>
<summary>英文原文</summary>

We select 20 surveys from different topics within the LLM field. During the selection process, we prioritize both the breadth of the topics and the citation count (from google scholar) of the surveys. The basic information of surveys are listed in Table 6 .

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0312)

表6：文献综述表


<details>
<summary>英文原文</summary>

Table 6 : Survey Table

</details>

## 附录 B 实现细节


<details>
<summary>英文原文</summary>

Appendix B Details of Implementations

</details>

我们采用了 nomic-embed-text-v1.5 [ 48 ] 模型，该模型是 RAG 应用中最常用的嵌入模型。为了构建我们的数据库，我们会存储每篇论文的标题和摘要的嵌入向量。由于上下文窗口长度为 8k，比任何单个摘要都要长，因此我们直接对原始文本进行嵌入处理，无需分块。在生成过程中，系统会根据摘要检索相关论文，并根据与查询的相似度对它们进行排序。在生成子章节内容时，模型需要写出需要引用引用的对应论文标题。生成完成后，每个标题会被作为查询进行嵌入，并映射到数据库中最近的论文标题。
这种方法使大语言模型能够利用自身的参数知识生成无参考文献的引文，同时确保这些引文的真实性。在调用 API 时，我们默认设置温度值为 1 及其他参数。即使使用相同的参数，生成的文献综述的最终长度也会有所不同。因此，长度为 8k 到 16k 的论文被归类为 8k 类别，而长度为 16k 到 32k 的论文则被归类为 16k 类别，依此类推。


<details>
<summary>英文原文</summary>

We adopt nomic-embed-text-v1.5 [ 48 ] , a widely used embedding model in RAG applications. To build our database, we store the embeddings of the title and abstract for each paper. Since the context window length is 8k, which is longer than any individual abstract, we embed the raw text directly without chunkings. During generation, related papers are retrieved by the abstract and ranked by their similarity to the query.
When generating subsection content, the model needs to write the corresponding paper titles where citations are required. After generation, each title will be embedded as a query and be mapped to the closest paper title in our database. This approach allows the LLMs to use their own parameter knowledge to generate citations without references while ensuring the existence of the generated citations. When calling API, we set temperature = 1 and other parameters as default.
Even with the same parameters, the final length of the generated surveys can vary. Therefore, papers with lengths from 8k to 16k are classified into the 8k category, those from 16k to 32k into the 16k category, and so on.

</details>

## 附录 C 评估细节


<details>
<summary>英文原文</summary>

Appendix C Details of Evaluation

</details>

在引用质量方面，我们将包含至少一条引用的句子定义为一个主张，并从生成的文献综述中提取所有主张。在人工评估环节，我们邀请了三名博士生参与，他们均具有撰写大语言模型相关文献综述的经验。我们为他们提供了相同的评分标准及具体指标的说明，要求他们依据这些标准进行评分，最终生成的文献综述排名则根据总得分确定。


<details>
<summary>英文原文</summary>

For citation quality, we define a sentence with at least one citation as a claim and extract all the claims from the generated survey. For human evaluations, we invite three PhD students and all of them have experience in writing LLMs-related surveys. We provide them with the same scoring criteria, along with explanations of the specific metrics. They are asked to score based on these criteria, and the final rankings of the generated surveys are determined by the total scores.

</details>

## 附录 D 成本分析


<details>
<summary>英文原文</summary>

Appendix D Cost Analysis

</details>

我们在表7中展示了生成32k个token的文献综述所需的平均标记数，以及使用不同大语言模型的成本。


<details>
<summary>英文原文</summary>

We present the average number of tokens to generate a 32k-tokens survey, along with the cost of using different LLMs in Table 7 .

</details>

[查看原图表（阅读版）](bilingual.html#autosurvey-0320)

表7：AutoSurvey的成本


<details>
<summary>英文原文</summary>

Table 7 : Cost of AutoSurvey

</details>

## 附录 E 社会影响与伦理考量


<details>
<summary>英文原文</summary>

Appendix E Societal Impact and Ethical
Considerations

</details>

通过整合各种专业数据库，我们的方法能够生成不同领域的学术文献综述，从而可能填补现有评论中的空白。然而，由于该方法依赖于大语言模型的性能，因此不可避免地存在引用错误。因此，生成的文献综述内容仅用于参考之用。参与评估过程的所有人员均为自愿参与，并获得了充足的报酬。我们实验中使用的所有数据均来自 arXiv，且允许用于非商业用途。


<details>
<summary>英文原文</summary>

By integrating various specialized databases, our approach can generate academic surveys across different fields, potentially filling the gaps in existing reviews. However, as our method relies on the performance of large models, it inevitably contains citation errors. Therefore, the generated survey content is intended for reference only.
All personnel involved in the evaluation process participated voluntarily and received ample compensation. All data used in our experiment is sourced from arXiv and is allowed for non-commercial use.

</details>

## 附录 F 在 AutoSurvey 中使用的提示词


<details>
<summary>英文原文</summary>

Appendix F Prompt used in AutoSurvey

</details>

⬇ ROUGH_OUTLINE_PROMPT = ’’ ’ 您需要撰写一篇关于 [主题] 的全面学术文献综述。您获得了以下与该主题相关的论文列表：--- [论文列表] --- 您需要根据这些论文起草一个大纲。该大纲应包含标题及多个部分。每个部分后需附有一句简短说明，指出该部分应写什么内容。大纲需具有全面性，并包含 [部分编号] 个部分。请以以下格式返回：<format> 标题：[文献综述标题] 第1部分：[第1部分的名称] 描述1：[第1段文字描述]... 第K部分：[第K部分的名称] 描述K：[第K段文字描述] </format>
大纲：’ ’’ SUBSECTION_OUTLINE_PROMPT = ’’ ’ 你需要撰写一篇关于[主题]的文献综述。你已制定如下大纲：--- [整体大纲] --- 该大纲包含标题及多个部分。每个部分后都附有一句简短说明，用于指出该部分应写的内容。你需要丰富[部分名称]部分的内容。[部分名称]的描述：[部分描述]。你需要根据整体大纲生成包含多个子部分的框架。每个子部分后也附有一句简短说明，用于指出该子部分应写的内容。这些文献提供了参考文献：--- [文献列表] --- 请以<格式>的形式返回大纲。
小节 1：[小节 1 名称] 描述 1：[小节 1 的内容] …… 小节 K：[小节 K 名称] 描述 K：[小节 K 的内容] </format> 仅返回大纲，不提供其他信息： ’ ’’ MERGING_OUTLINE_PROMPT = ’’ ’ 你需要撰写一篇关于 [主题] 的文献综述。下面提供了一些作为候选的大纲列表： --- [大纲列表] --- 每个大纲包含标题及多个部分。每个部分后都附有一句简短的句子，说明该部分应写什么内容。你需要基于这些提供的大纲生成最终大纲，使最终大纲能够全面反映该主题的见解并更加逻辑清晰。
按以下格式返回内容：<format> 标题：[文献综述标题] 第1节：[第1节名称] 描述1：[第1段文字描述]... 第K节：[第K节名称] 描述K：[第K段文字描述] </format> 仅返回最终大纲，不提供其他任何信息： ’ ’’ SUBSECTION_WRITING_PROMPT = ’’ ’ 你需要撰写一篇关于[主题]的全面性文献综述。你已制定如下整体大纲：--- [整体大纲]--- 以下是可供参考的论文列表：--- [论文列表]--- 现在你需要撰写[子章节名称]的内容。该子章节应写什么内容的详细要求见此描述：
--- [DESCRIPTION] --- 请遵循以下要求：1. 该小节建议包含超过 [WORD NUM] 个单词的内容。2. 在撰写基于上述特定论文的句子时，请以 ’ [] ’ 格式引用“paper_title”以支持你的内容。以下是文献综述中引用论文的简要指南：--- 1. 总结研究内容：在总结现有文献时引用来源。2. 使用特定概念或数据：讨论特定理论、模型或数据时提供引用。3. 使用成熟方法：在文献综述中引用所采用方法的创造者。4. 支持论点：引用支持你结论的来源。
以及论据。--- 仅返回您为子章节[ SUBSECTION NAME ]所撰写的超过[ WORD NUM ]字的内容，不要包含其他信息：’’ ’ CITATION_REFLECTION_PROMPT = ’ ’’ 您希望撰写一篇关于[ TOPIC ]的全面文献综述。以下是用于引用的论文列表：--- [ PAPER LIST ] --- 您已编写了子章节：--- [ SUBSECTION ] --- 基于上述特定论文的句子后面会加上“paper_title”的引用，格式为“[]”。例如‘the emergence of large language models (LLMs) [PaLM: Scaling language modeling with pathways]’。以下是文献综述中何时引用论文的简要指南：--- 1. 总结
研究：在总结现有文献时需注明出处。2. 使用特定概念或数据：讨论特定理论、模型或数据时需提供引用。3. 使用成熟方法：在文献综述中需注明所采用方法的提出者。4. 支持论点：引用能够支撑你的结论和论点的来源。--- 现在你需要检查本小节中“paper_title”的引用是否正确。如果引用无法支持你所写的句子，请修改 ’ [] ’ 中的 paper_title 或将其删除。除引用外，不要更改其他任何内容。仅返回引用正确的小节：’ ’’ COHERENCY_REFINEMENT_PROMPT = ’’ ’ 你
想要撰写一篇全面且完整的文献综述。现在你需要协助完善其中一个小节，以提升该文献综述的连贯性。你已获得该小节的内容以及之前和后续的小节内容。之前的小节：--- [PREVIOUS] --- 后续小节：--- [FOLLOWING] --- 需要完善的小节：--- [SUBSECTION] --- 请完善该小节，增强其连贯性，并确保它能更流畅地与之前和后续小节相衔接。请记住，要保留该小节的全部核心信息，不要修改句后括号内的任何引用内容！！！仅返回完整内容
不含其他信息的该小节精炼内容：’ ’’


<details>
<summary>英文原文</summary>

⬇


ROUGH_OUTLINE_PROMPT

=





’’
’





You

want

to

write

a

overall

and

comprehensive

academic

survey

about

[TOPIC].





You

are

provided

with

a

list

of

papers

related

to

the

topic

below:





---





[PAPER

LIST]





---





You

need

to

draft

a

outline

based

on

the

given

papers.





The

outline

should

contains

a

title

and

several

sections.





Each

section

follows

with

a

brief

sentence

to

describe

what

to

write

in

this

section.





The

outline

is

supposed

to

be

comprehensive

and

contains

[SECTION

NUM]

sections.









Return

in

the

format:





<format>





Title:

[TITLE

OF

THE

SURVEY]





Section

1:

[NAME

OF

SECTION

1]





Description

1:

[DESCRIPTION

OF

SENTCTION

1]









...









Section

K:

[NAME

OF

SECTION

K]





Description

K:

[DESCRIPTION

OF

SENTCTION

K]





</format>





The

outline:





’
’’








SUBSECTION_OUTLINE_PROMPT

=





’’
’





You

want

to

write

a

overall

survey

about

[TOPIC].





You

have

created

a

overall

outline

below:





---





[OVERALL

OUTLINE]





---





The

outline

contains

a

title

and

several

sections.





Each

section

follows

with

a

brief

sentence

to

describe

what

to

write

in

this

section.





You

need

to

enrich

the

section

[SECTION

NAME].





The

description

of

[SECTION

NAME]:

[SECTION

DESCRIPTION]





You

need

to

generate

the

framwork

containing

several

subsections

based

on

the

overall

outlines.





Each

subsection

follows

with

a

brief

sentence

to

describe

what

to

write

in

this

subsection.





These

papers

provided

for

references:





---





[PAPER

LIST]





---





Return

the

outline

in

the

format:





<format>





Subsection

1:

[NAME

OF

SUBSECTION

1]





Description

1:

[DESCRIPTION

OF

SUBSENTCTION

1]









...









Subsection

K:

[NAME

OF

SUBSECTION

K]





Description

K:

[DESCRIPTION

OF

SUBSENTCTION

K]





</format>





Only

return

the

outline

without

any

other

informations:





’
’’








MERGING_OUTLINE_PROMPT

=





’’
’





You

want

to

write

a

overall

survey

about

[TOPIC].





You

are

provided

with

a

list

of

outlines

as

candidates

below:





---





[OUTLINE

LIST]





---





Each

outline

contains

a

title

and

several

sections.





Each

section

follows

with

a

brief

sentence

to

describe

what

to

write

in

this

section.





You

need

to

generate

a

final

outline

based

on

these

provided

outlines

to

make

the

final

outline

show

comprehensive

insights

of

the

topic

and

more

logical.





Return

the

in

the

format:





<format>





Title:

[TITLE

OF

THE

SURVEY]





Section

1:

[NAME

OF

SECTION

1]





Description

1:

[DESCRIPTION

OF

SENTCTION

1]









...









Section

K:

[NAME

OF

SECTION

K]





Description

K:

[DESCRIPTION

OF

SENTCTION

K]





</format>





Only

return

the

final

outline

without

any

other

informations:





’
’’








SUBSECTION_WRITING_PROMPT

=





’’
’





You

wants

to

write

a

overall

and

comprehensive

survey

about

[TOPIC].





You

have

created

a

overall

outline

below:





---





[OVERALL

OUTLINE]





---





Below

are

a

list

of

papers

for

reference:





---





[PAPER

LIST]





---









Now

you

need

to

write

the

content

for

the

subsection:





"[SUBSECTION

NAME]".





The

details

of

what

to

write

in

this

subsection

called

[SUBSECTION

NAME]

is

in

this

descripition:





---





[DESCRIPTION]





---





Here

is

the

requirement

you

must

follow:





1.

The

subsection

is

recommended

to

contain

more

than

[WORD

NUM]

words.





2.

When

writing

sentences

that

are

based

on

specific

papers

above,

you

cite

the

"paper_title"

in

a

’
[]
’

format

to

support

your

content.









Here’
s

a

concise

guideline

for

when

to

cite

papers

in

a

survey
:





---





1.

Summarizing

Research
:

Cite

sources

when

summarizing

the

existing

literature
.





2.

Using

Specific

Concepts

or

Data
:

Provide

citations

when

discussing

specific

theories
,

models
,

or

data
.





3.

Using

Established

Methods
:

Cite

the

creators

of

methodologies

you

employ

in

your

survey
.





4.

Supporting

Arguments
:

Cite

sources

that

back

up

your

conclusions

and

arguments
.





---





Only

return

the

content

more

than

[
WORD

NUM
]

words

you

write

for

the

subsection

[
SUBSECTION

NAME
]

without

any

other

information
:





’’
’








CITATION_REFLECTION_PROMPT

=





’
’’





You

want

to

write

a

overall

and

comprehensive

survey

about

[
TOPIC
].





Below

are

a

list

of

papers

for

references
:





---





[
PAPER

LIST
]





---





You

have

written

a

subsection

below
:





---





[
SUBSECTION
]





---





The

sentences

that

are

based

on

specific

papers

above

are

followed

with

the

citation

of

"paper_title"

in

"[]"
.





For

example

’the

emergence

of

large

language

models

(LLMs)

[PaLM:

Scaling

language

modeling

with

pathways]’









Here
’s

a

concise

guideline

for

when

to

cite

papers

in

a

survey:





---





1.

Summarizing

Research:

Cite

sources

when

summarizing

the

existing

literature.





2.

Using

Specific

Concepts

or

Data:

Provide

citations

when

discussing

specific

theories,

models,

or

data.





3.

Using

Established

Methods:

Cite

the

creators

of

methodologies

you

employ

in

your

survey.





4.

Supporting

Arguments:

Cite

sources

that

back

up

your

conclusions

and

arguments.





---









Now

you

need

to

check

whether

the

citations

of

"paper_title"

in

this

subsection

is

correct.





Once

the

citation

can

not

support

the

sentence

you

write,

correct

the

paper_title

in

’
[]
’

or

just

remove

it.









Do

not

change

any

other

things

except

the

citations.





Only

return

the

subsection

with

correct

citations:





’
’’








COHERENCY_REFINEMENT_PROMPT

=





’’
’





You

want

to

write

a

overall

and

comprehensive

survey

about

[TOPIC].









Now

you

need

to

help

to

refine

one

of

the

subsection

to

improve

th

ecoherence

of

your

survey.









You

are

provied

with

the

content

of

the

subsection

along

with

the

previous

subsections

and

following

subsections.









Previous

Subsection:





---





[PREVIOUS]





---









Following

Subsection:





---





[FOLLOWING]





---









Subsection

to

Refine:





---





[SUBSECTION]





---









Now

refine

the

subsection

to

enhance

coherence,

and

ensure

that

it

connects

more

fluidly

with

the

previous

and

following

subsections.





Remember

that

keep

all

the

essence

and

core

information

of

the

subsection

intact.

Do

not

modify

any

citations

in

[]

following

the

sentences!!!!





Only

return

the

whole

refined

content

of

the

subsection

without

any

other

informations:





’
’’

</details>

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


<details>
<summary>英文原文</summary>

⬇


#

Comprehensive

Survey

on

Emotion

Recognition

using

Large

Language

Models








##

1.

Introduction

to

Emotion

Recognition

and

Large

Language

Models





Emotion

recognition

has

been

a

crucial

and

active

research

area

in

the

field

of

affective

computing
,

which

aims

to

enable

machines

to

understand
,

interpret
,

and

respond

to

human

emotions

[1].

Emotions

play

a

fundamental

role

in

human

cognition
,

decision
-
making
,

and

social

interaction

[2],

and

the

ability

to

automatically

recognize

and

interpret

emotions

has

a

wide

range

of

applications
,

including

healthcare
,

education
,

entertainment
,

and

human
-
computer

interaction

[3].

The

importance

of

emotion

recognition

is

evident

in

various

real
-
world

applications
.

In

healthcare
,

emotion

recognition

can

be

used

to

monitor

patient

mental

health
,

provide

personalized

therapy
,

and

improve

doctor
-
patient

communication

[4].

In

education
,

emotion

recognition

can

help

identify

student

engagement

and

frustration

levels
,

enabling

adaptive

learning

environments

that

cater

to

individual

needs

[5].

In

the

entertainment

industry
,

emotion

recognition

can

be

used

to

analyze

viewer

responses

and

tailor

content

to

evoke

desired

emotional

responses

[6].

Despite

the

significant

benefits

of

emotion

recognition
,

the

field

faces

several

challenges

that

have

hindered

its

widespread

adoption

and

implementation

[7].

One

of

the

primary

challenges

is

the

inherent

complexity

and

subjectivity

of

emotions
,

which

can

vary

across

individuals
,

cultures
,

and

contexts

[8].

Emotions

are

often

expressed

through

multiple

modalities
,

including

facial

expressions
,

vocal

cues
,

body

language
,

and

physiological

signals
,

and

integrating

these

diverse

sources

of

information

is

a

significant

challenge

[9].

Additionally
,

the

availability

of

high
-
quality
,

diverse
,

and

annotated

emotion

datasets

is

a

persistent

challenge

in

the

field

[10].

Many

existing

datasets

are

limited

in

size
,

lack

diversity
,

or

have

inconsistent

or

subjective

emotion

labeling
,

which

can

lead

to

biases

and

poor

generalization

of

emotion

recognition

models

[11].





...




###

1.1

Background

on

Emotion

Recognition








###

1.2

Large

Language

Models

and

their

Capabilities








###

1.3

Emotion

Representation

in

LLMs








###

1.4

Multimodal

Emotion

Recognition

using

LLMs








##

2.

Techniques

and

Approaches

for

Emotion

Recognition

using

LLMs








###

2.1

Fine-tuning

LLMs

on

Emotion

Datasets








###

2.2

LLM-based

Prompting

Methods

for

Emotion

Recognition








###

2.3

Integrating

LLMs

with

Other

Modalities

for

Multimodal

Emotion

Recognition








##

3.

Enhancing

LLM-based

Emotion

Recognition








###

3.1

Data

Augmentation

for

Improving

Emotion

Recognition








###

3.2

Prompt

Engineering

for

Emotion

Recognition








###

3.3

Integrating

External

Knowledge

for

Emotion

Recognition








##

4.

Challenges,

Limitations,

and

Ethical

Considerations








###

4.1

Model

Biases

and

Hallucinations








###

4.2

Interpretability

and

Explainability








###

4.3

Ethical

Considerations








##

5.

Applications

and

Future

Directions








###

5.1

Assistive

Robotics








###

5.2

Mental

Health

Assessment








###

5.3

Customer

Service

and

User

Experience








###

5.4

Symbolic

Reasoning

and

Long-tailed

Emotions








###

5.5

Robust

Evaluation

Frameworks








##

References








[1]

Affective

Computing

for

Large
-
Scale

Heterogeneous

Multimedia

Data

A

Survey




[2]

Emotion

Recognition

in

Conversation

Research

Challenges
,

Datasets
,

and

Recent

Advances




[3]

A

Comprehensive

Survey

on

Affective

Computing
;

Challenges
,

Trends
,

Applications
,

and

Future

Directions




[4]

Affective

Computing

for

Healthcare

Recent

Trends
,

Applications
,

Challenges
,

and

Beyond




[5]

Automatic

Sensor
-
free

Affect

Detection

A

Systematic

Literature

Review




[6]

Affective

Video

Content

Analysis

Decade

Review

and

New

Perspectives




[7]

Emotion

Recognition

from

Multiple

Modalities

Fundamentals

and

Methodologies




[8]

The

Ambiguous

World

of

Emotion

Representation




[9]

Multimodal

Affective

Analysis

Using

Hierarchical

Attention

Strategy

with

Word
-
Level

Alignment




[10]

Expression
,

Affect
,

Action

Unit

Recognition

Aff
-
Wild2
,

Multi
-
Task

Learning

and

ArcFace




[11]

Feature

Dimensionality

Reduction

for

Video

Affect

Classification

A

Comparative

Study

</details>

