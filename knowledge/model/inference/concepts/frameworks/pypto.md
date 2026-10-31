---
type: Concept
title: PyPTO
description: PyPTO 以声明式 Tensor 图表达融合算子，经 PTO-ISA、MPMD 调度和后端编译实现不同硬件的适配；本卡维护框架机制，Duration 与 VF 收益由独立观测记录。
tags:
- task.implementation
- topic.architecture
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_pypto_operator_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/pypto_python/impl/hc_pre_pypto.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- a2
- a3
- '950'
---
# PyPTO

## Summary

自研的 Python 级融合算子编程框架，通过声明式的 Tensor 操作图来描述融合 kernel，兼顾开发效率与运行性能。在 cann-recipes-infer 中用于实现 MegaKernel 级别的多算子融合。

## Architecture

- 用户以 Python DSL 描述 Tensor 级计算图
- 框架自动完成 Tiling 划分、内存分配、指令调度
- 编译为 NPU 可执行的融合 kernel

## Key Features

- Python 级编程，开发效率高
- 自动 Tiling 和内存管理
- 支持多算子融合为 MegaKernel
- 支持多核 MPMD 并行调度

## Usage Scenarios

- 快速实现融合算子原型
- MegaKernel：将 decode 阶段多个算子融合为单一大 kernel
- 开发效率优先但仍需较好性能的场景

## Constraints

- 性能上限可能低于手写 AscendC
- 对复杂数据流模式的表达能力有限

## DeepSeek-V4 框架级增强

DeepSeek-V4 0day 适配在 PyPTO 上一次性发布了 `hc_pre`、`Compressor`、三个 FA 类算子（`SWA` / `CFA` / `SCFA`），并对 `MlaProlog` / `IndexerProlog` 做了新架构适配。实现代码位于 `ops/pypto_python/impl/`（compressor_pypto.py / hc_pre_pypto.py / mla_prolog_pypto.py / sliding_window_attention_pypto.py / compressed_flash_attention_pypto.py / sparse_compress_flash_attention_pypto.py / lightning_indexer_prolog_quant_pypto.py 等）。源码规模、开发周期与各算子 Duration 属该来源的一次披露，统一见[平台待核验观测](../../optimizations/benchmark_observations/pypto_v4_operator_source_observations.md)。

### PTO-ISA：跨代际芯片兼容（兼容不降速）

PyPTO 后端基于 **PTO 虚拟指令集（PTO ISA）** 打造。算子前端无需感知芯片代际差异 —— **一套算子代码即可在不同代际芯片（A2 / A3 / 950D）上运行**，代际能力差异通过 pass IR 与后续 PTO 指令在后端区分（除 MXFP8 量化等芯片本身能力不支持的情形外）。PTO ISA 统一指令接口、做到微架构高度适配，guide 称其「兼容不降速」。其支持的 Atlas A2 / A3 / Ascend 950PR / 950DT 平台在 `ops/pypto_python/README.md` 中明示（README「概述」段）。

> PTO ISA、毕昇 PTO 编译器及 DFX（TPRINT 等）是 **外部 Cann-PyPTO 编译器仓（`gitcode.com/cann/pypto`）** 的能力，cann-recipes-infer 的 `ops/pypto_python/` 仅含调用其 API 的算子 kernel 实现。PTO ISA、编译器和 DFX 的说明依据 guide 文档，未经过编译器源码级验证。

### MPMD 调度与 Unrollist 动态转静态

- **MPMD（多程序多数据）调度**：Decode 场景下，像 MLAProlog 的 `x@wq_a` 与 `x@wkv` 不会用满所有核，PyPTO 框架自动让无依赖任务并行执行（query/kv 后续 RmsNorm 同理），无需手动插同步。hc_pre 计算流程第一步 Vector（RMSNorm 分母）与第二步 Cube（`x @ hc_fn` 矩阵乘）无依赖 —— 框架支持两任务同时执行。
- **Unrollist（动态展开为静态图）**：Prefill 与 Decode 的 token 数 `t` 差异巨大，一套 Tile 切分很难两端都优。PyPTO 用 `pypto.loop_unroll(0, t, 1, ..., unroll_list=[...])` 对动态值 `t` 多分档、采用静态 tTile 切分，在不同场景下均达较优性能。两个算子的分档表不同：**hc_pre 生产入口取 `unroll_list=[256, 64, 16, 4, 1]`**（实现位置：hc_pre_pypto.py:149，由 :155 `loop_unroll` 消费；示例路径 `hc_pre_kernel_prefill` 另用 [128, 1]，见 :266），与 [mhc-hcpre-hcpost](../kernels/mhc_hcpre_hcpost.md) 一致；**mla_prolog 取 `unroll_list=[128, 64, 32, 16, 1]`**（实现位置：mla_prolog_pypto.py:470 `MlaPrologV4Configs`，经 :335→:337 `loop_unroll` 消费）。

### 合图参数与 MatMul 优化

- **合图优化**：通过 `pass_options={"cube_nbuffer_mode": 1, "vec_nbuffer_mode": 2, "vec_nbuffer_setting": {-1: 2}}`（实现位置：mla_prolog_quant_pypto.py:508-510）合并相同结构子图，避免子图数过大与重复搬运，增大核内流水调度可能性。
- **切 K MatMul**：Decode 场景 MatMul 的 K 轴很长（如 hc_pre 16K）而 M/N 轴较小，采用 `pypto.set_cube_tile_shapes(..., enable_split_k=True, enable_multi_data_load=True)` 切 K（实现位置：hc_pre_pypto.py:176）把数据切到不同核充分利用算力；shape 大时开大包搬运提带宽利用率。
- **免广播 / scatter_update / 转置技巧**：Sinkhorn-Knopp 的归约串联逐元素乘除经 `pypto.experimental.set_operation_config(combine_axis=True)`（实现位置：hc_pre_pypto.py:136）避免显式广播；Compressor 的 `kv_state`/`score_state` 刷新用 `scatter_update_3d`（实现位置：compressor_pypto.py:453,611）规避反复搬入 UB + concat；仅 guide/test 的 hc_pre_kernel_prefill 示例用 hc_fn^T @ x^T 转置技巧把归约轴置于 -2/-3；生产入口 hc_pre_kernel 使用 matmul(x_fp32, hc_fn, b_trans=True)，不能将示例转置归为整网 Prefill 的生产实现。各算子级细节见对应 kernel 页。

### 毕昇 PTO 编译器 VF 自动融合

`hc_post`（仅用 Vector 核，计算式 `y = post.unsqueeze(-1)*x.unsqueeze(-2) + sum(comb.unsqueeze(-1)*residual.unsqueeze(-2), dim=2)`）在已做其他优化基础上，PTO-ISA 结合毕昇 PTO 编译器的 **VF（Vector Fusion）自动融合**能力，做 micro kernel 级融合，该来源报告过相对收益，数字统一由独立观测维护。

> 该单算子结果未绑定具体测量型号、完整 shape 与端到端收益，见[来源观测](../../optimizations/benchmark_observations/pypto_v4_operator_source_observations.md)。VF 融合属外部毕昇 PTO 编译器能力，cann-recipes-infer 不含该编译器源码。cann-recipes-infer 的 `hc_post` 另有 **AscendC 手写实现**（`ops/ascendc/src/hc_post/`），PyPTO 侧 hc_post 未单独建实现文件 —— 二者并列，见 [mhc-hcpre-hcpost](../kernels/mhc_hcpre_hcpost.md)。

## 机制落地（V3.2-Exp PyPTO 算子开发指南）

以下三块来自 DeepSeek-V3.2-Exp 的 PyPTO 算子开发指南，给上文抽象引用的 PTO ISA / 子图切分 / MPMD 运行时补具体内容。

### PTO ISA 指令分类（Parallel Tile Operation）

PyPTO 中对数据的操作称为 Operation；Tensor Operation 经 Tiling 后转换为 Tile Operation。框架提供一组基本 Tile Operation 作底层硬件抽象，可针对不同芯片适配以实现跨平台支持，开发者也可自定义扩充。guide 列举的 PTO 指令实例分为以下 7 类（每类仅给代表指令，原表未列出完整指令集）：

| 分类 | 代表指令 | 功能描述 |
| --- | --- | --- |
| Element Op（逐元素操作） | TADD | 执行两个 Tile 数据块内逐元素的加法运算 |
| Tile-Scalar Op（块与标量操作） | TADDS | 将标量与 Tile 数据块内逐元素相加 |
| Axis Op（按轴操作） | TROWSUM | 对 Tile 数据块的每一行执行求和 |
| MATMUL Op（矩阵乘操作） | MAMULB | 执行两个 Tile 矩阵数据块的乘法 |
| Fix Pipe Op（固定管线操作） | TMOV | 将 Tile 元素从源寄存器搬移到目的寄存器（可带随路运算） |
| MEM Op（访存操作） | TLOAD / TSTORE | TLOAD 将数据从内存加载到 Tile 数据块；TSTORE 将 Tile 数据块写回内存 |
| Complex Op（复杂操作） | TCVT | 执行 Tile 数据块的类型转换 |

### 子图切分的三个权衡（核内 SRAM 管理）

Tiling 得到 Tile Operation 粒度的计算图后，框架对计算图切分并为子图插入数据搬运指令以使用各层级核内 SRAM——每个子图的输入输出放在 Global Memory，子图内只用核内 SRAM 存放中间数据。切分过程权衡三点：

1. **Operation 亲和性**：在同一类型核上执行的 Operation 会被尽可能分配到同一子图。
2. **子图同构性**：尽可能保证切分出的子图可复用，以减少编译耗时、降低 ICache Miss 率。
3. **子图并行度与重复数据搬运的权衡**：过大的子图会导致核空闲，过小的子图会导致同一份数据向不同核重复搬运；开发者可通过配置参数调整切分策略，在并行度与 SRAM 利用率间取得平衡。

### MPMD 运行时三步机制

切图后得到许多小子图（PyPTO 的最小执行单元），每个子图编译成可执行文件、生成对应任务，分发到不同核执行。运行时为 MPMD，整个过程分三步：

1. 根据子图间的**数据依赖**创建任务间依赖；
2. 调度 [aicpu-scheduler](../techniques/aicpu_scheduler.md)（AICPU）按任务的**拓扑顺序**把无前置依赖的任务下发到空闲 AI 核，AI 核收到任务后**立即异步执行**；
3. 任务执行完成后 AICPU 收到回调信息，**解除后续任务依赖并继续尝试下发**。

这是区别于 SPMD 的**事件驱动闭环**：SPMD 要求同一时刻所有核执行相同程序、需全局同步；MPMD 则按运行时实际解依赖情况调度，无需全局同步，使不同核在同一时间执行不同程序，充分利用多核并行。

## Evidence

- [deepseek_v4_pypto_operator_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_pypto_operator_guide.md)（primary）
- [hc_pre_pypto.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/ops/pypto_python/impl/hc_pre_pypto.py)（implementation）

## Known Usages

- **Qwen3-Next ChunkGDN**（Prefill 路径的 Gated DeltaNet 分块递推融合算子），提升长序列 Prefill GDN 的融合易用性；与 AscendC 的 Decode 端 [recurrent-gated-delta-rule](../kernels/recurrent_gated_delta_rule.md) 形成 Prefill/Decode 两端互补。

> **并非所有混合注意力模型的 Prefill GDN 都走 PyPTO。** [qwen3-5-moe](../models/qwen3_5_moe.md) 的 Prefill ChunkGDN 用的是 **torch_npu 原生算子 `torch_npu.npu_chunk_gated_delta_rule`**，不经 PyPTO；仅 Qwen3-Next 的 ChunkGDN 是 PyPTO 实现。两者 Decode 端则都用 AscendC 的 `recurrent_gated_delta_rule`。读者不应据 Qwen3-Next 推断"所有 GDN Prefill 融合都来自 PyPTO"。

## Links

- [ascendc](ascendc.md)
- [tilelang](tilelang.md)（TileLang PTO-AS 对接层走 PyPTO 的 PTO ISA）
- [deepseek-v4](../models/deepseek_v4.md)（V4 0day PyPTO 算子：hc_pre / Compressor / SWA·CFA·SCFA / MlaProlog / IndexerProlog）
- [atlas-a3](../platforms/atlas_a3.md)
- [ascend-950](../platforms/ascend_950.md)（PTO-ISA 跨代际目标平台之一：950D「兼容不降速」）
- [qwen3-next](../models/qwen3_next.md)
- [qwen3-5-moe](../models/qwen3_5_moe.md)
- [gated-deltanet](../modules/gated_deltanet.md)
- [recurrent-gated-delta-rule](../kernels/recurrent_gated_delta_rule.md)
- [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)（V4 SAS 的 SWA/CFA/SCFA 三场景化算子由 PyPTO 实现）
- [compressor](../kernels/compressor.md)（V4 KV 压缩融合算子 PyPTO 实现：MatMul/向量分子图优化 + scatter_update 刷 state）
- [lightning-indexer](../kernels/lightning_indexer.md)（LI PyPTO 实现：自研 MegaKernel，泳道图调优 +27%）
- [mhc-hcpre-hcpost](../kernels/mhc_hcpre_hcpost.md)（HcPre 的 PyPTO 实现：MPMD 流水、免广播指令优化、切 K MatMul、Unrollist；HcPost 仅 Native/AscendC，无 PyPTO 版）
- [mla-prolog](../kernels/mla_prolog.md)（V4 MLAProlog 适配为 PyPTO 算子：inplace interleaved RoPE、Unrollist 分档、合图）
- [indexer-prolog](../kernels/indexer_prolog.md)（V3.2-Exp `npu_lightning_indexer_prolog_pto` 大融合算子；V4 CSA 层 IndexerProlog q_hadamard / Quant 流程）
- [cann-shmem](../techniques/cann_shmem.md)（pyPTO-shmem 框架接入 SHMEM：以 `shmem_put`/`shmem_get`/`ShmemSignal` 等图记法做通算融合算子）
- [shmem-dispatch-combine](../techniques/shmem_dispatch_combine.md)（pyPTO-shmem 写 MoE dispatch&combine：dispatch 三子图 / combine 两子图，ShmemPut/WaitUntil/ShmemGet/Matmul 加权融合）
