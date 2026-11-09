# OpenScholar：全文中英对照

OpenScholar: Synthesizing Scientific Literature with Retrieval-augmented LMs

版本：2411.14199v1。获取日期：2026-11-09。

来源：[原始页面](https://arxiv.org/abs/2411.14199v1) · [原始 PDF](../../../sources/fulltext/openscholar/original.pdf)

原文许可：http://creativecommons.org/licenses/by/4.0/

> 全文可提取文本的中英对照机器初译，含附录。摘要由当前助手复核，全文尚未逐段精校。作者/机构、参考文献、代码和公式按需保留原文；图内文字和复杂表格请结合原 PDF 核对。译文为非官方改编，作者未为其背书。

## 论文总结 / Reading summary

OpenScholar combines scientific retrieval, reranking, generation, and citation checking. The system separates access to relevant evidence from the language model's writing ability, and evaluates answers using expert scientific questions.

OpenScholar 结合科学文献检索、重排、生成和引用核查。系统将相关证据获取与语言模型写作能力区分开，并使用专家科学问题评价回答。

1. 研究问题：科学文献问答需要综合多篇论文并给出可核查引用，通用模型的参数知识和表达能力无法保证证据正确。
2. 方法：建立学术数据存储，先检索相关片段，再重排并生成回答；通过自反馈补充检索和修订，并核查引用。论文还利用推理流程合成训练数据。
3. 评价：ScholarQABench 覆盖不同学科，区分单篇与多篇文献任务，并评价回答正确性、引用准确性和内容组织；这些维度不能被一个总写作分数替代。
4. 证据：本次采用的 2024 arXiv v1 报告检索增强模型相对当时模型的优势。它不能说明 2026 年最新模型之间的排序。
5. 版本：本次全文翻译来自明确标注 CC BY 4.0 的 arXiv v1。2026 年 Nature 正式版另有出版信息和修订；这里没有把两个版本拼接成一篇原文。
6. 局限：能回答带引用的问题，不等于能完成有原创分类和批判性综合的整篇综述。检索不到关键反例时，引用存在也可能掩盖结论偏差。
7. 本项目可复用：保存每条主张对应的原文位置、条件和支持关系；评价“引用存在”与“引用足以支持这条主张”之间的差异。

## 逐段对照正文与附录

### openscholar-0001

**English original**

Open Scholar : Synthesizing Scientific Literature with Retrieval-augmented LMs

**中文译文 · 助手校对题名**

OpenScholar：利用检索增强语言模型综合科学文献

### openscholar-0002

**English original**

Akari Asai Jacqueline He Rulin Shao Weijia Shi

**原文保留（专名、技术内容或文献信息） · 保留原文**

Akari Asai Jacqueline He Rulin Shao Weijia Shi

### openscholar-0003

**English original**

†

**原文保留（专名、技术内容或文献信息） · 保留原文**

†

### openscholar-0004

**English original**

†

**原文保留（专名、技术内容或文献信息） · 保留原文**

†

### openscholar-0005

**English original**

thanks:

**原文保留（专名、技术内容或文献信息） · 保留原文**

thanks:

### openscholar-0006

**English original**

Contributed equally (alphabetical order). All authors’ contributions are detailed in the Contribution section.

**原文保留（专名、技术内容或文献信息） · 保留原文**

Contributed equally (alphabetical order). All authors’ contributions are detailed in the Contribution section.

### openscholar-0007

**English original**

Email:

**原文保留（专名、技术内容或文献信息） · 保留原文**

Email:

### openscholar-0008

**English original**

akari@cs.washington.edu

**原文保留（专名、技术内容或文献信息） · 保留原文**

akari@cs.washington.edu

### openscholar-0009

**English original**

Amanpreet Singh Joseph Chee Chang Kyle Lo Luca Soldaini

**原文保留（专名、技术内容或文献信息） · 保留原文**

Amanpreet Singh Joseph Chee Chang Kyle Lo Luca Soldaini

### openscholar-0010

**English original**

Email:

**原文保留（专名、技术内容或文献信息） · 保留原文**

Email:

### openscholar-0011

**English original**

pangwei@cs.washington.edu

**原文保留（专名、技术内容或文献信息） · 保留原文**

pangwei@cs.washington.edu

### openscholar-0012

**English original**

Sergey Feldman Mike D’arcy David Wadden Matt Latzke

**原文保留（专名、技术内容或文献信息） · 保留原文**

Sergey Feldman Mike D’arcy David Wadden Matt Latzke

### openscholar-0013

**English original**

Email:

**原文保留（专名、技术内容或文献信息） · 保留原文**

Email:

### openscholar-0014

**English original**

hannaneh@cs.washington.edu

**原文保留（专名、技术内容或文献信息） · 保留原文**

hannaneh@cs.washington.edu

### openscholar-0015

**English original**

Minyang Tian Pan Ji Shengyan Liu Hao Tong Bohao Wu Yanyu Xiong

**原文保留（专名、技术内容或文献信息） · 保留原文**

Minyang Tian Pan Ji Shengyan Liu Hao Tong Bohao Wu Yanyu Xiong

### openscholar-0016

**English original**

Affiliation:

**原文保留（专名、技术内容或文献信息） · 保留原文**

Affiliation:

### openscholar-0017

**English original**

University of Washington Allen Institute for AI University of Illinois, Urbana-Champaign

**原文保留（专名、技术内容或文献信息） · 保留原文**

University of Washington Allen Institute for AI University of Illinois, Urbana-Champaign

### openscholar-0018

**English original**

Affiliation:

**原文保留（专名、技术内容或文献信息） · 保留原文**

Affiliation:

### openscholar-0019

**English original**

Carnegie Mellon University Meta University of North Carolina, Chapel Hill Stanford University

**原文保留（专名、技术内容或文献信息） · 保留原文**

Carnegie Mellon University Meta University of North Carolina, Chapel Hill Stanford University

### openscholar-0020

**English original**

Luke Zettlemoyer Graham Neubig Dan Weld Doug Downey

**原文保留（专名、技术内容或文献信息） · 保留原文**

Luke Zettlemoyer Graham Neubig Dan Weld Doug Downey

### openscholar-0021

**English original**

Wen-tau Yih Pang Wei Koh Hannaneh Hajishirzi

**原文保留（专名、技术内容或文献信息） · 保留原文**

Wen-tau Yih Pang Wei Koh Hannaneh Hajishirzi

### openscholar-0022

**English original**

Abstract

**中文译文 · 机器初译**

摘要

### openscholar-0023

**English original**

Scientific progress depends on researchers’ ability to synthesize the growing body of literature. Can large language models (LMs) assist scientists in this task?
We introduce OpenScholar , a specialized retrieval-augmented LM that answers scientific queries by identifying relevant passages from 45 million open-access papers and synthesizing citation-backed responses.
To evaluate OpenScholar , we develop ScholarQABench , the first large-scale multi-domain benchmark for literature search, comprising 2,967 expert-written queries and 208 long-form answers across computer science, physics, neuroscience, and biomedicine.
On ScholarQABench , OpenScholar -8B outperforms GPT-4o by 5% and PaperQA2 by 7% in correctness, despite being a smaller, open model. While GPT4o hallucinates citations 78–90% of the time, OpenScholar achieves citation accuracy on par with human experts. OpenScholar ’s datastore, retriever, and self-feedback inference loop also improves off-the-shelf LMs: for instance, OpenScholar -GPT4o improves GPT-4o’s correctness by 12%.
In human evaluations, experts preferred OpenScholar -8B and OpenScholar -GPT4o responses over expert-written ones 51% and 70% of the time, respectively, compared to GPT4o’s 32%.
We open-source all of our code, models, datastore, data and a public demo.

**中文译文 · 助手复核摘要**

科学进步依赖研究者综合不断增长的文献的能力。语言模型（LM）能否帮助科学家完成这一任务？我们提出 OpenScholar，一种专门的检索增强语言模型：它从 4,500 万篇开放获取论文中识别相关片段，并综合生成有引用支持的回答。为评价 OpenScholar，我们建立了 ScholarQABench——首个大规模、多领域的文献检索基准，包含计算机科学、物理学、神经科学和生物医学领域的 2,967 个专家编写的问题和 208 个长篇回答。在 ScholarQABench 上，尽管 OpenScholar-8B 是规模更小的开放模型，其正确性仍分别比 GPT-4o 和 PaperQA2 高出 5% 和 7%。GPT-4o 编造引用的比例为 78%–90%，而 OpenScholar 的引用准确性达到与人类专家相当的水平。OpenScholar 的数据存储、检索器和自反馈推理循环也能改善现成语言模型：例如，OpenScholar-GPT4o 使 GPT-4o 的正确性提高了 12%。在人类评价中，相对于专家撰写的回答，专家选择 OpenScholar-8B 和 OpenScholar-GPT4o 回答的比例分别为 51% 和 70%，而 GPT-4o 的相应比例为 32%。我们开放了全部代码、模型、数据存储、数据以及公开演示。

### openscholar-0024

**English original**

Demo | | openscholar.allen.ai/
Blog | | allenai.org/blog/openscholar
OpenScholar code | | github.com/AkariAsai/OpenScholar
ScholarBench code | | github.com/AkariAsai/ScholarBench
Checkpoints, Data, Index | | OpenScholar/openscholar-v1
Expert Evaluation | | AkariAsai/OpenScholar_ExpertEval

**中文译文 · 机器初译**

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

### openscholar-0025

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0026

**English original**

Figure 1: (Top) Overview of OpenScholar : OpenScholar consists of a specialized datastore, retrievers and LMs and iteratively improves responses using self-feedback inference with retrieval. (Middle) Overview of ScholarQABench : ScholarQABench consists of 2.2k expert-written questions across multiple scientific disciplines, and we introduce automatic and human evaluation protocols for ScholarQABench . (Bottom) Automatic and Human Evaluation Results: Experimental results show the effectiveness of ScholarQABench , and that OpenScholar with our trained 8B or GPT4o significantly outperforms other systems, and is preferred over experts over 50% of the time in human evaluations.

**中文译文 · 机器初译**

图1：（顶部）OpenScholar概述：OpenScholar由专门的数据存储库、检索器及大语言模型组成，通过结合检索的自我反馈推理机制来逐步优化回答。（中间）ScholarQABench概述：ScholarQABench包含2,200个来自多个科学领域的专家编写的问题，我们针对ScholarQABench引入了自动评估与人工评估方案。（底部）自动评估与人工评估结果：实验结果表明ScholarQABench具有显著效果，而经过我们训练的8B或GPT4o版本的OpenScholar表现优于其他系统，在人工评估中超过50%的时间都优于专家系统。

### openscholar-0027

**English original**

1 Introduction

**中文译文 · 机器初译**

1 引言

### openscholar-0028

**English original**

Synthesizing knowledge from scientific literature is essential for uncovering new research directions, refining methodologies, and supporting evidence-based decisions. However, the vast volume of papers published annually makes it increasingly difficult for researchers to stay informed. Effective synthesis requires precise retrieval, accurate attribution, and real-time access to current literature.
While large language models (LLMs) show promise in assisting researchers, they face significant challenges, including hallucinations ( Mallen et al., 2023 ; Mishra et al., 2024 ) , reliance on outdated pre-training data ( Kasai et al., 2023 ) , and a lack of transparent attribution. For instance, when tasked with citing up-to-date literature, GPT-4 fabricated citations in 78-90% of cases across fields like computer science and biomedicine in our experiments.

**中文译文 · 机器初译**

整合科学文献中的知识对于发现新的研究方向、完善研究方法以及支持基于证据的决策至关重要。然而，每年发表的论文数量庞大，使得研究人员难以及时获取最新信息。有效的整合工作需要精确的检索、准确的归属标注以及对当前文献的实时访问能力。尽管大语言模型在辅助研究人员方面具有潜力，但它们也面临诸多挑战，包括幻觉现象（Mallen等，2023；Mishra等，2024）、依赖过时的预训练数据（Kasai等，2023）以及缺乏透明的归属标注机制。
例如，在需要引用最新文献的任务中，我们的实验中 GPT-4 在计算机科学和生物医学等领域有 78-90% 的案例中伪造了引用内容。

### openscholar-0029

**English original**

Retrieval-augmented LMs ( Lewis et al., 2020 ; Guu et al., 2020 ) , on the other hand, can mitigate many of these issues by integrating retrieved external knowledge sources at inference-time, driving the development of systems for literature search and synthesis ( Agarwal et al., 2024 ; Zheng et al., 2024 ; Skarlinski et al., 2024 ) .
However, many such systems rely on black-box APIs or general-purpose LLMs that are neither optimized for literature synthesis nor paired with open, domain-specific retrieval datastores (i.e., a processed corpus and corresponding retrieval index) that are specifically suited for scientific domains.
Moreover, evaluations for scientific literature synthesis have been limited, using single-discipline and small-scale human evaluations ( Agarwal et al., 2024 ; Zheng et al., 2024 ) or simplified tasks such as multiple-choice question answering ( Skarlinski et al., 2024 ) .

**中文译文 · 机器初译**

另一方面，基于检索增强的大语言模型（Lewis等，2020；Guu等，2020）通过在推理阶段整合检索到的外部知识来源，能够缓解许多问题，从而推动文献搜索与合成系统的发展（Agarwal等，2024；Zheng等，2024；Skarlinski等，2024）。然而，许多此类系统依赖于黑盒式API或通用大语言模型，这些模型既未针对文献合成进行优化，也未能与适合科学领域使用的开放、领域特定的检索数据存储库（即经过处理的语料库及相应的检索索引）结合使用。
此外，针对科学文献整合的评估工作十分有限，通常依赖单一学科的小规模人工评估（Agarwal等，2024；Zheng等，2024），或采用简单的任务如选择题回答（Skarlinski等，2024）。

### openscholar-0030

**English original**

To address these gaps, we present OpenScholar (Figure 1 , top), a state-of-the-art retrieval-augmented LM with a specialized paper datastore and retrievers trained on scientific literature. At inference time, OpenScholar retrieves relevant passages and uses iterative self-feedback generation to refine its own output.
We further train a new, efficient 8B LM.
To evaluate the effectiveness of OpenScholar , we introduce ScholarQABench (Figure 1 , middle), a benchmark specifically designed to enable a realistic and reproducible evaluation of open-ended scientific question answering.

**中文译文 · 机器初译**

为了填补这些空白，我们提出了 OpenScholar（图1顶部），这是一种先进的检索增强型大语言模型，拥有专门的文献数据存储库以及基于科学文献训练的检索器。在推理过程中，OpenScholar会检索相关段落，并通过迭代自我反馈生成机制来优化其输出结果。我们还训练了新的高效8B大语言模型。为了评估 OpenScholar 的有效性，我们引入了 ScholarQABench（图1中间部分），这是一个专门设计的基准测试工具，旨在实现真实且可重复的开放式科学问题回答评估。

### openscholar-0031

**English original**

OpenScholar (Section 2 ) uses our new OpenScholar - DataStore (OSDS), which contains 45 million open-access papers from Semantic Scholar, along with 237 million corresponding passage embeddings.
To the best of our knowledge, this is the largest open-sourced datastore of scientific domains. OpenScholar first retrieves passages from OSDS using a retriever and reranker. Subsequently, an LM synthesizes the retrieved passages to generate responses with citations. OpenScholar iteratively refines its outputs through natural language feedback, which improves quality and adaptively incorporates supplementary information.
This pipeline is also used to create large-scale, high-quality training data for smaller, more efficient models. We generate synthetic queries and instructions from sampled datastore passages, feed them into OpenScholar , and use intermediate and final output to train open 8B model, OpenScholar -8B and retrieval models.

**中文译文 · 机器初译**

OpenScholar（第2节）使用我们的新版 OpenScholar - DataStore（OSDS），该数据库包含来自 Semantic Scholar的4500万篇开放获取论文以及2.37亿个对应的段落嵌入数据。据我们所知，这是科学领域最大的开源数据存储库。OpenScholar首先通过检索器和重新排序器从 OSDS 中检索段落，随后由大语言模型对这些检索到的段落进行整合，以生成带有引用信息的回复。OpenScholar通过自然语言反馈不断优化其输出结果，从而提升质量并自适应地纳入补充信息。
该流程还被用于为更小、更高效的模型生成大规模、高质量的训练数据。我们从采样的数据存储段落中生成合成查询和指令，将其输入到 OpenScholar 系统中，并利用中间和最终输出来训练开放 8B 模型、OpenScholar -8B 模型以及检索模型。

### openscholar-0032

**English original**

ScholarQABench (Section 3 ) is a benchmark designed to evaluate the ability of models to understand and synthesize existing research. Unlike previous benchmarks that assume that answers can be found in a single paper (e.g., scientific fact-checking; Wadden et al., 2020 ; Skarlinski et al., 2024 ), many real-world scenarios require identifying multiple relevant papers and generating long-form output with accurate citations. To address these challenges, we curated a dataset of 2,967 literature synthesis questions, along with 208 long-form responses that are written by experts and span four scientific disciplines, namely computer science, physics, biomedicine, and neuroscience. These responses were crafted by Ph.D. students and postdoctoral researchers with more than three years of experience and relevant publications in the field. On average, each response required approximately one hour to compose.
We also introduce a multifaceted evaluation protocol that combines automated metrics and human assessments to measure citation accuracy, factual correctness, content coverage, coherence, and overall quality.
This multifaceted approach ensures robust and reproducible evaluations, both automatic and human-driven.

**中文译文 · 机器初译**

ScholarQABench（第3节）是一个用于评估模型理解与整合现有研究能力的基准测试。与那些假设答案仅存在于单一文献中的先前基准测试不同（例如科学事实核查研究；Wadden等，2020；Skarlinski等，2024），许多现实场景需要识别多篇相关文献，并生成包含准确引用信息的长篇输出内容。为了应对这些挑战，我们整理了一组2,967个文献综合问题以及208篇由专家撰写的长篇回答，这些回答涉及计算机科学、物理学、生物医学和神经科学四个科学领域。
这些回复由拥有三年以上经验且在该领域有相关出版成果的博士学生和博士后研究人员撰写。平均而言，每一条回复的撰写时间约为一小时。我们还引入了一种多维度评估方案，结合自动化指标与人工评估，以衡量引用准确性、事实正确性、内容覆盖度、连贯性及整体质量。这种多维度方法能够确保自动和人工驱动的评估都具有稳健性和可重复性。

### openscholar-0033

**English original**

We evaluated proprietary and open models (e.g., GPT4o, Llama 3.1 8B, 70B) with and without retrieval capabilities, as well as specialized systems like PaperQA2 ( Skarlinski et al., 2024 ) , on ScholarQABench (Section 4 ). While GPT4o demonstrated strong general performance, it struggled with citation accuracy and coverage, often producing inaccurate or non-existent citations. OpenScholar outperformed both LM-only and retrieval-augmented pipelines, surpassing proprietary and open-source systems. Notably, using fully open-source checkpoints, OpenScholar outperformed PaperQA2 ( Skarlinski et al., 2024 ) , built on proprietary LMs, and production systems like Perplexity Pro, achieving 6% and 10% improvements, respectively. Additionally, OpenScholar ’s use of smaller, efficient retrievers significantly reduced costs.
Combining OpenScholar with GPT4o also improved correctness by 12% over GPT4o alone.
The OpenScholar pipeline can also enhance off-the-shelf LMs. For example, when using GPT-4o as the underlying model, OpenScholar -GPT4o achieves a 12% improvement in correctness compared to GPT-4o alone.

**中文译文 · 机器初译**

我们在 ScholarQABench上对具有和缺乏检索功能的专有及开源模型（如 GPT4o、Llama 3.1 8B、70B），以及像 PaperQA2 这样的专用系统（Skarlinski等，2024年）进行了评估（第4节）。虽然 GPT4o 表现出良好的整体性能，但在引用准确性和覆盖率方面存在不足，常常产生不准确或不存在的引用。OpenScholar 则优于仅基于语言模型的流程和带有检索增强的流程，甚至超过了专有及开源系统。
值得注意的是，使用完全开源的检查点模型，OpenScholar在基于专有大语言模型的PaperQA2（Skarlinski等，2024）以及Perplexity Pro等生产系统中均取得了6%和10%的性能提升。此外，OpenScholar采用更小、更高效的检索器显著降低了成本。将OpenScholar与GPT4o结合使用后，其正确性也比单独使用GPT4o提升了12%。OpenScholar流程还能提升现成的大语言模型性能，例如，当以GPT-4o作为底层模型时，OpenScholar-GPT4o的正确率相比单独使用GPT-4o提升了12%。

### openscholar-0034

**English original**

In addition to automatic evaluations on ScholarQABench , we conducted detailed expert assessments with 16 scientists from fields such as computer science, physics, and biomedicine (Section 5 ). These experts performed pairwise and fine-grained evaluations of OpenScholar ’s outputs against 108 expert-written responses to literature synthesis queries in ScholarQABench . OpenScholar , when paired with GPT-4o and our trained 8B model, consistently outperformed expert-written responses, with win rates of 70% and 51%, respectively.
In contrast, GPT-4o without retrieval struggled with information coverage and was rated as less helpful than human experts, achieving only a 31% win rate against human responses.
This highlights that OpenScholar -generated outputs are more comprehensive, well-organized, and useful for synthesizing literature.
These findings demonstrate that OpenScholar produces high-quality outputs that are not only competitive with expert-written answers but, in some cases, exceed them, particularly in terms of coverage and organization.

**中文译文 · 机器初译**

除了在 ScholarQABench 上的自动评估外，我们还邀请了来自计算机科学、物理学和生物医学领域的16位专家进行了详细评估（第5节）。这些专家对 OpenScholar 的输出与 ScholarQABench 中针对文献综合查询的108份专家撰写回复进行了成对及细致评估。当 OpenScholar 与 GPT-4o 以及我们训练的8B模型结合使用时，其表现始终优于专家撰写的回复，分别获得了70%和51%的胜率。
相比之下，没有检索功能的 GPT-4o在信息覆盖度方面存在不足，其帮助程度低于人类专家，对人类回复的回应成功率仅为 31%。这凸显了 OpenScholar 生成的输出更为全面、结构清晰，且有助于文献整合。这些研究结果表明，OpenScholar 产生的高质量输出不仅与专家撰写的答案具有竞争力，在某些情况下甚至更胜一筹，尤其是在信息覆盖度和组织性方面。

### openscholar-0035

**English original**

OpenScholar -8B is an open retrieval-augmented LM that avoids reliance on proprietary LMs or retrieval systems, leveraging one of the largest datastores in scientific literature domains.
We release the full OpenScholar ecosystem, including code, trained retrievers, the LM checkpoint, the datastore, the ScholarQABench benchmark, expert evaluation tools, and a public demo.

**中文译文 · 机器初译**

OpenScholar -8B 是一种开放式的检索增强型大语言模型，它无需依赖专有大语言模型或检索系统，能够利用科学文献领域中最大的数据存储库之一。我们发布了完整的 OpenScholar 生态系统，包括代码、训练好的检索模型、模型检查点、数据存储库、ScholarQABench 基准测试、专家评估工具以及公开演示平台。

### openscholar-0036

**English original**

2 OpenScholar : Open Retrieval-augmented LM to Synthesizing Scientific Literature

**中文译文 · 机器初译**

2 OpenScholar：用于整合科学文献的大语言模型与检索增强技术

### openscholar-0037

**English original**

OpenScholar (detailed in Figure 2 ) is a new retrieval-augmented LM designed to ensure reliable, high-quality responses to a range of information-seeking queries about scientific literature.

**中文译文 · 机器初译**

OpenScholar（详见图2）是一种基于检索增强的大语言模型，旨在为各种关于科学文献的信息查询提供可靠且高质量的回复。

### openscholar-0038

**English original**

Task formulation.

**中文译文 · 机器初译**

任务构建。

### openscholar-0039

**English original**

Given a scientific query $x$ , the task is to identify relevant papers, synthesize their findings, and generate a response $y$ that effectively addresses the query. This response should be accompanied by a set of citations, $\mathbf{C}={c_{1},c_{2},\ldots,c_{K}}$ , wherein each citation $c_{i}$ corresponds to an existing scientific paper. Each $c_{i}$ in $\mathbf{C}$ corresponds to specific passages from scientific literature, and should be provided as an in-line citation, linked to the relevant spans of text in $y$ , following standard practice in scientific writing.
These citations allow researchers to trace the output back to the original literature, ensuring transparency and verifiability.

**中文译文 · 机器初译**

针对一个科学查询 $x$，任务在于识别相关的文献，综合其研究结论，并生成能够有效解答该查询的回应 $y$。该回应应附带一组引用信息 $\mathbf{C}={c_{1},c_{2},\ldots,c_{K}}$，其中每个引用 $c_{i}$ 都对应一篇现有的科学论文。$\mathbf{C}$ 中的每个 $c_{i}$ 均来自科学文献的特定段落，应按照科学写作的标准做法，以在线引用形式呈现，并与相关文本片段相关联。
这些引用使得研究人员能够将输出结果追溯到原始文献，从而确保透明性和可验证性。

待核对标记：formula_or_link_placeholder_missing

### openscholar-0040

**English original**

Overview of OpenScholar .

**中文译文 · 机器初译**

OpenScholar 概述

### openscholar-0041

**English original**

To ensure the retrieval of relevant papers and generate high-quality outputs, ScholarQABench consists of three key components: a datastore $\mathbf{D}$ , a retriever $\mathcal{R}$ , and a generator LM $\mathcal{G}$ .
In standard retrieval-augmented inference pipelines, the process begins with $\mathcal{R}$ , which retrieves a set of passages $\mathbf{P}=\{p_{1},p_{2},\ldots,p_{N}\}$ from $\mathbf{D}$ —a large-scale corpus of previously published scientific papers—based on semantic relevance to the input query $x$ . These passages serve as context for the next step.
The generator LM $\mathcal{G}$ then takes both the retrieved passages $\mathbf{P}$ and the input query $x$ to produce the output $y$ along with corresponding citations $\mathbf{C}$ . Formally, this process can be represented as:

**中文译文 · 机器初译**

为确保能够检索到相关文献并生成高质量输出，ScholarQABench由三个关键组件构成：数据存储系统、检索器以及大语言模型生成器。在标准的检索增强推理流程中，整个过程始于基于输入查询的语义相关性，从大规模已发表科学论文语料库中检索一组段落——这些段落作为下一步的上下文。
该生成器大语言模型 $\mathcal{G}$ 随后会结合检索到的段落 $\mathbf{P}$ 和输入查询 $x$，生成输出 $y$以及相应的引用信息 $\mathbf{C}$。从形式上看，这一过程可以表示为：

待核对标记：formula_or_link_placeholder_missing

### openscholar-0042

**English original**

| $y,\mathbf{C}=\mathcal{G}(x,\mathcal{R}(x,\mathbf{D})),$ |

**中文译文 · 机器初译**

| $y,\mathbf{C}=\mathcal{G}(x,\mathcal{R}(x,\mathbf{D})),$ |

表内文字对照（数值与原始行列保持不变）：
mathbf → mathbf
mathcal → mathcal

### openscholar-0043

**English original**

where each $c_{i}$ in $\mathbf{C}$ corresponds to a specific passage from $\mathbf{P}$ .
In OpenScholar (Figure 1 ), we leverage a suite of specialized components designed for scientific domains: the OpenScholar - DataStore $\mathbf{D}$ , a OpenScholar - Retriever /- Reranker , and an LM, enabling flexible use of either off-the-shelf LMs (e.g., GPT4o) or our newly trained OpenScholar -LM. We develop self-feedback retrieval-augmented inference to improve reliability and citation accuracy.

**中文译文 · 机器初译**

其中，每个 $c_{i}$ 在 $\mathbf{C}$ 中对应 $\mathbf{P}$ 中的特定段落。在 OpenScholar 系统中（图 1），我们利用了专为科学领域设计的多种专用组件：OpenScholar - DataStore $\mathbf{D}$、OpenScholar - Retriever/- Reranker 以及大语言模型，从而能够灵活使用现成的大语言模型（如 GPT4o）或我们新训练的 OpenScholar -LM。我们开发了基于自我反馈的检索增强推理机制，以提升可靠性与引用准确性。

### openscholar-0044

**English original**

OpenScholar - DataStore (OSDS) is a database of 45 million scientific papers, for which we build embeddings.
We train OpenScholar - Retriever and OpenScholar - Reranker on scientific data, which passes the top $N$ passages to the generator $\mathcal{G}$ (Section 2.1 ).
Subsequently, we use iterative self-feedback inference with retrieval: the LM first generates an initial draft $y_{0}$ with $\mathcal{G}$ , then iteratively enhances its output through retrieval-augmented self-feedback (Section 2.2 ).
We use this pipeline to generate high-quality training data (Section 2.3 ), enabling the training of specialized LMs that produce higher-quality output and more accurate citations.

**中文译文 · 机器初译**

OpenScholar - DataStore (OSDS) 是一个包含4500万篇科学论文的数据库，我们基于该数据库构建嵌入向量。我们在科学数据上训练 OpenScholar - Retriever 和 OpenScholar - Reranker，这些模型会将最关键的段落传递给生成器（第2.1节）。随后，我们采用基于检索的迭代自反馈推理机制：大语言模型首先使用特定参数生成初始草案，然后通过基于检索的自反馈机制逐步优化其输出（第2.2节）。我们利用这一流程生成高质量训练数据（第2.3节），从而能够训练出能产生更高质量输出和更精准引用的专业大语言模型。

待核对标记：formula_or_link_placeholder_missing

### openscholar-0045

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0046

**English original**

Figure 2: Detailed overview of OpenScholar inference (top) and training (bottom) .
At inference time, given an input $x$ , OpenScholar first uses a retriever to identify relevant papers from a specialized datastore ( OpenScholar -Datastore), and then uses a reranker to refine and identify the top $N$ retrieved documents. The retrieved output is then passed to the LM, which generates both an (1) initial response $y_{0}$ and (2) self-feedback $f_{1}$ . By incorporating its own feedback, the LM iteratively refines its output a pre-defined number of times.
Subsequently, an LM (1) generates initial response $y_{0}$ , (2) generates self-feedback on the initial output, and (3) incorporate feedback ( $f_{i}$ ) to generates an updated response $y_{1}$ .
The LM repeats the process until all feedback is incorporated.
To train a smaller yet competitive 8B LM, we generate high-quality training data using this inference-time pipeline followed by data filtering and mixing.

**中文译文 · 机器初译**

图2：OpenScholar推理（上）与训练（下）的详细概述。在推理过程中，给定输入$x$后，OpenScholar首先使用检索器从专用数据存储库中识别相关论文（OpenScholar -Datastore），然后利用重新排序器对检索到的文档进行优化和筛选，选出前$N$篇文档。这些检索结果随后被传递给大语言模型，该模型生成（1）初始响应$y_{0}$和（2）自我反馈$f_{1}$。通过整合自身的反馈，大语言模型会反复迭代优化其输出，直至达到预定义的次数。
随后，大语言模型(1)生成初始响应 $y_{0}$，(2)对初始输出进行自我反馈，然后(3)将反馈 $f_{i}$ 纳入其中以生成更新后的响应 $y_{1}$。该大语言模型重复此过程直至所有反馈都被整合完毕。为了训练一个规模较小但性能相当的8B大语言模型，我们采用这种推理阶段流程生成高质量训练数据，随后进行数据筛选与混合处理。

### openscholar-0047

**English original**

2.1 OpenScholar Retrieval Pipeline

**中文译文 · 机器初译**

2.1 OpenScholar 检索管道

### openscholar-0048

**English original**

Figure 2 (top left) shows our retrieval pipeline, consisting of a datastore $\mathbf{D}$ , a bi-encoder retriever $\theta_{\text{bi}}$ , and a cross-encoder reranker $\theta_{\text{cross}}$ .
We first select initial candidate paragraphs using $\mathbf{D}$ and $\theta_{\text{bi}}$ , as well as external APIs, and then refine and identify the top $N$ relevant paragraphs using $\theta_{\text{cross}}$ .

**中文译文 · 机器初译**

图2（左上角）展示了我们的检索流程，包括一个数据存储系统 $\mathbf{D}$、一个双编码器检索器 $\theta_{\text{bi}}$ 以及一个交叉编码器重排序器 $\theta_{\text{cross}}$。我们首先使用 $\mathbf{D}$ 和 $\theta_{\text{bi}}$ 以及外部 API 选择初始候选段落，随后通过 $\theta_{\text{cross}}$ 对这些段落进行优化和筛选，最终选出最相关的 $N$ 段落。

### openscholar-0049

**English original**

Collect scientific papers to construct datastore.

**中文译文 · 机器初译**

收集科学论文以构建数据存储库。

### openscholar-0050

**English original**

While prior work often uses a small subset of papers, such as arXiv papers from 2023-2024 ( Zheng et al., 2024 ) , it is important to have a diverse set of papers to improve the quality and coverage of model generation ( Shao et al., 2024 ) .
To this end, we use peS2o ( Soldaini et al., 2024 ) as our retrieval source, which consists of open-access academic papers from S2ORC ( Lo et al., 2020 ) . We built our datastore using peS2o v3, 1 1 1 https://huggingface.co/datasets/allenai/peS2o/tree/main/data/v3 . which includes 45 million papers up until October 2024. 2 2 2 For evaluations, we use peS2o v2 for evaluation, which consists of papers up to January 2023, as our main benchmarks and models were constructed before the v3 curation. Following prior work ( Shao et al., 2024 ) , we split the main text of each paper into discrete, 250-word text blocks (as determined by white space) and concatenate the paper title to each block to formulate passages in $\mathbf{D}$ .
Our datastore consists of 234 million passages.
To our knowledge, this is the largest open-sourced datastore for scientific literature.

**中文译文 · 机器初译**

虽然以往的研究通常仅使用少量论文，例如 2023-2024 年的 arXiv 论文（Zheng 等，2024），但拥有多样化的论文集合对于提升模型生成的质量与覆盖范围至关重要（Shao 等，2024）。为此，我们采用 peS2o（Soldaini 等，2024）作为检索来源，该数据集包含来自 S2ORC 的开放获取学术论文（Lo 等，2020）。我们基于 peS2o v3 构建数据仓库，其中包含了截至 2024 年 10 月的 4500 万篇论文。
2 2 2 在评估方面，我们使用 peS2o v2 作为主要基准，该数据集包含截至 2023 年 1 月的文献，因为我们的模型和基准是在 v3 版本整理之前构建的。依据先前的研究（Shao等人，2024），我们将每篇文献的主要文本划分为独立的 250 词文本块（通过空白字符确定），并将文献标题与每个文本块拼接起来，从而生成 $\mathbf{D}$ 格式的文本段落。我们的数据存储包含 2.34 亿个文本段落。据我们所知，这是最大的开源科学文献数据存储库。

待核对标记：formula_or_link_placeholder_missing

### openscholar-0051

**English original**

Retrieve initial paragraphs.

**中文译文 · 机器初译**

检索初始段落。

### openscholar-0052

**English original**

We retrieve passages from three sources: (1) the peS2o datastore using our trained retriever, (2) publicly available abstract from papers returned via the Semantic Scholar API ( Kinney et al., 2023 ) based on search keywords, and (3) publicly available texts from papers retrieved through a web search engine using the original query $x$ .
For (1), we first generate embeddings of each passage in $\mathbf{D}$ using the passage bi-encoder $\theta_{\text{bi}}$ , which processes text chunks (e.g., queries or passages) into dense vectors ( Karpukhin et al., 2020 ) offline.
Off-the-shelf retrieval models often struggle in out-of-domain scenarios ( Thakur et al., 2021 ) .
To overcome this limitations, we develop $\theta_{\text{bi}}$ by continually pre-training Contriever ( Izacard et al., 2022 ) on the peS2o datastore in an unsupervised fashion to improve domain-specific retrieval performance (see Appendix C.1 for details).
During inference, we encode the query using $\theta_{\text{bi}}$ and retrieve the top 100 passages through a nearest neighbor search ( Karpukhin et al., 2020 ) .
For (2), we first generate keywords from the query $x$ using a generator LM. These keywords are then used to retrieve the top 10 papers for each, as ranked by citation count, via the Semantic Scholar Search API.
This approach addresses a limitation of the Semantic Scholar API, which cannot effectively handle long, question-like search queries.
For (3), we obtain the top 10 search results using the You.com retrieval API, 3 3 3 https://api.you.com/ restricting the search to academic platforms such as ArXiv and PubMed. If the papers are open-access, we extract and add their full texts to the candidate pool; otherwise, we include only their abstracts.

**中文译文 · 机器初译**

我们从三个来源检索段落：(1) 使用训练好的检索器对 peS2o 数据存储进行检索；(2) 根据搜索关键词，通过 Semantic Scholar API 获取论文的公开摘要（Kinney 等，2023）；(3) 使用原始查询 $x$ 通过网络搜索引擎检索到的论文中的公开文本。对于第 (1) 项，我们首先使用段落双编码器 $\theta_{\text{bi}}$ 以 $\mathbf{D}$ 格式生成每个段落的嵌入向量，该编码器可在离线状态下将文本块（如查询或段落）转换为密集向量（Karpukhin 等，2020）。现成的检索模型通常在领域外场景中表现不佳（Thakur 等，2021）。
为了克服这些限制，我们通过以无监督方式持续在 peS2o 数据存储上预训练 Contriever（Izacard等，2022），从而提升特定领域的检索性能（详情见附录 C.1）。在推理过程中，我们使用 $\theta_{\text{bi}}$ 对查询进行编码，并通过最近邻搜索（Karpukhin等，2020）获取前 100 篇相关段落。对于第（2）项，我们首先使用生成式 LLM从查询中生成关键词 $x$，随后利用 Semantic Scholar 搜索 API，根据引用次数对这些关键词对应的前 10 篇论文进行排序后进行检索。
这种方法解决了 Semantic Scholar API 的一个缺陷，即无法有效处理长且类似问题的搜索查询。对于第(3)项研究，我们利用 You.com 检索 API 获取前10个搜索结果，并将搜索范围限制在 ArXiv 和 PubMed 等学术平台上。如果论文为开放获取，我们会提取其全文并纳入候选库；否则，仅包含其摘要。

待核对标记：formula_or_link_placeholder_missing

### openscholar-0053

**English original**

Rerank and finalize top $N$ paragraphs.

**中文译文 · 机器初译**

重新排序并确定最优秀的段落。

待核对标记：formula_or_link_placeholder_missing

### openscholar-0054

**English original**

After the initial stage, we have gathered over 100, or even a thousand of relevant passages per query. However, passages retrieved by the bi-encoder may include unhelpful context due to deep interactions between a query and passages, as they are encoded separately ( Asai et al., 2023 ) .
Feeding a large number of documents that might including irrelevant content to LLMs can cause efficiency and performance issues, even with state-of-the-art models ( Liu et al., 2024 ; Xu et al., 2023a ) .
To overcome these challenges, we use a cross-encoder reranker ( Nogueira & Cho, 2019 ; Xiao et al., 2023 ) , denoted as $\theta_{\text{cross}}$ . For each candidate paragraph, the cross-encoder reranker jointly encodes and computes the relevance score between the input query and each of the passages. We then use the relevance score to rank the passages accordingly.
To train $\theta_{\text{cross}}$ for scientific domains, we fine-tune a BGE-reranker ( Xiao et al., 2023 ) using synthetic data generated by Llama 3 70B Instruct. Specifically, we randomly generate queries based on abstracts from peS2o and retrieve the top 10 passages. Llama 3 70B Instruct then assigns relevance scores from 1 to 5 for these passages, where we consider scores of 4 or 5 as positive, and scores of 1 or 2 as negative. Passages with a score of 3 are discarded.
More details of $\theta_{\text{cross}}$ training are in Appendix C.2 .
During reranking and finalization of top $N$ passages, we also implement additional meta-filtering, which includes: (1) limiting the number of passages per paper to three passages, and (2) incorporating normalized citation counts into relevance scores predicted by the cross-encoder.

**中文译文 · 机器初译**

在初始阶段之后，我们每次查询都能收集到超过100条甚至上千条相关段落。然而，由于查询与段落之间存在深度交互，由双编码器检索到的段落可能包含无用的上下文信息，因为这些内容是分别编码的（Asai等，2023）。向大语言模型输入大量可能包含无关内容的文档，即使使用最先进的模型也会导致效率与性能问题（Liu等，2024；Xu等，2023a）。为了克服这些挑战，我们使用了一个交叉编码器重排序器（Nogueira & Cho，2019；Xiao等，2023），其标记为$\theta_{\text{cross}}$。
对于每个候选段落，跨编码器重排序器会共同编码输入查询与各个段落之间的相关性得分，然后利用该得分对段落进行排序。为了训练适用于科学领域的 $\theta_{\text{cross}}$，我们使用 Llama 3 70B Instruct 生成的合成数据对 BGE-重排序器（Xiao等人，2023）进行微调。具体而言，我们基于 peS2o 的摘要随机生成查询，并检索前10个段落。随后，Llama 3 70B Instruct 为这些段落分配1到5的相关性得分，其中4或5分视为正面得分，1或2分视为负面得分。得分为3的段落则被排除。
关于 $\theta_{\text{cross}}$ 训练的更多细节见附录 C.2。在重新排序及确定前 $N$ 篇目时，我们还实施了额外的元过滤机制，包括：(1) 每篇论文的篇目数量限制为三篇；(2) 将标准化引用次数纳入交叉编码器预测的相关度得分中。

### openscholar-0055

**English original**

2.2 Inference: Iterative Generation with Retrieval-augmented Self-Feedback

**中文译文 · 机器初译**

2.2 推理：基于检索增强自反馈的迭代生成

### openscholar-0056

**English original**

In standard retrieval-augmented generation (RAG; Lewis et al. 2020 ; Ram et al. 2023 ), a generator LM takes in the original input $x$ and top $N$ retrieved passages $\mathbf{P}$ and generates the output $y_{0}$ . Although effective for tasks such as question answering ( Mallen et al., 2023 ) , this one-step generation can lead to unsupported claims ( Liu et al., 2023 ) or incomplete output due to missing information ( Asai et al., 2024 ; Jiang et al., 2023 ) .
To address these challenges, in OpenScholar , we introduce an iterative generation approach with self-feedback, which involves three steps: (1) initial response and feedback generation to output the initial draft $y_{0}$ and a set of feedback on $y_{0}$ ; (2) iterative refinement with additional retrieval to improve $y_{0}$ using the feedback, and (3) citation verification . Full details are in the Appendix.

**中文译文 · 机器初译**

在标准的检索增强生成（RAG；Lewis等，2020；Ram等，2023）中，生成器大语言模型接收原始输入 $x$，并检索到前 $N$ 个段落 $\mathbf{P}$，进而生成输出 $y_{0}$。尽管这种一步式生成方法适用于问题回答等任务（Mallen等，2023），但可能导致无依据的断言（Liu等，2023）或因信息缺失而产生的不完整输出（Asai等，2024；Jiang等，2023）。
为应对这些挑战，在 OpenScholar 中我们引入了一种包含自我反馈的迭代生成方法，该过程包含三个步骤：(1) 生成初始响应与反馈，以输出初始草稿 $y_{0}$ 以及一组相关反馈 $y_{0}$ ；(2) 通过额外的检索进行迭代优化，利用反馈改进 $y_{0}$ ；(3) 引用验证。详细内容请参阅附录。

### openscholar-0057

**English original**

Initial response and feedback generation.

**中文译文 · 机器初译**

初始响应与反馈生成。

### openscholar-0058

**English original**

Given the input $x$ and retrieved passages $\mathbf{P}$ , the generator LM first produces an initial response $y_{0}$ with citation markers tied to the corresponding passages in $\mathbf{P}$ .
After generating $y_{0}$ , the LM generates a set of feedback on $y_{0}$ , $\mathbf{F}={f_{1},f_{2},\ldots,f_{T}}$ , that is aimed at improving the initial response, wherein each feedback $f_{t}$ is a natural language sentence that describes potential improvements.
Although the model can generate an arbitrary number of feedback ( $T$ ), we set a maximum limit of three feedback sentences for efficient inference.
Unlike prior work that relies on a predefined set of feedback signals ( Asai et al., 2024 ) , our approach allows the LM to generate flexible natural language feedback on various aspects of the response, such as organization, completeness, or additional needed information. If the feedback sequence identifies missing content (e.g., “The answer only includes empirical results on QA tasks. Add results from other task types.”), the LM also generates a retrieval query for additional retrieval using the pipeline in Section 2.1 .

**中文译文 · 机器初译**

给定输入 $x$ 和检索到的段落 $\mathbf{P}$，生成器大语言模型首先生成初始回应 $y_{0}$，并在 $\mathbf{P}$ 中设置与对应段落相关的引用标记。在生成完 $y_{0}$ 后，该模型会在 $y_{0}$ 和 $\mathbf{F}={f_{1},f_{2},\ldots,f_{T}}$ 上生成一组反馈内容，旨在优化初始回应，其中每一条反馈 $f_{t}$ 都是描述潜在改进的自然语言句子。尽管模型可以生成任意数量的反馈（$T$），但我们设定了最多三条反馈句子的上限，以实现高效的推理过程。
与依赖预定义反馈信号集的先前研究（Asai等，2024）不同，我们的方法使大语言模型能够针对回复的多个方面生成灵活的自然语言反馈，例如组织性、完整性或所需补充信息。如果反馈序列识别出缺失内容（例如：“答案仅包含QA任务上的实证结果。请添加其他任务类型的结果。”），大语言模型还会根据第2.1节中的流程生成检索查询以进行额外检索。

### openscholar-0059

**English original**

Iterative refinement.

**中文译文 · 机器初译**

迭代优化。

### openscholar-0060

**English original**

We then iterate over the feedback $\mathbf{F}$ to incrementally refine the output.
If $f_{k}$ indicates that further retrieval is needed, the query $q_{k}$ is used to retrieve additional passages, which are appended to $\mathbf{P}$ before producing $y_{k}$ . 4 4 4 Although we could iteratively regenerate the output each time feedback is provided, doing so introduces additional latency. Empirically, we found that feedback is often diverse, addressing different aspects of generation. As a result, sequentially incorporating feedback from the initial output remains effective. The LM uses the previous output $y_{k-1}$ , the retrieved passages $\mathbf{P}$ , and newly retrieved passages if any, to generate an updated output $y_{k}$ .
This process is repeated until all feedback has been addressed, resulting in a final output $y_{T}$ by timestep $T$ .

**中文译文 · 机器初译**

我们随后对反馈进行迭代处理，以逐步优化输出结果。如果反馈表明需要进一步的检索，则使用查询内容进行额外段落的检索，并将这些段落添加到初始输出中，最终生成最终的文本。虽然每次收到反馈都可以重新生成输出，但这样做会引入额外的延迟。经验表明，反馈往往具有多样性，能够涵盖生成的多个不同方面。因此，依次整合初始输出的反馈仍然有效。
该大语言模型使用之前的输出 $y_{k-1}$、检索到的段落 $\mathbf{P}$，以及任何新检索到的段落，来生成更新后的输出 $y_{k}$。这一过程不断重复，直到所有反馈问题都得到解决，最终在指定时间步长 $T$ 下产生最终输出 $y_{T}$。

待核对标记：formula_or_link_placeholder_missing

### openscholar-0061

**English original**

Citation verification.

**中文译文 · 机器初译**

引用验证。

### openscholar-0062

**English original**

Finally, we instruct the generator LM to verify the citations in $y_{t}$ .
Specifically, the generator ensures that all citation-worthy statements—scientific claims requiring justification—are adequately supported by references from the retrieved passages.
If any claims lack proper citations, the LM performs a post hoc insertion to ensure that citation-worthy statements are supported by passages. In our pipeline, we do not remove sentences that lack citation-worthy statements.

**中文译文 · 机器初译**

最后，我们指示大语言模型验证 $y_{t}$ 中的引用情况。具体而言，该模型会确保所有具有引用价值的陈述——即需要依据支撑的科学主张——都能通过检索到的段落中的参考文献得到充分支持。如果某些陈述缺乏适当的引用，大语言模型会进行事后补充，以确保这些具有引用价值的陈述有相应的段落作为支撑。在我们的处理流程中，我们不会删除那些没有具有引用价值的陈述的句子。

### openscholar-0063

**English original**

2.3 Training: High-quality Synthetic Data Generation with Inference Pipeline

**中文译文 · 机器初译**

2.3 训练：通过推理管道生成高质量合成数据

### openscholar-0064

**English original**

Building powerful LMs that can effectively synthesize scientific literature is challenging due to the lack of training data for this problem. While there are some resources to train scientific LMs ( Wadden et al., 2024 ) , most tasks do not require open-retrieval settings and are single-paper tasks. As a result, most prior work in this area ( Skarlinski et al., 2024 ) rely on proprietary LMs, which poses challenges for reproducibility and inference costs.

**中文译文 · 机器初译**

由于缺乏针对此问题的训练数据，构建能够有效整合科学文献的强大大语言模型具有挑战性。尽管有一些用于训练科学领域大语言模型的资源（Wadden等，2024），但大多数任务并不需要开放检索机制，且均为单篇论文相关任务。因此，该领域的大部分先前研究（Skarlinski等，2024）依赖于专有大语言模型，这给可复现性和推理成本带来了困难。

### openscholar-0065

**English original**

We leverage our inference-time pipeline to synthetically generate high-quality training data through self-feedback, so that the resulting model can get better at generating higher-quality output without going through the self-feedback process (Figure 2 bottom).

**中文译文 · 机器初译**

我们利用推理阶段流程通过自我反馈机制合成高质量训练数据，从而使得最终模型能够在无需进行自我反馈过程的情况下，更擅长生成高质量输出（图2底部）。

### openscholar-0066

**English original**

Question and response generations.

**中文译文 · 机器初译**

问题和回答生成。

### openscholar-0067

**English original**

Our data generation process involves three steps: first, selecting the top-cited papers from $\mathbf{D}$ ; second, generating information-seeking queries based on their abstracts; and third, using the OpenScholar inference-time pipeline to produce high-quality responses.
We generate data using LLama 3.1 70B ( Dubey et al., 2024 ) .
Specifically, we begin by sampling 1 million paper abstracts from the peS2o dataset and the retrieve papers’ meta information such as publication year or citations.
We then randomly select 10,000 papers that published later than 2017, and then prompt an LM to generate literature review questions or information-seeking queries based on each abstract, that may require multiple papers to answer.
Next, we employ our OpenScholar pipeline to produce the final output $y_{T}$ , along with intermediate generations such as feedback $\mathbf{F}$ and initial outputs.

**中文译文 · 机器初译**

我们的数据生成过程包含三个步骤：首先，从 $\mathbf{D}$ 中选取被引用最多的文献；其次，根据这些文献的摘要生成信息查询；最后，利用 OpenScholar 推理阶段管道生成高质量回复。我们使用 LLama 3.1 70B 模型进行数据生成（Dubey 等，2024）。具体而言，我们首先从 peS2o 数据集中抽取100万篇论文的摘要，并提取这些被检索文献的元数据，如发表年份或引用次数。
然后我们随机选取了10,000篇2017年之后发表的论文，接着引导大语言模型根据每篇摘要生成文献综述问题或信息查询需求，这些问题可能需要多篇论文才能解答。接下来，我们使用OpenScholar流程生成最终输出$y_{T}$，同时还会生成反馈$\mathbf{F}$和初始输出等中间结果。

### openscholar-0068

**English original**

Data filtering.

**中文译文 · 机器初译**

数据筛选。

### openscholar-0069

**English original**

Despite its effectiveness and scalability, synthetic data may also contain issues such as hallucinations, repetitive writing, or limited instruction-following ( Li et al., 2024c ) .
To address this, we introduce a two-step data filtering process: pairwise-filtering and rubric-filtering, leveraging the same LM used for data generation.
In pair-wise filtering, we compare the quality of model outputs $y_{T}$ (output at the final step) and $y_{0}$ (initial output), and retain the output that is judged to be higher quality.
We find that $y_{0}$ is preferred over $y_{T}$ around 20% of the time, due to over-editing or increased redundancy after multiple iteration steps.
We then evaluate the quality of the chosen response on a five-point scale across two aspects: organization and factual precision and citation accuracy . A valid model output must achieve a score of 4.5 or higher in both categories, and we discard instances whose outputs do not meet this requirement. More details are provided in the Appendix.

**中文译文 · 机器初译**

尽管大语言模型具有高效性和可扩展性，但合成数据也可能存在幻觉、重复写作或指令遵循能力有限等问题（Li等，2024c）。为解决这些问题，我们引入了两步数据过滤机制：成对过滤与评分标准过滤，并使用与数据生成相同的大语言模型。在成对过滤过程中，我们对比模型输出的质量——$y_{T}$（最终步骤的输出）与$y_{0}$（初始输出），并保留被判定为质量更高的输出。我们发现，由于多次迭代后的过度编辑或冗余现象，约20%的情况下更倾向于选择$y_{0}$而非$y_{T}$。
我们随后在五个等级范围内，从组织结构和事实准确性及引用精度两个方面对所选回答的质量进行评估。有效的模型输出必须在这两个类别中均达到4.5或更高的分数，我们将那些输出不符合此要求的实例排除在外。更多细节请参见附录。

### openscholar-0070

**English original**

Data mixing and training.

**中文译文 · 机器初译**

数据混合与训练。

### openscholar-0071

**English original**

From this synthetic pipeline, we generate three types of training data: answer generation $(x\rightarrow y)$ , feedback generation $(y_{0}\rightarrow\mathbf{F})$ , and feedback incorporation $(y_{t-1},f_{t}\rightarrow y_{t})$ . We found that incorporating both final and intermediate outputs during training helps smaller LMs learn to generate more effective feedback.
We further blend this synthetic training data with existing general-domain instruction-tuning data ( Ivison et al., 2023 ) and scientific instruction-tuning data ( Wadden et al., 2024 ) , ensuring that 50% of the training data comes from scientific domains, while the remaining 50% is sourced from general-domain data.
We also generate synthetic fact verification and boolean QA data based on sampled abstract data from peS2o. For this, we sort the papers based on citation count and select the top 100,000 papers.
More details of data mixing and training are available at Appendix C.3 .
After data mixing, we train generator LMs on our large-scale synthetic training data. We train Llama 3.1 8B Instruct on the generated training data.

**中文译文 · 机器初译**

基于这一合成训练流程，我们生成了三种类型的训练数据：答案生成 $(x\rightarrow y)$、反馈生成 $(y_{0}\rightarrow\mathbf{F})$ 以及反馈整合 $(y_{t-1},f_{t}\rightarrow y_{t})$。我们发现，在训练过程中同时使用最终输出与中间输出有助于较小的大语言模型学会生成更有效的反馈。我们进一步将这种合成训练数据与现有的通用领域指令调整数据（Ivison等，2023）及科学领域指令调整数据（Wadden等，2024）进行融合，确保 50% 的训练数据来自科学领域，而剩余 50% 则来自通用领域数据。
我们还基于 peS2o 中抽样的摘要数据生成合成事实验证及布尔式问答数据。为此，我们按引用次数对论文进行排序，选取前 100,000 篇论文。关于数据混合与训练的更多细节，请参见附录 C.3。数据混合完成后，我们在大规模合成训练数据上训练生成器 LLM。随后，我们在生成的训练数据上训练 Llama 3.1 8B Instruct。

### openscholar-0072

**English original**

3 ScholarQABench : Realistic Literature Review Evaluation Benchmark annotated by Ph.D. Experts

**中文译文 · 机器初译**

3 ScholarQABench：由博士专家标注的现实化文献综述评估基准

### openscholar-0073

**English original**

Challenges and overview.

**中文译文 · 机器初译**

挑战与概述。

### openscholar-0074

**English original**

Prior studies on building LLMs to synthesize scientific literature employ either small-scale, single-domain human evaluation ( Agarwal et al., 2024 ; Zheng et al., 2024 ) or over-simplified multiple-choice QA setups ( Skarlinski et al., 2024 ) .
Building high-quality benchmarks for literature review has two major challenges. First, creating such datasets is resource-intensive, as it requires Ph.D.-level domain expertise and research experience, particularly when annotating realistic questions and high-quality answers. Second, even when high-quality data is available, reliably evaluating long-form natural language responses presents a significant challenge, especially in expert domains ( Xu et al., 2023b ; Xu et al., 2024 ) . This contrasts with benchmarks for other scientific processes, such as automated experimental code generation, for which clearer evaluation criteria, such as Pass@1, are more readily available ( Si et al., 2024 ) .

**中文译文 · 机器初译**

先前关于构建大语言模型以综合科学文献的研究，要么采用小规模、单一领域的人工评估方法（Agarwal等，2024；Zheng等，2024），要么使用过于简化的选择题问答模式（Skarlinski等，2024）。构建高质量的文献综述基准数据存在两个主要挑战：首先，创建此类数据集需要大量资源，因为需要博士级别的领域专业知识和研究经验，尤其是对真实问题及高质量答案进行标注时。
其次，即使拥有高质量数据，要可靠地评估长文本自然语言回答仍然面临重大挑战，尤其是在专家领域（Xu等，2023b；Xu等，2024）。这与其他科学过程的评估基准不同，例如自动化实验代码生成，后者更容易获得更明确的评估标准，如Pass@1（Si等，2024）。

### openscholar-0075

**English original**

To address these gaps, we introduce ScholarQABench , a benchmark that supports diverse formats of scientific literature synthesis tasks, including closed-form classification, multiple-choice, and long-form generation, as shown in Table 1 .
We adopt three existing single-paper datasets, and then construct a suite of high-quality, expert annotated datasets for computer science, biomedicine, physics, and neuroscience (Section 3.1 ). We also build a reliable automatic evaluation pipeline (Section 3.2 ).
Table 1 provides a list of tasks in ScholarQABench , and Figure 3 shows an example and an overview of the evaluation pipeline.

**中文译文 · 机器初译**

为了填补这些空白，我们引入了 ScholarQABench 这一基准测试工具，该工具支持多种科学文献综合任务形式，包括封闭式分类、选择题以及长文生成，如表1所示。我们采用了三个现有的单篇论文数据集，随后构建了用于计算机科学、生物医学、物理学和神经科学领域的高质量、专家标注数据集（第3.1节）。我们还建立了可靠的自动评估流程（第3.2节）。表1列出了 ScholarQABench 中的任务列表，图3则展示了评估流程的示例及整体概况。

### openscholar-0076

**English original**

Dataset | Task Format | Discipline | Size | Evaluation | Multi-paper
SciFact | Claim $\rightarrow$ Label | Biomedicine | 208 | Corr , Cite | 
( Wadden et al. 2020 ) | (True or False) | | | | 
PubMed QA | Question $\rightarrow$ Answer | Biomedicine | 843 | Corr , Cite | 
( Jin et al. 2019 ) | (Yes, No) | | | | 
QASA | Question $\rightarrow$ Answer | Computer Science | 1,375 | Corr , Cite | 
( Lee et al. 2023 ) | (Long-form) | | | | 
ScholarQA-CS | Question $\rightarrow$ Answer † | Computer Science | 100 | Corr , Cite | ✓
 | (Long-form) | | | 
ScholarQA-Bio | Question $\rightarrow$ Answer ∗ | Biomedicine | 1,451 | Cite | ✓
 | (Long-form) | | | 
ScholarQA-Neuro | Question $\rightarrow$ Answer ∗ | Neuroscience | 1,308 | Cite | ✓
 | (Long-form) | | | 
ScholarQA-Multi | Question $\rightarrow$ Answer | Computer Science, Physics, | 108 | Cite , | ✓
 | (Long-form) | Biomedicine | | LLM , Expert

**中文译文 · 机器初译**

Dataset | Task Format | Discipline | Size | Evaluation | Multi-paper
SciFact | Claim $\rightarrow$ Label | Biomedicine | 208 | Corr , Cite | 
( Wadden et al. 2020 ) | (True or False) | | | | 
PubMed QA | Question $\rightarrow$ Answer | Biomedicine | 843 | Corr , Cite | 
( Jin et al. 2019 ) | (Yes, No) | | | | 
QASA | Question $\rightarrow$ Answer | Computer Science | 1,375 | Corr , Cite | 
( Lee et al. 2023 ) | (Long-form) | | | | 
ScholarQA-CS | Question $\rightarrow$ Answer † | Computer Science | 100 | Corr , Cite | ✓
 | (Long-form) | | | 
ScholarQA-Bio | Question $\rightarrow$ Answer ∗ | Biomedicine | 1,451 | Cite | ✓
 | (Long-form) | | | 
ScholarQA-Neuro | Question $\rightarrow$ Answer ∗ | Neuroscience | 1,308 | Cite | ✓
 | (Long-form) | | | 
ScholarQA-Multi | Question $\rightarrow$ Answer | Computer Science, Physics, | 108 | Cite , | ✓
 | (Long-form) | Biomedicine | | LLM , Expert

表内文字对照（数值与原始行列保持不变）：
Dataset → 数据集
Task Format → 任务格式
Discipline → 学科
Size → 规模
Evaluation → 评估
Multi-paper → 多篇论文
SciFact → SciFact
Claim → 主张
rightarrow → →
Label → 标签
Biomedicine → 生物医学
Corr → Corr
Cite → 引用
Wadden et al → Wadden等人
True or False) → 正确或错误）
PubMed QA → PubMed QA
Question → 问题
Answer → 回答
Jin et al → 金等人
Yes → 是
No) → 否)
QASA → QASA
Computer Science → 计算机科学
Lee et al → 李等人
Long-form) → 长文形式）
ScholarQA-CS → ScholarQA-CS
ScholarQA-Bio → ScholarQA-Bio
ScholarQA-Neuro → ScholarQA-Neuro
Neuroscience → 神经科学
ScholarQA-Multi → ScholarQA-Multi
Physics → 物理学
LLM → 大语言模型
Expert → 专家

### openscholar-0077

**English original**

Table 1: Overview of ScholarQABench . The top three rows show single-paper datasets adopted from prior datasets.
The bottom four rows are new datasets, which we constructed by recruiting Ph.D.-level experts.
Answer ∗ indicates that the dataset comes with questions only, and answer † indicates that answer will be evaluated based on human-annotated rubrics.
The evaluation columns corresponds to the multi-faceted evaluations in Section 3.2 . The “Multi-paper” column indicates whether the task requires multiple papers to answer. LLM and Expert indicate the fine-grained evaluations by evaluator LLMs (i.e., Prometheus; Kim et al. 2024a ) and expert humans, respectively.

**中文译文 · 机器初译**

表1：ScholarQABench概述。前三行展示了从先前数据集中提取的单篇论文数据集；后四行则是我们通过招募博士级别专家构建的新数据集。回答∗表示该数据集仅包含问题，而回答†则表示答案将依据人工标注的评分标准进行评估。评估列对应第3.2节中的多维度评估方式。“多篇论文”列则表明任务是否需要使用多篇论文来作答。LLM和Expert分别指由评估大语言模型LLM（即Prometheus；Kim等人，2024a）和人类专家进行的细粒度评估。

### openscholar-0078

**English original**

3.1 Data Curation

**中文译文 · 机器初译**

3.1 数据整理

### openscholar-0079

**English original**

ScholarQABench is designed to evaluate model capabilities in automating scientific literature review. The curation process is guided by three key factors: Diversity of tasks : ScholarQABench includes tasks with a range of input-output formats; Diversity of disciplines : Unlike previous analyses that often focus on a single discipline such as computer science, ScholarQABench spans four scientific disciplines; Inclusion of multi-paper tasks : Unlike prior work that focuses on understanding single, pre-selected papers, all tasks require retrieving from the entire open-access collection of full text of papers (Section 3.1.1 )
and four datasets specifically require reasoning over multiple retrieved papers (Section 3.1.2 ).

**中文译文 · 机器初译**

ScholarQABench旨在评估大语言模型在自动化科学文献综述方面的能力。其筛选过程由三个关键因素指导：任务多样性：ScholarQABench包含多种输入输出格式的任务；学科多样性：与通常仅关注计算机科学等单一学科的先前研究不同，ScholarQABench涵盖了四个科学领域；多篇论文任务的纳入：与仅针对已预先选定的单篇论文进行研究的先前工作不同，所有任务都需要从完整的开放获取论文全文集合中检索数据（第3.1.1节）
以及四个数据集特别要求对多个检索到的论文进行推理分析（第3.1.2节）。

### openscholar-0080

**English original**

3.1.1 Single-Paper Tasks

**中文译文 · 机器初译**

3.1.1 单篇论文任务

### openscholar-0081

**English original**

For single-paper tasks, we curate and adapt existing widely-used single-paper datasets. Figure 15 shows examples of single-paper tasks; more details are in Appendix B.2 .

**中文译文 · 机器初译**

对于单篇论文任务，我们筛选并调整了现有的常用单篇论文数据集。图15展示了单篇论文任务的示例；更多细节见附录B.2。

### openscholar-0082

**English original**

SciFact.

**中文译文 · 机器初译**

SciFact。

### openscholar-0083

**English original**

SciFact ( Wadden et al., 2020 ) is a dataset of 1.4K expert-written scientific claims in the biomedical domain, paired with gold evidence from existing PubMed paper abstracts annotated with labels and rationales.
We include validation set queries labeled as either supports (true) or contradicts (false), discarding the original gold evidence, and reformulate the task as binary open-retrieval, wherein a system needs to identify relevant papers from a large collection of papers.

**中文译文 · 机器初译**

SciFact（Wadden等，2020）是一个包含1.4K篇由专家撰写的生物医学领域科学论断的数据集，这些论断与带有标签和解释说明的现有PubMed论文摘要中的黄金证据相对应。我们包含了被标记为“支持”（正确）或“矛盾”（错误）的验证集查询，并删除了原始黄金证据，将任务重新设计为二元检索任务，即系统需要从大量论文中识别出相关的论文。

### openscholar-0084

**English original**

PubMedQA.

**中文译文 · 机器初译**

PubMedQA。

### openscholar-0085

**English original**

PubMedQA ( Jin et al., 2019 ) has expert-annotated (yes/no/maybe) QA data on PubMed paper abstracts.
Similarly to SciFact, we only keep instances with yes or no labels, and discard the original abstract passage to formulate the task as an open-retrieval setup.

**中文译文 · 机器初译**

PubMedQA（Jin等，2019）包含来自PubMed论文摘要的由专家标注的（是/否/可能）问答数据。与SciFact类似，我们仅保留带有“是”或“否”标签的数据样本，并丢弃原始摘要段落，从而将任务构建为一种开放检索模式。

### openscholar-0086

**English original**

QASA.

**中文译文 · 机器初译**

QASA。

### openscholar-0087

**English original**

QASA ( Lee et al., 2023 ) is a single paper QA dataset that consists of question answering pairs, requiring reasoning over scientific articles in AI and ML.
We evaluate the model’s ability to sufficiently answer a detailed question about the target paper. While the original dataset provides three subtasks (answer selection, rationale generation and answer compositions) as well as end-to-end QA, we evaluate the models’ performance based on an end-to-end QA setup.

**中文译文 · 机器初译**

QASA（Lee等人，2023年）是一个单一的文献综述QA数据集，包含问题回答对，需要针对人工智能与机器学习领域的科学文章进行推理。我们评估模型能否充分回答关于目标文献的详细问题。虽然原始数据集包含三个子任务（答案选择、理由生成及答案组合）以及端到端QA机制，但我们基于端到端QA设置来评估模型的性能。

### openscholar-0088

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0089

**English original**

Figure 3: An ScholarQA-CS example and evaluation overview. ScholarQA-CS consists of 100 questions and an average of 4.4 expert-written rubrics to be satisfied. Our ScholarQABench evaluation pipeline evaluates aspects like correctness and citation accuracy.

**中文译文 · 机器初译**

图3：ScholarQA-CS示例及评估概览。ScholarQA-CS包含100道问题，以及平均4.4份专家编写的评分标准作为评估依据。我们的ScholarQABench评估流程会考量正确性与引用精度等指标。

### openscholar-0090

**English original**

3.1.2 Multi-paper Tasks

**中文译文 · 机器初译**

3.1.2 多篇论文任务

### openscholar-0091

**English original**

Single-paper, closed-set tasks may provide reliable evaluations. However, they may not be reflective of realistic scenarios, in which complex, open-ended questions are asked independently from existing papers, and require multi-paper retrieval and reasoning.
Few datasets ( Xu et al., 2024 ; Malaviya et al., 2023 ) explore multi-paper setups with realistic queries, and most lack a reliable evaluation pipeline or human-written references. We address this gap by curating three new long-form QA datasets, annotated by experts, for these challenging settings (details in Appendix B.2 ).
Furthermore, our multi-paper tasks include four scientific disciplines.

**中文译文 · 机器初译**

单篇论文的封闭集任务或许能够提供可靠的评估结果。然而，它们可能无法反映现实场景——在现实场景中，复杂的开放式问题会独立于现有论文被提出，并需要跨多篇论文的检索与推理。目前很少有数据集（Xu等人，2024；Malaviya等人，2023）涉及包含真实查询的多篇论文设置，且大多数缺乏可靠的评估流程或人工编写的参考文献。我们通过整理三个由专家标注的新长格式问答数据集来填补这一空白，以应对这些具有挑战性的场景（详情见附录B.2）。此外，我们的多篇论文任务涵盖了四个科学领域。

### openscholar-0092

**English original**

ScholarQA-CS .

**中文译文 · 机器初译**

ScholarQA-CS

### openscholar-0093

**English original**

We collected 100 questions along with detailed answer rubrics for each question across various computer science disciplines by recruiting expert annotators holding Ph.D.s in the field (professors, postdoctoral researchers, and research scientists).
Annotators were tasked with writing literature review questions that were expected to require multiple research papers to answer.
The question topics span areas such as networks, algorithms, the Internet of Things, artificial intelligence, and human-computer interaction.
Then, for each question, two other annotators searched the Web to produce a rubric listing the key ingredients for a correct answer, categorized by importance (“must-have” and “nice-to-have”), along with supporting quotes from sources for each ingredient. The annotators were instructed not to use any LLM services for this initial part of the task. After the initial web search, the annotators were shown corresponding responses from four LLM services (Claude 3.5 Sonnet, GPT-4o, Perplexity Pro and an unpublished RAG prototype based on Claude 3.5) in a randomized order in case they wanted to revise their rubrics. On average, each question is annotated with 4.4 key ingredients, each supported by 4.4 quotes.

**中文译文 · 机器初译**

我们招募了该领域的博士专家——包括教授、博士后研究员和研究科学家——收集了来自多个计算机科学学科的100个问题以及每个问题的详细答案评分标准。这些注释者的任务是撰写需要结合多篇研究论文才能解答的文献综述问题，问题主题涵盖网络、算法、物联网、人工智能和人机交互等领域。
然后，针对每个问题，另外两位注释者通过网络搜索，制定了一份评分标准，其中列出了正确回答的关键要素及其重要性等级（“必须包含”与“理想包含”），并提供了各要素的相关来源引用。注释者被要求在任务初期阶段不使用任何大语言模型服务。在初步网络搜索之后，注释者会以随机顺序看到来自四种大语言模型服务的相应回复（Claude 3.5 Sonnet、GPT-4o、Perplexity Pro以及基于Claude 3.5的未发表RAG原型），以便他们能够修改自己的评分标准。
平均而言，每个问题都包含 4.4 个关键要素，且每个要素都有 4.4 条引用支持。

### openscholar-0094

**English original**

To measure agreement, we had both annotators produce rubrics for a subset of 10 randomly sampled questions. We then compute the scores for responses from the four LLM services the annotators were exposed to using our automated approach, once for each set of annotator rubrics. Finally, we compute Pearson’s correlation coefficient among the scores for each question and take the mean. Since the rubric annotation task is subjective, we compute this agreement both with and without the general criterion as part of the scores, which comes out to be 79.3 and 59.5, respectively.
Figure 3 shows one example, and more examples and details are available in Appendix E.2 .

**中文译文 · 机器初译**

为了衡量一致性，我们让两位注释者为随机选取的10道问题样本分别制定评分标准。随后，使用自动化方法对注释者所接触的4种大语言模型服务的回答进行评分，每套评分标准对应一次计算。最后，我们计算了各题得分之间的皮尔逊相关系数并取平均值。由于评分标准注释任务具有主观性，我们在得分中同时纳入了通用标准和不纳入的情况，结果分别为79.3和59.5。图3展示了一个示例，更多示例及详细内容见附录E.2。

### openscholar-0095

**English original**

ScholarQA-Bio , ScholarQA-Neuro .

**中文译文 · 机器初译**

ScholarQA-Bio、ScholarQA-Neuro

### openscholar-0096

**English original**

We further collected 2,759 expert-written literature review questions in biomedicine and neuroscience, recruiting six experts who have a Ph.D. in relevant areas and are currently research scientists and engineers.
The annotators were asked to choose papers from their area of expertise, and generate complex scientific questions that biomedical scientists might reasonably ask about the scientific literature based upon their parsing of those papers. We collected questions from different areas, such as bioimaging, genetics, microbiology, and neuromodulation for each.
Due to the cost of annotation, we focused solely on curating the questions.
Full instructions and examples are available in Appendix 6 and E.3 .

**中文译文 · 机器初译**

我们进一步收集了2,759个由专家撰写的生物医学与神经科学领域的文献综述问题，这些专家均为相关领域拥有博士学位的研究科学家和工程师。标注人员被要求从自己的专业领域中选择论文，并根据对这些论文的解析，提出生物医学科学家可能提出的复杂科学问题。我们针对生物成像、遗传学、微生物学及神经调节等不同领域分别收集了相关问题。由于标注成本较高，我们仅专注于对这些问题进行整理与筛选。
完整说明与示例可在附录 6 和 E.3 中找到。

### openscholar-0097

**English original**

ScholarQA-Multi .

**中文译文 · 机器初译**

ScholarQA-Multi.

### openscholar-0098

**English original**

Lastly, we collected 108 literature review questions and expert-written answers with citations in four domains: computer science (AI/ML, HCI), Biomedicine (Bioimaging, Genetics), Physics (Astrophysics, Photonics, Bio Physics).
All annotations are conducted by Ph.D. students or post-Ph.D. scientists, who have more than three years of research experience in the corresponding areas and have multiple first-author publications.
We asked them to come up with questions that are related to most recent literature, and to compose answers to the questions using relevant papers that they found via search. Our annotators were instructed not to use any LLM-based systems such as ChatGPT, and told to only use general search (e.g., Google Search) or paper search systems (e.g., Semantic Scholar).
Table 14 show statistics of the collected questions and answers and the distribution of subjects are in Figure 6(a) , along with the average annotation time per subject. We show several examples in Appendix E.4 .
On average, each annotator spent 56 minutes per instance.

**中文译文 · 机器初译**

最后，我们收集了108个文献综述问题以及由专家撰写的带有引用信息的答案，这些内容涉及四个领域：计算机科学（人工智能/机器学习、人机交互）、生物医学（生物成像、遗传学）、物理学（天体物理、光子学、生物物理学）。所有注释工作由拥有相应领域三年以上研究经验且有多篇第一作者论文的博士学生或博士后科学家完成。我们要求他们提出与最新文献相关的问题，并利用通过搜索找到的相关论文来撰写这些问题的解答。
我们的标注人员被要求不得使用任何基于大语言模型的系统，如 ChatGPT，并且只能使用常规搜索工具（例如 Google 搜索）或文献搜索系统（例如 Semantic Scholar）。表 14 展示了所收集的问题与答案的统计数据，各主题的分布情况见图 6(a)，同时还有每个主题的平均标注时间。我们在附录 E.4 中提供了几个示例。平均而言，每位标注人员处理每个实例需要 56 分钟。

### openscholar-0099

**English original**

3.2 Metrics and Evaluation Protocols

**中文译文 · 机器初译**

3.2 指标与评估方案

### openscholar-0100

**English original**

We developed a multifaceted automatic evaluation pipeline to facilitate reproducible and efficient evaluations, complementing expert assessments. An overview of our evaluations is in Figure 3 .

**中文译文 · 机器初译**

我们开发了一种多维度自动评估流程，以实现可重复且高效的评估工作，从而补充专家评估的作用。我们的评估结果大纲见图3。

### openscholar-0101

**English original**

Correctness ( Corr ).

**中文译文 · 机器初译**

正确性（Corr）。

### openscholar-0102

**English original**

Correctness evaluates the degree of overlap or matching of a model-generated answer and human-annotated reference. This metric is only applied to tasks with human-annotated reference answers.
For short-form generation tasks given a fixed set of answer classes, namely SciFact and PubMedQA, we use accuracy as the correctness metric.
For QASA, we use ROUGE-L as an evaluation metric, following Lee et al. (2023) .
For ScholarQA-CS , we develop a new long-form evaluation pipeline, which employs expert-annotated rubrics. Each rubric has two criteria: general (accounting for 40% of the score) and annotation-driven (60%).
General criteria cover the evaluation of length, expertise, citations, and excerpts, while annotation-driven criteria involve assessing the presence of specific key ingredients identified by annotators. GPT4o-turbo assigns scores for each criterion, and a weighted sum is computed to obtain a final score.
More details are in appendix B.3.1 .

**中文译文 · 机器初译**

正确性指标用于衡量模型生成的答案与人工标注的参考内容之间的重叠或匹配程度。该指标仅适用于包含人工标注答案的任务。对于给定固定答案类别的短格式生成任务，即 SciFact 和 PubMedQA，我们采用准确率作为正确性指标。对于 QASA，我们遵循 Lee 等（2023）的研究方法，使用 ROUGE-L 作为评估指标。对于 ScholarQA-CS，我们开发了一种新的长格式评估流程，该流程采用专家标注的评分标准，每个评分标准包含两个维度：通用维度（占得分的 40%）和标注驱动维度（占 60%）。
一般标准包括长度、专业水平、引用次数和摘录内容的评估，而基于注释的标准则涉及对注释者所确定的特定关键要素的考察。GPT4o-turbo会对每个标准进行评分，然后计算加权总和以得出最终得分。更多细节见附录B.3.1。

### openscholar-0103

**English original**

Citation accuracy ( Cite ).

**中文译文 · 机器初译**

引用准确性（Cite）。

### openscholar-0104

**English original**

Evaluating long-form responses to literature review questions requires citation accuracy: LMs should correctly attribute relevant evidence for all citation-worthy statements. In ScholarQABench , all systems generate outputs with reference numbers (e.g., [1], [2] ) linked to passages provided during inference. Following prior work ( Gao et al., 2023 ; Liu et al., 2023 ) , we measure citation precision and recall. Specifically, we check if each citation-worthy statement has appropriate citations and if the citations support the statement ( Citation Recall , Cite -r).
For each citation, we then verify its relevance and necessity—specifically, whether the citation supports the statement and if its removal impacts the integrity of remaining citations ( Citation Precision , Cite -p).
Finally, we compute Citation F1 ( Cite -F1) as well, and use it as a primarily metric for citation accuracy.
Citation accuracy does not require gold reference answers or rubrics, so we apply this evaluation across all tasks.

**中文译文 · 机器初译**

对文献综述问题的长文回答进行评估需要引用准确性：大语言模型应正确标注所有具有引用价值的陈述所对应的相关证据。在 ScholarQABench 中，所有系统生成的输出都包含与推理过程中提供的段落相连接的引用编号（例如 [1]、[2]）。借鉴之前的研究（Gao等人，2023；Liu等人，2023），我们测量了引用精确度和召回率。具体而言，我们检查每个具有引用价值的陈述是否拥有适当的引用，以及这些引用是否能够支持该陈述（引用召回率，Cite-r）。
对于每一条引用，我们进一步验证其相关性和必要性——即该引用是否支持相关陈述，以及删除该引用是否会影响其余引用的完整性（引用精确性，Cite -p）。最后，我们还计算了引用F1值（Cite -F1），并将其作为衡量引用准确性的主要指标。由于引用准确性无需金标准参考答案或评分标准，因此我们在所有任务中均采用这一评估方法。

### openscholar-0105

**English original**

Content quality and organization ( LLM , Expert ).

**中文译文 · 机器初译**

内容质量与结构（大语言模型，专家）。

### openscholar-0106

**English original**

We further define key aspects to evaluate the generated answers beyond Corr or Cite alone. Specifically, we assess Relevance ( Rel ) to the question, Coverage ( Cov ) of topics (e.g., diversity of discussed papers) and depth (e.g., sufficiency of details), and Organization and Writing Flow ( Org ). These aspects are challenging to capture with standard metrics.
Since LMs can effectively follow detailed evaluation rubrics ( Zheng et al., 2023a ; Kim et al., 2024a ) , we use Prometheus v2 ( Kim et al., 2024a ) to assign five-scale scores based on defined rubrics and use the same schema for human evaluations. For human evaluation, we further evaluate Overall Usefulness ( Use ).
Full instructions for this evaluation are provided in the Appendix B.3 .
As prior studies show that LLM is less reliable when gold reference answers are not available ( Kim et al., 2024b ) , this evaluation is only applied to a task with human-annotated reference answer, namely ScholarQA-Multi .
We analyzed the agreement between human and model assessments on fine-grained aspects (Appendix D.2 ) and found that the model’s evaluations often align with human rankings, showing higher correlation especially in organization and coverage.

**中文译文 · 机器初译**

我们进一步定义了除了“相关度”或“引用量”之外用于评估生成答案的关键指标。具体而言，我们考察了与问题的相关性（Rel）、话题覆盖度（如所讨论论文的多样性）以及深度（如细节的充分性），还有组织结构与写作流畅性（Org）。这些指标很难用标准指标来衡量。由于大语言模型能够有效遵循详细的评估评分标准（Zheng等，2023a；Kim等，2024a），我们采用Prometheus v2（Kim等，2024a）根据定义的评分标准分配五级评分，并采用相同的框架进行人工评估。在人工评估中，我们还进一步考察了整体实用性（Use）。
此评估的完整说明见附录 B.3。正如先前研究所示，当没有黄金参考答案时，大语言模型的可靠性较低（Kim等人，2024b），因此本次评估仅适用于包含人类标注参考答案的任务，即ScholarQA-Multi。我们分析了人类评估与模型评估在细致方面的一致性（附录 D.2），发现模型的评估结果往往与人类的排名一致，尤其是在组织和覆盖度方面具有更高的相关性。

### openscholar-0107

**English original**

4 Experiments and Results

**中文译文 · 机器初译**

4 实验与结果

### openscholar-0108

**English original**

4.1 Experimental Details

**中文译文 · 机器初译**

4.1 实验细节

### openscholar-0109

**English original**

Models.

**中文译文 · 机器初译**

模型。

### openscholar-0110

**English original**

First, we evaluate both open-weight and proprietary LMs, including Llama 3.1 (8B, 70B) and GPT-4o ( gpt-4o-2024-05-13 ). In this setup, each LM generates an answer independently, without external retrieval, and provides a list of referenced paper titles. For evaluation, we verify whether the generated paper titles exist. If they do, we retrieve their corresponding abstracts to use as citations.
For multi-paper tasks, we further evaluate other proprietary systems: Perplexity Pro, 5 5 5 https://www.perplexity.ai/ . We used the paid subscription version for the experiments. Note that Perplexity Search does not have an API, so we use the selenium toolkit and save their final prediction results from the interface. Due to this, we could not retrieve their citation information. and PaperQA2 ( Skarlinski et al., 2024 ) , a concurrent literature review agent system that uses GPT4o for reranking, summarization, and answer generation. 6 6 6 We use their official codebase. As PaperQA2 does not release their retrieval corpus and requires downloading PDF files offline, we downloaded PDF files of papers suggested by our retrieval pipelines and the Semantic Scholar API. Unlike PaperQA2, we do not have access to private or license-protected papers, which may limit the effectiveness of our replication to some extent. Then, we evaluate models using our OpenScholar-DataStore (+OSDS), where we retrieve the top $N$ passages, and concatenate and feed them together with the original input.
Lastly, we evaluate our proposed OpenScholar , leveraging our custom inference-time pipeline using trained 8B model models ( OS-8B ), as well as Llama 3.1 70B and GPT4o ( OS-70B , OS-GPT4o ).

**中文译文 · 机器初译**

首先，我们评估了开放版与专有版大语言模型，包括 Llama 3.1（8B、70B）和 GPT-4o（gpt-4o-2024-05-13）。在这种设置下，每个大语言模型独立生成答案，无需外部检索，并提供一份引用的文献标题列表。为了进行评估，我们核实所生成的文献标题是否存在；如果存在，则检索其对应的摘要作为引用。对于多篇文献任务，我们还对其他专有系统进行了评估：Perplexity Pro、5 5 5  https://www.perplexity.ai/。实验采用了付费订阅版本。
请注意，Perplexity Search没有API接口，因此我们使用selenium工具包从界面中获取其最终预测结果。由于此原因，我们无法检索到其引用信息。而PaperQA2（Skarlinski等人，2024年）是一种同时进行的文献综述智能体系统，它使用GPT4o进行重新排序、摘要生成和答案生成。我们使用了他们的官方代码库。由于PaperQA2不公开其检索语料库，且需要离线下载PDF文件，所以我们下载了由我们的检索管道及Semantic Scholar API推荐的论文的PDF文件。
与 PaperQA2 不同，我们无法获取私有或受许可保护的文献，这可能会在一定程度上限制我们复现研究的有效性。然后，我们使用 OpenScholar-DataStore (+OSDS) 对模型进行评估，在该系统中我们检索出排名前 $N$ 的段落，并将其与原始输入拼接后输入模型。最后，我们利用自定义的推理时间管道以及训练好的 8B 模型（OS-8B）、Llama 3.1 70B 和 GPT4o（OS-70B、OS-GPT4o）来评估我们提出的 OpenScholar 模型。

### openscholar-0111

**English original**

Details of OpenScholar .

**中文译文 · 机器初译**

OpenScholar 的详细信息。

### openscholar-0112

**English original**

We use peS2o v2 as our default datastore $\mathbf{D}$ . We analyze the effect of different datastores in Appendix D.1 .
For $\theta_{\text{bi}}$ and $\theta_{\text{cross}}$ in OpenScholar , we use our trained bi-encoder and cross-encoder models, which consist of 110 million and 340 million parameters, respectively. We set the maximum number of papers from web search and Semantic Scholar to 10.
For the generator LMs, we set the temperature to 0.7 and limit the maximum token count to 3,000 for response generation and 1,000 for feedback generation, and use the vllm package for faster inference. We train Llama 3.1 8B for two epochs on 130k training instances for two epochs, using torchtune .
Further details are in Appendix C .
For all models, we set the number of passages input into the generator LM to five for single-paper tasks and ten for multi-paper tasks. No few-shot demonstrations are provided, except for SciFact and PubMed, where we include one-shot demonstrations.

**中文译文 · 机器初译**

我们采用 peS2o v2 作为默认数据存储系统。不同数据存储方式的影响在附录 D.1 中进行了分析。在 OpenScholar 中的 $\theta_{\text{bi}}$ 和 $\theta_{\text{cross}}$ 部分，我们使用经过训练的双编码器和交叉编码器模型，分别包含 1.1 亿和 3.4 亿参数。我们将从网络搜索和 Semantic Scholar 中检索的论文数量上限设定为 10 篇。对于生成式 LLM，我们将温度参数设为 0.7，并将响应生成的最大令牌数限制为 3,000，反馈生成的最大令牌数限制为 1,000，同时使用 vllm 包以加快推理速度。我们使用 torchtune 在 13 万个训练样本上训练了两个周期的 Llama 3.1 8B 模型。
更多细节见附录 C。对于所有模型，我们在单篇论文任务中设置输入给生成式大语言模型的段落数为五段，在多篇论文任务中则设置为十段。除了 SciFact 和 PubMed 外，未提供少样本演示，而在这些领域我们提供了单样本演示。

待核对标记：formula_or_link_placeholder_missing

### openscholar-0113

**English original**

4.2 Results

**中文译文 · 机器初译**

4.2 结果

### openscholar-0114

**English original**

Table 2 show scores for multiple aspects of the main baselines.
In summary, OpenScholar achieves state-of-the performance, significantly outperforming GPT4o and their standard RAG version, as well as specialized literature review systems such as PaperQA2 ( Skarlinski et al., 2024 ) by a large margin.

**中文译文 · 机器初译**

表2展示了主要基准模型的多个方面的得分情况。总体而言，OpenScholar表现处于顶尖水平，其性能显著优于GPT4o及其标准RAG版本，也远超如PaperQA2（Skarlinski等，2024）这样的专业文献综述系统。

### openscholar-0115

**English original**

Single-paper tasks.

**中文译文 · 机器初译**

单篇论文任务。

### openscholar-0116

**English original**

On single-paper tasks, OpenScholar consistently outperforms other models. OS-8B and OS-70B outperforms Llama 3.1 8B and 70B with and without retrieval augmentation in terms of final Corr and Cite in Table 2 .
OS-70B even matches or outperforms GPT4o on PubMedQA and QASA.

**中文译文 · 机器初译**

在单篇论文任务中，OpenScholar始终优于其他模型。如表2所示，OS-8B和OS-70B在最终Corr和Cite指标上，无论是否进行检索增强，均优于Llama 3.1 8B和70B。OS-70B甚至在PubMedQA和QASA任务中与GPT4o相当或表现更优。

### openscholar-0117

**English original**

| Single-paper performance | Multi-paper performance | Cost
 | Pub | Sci | QASA | CS | Multi | Bio | Neu | CS
Model | Corr | Cite | Corr | Cite | Corr | Cite | Corr | Cite | LLM | Cite | Cite | Cite | USD / q
Llama3-8B | 61.5 | 0.0 | 66.8 | 0.0 | 14.3 | 0.0 | 41.9 | 0.0 | 3.79 | 0.0 | 0.0 | 0.0 | 0.0001
+OSDS | 75.2 | 63.9 | 75.5 | 36.2 | 18.6 | 47.2 | 46.7 | 26.1 | 4.22 | 25.3 | 38.0 | 36.8 | 0.0001
OS-8B | 76.4 | 68.9 | 76.0 | 43.6 | 23.0 | 56.3 | 51.1 | 47.9 | 4.12 | 42.8 | 50.8 | 56.8 | 0.003
Llama3-70B | 69.5 | 0.0 | 76.9 | 0.0 | 13.7 | 0.0 | 44.9 | 0.0 | 3.82 | 0.0 | 0.0 | 0.0 | 0.0004
+OSDS | 77.4 | 71.1 | 78.2 | 42.5 | 22.7 | 63.6 | 48.5 | 24.5 | 4.24 | 41.4 | 53.8 | 58.1 | 0.0004
OS-70B | 79.6 | 74.0 | 82.1 | 47.5 | 23.4 | 64.2 | 52.5 | 45.9 | 4.03 | 54.7 | 55.9 | 63.1 | 0.01
GPT4o | 65.8 | 0.0 | 77.8 | 0.0 | 21.2 | 0.0 | 45.0 | 0.1 | 4.01 | 0.7 | 0.2 | 0.1 | 0.006
+OSDS | 75.1 | 73.7 | 79.3 | 47.9 | 18.3 | 53.6 | 52.4 | 31.1 | 4.03 | 31.5 | 36.3 | 21.9 | 0.01
OS-GPT4o | 74.8 | 77.1 | 81.3 | 56.5 | 18.7 | 60.4 | 57.7 | 39.5 | 4.51 | 37.5 | 51.5 | 43.5 | 0.05
PaperQA2 | – | – | – | – | – | – | 45.6 | 48.0 | 3.82 | 47.2 | 56.7 | 56.0 | 0.3 $\sim$ 2.3
Perplexity | – | – | – | – | – | – | 40.0 | – | 4.15 | – | – | – | 0.002 ∗∗

**中文译文 · 机器初译**

| Single-paper performance | Multi-paper performance | Cost
 | Pub | Sci | QASA | CS | Multi | Bio | Neu | CS
Model | Corr | Cite | Corr | Cite | Corr | Cite | Corr | Cite | LLM | Cite | Cite | Cite | USD / q
Llama3-8B | 61.5 | 0.0 | 66.8 | 0.0 | 14.3 | 0.0 | 41.9 | 0.0 | 3.79 | 0.0 | 0.0 | 0.0 | 0.0001
+OSDS | 75.2 | 63.9 | 75.5 | 36.2 | 18.6 | 47.2 | 46.7 | 26.1 | 4.22 | 25.3 | 38.0 | 36.8 | 0.0001
OS-8B | 76.4 | 68.9 | 76.0 | 43.6 | 23.0 | 56.3 | 51.1 | 47.9 | 4.12 | 42.8 | 50.8 | 56.8 | 0.003
Llama3-70B | 69.5 | 0.0 | 76.9 | 0.0 | 13.7 | 0.0 | 44.9 | 0.0 | 3.82 | 0.0 | 0.0 | 0.0 | 0.0004
+OSDS | 77.4 | 71.1 | 78.2 | 42.5 | 22.7 | 63.6 | 48.5 | 24.5 | 4.24 | 41.4 | 53.8 | 58.1 | 0.0004
OS-70B | 79.6 | 74.0 | 82.1 | 47.5 | 23.4 | 64.2 | 52.5 | 45.9 | 4.03 | 54.7 | 55.9 | 63.1 | 0.01
GPT4o | 65.8 | 0.0 | 77.8 | 0.0 | 21.2 | 0.0 | 45.0 | 0.1 | 4.01 | 0.7 | 0.2 | 0.1 | 0.006
+OSDS | 75.1 | 73.7 | 79.3 | 47.9 | 18.3 | 53.6 | 52.4 | 31.1 | 4.03 | 31.5 | 36.3 | 21.9 | 0.01
OS-GPT4o | 74.8 | 77.1 | 81.3 | 56.5 | 18.7 | 60.4 | 57.7 | 39.5 | 4.51 | 37.5 | 51.5 | 43.5 | 0.05
PaperQA2 | – | – | – | – | – | – | 45.6 | 48.0 | 3.82 | 47.2 | 56.7 | 56.0 | 0.3 $\sim$ 2.3
Perplexity | – | – | – | – | – | – | 40.0 | – | 4.15 | – | – | – | 0.002 ∗∗

表内文字对照（数值与原始行列保持不变）：
Single-paper performance → 单篇论文表现
Multi-paper performance → 多篇论文表现
Cost → 成本
Pub → 出版物
Sci → 科学
QASA → QASA
Multi → 多模态
Bio → 生物
Neu → 神经
Model → 模型
Corr → Corr
Cite → 引用
LLM → 大语言模型
USD / q → 美元 / 数量
Llama → Llama
OSDS → OSDS
OS- → 操作系统
GPT → GPT
OS-GPT → OS-GPT
PaperQA → PaperQA
sim → 模拟
Perplexity → 困惑度

### openscholar-0118

**English original**

Table 2: Results of ScholarQABench . CS, Multi, Bio and Neu indicate Scholar-CS , ScholarQA-Multi , ScholarQA-Bio and ScholarQA-Neuro , respectively. Corr indicates correctness metrics (accuracy for PubMedQA and SciFact, ROUGE-L for QASA and Overall scores for ScholarQA-CS ) and Cite indicates citation F1. LLM indicates the average score of Org (organization), Rel (relevance), Cov (coverage) as predicted by Prometheus ( Kim et al., 2024a ) . ∗ PaperQA2 is based on GPT4o, and its pricing is dependent on the number of PDF files used during inference.
For the 8B and 70B model costs, while evaluations were conducted on our local machines, we estimated costs based on Together.ai pricing. ∗∗ We used Perplexity Pro (which requires a monthly subscription at $20 USD) and divided this cost by 9,000, which is the maximum number of queries allowed under the Pro subscription.
Since the Perplexity UI does not provide snippets for each citation, we were unable to evaluate its citation accuracy.

**中文译文 · 机器初译**

表2：ScholarQABench的结果。CS、Multi、Bio和Neu分别代表Scholar-CS、ScholarQA-Multi、ScholarQA-Bio和ScholarQA-Neuro。Corr表示正确率指标（PubMedQA和SciFact的准确率，QASA的ROUGE-L值，ScholarQA-CS的整体得分），Cite表示引用F1值。LLM表示根据Prometheus（Kim等人，2024a）研究预测的Org（组织）、Rel（相关性）、Cov（覆盖度）的平均得分。∗PaperQA2基于GPT4o构建，其定价取决于推理过程中使用的PDF文件数量。
对于 8B 和 70B 模型的成本，虽然评估是在本地机器上进行的，但我们是根据 Together.ai 的定价来估算成本的。∗∗ 我们使用了 Perplexity Pro 工具（需要每月支付 20 美元的订阅费），并将该费用除以 9,000，即 Pro 订阅下允许的最大查询数量。由于 Perplexity 界面不提供每篇引用的片段内容，因此我们无法评估其引用准确性。

### openscholar-0119

**English original**

| Computer Science | Biomedicine
Model | Total # | # of Hallucinated ( $\downarrow)$ | Ratio ( $\downarrow)$ | Total # | # of Hallucinated ( $\downarrow)$ | Ratio ( $\downarrow)$
OS-8B | 9.65 | 0.0 | 0.0 | 6.25 | 0.0 | 0.0
Llama 3.1 8B | 5.20 | 4.79 | 92.1% | 5.58 | 5.46 | 97.6%
Llama 3.1 70B | 6.14 | 4.78 | 78.1% | 6.98 | 6.74 | 96.6%
GPT4o | 5.74 | 4.52 | 78.7% | 5.24 | 4.97 | 94.8%

**中文译文 · 机器初译**

| Computer Science | Biomedicine
Model | Total # | # of Hallucinated ( $\downarrow)$ | Ratio ( $\downarrow)$ | Total # | # of Hallucinated ( $\downarrow)$ | Ratio ( $\downarrow)$
OS-8B | 9.65 | 0.0 | 0.0 | 6.25 | 0.0 | 0.0
Llama 3.1 8B | 5.20 | 4.79 | 92.1% | 5.58 | 5.46 | 97.6%
Llama 3.1 70B | 6.14 | 4.78 | 78.1% | 6.98 | 6.74 | 96.6%
GPT4o | 5.74 | 4.52 | 78.7% | 5.24 | 4.97 | 94.8%

表内文字对照（数值与原始行列保持不变）：
Computer Science → 计算机科学
Biomedicine → 生物医学
Model → 模型
Total → 总数
of Hallucinated ( → 关于幻觉现象（
downarrow) → (向下)
Ratio ( → 比例（
OS- → 操作系统
Llama → Llama
GPT → GPT

### openscholar-0120

**English original**

Table 3: Statistics of hallucinated papers in computer science and biomedicine domains . Our analysis revealed a significant number of non-existent cited papers in predictions made by LLMs without retrieval, which is a problem not observed in OpenScholar .

**中文译文 · 机器初译**

表3：计算机科学与生物医学领域虚假论文的统计数据。我们的分析显示，在缺乏检索机制的LLM预测中，存在大量不存在的被引用论文，这是OpenScholar中未出现的问题。

### openscholar-0121

**English original**

Multi-paper tasks.

**中文译文 · 机器初译**

多篇论文任务。

### openscholar-0122

**English original**

OpenScholar -8B, 70B, and GPT4o (OS-8B, OS-70B and OS-GPT4o) demonstrate strong performance in multi-paper tasks. Specifically, OS-GPT4o provides a 12.7 point improvement over GPT4o alone in Scholar-CS Corr and a 5.3 improvement over standard RAG.
When combined with trained OS-8B, OpenScholar significantly outperforms the pipeline that uses off-the-shelf Llama 3.1 8B, showcasing the benefits of domain-specific training.
Furthermore, this OpenScholar -8B outperforms proprietary systems such as GPT4o, Perplexity Pro, or PaperQA2, which uses GPT4o models for passage reranking, summarization and answer generation, by a substantial margin.
Notably, by leveraging efficient retrieval pipelines with lightweight bi-encoders, cross-encoders, and in-house models, OpenScholar -8B and OpenScholar -GPT4o achieve significantly lower costs—orders of magnitude cheaper than PaperQA2—while maintaining high performance.

**中文译文 · 机器初译**

OpenScholar -8B、70B以及GPT4o（OS-8B、OS-70B和OS-GPT4o）在多篇文献处理任务中表现出优异性能。具体而言，OS-GPT4o在Scholar-CS Corr任务中比GPT4o本身提升了12.7分，比标准RAG方案提升了5.3分。当与训练过的OS-8B结合使用时，OpenScholar的表现显著优于使用现成Llama 3.1 8B的流程，充分展现了特定领域训练的优势。此外，OpenScholar -8B的表现也大幅超过了GPT4o、Perplexity Pro或PaperQA2等专有系统——这些系统使用GPT4o模型进行段落重新排序、摘要生成和答案生成。
值得注意的是，通过利用高效的检索流程以及轻量级双编码器、跨编码器和内部模型，OpenScholar -8B与OpenScholar -GPT4o能够大幅降低成本——其成本比PaperQA2低数个数量级——同时仍保持高性能。

### openscholar-0123

**English original**

Limitations of parametric LMs.

**中文译文 · 机器初译**

参数化大语言模型的局限性。

### openscholar-0124

**English original**

On both single-paper and multi-paper tasks, we observe that non-retrieval augmented baselines struggle and retrieval is almost always conducive to achieving better performance, and models without any retrieval often struggle to generate correct citations and show limited coverage on multi-paper tasks.
As shown in Table 3 , the proportion of cited papers that actually exist is strikingly low. In particular, while models such as GPT4o and Llama can generate plausible reference lists, we find that 78-98% of the cited papers are fabricated, and the issue is exacerbated in biomedical domains. Even when citations refer to real papers, the majority are not substantiated by the corresponding abstracts, resulting in near-zero citation accuracy.

**中文译文 · 机器初译**

在单篇论文和多篇论文任务中，我们观察到非检索增强基线模型表现不佳，而检索几乎总能提升性能；缺乏检索功能的模型往往难以生成正确的引用信息，在多篇论文任务中的覆盖范围也较为有限。如表3所示，实际存在的被引用论文比例极低。尤其值得注意的是，尽管GPT4o和Llama等模型能够生成合理的参考文献列表，但我们发现78-98%的被引用论文都是虚构的，这一问题在生物医学领域更为严重。
即使引文指向真实的论文，大多数引文也未能得到相应摘要的支撑，导致引用准确率几乎为零。

### openscholar-0125

**English original**

We also observe that such models also generate responses with limited coverage.
On Scholar -Multi, non-retrieval models (Llama 3.1 8B, 70B, and GPT4o) consistently exhibit significantly lower average scores compared to retrieval-augmented models. This discrepancy is largely driven by much lower Cov scores; for instance, Llama 3.1 8B achieves a Cov score of 3.45, while Llama 3.1 8B + OSDS (a standard RAG baseline) improves it to 4.01.
These results suggest that solely relying on models’ parametric knowledge alone is particularly difficult in scientific domains, especially for smaller LMs.

**中文译文 · 机器初译**

我们还观察到，这类模型生成的回答覆盖范围也较为有限。在 Scholar-Multi平台上，非检索模型（Llama 3.1 8B、70B以及GPT4o）的平均得分与检索增强模型相比始终显著较低。这种差异主要源于其 Cov得分低得多：例如，Llama 3.1 8B的Cov得分为3.45，而Llama 3.1 8B + OSDS（一种标准的RAG基线模型）将其提升至4.01。这些结果表明，在科学领域，仅依赖模型的参数化知识尤其困难，尤其是对于较小的大语言模型而言。

### openscholar-0126

**English original**

4.3 Analysis

**中文译文 · 机器初译**

4.3 分析

### openscholar-0127

**English original**

| Scholar-CS
 | Corr | Cite
OS -8B | 51.3 | 47.9
- training | 49.4 | 42.3
- reranking | 49.6 | 28.2
- feedback | 51.1 | 50.2
- attribution | 49.3 | 44.0
OS- GPT4o | 57.7 | 39.5
- reranking | 52.4 | 22.9
- feedback | 55.1 | 31.0
- attribution | 55.6 | 30.6

**中文译文 · 机器初译**

| Scholar-CS
 | Corr | Cite
OS -8B | 51.3 | 47.9
- training | 49.4 | 42.3
- reranking | 49.6 | 28.2
- feedback | 51.1 | 50.2
- attribution | 49.3 | 44.0
OS- GPT4o | 57.7 | 39.5
- reranking | 52.4 | 22.9
- feedback | 55.1 | 31.0
- attribution | 55.6 | 30.6

表内文字对照（数值与原始行列保持不变）：
Scholar-CS → 学者-CS
Corr → Corr
Cite → 引用
OS - → 操作系统 -
training → 训练
reranking → 重新排序
feedback → 反馈
attribution → 归因
OS- GPT → OS- GPT

### openscholar-0128

**English original**

(a) Ablation of different components of OpenScholar .

**中文译文 · 机器初译**

(a) 对 OpenScholar 不同组件的剔除实验。

### openscholar-0129

**English original**

(b) Top N Ablations ( Corr ) on Scholar-CS .

**中文译文 · 机器初译**

(b) Scholar-CS 上排名前 N 的消融实验（Corr）。

### openscholar-0130

**English original**

(c) Top N Ablations ( Cite -F1) on Scholar-CS .

**中文译文 · 机器初译**

(c) Scholar-CS 上的前 N 名消融实验（Cite-F1）

### openscholar-0131

**English original**

Figure 4: Analysis on OpenScholar : (a) Ablation studies for key components of OpenScholar training and inference based on different underlying LMs. (b) Top N docs: Analysis of the effect of varying the number of context chunks for final downstream tasks. We evaluate final model performance based on citation accuracy and correctness on multi-doc QA tasks, using OpenScholar 8B and Llama 3.1 8B.

**中文译文 · 机器初译**

图4：OpenScholar分析：(a) 基于不同底层大语言模型，对OpenScholar训练与推理关键组件的消融研究。(b) 前N篇文档：分析不同上下文块数量对最终下游任务影响的研究。我们使用OpenScholar 8B和Llama 3.1 8B，以引用准确率和多文档问答任务的正确性作为最终模型性能评估指标。

### openscholar-0132

**English original**

Ablation studies.

**中文译文 · 机器初译**

剔除研究。

### openscholar-0133

**English original**

We conduct ablations to assess the effectiveness of individual components of OpenScholar (inference and training). Specifically, we remove each of the inference-time procedures, reranking, feedback and attribution, and for OS-8B, we ablate the training, where we use Llama3-8B without any further training.

**中文译文 · 机器初译**

我们进行了各种消融实验，以评估 OpenScholar 中各个组件的有效性（包括推理和训练）。具体而言，我们去除了所有的推理阶段流程，包括重新排序、反馈和归因机制；对于 OS-8B 模型，我们还去除了训练过程，直接使用 Llama3-8B 模型而不进行任何额外训练。

### openscholar-0134

**English original**

As shown in Figure 4 (a), removing these components significantly impacts both the overall correctness and citation accuracy of the model outputs. Notably, removing the reranker led to substantial performance drops on both models.
The pronounced decline in performance after removing feedback loops in GPT4o suggests that more powerful models greatly benefit from a self-feedback cycle, consistent with Madaan et al. (2023) , while it gives limited performance drops in our trained 8B. Additionally, the removal of post-hoc attribution assessments negatively affected both citation accuracy and final output correctness, highlighting the importance of ensuring that models verify their outputs.
The significant performance gap between trained versus vanilla OS-8B suggests that further training on high-quality, domain-specific data is key to building efficient, task-specialized LMs.
In the next analysis, we demonstrate that training has a significant impact on an LM’s ability to effectively utilize more context, while maintaining citation accuracy.

**中文译文 · 机器初译**

如图4(a)所示，移除这些组件显著影响了模型输出的整体正确性和引用准确性。值得注意的是，移除重排序模块导致两种模型的性能都大幅下降。在GPT4o中移除反馈回路后，性能出现明显下降，这表明更强大的模型能从自我反馈机制中获得巨大收益，这与Madaan等人（2023）的研究结果一致；而在我们训练的8B模型中，这种机制仅导致有限的性能下降。此外，事后归因评估的移除对引用准确性和最终输出正确性都产生了负面影响，这凸显了确保模型验证其输出的重要性。
经过训练的大语言模型与普通 OS-8B 模型之间的显著性能差距表明，利用高质量、特定领域的数据进行进一步训练是构建高效、任务专用大语言模型的关键。在后续分析中，我们证明训练对大语言模型有效利用更多上下文的能力有着显著影响，同时又能保持引用准确性。

### openscholar-0135

**English original**

Number of context passages.

**中文译文 · 机器初译**

上下文段落数量。

### openscholar-0136

**English original**

We analyzed how varying the number of context passages (top $N$ ) impacts model performance.
Specifically, we experimented with Standard RAG and OpenScholar using our trained 8B model and Llama 3.1 8B, and evaluated both generation accuracy and citation accuracy on Scholar-CS .
Figures 4 (b)(c) show the results.
Although Llama 3.1 is trained to handle and accept a context length of up to 128K tokens, we found that its performance deteriorates after a certain context size. While increasing the top $N$ context window from 5 to 10 does improve the model’s correctness score, expanding further actually worsens both correctness and citation accuracy. This suggests that even though LMs can process large numbers of passages, they may struggle to effectively use them without specialized training, particularly for smaller models.

**中文译文 · 机器初译**

我们分析了上下文段落数量的变化对模型性能的影响。具体而言，我们使用训练好的8B模型和Llama 3.1 8B，在Standard RAG和OpenScholar环境中进行了实验，并在Scholar-CS上评估了生成准确性和引用准确性。图4 (b)(c)展示了实验结果。尽管Llama 3.1被训练为能够处理并接受高达128K个令牌的上下文长度，但我们发现当上下文规模超过一定限度后，其性能会下降。虽然将最高$N$上下文窗口从5扩展至10确实能提升模型的准确性得分，但进一步扩展反而会降低准确性和引用准确性。
这表明，尽管大语言模型能够处理大量文本，但在没有专门训练的情况下，它们可能难以有效利用这些文本，尤其是对于较小的模型而言。

待核对标记：formula_or_link_placeholder_missing

### openscholar-0137

**English original**

In contrast, our trained 8B model maintains strong performance for up to $N=20$ passages.
We also found larger models such as Llama 3.1 70B to be more robust to increased context length.
In terms of citation accuracy, as shown in Figures 4 (c), Llama 3.1 8B observes quick decline and citation F1 gets as low as 10, while our 8B LM and Llama 70B both maintain around 40 citation F1, although they also see some performance decline.

**中文译文 · 机器初译**

相比之下，我们训练好的8B模型在长达$N=20$的段落中仍保持良好的性能。我们还发现，像Llama 3.1 70B这样更大的模型对上下文长度的增加更为稳健。在引用准确性方面，如图4 (c)所示，Llama 3.1 8B的准确率迅速下降，引用F1值低至10，而我们的8B大语言模型和Llama 70B的引用F1值均保持在约40左右，尽管它们也出现了一定的性能下降。

### openscholar-0138

**English original**

5 Expert Evaluation

**中文译文 · 机器初译**

5 专家评估

### openscholar-0139

**English original**

To complement our automatic evaluations and better understand the effectiveness and limitations of OpenScholar , we conducted human evaluations. This study involved over 100 literature review questions and more than 15 participants, including Ph.D. students, research scientists, and university professors with expertise in the relevant fields. In total, we curated more than 400 fine-grained expert evaluations on human and model answers.

**中文译文 · 机器初译**

为了补充自动评估结果，并更全面地了解 OpenScholar 的效果与局限性，我们进行了人工评估。本研究涉及超过 100 个文献综述问题及 15 多名参与者，包括博士学生、研究科学家以及相关领域专家教授。最终共收集了超过 400 份针对人类与模型回答的细致专家评估意见。

### openscholar-0140

**English original**

5.1 Human Evaluation Design

**中文译文 · 机器初译**

5.1 人类评估设计

### openscholar-0141

**English original**

Evaluations against human experts.

**中文译文 · 机器初译**

针对人类专家的评估。

### openscholar-0142

**English original**

For human evaluations, we use 108 question-answer pairs from ScholarQA-Multi , written by experts.
We run three models on these questions to generate answers with citations: GPT4o (without external retrieval), OpenScholar with GPT4o as the generator (OS-GPT4o), and OpenScholar with our trained 8B model (OS-8B). Expert annotators are then asked to evaluate the model-generated answers against human-written answers.

**中文译文 · 机器初译**

对于人类评估，我们使用了来自 ScholarQA-Multi 的 108 对问题与答案对，这些内容由专家撰写。我们对这些问题运行了三种模型，以生成带有引用信息的答案：GPT4o（无外部检索）、使用 GPT4o 作为生成器的 OpenScholar（OS-GPT4o），以及使用我们训练的 8B 模型的 OpenScholar（OS-8B）。随后，让专业标注员对模型生成的答案与人类撰写的答案进行对比评估。

### openscholar-0143

**English original**

Each evaluation involves presenting a question, a model-generated answer, and a human-written answer. Expert annotators then conduct fine-grained assessments of each answer and provide pairwise preference judgments between the two.
For fine-grained evaluations, we use the five-scale evaluation criteria described in Section 3 ( Cov , Org , Rel ), with annotators scoring both model and human answers using the same rubrics.
For usefulness ( Use ), annotators assign scores on a scale from 1-5, which we convert into three classes: Not Useful (1-2), Neutral (3), and Useful (4-5). We then calculate the percentage of answers that fall into the Useful category. For pairwise preference, annotators either choose one of the answers or mark a “tie” if they judge both answers to be of equal quality. Optionally, experts provide explanations on why one answer is better than the other.

**中文译文 · 机器初译**

每次评估都包括一个问题、一个模型生成的答案以及一个人写的答案。专家注释者随后会对每个答案进行细致评估，并给出两者之间的偏好判断。在细致评估中，我们采用第3节中描述的五级评估标准（Cov、Org、Rel），注释者使用相同的评分标准对模型和人类答案进行评分。对于实用性指标（Use），注释者会在1到5的等级范围内打分，我们将其划分为三类：无用（1-2）、中性（3）和有用（4-5）。随后我们计算属于“有用”类别的答案所占的比例。
在成对偏好评估中，标注者可以选择其中一个答案，或如果认为两个答案质量相同，则标记为“平局”。此外，专家也可提供解释说明为何一个答案优于另一个答案。

### openscholar-0144

**English original**

Expert annotators for answer writing.

**中文译文 · 机器初译**

用于回答撰写的大语言模型专家注释者。

### openscholar-0145

**English original**

Our expert annotators for question and answer writing are 12 Ph.D. students and post-doctoral researchers from research institutions across the United States, all of whom have at least three years of research experience and published multiple papers in journals or conferences from their fields.
Our annotators’ expert areas span computer science (Natural Language Processing, computer Vision, Human-Computer Interaction), physics (Astrophysics and Photonics / Optics), and biomedical (Neuroscience, Bioimaging) domains, and we assign our expert annotators to questions in their expertise. On average, we paid 35-40 USD per person.

**中文译文 · 机器初译**

负责问答内容标注的专家智能体共有12名博士学生及博士后研究人员，他们均来自美国各研究机构，拥有至少三年的研究经验，并在各自领域的相关期刊或会议上发表了多篇论文。这些标注专家的专业领域涵盖计算机科学（自然语言处理、计算机视觉、人机交互）、物理学（天体物理与光子学/光学）以及生物医学（神经科学、生物成像）等领域，我们会根据问题所属的专业领域来分配标注任务。平均而言，我们向每位专家支付35至40美元的费用。

### openscholar-0146

**English original**

Expert annotators for evaluations.

**中文译文 · 机器初译**

用于评估的大语言模型专家注释员。

### openscholar-0147

**English original**

A total of 16 expert annotators from the three fields contributed to our evaluations, with 12 of them also participating in answer generation. All expert annotators met the same qualifications as those who composed the answers. To minimize potential biases, we ensured that annotators did not evaluate responses to their own questions by assigning evaluation tasks to different groups of experts.
Each instance was reviewed by 1 to 3 expert annotators, depending on availability. The inter-annotator agreement was 0.68 using pairwise comparison with ties, and 0.70 using a relaxed approach, wherein ties were merged. On average, each expert spent five minutes per instance on evaluation, and received compensation ranging from 25–35 USD.

**中文译文 · 机器初译**

来自三个领域的共16位专家注释员参与了我们的评估工作，其中12位还参与了答案的生成。所有专家注释员的资质与撰写答案的人员一致。为了尽可能减少潜在偏见，我们通过将评估任务分配给不同的专家小组，确保注释员不会对自己提出的问题的回复进行评估。根据可用人员情况，每个案例由1至3位专家注释员进行审核。使用配对比较并处理平局时，不同注释员之间的一致性为0.68；采用放宽方法并合并平局时，一致性为0.70。
平均而言，每位专家每个实例需要花费五分钟进行评估，并获得25–35美元的报酬。

### openscholar-0148

**English original**

| Fine-grained (1-5, Avg.) | Overall Usefulness | Relative to Human (%)
 | Org | Cov | Rel | Use (%) | Win | Tie | Lose
GPT4o | 4.63 (+0.4) | 4.06 (-0.2) | 4.50 (-0.1) | 69.7 (-13.9) | 31.9 | 13.8 | 54.2
OS -8B | 3.82 (-0.3) | 4.30 (+0.7) | 4.00 (-0.4) | 72.1 (+8.7) | 50.8 | 12.3 | 36.9
OS -GPT4o | 4.47 (+0.8) | 4.38 (+0.9) | 4.30 (0.0) | 80.0 (+22.5) | 70.0 | 6.8 | 23.2

**中文译文 · 机器初译**

| Fine-grained (1-5, Avg.) | Overall Usefulness | Relative to Human (%)
 | Org | Cov | Rel | Use (%) | Win | Tie | Lose
GPT4o | 4.63 (+0.4) | 4.06 (-0.2) | 4.50 (-0.1) | 69.7 (-13.9) | 31.9 | 13.8 | 54.2
OS -8B | 3.82 (-0.3) | 4.30 (+0.7) | 4.00 (-0.4) | 72.1 (+8.7) | 50.8 | 12.3 | 36.9
OS -GPT4o | 4.47 (+0.8) | 4.38 (+0.9) | 4.30 (0.0) | 80.0 (+22.5) | 70.0 | 6.8 | 23.2

表内文字对照（数值与原始行列保持不变）：
Fine-grained ( → 细粒度（
Avg → 平均值
Overall Usefulness → 整体实用性
Relative to Human ( → 与人类相比（
Org → 组织
Cov → Cov
Rel → 相关
Use ( → 使用（
Win → 获胜
Tie → 平局
Lose → 失败
GPT → GPT
OS - → 操作系统 -
OS -GPT → 操作系统 -GPT

### openscholar-0149

**English original**

Table 4: Human evaluation results . Fine-grained aspect evaluations are conducted on a five-point scale across four aspects using our detailed instructions and rubrics. Values in parentheses represent the relative performance difference; (+) indicates that the model shows higher performance, and (-) indicates that the human shows higher performance.

**中文译文 · 机器初译**

表4：人类评估结果。根据我们的详细指导与评分标准，在四个方面上使用五点量表对细节层面的评价进行评估。括号中的数值表示相对性能差异；(+)表示模型表现更优，(-)表示人类表现更优。

### openscholar-0150

**English original**

5.2 Human Evaluation Results

**中文译文 · 机器初译**

5.2 人类评估结果

### openscholar-0151

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0152

**English original**

Figure 5: Fine-grained evaluation results. Score distributions between 1) GPT4o (top), OpenScholar with 8B (middle), OpenScholar with GPT4o with Human (bottom).

**中文译文 · 机器初译**

图5：细粒度评估结果。得分分布分别为：1) GPT4o（最高分），OpenScholar 8B版本（中等水平），OpenScholar 结合 GPT4o 与人工干预的版本（最低分）。

### openscholar-0153

**English original**

Results of human evaluations.

**中文译文 · 机器初译**

人类评估结果。

### openscholar-0154

**English original**

Table 4 presents the average scores for each evaluation aspect, alongside the relative win rates against human responses.
Figure 5 illustrates the score distributions for Human, GPT4o, and OpenScholar with Llama 3 8B and GPT4o.
Notably, both OS-GPT4o and our OS-8B versions outperform human answers in over 50% of cases, with their advantage primarily attributed to their ability to provide a greater breadth and depth of information (coverage; Cov ). In contrast, GPT4o, which lacks retrieval capabilities, demonstrates significantly limited coverage and wins in fewer than 35% of cases, with its overall usefulness rated much lower than responses from humans and the other two models. These results highlight that even for state-of-the-art models, synthesizing and answering scientific literature review questions remains a challenging task, consistent with our findings on ScholarQABench .
Overall, OpenScholar -GPT4o and OpenScholar -8B are rated as Useful in 80% and 72% of the queries, respectively.

**中文译文 · 机器初译**

表4展示了每个评估维度的平均得分，以及与人类回答相比的胜率。图5则展示了使用Llama 3 8B和GPT4o的人类、GPT4o及OpenScholar模型的得分分布。值得注意的是，OS-GPT4o和我们的OS-8B版本在超过50%的情况下都优于人类答案，其优势主要源于能够提供更广泛、更深入的信息（覆盖度；Cov）。相比之下，缺乏检索功能的GPT4o在不到35%的情况下仅获得少量胜率，其整体实用性也远低于人类及其他两个模型的回答。
这些结果表明，即使对于最先进的模型而言，整合并回答科学文献综述问题仍是一项具有挑战性的任务，这与我们在 ScholarQABench 上的研究结果一致。总体而言，OpenScholar -GPT4o 和 OpenScholar -8B 在分别 80% 和 72% 的查询中被评为“有用”。

### openscholar-0155

**English original**

While OpenScholar with a smaller open 8B LM already suppresses human experts, the 8B model’s output is judged to be less organized or fluent than the current state-of-the-art private LM-based OpenScholar . We found that GPT4o incorporates feedback more effectively, and generally generates longer and more fluent outputs, leading to significantly higher organization scores compared to 8B based OpenScholar as well as humans.

**中文译文 · 机器初译**

虽然较小的 8B 大语言模型版本的 OpenScholar 已经能够替代人类专家，但 8B 模型的输出在条理性和流畅性方面仍不如当前最先进的基于私有大语言模型的 OpenScholar。我们发现 GPT4o 能更有效地整合反馈，通常能生成更长且更流畅的输出内容，因此与 8B 版本的 OpenScholar 以及人类相比，其组织性得分明显更高。

### openscholar-0156

**English original**

Effects of length control on model responses.

**中文译文 · 机器初译**

长度控制对模型回答的影响。

### openscholar-0157

**English original**

While we found model outputs to often be preferred over human outputs, one potential confounding factor is the significant difference in their output length– OpenScholar -GPTo and OpenScholar -8B are 2.4 times and 2.0 times longer than human-written answers, respectively, which may affect human judgment Dubois et al. (2024) .
To understand the effect of output length, we conducted a controlled experiment: for randomly sampled 50 questions, we generate shorter version of responses for OpenScholar -GPT4o, by prompting GPT4o to create summaries of the responses that fall under 300 words. As a result, we collected OpenScholar answers that average around 333 words, which is close to the average human answer length.
We then conduct the same human evaluation and evaluate fine-grained and overall responses.
On average, the shortened GPT4o scores 4.5 for organization, 4.6 for coverage, and 4.6 for relevance.
The shortened OpenScholar -GPT4o responses are preferred or tied with expert answers in 75% of the queries.
The experimental results show that the model’s superior performance is not merely due to the increased length of the OpenScholar answers. Moreover, human annotators’ explanations often mention that both shortened OpenScholar and human answers could be improved by incorporating more details, implying that a 300-word restriction may limit the utility of answers.

**中文译文 · 机器初译**

虽然我们发现模型输出往往比人类输出更受青睐，但一个潜在的干扰因素是其输出长度存在显著差异——OpenScholar-GPTo 的输出长度是人类写作答案的 2.4 倍，而 OpenScholar-8B 则长达 2.0 倍，这可能会影响人类的判断（Dubois 等，2024）。为了了解输出长度的影响，我们进行了一项控制实验：针对随机选取的 50 道问题，我们让 OpenScholar-GPT4o 生成较短版本的回答，通过提示 GPT4o 对字数在 300 字以内的回答进行总结来实现。
因此，我们收集了平均约 333 字的 OpenScholar 回答，这一长度与人类回答的平均长度相近。随后进行了相同的人类评估，对细致且全面的回答进行了评价。平均而言，缩短后的 GPT4o 在组织性方面得分为 4.5，在覆盖度方面为 4.6，在相关性方面也为 4.6。在 75% 的查询中，缩短后的 OpenScholar -GPT4o 回答与专家答案相当或更优。实验结果表明，该模型的出色表现并非仅仅源于 OpenScholar 回答长度的增加。
此外，人类注释者的说明通常提到，通过添加更多细节，缩短后的 OpenScholar 结果及人类回答都可以得到改进，这表明 300 字的限制可能会限制这些回答的实用性。

### openscholar-0158

**English original**

Analyses on human explanations for pair-wise explanations.

**中文译文 · 机器初译**

关于人类对成对解释的解释行为的分析。

### openscholar-0159

**English original**

We randomly sampled 59 instances with free-form explanations of pairwise preferences and conducted a manual analysis to identify factors that influence overall preferences. Specifically, we examined whether the explanations referenced one or more of the following four categories: organization, relevance, coverage, and citations. While the first three categories align with the fine-grained human evaluation criteria, the citation category also considers the quality of the cited papers (e.g., whether the system includes key representative papers in the field).
Our analysis revealed that 12%, 23%, 29%, and 9% of the explanations cited organization, relevance, coverage, and citations, respectively, as key factors in pairwise decisions. This suggests that coverage plays a crucial role in how humans assess the quality of responses, with annotators largely favoring model-generated answers for their greater coverage and depth of information. However, annotators also noted that the citations provided by models could be improved, pointing out that the suggested papers were occasionally outdated or less relevant compared to more representative work. Appendix 15 shows example explanations.

**中文译文 · 机器初译**

我们随机选取了59个样本，这些样本包含自由形式的成对偏好说明，并进行了手动分析以识别影响整体偏好的因素。具体而言，我们检查了这些说明是否涉及以下四个类别中的一个或多个：组织结构、相关性、覆盖范围和引用。前三个类别与细致的人机评估标准相符，而引用类别则还考虑了被引用的论文的质量（例如，系统是否包含了该领域的重要代表性论文）。
我们的分析显示，在成对决策中，分别有12%、23%、29%和9%的解释将组织性、相关性、覆盖率和引用量视为关键因素。这表明，在人类评估回答质量的过程中，覆盖率起着至关重要的作用，注释者通常更青睐模型生成的答案，因为后者具有更广泛的信息覆盖率和深度。然而，注释者也指出，模型提供的引用内容可以改进，他们提到所推荐的文献有时已过时或不如更具代表性的研究相关。附录15展示了示例解释。

### openscholar-0160

**English original**

6 Related Work

**中文译文 · 机器初译**

6 相关研究

### openscholar-0161

**English original**

Scientific LMs.

**中文译文 · 机器初译**

科学大语言模型。

### openscholar-0162

**English original**

Scientific LMs have spanned various domains, including biomedical ( Phan et al., 2021 ; Yuan et al., 2022 ; Luo et al., 2022 ) , medical ( Singhal et al., 2023a ; Gu et al., 2024 ; Tan et al., 2023 ; Singhal et al., 2023b ) , biomedical ( Zhang et al., 2024b ; Fang et al., 2024 ; Li et al., 2024a ) , geoscience ( Feng et al., 2023 ) , astronomy ( Nguyen et al., 2023 ) and multidisciplinary science ( Shaikh et al., 2023 ) , with some models such as SciGLM ( Zhang et al., 2024a ) and UniSmart ( Chi et al., 2024 ) that aim to cover diverse scientific domains in a single model.
Recently, several works show that powerful general-purpose LLMs can also show strong capabilities in scientific tasks, such as medical question answering ( AI4Science & Quantum, 2023 ; Singhal et al., 2023a ) , chemistry experimentation ( Zheng et al., 2023b ) and applied mechanics ( Brodnik et al., 2023 ) .
However, the language model’s reliance on information memorized within its parameters leads to frequent hallucinations in its output ( Li et al., 2024b ) .

**中文译文 · 机器初译**

科学型大语言模型已应用于多个领域，包括生物医学（Phan等，2021；Yuan等，2022；Luo等，2022）、医学（Singhal等，2023a；Gu等，2024；Tan等，2023；Singhal等，2023b）、生物医学（Zhang等，2024b；Fang等，2024；Li等，2024a）、地球科学（Feng等，2023）、天文学（Nguyen等，2023）以及多学科科学（Shaikh等，2023）。部分模型如SciGLM（Zhang等，2024a）和UniSmart（Chi等，2024）则旨在通过单一模型覆盖多种科学领域。
最近有多项研究表明，强大的通用大语言模型在科学任务中也能展现出强大的能力，例如医疗问题解答（AI4Science & Quantum, 2023；Singhal等，2023a）、化学实验（Zheng等，2023b）以及应用力学领域（Brodnik等，2023）。然而，语言模型依赖于其参数中存储的信息，这导致其输出中频繁出现幻觉现象（Li等，2024b）。

### openscholar-0163

**English original**

LMs to assist scientists.

**中文译文 · 机器初译**

大语言模型助力科学家工作。

### openscholar-0164

**English original**

Recent studies have also examined LLMs’ capabilities to assist scientists in performing a range of scientific procedures, including generating novel research ideas ( Baek et al., 2024 ; Yang et al., 2023 ) and automating experimental code generation ( Huang et al., 2023 ; Tian et al., 2024 ) . Our work, however, focuses specifically on benchmarking and developing methods for automating literature reviews and addressing questions related to up-to-date research—tasks that are crucial to, and particularly challenging, for scientific inquiry.
Several concurrent studies have attempted to build retrieval-augmented pipelines using proprietary LLMs and external APIs (e.g., Semantic Scholar API) for scientific literature review agents ( Agarwal et al., 2024 ; Skarlinski et al., 2024 ; Wang et al., 2024 ) . While these studies and our research all explore the potential of retrieval-augmented LMs in automating literature synthesis, prior works often relied on proprietary, black-box systems and limited evaluations, which commonly entail small-scale human evaluation or simplified setups such as multiple-choice QA.
In contrast, our work introduces a comprehensive benchmark with automated metrics, involves user studies with experts across three scientific disciplines, and develops new methodologies to train specialized open models. OpenScholar significantly outperforms previously introduced systems and shows superiority over human experts in five domains.

**中文译文 · 机器初译**

近期研究还探讨了大语言模型在协助科学家完成各类科学操作方面的能力，包括生成新的研究思路（Baek等，2024；Yang等，2023）以及自动生成实验代码（Huang等，2023；Tian等，2024）。然而，我们的工作则专注于对文献综述进行标准化评估，并开发自动化方法以处理与最新研究相关的问题——这些任务对于科学研究来说至关重要，同时也具有很大的挑战性。
多项同时进行的研究尝试使用专有大语言模型与外部 API（如 Semantic Scholar API）来构建检索增强流程，用于科学文献综述智能体（Agarwal等，2024；Skarlinski等，2024；Wang等，2024）。尽管这些研究和我们的研究都探讨了检索增强大语言模型在自动化文献合成方面的潜力，但以往的研究通常依赖专有且黑盒式的系统，且评估范围有限，往往仅采用小规模人工评估或简单的测试方式，例如选择题问答形式。
相比之下，我们的研究引入了包含自动化指标的全面基准测试，进行了涉及三个科学领域专家的用户研究，并开发了训练专用开放模型的新方法。OpenScholar的表现显著优于以往提出的系统，在五个领域也优于人类专家。

### openscholar-0165

**English original**

Benchmarks for scientific literature understanding.

**中文译文 · 机器初译**

科学文献理解基准测试。

### openscholar-0166

**English original**

Several works have developed benchmarks to evaluate models’ abilities to understand scientific literature. Prior datasets, such as SciFact ( Wadden et al., 2020 ) , QASPER ( Dasigi et al., 2021 ) , and QASA ( Lee et al., 2023 ) , largely focus on single-paper settings, where the necessary information to answer queries is contained within a single pre-selected paper. However, in real-world scenarios, experts often need to synthesize information from multiple papers to answer questions. To address this gap, ScholarQABench introduces newly annotated tasks that require reasoning across multiple papers.
There are also scientific summarization tasks, such as Multi-XScience ( Lu et al., 2020 ) , where models are provided with multiple papers and asked to generate summaries, typically based on the related work sections of those papers. However, in this work, we focus on scenarios where the relevant papers are not specified in advance, making the task more challenging.
Recently, Xu et al. (2024) introduced KIWI, a dataset containing 200 questions and human-verified or edited answers generated by state-of-the-art LLMs, with a focus on the NLP domain. KIWI also provides a set of relevant papers that models must consider. While both KIWI and ScholarQABench feature multi-paper, information-seeking tasks, ScholarQABench includes both human-written answers and automatic evaluation pipelines. In contrast, KIWI focuses more on human evaluations, and its reference answers are primarily model-generated.

**中文译文 · 机器初译**

已有多项研究开发了评估大语言模型理解科学文献能力的基准测试。以往的数据集如 SciFact（Wadden等，2020）、QASPER（Dasigi等，2021）和 QASA（Lee等，2023）主要针对单篇论文场景，其中回答查询所需的信息都包含于预先选定的单篇论文中。然而在现实场景中，专家通常需要整合多篇论文中的信息来回答问题。为了填补这一空白，ScholarQABench引入了新标注任务，这些任务要求对多篇论文进行综合推理。
还有科学总结任务，例如 Multi-XScience（Lu等人，2020年）项目，其中模型被提供多篇论文，要求生成摘要，通常基于这些论文中的相关工作部分。然而，在本研究中，我们关注那些无法提前指定相关论文的场景，这使得任务更具挑战性。最近，Xu等人（2024年）引入了KIWI数据集，该数据集包含200道问题以及由先进大语言模型生成且经过人类验证或编辑的答案，主要聚焦于自然语言处理领域。KIWI还提供了一组模型必须考虑的相关论文。
虽然 KIWI 和 ScholarQABench 都包含多篇文献及信息检索任务，但 ScholarQABench 还包含人工撰写的答案和自动评估流程。相比之下，KIWI 则更侧重人工评估，其参考答案主要由模型生成。

### openscholar-0167

**English original**

7 Conclusion

**中文译文 · 机器初译**

7 结论

### openscholar-0168

**English original**

In order to further research on LM-based systems that can assist scientific progress, we introduce OpenScholar and ScholarQABench , which can help navigate the complex, ever-growing task of scientific literature review. OpenScholar , a retrieval-augmented system, leverages open-checkpoint LLMs and trained retrieval models to iteratively refine scientific output, addressing challenges such as hallucinations and citation accuracy. ScholarQABench , a novel large-scale benchmark, provides a standardized way to evaluate literature review automation across multiple scientific domains.
In evaluations using ScholarQABench , OpenScholar demonstrates substantial improvements, outperforming existing systems, including GPT-4o and the concurrent proprietary system PaperQA2. Our expert evaluation across three scientific disciplines reveals that ScholarQABench , when paired with fully open-checkpoint models and open-access data stores, generates answers that are more helpful than those produced by expert annotators, who required an hour per annotation. This approach also significantly increases coverage. OpenScholar using our trained 8B and GPT4o achieves a 51% and 70% win rate against human-generated answers.
We open-source the OpenScholar code, data, model checkpoints, datastores, and ScholarQABench , along with a public demo, to support and accelerate future research efforts.

**中文译文 · 机器初译**

为了进一步研究能够助力科学进展的大语言模型相关系统，我们引入了 OpenScholar 和 ScholarQABench，这两个工具可以帮助应对复杂且不断增长的科学文献综述任务。作为一种基于检索增强的系统，OpenScholar 利用开放的检查点大语言模型和训练好的检索模型来逐步优化科学成果，从而解决幻觉现象和引用准确性等问题。而新型大规模基准测试 ScholarQABench 则提供了一种标准化的方法，用于评估不同科学领域中的文献综述自动化水平。
在使用 ScholarQABench 进行的评估中，OpenScholar 取得了显著改进，其表现优于现有的系统，包括 GPT-4o 以及同期的专有系统 PaperQA2。我们在三个科学领域进行的专家评估表明，当 ScholarQABench 与完全开放检查点模型及开放访问数据存储相结合时，其生成的答案比专家标注员每小时需花费一小时的答案更有帮助，且覆盖范围也大幅扩大。使用我们训练的 8B 模型和 GPT4o 的 OpenScholar 在针对人类生成答案的测试中分别获得了 51% 和 70% 的正确率。
我们开源了 OpenScholar 代码、数据、模型检查点、数据存储以及 ScholarQABench，并提供了公开演示版本，以支持和加速未来的研究工作。

### openscholar-0169

**English original**

Limitations

**中文译文 · 机器初译**

局限性

### openscholar-0170

**English original**

We highlight several limitations of our work in this section. It is important to note that we do not claim that LM-based systems can fully automate scientific literature synthesis.
To further advance research in this area, we are releasing both ScholarQABench and OpenScholar to the community.

**中文译文 · 机器初译**

在本节中，我们指出了本研究的若干局限性。需要指出的是，我们并不声称基于大语言模型的系统能够完全实现科学文献的自动化合成。为了推动该领域的研究发展，我们正在向社区发布 ScholarQABench 和 OpenScholar 工具。

### openscholar-0171

**English original**

Limitations of ScholarQABench .

**中文译文 · 机器初译**

ScholarQABench 的局限性。

### openscholar-0172

**English original**

There are several limitations to ScholarQABench . First, due to the cost and time required to engage expert annotators—individuals with either a Ph.D. or are currently pursuing one in relevant fields—the evaluation dataset with human-written answers is relatively small (e.g., 110 for CS-LFQA and 108 for expert-written answers). This limited dataset may introduce statistical variance and potential biases stemming from the specific expertise of the annotators. To support future research in expanding the size and scope of ScholarQABench , we open-source our data and annotation pipelines.

**中文译文 · 机器初译**

ScholarQABench 存在若干局限性。首先，由于需要耗费成本与时间来聘请专家标注员——这些人员通常拥有博士学位或正在相关领域攻读学位——包含人工回答的评估数据集规模相对较小（例如，CS-LFQA 的数据集为 110 条，专家撰写的答案数据集为 108 条）。这种有限的数据集可能会引入统计波动，并因标注员的特定专业背景而产生潜在偏差。为了支持未来在扩大 ScholarQABench 规模与范围方面的研究，我们将其数据及标注流程开源共享。

### openscholar-0173

**English original**

Second, our automatic evaluation pipelines may not always perfectly capture the quality of generated content. For example, in Scholar-CS , we combine various components (e.g., length, excerpts, rubric items) using heuristically determined weight terms. Further, we discovered that often annotators asked for specific kinds of ancillary information in their rubrics—background, elaborations and challenges—even though these aspects might not be strictly required to answer the question. In our experiments, we found that LLMs are proficient at generating the background aspects, which can give them an advantage over systems that directly answer a query but do not satisfy all the constraints of the rubrics. Moreover, future systems could potentially take advantage of the stylistic biases in the rubrics and be prompted to address more rubric elements in a way that does not improve answer quality. Although we carefully analyzed the correlation between final scores and human expert evaluations, there is still room for improvement in refining which aspects should be emphasized and how these scores should be aggregated. Additionally, our evaluations of citation precision and recall are conducted at the sentence level, but we found that some sentences without direct citations are often supported by citations in adjacent sentences. As a result, our precision and recall metrics might be overly strict, potentially underestimating the true citation accuracy. We also note that our annotations were captured at particular times (July 2024 for Scholar-CS and September 2024 for Scholar-Multi ), and may not reflect subsequent scientific developments.
Researchers who use our evaluation benchmark should ignore papers published after these dates for a fair comparison.

**中文译文 · 机器初译**

其次，我们的自动评估流程可能并不总能准确反映生成内容的质量。例如，在 Scholar-CS 中，我们采用启发式确定的权重机制来整合各种要素（如长度、摘录、评分标准项）。此外，我们发现标注者通常在评分标准中要求特定类型的辅助信息——背景说明、详细阐述及挑战点——尽管这些方面未必是回答问题的必要条件。
在我们的实验中发现，大语言模型能够熟练生成背景信息，这使其比那些直接回答查询但无法满足评分标准所有要求的系统具有优势。此外，未来的系统或许可以利用评分标准中的风格偏见，被引导去处理更多评分标准要素，而无需提升答案质量。尽管我们仔细分析了最终得分与人类专家评估之间的关联，但在确定应强调哪些方面以及如何汇总这些得分方面仍有改进空间。
此外，我们对引用精确度和召回率的评估是在句子层面进行的，但我们发现一些没有直接引用的句子往往由相邻句子中的引用支持。因此，我们的精确度和召回率指标可能过于严格，从而可能低估了真实的引用准确性。我们还注意到，我们的注释是在特定时间采集的（Scholar-CS为2024年7月，Scholar-Multi为2024年9月），可能无法反映后续的科学发展情况。使用我们评估基准的研究人员应忽略这些日期之后发表的论文，以便进行公平比较。

### openscholar-0174

**English original**

Lastly, ScholarQABench primarily focuses on computer science, biomedicine, and physics, with no instances from social sciences or other engineering and scientific disciplines. We recognize that our findings may not fully generalize to other domains, particularly those with more restricted access to paper data.

**中文译文 · 机器初译**

最后，ScholarQABench主要聚焦于计算机科学、生物医学和物理学领域，没有来自社会科学或其他工程与科学学科的研究案例。我们认识到，我们的研究结果可能无法完全适用于其他领域，尤其是那些获取论文数据较为受限的领域。

### openscholar-0175

**English original**

Limitations of OpenScholar .

**中文译文 · 机器初译**

OpenScholar 的局限性。

### openscholar-0176

**English original**

While OpenScholar demonstrates strong performance on ScholarQABench and in human evaluations, as discussed in the relevant sections, our expert annotators identified several limitations.
Despite these issues, we believe OpenScholar remains a valuable tool for supporting human experts.

**中文译文 · 机器初译**

正如相关章节所讨论的，尽管 OpenScholar 在 ScholarQABench 测试及人工评估中表现优异，但我们的专业注释者发现了若干局限性。尽管存在这些问题，我们认为 OpenScholar 仍然是支持人类专家的重要工具。

### openscholar-0177

**English original**

First, as highlighted by our expert annotators, OpenScholar does not consistently retrieve the most representative or relevant papers for certain queries. Enhancing retrieval methodologies by incorporating additional information, such as citation networks or metadata like publication recency, could significantly improve its performance. OpenScholar outputs may contain factual inaccuracies or unsupported information, particularly in versions based on our 8B model, which has limited capacity for instruction-following and scientific knowledge.
Future work can explore training that further improve OpenScholar -8B.
In parallel, although it is competitive, OpenScholar -GPT4o relies on the proprietary GPT4o API, which may evolve over time, making exact reproduction of results challenging. OpenScholar does not use license-protected papers during inference time.
There are ongoing discussions on how to ensure fair data use in retrieval-augmented LMs, and we leave the exploration of properly incorporating copyright-protected content to future work.

**中文译文 · 机器初译**

首先，正如我们的专家注释者所指出的，OpenScholar 在某些查询下无法始终检索到最具代表性或相关的论文。通过引入额外信息，如引用网络或出版时间等元数据来改进检索方法，可以显著提升其性能。OpenScholar 的输出可能包含事实错误或不具依据的信息，尤其是在基于 8B 模型的版本中，该模型在遵循指令和获取科学知识方面能力有限。未来的研究可以探索进一步训练以改进 OpenScholar-8B 的效果。
同时，尽管 OpenScholar-GPT4o 具有竞争力，但它依赖自研的 GPT4o API，而该 API 可能会随时间发展变化，因此难以完全复现实验结果。在推理过程中，OpenScholar 不会使用受许可保护的文献。目前正在就如何确保检索增强型大语言模型中的数据使用公平展开讨论，我们将如何合理融合受版权保护的内容问题留待后续研究解决。

### openscholar-0178

**English original**

We encourage future research to address these limitations and continue improving LM-based systems for scientific literature review.

**中文译文 · 机器初译**

我们鼓励未来的研究解决这些局限性问题，并继续改进基于大语言模型的科学文献综述系统。

### openscholar-0179

**English original**

Limitations of our human evaluation process.

**中文译文 · 机器初译**

我们人工评估过程的局限性。

### openscholar-0180

**English original**

In our human evaluations, annotators performed fine-grained assessments on aspects such as coverage, relevance, organization, and usefulness, while other factors such as citation precision and recall were separately evaluated. As a result, when assessing usefulness or pairwise preferences, annotators may have focused more on the overall quality of writing instead of carefully evaluating factual correctness or citation accuracy. We leave more detailed human analysis on citation accuracy, validity, and factuality for future work.

**中文译文 · 机器初译**

在我们的人类评估中，注释者对涵盖性、相关性、组织性和实用性等方面进行了细致评估，而引用精确度和召回率等其他因素则被单独评估。因此，在评估实用性或成对偏好时，注释者可能更关注文章的整体质量，而未能仔细审查事实准确性或引用精度。关于引用精度、有效性和事实性的详细人类分析，我们留待后续研究进行。

### openscholar-0181

**English original**

Our evaluations were conducted by 16 Ph.D. students and postdoctoral professionals, and we made an effort to align their expertise with the topics being evaluated. However, since research often demands deep domain knowledge, the annotators may not have captured more nuanced differences for questions outside their immediate areas of expertise.
Additionally, these evaluations were based on 108 questions spanning three scientific disciplines, meaning that findings may not fully generalize to other fields or domains.

**中文译文 · 机器初译**

我们的评估工作由16名博士学生和博士后专业人士完成，我们努力使他们的专业背景与所评估的主题相匹配。然而，由于研究通常需要深厚的领域知识，标注人员可能无法准确捕捉其专业领域之外问题的更细微差异。此外，这些评估基于涵盖三个科学领域的108个问题，因此研究结果可能无法完全适用于其他领域或学科。

### openscholar-0182

**English original**

Author Contribution

**中文译文 · 机器初译**

作者贡献

### openscholar-0183

**English original**

The author contributions are summarized below:

**中文译文 · 机器初译**

作者的贡献总结如下：

### openscholar-0184

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0185

**English original**

Project Lead : Akari Asai

**中文译文 · 机器初译**

项目负责人：浅井明

### openscholar-0186

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0187

**English original**

Project Conception : Akari Asai, Wen-tau Yih, Pang Wei Koh, Hannaneh Hajishirzi

**中文译文 · 机器初译**

项目构思：Aisa Akari、Yih Wen-tau、Koh Pang Wei、Hajishirzi Hannaneh

### openscholar-0188

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0189

**English original**

OpenScholar Development : Akari Asai, Weijia Shi, Rulin Shao, Jacqueline He

**中文译文 · 机器初译**

OpenScholar 开发项目：浅井明、石伟佳、邵瑞林、何杰

### openscholar-0190

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0191

**English original**

OpenScholar Public Demo Development : Amanpreet Singh, Joseph Chee Cheng, Akari Asai, Rulin Shao, Doug Downey, Matt Latzke

**中文译文 · 机器初译**

OpenScholar 公开演示开发：Amanpreet Singh、Joseph Chee Cheng、Akari Asai、Rulin Shao、Doug Downey、Matt Latzke

### openscholar-0192

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0193

**English original**

peS2o Construction : Luca Soldaini, Kyle Lo

**中文译文 · 机器初译**

peS2o 构建方法：Luca Soldaini、Kyle Lo

### openscholar-0194

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0195

**English original**

Datastore (peS2o Index) Construction : Rulin Shao, Jacqueline He, Akari Asai

**中文译文 · 机器初译**

数据存储库（peS2o 索引）构建：邵瑞林、何杰、浅井明

### openscholar-0196

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0197

**English original**

Legal Discussions on Paper Licensing : Kyle Lo, Luca Soldaini, Doug Downey, Pang Wei Koh, Amanpreet Singh, Akari Asai

**中文译文 · 机器初译**

关于纸质许可的法律讨论：Kyle Lo、Luca Soldaini、Doug Downey、Pang Wei Koh、Amanpreet Singh、Akari Asai

### openscholar-0198

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0199

**English original**

OpenScholar -LM Training : Akari Asai, Weijia Shi

**中文译文 · 机器初译**

OpenScholar -LM 训练：浅井明、石伟佳

### openscholar-0200

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0201

**English original**

OpenScholar -Retrievers Training and Evaluation : Akari Asai, Jacqueline He, Rulin Shao

**中文译文 · 机器初译**

OpenScholar -检索器训练与评估：Asai Akari、He Jacqueline、Shao Rulin

### openscholar-0202

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0203

**English original**

ScholarQABench Design and Conception : Akari Asai, Pang Wei Koh, David Wadden, Doug Downey, Kyle Lo, Weijia Shi, Amanpreet Singh, Sergey Feldman, Dan Weld

**中文译文 · 机器初译**

ScholarQABench 设计与构思：Akari Asai、Pang Wei Koh、David Wadden、Doug Downey、Kyle Lo、Weijia Shi、Amanpreet Singh、Sergey Feldman、Dan Weld

### openscholar-0204

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0205

**English original**

ScholarQABench Collections (Single-paper Tasks) : Akari Asai

**中文译文 · 机器初译**

ScholarQABench 集合（单篇论文任务）：浅井明

### openscholar-0206

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0207

**English original**

ScholarQABench Evaluation Pipeline Design and Development : Akari Asai

**中文译文 · 机器初译**

ScholarQABench评估流程设计与开发：浅井明

### openscholar-0208

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0209

**English original**

ScholarQA -CS Collection and Evaluation : Doug Downey, Amanpreet Singh, Sergey Feldman, Dan Weld, Mike D’arcy

**中文译文 · 机器初译**

ScholarQA -CS 数据集收集与评估：Doug Downey、Amanpreet Singh、Sergey Feldman、Dan Weld、Mike D’arcy

### openscholar-0210

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0211

**English original**

ScholarQA -Multi Collection : Akari Asai, Minyang Tian, Rulin Shao, Jacqueline He, Weijia Shi, Pan Ji, Shengyan Liu, Hao Tong, Bohao Wu, Yanyu Xiong

**中文译文 · 机器初译**

ScholarQA -多数据集版本：浅井明、田敏阳、邵润林、何杰琳、施伟佳、季攀、刘胜岩、童浩、吴博浩、熊燕宇

### openscholar-0212

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0213

**English original**

ScholarQA -Neuro, Bio Collection : Doug Downey

**中文译文 · 机器初译**

ScholarQA -神经与生物领域合集：道格·道尼

### openscholar-0214

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0215

**English original**

Results and Codebases : Akari Asai, Jacqueline He, Rulin Shao, Weijia Shi, Amanpreet Singh

**中文译文 · 机器初译**

结果与代码库：Asai Akari、Jacqueline He、Shao Rulin、Shi Weijia、Amanpreet Singh

### openscholar-0216

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0217

**English original**

Human Evaluation Design : Akari Asai, Pang Wei Koh, Graham Neubig

**中文译文 · 机器初译**

人类评估设计：浅井明、潘伟科、格雷厄姆·诺伊比格

### openscholar-0218

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0219

**English original**

Human Evaluation Interface Development and Supervision : Akari Asai, Minyang Tian

**中文译文 · 机器初译**

人类评估界面开发与监督研究：浅井明、田民阳

### openscholar-0220

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0221

**English original**

Manuscript Writing : Akari Asai, Jacqueline He, Doug Downey, Amanpreet Singh, Kyle Lo, Pang Wei Koh

**中文译文 · 机器初译**

文稿撰写：Akari Asai、Jacqueline He、Doug Downey、Amanpreet Singh、Kyle Lo、Pang Wei Koh

### openscholar-0222

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0223

**English original**

OpenScholar Public Demo Testing : Everyone

**中文译文 · 机器初译**

OpenScholar 公开演示测试：所有人

### openscholar-0224

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0225

**English original**

Manuscript Editing : Everyone

**中文译文 · 机器初译**

文稿编辑：所有人

### openscholar-0226

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0227

**English original**

Advisory : Pang Wei Koh, Hannaneh Hajishirzi, Doug Downey, Wen-tau Yih, Graham Neubig, Dan Weld, Luke Zettlemoyer

**中文译文 · 机器初译**

建议：Pang Wei Koh、Hannaneh Hajishirzi、Doug Downey、Wen-tau Yih、Graham Neubig、Dan Weld、Luke Zettlemoyer

### openscholar-0228

**English original**

Acknowledgments

**中文译文 · 机器初译**

致谢

### openscholar-0229

**English original**

We thank our expert annotators, for their help curating high-quality data, and Jenna Sparks at the Ai2 Annotation team for managing and supervising data collection process.
We thank Yizhong Wang for his help in developing the human evaluation interface; Hamish Ivison for providing an earlier version of the Tulu v3 instruction tuning data we used for OpenScholar 8B training; and Seungone Kim for his help on Prometheus evaluations. We thank Jena Hwang for analyzing limitations of our evaluation data.
For assistance with the public demo, we thank Chloe Anastasiades, Crystal Nam, Sophie Lebrecht, Taira Anderson, and Will Smith.
We thank Fangyuan Xu, Eunsol Choi, Aran Komatsuzaki, Sean Welleck, Xiang Yue, Tong Chen, Vijay Viswanathan, Shannon Shen and the members of H2lab and Neulab students for fruitful discussions on this project and feedback on our human evaluation experiments.
PWK is supported by the Singapore National Research Foundation and the National AI Group in the Singapore Ministry of Digital Development and Information under the AI Visiting Professorship Programme (award number AIVP-2024-001).
This work partially done while AA is part of the UW-Meta AI Mentorship program.

**中文译文 · 机器初译**

我们感谢那些专业标注人员在整理高质量数据方面提供的帮助，也感谢 Ai2 Annotation 团队的 Jenna Sparks在管理与监督数据收集过程方面所做出的贡献。我们感谢 Yizhong Wang在开发人类评估界面方面的协助；Hamish Ivison提供了我们在 OpenScholar 8B 训练中使用的 Tulu v3 指令调整数据的早期版本；Seungone Kim在 Prometheus 评估工作上的帮助。我们感谢 Jena Hwang对评估数据局限性进行分析的工作。对于公共演示方面的协助，我们感谢 Chloe Anastasiades、Crystal Nam、Sophie Lebrecht、Taira Anderson和Will Smith。
我们感谢方远徐、Eunsol Choi、Aran Komatsuzaki、Sean Welleck、项跃、陈彤、Vijay Viswanathan、Shannon Shen以及H2lab和Neulab学生团队的成员们就该项目进行的富有成效的讨论，以及对我们人类评估实验的反馈。PWK由新加坡国家研究基金会和新加坡数字发展与信息部国家人工智能小组在AI访问教授计划下支持（授予编号AIVP-2024-001）。这项工作部分由AA在UW-Meta AI导师计划中完成。

### openscholar-0230

**English original**

References

**中文译文 · 机器初译**

参考文献

### openscholar-0231

**English original**

Agarwal et al. (2024) Shubham Agarwal, Issam H Laradji, Laurent Charlin, and Christopher Pal. Litllm: A toolkit for scientific literature review. arXiv preprint arXiv:2402.01788 , 2024. URL https://arxiv.org/abs/2402.01788 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Agarwal et al. (2024) Shubham Agarwal, Issam H Laradji, Laurent Charlin, and Christopher Pal. Litllm: A toolkit for scientific literature review. arXiv preprint arXiv:2402.01788 , 2024. URL https://arxiv.org/abs/2402.01788 .

### openscholar-0232

**English original**

AI4Science & Quantum (2023) Microsoft Research AI4Science and Microsoft Azure Quantum. The impact of large language models on scientific discovery: a preliminary study using gpt-4. arXiv preprint arXiv:2311.07361 , 2023. URL https://arxiv.org/abs/2311.07361 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

AI4Science & Quantum (2023) Microsoft Research AI4Science and Microsoft Azure Quantum. The impact of large language models on scientific discovery: a preliminary study using gpt-4. arXiv preprint arXiv:2311.07361 , 2023. URL https://arxiv.org/abs/2311.07361 .

### openscholar-0233

**English original**

Asai & Choi (2021) Akari Asai and Eunsol Choi. Challenges in information-seeking QA: Unanswerable questions and paragraph retrieval. In ACL , 2021. URL https://aclanthology.org/2021.acl-long.118 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Asai & Choi (2021) Akari Asai and Eunsol Choi. Challenges in information-seeking QA: Unanswerable questions and paragraph retrieval. In ACL , 2021. URL https://aclanthology.org/2021.acl-long.118 .

### openscholar-0234

**English original**

Asai et al. (2023) Akari Asai, Timo Schick, Patrick Lewis, Xilun Chen, Gautier Izacard, Sebastian Riedel, Hannaneh Hajishirzi, and Wen-tau Yih. Task-aware retrieval with instructions. In Findings of the Association for Computational Linguistics , 2023. URL https://aclanthology.org/2023.findings-acl.225 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Asai et al. (2023) Akari Asai, Timo Schick, Patrick Lewis, Xilun Chen, Gautier Izacard, Sebastian Riedel, Hannaneh Hajishirzi, and Wen-tau Yih. Task-aware retrieval with instructions. In Findings of the Association for Computational Linguistics , 2023. URL https://aclanthology.org/2023.findings-acl.225 .

### openscholar-0235

**English original**

Asai et al. (2024) Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, and Hannaneh Hajishirzi. Self-RAG: Learning to retrieve, generate, and critique through self-reflection. In ICLR , 2024. URL https://openreview.net/forum?id=hSyW5go0v8 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Asai et al. (2024) Akari Asai, Zeqiu Wu, Yizhong Wang, Avirup Sil, and Hannaneh Hajishirzi. Self-RAG: Learning to retrieve, generate, and critique through self-reflection. In ICLR , 2024. URL https://openreview.net/forum?id=hSyW5go0v8 .

### openscholar-0236

**English original**

Azerbayev et al. (2024) Zhangir Azerbayev, Hailey Schoelkopf, Keiran Paster, Marco Dos Santos, Stephen Marcus McAleer, Albert Q. Jiang, Jia Deng, Stella Biderman, and Sean Welleck. Llemma: An open language model for mathematics. In ICLR , 2024. URL https://openreview.net/forum?id=4WnqRR915j .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Azerbayev et al. (2024) Zhangir Azerbayev, Hailey Schoelkopf, Keiran Paster, Marco Dos Santos, Stephen Marcus McAleer, Albert Q. Jiang, Jia Deng, Stella Biderman, and Sean Welleck. Llemma: An open language model for mathematics. In ICLR , 2024. URL https://openreview.net/forum?id=4WnqRR915j .

### openscholar-0237

**English original**

Baek et al. (2024) Jinheon Baek, Sujay Kumar Jauhar, Silviu Cucerzan, and Sung Ju Hwang. Researchagent: Iterative research idea generation over scientific literature with large language models. arXiv preprint arXiv:2404.07738 , 2024. URL https://arxiv.org/abs/2404.07738 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Baek et al. (2024) Jinheon Baek, Sujay Kumar Jauhar, Silviu Cucerzan, and Sung Ju Hwang. Researchagent: Iterative research idea generation over scientific literature with large language models. arXiv preprint arXiv:2404.07738 , 2024. URL https://arxiv.org/abs/2404.07738 .

### openscholar-0238

**English original**

Brodnik et al. (2023) Neal R. Brodnik, Samuel Carton, Caelin Muir, Satanu Ghosh, Doug Downey, McLean P. Echlin, Tresa M. Pollock, and Samantha Daly. Perspective: Large Language Models in Applied Mechanics. Journal of Applied Mechanics , 2023. URL https://doi.org/10.1115/1.4062773 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Brodnik et al. (2023) Neal R. Brodnik, Samuel Carton, Caelin Muir, Satanu Ghosh, Doug Downey, McLean P. Echlin, Tresa M. Pollock, and Samantha Daly. Perspective: Large Language Models in Applied Mechanics. Journal of Applied Mechanics , 2023. URL https://doi.org/10.1115/1.4062773 .

### openscholar-0239

**English original**

Chi et al. (2024) Chenglei Chi, Qiaozi Cheng, Zheng Wen, Rongzhe Lin, Chunyang Wen, Zhaowei Wang, Cuiling Gao, Jian Zhang, Xu Jiang, Jian Yin, et al. Uni-SMART: Universal science multimodal analysis and research transformer. arXiv preprint arXiv:2403.10301 , 2024. URL https://arxiv.org/abs/2403.10301 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Chi et al. (2024) Chenglei Chi, Qiaozi Cheng, Zheng Wen, Rongzhe Lin, Chunyang Wen, Zhaowei Wang, Cuiling Gao, Jian Zhang, Xu Jiang, Jian Yin, et al. Uni-SMART: Universal science multimodal analysis and research transformer. arXiv preprint arXiv:2403.10301 , 2024. URL https://arxiv.org/abs/2403.10301 .

### openscholar-0240

**English original**

Choi et al. (2018) Eunsol Choi, He He, Mohit Iyyer, Mark Yatskar, Wen-tau Yih, Yejin Choi, Percy Liang, and Luke Zettlemoyer. QuAC: Question answering in context. In EMNLP , Brussels, Belgium, 2018. Association for Computational Linguistics. URL https://aclanthology.org/D18-1241 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Choi et al. (2018) Eunsol Choi, He He, Mohit Iyyer, Mark Yatskar, Wen-tau Yih, Yejin Choi, Percy Liang, and Luke Zettlemoyer. QuAC: Question answering in context. In EMNLP , Brussels, Belgium, 2018. Association for Computational Linguistics. URL https://aclanthology.org/D18-1241 .

### openscholar-0241

**English original**

Dasigi et al. (2021) Pradeep Dasigi, Kyle Lo, Iz Beltagy, Arman Cohan, Noah A. Smith, and Matt Gardner. A dataset of information-seeking questions and answers anchored in research papers. In NAACL , 2021. URL https://aclanthology.org/2021.naacl-main.365 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Dasigi et al. (2021) Pradeep Dasigi, Kyle Lo, Iz Beltagy, Arman Cohan, Noah A. Smith, and Matt Gardner. A dataset of information-seeking questions and answers anchored in research papers. In NAACL , 2021. URL https://aclanthology.org/2021.naacl-main.365 .

### openscholar-0242

**English original**

Dubey et al. (2024) Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Amy Yang, Angela Fan, et al. The llama 3 herd of models. arXiv preprint arXiv:2407.21783 , 2024. URL https://arxiv.org/abs/2407.21783 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Dubey et al. (2024) Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Amy Yang, Angela Fan, et al. The llama 3 herd of models. arXiv preprint arXiv:2407.21783 , 2024. URL https://arxiv.org/abs/2407.21783 .

### openscholar-0243

**English original**

Dubois et al. (2024) Yann Dubois, Balázs Galambosi, Percy Liang, and Tatsunori B Hashimoto. Length-controlled alpacaeval: A simple way to debias automatic evaluators. In COLM , 2024. URL https://openreview.net/forum?id=CybBmzWBX0 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Dubois et al. (2024) Yann Dubois, Balázs Galambosi, Percy Liang, and Tatsunori B Hashimoto. Length-controlled alpacaeval: A simple way to debias automatic evaluators. In COLM , 2024. URL https://openreview.net/forum?id=CybBmzWBX0 .

### openscholar-0244

**English original**

Fang et al. (2024) Ziheng Fang, Guangxu Wang, Jinsung Xu, Yifeng Cai, Jingya Wang, Qicheng Qiu, Ruixuan Zhang, Xiaofeng Chen, Jinna Wang, Jiayi Dong, et al. Biomedgpt: A unified and generalist biomedical generative pre-trained transformer for vision, language, and knowledge reasoning tasks. arXiv preprint arXiv:2403.18421 , 2024. URL https://arxiv.org/abs/2305.17100 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Fang et al. (2024) Ziheng Fang, Guangxu Wang, Jinsung Xu, Yifeng Cai, Jingya Wang, Qicheng Qiu, Ruixuan Zhang, Xiaofeng Chen, Jinna Wang, Jiayi Dong, et al. Biomedgpt: A unified and generalist biomedical generative pre-trained transformer for vision, language, and knowledge reasoning tasks. arXiv preprint arXiv:2403.18421 , 2024. URL https://arxiv.org/abs/2305.17100 .

### openscholar-0245

**English original**

Feng et al. (2023) Qiang Feng, Yuxi Li, Jintao Zou, Zhiwei Li, Zhiqiang Ding, Chao Zhang, Qinyan Zhang, Xueqi Hu, Weihao Peng, Xiangyu Meng, et al. K2: A foundation language model for geoscience knowledge understanding and generation. arXiv preprint arXiv:2306.05064 , 2023.

**原文保留（专名、技术内容或文献信息） · 保留原文**

Feng et al. (2023) Qiang Feng, Yuxi Li, Jintao Zou, Zhiwei Li, Zhiqiang Ding, Chao Zhang, Qinyan Zhang, Xueqi Hu, Weihao Peng, Xiangyu Meng, et al. K2: A foundation language model for geoscience knowledge understanding and generation. arXiv preprint arXiv:2306.05064 , 2023.

### openscholar-0246

**English original**

Gao et al. (2023) Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. Enabling large language models to generate text with citations. arXiv preprint arXiv:2305.14627 , 2023. URL https://arxiv.org/abs/2305.14627 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Gao et al. (2023) Tianyu Gao, Howard Yen, Jiatong Yu, and Danqi Chen. Enabling large language models to generate text with citations. arXiv preprint arXiv:2305.14627 , 2023. URL https://arxiv.org/abs/2305.14627 .

### openscholar-0247

**English original**

Gu et al. (2024) Xiaodan Gu, Zhen Wang, Zhengliang Shi, Hongyan Li, Xiaoye Chen, and Dehong Cheng. Me-llama: Foundation model for medical language understanding and generation. arXiv preprint arXiv:2402.12749 , 2024. URL https://arxiv.org/abs/2402.12749 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Gu et al. (2024) Xiaodan Gu, Zhen Wang, Zhengliang Shi, Hongyan Li, Xiaoye Chen, and Dehong Cheng. Me-llama: Foundation model for medical language understanding and generation. arXiv preprint arXiv:2402.12749 , 2024. URL https://arxiv.org/abs/2402.12749 .

### openscholar-0248

**English original**

Guu et al. (2020) Kelvin Guu, Kenton Lee, Zora Tung, Panupong Pasupat, and Mingwei Chang. Retrieval augmented language model pre-training. In International Conference on Machine Learning , 2020. URL https://dl.acm.org/doi/pdf/10.5555/3524938.3525306 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Guu et al. (2020) Kelvin Guu, Kenton Lee, Zora Tung, Panupong Pasupat, and Mingwei Chang. Retrieval augmented language model pre-training. In International Conference on Machine Learning , 2020. URL https://dl.acm.org/doi/pdf/10.5555/3524938.3525306 .

### openscholar-0249

**English original**

Huang et al. (2023) Qian Huang, Jian Vora, Percy Liang, and Jure Leskovec. Mlagentbench: Evaluating language agents on machine learning experimentation. In International Conference on Machine Learning , 2023. URL https://api.semanticscholar.org/CorpusID:263671541 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Huang et al. (2023) Qian Huang, Jian Vora, Percy Liang, and Jure Leskovec. Mlagentbench: Evaluating language agents on machine learning experimentation. In International Conference on Machine Learning , 2023. URL https://api.semanticscholar.org/CorpusID:263671541 .

### openscholar-0250

**English original**

Ivison et al. (2023) Hamish Ivison, Yizhong Wang, Valentina Pyatkin, Nathan Lambert, Matthew Peters, Pradeep Dasigi, Joel Jang, David Wadden, Noah A Smith, Iz Beltagy, et al. Camels in a changing climate: Enhancing lm adaptation with tulu 2. arXiv preprint arXiv:2311.10702 , 2023. URL https://arxiv.org/abs/2311.10702 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Ivison et al. (2023) Hamish Ivison, Yizhong Wang, Valentina Pyatkin, Nathan Lambert, Matthew Peters, Pradeep Dasigi, Joel Jang, David Wadden, Noah A Smith, Iz Beltagy, et al. Camels in a changing climate: Enhancing lm adaptation with tulu 2. arXiv preprint arXiv:2311.10702 , 2023. URL https://arxiv.org/abs/2311.10702 .

### openscholar-0251

**English original**

Izacard et al. (2022) Gautier Izacard, Mathilde Caron, Lucas Hosseini, Sebastian Riedel, Piotr Bojanowski, Armand Joulin, and Edouard Grave. Unsupervised dense information retrieval with contrastive learning. TMLR , 2022. URL https://openreview.net/forum?id=jKN1pXi7b0 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Izacard et al. (2022) Gautier Izacard, Mathilde Caron, Lucas Hosseini, Sebastian Riedel, Piotr Bojanowski, Armand Joulin, and Edouard Grave. Unsupervised dense information retrieval with contrastive learning. TMLR , 2022. URL https://openreview.net/forum?id=jKN1pXi7b0 .

### openscholar-0252

**English original**

Jiang et al. (2023) Zhengbao Jiang, Frank F Xu, Luyu Gao, Zhiqing Sun, Qian Liu, Jane Dwivedi-Yu, Yiming Yang, Jamie Callan, and Graham Neubig. Active retrieval augmented generation. In ACL , 2023. URL https://aclanthology.org/2023.emnlp-main.495/ .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Jiang et al. (2023) Zhengbao Jiang, Frank F Xu, Luyu Gao, Zhiqing Sun, Qian Liu, Jane Dwivedi-Yu, Yiming Yang, Jamie Callan, and Graham Neubig. Active retrieval augmented generation. In ACL , 2023. URL https://aclanthology.org/2023.emnlp-main.495/ .

### openscholar-0253

**English original**

Jin et al. (2019) Qiao Jin, Bhuwan Dhingra, Zhengping Liu, William Cohen, and Xinghua Lu. PubMedQA: A dataset for biomedical research question answering. In EMNLP-IJCNLP , 2019. URL https://aclanthology.org/D19-1259 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Jin et al. (2019) Qiao Jin, Bhuwan Dhingra, Zhengping Liu, William Cohen, and Xinghua Lu. PubMedQA: A dataset for biomedical research question answering. In EMNLP-IJCNLP , 2019. URL https://aclanthology.org/D19-1259 .

### openscholar-0254

**English original**

Karpukhin et al. (2020) Vladimir Karpukhin, Barlas Oğuz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, and Wen-tau Yih. Dense passage retrieval for open-domain question answering. In EMNLP , 2020. URL https://aclanthology.org/2020.emnlp-main.550/ .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Karpukhin et al. (2020) Vladimir Karpukhin, Barlas Oğuz, Sewon Min, Patrick Lewis, Ledell Wu, Sergey Edunov, Danqi Chen, and Wen-tau Yih. Dense passage retrieval for open-domain question answering. In EMNLP , 2020. URL https://aclanthology.org/2020.emnlp-main.550/ .

### openscholar-0255

**English original**

Kasai et al. (2023) Jungo Kasai, Keisuke Sakaguchi, Yoichi Takahashi, Ronan Le Bras, Akari Asai, Xinyan Yu, Dragomir Radev, Noah A Smith, Yejin Choi, and Kentaro Inui. RealTime QA: What’s the answer right now? In NeurIPS (Datasets and Benchmarks) , 2023. URL https://openreview.net/forum?id=HfKOIPCvsv&noteId=YNFU7iQmxA .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Kasai et al. (2023) Jungo Kasai, Keisuke Sakaguchi, Yoichi Takahashi, Ronan Le Bras, Akari Asai, Xinyan Yu, Dragomir Radev, Noah A Smith, Yejin Choi, and Kentaro Inui. RealTime QA: What’s the answer right now? In NeurIPS (Datasets and Benchmarks) , 2023. URL https://openreview.net/forum?id=HfKOIPCvsv&noteId=YNFU7iQmxA .

### openscholar-0256

**English original**

Kim et al. (2024a) Seungone Kim, Jamin Shin, Yejin Cho, Joel Jang, Shayne Longpre, Hwaran Lee, Sangdoo Yun, Seongjin Shin, Sungdong Kim, James Thorne, and Minjoon Seo. Prometheus: Inducing fine-grained evaluation capability in language models. In ICLR , 2024a. URL https://openreview.net/forum?id=8euJaTveKw .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Kim et al. (2024a) Seungone Kim, Jamin Shin, Yejin Cho, Joel Jang, Shayne Longpre, Hwaran Lee, Sangdoo Yun, Seongjin Shin, Sungdong Kim, James Thorne, and Minjoon Seo. Prometheus: Inducing fine-grained evaluation capability in language models. In ICLR , 2024a. URL https://openreview.net/forum?id=8euJaTveKw .

### openscholar-0257

**English original**

Kim et al. (2024b) Seungone Kim, Juyoung Suk, Ji Yong Cho, Shayne Longpre, Chaeeun Kim, Dongkeun Yoon, Guijin Son, Yejin Cho, Sheikh Shafayat, Jinheon Baek, et al. The biggen bench: A principled benchmark for fine-grained evaluation of language models with language models. arXiv preprint arXiv:2406.05761 , 2024b. URL https://arxiv.org/abs/2406.05761 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Kim et al. (2024b) Seungone Kim, Juyoung Suk, Ji Yong Cho, Shayne Longpre, Chaeeun Kim, Dongkeun Yoon, Guijin Son, Yejin Cho, Sheikh Shafayat, Jinheon Baek, et al. The biggen bench: A principled benchmark for fine-grained evaluation of language models with language models. arXiv preprint arXiv:2406.05761 , 2024b. URL https://arxiv.org/abs/2406.05761 .

### openscholar-0258

**English original**

Kinney et al. (2023) Rodney Michael Kinney, Chloe Anastasiades, Russell Authur, Iz Beltagy, Jonathan Bragg, Alexandra Buraczynski, Isabel Cachola, Stefan Candra, Yoganand Chandrasekhar, Arman Cohan, Miles Crawford, Doug Downey, Jason Dunkelberger, Oren Etzioni, Rob Evans, Sergey Feldman, Joseph Gorney, David W. Graham, F.Q. Hu, Regan Huff, Daniel King, Sebastian Kohlmeier, Bailey Kuehl, Michael Langan, Daniel Lin, Haokun Liu, Kyle Lo, Jaron Lochner, Kelsey MacMillan, Tyler Murray, Christopher Newell, Smita Rao, Shaurya Rohatgi, Paul L Sayre, Zejiang Shen, Amanpreet Singh, Luca Soldaini, Shivashankar Subramanian, A. Tanaka, Alex D Wade, Linda M. Wagner, Lucy Lu Wang, Christopher Wilhelm, Caroline Wu, Jiangjiang Yang, Angele Zamarron, Madeleine van Zuylen, and Daniel S. Weld. The semantic scholar open data platform. ArXiv , abs/2301.10140, 2023. URL https://arxiv.org/abs/2301.10140 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Kinney et al. (2023) Rodney Michael Kinney, Chloe Anastasiades, Russell Authur, Iz Beltagy, Jonathan Bragg, Alexandra Buraczynski, Isabel Cachola, Stefan Candra, Yoganand Chandrasekhar, Arman Cohan, Miles Crawford, Doug Downey, Jason Dunkelberger, Oren Etzioni, Rob Evans, Sergey Feldman, Joseph Gorney, David W. Graham, F.Q. Hu, Regan Huff, Daniel King, Sebastian Kohlmeier, Bailey Kuehl, Michael Langan, Daniel Lin, Haokun Liu, Kyle Lo, Jaron Lochner, Kelsey MacMillan, Tyler Murray, Christopher Newell, Smita Rao, Shaurya Rohatgi, Paul L Sayre, Zejiang Shen, Amanpreet Singh, Luca Soldaini, Shivashankar Subramanian, A. Tanaka, Alex D Wade, Linda M. Wagner, Lucy Lu Wang, Christopher Wilhelm, Caroline Wu, Jiangjiang Yang, Angele Zamarron, Madeleine van Zuylen, and Daniel S. Weld. The semantic scholar open data platform. ArXiv , abs/2301.10140, 2023. URL https://arxiv.org/abs/2301.10140 .

### openscholar-0259

**English original**

Lee et al. (2023) Yoonjoo Lee, Kyungjae Lee, Sunghyun Park, Dasol Hwang, Jaehyeon Kim, Hong-in Lee, and Moontae Lee. QASA: advanced question answering on scientific articles. In ICML , 2023. URL https://proceedings.mlr.press/v202/lee23n.html .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Lee et al. (2023) Yoonjoo Lee, Kyungjae Lee, Sunghyun Park, Dasol Hwang, Jaehyeon Kim, Hong-in Lee, and Moontae Lee. QASA: advanced question answering on scientific articles. In ICML , 2023. URL https://proceedings.mlr.press/v202/lee23n.html .

### openscholar-0260

**English original**

Lewis et al. (2020) Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, and Douwe Kiela. Retrieval-augmented generation for knowledge-intensive nlp tasks. In NeurIPS , 2020. URL https://proceedings.neurips.cc/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Lewis et al. (2020) Patrick Lewis, Ethan Perez, Aleksandra Piktus, Fabio Petroni, Vladimir Karpukhin, Naman Goyal, Heinrich Küttler, Mike Lewis, Wen-tau Yih, Tim Rocktäschel, Sebastian Riedel, and Douwe Kiela. Retrieval-augmented generation for knowledge-intensive nlp tasks. In NeurIPS , 2020. URL https://proceedings.neurips.cc/paper/2020/file/6b493230205f780e1bc26945df7481e5-Paper.pdf .

### openscholar-0261

**English original**

Li et al. (2024a) Junfeng Li, Junjie Gao, Siru Zhang, Yiwen Wang, Xinhang Yan, Hongyan Liu, Shiping Yang, Jie Qiao, and Qian Zhan. BioMistral: A collection of open-source pretrained large language models for biomedicine. In Findings of ACL , 2024a. URL https://aclanthology.org/2024.findings-acl.348/ .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Li et al. (2024a) Junfeng Li, Junjie Gao, Siru Zhang, Yiwen Wang, Xinhang Yan, Hongyan Liu, Shiping Yang, Jie Qiao, and Qian Zhan. BioMistral: A collection of open-source pretrained large language models for biomedicine. In Findings of ACL , 2024a. URL https://aclanthology.org/2024.findings-acl.348/ .

### openscholar-0262

**English original**

Li et al. (2024b) Junyi Li, Jie Chen, Ruiyang Ren, Xiaoxue Cheng, Xin Zhao, Jian-Yun Nie, and Ji-Rong Wen. The dawn after the dark: An empirical study on factuality hallucination in large language models. In Lun-Wei Ku, Andre Martins, and Vivek Srikumar (eds.), Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) , pp. 10879–10899, Bangkok, Thailand, August 2024b. Association for Computational Linguistics. URL https://aclanthology.org/2024.acl-long.586 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Li et al. (2024b) Junyi Li, Jie Chen, Ruiyang Ren, Xiaoxue Cheng, Xin Zhao, Jian-Yun Nie, and Ji-Rong Wen. The dawn after the dark: An empirical study on factuality hallucination in large language models. In Lun-Wei Ku, Andre Martins, and Vivek Srikumar (eds.), Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers) , pp. 10879–10899, Bangkok, Thailand, August 2024b. Association for Computational Linguistics. URL https://aclanthology.org/2024.acl-long.586 .

### openscholar-0263

**English original**

Li et al. (2024c) Ming Li, Yong Zhang, Shwai He, Zhitao Li, Hongyu Zhao, Jianzong Wang, Ning Cheng, and Tianyi Zhou. Superfiltering: Weak-to-strong data filtering for fast instruction-tuning. In ACL , 2024c. URL https://aclanthology.org/2024.acl-long.769 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Li et al. (2024c) Ming Li, Yong Zhang, Shwai He, Zhitao Li, Hongyu Zhao, Jianzong Wang, Ning Cheng, and Tianyi Zhou. Superfiltering: Weak-to-strong data filtering for fast instruction-tuning. In ACL , 2024c. URL https://aclanthology.org/2024.acl-long.769 .

### openscholar-0264

**English original**

Liu et al. (2023) Nelson F Liu, Tianyi Zhang, and Percy Liang. Evaluating verifiability in generative search engines. In Findings of EMNLP , 2023. URL https://aclanthology.org/2023.findings-emnlp.467/ .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Liu et al. (2023) Nelson F Liu, Tianyi Zhang, and Percy Liang. Evaluating verifiability in generative search engines. In Findings of EMNLP , 2023. URL https://aclanthology.org/2023.findings-emnlp.467/ .

### openscholar-0265

**English original**

Liu et al. (2024) Nelson F Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. Lost in the middle: How language models use long contexts. TACL , 2024. URL https://aclanthology.org/2024.tacl-1.9/ .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Liu et al. (2024) Nelson F Liu, Kevin Lin, John Hewitt, Ashwin Paranjape, Michele Bevilacqua, Fabio Petroni, and Percy Liang. Lost in the middle: How language models use long contexts. TACL , 2024. URL https://aclanthology.org/2024.tacl-1.9/ .

### openscholar-0266

**English original**

Lo et al. (2020) Kyle Lo, Lucy Lu Wang, Mark Neumann, Rodney Kinney, and Daniel Weld. S2ORC: The semantic scholar open research corpus. In ACL , 2020. URL https://aclanthology.org/2020.acl-main.447 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Lo et al. (2020) Kyle Lo, Lucy Lu Wang, Mark Neumann, Rodney Kinney, and Daniel Weld. S2ORC: The semantic scholar open research corpus. In ACL , 2020. URL https://aclanthology.org/2020.acl-main.447 .

### openscholar-0267

**English original**

Loshchilov & Hutter (2019) Ilya Loshchilov and Frank Hutter. Decoupled weight decay regularization. In ICLR , 2019. URL https://openreview.net/forum?id=Bkg6RiCqY7 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Loshchilov & Hutter (2019) Ilya Loshchilov and Frank Hutter. Decoupled weight decay regularization. In ICLR , 2019. URL https://openreview.net/forum?id=Bkg6RiCqY7 .

### openscholar-0268

**English original**

Lu et al. (2020) Yao Lu, Yue Dong, and Laurent Charlin. Multi-xscience: A large-scale dataset for extreme multi-document summarization of scientific articles. In EMNLP , 2020. URL https://aclanthology.org/2020.emnlp-main.648/ .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Lu et al. (2020) Yao Lu, Yue Dong, and Laurent Charlin. Multi-xscience: A large-scale dataset for extreme multi-document summarization of scientific articles. In EMNLP , 2020. URL https://aclanthology.org/2020.emnlp-main.648/ .

### openscholar-0269

**English original**

Luo et al. (2022) Renqian Luo, Liai Sun, Yingce Xie, Zhiting Jiang, Yangbin Gu, Kun Shi, Dejia Xiong, Sheng He, Zhen Xu, and Tao Qin. Biogpt: Generative pre-trained transformer for biomedical text generation and mining. Briefings in Bioinformatics , 2022. URL https://academic.oup.com/bib/article/23/6/bbac409/6713511 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Luo et al. (2022) Renqian Luo, Liai Sun, Yingce Xie, Zhiting Jiang, Yangbin Gu, Kun Shi, Dejia Xiong, Sheng He, Zhen Xu, and Tao Qin. Biogpt: Generative pre-trained transformer for biomedical text generation and mining. Briefings in Bioinformatics , 2022. URL https://academic.oup.com/bib/article/23/6/bbac409/6713511 .

### openscholar-0270

**English original**

Madaan et al. (2023) Aman Madaan, Niket Tandon, Prakhar Gupta, Skyler Hallinan, Luyu Gao, Sarah Wiegreffe, Uri Alon, Nouha Dziri, Shrimai Prabhumoye, Yiming Yang, et al. Self-refine: Iterative refinement with self. Feedback , 2023. URL https://arxiv.org/abs/2303.17651 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Madaan et al. (2023) Aman Madaan, Niket Tandon, Prakhar Gupta, Skyler Hallinan, Luyu Gao, Sarah Wiegreffe, Uri Alon, Nouha Dziri, Shrimai Prabhumoye, Yiming Yang, et al. Self-refine: Iterative refinement with self. Feedback , 2023. URL https://arxiv.org/abs/2303.17651 .

### openscholar-0271

**English original**

Malaviya et al. (2023) Chaitanya Malaviya, Subin Lee, Sihao Chen, Elizabeth Sieber, Mark Yatskar, and Dan Roth. Expertqa: Expert-curated questions and attributed answers. arXiv preprint arXiv:2309.07852 , 2023. URL https://arxiv.org/abs/2309.07852 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Malaviya et al. (2023) Chaitanya Malaviya, Subin Lee, Sihao Chen, Elizabeth Sieber, Mark Yatskar, and Dan Roth. Expertqa: Expert-curated questions and attributed answers. arXiv preprint arXiv:2309.07852 , 2023. URL https://arxiv.org/abs/2309.07852 .

### openscholar-0272

**English original**

Mallen et al. (2023) Alex Mallen, Akari Asai, Victor Zhong, Rajarshi Das, Daniel Khashabi, and Hannaneh Hajishirzi. When not to trust language models: Investigating effectiveness of parametric and non-parametric memories. In ACL , 2023. URL https://aclanthology.org/2023.acl-long.546 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Mallen et al. (2023) Alex Mallen, Akari Asai, Victor Zhong, Rajarshi Das, Daniel Khashabi, and Hannaneh Hajishirzi. When not to trust language models: Investigating effectiveness of parametric and non-parametric memories. In ACL , 2023. URL https://aclanthology.org/2023.acl-long.546 .

### openscholar-0273

**English original**

Mishra et al. (2024) Abhika Mishra, Akari Asai, Vidhisha Balachandran, Yizhong Wang, Graham Neubig, Yulia Tsvetkov, and Hannaneh Hajishirzi. Fine-grained hallucination detection and editing for language models. In COLM , 2024. URL https://openreview.net/forum?id=dJMTn3QOWO .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Mishra et al. (2024) Abhika Mishra, Akari Asai, Vidhisha Balachandran, Yizhong Wang, Graham Neubig, Yulia Tsvetkov, and Hannaneh Hajishirzi. Fine-grained hallucination detection and editing for language models. In COLM , 2024. URL https://openreview.net/forum?id=dJMTn3QOWO .

### openscholar-0274

**English original**

Nguyen et al. (2023) Tuan Dung Nguyen, Yuan-Sen Ting, Ioana Ciuca, Charles O’Neill, Ze-Chang Sun, Maja Jabłońska, Sandor Kruk, Ernest Perkowski, Jack Miller, Jason Jason Jingsh Li, Josh Peek, Kartheik Iyer, Tomasz Rozanski, Pranav Khetarpal, Sharaf Zaman, David Brodrick, Sergio J. Rodriguez Mendez, Thang Bui, Alyssa Goodman, Alberto Accomazzi, Jill Naiman, Jesse Cranney, Kevin Schawinski, and Roberta Raileanu. AstroLLaMA: Towards specialized foundation models in astronomy. In Proceedings of the Second Workshop on Information Extraction from Scientific Publications , 2023. URL https://aclanthology.org/2023.wiesp-1.7 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Nguyen et al. (2023) Tuan Dung Nguyen, Yuan-Sen Ting, Ioana Ciuca, Charles O’Neill, Ze-Chang Sun, Maja Jabłońska, Sandor Kruk, Ernest Perkowski, Jack Miller, Jason Jason Jingsh Li, Josh Peek, Kartheik Iyer, Tomasz Rozanski, Pranav Khetarpal, Sharaf Zaman, David Brodrick, Sergio J. Rodriguez Mendez, Thang Bui, Alyssa Goodman, Alberto Accomazzi, Jill Naiman, Jesse Cranney, Kevin Schawinski, and Roberta Raileanu. AstroLLaMA: Towards specialized foundation models in astronomy. In Proceedings of the Second Workshop on Information Extraction from Scientific Publications , 2023. URL https://aclanthology.org/2023.wiesp-1.7 .

### openscholar-0275

**English original**

Nogueira & Cho (2019) Rodrigo Nogueira and Kyunghyun Cho. Passage re-ranking with bert. arXiv preprint arXiv:1901.04085 , 2019. URL https://arxiv.org/abs/1901.04085 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Nogueira & Cho (2019) Rodrigo Nogueira and Kyunghyun Cho. Passage re-ranking with bert. arXiv preprint arXiv:1901.04085 , 2019. URL https://arxiv.org/abs/1901.04085 .

### openscholar-0276

**English original**

Panickssery et al. (2024) Arjun Panickssery, Samuel R. Bowman, and Shi Feng. LLM evaluators recognize and favor their own generations. In NeurIPS , 2024. URL https://openreview.net/forum?id=4NJBV6Wp0h .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Panickssery et al. (2024) Arjun Panickssery, Samuel R. Bowman, and Shi Feng. LLM evaluators recognize and favor their own generations. In NeurIPS , 2024. URL https://openreview.net/forum?id=4NJBV6Wp0h .

### openscholar-0277

**English original**

Phan et al. (2021) Long N Phan, James T Anibal, Hieu Tran, Shaurya Chanana, Erol Bahadroglu, Alec Peltekian, and Grégoire Altan-Bonnet. Scifive: a text-to-text model for biomedical literature. arXiv preprint arXiv:2106.03598 , 2021. URL https://arxiv.org/abs/2106.03598 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Phan et al. (2021) Long N Phan, James T Anibal, Hieu Tran, Shaurya Chanana, Erol Bahadroglu, Alec Peltekian, and Grégoire Altan-Bonnet. Scifive: a text-to-text model for biomedical literature. arXiv preprint arXiv:2106.03598 , 2021. URL https://arxiv.org/abs/2106.03598 .

### openscholar-0278

**English original**

Ram et al. (2023) Ori Ram, Yoav Levine, Itay Dalmedigos, Dor Muhlgay, Amnon Shashua, Kevin Leyton-Brown, and Yoav Shoham. In-context retrieval-augmented language models. TACL , 2023. URL https://aclanthology.org/2023.tacl-1.75/ .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Ram et al. (2023) Ori Ram, Yoav Levine, Itay Dalmedigos, Dor Muhlgay, Amnon Shashua, Kevin Leyton-Brown, and Yoav Shoham. In-context retrieval-augmented language models. TACL , 2023. URL https://aclanthology.org/2023.tacl-1.75/ .

### openscholar-0279

**English original**

Shaikh et al. (2023) Shishir G Shaikh, Jaideep Ramachandran, Varnith Nanda, Benjamin Lunt, Miltiadis Allamanis, Daman Sharma, Sebastien Bubeck, and Prateek Jain. Darwin: Data analytics and reasoning with large language models for science. arXiv preprint arXiv:2308.13565 , 2023. URL https://arxiv.org/abs/2308.13565 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Shaikh et al. (2023) Shishir G Shaikh, Jaideep Ramachandran, Varnith Nanda, Benjamin Lunt, Miltiadis Allamanis, Daman Sharma, Sebastien Bubeck, and Prateek Jain. Darwin: Data analytics and reasoning with large language models for science. arXiv preprint arXiv:2308.13565 , 2023. URL https://arxiv.org/abs/2308.13565 .

### openscholar-0280

**English original**

Shao et al. (2024) Rulin Shao, Jacqueline He, Akari Asai, Weijia Shi, Tim Dettmers, Sewon Min, Luke Zettlemoyer, and Pang Wei Koh. Scaling retrieval-based language models with a trillion-token datastore. In The Thirty-eighth Annual Conference on Neural Information Processing Systems , 2024. URL https://openreview.net/forum?id=iAkhPz7Qt3 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Shao et al. (2024) Rulin Shao, Jacqueline He, Akari Asai, Weijia Shi, Tim Dettmers, Sewon Min, Luke Zettlemoyer, and Pang Wei Koh. Scaling retrieval-based language models with a trillion-token datastore. In The Thirty-eighth Annual Conference on Neural Information Processing Systems , 2024. URL https://openreview.net/forum?id=iAkhPz7Qt3 .

### openscholar-0281

**English original**

Si et al. (2024) Chenglei Si, Diyi Yang, and Tatsunori Hashimoto. Can llms generate novel research ideas? a large-scale human study with 100+ nlp researchers. arXiv preprint arXiv:2409.04109 , 2024. URL https://arxiv.org/abs/2409.04109 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Si et al. (2024) Chenglei Si, Diyi Yang, and Tatsunori Hashimoto. Can llms generate novel research ideas? a large-scale human study with 100+ nlp researchers. arXiv preprint arXiv:2409.04109 , 2024. URL https://arxiv.org/abs/2409.04109 .

### openscholar-0282

**English original**

Singhal et al. (2023a) Karan Singhal, Shekoofeh Azizi, Tao Tu, S Sara Mahdavi, Jason Wei, Hyung Won Chung, Nathan Scales, Ajay Tanwani, Heather Cole-Lewis, Stephen Pfohl, et al. Large language models encode clinical knowledge. Nature , 2023a. URL https://www.nature.com/articles/s41586-023-06291-2 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Singhal et al. (2023a) Karan Singhal, Shekoofeh Azizi, Tao Tu, S Sara Mahdavi, Jason Wei, Hyung Won Chung, Nathan Scales, Ajay Tanwani, Heather Cole-Lewis, Stephen Pfohl, et al. Large language models encode clinical knowledge. Nature , 2023a. URL https://www.nature.com/articles/s41586-023-06291-2 .

### openscholar-0283

**English original**

Singhal et al. (2023b) Zeming Singhal, Charles Sutton, Adam Mottram, Owain Lavelle, Iz Beltagy, Leonardo Neves, Kyle Lo, Stephanie Hyland, Michael Wainwright, Alexander Wettig, et al. MEDITRON-70B: Scaling medical pretraining for large language models. arXiv preprint arXiv:2311.16079 , 2023b. URL https://arxiv.org/abs/2311.16079 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Singhal et al. (2023b) Zeming Singhal, Charles Sutton, Adam Mottram, Owain Lavelle, Iz Beltagy, Leonardo Neves, Kyle Lo, Stephanie Hyland, Michael Wainwright, Alexander Wettig, et al. MEDITRON-70B: Scaling medical pretraining for large language models. arXiv preprint arXiv:2311.16079 , 2023b. URL https://arxiv.org/abs/2311.16079 .

### openscholar-0284

**English original**

Skarlinski et al. (2024) Michael D. Skarlinski, Sam Cox, Jon M. Laurent, James D. Braza, Michaela Hinks, Michael J. Hammerling, Manvitha Ponnapati, Samuel G. Rodriques, and Andrew D. White. Language agents achieve superhuman synthesis of scientific knowledge. preprint , 2024. URL https://paper.wikicrow.ai .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Skarlinski et al. (2024) Michael D. Skarlinski, Sam Cox, Jon M. Laurent, James D. Braza, Michaela Hinks, Michael J. Hammerling, Manvitha Ponnapati, Samuel G. Rodriques, and Andrew D. White. Language agents achieve superhuman synthesis of scientific knowledge. preprint , 2024. URL https://paper.wikicrow.ai .

### openscholar-0285

**English original**

Soldaini et al. (2024) Luca Soldaini, Rodney Kinney, Akshita Bhagia, Dustin Schwenk, David Atkinson, Russell Authur, Ben Bogin, Khyathi Chandu, Jennifer Dumas, Yanai Elazar, et al. Dolma: An open corpus of three trillion tokens for language model pretraining research. In ACL , 2024. URL https://aclanthology.org/2024.acl-long.840/ .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Soldaini et al. (2024) Luca Soldaini, Rodney Kinney, Akshita Bhagia, Dustin Schwenk, David Atkinson, Russell Authur, Ben Bogin, Khyathi Chandu, Jennifer Dumas, Yanai Elazar, et al. Dolma: An open corpus of three trillion tokens for language model pretraining research. In ACL , 2024. URL https://aclanthology.org/2024.acl-long.840/ .

### openscholar-0286

**English original**

Tan et al. (2023) Cheng Tan, Miao Huang, Xianxin Huang, Qian Fu, and Bo Wu. PMC-LLaMA: Further finetuning llama on medical papers. arXiv preprint arXiv:2304.14454 , 2023. URL https://arxiv.org/abs/2304.14454 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Tan et al. (2023) Cheng Tan, Miao Huang, Xianxin Huang, Qian Fu, and Bo Wu. PMC-LLaMA: Further finetuning llama on medical papers. arXiv preprint arXiv:2304.14454 , 2023. URL https://arxiv.org/abs/2304.14454 .

### openscholar-0287

**English original**

Thakur et al. (2021) Nandan Thakur, Nils Reimers, Andreas Rücklé, Abhishek Srivastava, and Iryna Gurevych. BEIR: A heterogeneous benchmark for zero-shot evaluation of information retrieval models. In NeurIPS (Datasets and Benchmarks) , 2021. URL https://openreview.net/forum?id=wCu6T5xFjeJ .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Thakur et al. (2021) Nandan Thakur, Nils Reimers, Andreas Rücklé, Abhishek Srivastava, and Iryna Gurevych. BEIR: A heterogeneous benchmark for zero-shot evaluation of information retrieval models. In NeurIPS (Datasets and Benchmarks) , 2021. URL https://openreview.net/forum?id=wCu6T5xFjeJ .

### openscholar-0288

**English original**

Tian et al. (2024) Minyang Tian, Luyu Gao, Shizhuo Dylan Zhang, Xinan Chen, Cunwei Fan, Xuefei Guo, Roland Haas, Pan Ji, Kittithat Krongchon, Yao Li, et al. Scicode: A research coding benchmark curated by scientists. arXiv preprint arXiv:2407.13168 , 2024. URL https://arxiv.org/abs/2407.13168 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Tian et al. (2024) Minyang Tian, Luyu Gao, Shizhuo Dylan Zhang, Xinan Chen, Cunwei Fan, Xuefei Guo, Roland Haas, Pan Ji, Kittithat Krongchon, Yao Li, et al. Scicode: A research coding benchmark curated by scientists. arXiv preprint arXiv:2407.13168 , 2024. URL https://arxiv.org/abs/2407.13168 .

### openscholar-0289

**English original**

Wadden et al. (2020) David Wadden, Shanchuan Lin, Kyle Lo, Lucy Lu Wang, Madeleine van Zuylen, Arman Cohan, and Hannaneh Hajishirzi. Fact or fiction: Verifying scientific claims. In EMNLP , 2020. URL https://aclanthology.org/2020.emnlp-main.609 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Wadden et al. (2020) David Wadden, Shanchuan Lin, Kyle Lo, Lucy Lu Wang, Madeleine van Zuylen, Arman Cohan, and Hannaneh Hajishirzi. Fact or fiction: Verifying scientific claims. In EMNLP , 2020. URL https://aclanthology.org/2020.emnlp-main.609 .

### openscholar-0290

**English original**

Wadden et al. (2024) David Wadden, Kejian Shi, Jacob Morrison, Aakanksha Naik, Shruti Singh, Nitzan Barzilay, Kyle Lo, Tom Hope, Luca Soldaini, Shannon Zejiang Shen, et al. Sciriff: A resource to enhance language model instruction-following over scientific literature. arXiv preprint arXiv:2406.07835 , 2024. URL https://arxiv.org/abs/2406.07835 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Wadden et al. (2024) David Wadden, Kejian Shi, Jacob Morrison, Aakanksha Naik, Shruti Singh, Nitzan Barzilay, Kyle Lo, Tom Hope, Luca Soldaini, Shannon Zejiang Shen, et al. Sciriff: A resource to enhance language model instruction-following over scientific literature. arXiv preprint arXiv:2406.07835 , 2024. URL https://arxiv.org/abs/2406.07835 .

### openscholar-0291

**English original**

Wang et al. (2024) Yidong Wang, Qi Guo, Wenjin Yao, Hongbo Zhang, Xin Zhang, Zhen Wu, Meishan Zhang, Xinyu Dai, Min zhang, Qingsong Wen, Wei Ye, Shikun Zhang, and Yue Zhang. AutoSurvey: Large language models can automatically write surveys. In NeurIPS , 2024. URL https://openreview.net/forum?id=FExX8pMrdT .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Wang et al. (2024) Yidong Wang, Qi Guo, Wenjin Yao, Hongbo Zhang, Xin Zhang, Zhen Wu, Meishan Zhang, Xinyu Dai, Min zhang, Qingsong Wen, Wei Ye, Shikun Zhang, and Yue Zhang. AutoSurvey: Large language models can automatically write surveys. In NeurIPS , 2024. URL https://openreview.net/forum?id=FExX8pMrdT .

### openscholar-0292

**English original**

Xiao et al. (2023) Shitao Xiao, Zheng Liu, Peitian Zhang, Niklas Muennighoff, Defu Lian, and Jian-Yun Nie. C-pack: Packaged resources to advance general chinese embedding, 2023. URL https://arxiv.org/abs/2309.07597 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Xiao et al. (2023) Shitao Xiao, Zheng Liu, Peitian Zhang, Niklas Muennighoff, Defu Lian, and Jian-Yun Nie. C-pack: Packaged resources to advance general chinese embedding, 2023. URL https://arxiv.org/abs/2309.07597 .

### openscholar-0293

**English original**

Xu et al. (2023a) Fangyuan Xu, Weijia Shi, and Eunsol Choi. RECOMP: Improving retrieval-augmented lms with compression and selective augmentation, 2023a. URL https://arxiv.org/abs/2310.04408 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Xu et al. (2023a) Fangyuan Xu, Weijia Shi, and Eunsol Choi. RECOMP: Improving retrieval-augmented lms with compression and selective augmentation, 2023a. URL https://arxiv.org/abs/2310.04408 .

### openscholar-0294

**English original**

Xu et al. (2023b) Fangyuan Xu, Yixiao Song, Mohit Iyyer, and Eunsol Choi. A critical evaluation of evaluations for long-form question answering. In ACL , 2023b. URL https://aclanthology.org/2023.acl-long.181 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Xu et al. (2023b) Fangyuan Xu, Yixiao Song, Mohit Iyyer, and Eunsol Choi. A critical evaluation of evaluations for long-form question answering. In ACL , 2023b. URL https://aclanthology.org/2023.acl-long.181 .

### openscholar-0295

**English original**

Xu et al. (2024) Fangyuan Xu, Kyle Lo, Luca Soldaini, Bailey Kuehl, Eunsol Choi, and David Wadden. KIWI: A dataset of knowledge-intensive writing instructions for answering research questions. In Findings of ACL , 2024. URL https://aclanthology.org/2024.findings-acl.770 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Xu et al. (2024) Fangyuan Xu, Kyle Lo, Luca Soldaini, Bailey Kuehl, Eunsol Choi, and David Wadden. KIWI: A dataset of knowledge-intensive writing instructions for answering research questions. In Findings of ACL , 2024. URL https://aclanthology.org/2024.findings-acl.770 .

### openscholar-0296

**English original**

Yang et al. (2023) Zonglin Yang, Xinya Du, Junxian Li, Jie Zheng, Soujanya Poria, and E. Cambria. Large language models for automated open-domain scientific hypotheses discovery. In ACL , 2023. URL https://api.semanticscholar.org/CorpusID:261557055 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Yang et al. (2023) Zonglin Yang, Xinya Du, Junxian Li, Jie Zheng, Soujanya Poria, and E. Cambria. Large language models for automated open-domain scientific hypotheses discovery. In ACL , 2023. URL https://api.semanticscholar.org/CorpusID:261557055 .

### openscholar-0297

**English original**

Yuan et al. (2022) Hongyi Yuan, Zheng Yuan, Ruyi Gan, Jiaxing Zhang, Yutao Xie, and Sheng Yu. BioBART: Pretraining and evaluation of a biomedical generative language model. In The 21st Workshop on Biomedical Language Processing (BioNLP) , May 2022. URL https://aclanthology.org/2022.bionlp-1.9 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Yuan et al. (2022) Hongyi Yuan, Zheng Yuan, Ruyi Gan, Jiaxing Zhang, Yutao Xie, and Sheng Yu. BioBART: Pretraining and evaluation of a biomedical generative language model. In The 21st Workshop on Biomedical Language Processing (BioNLP) , May 2022. URL https://aclanthology.org/2022.bionlp-1.9 .

### openscholar-0298

**English original**

Yue et al. (2023) Xiang Yue, Boshi Wang, Ziru Chen, Kai Zhang, Yu Su, and Huan Sun. Automatic evaluation of attribution by large language models. In Findings of EMNLP , 2023. URL https://aclanthology.org/2023.findings-emnlp.307 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Yue et al. (2023) Xiang Yue, Boshi Wang, Ziru Chen, Kai Zhang, Yu Su, and Huan Sun. Automatic evaluation of attribution by large language models. In Findings of EMNLP , 2023. URL https://aclanthology.org/2023.findings-emnlp.307 .

### openscholar-0299

**English original**

Zhang et al. (2024a) Dan Zhang, Ziniu Hu, Sining Zhoubian, Zhengxiao Du, Kaiyu Yang, Zihan Wang, Yisong Yue, Yuxiao Dong, and Jie Tang. Sciinstruct: a self-reflective instruction annotated dataset for training scientific language models. In NeurIPS (Datasets and Benchmarks Track) , 2024a. URL https://openreview.net/forum?id=LC1QAqhePv .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Zhang et al. (2024a) Dan Zhang, Ziniu Hu, Sining Zhoubian, Zhengxiao Du, Kaiyu Yang, Zihan Wang, Yisong Yue, Yuxiao Dong, and Jie Tang. Sciinstruct: a self-reflective instruction annotated dataset for training scientific language models. In NeurIPS (Datasets and Benchmarks Track) , 2024a. URL https://openreview.net/forum?id=LC1QAqhePv .

### openscholar-0300

**English original**

Zhang et al. (2024b) Yuqi Zhang, Zihao Zhao, Lanqing Hu, Shuai Wang, Penghui Jiao, Min Leng, Yuzhi Liu, Guotong Li, Chengming Xu, Chenhui Lin, et al. BioMedGPT: Open multimodal generative pre-trained transformer for biomedicine. Nature Medicine , 2024b. URL https://www.nature.com/articles/s41591-024-03185-2 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Zhang et al. (2024b) Yuqi Zhang, Zihao Zhao, Lanqing Hu, Shuai Wang, Penghui Jiao, Min Leng, Yuzhi Liu, Guotong Li, Chengming Xu, Chenhui Lin, et al. BioMedGPT: Open multimodal generative pre-trained transformer for biomedicine. Nature Medicine , 2024b. URL https://www.nature.com/articles/s41591-024-03185-2 .

### openscholar-0301

**English original**

Zheng et al. (2023a) Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric Xing, Hao Zhang, Joseph E. Gonzalez, and Ion Stoica. Judging LLM-as-a-judge with MT-bench and chatbot arena. In NeurIPS (Datasets and Benchmarks Track) , 2023a. URL https://openreview.net/forum?id=uccHPGDlao .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Zheng et al. (2023a) Lianmin Zheng, Wei-Lin Chiang, Ying Sheng, Siyuan Zhuang, Zhanghao Wu, Yonghao Zhuang, Zi Lin, Zhuohan Li, Dacheng Li, Eric Xing, Hao Zhang, Joseph E. Gonzalez, and Ion Stoica. Judging LLM-as-a-judge with MT-bench and chatbot arena. In NeurIPS (Datasets and Benchmarks Track) , 2023a. URL https://openreview.net/forum?id=uccHPGDlao .

### openscholar-0302

**English original**

Zheng et al. (2024) Yuxiang Zheng, Shichao Sun, Lin Qiu, Dongyu Ru, Cheng Jiayang, Xuefeng Li, Jifan Lin, Binjie Wang, Yun Luo, Renjie Pan, et al. Openresearcher: Unleashing ai for accelerated scientific research. arXiv preprint arXiv:2408.06941 , 2024. URL https://arxiv.org/abs/2408.06941 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Zheng et al. (2024) Yuxiang Zheng, Shichao Sun, Lin Qiu, Dongyu Ru, Cheng Jiayang, Xuefeng Li, Jifan Lin, Binjie Wang, Yun Luo, Renjie Pan, et al. Openresearcher: Unleashing ai for accelerated scientific research. arXiv preprint arXiv:2408.06941 , 2024. URL https://arxiv.org/abs/2408.06941 .

### openscholar-0303

**English original**

Zheng et al. (2023b) Zhiling Zheng, Zichao Rong, Nakul Rampal, Christian Borgs, Jennifer T Chayes, and Omar M Yaghi. A gpt-4 reticular chemist for guiding mof discovery. Angewandte Chemie International Edition , 2023b. URL https://arxiv.org/abs/2306.14915 .

**原文保留（专名、技术内容或文献信息） · 保留原文**

Zheng et al. (2023b) Zhiling Zheng, Zichao Rong, Nakul Rampal, Christian Borgs, Jennifer T Chayes, and Omar M Yaghi. A gpt-4 reticular chemist for guiding mof discovery. Angewandte Chemie International Edition , 2023b. URL https://arxiv.org/abs/2306.14915 .

### openscholar-0304

**English original**

Appendix

**中文译文 · 机器初译**

附录

### openscholar-0305

**English original**

Appendix A Released Artifacts

**中文译文 · 机器初译**

附录 A 已发布的成果

### openscholar-0306

**English original**

We release a set of artifacts to facilitate future research:

**中文译文 · 机器初译**

我们发布了一组成果以推动后续研究：

### openscholar-0307

**English original**

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

**中文译文 · 机器初译**

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

### openscholar-0308

**English original**

Appendix B More Details on ScholarQABench

**中文译文 · 机器初译**

附录 B：关于 ScholarQABench的更多细节

### openscholar-0309

**English original**

B.1 Goal of ScholarQABench

**中文译文 · 机器初译**

B.1 ScholarQABench的目标

### openscholar-0310

**English original**

There are two key principles to ScholarQABench : it should serve as a realistic benchmark for literature review, and as a reproducible, mutifaceted evaluation pipeline.

**中文译文 · 机器初译**

ScholarQABench 有两个关键原则：它应作为文献综述的现实性基准，同时也是一个可复现且多维度的评估流程。

### openscholar-0311

**English original**

Realistic benchmark for literature review (Section 3.1 ).

**中文译文 · 机器初译**

大语言模型文献综述的现实性基准（第3.1节）。

### openscholar-0312

**English original**

ScholarQABench integrates tasks from two key sources: (i) curated and adapted existing datasets related to literature synthesis tasks and annotated by scientists, and (ii) four new datasets, annotated by Ph.D. experts from four scientific domains that reflect realistic literature review scenarios, such as information synthesis from multiple papers.
The tasks in ScholarQABench require different output formats and disciplines.

**中文译文 · 机器初译**

ScholarQABench整合了来自两个关键来源的任务：(i) 经过筛选和改编的现有数据集，这些数据集与文献综合任务相关且由科学家标注；以及 (ii) 四个新的数据集，这些数据集由四个科学领域的博士专家标注，反映了真实的文献综述场景，例如来自多篇论文的信息整合。ScholarQABench中的任务需要不同的输出格式和学科领域。

### openscholar-0313

**English original**

For multi-paper tasks, we instruct our expert annotators to formulate information-seeking questions—questions they are genuinely interested in finding answers to, rather than questions they already know the answers to or that could be answered using small text chunks from a single paper ( Asai & Choi, 2021 ; Choi et al., 2018 ) .
We found this approach crucial for curating realistic questions that real-world scientists might ask. These questions are typically more detailed, contextualized (e.g., “I am planning to generate synthetic training data using GPT4o and filter noisy data using GPT4o, but I’m concerned that GPT4o is not filtering models in this case, as it may favor its own generation.”), and require nuanced, long-form answers rather than simple yes/no or multiple-choice responses.
We collected human-written answers or rubrics to ensure reliable evaluation, rather than relying on answers generated by state-of-the-art proprietary LMs, as done in Xu et al. (2024) ; Malaviya et al. (2023) . While these proprietary models are powerful, they still exhibit limitations, such as hallucinations from lacking domain knowledge, biases, and rapid information changes, making them unsuitable for consistent evaluation with newer models. Additionally, using model-generated answers as references can unfairly favor models from the same family, introducing possible evaluation biases Panickssery et al. (2024) . To avoid these issues, we curated expert-written answers for ScholarQA-CS and ScholarQA-Multi .

**中文译文 · 机器初译**

对于多篇论文任务，我们要求专家注释者提出信息寻求问题——即那些他们真正希望得到解答的问题，而非已经知道答案或可以通过单篇论文中的小文本片段得到解答的问题（Asai & Choi, 2021；Choi et al., 2018）。我们发现这种方法对于筛选出现实科学家可能提出的真实问题至关重要。
这些问题通常更为详细且具有情境性（例如：“我计划使用 GPT4o 生成合成训练数据，并使用 GPT4o 过滤噪声数据，但我担心在这种情况下 GPT4o 不会过滤模型，因为它可能会倾向于自身生成的内容”），需要细致、长篇的回答，而非简单的是/否或选择题形式的回应。我们收集了人类撰写的答案或评分标准，以确保评估的可靠性，而不是像 Xu et al. (2024) 和 Malaviya et al. (2023) 那样依赖最先进的专有 LLM 生成的答案。
虽然这些专有模型功能强大，但仍然存在一些局限性，例如缺乏领域知识导致的幻觉、偏见以及信息快速变化等问题，因此无法与新型模型进行一致的评估。此外，以模型生成的答案作为参考可能会不公平地偏向同一系列的模型，从而引入潜在的评估偏差（Panickssery等，2024）。为避免这些问题，我们为 ScholarQA-CS 和 ScholarQA-Multi 筛选了由专家撰写的答案。

### openscholar-0314

**English original**

Reproducible multi-face evaluation pipelines (Section 3.2 ).

**中文译文 · 机器初译**

可复现的多面评估流程（第3.2节）。

### openscholar-0315

**English original**

Due to low correlation between conventional similarity-based metrics such as ROUGE ( Xu et al., 2023b ; Malaviya et al., 2023 ) and human judgments, evaluations of long-form generation tasks in expert domains have typically relied on small- to medium-scale expert annotations ( Zheng et al., 2024 ; Singhal et al., 2023a ; Si et al., 2024 ) . While expert human evaluation is valuable (as we detail in Section 5 ), it requires significant costs for hiring annotators and is hard to reproduce.
To address these limitations, we introduce automated evaluation pipelines that comprehensively assess the quality of long-form generation outputs from important aspects such as citation correctness or coverage.

**中文译文 · 机器初译**

由于 ROUGE 等传统基于相似度的评估指标与人类判断之间的相关性较低（Xu 等，2023b；Malaviya 等，2023），专家领域长文本生成任务的评估通常依赖于小规模至中规模的专家标注数据（Zheng 等，2024；Singhal 等，2023a；Si 等，2024）。尽管专家人工评估具有价值（如第5节所述），但雇佣标注人员需要高昂成本，且难以重复实施。
为了克服这些限制，我们引入了自动化评估流程，从引用准确性或覆盖度等关键方面全面评估长文本生成结果的质量。

### openscholar-0316

**English original**

B.2 Data Curation Details

**中文译文 · 机器初译**

B.2 数据整理细节

### openscholar-0317

**English original**

B.2.1 Details of Modification of Single-paper Tasks

**中文译文 · 机器初译**

B.2.1 单篇论文任务修改的详细内容

### openscholar-0318

**English original**

SciFact.

**中文译文 · 机器初译**

SciFact。

### openscholar-0319

**English original**

SciFact ( Wadden et al., 2020 ) is a dataset of 1.4K expert-written scientific claims in the biomedical domain, paired with evidence-based abstracts annotated with labels and rationales. The original task involves three subtasks—paragraph selection, sentence selection, and label prediction—based on a collection of 5,000 abstracts. However, we reformulate this as an open-retrieval label prediction task, where the model is given only a query and must predict the label from a larger corpus of 40 million passages.
We exclude queries labeled as not enough information and retain only instances labeled as either supports (true) or contradicts (false).

**中文译文 · 机器初译**

SciFact（Wadden等，2020）是一个包含1.4K个由专家撰写的生物医学领域科学论断的数据集，这些论断均配有带有标签和解释的基于证据的摘要。原始任务包含三个子任务——段落选择、句子选择和标签预测——这些任务基于5,000篇摘要的集合进行设计。然而，我们将其重新设计为开放检索标签预测任务，模型中仅接收查询信息，必须从4000万条文本中预测出相应的标签。我们排除了被标记为“信息不足”的查询，仅保留被标记为“支持”（正确）或“矛盾”（错误）的实例。

### openscholar-0320

**English original**

PubMedQA.

**中文译文 · 机器初译**

PubMedQA。

### openscholar-0321

**English original**

We leverage PubMedQA ( Jin et al., 2019 ) , which has 1k expert-annotated (yes/no/maybe) QA data on PubMed paper abstracts.
Similarly to SciFact , we keep instances with yes or no labels, and discard the original abstract passage to formulate the task as an open setup.

**中文译文 · 机器初译**

我们利用了 PubMedQA（Jin等人，2019年）数据集，该数据集包含1000条由专家标注的“是/否/可能”类型的PubMed论文摘要问答数据。与SciFact类似，我们保留了带有“是”或“否”标签的实例，并丢弃原始摘要段落，从而将任务设定为一种开放式设置。

### openscholar-0322

**English original**

QASA.

**中文译文 · 机器初译**

QASA。

### openscholar-0323

**English original**

QASA ( Lee et al., 2023 ) is a single paper QA dataset consisting of 1,798
novel question answering pairs that require reasoning over scientific articles in AI and ML. We evaluate the model’s ability to sufficiently answer a detailed question about the target paper. While they provide three subtasks (answer selection, rational generation and answer compositions) and the end-to-end full-stack QA, we evaluate the models’ performance based on full-stack QA.

**中文译文 · 机器初译**

QASA（Lee等人，2023年）是一个单一的文献综述QA数据集，包含1,798对新的问题回答对，这些问题需要针对AI和ML领域的科学文章进行推理。我们评估模型能否充分回答关于目标文献的详细问题。虽然该数据集包含三个子任务（答案选择、理性生成和答案组合）以及端到端的全栈QA形式，但我们仍基于全栈QA来评估模型的性能。

### openscholar-0324

**English original**

B.2.2 Details of Data Collections of Multi-paper Tasks

**中文译文 · 机器初译**

B.2.2 多篇论文任务的数据收集细节

### openscholar-0325

**English original**

Recruiting annotators.

**中文译文 · 机器初译**

招募注释员。

### openscholar-0326

**English original**

For data curation, we recruit expert annotators through UpWork and inter-institution channels, ensuring that they meet the following criteria: (1) they hold a Ph.D. or are enrolled in a relevant Ph.D. program, (2) they have over three years of research experience in the field, and (3) they have published papers in the target areas. In total, we recruited over 20 annotators, including Ph.D. students, postdoctoral fellows, professors, and research scientists, across various multi-paper subsets in the target domains.

**中文译文 · 机器初译**

在数据整理方面，我们通过 UpWork 及跨机构渠道招募专业标注员，确保他们符合以下标准：(1) 拥有博士学位或正在攻读相关博士学位；(2) 在该领域拥有超过三年的研究经验；(3) 在目标领域发表过相关论文。总计我们招募了超过 20 名标注员，包括博士生、博士后研究员、教授及研究科学家，涵盖目标领域多个论文类别。

### openscholar-0327

**English original**

Annotation instructions.

**中文译文 · 机器初译**

注释说明。

### openscholar-0328

**English original**

Table 5 outlines our annotations instructions to collect rubrics for ScholarQA-CS , and
Table 6 shows annotation instructions given to the annotators for ScholarQA-Bio and ScholarQA-Neuro .
Table 7 shows the instructions given to annotators for ScholarQA-Multi .

**中文译文 · 机器初译**

表5列出了我们用于收集 ScholarQA-CS评分标准的标注说明；表6则展示了针对 ScholarQA-Bio和ScholarQA-Neuro的标注员所需的标注指南。表7则给出了针对 ScholarQA-Multi的标注员指示。

### openscholar-0329

**English original**

Instructions

**中文译文 · 机器初译**

说明

### openscholar-0330

**English original**

This project is aimed at building a dataset that can be used to evaluate how well large language models can answer scientific questions. Specifically, for a set of complex scientific questions that require multiple documents to answer, you’re asked to provide the points that are important to include in an answer, along with supporting text from the scientific literature and other sources. We will release your output to the community in the form of a dataset that allows researchers to assess how well AI systems can answer complex scientific questions.

**中文译文 · 机器初译**

该项目旨在构建一个数据集，用于评估大语言模型回答科学问题时的表现。具体而言，针对那些需要多份文档才能解答的复杂科学问题，要求您提供在回答中必须包含的关键点，以及来自科学文献和其他来源的支持性文本。我们将以数据集的形式向社区发布您的成果，以便研究人员能够评估人工智能系统回答复杂科学问题的能力。

### openscholar-0331

**English original**

For each question, you are given two documents -

**中文译文 · 机器初译**

对于每个问题，您都会得到两份文档——

### openscholar-0332

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0333

**English original**

A key ingredients document that you will fill-in with components that you feel are necessary to include in a correct answer to the question.
Key ingredients are short (1-4 sentences) statements of an important item to include in a correct answer, such as “near the beginning, the answer should should briefly define state space models and transformers and detail their technical differences.”

**中文译文 · 机器初译**

一份关键要素文档要求你填写那些你认为对于给出正确答案而言必要的内容。关键要素是简短（1-4句）的陈述，用于说明正确答案中需要包含的重要事项，例如：“在开头部分，应简要介绍状态空间模型和Transformer，并详细说明它们的技术差异。”

### openscholar-0334

**English original**

•

**原文保留（专名、技术内容或文献信息） · 保留原文**

•

### openscholar-0335

**English original**

(do not read right away) A sources document that you will use for reference, giving the output for the question from different online services

**中文译文 · 机器初译**

（不要立即阅读）一份作为参考的源文件，其中包含了来自不同在线服务的相关答案

### openscholar-0336

**English original**

Perform the following steps:

**中文译文 · 机器初译**

执行以下步骤：

### openscholar-0337

**English original**

1.

**原文保留（专名、技术内容或文献信息） · 保留原文**

1.

### openscholar-0338

**English original**

First, BEFORE reading the existing text in the sources document, based on your knowledge of the question and about 40 minutes of literature review using Google Scholar or Semantic Scholar (but NOT any online large language model services like ChatGPT or similar), compose a set of key ingredients of the answer and supporting quotes from the documents. Starting from the corresponding key ingredients file for the question, add your key ingredient to the list along with zero or more snippets of text from the documents under “supporting quotes.” Each snippet should be less than 150 words. After each quote, paste a link from the source (if you quote a document multiple times, paste a link after each quote). Your key ingredients should typically have supporting snippets, but may not always if you wish to include an important fact that you know but cannot find support for.

**中文译文 · 机器初译**

首先，在阅读来源文档中的现有内容之前，根据你对问题的了解以及大约40分钟的文献综述时间（使用Google Scholar或Semantic Scholar，但不得使用ChatGPT等在线大语言模型服务），先整理出答案的关键要素以及来自文档的支撑引文。从与问题相关的关键要素文件中开始，将你的关键要素加入列表中，并附上“支撑引文”部分中零个或更多段文字片段。每段文字片段的长度应少于150字。
在每一条引文之后，粘贴来自原材料的链接（如果您多次引用同一文档，则每条引文后都粘贴一个链接）。您的核心内容通常应包含支持性片段，但如果需要包含某个已知但无法找到支持依据的重要事实，则不一定必须包含这些片段。

### openscholar-0339

**English original**

2.

**原文保留（专名、技术内容或文献信息） · 保留原文**

2.

### openscholar-0340

**English original**

Then, in a total of about 20-50 additional minutes, read through the sources document for the question (you may have to skim over portions, as some source documents are long), and complete the set of key ingredients in the answer based on the combination of what you’d listed in step 1, and what you learn from the sources. You should delete or change ingredients you added after step one, if appropriate.

**中文译文 · 机器初译**

然后，在大约 20-50 分钟的时间里，阅读与问题相关的资料文档（可能需要快速浏览部分内容，因为有些文档篇幅较长），根据第一步中列出的内容以及从资料中获得的信息，完成答案中的关键要素组合。如果合适的话，应删除或修改第一步之后添加的要素。

### openscholar-0341

**English original**

Note: you can copy and paste text directly from the sources document as Supporting Quotes, and for those quotes you do NOT need to include a link, just paste the relevant portion in quotation marks.

**中文译文 · 机器初译**

注意：您可以直接从源文件复制并粘贴文本作为支持引用，对于这些引用无需提供链接，只需将相关部分用引号括起来即可。

### openscholar-0342

**English original**

In your key ingredients, you do not need to cover general stylistic points (e.g., that the answer should be well-organized and include citations), those characteristics are already captured in a general rubric we’ve written. Instead, focus on the specific content needed in the answer, organized as bullet points. When capturing the ingredients, follow the template of the document to separate them into

**中文译文 · 机器初译**

在关键要素部分，无需涉及一般性的风格要点（例如，答案应结构清晰并包含引用），这些特征已包含在我们制定的通用评分标准中。相反，应重点关注答案中所需的具体内容，并以项目符号形式进行组织。在列出这些要素时，需遵循文档的模板，将其区分开来

### openscholar-0343

**English original**

Most important

**中文译文 · 机器初译**

最重要的

### openscholar-0344

**English original**

and

**中文译文 · 机器初译**

并且

### openscholar-0345

**English original**

nice-to-have

**中文译文 · 机器初译**

实用的附加功能

### openscholar-0346

**English original**

. The “most important” items should be ones that, if they were missing, would lead the answer to be misleading or incomplete. The “nice to have” should include other helpful elements, but ones that could potentially be omitted in a short answer.

**中文译文 · 机器初译**

. “最重要的”项目应当是那些如果缺失会导致答案具有误导性或不完整的内容；“额外的有益元素”则应包含其他有助于说明的内容，但这类内容在简短的回答中可能可以省略。

### openscholar-0347

**English original**

To help you understand the task, an example of a completed ingredients file, and the corresponding sources file is provided.

**中文译文 · 机器初译**

为了帮助您理解任务，这里提供了一份完成的成分文件示例以及对应的来源文件。

### openscholar-0348

**English original**

Table 5: ScholarQA-CS annotation instructions : Instructions given to our expert annotators for producing key ingredients for ScholarQA-CS questions.

**中文译文 · 机器初译**

表5：ScholarQA-CS注释说明：提供给专家注释者的指导方针，用于生成ScholarQA-CS问题的关键要素。

### openscholar-0349

**English original**

Instructions

**中文译文 · 机器初译**

说明

### openscholar-0350

**English original**

In this task, you are asked to generate complex scientific questions that biomedical scholars might reasonably ask about scientific literature. These should be broad literature review questions that require multiple papers to answer, e.g.: “What are the various molecular mechanisms through which chronic inflammation contributes to the development of colon cancer?” This question requires multiple papers to answer, as there are a variety of different studies on such molecular mechanisms. By contrast, an example of a question we are NOT looking for would be “What was the efficacy of Pembrolizumab in reducing tumor size in patients with advanced melanoma based on the S1801 clinical trial?”, since a single paper (the results of the clinical trial) holds the answer.

**中文译文 · 机器初译**

在这项任务中，你需要生成一些复杂的科学问题，这些问题可能是生物医学学者针对相关科学文献可能提出的。这些问题应属于广泛的文献综述类问题，需要结合多篇论文才能解答，例如：“慢性炎症通过哪些不同的分子机制导致结肠癌的发生？”这个问题需要结合多篇论文来回答，因为关于这些分子机制的研究有很多不同的研究。
相比之下，我们并不希望看到的提问示例是：“根据 S1801 临床试验的结果，帕博利珠单抗在缩小晚期黑色素瘤患者的肿瘤大小方面的效果如何？”，因为答案仅存在于一篇文献中（即该临床试验的结果）。

### openscholar-0351

**English original**

To help ensure we obtain a wide variety of questions, we’d like you to use existing papers as inspiration for your questions. You can think of it as trying to guess what kinds of literature review questions the authors of the paper may have had while they were performing the research in the paper. Specifically, follow the following steps:

**中文译文 · 机器初译**

为了确保获得多样化的问题，我们希望您能够以现有文献为灵感来提出问题。您可以将其视为尝试推测该论文作者在开展研究时可能遇到的何种类型的文献综述问题。具体而言，请遵循以下步骤：

### openscholar-0352

**English original**

1. Pick a paper of interest in your domain. This can be any paper, but review or survey articles can be an especially useful source of inspiration as they cover broad topics encompassing many previous papers. Also, previous work or future work sections of papers can be good sources.

**中文译文 · 机器初译**

1. 选择您所在领域中感兴趣的文献。任何文献都可以，但综述或文献综述类文章尤其能提供灵感，因为它们涵盖了包含许多先前论文的广泛主题。此外，论文中的先前研究或未来研究方向部分也是良好的参考来源。

### openscholar-0353

**English original**

2. Write up to 5-10 literature review questions that are relevant to the paper. These should be:
(a) Questions that generally require multiple documents to answer; (b) Questions about the published literature—the kinds of questions that a scientist could attempt to answer by searching and reading papers (i.e., they don’t necessarily require new experiments)

**中文译文 · 机器初译**

2. 提出最多5-10个与论文相关的文献综述问题。这些问题应属于：(a) 需要查阅多份文献才能解答的问题；(b) 关于已发表文献的问题——即科学家通过搜索和阅读论文可以尝试解答的问题类型（也就是说，这些问题不一定需要新的实验）

### openscholar-0354

**English original**

We have provided a Google Sheet with three columns, “question,” “inspiring paper,” and “estimated number of papers needed to answer (1/10/100/1000+),” for you to list each of your questions and roughly how many papers you think a person would need to examine in order to answer it accurately.

**中文译文 · 机器初译**

我们提供了一个包含三列的 Google 表格：“问题”、“启发性论文”以及“为解答该问题所需的论文数量估计值（1/10/100/1000+）”，供您列出每个问题，并大致说明为了准确解答这些问题，一个人需要查阅多少篇论文。

### openscholar-0355

**English original**

While it is important to choose papers on topics you are familiar with, please also strive to choose a diverse set of papers on a variety of subtopics, and do not write more than 10 questions about any single paper. Paste each of your questions and the Semantic Scholar link for the inspiring paper in the spreadsheet (in the unlikely event that the link cannot be found, please paste the bibliographic information for the paper in APA format).

**中文译文 · 机器初译**

虽然选择自己熟悉的主题的论文很重要，但也应努力选取不同子主题的多样化论文，且任何一篇论文的提问数量不得超过10个。请将每个问题以及该启发性论文的 Semantic Scholar 链接粘贴到电子表格中（如果无法找到链接，请以 APA 格式提供该论文的参考文献信息）。

### openscholar-0356

**English original**

As a concrete example, consider this paper:

**中文译文 · 机器初译**

作为一个具体示例，请参考这篇论文：

### openscholar-0357

**English original**

You do not need to make any attempt to determine the answers to your questions, or even try to verify whether such answers exist. It is okay if some of your questions turn out to be unanswerable (for example, for Q1 above, it might be the case that there are no known biomarkers; or for Q2, perhaps no such studies exist). We want you to choose the most realistic literature review questions you can, and sometimes realistic questions will not have answers in the current literature.

**中文译文 · 机器初译**

您无需尝试确定问题的答案，甚至不必试图验证这些答案是否存在。部分问题无法得到解答也是正常的（例如，对于上述第1个问题，可能不存在已知的生物标志物；对于第2个问题，也可能没有相关的研究）。我们希望您选择尽可能具有现实性的文献综述问题，有时现实性的问题在现有文献中确实没有答案。

### openscholar-0358

**English original**

Table 6: ScholarQA-Bio , Neuro annotation instructions :Instructions given to our expert annotators for authoring questions in biomedicine. The example questions in this passage were composed with assistance from GPT.

**中文译文 · 机器初译**

表6：ScholarQA-Bio，神经科学注释说明：我们向专家注释者提供的用于撰写生物医学问题的指导方针。本文中的示例问题是在GPT的协助下编写的。

### openscholar-0359

**English original**

Instructions

**中文译文 · 机器初译**

说明

### openscholar-0360

**English original**

You will be given a question and your task is to annotate your answers with appropriate citations. You are allowed to use tools like Google Search, Google Scholar, or Semantic Scholar to find sources. However, you may not use any language model-powered systems such as ChatGPT, GPT-4, Claude, Perplexity, or you.com.

**中文译文 · 机器初译**

你将得到一个问题，任务是在回答中标注相应的参考文献。你可以使用 Google 搜索、Google Scholar 或 Semantic Scholar等工具来查找资料。但是，你不得使用 ChatGPT、GPT-4、Claude、Perplexity 或 you.com 等由语言模型驱动的系统。

### openscholar-0361

**English original**

Steps to Follow:

**中文译文 · 机器初译**

遵循步骤：

### openscholar-0362

**English original**

1. Start the Stopwatch: Before you begin reading the question, start a stopwatch to track how long it takes you to complete the task.

**中文译文 · 机器初译**

1. 启动秒表：在开始阅读题目之前，先启动秒表来记录完成该任务所需的时间。

### openscholar-0363

**English original**

2. Answer the Question: After reading the question, write your answer. Ensure that every sentence that requires a citation is followed by a citation number (e.g., [1]).

**中文译文 · 机器初译**

2. 回答问题：阅读完问题后写出答案。确保每句需要引用内容后都标注相应的引用编号（例如 [1]）。

### openscholar-0364

**English original**

3. Track Time: Once you have finished writing your answer, stop the stopwatch and note the exact duration it took to complete the task.

**中文译文 · 机器初译**

3. 记录时间：完成答案撰写后，停止秒表并记录完成该任务的确切耗时。

### openscholar-0365

**English original**

Answer Format:

**中文译文 · 机器初译**

回答格式：

### openscholar-0366

**English original**

Output

**中文译文 · 机器初译**

输出

### openscholar-0367

**English original**

: Write your answer under

**中文译文 · 机器初译**

：在下方填写你的答案

### openscholar-0368

**English original**

Output

**中文译文 · 机器初译**

输出

### openscholar-0369

**English original**

. Ensure that all citation-worthy sentences include at least one citation, indicated as [citation number] (e.g., [1]).

**中文译文 · 机器初译**

确保所有具有引用价值的句子至少包含一条引用，并以 [引用编号] 的形式标注（例如 [1]）。

### openscholar-0370

**English original**

Citations

**中文译文 · 机器初译**

引用

### openscholar-0371

**English original**

: For each citation you use (denoted as [i] in your answer), you need to fill out the following information:

**中文译文 · 机器初译**

：对于您使用的每一条引用（在您的答案中标记为[i]），您需要填写以下信息：

### openscholar-0372

**English original**

citation_i_title

**中文译文 · 机器初译**

引用_标题

### openscholar-0373

**English original**

:
Provide the title of the paper.

**中文译文 · 机器初译**

：请提供该文献的标题。

### openscholar-0374

**English original**

citation_i_corpus_id

**中文译文 · 机器初译**

引用_i_语料库编号

### openscholar-0375

**English original**

: Semantic Scholar Corpus ID for the citation.

**中文译文 · 机器初译**

：用于引文的 Semantic Scholar 语料库编号。

### openscholar-0376

**English original**

citation_i_text

**中文译文 · 机器初译**

引用文本

### openscholar-0377

**English original**

: Copy the relevant paragraph from the paper that supports your answer. In this context, a “paragraph” refers to a set of sentences separated by a new line in the paper. Below, we show an example of paragraphs. If there’s no new line and one paragraph gets really long e.g., over 0.5 pages, then please copy and paste the core sentences including the useful information.

**中文译文 · 机器初译**

：请复制支持您答案的论文中的相关段落。在此语境下，“段落”指的是论文中由换行符分隔的一组句子。下面展示一些段落示例。如果段落没有换行符且非常长（例如超过0.5页），则请复制并粘贴包含有用信息的核心句子。

### openscholar-0378

**English original**

citation_i_url

**中文译文 · 机器初译**

引用_i_url

### openscholar-0379

**English original**

: Provide the URL link to the paper (e.g., arXiv abstract page, Semantic Scholar page, PubMed abstract page, etc.).

**中文译文 · 机器初译**

：请提供该文献的网址链接（例如 arXiv 摘要页面、Semantic Scholar 页面、PubMed 摘要页面等）。

### openscholar-0380

**English original**

Table 7: ScholarQAMulti annotation instructions : Instructions given to our expert annotators to annotate question and answers.

**中文译文 · 机器初译**

表7：ScholarQAMulti注释说明：提供给专家注释者的注释问题和答案的标注指南。

### openscholar-0381

**English original**

Statistics of human-written questions and answers in ScholarQA-Multi .

**中文译文 · 机器初译**

ScholarQA-Multi 中人工撰写的问答统计情况

### openscholar-0382

**English original**

Figure 6(a) shows the subject distribution, and Figure 6(b) depicts the average time in seconds that experts spend on annotating each answer across different subjects.
Annotators on average spend at least 30 minutes per answer, but those from some subjects, such as Physics, took over an hour (e.g., approximately 5,000 seconds) to complete a single annotation. This demonstrates that the task is highly time-consuming and challenging even for domain experts.

**中文译文 · 机器初译**

图6(a)展示了各主题的分布情况，图6(b)则显示了专家在标注不同主题的答案时平均花费的时间（以秒为单位）。平均而言，标注者每标注一个答案至少需要30分钟，而某些主题如物理学的标注者则需要超过1小时（约5,000秒）才能完成一次标注。这表明即使对于领域专家来说，这项任务也极其耗时且具有挑战性。

### openscholar-0383

**English original**

(a) Subject distributions of expert-annotated answers

**中文译文 · 机器初译**

(a) 专家标注答案的主题分布

### openscholar-0384

**English original**

(b) Average per-instance annotation time for each subject (seconds).

**中文译文 · 机器初译**

(b) 每个受试者的平均实例标注时间（秒）。

### openscholar-0385

**English original**

Figure 6: Analysis of human-written answers: (a) shows the distribution of instances per subject, and (b) shows the average annotation time per instance per subject.

**中文译文 · 机器初译**

图6：人类撰写的答案分析：(a) 展示了各主题下的实例分布，以及(b) 展示了每个主题的每个实例平均标注时间。

### openscholar-0386

**English original**

B.3 Evaluation Metrics Details

**中文译文 · 机器初译**

B.3 评估指标详情

### openscholar-0387

**English original**

B.3.1 ScholarQA-CS Corr Evaluation

**中文译文 · 机器初译**

B.3.1 ScholarQA-CS 校正评估

### openscholar-0388

**English original**

For ScholarQA-CS , we employ expert-annotated rubrics to evaluate the generated answers.
Each rubric has two criteria—general (accounting for 40% of the score) and annotation-driven (60%).
The general criterion covers the evaluation of length, expertise, citations, and excerpts, while the annotation criterion involves assessing the extent to which each specific key ingredient (and associated quotes) identified by annotators is present in the answer, on a scale of 0 to 1.
Each must-have ingredient is considered twice as important as a nice-to-have. However, there is no distinction between individual ingredients of the same type.
Using LLM-as-a-judge ( Zheng et al., 2023a ) , a score is assigned for each criterion, and a weighted sum is computed across the criterion to obtain a final score. This score emphasizes the presence of citations and excerpts, such that systems lacking either tend to underperform even when they score relatively high on the remaining criteria, as seen in our experiments.

**中文译文 · 机器初译**

对于 ScholarQA-CS 项目，我们采用专家标注的评分标准来评估生成的答案。每个评分标准包含两个维度——通用指标（占得分的 40%）和标注驱动指标（占 60%）。通用指标涵盖长度、专业水平、引用次数及摘录内容方面的评估，而标注驱动指标则通过 0 到 1 的评分体系，衡量标注者所识别的每个具体关键要素及其相关引文在答案中的出现程度。每个必须包含的要素被认为比可选要素重要两倍，但同一类型的不同要素之间则没有区分。
采用大语言模型作为评判者（Zheng等，2023a），针对每个标准进行评分，然后按权重计算各标准的总和以得出最终得分。该评分机制强调引文和摘录的完整性，因此，如我们的实验所示，缺乏其中任一要素的系统即便在其余标准上得分较高，也往往表现不佳。

### openscholar-0389

**English original**

Aspect | Definition | Instructions
Organization | Evaluate if the output is well-organized and logically structured. | Table 10
Coverage | Evaluate if the output provides sufficient coverage and amount of information. | Table 11
Relevance | Evaluate if the response stay on topic and maintain a clear focus to provide a useful response to the question | Table 12
Overall Usefulness | Evaluate if the output contains useful information to fulfill the information needs. | Table 13

**中文译文 · 机器初译**

Aspect | Definition | Instructions
Organization | Evaluate if the output is well-organized and logically structured. | Table 10
Coverage | Evaluate if the output provides sufficient coverage and amount of information. | Table 11
Relevance | Evaluate if the response stay on topic and maintain a clear focus to provide a useful response to the question | Table 12
Overall Usefulness | Evaluate if the output contains useful information to fulfill the information needs. | Table 13

表内文字对照（数值与原始行列保持不变）：
Aspect → 方面
Definition → 定义
Instructions → 说明
Organization → 组织
Evaluate if the output is well-organized and logically structured → 评估输出内容是否条理清晰且逻辑严密
Table → 表格
Coverage → 覆盖范围
Evaluate if the output provides sufficient coverage and amount of information → 评估输出内容是否具备足够的覆盖范围和信息量
Relevance → 相关性
Evaluate if the response stay on topic and maintain a clear focus to provide a useful response to the question → 评估该回复是否紧扣主题且保持清晰重点，以便对问题提供有用的解答
Overall Usefulness → 整体实用性
Evaluate if the output contains useful information to fulfill the information needs → 评估输出内容是否包含有助于满足信息需求的有用信息

### openscholar-0390

**English original**

Table 8: Evaluation protocols for writing quality . We define three fine-grained aspects to be evaluated by both human experts and LLMs. In addition to these, experts are also asked to assess whether the answers are useful.

**中文译文 · 机器初译**

表8：写作质量评估方案。我们定义了三个由人类专家和大语言模型共同评估的细致维度。除此之外，专家还需判断这些回答是否有用。

### openscholar-0391

**English original**

B.3.2 Content Quality and Organization

**中文译文 · 机器初译**

B.3.2 内容质量与结构安排

### openscholar-0392

**English original**

An overview of the evaluation aspects is in Table 8 .
We use Relevance, Coverage and Organization for automatic evaluation. We found that existing evaluator LMs struggle with evaluating overall usefulness, and tend to be over-optimistic.

**中文译文 · 机器初译**

评估方面的概述见表8。我们采用相关性、覆盖率和组织性这三个指标进行自动评估。我们发现现有的评估智能体大语言模型在评估整体实用性方面存在困难，且往往过于乐观。

### openscholar-0393

**English original**

Evaluation instructions and rubrics.

**中文译文 · 机器初译**

评估说明与评分标准。

### openscholar-0394

**English original**

We show annotator rubrics for organization, coverage, relevance and overall usefulness in Tables 10 , 11 , 12 , and 13 , respectively.

**中文译文 · 机器初译**

我们在表10、表11、表12和表13中分别展示了标注者的评分标准，这些标准涉及组织性、覆盖范围、相关性以及整体实用性。

### openscholar-0395

**English original**

Prometheus configuration.

**中文译文 · 机器初译**

Prometheus 配置。

### openscholar-0396

**English original**

For evaluations, we combine Prometheus BGB ( Kim et al., 2024b ) ( prometheus-eval/prometheus-bgb-8x7b-v2.0 ) and Prometheus v2 ( Kim et al., 2024a ) ( https://huggingface.co/prometheus-eval/prometheus-8x7b-v2.0 ).
We found that Prometheus BGB generally works well, while on Rel it sometimes gives scores that are much higher than human assessments, especially for GPT4o. Consequently, we use Prometheus BGB for Org and Cov , and Prometheus v2 for relevance.
We use human-written answers as gold references, which are shown to improve Prometheus’ correlation with human evaluation. We use these models with vllm .
Following the default setup, we set the maximum number of new tokens to 512, top- $p$ to 0.95, and temperature to 0.01.

**中文译文 · 机器初译**

在评估方面，我们结合了 Prometheus BGB（Kim等人，2024b）（prometheus-eval/prometheus-bgb-8x7b-v2.0）和 Prometheus v2（Kim等人，2024a）（https://huggingface.co/prometheus-eval/prometheus-8x7b-v2.0）。我们发现 Prometheus BGB 通常表现良好，但在 Rel 任务上有时会给出远高于人类评估的得分，尤其是针对 GPT4o。因此，我们将 Prometheus BGB 用于 Org 和 Cov 任务，将 Prometheus v2 用于相关性任务。我们使用人工撰写的答案作为金标准参考，这能提升 Prometheus 与人类评估的关联度。我们将这些模型与 vllm 结合使用。
按照默认设置，我们将新令牌的最大数量设定为 512，top- $p$ 为 0.95，温度设定为 0.01。

### openscholar-0397

**English original**

B.3.3 Citation Accuracy

**中文译文 · 机器初译**

B.3.3 引用准确性

### openscholar-0398

**English original**

To evaluate citation accuracy, we use osunlp/attrscore-flan-t5-xl ( Yue et al., 2023 ) , which is FLAN-T5-XL trained on a mixture of attribution tasks. We follow citation precision and recall formulation from Gao et al. (2023) and compute citation precision and recall at the sentence level. We discard sentences under 50 characters, as these sentences are often paragraph or subsection headers that do not require citations.
We use the original citation evaluation instructions from Yue et al. (2023) , as shown in Table 9 .

**中文译文 · 机器初译**

为了评估引用准确性，我们使用了 osunlp/attrscore-flan-t5-xl（Yue等，2023），该模型是在多种归因任务上训练的 FLAN-T5-XL。我们遵循 Gao等（2023）提出的引用精确率和召回率计算方法，并在句子层面计算引用精确率和召回率。我们将字符数少于50的句子排除在外，因为这些句子通常是不需要引用的段落或子标题。我们采用 Yue等（2023）提供的原始引用评估指南，如表9所示。

### openscholar-0399

**English original**

As an Attribution Validator, your task is to verify whether a given reference can support the given claim. A claim can be either a plain sentence or a question followed by its answer. Specifically, your response should clearly indicate the relationship: Attributable, Contradictory or Extrapolatory. A contradictory error occurs when you can infer that the answer contradicts the fact presented in the context, while an extrapolatory error means that you cannot infer the correctness of the answer based on the information provided in the context.

**中文译文 · 机器初译**

作为归因验证器，您的任务是判断给定的参考文献是否能够支持该主张。该主张可以是简单的句子，也可以是带有答案的问题。具体而言，您的回复应明确说明关系类型：可归因、矛盾或推断性错误。当您能推断出答案与上下文中的事实相矛盾时，即属于矛盾错误；而推断性错误则意味着您无法根据上下文提供的信息来判断答案的正确性。

### openscholar-0400

**English original**

Claim:

**中文译文 · 机器初译**

主张：

### openscholar-0401

**English original**

Reference:

**中文译文 · 机器初译**

参考文献：

### openscholar-0402

**English original**

Table 9: Evaluation instruction for citation evaluation. We prompt an attribution LM if the claim is supported by the provided reference or not. The instruction is adapted from Yue et al. (2023) .

**中文译文 · 机器初译**

表9：引文评估的评估指令。如果某项主张有提供的参考文献作为支持，我们就会向大语言模型发出引用提示。该指令改编自Yue等人（2023）的研究。

### openscholar-0403

**English original**

Appendix C More Details on OpenScholar

**中文译文 · 机器初译**

附录 C 关于 OpenScholar 的更多细节

### openscholar-0404

**English original**

C.1 Training a scientific bi-encoder $\theta_{\rm bi}$

**中文译文 · 机器初译**

C.1 训练科学型生物编码器  $\theta_{\rm bi}$

### openscholar-0405

**English original**

For $\theta_{\text{bi}}$ , we follow the unsupervised training methodology from Izacard et al. (2022) , and continually pre-train the Contriever bi-encoder on a mixture of peS2o version 2, CCNews, and Proofpile2 ( Azerbayev et al., 2024 ) data for 500k steps, using a batch size of 4,096 and a learning rate of 0.00005. We initialize the model checkpoint from Contriever.

**中文译文 · 机器初译**

对于 $\theta_{\text{bi}}$ ，我们采用 Izacard 等人在 2022 年提出的无监督训练方法，在 peS2o 版本 2、CCNews 和 Proofpile2（Azerbayev 等，2024）数据的混合数据集上，以 4,096 的批量大小和 0.00005 的学习率，对 Contriever 双编码器进行持续预训练，共进行 500k 步。我们从 Contriever 中初始化模型检查点。

### openscholar-0406

**English original**

C.2 Training a scientific cross-encoder $\theta_{\rm cross}$

**中文译文 · 机器初译**

C.2 训练科学交叉编码器  $\theta_{\rm cross}$

### openscholar-0407

**English original**

Paragraphs that score above 3 are labeled as positive, while those that score below 3 are labeled negative. Finally, we select the top $N$ passages based on this process, passing the top paragraphs $\mathbf{P}$ to the generator LM.
For $\theta_{\text{cross}}$ , we fine-tune the BGE-large reranker for 5 epochs on our newly created training data for five epochs, using a learning rate of 6e-5.

**中文译文 · 机器初译**

得分超过3分的段落被标记为正面，而得分低于3分的段落则被标记为负面。最后，根据这一流程选出前$N$段落，并将这些高分段落$\mathbf{P}$提交给生成器LLM。对于$\theta_{\text{cross}}$部分，我们在新创建的训练数据上使用6e-5的学习率进行5个周期의 BGE-large重排序器微调。

### openscholar-0408

**English original**

C.3 Training Details of Generators $\mathcal{G}$

**中文译文 · 机器初译**

C.3 生成器训练细节  $\mathcal{G}$

### openscholar-0409

**English original**

Training data statistics.

**中文译文 · 机器初译**

训练数据统计信息。

### openscholar-0410

**English original**

Figure 7 shows the training data distribution. “Tulu” indicates general-domain instruction-tuning data from Ivison et al. (2023) and SciRIFF ( Wadden et al., 2024 ) indicates task-specific data from SciRIFF. For both datasets, we ensure that we do not include any data used for evaluation, namely PubMedQA, SciFact and QASA. In total, this leads to 130,135 training instances.

**中文译文 · 机器初译**

图7展示了训练数据分布。“Tulu”表示来自Ivison等人（2023年）的通用领域指令调整数据，而SciRIFF（Wadden等人，2024年）中的数据则代表来自SciRIFF的任务特定数据。对于这两个数据集，我们都确保不包含任何用于评估的数据，即PubMedQA、SciFact和QASA的数据。总计共有130,135个训练样本。

### openscholar-0411

**English original**

Figure 7: Generator training data distribution. We mix diverse training data to train our 8B LM.

**中文译文 · 机器初译**

图7：生成器训练数据分布。我们混合了多种不同的训练数据来训练我们的8B大语言模型。

### openscholar-0412

**English original**

Training hyperparameters.

**中文译文 · 机器初译**

训练超参数。

### openscholar-0413

**English original**

For OS-8B, we initialize model checkpoints from Llama 3.1 8B Instruct ( Dubey et al., 2024 ) . We use torchtune 7 7 7 https://github.com/pytorch/torchtune for training.

**中文译文 · 机器初译**

对于 OS-8B 模型，我们以 Llama 3.1 8B Instruct（Dubey 等，2024）的模型检查点作为初始值。我们使用 torchtune 7 7 7  https://github.com/pytorch/torchtune 进行训练。

### openscholar-0414

**English original**

We train both models for two epochs using learning rates of 5e-6 and 1e-4, respectively, with a maximum context length of 10k and batch size of 1 and gradient accumulation step of 2 with bf16.
We use AdamW ( Loshchilov & Hutter, 2019 ) as an optimizer.

**中文译文 · 机器初译**

我们分别使用 5e-6 和 1e-4 的学习率对这两个模型进行两个轮次的训练，最大上下文长度为 10k，批量大小为 1，梯度累积步长为 2，并使用 bf16 算子。我们采用 AdamW（Loshchilov & Hutter, 2019）作为优化器。

### openscholar-0415

**English original**

Instructions

**中文译文 · 机器初译**

说明

### openscholar-0416

**English original**

Evaluate if the answer is well-organized and logically structured. An acceptable response should: 1. be clearly structured, grouping related points together for a logical flow., and 2. be coherent, without any contradictions or unnecessary repetition.

**中文译文 · 机器初译**

评估答案是否结构清晰且逻辑合理。一个合格的回答应：1. 结构明确，将相关要点归为一组以形成合理的逻辑流程；2. 连贯一致，不存在矛盾或不必要的重复。

### openscholar-0417

**English original**

Score 1: Poor Organization

**中文译文 · 机器初译**

分数1：组织混乱

### openscholar-0418

**English original**

- The response is disorganized, with no clear structure.

**中文译文 · 机器初译**

- 回复内容缺乏条理，没有清晰的结构。

### openscholar-0419

**English original**

- Points are scattered without any logical order, making it difficult to follow.

**中文译文 · 机器初译**

- 各点分散排列，没有逻辑顺序，难以理解。

### openscholar-0420

**English original**

- The text lacks coherence, and there are contradictions or irrelevant repetitions throughout.

**中文译文 · 机器初译**

- 文本缺乏连贯性，且存在矛盾或无关的重复内容。

### openscholar-0421

**English original**

Score 2: Basic Organization

**中文译文 · 机器初译**

得分2：基础组织结构

### openscholar-0422

**English original**

- The response has some organization, but the structure is inconsistent.
- There are occasional lapses in coherence, with minor contradictions or repetitive statements that disrupt the overall clarity.

**中文译文 · 机器初译**

- 回复内容有一定的条理，但结构不够统一。 - 偶尔会出现连贯性不足的情况，存在轻微的矛盾或重复表述，从而破坏了整体清晰度。

### openscholar-0423

**English original**

Score 3: Moderate Organization

**中文译文 · 机器初译**

得分3：组织程度中等

### openscholar-0424

**English original**

- The response is generally well-organized, with a clear structure that is mostly maintained.
- Points are grouped logically, though there may be some minor lapses in flow or coherence. The answers have several clear paragraphs, each of which clearly discuss some core points.
- The text is mostly clear, with only occasional repetition or slight contradictions.

**中文译文 · 机器初译**

- 回复内容整体组织有序，结构清晰且基本保持完整。  
- 各要点按逻辑分组，尽管可能存在一些流程或连贯性上的小问题。回答包含多个清晰的段落，每个段落都明确讨论了某些核心观点。  
- 文本整体较为清晰，仅偶尔出现重复或轻微矛盾。

### openscholar-0425

**English original**

Score 4: Strong Organization

**中文译文 · 机器初译**

得分 4：组织严谨

### openscholar-0426

**English original**

- The response is well-organized, with a clear and logical structure that is followed consistently.
- Points are effectively grouped, and the flow is smooth.
- There may be minor lapses in coherence, but overall, the response is clear and easy to follow, with minimal repetition or contradictions.

**中文译文 · 机器初译**

- 回复结构清晰有序，遵循了一致且合理的逻辑框架。  
- 各要点分组合理，行文流畅自然。  
- 可能存在一些连贯性的小问题，但总体而言，回复内容明确易读，重复或矛盾之处极少。

### openscholar-0427

**English original**

Score 5: Exceptional Organization

**中文译文 · 机器初译**

得分 5：出色的组织性

### openscholar-0428

**English original**

- The response is exceptionally well-organized, with a flawless logical structure.
- Points are grouped perfectly, and the flow between them is seamless.
- The text is coherent throughout, with no contradictions or unnecessary repetition, making the argument clear and compelling.

**中文译文 · 机器初译**

- 该回应组织得非常有序，逻辑结构也完美无缺。  
- 各要点分类清晰，它们之间的衔接也非常流畅。  
- 全文连贯一致，没有矛盾或不必要的重复，使得论证清晰且具有说服力。

### openscholar-0429

**English original**

Table 10: Evaluation rubrics for organization. The evaluation instructions and five-point rubric for assessing organization.

**中文译文 · 机器初译**

表10：组织的评估评分标准。评估说明及用于评估组织的五点评分标准。

### openscholar-0430

**English original**

Instructions

**中文译文 · 机器初译**

说明

### openscholar-0431

**English original**

Evaluate if the output provides sufficient coverage and amount of information. The output should: 1. (coverage) Offer a comprehensive review of the area of interest, citing a diverse range of representative papers and discussing a variety of sources, not just a few (1-2 papers) 2. (depth) Provide enough relevant information to understand each discussion point.

**中文译文 · 机器初译**

评估输出内容是否具备足够的覆盖范围和信息量。输出应：1. （覆盖范围）对感兴趣领域进行全面综述，引用多种代表性文献并讨论多种来源，而不仅仅只有几篇（1-2篇）文献；2. （深度）提供足够的相关信息以理解每个讨论点。

### openscholar-0432

**English original**

Score 1:

**中文译文 · 机器初译**

分数 1：

### openscholar-0433

**English original**

-

**原文保留（专名、技术内容或文献信息） · 保留原文**

-

### openscholar-0434

**English original**

Severely Lacking Coverage

**中文译文 · 机器初译**

覆盖范围严重不足

### openscholar-0435

**English original**

: The output lacks coverage of several core lines of research or focuses predominantly on a single line of work, missing a holistic view of the area.
-

**中文译文 · 机器初译**

：该成果未能涵盖若干核心研究方向，或主要聚焦于单一研究领域，缺乏对该领域的整体认识。

### openscholar-0436

**English original**

Greatly Limited Depth of Information

**中文译文 · 机器初译**

信息深度极为有限

### openscholar-0437

**English original**

: The output either lacks essential details needed to fully understand the topic (e.g., definitions of methods, relationships between methods).

**中文译文 · 机器初译**

：输出结果缺乏理解该主题所需的基本信息（例如，方法的定义以及各方法之间的关联）。

### openscholar-0438

**English original**

Score 2:

**中文译文 · 机器初译**

分数 2：

### openscholar-0439

**English original**

-

**原文保留（专名、技术内容或文献信息） · 保留原文**

-

### openscholar-0440

**English original**

Partial Coverage

**中文译文 · 机器初译**

部分覆盖

### openscholar-0441

**English original**

: The output covers some key aspects of the area but misses significant lines of research or focuses too narrowly on a few sources. It lacks a well-rounded view and fails to adequately represent the diversity of work in the field.

**中文译文 · 机器初译**

：该成果涵盖了该领域的一些关键方面，但遗漏了重要的研究方向，また对少数来源的研究关注过于狭窄。它缺乏全面的观点，未能充分体现该领域的研究多样性。

### openscholar-0442

**English original**

-

**原文保留（专名、技术内容或文献信息） · 保留原文**

-

### openscholar-0443

**English original**

Limited Amount of Information

**中文译文 · 机器初译**

信息量有限

### openscholar-0444

**English original**

: The response provides some relevant information but leaves out important details that would help in understanding the topic fully.

**中文译文 · 机器初译**

：该回应提供了一些相关信息，但遗漏了有助于全面理解该主题的重要细节。

### openscholar-0445

**English original**

Score 3:

**中文译文 · 机器初译**

得分 3：

### openscholar-0446

**English original**

-

**原文保留（专名、技术内容或文献信息） · 保留原文**

-

### openscholar-0447

**English original**

Acceptable Coverage / Overview

**中文译文 · 机器初译**

可接受的覆盖度 / 概述

### openscholar-0448

**English original**

: The output discusses several representative works and provides a satisfactory overview of the area. However, including more papers or discussion points could enhance the answer significantly. It addresses the core aspects of the question but may miss some details.

**中文译文 · 机器初译**

：该输出讨论了几篇具有代表性的研究，并对该领域提供了令人满意的概述。然而，如果包含更多论文或讨论点，就能显著提升回答质量。虽然该内容涵盖了问题的核心方面，但可能遗漏了一些细节。

### openscholar-0449

**English original**

-

**原文保留（专名、技术内容或文献信息） · 保留原文**

-

### openscholar-0450

**English original**

Acceptable Amount of Relevant Information

**中文译文 · 机器初译**

可接受的相关信息量

### openscholar-0451

**English original**

: The output provides a reasonable amount of relevant information, though it may lack some helpful details.

**中文译文 · 机器初译**

：该输出提供了相当多的相关信息，尽管可能缺乏一些有用的细节。

### openscholar-0452

**English original**

Score 4:

**中文译文 · 机器初译**

得分 4：

### openscholar-0453

**English original**

-

**原文保留（专名、技术内容或文献信息） · 保留原文**

-

### openscholar-0454

**English original**

Good Coverage

**中文译文 · 机器初译**

良好的覆盖度

### openscholar-0455

**English original**

: The output offers good coverage of the area, discussing a variety of representative papers and sources. While it provides a broad overview, it may miss a few minor areas or additional papers that could enhance the comprehensiveness.

**中文译文 · 机器初译**

：该成果对相关领域进行了全面的覆盖，讨论了多种具有代表性的论文与资料。虽然它提供了广泛的概述，但可能遗漏了一些较小的领域或能够提升整体全面性的额外论文。

### openscholar-0456

**English original**

-

**原文保留（专名、技术内容或文献信息） · 保留原文**

-

### openscholar-0457

**English original**

Mostly Sufficient Amount of Information

**中文译文 · 机器初译**

大部分足够的信息量

### openscholar-0458

**English original**

: The response includes most of the necessary and relevant information to understand the topic. It avoids excessive irrelevant details, but a few points might benefit from deeper exploration or more specific examples.

**中文译文 · 机器初译**

: 该回应包含了理解该主题所需的大部分必要且相关的信息。它避免了过多的无关细节，但部分内容或许需要更深入的探讨或更具体的例子来完善。

### openscholar-0459

**English original**

Score 5:

**中文译文 · 机器初译**

得分 5：

### openscholar-0460

**English original**

-

**原文保留（专名、技术内容或文献信息） · 保留原文**

-

### openscholar-0461

**English original**

Comprehensive Coverage

**中文译文 · 机器初译**

全面覆盖

### openscholar-0462

**English original**

: The answer covers a diverse range of papers and viewpoints, offering a thorough overview of the area. It includes additional important discussion points not explicitly mentioned in the original question.

**中文译文 · 机器初译**

：该回答涵盖了多种不同的论文和观点，对这一领域进行了全面的概述。其中还包含了原问题未明确提及的其他重要讨论点。

### openscholar-0463

**English original**

-

**原文保留（专名、技术内容或文献信息） · 保留原文**

-

### openscholar-0464

**English original**

Necessary and Sufficient Amount of Information

**中文译文 · 机器初译**

必要且充分的信息量

### openscholar-0465

**English original**

: The response provides all necessary and sufficient information.

**中文译文 · 机器初译**

：该回应提供了所有必要且充分的信息。

### openscholar-0466

**English original**

Table 11: Evaluation rubrics for coverage. The evaluation instructions and five-point rubric for assessing coverage.

**中文译文 · 机器初译**

表11：覆盖度评估评分标准。评估说明及用于评估覆盖度的五分制评分标准。

### openscholar-0467

**English original**

Instructions

**中文译文 · 机器初译**

说明

### openscholar-0468

**English original**

Evaluate if the response stays on topic and maintain a clear focus to provide a useful response to the question. Specifically, the output should: 1. fully address the core points of the original question and satisfy your information needs if they are factual 2. not contain a lot of minor information that is not related to the original question.

**中文译文 · 机器初译**

评估回复是否紧扣主题并保持清晰重点，以对问题提供有用的解答。具体而言，输出内容应：1. 充分涵盖原问题的核心要点，并满足其事实性信息需求；2. 不包含大量与原问题无关的琐碎信息。

### openscholar-0469

**English original**

Score 1: Off-topic

**中文译文 · 机器初译**

分数 1：与主题无关

### openscholar-0470

**English original**

- The content significantly deviates from the original question, making it difficult to discern its relevance or distract the user.

**中文译文 · 机器初译**

- 内容与原始问题存在显著偏差，难以判断其相关性，还会分散用户的注意力。

### openscholar-0471

**English original**

Score 2: Frequently off-topic with limited focus

**中文译文 · 机器初译**

得分2：经常偏离主题，关注点有限

### openscholar-0472

**English original**

- The response addresses the question to some extent but often strays off-topic.
- There are several sections with irrelevant information or tangential points that do not contribute to answering the main question.
- These distractions make it difficult to maintain a clear focus and reduce the overall usefulness of the response.

**中文译文 · 机器初译**

- 该回复在某种程度上回应了问题，但经常偏离主题。- 有几个部分包含无关信息或旁枝末节的内容，无法帮助解答核心问题。- 这些干扰因素使得难以保持清晰的焦点，也降低了回复的整体实用性。

### openscholar-0473

**English original**

Score: 3: Somewhat on topic but with several digressions or irrelevant information

**中文译文 · 机器初译**

得分：3分：内容 somewhat 相关，但存在多处离题或无关信息

### openscholar-0474

**English original**

- While the response still centers around the original question, there are frequent deviations that distract from the main question or redundant information.

**中文译文 · 机器初译**

- 尽管回复仍然围绕原始问题展开，但频繁出现的偏离内容会分散对核心问题的注意力，或包含冗余信息。

### openscholar-0475

**English original**

Score 4: Mostly on-topic with minor deviations

**中文译文 · 机器初译**

得分 4：大部分内容与主题相关，存在少量偏差

### openscholar-0476

**English original**

- The response stays largely on-topic, with a clear focus on addressing the question. However, there may be a few minor digressions or slightly irrelevant details that momentarily detract from the main focus.
- These deviations are infrequent and do not significantly undermine the overall clarity or usefulness of the response.
.

**中文译文 · 机器初译**

- 回复内容主要围绕主题，明确针对了问题展开讨论。不过，可能会有一些轻微的偏离或不太相关的细节，暂时影响了核心重点的呈现。- 这些偏差并不常见，也不会显著影响回复的整体清晰度和实用性。

### openscholar-0477

**English original**

Score 5: Focused and entirely on topic

**中文译文 · 机器初译**

得分 5：专注且完全围绕主题展开

### openscholar-0478

**English original**

- The response remains tightly centered on the subject matter with enough depth and coverage of the core information, with every piece of information contributing directly to a comprehensive understanding of the topic.

**中文译文 · 机器初译**

- 该回应紧密围绕主题展开，对核心信息进行了充分的深度和覆盖，每一条信息都直接有助于对主题的全面理解。

### openscholar-0479

**English original**

Table 12: Evaluation rubrics for relevance. The evaluation instructions and five-point rubric for assessing relevance.

**中文译文 · 机器初译**

表12：相关性评估评分标准。评估说明及用于评估相关性的五分制评分标准。

### openscholar-0480

**English original**

Instructions

**中文译文 · 机器初译**

说明

### openscholar-0481

**English original**

Do you think the provided answers are overall helpful and assist your literature review? In particular:

**中文译文 · 机器初译**

您认为所给出的答案整体是否有帮助，能够辅助您的文献综述工作？特别是：

### openscholar-0482

**English original**

Score 1: Unhelpful

**中文译文 · 机器初译**

分数 1：无帮助

### openscholar-0483

**English original**

- The response does not answer the question or provide rather confusing information.
- It does not serve as a useful starting point for learning or writing about the area or understanding the literature.

**中文译文 · 机器初译**

- 该回应未能回答问题或提供相当混乱的信息。 - 它无法作为学习或撰写相关内容、理解相关文献的实用起点。

### openscholar-0484

**English original**

Score 2: Better than searching by myself from scratch but limited utility

**中文译文 · 机器初译**

得分2：比我自己从头搜索要好，但实用性有限

### openscholar-0485

**English original**

- The response provides at least one helpful paper that I can take a closer look at.
- However, overall the discussion in the answer is somewhat irrelevant and does not provide helpful information.

**中文译文 · 机器初译**

- 该回复提供了至少一篇我可以进一步研究的有用文献。 - 然而，整体来看回答中的讨论有些无关紧要，并未提供有用的信息。

### openscholar-0486

**English original**

Score 3: Provides some useful discussions and papers, although I need to read individual papers by myself

**中文译文 · 机器初译**

得分3：提供了一些有价值的讨论和论文，不过我需要自己阅读这些论文

### openscholar-0487

**English original**

- The response is generally helpful and provides at least 2-3 helpful papers that I wasn’t aware of. I can start looking at some of the suggested papers.
- It provides some good overview of the areas and multiple viewpoints, which I can dive into.
- Yet, I may need to verify some details or consult additional core research papers to ensure completeness.

**中文译文 · 机器初译**

- 该回复非常有帮助，还提供了至少2-3篇我之前不知道的优质文献。我可以开始查看那些建议的论文了。  
- 它对相关领域及多种观点进行了很好的概述，我可以进一步深入研究。  
- 不过，我可能需要核实一些细节或查阅更多核心研究论文，以确保内容的完整性。

### openscholar-0488

**English original**

Score 4: Useful. I may try to verify some details, but overall the output gives me a great summary of the area of my interest.

**中文译文 · 机器初译**

得分 4：很有用。我可能会尝试验证一些细节，但总体而言，该输出为我所关注的领域提供了很好的总结。

### openscholar-0489

**English original**

- The answer gives me a great set of papers highly related to my question.
- The answer provides a great overview and detailed information.
- I may need to check some minor details from 1-2 specific papers included in the answers, but overall the provided answer is useful with little need of additional editing.

**中文译文 · 机器初译**

- 这个回答提供了大量与我的问题高度相关的论文。  
- 该回答给出了很好的概述和详细信息。  
- 我可能需要检查答案中包含的1-2篇特定论文中的一些细节问题，但总体而言，所提供的答案非常有用，几乎不需要额外编辑。

### openscholar-0490

**English original**

Score 5: Super Useful. I can fully trust the answer

**中文译文 · 机器初译**

得分 5：非常有用。我可以完全信任该答案

### openscholar-0491

**English original**

- The response provides a comprehensive overview of the area, and sufficiently answers my question.
- I don’t think I need to search additional papers or check details by myself.

**中文译文 · 机器初译**

- 该回复对这一领域提供了全面的概述，并充分回答了我的问题。 - 我认为不需要再搜索其他文献或自行核实细节。

### openscholar-0492

**English original**

Table 13: Evaluation rubrics for overall helpfulness. The evaluation instructions and five-point rubric for assessing overall usefulness.

**中文译文 · 机器初译**

表13：整体有用性的评估评分标准。评估说明及用于衡量整体实用性的五点评分标准。

### openscholar-0493

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0494

**English original**

Figure 8: Human evaluation annotation interface.

**中文译文 · 机器初译**

图8：人类评估注释界面。

### openscholar-0495

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0496

**English original**

Figure 9: Human evaluation annotation interface.

**中文译文 · 机器初译**

图9：人类评估注释界面。

### openscholar-0497

**English original**

Appendix D More Analysis

**中文译文 · 机器初译**

附录 D 更多分析

### openscholar-0498

**English original**

D.1 Comparison of peS2o v2 and v3

**中文译文 · 机器初译**

D.1 peS2o v2与v3的对比

### openscholar-0499

**English original**

Figure 10: Distributions of the paper publication years of top 20 retrieved papers for ScholarQA-CS . This figure shows that by updating the datastore from peS2o v2 to the more recent peS2o v3, which includes papers up till October 2024, our dense retrieval model can successfully retrieve more recent papers.

**中文译文 · 机器初译**

图10：ScholarQA-CS中检索到的前20篇论文的发表年份分布。该图表明，通过将数据存储从peS2o v2更新为更新的peS2o v3（包含截至2024年10月的论文），我们的密集检索模型能够成功检索到更多近期的论文。

### openscholar-0500

**English original**

In this section, we conduct a brief analysis on datastores used in OpenScholar .
Figure 10 shows the distributions of top 20 retrieved papers from the two datastores, peS2o v2 and v3 for the same ScholarQA-CS queries. Note that our retrieval models are trained on peS2o v2 data. Although our model is not directly trained on the new version 3 datastore, we found that it can constantly retrieve relevant papers from the newer datastore at test time, resulting in many papers from 2023 - 2024.

**中文译文 · 机器初译**

在本节中，我们对 OpenScholar 中使用的数据存储进行了简要分析。图 10 展示了针对相同的 ScholarQA-CS 查询，从 peS2o v2 和 v3 两个数据存储中检索到的前 20 篇文献的分布情况。需要注意的是，我们的检索模型是在 peS2o v2 数据上训练的。虽然我们的模型并未直接在新的 v3 数据存储上训练，但我们发现它在测试时能够持续从较新的数据存储中检索到相关文献，因此获得了大量来自 2023 - 2024 年的文献。

### openscholar-0501

**English original**

D.2 More analysis on Expert Evaluation

**中文译文 · 机器初译**

D.2 关于专家评估的进一步分析

### openscholar-0502

**English original**

Automatic evaluations of human and model-generated answers.

**中文译文 · 机器初译**

对人类和模型生成的答案进行自动评估。

### openscholar-0503

**English original**

| Length | Inf. time (min) | # of Citations | Prec. | Rec. | Org. | Cov. | Rel.
Human | 289.5 | 56.8 | 6.0 | 44.4 | 41.5 | – | – | –
OS -GPT4o | 716.3 | 1.5 | 9.8 | 38.0 | 37.1 | 4.63 | 4.50 | 4.23
OS -8B | 578.6 | 0.9 | 21.6 | 42.5 | 43.2 | 3.92 | 4.44 | 4.02
GPT4o | 281.3 | 0.5 | 3.8 | 0.8 | 0.6 | 4.06 | 3.94 | 4.21
PaperQA2 | 166.9 | 0.7 | 3.14 | 53.1 | 42.2 | 3.67 | 3.46 | 4.20

**中文译文 · 机器初译**

| Length | Inf. time (min) | # of Citations | Prec. | Rec. | Org. | Cov. | Rel.
Human | 289.5 | 56.8 | 6.0 | 44.4 | 41.5 | – | – | –
OS -GPT4o | 716.3 | 1.5 | 9.8 | 38.0 | 37.1 | 4.63 | 4.50 | 4.23
OS -8B | 578.6 | 0.9 | 21.6 | 42.5 | 43.2 | 3.92 | 4.44 | 4.02
GPT4o | 281.3 | 0.5 | 3.8 | 0.8 | 0.6 | 4.06 | 3.94 | 4.21
PaperQA2 | 166.9 | 0.7 | 3.14 | 53.1 | 42.2 | 3.67 | 3.46 | 4.20

表内文字对照（数值与原始行列保持不变）：
Length → 长度
Inf → Inf
time (min) → 时间（分钟）
of Citations → 引用量
Prec → Prec
Rec → Rec
Org → 组织
Cov → Cov
Rel → 相关
Human → 人类
OS -GPT → 操作系统 -GPT
OS - → 操作系统 -
GPT → GPT
PaperQA → PaperQA

### openscholar-0504

**English original**

Table 14: Human-written answer stats . Models tend to generate longer responses, citing more papers than humans. For reference, we run GPT4o without retrieval on the human evaluation queries.

**中文译文 · 机器初译**

表14：人类撰写的回答统计。与人类相比，这些模型倾向于生成更长的回复，并引用更多的文献。作为参考，我们在人类评估查询中使用了未进行检索的 GPT4o。

### openscholar-0505

**English original**

Table 14 provides basic statistics for human and OpenScholar -generated responses, detailing the average length, the number of cited articles, and the scores for each evaluation metric. We observed that human answers are generally shorter and reference fewer papers compared to model-generated outputs.
While a concurrent study normalizes human-written answers using an LM to control for confounding factors ( Si et al., 2024 ) , we retain the original human and model answers for our human evaluation and conduct extensive analysis to understand how these differences influence human preferences.

**中文译文 · 机器初译**

表14提供了人类回答与OpenScholar生成回答的基本统计信息，详细列出了平均长度、引用的论文数量以及各项评估指标的得分。我们观察到，与模型生成的输出相比，人类的回答通常更短，引用的论文也较少。虽然一项相关研究使用大语言模型对人工撰写的回答进行标准化处理以控制混杂因素（Si等，2024），但在我们的人类评估中仍保留了原始的人类回答和模型生成的回答，并进行了深入分析以了解这些差异如何影响人类的偏好。

### openscholar-0506

**English original**

We ran our automated evaluation pipelines, which include assessments of citation precision, recall, and writing quality, on both human- and model-generated answers. Our findings reveal that OS-8B frequently matches or even surpasses expert-level citation precision and recall, whereas OS-GPT4o performs slightly worse in terms of citation accuracy. Although PaperQA2 demonstrates higher citation precision compared to OS-8B or human experts, its answers are often brief and cite fewer papers, leading to limited coverage.

**中文译文 · 机器初译**

我们对自动化评估流程进行了测试，该流程包括对人类和模型生成的答案的引用精度、召回率及写作质量进行评估。研究结果表明，OS-8B的引用精度与专家水平相当甚至更高，而OS-GPT4o在引用准确性方面表现稍差。尽管PaperQA2的引用精度高于OS-8B或人类专家，但其答案通常较为简短，引用的论文数量也较少，因此覆盖范围有限。

### openscholar-0507

**English original**

Qualitative analyses on experts’ explanations of pair-wise preference.

**中文译文 · 机器初译**

对专家对成对偏好解释的定性分析。

### openscholar-0508

**English original**

Table 15 shows experts’ explanations on pair-wise preferences.

**中文译文 · 机器初译**

表15展示了专家对成对偏好方面的解释。

### openscholar-0509

**English original**

Category | % | Examples
Organization | 12% | Lots of redundancy and repeat in B
 | | Although B has lots of overlaps, but B covers more aspects in grating behavior
Relevance | 23% | Response spends half of the text talking about the performance comparison between fine-tuning and RAG, instead of the question “fine-tuning on RAG”.
 | | A contains some unnecessary details that don’t help understand the topic.
 | | Response A has a poor organization and a little deviation from the topic when it talks about privacy and safety of RLHF.
 | | Although response A shows a smaller coverage, it is slightly better than B due to detailed description of the techniques in generating reasoning data.
 | | B focuses on numerical methods and gives more approachable models.
Coverage | 29% | A is clearly more helpful as it provides a clean organization and cover more papers.
 | | Although response A shows a smaller coverage, it is slightly better than B due to detailed description of the techniques in generating reasoning data.
 | | both answers are really organized and provides a nice overview! I slightly prefer A as it’s more detailed.
 | | B is too concise and the organization could be improved.
 | | I prefer B, since A is a little scant in terms of information coverage. Furthermore, A uses some shorthand that was confusing to parse. Overall B gave a much more comprehensive and useful response.
 | | While A has several issues e.g., initial part of the answer are heavily depending on single paper, compared to B, which is too short and concise, A is more detailed and at least provide nice overview of the area.
 | | B contains more comprehensive results that addresses both phenomena and theories.
Citations | 9% | Some information provided by B is irrelevant to the quantum effect (like dark matter) and some citations are not representative (biological).

**中文译文 · 机器初译**

Category | % | Examples
Organization | 12% | Lots of redundancy and repeat in B
 | | Although B has lots of overlaps, but B covers more aspects in grating behavior
Relevance | 23% | Response spends half of the text talking about the performance comparison between fine-tuning and RAG, instead of the question “fine-tuning on RAG”.
 | | A contains some unnecessary details that don’t help understand the topic.
 | | Response A has a poor organization and a little deviation from the topic when it talks about privacy and safety of RLHF.
 | | Although response A shows a smaller coverage, it is slightly better than B due to detailed description of the techniques in generating reasoning data.
 | | B focuses on numerical methods and gives more approachable models.
Coverage | 29% | A is clearly more helpful as it provides a clean organization and cover more papers.
 | | Although response A shows a smaller coverage, it is slightly better than B due to detailed description of the techniques in generating reasoning data.
 | | both answers are really organized and provides a nice overview! I slightly prefer A as it’s more detailed.
 | | B is too concise and the organization could be improved.
 | | I prefer B, since A is a little scant in terms of information coverage. Furthermore, A uses some shorthand that was confusing to parse. Overall B gave a much more comprehensive and useful response.
 | | While A has several issues e.g., initial part of the answer are heavily depending on single paper, compared to B, which is too short and concise, A is more detailed and at least provide nice overview of the area.
 | | B contains more comprehensive results that addresses both phenomena and theories.
Citations | 9% | Some information provided by B is irrelevant to the quantum effect (like dark matter) and some citations are not representative (biological).

表内文字对照（数值与原始行列保持不变）：
Category → 类别
Examples → 示例
Organization → 组织
Lots of redundancy and repeat in B → 其中存在大量冗余和重复内容
Although B has lots of overlaps → 尽管 B 有很多重叠部分
but B covers more aspects in grating behavior → 但 B 在光栅行为方面涵盖了更多方面
Relevance → 相关性
Response spends half of the text talking about the performance comparison between fine-tuning and RAG → 回复内容中有一半篇幅讨论了微调与 RAG 的性能对比
instead of the question → 而非该问题
fine-tuning on RAG → 在 RAG 上进行微调
A contains some unnecessary details that don → A 中包含了一些不必要的细节
t help understand the topic → 有助于理解该主题
Response A has a poor organization and a little deviation from the topic when it talks about privacy and safety of RLHF → 回应A在讨论强化学习人类反馈强化学习（RLHF）的隐私与安全性时，组织混乱且偏离主题程度较大
Although response A shows a smaller coverage → 尽管选项 A 的覆盖范围较小
it is slightly better than B due to detailed description of the techniques in generating reasoning data → 由于对生成推理数据的技术进行了详细描述，其性能略优于 B
B focuses on numerical methods and gives more approachable models → B部分专注于数值方法，提供了更易于理解的模型
Coverage → 覆盖范围
A is clearly more helpful as it provides a clean organization and cover more papers → A显然更有帮助，因为它结构清晰，且涵盖更多论文
both answers are really organized and provides a nice overview → 两个答案都非常有条理，并提供了良好的概述
I slightly prefer A as it → 我稍微更偏爱 A，因为
s more detailed → 更详细的说明
B is too concise and the organization could be improved → B的表述过于简洁，其组织结构还可以改进
I prefer B → 我更喜欢 B
since A is a little scant in terms of information coverage → 由于 A 在信息覆盖方面稍显不足
Furthermore → 此外
A uses some shorthand that was confusing to parse → A使用了一些难以解析的简写符号
Overall B gave a much more comprehensive and useful response → 整体B给出了更为全面且实用的回应
While A has several issues e → 虽然 A 存在多个问题
initial part of the answer are heavily depending on single paper → 答案的初始部分在很大程度上依赖于某篇特定论文
compared to B → 与 B 相比
which is too short and concise → 这太短且简洁了
A is more detailed and at least provide nice overview of the area → A 的内容更为详细，至少能提供该领域的良好概述
B contains more comprehensive results that addresses both phenomena and theories → B包含了更为全面的结果，既涉及现象研究，也涉及理论探讨
Citations → 引用
Some information provided by B is irrelevant to the quantum effect (like dark matter) and some citations are not representative (biological) → B提供的某些信息与量子效应（如暗物质）无关，且部分引用并不具有代表性（属于生物学领域）

### openscholar-0510

**English original**

Table 15: Explanations on preferences .

**中文译文 · 机器初译**

表15：偏好说明。

### openscholar-0511

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0512

**English original**

(a) GPT4 answer

**中文译文 · 机器初译**

(a) GPT4 回答

### openscholar-0513

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0514

**English original**

(b) Llama 3 8B

**中文译文 · 机器初译**

(b) Llama 3 8B

### openscholar-0515

**English original**

Figure 11: Agreement between Prometheus and humans
on fluency.

**中文译文 · 机器初译**

图11：Prometheus与人类在流畅性方面的一致性。

### openscholar-0516

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0517

**English original**

(a) GPT4 answer

**中文译文 · 机器初译**

(a) GPT4 回答

### openscholar-0518

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0519

**English original**

(b) Llama 3 8B

**中文译文 · 机器初译**

(b) Llama 3 8B

### openscholar-0520

**English original**

Figure 12: Agreement between Prometheus and humans
on relevance.

**中文译文 · 机器初译**

图 12：Prometheus与人类在相关性方面的一致性。

### openscholar-0521

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0522

**English original**

(a) GPT4 answer

**中文译文 · 机器初译**

(a) GPT4 回答

### openscholar-0523

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0524

**English original**

(b) Llama 3 8B

**中文译文 · 机器初译**

(b) Llama 3 8B

### openscholar-0525

**English original**

Figure 13: Agreement between Prometheus and humans
on coverage.

**中文译文 · 机器初译**

图13：Prometheus与人类在覆盖范围上的一致性。

### openscholar-0526

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0527

**English original**

(a) GPT4 answer

**中文译文 · 机器初译**

(a) GPT4 回答

### openscholar-0528

**English original**

Refer to caption

**中文译文 · 机器初译**

参见标题说明

### openscholar-0529

**English original**

(b) Llama 3 8B

**中文译文 · 机器初译**

(b) Llama 3 8B

### openscholar-0530

**English original**

Figure 14: Agreement between Prometheus and humans
on overall usefulness.

**中文译文 · 机器初译**

图14：Prometheus与人类在整体实用性方面的共识程度。

### openscholar-0531

**English original**

Agreements between humans and LLM-as-a-judge.

**中文译文 · 机器初译**

人类与作为评判者的大语言模型之间的协议。

### openscholar-0532

**English original**

| Accuracy ( $\uparrow$ ) | Pearsonr | $\Delta$ (human - model)
 | Org | Cov | Rel | Org | Cov. | Rel | Org | Cov. | Rel
OS-GPT4 | 0.49 | 0.52 | 0.36 | 0.21 | 0.10 | -0.01 | -0.22 | 0.02 | 0.08
OS-8B | 0.47 | 0.48 | 0.53 | 0.34 | 0.15 | -0.20 | 0.18 | 0.22 | -0.16

**中文译文 · 机器初译**

| Accuracy ( $\uparrow$ ) | Pearsonr | $\Delta$ (human - model)
 | Org | Cov | Rel | Org | Cov. | Rel | Org | Cov. | Rel
OS-GPT4 | 0.49 | 0.52 | 0.36 | 0.21 | 0.10 | -0.01 | -0.22 | 0.02 | 0.08
OS-8B | 0.47 | 0.48 | 0.53 | 0.34 | 0.15 | -0.20 | 0.18 | 0.22 | -0.16

表内文字对照（数值与原始行列保持不变）：
Accuracy ( → 准确性（
uparrow → ↑
Pearsonr → Pearsonr
Delta → Delta
human - model) → 人类模型
Org → 组织
Cov → Cov
Rel → 相关
OS-GPT → OS-GPT
OS- → 操作系统

### openscholar-0533

**English original**

Table 16: Agreement between human and Prometheus assessments on Human and OpenScholar (GPT4o) answers . We found that with gold answers, Prometheous evaluations often align with expert evaluations on some aspects.

**中文译文 · 机器初译**

表16：人类评估与Prometheus评估在“人类”及OpenScholar（GPT4o）回答方面的一致性。我们发现，在采用黄金答案的情况下，Prometheus的评估在某些方面往往与专家评估一致。

### openscholar-0534

**English original**

We also examine the alignment between human assessments and LLM assessments for evaluating the fine-grained quality of responses. Specifically, we assess both the accuracy and the mean absolute error of the evaluator LLM (i.e., prometheus-eval/prometheus-bgb-8x7b-v2.0 ), using human annotations as the gold standard. Table 16 presents the results.

**中文译文 · 机器初译**

我们还研究了人类评估与大语言模型评估之间的匹配程度，以评估回复的细致质量。具体而言，我们以人类注释作为金标准，评估了评估器大语言模型的准确性及平均绝对误差（即 prometheus-eval/prometheus-bgb-8x7b-v2.0）。表16展示了相关结果。

### openscholar-0535

**English original**

Figures 12 , 13 , and 14 show the confusion matrices between human and Prometheus predictions. Confusions often happen between adjacent classes (e.g., 4 v.s. 5), and the evaluator LMs rarely confuse negative classes (lower than 3) and positive classes.
Overall, for organization and coverage, Prometheus shows a weak correlation and about 50% accuracy, with disagreements that often occur between adjacent classes (e.g., scoring a 4 versus a 5).
When we compare the differences between the average scores of each aspect, as predicted by human and evaluator LMs, on relevance, coverage, and overall usefulness, the absolute difference is less than -0.2, and the ranking between models remains the same.

**中文译文 · 机器初译**

图12、图13和图14展示了人类预测与Prometheus预测之间的混淆矩阵。混淆现象通常发生在相邻类别之间（例如4与5），而评估智能体LLM则很少出现负类别（低于3）与正类别之间的混淆。总体而言，在组织和覆盖度方面，Prometheus的相关性较弱，准确率约为50%，且经常出现相邻类别之间的差异（例如给4分和给5分）。
当我们比较各方面的平均得分差异时，根据人类评估者大语言模型和评估大语言模型的预测，在相关性、覆盖率和整体实用性方面，绝对差异小于 -0.2，各模型的排名也保持不变。

### openscholar-0536

**English original**

Comparison of model and expert-written answers.

**中文译文 · 机器初译**

模型与专家撰写的答案对比。

### openscholar-0537

**English original**

Tables 17 , 18 , 19 , 20 , 21 show model and expert-written answers with expert-evaluated scores.

**中文译文 · 机器初译**

表17、表18、表19、表20、表21展示了模型及专家撰写的答案以及由专家评估的得分。

### openscholar-0538

**English original**

Question: What are ways to cool the center-of-mass (CoM) motion of levitated nanoparticles?
Human: For levitated nanoparticles, cooling their motional degrees of freedom—especially to the quantum ground state—is of great importance. Cooled nanoparticles can be employed to study quantum effects in macroscopic objects, prepare complex quantum states, and even explore the interplay between gravity and quantum mechanics through free-fall experiments.Currently, the most commonly used cooling method is feedback cooling [Tongcang Li et al. 2011 - 1]. By measuring the real-time position of the levitated nanoparticle, its instantaneous velocity can be determined, allowing for the application of a feedback cooling scattering force in the opposite direction of the velocity. Using this approach, the center-of-mass (CoM) motion of a levitated nanoparticle can be cooled from room temperature to 1.5 mK [Tongcang Li et al. 2011 - 2], or even to the ground state in cryogenic environments [L. Novotný et al. 2021].An alternative method involves levitating the nanosphere in an optical cavity and cooling via coherent scattering [Uroš Delić et al. 2018 - 1]. The trapping laser is red-detuned from the optical resonance at the CoM motional frequency. The anti-Stokes scattering process, which removes energy from the nanoparticle, becomes resonant with and enhanced by the optical cavity. This technique can cool the CoM motion to temperatures as low as 1 K [Uroš Delić et al. 2018 - 2] and also to the ground-state [Unknown et al. 2020]. A more recent proposal, known as cold damping, is similar to conventional feedback cooling. However, instead of applying a counteracting force by modulating the light’s intensity, this method adjusts the spatial position of the optical traps using an acousto-optic deflector (AOD) [Jayadev Vijayan et al. 2022 - 1]. When the position of the traps does not align with the center of the levitated nanoparticle, the particle experiences an optical gradient force, which serves as the feedback force. The main advantages of this method are its relative simplicity and its potential scalability for cooling multiple nanoparticles [Jayadev Vijayan et al. 2022 - 2].
Fine-grained Assessments: Org 5.0 Rel 5.0 Cov 4.0
Model (OS-GPT4o): Cooling the center-of-mass (CoM) motion of levitated nanoparticles is crucial for advancing experiments in levitated optomechanics and achieving quantum control of macroscopic objects. Several techniques have been developed and refined to address this challenge, each with its unique advantages and limitations.One prominent approach is **cavity-assisted optomechanical cooling**, where the CoM motion is cooled via coherent scattering of light into an optical cavity. In this method, a nanoparticle is trapped using an optical tweezer, and light from the tweezer is coherently scattered into a blue-detuned cavity mode, reducing the mechanical energy of the particle [Dominik Windey et al. 2018][Dominik Windey et al. Cavity-Based 3D Cooling of a Levitated Nanoparticle via Coherent Scattering.]. This technique has been experimentally realized to achieve minimal temperatures in the millikelvin regime for pressures around ( $10^{-5}$ ) [Dominik Windey et al. Cavity-Based 3D Cooling of a Levitated Nanoparticle via Coherent Scattering.]. The major advantage of this method is the reduced technological complexity and the ability to cool along all three motional axes [C. Gonzalez-Ballestero et al. Theory for cavity cooling of levitated nanoparticles via coherent scattering: Master equation approach][Dominik Windey et al. Cavity-Based 3D Cooling of a Levitated Nanoparticle via Coherent Scattering.]. Additionally, this techniqueś ability to leverage the standing wave patterns in the cavity allows precise control over the cooling process. However, this method is limited by the precision with which the particle can be positioned within the intracavity standing wave and the alignment stability of the optical setup.Another effective method is **parametric feedback cooling**, which involves actively measuring the CoM position and applying a feedback force to counteract the motion [C. Gonzalez-Ballestero et al. Theory for cavity cooling of levitated nanoparticles via coherent scattering: Master equation approach][T. Penny et al. 2021]. This is typically achieved using an optical tweezer combined with electronic feedback to modulate the trapping potential. Parametric feedback cooling has been successful in reducing CoM temperatures from room temperature to below a hundred phonons [F. Tebbenjohanns et al. 2018]. This method is particularly beneficial for its simplicity and effectiveness in environments with significant experimental noise. Experimental results indicate that velocity damping, a specific form of feedback cooling, can achieve lower temperatures and is more resilient to experimental noise [T. Penny et al. 2021]. However, parametric feedback cooling generally requires sophisticated electronic control systems and precise calibration, which can be technically demanding.**Optimal feedback cooling** with adaptive control represents another innovative technique. Here, a Coulomb force is applied to a charged levitated nanoparticle using a pair of electrodes. A machine learning algorithm optimizes the control gains, enabling rapid cooling to temperatures as low as 5 mK at ( $3\times 10^{-7},\text{mbar}$ ) [Gerard P. Conangla et al. Optimal Feedback Cooling of a Charged Levitated Nanoparticle with Adaptive Control.][Gerard P. Conangla et al. 2018]. This method is noted for its robustness and the ability to extend easily to 3D cooling, making it particularly suitable for high repetition rate experiments and force sensing applications. The adaptive control strategy also ensures high precision and adaptability to varying experimental conditions. Despite its advantages, the implementation of this method can be complex due to the need for charging the nanoparticles and sophisticated control algorithms.**Cold damping**, which is a form of measurement-based feedback cooling, uses linear velocity feedback on charged particles. This technique employs external electrodes to apply electrostatic forces, achieving cooling down to microkelvin temperatures [F. Tebbenjohanns et al. 2018][Jayadev Vijayan et al. 2022]. (cont.)
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 5.0
Preference: OS-GPT4o. Explanation: B has more details from various citations, though the citations are not well chosen. For example, B lists theoretical papers when introducing experimental techniques and some papers are not most representative in the field.

**中文译文 · 机器初译**

Question: What are ways to cool the center-of-mass (CoM) motion of levitated nanoparticles?
Human: For levitated nanoparticles, cooling their motional degrees of freedom—especially to the quantum ground state—is of great importance. Cooled nanoparticles can be employed to study quantum effects in macroscopic objects, prepare complex quantum states, and even explore the interplay between gravity and quantum mechanics through free-fall experiments.Currently, the most commonly used cooling method is feedback cooling [Tongcang Li et al. 2011 - 1]. By measuring the real-time position of the levitated nanoparticle, its instantaneous velocity can be determined, allowing for the application of a feedback cooling scattering force in the opposite direction of the velocity. Using this approach, the center-of-mass (CoM) motion of a levitated nanoparticle can be cooled from room temperature to 1.5 mK [Tongcang Li et al. 2011 - 2], or even to the ground state in cryogenic environments [L. Novotný et al. 2021].An alternative method involves levitating the nanosphere in an optical cavity and cooling via coherent scattering [Uroš Delić et al. 2018 - 1]. The trapping laser is red-detuned from the optical resonance at the CoM motional frequency. The anti-Stokes scattering process, which removes energy from the nanoparticle, becomes resonant with and enhanced by the optical cavity. This technique can cool the CoM motion to temperatures as low as 1 K [Uroš Delić et al. 2018 - 2] and also to the ground-state [Unknown et al. 2020]. A more recent proposal, known as cold damping, is similar to conventional feedback cooling. However, instead of applying a counteracting force by modulating the light’s intensity, this method adjusts the spatial position of the optical traps using an acousto-optic deflector (AOD) [Jayadev Vijayan et al. 2022 - 1]. When the position of the traps does not align with the center of the levitated nanoparticle, the particle experiences an optical gradient force, which serves as the feedback force. The main advantages of this method are its relative simplicity and its potential scalability for cooling multiple nanoparticles [Jayadev Vijayan et al. 2022 - 2].
Fine-grained Assessments: Org 5.0 Rel 5.0 Cov 4.0
Model (OS-GPT4o): Cooling the center-of-mass (CoM) motion of levitated nanoparticles is crucial for advancing experiments in levitated optomechanics and achieving quantum control of macroscopic objects. Several techniques have been developed and refined to address this challenge, each with its unique advantages and limitations.One prominent approach is **cavity-assisted optomechanical cooling**, where the CoM motion is cooled via coherent scattering of light into an optical cavity. In this method, a nanoparticle is trapped using an optical tweezer, and light from the tweezer is coherently scattered into a blue-detuned cavity mode, reducing the mechanical energy of the particle [Dominik Windey et al. 2018][Dominik Windey et al. Cavity-Based 3D Cooling of a Levitated Nanoparticle via Coherent Scattering.]. This technique has been experimentally realized to achieve minimal temperatures in the millikelvin regime for pressures around ( $10^{-5}$ ) [Dominik Windey et al. Cavity-Based 3D Cooling of a Levitated Nanoparticle via Coherent Scattering.]. The major advantage of this method is the reduced technological complexity and the ability to cool along all three motional axes [C. Gonzalez-Ballestero et al. Theory for cavity cooling of levitated nanoparticles via coherent scattering: Master equation approach][Dominik Windey et al. Cavity-Based 3D Cooling of a Levitated Nanoparticle via Coherent Scattering.]. Additionally, this techniqueś ability to leverage the standing wave patterns in the cavity allows precise control over the cooling process. However, this method is limited by the precision with which the particle can be positioned within the intracavity standing wave and the alignment stability of the optical setup.Another effective method is **parametric feedback cooling**, which involves actively measuring the CoM position and applying a feedback force to counteract the motion [C. Gonzalez-Ballestero et al. Theory for cavity cooling of levitated nanoparticles via coherent scattering: Master equation approach][T. Penny et al. 2021]. This is typically achieved using an optical tweezer combined with electronic feedback to modulate the trapping potential. Parametric feedback cooling has been successful in reducing CoM temperatures from room temperature to below a hundred phonons [F. Tebbenjohanns et al. 2018]. This method is particularly beneficial for its simplicity and effectiveness in environments with significant experimental noise. Experimental results indicate that velocity damping, a specific form of feedback cooling, can achieve lower temperatures and is more resilient to experimental noise [T. Penny et al. 2021]. However, parametric feedback cooling generally requires sophisticated electronic control systems and precise calibration, which can be technically demanding.**Optimal feedback cooling** with adaptive control represents another innovative technique. Here, a Coulomb force is applied to a charged levitated nanoparticle using a pair of electrodes. A machine learning algorithm optimizes the control gains, enabling rapid cooling to temperatures as low as 5 mK at ( $3\times 10^{-7},\text{mbar}$ ) [Gerard P. Conangla et al. Optimal Feedback Cooling of a Charged Levitated Nanoparticle with Adaptive Control.][Gerard P. Conangla et al. 2018]. This method is noted for its robustness and the ability to extend easily to 3D cooling, making it particularly suitable for high repetition rate experiments and force sensing applications. The adaptive control strategy also ensures high precision and adaptability to varying experimental conditions. Despite its advantages, the implementation of this method can be complex due to the need for charging the nanoparticles and sophisticated control algorithms.**Cold damping**, which is a form of measurement-based feedback cooling, uses linear velocity feedback on charged particles. This technique employs external electrodes to apply electrostatic forces, achieving cooling down to microkelvin temperatures [F. Tebbenjohanns et al. 2018][Jayadev Vijayan et al. 2022]. (cont.)
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 5.0
Preference: OS-GPT4o. Explanation: B has more details from various citations, though the citations are not well chosen. For example, B lists theoretical papers when introducing experimental techniques and some papers are not most representative in the field.

表内文字对照（数值与原始行列保持不变）：
Question → 问题
What are ways to cool the center-of-mass (CoM) motion of levitated nanoparticles → 有哪些方法可以冷却悬浮纳米粒子的质心运动
Human → 人类
For levitated nanoparticles → 对于悬浮纳米颗粒
cooling their motional degrees of freedom → 降低其运动自由度
especially to the quantum ground state → 尤其是针对量子基态
is of great importance → 非常重要
Cooled nanoparticles can be employed to study quantum effects in macroscopic objects → 冷却后的纳米粒子可用于研究宏观物体中的量子效应
prepare complex quantum states → 准备复杂的量子态
and even explore the interplay between gravity and quantum mechanics through free-fall experiments → 甚至通过自由落体实验探索重力与量子力学之间的相互作用
Currently → 目前
the most commonly used cooling method is feedback cooling → 最常用的冷却方法为反馈冷却
Tongcang Li et al → 童康 李等
By measuring the real-time position of the levitated nanoparticle → 通过测量悬浮纳米粒子的实时位置
its instantaneous velocity can be determined → 其瞬时速度可以确定
allowing for the application of a feedback cooling scattering force in the opposite direction of the velocity → 允许在速度相反的方向上应用反馈冷却散射力
Using this approach → 采用这种方法
the center-of-mass (CoM) motion of a levitated nanoparticle can be cooled from room temperature to → 悬浮纳米粒子的质心运动温度可从室温降至
or even to the ground state in cryogenic environments → 甚至在低温环境中也能回到基态
Novotn → Novotn
et al → 等
An alternative method involves levitating the nanosphere in an optical cavity and cooling via coherent scattering → 另一种方法是将纳米球悬浮在光学腔中，通过相干散射进行冷却
Uro → 泌尿科
Deli → Deli
The trapping laser is red-detuned from the optical resonance at the CoM motional frequency → 捕获激光与 CoM 运动频率下的光学共振频率存在红移失谐
The anti-Stokes scattering process → 反斯托克斯散射过程
which removes energy from the nanoparticle → 该过程会从纳米粒子中去除能量
becomes resonant with and enhanced by the optical cavity → 与光腔产生共鸣并得到增强
This technique can cool the CoM motion to temperatures as low as → 这种技术可以将 CoM 运动的温度降至极低水平
and also to the ground-state → 以及到基态
Unknown et al → Unknown等人
A more recent proposal → 一项较新的提案
known as cold damping → 被称为冷阻尼
is similar to conventional feedback cooling → 与常规反馈冷却方式类似
However → 然而
instead of applying a counteracting force by modulating the light → 而不是通过调节光线来施加反作用力
s intensity → s强度
this method adjusts the spatial position of the optical traps using an acousto-optic deflector (AOD) → 该方法利用声光偏转器调整光学陷阱的空间位置
Jayadev Vijayan et al → Jayadev Vijayan 等
When the position of the traps does not align with the center of the levitated nanoparticle → 当陷阱的位置与悬浮纳米粒子的中心不一致时
the particle experiences an optical gradient force → 该粒子受到光学梯度力作用
which serves as the feedback force → 作为反馈机制的那个
The main advantages of this method are its relative simplicity and its potential scalability for cooling multiple nanoparticles → 该方法的主要优势在于其相对简单性，以及其在冷却多个纳米粒子方面的潜在可扩展性
Fine-grained Assessments → 细粒度评估
Org → 组织
Rel → 相关
Cov → Cov
Model (OS-GPT → 模型（OS-GPT）
Cooling the center-of-mass (CoM) motion of levitated nanoparticles is crucial for advancing experiments in levitated optomechanics and achieving quantum control of macroscopic objects → 冷却悬浮纳米颗粒的质心运动对于推进悬浮光力学实验以及实现宏观物体的量子控制至关重要
Several techniques have been developed and refined to address this challenge → 已经开发并改进了多种技术来应对这一挑战
each with its unique advantages and limitations → 每个模型都具有其独特的优势与局限性
One prominent approach is → 一种重要的方法是将
cavity-assisted optomechanical cooling → 腔体辅助光机冷却
where the CoM motion is cooled via coherent scattering of light into an optical cavity → 其中，CoM 的运动通过光向光学腔的相干散射来冷却
In this method → 在该方法中
a nanoparticle is trapped using an optical tweezer → 使用光学镊子捕获了一种纳米粒子
and light from the tweezer is coherently scattered into a blue-detuned cavity mode → 以及镊子发出的光被一致地散射到一种蓝色失谐腔模中
reducing the mechanical energy of the particle → 降低粒子的机械能
Dominik Windey et al → Dominik Windey 等
Cavity-Based → 基于腔体的方法
D Cooling of a Levitated Nanoparticle via Coherent Scattering → 通过相干散射实现悬浮纳米颗粒的冷却
This technique has been experimentally realized to achieve minimal temperatures in the millikelvin regime for pressures around ( → 该技术已通过实验验证，能够在约（  ）的压力下实现微开尔文范围内的最低温度。
The major advantage of this method is the reduced technological complexity and the ability to cool along all three motional axes → 该方法的主要优势在于技术复杂度较低，且能够沿所有三个运动轴进行冷却
Gonzalez-Ballestero et al → Gonzalez-Ballestero 等
Theory for cavity cooling of levitated nanoparticles via coherent scattering → 基于相干散射的悬浮纳米粒子腔体冷却理论
Master equation approach → 主方程方法
Additionally → 此外
this technique → 这种技术
ability to leverage the standing wave patterns in the cavity allows precise control over the cooling process → 能够利用腔体内的驻波模式，从而实现对冷却过程的精准控制
this method is limited by the precision with which the particle can be positioned within the intracavity standing wave and the alignment stability of the optical setup → 该方法受到粒子在腔内驻波中定位精度以及光学装置对齐稳定性这两个因素的限制
Another effective method is → 另一种有效方法是将
parametric feedback cooling → 参数化反馈冷却
which involves actively measuring the CoM position and applying a feedback force to counteract the motion → 该过程涉及主动测量CoM位置，并施加反馈力以抵消运动
Penny et al → Penny等人
This is typically achieved using an optical tweezer combined with electronic feedback to modulate the trapping potential → 这通常是通过使用光学镊子结合电子反馈来调节捕获势来实现
Parametric feedback cooling has been successful in reducing CoM temperatures from room temperature to below a hundred phonons → 参数化反馈冷却技术成功地将 CoM 温度从室温降低至一百个声子以下
Tebbenjohanns et al → Tebbenjohanns 等
This method is particularly beneficial for its simplicity and effectiveness in environments with significant experimental noise → 该方法因其简单性和在存在大量实验噪声的环境中有效性而特别有益
Experimental results indicate that velocity damping → 实验结果表明了速度阻尼的效果
a specific form of feedback cooling → 一种特定的反馈冷却形式
can achieve lower temperatures and is more resilient to experimental noise → 能够实现更低的温度，且对实验噪声具有更强的耐受性
parametric feedback cooling generally requires sophisticated electronic control systems and precise calibration → 参数化反馈冷却通常需要复杂的电子控制系统和精确的校准
which can be technically demanding → 这在技术层面可能具有挑战性
Optimal feedback cooling → 最优反馈冷却
with adaptive control represents another innovative technique → 自适应控制代表了另一种创新技术
Here → 这里
a Coulomb force is applied to a charged levitated nanoparticle using a pair of electrodes → 使用一对电极对带电悬浮纳米粒子施加库仑力
A machine learning algorithm optimizes the control gains → 一种机器学习算法优化了控制增益
enabling rapid cooling to temperatures as low as → 实现快速冷却至低至的温度
mK at ( → mK 在 (
times → 次数
text → 文本
mbar → mbar
Gerard P → 杰拉德·P
Conangla et al → Conangla等人
Optimal Feedback Cooling of a Charged Levitated Nanoparticle with Adaptive Control → 采用自适应控制技术对带电悬浮纳米颗粒进行最优反馈冷却
This method is noted for its robustness and the ability to extend easily to → 该方法以其稳健性以及易于扩展的能力而著称
D cooling → D冷却
making it particularly suitable for high repetition rate experiments and force sensing applications → 使其特别适用于高重复率实验和力感知应用
The adaptive control strategy also ensures high precision and adaptability to varying experimental conditions → 这种自适应控制策略还能确保高精度以及对不同实验条件的适应性
Despite its advantages → 尽管具有优势
the implementation of this method can be complex due to the need for charging the nanoparticles and sophisticated control algorithms → 该方法的实现可能较为复杂，因为需要对纳米颗粒进行充电以及使用复杂的控制算法
Cold damping → 冷阻尼
which is a form of measurement-based feedback cooling → 这是一种基于测量的反馈冷却方式
uses linear velocity feedback on charged particles → 利用带电粒子的线速度反馈机制
This technique employs external electrodes to apply electrostatic forces → 该技术使用外部电极来施加静电力
achieving cooling down to microkelvin temperatures → 实现冷却至微开尔文温度
cont → 内容
Preference → 偏好
OS-GPT → OS-GPT
Explanation → 说明
B has more details from various citations → B 包含了来自不同引文的更多细节
though the citations are not well chosen → 尽管引用的文献选择并不恰当
For example → 例如
B lists theoretical papers when introducing experimental techniques and some papers are not most representative in the field → 在介绍实验技术时，B类列出了理论论文，而部分论文在该领域并非最具代表性

### openscholar-0539

**English original**

Table 17: Comparison of human and model answers (Photonics).

**中文译文 · 机器初译**

表17：人类与模型答案的对比（光子学）。

### openscholar-0540

**English original**

Question: Is it possible for microcapsules to cross the blood brain barrier?
Human: The blood-brain barrier (BBB) is an essential semi-permeable biological barrier that protects the brain by preventing foreign substances from entering [Di Wu et al. 2023]. This means that even therapeutics cannot properly access the brain as the BBB excludes them as well. The tight gap of the semi-permeable barrier only allows lipid-soluble drugs with an average molecular weight lower than 600 Da through passive diffusion. Nanoparticles are commonly used to deliver therapeutics to the brain by crossing the BBB thanks to their small size, low toxicity, biocompatibility, and controllable drug release kinetics [Andrew M Hersh et al. 2022]. For brain delivery applications, nanoparticles between 10-100 nm are the most effective, but the optimal size depends on the type of biomaterial that forms the nanoparticles. Interestingly, some studies reported that some 1-10 $\mu$ m bacteria can pass through the BBB, which gave the researchers an idea to develop bacteria-mediated drug delivery systems [Di Wu et al. 2023]. Other studies also demonstrated the BBB crossing of micron-scale plastic particles using polystyrene (PS) microspheres of size 0.293, 1.14, and 9.55 $\mu$ m, with the smallest particle reaching the brain within only 2 hours upon exposure [V. Kopatz et al. 2023]. Researchers have developed various methods for improved drug delivery to the brain, and one good example is the focused ultrasound technique with microbubbles [N. Lapin et al. 2020]. Here, the rapid oscillation of intravascular microbubbles stimulates the BBB to increase the uptake of nanoparticles and other forms of therapeutics. The average diameter of microbubbles is 1.1-3.3 $\mu$ m, and they are typically administered via bolus intravenous injection.
Fine-grained Assessments: Org 4.0 Rel 4.0 Cov 4.0
Model (OS-GPT4o): The blood-brain barrier (BBB) presents a significant challenge for delivering therapeutic agents directly to the central nervous system (CNS). However, various strategies have been developed to enable microcapsules to cross the BBB, making it possible to deliver drugs or therapeutic agents effectively to the brain. Microcapsules, particularly those composed of alginate, have demonstrated potential in transporting substances across the BBB. Studies show that small alginate microcapsules, specifically in the size range of 100-200 $\mu m$ , can effectively bypass the BBB and deliver therapeutic agents to the brain. These microcapsules can pack more tightly together, increasing the number of cells and the rate of recombinant gene product secretion per volume of microcapsules. They also display increased mechanical strength, which is crucial for maintaining integrity during and after crossing the BBB [C. Ross et al. Development of small alginate microcapsules for recombinant gene product delivery to the rodent brain][M. Fakhoury et al. 2015]. Furthermore, lipid-based microcapsules have also been explored for BBB penetration. Lipid-alginate microcapsules (L-A microcapsules), which combine the properties of both lipids and alginate, have shown promising results. These microcapsules not only provide a physical barrier to protect encapsulated cells but also enhance autophagy, which promotes cell survival after transplantation into the brain. Studies have demonstrated that L-A microcapsules facilitate the delivery of neural stem cells (NSCs) into ischemic stroke models, reducing infarct volume and brain edema, and improving neurological outcomes [Rui Xu et al. 2022].Engineering of capsid-receptor interactions is another innovative approach. For example, peptide-modified adeno-associated virus (AAV) capsids can be engineered to interact with specific proteins that are expressed on the BBB, such as LY6A or LY6C1. These engineered capsids show enhanced CNS tropism, enabling the delivery of gene therapies more effectively across the BBB [Qin Huang et al. Targeting AAV vectors to the central nervous system by engineering capsid–receptor interactions that enable crossing of the blood–brain barrier]. Additionally, nanotechnology applications, such as the use of dendrimers, show promise. Poly-(amidoamine) (PAMAM) dendrimers have demonstrated the ability to diffuse in the CNS and penetrate neurons, presenting low cytotoxicity and effective delivery of anticancer drugs to the brain [M. Fakhoury et al. 2015]. These nanocarriers can be designed to be small enough to navigate the tight junctions of the BBB and deliver therapeutic agents.In some cases, osmotic agents like mannitol can be used to temporarily disrupt the BBB, enhancing the penetration of large molecules such as antibodies. This approach increases the permeability of the BBB by drawing water out of cells, thereby opening the tight junctions between endothelial cells [S. Liddelow et al. 2017]. Moreover, microcapsules coated with specific proteins or peptides to target the BBB have shown efficacy. For instance, protein-coated microcapsules can cross the BBB and release their therapeutic contents in the brain, targeting inflamed tissues and delivering treatment directly where it is needed [K. Timmis et al. 2020]. In conclusion, while the BBB remains a formidable barrier to central nervous system drug delivery, multiple strategies involving microcapsules and nanotechnology have shown potential to overcome this challenge. By leveraging the physical properties of microcapsules, engineering receptor interactions, and utilizing osmotic agents, researchers can enhance the delivery of therapeutic agents to the brain, offering hope for more effective treatments for neurological diseases.
Fine-grained Assessments: Org 3.0 Rel 5.0 Cov 5.0
Preference: OS-GPT4o. Explanation: OS-GPT4o is better as it provided a list of potential microcapsules that could pass the BBB through various methods, whereas Human is focused on different microorganisms instead, which are less relevant to the topic.)

**中文译文 · 机器初译**

Question: Is it possible for microcapsules to cross the blood brain barrier?
Human: The blood-brain barrier (BBB) is an essential semi-permeable biological barrier that protects the brain by preventing foreign substances from entering [Di Wu et al. 2023]. This means that even therapeutics cannot properly access the brain as the BBB excludes them as well. The tight gap of the semi-permeable barrier only allows lipid-soluble drugs with an average molecular weight lower than 600 Da through passive diffusion. Nanoparticles are commonly used to deliver therapeutics to the brain by crossing the BBB thanks to their small size, low toxicity, biocompatibility, and controllable drug release kinetics [Andrew M Hersh et al. 2022]. For brain delivery applications, nanoparticles between 10-100 nm are the most effective, but the optimal size depends on the type of biomaterial that forms the nanoparticles. Interestingly, some studies reported that some 1-10 $\mu$ m bacteria can pass through the BBB, which gave the researchers an idea to develop bacteria-mediated drug delivery systems [Di Wu et al. 2023]. Other studies also demonstrated the BBB crossing of micron-scale plastic particles using polystyrene (PS) microspheres of size 0.293, 1.14, and 9.55 $\mu$ m, with the smallest particle reaching the brain within only 2 hours upon exposure [V. Kopatz et al. 2023]. Researchers have developed various methods for improved drug delivery to the brain, and one good example is the focused ultrasound technique with microbubbles [N. Lapin et al. 2020]. Here, the rapid oscillation of intravascular microbubbles stimulates the BBB to increase the uptake of nanoparticles and other forms of therapeutics. The average diameter of microbubbles is 1.1-3.3 $\mu$ m, and they are typically administered via bolus intravenous injection.
Fine-grained Assessments: Org 4.0 Rel 4.0 Cov 4.0
Model (OS-GPT4o): The blood-brain barrier (BBB) presents a significant challenge for delivering therapeutic agents directly to the central nervous system (CNS). However, various strategies have been developed to enable microcapsules to cross the BBB, making it possible to deliver drugs or therapeutic agents effectively to the brain. Microcapsules, particularly those composed of alginate, have demonstrated potential in transporting substances across the BBB. Studies show that small alginate microcapsules, specifically in the size range of 100-200 $\mu m$ , can effectively bypass the BBB and deliver therapeutic agents to the brain. These microcapsules can pack more tightly together, increasing the number of cells and the rate of recombinant gene product secretion per volume of microcapsules. They also display increased mechanical strength, which is crucial for maintaining integrity during and after crossing the BBB [C. Ross et al. Development of small alginate microcapsules for recombinant gene product delivery to the rodent brain][M. Fakhoury et al. 2015]. Furthermore, lipid-based microcapsules have also been explored for BBB penetration. Lipid-alginate microcapsules (L-A microcapsules), which combine the properties of both lipids and alginate, have shown promising results. These microcapsules not only provide a physical barrier to protect encapsulated cells but also enhance autophagy, which promotes cell survival after transplantation into the brain. Studies have demonstrated that L-A microcapsules facilitate the delivery of neural stem cells (NSCs) into ischemic stroke models, reducing infarct volume and brain edema, and improving neurological outcomes [Rui Xu et al. 2022].Engineering of capsid-receptor interactions is another innovative approach. For example, peptide-modified adeno-associated virus (AAV) capsids can be engineered to interact with specific proteins that are expressed on the BBB, such as LY6A or LY6C1. These engineered capsids show enhanced CNS tropism, enabling the delivery of gene therapies more effectively across the BBB [Qin Huang et al. Targeting AAV vectors to the central nervous system by engineering capsid–receptor interactions that enable crossing of the blood–brain barrier]. Additionally, nanotechnology applications, such as the use of dendrimers, show promise. Poly-(amidoamine) (PAMAM) dendrimers have demonstrated the ability to diffuse in the CNS and penetrate neurons, presenting low cytotoxicity and effective delivery of anticancer drugs to the brain [M. Fakhoury et al. 2015]. These nanocarriers can be designed to be small enough to navigate the tight junctions of the BBB and deliver therapeutic agents.In some cases, osmotic agents like mannitol can be used to temporarily disrupt the BBB, enhancing the penetration of large molecules such as antibodies. This approach increases the permeability of the BBB by drawing water out of cells, thereby opening the tight junctions between endothelial cells [S. Liddelow et al. 2017]. Moreover, microcapsules coated with specific proteins or peptides to target the BBB have shown efficacy. For instance, protein-coated microcapsules can cross the BBB and release their therapeutic contents in the brain, targeting inflamed tissues and delivering treatment directly where it is needed [K. Timmis et al. 2020]. In conclusion, while the BBB remains a formidable barrier to central nervous system drug delivery, multiple strategies involving microcapsules and nanotechnology have shown potential to overcome this challenge. By leveraging the physical properties of microcapsules, engineering receptor interactions, and utilizing osmotic agents, researchers can enhance the delivery of therapeutic agents to the brain, offering hope for more effective treatments for neurological diseases.
Fine-grained Assessments: Org 3.0 Rel 5.0 Cov 5.0
Preference: OS-GPT4o. Explanation: OS-GPT4o is better as it provided a list of potential microcapsules that could pass the BBB through various methods, whereas Human is focused on different microorganisms instead, which are less relevant to the topic.)

表内文字对照（数值与原始行列保持不变）：
Question → 问题
Is it possible for microcapsules to cross the blood brain barrier → 微胶囊能否穿过血脑屏障？
Human → 人类
The blood-brain barrier (BBB) is an essential semi-permeable biological barrier that protects the brain by preventing foreign substances from entering → 血脑屏障（BBB）是一种重要的半透性生物屏障，通过阻止外来物质进入来保护大脑
Di Wu et al → 戴武等
This means that even therapeutics cannot properly access the brain as the BBB excludes them as well → 这意味着即使是治疗药物也无法正常进入大脑，因为血脑屏障同样将其排除在外
The tight gap of the semi-permeable barrier only allows lipid-soluble drugs with an average molecular weight lower than → 半透膜之间的紧密间隙仅允许平均分子量低于的脂溶性药物通过
Da through passive diffusion → 通过被动扩散
Nanoparticles are commonly used to deliver therapeutics to the brain by crossing the BBB thanks to their small size → 纳米颗粒因其较小的尺寸，常被用于通过血脑屏障将治疗药物输送至大脑
low toxicity → 低毒性
biocompatibility → 生物相容性
and controllable drug release kinetics → 以及可控制的药物释放动力学
Andrew M Hersh et al → Andrew M Hersh 等
For brain delivery applications → 用于大脑递送应用
nanoparticles between → 纳米颗粒之间
nm are the most effective → 这些方法是最有效的
but the optimal size depends on the type of biomaterial that forms the nanoparticles → 但最佳规模取决于构成纳米颗粒的生物材料类型
Interestingly → 有趣的是
some studies reported that some → 一些研究指出，某些
m bacteria can pass through the BBB → m种细菌能够穿过血脑屏障
which gave the researchers an idea to develop bacteria-mediated drug delivery systems → 这让研究人员有了开发细菌介导的药物输送系统的思路
Other studies also demonstrated the BBB crossing of micron-scale plastic particles using polystyrene (PS) microspheres of size → 其他研究也展示了使用聚苯乙烯（PS）微球作为尺寸为微米级的塑料颗粒时，其能够跨越 BBB 屏障
and → 并且
with the smallest particle reaching the brain within only → 最小的粒子仅在短时间内就到达大脑
hours upon exposure → 暴露时间
Kopatz et al → Kopatz等人
Researchers have developed various methods for improved drug delivery to the brain → 研究人员开发了多种改进大脑药物递送的方法
and one good example is the focused ultrasound technique with microbubbles → 另一个很好的例子是带有微气泡的聚焦超声技术
Lapin et al → Lapin等人
Here → 这里
the rapid oscillation of intravascular microbubbles stimulates the BBB to increase the uptake of nanoparticles and other forms of therapeutics → 血管内微气泡的快速振荡促使血脑屏障增强对纳米颗粒及其他形式治疗药物的吸收
The average diameter of microbubbles is → 微气泡的平均直径为
and they are typically administered via bolus intravenous injection → 它们通常通过连续静脉推注的方式实施
Fine-grained Assessments → 细粒度评估
Org → 组织
Rel → 相关
Cov → Cov
Model (OS-GPT → 模型（OS-GPT）
The blood-brain barrier (BBB) presents a significant challenge for delivering therapeutic agents directly to the central nervous system (CNS) → 血脑屏障对将治疗剂直接递送到中枢神经系统（CNS）提出了重大挑战
However → 然而
various strategies have been developed to enable microcapsules to cross the BBB → 已经开发了多种策略，以使微胶囊能够穿越血脑屏障
making it possible to deliver drugs or therapeutic agents effectively to the brain → 使得将药物或治疗剂有效输送至大脑成为可能
Microcapsules → 微胶囊
particularly those composed of alginate → 尤其是由藻酸盐构成的那些
have demonstrated potential in transporting substances across the BBB → 已证明在跨血脑屏障运输物质方面具有潜力
Studies show that small alginate microcapsules → 研究表明，小型藻胶微胶囊具有良好效果
specifically in the size range of → 特别是在大小范围内
mu m → μ m
can effectively bypass the BBB and deliver therapeutic agents to the brain → 能够有效绕过 BBB，将治疗药物输送至大脑
These microcapsules can pack more tightly together → 这些微胶囊可以更紧密地聚集在一起
increasing the number of cells and the rate of recombinant gene product secretion per volume of microcapsules → 增加微胶囊中的细胞数量以及每体积重组基因产物分泌率
They also display increased mechanical strength → 它们还表现出更高的机械强度
which is crucial for maintaining integrity during and after crossing the BBB → 这对在跨过 BBB 期间及之后保持完整性至关重要
Ross et al → Ross等人
Development of small alginate microcapsules for recombinant gene product delivery to the rodent brain → 开发用于向啮齿动物大脑输送重组基因产物的小海藻酸盐微胶囊
Fakhoury et al → Fakhoury等人
Furthermore → 此外
lipid-based microcapsules have also been explored for BBB penetration → 基于脂质的微胶囊也被用于探索其穿透血脑屏障的能力
Lipid-alginate microcapsules (L-A microcapsules) → 脂质藻酸盐微胶囊（L-A微胶囊）
which combine the properties of both lipids and alginate → 这些材料结合了脂质和藻酸盐的特性
have shown promising results → 已显示出令人满意的结果
These microcapsules not only provide a physical barrier to protect encapsulated cells but also enhance autophagy → 这些微胶囊不仅提供了物理屏障来保护封装细胞，还能促进自噬过程
which promotes cell survival after transplantation into the brain → 该机制有助于细胞在移植到大脑后存活
Studies have demonstrated that L-A microcapsules facilitate the delivery of neural stem cells (NSCs) into ischemic stroke models → 研究表明，L-A微胶囊有助于将神经干细胞（NSCs）输送至缺血性中风模型中
reducing infarct volume and brain edema → 减少梗死体积和脑水肿
and improving neurological outcomes → 并改善神经学预后
Rui Xu et al → 徐瑞等
Engineering of capsid-receptor interactions is another innovative approach → 衣壳-受体相互作用的工程化设计是另一种创新方法
For example → 例如
peptide-modified adeno-associated virus (AAV) capsids can be engineered to interact with specific proteins that are expressed on the BBB → 肽修饰的腺相关病毒衣壳可以被改造，以与血脑屏障上表达的特定蛋白质相互作用
such as LY → 例如 LY
A or LY → A 或 LY
These engineered capsids show enhanced CNS tropism → 这些工程化衣壳表现出增强的中枢神经系统靶向性
enabling the delivery of gene therapies more effectively across the BBB → 使基因疗法的传递在血脑屏障范围内更加有效
Qin Huang et al → 秦黄等
Targeting AAV vectors to the central nervous system by engineering capsid → 通过设计衣壳结构，将 AAV 向量靶向至中枢神经系统
receptor interactions that enable crossing of the blood → 使血液流动得以进行的受体相互作用
brain barrier → 大脑障碍
Additionally → 此外
nanotechnology applications → 纳米技术应用
such as the use of dendrimers → 例如树状大分子的使用
show promise → 展现出巨大潜力
Poly-(amidoamine) (PAMAM) dendrimers have demonstrated the ability to diffuse in the CNS and penetrate neurons → 聚酰胺胺（PAMAM）树状分子具有在中枢神经系统中扩散并穿透神经细胞的能力
presenting low cytotoxicity and effective delivery of anticancer drugs to the brain → 具有低细胞毒性，并能有效将抗癌药物输送至大脑
These nanocarriers can be designed to be small enough to navigate the tight junctions of the BBB and deliver therapeutic agents → 这些纳米载体可以被设计成足够小，以穿过血脑屏障的紧密连接处并传递治疗药物
In some cases → 在某些情况下
osmotic agents like mannitol can be used to temporarily disrupt the BBB → 像甘露醇这样的渗透性智能体可用于暂时破坏血脑屏障
enhancing the penetration of large molecules such as antibodies → 提升抗体等大分子药物的渗透性
This approach increases the permeability of the BBB by drawing water out of cells → 这种方法通过从细胞中抽取水分，提高了血脑屏障的渗透性
thereby opening the tight junctions between endothelial cells → 从而打开内皮细胞之间的紧密连接
Liddelow et al → Liddelow 等
Moreover → 此外
microcapsules coated with specific proteins or peptides to target the BBB have shown efficacy → 涂有特定蛋白质或肽类的微胶囊能够针对血脑屏障发挥作用
For instance → 例如
protein-coated microcapsules can cross the BBB and release their therapeutic contents in the brain → 蛋白质包覆微胶囊能够穿过血脑屏障，并在大脑中释放其治疗成分
targeting inflamed tissues and delivering treatment directly where it is needed → 针对炎症组织，直接在需要处实施治疗
Timmis et al → Timmis 等
In conclusion → 总结
while the BBB remains a formidable barrier to central nervous system drug delivery → 尽管 BBB仍然是中枢神经系统药物递送的巨大障碍
multiple strategies involving microcapsules and nanotechnology have shown potential to overcome this challenge → 涉及微胶囊和纳米技术的多种策略显示出克服这一挑战的潜力
By leveraging the physical properties of microcapsules → 利用微胶囊的物理特性
engineering receptor interactions → 工程受体相互作用
and utilizing osmotic agents → 并利用渗透剂
researchers can enhance the delivery of therapeutic agents to the brain → 研究人员可以提升药物向大脑的输送效果
offering hope for more effective treatments for neurological diseases → 为神经疾病更有效的治疗方法带来希望
Preference → 偏好
OS-GPT → OS-GPT
Explanation → 说明
o is better as it provided a list of potential microcapsules that could pass the BBB through various methods → o方案更优，因为它提供了通过不同方法通过 BBB的潜在微胶囊清单
whereas Human is focused on different microorganisms instead → 而人类智能体则专注于不同的微生物
which are less relevant to the topic → 这些与主题的相关性较低

### openscholar-0541

**English original**

Table 18: Comparison of human and model answers (Biomedicine). In the original evaluation, we randomized the order of models and anonymized the responses to prevent any biases. For this analysis, we substituted the anonymized model IDs with their corresponding actual names.

**中文译文 · 机器初译**

表18：人类与模型答案的对比（生物医学领域）。在原始评估中，我们随机排列了模型顺序，并对回答进行了匿名处理以排除任何偏见。在本分析中，我们将匿名化的模型编号替换为其对应的实际名称。

### openscholar-0542

**English original**

Question: Can you share papers on synthetic data generation, especially those that generate hard reasoning problems?
Human: There is active research focused on synthetically generating high-quality data using large language models. Generating Diverse Instruction-Tuning Data: To overcome the expensive cost of annotating large-scale, diverse instruction-tuning data, recent work explores the effectiveness of using LLMs to generate diverse, high-quality data. For instance, Self-Instruct [Yizhong Wang et al. 2022 - 1]is one of the earlier works that uses LLMs to generate synthetic data—it iteratively starts with a limited seed set of manually written tasks used to guide the overall generation. The model is prompted to generate instructions for new tasks, and then prompted again to generate responses to those instructions [Yizhong Wang et al. 2022 - 2]. This research shows that GPT-3 can generate diverse instruction-tuning data and demonstrates that by fine-tuning GPT-3 on GPT-3-generated synthetic data, the fine-tuned models can further improve performance on diverse benchmarks. GPT-3 Self-Instruct outperforms the original GPT-3 model by a large margin (+33.1%) [Yizhong Wang et al. 2022 - 2]. This inspired many follow-up works, such as Alpaca and Vicuna, which use powerful LLMs to generate high-quality instruction-tuning data [Baolin Peng et al. 2023]. Generating Hard Reasoning Problems Several papers demonstrate the effectiveness of generating questions and answers for hard mathematical reasoning tasks [Ruibo Liu et al. 2024].- WizardMath [Haipeng Luo et al. 2023 - 1]introduces Reinforcement Learning from Evol-Instruct Feedback (RLEIF), which first generates diverse math instruction data through math-specific Evol-Instruct, then trains an instruction reward model (IRM) and a process-supervised reward model. By producing grade-school and challenging math problems and training the Llama-2 models with these reward models, WizardMath achieves state-of-the-art (SOTA) performance [Haipeng Luo et al. 2023 - 2].- MetaMath [L. Yu et al. 2023]bootstraps the questions in MATH and GSM8K by rewriting them in different ways, showing that training Llama-2 on the resulting MetaMath dataset leads to state-of-the-art performance on two popular benchmarks (i.e., GSM8K and MATH).Several works also show the effectiveness of LLM-based synthetic data generation beyond mathematical reasoning. For instance:Self-Taught Reasoner (STaR) [E. Zelikman et al. 2022 - 1]is a simple approach to generating rationales for answering questions. 1) Prompt the LLM with a few rationale examples to generate answers with rationales. 2) If the answers are wrong, generate a rationale given the correct answer. 3) Collect the rationales that result in correct answers. 4) Fine-tune the model on all the rationales that yielded correct answers [E. Zelikman et al. 2022 - 1]. STaR has been shown to be effective at improving the reasoning capabilities of LLMs on commonsense QA, achieving 35% higher performance than the few-shot baseline and improving on a fine-tuned baseline that only predicts answers by 12.5% [E. Zelikman et al. 2022 - 2].
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 2.0
Model (OS-8B): Generating synthetic data with hard reasoning problems is a topic of growing interest in the field of artificial intelligence, particularly in natural language processing and machine learning. Here are some papers that explore this topic: 1. ”Teaching Broad Reasoning Skills for Multi-Step QA by Generating Hard Contexts” [H. Trivedi et al. Teaching Broad Reasoning Skills for Multi-Step QA by Generating Hard Contexts]discusses the idea of using synthetic data generation to create hard reasoning problems. The authors create synthetic contexts for real questions to improve the robustness of language modelsb́road multi-step reasoning skills. 2. ”Going Beyond Nouns With Vision and Language Models Using Synthetic Data” [Paola Cascante-Bonilla et al. Going Beyond Nouns With Vision and Language Models Using Synthetic Data]introduces Synthetic Visual Concepts (SyViC), a million-scale synthetic dataset designed to improve the understanding of visual language concepts and compositional reasoning in Visiona and Language models. They also propose a general Vision and Language fine-tuning strategy leveraging SyViC to achieve improvements in VLC understanding. 3. ”MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs” [Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 1][Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 3]introduces a method for generating diverse and reliable math problems from a small-scale problem-solution dataset and verifies the generated solutions using code-integrated verification. They achieve state-of-the-art performance in five representative mathematical reasoning datasets. 4. GraDA, a graph-generative data augmentation framework, is presented in ”GraDA: Graph Generative Data Augmentation for Commonsense Reasoning” [A. Maharana et al. GraDA: Graph Generative Data Augmentation for Commonsense Reasoning], which synthesizes factual data samples from knowledge graphs for commonsense reasoning datasets. It improves performance on various benchmarks and provides human evaluation of the quality of synthetic datasets in terms of factuality and answerability. 5. ”MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs” [Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 1][Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 2][Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 4]also discusses the use of synthetic data to enhance mathematical reasoning of Large Language Models. (cont.)
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 4.0
Preference: OS-8B. Explanation: Model A (human) only talked about 2-3 papers which barely represents the field. Model B (OS-8B) had much more detail about many more works.

**中文译文 · 机器初译**

Question: Can you share papers on synthetic data generation, especially those that generate hard reasoning problems?
Human: There is active research focused on synthetically generating high-quality data using large language models. Generating Diverse Instruction-Tuning Data: To overcome the expensive cost of annotating large-scale, diverse instruction-tuning data, recent work explores the effectiveness of using LLMs to generate diverse, high-quality data. For instance, Self-Instruct [Yizhong Wang et al. 2022 - 1]is one of the earlier works that uses LLMs to generate synthetic data—it iteratively starts with a limited seed set of manually written tasks used to guide the overall generation. The model is prompted to generate instructions for new tasks, and then prompted again to generate responses to those instructions [Yizhong Wang et al. 2022 - 2]. This research shows that GPT-3 can generate diverse instruction-tuning data and demonstrates that by fine-tuning GPT-3 on GPT-3-generated synthetic data, the fine-tuned models can further improve performance on diverse benchmarks. GPT-3 Self-Instruct outperforms the original GPT-3 model by a large margin (+33.1%) [Yizhong Wang et al. 2022 - 2]. This inspired many follow-up works, such as Alpaca and Vicuna, which use powerful LLMs to generate high-quality instruction-tuning data [Baolin Peng et al. 2023]. Generating Hard Reasoning Problems Several papers demonstrate the effectiveness of generating questions and answers for hard mathematical reasoning tasks [Ruibo Liu et al. 2024].- WizardMath [Haipeng Luo et al. 2023 - 1]introduces Reinforcement Learning from Evol-Instruct Feedback (RLEIF), which first generates diverse math instruction data through math-specific Evol-Instruct, then trains an instruction reward model (IRM) and a process-supervised reward model. By producing grade-school and challenging math problems and training the Llama-2 models with these reward models, WizardMath achieves state-of-the-art (SOTA) performance [Haipeng Luo et al. 2023 - 2].- MetaMath [L. Yu et al. 2023]bootstraps the questions in MATH and GSM8K by rewriting them in different ways, showing that training Llama-2 on the resulting MetaMath dataset leads to state-of-the-art performance on two popular benchmarks (i.e., GSM8K and MATH).Several works also show the effectiveness of LLM-based synthetic data generation beyond mathematical reasoning. For instance:Self-Taught Reasoner (STaR) [E. Zelikman et al. 2022 - 1]is a simple approach to generating rationales for answering questions. 1) Prompt the LLM with a few rationale examples to generate answers with rationales. 2) If the answers are wrong, generate a rationale given the correct answer. 3) Collect the rationales that result in correct answers. 4) Fine-tune the model on all the rationales that yielded correct answers [E. Zelikman et al. 2022 - 1]. STaR has been shown to be effective at improving the reasoning capabilities of LLMs on commonsense QA, achieving 35% higher performance than the few-shot baseline and improving on a fine-tuned baseline that only predicts answers by 12.5% [E. Zelikman et al. 2022 - 2].
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 2.0
Model (OS-8B): Generating synthetic data with hard reasoning problems is a topic of growing interest in the field of artificial intelligence, particularly in natural language processing and machine learning. Here are some papers that explore this topic: 1. ”Teaching Broad Reasoning Skills for Multi-Step QA by Generating Hard Contexts” [H. Trivedi et al. Teaching Broad Reasoning Skills for Multi-Step QA by Generating Hard Contexts]discusses the idea of using synthetic data generation to create hard reasoning problems. The authors create synthetic contexts for real questions to improve the robustness of language modelsb́road multi-step reasoning skills. 2. ”Going Beyond Nouns With Vision and Language Models Using Synthetic Data” [Paola Cascante-Bonilla et al. Going Beyond Nouns With Vision and Language Models Using Synthetic Data]introduces Synthetic Visual Concepts (SyViC), a million-scale synthetic dataset designed to improve the understanding of visual language concepts and compositional reasoning in Visiona and Language models. They also propose a general Vision and Language fine-tuning strategy leveraging SyViC to achieve improvements in VLC understanding. 3. ”MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs” [Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 1][Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 3]introduces a method for generating diverse and reliable math problems from a small-scale problem-solution dataset and verifies the generated solutions using code-integrated verification. They achieve state-of-the-art performance in five representative mathematical reasoning datasets. 4. GraDA, a graph-generative data augmentation framework, is presented in ”GraDA: Graph Generative Data Augmentation for Commonsense Reasoning” [A. Maharana et al. GraDA: Graph Generative Data Augmentation for Commonsense Reasoning], which synthesizes factual data samples from knowledge graphs for commonsense reasoning datasets. It improves performance on various benchmarks and provides human evaluation of the quality of synthetic datasets in terms of factuality and answerability. 5. ”MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs” [Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 1][Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 2][Zimu Lu et al. MathGenie: Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - 4]also discusses the use of synthetic data to enhance mathematical reasoning of Large Language Models. (cont.)
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 4.0
Preference: OS-8B. Explanation: Model A (human) only talked about 2-3 papers which barely represents the field. Model B (OS-8B) had much more detail about many more works.

表内文字对照（数值与原始行列保持不变）：
Question → 问题
Can you share papers on synthetic data generation → 你能分享关于合成数据生成的相关论文吗
especially those that generate hard reasoning problems → 尤其是那些生成困难推理问题的那些
Human → 人类
There is active research focused on synthetically generating high-quality data using large language models → 目前有大量研究致力于利用大语言模型合成生成高质量数据
Generating Diverse Instruction-Tuning Data → 生成多样化的指令调优数据
To overcome the expensive cost of annotating large-scale → 为了克服大规模标注的高昂成本
diverse instruction-tuning data → 多样化的指令调整数据
recent work explores the effectiveness of using LLMs to generate diverse → 近期研究探讨了使用大语言模型生成多样化内容的有效性
high-quality data → 高质量数据
For instance → 例如
Self-Instruct → 自指导
Yizhong Wang et al → 王志忠等
is one of the earlier works that uses LLMs to generate synthetic data → 这是较早的利用大语言模型生成合成数据的研究之一
it iteratively starts with a limited seed set of manually written tasks used to guide the overall generation → 它首先通过有限的手动编写任务集合进行迭代启动，这些任务用于指导整体生成过程
The model is prompted to generate instructions for new tasks → 该模型被提示生成新任务的指令
and then prompted again to generate responses to those instructions → 然后再次被提示生成针对这些指令的回应
This research shows that GPT- → 这项研究表明，GPT-
can generate diverse instruction-tuning data and demonstrates that by fine-tuning GPT- → 能够生成多样化的指令调整数据，并证明通过微调 GPT-
on GPT- → 关于 GPT-
generated synthetic data → 生成的合成数据
the fine-tuned models can further improve performance on diverse benchmarks → 经过微调的模型能够在多种基准测试中进一步提升性能
GPT- → GPT-
Self-Instruct outperforms the original GPT- → 自指导方法优于原始的 GPT-
model by a large margin ( → 以巨大优势领先（
This inspired many follow-up works → 这激发了许多后续研究工作
such as Alpaca and Vicuna → 例如 Alpaca 和 Vicuna
which use powerful LLMs to generate high-quality instruction-tuning data → 这些方法使用强大的大语言模型来生成高质量指令调整数据
Baolin Peng et al → 彭宝林等
Generating Hard Reasoning Problems Several papers demonstrate the effectiveness of generating questions and answers for hard mathematical reasoning tasks → 生成困难推理问题 多篇论文证明了为困难数学推理任务生成问题和答案的有效性
Ruibo Liu et al → 刘瑞波等
WizardMath → WizardMath
Haipeng Luo et al → 罗海鹏等
introduces Reinforcement Learning from Evol-Instruct Feedback (RLEIF) → 介绍了基于进化指令反馈的强化学习（RLEIF）
which first generates diverse math instruction data through math-specific Evol-Instruct → 首先通过数学特定的 Evol-Instruct 生成多样化的数学教学数据
then trains an instruction reward model (IRM) and a process-supervised reward model → 然后训练一个指令奖励模型（IRM）和一个过程监督奖励模型
By producing grade-school and challenging math problems and training the Llama- → 通过生成小学级及具有挑战性的数学题目，并对 Llama-进行训练
models with these reward models → 带有这些奖励模型的模型
WizardMath achieves state-of-the-art (SOTA) performance → WizardMath 实现了最先进的性能表现
MetaMath → MetaMath
Yu et al → Yu等人
bootstraps the questions in MATH and GSM → 在 MATH 和 GSM 中自举问题
K by rewriting them in different ways → 通过以不同方式重写它们来研究 K
showing that training Llama- → 表明训练 Llama-
on the resulting MetaMath dataset leads to state-of-the-art performance on two popular benchmarks (i → 关于由此产生的 MetaMath 数据集在两个热门基准测试上取得了最先进的性能（i
GSM → GSM
K and MATH) → K 与 MATH）
Several works also show the effectiveness of LLM-based synthetic data generation beyond mathematical reasoning → 多项研究也证明了基于大语言模型的合成数据生成技术在数学推理之外的应用效果
Self-Taught Reasoner (STaR) → 自学习推理器 (STaR)
Zelikman et al → Zelikman等人
is a simple approach to generating rationales for answering questions → 这是一种生成回答问题的理由的简单方法
Prompt the LLM with a few rationale examples to generate answers with rationales → 用几个合理的示例提示大语言模型，以生成带有理由的回答
If the answers are wrong → 如果答案错误
generate a rationale given the correct answer → 根据正确答案生成理由
Collect the rationales that result in correct answers → 收集能得出正确答案的理由
Fine-tune the model on all the rationales that yielded correct answers → 针对所有给出正确答案的推理依据对模型进行微调
STaR has been shown to be effective at improving the reasoning capabilities of LLMs on commonsense QA → 研究表明，STaR能够有效提升大语言模型在常识问答任务中的推理能力
achieving → 实现
higher performance than the few-shot baseline and improving on a fine-tuned baseline that only predicts answers by → 性能优于少数样本基准模型，且优于仅能预测答案的微调基准模型
Fine-grained Assessments → 细粒度评估
Org → 组织
Rel → 相关
Cov → Cov
Model (OS- → 模型（操作系统）
Generating synthetic data with hard reasoning problems is a topic of growing interest in the field of artificial intelligence → 利用复杂推理问题生成合成数据是人工智能领域日益受到关注的研究课题
particularly in natural language processing and machine learning → 尤其是在自然语言处理和机器学习领域
Here are some papers that explore this topic → 以下是一些探讨该主题的论文
Teaching Broad Reasoning Skills for Multi-Step QA by Generating Hard Contexts → 通过生成困难上下文来培养多步骤问答场景中的广泛推理能力
Trivedi et al → Trivedi等人
discusses the idea of using synthetic data generation to create hard reasoning problems → 讨论了利用合成数据生成技术来创建困难推理问题的理念
The authors create synthetic contexts for real questions to improve the robustness of language modelsb → 作者为真实问题创建合成上下文，以提升语言模型的鲁棒性
road multi-step reasoning skills → 道路多步推理能力
Going Beyond Nouns With Vision and Language Models Using Synthetic Data → 利用合成数据借助视觉与语言模型超越名词的边界
Paola Cascante-Bonilla et al → Paola Cascante-Bonilla 等
introduces Synthetic Visual Concepts (SyViC) → 介绍了合成视觉概念（SyViC）
a million-scale synthetic dataset designed to improve the understanding of visual language concepts and compositional reasoning in Visiona and Language models → 用于提升 Visiona 和语言模型中视觉语言概念及组合推理能力的百万级合成数据集
They also propose a general Vision and Language fine-tuning strategy leveraging SyViC to achieve improvements in VLC understanding → 他们还提出了一种基于 SyViC 的通用视觉与语言微调策略，以提升 VLC 理解能力
MathGenie → MathGenie
Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs → 通过问题反向翻译生成合成数据以提升大语言模型的数学推理能力
Zimu Lu et al → 陆志模等
Generating Synthetic Data with Question Back-translation for Enhancing Mathematical Reasoning of LLMs - → 通过问题反向翻译生成合成数据，以提升大语言模型的数学推理能力——
introduces a method for generating diverse and reliable math problems from a small-scale problem-solution dataset and verifies the generated solutions using code-integrated verification → 提出了一种从小规模问题-解决方案数据集生成多样化且可靠的数学问题的方法，并使用代码集成验证对生成的解决方案进行验证
They achieve state-of-the-art performance in five representative mathematical reasoning datasets → 它们在五个具有代表性的数学推理数据集上实现了最先进的性能表现
GraDA → GraDA
a graph-generative data augmentation framework → 一种图生成式数据增强框架
is presented in → 体现在中
Graph Generative Data Augmentation for Commonsense Reasoning → 用于常识推理的图生成式数据增强方法
Maharana et al → Maharana等人
which synthesizes factual data samples from knowledge graphs for commonsense reasoning datasets → 该模型从知识图谱中整合事实数据样本，用于常识推理数据集的构建
It improves performance on various benchmarks and provides human evaluation of the quality of synthetic datasets in terms of factuality and answerability → 它在各种基准测试中的表现有所提升，并提供了关于合成数据集在事实性和准确性方面的人类评估结果
also discusses the use of synthetic data to enhance mathematical reasoning of Large Language Models → 还讨论了使用合成数据来增强大语言模型的数学推理能力
cont → 内容
Preference → 偏好
OS- → 操作系统
Explanation → 说明
Model A (human) only talked about → 模型 A（人类）仅讨论了相关内容
papers which barely represents the field → 几乎无法反映该领域的论文
Model B (OS- → 模型 B（操作系统）
B) had much more detail about many more works → B) 对更多作品有更详细的介绍

### openscholar-0543

**English original**

Table 19: Comparison of human and model answers (Computer Science). In the original evaluation, we randomized the order of the models and anonymized the responses to prevent any biases. For this analysis, we have replaced the anonymized model IDs with their actual names.

**中文译文 · 机器初译**

表19：人类与模型答案的对比（计算机科学）。在原始评估中，我们随机化了模型的排序，并对回答进行了匿名处理以排除任何偏见。对于本次分析，我们将匿名处理的模型编号替换为其实际名称。

### openscholar-0544

**English original**

Question: What are the latest works on finetuning an auto-regressive LM for dense passage retrieval? How are their performance compared with bi-directional encoders?
Human: It was traditionally assumed that decoder models would underperform compared to bi-directional autoregressive models, as referenced in [Chankyu Lee et al. 2024 - 3]. However, recent advancements have challenged this notion, demonstrating that finetuned auto-regressive language models (LMs) can indeed surpass the capabilities of bi-directional encoder models in retrieval embedding tasks [Liang Wang et al. 2023 - 1][Parishad BehnamGhader et al. 2024][Niklas Muennighoff et al. 2024 - 1][Chankyu Lee et al. 2024 - 1].One notable example is the E5-Mixtral model [Liang Wang et al. 2023 - 1], which employs a novel approach by generating a diverse set of synthetic data to finetune Mistral, a pre-trained large language model (LLM). This model has shown superior performance over the state-of-the-art (SOTA) bi-directional embedding models of that time, including OpenAIś text-embedding-3-large, Cohere-embed-english-v3.0, and voyage-lite-01-instruct on the MTEB benchmark [Niklas Muennighoff et al. 2022].Another study LLM2Vec [Parishad BehnamGhader et al. 2024] demonstrates the adaptation of a decoder model solely using public data for embedding tasks, which also achieved remarkable results on the MTEB benchmark [Niklas Muennighoff et al. 2022], surpassing other encoder models by a significant margin. This highlights the potential of decoder models when optimized appropriately. Furthermore, the GRIT model [Niklas Muennighoff et al. 2024 - 1] unifies auto-regressive and bi-directional model designs. It incorporates two distinct language modeling heads atop the Transformer layers: one auto-regressive head, designed for generative tasks with a causal attention mask, and another bi-directional head, tailored for embedding tasks. This dual-head approach allows GRIT to leverage the strengths of both modeling techniques. Lastly, the NV-Embed model [Chankyu Lee et al. 2024 - 1] adapts the decoder model architecture to enhance finetuning effectiveness using public datasets. This model not only ranks at the top on the MTEB benchmark [Niklas Muennighoff et al. 2022] but also outperforms all existing baselines on the information retrieval benchmark [Chankyu Lee et al. 2024 - 2], underscoring the robustness and versatility of decoder models in handling complex language tasks.In short, E5-Mixtral [Liang Wang et al. 2023 - 1], LLM2Vec [Parishad BehnamGhader et al. 2024], GRIT [Niklas Muennighoff et al. 2024 - 1], and NV-Embed [Chankyu Lee et al. 2024 - 1] are good representations of the SOTA auto-regressive LMs on retrieval tasks whose performance is superior than traditional bi-directional encoders [Chankyu Lee et al. 2024 - 2][Liang Wang et al. 2023 - 2][Niklas Muennighoff et al. 2024 - 2][Niklas Muennighoff et al. 2022].
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 3.0
Model (OS-8B): Recent works on fine-tuning an auto-regressive language model (LM) for dense passage retrieval have achieved impressive results, outperforming bi-directional encoders in many cases. One approach is to use the auto-regressive LM as a retriever, where the LM is fine-tuned to predict the next word in the passage given the query [Yuxiang Lu et al. ERNIE-Search: Bridging Cross-Encoder with Dual-Encoder via Self On-the-fly Distillation for Dense Passage Retrieval - 2]. Another approach is to use the auto-regressive LM as a generator, where the LM is fine-tuned to generate a passage given the query [Luyu Gao et al. 2021 - 1].One notable work is ERNIE-Search [Yuxiang Lu et al. ERNIE-Search: Bridging Cross-Encoder with Dual-Encoder via Self On-the-fly Distillation for Dense Passage Retrieval - 1], which bridges cross-encoder with dual-encoder via self on-the-fly distillation for dense passage retrieval. ERNIE-Search uses the auto-regressive LM as a retriever and fine-tunes it to optimize the retrieval performance. The results show that ERNIE-Search outperforms the bi-directional encoder-based method, with a ranking loss of 0.0104 vs 0.0167 on the Natural News dataset.Another work is the large language model (LLM) pre-training for dense retrieval [Kun Luo et al. 2024]. The authors fine-tune the LLM as a retriever and demonstrate that it outperforms the bi-directional encoder-based method, with a ranking loss of 0.0085 vs 0.0131 on the Natural News dataset.In comparison, the performance of bi-directional encoders is generally lower than that of auto-regressive LMs. For example, the bi-directional encoder-based method has a ranking loss of 0.0156 on the Natural News dataset [Kun Luo et al. 2024], which is higher than the ranking loss of ERNIE-Search (0.0104) and the LLM-based method (0.0085). However, itś worth noting that the performance of both auto-regressive LMs and bi-directional encoders can be improved with careful fine-tuning and adaptation to the specific task. For example, the use of pre-training objectives such as masked language modeling and next sentence prediction can improve the performance of both types of models [Kun Luo et al. 2024].Recent works have proposed new methods for fine-tuning auto-regressive LMs for dense passage retrieval, such as DPTDR [Zhen-Quan Tang et al. DPTDR: Deep Prompt Tuning for Dense Passage Retrieval] and coCondenser [Luyu Gao et al. 2021 - 2]. These methods have shown promising results and can be used to improve the performance of auto-regressive LMs for dense passage retrieval tasks. Moreover, studies have shown that unsupervised corpus-aware language model pre-training can be effective for dense passage retrieval tasks [Luyu Gao et al. 2021 - 3]. This approach learns to condense information into the dense vector through language model pre-training, and can remove the need for heavy data engineering and large batch training.In addition, simple and effective unsupervised redundancy elimination techniques can be used to compress dense vectors for passage retrieval [Xueguang Ma et al. 2021]. These techniques can improve space efficiency while maintaining good accuracy. Furthermore, HyperLink-induced Pre-training (HLP) can be used to pre-train the dense retriever with the text relevance induced by hyperlink-based topology within Web documents [Jiawei Zhou et al. 2022]. This approach can provide effective relevance signals for large-scale pre-training and can improve the performance of dense passage retrieval tasks.Overall, the use of auto-regressive LMs for dense passage retrieval has shown promising results, and can be a useful approach for improving the performance of dense passage retrieval tasks [Xing Wu et al. 2022].
Fine-grained Assessments: Org 5.0 Rel 5.0 Cov 5.0
Preference: OS-8B. Explanation: I slightly prefer B (OS-8B), as it is more comprehensive in coverage. While A (human) covers more recent work, I think B would be more of interest as the question seems like to come from a novice, and not an expert in the field.

**中文译文 · 机器初译**

Question: What are the latest works on finetuning an auto-regressive LM for dense passage retrieval? How are their performance compared with bi-directional encoders?
Human: It was traditionally assumed that decoder models would underperform compared to bi-directional autoregressive models, as referenced in [Chankyu Lee et al. 2024 - 3]. However, recent advancements have challenged this notion, demonstrating that finetuned auto-regressive language models (LMs) can indeed surpass the capabilities of bi-directional encoder models in retrieval embedding tasks [Liang Wang et al. 2023 - 1][Parishad BehnamGhader et al. 2024][Niklas Muennighoff et al. 2024 - 1][Chankyu Lee et al. 2024 - 1].One notable example is the E5-Mixtral model [Liang Wang et al. 2023 - 1], which employs a novel approach by generating a diverse set of synthetic data to finetune Mistral, a pre-trained large language model (LLM). This model has shown superior performance over the state-of-the-art (SOTA) bi-directional embedding models of that time, including OpenAIś text-embedding-3-large, Cohere-embed-english-v3.0, and voyage-lite-01-instruct on the MTEB benchmark [Niklas Muennighoff et al. 2022].Another study LLM2Vec [Parishad BehnamGhader et al. 2024] demonstrates the adaptation of a decoder model solely using public data for embedding tasks, which also achieved remarkable results on the MTEB benchmark [Niklas Muennighoff et al. 2022], surpassing other encoder models by a significant margin. This highlights the potential of decoder models when optimized appropriately. Furthermore, the GRIT model [Niklas Muennighoff et al. 2024 - 1] unifies auto-regressive and bi-directional model designs. It incorporates two distinct language modeling heads atop the Transformer layers: one auto-regressive head, designed for generative tasks with a causal attention mask, and another bi-directional head, tailored for embedding tasks. This dual-head approach allows GRIT to leverage the strengths of both modeling techniques. Lastly, the NV-Embed model [Chankyu Lee et al. 2024 - 1] adapts the decoder model architecture to enhance finetuning effectiveness using public datasets. This model not only ranks at the top on the MTEB benchmark [Niklas Muennighoff et al. 2022] but also outperforms all existing baselines on the information retrieval benchmark [Chankyu Lee et al. 2024 - 2], underscoring the robustness and versatility of decoder models in handling complex language tasks.In short, E5-Mixtral [Liang Wang et al. 2023 - 1], LLM2Vec [Parishad BehnamGhader et al. 2024], GRIT [Niklas Muennighoff et al. 2024 - 1], and NV-Embed [Chankyu Lee et al. 2024 - 1] are good representations of the SOTA auto-regressive LMs on retrieval tasks whose performance is superior than traditional bi-directional encoders [Chankyu Lee et al. 2024 - 2][Liang Wang et al. 2023 - 2][Niklas Muennighoff et al. 2024 - 2][Niklas Muennighoff et al. 2022].
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 3.0
Model (OS-8B): Recent works on fine-tuning an auto-regressive language model (LM) for dense passage retrieval have achieved impressive results, outperforming bi-directional encoders in many cases. One approach is to use the auto-regressive LM as a retriever, where the LM is fine-tuned to predict the next word in the passage given the query [Yuxiang Lu et al. ERNIE-Search: Bridging Cross-Encoder with Dual-Encoder via Self On-the-fly Distillation for Dense Passage Retrieval - 2]. Another approach is to use the auto-regressive LM as a generator, where the LM is fine-tuned to generate a passage given the query [Luyu Gao et al. 2021 - 1].One notable work is ERNIE-Search [Yuxiang Lu et al. ERNIE-Search: Bridging Cross-Encoder with Dual-Encoder via Self On-the-fly Distillation for Dense Passage Retrieval - 1], which bridges cross-encoder with dual-encoder via self on-the-fly distillation for dense passage retrieval. ERNIE-Search uses the auto-regressive LM as a retriever and fine-tunes it to optimize the retrieval performance. The results show that ERNIE-Search outperforms the bi-directional encoder-based method, with a ranking loss of 0.0104 vs 0.0167 on the Natural News dataset.Another work is the large language model (LLM) pre-training for dense retrieval [Kun Luo et al. 2024]. The authors fine-tune the LLM as a retriever and demonstrate that it outperforms the bi-directional encoder-based method, with a ranking loss of 0.0085 vs 0.0131 on the Natural News dataset.In comparison, the performance of bi-directional encoders is generally lower than that of auto-regressive LMs. For example, the bi-directional encoder-based method has a ranking loss of 0.0156 on the Natural News dataset [Kun Luo et al. 2024], which is higher than the ranking loss of ERNIE-Search (0.0104) and the LLM-based method (0.0085). However, itś worth noting that the performance of both auto-regressive LMs and bi-directional encoders can be improved with careful fine-tuning and adaptation to the specific task. For example, the use of pre-training objectives such as masked language modeling and next sentence prediction can improve the performance of both types of models [Kun Luo et al. 2024].Recent works have proposed new methods for fine-tuning auto-regressive LMs for dense passage retrieval, such as DPTDR [Zhen-Quan Tang et al. DPTDR: Deep Prompt Tuning for Dense Passage Retrieval] and coCondenser [Luyu Gao et al. 2021 - 2]. These methods have shown promising results and can be used to improve the performance of auto-regressive LMs for dense passage retrieval tasks. Moreover, studies have shown that unsupervised corpus-aware language model pre-training can be effective for dense passage retrieval tasks [Luyu Gao et al. 2021 - 3]. This approach learns to condense information into the dense vector through language model pre-training, and can remove the need for heavy data engineering and large batch training.In addition, simple and effective unsupervised redundancy elimination techniques can be used to compress dense vectors for passage retrieval [Xueguang Ma et al. 2021]. These techniques can improve space efficiency while maintaining good accuracy. Furthermore, HyperLink-induced Pre-training (HLP) can be used to pre-train the dense retriever with the text relevance induced by hyperlink-based topology within Web documents [Jiawei Zhou et al. 2022]. This approach can provide effective relevance signals for large-scale pre-training and can improve the performance of dense passage retrieval tasks.Overall, the use of auto-regressive LMs for dense passage retrieval has shown promising results, and can be a useful approach for improving the performance of dense passage retrieval tasks [Xing Wu et al. 2022].
Fine-grained Assessments: Org 5.0 Rel 5.0 Cov 5.0
Preference: OS-8B. Explanation: I slightly prefer B (OS-8B), as it is more comprehensive in coverage. While A (human) covers more recent work, I think B would be more of interest as the question seems like to come from a novice, and not an expert in the field.

表内文字对照（数值与原始行列保持不变）：
Question → 问题
What are the latest works on finetuning an auto-regressive LM for dense passage retrieval → 关于微调自回归大语言模型用于密集段落检索的最新研究有哪些？
How are their performance compared with bi-directional encoders → 他们的性能与双向编码器相比如何
Human → 人类
It was traditionally assumed that decoder models would underperform compared to bi-directional autoregressive models → 传统上认为，解码器模型相比双向自回归模型表现会较差
as referenced in → 如参考文献所述
Chankyu Lee et al → Chankyu Lee 等
However → 然而
recent advancements have challenged this notion → 最近的进展挑战了这一观念
demonstrating that finetuned auto-regressive language models (LMs) can indeed surpass the capabilities of bi-directional encoder models in retrieval embedding tasks → 证明经过微调的自回归语言模型在检索嵌入任务中确实能够超越双向编码模型的能力
Liang Wang et al → 梁王等
Parishad BehnamGhader et al → Parishad BehnamGhader 等
Niklas Muennighoff et al → Niklas Muennighoff 等
One notable example is the E → 一个显著的例子是 E
Mixtral model → Mixtral 模型
which employs a novel approach by generating a diverse set of synthetic data to finetune Mistral → 采用一种创新方法，通过生成多样化的合成数据来微调 Mistral
a pre-trained large language model (LLM) → 一个预训练的大语言模型（LLM）
This model has shown superior performance over the state-of-the-art (SOTA) bi-directional embedding models of that time → 该模型在当时最先进的双向嵌入模型中表现更优
including OpenAI → 包括 OpenAI
text-embedding- → 文本嵌入
large → 大语言模型
Cohere-embed-english-v → 共指-嵌入-英语-视频
and voyage-lite- → 以及轻量级航行系统
instruct on the MTEB benchmark → 针对 MTEB 基准测试进行指导
Another study LLM → 另一项关于大语言模型的研究
Vec → 向量
demonstrates the adaptation of a decoder model solely using public data for embedding tasks → 展示了仅使用公开数据对解码器模型进行嵌入任务适配的过程
which also achieved remarkable results on the MTEB benchmark → 这也在 MTEB 基准测试中取得了显著成果
surpassing other encoder models by a significant margin → 以显著优势超越其他编码模型
This highlights the potential of decoder models when optimized appropriately → 这凸显了经过适当优化的解码器模型的潜力
Furthermore → 此外
the GRIT model → GRIT 模型
unifies auto-regressive and bi-directional model designs → 统一自回归与双向模型设计
It incorporates two distinct language modeling heads atop the Transformer layers → 它将在 Transformer 层之上集成两个不同的语言建模模块
one auto-regressive head → 一个自回归头模块
designed for generative tasks with a causal attention mask → 专为生成任务设计，带有因果注意力掩码
and another bi-directional head → 以及另一个双向头模块
tailored for embedding tasks → 专为嵌入任务量身定制
This dual-head approach allows GRIT to leverage the strengths of both modeling techniques → 这种双头架构方法使得 GRIT 能够充分利用两种建模技术的优势
Lastly → 最后
the NV-Embed model → NV-Embed模型
adapts the decoder model architecture to enhance finetuning effectiveness using public datasets → 调整解码器模型架构，利用公共数据集提升微调效果
This model not only ranks at the top on the MTEB benchmark → 该模型不仅在 MTEB 基准测试中名列前茅
but also outperforms all existing baselines on the information retrieval benchmark → 此外，在信息检索基准测试中也优于所有现有的基线模型
underscoring the robustness and versatility of decoder models in handling complex language tasks → 强调解码器模型在处理复杂语言任务中的稳健性和多功能性
In short → 简而言之
Mixtral → Mixtral
LLM → 大语言模型
GRIT → GRIT
and NV-Embed → 以及 NV-Embed
are good representations of the SOTA auto-regressive LMs on retrieval tasks whose performance is superior than traditional bi-directional encoders → 它们是用于检索任务的大语言模型最新研究成果的良好表征，其性能优于传统的双向编码器
Fine-grained Assessments → 细粒度评估
Org → 组织
Rel → 相关
Cov → Cov
Model (OS- → 模型（操作系统）
Recent works on fine-tuning an auto-regressive language model (LM) for dense passage retrieval have achieved impressive results → 关于对自回归语言模型进行微调以用于密集段落检索的最新研究已取得了令人瞩目的成果
outperforming bi-directional encoders in many cases → 在许多情况下优于双向编码器
One approach is to use the auto-regressive LM as a retriever → 一种方法是将自回归大语言模型用作检索器
where the LM is fine-tuned to predict the next word in the passage given the query → 其中，大语言模型经过微调，能够根据查询预测段落中的下一个单词
Yuxiang Lu et al → 陆宇翔等
ERNIE-Search → ERNIE-Search
Bridging Cross-Encoder with Dual-Encoder via Self On-the-fly Distillation for Dense Passage Retrieval - → 通过自适应即时蒸馏技术实现双编码器间的桥梁连接，以完成密集段落检索任务——
Another approach is to use the auto-regressive LM as a generator → 另一种方法是将自回归大语言模型作为生成器使用
where the LM is fine-tuned to generate a passage given the query → 其中，大语言模型经过微调，能够在给定查询的情况下生成一段文本
Luyu Gao et al → 高露瑜等
One notable work is ERNIE-Search → 一项值得注意的研究是 ERNIE-Search
which bridges cross-encoder with dual-encoder via self on-the-fly distillation for dense passage retrieval → 通过即时自蒸馏技术，该方法实现了跨编码器与双编码器之间的连接，用于密集段落的检索
ERNIE-Search uses the auto-regressive LM as a retriever and fine-tunes it to optimize the retrieval performance → ERNIE-Search 使用自回归大语言模型作为检索器，并对其进行微调以优化检索性能
The results show that ERNIE-Search outperforms the bi-directional encoder-based method → 结果表明，ERNIE-Search优于基于双向编码器的方法
with a ranking loss of → 排名损失为
on the Natural News dataset → 关于 Natural News 数据集
Another work is the large language model (LLM) pre-training for dense retrieval → 另一项研究涉及大语言模型（LLM）的密集检索预训练
Kun Luo et al → 卢坤等
The authors fine-tune the LLM as a retriever and demonstrate that it outperforms the bi-directional encoder-based method → 作者将大语言模型作为检索器进行微调，并证明其性能优于基于双向编码器的方法
In comparison → 相比之下
the performance of bi-directional encoders is generally lower than that of auto-regressive LMs → 双向编码器的性能通常低于自回归LMs
For example → 例如
the bi-directional encoder-based method has a ranking loss of → 基于双向编码器的方法具有排名损失
which is higher than the ranking loss of ERNIE-Search ( → 该值高于 ERNIE-Search 的排序损失
and the LLM-based method ( → 以及基于大语言模型的方法（
worth noting that the performance of both auto-regressive LMs and bi-directional encoders can be improved with careful fine-tuning and adaptation to the specific task → 值得注意的是，通过仔细的微调以及针对特定任务的适配，自回归 LMs 和双向编码器的性能都可以得到提升
the use of pre-training objectives such as masked language modeling and next sentence prediction can improve the performance of both types of models → 采用掩码语言建模和下一句预测等预训练目标，可以提高这两种类型模型的性能
Recent works have proposed new methods for fine-tuning auto-regressive LMs for dense passage retrieval → 近期的研究提出了新的方法，用于微调自回归大语言模型以进行密集段落检索
such as DPTDR → 例如 DPTDR
Zhen-Quan Tang et al → 唐振泉等
DPTDR → DPTDR
Deep Prompt Tuning for Dense Passage Retrieval → 用于密集段落检索的深度提示调整
and coCondenser → 以及共凝聚器
These methods have shown promising results and can be used to improve the performance of auto-regressive LMs for dense passage retrieval tasks → 这些方法已显示出令人满意的效果，可用于提升自回归语言模型在密集文本检索任务中的性能
Moreover → 此外
studies have shown that unsupervised corpus-aware language model pre-training can be effective for dense passage retrieval tasks → 研究表明，无监督的语料库感知语言模型预训练对密集段落检索任务具有有效性
This approach learns to condense information into the dense vector through language model pre-training → 这种方法通过大语言模型预训练，学会将信息压缩到密集向量中
and can remove the need for heavy data engineering and large batch training → 并且可以消除对大量数据工程和大规模批量训练的需求
In addition → 此外
simple and effective unsupervised redundancy elimination techniques can be used to compress dense vectors for passage retrieval → 简单有效的无监督冗余消除技术可用于压缩密集向量以进行文章检索
Xueguang Ma et al → 马雪光等
These techniques can improve space efficiency while maintaining good accuracy → 这些技术可以在保持良好准确性的同时提升空间利用率
HyperLink-induced Pre-training (HLP) can be used to pre-train the dense retriever with the text relevance induced by hyperlink-based topology within Web documents → 基于超链接的大语言模型诱导预训练方法可用于对密集检索器进行预训练，利用网络文档中基于超链接的拓扑结构所引发的文本相关性来实现这一目的
Jiawei Zhou et al → 周佳伟等
This approach can provide effective relevance signals for large-scale pre-training and can improve the performance of dense passage retrieval tasks → 这种方法能够为大规模预训练提供有效的相关性信号，并能够提升密集段落检索任务的性能
Overall → 总体情况
the use of auto-regressive LMs for dense passage retrieval has shown promising results → 使用自回归大语言模型进行密集段落检索已显示出令人满意的效果
and can be a useful approach for improving the performance of dense passage retrieval tasks → 并且可以成为提升密集段落检索任务性能的有效方法
Xing Wu et al → 邢武等
Preference → 偏好
OS- → 操作系统
Explanation → 说明
I slightly prefer B (OS- → 我稍微更倾向 B（操作系统）
as it is more comprehensive in coverage → 因为其覆盖范围更为全面
While A (human) covers more recent work → 当 A（人类）负责涵盖较新的研究时
I think B would be more of interest as the question seems like to come from a novice → 我认为 B 会更有吸引力，因为这个问题似乎出自一个初学者之手
and not an expert in the field → 且并非该领域的专家

### openscholar-0545

**English original**

Table 20: Comparison of human and model answers (Computer Science). In the original evaluation, we randomized the order of the models and anonymized the responses to prevent any biases. For this analysis, we substituted the anonymized model IDs with their corresponding actual names.

**中文译文 · 机器初译**

表20：人类与模型答案的对比（计算机科学）。在原始评估中，我们随机化了模型的排序，并对回复进行了匿名处理以排除任何偏见。对于本次分析，我们将匿名化的模型ID替换为其对应的实际名称。

### openscholar-0546

**English original**

Question: What recent experiments have verified the existence of the Casimir force at the micro- and nanoscale?
Human: The Casimir force, a quantum effect arising from vacuum fluctuations, has garnered significant research interest due to its fundamental nature and implications. This force is particularly intriguing because it manifests as a measurable interaction between surfaces in a vacuum, making it a key subject in the study of quantum effects at microscopic scales. Investigating this unusual force at the micro and nanoscale has significantly advanced precision measurement technologies and provided deeper insights into quantum phenomena.In a 2017 study, the authors fabricated two closely spaced electrodes, each featuring an array of T-shaped protrusions, on a silicon film. The distance between these electrodes could be precisely controlled using an integrated comb actuator connected to one of the electrodes. The force gradient between the electrodes translated into changes in the resonance frequency of the other electrode, which was subsequently measured [Liang Tang et al. 2017 - 1]. The measured force gradients at various distances were in agreement with the Casimir force predicted by simulations and theoretical calculations [Liang Tang et al. 2017 - 2].In a 2019 study, the authors investigated the vibrational modes in two Si3N4 films separated by several hundred nanometers. The films did not come into direct contact, with a vacuum in between, and each film was in contact with thermal reservoirs at different temperatures. The Casimir force between the films coupled their vibrational modes. Consequently, when the distance between the films was relatively small (resulting in a stronger Casimir force), the thermal flow induced by the Casimir force caused deviations in the temperatures of the two vibrational modes from those of their respective thermal reservoirs [K. Fong et al. 2019 - 1]. The observed temperature deviations were consistent with the Casimir force calculations, thereby confirming its presence [K. Fong et al. 2019 - 2].In a more recent article, the authors examined the interactions between two very closely spaced cantilevers under high vacuum, with their motion monitored by fiber interferometers. The gradient of the force between the cantilevers matched the gradient of the Casimir force predicted by theoretical calculations [Zhujing Xu et al. 2021 - 1]. Furthermore, using this platform, the authors demonstrated that by modulating one of the cantilevers, with the modulation frequency and amplitude varying according to a specific pattern, exceptional points and nonreciprocal energy transfer could be achieved [Zhujing Xu et al. 2021 - 2].
Fine-grained Assessments: Org 5.0 Rel 5.0 Cov 5.0
Model (OS-GPT4o): Recent experiments have provided significant evidence for verifying the existence of the Casimir force at both the micro- and nanoscale, harnessing innovative technologies and methodologies to improve accuracy and reliability.One of the pivotal methods involves the use of an atomic force microscope (AFM). In an experiment that replaced the sharp tip of the AFM with a polystyrene sphere about 200 $\mu$ m in diameter, researchers observed the Casimir force between a metallic-coated sphere and a sapphire disk. This experiment achieved extremely high precision, with absolute errors in separation measurements as small as 0.8 nm and force measurements with a relative error of about 1.75% at the shortest separation of 62 nm [G. L. Klimchitskaya et al. 2006]. Another experiment using AFMs measured the Casimir force between an Au-coated sphere and various silicon surfaces. These experiments demonstrated the impact of different charge-carrier densities on Casimir interactions, revealing that the force can vary significantly with the siliconś doping level [G. L. Klimchitskaya et al. 2009 - 2]. In particular, n-type Si doped with phosphorus showed different Casimir force profiles compared to undoped or differently doped silicon, highlighting the materialś charge-carrier concentrationś role in modulating the force. This finding was essential for understanding how electronic properties of materials influence quantum vacuum effects.Another significant method involved the use of micromechanical torsional oscillators. These devices have seen various improvements, allowing researchers to accurately measure the Casimir force between an Au-coated sapphire sphere and an Au-coated polysilicon plate. This setup was notably used to study the force over separations from 0.2 to 8 $\mu$ m, producing results that agreed well with theoretical predictions [G. Bimonte et al. Measurement of the Casimir Force between 0.2 and 8 $\mu$ m: Experimental Procedures and Comparison with Theory - 1][G. L. Klimchitskaya et al. Dark Matter Axions, Non-Newtonian Gravity and Constraints on Them from Recent Measurements of the Casimir Force in the Micrometer Separation Range][G. Bimonte et al. Measurement of the Casimir Force between 0.2 and 8 $\mu$ m: Experimental Procedures and Comparison with Theory - 2]. The dynamic regime of measurement, where the change in the oscillatorś resonant frequency reflects the Casimir force derivative, has also been employed effectively. For instance, experiments by Chan et al. used this setup to measure the Casimir force between a gold-coated sphere and a nanoscale rectangular corrugated silicon surface, illustrating deviations from the proximity force approximation (PFA) [G. L. Klimchitskaya et al. 2009 - 1].Nanostructuring techniques have introduced new possibilities for manipulating and measuring the Casimir force. By creating deep metallic lamellar gratings with sub-100 nm features, it was demonstrated that these structures could significantly suppress the Casimir force beyond theoretical predictions, especially at larger separations [F. Intravaia et al. 2012]. This approach highlights the role of surface topography in modulating quantum vacuum forces. Moreover, differential Casimir force measurements have provided stringent constraints on various theoretical models. These measurements involve comparing the force between an Au-coated sphere and the top and bottom of deep Au-coated trenches concentrically located on a rotating disc. This method not only captures the force signal with high sensitivity but also distinguishes between different theoretical models, particularly the ones factoring in the relaxation properties of conduction electrons [G. L. Klimchitskaya et al. Dark Matter Axions, Non-Newtonian Gravity and Constraints on Them from Recent Measurements of the Casimir Force in the Micrometer Separation Range].**Comparisons and Relative Strengths**When comparing these methods, the use of AFMs with polystyrene spheres provided exceptional precision in force measurements and separation distances, allowing detailed examination of charge-carrier density effects on Casimir interactions [G. L. Klimchitskaya et al. 2009 - 2][G. L. Klimchitskaya et al. 2006].
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 5.0
Preference: Although B (OS-GPT4) list lots of experiments with more details, they are too outdated in the field when the question is asking for recent progress.

**中文译文 · 机器初译**

Question: What recent experiments have verified the existence of the Casimir force at the micro- and nanoscale?
Human: The Casimir force, a quantum effect arising from vacuum fluctuations, has garnered significant research interest due to its fundamental nature and implications. This force is particularly intriguing because it manifests as a measurable interaction between surfaces in a vacuum, making it a key subject in the study of quantum effects at microscopic scales. Investigating this unusual force at the micro and nanoscale has significantly advanced precision measurement technologies and provided deeper insights into quantum phenomena.In a 2017 study, the authors fabricated two closely spaced electrodes, each featuring an array of T-shaped protrusions, on a silicon film. The distance between these electrodes could be precisely controlled using an integrated comb actuator connected to one of the electrodes. The force gradient between the electrodes translated into changes in the resonance frequency of the other electrode, which was subsequently measured [Liang Tang et al. 2017 - 1]. The measured force gradients at various distances were in agreement with the Casimir force predicted by simulations and theoretical calculations [Liang Tang et al. 2017 - 2].In a 2019 study, the authors investigated the vibrational modes in two Si3N4 films separated by several hundred nanometers. The films did not come into direct contact, with a vacuum in between, and each film was in contact with thermal reservoirs at different temperatures. The Casimir force between the films coupled their vibrational modes. Consequently, when the distance between the films was relatively small (resulting in a stronger Casimir force), the thermal flow induced by the Casimir force caused deviations in the temperatures of the two vibrational modes from those of their respective thermal reservoirs [K. Fong et al. 2019 - 1]. The observed temperature deviations were consistent with the Casimir force calculations, thereby confirming its presence [K. Fong et al. 2019 - 2].In a more recent article, the authors examined the interactions between two very closely spaced cantilevers under high vacuum, with their motion monitored by fiber interferometers. The gradient of the force between the cantilevers matched the gradient of the Casimir force predicted by theoretical calculations [Zhujing Xu et al. 2021 - 1]. Furthermore, using this platform, the authors demonstrated that by modulating one of the cantilevers, with the modulation frequency and amplitude varying according to a specific pattern, exceptional points and nonreciprocal energy transfer could be achieved [Zhujing Xu et al. 2021 - 2].
Fine-grained Assessments: Org 5.0 Rel 5.0 Cov 5.0
Model (OS-GPT4o): Recent experiments have provided significant evidence for verifying the existence of the Casimir force at both the micro- and nanoscale, harnessing innovative technologies and methodologies to improve accuracy and reliability.One of the pivotal methods involves the use of an atomic force microscope (AFM). In an experiment that replaced the sharp tip of the AFM with a polystyrene sphere about 200 $\mu$ m in diameter, researchers observed the Casimir force between a metallic-coated sphere and a sapphire disk. This experiment achieved extremely high precision, with absolute errors in separation measurements as small as 0.8 nm and force measurements with a relative error of about 1.75% at the shortest separation of 62 nm [G. L. Klimchitskaya et al. 2006]. Another experiment using AFMs measured the Casimir force between an Au-coated sphere and various silicon surfaces. These experiments demonstrated the impact of different charge-carrier densities on Casimir interactions, revealing that the force can vary significantly with the siliconś doping level [G. L. Klimchitskaya et al. 2009 - 2]. In particular, n-type Si doped with phosphorus showed different Casimir force profiles compared to undoped or differently doped silicon, highlighting the materialś charge-carrier concentrationś role in modulating the force. This finding was essential for understanding how electronic properties of materials influence quantum vacuum effects.Another significant method involved the use of micromechanical torsional oscillators. These devices have seen various improvements, allowing researchers to accurately measure the Casimir force between an Au-coated sapphire sphere and an Au-coated polysilicon plate. This setup was notably used to study the force over separations from 0.2 to 8 $\mu$ m, producing results that agreed well with theoretical predictions [G. Bimonte et al. Measurement of the Casimir Force between 0.2 and 8 $\mu$ m: Experimental Procedures and Comparison with Theory - 1][G. L. Klimchitskaya et al. Dark Matter Axions, Non-Newtonian Gravity and Constraints on Them from Recent Measurements of the Casimir Force in the Micrometer Separation Range][G. Bimonte et al. Measurement of the Casimir Force between 0.2 and 8 $\mu$ m: Experimental Procedures and Comparison with Theory - 2]. The dynamic regime of measurement, where the change in the oscillatorś resonant frequency reflects the Casimir force derivative, has also been employed effectively. For instance, experiments by Chan et al. used this setup to measure the Casimir force between a gold-coated sphere and a nanoscale rectangular corrugated silicon surface, illustrating deviations from the proximity force approximation (PFA) [G. L. Klimchitskaya et al. 2009 - 1].Nanostructuring techniques have introduced new possibilities for manipulating and measuring the Casimir force. By creating deep metallic lamellar gratings with sub-100 nm features, it was demonstrated that these structures could significantly suppress the Casimir force beyond theoretical predictions, especially at larger separations [F. Intravaia et al. 2012]. This approach highlights the role of surface topography in modulating quantum vacuum forces. Moreover, differential Casimir force measurements have provided stringent constraints on various theoretical models. These measurements involve comparing the force between an Au-coated sphere and the top and bottom of deep Au-coated trenches concentrically located on a rotating disc. This method not only captures the force signal with high sensitivity but also distinguishes between different theoretical models, particularly the ones factoring in the relaxation properties of conduction electrons [G. L. Klimchitskaya et al. Dark Matter Axions, Non-Newtonian Gravity and Constraints on Them from Recent Measurements of the Casimir Force in the Micrometer Separation Range].**Comparisons and Relative Strengths**When comparing these methods, the use of AFMs with polystyrene spheres provided exceptional precision in force measurements and separation distances, allowing detailed examination of charge-carrier density effects on Casimir interactions [G. L. Klimchitskaya et al. 2009 - 2][G. L. Klimchitskaya et al. 2006].
Fine-grained Assessments: Org 5.0 Rel 4.0 Cov 5.0
Preference: Although B (OS-GPT4) list lots of experiments with more details, they are too outdated in the field when the question is asking for recent progress.

表内文字对照（数值与原始行列保持不变）：
Question → 问题
What recent experiments have verified the existence of the Casimir force at the micro- and nanoscale → 哪些近期实验证实了卡西米尔力在微观和纳米尺度上的存在
Human → 人类
The Casimir force → 卡西米尔力
a quantum effect arising from vacuum fluctuations → 由真空涨落产生的量子效应
has garnered significant research interest due to its fundamental nature and implications → 由于其基础性质与重要意义，该领域已吸引了大量的研究兴趣
This force is particularly intriguing because it manifests as a measurable interaction between surfaces in a vacuum → 这种力特别引人关注，因为它表现为真空中表面之间的可测量相互作用
making it a key subject in the study of quantum effects at microscopic scales → 使其成为研究微观尺度量子效应的重要课题
Investigating this unusual force at the micro and nanoscale has significantly advanced precision measurement technologies and provided deeper insights into quantum phenomena → 对微观和纳米尺度上这种异常力的研究显著推动了精密测量技术的发展，并提供了对量子现象更深入的理解
In a → 在一项研究中
study → 研究
the authors fabricated two closely spaced electrodes → 作者制造了两个间距很近的电极
each featuring an array of T-shaped protrusions → 每个都包含一组T形凸起结构
on a silicon film → 在硅薄膜上
The distance between these electrodes could be precisely controlled using an integrated comb actuator connected to one of the electrodes → 这些电极之间的距离可以通过连接到一个电极的集成梳状执行器进行精确控制
The force gradient between the electrodes translated into changes in the resonance frequency of the other electrode → 电极之间的力梯度转化为另一电极的共振频率变化
which was subsequently measured → 随后对其进行了测量
Liang Tang et al → 梁唐等
The measured force gradients at various distances were in agreement with the Casimir force predicted by simulations and theoretical calculations → 不同距离下的测量力梯度与模拟及理论计算所预测的卡西米尔力一致
the authors investigated the vibrational modes in two Si → 作者们研究了两种硅材料中的振动模式
films separated by several hundred nanometers → 相隔数百纳米的薄膜
The films did not come into direct contact → 这些电影没有发生直接接触
with a vacuum in between → 处于中间状态的真空状态
and each film was in contact with thermal reservoirs at different temperatures → 且每一部电影都与不同温度的热储存器发生了接触
The Casimir force between the films coupled their vibrational modes → 薄膜之间的卡西米尔力耦合了它们的振动模式
Consequently → 因此
when the distance between the films was relatively small (resulting in a stronger Casimir force) → 当薄膜之间的距离相对较小时（导致更强的卡西米尔力）
the thermal flow induced by the Casimir force caused deviations in the temperatures of the two vibrational modes from those of their respective thermal reservoirs → 卡西米尔力引起的热流导致两种振动模式的温度与各自热库的温度产生偏差
Fong et al → Fong等人
The observed temperature deviations were consistent with the Casimir force calculations → 观察到的温度偏差与卡西米尔力计算结果一致
thereby confirming its presence → 从而确认其存在
In a more recent article → 在一篇较新的文章中
the authors examined the interactions between two very closely spaced cantilevers under high vacuum → 作者研究了高真空环境下两个间距极近的悬臂结构之间的相互作用
with their motion monitored by fiber interferometers → 通过光纤干涉仪监测其运动
The gradient of the force between the cantilevers matched the gradient of the Casimir force predicted by theoretical calculations → 悬臂结构之间力的梯度与理论计算所预测的卡西米尔力梯度一致
Zhujing Xu et al → 朱静 等
Furthermore → 此外
using this platform → 使用该平台
the authors demonstrated that by modulating one of the cantilevers → 作者们证明，通过调节其中一个悬臂结构可以实现相关效果
with the modulation frequency and amplitude varying according to a specific pattern → 通过根据特定模式变化调制频率与幅度
exceptional points and nonreciprocal energy transfer could be achieved → 可以实现特殊的点状现象以及非互易能量传递
Fine-grained Assessments → 细粒度评估
Org → 组织
Rel → 相关
Cov → Cov
Model (OS-GPT → 模型（OS-GPT）
Recent experiments have provided significant evidence for verifying the existence of the Casimir force at both the micro- and nanoscale → 最近的实验为验证卡西米尔力在微观和纳米尺度上的存在提供了重要的证据
harnessing innovative technologies and methodologies to improve accuracy and reliability → 利用创新技术与方法提升准确性和可靠性
One of the pivotal methods involves the use of an atomic force microscope (AFM) → 其中一种关键方法涉及使用原子力显微镜（AFM）
In an experiment that replaced the sharp tip of the AFM with a polystyrene sphere about → 在一项实验中，用一个聚苯乙烯球体替代了 AFM 的尖锐尖端
m in diameter → 直径为 m
researchers observed the Casimir force between a metallic-coated sphere and a sapphire disk → 研究人员观察了金属涂层球体与蓝宝石圆盘之间的卡西米尔力
This experiment achieved extremely high precision → 该实验实现了极高的精确度
with absolute errors in separation measurements as small as → 分离测量绝对误差小至
nm and force measurements with a relative error of about → 相对误差约为的纳米与力测量
at the shortest separation of → 在最短的间隔下
Klimchitskaya et al → Klimchitskaya 等
Another experiment using AFMs measured the Casimir force between an Au-coated sphere and various silicon surfaces → 另一项使用 AFM 的实验测量了镀金球体与各种硅表面之间的卡西米尔力
These experiments demonstrated the impact of different charge-carrier densities on Casimir interactions → 这些实验展示了不同电荷载体密度对卡西米尔相互作用的影响
revealing that the force can vary significantly with the silicon → 表明该力会随着硅材质的不同而显著变化
doping level → 兴奋剂使用水平
In particular → 特别是
n-type Si doped with phosphorus showed different Casimir force profiles compared to undoped or differently doped silicon → 掺磷的n型硅与未掺杂或不同掺杂的硅相比，表现出不同的卡西米尔力分布特征
highlighting the material → 突出显示材料
charge-carrier concentration → 电荷载体浓度
role in modulating the force → 在调节力方面的作用
This finding was essential for understanding how electronic properties of materials influence quantum vacuum effects → 这一发现对于理解材料的电子性质如何影响量子真空效应至关重要
Another significant method involved the use of micromechanical torsional oscillators → 另一种重要方法涉及使用微机械扭转振荡器
These devices have seen various improvements → 这些设备已经经历了多种改进
allowing researchers to accurately measure the Casimir force between an Au-coated sapphire sphere and an Au-coated polysilicon plate → 使研究人员能够准确测量镀金蓝宝石球体与镀金多硅板之间的卡西米尔力
This setup was notably used to study the force over separations from → 这种设置被专门用于研究距离变化下的力现象
producing results that agreed well with theoretical predictions → 生成与理论预测高度一致的结果
Bimonte et al → Bimonte等人
Measurement of the Casimir Force between → 卡西米尔力测量的方法
and → 并且
Experimental Procedures and Comparison with Theory - → 实验步骤与理论对比——
Dark Matter Axions → 暗物质轴子
Non-Newtonian Gravity and Constraints on Them from Recent Measurements of the Casimir Force in the Micrometer Separation Range → 非牛顿流体重力及其在微米级间距卡西米尔力测量中的限制
The dynamic regime of measurement → 测量的动态机制
where the change in the oscillator → 其中振荡器的变化
resonant frequency reflects the Casimir force derivative → 共振频率反映了卡西米尔力导数
has also been employed effectively → 也已被有效应用
For instance → 例如
experiments by Chan et al → Chan等人的实验
used this setup to measure the Casimir force between a gold-coated sphere and a nanoscale rectangular corrugated silicon surface → 使用这种设置来测量镀金球体与纳米级矩形波纹硅表面之间的卡西米尔力
illustrating deviations from the proximity force approximation (PFA) → 说明与邻近力近似（PFA）的偏差情况
Nanostructuring techniques have introduced new possibilities for manipulating and measuring the Casimir force → 纳米结构化技术为操控和测量卡西米尔力带来了新的可能性
By creating deep metallic lamellar gratings with sub- → 通过制造具有亚级结构的深层金属层状光栅
nm features → 纳米特征
it was demonstrated that these structures could significantly suppress the Casimir force beyond theoretical predictions → 已证明这些结构能够显著抑制卡西米尔力，超出理论预测范围
especially at larger separations → 尤其是在较大的间隔情况下
Intravaia et al → Intravaia 等
This approach highlights the role of surface topography in modulating quantum vacuum forces → 这种方法强调了表面拓扑结构在调节量子真空力方面的作用
Moreover → 此外
differential Casimir force measurements have provided stringent constraints on various theoretical models → 差异型卡西米尔力测量为各种理论模型提供了严格的约束条件
These measurements involve comparing the force between an Au-coated sphere and the top and bottom of deep Au-coated trenches concentrically located on a rotating disc → 这些测量涉及对镀Au球体与旋转盘上同心排列的镀深Au沟槽的上下表面之间的力进行比较
This method not only captures the force signal with high sensitivity but also distinguishes between different theoretical models → 该方法不仅能够以高灵敏度捕捉力信号，还能区分不同的理论模型
particularly the ones factoring in the relaxation properties of conduction electrons → 尤其是那些考虑了传导电子弛豫特性的部分
Comparisons and Relative Strengths → 比较与相对优势
When comparing these methods → 在比较这些方法时
the use of AFMs with polystyrene spheres provided exceptional precision in force measurements and separation distances → 使用AFM与聚苯乙烯球体进行测量，在力值和分离距离方面实现了极高的精度
allowing detailed examination of charge-carrier density effects on Casimir interactions → 允许对电荷载体密度对卡西米尔相互作用的影响进行详细研究
Preference → 偏好
Although B (OS-GPT → 尽管 B (OS-GPT
list lots of experiments with more details → 列出大量实验并提供更多细节
they are too outdated in the field when the question is asking for recent progress → 在探讨最新进展的问题下，这些内容在该领域已经过时了

### openscholar-0547

**English original**

Table 21: Comparison of human and model answers (Photonics). In the original evaluation, we randomized the order of the models and anonymized the responses to prevent any biases. For this analysis, we have replaced the anonymized model IDs with their actual names.

**中文译文 · 机器初译**

表21：人类与模型答案的对比（光子学领域）。在原始评估中，我们随机化了模型的排序，并对回答进行了匿名处理以排除任何偏见。对于本次分析，我们将匿名化的模型编号替换为其实际名称。

### openscholar-0548

**English original**

Appendix E Examples of ScholarQABench

**中文译文 · 机器初译**

附录 E  scholarQABench 示例

### openscholar-0549

**English original**

In this section, we show example instances included in ScholarQABench .

**中文译文 · 机器初译**

在本节中，我们将展示包含在 ScholarQABench 中的示例实例。

### openscholar-0550

**English original**

E.1 Single-paper Tasks

**中文译文 · 机器初译**

E.1 单篇论文任务

### openscholar-0551

**English original**

Figure 15 shows examples from single-paper tasks.

**中文译文 · 机器初译**

图15展示了单篇论文任务中的示例。

### openscholar-0552

**English original**

Figure 15: Single-task examples in ScholarQABench .

**中文译文 · 机器初译**

图15：ScholarQABench中的单任务示例。

### openscholar-0553

**English original**

E.2 ScholarQA -CS

**中文译文 · 机器初译**

E.2 ScholarQA -CS

### openscholar-0554

**English original**

Table 22 shows an example from ScholarQA-CS .

**中文译文 · 机器初译**

表22展示了来自ScholarQA-CS的一个示例。

### openscholar-0555

**English original**

Question: What publicly available datasets are typically used for evaluating type inference systems in Python?
Most Important: • Near the beginning, the answer should briefly define what is the goal of using a type inference system for programming languages in general. • The answer should emphasize on the importance of an automatic type inference system for Python. • The answer should discuss the need for a unified approach for evaluating different type inference systems and mention several evaluation metrics, including exact matches, report of missing types, accuracy, etc. • The answer should enumerate publicly available datasets used for evaluating type inference systems in Python and provide a brief description for each of them. Nice to have: • The answer could explain different categories of methods for type inference in Python such as rule-based and ML-based approaches.

**中文译文 · 机器初译**

Question: What publicly available datasets are typically used for evaluating type inference systems in Python?
Most Important: • Near the beginning, the answer should briefly define what is the goal of using a type inference system for programming languages in general. • The answer should emphasize on the importance of an automatic type inference system for Python. • The answer should discuss the need for a unified approach for evaluating different type inference systems and mention several evaluation metrics, including exact matches, report of missing types, accuracy, etc. • The answer should enumerate publicly available datasets used for evaluating type inference systems in Python and provide a brief description for each of them. Nice to have: • The answer could explain different categories of methods for type inference in Python such as rule-based and ML-based approaches.

表内文字对照（数值与原始行列保持不变）：
Question → 问题
What publicly available datasets are typically used for evaluating type inference systems in Python → 通常用于评估 Python 类型推断系统的公开数据集有哪些
Most Important → 最重要的
Near the beginning → 接近开头
the answer should briefly define what is the goal of using a type inference system for programming languages in general → 该回答应简要说明在编程语言中使用类型推断系统的总体目标是什么
The answer should emphasize on the importance of an automatic type inference system for Python → 该回答应强调自动类型推断系统对 Python 的重要性
The answer should discuss the need for a unified approach for evaluating different type inference systems and mention several evaluation metrics → 该回答应探讨针对不同类型推理系统进行评估的统一方法的必要性，并提及若干评估指标
including exact matches → 包括完全匹配项
report of missing types → 缺失类型报告
accuracy → 准确率
etc → 等等
The answer should enumerate publicly available datasets used for evaluating type inference systems in Python and provide a brief description for each of them → 答案应列出用于评估 Python 类型推断系统的公开可用数据集，并对每个数据集进行简要描述
Nice to have → 很高兴拥有
The answer could explain different categories of methods for type inference in Python such as rule-based and ML-based approaches → 该答案可以解释 Python 中类型推断的多种方法类别，例如基于规则的方法与基于机器学习的方法

### openscholar-0556

**English original**

(a) Example question and corresponding key ingredients annotation from ScholarQA-CS .

**中文译文 · 机器初译**

(a) 来自 ScholarQA-CS 的示例问题及对应的关键要素注释。

### openscholar-0557

**English original**

Most Important: The answer should enumerate publicly available datasets used for evaluating type inference systems in Python and provide a brief description for each of them.
Supporting quotes • “ 1. ManyTypes4Py : – Description : ManyTypes4Py is a large Python dataset for machine learning-based type inference. It contains 5,382 Python projects with over 869,000 type annotations. The dataset is split into training, validation, and test sets by files to facilitate the training and evaluation of machine learning models. – Features : The dataset includes a lightweight static analyzer pipeline to extract type information from abstract syntax trees (ASTs) and store the results in JSON-formatted files.” • “ 2. TypeEvalPy : – Description : TypeEvalPy is a micro-benchmarking framework for evaluating type inference tools. It contains 154 code snippets with 845 type annotations across 18 categories targeting various Python features. – Features : The framework manages the execution of containerized tools, transforms inferred types into a standardized format, and produces meaningful metrics for assessment.” • “ 3. BigQuery Public Datasets : – Description : BigQuery provides a range of public datasets that can be used for various purposes, including type inference. These datasets are accessible through the Google Cloud Public Dataset Program and can be queried using SQL or GoogleSQL. – Features : The datasets include a variety of data sources, such as weather information, GitHub repository data, and Wikipedia revision history.” • “The Typilus model [8] is accompanied by a dataset that contains 600 Python projects. Moreover, the source code files of Typilus’ dataset are converted to graph representations that are only suitable for training the Typilus model.” • “Raychev et al. [16] published the Python-150K dataset in 2016, which contains 8,422 Python projects.” 2104.04706 (arxiv.org) • “Python-150K dataset [16] is not collected solely for the ML-based type inference task, meaning that a large number of projects in the dataset may not have type annotations at all, especially given the time that the dataset was created.” 2104.04706 (arxiv.org) • “Our main dataset, BetterTypes4Py, is constructed by selecting a high-quality subset from the ManyTypes4Py dataset (Mir et al., 2021), which was used to train Type4Py.” 2303.09564 (arxiv.org) • “InferTypes4Py, a test set derived from the source code of Typilus, Type4Py, and our own tool, none of which were used as CodeT5’s (pre-)training data” 2303.09564 (arxiv.org)

**中文译文 · 机器初译**

Most Important: The answer should enumerate publicly available datasets used for evaluating type inference systems in Python and provide a brief description for each of them.
Supporting quotes • “ 1. ManyTypes4Py : – Description : ManyTypes4Py is a large Python dataset for machine learning-based type inference. It contains 5,382 Python projects with over 869,000 type annotations. The dataset is split into training, validation, and test sets by files to facilitate the training and evaluation of machine learning models. – Features : The dataset includes a lightweight static analyzer pipeline to extract type information from abstract syntax trees (ASTs) and store the results in JSON-formatted files.” • “ 2. TypeEvalPy : – Description : TypeEvalPy is a micro-benchmarking framework for evaluating type inference tools. It contains 154 code snippets with 845 type annotations across 18 categories targeting various Python features. – Features : The framework manages the execution of containerized tools, transforms inferred types into a standardized format, and produces meaningful metrics for assessment.” • “ 3. BigQuery Public Datasets : – Description : BigQuery provides a range of public datasets that can be used for various purposes, including type inference. These datasets are accessible through the Google Cloud Public Dataset Program and can be queried using SQL or GoogleSQL. – Features : The datasets include a variety of data sources, such as weather information, GitHub repository data, and Wikipedia revision history.” • “The Typilus model [8] is accompanied by a dataset that contains 600 Python projects. Moreover, the source code files of Typilus’ dataset are converted to graph representations that are only suitable for training the Typilus model.” • “Raychev et al. [16] published the Python-150K dataset in 2016, which contains 8,422 Python projects.” 2104.04706 (arxiv.org) • “Python-150K dataset [16] is not collected solely for the ML-based type inference task, meaning that a large number of projects in the dataset may not have type annotations at all, especially given the time that the dataset was created.” 2104.04706 (arxiv.org) • “Our main dataset, BetterTypes4Py, is constructed by selecting a high-quality subset from the ManyTypes4Py dataset (Mir et al., 2021), which was used to train Type4Py.” 2303.09564 (arxiv.org) • “InferTypes4Py, a test set derived from the source code of Typilus, Type4Py, and our own tool, none of which were used as CodeT5’s (pre-)training data” 2303.09564 (arxiv.org)

表内文字对照（数值与原始行列保持不变）：
Most Important → 最重要的
The answer should enumerate publicly available datasets used for evaluating type inference systems in Python and provide a brief description for each of them → 答案应列出用于评估 Python 类型推断系统的公开可用数据集，并对每个数据集进行简要描述
Supporting quotes → 支持性引文
ManyTypes → 多种类型
Description → 描述
Py is a large Python dataset for machine learning-based type inference → Py 是一个用于基于机器学习的类型推断的大规模 Python 数据集
It contains → 它包含
Python projects with over → 包含超过……的 Python 项目
type annotations → 类型注解
The dataset is split into training → 该数据集被分为训练集和测试集
validation → 验证
and test sets by files to facilitate the training and evaluation of machine learning models → 通过文件形式对测试集进行划分，以方便机器学习模型的训练与评估
Features → 特征
The dataset includes a lightweight static analyzer pipeline to extract type information from abstract syntax trees (ASTs) and store the results in JSON-formatted files → 该数据集包含了一个轻量级的静态分析器管道，用于从抽象语法树（AST）中提取类型信息，并将结果存储为 JSON 格式的文件
TypeEvalPy → TypeEvalPy
TypeEvalPy is a micro-benchmarking framework for evaluating type inference tools → TypeEvalPy 是一个用于评估类型推理工具的微基准测试框架
code snippets with → 代码片段
type annotations across → 类型注解跨
categories targeting various Python features → 针对不同 Python 特性的分类
The framework manages the execution of containerized tools → 该框架管理容器化工具的执行
transforms inferred types into a standardized format → 将推断出的类型转换为标准化格式
and produces meaningful metrics for assessment → 并生成用于评估的有意义指标
BigQuery Public Datasets → BigQuery 公共数据集
BigQuery provides a range of public datasets that can be used for various purposes → BigQuery 提供了一系列公共数据集，可用于多种用途
including type inference → 包括类型推断
These datasets are accessible through the Google Cloud Public Dataset Program and can be queried using SQL or GoogleSQL → 这些数据集可通过 Google Cloud 公共数据集项目获取，并可使用 SQL 或 GoogleSQL 进行查询。
The datasets include a variety of data sources → 这些数据集包含多种数据来源
such as weather information → 例如天气信息
GitHub repository data → GitHub 仓库数据
and Wikipedia revision history → 以及维基百科的修订历史
The Typilus model → Typilus模型
is accompanied by a dataset that contains → 伴随一个包含数据的数据集
Python projects → Python 项目
Moreover → 此外
the source code files of Typilus → Typilus 的源代码文件
dataset are converted to graph representations that are only suitable for training the Typilus model → 数据集被转换为图表示形式，这些形式仅适用于训练 Typilus 模型
Raychev et al → Raychev等人
published the Python- → 发表了 Python-
K dataset in → K数据集
which contains → 包含…的内容
arxiv → arxiv
org) → （组织）
Python- → Python-
K dataset → K数据集
is not collected solely for the ML-based type inference task → 并非仅为了基于机器学习的类型推断任务而收集
meaning that a large number of projects in the dataset may not have type annotations at all → 这意味着数据集中的大量项目可能根本没有类型注解
especially given the time that the dataset was created → 尤其是考虑到该数据集的创建时间
Our main dataset → 我们的主要数据集
BetterTypes → 更好的类型
is constructed by selecting a high-quality subset from the ManyTypes → 通过从 ManyTypes 中选择高质量子集来构建
Py dataset (Mir et al → Py数据集（Mir等）
which was used to train Type → 用于训练 Type 的模型
InferTypes → 推断类型
a test set derived from the source code of Typilus → 来自 Typilus 源代码的测试集
Type → 类型
and our own tool → 以及我们自己的工具
none of which were used as CodeT → 其中没有任何一项被用作 CodeT
s (pre-)training data → s（预）训练数据

### openscholar-0558

**English original**

(b) Supporting quotes for one of the ‘Most Important’ key ingredients, as sourced from a combination of scholarly literature review and the source document provided to annotators.

**中文译文 · 机器初译**

(b) 针对“最重要的”关键要素之一所引用的支持性引文，这些引文来自学术文献综述与提供给注释者的原始文件的组合。

### openscholar-0559

**English original**

Table 22: Annotation example from ScholarQA-CS with associated key ingredients and supporting quotes. We use the ingredients and quotes as rubrics for evaluating Scholarly QA systems.

**中文译文 · 机器初译**

表22：来自 ScholarQA-CS的标注示例，以及相关的关键要素和支持性引文。我们将这些要素和引文作为评估学术问答系统的评分标准。

### openscholar-0560

**English original**

E.3 ScholarQA-Bio

**中文译文 · 机器初译**

E.3 ScholarQA-Bio

### openscholar-0561

**English original**

Table 23 shows several expert-annotated biomedical queries, along with the papers provided to the annotators for inspiration.

**中文译文 · 机器初译**

表23展示了几条由专家标注的生物医学查询，以及提供给标注人的相关文献以供参考。

### openscholar-0562

**English original**

Question: What are different types of GLP-1 analogs targeted for diabetes treatment?
Inspiring Paper: Beloqui et al. 2024. Gut hormone stimulation as a therapeutic approach in oral peptide delivery
In this contribution to the Orations - New Horizons of the Journal of Controlled Release, I discuss the research that we have conducted on gut hormone stimulation as a therapeutic strategy in oral peptide delivery. One of the greatest challenges in oral drug delivery involves the development of new drug delivery systems that enable the absorption of therapeutic peptides into the systemic circulation at therapeutically relevant concentrations. This scenario is especially challenging in the treatment of chronic diseases (such as type 2 diabetes mellitus), wherein daily injections are often needed. However, for certain peptides, there may be an alternative in drug delivery to meet the need for increased peptide bioavailability; this is the case for gut hormone mimetics (including glucagon-like peptide (GLP)-1 or GLP-2). One plausible alternative for improved oral delivery of these peptides is the co-stimulation of the endogenous secretion of the hormone to reach therapeutic levels of the peptide. This oration will be focused on studies conducted on the stimulation of gut hormones secreted from enteroendocrine L cells in the treatment of gastrointestinal disorders, including a critical discussion of the limitations and future perspectives of implementing this approach in the clinical setting.
Question: What are the ways to prevent mass transport of analytes to improve the accuracy of biosensors?
Inspiring Paper: Awawdeh et al. 2024. Enhancing the performance of porous silicon biosensors: the interplay of nanostructure design and microfluidic integration
This work presents the development and design of aptasensor employing porous silicon (PSi) Fabry‒Pérot thin films that are suitable for use as optical transducers for the detection of lactoferrin (LF), which is a protein biomarker secreted at elevated levels during gastrointestinal (GI) inflammatory disorders such as inflammatory bowel disease and chronic pancreatitis. To overcome the primary limitation associated with PSi biosensors—namely, their relatively poor sensitivity due to issues related to complex mass transfer phenomena and reaction kinetics—we employed two strategic approaches: First, we sought to optimize the porous nanostructure with respect to factors including layer thickness, pore diameter, and capture probe density. Second, we leveraged convection properties by integrating the resulting biosensor into a 3D-printed microfluidic system that also had one of two different micromixer architectures (i.e., staggered herringbone micromixers or microimpellers) embedded. We demonstrated that tailoring the PSi aptasensor significantly improved its performance, achieving a limit of detection (LOD) of 50M—which is $>1$ order of magnitude lower than that achieved using previously-developed biosensors of this type. Moreover, integration into microfluidic systems that incorporated passive and active micromixers further enhanced the aptasensor’s sensitivity, achieving an additional reduction in the LOD by yet another order of magnitude. These advancements demonstrate the potential of combining PSi-based optical transducers with microfluidic technology to create sensitive label-free biosensing platforms for the detection of GI inflammatory biomarkers.
Question: How does CRISPR/Cas9 compare to other gene-editing technologies in terms of efficiency and precision?
Inspiring Paper: Sajeesh et al. 2006. CRISPR/Cas9 gene-editing: Research technologies, clinical applications and ethical considerations
Gene therapy carries the potential to treat more than 10,000 human monogenic diseases and benefit an even greater number of complex polygenic conditions. The repurposing of CRISPR/Cas9, an ancient bacterial immune defense system, into a gene-editing technology has armed researchers with a revolutionary tool for gene therapy. However, as the breadth of research and clinical applications of this technology continues to expand, outstanding technical challenges and ethical considerations will need to be addressed before clinical applications become commonplace. Here, we review CRISPR/Cas9 technology and discuss its benefits and limitations in research and the clinical context, as well as ethical considerations surrounding the use of CRISPR gene editing.

**中文译文 · 机器初译**

Question: What are different types of GLP-1 analogs targeted for diabetes treatment?
Inspiring Paper: Beloqui et al. 2024. Gut hormone stimulation as a therapeutic approach in oral peptide delivery
In this contribution to the Orations - New Horizons of the Journal of Controlled Release, I discuss the research that we have conducted on gut hormone stimulation as a therapeutic strategy in oral peptide delivery. One of the greatest challenges in oral drug delivery involves the development of new drug delivery systems that enable the absorption of therapeutic peptides into the systemic circulation at therapeutically relevant concentrations. This scenario is especially challenging in the treatment of chronic diseases (such as type 2 diabetes mellitus), wherein daily injections are often needed. However, for certain peptides, there may be an alternative in drug delivery to meet the need for increased peptide bioavailability; this is the case for gut hormone mimetics (including glucagon-like peptide (GLP)-1 or GLP-2). One plausible alternative for improved oral delivery of these peptides is the co-stimulation of the endogenous secretion of the hormone to reach therapeutic levels of the peptide. This oration will be focused on studies conducted on the stimulation of gut hormones secreted from enteroendocrine L cells in the treatment of gastrointestinal disorders, including a critical discussion of the limitations and future perspectives of implementing this approach in the clinical setting.
Question: What are the ways to prevent mass transport of analytes to improve the accuracy of biosensors?
Inspiring Paper: Awawdeh et al. 2024. Enhancing the performance of porous silicon biosensors: the interplay of nanostructure design and microfluidic integration
This work presents the development and design of aptasensor employing porous silicon (PSi) Fabry‒Pérot thin films that are suitable for use as optical transducers for the detection of lactoferrin (LF), which is a protein biomarker secreted at elevated levels during gastrointestinal (GI) inflammatory disorders such as inflammatory bowel disease and chronic pancreatitis. To overcome the primary limitation associated with PSi biosensors—namely, their relatively poor sensitivity due to issues related to complex mass transfer phenomena and reaction kinetics—we employed two strategic approaches: First, we sought to optimize the porous nanostructure with respect to factors including layer thickness, pore diameter, and capture probe density. Second, we leveraged convection properties by integrating the resulting biosensor into a 3D-printed microfluidic system that also had one of two different micromixer architectures (i.e., staggered herringbone micromixers or microimpellers) embedded. We demonstrated that tailoring the PSi aptasensor significantly improved its performance, achieving a limit of detection (LOD) of 50M—which is $>1$ order of magnitude lower than that achieved using previously-developed biosensors of this type. Moreover, integration into microfluidic systems that incorporated passive and active micromixers further enhanced the aptasensor’s sensitivity, achieving an additional reduction in the LOD by yet another order of magnitude. These advancements demonstrate the potential of combining PSi-based optical transducers with microfluidic technology to create sensitive label-free biosensing platforms for the detection of GI inflammatory biomarkers.
Question: How does CRISPR/Cas9 compare to other gene-editing technologies in terms of efficiency and precision?
Inspiring Paper: Sajeesh et al. 2006. CRISPR/Cas9 gene-editing: Research technologies, clinical applications and ethical considerations
Gene therapy carries the potential to treat more than 10,000 human monogenic diseases and benefit an even greater number of complex polygenic conditions. The repurposing of CRISPR/Cas9, an ancient bacterial immune defense system, into a gene-editing technology has armed researchers with a revolutionary tool for gene therapy. However, as the breadth of research and clinical applications of this technology continues to expand, outstanding technical challenges and ethical considerations will need to be addressed before clinical applications become commonplace. Here, we review CRISPR/Cas9 technology and discuss its benefits and limitations in research and the clinical context, as well as ethical considerations surrounding the use of CRISPR gene editing.

表内文字对照（数值与原始行列保持不变）：
Question → 问题
What are different types of GLP- → 大语言模型有哪些不同的类型
analogs targeted for diabetes treatment → 用于糖尿病治疗的类似物
Inspiring Paper → 激励性论文
Beloqui et al → Beloqui等人
Gut hormone stimulation as a therapeutic approach in oral peptide delivery → 通过口服肽类递送方式利用肠道激素刺激作为治疗手段
In this contribution to the Orations - New Horizons of the Journal of Controlled Release → 在这篇为《控制释放杂志》的“演讲——新视野”系列文章中所做的贡献中
I discuss the research that we have conducted on gut hormone stimulation as a therapeutic strategy in oral peptide delivery → 我讨论了我们在口服肽剂递送中利用肠道激素刺激作为治疗策略所开展的研究
One of the greatest challenges in oral drug delivery involves the development of new drug delivery systems that enable the absorption of therapeutic peptides into the systemic circulation at therapeutically relevant concentrations → 口头药物递送领域最大的挑战之一在于开发新的药物递送系统，以使治疗性肽类以具有治疗意义的浓度被吸收到全身循环系统中
This scenario is especially challenging in the treatment of chronic diseases (such as type → 这种情况在慢性疾病的治疗中尤其具有挑战性（例如糖尿病）
diabetes mellitus) → 糖尿病
wherein daily injections are often needed → 其中通常需要每日注射
However → 然而
for certain peptides → 对于某些肽段
there may be an alternative in drug delivery to meet the need for increased peptide bioavailability → 在药物递送方面可能存在另一种方案，以满足提高肽类生物利用度的需求
this is the case for gut hormone mimetics (including glucagon-like peptide (GLP)- → 对于肠道激素模拟物而言也是如此（包括胰高血糖素样肽 (GLP)）
or GLP- → 或 GLP-
One plausible alternative for improved oral delivery of these peptides is the co-stimulation of the endogenous secretion of the hormone to reach therapeutic levels of the peptide → 改善这些肽的口服给药效果的一种可行替代方案，是协同刺激内源性激素分泌，以达到治疗水平的肽浓度
This oration will be focused on studies conducted on the stimulation of gut hormones secreted from enteroendocrine L cells in the treatment of gastrointestinal disorders → 本次讨论将聚焦于关于刺激肠内分泌L细胞分泌的肠道激素在治疗胃肠道疾病中的应用研究
including a critical discussion of the limitations and future perspectives of implementing this approach in the clinical setting → 包括对在临床环境中实施该方法的局限性及未来展望的批判性讨论
What are the ways to prevent mass transport of analytes to improve the accuracy of biosensors → 如何防止分析物在大规模传输过程中的扩散，以提高生物传感器的准确性
Awawdeh et al → Awawdeh等人
Enhancing the performance of porous silicon biosensors → 提升多孔硅生物传感器的性能
the interplay of nanostructure design and microfluidic integration → 纳米结构设计与微流体集成之间的相互作用
This work presents the development and design of aptasensor employing porous silicon (PSi) Fabry → 本文介绍了采用多孔硅（PSi）Fabry的大语言模型感知器开发与设计
rot thin films that are suitable for use as optical transducers for the detection of lactoferrin (LF) → 适合作为乳铁蛋白检测光学换能器的薄层薄膜
which is a protein biomarker secreted at elevated levels during gastrointestinal (GI) inflammatory disorders such as inflammatory bowel disease and chronic pancreatitis → 这是一种在胃肠道炎症疾病如炎症性肠病和慢性胰腺炎期间会升高水平的蛋白质生物标志物
To overcome the primary limitation associated with PSi biosensors → 为了克服 PSi 生物传感器的主要局限性
namely → 即
their relatively poor sensitivity due to issues related to complex mass transfer phenomena and reaction kinetics → 由于复杂的质量传递现象和反应动力学问题，其灵敏度相对较低
we employed two strategic approaches → 我们采用了两种策略性方法
First → 首先
we sought to optimize the porous nanostructure with respect to factors including layer thickness → 我们试图根据包括层厚度在内的各种因素来优化多孔纳米结构
pore diameter → 孔隙直径
and capture probe density → 并捕获探针密度
Second → 第二
we leveraged convection properties by integrating the resulting biosensor into a → 我们将对流特性利用起来，将得到的生物传感器整合到了一个系统中
D-printed microfluidic system that also had one of two different micromixer architectures (i → D打印微流体系统，同时具有两种不同微混合器结构之一（i
staggered herringbone micromixers or microimpellers) embedded → 交错式鱼骨状微混合器或微推进器
We demonstrated that tailoring the PSi aptasensor significantly improved its performance → 我们证明，对 PSi 感知传感器进行定制优化显著提升了其性能
achieving a limit of detection (LOD) of → 实现检测限（LOD）为
which is → 即
order of magnitude lower than that achieved using previously-developed biosensors of this type → 比使用此类先前开发的生物传感器所达到的水平低几个数量级
Moreover → 此外
integration into microfluidic systems that incorporated passive and active micromixers further enhanced the aptasensor → 整合到包含被动和主动微混合器的微流体系统中，进一步提升了aptasensor的性能
s sensitivity → s 的敏感性
achieving an additional reduction in the LOD by yet another order of magnitude → 进一步将 LOD 降低一个数量级
These advancements demonstrate the potential of combining PSi-based optical transducers with microfluidic technology to create sensitive label-free biosensing platforms for the detection of GI inflammatory biomarkers → 这些进展表明，将基于 PSi 的光学换能器与微流体技术相结合，能够打造出灵敏的无标签生物传感平台，用于检测胃肠道炎症生物标志物
How does CRISPR/Cas → CRISPR/Cas是如何工作的
compare to other gene-editing technologies in terms of efficiency and precision → 就效率和精准度方面与其他基因编辑技术进行比较
Sajeesh et al → Sajeesh等人
CRISPR/Cas → CRISPR/Cas
gene-editing → 基因编辑
Research technologies → 研究技术
clinical applications and ethical considerations → 临床应用与伦理考量
Gene therapy carries the potential to treat more than → 基因治疗具有治疗更多疾病的潜力
human monogenic diseases and benefit an even greater number of complex polygenic conditions → 人类单基因疾病以及更多复杂的多基因疾病也受到其影响
The repurposing of CRISPR/Cas → CRISPR/Cas技术的重新应用
an ancient bacterial immune defense system → 一种古老的细菌免疫防御系统
into a gene-editing technology has armed researchers with a revolutionary tool for gene therapy → 这种基因编辑技术为研究人员提供了用于基因治疗的革命性工具
as the breadth of research and clinical applications of this technology continues to expand → 随着该技术的研究范围与临床应用不断扩展
outstanding technical challenges and ethical considerations will need to be addressed before clinical applications become commonplace → 在临床应用普及之前，必须解决突出的技术挑战与伦理问题
Here → 这里
we review CRISPR/Cas → 我们对 CRISPR/Cas 进行了回顾
technology and discuss its benefits and limitations in research and the clinical context → 探讨该技术，并分析其在研究和临床场景中的优势与局限性
as well as ethical considerations surrounding the use of CRISPR gene editing → 以及与 CRISPR 基因编辑使用相关的伦理问题

### openscholar-0563

**English original**

Table 23: Scholar-Bio query examples . The “Inspiring Paper” refers to the paper used to help the expert annotator formulate a question.

**中文译文 · 机器初译**

表23：学者简介查询示例。“启发式文献”指用于帮助专家注释者提出问题的文献。

### openscholar-0564

**English original**

E.4 ScholarQA-Multi

**中文译文 · 机器初译**

E.4 ScholarQA-Multi

### openscholar-0565

**English original**

Figures 16 , 17 , 18 , 19 , and 20 show expert-annotated examples from different domains.

**中文译文 · 机器初译**

图16、图17、图18、图19和图20展示了来自不同领域的专家注释示例。

### openscholar-0566

**English original**

Figure 16: Examples of ScholarBench (Bio).

**中文译文 · 机器初译**

图 16：ScholarBench 示例（生物领域）。

### openscholar-0567

**English original**

Figure 17: An example of ScholarQA-Multi .

**中文译文 · 机器初译**

图17：ScholarQA-Multi的一个示例。

### openscholar-0568

**English original**

Figure 18: An example of ScholarQA-Multi .

**中文译文 · 机器初译**

图 18：ScholarQA-Multi 的一个示例。

### openscholar-0569

**English original**

Figure 19: An example of ScholarQA-Multi .

**中文译文 · 机器初译**

图19：ScholarQA-Multi的一个示例。

### openscholar-0570

**English original**

Figure 20: An example of ScholarQA-Multi .

**中文译文 · 机器初译**

图 20：ScholarQA-Multi 的一个示例。

