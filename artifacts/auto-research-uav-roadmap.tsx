import { H1, H2, H3, Text, Stack, Row, Grid, Card, CardHeader, CardBody, Table, Link, Pill, Button, Divider, useCanvasState, useHostTheme } from 'cursor/canvas';

const papers = [
  {group:'文献综合', name:'AutoSurvey', year:'NeurIPS 2024', url:'https://papers.nips.cc/paper_files/paper/2024/hash/d07a9fc7da2e2ec0574c38d5f504d105-Abstract-Conference.html', learn:'检索→大纲→分节写作→整合评估，是综述流水线的直接基线。', limit:'自动生成综述不等于完成系统性文献审查，也不能单靠语言质量证明可靠。', order:'第一轮'},
  {group:'文献综合', name:'OpenScholar', year:'2024 预印本；Nature 2026 论文版', url:'https://arxiv.org/abs/2411.14199', learn:'学习检索、证据片段与带引用的科学问答；先做小语料复现。', limit:'问答评测与完整综述、原创研究是不同任务。历史模型得分不代表当前前沿水平。', order:'第一轮'},
  {group:'文献综合', name:'SurveyForge / SurveyBench', year:'ACL 2025 正式版', url:'https://aclanthology.org/2025.acl-long.609/', learn:'观察大纲、记忆与引文质量如何分别评价。', limit:'人工综述不是唯一正确答案；需要单独检查证据支持和遗漏。', order:'第二轮'},
  {group:'科研闭环', name:'The AI Scientist-v2', year:'2025 预印本', url:'https://arxiv.org/abs/2504.08066', learn:'树搜索实验管理、运行代码、分析结果、生成论文。', limit:'论文报告的 workshop 评审结果不能外推为稳定达到主会水平。', order:'第一轮'},
  {group:'科研闭环', name:'Towards end-to-end automation of AI research', year:'Nature，2026-03-25', url:'https://www.nature.com/articles/s41586-026-10265-5', learn:'综合理解有模板与无模板的研究自动化及其评测。', limit:'与 AI Scientist 系列有延续关系，不作为独立重复验证计算。', order:'第二轮'},
  {group:'科研闭环', name:'Co-Scientist', year:'2025；2026-06 修订', url:'https://arxiv.org/abs/2502.18864', learn:'生成、批评、改进假设与锦标赛式选择；有生物医学实验案例。', limit:'案例来自特定应用；系统内部排名不能直接替代无人机实验。', order:'第二轮'},
  {group:'科研闭环', name:'Kosmos', year:'2025 预印本', url:'https://arxiv.org/abs/2511.02824', learn:'结构化研究记忆连接文献、分析代码和结论。', limit:'长时运行和作者报告的效率提升不等于每个结论都已验证。', order:'拓展'},
  {group:'科研闭环', name:'karpathy/autoresearch', year:'开源工程仓库；检索于 2026-11-05', url:'https://github.com/karpathy/autoresearch', learn:'从受限修改、固定训练预算和可计算指标学习最小实验闭环。', limit:'固定任务的优化循环与开放式科学创新、论文写作并非同一问题。', order:'第一轮'},
  {group:'评测与可信性', name:'PaperBench', year:'2025 预印本', url:'https://arxiv.org/abs/2504.01848', learn:'从论文复现任务学习细分评分标准与可执行验收。', limit:'复现能力不能直接推断发现新知识的能力。', order:'第一轮'},
  {group:'评测与可信性', name:'AstaBench', year:'ICLR 2026；2026-04 修订', url:'https://arxiv.org/abs/2510.21652', learn:'统一工具、预算、任务接口，比较文献到研究闭环的能力。', limit:'整体平均分不能替代你自己的无人机任务评测。', order:'第一轮'},
  {group:'评测与可信性', name:'PAPERBENCHX', year:'2026-10-29 预印本', url:'https://arxiv.org/abs/2610.39744', learn:'跨学科复现与从干净环境重跑后评分的设计。', limit:'新近预印本；局部步骤得分和完整复现率需要分开报告。', order:'第二轮'},
  {group:'评测与可信性', name:'Can LLMs Generate Novel Research Ideas?', year:'2024 首发；ICLR 2025 正式版', url:'https://arxiv.org/abs/2409.04109', learn:'学习专家盲评、可行性与新颖性分开评价的设计。', limit:'想法被认为新颖，不等于实施后有收益。', order:'第二轮'},
  {group:'评测与可信性', name:'EPOCH', year:'2026-10-04 预印本', url:'https://arxiv.org/abs/2610.06986', learn:'研究任务契约、证据记忆、主动反证与独立重跑。', limit:'与拟议方向高度相关；不能把“加入证据审核”直接当作原创贡献。', order:'第一轮'},
  {group:'评测与可信性', name:'Sound Agentic Science Requires Adversarial Experiments', year:'ICLR 2026 workshop', url:'https://arxiv.org/abs/2604.22080', learn:'建立能推翻主张的测试，识别选择性分析与正结果偏好。', limit:'方法论主张需要在具体任务上进行受控验证。', order:'第二轮'},
  {group:'无人机实验', name:'EGO-Planner', year:'RA-L 2021', url:'https://arxiv.org/abs/2008.08835', learn:'固定为局部轨迹规划基础，辨明与高层探索决策的接口。', limit:'局部规划能力不能单独代表完整探索或语言导航能力。', order:'领域基础'},
  {group:'无人机实验', name:'FUEL', year:'RA-L / ICRA 2021', url:'https://github.com/HKUST-Aerial-Robotics/FUEL', learn:'frontier、视点和分层探索规划；适合几何探索基线。', limit:'统一传感器、动力学、速度和地图设置后才可比较。', order:'领域基础'},
  {group:'无人机实验', name:'FlightBench', year:'2025-05 v3；关联 RA-L 2025 DOI', url:'https://arxiv.org/abs/2406.05687', learn:'局部视觉导航评测与场景难度维度。', limit:'它不是语义探索或指令跟随的直接替代基准。', order:'领域基础'},
  {group:'无人机实验', name:'OpenUAV / UAV-Need-Help', year:'ICLR 2025', url:'https://proceedings.iclr.cc/paper_files/paper/2025/hash/15ce8e7afe5ee95bad56e3b9be28d3d1-Abstract-Conference.html', learn:'真实感 UAV 仿真、目标搜索与不同级别指导信息。', limit:'与纯几何覆盖、局部避障任务分别评价。', order:'第二阶段'},
  {group:'无人机实验', name:'VLN on the Fly', year:'IMAV 2026', url:'https://vln-on-the-fly.github.io/', learn:'Orin NX 上的视觉语言模块与 EGO-Planner 组合。', limit:'项目报告使用室内动捕，不能等同于无外部定位的野外自主飞行。', order:'第二阶段'},
  {group:'无人机实验', name:'LightVLN', year:'2026-10-04 预印本', url:'https://arxiv.org/abs/2610.05024', learn:'紧凑历史表示与计算约束，供 Orin NX 部署研究参考。', limit:'报告的 Orin NX 结果是 real-to-sim HIL，不能当作自由飞行实证。', order:'拓展'},
];

const weeks = [
  ['1–2','定义任务与学习','阅读第一轮论文，建立文献卡；冻结一个能重复运行的探索 baseline；列出所有人工干预。','一页任务合同、30–50 篇候选文献、5 个可重复场景。若基线不稳定，先修实验基础。'],
  ['3–4','文献证据与综述原型','精选 20–30 篇全文，记录原始段落、适用条件、支持/反驳关系；比较直接长上下文、普通 RAG、AutoSurvey 风格流程。','可追溯的短综述、100 条左右人工核查主张、失败类型分析。数字是 pilot 目标。'],
  ['5–6','最小研究闭环','连接候选生成、受限代码修改、仿真执行和独立评分；只开放 frontier 排序或恢复策略一个模块。','一个 Agent 能从失败案例提出可证伪假设、跑实验并如实输出正负结果。'],
  ['7–8','选题验证与小规模对照','比较强单 Agent、常规自动搜索、条件证据检索和实验选择策略；检查与 EPOCH 等最近工作差异。','继续/收缩/转向决定。若收益来自更多预算或更强模型，不能归因于新机制。'],
  ['9–12','正式仿真实验','冻结开发/验证/盲测划分；跨场景族、研究任务和独立搜索重复；完成机制消融与失败归因。','研究系统与无人机双层指标、置信区间、成本曲线、完整运行档案。'],
  ['13–14','Orin NX 与硬件在环','测端到端 p50/p95 延迟、内存、功率模式和超时行为；在既有飞控接口上验证。','硬件部署证据与淘汰记录。单独报告仿真、HIL、自由飞行。'],
  ['15–16','有限实机验证与论文','在匹配条件下比较固定 baseline 与预先选定候选，记录接管与失败；按证据生成图表和稿件。','可重跑实验包、论文初稿、适用边界；不承诺接收或一定获得正结果。'],
];

const firstWeek = [
  '写一页任务合同：先选纯几何探索；明确覆盖口径、时限、失败、可修改模块和预算。',
  '冻结一个已有基线，记录代码、镜像、地图、传感器、控制参数与评测脚本版本。',
  '用 5 个场景各跑 3 次，检查是否能稳定复现；结果不一致先定位原因。',
  '精读 AutoSurvey、OpenScholar、AI Scientist-v2、AstaBench、EPOCH；每篇留一页笔记。',
  '收集约 30 篇领域候选论文，优先人工精读其中 10 篇；标出适用条件与局限。',
  '选一个常见失败，写 3 个竞争性解释和 1 个区分它们的最小实验。',
  '形成周报：已知事实、尚未验证假设、失败日志、下一轮实验和预算。',
];

export default function AutoResearchRoadmap() {
  const {tokens:t} = useHostTheme();
  const [tab,setTab] = useCanvasState('auto-research-uav-tab','路线');
  const [filter,setFilter] = useCanvasState('auto-research-uav-paper-filter','全部');
  const [done,setDone] = useCanvasState<number[]>('auto-research-uav-week-one',[]);
  const tabs=['路线','文献地图','流水线','研究设计','执行计划'];
  return <Stack gap={20} style={{padding:24,maxWidth:1180,margin:'0 auto',color:t.text.primary,background:t.bg.editor}}>
    <Stack gap={8}>
      <Text size="small" tone="secondary">研究启动方案 · 2026-11-05 · 定向检索与方案建议，非穷尽式系统综述</Text>
      <H1>让 Auto Research 在无人机实验中接受检验</H1>
      <Text>以已有探索/导航系统为实验对象，先建可靠的研究助手，再验证它能否在固定预算下发现可复现、可部署的改进。</Text>
      <Text>文献清单已补充近期工作并修正阅读顺序，原始 20 项不代表当前最强方法。</Text>
      <Link href="/home/zhywwyzh/.cursor/projects/home-zhywwyzh-workspace-AutoResearch-UAV/canvases/auto-research-bilingual-reading.canvas.tsx">打开 26 项中英对照阅读与时效性复核</Link>
      <Row gap={8} wrap>{tabs.map(x=><Pill key={x} active={tab===x} onClick={()=>setTab(x)}>{x}</Pill>)}</Row>
    </Stack>

    {tab==='路线' && <Stack gap={20}>
      <Card><CardHeader>建议的第一主线</CardHeader><CardBody><Stack gap={10}>
        <H2>文献条件 → 可证伪假设 → 最小判别实验 → 留出场景复验</H2>
        <Text>先围绕几何探索中的 frontier 选择、视点选择或失败恢复开展研究；固定 EGO 类局部规划器和飞控。流程稳定后，再引入语义找物、语言导航、模型调用调度。</Text>
        <Text>候选研究题目：面向无人机探索的条件感知文献综合与预算受限实验选择。它目前是研究问题，不是已确认的新颖方法；证据治理、反证和实验搜索已有先例，必须做最近邻对照。</Text>
      </Stack></CardBody></Card>
      <Grid columns="repeat(auto-fit,minmax(260px,1fr))" gap={24}>
        <Stack gap={8}><H3>你的基础</H3><Text>Orin-NX 四旋翼；4070 Ti SUPER；少量 H20/A100；已有 EGO-Planner、VLN 类工作；需要仿真与实机验证。人员尚未确定，16 周按约 2 名主要参与者估算，单人需收缩范围或延长。</Text></Stack>
        <Stack gap={8}><H3>两类论文目标</H3><Text>应用论文：AI 帮你发现了有效的无人机方法，主要证明导航贡献。Auto Research 论文：提出改进研究流程的方法，需跨多个研究任务证明系统更可靠或更节省预算。应先确定主贡献，避免两边都证据不足。</Text></Stack>
      </Grid>
      <H2>三个可选入口</H2>
      <Table headers={['入口','起步交付','论文贡献可能来自','适合条件']} rows={[
        ['A 文献综合','带证据的专题综述和研究缺口图','任务/假设/部署条件分类；遗漏与矛盾识别；高质量评价数据','暂时没有稳定仿真；约 4–6 周可做原型'],
        ['B 已有成果改进（推荐）','一个可重跑的无人机研究闭环','条件感知检索、实验选择或错误结论控制的可验证机制','有稳定基线、日志和可计算指标'],
        ['C 通用端到端科研','跨领域发现、代码、实验和论文系统','跨任务泛化与长期研究自治','适合作为长期愿景；早期投入和评价负担较大'],
      ]}/>
      <Text size="small" tone="secondary">以上时间为规划估计，不是已有实验结果或论文产出保证。</Text>
      <H2>与你现有工程记录的连接</H2>
      <Text>2026-10-26 的 frontier A/B 记录明确撤回了混入仿真内部控制律差异的比较。这个案例可用于设计研究 Agent 的“混杂识别”任务：它能否发现比较条件不一致，并拒绝把覆盖变化解释成算法收益？它不是当前算法有问题的结论，也不能用撤回数字证明提升。</Text>
      <Link href="/home/zhywwyzh/workspace/DiffAgent2-Exploration/doc/iteration/2026-10-26-frontier-full-scene-benchmark.md">查看既有 A/B 记录</Link>
      <Text>VLN-AN 的确切论文或代码版本尚未确认，本方案不把它擅自对应到 AerialVLN、OpenUAV 或其他同类工作。正式基线需核对原论文与 commit。</Text>
    </Stack>}

    {tab==='文献地图' && <Stack gap={18}>
      <H2>先读机制与评价，再扩展论文数量</H2>
      <Text>第一轮约 7–8 项，目标是能解释输入、输出、研究循环、证据、评测和失败条件。每篇做一页笔记；“作者声称”“实验支持”“我们推测”分别记录。条目按原论文/作者项目核对，尚未逐篇完成全文复现。</Text>
      <Row wrap gap={8}>{['全部','文献综合','科研闭环','评测与可信性','无人机实验'].map(x=><Pill key={x} active={filter===x} onClick={()=>setFilter(x)}>{x}</Pill>)}</Row>
      <Table headers={['工作与来源','阅读用途','证据边界','顺序']} rows={papers.filter(x=>filter==='全部'||x.group===filter).map(p=>[
        <Stack gap={4} key={p.name}><Link href={p.url}>{p.name}</Link><Text size="small" tone="secondary">{p.year} · {p.group}</Text></Stack>,p.learn,p.limit,p.order
      ])}/>
      <H2>后续文献检索协议</H2>
      <Text>按两个语料库检索：科研自动化方法库，以及无人机领域知识库。先用会议/期刊原站、arXiv 和作者仓库确认身份，再沿参考文献向后追溯、沿被引关系向前扩展。记录检索日期、检索式、版本、纳入和排除理由；同一论文预印本与正式版去重。</Text>
      <Text>领域检索维度：aerial exploration、frontier/viewpoint selection、semantic object search、aerial VLN、active perception、latency-aware navigation。方法检索维度：autonomous scientific discovery、literature synthesis、experiment selection、falsification、scientific reproducibility、evidence-grounded agents。</Text>
      <Text>Related Work 是发现候选文献的入口。重要判断必须回到被引论文的原始实验与限制；不能把多篇论文重复引用同一结果当作多份独立证据。</Text>
      <Text>近期顶会用于发现趋势，经典和期刊用于追溯基础，预印本单独标注状态。不要用“顶会”标签替代实验质量和可复现性判断。</Text>
    </Stack>}

    {tab==='流水线' && <Stack gap={20}>
      <H2>研究系统在工作站运行；被研究的导航系统在无人机上运行</H2>
      <Text>外层研究 Agent 负责文献、假设、代码、实验和报告。内层导航 Agent 负责感知、探索与运动。两者分别设定预算与评价指标，避免把研究模型的 API 延迟当成飞行推理延迟。</Text>
      <Table headers={['阶段','输入 → 产物','必须保留的证据']} rows={[
        ['1 任务合同','研究目标、基线与硬件 → 固定任务规范','可修改文件/模块、场景划分、预算、成功/失败定义、停止规则'],
        ['2 文献采集','种子论文与检索式 → 去重语料','DOI/arXiv ID、版本、日期、来源、全文缺失、纳入/排除理由'],
        ['3 条件化证据','全文与图表 → 主张卡片','原文位置、任务、传感器、运动假设、训练数据、比较设置、支持与反证'],
        ['4 综述与缺口','证据卡 → 分类、争议、缺口和大纲','每条综合结论的证据；“未检索到”不得自动升级为“无人做过”'],
        ['5 假设与设计','已有方法、失败日志、领域证据 → 候选方案','最近邻方法、机制解释、预测、替代解释、可推翻条件、最小实验'],
        ['6 受限实现','入选方案 → 独立代码修改','代码 diff、单元/接口检查、环境与依赖；不修改评分器和盲测集'],
        ['7 实验执行','候选与实验计划 → 原始运行记录','容器/commit、场景、seed、资源、启动命令、退出状态、超时、人工接管'],
        ['8 独立复核','原始记录 → 经复核结论','独立指标计算、留出集重跑、统计不确定性、混杂与数据泄漏检查'],
        ['9 论文生成','已核验结论 → 图表与稿件','图表由脚本生成，数值可追溯到 run；无证据时输出未知或失败'],
      ]}/>
      <Grid columns="repeat(auto-fit,minmax(270px,1fr))" gap={24}>
        <Stack gap={10}><H3>最小数据结构</H3><Text>Paper：身份、版本、出处和全文。Claim：主张、原文位置、条件、支持/反驳证据。Hypothesis：机制、预测、替代解释、证伪条件。Experiment：基线、候选、场景、预算、评价脚本和结果。ManuscriptClaim：可引用的文献/实验 ID。</Text><Text>初期用 JSON/SQLite、文件存储和明确状态机即可；先把来源与重跑打通，后续再决定是否需要图数据库或多 Agent 编排。</Text></Stack>
        <Stack gap={10}><H3>理论依据的层次</H3><Text>区分已有定理及其适用条件、待证明命题、机制假设和纯经验观察。模型写出的推导要独立检查假设、单位、边界情况和反例；小规模仿真验证不能冒充一般性证明。</Text><Text>以探索为例，可从信息增益、部分可观测决策与成本约束解释设计，但应声明近似：未知地图、非独立观测与动态延迟可能破坏理想假设。</Text></Stack>
      </Grid>
      <H2>模型与算力的分工</H2>
      <Table headers={['资源','建议职责','实验前需要测量']} rows={[
        ['前沿推理/编码模型','难文献分析、研究设计、代码修改和审查；初期可用 API','以自己的 10–20 个任务比较至少两种可用模型；固定版本、预算和工具后选型'],
        ['4070 Ti SUPER','本地开发、渲染仿真、小模型推理、短周期实验','仿真与模型争用造成的时序变化；先测吞吐再决定并行数'],
        ['H20 / A100','批量候选测试、可行范围内的训练或微调、较大模型离线服务','准确卡型、显存、数量和使用配额尚未知；不假定支持任何特定大模型'],
        ['Orin NX','目标导航模型、规划器的部署测量与 HIL','端到端 p50/p95、内存、功率模式、热稳态、降频和网络断连行为'],
      ]}/>
      <Text>优先验证研究机制，之后再决定是否训练科研专用模型。语言模型角色增加也会增加调用成本和相关错误，必须与同预算强单 Agent 比较。</Text>
    </Stack>}

    {tab==='研究设计' && <Stack gap={20}>
      <H2>可正式开题的研究问题</H2>
      <Text weight="semibold">在固定研究预算下，将文献结论的适用条件与候选方法的反证需求连接起来，能否提高无人机探索改进在未见场景和端侧约束下的复验成功率？</Text>
      <Text>新颖性仍待核查。EPOCH 已覆盖证据治理，Co-Scientist 已覆盖假设生成与筛选；拟研究的差异应具体到“条件如何表示、实验如何选、哪些失败被减少”，而不是更换领域或增加几个 Agent 名称。</Text>
      <Table headers={['问题','可实现机制','预注册检验']} rows={[
        ['RQ1 文献条件是否有效？','把传感器、场景、动力学、数据条件结构化；检索时约束可迁移性','相同候选数量与预算，比较条件卡与普通文本 RAG 的假设可实施率、复验通过率'],
        ['RQ2 怎样选择下一实验？','优先选择能区分竞争性解释、覆盖关键未知且成本低的实验','对比随机场景、固定覆盖、失败优先和预算内主动选择；报告每预算的有效改进'],
        ['RQ3 怎样避免错误结论？','冻结环境/评分器；可追溯主张；主动反证；独立重跑','在真实失败与可控混杂案例中统计错误接受与错误拒绝；避免只降低产出换可靠性'],
        ['RQ4 是否能迁移？','验证集选候选后冻结，在未见地图及 Orin NX 上重测','报告场景泛化、性能/延迟权衡及从仿真到 HIL/实机的成功与失败'],
      ]}/>
      <H2>第一项任务：只改探索决策的一个接口</H2>
      <Text>固定定位、地图、局部规划器、控制器与传感器。允许系统修改 frontier 排序、视点选择或失败恢复中的一项。任务包包含：基线代码、失败日志、开发地图、允许修改范围、时间预算、目标指标。初期不要同时改变语义模型、控制器和仿真动力学。</Text>
      <Text>示例假设：加入路径重复代价可减少回访，但也可能使系统过早放弃狭窄入口。竞争性解释：收益来自更低速度、更多观测，或不同控制参数。最小实验应包含环形、死胡同与遮挡入口场景，保持速度、传感器和控制器一致。这是演示假设，未宣称新颖或有效。</Text>
      <H2>双层评测：研究方法和导航方法各自证明</H2>
      <Table headers={['层级','主要指标','解释边界']} rows={[
        ['研究系统','单位总预算获得的复验通过改进数；首次有效改进成本；误报/漏报；人工分钟','分母包含失败、崩溃、工具成本与全部搜索尝试。若没有有效改进，明确报告为 0'],
        ['文献与假设','引用真实性、主张支持率、关键主题覆盖、条件提取准确率、假设可实施率','覆盖针对人工审定集合，不声称全领域绝对召回；多位专家盲评并报告分歧'],
        ['几何探索','固定时限覆盖、覆盖曲线、T90/T95 达成率、路径长度/回访、碰撞与接管','未达 T90 不删除或伪造时间；固定可达区域分母；2D 面积与 3D 体积区分'],
        ['语义/VLN（后续）','任务成功率、SPL 或适合该任务的路径效率、错误目标、指令完成与安全事件','只有目标/路径定义适用时使用 SPL；不与纯几何探索混成一个成功率'],
        ['部署','端到端 p50/p95 延迟、截止期违约、内存/功率、任务收益','模型推理 Hz 不等于闭环决策 Hz；HIL 不等于自由飞行'],
      ]}/>
      <H2>对照、消融与统计</H2>
      <Text>最低对照：固定 baseline；随机/贝叶斯式参数搜索（只作调参对照）；同工具同预算的强单 Agent；最相关的现有科研流水线；你的方法。少量人工研究作为参考时，单独报告人员经验与投入，不能直接混合成本。</Text>
      <Text>消融顺序：去掉条件化证据；去掉主动实验选择；去掉反证；去掉跨轮记忆。先小规模筛选，再扩展必要实验，避免全排列。共同冻结基础模型、检索库、候选次数上限和资源约束，并报告实际消耗。</Text>
      <Text>划分单位是地图/建筑/场景族，不是同一地图中的不同帧；开发集用于搜索、验证集用于选候选，最终盲测集冻结后一次性评估。时间截断文献库只能控制检索泄漏，不能证明预训练中没有见过答案。</Text>
      <Text>建议 pilot：3 个研究子任务，每任务 3 次独立搜索，4 个研究策略；每次搜索暂设最多 10 个候选、每候选 5 个开发场景。至多 1,800 个仿真 episode，实际先跑 10–20 个 episode 标定成本再缩放。另给入选候选留出复验预算。该规模用于估计方差，正式样本量由效应与功效分析决定。</Text>
      <Text>搜索重复与导航随机种子分别记录。按研究任务/场景簇进行配对比较和置信区间估计，不能把大量相关帧当独立样本。终验前锁定主指标、阈值和允许的安全/时延退化；自适应搜索不能反复看最终测试集。</Text>
      <H2>理论研究可以做到哪一层</H2>
      <Text>将实验选择表述为成本约束下的序贯决策：状态是现有证据和不确定性，行动是候选实验，反馈是观测和反例，目标是在预算内减少错误采纳并发现真实改进。可先研究有限候选集合上的选择策略；只有明确可检验的统计假设后再争取界或保证。现阶段不必为了“理论”给复杂系统包装无根据定理。</Text>
      <H2>继续或转向的判据</H2>
      <Text>若只有综述更流畅，收缩到文献质量研究；若只胜过弱提示基线，加强对照；若仅会调参，比较标准搜索；若收益仅在一张地图，不能主张研究能力泛化；若独立复验失败，保留负结果并研究失效机制。候选方法和审查机制均可能无效，这本身是需要实验回答的内容。</Text>
    </Stack>}

    {tab==='执行计划' && <Stack gap={20}>
      <H2>16 周路线与交付门槛</H2>
      <Table headers={['周','阶段','工作','交付 / 转向条件']} rows={weeks}/>
      <Text size="small" tone="secondary">时间为建议，不代表已经实施。约 2 名主要参与者：一人侧重科研 Agent/评价，一人侧重仿真/部署；领域专家参与假设和关键证据复核。单人先完成前 8 周范围。</Text>
      <H2>第一周清单</H2>
      <Text>{done.length} / {firstWeek.length} 项由你手动标记完成；清单状态不代表自动验证。</Text>
      <Stack gap={12}>{firstWeek.map((x,i)=><Row key={x} gap={12} align="start"><Button variant={done.includes(i)?'primary':'secondary'} onClick={()=>setDone(v=>v.includes(i)?v.filter(j=>j!==i):[...v,i])}>{done.includes(i)?'已完成':'待办'}</Button><Text>{x}</Text></Row>)}</Stack>
      <Divider/>
      <H2>学习与产出同步</H2>
      <Text>第一阶段补齐工具调用、结构化输出、RAG、检索评测、Agent 状态机；同时实现论文卡与引用核查。第二阶段学习实验设计、混杂、配对比较、置信区间、序贯选择；同时重做一个公平 A/B。第三阶段学习端侧测量与 sim-to-real 失效分析；同时完成一次冻结候选的 Orin NX 复验。</Text>
      <Text>读论文时统一回答：输入是什么？允许访问什么？实际自主完成哪些环节？失败后如何继续？哪些结论由真实实验支持？比较是否控制模型/预算/工具？代码、数据与评测是否能拿到？最小可借鉴模块是什么？</Text>
      <H2>经费与停止规则</H2>
      <Text>总预算分成模型调用、仿真 CPU/GPU 小时、训练、存储和人工飞行。先做 10–20 个短任务得到中位数和尾部成本，再决定总实验规模。以候选数、GPU 小时和墙钟三种上限终止搜索，失败与重试均计入预算。首轮可暂留约 30% 计算预算给独立复验，这是可调整的规划比例。</Text>
      <H2>从仿真进入实机</H2>
      <Text>依次经过离线日志重放、固定仿真条件的闭环评测、Orin NX 测量/HIL、受控场地实飞。研究 Agent 生成待审查实验包；实飞候选和终止规则由实验人员确认，既有飞控约束与接管机制保留。安排匹配的基线/候选飞行，记录电量、环境、定位条件、接管与异常，避免只展示成功片段。</Text>
      <H2>最终研究包应包括</H2>
      <Text>冻结文献清单、证据卡、任务合同、代码与环境、全部候选/失败、搜索轨迹、原始日志、评分器、统计与绘图脚本、人工介入记录、仿真/HIL/实机区分、可追溯稿件。稿件重点解释研究问题、方法差异、证据和适用边界。</Text>
    </Stack>}
    <Divider/>
    <Text size="small" tone="secondary">所有周数、任务数和预算比例均为建议；本次完成的是公开资料核对和研究方案，未运行科研系统、仿真或实机实验。论文事实与链接见文献地图；研究问题及推荐路线是基于这些材料和用户条件的判断。</Text>
  </Stack>;
}
