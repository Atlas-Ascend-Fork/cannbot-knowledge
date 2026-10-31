---
type: Concept
title: Indexer Prolog Kernel
description: 区分 V3.2 的 PyPTO 三流融合与 V4 压缩 K、HiF8/FP8/Int8 Q 前处理，并修正 GLM-5 模型身份和当前 FP8 支持。
tags:
- task.implementation
- topic.attention
- topic.precision
- topic.compilation
status: stable
sources:
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_pypto_operator_guide.md
  role: primary
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/indexer.py
  role: implementation
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py
  role: implementation
created_at: '2026-04-14T00:00:00Z'
updated_at: '2026-10-29T15:24:38Z'
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

![Indexer Prolog 计算流程](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/IndexerPrologQuant.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/IndexerPrologQuant.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/IndexerPrologQuant.png)（cann-recipes-infer @ 944d2d3）*

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

![Indexer Prolog 泳道图](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/IndexerPrologSwimLane.png)
*来源：[`docs/models/deepseek-v3.2-exp/figures/IndexerPrologSwimLane.png`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/IndexerPrologSwimLane.png)（cann-recipes-infer @ 944d2d3）*

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

![IndexerProlog 多流并行](https://raw.gitcode.com/cann/cann-recipes-infer/raw/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/indexer_prolog_multi_stream.jpg)
*来源：[`docs/models/deepseek-v3.2-exp/figures/indexer_prolog_multi_stream.jpg`](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/figures/indexer_prolog_multi_stream.jpg)（cann-recipes-infer @ 944d2d3）*

见 [moe-multi-stream](../techniques/moe_multi_stream.md)（本技术页面同时记录 MoE 多流与 Indexer Prolog 多流两种 V3.2-Exp 多流场景）。

### 与 Deepseek Indexer Attention 的关系

作为独立融合算子，Indexer Prolog 已接近极致性能；但进一步可以把 MLAProlog + IndexerProlog + LightningIndexer + SFA 四者融合成 **Deepseek Indexer Attention** 大融合算子，获取更大并行度。见 [deepseek-indexer-attention](deepseek_indexer_attention.md)。

### 下一步计划

源文档明示："仿照 Indexer Prolog 的调优过程，将其他几个子算子进行独立性能调优，达到极致性能。"

## DeepSeek-V4 当前前处理

CSA 仅在 compress_ratio=4 时建立 Indexer；K 路通过 Compressor 生成压缩 cache，不能照搬 V3.2 的独立 wk/LayerNorm 流。Q 由 wq_b(qr,dynamic_scale=qr_scale) 投影，再做 interleaved Partial RoPE。Int8/FP8 分支执行 Hadamard，随后分别 dynamic_quant（FP16 scale）或 dynamic_block_quant（FP32 scale）。HiF8 用 Partial RoPE 后量化并跳过 Hadamard，Q scale 为单位；weights_proj 在 HiF8 模式也采用量化 Linear。

weights = weights_proj(x) / sqrt(head_dim×index_n_heads)，Int8 转FP16、浮点分支转FP32，供当前 quant_lightning_indexer。离线 CP 从临时压缩缓存读取并按 prev/next 分段，不能继续访问旧 cache_data 字典。PyPTO 技术报告提供融合优化参考；当前 V4 indexer.py 是展开的前处理及多流事件链，不据文档标题推断调用 V3.2 的 custom_pypto prolog。

GLM-5 使用 models/glm_5，而非GLM-5.2；当前其 apply_hadamard_quant 已有 Int8 和 FP8 分支，RoPE 使用模型专属交错布局。多流的 GE/native 事件细节见[实现案例](../../optimizations/cases/indexer_prolog_streams_fixed_implementation.md)。

## 多流优化（case pattern）

该固定实现的事件和分支代码统一维护在[独立实现案例](../../optimizations/cases/indexer_prolog_streams_fixed_implementation.md)。本卡保留机制、变体与接口；案例不能继承更宽的平台或收益范围。

## Evidence

- [deepseek_v3.2_exp_pypto_operator_guide.md](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/docs/models/deepseek_v3_2_exp/deepseek_v3.2_exp_pypto_operator_guide.md)（primary）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/models/indexer.py)（implementation）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v4/models/modules/indexer.py)（implementation）
- [indexer.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/glm_5/models/indexer.py)（implementation）

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
