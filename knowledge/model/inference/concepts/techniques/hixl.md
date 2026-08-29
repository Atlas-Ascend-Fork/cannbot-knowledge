---
type: Concept
title: HIXL（Huawei Xfer Library 单边零拷贝通信库）
description: HIXL 是基于 SHMEM 全局统一编址的昇腾单边通信库，主要解决超长序列推理将 KV Cache 卸载到 CPU DRAM 后的 Device→Remote Host PUT 与 Remote Host→Device GET。它通过 SDMA 直接访问对端 DRAM，无需对端进程参与或内核态中转，并屏蔽 HCCS、RoCE 等链路差异。vLLM 侧选择 Mooncake 后端且 protocol=ascend 时调用 HIXL；依赖 libcann_hixl.so、libllm_datadist.so，并需 Mooncake 以 USE_ASCEND_DIRECT 构建。HCCS IPC 缓冲区基址要求 2 MiB 对齐，RoCE 无此约束；默认 memfabric 后端不使用 HIXL。本卡只核对 Mooncake 接入封装，HIXL 库本体仍以外部仓为准。
tags:
- task.optimization
- topic.kv_cache
- topic.memory
- topic.model_serving
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_shmem_guide.md
  role: primary
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# HIXL（Huawei Xfer Library 单边零拷贝通信库）

## Summary

**HIXL（Huawei Xfer Library）** 是面向集群场景的昇腾**单边通信库**，提供点对点数据传输能力，并以极简 API 开放给用户。它**基于 SHMEM 机制**（见 [cann-shmem](cann_shmem.md)），针对超长序列 LLM 推理把 KVCache 卸载到 CPU 侧 DRAM 后产生的 **PUT D2rH（Device→Remote Host）/ GET rH2D（Remote Host→Device）** 高频数据交互痛点设计。核心优势三点：

1. **单边零拷贝（One-Sided Zero-Copy）**：基于全局统一编址，发起方经 SDMA 直接读写对端 DRAM，无需对端进程显式交互、无内核态拷贝；
2. **屏蔽硬件差异**：兼容多链路实现跨设备高速互联；
3. **极简 API + 深度适配开源生态**：当前已与 **Mooncake 社区**深度集成，支撑 KVCache 低延迟传输与池化复用。

> 应用场景：上下文窗口突破 128K~百万级 token 后，KVCache 随序列线性增长可达数十 GB，远超单卡 NPU HBM 上限，必须卸载部分/全部 KVCache 到 CPU DRAM。HIXL 解决的是卸载后 NPU↔DRAM 的高性能传输瓶颈。

> 知识归属为 DeepSeek 系列通用：guide 性能测试以 **DeepSeek-R1 KV 大小**为模拟负载、Offload 场景以 **DeepSeek-V3.2** 举例，HIXL 本身是跨模型的传输库（关联 [deepseek-v4](../models/deepseek_v4.md) 与 [deepseek-v3.2-exp](../models/deepseek_v3_2_exp.md)，非纯 V4）。

## HIXL 集成 SHMEM：全局统一编址

HIXL 集成 SHMEM 的核心目标是**跨进程全局统一编址**，依托 SHMEM 内存共享机制使各进程可直接访问彼此 DRAM，无需内核态拷贝。技术流程（guide）：

1. **内存申请**：各进程独立向本地 DRAM 申请私有内存段，获取虚拟地址与本地物理地址；
2. **地址交换**：各进程把自身内存段物理地址信息（基址 / 长度 / 权限）同步到集群内所有进程，构建全局物理地址池；
3. **跨进程页表映射**：各进程把收到的其它进程物理地址映射到自身虚拟地址空间，形成全局统一虚拟—物理映射（"一处编址、全域可达"）；
4. **SDMA 数据访问**：基于全局统一编址，经 SDMA 引擎发起远程内存读写，直接访问任意进程 DRAM，无需进程间显式交互。

开关：`OPTION_ENABLE_USE_FABRIC_MEM`（`1`：开启 SHMEM 模式 / `0`：不开启）。

## 在 cann-recipes-infer 中的落地：Mooncake 后端

本仓 PD 分离的 KV 传输（[online-pd-inference](../frameworks/online_pd_inference.md)）通过 `engine_backend` 选择后端，**`"mooncake"` 即走 HIXL 路径**（默认 `"memfabric"` 为非 HIXL 路径）：

- `MooncakeAscendTransferEngine`（`executor/online/kv_transfer/transfer_engine.py:294`）包装 `mooncake.engine.TransferEngine`，以 `initialize(hostname, "P2PHANDSHAKE", "ascend", device_name)` 4 个严格位置参数初始化（`protocol="ascend"` + metadata mode `P2PHANDSHAKE`）；运行时依赖 **`libcann_hixl.so` + `libllm_datadist.so`（CANN 提供）**，Mooncake 需 `cmake -DUSE_ASCEND_DIRECT=ON` 构建（代码核对 transfer_engine.py:298-299,338-343）。
- **传输**：`batch_register(ptrs, lengths)` 调 `engine.register_memory` 注册内存，`batch_transfer_sync` 调 `engine.batch_transfer_sync_write(decode_session_id, src, dst, lengths)` 把 KV 写到对端 NPU 内存；`session_id = "<ip>:<rpc_port>"` 供对端寻址。
- **2 MiB 对齐约束**：HIXL HCCS IPC 要求注册内存基址 **2 MiB 对齐**——`HIXL_ALIGNMENT = 2 * 1024 * 1024`（`buffer.py:98`、`cache_utils.py:81-108`：:81 注明 "2 MiB aligned HIXL HCCS IPC contract"，:104-108 为 slack 计算 + `align_memory` + `narrow`），KV cache 与 metadata buffer 分配时统一 `align_memory()` over-allocate 后 `narrow` 切到对齐起点（代码核对）。ROCE 路径（`HCCL_INTRA_ROCE_ENABLE=1`）无对齐要求（transfer_engine.py:360-361）。
- **lazy import**：`mooncake` 模块仅在 `engine_backend=="mooncake"` 路径下 lazy import，memfabric-only 部署无需安装（transfer_engine.py:315-323）。

## 性能测试（A3 超节点）

guide 性能数据（A3 超节点，HIXL+SHMEM）：

- 双机单卡 1 对 1，一个 block 数据量模拟 **DeepSeek-R1 KV 大小**：`61×128K + 61×16K = 8784KB`，传输 100 次取平均、剔除首次建链时间；
- 双机 16 卡 1 对 1；
- 双机单卡 1 对 1 大块数据量测试。

> ⚠️ gap（仅图、无数值）：guide 三组性能均以图（`HIXL_perf1/2/_channel.png`）呈现，正文未给数值时延/带宽，本页不臆测具体数字；平台前提为 A3 超节点。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_shmem_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_shmem_guide.md)（HIXL 介绍 / 集成 SHMEM / 全局统一编址 / 性能测试节）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`executor/online/kv_transfer/transfer_engine.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/executor/online/kv_transfer/transfer_engine.py)（`MooncakeAscendTransferEngine`、`protocol="ascend"`+`P2PHANDSHAKE`、`libcann_hixl.so`、`batch_transfer_sync_write`；代码核对）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`executor/online/kv_transfer/buffer.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/executor/online/kv_transfer/buffer.py) + [`executor/core/kv_cache/cache_utils.py:81-108`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/executor/core/kv_cache/cache_utils.py#L81-L108)（`HIXL_ALIGNMENT = 2 MiB`、`align_memory` over-allocate+narrow；代码核对）
- 外部仓（未核对源码）：HIXL 库 [`gitcode.com/cann/hixl`](https://gitcode.com/cann/hixl)
- 引入 / 演进：MR!452（`cffb850` [feat] mooncake + hixl, import, support models lazy import）；diff 区间 `2f82d10..2c45117`

## Links

- [cann-shmem](cann_shmem.md)
- [kvcache-offload](kvcache_offload.md)
- [online-pd-inference](../frameworks/online_pd_inference.md)
- [deepseek-v4](../models/deepseek_v4.md)
- [deepseek-v3.2-exp](../models/deepseek_v3_2_exp.md)

## Notes

- **doc≠code 边界**：HIXL 库本体（`OPTION_ENABLE_USE_FABRIC_MEM`、SDMA 引擎、全局物理地址池构建等）在外部 `cann/hixl` 仓，本仓未开源、未核对源码——本页对外部仓内容以 guide 文档为准。本仓**实际可核对**的是 Mooncake `protocol="ascend"` 后端对 HIXL 的接入封装（`MooncakeAscendTransferEngine` + 2 MiB 对齐契约），上述「在 cann-recipes-infer 中的落地」节均经代码 grep 核实。
- **memfabric vs mooncake**：默认后端 `memfabric`（`AscendTransferEngine` 基于 `memfabric_hybrid`）非 HIXL 路径；mooncake 为 opt-in 的 HIXL 路径。区别详见 [online-pd-inference](../frameworks/online_pd_inference.md)「传输后端」节。

<!-- cannbot:related:start -->
## 相关

- [CANN SHMEM 通信编程模型](cann_shmem.md)（`related`）：焦点卡区分“远端 DRAM 访问走的 **SDMA** 引擎属 ［hixl］(hixl.md) 子节”，候选卡说明“基于全局统一编址，发起方经 SDMA 直接读写对端 DRAM”；两卡共同闭合 SHMEM 编址到 HIXL 远端 DRAM 传输的执行路径。
- [HIXL/HCCS IPC KV 传输须 2 MiB 内存对齐（分配点 over-allocate + narrow）](../../optimizations/experience/rules/hixl_hccs_ipc_2mib_alignment.md)（`related`）：**HIXL（Huawei Xfer Library）** 是面向集群场景的昇腾**单边通信库**，提供点对点数据传输能力，并以极简 API 开放给用户。它**基于 SHMEM 机制**（见 ［cann-shmem］(cann_shmem.md)），针对超长序列 LLM 推理把 KVCache 卸载到 CPU 侧 DRAM 后产生的 **PUT D2rH（Device→Remote Host）/ GET rH2D（Remote Host→Device）** 高频数据交互痛点设计。核心优势三点：；online PD 分离推理走 ［HIXL］(../../../concepts/techniques/hixl.md) / HCCS IPC 的 KV 传输后端（［KVTransferManager］(../../../concepts/frameworks/kv_cache_manager.md)，`mooncake.engine.TransferEngine` protocol=`ascend`，对应 Atlas A3 超节点场景）时：**所有要向传输引擎 `register_memory` 的 NPU HBM 基址必须 2 MiB 对齐**。。HIXL 概念卡定义 KVCache 单边传输，规则卡补齐该传输在 HCCS IPC 注册 NPU HBM 时必须满足的 2 MiB 地址合同。
- [Mooncake（protocol=ascend / HIXL）KV 传输后端在昇腾的三个非显式前置约束](../../runbooks/runtime/mooncake_ascend_hixl_kv_transfer_bringup.md)（`related`）：**HIXL（Huawei Xfer Library）** 是面向集群场景的昇腾**单边通信库**，提供点对点数据传输能力，并以极简 API 开放给用户。它**基于 SHMEM 机制**（见 ［cann-shmem］(cann_shmem.md)），针对超长序列 LLM 推理把 KVCache 卸载到 CPU 侧 DRAM 后产生的 **PUT D2rH（Device→Remote Host）/ GET rH2D（Remote Host→Device）** 高频数据交互痛点设计。核心优势三点：；在昇腾上启用 cann-recipes-infer 的 mooncake（protocol=`ascend` / ［HIXL］(../../concepts/techniques/hixl.md)）KV 传输后端（online ［PD 分离］(../../concepts/frameworks/online_pd_inference.md)推理，`--engine_backend mooncake`）时，有三个非显式前置约束，违反会在 bringup 期直接失败：。HIXL 概念卡给出通信库和 KVCache 传输定位，Runbook 给出 Mooncake Ascend 后端启用该库时的构建、NPU 绑定与初始化前置。
<!-- cannbot:related:end -->
