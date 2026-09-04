---
type: Optimization
title: MLA/SFA decode 前处理融合算子（MLAPO）的两条硬前置：W8A8-only + 非 SFA-CP，否则 per-layer 静默回退
description: MLAPO 将 MLA/SFA decode 前的 QKV 投影、split、Q LayerNorm、KV 与 Q 上投影及 RoPE 融合为单个 NPU 预处理算子，以减少重复计算和 kernel 下发。它按层生效且同时要求 fused_qkv_a_proj 使用 AscendW8A8LinearMethod、SFA context parallel 未开启；任一条件不满足都会记录一次 warning 并静默回退逐算子路径，因此同一模型部分层启用属于正常行为。融合路径会把权重转为 int8 FRACTAL_NZ 并配置配套 scale、bias，只用于 decode，prefill 仍走原路径。开关为 VLLM_ASCEND_ENABLE_MLAPO；当前来源仅说明优化意图，没有实测收益数字。
tags:
- task.optimization
- topic.attention
- topic.precision
- topic.model_serving
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/4753
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-09-03T13:55:44Z'
platforms:
- agnostic
---

# MLA/SFA decode 前处理融合算子（MLAPO）的两条硬前置：W8A8-only + 非 SFA-CP，否则 per-layer 静默回退

## 适用场景

**场景**：你在给一个 MLA / SFA（Sparse Flash Attention，DSA 结构）注意力的 decode 路径做前处理加速，想把 decode 前那一串小算子——`fused_qkv_a_proj` matmul → split → `q_a_layernorm` → `exec_kv` → q 上投影与 K up-proj → `rope`——融成**一个** NPU 前处理算子（MLAPO），以吃掉 kernel launch 与中间张量搬运开销，并避免 q_down 的重复计算。

**通向该规则的判断**：MLAPO 这类前处理融合算子**不是无条件可用**的。融合把「量化 dequant + layernorm + RoPE 维度重排 + 上投影」全部内联进单算子，因此它对**权重的量化方案**和**注意力的并行方式**有硬约束——只有当每层的权重能被预处理成融合算子要吃的量化布局、且 KV 序列没有被切成 context-parallel 段时，融合算子的输入契约才成立。

**这条规则本身**（可迁移的判断）：接入前处理融合算子时，要按**层粒度**逐层核两条前置，任一不满足就让该层退回原逐算子路径，而不是全局开关一刀切、也不是让它在运行期崩：

1. **量化前置**：该注意力层的 QKV 下投影必须是 **W8A8**（int8 权重 + int8 激活，走 `AscendW8A8LinearMethod`）量化。非 W8A8 的层（例如保 BF16 / 走别的量化 scheme 的层）不满足融合算子的 dequant/scale 契约 → 该层关融合。
2. **并行前置**：**未开启该注意力的 context-parallel（CP）**。一旦 KV 序列被 CP 切段，前处理与 KV 写入的语义变了，融合算子不覆盖这条路径 → 关融合。

**为何做成 per-layer 静默回退而非报错**：同一模型里不同层的量化方案可以不同（例如只有部分 Linear 真走 W8A8，见稀疏注意力 + 双 prolog 结构下的选层律 [w8a8c8](../../../concepts/quantization/w8a8c8.md)）。若某层不满足前置就抛异常，会让「本可以部分加速」的模型直接无法启动；正确做法是**该层回退、其余层照常融合**，把回退降级为一条 `warning_once` 提示。因此对优化 agent 的行动含义是：**看到「只有一部分层用了 MLAPO」是设计内的正常现象，不是 bug**；要提整模型的融合覆盖率，得从「让更多层满足 W8A8 + 关掉 SFA-CP」入手，而不是去强开融合。

### 何时不适用 / 边界
- prefill 阶段不走这条融合路径（gate 判据是 decode，即 `not with_prefill`）；本规则只约束 decode 前处理。
- 收益「避免 q_down 重复计算」是融合意图（intent），**不是本处实测的 before→after 数字**；不要把它当成已验证的加速比引用。
- 这两条前置是**该参考实现（vllm-ascend 的 MLAPO 接入）**当前的接受面，不是「MLAPO 算子规格本身只能吃 W8A8 / 只能非 CP」的物理结论——是接入代码画的门，随实现演进可能放宽。

## 参考实现及其约束

参考实现：vLLM 的昇腾后端 vllm-ascend，DeepSeek-V3.2（[deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md)）的 SFA/DSA（[dsa](../../../concepts/modules/dsa.md)）decode 路径，文件 `vllm_ascend/attention/sfa_v1.py`。融合算子是 `torch.ops._C_ascend.mla_preprocess`（MLAPO），由环境变量 `VLLM_ASCEND_ENABLE_MLAPO` 打开（`self.enable_mlapo = envs.VLLM_ASCEND_ENABLE_MLAPO`）。MLAPO 算子本体由另一 PR 提供，本接入只负责「把它接进 SFA decode 路径 + 前置门控」。

### 两条前置检查（权重加载后 `process_weights_after_loading` 内执行）

```python
if self.enable_mlapo:
    quant_method = getattr(getattr(self.fused_qkv_a_proj, "quant_method", None), "quant_method", None)
    reasons = []
    if self.fused_qkv_a_proj is None or not isinstance(quant_method, AscendW8A8LinearMethod):
        reasons.append("Currently mlapo only supports W8A8 quantization in MLA scenario. ...")
    if self.enable_sfa_cp:
        reasons.append("Currently mlapo does not support SFA with CP, ...")
    if reasons:
        self.enable_mlapo = False
        for msg in reasons:
            logger.warning_once(msg)
    else:
        self._process_weights_for_fused_mlapo(act_dtype)
```

- 判据 1：`fused_qkv_a_proj.quant_method.quant_method` 必须 `isinstance(..., AscendW8A8LinearMethod)`；否则该层 `enable_mlapo=False`。
- 判据 2：`self.enable_sfa_cp` 为真（开了 SFA 的 CP）→ 该层 `enable_mlapo=False`。
- 回退是 **per-layer + 静默**（仅 `warning_once`，不抛异常），未启用层照走原逐小算子 else 分支。

### 融合生效时的权重预处理（`_process_weights_for_fused_mlapo`）——即该融合算子的输入契约

这是让复用者能对齐/排错的关键约定（注意：这是**本接入实现为满足 MLAPO 所产出的权重布局**，属 converter 侧产出，非「算子规格只接受这些」）：

- 从 `fused_qkv_a_proj` 权重按 `q_lora_rank` 切出 **kv_a / q_a** 两段；kv_a 段经 `trans_rope_weight(..., qk_rope_head_dim)` 对 RoPE 维做交错重排，再与 q_a 段 `cat`，`transdata(block_size=(16,32))`，最后 `torch_npu.npu_format_cast(wd_qkv, 29)` 转成 **FRACTAL_NZ（29）** 布局 → `self.wd_qkv`。
- `deq_scale` / `quant_bias` 同样按 `q_lora_rank` 切成 kv+rope / q 两段，kv 段对 `(kv_lora_rank + qk_rope_head_dim)` 维 `trans_rope_weight` 后拼回 → `deq_scale_qkv` / `quant_bias_qkv`。
- Q 上投影权重 `q_proj.weight` reshape 成 `(num_heads, qk_nope_head_dim + qk_rope_head_dim, -1)` → `trans_rope_weight` → `transdata(16,32)` → `npu_format_cast(..., 29)` → `self.wu_q`；其 `deq_scale` / `quant_bias` 同法处理。
- 量化辅助量：`quant_scale0/offset0`（来自 `fused_qkv_a_proj.input_scale/offset`）、`quant_scale1/offset1`（来自 `q_proj.input_scale/offset`）、`gamma1/beta1`（`q_a_layernorm`）、`gamma2`（`kv_a_layernorm`）、`ctkv_scale` / `q_nope_scale`（act_dtype 的常量 1）。
- 释放冗余权重：`self.fused_qkv_a_proj.weight = None`；当 `kv_transfer_config` 非空时进一步把 `deq_scale` / `quant_bias` 置 None 并 `torch.npu.empty_cache()`。

上述 FRACTAL_NZ 转换（`npu_mla_prolog`（[mla-prolog](../../../concepts/kernels/mla_prolog.md)）与 MLAPO 同属 MLA 前处理融合算子族、同样吃 FRACTAL_NZ 权重）是「W8A8-only」这条前置的物理原因之一：只有 W8A8 层才有配套的 `deq_scale` / `quant_bias` / `input_scale`，才能被 cast 成融合算子所需的 int8 NZ 布局。

### decode 前向调用（`_sfa_preprocessc_decode`）

单算子 `torch.ops._C_ascend.mla_preprocess(...)` 一次产出 `q_out0=ql_nope`、`q_out1=q_pe`、`inner_out=q_c`，并就地更新 `kv_cache_out0/1`。关键参数：`cache_mode="krope_ctkv"`、`quant_mode="per_tensor_quant_asymm"`、`enable_inner_out=True`。前向分支：

```python
if self.enable_mlapo and not forward_context.with_prefill:
    # 走 mla_preprocess 融合前处理
else:
    # prefill、以及 MLAPO 未启用层：走原逐算子路径
```

## Evidence

- 溯源：[vllm-ascend-deepseek-v3-2-sfa-decode-接入-mlapo-融合预处理算子的两条硬前置](https://github.com/vllm-project/vllm-ascend/pull/4753)
- 上游 diff：vllm-project/vllm-ascend `vllm_ascend/attention/sfa_v1.py`，merge sha `b91a5f096889b2b6e1d09c2137974de13ad9b904`（单文件 +244/-53）。两条前置、静默回退、权重预处理链、`mla_preprocess` 调用参数均出自该合并态 diff。
- 无 before→after 性能数字：该变更的 'How was this patch tested' 为空，「避免 q_down 重复计算」为描述层意图，尚无验证结果支持。

<!-- cannbot:related:start -->
## 相关

- [DSA（DeepSeek Sparse Attention）架构模式](../../../concepts/modules/dsa.md)（`related`）：“**场景**：你在给一个 MLA / SFA（Sparse Flash Attention，DSA 结构）注意力的 decode 路径做前处理加速，想把 decode 前那一串小算子——`fused_qkv_a_proj` matmul → split → `q_a_layernorm` → `exec_kv` → q 上投影与 K up-proj → `rope`——融成**一个** NPU 前处理算子（MLAPO），以吃掉 kernel launch 与中间张量搬运开销，并避免 q_down 的重复计算。”与“其本质是 **MLA 的 Q/K/V LoRA 计算图 + 一个并行的学习式 indexer overlay**：indexer 与 MLA 共享同一份输入 `x`（及 MLA Q 侧 LoRA 中间量 `qr`），独立打分后为**每个 query 位置**选出 `index_topk` 个最相关的 key，产出一个加性 `-inf` mask；该 mask 在 **softmax 之前**叠加到 MLA 的注意力分数上，把非 top-k 位置置零。”分别说明融合目标与 DSA 计算结构。优化卡作用于 DSA decode 中 MLA/SFA 前处理小算子链，架构卡说明 MLA 与 indexer 的共享输入和 mask 关系；结合后才能判断 MLAPO 门控影响的确切子图。
<!-- cannbot:related:end -->
