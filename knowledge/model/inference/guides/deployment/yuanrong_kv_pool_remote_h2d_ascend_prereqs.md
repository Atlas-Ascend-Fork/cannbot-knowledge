---
type: Guide
title: 启用 KV-Pool Remote H2D 直传前的 Ascend 前置校验（2MiB HugeTLB + worker H2D 参数 + NPU/RoCE 环境）
description: 依据固定部署文档检查 Yuanrong Remote H2D 的主机 HugeTLB、worker 参数和 NPU/RoCE 环境；关闭开关后仍需验证默认传输，不推导零拷贝次数或设备大页布局。
tags:
- task.debugging
- topic.kv_cache
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/9203
  role: evidence
- resource: https://github.com/vllm-project/vllm-ascend/blob/62baa5932a9b5a909d7a506c5ba32e4abdcd3733/docs/source/user_guide/feature_guide/kv_pool.md
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-10-21T02:05:13Z'
platforms:
- a2
---

# 启用 KV-Pool Remote H2D 直传前的 Ascend 前置校验（2MiB HugeTLB + worker H2D 参数 + NPU/RoCE 环境）

## 适用场景

把 KV cache offload 到一个分布式内存后端（此处为 Yuanrong Datasystem KV-Pool），并希望**跨节点把 KV 直接搬到远端 NPU device**。所引文档列出 Remote Host-to-Device（Remote H2D）的启用条件，未提供默认路径与该路径的拷贝次数对照；其部署前提是：主机侧要预留足量 2MiB HugeTLB 大页、worker 要按 H2D 语义启动、且节点间要真的走通 RoCE/RDMA 网络。

**这条经验回答的问题**：我要在 NPU 集群上打开 KV-Pool 的 Remote H2D 加速开关，开之前该核对哪些前置条件，核不过时怎么办。

**前提 / 何时适用**：
- KV cache offload 后端是可做远端直传的分布式内存系统（本参考实现为 Yuanrong Datasystem，vLLM-Ascend 里以 `AscendStoreConnector` + `backend: "yuanrong"` 接入）。
- 目标是打开 Remote H2D 传输路径，而非仅用默认传输路径。
- 集群为多机、跨节点搬 KV，需要 RoCE/RDMA 物理链路联通。

**何时不适用 / 直接关掉**：下述任一前置校验不通过（大页不足、RoCE link 非 UP、光模块/ping 不通、驱动或固件对 worker 不可见），就**不要**打开 Remote H2D，保持直传开关为关、走后端默认传输路径。默认路径仍需单独完成连通性和功能验收。

> 以下校验来自固定版本部署文档；这些前提不代替实际传输验证，也不单凭 Remote H2D 名称推导零拷贝次数或物理内存布局。

## 问题信号

- 打开 Remote H2D 直传开关后，KV-Pool 远端传输不可用或运行时报错。
- 大页未预留 / 预留不足：进程无法 pin 到所需的 2MiB HugeTLB 内存。
- 跨节点 KV 搬运失败，底层是 RoCE 物理链路非 UP、光模块异常、或本地 NPU 到远端 NPU IP 不可达。

## 前置条件 / 做什么

开直传客户端开关**之前**，逐项落实以下四件事：

### 1. 预留 2MiB HugeTLB 大页

来源要求的是主机共享内存使用 2MiB HugeTLB 大页；它不要求整块 40GiB 物理连续，也不表示这些是 NPU 设备内存页。按共享内存总量换算大页数量：**40 GiB 共享内存至少预留 20480 个 2MiB 大页**（40960 MiB ÷ 2 MiB = 20480）。大页需在启 worker 前预留好；预留后用 per-NUMA-node hugepages 命令确认分布落在 worker 会用到的 node 上（见下方 correctness 验证）。

### 2. worker 启动带 Remote H2D 参数

worker 进程（`dscli start -w`）必须以 H2D 语义启动：显式给出用于直传的 NPU device id、开启大页、每租户单 arena、关闭 fallocate、并放开 worker 间批量 get。示例（8 卡节点）：

```bash
dscli start -w \
  --worker_address "${WORKER_IP}:31501" \
  --etcd_address "${ETCD_IP}:2379" \
  --shared_memory_size_mb 40960 \
  --arena_per_tenant 1 \
  --enable_huge_tlb true \
  --enable_fallocate false \
  --remote_h2d_device_ids "0,1,2,3,4,5,6,7" \
  --enable_worker_worker_batch_get=true
```

关键参数含义：
- `--remote_h2d_device_ids`：参与 Remote H2D 直传的本地 NPU device id，建议用节点上多个可用 NPU（8 卡节点即 `"0,1,2,3,4,5,6,7"`）。
- `--enable_huge_tlb true`：让 worker 使用上一步预留的 2MiB HugeTLB 大页。
- `--arena_per_tenant 1`、`--enable_fallocate false`：内存 arena 与分配策略按直传要求配置。
- `--shared_memory_size_mb 40960`：共享内存 40 GiB，与「预留 20480 个 2MiB 大页」相互对应。
- `--enable_worker_worker_batch_get=true`：放开 worker 间批量 get 路径。

### 3. 容器内挂载 Ascend 依赖，使 NPU 栈对 worker 可见

Remote H2D 直接操作 NPU device，worker 进程必须能看到完整 NPU 软硬件栈。容器需挂载：
- NPU 驱动、固件、CANN toolkit（版本须与运行环境匹配）；
- `npu-smi`、`hccn_tool` 两个诊断工具；
- `/etc/hccn.conf`、`/etc/ascend_install.info`；
- 所需的 `/dev/davinci*` 设备节点。

### 4. 版本不匹配时从源码构建后端

若预编译的后端包与环境里的 CANN 版本或 Ascend 驱动版本不匹配，须在同一镜像内**从源码构建** Yuanrong Datasystem（参考实现见 Evidence），避免 ABI/版本漂移导致的直传失败。

## correctness 验证（开客户端开关前逐项校验）

四件事落实后，用以下命令逐项确认环境真的具备直传条件；任一不达标就回到 rollback：

```bash
# 2MiB HugeTLB 大页总量 / 空闲
grep -E "HugePages_Total|HugePages_Free|Hugepagesize" /proc/meminfo

# 各 NUMA node 上的 2MiB 大页（确认预留分布在会用到的 node 上）
for node in /sys/devices/system/node/node*/hugepages/hugepages-2048kB; do
  echo "$node total=$(cat "$node/nr_hugepages") free=$(cat "$node/free_hugepages")"
done

# NPU 与驱动对 worker 可见
npu-smi info

# NPU 拓扑可见
npu-smi info -t topo

# 选定本地 NPU 的光模块检测
hccn_tool -i <local_npu_id> -optical -g

# RoCE 物理链路状态（期望 UP）
for i in {0..7}; do hccn_tool -i $i -link -g; done

# 选定 NPU 的 IP 及到远端 NPU 的可达性
hccn_tool -i <local_npu_id> -ip -g
hccn_tool -i <local_npu_id> -ping -g address <remote_npu_ip>
```

判定：`HugePages_Free` 覆盖预留目标、每块参与 NPU 的 RoCE link 为 UP、光模块正常、本地 NPU 能 ping 通远端 NPU IP。全绿才允许打开 Remote H2D。

## 风险 / rollback

- **风险**：校验失败（HugeTLB 不足、RoCE link 非 UP、光模块/ping 不通、驱动对 worker 不可见等）仍强行打开 Remote H2D 直传，会导致直传不可用或运行时失败。
- **rollback**：把 Remote H2D 直传开关关闭，回退到后端默认传输路径，并重新验证传输与推理功能。在此参考实现中，直传开关由环境变量 `DS_ENABLE_REMOTE_H2D` 控制（`1` 开、`0` 关），透传给后端的 `HeteroClient.enable_remote_h2d`；rollback 即置 `DS_ENABLE_REMOTE_H2D=0`。

## 参考实现及其约束

- **参考实现**：vLLM-Ascend 的 KV-Pool 特性文档 `docs/source/user_guide/feature_guide/kv_pool.md`，以 Yuanrong Datasystem（`openyuanrong-datasystem`）作 KV offload 后端，通过 `AscendStoreConnector`（`backend: "yuanrong"`）接入；Remote H2D 由环境变量 `DS_ENABLE_REMOTE_H2D` 门控。Yuanrong Datasystem 源码构建入口见 <https://atomgit.com/openeuler/yuanrong-datasystem>。
- **约束（属该参考实现，非技术本身）**：
  - `20480` 个 2MiB 大页、`40960` MiB 共享内存是该文档自报的推荐配比，随共享内存大小按 `大页数 = 共享内存MiB ÷ 2` 线性换算，并非硬性绝对值。
  - `dscli`、`--remote_h2d_device_ids`、`--enable_worker_worker_batch_get`、`DS_ENABLE_REMOTE_H2D` 均为 Yuanrong Datasystem 专有的命令与开关名；换其他分布式内存后端时，思想（大页预留 + worker 直传参数 + NPU/RoCE 环境核验 + 失败即回退默认路径）可迁移，具体开关名不可照抄。
  - 该配方以文档披露的部署指引为依据，`20480`/`40960` 数值未经独立复测，属推荐值而非实测最优值。

## 关联

- 卸载技术本身：[kvcache-offload](../../concepts/techniques/kvcache_offload.md) —— 本页是其「跨节点分布式后端 + 远端设备直传」的部署硬化配方。
- KV 缓存生命周期与后端接入：[kv-cache-manager](../../concepts/frameworks/kv_cache_manager.md)。

## Evidence

- claim：[vllm-ascend-yuanrong-kv-pool-启用-remote-h2d-的前置-预留-2mib-huget](https://github.com/vllm-project/vllm-ascend/pull/9203)
- 参考源（合并态）：`vllm-project/vllm-ascend@62baa5932a9b5a909d7a506c5ba32e4abdcd3733` 的 `docs/source/user_guide/feature_guide/kv_pool.md`「Remote H2D Requirements」节。
- evidence tier：文档披露（仓内部署指引，非独立复测的 benchmark）；`20480` 大页 / `40960` MiB 共享内存为仓自报推荐值。