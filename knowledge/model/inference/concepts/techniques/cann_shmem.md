---
type: Concept
title: CANN SHMEM 通信编程模型
description: CANN SHMEM 是面向昇腾多设备的共享地址空间通信模型，以 OpenSHMEM 风格 Host/Device 接口支持跨设备访存和通算融合。它提供 NPU HBM 与 CPU DDR 混合编址、对称内存及 put/get/signal/wait/barrier 等原语；通信域各卡共享虚拟地址，单 die 对称区总量不超过 1 GiB，状态区紧随数据区。基础层使用 MTE/xDMA 处理 D2D/D2H，HIXL 则通过 SDMA 访问远端 DRAM，二者不可混为同一路径。典型用途包括 KV Cache Offload、MoE Dispatch/Combine 和 HIXL 单边通信，可由原生 API、pyPTO 或 TileLang 接入。运行时实现位于外部 cann/shmem 仓，本卡 API 以固定 guide 为依据。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.kv_cache
- topic.parallelism
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_shmem_guide.md
  role: primary
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-08-27T12:23:11Z'
platforms:
- a3
---

# CANN SHMEM 通信编程模型

## Summary

**CANN SHMEM** 是 CANN 开源社区对标 **OpenSHMEM** 提供的共享地址空间并行编程接口，基于 CANN 的全局内存交互能力构建。它封装 Host 侧与 Device 侧接口，为模型/算子开发者提供跨设备内存通信能力，简化卡间数据同步与**通算融合（通信-计算融合）算子**的开发。其设计价值：

- **混合编址**：支持 NPU HBM 与 CPU DDR 混合编址，把 Host 内存映射成可直接当 Device tensor 使用的内存，优化 KVCache Offload 吞吐（见 [kvcache-offload](kvcache_offload.md)）；
- **对称内存（symmetric memory）**：通信域内各卡共享一个全局虚拟地址空间，卡间内存按固定步距编址，put/get 直接寻址对端；
- **集成高性能通信引擎**：SHMEM 基础层集成 **MTE、xDMA** 等引擎，支持 **D2D / D2H** 通信，降低卡间通信延迟（注：远端 DRAM 访问走的 **SDMA** 引擎属 [hixl](hixl.md) 子节，非 SHMEM 基础层 D2D/D2H 路径，两者不混同）；
- **多框架接入**：除原生 SHMEM API 外，还接入 **TileLang-shmem** 与 **pyPTO-shmem** 编程框架，提升通算融合算子的开发易用性。

> 跨模型基础通信技术：shmem_guide 以 **DeepSeek-V3.2（KVOffload）** 与 **DeepSeek-V4** 为典型场景举例，但 SHMEM 是 DeepSeek 系列通用的底层通信能力，并非 V4 独有，属 DeepSeek 系列通用通信基础。

> ⚠️ gap（算子库为外部仓）：API/符号取自 **shmem_guide 文档**。SHMEM 运行时库与底层 kernel 实现在**外部开源仓** [`gitcode.com/cann/shmem`](https://gitcode.com/cann/shmem)（编译产物 `libcommshmem.so` + `_pyshmem.*.so` 动态库），cann-recipes-infer 仅在 doc 中演示其调用方式。

## 对称内存与全局编址

shmem 的对称内存原理（guide 对称内存原理示意，dispatch&combine 章节配图）：通信域内**每张卡（die）在各自本地申请内存**，所有卡通过全局虚拟地址空间形成统一编址，die 与 die 之间的内存**步距设为 1G**（用户可决定分配次数/大小，但**单 die 分配总大小不可超过 1G**）。`context->shmem_addr` 对应当前卡的 shmem 内存起址；**状态区紧跟数据区之后**——这是 dispatch/combine 等通算融合算子布局 win 区（数据区 + 状态区）的基础约定。

算子内通过 `GetShmemDataAddr` / `GetShmemSignalAddr` 获取目标对端卡数据区 / 状态区的内存起始地址。

**SHMEM 使能：init → context 传递机制。** 通算融合算子复用 SHMEM 基础语义需先初始化对称内存并取得通信 context：`ShmemInit(rank, 总die数)` 为当前 die 分配数据区 + 状态区共用的 win 内存，再经 `InitAndGetMC2CommContext()` 把共享内存信息封装成 `shmem_context`，作为入参传给 dispatch/combine 算子；整网用 `init_shmem_once` 保证 shmem 内存只初始化一次（重复初始化会报错）。具体 byte/rank 数等案例参数可省。

## Host 侧接口：HBM&DDR 混合编址

用于把 Host 内存映射成 Device tensor（KVCache Offload 的核心）。guide 以 DeepSeek-V3.2 为例，模型初始化阶段为待卸载 KVCache 在 Host 侧分配内存并映射到 Device：

```python
cache_nope_bytes = cache_nope_tensor.untyped_storage().nbytes()
cache_nope_data_ptr = aclshmem_malloc(cache_nope_bytes, MemType.HOST_SIDE)
# 用 metadata(data_ptr/device/nbytes/dtype/size/stride/...) 重建 storage
storage = torch_npu._C._construct_storage_from_data_pointer(
    metadata["data_ptr"], metadata["device"], metadata["nbytes"])
cache_nope = torch_npu._C._construct_NPU_Tensor_From_Storage_And_Metadata(metadata, storage)
```

映射后模型推理可**直接把这块 Host 内存当 Device tensor 使用**，无需感知 Host/Device 内存差异；算子（如 [gather-selection-kv-cache](../kernels/gather_selection_kv_cache.md)）直接操作映射后的 tensor，无需感知 Host 侧排布。

## Device 侧 / 算子内 API

### pyPTO-shmem（实现部分 OpenSHMEM 语义）

| API | 语义 |
|---|---|
| `shmem_put` | 将本地 tensor 发送到对称内存指定位置 |
| `shmem_get` | 从对称内存指定位置取数据到本地 tensor |
| `shmem_signal` | 给其他卡发送信号 |
| `shmem_wait` | 等待本卡信号等于指定值 |
| `shmem_barrier_all` | 通信域内卡间同步（所有卡到达才继续） |

非标准 OpenSHMEM 语义：`create_shmem_tensor`（指定通信域创建对称内存 Tensor）、`shmem_clear_data`（数据区清零）、`shmem_signal_data`（signal 清零）、`my_symbolic_pe`（本卡符号化 rank id）。pyPTO 图描述里对应 C++ 算子记法为 `ShmemPut` / `ShmemGet` / `ShmemSignal(..., AtomicType::ADD)` / `WaitUntil(...)`（见 [pypto](../frameworks/pypto.md)）。

### TileLang-shmem

封装 `T.shmem_ub_put_nbi_new(x_ub, win, ub_size, dest_rank_id, stride)`——把本卡 UB 数据非阻塞（nbi）传送到对端 win 区（`stride` 为偏移量）；配套 `T.alloc_ub` / `T.sync_all()`（核间同步）等。见 [tilelang](../frameworks/tilelang.md)。

## 典型场景

- **KVCache Offload**：HBM&DDR 混合编址使模型侧无需感知 Host/Device 差异即可做 h2d/d2h，且 shmem 低延迟高带宽通信降低 h2d 耗时；DeepSeek-V3.2 上使能 Offload+shmem，Atlas A3 64 卡、64K 序列下最大 batch 从 1024 增至 2048（与 [kvcache-offload](kvcache_offload.md) 容量型口径一致；A3 平台前提）。
- **DeepEP dispatch&combine 通算融合**：基于对称内存的 win 区（数据区+状态区）与 put/signal/wait 语义实现 MoE 专家并行 All-to-All（[expert-parallel](../parallelism/expert_parallel.md)）——此场景的发/等状态 + win 拷贝机制与三路实现样例（原生 SHMEM API / Tilelang-shmem / pyPTO-shmem）见 [shmem-dispatch-combine](shmem_dispatch_combine.md)，其依赖的 SHMEM 基础语义如上。
- **HIXL 单边通信**：[hixl](hixl.md) 基于 SHMEM 机制实现 PUT D2rH / GET rH2D 的池化数据访问。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_shmem_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_shmem_guide.md)（简介 / Highlights / KVCache Offload / 对称内存原理 / pyPTO-shmem API / TileLang-shmem API；主源 656 行，本页取 SHMEM 编程模型部分）
- 外部仓：SHMEM 运行时库与 kernel 实现 [`gitcode.com/cann/shmem`](https://gitcode.com/cann/shmem)
- 溯源：shmem_guide 随 V4 引入（`5df82b1` support deepseek v4，MR!366）

## Links

- [hixl](hixl.md)
- [kvcache-offload](kvcache_offload.md)
- [online-pd-inference](../frameworks/online_pd_inference.md)
- [deepseek-v4](../models/deepseek_v4.md)
- [pypto](../frameworks/pypto.md)
- [tilelang](../frameworks/tilelang.md)
- [gather-selection-kv-cache](../kernels/gather_selection_kv_cache.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [shmem-dispatch-combine](shmem_dispatch_combine.md)

## Notes

- **gap（外部仓）**：SHMEM kernel 级实现（MTE/xDMA/SDMA 引擎封装、`aclshmem_init`/`aclshmem_finialize`/`aclshmem_create_tensor` 等运行时细节）在外部 `cann/shmem` 仓，cann-recipes-infer 未含。
- **接口名记法**：`GetShmemDataAddr`/`GetShmemSignalAddr`/`shmem_ub_put_nbi_new`/`aclshmem_malloc`/`MemType.HOST_SIDE` 均按 guide 文档原拼写记录；guide 代码片段为示意（省略号略去细节）。