/* 结构化研究设计，非已运行的实验配置或训练实现。 */
window.RESEARCH_DESIGN = {
  experiments: [
    {id:'E0',stage:'规范',title:'环境与评价口径',claim:'先确保采集、能量、充电和终止语义正确。',control:'小地图枚举/可行路径；事件日志独立重算；禁止靠训练曲线判环境正确。',measure:'守恒、越界、重复采集、碰撞/耗尽定义；记录与4.3实现的差异。',failure:'语义不一致就暂停所有算法比较。',budget:'仅规划：先定位原4.3代码，后确定校验规模。'},
    {id:'E1',stage:'机制',title:'短探测能否预测长期迁移',claim:'Δh是否能识别负迁移，并预测ΔH的方向或排序？',control:'在多个固定检查点克隆候选/控制；相同h步探测后各续训H−h步；确认/长期评价独立于候选生成。',measure:'符号一致率、排序相关、误收/错拒、每个检查点的失败案例；按训练种子/检查点聚类报告。',failure:'短探测与长期收益无关，则停止“可靠长期课程选择”主张；考虑延长探测或改用其他信号。',budget:'单独账本：m个检查点×K个候选×q次训练重复；共享控制须披露相关性。不得并入9M后漏计。'},
    {id:'E2',stage:'主对照',title:'生成器 × 选择器',claim:'选择器有效吗？LLM在同选择器下是否额外有效？',control:'G1固定原任务；G2随机直接；G3 LLM直接；G4随机+迁移准入；G5 LLM+迁移准入；G6 ALP-GMM。',measure:'等全局交互主结果，另报告墙钟/调用费用；采集主指标、覆盖与违规并列。',failure:'G4≈G5则删去LLM必要性；G5仅在额外成本下好则不宣称效率收益。',budget:'讨论值：6组×3独立训练种子×0.5M步=9M训练/探测步；评价与E1另计。'},
    {id:'E3',stage:'机制',title:'任务依赖是否解释收益',claim:'优势是否来自采集—充电—多机协同的耦合，而非仅增加任务多样性？',control:'设置弱/强充电依赖、单机/多机等预定义任务层；每层所有算法同条件；增加难度匹配随机干预。',measure:'方法×任务层的差异、远端覆盖、充电前耗尽、重复采集；检查难度与信息不对称。',failure:'只在简单地图获益或检查器提供额外规划信息，则收缩领域机制解释。',budget:'按任务层乘入主实验预算；不把任务层改变当作完全单因素因果干预。'},
    {id:'E4',stage:'泛化',title:'锁定的场景族与组合外推',claim:'收益能否超出反馈地图和参数组合？',control:'预先锁定ID、单因素OOD、组合OOD；测试不进提示词、不选模型；可变机数先验证骨干支持。',measure:'种子级主差异、最差场景组、负迁移比例与约束退化。',failure:'只开发集改善则否定广泛泛化；仅换随机种子不能称OOD。',budget:'初始讨论40张留出地图；地图数不是独立训练种子数。'},
    {id:'E5',stage:'复验',title:'成本与独立重放',claim:'方法收益足够稳定，且不是预算漏记或版本变化造成的。',control:'冻结环境、模型、生成响应、配置与统计入口；干净环境重跑关键种子；第二骨干后置。',measure:'全部分支交互数、CPU/GPU时间、LLM调用/重试/费用、重放偏差。',failure:'关键结论无法重放或计全成本后消失，就不能进入论文摘要。',budget:'正式8组×5种子×3M=120M仅为单骨干单训练分布上限示例。'}
  ],
  contracts: [
    {name:'TaskSpec',role:'声明任务，限制生成器权限',input:'parent_task_id、地图/PoI/站点、任务期限、能量参数、修改字段与理由',output:'task_hash、schema_version、split、generator_provenance',invariant:'物理模型、奖励与最终指标不可由候选修改；改变范围可追踪。'},
    {name:'FailureSummary',role:'把事件事实与原因假设分开',input:'开发轨迹、检查点ID、任务ID、事件定义版本',output:'观测事件计数、轨迹引用、LLM原因假设、证据支持程度',invariant:'不能把生成的解释当真值；不读取最终测试轨迹。'},
    {name:'CandidateGenerator',role:'随机与LLM共享同一候选接口',input:'允许参数范围、任务族、开发失败摘要、候选预算',output:'TaskSpec列表、原始响应/随机种子、失败/重试成本',invariant:'相同候选权限与必要条件检查；不生成可直接执行代码。'},
    {name:'FeasibilityChecker',role:'格式与物理必要条件检查',input:'TaskSpec及固定模型版本',output:'accept/reject/unknown、理由、必要/充分条件标签',invariant:'unknown不冒充安全证明；几何和能量下界不保证多机时序可行。'},
    {name:'LearnerSnapshot',role:'让成对比较可追溯',input:'模型、优化器、归一化、replay/循环状态、训练计数、RNG状态',output:'不可变snapshot_id及完整恢复清单',invariant:'不能只复制网络权重；训练随机性与评价随机性分别记录。'},
    {name:'ProbeRunner（拟设计）',role:'从同一状态执行候选/控制探测',input:'snapshot_id、候选z、控制课程、h、训练重复q',output:'两个冻结策略、ProbeRecord、所有分支CostRecord',invariant:'双方等训练步；失败与淘汰分支都计成本；当前未实现。'},
    {name:'Evaluator',role:'独立评价与测试隔离',input:'冻结策略、评价清单、seed、mode、固定metric_version',output:'逐回合主得分、约束事件、场景组与不确定性输入',invariant:'confirm样本不能提前参与候选选择；test只用于冻结后报告。'},
    {name:'AdmissionRule',role:'选择、确认、准入或回退',input:'ProbeRecord、阈值tau、delta、候选/轮次数和成本',output:'decision、理由、使用的假设、selected_snapshot_id',invariant:'启发式评分与满足统计前提的确认结果分开；不输出“长期保证”。'},
    {name:'BudgetLedger',role:'累计全成本并防止遗漏',input:'每次训练/探测/控制/失败/评价/API事件',output:'global_env_steps、agent_transitions、eval_steps、CPU/GPU秒、token与费用',invariant:'预算耗尽时停止新增探测；训练和评价分账但均报告总量。'},
    {name:'ExperimentManifest',role:'使论文结论可重放',input:'代码/环境commit、split哈希、完整配置、生成缓存、种子、主比较与统计方案',output:'不可变run_id及产物清单',invariant:'计划、失败和结果分开；没有真实run不得填性能数字。'}
  ]
};
