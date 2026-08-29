---
type: Concept
title: DeepSeek-V3.2-Exp
description: DeepSeek-V3.2-Exp 是 DeepSeek 2026 年发布的实验性长序列模型，在 DeepSeek-V3.1 基础上引入 DeepSeek Sparse Attention (DSA) —— 由 Lightning Indexer (LI) 与 Sparse Flash Attention (SFA) 两个核心模块组成 —— 通过"选前 TopK 个相关 token 再计算注意力"将长序列 Attention 从 O(S²) 降至 O(S·TopK)。DSA 的引入保留了完整 MLA KVCache，同时新增 Indexer Key Cache；MoE/MLA 主干继续沿用 V3.1 的结构。
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-06-27T00:00:00Z'
platforms:
- a3
---

# DeepSeek-V3.2-Exp

## Summary

DeepSeek-V3.2-Exp 是 DeepSeek 2026 年发布的实验性长序列模型，在 DeepSeek-V3.1 基础上引入 **DeepSeek Sparse Attention (DSA)** —— 由 **Lightning Indexer (LI)** 与 **Sparse Flash Attention (SFA)** 两个核心模块组成 —— 通过"选前 TopK 个相关 token 再计算注意力"将长序列 Attention 从 O(S²) 降至 O(S·TopK)。DSA 的引入保留了完整 MLA KVCache，同时新增 Indexer Key Cache；MoE/MLA 主干继续沿用 V3.1 的结构。

cann-recipes-infer 在 Atlas A3 集群上完成 0day BF16、1day W8A8C16 部署，现已支持 W8A8C8 与 MoE W4A8 + Attention W8A8C8 量化。Prefill 采用长序列亲和的 **Context Parallel (CP)** 并行（摒弃 DP），Decode 沿用 V3.1 的 Attention DP + MoE EP 方案，MTP3 / perfect-eplb / KVCache Offload 全链路可选。

本次开源首次同时覆盖 **AscendC**（手写高性能）、**PyPTO**（自研 MegaKernel 融合编程）、**TileLang**（社区开源编译框架）三套实现，分别对应不同的开发/性能权衡。

### Highlights

- **长序列优势**：64 卡 W8A8C8，128K 序列 TPOT < **20 ms**；BF16 场景 64 卡 128K TTFT < 2 s、TPOT < 30 ms。
- **相对 V3.1 扩展**：随着序列长度增加吞吐优势扩大，128K 序列下达到 V3.1 吞吐的 **450%**（见 Benchmark 曲线）。
- **算子栈三合一**：AscendC `LightningIndexer` + `SparseFlashAttention`；PyPTO `Lightning Indexer` / `Indexer Prolog` / `Deepseek Indexer Attention` 融合算子；TileLang 社区版 LI + SFA。见 [ascendc](../frameworks/ascendc.md)、[pypto](../frameworks/pypto.md)、[tilelang](../frameworks/tilelang.md)。
- **量化**：W8A8C8、**W4A8C8**（MoE W4A8 + Attention W8A8C8）；MMLU / GPQA / DROP / MGSM 四项基准相对 BF16 基本无损（见 Known Optimizations/量化）。
- **KVCache Offload**：W8A8C8 + Offload 场景下同序列长度最大 batch size 翻倍，64K 序列下 global batch 可从 1024 → 2048。

## Architecture And Serving Traits

### DeepSeek-V3.2-Exp vs V3.1

> 源："相较 DeepSeek-V3.1，DeepSeek-V3.2-Exp 主要新增了 Lightning Indexer 稀疏模块，旨在从长序列中稀疏选择 Topk 个 Token 用于计算注意力。"

- **权重内存新增**：Lightning Indexer 是类 MQA 结构，新增 `q_b_proj`、`wk_proj`、`weight_proj` 三个 Linear，综合所有 Layer 约 **+0.85B** 参数。
- **KVCache 内存新增**：在保留完整 MLA Full KVCache 的基础上，额外缓存 **Indexer Key Cache**：
 `batch_size × kv_length × Indexer_head_dim × storage_bytes × num_layers`。每 rank 4batch × 64K、BF16 场景新增约 **4 GB**。
- **Prefill MLA 模式选择**：Lightning Indexer 每个 q token 选出 TopK=2048 个 kv token 后，Prefill MLA 有三种方案：

 | 方案 | 说明 | BMM1 / BMM2 Shape | 瓶颈 |
| ---- | ---- | ---- | ---- |
| 1. MLA Naive + Sparse Mask | 计算完整 Attention，softmax 前屏蔽非 TopK token | `(1*128, 64K, 192, 64K)` / `(1*128, 64K, 64K, 128)` | 与 Full Attention 计算量一致，无 DSA 收益 |
| 2. MLA Naive + Sparse Attention | 每 q token 仅和 TopK=2048 个 kv token 算 | `(1*64K*128, 1, 192, 2048)` / `(1*64K*128, 1, 2048, 128)` | M=1 矩阵乘效率差；HBM 访存量激增 **2048 倍** |
| 3. MLA Absorb + Sparse Attention | Prefill 走 Absorb（与 Decode 一致） | `(1*64K, 128, 576, 2048)` / `(1*64K, 128, 2048, 512)` | 计算量比方案 2 多 3 倍，但 M=128 矩阵乘友好；访存比方案 2 降低几十倍 |

 本实践采用**方案三（MLA Absorb + Sparse Attention）**，Prefill 与 Decode 的 MLA 计算流归一。

### DSA 计算流

DSA 可分为 5 个阶段：

![DSA 融合范围](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/kernel_scope.jpg)
*来源：[`docs/models/deepseek-v3.2-exp/figures/kernel_scope.jpg`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/kernel_scope.jpg)（cann-recipes-infer @ 2f82d10）*

```mermaid
flowchart LR
 In[Hidden] --> MLAP[MLAProlog<br/>Q/KV LoRA + RoPE + Norm<br/>MLA KVCache 写入]
 In --> IP[IndexerProlog<br/>Indexer Q/K proj<br/>Hadamard + 动态量化<br/>Indexer KCache 写入]
 IP --> LI[Lightning Indexer<br/>BatchMatmul Q@K^T + ReLU<br/>× W (GQA-sum) + Top-K 2048]
 LI --> SFA[Sparse Flash Attention<br/>Gather TopK KV + FA]
 MLAP --> SFA
 SFA --> Ep[MLAEpilog<br/>O_proj + V 升维]
```

见 [sparse-flash-attention](../modules/sparse_flash_attention.md)、[lightning-indexer](../modules/lightning_indexer.md) 展开每个模块的计算语义；算子层面见 [lightning-indexer](../kernels/lightning_indexer.md)、[sparse-flash-attention](../kernels/sparse_flash_attention.md)、[indexer-prolog](../kernels/indexer_prolog.md)、[deepseek-indexer-attention](../kernels/deepseek_indexer_attention.md)。

### 部署规格（config/）

| 阶段 | YAML | world_size | 并行 | 量化 | 备注 |
| ---- | ---- | ---- | ---- | ---- | ---- |
| Prefill | `deepseek_v3.2_exp_rank_64_64ep_prefill_benchmark.yaml` | 64 | CP64 + MoE-EP64 | BF16 | `next_n: 3`、`enable_multi_streams: True` |
| Prefill | `deepseek_v3.2_exp_rank_64_64ep_w8a8c8_prefill_benchmark.yaml` | 64 | CP64 + MoE-EP64 | W8A8C8 | `embed/lmhead_tp_size: 16`（单 node HCCS 内 TP） |
| Decode | `deepseek_v3.2_exp_rank_128_128ep_decode_benchmark.yaml` | 128 | DP128 + MoE-EP128 | BF16 | `oproj_tp_size: 4`、`dense_tp_size: 4` |
| Decode | `deepseek_v3.2_exp_rank_128_128ep_w8a8c8_decode_benchmark.yaml` | 128 | DP128 + MoE-EP128 | W8A8C8 | 主 benchmark 配置，`ge_graph` 图模式 |
| Decode | `deepseek_v3.2_exp_rank_128_128ep_w8a8c8_offload_benchmark.yaml` | 128 | DP128 + MoE-EP128 | W8A8C8 | `enable_offload: True` |
| Decode | `deepseek_v3.2_exp_rank_64_64ep_w8a8c8_decode_aclgraph_benchmark.yaml` | 64 | DP64 + MoE-EP64 | W8A8C8 | `acl_graph` 模式 |

> `exe_mode: ge_graph / acl_graph / eager` 三选一（见 [torchair](../frameworks/torchair.md)）。`world_size = 2 × chip_num` 在 A3（两 die 一卡）。

### 模型代码入口

- `models/deepseek-v3.2-exp/models/modeling_deepseek.py` — `DeepseekIndexerAttention` 封装 MLAProlog → Indexer → SFA 调用。
- `models/deepseek-v3.2-exp/models/indexer.py` — `Indexer` 模块同时挂接 AscendC / PyPTO 两条路径（`prefill_decode_ascendc` / `decode_indexer_prolog_pypto`，pypto 路径仅在 decode + int8 KVCache 下启用 `enable_pypto and kv_cache_quant_mode == "int8"`）。
- `models/deepseek-v3.2-exp/models/offload_cache.py` — `OffloadCache` 维护 `selection_kv_block_table` / `selection_kv_block_status`，配合 `npu_gather_selection_kv_cache` 做 Decode 复用判定。
- `models/deepseek-v3.2-exp/models/model_infer.py` — 自研 executor 的 model 入口（与 DeepSeek-R1 同一套 `executor/` 框架）。

## Known Optimizations

来源：`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md` 整体章节。

### 部署总图

![PD 部署总览](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/pd_overview.jpg)
*来源：[`docs/models/deepseek-v3.2-exp/figures/pd_overview.jpg`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/pd_overview.jpg)（cann-recipes-infer @ 2f82d10）*

Prefill 使用 M 个节点、Decode 使用 N 个节点，每节点 8 卡。BF16 场景下根据资源 / SLA，M ∈ [4, 8]、N ∈ [4, 16] 动态调整。

### Prefill 并行策略（选 CP，弃 DP）

> 源："DeepSeek-V3.2-Exp 新增的 DSA 主要面向长序列推理场景，Prefill 阶段设备内存 OOM 风险较高，而且推理服务部署时 TTFT 也会面临巨大的挑战，因此优化内存占用和 TTFT 是并行策略设计的主要目的。"

- 沿用 V3.1 的 Attention DP → 每 rank 都要推理完整长序列，TTFT 高。
- TP 切 Indexer head 轴会引入大量 Reduce 通信（Indexer 对 head 做 ReduceSum）→ 拖慢整网。
- **结论**：Attention 选 **Context Parallel (CP)**，多 rank 均摊长序列计算，单 rank activation/计算量都小，TTFT 可控；MoE 沿用 EP 复用 CP 通信域。

![Prefill 并行拓扑](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/prefill_parallel.jpg)
*来源：[`docs/models/deepseek-v3.2-exp/figures/prefill_parallel.jpg`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/prefill_parallel.jpg)（cann-recipes-infer @ 2f82d10）*

- **Embedding**：TP 切分（tp_size ≤ 1 节点），AllReduce 聚合。
- **Attention**：CP 切分。64K 输入、cp_size 场景下每 rank 处理 `64K / cp_size = 1K` token；KV 算完后 CP 域内 AllGather 得完整 KV，每 rank 用 `1K q × 完整 KV` 做 Attention。
- **因果负载均衡**：简单按 rank 顺序切片会使首 rank 历史 KV 少（计算轻）、尾 rank 历史 KV 多（计算重）。input_ids 按 **cp_size × 2** 切片，每 rank 负责头尾对称两片，LI / SFA 计算前用 Token 重排还原因果顺序。思想与 [zigzag-cp](../parallelism/zigzag_cp.md) 同源。
- **O_proj 局部 TP**：O_proj 内存大，引入 `AllToAll → TP → ReduceScatter`。
- **MoE**：EP 并行，EP 域复用 CP 通信域。
- **LM Head**：TP（tp_size ≤ 1 节点），CP 域 AllGather + Token 重排后喂入 LM Head。

### Decode 并行策略

> 源："Decode 阶段依旧沿用 DeepSeek-V3.1 的部署策略，选用 Attention DP + MoE EP 部署。"

![Decode 并行拓扑](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/decode_parallel.jpg)
*来源：[`docs/models/deepseek-v3.2-exp/figures/decode_parallel.jpg`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/decode_parallel.jpg)（cann-recipes-infer @ 2f82d10）*

- **Attention**：DP（与 V3.1 一致）。
- **O_proj / LM_Head / Embedding**：访存瓶颈下采用**局部 TP**，TP 域**控制在单节点的 HCCS 内**以降低通信开销。YAML `oproj_tp_size: 4`、`dense_tp_size: 4`、`embed_tp_size: 16`、`lmhead_tp_size: 16`（A3 上 tp_size=16 对应单 node 8 卡 × 2 die）。
- **MoE**：EP。Decode 走 `moe_infer_dispatch_combine`（`modeling_deepseek.py:621`，tp+ep mix、`is_prefill` 恒 False）的一体化融合算子 `npu_moe_distribute_dispatch_v2`/`combine_v2`（`:635/:666`），见 [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)。

### MTP（对 DSA 的差异化收益）

DeepSeek-V3.2-Exp 沿用 V3 的 Multi-Token Prediction。但由于 DSA 结构，MTP 在三类算子上的收益不同：

**64K 序列 × 4 batch 搬运量/计算量对比（源文档表）**：

| |
| KV 搬运量 (MB) | Cube 计算量 (GFlops) | QK^T 搬运量 (MB) |
| ---- | ---- | ---- | ---- | ---- |
| MLA | 非 MTP | 144 | 19.33 | 32 |
| MLA | MTP1 | 144 | 38.65 | 64 |
| SFA | 非 MTP | 4.5 | 0.60 | 1 |
| SFA | MTP1 | **9** | 1.21 | 2 |
| LI | 非 MTP | 32 | 2.15 | 16 |
| LI | MTP1 | 32 | 4.29 | **32** |

- **MLA**：KV 搬运量不变，MTP 提升计算访存比 → 算力利用率 >70%。
- **SFA**：MTP1 下 KV 搬运量**翻倍**（每 q token 单独选 TopK=2048），反而增加离散访存代价 —— MTP 对 SFA 难以获得可观收益。
- **LI**：K Cache 搬运与稠密 MLA 类似，MTP 可提高计算访存比。

> 源结论："尽管 Sparse Flash Attention 很难利用 MTP 实现可观的加速效果，但是 Lightning Indexer 算子在长序列场景中耗时占比更高……使用 MTP 对整个推理有比较可观的加速。"

各 decode YAML 默认 `next_n: 3`（MTP3），benchmark 显示平均 3 个 draft token 中 accept 1.44 个。见 [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)。

### 融合 Kernel

DSA 拆分 5 阶段（[lightning-indexer](../kernels/lightning_indexer.md) / [sparse-flash-attention](../kernels/sparse_flash_attention.md) / [indexer-prolog](../kernels/indexer_prolog.md) / [mla-prolog](../kernels/mla_prolog.md)）：

- **Lightning Indexer**：Score BatchMatmul + ReLU + ReduceSum + TopK。长序列下 TopK 成为瓶颈，用 TopK 耗时掩盖其他操作。
- **Sparse Flash Attention**：TopK Gather + FA。瓶颈在离散聚合访存，用访存掩盖其他操作。
- **MLAProlog / IndexerProlog**：Q/KV LoRA + RoPE + Norm + KVCache 更新。存在大量 Cube/Vector 并行流水空间。
- **MLAEpilog**：O_proj + V 升维。

目前 NPU 已开源 **LightningIndexer** 与 **SparseFlashAttention** 两个 AscendC 融合算子，并同时提供 PyPTO / TileLang 实现。

### 量化策略

![W8A8C8 量化架构](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/w8a8c8_quantization.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/w8a8c8_quantization.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/w8a8c8_quantization.png)（cann-recipes-infer @ 2f82d10）*

![量化融合算子细节](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/w8a8c8_quantization_details.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/w8a8c8_quantization_details.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/w8a8c8_quantization_details.png)（cann-recipes-infer @ 2f82d10）*

逐模块策略（源文档）：

- **MLAProlog**：除 `Q_b_proj` 使用 W8A8，其他 Linear 不量化；KVCache 量化到 **C8**（动态 Per-Token-Head-Tile-128）。
- **Sparse Flash Attention**：KVCache Int8 存储，**BF16 计算**（"算 16 存 8"）。
- **IndexerProlog**：除 `Q_b_proj` W8A8，其他 Linear 不量化；Indexer Q **A8**（动态 Per-Token-Head），Indexer Cache **C8**。
- **Lightning Indexer**：BatchMatmul **Int8 计算**。
- **MoE**：路由专家 **W8A8/W4A8**，共享专家 W8A8。
- **MLAEpilog**：O_proj 用 W8A8。
- **LM_Head**：暂不量化。

> 设计选择："IndexerProlog 融合算子设计成 `weights_proj` 出 FP16 且不做量化，因此 MLA 输入关联的 Linear 统一不做量化，好处是可将同一份 BF16 数据输入 IndexerProlog 和 MLAProlog。"

W4A8C8（MoE W4A8 + Attention W8A8C8）针对 V3.2-Exp 用基于学习的量化算法优化 Clamp 参数缓解 W4A8 离群值；相比 W8A8C8 节约 MoE 权重显存 **2×**，大 EP 下可装下更多 expert。见 [w8a8c8](../quantization/w8a8c8.md)、[w4a8c8](../quantization/w4a8c8.md)。

**量化精度**（源表）：

| 模型 | MMLU | GPQA | DROP | MGSM |
| ---- | ---- | ---- | ---- | ---- |
| DeepSeek-V3.2-BF16 | 90.8 | 75.85 | 87.57 | 90.9 |
| DeepSeek-V3.2-Exp-W8A8C8 | 90.62 | 75.90 | 87.41 | 90.87 |
| DeepSeek-V3.2-Exp-W4A8C8 | 90.66 | 76.5 | 87.68 | 91.3 |

### 多流并行优化

MoE 侧：共享专家计算与路由专家的 Gating/Dispatch/计算无依赖，shared expert 走 HBM 带宽瓶颈，Gating（权重小）+ Dispatch（通信算子）的 HBM 占用低，可与 shared expert 并发掩盖。思想与 R1 一致，见 [moe-multi-stream](../techniques/moe_multi_stream.md)。

IndexerProlog 侧：IndexerProlog 内一系列 Cube / Vector 算子可多流并行，见 [indexer-prolog](../kernels/indexer_prolog.md)。

```python
with torchair.scope.npu_stream_switch(stream_tag, stream_priority):
 # shared_expert use another stream
 hidden_states_share = self.shared_experts(hidden_states)
# router_experts use main stream
hidden_states_router = self.router_experts(hidden_states)
hidden_states = hidden_states_share + hidden_states_router
```

由 YAML `enable_multi_streams: True` 使能。

### KVCache Offload

W8A8C8 + 长序列仍受限于设备内存 → 将 MLA Full KVCache 卸载到 Host 内存，释放设备内存提升 batch size。Prefill 阶段只在设备上申请 1 层 MLA KVCache，计算完多流卸载到 Host；Decode 阶段通过新增 `npu_gather_selection_kv_cache` 算子根据 LI TopK index 从 Host 端选 KV 搬回，**利用相邻 token 同层 TopK 命中率（相似度）复用已在设备上的 cache**。详见 [kvcache-offload](../techniques/kvcache_offload.md)、[gather-selection-kv-cache](../kernels/gather_selection_kv_cache.md)。

### weightNZ / PA_NZ

Decode YAML 默认 `enable_weight_nz: True`、`pa_block_size: 128`；见 [weight-nz](../techniques/weight_nz.md)。

## Benchmark

> 源文档 `deepseek_v3.2_exp_inference_guide.md` Benchmark 章节。

### W8A8C8（未启用 Offload）

基于 Atlas A3，MTP3、perfect eplb 配置：

| Global Batch Size | Seq Length | Chips | TPOT (ms) | Throughput (tokens/p/s) |
| ---- | ---- | ---- | ---- | ---- |
| 256 | 65536 | 64 | 19.84 | 202 |
| 512 | 65536 | 64 | 22.78 | 351 |
| 128 | 131072 | 64 | 18.85 | 106 |
| 512 | 131072 | 64 | 25.8 | 310 |

> 平均 3 个 draft token 中 accept 1.44 个。

### V3.2-Exp vs V3.1 长序列吞吐对比

![V3.2-Exp vs V3.1 Benchmark](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/benchmark.jpg)
*来源：[`docs/models/deepseek-v3.2-exp/figures/benchmark.jpg`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/benchmark.jpg)（cann-recipes-infer @ 2f82d10）*

随序列长度增加 V3.2-Exp 优势扩大，**128K 达到 V3.1 的 450%**。

### MoE W4A8 + Attention W8A8C8

| MoE Quant Mode | Global Batch Size | Chips | TPOT (ms) | Throughput (tokens/p/s) |
| ---- | ---- | ---- | ---- | ---- |
| W8A8 | 64 | 32 | 20.81 | 96 |
| W4A8 | 64 | 32 | 20.18 | 99 |
| W8A8 | 32 | 16 | 24.39 | 82 |
| W4A8 | 32 | 16 | 22.51 | 89 |

> 相同序列长度 65536，MTP 及其他配置同上。权重越大、性能提升越明显。

### KVCache Offload

![Offload batch 提升](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/offload_mem_bs.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/offload_mem_bs.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/offload_mem_bs.png)（cann-recipes-infer @ 2f82d10）*

![Offload 序列长度提升](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/offload_mem_seq.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/offload_mem_seq.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/offload_mem_seq.png)（cann-recipes-infer @ 2f82d10）*

- 固定 64K 序列：global batch 1024 → **2048**（翻倍）。
- 固定 batch 128：序列长度 256K → **384K**。

## Future Plan

源文档明示：

- **量化**：低比特量化 + KVCache 量化压缩算法，软硬协同进一步降低时延。
- **KVCache Offload**：利用前后 Token 命中率或跨 layer 预取进一步降低 `GatherSelectionKvCache` 耗时。
- **MegaKernel**：Decode 阶段可借助 PyPTO 实现更大范围 MegaKernel，多核 MPMD 并行调度。

## 架构图（stock HF 基线）

这是 DeepSeek-V3.2-Exp 的 **stock HF 架构**（部署前基线，源自 HF `config.json` + 自带 `inference/model.py` 核实），刻画 ×61 层 block 级前向拓扑与原始模型规格，与本页其余面向 NPU 部署的优化（DSA 融合算子、CP/EP 并行、量化、Offload 等）互补——前者是模型先验，后者是 cann-recipes-infer 在 [atlas-a3](../platforms/atlas_a3.md) 上的部署改造。模型主体即 [mla](../modules/mla.md) + [lightning-indexer](../modules/lightning_indexer.md) 构成的 DSA 注意力（详见上文「DSA 计算流」）。

> 溯源：`deepseek-ai/DeepSeek-V3.2-Exp/config.json`（verified 2026-05-15，`architectures=["DeepseekV32ForCausalLM"]`、`model_type=deepseek_v32`）+ `deepseek-ai/DeepSeek-V3.2-Exp/inference/model.py`（verified 2026-05-15，自带定制推理代码，无标准 HF `modeling_*.py`）。

```mermaid
flowchart TD
    in([input tokens])
    in --> embed["Embed : V → 7168"]

    subgraph block ["Block × 61"]
        direction TB
        n1[RMSNorm]
        attn["DSA Attn<br/><i>MLA + lightning indexer</i>"]
        n2[RMSNorm]
        moe[MoE FFN]
        n1 --> attn
        attn -->|+ residual| n2
        n2 --> moe
    end

    embed --> n1
    moe -->|+ residual| fnorm[RMSNorm]
    fnorm --> head["LMHead : 7168 → V"]
    head --> logits([logits])
```

注意力模块标注为 **DSA Attn**：在自带 `inference/model.py` 中 indexer 作为 `self.indexer` 实例化于 `MLA` 类内、由 `MLA.forward` 调用，indexer 输出的 TopK index 转为 pre-softmax 加性 mask（`scatter(−inf, topk_indices, 0)` 加到 raw attention score 上）。位置 5 的 FFN 按层号交替：第 1–3 层为 dense FFN、第 4–61 层为 MoE FFN（`first_k_dense_replace=3`）。

### 关键参数（stock HF config）

| 模块 | 参数 | 值 |
| ---- | ---- | ---- |
| — | n_layers | 61 |
| — | hidden | 7168 |
| — | vocab | 129280 |
| MLA | n_heads | 128 |
| MLA | q_lora_rank | 1536 |
| MLA | kv_lora_rank | 512 |
| MLA | qk_nope_head_dim | 128 |
| MLA | qk_rope_head_dim | 64 |
| MLA | v_head_dim | 128 |
| Indexer | index_n_heads | 64 |
| Indexer | index_head_dim | 128 |
| Indexer | index_topk | 2048 |
| MoE | n_routed_experts | 256 |
| MoE | n_shared_experts | 1 |
| MoE | top_k | 8 |
| MoE | moe_intermediate | 2048 |
| MoE | dense_layers | 仅第 1–3 层 |
| RoPE | yarn factor | 40（`original_max_pos=4096`） |
| — | max_position_embeddings | 163840 |

> stock HF 的 `inference/model.py` 仅有单个输出 head，`config.json` 的 `num_nextn_predict_layers=1` 在该自带推理代码中**未落地**（无 MTP/NextNPredictor 类）；而本页上文记录的 `next_n: 3`（MTP3）是 cann-recipes-infer 的 NPU 部署在自研 executor 框架下另行实现的推测解码，二者描述不同制品（stock HF 推理 vs. NPU 部署），互补而非冲突。MoE 规格（256+1、top-8、`moe_intermediate=2048`、`noaux_tc`）与 DeepSeek-V3 完全一致，区别仅在注意力身份由 `mla` 变为 `dsa`（MLA + lightning indexer），见 [deepseek-r1](deepseek_r1.md) 的 V3 谱系与 [deepseek-v4](deepseek_v4.md) 的后继 DSA/MQA 演进。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md)（推理总览、并行、MTP、量化、多流、Offload、Benchmark、Future Plan）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_ascendc_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_ascendc_operator_guide.md)（AscendC LI + SFA 融合算子）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md)（PyPTO Indexer Prolog / Deepseek Indexer Attention / Lightning Indexer）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_tilelang_operator_guide.md)（TileLang NPU 适配 + LI/SFA 实现）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v3.2-exp/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek-v3.2-exp/README.md)、`config/*.yaml`（部署规格与环境）、`models/{modeling_deepseek,indexer,offload_cache,model_infer}.py`（调用入口）

## Links

- [atlas-a3](../platforms/atlas_a3.md)
- [ascendc](../frameworks/ascendc.md)
- [pypto](../frameworks/pypto.md)
- [tilelang](../frameworks/tilelang.md)
- [torchair](../frameworks/torchair.md)
- [mla](../modules/mla.md)
- [sparse-flash-attention](../modules/sparse_flash_attention.md)
- [lightning-indexer](../modules/lightning_indexer.md)
- [dsa](../modules/dsa.md)（DSA 顶层架构模式 = MLA 子图 + indexer overlay，V3.2-Exp 是核心验证实例）
- [mla-prolog](../kernels/mla_prolog.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [lightning-indexer](../kernels/lightning_indexer.md)
- [sparse-flash-attention](../kernels/sparse_flash_attention.md)
- [indexer-prolog](../kernels/indexer_prolog.md)
- [deepseek-indexer-attention](../kernels/deepseek_indexer_attention.md)
- [gather-selection-kv-cache](../kernels/gather_selection_kv_cache.md)
- [context-parallel](../parallelism/context_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [data-parallel](../parallelism/data_parallel.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [kvcache-offload](../techniques/kvcache_offload.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [weight-nz](../techniques/weight_nz.md)
- [zigzag-cp](../parallelism/zigzag_cp.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [w4a8c8](../quantization/w4a8c8.md)
- [deepseek-r1](deepseek_r1.md)
- [deepseek-v4](deepseek_v4.md)（后继 DeepSeek-V4 —— DSA/LI 谱系延续，attention 主体由 MLA 改为 MQA/Shared-KV + 滑窗/压缩交错）
- [glm-5](glm_5.md)（GLM-5 结构与本模型一致，cann-recipes 部署方案直接沿用 V3.2-Exp）
- [hixl](../techniques/hixl.md)（长序列 KVCache 卸载 DRAM 后 NPU↔DRAM 高性能传输经 HIXL 单边零拷贝）
- [multi-stream](../techniques/multi_stream.md)（共享专家双流 / Indexer 前处理多流 / KVCache 异步流的方法论总纲）
- [deepseek-v32-pretrain](../../../training/guides/recipes/deepseek_v32_pretrain.md)（跨域：训练侧 DeepSeek-V3.2 TorchTitan 32K 长序列预训练 —— DSA 反向 SLIG/SFAG、自定义 CP for DSA、FSDP2 极致显存部署）

<!-- cannbot:related:start -->
## 相关

- [DSA（DeepSeek Sparse Attention）架构模式](../modules/dsa.md)（`related`）：“DeepSeek-V3.2-Exp 是 DeepSeek 2026 年发布的实验性长序列模型，在 DeepSeek-V3.1 基础上引入 **DeepSeek Sparse Attention (DSA)** —— 由 **Lightning Indexer (LI)** 与 **Sparse Flash Attention (SFA)** 两个核心模块组成 —— 通过"选前 TopK 个相关 token 再计算注意力"将长序列 Attention 从 O(S²) 降至 O(S·TopK)。DSA 的引入保留了完整 MLA KVCache，同时新增 Indexer Key Cache；MoE/MLA 主干继续沿用 V3.1 的结构。”与“｜ DeepSeek V3.2-Exp ｜ `MLA` 内 `self.indexer = Indexer(args)` ｜ `deepseek_v32` ｜ `MLA.forward` 算完 Q/KV 后调用 indexer，把 `topk_indices` 散射成加性 `-inf` mask 累加进注意力分数再 softmax ｜”提供双方正文证据。模型卡给出 DSA 的组成和复杂度收益，DSA 卡补齐 V3.2-Exp 中 indexer 产出 top-k mask 并在 softmax 前叠加的结构合同。
- [DeepSeek-V4](deepseek_v4.md)（`related`）：“DeepSeek-V3.2-Exp 是 DeepSeek 2026 年发布的实验性长序列模型，在 DeepSeek-V3.1 基础上引入 **DeepSeek Sparse Attention (DSA)** —— 由 **Lightning Indexer (LI)** 与 **Sparse Flash Attention (SFA)** 两个核心模块组成 —— 通过"选前 TopK 个相关 token 再计算注意力"将长序列 Attention 从 O(S²) 降至 O(S·TopK)。DSA 的引入保留了完整 MLA KVCache，同时新增 Indexer Key Cache；MoE/MLA 主干继续沿用 V3.1 的结构。”与“DeepSeek-V4 是 DeepSeek 发布的新一代长序列模型，包含 **DeepSeek-V4 Flash（285B）** 与 **DeepSeek-V4 Pro（1.6T）** 两种规格。在 DeepSeek-V3.2 的稀疏 Attention（DSA）基础上，V4 进一步在**层间交错**引入 **KV Cache 滑窗（Window Cache）** 与 **KV Cache 压缩（Compress）**，在保持注意力计算量/访存量低位（相对 Full Cache）的同时大幅提升长序列效率，提供长达 **1M 序列** 的高性能推理。”提供双方正文证据。V4 明确以 V3.2 的 DSA 为演进基线并增加滑窗与压缩，结合两卡可判断模型升级时注意力主体、缓存形态和长序列能力的迁移。
- [GLM-5](glm_5.md)（`related`）：“其网络结构与 ［deepseek-v3.2-exp］(deepseek_v3_2_exp.md) **完全一致**——同款 DeepSeek Sparse Attention (DSA)：MLA 主干 + Lightning Indexer 稀疏选择；因此 cann-recipes-infer 在 GLM-5 上的**并行策略与性能优化方案均直接沿用 V3.2-Exp**（README 明述）。”与“DeepSeek-V3.2-Exp 是 DeepSeek 2026 年发布的实验性长序列模型，在 DeepSeek-V3.1 基础上引入 **DeepSeek Sparse Attention (DSA)** —— 由 **Lightning Indexer (LI)** 与 **Sparse Flash Attention (SFA)** 两个核心模块组成 —— 通过"选前 TopK 个相关 token 再计算注意力"将长序列 Attention 从 O(S²) 降至 O(S·TopK)。”提供双方正文证据。GLM-5 卡明确声明网络同构并直接复用 V3.2-Exp 的并行与优化方案；V3.2-Exp 卡给出被复用的 DSA 基线，因此后者可直接补全前者省略的机制。
<!-- cannbot:related:end -->
