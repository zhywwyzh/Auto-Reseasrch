# AutoResearch-UAV · 自动研究系统

本仓库保存公共规则和可复用的自动研究系统。具体研究任务的源码、材料、配置、实验、稿件和阅读页面仅保存在本地，不上传Git。

整个项目只使用这一套主仓库 Git。公共依赖以保留许可证和来源清单的普通文件管理；
任务、实验、稿件及执行副本使用本地忽略目录，不创建子仓库、子模块或额外 Git 工作树。
`python3 scripts/check_git_layout.py` 可核对这一目录结构约定。

## 系统入口

- [系统源码与使用说明](workspaces/autonomous-research-system/README.md)
- [操作台](workspaces/autonomous-research-system/runtime.html)
- [公共约束](AGENTS.md)
- [通用论文预审量表](docs/research/ai-paper-review/aas-review-profile.json)
- [共享排版模板](templates/acta-automatica-sinica/README.md)
- [外部公共源码与版本清单](external/README.md)

## 本地初始化

```sh
python3 workspaces/autonomous-research-system/init_local.py
cd workspaces/autonomous-research-system/ui
npm ci
npm run build
cd ../../..
python3 workspaces/autonomous-research-system/serve.py --port 18767
```

初始化只补充不存在的空白本地登记文件，不覆盖任务或服务器设置，不启动模型或研究作业。浏览器与服务同机时，可访问 `http://127.0.0.1:18767/`。本地任务按忽略的 `workspaces/topics.json` 登记，任务目录不随克隆分发。

## 提交边界

`.gitignore` 使用默认拒绝的允许清单。公共系统源码、测试、界面、文档和必要的共享工具/模板可以跟踪；任务目录、论文、资料、任务登记、真实服务器配置和运行记录均忽略。

`external/` 中经审查的公共源码作为普通文件由本仓库管理，不使用子模块或嵌套仓库。其逐文件允许清单见 `external/.gitignore`，上游地址、提交和源码校验和见 `external/sources.lock.json`；未列入清单的数据、附件和新增文件继续仅留本地。

```sh
python3 scripts/check_git_scope.py
python3 scripts/check_git_history.py
```

检查通过后仍应按明确路径暂存和审阅。不使用强制添加绕过规则；修改索引不删除本地文件，也不自动清除历史提交中的旧材料。

通用源码、测试和界面没有预置的真实研究内容。课题编号、会话映射、服务器、授权、专用科学验证器与旧执行端兼容实现只在本地登记或忽略目录中保存；新克隆获得空白研究工作台。提交检查读取索引中的实际文件，推送检查覆盖提交的全部可达历史，防止旧研究提交随新分支再次上传。
