---
type: Concept
title: SMLA（Sparse Flash MLA，DeepSeek-V4 稀疏 MLA 融合算子）
description: npu_smla converter（torchtitan-npu）：DeepSeek-V4 Sparse Flash MLA 融合算子。A5/Ascend-950 走 torch_npu SMLA 融合路径 + attention mask 接入 post_dataloading_process；非 A5 保持兼容 V4 稀疏注意力/LI/LI-loss。关键：LI-loss 计算+反向梯度融进 npu_sparse_lightning_indexer_klloss_grad，默认不显式算/打印 LI-loss、跳过 save_loss_to_tracker（区别 V3.2 DSA 显式 LI-loss），避免额外重计算；调试设 logger npu_smla=DEBUG 强制写 tracker。与 slig/sfag/sasg 同属 V4 稀疏注意力训练融合算子。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/README.md
  role: primary
- resource: https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/npu_fused_ops.md
  role: supporting
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- a2
- a3
- '950'
---

# SMLA（Sparse Flash MLA，DeepSeek-V4 稀疏 MLA 融合算子）

## Summary

`npu_smla` 是 [torchtitan](../frameworks/torchtitan.md)-npu 面向 **DeepSeek-V4 稀疏 MLA（Sparse Flash MLA）** 注意力路径的 NPU 融合算子 ModelConverter。它把 DeepSeek-V4 模型里的 sparse MLA 子模块替换成 NPU 亲和实现，并按硬件类型走两套**不同的替换集**（合计涉及 `LiCompute` / `InnerAttention` / `SparseAttention` / `LiLoss` 四类子模块，见「硬件分流」）：在 **A5（Ascend-950 系列）** 上走 `torch_npu` 提供的 SMLA 融合算子路径（`SparseFlashMLA` autograd），只替换 `LiCompute` / `InnerAttention`，同时把 SMLA 所需的 attention masks 接入 torchtitan 原生 `post_dataloading_process`；在**非 A5** 场景下回落到兼容原有 DeepSeek-V4 sparse attention / [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md) / LI-loss 的 NPU 实现（基于 `build_op` 编译的自定义算子），只替换 `SparseAttention` / `LiCompute` / `LiLoss`。它与 DSA 训练算子家族 [slig](slig.md) / [sfag](sfag.md) / [sasg](sasg.md) 同属稀疏注意力反向训练件，但**关键差异**是把 LI-loss 计算融进了反向梯度算子，默认不显式记录 LI-loss（见下）。配置经 [npu-fused-op-converters](../frameworks/npu_fused_op_converters.md) 的 `get_model_converter_config("npu_smla")` 启用。

```python
get_model_converter_config("npu_smla")
```

注册入口为 `@register_model_converter("npu_smla")` → `NpuSMLAModelConfig`（`model_converter = NpuSMLAConverter`）。

## 硬件分流（A5 vs 非 A5）

`NpuSMLAConverter.convert` 用 `get_npu_device_type() == "A5"` 选择两条互斥路径：

```python
def convert(self, model):
    use_smla_kernel = get_npu_device_type() == "A5"
    if use_smla_kernel:
        self.convert_smla_kernel(model)   # A5: torch_npu SMLA 融合路径
        return
    # 非 A5: 逐 module 用 build_op 编译自定义算子替换
    #   SparseAttention -> NpuSparseAttention (_sas_op = build_op("sparse_attn_sharedkv", ...))
    #   LiCompute       -> NpuLiCompute      (_li_op  = build_op("lightning_indexer", ...))
    #   LiLoss          -> NpuLiLoss         (_kl_op  = build_op("sparse_lightning_indexer_grad_kl_loss", ...))
# torchtitan_npu/converters/kernels/npu_smla.py — NpuSMLAConverter.convert
```

设备名→类型映射里 `Ascend950DT` / `Ascend950PR` / `Ascend910_95` / `Ascend950` 均归类为 `"A5"`（`torchtitan_npu/tools/device.py`）。

### A5：SMLA 融合路径

`convert_smla_kernel` 先 `_enable_native_smla_attention_mask_building()`，把 DeepSeek-V4 伪装成 varlen-attention decoder config（重写 `DeepSeekV4Model.get_attention_masks` / `attn_type` / `layers`，并将 `DeepSeekV4Model.Config` 挂进 trainer 的 `post_dataloading_process` 全局 `Decoder.Config`），从而让 torchtitan 原生 dataloading 链路构建 SMLA masks，而非 patch trainer 代码。随后建一份 `SMLAMetadataCache`，把 `LiCompute` 替换为 `NpuLiComputeSMLA`、`InnerAttention` 替换为 `NpuInnerAttentionSMLA`，二者共享该 cache。核心融合算子（均由 `torch_npu` 提供）：

| 阶段 | torch_npu 算子 |
| --- | --- |
| Lightning Indexer 正向 | `torch_npu.npu_lightning_indexer`（metadata 由 `npu_quant_lightning_indexer_metadata` 产，`query/key_quant_mode=2`） |
| 稀疏 MLA Attention 正向 | `torch_npu.npu_sparse_attn_sharedkv`（metadata 由 `npu_sparse_attn_sharedkv_metadata` 产） |
| 稀疏 MLA Attention 反向 | `torch_npu.npu_sparse_flash_mla_grad`（metadata 由 `npu_sparse_flash_mla_grad_metadata` 产） |
| LI 反向梯度 + LI-loss | `torch_npu.npu_sparse_lightning_indexer_klloss_grad`（metadata 由 `npu_sparse_lightning_indexer_klloss_grad_metadata` 产） |

正反向封装在 `SparseFlashMLA(torch.autograd.Function)`：`forward` 调 `npu_sparse_attn_sharedkv`（`return_softmax_lse=True`），`backward` 先 `npu_sparse_flash_mla_grad` 出 `dq/dori_kv/dcmp_kv/dsinks` 与 `cmp_softmax_l1`，再（仅 `cmp_ratio == 4` 时）调 `npu_sparse_lightning_indexer_klloss_grad` 出 indexer 三路梯度。共享的 metadata kwargs 含 `ori_mask_mode=4`、`cmp_mask_mode=3`、`ori_win_left=127`、`ori_win_right=0`、`layout_q/kv="BSND"`。

### 非 A5：兼容 NPU 实现

非 A5 用 `build_op(...)` 把 binding 编译成自定义算子并逐 module 替换：`NpuSparseAttention` 调 `_sas_op.npu_sparse_attn_sharedkv`，`NpuLiCompute` 调 `_li_op.npu_lightning_indexer`，`NpuLiLoss` 调 `_kl_op.npu_sparse_lightning_indexer_grad_kl_loss`。三个算子惰性编译（converter 命中时才 `build_op`），保持与 DeepSeek-V4 sparse attn / Lightning-Indexer / LI-loss 行为兼容。

## SMLA 与 Context Parallel

SMLA 的 varlen masks（`DeepSeekV4SMLAAttentionMasks`，含 `actual_seq_qlen` / `actual_seq_klen` / `cmp_residual_kv`）由 `build_smla_attention_masks` 在 **CP 分片前按 full `seq_len`** 构建。开启 Context Parallel 后，不能像普通序列张量那样直接做 cp 序列分片，而是由模块加载即注册的 `register_cp_mask_handler(_smla_cp_mask_handler)` 接管：handler 把 full-seq masks **按本 rank 重算 per-rank 形状**并返回，从而让 `cp_shard` 对这份 mask 跳过序列分片（非 SMLA mask 类型返回 `None` 不接管）。

per-rank 长度由 `_cp_smla_seq_lengths(seq_len, cp_degree, cp_rank)` 给出，对齐 `CompressorAttentionCP._post_hook` 的因果分布——rank `r` 持有 `local_s = seq_len // cp_degree` 个 query，因果地 attend `(r + 1) * local_s` 个 key：

```python
local_s = seq_len // cp_degree
return local_s, (cp_rank + 1) * local_s   # (q_len, kv_len)
```

因此 `q_seq_len = local_s`、`kv_seq_len = (r + 1) * local_s`（无 CP 时二者均回落为 `seq_len`）。`seq_len` 必须被 `cp_degree` 整除，否则 `_cp_smla_seq_lengths` 抛 `ValueError`。`DeepSeekV4SMLAAttentionMasks` 专设 `q_seq_len` / `kv_seq_len` 字段承载这一 per-rank 结果，供后续 SMLA 融合算子使用。

## LI-loss 融合与默认关闭日志（与 V3.2 DSA 的关键差异）

DeepSeek-V4 用 `npu_smla` 时，**LI-loss 的计算与其反向梯度计算被整合进 `npu_sparse_lightning_indexer_klloss_grad` 算子**，因此前向不再显式计算 LI-loss。与 DeepSeek-V3.2 默认 DSA 路径（[dsa](../../../inference/concepts/modules/dsa.md)，显式算并打印 LI-loss）不同：

- **默认日志级别下，SMLA 路径不额外计算/打印 LI-loss，也不调用 `DSAIndexerLossLoggingHelper.save_loss_to_tracker`**——避免在融合反向算子之外为了日志再重算一次 loss 带来的性能开销（额外计算 + 同步 + 日志记录）。
- 反向里的 LI-loss 计算被门控在 `logger.isEnabledFor(logging.DEBUG)` 之后：

```python
if logger.isEnabledFor(logging.DEBUG):
    li_loss = _compute_li_loss(softmax_out, cmp_softmax_l1, ctx.softmax_scale)
    if ctx.layer_number is not None:
        DSAIndexerLossLoggingHelper.save_loss_to_tracker(li_loss, ctx.layer_number, ctx.num_layers)
# torchtitan_npu/converters/kernels/npu_smla.py — _run_lightning_indexer_klloss_grad
```

### 调试：强制开启 LI-loss

如需在调试阶段查看 LI-loss，把 `torchtitan_npu.converters.kernels.npu_smla` logger 调到 `DEBUG` 级别：

```python
import logging
logging.getLogger("torchtitan_npu.converters.kernels.npu_smla").setLevel(logging.DEBUG)
```

开启后 SMLA 反向路径会额外计算 LI-loss（`_compute_li_loss` 用 `F.kl_div`：student=`softmax_out`，teacher=`cmp_softmax_l1` L1 归一化），并写入 `DSAIndexerLossLoggingHelper` tracker，后续按现有 indexer-loss 日志链路汇总打印。该模式仅建议用于问题定位或与 DeepSeek-V3.2 行为对齐验证；正式性能测试和生产训练应保持默认关闭，否则会引入额外计算、同步与日志记录开销。

## Evidence

- [torchtitan-npu](https://gitcode.com/cann/torchtitan-npu) — [`docs/feature_guides/npu_fused_ops.md`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/docs/feature_guides/npu_fused_ops.md)（『SMLA (Sparse Flash MLA)』节：A5/非 A5 分流、LI-loss 融合进 `npu_sparse_lightning_indexer_klloss_grad`、默认不打印、DEBUG 强制开启）
- [`torchtitan_npu/converters/kernels/npu_smla.py`](https://gitcode.com/cann/torchtitan-npu/blob/8f128cd177e9c9a14d9b70f4491bde28bc342481/torchtitan_npu/converters/kernels/npu_smla.py)（`NpuSMLAConverter` 硬件分流、`SparseFlashMLA` autograd、`_run_lightning_indexer_klloss_grad` DEBUG 门控、`@register_model_converter("npu_smla")`）

## Links

- [slig](slig.md)（V3.2 DSA 训练反向：显式 LI-loss + tracker；SMLA 把它融进 `klloss_grad` 并默认关日志）
- [sfag](sfag.md)（同批稀疏注意力训练反向算子 SFA Score Grad；SMLA 对应件为 `npu_sparse_flash_mla_grad`）
- [sasg](sasg.md)（同批稀疏注意力训练反向算子 SAS Grad；与 SMLA 同属 DSA 稀疏注意力反向训练件家族）
- [npu-fused-op-converters](../frameworks/npu_fused_op_converters.md)（ModelConverter 启用机制，经 `get_model_converter_config("npu_smla")` 注入）
- [deepseek-v4-continue-pretrain](../../guides/recipes/deepseek_v4_continue_pretrain.md)（V4 续训练实践，SMLA 是其稀疏 MLA 注意力路径）
- [mla](../../../inference/concepts/modules/mla.md)（跨域：MLA 注意力模块，SMLA 是其稀疏化训练融合路径）
- [dsa](../../../inference/concepts/modules/dsa.md)（跨域：DeepSeek Sparse Attention；V3.2 显式 LI-loss vs V4 SMLA 融合默认关）
- [lightning-indexer](../../../inference/concepts/kernels/lightning_indexer.md)（跨域：Lightning Indexer 正向算子，SMLA 反向融其 KL-loss）
