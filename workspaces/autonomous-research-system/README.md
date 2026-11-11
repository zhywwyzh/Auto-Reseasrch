# 自动研究智能体程序 · ARS v0.1

这里包含可运行的自动研究程序，以及此前的系统设计。程序使用Python标准库、SQLite和本机Codex CLI，不需要安装Python包。操作台是纯HTML，不使用Canvas。

**当前电脑入口：<http://127.0.0.1:18767/workspaces/autonomous-research-system/runtime.html>**。仅适用于浏览器与服务同机；没有公开发布。打开页面不会自动调用模型。

## 直接使用

1. 打开操作台，选择课题，输入明确的研究目标。
2. 选择Codex进行真实研究，或选择模拟执行器验证程序。设置调用总上限和累计控制器运行时间。
3. 点击“创建任务”，再点击“启动”。Codex会使用当前已登录账号的模型配额。
4. 程序自动执行“形成计划 → 只读研究任务 → 批判与反证 → 有界补充 → 阶段报告”，保存任务、决策记忆、引用和调用回执。每次使用新会话，记录显式会话ID。
5. 页面自动刷新任务队列、记忆、事件与报告。可停止、恢复、导入已有历史或补充任务。

当前实现的范围是**只读材料研究、分析和报告**。没有训练/仿真实验作业适配器，不自动修改三个课题源码、不投稿或发布。Codex通过read-only沙箱执行；这不构成跨课题读权限或多租户安全隔离。课题来源范围和摘录匹配由控制器另行核对，目标与科学语义仍需要模型遵守及后续学术审查。

## 命令行

从仓库根目录运行：

```sh
python3 workspaces/autonomous-research-system/ars.py doctor

# 创建本课题的真实Codex任务；创建本身不调用模型。
python3 workspaces/autonomous-research-system/ars.py init \
  --topic TR-002 --name bearing-evidence \
  --goal '只读核对当前方位角研究的核心论点与证据缺口，给出可证伪的补强建议' \
  --backend codex --max-calls 8 --max-seconds 3600

# 后台启动；关闭网页不影响控制器。
python3 workspaces/autonomous-research-system/ars.py start \
  --campaign workspaces/bearing-swarm-review/runs/ars/bearing-evidence
```

以下命令的 `--campaign` 均填写 `init` 返回的目录：

```sh
python3 workspaces/autonomous-research-system/ars.py status --campaign <运行目录>
python3 workspaces/autonomous-research-system/ars.py stop --campaign <运行目录>
python3 workspaces/autonomous-research-system/ars.py resume --campaign <运行目录>
python3 workspaces/autonomous-research-system/ars.py import-history --campaign <运行目录>
python3 workspaces/autonomous-research-system/ars.py report --campaign <运行目录>
```

`run`是前台运行；`start`启动后台看护进程，控制器异常退出后自动尝试恢复，累计最多3次。看护进程仍然遵守停止状态、调用上限和UNKNOWN处理规则。`resume`先核对已有回执和进程，再继续。控制器崩溃后可再次start接管；操作台“继续/恢复”也能核对。电脑重启后需再次执行启动命令，本版未配置开机自动运行研究。

## 记忆与恢复

- 每课题数据放在自己的 `workspaces/<topic>/runs/ars/<name>/`，由既有Git规则忽略。ARS-DEMO数据在本工作区的runs目录。程序不自动提交或推送。
- `state.sqlite3`：目标、约束、任务、操作回执、事件和记忆的权威账本。不要在运行时只复制这个文件而漏掉WAL；备份使用SQLite备份接口或一致性备份工具。
- `operations/`：各次任务的上下文、schema、模型输出和独立监督进程回执。原始JSONL仅留本地，不从隐藏推理中抽取研究记忆。
- `artifacts/report.md`：当前阶段报告，可由账本重建。结构检查不等于科学正确，mock产物明确标注为模拟。
- 历史导入仅处理已登记、匹配本仓库cwd的本课题会话中的可见用户消息，按来源、时间和内容指纹去重。保存为历史候选记忆，不替代当前授权；新增或迁移的会话需更新代码中的显式课题映射。

控制器使用单写者锁、操作ID和任务fence。模型任务与控制器进程分开，中断后读取已完成回执或等待原任务结束。执行状态无法确认时进入NEEDS_RECONCILIATION，保留配额，不无声重复调用。

```sh
# 确认原调用状态并明确需要重试后，手动解决UNKNOWN。
python3 workspaces/autonomous-research-system/ars.py resolve \
  --campaign <运行目录> --operation <操作ID> --action retry

# 或明确放弃该次未知调用。
python3 workspaces/autonomous-research-system/ars.py resolve \
  --campaign <运行目录> --operation <操作ID> --action fail

# 新增预算需显式操作，原消耗不归零。
python3 workspaces/autonomous-research-system/ars.py extend \
  --campaign <运行目录> --calls 4 --seconds 1800
```

调用配额在派发前占用，失败或UNKNOWN也保留。token从可观察的Codex回执累计，阈值阻止下一次派发，单次调用可能越过阈值；没有逐次实付回执时金额保持未知。时间限制是累计控制器运行时间，单任务另有超时，中断停机时间不计入累计值。

## 校验与限制

```sh
python3 -m unittest discover -s workspaces/autonomous-research-system/tests -v
```

测试涵盖完整队列、预算、失败重试、来源不匹配、跨课题/符号链接来源、历史去重、重复控制器、旧fence、控制器强杀与回执恢复、停止恢复，以及可控CLI替身的适配器测试。真实Codex连通性和浏览器结果另记录于runtime-validation.json，替身或模拟测试不是研究效果。

本版保存推断、假设、决策等类型化候选记忆，并执行只读任务、来源定位和逐字摘录核对。外部URL仅标注为尚未由控制器独立核验的引用，批判会话不是独立科学复验。依赖图级联失效、跨主机调度、训练作业管理和24/72小时连续运行验收尚未实现；完整架构中的这些部分仍是后续工作。

## 设计与汇报材料

[系统设计HTML](index.html) · [设计源](design.json) · [历史审计](history-audit.json) · [拟议设计案例](replay-cases.json)。设计页“恢复演练”是预写说明，上方操作台连接实际程序。

16:9汇报图在figures/system-overview.svg与.png。运行 `python3 build.py` 同步生成设计HTML、SVG和高清PNG；构建图像需要Node.js、Playwright与Chromium，智能体程序本身不依赖它们。设计图描述完整目标架构，不表示所有模块已在v0.1实现。

HTML与操作台由用户级autoresearch-system-docs.service提供；服务未启动时也可运行 `python3 serve.py`。只绑定127.0.0.1，POST操作检查来源和令牌，不开放原始论文、运行目录或Git配置的静态下载。

Codex调用接口依据[OpenAI官方非交互模式文档](https://learn.chatgpt.com/docs/non-interactive-mode)，本机版本与登录状态由doctor实查。
