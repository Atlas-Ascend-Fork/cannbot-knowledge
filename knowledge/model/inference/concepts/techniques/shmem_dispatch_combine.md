---
type: Concept
title: 基于 SHMEM 重写的 MoE Dispatch&Combine
description: MoE Dispatch 按路由将 token 发往专家所在 rank，Combine 再按逆映射返回并按权重聚合结果。本方案用 CANN SHMEM 对称 win 区和 put/signal/wait 语义，将两者显式编排为发送数据、发送状态、等待状态、本地拷贝四步；Dispatch 还记录来源 rank、token 和 top-k 序号供 Combine 原路返回。guide 给出原生 SHMEM、TileLang-shmem 与 pyPTO-shmem 三种实现，均依赖独立数据区和状态区。它适用于 MoE EP All-to-All 通算融合，但不同于 HCCL double-routing，也不同于将通信封装在 npu_moe_distribute_dispatch_v2/combine_v2 内的融合算子。当前 DeepSeek-V4 生产模型仍调用 torch_npu 融合算子，SHMEM 重写仅为文档级开发示例，未验证独立 cann/shmem 运行时的实际执行行为。
tags:
- task.optimization
- topic.mixture_of_experts
- topic.parallelism
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_shmem_guide.md
  role: primary
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-10-29T15:24:39Z'
platforms:
- agnostic
---

# 基于 SHMEM 重写的 MoE Dispatch&Combine

## Summary

DeepEP（DeepSeek 开源的**通用 MoE EP dispatch/combine 通信库**，也见于 qwen3-next 等 MoE 部署的 `--moe-a2a-backend deepep`）的 **Dispatch / Combine** 是 MoE 专家并行（[expert-parallel](../parallelism/expert_parallel.md)）中 All-to-All 通信的两个核心操作：Dispatch 把每个 token 按路由结果分发到所选专家所在 rank，Combine 把专家处理后的结果按逆映射退还回 token 原属 rank（两者本质互为逆映射）。shmem_guide 给出**用 CANN SHMEM 对称内存语义手写重写这两个算子**的实现：以 [cann-shmem](cann_shmem.md) 提供的对称内存 win 区（数据区 + 状态区）与 put/signal/wait 语义为基础，把发送/状态同步/拷贝过程显式编排，提供**原生 SHMEM API / Tilelang-shmem / pyPTO-shmem 三路实现样例**。

> 知识归属：该 SHMEM dispatch&combine 重写记于 **DeepSeek-V4 的 shmem_guide**（随 V4 引入）。DeepEP 本身是 DeepSeek 开源的通用 MoE EP 通信库（同 guide 标题"集成至 DeepEP"），不限于单一模型版本；guide 中 DeepSeek-V3.2-Exp 仅出现在 KV-Offload + shmem 显存收益的论述里，与 dispatch&combine 重写无直接依据。

> ⚠️ gap（文档级演示）：shmem_guide 是"如何基于 SHMEM 重写 dispatch&combine"的开发指南。V4 生产模型 [`models/deepseek-v4/models/modeling_deepseek.py`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py) 当前Decode EP路径 实际调用的是**融合算子** `npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（torch_npu 原生），而非 SHMEM 重写路径。SHMEM 重写所用符号（`shmem_ub_put_nbi_new` / `ShmemPut` / `WaitUntil` / `aclshmem_create_tensor` 等）仅出现于 shmem_guide.md，运行时库在外部 [`cann/shmem`](https://gitcode.com/cann/shmem) 仓（`libcommshmem.so` + `_pyshmem.*.so`）。下述 API 记法以 guide 为准。

## 通信流程（四步范式）

Dispatch 与 Combine 共用同一套时序：**发数据 → 发状态 → 等状态 → 本地 win 区数据拷贝**。

| 阶段 | Dispatch | Combine |
|---|---|---|
| 发数据 | x shape `[Bs,H]`、expertIds shape `[Bs,K]`，每 token 发 K 次到不同 expert 所在 rank 的 win 数据区 | 借 `assistInfoForCombine` 三元组（来自哪 rank / 哪 token / 第 k 次发送），逐条把 token 还回原 rank win 数据区正确位置 |
| 发状态 | 状态区标记"某 rank 发往某 expert 数据是否发完"：`flag`（发完置 1）+ `cnt`（该路 token 数） | 发一条数据即发一条状态，**整条状态区填 1** |
| 等状态 | while 循环读本 rank 状态区 flag 求和，达目标值即"已收齐其他 rank 发来的 token" | while 等本 rank 发出的 A 个 token×K 次共 A·K 条是否全部还回（状态区求和等于目标值） |
| 本地拷贝 | win 数据区→UB→GM，每行含 token + 量化参数 + 三元组，切片得 `expandXOut` / `assistInfoForCombineOut` | 每 token 的 K 条结果（同 token 被不同 expert 处理）批量取出，按专家权重**融合为 1 条**，A 次循环得 `combineOut` |

Dispatch 主要输出：`expandXOut`（按专家重排后的接收 token）、`assistInfoForCombineOut`（三元组）、`expertTokenNumsOut`（每专家收到 token 数）、`epRecvCountsOut`（从各卡接收 token 数，对应 CombineV2 的 `epSendCounts`）。win 数据区布局见 cann-shmem 页"对称内存与全局编址"（状态区紧跟数据区）。

## 三路实现样例

### 原生 SHMEM API

shmem 初始化三步：`MoeDistributeCppBuffer(<bytes>, 1)` 为当前 die 分配数据区+状态区共用空间（不可超分配总量，单 die ≤1G）→ `dc_buffer.ShmemInit(<world_size>, rank, t)` 设 rank_id 与总 die 数 → `dc_buffer.InitAndGetMC2CommContext()` 封装 `shmem_context` 作算子入参。算子内用 `GetShmemDataAddr` / `GetShmemSignalAddr` 取对端数据区/状态区起址（`context->shmem_addr` 为本卡起址，状态区紧跟数据区）。整网接入：放置 `libcommshmem.so` + `_pyshmem.*.so`，封装 `init_shmem_once`（整网仅初始化一次，置于 `DeepseekV3ForCausalLM.__init__`），dispatch/combine 入参加 `shmem_context`，替换原生 torch_npu 版本。

### Tilelang-shmem

用 [tilelang](../frameworks/tilelang.md) DSL 写 kernel，载体 API `T.shmem_ub_put_nbi_new(x_ub, win, ub_size, dest_rank_id, stride)`——guide 描述为"Tilelang 封装的 shmem 接口，将本卡 UB 数据传送到对端 win 区"（`stride` 为偏移量；`_nbi` 后缀按 OpenSHMEM 惯例为非阻塞接口，guide 未显式说明，按命名推断）；配 `T.alloc_ub(shape, dtype)`、`T.sync_all()`（核间同步）。Dispatch kernel 入参含 `win_data [total_expert_num*Bs, ub_size]` / `win_status [total_expert_num, 8]`，发数据/发状态各调一次 `shmem_ub_put_nbi_new`（数据写 `(rank*Bs*local_expert_num + dest_expert_id*Bs + token_repeat_num[0])*ub_size`、状态写 `local_expert_id*ep_world_size*8 + rank*8`），`while(sum_of_flag[0] != aiv_expert_fp_num)` 等状态后本地拷贝。调用侧多进程 `mp.Process` + `aclshmem_init` → `aclshmem_create_tensor` 申请 win 区 → dispatch 输出喂 combine → `aclshmem_finialize`（[sic] guide 拼写）。

### pyPTO-shmem

用 [pypto](../frameworks/pypto.md) 声明式 Tensor 图描述。Dispatch 拆**三张子图**：`send_token`（按专家表 `ShmemPut` 发 token + 三元组 `moeSendMsg` 到对称内存）、`send_signal`（`ShmemPut` 计数 + `ShmemSignal(..., AtomicType::ADD)` 通知对端）、`receive_token`（`WaitUntil(..., moeExpertNum, true)` 等齐 → `ShmemGet` + `CumSum` 求偏移 → `Assemble` 拼出 `expandX` / `assistInfoForCombine`）。Combine 拆**两张子图**：`send`（按三元组 `ShmemPut` 原路返回 + `ShmemSignal(ADD)`）、`receive`（`WaitUntil(..., topK)` 等齐 K 条 → `ShmemGet` → 与 `expertScales` 做 `Matmul` 加权融合 → `Assemble` 输出）。pyPTO-shmem 对应的 OpenSHMEM 语义 API（`shmem_put`/`shmem_get`/`shmem_signal`/`shmem_wait`/`shmem_barrier_all` + 非标准 `create_shmem_tensor`/`shmem_clear_data`/`shmem_signal_data`/`my_symbolic_pe`）见 cann-shmem 页。

## 当前模型分派边界

V4 普通EP的Prefill仍双路由，Decode调用distribute_dispatch_v2/combine_v2；950新增low_latency_tp分支改走本地routing+TP专家GMM+all_reduce。A4W4 Decode会以FP4量化dispatch传输。上述当前生产分支均不能被描述为本页SHMEM示例已接入。

## Notes

- **与融合算子路径区分**：SHMEM 手写重写（显式发/等状态 + win 拷贝机制）与 `npu_moe_distribute_dispatch_v2` / `npu_moe_distribute_combine_v2`（torch_npu **一体化融合算子**，[moe-dispatch-combine-v2](moe_dispatch_combine_v2.md)，Qwen3-MoE/Qwen3.5/Gemma-4 及 V4 生产路径普遍调用）是不同机制——融合算子把发/等/拷贝封装在算子内部，不暴露 win 区。两者的输出字段互为对应：SHMEM 重写的 `epRecvCountsOut` ↔ CombineV2 `epSendCounts`、`assistInfoForCombineOut` ↔ DispatchV2 三元组。
- **与 Double-Routing 区分**：[double-routing](double_routing.md) 是 Prefill 阶段基于 `npu_moe_init_routing_v2` + `dist.all_to_all_single` 的 **8 步集合通信路由**（两轮路由与两轮顺序恢复；npu_moe_init_routing_v2、npu_moe_re_routing、index_select、npu_moe_finalize_routing 各调用一次，逻辑轮数不等于同名接口次数），走 HCCL AllToAll；SHMEM 重写则基于对称内存 win 区 + put/signal/wait 做**单边通信**，两者解决同一 EP All-to-All 问题但通信原语不同。
- **接口名记法**：`shmem_ub_put_nbi_new` / `aclshmem_create_tensor` / `aclshmem_finialize`[sic typo] / `MoeDistributeCppBuffer` / `InitAndGetMC2CommContext` / `ShmemSignal` / `WaitUntil` 均按 guide 原拼写记录；guide 代码片段为示意（`...` 略去细节），非完整可编译代码。

## Evidence

- [deepseek_v4_shmem_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_shmem_guide.md)（primary）

## Links

- [cann-shmem](cann_shmem.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [double-routing](double_routing.md)
- [moe-dispatch-combine-v2](moe_dispatch_combine_v2.md)（torch_npu 标准一体化融合算子，V4 生产路径实调，区别于 SHMEM 手写重写）
- [deepseek-v4](../models/deepseek_v4.md)
- [tilelang](../frameworks/tilelang.md)
- [pypto](../frameworks/pypto.md)
