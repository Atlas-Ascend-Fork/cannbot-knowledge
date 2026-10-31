---
type: Concept
title: DeepSeek-V4
description: DeepSeek-V4 Flash/Pro 的 Shared-KV、SWA/CSA/HCA、mHC、当前 CacheEntry 生命周期，以及 HiF8、A4W4、DSpark 和 950 低时延 TP 入口。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/README.md
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/configuration_deepseek.py
  role: implementation
created_at: '2026-05-30T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
platforms:
- a3
- '950'
---

# DeepSeek-V4

## Summary

DeepSeek-V4 是 DeepSeek 发布的新一代长序列模型，包含 **DeepSeek-V4 Flash（285B）** 与 **DeepSeek-V4 Pro（1.6T）** 两种规格。在 DeepSeek-V3.2 的稀疏 Attention（DSA）基础上，V4 进一步在**层间交错**引入 **KV Cache 滑窗（Window Cache）** 与 **KV Cache 压缩（Compress）**，在保持注意力计算量/访存量低位（相对 Full Cache）的同时大幅提升长序列效率，提供长达 **1M 序列** 的高性能推理。

cann-recipes-infer 0day 适配 V4，覆盖 **Atlas A3 Pod** 与新代际 **Ascend 950PR/DT** 两类昇腾芯片，AscendC / PyPTO / TileLang 三套算子实现同步开源。Decode 沿用 DeepSeek 的 Attention DP + MoE EP 部署，Prefill 长序列走 CP + zigzag 切分；图模式默认采用 `npugraph_ex` 后端。

V4 与 [deepseek-v3.2-exp](deepseek_v3_2_exp.md) 的关键结构差异：
- **Attention 主体由 MLA 改为 MQA（Shared-KV）**，不再区分 `naive` / `absorb` 计算流，引入 `attention_sink` 参数（详见下文 Architecture）。
- **分层交错 Hybrid Attention**：滑窗 + 4x/128x 压缩 + LI 稀疏交替。
- **MoE 激活 6 路由 + 1 共享**专家（DSV3.2 为 8 路由），前几层 hash routing、后续层 soft routing。
- 新增 **mHC（Manifold-Constrained Hyper-Connections）** 多路残差结构（见 [mhc](../modules/mhc.md)）。
- A3 Pod KV Cache 采用 **C16**（DSV3.2 为 C8）。


## Architecture

每个 Layer 含 **mHC、Attention、MoE** 三种模块。

### 分层交错 Hybrid Attention

Attention 沿用 LI 稀疏机制并新增滑窗与压缩，按 `compress_ratio`（代码 `Attention.compress_ratio`；`compress_ratio = 1 if is_mtp else config.compress_ratios[layer_idx]`，逐层值由权重 config 的 `compress_ratios` 列表决定，无 `% 2` / 奇偶规则）分三类：

| 类型 | compress_ratio | 含义 | LI 稀疏 | 层位置（交替，源 guide 文字；具体逐层由 config 列表决定） |
| ---- | ---- | ---- | ---- | ---- |
| SWA（compress_ratio=1） | 1 | Sliding Window Attention，`sliding_window=128` 大小 KV Cache（代码内部 RoPE 路径 dict key 为 `c1a`，非 guide 定义的 attention type） | 无 | Flash 前两层 |
| HCA | 128 | Heavily Compressed Attention，Full Cache 压缩 128× | 无 | Pro 前两层；后续层与 CSA 交替（alternate） |
| CSA | 4 | Compressed Sparse Attention，Full Cache 压缩 4× | 有 | 后续层与 HCA 交替（alternate） |

- **CSA 层**在压缩后的 Cache 上叠加 LI（[lightning-indexer](../modules/lightning_indexer.md)）稀疏选择，选 **Top512**（**guide 示例值**）对 KV 参与 Attention 计算；运行时 CSA topk = `config.index_topk`（代码 `cmp_topk = self.config.index_topk`，仓内 `configuration_deepseek.py` 默认 **2048**，实际取权重 config）。
- Attention 计算采用 **MQA（Multi-Query Attention）而非 MLA**：代码 `modeling_deepseek.py` 中 attention 类为 `Attention`（docstring 标注 `"""Multi-Query Attention (MQA) Layer."""`），统一 **Shared-KV**，不再区分 Prefill / Decode 的 `naive` / `absorb` 流；引入 `attn_sink`（per-head `nn.Parameter`，作为 `sinks` 入参喂入 SAS 算子）。SWA / CSA / HCA 三类场景由统一融合算子 **SparseAttnSharedKV（SAS）** 落地（一套接口覆盖滑窗 / 压缩 / 稀疏及其组合 + Attention Sink），详见 [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)。
- V4 仍调用 **MLAProlog** 前置（代码 `mla_prolog()` → `mla_prolog_pypto` / `mla_prolog_prefill` / `mla_prolog_decode`），即 Q/KV 投影前置仍复用该融合算子，但 attention 主体已非 [mla](../modules/mla.md) 的低秩 KV 升降维计算流——见下方对比。见 [mla-prolog](../kernels/mla_prolog.md)。


### KV Cache 组成与内存

KV Cache 由 **Window Cache + Compress Cache + remainder** 组成（压缩层的 KV/Indexer Cache 由 [compressor](../kernels/compressor.md) 融合算子产出并刷新）：

- **SWA 层**仅保留 `sliding_window=128` 大小 KV Cache。
- **压缩层**存压缩后的 KV，大小 ≈ `batch_size × (kv_length // compress_ratio) × head_dim × storage_bytes × num_compress_layers`。
- 未满足压缩长度的 `kv_state` / `score_state` 暂存 **remainder**（最大 ≈ `batch_size × (compress_ratio − 1) × compress_dim × storage_bytes × num_compress_layers`）。
- CSA 层的 LI 同样经 [compressor](../kernels/compressor.md) 做 4× 压缩，保留压缩后长度的 **Indexer Cache**（未满足压缩长度的暂存 `indexer_kv_state` / `indexer_score_state`）。

效果（源 guide）：128k 序列下 HCA（128×）仅需保留约 **1k KV**，CSA（4×）保留约 **32k KV**，相对 Full Cache 内存压力显著缓解。

### MoE 专家

| 模型规格 | 路由专家数 | 共享专家数 | 单 Token 路由专家激活参数量 |
| ---- | ---- | ---- | ---- |
| 285B（Flash） | 256 | 1 | 6G |
| 1.6T（Pro） | 384 | 1 | 22.5G |

每次激活 **6 个路由专家 + 1 个共享专家**（代码 config 默认 `num_experts_per_tok=6`、`n_shared_experts=1`）。专家选取：前几层 `hash routing`（代码 `DeepseekV3MoE.hash = layer_idx < config.num_hash_layers`），后续层可学习 `soft routing`；源 guide 给出"前 3 层 hash / 后 40 层 soft"的层划分。


### mHC（Manifold-Constrained Hyper-Connections）

mHC 是对传统残差连接的扩展：把 `hidden_state` 从一路扩展到多路，在 Attention/MoE 计算前经 Pre Mapping 融合回一路（保持 Attention/MoE 计算过程不变），输出经 Post Mapping 扩展回多路，多路残差经 Res Mapping（Sinkhorn-Knopp 约束的混合矩阵）特征融合后与 Post Mapping 结果加和得到 mHC 输出。结构语义与计算公式见 [mhc](../modules/mhc.md)。本仓提供 `HcPre` / `HcPost` 融合算子（`HcPre` 含 AscendC + PyPTO，`HcPost` 含 AscendC），算子级 Tiling/流水/性能见 [mhc-hcpre-hcpost](../kernels/mhc_hcpre_hcpost.md)。`hc_post` 等小算子组合另有 `@torch.compile` + [autofuse](../frameworks/autofuse.md) 自动融合路径，与手写 AscendC 算子并列。

## Serving Strategy

配置、CP 数据交换、MTP 缓存与接受率验收集中到[DeepSeek-V4 部署流程](../../guides/models/deepseek_v4_deployment.md)。本页保留模型结构，具体优化取舍与验证按流程引用的规则执行。

## Quantization Overview

逐模块量化矩阵为独立子主题（A3 整数路径见 [int8-int4-hybrid](../quantization/int8_int4_hybrid.md)，950 浮点路径见 [hybrid-mxfp8-mxfp4](../quantization/hybrid_mxfp8_mxfp4.md)），此处为总览：

- **Atlas A3 Pod / W8A8C16（Int8，推荐 Flash）**：基于原生 Hybrid FP8-MXFP4 权重做 Int8 W8A8；仅对参数量大的部分 Linear（MLA `q_b_proj`/`o_b_proj`、Indexer `q_b_proj`）量化，KV Cache 维持 **C16（BF16 存算）**；LI 经 A8C8 降时延。见 [int8-int4-hybrid](../quantization/int8_int4_hybrid.md)。
- **Atlas A3 Pod / Hybrid INT8-INT4（推荐 Pro）**：在上策略基础上对 MoE 路由专家用 W4A8（[w4a8c8](../quantization/w4a8c8.md)）、共享专家用 W8A8，显著降低 MoE 存储/访存。见 [int8-int4-hybrid](../quantization/int8_int4_hybrid.md)。
- **Ascend 950PR/DT / Hybrid FP8-MXFP4（原生）与 Hybrid MXFP8-MXFP4（硬件亲和）**：950 平台原生 Hybrid FP8-MXFP4 可权重无损平滑迁移；可用 MXFP8 替代原生 FP8 在 Prefill/Decode 高吞吐场景提升算力利用率；KV Cache C8 动态存 8 算 16，实际容量按混合打包记录核算。见 [hybrid-mxfp8-mxfp4](../quantization/hybrid_mxfp8_mxfp4.md)。


## 多流并行优化

Attention/Compressor 和共享/路由专家的具体编排与检查集中到[部署流程的多流章节](../../guides/models/deepseek_v4_deployment.md#4-多流数据依赖检查)，通用机制见[多流](../techniques/multi_stream.md)。

## Platform

V4 在 Atlas A3 Pod（[atlas-a3](../platforms/atlas_a3.md)，每节点 8 卡，`world_size = 2 × chip_num`）外，新增 **Ascend 950PR / 950DT** 代际支持（`platform_version: "950"`，PR 偏 Prefill、DT 偏 Decode）。950 平台的代际特性（原生 Hybrid FP8-MXFP4、MXFP8 替代、Histograms 指令加速 LI Top-k、L0A/L0B 容下 256³ 基本块（字节容量源未给对比、据 Tiling 约束推断）、V4 weightNZ 关闭等）详见 [ascend-950](../platforms/ascend_950.md)。最小部署单元（源 README）：950PR/DT Flash 4 chips / Pro 16 chips；A3 Flash 4 chips / Pro 32 chips。

## Benchmark

来源自报数字分平台统一维护在[950DT 观测](../../optimizations/benchmark_observations/deepseek_v4_950_source_benchmark.md)和[A3 Pod 观测](../../optimizations/benchmark_observations/deepseek_v4_a3_source_benchmark.md)。核对每行 GBS、卡数、MTP、量化和计时缺口；这里不重复性能表。

## 当前新增能力与边界

HiF8 混合量化、A4W4、950 low_latency_tp 和 Flash DSpark 已有当前实现，不再作为未来计划。DSpark 从主模型选定层收集辅助 hidden，分块 proposal 后批量 Verify；A3 与 950 均有路径，但 V4 DSpark 强制 cp_size=1。原生 MTP 的 Draft 共享权重不等于所有 Proposal Stage 共用 KV 内容；DSpark 每个 stage 的 CacheEntry 独立。

当前配置通过共享 Executor，六类配置统一预处理；持久 CacheEntry 由管理器绑定，离线 CP 使用逐层隔离的临时 state 并将有效请求状态写回，详见[部署流程](../../guides/models/deepseek_v4_deployment.md)与[DSpark 流程](../../guides/models/deepseek_v4_dspark.md)。

## Evidence

- [deepseek_v4_inference_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v4/deepseek_v4_inference_guide.md)（primary）
- [modeling_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modeling_deepseek.py)（implementation）
- [README.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/README.md)（implementation）
- [configuration_deepseek.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/configuration_deepseek.py)（implementation）

## Links

- [deepseek-v3.2-exp](deepseek_v3_2_exp.md)
- [mla](../modules/mla.md)
- [mhc](../modules/mhc.md)
- [lightning-indexer](../modules/lightning_indexer.md)
- [mla-prolog](../kernels/mla_prolog.md)
- [lightning-indexer](../kernels/lightning_indexer.md)
- [sparse-flash-attention](../kernels/sparse_flash_attention.md)
- [sparse-attn-sharedkv](../kernels/sparse_attn_sharedkv.md)
- [compressor](../kernels/compressor.md)
- [indexer-prolog](../kernels/indexer_prolog.md)
- [mhc-hcpre-hcpost](../kernels/mhc_hcpre_hcpost.md)
- [w4a8c8](../quantization/w4a8c8.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [int8-int4-hybrid](../quantization/int8_int4_hybrid.md)（A3 Pod Int8 W8A8C16 + Hybrid INT8-INT4 逐模块矩阵）
- [hybrid-mxfp8-mxfp4](../quantization/hybrid_mxfp8_mxfp4.md)（950PR/DT 原生 Hybrid FP8-MXFP4 + 硬件亲和 Hybrid MXFP8-MXFP4 + MXFP4 算法）
- [atlas-a3](../platforms/atlas_a3.md)
- [ascend-950](../platforms/ascend_950.md)（950PR/DT 代际：原生 FP8-MXFP4 / Histograms Top-k / L0A-L0B 256³[据 Tiling 约束推断] / weightNZ 关闭）
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [multi-stream](../techniques/multi_stream.md)（V4 Attention 多流：MLAProlog Cube/Vector + LI↔CSA Compressor CV 控核掩盖）
- [moe-multi-stream](../techniques/moe_multi_stream.md)（V4 共享↔路由专家多流，Int8/MXFP8 场景掩盖共享专家）
- [superkernel](../techniques/superkernel.md)
- [autofuse](../frameworks/autofuse.md)
- [pypto](../frameworks/pypto.md)（V4 PyPTO：PTO-ISA 跨代际 / MPMD / Unrollist / 合图 / hc_post VF 融合 +22.7%）
- [tilelang](../frameworks/tilelang.md)（V4 TileLang Developer 模式 + 四算子样例 SFA/mHC/Int8-GEMM/Act-Quant）
- [ascendc](../frameworks/ascendc.md)（V4 AscendC：950PR/DT 直方图 Top-k / FP8 模式 / Tiling 模板 + Cost Model / AICPU Scheduler）
- [aicpu-scheduler](../techniques/aicpu_scheduler.md)
- [context-parallel](../parallelism/context_parallel.md)
- [zigzag-cp](../parallelism/zigzag_cp.md)
- [data-parallel](../parallelism/data_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [cann-shmem](../techniques/cann_shmem.md)（DeepSeek 系列通用 SHMEM 通信基础）
- [hixl](../techniques/hixl.md)（基于 SHMEM 的单边零拷贝传输库）
- [shmem-dispatch-combine](../techniques/shmem_dispatch_combine.md)（DeepEP dispatch&combine 的 SHMEM 重写指南；V4 生产路径实调融合算子 distribute_dispatch_v2/combine_v2）
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)（V4 Decode 生产路径实调的一体化融合算子 dispatch_v2/combine_v2）
- [dsa](../modules/dsa.md)（DSA 架构模式；V4 为其思想延续，注意力主体改 MQA/Shared-KV，见上文矛盾标记）
- [deepseek-v4-continue-pretrain](../../../training/guides/recipes/deepseek_v4_continue_pretrain.md)（跨域·训练：DeepSeek-V4 的续训(CPT)实践）
