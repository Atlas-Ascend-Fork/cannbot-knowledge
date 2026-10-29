---
type: Concept
title: Indexer Prolog Kernel
description: '`Indexer Prolog` 是 LightningIndexer 之前的准备算子，为 LI 提供输入 q、weight、q_scale，处理
  Indexer Q / Indexer Cache(K) / Indexer Weight 三条独立计算流（Q 不含 LayerNorm，K 含 LayerNorm；Q/K 涉及 RoPE、Hadamard 与动态量化，Weight 仅投影与缩放且不量化）。DeepSeek-V3.2-Exp(DSA)：PyPTO 单一大融合算子 npu_lightning_indexer_prolog_pto，4
  batch×MTP1×64K 逼近理论极限（Indexer Q 四段理论拆解、瓶颈在搬运、Q 掩盖 Cache/Weight）；配合 torchair npu_stream_switch
  多流。DeepSeek-V4 适配（PyPTO）：IndexerProlog 仅出现在 compress_ratio=4 的 CSA 层（C128A/HCA 无
  LI 模块，代码 cmp_ratio:4 only c4a have li module）。Query q_hadamard/Quant 流程：q_tmp=qr@idx_wq_b·scale
  → q_hadamard=Cat(q_tmp[:,:nope_dim],Rope(q_tmp[:,nope_dim:]))@hadamard → q,q_scale=Quant；代码实际展开为
  wq_b→inplace_partial_rotary_mul(interleave)→rotate_activation(hadamard_matrix=get_had_pow2)→量化（int8
  走 npu_dynamic_quant 转 FP16 / FP8 走 npu_dynamic_block_quant）。Weights=x@weights_proj·1/sqrt(idx_nq·head_dim)（代码
  softmax_scale=head_dim**-0.5·n_heads**-0.5 一致），不量化转 FP16/FP32。doc 描述 fused 而 code
  为展开步骤（V4 图模式是否回落单一融合 PyPTO 算子源未明示，待验证）。'
tags:
- task.implementation
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/README.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md
  role: supporting
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-22T10:35:31Z'
platforms:
- a3
- '950'
---
# Indexer Prolog Kernel

## Summary

`Indexer Prolog` 是 [lightning-indexer](lightning_indexer.md) 之前的准备算子，为 LI 计算提供输入 `q`、`weight`（及 `q_scale`）。它处理三条独立计算流 —— **Indexer Q**、**Indexer Cache (K)**、**Indexer Weight** —— 三条流的操作并不相同：Q 流无 LayerNorm，K 流有 LayerNorm，Q/K 流进行相应 RoPE、Hadamard 与动态量化，Weight 流仅投影、缩放而不量化。

- **DeepSeek-V3.2-Exp（DSA）**：cann-recipes-infer 通过 **PyPTO** 实现为单一大融合算子 `npu_lightning_indexer_prolog_pto`，典型 Shape（4 batch × MTP1 × 64K）下已**逼近理论极限性能**。PyPTO 源码：`ops/pypto/src/lightning_indexer_prolog_pto/op_kernel/`。
- **DeepSeek-V4**：IndexerProlog **仅出现在 `compress_ratio = 4` 的 CSA 层**（C128A/HCA 层无 LI 模块），Query 计算走 q_hadamard / Quant 流程（int8 或 FP8），见 [DeepSeek-V4 适配](#deepseek-v4-适配pypto)。

## Role In Pipeline

![Indexer Prolog 计算流程](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/IndexerPrologQuant.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/IndexerPrologQuant.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/IndexerPrologQuant.png)（cann-recipes-infer @ 2f82d10）*

在 `models/deepseek-v3.2-exp/models/indexer.py:L184` 处入口：

```python
res = torch.ops.custom_pypto.npu_lightning_indexer_prolog_pto(
 token_x=x.view(-1, self.dim),
 q_norm=qr.view(-1, self.q_lora_rank),
 q_norm_scale=c8_input_dict.get("pertoken_scale", None),
 wq_b=self.wq_b.weight, wq_b_scale=self.wq_b.weight_scale,
 wk=self.wk.weight,
 weights_proj=self.weights_proj.weight,
 ln_gamma_k=self.k_norm.weight, ln_beta_k=self.k_norm.bias,
 cos_idx_rope=cos.squeeze(1).squeeze(1),
 sin_idx_rope=sin.squeeze(1).squeeze(1),
 hadamard_q=self.hadamard_matrix, hadamard_k=self.hadamard_matrix,
 idx_k_cache=past_key_states,
 idx_k_scale_cache=past_key_scales,
 idx_k_cache_index=slot_mapping.view(-1),
 layernorm_epsilon_k=self.k_norm.eps,
 layout_query="TND", layout_key="PA_BSND",
)
```

输出 `(q, query_dequant_scale, weights)` 直接喂给后续 Lightning Indexer 算子。

### 三条独立流

**Indexer Q**：

$$
\bold{q}, \bold{q}_{scale} = \text{DynamicQuant}(\text{Hadamard}(\text{RoPE}(\text{DeQuant}(\bold{q} \cdot \bold{w}_{qb}))))
$$

Q 走动态 **Per-Token-Head A8**；Hadamard 变换通过矩阵右乘 `hadamard_q` 实现；$\bold{q}, \bold{w}_{qb}$ 均 Int8。

**Indexer Cache (K)**：

$$
\bold{k}, \bold{k}_{scale} = \text{DynamicQuant}(\text{Hadamard}(\text{RoPE}(\text{LayerNorm}(\bold{x} \cdot \bold{w}_k))))
$$

K 走动态 **Per-Token-Head C8**；Hadamard 通过矩阵右乘 `hadamard_k`。

**Indexer Weight**：

$$
\bold{weight} = (\bold{x} \cdot \bold{w}_{proj}) * \text{scale}
$$

Weight 不量化，最后转 FP16 喂给后续 LI。

> 量化策略约束（源文档）："Indexer Prolog 的量化策略为：Q_b_proj 使用 W8A8 量化，其他 Linear 均不量化；Indexer Q 使用 A8 量化，Indexer Cache 使用 C8 量化；反量化因子以 FP16 存储；同时，在量化前，会进行 Hadamard 变换，Hadamard 变换在业界最新的低 bit 量化方案中十分常用，可以有效消除 outlier。"

## Performance Signals

### 泳道图与性能拆解

典型 Shape（4 batch × MTP1 × KV-Cache 64K）Profiling 泳道图：

![Indexer Prolog 泳道图](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/IndexerPrologSwimLane.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/IndexerPrologSwimLane.png`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/IndexerPrologSwimLane.png)（cann-recipes-infer @ 2f82d10）*

**计算流特点**（源文档）：

- 三部分互相独立、各自串行；
- Indexer Q 耗时最长，可以掩盖 Indexer Cache 和 Indexer Weight；
- 典型 Shape 下计算量较小，不会打满所有核，**性能瓶颈在搬运上**。

**Indexer Q 四段理论性能拆解**：

| 段 | 内容 | 性质 |
| ---- | ---- | ---- |
| 1 | `(8, 1536) @ (1536, 8192)` Matmul | MTE bound，理论极限 13 μs；与 K/Weight Matmul 并行抢带宽，已近极致 |
| 2 | DeQuant + RoPE（Vector 核） | 合适 tile 切分后全在 UB 内，无 UB↔GM 冗余搬运，已达极致 |
| 3 | Hadamard 变换：`(8, 64, 128) @ (1, 128, 128)` BatchMatmul | MTE bound，已达极致 |
| 4 | Int8 量化（Vector 核） | 合适 tile 切分后全在 UB 内，已达极致 |

> 源结论："Indexer Prolog 的计算已经逼近理论极限性能。"

## Optimization Notes

### 与多流优化配合

除了融合本身，**Indexer Prolog 前的一系列 Cube 和 Vector 算子**可进一步使用 torchair 的 `npu_stream_switch` 多流并行，流水示意：

![IndexerProlog 多流并行](https://raw.gitcode.com/cann/cann-recipes-infer/raw/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v3.2-exp/figures/indexer_prolog_multi_stream.jpg)
*来源：[`docs/models/deepseek-v3.2-exp/figures/indexer_prolog_multi_stream.jpg`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/figures/indexer_prolog_multi_stream.jpg)（cann-recipes-infer @ 2f82d10）*

见 [moe-multi-stream](../techniques/moe_multi_stream.md)（本技术页面同时记录 MoE 多流与 Indexer Prolog 多流两种 V3.2-Exp 多流场景）。

### 与 Deepseek Indexer Attention 的关系

作为独立融合算子，Indexer Prolog 已接近极致性能；但进一步可以把 MLAProlog + IndexerProlog + LightningIndexer + SFA 四者融合成 **Deepseek Indexer Attention** 大融合算子，获取更大并行度。见 [deepseek-indexer-attention](deepseek_indexer_attention.md)。

### 下一步计划

源文档明示："仿照 Indexer Prolog 的调优过程，将其他几个子算子进行独立性能调优，达到极致性能。"

## DeepSeek-V4 适配（PyPTO）

与 DeepSeek-V3.2 不同，DeepSeek-V4 的 **IndexerProlog 只出现在 `compress_ratio = 4` 的层（即 C4A / CSA 层）**——只有 CSA 层才在 Compressor 压缩后的 cmp_KV 上叠加 LI 稀疏选择，因此只有 CSA 层需要 IndexerProlog 为后续 [lightning-indexer](lightning_indexer.md) 计算提供输入 `q`、`weight` 及 `q_scale`（C128A / HCA 层不带 LI 模块）：`Indexer.__init__(..., compress_ratio=4)`、`cmp_ratio: 4  # only c4a have li module`（`models/deepseek-v4/models/modules/indexer.py`）。上文 V3.2-Exp 的三流公式、泳道图、极限性能分析继续有效（对应 V3.2-Exp 谱系）。

### Query 计算：q_hadamard / Quant 流程

PyPTO guide 给出 V4 IndexerProlog 的 Query 计算公式（`Rope` 为旋转位置编码、`Quant` 为量化）：

$$q\_tmp = qr @ idx\_wq\_b \cdot qr\_scale \cdot idx\_wq\_b\_scale$$
$$q\_hadamard = \text{Cat}(\{q\_tmp[:, :nope\_dim],\ Rope(q\_tmp[:, nope\_dim:])\}, -1) @ hadamard$$
$$q,\ q\_scale = Quant(q\_hadamard)$$

`indexer.py` forward 把 Query 计算拆为独立步骤而非单一融合调用：`wq_b(qr, dynamic_scale=qr_scale)` → `inplace_partial_rotary_mul(..., rotary_mode="interleave", partial_slice=...)`（只对后 `rope_head_dim` 做 interleave RoPE）→ `rotate_activation(q, self.hadamard_matrix)`（Hadamard 右乘，`hadamard_matrix = get_had_pow2(head_dim)`）→ 量化。量化按 `li_cache_quant_mode` 分两路：

- `"int8"`：`q, q_scale = torch_npu.npu_dynamic_quant(...)`，`q_scale` 转 FP16（Indexer Cache C8）；
- **FP8**：`q, q_scale = torch_npu.npu_dynamic_block_quant(..., dst_type=cache_data["li_cmp_kv"].dtype)`，对应 950PR/DT 上 LI FP8 全量化版的 Indexer Q 输入。

> **源/代码差异**：PyPTO guide 把 IndexerProlog 描述为单一融合算子（fused "IndexerProlog 算子"），而 V4 `indexer.py` 把上述步骤展开为 `wq_b` / `inplace_partial_rotary_mul` / `rotate_activation` / `dynamic_quant` 等独立 op（含 `enable_multi_streams` 多流切换）。V3.2-Exp 谱系的 `npu_lightning_indexer_prolog_pto` 单一大融合算子仍存在于 `ops/pypto/src/lightning_indexer_prolog_pto/`（commit `f8c6f67` 清理过其 `quant_lightning_indexer_prolog_impl.cpp` 冗余头文件）。**V4 是否在某图模式路径下回落到该单一融合 PyPTO 算子，源/代码未明示。**

### Weights 计算

$$weights = x @ weights\_proj \cdot \frac{1}{\sqrt{idx\_nq \cdot head\_dim}}$$

实现为 `weights = self.weights_proj(x_for_weights_proj) * (self.softmax_scale * self.n_heads ** -0.5)`，其中 `softmax_scale = head_dim ** -0.5`、`n_heads = config.index_n_heads`（公式 `idx_nq` 对应代码 `index_n_heads`），合并即 $1/\sqrt{head\_dim\cdot idx\_nq}$。Weight 不量化，按 `li_cache_quant_mode` 转 FP16（int8 路）或 FP32（fp8 路）后喂给 LI。

## 多流优化（case pattern）

该固定实现的事件和分支代码统一维护在[独立实现案例](../../optimizations/cases/indexer_prolog_streams_fixed_implementation.md)。本卡保留机制、变体与接口；案例不能继承更宽的平台或收益范围。

## Evidence

- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_pypto_operator_guide.md)（Indexer Prolog 三流公式、泳道图、极限性能分析）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_inference_guide.md)（量化策略中 IndexerProlog 融合算子 A8C8 配置、多流并行）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v3.2-exp/models/indexer.py:L184`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/models/deepseek-v3.2-exp/models/indexer.py#L184)（PyPTO prolog 调用）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`ops/pypto/src/lightning_indexer_prolog_pto/op_kernel/`](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/ops/pypto/src/lightning_indexer_prolog_pto/op_kernel/)（V3.2-Exp PyPTO 实现源码；`quant_lightning_indexer_prolog_impl.cpp` 冗余头清理见 commit `f8c6f67`）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`docs/models/deepseek-v4/deepseek_v4_pypto_operator_guide.md`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_pypto_operator_guide.md) `## IndexerProlog`（V4 仅 compress_ratio=4 层、q_hadamard / Quant 公式、Weights 公式）。
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v4/models/modules/indexer.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4/models/modules/indexer.py)（`compress_ratio=4` / `cmp_ratio:4 # only c4a have li module`、`wq_b`→`inplace_partial_rotary_mul`(interleave)→`rotate_activation`(hadamard)→`npu_dynamic_quant`/`npu_dynamic_block_quant`、`weights = weights_proj(x)*(head_dim**-0.5 * n_heads**-0.5)`；doc 描述 fused 而 code 为展开步骤）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/glm-5/models/indexer.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/glm-5/models/indexer.py)（多流前处理切流核对 @2c45117：`enable_multi_streams = ... and not is_prefill`:169；`npu_stream_switch(.., "22")`:177（Q 路径，`wq_b`:80）；`npu_wait_tensor(qr, query_states[0])`:183；`npu_stream_switch(.., "33")`:202（`weights_proj`:90）；`npu_wait_tensor(x, q_b)`:207；RoPE 用 `npu_interleave_rope`；Q 量化再入 `"22"`:225；aclgraph 路径用 `npu_record_tagged_stream`/`npu_tagged_event_record/wait(indexer_npu_events[0..3])`）
- [cann-recipes-infer](https://gitcode.com/cann/cann-recipes-infer/tree/2c45117d781ab9ab88dcb89a28ae30f5d2450399) — [`models/deepseek-v3.2-exp/models/indexer.py`](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v3.2-exp/models/indexer.py)（多流前处理切流核对 @2c45117：`"22"`:256（`wq_b`:85）、`"33"`:283（`weights_proj`:95）、`npu_wait_tensor(qr, query_states[0])`:262、`npu_wait_tensor(x, q_b)`:288、Q 量化再入 `"22"`:306；RoPE 用 `npu_rotary_mul`——与 GLM-5 的 `npu_interleave_rope` 不同）

## Links

- [deepseek-v3.2-exp](../models/deepseek_v3_2_exp.md)
- [lightning-indexer](../modules/lightning_indexer.md)
- [lightning-indexer](lightning_indexer.md)
- [deepseek-indexer-attention](deepseek_indexer_attention.md)
- [pypto](../frameworks/pypto.md)
- [w8a8c8](../quantization/w8a8c8.md)
- [moe-multi-stream](../techniques/moe_multi_stream.md)
- [multi-stream](../techniques/multi_stream.md)（多流方法论总纲；本页 [多流优化（case pattern）](#多流优化case-pattern) 记 Indexer Prolog 前处理切流细节）
- [glm-5](../models/glm_5.md)（GLM-5 `indexer.py` 同构多流前处理，Q 路径 RoPE 用 `npu_interleave_rope`）
- [deepseek-v4](../models/deepseek_v4.md)（V4 CSA 层 IndexerProlog 前置 LI，量化路径 Indexer Cache C8）
- [compressor](compressor.md)（V4 CSA 层 IndexerProlog 的 LI 作用于 Compressor 压缩后的 cmp_KV）
