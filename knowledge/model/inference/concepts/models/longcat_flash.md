---
type: Concept
title: LongCat-Flash
description: LongCat-Flash 是美团 2025 年开源（arXiv 2509.01322）的 **560B MoE** 大语言模型，核心架构特色是 **ScMoE（Shortcut-connected MoE）**，每个 Transformer Block 内部存在 "第一段 Attention → FFN → 第二段 Attention → MoE" 的双段结构，天然存在可并行的计算路径。模型结构中与 Llama 类似的部分沿用通用优化点（固定 KV Cache 大小、cos/sin 优化、AddRMSNorm 融合）。 cann-recipes-infer 在 Atlas A3 上基于自研 `executor/` 推理框架对 LongCat-Flash 进行推理优化：除了沿用 DeepSeek-R1 的 MLA 融合算子 + EP MoE + 图模式 + SuperKernel + MTP 外，还引入了 **多流并行与控核**、**权重预取**、**o_proj TP K 轴切分**、**MLA KVP 切分**、**MLP dense-TP**、以及面向 Decode TPOT 极致优化的 **Attention-FFN Disaggregation (AFD)**，使能 AFD 后 TPOT 迈入 10 ms 内。 （MLA KVP 部署已于 2026-05 回退，kvp8 YAML/新 ParallelConfig.kvp_size 字段/优化文档移除，legacy modeling 代码残留）
tags:
- task.design
- topic.model_architecture
- topic.attention
- topic.mixture_of_experts
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/longcat_flash_optimization.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- a3
---

# LongCat-Flash

## Summary

LongCat-Flash 是美团 2025 年开源（arXiv 2509.01322）的 **560B MoE** 大语言模型，核心架构特色是 **ScMoE（Shortcut-connected MoE）**，每个 Transformer Block 内部存在 "第一段 Attention → FFN → 第二段 Attention → MoE" 的双段结构，天然存在可并行的计算路径。模型结构中与 Llama 类似的部分沿用通用优化点（固定 KV Cache 大小、cos/sin 优化、AddRMSNorm 融合）。

cann-recipes-infer 在 Atlas A3 上基于自研 `executor/` 推理框架对 LongCat-Flash 进行推理优化：除了沿用 DeepSeek-R1 的 MLA 融合算子 + EP MoE + 图模式 + SuperKernel + MTP 外，还引入了 **多流并行与控核**、**权重预取**、**o_proj TP K 轴切分**、**MLA KVP 切分**（部署已于 2026-05 回退，legacy 代码残留；详见「MLA KVP 切分优化」节）、**MLP dense-TP**、以及面向 Decode TPOT 极致优化的 **Attention-FFN Disaggregation (AFD)**，使能 AFD 后 TPOT 迈入 10 ms 内。

### Highlights

- **多流并行 + 控核**：针对 ScMoE 四段拆分，stage1 不控核、stage2 分流（stream0 `c16v32`、stream1 `c8v16`）使双流计算时间接近（见 [moe-multi-stream](../techniques/moe_multi_stream.md)（LongCat-Flash ScMoE 变体））
- **权重预取**：`npu_prefetch` 对 QBMM / MLAProlog / Matmul 等访存 bound 算子提前搬权重到 L2 Cache（见 [weight-prefetch](../techniques/weight_prefetch.md)）
- **MLA + 融合算子**：`npu_mla_prolog_v3` + `npu_fused_infer_attention_score`，与 [deepseek-r1](deepseek_r1.md) 共同依赖
- **o_proj TP K 轴切分**：`attn_output` 走 `all_to_all` + 局部线性 + `reduce_scatter`（`o_proj_tp_size` 开关）
- **MLA KVP 切分**（部署已于 2026-05 回退）：长序列 KV Cache 沿 S 维度切到多 rank，Decode 走 `softmax_lse_flag` + `npu_attention_update` 归约（见 [kvp](../parallelism/kvp.md)；「MLA KVP 切分优化」节 ⚠️ 标回退范围）
- **MoE EP + 零计算专家**：`dispatch_v2`/`combine_v2`（[moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)）的 `copy_expert_num` 支持零专家 `MoE(x) = x`
- **Dense TP8**：MLP `gate_up_proj` N 轴切 + `down_proj` K 轴切，DP→TP→DP 的 AllGather + ReduceScatter
- **MTP1 / MTP2**：`next_n=1/2` 使能
- **AFD (Attention-FFN Disaggregation)**：Decode 阶段 Attention 与 MoE 分节点部署，Send/Recv 走 SDMA 不占 Vector Core，解除控核约束，AFD 场景下 **TPOT 9.5 ms @ W8A8 GBS=256 Seq=4608 64 Chips**（见 [afd](../techniques/afd.md)）

## Architecture And Serving Traits

### ScMoE 双段结构与多流拆分

LongCat-Flash 原论文提供了四阶段的并行策略，方案图如下（源图原貌）：

![LongCat-Flash 原始 overlap 策略](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/longcat-flash/figures/overlap_strategy.png)
*来源：[`docs/models/longcat-flash/figures/overlap_strategy.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/figures/overlap_strategy.png)（cann-recipes-infer @ 2f82d10）*

本实践对并行策略进行了调整，**将第二段 attention 和 FFN 专家提前执行，并通过控制多流上的 ai core 和 vector core 核数**，使得双流的计算时间接近，无明显拖尾，提升性能：

- stage1：不做控核，默认占用全部 ai core 和 vector core 核数；
- stage2：stream0 采用 `c16v32`，stream1 采用 `c8v16`。

![LongCat-Flash 多流 + 控核方案](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/longcat-flash/figures/multi_stream_limit_core_num.png)
*来源：[`docs/models/longcat-flash/figures/multi_stream_limit_core_num.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/figures/multi_stream_limit_core_num.png)（cann-recipes-infer @ 2f82d10）*

详见 [moe-multi-stream](../techniques/moe_multi_stream.md)（LongCat-Flash ScMoE 变体）。

### 支持的规格（Atlas A3）

| 配置文件 | world_size | 并行策略 | 量化 | 关键开关 |
| ---- | ---- | ---- | ---- | ---- |
| `longcat_flash_densetp8_ep32.yaml` | 32 | dense_tp=8, oproj_tp=1, moe_ep=32 | BF16 | eager/`moe_chunk_max_len: 1024` |
| `longcat_flash_densetp8_ep32_gegraph_mtp.yaml` | 32 | dense_tp=8, oproj_tp=8, moe_ep=32 | BF16 | `ge_graph` + `next_n: 1` |
| `longcat_flash_densetp8_ep32_kvp8_gegraph_w8a8.yaml` ⚑ | 32 | dense_tp=8, oproj_tp=8, `kvp_size=8`, moe_ep=32 | W8A8 | KVP 长序列，`input_max_len: 131072` |
| `longcat_flash_densetp8_ep64_gegraph_mtp2_eplb_afd_w8a8.yaml` | 128 | dense_tp=8, oproj_tp=8, moe_ep=64 | W8A8 | `enable_afd: True` + `next_n: 2` + `perfect_eplb: True` + `enable_superkernel: True` + `enable_prefetch: True` |
| `longcat_flash_densetp8_ep128_gegraph_mtp_eplb_w8a8.yaml` | 128 | 同上（无 AFD） | W8A8 | 标准 ge_graph + MTP + eplb |

> ⚑ `kvp8` 配置（`config/longcat_flash_densetp8_ep32_kvp8_gegraph_w8a8.yaml` 及 `config/ci/longcat_flash_densetp8_ep16_kvp8_gegraph_w8a8.yaml`）**已于 2026-05 回退删除**，HEAD@2c45117 不再 ship 该 YAML，列于此处仅记录回退前可用规格（详见「MLA KVP 切分优化」节 ⚠️）。

> 约束：当 `kvp_size > 1` 时 `attn_tp_size == 1`、`o_proj_tp_size == kvp_size`（**KVP 部署已于 2026-05 回退**，此约束属回退前；legacy `modeling_longcat_flash.py` 代码仍保留但无 shipped 配置触发）；AFD 与 `enable_multi_stream` 不叠加（YAML 注释：`AFD scenario will not take effect.`）；当前 Send/Recv 单次通信只支持 **1:1**（M == N），不支持 M:N 部署（README 声明）。

### 权重转换

```bash
# BF16 → W8A8
python models/longcat-flash/utils/convert_model.py \
 --input_bf16_hf_path /data/models/LongCat-Flash-Chat \
 --output_hf_path /data/models/LongCat-Flash-Chat-W8A8
```

## Known Optimizations

所有优化默认基于 Atlas A3、自研 `executor/`、`models/longcat-flash/models/modeling_longcat_flash.py`（优化文档见 Evidence）。

### 通用优化

LongCat-Flash 结构中的与 Llama 类似的部分，可参考通用优化点 [Llama](https://gitcode.com/Ascend/torchair/tree/41af5b5871232805a670bd62527e4d0a7b7ab446/npu_tuned_model/llm/llama) 的改动，如**固定 KV Cache 大小、cos/sin 优化、AddRMSNorm 融合**等。

### 使能图模式

使用静态图可以获得更好的推理性能。`LongcatFlashRunner` 通过覆写 `executor/model_runner.py` 中的 `ModelRunner` 的 `graph_compile` 函数，将模型编译为静态图，**当前暂不支持 acl_graph**。

#### 图编译缓存（含 MTP 特殊处理）

`torch.compile` 是一种即时编译器（Just-In-Time compiler），成图首次编译时间通常较长，在时延敏感的模型推理场景下，使能图编译缓存可以缓存编译后的静态图，有效缩短服务启动后的首次推理时延。

```python
if self.enable_cache_compile:
 case_name = "compile_cache/" + os.getenv("CASE_NAME")
 cache_model = self.model.decode
 if self.is_mtp:
 case_name += "_spec"
 cache_model = self.model.mtp_compile_decode
 cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), case_name)
 self.model.decode = tng.inference.cache_compile(cache_model, cache_dir=cache_dir,
 config=compiler_config, dynamic=False, fullgraph=True, ge_cache=True)
```

主模型缓存默认路径为 `./compile_cache/CASE_NAME`，**mtp 模型缓存默认路径为 `./compile_cache/CASE_NAME_spec`**（这是与 R1 的一个差异）。

### 多流并行与控核

大模型推理场景下，对于一些可并行的场景，可以划分多个 stream 做并行计算，多个 stream 上的计算形成 overlap，从而降低整体计算耗时。

多流场景下，会出现所有核（Core）都被一个流占用的情况，导致算子执行并行度降低，因此需要把核分给不同的流用，从而保证算子并行执行的收益。

核心伪代码：

```python
attn
layernorm
with npu_stream_switch(True, "1"):
 with limit_core_num(True, "8", "16"):
 router
 dispatch
 gmm
 combine
with limit_core_num(True, "16", "32"):
 dense
 attn
 layernorm
 dense
```

详见 [moe-multi-stream](../techniques/moe_multi_stream.md)（LongCat-Flash ScMoE 变体）。

### 权重预取

该优化提供网络 weight 预取功能，在算子计算的同时，利用空闲的带宽，提前将一些访存 bound 算子的权重从 HBM 搬运到 L2 Cache 中。`npu_prefetch` 优化功能可通过 `enable_prefetch` 开关使能。

LongCat-Flash 对访存 bound 的算子如 **QuantBatchMatmul (QBMM)、MLAProlog、Matmul** 提前预取了对应的权重。其中 MLAProlog 算子包含了多个矩阵乘计算，搬运 bound 较大，因此提前预取了前置的 QBMM 的权重，为 MLAProlog 提供了更大的预取空间，获取较大的性能收益。具体的预取大小及预取位置，可在 `models/modeling_longcat_flash.py` 中搜索 `npu_prefetch` 接口查看。

详见 [weight-prefetch](../techniques/weight_prefetch.md)。

### 使能 SuperKernel

SuperKernel 优化功能在 decode 启用 `ge_graph` 图模式的场景下，根据用户定义的范围对模型的计算图进行优化。将通过 `enable_superkernel` 开关使能，可将部分算子优化在一个 SuperKernel scope 内。**由于 LongCat-Flash 在不同流上采取了不同的分核策略，按照分核、分流的范围标定各 SuperKernel scope 的范围即可。**

![LongCat-Flash SuperKernel scope 范围](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/longcat-flash/figures/superkernel.png)
*来源：[`docs/models/longcat-flash/figures/superkernel.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/figures/superkernel.png)（cann-recipes-infer @ 2f82d10）*

详见 [superkernel](../techniques/superkernel.md)。

### MLA 低秩压缩优化

Decode 阶段参考 [DeepSeek 论文](https://arxiv.org/pdf/2405.04434) 中提及的低秩压缩方法，可以减少 KV Cache 占用的内存，提升推理效率，相关实现可以参考 `LongcatFlashAttention` 类中的 `forward_page_attention_absorb` 函数。**MLA 整体采用 Data Parallelism (DP) 数据并行，并针对 `o_proj` matmul 单独采用 Tensor Parallelism (TP) 切分提升性能。**

#### 融合算子优化

- **MLA 前置计算性能优化**：使能 [mla-prolog](../kernels/mla_prolog.md) (`npu_mla_prolog_v3`) 融合 kernel，替换 attention 计算前的计算，其中包含 Q、K、V 的线性层计算、旋转位置编码 (ROPE)、RmsNorm 计算及 KV Cache 更新等计算处理；
- **Attention 性能优化**：使能 [fused-infer-attention-score](../kernels/fused_infer_attention_score.md) (`npu_fused_infer_attention_score`) 融合 kernel，实现对 MLA 计算的加速。

#### o_proj Tensor Parallelism K 轴切分

对线性层 `o_proj` 进行行切分处理，`o_proj` 的输入维度为 `num_heads * v_head_dim`，输出维度为 `hidden_size`。在进行 o_proj TP 时，将这一输入维度按照 `o_proj_tp_size` 进行切分，要求 `num_heads * v_head_dim` 能被 `o_proj_tp_size` 整除，**每个 rank 上只保存一部分输入通道对应的权重**。

在推理过程中：
1. `attn_output` 先经过 `all_to_all`，使得每个 rank 只拿到自己负责的那一段输入特征；
2. 每个 rank 对局部张量执行线性层变换，得到局部输出；
3. 最后通过 `reduce_scatter` 对各 rank 的局部输出按元素求和，并在 batch 维度切分，得到各 rank 的输出。

![LongCat-Flash o_proj TP K 轴切分](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/longcat-flash/figures/o_proj_tp.png)
*来源：[`docs/models/longcat-flash/figures/o_proj_tp.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/figures/o_proj_tp.png)（cann-recipes-infer @ 2f82d10）*

### MLA KVP 切分优化（长序列） ⚠️ 部署已回退

> ⚠️ **KVP 部署已于 2026-05 回退**：kvp8 部署 YAML（`longcat_flash_densetp8_ep{16,32}_kvp8_gegraph_w8a8.yaml`）、新 `ParallelConfig` 的 `kvp_size` 字段（`executor/core/config/inference_config.py`）、优化文档 KVP 章节（含 `figures/kvp.png`）、README「长序列 OOM」的 KVP 小节、`config/README.md` / `docs/common/inference_config_guide.md` 的 `kvp_size` 条目均移除；`model_setting.py:check_and_update_vars` 新增 `if "kvp_size" in parallel_config: raise ValueError("kvp_size is removed; longcat KVP is temporarily disabled")` 守卫。HEAD@2c45117 不再有 KVP 部署/文档（commit/MR 溯源见 Evidence）。
> 但 **legacy `modeling_longcat_flash.py` 仍保留 `kvp_size` 处理**（`runner_settings.get("parallel_config").get("kvp_size", 1)`，默认 1，legacy `ModelRunner` 路径；`kvp_rank` / `kvp_group`（`kvp_size==1` 时为 `None`）/ slot_mapping 轮转 / `softmax_lse_flag` / `_all_to_all_along_headdim` / `o_proj` `all_reduce` 等 `kvp_size > 1` 分支均未删，仅 `kvp_group` init 收束到 `kvp_size > 1` 才建组），未对外暴露/无对应 shipped 配置。以下机制为回退前 KVP 实现，保留作历史/机制参考。

KVP 特性旨在面向**长序列推理场景**，通过将 KV Cache 沿 S 维度切分到多个 rank 上，缓解单 rank 的 KV Cache 访存压力，从而降低时延。**KVP 特性暂未支持 Multi-Token Prediction 投机推理**（属回退前描述）。

- **Prefill 阶段**：根据 `kvp_size` 和 `kvp_rank` 对 `slot_mapping` 进行切分，并将 `slot_mapping` 作为 `npu_kv_rmsnorm_rope_cache` 算子的 index 参数，将完整的 KV Cache 分片**轮转**写入到各个 `kvp_rank` 上，每个 `kvp_rank` 上存储 `1/kvp_size` 长度的 KV Cache；此外，Prefill 阶段在计算 Attention 时复用了 `kvp_size`，同时约束 `attn_tp_size = 1`，对 `npu_fused_infer_attention_score` 算子的输入 Q、K、V 按头维度进行 TP 切分。
- **Decode 阶段**：启用 `npu_fused_infer_attention_score` 算子的 `softmax_lse_flag` 功能，输入 Q、K、V 头维度保持完整，与各个 `kvp_rank` 上存储的部分 KV Cache 进行 Attention 计算，并输出相应的 softmax lse，每个 `kvp_rank` 拿到完整 `num_heads_per_rank` 个 Q head 对部分 KV Cache 的计算结果 `attn_partial` 和 `lse_partial`；通过 `_all_to_all_along_headdim` 从各个 `kvp_rank` 拿到 `kvp_size` 份 `num_heads_per_rank // kvp_size` 个 Q head 对各个部分 KV Cache 的计算结果 `attn_scatter` 和 `lse_scatter`，并通过 `npu_attention_update` 算子对 `attn_scatter` 和 `lse_scatter` 执行归约操作。Decode 阶段 `actual_seq_lengths_kv` 表示当前 `kvp_rank` 实际存储的 KV Cache 长度，因此需要根据 `kvp_size` 和 `kvp_rank` 进行调整。
  > 注：归约算子 `npu_attention_update` 系回退前 optimization 文档描述；HEAD 代码实际以内联 `(attn_scatter * lse_scatter.softmax(dim=0)).sum(dim=0)` 实现 lse-softmax 归约（`modeling_longcat_flash.py`，无算子调用）。
- **o_proj 配合约束**：使能 KVP 特性的场景下（`kvp_size > 1`），新增 `o_proj_tp_size = kvp_size` 约束，在 `o_proj_forward` 中配合执行 o_proj TP 切分并后续执行 `all_reduce` 通信。

![LongCat-Flash KVP 切分示意](https://raw.gitcode.com/AndyKong2020/CANN-Infer-Wiki/raw/60b3e9fc6bec92ca4bb90dd2b4c27ae3557c8295/wiki/static/cann-infer/assets/parallelism/kvp/kvp.png)
*来源：[`docs/models/longcat-flash/figures/kvp.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/figures/kvp.png)（cann-recipes-infer @ 2f82d10）*

详见 [kvp](../parallelism/kvp.md)。

### MoE (Mixture of Experts) 模块实现 Expert Parallel (EP) 及使能融合算子

MoE 计算阶段采用 EP (Expert Parallelism) 切分策略，将**路由专家和零计算专家**均匀分布到每张卡上。

#### Router 使能融合算子

使用 [`torch_npu.npu_moe_gating_top_k`](https://www.hiascend.com/document/detail/zh/Pytorch/720/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_gating_top_k.md) 算子，对 router 计算的结果排序，并选取前 top-k 个专家。

#### Prefill 阶段优化

Prefill 阶段路由专家采用 **Double-Routing** 的计算策略完成计算，具体计算步骤可参见 [double-routing](../techniques/double_routing.md)（沿用 DeepSeek-R1 Prefill 方案）。

#### Decode 阶段优化

- **高性能专家计算**：使用 [`torch_npu.npu_grouped_matmul`](https://www.hiascend.com/document/detail/zh/Pytorch/720/apiref/torchnpuCustomsapi/context/torch_npu-npu_grouped_matmul.md) 算子，可以同时处理多个专家的计算，提高计算和搬运效率；
- **多卡间高性能通信路由**：使能 [`torch_npu.npu_moe_distribute_dispatch_v2`](https://www.hiascend.com/document/detail/zh/Pytorch/720/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_distribute_dispatch_v2.md) 和 [`torch_npu.npu_moe_distribute_combine_v2`](https://www.hiascend.com/document/detail/zh/Pytorch/720/apiref/torchnpuCustomsapi/context/torch_npu-npu_moe_distribute_combine_v2.md) 算子，实现 EP 并行下多卡间的通信。**通过传入参数 `copy_expert_num` 使能 dispatch_v2 和 combine_v2 算子支持零专家处理**，计算公式为：`MoE(ori_x) = ori_x`。在使用前可参考上述的算子文档，检查 `HCCL_BUFFSIZE` 等环境变量的配置是否合理。

### MLP 线性层优化

#### MLP 线性层计算合并

原始 `LongCatFlashMLP` 实现中，存在 `gate_proj`、`up_proj` 与 `down_proj` 三个 matmul 运算，可通过将 `gate_proj` 与 `up_proj` 进行合并计算，得到 `gate_up_proj` 提升整体计算效率。

#### MLP 线性层 TP 切分

在 MLP 的计算中，`gate_up_proj` 和 `down_proj` 需要全量存储到每一个 device 上，造成 device 内存压力。本优化将：

- `gate_up_proj` 沿 **N 轴**切分
- `down_proj` 沿 **K 轴**切分

到 `dense_tp` 域内的不同 device 上，以完成 MLP 线性层的 TP 切分，降低单个 device 的内存使用，并减少 matmul 矩阵运算时的权重搬运开销。需要注意的是，**MLP 阶段采用 TP 切分，但前后的 Attention 模块采用的是 DP 切分**，在 MLP 计算之前和之后需要分别进行 AllGather 和 ReduceScatter，完成 **DP → TP → DP** 的并行方式转化。虽然有额外的通信开销，但整体仍有较好的性能收益。**在当前的优化实践中，Dense FFN 专家采用 TP8 切分。**

![LongCat-Flash Dense TP8 切分](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/longcat-flash/figures/dense_tp.png)
*来源：[`docs/models/longcat-flash/figures/dense_tp.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/figures/dense_tp.png)（cann-recipes-infer @ 2f82d10）*

### 支持 Multi-Token Prediction (MTP)

实现了 MTP 投机推理，在未达到计算 bound 的场景下，MTP 计算可以实现较好的推理加速效果。可通过 `next_n` 参数使能 MTP。**当前支持了 MTP1，MTP2。** 见 [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)。

### Attention-FFN Disaggregation (AFD)

LongCat-Flash 独有的 Decode 极致时延优化。在非分离场景中，Attention 与 MoE 部署在同一卡上，stage2 的双流控核约束了 Cube/Vector 核数；使能 AFD 后 Attention / MoE 分节点部署，Send/Recv 走 SDMA 不占 Vector 核，Attention 侧算子解除控核约束耗时大幅下降，配合 FFN 侧 GMM/Matmul 权重预取减少通信拖尾。

**AFD 场景下 TPOT 9.5 ms**（W8A8，GBS=256，Seq=4608，64 Chips），相比同配置非分离 TPOT 9.95 ms 有进一步改善，且吞吐更高。

详见 [afd](../techniques/afd.md)。

## Benchmark

基于 Atlas A3 环境，本实践对 LongCat-Flash W8A8 量化版本进行了性能 Benchmark 测试。**在使能 AFD 特性后，模型的 TPOT 迈入了 10 ms 之内**，并且相比于同样卡数和 global batch size 的不分离场景，拥有更优的 TPOT 和吞吐。

| Enable AFD | Quant Mode | Global Batch Size | Seq Length | Chips | TPOT (ms) | Throughput (tokens/p/s) |
| ---- | ---- | ---- | ---- | ---- | ---- | ---- |
| N | W8A8 | 512 | 4608 | 64 | 10.37 | 771.46 |
| N | W8A8 | 256 | 4608 | 32 | 10.64 | 751.88 |
| N | W8A8 | 256 | 4608 | 64 | 9.95 | 402.01 |
| Y | W8A8 | 256 | 4608 | 64 | **9.5** | **421.05** |

> 1. 性能数据基于 **MTP2 与 perfect eplb** 配置采集。
> 2. 当前 CANN 软件版本下，SuperKernel 标记范围内的部分算子尚不支持完全融合，将在后续社区版本中得到解决。
> 3. 由于当前 Send/Recv 算子**单次通信只支持 1:1** 的发送/接收模式，不支持 M:N 模式，所以 AFD 场景部署时 Attention Instance 的 Node 个数和 FFN Instance 的 Node 个数是一样，也即 M == N；后续会计划支持 M:N 的部署模式。

## 长序列 OOM 处理

1. 长序列请求可能导致 device 内存 OOM，尤其是在 prefill 阶段，MoE 的 Routing 分发可能存在极端负载不均，导致个别卡上的 `grouped_matmul` 算子占用较大内存。为缓解此问题，可采用 **Chunk MoE 推理**，在 MoE 切 Chunk 串行推理，降低极端场景下的峰值内存，可通过 YAML 中的 `moe_chunk_max_len` 开关设置 chunk 的大小。当前该开关只针对 prefill 生效。
2. 长序列请求的 KV Cache 内存占用过大，可使能 **KVP 特性**（`kvp_size`）将长序列的 KV Cache 沿 S 维度交错式存储至多个 rank，见 [kvp](../parallelism/kvp.md)。
   > ⚠️ **此 KVP OOM 处理项已于 2026-05 从 README 回退**（HEAD@2c45117 README 仅保留 Chunk MoE 一项）；保留作回退前长序列 OOM 缓解方案的机制参考，详见「MLA KVP 切分优化」节。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/longcat-flash/longcat_flash_optimization.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/longcat-flash/longcat_flash_optimization.md)（11 大章节：通用优化 / 图模式 / 图编译缓存 / 多流并行与控核 / 权重预取 / SuperKernel / MLA 低秩压缩 + o_proj TP / KVP / MoE EP / MLP 合并与 TP / MTP / AFD）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/longcat-flash/README.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/README.md)（benchmark 表、长序列 OOM 处理、Send/Recv 1:1 约束）；`models/longcat-flash/config/*.yaml`（5 份默认 + 3 份 CI 部署配置）；`models/longcat-flash/models/modeling_longcat_flash.py` / `ffn.py` / `mtp.py`（`LongcatFlashAttention.forward_page_attention_absorb`、MoE forward、`npu_prefetch`、`npu_stream_switch`、`limit_core_num`、`superkernel_scope` 使用处）；`models/longcat-flash/runner_longcat_flash.py`（主 runner）；`models/longcat-flash/utils/convert_model.py`（BF16 → W8A8 权重转换）
- 原始模型：Meituan LongCat-Flash-Chat HF repo（`meituan-longcat/LongCat-Flash-Chat`）；论文 arXiv 2509.01322（四阶段并行策略来源）
- **KVP 部署回退**（!501 / b085e02，2026-05，「回退 longcat kvp 特性开关与介绍文档」）：删除 [`config/longcat_flash_densetp8_ep32_kvp8_gegraph_w8a8.yaml`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/longcat-flash/config/longcat_flash_densetp8_ep32_kvp8_gegraph_w8a8.yaml) 与 `config/ci/longcat_flash_densetp8_ep16_kvp8_gegraph_w8a8.yaml`、`executor/core/config/inference_config.py` 的 `ParallelConfig.kvp_size` 字段+校验、`docs/models/longcat-flash/longcat_flash_optimization.md` 的「MLA KVP 切分优化」整节+`figures/kvp.png`、README 长序列 OOM 的 KVP 小节、`config/README.md` 与 `docs/common/inference_config_guide.md` 的 `kvp_size` 条目；新增 `models/longcat-flash/models/model_setting.py:check_and_update_vars` 守卫 `raise ValueError("kvp_size is removed; longcat KVP is temporarily disabled")`。**legacy 残留**：[`models/longcat-flash/models/modeling_longcat_flash.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat-flash/models/modeling_longcat_flash.py) @2c45117 仍含 `kvp_size`（L178/560/1562 `runner_settings...get("kvp_size", 1)`）、`kvp_rank`/`kvp_group`（L589-590；L1619-1624 `kvp_group` 仅 `kvp_size > 1` 建组否则 `None`）、slot_mapping 轮转（L1372-1374）、`softmax_lse_flag`（L1022）、`_all_to_all_along_headdim`（L1038）、`o_proj` `all_reduce`（L709-710）等 `kvp_size > 1` 分支

## Links

- [longcat-flash-lite](longcat_flash_lite.md)（减配验证模型：保留 MoE+MLA+N-gram Embedding 核心结构、缩小层/expert 数，A2/A3 单节点冷启动优化）
- [atlas-a3](../platforms/atlas_a3.md)
- [torchair](../frameworks/torchair.md)
- [ascendc](../frameworks/ascendc.md)
- [mla](../modules/mla.md)
- [mla-prolog](../kernels/mla_prolog.md)
- [fused-infer-attention-score](../kernels/fused_infer_attention_score.md)
- [tensor-parallel](../parallelism/tensor_parallel.md)
- [expert-parallel](../parallelism/expert_parallel.md)
- [data-parallel](../parallelism/data_parallel.md)
- [kvp](../parallelism/kvp.md)
- [afd](../techniques/afd.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)（LongCat-Flash ScMoE 变体）
- [weight-prefetch](../techniques/weight_prefetch.md)
- [superkernel](../techniques/superkernel.md)
- [double-routing](../techniques/double_routing.md)
- [moe-dispatch-combine-v2](../techniques/moe_dispatch_combine_v2.md)
- [mtp-speculative-decoding](../techniques/mtp_speculative_decoding.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [multi-stream](../techniques/multi_stream.md)（多流编排/控核方法论总纲；LongCat ScMoE 多流+控核+AFD 为代表案例）

## 已知冲突

- [kvp](../parallelism/kvp.md)

<!-- cannbot:related:start -->
## 相关

- [LongCat-Flash-Lite](longcat_flash_lite.md)（`related`）：“LongCat-Flash 是美团 2025 年开源（arXiv 2509.01322）的 **560B MoE** 大语言模型，核心架构特色是 **ScMoE（Shortcut-connected MoE）**，每个 Transformer Block 内部存在 "第一段 Attention → FFN → 第二段 Attention → MoE" 的双段结构，天然存在可并行的计算路径。”与“LongCat-Flash-Lite 是 ［longcat-flash］(longcat_flash.md) 的**减配验证模型**：保留 **MoE + MLA + N-gram Embedding** 核心结构，但层数、expert 数与若干配置缩小到适合**单节点 8 卡（A2 / A3）冷启动优化**的规模（顶层类 `LongcatFlashNgramForCausalLM`，`model_type="longcat_flash_ngram"`）。”是双方正文中的具体合同。满配卡定义 ScMoE 双段结构，Lite 卡明确自己由该模型缩小并保留 MoE、MLA 与 N-gram 核心，互读可区分共享架构与不同部署规模。
<!-- cannbot:related:end -->
