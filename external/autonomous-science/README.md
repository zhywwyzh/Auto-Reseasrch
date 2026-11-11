# 自主科研公开代码与资料

这些目录是上游 Git 子模块，主仓库保存确切提交指针，不将上游源码重新打包或改写成自有实现。

阅读入口：[中文译读、原件与开放范围](../../docs/research/autonomous-science-2026-11-10/library/index.html)。
完整提交、日期、许可证文件校验和、抓取来源和稀疏检出范围见 [repositories.json](../../docs/research/autonomous-science-2026-11-10/library/repositories.json)。

本轮仅拉取资料，没有安装依赖、执行上游脚本、初始化上游嵌套子模块或运行科研实验。LFS 数据载荷未获取；它们的指针不是可运行数据。

恢复当前主仓库锁定的提交：

```sh
GIT_LFS_SKIP_SMUDGE=1 git submodule update --init --depth 1 -- external/autonomous-science
python3 scripts/fetch_autonomous_science_repos.py
```

第二条命令检查现有来源、恢复代码为主的稀疏检出，并更新核验记录；不自动切换到上游最新提交。有未提交修改的子模块会保留其工作区，不强行稀疏检出。首次恢复可能先取回上游附件，Git 对象库也可能保留已传输对象；稀疏检出限制的是工作区，不能被描述成从未下载这些对象。

开放范围有区别：

- AI Scientist-v3、AutoDNA、AlphaEvolve 最小实现，以及心理学工作的公开产物仓库有 Apache-2.0 文件。
- OmniScientist、MOMbot 与 PaperBenchX 有 MIT 文件；DISCERN 作者代码为 MIT，数据和外部资源适用混合条款。
- AI Scientist-v2 使用带用途限制的自定义 The AI Scientist Source Code License。
- autoresearch 在 README 声明 MIT，当前未发现单独 LICENSE 文件。
- A-Lab GPSS 当前未发现根目录覆盖全仓的许可证，不擅自推定授权。
- 心理学仓库提供公开产物，不能据此认定论文中的专有研究工作流完整开源。未拉取 Co-Scientist、Kosmos 或 ScientistTwo 的第三方复刻来替代官方系统。

保留上游许可证。代码许可不自动覆盖论文、数据、权重、实验仪器或商业科学软件。
