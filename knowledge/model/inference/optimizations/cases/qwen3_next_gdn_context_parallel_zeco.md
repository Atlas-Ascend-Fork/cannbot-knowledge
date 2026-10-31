---
type: Optimization
title: Qwen3-Next A3 GDN Context Parallel 案例：ZECO 状态传播与版本限制
description: 记录 PR359 的 GDN CP 实现、单 batch 与 head_dim=128 边界；与早期全注意力 CP 案例分开，不把测量点外推为通用加速规律。
tags:
- task.debugging
- topic.model_architecture
- topic.attention
- topic.parallelism
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md
  role: supporting
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage6/0001-support-gdn-cp.patch
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/sgl_kernel_npu_support_gdn_cp.patch
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T13:54:05Z'
platforms:
- a3
scope:
  schema: model.inference.v1
  any_of:
  - all_of:
      phase:
      - prefill
      objective:
      - ttft
      framework:
      - sglang
      parallelism:
        all_of:
        - cp
        - tp
---

# Qwen3-Next A3 GDN Context Parallel 案例：ZECO 状态传播与版本限制

## 适用场景（问题信号）

在优化**线性注意力**（[GatedDeltaNet](../../concepts/modules/gated_deltanet.md) / Mamba / DeltaNet 风格的 chunk 递推）时，遇到以下场景应想到 ZECO：

- 要给线性注意力层上**序列并行 / Context Parallel**（长序列 prefill、单卡 activation 显存不够 / OOM），但——
- 线性注意力的 **chunk 递推状态跨 chunk 顺序依赖**（`h_t` 要等 `h_{t-1}`），天然抗拒按序列切分：常见结果是全注意力层能吃 CP、**线性注意力层只能回退 full Tensor Parallelism**、拿不到序列并行的加速与省显存。

ZECO 就是让线性注意力突破这个「顺序依赖」、也能像全注意力一样切序列的算法。

## ZECO 是什么

线性注意力的 chunk 递推是**仿射线性**的：`h_t = A_t · h_0 + B_t`（`A_t`/`B_t` 只依赖本 chunk 的输入，与前序状态 `h_0` 无关）。据此可把「跨 rank 顺序算 h」拆成两步、让各 rank 并行：

1. **各 rank 先并行算本地 chunk 的状态转移系数 `(a, b)`**（不需要上游状态），与跨 rank 通信重叠。
2. **一次轻量的跨 rank 状态传播**得到每个 rank 的 initial_state，再用 `h_t = a·h_0 + b` 本地还原状态、出输出——不再需要按 rank 顺序滚算 `h`。

拓扑**非 ring**：首 rank 正常算出 final_state 沿链传播、末 rank 把 global final_state broadcast 给全组。于是线性注意力层也能沿序列维切到多 rank（CP），与全注意力层的 CP（ZigZag 负载均衡，见 [long-seq-prefill-context-parallel](../rules/long_seq_prefill_context_parallel.md)）配齐。

> 一句话：**利用 chunk 递推的线性性，把「顺序依赖的状态滚算」换成「并行算系数 + 一次状态传播」——这是该实现的设计依据；迁移到其他递推或并行方案时仍需重新证明状态传播和数值正确性。**

## 参考实现：cann-recipes-infer（Qwen3-Next）

cann-recipes-infer 在 [qwen3-next](../../concepts/models/qwen3_next.md) 上有一份可参考的 ZECO 实现，可直接借鉴其工程结构：

- **选路**：`chunk_gated_delta_rule_npu` 在 `cp_group is not None` 时走 `chunk_gated_delta_rule_zeco_fwd`；first_rank 与其它 rank 分别编排 `isend/irecv` + 独立 `comm_stream` 与计算重叠。
- **两个 Triton-on-Ascend 核**：`chunk_delta_h_zeco.py`（a/b 系数核 + `chunk_final_state_zeco_kernel`）、`chunk_o_zeco.py`（输出核）。
- **框架元数据**（`AscendGDNAttnBackend.init_cp_metadata`）：切序列前按每卡重建 `query_start_loc`/`cu_seqlens`（均匀切分、余数摊到前几卡、`.clone()` 防改共享张量）；单 batch 走 `single_batch_overlapped_causal_conv1d_update`（isend 末尾 `overlap_size = weight.shape[1]-1` 个元素重叠 conv1d）。
- **使能**：`export ENABLE_CONTEXT_PARALLEL_GDN=1` + `--cp-size N`（替换 `--enable-dp-attention --dp-size N`）；env 打开后 `use_full_tp=False` → GDN 走 CP。

**该参考实现的约束**——照搬这套代码要受它们约束，迁移算法思想则不受：

当前 README 的部署限制：CP 仅支持 PD 分离，P/D 卡数相同，`cp_size < tp_size`，因 GDN 切分头数限制还要求启动参数 `tp_size <= 32`，不能同时启用独立 DP。这里的 `tp_size` 是启动参数，不能与每个 CP rank 内的局部 TP 因子混用。环境开关或状态传输实现不代表其他部署组合已支持。

- **GDN `head_dim` 硬编码 128**（`assert K==128`、无回退，维护者确认刻意如此）：其它 head_dim 的线性注意力模型上 CP 前须先确认或改核。
- **只针对单 batch 均衡切分**：多 batch 有代码路径但切分不按 batch 均衡，非目标场景。
- **SGLang + sgl_kernel_npu 的 fla 栈**、Atlas A3（910C）。
- **PD 分离**：`attn_tp_size` 不等时按 head 维切 Mamba/GDN state 做 M:N TP 传输（`send_mamba_state_slice`，要求 `state_type=="mamba"`；源码分别实现源 TP 大于目标 TP 与不大于目标 TP 的切片分支，不能据此额外规定前者不合法）；PD 分离下强制 `swap_kv`，会破坏 chunked prefill 并带额外通信开销。

## 当前证据与验证

当前 stage6 和 kernel patch 保留 ZECO 状态转移、P2P 卷积 overlap 与 head_dim=128 限制，README 保留 GDN-CP 的环境开关和 PD/CP 部署边界。当前这些来源未给出可绑定本版本的原始算子/端到端测量记录，因此撤下旧 PR 多轮性能数字，不把不同次测量拼成当前结果。

应在所选模型与软件栈中验证卷积边界、initial/final state、位置/序列重排和完整输出，再测 TTFT、显存与通信时间。本次未应用补丁或运行 NPU。

## rollback

关闭 ENABLE_CONTEXT_PARALLEL_GDN 会选择 full-TP 路径；需同时恢复合法部署参数并重新验证输出，不假定运行态缓存可直接复用。

## 相关经验

- 另见 [混合线性注意力 (Mamba / Gated-DeltaNet) 昇腾部署的精度陷阱清单](../../runbooks/precision/precision_mamba_gdn_linear_attention.md)。


## Evidence

- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/README.md)（primary）
- [qwen3_next_optimization.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/integration/sglang/qwen3-next/qwen3_next_optimization.md)（supporting）
- [0001-support-gdn-cp.patch](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/stage6/0001-support-gdn-cp.patch)（implementation）
- [sgl_kernel_npu_support_gdn_cp.patch](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/integration/sglang/qwen3-next/patches/sgl_kernel_npu_support_gdn_cp.patch)（implementation）

## 与统一规则和早期 CP 实现的关系

CP 选型统一见 [长序列 Prefill CP 规则](../rules/long_seq_prefill_context_parallel.md)。本卡覆盖 PR359 stage6 的 GDN 扩展；[早期 Qwen3-Next CP 案例](qwen3_next_a3_prefill_cp_tp.md) 覆盖 PR235 stage4，不能把两个版本的限制拼成一个配置。上线前应按目标版本验收单 batch 切分、PD 状态传输和输出精度；现有性能表是来源自报，未在此复测。
