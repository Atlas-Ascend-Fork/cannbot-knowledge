---
type: Guide
title: 启用 KV-Pool Remote H2D 直传前的 Ascend 前置校验（2MiB HugeTLB + worker H2D 参数 + NPU/RoCE 环境）
description: 启用 KV-Pool（Yuanrong Datasystem）Remote Host-to-Device 直传前的 Ascend 前置校验配方：跨节点把 KV cache offload 到远端 NPU device 时，开直传开关（DS_ENABLE_REMOTE_H2D=1）前须逐项核对四件事——预留足量 2MiB HugeTLB 大页（40 GiB 共享内存对应 20480 个 2MiB 大页）；worker 用 dscli start -w 带 --remote_h2d_device_ids、--enable_huge_tlb true、--arena_per_tenant 1、--enable_fallocate false、--shared_memory_size_mb 40960、--enable_worker_worker_batch_get=true 启动；容器挂载 NPU 驱动/固件/CANN toolkit、npu-smi、hccn_tool、/etc/hccn.conf、/dev/davinci*；版本不匹配时从源码构建后端。用 /proc/meminfo 与 NUMA node hugepages 查大页、npu-smi info/-t topo 查 NPU 与拓扑、hccn_tool 查光模块/RoCE link UP/IP 与 ping 远端 NPU 可达性做 correctness 验证。任一不达标则保持 DS_ENABLE_REMOTE_H2D=0 回退默认 Datasystem 传输路径（rollback）。参考实现 vLLM-Ascend kv_pool.md AscendStoreConnector backend yuanrong；20480/40960 为文档推荐值非实测。涉及 kvcache-offload、RoCE/RDMA、HugeTLB、NPU device 直传。
tags:
- task.debugging
- topic.kv_cache
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/9203
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- a2
---

# 启用 KV-Pool Remote H2D 直传前的 Ascend 前置校验（2MiB HugeTLB + worker H2D 参数 + NPU/RoCE 环境）

## 适用场景

把 KV cache offload 到一个分布式内存后端（此处为 Yuanrong Datasystem KV-Pool），并希望**跨节点把 KV 直接搬到远端 NPU device**。这条「远端主机到设备直传」（Remote Host-to-Device，Remote H2D）按其语义推断，相较默认传输路径通常需经远端 Host 内存中转，可省掉这一跳中转拷贝；但它对底层环境有硬要求：设备侧要有足量物理连续的大页可 pin、worker 要按 H2D 语义启动、且节点间要真的走通 RoCE/RDMA 网络。

**这条经验回答的问题**：我要在 NPU 集群上打开 KV-Pool 的 Remote H2D 加速开关，开之前该核对哪些前置条件，核不过时怎么办。

**前提 / 何时适用**：
- KV cache offload 后端是可做远端直传的分布式内存系统（本参考实现为 Yuanrong Datasystem，vLLM-Ascend 里以 `AscendStoreConnector` + `backend: "yuanrong"` 接入）。
- 目标是打开 Remote H2D 直传（省掉一次远端 Host 中转），而非仅用默认传输路径。
- 集群为多机、跨节点搬 KV，需要 RoCE/RDMA 物理链路联通。

**何时不适用 / 直接关掉**：下述任一前置校验不通过（大页不足、RoCE link 非 UP、光模块/ping 不通、驱动或固件对 worker 不可见），就**不要**打开 Remote H2D，保持直传开关为关、走后端默认传输路径。默认路径功能可用，只是少了这条设备直传的加速。

> 为什么先校验再开：Remote H2D 直传要求把主机侧大块内存 pin 成物理连续的 2MiB HugeTLB 大页供 RDMA 零拷贝使用，并要求本地 NPU 能经 RoCE 直达远端 NPU 的 device 内存。这两条任一不满足，直传会在运行时失败或不可用；而这些条件在部署阶段就可用系统命令确定性地验证，因此把它当作一道开关前的准入门，比开完再排障便宜得多。

## 问题信号

- 打开 Remote H2D 直传开关后，KV-Pool 远端传输不可用或运行时报错。
- 大页未预留 / 预留不足：进程无法 pin 到所需的 2MiB HugeTLB 内存。
- 跨节点 KV 搬运失败，底层是 RoCE 物理链路非 UP、光模块异常、或本地 NPU 到远端 NPU IP 不可达。

## 前置条件 / 做什么

开直传客户端开关**之前**，逐项落实以下四件事：

### 1. 预留 2MiB HugeTLB 大页

Remote H2D 要把共享内存 pin 成物理连续的 2MiB 大页给 RDMA 用。按共享内存总量换算大页数量：**40 GiB 共享内存至少预留 20480 个 2MiB 大页**（40960 MiB ÷ 2 MiB = 20480）。大页需在启 worker 前预留好；预留后用 per-NUMA-node hugepages 命令确认分布落在 worker 会用到的 node 上（见下方 correctness 验证）。

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
- **rollback**：把 Remote H2D 直传开关关闭，回退到后端默认传输路径——功能仍可用，只是没有这条设备直传加速。在此参考实现中，直传开关由环境变量 `DS_ENABLE_REMOTE_H2D` 控制（`1` 开、`0` 关），透传给后端的 `HeteroClient.enable_remote_h2d`；rollback 即置 `DS_ENABLE_REMOTE_H2D=0`。

## 参考实现及其约束

- **参考实现**：vLLM-Ascend 的 KV-Pool 特性文档 `docs/source/user_guide/feature_guide/kv_pool.md`，以 Yuanrong Datasystem（`openyuanrong-datasystem`）作 KV offload 后端，通过 `AscendStoreConnector`（`backend: "yuanrong"`）接入；Remote H2D 由环境变量 `DS_ENABLE_REMOTE_H2D` 门控。Yuanrong Datasystem 源码构建入口见 <https://atomgit.com/openeuler/yuanrong-datasystem>。
- **约束（属该参考实现，非技术本身）**：
  - `20480` 个 2MiB 大页、`40960` MiB 共享内存是该文档自报的推荐配比，随共享内存大小按 `大页数 = 共享内存MiB ÷ 2` 线性换算，并非硬性绝对值。
  - `dscli`、`--remote_h2d_device_ids`、`--enable_worker_worker_batch_get`、`DS_ENABLE_REMOTE_H2D` 均为 Yuanrong Datasystem 专有的命令与开关名；换其他分布式内存后端时，思想（大页预留 + worker 直传参数 + NPU/RoCE 环境核验 + 失败即回退默认路径）可迁移，具体开关名不可照抄。
  - 该配方以文档披露的部署指引为依据，`20480`/`40960` 数值未经独立复测，属推荐值而非实测最优值。

## 关联

- 卸载技术本身：[kvcache-offload](../../../concepts/techniques/kvcache_offload.md) —— 本页是其「跨节点分布式后端 + 远端设备直传」的部署硬化配方。
- KV 缓存生命周期与后端接入：[kv-cache-manager](../../../concepts/frameworks/kv_cache_manager.md)。

## Evidence

- claim：[vllm-ascend-yuanrong-kv-pool-启用-remote-h2d-的前置-预留-2mib-huget](https://github.com/vllm-project/vllm-ascend/pull/9203)
- 参考源（合并态）：`vllm-project/vllm-ascend@62baa5932a9b5a909d7a506c5ba32e4abdcd3733` 的 `docs/source/user_guide/feature_guide/kv_pool.md`「Remote H2D Requirements」节。
- evidence tier：文档披露（仓内部署指引，非独立复测的 benchmark）；`20480` 大页 / `40960` MiB 共享内存为仓自报推荐值。

<!-- cannbot:related:start -->
## 相关

- [KVCache Offload](../../../concepts/techniques/kvcache_offload.md)（`related`）：把 KV cache offload 到一个分布式内存后端（此处为 Yuanrong Datasystem KV-Pool），并希望**跨节点把 KV 直接搬到远端 NPU device**。；**KVCache Offload** 泛指把部分或全部 KV Cache 从设备 HBM 卸载到 Host 内存（或延后到异步 stream 上执行），以换取显存容量或计算/通信重叠。。前者把 KVCache Offload 的卸载目标扩展为分布式内存后端并补充远端 NPU 搬运前置条件，直接细化后者的卸载机制。
<!-- cannbot:related:end -->
