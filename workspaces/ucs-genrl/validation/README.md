# TR-001 本机最小运行验证

2026-11-11 用户授权先做更小规模验证，再考虑服务器实际训练。本目录只实现有界运行验收，不启动完整 R1-P / R1-S、课程优化、B-CF、服务器任务或模型 API。

阅读入口：[最小验证报告](../local-validation.html)。机器可读结果为 `result-summary.json`；原始日志、检查点和运行 manifest 保存在本课题被 Git 忽略的 `../runs/cpu-smoke-*`。报告不是论文效果数据。

## 验证对象与差异

- 只读导入 MIT 仓库 `BIT-MCS/DRL-MTVCS` 的固定提交 `780e0b41d3fff54c8fa5ea0335979b3f1ec1f225`，保留源文件及其许可证，不复制、改写原环境或原学习器。
- 使用原 `data_collection_1.Env`、`ResNetLSTMAgent`、`build_learner`、V-trace、归一化、pixel control 和 RMSProp。默认学习率时域保留 75M，不能与拟定正式 3M 协议混同。
- 同步单环境采样、batch=1、unroll=20；不执行原异步队列主循环或 `batcher.so`。动作从原 logits 对应的分类分布用 NumPy RNG 采样；不声称 TensorFlow 原随机算子的恢复已通过。
- 原候选配置为 16×16、初始能量30等，与学位论文差异仍保留。本轮是兼容性与链路测试，不是 §4.2 / §4.3 的数值复现。
- 每次最多160次真实环境转移（80随机检查＋20环境恢复重放＋60策略采样）；5次更新消耗100个样本，含40个固定批次重复消耗。消耗与生成分列，不能相加冒充环境交互总量。
- Python环境及其随机流验证磁盘恢复；学习器154个全局变量验证新会话恢复和固定批次下一更新重放。二者不是完整异步训练断点恢复证据。

## 重跑

需要本机 Docker 和本地候选源码；正式服务器运行另行授权。主机不安装旧版 TensorFlow。

```sh
docker build -t tr001-cpu-smoke:v1 workspaces/ucs-genrl/validation
python3 workspaces/ucs-genrl/validation/launch.py
python3 workspaces/ucs-genrl/validation/launch.py --execute
```

第二条仅显示合同；第三条才执行。可通过 `--source /path/to/DRL-MTVCS` 指定已核验的同一提交。运行无网络、无GPU、只读根目录和源码，仅结果目录可写；限2核、3GiB内存、不增加交换空间、300秒。不会停止或清理其他项目任务。

基础镜像按digest固定，Python依赖用 `environment.freeze.txt` 约束；`requirements.in`列直接依赖。冻结版本不等于wheel内容校验，镜像ID及实际源文件哈希另存每次manifest。旧镜像只作隔离兼容验证，不能直接当成正式GPU环境。

最初两次镜像构建分别因 Gym/TFP 的 cloudpickle 版本冲突、dm-tree缺少预编译兼容版本而失败，均未开始环境交互。调整Gym为0.12.5、dm-tree为0.1.5并固定间接依赖后构建成功。没有修改原算法来绕过依赖错误。

## 迁移前仍需处理

1. 原始定义对齐：η、奖励、配置与评价聚合口径。
2. 记录零分母下指标未定义，不擅自把它补成0或改写奖励。
3. 环境生成数、学习器接纳数、更新次数单独记账；原global_step每次多计1还影响学习率，正式修正要固定版本。
4. 在服务器验证GPU算子、正式batch32、actor并发、完整状态恢复及吞吐；CPU小批次耗时不能外推。
5. 经用户确认再启动真实课程对照、跨种子诊断与正式训练。

运行方式依据：[TensorFlow官方Docker说明](https://www.tensorflow.org/install/docker)。原代码来源：[BIT-MCS/DRL-MTVCS](https://github.com/BIT-MCS/DRL-MTVCS)。
