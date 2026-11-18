# AI 辅助论文写作工具源码

`upstream/` 中的 8 个公共工具以普通文件由主仓库管理，不保留独立 Git 仓库。各项目的许可证与说明保持原有归属，统一来源、固定提交与文件校验和见 [sources.lock.json](../sources.lock.json)。

包括 Academic Humanizer、Humanizer Chinese、Vale、Textidote、write-good、HalluCiteChecker、PaperQA 和 DeepReviewer-v2。工具建议不能替代对科学证据、数字、公式和引用的人工核对。

```sh
python3 external/ai-paper-tools/fetch_sources.py
```

从仓库根目录运行。此兼容入口现在只验证已纳入主仓库的源码，不克隆上游、不安装依赖、不运行工具、不建立索引、不调用模型。新克隆不需要额外获取源码。

任务稿件、工具执行结果、缓存、数据、模型权重和费用均仅保存在各任务本地忽略目录。完整边界见 [外部源码说明](../README.md)。
