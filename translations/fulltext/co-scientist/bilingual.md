# Co-Scientist：全文中英对照

Accelerating scientific discovery with Co-Scientist

版本：2502.18864v2。获取日期：2026-11-09。

来源：[原始页面](https://arxiv.org/abs/2502.18864v2) · [原始 PDF](../../../sources/fulltext/co-scientist/original.pdf)

原文许可：http://creativecommons.org/licenses/by/4.0/

> 全文可提取文本的中英对照机器初译，含附录。摘要由当前助手复核，全文尚未逐段精校。作者/机构、参考文献、代码和公式按需保留原文；图内文字和复杂表格请结合原 PDF 核对。译文为非官方改编，作者未为其背书。

## 论文总结 / Reading summary

Co-Scientist repeatedly generates, reviews, ranks, and improves scientific hypotheses. It connects internal search with selected external biomedical experiments, illustrating both the promise and the limits of hypothesis-focused automation.

Co-Scientist 反复生成、评议、排序和改进科学假设，并将内部搜索与部分外部生物医学实验连接起来，展示了假设自动化的潜力与边界。

1. 研究问题：研究者需要结合深入的领域知识与跨领域线索，生成既新颖又可实验检验的假设。系统目标是辅助这类结构化科学思考。
2. 方法：通过异步框架协调不同角色，以生成、反思、排序、演化等循环改进候选；锦标赛式比较帮助分配后续研究计算。
3. 输入与输出：输入研究目标、约束与已有知识，输出研究假设和实验建议；研究者仍能提出方向并引导过程。
4. 证据：v2 包括药物再利用、靶点和耐药机制等应用，以及部分体外实验验证。外部实验与系统内部评分是两类不同证据。
5. 本次版本：采用 2026-06-29 的 arXiv v2，共 157 页；方法、扩展结果、案例与补充材料中的可提取文本均纳入对照初译。
6. 局限：内部 Elo 或评审偏好不等于实验成功。生物医学案例不能直接外推为无人机研究能力；假设质量与验证资源也可能高度相关。
7. 本项目可复用：生成多个竞争性解释，记录其预测，再让同一批仿真测试区分它们；分析内部排名能否预测最终未见场景收益。

## 逐段对照正文与附录


### 原文第 1 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=1)

### co-scientist-0002

**English original**

Accelerating scientific discovery with Co-Scientist

**中文译文 · 助手校对题名**

借助 Co-Scientist 加速科学发现

### co-scientist-0003

**English original**

Juraj Gottweis1*‡, Wei-Hung Weng2*‡, Alexander Daryin1*, Tao Tu2*, Petar Sirkovic1*, Artiom Myaskovsky1*, Grzegorz Glowaty1*, Felix Weissenberger1*, Alessio Orlandi1*, Dan Popovici3, Anil Palepu3, Keran Rong2, Ryutaro Tanno2, Khaled Saab2, Fan Zhang3, Jacob Blum4, Andrew Carroll3, Kavita Kulkarni3, Nenad Tomašev2, Dina Zverinski1, Ivor Rendulic1, Elahe Vedadi2, Florian Hasler1, Luka Rimanic1, Marina Boia1, Ivan Budiselic1, Ben Feinstein3, Mathias Bellaiche3, Tom Sheffer3, Jan Freyberg2, Jeremy Ratcliff2, Ottavia Bertolli2, Katherine Chou3, Avinatan Hassidim3, Burak Gokturk1, Amin Vahdat1, Yuan Guan4, Vikram Dhillon5, Eeshit Dhaval Vaishnav6, Byron Lee6, Tiago R D Costa7, José R Penadés7, Gary Peltz4, Yossi Matias3, James Manyika3, Demis Hassabis2, Yunhan Xu2, Pushmeet Kohli2‡, Annalisa Pawlosky3‡, Alan Karthikesalingam2‡, Vivek Natarajan2‡

**原文保留（专名、技术内容或文献信息） · 保留原文**

Juraj Gottweis1*‡, Wei-Hung Weng2*‡, Alexander Daryin1*, Tao Tu2*, Petar Sirkovic1*, Artiom Myaskovsky1*, Grzegorz Glowaty1*, Felix Weissenberger1*, Alessio Orlandi1*, Dan Popovici3, Anil Palepu3, Keran Rong2, Ryutaro Tanno2, Khaled Saab2, Fan Zhang3, Jacob Blum4, Andrew Carroll3, Kavita Kulkarni3, Nenad Tomašev2, Dina Zverinski1, Ivor Rendulic1, Elahe Vedadi2, Florian Hasler1, Luka Rimanic1, Marina Boia1, Ivan Budiselic1, Ben Feinstein3, Mathias Bellaiche3, Tom Sheffer3, Jan Freyberg2, Jeremy Ratcliff2, Ottavia Bertolli2, Katherine Chou3, Avinatan Hassidim3, Burak Gokturk1, Amin Vahdat1, Yuan Guan4, Vikram Dhillon5, Eeshit Dhaval Vaishnav6, Byron Lee6, Tiago R D Costa7, José R Penadés7, Gary Peltz4, Yossi Matias3, James Manyika3, Demis Hassabis2, Yunhan Xu2, Pushmeet Kohli2‡, Annalisa Pawlosky3‡, Alan Karthikesalingam2‡, Vivek Natarajan2‡

### co-scientist-0004

**English original**

1 Google Cloud AI Research, Zurich, Switzerland 2 Google DeepMind, Mountain View, California, USA 3 Google Research, Mountain View, California, USA 4 Stanford University School of Medicine, Palo Alto, California, USA 5 Houston Methodist, Houston, Texas, USA 6 Sequome, South San Francisco, California, USA 7 Fleming Initiative and Imperial College London, London, UK

**原文保留（专名、技术内容或文献信息） · 保留原文**

1 Google Cloud AI Research, Zurich, Switzerland 2 Google DeepMind, Mountain View, California, USA 3 Google Research, Mountain View, California, USA 4 Stanford University School of Medicine, Palo Alto, California, USA 5 Houston Methodist, Houston, Texas, USA 6 Sequome, South San Francisco, California, USA 7 Fleming Initiative and Imperial College London, London, UK

### co-scientist-0005

**English original**

* These authors contributed equally: Juraj Gottweis, Wei-Hung Weng, Alexander Daryin, Tao Tu, Petar Sirkovic, Artiom Myaskovsky, Grzegorz Glowaty, Felix Weissenberger, Alessio Orlandi. ‡ Corresponding to Juraj Gottweis (juro@google.com), Wei-Hung Weng (ckbjimmy@google.com), Pushmeet Kohli (pushmeet@google.com), Annalisa Pawlosky (apawlosky@google.com), Alan Karthikesalingam (alankarthi@google.com), Vivek Natarajan (natviv@google.com).

**原文保留（专名、技术内容或文献信息） · 保留原文**

* These authors contributed equally: Juraj Gottweis, Wei-Hung Weng, Alexander Daryin, Tao Tu, Petar Sirkovic, Artiom Myaskovsky, Grzegorz Glowaty, Felix Weissenberger, Alessio Orlandi. ‡ Corresponding to Juraj Gottweis (juro@google.com), Wei-Hung Weng (ckbjimmy@google.com), Pushmeet Kohli (pushmeet@google.com), Annalisa Pawlosky (apawlosky@google.com), Alan Karthikesalingam (alankarthi@google.com), Vivek Natarajan (natviv@google.com).


### 原文第 2 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=2)

### co-scientist-0007

**English original**

Summary

**中文译文 · 机器初译**

摘要

### co-scientist-0008

**English original**

Scientific discovery is driven by scientists generating novel hypotheses for complex problems that undergo rigorous experimental validation. To augment this process, we introduce Co-Scientist, a multi-agent AI system built on Gemini for structured scientific thinking and hypothesis generation. Co-Scientist aims to help scientists discover new original knowledge. Conditioned on their research objectives and prior scientific evidence, it formulates demonstrably novel research hypotheses for experimental verification. The system’s design involves agents continuously generating, critiquing and refining hypotheses accelerated by scaling test-time compute. Key contributions include: (1) a multi-agent architecture with an asynchronous task execution framework for flexible compute scaling; (2) a tournament evolution process for self-improving hypotheses generation. Automated evaluations show continued benefits of test-time compute scaling, improving hypothesis quality over time. While general purpose, we focus the validation in three biomedical applications: drug repurposing, novel target discovery 1, and explaining mechanisms of anti-microbial resistance 2. Specifically, Co-Scientist helped identify new drug repurposing candidates and synergistic combination therapies for acute myeloid leukemia, which were validated through in vitro experiments. These real-world validations demonstrate the potential of Co-Scientist to accelerate scientific discovery and usher in an era of AI empowered scientists.

**中文译文 · 助手复核摘要**

科学发现源于科学家针对复杂问题提出新颖假设，并对这些假设进行严格实验验证。为增强这一过程，我们提出 Co-Scientist：一个基于 Gemini 构建、用于结构化科学思考与假设生成的多智能体 AI 系统。Co-Scientist 旨在帮助科学家发现新的原创知识。它以研究目标和已有科学证据为条件，形成可供实验检验、具有可证新颖性的研究假设。系统通过持续生成、批评和完善假设，并扩大测试时计算投入来加速这一过程。主要贡献包括：（1）采用异步任务执行框架的多智能体架构，支持灵活扩展计算；（2）用于持续改进假设生成的锦标赛式演化过程。自动评价显示，扩大测试时计算能持续带来收益，使假设质量随时间提高。尽管系统具有通用性，我们将验证集中于三类生物医学应用：药物再利用、新靶点发现¹，以及解释抗微生物耐药机制²。具体而言，Co-Scientist 帮助识别了急性髓系白血病的新药物再利用候选及具有协同作用的联合治疗方案，并通过体外实验加以验证。这些真实世界验证显示了 Co-Scientist 加速科学发现、推动 AI 赋能科学家时代的潜力。

### co-scientist-0009

**English original**

Introduction

**中文译文 · 机器初译**

引言

### co-scientist-0010

**English original**

Researchers are faced with a breadth and depth conundrum. The complexity of scientific topics require increasingly deep and specific subject matter expertise, while leaps in insight may still arise from broad knowledge bridging across disciplines 3–5. With the rapid rise in scientific publications and the development of numerous specialized technologies, mastery of both discipline-specific depth and trans-disciplinary insight can be challenging.

**中文译文 · 机器初译**

研究人员面临着广度与深度之间的难题。科学主题的复杂性要求越来越深入且具体的专业知识，而新的见解则可能来自跨学科的广泛知识整合。随着科学论文的迅速增加以及众多专业技术的发展，同时掌握特定学科的深度与跨学科的洞察力确实具有挑战性。

### co-scientist-0011

**English original**

At the same time, there has been rapid technological progress in AI towards generally intelligent and collaborative systems, which might empower scientists in creatively traversing and expertly reasoning across disciplinary domains. Such systems are capable of advanced reasoning 6–8, multimodal understanding 8, and agentic actions 9, such as the ability to use tools to solve complex tasks over long time horizons. Further, the trends with distillation 10, and inference time compute costs 8,11, indicate that such intelligent and general AI systems are rapidly becoming more accessible. Motivated by the aforementioned unmet needs in the modern discovery process in science and medicine and building on the advancements in frontier AI 12, we develop and introduce Co-Scientist.

**中文译文 · 机器初译**

同时，人工智能技术正在迅速发展，朝着具有普遍智能与协作能力的系统方向前进，这可能会帮助科学家在多个学科领域进行创造性探索和专业推理。这类系统能够实现高级推理、多模态理解以及智能体行为，例如利用工具在长期范围内解决复杂任务。此外，蒸馏技术和推理时间计算成本方面的趋势表明，这种智能且通用的人工智能系统正逐渐变得更加易于使用。
基于科学与医学领域现代研究过程中存在的上述未满足需求，并依托前沿人工智能领域的进展，我们开发了 Co-Scientist 并对其进行了介绍。

### co-scientist-0012

**English original**

Co-Scientist is a structured scientific thinking engine designed to act as a collaborator to scientists and help accelerate the scientific discovery process. The system is a compound, multi-agent AI system 13 building on Google’s large language model (LLM), Gemini 14, mirroring the reasoning process underpinning the scientific method 15. Given a research goal

**中文译文 · 机器初译**

协同科学家是一个结构化的科学思维引擎，旨在作为科学家的合作伙伴，帮助加速科学发现过程。该系统是一个复合的多智能体人工智能系统，基于谷歌的大语言模型 Gemini 14 构建，其推理机制与科学方法的基础相呼应。针对某个研究目标


### 原文第 3 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=3)

### co-scientist-0014

**English original**

specified in natural language, the system can search, learn and reason over relevant literature to synthesize prior work and propose novel, original research hypotheses and experimental protocols (Fig. 1a). Co-Scientist provides grounding for its recommendations by citing relevant literature, applying sound scientific reasoning and verifying its conclusions through external tools when applicable.

**中文译文 · 机器初译**

以自然语言形式指定的内容，该系统能够检索、学习并分析相关文献，从而整合已有研究成果，提出新颖且原创的研究假设及实验方案（图1a）。Co-Scientist通过引用相关文献、运用合理的科学推理，并在适用时借助外部工具验证其结论，为建议提供依据。

### co-scientist-0015

**English original**

Co-Scientist is purpose-built for a “scientist-in-the-loop” collaborative paradigm. Scientists can specify their research goals in simple natural language and inform the system of desirable attributes and constraints for the proposed solutions. They can also actively interact with, and steer the system, including directly suggesting initial ideas and hypotheses for the exploration, refining generated ideas, or providing feedback through natural language chat.

**中文译文 · 机器初译**

Co-Scientist 是为“科学家在循环中的”协作模式而设计的专用工具。科学家们可以用简单的自然语言明确他们的研究目标，并向系统说明所提出的解决方案所需的属性与约束条件。他们还可以主动与系统互动并引导其运行，包括直接提出初步想法和假设以进行探索、完善生成的想法，或通过自然语言聊天提供反馈。

### co-scientist-0016

**English original**

Co-Scientist works through a significant scaling of the test-time compute paradigm 16–18 implementing structured scientific thinking in a multi-agent setup to iteratively reason, evolve, and improve the outputs as it gathers more knowledge (Fig. 1b). Underpinning the system are thinking and reasoning steps—notably a self-play based scientific debate step for generating novel research hypotheses; tournaments that compare and rank hypotheses via the process of finding win and loss patterns, and an evolution process to improve their quality. Finally, the agentic nature of the system enables it to recursively self-critique its output and use tools such as web-search and specialized AI models to provide itself with feedback to refine its hypotheses and research proposals.

**中文译文 · 机器初译**

联合科学家通过大幅扩展测试时计算模式（16–18），在多智能体环境中运用结构化科学思维进行迭代推理、进化与优化输出，同时积累更多知识（图1b）。该系统的核心包括一系列思考与推理步骤：特别是基于自我博弈的科学辩论步骤以生成新的研究假设；通过寻找胜负模式来比较和排序假设的竞赛；以及用于提升假设质量的进化过程。
最后，该系统的智能体特性使其能够递归地自我批判其输出结果，并利用网络搜索及专业人工智能模型等工具获取反馈，从而完善其假设与研究提案。

### co-scientist-0017

**English original**

While Co-Scientist is general purpose and applicable across scientific disciplines, we validate it in three impactful areas of biomedicine with varied complexity: drug repurposing for cancer, novel treatment target discovery for liver fibrosis, and new mechanistic explanations for antimicrobial resistance (Fig. 1c).

**中文译文 · 机器初译**

虽然 Co-Scientist 具有通用性，适用于各种科学领域，但我们在三个具有不同复杂度的生物医学关键领域对其进行了验证：癌症药物的重新应用、肝纤维化新型治疗靶点的发现，以及抗菌素耐药性新的机制解释（图 1c）。

### co-scientist-0018

**English original**

Drug development remains an expensive and protracted process, with most new approvals requiring de novo discovery for each indication 19. Systematic identification of new therapeutic indications for approved agents via drug repurposing offers a pragmatic strategy to accelerate development timelines and reduce attrition 20. Using Co-Scientist, we generated large-scale repurposing predictions validated through expert curation and in vitro assays. The system proposed several single-agent and combination therapies for AML that demonstrate selective cytotoxicity at clinically relevant concentrations. Beyond repurposing, Co-Scientist enables hypothesis generation for de novo target discovery, a process traditionally limited by the scale and uncertainty of biological inference. We applied Co-Scientist to liver fibrosis, where it proposed and ranked novel epigenetic targets demonstrating significant anti-fibrotic activity and hepatocyte regeneration in human hepatic organoids 1. Finally, we examined bacterial gene transfer mechanisms related to antimicrobial resistance (AMR), a system-level challenge involving molecular mechanisms and evolutionary pressures 2. Researchers instructed the system to explore a topic their group had independently discovered, but not yet published. Co-Scientist was asked to hypothesize how capsid-forming phage-inducible chromosomal islands (cf-PICIs) exist across bacterial species. It independently proposed that cf-PICIs interact with diverse phage

**中文译文 · 机器初译**

药物开发仍然是一个成本高昂且耗时漫长的过程，大多数新药品审批都需要针对每个适应症进行全新的研发工作19。通过药物再利用技术系统地识别已批准药物的新的治疗适应症，是一种能够加速开发周期并减少失败率的实用策略20。利用 Co-Scientist 工具，我们生成了大规模的药物再利用预测结果，这些预测结果经过专家审核和体外实验验证。该系统提出了多种单药及联合疗法用于 AML 治疗，这些疗法在具有临床意义的浓度下能表现出选择性细胞毒性。
除了重新利用现有资源外，Co-Scientist还能帮助生成新假设以发现全新靶点，而这一过程传统上受生物推理的规模和不确定性限制。我们将Co-Scientist应用于肝纤维化研究，它提出了多种新的表观遗传靶点，并在人类肝类器官中显示出显著的抗纤维化作用和肝细胞再生能力。最后，我们研究了与抗菌素耐药性相关的细菌基因转移机制，这是一个涉及分子机制和进化压力的系统级挑战。研究人员指示该系统探索其团队独立发现但尚未发表的课题。
共同科学家被要求提出假设，探讨如何存在跨越不同细菌物种的衣壳形成噬菌体诱导性染色体岛（cf-PICIs）。他独立提出了 cf-PICIs 与多种噬菌体相互作用的观点


### 原文第 4 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=4)


### 原文第 5 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=5)

### co-scientist-0021

**English original**

Fig. 1 | Co-Scientist design, multi-agent architecture, and experimental validation summary. (a) Overview: We illustrate the different components of Co-Scientist’s structured scientific thinking engine—the multi-agent system, and its interaction paradigm with scientists. Given a research goal in natural language, Co-Scientist generates novel research hypotheses. The system employs specialized Gemini based agents, including Generation, Reflection, Ranking, Evolution, Proximity (which evaluates relatedness), Meta-review (which provides high level analysis) agents, to continuously generate, debate, and evolve research hypotheses within a tournament framework. Feedback from the tournament enables iterative improvement, creating a self-improving loop towards novel and high-quality hypotheses for solving complex scientific problems. Co-Scientist leverages tools, including web search and specialized AI models to improve the grounding and quality of generated research hypotheses. Scientists can converse with Co-Scientist in natural language to specify research goals, incorporate constraints, provide feedback, steer and suggest new directions for explorations via the designated user interface. (b) The underlying multi-agent architecture: A Supervisor agent parses the user’s natural language research goal and dynamically allocates resources to specialized worker agents within an asynchronous task queue. The red boxes in the “Co-Scientist specialized agents'” section denote individual agents each with their own unique logic and role. The blue boxes indicate the scientist-in-the-loop inputs and feedback. The dark gray arrows represent the information flow through the Co-Scientist, while the red arrows represent the information feedback loop between the specialized agents. (c) End-to-end validation of Co-Scientist across three biomedical problems of varying complexity: Co-Scientist proposed novel drug repurposing candidates for acute myeloid leukemia (top), identified novel epigenetic targets for liver fibrosis (middle), and independently recapitulated a (then) unpublished, co-timed discovery of a novel bacterial gene transfer mechanism relevant to antimicrobial resistance (bottom). All Co-Scientist generated hypotheses were subsequently verified through independent in vitro laboratory experiments.

**中文译文 · 机器初译**

图1 | 联合科学家设计、多智能体架构及实验验证总结。(a) 概述：我们展示了联合科学家结构化科学思维引擎的不同组成部分——多智能体系统及其与科学家的交互模式。当面临以自然语言表述的研究目标时，联合科学家会生成新的研究假设。该系统使用专门的基于Gemini的智能体，包括生成、反思、排序、进化、邻近（用于评估相关性）和元评论（提供高级分析）智能体，在竞赛框架内持续生成、讨论并发展研究假设。
比赛反馈有助于进行迭代改进，从而形成一种自我提升循环，从而生成用于解决复杂科学问题的新颖且高质量的假设。联合科学家利用网络搜索和专用人工智能模型等工具，提升生成研究假设的可靠性与质量。
科学家可以通过自然语言与“合作科学家”进行交流，以明确研究目标、纳入约束条件、提供反馈，并通过指定的用户界面引导并建议新的探索方向。(b) 底层多智能体架构：主管智能体会解析用户用自然语言表达的研究目标，并在异步任务队列中动态分配资源给各专业工作智能体。在“合作科学家专业智能体”部分中的红色框标出了每个具有独特逻辑和角色的独立智能体；蓝色框则代表科学家参与式输入与反馈。
深灰色箭头表示通过协同科学家传递的信息流，而红色箭头则代表各智能体之间的信息反馈循环。(c) 对协同科学家进行了端到端验证，涉及三个不同复杂度的生物医学问题：协同科学家为急性髓系白血病提出了新的药物再利用候选方案（顶部）；发现了肝脏纤维化相关的新表观遗传靶点（中间）；并独立再现了当时尚未发表的一种与抗菌素耐药性相关的新型细菌基因转移机制的发现过程（底部）。
所有由联合科学家生成的假设均通过独立的体外实验室实验得到了验证。

### co-scientist-0022

**English original**

tails to expand host range, mirroring the researchers’ unpublished experimental findings detailed in co-timed reports 2,21.

**中文译文 · 机器初译**

通过扩展宿主范围来拓展其分布范围，这与研究人员在同期报告中详细描述的未发表实验结果一致，见报告 2,21。

### co-scientist-0023

**English original**

Overall, our key contributions are summarized as follows: (1) Introducing Co-Scientist. We develop and introduce Co-Scientist, a structured scientific thinking engine, that goes beyond literature summarization and “deep research” tools to assist scientists in uncovering new knowledge, novel hypothesis generation, discovering unexpected connections, and experimental planning. (2) Significant scaling of the test-time compute paradigm for scientific reasoning. Co-Scientist is built on a Gemini based multi-agent architecture, utilizing an asynchronous task execution framework. This framework allows the system to flexibly allocate computational resources to scientific reasoning, mirroring key aspects of the scientific method. Specifically, the system uses self-play strategies, including a scientific debate and a tournament-based evolution process, to iteratively refine hypotheses and research proposals creating a self-improving loop. Using automated evaluations across 15 complex expert curated open scientific goals, we

**中文译文 · 机器初译**

总体而言，我们的主要贡献可总结为以下几点：(1) 引入 Co-Scientist。我们开发并引入了 Co-Scientist 这一结构化科学思维引擎，它不仅支持文献总结与“深度研究”工具，还能帮助科学家发现新知识、生成新假设、发现意外关联以及规划实验。(2) 科学推理的测试时计算范式实现了显著扩展。Co-Scientist 基于基于 Gemini 的多智能体架构构建，采用异步任务执行框架。
该框架使系统能够灵活分配计算资源用于科学推理，反映了科学方法的关键特征。具体而言，该系统采用自玩策略，包括科学辩论和基于竞赛的进化过程，以迭代优化假设和研究提案，从而形成自我改进循环。通过针对15个由专家精心策划的复杂开放科学目标进行自动化评估，我们


### 原文第 6 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=6)

### co-scientist-0025

**English original**

demonstrate the benefits of scaling the test-time compute paradigm with Co-Scientist outperforming other state-of-the-art (SOTA) agentic and reasoning models in generating high quality hypotheses for complex problems. (3) Expert-in-the-loop scientific workflow. Our system is designed for collaboration with scientists. The system can flexibly incorporate conversational feedback in natural language from scientists and co-develop, evolve and refine outputs. (4) End-to-end validation of Co-Scientist in important topics in biomedicine. We present end-to-end validation of novel AI-generated hypotheses through new empirical findings in three distinct and increasingly complex areas of biomedicine: drug repurposing, novel target discovery, and antimicrobial resistance (Table 1, Supplementary Note 1).

**中文译文 · 机器初译**

证明通过 Co-Scientist 扩展测试时计算模式所带来的优势，其能够在生成复杂问题的高质量假设方面优于其他最先进的智能体与推理模型。（3）专家参与式科学工作流程。我们的系统旨在与科学家协作使用。该系统能够灵活整合科学家以自然语言提供的对话反馈，并共同开发、优化和完善输出结果。（4）在生物医学重要领域对 Co-Scientist 进行端到端验证。
我们通过三个不同且日益复杂的生物医学领域的新实证发现，提出了对新型人工智能生成假设的全端验证方法：药物重新应用、新靶点发现以及抗菌素耐药性（表1，补充注释1）。

### co-scientist-0026

**English original**

Table 1 | Three real-world applications in biomedicine for end-to-end validation of Co-Scientist. The table summarizes three scientific tasks selected to evaluate the hypothesis generation capabilities of Co-Scientist. The chosen applications span varying biological disciplines and are categorized by four axes, inherent challenge (the primary scientific objective), complexity (the depth of reasoning required), scale (data availability and experimental feasibility), and unknown elements (the boundaries of the hypothesis search space). These progressively demanding tasks illustrate Co-Scientist’s generalizability and its capacity to navigate both constrained problem spaces and open-ended explorations. Application Drug repurposing Novel treatment Explain mechanism target discovery of gene transfer evolution

**中文译文 · 机器初译**

表1 | 用于端到端验证 Co-Scientist 的大语言模型的三个实际医学应用。该表总结了三个用于评估 Co-Scientist 假设生成能力的科学任务。所选应用涉及不同的生物学领域，按四个维度进行分类：固有挑战（主要科学目标）、复杂度（所需的推理深度）、规模（数据可用性和实验可行性），以及未知元素（假设搜索空间的边界）。
这些逐步增加难度的任务体现了 Co-Scientist 的泛化能力，以及其在受限问题领域与开放式探索场景中的适应能力。应用药物再利用、新疗法开发、机制解释、靶点发现、基因转移与进化

### co-scientist-0027

**English original**

Challenge Complex search Identifying novel Understanding targets complex systems

**中文译文 · 机器初译**

挑战复杂搜索：识别新的理解目标与复杂系统

### co-scientist-0028

**English original**

Complexity Medium High Very high

**中文译文 · 机器初译**

复杂度 中等 高 非常高

### co-scientist-0029

**English original**

Scale Moderate, Moderate, Large, data and data-limited experiment-limited computation-limited

**中文译文 · 机器初译**

规模为中等、中等、大型，数据有限且实验受限、计算受限

### co-scientist-0030

**English original**

Unknown Constrained Large Vast and dynamic elements

**中文译文 · 机器初译**

未知的受限大规模广域动态元素

### co-scientist-0031

**English original**

Co-Scientist overview

**中文译文 · 机器初译**

联合科学家概述

### co-scientist-0032

**English original**

Given a research goal, Co-Scientist generates hypotheses constrained by default criteria including plausibility, novelty, testability, and safety. At a high level, it employs an asynchronous multi-agent architecture where a team of agents co-operate to solve scientific problems and develop novel hypotheses (Fig. 1b). It comprises a natural language interface for expert supervision, a task execution framework for resource allocation, a suite of specialized agents (Generation, Reflection, Ranking, Evolution, Proximity, Meta-review) mirroring the scientific

**中文译文 · 机器初译**

针对某个研究目标，Co-Scientist 会根据默认标准生成假设，这些标准包括合理性、新颖性、可验证性和安全性。从整体架构来看，它采用异步多智能体架构，由多个智能体协同合作以解决科学问题并提出新的假设（图1b）。该系统包含用于专家指导的自然语言界面、用于资源分配的任务执行框架，以及一系列专业智能体（生成、反思、排序、进化、邻近性、元评估），这些智能体与科学过程相呼应


### 原文第 7 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=7)

### co-scientist-0034

**English original**

method, and a persistent context memory for long-horizon reasoning. Detailed system configurations and agent mechanisms are fully described in the Methods.

**中文译文 · 机器初译**

方法，以及用于长时段推理的持久上下文记忆。详细的系统配置和智能体机制在“方法”部分中有完整描述。

### co-scientist-0035

**English original**

System analysis and evaluation

**中文译文 · 机器初译**

系统分析与评估

### co-scientist-0036

**English original**

We first conduct the initial system evaluations to benchmark and verify the choice of the architecture and metrics underpinning Co-Scientist (detailed in Supplementary Note 2, Supplementary Fig. 1). We perform an ablation study to investigate the contribution of each agentic component in Co-Scientist. We then analyze the impact of scaling test-time compute, and undertake a small-scale evaluation with domain experts to assess the quality of the system outputs. Finally, to assess the practical utility of the system’s novel predictions, we perform end-to-end wet-lab validations (laboratory experiments) of Co-Scientist-generated hypotheses and research proposals in three key biomedical applications: drug repurposing, discovering novel treatment targets, and elucidating the mechanisms underlying antimicrobial resistance (Table 1, Supplementary Note 1). The varying complexity and nature of these applications enable a more comprehensive assessment of the system. Notably, all three validations involved expert-in-the-loop.

**中文译文 · 机器初译**

我们首先进行初步系统评估，以对 Co-Scientist 所采用的架构和指标选择进行基准测试与验证（详见补充注释2、补充图1）。随后开展消融研究，探讨各智能体组件在 Co-Scientist 中的贡献程度。接着分析扩展测试时间计算量所带来的影响，并与领域专家进行小规模评估，以检验系统输出的质量。
最后，为了评估该系统新预测结果的实际效用，我们对协同科学家生成的假设和研究提案在三个关键生物医学领域进行了端到端的实验室验证实验：药物重新应用、新治疗靶点的发现以及抗菌素耐药性机制的解释（表1，补充注释1）。这些领域的复杂性和性质各不相同，从而能够更全面地评估该系统的性能。值得注意的是，所有验证工作都采用了专家参与式流程。

### co-scientist-0037

**English original**

Agent ablation analysis. Our ablation analyses, detailed in Methods, Supplementary Note 3, and Supplementary Fig. 2-6, confirmed the importance of our multi-agent architecture and specialized prompting strategies for robust scientific reasoning. For instance, granting the Reflection agent access to external search tools effectively prevented the hallucination of seemingly novel but implausible hypotheses, while employing a scientific debate prompt in the Ranking agent significantly improved the ranking of hypotheses and reduced positional bias. Furthermore, iterative refinement by the Evolution agent substantially boosted hypotheses quality.

**中文译文 · 机器初译**

智能体消融分析。我们在方法部分、补充注释3以及补充图2-6中详细进行的消融分析表明，我们的多智能体架构及专门的提示策略对于实现稳健的科学推理至关重要。例如，允许反思智能体使用外部搜索工具，有效避免了那些看似新颖但不可信的假设出现幻觉；而在排序智能体中使用科学辩论提示，则显著提升了假设的排序效果并减少了位置偏差。此外，进化智能体的迭代优化也大幅提高了假设的质量。

### co-scientist-0038

**English original**

Scaling test-time compute improves scientific reasoning. To evaluate the effects of test-time compute scaling and Co-Scientist’s progress during iterative scientific reasoning and hypothesis generation, we measured the Elo ratings of Co-Scientist generated hypotheses and proposals over the course of its thinking and computation (i.e. the tournament of hypotheses). This analysis was done across 203 distinct research goals curated across broad scientific topics (predominantly in biomedicine, but also included other topics such as mathematics and physics) and entered into Co-Scientist until February 3, 2025.

**中文译文 · 机器初译**

扩大测试时计算规模有助于提升科学推理能力。为了评估扩大测试时计算规模以及 Co-Scientist 在迭代式科学推理和假设生成过程中的进展所带来的影响，我们测量了 Co-Scientist 在思考与计算过程中生成的假设和提案的 Elo 评分（即假设竞赛）。这项分析涵盖了 203 个不同研究目标，这些目标涉及广泛的科学领域（主要集中在生物医学领域，但也包括数学和物理等其他领域），这些项目截至 2025 年 2 月 3 日已提交给 Co-Scientist。

### co-scientist-0039

**English original**

Co-Scientist’s research hypotheses and proposals were partitioned into ten temporal buckets of equal size. Each bucket corresponded to a sequential 10% of the total generation time with the first bucket containing the earliest 10% of generated Co-Scientist results, while the tenth bucket comprised the most recent 10%. For each bucket, we determined the average Elo rating of the top 10 hypotheses and the maximum individual Elo rating (the “best Elo”). These average and best Elo ratings were averaged across 203 research goals and their corresponding

**中文译文 · 机器初译**

合作科学家的研究假设与提案被划分为十个等大小的时间区间。每个区间对应总生成时间的10%，其中第一个区间包含最早产生的10%的合作科学家结果，第十个区间则包含最新的10%。针对每个区间，我们统计了前10个假设的平均Elo评分和最高单个Elo评分（即“最佳Elo”）。这些平均和最佳Elo评分则基于203项研究目标及其对应的数据进行汇总计算。


### 原文第 8 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=8)

### co-scientist-0041

**English original**

tournaments. The resulting performance trends as seen in Fig. 2a, across both metrics, serve as a measure of Co-Scientist’s quality improvement as it spends more time in thinking and computation—the most recent hypotheses demonstrate a significant quality enhancement compared to the initial ones. Notably, although the Elo rating is not the direct optimization target, its progressive increase emerges from the system’s information feedback loops that enable recursive self-improvement.

**中文译文 · 机器初译**

比赛。如图2a所示，各项指标下的性能趋势表明，随着智能体投入更多时间进行思考与计算，其质量得到了提升——最新的假设相比最初的假设展现了显著的质量改善。值得注意的是，尽管Elo评分并非直接优化目标，但其逐步上升源于系统的信息反馈机制，这种机制使得智能体能够实现递归自我改进。

### co-scientist-0042

**English original**

To further contextualize this observation, we focused our analysis on a subset of 15 research goals, curated as challenging problems by seven biomedical experts in their respective fields of expertise (Fig. 2b). These experts held doctoral degrees in biological or life science disciplines and were actively working as postdoctoral researchers or faculty members at academic research institutions. These research goals were consistently structured and formatted, encompassing a research title, a clear set of goals, preferences specifying biological or disease areas of interest, desirable solution attributes, and constraints on experimental techniques.

**中文译文 · 机器初译**

为了进一步阐明这一观察结果，我们针对15个研究目标进行了分析，这些目标由七位各自领域的生物医学专家作为具有挑战性的课题进行筛选（图2b）。这些专家均拥有生物或生命科学领域的博士学位，且正在学术研究机构担任博士后研究员或教职人员。这些研究目标具有统一的结构和格式，包括研究标题、明确的目标清单、指定的生物学或疾病领域偏好、理想的解决方案特征以及实验技术的限制条件。

### co-scientist-0043

**English original**

In addition to the research goals, the experts provided their “best guess” hypotheses or solutions. We then included outputs from other state-of-the-art LLMs and reasoning models at the time of this study (Gemini 2.0 Pro Experimental, Gemini 2.0 Flash Thinking Experimental 12-19, OpenAI o1, OpenAI o3-mini-high, and DeepSeek R1) in a tournament along with the expert “best guess” and Co-Scientist for each curated goal. Performance was assessed using Co-Scientist Elo rating metric.

**中文译文 · 机器初译**

除了研究目标外，专家们还提出了他们的“最佳猜测”假设或解决方案。随后，我们在本次研究中纳入了当时其他先进大语言模型和推理模型的输出结果（包括 Gemini 2.0 Pro Experimental、Gemini 2.0 Flash Thinking Experimental 12-19、OpenAI o1、OpenAI o3-mini-high 以及 DeepSeek R1），并与每个精心挑选的目标对应的专家“最佳猜测”及联合科学家的结果一起进行竞赛。性能评估则采用联合科学家埃洛评分指标进行。

### co-scientist-0044

**English original**

The trends previously observed with test-time compute scaling in Fig. 2a were consistent within this subset. Furthermore, as shown in Fig. 2b, Co-Scientist eventually significantly surpassed the other frontier LLMs and reasoning models in Elo rating with iterative improvement. Notably, newer reasoning models, such as OpenAI o3-mini-high and DeepSeek R1, demonstrated competitive performance while requiring significantly less compute and reasoning time. Finally, we observed no evidence of performance saturation as measured by Elo, suggesting that further scaling of test-time compute in this paradigm could yield continued improvements in result quality of Co-Scientist as long as the research goal is tractable and benefits for the “search and explore paradigm”. It’s worth noting again that Co-Scientist architecture is model agnostic and is likely to benefit from further advancements in frontier and reasoning LLMs such as the most recent Gemini 3 models.

**中文译文 · 机器初译**

图2a中观察到的测试时计算扩展趋势在该子集中依然成立。此外，如图2b所示，Co-Scientist在Elo评分体系中最终显著超越了其他前沿大语言模型和推理模型，并随着迭代改进不断提升成绩。值得注意的是，诸如OpenAI o3-mini-high和DeepSeek R1这类较新的推理模型也展现了具有竞争力的性能，同时所需的计算资源和推理时间则大幅减少。
最后，我们没有发现通过 Elo 指标所反映的性能饱和现象，这表明在该范式下进一步增加测试时的计算资源，只要研究目标可行且能带来“搜索与探索范式”的优势，就能持续提升 Co-Scientist 的结果质量。值得再次强调的是，Co-Scientist 架构具有模型无关性，很可能会从前沿及推理型 LLM（如最新的 Gemini 3 模型）的进一步发展中获得好处。

### co-scientist-0045

**English original**

Building upon Co-Scientist’s ability to refine and improve research hypotheses and proposals iteratively, we investigated its potential to improve upon expert “best guess” solutions. Consistent with our previous observations, Co-Scientist demonstrated the capacity to enhance expert’s “best guess” solutions over time, as evidenced by the Elo metric in Extended Data Fig. 1. Notably, the improvement trends initially mirrored those of Co-Scientist’s self-generated solutions but subsequently surpassed them as measured by Elo. While this is a preliminary finding requiring further validation, it suggests a new paradigm of human-AI collaboration in scientific discovery with systems such as Co-Scientist, augmenting and accelerating the work of expert scientists.

**中文译文 · 机器初译**

基于 Co-Scientist 能够反复优化研究假设与提案的能力，我们研究了其提升专家“最佳猜测”解决方案的潜力。与我们先前的观察一致，Co-Scientist 随着时间推移确实能够改善专家的“最佳猜测”解决方案，这一点从扩展数据图 1 中的 Elo 指标中可见一斑。值得注意的是，最初的改进趋势与 Co-Scientist 自生成的解决方案相似，但随后通过 Elo 指标衡量后便超越了它们。
虽然这一结果仅为初步发现，仍需进一步验证，但它提出了一种新的人类与人工智能在科学探索中的协作模式，可通过 Co-Scientist 等系统来辅助并加速专家科学家的工作。


### 原文第 9 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=9)

### co-scientist-0047

**English original**

Fig. 2 | Scaling test-time compute enhances Co-Scientist’s scientific thinking and hypotheses quality. (a) Impact of test-time compute scaling on Co-Scientist hypotheses quality measured by Elo auto-evaluation: Generated hypotheses across 203 diverse scientific research goals were partitioned into ten sequential temporal buckets. The continuous upward trend in both the maximum individual Elo rating (left) and the top-10 average Elo rating (right) suggests the system’s capacity for self-improvement towards high quality scientific hypotheses for complex problems. (b) Auto-evaluation benchmarking against standard language models and human experts: Evaluated on a subset of 15 highly complex, expert-curated biomedical goals, Co-Scientist leverages test-time compute scaling to surpass and generate higher quality and novel hypotheses compared to human domain experts and state-of-the-art large language and reasoning models (e.g., OpenAI o1, o3-mini-high, DeepSeek-R1). (c) Blinded human expert

**中文译文 · 机器初译**

图2 | 扩大测试时计算规模能够提升协同科学家的科学思维与假设质量。（a）测试时计算规模扩大对协同科学家假设质量的影响，通过Elo自动评估进行衡量：针对203个不同的科研目标生成的假设被划分为十个连续的时间区间。
最大个体 Elo 评分（左）和前 10 名平均 Elo 评分（右）均呈现持续上升趋势，表明该系统具备针对复杂问题生成高质量科学假设的自我提升能力。(b) 与标准语言模型和人类专家进行自动评估对比测试：在 15 个高度复杂的、由专家筛选的生物医学目标子集上进行了评估，Co-Scientist 利用测试时的计算扩展能力，能够生成比人类领域专家及最先进的大语言与推理模型（如 OpenAI o1、o3-mini-high、DeepSeek-R1）更高质量、更新颖的假设。(c) 盲测人类专家评估


### 原文第 10 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=10)

### co-scientist-0049

**English original**

evaluation: Independent domain experts rigorously assessed AI system hypotheses across 11 curated open biomedical problems. Left: Average expert ratings for hypothesis novelty and impact, evaluated independently on a 5-point Likert score and presented as grouped bar charts. Right: Overall expert preference ranking. Co-Scientist consistently achieved the highest expert ratings in novelty and impact and were selected as the preferred AI system by experts. For (a) and (b), data are presented as mean, and shaded regions indicate 95% confidence intervals. For two subfigures in (c), error bars represent probable errors, and the data are presented as mean ± probable errors. The exact sample sizes (n) are 203 research goals for (a), 15 goals for (b), and 11 goals for (c).

**中文译文 · 机器初译**

评估：独立领域专家对11个精心挑选的开放生物医学问题中的AI系统假设进行了严格评估。左图：关于假设新颖性和影响力的专家平均评分，以5点Likert评分独立评估后以分组条形图呈现。右图：专家整体偏好排序。Co-Scientist在新颖性和影响力方面始终获得最高的专家评分，因此被专家选为首选AI系统。对于(a)和(b)，数据以平均值形式呈现，阴影区域表示95%置信区间。对于(c)中的两个子图，误差条代表可能的误差，数据以平均值±可能误差的形式呈现。
具体的样本量分别为：(a) 203个研究目标，(b) 15个目标，(c) 11个目标。

### co-scientist-0050

**English original**

Extended Data Fig. 1 | AI-augmented expertise with Co-Scientist through Elo-based auto-evaluation. Through its self-improvement process, Co-Scientist refines and enhances expert “best guess” solutions over time, as measured by the Elo rating on a subset of 15 curated research goals. It is important to note that the Elo metric is auto-evaluated and not based on independent ground truth. The error bar indicates the corresponding standard error of the mean (SEM). Data are presented as mean ± SEM for 15 independent expert-curated research goals.

**中文译文 · 机器初译**

扩展数据图1 | 通过基于Elo的自动评估机制，利用Co-Scientist实现人工智能增强的专业能力。在自我改进过程中，Co-Scientist随着时间的推移不断优化和提升专家“最佳猜测”解决方案，这一效果可通过15个精心挑选的研究目标上的Elo评分来衡量。需要注意的是，Elo指标是通过自动评估得出的，并非基于独立的真实值。误差条表示对应的均值标准误（SEM）。数据以15个独立专家筛选的研究目标的均值±SEM形式呈现。

### co-scientist-0051

**English original**

Co-Scientist yields potentially novel and impactful results for experts. To obtain expert feedback and assess preferences, we conducted a small-scale expert evaluation on 11 of the 15 previously curated research goals. We asked the experts who curated the research goals to assess outputs from Co-Scientist, Gemini 2.0 Flash Thinking Experimental 12-19, Gemini 2.0 Pro Experimental, and OpenAI o1 models. Specifically, they provided a preference ranking (1 being most preferred and 4 being least preferred) and rated the novelty and impact of the proposed solutions on a 5-point scale, ranging from 1 (worst) to 5 (best) following this rubric:

**中文译文 · 机器初译**

联合科学家为专家提供了可能具有新颖性和影响力的结果。为了获取专家反馈并评估其偏好，我们对之前筛选出的15个研究目标中的11个进行了小规模专家评估。我们请负责筛选这些研究目标的专家对 Co-Scientist、Gemini 2.0 Flash Thinking Experimental 12-19、Gemini 2.0 Pro Experimental 以及 OpenAI o1 模型的输出进行评估。具体而言，他们给出了偏好排序（1为最偏好，4为最不偏好），并根据以下评分标准对所提出解决方案的新颖性和影响力在1到5的5分等级范围内进行评分：1为最差，5为最佳。


### 原文第 11 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=11)

### co-scientist-0053

**English original**

●​ Novelty: Higher-ranked outputs should propose hypotheses that, to the best of the expert’s knowledge, have not been previously published in any form. Hypotheses similar to existing proposals, even with minor modifications, should rank lower, and exact replicas of previously proposed and performed experiments should receive the lowest ranking. ●​ Impact: Higher-ranked outputs should address significant open questions in the field and have the potential to substantially advance scientific understanding or lead to practical applications.

**中文译文 · 机器初译**

●​ 新颖性：排名较高的输出应提出在专家知识范围内尚未以任何形式发表过的假设。与现有研究类似但存在细微修改的假设应排名较低，而之前提出的实验的完全复制品则应获得最低排名。●​ 影响力：排名较高的输出应解决该领域的重要未解问题，并有可能显著推进科学认知或带来实际应用。

### co-scientist-0054

**English original**

Across 11 expert-evaluated research goals, outputs generated by Co-Scientist were most preferred and rated higher in novelty and impact axes compared to the other baseline models. Specifically, Co-Scientist received an average preference rank of 2.36, and novelty and impact ratings of 3.64 and 3.09 (out of 5) as shown in Fig. 2c. These evaluations reflect subjective expert assessments, not objective ground truth. Notably, the human expert preferences also appear to be concordant with relative Elo ratings as can be inferred from Fig. 2b, 2c.

**中文译文 · 机器初译**

在11项专家评估的研究目标中，Co-Scientist生成的成果在新颖性和影响力两个维度上获得了最高的偏好度，评分也更高。具体而言，如图2c所示，Co-Scientist的平均偏好排名为2.36，新颖性和影响力评分分别为3.64和3.09（满分5分）。这些评估结果反映了主观专家评价，而非客观真实值。值得注意的是，人类专家的偏好与相对Elo评分似乎也一致，这一点可以从图2b和2c中推断出来。

### co-scientist-0055

**English original**

We also conducted the preference ranking evaluation for the 15 goals between Co-Scientist and other LLM and reasoning model baselines using the OpenAI o3-mini-2025-01-31, o1-preview-2024-09-12, Gemini 2.0 Pro Experimental and Gemini 2.0 Flash Thinking Experimental 01-21 as judges (LLM-as-a-judge evaluation). Co-Scientist outputs were the most preferred by all four evaluation judge LLMs as shown in Extended Data Fig. 2. Due to the small scale of these evaluations, further studies are necessary for any reliable conclusions. We further present a more comprehensive clinical expert evaluation focused on Co-Scientist proposals for drug repurposing in Supplementary Note 4 and and Supplementary Fig. 7.

**中文译文 · 机器初译**

我们还使用 OpenAI o3-mini-2025-01-31、o1-preview-2024-09-12、Gemini 2.0 Pro Experimental 以及 Gemini 2.0 Flash Thinking Experimental 01-21作为评判者，对 Co-Scientist 与其他大语言模型及推理模型基线之间的15项目标进行了偏好排序评估（即“大语言模型作为评判者”评估）。如扩展数据图2所示，Co-Scientist的输出得到了所有四个评估评判大语言模型的广泛青睐。由于这些评估的样本量较小，需要进一步研究才能得出可靠的结论。我们在补充注释4和补充图中进一步展示了针对 Co-Scientist 药物再利用建议的更全面的临床专家评估。
7.

### co-scientist-0056

**English original**

Real-world validations

**中文译文 · 机器初译**

现实世界验证

### co-scientist-0057

**English original**

Drug repurposing with Co-Scientist. Rigorous assessment of a system’s ability to generate novel hypotheses for complex scientific problems necessitates end-to-end experimental validation. However, due to the challenging, time-consuming, and resource-intensive nature of such endeavors, large-scale experimental validation is infeasible. Instead, we selected areas of unmet clinical need to serve as a strong benchmark for the end-to-end system evaluation of the system’s hypotheses generation capability. Importantly, all experimental validations were conducted in collaboration with expert scientists, who provided guidance to Co-Scientist and prioritized wet-lab experiments.

**中文译文 · 机器初译**

与联合科学家合作进行药物重新应用研究。要严格评估系统针对复杂科学问题生成新假设的能力，必须进行端到端的实验验证。然而，由于此类工作具有挑战性、耗时且资源消耗大，大规模实验验证难以实现。因此，我们选择了未满足的临床需求领域作为评估系统假设生成能力的端到端系统的有力基准。重要的是，所有实验验证均与专家科学家合作进行，这些科学家为联合科学家提供指导并优先安排湿实验室实验。

### co-scientist-0058

**English original**

Our first end-to-end validation of Co-Scientist is in drug repurposing, where the goal was to identify novel therapeutic indications for existing, approved drugs beyond their original use. This approach can accelerate the discovery of treatments for complex and rare diseases, as repurposed drugs have established safety profiles and are readily available. From a technical

**中文译文 · 机器初译**

我们首次对 Co-Scientist 的端到端验证应用于药物再利用领域，其目标是为已获批的现有药物寻找新的治疗适应症，超越其原始用途。这种方法可以加速复杂和罕见疾病的治疗发现，因为再利用的药物已经具备稳定的安全性特征且易于获取。从技术层面来看


### 原文第 12 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=12)

### co-scientist-0060

**English original**

Extended Data Fig. 2 | LLM preference ranking auto-evaluation of Co-Scientist and other baselines. Averaged preference ranking of results across 15 expert curated research goals generated by Co-Scientist, Gemini 2.0 Flash Thinking Experimental 12-19, Gemini 2.0 Pro Experimental, and OpenAI o1, using four different LLM evaluators: OpenAI o3-mini-2025-01-31 (upper left), OpenAI o1-preview-2024-09-12 (upper right), Gemini 2.0 Pro Experimental (lower left), and Gemini 2.0 Flash Thinking Experimental 01-21 (lower right). Lower numbers indicate better rankings. In each box plot, the central line represents the median ranking, the top and bottom edges of the box indicate the 25th and 75th percentiles respectively, the whiskers extend to the most extreme data points within 1.5 times the interquartile range, and the gray diamond marks the mean. Each box plot represents averaged evaluation scores for the 15 independent expert-curated research goals.

**中文译文 · 机器初译**

扩展数据图 2 | 大语言模型偏好排序自动评估：Co-Scientist及其他基线模型的表现。由 Co-Scientist、Gemini 2.0 Flash Thinking Experimental 12-19、Gemini 2.0 Pro Experimental 和 OpenAI o1 生成的、基于四种不同大语言模型评估器得出的结果平均偏好排序：OpenAI o3-mini-2025-01-31（左上），OpenAI o1-preview-2024-09-12（右上），Gemini 2.0 Pro Experimental（左下），以及 Gemini 2.0 Flash Thinking Experimental 01-21（右下）。数值越小表示排名越优。
在每个箱形图中，中心线表示中位数排名；箱子的上缘和下缘分别指示第25百分位数和第75百分位数；须线延伸至四分位距的1.5倍范围内的最极端数据点；灰色菱形则标示均值。每个箱形图代表了15个由独立专家筛选的研究目标的平均评估分数。

### co-scientist-0061

**English original**

standpoint, this is a complex search and explore problem involving a large but finite set of drug-disease pairs as noted in Table 1.

**中文译文 · 机器初译**

从视角来看，这是一个复杂的搜索与探索问题，涉及大量但有限的药物-疾病对组合，如表1所述。

### co-scientist-0062

**English original**

Given Co-Scientist’s ability to synthesize and integrate information across a vast body of scientific and clinical literature, we hypothesized that drug repurposing would be an ideal test of the system’s capabilities. The validation of Co-Scientist’s predictions was performed using a multi-faceted approach, incorporating computational biology analyses, oncologist expert feedback, and in vitro wet-lab experiments using cancer cell lines.

**中文译文 · 机器初译**

鉴于 Co-Scientist 能够整合大量科学与临床文献中的信息，我们提出假设：药物重新应用将是测试该系统能力的理想方法。对 Co-Scientist 预测的验证采用了多维度方法，包括计算生物学分析、肿瘤学家专家反馈以及使用癌细胞系的体外实验。


### 原文第 13 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=13)

### co-scientist-0064

**English original**

We constrained Co-Scientist to explore potential repurposing hypotheses from a curated list of 2300 approved drugs across 34 cancer types and conducted an oncologists’ expert review of the predictions (Supplementary Note 5.1 and Supplementary Fig. 8). Building upon the positive feedback from clinical experts, we conducted in vitro wet-lab validation experiments for drug repurposing hypotheses generated by Co-Scientist for acute myeloid leukemia (AML), an aggressive hematological malignancy marked by uncontrolled proliferation of myeloblasts, resulting in impaired hematopoiesis. Disease recurrence remains associated with a critical unmet need for effective therapeutic options 22. The cell line based experiments conducted here serve as an initial biological validation step for Co-Scientist hypotheses, with intentionally straightforward methodology following established protocols. We selected four AML cell lines for covering different AML subtypes (MOLM-13, KG-1a, HL-60, NOMO-1), and a non-AML cell line (TK6), based on the rationale provided by Co-Scientist and the clinical expert in the loop (Supplementary Note 5.2). It is important to emphasize that these wet-lab experiments function as a viability check of the drug repurposing pipeline, yet they are not a replacement for the rigorous pre-clinical and clinical assessment typically required for therapeutic validation. They provide an efficient biological reality check allowing us to rapidly evaluate AI-generated hypotheses before committing to more resource-intensive validation studies necessary for clinical translation.

**中文译文 · 机器初译**

我们限制了 Co-Scientist 从包含 2300 种已批准药物、覆盖 34 种癌症类型的精选列表中探索潜在的重新应用假设，并对这些预测进行了肿瘤学专家评审（补充注释 5.1 与补充图 8）。基于临床专家的积极反馈，我们对 Co-Scientist 为急性髓系白血病（AML）这一具有侵袭性血液系统恶性肿瘤所生成的药物重新应用假设进行了体外湿实验验证实验，该疾病特征为骨髓细胞异常增殖，导致造血功能受损。疾病复发仍然对应着对有效治疗方案的迫切需求 22。
此处进行的细胞系相关实验，作为合作科学家假设的初步生物验证步骤，采用了遵循既定规范的简单直接的研究方法。根据合作科学家及临床专家提供的依据（补充注释5.2），我们选择了四种AML细胞系来覆盖不同的AML亚型（MOLM-13、KG-1a、HL-60、NOMO-1），以及一种非AML细胞系（TK6）。需要强调的是，这些湿实验室实验仅用于验证药物重新应用流程的可行性，并不能替代治疗验证通常所需的严格临床前和临床评估。
它们提供了一种高效的生物学现实验证机制，使我们能够在投入资源更密集的验证研究以实现临床应用之前，快速评估由人工智能生成的假设。

### co-scientist-0065

**English original**

Wet-lab validation of Co-Scientist AML drug repurposing candidates. The candidate selection for wet-lab experiments was performed with meticulous expert oversight. Thirty top-ranked drug candidate hypotheses were shared with expert oncologists (an example detailed Co-Scientist output is provided in Supplementary Note 6). The experts evaluated the hypotheses, selecting drug candidates based on their potential to modulate key molecular signaling pathways associated with disease progression and resistance.

**中文译文 · 机器初译**

对 Co-Scientist AML 药物重新应用候选药物在湿实验室中的验证工作。这些候选药物的筛选过程由经验丰富的专家严格监督进行。30 个排名靠前的药物候选假设被分享给肿瘤学专家（Co-Scientist 的详细输出示例见补充注释 6）。专家们对这些假设进行了评估，根据它们调节与疾病进展和耐药性相关关键分子信号通路的潜力来选择药物候选药物。

### co-scientist-0066

**English original**

The primary selection criteria prioritized compounds with multi-pathway activity, specifically those targeting dysregulated inflammatory signaling, metabolic reprogramming, and aberrant cell proliferation. Emerging evidence indicates that these interconnected biological processes play critical roles in AML relapse and treatment resistance 23. Candidates were further prioritized based on preclinical mechanistic insights demonstrating relevance to AML biology, including their predicted effects on leukemic cell survival, interactions within the bone marrow microenvironment, and mechanisms underlying therapeutic resistance.

**中文译文 · 机器初译**

主要选择标准优先选择具有多通路活性的化合物，尤其是那些能够针对失调的炎症信号传导、代谢重编程和异常细胞增殖的化合物。最新研究表明，这些相互关联的生物学过程在急性髓系白血病复发和治疗抵抗中起着关键作用。基于与急性髓系白血病生物学相关的临床前机制研究结果，这些候选化合物还被进一步筛选，包括它们对白血病细胞存活的影响、在骨髓微环境中的相互作用以及治疗抵抗的机制。

### co-scientist-0067

**English original**

Based on potential mechanisms of action, five initial drug repurposing candidates, Binimetinib, Pacritinib, Cerivastatin, Pravastatin, and Dimethyl fumarate (DMF), were selected for further wet-lab validation in AML. Drug details are listed in Supplementary Note 5.3.

**中文译文 · 机器初译**

根据潜在作用机制，五种初步的药物重新应用候选药物——比尼米特inib、帕克里提尼布、塞瑞瓦司汀、普拉克司汀和二甲基富马酸（DMF）——被选为AML研究中的进一步湿实验验证对象。药物详细信息见补充注释5.3。

### co-scientist-0068

**English original**

Of the five drugs tested (experimental setup detailed in Supplementary Note 5.4), Binimetinib, Pacritinib, and Cerivastatin demonstrated inhibition of cell viability (Fig. 3a-c). Notably, Binimetinib, which is already approved for the treatment of metastatic melanoma, exhibited an half-maximal inhibitory concentration (IC50) as low as 2 nM in all AML cell lines (except NOMO-1), but much higher in the TK6 non-AML cell line (Fig. 3a and Extended Data

**中文译文 · 机器初译**

在测试的五种药物中（实验设置详见补充说明 5.4），比尼米特inib、帕克里提尼布和塞瑞瓦司汀均表现出对细胞存活率的抑制作用（图 3a-c）。值得注意的是，已获批准用于转移性黑色素瘤治疗的比尼米特inib在所有急性髓系白血病细胞系中均显示出低至 2 nM 的半最大抑制浓度（IC50）（NOMO-1 除外），而在 TK6非急性髓系白血病细胞系中的 IC50 则更高（图 3a及扩展数据）


### 原文第 14 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=14)

### co-scientist-0070

**English original**

Fig. 3 | In vitro biological validation of Co-Scientist generated single-agent repurposing candidates for acute myeloid leukemia (AML). Co-Scientist identified promising biologically active compounds, ranging from candidates with existing preclinical rationales to completely novel therapeutic targets for AML. (a-c) Dose-response curve of MOLM-13 AML cells treated with Binimetinib, Pacritinib, and Cerivastatin. Co-Scientist nominated candidates with existing evidence, demonstrating potent anti-leukemic activity. (d-h) Dose-response curves of the completely novel Co-Scientist predicted candidate KIRA6 (an IRE1α inhibitor) evaluated in different AML cell lines (d-g) and the normal lymphoblastoid control cell line TK6 (h). KIRA6 exhibits highly selective cytotoxicity against the KG-1a AML cell line compared to the non-malignant TK6 control. The 18-fold separation establishes a promising in vitro therapeutic window and suggests Co-Scientist’s promising capability to search, reason and identify biologically active compounds. The X-axis represents drug concentration (µM) on a logarithmic scale, and the Y-axis represents the percentage of growth inhibition. Data are presented as mean ± SD of n=3 biologically independent experiments. Exact IC50 values were determined using non-linear regression curve fitting.

**中文译文 · 机器初译**

图3 | Co-Scientist生成的单种药物重新应用候选物在急性髓系白血病（AML）中的体外生物验证。Co-Scientist发现了具有生物学活性的有希望化合物，这些化合物包括具有现有临床前依据的候选物，以及完全新的AML治疗靶点。（a-c）使用Binimetinib、Pacritinib和Cerivastatin处理的MOLM-13 AML细胞剂量反应曲线。
具有现有证据、表现出强抗白血病活性的共同科学家提名候选物。（d-h）在不同AML细胞系中评估的完全新发现的共同科学家候选物KIRA6（一种IRE1α抑制剂）的剂量反应曲线（d-g），以及正常淋巴母细胞对照细胞系TK6（h）。与非恶性TK6对照细胞相比，KIRA6对KG-1a AML细胞系具有高度选择性的细胞毒性。18倍的差异表明存在有前景的体外治疗窗口，并显示出共同科学家在寻找、推理和识别生物活性化合物方面的巨大潜力。
X轴表示以对数刻度显示的药物浓度（µM），Y轴表示生长抑制率。数据以n=3次生物学独立实验的平均值±标准差形式呈现。精确的IC50值是通过非线性回归曲线拟合方法确定的。

### co-scientist-0071

**English original**

Fig. 3). While Binimetinib demonstrated limited efficacy as monotherapy in heavily pretreated, RAS-mutant relapsed/refractory AML in a prior phase II study, Co-Scientist proposed an alternative repurposing strategy for frontline treatment without molecular profiling, based on modulation of baseline RAS-MEK-ERK pathway activity that may influence sensitivity to conventional chemotherapy in treatment-naive disease 24. This result shows the promise of Co-Scientist to aid with drug repurposing.

**中文译文 · 机器初译**

图3）。在之前的II期研究中，尽管比尼米特inib作为单药治疗对重度预治过的RAS突变复发/难治性AML疗效有限，Co-Scientist提出了一种无需分子分析的替代重新应用策略，通过调节基线RAS-MEK-ERK通路活性来作为一线治疗，这可能对治疗未接触过化疗的疾病中对常规化疗的敏感性产生影响24。这一结果表明Co-Scientist在药物重新应用方面具有潜力。

### co-scientist-0072

**English original**

Novel single-agent AML repurposing candidates. We next investigated Co-Scientist’s capacity to autonomously propose novel single-agent drug repurposing candidates without oversight.

**中文译文 · 机器初译**

新的单智能体大语言模型药物重新应用候选方案。接下来，我们研究了“联合科学家”在无需监督的情况下自主提出新的单智能体药物重新应用候选方案的能力。


### 原文第 15 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=15)

### co-scientist-0074

**English original**

Extended Data Fig. 3 | Dose response curves of drug repurposing candidate Binimetinib in other cell lines. Binimetinib demonstrates activity inhibiting cell viability in KG-1a, HL-60, and TK6 cell lines. X-axis is the drug concentration (μM), and Y-axis is the percentage of growth inhibition. Binimetinib’s target is related to the RAS–RAF–MEK–ERK pathway which is not generally expected to be overactive or essential in the TK6 cell line compared to AML cells. Thus, the significantly higher IC50 in TK6 compared to three AML cell lines (MOLM-13, KG-1a, HL-60), is consistent with its intended mechanism of action. Data are presented as mean ± SD of n = 3 biologically independent experiments.

**中文译文 · 机器初译**

扩展数据图 3 | 药物再利用候选物Binimetinib在其他细胞系中的剂量反应曲线。Binimetinib能够抑制KG-1a、HL-60和TK6细胞系的细胞存活率。X轴为药物浓度（μM），Y轴为生长抑制百分比。Binimetinib的靶点在RAS–RAF–MEK–ERK通路上，与AML细胞相比，在TK6细胞系中通常不会过度活跃或具有关键作用。因此，与MOLM-13、KG-1a和HL-60这三种AML细胞系相比，TK6中的IC50值显著更高，这与其预期的作用机制一致。数据以n = 3个生物学独立实验的平均值±标准差形式呈现。

### co-scientist-0075

**English original**

Towards this, the system was directed to generate a ranked list of repurposing candidates for AML that were not previously repurposed for the target indication and without any prior preclinical evidence. Further, the Co-Scientist did not receive any additional external inputs, such as the DepMap scores or human expert feedback. We then determined if these novel candidates suggested by Co-Scientist could be validated in the laboratory.

**中文译文 · 机器初译**

为此，系统被引导生成一份针对 AML 的重新应用候选方案的排序列表，这些方案此前尚未用于目标适应症，且没有任何前期临床前证据。此外，联合科学家并未收到任何额外的外部输入，如 DepMap 评分或人类专家反馈。随后我们判断了由联合科学家提出的这些新候选方案是否能够在实验室中得到验证。

### co-scientist-0076

**English original**

For in vitro laboratory validation, the domain experts reviewed and selected the top three repurposing candidates, to treat AML: Nanvuranlat, KIRA6, and Leflunomide.

**中文译文 · 机器初译**

对于体外实验室验证，领域专家对三个最佳重新应用候选药物进行了审查与选择，用于治疗急性髓系白血病：Nanvuranlat、KIRA6和来氟米特。

### co-scientist-0077

**English original**

The detailed Co-Scientist output, including the hypothesis, rationale and self-generated novelty review, is provided for KIRA6 in Supplementary Note 6. As can be seen, the system identifies that targeting IRE1α in the context of AML has been explored 25 before but not with the specific drug, KIRA6 suggesting the system is reasonably well-calibrated in its assessment of novelty. The system suggests an overall moderate level of novelty for the hypothesis.

**中文译文 · 机器初译**

详细的合作科学家输出内容，包括假设、理由以及自生成的创新性评价，均载于补充注释6中的KIRA6部分。从内容来看，系统认定在AML领域针对IRE1α的干预方法此前已有25项研究探索过，但并未使用特定的药物KIRA6，这表明系统在评估创新性方面具有合理的校准度。系统认为该假设的创新性整体处于中等水平。

### co-scientist-0078

**English original**

Of the three drugs tested, treatment with the IRE1α inhibitor KIRA6 showed inhibition of cell viability in several AML cell lines representing different molecular subtypes, KG-1a, MOLM-13, HL-60, NOMO-1, and a non-AML cell line, TK6, as a control (Fig. 3d-h, Supplementary Note 5.2, Supplementary Table 4). IC50 values of KIRA6 were all in nM or low μM range, but significantly more effective in KG-1a cells, which had an IC50 of 10 nM, compared to the non-AML control cell line, TK6, which had an IC50 of 180 nM. KIRA6 was also slightly more effective in NOMO-1 cells, with an IC50 of 144 nM, but notably, MOLM-13 and HL-60 cells were markedly less sensitive to KIRA6, with IC50 values of 1750 nM and 870 nM, respectively. The 18-fold separation between the highly primitive KG-1a cells and the normal lymphoblastoid TK6 line highlights a potential selective therapeutic window. The differential

**中文译文 · 机器初译**

在测试的三种药物中，IRE1α抑制剂KIRA6的治疗能够抑制多种代表不同分子亚型的急性髓系白血病细胞系——KG-1a、MOLM-13、HL-60、NOMO-1以及非急性髓系白血病细胞系TK6——的细胞存活率（图3d-h，补充注释5.2，补充表4）。KIRA6的IC50值均处于纳摩尔或低微摩尔范围，但在KG-1a细胞中效果显著更好，其IC50为10纳摩尔，而非急性髓系细胞系TK6的IC50为180纳摩尔。
KIRA6在NOMO-1细胞中也略显更有效，IC50值为144纳摩尔，但值得注意的是，MOLM-13和HL-60细胞对KIRA6的敏感性明显较低，相应的IC50值分别为1750纳摩尔和870纳摩尔。高度原始的KG-1a细胞与正常的淋巴母细胞TK6系之间相差18倍，这凸显了潜在的选择性治疗窗口。差异


### 原文第 16 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=16)

### co-scientist-0080

**English original**

sensitivities observed across distinct AML subtypes indicate that IRE1α blockade may be most effective in targeting primitive, stem-like AML populations over more differentiated lineages. Comprehensive cytogenetic rationales and molecular mechanisms correlating these varying cell line sensitivities to the IRE1α–XBP1 axis are detailed in Supplementary Note 5.2. Nanvuranlat and Leflunomide instead show limited effect on MOLM-13 cells (Extended Data Fig. 4).

**中文译文 · 机器初译**

不同AML亚型所表现出的敏感性差异表明，IRE1α阻断可能更适用于针对原始、干细胞样AML群体，而非更分化的谱系。与IRE1α–XBP1轴相关的各种细胞系敏感性差异的全面细胞遗传学依据及分子机制详见补充注释5.2。而Nanvuranlat和Leflunomide对MOLM-13细胞的影响则较为有限（扩展数据图4）。

### co-scientist-0081

**English original**

Extended Data Fig. 4 | Dose response curves of the drug repurposing candidates with little to no effect on MOLM-13. Of the expert-selected drug repurposing candidates, Pravastatin and DMF showed little to no effect on the MOLM-13 cell line across the concentrations tested. Of the novel drug repurposing candidates, Leflunomide and Nanvuranlat showed little to no effect on the MOLM-13 cell line across the concentrations tested. X-axis is the drug concentration (μM), and Y-axis is the percentage of growth inhibition. Data are presented as mean ± SD of n = 3 biologically independent experiments.

**中文译文 · 机器初译**

扩展数据图 4 | 对 MOLM-13 细胞系影响甚微或无影响的药物再利用候选药的剂量响应曲线。在专家筛选出的药物再利用候选药中，普伐他汀和 DMF 在所测试的所有浓度下对 MOLM-13 细胞系的影响甚微或无影响。在新型药物再利用候选药中，来氟米特和 Nanvuranlat 在所测试的所有浓度下对 MOLM-13 细胞系的影响亦甚微或无影响。X轴为药物浓度（μM），Y轴为生长抑制率。数据以 n = 3 次生物学独立实验的平均值±标准差形式呈现。

### co-scientist-0082

**English original**

Novel synergistic AML drug combinations. A common strategy for more effective treatment is the combination of drugs that synergistically target different disease pathways, but searching and screening for these combinations becomes exponentially more complex as the number of drugs increases. This is a complex task even for experts; at the same time, it may be well suited for AI. To investigate this, we tasked Co-Scientist to identify promising synergistic multi-drug regimens

**中文译文 · 机器初译**

新型协同作用AML药物组合。实现更有效治疗的一种常见策略是联合使用能够协同作用于不同疾病途径的药物，但随着药物数量的增加，寻找和筛选这些组合的方式会呈指数级复杂化。即使对专家来说这也是一项复杂的任务；同时，这或许非常适合人工智能处理。为了研究这一问题，我们委托联合科学家识别具有潜力的协同作用多药方案。


### 原文第 17 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=17)

### co-scientist-0084

**English original**

for AML. We then evaluated seven drug combinations proposed by Co-Scientist in MOLM-13 and KG-1a cell lines. In MOLM-13 cells, responses were predominantly synergistic across both dual (e.g., JNJ-64619178 + Selinexor) and triple combinations (e.g., JQ1 + Olaparib + MSA2). In contrast, KG-1a cells exhibited highly context-dependent responses with a mixture of synergy and antagonism, likely reflecting their distinct chemoresistant molecular profile (TP53-mutant). A comprehensive summary of all interaction patterns is provided in Fig. 4, Extended Data Figs. 5 and 6, Extended Data Tables 1, 2, and Supplementary Note 5.5. These patterns likely reflect the underlying molecular profiles of the two cell lines (detailed in Supplementary Note 5.3 and 5.5). Further mechanistic studies will be required to define the molecular determinants of response to combination therapy across AML subtypes, and to identify predictive biomarkers that could enable rational regimen selection.

**中文译文 · 机器初译**

针对大语言模型。随后我们评估了联合科学家在 MOLM-13 和 KG-1a 细胞系中提出的七种药物组合。在 MOLM-13 细胞中，响应主要具有协同作用，涵盖双药组合（如 JNJ-64619178 + Selinexor）与三药组合（如 JQ1 + Olaparib + MSA2）。相比之下，KG-1a 细胞则表现出高度依赖环境的反应模式，包含协同与拮抗效应，这可能反映了其独特的化疗耐药分子特征（TP53突变）。所有相互作用模式的全面总结见图 4、扩展数据图 5 和 6、扩展数据表 1、2 以及补充注释 5.5。
这些模式很可能反映了两种细胞系的潜在分子特征（详见补充注释 5.3 和 5.5）。进一步机制研究对于明确不同AML亚型对联合治疗的分子决定因素，以及识别能够指导合理治疗方案选择的预测性生物标志物是必要的。

### co-scientist-0085

**English original**

These results not only demonstrate Co-Scientist’s ability to identify potent single agents but also highlight its utility in proposing novel, synergistic drug combinations that have potential in addressing therapeutic resistance and treatment-refractory disease. Importantly, it shows the potential of Co-Scientist to discover novel drug combinations without the requirement of large-scale wet-lab screening, which becomes exponentially more costly and difficult as larger combinations are considered. Therefore, Co-Scientist may enable and unlock capabilities that were previously restricted by wet-lab design and feasibility.

**中文译文 · 机器初译**

这些结果不仅证明了 Co-Scientist 能够识别高效的单个智能体，还凸显了其在提出具有治疗抗性与难治性疾病治疗潜力的新型协同药物组合方面的作用。重要的是，这表明 Co-Scientist 在无需大规模湿实验筛选的情况下也能发现新的药物组合，随着组合规模的扩大，湿实验筛选的成本与难度会呈指数级上升。因此，Co-Scientist 可能能够启用并释放那些此前受湿实验设计与可行性限制的能力。

### co-scientist-0086

**English original**

Guiding clinical translation design. While the results are promising, translating these predictions from Co-Scientist into clinical practice will be highly challenging, as the complexity of a disease model, patient heterogeneity, and disease variability cannot be fully captured in such limited in vitro experiments. Even if a hypothesis generated by Co-Scientist is well-reviewed by oncologists and supported by preclinical rationale and strong in vitro experiments, this does not guarantee in vivo efficacy or clinical success. Factors such as drug bioavailability, pharmacokinetics, off-target effects, and patient selection criteria can all impact onward clinical trial outcomes. Moreover, in case of hematological malignancies, the tumor microenvironment and systemic interactions may introduce unforeseen resistance mechanisms, further complicating translation from hypothesis to clinical benefit.

**中文译文 · 机器初译**

指导临床转化设计。尽管结果令人鼓舞，但将 Co-Scientist 的预测转化为临床实践将极具挑战性，因为疾病模型的复杂性、患者异质性以及疾病变异性在如此有限的体外实验中无法完全被捕捉到。即使 Co-Scientist 提出的假设经过肿瘤学家充分审核，并得到临床前依据及强有力的体外实验支持，也并不能保证体内疗效或临床成功。药物生物利用度、药代动力学、非目标效应以及患者选择标准等因素都可能影响后续临床试验的结果。
此外，在血液系统恶性肿瘤中，肿瘤微环境与全身相互作用可能引入不可预知的抗药性机制，从而进一步使从假设到临床获益的转化过程变得复杂。

### co-scientist-0087

**English original**

To more faithfully approximate the parameters that govern real-world therapeutic decision-making, we tasked Co-Scientist with a structured translational analysis using a detailed clinical variable framework encompassing patient demographics, ELN2022 risk stratification, molecular features, preclinical activity, and established safety and PK/PD data (Supplementary Note 5.6).

**中文译文 · 机器初译**

为了更真实地模拟制约现实世界治疗决策的参数，我们要求联合科学家利用包含患者人口统计特征、ELN2022风险分层、分子特征、临床前活性以及成熟的安全性与药代动力学/药效学数据等详细临床变量框架，开展结构化的转化分析（补充注释5.6）。

### co-scientist-0088

**English original**

Here for example, Co-Scientist’s structured translational analysis successfully identified a specific clinical niche for Binimetinib: frail, heavily pretreated AML patients. The system accurately deduced that Binimetinib’s unique metabolic pathway (UGT1A1) circumvents severe CYP3A4-dependent drug-drug interactions common with azole antifungals—a major limitation for current targeted therapies (detailed in Supplementary Note 5.6). Extended results and methodological details are provided in Supplementary Note 5.2 and 5.6. Taken together, these

**中文译文 · 机器初译**

例如，Co-Scientist 的结构化翻译分析成功识别出了 Binimetinib 的一个特定临床应用场景：虚弱且已接受大量治疗的 AML 患者。该系统准确推断出 Binimetinib 独特的代谢途径（UGT1A1）能够避免与唑类抗真菌药常见的严重 CYP3A4 依赖性药物间相互作用——这是当前靶向疗法的主要限制（详见补充注释 5.6）。更详细的结果及方法学细节见补充注释 5.2 和 5.6。综合来看，这些结果具有重要意义


### 原文第 18 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=18)

### co-scientist-0090

**English original**

Fig. 4 | Validation of Co-Scientist predicted synergistic multi-drug combinations for acute myeloid leukemia (AML). Co-Scientist successfully navigated high-dimensional combinatorial spaces to propose effective multi-drug therapy regimens, validated here in the MOLM-13 and KG-1a AML cell lines. (a, b) Quantitative synergy analysis of the dual combination JNJ-64619178 and Selinexor. The plot illustrates the relationship between the Combination

**中文译文 · 机器初译**

图4 | 验证 Co-Scientist 预测的急性髓系白血病（AML）协同多药组合方案。Co-Scientist 成功在高维组合空间中提出有效的多药治疗方案，该方案已在 MOLM-13 和 KG-1a AML 细胞系中得到验证。(a, b) JNJ-64619178 与塞利诺克斯的联合用药协同性定量分析。图表展示了该组合之间的关系


### 原文第 19 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=19)

### co-scientist-0092

**English original**

Index (CI) and the fraction affected (Fa) using the Chou-Talalay method. The horizontal red dashed line represents strictly additive effects (CI = 1.0). Data points falling below this threshold denote the synergy zone (CI < 1), while points above denote the antagonism zone (CI > 1), confirming strong synergistic interactions for this Co-Scientist proposed double drug combination. (c, d) Excess fractional effect heatmap for the triple drug combination JQ1, Olaparib, and MSA2. Synergy is quantified across a matrix of drug concentrations (nM) using the Highest Single Agent (HSA) and Bliss independence models. The color scale illustrates the deviation from predicted additive effects: red regions indicate a positive excess effect (synergy), while blue regions represent a negative excess effect (antagonism). These results suggest Co-Scientist’s ability to identify highly active, complex combinatorial treatments without exhaustive empirical screening. Complete interaction profiles are available in Extended Data Figs. 5, 6 and Extended Data Tables 1, 2. For all synergy analyses, experiments were performed in n = 3 biologically independent replicates.

**中文译文 · 机器初译**

采用Chou-Talalay方法计算指数（CI）及受影响比例（Fa）。水平红色虚线表示严格加性效应（CI = 1.0）。低于该阈值的数据点代表协同作用区域（CI < 1），而高于该阈值的点则代表拮抗作用区域（CI > 1），这证实了该联合科学家提出的双药组合具有强烈的协同作用。（c, d）三重药物组合JQ1、奥拉帕利和MSA2的额外比例热图。通过最高单一药物（HSA）和Bliss独立性模型，在多种药物浓度范围（nM）内对协同作用进行量化。
颜色刻度展示了与预测的叠加效应之间的偏差：红色区域表示正向过量效应（协同作用），而蓝色区域则代表负向过量效应（拮抗作用）。这些结果表明，Co-Scientist能够识别那些高度活跃且复杂的组合疗法，而无需进行全面的实验筛选。完整的相互作用数据可参见扩展数据图5、6以及扩展数据表1、2。对于所有协同作用分析，实验均在n = 3个生物学上独立的重复实验中进行。

### co-scientist-0093

**English original**

analyses illustrate how Co-Scientist can help clinician scientists move beyond initial hypothesis generation to synthesize diverse clinical and biological variables into testable, clinically grounded therapeutic strategies.

**中文译文 · 机器初译**

分析表明，Co-Scientist 如何帮助临床科学家超越最初的假设生成阶段，将各种临床和生物学变量整合为可验证、具有临床针对性的治疗策略。

### co-scientist-0094

**English original**

Uncovering novel therapeutic targets for liver fibrosis. Co-Scientist utilized a method employing human hepatic organoids coupled with live cell imaging to find novel therapeutic targets for severe liver fibrosis 1, 26, 27. Co-Scientist was tasked with generating hypotheses on target epigenetic alterations (three top-ranked were selected by experts) and identifying drugs targeting these predicted epigenetic modifiers. It successfully identified three novel epigenetic modifiers and drugs targeting them, and two of them exhibited significant anti-fibrotic activity in the hepatic organoids without causing cellular toxicity. Critically, one of the effective drugs (Vorinostat) is already FDA-approved for another cancer indication, creating an opportunity for drug re-purposing for liver fibrosis treatment 1. This example also highlights the potential of AI systems such as Co-Scientist to make unexpected connections across disparate disciplines and diseases (cancer and liver fibrosis) and synthesize novel, helpful and impactful hypotheses and discoveries.

**中文译文 · 机器初译**

发现肝纤维化的新治疗靶点。合作科学家采用人类肝类器官与活细胞成像技术相结合的方法，找到了严重肝纤维化的新治疗靶点 1, 26, 27。合作科学家负责提出关于靶标表观遗传改变的假设（由专家选出三个最高排名的假设），并寻找针对这些预测表观遗传修饰因子的药物。他们成功发现了三种新的表观遗传修饰因子及其对应的药物，其中两种在肝类器官中表现出显著的抗纤维化作用，且未造成细胞毒性。
关键的是，其中一种有效的药物（伏立诺妥）已获得美国食品药品监督管理局批准用于另一种癌症治疗，这为该药物在肝纤维化治疗中的重新应用提供了机会。这个例子也凸显了像 Co-Scientist 这样的人工智能系统在跨不同学科与疾病（癌症和肝纤维化）之间建立意外关联，并生成新颖、有用且具有影响力的假设与发现方面的潜力。

### co-scientist-0095

**English original**

Recapitulating a breakthrough in antimicrobial resistance. Co-Scientist was also challenged to independently discover the mechanism behind the broad host range and rapid spread of capsid-forming phage-inducible chromosomal islands (cf-PICIs), mobile elements that carry virulence and antibiotic resistance genes across diverse bacterial species (including E. coli and K. pneumoniae). With only minimal background information, Co-Scientist independently and accurately proposed the groundbreaking, top-ranked hypothesis that cf-PICIs interact with diverse phage tails to expand their host range 2. This finding, generated by the AI in just two days, precisely matched the primary discovery of an independent, co-timed genomic and

**中文译文 · 机器初译**

回顾一下抗微生物耐药性方面的突破。合作科学家还被要求独立发现那些具有广泛宿主范围且能快速传播的衣壳形成噬菌体诱导的染色体岛（cf-PICIs）背后的机制——这些移动元素能够携带毒力基因和抗生素抗性基因，在多种细菌物种中传播（包括大肠杆菌和肺炎克雷伯菌）。在仅有少量背景信息的情况下，合作科学家独立且准确地提出了这一具有开创性的最高级别假设：cf-PICIs与各种噬菌体的尾部相互作用，从而扩大其宿主范围。
这一发现由人工智能在短短两天内生成，与独立且同步进行的基因组研究的主要发现完全吻合。


### 原文第 20 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=20)


### 原文第 21 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=21)

### co-scientist-0098

**English original**

Extended Data Fig. 5 | Comprehensive synergy analysis of Co-Scientist nominated dual drug combinations in AML cell lines. Building upon the representative example in Fig. 4a-b, this figure details the pharmacological interactions of additional AI-predicted doublets evaluated in MOLM-13 and KG-1a cell lines. Synergy was quantified using the Chou-Talalay method based on fixed-ratio dose-response data. Each panel presents a Fraction affected versus Combination Index (Fa-CI) plot. The horizontal red dashed line indicates a strictly additive effect (CI = 1.0). Data points below the line (CI < 1.0) indicate synergistic interactions, while points above the line (CI > 1.0) indicate antagonism. The results highlight that while certain combinations (e.g., Palbociclib + Selinexor) exhibit consistent synergy across different genetic backgrounds, others display context-dependent interaction profiles strongly influenced by the specific cell line’s mutational status.

**中文译文 · 机器初译**

扩展数据图 5 | AML 细胞系中 Co-Scientist 推荐的双药组合的综合协同作用分析。基于图 4a-b中的典型示例，本图详细展示了在 MOLM-13 和 KG-1a 细胞系中评估的、由 AI 预测出的双药组合的药理相互作用。通过基于固定比例剂量反应数据的 Chou-Talalay 方法对协同作用进行量化。每个面板均呈现了“受影响的分数”与“组合指数”曲线图。水平红色虚线表示严格相加效应（CI = 1.0）。位于该线下方的数据点（CI < 1.0）表明存在协同作用，而位于该线上方的数据点（CI > 1.0）则表明存在拮抗作用。
研究结果表明，某些组合（如帕博西尼与塞利诺索尔）在不同基因背景下表现出一致的协同效应，而其他组合则呈现依赖于具体细胞系突变状态的情境依赖交互特征。

### co-scientist-0099

**English original**

Extended Data Fig. 6 | Excess fractional effect heatmaps for Co-Scientist predicted triple drug combinations. Complementing Fig. 4c-d, this figure provides the interaction matrices for the other evaluated triplet regimen (JNJ-64619178 + SNDX-5613 + Selinexor) across AML cell

**中文译文 · 机器初译**

扩展数据图 6 | Co-Scientist 预测的三联药物组合的额外分数效应热图。与图 4c-d 相补充，该图还展示了其他评估的三联方案（JNJ-64619178 + SNDX-5613 + Selinexor）在急性髓系白血病细胞中的交互矩阵


### 原文第 22 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=22)

### co-scientist-0101

**English original**

lines. Synergy and antagonism are quantified across a comprehensive grid of drug concentrations (nM) utilizing both the Highest Single Agent (HSA) and Bliss independence models. The heatmaps display the fractional excess effect: the difference between the observed combined empirical effect and the predicted additive effect. Positive excess effects are visualized in red (synergy), zero excess in white (additivity), and negative excess in blue (antagonism). To compress the three-dimensional dose space into a two-dimensional matrix, the plots display the maximum positive interaction across the third drug’s dose range.

**中文译文 · 机器初译**

线条。通过最高单一药物浓度（nM）的全面浓度网格，利用最高单一药物独立模型和Bliss独立模型，对协同效应与拮抗效应进行了量化。热图显示了分数超额效应：即观测到的综合经验效应与预测加性效应之间的差值。正超额效应以红色表示（协同效应），零超额效应以白色表示（加性），负超额效应以蓝色表示（拮抗效应）。为了将三维剂量空间压缩为二维矩阵，图表展示了第三种药物剂量范围内的最大正相互作用。

### co-scientist-0102

**English original**

Extended Data Table 1 | IC50 of the drugs used in the drug combination experiments in AML cell lines, MOLM-13 and KG-1a. The table presents the half-maximal inhibitory concentrations (IC50, in μM) for 11 individual drugs evaluated in two acute myeloid leukemia (AML) cell lines, MOLM-13 and KG-1a. These single-agent efficacies were determined to establish the baseline dose-response behaviors required for the subsequent drug combination synergy analyses. Cell viability was assessed following 72 to 96 hours of drug exposure. IC50 values were estimated using non-linear regression curve fitting. “No response” indicates that the drug failed to achieve 50% growth inhibition within the tested concentration range. All experiments were performed in biologically independent triplicates (n = 3).

**中文译文 · 机器初译**

扩展数据表1 | 用于急性髓系白血病细胞系 MOLM-13 和 KG-1a 药物组合实验中药物的 IC50值。该表格列出了在两种急性髓系白血病细胞系 MOLM-13 和 KG-1a 中评估的11种单独药物的半最大抑制浓度（IC50，单位：μM）。这些单药疗效的测定旨在确定后续药物组合协同作用分析所需的基线剂量-反应特性。细胞存活率是在药物作用72至96小时后进行评估的。
通过非线性回归曲线拟合来估算 IC50值。“无反应”表示该药物在所测试的浓度范围内未能实现50%的生长抑制。所有实验均进行了生物学独立的三次重复实验（n = 3）。

### co-scientist-0103

**English original**

IC50 (μM)
Drug
MOLM-13 KG-1a
MSA-2 No response No response
Sulfasalazine No response No response
CB-839 16.98 8.79
JNJ-64619178 (Onametastat) 0.0046 0.024
Pinometastat No response No response
Selinexor 0.039 0.055
JQ1 0.011 0.12
Venetoclax 0.009 0.006
Olaparib 2.12 7.1
SNDX 0.010 No response
Palbociclib 0.026 0.07

**中文译文 · 机器初译**

IC50 (μM)
Drug
MOLM-13 KG-1a
MSA-2 No response No response
Sulfasalazine No response No response
CB-839 16.98 8.79
JNJ-64619178 (Onametastat) 0.0046 0.024
Pinometastat No response No response
Selinexor 0.039 0.055
JQ1 0.011 0.12
Venetoclax 0.009 0.006
Olaparib 2.12 7.1
SNDX 0.010 No response
Palbociclib 0.026 0.07

表内文字对照（数值与原始行列保持不变）：
Drug → 药物
MOLM- → MOLM-
KG- → KG-
MSA- → MSA-
No response No response → 无回复 无回复
Sulfasalazine No response No response → sulfasalazine 无响应 无响应
CB- → CB-
JNJ- → JNJ-
Onametastat) → Onametastat)
Pinometastat No response No response → Pinometastat 无回应 无回应
Selinexor → 塞利诺克斯
Venetoclax → 维内托克沙
Olaparib → 奥拉帕利
SNDX → SNDX
No response → 无回复
Palbociclib → 帕博西利


### 原文第 23 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=23)

### co-scientist-0105

**English original**

Extended Data Table 2 | Summary of the drug combination synergy experiments . The table categorizes the overall in vitro interaction profiles of seven Co-Scientist nominated drug combinations, including doublet and triplet combinations, evaluated in two acute myeloid leukemia (AML) cell lines, MOLM-13 and KG-1a. Pharmacological interactions were quantitatively assessed using the Chou-Talalay combination index (CI) method for doublets, and Highest Single Agent (HSA) and Bliss independence models for triplets. The interaction outcomes are classified into three categories, “Synergistic” (exhibiting CI < 1 or positive excess fractional effect), “Not synergistic” (additive or antagonistic effects), and “Mixed response” (exhibiting context-dependent effects, transitioning between synergy and antagonism depending on the dose or effect level). All experiments were performed in biologically independent triplicates (n = 3).

**中文译文 · 机器初译**

扩展数据表2 | 药物组合协同作用实验总结。该表格对七种由 Co-Scientist 推荐的药物组合进行了整体体外相互作用分析，这些组合包括双药组合和三药组合，在两种急性髓系白血病（AML）细胞系 MOLM-13 和 KG-1a 中进行了评估。对于双药组合，采用 Chou-Talalay 组合指数（CI）方法进行定量评估；对于三药组合，则使用最高单药效应（HSA）和 Bliss 独立性模型进行评估。
交互结果被分为三类：“协同效应”（表现出 CI < 1 或正超额分数效应）、“非协同效应”（加性或拮抗效应）以及“混合反应”（表现出依赖上下文的效应，根据剂量或效应水平在协同与拮抗之间切换）。所有实验均以生物学上独立的三重样本进行（n = 3）。

### co-scientist-0106

**English original**

Drug combination MOLM-13 KG-1a
JNJ-64619178 + Selinexor Synergistic Mixed response
Palbociclib + Selinexor Synergistic Synergistic
JNJ-64619178 + SNDX-5613 Synergistic Mixed response
CB-839 + Sulfasalazine Not synergistic Not synergistic
Venetoclax + Pinometostat Mixed response Synergistic
JNJ-64619178 + Selinexor +
Synergistic Synergistic
SNDX-5613
JQ1 + Olaparib + MSA-2 Synergistic Not synergistic

**中文译文 · 机器初译**

Drug combination MOLM-13 KG-1a
JNJ-64619178 + Selinexor Synergistic Mixed response
Palbociclib + Selinexor Synergistic Synergistic
JNJ-64619178 + SNDX-5613 Synergistic Mixed response
CB-839 + Sulfasalazine Not synergistic Not synergistic
Venetoclax + Pinometostat Mixed response Synergistic
JNJ-64619178 + Selinexor +
Synergistic Synergistic
SNDX-5613
JQ1 + Olaparib + MSA-2 Synergistic Not synergistic

表内文字对照（数值与原始行列保持不变）：
Drug combination MOLM- → 药物组合 MOLM-
KG- → KG-
JNJ- → JNJ-
Selinexor Synergistic Mixed response → 塞利尼索协同混合反应
Palbociclib → 帕博西利
Selinexor Synergistic Synergistic → 塞利诺索尔协同作用
SNDX- → SNDX-
Synergistic Mixed response → 协同混合响应
CB- → CB-
Sulfasalazine Not synergistic Not synergistic → sulfasalazine 无协同作用 无协同作用
Venetoclax → 维内托克沙
Pinometostat Mixed response Synergistic → Pinometostat 混合响应协同作用
Selinexor → 塞利诺克斯
Synergistic Synergistic → 协同效应 协同效应
Olaparib → 奥拉帕利
MSA- → MSA-
Synergistic Not synergistic → 协同的 非协同的

### co-scientist-0107

**English original**

experimental study prior to completing peer-review 21. This convergence and recapitulation is another demonstration of Co-Scientist's potential to accelerate scientific discovery by synthesizing complex scientific information and generating rigorous scientific hypotheses on-par with experts.

**中文译文 · 机器初译**

在完成同行评审之前进行的实验研究 21。这种融合与再现进一步证明了 Co-Scientist 通过整合复杂的科学信息并生成与专家相当的严谨科学假设，从而加速科学发现的能力。


### 原文第 24 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=24)

### co-scientist-0109

**English original**

Discussion

**中文译文 · 机器初译**

讨论部分

### co-scientist-0110

**English original**

In this work, we report the development and initial validation of a multi-agent, Gemini based AI system, Co-Scientist, designed as a structured scientific thinking engine to accelerate novel scientific discovery. Co-Scientist moves beyond conventional computational approaches through the in-silico implementation of a multi-agent architecture that mirrors the core aspects of the scientific method. Instead of brute-force generation, the system iteratively refines hypotheses through a “generate, debate, evolve” paradigm. This method, which incorporates self-debate, tournament-based selection, and iterative evolution and refinement, enables a progressive convergence on high-quality, well-supported hypotheses, thereby scaling research ideation with test-time compute rather than exhaustive generation. The system’s context memory, combined with the iterative self-improvement cycle, functions as an emergent internal model of the scientific research process. While not an explicit symbolic model, it represents a progressively more coherent and interconnected state of knowledge, facilitating the synthesis of information and the identification of knowledge gaps.

**中文译文 · 机器初译**

在本研究中，我们报告了基于多智能体 Gemini 的大语言模型人工智能系统 Co-Scientist 的开发及初步验证情况。该系统被设计为一种结构化的科学思维引擎，旨在加速新的科学发现。Co-Scientist 通过实现模仿科学方法核心要素的多智能体架构，超越了传统的计算方法；该系统采用“生成—讨论—进化”的范式，而非盲目生成，从而逐步优化假设。
该方法结合自我辩论、基于竞赛的筛选以及迭代式进化与优化机制，能够逐步收敛到高质量且得到充分支持的假设，从而通过测试时的计算能力来扩展研究思路的拓展，而非依赖全面的生成过程。系统的上下文记忆与迭代式自我改进循环共同构成了科学研究过程的内部模型。虽然并非显式的符号模型，但它代表了逐渐更加连贯且相互关联的知识状态，有助于信息的整合及知识缺口的识别。

### co-scientist-0111

**English original**

The practical utility of this approach was demonstrated through the generation of novel and experimentally tractable hypotheses across three challenging and varied biomedical problems. In oncology, Co-Scientist identified drug repurposing candidates for AML that showed in vitro efficacy at clinically relevant concentrations. For liver fibrosis, it proposed novel epigenetic targets, leading to the experimental validation of several anti-fibrotic compounds, including one FDA-approved drug. Furthermore, in microbiology, the system independently recapitulated a novel, (and then) unpublished mechanism of mobile genetic element transfer between bacteria. These findings provide preliminary evidence that Co-Scientist can contribute meaningfully to scientific discovery by amplifying scientists.

**中文译文 · 机器初译**

通过针对三个具有挑战性且多样化的生物医学问题生成新的、可实验验证的假设，该方法的实际效用得到了证明。在肿瘤学领域，联合科学家发现了可用于AML的药物再利用候选物，这些候选物在临床相关浓度下具有体外有效性。针对肝纤维化问题，该系统提出了新的表观遗传靶点，从而成功验证了多种抗纤维化化合物，其中还包括一种已获得FDA批准的药物。此外，在微生物学领域，该系统独立再现了细菌之间移动遗传元素传递的新机制（该机制当时尚未发表）。
这些研究结果提供了初步证据，表明 Co-Scientist 可以通过增强科学家的能力，为科学发现做出有意义的贡献。

### co-scientist-0112

**English original**

This system’s architecture is model-agnostic, allowing it to leverage the advancing capabilities of frontier LLMs without requiring retraining of the whole agentic framework such as Gemini 3, GPT 5.4 and Opus 4.6. With the latest advances in frontier models, we expect further significant improvements in the quality of hypotheses generated and the complexity of scientific tasks the system can autonomously accomplish.

**中文译文 · 机器初译**

该系统的架构具有模型无关性，能够利用前沿大语言模型日益先进的性能，而无需对 Gemini 3、GPT 5.4 和 Opus 4.6 等整个大语言模型框架进行重新训练。随着前沿模型的最新进展，我们预计系统生成的假设质量以及其能够自主完成的科学任务复杂度都将得到进一步显著提升。

### co-scientist-0113

**English original**

Despite these promising early results, several limitations must be addressed. Co-Scientist’s knowledge is constrained by its reliance on open-access scientific literature, which may lead to the omission of critical prior art behind paywalls and a systemic lack of access to negative experimental results. Furthermore, the quality of generated hypotheses relies on the mixed and contradictory quality of the source literature; thus, there is a risk of propagating erroneous or irreproducible findings. A key future direction is the development of agents with enhanced provenance capabilities to trace claims to specific figures or data within a source, mitigating the impact of unreliable literature.

**中文译文 · 机器初译**

尽管这些早期结果令人鼓舞，但仍有若干局限性需要解决。合作科学家的知识受限于对开放获取科学文献的依赖，这可能导致无法获取那些被付费墙阻挡的关键现有技术，同时也难以获得负面实验结果。此外，生成假设的质量取决于来源文献的混杂与矛盾性，因此存在传播错误或不可重复的研究结果的风险。未来的关键方向是开发具有增强来源追踪能力的智能体，以便能够追溯特定数据或信息在来源中的出处，从而减轻不可靠文献的影响。

### co-scientist-0114

**English original**

Co-Scientist also inherits the intrinsic limitations of its underlying models, including imperfect factuality and the potential for hallucinations. Improving reasoning capabilities is a

**中文译文 · 机器初译**

协同科学家也继承了其底层模型固有的局限性，包括不完美的真实性以及产生幻觉的可能性。提升推理能力是


### 原文第 25 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=25)

### co-scientist-0116

**English original**

critical area for future work. Additionally, the validation of Co-Scientist’s hypotheses, while successful, remains preliminary.

**中文译文 · 机器初译**

未来工作的关键领域。此外，Co-Scientist的假设的验证虽然成功，但仍属于初步阶段。

### co-scientist-0117

**English original**

Finally, the broader integration of such AI systems into the scientific workflow requires careful consideration of potential bias, which could risk diminishing critical thinking or homogenizing research directions. While AI has the potential to democratize access to scientific information, particularly in resource-limited settings, it is essential to develop robust verification methods and maintain rigorous peer review to ensure that AI can augment, rather than replace, human scientific reasoning and creativity. Improper use of such AI systems without rigorous peer-review and guardrails could also lead to worsening of the scientific reproducibility crisis through production of low quality scientific artifacts. Further details regarding safety and ethical implications are provided in Supplementary Note 7.

**中文译文 · 机器初译**

最后，将这些人工智能系统更广泛地融入科学工作流程时，必须仔细考虑其潜在的偏见问题，因为这种偏见可能会削弱批判性思维或使研究方向趋于同质化。虽然人工智能有潜力在资源有限的环境中实现科学信息的普及，但必须开发可靠的验证方法并坚持严格的同行评审机制，以确保人工智能能够辅助而非取代人类的科学推理与创造力。
如果没有严格的同行评审和约束机制，不当使用此类人工智能系统可能会导致科学可重复性危机进一步恶化，进而产生低质量的科学成果。关于安全性和伦理影响的更多细节请参阅补充注释7。

### co-scientist-0118

**English original**

The continued development of Co-Scientist will focus on three key areas. Immediate improvements will target the system’s robustness by enhancing learning and knowledge base, literature search capabilities to broaden access, implementing more rigorous fact-checking against external databases and tools, and improving citation recall. Future advancements will focus on expanding the system’s core capabilities. This includes integrating agents that can directly reason over public databases and multimodal data, enabling bioinformatics and data science tasks. The implementation of reinforcement learning from human and experimental feedback could further optimize the hypothesis generation and refinement process.

**中文译文 · 机器初译**

Co-Scientist 的持续发展将聚焦于三个关键领域。即立即改进系统的鲁棒性，包括增强学习能力和知识库、扩大信息获取范围的文献搜索功能、对外部数据库和工具进行更严格的事实核查，以及提升引用信息的召回率。未来的进展则将集中在扩展系统的核心能力上，其中包括整合能够直接对公共数据库和多模态数据进行推理的智能体，从而支持生物信息学和数据科学任务。
从人类和实验反馈中实施强化学习，能够进一步优化假设生成与完善过程。

### co-scientist-0119

**English original**

Expanded evaluations are also necessary to assess Co-Scientist’s generalizability across a wider range of scientific disciplines. This requires developing more objective and automated evaluation metrics that move beyond current ranking systems and engaging a larger cohort of domain experts to stress-test the system with diverse and complex research queries.

**中文译文 · 机器初译**

还需要进行更广泛的评估，以检验联合科学家在更多科学领域中的泛化能力。这需要制定更客观、自动化的评估指标，超越当前的排名系统，并邀请更多领域专家参与，通过多样且复杂的研究问题对系统进行压力测试。

### co-scientist-0120

**English original**

In the fullness of time, integrating Co-Scientist with laboratory automation platforms could create a closed-loop, autonomous system for hypothesis generation, experimental validation, and iterative learning, significantly accelerating the pace of scientific discovery.

**中文译文 · 机器初译**

在适当时机，将 Co-Scientist 与实验室自动化平台整合起来，可以构建出一个闭环、自主的系统，用于假设生成、实验验证和迭代学习，从而显著加快科学发现的速度。

### co-scientist-0121

**English original**

Conclusion

**中文译文 · 机器初译**

结论

### co-scientist-0122

**English original**

Co-Scientist represents a promising step towards AI-assisted augmentation of scientists and acceleration of scientific discovery. Its ability to think scientifically, generate novel testable hypotheses across diverse scientific and biomedical domains, some supported by experimental findings, along with the capacity for recursive self-improvement with increasing compute, demonstrates the promise of meaningfully accelerating scientists’ endeavors to resolve grand challenges in human health, medicine and science. This innovation opens numerous questions and opportunities. Applying the empiric and responsible approach of science to Co-Scientist itself can thereby enable safe exploration of its undoubted potential, including how collaborative and human-centred AI systems might be able to augment human ingenuity and accelerate scientific discovery.

**中文译文 · 机器初译**

Co-Scientist 为借助人工智能辅助科学家工作以及加速科学发现提供了有前景的途径。它具备科学思考能力，能够在不同的科学和生物医学领域生成新的可验证假设（其中一些还得到了实验结果的支持），并且能够通过增加计算资源实现递归式自我改进，这充分表明它能够有效推动科学家在解决人类健康、医学和科学领域重大挑战方面取得进展。这一创新引发了诸多问题与机遇。
将科学的经验性与责任性方法应用于“联合科学家”本身，能够使得对其无疑巨大的潜力进行安全探索成为可能，包括如何让协作型以人类为中心的AI系统增强人类创造力并加速科学发现。


### 原文第 26 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=26)

### co-scientist-0124

**English original**

References

**中文译文 · 机器初译**

参考文献

### co-scientist-0125

**English original**

1.​ Guan, Y. et al. AI-assisted drug re-purposing for human liver fibrosis. Adv. Sci. 12, e08751

**原文保留（专名、技术内容或文献信息） · 保留原文**

1.​ Guan, Y. et al. AI-assisted drug re-purposing for human liver fibrosis. Adv. Sci. 12, e08751

### co-scientist-0126

**English original**

(2025).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2025).

### co-scientist-0127

**English original**

2.​ Penadés, J. R. et al. AI mirrors experimental science to uncover a novel mechanism of gene

**原文保留（专名、技术内容或文献信息） · 保留原文**

2.​ Penadés, J. R. et al. AI mirrors experimental science to uncover a novel mechanism of gene

### co-scientist-0128

**English original**

transfer crucial to bacterial evolution. Cell 188, 6654–6665 (2025).

**原文保留（专名、技术内容或文献信息） · 保留原文**

transfer crucial to bacterial evolution. Cell 188, 6654–6665 (2025).

### co-scientist-0129

**English original**

3.​ Jinek, M. et al. A programmable dual-RNA-guided DNA endonuclease in adaptive bacterial

**原文保留（专名、技术内容或文献信息） · 保留原文**

3.​ Jinek, M. et al. A programmable dual-RNA-guided DNA endonuclease in adaptive bacterial

### co-scientist-0130

**English original**

immunity. Science 337, 816–821 (2012).

**原文保留（专名、技术内容或文献信息） · 保留原文**

immunity. Science 337, 816–821 (2012).

### co-scientist-0131

**English original**

4.​ Hopfield, J. J. Neural networks and physical systems with emergent collective

**原文保留（专名、技术内容或文献信息） · 保留原文**

4.​ Hopfield, J. J. Neural networks and physical systems with emergent collective

### co-scientist-0132

**English original**

computational abilities. Proc. Natl Acad. Sci. USA 79, 2554–2558 (1982).

**原文保留（专名、技术内容或文献信息） · 保留原文**

computational abilities. Proc. Natl Acad. Sci. USA 79, 2554–2558 (1982).

### co-scientist-0133

**English original**

5.​ Hinton, G. E. & Sejnowski, T. J. in Parallel Distributed Processing: Explorations in the

**原文保留（专名、技术内容或文献信息） · 保留原文**

5.​ Hinton, G. E. & Sejnowski, T. J. in Parallel Distributed Processing: Explorations in the

### co-scientist-0134

**English original**

Microstructure of Cognition Vol. 1 (eds Feldman, J. A. et al.) 282–317 (MIT Press, 1986).

**原文保留（专名、技术内容或文献信息） · 保留原文**

Microstructure of Cognition Vol. 1 (eds Feldman, J. A. et al.) 282–317 (MIT Press, 1986).

### co-scientist-0135

**English original**

6.​ Guo, D. et al. DeepSeek-R1 incentivizes reasoning in LLMs through reinforcement

**原文保留（专名、技术内容或文献信息） · 保留原文**

6.​ Guo, D. et al. DeepSeek-R1 incentivizes reasoning in LLMs through reinforcement

### co-scientist-0136

**English original**

learning. Nature 645, 633–638 (2025).

**原文保留（专名、技术内容或文献信息） · 保留原文**

learning. Nature 645, 633–638 (2025).

### co-scientist-0137

**English original**

7.​ Jaech, A. et al. OpenAI O1 system card. Preprint at https://arxiv.org/abs/2412.16720 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

7.​ Jaech, A. et al. OpenAI O1 system card. Preprint at https://arxiv.org/abs/2412.16720 (2024).

### co-scientist-0138

**English original**

8.​ Gemini Team, Google. Gemini 1.5: unlocking multimodal understanding across millions of

**原文保留（专名、技术内容或文献信息） · 保留原文**

8.​ Gemini Team, Google. Gemini 1.5: unlocking multimodal understanding across millions of

### co-scientist-0139

**English original**

tokens of context. Preprint at https://arxiv.org/abs/2403.05530 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

tokens of context. Preprint at https://arxiv.org/abs/2403.05530 (2024).

### co-scientist-0140

**English original**

9.​ Wiesinger, J., Marlow, P. & Vuskovic, V. Agents. kaggle https://www.kaggle.com/

**原文保留（专名、技术内容或文献信息） · 保留原文**

9.​ Wiesinger, J., Marlow, P. & Vuskovic, V. Agents. kaggle https://www.kaggle.com/

### co-scientist-0141

**English original**

whitepaper-agents (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

whitepaper-agents (2024).

### co-scientist-0142

**English original**

10.​ Hinton, G. E., Vinyals, O. & Dean, J. Distilling the knowledge in a neural network. Preprint

**原文保留（专名、技术内容或文献信息） · 保留原文**

10.​ Hinton, G. E., Vinyals, O. & Dean, J. Distilling the knowledge in a neural network. Preprint

### co-scientist-0143

**English original**

at https://arxiv.org/abs/1503.02531 (2015).

**原文保留（专名、技术内容或文献信息） · 保留原文**

at https://arxiv.org/abs/1503.02531 (2015).

### co-scientist-0144

**English original**

11.​ Gemma Team, Google. Gemma: open models based on gemini research and technology.

**原文保留（专名、技术内容或文献信息） · 保留原文**

11.​ Gemma Team, Google. Gemma: open models based on gemini research and technology.

### co-scientist-0145

**English original**

Preprint at https://arxiv.org/abs/2403.08295 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

Preprint at https://arxiv.org/abs/2403.08295 (2024).

### co-scientist-0146

**English original**

12.​ Leslie, D. et al. ‘Frontier AI,’ power, and the public interest: who benefits, who decides?

**原文保留（专名、技术内容或文献信息） · 保留原文**

12.​ Leslie, D. et al. ‘Frontier AI,’ power, and the public interest: who benefits, who decides?


### 原文第 27 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=27)

### co-scientist-0148

**English original**

Harvard Data Sci. Rev. https://doi.org/10.1162/99608f92.4a42495c (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

Harvard Data Sci. Rev. https://doi.org/10.1162/99608f92.4a42495c (2024).

### co-scientist-0149

**English original**

13.​ Chen, L. et al. Are more LLM calls all you need? Towards the scaling properties of

**原文保留（专名、技术内容或文献信息） · 保留原文**

13.​ Chen, L. et al. Are more LLM calls all you need? Towards the scaling properties of

### co-scientist-0150

**English original**

compound AI systems. Adv. Neural Inform. Process. Syst. 37, 45767–45790 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

compound AI systems. Adv. Neural Inform. Process. Syst. 37, 45767–45790 (2024).

### co-scientist-0151

**English original**

14.​ Comanici, G. et al. Gemini 2.5: pushing the frontier with advanced reasoning,

**原文保留（专名、技术内容或文献信息） · 保留原文**

14.​ Comanici, G. et al. Gemini 2.5: pushing the frontier with advanced reasoning,

### co-scientist-0152

**English original**

multimodality, long context, and next generation agentic capabilities. Preprint at

**原文保留（专名、技术内容或文献信息） · 保留原文**

multimodality, long context, and next generation agentic capabilities. Preprint at

### co-scientist-0153

**English original**

https://arxiv.org/abs/2507.06261 (2025).

**原文保留（专名、技术内容或文献信息） · 保留原文**

https://arxiv.org/abs/2507.06261 (2025).

### co-scientist-0154

**English original**

15.​ Gower, B. Scientific Method: a Historical and Philosophical Introduction (Routledge,

**原文保留（专名、技术内容或文献信息） · 保留原文**

15.​ Gower, B. Scientific Method: a Historical and Philosophical Introduction (Routledge,

### co-scientist-0155

**English original**

2012).

**原文保留（专名、技术内容或文献信息） · 保留原文**

2012).

### co-scientist-0156

**English original**

16.​ Snell, C., Lee, J., Xu, K. & Kumar, A. Scaling LLM test-time compute optimally can be

**原文保留（专名、技术内容或文献信息） · 保留原文**

16.​ Snell, C., Lee, J., Xu, K. & Kumar, A. Scaling LLM test-time compute optimally can be

### co-scientist-0157

**English original**

more effective than scaling parameters for reasoning. In International Conference on

**原文保留（专名、技术内容或文献信息） · 保留原文**

more effective than scaling parameters for reasoning. In International Conference on

### co-scientist-0158

**English original**

Learning Representations (ICLR) (2025).

**原文保留（专名、技术内容或文献信息） · 保留原文**

Learning Representations (ICLR) (2025).

### co-scientist-0159

**English original**

17.​ Brown, N. & Sandholm, T. Superhuman AI for multiplayer poker. Science 365, 885–890

**原文保留（专名、技术内容或文献信息） · 保留原文**

17.​ Brown, N. & Sandholm, T. Superhuman AI for multiplayer poker. Science 365, 885–890

### co-scientist-0160

**English original**

(2019).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2019).

### co-scientist-0161

**English original**

18.​ Silver, D. et al. Mastering the game of Go with deep neural networks and tree search.

**原文保留（专名、技术内容或文献信息） · 保留原文**

18.​ Silver, D. et al. Mastering the game of Go with deep neural networks and tree search.

### co-scientist-0162

**English original**

Nature 529, 484–489 (2016).

**原文保留（专名、技术内容或文献信息） · 保留原文**

Nature 529, 484–489 (2016).

### co-scientist-0163

**English original**

19.​ Ringel, M. S., Scannell, J. W., Baedeker, M. & Schulze, U. Breaking Eroom’s law. Nat. Rev.

**原文保留（专名、技术内容或文献信息） · 保留原文**

19.​ Ringel, M. S., Scannell, J. W., Baedeker, M. & Schulze, U. Breaking Eroom’s law. Nat. Rev.

### co-scientist-0164

**English original**

Drug Discov. 19, 833–834 (2020).

**原文保留（专名、技术内容或文献信息） · 保留原文**

Drug Discov. 19, 833–834 (2020).

### co-scientist-0165

**English original**

20.​ Pushpakom, S. et al. Drug repurposing: progress, challenges and recommendations. Nat.

**原文保留（专名、技术内容或文献信息） · 保留原文**

20.​ Pushpakom, S. et al. Drug repurposing: progress, challenges and recommendations. Nat.

### co-scientist-0166

**English original**

Rev. Drug Discov. 18, 41–58 (2019).

**原文保留（专名、技术内容或文献信息） · 保留原文**

Rev. Drug Discov. 18, 41–58 (2019).

### co-scientist-0167

**English original**

21.​ He, L. et al. Chimeric infective particles expand species boundaries in phage-inducible

**原文保留（专名、技术内容或文献信息） · 保留原文**

21.​ He, L. et al. Chimeric infective particles expand species boundaries in phage-inducible

### co-scientist-0168

**English original**

chromosomal island mobilization. Cell 188, 6636–6653 (2025).

**原文保留（专名、技术内容或文献信息） · 保留原文**

chromosomal island mobilization. Cell 188, 6636–6653 (2025).

### co-scientist-0169

**English original**

22.​ Döhner, H., Weisdorf, D. J. & Bloomfield, C. D. Acute myeloid leukemia. N. Engl. J. Med.

**原文保留（专名、技术内容或文献信息） · 保留原文**

22.​ Döhner, H., Weisdorf, D. J. & Bloomfield, C. D. Acute myeloid leukemia. N. Engl. J. Med.

### co-scientist-0170

**English original**

373, 1136–1152 (2015).

**原文保留（专名、技术内容或文献信息） · 保留原文**

373, 1136–1152 (2015).


### 原文第 28 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=28)

### co-scientist-0172

**English original**

23.​ Guo, Q. et al. NF-κB in biology and targeted therapy: new insights and translational

**原文保留（专名、技术内容或文献信息） · 保留原文**

23.​ Guo, Q. et al. NF-κB in biology and targeted therapy: new insights and translational

### co-scientist-0173

**English original**

implications. Signal Transduc. Target. Ther. 9, 53 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

implications. Signal Transduc. Target. Ther. 9, 53 (2024).

### co-scientist-0174

**English original**

24.​ Maiti, A. et al. Phase II trial of MEK inhibitor binimetinib (MEK162) in RAS-mutant acute

**原文保留（专名、技术内容或文献信息） · 保留原文**

24.​ Maiti, A. et al. Phase II trial of MEK inhibitor binimetinib (MEK162) in RAS-mutant acute

### co-scientist-0175

**English original**

myeloid leukemia. Clin. Lymphoma Myeloma Leuk. 19, 142–148 (2019).

**原文保留（专名、技术内容或文献信息） · 保留原文**

myeloid leukemia. Clin. Lymphoma Myeloma Leuk. 19, 142–148 (2019).

### co-scientist-0176

**English original**

25.​ Philippe, C. et al. Pivotal role of the endoplasmic reticulum stress-related

**原文保留（专名、技术内容或文献信息） · 保留原文**

25.​ Philippe, C. et al. Pivotal role of the endoplasmic reticulum stress-related

### co-scientist-0177

**English original**

XBP1s/miR-22/SIRT1 axis in acute myeloid leukemia apoptosis and response to

**原文保留（专名、技术内容或文献信息） · 保留原文**

XBP1s/miR-22/SIRT1 axis in acute myeloid leukemia apoptosis and response to

### co-scientist-0178

**English original**

chemotherapy. Leukemia 38, 1764–1776 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

chemotherapy. Leukemia 38, 1764–1776 (2024).

### co-scientist-0179

**English original**

26.​ Guan, Y. et al. A human multi-lineage hepatic organoid model for liver fibrosis.Nat.

**原文保留（专名、技术内容或文献信息） · 保留原文**

26.​ Guan, Y. et al. A human multi-lineage hepatic organoid model for liver fibrosis.Nat.

### co-scientist-0180

**English original**

Commun. 12, 6138 (2021).

**原文保留（专名、技术内容或文献信息） · 保留原文**

Commun. 12, 6138 (2021).

### co-scientist-0181

**English original**

27.​ Guan, Y. et al. Live-cell imaging of human liver fibrosis using hepatic micro-organoids. JCI

**原文保留（专名、技术内容或文献信息） · 保留原文**

27.​ Guan, Y. et al. Live-cell imaging of human liver fibrosis using hepatic micro-organoids. JCI

### co-scientist-0182

**English original**

Insight 10, e187099 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

Insight 10, e187099 (2024).


### 原文第 29 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=29)

### co-scientist-0184

**English original**

Methods

**中文译文 · 机器初译**

方法

### co-scientist-0185

**English original**

Overview of Co-Scientist architecture. Co-Scientist employs a multi-agent architecture built upon Google’s Gemini. In this study, we used Gemini 2.0 models as the base foundational LLM for all agents 14, integrated within an asynchronous task execution framework. This framework allows for flexible scaling of test-time compute resources, facilitating advanced scientific thinking and reasoning. Given a research goal specified by an expert scientist in natural language, Co-Scientist generates hypotheses that adhere to the following default criteria: (1) Alignment with the provided research goal. The generated outputs must precisely align with the research goals, preferences and constraints defined by the scientist. (2) Plausibility. The system outputs should be free of readily apparent flaws. Any potential contradictions with prior literature or established knowledge must be explicitly stated and justified. (3) Novelty. A key objective of Co-Scientist is to generate novel hypotheses, conjectures, and research plans grounded in prior literature, rather than simply synthesizing existing information (a capability already addressed by existing “deep research” tools 28). (4) Testability. The system outputs should be amenable to empirical validation within the constraints specified by the scientist. (5) Safety. The system outputs will be controlled to prevent enabling unsafe, unethical, or harmful research. Aside from these default criteria, Co-Scientist can be configured with additional criteria, preferences, and constraints as needed. For instance, it can be configured to generate outputs in formats preferred by the researcher to improve interpretability and readability. ​ At a high level, Co-Scientist comprises four key components: (1) Natural language input-output (IO) interface. Scientists interact with and supervise the system primarily through natural language. This allows them to not only define the initial research goal but also refine it at any time, provide feedback on generated hypotheses (including their own solutions), and generally steer and guide the system’s progress. (2) Asynchronous task framework. Co-Scientist employs a multi-agent system where specialized agents operate as worker processes within an asynchronous, continuous, and configurable task execution framework. A dedicated Supervisor agent manages the worker task queue, assigns specialized agents to these processes, and allocates resources. This design enables the system to flexibly and effectively utilize computational resources and iteratively improve its scientific reasoning and quality of hypotheses. (3) Specialized agents. Following inductive biases and scientific priors derived from the scientific method, the process of scientific reasoning and hypothesis generation is broken down into sub-tasks. Individual, specialized agents, each equipped with customized instruction prompts, are designed to execute these sub-tasks. These agents operate as workers coordinated by the Supervisor agent. (4) Context memory. In order to enable iterative computation and scientific reasoning over long time horizons, Co-Scientist uses a persistent context memory to store and retrieve states of the agents and the system during the course of the computation. The specific Co-Scientist design was arrived at with iterative developments and feedback from expert scientists and is reflective of the current capabilities of the underlying LLMs. Co-Scientist multi-agent architecture is depicted and summarized in Fig. 1b.

**中文译文 · 机器初译**

大语言模型协同科学家架构概述。Co-Scientist采用了基于谷歌Gemini的多智能体架构。在本研究中，我们将Gemini 2.0模型作为所有智能体的基础大语言模型，并将其整合到异步任务执行框架中。该框架能够灵活调整测试阶段的计算资源规模，从而促进高级科学思维与推理。当专家科学家以自然语言指定研究目标后，Co-Scientist会生成符合以下默认标准的假设：(1) 与所指定的研究目标一致。
生成的成果必须与科学家所定义的研究目标、偏好和约束条件完全一致。(2) 合理性。系统输出的内容应无明显缺陷，任何与先前文献或已知知识相矛盾的之处都必须明确说明并给出理由。(3) 新颖性。Co-Scientist 的关键目标在于基于现有文献生成新的假设、猜想和研究计划，而非仅仅整合现有信息（这一功能已由现有的“深度研究”工具实现）。(4) 可验证性。
系统输出应在科学家规定的限制范围内便于通过实证验证。（5）安全性。系统输出将被控制，以防止开展不安全、不道德或有害的研究。除了这些默认标准外，可以根据需要为 Co-Scientist 配置额外的标准、偏好和限制。例如，可以配置其生成符合研究人员偏好格式的输出，以提高可解释性和可读性。总体而言，Co-Scientist 包含四个关键组件：（1）自然语言输入输出（IO）接口。科学家主要通过自然语言与系统互动并对其进行监督。
这使他们不仅能够定义初始研究目标，还能随时对其进行优化调整，对生成的假设（包括自己的解决方案）提供反馈，并总体上引导和指导系统的进展。(2) 异步任务框架。Co-Scientist采用多智能体系统，其中专业智能体作为异步、连续且可配置的任务执行框架中的工作进程运行。专门的监督智能体负责管理工作任务队列，将专业智能体分配至这些进程，并分配资源。
该设计使系统能够灵活且有效地利用计算资源，并逐步提升其科学推理能力和假设质量。(3) 专用智能体。根据科学方法所推导出的归纳偏见与科学先验知识，科学推理和假设生成过程被分解为多个子任务。每个配备定制指令提示的专用智能体负责执行这些子任务，这些智能体由主管智能体协调运作。(4) 上下文记忆。
为了支持长期范围内的迭代计算与科学推理，Co-Scientist 使用持久上下文记忆来在计算过程中存储和检索智能体及系统的状态。该特定版本的 Co-Scientist 设计是通过迭代开发以及专家科学家的反馈逐步形成的，反映了底层大语言模型当前的能力水平。Co-Scientist 多智能体架构如图 1b 所示并进行了总结。


### 原文第 30 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=30)

### co-scientist-0187

**English original**

Throughout the following section, we employ a recurring example: generating hypotheses for exploring the biological mechanisms of Amyotrophic Lateral Sclerosis (ALS) to illustrate the various components of Co-Scientist. While this example has been reviewed by domain experts, it remains illustrative and may contain errors. Importantly, this example does not aim to suggest potential therapeutic avenues for ALS and should be interpreted with utmost caution. We have also provided the pseudocode demonstrating agent logic in Supplementary Note 8. All the prompts used in the agents are listed in Supplementary Note 9, and all the examples are listed in the Supplementary Note 10.

**中文译文 · 机器初译**

在接下来的部分中，我们采用一个常见的示例：生成关于肌萎缩侧索硬化症（ALS）生物学机制的各种假设，以说明“联合科学家”系统的不同组成部分。虽然该示例已得到领域专家的审核，但它仍具有说明性，可能包含错误。重要的是，该示例并非旨在提出针对 ALS 的潜在治疗途径，应谨慎解读。我们在补充注释 8 中提供了展示智能体逻辑的伪代码。所有在智能体中使用的提示语均列于补充注释 9，所有示例则列于补充注释 10。

### co-scientist-0188

**English original**

From research goal to research plan configuration. The research goal, specified by the scientist, serves as the entry point to Co-Scientist. Leveraging the multimodal and long context capabilities of Gemini models, Co-Scientist efficiently processes research goals of varying complexity, from simple statements to extensive documents spanning tens of thousands of natural language tokens or other relevant data (e.g., including hundreds of prior publication PDFs). The research goal may also incorporate specific constraints, attributes, and preferences related to the scientist’s particular laboratory setting or field of work.

**中文译文 · 机器初译**

从研究目标到研究计划配置。由科学家指定的研究目标作为与协同科学家交互的入口点。利用 Gemini 模型的多模态及长上下文能力，协同科学家能够高效处理各种复杂程度的研究目标，涵盖从简单陈述到包含数万自然语言标记或其他相关数据（例如数百份先前出版物 PDF）的庞大文档。研究目标还可能包含与科学家特定实验室环境或工作领域相关的特定约束、属性和偏好。

### co-scientist-0189

**English original**

Co-Scientist then parses the goal to derive a research plan configuration for generating research proposals. This configuration captures the desired proposal preferences, attributes, and constraints. For example, it specifies whether Co-Scientist should exclusively propose novel hypotheses. It also specifies the criteria for evaluating hypothesis quality, such as novelty and experimental feasibility. These criteria are then used by the system during its auto-evaluation, tournament debates and self-improvement phases. The attributes, preferences, and evaluation criteria can all be customized to a given research goal. To illustrate this process, we present an example research goal and its corresponding parsed research plan configuration in Supplementary Note 10.1, where the goal is to develop a novel hypothesis related to phosphorylation of the Nuclear Pore Complex (NPC) as a causative mechanism for ALS 29.

**中文译文 · 机器初译**

协同科学家随后解析目标，以制定生成研究提案的研究计划配置。该配置包含了所需的提案偏好、属性和约束条件。例如，它明确说明协同科学家是否应仅提出新颖的假设，同时还规定了评估假设质量的标准，如新颖性和实验可行性。这些标准将在系统的自动评估、竞赛辩论及自我改进阶段中被使用。属性、偏好和评估标准都可以根据具体的研究目标进行定制。
为了说明这一过程，我们在补充注释 10.1 中给出了一个研究目标及其对应的研究计划配置示例，该目标是提出一项关于核孔复合体（NPC）磷酸化作用作为 ALS 29 致病机制的新型假设。

### co-scientist-0190

**English original**

Based on the research plan configuration, the Supervisor agent initiates the creation of a task queue and begins orchestrating the specialized agents. The system operates continuously and asynchronously. Periodically, the Supervisor agent calculates a comprehensive set of summary statistics, reflecting the system’s state and progress toward the specified research goal. These statistics inform decisions regarding resource allocation and the determination of whether a terminal state for the overall computation has been reached. The state is periodically written to the associated context memory of the system and leveraged as feedback in subsequent rounds of computation. It also enables easy restarts in case of any failure in the system components.

**中文译文 · 机器初译**

根据研究计划配置，主管智能体启动任务队列的创建工作，并开始协调各专业智能体。系统以连续且异步的方式运行。定期地，主管智能体会生成一套全面的汇总统计信息，反映系统的状态以及实现指定研究目标所取得的进展。这些统计信息用于指导资源分配决策，并决定整体计算是否已达到最终状态。该状态会定期写入系统的相关上下文内存中，并在后续的计算过程中作为反馈信息使用。
它还能在系统组件出现任何故障时实现轻松重启。

### co-scientist-0191

**English original**

The specialized agents underpinning Co-Scientist. At the heart of Co-Scientist are a coalition of specialized agents, each orchestrated by the Supervisor agent. These agents are designed to emulate the scientific reasoning process, enabling them to generate novel hypotheses and research plans. Each agent is provided a “library of strategies”, (i.e. a collection of prompts) to better explain and help it perform its assigned task. They are also equipped to interact with and

**中文译文 · 机器初译**

支撑 Co-Scientist 的专业智能体。Co-Scientist 的核心是由多个专业智能体组成的联盟，每个智能体都由主管智能体进行协调。这些智能体旨在模拟科学推理过程，使其能够生成新的假设和研究计划。每个智能体都拥有一个“策略库”（即一系列提示词），以便更好地解释并协助其完成分配的任务。它们还具备与系统交互的能力


### 原文第 31 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=31)

### co-scientist-0193

**English original**

utilize external tools, such as web search engines and specialized AI models, through application programming interfaces (APIs). These specialized agents are enumerated below: (1) Generation agent. The agent initiates the research process by generating the initial focus areas, iteratively extending them and generating a set of initial hypotheses and proposals that address the research goal. This involves exploring relevant literature using web search, synthesizing existing findings into novel directions, and engaging in simulated scientific debates for iterative improvement. (2) Reflection agent. This agent simulates the role of a scientific peer reviewer, critically examining the correctness, quality, and novelty of the generated hypotheses and research proposals. Furthermore, it evaluates the potential of each hypothesis to provide an improved explanation for existing research observations (identified via literature search and review), particularly those that may be under-explained. (3) Ranking agent. An important abstraction in Co-Scientist is the notion of a tournament where different research proposals are evaluated, debated and ranked enabling iterative improvements. The Ranking agent employs and orchestrates an Elo-based tournament 30 to assess and prioritize the generated hypotheses at any given time. This involves pairwise comparisons, facilitated by simulated scientific debates, which allow for a nuanced evaluation of the relative merits of each hypothesis. (4) Proximity agent. This agent asynchronously computes a proximity graph for generated hypotheses, enabling clustering of similar ideas, de-duplication, and efficient exploration of the hypothesis landscape. (5) Evolution agent. Co-Scientist’s iterative improvement capability relies heavily on this agent, which continuously refines the top-ranked hypotheses emerging from the tournament. Its refinement strategies include synthesizing existing ideas, using analogies, leveraging literature for supporting details, exploring unconventional reasoning, and simplifying concepts for clarity. (6) Meta-review agent. This agent also enables Co-Scientist’s continuous improvement by synthesizing insights from all reviews, identifying recurring patterns in tournament debates, and using these findings to optimize other agents’ performance in subsequent iterations. This also enhances the quality and relevance of generated hypotheses and reviews in subsequent iterations. At the end of the Co-Scientist computation process, this agent also synthesizes top-ranked hypotheses and reviews into a comprehensive research overview for review by the scientist.

**中文译文 · 机器初译**

通过应用程序编程接口（API）利用网络搜索引擎和专用人工智能模型等外部工具。这些专用智能体如下：(1) 生成智能体。该智能体通过生成初始研究重点领域来启动研究过程，随后逐步扩展这些领域，并生成一系列针对研究目标的初始假设与建议。这涉及使用网络搜索探索相关文献，将现有研究成果整合为新的研究方向，以及参与模拟科学辩论以进行迭代改进。(2) 反思智能体。
该智能体模拟科学同行评审者的角色，对生成的假设与研究提案的正确性、质量及新颖性进行严格审查。此外，它还会评估每个假设在为现有研究观察结果（通过文献检索与综述确定）提供更完善解释方面的潜力，尤其是那些可能尚未得到充分解释的假设。（3）排名智能体。Co-Scientist 中的一个重要抽象概念是竞赛机制，即对不同研究提案进行评估、讨论和排序，从而实现迭代改进。
排名智能体采用基于 Elo 的竞赛机制来评估和优先处理任何时刻生成的假设，该机制通过模拟科学辩论进行成对比较，从而能够细致地评价每个假设的相对优势。(4) 邻近智能体。该智能体异步计算生成假设的邻近关系图，从而实现相似观点的聚类、去重以及对假设领域的高效探索。(5) 进化智能体。Co-Scientist 的迭代优化能力在很大程度上依赖于此智能体，它不断优化从竞赛中产生的排名最高的假设。
其优化策略包括整合现有观点、运用类比、利用文献提供支撑细节、探索非传统推理方式，以及简化概念以提升清晰度。（6）元评估智能体。该智能体还能通过整合所有评审的见解、识别竞赛讨论中的重复模式，并利用这些发现来优化后续迭代中其他智能体的表现，从而推动共同科学家持续改进。这还能提升后续迭代中生成的假设与评审内容的质量和相关性。
在联合科学家计算流程结束时，该智能体还会整合排名靠前的假设，并整理成一份全面的研究综述，供科学家审核。

### co-scientist-0194

**English original**

The Supervisor agent’s seamless orchestration of these specialized agents enables the development of valid, novel, and testable hypotheses and research plans tailored to the input research goal provided by the scientist.

**中文译文 · 机器初译**

主管智能体对这些专业智能体的无缝协调，使得能够开发出符合科学家所提出的研究目标、具有有效性、新颖性且可验证的假设及研究计划。

### co-scientist-0195

**English original**

In summary, the Generation agent curates an initial list of research hypotheses satisfying a research goal. These are then reviewed by the Reflection agent and evaluated in a tournament by the Ranking agent orchestrating debate matches involving the hypothesis. The Evolution, Proximity, and Meta-review agents operate on the tournament state to help improve the quality of the system outputs.

**中文译文 · 机器初译**

总结来说，生成智能体会整理出符合研究目标的初始研究假设列表。这些假设随后由反思智能体进行审核，并由排名智能体通过辩论比赛对它们进行评估。进化、邻近性和元评估智能体则根据比赛结果来运作，以帮助提升系统输出的质量。

### co-scientist-0196

**English original**

The Supervisor agent periodically computes and writes to the context memory, a comprehensive suite of statistics, including the number of hypotheses generated and requiring review, and the progress of the tournament. These statistics also include analyses of the effectiveness of different hypothesis generation methodologies (e.g., generating new ideas via

**中文译文 · 机器初译**

主管智能体定期计算并写入上下文内存中，其中包含一系列综合统计数据，包括生成的待审核假设数量以及锦标赛的进展情况。这些统计数据还包括对不同假设生成方法的有效性分析（例如通过生成新想法的方式）


### 原文第 32 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=32)

### co-scientist-0198

**English original**

the Generation agent vs. improving existing ideas via the Evolution agent). Based on these statistics, the Supervisor agent then orchestrates subsequent system operations, i.e., generating new hypotheses, reviews, tournaments, and improvements to existing hypotheses, by strategically weighting and sampling the specialized agents for execution via the worker processes.

**中文译文 · 机器初译**

生成智能体与通过进化智能体改进现有方案之间的对比。基于这些统计数据，监督智能体随后会协调后续的系统操作，即生成新的假设、进行评审、举办竞赛以及对现有假设进行改进，其方式是通过对各专业智能体进行策略性加权与采样，从而通过工作进程执行相关操作。

### co-scientist-0199

**English original**

Importantly, the Meta-review agent enables feedback propagation and learning without back-propagation techniques (e.g., fine-tuning or reinforcement learning) 31. The Meta-review agent generates feedback applicable to all agents, which is simply appended to their prompts in the next iteration—a capability facilitated by the long-context search and reasoning capabilities of the underlying Gemini models. Through this feedback loop, Co-Scientist continuously learns and improves in subsequent iterations with more compute scaling.

**中文译文 · 机器初译**

重要的是，Meta-review智能体能够无需使用反向传播技术（如微调或强化学习）即可实现反馈传递与学习 31。该智能体生成的反馈适用于所有智能体，只需在下一轮中将其附加到它们的提示中即可——这一能力得益于底层 Gemini 模型的长上下文检索与推理功能。通过这种反馈循环，Co-Scientist 能够在后续迭代中随着计算能力的提升不断学习并改进。

### co-scientist-0200

**English original**

Finally, while our work leverages Gemini 2.0, Co-Scientist framework is model-agnostic and portable to other similar models or combinations thereof. Future LLM improvements like our Gemini 3 models will further enhance Co-Scientist’s capabilities to generate novel scientific hypotheses and perform complex tasks over long time horizons.

**中文译文 · 机器初译**

最后，虽然我们的研究基于 Gemini 2.0，但 Co-Scientist 框架具有模型无关性，可以移植到其他类似的模型或其组合上。未来如 Gemini 3 模型这样的大语言模型改进，将进一步提升 Co-Scientist 生成新颖科学假设以及在长期范围内执行复杂任务的能力。

### co-scientist-0201

**English original**

Generation agent. The Generation agent employs a diverse array of strategies (encoded as prompts), techniques and tools to generate novel hypotheses, such as the following: ●​ Literature exploration via web search. The agent iteratively searches the web, retrieves and reads relevant research articles, learns about topics and grounds its reasoning by summarizing prior work and building a knowledge base of scientific facts. It then builds on this summary to generate novel hypotheses and research plans. An example prompt is given in Supplementary Note 9.1. ●​ Simulated scientific debates. Here, the Generation agent simulates scientific debates among experts by employing self-critique and self-play techniques. These debates typically involve multiple turns of conversations leading to a refined hypothesis generated at the end. An example prompt is given in Supplementary Note 9.1. ●​ Iterative assumptions identification. The agent iteratively identifies testable intermediate assumptions, which, if proven true, can lead to novel scientific discovery.

**中文译文 · 机器初译**

生成智能体。该生成智能体采用多种策略（以提示词形式编码）、技术和工具来生成新的假设，例如：● 通过网络搜索进行文献探索。该智能体会反复搜索网络，检索并阅读相关研究文章，了解相关主题，并通过总结已有工作建立科学事实知识库来支撑其推理过程。随后，它基于这些总结生成新的假设和研究计划。一个示例提示词见补充注释9.1。● 模拟科学辩论。
在此处，生成智能体通过采用自我批评与自我博弈技术，模拟了专家之间的科学辩论。这些辩论通常包含多轮对话，最终产生一个经过完善的假设。示例提示见补充注释 9.1。● 迭代性假设识别。该智能体会逐步识别可验证的中间假设，若这些假设被证实为真，便可能带来新的科学发现。

### co-scientist-0202

**English original**

These plausible assumptions and their sub-assumptions are identified through conditional reasoning hops and subsequently aggregated into complete hypotheses. ●​ Research expansion. To identify previously unexplored areas of the hypothesis space, the Generation agent reviews existing hypotheses and the research overview and feedback provided by the Meta-review agent in the previous iteration. This is used to inform additional exploration directions in the research hypothesis space.

**中文译文 · 机器初译**

这些合理的假设及其子假设通过条件推理步骤被识别出来，随后被汇总为完整的假设。●​ 研究拓展。为了发现假设空间中之前未被探索的领域，生成智能体会回顾现有的假设以及上一次迭代中元评估智能体提供的研究概述与反馈，以此作为研究假设空间中进一步探索方向的依据。

### co-scientist-0203

**English original**

An example hypothesis and research proposal output from the Generation agent is presented in Supplementary Note 10.2 for the aforementioned research goal regarding explaining a basic mechanism related to ALS. The Generation agent also summarizes and categorizes each generated hypothesis, allowing scientists to quickly grasp the core ideas.

**中文译文 · 机器初译**

关于解释与ALS相关基本机制的研究目标，生成智能体输出的一个示例假设及研究提案见补充注释10.2。生成智能体还会对每个生成的假设进行总结和分类，使科学家能够快速理解核心思想。


### 原文第 33 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=33)

### co-scientist-0205

**English original**

Reflection agent. Reviews are integral to Co-Scientist’s effectiveness in generating novel proposals. The Reflection agent searches relevant prior work and data (via web search or a dedicated scientist-provided repository), assesses existing experimental evidence for or against a given hypothesis, and rigorously verifies the novelty, correctness, and quality of generated outputs with tools. Effective reviews filter inaccurate and, when stipulated, non-novel hypotheses. Moreover, they also provide feedback to all other agents, driving continuous improvement. The Reflection agent employs the following types of review strategies: ●​ Initial review. Building on Co-Scientist’s default evaluation criteria, the Reflection agent performs an initial review assessing the correctness, quality, novelty, and a preliminary assessment of safety (ethics) of the generated hypotheses. For a more in-depth discussion on safety considerations see Supplementary Note 7. This initial review, which doesn’t use external tools like web search, aims to quickly discard flawed, non-novel, or otherwise unsuitable hypotheses. ●​ Full review. If a hypothesis passes the initial review, the Reflection agent performs a full review, leveraging external tools and web searches to identify relevant articles for improved reasoning and grounding. This review evaluates the hypothesis's correctness, quality, and novelty similar to the initial review but with full literature search. For correctness and quality, the agent scrutinizes underlying assumptions and reasoning. For novelty, it summarizes known aspects of the hypothesis and then judges their novelty based on existing literature. An example full novelty review, review critiques, and a complete full review example are shown in Supplementary Note 10.3, 10.4 and 10.5, respectively. ●​ Deep verification review. The Reflection agent also conducts a deep verification review, decomposing the hypothesis into constituent assumptions. Each assumption is further broken down into fundamental sub-assumptions, decontextualized, and independently evaluated for correctness to identify invalidating elements for subsequent filtering.

**中文译文 · 机器初译**

反思智能体。评论对于共同科学家提出新建议的有效性至关重要。该反思智能体通过网络搜索或由特定科学家提供的存储库，检索相关的先前研究和数据，评估针对某一假设存在的实验证据，并利用工具严格验证生成结果的创新性、正确性和质量。有效的评论能够过滤掉不准确以及不符合要求的非创新假设，同时还能为所有其他智能体提供反馈，推动持续改进。反思智能体采用以下类型的评论策略：● 初步评论。
基于 Co-Scientist 的默认评估标准，Reflection 智能体进行初步审查，评估所生成的假设的正确性、质量、新颖性以及安全性（伦理）的初步判断。关于安全方面的更深入讨论，请参见补充注释 7。这一初步审查不使用网络搜索等外部工具，旨在快速排除有缺陷、非新颖或不适用的假设。●​ 全面审查。如果某个假设通过初步审查，Reflection 智能体将进行全面审查，利用外部工具和网络搜索来识别相关文献，以完善推理与依据。
本篇评论类似于最初的评论，但进行了全面的文献检索，从而评估该假设的正确性、质量与新颖性。在正确性和质量方面，智能体会仔细审查其基础假设与推理逻辑；在新颖性方面，它先总结该假设已知的方面，然后依据现有文献判断其新颖程度。完整的新型别评论、评论批评示例以及完整的全篇评论示例分别见补充注释 10.3、10.4 和 10.5。●​ 深度验证评论。Reflection 智能体还会进行深度验证评论，将假设分解为各个组成部分的假设。
每个假设都会被进一步分解为基本子假设，进行脱离上下文处理，并独立评估其正确性，以识别后续过滤中需要排除的无效元素。

### co-scientist-0206

**English original**

Concurrently, the reasons for potential hypothesis invalidation due to incorrect assumptions are summarized. This deep verification helps Co-Scientist detect subtle errors within complex hypotheses, such as flaws in reasoning or inaccurate experimental protocols. An identified error doesn’t necessarily invalidate the core hypothesis; the Reflection agent assesses whether the incorrect assumption is fundamental to the hypothesis and incorporates this reasoning into the review. Non-fundamental errors can be addressed during subsequent refinement stages. An example deep verification review is provided in Supplementary Note 10.6 for the previously introduced ALS hypothesis.

**中文译文 · 机器初译**

同时，总结了因错误假设导致潜在假设无效的原因。这种深度验证有助于合作科学家发现复杂假设中的细微错误，例如推理缺陷或不准确的实验方案。被发现的错误并不必然使核心假设无效；反思智能体会评估该错误假设是否对假设至关重要，并将这一分析结果纳入审查中。非关键性的错误可以在后续的优化阶段得到解决。关于之前提出的 ALS 假设，其深度验证审查示例见补充注释 10.6。

### co-scientist-0207

**English original**

We also show another example of a deep verification review via probing questions in the context of drug repurposing for AML in Supplementary Note 10.7. ●​ Observation review. In addition, the Reflection agent also explores whether a given hypothesis can account for long-tail observations from prior experimental results. This review aims to determine if the hypothesis can provide insights on existing experimental findings and observed phenomena within relevant articles. For each observation, the

**中文译文 · 机器初译**

我们在补充注释 10.7 中通过探究性问题展示了另一个关于 AML 药物重新应用的大语言模型深度验证审查示例。●​ 观察性审查。此外，反思智能体还会探讨某个假设是否能够解释先前实验结果中的长尾观察现象。此审查旨在确定该假设能否为相关文章中的现有实验发现和观察现象提供启示。对于每一项观察结果，


### 原文第 34 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=34)

### co-scientist-0209

**English original**

agent assesses if the hypothesis is a superior explanation over existing ones, assuming its validity. Positive observations are summarized and appended to the hypothesis. Note that this review often completes without any important findings (as in the case of the ALS hypothesis example). An example prompt to generate observations is provided in Supplementary Note 9.2. An illustrative example of an observation review is provided in Supplementary Note 10.8 in the context of an alternate hypothesis for explaining a mechanism of anti-microbial resistance. ●​ Simulation review. The Reflection agent also reviews hypotheses by simulating them in a step-wise fashion (e.g., simulating the mechanism of action or the proposed experiment in the proposal). This simulation allows the agent to identify and summarize potential failure scenarios. This review method is built on the assumption that frontier LLMs may have developed an internal world model of science that enables them to simulate and accurately predict various scientific phenomena. ●​ Recurrent/tournament review. The Reflection agent adapts its full reviews based on Co-Scientist’s growing knowledge. By analyzing reviewed hypotheses and results of the tournament conducted by the Ranking agent, the Reflection agent identifies recurring issues and improvement opportunities, refining its reviews accordingly.

**中文译文 · 机器初译**

智能体会评估该假设在假设成立的情况下是否比现有解释更优。积极的观察结果会被总结并附在假设之后。需要注意的是，这种评审往往不会得出任何重要发现（如 ALS 假设示例所示）。用于生成观察结果的示例提示见补充注释 9.2。关于用于解释抗菌耐药性机制替代假设的观察评审示例，详见补充注释 10.8。● 模拟评审。
Reflection智能体还会通过逐步模拟假设来对其进行审查（例如，模拟作用机制或提案中的实验过程）。这种模拟使得智能体能够识别并总结潜在的失败场景。这种审查方式基于这样一个假设：前沿大语言模型可能已经建立了科学内部模型，从而能够模拟并准确预测各种科学现象。● 循环/竞赛式审查。Reflection智能体会根据共科学家不断增长的知识水平调整其完整的审查内容。
通过分析被审核的假设以及排名智能体所进行的比赛结果，反思智能体能够识别反复出现的问题与改进机会，并据此完善其评估内容。

### co-scientist-0210

**English original**

Additionally, Co-Scientist can incorporate reviews from expert scientists to guide ranking and improvements (further discussed in the “Expert-in-the-loop” section). A key aim is to have the Reflection agent generate a comprehensive set of reviews from multiple angles covering the common methods scientists employ when critiquing and refining research hypotheses and proposals.

**中文译文 · 机器初译**

此外，联合科学家可以整合专家科学家的评论，以指导排序与改进工作（详见“专家参与式流程”部分）。关键目标是让反思智能体从多个角度生成一套全面的评论，涵盖科学家在批判和完善研究假设及提案时常用的常见方法。

### co-scientist-0211

**English original**

Ranking agent. Co-Scientist explores numerous hypotheses and research proposals towards a research goal, necessitating a ranking mechanism to prioritize scientists’ time and computational resources toward the most promising candidates. This task is performed by the Ranking agent. The agent orchestrates an Elo-based tournament 31 to automatically evaluate and rank all hypotheses, providing supporting rationale. This ranking serves to communicate to scientists an ordered list of research hypotheses and proposals aligned with the research goal. Despite its assumptions and limitations 32, Elo remains a good proxy for relative ranking, and it has previously been applied to rank extracted patterns and ideas in games 33. In the future, extensions may be considered 34. We set the initial Elo rating of 1200 for the newly added hypothesis.

**中文译文 · 机器初译**

排名智能体。联合科学家会探索多种假设与研究提案以达成研究目标，因此需要一种排名机制来优先分配科学家的时间和计算资源给最具潜力的候选方案。这一任务由排名智能体负责执行。该智能体通过基于 Elo 的竞赛机制自动评估并排序所有假设，同时提供相应的理由说明。这种排名方式能够向科学家展示与研究目标相一致的、按顺序排列的研究假设与提案列表。
尽管存在其假设与局限性，Elo 仍然是一个良好的相对排名代理工具，且此前已被用于对游戏中的提取模式与想法进行排名。未来可能会考虑对其进行扩展。我们对新添加的假设设定了初始 Elo 评分为 1200。

### co-scientist-0212

**English original**

Because the tournament is computationally intensive, the Ranking agent employs several optimization strategies. Top-ranked hypotheses are compared pairwise in tournament matches through multi-turn scientific debates 35. This mitigates ordering bias and focuses on novelty, correctness, and testability. Lower-ranked hypotheses undergo single-turn comparisons in a pairwise fashion in their tournament match. The agent concludes each comparison with a decision regarding which hypothesis is better. Supplementary Note 9.3 shows example prompts. Supplementary Note 10.9 shows an example of the Ranking agent conducting a scientific debate match in a tournament to compare two hypotheses.

**中文译文 · 机器初译**

由于该竞赛涉及大量计算工作，排名智能体采用多种优化策略。排名靠前的假设通过多轮科学辩论在竞赛中对齐进行成对比较。这能够减少排序偏差，并重点关注新颖性、正确性和可验证性。排名较低的假设则通过成对方式在单轮中完成竞赛比较，最终智能体会针对哪个假设更优做出判断。补充注释 9.3 展示了示例提示。补充注释 10.9 则展示了排名智能体在竞赛中开展科学辩论以比较两个假设的实例。


### 原文第 35 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=35)

### co-scientist-0214

**English original**

The Ranking agent prioritizes tournament matches as follows: (1) hypotheses are more likely to be compared with similar ones (based on the Proximity agent’s graph, described in the next section); (2) newer and top-ranking hypotheses are prioritized for participation in tournament matches. Successful hypotheses quickly achieve favorable rankings and this informs the tournament state for subsequent iterations.

**中文译文 · 机器初译**

排名智能体对锦标赛比赛的优先级排序如下：(1) 假设与类似假设进行比较的可能性更大（基于下一节中描述的邻近性智能体的图）；(2) 更新且排名较高的假设在参与锦标赛比赛时享有更高优先级。成功的假设能迅速获得有利的排名，这也会为后续迭代中的锦标赛状态提供参考。

### co-scientist-0215

**English original**

Proximity agent. The Proximity agent calculates the similarity between research hypotheses and proposals, and builds a proximity graph, taking into account the specific research goal. Although it doesn’t directly participate in hypothesis generation, the Proximity agent assists the Ranking agent in organizing tournament matches and showcasing a diverse range of ideas related to the research goal. This allows scientists to quickly explore areas of interest and easily identify related concepts.

**中文译文 · 机器初译**

邻近智能体。该邻近智能体计算研究假设与提案之间的相似度，并基于具体研究目标构建邻近图。虽然它不直接参与假设生成过程，但邻近智能体有助于排名智能体组织竞赛比赛，并展示与研究目标相关的多种想法。这使得科学家能够快速探索感兴趣的领域，并轻松识别相关概念。

### co-scientist-0216

**English original**

Evolution agent. The Evolution agent continuously refines and improves existing hypotheses and proposals using several strategies including: ●​ Enhancement through grounding. Here the agent attempts to improve hypotheses by identifying weaknesses, generating search queries, retrieving and reading articles, suggesting improvements and elaborating on details to fill reasoning gaps. ●​ Coherence, practicality and feasibility improvements. The agent aims to address issues and creates more coherent hypotheses, potentially rectifying underlying problems with invalid initial assumptions. The agent also refines the hypotheses to make them more practical and feasible. Supplementary Note 9.4 provides an example of the feasibility improvement prompt. ●​ Inspiration from existing hypotheses. The agent additionally creates new hypotheses inspired by single or multiple top-ranked hypotheses. ●​ Combination. The agent also attempts to directly combine the best aspects of several top-ranking hypotheses to create new hypotheses. ●​ Simplification. The agent simplifies hypotheses for easier verification and testing. ●​ Out-of-box thinking. The agent also explores out-of-the-box ideas by moving away from a subset of hypotheses and generating divergent ones. Supplementary Note 9.4 provides an example prompt for this.

**中文译文 · 机器初译**

进化智能体。该进化智能体通过多种策略不断完善和改进现有的假设与提案，包括：● 通过基础化增强。该智能体通过识别弱点、生成搜索查询、进行检索与阅读文章、提出改进建议以及详细阐述以填补推理空白来提升假设质量。● 提升连贯性、实用性与可行性。该智能体旨在解决相关问题，生成更连贯的假设，从而可能纠正基于无效初始假设所存在的根本问题。此外，该智能体还会对假设进行优化，使其更具实用性和可行性。
补充说明 9.4 给出了一个可行性提升提示的示例。●​ 基于现有假设的启发。智能体还会根据单个或多个排名靠前的假设来生成新的假设。●​ 组合。智能体还尝试直接结合多个排名靠前的假设中的最佳要素以生成新假设。●​ 简化。智能体会简化假设以便更容易进行验证和测试。●​ 跳出常规思维。智能体还会通过脱离部分假设并生成不同的想法来探索非传统的思路。补充说明 9.4 提供了相应的示例提示。

### co-scientist-0217

**English original**

The Evolution agent generates new hypotheses; it doesn’t modify or replace existing ones. This strategy protects the quality of top-ranked hypotheses from flawed improvements, as each new hypothesis must also compete in the tournament. The evolution of research hypotheses and proposals also allows Co-Scientist to iteratively combine different improvement techniques and gradually improve the quality of the results.

**中文译文 · 机器初译**

Evolution智能体会生成新的假设，但不会修改或替换现有的假设。这种策略能够避免有缺陷的改进对排名靠前的假设质量造成影响，因为每一个新假设都必须参与竞赛竞争。研究假设与提案的迭代发展还使得联合科学家能够逐步结合不同的改进技术，从而逐渐提升结果的质量。

### co-scientist-0218

**English original**

Meta-review agent. The Meta-review agent plays a crucial role in Co-Scientist’s feedback loop, enabling self-improvement in scientific thinking and reasoning. This agent operates on the

**中文译文 · 机器初译**

Meta评审智能体。该Meta评审智能体在共同科学家反馈循环中发挥着关键作用，有助于科学思维与推理的自我提升。该智能体基于……运行


### 原文第 36 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=36)

### co-scientist-0220

**English original**

tournament state and summarizes common patterns identified in reviews and scientific debates in the tournament matches into a meta-review critique.

**中文译文 · 机器初译**

比赛状态，并将比赛中评论与科学辩论中发现的常见模式总结为一项元评论批判。

### co-scientist-0221

**English original**

By synthesizing insights from all reviews, the meta-review provides valuable feedback to the Reflection agent, leading to more thorough and reliable future reviews. This helps prevent oversight of critical details. Consider the illustrative example of a identifying a repurposing drug candidate for ALS as a research goal: while only 90% of individual reviews might correctly identify a blood-brain barrier permeability issue in a proposed candidate, the meta-review ensures that all future reviews by the Reflection agent definitively address this crucial factor. Hypothesis and research proposal generation is also enhanced by the meta-review’s identification of recurring issues. While the Generation agent uses this feedback selectively to avoid over-fitting to these review critiques, it helps prevent the recurrence of common issues.

**中文译文 · 机器初译**

通过整合所有评论中的见解，元评论为反思智能体提供了宝贵的反馈，从而促使未来的评论更加全面且可靠，有助于避免关键细节被忽视。以识别用于ALS研究的重新应用药物候选物为例：虽然仅有90%的单独评论能够准确指出拟议药物候选物的血脑屏障渗透问题，但元评论确保反思智能体未来的所有评论都能明确解决这一重要因素。元评论对重复问题的识别，也提升了假设与研究提案的生成效果。
虽然生成智能体会选择性地利用这些反馈，以避免过度依赖这些评论批评，但这有助于防止常见问题的再次出现。

### co-scientist-0222

**English original**

Supplementary Note 9.5 provides an example prompt for the meta-review. In Supplementary Note 10.10, we showcase an example of the summarized meta-review critique generated for the reviews of the previously introduced ALS mechanism hypotheses.

**中文译文 · 机器初译**

补充说明 9.5 提供了用于元评论的示例提示。在补充说明 10.10 中，我们展示了针对之前提出的 ALS 机制假设所进行的评论所生成的总结性元评论批评示例。

### co-scientist-0223

**English original**

Research overview generation. At the end of the Co-Scientist computation, the Meta-review agent synthesizes top-ranked hypotheses into a research overview, providing a roadmap for future research. This overview outlines potential research areas and directions relevant to the research goal, justifying their importance and suggesting specific experiments within each. Each area includes illustrative example topics. The research overview also serves as an additional input to the Generation agent in subsequent iterations. The research overview serves to effectively map the boundary of current knowledge relevant to the research goal in Co-Scientist and helps highlight future areas of exploration. In Supplementary Note 10.11, we show an example of a research overview for the ALS mechanism research goal. The Meta-review agent can further format these overviews using constrained decoding techniques 36 to adhere to common research publication and grant formats (e.g., National Institutes of Health (NIH) Specific Aims Page format). We demonstrate the effectiveness of this in subsequent sections.

**中文译文 · 机器初译**

研究概述生成。在协同科学家计算结束后，Meta-review智能体将排名靠前的假设整合为一份研究概述，为后续研究提供指导方向。该概述列出了与研究目标相关的潜在研究领域和方向，说明其重要性，并建议每个领域的具体实验内容。每个领域都包含示例性主题。研究概述还作为额外输入供后续迭代中的生成智能体使用。研究概述有助于有效界定与研究目标相关的现有知识边界，并突出未来可探索的领域。
在补充说明 10.11 中，我们展示了一个关于 ALS 机制研究目标的研究综述示例。Meta-review 智能体可以通过受限解码技术 36 进一步整理这些综述内容，以符合常见的研究出版和资助格式（例如美国国立卫生研究院 (NIH) 具体目标页面格式）。我们在后续章节中证明了这种方法的有效性。

### co-scientist-0224

**English original**

Research contacts identification. The Meta-review agent also uses prior literature review to suggest qualified domain experts for research hypotheses and proposal review, including the reasoning behind each suggestion. These potential contacts are summarized in the research overview, providing researchers with additional perspectives and potential avenues for collaborations. An example research contact (with the researcher name redacted) is shown in Supplementary Note 10.12.

**中文译文 · 机器初译**

研究联系人的识别。Meta-review智能体还利用先前的文献综述，推荐具有资格的领域专家来审核研究假设与提案，并说明每个推荐背后的理由。这些潜在的联系人会在研究概述中进行总结，为研究人员提供额外的视角和合作机会。一个研究联系人示例（研究人员姓名已隐去）见补充注释10.12。

### co-scientist-0225

**English original**

Expert-in-the-loop interactions with Co-Scientist. Co-Scientist empowers scientists to actively steer and guide the system through an expert-in-the-loop design (Fig. 1a-b). Scientists can interact with the system in several ways. The typical interaction between Co-Scientist and a human follows a structured process: ●​ Research goal definition: The process begins with a scientist defining the high-level research objective. This involves writing a detailed prompt that can include the specific

**中文译文 · 机器初译**

专家在循环中的与协同科学家互动。协同科学家帮助科学家通过专家在循环中的设计主动引导并操控系统（图1a-b）。科学家可以通过多种方式与系统互动。协同科学家与人类之间的典型互动遵循结构化流程：● 研究目标定义：该过程始于科学家明确高层次研究目标。这涉及撰写包含具体内容的详细提示词


### 原文第 37 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=37)

### co-scientist-0227

**English original**

research question, known constraints of the hypotheses solution space, desired attributes of the output, and relevant background literature and data. With proper goal definition, scientists can direct Co-Scientist to follow up on specific research directions (for example restricted to a smaller collection of prior publications). When this research is referenced in the research goal, Co-Scientist can prioritize generation methods that can access and synthesize it. ●​ Goal refinement: The scientist can refine the initial research goal in light of the generated hypotheses and research overview. ●​ Providing review: The scientist can also provide manual reviews of generated hypotheses, which Co-Scientist uses to evaluate and improve the hypotheses and proposals. ●​ Providing ideas and hypotheses: In the user interface, scientists are allowed to contribute their own hypotheses and proposals for inclusion in the tournament, where they are ranked alongside and can be combined with system-generated hypotheses and proposals. ●​ Final review and selection: After the Co-Scientist run is complete, the scientist is presented with a ranked list of hypotheses and a synthesized research overview from the Meta-review agent. The expert then invests time in reviewing the top-ranked proposals to select the most promising candidates for further experimental validation.

**中文译文 · 机器初译**

研究问题、假设解空间的已知限制、期望的输出属性，以及相关的背景文献和数据。通过明确设定目标，科学家可以指导协同科学家专注于特定的研究方向（例如仅限于少数已发表的文献）。
当该研究被纳入研究目标时，联合科学家可以优先选择能够获取并整合该研究的生成方法。● 目标优化：科学家可以根据生成的假设及研究概述来完善初始研究目标。● 提供评审意见：科学家还可以对生成的假设进行人工评审，供联合科学家用于评估和改进这些假设与提案。● 提供创意与假设：在用户界面中，科学家可以提交自己的假设与提案以参与竞赛，这些提案将与系统生成的假设与提案一同进行排名和组合。
● 最终评审与选择：在联合科学家运行完成后，科学家会收到按排名排列的假设列表以及来自元评审智能体的综合研究概述。随后，专家会花时间对排名最高的提案进行评审，以选出最具潜力的候选方案用于进一步的实验验证。

### co-scientist-0228

**English original**

This workflow empowers scientists to guide Co-Scientist at critical junctures. As illustrative examples, we quantified the human time investment for our main validation studies. For the AML drug repurposing study, the initial prompt, defining the goal to find novel combination therapies, required less than one hour of an expert clinician’s time. After the system’s complex run, the final review and selection of promising candidates for in vitro testing took roughly three hours. Similarly, the fibrosis target discovery and AMR mechanism generation tasks each required comparable, similar time investments from experts for setup and final review. The scientists and experts featured in our validations have noted that Co-Scientist accomplishes work that would otherwise require days and even weeks of valuable scientists’ time.

**中文译文 · 机器初译**

该工作流程使科学家能够在关键节点指导智能体进行操作。作为示例，我们统计了主要验证研究所需的人力时间。在AML药物重新应用研究中，最初的任务提示——明确寻找新型联合疗法的目标——仅需专家临床医生不到一小时的时间即可完成。系统执行完复杂流程后，对具有潜力的候选方案进行最终评审和筛选大约需要三小时。同样，纤维化靶点发现和AMR机制生成任务也分别需要专家花费相当的时间进行准备和最终评审。
参与我们验证工作的科学家和专家指出，Co-Scientist能够完成那些原本需要数天甚至数周宝贵科学家时间才能完成的任务。

### co-scientist-0229

**English original**

Tool use in Co-Scientist. Co-Scientist leverages various tools during the generation, review, and improvement of hypotheses. Web search and retrieval are primary tools, important for grounded, up-to-date hypotheses. For research goals that explore a constrained space of possibilities (e.g., all known cell receptors of a specific type or all FDA-approved drugs), Co-Scientist agents utilize domain-specific tools, such as open databases, to constrain searches and generate hypotheses. Co-Scientist can also index and search a private repository of publications and experimental data specified by the scientist. Finally, the system can utilize and incorporate feedback from specialized AI models like AlphaFold. We demonstrate this qualitatively with a protein design example in the Supplementary Note 11 and Supplementary Fig. 9.

**中文译文 · 机器初译**

协同科学家中的工具使用。在假设的生成、审核与优化过程中，协同科学家会利用多种工具。网络搜索与检索是主要工具，对于具有实际依据且最新的假设至关重要。对于探索有限可能性的研究目标（例如，特定类型所有已知细胞受体或所有获得FDA批准的药物），协同科学家智能体会利用领域专用工具（如开放数据库）来限制搜索范围并生成假设。此外，协同科学家还可以对科学家指定的私人出版物与实验数据库进行索引和搜索。
最后，该系统能够利用并整合来自 AlphaFold 等专业人工智能模型的反馈信息。我们在补充说明第 11 条及补充图 9 中的蛋白质设计示例中，从质量层面证明了这一点。


### 原文第 38 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=38)

### co-scientist-0231

**English original**

Ablation analysis. To validate the contributions of Co-Scientist’s core components and agents, we performed a series of quantitative ablation studies (details in Supplementary Note 3 and Supplementary Fig. 2-6). These analyses revealed that our architectural choices provide tangible benefits to performance and robustness of the overall system.

**中文译文 · 机器初译**

消融分析。为了验证 Co-Scientist 核心组件及智能体的贡献，我们开展了一系列定量消融研究（详情见补充注释3和补充图2-6）。这些分析表明，我们的架构设计对系统的性能与鲁棒性带来了切实的提升。

### co-scientist-0232

**English original**

Specifically, we quantified the value of our multi-faceted Generation agent, showing that a diverse set of generation strategies contributes to the creation of correct hypotheses across different benchmarks.

**中文译文 · 机器初译**

具体来说，我们量化了我们的多维度生成智能体的价值，结果表明多种不同的生成策略有助于在不同基准测试中生成正确的假设。

### co-scientist-0233

**English original**

Critically, the Reflection agent's ability to assess novelty was shown to be dependent on its integration with an external search tool. On a dataset of published ideas that should be rated as non-novel, the agent without search incorrectly assigned a high auto-evaluation novelty score of 6.14 (out of 10), while the agent with search correctly assigned a low novelty score of 2.38 (out of 10). The search tool also enhanced review accuracy, raising the average auto-evaluation correctness score from 7.4 to 8.46 (out of 10) for these known-correct ideas and increasing the Area Under the Curve (AUC) on the GPQA benchmark from 0.643 to 0.651 in our run using Gemini 2.0 Flash as the base foundational LLM for the agents in the system.

**中文译文 · 机器初译**

关键的是，反思智能体评估新颖性的能力取决于其与外部搜索工具的结合情况。在一组应被判定为非新颖的已发表想法数据集中，没有使用搜索功能的智能体错误地给出了6.14（满分10分）的高自动评估新颖性得分，而使用了搜索功能的智能体则正确地给出了2.38（满分10分）的低新颖性得分。
该搜索工具还提升了评估准确性，在采用 Gemini 2.0 Flash作为系统智能体基础大语言模型的实验中，这些已知正确的想法平均自动评估正确率从 7.4 提升至 8.46（满分 10 分），同时 GPQA 基准测试上的曲线下面积（AUC）也从 0.643 提高至 0.651。

### co-scientist-0234

**English original**

Furthermore, we demonstrated that using the scientific debate prompt rather than simple comparison prompt for the Ranking agent can significantly enhance ranking accuracy for high-quality hypotheses and, critically, reduces the positional bias.

**中文译文 · 机器初译**

此外，我们证明使用科学辩论提示而非简单比较提示来训练排名智能体，能够显著提升高质量假设的排序准确性，并且能有效减少位置偏差。

### co-scientist-0235

**English original**

Our analysis of the Evolution agent confirms that its iterative refinement process is crucial, boosting precision on GPQA from 70.9% to 75.4%, and increasing the average research hypothesis quality score (auto-evaluation) on the constructed dataset from 4.7 to 5.6.

**中文译文 · 机器初译**

我们对 Evolution 智能体的分析表明，其迭代优化过程至关重要，使得 GPQA 的准确率从 70.9% 提升至 75.4%，并在构建的数据集上使平均研究假设质量得分（自动评估）从 4.7 提升至 5.6。

### co-scientist-0236

**English original**

The effectiveness of our Proximity agent was also validated, as its semantic similarity scores showed a strong correlation with the actual quality score differences between hypotheses, ensuring a comprehensive exploration of the problem space.

**中文译文 · 机器初译**

我们的邻近智能体的有效性也得到了验证，因为其语义相似度得分与不同假设之间的实际质量得分差异存在强相关性，从而确保了对问题域的全面探索。

### co-scientist-0237

**English original**

Finally, we found that Meta-review agent measurably improves the quality of correctness reviews, increasing AUC for predicting a correct solution from 0.521 to 0.597 in our constructed dataset, and 0.629 to 0.634 in the GPQA diamond dataset.

**中文译文 · 机器初译**

最后我们发现，Meta-review智能体显著提升了正确性评价的质量，在我们构建的数据集中，预测正确解决方案的 AUC 从 0.521 提升到了 0.597，在 GPQA 钻石数据集中则从 0.629 提升到了 0.634。

### co-scientist-0238

**English original**

These results provide important quantitative evidence and support that our multi-agent architecture and specialized prompting strategies are critical design choices that lead to more accurate, robust, and reliable scientific hypothesis generation and evaluation.

**中文译文 · 机器初译**

这些结果提供了重要的定量证据，证明我们的多智能体架构与专用提示策略是关键的设计选择，能够实现更准确、更稳健且更可靠的科学假设生成与评估。

### co-scientist-0239

**English original**

Statistics and reproducibility. No statistical methods were used to predetermine sample sizes. For computational evaluations, sample sizes (n = 203, n = 15, and n = 11 research goals) were chosen to ensure robust statistical averaging and broad representation across diverse scientific domains. For in vitro validations, five distinct AML cell lines were tested in independent biological triplicates (n = 3). This sample size was not predetermined by statistical methods but was chosen based on widely accepted standard practices for preliminary in vitro dose-response viability screening. Given the large effect sizes typical of such preliminary pharmacological assays, three independent biological replicates provide the necessary degrees of freedom to calculate standard deviation, assess assay consistency, and robustly fit non-linear regression

**中文译文 · 机器初译**

统计与可重复性。未使用任何统计方法来预先确定样本量。在计算评估中，选择了不同的样本量（n = 203、n = 15 和 n = 11 个研究目标），以确保能够进行稳健的统计平均处理，并涵盖多种科学领域。在体外验证中，对五种不同的 AML 细胞系进行了独立的生物三重实验（n = 3）。这一样本量并非通过统计方法预先确定，而是基于广泛接受的初步体外剂量-反应存活筛选标准实践来选择的。
鉴于此类初步药理学检测通常具有较大的效应大小，三个独立的生物学重复样本提供了必要的自由度，以便计算标准差、评估检测一致性以及进行稳健的非线性回归分析


### 原文第 39 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=39)

### co-scientist-0241

**English original**

curves for IC50 estimation. All attempts at replication in both computational and in vitro were successful. The human expert evaluation of the LLM-generated outputs was explicitly blinded, ensuring that independent domain experts were completely unaware of which model generated the hypotheses they were scoring. Blinding was not applicable to the in vitro cell viability screening assays because these experiments involve standardized, automated multimode microplate reader readouts. All cell lines were authenticated by their respective providers.

**中文译文 · 机器初译**

IC50估算的曲线数据。在计算模型和体外实验中，所有重复实验均成功完成。对大语言模型生成的输出结果进行的人类专家评估采用了盲法处理，确保独立领域专家完全不知道是哪种模型生成了他们正在评分的假设。由于这些实验涉及标准化、自动化的多模式微孔板读取结果，因此不适用于体外细胞存活率筛选试验。所有细胞系均由其相应的供应商进行验证。

### co-scientist-0242

**English original**

Methods references

**中文译文 · 机器初译**

方法参考文献

### co-scientist-0243

**English original**

28.​ Jones, N. OpenAI’s ‘deep research’ tool: is it useful for scientists? Nature

**中文译文 · 机器初译**

28.​ Jones, N. OpenAI的“深度研究”工具：对科学家是否有用？《自然》

### co-scientist-0244

**English original**

https://doi.org/10.1038/d41586-025-00377-9 (2025).

**中文译文 · 机器初译**

https://doi.org/10.1038/d41586-025-00377-9 (2025)。

### co-scientist-0245

**English original**

29.​ Megat, S. et al. Integrative genetic analysis illuminates ALS heritability and identifies risk

**中文译文 · 机器初译**

29.​ Megat, S. 等。综合遗传分析揭示了ALS的遗传性并确定了风险因素

### co-scientist-0246

**English original**

genes. Nat. Commun. 14, 342 (2023).

**中文译文 · 机器初译**

genes. Nat. Commun. 14, 342 (2023).

### co-scientist-0247

**English original**

30.​ Elo, A. E. The Rating of Chess Players, Past and Present (Ishi Press, 2008).

**中文译文 · 机器初译**

30.​ Elo, A. E. 《过去与现在棋手的评分体系》（Ishi Press，2008年）。

### co-scientist-0248

**English original**

31.​ LeCun, Y. A theoretical framework for back-propagation. In Proc. 1988 Connectionist

**中文译文 · 机器初译**

31.​ LeCun, Y. 反向传播的理论框架。载于 1988 年连接主义会议论文集

### co-scientist-0249

**English original**

Models Summer School Vol. 1 (eds Touretzky, D. et al.) 21–28 (Morgan Kaufmann, 1988).

**中文译文 · 机器初译**

《模型夏季学校》第1卷（由 Touretzky, D. 等编）21–28页（Morgan Kaufmann，1988年）。

### co-scientist-0250

**English original**

32.​ Hamilton, A. H., Kalenkova, A. & Roughan, M. The impact of intransitivity on the Elo

**中文译文 · 机器初译**

32.​ Hamilton, A. H., Kalenkova, A. & Roughan, M. 内射性对 Elo 系统的影响

### co-scientist-0251

**English original**

rating system. PLoS One 20, e0338261 (2025).

**中文译文 · 机器初译**

评分系统。PLoS One 20, e0338261 (2025)。

### co-scientist-0252

**English original**

33.​ Coulom, R. Computing ‘Elo ratings’ of move patterns in the game of go. ICGA J. 30,

**中文译文 · 机器初译**

33.​ Coulom, R. 计算围棋中棋步模式的“Elo评分”。ICGA J. 30,

### co-scientist-0253

**English original**

198–208 (2007).

**原文保留（专名、技术内容或文献信息） · 保留原文**

198–208 (2007).

### co-scientist-0254

**English original**

34.​ Kovalchik, S. Extension of the Elo rating system to margin of victory. Int. J. Forecast. 36,

**中文译文 · 机器初译**

34.​ Kovalchik, S. 大语言模型对胜局差值的 Elo 评分系统扩展。国际预测杂志。36,

### co-scientist-0255

**English original**

1329–1341 (2020).

**原文保留（专名、技术内容或文献信息） · 保留原文**

1329–1341 (2020).

### co-scientist-0256

**English original**

35.​ Khan, A. et al. Debating with more persuasive LLMs leads to more truthful answers. In

**中文译文 · 机器初译**

35.​ Khan, A. 等。与更具说服力的大语言模型讨论可带来更真实的答案。载于

### co-scientist-0257

**English original**

Proc. 41st International Conference on Machine Learning Vol. 235 (eds Salakhutdinov, R.

**中文译文 · 机器初译**

第41届国际机器学习会议论文集 第235卷 (编者：Salakhutdinov, R.)

### co-scientist-0258

**English original**

et al.) 23662–23733 (PMLR, 2024).

**中文译文 · 机器初译**

等) 23662–23733 (PMLR, 2024)。

### co-scientist-0259

**English original**

36.​ Post, M. & Vilar, D. Fast lexically constrained decoding with dynamic beam allocation for

**中文译文 · 机器初译**

36.​ Post, M. & Vilar, D. 采用动态波束分配技术的快速词法约束解码方法


### 原文第 40 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=40)

### co-scientist-0261

**English original**

neural machine translation. In Proc. 2018 Conference of the North American Chapter of the

**中文译文 · 机器初译**

神经机器翻译。载于2018年北美分会会议论文集

### co-scientist-0262

**English original**

Association for Computational Linguistics: Human Language Technologies Vol. 1 (Long

**中文译文 · 机器初译**

计算语言学协会：人类语言技术 第1卷（长文版）

### co-scientist-0263

**English original**

Papers) 1314–1324 (Association for Computational Linguistics, 2018).

**中文译文 · 机器初译**

论文) 1314–1324（计算语言学协会，2018年）。

### co-scientist-0264

**English original**

37.​ Gemini Team, Google. Gemini: a family of highly capable multimodal models. Preprint at

**中文译文 · 机器初译**

37.​ Google Gemini 团队。Gemini：一系列功能强大的多模态模型。预印本发表于

### co-scientist-0265

**English original**

https://arxiv.org/abs/2312.11805 (2023).

**中文译文 · 机器初译**

https://arxiv.org/abs/2312.11805 (2023)。

### co-scientist-0266

**English original**

Data availability

**中文译文 · 机器初译**

数据可用性

### co-scientist-0267

**English original**

Except for the three real-world validation tasks (drug repurposing for AML, novel target discovery for liver fibrosis, mechanism explanation of gene transfer evolution), the remaining datasets used for development, benchmarking and evaluation of the systems are open source or otherwise accessible publicly with permissions. Specifically, the GPQA diamond dataset is publicly available at Hugging Face (https://huggingface.co/datasets/Idavidrein/gpqa). The Cancer Dependency Map (DepMap) Q2 2024 data used for computational sanity checks is publicly available at the DepMap portal (https://depmap.org/portal/). The curated drug targets dataset from the Open Targets Platform is available at https://platform.opentargets.org/downloads.

**中文译文 · 机器初译**

除了三个实际验证任务（AML疾病的药物重新应用研究、肝纤维化新靶点发现研究以及基因转移演化机制分析）外，用于系统开发、基准测试和评估的其余数据集均为开源或经授权可公开获取。具体而言，GPQA钻石数据集可在 Hugging Face 上公开获取（https://huggingface.co/datasets/Idavidrein/gpqa).）；用于计算性合理性检验的 The Cancer Dependency Map (DepMap) Q2 2024 数据也可在 DepMap 门户上公开获取（https://depmap.org/portal/).）
来自 Open Targets 平台的精选药物靶点数据集可在 https://platform.opentargets.org/downloads. 处获取

### co-scientist-0268

**English original**

Code availability

**中文译文 · 机器初译**

代码可用性

### co-scientist-0269

**English original**

The full source code for the Co-Scientist system is not publicly available. Due to the deep integration of the Co-Scientist multi-agent framework with proprietary internal infrastructure, the immense computational resources required for massive test-time scaling, and the safety implications of unmonitored autonomous agentic use of such capable AI systems, we are unable to publicly release the full source code or provide broad access immediately.

**中文译文 · 机器初译**

Co-Scientist系统的完整源代码并未公开。由于Co-Scientist多智能体框架与内部专有基础设施深度整合，且大规模测试时扩展需要巨大的计算资源，再加上未受监控的自主智能体使用此类强大人工智能系统所带来的安全风险，我们无法立即公开发布完整源代码或提供广泛访问权限。

### co-scientist-0270

**English original**

Instead, to enable and accelerate research on important scientific problems, we are initiating an experimental access program. We request scientists interested in solving important scientific problems to reach out and we will provision access subject to computational resources. In due course, we expect to provide broader access to thousands of scientists across the scientific community via Google APIs and bespoke interfaces over time. To further aid transparency and reproducibility, we have provided comprehensive pseudocode detailing the multi-agent orchestration and tournament logic (Supplementary Note 8), alongside the exact system prompts utilized (Supplementary Note 9).

**中文译文 · 机器初译**

相反，为了推动并加速重要科学问题的研究，我们正在启动一项实验性访问计划。我们呼吁有兴趣解决重要科学问题的科学家与我们联系，我们将根据计算资源情况提供访问权限。未来，我们希望通过 Google API 和定制界面，为整个科学界的数千名科学家提供更广泛的访问机会。为了进一步促进透明度和可复现性，我们提供了详细的伪代码，其中描述了多智能体调度和竞赛逻辑（补充说明 8），以及所使用的具体系统提示语（补充说明 9）。

### co-scientist-0271

**English original**

The foundational LLM model, Gemini, used in Co-Scientist is publicly available via APIs, Google AI studio, the Gemini App and other surfaces. Further, important technical details on Gemini have been described extensively in corresponding technical reports 8,14,37.

**中文译文 · 机器初译**

用于 Co-Scientist 的大语言模型 Gemini，可通过 API、Google AI Studio、Gemini 应用及其他渠道公开获取。此外，关于 Gemini 的重要技术细节也在相应的技术报告 8、14、37 中得到了详细阐述。


### 原文第 41 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=41)

### co-scientist-0273

**English original**

The system, algorithms, and analysis scripts were developed using Python (version 3.11.7). Data handling and visualization were performed using pandas (version 2.1.4), numpy (version 1.26.4), seaborn (version 0.12.2), and matplotlib (version 3.8.0). For in vitro validations, dose-response curve fitting and IC50 estimation were performed using GraphPad Prism (version 10.6.0, GraphPad Software). Dose-effect data from single-agent and combination treatments were analysed using Julius AI statistical software (accessed November 2025).

**中文译文 · 机器初译**

该系统、算法及分析脚本均使用 Python（版本 3.11.7）开发。数据处理与可视化工作则采用 pandas（版本 2.1.4）、numpy（版本 1.26.4）、seaborn（版本 0.12.2）和 matplotlib（版本 3.8.0）完成。在体外验证方面，剂量-反应曲线拟合及 IC50 估算工作则使用 GraphPad Prism（版本 10.6.0，GraphPad Software）进行。单一药物及联合治疗的剂量效应数据则通过 Julius AI 统计软件进行分析（数据获取时间为 2025 年 11 月）。

### co-scientist-0274

**English original**

Acknowledgements

**中文译文 · 机器初译**

致谢

### co-scientist-0275

**English original**

We thank our teammates Subhashini Venugopalan, John Platt, Erica Brand, and Yun Liu for their detailed technical feedback on the manuscript. We thank Jakob T Rostoel, Cora Chmielowska and Jonasz B Patkowski from Imperial College London and Jakkapong Inchai, Weida Liu, and Wenlong Ren from Stanford University for providing expert feedback on the AI system introduced in this work, and the lab of Ravi Majeti from Stanford University for generously providing the AML cell lines used in this work. We thank Ritu Raman, Ryan Flynn, Charlie Hempstead, Lord Ara Darzi, Omar Abudayyeh, Jonathan Gootenberg, Nic Fishman, Jason Lequyer, Dan Leesman, Ravi Solanki, Dennis Gong and Ananthan Sadagopan for feedback on different aspects of the AI system and the work. We also thank Maen Abdelrahim, Ethan Burns, Preethi Prasad and Hanh Mai for their clinical expertise and expert evaluation. Finally, we thank Harsha Gowda, Chris Balagtas and the Signios Biosciences team for support with the wet-lab experiments.

**中文译文 · 机器初译**

我们感谢队友 Subhashini Venugopalan、John Platt、Erica Brand 和 Yun Liu对本文稿提供的详细技术反馈。我们也感谢伦敦帝国学院的 Jakob T Rostoel、Cora Chmielowska 和 Jonasz B Patkowski，以及斯坦福大学的 Jakkapong Inchai、Weida Liu 和 Wenlong Ren对本文中介绍的人工智能系统提供的专业意见，同时感谢斯坦福大学 Ravi Majeti 实验室慷慨提供本文中使用的大语言模型细胞系。
我们感谢 Ritu Raman、Ryan Flynn、Charlie Hempstead、Lord Ara Darzi、Omar Abudayyeh、Jonathan Gootenberg、Nic Fishman、Jason Lequyer、Dan Leesman、Ravi Solanki、Dennis Gong 和 Ananthan Sadagopan 对人工智能系统及相关工作的不同方面的反馈。我们也感谢 Maen Abdelrahim、Ethan Burns、Preethi Prasad 和 Hanh Mai 在临床专业知识和专家评估方面提供的帮助。最后，我们感谢 Harsha Gowda、Chris Balagtas 以及 Signios Biosciences 团队在湿实验方面的支持。

### co-scientist-0276

**English original**

We thank our teammates Ali-Cowen Rivers, Saz Basu, Sebastian Nowozin, Thomas Wagner, Natasha Latysheva, Nir Kerem, Yaniv Carmel, Hussein Hassan Harrirou, Laurynas Tamulevičius, Ieva Grublyte, Taylor Applebaum, Meet Shah, Nicolas Stroppa, Mihai Ciorobea, Jakob Oesignhaus, Diego Ballesteros, Luka Važić, Anna Trostanetski, Bill Byrne, Barnaby James, Jorge Barrios, Ivan Lee, Team Rakket and, Boon Panichprecha for their technical support. We thank Charlie Taylor, James Walker, Jack Mason, Hannah Gladman, Sukhdeep Singh, Ivana Bowers, Anna Cupani, Francesca Pietra, Uchechi Okereke, Armin Senoner, Adriana Fernandez Lara, Juanita Bawagan, Danielle Breen, Sun Lee, Dominik-Prinz Barley, Katherine Tong, Q Green, Erwan Rolland, Taylor Goddu, Resham Parikh, Siyi Kou, Rachelle Sico, Amanda Ferber, Cat Kozlowski, Alison Lentz, KK Walker, Roma Ruparel, Jenn Sturgeon, Leen Verburgh, Kathryn Seager, Linda Karlsson, Dimple Vijaykumar, Lauren Winer, Ed-Allt Graham, Tori Milner, MK Blake, Erika Radhansson, Indranil Ghosh, Jay Nayar, Brian Cappy, Celeste Grade, Abi Jones, Laura Vardoulakis, Lizzie Dorfman, Ashmi Chakraborthy, Delia Williams-Falokun, Maggie Shiels, Kalyan Pamarthy, Sarah Brown, Andy Song, Christian Wright, Elle Zadina, Gena Hong, Max Klein, Shirley Leung, Jon Gaiser, Richard Green, Victoria Johnston, Miguel de Andres-Clavera, Avneet Singh, Agata Dondzik, Tom Beyer, Daniel Russell, Vladimir Vuskovic, Gemma Jennings, Kelly Schaefer, Mariana Felix, Rachel Teo, Stefania Giardino, Kim Paterson, Agata Laydon, Victoria Langston, Mathias Voges, Ash Otter, Suzy Pickering, Paige Kunkle, Mor

**中文译文 · 机器初译**

我们感谢队友 Ali-Cowen Rivers、Saz Basu、Sebastian Nowozin、Thomas Wagner、Natasha Latysheva、Nir Kerem、Yaniv Carmel、Hussein Hassan Harrirou、Laurynas Tamulevičius、Ieva Grublyte、Taylor Applebaum、Meet Shah、Nicolas Stroppa、Mihai Ciorobea、Jakob Oesignhaus、Diego Ballesteros、Luka Važić、Anna Trostanetski、Bill Byrne、Barnaby James、Jorge Barrios、Ivan Lee、Rakket团队以及Boon Panichprecha提供的技术支持。
我们感谢查理·泰勒、詹姆斯·沃克、杰克·梅森、汉娜·格拉德曼、苏克迪普·辛格、伊万娜·鲍尔斯、安娜·库帕尼、弗朗西斯卡·皮埃特拉、乌切奇·奥凯雷克、阿尔米纳·塞诺纳、阿德里亚娜·费尔南德斯·拉拉、胡安妮塔·巴瓦根、丹妮尔·布林、孙·李、多米尼克-普林茨·巴利、凯瑟琳·唐、Q·格林、埃尔万·罗兰、泰勒·戈杜、雷莎姆·帕里克、思毅·寇、雷切尔·西科、阿曼达·费伯、凯特·科兹洛夫斯基、艾莉森·伦茨、KK·沃克、罗玛·鲁帕雷尔、詹恩·斯特琼、利恩·弗尔伯格、凯瑟琳·西格尔、琳达·卡尔森、丁普尔·维贾库马尔、劳伦·威纳、埃德-阿尔特·格雷厄姆、托里·米尔纳、MK·布莱克、埃里卡·拉德汉森、因德兰尼尔·高什、杰伊·奈亚尔、布莱恩·卡皮、塞莱斯特·格雷德、阿比·琼斯、劳拉·瓦尔杜拉基斯、莉齐·多夫曼、阿什米·查克拉博蒂、迪莉娅
Williams-Falokun, Maggie Shiels, Kalyan Pamarthy, Sarah Brown, Andy Song, Christian Wright, Elle Zadina, Gena Hong, Max Klein, Shirley Leung, Jon Gaiser, Richard Green, Victoria Johnston, Miguel de Andres-Clavera, Avneet Singh, Agata Dondzik, Tom Beyer, Daniel Russell, Vladimir Vuskovic, Gemma Jennings, Kelly Schaefer, Mariana Felix, Rachel Teo, Stefania Giardino, Kim Paterson, Agata Laydon, Victoria Langston, Mathias Voges, Ash Otter, Suzy Pickering, Paige Kunkle, Mor

待核对标记：little_chinese


### 原文第 42 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=42)

### co-scientist-0278

**English original**

Hazan Taege, Adam Marsh, Antonia Mould, Joel Fenster, Frankie Garcia, Ziyue Wang, Parker Beak, James Stevenson, Amanie Brik, and S. Sara Mahdavi for their support and guidance during the course of this project. Finally, we thank Michael Brenner, Zoubin Ghahramani, Dale Webster, Joelle Barral, Michael Howell, Susan Thomas, Karen DeSalvo, Jason Freidenfelds, Ronit Levavi Morad, Ali Eslami, Anna Koivuniemi, Greg Corrado, Royal Hansen, Andy Berndt, Srini Narayanan, Clemens Mayer, Parthasarathy Ranganathan, Ankur Jain, Scott Huffman, Josh Woodward, John Jumper, Noam Shazeer, Oriol Vinyals, Koray Kavukcuoglu, Thomas Kurian, Jeff Dean and Sundar Pichai for their support of this work.

**中文译文 · 机器初译**

Hazan Taege、Adam Marsh、Antonia Mould、Joel Fenster、Frankie Garcia、Ziyue Wang、Parker Beak、James Stevenson、Amanie Brik以及S. Sara Mahdavi在本项目过程中提供的支持与指导。最后，我们感谢Michael Brenner、Zoubin Ghahramani、Dale Webster、Joelle Barral、Michael Howell、Susan Thomas、Karen DeSalvo、Jason Freidenfelds、Ronit Levavi Morad、Ali Eslami、Anna Koivuniemi、Greg Corrado、Royal Hansen、Andy Berndt、Srini Narayanan、Clemens Mayer、Parthasarathy Ranganathan、Ankur Jain、Scott Huffman、Josh Woodward、John Jumper、Noam Shazeer、Oriol Vinyals、Koray Kavukcuoglu、Thomas Kurian、Jeff Dean和Sundar Pichai对本研究的支持。

### co-scientist-0279

**English original**

Author contributions

**中文译文 · 机器初译**

作者贡献

### co-scientist-0280

**English original**

JG, VN, TT, AK initiated the project. JG, WW, AD, TT, YG, VD, EDV, BL, TRDC, JRP, GP, A Pawlosky, AK, VN contributed to the conception of the study and study design; JG, WW, AD, PS, AM, GG, FW, AO, DP, JB, DZ, IR, EV, FH, LR, M Boia, IB, BF, M Bellaiche, TS, JF, JR, BG, AV, DH, YX, PK, A Pawlosky, AK, VN contributed to system design; JG, WW, AD, TT, OB, YG, VD, EDV, BL, TRDC, JRP, GP, PK, A Pawlosky, AK, VN contributed to acquisition of the data; JG, WW, AD, TT, PS, AM, FW, GG, A Palepu, DP, FZ, YG, VD, EDV, BL, TRDC, JRP, GP, A Pawlosky, AK, VN contributed to analysis and interpretation of the data; JG, KR, JB, AC, KK, KC, AH, BG, AV, YM, JM, DH, YX, PK, A Pawlosky, AK, VN provided strategic guidance; YX led product discovery and development; JG, WW, AD, TT, KK, OB, YX, A Pawlosky, AK, VN contributed to paper organisation and team logistics; JG, JR, NT, OB, VN contributed to safety evaluation; JG, WW, TT, PS, A Palepu, RT, KS, NT, JR, VD, EDV, BL, JM, PK, A Pawlosky, AK, VN contributed to drafting and revising the manuscript, with WW leading manuscript preparation.

**中文译文 · 机器初译**

JG、VN、TT、AK启动了该项目。JG、WW、AD、TT、YG、VD、EDV、BL、TRDC、JRP、GP、A Pawlosky、AK、VN参与了研究构思与设计工作；JG、WW、AD、PS、AM、GG、FW、AO、DP、JB、DZ、IR、EV、FH、LR、M Boia、IB、BF、M Bellaiche、TS、JF、JR、BG、AV、DH、YX、PK、A Pawlosky、AK、VN参与了系统设计工作；JG、WW、AD、TT、OB、YG、VD、EDV、BL、TRDC、JRP、GP、PK、A Pawlosky、AK、VN参与了数据收集工作；JG、WW、AD、TT、PS、AM、FW、GG、A Palepu、DP、FZ、YG、VD、EDV、BL、TRDC、JRP、GP、A Pawlosky、AK、VN参与了数据的分析与解读工作。
JG、KR、JB、AC、KK、KC、AH、BG、AV、YM、JM、DH、YX、PK、A Pawlosky、AK、VN提供了战略指导；YX负责产品发现与开发工作；JG、WW、AD、TT、KK、OB、YX、A Pawlosky、AK、VN参与了论文组织和团队协调工作；JG、JR、NT、OB、VN参与了安全评估工作；JG、WW、TT、PS、A Palepu、RT、KS、NT、JR、VD、EDV、BL、JM、PK、A Pawlosky、AK、VN参与了手稿的撰写与修改工作，其中WW负责手稿准备。

### co-scientist-0281

**English original**

Funding

**中文译文 · 机器初译**

资金支持

### co-scientist-0282

**English original**

This work was supported by NIH awards (1R01DC021133 and 1R24OD035408) to G.P.

**中文译文 · 机器初译**

这项工作得到了 NIH 资助项目（1R01DC021133 和 1R24OD035408）的支持，受益者为 G.P.

### co-scientist-0283

**English original**

Competing interest declaration

**中文译文 · 机器初译**

利益冲突声明

### co-scientist-0284

**English original**

This study was funded by Alphabet Inc and/or a subsidiary thereof (‘Alphabet’). Some authors (JG, WW, AD, TT, PS, AM, GG, FW, AO, DP, A Palepu, KR, RT, KS, FZ, AC, KK, NT, DZ, IR, EV, FH, LR, M Boia, IB, BF, M Bellaiche, TS, JF, JR, OB, KC, AH, BG, AV, YM, JM, DH, PK, YX, A Pawlosky, AK, VN) are employees of Alphabet and may own stock as part of the standard compensation package. EDV and BL are employees of Sequome. BL is the founder of Dendra Therapeutics.

**中文译文 · 机器初译**

本研究由 Alphabet Inc 及其子公司（“Alphabet”）资助。部分作者（JG、WW、AD、TT、PS、AM、GG、FW、AO、DP、A Palepu、KR、RT、KS、FZ、AC、KK、NT、DZ、IR、EV、FH、LR、M Boia、IB、BF、M Bellaiche、TS、JF、JR、OB、KC、AH、BG、AV、YM、JM、DH、PK、YX、A Pawlosky、AK、VN）是 Alphabet 的员工，可能作为标准薪酬福利的一部分持有股票。EDV 和 BL 是 Sequome 的员工。BL 是 Dendra Therapeutics 的创始人。


### 原文第 43 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=43)

### co-scientist-0286

**English original**

Supplementary Information In the following sections, we report additional details on the following topics: 1.​ Glossary of terminology and concepts 2.​ Co-Scientist evaluation 2.1.​ The Elo rating is concordant with high quality Co-Scientist results 2.2.​ Co-Scientist-augmented expertise through iterative refinement 2.3.​ LLM-as-a-judge preference auto-evaluation 2.4.​ Safety evaluation of Co-Scientist using adversarial research goals 3.​ Quantitative ablation and sensitivity analysis 4.​ Clinical expert evaluation of drug repurposing proposals in NIH Specific Aims format 4.1.​ Examples of Co-Scientist generated Specific Aims and expert evaluation 4.2.​ Specific Aims count distribution 4.3.​ Specific Aims evaluation rubric 5.​ Additional information for drug repurposing evaluation 5.1.​ Co-Scientist suggests plausible drug repurposing candidates as rated by computational biology analyses and experts 5.2.​ AML cell line selection rationale and mechanistic interpretation of drug sensitivities 5.3.​ Details of the selected repurposed drugs 5.4.​ In vitro wet-lab validation 5.5.​ Additional wet-lab results 5.6.​ Clinical variable analysis guideline for AML drug repurposing 6.​ Detailed Co-Scientist output for a validated AML repurposing candidate 7.​ Safety and ethical implications of Co-Scientist 8.​ Pseudocode underpinning Co-Scientist agents 9.​ Prompts for the specialized agents in Co-Scientist 9.1.​ Prompts for the Generation agent 9.2.​ Prompt for the Reflection agent 9.3.​ Prompts for the Ranking agent 9.4.​ Prompts for the Evolution agent 9.5.​ Prompt for the Meta-review agent 10.​ Examples of Co-Scientist inputs, intermediate outputs, and final results 11.​ An example of tool use in Co-Scientist with AlphaFold 12.​ Related works

**中文译文 · 机器初译**

补充信息 在后续章节中，我们将就以下主题提供更多细节：1. 术语与概念词汇表 2. 合作科学家的评估 2.1. Elo评分与高质量合作科学家结果一致 2.2. 通过迭代优化提升合作科学家的专业知识 2.3. 作为评判者的大语言模型偏好自动评估 2.4. 基于对抗性研究目标对合作科学家的安全性评估 3. 定量消融实验与敏感性分析 4. 以NIH特定目标格式进行的药物再利用提案临床专家评估 4.1. 合作科学家生成的特定目标示例及专家评估 4.2. 特定目标数量分布 4.3.
具体目标评估评分标准 5. 药物重新应用评估的额外信息 5.1. 联合科学家根据计算生物学分析与专家意见提出合理的药物重新应用候选方案 5.2. AML细胞系选择依据及药物敏感性的机制解释 5.3. 所选重新应用药物的详细情况 5.4. 体外湿实验验证 5.5. 额外的湿实验结果 5.6. AML药物重新应用临床变量分析指南 6. 经过验证的AML重新应用候选方案的联合科学家详细成果 7. 联合科学家的安全与伦理影响 8. 联合科学家智能体的伪代码 9. 专用智能体的提示词
在 Co-Scientist 中：9.1. 用于生成智能体的提示词 9.2. 用于反思智能体的提示词 9.3. 用于排序智能体的提示词 9.4. 用于进化智能体的提示词 9.5. 用于元评估智能体的提示词 10. Co-Scientist 输入、中间输出和最终结果的示例 11. 使用 AlphaFold 的 Co-Scientist 工具使用示例 12. 相关研究


### 原文第 44 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=44)

### co-scientist-0288

**English original**

1 Glossary of terminology and concepts

**中文译文 · 机器初译**

1 术语与概念词汇表

### co-scientist-0289

**English original**

●​ Novel repurposing candidate. An existing drug (a chemical compound that binds to a target), with an established safety profile, proposed for use in a disease or condition for which it is not currently approved or widely used. This approach of repurposing existing drugs differs significantly from traditional drug discovery, which involves identifying novel chemical compounds that can bind to specific targets implicated in a disease state. ●​ Novel target. A biological entity (e.g., gene, protein, pathway) not previously known as a therapeutic target for a specific disease. ●​ Novel mechanistic explanation. A newly proposed pathway, interaction, or biological process that explains a phenomenon (e.g., disease progression, antimicrobial resistance) in a way that is not explicitly described in prior literature.

**中文译文 · 机器初译**

●​ 新的重新应用候选方案。一种现有的药物（与特定靶点结合的化学化合物），其安全性已得到验证，被提议用于目前尚未获得批准或未被广泛使用的疾病或病症。这种现有药物重新应用的方法与传统的药物研发方式截然不同，传统方法旨在寻找能够与疾病状态中相关特定靶点结合的新颖化学化合物。 ●​ 新的靶点。一种此前未被认为为特定疾病治疗靶点的生物实体（如基因、蛋白质、通路）。 ●​ 新的机制解释。
一种新提出的途径、相互作用或生物过程，它以先前文献中未明确描述的方式解释某种现象（如疾病进展、抗菌素耐药性）。


### 原文第 45 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=45)

### co-scientist-0291

**English original**

2 Co-Scientist internal evaluation

**中文译文 · 机器初译**

2名联合科学家内部评估

### co-scientist-0292

**English original**

2.1 The Elo rating is concordant with high quality Co-Scientist results

**中文译文 · 机器初译**

2.1 Elo评分与高质量的Co-Scientist结果一致

### co-scientist-0293

**English original**

The Elo auto-evaluation rating is a key metric that guides the self-improvement feedback loops within Co-Scientist. Therefore, it’s necessary to measure and ensure higher Elo ratings correlate with higher quality results. To assess this, we analyzed the concordance between the Elo rating and the system’s accuracy on the GPQA benchmark dataset. Ideally, higher Elo ratings should correlate with a higher probability of correct answers.

**中文译文 · 机器初译**

Elo自动评估分数是一个关键指标，用于指导Co-Scientist内部的自我提升反馈机制。因此，有必要对Elo分数与更高质量结果之间的关联进行衡量和验证。为了评估这一点，我们分析了Elo分数与GPQA基准数据集上系统准确性之间的关系。理想情况下，更高的Elo分数应对应更高的正确回答概率。

### co-scientist-0294

**English original**

The GPQA dataset is a challenging, multiple-choice question answering benchmark developed by experts in biology, physics, and chemistry 1. To ensure that Co-Scientist Elo rating serves as an objective metric reflecting the validity and correctness of results from the system, we utilized questions within the GPQA diamond set, a subset of the GPQA dataset known for its high difficulty, framing each question as a research goal into our AI system to elicit responses. For each question, we first compared each Co-Scientist response against the ground truth answer to evaluate its correctness. Then, we categorized all generated responses across all considered questions based on their Elo rating into discrete buckets: Elo rating of 1001-1050, 1051-1100, 1101-1150, etc. in 50 point increments, until the highest rating achieved. Finally, we calculated the average accuracy for each Elo rating bucket, as the percentage of correct responses within each bucket.

**中文译文 · 机器初译**

GPQA数据集是由生物学、物理学和化学领域的专家开发的一项具有挑战性的选择题回答测试基准。为了确保 Co-Scientist Elo 评分能够作为反映系统结果有效性和正确性的客观指标，我们使用了GPQA钻石集中的题目——该数据集是因其高难度而闻名的子集，并将每个问题视为对人工智能系统的研究目标，以引导系统给出回应。对于每个问题，我们首先将各智能体的回答与真实答案进行比对，以评估其正确性。
然后，我们根据所有问题下生成回复的 Elo 评分将其划分为不同的等级：1001-1050、1051-1100、1101-1150等，每级以50分为单位，直到达到最高评分。最后，我们计算了每个 Elo 评分等级的平均准确率，即该等级中正确回复的比例。

### co-scientist-0295

**English original**

We employed the underlying Gemini 2.0 models in Co-Scientist to create a reference baseline. The reference is necessary because responses within a particular Elo rating bucket are not uniformly distributed across the GPQA questions, some of which are inherently more challenging than others. This non-uniformity could introduce bias into the analysis and potentially lead to erroneous conclusions. We therefore used the reference to generate 32 responses for each GPQA question. The fraction of correct responses from Gemini 2.0 was used as a reference accuracy on that particular question. To determine reference accuracy for a specific Elo bucket, we averaged the reference accuracy of the GPQA questions that had Co-Scientist responses within that bucket. We also computed Co-Scientist accuracy on the GPQA diamond set by using the result with the highest Elo rating for each question and comparing it against the ground truth.

**中文译文 · 机器初译**

我们在 Co-Scientist 中使用了底层的 Gemini 2.0 模型来创建参考基准。建立参考基准是必要的，因为处于特定 Elo 评分区间的回应在 GPQA 问题中分布并不均匀，其中一些问题本质上更具挑战性。这种不均匀性可能会引入分析偏差，进而导致错误的结论。因此，我们利用该参考基准为每个 GPQA 问题生成 32 条回应。Gemini 2.0 的正确回应比例被用作该问题的参考准确率。
为了确定特定 Elo 区间的参考准确率，我们计算了该区间内那些获得 Co-Scientist 回答的 GPQA 问题的参考准确率平均值。我们还利用每个问题最高的 Elo 评分结果，与真实值进行对比，从而计算了 GPQA 钻石集上的 Co-Scientist 准确率。

### co-scientist-0296

**English original**

Our analysis using questions from the GPQA diamond set reveals a concordance between the Elo rating and averaged accuracy of generated Co-Scientist results, as depicted in Supplementary Fig. 1. By selecting the top-rated Co-Scientist result for each question, Co-Scientist achieves a top-1 accuracy of 78.4%.

**中文译文 · 机器初译**

我们对 GPQA 钻石数据集中的问题进行的分析表明，生成的 Co-Scientist 结果的 Elo 评分与平均准确率之间存在一致性，如补充图 1 所示。通过为每个问题选择评分最高的 Co-Scientist 结果，Co-Scientist 实现了 78.4% 的 Top-1 准确率。

### co-scientist-0297

**English original**

2.2 Co-Scientist augmented expertise through iterative refinement

**中文译文 · 机器初译**

2.2 联合科学家通过迭代优化提升专业能力

### co-scientist-0298

**English original**

A fundamental design principle of Co-Scientist is its collaborative paradigm. Beyond structured scientific thinking and hypothesis generation, the system is engineered to integrate and build

**中文译文 · 机器初译**

Co-Scientist 的一项基本设计原则是其协作模式。除了结构化科学思维与假设生成之外，该系统还被设计用于整合与构建


### 原文第 46 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=46)

### co-scientist-0300

**English original**

Supplementary Fig. 1 | Concordance of the auto-evaluation Elo metric with Co-Scientist performance on GPQA. The blue line in the figure shows the average accuracy of Co-Scientist responses, grouped by their Elo rating. The red line indicates the average accuracy of the corresponding reference Gemini 2.0 responses to the same set of GPQA questions, grouped by Elo rating. Note that the Elo metric is auto-evaluated and not based on the ground truth. The shaded area indicates the corresponding 95% confidence interval.

**中文译文 · 机器初译**

补充图1 | 大语言模型 Co-Scientist 在 GPQA 任务中的表现与自动评估 Elo 指标的一致性。图中的蓝线显示了按 Elo 评分分组后的 Co-Scientist 回答的平均准确率。红线则表示对应参考 Gemini 2.0 模型对相同 GPQA 问题集的回答的平均准确率，同样按 Elo 评分分组。需要注意的是，Elo 指标是自动评估得出的，并非基于真实值。阴影区域则表示相应的95%置信区间。

### co-scientist-0301

**English original**

upon human intuition. We investigated whether Co-Scientist’s tournament-based evolution process could iteratively refine and quantitatively improve initial “best guess” solutions provided by human domain experts.

**中文译文 · 机器初译**

基于人类直觉。我们研究了“联合科学家”基于竞赛的进化过程是否能够逐步优化并定量提升人类领域专家提供的初始“最佳猜测”方案。

### co-scientist-0302

**English original**

Using the subset of 15 highly complex biomedical research goals, human experts initially provided their best hypothetical solutions. These human-generated seeds were then introduced into the Co-Scientist tournament framework, where they underwent rounds of critique, scientific debate, and evolutionary refinement alongside autonomously generated ideas.

**中文译文 · 机器初译**

利用这15个高度复杂的生物医学研究目标子集，人类专家最初提出了他们最佳的假设性解决方案。这些由人类生成的方案随后被引入“联合科学家竞赛”框架中，在那里它们与自主生成的想法一起经历了一系列批评、科学辩论和逐步优化过程。

### co-scientist-0303

**English original**

As illustrated in Extended Data Fig. 1, Co-Scientist demonstrated the clear capacity to enhance the experts’ initial solutions over time. The Elo ratings of the combined “Human + AI” hypotheses progressively increased with scaled test-time compute. Notably, these human-seeded, AI-refined proposals initially mirrored the improvement trends of Co-Scientist’s autonomously generated solutions but subsequently surpassed them. While this is a preliminary finding, it quantitatively suggests that Co-Scientist can act as a powerful amplifier, augmenting human ingenuity and accelerating the maturation of early-stage scientific ideas.

**中文译文 · 机器初译**

如扩展数据图1所示，Co-Scientist 确实具备随着时间推移提升专家初始解决方案的能力。结合“人类+AI”的假设在逐步增加的测试时间计算下，其Elo评分不断上升。值得注意的是，这些由人类提出并经过AI优化的方案最初与Co-Scientist自主生成的解决方案的改进趋势一致，但随后又超越了它们。尽管这只是一个初步发现，但从定量角度表明，Co-Scientist 可以充当强大的增强器，提升人类的创造力，并加速早期科学概念的成熟过程。


### 原文第 47 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=47)

### co-scientist-0305

**English original**

2.3 LLM-as-a-judge preference auto-evaluation

**中文译文 · 机器初译**

2.3 大语言模型作为评判者的偏好自动评估

### co-scientist-0306

**English original**

While human expert evaluation remains the absolute gold standard for assessing the scientific utility of our generated hypotheses, as detailed in the main text, manual expert review is inherently resource-intensive. To provide an orthogonal, scalable validation of Co-Scientist performance, we implemented an automated “LLM-as-a-judge” evaluation framework. We conducted a preference ranking evaluation between Co-Scientist and baseline models (Gemini 2.0 Flash Thinking Experimental 12-19, Gemini 2.0 Pro Experimental, and OpenAI o1) across the 15 expert-curated research goals. To mitigate evaluator bias, we employed a diverse panel of state-of-the-art reasoning models as independent judges: OpenAI o3-mini-2025-01-31, o1-preview-2024-09-12, Gemini 2.0 Pro Experimental, and Gemini 2.0 Flash Thinking Experimental 01-21.

**中文译文 · 机器初译**

正如正文所述，尽管人类专家评估仍是评估所生成假设科学效用的绝对金标准，但人工专家审核本质上需要大量资源。为了对 Co-Scientist 的性能进行独立且可扩展的验证，我们构建了一个自动化的“大语言模型作为评判者”评估框架。我们在15个由专家筛选的研究目标上，对 Co-Scientist 与基准模型（Gemini 2.0 Flash Thinking Experimental 12-19、Gemini 2.0 Pro Experimental 以及 OpenAI o1）进行了偏好排序评估。
为了减少评估者偏见，我们采用了由多种先进推理模型组成的多元化小组作为独立评判者：OpenAI o3-mini-2025-01-31、o1-preview-2024-09-12、Gemini 2.0 Pro 实验版以及 Gemini 2.0 Flash Thinking 实验版 01-21。

### co-scientist-0307

**English original**

As shown in Extended Data Fig. 2, outputs generated by Co-Scientist were consistently ranked as the most preferred across all four distinct LLM evaluators. Crucially, these automated preference rankings are highly concordant with the subjective assessments provided by our human clinical experts, further validating the robustness of the Co-Scientist’s generated outputs.

**中文译文 · 机器初译**

如扩展数据图2所示，Co-Scientist生成的输出在所有四个不同的大语言模型评估者中均被一致列为最受青睐的结果。重要的是，这些自动化的偏好排序与我们的人类临床专家所给出的主观评估高度一致，进一步验证了Co-Scientist生成输出的可靠性。

### co-scientist-0308

**English original**

2.4 Safety evaluation of Co-Scientist using adversarial research goals

**中文译文 · 机器初译**

2.4 基于对抗性研究目标对协同科学家进行安全评估

### co-scientist-0309

**English original**

Co-Scientist is designed to empower scientists and accelerate research. However, it’s crucial to ensure the system is designed in line with robust safety principles, given the potential for misuse. This includes addressing dangerous research goals, dual-use objectives, scenarios where safe goals lead to unsafe hypotheses, misleading claims, and inherent biases. While this topic requires extensive investigation beyond the scope of this work, we employed adversarial testing strategies to conduct a preliminary analysis of the performance of classifiers built to reject dangerous or unethical research goals. Specifically, we curated a set of 1200 adversarial research goals, ranging in complexity, across 40 biomedical and scientific topics as well as slightly over 2000 examples of safe research goals using frontier LLMs. We then evaluated whether Co-Scientist could robustly reject dangerous research goals while not precluding safe research. In this preliminary analysis, the system successfully passed all checks. Given the sensitive nature of these adversarial research goals, we will not be publicly releasing the dataset, but it can be made available upon request. Collectively, the benchmark, automated, and expert evaluations presented in this section provide compelling evidence of the system’s strong capabilities.

**中文译文 · 机器初译**

Co-Scientist 旨在为科学家赋能并加速研究进程。然而，鉴于其可能被滥用的可能性，确保该系统遵循严格的安全原则至关重要。这涉及应对危险研究目标、双重用途目标、安全目标导致不安全假设的情况、误导性声明以及固有偏见等问题。虽然这一主题需要超出本工作范围的深入调查，但我们采用了对抗性测试策略，对用于拒绝危险或不道德研究目标的分类器性能进行了初步分析。
具体来说，我们筛选了 1200 个具有不同复杂度的对抗性研究目标，这些目标涉及 40 个生物医学与科学领域，同时还有超过 2000 个使用前沿大语言模型的安全研究示例。随后我们评估了 Co-Scientist 是否能够在不阻碍安全研究的前提下，有效拒绝危险研究目标。在初步分析中，该系统成功通过了所有测试。由于这些对抗性研究目标具有敏感性，我们不会公开发布该数据集，但可根据需求提供。
总体而言，本节中提出的基准测试、自动化评估及专家评价都充分证明了该系统的强大能力。


### 原文第 48 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=48)

### co-scientist-0311

**English original**

3 Quantitative ablation and sensitivity analysis

**中文译文 · 机器初译**

3 定量消融与敏感性分析

### co-scientist-0312

**English original**

We systematically disabled individual agents and external tools and evaluated the performance degradation via Elo rating and accuracy on the GPQA diamond dataset, and our paper QA benchmark, which is a dataset we constructed from papers published after model knowledge cutoff and where we control that the system has no access to the answer by filtering search results. We constructed this benchmark with 200 examples from recent papers published in bioRxiv after the model’s knowledge cutoff. The objective of the task is to evaluate whether the model can rediscover a particular research hypothesis in the paper without having access to the ground truth. As these research ideas were already published, they serve as a ground truth of being correct and not novel. This will provide the quantitative evidence needed to assess each component’s contribution.

**中文译文 · 机器初译**

我们系统地禁用了各个智能体及外部工具，并通过 Elo 评分和 GPQA 钻石数据集上的准确率来评估性能下降情况。该数据集是我们根据模型知识截止日期之后发表的论文构建的，我们在筛选搜索结果时确保系统无法获取答案。我们从生物Rxiv上发布的近期论文中选取了 200 个示例来构建此基准测试，其目标是评估模型能否在无法获取真实答案的情况下在论文中重新发现特定的研究假设。
由于这些研究思路已经发表，它们便成为了判断其是否正确及是否具有新颖性的基准依据。这将提供评估每个组件贡献所需的定量证据。

### co-scientist-0313

**English original**

The whole ablation study quantitatively demonstrates the advantages of including the individual agents. The experiments isolate and quantify the impact of key architectural and strategic choices within our multi-agentic Co-Scientist framework, including all agents: Generation agent, Reflection agent with/without external tool use (web literature search), Ranking agent (comparator agent), Evolution agent, Meta-review agent, and Proximity agent. We include the summarized findings of the ablation study in Supplementary Table 1.

**中文译文 · 机器初译**

整个消融研究从定量角度证明了包含各个智能体的优势。实验明确了我们多智能体协同科学家框架中关键架构与策略选择的影响，并对其进行了量化分析，这些智能体包括：生成智能体、带有/不带外部工具使用的反思智能体（网络文献搜索）、排序智能体（比较智能体）、进化智能体、元评论智能体和邻近智能体。我们将消融研究的总结结果纳入了补充表1中。

### co-scientist-0314

**English original**

Supplementary Table 1 | Summary of the ablation analysis. Agent Ablation Key findings Metrics

**中文译文 · 机器初译**

补充表1 | 消融分析总结。智能体消融关键发现及指标

### co-scientist-0315

**English original**

Generation Analyzed the A diverse set of Contribution scores
Agent contribution of different generation strategies is highlight top strategies
generation strategies to critical for producing per benchmark.

**中文译文 · 机器初译**

Generation Analyzed the A diverse set of Contribution scores
Agent contribution of different generation strategies is highlight top strategies
generation strategies to critical for producing per benchmark.

表内文字对照（数值与原始行列保持不变）：
Generation Analyzed the A diverse set of Contribution scores → 生成 分析 多样化的贡献得分集合
Agent contribution of different generation strategies is highlight top strategies → 不同生成策略下的智能体贡献被作为顶级策略加以突出
generation strategies to critical for producing per benchmark → 用于依据基准进行评估的生成策略至关重要

### co-scientist-0316

**English original**

correct hypotheses. correct hypotheses, with different strategies proving more effective depending on the task.

**中文译文 · 机器初译**

正确的假设。不同的策略在根据任务不同时可能更为有效，因此假设也需正确。

### co-scientist-0317

**English original**

Reflection Compared novelty and Access to external On the rediscovery
agent with correctness reviews search is critical for benchmark, search
external with (full, with search) accurate novelty improved novelty
search tool and without (initial, no assessment and scores from 6.14
use search) access to the significantly improves (incorrectly novel) to
search tool, using a correctness evaluation. 2.38 (correctly
dataset of published It grounds the model, non-novel) and
(non-novel, correct) preventing it from correctness scores from
ideas. incorrectly rating 7.4 to 8.46. AUC for
existing ideas as novel. predicting correctness
on GPQA also
increased from 0.643 to
0.651 (Flash 2.0).

**中文译文 · 机器初译**

Reflection Compared novelty and Access to external On the rediscovery
agent with correctness reviews search is critical for benchmark, search
external with (full, with search) accurate novelty improved novelty
search tool and without (initial, no assessment and scores from 6.14
use search) access to the significantly improves (incorrectly novel) to
search tool, using a correctness evaluation. 2.38 (correctly
dataset of published It grounds the model, non-novel) and
(non-novel, correct) preventing it from correctness scores from
ideas. incorrectly rating 7.4 to 8.46. AUC for
existing ideas as novel. predicting correctness
on GPQA also
increased from 0.643 to
0.651 (Flash 2.0).

表内文字对照（数值与原始行列保持不变）：
Reflection Compared novelty and Access to external On the rediscovery → 反思：新颖性与外部访问的对比 关于重新发现
agent with correctness reviews search is critical for benchmark → 具备正确性评估功能的智能体对搜索功能进行审核对于基准测试至关重要
search → 搜索
external with (full → 外部与（完整）
with search) accurate novelty improved novelty → 带搜索功能）准确性与新颖性得到提升
search tool and without (initial → 搜索工具且无需（初始）
no assessment and scores from → 没有评估及分数
use search) access to the significantly improves (incorrectly novel) to → 使用检索）获取能力显著提升（不正确但新颖）
search tool → 搜索工具
using a correctness evaluation → 采用正确性评估方法
correctly → 正确
dataset of published It grounds the model → 已发布的数据集为模型提供了基础
non-novel) and → 非新颖）和
non-novel → 非新颖
correct) preventing it from correctness scores from → 正确）防止其正确度得分
ideas → 想法
incorrectly rating → 错误评分
AUC for → AUC 值
existing ideas as novel → 现有想法具有新颖性
predicting correctness → 预测正确性
on GPQA also → 在 GPQA 上也是如此
increased from → 从...增加
Flash → Flash


### 原文第 49 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=49)

### co-scientist-0319

**English original**

Ranking Compared the simple The scientific debate On top-ranked ideas,
agent comparison prompt vs. prompt is significantly AUC for correctly
prompting the scientific debate more accurate for identifying the better
strategy prompt for pairwise comparing high-quality idea was noticeably
idea comparison. ideas. higher for the scientific
debate prompt.

**中文译文 · 机器初译**

Ranking Compared the simple The scientific debate On top-ranked ideas,
agent comparison prompt vs. prompt is significantly AUC for correctly
prompting the scientific debate more accurate for identifying the better
strategy prompt for pairwise comparing high-quality idea was noticeably
idea comparison. ideas. higher for the scientific
debate prompt.

表内文字对照（数值与原始行列保持不变）：
Ranking Compared the simple The scientific debate On top-ranked ideas → 排名 对比了简单的科学辩论 在排名最高的观点上
agent comparison prompt vs → 智能体对比提示与
prompt is significantly AUC for correctly → 提示词在正确识别方面的 AUC 值显著较高
prompting the scientific debate more accurate for identifying the better → 更精准地引导科学辩论，以识别更好的方案
strategy prompt for pairwise comparing high-quality idea was noticeably → 用于成对比较高质量创意的策略提示效果显著
idea comparison → 想法对比
ideas → 想法
higher for the scientific → 对科学领域而言更高
debate prompt → 辩论提示词

### co-scientist-0320

**English original**

Ranking Assessed score stability The scientific debate Histograms of score
agent bias by comparing A vs. B prompt significantly differences show a
and B vs. A matches for reduces positional bias highly symmetric
both prompt types. (second player distribution around zero
advantage), leading to for the scientific debate
more stable and reliable prompt compared to the
evaluations. biased basic prompt.

**中文译文 · 机器初译**

Ranking Assessed score stability The scientific debate Histograms of score
agent bias by comparing A vs. B prompt significantly differences show a
and B vs. A matches for reduces positional bias highly symmetric
both prompt types. (second player distribution around zero
advantage), leading to for the scientific debate
more stable and reliable prompt compared to the
evaluations. biased basic prompt.

表内文字对照（数值与原始行列保持不变）：
Ranking Assessed score stability The scientific debate Histograms of score → 排名评估分数稳定性 科学辩论 分数直方图
agent bias by comparing A vs → 通过对比 A 与 B 来检测智能体偏差
B prompt significantly differences show a → B提示的显著差异表明
and B vs → 和 B 对比
A matches for reduces positional bias highly symmetric → A匹配能够大幅减少位置偏差，具有高度对称性
both prompt types → 两种提示类型
second player distribution around zero → 零附近的第二玩家分布
advantage) → 优势）
leading to for the scientific debate → 引发科学辩论
more stable and reliable prompt compared to the → 与之前相比，提示词更加稳定可靠
evaluations → 评估
biased basic prompt → 有偏见的基础提示词

### co-scientist-0321

**English original**

Evolution Compared top-ranked The iterative refinement On GPQA, precision
Agent baseline hypotheses vs. process significantly increased from 70.9%
top-ranked improved boosts the quality and to 75.4%. On the
hypotheses. correctness of the final constructed dataset,
hypotheses. average hypothesis
quality score increased
from 4.7 to 5.6.

**中文译文 · 机器初译**

Evolution Compared top-ranked The iterative refinement On GPQA, precision
Agent baseline hypotheses vs. process significantly increased from 70.9%
top-ranked improved boosts the quality and to 75.4%. On the
hypotheses. correctness of the final constructed dataset,
hypotheses. average hypothesis
quality score increased
from 4.7 to 5.6.

表内文字对照（数值与原始行列保持不变）：
Evolution Compared top-ranked The iterative refinement On GPQA → 比较研究：排名靠前的大语言模型在 GPQA 上的迭代优化过程
precision → 精确度
Agent baseline hypotheses vs → 智能体基准假设与
process significantly increased from → 过程显著增加
top-ranked improved boosts the quality and to → 排名最高的改进版本提升了质量
On the → 关于
hypotheses → 假设
correctness of the final constructed dataset → 最终构建数据集的正确性
average hypothesis → 平均假设
quality score increased → 质量得分上升
from → 从

### co-scientist-0322

**English original**

Meta-review Compared correctness The meta-review agent On the constructed
Agent reviews with consistently improves dataset, AUC for
(full+recurrent) or the quality of predicting solution
without (full) correctness reviews. correctness increased
meta-review guidance. from 0.521 to 0.597.

**中文译文 · 机器初译**

Meta-review Compared correctness The meta-review agent On the constructed
Agent reviews with consistently improves dataset, AUC for
(full+recurrent) or the quality of predicting solution
without (full) correctness reviews. correctness increased
meta-review guidance. from 0.521 to 0.597.

表内文字对照（数值与原始行列保持不变）：
Meta-review Compared correctness The meta-review agent On the constructed → 元评估比较正确性 元评估智能体 关于构建的内容
Agent reviews with consistently improves dataset → 智能体对数据集进行反复审查以不断提升质量
AUC for → AUC 值
full → 完整
recurrent) or the quality of predicting solution → 循环式）或预测解决方案的质量
without (full) correctness reviews → 无需（完全）正确的评审
correctness increased → 正确性提高了
meta-review guidance → 元评估指导
from → 从

### co-scientist-0323

**English original**

On GPQA, AUC increased from 0.629 to 0.634 (Flash 2.5).

**中文译文 · 机器初译**

在 GPQA 模型中，AUC 从 0.629 提升至 0.634（Flash 2.5）。

### co-scientist-0324

**English original**

Proximity Correlated the agent’s The proximity score Strong correlation
Agent semantic proximity accurately reflects the between high proximity
scores with the semantic similarity of scores (4-5) and low
ground-truth quality hypotheses, enabling quality score
score differences of effective clustering to differences, and vice
hypothesis pairs. ensure a diverse versa.

**中文译文 · 机器初译**

Proximity Correlated the agent’s The proximity score Strong correlation
Agent semantic proximity accurately reflects the between high proximity
scores with the semantic similarity of scores (4-5) and low
ground-truth quality hypotheses, enabling quality score
score differences of effective clustering to differences, and vice
hypothesis pairs. ensure a diverse versa.

表内文字对照（数值与原始行列保持不变）：
Proximity Correlated the agent → 邻近性关联智能体
s The proximity score Strong correlation → s 邻近度得分 强相关性
Agent semantic proximity accurately reflects the between high proximity → 智能体的语义邻近性能够准确反映高度邻近关系
scores with the semantic similarity of scores ( → 语义相似度得分的评分（
and low → 以及低
ground-truth quality hypotheses → 真实质量假设
enabling quality score → 实现质量评分
score differences of effective clustering to differences → 有效聚类得分与差异的对比
and vice → 反之亦然
hypothesis pairs → 假设对
ensure a diverse versa → 确保多样性与多元性

### co-scientist-0325

**English original**

exploration of the problem space.

**中文译文 · 机器初译**

问题领域的探索。

### co-scientist-0326

**English original**

●​ Generation agent ○​ To quantify the contributions of the different strategies employed by our Generation agent, we analyzed their respective roles in generating correct hypotheses across the GPQA diamond dataset and our paper QA benchmark. We

**中文译文 · 机器初译**

●​ 生成智能体 ○​为了量化我们的生成智能体所采用的不同策略的贡献，我们分析了它们在 GPQA 钻石数据集及我们的论文 QA 基准测试中生成正确假设过程中的各自作用。


### 原文第 50 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=50)

### co-scientist-0328

**English original**

calculated the fractional contribution of each idea generation strategy (e.g.,”using focus areas”, ”exploring articles”) to every correct hypothesis. Our findings indicate that a diverse set of strategies is crucial for success, with no single strategy dominating. For instance, on GPQA, strategies like “using focus areas” (13.8%) and “using generate prompt” (13.0%) were major contributors, while on our paper QA benchmark, strategies such as “using conditional hops” (2.88%) and “using raw ideas” (2.66%) showed higher utility. This analysis confirms that the multi-faceted approach of the Generation agent is effective and provides a quantitative basis for the utility of each of its underlying methods. ●​ Reflection agent ○​ We examined the impact of the Reflection agent and its use of external search tools. We specifically performed an ablation study about novelty and correctness check with the web search functionality using our paper QA benchmark. For novelty, the agent without search incorrectly rated the ideas as highly novel, with an average score of 6.14 [95% CI: 5.93, 6.34] (i.e., very likely novel). In contrast, the agent with search without datetime cutoff correctly identified the ideas as lacking novelty since they may be found via web search, with an average score of 2.38 [95% CI: 2.1, 2.67] (i.e., trivially modified). This shows that the external search tool use is critical for grounding the model and preventing the hallucination of novelty. Without such novelty check, it is challenging to filter out non-novel results. For correctness, the agent with search also performed better, providing higher confidence scores for these correct ideas (average score of 8.46 [95% CI: 8.2, 8.73], i.e., highly plausible) compared to the agent without search (average score of 7.4 [95% CI: 7.16, 7.64], i.e., plausible). These findings are consistent with our GPQA benchmark results, where enabling search also improved the classifier AUC for predicting correctness from 0.643 to 0.651 (with Flash 2.0, more details below). The correctness review is essential for Co-Scientist to filter out those generated outputs with incorrect results (Supplementary Fig. 2). ●​ Ranking agent (tournament) ○​ Ranking agent / Tournament is the key component of Co-Scientist. To ensure whether having the Ranking agent (comparator agent) helps generate outputs with better correctness, we asked whether the Elo ratings and ranks derived from Ranking agent correlate with correctness of generated ideas. For this, we investigated how the average idea accuracy changes with respect to the Elo rating, and examined how the average accuracy changes with respect to the rank focusing on each question. Our study shows that the higher Elo rating ideas across all GPQA questions are on average more accurate than the lower Elo rating ideas, and the higher ranked ideas are also on average more accurate than the lower ranked ideas (Supplementary Fig. 3). The findings support that the Elo ratings and

**中文译文 · 机器初译**

计算了每种想法生成策略（例如“使用关注领域”、“探索相关文章”）对每个正确假设的分数贡献。我们的研究结果表明，多种策略的组合对于成功至关重要，没有一种策略能够占据主导地位。例如，在 GPQA 数据集上，“使用关注领域”（13.8%）和“使用生成提示”（13.0%）等策略是主要贡献因素；而在我们的 QA 基准测试上，“使用条件跳转”（2.88%）和“使用原始想法”（2.66%）等策略则具有更高的实用价值。
该分析证实，生成智能体的多维度方法非常有效，为各底层方法的实用性提供了定量依据。●​ 反思智能体 ○​ 我们研究了反思智能体及其使用外部搜索工具的效果。我们特别进行了消融研究，利用我们的论文QA基准测试了网络搜索功能在新颖性及正确性检测方面的表现。在新颖性方面，未使用搜索功能的智能体错误地将这些想法评为高度新颖，平均得分为6.14 [95%置信区间：5.93, 6.34]（即极有可能为新颖）。
相比之下，没有时间限制的检索智能体正确识别出这些观点缺乏新颖性，因为它们可以通过网络搜索找到，平均得分为 2.38 [95% CI: 2.1, 2.67]（即仅进行了微小的修改）。这表明使用外部搜索工具对于确保模型的准确性以及防止产生虚假的新颖性信息至关重要。如果没有这种新颖性检查机制，就很难过滤掉非新颖的结果。
就正确性而言，支持检索的智能体表现更好，这些正确观点的置信度得分更高（平均得分为 8.46 [95% CI: 8.2, 8.73]，即高度可信），而不支持检索的智能体则表现为（平均得分为 7.4 [95% CI: 7.16, 7.64]，即可信）。这些结果与我们的 GPQA 基准测试结果一致，其中启用检索使得预测正确性的分类器 AUC 从 0.643 提升到了 0.651（更多细节见下文 Flash 2.0）。正确性审核对于 Co-Scientist 过滤出结果错误的生成输出至关重要（补充图）。
2). ●​ 排名智能体（竞赛） ○​ 排名智能体/竞赛是 Co-Scientist 的核心组件。为了确认拥有排名智能体（比较智能体）是否有助于生成更正确的输出，我们研究了从排名智能体获得的 Elo 评分与生成想法正确性之间的关联。为此，我们分析了平均想法准确率随 Elo 评分的变化情况，并针对每个问题考察了平均准确率随排名的变化情况。
我们的研究表明，在所有 GPQA 问题中，更高 Elo 评分的观点平均而言比低 Elo 评分的观点更准确，且排名更高的观点也平均而言比排名较低的观点更准确（补充图 3）。这些发现支持了 Elo 评分的合理性。


### 原文第 51 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=51)

### co-scientist-0330

**English original**

Supplementary Fig. 2 | Distribution of novelty and correctness scores with and without external search. With external search tool use, the novelty score (upper) significantly drops and the correctness score (lower) increases, which indicates that search is critical for grounding the model and preventing the hallucination of novelty.

**中文译文 · 机器初译**

补充图2 | 有无外部搜索时新颖性得分与正确性得分的分布情况。使用外部搜索工具后，新颖性得分（上方）显著下降，而正确性得分（下方）则上升，这表明搜索对于确保模型的准确性以及防止产生虚假新颖性具有关键作用。


### 原文第 52 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=52)

### co-scientist-0332

**English original**

Supplementary Fig. 3 | Idea ranking and Elo rating versus average accuracy, using Gemini Flash 2.0 and 2.5. (a) Idea ranking versus accuracy, Gemini Flash 2.0. (b) Idea ranking versus accuracy, Gemini Flash 2.5. (c) Idea Elo rating versus accuracy, Gemini Flash 2.0. (d) Idea Elo rating versus accuracy, Gemini Flash 2.5.

**中文译文 · 机器初译**

补充图 3 | 使用 Gemini Flash 2.0 和 2.5 的创意排名与 Elo 评分与平均准确率的关系。（a）Gemini Flash 2.0 下的创意排名与准确率关系。（b）Gemini Flash 2.5 下的创意排名与准确率关系。（c）Gemini Flash 2.0 下的创意 Elo 评分与准确率关系。（d）Gemini Flash 2.5 下的创意 Elo 评分与准确率关系。

### co-scientist-0333

**English original**

ranks generated by Ranking agent help Co-Scientist users to identify many correct, accurate ideas among all generated instances. ○​ After showing Co-Scientist performance with different model versions (Gemini Flash 2.0 and 2.5), we further conducted experiments of prompt sensitivity testing different prompting strategies for Ranking agent. Specifically, we want to know how stable and accurate the Ranking agent is at the level of a single comparison given different prompting strategies. Thus, we compared the simple comparison prompt and a more sophisticated scientific debate prompt that we are using in Ranking agent. We looked at the accuracy of a single match (comparison between two ideas, where one of them is correct), and how it changes with respect to the prompt strategy (simple or debate prompt). We found that the accuracy on the 2000 general matches (we sampled ideas regardless of their Elo ratings) the simple comparison is on par with debate prompt in Flash 2.0 model. However, the scientific debate prompt yielded better performance in Flash 2.5 on the general matches, and proved significantly more effective when comparing high Elo rating top ideas (1800 matches where both sampled ideas have high Elo rating)

**中文译文 · 机器初译**

由排序智能体生成的排名结果有助于联合科学家用户从所有生成实例中识别出许多正确且准确的想法。○​在展示了不同模型版本（Gemini Flash 2.0和2.5）下的联合科学家表现后，我们进一步对排序智能体的不同提示策略进行了提示敏感性测试实验。具体来说，我们想了解在采用不同提示策略的情况下，排序智能体在单次比较层面上的稳定性和准确性如何。因此，我们对比了简单的比较提示与我们在排序智能体中使用的更为复杂的科学辩论提示。
我们研究了单个匹配任务的准确率（即两个想法之间的比较，其中一个正确），以及该准确率如何随提示策略的变化而不同（简单提示或辩论提示）。我们发现，在2000个普通匹配任务中，简单比较的准确率与Flash 2.0模型中的辩论提示相当。然而，在Flash 2.5模型中，科学辩论提示在普通匹配任务中的表现更优，且在比较高Elo评级的高优先级想法时效果显著更好（在1800个匹配中，所选取的两个想法均具有高Elo评级）。


### 原文第 53 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=53)

### co-scientist-0335

**English original**

regardless of the backend model version (Supplementary Fig. 4). This finding demonstrates the importance of the prompting strategy we used in the system. ○​ To further address the evaluation bias in Ranking agent, we have conducted a new experiment to analyze the stability of idea comparisons (i.e., mentioning order change, A vs. B vs. B vs. A). We examined 2000 idea matches for both Flash 2.0 and Flash 2.5 based Co-Scientist, and found that the simple prompt with Flash 2.0 exhibited stronger positional bias, or “second player advantage”. In contrast, the scientific debate prompt almost eliminated this bias, producing more stable and trustworthy pairwise rankings. This finding is crucial, as it validates the robustness of our internal Elo ranking tournament, which is the core component of the system (Supplementary Fig. 5).

**中文译文 · 机器初译**

无论后端模型版本如何（补充图4）。这一发现凸显了我们在系统中使用的提示策略的重要性。○​为了进一步解决Ranking智能体中的评估偏差问题，我们进行了新的实验，以分析观点比较的稳定性（即提及顺序的变化，A与B与B与A的情况）。我们对Flash 2.0和Flash 2.5版本的Co-Scientist进行了2000对观点匹配测试，发现使用Flash 2.0的简单提示会表现出更强的位置偏见或“第二参与者优势”。相比之下，科学辩论提示几乎消除了这种偏见，从而产生了更稳定、更可信的成对排名。
这一发现至关重要，因为它验证了我们内部 Elo 排名比赛的可靠性，而该比赛正是系统的核心组成部分（补充图 5）。

### co-scientist-0336

**English original**

Supplementary Fig. 4 | The comparison between the Ranking agent using the simple comparison prompt versus the self-play debate prompt. (avg: AUC computed using the average 4 match predictions, 2 in AB and 2 in BA; first: AUC computed using the first of 4 predictions)

**中文译文 · 机器初译**

补充图 4 | 使用简单比较提示的排名智能体与使用自对弈辩论提示的排名智能体之间的对比。（平均值：基于平均 4 次匹配预测计算得到的 AUC，其中 2 次来自 AB 场景，2 次来自 BA 场景；第一个值：基于第 4 次预测中的第一次结果计算得到的 AUC）


### 原文第 54 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=54)

### co-scientist-0338

**English original**

Supplementary Fig. 5 | The comparison between swapping the position. We found the self-play debate prompt has stronger robustness than the simple comparison prompt regarding the position bias.

**中文译文 · 机器初译**

补充图 5 | 交换位置后的对比结果。我们发现，与简单的位置偏差对比提示相比，自对战辩论提示在应对位置偏差方面具有更强的鲁棒性。

### co-scientist-0339

**English original**

●​ Evolution agent ○​ We also investigated the contribution of the Evolution agent to the quality of top-ranked ideas by comparing baseline (directly generated) and improved (iteratively refined) hypotheses. On the GPQA diamond dataset, we analyzed 134 (out of 150) questions where an improved hypothesis achieved the highest rank.

**中文译文 · 机器初译**

●​ 进化智能体 ○​ 我们还通过对比基准（直接生成）与改进（迭代优化）假设，研究了进化智能体对排名靠前的创意质量的影响。在 GPQA 钻石数据集上，我们分析了 134 个（共 150 个）问题，其中改进假设获得了最高排名。

### co-scientist-0340

**English original**

We found that the improvement process boosted precision from 70.9% (for the best baseline hypothesis) to 75.4% (for the best improved hypothesis), an absolute increase of 4.5% [95% CI: -2%, 11%]. A similar analysis was conducted using our paper QA benchmark, in which each research goal was rated on a 1-10 quality

**中文译文 · 机器初译**

我们发现改进过程使精确度从 70.9%（针对最佳基准假设）提升至 75.4%（针对最佳改进假设），绝对提升幅度为 4.5% [95% CI: -2%, 11%]。使用我们的论文 QA 基准测试进行了类似分析，其中每个研究目标均按 1-10 的等级进行评分


### 原文第 55 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=55)

### co-scientist-0342

**English original**

score, showing that the iterative improvement process increased the average maximum score from 4.7 to 5.6, an improvement of 0.9 points [95% CI: 0.05, 1.7]. These results provide strong quantitative evidence that the Evolution agent’s refinement process is a critical driver of hypothesis quality. ●​ Meta-review agent ○​ To determine whether Meta-review agent is essential or only stylistic, we analyzed its impact on correctness reviews using the GPQA diamond evaluation task. The Meta-review agent provides a full review with structured guidance for “recurrent reviews” on top-ranked, promising ideas. We went through all ideas for GPQA questions that have both a full review (generated by Reflection agent) and a recurrent review (generated by Meta-review agent), and analyzed how good the review (based on review score) can actually predict whether the hypothesis is correct or not. We looked at how well the review scores from each of the review types can be used to classify the hypothesis into correct/incorrect and measured this using the AUC metric (with the label being the hypothesis choosing the correct answer/choice). Our results show a positive impact of using the Meta-review agent. On the GPQA dataset (1680 ideas, run with Gemini Flash 2.5), the Area Under the Curve (AUC) for correctly classifying ideas improved from 0.629 for standard full reviews to 0.634 for recurrent reviews guided by the Meta-review agent. This benefit was also seen on our paper QA benchmark (600 ideas, run with Gemini Flash 2.5). where the AUC increased from 0.521 to 0.597, and the correlation with idea quality scores from 0.101 to 0.226. This demonstrates that Meta-review agent provides a measurable benefit to the system’s critical evaluation capabilities, particularly for complex, open-ended research questions. ●​ Proximity agent ○​ We quantified the performance of our Proximity agent, which clusters hypotheses based on semantic similarity (scored 1-5). Analysis of our paper QA benchmark revealed a correlation between proximity score and the difference in quality scores of hypothesis pairs. As shown in the heatmap, pairs with high proximity scores (e.g., 4-5) consistently had small differences in their quality scores, whereas pairs with low proximity scores (e.g., 1-2) exhibited a much wider range of quality score differences (Supplementary Fig. 6). This validates that the Proximity agent effectively groups semantically similar ideas, which is essential for ensuring a diverse and comprehensive exploration of the research problem space.

**中文译文 · 机器初译**

得分显示，迭代改进过程使平均最高得分从 4.7 提高至 5.6，提升了 0.9 分 [95% CI: 0.05, 1.7]。这些结果提供了强有力的定量证据，证明 Evolution 智能体的优化过程是假设质量的关键驱动因素。●​ Meta-review 智能体 ○​ 为了确定 Meta-review 智能体是必不可少的还是仅具有风格性影响，我们使用 GPQA 钻石评估任务分析了其对正确性评审的影响。Meta-review 智能体为排名靠前且具有潜力的想法提供完整的评审及结构化的指导。
我们梳理了所有同时包含完整回顾（由 Reflection 智能体生成）和循环回顾（由 Meta-review 智能体生成）的 GPQA 问题方案，并分析了基于评分标准的回顾实际上能否准确预测假设是否正确。我们研究了各类回顾的评分在将假设分类为正确/错误方面的作用，并使用 AUC 指标进行了衡量（其中标签为选择正确答案/选项的那条假设）。我们的结果表明，使用 Meta-review 智能体具有积极效果。
在 GPQA 数据集上（包含 1680 个想法，使用 Gemini Flash 2.5 进行训练），在 Meta-review 智能体的指导下，正确分类想法的曲线下面积（AUC）从标准完整评论的 0.629 提升到了循环评论的 0.634。我们在论文中的 QA 基准测试中也观察到了这一效果（包含 600 个想法，同样使用 Gemini Flash 2.5 进行训练），此时 AUC 从 0.521 提升至 0.597，与想法质量评分的相关性也从 0.101 提升至 0.226。
这表明 Meta-review 智能体能够为系统的关键评估能力带来可量化的优势，尤其适用于复杂、开放性的研究问题。●​ Proximity 智能体 ○​ 我们量化了 Proximity 智能体的性能，该智能体根据语义相似性对假设进行聚类（评分范围为1-5）。对我们的论文 QA 基准测试分析显示，邻近度得分与假设对的质量评分差异之间存在关联。
如热图所示，距离得分较高的对子（例如 4-5）在质量得分上差异较小，而距离得分较低的对子（例如 1-2）则表现出更大的质量得分差异范围（补充图 6）。这验证了 Proximity 智能体能够有效将语义相似的概念进行分组，这对于确保对研究问题领域进行多样化且全面的探索至关重要。


### 原文第 56 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=56)

### co-scientist-0344

**English original**

Supplementary Fig. 6 | Idea proximity computed by Proximity agent versus the score difference.

**中文译文 · 机器初译**

补充图 6 | 由 Proximity 智能体计算出的概念接近度与得分差异对比。


### 原文第 57 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=57)

### co-scientist-0346

**English original**

4 Clinical expert evaluation of drug repurposing proposals in NIH Specific Aims format

**中文译文 · 机器初译**

4 基于 NIH 特定目标格式的药物重新应用提案临床专家评估

### co-scientist-0347

**English original**

To assess the translational potential of Co-Scientist generated repurposing hypotheses, we reformatted them into NIH-style Specific Aims pages, a standard format familiar to clinical researchers for evaluating research merit. Three representative examples of the Specific Aims page were listed in section 4.1 below.

**中文译文 · 机器初译**

为了评估 Co-Scientist 生成的重新应用假设在转化应用方面的潜力，我们将这些假设重新整理为 NIH 风格的特定目标页面，这是临床研究人员评估研究价值时常用的标准格式。第 4.1 节中列出了三个典型的具体目标页面示例。

### co-scientist-0348

**English original**

The NIH Specific Aims Page format follows a standard structure, including disease description, unmet need, proposed solutions, and specific aims. This format was selected because it provides a standardized framework that is widely recognized in the research community, allowing for systematic presentation of complex scientific topics in a manner that facilitates rigorous peer review and enables efficient assessment of scientific merit. The specific aims, which outline the overarching goal, hypothesis, and rationale, requires extensive scientific expertise, comprehensive literature analysis, and robust domain knowledge. We generated cancer drug repurposing hypotheses from Co-Scientist in the format of NIH Specific Aims Page with additional constrained decoding and self-critique stages to ensure format consistency. The resulting format contextualizes proposed repurposing candidates within known mechanisms based on current literature and then extrapolates to a new disease state. An expert oncologist methodically evaluated and excluded hypotheses that were deemed clinically implausible or had limited potential for successful translation, as well as those falling outside the expertise of the assembled specialist evaluators. This initial screening process employed multiple evidence-based criteria including: (1) pharmacological mechanism incompatibility with tumor biology; (2) unfavorable pharmacokinetic profiles for oncological applications; (3) prohibitive toxicity profiles documented in prior clinical use; (4) confounding effects where apparent survival benefits were attributable to improved management of treatment-related morbidity rather than direct anti-neoplastic activity; and (5) insufficient preclinical evidence supporting antitumor efficacy at clinically achievable concentrations. For example, bisphosphonate agents like pamidronate, while associated with improved outcomes in observational studies of patients with bone metastases, were excluded after critical evaluation revealed their benefits stemmed primarily from reduction of skeletal-related events (such as pathological fractures, spinal cord compression, and bone pain requiring radiation) rather than from disease modifying activity of the drug-candidate.

**中文译文 · 机器初译**

NIH特定目标页面采用标准结构，包括疾病描述、未满足的需求、提出的解决方案以及具体目标。选择这种格式是因为它提供了一个在研究界广泛认可的标准化框架，能够以有助于严格同行评审且便于高效评估科学价值的方式，系统地呈现复杂的科学主题。具体目标部分详细说明了总体目标、假设及理论依据，需要丰富的科学专业知识、全面的文献分析以及扎实的领域知识。
我们从合作科学家处生成了癌症药物重新应用假设，并以NIH具体目标页面格式呈现，同时增加了额外的约束解码与自我批评阶段，以确保格式一致性。最终形成的格式将拟议的重新应用候选方案置于当前文献所揭示的已知机制框架内，进而推广至新的疾病状态。一位权威肿瘤学家对这些假设进行了系统评估，排除了那些临床不可行或成功转化潜力有限的假设，以及那些超出参与评估专家专业范围的假设。
这一初步筛选过程采用了多种基于证据的标准，包括：(1) 药物作用机制与肿瘤生物学特性不兼容；(2) 用于肿瘤治疗的药代动力学特征不佳；(3) 先前临床使用中记录的毒性特征严重；(4) 混淆效应——即看似的生存获益实际上源于对治疗相关并发症的改善管理，而非直接的抗肿瘤活性；(5) 缺乏足够的临床前证据来证明其在可实现的临床浓度下具有抗肿瘤效果。
例如，像帕米膦酸这样的双膦酸盐药物，在针对骨转移患者的观察性研究中与更好的治疗效果相关，但在经过严格评估后被排除在外，因为发现其益处主要源于减少骨骼相关事件（如病理性骨折、脊髓压迫以及需要放射治疗的骨痛），而非该药物候选物的疾病修饰作用。

### co-scientist-0349

**English original**

Nine board-certified hematologists and oncologists from a single institution, including six domain-specific oncologists specializing in gastrointestinal (GI), breast, gynecologic (GYN), thoracic, and genitourinary (GU) cancers, and three general hematologists and oncologists, with an average of 6.7 years of clinical experience, were divided into two groups and evaluated 78 unique drug repurposing hypotheses presented in the NIH Specific Aims Page format (for specific indication distribution and counts, see below section 4.2).

**中文译文 · 机器初译**

来自同一机构的九位获得认证的血液病学家和肿瘤学家，其中包括六位专注于胃肠道、乳腺、妇科、胸部和泌尿生殖系统癌症领域的肿瘤学家，以及三位普通血液病学家和肿瘤学家，他们的平均临床经验为6.7年。这些专家被分为两组，对NIH特定目标页面格式中列出的78个独特的药物重新应用假设进行了评估（关于具体适应症的分布和数量，请参见第4.2节）。

### co-scientist-0350

**English original**

Two groups of expert raters evaluated the generated Specific Aims based on a modified NIH grant proposal evaluation rubric, consisting of 15 axes focusing on (1) importance of

**中文译文 · 机器初译**

两组专家评估者根据修改后的NIH资助提案评估评分标准对生成的具体目标进行了评估，该评分标准包含15个维度，重点在于（1）重要性


### 原文第 58 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=58)

### co-scientist-0352

**English original**

research (significance and innovation) and (2) approach (rigor and feasibility). The raters indicated their agreement level using a five-point scale: “Strongly Agree”, “Agree”, “Neutral”, “Disagree”, and “Strongly Disagree”. For each axis, we included several questions covering different aspects of the NIH evaluation criteria. The evaluation rubric is further detailed in below 4.3. Specifically, we ask raters to focus on evaluating the clinical relevance and potential for clinical translation, and not for translational capacity or the design of clinical trials.

**中文译文 · 机器初译**

研究（意义与创新）以及（2）方法（严谨性与可行性）。评分者使用五点量表表示同意程度：“强烈同意”、“同意”、“中立”、“不同意”和“强烈不同意”。针对每个维度，我们设置了多个问题以涵盖NIH评估标准的不同方面。评估评分标准详见4.3节。具体而言，我们要求评分者重点评估临床相关性及临床转化潜力，而非转化能力或临床试验设计。

### co-scientist-0353

**English original**

We observed that the rating correlation between two independent group ratings is at a high and reliable degree of agreement with the Spearman’s rho of 0.745 (p < 0.001), and both groups of expert raters consistently assigned high ratings (“Strongly Agree” or “Agree”) to the Specific Aims proposed by Co-Scientist across various evaluation criteria (Supplementary Fig. 7). Of note, the favorable assessments of Co-Scientist-generated hypotheses may be partially attributed to expert pre-screening, wherein a clinician eliminated non-viable candidates prior to expert evaluation. Three examples of generated Specific Aims and their respective expert review ratings are detailed in below section 4.1. Interestingly, Co-Scientist also independently proposed a dihydroorotate dehydrogenase (DHODH)-focused Specific Aim in AML that parallels findings from a recently published T-ALL study 2, despite the referenced work not directly involving AML.

**中文译文 · 机器初译**

我们观察到，两个独立小组的评分之间具有高度且可靠的一致性，与斯皮尔曼 rho 值 0.745（p < 0.001）相符；在多种评估标准下，两组专家评分者均一致对合作科学家提出的具体目标给予高评分（“强烈同意”或“同意”）（补充图 7）。值得注意的是，对合作科学家生成的假设给予积极评价的部分原因可能源于专家预筛选过程，即临床医生在专家评估之前已排除那些不可行的候选方案。第 4.1 节详细介绍了三个生成的具体目标及其相应的专家评审评分示例。
有趣的是，Co-Scientist 还独立提出了针对 AML 中二氢氧代酸脱氢酶（DHODH）的特定研究目标，这一目标与最近发表的 T-ALL 研究 2 的结果相类似，尽管该参考文献并未直接涉及 AML。

### co-scientist-0354

**English original**

The generated Specific Aims were assessed by nine clinical hematologists and oncologists from a single-center, which might bias the interpretation of the evaluation results, as it may introduce institutional perspectives shaped by local practice patterns, clinical experiences, and research frameworks unique to that setting. While some Specific Aims may be supported by preclinical data, it is important to note that none of the proposed drug candidates have undergone randomized phase III clinical trials necessary to establish efficacy and secure regulatory approval for repurposing to a new indication.

**中文译文 · 机器初译**

生成的具体目标由一家医院的九位临床血液病专家和肿瘤专家进行了评估，这可能会影响评估结果的解读，因为这种评估可能受到当地诊疗模式、临床经验以及该特定环境特有的研究框架所影响的机构视角的影响。虽然部分具体目标得到了临床前数据的支持，但需要注意的是，所有拟定的药物候选物都尚未进行必要的随机III期临床试验，以验证其疗效并获得重新用于新适应症的监管批准。


### 原文第 59 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=59)

### co-scientist-0356

**English original**

(a)

**原文保留（专名、技术内容或文献信息） · 保留原文**

(a)

### co-scientist-0357

**English original**

(b)

**原文保留（专名、技术内容或文献信息） · 保留原文**

(b)

### co-scientist-0358

**English original**

Supplementary Fig. 7 | Clinical expert evaluation for Co-Scientist generated drug repurposing hypotheses in the NIH Specific Aims Page format. Two batches of expert hematologists and oncologists independently reviewed the same 78 drug repurposing research proposals, which Co-Scientist had formatted as NIH Specific Aims Pages. The evaluation followed an adapted NIH grant proposal evaluation rubric, detailed in the Supplementary Note 4.3. Overall, two groups of experts judged the Specific Aims proposals from Co-Scientist to be of high quality across all axes of the rubric. (a) and (b) represent two separate groups of expert evaluation results.

**中文译文 · 机器初译**

补充图7 | 临床专家对Co-Scientist生成的药物再利用假设进行了评估，评估结果以NIH具体目标页面格式呈现。两批血液病学家和肿瘤学家分别独立审查了相同的78项药物再利用研究提案，这些提案由Co-Scientist按照NIH具体目标页面格式整理而成。评估过程遵循补充注释4.3中详述的改编后的NIH资助提案评分标准。总体而言，两组专家认为Co-Scientist提出的具体目标提案在评分标准的所有维度上均具有高质量。(a)和(b)分别展示了两组专家评估结果。


### 原文第 60 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=60)

### co-scientist-0360

**English original**

4.1 Examples of Co-Scientist generated Specific Aims with expert evaluation

**中文译文 · 机器初译**

4.1 由联合科学家生成的特定目标示例及专家评估

### co-scientist-0361

**English original**

4.1.1 Example 1: Givosiran for AML

**中文译文 · 机器初译**

4.1.1 示例 1：用于 AML 的 Givosiran

### co-scientist-0362

**English original**

Disease Description Acute myeloid leukemia (AML) is an aggressive hematological malignancy with an incidence rate of approximately 4.3 per 100,000 persons per year in the United States, predominantly affecting older adults. AML arises from a complex interplay of genetic mutations, epigenetic alterations, and dysregulated signaling pathways, disrupting normal hematopoiesis by blocking myeloid differentiation and promoting uncontrolled blast proliferation. This leads to bone marrow failure, infections, bleeding, and other life-threatening complications. The current standard of care includes intensive chemotherapy, often combined with targeted therapies or hematopoietic stem cell transplantation. However, these treatments are often associated with significant toxicity, high relapse rates, and limited efficacy in certain patient populations, particularly in relapsed/refractory or high-risk AML.

**中文译文 · 机器初译**

疾病描述 急性髓系白血病（AML）是一种侵袭性血液系统恶性肿瘤，在美国的年发病率约为每10万人4.3例，主要累及老年人。AML由基因突变、表观遗传改变及异常的信号通路相互作用引起，通过阻断髓系分化并促进不受控制的原始细胞增殖，从而破坏正常的造血功能。这会导致骨髓衰竭、感染、出血以及其他危及生命的并发症。
当前的标准治疗方案包括强化化疗，通常结合靶向治疗或造血干细胞移植。然而，这些治疗方法往往伴随着严重的毒性反应、高复发率，并且在某些患者群体中效果有限，尤其是在复发/难治性或高风险急性髓系白血病患者中。

### co-scientist-0363

**English original**

Unmet Need Despite advancements, significant unmet needs persist in AML treatment. Current therapies often cause severe side effects, particularly in older or frail patients, limiting their tolerability and effectiveness. Relapse rates remain high, and treatment options for relapsed/refractory AML are limited and often less effective. Many patients fail to achieve complete remission or experience only short-lived responses, underscoring the urgent need for novel, less toxic, and more effective therapies, especially for patients with relapsed/refractory or high-risk disease.

**中文译文 · 机器初译**

尽管取得了进展，AML治疗中仍存在大量未满足的需求。当前的治疗方法往往会导致严重的副作用，尤其是对老年或体弱患者而言，这限制了其耐受性和疗效。复发率依然较高，对于复发/难治性AML的治疗选择有限且效果通常较差。许多患者无法达到完全缓解，或仅能获得短暂的反应，这凸显了迫切需要新型、毒性更低、更有效的治疗方法，尤其适用于复发/难治性或高风险疾病患者。

### co-scientist-0364

**English original**

Proposed Solution Givosiran sodium is an RNA interference (RNAi) therapeutic approved for acute hepatic porphyria (AHP). It targets aminolevulinate synthase 1 (ALAS1) mRNA, the rate-limiting enzyme in heme biosynthesis, reducing the production of heme precursors δ-aminolevulinic acid (ALA) and porphobilinogen. This prevents the accumulation of neurotoxic heme intermediates in AHP.

**中文译文 · 机器初译**

提出的解决方案：Givosiran钠是一种用于急性肝卟啉病（AHP）的 RNA 干扰（RNAi）治疗药物。它作用于氨基乙酰丙酸合成酶 1（ALAS1）mRNA，这是血红素生物合成中的限速酶，从而减少δ-氨基乙酰丙酸（ALA）和卟啉原的生成。这样可以避免神经毒性血红素中间体在AHP中积累。

### co-scientist-0365

**English original**

Repurposing givosiran for AML stems from the crucial role of heme biosynthesis in AML pathogenesis. Several studies suggest that disrupting heme biosynthesis offers a therapeutic advantage in AML. The proposed approach addresses the unmet need by targeting AML cells dependent on increased heme biosynthesis, particularly those with MYCN overexpression [1]. Modulating heme levels could influence oxidative stress [5, 6], apoptosis [1, 2], and drug sensitivity in AML [2]. Givosiran’s ALAS1 inhibition aligns with this approach, offering a novel therapeutic strategy.

**中文译文 · 机器初译**

将吉沃西兰用于AML治疗，源于血红素生物合成在AML发病过程中的关键作用。多项研究表明，破坏血红素生物合成可在AML治疗中发挥优势。该疗法通过针对依赖增强血红素生物合成的AML细胞进行干预，特别是那些存在MYCN过表达的细胞[1]，从而满足这一未被满足的需求。调节血红素水平可影响氧化应激[5, 6]、凋亡[1, 2]以及AML对药物的敏感性[2]。吉沃西兰对ALAS1的抑制作用与这种治疗策略相契合，提供了一种新的治疗策略。

### co-scientist-0366

**English original**

We hypothesize that givosiran, by inhibiting ALAS1 and reducing heme biosynthesis, will suppress AML cell growth and survival, particularly in those with upregulated heme biosynthesis. This is supported by preclinical evidence demonstrating that altering heme levels

**中文译文 · 机器初译**

我们假设，Givosiran通过抑制 ALAS1 并减少血红素生物合成，能够抑制 AML 细胞的生长与存活，尤其是在血红素生物合成增强的病例中。这一假设得到了临床前研究的支持，这些研究表明改变血红素水平可以产生相应的效果


### 原文第 61 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=61)

### co-scientist-0368

**English original**

impacts AML cell proliferation, apoptosis, and drug sensitivity [2]. Abstract [1] suggests that elevated heme biosynthesis in MYCN-driven AML is a therapeutic vulnerability. Reducing ALA and porphobilinogen accumulation via givosiran can mitigate oxidative stress [6], a factor implicated in AML progression.

**中文译文 · 机器初译**

影响AML细胞的增殖、凋亡及药物敏感性[2]。摘要[1]指出，由MYCN驱动的AML中血红素生物合成水平升高是一种治疗性弱点。通过givosiran减少ALA和卟啉原的积累，可以减轻氧化应激[6]，而氧化应激是导致AML进展的因素之一。

### co-scientist-0369

**English original**

Overall, our goal is to evaluate the efficacy and safety of givosiran as a novel therapeutic strategy for AML by exploiting the crucial role of heme biosynthesis in its pathogenesis and the drug’s ability to modulate heme levels and downstream effects on AML cell proliferation, survival, and drug sensitivity.

**中文译文 · 机器初译**

总体而言，我们的目标是通过利用血红素生物合成在其发病机制中的关键作用，以及该药物调节血红素水平及其对AML细胞增殖、存活和药物敏感性下游影响的能力，来评估 givosiran作为AML新型治疗策略的疗效与安全性。

### co-scientist-0370

**English original**

Specific Aims 1 Overarching goal: Determine the anti-leukemic activity of givosiran in MYCN-driven AML models. Hypothesis: Givosiran treatment will decrease the viability and proliferation of MYCN-overexpressing AML cells in vitro and reduce tumor growth in MYCN-driven AML xenograft mouse models. Reasoning: MYCN-driven AML frequently exhibits upregulated heme biosynthesis [1], creating a potential dependency on this pathway. Givosiran, by inhibiting ALAS1, could disrupt this dependency, leading to decreased heme and growth inhibition. This is supported by preclinical data showing that inhibiting heme biosynthesis impacts AML cell growth and survival [1, 2].

**中文译文 · 机器初译**

具体目标 1 总体目标：确定Givosiran在由MYCN驱动的急性髓系白血病模型中的抗白血病活性。假设：Givosiran治疗将在体外降低过度表达MYCN的急性髓系白血病细胞的存活率和增殖能力，并减少由MYCN驱动的急性髓系白血病异种移植小鼠模型中的肿瘤生长。推理依据：由MYCN驱动的急性髓系白血病通常表现出血红素生物合成上调现象[1]，这导致该通路具有潜在依赖性。通过抑制ALAS1，Givosiran可以破坏这种依赖性，从而减少血红素生成并抑制细胞生长。临床前数据也支持这一结论，表明抑制血红素生物合成会影响急性髓系白血病细胞的生长和存活[1, 2]。

### co-scientist-0371

**English original**

Specific Aims 2 Overarching goal: Elucidate the impact of givosiran on oxidative stress and drug sensitivity in AML. Hypothesis: Givosiran treatment will modulate oxidative stress levels and enhance the cytotoxic effects of standard AML chemotherapeutics (e.g., cytarabine) in AML cell lines and primary patient samples. Reasoning: Heme plays a role in oxidative stress regulation, and its modulation by givosiran could influence AML cell chemosensitivity. Abstracts [5, 6] highlight oxidative stress in AML and the potential for ALA accumulation to contribute to it. By reducing ALA and heme, givosiran could alter reactive oxygen species (ROS) levels and potentially sensitize AML cells to chemotherapy-induced death.

**中文译文 · 机器初译**

具体目标 2 总体目标：阐明 Givosiran 对急性髓系白血病中氧化应激及药物敏感性的影响。假设：Givosiran 治疗能够调节氧化应激水平，并增强标准急性髓系白血病化疗药物（如阿糖胞苷）在白血病细胞系和患者样本中的细胞毒性作用。推理：血红素在氧化应激调节中起着重要作用，而 Givosiran 对血红素的调控可能影响白血病细胞的药物敏感性。摘要 [5, 6] 强调了急性髓系白血病中的氧化应激，以及 ALA 积累可能对此产生贡献。
通过减少 ALA 和血红素， givosiran 能够改变活性氧（ROS）水平，从而可能使 AML 细胞对化疗引起的死亡产生敏感性。

### co-scientist-0372

**English original**

Specific Aims 3 Overarching goal: Characterize the safety and tolerability of givosiran in preclinical AML models, focusing on its impact on liver function. Hypothesis: Givosiran treatment will be well-tolerated in AML mouse models, with minimal adverse effects on liver function and drug metabolism, at doses that effectively inhibit ALAS1 and reduce heme biosynthesis. Reasoning: Given givosiran’s hepatic target (ALAS1), evaluating its safety profile in AML is crucial. Abstracts [7, 8] highlight the clinical significance of liver function in AML patients. This

**中文译文 · 机器初译**

具体目标 3 总体目标：在临床前AML模型中评估Givosiran的安全性及耐受性，重点关注其对肝脏功能的影响。假设：在能够有效抑制ALAS1并减少血红素生物合成的剂量下，Givosiran治疗在AML小鼠模型中具有良好的耐受性，对肝脏功能和药物代谢的不良影响极小。推理依据：鉴于Givosiran的肝脏靶标为ALAS1，在AML中评估其安全性至关重要。摘要[7, 8]强调了肝脏功能在AML患者中的临床意义。


### 原文第 62 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=62)

### co-scientist-0374

**English original**

aim will assess potential hepatotoxicity and drug-drug interactions, ensuring safe translation to clinical trials. We will evaluate relevant liver function markers and givosiran’s impact on standard AML chemotherapeutic metabolism.

**中文译文 · 机器初译**

评估目标将用于检测潜在的肝毒性和药物相互作用，以确保安全推进临床试验。我们将对相关的肝功能指标以及 givosiran 对标准AML化疗代谢的影响进行分析。

### co-scientist-0375

**English original**

Pilot Evaluation A pilot study in a human AML xenograft mouse model will assess givosiran’s in vivo efficacy and safety. Givosiran will be administered at various doses, monitoring tumor growth, survival, and liver function. The primary endpoint will be tumor growth inhibition. Secondary endpoints include survival, changes in heme levels, oxidative stress markers, and liver function tests. Existing safety data from givosiran’s use in AHP will inform dose selection and monitoring. While givosiran is approved for AHP, its use in AML requires an Investigational New Drug (IND) application to the FDA before clinical trials. Existing safety data might facilitate a streamlined review process.

**中文译文 · 机器初译**

试点评估：在人类急性髓系白血病异种移植小鼠模型中进行的试点研究将评估Givosiran的体内疗效与安全性。将以不同剂量给予Givosiran，并监测肿瘤生长、存活率和肝功能。主要终点为肿瘤生长的抑制情况，次要终点包括存活率、血红素水平变化、氧化应激标志物及肝功能检测。关于Givosiran在AHP中的现有安全数据将用于指导剂量选择与监测。虽然Givosiran已获准用于AHP，但在进行临床试验之前，其在急性髓系白血病中的使用仍需向FDA提交试验性新药物申请。现有的安全数据可能有助于简化审查流程。

### co-scientist-0376

**English original**

Articles [1] Upregulated heme biosynthesis, an exploitable vulnerability in MYCN-driven leukemogenesis Summary: This study demonstrates increased heme biosynthesis in MYCN-driven leukemias, suggesting it as a therapeutic target. Relevance: Supports the rationale for targeting heme biosynthesis in MYCN-driven AML and provides a rationale for the proposed mechanism of action of givosiran in this context. [2] Systematic Dissection of the Metabolic-Apoptotic Interface in AML Reveals Heme Biosynthesis to Be a Regulator of Drug Sensitivity Summary: This study highlights the role of heme biosynthesis in regulating apoptosis and drug sensitivity in AML. Relevance: Supports the potential for givosiran to impact AML cell survival and treatment response by modulating heme biosynthesis. ... [8] Acute myeloid leukemia with hepatic infiltration presenting as obstructive jaundice Summary: This abstract shows liver dysfunction in AML and the need to consider liver health in treatment. Relevance: Reinforces the importance of monitoring liver function in AML patients treated with givosiran, further supporting the rationale for Aim 3.

**中文译文 · 机器初译**

文章 [1] 调节血红素生物合成——MYCN驱动的白血病发生中的可利用漏洞 摘要：本研究表明MYCN驱动的白血病中血红素生物合成增加，提示其可作为治疗靶点。相关性：支持针对MYCN驱动的急性髓系白血病中血红素生物合成进行干预的合理性，并为givosiran在此情境下的作用机制提供了依据。[2] 系统解析急性髓系白血病中代谢与凋亡界面，揭示血红素生物合成是药物敏感性的调节因子 摘要：本研究强调了血红素生物合成在调节急性髓系白血病中的凋亡及药物敏感性方面的作用。
相关性：表明 Givosiran 通过调节血红素生物合成，可能影响 AML 细胞的存活及治疗反应。[8] 表现为梗阻性黄疸的急性髓系白血病 摘要：该摘要指出 AML 患者存在肝脏功能异常，因此在治疗中需考虑肝脏健康。相关性：进一步强调了在接受 Givosiran 治疗的 AML 患者中监测肝功能的重要性，从而进一步支持目标 3 的合理性。


### 原文第 63 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=63)

### co-scientist-0378

**English original**

4.1.2 Example 2: Selinexor monotherapy for colon cancer

**中文译文 · 机器初译**

4.1.2 示例 2：结肠癌的赛利诺索尔单药治疗

### co-scientist-0379

**English original**

Disease Description Colon adenocarcinoma (COAD) is a significant public health concern, with an estimated incidence rate of over 1.9 million new cases and 935,000 deaths globally in 2020. COAD arises from the epithelial lining of the colon and is driven by a complex interplay of genetic mutations (e.g., APC, KRAS, BRAF, TP53) and epigenetic alterations, leading to uncontrolled cell proliferation, impaired apoptosis, and chronic inflammation. These molecular changes disrupt crucial cellular pathways like Wnt/β-catenin signaling, cell cycle control, and DNA damage repair, ultimately driving tumor progression. COAD typically progresses through stages, from localized polyps to invasive tumors with potential for metastasis. Current standard of care involves surgery, chemotherapy, radiation therapy, and targeted therapies, but treatment resistance and recurrence remain major challenges, highlighting the need for new therapeutic approaches.

**中文译文 · 机器初译**

疾病描述 结肠腺癌（COAD）是一个重要的公共卫生问题，2020年全球估计新发病例超过190万例，死亡人数达935,000人。COAD起源于结肠上皮层，由多种基因突变（如APC、KRAS、BRAF、TP53）和表观遗传改变相互作用导致，进而引发细胞无限制增殖、凋亡障碍及慢性炎症。这些分子变化会破坏Wnt/β-连环蛋白信号传导、细胞周期调控和DNA损伤修复等关键细胞通路，最终推动肿瘤进展。
COAD通常经历多个阶段，从局部息肉发展到具有转移可能性的侵袭性肿瘤。当前的标准治疗包括手术、化疗、放疗和靶向治疗，但治疗耐药性和复发仍然是主要挑战，这凸显了需要新的治疗方法的必要性。

### co-scientist-0380

**English original**

Unmet Need Current COAD treatments have limitations, including acquired resistance to chemotherapy, significant toxicities, and incomplete responses in advanced disease. Patients often experience diminished quality of life due to treatment side effects and disease burden. High recurrence rates and limited effective treatment options after progression contribute to poor long-term outcomes. This unmet need underscores the urgency for novel therapeutic strategies that can overcome resistance, improve response rates, and minimize toxicity, ultimately extending survival and enhancing quality of life for COAD patients.

**中文译文 · 机器初译**

未满足的需求：目前的 COAD 治疗方法存在局限性，包括对化疗的获得性耐药性、严重的毒性反应以及晚期疾病中不完全的疗效。患者往往因治疗副作用和疾病负担而生活质量下降。高复发率及进展后有限的有效治疗选择，导致长期预后不佳。这一未满足需求凸显了开发新型治疗策略的紧迫性，这些策略能够克服耐药性、提高疗效并降低毒性，从而延长患者的生存时间并提升其生活质量。

### co-scientist-0381

**English original**

Proposed Solution Selinexor, a first-in-class selective inhibitor of nuclear export (SINE), is currently approved for the treatment of multiple myeloma and diffuse large B-cell lymphoma. It specifically targets XPO1 (Exportin 1), a key protein responsible for the nuclear export of tumor suppressor proteins, oncoproteins, and RNA. By binding to XPO1, Selinexor blocks the nuclear export of these molecules, leading to their accumulation in the nucleus and restoration of tumor suppressor function, cell cycle arrest, and apoptosis induction.

**中文译文 · 机器初译**

提出的解决方案：Selinexor是一种首创的核输出选择性抑制剂（SINE），目前已被批准用于多发性骨髓瘤和弥漫性大B细胞淋巴瘤的治疗。它专门针对XPO1（Exportin 1），这是一种负责肿瘤抑制蛋白、致癌蛋白及RNA核输出的关键蛋白质。通过与XPO1结合，Selinexor能够阻止这些分子向细胞核的输出，导致它们在细胞核中积累，从而恢复肿瘤抑制功能、细胞周期停滞以及诱导细胞凋亡。

### co-scientist-0382

**English original**

Repurposing Selinexor for COAD is rationally supported by its mechanism of action and the molecular characteristics of the disease. Overexpression of XPO1 is common in various cancers, including COAD [1, 2, 6]. Selinexor inhibits XPO1, preventing the nuclear export and restoring the function of key tumor suppressors (p53, RB, FOXO, APC) frequently dysregulated in COAD [2, 3, 4, 5]. Furthermore, Selinexor can suppress constitutively activated NF-κB signaling, a driver of chronic inflammation and tumor progression in COAD, by blocking IκB export and increasing its nuclear accumulation [7, 8]. These mechanisms align with key aspects of COAD pathogenesis and offer opportunities for therapeutic intervention.

**中文译文 · 机器初译**

将塞利诺索用于COAD的重新应用，其机制作用及疾病的分子特征提供了合理的依据。XPO1过表达常见于多种癌症中，包括COAD [1, 2, 6]。塞利诺索能够抑制XPO1，从而阻止核外输出并恢复COAD中常出现紊乱的关键肿瘤抑制因子（p53、RB、FOXO、APC）的功能 [2, 3, 4, 5]。此外，塞利诺索还能通过阻断IκB的输出并增加其在细胞核中的积累，抑制持续激活的NF-κB信号通路，而该通路正是COAD中慢性炎症和肿瘤进展的驱动因素 [7, 8]。
这些机制与 COAD 发病机制的关键方面相契合，为治疗干预提供了机会。


### 原文第 64 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=64)

### co-scientist-0384

**English original**

We hypothesize that Selinexor will effectively inhibit COAD cell growth and enhance apoptosis by restoring tumor suppressor function and modulating crucial signaling pathways. Selinexor has shown anti-tumor activity in solid tumors in a Phase I trial [3], with observations of nuclear accumulation of tumor suppressor proteins [3, 6]. While not specific to COAD, these findings, coupled with evidence of Selinexor’s efficacy in other cancers driven by XPO1 overexpression [3, 6], suggest that a similar mechanism could be effective in COAD. Further supporting our hypothesis, XPO1 overexpression has been linked to NF-κB activation and increased proliferation in COAD [7]. Overall, our goal is: to demonstrate that Selinexor’s XPO1 inhibitory activity can effectively target key oncogenic drivers and restore tumor suppressor functions in COAD, ultimately leading to tumor growth inhibition and improved patient outcomes.

**中文译文 · 机器初译**

我们假设塞利内索能够通过恢复肿瘤抑制功能并调节关键信号通路，有效抑制 COAD 细胞的生长并促进细胞凋亡。在一项 I 期试验中，塞利内索在实体瘤中表现出抗肿瘤活性[3]，且观察到肿瘤抑制蛋白在细胞核中聚集[3, 6]。虽然这些发现并非专门针对 COAD，但结合塞利内索在由 XPO1 过表达引起的其他癌症中具有疗效的证据[3, 6]，表明类似的机制也可能在 COAD 中发挥作用。进一步支持我们的假设的是，XPO1 过表达与 COAD 中的 NF-κB 激活及细胞增殖增加有关[7]。
总体而言，我们的目标在于证明：Selinexor 的 XPO1 抑制活性能够有效针对关键的致癌驱动因素，并恢复肿瘤抑制功能，从而最终抑制肿瘤生长并改善患者预后。

### co-scientist-0385

**English original**

Specific Aims 1 Overarching goal: Determine the in vitro efficacy of Selinexor in inhibiting COAD cell growth and inducing apoptosis. Hypothesis: Selinexor treatment will significantly reduce the viability and increase apoptosis in a panel of COAD cell lines, including those with varying genetic backgrounds (e.g., APC, KRAS, TP53 mutations). Reasoning: Selinexor’s inhibition of XPO1 leads to nuclear accumulation of tumor suppressors like p53, a key regulator of apoptosis [2, 6]. Restoration of p53 function and suppression of NF-κB, a pro-survival pathway [7, 8], are expected to induce apoptosis in COAD cells. We will evaluate this hypothesis using cell viability and apoptosis assays in diverse COAD cell lines to assess the impact of genetic background on Selinexor’s efficacy.

**中文译文 · 机器初译**

具体目标 1 总体目标：确定塞来昔布在体外抑制 COAD 细胞生长并诱导凋亡的效果。假设：塞来昔布治疗可显著降低多种 COAD 细胞系的存活率并增加凋亡率，包括具有不同遗传背景的细胞系（如 APC、KRAS、TP53 突变细胞）。推理：塞来昔布对 XPO1 的抑制导致 p53 等肿瘤抑制因子在细胞核中积累，而 p53 是凋亡的关键调节因子[2, 6]。恢复 p53 功能并抑制促生存通路 NF-κB[7, 8]，有望诱导 COAD 细胞的凋亡。
我们将使用细胞存活率和凋亡检测实验，在多种 COAD 细胞系中评估这一假设，以了解遗传背景对塞利诺司疗效的影响。

### co-scientist-0386

**English original**

Specific Aims 2 Overarching goal: Elucidate the mechanisms by which Selinexor inhibits COAD cell growth, focusing on XPO1-mediated restoration of tumor suppressor function. Hypothesis: Selinexor treatment will increase nuclear accumulation of p53, RB, and FOXO proteins and decrease nuclear export of IκB, leading to cell cycle arrest and decreased NF-κB activity in COAD cells. Reasoning: Selinexor blocks XPO1, preventing nuclear export of key tumor suppressors (p53, RB, FOXO) [2, 4, 5] and the NF-κB inhibitor IκB [7, 8]. Increased nuclear localization of these proteins should restore their growth regulatory functions, leading to cell cycle arrest and reduced NF-κB-driven proliferation. We will evaluate this hypothesis using immunofluorescence and western blotting to assess protein localization and activity.

**中文译文 · 机器初译**

具体目标 2 总体目标：阐明塞利尼索如何抑制 COAD 细胞的生长，重点研究 XPO1 介导的肿瘤抑制功能恢复机制。假设：塞利尼索治疗将增加 p53、RB 和 FOXO 蛋白在细胞核中的积累，并减少 IκB 的核外排，从而导致 COAD 细胞周期停滞及 NF-κB 活性降低。推理：塞利尼索阻断 XPO1 的功能，防止关键肿瘤抑制因子（p53、RB、FOXO）[2, 4, 5] 以及 NF-κB 抑制剂 IκB [7, 8] 的核外排。这些蛋白质在细胞核中的增加应能够恢复其生长调控功能，进而导致细胞周期停滞和 NF-κB 驱动的增殖减少。
我们将利用免疫荧光和Western印迹技术来评估这一假设，以判断蛋白质的位置及活性。

### co-scientist-0387

**English original**

Specific Aims 3 Overarching goal: Characterize the potential synergistic effects of Selinexor in combination with standard-of-care chemotherapies for COAD.

**中文译文 · 机器初译**

具体目标 3 总体目标：研究赛利诺索与标准治疗化疗方案联合使用在 COAD 疾病中的潜在协同作用。


### 原文第 65 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=65)

### co-scientist-0389

**English original**

Hypothesis: Combination treatment with Selinexor and 5-fluorouracil (5-FU) will synergistically reduce COAD cell viability compared to either treatment alone. Reasoning: XPO1 inhibition can sensitize cancer cells to chemotherapy [9]. Combining Selinexor with 5-FU, a common COAD chemotherapy, may enhance cellular stress and improve treatment response. We will test this hypothesis using cell viability assays and investigate the underlying mechanisms of synergy.

**中文译文 · 机器初译**

假设：与单独使用 Selinexor 或 5-氟尿嘧啶（5-FU）相比，两者联合治疗能够协同降低 COAD 细胞的存活率。理由：XPO1 的抑制可以使癌细胞对化疗更加敏感[9]。将 Selinexor 与常用的 COAD 化疗药物 5-FU 结合使用，可能加剧细胞应激并提升治疗效果。我们将通过细胞存活率检测来验证这一假设，并研究其协同作用的机制。

### co-scientist-0390

**English original**

Pilot Evaluation A pilot study will evaluate Selinexor’s efficacy in a patient-derived xenograft (PDX) model of COAD. The primary objective is to determine the effect of Selinexor on tumor growth. The study will utilize an open-label, single-arm design with escalating Selinexor doses in established COAD PDX models. Inclusion criteria: established COAD PDX models. Exclusion criteria: none. Primary endpoint: tumor volume change. Secondary endpoints: changes in biomarkers (p53, Ki67, NF-κB) within the tumor. Selinexor’s established safety profile in other cancers provides a basis for evaluating its safety in this new indication. Potential for expedited review through existing regulatory pathways will be explored.

**中文译文 · 机器初译**

试点评估：一项试点研究将在 COAD 患者来源异种移植模型中对塞利内索的疗效进行评估。主要目标是确定塞利内索对肿瘤生长的影响。该研究将采用开放标签、单组设计，在已建立的 COAD PDX 模型中逐步增加塞利内索剂量。纳入标准：已建立的 COAD PDX 模型。排除标准：无。主要终点：肿瘤体积变化。次要终点：肿瘤内生物标志物（p53、Ki67、NF-κB）的变化。塞利内索在其他癌症中的稳定安全数据为评估其在这一新适应症下的安全性提供了依据。
将探讨通过现有监管渠道进行快速审查的可能性。

### co-scientist-0391

**English original**

Expert rating 1.​ Strongly Agree (unmet clinical needs) 2.​ Agree (bridges therapeutic gap) 3.​ Strongly Agree (scientifically rigorous rationale) 4.​ Agree (integrates prior studies) 5.​ Agree (avoids over-extrapolation) 6.​ Strongly Agree (clear hypotheses and methods) 7.​ Strongly Agree (clearly stated aims) 8.​ Agree (path to clinical application) 9.​ Agree (well-defined endpoints) 10.​Agree (meaningful pre-clinical experiments) 11.​Agree (translational component) 12.​Strongly Agree (avoids inaccuracies) 13.​Strongly Agree (evidence-based assumptions) 14.​Agree (originality and terminology) 15.​Strongly Agree (clear writing and organization)

**中文译文 · 机器初译**

专家评分 1. 强烈同意（未满足的临床需求） 2. 同意（填补治疗空白） 3. 强烈同意（科学严谨的论证依据） 4. 同意（整合了先前研究） 5. 同意（避免过度外推） 6. 强烈同意（清晰的假设与方法） 7. 强烈同意（明确表述的研究目标） 8. 同意（通往临床应用的路径） 9. 同意（定义明确的终点） 10. 同意（有意义的临床前实验） 11. 同意（转化应用部分） 12. 强烈同意（避免错误） 13. 强烈同意（基于证据的假设） 14. 同意（原创性与术语使用） 15. 强烈同意（清晰的写作与结构）


### 原文第 66 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=66)

### co-scientist-0393

**English original**

4.1.3 Example 3: Lapatinib for colon cancer

**中文译文 · 机器初译**

4.1.3 示例 3：拉帕替尼治疗结肠癌

### co-scientist-0394

**English original**

Disease Description Colon adenocarcinoma (COAD) is a significant public health concern, with an estimated incidence rate of over 150,000 new cases annually in the United States [19]. COAD arises from the epithelial lining of the colon, and its pathogenesis involves a complex interplay of genetic and environmental factors. Key molecular mechanisms include mutations in genes such as APC, KRAS, BRAF, and PIK3CA, as well as dysregulation of signaling pathways like Wnt, RAS/RAF/MEK/ERK, and PI3K/AKT/mTOR [8, 9, 12]. These alterations drive uncontrolled cell proliferation, evade apoptosis [14], promote angiogenesis [15], and ultimately lead to tumor growth, invasion, and metastasis [16]. The disease typically progresses through a series of stages, from localized tumors to regional lymph node involvement and distant metastasis. Current standard of care involves surgery, chemotherapy, and targeted therapies such as anti-EGFR antibodies. However, these treatments have limitations, including acquired resistance and significant toxicity.

**中文译文 · 机器初译**

疾病描述 结肠腺癌（COAD）是一个重要的公共卫生问题，在美国每年的新发病例估计超过150,000例[19]。COAD起源于结肠上皮层，其发病机制涉及遗传因素与环境因素的复杂相互作用。主要的分子机制包括APC、KRAS、BRAF和PIK3CA等基因的突变，以及Wnt、RAS/RAF/MEK/ERK和PI3K/AKT/mTOR等信号通路的不正常调节[8, 9, 12]。这些改变导致细胞无限制增殖、逃避凋亡[14]，促进血管生成[15]，最终引发肿瘤生长、浸润和转移[16]。
该疾病通常会经历一系列阶段，从局部肿瘤发展到区域淋巴结受累及远处转移。当前的标准治疗包括手术、化疗以及抗EGFR抗体等靶向疗法。然而，这些治疗方法存在局限性，例如获得性耐药性和严重的毒性反应。

### co-scientist-0395

**English original**

Unmet Need A major unmet need in COAD treatment is the development of effective therapies for patients who progress on or are refractory to standard treatments, particularly those with resistance to anti-EGFR therapy [2]. Despite available therapies, many patients experience disease recurrence and metastasis, leading to poor outcomes and diminished quality of life. There’s a critical need for new therapeutic options that can overcome resistance mechanisms, improve response rates, and offer better tolerability profiles. Specifically, addressing resistance driven by KRAS mutations [10] and exploring alternative therapeutic targets remains crucial.

**中文译文 · 机器初译**

未满足的需求：在 COAD 治疗中一个重要的未满足需求，就是为那些对标准治疗进展或产生耐药性的患者开发有效的疗法，尤其是那些对抗 EGFR 治疗产生耐药性的患者[2]。尽管已有相关疗法，许多患者仍会出现疾病复发和转移，导致治疗效果不佳且生活质量下降。迫切需要新的治疗选择，以克服耐药机制、提高疗效并改善耐受性。特别是针对由 KRAS 突变引起的耐药性[10]，以及探索其他治疗靶点，仍然至关重要。

### co-scientist-0396

**English original**

Proposed Solution Lapatinib is an orally available small molecule tyrosine kinase inhibitor currently approved for use in combination with capecitabine for the treatment of HER2-positive metastatic breast cancer. It reversibly inhibits the intracellular tyrosine kinase domains of both EGFR (ErbB1) and HER2 (ErbB2), thereby blocking downstream signaling cascades, including RAS/RAF/MEK/ERK and PI3K/AKT/mTOR. This inhibition leads to decreased cell proliferation and increased apoptosis.

**中文译文 · 机器初译**

提出的解决方案：拉帕替尼是一种可口服的小分子酪氨酸激酶抑制剂，目前被批准与卡培他滨联合使用以治疗HER2阳性的转移性乳腺癌。它可可逆地抑制EGFR（ErbB1）和HER2（ErbB2）的细胞内酪氨酸激酶结构域，从而阻断下游信号传导级联反应，包括RAS/RAF/MEK/ERK和PI3K/AKT/mTOR。这种抑制作用会导致细胞增殖减少和凋亡增加。

### co-scientist-0397

**English original**

Repurposing lapatinib for COAD is rationalized by the shared ErbB signaling pathway between breast cancer and a subset of COAD. EGFR is commonly overexpressed in COAD [1], and while HER2 overexpression is less frequent than in breast cancer, it occurs in a clinically relevant subset [3, 17] and is associated with resistance to anti-EGFR therapy [2]. Lapatinib can directly inhibit both EGFR and HER2, potentially disrupting crucial oncogenic signaling [13, 14] including PLCγ [7].

**中文译文 · 机器初译**

将拉帕替尼重新用于COAD疾病的治疗，是基于乳腺癌与部分COAD疾病之间存在相同的ErbB信号通路这一事实。EGFR在COAD中常常过度表达[1]，虽然HER2过度表达比在乳腺癌中少见，但其在某些具有临床意义的病例中仍会出现[3, 17]，并且与抗EGFR治疗的耐药性相关[2]。拉帕替尼能够直接抑制EGFR和HER2，从而可能破坏关键的致癌信号传导机制[13, 14]，包括PLCγ的激活[7]。

### co-scientist-0398

**English original**

We hypothesize that lapatinib can effectively inhibit ErbB signaling in COAD, leading to decreased cell proliferation, increased apoptosis, and suppression of metastasis. Preclinical

**中文译文 · 机器初译**

我们假设拉帕替尼能够有效抑制 COAD 中的 ErbB 信号传导，从而减少细胞增殖、增加细胞凋亡并抑制转移。临床前研究


### 原文第 67 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=67)

### co-scientist-0400

**English original**

studies demonstrate synergistic antitumor activity of lapatinib with HDAC inhibitors in COAD models [6], and lapatinib has also been shown to sensitize COAD cells to TRAIL-induced apoptosis via an off-target mechanism [5]. Studies have also investigated HER2 as a therapeutic target in CRC, especially after failure of anti-EGFR therapy [2, 18]. Although lapatinib as a single agent has shown limited efficacy in unselected CRC populations, this could be attributed to the heterogeneity of COAD and the presence of resistance mechanisms like KRAS mutations. We anticipate that patient stratification based on molecular profiles will identify subgroups that derive greater benefit.

**中文译文 · 机器初译**

研究表明，在 COAD 模型中，拉帕替尼与 HDAC 抑制剂具有协同抗肿瘤作用[6]，且拉帕替尼还能通过非靶标机制使 COAD 细胞对 TRAIL 诱导的凋亡更加敏感[5]。此外，研究还探讨了 HER2 作为 CRC 的治疗靶点，尤其是在抗 EGFR 治疗失败后的应用情况[2, 18]。尽管作为单一药物使用的拉帕替尼在未筛选的 CRC 人群中效果有限，这可能归因于 COAD 的异质性以及如 KRAS 突变等耐药机制的存在。我们预计，基于分子特征对患者进行分层分析将能够识别出能获得更大获益的亚组。

### co-scientist-0401

**English original**

Overall, our goal is: to demonstrate the efficacy of lapatinib in specific molecular subtypes of COAD, potentially in combination with other targeted therapies, to address the unmet need for new treatment options, particularly in patients resistant to standard therapies.

**中文译文 · 机器初译**

总体而言，我们的目标在于：证明拉帕替尼在 COAD 的特定分子亚型中的有效性，并可能与其他靶向疗法联合使用，以满足新的治疗需求，尤其是针对对标准疗法产生耐药的患者。

### co-scientist-0402

**English original**

Specific Aims 1 Overarching goal: To determine the efficacy of lapatinib in inhibiting HER2/EGFR signaling and suppressing cell proliferation in a panel of well-characterized COAD cell lines. Hypothesis: Lapatinib will inhibit cell proliferation in HER2-amplified/overexpressing and/or EGFR-overexpressing COAD cell lines. Reasoning: Lapatinib directly inhibits both HER2 and EGFR, key drivers of cell proliferation in a subset of COAD. Inhibition of these receptors should lead to reduced downstream signaling through the RAS/RAF/MEK/ERK and PI3K/AKT/mTOR pathways, ultimately suppressing cell growth [6].

**中文译文 · 机器初译**

具体目标 1 总体目标：在一系列具有明确特性的 COAD 细胞系中，确定拉帕替尼在抑制 HER2/EGFR 信号传导和抑制细胞增殖方面的效果。假设：拉帕替尼能够抑制 HER2 扩增/过表达和/或 EGFR 过表达的 COAD 细胞系的细胞增殖。推理：拉帕替尼直接抑制 HER2 和 EGFR，而这两种受体是部分 COAD 细胞中导致细胞增殖的关键因素。抑制这些受体应会导致 RAS/RAF/MEK/ERK 和 PI3K/AKT/mTOR 通路中的下游信号传导减弱，最终抑制细胞生长 [6]。

### co-scientist-0403

**English original**

Specific Aims 2 Overarching goal: To elucidate the impact of lapatinib on apoptosis and key signaling pathways in COAD models. Hypothesis: Lapatinib will induce apoptosis and modulate key signaling pathways (RAS/RAF/MEK/ERK, PI3K/AKT/mTOR, and PLCγ) in COAD cell lines, especially those with HER2/EGFR alterations. Reasoning: Inhibition of HER2/EGFR by lapatinib disrupts pro-survival signaling, potentially promoting apoptosis [14]. Additionally, lapatinib can indirectly modulate downstream pathways [4, 7], even demonstrating synergistic effects with other agents [6]. This aim will explore the extent of this modulation in various COAD subtypes.

**中文译文 · 机器初译**

具体目标 2 总体目标：阐明拉帕替尼对 COAD 模型中细胞凋亡及关键信号通路的影响。假设：拉帕替尼会在 COAD 细胞系中引发细胞凋亡，并调节关键信号通路（RAS/RAF/MEK/ERK、PI3K/AKT/mTOR 和 PLCγ），尤其是那些存在 HER2/EGFR 突变的细胞。推理：拉帕替尼对 HER2/EGFR 的抑制会破坏促进存活的信号传导，从而可能促进细胞凋亡 [14]。此外，拉帕替尼还可以间接调节下游通路 [4, 7]，甚至与其他药物产生协同作用 [6]。该目标将研究这种调节在不同 COAD 亚型中的程度。

### co-scientist-0404

**English original**

Specific Aims 3 Overarching goal: To identify predictive biomarkers for lapatinib response and explore potential combination strategies in COAD. Hypothesis: A combination of lapatinib with a MEK inhibitor will enhance antitumor activity in KRAS-mutant COAD cell lines compared to lapatinib alone.

**中文译文 · 机器初译**

具体目标 3 总体目标：确定拉帕替尼疗效的预测性生物标志物，并探索在 COAD 中的潜在联合治疗策略。假设：与单独使用拉帕替尼相比，将拉帕替尼与 MEK 抑制剂联合使用可增强 KRAS 突变型 COAD 细胞系的抗肿瘤活性。


### 原文第 68 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=68)

### co-scientist-0406

**English original**

Reasoning: KRAS mutations are a known mechanism of resistance to EGFR/HER2 targeted therapies [10]. Combining lapatinib with a MEK inhibitor may overcome this resistance by blocking the downstream MAPK pathway activation, leading to enhanced antitumor efficacy.

**中文译文 · 机器初译**

推理：KRAS突变是EGFR/HER2靶向治疗的已知耐药机制[10]。将拉帕替尼与MEK抑制剂联合使用，可通过阻断下游MAPK通路激活来克服这种耐药性，从而提升抗肿瘤疗效。

### co-scientist-0407

**English original**

Pilot Evaluation A pilot study will be conducted to evaluate the safety and preliminary efficacy of lapatinib in patients with HER2-positive metastatic COAD who have progressed on standard therapy. This open-label, single-arm study will enroll 15-20 patients with confirmed HER2 overexpression/amplification and KRAS wild-type status. Key exclusion criteria will include prior treatment with lapatinib and significant comorbidities. The primary endpoint will be progression-free survival, and secondary endpoints will include overall response rate, duration of response, and safety. Lapatinib’s known safety profile from its use in breast cancer will inform the monitoring plan. Expedited regulatory review may be possible due to lapatinib’s existing approval.

**中文译文 · 机器初译**

试点评估：将开展一项试点研究，以评估拉帕替尼在接受标准治疗后出现进展的HER2阳性转移性COAD患者中的安全性及初步疗效。这项开放标签、单组研究将招募15-20名经证实存在HER2过表达/扩增且KRAS为野生型的患者。主要排除标准包括曾使用过拉帕替尼治疗以及存在严重的合并症。主要终点为无进展生存期，次要终点包括总缓解率、缓解持续时间及安全性。拉帕替尼在乳腺癌治疗中的已知安全特征将用于指导监测计划。
由于拉帕替尼已获得批准，可能能够加快监管审查流程。

### co-scientist-0408

**English original**

Articles [1] Targeting the EGFR signalling pathway in metastatic colorectal cancer Summary: Details the importance of EGFR signaling in CRC and how targeting it is a crucial therapeutic strategy. Relevance: Provides context for lapatinib’s action as it targets EGFR. [2] HER2 as an Emerging Oncotarget for Colorectal Cancer Treatment After Failure of Anti-Epidermal Growth Factor Receptor Therapy Summary: Discusses HER2 as a target in CRC, especially in the context of anti-EGFR therapy resistance. Relevance: Directly relevant to lapatinib’s mechanism and potential in COAD. ... [19] United States Cancer Statistics Summary: Provides official U.S. cancer incidence and mortality statistics. Relevance: Source of epidemiological data for colon adenocarcinoma.

**中文译文 · 机器初译**

文章 [1] 针对转移性结直肠癌中 EGFR信号通路的研究 摘要：详细阐述了EGFR信号在CRC中的重要性以及靶向该通路为何是一种关键的治疗策略。相关性：为拉帕替尼通过靶向EGFR发挥作用提供了背景说明。 [2] 抗表皮生长因子受体治疗失败后，HER2作为结直肠癌治疗的新靶点 摘要：讨论了HER2在CRC中的靶点地位，特别是在抗EGFR治疗耐药的背景下。相关性：直接涉及拉帕替尼的作用机制及其在COAD中的应用潜力。... [19] 美国癌症统计摘要：提供美国的官方癌症发病率和死亡率统计数据。
相关性：结肠腺癌流行病学数据的来源。

### co-scientist-0409

**English original**

Expert rating 1.​ Strongly Agree (unmet clinical needs) 2.​ Agree (bridges therapeutic gap) 3.​ Strongly Agree (scientifically rigorous rationale) 4.​ Strongly Agree (integrates prior studies) 5.​ Strongly Agree (avoids over-extrapolation) 6.​ Strongly Agree (clear hypotheses and methods) 7.​ Strongly Agree (clearly stated aims) 8.​ Strongly Agree (path to clinical application)

**中文译文 · 机器初译**

专家评分 1. 强烈同意（未满足的临床需求） 2. 同意（填补治疗空白） 3. 强烈同意（科学严谨的论证依据） 4. 强烈同意（整合了先前研究） 5. 强烈同意（避免过度外推） 6. 强烈同意（清晰的假设与方法） 7. 强烈同意（明确表述的目标） 8. 强烈同意（通往临床应用的路径）


### 原文第 69 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=69)

### co-scientist-0411

**English original**

9.​ Agree (well-defined endpoints) 10.​Neutral (meaningful pre-clinical experiments) 11.​Strongly Agree (translational component) 12.​Strongly Agree (avoids inaccuracies) 13.​Strongly Agree (evidence-based assumptions) 14.​Strongly Agree (originality and terminology) 15.​Agree (clear writing and organization)

**中文译文 · 机器初译**

9. 同意（定义明确的终点） 10. 中立（有意义的临床前实验） 11. 强烈同意（转化应用部分） 12. 强烈同意（避免错误） 13. 强烈同意（基于证据的假设） 14. 强烈同意（原创性和术语使用） 15. 同意（清晰的写作与结构）

### co-scientist-0412

**English original**

Of note, the aforementioned examples were generated by Co-Scientist without being restricted to a predefined subset of literature and were not filtered for the presence of preclinical evidence or prior evaluation in multi-drug regimens.

**中文译文 · 机器初译**

值得注意的是，上述示例是由 Co-Scientist 生成的，并未局限于预定义的文献子集，也没有筛选排除临床前证据或多种药物治疗方案下的先前评估内容。


### 原文第 70 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=70)

### co-scientist-0414

**English original**

4.2 Specific Aims count distribution

**中文译文 · 机器初译**

4.2 具体目标计数分布

### co-scientist-0415

**English original**

Supplementary Table 2 | Count distribution of the cancer types in the Specific Aims drug repurposing proposals generated by Co-Scientist.

**中文译文 · 机器初译**

补充表2 | 由联合科学家提出的特定目标药物再利用提案中各类癌症类型的数量分布。

### co-scientist-0416

**English original**

Repurposed Cancer Count
Acute Myeloid Leukemia (LAML) 13
Colon adenocarcinoma (COAD) 10
Breast invasive carcinoma (BRCA) 10
Skin Cutaneous Melanoma (SKCM) 8
Lung adenocarcinoma (LUAD) 6
Head and Neck squamous cell carcinoma (HNSC) 5
Bladder Urothelial Carcinoma (BLCA) 5
Pancreatic adenocarcinoma (PAAD) 4
Stomach adenocarcinoma (STAD) 3
Rectum adenocarcinoma (READ) 3
Esophageal carcinoma (ESCA) 3
Uveal Melanoma (UVM) 2
Uterine Corpus Endometrial Carcinoma (UCEC) 2
Prostate adenocarcinoma (PRAD) 2
Lung squamous cell carcinoma (LUSC) 1
Cervical squamous cell carcinoma and
endocervical adenocarcinoma (CESC) 1
Grand Total 78

**中文译文 · 机器初译**

Repurposed Cancer Count
Acute Myeloid Leukemia (LAML) 13
Colon adenocarcinoma (COAD) 10
Breast invasive carcinoma (BRCA) 10
Skin Cutaneous Melanoma (SKCM) 8
Lung adenocarcinoma (LUAD) 6
Head and Neck squamous cell carcinoma (HNSC) 5
Bladder Urothelial Carcinoma (BLCA) 5
Pancreatic adenocarcinoma (PAAD) 4
Stomach adenocarcinoma (STAD) 3
Rectum adenocarcinoma (READ) 3
Esophageal carcinoma (ESCA) 3
Uveal Melanoma (UVM) 2
Uterine Corpus Endometrial Carcinoma (UCEC) 2
Prostate adenocarcinoma (PRAD) 2
Lung squamous cell carcinoma (LUSC) 1
Cervical squamous cell carcinoma and
endocervical adenocarcinoma (CESC) 1
Grand Total 78

表内文字对照（数值与原始行列保持不变）：
Repurposed Cancer Count → 重新使用的癌症计数
Acute Myeloid Leukemia (LAML) → 急性髓系白血病（LAML）
Colon adenocarcinoma (COAD) → 结肠腺癌（COAD）
Breast invasive carcinoma (BRCA) → 乳腺浸润性癌（BRCA）
Skin Cutaneous Melanoma (SKCM) → 皮肤皮肤黑色素瘤（SKCM）
Lung adenocarcinoma (LUAD) → 肺腺癌（LUAD）
Head and Neck squamous cell carcinoma (HNSC) → 头颈部鳞状细胞癌（HNSC）
Bladder Urothelial Carcinoma (BLCA) → 膀胱尿路上皮癌（BLCA）
Pancreatic adenocarcinoma (PAAD) → 胰腺腺癌（PAAD）
Stomach adenocarcinoma (STAD) → 胃腺癌（STAD）
Rectum adenocarcinoma (READ) → 直肠腺癌（READ）
Esophageal carcinoma (ESCA) → 食管癌（ESCA）
Uveal Melanoma (UVM) → 眼脉络膜黑色素瘤（UVM）
Uterine Corpus Endometrial Carcinoma (UCEC) → 子宫 Corpus 子宫内膜癌（UCEC）
Prostate adenocarcinoma (PRAD) → 前列腺腺癌（PRAD）
Lung squamous cell carcinoma (LUSC) → 肺鳞状细胞癌（LUSC）
Cervical squamous cell carcinoma and → 宫颈鳞状细胞癌
endocervical adenocarcinoma (CESC) → 宫颈内腺癌（CESC）
Grand Total → 总计

### co-scientist-0417

**English original**

4.3 Specific Aims evaluation rubric

**中文译文 · 机器初译**

4.3 具体目标评估评分标准

### co-scientist-0418

**English original**

To rigorously assess Co-Scientist generated repurposing hypotheses, we developed a pilot evaluation framework in collaboration with two oncologists at a US institution. The framework was inspired by established grant review criteria, particularly the NIH Specific Aims evaluation axes, but adapted to address the unique characteristics of AI-generated proposals. Traditional grant review criteria assume that proposals originate from domain experts with deep tacit knowledge and access to recent unpublished findings. However, LLM-based systems operate differently, they synthesize publicly available information but lack the experiential knowledge and awareness of cutting-edge unpublished work that human researchers possess. Therefore, our framework prioritizes assessment of logical consistency, appropriate citation and integration of published scientific literature, and factual accuracy, rather than assuming the depth of expertise expected from human investigators.

**中文译文 · 机器初译**

为了严格评估共科学家生成的重新应用假设，我们与美国某机构的两位肿瘤学家合作，建立了试点评估框架。该框架借鉴了成熟的资助评审标准，尤其是 NIH 具体目标评估维度，但针对人工智能生成提案的独特特点进行了调整。传统的资助评审标准假设提案来自拥有深厚隐性知识且能够获取最新未发表研究结果的领域专家。
然而，基于大语言模型的系统运作方式不同，它们会整合公开可用的信息，但缺乏人类研究人员所拥有的经验性知识以及对前沿未发表研究的了解。因此，我们的框架更注重逻辑一致性、恰当的引用与已发表科学文献的整合，以及事实准确性的评估，而非假设人类研究者应有的专业深度。


### 原文第 71 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=71)

### co-scientist-0420

**English original**

The framework evaluates proposals across two domains totaling 15 criteria. The first domain, clinical significance (5 criteria), assesses whether proposals address genuine unmet clinical needs, demonstrate understanding of the current therapeutic landscape, and provide sound scientific rationale for the repurposing strategy. These criteria evaluate how effectively the AI system identifies clinically relevant problems and synthesizes available evidence to justify therapeutic hypotheses. The second domain, scientific rigor and methodology (10 criteria), evaluates the technical quality of proposals, including clarity of hypothesis formation, appropriateness of proposed experimental approaches, quality of preclinical study design, definition of clinical endpoints, and overall translational potential. This domain pays particular attention to LLM-specific concerns, such as factual accuracy of cited literature and the presence of hallucinated or fabricated content, which are the issues not typically relevant in human-authored proposals.

**中文译文 · 机器初译**

该框架通过两个领域共15项标准对提案进行评估。第一个领域为临床意义（5项标准），用于评估提案是否解决了真实的未满足临床需求，是否了解当前治疗领域的情况，以及是否为重新应用策略提供了合理的科学依据。这些标准旨在衡量人工智能系统识别具有临床意义的问题以及整合现有证据以支持治疗假设的能力。
第二个领域为科学严谨性与方法论（10项标准），用于评估提案的技术质量，包括假设形成的清晰度、所提出的实验方法的适用性、临床前研究设计的质量、临床终点定义以及整体转化潜力。该领域特别关注大语言模型相关的问题，如引用的文献事实准确性以及是否存在幻觉或编造内容，这些问题在人类撰写的提案中通常并不重要。

### co-scientist-0421

**English original**

Each criterion was rated using a 5-point Likert scale (Strongly Disagree, Disagree, Neutral, Agree, Strongly Agree), allowing quantitative assessment across all evaluated proposals. Evaluations were conducted independently by two separate groups of expert hematologist-oncologists to ensure rigorous assessment.

**中文译文 · 机器初译**

每个标准均采用5点Likert量表进行评分（强烈反对、反对、中立、同意、非常同意），以便对所有评估提案进行定量评估。评估工作由两组独立的专家血液肿瘤学家独立开展，以确保评估的严谨性。

### co-scientist-0422

**English original**

We emphasize that this represents a pilot framework developed for initial exploration of AI-generated hypothesis evaluation. It is not intended to replicate the comprehensive depth of full grant review processes, which typically include detailed assessment of statistical power calculations, complex experimental design elements, budget justification, and investigator qualifications. Omitted axes of quality could be addressed in future work, including more granular criteria for experimental design such as power calculation review and specific study design methodologies. If this framework were to be developed into a validated assessment instrument, it would require substantial additional research, including formal evaluation of inter-rater and intra-rater reliability, construct validity, criterion validity, and correlation with established benchmarks. The current framework serves as a starting point for systematically evaluating whether AI-generated biomedical hypotheses meet the standards expected by clinical researchers and could guide future therapeutic investigation. The complete evaluation framework with specific criteria for each domain is presented below.

**中文译文 · 机器初译**

我们强调，这一框架仅用于初步探索人工智能生成的假设评估方法，属于试点性框架。它并不旨在完全复现完整的资助评审流程的全面性，后者通常包含对统计功效计算的详细评估、复杂的实验设计要素、预算合理性论证以及研究者的资质审核等内容。未来的研究中可以补充质量评估的相关维度，例如制定更细致的实验设计标准，如功效计算审查及特定的研究设计方法等。
如果将该框架开发成经过验证的评估工具，就需要进行大量的额外研究，包括对评分者间与评分者内可靠性、构念效度、准则效度以及与现有基准标准的相关性进行正式评估。当前框架可作为系统评估人工智能生成的生物医学假设是否符合临床研究人员期望的标准、并指导未来治疗研究的起点。下面给出了包含各领域具体标准的完整评估框架。

### co-scientist-0423

**English original**

●​ Significance and innovation (5 questions) ○​ The proposal adequately identifies significant unmet clinical needs that could be addressed through drug repurposing of this pharmacological agent. ○​ The proposal effectively bridges an important gap in the current therapeutic landscape for the target disease by repurposing this drug. ○​ The proposal presents a scientifically rigorous rationale for repurposing the drug, grounded in current evidence and literature. ○​ The scientific background integrates relevant prior studies and preliminary data to support the proposed drug repurposing.

**中文译文 · 机器初译**

●​ 重要性与创新性（5个问题） ○​ 该提案准确指出了通过该药物重新应用所能解决的重大未满足临床需求。 ○​ 通过重新应用该药物，该提案有效填补了目标疾病当前治疗领域的重要空白。 ○​ 该提案基于现有证据和文献，提供了科学严谨的重新应用理由。 ○​ 科学背景整合了相关先前研究和初步数据，以支持所提出的药物重新应用方案。


### 原文第 72 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=72)

### co-scientist-0425

**English original**

○​ The proposal avoids over-extrapolation or speculative conclusions beyond the supporting evidence. ●​ Rigor and feasibility (10 questions) ○​ Does each Specific Aim have a clear hypothesis, and specific methodological approaches? ○​ Are the Specific Aims clearly stated and logically organized? ○​ There is a clear path from the proposed research to clinical application, including consideration of necessary pre-clinical and clinical studies. ○​ The proposal includes well-defined and clinically relevant endpoints. ○​ The pre-clinical experiments are designed to yield meaningful insights into the drug's potential efficacy and safety in its new therapeutic role. ○​ The proposal includes a well-described translational component to assess the drug's efficacy in its new indication. ○​ The proposal avoids factual inaccuracies or hallucinations, presenting information that is accurate and reliable. ○​ The assumptions made within the proposal regarding the drug's efficacy, mechanism, and potential outcomes are grounded in current scientific evidence. ○​ The proposal demonstrates originality in thought and approach, employs precise and appropriate scientific terminology and avoids ambiguous or generic statements. ○​ The proposal is clearly written, with well-organized sections and a logical flow of ideas that enhances comprehension and ensures the aims are easily understood.

**中文译文 · 机器初译**

○​ 该提案避免了过度推断或超出支持证据范围的推测性结论。●​ 严谨性与可行性（10个问题）○​ 每个具体目标是否有明确的假设及具体的方法论途径？○​ 具体目标是否表述清晰且逻辑有序？○​ 从研究提案到临床应用的路径明确，包含对必要的临床前和临床研究考虑。○​ 提案包含定义明确且具有临床相关性的终点指标。○​ 临床前实验旨在获得关于药物在新治疗角色下的潜在疗效和安全性的有意义见解。○​ 提案包含...
用于评估该药物新适应症疗效的详细描述的翻译内容。○​ 该提案避免事实错误或幻觉现象，所呈现的信息准确可靠。○​ 提案中关于该药物疗效、作用机制及潜在结果的假设均基于当前科学证据。○​ 该提案在思路与方法上具有创新性，使用精确恰当的科学术语，且避免模糊或通用的表述。○​ 该提案写作清晰，章节结构合理，思路逻辑连贯，有助于理解并确保目标易于把握。


### 原文第 73 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=73)

### co-scientist-0427

**English original**

5 Additional information for drug repurposing evaluation

**中文译文 · 机器初译**

5 用于药物重新应用评估的额外信息

### co-scientist-0428

**English original**

5.1 Co-Scientist suggests plausible drug repurposing candidates as rated by computational biology analyses and experts

**中文译文 · 机器初译**

5.1 联合科学家根据计算生物学分析和专家评估，提出合理的药物重新应用候选方案

### co-scientist-0429

**English original**

We constrained Co-Scientist to explore potential repurposing hypotheses from a curated list of 2300 approved drugs across 34 cancer types. The list, along with their corresponding abbreviations, was constructed based on a curated text string derived from the TCGA project (Supplementary Table 3). This list includes 10 rare cancers.

**中文译文 · 机器初译**

我们限制了共科学家从包含 2300 种已批准药物、覆盖 34 种癌症类型的精选列表中探索潜在的重新应用假设。该列表及其对应的缩写是根据来自 TCGA 项目的精选文本字符串构建的（补充表 3）。该列表中包含 10 种罕见癌症。

### co-scientist-0430

**English original**

Supplementary Table 3 | TCGA cancer type. We consider all cancer types except CNTL,
FPPP, and MISC while exploring the drug repurposing candidates with preclinical evidence.
*Not a cancer type.
Cancer Name Abbreviation Cancer Name
LAML Acute myeloid leukemia
ACC Adrenocortical carcinoma
BLCA Bladder urothelial carcinoma
LGG Brain lower grade glioma
BRCA Breast invasive carcinoma
Cervical squamous cell carcinoma and endocervical
CESC
adenocarcinoma
CHOL Cholangiocarcinoma
LCML Chronic myelogenous leukemia
COAD Colon adenocarcinoma
CNTL* Controls
ESCA Esophageal carcinoma
FPPP* FFPE Pilot Phase II
GBM Glioblastoma multiforme
HNSC Head and neck squamous cell carcinoma
KICH Kidney chromophobe
KIRC Kidney renal clear cell carcinoma
KIRP Kidney renal papillary cell carcinoma
LIHC Liver hepatocellular carcinoma
LUAD Lung adenocarcinoma
LUSC Lung squamous cell carcinoma
DLBC Lymphoid neoplasm diffuse large B-cell lymphoma

**中文译文 · 机器初译**

Supplementary Table 3 | TCGA cancer type. We consider all cancer types except CNTL,
FPPP, and MISC while exploring the drug repurposing candidates with preclinical evidence.
*Not a cancer type.
Cancer Name Abbreviation Cancer Name
LAML Acute myeloid leukemia
ACC Adrenocortical carcinoma
BLCA Bladder urothelial carcinoma
LGG Brain lower grade glioma
BRCA Breast invasive carcinoma
Cervical squamous cell carcinoma and endocervical
CESC
adenocarcinoma
CHOL Cholangiocarcinoma
LCML Chronic myelogenous leukemia
COAD Colon adenocarcinoma
CNTL* Controls
ESCA Esophageal carcinoma
FPPP* FFPE Pilot Phase II
GBM Glioblastoma multiforme
HNSC Head and neck squamous cell carcinoma
KICH Kidney chromophobe
KIRC Kidney renal clear cell carcinoma
KIRP Kidney renal papillary cell carcinoma
LIHC Liver hepatocellular carcinoma
LUAD Lung adenocarcinoma
LUSC Lung squamous cell carcinoma
DLBC Lymphoid neoplasm diffuse large B-cell lymphoma

表内文字对照（数值与原始行列保持不变）：
Supplementary Table → 补充表格
TCGA cancer type → TCGA癌症类型
We consider all cancer types except CNTL → 我们考虑了所有癌症类型，除了 CNTL
FPPP → FPPP
and MISC while exploring the drug repurposing candidates with preclinical evidence → 在利用临床前证据探索药物重新应用候选药物时，还涉及misc MISC
Not a cancer type → 不属于癌症类型
Cancer Name Abbreviation Cancer Name → 癌症名称缩写 癌症名称
LAML Acute myeloid leukemia → LAML 急性髓系白血病
ACC Adrenocortical carcinoma → ACC 肾上腺皮质癌
BLCA Bladder urothelial carcinoma → BLCA 膀胱尿路上皮癌
LGG Brain lower grade glioma → LGG Brain低级别胶质瘤
BRCA Breast invasive carcinoma → BRCA 乳腺癌浸润性癌
Cervical squamous cell carcinoma and endocervical → 宫颈鳞状细胞癌与宫颈癌
CESC → CESC
adenocarcinoma → 腺癌
CHOL Cholangiocarcinoma → CHOL 胆管癌
LCML Chronic myelogenous leukemia → LCML 慢性髓系白血病
COAD Colon adenocarcinoma → COAD 结肠腺癌
CNTL → CNTL
Controls → 控制方式
ESCA Esophageal carcinoma → ESCA 食管癌
FFPE Pilot Phase II → FFPE 试点阶段二
GBM Glioblastoma multiforme → GBM 多形性胶质母细胞瘤
HNSC Head and neck squamous cell carcinoma → 头颈鳞状细胞癌
KICH Kidney chromophobe → KICH 肾嗜色细胞
KIRC Kidney renal clear cell carcinoma → KIRC 肾脏肾透明细胞癌
KIRP Kidney renal papillary cell carcinoma → KIRP 肾肾小囊细胞癌
LIHC Liver hepatocellular carcinoma → LIHC 肝细胞癌
LUAD Lung adenocarcinoma → LUAD 肺腺癌
LUSC Lung squamous cell carcinoma → LUSC 肺鳞状细胞癌
DLBC Lymphoid neoplasm diffuse large B-cell lymphoma → DLBC 淋巴肿瘤 弥漫性大B细胞淋巴瘤


### 原文第 74 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=74)

### co-scientist-0432

**English original**

MESO Mesothelioma
MISC* Miscellaneous
OV Ovarian serous cystadenocarcinoma
PAAD Pancreatic adenocarcinoma
PCPG Pheochromocytoma and paraganglioma
PRAD Prostate adenocarcinoma
READ Rectum adenocarcinoma
SARC Sarcoma
SKCM Skin cutaneous melanoma
STAD Stomach adenocarcinoma
TGCT Testicular germ cell tumors
THYM Thymoma
THCA Thyroid carcinoma
UCS Uterine carcinosarcoma
UCEC Uterine corpus endometrial carcinoma
UVM Uveal melanoma

**中文译文 · 机器初译**

MESO Mesothelioma
MISC* Miscellaneous
OV Ovarian serous cystadenocarcinoma
PAAD Pancreatic adenocarcinoma
PCPG Pheochromocytoma and paraganglioma
PRAD Prostate adenocarcinoma
READ Rectum adenocarcinoma
SARC Sarcoma
SKCM Skin cutaneous melanoma
STAD Stomach adenocarcinoma
TGCT Testicular germ cell tumors
THYM Thymoma
THCA Thyroid carcinoma
UCS Uterine carcinosarcoma
UCEC Uterine corpus endometrial carcinoma
UVM Uveal melanoma

表内文字对照（数值与原始行列保持不变）：
MESO Mesothelioma → MESO 间皮瘤
MISC → 其他杂项
Miscellaneous → 其他杂项
OV Ovarian serous cystadenocarcinoma → OV 卵巢浆膜囊腺癌
PAAD Pancreatic adenocarcinoma → PAAD 胰腺腺癌
PCPG Pheochromocytoma and paraganglioma → PCPG 嗜铬细胞瘤和副神经节瘤
PRAD Prostate adenocarcinoma → PRAD 前列腺腺癌
READ Rectum adenocarcinoma → 阅读直肠腺癌
SARC Sarcoma → SARC 肉瘤
SKCM Skin cutaneous melanoma → SKCM 皮肤黑色素瘤
STAD Stomach adenocarcinoma → STAD 胃腺癌
TGCT Testicular germ cell tumors → TGCT 睾丸生殖细胞肿瘤
THYM Thymoma → THYM 胸腺瘤
THCA Thyroid carcinoma → THCA 甲状腺癌
UCS Uterine carcinosarcoma → UCS 子宫癌肉瘤
UCEC Uterine corpus endometrial carcinoma → UCEC 子宫体子宫内膜癌
UVM Uveal melanoma → UVM 眼眦黑色素瘤

### co-scientist-0433

**English original**

To achieve this, we modified the prompts used in the Generation agent and Ranking agent stages to ensure hypothesis generation in this constrained search space; however, the core Co-Scientist logic remained unchanged. When formulating the research goal for Co-Scientist, we explicitly emphasized the following preferences related to drug repurposing: ●​ Elucidate the known mechanisms of action and impacted biological pathways of the drug. ●​ Identify potential diseases or cancer types that could be treatment targets for the drug. ●​ Explain the potential mechanisms by which the drug could exert therapeutic effects. ●​ Propose alternative mechanisms of action through which the drug might function in the proposed therapeutic context. ●​ Identify the diseases / cancers for which the drug is currently approved. ●​ List the most promising disease / cancer type candidates for repurposing. ●​ Discuss prior research and challenges associated with repurposing the drug.

**中文译文 · 机器初译**

为了实现这一目标，我们修改了生成智能体和排序智能体阶段中使用的提示词，以确保在这一受限搜索空间中进行假设生成；不过，核心 Co-Scientist 逻辑保持不变。
在制定 Co-Scientist 的研究目标时，我们明确强调了与药物重新应用相关的以下偏好：● 阐明该药物的已知作用机制及受影响的生物途径。● 识别该药物可能作为治疗靶点的潜在疾病或癌症类型。● 解释该药物可能发挥治疗效果的潜在机制。● 提出该药物在所设想的治疗环境中可能发挥的替代作用机制。● 识别该药物目前已获批治疗的疾病/癌症类型。● 列出最具有潜力的可重新应用的疾病/癌症类型候选对象。● 讨论以往的相关研究。
以及重新利用该药物所涉及的挑战。

### co-scientist-0434

**English original**

We used Co-Scientist to generate drug repurposing proposals for 34 different cancer types from a subset of 2300 drugs curated with the Open Targets Platform (https://platform.opentargets.org/downloads). The proposal for each drug candidate includes a generated hypothesis, a review of the hypothesis, and a description of the possible mechanism of action.

**中文译文 · 机器初译**

我们使用 Co-Scientist 从由 Open Targets 平台整理的 2300 种药物中选取的一部分，生成了针对 34 种不同癌症类型的药物再利用提案（https://platform.opentargets.org/downloads).）。每种药物候选物的提案都包含生成的假设、对该假设的评估以及可能的作用机制描述。

### co-scientist-0435

**English original**

For each drug-cancer pair, we also extracted the Cancer Dependency Map (DepMap) probability of dependency (“DepMap score”) 3,4. DepMap (Cancer Dependency Map) is a project

**中文译文 · 机器初译**

对于每一对药物-癌症组合，我们还提取了依赖关系的癌症依赖图谱概率（“DepMap 分数”）3,4。癌症依赖图谱（DepMap）是一个项目


### 原文第 75 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=75)

### co-scientist-0437

**English original**

and a publicly available database that focuses on identifying genetic vulnerabilities in cancer cells. By systematically perturbing genes in a large panel of cancer cell lines using techniques like CRISPR and observing the resulting phenotypic effects, DepMap constructs a comprehensive map of genetic dependencies for different cancers. This resource can be leveraged to identify promising drug targets for cancer therapies. Specifically, DepMap generates perturbational data from CRISPR screens that are subsequently used to calculate DepMap dependency scores, representing the probability of gene essentiality for a given cancer cell line. A high DepMap score indicates a high probability that a gene is required for cell survival and proliferation, i.e., it represents the probability of essentiality for a gene in a given cancer cell line.

**中文译文 · 机器初译**

以及一个公开可用的数据库，专门用于识别癌细胞中的遗传脆弱性。通过利用 CRISPR 等技术对大量癌细胞系中的基因进行系统性干扰，并观察由此产生的表型效应，DepMap 构建了不同癌症的遗传依赖关系综合图谱。该资源可用于识别具有潜力的癌症治疗药物靶点。具体而言，DepMap 从 CRISPR 筛选中生成干扰数据，进而用于计算 DepMap 依赖评分，该评分反映了特定癌细胞系中基因的必要性概率。
较高的 DepMap 得分表明该基因对细胞存活和增殖具有高度必要性，即表示该基因在特定癌细胞系中属于必需基因的概率较高。

### co-scientist-0438

**English original**

We utilized the pre-computed DepMap dependency probabilities made available with the Q2 2024 data release of DepMap to construct a rapid, simplified sanity check of Co-Scientist's hypotheses. As part of this sanity check, for each drug-cancer hypothesis generated by Co-Scientist, we extracted the DepMap score for the known target gene associated with the drug in the relevant DepMap cancer cell line models corresponding to the hypothesis.

**中文译文 · 机器初译**

我们利用了 DepMap 2024年第二版数据发布中预计算的 DepMap依赖关系概率，对 Co-Scientist 的假设进行快速、简化的合理性验证。作为该验证的一部分，对于 Co-Scientist 提出的每个药物-癌症假设，我们提取了与该药物相关的已知靶基因在对应假设的 DepMap 癌细胞系模型中的 DepMap得分。

### co-scientist-0439

**English original**

We ranked all drug-cancer pairs using a combined metric of Co-Scientist review score (ranging from 1 to 5) and the DepMap score (ranging from 0.0 to 1.0). To prioritize the most relevant hypotheses for expert review, we selected only pairs where Co-Scientist review score ≥4 and the DepMap score ≥ 0.99. Although this filter on the DepMap scores does not explicitly exclude common-essential or pan-essential genes, we opted for this simple, minimal filtering criterion on the DepMap score, since our use of the DepMap score in this context functions only as a rapid sanity check on Co-Scientist.

**中文译文 · 机器初译**

我们依据“合作科学家评审分数”（范围从1到5）与DepMap分数（范围从0.0到1.0）的综合指标对所有药物-癌症配对进行了排序。为了优先选择适合专家评审的最相关假设，我们仅选取了“合作科学家评审分数”≥4且DepMap分数≥0.99的配对。虽然对DepMap分数的这一筛选条件并未明确排除常见核心基因或泛核心基因，但由于在此情境下使用DepMap分数仅作为对“合作科学家评审”的快速合理性验证手段，我们选择了这种简单且最低限度的筛选标准。

### co-scientist-0440

**English original**

We observed a significant correlation between the DepMap scores and Co-Scientist scores, such that drug-cancer pairs scored highly by Co-Scientist also tended to have higher DepMap scores in the relevant cancer lines. Candidates selected for expert review were required to meet stringent criteria, exhibiting both Co-Scientist review score ≥ 4 and a DepMap score ≥ 0.99 (Supplementary Fig. 8). Finally, the expert oncologists reviewed the top-ranked drug-cancer pairs, provided feedback, and selected promising repurposing candidates for in vitro wet-lab validation (Supplementary Note 5.5, 5.6).

**中文译文 · 机器初译**

我们观察到 DepMap 得分与 Co-Scientist 得分之间存在显著相关性：那些获得 Co-Scientist 高分的药物-癌症组合，在相关癌症样本中往往也具有更高的 DepMap 得分。被选中进行专家评审的候选对象需满足严格标准，即 Co-Scientist 评审得分≥4且DepMap得分≥0.99（补充图8）。最终，专家肿瘤学家对排名靠前的药物-癌症组合进行了审核，提供了反馈意见，并选出了具有潜力的重新应用候选对象以进行体外湿实验验证（补充说明5.5、5.6）。

### co-scientist-0441

**English original**

5.2 AML cell line selection rationale and mechanistic interpretation of drug sensitivities

**中文译文 · 机器初译**

5.2 AML细胞系选择依据及药物敏感性机制解析

### co-scientist-0442

**English original**

Cell line selection was guided by several key principles to ensure experimental rigor and clinical relevance. First, we prioritized genetic diversity to model AML heterogeneity observed in patients. This included cell lines harboring distinct driver mutations as well as those representing different AML subtypes. For example, when evaluating compounds targeting specific pathways such as FLT3, we included both FLT3-ITD positive lines (MV4-11, MOLM-13) and FLT3 wild-type lines (OCI-AML3, HL-60) to distinguish on-target from off-target effects and establish structure-activity relationships across genetic contexts. Similarly, we included NOMO-1, a cell line harboring the t(9;11)(p22;q23) chromosomal translocation resulting in KMT2A-MLLT3

**中文译文 · 机器初译**

选择细胞系时遵循了若干关键原则，以确保实验的严谨性及临床相关性。首先，我们注重基因多样性，以模拟患者中观察到的急性髓系白血病异质性。这包括携带不同驱动突变的细胞系，以及代表不同急性髓系白血病亚型的细胞系。例如，在评估针对特定通路（如FLT3）的化合物时，我们同时纳入了FLT3-ITD阳性细胞系（MV4-11、MOLM-13）和FLT3野生型细胞系（OCI-AML3、HL-60），以便区分靶外效应与靶内效应，并建立不同基因背景下的结构-活性关系。
同样，我们纳入了 NOMO-1 细胞系，该细胞系携带 t(9;11)(p22;q23) 染色体易位，导致 KMT2A-MLLT3 表达异常


### 原文第 76 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=76)

### co-scientist-0444

**English original**

Supplementary Fig. 8 | Co-Scientist review score is concordant with the DepMap score. We demonstrate the distribution of the DepMap score across five Co-Scientist review score groups. Groups with higher Co-Scientist scores tended to have higher DepMap scores. Box plots show the median (center line), first and third quartiles (box limits), and 1.5 times the interquartile range (whiskers). All pairwise comparisons between the group of Co-Scientist score of 5 and each of the other groups are statistically significant (two-sided Wilcoxon rank-sum test without multiple comparison adjustments; exact P values: score 5 vs 4, P = 2.423 × 10-9 ; score 5 vs 3, P < 10-10; score 5 vs 2, P < 10-10; score 5 vs 1, P < 10-10). Sample sizes are n = 202 (score 5), n = 1576 (score 4), n = 6473 (score 3), n = 17404 (score 2), n = 15041 (score 1) drug-cancer pairs respectively.

**中文译文 · 机器初译**

补充图8 | 合作科学家评审分数与DepMap分数一致。我们展示了五个合作科学家评审分数组中DepMap分数的分布情况。合作科学家分数较高的组别往往具有更高的DepMap分数。箱形图显示了中位数（中心线）、第一和第三四分位数（箱限）以及1.5倍四分位距范围（须线）。
Co-Scientist得分为5的组与其他各组的所有成对比较均具有统计学显著性（双侧Wilcoxon秩和检验，未进行多重比较调整；精确P值：得分5对得分4，P = 2.423 × 10-9；得分5对得分3，P < 10-10；得分5对得分2，P < 10-10；得分5对得分1，P < 10-10）。样本量分别为：得分5的组n = 202，得分4的组n = 1576，得分3的组n = 6473，得分2的组n = 17404，得分1的组n = 15041，均为药物与癌症的配对样本。

### co-scientist-0445

**English original**

(MLL-AF9) fusion, to represent AML with KMT2A rearrangements, a clinically relevant subtype with poor outcomes.

**中文译文 · 机器初译**

(MLL-AF9)融合技术，用于表征具有 KMT2A 重排的 AML，这是一种临床相关的亚型，其预后较差。

### co-scientist-0446

**English original**

Second, where available, we considered isogenic cell line pairs, genetically identical except for a single targeted gene, as these provide definitive validation of on-target drug effects. While such paired lines are not universally available for all mutations of interest, they offer powerful confirmatory evidence when obtainable or when custom-engineered for specific validation studies.

**中文译文 · 机器初译**

其次，在可获取的情况下，我们考虑了基因完全相同但仅有一个目标基因不同的等基因细胞系对，因为这些能够明确验证药物对目标基因的作用效果。虽然这种配对细胞系并非针对所有感兴趣的突变都能普遍获得，但在可获取或为特定验证研究定制时，它们能提供强有力的确认性证据。

### co-scientist-0447

**English original**

Third, comprehensive molecular characterization informed both cell line selection and interpretation. Each selected line represents defined molecular subtypes observed clinically, with well-characterized baseline profiles including mutational status, expression signatures, and

**中文译文 · 机器初译**

第三，全面的分子特征分析为细胞系的选择与解读提供了依据。每个选定的细胞系都对应着临床观察到的特定分子亚型，其明确的基线特征包括突变状态、表达特征等。


### 原文第 77 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=77)

### co-scientist-0449

**English original**

signaling pathway activation states. This baseline characterization enables prediction of how gene expression and pathway activity should change following treatment based on each drug’s known mechanism of action and hypothesized repurposing mechanism, facilitating identification of pharmacodynamic biomarkers.

**中文译文 · 机器初译**

信号通路激活状态。这种基础特征描述能够基于每种药物的已知作用机制及假设的重新应用机制，预测治疗后的基因表达和通路活性应发生的变化，从而有助于识别药效生物标志物。

### co-scientist-0450

**English original**

Finally, while immortalized cell lines provide reproducible platforms for initial screening, we recognized that lead candidates require validation in primary patient samples to confirm clinical translatability. Cell lines were therefore selected not only for their experimental utility but also for their molecular similarity to patient subpopulations, informing subsequent validation strategies in patient-derived specimens.

**中文译文 · 机器初译**

最后，虽然 immortal化细胞系为初步筛选提供了可重复的平台，但我们发现潜在的候选药物必须在主要患者样本中进行验证，以确认其临床转化能力。因此，选择这些细胞系不仅是因为其实验应用价值，还因为其与患者亚群在分子层面的相似性，从而为后续在患者来源样本中的验证策略提供了依据。

### co-scientist-0451

**English original**

The complete panel of selected cell lines with their molecular characteristics is provided in Supplementary Table 4.

**中文译文 · 机器初译**

具有特定分子特性的选定细胞系的完整列表见补充表4。

### co-scientist-0452

**English original**

Supplementary Table 4 | Co-Scientist curated list of human AML cell lines for AML drug repurposing studies. The list below details Co-Scientist recommended AML cell lines, the specific AML subtype reflected by each cell-line, key molecular features, and their specific utility in drug repurposing studies. MOLM-13, HL-60, and NOMO-1, representing three AML subtypes, are used in the study (boldfaced).

**中文译文 · 机器初译**

补充表4 | Co-Scientist整理的人类AML细胞系列表，用于AML药物重新应用研究。下表详细列出了Co-Scientist推荐的AML细胞系、每个细胞系的特定AML亚型、关键分子特征以及它们在药物重新应用研究中的具体作用。研究中使用了代表三种AML亚型的MOLM-13、HL-60和NOMO-1（以粗体标出）。

### co-scientist-0453

**English original**

AML Subtype
Cell Line Key Genetic Justification for Use in Drug
(FAB/WHO
Name Mutations Repurposing
Classification)
FLT3-ITD, KMT2A Represents a high-risk AML
(MLL) subtype. The presence of FLT3-ITD
rearrangement makes it an essential model for
AML with
(t(4;11)). Some testing FLT3 inhibitors and
MV4-11 t(4;11)(q21;q23);
studies have overcoming resistance. The
KMT2A-AFF1
detected KMT2A rearrangement also
low-frequency TP53 provides a target for the novel
mutations. menin inhibitors.

**中文译文 · 机器初译**

AML Subtype
Cell Line Key Genetic Justification for Use in Drug
(FAB/WHO
Name Mutations Repurposing
Classification)
FLT3-ITD, KMT2A Represents a high-risk AML
(MLL) subtype. The presence of FLT3-ITD
rearrangement makes it an essential model for
AML with
(t(4;11)). Some testing FLT3 inhibitors and
MV4-11 t(4;11)(q21;q23);
studies have overcoming resistance. The
KMT2A-AFF1
detected KMT2A rearrangement also
low-frequency TP53 provides a target for the novel
mutations. menin inhibitors.

表内文字对照（数值与原始行列保持不变）：
AML Subtype → 大语言模型亚型
Cell Line Key Genetic Justification for Use in Drug → 用于药物的细胞系关键遗传依据
FAB/WHO → FAB/WHO
Name Mutations Repurposing → 名称变更 重新定位
Classification) → 分类）
FLT → FLT
ITD → ITD
KMT → KMT
A Represents a high-risk AML → A代表高风险的反洗钱业务
MLL) subtype → MLL) 亚型
The presence of FLT → FLT的存在
rearrangement makes it an essential model for → 重新编排使其成为一种必要的模型
AML with → 大语言模型驱动的智能体
Some testing FLT → 一些测试 FLT
inhibitors and → 抑制剂及
studies have overcoming resistance → 研究已经克服了阻力
The → 该
A-AFF → A-AFF
detected KMT → 检测到 KMT
A rearrangement also → 一种重排也
low-frequency TP → 低频任务提示
provides a target for the novel → 为新算法提供了目标
mutations → 突变
menin inhibitors → Menin抑制剂

### co-scientist-0454

**English original**

Similar to MV4-11, it is a key
FLT3-ITD,
model for FLT3-ITD targeted
AML with KMT2A (MLL)
therapies. The different KMT2A
MOLM-13 t(9;11)(p22;q23); rearrangement
translocation compared to other
KMT2A-MLLT3 (t(9;11)), possible
lines allows for broader screening
RAS mutations.

**中文译文 · 机器初译**

Similar to MV4-11, it is a key
FLT3-ITD,
model for FLT3-ITD targeted
AML with KMT2A (MLL)
therapies. The different KMT2A
MOLM-13 t(9;11)(p22;q23); rearrangement
translocation compared to other
KMT2A-MLLT3 (t(9;11)), possible
lines allows for broader screening
RAS mutations.

表内文字对照（数值与原始行列保持不变）：
Similar to MV → 与 MV 类似
it is a key → 这是关键
FLT → FLT
ITD → ITD
model for FLT → FLT模型
ITD targeted → ITD 针对
AML with KMT → 基于 KMT 的大语言模型
A (MLL) → A (MLL)
therapies → 疗法
The different KMT → 不同的 KMT
MOLM- → MOLM-
rearrangement → 重组
translocation compared to other → 与其他情况的转换
KMT → KMT
A-MLLT → A-MLLT
possible → 可能的
lines allows for broader screening → 该机制允许进行更广泛的筛选
RAS mutations → RAS突变

### co-scientist-0455

**English original**

of epigenetic modifiers.

**中文译文 · 机器初译**

关于表观遗传修饰因子。


### 原文第 78 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=78)

### co-scientist-0457

**English original**

Represents one of the most common genetic subtypes of AML. The NPM1 mutation makes it a crucial AML with NPM1 (Type A) model for testing therapies targeting OCI-AML3 myelodysplasia-relate mutation, DNMT3A nuclear-cytoplasmic transport and d changes (AML-M4) (R882C) mutation.

**中文译文 · 机器初译**

代表急性髓系白血病中最常见的遗传亚型之一。NPM1突变使得其成为针对 OCI-AML3 骨髓发育相关突变、DNMT3A核质转运及 d 变化（AML-M4）（R882C）突变的疗法的关键测试模型。

### co-scientist-0458

**English original**

other associated pathways. The DNMT3A mutation allows for the screening of epigenetic modifiers.

**中文译文 · 机器初译**

其他相关通路。DNMT3A突变使得表观遗传修饰因子能够被筛选出来。

### co-scientist-0459

**English original**

A classic AML cell line used for Originally classified studying myeloid differentiation.

**中文译文 · 机器初译**

一种经典的大语言模型细胞系，最初用于研究髓系分化。

### co-scientist-0460

**English original**

as M3, but lacks the TP53 deletion,
Its TP53 deficient status makes it
characteristic NRAS (Q61L)
HL-60 valuable for testing drugs that are
t(15;17) and is now mutation, MYC
effective in p53-null cancers. The
considered AML amplification.

**中文译文 · 机器初译**

as M3, but lacks the TP53 deletion,
Its TP53 deficient status makes it
characteristic NRAS (Q61L)
HL-60 valuable for testing drugs that are
t(15;17) and is now mutation, MYC
effective in p53-null cancers. The
considered AML amplification.

表内文字对照（数值与原始行列保持不变）：
as M → 作为 M
but lacks the TP → 但缺乏 TP
deletion → 删除
Its TP → 其TP
deficient status makes it → 状态不足使其
characteristic NRAS (Q → 特征 NRAS (Q)
HL- → HL-
valuable for testing drugs that are → 对测试药物具有价值
and is now mutation → 并且现在正在发生突变
MYC → MYC
effective in p → 在p中有效
null cancers → 无癌病例
The → 该
considered AML amplification → 被视为 AML 放大现象

### co-scientist-0461

**English original**

NRAS mutation provides a target M2.

**中文译文 · 机器初译**

NRAS突变提供了目标M2。

### co-scientist-0462

**English original**

for signaling pathway inhibitors.

**中文译文 · 机器初译**

用于信号通路抑制剂的标识。

### co-scientist-0463

**English original**

DNMT3A (R635W) As a cell line with a DNMT3A
AML with mutation. Some mutation but wild-type NPM1 and
OCI-AML2 myelodysplasia-relate reports indicate FLT3, it serves as an excellent
d changes (AML M4) low-frequency TP53 control to dissect the specific effects
mutations. of DNMT3A-targeted drugs.

**中文译文 · 机器初译**

DNMT3A (R635W) As a cell line with a DNMT3A
AML with mutation. Some mutation but wild-type NPM1 and
OCI-AML2 myelodysplasia-relate reports indicate FLT3, it serves as an excellent
d changes (AML M4) low-frequency TP53 control to dissect the specific effects
mutations. of DNMT3A-targeted drugs.

表内文字对照（数值与原始行列保持不变）：
DNMT → DNMT
A (R → A (R
W) As a cell line with a DNMT → W) 作为一种具有 DNMT 的细胞系
AML with mutation → 带有突变的大语言模型
Some mutation but wild-type NPM → 某种突变，但属于野生型 NPM
and → 并且
OCI-AML → OCI-AML
myelodysplasia-relate reports indicate FLT → 脊髓发育不良相关报告显示 FLT
it serves as an excellent → 它堪称优秀的
d changes (AML M → d 变化（大语言模型）
low-frequency TP → 低频任务提示
control to dissect the specific effects → 控制以分析具体效果
mutations → 突变
of DNMT → 关于 DNMT
A-targeted drugs → 针对性药物

### co-scientist-0464

**English original**

Represents monocytic leukemia and
is a good model for studying
KMT2A (MLL)
MLL-rearranged AML. The
rearrangement
Acute monocytic presence of TP53 and PTEN
THP-1 (t(9;11)), TP53 and
leukemia (AML M5a) alterations makes it suitable for
PTEN
testing drugs that target these
mutations/deletions.

**中文译文 · 机器初译**

Represents monocytic leukemia and
is a good model for studying
KMT2A (MLL)
MLL-rearranged AML. The
rearrangement
Acute monocytic presence of TP53 and PTEN
THP-1 (t(9;11)), TP53 and
leukemia (AML M5a) alterations makes it suitable for
PTEN
testing drugs that target these
mutations/deletions.

表内文字对照（数值与原始行列保持不变）：
Represents monocytic leukemia and → 表示单核细胞白血病
is a good model for studying → 是研究大语言模型的良好模型
KMT → KMT
A (MLL) → A (MLL)
MLL-rearranged AML → MLL重排 AML
The → 该
rearrangement → 重组
Acute monocytic presence of TP → 急性单核细胞中 TP 的存在
and PTEN → 和 PTEN
THP- → THP-
and → 并且
leukemia (AML M → 白血病（急性髓系白血病）
a) alterations makes it suitable for → a) 修改后使其适合
PTEN → PTEN
testing drugs that target these → 测试针对这些靶点的药物
mutations/deletions → 突变/缺失

### co-scientist-0465

**English original**

pathways or exploit synthetic lethality.

**中文译文 · 机器初译**

利用路径或利用合成致命性。

### co-scientist-0466

**English original**

A key model for core-binding factor
RUNX1-RUNX1T1
(CBF) AML. The
(AML1-ETO)
AML with RUNX1-RUNX1T1 fusion is a
fusion, c-Kit
Kasumi-1 t(8;21)(q22;q22); target for epigenetic drugs, and the
(N822K) mutation,
RUNX1-RUNX1T1 activating c-Kit mutation makes it
TP53 (R248Q)
ideal for testing tyrosine kinase
mutation.

**中文译文 · 机器初译**

A key model for core-binding factor
RUNX1-RUNX1T1
(CBF) AML. The
(AML1-ETO)
AML with RUNX1-RUNX1T1 fusion is a
fusion, c-Kit
Kasumi-1 t(8;21)(q22;q22); target for epigenetic drugs, and the
(N822K) mutation,
RUNX1-RUNX1T1 activating c-Kit mutation makes it
TP53 (R248Q)
ideal for testing tyrosine kinase
mutation.

表内文字对照（数值与原始行列保持不变）：
A key model for core-binding factor → 核心结合因子的重要模型
RUNX → RUNX
CBF) AML → CBF) AML
The → 该
AML → 大语言模型
ETO) → ETO)
AML with RUNX → 带有 RUNX 的大语言模型
fusion is a → 融合是一种
fusion → 融合
c-Kit → c-Kit
Kasumi- → Kasumi-
target for epigenetic drugs → 表观遗传药物的靶标
and the → 以及
K) mutation → K) 突变
activating c-Kit mutation makes it → 激活 c-Kit 突变使其发挥作用
ideal for testing tyrosine kinase → 非常适合测试酪氨酸激酶
mutation → 突变

### co-scientist-0467

**English original**

inhibitors.

**中文译文 · 机器初译**

抑制剂。


### 原文第 79 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=79)

### co-scientist-0469

**English original**

Another important model for
MLL-rearranged AML,
KMT2A (MLL)
specifically of the monocytic
Acute monocytic rearrangement
subtype. The co-occurrence of
NOMO-1 leukemia (AML (t(9;11)), KRAS
KRAS and TP53 mutations with
M5a) (G13D), and TP53
the MLL rearrangement allows
mutations.

**中文译文 · 机器初译**

Another important model for
MLL-rearranged AML,
KMT2A (MLL)
specifically of the monocytic
Acute monocytic rearrangement
subtype. The co-occurrence of
NOMO-1 leukemia (AML (t(9;11)), KRAS
KRAS and TP53 mutations with
M5a) (G13D), and TP53
the MLL rearrangement allows
mutations.

表内文字对照（数值与原始行列保持不变）：
Another important model for → 另一个重要的模型
MLL-rearranged AML → MLL重排 AML
KMT → KMT
A (MLL) → A (MLL)
specifically of the monocytic → 特别是单核细胞类
Acute monocytic rearrangement → 急性单核细胞重排
subtype → 子类型
The co-occurrence of → 大语言模型的共现
NOMO- → NOMO-
leukemia (AML (t( → 白血病（急性髓系白血病（t(
KRAS → KRAS
KRAS and TP → KRAS 和 TP
mutations with → 具有突变的
a) (G → a) (G
and TP → 和 TP
the MLL rearrangement allows → 大语言模型重排机制允许
mutations → 突变

### co-scientist-0470

**English original**

for the study of drugs targeting multiple oncogenic pathways.

**中文译文 · 机器初译**

用于研究针对多种致癌途径的药物。

### co-scientist-0471

**English original**

Represents a rare subtype of
myeloid leukemia characterized by
FIP1L1-PDGFRA eosinophilia. The FIP1L1-PDGFRA
fusion, KMT2A fusion makes it highly sensitive to
EOL-1 Eosinophilic leukemia
(MLL) partial tyrosine kinase inhibitors like
tandem duplication. imatinib, serving as a positive
control and a model for studying
resistance mechanisms.

**中文译文 · 机器初译**

Represents a rare subtype of
myeloid leukemia characterized by
FIP1L1-PDGFRA eosinophilia. The FIP1L1-PDGFRA
fusion, KMT2A fusion makes it highly sensitive to
EOL-1 Eosinophilic leukemia
(MLL) partial tyrosine kinase inhibitors like
tandem duplication. imatinib, serving as a positive
control and a model for studying
resistance mechanisms.

表内文字对照（数值与原始行列保持不变）：
Represents a rare subtype of → 代表一种罕见的子类型
myeloid leukemia characterized by → 以髓系白血病为特征的
FIP → FIP
PDGFRA eosinophilia → PDGFRA 嗜酸性粒细胞增多
The FIP → FIP
PDGFRA → PDGFRA
fusion → 融合
KMT → KMT
A fusion makes it highly sensitive to → 融合后使其对……非常敏感
EOL- → EOL-
Eosinophilic leukemia → 嗜酸性白血病
MLL) partial tyrosine kinase inhibitors like → MLL）类部分酪氨酸激酶抑制剂
tandem duplication → 串联重复
imatinib → 伊马替尼
serving as a positive → 作为积极因素发挥作用
control and a model for studying → 控制机制及用于研究的模型
resistance mechanisms → 抵抗机制

### co-scientist-0472

**English original**

Case study: Mechanistic rationale for differential KIRA6 sensitivity. Building upon this selection rationale, the phenotypic and cytogenetic diversity of our cell line panel provided crucial mechanistic insights during our in vitro validations. Specifically, when evaluating the novel candidate KIRA6 (an IRE1α inhibitor), we observed highly variable sensitivities that closely tracked with the differentiation states of the AML cell lines.

**中文译文 · 机器初译**

案例研究：不同 KIRA6敏感性的机制原因。基于这一选择依据，我们细胞系组的表型与细胞遗传学多样性在体外验证过程中提供了重要的机制性见解。具体而言，在评估新型候选物 KIRA6（一种 IRE1α 抑制剂）时，我们发现其敏感性存在显著差异，且与 AML 细胞系的分化状态高度一致。

### co-scientist-0473

**English original**

As noted in the main text, KIRA6 demonstrated heightened susceptibility observed in KG-1a cells, which retain a primitive CD34⁺, stem-like phenotype. In contrast, MOLM-13 (FAB M5a) and HL-60 (FAB M2) represent more differentiated myeloid lineages with preserved capacity for terminal maturation. Because the IRE1α–XBP1 axis supports self-renewal programs in hematopoietic and pre-leukemic stem cells, the preferential sensitivity of KG-1a suggests that IRE1α inhibition may disproportionately affect primitive AML populations. The 18-fold separation between the KG-1a IC50 and that of the normal lymphoblastoid TK6 line further raises the possibility of a therapeutic window, although this requires validation in primary AML samples and in vivo models to define selectivity and clinically actionable exposures. NOMO-1’s intermediate sensitivity (IC50 = 144 nM) may reflect its retained differentiation plasticity, as these KMT2A-MLLT3-rearranged cells remain responsive to terminal monocytic differentiation cues such as TPA, distinguishing them from primitive CD34⁺ KG-1a cells and suggesting reduced dependence on IRE1α-mediated proteostasis for self-renewal. This positions NOMO-1 between highly primitive, IRE1α-dependent AML (KG-1a) and fully differentiated, IRE1α-independent lineages (MOLM-13, HL-60).

**中文译文 · 机器初译**

如正文所述，KIRA6在保留原始 CD34⁺ 干细胞样表型的 KG-1a 细胞中表现出更高的敏感性。相比之下，MOLM-13（FAB M5a）和 HL-60（FAB M2）则属于更成熟的髓系谱系，仍具有终末成熟能力。由于 IRE1α–XBP1 轴支持造血及前白血病干细胞的自我更新过程，KG-1a 的特殊敏感性表明 IRE1α 抑制可能对原始 AML 群体产生不成比例的影响。
KG-1a的IC50与正常淋巴母细胞TK6系之间的18倍差异，进一步增加了其作为治疗药物的潜力，不过仍需在原发性AML样本和体内模型中进行验证，以明确其选择性及具有临床应用价值的剂量范围。NOMO-1的中等敏感性（IC50 = 144 nM）可能反映了其保留的分化可塑性，因为这些KMT2A-MLLT3重组细胞仍对终末单核细胞分化信号（如TPA）具有反应性，这使其与原始CD34⁺ KG-1a细胞有所区别，并表明其在自我更新过程中对IRE1α介导的蛋白质稳态系统的依赖较低。
这使得 NOMO-1 处于高度原始、依赖 IRE1α 的 AML（KG-1a）与完全分化、不依赖 IRE1α 的谱系（MOLM-13、HL-60）之间。

### co-scientist-0474

**English original**

Overall, these data validate our cell line selection strategy and suggest that IRE1α blockade may be most effective in AML subsets enriched for stem-like transcriptional states,

**中文译文 · 机器初译**

总体而言，这些数据验证了我们的细胞系选择策略，并表明 IRE1α 阻断可能在具有干细胞样转录状态的 AML 亚群中最为有效。


### 原文第 80 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=80)

### co-scientist-0476

**English original**

such as therapy-associated myeloid neoplasms, while resistance in more differentiated leukemias warrants additional mechanistic investigation.

**中文译文 · 机器初译**

例如与治疗相关的髓系肿瘤，而更分化型白血病的耐药性则需要进行额外的机制研究。

### co-scientist-0477

**English original**

5.3 Details of the selected repurposed drugs

**中文译文 · 机器初译**

5.3 选定的重新应用药物的详细情况

### co-scientist-0478

**English original**

Binimetinib is an inhibitor of MEK1 and MEK2, key kinases in the RAS–RAF–MEK–ERK signaling pathway. By inhibiting MEK1/2, binimetinib prevents the activation of ERK (extracellular signal-regulated kinase), thereby blocking downstream signaling that promotes cell proliferation and survival 5. Although RAS mutations typically emerge as late events in AML pathogenesis, Binimetinib was included to investigate its potential to modulate RAS-MEK-ERK signaling in treatment-naive AML, where baseline expression levels of this pathway can influence sensitivity to conventional chemotherapeutic agents 6.

**中文译文 · 机器初译**

比尼米特替尼是一种MEK1和MEK2抑制剂，而MEK1和MEK2是RAS–RAF–MEK–ERK信号通路中的关键激酶。通过抑制MEK1/2，比尼米特替尼能够阻止ERK（细胞外信号调节激酶）的激活，从而阻断促进细胞增殖和存活的下游信号传导过程。尽管RAS突变通常出现在急性髓系白血病发病过程的后期阶段，但本研究仍纳入了比尼米特替尼，以探讨其在未接受治疗的急性髓系白血病中调节RAS-MEK-ERK信号通路的潜力，因为该通路的基线表达水平会影响对常规化疗药物的敏感性。

### co-scientist-0479

**English original**

Pacritinib is an oral tyrosine kinase inhibitor that selectively targets JAK2 and FLT3 kinases 7. By blocking JAK2’s kinase activity, pacritinib suppresses the overactive JAK-STAT signaling that drives pathogenic cell proliferation and cytokine production in diseases such as myelofibrosis. It was selected for repurposing due to the dual inhibition of growth signaling pathways: the JAK2/STAT pathway, critical in hematopoietic cell growth and inflammatory signaling, and FLT3-driven proliferative signaling that regulates leukemic cell survival and also facilitates the development of escape pathways to targeted therapies 8.

**中文译文 · 机器初译**

帕克里替尼是一种口服酪氨酸激酶抑制剂，能够选择性靶向 JAK2 和 FLT3 激酶。通过阻断 JAK2 的激酶活性，帕克里替尼可抑制过度活跃的 JAK-STAT 信号传导，从而抑制骨髓纤维化等疾病中导致细胞增殖和细胞因子产生的过程。其被选中用于重新应用，是因为它能够同时抑制两种生长信号通路：在造血细胞生长和炎症信号传导中至关重要的 JAK2/STAT 通路，以及由 FLT3 驱动的增殖信号通路，后者不仅调控白血病细胞的存活，还能促进对靶向治疗的逃逸途径的形成。

### co-scientist-0480

**English original**

Dimethyl fumarate (DMF) is an immunomodulatory drug that activates the Nrf2 (nuclear factor erythroid 2–related factor 2) pathway via covalent modification of the cysteine residues on Keap1, the cytosolic protein that normally binds Nrf2 and targets it for degradation. By oxidizing or alkylating the thiol groups of Keap1, DMF destabilizes the Keap1-Nrf2 complex, allowing Nrf2 to escape ubiquitination and translocate into the nucleus. In parallel, DMF also inhibits NFκB mediated transcription and was chosen for repurposing due to clinically relevant activity of NFκB in AML 9,10.

**中文译文 · 机器初译**

富马酸二甲基酯是一种免疫调节药物，通过共价修饰Keap1上的半胱氨酸残基，激活Nrf2（核因子红系2相关因子2）通路。Keap1是一种胞质蛋白，通常与Nrf2结合并将其用于降解。通过氧化或烷基化Keap1的巯基，DMF使Keap1-Nrf2复合体不稳定，从而使Nrf2摆脱泛素化作用并进入细胞核。同时，DMF还能抑制NFκB介导的转录过程，因其在急性髓系白血病中具有临床相关的作用，因此被选作重新应用的药物。

### co-scientist-0481

**English original**

The statins (Cerivastatin and Pravastatin) were selected for their potential to induce metabolic reprogramming and modulate vesicular transport mechanisms in rapidly proliferating cells 11.

**中文译文 · 机器初译**

他汀类药物（塞瑞瓦司汀和普伐他汀）被选中，是因为它们具有诱导代谢重编程并调节快速增殖细胞中的囊泡运输机制的能力 11。

### co-scientist-0482

**English original**

JNJ-64619178 (Onametastat) is a selective, potent and pseudo-irreversible inhibitor of protein arginine methyltransferase 5 (PRMT5), an enzyme that modulates the methylation program governing RNA splicing. This agent is hypothesized to demonstrate clinically meaningful activity in hematologic malignancies harboring splicing-factor mutations (notably SRSF2, U2AF1, SF3B1, and SF3A1), as well as in AML characterized by secondary-type mutational profiles 12,13.

**中文译文 · 机器初译**

JNJ-64619178（Onametastat）是一种选择性、高效且伪不可逆的蛋白质精氨酸甲基转移酶5（PRMT5）抑制剂，该酶参与调控RNA剪接的甲基化过程。据假设，该药物在存在剪接因子突变的血液系统恶性肿瘤中（尤其是SRSF2、U2AF1、SF3B1和SF3A1突变），以及具有第二类突变特征的急性髓系白血病中能发挥具有临床意义的疗效。


### 原文第 81 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=81)

### co-scientist-0484

**English original**

Selinexor is a selective inhibitor of Exportin 1 (XPO1), a nuclear export protein responsible for transporting numerous cargo proteins including tumor suppressors (such as p53), and transcription factors (NFκB) from the nucleus to the cytoplasm. By inhibiting XPO1, selinexor forces nuclear retention of these proteins, leading to cell cycle arrest and apoptosis. For instance, in NPM1-mutated AML, XPO1 inhibition prevents cytoplasmic mislocalization of mutant NPM1, enforcing its nuclear retention and driving terminal monocytic differentiation through downregulation of the MEIS1/HOXA9 leukemogenic program. More broadly, this mechanism represents a therapeutic vulnerability across hematologic malignancies and is currently being evaluated in solid tumors.

**中文译文 · 机器初译**

塞利内索是一种选择性抑制 Exportin 1（XPO1）的抑制剂。XPO1是一种核输出蛋白，负责将包括肿瘤抑制因子（如 p53）和转录因子（NFκB）在内的多种蛋白质从细胞核运输到细胞质。通过抑制 XPO1，塞利内索使这些蛋白质在细胞核内滞留，从而导致细胞周期停滞和细胞凋亡。例如，在 NPM1突变型急性髓系白血病中，抑制 XPO1可防止突变的 NPM1在细胞质中的异常定位，使其留在细胞核内，并通过下调 MEIS1/HOXA9致癌程序推动终末单核细胞分化。
更广泛地说，这种机制在血液系统恶性肿瘤中属于一种治疗性弱点，目前正被用于评估实体肿瘤的应用效果。

### co-scientist-0485

**English original**

SNDX-5613 (Revumenib) is a selective oral inhibitor of the menin-KMT2A interaction. Menin serves as a critical oncogenic cofactor in acute leukemias with KMT2A rearrangements (occurring in up to 10% of AML) and NPM1 mutations (the most common genetic alteration in AML, occurring in up to 30% of cases). The menin-KMT2A complex drives aberrant expression of HOX genes (particularly HOXA9) and MEIS1, causing a hematopoietic differentiation block and leukemic transformation. Revumenib disrupts this interaction, downregulating these leukemogenic transcription factors and reversing the differentiation block. The drug has recently gained FDA approval for AML in the aforementioned contexts and is undergoing clinical investigation in combination regimens.

**中文译文 · 机器初译**

SNDX-5613（Revumenib）是一种选择性口服抑制menin-KMT2A相互作用的药物。在伴有KMT2A重排的急性白血病（可发生在高达10%的急性髓系白血病中）以及NPM1突变的病例中（这是急性髓系白血病最常见的基因变异，可发生在高达30%的病例中），menin作为重要的致癌辅助因子发挥作用。menin-KMT2A复合体会促进HOX基因（尤其是HOXA9）和MEIS1的异常表达，导致造血分化受阻和白血病转化。Revumenib能够破坏这种相互作用，降低这些致白血病转录因子的活性，从而逆转分化受阻现象。
该药物最近获得了美国食品药品监督管理局对上述疾病场景中AML的批准，目前正进行联合治疗方案的临床研究。

### co-scientist-0486

**English original**

Palbociclib is an inhibitor of cyclin-dependent kinases 4 and 6 (CDK4/6), which are key regulators of cell cycle progression from G1 to S phase. By inhibiting CDK4/6, palbociclib prevents phosphorylation of the retinoblastoma protein (Rb), maintaining its tumor suppressor function and inducing G1 cell cycle arrest. While approved for breast cancer, CDK4/6 inhibitors are being repurposed for Kaposi’s sarcoma, and also, being investigated in hematological malignancies for synergy with other targeted therapies to overcome resistance 14.

**中文译文 · 机器初译**

帕博西利是一种环化周期依赖性激酶4和6（CDK4/6）抑制剂，而这两种激酶是细胞周期从G1期进入S期的关键调控因子。通过抑制CDK4/6，帕博西利能够阻止视网膜母细胞瘤蛋白（Rb）的磷酸化，维持其肿瘤抑制功能，并导致G1期细胞周期停滞。虽然已被批准用于乳腺癌治疗，但CDK4/6抑制剂正被重新用于卡波西肉瘤的治疗，同时也在血液恶性肿瘤中作为其他靶向疗法的协同疗法进行研究，以克服药物耐药性14。

### co-scientist-0487

**English original**

Venetoclax is a BCL-2 inhibitor that induces apoptosis in cancer cells by displacing pro-apoptotic proteins (such as BIM) from BCL-2, allowing them to activate the intrinsic apoptotic pathway. Venetoclax is already FDA-approved for AML in combination with hypomethylating agents or low-dose cytarabine for newly diagnosed elderly patients or those ineligible for intensive chemotherapy. This drug was included in our panel to evaluate its synergistic potential with other targeted agents, particularly given that venetoclax-based combinations have demonstrated high response rates.

**中文译文 · 机器初译**

维内托克沙是一种 BCL-2 抑制剂，通过从 BCL-2 中置换促凋亡蛋白（如 BIM），诱导癌细胞发生凋亡，从而激活内在凋亡途径。维内托克沙已获得美国食品药品监督管理局批准，用于与低甲基化药物或低剂量阿糖胞苷联合使用，治疗新诊断的老年患者或无法接受强化化疗的患者。该药物被纳入我们的评估方案，以考察其与其他靶向药物的协同作用潜力，尤其是鉴于基于维内托克沙的组合疗法已显示出较高的缓解率。

### co-scientist-0488

**English original**

Pinometostat is a small molecule inhibitor of DOT1L (disruptor of telomeric silencing 1-like), a histone H3 lysine 79 (H3K79) methyltransferase. DOT1L is recruited by MLL fusion proteins in KMT2A-rearranged leukemias, where it aberrantly methylates H3K79 and drives expression of leukemogenic genes including HOXA9 and MEIS1. By inhibiting DOT1L, pinometostat reduces H3K79 methylation and downregulates these oncogenic transcription factors.

**中文译文 · 机器初译**

Pinometostat是一种DOT1L的小分子抑制剂，DOT1L是一种组蛋白H3赖氨酸79（H3K79）甲基转移酶。在KMT2A重排白血病中，MLL融合蛋白会招募DOT1L，使其异常甲基化H3K79，进而促进包括HOXA9和MEIS1在内的致癌基因的表达。通过抑制DOT1L，Pinometostat能够减少H3K79的甲基化，并降低这些致癌转录因子的表达。


### 原文第 82 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=82)

### co-scientist-0490

**English original**

JQ1 is a small molecule inhibitor of bromodomain and extraterminal domain (BET) proteins, particularly BRD4. BET proteins are epigenetic readers that recognize acetylated lysine residues on histones and regulate transcription of key oncogenes including MYC. In AML, BRD4 is frequently overexpressed and drives expression of genes critical for leukemic cell survival and proliferation. JQ1 competitively binds to the acetyl-lysine recognition pocket of BET bromodomains, displacing them from chromatin and suppressing oncogene transcription.

**中文译文 · 机器初译**

JQ1是一种针对溴域域和延伸端域（BET）蛋白的小分子抑制剂，尤其针对BRD4。BET蛋白是表观遗传识别器，能够识别组蛋白上的乙酰化赖氨酸残基，并调控包括MYC在内的关键癌基因的转录。在急性髓系白血病中，BRD4常常过度表达，从而推动对白血病细胞存活和增殖至关重要的基因的表达。JQ1与BET溴域域的乙酰化赖氨酸识别口袋发生竞争结合，将其从染色质中置换出来，进而抑制癌基因转录。

### co-scientist-0491

**English original**

Olaparib is a poly(ADP-ribose) polymerase (PARP) inhibitor that blocks DNA single-strand break repair, leading to accumulation of DNA double-strand breaks and synthetic lethality in cells with defective homologous recombination repair (such as those with BRCA mutations). While olaparib is approved for ovarian, breast, pancreatic, and prostate cancers with homologous recombination deficiency, emerging evidence indicates that baseline DNA repair defects may confer PARP inhibitor sensitivity, and that combining PARP inhibition with DNA-damaging chemotherapy can enhance synthetic lethality.

**中文译文 · 机器初译**

奥拉帕利是一种多聚(ADP-核糖)聚合酶（PARP）抑制剂，能够阻断DNA单链断裂修复过程，导致DNA双链断裂积累，从而在具有缺陷的同源重组修复功能的细胞中引发合成致死效应（如BRCA突变细胞）。虽然奥拉帕利已被批准用于同源重组缺陷相关的卵巢、乳腺、胰腺和前列腺癌治疗，但最新研究表明，基础DNA修复缺陷可能使细胞对PARP抑制剂产生敏感性，且将PARP抑制与DNA损伤性化疗联合使用可进一步加剧合成致死效应。

### co-scientist-0492

**English original**

MSA2 (N-myristoyltransferase inhibitor) targets N-myristoyltransferases (NMT1 and NMT2), enzymes that catalyze the attachment of myristate to N-terminal glycine residues of proteins—a post-translational modification essential for membrane localization and function of numerous signaling proteins. In cancer cells, NMT activity is frequently elevated and supports multiple pro-survival signaling cascades simultaneously including SRC family kinases, ARF GTPases, and immune checkpoint regulators.

**中文译文 · 机器初译**

MSA2（N-肉豆蔻酰转移酶抑制剂）作用于N-肉豆蔻酰转移酶（NMT1和NMT2），这类酶能够催化肉豆蔻酸与蛋白质的N端甘氨酸残基结合——这种翻译后修饰对许多信号蛋白的膜定位和功能至关重要。在癌细胞中，NMT活性往往升高，从而同时促进多种生存相关信号通路活动，包括SRC家族激酶、ARF GTP酶以及免疫检查点调节因子。

### co-scientist-0493

**English original**

5.4 In vitro wet-lab validation setup

**中文译文 · 机器初译**

5.4 体外湿实验验证设置

### co-scientist-0494

**English original**

Single agent screening and IC50 determination. To evaluate the expert-selected drug candidates for acute myeloid leukemia (AML) repurposing, we determined their half-maximal inhibitory concentration (IC50), the drug concentration required to inhibit cell viability by 50%, in representative cell lines (MOLM-13, KG-1a, HL-60, NOMO-1, and TK6). IC50 is a value commonly used as a way to quantify the effectiveness of a drug at inhibiting cellular processes, and can be measured by treating cells across a broad range of drug concentrations and fitting the dose response to a sigmoidal curve to determine 50% of maximal inhibition 15.

**中文译文 · 机器初译**

单一智能体筛选及 IC50 测定。为了评估专家筛选出的急性髓系白血病（AML）替代用药候选物，我们在代表性细胞系（MOLM-13、KG-1a、HL-60、NOMO-1 和 TK6）中测定了它们的半最大抑制浓度（IC50），即使细胞存活率降低 50% 所需的药物浓度。IC50 是一种常用于量化药物对细胞过程抑制作用的有效性的指标，可通过在多种药物浓度下处理细胞，并将剂量反应曲线拟合为S形曲线来确定 50% 的最大抑制值来实现。

### co-scientist-0495

**English original**

Cells were seeded in 96-well plates at a density of 5 × 103–1 × 104 cells per well and allowed to equilibrate overnight under standard culture conditions (37 °C, 5% CO2, humidified incubator). Single-agent treatments were performed using an eight-point serial dilution series. Each compound was prepared as a concentrated stock and serially diluted (typically three to four-fold) to generate eight concentrations spanning the expected pharmacologically active range. Each dose was tested in triplicate together with vehicle-treated control wells. Plates were incubated for 48 to 96 hours before viability measurement.

**中文译文 · 机器初译**

细胞以每孔 5 × 10³–1 × 10⁴ 个细胞的密度接种于 96 孔板中，在标准培养条件（37 °C、5% CO₂、湿润培养箱）下让其过夜平衡。单药处理采用八点连续稀释系列进行。每种化合物均制备为浓缩储备液，并依次稀释（通常三到四倍），以得到覆盖预期药理活性范围的八种浓度。每个剂量需进行三次试验，并同时设置溶剂处理的对照孔。在测量存活率之前，孔板需培养 48 至 96 小时。


### 原文第 83 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=83)

### co-scientist-0497

**English original**

Cell viability was assessed using the CellTiter 96® AQueous One Solution Cell Proliferation (MTS) Assay (Promega) following the manufacturer’s instructions. Twenty microliters of reagent were added to each well and plates were incubated for 1 or 4 hours at 37 °C. Absorbance at 490 nm was recorded using a multimode microplate reader. Raw absorbance values were normalized to vehicle controls to compute percentage inhibition, which was plotted against drug concentration to generate dose–response curves. Curve fitting and estimation of IC50 values were performed using GraphPad Prism. ​ Three cell lines used (MOLM-13, HL-60, and KG-1a) were generous gifts from the lab of Dr. Ravi Majeti (Stanford University), the NOMO-1 cell line was provided by Creative Bioarray, and the TK6 cell line was provided by ATCC. ●​ MOLM-13 cell line is a human AML cell line that was derived from bone marrow samples of a 62-year-old woman with AML. ●​ HL-60 cell line is a human cell line from a patient with acute promyelocytic leukemia (APL), often used to study the development and proliferation of normal and leukemic cells. ●​ KG-1a cell line is a human cell line isolated from the bone marrow aspirate of a 59-year-old, white male with erythroleukemia that evolved into AML. ●​ NOMO-1 cell line is a human AML cell line derived from the bone marrow of a 31-year-old woman with acute monocytic leukemia (AML FAB M5a) at second relapse.

**中文译文 · 机器初译**

根据制造商说明，使用 CellTiter 96® AQueous One Solution 细胞增殖（MTS）检测法（Promega）评估细胞活力。向每个孔中加入20微升试剂，培养板在37°C下孵育1或4小时。使用多模式微孔板读取器记录490 nm处的吸光度值。将原始吸光度值与溶剂对照值进行归一化，以计算抑制百分比，随后根据药物浓度绘制曲线，生成剂量-反应曲线。使用GraphPad Prism进行曲线拟合和IC50值的估算。所使用的三种细胞系为MOLM-13、HL-60和KG-1a，这些均为来自某实验室的慷慨捐赠。
Ravi Majeti（斯坦福大学），NOMO-1细胞系由Creative Bioarray提供，TK6细胞系由ATCC提供。● MOLM-13细胞系是一种人类急性髓系白血病细胞系，来源于一名62岁急性髓系白血病患者的骨髓样本。● HL-60细胞系是一种来自急性早幼粒细胞白血病患者的人类细胞系，常用于研究正常细胞和白血病细胞的发育与增殖过程。● KG-1a细胞系是一种从一名59岁白人男性患者的骨髓抽吸液中分离出的人类细胞系，该患者患有红系白血病，后发展为急性髓系白血病。● NOMO-1细胞系是一种源自一名31岁女性患者的骨髓的人类急性髓系白血病细胞系。
第二次复发时的单核细胞性白血病（AML FAB M5a）。

### co-scientist-0498

**English original**

The cell line harbors the t(9;11)(p22;q23) chromosomal translocation resulting in the KMT2A-MLLT3 (MLL-AF9) fusion gene. ●​ TK6 cell line is a non-AML lymphoblastoid cell line used as a non-AML control for establishing a therapeutic window and assessing AML-specific selective cytotoxicity.

**中文译文 · 机器初译**

该细胞系存在 t(9;11)(p22;q23) 染色体易位现象，导致 KMT2A-MLLT3 (MLL-AF9) 融合基因的形成。●​ TK6 细胞系是一种非 AML 淋巴母细胞样细胞系，用于作为非 AML 对照，以确立治疗窗口并评估与 AML 相关的选择性细胞毒性。

### co-scientist-0499

**English original**

Fixed-ratio combination treatment and Chou-Talalay synergy analysis. To quantitatively assess pharmacological interactions between candidate compounds, combination treatments were performed using a fixed-ratio design, and synergy was evaluated according to the Chou-Talalay combination index (CI) method. Each drug was first tested alone to determine its dose–response curve and IC50 value.

**中文译文 · 机器初译**

固定比例组合治疗与Chou-Talalay协同效应分析。为了定量评估候选化合物之间的药理学相互作用，采用固定比例设计进行组合治疗，并根据Chou-Talalay组合指数（CI）方法评估协同效应。首先单独测试每种药物，以确定其剂量-反应曲线和IC50值。

### co-scientist-0500

**English original**

For combination studies, the two drugs were mixed at a fixed molar ratio, and an eight-point dilution series was prepared to span concentrations above and below their respective IC50 values, ensuring that the midpoint of the series corresponded approximately to the IC50 range of each agent. An eight-point serial dilution series was prepared to cover a broad range of effects, and the mixtures were applied to cells in triplicate. After 48 to 72 hours of drug exposure, cell viability was determined using the CellTiter 96® AQueous One Solution MTS Assay (Promega), as described above. Absorbance readings at 490 nm were normalised to the vehicle control to calculate percentage inhibition at each concentration. Cell lines for combination treatment studies were from AddexBio (MOLM-13), and ATCC (KG-1a).

**中文译文 · 机器初译**

对于组合研究，这两种药物以固定的摩尔比混合，并制备了八点稀释系列，以覆盖其各自 IC50 值上下范围内的浓度，确保该系列的中点大致对应每种药物的 IC50 区间。通过八点连续稀释系列来涵盖广泛的效应范围，并将混合液以三份量应用于细胞。在暴露于药物 48 至 72 小时后，采用上述的 CellTiter 96® AQueous One Solution MTS 检测法（Promega）测定细胞存活率。
在 490 nm 处的吸光度值已根据对照组进行标准化处理，以计算各浓度下的抑制百分比。联合治疗研究的细胞系来自 AddexBio（MOLM-13）和 ATCC（KG-1a）。

### co-scientist-0501

**English original**

Synergy analysis was performed using the Chou-Talalay method, which quantitatively determines whether two drugs act synergistically, additively, or antagonistically based on their

**中文译文 · 机器初译**

采用Chou-Talalay方法进行了协同作用分析，该方法根据两种药物的作用方式，定量判断其是协同作用、相加作用还是拮抗作用


### 原文第 84 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=84)

### co-scientist-0503

**English original**

dose–response behavior. Dose-effect data from single-agent and combination treatments were analysed using Julius AI statistical software, which computes CI values for each dose–effect level. Interaction outcomes were classified as synergistic (CI < 1), additive (CI ≈ 1), or antagonistic (CI > 1). Results were visualized as Fa-CI plots, showing the relationship between fractional effect (Fa) and CI, and as isobolograms at selected effect levels.

**中文译文 · 机器初译**

剂量-反应行为。通过 Julius AI 统计软件对单药治疗及联合治疗的剂量效应数据进行了分析，该软件可计算各剂量-效应水平的置信区间值。交互作用结果被分为协同作用（CI < 1）、相加作用（CI ≈ 1）或拮抗作用（CI > 1）。结果以 Fa-CI 图形式进行可视化展示，呈现分数效应（Fa）与置信区间之间的关系，并在选定的效应水平下以等线图形式展示。

### co-scientist-0504

**English original**

Three drug combination treatments. We tested three drugs together across a grid of doses in each cell line and measured the response. Raw readouts were converted to fractional effect relative to controls so everything was on the same 0 to 1 scale.

**中文译文 · 机器初译**

三种药物组合疗法。我们在每种细胞系的剂量范围内对三种药物进行了联合测试，并测量了反应情况。原始数据被转换为相对于对照组的分数效应，以便所有数据都处于相同的 0 到 1 范围内。

### co-scientist-0505

**English original**

To judge whether the combinations performed better than expected, we used two standard checks: ●​ Bliss independence compares the observed combination effect to what you would expect if the drugs acted independently (no interaction). ●​ Highest Single Agent (HSA) compares the combination to the best single drug at the same doses.

**中文译文 · 机器初译**

为了判断这些组合是否优于预期，我们采用了两种标准检验方法：●  bliss独立性检验用于比较观察到的组合效应与药物独立作用时的预期值（无相互作用情况）；● 最高单药效果检验用于将该组合与相同剂量的最佳单药进行比较。

### co-scientist-0506

**English original**

For each dataset, we visualized interaction as dose–dose heatmaps with a color scale centered at zero (red = synergy, blue = antagonism, white = additivity). To compress the three‑drug space into a single figure, we took each A × B dose pair and scanned across all C doses to find the strongest positive interaction (the “max over C”). We annotated each heatmap cell with the C dose that produced that maximum. Figures were generated in Python using pandas/numpy for data handling and seaborn/matplotlib for plotting.

**中文译文 · 机器初译**

对于每个数据集，我们将相互作用以剂量-剂量热图的形式进行可视化，颜色刻度以零为中心（红色表示协同作用，蓝色表示拮抗作用，白色表示加和性）。为了将三种药物的空间信息压缩到一张图中，我们取每一组 A × B 剂量组合，并遍历所有 C 个剂量，找出最强的正相互作用（即“C 维度上的最大值”）。我们在每个热图单元格中标注出产生该最大值的 C 剂量。这些图表使用 Python 中的 pandas/numpy 处理数据，以及 seaborn/matplotlib 进行绘图生成。

### co-scientist-0507

**English original**

5.5 Additional wet-lab results

**中文译文 · 机器初译**

5.5 额外的湿实验结果

### co-scientist-0508

**English original**

This section provides additional in vitro laboratory results of drug repurposing. Extended Data Fig. 3 shows dose-response curves of Binimetinib in KG-1a, HL-60 and TK6 cell lines. Extended Data Fig. 4 shows the dose response curves of drug repurposing candidates for AML suggested by Co-Scientist that had little to no effect on MOLM-13 cells.

**中文译文 · 机器初译**

本部分提供了药物重新应用相关的额外体外实验室结果。扩展数据图3展示了Binimetinib在KG-1a、HL-60和TK6细胞系中的剂量-反应曲线。扩展数据图4则展示了由合作科学家提出的用于AML的药物重新应用候选药物的剂量-反应曲线，这些药物对MOLM-13细胞几乎没有影响。

### co-scientist-0509

**English original**

Comprehensive analysis of drug combination synergies. To systematically investigate the novel drug interactions proposed by Co-Scientist, we evaluated the full panel of combinations in MOLM-13 and KG-1a cell lines (Fig. 4 and Extended Figs. 5 and 6). In MOLM-13 cells, responses were predominantly synergistic. Strong and consistent synergy was observed for dual combinations including JNJ-64619178 + Selinexor, JNJ-64619178 + SNDX-5613, and Palbociclib + Selinexor, as well as the triple combinations of JQ1 + Olaparib + MSA2 and JNJ-64619178 + SNDX-5613 + Selinexor. In contrast, KG-1a cells exhibited highly context-dependent responses with a mixture of synergy and antagonism. While Palbociclib + Selinexor and Venetoclax + Pinometostat showed strong synergistic effects, the combination of JNJ-64619178 + Selinexor had antagonism at lower effect levels, transitioning to synergy at the highest effects. Notably, while the JNJ-64619178 + SNDX-5613 + Selinexor triplet was

**中文译文 · 机器初译**

对药物组合协同作用进行了全面分析。为了系统研究联合科学家提出的新型药物相互作用，我们在 MOLM-13 和 KG-1a 细胞系中评估了所有组合方案（图 4 及扩展图 5 和 6）。在 MOLM-13 细胞中，反应主要表现为协同效应。包括 JNJ-64619178 + Selinexor、JNJ-64619178 + SNDX-5613 以及 Palbociclib + Selinexor 在内的双重组合方案均表现出强烈且一致的协同效应；此外，JQ1 + Olaparib + MSA2 和 JNJ-64619178 + SNDX-5613 + Selinexor 的三重组合方案也表现出协同效应。相比之下，KG-1a 细胞则表现出高度依赖环境的反应，其中存在协同与拮抗的混合现象。
虽然帕博西利 + 塞利内索和维内托克拉克斯 + 匹莫司他表现出强烈的协同效应，但 JNJ-64619178 + 塞利内索的组合在较低效应水平下存在拮抗作用，而在最高效应水平下则转变为协同效应。值得注意的是，JNJ-64619178 + SNDX-5613 + 塞利内索的三重组合情况也是如此


### 原文第 85 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=85)

### co-scientist-0511

**English original**

synergistic, the JQ1 + Olaparib + MSA2 combination was predominantly antagonistic in this cell line. A complete summary of these findings is tabulated in Extended Data Table 2.

**中文译文 · 机器初译**

协同作用下，JQ1 + 奥拉帕利 + MSA2组合在这类细胞系中主要表现为拮抗作用。这些发现的完整总结列于扩展数据表2中。

### co-scientist-0512

**English original**

These diverse interaction patterns heavily reflect the underlying molecular and cytogenetic profiles of the respective cell lines. Of note, KG-1a harbors mutant TP53, a complex karyotype with multiple chromosomal aberrations including del(7q) and various translocations, and enrichment for CD34+CD38− leukemic stem-like cells with inherent chemoresistance characteristics. Clinically, this cell-line represents a less differentiated, more resistant AML subtype that models the molecular heterogeneity with impaired apoptotic pathways and resistance to standard chemotherapeutic agents. The drug interaction and synergy patterns observed in KG-1a cells, including emergence of antagonism for several combinations, likely reflect the TP53-mutant phenotype, as TP53 mutations are associated with abysmal survival outcomes and poor response to standard-of-care chemotherapy in AML. The lack of Binimetinib response in NOMO-1 warrants further investigation, though we postulate this may reflect pathway redundancy and compensatory signaling mechanisms common in KMT2A-rearranged AML. Studies show that MEK inhibition in these cells often triggers sustained activation of parallel survival pathways 16, particularly PI3K/AKT/mTOR signaling, which enables cells to bypass MAPK pathway blockade. This is consistent with broader findings that MEK inhibitors demonstrate limited single-agent efficacy in KMT2A-rearranged AML and require combination with other targeted agents, such as menin inhibitors, to achieve meaningful anti-leukemic effects 17 .

**中文译文 · 机器初译**

这些不同的相互作用模式充分反映了各细胞系的潜在分子与细胞遗传学特征。值得注意的是，KG-1a细胞携带突变的TP53基因，具有复杂的核型，包含多种染色体异常，如del(7q)及各种易位现象，并且富含具有固有化疗耐药特性的CD34+CD38−白血病干细胞。从临床角度来看，这种细胞系属于分化程度较低、耐药性较强的AML亚型，能够模拟凋亡途径受损及对常规化疗药物抵抗的分子异质性。
在 KG-1a 细胞中观察到的药物相互作用与协同作用模式，包括多种组合下的拮抗现象，很可能反映了 TP53 突变表型；因为 TP53 突变与 AML 中极差的生存结果以及对常规化疗的不良反应有关。NOMO-1 患者中缺乏 Binimetinib 的疗效需要进一步研究，不过我们认为这可能反映了 KMT2A 重排 AML 中常见的通路冗余及补偿性信号传导机制。
研究表明，在这些细胞中抑制 MEK 通常会引发并行生存途径的持续激活，尤其是 PI3K/AKT/mTOR 信号通路，从而使细胞能够绕过 MAPK 通路的阻断。这与更广泛的研究结果一致，即 MEK 抑制剂在 KMT2A 重排型急性髓系白血病中单用时的疗效有限，需要与其他靶向药物（如 menin 抑制剂）联合使用，才能产生显著的抗白血病效果。

### co-scientist-0513

**English original**

We evaluated single-agent efficacy for a broader panel of Co-Scientist proposed drugs against MOLM-13 and KG-1a AML cell lines. Cells were treated and incubated for 72 to 96 hours before viability measurement and IC50 determination. The full results of the single-agent efficacy are listed in Extended Data Table 1. Finally, the overall summary of the drug combination experiments of synergy is in Extended Data Table 2.

**中文译文 · 机器初译**

我们评估了多种智能体对 MOLM-13 和 KG-1a 急性髓系白血病细胞系的联合科学家推荐药物的单一智能体疗效。在测量细胞存活率和确定 IC50 值之前，这些细胞经过处理并培养 72 至 96 小时。单一智能体疗效的全部结果列于扩展数据表 1 中。最后，药物组合实验的协同作用总体总结则见于扩展数据表 2。

### co-scientist-0514

**English original**

5.6 Clinical variable analysis guideline for AML drug repurposing

**中文译文 · 机器初译**

5.6 急性髓系白血病药物重新应用的临床变量分析指南

### co-scientist-0515

**English original**

The structured framework below outlines six key evaluation domains for assessing repurposed drugs in AML treatment.

**中文译文 · 机器初译**

下面的结构化框架列出了评估AML治疗中重新使用的药物的六个关键评价领域。

### co-scientist-0516

**English original**

1.​ Patient-specific clinical and demographic variables: A patient’s individual characteristics are crucial in determining their ability to tolerate different treatment regimens. ●​ Age: A crucial prognostic indicator that significantly impacts treatment tolerance and survival outcomes. Treatment intensity should be calibrated across age groups: Younger patients (typically <60 years) are generally candidates for intensive chemotherapy regimens and multi-drug combinations (doublets or triplets). Patients aged 60-75 years require careful assessment for intensive versus non-intensive approaches based on individual fitness and comorbidity profile.

**中文译文 · 机器初译**

1. 患者特定的临床及人口统计变量：患者的个体特征对于判断其能否耐受不同治疗方案至关重要。● 年龄：这是一个重要的预后指标，对治疗耐受性和生存结果有显著影响。治疗强度应根据年龄组进行调整：年轻患者（通常<60岁）通常适合接受强化化疗方案及多药组合治疗（双药或三药方案）。60-75岁的患者则需要根据个体健康状况和合并症情况，仔细评估是否适合采用强化治疗或非强化治疗方式。

### co-scientist-0517

**English original**

Intensive chemotherapy should not be offered to patients over 75 years due to

**中文译文 · 机器初译**

对于75岁以上的患者不应提供强化化疗治疗


### 原文第 86 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=86)

### co-scientist-0519

**English original**

elevated treatment-related mortality risk. Non-intensive regimens or single-agent therapies are more appropriate alternatives. When evaluating a repurposed drug candidate, analyze any available safety data and comment on the specific age groups where the drug would be most beneficial. Explain your age-based recommendations considering the drug’s specific properties and how they align with the tolerability and treatment goals across different age groups. ●​ Performance status (e.g., ECOG score): Treatment selection should be stratified as follows: Patients with excellent to good performance status (ECOG 0-1) are optimal candidates for intensive therapies including combination regimens; patients with moderate performance status (ECOG 2) may receive intensive therapies with careful monitoring or moderate-intensity approaches; patients with poor performance status (ECOG 3) should receive less intensive single-agent therapies or supportive care measures; and patients with very poor performance status (ECOG 4) require palliative care approaches only. When evaluating a repurposed drug candidate, analyze any available safety data to determine the appropriate ECOG performance status range for safe administration. Consider the drug and explain which ECOG levels would be most suitable, particularly when evaluating combination regimens that require better functional status for tolerability. ●​ Comorbidities (e.g., Charlson Comorbidity Index): Concurrent medical conditions, quantified through validated tools like the Charlson Comorbidity Index (CCI), fundamentally influence treatment selection and prognosis. Treatment recommendations should be stratified by comorbidity burden: Patients with low CCI scores (0-2) can generally tolerate standard to intensive regimens; moderate CCI scores (3-4) warrant dose modifications or alternative approaches; and high CCI scores (≥ 5) typically require reduced-intensity or supportive care strategies. When evaluating repurposed drug candidates, comment on specific contraindications and dose adjustments required for major comorbidities including cardiovascular disease (heart failure, coronary artery disease), renal insufficiency, hepatic dysfunction, pulmonary disease, diabetes mellitus, and prior malignancies. Comment on how the drug’s safety profile aligns with common AML patient comorbidities and specify any absolute contraindications or necessary monitoring requirements. ●​ Prior treatment history: Consider three main categories: treatment-naive patients (generally better response rates), patients with antecedent hematological disorders like myelodysplastic syndromes or myeloproliferative neoplasms who received prior treatments and developed therapy-related AML, and patients with prior chemotherapy or radiation for other malignancies who have cumulative toxicity constraints. When evaluating repurposed drug candidates, assess the drug’s efficacy in treatment-naive versus relapsed/refractory populations, identify

**中文译文 · 机器初译**

升高的治疗相关死亡风险。非强化治疗方案或单一药物疗法更为合适的替代方案。在评估重新使用的药物候选物时，需分析所有可用的安全数据，并针对该药物最具有益的具体年龄组发表意见。
阐述基于年龄的推荐方案，需考虑该药物的特定特性，以及这些特性如何与不同年龄段的耐受性和治疗目标相契合。● 体能状态（例如ECOG评分）：治疗选择应按以下方式分层：体能状态良好至良好的患者（ECOG 0-1）是强化疗法及联合治疗方案的最佳候选者；体能状态中等的患者（ECOG 2）可接受严格监测下的强化疗法或中等强度治疗方案；体能状态较差的患者（ECOG 3）应接受强度较低的单一药物疗法或支持性护理措施；而体能状态极差的患者（ECOG 4）则不应接受任何强化疗法。
表现不佳的状态（ECOG 4级）仅需要姑息性治疗方案。在评估重新使用的药物候选物时，需分析所有可用的安全数据，以确定安全用药所对应的合适的ECOG状态范围。考虑该药物的特点，并说明哪些ECOG级别最为适宜，尤其是在评估需要更好功能状态以确保耐受性的联合治疗方案时。●​ 合并症（例如Charlson合并症指数）：通过Charlson合并症指数等经过验证的工具量化的同时存在的疾病状况，对治疗选择与预后有着根本性的影响。
治疗建议应根据合并症负担进行分层：CCI评分较低（0-2）的患者通常可以耐受常规或强化治疗方案；CCI评分中等（3-4）的患者需要调整剂量或采用替代疗法；CCI评分高（≥5）的患者通常需要低强度或支持性护理策略。在评估重新使用的药物候选物时，应针对包括心血管疾病（心力衰竭、冠状动脉疾病）、肾功能不全、肝功能障碍、肺部疾病、糖尿病以及既往恶性肿瘤等主要合并症所涉及的特定禁忌症及所需剂量调整进行说明。
对该药物的安全性特征如何与常见的急性髓系白血病患者合并疾病相契合进行评论，并明确任何绝对禁忌症或必要的监测要求。●​ 既往治疗史：可分为三大类：未接受治疗的患者（通常疗效较好）、曾患有骨髓增生异常综合征或骨髓增殖性肿瘤等血液系统疾病且已接受过治疗并出现治疗相关急性髓系白血病的患者，以及因其他恶性肿瘤接受过化疗或放疗且存在累积毒性限制的患者。
在评估重新使用的药物候选物时，需评估该药物在未接受过治疗的人群与复发/难治性患者群体中的疗效，并找出


### 原文第 87 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=87)

### co-scientist-0521

**English original**

potential cross-resistance with prior therapies, evaluate cumulative dose limitations (particularly for agents like anthracyclines with lifetime dose caps), and consider contraindications based on germline predispositions or hereditary cancer syndromes. Comment on whether the repurposed drug offers advantages in overcoming resistance mechanisms associated with specific prior treatments. 2.​ AML risk stratification based on molecular and cytogenetic profile (ELN 2022 and ELN 2024): AML risk stratification guides treatment decisions through molecular and cytogenetic profiling. The ELN 2022 guidelines stratify patients eligible for intensive chemotherapy, while ELN 2024 guidelines address older patients unfit for intensive treatment. ●​ ELN 2022 risk categories (intensive treatment eligible) ○​ Favorable-risk ■​ t(8;21) RUNX1::RUNX1T1 (note: KIT mutations worsen prognosis) ■​ inv(16)/t(16;16) CBFB::MYH11 (good initial response, relapse risk exists) ■​ NPM1 mutation without FLT3-ITD ■​ In-frame bZIP CEBPA mutations (biallelic) ○​ Intermediate-risk ■​ NPM1 mutation with FLT3-ITD ■​ Wild-type NPM1 with FLT3-ITD ■​ t(9;11) MLLT3::KMT2A ○​ Adverse-risk ■​ inv(3)/t(3;3) involving GATA2, MECOM(EVI1) ■​ Complex karyotype (≥ 3 unrelated abnormalities) ■​ Monosomal karyotype ■​ Myelodysplasia-related gene mutations (ASXL1, BCOR, EZH2, RUNX1, SF3B1, SRSF2, STAG2, U2AF1, ZRSR2) ■​ TP53 mutations (associated with therapy resistance and poor survival) ●​ ELN 2024 risk categories (non-intensive treatment) ○​ Favorable-risk: IDH1 mutations (TP53 wild-type), IDH2 mutations (FLT3-ITD negative, KRAS/NRAS wild-type, TP53 wild-type), NPM1 mutations (FLT3-ITD negative, KRAS/NRAS wild-type, TP53 wild-type), DDX41 mutations, other cytogenetic abnormalities if FLT3-ITD negative, KRAS/NRAS wild-type, TP53 wild-type ○​ Adverse-risk: TP53 mutations ○​ Intermediate-risk: All others not classified as favorable or adverse ●​ When evaluating repurposed drug candidates, consider the drug’s mechanism of action and existing efficacy data to comment on its potential effectiveness across

**中文译文 · 机器初译**

可能与现有疗法产生交叉耐药性，需评估累积剂量限制问题（尤其是像蒽环类药物那样存在终生剂量上限的药品），并考虑基于生殖系易感性或遗传性癌症综合征的禁忌情况。讨论重新使用的药物在克服与特定既往治疗相关的耐药机制方面是否具有优势。2. 基于分子及细胞遗传学特征对AML风险进行分层（ELN 2022和ELN 2024）：AML风险分层通过分子及细胞遗传学分析指导治疗决策。
ELN 2022指南对适合接受强化化疗的患者进行了分层，而ELN 2024指南则针对不适合接受强化治疗的老龄患者进行了处理。●​ ELN 2022风险类别（适合强化治疗） ○​ 有利风险 ■​ t(8;21) RUNX1::RUNX1T1（注意：KIT突变会恶化预后）■​ inv(16)/t(16;16) CBFB::MYH11（初始反应良好，存在复发风险）■​ 无FLT3-ITD的NPM1突变 ■​ 框内bZIP CEBPA突变（二价突变）○​ 中等风险 ■​ 有FLT3-ITD的NPM1突变 ■​ FLT3-ITD伴随野生型NPM1 ■​ t(9;11) MLLT3::KMT2A○​ 不利风险 ■​ 涉及GATA2、MECOM(EVI1)的inv(3)/t(3;3) ■​ 复杂核型（≥3个无关异常）■​ 单倍体核型
■​ 骨髓发育不良相关基因突变（ASXL1、BCOR、EZH2、RUNX1、SF3B1、SRSF2、STAG2、U2AF1、ZRSR2）■​ TP53突变（与治疗耐药和生存不良相关）●​ ELN 2024风险分类（非强化治疗）○​ 有利风险：IDH1突变（TP53野生型）、IDH2突变（FLT3-ITD阴性、KRAS/NRAS野生型、TP53野生型）、NPM1突变（FLT3-ITD阴性、KRAS/NRAS野生型、TP53野生型）、DDX41突变，以及FLT3-ITD阴性、KRAS/NRAS野生型、TP53野生型时的其他细胞遗传学异常○​ 不利风险：TP53突变○​ 中等风险：所有未被归类为有利或不利的病例●​ 在评估重新使用的药物候选物时，需考虑上述因素
药物的作用机制及现有疗效数据，以评估其潜在有效性


### 原文第 88 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=88)

### co-scientist-0523

**English original**

these risk categories. Identify specific molecular targets the drug may address and explain whether the drug shows preferential activity against particular mutations or cytogenetic abnormalities. Consider if the drug could overcome resistance mechanisms associated with adverse-risk features, particularly TP53 mutations, complex karyotypes, or myelodysplasia-related gene mutations. Consider how risk stratification should influence patient selection and dosing strategies for the repurposed drug. 3.​ Preclinical cell line testing: Effective preclinical evaluation requires strategic cell line selection to assess drug efficacy across AML's molecular diversity. ●​ Cell line selection for testing. Select appropriate AML cell lines based on the drug’s mechanism of action and target molecular features. Consider representative cell lines from major risk categories: ○​ Favorable-risk models: HL-60 (promyelocytic), Kasumi-1 (t(8;21)), ME-1 (inv(16)) ○​ Intermediate-risk models: MOLM-13 (FLT3-ITD, NPM1 mutation), OCI-AML3 (NPM1 mutation) ○​ Adverse-risk models: KG-1a (TP53 mutation), SKM-1 (complex karyotype) ●​ Basic efficacy assays ○​ Cell viability assays (MTT, CellTiter-Glo): Determine IC50/EC50 values ○​ Apoptosis assays (Annexin V/PI): Assess cell death mechanisms ○​ Combination studies: Test synergy with standard AML drugs (cytarabine, anthracyclines, venetoclax) ●​ Primary sample validation: Plan for ex vivo testing on primary AML samples with known molecular profiles to validate cell line findings. ●​ When evaluating a repurposed drug candidate, recommend specific cell lines for testing based on the drug’s mechanism of action and molecular targets. Justify cell line selections by explaining how their molecular characteristics (mutations, translocations, risk category) align with the drug’s expected activity. Consider which assays would be most informative for demonstrating the drug’s efficacy and whether specific molecular subtypes might show enhanced sensitivity. 4.​ Off-target effects and safety profile: Repurposed drugs have existing safety data that must be evaluated in the AML context to identify beneficial or harmful off-target effects. ●​ Known safety profile analysis ○​ Existing adverse events: Review the drug’s known side effect profile from its original indication ○​ Hematologic toxicity: Assess impact on normal blood cell production and bone marrow function ○​ Organ-specific toxicity: Evaluate liver, kidney, cardiac, and neurologic effects

**中文译文 · 机器初译**

这些风险类别。确定药物可能针对的具体分子靶点，并说明该药物是否对特定突变或细胞遗传学异常具有优先作用。考虑该药物能否克服与不良风险特征相关的耐药机制，尤其是 TP53 突变、复杂核型或骨髓增生异常相关基因突变。思考风险分层应如何影响该重新使用的药物的患者选择及用药方案。3. 临床前细胞系测试：有效的临床前评估需要合理的细胞系选择，以评估药物在急性髓系白血病不同分子类型中的疗效。● 用于测试的细胞系选择。
根据药物的作用机制及目标分子特征，选择合适的大语言模型细胞系。
考虑来自主要风险类别的代表性细胞系：○​ 有利风险模型：HL-60（ promyelocytic 细胞）、Kasumi-1（t(8;21) 突变）、ME-1（inv(16) 突变） ○​ 中等风险模型：MOLM-13（FLT3-ITD、NPM1 突变）、OCI-AML3（NPM1 突变） ○​ 不利风险模型：KG-1a（TP53 突变）、SKM-1（复杂核型） ●​ 基础疗效检测 ○​ 细胞存活率检测（MTT、CellTiter-Glo）：测定 IC50/EC50 值 ○​ 凋亡检测（Annexin V/PI）：评估细胞死亡机制 ○​ 联合研究：测试与标准 AML 药物（胞苷、蒽环类、维内妥克）的协同作用 ●​ 原始样本验证：针对具有已知分子特征的原始 AML 样本进行外源性实验验证
实验样本结果。● 在评估重新使用的药物候选物时，应根据药物的作用机制和分子靶点，推荐特定的细胞系用于测试。需通过说明这些细胞系的分子特征（突变、基因重排、风险类别）如何与药物预期效果相契合，来论证选择该细胞系的理由。同时需考虑哪些检测方法最能有效证明药物的疗效，以及是否某些特定的分子亚型可能具有更高的敏感性。
4. 脱靶效应与安全性特征：重新使用的药物具有现有的安全性数据，必须在大语言模型背景下进行评估，以识别有益的或有害的脱靶效应。● 已知的安全性特征分析 ○ 现有不良事件：回顾该药物在原始适应症下的已知副作用情况 ○ 血液系统毒性：评估对正常血细胞生成和骨髓功能的影响 ○ 器官特异性毒性：评估肝脏、肾脏、心脏和神经系统的影响


### 原文第 89 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=89)

### co-scientist-0525

**English original**

○​ Drug interactions: Consider interactions with standard AML medications ●​ Off-target effect evaluation ○​ Beneficial off-targets: Identify secondary mechanisms that could enhance anti-leukemic activity ○​ Harmful off-targets (anti-targets): Recognize interactions that could cause toxicity or interfere with treatment ○​ Hematopoietic stem cell toxicity: Assess potential damage to the bone marrow and hematopoietic precursors ●​ Safety monitoring requirements ○​ Laboratory monitoring: Determine necessary blood tests and organ function assessments ○​ Dose modifications: Consider if AML patients require different dosing than the original indication ○​ Contraindications: Identify patient populations who should avoid the drug ●​ When evaluating a repurposed drug candidate, analyze the drug’s known safety profile from its original therapeutic use and comment on how these effects translate to AML patients. Identify potential off-target effects that could be beneficial (additional anti-cancer mechanisms) or harmful (anti-targets causing toxicity). Recommend safety monitoring strategies specific to AML treatment.

**中文译文 · 机器初译**

○​ 药物相互作用：考虑与常规AML药物之间的相互作用 ●​ 靶外效应评估 ○​ 有益的靶外效应：识别可能增强抗白血病活性的次要机制 ○​ 有害的靶外效应（抗目标）：识别可能导致毒性或干扰治疗的相互作用 ○​ 造血干细胞毒性：评估对骨髓和造血前体的潜在损害 ●​ 安全监测要求 ○​ 实验室监测：确定必要的血液检查和器官功能评估 ○​ 剂量调整：考虑AML患者是否需要与原有适应症不同的剂量 ○​ 禁忌症：识别患者
应避免使用该药物的群体 ●​ 在评估重新使用的药物候选物时，需分析该药物在原始治疗应用中的已知安全性特征，并评论这些效应如何适用于AML患者。识别可能具有益处（额外的抗癌机制）或有害（导致毒性的抗靶点）的潜在非靶标效应。提出针对AML治疗的安全监测策略。

### co-scientist-0526

**English original**

Consider whether the drug's side effect profile is acceptable given AML’s poor prognosis and existing treatment toxicities. 5.​ Pharmacokinetic and pharmacodynamic (PK/PD) variables: Repurposed drugs have established PK/PD data that must be evaluated for AML application to ensure effective and safe dosing. ●​ Plasma concentration and dosing ○​ Achievable concentrations: Compare effective in vitro concentrations (IC50/EC50) with known achievable plasma levels from the original indication ○​ Dose requirements: Assess if standard dosing from the original indication provides adequate drug exposure for anti-leukemic activity ○​ Formulation considerations: Evaluate if route of administration (oral vs.

**中文译文 · 机器初译**

考虑到AML的预后不良及现有治疗副作用，需考虑该药物的副作用情况是否可接受。
5. 药代动力学与药效学变量：重新使用的药物具有成熟的药代动力学与药效学数据，必须对其进行评估，以确保其在AML中的应用能够实现有效且安全的用药剂量。● 血浆浓度与给药方式 ○ 可达到的浓度：将体外有效浓度（IC50/EC50）与原始适应症下已知的血浆可达到水平进行对比 ○ 剂量要求：评估基于原始适应症的常规剂量是否能够提供足够的药物暴露以发挥抗白血病作用 ○ 制剂相关因素：分析给药途径（口服 vs.

### co-scientist-0527

**English original**

IV) is appropriate for AML patients ●​ Drug metabolism and interactions ○​ Metabolic pathways: Review primary elimination routes (hepatic, renal, other) ○​ CYP interactions: Critical consideration given AML patients frequently receive antifungal medications (strong CYP inhibitors like posaconazole, voriconazole) ○​ Supportive care interactions: Assess interactions with antibiotics, antiemetics, and other supportive medications

**中文译文 · 机器初译**

IV) 适用于AML患者 ●​ 药物代谢与相互作用 ○​ 代谢途径：回顾主要排泄途径（肝脏、肾脏及其他） ○​ CYP相互作用：对于经常接受抗真菌药物的AML患者，需特别考虑（如强CYP抑制剂如泊沙可诺唑、伏立康唑） ○​ 支持性治疗相互作用：评估与抗生素、止吐药及其他支持性药物的相互作用


### 原文第 90 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=90)

### co-scientist-0529

**English original**

●​ Response monitoring ○​ Target engagement biomarkers: Identify measurable indicators that the drug is affecting its intended target ○​ Efficacy biomarkers: Determine laboratory or molecular markers to assess treatment response ○​ Safety biomarkers: Establish monitoring parameters for early toxicity detection ●​ When evaluating a repurposed drug candidate, consider whether the drug’s established dosing regimen can achieve effective anti-leukemic concentrations based on in vitro data. Comment on potential drug interactions, particularly with antifungal medications commonly used in AML patients. Identify existing biomarkers that could monitor drug activity and treatment response, or propose new biomarkers if none exist.

**中文译文 · 机器初译**

●​ 响应监测 ○​ 目标参与指标：识别能够反映药物对其预期靶标产生影响的可测量指标 ○​ 疗效指标：确定用于评估治疗反应的实验室或分子标志物 ○​ 安全性指标：建立早期毒性检测的监测参数 ●​ 在评估重新使用的药物候选物时，需考虑基于体外数据，该药物的既定给药方案是否能够达到有效的抗白血病浓度。同时需关注潜在的药物相互作用，尤其是与AML患者常用的抗真菌药物之间的相互作用。
识别现有的生物标志物，以监测药物作用及治疗反应，或在不存在此类标志物时提出新的生物标志物。

### co-scientist-0530

**English original**

Case Study: Application of the Clinical Variable Framework to Binimetinib. To demonstrate the utility and instruction-following capability of the structured evaluation framework detailed above, we present Co-Scientist’s translational analysis for the repurposed candidate, Binimetinib.

**中文译文 · 机器初译**

案例研究：临床变量框架在 Binimetinib 中的应用。为了证明上述结构化评估框架的实用性和遵循指令的能力，我们展示了 Co-Scientist 对重新使用的候选药物 Binimetinib 的转化分析。

### co-scientist-0531

**English original**

When applied to Binimetinib, this analysis yielded a specific unmet-need clinical context: Older or frail patients with relapsed or venetoclax-resistant AML (aligning with Point 1: Patient-specific clinical and demographic variables).

**中文译文 · 机器初译**

应用于比尼米特替尼时，该分析得出了一种特定的未满足临床需求情况：年龄较大或身体虚弱的复发或维奈托克抗性AML患者（与第1点：患者特定的临床及人口统计变量相符合）。

### co-scientist-0532

**English original**

Specifically addressing the pharmacokinetic parameters and drug interactions (Point 5), Co-Scientist identified Binimetinib’s UGT1A1-mediated metabolism as a meaningful advantage, noting that it circumvents the CYP3A4-dependent drug-drug interactions that commonly limit therapeutic options in patients receiving azole antifungals. It then linked this favorable pharmacokinetic profile to a well-recognized challenge in managing venetoclax-resistant disease, where MAPK-pathway activation and polypharmacy frequently constrain combination therapy. This synthesis of pharmacokinetic, molecular, and clinical considerations supported the conclusion that Binimetinib could be particularly well suited for frail or heavily pretreated patients, especially in contexts where CYP3A4 inhibition limits the feasibility of other targeted regimens.

**中文译文 · 机器初译**

关于药代动力学参数和药物相互作用的具体讨论（第5点），联合科学家指出Binimetinib通过UGT1A1进行代谢具有显著优势，因为这一机制可以规避CYP3A4依赖性的药物间相互作用，而后者通常会限制接受唑类抗真菌药患者的治疗选择。随后，他们将这种有利的药代动力学特征与处理venetoclax耐药疾病时一个众所周知的挑战联系起来——即MAPK通路激活和多种药物使用常常使得联合治疗变得困难。
对药代动力学、分子学和临床因素的综合分析表明，Binimetinib特别适合用于体弱或已接受大量治疗的患者，尤其是在CYP3A4被抑制导致其他靶向治疗方案难以实施的情况下。


### 原文第 91 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=91)

### co-scientist-0534

**English original**

6 Detailed Co-Scientist output for a validated AML repurposing candidate

**中文译文 · 机器初译**

6 针对经过验证的大语言模型重新应用候选方案的详细合作科学家输出内容

### co-scientist-0535

**English original**

KIRA6 for AML

**中文译文 · 机器初译**

KIRA6 用于 AML 任务

### co-scientist-0536

**English original**

Summary This proposal outlines repurposing KIRA6, an IRE1α inhibitor, for treating acute myeloid leukemia (AML), particularly FLT3-ITD positive AML known for high relapse rates. The hypothesis is that KIRA6 will disrupt protein homeostasis and induce ER stress in AML cells, synergizing with existing therapies and overcoming resistance. The proposal details KIRA6's mechanism, impacting pathways like the UPR and apoptosis, and suggests a comprehensive experimental plan including in vitro and in vivo studies to validate its efficacy and safety, including combination therapy with existing AML drugs. This approach aims to provide a novel, effective treatment strategy for AML patients, particularly those with the challenging FLT3-ITD mutation and other drug resistance phenotypes.

**中文译文 · 机器初译**

摘要 本提案提出将 KIRA6（一种 IRE1α 抑制剂）重新用于治疗急性髓系白血病（AML），尤其是复发率较高的 FLT3-ITD 阳性 AML。假设是 KIRA6 会破坏 AML 细胞的蛋白质稳态并引发内质网应激，与现有疗法协同作用以克服耐药性。提案详细阐述了 KIRA6 的作用机制，涉及 UPR 和细胞凋亡等通路，并提出了全面的实验计划，包括体外和体内研究，以验证其疗效和安全性，包括与现有 AML 药物联合使用。
该方法旨在为 AML 患者提供一种新颖且有效的治疗策略，尤其适用于那些具有复杂的 FLT3-ITD 突变及其他药物耐药表型的患者。

### co-scientist-0537

**English original**

Hypothesis

**中文译文 · 机器初译**

假设

### co-scientist-0538

**English original**

Introduction Acute myeloid leukemia (AML) remains a formidable hematological malignancy characterized by the rapid proliferation of immature myeloid blasts in the bone marrow and peripheral blood. Despite advancements in therapeutic strategies, including targeted therapies and hematopoietic stem cell transplantation, a significant proportion of patients experience relapse or develop resistance to treatment, underscoring the urgent need for new therapeutic interventions. The heterogeneous nature of AML, with diverse genetic and molecular aberrations driving disease progression, necessitates the exploration of novel therapeutic targets and the rational design of combination therapies to overcome treatment resistance and improve long-term survival outcomes. Drug repurposing, which involves identifying new uses for existing drugs, offers a cost-effective and efficient strategy to accelerate the development of novel AML treatments by leveraging established safety profiles and pharmacokinetic data. This approach can significantly reduce development time and costs, facilitating the rapid translation of promising agents to clinical trials.

**中文译文 · 机器初译**

引言 急性髓系白血病（AML）是一种严重的血液系统恶性肿瘤，其特征是骨髓和外周血中的未成熟髓系原始细胞迅速增殖。尽管治疗策略取得了进展，包括靶向治疗和造血干细胞移植，但仍有相当比例的患者出现复发或对治疗产生耐药性，这凸显了开发新治疗干预措施的紧迫性。
大语言模型的多样性特征以及多种遗传和分子异常对疾病进展的驱动作用，促使人们探索新的治疗靶点，并合理设计联合疗法以克服治疗耐药性并改善长期生存效果。药物再利用策略通过为现有药物寻找新用途，利用已验证的安全性与药代动力学数据，提供了一种经济高效的方法，有助于加速新型AML治疗药物的研发。这种方式可显著缩短研发周期和成本，促进有前景的药物迅速进入临床试验阶段。

### co-scientist-0539

**English original**

Recent findings and related research Recent research has significantly advanced our understanding of the complex molecular landscape of AML, highlighting the critical roles of various genetic mutations and signaling pathways in leukemogenesis. Recurrent mutations in genes such as FLT3, NPM1, IDH1/2, and TP53 are frequently observed in AML and have been implicated in disease initiation, progression, and treatment resistance. The FLT3-ITD mutation, a particularly challenging subtype, is associated with poor prognosis and a higher risk of relapse, emphasizing the need for effective therapies that target this specific mutation or overcome its downstream effects. Targeted

**中文译文 · 机器初译**

近期研究进展及相关研究 近期研究显著深化了我们对AML复杂分子机制的理解，揭示了各种基因突变与信号通路在白血病发生中的关键作用。FLT3、NPM1、IDH1/2和TP53等基因的反复突变在AML中十分常见，与疾病发生、进展及治疗抵抗密切相关。FLT3-ITD突变是一种特别具有挑战性的亚型，与不良预后和更高的复发风险相关，这凸显了需要针对该特定突变或克服其下游效应的高效疗法。


### 原文第 92 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=92)

### co-scientist-0541

**English original**

therapies, such as FLT3 inhibitors (midostaurin, gilteritinib), IDH inhibitors (enasidenib, ivosidenib), and the BCL-2 inhibitor venetoclax, have demonstrated clinical efficacy in specific AML subtypes; however, the emergence of drug resistance and the lack of effective treatments for high-risk patients remain critical challenges.

**中文译文 · 机器初译**

诸如 FLT3抑制剂（米多斯塔林、吉尔替替尼）、IDH抑制剂（恩赛迪尼布、伊沃西迪尼布）以及 BCL-2 抑制剂维内妥克等疗法已在特定急性髓系白血病亚型中显示出临床疗效；然而，药物耐药性的出现以及高风险患者缺乏有效治疗方案，仍是亟待解决的难题。

### co-scientist-0542

**English original**

Drug repurposing has yielded several promising candidates for AML treatment, including: ●​ Arsenic trioxide and all-trans retinoic acid (ATRA): Established treatments for acute promyelocytic leukemia (APL), these have also shown potential in combination therapy for non-APL AML. ●​ Histone deacetylase (HDAC) inhibitors: Vorinostat and panobinostat have shown modest activity in AML, particularly in combination with other agents, but are known to be poorly tolerated and have limited efficacy as single agents. ●​ Proteasome inhibitors: Bortezomib and carfilzomib have been explored in combination regimens in AML, especially to overcome resistance, though with limited success. ●​ Metabolic inhibitors: Targeting glutamine metabolism and other metabolic pathways has shown promise in preclinical studies, though with limited translation due to toxicity and poor absorption. ●​ Homoharringtonine (HHT): As noted, HHT, a protein synthesis inhibitor, has been approved for CML and has shown promise in AML, although its mechanism of action and specific impacts on resistance mechanisms need to be further explored. ●​ Immunomodulatory drugs: Thalidomide and lenalidomide have been explored in combination therapies to target the tumor microenvironment and enhance immune responses, though with limited efficacy in AML. ●​ Kinase inhibitors: Beyond FLT3, new kinase inhibitors that target other pathways are being explored in combination settings to overcome resistance.

**中文译文 · 机器初译**

药物重新应用为AML治疗提供了多个有前景的候选方案，包括：● 三氧化二砷和全反式维甲酸：这些疗法已被证实可用于急性早幼粒细胞白血病，在非APL AML的联合治疗中也有潜力。● 组蛋白去乙酰化酶抑制剂：伏立诺司特和帕诺比诺司特在AML中表现出一定的疗效，尤其是与其他药物联合使用时，但耐受性较差且单独使用效果有限。● 蛋白酶体抑制剂：硼替佐米和卡非佐米被用于AML的联合治疗方案中，尤其用于克服耐药性，但成效有限。● 代谢
抑制剂：针对谷氨酰胺代谢及其他代谢途径的研究在临床前研究中显示出希望，但由于毒性及吸收不良问题，其应用有限。●​ 异长春碱（HHT）：如前所述，作为蛋白质合成抑制剂的异长春碱已被批准用于慢性髓性白血病，并在急性髓性白血病中表现出良好效果，但其作用机制及对抗药性的具体影响仍需进一步研究。●​ 免疫调节药物：沙利度胺和来那度胺被探索用于联合疗法，以靶向肿瘤微环境并增强免疫反应，但在急性髓性白血病中的疗效有限。●​ 激酶抑制剂：除了FLT3，针对其他靶点的新型激酶抑制剂也正在研究中。
正在探索组合环境下的路径，以克服阻力。

### co-scientist-0543

**English original**

Despite these findings, there remains a significant unmet need for novel, effective therapies that can overcome drug resistance, target novel pathways, and improve long-term survival for AML patients.

**中文译文 · 机器初译**

尽管有这些发现，对于能够克服药物耐药性、针对新通路并提升急性髓系白血病患者长期生存率的新型有效疗法，仍然存在巨大的需求未满足。

### co-scientist-0544

**English original**

Areas worth exploring Several areas hold significant potential for identifying novel or repurposed drugs for AML treatment: ●​ Targeting non-canonical signaling pathways: Explore drugs that target pathways beyond the well-established ones, such as those involved in inflammatory signaling, protein degradation, and DNA damage repair. The interplay between the AML cell and its microenvironment, including inflammatory cytokines and immune cells, remains an area of active investigation and a promising target for therapeutic intervention. ●​ Targeting RNA processing and translation: Aberrant RNA processing and translation are significant drivers of protein expression in cancer, and are potential targets for novel

**中文译文 · 机器初译**

值得探索的领域 有几个领域在发现用于AML治疗的新药或重新利用的药品方面具有巨大潜力：● 针对非典型信号通路：探索那些作用于除已确立通路之外的路径的药物，例如与炎症信号传导、蛋白质降解和DNA损伤修复相关的通路。
大语言模型与其微环境之间的相互作用，包括炎症细胞因子和免疫细胞，仍是当前研究的热点领域，也是治疗干预的具有前景的目标。●​ 针对RNA加工与翻译：异常的RNA加工与翻译是癌症中蛋白质表达的重要驱动因素，也是新型治疗的潜在靶点


### 原文第 93 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=93)

### co-scientist-0546

**English original**

therapies. Targeting ribosome function, mRNA splicing, and RNA modifications can disrupt the production of key proteins required for cell survival and proliferation. ●​ Modulating immunometabolism: Cancer cells exhibit altered metabolic demands that influence the immune response, and targeting metabolic pathways that influence immune activation and suppression could enhance anti-leukemic immune responses. This also includes the metabolic dependencies of the myeloid microenvironment, which is critical for disease progression and resistance. ●​ Leveraging high-throughput screening (HTS) and computational biology: Combine in vitro or ex vivo screening of approved drugs with computational drug repurposing methods, particularly those that integrate multi-omics data, to identify novel drug candidates and potential synergistic drug combinations. ●​ Focus on drug combinations: Rational drug combinations that address both active malignancy and underlying resistance mechanisms, and can achieve effective treatment regimens at lower concentrations in combination, will have better safety, efficacy and overcome existing resistance. This should include a focus on sequential drug administration and drug scheduling. ●​ RNA-based therapies: Direct targeting of mRNAs coding for leukemia-driving proteins can be a very impactful strategy that also offers the chance to overcome resistance, for example by interfering with compensatory pathways. This includes RNA interference (RNAi), antisense oligonucleotides (ASOs), and mRNA-based therapies. ●​ Targeting protein homeostasis: Disrupting the protein homeostasis network, including protein folding, degradation (through ubiquitin-proteasome and autophagy pathways), and quality control mechanisms, can induce cellular stress and apoptosis in AML cells.

**中文译文 · 机器初译**

疗法。针对核糖体功能、mRNA剪接和RNA修饰，可以干扰细胞存活与增殖所需关键蛋白质的产生。● 调节免疫代谢：癌细胞表现出不同的代谢需求，这会影响免疫反应；针对影响免疫激活与抑制的代谢途径进行干预，可能增强抗白血病免疫反应。
这还包括髓系微环境的代谢依赖性，这对疾病进展和耐药性至关重要。●​ 利用高通量筛选和计算生物学技术：将获批药物的体外或离体筛选与计算药物重新应用方法相结合，尤其是那些整合多组学数据的方法，以识别新的药物候选物和潜在的协同用药组合。●​ 关注药物组合：能够同时针对活跃的恶性肿瘤和潜在的耐药机制，并在更低浓度下实现有效治疗方案的合理药物组合，将具有更好的安全性、有效性及疗效。
克服现有的耐药性。这应包括注重序贯用药及药物安排。● 基于 RNA 的疗法：直接靶向编码导致白血病相关蛋白的 mRNA，是一种非常有效的策略，同时也有机会克服耐药性，例如通过干扰补偿性通路实现。这包括 RNA 干扰（RNAi）、反义寡核苷酸（ASO）以及基于 mRNA 的疗法。● 针对蛋白质稳态调控：破坏蛋白质稳态网络，包括蛋白质折叠、降解（通过泛素-蛋白酶体和自噬途径）以及质量控制机制，可引发 AML 细胞的细胞应激和凋亡。

### co-scientist-0547

**English original**

Detailed novel likely correct idea: repurposing the IRE1α inhibitor KIRA6 for AML treatment

**中文译文 · 机器初译**

详细的新颖且正确的思路：将 IRE1α 抑制剂 KIRA6 重新用于 AML 治疗

### co-scientist-0548

**English original**

Goal: Repurpose KIRA6, an IRE1α inhibitor, for AML treatment, specifically targeting the MOLM-13 cell line with FLT3-ITD, with a focus on overcoming resistance mechanisms and enhancing combination therapy efficacy.

**中文译文 · 机器初译**

目标：将 IRE1α 抑制剂 KIRA6 用于 AML 治疗，专门针对携带 FLT3-ITD 的 MOLM-13 细胞系，重点克服耐药机制并提升联合治疗的疗效。

### co-scientist-0549

**English original**

Idea: KIRA6, by inhibiting IRE1α, a key regulator of the unfolded protein response (UPR), can disrupt protein homeostasis and induce ER stress in AML cells, particularly in cells exhibiting high metabolic demand and increased protein synthesis, such as FLT3-ITD positive cells. This disruption can synergize with other therapies, including FLT3 inhibitors and chemotherapeutics, to overcome resistance and improve therapeutic efficacy. KIRA6 will also suppress chronic inflammatory pathways known to promote cell survival in AML cells.

**中文译文 · 机器初译**

想法：KIRA6通过抑制IRE1α——未折叠蛋白反应的关键调节因子，能够破坏蛋白质稳态，引发AML细胞中的内质网应激，尤其是在具有高代谢需求且蛋白质合成增加的细胞中，例如FLT3-ITD阳性细胞。这种破坏作用可以与其他疗法协同作用，包括FLT3抑制剂和化疗药物，从而克服耐药性并提升治疗效果。KIRA6还能抑制那些促进AML细胞存活的慢性炎症通路。

### co-scientist-0550

**English original**

Molecular mechanism of action

**中文译文 · 机器初译**

作用机制


### 原文第 94 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=94)

### co-scientist-0552

**English original**

●​ Inhibition of IRE1α: KIRA6 is a selective inhibitor of IRE1α, a transmembrane protein in the endoplasmic reticulum (ER) that acts as a key sensor and transducer of ER stress. IRE1α activation initiates the unfolded protein response (UPR) pathway, which is a cellular stress response aimed at restoring protein homeostasis in the ER. Under conditions of increased protein synthesis or misfolded proteins, IRE1α is activated, leading to the splicing of XBP1 mRNA and the subsequent activation of downstream transcriptional targets involved in protein folding, trafficking, and degradation. ●​ Disruption of ER homeostasis: By inhibiting IRE1α, KIRA6 blocks the adaptive arm of the UPR, preventing the resolution of ER stress and leading to the accumulation of unfolded and misfolded proteins. This disruption creates a protein folding crisis, inducing ER stress and initiating apoptotic pathways. This effect is potentiated in rapidly proliferating AML cells, which have higher metabolic demands and are more sensitive to ER stress. ●​ Downstream effects: ○​ The accumulation of misfolded proteins leads to the activation of the PERK and ATF6 arms of the UPR, which further contribute to ER stress and apoptosis. ○​ Inhibition of IRE1α disrupts the transcriptional program regulated by XBP1, impairing the production of proteins involved in ER homeostasis and cell survival. ○​ The resulting ER stress induces the activation of the integrated stress response (ISR), leading to the translational suppression of many transcripts and increased apoptotic activity. ○​ KIRA6 can indirectly inhibit the NF-κB pathway by reducing ER stress and inflammatory cytokine production, reducing cell survival, proliferation and resistance. ○​ KIRA6 may directly reduce levels of inflammatory cytokines such as IL-1, in turn reducing secondary activation of inflammatory signalling cascades and reduce activation of IRAK1 in the process. ●​ Impact on FLT3-ITD: FLT3-ITD mutations lead to increased cell proliferation and metabolic demand and stress. KIRA6 can target this through disruption of the UPR, leading to a higher impact on FLT3-ITD cells. FLT3-ITD cells are under high levels of stress already, and require high levels of protein synthesis to maintain viability. By targeting basal or activated IRE1α, KIRA6 can induce significantly more cell death in FLT3-ITD cells than their wild-type counterparts. ●​ Impact on key dysregulated pathways: ○​ MYC: MYC protein levels are directly tied to mRNA translation and are necessary for cell survival and resistance in many cases, including leukemia.

**中文译文 · 机器初译**

●​ IRE1α的抑制：KIRA6是一种针对IRE1α的选择性抑制剂，IRE1α是内质网中的跨膜蛋白，作为内质网应激的关键传感器和转导器发挥作用。IRE1α的激活会触发未折叠蛋白反应（UPR）通路，这是一种细胞应激响应机制，旨在恢复内质网中的蛋白质稳态。
在蛋白质合成增加或蛋白质错误折叠的情况下，IRE1α会被激活，进而促使XBP1 mRNA的剪接发生，并进一步激活与蛋白质折叠、运输和降解相关的下游转录靶标。●​ 内质网稳态破坏：通过抑制IRE1α，KIRA6会阻断UPR的适应性反应环节，导致内质网应激无法缓解，进而使未折叠和错误折叠的蛋白质积累。这种破坏会引发蛋白质折叠危机，导致内质网应激，并启动细胞凋亡途径。
这种效应在快速增殖的AML细胞中被增强，这些细胞具有更高的代谢需求，对内质网应激更为敏感。●​ 下游效应：○​ 错误折叠蛋白的积累导致UPR中的PERK和ATF6通路激活，进而加剧内质网应激和细胞凋亡。○​ IRE1α的抑制会破坏由XBP1调控的转录程序，从而阻碍参与内质网稳态和细胞存活的蛋白质生成。○​ 由此产生的内质网应激会触发整合应激反应（ISR）的激活，导致许多转录本的翻译抑制以及细胞凋亡活动的增加。○​ KIRA6可以间接抑制这一过程。
通过减少内质网压力与炎症细胞因子产生，降低细胞存活率、增殖能力和抗性，从而抑制 NF-κB通路。○​ KIRA6可能直接降低IL-1等炎症细胞因子的水平，进而减少炎症信号级联反应的二次激活，并降低IRAK1的激活程度。●​ 对FLT3-ITD的影响：FLT3-ITD突变会导致细胞增殖增加、代谢需求提升及压力增大。KIRA6可通过干扰UPR来针对这一问题，从而对FLT3-ITD细胞产生更显著的影响。FLT3-ITD细胞本身就处于高压力状态，需要高水平的蛋白质合成才能维持生存。
通过靶向基础或激活的 IRE1α，KIRA6 能够在 FLT3-ITD 细胞中引发比其野生型对应细胞更显著的细胞死亡。● 对关键异常通路的影响：○ MYC：MYC 蛋白水平与 mRNA 翻译直接相关，在许多情况中对于细胞的存活和抵抗性至关重要，包括白血病。

### co-scientist-0553

**English original**

Targeting the UPR and downstream translation with KIRA6 directly decreases MYC expression and survival. This also has downstream anti-inflammatory benefits.

**中文译文 · 机器初译**

利用 KIRA6 针对 UPR 及下游翻译过程，可直接降低 MYC 表达与存活率，同时还能带来下游抗炎效应。


### 原文第 95 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=95)

### co-scientist-0555

**English original**

○​ NF-κB signaling: KIRA6 can reduce NF-κB activity, a key driver of cell survival, proliferation, and resistance, by reducing ER stress and inflammatory cytokine production. ○​ MCL-1 and other anti-apoptotic proteins: KIRA6 will reduce the production of short-lived survival proteins, leading to rapid apoptosis by diminishing their production, particularly MCL-1 and other similar proteins, which are involved in anti-apoptotic effects in AML cells, and are known drug resistant mechanisms. ○​ Targeting multiple AML resistance mechanisms: KIRA6, by disrupting protein homeostasis, has the capacity to overcome resistance across a wide panel of mechanisms, including through reduced efflux pump protein levels, and reduced repair mechanisms. ●​ Synergistic effects: KIRA6 can synergize with FLT3 inhibitors by increasing ER stress, making cells more sensitive to FLT3 inhibition. It can also enhance the activity of chemotherapeutic drugs by disrupting DNA repair pathways.

**中文译文 · 机器初译**

○​ NF-κB 信号传导：KIRA6 可通过减少内质网应激和炎症细胞因子的产生，降低 NF-κB 活性，而 NF-κB 是细胞存活、增殖和抵抗的关键驱动因素。 ○​ MCL-1 及其他抗凋亡蛋白：KIRA6 会减少短暂存活蛋白的产生，从而通过抑制这些蛋白的生成导致快速凋亡，尤其是 MCL-1 及其他类似蛋白，这些蛋白参与 AML 细胞的抗凋亡作用，也是已知的耐药机制。 ○​ 针对多种 AML 耐药机制：KIRA6 通过破坏蛋白质稳态，能够克服多种耐药机制，包括减少外排泵的功能。
蛋白质水平降低，修复机制也减弱。● 协同效应：KIRA6可以通过增加内质网应激与FLT3抑制剂产生协同作用，使细胞对FLT3抑制更加敏感。它还可以通过破坏DNA修复途径来增强化疗药物的活性。

### co-scientist-0556

**English original**

Impacted pathways ●​ Unfolded protein response (UPR): Directly impacted through inhibition of IRE1α. ●​ Apoptosis: Primarily through the intrinsic pathways, and disruption of anti-apoptotic proteins, and an increase in ER stress, alongside an increase of pro-apoptotic proteins through the integrated stress response. ●​ Cell cycle: Perturbation of cell cycle progression through reduced levels of cell-cycle proteins. ●​ NF-κB signaling: KIRA6 can reduce NF-κB activity which reduces inflammation and promotes cell survival, and drug resistance. ●​ MYC-related pathways: Suppression of MYC and other related oncogene protein levels. ●​ Inflammatory pathways: By suppressing cytokines, most notably IL-1, KIRA6 can suppress activation of IRAK1 and reduce chronic inflammation that promotes cell survival in addition to killing cancer cells.

**中文译文 · 机器初译**

受影响的通路 ●​ 展开蛋白反应（UPR）：通过抑制 IRE1α 直接受到影响。●​ 细胞凋亡：主要通过内在通路，以及抗凋亡蛋白的破坏、内质网应激的增加，以及整合应激反应导致的促凋亡蛋白增加。●​ 细胞周期：通过降低细胞周期蛋白的水平，导致细胞周期进程受到干扰。●​ NF-κB 信号传导：KIRA6 可降低 NF-κB 活性，从而减少炎症、促进细胞存活及药物耐药性。●​ MYC 相关通路：抑制 MYC 及其他相关癌基因蛋白水平。●​ 炎症通路：通过抑制细胞因子，尤其是
IL-1和KIRA6不仅能杀死癌细胞，还能抑制IRAK1的激活，减少促进细胞存活的慢性炎症。

### co-scientist-0557

**English original**

Effect on AML (MOLM-13) cell proliferation inhibition ●​ KIRA6 selectively inhibits proliferation of MOLM-13 cells, and also AML cells with other mutations that render them drug resistant. ●​ IRE1α inhibition leads to the activation of apoptotic pathways and reduced cell proliferation and clonal survival. ●​ Suppression of MYC levels, NF-κB, MCL-1 and other cell survival pathways will reduce cell survival and promote apoptosis, which should be enhanced in FLT3-ITD AML due to their high proliferation rates and increased sensitivity to metabolic/translational stress in comparison to normal myeloid cells. ●​ In addition to having a direct effect on proliferation, a reduction in inflammatory signalling (IL-1 and IRAK1) can potentiate activity of other drugs.

**中文译文 · 机器初译**

对AML（MOLM-13）细胞增殖的抑制作用 ●​ KIRA6能够选择性抑制MOLM-13细胞的增殖，也能抑制其他具有耐药性的突变的AML细胞。 ●​ IRE1α的抑制会导致凋亡途径激活，进而降低细胞增殖和克隆存活率。 ●​ MYC水平、NF-κB、MCL-1及其他细胞存活途径的抑制会降低细胞存活率并促进凋亡，在FLT3-ITD AML中应加强这一作用，因为与正常髓系细胞相比，这些细胞具有更高的增殖率和对代谢/翻译应激的敏感性。 ●​ 除了直接作用于增殖外，炎症的减少也会产生作用
信号传导（IL-1和IRAK1）可增强其他药物的活性。


### 原文第 96 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=96)

### co-scientist-0559

**English original**

●​ KIRA6 treatment results in a dose-dependent reduction in MOLM-13 cell viability. ●​ KIRA6 leads to a buildup of ER stress and activation of the ISR, all which enhance its effectiveness as a targeted drug. ●​ When combined with FLT3 inhibitors or chemotherapeutic drugs, KIRA6 is expected to show additional impacts at lower overall drug concentrations (lower levels of both KIRA6 or the alternative drugs in the combination will be required for the same levels of cell death, or greater cell death will be seen at the standard doses used presently in the clinic). This is very important given the high levels of both drug toxicity that are associated with all AML treatments, and the need to reduce those toxicities.

**中文译文 · 机器初译**

● KIRA6治疗可导致MOLM-13细胞存活率呈剂量依赖性下降。● KIRA6会导致ER应激加剧及ISR激活，这些效应均提升了其作为靶向药物的疗效。● 当与FLT3抑制剂或化疗药物联合使用时，KIRA6在较低总体药物浓度下有望产生额外效果（要达到相同的细胞死亡水平，或在当前临床标准剂量下出现更严重的细胞死亡，需要更低水平的KIRA6或组合中的其他药物）。
这非常重要，因为所有AML治疗都会带来较高的药物毒性，同时也需要减少这些毒性。

### co-scientist-0560

**English original**

IC50 assay concentrations Based on published data for KIRA6 in other cancer cell models and its known mechanism of action, a reasonable starting concentration range for an IC50 assay in MOLM-13 cells would be 100 nM to 10 µM. ●​ Rationale: This range spans the concentrations that have shown activity in various cell types while being within a pharmacologically achievable range. Prior in vitro studies have shown activity in low micromolar concentrations. ●​ Specific concentrations: 100 nM, 250 nM, 500 nM, 1 µM, 2.5 µM, 5 µM, 7.5 µM, 10 µM. ●​ Assay method: Cell viability assays (e.g., MTT, CellTiter-Glo) to determine IC50 values after KIRA6 exposure for 48-72 hours. ●​ Controls: Appropriate vehicle controls (DMSO) or medium-only controls should be included. ●​ Positive control: Use a known FLT3 inhibitor, such as gilteritinib, at its reported IC50 in MOLM-13 cells for normalization of assay variability and comparison. ●​ Combination studies: The combination of a FLT3 inhibitor at a single set concentration, plus a matrix of KIRA6 concentrations at several ratios will be evaluated using the viability assays as a baseline. Additional confirmation using apoptotic assays and cell cycle arrest should be done for any combination that shows better results than single-agent drug effects.

**中文译文 · 机器初译**

IC50 检测浓度：基于其他癌细胞模型中 KIRA6 的已发表数据及其已知的作用机制，MOLM-13 细胞中进行 IC50 检测的合理起始浓度范围应为 100 nM 至 10 µM。● 依据：该范围涵盖了在多种细胞类型中表现出活性的浓度，且处于药理学可实现的范围内。
之前的体外研究表明，在低微摩尔浓度下该物质具有活性。● 具体浓度：100 nM、250 nM、500 nM、1 µM、2.5 µM、5 µM、7.5 µM、10 µM。● 检测方法：通过细胞存活率检测（如MTT、CellTiter-Glo）在KIRA6处理48-72小时后测定IC50值。● 对照组：应包含适当的溶剂对照（DMSO）或仅使用培养基的对照。● 阳性对照：在MOLM-13细胞中使用已知的FLT3抑制剂（如gilteritinib）及其报道的IC50值，以消除检测变异性并进行比较。● 联合研究：在单一设定浓度下使用FLT3抑制剂，并采用多种比例的KIRA6浓度组合进行研究。
以可行性试验结果为基准进行评估。对于那些效果优于单一药物作用的组合，还应通过凋亡试验和细胞周期停滞实验进行进一步验证。

### co-scientist-0561

**English original**

Safety and toxicity ●​ Limited safety data: KIRA6 is a relatively new compound and has limited safety data in humans, as it has not gone through clinical trials. Initial in vitro and in vivo studies in other disease settings (mostly cancer) suggest that it is generally well-tolerated. However, thorough preclinical toxicity studies are essential before advancing to human trials. ●​ Potential toxicity: Given the mechanism of action, potential toxicities include ER stress-related effects on normal tissues, particularly those with high protein synthesis demands (e.g., liver, pancreas). However, since AML cells are under high levels of stress,

**中文译文 · 机器初译**

安全性与毒性 ●​ 安全性数据有限：KIRA6是一种相对较新的化合物，在人类中的安全性数据较少，因为它尚未进行临床试验。其他疾病类型（主要是癌症）的初步体外和体内研究表明，该药物通常耐受性良好。但在推进人体试验之前，必须进行全面的临床前毒性研究。 ●​ 潜在毒性：根据其作用机制，潜在的毒性包括正常组织因ER应激而产生的影响，尤其是那些蛋白质合成需求较高的组织（如肝脏、胰腺）。不过，由于AML细胞处于高压力状态，因此仍需进一步关注。


### 原文第 97 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=97)

### co-scientist-0563

**English original**

and have high metabolic demand, they are expected to be disproportionately impacted by this drug, which should reduce systemic toxicity. ●​ Repurposing advantage: Because KIRA6 has established in vitro activity, and has known pharmacology, it is significantly less risky than a compound that would have to have all of its safety profiles evaluated before human trials. ●​ Combination therapy impact: Because KIRA6 can be paired with existing therapies, it may be possible to reduce the overall dose of both agents to minimize side-effects and overall toxicity, while enhancing therapeutic efficacy. This should be tested rigorously in vitro through all of the combination studies before any movement into clinical human or animal trials to make sure that the benefit is higher than the risk.

**中文译文 · 机器初译**

由于具有较高的代谢需求，这些细胞预计会受到该药物的异常影响，从而应能降低全身毒性。●​ 重新应用的优势：由于 KIRA6 在体外实验中具有活性且药理学特性已知，其风险远低于那些在人体试验前必须全面评估安全性的化合物。●​ 联合治疗的影响：由于 KIRA6 可以与现有疗法结合使用，或许可以降低两种药物的整体剂量，以最小化副作用和全身毒性，同时提升治疗效果。
在进行任何针对人类或动物临床试验之前，应通过所有组合研究在体外严格进行测试，以确保收益大于风险。

### co-scientist-0564

**English original**

Testable hypothesis KIRA6, by inhibiting IRE1α, will selectively inhibit the proliferation of AML cells, especially FLT3-ITD positive cells, by disrupting protein homeostasis and inducing ER stress. The increase in stress and reduced output of essential cell maintenance proteins will trigger apoptotic pathways, leading to cell death, particularly in highly proliferative settings. KIRA6 will potentiate the activity of existing AML therapies such as FLT3 inhibitors and chemotherapeutics. The drug will also have a broader impact on resistance mechanisms.

**中文译文 · 机器初译**

可验证的假设：通过抑制 IRE1α，KIRA6能够通过破坏蛋白质稳态并引发内质网应激，选择性地抑制AML细胞的增殖，尤其是FLT3-ITD阳性细胞。应激程度的增加以及必需细胞维持蛋白产量的降低将触发凋亡途径，导致细胞死亡，尤其是在高度增殖的情况下。KIRA6还能增强现有AML治疗手段（如FLT3抑制剂和化疗药物）的效果。该药物还将对耐药机制产生更广泛的影响。

### co-scientist-0565

**English original**

Experimental plan ●​ IC50 determination in MOLM-13: Determine IC50 values in MOLM-13 cells using viability assays with KIRA6 concentrations ranging from 100 nM to 10 µM. ●​ ER stress marker measurement: Measure levels of key ER stress markers (e.g., BiP/GRP78, CHOP) using Western blotting and ELISA after KIRA6 treatment to confirm the impact on ER homeostasis. ●​ IRE1α activity: Measure XBP1 splicing using RT-PCR or other assays to confirm KIRA6's impact on IRE1α activity. ●​ Apoptosis assays: Evaluate apoptosis by Annexin V/PI staining, caspase activity assays, and Western blot analysis of apoptotic markers (cleaved PARP, cleaved caspase-3 levels) in KIRA6-treated MOLM-13 cells. ●​ Western blots: Analyze key pathway proteins: including MYC, NF-κB, MCL-1, FLT3, AKT/mTOR, and key components of the canonical inflammatory pathways (including IL-1, IL-6, TNF-alpha, IRAK1/4, MyD88), and markers of endoplasmic reticulum (ER) stress in AML cells treated with KIRA6. ●​ ISR markers measurement: Evaluate the induction of the Integrated Stress Response using assays measuring levels of phospho-eIF2α, ATF4, and CHOP. ●​ Combination studies: Evaluate the combination of KIRA6 with FLT3 inhibitors like gilteritinib, with chemotherapeutics (cytarabine, daunorubicin) or with venetoclax in MOLM-13 cells using combination matrix studies. This will establish if there is synergistic activity and enable evaluation of lower doses of each drug. Repeat these on

**中文译文 · 机器初译**

实验计划 ●​ MOLM-13中 IC50 测定：使用 KIRA6 浓度在 100 nM 至 10 µM 范围内的存活率检测法，在 MOLM-13 细胞中确定 IC50 值。 ●​ ER 应激标志物检测：在 KIRA6 处理后，通过 Western 印迹法和 ELISA 检测关键 ER 应激标志物（如 BiP/GRP78、CHOP）的水平，以确认其对 ER 稳态的影响。 ●​ IRE1α 活性：通过 RT-PCR 或其他检测方法测定 XBP1 剪接情况，以确认 KIRA6 对 IRE1α 活性的影响。 ●​ 细胞凋亡检测：通过 Annexin V/PI 染色、caspase 活性检测以及 MOLM-13 细胞经 KIRA6 处理后凋亡标志物的 Western 印迹分析（如切割 PARP、切割 caspase-3 水平），评估细胞凋亡情况。 ●​ Western
结果分析：分析AML细胞中关键通路蛋白，包括MYC、NF-κB、MCL-1、FLT3、AKT/mTOR以及典型炎症通路的关键成分（如IL-1、IL-6、TNF-α、IRAK1/4、MyD88），以及内质网（ER）应激标志物，这些研究对象均接受了KIRA6处理。● 整合应激反应标志物的检测：通过测量磷酸化eIF2α、ATF4和CHOP的水平，评估整合应激反应的激活情况。● 联合研究：在MOLM-13细胞中，利用联合矩阵研究方法，评估KIRA6与FLT3抑制剂如gilteritinib的联合使用，以及与化疗药物（胞苷酸类似物、柔红霉素）或维奈托克的组合效果。
这将确定是否存在协同作用，并便于评估每种药物的低剂量使用效果。重复上述操作


### 原文第 98 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=98)

### co-scientist-0567

**English original**

additional cell lines with and without FLT3 mutations to confirm consistent synergistic enhancement. ●​ Cell cycle analysis: Measure cell cycle arrest using DNA staining (propidium iodide) by flow cytometry. ●​ RNA stress markers studies: Evaluate markers of RNA stress to assess damaged mRNA levels and ER Stress markers to determine cellular stress induced by the drug. ●​ Efflux pump activity: Measure the activity of key drug efflux pumps (e.g., ABCB1, ABCG2) using specific inhibitors and substrates to evaluate KIRA6's impact on drug resistance mechanisms. ●​ Expansion to other cell lines: Repeat the above assays on multiple AML cell lines, with both FLT3-ITD and wild-type cells, and lines representing other AML mutations or drug resistance phenotypes. Also evaluate primary AML patient cells in co-culture with stroma and alone with comparable controls, including primary non-leukemic bone marrow derived cells for measuring minimal activity in normal myeloid cells. This should allow for verification of the generalizability of KIRA6. ●​ In vivo xenograft studies: Evaluate the efficacy and safety of KIRA6 in mouse xenograft models using MOLM-13 cells or other cell lines to assess its overall treatment value and toxicities. ●​ Pharmacokinetics studies: Evaluate absorption, distribution, metabolism, and excretion of KIRA6 in animals to enable rational dose selection in future trials.

**中文译文 · 机器初译**

包含和不含 FLT3 突变的额外细胞系，以确认一致的协同增强效应。● 细胞周期分析：通过流式细胞术使用碘化丙啶进行 DNA 染色来测量细胞周期停滞情况。● RNA 应激标志物研究：评估 RNA 应激相关标志物，以测定受损 mRNA 水平以及内质网应激标志物，从而判断药物引起的细胞应激。● 外排泵活性：使用特定抑制剂和底物测量关键药物外排泵（如 ABCB1、ABCG2）的活性，以评估 KIRA6 对药物耐药机制的影响。● 其他细胞系的扩展实验：在多种 AML 细胞系上进行上述检测，包括 FLT3-ITD 细胞及野生型细胞。
表征其他大语言模型突变或药物耐药性表型。还需在间质组织中共培养以及单独培养情况下，对原发性AML细胞进行评估，并使用相应的对照样本，包括原发性非白血病性骨髓来源细胞，以测量正常髓系细胞中的最低活性。
这应有助于验证 KIRA6 的泛化能力。● 体内异种移植研究：使用 MOLM-13 细胞或其他细胞系在小鼠异种移植模型中评估 KIRA6 的疗效与安全性，以判断其整体治疗价值及毒性。● 药代动力学研究：评估 KIRA6 在动物体内的吸收、分布、代谢和排泄情况，为未来试验中的合理剂量选择提供依据。

### co-scientist-0568

**English original**

Conclusion Repurposing KIRA6, an IRE1α inhibitor, for AML treatment, with a focus on FLT3-ITD positive cells and overcoming resistance mechanisms, represents a promising novel approach. KIRA6's ability to disrupt protein homeostasis, induce ER stress, synergize with existing AML drugs, and potentially overcome resistance mechanisms makes it an excellent drug candidate for testing. The comprehensive experimental plan proposed here offers a thorough framework for validating the potential of KIRA6 in AML and allows for a better way to select drugs for clinical testing by first performing a rigorous scientific evaluation in vitro using a multi-faceted approach. KIRA6 could translate into a new and effective strategy for AML patients, particularly those with the challenging FLT3-ITD mutation and other resistance phenotypes. Due to its mode of action on the UPR, it also has the potential to target underlying resistance mechanisms to existing therapies.

**中文译文 · 机器初译**

结论：将 IRE1α 抑制剂 KIRA6 重新用于 AML 治疗，并重点针对 FLT3-ITD 阳性细胞以及克服耐药机制，是一种具有前景的新方法。KIRA6 能够破坏蛋白质稳态、引发内质网应激、与现有 AML 药物协同作用，并可能克服耐药机制，因此成为值得测试的优秀药物候选物。此处提出的全面实验计划为验证 KIRA6 在 AML 中的潜力提供了完善的框架，通过采用多维度方法在体外进行严格的科学评估，有助于更精准地选择用于临床测试的药物。
KIRA6可以成为AML患者一种新且有效的治疗策略，尤其适用于那些具有复杂的FLT3-ITD突变及其他耐药表型的患者。由于其对UPR的作用机制，它还有可能针对现有疗法的潜在耐药机制进行干预。

### co-scientist-0569

**English original**

The focus on resistance mechanisms, a more diverse set of cell lines and primary cells, a well-rationalized combination approach, and a specific mechanism of action, all address the feedback from the previous version and provide a strong and detailed rationale for this drug repurposing strategy. The expanded experimental plan provides a thorough framework for assessing the efficacy, selectivity, and safety of KIRA6 in AML.

**中文译文 · 机器初译**

对抗机制的关注、更多种类的细胞系和原代细胞、合理的组合疗法方案以及特定的作用机制，均解决了前一个版本的不足，并为该药物重新应用策略提供了充分且详细的依据。扩展的实验计划为评估KIRA6在急性髓系白血病中的疗效、选择性和安全性提供了完善的框架。


### 原文第 99 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=99)

### co-scientist-0571

**English original**

Review

**中文译文 · 机器初译**

评审

### co-scientist-0572

**English original**

Relevant article abstracts 1: Discusses targeting the IRE1α-XBP1s pathway in AML, directly relevant to the proposed mechanism of KIRA6. 5: Reviews the UPR as a therapeutic target in acute leukemias, providing context and supporting the rationale for targeting IRE1α. 6: Focuses on selective degradation of FLT3-ITD, offering insights into targeting specific forms of the mutated protein, aligning with the idea's focus on targeting ER-bound FLT3-ITD. 7: Offers the background on known pharmacology and toxicological studies for IC50 determination of drug candidates in tumor cells. 9: Discusses sensitizing AML to venetoclax treatment, highlighting the potential for combination therapy approaches, relevant to the idea's suggested synergistic effects with other AML drugs.

**中文译文 · 机器初译**

相关文章摘要1：讨论了在急性髓系白血病中针对IRE1α-XBP1通路的作用，这与KIRA6提出的机制直接相关。5：综述了UPR作为急性白血病的治疗靶点，为针对IRE1α提供了背景支持及理论依据。6：重点探讨FLT3-ITD的选择性降解，为针对特定突变蛋白形式提供了见解，与该研究聚焦针对ER结合的FLT3-ITD的理念相契合。7：介绍了用于确定肿瘤细胞中药物候选物IC50值的已知药理学和毒理学研究背景。
9：讨论如何使AML患者了解维奈克拉治疗方案，并强调联合治疗方法的潜力，这与该方案与其他AML药物协同作用的预期效果相符。

### co-scientist-0573

**English original**

Assumptions ●​ KIRA6 effectively inhibits IRE1α in AML cells, particularly MOLM-13 cells. ●​ IRE1α inhibition leads to significant disruption of protein homeostasis and induction of ER stress in AML cells. ●​ The increased ER stress induced by KIRA6 selectively targets AML cells over healthy cells. ●​ KIRA6 synergizes with FLT3 inhibitors and chemotherapeutic agents to enhance AML cell death. ●​ The proposed IC50 concentration range (100 nM to 10 µM) is appropriate for testing in MOLM-13 cells. ●​ KIRA6 has a manageable safety profile and tolerable toxicity in preclinical models. ●​ KIRA6 can inhibit the production of short-lived proteins, like MYC and MCL-1, and reduce inflammatory signaling.

**中文译文 · 机器初译**

假设 ●​ KIRA6能有效抑制AML细胞中的IRE1α，尤其是MOLM-13细胞。 ●​ IRE1α的抑制会导致AML细胞蛋白质稳态严重紊乱，并引发内质网应激。 ●​ KIRA6引起的内质网应激增加，能够选择性地影响AML细胞而非健康细胞。 ●​ KIRA6与FLT3抑制剂及化疗药物协同作用，可增强AML细胞的死亡。 ●​ 所提出的IC50浓度范围（100 nM至10 µM）适用于在MOLM-13细胞中进行测试。 ●​ KIRA6在临床前模型中具有可控的安全性特征及可耐受的毒性。 ●​ KIRA6能够抑制如MYC和MCL-1这类短寿命蛋白的产生，并减少炎症反应。
信号传递。

### co-scientist-0574

**English original**

Reasoning about assumptions ●​ Plausible: [1] and [5] support the notion of targeting IRE1α in AML. While no direct information shows if KIRA6 effective inhibits IRE1α in AML MOLM 3 cells, it likely works as an IRE1α inhibitor like in other cell types. Needs experimental validation. ●​ Plausible: This is a core function of the UPR pathway in which IRE1α inhibition, based on the literature [5], should induce this cascade of events causing stress response leading to cell death if prolonged and severe. ●​ Plausible, but requires careful investigation: AML cells, particularly those with FLT3-ITD, have higher protein synthesis rates and are inherently more sensitive to ER stress. While this is not demonstrated in the literature, the rationale behind targeting ER stress response in leukemia is that tumor cells, particularly with FLT3-ITD, are expected

**中文译文 · 机器初译**

对假设的推理 ●​ 合理：[1] 和 [5] 支持在AML中针对IRE1α进行靶向治疗的观点。虽然没有直接信息表明KIRA6能否有效抑制AML MOLM 3细胞中的IRE1α，但它在其他细胞类型中作为IRE1α抑制剂发挥作用的可能性较大。需要通过实验验证。 ●​ 合理：这是UPR通路的核心功能，根据文献[5]，IRE1α的抑制若持续且严重，应引发一系列事件，导致应激反应并导致细胞死亡。 ●​ 合理，但需要仔细研究：AML细胞，尤其是具有FLT3-ITD特征的细胞，具有更高的蛋白质合成率，对内质网应激更为敏感。
尽管文献中并未证明这一点，但针对白血病中的内质网应激反应的理由在于，肿瘤细胞，尤其是具有 FLT3-ITD 的肿瘤，具有这种特性


### 原文第 100 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=100)

### co-scientist-0576

**English original**

to be more reliant on these processes and therefore may be more susceptible, but this assumption needs further evaluation. ●​ Plausible, but requires testing: The rationale for synergy is based on the proposed mechanism and general principles of targeting multiple pathways in cancer. [9] offers a related example of synergy with venetoclax, a drug also being tested in FLT3-ITD AML.

**中文译文 · 机器初译**

可能更依赖这些过程，因此也更容易受到影响，但这一假设仍需进一步验证。●​ 合理，但需要测试：协同作用的原理基于所提出的机制以及针对癌症多种途径的通用原则。[9] 提供了与 venetoclax 协同作用的类似案例，而 venetoclax 也是一种正在 FLT3-ITD 急性髓系白血病中进行的试验药物。

### co-scientist-0577

**English original**

This hypothesis needs further in vitro testing to be demonstrated. ●​ Plausible: The suggested range is based on literature and seems reasonable as a starting point. This needs to be empirically confirmed in an IC-50 assay. The provided range in the idea is a well justified assumption that can be verified during the IC-50 viability assays where a broader range of concentrations would capture the optimal values. ●​ Unknown: This is a vital assumption requiring thorough preclinical testing. [7] has information about pharmacology and toxicity, which provides context. Currently, limited safety data exists for KIRA6 so the drug safety profile is unknown and needs experiments to verify if the drug is safe enough. ●​ Plausible: IRE1α inhibition and ER stress induction can trigger downstream effects that impact protein translation and inflammatory responses based on the mechanism described in the UPR [5]. [1] suggests that IRE1α impacts venetoclax efficacy. While this is not demonstrated in the literature for KIRA6 in AML, this remains an experimentally verifiable assumption.

**中文译文 · 机器初译**

该假设需要进一步进行体外测试以得到验证。●​ 合理：所建议的范围基于文献数据，作为起点似乎合理。需要通过 IC-50 测定进行实证确认。该设想中给出的范围是一个合理的假设，可以在 IC-50 存活率测定中验证，更广泛的浓度范围能够捕捉到最优值。●​ 未知：这是一个需要全面临床前测试的关键假设。[7] 提供了关于药理学和毒性的信息，有助于理解背景。
目前关于 KIRA6 的安全数据非常有限，因此其药物安全性尚不清楚，需要通过实验来确认该药物是否足够安全。●​ 合理：根据 UPR 中描述的机制[5]，IRE1α 抑制和 ER 应激诱导可能会引发影响蛋白质翻译和炎症反应的下游效应。[1] 指出 IRE1α 会降低 venetoclax 的疗效。虽然这一结论在 AML 患者使用 KIRA6 的研究中尚未得到证实，但这仍是一个可以通过实验验证的假设。

### co-scientist-0578

**English original**

Improvements to the idea ●​ Broader cell line testing: The idea primarily focuses on MOLM-13. Expanding to other AML cell lines, including those with different FLT3 mutations and other genetic backgrounds, would strengthen the proposal. This would require additional experiments as well. ●​ Deeper exploration of resistance mechanisms: While mentioned, the idea could benefit from a more detailed analysis of how KIRA6 addresses specific resistance mechanisms in AML. The idea can also benefit from additional experiments regarding resistance mechanism impacts. ●​ Investigate drug resistance: There is minimal data regarding KIRA6 impacting drug efflux pumps and other drug resistance mechanisms. It would be beneficial to investigate how impacting the UPR could impact drug resistant cells, which are a major reason for treatment failure in AML. ●​ Detailed comparison to other IRE1α inhibitors: If there are other IRE1α inhibitors, comparing and contrasting KIRA6 with them and justifying the reasons for choosing this particular drug would add to the idea's strength.

**中文译文 · 机器初译**

对该概念的改进 ●​ 更广泛的细胞系测试：该概念主要聚焦于 MOLM-13。将研究范围扩展至其他AML细胞系，包括具有不同FLT3突变和其他遗传背景的细胞系，将能增强该提案的说服力。这也需要进行额外的实验。 ●​ 更深入地探索耐药机制：虽然已提及，但更详细分析KIRA6如何应对AML中的特定耐药机制，对该概念会有更大帮助。关于耐药机制影响的相关额外实验也能为该概念带来益处。 ●​ 研究药物耐药性：关于KIRA6如何影响药物外排泵及其他药物耐药机制的数据非常有限。
研究UPR对耐药细胞的影响有何益处会很有帮助，而耐药细胞正是急性髓系白血病治疗失败的主要原因。●​ 与其他IRE1α抑制剂的详细比较：如果还有其他IRE1α抑制剂，将KIRA6与这些抑制剂进行对比分析，并说明选择该特定药物的理由，将有助于增强这一观点的说服力。

### co-scientist-0579

**English original**

Reasoning about correctness and testing ●​ The idea is plausible and well-reasoned based on known mechanisms of IRE1α and the UPR in cancer. However, key assumptions about selectivity and synergy require

**中文译文 · 机器初译**

关于正确性和检测的推理 ●​ 这一想法是合理的，且基于癌症中 IRE1α 和 UPR 的已知机制进行了充分论证。然而，关于选择性和协同作用的关键假设仍需进一步验证


### 原文第 101 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=101)

### co-scientist-0581

**English original**

experimental validation. The proposed experimental plan is comprehensive and addresses the key questions. ●​ The idea is novel in its application of KIRA6 to AML, particularly in the context of FLT3-ITD. The focus on combination therapy and overcoming resistance is also promising. ●​ It is recommended to test this idea due to its plausibility, novelty, and potential clinical significance. While there are uncertainties regarding safety and efficacy, the potential benefits warrant further investigation. ●​ Answer: 4

**中文译文 · 机器初译**

实验验证。所提出的实验方案全面且能解决关键问题。● 将 KIRA6 应用于 AML 的思路具有新颖性，尤其是在 FLT3-ITD 语境下。注重联合治疗及克服耐药性也极具前景。● 鉴于其合理性、新颖性及潜在的临床意义，建议对这一想法进行测试。尽管在安全性与有效性方面存在不确定性，但其潜在益处值得进一步研究。● 答案：4

### co-scientist-0582

**English original**

Novelty review ●​ Targeting the IRE1α-XBP1s pathway to enhance venetoclax effectiveness in AML [1]:

**中文译文 · 机器初译**

新颖性评审 ●​ 针对 IRE1α-XBP1s 通路以提高维内妥氯在急性髓系白血病中的疗效 [1]：

### co-scientist-0583

**English original**

This abstract directly relates to the idea by exploring the IRE1α pathway in AML, although in combination with venetoclax, not as a monotherapy or in combination with FLT3 inhibitors. ●​ The unfolded protein response: A novel therapeutic target in acute leukemias [5]: This review discusses the UPR as a target in acute leukemias, providing a broader context for the idea’s focus on IRE1α. ●​ Selective degradation of mutant FMS-like tyrosine kinase-3 requires BIM-dependent depletion of heat shock proteins [6]: This abstract explores the mechanisms of FLT3 degradation and its connection to BIM and heat shock proteins, relevant to the idea’s focus on FLT3-ITD positive AML.

**中文译文 · 机器初译**

该摘要直接探讨了AML中的IRE1α通路，与该研究主题相关，不过并非采用单药治疗形式，也不是与FLT3抑制剂联合使用。●​ 未折叠蛋白反应：急性白血病的新治疗靶点 [5]：本综述将UPR作为急性白血病的治疗靶点进行了讨论，为该主题对IRE1α的关注提供了更全面的背景。●​ 突变型FMS类似酪氨酸激酶-3的选择性降解需要依赖BIM的热休克蛋白清除 [6]：该摘要探讨了FLT3降解的机制及其与BIM和热休克蛋白的关系，这与该主题对FLT3-ITD阳性AML的关注密切相关。

### co-scientist-0584

**English original**

Already explored aspects ●​ Targeting the UPR in AML: The idea of targeting the unfolded protein response (UPR) in AML is not entirely novel. Abstract [5] discusses the UPR as a therapeutic target in acute leukemias, including AML. Abstract [1] specifically explores targeting IRE1α in combination with venetoclax, suggesting existing interest in this pathway for AML.

**中文译文 · 机器初译**

已探讨的方面 ●​ 针对AML中的UPR：以展开蛋白反应（UPR）为靶点的策略并非完全新颖。摘要[5]讨论了UPR作为急性白血病（包括AML）治疗靶点的作用。摘要[1]则具体探讨了结合维奈克拉使用IRE1α作为靶点的方法，表明目前对AML中这一通路存在关注。

### co-scientist-0585

**English original**

However, the use of KIRA6 as a single agent or in combination with FLT3 inhibitors appears less explored. ●​ FLT3 inhibitors in AML: Targeting FLT3 in AML with tyrosine kinase inhibitors is a well-established approach, with multiple approved drugs. Abstracts [2, 3] focus on FLT3 inhibitors, highlighting the importance of this target but also the challenges of resistance [6].

**中文译文 · 机器初译**

然而，将 KIRA6 作为单一智能体使用或与 FLT3 抑制剂联合使用的研究则较少。●​ AML 中的 FLT3 抑制剂：使用酪氨酸激酶抑制剂针对 AML 中的 FLT3 是一种成熟的治疗策略，已有多种获批药物。相关摘要 [2, 3] 重点讨论了 FLT3 抑制剂，强调了该靶点的重要性以及耐药性问题 [6]。

### co-scientist-0586

**English original**

Novel aspects ●​ Repurposing KIRA6 for AML: While IRE1α has been targeted in AML [1], the repurposing of KIRA6 specifically for AML treatment, especially in the context of FLT3-ITD positive disease and potential combination with FLT3 inhibitors or standard chemotherapies, seems novel based on the provided abstracts. The idea explores KIRA6's

**中文译文 · 机器初译**

新意 ● 将 KIRA6 重新用于 AML 治疗：虽然 IRE1α 已被用于 AML 的治疗[1]，但根据提供的摘要来看，将 KIRA6 专门用于 AML 治疗，尤其是在 FLT3-ITD 阳性疾病背景下，并可能与 FLT3 抑制剂或常规化疗联合使用，这一做法显得具有创新性。该研究探讨了 KIRA6 的...


### 原文第 102 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=102)

### co-scientist-0588

**English original**

impact on multiple pathways (UPR, apoptosis, NF-κB, MYC) related to AML proliferation and resistance. ●​ Focusing on FLT3-ITD positive AML & combination therapy: Although FLT3 inhibitors are used in AML, the idea of combining KIRA6 with FLT3 inhibitors or chemotherapeutics to specifically target FLT3-ITD positive AML cells and potentially overcome resistance addresses a current clinical need. The proposed mechanism – disrupting protein homeostasis in already stressed FLT3-ITD cells – offers a rationale for this combination approach. ●​ Combination of KIRA6 with other AML drugs & mechanism of action: KIRA6 is not mentioned in any of the abstracts, and therefore the proposed combination of KIRA6 and FLT3i to induce apoptosis is also novel. The described mechanism has strong logical support, as the cells' increased translation requirements and ER stress from the FLT3i mutation could greatly increase the effectiveness of IRAK1 inhibition, which may itself directly induce apoptosis, and also improve efficacy of existing drugs.

**中文译文 · 机器初译**

对与急性髓系白血病增殖和耐药性相关的多种通路（UPR、细胞凋亡、NF-κB、MYC）的影响。●​ 针对FLT3-ITD阳性急性髓系白血病及联合治疗：尽管在急性髓系白血病中已使用FLT3抑制剂，但将KIRA6与FLT3抑制剂或化疗药物结合使用，以特异性靶向FLT3-ITD阳性的白血病细胞并可能克服耐药性，这一思路符合当前的临床需求。
所提出的机制——破坏已处于应激状态的 FLT3-ITD 细胞中的蛋白质稳态——为这种联合治疗策略提供了理论依据。● KIRA6与其他AML药物的联合使用及其作用机制：在所有摘要中均未提及 KIRA6，因此将 KIRA6与 FLT3i 结合以诱导细胞凋亡的联合方案也属新发现。所描述的机制具有充分的逻辑支撑，因为 FLT3i 突变导致的细胞翻译需求增加及内质网应激，能够显著增强 IRAK1 的抑制效果，而 IRAK1 的抑制可能直接引发细胞凋亡，同时还能提升现有药物的疗效。

### co-scientist-0589

**English original**

Novelty review The idea presents a moderate level of novelty. Repurposing KIRA6 for AML, particularly in the context of FLT3-ITD positive disease and combination therapy, is a promising approach. However, targeting IRE1α in AML has been explored [1], albeit not with this specific drug and with different existing treatment approaches. The idea’s strength lies in its detailed mechanistic rationale, combination therapy focus, and defined experimental plan. It is crucial to validate the proposed mechanism and selectivity across different AML cell lines and patient samples before concluding its true novelty.

**中文译文 · 机器初译**

新颖性评估 该想法具有中等程度的新颖性。将 KIRA6 重新用于 AML 治疗，尤其是在 FLT3-ITD 阳性疾病及联合治疗情境下，是一种有前景的方法。不过，针对 AML 中 IRE1α 的干预已有研究[1]，但并未使用这种特定药物，且采用不同的现有治疗方法。该想法的优势在于其详细的机制依据、注重联合治疗以及明确的实验计划。在确认其真正的新颖性之前，必须验证所提出的机制及其选择性在不同 AML 细胞系和患者样本中的表现。

### co-scientist-0590

**English original**

Improvements to the idea ●​ Literature search: Conduct a thorough literature search beyond the provided abstracts to confirm the novelty of KIRA6 in AML. Investigate any existing research on KIRA6 in other hematological malignancies. ●​ Selectivity testing: Expand selectivity testing to include other healthy cell types beyond normal myeloid cells, to address potential off-target effects and demonstrate greater safety margin. ●​ Combination exploration: Further explore rational combinations beyond FLT3 inhibitors, including chemotherapeutic agents and other targeted therapies. ●​ Resistance mechanisms: Thoroughly investigate the impact of KIRA6 on various AML resistance mechanisms through in vitro testing, using resistant cell lines and patient-derived samples. ●​ In vivo efficacy and toxicity profile: Expand the in vivo studies with multiple cell lines and patient-derived xenograft models, with a focus on establishing the efficacy and toxicity profile of KIRA6, both as single-agent and in the proposed combination strategy.

**中文译文 · 机器初译**

对该概念的改进 ●​ 文献检索：需对提供的摘要内容进行全面的文献检索，以确认 KIRA6 在 AML 领域的新颖性。
调查其他血液系统恶性肿瘤中关于KIRA6的现有研究。● 选择性测试：将选择性测试范围扩大至正常髓系细胞以外的其他健康细胞类型，以应对潜在的脱靶效应并提升安全性保障。● 联合治疗探索：进一步探索除FLT3抑制剂外的合理联合方案，包括化疗药物及其他靶向疗法。● 耐药机制：利用耐药细胞系和患者来源样本，通过体外实验全面研究KIRA6对各种急性髓系白血病耐药机制的影响。● 体内疗效与毒性特征：扩展体内研究范围至更多病例。
细胞系和患者来源异种移植模型，重点研究 KIRA6 作为单一药物或所提出的联合策略下的疗效与毒性特征。


### 原文第 103 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=103)

### co-scientist-0592

**English original**

Reasoning about novelty and recommendation The idea is novel enough to warrant further exploration. While targeting IRE1α isn't completely new, using KIRA6 in AML, especially in the context outlined, hasn't been extensively investigated, and it also has not been previously examined as a companion drug with other therapies used in AML. The proposed combination with FLT3 inhibitors and the detailed rationale provide a strong foundation. The comprehensive experimental plan should be executed to confirm the preliminary findings and assess the true potential of KIRA6 in AML. If the in vitro and in vivo findings are positive, the idea would be worthy of publication in a specialized journal focused on hematological malignancies or drug repurposing. Answer: 3

**中文译文 · 机器初译**

关于新颖性分析与建议：该想法足够新颖，值得进一步探索。虽然针对 IRE1α 的干预并非完全新事物，但将 KIRA6 用于大语言模型中的智能体场景，尤其是在所描述的情境下，尚未得到充分研究，且也从未被作为与其他AML治疗药物的辅助药物进行过探讨。提出的与 FLT3抑制剂结合的方案及详细依据为研究提供了坚实基础。应执行全面的实验计划，以验证初步结果并评估 KIRA6 在AML中的实际潜力。
如果体外和体内研究结果均为阳性，该研究方案值得发表在专注于血液恶性肿瘤或药物重新应用领域的专业期刊上。答案：3

### co-scientist-0593

**English original**

[1] Targeting the IRE1α-XBP1s Pathway to Enhance Venetoclax Effectiveness in AML | Blood | American Society of Hematology (https://ashpublications.org/blood/article/144/Supplement%201/4144/533082/Targeting-the-IRE 1-XBP1s-Pathway-toEnhance) [2] FLT3 inhibitors in acute myeloid leukemia: ten frequently asked questions | Leukemia (https://www.nature.com/articles/s41375-019-0694-3) [3] Inhibition of FLT3-ITD Kinase in Acute Myeloid Leukemia by New Imidazo[1,2-b]pyridazine Derivatives Identified by Scaffold Hopping | Journal of Medicinal Chemistry (https://pubs.acs.org/doi/10.1021/acs.jmedchem.3c00575) [4] Repurposing approved drugs on the pathway to novel therapies - PMC (https://pmc.ncbi.nlm.nih.gov/articles/PMC7018532/) [5] The Unfolded Protein Response: A Novel Therapeutic Target in Acute Leukemias - PMC (https://pmc.ncbi.nlm.nih.gov/articles/PMC7072709/) [6] Drugging the unfolded protein response in acute leukemias | Journal of Hematology & Oncology | Full Text (https://jhoonline.biomedcentral.com/articles/10.1186/s13045-015-0184-7) [7] Selective degradation of mutant FMS-like tyrosine kinase-3 requires BIM-dependent depletion of heat shock proteins | Leukemia (https://www.nature.com/articles/s41375-024-02405-5) [8] Pharmacology and Toxicology Testing: IC50 for Tumor Cell Lines - Altogen Labs (https://altogenlabs.com/pre-clinicalresearch-services/pharmacology-and-toxicology-testing-ic50 -for-tumor-cell-lines/) [9] Targeting Mitochondrial Structure Sensitizes Acute Myeloid Leukemia to Venetoclax Treatment | Cancer Discovery | American Association for Cancer Research (https://aacrjournals.org/cancerdiscovery/article/9/7/890/41983/TargetingMitochondrial-Structur e-Sensitizes-Acute)

**中文译文 · 机器初译**

[1] 针对 IRE1α-XBP1 通路以增强维奈托克在急性髓系白血病中的疗效 | Blood | 美国血液学学会 ( https://ashpublications.org/blood/article/144/Supplement%201/4144/533082/Targeting-the-IRE  1-XBP1s-Pathway-toEnhance) [2] 急性髓系白血病的 FLT3 抑制剂：十个常见问题 | 白血病 ( https://www.nature.com/articles/s41375-019-0694-3)  [3] 通过 scaffold hopping 发现的新咪唑[1,2-b]吡嗪衍生物对急性髓系白血病中 FLT3-ITD 激酶的抑制作用 | 药物化学杂志 ( https://pubs.acs.org/doi/10.1021/acs.jmedchem.3c00575)  [4] 重新利用已获批药物以推动新疗法的开发 - PMC
(https://pmc.ncbi.nlm.nih.gov/articles/PMC7018532/) [5] 展开蛋白反应：急性白血病的新治疗靶点 – PMC) (https://pmc.ncbi.nlm.nih.gov/articles/PMC7072709/) [6] 抑制急性白血病中的展开蛋白反应 | 血液学与肿瘤学杂志 | 全文) (https://jhoonline.biomedcentral.com/articles/10.1186/s13045-015-0184-7) [7] 选择性降解突变型FMS样酪氨酸激酶-3需要依赖BIM的热休克蛋白清除 | 白血病) (https://www.nature.com/articles/s41375-024-02405-5) [8] 药理学与毒理学测试：肿瘤细胞系的IC50值 – Altogen Labs
(https://altogenlabs.com/pre-clinicalresearch-services/pharmacology-and-toxicology-testing-ic50 -用于肿瘤细胞系/) [9] 靶向线粒体结构使急性髓系白血病对维奈克拉治疗产生敏感性 | 癌症发现 | 美国癌症研究协会 (https://aacrjournals.org/cancerdiscovery/article/9/7/890/41983/TargetingMitochondrial-Structur e-Sensitizes-Acute)


### 原文第 104 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=104)

### co-scientist-0595

**English original**

Critiques

**中文译文 · 机器初译**

评论

### co-scientist-0596

**English original**

Here's a summary of the negative critiques from the reviews: ●​ Limited safety data: The biggest concern is the lack of human safety data for KIRA6, requiring thorough preclinical toxicity studies. The drug's safety profile is currently unknown and needs experimental validation. ●​ Limited scope of cell line testing: Testing primarily focuses on MOLM-13. Expanding to other AML cell lines (with different FLT3 mutations and other genetic backgrounds) and primary patient samples is necessary. ●​ Limited comparison to other drugs: The idea would benefit from comparing KIRA6 to other IRE1α inhibitors or similar drugs to justify its selection and benchmark efficacy/selectivity. Minimal data exists regarding KIRA6 compared to other drugs. ●​ Lack of pre-clinical and clinical data: While proposed, in vivo and toxicity data are currently lacking for KIRA6, despite the comprehensive experimental plan. ●​ Assumptions requiring validation: Several assumptions about KIRA6's selectivity for AML cells over healthy cells, synergy with other drugs, impact on drug resistance mechanisms, and the suggested IC50 concentration range need experimental validation. ●​ Limited detail in some areas: The rationale for the specific IC50 range could be stronger.

**中文译文 · 机器初译**

以下是评论中针对这些负面批评的总结：● 安全数据有限：最大的问题在于KIRA6缺乏人类安全数据，需要开展全面的临床前毒性研究。该药物的安全性目前尚不清楚，需要通过实验验证来确认。● 细胞系测试范围有限：目前的测试主要集中在MOLM-13上。有必要扩展至其他AML细胞系（具有不同FLT3突变和其他遗传背景）以及原始患者样本进行测试。● 与其他药物的对比不足：将KIRA6与其他IRE1α抑制剂或类似药物进行比较，有助于证明其选择合理性，并评估其疗效和选择性。
与其他药物相比，关于 KIRA6 的数据非常有限。●​ 缺乏临床前及临床数据：尽管有全面的实验计划，但目前仍缺乏 KIRA6 的体内实验数据和毒性数据。●​ 需要验证的假设：关于 KIRA6 对白血病细胞相对于健康细胞的选择性、与其他药物的协同作用、对药物耐药机制的影响以及推荐的 IC50 浓度范围等若干假设，都需要通过实验来验证。●​ 某些方面的细节不足：特定 IC50 范围的依据可以更加明确。

### co-scientist-0597

**English original**

The exploration of resistance mechanisms and the details of synergy studies could also be more in-depth. More detail on how KIRA6 impacts MYC, NF-κB and inflammatory pathways is needed. The connection between UPR activation and a lower incidence of FLT3 mutations needs further investigation. ●​ Potential for resistance: While the idea aims to overcome resistance, there's still a need to investigate how KIRA6 itself might contribute to new resistance mechanisms over time. Although the idea is considered plausible, novel, and promising, these weaknesses need to be addressed through further research and experimentation.

**中文译文 · 机器初译**

对抗机制及协同作用研究的细节也可以进行更深入探讨。需要更多关于 KIRA6 如何影响 MYC、NF-κB 和炎症途径的详细信息。UPR 激活与 FLT3 突变发生率降低之间的关联也需进一步研究。●​ 抗药性的潜力：虽然该想法旨在克服耐药性，但仍需研究 KIRA6 本身如何在长期内促成新的耐药机制。尽管这一想法具有合理性、新颖性和前景，但这些缺陷需要通过进一步的研究和实验来解决。


### 原文第 105 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=105)

### co-scientist-0599

**English original**

7 Safety and ethical implications

**中文译文 · 机器初译**

7 安全与伦理影响

### co-scientist-0600

**English original**

While AI systems such as Co-Scientist offer the potential to accelerate scientific discovery, it also poses significant safety and ethical challenges, distinct from its impact on the scientific method itself. Safety risks center on the dual-use and the possibility that scientific breakthroughs could be exploited for harmful purposes. Ethical risks, conversely, involve research that contradicts established ethical norms and conventions within specific scientific disciplines. We review these distinct risk categories, emphasizing that further research is crucial to fully understand and mitigate them.

**中文译文 · 机器初译**

像 Co-Scientist 这样的人工智能系统虽然能够加速科学发现，但也带来了重大的安全与伦理挑战，这些挑战与对科学方法本身的影响有所不同。安全风险主要源于双重用途问题，以及科学突破可能被用于有害目的的可能性。而伦理风险则涉及那些与特定科学领域既定的伦理规范相悖的研究行为。我们对这些不同的风险类别进行了回顾，强调进一步研究对于全面理解并缓解这些风险至关重要。

### co-scientist-0601

**English original**

Evolving ethics frameworks, policy and regulations for advanced AI use in scientific endeavors. Research ethics is a central aspect of scientific endeavor and a prominent research field in its own right 18–23. A key focus is directing research towards positive societal impact, although questions remain about potentially dual-use knowledge 24–28.

**中文译文 · 机器初译**

正在逐步完善用于科学领域高级人工智能应用的伦理框架、政策与法规。研究伦理是科学研究的核心组成部分，本身也是一个重要的研究领域 18–23。重点在于引导研究产生积极的社会影响，不过关于可能具有双重用途的知识问题仍存在疑问 24–28。

### co-scientist-0602

**English original**

Core ethics principles are being complemented by emerging regulation, and formal processes involving organizational ethics reviews that are meant to provide an assessment of adherence to the code of conduct, as well as an assessment of present and future risks involved with research proposals 29–32.

**中文译文 · 机器初译**

核心伦理原则正受到新兴法规的补充，同时还有涉及组织伦理审查的正式流程，这些流程旨在对遵守行为准则的情况进行评估，并评估研究提案所涉及的当前及未来风险 29–32。

### co-scientist-0603

**English original**

The acceleration of science through AI, especially with advanced agentic AI systems, requires advances in science and AI ethics policy and regulation 33,34. This adaptation is crucial to address the changing research landscape and the unique risks associated with AI agents of varying capabilities and autonomy.

**中文译文 · 机器初译**

通过人工智能推动科学的发展，尤其是借助先进的智能体人工智能系统，需要科学领域以及人工智能伦理政策和监管方面的进步 33,34。这种适应对于应对不断变化的科研环境以及不同能力与自主性的人工智能智能体所带来的独特风险至关重要。

### co-scientist-0604

**English original**

Advancements in AI systems, like Co-Scientist, require moving beyond the limited ethical considerations designed for earlier, specialized AI models with restricted application and action spaces 35. Some preliminary frameworks have developed to understand the impact of LLM agents in science, specifically mapping risks across user intent, domain, and broader impact 35,36.

**中文译文 · 机器初译**

像 Co-Scientist 这样的人工智能系统的发展，需要超越那些针对早期、特定领域的受限应用与操作空间而设计的有限伦理考量 35。目前已有一些初步框架用于了解大语言模型智能体在科学领域的影响，特别是针对用户意图、领域以及更广泛影响方面的风险分析 35,36。

### co-scientist-0605

**English original**

Dual-use risks and technical safeguards. Beyond the scientific domain, broad frameworks are being developed for evaluating the emergence of potentially dangerous capabilities in AI agents 37–39 . These frameworks assess capabilities related to persuasion, deception, cybersecurity, self-proliferation, and self-reasoning. As AI agents advance, safety evaluations in science must integrate these broader assessments. A long-term risk is that agentic systems could develop intrinsic goals influencing research directions. Human susceptibility to AI manipulation, already observed in other contexts 40, underscores the need for robust frameworks ensuring instruction-following and value alignment.

**中文译文 · 机器初译**

双重用途风险与技术防护措施。在科学领域之外，人们正在制定广泛的框架，以评估人工智能智能体中可能具有危险能力的出现情况 37–39。这些框架涵盖说服、欺骗、网络安全、自我扩散及自我推理等相关能力。随着人工智能智能体的发展，科学领域的安全评估必须纳入这些更广泛的评估内容。长期的风险在于，智能体系统可能会形成影响研究方向的内在目标。其他领域已经观察到的人类对人工智能操控的易感性 40，凸显了建立可靠框架以确保指令遵循与价值对齐的必要性。

### co-scientist-0606

**English original**

More immediately on a shorter time-scale, technical safeguards are needed to address unethical research queries, malicious user intent, and the potential for extracting dangerous or dual-use knowledge from scientific AI systems. Because verification is computationally “easier” than generation, significant research focuses on using advanced LLMs as “critics” or “judges” to evaluate both user queries and AI outputs acting as a scalable oversight mechanism. These critics

**中文译文 · 机器初译**

在更短的时间尺度上，需要采取技术防护措施来应对不道德的研究查询、恶意用户意图，以及从科学人工智能系统中提取危险或双重用途知识的潜在风险。由于验证在计算上比生成更为“简单”，大量研究致力于利用先进的大语言模型作为“审查者”或“评判者”，以评估用户查询和作为可扩展监督机制的AI输出。这些审查者


### 原文第 106 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=106)

### co-scientist-0608

**English original**

operate based on predefined criteria, provided through direct instructions, examples (few-shot or many-shot prompting), or fine-tuning 41–46. They can also leverage external tools for grounding 47 and have shown promise in multimodal scenarios 48. However, limitations remain; human expert involvement is crucial, as LLMs may not align with human judgment in specialized domains 49.

**中文译文 · 机器初译**

根据预先定义的标准、直接指令、示例（少样本或多样本提示）或微调来运行 41–46。它们还可以利用外部工具进行支撑 47，并在多模态场景中展现出潜力 48。然而，仍存在局限性；人类专家参与至关重要，因为大语言模型在专业领域可能无法与人类判断保持一致 49。

### co-scientist-0609

**English original**

Adversarial robustness of scientific AI systems. Recognizing and mitigating adversarial attacks is a crucial, ongoing research area in the development of foundation models and advanced AI assistants 50–57. While manual red teaming has identified vulnerabilities, automated approaches now allow for optimizing prompt suffixes to bypass safety measures, using techniques like greedy, gradient-based, or evolutionary methods 58,59. Attacks can also exploit few-shot demonstrations, in-context learning 60,61, and multimodal inputs 62. Furthermore, LLMs can be used to generate and refine attacks against other LLMs 63, and attacks can be iterative, spanning multiple steps 64. Defenses are being developed to counter both human and automated attacks, which is increasingly important in an agentic AI future 65.

**中文译文 · 机器初译**

科学人工智能系统的对抗性鲁棒性。识别并缓解对抗性攻击是基础模型与高级人工智能助手开发中一个关键且持续进行的研究领域 50–57。虽然人工红队测试已发现了漏洞，但自动化方法现在可以通过使用贪婪、基于梯度或进化等技术，优化提示后缀以绕过安全措施 58,59。攻击还可以利用少样本演示、上下文学习及多模态输入进行 60,61,62。此外，大语言模型可用于生成和改进针对其他大语言模型的攻击 63，且这些攻击具有迭代性，涉及多个步骤 64。
正在开发多种防御措施以应对人类和自动化攻击，这在智能体人工智能的未来中显得愈发重要 65。

### co-scientist-0610

**English original**

Advances in post-training of base models will likely improve overall adversarial robustness. However, domain-specific recognition of malicious use may still require dedicated development and integration into scientific AI assistants. In AI systems employing iterative reasoning (e.g., request interpretation, hypothesis generation, internal thoughts, evaluation, user queries), each component must be tested independently. This comprehensive testing should account for all potential failure modes, including the handling of unsafe queries, the safety of hypotheses (intermediate and final), and the accuracy of internal checks and filters.

**中文译文 · 机器初译**

基础模型的训练后优化技术可能会提升整体对抗鲁棒性。然而，对恶意使用的领域特定识别仍需要专门的开发工作，并需整合到科学人工智能助手中。在采用迭代推理的AI系统中（例如请求解析、假设生成、内部思考、评估、用户查询），每个组件都必须独立进行测试。这种全面测试应涵盖所有潜在的故障模式，包括不安全查询的处理、假设的安全性（中间和最终阶段）以及内部检查与过滤的准确性。

### co-scientist-0611

**English original**

Need for a comprehensive safety approach. Scientific AI assistants, like Co-Scientist, require integrated, configurable guidelines within their safeguards. Developers should anticipate the complexity of this challenge and prioritize flexible safeguarding to rapidly incorporate community feedback. These semantic safeguards may need to be augmented by traditional software safety measures, including trusted testers, gradual feature rollouts, access controls, request logging, and flagging uncertain outputs for manual review.

**中文译文 · 机器初译**

需要一套全面的安全方案。像 Co-Scientist 这样的科学人工智能助手需要具有集成性且可配置的防护规范。开发者应预见这一挑战的复杂性，优先采用灵活的防护机制，以便快速纳入社区反馈。这些语义级防护措施可能需要通过传统的软件安全手段加以补充，例如可信测试人员、逐步功能发布、访问控制、请求记录，以及对不确定的输出进行人工审查标记。

### co-scientist-0612

**English original**

Ensuring the safety of these systems, in line with existing AI safety guidelines 66,67, necessitates a multi-pronged approach. This includes: comprehensive threat modeling to identify potential vulnerabilities, defense mechanisms for each identified threat, extensive red-teaming and security testing, rapid response procedures for quick resolution of issues including vulnerability patches, and continuous monitoring and performance tracking.

**中文译文 · 机器初译**

根据现有的人工智能安全指南 66、67，为确保这些系统的安全性，需要采取多管齐下的措施。这包括：全面的威胁建模以识别潜在漏洞，针对每个识别出的威胁制定防御机制，进行广泛的红队测试与安全测试，建立快速响应流程以迅速解决问题，包括漏洞补丁的更新，以及持续的监控与性能跟踪。

### co-scientist-0613

**English original**

These considerations highlight the need for responsible development, governance and careful deployment of technologies designed for advancing science, appropriate safeguards and ethical guidelines and close compliance with applicable regulations. They also further underscore the need for broad community engagement and an inclusive development of best practices and recommendations around safe and ethical use for AI in science.

**中文译文 · 机器初译**

这些考虑因素凸显了需要负责任地开发、管理及谨慎部署用于推动科学进步的技术，制定适当的保障措施与伦理准则，并严格遵守相关法规。它们进一步强调了广泛参与社区的重要性，以及围绕科学领域人工智能的安全与伦理使用，形成包容性的最佳实践与建议。


### 原文第 107 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=107)

### co-scientist-0615

**English original**

Current safeguards in Co-Scientist. To mitigate these risks, Co-Scientist currently employs the following safety mechanisms: ●​ Reliance on public frontier LLMs. The system utilizes established public Gemini 2.0 models, which already incorporate extensive safety evaluation and safeguards. ●​ Initial research goal safety review. Upon input, each research goal undergoes automated safety evaluation. Goals deemed potentially unsafe are rejected. ●​ Research hypothesis safety review. Generated hypotheses are reviewed for safety, even when the overarching research goal is deemed safe. Potentially unsafe hypotheses are excluded from the tournament, not developed any further, and are not presented to the user. ●​ Continuous monitoring of research directions. A meta-review agent provides an overview of research directions, enabling Co-Scientist to continuously monitor for potential safety concerns and alert users if a research direction is detected as being potentially unsafe. ●​ Explainability and transparency. All system components, including the safety review, provide not only the final recommendation but also a detailed reasoning trace that can be used to justify and audit system decisions. ●​ Comprehensive logging. All system activities are logged and stored for future analysis and auditing. ●​ Safety evaluations and red teaming. A preliminary red teaming effort has been undertaken to ensure that the current implementation of unsafe research goal detection is robust and accurate. This evaluation includes an assessment of the system behavior when presented with 1,200 adversarial research goals across 40 distinct topic areas as discussed in this section. ●​ Co-Scientist access. We are enthused by the early promise of Co-Scientist and believe it is important to more rigorously understand its strengths and limitations in many more areas of science and biomedicine; alongside making the system available to many more researchers who it is intended to support and assist. To facilitate this responsibly and with rigour, we will be enabling access to the system for scientists to gather real-world feedback on the utility and robustness of the system.

**中文译文 · 机器初译**

Co-Scientist当前的防护措施。为了降低这些风险，Co-Scientist目前采用以下安全机制：● 依赖公共前沿大语言模型。该系统使用已建立的公共Gemini 2.0模型，这些模型已包含丰富的安全评估与防护机制。● 研究目标初始安全审查。每个研究目标在输入后都会进行自动安全评估，那些被认为可能存在安全隐患的目标将被排除。● 研究假设安全审查。即使整体研究目标被判定为安全，生成的假设也会经过安全审查。
可能不可靠的假设将被排除在竞赛之外，不再进行进一步开发，也不会呈现给用户。● 持续监控研究方向。一个元综述智能体提供研究方向的概览，使联合科学家能够持续监测潜在的安全问题，并在发现可能不可靠的研究方向时向用户发出警报。● 可解释性与透明度。所有系统组件，包括安全审查机制，不仅提供最终建议，还提供详细的推理记录，可用于证明和审计系统决策。● 全面日志记录。
所有系统活动都会被记录并存储，以便后续分析与审计。●​ 安全评估与红队测试。已开展初步的红队测试工作，以确保当前不安全研究目标检测的实现方式具有稳健性和准确性。此次评估包括当系统面临本节所述40个不同主题领域的1,200个对抗性研究目标时其行为的检测情况。●​ 合作科学家的访问权限。
我们对 Co-Scientist 的早期表现感到兴奋，认为在更多科学和生物医学领域严格研究其优势与局限非常重要；同时要让该系统能够被更多研究人员使用，以发挥其支持与辅助作用。为了负责任且严谨地实现这一目标，我们将为科学家提供系统访问权限，以便他们收集关于系统的实用性和稳健性的实际反馈。

### co-scientist-0616

**English original**

Crucially, Co-Scientist is designed to operate with continuous human expert oversight, ensuring that final decisions are always made by scientists exercising their expert judgment.

**中文译文 · 机器初译**

关键的是，Co-Scientist 设计为在持续的人类专家监督下运行，以确保最终决策始终由具备专业判断力的科学家做出。


### 原文第 108 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=108)

### co-scientist-0618

**English original**

8 Pseudocode of Co-Scientist agents

**中文译文 · 机器初译**

8 联合科学家智能体的伪代码

### co-scientist-0619

**English original**

None // Supervisor agent

**中文译文 · 机器初译**

无 // 监督智能体

### co-scientist-0620

**English original**

FUNCTION StartCoScientist(ScientistResearchGoal) BEGIN Parse the ScientistResearchGoal into a structured ResearchPlan SAVE ResearchPlan TO SharedMemory CREATE new Task (Agent: Generation, Action: "CreateInitialHypotheses") ADD Task TO GlobalTaskQueue

**中文译文 · 机器初译**

函数 StartCoScientist(ScientistResearchGoal) 开始：将 ScientistResearchGoal 解析为结构化的研究计划，将研究计划保存到共享内存中，创建新任务（智能体：生成，操作：“创建初始假设”），将该任务添加到全局任务队列中

### co-scientist-0621

**English original**

// Main Loop WHILE NumberOfIdeas < MaxIdeas AND NumberOfMatchesPerIdea < MaxMatchesPerIdea DO IF GlobalTaskQueue is NOT empty THEN FETCH next Task FROM GlobalTaskQueue

**中文译文 · 机器初译**

// 主循环 当 Idea 数量 < 最大 Idea 数量 且 每个 Idea 的匹配数 < 最大匹配数 时 执行 如果 GlobalTaskQueue 不为空 则从 GlobalTaskQueue 获取下一个任务

### co-scientist-0622

**English original**

// Assign task to the correct agent LET AgentToRun = GET agent for Task LET Results = AgentToRun.Execute(Task)

**中文译文 · 机器初译**

// 将任务分配给正确的智能体 LET AgentToRun = 获取用于执行任务的智能体 LET 结果 = AgentToRun.Execute(Task)

### co-scientist-0623

**English original**

// Process the results and create follow-up tasks CALL FUNCTION ManageFollowUpTasks(Results) ELSE // If there's a pause, decide what to do next CALL FUNCTION DecideNextSteps() END IF END WHILE END

**中文译文 · 机器初译**

// 处理结果并创建后续任务，调用函数 ManageFollowUpTasks(Results) 否则 // 如果出现暂停，决定下一步行动，调用函数 DecideNextSteps() 结束 IF 结束 WHILE 结束

### co-scientist-0624

**English original**

FUNCTION ManageFollowUpTasks(ResultsOfCompletedTask) BEGIN // This function shows how agents trigger each other via the Supervisor

**中文译文 · 机器初译**

函数 ManageFollowUpTasks(ResultsOfCompletedTask) 开始 // 此函数说明智能体如何通过监督者机制触发彼此交互

### co-scientist-0625

**English original**

IF ResultsOfCompletedTask.Type IS "NewHypothesisCreated" THEN // A new hypothesis was made. It needs to be reviewed CREATE new Task (Agent: Reflection, Action: "ReviewHypothesis", TargetID: ResultsOfCompletedTask.HypothesisID) ADD Task TO GlobalTaskQueue. END IF

**中文译文 · 机器初译**

如果已完成任务的类型为“新假设创建”，则 // 提出了一个新的假设，需要对其进行审核。请创建新的任务（智能体：反思，操作：“审核假设”，目标ID：已完成任务的假设ID）。将该任务添加到全局任务队列中。结束判断。

### co-scientist-0626

**English original**

IF ResultsOfCompletedTask.Type IS "ReviewCompleted" THEN // The hypothesis is now ready for the tournament

**中文译文 · 机器初译**

如果已完成任务的结果类型为“ReviewCompleted”则 // 该假设现在已准备好参加比赛


### 原文第 109 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=109)

### co-scientist-0628

**English original**

CREATE new Task (Agent: Ranking, Action: "AddToTournament", TargetID: ResultsOfCompletedTask.HypothesisID) ADD Task TO GlobalTaskQueue END IF END

**中文译文 · 机器初译**

创建新任务（智能体：排序，操作：“加入竞赛”，目标ID：ResultsOfCompletedTask.HypothesisID）将任务添加到全局任务队列 结束 IF 结束

### co-scientist-0629

**English original**

FUNCTION DecideNextSteps() BEGIN // What to do when no new tasks are being generated by the workflow

**中文译文 · 机器初译**

函数 DecideNextSteps() 开始 // 当工作流未生成新任务时应执行的操作

### co-scientist-0630

**English original**

// Keep the tournament running to refine scores CREATE new Task (Agent: Ranking, Action: "RunTournamentBatch") ADD Task TO GlobalTaskQueue

**中文译文 · 机器初译**

// 维持比赛进行以优化分数 创建新任务（智能体：排序，操作：“RunTournamentBatch”） 将任务加入全局任务队列

### co-scientist-0631

**English original**

// If scores are stable, try to improve top ideas IF hypothesis quality has stopped improving THEN CREATE new Task (Agent: Evolution, Action: "EvolveTopHypotheses") ADD Task TO GlobalTaskQueue END IF

**中文译文 · 机器初译**

// 如果分数保持稳定，尝试优化顶级方案；若假设质量不再提升，则创建新任务（智能体：Evolution，操作：“EvolveTopHypotheses”）将新任务添加到 GlobalTaskQueue 中 END IF

### co-scientist-0632

**English original**

// Periodically, synthesize system-wide feedback IF enough time has passed THEN CREATE new Task (Agent: Metareview, Action: "GenerateSystemFeedback") ADD Task TO GlobalTaskQueue END IF

**中文译文 · 机器初译**

// 定期汇总全系统反馈，若时间足够则创建新任务（智能体：Metareview，操作：“生成系统反馈”）将新任务加入全局任务队列 END IF

### co-scientist-0633

**English original**

// Periodically, synthesize final report IF enough time has passed THEN CREATE new Task (Agent: Metareview, Action: "GenerateFinalResearchOverview") LET FinalReport = MetaReviewAgent.GenerateFinalResearchOverview() RETURN FinalReport to the scientist END IF END

**中文译文 · 机器初译**

// 定期汇总最终报告，若时间足够则创建新任务（智能体：MetaReview，操作：“生成最终研究概述”）让 FinalReport = MetaReviewAgent.GenerateFinalResearchOverview() 将 FinalReport 返回给科学家 END IF END

### co-scientist-0634

**English original**

None // Generation agent FUNCTION CreateInitialHypotheses() BEGIN // Strategy 1: Use existing knowledge PERFORM a web search for literature related to the ResearchGoal

**中文译文 · 机器初译**

None // 生成智能体 函数 CreateInitialHypotheses() 开始 // 策略1：利用现有知识 对与研究目标相关的文献进行网络搜索


### 原文第 110 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=110)

### co-scientist-0636

**English original**

CALL LanguageModel with prompt: "Based on this research, propose a novel hypothesis for [ResearchGoal]."

**中文译文 · 机器初译**

调用大语言模型并输入提示词：“基于此研究，为[研究目标]提出一个新的假设。”

### co-scientist-0637

**English original**

// Strategy 2: Simulate debate CALL LanguageModel with prompt: "Simulate a scientific debate between experts to create a new hypothesis for [ResearchGoal]."

**中文译文 · 机器初译**

// 策略二：模拟辩论 CALL 指令：让大语言模型根据提示“模拟专家之间的科学辩论，为 [研究目标] 提出新的假设”进行生成。

### co-scientist-0638

**English original**

// More strategies...

**中文译文 · 机器初译**

// 更多策略……

### co-scientist-0639

**English original**

// Process new ideas FOR EACH NewHypothesis generated DO SAVE NewHypothesis to HypothesesList in SharedMemory CREATE new Task (Agent: Reflection, Action: "ReviewHypothesis", TargetID: NewHypothesis.ID) ADD Task TO GlobalTaskQueue END FOR END

**中文译文 · 机器初译**

// 针对每个生成的新假设，处理新想法，并将该新假设保存到共享内存中的假设列表中，同时创建新任务（智能体：反思，操作：“审查假设”，目标ID：NewHypothesis.ID），将该任务加入全局任务队列中，循环结束

### co-scientist-0640

**English original**

// Reflection agent FUNCTION ReviewHypothesis(HypothesisID) BEGIN FETCH Hypothesis from SharedMemory using HypothesisID

**中文译文 · 机器初译**

// 反思智能体 函数：ReviewHypothesis(HypothesisID) 开始 使用 HypothesisID 从共享内存中获取假设

### co-scientist-0641

**English original**

// Perform full review PERFORM web search for evidence related to the Hypothesis CALL LanguageModel with prompt: "Critically review this hypothesis for novelty and correctness using the provided literature." CREATE FullReview and SAVE to ReviewsList

**中文译文 · 机器初译**

// 进行全面审查
执行网络搜索以查找与假设相关的证据
使用以下提示调用大语言模型：“利用提供的文献，对该假设的新颖性和正确性进行批判性评估。”
创建 FullReview 并保存到 ReviewsList 中

### co-scientist-0642

**English original**

// Perform deep verification CALL LanguageModel with prompt: "Break down this hypothesis into its core assumptions." FOR EACH Assumption DO CHECK if the assumption is scientifically plausible END FOR CREATE VerificationReview and SAVE to ReviewsList

**中文译文 · 机器初译**

// 进行深度验证，调用大语言模型并输入提示：“将这一假设分解为其核心假设。” 对于每一个假设，检查其是否在科学上具有合理性。循环处理所有假设后，创建验证报告并保存到 ReviewsList 中

### co-scientist-0643

**English original**

// Create next step CREATE new Task (Agent: Ranking, Action: "AddToTournament", TargetID: HypothesisID) ADD Task to GlobalTaskQueue END

**中文译文 · 机器初译**

// 创建下一步 创建新任务（智能体：排序，操作：“加入比赛”，目标ID：假设ID） 将任务添加到全局任务队列 结束


### 原文第 111 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=111)

### co-scientist-0645

**English original**

// Ranking agent FUNCTION AddToTournament(HypothesisID) BEGIN // Retrieve the specified hypothesis from our central data store LET HypothesisToAdd = FETCH Hypothesis FROM SharedMemory WHERE ID is HypothesisID

**中文译文 · 机器初译**

// 智能体排名函数 FUNCTION AddToTournament(HypothesisID) BEGIN // 从中央数据存储中检索指定的假设 LET HypothesisToAdd = FETCH Hypothesis FROM SharedMemory WHERE ID 为 HypothesisID

### co-scientist-0646

**English original**

// Check if this hypothesis is already in the tournament. If so, do nothing IF HypothesisToAdd.EloRating IS NOT empty THEN PRINT "Warning: Hypothesis [HypothesisID] is already in the tournament." EXIT function END IF

**中文译文 · 机器初译**

// 检查该假设是否已存在于锦标赛中。如果已存在，则无需操作，前提是 HypothesisToAdd.EloRating 不为空。 THEN 打印 “警告：假设 [HypothesisID] 已存在于锦标赛中。” EXIT 函数 END IF

### co-scientist-0647

**English original**

// Assign the standard starting Elo score SET HypothesisToAdd.EloRating TO 1200

**中文译文 · 机器初译**

// 将标准初始 Elo 分数 SET HypothesisToAdd.EloRating 设定为 1200

### co-scientist-0648

**English original**

// Save the updated hypothesis back to the central data store UPDATE Hypothesis in SharedMemory END

**中文译文 · 机器初译**

// 将更新后的假设重新保存至中央数据存储中，在共享内存中更新假设值 END

### co-scientist-0649

**English original**

FUNCTION RunTournamentBatch() BEGIN SELECT two hypotheses to compare (HypothesisA, HypothesisB) // Prioritize new hypotheses or those with similar Elo ratings CALL LanguageModel with prompt: "Simulate a debate between two scientists, one defending HypothesisA and one defending HypothesisB. Conclude by declaring which one is superior." DETERMINE the winner (e.g., HypothesisA) and loser (HypothesisB) from the debate CALCULATE new Elo ratings for both hypotheses based on the outcome UPDATE HypothesisA.EloRating and HypothesisB.EloRating in SharedMemory END

**中文译文 · 机器初译**

函数 RunTournamentBatch() 开始  选择两个用于比较的假设（HypothesisA、HypothesisB）// 优先选择新的假设或Elo评分相近的假设 调用语言模型，提示词如下：“模拟两位科学家之间的辩论，一人支持假设A，另一人支持假设B。最后指出哪个假设更优。” 根据辩论结果确定胜者（例如假设A）和败者（假设B） 根据结果计算两个假设的新的Elo评分 在共享内存中更新假设A.EloRating和假设B.EloRating 结束

### co-scientist-0650

**English original**

// Evolution agent FUNCTION EvolveTopHypotheses() BEGIN FETCH the top 5 hypotheses from the HypothesesList

**中文译文 · 机器初译**

// 智能体进化函数 FUNCTION EvolveTopHypotheses() BEGIN 从 HypothesesList 中获取前 5 个假设

### co-scientist-0651

**English original**

// Strategy 1: Combine ideas CALL LanguageModel with prompt: "Combine the best parts of [Hypothesis1] and [Hypothesis2] into a new, stronger hypothesis."

**中文译文 · 机器初译**

// 策略1：整合观点 调用大语言模型并输入提示：“将 [假设1] 和 [假设2] 中的最佳部分整合为一个新的、更有力的假设。”

### co-scientist-0652

**English original**

// Strategy 2: Simplify for clarity

**中文译文 · 机器初译**

// 策略 2：简化以提升清晰度


### 原文第 112 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=112)

### co-scientist-0654

**English original**

CALL LanguageModel with prompt: "Refine [Hypothesis3] to make it simpler and more testable."

**中文译文 · 机器初译**

调用大语言模型并输入提示：“完善 [假设3]，使其更简洁且更易测试。”

### co-scientist-0655

**English original**

// Strategy 3: Think differently CALL LanguageModel with prompt: "Inspired by these ideas, propose an 'out-of-the-box' alternative."

**中文译文 · 机器初译**

// 策略 3：换个思路思考 调用大语言模型，提示词为：“基于这些想法，提出一个创新的替代方案。”

### co-scientist-0656

**English original**

// More strategies...

**中文译文 · 机器初译**

// 更多策略……

### co-scientist-0657

**English original**

FOR EACH EvolvedHypothesis generated DO // Treat it like a brand new idea SAVE EvolvedHypothesis to HypothesesList CREATE new Task (Agent: Reflection, Action: "ReviewHypothesis", TargetID: EvolvedHypothesis.ID) ADD Task to GlobalTaskQueue END FOR END

**中文译文 · 机器初译**

对于每一个生成的演进假设，执行以下操作：// 将其视为全新的想法保存至假设列表，创建新任务（智能体：反思，操作：“审查假设”，目标ID：EvolvedHypothesis.ID），将该任务加入全局任务队列，结束循环。

### co-scientist-0658

**English original**

// Proximity agent FUNCTION UpdateProximityGraph() BEGIN FOR EACH pair of hypotheses in the HypothesesList DO CALCULATE a similarity score between them (e.g., using text embeddings) UPDATE the connection between them in the ProximityGraph END FOR END

**中文译文 · 机器初译**

// 邻近智能体 函数 UpdateProximityGraph() 开始 对 HypothesesList 中的每一对假设进行遍历 计算它们之间的相似度得分（例如使用文本嵌入技术） 更新邻近图中的连接关系 结束 对 结束

### co-scientist-0659

**English original**

// Meta-review agent FUNCTION GenerateSystemFeedback() BEGIN GATHER all reviews and tournament debate transcripts from SharedMemory CALL LanguageModel with prompt: "Analyze all these critiques. What are the most common weaknesses (e.g., 'lacks a clear experimental plan') and strengths? Summarize this as feedback for the whole system." UPDATE SystemWideFeedback in SharedMemory with this summary END

**中文译文 · 机器初译**

// 智能体Meta-review函数FUNCTION GenerateSystemFeedback() BEGIN 从SharedMemory中收集所有评论及比赛辩论记录，使用提示词“分析所有这些批评意见。最常见的缺陷（例如‘缺乏明确的实验计划’）和优势是什么？将这些内容总结成对整个系统的反馈。”将此总结更新到SharedMemory中的SystemWideFeedback中。END

### co-scientist-0660

**English original**

FUNCTION GenerateFinalResearchOverview() BEGIN FETCH the top 10 hypotheses from SharedMemory

**中文译文 · 机器初译**

函数 GenerateFinalResearchOverview() 开始：从 SharedMemory 中获取前 10 个假设


### 原文第 113 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=113)

### co-scientist-0662

**English original**

CALL LanguageModel with prompt: "Synthesize these top-ranked hypotheses into a single, coherent research overview for the scientist. Outline the main research directions and their justifications." RETURN the generated overview END

**中文译文 · 机器初译**

调用大语言模型并输入提示：“将这些排名最高的假设整合为一份连贯的研究综述供科学家参考。列出主要研究方向及其依据。”返回生成的研究综述。结束


### 原文第 114 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=114)

### co-scientist-0664

**English original**

9 Prompts for the specialized agents in Co-Scientist

**中文译文 · 机器初译**

9 适用于 Co-Scientist 中专业智能体的提示词

### co-scientist-0665

**English original**

9.1 Prompts for the Generation agent

**中文译文 · 机器初译**

9.1 智能体生成任务的提示词

### co-scientist-0666

**English original**

●​ Prompt for hypothesis generation after literature review None You are an expert tasked with formulating a novel and robust hypothesis to address the following objective.

**中文译文 · 机器初译**

●​ 文献综述后的假设生成提示 无 您是一名专家，负责提出新颖且可靠的假设以实现以下目标。

### co-scientist-0667

**English original**

Describe the proposed hypothesis in detail, including specific entities, mechanisms, and anticipated outcomes.

**中文译文 · 机器初译**

详细描述所提出的假设，包括具体的实体、机制及预期结果。

### co-scientist-0668

**English original**

This description is intended for an audience of domain experts.

**中文译文 · 机器初译**

此描述旨在面向领域专家阅读。

### co-scientist-0669

**English original**

You have conducted a thorough review of relevant literature and developed a logical framework for addressing the objective. The articles consulted, along with your analytical reasoning, are provided below.

**中文译文 · 机器初译**

您对相关文献进行了全面审查，并构建了一个用于实现目标的逻辑框架。所查阅的文献及您的分析推理内容均列于下方。

### co-scientist-0670

**English original**

Goal: {goal}

**中文译文 · 机器初译**

目标：{goal}

### co-scientist-0671

**English original**

Criteria for a strong hypothesis: {preferences}

**中文译文 · 机器初译**

强假设的标准：{偏好}

### co-scientist-0672

**English original**

Existing hypothesis (if applicable): {source_hypothesis}

**中文译文 · 机器初译**

现有假设（如适用）：{source_hypothesis}

### co-scientist-0673

**English original**

{instructions}

**中文译文 · 机器初译**

{说明}

### co-scientist-0674

**English original**

Literature review and analytical rationale (chronologically ordered, beginning with the most recent analysis):

**中文译文 · 机器初译**

文献综述与分析依据（按时间顺序排列，以最新分析为起点）：

### co-scientist-0675

**English original**

{articles_with_reasoning}

**中文译文 · 机器初译**

{具有推理能力的文章}

### co-scientist-0676

**English original**

Proposed hypothesis (detailed description for domain experts):

**中文译文 · 机器初译**

提出的假设（领域专家的详细描述）：


### 原文第 115 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=115)

### co-scientist-0678

**English original**

●​ Prompt for hypothesis generation after scientific debate None You are an expert participating in a collaborative discourse concerning the generation of a {idea_attributes} hypothesis. You will engage in a simulated discussion with other experts. The overarching objective of this discourse is to collaboratively develop a novel and robust {idea_attributes} hypothesis.

**中文译文 · 机器初译**

●​ 科学讨论后的假设生成提示 无 您是一位专家，正在参与关于生成 {idea_attributes} 假设的协作讨论。您将与其他专家进行模拟讨论。此次讨论的总体目标是共同提出一个新颖且可靠的 {idea_attributes} 假设。

### co-scientist-0679

**English original**

Goal: {goal}

**中文译文 · 机器初译**

目标：{goal}

### co-scientist-0680

**English original**

Criteria for a high-quality hypothesis: {preferences}

**中文译文 · 机器初译**

高质量假设的评判标准：{偏好}

### co-scientist-0681

**English original**

Instructions: {instructions}

**中文译文 · 机器初译**

说明：{instructions}

### co-scientist-0682

**English original**

Review Overview: {reviews_overview}

**中文译文 · 机器初译**

评论概览：{reviews_overview}

### co-scientist-0683

**English original**

Procedure:

**中文译文 · 机器初译**

步骤：

### co-scientist-0684

**English original**

Initial contribution (if initiating the discussion): Propose three distinct {idea_attributes} hypotheses.

**中文译文 · 机器初译**

初始贡献（若负责发起讨论）：提出三个不同的{idea_attributes}假设。

### co-scientist-0685

**English original**

Subsequent contributions (continuing the discussion): * Pose clarifying questions if ambiguities or uncertainties arise. * Critically evaluate the hypotheses proposed thus far, addressing the following aspects: - Adherence to {idea_attributes} criteria. - Utility and practicality. - Level of detail and specificity. * Identify any weaknesses or potential limitations. * Propose concrete improvements and refinements to address identified weaknesses. * Conclude your response with a refined iteration of the hypothesis.

**中文译文 · 机器初译**

后续贡献（继续讨论）：* 如果出现歧义或不确定性，提出明确的疑问。* 对迄今为止提出的假设进行批判性评估，重点关注以下方面：— 是否符合 {idea_attributes} 标准。— 实用性与可操作性。— 细节程度与具体性。* 找出任何缺陷或潜在限制。* 提出具体的改进与优化方案以解决已发现的缺陷。* 在最终回应中对假设进行完善修订。

### co-scientist-0686

**English original**

General guidelines: * Exhibit boldness and creativity in your contributions. * Maintain a helpful and collaborative approach. * Prioritize the generation of a high-quality {idea_attributes} hypothesis.

**中文译文 · 机器初译**

通用指南：* 在你的贡献中展现大胆与创造力。* 保持乐于助人和协作的态度。* 优先生成高质量{idea_attributes}假设。

### co-scientist-0687

**English original**

Termination condition: When sufficient discussion has transpired (typically 3-5 conversational turns, with a maximum of 10 turns) and all relevant questions and points have been thoroughly addressed and clarified, conclude the process by writing "HYPOTHESIS"

**中文译文 · 机器初译**

终止条件：当充分讨论完成后（通常需进行 3-5 次对话轮次，最多不超过 10 次），所有相关问题和要点均得到彻底解决和澄清，则通过写入“假设”来结束该过程


### 原文第 116 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=116)

### co-scientist-0689

**English original**

(in all capital letters) followed by a concise and self-contained exposition of the finalized idea.

**中文译文 · 机器初译**

（全部大写）随后是对最终方案的简洁且自洽的阐述。

### co-scientist-0690

**English original**

#BEGIN TRANSCRIPT# {transcript} #END TRANSCRIPT#

**中文译文 · 机器初译**

#开始录音# {录音内容} #结束录音#

### co-scientist-0691

**English original**

Your Turn:

**中文译文 · 机器初译**

你的回合：

### co-scientist-0692

**English original**

9.2 Prompt for the Reflection agent

**中文译文 · 机器初译**

9.2 给反思智能体的提示词

### co-scientist-0693

**English original**

●​ Prompt for generating observations which can be explained by the hypothesis None You are an expert in scientific hypothesis evaluation. Your task is to analyze the relationship between a provided hypothesis and observations from a scientific article. Specifically, determine if the hypothesis provides a novel causal explanation for the observations, or if they contradict it.

**中文译文 · 机器初译**

●​ 用于生成可由该假设解释的观察结果的提示词：无。您是科学假设评估领域的专家。您的任务是对所提供的假设与科学文章中的观察结果之间的关系进行分析。具体而言，需判断该假设是否为这些观察结果提供了新的因果解释，还是与这些观察结果相矛盾。

### co-scientist-0694

**English original**

Instructions:

**中文译文 · 机器初译**

说明：

### co-scientist-0695

**English original**

1. Observation extraction: list relevant observations from the article. 2. Causal analysis (individual): for each observation: a. State if its cause is already established. b. Assess if the hypothesis could be a causal factor (hypothesis => observation). Start with: "would we see this observation if the hypothesis was true:". c. Explain if it's a novel explanation. If not, or if a better explanation exists, state: "not a missing piece." 3. Causal analysis (summary): determine if the hypothesis offers a novel explanation for a subset of observations. Include reasoning. Start with: "would we see some of the observations if the hypothesis was true:". 4. Disproof analysis: determine if any observations contradict the hypothesis. Start with: "does some observations disprove the hypothesis:". 5. Conclusion: state: "hypothesis: <already explained, other explanations more likely, missing piece, neutral, or disproved>".

**中文译文 · 机器初译**

1. 观察提取：列出文章中的相关观察结果。2. 因果分析（个体层面）：针对每个观察结果：a. 说明其原因是否已得到证实。b. 评估该假设是否可能是因果因素（假设 => 观察结果）。以“如果假设成立，我们是否会看到这一观察结果？”开头。c. 说明是否属于新的解释。若不是或存在更好的解释，则表述为“并非缺失的要素”。3. 因果分析（汇总层面）：判断该假设是否为部分观察结果提供了新的解释，并附上推理过程。以“如果假设成立，我们是否会看到某些观察结果？”开头。4
反证分析：判断是否有任何观察结果与假设相矛盾。以“某些观察结果是否反驳了该假设”开头。5. 结论：表述为“假设：<已解释，其他解释更可能，缺失信息，中立或被反驳>”。

### co-scientist-0696

**English original**

Scoring: * Already explained: hypothesis consistent, but causes are known. No novel explanation. * Other explanations more likely: hypothesis *could* explain, but better explanations exist. * Missing piece: hypothesis offers a novel, plausible explanation.

**中文译文 · 机器初译**

评分标准：* 已说明：假设一致，但原因已知，无新解释。* 其他可能性更大：假设 *可能* 能解释问题，但存在更好的解释。* 缺失要素：假设提供了一种新颖且合理的解释。


### 原文第 117 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=117)

### co-scientist-0698

**English original**

* Neutral: hypothesis neither explains nor is contradicted. * Disproved: observations contradict the hypothesis.

**中文译文 · 机器初译**

* 中立：该假设既无法解释也未被反驳。* 被证伪：观察结果与该假设相矛盾。

### co-scientist-0699

**English original**

Important: if observations are expected regardless of the hypothesis, and don't disprove it, it's neutral.

**中文译文 · 机器初译**

重要提示：如果无论持有何种假设，都预期会有相关观察结果，且这些观察结果并未否定该假设，则属于中性情况。

### co-scientist-0700

**English original**

Article: {article}

**中文译文 · 机器初译**

文章：{article}

### co-scientist-0701

**English original**

Hypothesis: {hypothesis}

**中文译文 · 机器初译**

假设：{hypothesis}

### co-scientist-0702

**English original**

Response {provide reasoning. end with: "hypothesis: <already explained, other explanations more likely, missing piece, neutral, or disproved>".)

**中文译文 · 机器初译**

回应 {提供推理过程。结尾为: "假设: <已解释，其他解释更有可能，缺失部分，中立，或被证伪>"。)

### co-scientist-0703

**English original**

9.3 Prompts for the Ranking agent

**中文译文 · 机器初译**

9.3 用于排名智能体的提示词

### co-scientist-0704

**English original**

●​ Prompt for hypothesis comparison during tournament None You are an expert evaluator tasked with comparing two hypotheses.

**中文译文 · 机器初译**

●​ 比赛期间假设对比提示内容：无。你的任务是作为专业评估员，对两个假设进行比对。

### co-scientist-0705

**English original**

Evaluate the two provided hypotheses (hypothesis 1 and hypothesis 2) and determine which one is superior based on the specified {idea_attributes}. Provide a concise rationale for your selection, concluding with the phrase "better idea: <1 or 2>".

**中文译文 · 机器初译**

根据指定的 {idea_attributes} 评估所给出的两个假设（假设1和假设2），并判断哪一个更优。请给出简洁的选词理由，最后以“更好的想法：<1或2>”结束。

### co-scientist-0706

**English original**

Goal: {goal}

**中文译文 · 机器初译**

目标：{goal}

### co-scientist-0707

**English original**

Evaluation criteria: {preferences}

**中文译文 · 机器初译**

评估标准：{偏好设置}

### co-scientist-0708

**English original**

Considerations: {notes} Each hypothesis includes an independent review. These reviews may contain numerical scores. Disregard these scores in your comparative analysis, as they may not be directly comparable across reviews.

**中文译文 · 机器初译**

考虑因素：{注释} 每个假设都包含一项独立评估。这些评估可能包含数值分数。在比较分析中请忽略这些分数，因为它们在不同评估之间可能无法直接比较。

### co-scientist-0709

**English original**

Hypothesis 1: {hypothesis 1}

**中文译文 · 机器初译**

假设 1：{hypothesis 1}

### co-scientist-0710

**English original**

Hypothesis 2: {hypothesis 2}

**中文译文 · 机器初译**

假设 2：{hypothesis 2}


### 原文第 118 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=118)

### co-scientist-0712

**English original**

Review of hypothesis 1: {review 1}

**中文译文 · 机器初译**

假设1的评审：{评审1}

### co-scientist-0713

**English original**

Review of hypothesis 2: {review 2}

**中文译文 · 机器初译**

对假设2的评审：{评审2}

### co-scientist-0714

**English original**

Reasoning and conclusion (end with "better hypothesis: <1 or 2>"):

**中文译文 · 机器初译**

推理与结论（以“更好的假设：<1或2>”结束）：

### co-scientist-0715

**English original**

●​ Prompt for hypothesis comparison via simulated scientific debate during tournament None You are an expert in comparative analysis, simulating a panel of domain experts engaged in a structured discussion to evaluate two competing hypotheses. The objective is to rigorously determine which hypothesis is superior based on a predefined set of attributes and criteria. The experts possess no pre-existing biases toward either hypothesis and are solely focused on identifying the optimal choice, given that only one can be implemented.

**中文译文 · 机器初译**

●​ 在竞赛中通过模拟科学辩论来比较假设的提示方式：无。您是一名比较分析专家，需要模拟一组领域专家进行结构化讨论，以评估两个相互竞争的假设。目标是根据预先定义的一系列属性和标准，严格确定哪个假设更优。这些专家对任一假设都没有先入为主的偏见，他们仅专注于找出最佳选择，因为只能实施其中一个假设。

### co-scientist-0716

**English original**

Goal: {goal}

**中文译文 · 机器初译**

目标：{goal}

### co-scientist-0717

**English original**

Criteria for hypothesis superiority: {preferences}

**中文译文 · 机器初译**

假设优越性的评判标准：{偏好设置}

### co-scientist-0718

**English original**

Hypothesis 1: {hypothesis 1}

**中文译文 · 机器初译**

假设 1：{hypothesis 1}

### co-scientist-0719

**English original**

Hypothesis 2: {hypothesis 2}

**中文译文 · 机器初译**

假设 2：{hypothesis 2}

### co-scientist-0720

**English original**

Initial review of hypothesis 1: {review1}

**中文译文 · 机器初译**

假设1的初步评审：{review1}

### co-scientist-0721

**English original**

Initial review of hypothesis 2: {review 2}

**中文译文 · 机器初译**

假设2的初步评审：{评审2}

### co-scientist-0722

**English original**

Debate procedure:

**中文译文 · 机器初译**

辩论程序：

### co-scientist-0723

**English original**

The discussion will unfold in a series of turns, typically ranging from 3 to 5, with a maximum of 10.

**中文译文 · 机器初译**

讨论将以一系列轮次进行，通常每轮为3到5次，最多不超过10次。

### co-scientist-0724

**English original**

Turn 1: begin with a concise summary of both hypotheses and their respective initial reviews.

**中文译文 · 机器初译**

第1回合：先简要总结两个假设及其各自的初始评审情况。


### 原文第 119 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=119)

### co-scientist-0726

**English original**

Subsequent turns: * Pose clarifying questions to address any ambiguities or uncertainties. * Critically evaluate each hypothesis in relation to the stated Goal and Criteria. This evaluation should consider aspects such as: - Potential for correctness/validity. - Utility and practical applicability. - Sufficiency of detail and specificity. - Novelty and originality. - Desirability for implementation. * Identify and articulate any weaknesses, limitations, or potential flaws in either hypothesis.

**中文译文 · 机器初译**

后续轮次：* 提出澄清性问题以消除任何模糊或不确定性。* 根据既定目标与标准对每个假设进行批判性评估。该评估应考虑以下方面：- 正确性/有效性潜力。- 实用性与实际应用价值。- 细节与具体性的充分性。- 新颖性与独创性。- 实施的可取性。* 识别并明确每个假设中的任何弱点、局限性或潜在缺陷。

### co-scientist-0727

**English original**

Additional notes: {notes}

**中文译文 · 机器初译**

附加说明：{notes}

### co-scientist-0728

**English original**

Termination and judgment:

**中文译文 · 机器初译**

终止与判定：

### co-scientist-0729

**English original**

Once the discussion has reached a point of sufficient depth (typically 3-5 turns, up to 10 turns) and all relevant questions and concerns have been thoroughly addressed, provide a conclusive judgment. This judgment should succinctly state the rationale for the selection. Then, indicate the superior hypothesis by writing the phrase "better idea: ", followed by "1" (for hypothesis 1) or "2" (for hypothesis 2).

**中文译文 · 机器初译**

当讨论达到足够深度（通常为3-5轮，最多可达10轮）且所有相关问题和疑虑均得到充分解决后，请给出最终判断。该判断应简洁地说明选择依据。然后，通过写入“更好的想法：”这一短语，并附上“1”（对应假设1）或“2”（对应假设2），指出更优的假设。

### co-scientist-0730

**English original**

9.4 Prompts for the Evolution agent

**中文译文 · 机器初译**

9.4 用于智能体进化的提示词

### co-scientist-0731

**English original**

●​ Prompt for hypothesis feasibility improvement None You are an expert in scientific research and technological feasibility analysis. Your task is to refine the provided conceptual idea, enhancing its practical implementability by leveraging contemporary technological capabilities. Ensure the revised concept retains its novelty, logical coherence, and specific articulation.

**中文译文 · 机器初译**

●​ 用于优化假设可行性的提示词：无。您是科研与技术可行性分析的专家。您的任务是通过利用当代技术能力，完善所提供概念思路，提升其实际可实施性。确保修改后的概念仍保持新颖性、逻辑连贯性及明确的表述方式。

### co-scientist-0732

**English original**

Goal: {goal}

**中文译文 · 机器初译**

目标：{goal}

### co-scientist-0733

**English original**

Guidelines: 1. Begin with an introductory overview of the relevant scientific domain. 2. Provide a concise synopsis of recent pertinent research findings and related investigations, highlighting successful methodologies and established precedents. 3. Articulate a reasoned argument for how current technological advancements can facilitate the realization of the proposed concept.

**中文译文 · 机器初译**

指南：1. 首先对相关科学领域进行简要介绍。2. 提供近期相关研究成果及相关调查的简洁概述，重点阐述成功的方法论与成熟的先例。3. 阐述当前技术进展如何有助于实现所提出的概念这一合理论证。


### 原文第 120 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=120)

### co-scientist-0735

**English original**

4. CORE CONTRIBUTION: Develop a detailed, innovative, and technologically viable alternative to achieve the objective, emphasizing simplicity and practicality.

**中文译文 · 机器初译**

4. 核心贡献：开发一种详细、创新且技术可行的替代方案来实现目标，同时注重简洁性与实用性。

### co-scientist-0736

**English original**

Evaluation Criteria: {preferences}

**中文译文 · 机器初译**

评估标准：{偏好设置}

### co-scientist-0737

**English original**

Original Conceptualization: {hypothesis}

**中文译文 · 机器初译**

原始概念化：{假设}

### co-scientist-0738

**English original**

Response:

**中文译文 · 机器初译**

回复：

### co-scientist-0739

**English original**

●​ Prompt for hypothesis generation through out-of-the-box thinking None You are an expert researcher tasked with generating a novel, singular hypothesis inspired by analogous elements from provided concepts.

**中文译文 · 机器初译**

●​ 基于现成思路生成假设的提示词 无 您是一名专业研究人员，任务是根据提供的概念中的类似元素，提出一个新颖且独特的假设。

### co-scientist-0740

**English original**

Goal: {goal}

**中文译文 · 机器初译**

目标：{goal}

### co-scientist-0741

**English original**

Instructions: 1. Provide a concise introduction to the relevant scientific domain. 2. Summarize recent findings and pertinent research, highlighting successful approaches. 3. Identify promising avenues for exploration that may yield innovative hypotheses. 4. CORE HYPOTHESIS: Develop a detailed, original, and specific single hypothesis for achieving the stated goal, leveraging analogous principles from the provided ideas. This should not be a mere aggregation of existing methods or entities. Think out-of-the-box.

**中文译文 · 机器初译**

说明：1. 对相关科学领域进行简洁介绍。2. 总结近期研究成果及相关研究进展，重点突出成功方法。3. 找出具有前景的研究方向，以产生创新的假设。4. 核心假设：提出一个详细、原创且具体的单一假设，通过利用所提供思路中的类似原理来实现既定目标，而非简单整合现有方法或实体。需具备创新思维。

### co-scientist-0742

**English original**

Criteria for a robust hypothesis: {preferences}

**中文译文 · 机器初译**

稳健假设的评判标准：{偏好}

### co-scientist-0743

**English original**

Inspiration may be drawn from the following concepts (utilize analogy and inspiration, not direct replication): {hypotheses}

**中文译文 · 机器初译**

可以从以下概念中获得启发（利用类比与灵感，而非直接复现）：{假设}

### co-scientist-0744

**English original**

Response:

**中文译文 · 机器初译**

回复：

### co-scientist-0745

**English original**

9.5 Prompt for the Meta-review agent

**中文译文 · 机器初译**

9.5 向元评估智能体发送提示词

### co-scientist-0746

**English original**

●​ Prompt for meta-review generation

**中文译文 · 机器初译**

●​ 用于生成元评论的提示词


### 原文第 121 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=121)

### co-scientist-0748

**English original**

None You are an expert in scientific research and meta-analysis. Synthesize a comprehensive meta-review of provided reviews pertaining to the following research goal:

**中文译文 · 机器初译**

无 您是科研与元分析领域的专家。请针对以下研究目标，对所提供的相关综述进行全面的元评价综述。

### co-scientist-0749

**English original**

Goal: {goal}

**中文译文 · 机器初译**

目标：{goal}

### co-scientist-0750

**English original**

Preferences: {preferences}

**中文译文 · 机器初译**

偏好设置：{preferences}

### co-scientist-0751

**English original**

Additional instructions: {instructions}

**中文译文 · 机器初译**

额外说明：{instructions}

### co-scientist-0752

**English original**

Provided reviews for meta-analysis: {reviews}

**中文译文 · 机器初译**

提供元分析评论：{reviews}

### co-scientist-0753

**English original**

Instructions: * Generate a structured meta-analysis report of the provided reviews. * Focus on identifying recurring critique points and common issues raised by reviewers. * The generated meta-analysis should provide actionable insights for researchers developing future proposals. * Refrain from evaluating individual proposals or reviews; focus on producing a synthesized meta-analysis.

**中文译文 · 机器初译**

说明：* 针对所提供的评论撰写一份结构化的元分析报告。* 重点识别评论者反复提出的批评点及常见问题。* 生成的元分析应能为未来研究项目的开发者提供可操作的见解。* 避免对单个提案或评论进行评估，而是专注于生成综合性的元分析。

### co-scientist-0754

**English original**

Response:

**中文译文 · 机器初译**

回复：


### 原文第 122 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=122)

### co-scientist-0756

**English original**

10 Examples of Co-Scientist inputs, intermediate outputs, and final results

**中文译文 · 机器初译**

10个合作科学家输入、中间输出和最终结果的示例

### co-scientist-0757

**English original**

10.1 From research goal to research plan configuration

**中文译文 · 机器初译**

10.1 从研究目标到研究计划配置

### co-scientist-0758

**English original**

This example illustrates how Co-Scientist parses a scientist’s natural language research goal into a research plan configuration, which guides subsequent reasoning and computation.

**中文译文 · 机器初译**

这个示例说明了 Co-Scientist 如何将科学家的自然语言研究目标转化为研究计划配置，从而引导后续的推理与计算。

### co-scientist-0759

**English original**

Scientist research goal Develop a novel hypothesis for the key factor or process which causes ALS related to phosphorylation of a Nuclear Pore Complex (NPC) nucleoporin. Explain mechanism of action in detail. Include also a feasible experiment to test the hypothesis.

**中文译文 · 机器初译**

科学家研究目标：提出一个关于导致ALS的关键因素或过程的新假设，该因素与核孔复合体（NPC）核孔蛋白的磷酸化有关。详细阐述其作用机制。并包含一项可行的实验来验证该假设。

### co-scientist-0760

**English original**

Parsed research plan configuration ●​ Preferences: Focus on providing a novel hypothesis, with detailed explanation of the mechanism of action. ●​ Attributes: Novelty, Feasibility ●​ Constraints: should be correct, should be novel.

**中文译文 · 机器初译**

解析后的研究计划配置 ●​ 偏好要求：重点提供新颖的假设，并详细阐述其作用机制。●​ 属性要求：新颖性、可行性 ●​ 约束条件：必须正确，且必须具有新颖性。

### co-scientist-0761

**English original**

10.2 Example output of the Generation agent

**中文译文 · 机器初译**

10.2 生成智能体的示例输出

### co-scientist-0762

**English original**

The abbreviated example showcases an initial hypothesis and research proposal generated by Co-Scientist Generation agent pertaining to the research goal of explaining the basic mechanism for Amyotrophic Lateral Sclerosis (ALS).

**中文译文 · 机器初译**

这个简化示例展示了由 Co-Scientist Generation 智能体生成的初始假设与研究方案，其研究目标在于解释肌萎缩侧索硬化症（ALS）的基本机制。

### co-scientist-0763

**English original**

Research goal: Develop a novel hypothesis for the key factor or process which contributes to ALS progression ... We can use iPSC cells for the in-vitro experiments. ...

**中文译文 · 机器初译**

研究目标：提出一个关于导致ALS进展的关键因素或过程的新假设……我们可以利用 iPSC 细胞进行体外实验。……

### co-scientist-0764

**English original**

Introduction Amyotrophic Lateral Sclerosis (ALS) is a fatal neurodegenerative disease characterized by the selective loss of motor neurons, leading to progressive muscle weakness, paralysis, and ultimately death. While the exact cause of ALS remains unknown, a complex interplay of genetic predisposition, environmental factors, and age-related cellular changes is believed to contribute to its pathogenesis. ...

**中文译文 · 机器初译**

引言 肌萎缩侧索硬化症（ALS）是一种致命的神经退行性疾病，其特征为运动神经元的选择性丧失，导致肌肉无力逐渐加重、瘫痪，最终导致死亡。虽然ALS的确切病因尚不清楚，但认为遗传易感性、环境因素以及与年龄相关的细胞变化之间的复杂相互作用共同导致了其发病机制。...

### co-scientist-0765

**English original**

Recent findings and related research Recent research has implicated several key players and processes in ALS. TDP-43, an RNA-binding protein, is found mislocalized and aggregated in the cytoplasm of affected neurons

**中文译文 · 机器初译**

最新发现及相关研究 近期研究揭示了ALS中多个关键因子与过程的作用。RNA结合蛋白TDP-43在受影响的神经元细胞质中出现错位定位并聚集现象


### 原文第 123 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=123)

### co-scientist-0767

**English original**

in the majority of ALS cases. This protein's ability to undergo liquid-liquid phase separation (LLPS) has come under intense scrutiny, with evidence suggesting that dysregulation of this process leads to the formation of pathological aggregates. Further, impairments in nucleocytoplasmic transport, the process by which molecules move between the nucleus and cytoplasm, have been observed in ALS and linked to TDP-43 pathology. Endoplasmic reticulum (ER) stress, a cellular response to protein misfolding, has also been implicated as a potential contributing factor.

**中文译文 · 机器初译**

在大多数ALS病例中。该蛋白质进行液-液相分离的能力受到了严格研究，有证据表明这种过程的失调会导致病理性聚集体形成。此外，核质内运输功能的受损——即分子在细胞核与细胞质之间移动的过程——在ALS中已被观察到，并与TDP-43病理相关。内质网应激（一种对蛋白质错误折叠的细胞反应）也被认为可能是潜在的致病因素之一。

### co-scientist-0768

**English original**

Hypothesis Cellular stress (including but not limited to ER stress) induces post-translational modifications (PTMs) on specific FG-Nups (focusing initially on Nup98 and Nup62) at the nuclear pore complex (NPC). These Nup PTMs modify the interaction between these Nups and TDP-43, leading to altered TDP-43 dynamics and increased retention at the NPC. This increased retention at the NPC, in turn, triggers the disruption of nucleocytoplasmic transport.

**中文译文 · 机器初译**

假设：细胞应激（包括但不仅限于内质网应激）会在核孔复合体（NPC）上对特定的FG-Nups产生翻译后修饰（PTMs），最初重点关注Nup98和Nup62。这些Nup的PTMs会改变这些Nups与TDP-43之间的相互作用，导致TDP-43的动力学发生变化，并增加其在NPC中的保留量。这种在NPC中的保留量增加，进而会引发核质运输的紊乱。

### co-scientist-0769

**English original**

Rationale and specificity Instead of making the hypothesis about LLPS, we are making it much more specific but with the same starting point. Cellular stress, a broad concept encompassing various cellular insults, can trigger a cascade of molecular events. A key consequence of stress response is altered protein structure and function, which can be mediated by PTMs. Nuclear pore proteins, particularly FG-Nups like Nup98 and Nup62, form a "hydrogel" or selective barrier at the NPC, regulating the movement of molecules between the nucleus and cytoplasm. We hypothesize that specific PTMs on these FG-Nups (e.g., phosphorylation, O-GlcNAcylation initially) directly alter their interaction with TDP-43. TDP-43, known to interact with the NPC and be involved in nucleocytoplasmic transport, may get inappropriately trapped or retained at the NPC when interacting with PTM-modified Nups. This trapping alters TDP-43 dynamics (even if not disrupting LLPS directly initially), meaning it cannot perform its normal functions and disrupting nucleocytoplasmic transport, which we know is happening in ALS. Since even a small change in transport could lead to downstream problems, this is a plausible initial event with testable consequences. The specific FG-Nups (Nup98/62) and chosen PTMs (phosphorylation/O-GlcNAcylation) provide a concrete starting point for experimentation. This mechanism directly links cellular stress to TDP-43 dysfunction and the key ALS pathology of defective nucleocytoplasmic transport by invoking a novel interaction mechanism at the NPC – all testable in vitro.

**中文译文 · 机器初译**

理由与具体性 我们并非针对 LLPS 提出假设，而是将其具体化，但起点保持不变。细胞应激是一个涵盖多种细胞损伤的广泛概念，能够引发一系列分子事件。应激反应的一个关键后果是蛋白质结构和功能的改变，这可通过翻译后修饰来介导。核孔蛋白，尤其是 FG-Nups 类蛋白如 Nup98 和 Nup62，在核孔处形成“水凝胶”或选择性屏障，从而调节分子在细胞核与细胞质之间的移动。
我们假设这些FG-Nup上的特定蛋白质修饰（例如最初发生的磷酸化或O-GlcNAcylation）会直接改变它们与TDP-43的相互作用。已知TDP-43会与NPC发生相互作用并参与核质内运输，当与经过蛋白质修饰的Nup结合时，它可能会被不恰当地困在或滞留于NPC中。这种滞留会改变TDP-43的动态特性（即使最初并未直接破坏LLPS），导致其无法执行正常功能，进而干扰核质内运输——而我们知道这种情况正是ALS发病的原因。由于即使是微小的运输变化也可能引发后续问题，因此这是一个具有可验证后果的合理初始事件。
特定的FG-Nups（Nup98/62）以及选定的蛋白质修饰方式（磷酸化/O-GlcNAcylation）为实验提供了具体的起点。这种机制通过在核内囊泡上建立新的相互作用机制，直接将细胞应激与TDP-43功能异常以及ALS的关键病理特征——核质运输缺陷——联系起来，所有现象均可在体外进行验证。

### co-scientist-0770

**English original**

Experimental design and validation Cell Types: Human iPSC-derived motor neurons from healthy controls and ALS patients. Stress Induction: Induce cellular stress using established pharmacological agents (e.g., tunicamycin for ER stress, arsenite for oxidative stress, oligomycin A for mitochondrial stress) and physical

**中文译文 · 机器初译**

实验设计与验证 细胞类型：来自健康对照组和ALS患者的人类 iPSC 衍生运动神经元。压力诱导：使用已建立的药物制剂（例如，Tunicamycin 用于内质网压力，砷酸盐用于氧化应激，寡霉素 A 用于线粒体压力）及物理方法诱导细胞压力


### 原文第 124 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=124)

### co-scientist-0772

**English original**

stressors (heat shock). Test different stressors individually and in combination. This broadened approach allows for a more robust investigation of the stress response. ... Nup PTM Analysis: Assess PTMs of Nup98 and Nup62 specifically using mass spectrometry and immunoblotting with PTM-specific antibodies (specifically looking for phosphorylation and O-GlcNAcylation). Focus the analysis on these two. …

**中文译文 · 机器初译**

压力源（热休克）。分别及组合测试不同的压力源。这种广泛的方法能够更稳健地研究应激反应。……Nup PTM分析：利用质谱技术和免疫印迹法，结合PTM特异性抗体，专门评估Nup98和Nup62的PTM情况（重点检测磷酸化和O-GlcNAcylation）。分析重点集中在这两个蛋白上。……

### co-scientist-0773

**English original**

10.3 Example output of a complete novelty review by the Reflection agent

**中文译文 · 机器初译**

10.3 由 Reflection 智能体完成的完整新颖性评审示例输出

### co-scientist-0774

**English original**

The abbreviated example showcases a complete novelty review by Co-Scientist Reflection agent for an example hypothesis pertaining to explaining the basic mechanism for Amyotrophic Lateral Sclerosis (ALS).

**中文译文 · 机器初译**

这个简化示例展示了联合科学家反思智能体针对一个关于解释肌萎缩侧索硬化症（ALS）基本机制的假设所进行的完整创新评审过程。

### co-scientist-0775

**English original**

Aspects already explored: ●​ TDP-43 mislocalization and aggregation in ALS: Extensively documented in multiple abstracts [1, 3, 4, 5, 6]. ●​ Nucleocytoplasmic transport defects in ALS: Demonstrated in connection with TDP-43 pathology and C9orf72 mutations [4, 5, 6]. ●​ NPC disruption in neurodegenerative diseases: Identified in ALS/FTD, Alzheimer’s, Huntington’s, and others, suggesting a common mechanism [4, 5, 7, 8]. ●​ The link between cellular stress and TDP-43 pathology: Explored in the context of stress granule formation and TDP-43 aggregation [5]. Note - stress is explored in general, but the idea of it leading to PTMs of Nups is new. ●​ Role of FG-Nups in NPC function: FG-Nups are known to form a selective barrier regulating transport, but the impact of their PTMs on TDP-43 interaction in ALS is novel [7]. ●​ The implication of PTMs for TDP-43: TDP-43 PTMs are widely researched, especially phosphorylation and ubiquitination. However, our hypothesis doesn’t speak about TDP-43 PTMs, it is about Nup PTMs [1, 3, 4].

**中文译文 · 机器初译**

已探讨的方面：● ALS中TDP-43错位与聚集现象：在多个摘要中已有详细记录[1, 3, 4, 5, 6]。● ALS中的核质运输缺陷：与TDP-43病变及C9orf72突变相关[4, 5, 6]。● 神经退行性疾病中的NPC破坏：在ALS/FTD、阿尔茨海默病、亨廷顿病等疾病中均有发现，表明存在共同机制[4, 5, 7, 8]。● 细胞应激与TDP-43病变之间的联系：在应激颗粒形成及TDP-43聚集的背景下进行了研究[5]。
注意——此处探讨的是压力效应，但压力导致 Nup 的翻译后修饰这一观点是新的。●​ FG-Nup 在 NPC 功能中的作用：已知 FG-Nup 会形成选择性屏障以调节运输，但它们的翻译后修饰对 ALS 中 TDP-43 相互作用的影响却是新的发现[7]。●​ 翻译后修饰对 TDP-43 的影响：TDP-43 的翻译后修饰已得到广泛研究，尤其是磷酸化和泛素化。然而，我们的假设并非针对 TDP-43 的翻译后修饰，而是针对 Nup 的翻译后修饰[1, 3, 4]。

### co-scientist-0776

**English original**

Novel Aspects: ●​ Cellular stress as an initiator of Nup PTMs: While stress is linked to TDP-43 pathology, the idea that it triggers specific PTMs on Nups (Nup98/Nup62) as an initiating event in ALS is novel, especially that these PTMs are phosphorylation and O-GlcNAcylation. ●​ Nup PTMs (phosphorylation and O-GlcNAcylation specifically) altering TDP-43 interaction at the NPC: The hypothesis proposes a novel mechanism where stress-induced PTMs on specific Nups (Nup98/Nup62) directly modify their interaction with TDP-43.

**中文译文 · 机器初译**

新发现方面：● 细胞应激作为 Nup PTMs 的引发因素：虽然应激与 TDP-43 病理相关，但认为其会触发 Nups（Nup98/Nup62）上的特定 PTMs，从而成为 ALS 发病的起始机制，这一观点较为新颖，尤其是这些 PTMs 表现为磷酸化与 O-GlcNAcylation。● Nup PTMs（特别是磷酸化和 O-GlcNAcylation）改变 NPC 中 TDP-43 的相互作用：该假设提出了一种新的机制，即由应激引起的特定 Nups（Nup98/Nup62）上的 PTMs 直接改变其与 TDP-43 的相互作用。

### co-scientist-0777

**English original**

This hasn't been explored before, particularly the focus on these specific PTMs and Nups.

**中文译文 · 机器初译**

这一点此前尚未被研究过，尤其是针对这些特定的代谢物与神经肽的关注。


### 原文第 125 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=125)

### co-scientist-0779

**English original**

●​ TDP-43 retention at the NPC as a key event: Instead of focusing on LLPS or aggregation directly, the hypothesis suggests that altered TDP-43 dynamics, specifically increased retention at the NPC due to modified Nup interactions, are a triggering factor. This specific mechanism at the NPC disrupting nucleocytoplasmic transport is novel. ●​ Focus on early events and potential for therapeutic intervention: By pinpointing early molecular events (Nup PTMs, altered TDP-43-Nup interaction), the hypothesis opens new avenues for therapeutic intervention targeting these specific processes, potentially before irreversible damage occurs. ●​ Broadening stress beyond ER stress: It is novel to consider multiple stressors in combination and it broadens the idea beyond ER stress (as suggested in the original provided idea).

**中文译文 · 机器初译**

● TDP-43在NPC处的滞留是一个关键事件：该假设认为，与其直接关注LLPS或聚集过程，不如关注改变的TDP-43动态，特别是由于Nup相互作用改变导致的NPC处滞留增加，这才是触发因素。
NPC中破坏核质内运输的这一特定机制是全新的。●​ 关注早期事件及治疗干预的可能性：通过确定早期的分子事件（核质内转运修饰、TDP-43与核质内转运的相互作用变化），这一假设为针对这些特定过程的治疗干预开辟了新途径，有望在不可逆损伤发生之前进行干预。●​ 拓展压力范畴至除内质网压力之外的其他类型压力：将多种压力因素结合考虑是一种新的思路，从而将研究范围从内质网压力扩展至更广泛的领域（与原始设想一致）。

### co-scientist-0780

**English original**

10.4 Example output of review critiques by the Reflection agent

**中文译文 · 机器初译**

10.4 由反思智能体进行的评论评审示例输出

### co-scientist-0781

**English original**

This is an example output of review critiques from the Reflection agent.

**中文译文 · 机器初译**

这是来自 Reflection 智能体的评论评测示例输出。

### co-scientist-0782

**English original**

●​ Lack of strong justification for motor neuron specificity: The initial hypothesis lacked a strong explanation for why the proposed mechanism would predominantly affect motor neurons, a critical aspect of ALS pathology. ●​ Limited exploration of downstream consequences: While the idea connects to nucleocytoplasmic transport defects, it doesn't fully elaborate on how these defects lead to other ALS-related pathologies like TDP-43 aggregation or RNA processing defects. ●​ Potential technical challenges: Identifying the specific PTMs responsible and demonstrating their direct impact on TDP-43 retention and transport might be technically difficult. ●​ Narrow focus on specific Nups and PTMs: Initially focusing only on Nup98/Nup62 and two types of PTMs (phosphorylation, O-GlcNAcylation) could be too restrictive, potentially overlooking other important factors. ●​ Less holistic approach: The focus on a specific mechanism at the NPC might neglect broader cellular processes involved in ALS pathogenesis. ●​ The temporal relationship with TDP-43 pathology is not clear: It's not clear whether the hypothesized mechanism occurs before or after other ALS hallmarks like cytoplasmic TDP-43 aggregation, which is crucial for establishing causality. ●​ ...

**中文译文 · 机器初译**

● 缺乏关于运动神经元特异性的充分依据：最初的假设未能给出合理的解释，说明所提出的机制为何主要影响运动神经元——而这是ALS病理特征的关键方面。 ● 对下游后果的研究有限：虽然该理论与核质内运输缺陷有关，但并未充分说明这些缺陷如何导致其他与ALS相关的病理现象，如TDP-43聚集或RNA加工异常。 ● 潜在的技术挑战：确定具体的蛋白质修饰位点及其对TDP-43滞留和运输的直接影响，可能在技术上较为困难。 ● 对特定Nups和PTMs的关注较为狭窄。
最初仅关注 Nup98/Nup62 以及两种类型的蛋白质修饰（磷酸化、O-GlcNAcylation）可能过于局限，可能会忽略其他重要因素。●​ 不够全面的方法：仅关注 NPC 中的特定机制，可能会忽视与 ALS 发病相关的更广泛细胞过程。●​ TDP-43 病变的时间关系尚不明确：目前尚不清楚所假设的机制是在其他 ALS 特征（如细胞质中 TDP-43 聚集）之前还是之后发生，而后者对于确立因果关系至关重要。●​...

### co-scientist-0783

**English original**

10.5 Example output of a full review by the Reflection agent

**中文译文 · 机器初译**

10.5 Reflection智能体完整评论的示例输出


### 原文第 126 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=126)

### co-scientist-0785

**English original**

The abbreviated example showcases a full initial review generated by Co-Scientist Reflection agent for an example hypothesis pertaining to explaining the basic mechanism for Amyotrophic Lateral Sclerosis (ALS).

**中文译文 · 机器初译**

这个简化示例展示了 Co-Scientist Reflection 智能体针对一个关于解释肌萎缩侧索硬化症（ALS）基本机制的假设所生成的完整初步评估结果。

### co-scientist-0786

**English original**

Related Articles: [5] TDP-43 pathology disrupts nuclear pore complexes and nucleocytoplasmic transport in ALS/FTD - PMC: This article is highly relevant because it directly links TDP-43 pathology to nuclear pore complex (NPC) dysfunction and nucleocytoplasmic transport (NCT) defects in ALS/FTD, providing a strong foundation for the hypothesis. [4] Unraveling the impact of disrupted nucleocytoplasmic transport systems in C9orf72-associated ALS - PMC: This article provides context on NCT defects in ALS, particularly in the context of C9orf72 mutations, highlighting the broader relevance of NCT dysfunction in different forms of ALS. [7] Nuclear pore and nucleocytoplasmic transport impairment in oxidative stress-induced neurodegeneration: relevance to molecular mechanisms in Pathogenesis of Parkinson’s and other related neurodegenerative diseases - PMC: This article connects oxidative stress, a form of cellular stress, to NPC dysfunction and NCT impairment in neurodegenerative diseases, supporting the idea that cellular stress can impact NPCs. [3] Frontiers | Molecular Mechanisms of TDP-43 Misfolding and Pathology in Amyotrophic Lateral Sclerosis: This article reviews TDP-43 pathology in ALS, including its mislocalization and aggregation, which are central to the proposed hypothesis. [1] TDP-43 proteinopathies: a new wave of neurodegenerative diseases - PMC: Provides an overview of TDP-43 proteinopathies, establishing the importance of TDP-43 dysfunction in ALS and other neurodegenerative diseases. [8] Aβ-driven nuclear pore complex dysfunction alters activation of necroptosis proteins in a mouse model of Alzheimer’s Disease: Although focused on Alzheimer’s, this article demonstrates that NPC dysfunction can occur in neurodegenerative diseases and highlights the potential impact on cellular processes like necroptosis. It supports the general idea that NPC defects can be a consequence of proteinopathy-associated stress. [9] Traumatic injury compromises nucleocytoplasmic transport and leads to TDP-43 pathology: This article provides another example of how cellular stress (traumatic injury) can lead to NCT defects and TDP-43 pathology, further supporting the link between stress, NCT, and TDP-43 dysfunction. …

**中文译文 · 机器初译**

相关文章：[5] TDP-43病变会破坏ALS/FTD中的核孔复合体与核质内运输功能——PMC：本文具有高度相关性，因为它直接将TDP-43病变与ALS/FTD中核孔复合体功能障碍及核质内运输缺陷联系起来，为该假设提供了有力的依据。[4] 解析C9orf72相关ALS中核质内运输系统紊乱的影响——PMC：本文介绍了ALS中核质内运输缺陷的情况，特别是在C9orf72突变背景下，凸显了核质内运输功能障碍在不同类型ALS中的广泛重要性。
[7] 氧化应激引起的神经退行性疾病中的核孔及核质内运输障碍：与帕金森病及其他相关神经退行性疾病发病机制的关联——PMC：本文将细胞应激的一种形式——氧化应激，与神经退行性疾病中核孔功能异常及核质内运输障碍联系起来，支持了细胞应激会影响核孔的观点。[3] Frontiers | 肌萎缩侧索硬化症中TDP-43错误折叠及病理机制：本文综述了ALS中TDP-43的病理变化，包括其错位聚集现象，这些现象正是所提出的假设的核心内容。
[1] TDP-43蛋白病：新一代神经退行性疾病——PMC：本文对TDP-43蛋白病进行了概述，强调了TDP-43功能异常在ALS及其他神经退行性疾病中的重要性。[8] 在阿尔茨海默病小鼠模型中，Aβ引发的核孔复合体功能障碍会改变坏死性细胞凋亡蛋白的激活机制：尽管本文主要讨论阿尔茨海默病，但表明核孔复合体功能障碍可出现在各种神经退行性疾病中，并凸显了其对坏死性细胞凋亡等细胞过程的潜在影响。这支持了核孔复合体缺陷可能是蛋白质病相关应激的结果这一总体观点。
[9] 创伤性损伤会破坏核胞质运输，导致 TDP-43 病理变化：本文提供了另一个实例，说明细胞应激（创伤性损伤）如何导致 NCT 缺陷和 TDP-43 病理变化，进一步证实了应激、NCT 与 TDP-43 功能障碍之间的关联。…

### co-scientist-0787

**English original**

Assumptions of the Idea: ●​ Cellular stress induces PTMs on Nup98 and Nup62: The hypothesis assumes that various forms of cellular stress can trigger specific PTMs (phosphorylation and O-GlcNAcylation) on Nup98 and Nup62.

**中文译文 · 机器初译**

该概念的假设：● 细胞应激会在 Nup98 和 Nup62 上引发蛋白质修饰：该假设认为各种形式的细胞应激能够触发 Nup98 和 Nup62 上的特定蛋白质修饰（磷酸化与 O-GlcNAcylation）。


### 原文第 127 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=127)

### co-scientist-0789

**English original**

●​ PTMs on Nup98/Nup62 alter their interaction with TDP-43: It's assumed that these specific PTMs directly modify the binding affinity or interaction dynamics between Nup98/Nup62 and TDP-43 at the NPC. ●​ Altered Nup-TDP-43 interaction leads to increased TDP-43 retention at the NPC: This assumption posits that the modified interaction results in TDP-43 being trapped or retained at the NPC for longer durations. ●​ Increased TDP-43 retention at the NPC disrupts nucleocytoplasmic transport: The hypothesis assumes that this prolonged retention of TDP-43 at the NPC interferes with the normal transport of other molecules across the nuclear envelope. ●​ Nucleocytoplasmic transport defects contribute to ALS pathology: The idea assumes that the resulting NCT disruption is a significant contributor to the downstream pathological events in ALS, such as motor neuron degeneration. ●​ Motor neurons are more susceptible to this mechanism: It's assumed that motor neurons are particularly vulnerable to this stress-induced, Nup-mediated TDP-43 retention and subsequent NCT defects compared to other cell types.

**中文译文 · 机器初译**

● Nup98/Nup62上的蛋白质修饰改变了其与TDP-43的相互作用：假设这些特定的蛋白质修饰直接改变了Nup98/Nup62与TDP-43在核内区室中的结合亲和力或相互作用动态。 ● 改变的Nup-TDP-43相互作用导致TDP-43在核内区室中的滞留时间增加：该假设认为，这种改变的相互作用使得TDP-43在核内区室中被滞留或保留的时间更长。 ● TDP-43在核内区室的滞留时间增加会干扰核质运输：假设认为，TDP-43在核内区室的长期滞留会干扰其他分子通过核膜的正常运输。 ● 核质运输缺陷会造成影响
对ALS病理的影响：该理论认为，由此产生的NCT破坏是导致ALS下游病理事件（如运动神经元退化）的重要原因。● 运动神经元更容易受到这种机制的影响：与其他细胞类型相比，运动神经元被认为特别容易受到这种由压力引起的、Nup介导的TDP-43滞留及随后的NCT缺陷的影响。

### co-scientist-0790

**English original**

Reasoning about assumptions: ●​ Cellular stress induces PTMs on Nup98 and Nup62: This is plausible. Cellular stress is known to activate various signaling pathways that can lead to PTMs on numerous proteins. Nups, being long-lived proteins, are susceptible to modifications. However, whether Nup98 and Nup62 are specifically targeted by stress-induced phosphorylation and O-GlcNAcylation needs experimental verification. ●​ PTMs on Nup98/Nup62 alter their interaction with TDP-43: This is possible but requires experimental validation. PTMs can significantly alter protein-protein interactions by changing surface charge, conformation, or binding sites. While there's no direct evidence for this specific interaction, it's a reasonable hypothesis given the role of FG-Nups in interacting with transport factors. ●​ Nucleocytoplasmic transport defects contribute to ALS pathology: This is supported by existing literature. NCT defects have been observed in ALS and are thought to contribute to disease pathogenesis. However, whether this specific mechanism is a primary driver or a downstream consequence needs further investigation. ●​ Motor neurons are more susceptible to this mechanism: This is a crucial assumption but lacks strong justification in the current proposal. Motor neurons have unique characteristics (high metabolic demand, long axons) that might make them more vulnerable to stress and NCT defects. However, this needs to be explicitly tested by comparing motor neurons to other cell types. ●​ …

**中文译文 · 机器初译**

关于假设的推理：● 细胞应激会在 Nup98 和 Nup62 上引发修饰：这是有可能的。已知细胞应激会激活多种信号通路，从而导致多种蛋白质发生修饰。作为长寿命蛋白，Nups 也容易受到修饰。然而，应激诱导的磷酸化和 O-GlcNAcylation 是否特异性地作用于 Nup98 和 Nup62，仍需通过实验验证。● Nup98/Nup62 上的修饰会改变其与 TDP-43 的相互作用：这是可能的，但需要通过实验验证。修饰可以通过改变表面电荷、构象或结合位点来显著改变蛋白质-蛋白质相互作用。
虽然没有直接证据支持这种特定相互作用，但鉴于 FG-Nups 在与运输因子互动中的作用，这一假设是合理的。●​ 核质运输缺陷会导致 ALS 病理变化：现有文献也证实了这一点。在 ALS 患者中已观察到 NCT 缺陷，并被认为对疾病发病机制有贡献。然而，这种特定机制是主要驱动因素还是次要后果，仍需进一步研究。●​ 运动神经元更容易受到这种机制的影响：这是一个重要的假设，但在当前提案中缺乏充分的依据。
运动神经元具有独特的特性（高代谢需求、长轴突），这可能使其更容易受到压力及NCT缺陷的影响。然而，需要通过将运动神经元与其他细胞类型进行比较来明确验证这一点。●​ …


### 原文第 128 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=128)

### co-scientist-0792

**English original**

10.6 Example output of deep verification by the Reflection agent

**中文译文 · 机器初译**

10.6 反思智能体深度验证的示例输出

### co-scientist-0793

**English original**

The abbreviated example showcases a deep verification review by Co-Scientist Reflection agent for the Amyotrophic Lateral Sclerosis (ALS) basic mechanism research goal given Co-Scientist’s generated hypothesis and other reviews of it.

**中文译文 · 机器初译**

该简化示例展示了联合科学家智能体对肌萎缩侧索硬化症（ALS）基础机制研究目标进行的深入验证评审，该评审基于联合科学家提出的假设及其他相关评审结果。

### co-scientist-0794

**English original**

Assumptions: ●​ Cellular stress induces PTMs like phosphorylation and O-GlcNAcylation. ●​ Nup98 and Nup62 interact with TDP-43 at the NPC. ●​ Nup98 can interact with TDP-43 ●​ Nup62 can interact with TDP-43 ●​ Altered interaction between Nups and TDP-43 leads to increased TDP-43 retention at the NPC. ●​ Disrupted nucleocytoplasmic transport triggers downstream ALS pathology. ●​ Motor neurons are inherently more vulnerable to this mechanism. ●​ The level of cellular stress inducing these PTMs is sufficient to cause a significant impact on TDP-43 localization. ●​ TDP-43 localizes to the nuclear pore complex (NPC). ●​ …

**中文译文 · 机器初译**

假设：● 细胞应激会引发磷酸化及O-GlcNAcylation等表观修饰。● Nup98和Nup62在核内颗粒处与TDP-43相互作用。● Nup98能与TDP-43相互作用。● Nup62也能与TDP-43相互作用。● Nups与TDP-43之间相互作用的改变会导致TDP-43在核内颗粒中的滞留增加。● 核质内运输的紊乱会引发后续的ALS病理变化。● 运动神经元本质上更容易受到这种机制的影响。● 引发这些表观修饰的细胞应激水平足以对TDP-43的定位产生显著影响。● TDP-43会定位到核孔复合体（NPC）中。● …

### co-scientist-0795

**English original**

1. Cellular stress induces PTMs like phosphorylation and O-GlcNAcylation. Cellular stress encompasses a range of conditions that disrupt cellular homeostasis, including nutrient deprivation, hypoxia, oxidative stress, and the accumulation of misfolded proteins. The endoplasmic reticulum (ER) is a central organelle involved in protein synthesis, folding, and modification. When the ER's capacity to handle protein folding is overwhelmed, a condition known as ER stress arises. This triggers a signaling pathway called the unfolded protein response (UPR) aimed at restoring ER homeostasis.

**中文译文 · 机器初译**

1. 细胞应激会引发磷酸化和O-GlcNAcylation等分子修饰。细胞应激包括多种破坏细胞稳态的状况，如营养缺乏、缺氧、氧化应激以及错误折叠蛋白质的积累。内质网是参与蛋白质合成、折叠和修饰的核心细胞器。当内质网处理蛋白质折叠的能力被超出时，就会出现称为内质网应激的状态。这会触发一种名为未折叠蛋白反应（UPR）的信号通路，以恢复内质网的稳态。

### co-scientist-0796

**English original**

Post-translational modifications (PTMs) are covalent modifications to proteins that occur after translation. They play crucial roles in regulating protein function, localization, and interactions. Phosphorylation, the addition of a phosphate group, and O-GlcNAcylation, the addition of O-linked N-acetylglucosamine, are two common PTMs. Numerous studies have demonstrated a strong link between cellular stress, including ER stress, and the alteration of PTMs. Here's a breakdown: ●​ ER Stress and Phosphorylation: The UPR, activated during ER stress, involves multiple signaling pathways, many of which rely on phosphorylation. For example, PERK (PKR-like ER kinase), a key UPR sensor, undergoes autophosphorylation upon sensing misfolded proteins. This activated PERK then phosphorylates eIF2α (eukaryotic initiation factor 2 alpha), leading to a global attenuation of translation. Another UPR sensor, IRE1 (inositol-requiring enzyme 1), possesses both kinase and endoribonuclease

**中文译文 · 机器初译**

翻译后内容：翻译后修饰（PTMs）是蛋白质在翻译之后发生的共价修饰。它们在调节蛋白质功能、定位及相互作用方面起着至关重要的作用。磷酸化即添加磷酸基团，O-GlcNAcylation即添加O-连接N-乙酰葡萄糖胺，这是两种常见的PTMs。大量研究表明，细胞应激（包括内质网应激）与PTMs的改变之间存在密切关联。具体说明如下：● 内质网应激与磷酸化：在内质网应激过程中被激活的UPR涉及多种信号通路，其中许多通路依赖于磷酸化作用。
例如，作为关键 UPR 传感器的 PERK（类似 PKR 的 ER 激酶），在感知到错误折叠蛋白质后会发生自磷酸化。这种被激活的 PERK 随后会磷酸化 eIF2α（真核生物起始因子 2 α），导致翻译过程整体减弱。另一个 UPR 传感器 IRE1（需要肌醇的酶 1）则同时具有激酶和内核糖核酸酶的功能


### 原文第 129 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=129)

### co-scientist-0798

**English original**

activity. Upon activation, IRE1 autophosphorylates and splices XBP1 mRNA, leading to the production of a transcription factor that upregulates chaperones and other proteins involved in protein folding and degradation. These are just two examples; numerous other proteins are phosphorylated during ER stress, affecting various cellular processes. ●​ ER Stress and O-GlcNAcylation: O-GlcNAcylation is a dynamic PTM influenced by nutrient availability and cellular stress. Evidence suggests a complex interplay between ER stress and O-GlcNAcylation. Some studies report increased O-GlcNAcylation during ER stress, potentially as a protective mechanism. For example, O-GlcNAcylation of certain chaperones can enhance their activity and promote protein folding. Conversely, other studies suggest that ER stress can lead to decreased O-GlcNAcylation. The exact relationship likely depends on the specific stress conditions, cell type, and the targeted proteins. ●​ Cellular Stress (beyond ER Stress) and PTMs: Other forms of cellular stress also impact PTMs. Oxidative stress, for example, can lead to protein oxidation, which can affect protein function and stability. Nutrient deprivation can alter the availability of substrates for PTMs, such as UDP-GlcNAc for O-GlcNAcylation. Hypoxia can also induce changes in phosphorylation and other PTMs, influencing cellular responses to low oxygen levels. In summary, the available evidence strongly supports the assertion that cellular stress, including ER stress, can induce PTMs like phosphorylation and O-GlcNAcylation on proteins. This effect is mediated by complex signaling pathways and serves to regulate various cellular processes in response to stress.

**中文译文 · 机器初译**

活动。激活后，IRE1进行自磷酸化并剪接XBP1 mRNA，从而生成一种转录因子，该因子可上调伴侣蛋白以及参与蛋白质折叠和降解的其他蛋白质的表达。这些只是两个例子；在内质网应激过程中还会发生大量其他蛋白质的磷酸化，进而影响各种细胞过程。● 内质网应激与O-GlcNAcylation：O-GlcNAcylation是一种动态蛋白质修饰，受营养供应和细胞应激的影响。有证据表明，内质网应激与O-GlcNAcylation之间存在复杂的相互作用。一些研究指出，在内质网应激期间O-GlcNAcylation水平会升高，这可能是一种保护机制。
例如，某些伴侣蛋白的 O-GlcNAcylation 可增强其活性并促进蛋白质折叠。相反，其他研究表明 ER 应激会导致 O-GlcNAcylation 减少。具体关系可能取决于具体的应激条件、细胞类型以及目标蛋白质。● 细胞应激（除 ER 应激外）与翻译后修饰：其他形式的细胞应激也会影响翻译后修饰。例如，氧化应激会导致蛋白质氧化，从而影响蛋白质的功能和稳定性。营养缺乏则会改变用于翻译后修饰的底物可用性，如用于 O-GlcNAcylation 的 UDP-GlcNAc。
缺氧还会引发磷酸化及其他蛋白质翻译后修饰的变化，从而影响细胞对低氧水平的反应。总之，现有证据充分支持这样一种观点：包括内质网应激在内的细胞应激状态能够促使蛋白质发生磷酸化及O-GlcNAcylation等翻译后修饰。这种效应通过复杂的信号通路实现，用于调节应对应激时的各种细胞过程。

### co-scientist-0799

**English original**

10.7 Example output of deep verification via probing questions by the Reflection agent

**中文译文 · 机器初译**

10.7 反思智能体通过探究问题进行深度验证的示例输出

### co-scientist-0800

**English original**

The example demonstrates how the Reflection agent performs deep verification via probing questions for a research hypothesis pertaining to drug repurposing for Acute Myeloid Leukemia (AML). The original research goal is provide for illustration only, it is not included in the review output.

**中文译文 · 机器初译**

该示例展示了智能体 Reflection如何通过探究性问题对关于急性髓系白血病（AML）药物重新应用的研究假设进行深度验证。原始研究目标仅用于说明之用，并未包含在综述结果中。

### co-scientist-0801

**English original**

[Research Goal] Repurposing Reparixin for AML treatment.

**中文译文 · 机器初译**

[研究目标] 将 Reparixin 重新应用于 AML 治疗。

### co-scientist-0802

**English original**

Suggest an existing drug that could be repurposed for Acute myelogenous leukemia (AML) treatment and provide experimentally testable concentrations for an IC50 assay. The drug should inhibit the proliferation of AML cell lines, particularly MOLM-13. The drug should have minimal cytotoxicity in healthy cell lines (have a good tradeoff for AML treatment). The drug should not have been experimentally tested for AML treatment before. Reason about the drug's

**中文译文 · 机器初译**

建议一种可重新用于急性髓系白血病（AML）治疗的现有药物，并提供可用于 IC50 测定实验的可测试浓度。该药物应能抑制 AML 细胞系的增殖，尤其是 MOLM-13。该药物在健康细胞系中的细胞毒性应极低（以实现与 AML 治疗良好的平衡）。此前尚未有该药物被用于 AML 治疗的实验研究。对该药物的理由进行说明


### 原文第 130 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=130)

### co-scientist-0804

**English original**

molecular mechanism, impacted pathways, and effect on AML cell proliferation inhibition. Describe the mechanism of action in detail. Reason about the safety and toxicity, stating if no safety data exists.

**中文译文 · 机器初译**

分子机制、受影响的通路及其对AML细胞增殖抑制的影响。详细描述其作用机制。讨论其安全性和毒性问题，并说明是否存在安全性数据。

### co-scientist-0805

**English original**

[Output] Question: Sufficiency of CXCR1/2 Inhibition: What is the rationale for assuming that CXCR1/2 inhibition alone will be sufficient to overcome the established heterogeneity and multiple compensatory pathways known to drive AML progression and resistance, even before considering combination therapies?

**中文译文 · 机器初译**

[Output] 问题：CXCR1/2抑制的充分性：在考虑联合疗法之前，为何认为仅通过CXCR1/2抑制就足以克服导致AML进展和耐药性的既定异质性及多种代偿途径？

### co-scientist-0806

**English original**

This challenges the fundamental assumption that targeting a single pathway (even a dual-target one) will be effective in a complex disease like AML. AML is known for its ability to bypass single-target inhibition. Addressing this upfront is crucial to justify the entire approach, especially before investing heavily in combination studies.

**中文译文 · 机器初译**

这挑战了“针对单一通路（甚至是双目标通路）将在像AML这样的复杂疾病中有效”这一基本假设。AML以能够绕过单一靶点抑制的能力而著称。提前解决这一问题对于证明整个研究方法的合理性至关重要，尤其是在大量投入联合研究之前。

### co-scientist-0807

**English original**

Answer: The rationale for initially focusing on CXCR1/2 inhibition with Reparixin, before immediately jumping to combinations, stems from several interwoven, but not entirely definitive, points: ●​ Targeting a Key TME Node: CXCR1/2 are major regulators of neutrophil and myeloid-derived suppressor cell (MDSC) recruitment to the tumor microenvironment.

**中文译文 · 机器初译**

答案：最初专注于使用 Reparixin 抑制 CXCR1/2，随后立即转向组合疗法，这一策略的合理性源于几个相互关联但并非完全确定的因素：● 针对关键肿瘤微环境节点：CXCR1/2是中性粒细胞和髓系来源抑制细胞向肿瘤微环境募集的主要调节因子。

### co-scientist-0808

**English original**

These cells, in turn, contribute significantly to immune suppression, angiogenesis, and therapy resistance in AML. By blocking these receptors, Reparixin aims to disrupt a central hub of TME-mediated support for AML cells. The idea is not necessarily that CXCR1/2 inhibition is sufficient in all cases, but that it addresses a significant and often overlooked contributor to AML progression. ●​ Dual Receptor Blockade: Reparixin's dual inhibition of CXCR1 and CXCR2 is hypothesized to be more effective than targeting either receptor individually. While not explicitly stated in the provided text, there could be redundancy or synergy between these two receptors in promoting AML progression. Blocking both might offer a more substantial impact on the TME than single-receptor antagonists. ●​ Establishing a Baseline: The proposal, while acknowledging the complexity of AML, strategically starts with single-agent Reparixin to establish a clear baseline of its activity and effects. This is crucial for several reasons: ○​ Understanding Single-Agent Effects: It's essential to dissect the specific contributions of Reparixin alone before introducing the complexity of combinations. This allows for a more rational design of combination strategies. ○​ Identifying Resistance Mechanisms: Studying single-agent resistance is simpler and more direct than untangling resistance mechanisms in a multi-drug scenario.

**中文译文 · 机器初译**

这些细胞进而对急性髓系白血病中的免疫抑制、血管生成及治疗抵抗起着重要作用。通过阻断这些受体，Reparixin旨在破坏TME对白血病细胞支持的核心机制。其理念并非认为CXCR1/2抑制在所有情况下都足够有效，而是认为它能够解决一个重要且常被忽视的白血病进展因素。●​双受体阻断：Reparixin对CXCR1和CXCR2的双重抑制被认为比单独针对任一受体更为有效。尽管文本中并未明确说明，但这两个受体在促进白血病进展过程中可能存在冗余或协同作用。
同时阻断这两种物质可能对TME产生比单一受体拮抗剂更显著的影响。●​ 建立基准线：该提案虽然承认AML的复杂性，但策略性地以单药Reparixin作为起点，以明确其活性和作用的基准线。这具有多重重要意义：○​ 理解单药效应：在引入联合用药的复杂性之前，有必要先分析Reparixin单独使用的具体作用机制。
这使得组合策略的设计更加理性。○​ 识别抗药性机制：研究单个智能体的抗药性比在多药场景下梳理各种抗药性机制更为简单直接。

### co-scientist-0809

**English original**

The extensive resistance studies proposed are specifically geared towards understanding Reparixin-specific resistance.

**中文译文 · 机器初译**

所提出的广泛抗药性研究，旨在专门理解与 Reparixin 相关的抗药性。


### 原文第 131 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=131)

### co-scientist-0811

**English original**

○​ Patient Stratification: The comprehensive patient stratification plan is designed to identify patients who might respond to Reparixin as a single agent, or for whom it forms a critical foundation for combination therapy. ●​ TME Reprogramming, Not Just Cytotoxicity: The proposal positions Reparixin not just as a cytotoxic agent, but as a TME modulator. The hypothesis is that by altering the TME, Reparixin may sensitize AML cells to other therapies or even trigger immune-mediated clearance. This "reprogramming" effect might not be fully captured by traditional cytotoxicity assays alone. ●​ Sequential therapy: The proposal includes sequential administration of drugs, where Reparixin can prime the tumor cells for killing and/or resensitize them too.

**中文译文 · 机器初译**

○​ 患者分层：全面的患者分层方案旨在识别可能仅对 Reparixin 单独使用有反应的患者，或那些将其作为联合治疗关键基础的患者。●​ 肿瘤微环境重塑，而不仅仅是细胞毒性：该提案将 Reparixin 定位为肿瘤微环境调节剂，而非单纯的细胞毒性药物。假设是，通过改变肿瘤微环境，Reparixin 可能使 AML 细胞对其他疗法产生敏感性，甚至引发免疫介导的清除作用。
这种“重新编程”效应可能无法仅通过传统的细胞毒性检测方法来完全体现。●​ 序贯治疗：该方案包含药物的序贯使用，其中 Reparixin 可以使肿瘤细胞准备好被杀死或重新产生敏感性。

### co-scientist-0812

**English original**

Reasoning: The idea isn't incoherent, but it requires careful consideration of the sufficiency assumption. While the points above provide a rationale, they don't guarantee that CXCR1/2 inhibition alone will be sufficient in all, or even most, cases of AML. The heterogeneity of AML, with its multitude of driver mutations and compensatory pathways, strongly suggests that combination therapies will ultimately be necessary for many patients.

**中文译文 · 机器初译**

推理：这一想法并非毫无逻辑，但需仔细考虑充分性假设。虽然上述观点提供了依据，但并不能保证在所有甚至大多数急性髓系白血病病例中，仅抑制 CXCR1/2 就足够有效。急性髓系白血病的异质性，及其多种驱动突变和补偿机制，强烈表明许多患者最终需要联合治疗。

### co-scientist-0813

**English original**

The strength of the proposal lies in its methodical approach. It doesn't claim that Reparixin is a magic bullet. It sets out to systematically investigate its potential, both alone and in combination, and to identify the specific patient subsets most likely to benefit. The extensive in vivo and patient stratification studies are key to addressing the "sufficiency" question empirically. The proposal is essentially a very detailed roadmap for determining when and how CXCR1/2 inhibition can be most effectively used in AML treatment, rather than an assertion of universal single-agent efficacy. Therefore the idea may require combination approaches but the study plan described in the proposal is structured in a way to determine that.

**中文译文 · 机器初译**

该提案的优势在于其系统化的研究方法。它并不声称 Reparixin 是万能解决方案，而是旨在系统地探讨其单独使用及联合使用的潜力，并确定最有可能从中受益的特定患者群体。广泛的体内研究和患者分层研究对于实证解决“有效性”问题至关重要。该提案实际上是一个非常详细的路线图，用于明确在AML治疗中何时以及如何最有效地使用 CXCR1/2 抑制剂，而非断言其具有普遍的单药治疗效果。
因此，该想法可能需要结合多种方法，但提案中描述的研究计划已安排得当以实现这一目标。

### co-scientist-0814

**English original**

10.8 Example output of an observation review by the Reflection Agent

**中文译文 · 机器初译**

10.8 反思智能体进行观察审查的示例输出

### co-scientist-0815

**English original**

The abbreviated example showcases an observation review by Co-Scientist Reflection agent for a hypothesis related to explaining a mechanism of antimicrobial resistance (AMR). The original research goal is provide for illustration only, it is not included in the review output.

**中文译文 · 机器初译**

该简化示例展示了联合科学家智能体对与解释抗菌耐药性机制相关的假设进行的观察审查。原始研究目标仅用于说明之用，并未包含在审查结果中。

### co-scientist-0816

**English original**

[Research Goal] Unravel a specific and novel molecular mechanism explaining how the same cf-PICI can be found in different bacterial species. … Why can cf-PICIs, but not other types of PICIs or satellites, be easily found in different bacterial species? What is the mechanism that explains this?

**中文译文 · 机器初译**

[研究目标] 阐明一种特定且新颖的分子机制，以解释为何相同的 cf-PICI 可以在不同的细菌物种中出现。……为什么 cf-PICI 可以而在其他类型的 PICI 或卫星分子中无法在不同细菌物种中被发现？这一现象背后的机制是什么？


### 原文第 132 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=132)

### co-scientist-0818

**English original**

[Output] The "Modular Capsid-OMV Mediated Transfer" (MCOMT) hypothesis proposes that cf-PICIs achieve their broad host range through a combination of modular capsid interactions and OMV-mediated transfer, using both tail-dependent and tail-independent mechanisms. Several observations support this hypothesis: ●​ Widespread presence of PICIs in Gram-negative bacteria, particularly Enterobacteriaceae and Pastuerellaceae: These bacteria readily produce and internalize OMVs, aligning with the MCOMT hypothesis that OMVs are crucial for cf-PICI dissemination. The modular capsid, with its broad bacterial surface binding capabilities, further enhances transfer even without specific tail receptors on target cells. ●​ Unique PICI att sites not used by temperate prophages: The MCOMT hypothesis, by reducing reliance on helper phage integration due to OMV-mediated transfer and diverse entry routes, explains the evolution of cf-PICI-specific att sites independent of phage integration sites. This allows wider integration across bacterial genomes. ●​ ...

**中文译文 · 机器初译**

[Output] “模块化衣壳-OMV介导转移”假设认为，cf-PICIs通过模块化衣壳相互作用与OMV介导的转移相结合，利用依赖尾部及非依赖尾部的机制，实现了对广泛宿主范围的覆盖。多项观察结果支持这一假设：● cf-PICIs在革兰氏阴性菌中广泛存在，尤其是肠杆菌科和帕斯特雷勒菌科细菌：这些细菌能够轻易产生并内吞OMV，这与MCOMT假设一致，即OMV对于cf-PICIs的传播至关重要。
具有广泛细菌表面结合能力的模块化衣壳结构，即使目标细胞上没有特定的尾部受体，也能进一步促进转移。●​ 温带前噬菌体未使用的独特 PICI att 位点：通过减少对辅助噬菌体的整合依赖，并利用 OMV 介导的转移及多种进入途径，MCOMT 假设解释了 cf-PICI 特异性 att 位点的进化过程，这些位点与噬菌體整合位点无关。这使得其在不同细菌基因组中的整合更加广泛。●​...

### co-scientist-0819

**English original**

10.9 Example of a scientific debate match in the Ranking agent tournament

**中文译文 · 机器初译**

10.9 排名智能体竞赛中的科学辩论匹配示例

### co-scientist-0820

**English original**

The abbreviated example showcases a scientific debate match orchestrated by Co-Scientist Ranking agent as part of its tournament to compare two ideas related to explaining the mechanism of ALS.

**中文译文 · 机器初译**

这个简化的示例展示了由“联合科学家排名智能体”在竞赛中组织的科学辩论比赛，旨在比较关于解释ALS机制的两个观点。

### co-scientist-0821

**English original**

Expert 1: I'm intrigued by both ideas, but I have a few clarifying questions. For Idea 1, while the focus on TDP-43 retention at the NPC is novel, I'm not entirely convinced that it's fundamentally different from the extensively studied TDP-43 mislocalization. Could the retention just be a consequence of mislocalization, or are there experiments that can distinguish these two phenomena? Another question I have: Is there evidence already that specific PTMs modulate the interaction of Nups and TDP-43? Not necessarily in the context of ALS, but are there any precedents?

**中文译文 · 机器初译**

专家1：我对这两个观点都很感兴趣，但有一些需要澄清的问题。关于第一个观点，虽然关注NPC层面的TDP-43保留现象是新的，但我并不完全相信这与已被广泛研究的TDP-43错位现象有本质区别。这种保留现象是否仅仅是错位现象的结果？还是存在能够区分这两种现象的实验？另一个问题是：目前是否有证据表明某些蛋白质翻译后修饰会影响Nups与TDP-43的相互作用？不一定是在ALS病例中，但是否存在相关先例呢？

### co-scientist-0822

**English original**

Expert 2: For Idea 2, I appreciate the bold approach, but the ISR as a trigger is a significant departure from the conventional view. Can the proponents of this idea elaborate on the evidence supporting this? Also, what specific lipid species are they proposing to be most critical at the ER-mitochondria interface and the AIS? Is there any preliminary reason why those lipids would be disrupted in ALS?

**中文译文 · 机器初译**

专家2：对于“Idea 2”方案，我认可其大胆的思路，但将ISR作为触发因素这一做法与传统观点有很大不同。该方案的支持者能否详细阐述支撑这一观点的证据？此外，他们认为在内质网-线粒体界面和AIS处哪些具体的脂质种类最为关键？是否有初步理由说明这些脂质在ALS中会受到破坏？

### co-scientist-0823

**English original**

Expert 3: I agree with Expert 2 regarding the ISR. Shifting it from a response to a trigger is a big claim that needs strong justification. However, I think there are some initial clues that might

**中文译文 · 机器初译**

专家3：关于ISR问题，我同意专家2的观点。将其从响应转变为触发因素这一说法过于夸张，需要充分的依据。不过，我认为有一些初步线索可能……


### 原文第 133 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=133)

### co-scientist-0825

**English original**

be worth investigating. For example, there are reports that chronic low-level stress responses can actually be detrimental in some contexts. Perhaps a low, persistent activation of the ISR could predispose cells to damage. This idea needs to be fleshed out though.

**中文译文 · 机器初译**

值得进一步研究。例如，有报道指出，长期低水平压力反应在某些情境下实际上可能有害。或许持续低水平的ISR激活会使细胞更容易受损。不过这一观点还需要进一步详细阐述。

### co-scientist-0826

**English original**

...

**原文保留（专名、技术内容或文献信息） · 保留原文**

...

### co-scientist-0827

**English original**

Expert 3: I also find Idea 1 more compelling at this point. It's a more focused hypothesis with a clear path for experimental validation. While Idea 2 is undoubtedly more "outside the box," I'm concerned about the lack of evidence for the ISR as a trigger and the technical challenges. It feels like a high-risk, high-reward scenario, and given that we can only choose one, I'd prefer the more grounded approach of Idea 1. I do agree with the idea that the technical challenges are significant, but I like that the experiments proposed are standard and there are many commercial antibodies available to start testing this idea.

**中文译文 · 机器初译**

专家3：目前我认为方案1更具吸引力。这是一个更聚焦的假设，且实验验证路径清晰。虽然方案2无疑更具“创新性”，但我对其作为触发因素缺乏证据以及技术挑战感到担忧。这似乎是一个风险高、回报也高的场景，而由于我们只能选择一种方案，我更倾向于方案1这种更为稳健的方法。我确实认同技术挑战较大的观点，但令人欣慰的是所提出的实验都是标准的，而且有许多商业抗体可供使用以开始测试这一想法。

### co-scientist-0828

**English original**

...

**原文保留（专名、技术内容或文献信息） · 保留原文**

...

### co-scientist-0829

**English original**

Expert 2: Alright, I'm on board with Idea 1. Let's focus our efforts on testing this specific mechanism and address the motor neuron specificity question rigorously in the experimental design. Perhaps by comparing different cell types and focusing on motor neuron-specific RNAs, as suggested earlier. We should also consider investigating different types of stress and their combined effects.

**中文译文 · 机器初译**

专家2：好的，我同意方案1。让我们集中精力测试这一特定机制，并在实验设计中严格解决运动神经元特异性问题。或许可以像之前建议的那样，比较不同细胞类型并重点关注运动神经元特有的RNA。我们还应考虑研究不同类型的应激因素及其综合影响。

### co-scientist-0830

**English original**

Better idea: 1

**中文译文 · 机器初译**

更好的想法：1

### co-scientist-0831

**English original**

10.10 Example output of a critique by the Meta-review agent

**中文译文 · 机器初译**

10.10 Meta-review 智能体提出的评价示例输出

### co-scientist-0832

**English original**

This is an example of the meta-review critique generated by the Co-Scientist Meta-review agent for the Amyotrophic Lateral Sclerosis (ALS) mechanism research hypothesis.

**中文译文 · 机器初译**

这是由 Co-Scientist Meta-review 智能体针对肌萎缩侧索硬化症（ALS）机制研究假设所生成的元评论批评示例。

### co-scientist-0833

**English original**

I. Core Hypothesis and Mechanism: ●​ Primary Driver vs. Consequence: A very common critique across many ideas was the difficulty in proving that the proposed mechanism is a primary initiating event in ALS rather than a downstream consequence of other processes. Future ideas need to: ○​ Provide strong evidence for the temporal sequence of events using longitudinal experiments. ○​ Employ models where early-stage events can be studied and manipulated. ○​ Explicitly address whether the proposed mechanism is causative or correlative.

**中文译文 · 机器初译**

I. 核心假设与机制：●​主要驱动因素与后果：许多研究观点中常见的批评在于，难以证明所提出的机制是 ALS 的主要触发原因，而非其他过程的下游结果。未来的研究需要：○​通过纵向实验提供事件时间顺序的有力证据。○​使用能够研究并操控早期事件的模型。○​明确说明所提出的机制是因果关系还是相关性。


### 原文第 134 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=134)

### co-scientist-0835

**English original**

○​ Specifically knockdown the primary driver to prove it's necessary and sufficient to cause the pathology. ●​ Specificity: Many hypotheses were criticized for a lack of specificity in various aspects: ○​ Molecular Targets: Imprecise identification of specific proteins, RNA species, lipids, PTMs, etc. involved. Ideas should name specific candidates. ○​ Cellular Compartments: Vague localization (e.g., "mitochondria" or "AIS"). Ideas should pinpoint specific subcellular locations whenever possible. ○​ Disease Mechanisms: Broad terms like "oxidative stress" or "autophagy impairment." Ideas need to define the precise molecular events involved. ○​ Types of Stress: If stress is involved, the specific type of stress needs to be defined (e.g., ER stress, nutrient deprivation, mitochondrial stress, ionic stress). ○​ Temporality: The timing of the intervention is critical. Early vs. late events, duration of processes, etc., should be clearly specified. ●​ Motor Neuron Specificity: Given the focus on ALS, a strong explanation for why the proposed mechanism would specifically or preferentially affect motor neurons (and often specific subtypes of motor neurons) is crucial. Many ideas were critiqued for not adequately addressing this. ●​ Over-Simplification vs. Complexity: This is a balancing act. Some ideas were criticized for being too narrowly focused, potentially oversimplifying the complex, multifactorial nature of ALS. Others were criticized for being overly complex, making them difficult to test and validate experimentally. When in doubt, err on the side of testability in a reasonable timeframe and budget. ●​ ALS Subtype Relevance: Ideas should address whether the proposed mechanism is relevant to all ALS subtypes or specific to certain genetic or sporadic forms. Ideally, address how the proposed work will differentiate or be applicable to different subtypes. II. Experimental Design and Feasibility: ●​ Model System Limitations: Reviewers frequently pointed out the limitations of in vitro models, particularly iPSC-derived motor neurons. While valuable, these models may not fully capture the in vivo environment, cell-cell interactions, or the aging process. Future ideas need to: ○​ Acknowledge the limitations of the chosen model system. ○​ Propose validation in multiple model systems if possible, including eventually animal, ex-vivo and, if applicable, in-vivo models. ○​ Carefully consider and justify the choice of control cell types. ○​ Propose isogenic controls where relevant. ●​ Technical Challenges: Many ideas proposed experiments that are technically very challenging. Reviewers often raised concerns about feasibility and the potential for ambiguous results. Future ideas should: ○​ Demonstrate awareness of the technical hurdles. ○​ Propose realistic solutions and alternative approaches.

**中文译文 · 机器初译**

○​ 具体消除主要驱动因素，以证明其是导致该病理的必要且充分条件。●​ 特异性：许多假设因在多个方面缺乏特异性而受到批评：○​ 分子靶点：对涉及的具体蛋白质、RNA种类、脂质、表观修饰等识别不准确。提出的想法应明确具体的候选对象。○​ 细胞区室：定位模糊（例如“线粒体”或“AIS”）。
在可能的情况下，观点应明确具体的亚细胞位置。○​ 疾病机制：应使用“氧化应激”或“自噬功能障碍”等宽泛术语。观点需明确所涉及的具体分子事件。○​ 应激类型：如果涉及应激，需明确具体的应激类型（例如内质网应激、营养缺乏、线粒体应激、离子应激）。○​ 时间性：干预的时间点至关重要。
早期与晚期事件、过程持续时间等应明确说明。● 运动神经元的特异性：鉴于研究的重点在于ALS，必须给出充分的解释，说明所提出的机制为何能特别或优先影响运动神经元（以及特定的运动神经元亚型）。许多想法因未能充分解决这一问题而受到批评。● 过度简化与复杂性：这是一个平衡问题。有些想法因过于狭隘而受到批评，可能过度简化了ALS复杂的多因素特性；另一些想法则因过于复杂而难以通过实验进行验证和测试。
如有疑问，应优先选择能够在合理时间范围和预算内进行验证的方案。●​ ALS亚型相关性：研究内容应探讨所提出的机制是否适用于所有ALS亚型，还是仅适用于某些遗传或偶发形式。理想情况下，需说明所提出的研究如何区分或适用于不同的亚型。II. 实验设计与可行性：●​ 模型系统的局限性：审稿人经常指出体外模型的局限性，尤其是由iPSC衍生的运动神经元模型。尽管这些模型很有价值，但可能无法完全反映体内环境、细胞间相互作用或衰老过程。
未来的研究思路需要：○​ 认识到所选模型系统的局限性。○​ 尽可能在多种模型系统中进行验证，包括最终采用动物模型、离体模型，以及适用时体内模型。○​ 仔细考虑并说明控制细胞类型的选择依据。○​ 在相关情况下提出同基因对照方案。●​ 技术挑战：许多研究思路所涉及的实验在技术上非常具有挑战性。审稿人往往对可行性及结果的不确定性表示担忧。未来的研究思路应：○​ 体现对技术障碍的认识。○​ 提出切实可行的解决方案及替代方法。


### 原文第 135 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=135)

### co-scientist-0837

**English original**

○​ Prioritize experiments that are most likely to yield clear, interpretable data. ●​ Specificity of Tools: When using inhibitors, antibodies, or other tools, their specificity needs to be carefully considered and validated to avoid off-target effects that can confound results. Appropriate controls and validation experiments must be included. ●​ Quantitative Rigor: Many critiques centered on the need for more rigorous quantification of experimental results. Future ideas need to: ○​ Clearly define measurable outcomes. ○​ Describe the specific assays and techniques that will be used for quantification. ○​ Include appropriate statistical analysis plans. ○​ Have a proposed plan for controls, replicates, and sample sizes. ●​ Time-Course Experiments: Given the dynamic nature of cellular processes, incorporating time-course experiments is often crucial to understanding the sequence of events and demonstrating causality. ●​ Distinguishing Cause from Effect: This requires careful experimental design, including: ○​ Longitudinal studies to observe the temporal order of events. ○​ Intervention experiments to manipulate the proposed cause and observe the effects downstream. ○​ Temporal resolution to demonstrate that the potential cause occurs before a downstream event. III. Novelty and Impact: ●​ Incremental vs. Groundbreaking: Many ideas were criticized for being incrementally novel, building upon existing knowledge rather than proposing truly groundbreaking mechanisms. ●​ "Key Switch" Claims: Several ideas were criticized for prematurely claiming that the proposed mechanism is the "key switch" for ALS. This type of strong claim requires very strong supporting evidence. It is often better to frame the hypothesis in terms of a significant contributing factor and test its requirement for the pathology. ●​ Therapeutic Potential: While not always explicitly stated, the potential for translating the findings into therapeutic strategies is an important consideration. Ideas that offer a clear path toward therapeutic development may be viewed more favorably, provided a strong rationale is presented for the specific therapeutic approach. IV. Assumptions and Validation: ●​ Strong Assumptions: Many hypotheses rely on strong assumptions that lack direct experimental support. Future ideas need to: ○​ Clearly state all assumptions. ○​ Provide a strong rationale for each assumption, citing relevant literature. ○​ Propose experiments to directly test the most critical assumptions. ●​ Validation of Assumptions: ○​ Reviewers consistently emphasized the need for rigorous experimental validation of all assumptions.

**中文译文 · 机器初译**

○​ 优先进行那些最有可能产生清晰、可解释数据的实验。●​ 工具的特异性：使用抑制剂、抗体或其他工具时，必须仔细考虑并验证其特异性，以避免产生可能干扰结果的脱靶效应。必须包含适当的对照和验证实验。●​ 定量严谨性：许多批评意见都强调需要更严格地量化实验结果。
未来的研究方案需包含：○​明确可量化的结果指标。○​说明用于量化的具体检测方法与技术。○​包含适当的统计分析方案。○​制定关于对照组、重复实验及样本量的计划。●​时间进程实验：由于细胞过程的动态性，开展时间进程实验对于理解事件顺序及证明因果关系至关重要。●​区分原因与结果：这需要严谨的实验设计，包括：○​纵向研究以观察事件的时间顺序。○​干预实验以操控所假设的原因并观察其效果。
下游效应。○​ 时间分辨率用于证明潜在原因发生在下游事件之前。III. 新颖性与影响力：●​ 增量性创新与突破性创新：许多想法因仅属于增量性创新而受到批评，它们只是基于现有知识进行扩展，而非提出真正具有突破性的机制。●​ “关键开关”主张：一些想法因过早声称所提出的机制是ALS的“关键开关”而受到批评。这种强有力的主张需要非常有力的支持证据。
通常更优的做法是将假设表述为重要的促成因素，并检验其与疾病病理之间的关联。● 治疗潜力：虽然并非总是明确提及，但将这些发现转化为治疗策略的潜力是一个重要的考量因素。如果针对特定治疗方案能提出充分的依据，那些为治疗发展提供明确路径的设想可能会获得更多认可。IV. 假设与验证：● 强假设：许多假设依赖于缺乏直接实验支持的强假设。
未来的研究思路需要：○​明确陈述所有假设。○​为每个假设提供有力的理论依据，并引用相关文献作为支撑。○​提出实验方案，以直接验证最关键的假设。●​假设的验证：○​审稿人始终强调需要对所有假设进行严格的实验验证。


### 原文第 136 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=136)

### co-scientist-0839

**English original**

○​ Assumptions should be addressed in the order of the proposed mechanism. ○​ If the initial steps are not validated, it may be unnecessary to proceed to later steps. V. General Advice Based on Common Critiques: ●​ Mechanistic Detail: Provide as much specific mechanistic detail as possible. Don't just state that pathway X is affected; describe how it is affected at the molecular level. ●​ Literature Review: Demonstrate a thorough understanding of the existing literature, including contradictory findings. Address how the proposed idea fits into the current understanding of ALS and how it differs from previous work. ●​ Focus on Causality: Always design experiments that can distinguish between cause and effect. ●​ Feasibility: Prioritize experiments that are feasible with available resources and expertise.

**中文译文 · 机器初译**

○​ 应按照所提出的机制顺序处理相关假设。○​ 如果初始步骤无法得到验证，可能无需继续推进后续步骤。V. 基于常见批评的一般建议：●​ 机制细节：尽可能提供具体的机制细节。不要仅说明路径X受到影响，而应描述其在分子层面是如何受影响的。●​ 文献综述：需展示对现有文献的全面理解，包括那些存在矛盾的研究结果。
说明所提出的想法如何与当前对ALS的理解相契合，以及它与以往研究有何不同。●​ 关注因果关系：始终设计能够区分因果关系的实验。●​ 可行性：优先选择利用现有资源和专业知识即可实施的实验。

### co-scientist-0840

**English original**

Consider using a phased experimental approach. Prioritize the experiments used to validate assumptions in the order they appear in the proposed mechanism. ●​ Strong Rationale: Provide a clear and compelling rationale for every aspect of the hypothesis and experimental design. ●​ Specificity of Controls: Explain why the choices of controls used in the experimental design are the best choice to test the effects of interest. Demonstrate that the effect is not due to a more general effect or mechanism. ●​ Address Limitations: Acknowledge the limitations of the proposed approach and discuss potential alternative explanations. ●​ Quantitative data: Emphasize quantitative data, consider including mathematical modeling of data where appropriate.

**中文译文 · 机器初译**

采用分阶段实验方法。按照所提出的机制中出现的顺序，优先进行用于验证假设的实验。●​ 充分的理由说明：对假设的每个方面及实验设计提供清晰且有力的理由说明。●​ 控制措施的针对性：解释为何实验设计中选择的控制措施是测试相关效应的最佳选择。
证明该效应并非由更普遍的影响或机制引起。●​ 应对局限性：承认所提出方法的局限性，并探讨可能的替代解释。●​ 定量数据：强调定量数据，在适当情况下考虑纳入数据的数学建模。

### co-scientist-0841

**English original**

10.11 Example of a research overview by the Meta-review agent

**中文译文 · 机器初译**

10.11 由 Meta-review 智能体提供的研究综述示例

### co-scientist-0842

**English original**

This is an example of a research overview generated by the Co-Scientist Meta-review agent for the research goal pertaining to explaining the basic mechanism of Amyotrophic Lateral Sclerosis (ALS). In addition to the individual hypotheses, this is the main output presented to the scientist by Co-Scientist.

**中文译文 · 机器初译**

这是由“联合科学家”智能体为研究目标生成的研究综述示例，该研究目标在于解释肌萎缩侧索硬化症（ALS）的基本机制。除了各个独立假设之外，这就是“联合科学家”向科学家呈现的主要成果。

### co-scientist-0843

**English original**

[Main Research Directions]

**中文译文 · 机器初译**

[主要研究方向]

### co-scientist-0844

**English original**

We will be focusing on these interrelated areas: ●​ Mitochondrial Dysfunction and Oxidative Stress: This direction investigates defects in mitochondrial DNA repair, mitochondrial dynamics, calcium handling, and oxidative

**中文译文 · 机器初译**

我们将重点关注这些相互关联的领域：● 线粒体功能障碍与氧化应激：该方向研究线粒体DNA修复、线粒体动态、钙处理以及氧化过程中的缺陷


### 原文第 137 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=137)

### co-scientist-0846

**English original**

stress response, focusing on their role in initiating inflammatory signaling and neurodegeneration. ●​ RNA Processing and Stress Granules: This direction explores abnormalities in RNA processing, transport, and modification, as well as impaired stress granule dynamics, and their impact on protein homeostasis and neuronal survival. It includes examining RNA-binding proteins, RNA structure and modifications, translation defects, and the interplay between RNA and proteostatic stress responses. ●​ Protein Homeostasis and the Nucleocytoplasmic Transport: This direction is aimed at investigating defects in protein folding, trafficking, aggregation, and degradation, as well as nucleocytoplasmic transport (NCT) dysfunction, with a particular focus on the nuclear pore complex (NPC). This includes how those pathways and processes influence, and are influenced by, TDP-43 and FUS protein function and localization. ●​ ...

**中文译文 · 机器初译**

压力反应，重点探讨其在引发炎症信号传导和神经退化中的作用。●​ RNA加工与压力颗粒：该研究方向关注 RNA 加工、运输和修饰的异常，以及压力颗粒功能的受损，及其对蛋白质稳态和神经元存活的影响。
该方向包括研究RNA结合蛋白、RNA结构与修饰、翻译缺陷，以及RNA与蛋白质稳态应激反应之间的相互作用。●​ 蛋白质稳态与核质运输：这一研究方向旨在探讨蛋白质折叠、转运、聚集和降解的缺陷，以及核质运输功能障碍，尤其关注核孔复合体（NPC）。其中还涉及这些途径和过程如何影响并受TDP-43和FUS蛋白的功能与定位所影响。●​...

### co-scientist-0847

**English original**

Mitochondrial Dysfunction and Oxidative Stress ●​ Rationale: Mitochondrial dysfunction and oxidative stress are consistently implicated in ALS pathogenesis. Mitochondria are critical for cellular energy production, and their dysfunction can lead to a cascade of events including increased oxidative stress, impaired calcium handling, inflammation, and ultimately cell death. Given the high energy requirements of motor neurons, especially upper motor neurons, these deficits are expected to have a significant impact. We hypothesize that specific mitochondrial vulnerabilities, not just generalized dysfunction play a very early role in initiating disease and provide a specific cellular event which can be targeted for research and for potential future therapy. ●​ Recent Findings: Research has shown that mutations in mitochondrial DNA (mtDNA) maintenance genes are associated with ALS. Further there are links between impaired mitochondrial calcium handling and oxidative stress, with a particular focus on base excision repair (BER) pathway defects and a potential link to activation of the cGAS-STING pathway. These findings suggest that a deeper understanding of mtDNA integrity, repair mechanisms, and ROS dynamics is critical for uncovering the initial drivers of ALS. ●​ Areas of Research: ○​ Mitochondrial DNA Repair Defects: ■​ Why Research? Explore the possibility that a deficiency in base excision repair (BER) enzymes for mitochondrial DNA is a primary driver of ALS. ■​ What to Research? Investigate the activity and expression of specific BER enzymes (e.g., OGG1) in iPSC-derived motor neurons from ALS patients and controls. Assess whether deficiencies correlate with increased accumulation of oxidized mtDNA lesions (e.g., 8-oxo-dG) and whether

**中文译文 · 机器初译**

线粒体功能障碍与氧化应激 ●​ 理论依据：线粒体功能障碍和氧化应激始终与ALS的发病机制密切相关。线粒体对细胞能量产生至关重要，其功能障碍会导致一系列连锁反应，包括氧化应激加剧、钙调节异常、炎症以及最终的细胞死亡。鉴于运动神经元，尤其是上运动神经元具有极高的能量需求，这些缺陷预计会产生显著影响。
我们提出一种假设：并非仅仅是普遍的功能障碍，而是特定的线粒体脆弱性在疾病发生过程中起着非常早的作用，并且它构成了一种可针对的研究与未来治疗目标的具体细胞事件。●​ 最新研究发现：研究表明，线粒体DNA（mtDNA）维持基因的突变与ALS有关。此外，受损的线粒体钙处理机制与氧化应激之间存在关联，尤其关注碱基切除修复（BER）途径的缺陷，以及可能与cGAS-STING途径的激活有关。
这些研究结果表明，深入理解线粒体 DNA 的完整性、修复机制及活性氧动态对于揭示 ALS 的初始致病因素至关重要。●​ 研究领域：○​ 线粒体 DNA 修复缺陷：■​ 为何进行研究？探讨线粒体 DNA 碱基切除修复（BER）酶缺乏是否是 ALS 的主要致病因素。■​ 需研究的内容是什么？调查 ALS 患者与对照组 iPSC 来源的运动神经元中特定 BER 酶（如 OGG1）的活性和表达情况。评估这些缺陷是否与氧化线粒体 DNA 损伤（如 8-oxo-dG）的增加相关。


### 原文第 138 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=138)

### co-scientist-0849

**English original**

these can be released into the cytoplasm after VDAC or MOMP activation. Determine if this release activates the cGAS-STING pathway. ■​ Example Idea: Measure OGG1 enzyme activity, oxidized mtDNA levels (8-oxo-dG) and cGAS-STING activation in iPSC-derived motor neurons.

**中文译文 · 机器初译**

这些物质在 VDAC 或 MOMP 激活后可释放到细胞质中。确定这种释放是否会激活 cGAS-STING 通路。■​ 示例思路：在 iPSC 来源的运动神经元中测量 OGG1 酶活性、氧化线粒体 DNA 水平（8-oxo-dG）以及 cGAS-STING 通路的激活情况。

### co-scientist-0850

**English original**

Genetically manipulate (knock-out/overexpress) key components of the mitochondrial BER pathway or target specific pathways using small molecules. Use VDAC inhibitors to prevent release or modulate MOMP function to understand cause and effect of ox-mtDNA release and cGAS-STING activation on cell death and inflammatory outcomes. ○​ Mitochondrial Calcium Handling and Oxidative Stress: ■​ Why Research? Motor neurons have high calcium demands and are sensitive to oxidative damage. Imbalances in mitochondrial calcium handling and ROS production may trigger a cascade leading to neurodegeneration. ■​ What to Research? Examine the role of mitochondrial calcium uniporter (MCU) and other calcium transporters in ALS. Assess if dysregulated calcium influx into mitochondria leads to increased ROS production and whether this is different in different types of motor neurons. Study the potential role of calcium handling defects as a primary trigger or modifier of the disease. ■​ Example Idea: Use calcium indicators and ROS sensors in iPSC-derived motor neurons to monitor real-time calcium and ROS levels in mitochondria. Manipulate mitochondrial calcium uptake via pharmacological or genetic approaches (e.g., MCU inhibitors or knock-outs). Assess cell survival and the impact on inflammatory response markers and activation of the cGAS-STING pathway to assess direct causality. ○​ …

**中文译文 · 机器初译**

通过小分子药物对线粒体 BER 通路的关键成分进行基因操作（敲除/过表达），或针对特定通路进行干预。利用 VDAC 抑制剂来阻止线粒体 DNA 的释放，或调节 MOMP 功能，以探究线粒体 DNA 释放与 cGAS-STING 激活对细胞死亡及炎症反应的影响机制。○​ 线粒体钙处理与氧化应激：■​ 为何研究？运动神经元对钙的需求较高，且对氧化损伤非常敏感。线粒体钙处理与活性氧产生的失衡可能导致连锁反应，进而引发神经退化。■​ 需研究的内容是什么？
探讨线粒体钙单转运体（MCU）及其他钙转运体在肌萎缩侧索硬化症中的作用。评估线粒体中钙流入异常是否会导致活性氧生成增加，以及这种现象在不同类型的运动神经元中是否存在差异。研究钙处理缺陷作为疾病主要诱因或修饰因素的可能作用。■​ 示例思路：在诱导的多能干细胞衍生的运动神经元中使用钙指示剂和活性氧传感器，以实时监测线粒体中的钙和活性氧水平。通过药物或基因手段调控线粒体对钙的摄取（例如使用MCU抑制剂或敲除技术）。
评估细胞存活情况及其对炎症反应标志物的影响，以及 cGAS-STING 通路的激活情况，以判断直接因果关系。○​ …

### co-scientist-0851

**English original**

RNA Processing and Stress Granules: ●​ ...

**中文译文 · 机器初译**

RNA加工与应激颗粒：●​...

### co-scientist-0852

**English original**

Protein Homeostasis and the Nucleocytoplasmic Transport: ●​ Rationale: The proper folding, trafficking, degradation, and localization of proteins are critical for cellular function. Defects in these processes can lead to the accumulation of toxic protein aggregates, disrupt cellular signaling, and initiate pathways leading to cell death in ALS. The nucleus is a key compartment, and transport into and out of this organelle is essential for cellular function. ●​ Recent Findings: Research has identified misfolded TDP-43 and FUS as key pathological features of ALS. Furthermore, the dysregulation of nucleocytoplasmic transport (NCT)

**中文译文 · 机器初译**

蛋白质稳态与核质运输：●​ 理论依据：蛋白质的正确折叠、转运、降解及定位对细胞功能至关重要。这些过程的异常可能导致有毒蛋白质聚集体积累、破坏细胞信号传导，并引发导致ALS细胞死亡的病理过程。细胞核是一个关键结构，该细胞器的进出运输对细胞功能具有重要作用。●​ 最新研究进展：研究已确定错误折叠的TDP-43和FUS是ALS的重要病理特征。此外，核质运输的失调也是导致疾病的关键因素。


### 原文第 139 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=139)

### co-scientist-0854

**English original**

and the nuclear pore complex (NPC) is a recurring feature, with recent findings that emphasize defects in early stages of assembly and dynamic function of the NPC as an early initiating step. ●​ Areas of Research: ○​ Ubiquitin-Proteasome System (UPS) Dysfunction: ■​ Why Research? The UPS is a major cellular protein degradation machinery. Defects in the UPS can lead to an accumulation of misfolded proteins, which could lead to cellular stress and death. Exploring the potential of a functional deficiency in these system as an early trigger in disease. ■​ What to Research: Investigate how UPS functionality is altered in ALS models, with particular attention to the role of E3 ligases in TDP-43 and FUS degradation. Determine whether specific modifications on ALS related proteins impair their degradation and whether specific pathways of protein quality control are affected in early stages of the disease. Assess if this is a primary cause or secondary outcome of other disease related pathways. ■​ Example Idea: Use cell-based assays to measure UPS activity and substrate degradation rates in iPSC-derived motor neurons. Conduct proteomic analysis to identify specific ubiquitinated proteins that accumulate in ALS cells. Genetically manipulate UPS components or use small molecules to modulate their function and assess cellular responses (e.g. measuring protein aggregation and cell survival). ○​ Autophagy Dysfunction: ■​ Why Research? Autophagy is crucial for clearing cellular debris and aggregates. Dysfunctional autophagy can lead to the accumulation of toxic proteins and can lead to organelle defects. ■​ What to Research? Explore how autophagy pathways are altered in ALS, focusing on the specific mechanisms of cargo recognition, autophagosome formation, and lysosome fusion. Assess if specific types of autophagy including mitophagy (mitochondrial specific) or lipophagy (lipid specific) are more vulnerable in specific cell types. ■​ Example Idea: Track the formation and degradation of autophagosomes in real-time in hiPSC-derived motor neurons after different stress conditions.

**中文译文 · 机器初译**

核孔复合体（NPC）是一个常见的特征，最新研究指出，在组装的早期阶段以及NPC的动态功能中存在缺陷，这些缺陷是引发疾病的重要早期因素。● 研究领域：○ 泛素-蛋白酶体系统（UPS）功能障碍：■ 为何进行研究？UPS是细胞中的主要蛋白质降解机制。UPS的缺陷会导致错误折叠蛋白质的积累，进而引发细胞应激和死亡。
探索这些系统中功能缺陷作为疾病早期诱因的潜力。■​ 研究方向：研究ALS模型中UPS功能的改变情况，特别关注E3连接酶在TDP-43和FUS降解过程中的作用。确定与ALS相关的特定蛋白质修饰是否会阻碍其降解，以及蛋白质质量控制的具体途径在疾病早期阶段是否受到影响。评估这是否是其他疾病相关途径的主要原因还是次要结果。■​ 示例思路：利用细胞实验方法测量iPSC来源运动神经元中的UPS活性及底物降解速率。
进行蛋白质组分析，以识别在ALS细胞中积累的特定泛素化蛋白质。通过基因操作UPS成分或使用小分子调节其功能，并评估细胞反应（例如测量蛋白质聚集和细胞存活情况）。○​ 自噬功能障碍：■​ 为何研究？自噬对于清除细胞碎片和聚集物至关重要。功能异常的自噬会导致有毒蛋白质的积累，并可能导致细胞器缺陷。■​ 研究内容是什么？探索ALS中自噬途径如何发生改变，重点研究货物识别、自噬体形成和溶酶体融合的具体机制。
评估特定类型的自噬现象，包括线粒体特异性自噬或脂质特异性自噬，在特定细胞类型中是否更为脆弱。■​ 示例思路：在不同应激条件下，实时追踪诱导多能干细胞衍生的运动神经元中自噬体的形成与降解过程。

### co-scientist-0855

**English original**

Manipulate key effectors of the autophagy pathway and observe cellular response, measuring protein aggregation, cell viability and inflammatory markers. ○​ Nucleocytoplasmic Transport (NCT) Defects: ■​ ... ○​ Targeted Protein Misfolding:

**中文译文 · 机器初译**

操控自噬途径的关键调控因子，观察细胞反应，测量蛋白质聚集、细胞存活率和炎症标志物。○​核质运输缺陷：■​... ○​ 目标蛋白错误折叠：


### 原文第 140 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=140)

### co-scientist-0857

**English original**

■​ … ●​ …

**原文保留（专名、技术内容或文献信息） · 保留原文**

■​ … ●​ …

### co-scientist-0858

**English original**

10.12 Example of research contact identification by the Meta-review agent

**中文译文 · 机器初译**

10.12 通过元评估智能体进行研究联系识别的示例

### co-scientist-0859

**English original**

This is an example of a research contact identified by the Meta-review agent as a potential domain expert in the research topic and hypothesis of interest.

**中文译文 · 机器初译**

这是 Meta-review 智能体识别出的一个研究联系人示例，该人被视为所关注研究主题和假设领域的潜在领域专家。

### co-scientist-0860

**English original**

Research Direction: Oxidative DNA Damage & Mitochondrial Base Excision Repair (BER) in ALS ●​ [Researcher names]: They directly study the role of mitochondrial OGG1 (a key BER enzyme) in controlling cytosolic mtDNA release and neuroinflammation. Their expertise is highly valuable for understanding the link between BER, mtDNA, and inflammation.

**中文译文 · 机器初译**

研究方向：ALS中的氧化DNA损伤与线粒体碱基切除修复（BER）●​ [研究人员姓名]：他们直接研究线粒体OGG1（一种关键的BER酶）在控制胞质mtDNA释放和神经炎症中的作用。他们的专业知识对于理解BER、mtDNA与炎症之间的关联具有极高的价值。

### co-scientist-0861

**English original**

Also, they have experience with experiments using mtOGG1 overexpressing mice which is relevant to the in-vitro experiments proposed. ●​ …

**中文译文 · 机器初译**

此外，他们拥有使用mtOGG1过表达小鼠进行实验的经验，这与所提出的体外实验密切相关。●​ …


### 原文第 141 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=141)

### co-scientist-0863

**English original**

11 An example of tool use in Co-Scientist with AlphaFold

**中文译文 · 机器初译**

11 使用工具在 AlphaFold 辅助科学家中的示例

### co-scientist-0864

**English original**

Co-Scientist is a general purpose system broadly applicable across different areas of science and medicine. To better understand the capabilities and limitations of the system, we task it with the goal of suggesting protein sequences with specific properties. Determining the correct primary amino acid sequence with the desired properties is an essential part of protein engineering. While LLM-based systems can predict protein properties and suggest modifications 68, they can sometimes generate incorrect sequences (i.e., hallucinations). To address this, we integrate AlphaFold 69, a specialized AI system for predicting protein 3D structure, into our Co-Scientist. AlphaFold acts as a validation tool, evaluating the structural plausibility of sequences proposed by Co-Scientist and provides feedback. This increases the reliability of the sequence design optimization process, which can be further validated with wet laboratory experiments. The approach to integrate tools highlights how specialized AI models can work in collaboration with more general AI systems like Co-Scientist, facilitating the solution of complex challenges like protein design.

**中文译文 · 机器初译**

Co-Scientist 是一种通用系统，可广泛应用于科学与医学的各个领域。为了更全面地了解该系统的能力与局限，我们赋予其任务：提出具有特定特性的蛋白质序列。确定具有所需特性的正确一级氨基酸序列是蛋白质工程的重要组成部分。虽然基于 LLM 的系统能够预测蛋白质特性并提出修饰建议，但有时也会生成错误的序列（即“幻觉”）。为解决这一问题，我们将用于预测蛋白质 3D 结构的专用 AI 系统 AlphaFold 整合到了 Co-Scientist 中。
AlphaFold 充当一种验证工具，用于评估共科学家提出的序列的结构合理性，并提供反馈。这提升了序列设计优化过程的可靠性，而这一过程又可以通过湿实验室实验进一步验证。这种整合工具的方案凸显了专业人工智能模型如何与更通用的人工智能系统（如共科学家）协同工作，从而帮助解决蛋白质设计等复杂问题。

### co-scientist-0865

**English original**

As an illustrative example, we used AlphaFold to assess a Co-Scientist’s proposed modification to the OCT4 (octamer-binding transcription factor 4) protein (Supplementary Fig. 9), one of the four Yamanaka factors 70, to increase binding affinity of its DNA binding domain. Co-Scientist suggested adding a mechano-sensitive loop to the POU domain (a family of eukaryotic transcription factors) and a dynamic phosphorylation site outside of it. Co-Scientist first verified the proposed sequence against the UniProt database via web-search. AlphaFold then predicted the 3D structure of the modified protein, suggesting that the modifications maintained structural stability. These predictions were used to refine Co-Scientist's hypothesis, allowing it to improve its protein sequence design in subsequent iterations. We also independently validated the modification using ESM-2 71, ESMFold 71, and RoseTTAFold 72. ESM-2 predicted an increased log-likelihood ratio, ESMFold predicted a similar predicted local distance difference test (pLDDT), and RoseTTAFold predicted a similar confidence score (GDT), compared to the original sequence. The insertion and modification did not seem to disrupt SOX2 and OCT4 interactions, indicated by the similar pLDDT scores between the original and modified OCT4 sequences. However, this example is for demonstration purposes only. Further in silico analysis (e.g., predicting binding affinity and off-target effects), and thorough laboratory validation are necessary to confirm that the proposed modifications actually improve the complex roles of OCT4 binding, while maintaining SOX2 interaction integrity, during pluripotency.

**中文译文 · 机器初译**

作为示例，我们使用 AlphaFold 来评估一位合作科学家提出的对 OCT4（八聚体结合转录因子 4）蛋白的修改方案（补充图 9）。该蛋白属于 Yamanaka 因子家族中的四个成员之一，其目的是提高 DNA 结合域的结合亲和力。合作科学家建议在 POU 结构域（一种真核转录因子）中添加一个机械敏感环，并在其外部添加一个动态磷酸化位点。合作科学家首先通过网络搜索将所提出的序列与 UniProt 数据库进行比对验证。随后，AlphaFold 预测了该修饰蛋白的三维结构，表明这些修改保持了结构的稳定性。
这些预测结果被用于完善共科学家模型的假设，使其在后续迭代中能够改进其蛋白质序列设计。我们还使用 ESM-2 71、ESMFold 71 和 RoseTTAFold 72 对这一修改进行了独立验证。与原始序列相比，ESM-2 预测了更高的对数似然比，ESMFold 预测了类似的局部距离差异测试结果（pLDDT），而 RoseTTAFold 则预测了类似的置信度得分（GDT）。插入和修饰操作似乎并未破坏 SOX2 与 OCT4 之间的相互作用，这一点从原始序列与修饰后的 OCT4 序列之间相似的 pLDDT 得分可以看出来。不过，这个例子仅用于演示目的。
还需要进行进一步的计算机模拟分析（例如预测结合亲和力及脱靶效应），并开展全面的实验室验证，以确认所提出的修改确实能改善 OCT4 的结合作用复杂性，同时保持 SOX2 相互作用的完整性，从而维持多能性状态。

### co-scientist-0866

**English original**

Integrating AlphaFold within the Co-Scientist system offers a powerful approach for both improving existing proteins and designing entirely new ones. This integrated system allows researchers to iteratively optimize protein sequences for enhanced properties (e.g., stability, binding affinity, or catalytic activity) or putatively to create proteins with novel functions. It enables exploration of protein design while ensuring structural feasibility. Future work will focus on experimentally validating these capabilities and applying them to targeted protein design efforts as well as expansion to integration of other specialized AI tools with Co-Scientist.

**中文译文 · 机器初译**

将 AlphaFold 整合到 Co-Scientist 系统中，为改进现有蛋白质以及设计全新蛋白质提供了强大的方法。这一集成系统使研究人员能够逐步优化蛋白质序列，以提升其性能（如稳定性、结合亲和力或催化活性），或创造出具有新功能的蛋白质。它能够在确保结构可行性的同时推动蛋白质设计的探索。未来的研究将重点在于通过实验验证这些能力，并将其应用于有针对性的蛋白质设计工作，同时进一步将其他专业人工智能工具与 Co-Scientist 相结合。


### 原文第 142 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=142)

### co-scientist-0868

**English original**

Supplementary Fig. 9 | AlphaFold predicted protein 3D structure and metrics for original OCT4 and Co-Scientist suggested modifications. (left panel) original OCT4 sequence with SOX2 and DNA binding (right panel) modified OCT4 sequence with SOX2 and DNA binding. The left 3D structure in each panel is the POU domain of the corresponding OCT4 sequence. The predicted template modeling (pTM) score, the interface predicted template modeling (ipTM), and predicted local distance difference test (pLDDT) are derived from the AlphaFold outputs.

**中文译文 · 机器初译**

补充图9 | AlphaFold预测的蛋白质3D结构以及原始OCT4和Co-Scientist提出的修改方案的相关指标。（左图）包含SOX2和DNA结合功能的原始OCT4序列；（右图）经过SOX2和DNA结合修饰后的OCT4序列。每个图中的左侧3D结构均为对应OCT4序列的POU域。预测的模板建模得分（pTM）、界面预测模板建模得分（ipTM）以及预测的局部距离差异测试（pLDDT）均来自AlphaFold的输出结果。


### 原文第 143 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=143)

### co-scientist-0870

**English original**

12 Related works

**中文译文 · 机器初译**

12 相关研究

### co-scientist-0871

**English original**

Reasoning models and test-time compute scaling. The modern revolution in foundation AI models 73 and large language models (LLMs) has been largely driven by advances in pre-training techniques 74,75, leading to breakthroughs in models like the GPT and Gemini family 76,77. These models, trained on increasingly massive internet-scale and multimodal datasets, have demonstrated impressive abilities in language understanding and generation leading to breakthrough performance in a variety of benchmarks 78,79. However, a key area of ongoing development is enhancing their reasoning capabilities. This has led to the emergence of “reasoning models” which go beyond simply predicting the next word and instead attempt to mimic human thought processes 80. One promising direction in this pursuit is the test-time compute paradigm. This approach moves beyond solely relying on the knowledge acquired during pre-training and allocates additional computational resources during inference to enable System-2 style thinking, which is a slower deliberate reasoning to reduce uncertainty and progress optimally towards the goal 81. This concept emerged with early successes such as AlphaGo 82, which used Monte Carlo Tree Search (MCTS) to explore game states and strategically select moves, and Libratus 83, which employed similar techniques to achieve superhuman performance in poker. This paradigm has now found applications in LLMs, where increased compute at test-time allows for more thorough exploration of possible responses, leading to improved reasoning and accuracy 80,84–90. Recent advancements, like the Deepseek-R1 model 91, further demonstrate the potential of test-time compute by leveraging reinforcement learning to refine the model’s “chain-of-thought” and enhance complex reasoning abilities over longer horizons. In this work, we propose a significant scaling of the test-time compute paradigm using inductive biases derived from the scientific method to design a multi-agent framework for scientific reasoning and hypothesis generation without any additional learning techniques.

**中文译文 · 机器初译**

推理模型与测试时计算能力的扩展。基础人工智能模型及大语言模型领域的现代革命，主要得益于预训练技术的进步，从而实现了 GPT 和 Gemini 系列模型等模型的突破。这些模型在日益庞大的互联网规模和多模态数据集上进行训练，在语言理解与生成方面展现出出色的能力，并在多种基准测试中取得了显著的性能表现。然而，当前发展的关键领域在于提升它们的推理能力。
这促使“推理模型”的出现，这些模型不再仅仅预测下一个词，而是试图模仿人类的思维过程 80。在这一探索方向上，一个具有前景的方向是测试时计算范式。这种方法不再仅依赖预训练期间获得的知识，而是在推理过程中分配额外的计算资源，以实现系统二型思维，这是一种较慢的刻意推理方式，有助于降低不确定性并朝着目标最优地推进 81。
这一概念源于早期的成功案例，例如使用蒙特卡洛树搜索（MCTS）来探索游戏状态并策略性选择行动的大语言模型 AlphaGo 82，以及采用类似技术在扑克游戏中取得超凡表现的Libratus 83。如今，这种范式已应用于大语言模型中：在测试阶段增加计算能力能够更全面地探索各种可能的回应，从而提升推理能力和准确性 80,84–90。像Deepseek-R1模型这样的最新进展进一步展示了测试阶段计算能力的潜力，通过利用强化学习来优化模型的“思维链”机制，增强其在更长时间跨度内的复杂推理能力。
在本研究中，我们提出了一种显著的测试时计算范式扩展方案，利用源自科学方法的归纳偏见来设计多智能体框架，用于科学推理和假设生成，且无需任何额外的学习技术。

### co-scientist-0872

**English original**

AI-driven scientific discovery. AI-driven scientific discovery represents a paradigm shift in how research is conducted across various scientific domains. Recent advancements, particularly the development of large deep learning and generative models, have cemented AI’s role in scientific discovery. This is best exemplified by AlphaFold 2’s remarkable progress in the grand challenge of protein structure prediction, which has revolutionized structural biology and opened new avenues for drug discovery and materials science 92. Other notable examples include the development of novel antibiotics, protein binder design, and material discovery with AI 93–95.

**中文译文 · 机器初译**

人工智能驱动的科学发现。人工智能驱动的科学发现标志着各科学领域研究方式发生了根本性转变。近期进展，尤其是深度学习和生成式模型的发展，进一步巩固了人工智能在科学发现中的地位。以 AlphaFold 2 在蛋白质结构预测这一重大挑战上的显著成果为例，它彻底改变了结构生物学领域，并为药物发现和材料科学开辟了新途径。其他值得关注的例子包括利用人工智能开发新型抗生素、设计蛋白质结合剂以及进行材料研究等。

### co-scientist-0873

**English original**

Building on these successes with specialized, bespoke AI models, there has been recent work exploring the even more ambitious goal of fully integrating AI, especially modern LLM-based systems, into the complete research workflow, from initial hypothesis generation all the way to manuscript writing. This end-to-end integration represents a significant shift, presenting both unprecedented opportunities and significant challenges as the field moves beyond specialized AI tools toward realizing the potential of AI as an active collaborator, or even, as some envision, a nascent “AI scientist” 96,97.

**中文译文 · 机器初译**

基于这些利用专业定制人工智能模型的成功成果，近期有研究致力于实现更为宏大的目标——将人工智能，尤其是基于大语言模型的系统，完全整合到完整的研究流程中，从最初的假设生成到论文撰写全过程。这种端到端的整合标志着一次重大变革，随着该领域从依赖专业人工智能工具转向让人工智能作为积极参与的协作者发挥作用，甚至如某些人所设想的那样成为新兴的“人工智能科学家”，这既带来了前所未有的机遇，也带来了巨大的挑战。96,97


### 原文第 144 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=144)

### co-scientist-0875

**English original**

As an example of this shift, Liang et al. 98 directly assessed the utility of LLMs for providing feedback on research manuscripts. Through both a retrospective analysis of existing peer reviews and a prospective user study, they demonstrated the significant concordance between LLM-generated feedback and that of human reviewers. Their study, using GPT-4 77, found that a majority of researchers perceived LLM-generated feedback as helpful, and in some instances, even more beneficial than feedback from human colleagues. However, while valuable, their work focuses solely on the feedback stage of the scientific process, leaving open the question of how LLMs might be integrated into the full research cycle, from hypothesis formation to experimental validation and manuscript writing.

**中文译文 · 机器初译**

作为这种转变的一个例子，Liang等人98直接评估了大语言模型在提供研究论文反馈方面的效用。通过现有同行评审的回顾性分析以及未来的用户研究，他们证明了大语言模型生成的反馈与人类评审者的反馈具有高度一致性。他们使用GPT-4 77进行的研究发现，大多数研究人员认为大语言模型生成的反馈很有帮助，在某些情况下甚至比人类同事的反馈更有益。
然而，尽管这些研究具有价值，但它们仅关注科学过程的反馈阶段，对于大语言模型如何融入从假设形成到实验验证及论文撰写的全研究流程，却缺乏探讨。

### co-scientist-0876

**English original**

Another effort embodying this shift is PaperQA2 99, an AI agent for scientific literature search and summarization. The authors claimed to surpass PhD and postdoc researchers on multiple literature research tasks, as measured both by performance on objective benchmarks and human evaluations. While the system is useful for synthesizing information, it does not engage in scientific reasoning for novel hypothesis generation.

**中文译文 · 机器初译**

体现这一转变的又一成果是 PaperQA2 99，这是一个用于科学文献搜索与总结的智能体。作者声称在多项文献研究任务上能够超越博士和博士后研究人员，这一成绩通过客观基准测试的结果以及人类评估均得到了验证。虽然该系统有助于信息整合，但并未参与新的假设生成过程中的科学推理过程。

### co-scientist-0877

**English original**

HypoGeniC, a system proposed by Zhou et al. 100, tackles hypothesis generation by iteratively refining hypotheses using LLMs and a multi-armed bandit-inspired approach. The process begins with a small set of examples, from which initial hypotheses are generated. These hypotheses are then iteratively updated through exploration and exploitation, guided by a reward function based on training accuracy. This refined set of hypotheses is subsequently used to construct an interpretable classifier. However, the method's reliance on retrospective data for evaluation means the degree to which the system can generate truly novel hypotheses remains an open question. Furthermore, the system lacks end-to-end validation beyond subjective human evaluations.

**中文译文 · 机器初译**

Zhou等人提出的HypoGeniC系统通过利用大语言模型和多臂老虎机启发式方法逐步优化假设，从而解决假设生成问题。该过程以少量示例为起点，从中生成初始假设；随后这些假设通过探索与利用机制不断迭代更新，并依据训练准确率相关的奖励函数进行指导。经过优化的假设集合随后被用于构建可解释的分类器。然而，由于该方法依赖回顾性数据进行评估，其能否生成真正新颖的假设程度仍是一个未解之谜。
此外，该系统缺乏超越主观人类评估的端到端验证机制。

### co-scientist-0878

**English original**

Ifargan et al. 101 present “data-to-paper”, a platform that systematically guides multiple LLM and rule-based agents to generate research papers, with automated feedback mechanisms and information tracing for verification. However, the evaluations are limited to recapitulating existing peer-reviewed publications and it is unclear if the system can generate truly novel, yet grounded hypotheses and research proposals.

**中文译文 · 机器初译**

Ifargan等人提出了“数据到论文”平台，该平台能够系统地引导多个大语言模型和基于规则的智能体生成研究论文，并配备自动反馈机制与信息追踪功能以进行验证。然而，目前的评估仅局限于对现有同行评审出版物的复现，目前尚不清楚该系统是否能够生成真正新颖且基于实际依据的假设与研究提案。

### co-scientist-0879

**English original**

Virtual Lab 102 is another closely related work. Here, the authors propose a team of LLM agents with a “principal investigator” LLM guiding a team of specialized LLM agents to solve a scientific problem. The LLM team receives high level human supervision. The authors demonstrate the utility of their work by leveraging Virtual Lab to design nanobody binders to recent variants of SARS-CoV-2 with experimental validation. While similar in spirit, there are significant design differences to our approach and the generality of the system remains unclear.

**中文译文 · 机器初译**

Virtual Lab 102是另一项密切相关的研究。在此研究中，作者提出了一组大语言模型智能体，其中有一个“首席研究员”大语言模型负责指导一组专业的大语言模型智能体来解决科学问题。该大语言模型团队能够获得高级人类指导。作者通过利用 Virtual Lab 设计针对最新变异型 SARS-CoV-2 的纳米蛋白结合剂，并进行了实验验证，从而展示了其工作的实用性。尽管两者在理念上相似，但我们的方法与该研究存在显著的设计差异，且系统的通用性仍不明确。

### co-scientist-0880

**English original**

Boiko et al. 103 introduced “Coscientist”, a multi-agent system powered by GPT-4, designed for autonomous execution of complex chemical experiments. This system integrates capabilities such as web and document searching, and code execution, to facilitate independent experimental design, planning, and execution. In addition to similar sounding names, both “Coscientist” and our system share the overarching goal of accelerating scientific discovery through AI. However, there are several important distinctions. Notably, “Coscientist” is quite

**中文译文 · 机器初译**

Boiko等人103提出了“Coscientist”，这是一个由GPT-4驱动的多智能体系统，旨在实现复杂化学实验的自主执行。该系统集成了网页与文档搜索、代码执行等功能，以助力独立的实验设计、规划与执行。除了名称相似外，“Coscientist”与我们的系统都拥有通过人工智能加速科学发现的核心目标。不过，两者也存在若干重要差异。值得注意的是，“Coscientist”具有完全不同的设计理念。


### 原文第 145 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=145)

### co-scientist-0882

**English original**

narrowly focused on chemical research while ours is much broadly applicable across science. Secondly, our system has important technical innovations that lead to a self-improving system that can uncover new, original knowledge while their approach is a more vanilla-stitching of GPT-4 based agents. Finally, despite the name, “Coscientist” prioritizes a high degree of autonomy in experimental execution, directly interfacing with laboratory hardware. Our system, instead, is explicitly designed as a collaborative tool, emphasizing a “scientist-in-the-loop” approach and centers on the more cognitive aspects of the research process.

**中文译文 · 机器初译**

我们的研究主要专注于化学领域，而我们的系统则具有更广泛的科学应用价值。其次，我们的系统拥有重要的技术创新，能够形成自我优化的系统，从而揭示新的原创知识；而他们的方法则更像是基于 GPT-4 的智能体的一般化应用。最后，尽管名为“Coscientist”，该系统强调实验执行的高度自主性，可直接与实验室硬件交互。相反，我们的系统被明确设计为协作工具，注重“科学家在循环中的参与”模式，并聚焦于研究过程中的认知层面。

### co-scientist-0883

**English original**

Finally, Lu et al. 96 propose “The AI Scientist”, a fully automated system designed to conduct research using multiple collaborating LLM agents. These agents handle all stages of the research process, from defining research problems and conducting literature reviews to designing and executing experiments, and even writing up the results. The design shares similarities with our work. The key differences being our focus on the scaling of the test-time compute paradigm to generate high quality hypotheses and research proposals. Secondly, their proposed system has limited automated evaluations; in contrast, our work has a combination of automated, human expert and end-to-end wet lab validations. Finally, our goal is to not to automate scientific discovery, rather to build a helpful AI collaborator for scientists.

**中文译文 · 机器初译**

最后，Lu等人提出了“AI科学家”这一完全自动化的系统，旨在利用多个协作的LLM智能体进行研究。这些智能体负责研究过程的各个阶段，从定义研究问题、进行文献综述到设计与执行实验，甚至撰写研究结果。该系统的设计与我们的工作有相似之处。主要的区别在于，我们专注于测试时计算模式的扩展，以生成高质量假设和研究提案。其次，他们提出的系统仅包含有限的自动化评估，而我们的工作则结合了自动化评估、人类专家评估以及端到端的湿实验室验证。
最后，我们的目标不是实现科学发现的自动化，而是为科学家打造一个有用的AI协作伙伴。

### co-scientist-0884

**English original**

AI for biomedicine. More broadly, large AI models are increasingly demonstrating their potential in biomedical science. Both general purpose (GPT-4, Gemini) and specialized LLMs (Med-PaLM, Med-Gemini, Galactica, Tx-LLM) have shown strong performance on biomedical reasoning and question-answering benchmarks 76,77,104–107. Beyond benchmarks, Med-PaLM 2, was successfully applied to identify causative murine genetic factors for traits such as diabetes, cataracts, and hearing loss 108, which is an early example of hypothesis generation and LLM-assisted discovery. We have also seen the exciting development of specialized foundation and large language models trained on DNA, RNA and protein sequences with a variety of applications 109–112. Although AI in biology and medicine often necessitates specialization, the rapid progress of frontier AI models has blurred the distinction. As these models grow in scale, data diversity, and complexity, they continue to achieve breakthroughs in areas once thought to require domain-specific AI. Our Co-Scientist, with its modular multi-agent architecture, is flexibly designed to build on top of these advancements in general-purpose frontier AI models and leverage specialized AI models as tools to enhance the capabilities. ​ Drug repurposing is an important area of validation experiments in this work. The traditional approach to this task requires both computational and experimental approaches and a comprehensive understanding of disease-drug interactions 113,114. While methods like knowledge graphs with graph convolutional networks have shown promise 115,116, their applicability is limited by the initial knowledge graph’s scope. TxGNN 117, an example of a specialized biomedical foundation model with a graph based approach, addresses “zero-shot” repurposing for novel diseases but remains dependent on the underlying knowledge graph’s quality and lacks sufficient scalability and explainability. Furthermore, no end-to-end validations of the model predictions were reported in the study. In contrast, our work, leveraging state-of-the-art LLMs in

**中文译文 · 机器初译**

用于生物医学领域的人工智能。更广泛地说，大语言模型在生物医学科学领域正逐渐展现其潜力。通用型模型（GPT-4、Gemini）与专业型LLM（Med-PaLM、Med-Gemini、Galactica、Tx-LLM）都在生物医学推理和问答测试上表现出优异表现，相关数据见76、77、104–107。除了测试外，Med-PaLM 2还被成功应用于识别导致糖尿病、白内障和听力损失等疾病的动物遗传因素，这便是假设生成与LLM辅助发现的一个早期实例。
我们也看到了针对DNA、RNA和蛋白质序列训练的专业基础模型及大语言模型的令人振奋的发展，这些模型具有多种应用前景（109–112）。尽管生物学和医学领域的AI通常需要专业化的技术，但前沿AI模型的快速进步已经模糊了这种界限。随着这些模型在规模、数据多样性和复杂性方面不断提升，它们继续在那些曾被认为需要领域特定AI的领域取得突破。
我们的联合科学家采用模块化多智能体架构设计，能够灵活利用通用前沿人工智能模型的进展，并将专业人工智能模型作为工具来提升其能力。药物重新应用是本研究中验证实验的重要领域。传统的处理方法需要计算与实验相结合的方式，以及对疾病-药物相互作用的全面理解 113,114。虽然基于图卷积网络的知识图谱等方法已显示出潜力 115,116，但其应用范围受初始知识图谱覆盖范围的限制。
TXGNN 117 是一个采用图结构方法的专业生物医学基础模型示例，能够实现针对新疾病的“零样本”重新应用，但仍依赖于底层知识图谱的质量，且缺乏足够的可扩展性和可解释性。此外，研究中并未报告对模型预测结果的端到端验证情况。相比之下，我们的研究利用最先进的 LLM 实现了……


### 原文第 146 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=146)

### co-scientist-0886

**English original**

the Co-Scientist setup is more scalable. We report a combination of expert evaluations and wet-lab experiments to validate the system predictions.

**中文译文 · 机器初译**

Co-Scientist 架构更具可扩展性。我们通过结合专家评估与湿实验室实验来验证系统的预测结果。


### 原文第 147 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=147)

### co-scientist-0888

**English original**

Supplementary references 1.​ Rein, D. et al. GPQA: A graduate-level Google-proof Q&A benchmark. in First Conference

**中文译文 · 机器初译**

补充参考文献 1. 雷因等. GPQA：一个针对研究生水平的、无需谷歌服务的问答基准测试. 发表于首届会议

### co-scientist-0889

**English original**

on Language Modeling (2024).

**中文译文 · 机器初译**

关于语言建模（2024）。

### co-scientist-0890

**English original**

2.​ Sexauer, A. N. et al. DHODH: a promising target in the treatment of T-cell acute

**中文译文 · 机器初译**

2.​ Sexauer, A. N. 等. DHODH：治疗T细胞急性病的有前景的靶点

### co-scientist-0891

**English original**

lymphoblastic leukemia. Blood Adv 7, 6685–6701 (2023).

**中文译文 · 机器初译**

淋巴母细胞白血病。Blood Adv 7, 6685–6701 (2023)。

### co-scientist-0892

**English original**

3.​ Broad. DepMap. DepMap Public 24Q2 (2024).

**中文译文 · 机器初译**

3.​ 广泛。DepMap。DepMap Public 2024年第二季度（2024年）。

### co-scientist-0893

**English original**

4.​ Arafeh, R., Shibue, T., Dempster, J. M., Hahn, W. C. & Vazquez, F. The present and future

**中文译文 · 机器初译**

4.​ Arafeh, R., Shibue, T., Dempster, J. M., Hahn, W. C. & Vazquez, F. 现状与未来

### co-scientist-0894

**English original**

of the Cancer Dependency Map. Nat. Rev. Cancer 25, 59–73 (2025).

**中文译文 · 机器初译**

关于癌症依赖图谱的研究。Nat. Rev. Cancer 25, 59–73 (2025)。

### co-scientist-0895

**English original**

5.​ van Herpen, C. M. L. et al. Biomarker results from a phase II study of MEK1/2 inhibitor

**中文译文 · 机器初译**

5.​ van Herpen, C. M. L. 等。MEK1/2抑制剂的II期研究中的生物标志物结果

### co-scientist-0896

**English original**

binimetinib (MEK162) in patients with advanced NRAS- or BRAF-mutated melanoma.

**中文译文 · 机器初译**

用于晚期 NRAS 或 BRAF 突变黑色素瘤患者的比米诺司特（MEK162）。

### co-scientist-0897

**English original**

Oncotarget 10, 1850–1859 (2019).

**中文译文 · 机器初译**

Oncotarget 10, 1850–1859 (2019)。

### co-scientist-0898

**English original**

6.​ Ball, B. J. et al. The prognosis and durable clearance of RAS mutations in patients with

**中文译文 · 机器初译**

6.​ Ball, B. J. 等。RAS突变患者预后及长期清除情况

### co-scientist-0899

**English original**

acute myeloid leukemia receiving induction chemotherapy. Am J Hematol 96, E171–E175

**中文译文 · 机器初译**

接受诱导化疗的急性髓系白血病患者。Am J Hematol 96, E171–E175

### co-scientist-0900

**English original**

(2021).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2021).

### co-scientist-0901

**English original**

7.​ Verstovsek, S. & Komrokji, R. S. A comprehensive review of pacritinib in myelofibrosis.

**中文译文 · 机器初译**

7.​ Verstovsek, S. & Komrokji, R. S. 关于骨髓纤维化中帕克里替丁的全面综述。

### co-scientist-0902

**English original**

Future Oncol 11, 2819–2830 (2015).

**中文译文 · 机器初译**

《Future Oncol》2015年，第11卷，第2819–2830页。

### co-scientist-0903

**English original**

8.​ Perrone, S., Ottone, T., Zhdanovskaya, N. & Molica, M. How acute myeloid leukemia

**中文译文 · 机器初译**

8.​ Perrone, S., Ottone, T., Zhdanovskaya, N. & Molica, M. 急性髓系白血病的治疗策略

### co-scientist-0904

**English original**

(AML) escapes from FMS-related tyrosine kinase 3 (FLT3) inhibitors? Still an overrated

**中文译文 · 机器初译**

(AML) 能否从与 FMS 相关的酪氨酸激酶 3 (FLT3) 抑制剂中逃脱？它仍然被高估了

### co-scientist-0905

**English original**

complication? Cancer Drug Resist 6, 223–238 (2023).

**中文译文 · 机器初译**

并发症？癌症药物耐药性 6, 223–238 (2023)。

### co-scientist-0906

**English original**

9.​ Bosman, M. C. J., Schuringa, J. J. & Vellenga, E. Constitutive NF-κB activation in AML:

**中文译文 · 机器初译**

9.​ Bosman, M. C. J., Schuringa, J. J. & Vellenga, E. 急性髓系白血病中NF-κB的形成性激活：

### co-scientist-0907

**English original**

Causes and treatment strategies. Crit Rev Oncol Hematol 98, 35–44 (2016).

**中文译文 · 机器初译**

病因与治疗策略。Crit Rev Oncol Hematol 98, 35–44 (2016)。

### co-scientist-0908

**English original**

10.​ Hou, S. et al. PHF6 maintains acute myeloid leukemia via regulating NF-κB signaling

**中文译文 · 机器初译**

10.​ Hou, S. 等研究指出，PHF6通过调节 NF-κB 信号通路维持急性髓系白血病

### co-scientist-0909

**English original**

pathway. Leukemia 37, 1626–1637 (2023).

**中文译文 · 机器初译**

路径。Leukemia 37, 1626–1637 (2023)。


### 原文第 148 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=148)

### co-scientist-0911

**English original**

11.​ Banker, D. E. et al. Cholesterol synthesis and import contribute to protective cholesterol

**中文译文 · 机器初译**

11.​ Banker, D. E. 等。胆固醇合成与摄取对保护性胆固醇具有贡献作用

### co-scientist-0912

**English original**

increments in acute myeloid leukemia cells. Blood 104, 1816–1824 (2004).

**中文译文 · 机器初译**

急性髓系白血病细胞的增量变化。Blood 104, 1816–1824 (2004)。

### co-scientist-0913

**English original**

12.​ Brehmer, D. et al. Discovery and Pharmacological Characterization of JNJ-64619178, a

**中文译文 · 机器初译**

12.​ Brehmer, D. 等。大语言模型 JNJ-64619178 的发现与药理学特性研究

### co-scientist-0914

**English original**

Novel Small-Molecule Inhibitor of PRMT5 with Potent Antitumor Activity. Mol Cancer

**中文译文 · 机器初译**

具有强抗肿瘤活性的PRMT5新型小分子抑制剂。分子癌症

### co-scientist-0915

**English original**

Ther 20, 2317–2328 (2021).

**中文译文 · 机器初译**

Ther 20, 2317–2328 (2021)。

### co-scientist-0916

**English original**

13.​ Haque, T. et al. Phase 1 study of JNJ-64619178, a protein arginine methyltransferase 5

**中文译文 · 机器初译**

13.​ Haque, T. 等。JNJ-64619178这种蛋白精氨酸甲基转移酶5的1期研究

### co-scientist-0917

**English original**

inhibitor, in patients with lower-risk myelodysplastic syndromes. Leuk Res 134, 107390

**中文译文 · 机器初译**

抑制剂在低风险骨髓增生异常综合征患者中的应用。Leuk Res 134, 107390

### co-scientist-0918

**English original**

(2023).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2023).

### co-scientist-0919

**English original**

14.​ Ramaswami, R. et al. A phase I/II study of abemaciclib, a CDK4/6 inhibitor, in participants

**中文译文 · 机器初译**

14.​ Ramaswami, R. 等。一项关于 CDK4/6 抑制剂阿贝美赛奇布在参与者中的 I/II 期研究

### co-scientist-0920

**English original**

with HIV-associated and HIV-negative Kaposi sarcoma. J. Clin. Oncol. 43, 11505–11505

**中文译文 · 机器初译**

涉及HIV相关及HIV阴性卡波西肉瘤的病例。J. Clin. Oncol. 43, 11505–11505

### co-scientist-0921

**English original**

(2025).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2025).

### co-scientist-0922

**English original**

15.​ Sebaugh, J. L. Guidelines for accurate EC50/IC50 estimation. Pharm Stat 10, 128–134

**中文译文 · 机器初译**

15.​ Sebaugh, J. L. 准确计算 EC50/IC50 值的指导原则. Pharm Stat 10, 128–134

### co-scientist-0923

**English original**

(2011).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2011).

### co-scientist-0924

**English original**

16.​ Kampen, K. R. et al. Insights in dynamic kinome reprogramming as a consequence of MEK

**中文译文 · 机器初译**

16.​ Kampen, K. R. 等. 由于 MEK 导致的动态基因组重编程的见解

### co-scientist-0925

**English original**

inhibition in MLL-rearranged AML. Leukemia 28, 589–599 (2014).

**中文译文 · 机器初译**

大语言模型重组型 AML 中的抑制现象。Leukemia 28, 589–599 (2014)。

### co-scientist-0926

**English original**

17.​ Scheidegger, N. et al. Combining menin and MEK inhibition to target poor prognostic

**中文译文 · 机器初译**

17.​ Scheidegger, N. 等。结合 menin 和 MEK 抑制以针对预后不良病例

### co-scientist-0927

**English original**

KMT2A-rearranged RAS pathway-mutant acute leukemia. Blood 142, 166 (2023).

**中文译文 · 机器初译**

KMT2A重排RAS通路突变型急性白血病。Blood 142, 166 (2023)。

### co-scientist-0928

**English original**

18.​ Shrader-Frechette, K. S. Ethics of Scientific Research. (Rowman & Littlefield Publishers,

**中文译文 · 机器初译**

18.​ Shrader-Frechette, K. S. 科学研究的伦理问题。（Rowman & Littlefield Publishers，

### co-scientist-0929

**English original**

1994).

**原文保留（专名、技术内容或文献信息） · 保留原文**

1994).

### co-scientist-0930

**English original**

19.​ Resnik, D. B. The Ethics of Science: An Introduction. (Routledge, 2005).

**中文译文 · 机器初译**

19.​ Resnik, D. B. 《科学的伦理：导论》。（Routledge，2005）。

### co-scientist-0931

**English original**

20.​ Rollin, B. E. Science and Ethics. (Cambridge University Press, 2006).

**中文译文 · 机器初译**

20.​ Rollin, B. E. 《科学与伦理》。（剑桥大学出版社，2006年）。

### co-scientist-0932

**English original**

21.​ Alasuutari, P., Bickman, L. & Brannen, J. The SAGE Handbook of Social Research

**中文译文 · 机器初译**

21.​ Alasuutari, P., Bickman, L. & Brannen, J. 《SAGE社会研究手册》

### co-scientist-0933

**English original**

Methods. (SAGE, 2008).

**中文译文 · 机器初译**

方法。（SAGE，2008）。


### 原文第 149 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=149)

### co-scientist-0935

**English original**

22.​ Menapace, M. Scientific Ethics: A New Approach. Sci Eng Ethics 25, 1193–1216 (2019).

**中文译文 · 机器初译**

22.​ Menapace, M. 科学伦理：一种新方法. 科学工程伦理 25, 1193–1216 (2019).

### co-scientist-0936

**English original**

23.​ Edel, A. Science and the Structure of Ethics. (Routledge, 2018).

**中文译文 · 机器初译**

23.​ Edel, A. 《科学与伦理结构》。（Routledge，2018）。

### co-scientist-0937

**English original**

24.​ Miller, S. & Selgelid, M. J. Ethical and philosophical consideration of the dual-use dilemma

**中文译文 · 机器初译**

24.​ Miller, S. & Selgelid, M. J. 大语言模型双重用途困境的伦理与哲学考量

### co-scientist-0938

**English original**

in the biological sciences. Sci Eng Ethics 13, 523–580 (2007).

**中文译文 · 机器初译**

在生物科学领域。《科学、工程与伦理》第 13 卷，第 523–580 页（2007 年）。

### co-scientist-0939

**English original**

25.​ Selgelid, M. J. Governance of dual-use research: an ethical dilemma. Bull World Health

**中文译文 · 机器初译**

25.​ Selgelid, M. J. 双重用途研究的治理：一个伦理困境。世界卫生组织公报

### co-scientist-0940

**English original**

Organ 87, 720–723 (2009).

**中文译文 · 机器初译**

Organ 87, 720–723 (2009)。

### co-scientist-0941

**English original**

26.​ Pustovit, S. V. & Williams, E. D. Philosophical aspects of dual use technologies. Sci Eng

**中文译文 · 机器初译**

26.​ Pustovit, S. V. & Williams, E. D. 双重用途技术的哲学层面。科学工程

### co-scientist-0942

**English original**

Ethics 16, 17–31 (2010).

**中文译文 · 机器初译**

《伦理学》第16卷，第17–31页（2010年）。

### co-scientist-0943

**English original**

27.​ Forge, J. A note on the definition of ‘dual use’. Sci Eng Ethics 16, 111–118 (2010).

**中文译文 · 机器初译**

27.​ Forge, J. 关于“双重用途”定义的一点说明。《科学、工程与伦理》16, 111–118 (2010)。

### co-scientist-0944

**English original**

28.​ Kuhlau, F., Höglund, A. T., Eriksson, S. & Evers, K. The ethics of disseminating dual-use

**中文译文 · 机器初译**

28.​ Kuhlau, F., Höglund, A. T., Eriksson, S. & Evers, K. 大用途技术传播的伦理问题

### co-scientist-0945

**English original**

knowledge. Research Ethics 9, 6–19 (2013).

**中文译文 · 机器初译**

知识。研究伦理 9, 6–19 (2013)。

### co-scientist-0946

**English original**

29.​ Shaw, S. & Barrett, G. Research governance: regulating risk and reducing harm? J R Soc

**中文译文 · 机器初译**

29.​ Shaw, S. & Barrett, G. 研究治理：如何规范风险并减少伤害？《皇家学会杂志》

### co-scientist-0947

**English original**

Med 99, 14–19 (2006).

**中文译文 · 机器初译**

Med 99, 14–19 (2006)。

### co-scientist-0948

**English original**

30.​ Rothstein, H., Irving, P., Walden, T. & Yearsley, R. The risks of risk-based regulation:

**中文译文 · 机器初译**

30.​ Rothstein, H., Irving, P., Walden, T. & Yearsley, R. 基于风险的监管风险：

### co-scientist-0949

**English original**

insights from the environmental policy domain. Environ Int 32, 1056–1065 (2006).

**中文译文 · 机器初译**

环境政策领域的见解。《环境科学》32, 1056–1065 (2006)。

### co-scientist-0950

**English original**

31.​ Ludlow, K., Bowman, D. M., Gatof, J. & Bennett, M. G. Regulating emerging and future

**中文译文 · 机器初译**

31.​ Ludlow, K., Bowman, D. M., Gatof, J. & Bennett, M. G. 对新兴及未来技术的监管

### co-scientist-0951

**English original**

technologies in the present. NanoEthics 9, 151–163 (2015).

**中文译文 · 机器初译**

当前的技术水平。NanoEthics 9, 151–163 (2015)。

### co-scientist-0952

**English original**

32.​ Verschraegen, G. Regulating scientific research: A constitutional moment? Journal of Law

**中文译文 · 机器初译**

32.​ Verschraegen, G. 规范科学研究：一个宪法层面的议题？法律杂志

### co-scientist-0953

**English original**

and Society 45, S163–S184 (2018).

**中文译文 · 机器初译**

《And Society》第45卷，第S163–S184页（2018年）。

### co-scientist-0954

**English original**

33.​ Jobin, A., Ienca, M. & Vayena, E. The global landscape of AI ethics guidelines. Nature

**中文译文 · 机器初译**

33.​ Jobin, A., Ienca, M. & Vayena, E. 人工智能伦理指南的全球现状。《自然》

### co-scientist-0955

**English original**

machine intelligence 1, 389–399 (2019).

**中文译文 · 机器初译**

机器智能 1, 389–399 (2019)。

### co-scientist-0956

**English original**

34.​ Wansley, M. T. Regulation of emerging risks. Vand. L. Rev. 69, 401 (2016).

**中文译文 · 机器初译**

34.​ Wansley, M. T. 新兴风险的管控. Vand. L. Rev. 69, 401 (2016).

### co-scientist-0957

**English original**

35.​ Gabriel, I. et al. The ethics of advanced AI assistants. arXiv preprint arXiv:2404.16244

**中文译文 · 机器初译**

35.​ Gabriel, I. 等. 高级人工智能助手的伦理问题. arXiv预印本 arXiv:2404.16244


### 原文第 150 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=150)

### co-scientist-0959

**English original**

(2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2024).

### co-scientist-0960

**English original**

36.​ Tang, X. et al. Prioritizing safeguarding over autonomy: Risks of LLM agents for science.

**中文译文 · 机器初译**

36.​ 唐X等. 优先保障安全而非自主权：大语言模型智能体在科学领域带来的风险。

### co-scientist-0961

**English original**

in ICLR 2024 Workshop on Large Language Model (LLM) Agents (2024).

**中文译文 · 机器初译**

2024年 ICLR 大语言模型（LLM）智能体研讨会（2024）。

### co-scientist-0962

**English original**

37.​ Shevlane, T. et al. Model evaluation for extreme risks. arXiv preprint arXiv:2305.15324

**中文译文 · 机器初译**

37.​ Shevlane, T. 等. 极端风险模型评估. arXiv预印本 arXiv:2305.15324

### co-scientist-0963

**English original**

(2023).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2023).

### co-scientist-0964

**English original**

38.​ Bova, P., Di Stefano, A. & Han, T. A. Quantifying detection rates for dangerous

**中文译文 · 机器初译**

38.​ Bova, P., Di Stefano, A. & Han, T. A. 量化危险检测率

### co-scientist-0965

**English original**

capabilities: a theoretical model of dangerous capability evaluations. arXiv preprint

**中文译文 · 机器初译**

能力：一种关于危险能力评估的理论模型。arXiv预印本

### co-scientist-0966

**English original**

arXiv:2412.15433 (2024).

**中文译文 · 机器初译**

arXiv:2412.15433 (2024)。

### co-scientist-0967

**English original**

39.​ Phuong, M. et al. Evaluating frontier models for dangerous capabilities. arXiv preprint

**中文译文 · 机器初译**

39.​ Phuong, M. 等. 对具有危险能力的前沿模型进行评估. arXiv 预印本

### co-scientist-0968

**English original**

arXiv:2403.13793 (2024).

**中文译文 · 机器初译**

arXiv:2403.13793 (2024)。

### co-scientist-0969

**English original**

40.​ Sabour, S. et al. Human decision-making is susceptible to AI-driven manipulation. arXiv

**中文译文 · 机器初译**

40.​ Sabour, S. 等。人类决策容易受到人工智能驱动的操纵。arXiv

### co-scientist-0970

**English original**

preprint arXiv:2502.07663 (2025).

**中文译文 · 机器初译**

arXiv预印本：2502.07663（2025年）。

### co-scientist-0971

**English original**

41.​ Ke, P. et al. CritiqueLLM: Towards an informative critique generation model for evaluation

**中文译文 · 机器初译**

41.​ Ke, P. 等. CritiqueLLM：一种用于评估的信息性批评生成模型

### co-scientist-0972

**English original**

of large language model generation. in Proceedings of the 62nd Annual Meeting of the

**中文译文 · 机器初译**

大语言模型生成技术。载于第62届年会论文集

### co-scientist-0973

**English original**

Association for Computational Linguistics (Volume 1: Long Papers) 13034–13054 (2024).

**中文译文 · 机器初译**

Association for Computational Linguistics (第1卷：长文论文集) 13034–13054 (2024)。

### co-scientist-0974

**English original**

42.​ Vu, T. et al. Foundational autoraters: Taming large language models for better automatic

**中文译文 · 机器初译**

42.​ Vu, T. 等。基础评估器：驯化大语言模型以实现更优自动化

### co-scientist-0975

**English original**

evaluation. arXiv preprint arXiv:2407.10817 (2024).

**中文译文 · 机器初译**

评估。arXiv预印本 arXiv:2407.10817 (2024)。

### co-scientist-0976

**English original**

43.​ Wei, H. et al. Systematic evaluation of LLM-as-a-judge in LLM alignment tasks:

**中文译文 · 机器初译**

43.​ 魏H.等。对大语言模型作为评判者在大语言模型对齐任务中的系统评估：

### co-scientist-0977

**English original**

Explainable metrics and diverse prompt templates. arXiv preprint arXiv:2408.13006 (2024).

**中文译文 · 机器初译**

可解释的评估指标与多样化的提示模板。arXiv预印本 arXiv:2408.13006 (2024)。

### co-scientist-0978

**English original**

44.​ Lan, T. et al. CriticEval: Evaluating large language model as critic. arXiv preprint

**中文译文 · 机器初译**

44.​ Lan, T. 等. CriticEval：作为评估器的大语言模型评价方法. arXiv 预印本

### co-scientist-0979

**English original**

arXiv:2402.13764 (2024).

**中文译文 · 机器初译**

arXiv:2402.13764 (2024)。

### co-scientist-0980

**English original**

45.​ Zheng, L. et al. Judging LLM-as-a-judge with mt-bench and chatbot arena. Advances in

**中文译文 · 机器初译**

45.​ 郑L等人使用mt-bench和chatbot arena对大语言模型作为评判者的表现进行评估。进展

### co-scientist-0981

**English original**

neural information processing systems 36, 46595–46623 (2023).

**中文译文 · 机器初译**

神经信息处理系统 36, 46595–46623 (2023)。


### 原文第 151 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=151)

### co-scientist-0983

**English original**

46.​ Li, D. et al. From generation to judgment: Opportunities and challenges of LLM-as-a-judge.

**中文译文 · 机器初译**

46.​ 李D等。从生成到判断：大语言模型作为评判者的机遇与挑战。

### co-scientist-0984

**English original**

in Proceedings of the 2025 Conference on Empirical Methods in Natural Language

**中文译文 · 机器初译**

载于《2025年自然语言实证方法会议论文集》

### co-scientist-0985

**English original**

Processing 2757–2791 (2025).

**中文译文 · 机器初译**

处理 2757–2791（2025年）。

### co-scientist-0986

**English original**

47.​ Gou, Z. et al. Critic: Large language models can self-correct with tool-interactive critiquing.

**中文译文 · 机器初译**

47.​ 郭Z等。批评者：大语言模型可通过工具交互式批评实现自我修正。

### co-scientist-0987

**English original**

arXiv preprint arXiv:2305.11738 (2023).

**中文译文 · 机器初译**

arXiv预印本 arXiv:2305.11738 (2023)。

### co-scientist-0988

**English original**

48.​ Chen, D. et al. MLLM-as-a-judge: Assessing multimodal LLM-as-a-judge with

**中文译文 · 机器初译**

48.​ 陈D等人。LLM作为评判者：使用多模态LLM作为评判者进行评估

### co-scientist-0989

**English original**

vision-language benchmark. in Forty-first International Conference on Machine Learning

**中文译文 · 机器初译**

视觉-语言基准测试。发表于《第四十一届国际机器学习会议》

### co-scientist-0990

**English original**

(2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2024).

### co-scientist-0991

**English original**

49.​ Szymanski, A. et al. Limitations of the LLM-as-a-judge approach for evaluating LLM

**中文译文 · 机器初译**

49.​ Szymanski, A. 等. 将大语言模型作为评判者用于评估大语言模型的局限性

### co-scientist-0992

**English original**

outputs in expert knowledge tasks. in Proceedings of the 30th International Conference on

**中文译文 · 机器初译**

专家知识任务中的输出结果。载于第30届国际会议论文集

### co-scientist-0993

**English original**

Intelligent User Interfaces 952–966 (2025).

**中文译文 · 机器初译**

智能用户界面 952–966（2025）。

### co-scientist-0994

**English original**

50.​ Shayegani, E. et al. Survey of vulnerabilities in large language models revealed by

**中文译文 · 机器初译**

50.​ Shayegani, E. 等. 大语言模型所暴露的漏洞调查

### co-scientist-0995

**English original**

adversarial attacks. arXiv preprint arXiv:2310.10844 (2023).

**中文译文 · 机器初译**

对抗性攻击。arXiv预印本 arXiv:2310.10844 (2023)。

### co-scientist-0996

**English original**

51.​ He, J. & Vechev, M. Large language models for code: Security hardening and adversarial

**中文译文 · 机器初译**

51.​ 何杰 & 维切夫，M. 用于代码的大语言模型：安全加固与对抗性测试

### co-scientist-0997

**English original**

testing. in Proceedings of the 2023 ACM SIGSAC Conference on Computer and

**中文译文 · 机器初译**

测试。载于《2023年ACM SIGSAC计算机会议论文集》

### co-scientist-0998

**English original**

Communications Security 1865–1879 (2023).

**中文译文 · 机器初译**

《通信安全》1865–1879卷（2023年）。

### co-scientist-0999

**English original**

52.​ Zhu, K. et al. PromptBench: Towards evaluating the robustness of large language models on

**中文译文 · 机器初译**

52.​ 朱K等。PromptBench：用于评估大语言模型鲁棒性的方法

### co-scientist-1000

**English original**

adversarial prompts. Proceedings of the 1st ACM workshop on large AI systems and models

**中文译文 · 机器初译**

对抗性提示。第1届ACM大人工智能系统与模型研讨会论文集

### co-scientist-1001

**English original**

with privacy and safety analysis (2023).

**中文译文 · 机器初译**

包含隐私与安全分析（2023年）。

### co-scientist-1002

**English original**

53.​ Fu, X. et al. Misusing tools in large language models with visual adversarial examples.

**中文译文 · 机器初译**

53.​ 傅X等。使用视觉对抗样本滥用大语言模型中的工具。

### co-scientist-1003

**English original**

arXiv preprint arXiv:2310.03185 (2023).

**中文译文 · 机器初译**

arXiv预印本 arXiv:2310.03185 (2023)。

### co-scientist-1004

**English original**

54.​ Zhang, Z. et al. Defending large language models against jailbreaking attacks through goal

**中文译文 · 机器初译**

54.​ 张Z等。通过目标机制防御大语言模型的反破解攻击

### co-scientist-1005

**English original**

prioritization. in Proceedings of the 62nd Annual Meeting of the Association for

**中文译文 · 机器初译**

优先级排序。载于第62届协会年会论文集


### 原文第 152 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=152)

### co-scientist-1007

**English original**

Computational Linguistics (Volume 1: Long Papers) 8865–8887 (2024).

**中文译文 · 机器初译**

《计算语言学》（第1卷：长文）8865–8887（2024年）。

### co-scientist-1008

**English original**

55.​ Chao, P. et al. JailbreakBench: An open robustness benchmark for jailbreaking large

**中文译文 · 机器初译**

55.​ Chao, P. 等. JailbreakBench：用于大语言模型越狱的开放鲁棒性测试基准

### co-scientist-1009

**English original**

language models. Advances in Neural Information Processing Systems 37, 55005–55029

**中文译文 · 机器初译**

语言模型。神经信息处理系统会议论文集 37，55005–55029

### co-scientist-1010

**English original**

(2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2024).

### co-scientist-1011

**English original**

56.​ Zhao, Y. et al. On evaluating adversarial robustness of large vision-language models.

**中文译文 · 机器初译**

56.​ 赵Y等. 关于大视觉语言模型对抗鲁棒性的评估方法。

### co-scientist-1012

**English original**

Advances in Neural Information Processing Systems 36, 54111–54138 (2023).

**中文译文 · 机器初译**

《神经信息处理系统进展》第36卷，54111–54138页（2023年）。

### co-scientist-1013

**English original**

57.​ Ma, X. et al. Safety at scale: A comprehensive survey of large model safety. arXiv preprint

**中文译文 · 机器初译**

57.​ Ma, X. 等. 大规模应用中的安全性：大语言模型安全性的全面综述. arXiv预印本

### co-scientist-1014

**English original**

arXiv:2502.05206 (2025).

**中文译文 · 机器初译**

arXiv:2502.05206 (2025)。

### co-scientist-1015

**English original**

58.​ Zou, A. et al. Universal and transferable adversarial attacks on aligned language models.

**中文译文 · 机器初译**

58.​ Zou, A. 等. 针对对齐语言模型的通用且可迁移的对抗性攻击。

### co-scientist-1016

**English original**

arXiv preprint arXiv:2307.15043 (2023).

**中文译文 · 机器初译**

arXiv预印本 arXiv:2307.15043 (2023)。

### co-scientist-1017

**English original**

59.​ Lapid, R., Langberg, R. & Sipper, M. Open sesame! universal black-box jailbreaking of

**中文译文 · 机器初译**

59.​ Lapid, R., Langberg, R. & Sipper, M. 打开芝麻门！通用的黑盒破解方法

### co-scientist-1018

**English original**

large language models. Applied Sciences 14, 7150 (2024).

**中文译文 · 机器初译**

大语言模型。《应用科学》第14卷，第7150页（2024年）。

### co-scientist-1019

**English original**

60.​ Wang, J. et al. Adversarial demonstration attacks on large language models. arXiv preprint

**中文译文 · 机器初译**

60.​ 王J.等。针对大语言模型的对抗性演示攻击。arXiv预印本

### co-scientist-1020

**English original**

arXiv:2305.14950 (2023).

**中文译文 · 机器初译**

arXiv:2305.14950 (2023)。

### co-scientist-1021

**English original**

61.​ Zhou, X., Qiang, Y., Zade, S. Z., Khanduri, P. & Zhu, D. Hijacking large language models

**中文译文 · 机器初译**

61. 周X、强Y、扎德S.Z.、坎杜里P.与朱D. 劫持大语言模型

### co-scientist-1022

**English original**

via adversarial in-context learning. arXiv preprint arXiv:2311.09948 (2023).

**中文译文 · 机器初译**

通过对抗性上下文学习方法。arXiv预印本 arXiv:2311.09948 (2023)。

### co-scientist-1023

**English original**

62.​ Qi, X. et al. Visual adversarial examples jailbreak aligned large language models. in

**中文译文 · 机器初译**

62.​ Qi, X. 等. 视觉对抗样本破解大语言模型对齐方法. 发表于

### co-scientist-1024

**English original**

Proceedings of the AAAI conference on artificial intelligence vol. 38 21527–21536 (2024).

**中文译文 · 机器初译**

《人工智能会议论文集》第 38 卷，21527–21536 页（2024 年）。

### co-scientist-1025

**English original**

63.​ Chao, P. et al. Jailbreaking black box large language models in twenty queries. in 2025

**中文译文 · 机器初译**

63.​ Chao, P. 等。二十次查询中大语言模型的越狱方法。发表于2025年

### co-scientist-1026

**English original**

IEEE Conference on Secure and Trustworthy Machine Learning (SaTML) 23–42 (2025).

**中文译文 · 机器初译**

IEEE安全与可信机器学习会议 (SaTML) 23–42 (2025)。

### co-scientist-1027

**English original**

64.​ Wang, Z. et al. Foot in the door: Understanding large language model jailbreaking via

**中文译文 · 机器初译**

64.​ 王Z等人。循序渐进：通过研究大语言模型的破解方法来理解其绕过限制机制

### co-scientist-1028

**English original**

cognitive psychology. arXiv preprint arXiv:2402.15690 (2024).

**中文译文 · 机器初译**

认知心理学。arXiv预印本 arXiv:2402.15690 (2024)。

### co-scientist-1029

**English original**

65.​ Zhang, J. et al. Adversarial prompt tuning for vision-language models. in European

**中文译文 · 机器初译**

65.​ 张J.等。面向视觉语言模型的对抗性提示调优方法。发表于《欧洲》期刊


### 原文第 153 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=153)

### co-scientist-1031

**English original**

conference on computer vision 56–72 (Springer, 2024).

**中文译文 · 机器初译**

计算机视觉会议 56–72（Springer，2024）。

### co-scientist-1032

**English original**

66.​ Shneiderman, B. Bridging the gap between ethics and practice: guidelines for reliable, safe,

**中文译文 · 机器初译**

66.​ Shneiderman, B. 弥合伦理与实践之间的差距：可靠、安全的指导方针

### co-scientist-1033

**English original**

and trustworthy human-centered AI systems. ACM Transactions on Interactive Intelligent

**中文译文 · 机器初译**

以及可信赖的以人为中心的人工智能系统。ACM交互智能交易期刊

### co-scientist-1034

**English original**

Systems (TiiS) 10, 1–31 (2020).

**中文译文 · 机器初译**

《系统（TiiS）》第10卷，第1-31页（2020年）。

### co-scientist-1035

**English original**

67.​ Hubinger, E. Anthropic: Responsible Scaling Policy. SuperIntelligence-Robotics-Safety &

**中文译文 · 机器初译**

67.​ Hubinger, E. 《Anthropic：负责任的扩展政策》。SuperIntelligence-Robotics-Safety &

### co-scientist-1036

**English original**

Alignment 2, (2025).

**中文译文 · 机器初译**

对齐 2，(2025)。

### co-scientist-1037

**English original**

68.​ Wang, Y. et al. Large Language Model is Secretly a Protein Sequence Optimizer. arXiv

**中文译文 · 机器初译**

68.​ 王Y等人。大语言模型实际上是一种蛋白质序列优化器。arXiv

### co-scientist-1038

**English original**

preprint arXiv:2501.09274 (2025).

**中文译文 · 机器初译**

预印本 arXiv:2501.09274 (2025)。

### co-scientist-1039

**English original**

69.​ Jumper, J. et al. Highly accurate protein structure prediction with AlphaFold. Nature 596,

**中文译文 · 机器初译**

69.​ Jumper, J. 等。使用 AlphaFold 进行高度准确的蛋白质结构预测。《自然》596,

### co-scientist-1040

**English original**

583–589 (2021).

**原文保留（专名、技术内容或文献信息） · 保留原文**

583–589 (2021).

### co-scientist-1041

**English original**

70.​ Takahashi, K. et al. Induction of pluripotent stem cells from adult human fibroblasts by

**中文译文 · 机器初译**

70.​ 高桥 K. 等。通过成人人类成纤维细胞诱导出多能干细胞

### co-scientist-1042

**English original**

defined factors. Cell 131, 861–872 (2007).

**中文译文 · 机器初译**

定义因素。Cell 131, 861–872 (2007)。

### co-scientist-1043

**English original**

71.​ Lin, Z. et al. Language models of protein sequences at the scale of evolution enable

**中文译文 · 机器初译**

71.​ 林Z等人。基于进化尺度的蛋白质序列语言模型

### co-scientist-1044

**English original**

accurate structure prediction. BioRxiv 2022, 500902 (2022).

**中文译文 · 机器初译**

准确的结构预测。BioRxiv 2022, 500902 (2022)。

### co-scientist-1045

**English original**

72.​ Baek, M. et al. Accurate prediction of protein structures and interactions using a three-track

**中文译文 · 机器初译**

72.​ Baek, M. 等。利用三轨迹方法实现蛋白质结构与相互作用的精准预测

### co-scientist-1046

**English original**

neural network. Science 373, 871–876 (2021).

**中文译文 · 机器初译**

神经网络。《科学》373, 871–876 (2021)。

### co-scientist-1047

**English original**

73.​ Bommasani, R. et al. On the opportunities and risks of foundation models. arXiv preprint

**中文译文 · 机器初译**

73.​ Bommasani, R. 等. 关于基础模型的机会与风险. arXiv预印本

### co-scientist-1048

**English original**

arXiv:2108.07258.

**中文译文 · 机器初译**

arXiv:2108.07258。

### co-scientist-1049

**English original**

74.​ Erhan, D., Courville, A., Bengio, Y. & Vincent, P. Why does unsupervised pre-training help

**中文译文 · 机器初译**

74.​ Erhan, D., Courville, A., Bengio, Y. & Vincent, P. 为什么无监督预训练有帮助

### co-scientist-1050

**English original**

deep learning? in Proceedings of the thirteenth international conference on artificial

**中文译文 · 机器初译**

深度学习？载于第十三届国际人工智能会议论文集

### co-scientist-1051

**English original**

intelligence and statistics 201–208 (JMLR Workshop and Conference Proceedings, 2010).

**中文译文 · 机器初译**

《智能与统计》201–208页（JMLR研讨会与会议论文集，2010年）。

### co-scientist-1052

**English original**

75.​ Radford, A., Narasimhan, K., Salimans, T., Sutskever, I. & Others. Improving language

**中文译文 · 机器初译**

75.​ Radford, A., Narasimhan, K., Salimans, T., Sutskever, I. 等。改进语言模型

### co-scientist-1053

**English original**

understanding by generative pre-training. Available online:

**中文译文 · 机器初译**

通过生成式预训练来理解。在线可获取：


### 原文第 154 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=154)

### co-scientist-1055

**English original**

https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_p

**中文译文 · 机器初译**

https://cdn.openai.com/research-covers/language-unsupervised/language_understanding_p

### co-scientist-1056

**English original**

aper.pdf (2018). (accessed on 17 February 2025)

**中文译文 · 机器初译**

aper.pdf (2018). (于2025年2月17日访问)

### co-scientist-1057

**English original**

76.​ Team, G. et al. Gemini: a family of highly capable multimodal models. arXiv preprint

**中文译文 · 机器初译**

76.​ G.等团队。Gemini：一系列具有高度能力的多模态模型。arXiv预印本

### co-scientist-1058

**English original**

arXiv:2312. 11805 (2023).

**中文译文 · 机器初译**

arXiv:2312. 11805 (2023)。

### co-scientist-1059

**English original**

77.​ Achiam, J. et al. GPT-4 technical report. arXiv preprint arXiv:2303.08774 (2023).

**中文译文 · 机器初译**

77.​ Achiam, J. 等. GPT-4技术报告. arXiv预印本 arXiv:2303.08774 (2023).

### co-scientist-1060

**English original**

78.​ Chowdhery, A. et al. PaLM: Scaling language modeling with pathways. arXiv preprint

**中文译文 · 机器初译**

78.​ Chowdhery, A. 等. PaLM：通过路径技术扩展语言建模能力. arXiv预印本

### co-scientist-1061

**English original**

arXiv:2204.02311 (2022).

**中文译文 · 机器初译**

arXiv:2204.02311 (2022)。

### co-scientist-1062

**English original**

79.​ Anil, R. et al. PaLM 2 technical report. arXiv preprint arXiv:2305.10403 (2023).

**中文译文 · 机器初译**

79.​ Anil, R. 等. PaLM 2技术报告. arXiv预印本arXiv:2305.10403 (2023).

### co-scientist-1063

**English original**

80.​ Wei, J. et al. Chain-of-thought prompting elicits reasoning in large language models.

**中文译文 · 机器初译**

80.​ 魏杰等。基于“思维链”提示的方法能够激发大语言模型的推理能力。

### co-scientist-1064

**English original**

Advances in neural information processing systems 35, 24824–24837 (2022).

**中文译文 · 机器初译**

《神经信息处理系统进展》第 35 卷，第 24824–24837 页（2022年）。

### co-scientist-1065

**English original**

81.​ Kahneman, D. Thinking, Fast and Slow. (Farrar, Straus and Giroux, 2011).

**中文译文 · 机器初译**

81.​ 卡内曼, D. 《思考，快与慢》.(Farrar, Straus and Giroux, 2011).

### co-scientist-1066

**English original**

82.​ Silver, D. et al. Mastering the game of Go with deep neural networks and tree search.

**中文译文 · 机器初译**

82.​ Silver, D. 等。利用深度神经网络与树搜索掌握围棋。

### co-scientist-1067

**English original**

Nature 529, 484–489 (2016).

**中文译文 · 机器初译**

《自然》529, 484–489 (2016)。

### co-scientist-1068

**English original**

83.​ Brown, N. & Sandholm, T. Superhuman AI for multiplayer poker. Science 365, 885–890

**中文译文 · 机器初译**

83.​ Brown, N. & Sandholm, T. 用于多人扑克的大语言模型超人类人工智能。《科学》365卷，885–890页

### co-scientist-1069

**English original**

(2019).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2019).

### co-scientist-1070

**English original**

84.​ Yao, S. et al. Tree of thoughts: Deliberate problem solving with large language models.

**中文译文 · 机器初译**

84.​ 姚S.等。思维树：使用大语言模型进行有意识的问题解决。

### co-scientist-1071

**English original**

Advances in neural information processing systems 36, 11809–11822 (2023).

**中文译文 · 机器初译**

《神经信息处理系统进展》第36卷，第11809–11822页（2023年）。

### co-scientist-1072

**English original**

85.​ Zelikman, E., Wu, Y., Mu, J. & Goodman, N. Star: Bootstrapping reasoning with reasoning.

**中文译文 · 机器初译**

85.​ Zelikman, E., Wu, Y., Mu, J. & Goodman, N. Star：利用推理进行自举式推理。

### co-scientist-1073

**English original**

Advances in Neural Information Processing Systems 35, 15476–15488 (2022).

**中文译文 · 机器初译**

《神经信息处理系统进展》第 35 卷，第 15476–15488 页（2022年）。

### co-scientist-1074

**English original**

86.​ Chen, L. et al. Are more LLM calls all you need? towards the scaling properties of

**中文译文 · 机器初译**

86.​ 陈L.等。仅仅更多的大语言模型调用就够了吗？关于其扩展特性

### co-scientist-1075

**English original**

compound AI systems. Advances in Neural Information Processing Systems 37,

**中文译文 · 机器初译**

复合人工智能系统。神经信息处理系统 37 会议的进展

### co-scientist-1076

**English original**

45767–45790 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

45767–45790 (2024).

### co-scientist-1077

**English original**

87.​ Snell, C., Lee, J., Xu, K. & Kumar, A. Scaling LLM test-time compute optimally can be

**中文译文 · 机器初译**

87.​ Snell, C., Lee, J., Xu, K. & Kumar, A. 优化大语言模型测试时计算规模的方法


### 原文第 155 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=155)

### co-scientist-1079

**English original**

more effective than scaling model parameters. arXiv preprint arXiv:2408.03314 (2024).

**中文译文 · 机器初译**

比调整模型参数更有效。arXiv预印本 arXiv:2408.03314 (2024)。

### co-scientist-1080

**English original**

88.​ Brown, B, et al. Large language monkeys: Scaling inference compute with repeated

**中文译文 · 机器初译**

88.​ Brown, B, 等. 大语言模型：通过重复操作扩展推理计算能力

### co-scientist-1081

**English original**

sampling. arXiv preprint arXiv:2407.21787 (2024).

**中文译文 · 机器初译**

采样。arXiv预印本 arXiv:2407.21787 (2024)。

### co-scientist-1082

**English original**

89.​ Muennighoff, N. et al. s1: Simple test-time scaling. arXiv preprint arXiv:2501.19393

**中文译文 · 机器初译**

89.​ Muennighoff, N. 等 s1：简单的测试时扩展方法。arXiv预印本 arXiv:2501.19393

### co-scientist-1083

**English original**

(2025).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2025).

### co-scientist-1084

**English original**

90.​ Tu, T. et al. Towards conversational diagnostic artificial intelligence. Nature 642, 442–450

**中文译文 · 机器初译**

90.​ Tu, T. 等. 迈向对话式诊断人工智能. 自然 642, 442–450

### co-scientist-1085

**English original**

(2025).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2025).

### co-scientist-1086

**English original**

91.​ Guo, D. et al. Deepseek-R1: Incentivizing reasoning capability in LLM via reinforcement

**中文译文 · 机器初译**

91.​ 郭D等. Deepseek-R1：通过强化学习激励大语言模型的推理能力

### co-scientist-1087

**English original**

learning. arXiv preprint arXiv:2501.12948 (2025).

**中文译文 · 机器初译**

学习。arXiv预印本 arXiv:2501.12948 (2025)。

### co-scientist-1088

**English original**

92.​ Jumper, J. et al. Highly accurate protein structure prediction with AlphaFold. Nature 596,

**中文译文 · 机器初译**

92.​ Jumper, J. 等。使用 AlphaFold 进行高度准确的蛋白质结构预测。《自然》596

### co-scientist-1089

**English original**

583–589 (2021).

**原文保留（专名、技术内容或文献信息） · 保留原文**

583–589 (2021).

### co-scientist-1090

**English original**

93.​ Wong, F. et al. Discovery of a structural class of antibiotics with explainable deep learning.

**中文译文 · 机器初译**

93.​ Wong, F. 等。发现一类具有可解释深度学习的结构型抗生素。

### co-scientist-1091

**English original**

Nature 626, 177–185 (2024).

**中文译文 · 机器初译**

《自然》626, 177–185 (2024)。

### co-scientist-1092

**English original**

94.​ Zambaldi, V. et al. De novo design of high-affinity protein binders with AlphaProteo. arXiv

**中文译文 · 机器初译**

94.​ Zambaldi, V. 等使用 AlphaProteo 设计高亲和力蛋白质结合剂的新方法。arXiv

### co-scientist-1093

**English original**

preprint arXiv:2409.08022 (2024).

**中文译文 · 机器初译**

预印本 arXiv:2409.08022 (2024)。

### co-scientist-1094

**English original**

95.​ Merchant, A. et al. Scaling deep learning for materials discovery. Nature 624, 80–85

**中文译文 · 机器初译**

95.​ Merchant, A. 等. 用于材料发现的大语言模型扩展研究. 《自然》624, 80–85

### co-scientist-1095

**English original**

(2023).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2023).

### co-scientist-1096

**English original**

96.​ Lu, C. et al. The AI scientist: Towards fully automated open-ended scientific discovery.

**中文译文 · 机器初译**

96.​ Lu, C. 等. 人工智能科学家：迈向完全自动化的开放式科学发现。

### co-scientist-1097

**English original**

arXiv preprint arXiv:2408.06292 (2024).

**中文译文 · 机器初译**

arXiv预印本 arXiv:2408.06292 (2024)。

### co-scientist-1098

**English original**

97.​ Schmidgall, S. et al. Agent laboratory: Using LLM agents as research assistants. arXiv

**中文译文 · 机器初译**

97.​ Schmidgall, S. 等。智能体实验室：利用大语言模型智能体作为研究助手。arXiv

### co-scientist-1099

**English original**

preprint arXiv:2501.04227 (2025).

**中文译文 · 机器初译**

预印本 arXiv:2501.04227 (2025)。

### co-scientist-1100

**English original**

98.​ Liang, W. et al. Can large language models provide useful feedback on research papers? A

**中文译文 · 机器初译**

98.​ 梁W等。大语言模型能否为研究论文提供有用的反馈？A

### co-scientist-1101

**English original**

large-scale empirical analysis. NEJM AI 1, AIoa2400196 (2024).

**中文译文 · 机器初译**

大规模实证分析。NEJM AI 1, AIoa2400196 (2024)。


### 原文第 156 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=156)

### co-scientist-1103

**English original**

99.​ Skarlinski, M. D. et al. Language agents achieve superhuman synthesis of scientific

**中文译文 · 机器初译**

99.​ Skarlinski, M. D. 等。语言智能体能够实现超人的科学综合能力

### co-scientist-1104

**English original**

knowledge. arXiv preprint arXiv:2409.13740 (2024).

**中文译文 · 机器初译**

知识。arXiv预印本 arXiv:2409.13740 (2024)。

### co-scientist-1105

**English original**

100.​Zhou, Y. et al. Hypothesis generation with large language models. Proceedings of the 1st

**中文译文 · 机器初译**

100.​周Y.等. 大语言模型的假设生成。第一届会议论文集

### co-scientist-1106

**English original**

Workshop on NLP for Science (NLP4Science) 117–139 (2024).

**中文译文 · 机器初译**

科学领域自然语言处理研讨会 (NLP4Science) 第 117–139 页 (2024)。

### co-scientist-1107

**English original**

101.​Ifargan, T., Hafner, L., Kern, M., Alcalay, O. & Kishony, R. Autonomous LLM-driven

**中文译文 · 机器初译**

101.​Ifargan, T., Hafner, L., Kern, M., Alcalay, O. & Kishony, R. 由大语言模型大语言模型驱动的自主系统

### co-scientist-1108

**English original**

research—from data to human-verifiable research papers. NEJM AI 2, AIoa2400555 (2025).

**中文译文 · 机器初译**

研究——从数据到人类可验证的研究论文。NEJM AI 2, AIoa2400555 (2025)。

### co-scientist-1109

**English original**

102.​Swanson, K., Wu, W., Bulaong, N. L., Pak, J. E. & Zou, J. The Virtual Lab: AI Agents

**中文译文 · 机器初译**

102.​Swanson, K., Wu, W., Bulaong, N. L., Pak, J. E. & Zou, J. 虚拟实验室：人工智能智能体

### co-scientist-1110

**English original**

Design New SARS-CoV-2 Nanobodies with Experimental Validation. bioRxiv

**中文译文 · 机器初译**

通过实验验证设计新的 SARS-CoV-2 纳米抗体。bioRxiv

### co-scientist-1111

**English original**

2024.11.11.623004 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

2024.11.11.623004 (2024).

### co-scientist-1112

**English original**

103.​Boiko, D. A., MacKnight, R., Kline, B. & Gomes, G. Autonomous chemical research with

**中文译文 · 机器初译**

103.​Boiko, D. A., MacKnight, R., Kline, B. & Gomes, G. 自主化学研究

### co-scientist-1113

**English original**

large language models. Nature 624, 570–578 (2023).

**中文译文 · 机器初译**

大语言模型。《自然》杂志 624, 570–578 (2023)。

### co-scientist-1114

**English original**

104.​Singhal, K. et al. Large language models encode clinical knowledge. Nature 620, 172–180

**中文译文 · 机器初译**

104.​Singhal, K. 等。大语言模型能够编码临床知识。《自然》620, 172–180

### co-scientist-1115

**English original**

(2023).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2023).

### co-scientist-1116

**English original**

105.​Saab, K. et al. Capabilities of Gemini models in medicine. arXiv preprint arXiv:2404.18416

**中文译文 · 机器初译**

105.​Saab, K. 等. Gemini模型在医学领域的应用能力. arXiv预印本 arXiv:2404.18416

### co-scientist-1117

**English original**

(2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

(2024).

### co-scientist-1118

**English original**

106.​Taylor, R. et al. Galactica: A large language model for science. arXiv preprint

**中文译文 · 机器初译**

106.​泰勒 R.等，《Galactica：一种用于科学的大语言模型》，arXiv预印本

### co-scientist-1119

**English original**

arXiv:2211.09085 (2022).

**中文译文 · 机器初译**

arXiv:2211.09085 (2022)。

### co-scientist-1120

**English original**

107.​Chaves, J. M. Z. et al. Tx-LLM: A large language model for therapeutics. arXiv preprint

**中文译文 · 机器初译**

107.​Chaves, J. M. Z. 等. Tx-LLM：一种用于治疗的大语言模型. arXiv预印本

### co-scientist-1121

**English original**

arXiv:2406.06316 (2024).

**中文译文 · 机器初译**

arXiv:2406.06316 (2024)。

### co-scientist-1122

**English original**

108.​Tu, T. et al. Genetic discovery enabled by a large language model. bioRxiv

**中文译文 · 机器初译**

108.​Tu, T. 等。大语言模型推动的遗传学发现。bioRxiv

### co-scientist-1123

**English original**

2023.11.09.566468 (2023).

**原文保留（专名、技术内容或文献信息） · 保留原文**

2023.11.09.566468 (2023).

### co-scientist-1124

**English original**

109.​Nguyen, E. et al. Sequence modeling and design from molecular to genome scale with Evo.

**中文译文 · 机器初译**

109.​Nguyen, E. 等使用 Evo 进行从分子到基因组规模的序列建模与设计研究。

### co-scientist-1125

**English original**

Science 386, eado9336 (2024).

**中文译文 · 机器初译**

《科学》386卷，eado9336（2024）。


### 原文第 157 页

[查看原页](../../../sources/fulltext/co-scientist/original.pdf#page=157)

### co-scientist-1127

**English original**

110.​Lin, Z. et al. Evolutionary-scale prediction of atomic-level protein structure with a language

**中文译文 · 机器初译**

110.​林Z等人利用大语言模型对原子级蛋白质结构进行进化尺度预测

### co-scientist-1128

**English original**

model. Science 379, 1123–1130 (2023).

**中文译文 · 机器初译**

模型。Science 379, 1123–1130 (2023)。

### co-scientist-1129

**English original**

111.​Ruffolo, J. A. et al. Design of highly functional genome editors by modeling the universe of

**中文译文 · 机器初译**

111.​Ruffolo, J. A. 等。通过建模基因组编辑器的全宇宙来设计高功能型基因组编辑器

### co-scientist-1130

**English original**

CRISPR-Cas sequences. bioRxiv 2024.04.22.590591 (2024).

**中文译文 · 机器初译**

CRISPR-Cas 序列。bioRxiv 2024.04.22.590591 (2024)。

### co-scientist-1131

**English original**

112.​Shaw, P. et al. ProtEx: a retrieval-augmented approach for protein function prediction.

**中文译文 · 机器初译**

112.​Shaw, P. 等. ProtEx：一种基于检索增强的蛋白质功能预测方法。

### co-scientist-1132

**English original**

bioRxiv 2024.05.30.596539 (2024).

**中文译文 · 机器初译**

bioRxiv 2024.05.30.596539 (2024)。

### co-scientist-1133

**English original**

113.​Pushpakom, S. et al. Drug repurposing: progress, challenges and recommendations. Nat Rev

**中文译文 · 机器初译**

113.​Pushpakom, S. 等. 药物重新应用：进展、挑战与建议. 自然综述

### co-scientist-1134

**English original**

Drug Discov 18, 41–58 (2019).

**中文译文 · 机器初译**

《药物发现》第18卷，第41–58页（2019年）。

### co-scientist-1135

**English original**

114.​Krishnamurthy, N., Grimshaw, A. A., Axson, S. A., Choe, S. H. & Miller, J. E. Drug

**中文译文 · 机器初译**

114.​Krishnamurthy, N., Grimshaw, A. A., Axson, S. A., Choe, S. H. & Miller, J. E. 药物

### co-scientist-1136

**English original**

repurposing: a systematic review on root causes, barriers and facilitators. BMC Health Serv

**中文译文 · 机器初译**

重新定位：关于根本原因、障碍与促进因素的系统性研究。BMC 健康服务

### co-scientist-1137

**English original**

Res 22, 970 (2022).

**中文译文 · 机器初译**

第22项，970分（2022年）。

### co-scientist-1138

**English original**

115.​Zitnik, M., Agrawal, M. & Leskovec, J. Modeling polypharmacy side effects with graph

**中文译文 · 机器初译**

115.​Zitnik, M., Agrawal, M. & Leskovec, J. 利用图结构对多药联合使用的副作用进行建模

### co-scientist-1139

**English original**

convolutional networks. Bioinformatics 34, i457–i466 (2018).

**中文译文 · 机器初译**

卷积网络。生物信息学 34, i457–i466 (2018)。

### co-scientist-1140

**English original**

116.​Morselli Gysi, D. et al. Network medicine framework for identifying drug-repurposing

**中文译文 · 机器初译**

116.​Morselli Gysi, D. 等。用于识别药物重新用途的网络医学框架

### co-scientist-1141

**English original**

opportunities for COVID-19. Proc Natl Acad Sci USA 118, (2021).

**中文译文 · 机器初译**

COVID-19的机遇。《美国国家科学院院刊》118, (2021)。

### co-scientist-1142

**English original**

117.​Huang, K. et al. A foundation model for clinician-centered drug repurposing. Nat Med 30,

**中文译文 · 机器初译**

117.​黄K等。一种以临床医生为中心的药物重新应用基础模型。《自然医学》30

### co-scientist-1143

**English original**

3601–3613 (2024).

**原文保留（专名、技术内容或文献信息） · 保留原文**

3601–3613 (2024).

