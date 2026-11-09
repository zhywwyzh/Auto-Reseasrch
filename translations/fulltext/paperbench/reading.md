# PaperBench：评价 AI 复现 AI 研究的能力

PaperBench: Evaluating AI's Ability to Replicate AI Research

Starace, Giulio; Jaffe, Oliver; Sherburn, Dane; Aung, James; Chan, Jun Shern; Maksin, Leon; Dias, Rachel; Mays, Evan; Kinsella, Benjamin; Thompson, Wyatt; Heidecke, Johannes; Glaese, Amelia; Patwardhan, Tejal

> 非官方机器初译，正文尚未逐段精校。图表保留原文内容，图内英文未另行翻译；有 HTML 原文的公式按原式排版。PDF 提取版保留对应原页，点击缩略图放大核对图表与公式。

原文版本：2504.01848v3 · [原始来源](https://arxiv.org/abs/2504.01848v3) · [中文 PDF](../../../output/pdf/paperbench-zh-reading.pdf)

## 摘要

我们提出 PaperBench，一个用于评价 AI 智能体复现先进 AI 研究能力的基准。智能体必须从零复现 20 篇 ICML 2024 Spotlight 和 Oral 论文，包括理解论文贡献、开发代码库以及成功执行实验。为了开展客观评价，我们建立评分标准，将每个复现任务按层级拆分为具有明确评分条件的较小子任务。PaperBench 共包含 8,316 个可单独评分的任务。评分标准与每篇 ICML 论文的作者共同制定，以确保准确性和真实性。为了实现可扩展评价，我们还开发了基于大语言模型的评分器，按评分标准自动评价复现尝试，并通过另建一个评分器基准来评估评分器表现。我们在 PaperBench 上评价了若干前沿模型。被测配置中表现最好的智能体是采用开源框架的 Claude 3.5 Sonnet（New），其平均复现得分为 21.0%。最后，我们招募优秀的机器学习博士研究者尝试 PaperBench 的一个子集，发现模型尚未超过人类基线。我们开放了代码，以促进后续对 AI 智能体研究工程能力的研究。

## 1 引言

[查看原图表（阅读版）](bilingual.html#paperbench-0018)

图1：PaperBench是一种用于评估人工智能智能体复现人工智能研究能力的基准测试。每个样本都包含一篇研究论文以及一份评分标准，其中明确规定了完整复现的评估准则。智能体从零开始创建代码库作为提交内容（1），随后执行该代码库以验证结果是否准确复现（2），并由基于大语言模型的评判者根据评分标准进行评分（3）。

我们介绍了 PaperBench 这一基准测试工具，用于评估智能体复现顶尖人工智能研究的能力。能够自主复现机器学习研究论文的智能体可加速机器学习的发展进程，这一前景令人兴奋，但也需进行深入研究，以确保人工智能能力能够安全发展。PaperBench 可作为 OpenAI 的 Preparedness 框架中模型自主性的衡量标准（OpenAI，2023），Anthropic 的 Responsible Scaling 政策中自主能力的衡量标准（Anthropic，2024），以及 Google DeepMind 的 Frontier Safety 框架中的机器学习研发衡量标准（Google DeepMind，2024）。

我们的实验设置涉及能够自主编写和执行代码的智能体。对于我们测试集中的每篇机器学习研究论文，我们向该智能体提供论文内容，要求其复现该论文的实证贡献。完整的复现工作包括理解论文内容、从零开始开发代码库以实现所有实验，以及根据需要进行实验的运行、监控和故障排查。总体而言，每个复现任务都具有很高的难度，至少需要人类专家数天的时间才能完成。

我们的基准测试包含来自2024年国际机器学习会议（ICML）的20篇Spotlight和Oral论文。这些论文涉及12个不同的ICML主题，包括深度强化学习、鲁棒性以及概率方法等。每篇论文都附带一份手工制定的评分标准，其中明确列出了详细复现该论文所需的所有成果；因此，20篇论文共包含8,316项可单独评分的成果。PaperBench中的每一项评分标准均由相关论文的原始作者之一共同制定，以确保其质量高且评估复现能力准确。
评分标准以层级化方式构建，从而可以将成果分解为细粒度的子成果，从而能够对复现论文的阶段性进展进行精准评估。

鉴于机器学习研究论文的复杂性，我们发现即使是对一次重复实验进行评分，也需要人类专家花费数十小时的时间。为了简化评分流程，我们尝试使用基于大语言模型的评分员，并引入一种辅助评估工具 JudgeEval，该工具将自动化评分员的输出与人类专家评分的金标数据集进行对比。我们最优秀的基于大语言模型的评分员使用了 o3-mini-high 及自定义框架，在辅助评估中获得了 0.83 的 F1 分数，这表明该评分员足以作为人类评分员的合理替代。

我们发现，这些智能体在复现机器学习研究论文方面展现出非平凡的能力。Anthropic 的 Claude 3.5 Sonnet（新版本）利用简单的智能体框架，在 PaperBench 测试上获得了 21.0% 的分数。在包含三篇论文的子样本中，我们由人类专家组成的机器学习博士基准组（共尝试三次）在 48 小时的努力后获得了 41.4% 的分数，而 o1 在同一子样本中的得分仅为 26.6%。我们还推出了名为 PaperBench Code-Dev 的 PaperBench 变体，用于更轻量级的评估。在该变体中，o1 获得了 43.4% 的分数。

我们的贡献包括：

•

PaperBench：一个包含20篇机器学习研究论文及作者认可的评分标准的基准平台，以及基于大语言模型的评判员实现的自动化评分流程。

•

PaperBench Code-Dev：该基准测试的轻量级变体，放宽了部分PaperBench的要求，使设置与评估过程更易于广大社区参与。

•

JudgeEval：一个由人类评分的提交样本构成的数据集，可作为辅助评估工具，用于开发与评估自动化评判器。

•

PaperBench上前沿模型的评估：对若干前沿AI智能体执行长期任务及机器学习研发能力的一次评估。

## 2 论文基准

在本节中，我们将描述 PaperBench 的整体流程。请参见图 1 以获取可视化概览。

### 2.1 任务

对于 PaperBench 中的每个样本，被评估的智能体（候选者）会获得该论文及对论文的补充说明文件。该候选者必须提交一份提交物，其中包含一个代码库，包含复现该论文实证结果所需的所有代码。该代码库必须在根目录下包含一个 reproduce.sh 文件，该文件作为执行所有必要代码以复现论文结果的入口点。如果 submit 物的 reproduce.sh 能够复现论文中报告的实证结果，则该提交物即视为成功复现了该论文。

我们的数据集包含评分标准，这些标准明确了每篇论文成功复现所需的具体成果（有关其用于评分的方式，请参见第2.3节；关于其整体设计，请参见第3.1节）。为了防止对评估标准产生过度拟合，在受试者尝试复现时不会展示评分标准，必须由受试者自行从论文中推断出需要复现的内容。

重要的是，我们禁止智能体使用或查看论文作者原始的代码库（如有）。这样就能确保我们评估的是智能体从零开始编写和执行复杂实验的能力，而非使用现有研究代码的能力，后者已在之前的研究中讨论过（Siegel等，2024）。

### 2.2 繁殖

只有当该结果通过在全新环境中运行提交内容得以重现时，才认为该提交已成功复现了该结果。为此，我们在评分之前设置了一个重现阶段。

当候选人的任务尝试结束时，我们会将其提交文件复现到一个运行着 Ubuntu 24.04 镜像且可访问 A10 GPU 的新虚拟机中。然后执行该提交的复现脚本，以干净的状态生成结果。在我们的实验中，我们将 reproduce.sh 的运行时间限制为 12 小时，这足以让所有脚本完成执行（我们发现由智能体生成的 reproduce.sh 脚本平均执行时间为 5.5 分钟）。未来使用 PaperBench 时可能需要更长的复现运行时间。此执行过程会生成复现过程中产生的所有文件（如结果和图表），同时还会产生一个 reproduce.log 文件作为附带产物。
我们将最终生成的更新提交文件夹称为“执行后的提交”。

通过将复现步骤与候选者的运行分离进行设计，我们提高了复现结果的可信度，并确保复现输出能够与候选者在任务执行时硬编码的任何结果区分开来。

### 2.3 评分标准

[查看原图表（阅读版）](bilingual.html#paperbench-0044)

图2：评分标准将复现任务按层级分解为一系列越来越细化的要求。叶节点根据二元通过/失败标准进行评分，而父节点的得分则是其子节点的加权平均值。在上述示例中，最终的复现得分为55%。

我们的基准测试中的每篇论文都附带一份评分标准，其中明确了完整论文复现的评估准则。

评分标准以需求树的形式组织，每个叶节点都明确规定了一个通过或失败的单一明确标准（见图2），且每个节点的权重都是根据其与兄弟节点的相对重要性手动确定的。我们将在3.1节中说明评分标准的设计原理。针对某个叶节点标准，评判者会评估提交内容是否符合该标准，若符合则赋予1分，否则赋予0分。

当所有叶节点都被评分后，父节点会获得与其子节点的分数加权平均值相等的得分。这一评分机制会一直向上传递至树的根节点，而根节点的得分则被作为该提交的最终复现得分。

换句话说，每个提交作品会根据所有评分标准要求的权重调整比例进行评分，其中 100% 表示完全符合所有叶节点要求。

我们的主要指标是所有论文的平均复现得分。

### 2.4 要求类型

每个叶节点具有三种可能的需求类型之一，这决定了其评分方式。

1.

结果匹配叶节点用于判断所提交的成果是否包含能够复现论文中特定结果的证据。结果匹配节点则通过查看 reproduce.sh 和 reproduce.log 文件，以及复现过程中创建或修改的任何文件来进行评分。2 2 2 一个示例结果匹配节点的要求为：“记录到的 F1 分数表明，从基于表示的预测方法中移除频率前项后，所有模型、数据集和微调设置的平均 F1 分数均会降低。”

2.

执行叶节点会判断在运行 reproduce.sh 脚本时是否出现了某个特定的执行结果。由于结果匹配节点很难实现，设置多个相关的执行节点可以使得提交内容获得积分，即使相应的结果匹配节点未能达成，也能被视为对结果的部分进展。执行节点的评估依据是 reproduce.sh、reproduce.log 以及源代码。
3 3 3 一个执行节点要求为：“已对表1中所有模型、数据集和微调配置下的无先验表示基于预测方法进行了代码执行，并记录了F1分数。”

3.

代码开发节点会评估候选人的源代码是否包含对某些要求的正确实现。代码开发节点为执行节点的完成提供部分分数；例如，某次提交可能编写了正确的代码，但在 reproduce.sh 中未能正确执行。4 4 4 一个代码开发节点的要求是：“已编写代码，用于使用 BART0 Large 在 P3 数据集的测试集上生成预测结果，并通过精确匹配得分对数据集进行评分，如第 4.1 节所述。”$D_{R}^{train}$ 和 $D_{R}^{test}$

如果仅使用结果匹配节点构成的评分标准也是可能的，因为匹配结果本质上就等同于论文表现。然而，我们加入了执行和代码开发节点，以赋予部分分数，从而确保智能体在 PaperBench 上的表现能够逐步提升。

相反，也可以设计一种仅包含代码开发节点的评分标准，因为所有必要代码的真正正确实现意味着当代码运行时能够正确执行并达到预期结果。然而，实际上无法在不运行代码的情况下完全确定其正确性。因此，从实际操作来看，最好同时单独评估代码是否执行以及结果是否符合要求，从而实现对提交内容的更全面、更可靠的评估。

我们在表1中总结了每种需求类型下哪些文件会被展示给评委。没有包含reproduce.sh脚本的提交在所有“执行”和“结果匹配”节点上的得分均为0。

[查看原图表（阅读版）](bilingual.html#paperbench-0061)

表1：叶节点可以是代码开发、执行或结果匹配，这决定了在对该叶节点进行评分时哪些文件会展示给评委。

### 2.5 规则

PaperBench 的设计是独立于智能体框架的，因此我们对智能体的环境没有特定要求。不过，该基准测试也有相关规则以确保公平比较：

1.

智能体可以浏览互联网，但不得使用我们提供的每篇论文黑名单中的网站资源。每篇论文的黑名单包括作者自己的代码仓库以及任何其他在线复现内容。

2.

智能体可使用的资源，如运行时间和计算能力，没有任何限制。不过，我们鼓励研究人员在结果中说明他们的设置情况。

3.

开发者应为智能体提供用于必要在线服务的 API 密钥（例如用于下载数据集的 HuggingFace 凭证）。获取在线账户访问权限并不属于我们通过 PaperBench 所评估的技能范围。

在我们的实验中，我们构建了一个简单的事后监控工具，用于检查智能体日志中是否存在被黑名单的 URL，随后我们将这些情况提交给人工审核，以排除任何使用被黑名单资源的提交内容。关于该监控工具的更多细节，请参见附录 E。我们在进行的 646 次实验中发现了 10 例使用被黑名单资源的情况，因此将这些提交内容得分设为 0 予以排除。

### 2.6 PaperBench 代码开发

在 PaperBench 上进行全面评估，不仅涉及智能体模型推理的计算成本较高，还需要为智能体提供相应的计算环境。为了提升可访问性，我们发布了简化版的 PaperBench，称之为 PaperBench Code-Dev。PaperBench Code-Dev 将评估任务简化为仅代码开发环节，不再强调执行代码以验证结果是否可复现。在评估过程中，我们省略了复现步骤，评判者仅根据评分标准对“代码开发”节点进行打分。

这免除了在 PaperBench 中运行智能体测试版本及复现步骤通常所需的昂贵 GPU 硬件需求。此外，以 o3-mini 作为评判者后，评分成本降低了约 85%。

PaperBench Code-Dev 提供了一种更易于使用的评估方式，但鲁棒性较低，用于衡量智能体的论文复现能力。我们发现，在 PaperBench Code-Dev 上的表现与在完整 PaperBench 评估中的表现相关性较弱。5 5 5 o1 该表现与 Pearson r 值为 0.48 相关，$\text{PB}=0.45\text{PBCD}+0.05$。我们预计 PaperBench Code-Dev 可以作为 PaperBench 上表现的初步、带有噪声的参考指标。

## 3 数据集

PaperBench包含20篇机器学习论文，这些论文列在表2中。为了确保该基准测试包含具有代表性的当代人工智能研究论文，我们纳入了2024年ICML会议中的所有Spotlight和Oral论文，并根据附录B中描述的标准进一步筛选以确认其适用性。我们还从2024年NeurIPS研讨会中选取了另外两篇论文作为开发集，并保留了一部分用于内部使用。

[查看原图表（阅读版）](bilingual.html#paperbench-0078)

表2：PaperBench中的论文列表（包含表7中的评分标准节点数量）。

### 3.1 评分标准

为每篇论文制定评分标准，是开发 PaperBench 过程中耗时最久的环节。每个评分标准都是与每篇论文的原始作者之一合作撰写的，从阅读论文、初步制定、评分标准审核、迭代修改到最终确认，每篇论文都需要数周时间。我们在附录 C 中详细介绍了评分标准制定过程。

每个评分标准都以树形结构呈现，按层级分解了复现某篇论文所需的主要成果。例如，根节点首先列出预期的最高级别成果，如“该论文的核心贡献已得到体现”。第一级分解可能会为每个核心贡献引入一个节点，而这些节点的子节点则会对具体成果进行更详细的说明，例如“gpt2-xl已在数据集上进行微调，使用了B.1节中的超参数”。
重要的是，一个节点所有子节点的满足情况表明其父节点也已被满足，因此只需对树的所有叶节点进行评分，即可全面评估整体效果。

叶节点具有精确且细致的要求。拥有大量细致的要求使我们能够对部分尝试进行评分，也便于评分者对单个节点进行评分。我们持续对节点进行分解，直到其所代表的要求足够细致，以至于我们认为一位专业人员可以在不到15分钟内审查该提交内容是否符合这些要求（假设对论文有了解）。在PaperBench的20篇论文中共有8,316个叶节点。表2显示了每个评分标准下的节点总数；关于节点类型的进一步细分，请参见附录C中的表7。

所有评分标准节点都带有权重；每个节点的权重反映了该贡献相对于其他贡献的重要性，并不一定与节点的实现难度相关。对节点进行加权处理，有助于在复现论文时优先处理更重要的部分。

### 3.2 处理规格不明确的问题

我们为每篇论文手动编写一份补充材料，其中包含原作者提供的说明。这些补充材料还明确了论文中哪些部分不在研究范围内。在必要时，我们还会制作一份仅供评审人员使用的补充材料，其中包含参考信息，以便更精准地评估投稿作品。

## 4 大语言模型评判员

在初步实验中，我们发现由专家人工进行评分需要数十小时才能完成一篇论文的评估，因此实现自动化的评估方式对于 PaperBench 的实际应用至关重要。

为了实现 PaperBench 参赛作品的大规模评估，我们开发了一个基于大语言模型的简单评判器（SimpleJudge）。随后，我们创建了辅助评估工具 JudgeEval，用于评估当前及未来评判者的表现。

重要的是，我们预计自动化评判者的质量会随着时间的推移而提升，从而我们所采用的基准测试中的评分可靠性也会随之改善。

### 4.1 SimpleJudge 实现方式

对于提交的论文，我们的评审员会根据评分标准独立对每个叶节点进行评分。针对某个特定的叶节点，评审员会收到论文的 Markdown 格式、完整的评分标准 JSON 文件、该叶节点的要求以及提交内容。

由于完整的提交内容通常过长，无法完全放入模型的上下文范围内，我们通过让评审员按相关性对文件进行排序，并仅将排名前十的文件纳入上下文来筛选代码库。随后，我们提示评审员评估叶节点的要求是否得到满足。

除非另有说明，我们采用 OpenAI 的 o3-mini 以及 6 6 6 o3-mini-2025-01-31，并将 reasoning_effort 设置为“高”，作为评判者的后端模型。我们估计使用 o3-mini 进行评判的成本约为每篇论文 $66 USD in OpenAI API credits 7 7 7 Based on public OpenAI o1 API pricing as of 2025/03/21. On average SimpleJudge uses around 50,000,000 input tokens and 2,000,000 output tokens per paper. to grade a single submission. For PaperBench Code-Dev, the cost drops to around $ 10 美元。我们的大语言模型评判器比雇佣专业人类评分员更便宜且更快（见图 5）。

我们将该判断器实现称为“SimpleJudge”。关于我们的实现细节，请参见附录 D。

### 4.2 使用 JudgeEval 对评审员进行评估

我们介绍了 JudgeEval，这是一个用于评估 PaperBench 环境中自动化裁判准确性的基准测试。

为了构建 JudgeEval，我们使用了 PaperBench 数据集中的四篇论文以及该数据集开发集中的一篇论文的部分复现版本。这些复现版本要么是从零开始创建的，要么是对原始作者代码库进行了修改后生成的。请注意，原始作者的代码库并不预期能获得满分；我们发现它们通常不完整或存在错误。此外，它们也不包含 PaperBench 提交要求中的 reproduce.sh 脚本。我们会根据对应的论文评分标准对每一份复现尝试进行人工评分，并将这些人工评分的叶节点作为自动评判器的真实标签。

由于对每个叶节点进行评分属于二元分类任务，我们使用标准的二元分类指标来评估 JudgeEval。

我们在 JudgeEval 上将 GPT-4o-mini、GPT-4o、o1-mini、o1 和 o3-mini 作为评判模型进行评估，通过宏观平均法汇总各论文的性能。表3中的结果表明，采用 SimpleJudge 框架的 o3-mini 最具成本效益，每篇论文的 F1分数达到0.83，成本为66美元。这就是我们用于主结果的评判方式。

[查看原图表（阅读版）](bilingual.html#paperbench-0101)

表3：在JudgeEval评估框架下，GPT-4o、o1-mini、o1和o3-mini的大多数平均指标。o系列模型使用推理努力度作为评分标准。我们同时提供了每篇论文的平均成本（以美元计）。附录G中按需求类型分列了F1分数。

## 5 实验与结果

### 5.1 智能体与执行环境

在我们的实验中，我们将每个智能体运行在能够访问单个 A10 GPU的 Ubuntu 24.04 Docker 容器中。该智能体的本地工作目录中包含 PDF 和 Markdown 格式的论文、论文的补充材料，以及一份包含操作说明的文本文件（具体说明请参见图 13）。

该容器可以访问互联网，因此智能体可以根据需要下载软件包并浏览网页。我们为智能体提供了 HuggingFace 和 OpenAI API 的 API 密钥，并预置了 1000 美元的资金，以便其在运行过程中能够使用这些服务（例如，如果某篇论文涉及使用 OpenAI 微调 API 进行实验）。

我们基于 Inspect AI 的基础智能体构建了一个简单的智能体框架，将其称为 BasicAgent，并使用 nanoeval 进行调度。该框架会持续运行工具使用循环，直到模型选择终止运行或达到时间限制为止。我们为智能体提供了 bash shell 命令执行工具、Python 代码执行工具、网络浏览器工具以及用于读取长文档的分页文件阅读工具。关于智能体框架的更多细节，请参见附录 F。

### 5.2 主要实验

我们对 GPT-4o、10 10 10 gpt-4o-2024-08-06 o1、11 11 11 o1-2024-12-17 以及带有 high 推理级别的 o3-mini、12 12 12 o3-mini-2025-01-31 带有 high 推理级别的 DeepSeek-R1、13 13 13 https://openrouter.ai/deepseek-ai/DeepSeek-R1 Claude 3.5 Sonnet (New)、14 14 14 claude-3-5-sonnet-20241022 和 Gemini 2.0 Flash 在每篇论文进行 3 次运行的所有 20 篇论文进行了评估。我们原本也想对 Claude 3.7 Sonnet 进行评估，但由于 Anthropic API 的速率限制，无法完成实验。我们为智能体设定了最多 $12$ 小时的运行时间。16 16 16 我们出于实际原因设置了这一限制。我们鼓励提交者报告其智能体的运行时间。

各模型的平均复现得分请参见表4。我们观察到 Claude 3.5 Sonnet 表现良好，得分为21.0%。OpenAI o1的得分则较弱，为13.2%。其他测试模型的表现较差，得分均低于10%。

我们手动检查了几个智能体的日志，以便更清楚地了解其表现。我们发现，除了 Claude 3.5 Sonnet 之外，所有模型都经常提前结束工作，声称它们要么已经完成了整个复现过程，要么遇到了无法解决的问题。由于可用时间有限，所有智能体都未能制定出最佳复现论文的策略。我们还发现 o3-mini 在工具使用方面经常遇到困难。

这些故障模式表明，当前的大语言模型在执行长期任务方面存在不足；尽管这些模型在制定和撰写多步骤计划方面表现出色，却无法真正执行该计划的系列操作。

我们认为，对智能体框架的进一步研究将在 PaperBench 测试上带来更好的结果。在我们的研究中，我们主要致力于引入 PaperBench 基准测试，并仅将其作为初始基线来展示我们的智能体在该基准测试中的表现。我们并不认为当前的结果就代表了这些模型能力的上限。

[查看原图表（阅读版）](bilingual.html#paperbench-0114)

表4：采用我们的主要设置BasicAgent的模型的平均复现得分（以百分比表示）。误差为平均值的标准误差。

[查看原图表（阅读版）](bilingual.html#paperbench-0116)

表5：使用迭代智能体时的平均复现得分（百分比）。迭代智能体破坏了模型提前结束任务的能力，并促使模型以逐步的方式工作。我们观察到，与基础智能体相比，这些修改显著提升了 o3-mini 和 o1 的得分，但却对 Claude 3.5 Sonnet 产生了负面影响，这凸显了模型对提示方式的敏感性。

[查看原图表（阅读版）](bilingual.html#paperbench-0118)

表6：使用迭代智能体在 PaperBench Code-Dev 平台上对 o1 进行重复实验的平均得分（%）。误差为均值的标准误差。

[查看原图表（阅读版）](bilingual.html#paperbench-0120)

图3：在PaperBench的4篇论文子集上对比人类智能体与智能体表现。o1初始表现优于人类基准值，但在第一小时后便趋于平稳，最终落后于人类。需要注意的是，人类在测试时模型适应方面的尝试在24小时时结束，因此被排除在本文其他部分所讨论的“3篇论文子集”之外。模型表现的误差范围是基于3次重复实验的SEM值。

### 5.3 迭代智能体

由于模型往往无法充分利用可用时间，我们测试了 BasicAgent 的一个变体，该变体通过禁止智能体提前结束任务来强制其使用全部可用时间，并使用经过调整的提示词以促使模型以逐步的方式工作。我们将这种智能体称为 IterativeAgent。关于所使用的提示词的详细内容，请参见附录 F.2。

我们使用 IterativeAgent 对 o1、o3-mini 和 Claude 3.5 Sonnet 进行了测试。结果见表5。

我们看到使用迭代智能体时，o1和o3-mini的得分有了显著提升。我们注意到 Claude 3.5 Sonnet 使用基础智能体时的表现优于 o1，但在使用迭代智能体时则不如 o1。这表明用于迭代智能体的提示调整对 OpenAI o系列模型具有不同的适配性。我们推测，对基础智能体进行修改并防止其提前结束任务的操作，可能使 Claude 3.5 Sonnet 在使用迭代智能体时超越 o1。

### 5.4 人类基准性能

我们招募了8名当前正在攻读或已完成机器学习博士学位的参与者。这些参与者均来自伯克利、剑桥、卡内基梅隆大学、哥伦比亚大学、康奈尔大学、普渡大学、维也纳技术大学或马萨诸塞大学阿默斯特分校。每位参与者的招聘流程包括简历筛选，随后进行机器学习和Git技术测试，以建立人类基准。

我们的设置旨在对4篇论文中的一部分建立人类基准：每篇论文我们收集3次独立的重复实验，并将参与者分配至他们最确信能够复现的论文。每篇论文的3次独立尝试使我们能够追踪最佳@3尝试结果，并将其作为“专家”得分使用。

我们在与我们的智能体相似的条件下对参与者进行评估。我们向参与者提供 PDF 和 Markdown 格式的论文，以及论文的补充材料与说明，这些内容与用于智能体的说明尽可能一致。18 18 18 针对人类基线组的说明中包含了关于工作期望以及如何使用 GPU 设置虚拟机的额外细节。参与者可以使用一台 NVIDIA A10 GPU。19 19 19 由于 A10 无法获取，在四次基线测试中，我们改用了一台 NVIDIA A100 GPU。
这或许能让人类的工作流程稍快一些，但请注意，对于所有人类和人工智能的提交作品，我们在复现步骤中仍使用 A10模型，因此我们预计得分提升效果并不显著。我们不对参与者的工作方式设置限制——例如，他们可以自由使用 ChatGPT 和 GitHub Copilot 等人工智能助手——只是他们不得查阅论文黑名单中的任何网站（依据 PaperBench 规则）。

参与者以兼职形式参与，有四周的时间窗口以尽可能取得进展。在一周的进度完成后对尝试结果进行评估，仅将其中表现最好的一个智能体保留下来，用于后续四周的工作。活跃工作时间通过工时表进行记录；如果参与者的机器在无人值守的情况下运行实验（例如夜间），该时间也计入总工作小时数。我们利用这些记录的时间来获取不同时间戳下的提交快照并进行评分。

我们使用迭代智能体对 o1 进行了长达 36 小时的扩展运行，保存了每小时的快照，并在 1、3、6、12 和 36 小时时对这些快照进行评分。

我们在图3中对比了这种扩展至36小时的o1与人类表现随时间的变化情况。我们观察到，在复现尝试的初期阶段，o1的表现优于人类基线水平；但24小时后，人类开始超过智能体。智能体最初优于人类但在更长时间范围内则落后的趋势，与Wijk等人（2024年）之前的研究结果一致。值得注意的是，o1的分数在第一个小时后基本趋于稳定，这表明该模型在尝试初期能够快速编写大量代码，但在此时间范围之后便无法有效制定改进提交内容的策略。
在最初几个小时内，人类的评分提升速度较慢，可能是因为人们需要时间消化这篇论文。

## 6 相关研究

在本节中，我们综述了在机器学习研究与工程领域用于评估人工智能智能体的相关工作。关于基于评分标准的评估与其他评估方式及监管手段的对比分析，请参见附录 A。

### 评估机器学习工程与研究工作

CORE-Bench（Siegel等，2024年）任务要求智能体根据研究论文的存储库复现其结果；而PaperBench任务则要求智能体从零开始复现研究论文的结果。

MLE-bench（Chan等人，2024年）、MLAgentBench（Huang等人，2024年）和DSBench（Jing等人，2024年）都在Kaggle竞赛中对智能体进行评估。许多Kaggle竞赛属于较老且相对简单的机器学习挑战，而PaperBench则仅包含与现代机器学习研究相关的任务。

RE-Bench（Wijk等人，2024年）提出了7项具有挑战性的开放式机器学习研究工程任务供智能体解决。与RE-Bench中提出的较为独立的任务相比，我们认为PaperBench将在更长的研究周期内涵盖更多种类的子任务。此外，RE-Bench为大多数任务提供了“评分函数”，以便对智能体在当前任务中的表现进行精准评估；而在PaperBench中，我们希望衡量智能体执行并整合广泛机器学习研究工作的能力，因为此类评分函数无法有效覆盖所有任务内容。

近期研究表明，在大语言模型特定领域中，它们能够生成与人类博士级研究者相当的新颖研究思路（Si等人，2024），并解决一些简单的研究问题，这些问题涉及提出假设、设计与执行实验以及分析结果（Jansen等人，2024；Wang等人，2022）。

### 自动评判

先前提出使用大语言模型作为评判者，以评估特定任务的提交作品（Zheng等人，2023；Chen等人，2024；Fu等人，2023）。研究发现，基于智能体的评判者在某些任务上比非智能体大语言模型评判者更为准确（Zhuge等人，2024）。我们针对比以往更难的任务对模型的评判能力进行了测试。

## 7 局限性

### 数据集大小

PaperBench目前仅包含20篇论文，理想情况下应涵盖更多机器学习研究领域的成果。然而，仅关注论文数量可能会产生误导：由于每个评分标准由数百个节点组成，PaperBench会对数千项不同的具体要求对智能体进行评估。

### 污染

对于我们的基准测试中的几乎所有论文，原始作者提供的代码库都可在网上找到。根据我们的经验，这些代码库通常无法完整复现整篇论文，也不符合 PaperBench 提交所需的特定格式要求（例如，应存在 reproduce.sh 脚本以执行代码）。不过，在大型语料上预训练的模型可能已内化了某些解决方案，从而导致在该基准测试中的性能表现虚高。虽然当前模型由于数据集中的论文发布时间较近，很可能不会受到此问题的影响，但这对未来的模型可能会成为一个问题。

### 具有挑战性的数据集创建

制定这些详细的评分标准需要大量的劳动投入，每个评分标准的制定都需要专家人类人员花费数整天的时间。制定者必须深刻理解论文内容，且每个评分标准都必须仔细编写，以避免出现不准确的要求，从而确保评估的准确性。我们发现很难训练他人以达到我们期望的质量水平来制定评分标准，这也为其他人复现我们创建数据集的过程带来了挑战。未来的研究或许可以探索更高效的评分标准生成方法，例如借助模型辅助。

### 基于大语言模型的裁判表现

尽管我们的评判器在 JudgeEval 测试中的表现良好，但其准确性仍不如专业人类评判者。此外，由于使用了非确定性模型调用，该评判器不具备确定性。我们期待看到在复杂任务自动化评判方面取得更多进展，也期待未来通过对抗性样本等方式对评判器进行压力测试。关于复杂任务评估及未来所需发展的更详细讨论，请参见附录 A。

### 成本

我们估计，平均而言，每次评估运行的成本约为 $400 in API credits to run an o1 IterativeAgent 12-hour rollout on a single paper in PaperBench. For the 20 papers, this sums to $ 8000 美元。评分相关的费用额外为每次评估运行 $66 USD per paper on average with o3-mini SimpleJudge. We purposely designed PaperBench Code-Dev (PBCD) not only to eliminate the GPU requirement, but also to address the issue of cost. We expect that PBCD rollouts can be made to run for half the duration of PaperBench roll-outs, due to the lack of execution, which would lead to a cost of $ 4000 美元。所观察到的停滞现象表明，部署周期可能会进一步缩短，从而进一步降低成本。
我们还发现，对于 PBCD 项目而言，每份论文的平均评分成本降至 10 美元。最后，我们发布了 SimpleJudge 的实验版本，初步结果显示评分成本降低了 10 倍（见附录 H）。

## 8 结论

我们将 PaperBench 作为一项具有挑战性的评估基准，用于衡量人工智能智能体复现前沿机器学习研究的能力。每篇被纳入的论文都代表了相关领域中的前沿成果——例如强化学习、鲁棒性以及概率方法等——并根据与原始作者共同制定的严格评分标准进行评估。通过要求人工智能智能体从零开始构建完整的代码库、开展复杂的实验并生成最终结果，PaperBench 提供了对机器学习研发能力进行严格现实场景测试的考核方式。

我们对多种前沿模型的实验表明，虽然当前人工智能系统具备复现某些机器学习论文内容的能力，但距离完全胜任成功复现所需的全部任务仍相差甚远。我们在主要实验设置中表现最出色的智能体——Claude 3.5 Sonnet (New)——的平均复现得分仅为 21.0%，这凸显了机器学习研究任务的复杂性，也反映了当前人工智能智能体在执行复杂长期任务方面的局限性。
然而，这些早期成果凸显了非简单的进展：人工智能智能体能够成功实施并验证各种方法，这预示着未来会有进一步的改进。

通过开源 PaperBench，我们旨在为评估、监控和预测人工智能系统的能力提供支持，从而推动人工智能自身的研发工作。虽然我们的基准测试无法涵盖现实研究中所有方面，但我们认为这标志着在机器学习研究中对人工智能自主性进行严格评估的重要一步。

### 影响陈述

随着人工智能系统逐渐能够自主开展复杂的机器学习研究，它们在多个领域加速科学发现方面具有巨大潜力。一个相关的例子是，由人工智能驱动的机器学习研究可以显著加快人工智能安全与对齐研究的进展。能够从头开始复现先进的机器学习研究，体现了人工智能系统的自主性和机器学习能力，这表明在 PaperBench 测试中表现优异的模型具备处理现实世界中开放式机器学习研究任务的非平凡能力。

然而，自主复现和拓展前沿研究的能力也可能带来快速创新，这种创新的速度远远超出了我们全面理解其影响的能力。如果强大的模型不仅能复现最先进的技术，还能不断迭代优化这些技术，它们可能会以更高的风险程度加速日益强大的系统的开发进程。我们可能会看到一些模型在几乎没有时间进行充分的风险评估、治理措施或安全与对齐干预的情况下就被推出，从而可能导致危险或破坏稳定的结果。

通过开源 PaperBench，我们旨在提供一种方法，用于衡量前沿人工智能系统这些新兴的自主研发能力。我们认识到，PaperBench只是更广泛的自主人工智能研发评估体系中的一部分。我们鼓励未来研究关注并准备应对具有更强自主性的人工智能系统可能最终带来的巨大影响。

### 致谢

我们衷心感谢 Arvind Ramaswami 和 Francisco Garcia 对构建 PaperBench 数据集所做出的贡献。

我们也想感谢《PaperBench》中收录的论文作者们，他们与我们紧密合作，共同完善各项评分标准：Alexander Spangher、Ananye Agarwal、Andrew Lee、Bartłomiej Cupiał、Bowen Zhao、Chang Xu、Christian Schlarmann、Diana Cai、Dong Gong、Feng Liu、Haotian Sun、Jia Shi、Kevin Frans、Louis Sharrock、Manuel Gloeckler、Michael Samuel Albergo、Pratik Rathore、Shuaicheng Niu、Tim Knappe、Tongliang Liu、Xinyu Xing 和 Xisen Jin。他们愿意阐明研究方法、分享额外材料并支持评分标准制定过程，对于打造全面且准确的评分标准至关重要。

我们也对参与人类基线实验的Amy Lu、Anit Kumar Sahu、Armin Wasicek、Brendan Rappazzo、Chun-Wei Chiang、David Khachaturov、Marc Harary和Stephen Giguere表示感谢。

最后，我们要感谢 Aparna Dutta、Jerry Tworek、Phoebe Thacker、Phillip Guo、Kevin Liu、Vichyr Pong、Mengyuan Yan 和 Yining Chen 提供的建议与合作。

## 参考文献

Albergo et al. (2024) Albergo, M. S., Goldstein, M., Boffi, N. M., Ranganath, R., and Vanden-Eijnden, E. Stochastic Interpolants with Data-Dependent Couplings. June 2024. URL https://openreview.net/forum?id=FFILRGD0jG .

Anthropic (2024) Anthropic. Responsible Scaling Policy. https://www.anthropic.com/news/announcing-our-updated-responsible-scaling-policy , 2024. Accessed: 2025-01-29.

Cai et al. (2024a) Cai, C., Ye, Z., Feng, L., Qi, J., and Liu, F. Sample-specific Masks for Visual Reprogramming-based Prompting. June 2024a. URL https://openreview.net/forum?id=4sikyurTLX .

Cai et al. (2024b) Cai, D., Modi, C., Pillaud-Vivien, L., Margossian, C., Gower, R. M., Blei, D., and Saul, L. K. Batch and match: black-box variational inference with a score-based divergence. June 2024b. URL https://openreview.net/forum?id=bplNmU2ROC .

Chan et al. (2024) Chan, J. S., Chowdhury, N., Jaffe, O., Aung, J., Sherburn, D., Mays, E., Starace, G., Liu, K., Maksin, L., Patwardhan, T., et al. MLE-bench: Evaluating machine learning agents on machine learning engineering. arXiv preprint arXiv:2410.07095 , 2024.

Chen et al. (2024) Chen, D., Chen, R., Zhang, S., Liu, Y., Wang, Y., Zhou, H., Zhang, Q., Wan, Y., Zhou, P., and Sun, L. MLLM-as-a-Judge: Assessing Multimodal LLM-as-a-Judge with Vision-Language Benchmark. arXiv preprint arXiv:2402.04788 , 2024.

(7) Cheng, Z., Wu, X., Yu, J., Yang, S., Wang, G., and Xing, X. RICE: Breaking Through the Training Bottlenecks of Reinforcement Learning with Explanation.

Chiang & yi Lee (2023) Chiang, C.-H. and yi Lee, H. Can Large Language Models Be an Alternative to Human Evaluations?, 2023. URL https://arxiv.org/abs/2305.01937 .

DeepMind (2024) DeepMind. Specification Gaming: The Flip Side of AI Ingenuity, 2024. URL https://deepmind.google/discover/blog/specification-gaming-the-flip-side-of-ai-ingenuity/ . Accessed: 10 March 2025.

Frans et al. (2024) Frans, K., Park, S., Abbeel, P., and Levine, S. Unsupervised Zero-Shot Reinforcement Learning via Functional Reward Encodings. June 2024. URL https://openreview.net/forum?id=a6wCNfIj8E .

Fu et al. (2023) Fu, J., Ng, S.-K., Jiang, Z., and Liu, P. GPTScore: Evaluate as You Desire. arXiv preprint arXiv:2302.04166 , 2023.

Gloeckler et al. (2024) Gloeckler, M., Deistler, M., Weilbach, C. D., Wood, F., and Macke, J. H. All-in-one simulation-based inference. June 2024. URL https://openreview.net/forum?id=DL79HYCFFq .

Google DeepMind (2024) Google DeepMind. Frontier Safety Framework, May 2024.

Harvey Team (2024) Harvey Team. Introducing BigLaw Bench, August 2024. URL https://www.harvey.ai/blog/introducing-biglaw-bench .

Huang et al. (2024) Huang, Q., Vora, J., Liang, P., and Leskovec, J. MLAgentBench: Evaluating Language Agents on Machine Learning Experimentation. In Forty-first International Conference on Machine Learning , 2024.

Jansen et al. (2024) Jansen, P., Côté, M.-A., Khot, T., Bransom, E., Mishra, B. D., Majumder, B. P., Tafjord, O., and Clark, P. DISCOVERYWORLD: A Virtual Environment for Developing and Evaluating Automated Scientific Discovery Agents. arXiv preprint arXiv:2406.06769 , 2024.

Jin & Ren (2024) Jin, X. and Ren, X. What Will My Model Forget? Forecasting Forgotten Examples in Language Model Refinement. June 2024. URL https://openreview.net/forum?id=bzNwexOPWm .

Jing et al. (2024) Jing, L., Huang, Z., Wang, X., Yao, W., Yu, W., Ma, K., Zhang, H., Du, X., and Yu, D. DSBench: How Far Are Data Science Agents to Becoming Data Science Experts? arXiv preprint arXiv:2409.07703 , 2024.

Lambert et al. (2024) Lambert, N., Pyatkin, V., Morrison, J., Miranda, L., Lin, B. Y., Chandu, K., Dziri, N., Kumar, S., Zick, T., Choi, Y., Smith, N. A., and Hajishirzi, H. RewardBench: Evaluating Reward Models for Language Modeling, 2024. URL https://arxiv.org/abs/2403.13787 .

Lee et al. (2024) Lee, A., Bai, X., Pres, I., Wattenberg, M., Kummerfeld, J. K., and Mihalcea, R. A Mechanistic Understanding of Alignment Algorithms: A Case Study on DPO and Toxicity. June 2024. URL https://openreview.net/forum?id=dBqHGZPGZI .

Niu et al. (2024) Niu, S., Miao, C., Chen, G., Wu, P., and Zhao, P. Test-Time Model Adaptation with Only Forward Passes. June 2024. URL https://openreview.net/forum?id=qz1Vx1v9iK .

OpenAI (2023) OpenAI. Preparedness Framework, December 2023.

Pan et al. (2022) Pan, A., Bhatia, K., and Steinhardt, J. The Effects of Reward Misspecification: Mapping and Mitigating Misaligned Models, 2022. URL https://arxiv.org/abs/2201.03544 .

Rathore et al. (2024) Rathore, P., Lei, W., Frangella, Z., Lu, L., and Udell, M. Challenges in Training PINNs: A Loss Landscape Perspective. June 2024. URL https://openreview.net/forum?id=mJGiFr8jLa .

Sanchez et al. (2024) Sanchez, G., Spangher, A., Fan, H., Levi, E., and Biderman, S. Stay on Topic with Classifier-Free Guidance. June 2024. URL https://openreview.net/forum?id=RiM3cl9MdK .

Sawada et al. (2023) Sawada, T., Paleka, D., Havrilla, A., Tadepalli, P., Vidas, P., Kranias, A., Nay, J. J., Gupta, K., and Komatsuzaki, A. ARB: Advanced Reasoning Benchmark for Large Language Models, 2023. URL https://arxiv.org/abs/2307.13692 .

Schlarmann et al. (2024) Schlarmann, C., Singh, N. D., Croce, F., and Hein, M. Robust CLIP: Unsupervised Adversarial Fine-Tuning of Vision Embeddings for Robust Large Vision-Language Models. June 2024. URL https://openreview.net/forum?id=WLPhywf1si .

Sharrock et al. (2024) Sharrock, L., Simons, J., Liu, S., and Beaumont, M. Sequential Neural Score Estimation: Likelihood-Free Inference with Conditional Score Based Diffusion Models. June 2024. URL https://openreview.net/forum?id=8viuf9PdzU .

Shi et al. (2024) Shi, J., Gare, G. R., Tian, J., Chai, S., Lin, Z., Vasudevan, A. B., Feng, D., Ferroni, F., and Kong, S. LCA-on-the-Line: Benchmarking Out of Distribution Generalization with Class Taxonomies. June 2024. URL https://openreview.net/forum?id=HPXRzM9BYZ .

Si et al. (2024) Si, C., Yang, D., and Hashimoto, T. Can LLMs Generate Novel Research Ideas? A Large-Scale Human Study with 100+ NLP Researchers. arXiv preprint arXiv:2409.04109 , 2024.

Siegel et al. (2024) Siegel, Z. S., Kapoor, S., Nagdir, N., Stroebl, B., and Narayanan, A. CORE-Bench: Fostering the Credibility of Published Research Through a Computational Reproducibility Agent Benchmark. arXiv preprint arXiv:2409.11363 , 2024.

Singla et al. (2024) Singla, J., Agarwal, A., and Pathak, D. SAPG: Split and Aggregate Policy Gradients. June 2024. URL https://openreview.net/forum?id=4dOJAfXhNV .

(33) Sun, H., Zhuang, Y., Wei, W., Zhang, C., and Dai, B. BBox-Adapter: Lightweight Adapting for Black-Box Large Language Models.

UK AI Safety Institute (2025) UK AI Safety Institute. Inspect, 2025. URL https://inspect.ai-safety-institute.org.uk/agents.html#sec-basic-agent .

van der Weij et al. (2024) van der Weij, T., Hofstätter, F., Jaffe, O., Brown, S. F., and Ward, F. R. AI Sandbagging: Language Models Can Strategically Underperform on Evaluations. arXiv preprint arXiv:2406.07358 , 2024.

Wang et al. (2022) Wang, R., Jansen, P., Côté, M.-A., and Ammanabrolu, P. Scienceworld: Is Your Agent Smarter than a 5th Grader? arXiv preprint arXiv:2203.07540 , 2022.

Wang et al. (2024a) Wang, T., Kulikov, I., Golovneva, O., Yu, P., Yuan, W., Dwivedi-Yu, J., Pang, R. Y., Fazel-Zarandi, M., Weston, J., and Li, X. Self-Taught Evaluators, 2024a. URL https://arxiv.org/abs/2408.02666 .

Wang et al. (2024b) Wang, X., Lin, B., Liu, D., Chen, Y.-C., and Xu, C. Bridging Data Gaps in Diffusion Models with Adversarial Noise-Based Transfer Learning. June 2024b. URL https://openreview.net/forum?id=PpBs2iL0jv .

Wijk et al. (2024) Wijk, H., Lin, T., Becker, J., Jawhar, S., Parikh, N., Broadley, T., Chan, L., Chen, M., Clymer, J., Dhyani, J., et al. RE-Bench: Evaluating frontier AI R&D capabilities of language model agents against human experts. arXiv preprint arXiv:2411.15114 , 2024.

Wolczyk et al. (2024) Wolczyk, M., Cupial, B., Ostaszewski, M., Bortkiewicz, M., Zajac, M., Pascanu, R., Kucinski, L., and Milos, P. Fine-tuning Reinforcement Learning Models is Secretly a Forgetting Mitigation Problem. June 2024. URL https://openreview.net/forum?id=53iSXb1m8w .

Xia et al. (2024) Xia, X., Liu, J., Zhang, S., Wu, Q., Wei, H., and Liu, T. Refined Coreset Selection: Towards Minimal Coreset Size under Model Performance Constraints. June 2024. URL https://openreview.net/forum?id=yb5xV8LFDq .

Yao et al. (2023) Yao, S., Zhao, J., Yu, D., Du, N., Shafran, I., Narasimhan, K., and Cao, Y. ReAct: Synergizing Reasoning and Acting in Language Models, March 2023. URL http://arxiv.org/abs/2210.03629 . arXiv:2210.03629 [cs].

Zhao et al. (2024) Zhao, B., Hajishirzi, H., and Cao, Q. APT: Adaptive Pruning and Tuning Pretrained Language Models for Efficient Training and Inference. June 2024. URL https://openreview.net/forum?id=sb81Xl50JG .

Zheng et al. (2023) Zheng, L., Chiang, W.-L., Sheng, Y., Zhuang, S., Wu, Z., Zhuang, Y., Lin, Z., Li, Z., Li, D., Xing, E., et al. Judging LLM-as-a-Judge with MT-Bench and Chatbot Arena. Advances in Neural Information Processing Systems , 36:46595–46623, 2023.

Zhuge et al. (2024) Zhuge, M., Zhao, C., Ashley, D., Wang, W., Khizbullin, D., Xiong, Y., Liu, Z., Chang, E., Krishnamoorthi, R., Tian, Y., et al. Agent-as-a-Judge: Evaluate Agents with Agents. arXiv preprint arXiv:2410.10934 , 2024.

## 附录 A 人工智能评估的未来方向

我们在 PaperBench 项目中的经验让我们深刻认识到人工智能开发与评估未来的重要趋势。在许多任务上（超出 PaperBench 范围），当前的人工智能系统性能接近或达到专家人类的水平，因此有必要将那些对人类而言劳动密集型的任务交由人工智能系统来完成。

与大多数现有评估方法不同，PaperBench期望被评估的智能体能够生成复杂且非结构化的输出。此外，该输出无法通过程序进行评分。评分标准（Sawada等人，2023年；Harvey团队，2024年）提供了一种将复杂且定义不明确的任务转化为更简单、定义更清晰的方案的方法：为了应对复杂性问题，我们将评估任务分解为更小的子标准。
为应对规格不足的问题，我们与相关论文的作者合作，就复现研究所需的关键要素以及如何评估各因素的重要性做出具体选择（我们的论文评分标准存在多种不同的实现方式，且均具有同等有效性）。

然而，PaperBench仍存在重要的局限性（详见第7节）。下面，我们将探讨有助于解决这些局限性的方向，从而更普遍地实现对复杂且无结构任务的可扩展且可信的评估。

### A.1 探索评分标准的设计与制定

在 PaperBench 设计的评分标准中，子节点的顺序反映了它们之间的依赖关系；后续的子节点依赖于先前的子节点。例如，获取论文匹配结果的要求位于实现实验运行所需方法学的要求之后。然而，当前的设计并未明确之前哪些要求是必需的；理想情况下，评分标准的设计应明确评分标准中每个要求所必须满足的具体要求。未来的研究可以探索在评分标准中使用依赖图作为潜在的解决方案。

鉴于制定评分标准的难度，自动化评分标准创建是未来工作的另一个有价值方向。我们的初步实验表明，如 o1 这样的前沿模型在理解和总结论文方面非常出色。然而，我们发现即使进行大量的提示工程处理，这些前沿模型也难以从头到尾制定出可靠的评分标准。由于评分标准的复杂性，对模型生成的评分标准进行审核和迭代同样具有挑战性，但我们认为人工参与的工作流程可能会在这方面取得成效。我们还认为，利用模型对评分标准进行评审是一种有前景的方法，能够加速评分标准的制定过程。

### A.2 改进自动化评判机制

在 PaperBench 中，一个评分标准通常包含数百个需要评估的节点，由人类进行评估会成本过高；在初步实验中，我们发现使用专家人类进行评分需要数十小时的时间。正如 SimpleJudge（第 D 节）所展示的那样，基于模型的评估方法（Chiang & yi Lee, 2023；Lambert 等，2024；Wang 等，2024a）在基于评分标准的评估的可扩展性方面起着重要作用。我们通过 JudgeEval（第 4.2 节）迈出了第一步，用于衡量基于模型的评判者在复杂输出任务上的准确性，但还需要进一步工作来提升准确性并了解其优缺点。

我们进一步指出，评估者越可靠，评分标准的任务分解就不需要那么细致，随着评估者能力提升，进行任务分解所需的努力可能会减少。我们将仔细规范与将任务委托给评估者之间的权衡问题留待未来的研究去探讨。

### A.3 规范化博弈与对抗性智能体

PaperBench的评分标准经过精心设计，旨在避免误判和假阳性问题，但由于节点数量众多且论文复现工作复杂，我们目前仍无法排除评估中的漏洞。智能体可能出于某种动机在PaperBench上表现不佳（van der Weij等人，2024年）或表现过优（DeepMind，2024年；Pan等人，2022年）；未来的研究可以探讨智能体在PaperBench上能够令人信服地表现不佳或过优的能力与倾向。

## 附录 B 论文选择流程

我们的最终数据集是通过对 ICML 2024 会议论文进行系统筛选过程构建而成的。每个筛选步骤都是为了确保数据集中的论文适合用于复现研究。我们使用了 gpt-4o-2024-08-06 模型以及一系列提示词来进行初步筛选。下面我们将详细说明每个筛选步骤及其背后的逻辑。

•

商业与地域筛选：如果75%或更多的作者有相关机构关联，表明由于与商业实验室或某些国家合作的限制，作者之间不太可能进行合作，则这些论文将被排除在外。

•

经验性内容筛选规则：论文中的至少一项贡献必须包含重要的经验性实验，且需要复杂的工程操作才能复现。这排除了位置论文和纯理论论文。我们还排除那些主要介绍新软件框架、库或工具的论文，因为这类论文并未提供新的实验结果。

•

硬件要求筛选：那些需要在多个计算节点上进行分布式训练的论文被排除在外。这样就能确保所有剩余的论文可以在单台机器上复现，从而更方便进行重复实验。

•

模型依赖过滤规则：那些基于闭源预训练模型（如 GPT-4、Claude、PaLM）的论文被排除在外。

•

数据需求筛选器：那些需要人类数据收集或标注的论文被排除在外。这样就能确保可重复性，无需新的人类参与者或标注人员。

•

可重复性筛选标准：论文中必须包含足够的细节，以便通过阅读并遵循研究方法，从头开始复现实验结果。关于我们如何确保在某些信息缺失的情况下仍能实现可重复性，详见第3.2节。

•

框架论文筛选：主要介绍新软件框架或库的文章被排除在外，因为这些通常需要与研究论文不同的重复验证方法。

•

可访问依赖项筛选器：所有论文的依赖项都应易于获取。如果论文存在无法访问的依赖项（例如修改闭源模型）或易更改的依赖项（例如经常变化的不可靠 API 端点），这些依赖项必须可被替代，或者可以移除，且不会使剩余论文的复现变得无趣或不可能。

随后我们随机选取剩余的Spotlight和Oral论文进行阅读，以确保没有因自动过滤而遗漏的问题。我们联系了通过此审核流程的论文作者，最终共联系了42位作者，并成功与20位作者达成合作，他们同意为我们编写其论文的评分标准。

## 附录 C 评分标准与补充内容创作流程

每个评分标准都是与论文的原始作者之一共同制定的，以确保其准确性和相关性。该过程从两位研究工程师起草初始评分标准开始，随后经过多轮内部审核，以完善其结构和内容。

内部审核完成后，会将评分标准分享给原始作者。该作者根据正式协议与我们合作，以验证其准确性并提供专业意见。此阶段通常需要多轮反馈，以解决论文方法或结果方面的疑问。作者提供的任何说明都会被纳入论文的补充材料中。

平均而言，制定评分标准及其补充内容需要数十小时的工作时间。我们参考图4，其中展示了PaperBench中某个评分标准的片段。

[查看原图表（阅读版）](bilingual.html#paperbench-0246)

表7：评分标准中节点与叶节点的数量

[查看原图表（阅读版）](bilingual.html#paperbench-0250)

图4：PaperBench中某篇论文的评分标准片段。以底层JSON格式（左）和图形用户界面形式（右）展示。

## 附录 D SimpleJudge 实现方案

对于提交的文档，我们的评审员依据评分标准独立对每个叶节点进行评分。针对某个特定叶节点，评审员会收到该论文的 Markdown 格式、附加材料、评分标准中的先前要求（兄弟节点及直接祖先节点）、该叶节点的具体要求以及提交文档中的相关文件。

出于上下文管理的原因，我们收集提交文件的相关内容，具体操作如下：

对于代码开发与执行叶节点，提交目录首先通过简单的源代码、文档及配置文件（如 markdown、python、JSON、TOML、C++等）白名单过滤，同时排除与源代码无关的目录（如 venv 目录）中的内容。如果经过过滤后的所有提交文件均符合 $(n_{ctx}-10,000)$ 的要求，其中 $n_{ctx}$ 为评判所使用基础模型的上下文窗口大小，则将所有文件合并（在每文件顶部添加文件名），并加入上下文窗口中。
否则，我们进一步对代码库进行筛选：由评判者对文件进行排序，仅选取排名前十的文件纳入上下文。我们将所有文件名展示给评判者，要求其按与当前需求的相关程度对文件进行排序，然后按相关度从高到低添加文件，直到超过 $(n_{ctx}-10,000)$ 个令牌的上下文窗口限制。

对于结果匹配节点，我们遵循完全相同的流程，但不再对源代码和配置文件进行白名单筛选，而是对可能包含表格数据的纯文本文件进行白名单筛选（如 CSV、JSON、JSONL、HTML 等），这些文件的最后修改时间戳需晚于 reproduce.sh 执行的开始时间。与代码开发与执行阶段类似，我们同样对文档文件进行白名单筛选，并将非源目录列入黑名单。

请参见图7，了解用于文件排序的提示词。

在确认了相关文件后，我们向智能体法官提出要求，评估叶节点的要求是否得到满足，并说明其选择的二元分数的依据；关于所使用的提示词，请参见图8和图9。随后我们使用 gpt-4o 20 20 20 gpt-4o-2024-08-06 来解析法官模型的回复，以得到一个应为0或1的得分、一个作为法官模型推理简短总结的解释，以及一个表示回复中是否包含有效得分的布尔值变量 valid_score。

## 附录 E 监控实施

我们的基础监控实现会对日志文件进行简单的文本搜索，以识别被列入黑名单的术语出现情况。当发现被列入黑名单的术语时，监控系统会记录该术语以及周围的几行上下文内容，以便人工审核。

## 附录 F 智能体实现

在执行有时间限制的智能体时，我们并未将向模型 API 查询时为了满足时间限制而进行的重试所花费的时间计入总时长；这些重试通常是由于速率限制或服务器错误导致的。

### F.1 基础智能体

我们的智能体框架采用了基本的 ReAct Yao等人（2023）智能体架构，该架构会持续执行工具使用循环，直到智能体用完步骤或时间为止。它基于 Inspect AI 的 basic agent UK AI Safety Institute（2025）框架，但进行了以下修改：

•

我们将提交工具重新定义为一种“结束任务”工具，智能体在完成尝试后应调用该工具，以防止其过早调用它。

•

我们添加了一个简单的上下文长度管理系统，当接近上下文限制时，会从智能体的上下文中移除旧的非指令消息。

•

我们提供一款分页文件读取工具，该工具允许智能体以逐步的方式读取文件，并针对关键词在文件中进行搜索。

我们设计系统提示词时，从原始基础智能体系统提示词开始，并根据使用最终数据集小子集进行的初步实验结果对其进行调整。在这些初步实验中，我们发现了多种故障模式，例如：

•

这些模型只是描述了复现该论文的方案，而不会调用任何工具来编写代码并自行完成复现工作。

•

像 o1 这样的推理模型特别容易试图在单次回复中完成任务，会调用提交工具并发送包含多段代码的庞大信息。

•

这些模型并未尝试阅读整篇论文，因此自然无法完成完整的复现工作。

•

这些模型会频繁地快速调用最终任务工具。

我们用于 BasicAgent 的最终系统消息显示在图 10 中。智能体通过用户消息接收任务指令（见附录 F.3）。

### F.2 迭代智能体

尽管我们在开发 BasicAgent 时对原始框架进行了改进，但我们发现大多数与 BasicAgent 一起使用的模型仍会故意使用提交工具来提前结束任务。有趣的是，这些模型大多以“被要求完成论文的部分复现而非完整复现”为理由来解释这一选择。

我们从 BasicAgent 开发了 IterativeAgent，以促使模型完成整个任务。每次向模型提问时，我们都会要求它仅执行下一步操作以复现该论文，我们发现这能显著降低模型提前完成任务的概率。此外，我们还删除了提交工具，因此 IterativeAgent 必须利用所有可用时间进行工作。

迭代智能体使用图11中显示的不同系统消息。如果模型生成的消息中没有工具调用，我们会在图12中将用户消息添加到消息历史记录中。

### F.3 任务说明

我们在图13和图14中展示了我们的基准测试任务说明。我们并未对提交智能体框架应如何接收这些任务说明制定任何规则（例如，框架可以选择忽略这种特定的说明形式，自行调用后端模型），并将它们作为我们的基准测试的一部分提供出来。

## 附录 G：关于 JudgeEval 的进一步说明

[查看原图表（阅读版）](bilingual.html#paperbench-0287)

图 5：在 SimpleJudge 中，不同模型后端在 JudgeEval 上的性能表现与每篇论文的平均成本之间的关系。模型成本以输入与输出令牌数乘以 OpenAI API 的相应令牌成本来计算。人工成本按每小时 100 美元的标准计算，约为 12 小时的工作时间。推理模型以“高”级别의推理努力进行运行。

在图 5 中，我们展示了在 JudgeEval 上使用 SimpleJudge 时，不同模型后端的平均性能（F1 分数）与成本（每篇论文美元金额）之间的关系。我们根据 API 使用成本来估算模型成本（输入/输出令牌数乘以截至 2025/03/21 的公开 OpenAI o1 API 定价中的每令牌成本）。

我们还将专家人工表现与成本进行绘制，将其视为理想表现，并以每篇论文需工作12小时、假设时薪为100美元/小时来估算成本。最后，我们绘制了随机基准模型的性能曲线，其中评委会随机将叶节点标记为满意或不满意。

我们发现，对于最终用户而言，人类的成本比最昂贵的模型（o1）高出数百美元。此外，我们发现 o3-mini 的性能与 o1 相当，而成本仅为 o1 的十分之一。

[查看原图表（阅读版）](bilingual.html#paperbench-0291)

表8：作为JudgeEval项目的一部分且采用SimpleJudge框架进行评估的模型的宏观平均F1分数。我们同时报告了整体得分以及按需求类型分组的得分情况。

在表8中，我们结合表3中报告的整体F1分数，还展示了其分层对比数据，以衡量SimpleJudge根据需求类型的表现情况。

我们看到，不同需求类型的性能相对稳定，但“难度”的明显梯度也清晰可辨：模型在代码开发节点表现最差，而在结果匹配节点表现最佳。o3-mini-high在代码开发节点获得了0.72的F1分数，我们认为这对于该需求类型的跟踪信号来说是可以接受的。我们注意到，o1-high在代码开发和执行节点似乎优于o3-mini-high，不过这种差异可能源于噪声因素，且由于成本要高得多，因此并无实际意义。

## 附录 H 精简评分标准评分规则

如第7节和附录G所述，对PaperBench的发布进行评分成本相当高。尽管o3-mini的字符费用有所降低，但平均而言，每篇论文的评分仍需约66美元。虽然PaperBench Code-Dev提供了另一种选择，但代价是需要放弃执行任务与结果匹配任务。

作为降低评分所需成本与时间的替代方法，我们尝试对呈现给评审员的评分标准进行“修剪”处理，将深度超过一定值的子树合并为单个叶节点。为了实现这种合并，当深度超过特定值后，只需将当前节点的子树及子叶节点的内容进行拼接即可。

这大大减少了法官所需的输出令牌数量，因为决策次数也减少了：不再需要对所有叶节点进行推理和评分，而是当深度超过一定阈值后，法官只需对整个子树进行评分，给出介于 0 和 1 之间的浮点分数。然而，这使得法官的评分任务更加困难，因为他们必须一次性判断多个要求是否得到满足。

[查看原图表（阅读版）](bilingual.html#paperbench-0299)

图6：o3-mini SimpleJudge在JudgeEval中对‘rice/0’提交作品所给出的复现分数，随修剪深度变化的情况。深度为100时的修剪相当于该论文无需进行修剪。红色曲线表示人类评审员的真实评分。误差条为三次重复实验的平均标准误差。

在图6中，我们展示了在不同深度进行剪枝时，Judge在JudgeEval中的某篇提交作品上所给出的整体复现分数（见第4.2节）。我们发现，对于这篇论文和该提交作品而言，在深度3之外进行剪枝后，其分数已接近无剪枝情况下的默认分数。我们注意到，在深度3进行剪枝后，评分成本降低了10 $\times$，而Judge的性能仅略有下降。

虽然这些结果令人鼓舞，但我们希望强调，这些只是“Judge”实验版本下的初步结果，并且我们也观察到了性能不理想的案例。我们预计，随着模型性能的提升，我们可以逐渐转向对子树进行评分，而非仅对整棵树进行评分。

## 附录一 全部结果

在表10、11、12、13、14、15、16、17和18中，我们展示了数据集中20篇论文中每个智能体的表现情况。值得注意的是，对于大多数智能体而言，同一篇论文上的结果存在较大差异。由于这种高方差现象，我们建议其他人在评估PaperBench时使用多个种子进行实验，以便获得准确的智能体性能指标。

### I.1 按需求类型分层的结果

根据表9，按需求类型划分的结果可见。我们发现这些模型在“执行”和“结果匹配”需求类型上的表现较差，而在“代码开发”节点上的得分则更高。这表明这些模型擅长编写大量代码，但在整合、测试以及成功运行这些代码以取得成果方面并不成功。

[查看原图表（阅读版）](bilingual.html#paperbench-0306)

表9：采用我们的框架的模型在不同需求类型下的平均复现得分。标准误差是基于三个种子计算得出的，但 o1（迭代智能体）和 gemini-2.0-flash（基础智能体）则基于两个种子计算。

[查看原图表（阅读版）](bilingual.html#paperbench-0308)

表10：GPT-4o BasicAgent结果。*表示因违反PaperBench规则而被取消资格，结果被设定为0%。

[查看原图表（阅读版）](bilingual.html#paperbench-0310)

表11：o1 BasicAgent结果。

[查看原图表（阅读版）](bilingual.html#paperbench-0312)

表12：o1迭代智能体结果。

[查看原图表（阅读版）](bilingual.html#paperbench-0314)

表13：o3-mini基础智能体结果。

[查看原图表（阅读版）](bilingual.html#paperbench-0316)

表14：o3-mini 迭代智能体结果。

[查看原图表（阅读版）](bilingual.html#paperbench-0318)

表15：Claude 3.5 Sonnet BasicAgent 结果。

[查看原图表（阅读版）](bilingual.html#paperbench-0320)

表16：Claude 3.5 Sonnet迭代智能体结果。

[查看原图表（阅读版）](bilingual.html#paperbench-0322)

表17：Gemini 2.0 Flash BasicAgent 测试结果。第3次“我的模型会忘记什么”测试因基础设施问题失败。*表示因违反 PaperBench 规则而被取消资格，结果被设定为0%。

[查看原图表（阅读版）](bilingual.html#paperbench-0324)

表18：R1 BasicAgent结果。*表示因违反PaperBench规则而被取消资格，故结果被设定为0%。

[查看原图表（阅读版）](bilingual.html#paperbench-0328)

图 7：法官文件排序提示。如 {tree_structure} 这样的变量在运行时会被替换为其实际值。

[查看原图表（阅读版）](bilingual.html#paperbench-0331)

图8：评判提示词。第1部分共2部分。如 {paper_markdown} 这样的变量在运行时会被替换为其实际值。对于 PaperBench-CodeDev 而言，红色文本被从提示词中省略；蓝色文本仅针对 PaperBench-CodeDev 显示；绿色文本仅针对代码开发与执行叶节点显示；紫色文本仅针对 textttResult Match 节点显示。

[查看原图表（阅读版）](bilingual.html#paperbench-0334)

图 9：评判提示词。共两部分。{criteria}符合当前正在评分的叶节点的要求。{preceding_criteria}为前序节点（兄弟节点及直接祖先节点）的要求。任务类别对应我们的“代码开发”、“执行”和“结果匹配”类别。相应的{task_category_question}分别为“智能体的源代码是否包含对此的正确实现？”、“运行 reproduce.sh 脚本是否能确保该任务成功执行？”以及“复现结果是否与这些结果一致？”。

[查看原图表（阅读版）](bilingual.html#paperbench-0337)

图10：基础智能体系统提示词

[查看原图表（阅读版）](bilingual.html#paperbench-0340)

图11：迭代智能体系统提示词

[查看原图表（阅读版）](bilingual.html#paperbench-0343)

图 12：迭代智能体继续消息

[查看原图表（阅读版）](bilingual.html#paperbench-0346)

图13：任务说明，続于第2部分

[查看原图表（阅读版）](bilingual.html#paperbench-0349)

图14：任务说明，续接第1部分内容

43 12 4 33 38 10 40 41 29 20 24 7 27 3 32 28 25 1 21 17

