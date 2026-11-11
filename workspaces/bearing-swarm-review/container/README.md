# TR-002 独立数值容器

本目录只管理 TR-002 的环境与环境验收，不实现无人机算法，不运行正式 benchmark。
镜像不包含原始论文、整个仓库、其他课题或宿主机凭据。最新实际验证以 `validation.json` 为准；缺少该文件时不能认定已通过。

## 环境与隔离

- Linux/amd64；容器内 Debian Bookworm，不改变宿主 Ubuntu。
- Python 3.10 与 Julia 1.11.3 基础镜像固定到摘要。
- Python 科学包固定版本与轮子哈希；Julia 使用 `Project.toml` / `Manifest.toml` 锁定依赖。
- 运行时普通用户、只读根文件系统、关闭网络、无GPU、无端口映射、无 Docker socket、无其他课题挂载。
- 唯一宿主写入挂载为本课题新建的 `runs/container-smoke-<时间>-<随机后缀>/`；临时文件写入512MiB的 `/tmp` tmpfs。
- 2个CPU配额、4GiB内存、0 Swap、256 PID；Julia与BLAS各1线程。CPU配额不是独占物理核，内存上限不是资源预留，容器仍共享宿主内核和资源竞争。

## 重建与验收

从仓库根目录执行：

```sh
python3 workspaces/bearing-swarm-review/container/build_image.py
python3 workspaces/bearing-swarm-review/container/run_smoke.py
```

构建需要网络下载依赖，验收运行关闭网络。脚本默认构建 `tr002-numerics:locked`，运行时先解析成本机不可变镜像ID，记录实际ID后使用它启动。

构建脚本针对本机 Docker 28，使用仍支持逐个构建步骤CPU/内存限制的 legacy builder；Docker会显示弃用提示。未来移除该后端时，需要迁移到带资源上限的专用 BuildKit builder，不能直接忽略限制。当前没有修改宿主 Docker daemon 配置。

默认构建拒绝缺失锁文件。Dockerfile中的 `RESOLVE_DEPENDENCIES=1` 仅供明确的依赖维护/首次引导；不是正式复现命令。重新解析依赖后须重新导出带哈希的 Python 锁文件和 Julia Manifest，重建锁定镜像并重新验收。基础镜像自带的pip等包由基础摘要固定，完整已装包版本记录在验收中。

## 验收内容及边界

1. 科学包导入、依赖一致性、实际cgroup限制、普通用户和只读根文件系统。
2. Python HDF5读写、SciPy对称特征值、无显示器绘图。
3. Python→Julia矩阵/向量布局与数值结果往返。
4. JuMP/SCS求解一个2×2已知答案SDP，独立重算目标、对角可行性和最小特征值。

该小SDP是环境验收，不是原论文复现、严格浮点认证、正式研究实验或实时性证明。输出运行时长包含启动/JIT，不能拿来当算法延迟。

结果包含 `environment-smoke.json`、`julia-smoke.json`、`host-receipt.json` 和日志。`runs/`由Git忽略；整理后的验收摘要可写入本目录 `validation.json`。运行结束只删除本次创建的容器，保留镜像和结果；不清理其他课题的镜像、容器或文件。

正式研究阶段仍需完成 bearing 目标适配、独立证书检查器、数据生成器与实验协议冻结。GPU、ROS/Gazebo、实机均不在当前容器验收范围。
