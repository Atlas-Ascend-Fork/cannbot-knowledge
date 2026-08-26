---
type: Runbook
title: 昇腾编码器 packed 全注意力：两个可互换融合算子的 seq_len 语义不同（unpad 吃原始长度、fusion_attention TND 吃 cumsum）
description: 昇腾多模态/视觉编码器（ViT类）packed（unpad/varlen）非因果全注意力路径上，两个可互换的昇腾融合算子对「每序列长度」入参语义不同：torch_npu._npu_flash_attention_unpad 的 seq_len 吃原始每序列长度、且是 out-tensor 语义（须 torch.empty_like 预分配传 out=）；torch_npu.npu_fusion_attention(input_layout="TND") 的 actual_seq_qlen/actual_seq_kvlen 吃累积前缀和 cumsum、直接返回 tuple 取[0]。转换为 list(seq_lens_cpu.cumsum(0))。两算子都要求 seq_len 张量驻留 CPU（FA requires CPU seq_lens；用 torch.diff(cu_seqlens).to('cpu') 现算会拖慢性能）。在两算子间切换时不做对应 cumsum/去cumsum 转换，序列切分会错位、注意力切到错误 token 边界、输出静默出错或报 shape 错。修法：把契约差异吸收进统一设备适配器入口 npu_flash_attention(query,key,value,seq_lens_cpu,head_num,scale_value,num_kv_heads)，按硬件型号在 import 期分派（A2/A3 走 BaseDeviceAdaptor 原始长度版、A5/Ascend-950 走 A5DeviceAdaptor cumsum TND 版，get_device_adaptor 依 get_ascend_device_type 决定）。参考实现 vllm-ascend 的 MMEncoderAttention.forward_oot（mm_encoder_attention.py packed [b*s,head,head_dim]）+ device_op.py，被 Hunyuan-OCR 等编码器模型使用。关联 FIA fused-infer-attention-score、Atlas A3 平台。
tags:
- task.debugging
- topic.attention
- topic.compilation
status: stable
sources:
- resource: https://github.com/vllm-project/vllm-ascend/pull/8671
  role: evidence
created_at: '2026-07-15T00:00:00Z'
updated_at: '2026-07-15T00:00:00Z'
platforms:
- a2
- a3
---

# 昇腾编码器 packed 全注意力：两个可互换融合算子的 seq_len 语义不同（unpad 吃原始长度、fusion_attention TND 吃 cumsum）

## 信号（现象）

在昇腾上给一类**多模态 / 视觉编码器（ViT 类）非因果全注意力**接融合算子，输入是 packed（unpad / varlen）布局——batch 内多序列被打平成 `[b*s, head, head_dim]`、靠一份「每序列长度」张量切分——时，若在两个可互换的昇腾融合算子之间切换、却沿用同一份长度入参，序列切分会**错位**：注意力按错误的 token 边界切分、结果不正确。

这一签名的触发点是：同一段 packed 全注意力，你既可以用 `torch_npu._npu_flash_attention_unpad`，也可以用 `torch_npu.npu_fusion_attention`（`input_layout="TND"`）来实现，二者对外看似等价，但对「每序列长度」入参的**语义定义不同**。

## 触发条件

- packed（unpad / varlen）布局的编码器全注意力，用一份 per-sequence length 张量做序列切分。
- 在 `_npu_flash_attention_unpad` 与 `npu_fusion_attention(TND)` 之间做算子切换 / 迁移 / 多平台分派，而**没有对长度入参做对应的 cumsum / 去 cumsum 转换**。
- 常见于按硬件型号分派算子的路径（例如 A2/A3 走一个算子、A5/Ascend-950 走另一个），或把内联算子调用抽成统一入口时。

## 根因：两个算子的 seq_len 语义不是同名同义

同一段 packed 全注意力可由两个昇腾融合算子实现，但它们的「每序列长度」入参**名字和含义都不同**：

| 算子 | 长度参数名 | 语义 | 返回值约定 |
|---|---|---|---|
| `torch_npu._npu_flash_attention_unpad` | `seq_len` | **原始每序列长度**（未累加，如 `[128, 96, 200]`） | out-tensor 语义：须 `torch.empty_like(query)` 预分配并传 `out=`，返回值走该 out |
| `torch_npu.npu_fusion_attention`（`input_layout="TND"`） | `actual_seq_qlen` / `actual_seq_kvlen` | **累积前缀和**（cumsum，如 `[128, 224, 424]`） | 直接返回 tuple，取 `[0]` |

- `unpad` 吃**原始长度**；`fusion_attention` TND 吃 **cumsum 前缀和**。把原始长度直接喂给 TND 版（或把 cumsum 喂给 unpad 版）就会按错误的边界切分。转换是 `list(seq_lens_cpu.cumsum(0))`（原始 → cumsum），反向做差分还原。
- **两个算子都要求该长度张量驻留在 CPU**（编码器注意力路径注释点明「FA requires CPU seq_lens」）。若临时用 `torch.diff(cu_seqlens).to('cpu')` 现算 seq_lens 会明显拖慢性能——长度张量应当从一开始就以 CPU 张量准备好、透传给算子，而非在热路径上从 device 张量反算。
- 除长度语义外，两者的返回值约定也不同（见上表 out-tensor vs. tuple），迁移时一并对齐。

## 修法

把两个算子的契约差异**吸收进一个统一入口**（设备适配器），由入口内部按目标算子做长度转换，而不是让上层调用点各自记住语义。参考实现把统一入口签名定为 `npu_flash_attention(query, key, value, seq_lens_cpu, head_num, scale_value, num_kv_heads)`，入口内部：

- 走 `_npu_flash_attention_unpad` 的分支：直接 `seq_len=seq_lens_cpu`（原始长度），预分配 `context_layer = torch.empty_like(query)` 传 `out=`：

```python
def npu_flash_attention(query, key, value, seq_lens_cpu, head_num, scale_value, num_kv_heads):
    context_layer = torch.empty_like(query)
    torch_npu._npu_flash_attention_unpad(
        query=query, key=key, value=value,
        seq_len=seq_lens_cpu,            # 原始每序列长度，非 cumsum
        scale_value=scale_value,
        num_heads=head_num, num_kv_heads=num_kv_heads,
        out=context_layer,               # out-tensor，须预分配
    )
    return context_layer
```

- 走 `npu_fusion_attention(TND)` 的分支：先 `seq_lens_cpu = list(seq_lens_cpu.cumsum(0))` 转前缀和，再喂 `actual_seq_qlen/actual_seq_kvlen`，取返回 tuple 的 `[0]`：

```python
def npu_flash_attention(query, key, value, seq_lens_cpu, head_num, scale_value, num_kv_heads):
    seq_lens_cpu = list(seq_lens_cpu.cumsum(0))   # 原始长度 → 累积前缀和
    context_layer = torch_npu.npu_fusion_attention(
        query=query, key=key, value=value,
        actual_seq_qlen=seq_lens_cpu, actual_seq_kvlen=seq_lens_cpu,
        head_num=head_num, scale=scale_value, input_layout="TND",
    )[0]
    return context_layer
```

按硬件型号在 import 期决定分派（如 `Ascend-950/A5` → cumsum 版、A2/A3 → 原始长度版），上层只传原始 `seq_lens_cpu`（CPU 张量），两算子的语义差异对调用点透明。

## 参考实现及其约束

- 参考实现：vllm-ascend（vLLM 昇腾后端），`vllm_ascend/ops/mm_encoder_attention.py` 的 `MMEncoderAttention.forward_oot`（输入经 `_reshape_qkv_to_3d` 打成 packed `[b*s, head, head_dim]`）+ `vllm_ascend/device/device_op.py` 的设备适配器（`BaseDeviceAdaptor` 走 A2/A3 原始长度版，`A5DeviceAdaptor` 走 cumsum TND 版；`get_device_adaptor()` 依 `get_ascend_device_type()` 在 import 期选择）。该路径被 Hunyuan-OCR 等编码器模型使用。
- 这些是该参考实现的具体绑定（型号分派名、类名、模型名），**不是技术本身的限制**。可迁移的核心事实是：`_npu_flash_attention_unpad` 与 `npu_fusion_attention(TND)` 的 per-sequence length 语义分别是「原始长度」与「cumsum 前缀和」，且都要 CPU 张量——任何在编码器 packed 全注意力路径上切换 / 接入这两个昇腾融合算子的人都会撞上同一差异。
- 本页只记算子契约差异这一事实，**不断言两算子的性能优劣**（该 PR 未给性能根因）；也不就该实现中 `num_kv_heads` 具体取值的正确性下断言（review 讨论未定论、以合并态调用点为准）。

## 相关经验
- [昇腾多模态模型 bringup 的结构失配：框架侧 config 扫描盲区与 OOT 算子秩](mm_bringup_config_scan_and_oot_op_rank_contract.md)
- [视觉编码器 SAM 式分解相对位置偏置：经 pse_shift 融进 npu_prompt_](../../optimizations/experience/rules/vision_encoder_rel_pos_bias_via_pse_shift.md)

- FIA / `npu_fused_infer_attention_score` 的 `actual_seq_lengths_kv` 变长实参**类型随后端不同**（int list vs. tensor），与本页「同一逻辑长度、不同算子要不同表示」同源，见 [fia-actual-seq-lengths-kv-backend-type](fia_actual_seq_lengths_kv_backend_type.md)。
- 昇腾推理统一 TND packed-sequence 布局的标准与 BSND/packed-1D shim 约束见 [tnd-packed-sequence-standard-and-bsnd-shim](../../optimizations/experience/rules/tnd_packed_sequence_standard_and_bsnd_shim.md)；把注意力算子迁到 TND 布局的调用约定见 [attention-compressor-tnd-layout-migration](../../optimizations/experience/rules/attention_compressor_tnd_layout_migration.md)。
- 非因果 / 双向全注意力走 FIA `atten_mask=None` 全注意力路径见 [bidirectional-attention-fia-non-causal-full](../../optimizations/experience/rules/bidirectional_attention_fia_non_causal_full.md)。

## 相关静态页

- 昇腾融合注意力算子 [FIA](../../concepts/kernels/fused_infer_attention_score.md)（与 `npu_fusion_attention`/`_npu_flash_attention_unpad` 同属昇腾融合注意力算子族，TND packed 布局与 cumsum actual_seq_len 约定同源）。
- 硬件平台 [Atlas A3](../../concepts/platforms/atlas_a3.md)（本签名的算子分派把 A2/A3 归到原始长度版分支）。

## Evidence

- `diff 事实`（merge commit `c9aff2b0`，`vllm_ascend/device/device_op.py` / `vllm_ascend/ops/mm_encoder_attention.py` @`c9aff2b095e0e3b9295bc4cadc497e5d8f447840`）：`_npu_flash_attention_unpad` 收 `seq_len=seq_lens_cpu`（原始长度、out-tensor 语义）、`npu_fusion_attention` 收 `list(seq_lens_cpu.cumsum(0))` 后的 `actual_seq_qlen/actual_seq_kvlen`（TND、返回取 `[0]`），两算子 seq_lens 均在 CPU；设备分派 `BaseDeviceAdaptor`(A2/A3) vs. `A5DeviceAdaptor`(A5) 由 `get_device_adaptor()` 在 import 期依 `get_ascend_device_type()` 决定。
- 溯源下探：[vllm-ascend-pr-8671-performance-in-scenarios-a2-and-a3-replace-npu-fusion-attention-with-the](https://github.com/vllm-project/vllm-ascend/pull/8671)
