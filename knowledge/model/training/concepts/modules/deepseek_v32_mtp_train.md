---
type: Concept
title: DeepSeek-V3.2 / V4 MTP 训练（串联预测与损失）
description: 当前独立 mtp_layers、num_mtp_layers 构造参数、packed sequence 位移、全局 token 损失归一化；区分 V3.2 logits 与 V4 mHC/chunk loss、CP 及可选梯度隔离。
tags:
- task.design
- topic.model_architecture
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/mtp.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/__init__.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/model.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v4/mtp.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v4/config_registry.py
  role: implementation
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-10-29T15:24:41Z'
platforms:
- agnostic
---

# DeepSeek-V3.2 / V4 MTP 训练（串联预测深度与损失）

## Summary

训练 MTP 在主 NTP 任务之后增加串联的辅助预测深度，第 k 个深度融合左移 k 位的 token embedding 与上一深度 hidden，预测更远的 token。它与推理侧把 MTP 头用于 [投机解码](../../../inference/concepts/techniques/mtp_speculative_decoding.md) 的目标不同，不能把训练辅助损失配置直接当成推理策略。

当前独立参数放在 `model.mtp_layers`，不再混在主干 `model.layers` 的尾部；不再使用旧 `TrainingConfig.num_mtp_modules`、`mtp_loss_weight` 或旧 loss monkey-patch。关闭时配置列表为空、运行时 mtp_layers 为 None，模型返回普通单一输出。

## 两种状态结构

| 路线 | 主干/MTP state | 每个深度的计算 | 预测输出 |
|---|---|---|---|
| V3.2 | `[B,S,H]` | enorm/hnorm → 拼接 → eh_proj → 独立 DSA Transformer block | 共享 LM head 的 logits |
| V4 | `[B,S,hc_mult,H]` | token/hidden 分别投影，embedding 广播到 mHC 流，再 HcPre→Attention→HcPost 与 FFN 分支 | 独立 HcHead 产生三维 prediction hidden，共享 LM head；多流 state 继续串联 |

V3.2 的 MTP block 复用 DSA 配置但不与主干末层共享参数。V4 MTP 保留 mHC 多流状态，attention 使用非压缩形式，不启用主干 compressor/indexer。不能先把多流 state 合成普通三维张量再继续深度链。

## 位移、文档边界和损失

`roll_mtp_sequence` 同时生成移位 token 和 valid_mask，排除序列尾部不足位置及 packed sequence 跨文档位置；无效的前一深度状态也不传给当前深度。模型返回 `[主预测, 深度1, ..., 深度K]`，loss 用相同 positions 规则移动 labels：

```text
L = L_main + mtp_scale / K * sum(L_mtp,k)
```

各分支使用 token-sum 交叉熵，再按全局有效 token 数统一归一化。模型与 loss 必须成套启用：只增加 MTP 层或只切换 loss 都会破坏输入输出契约。

- V3.2 直接复用社区 `list[logits] + MTPLoss`，当前不适配 chunk loss。
- V4 默认 `list[hidden] + MTPChunkedLossWrapper`，逐分支复用上游 sequence chunk、LM head FSDP、梯度累加和 decoder backward bridge，避免完整 `[B,S,V]` logits。分支权重在分块内部 backward **之前**应用，不能在最终标量上事后相乘替代梯度缩放。

## 当前配置方式

`num_mtp_layers` 是 model_registry 的模型构造参数，应在 Python recipe 同时设置模型与 loss。例如 V3.2：

```python
config.model_spec = model_registry("debugmodel", num_mtp_layers=2)
config.loss = MTPLoss.Config(
    mtp_scale=0.3,
    global_vocab_size=decoder_vocab_size(config.model_spec),
)
```

V4 对应使用 `MTPChunkedLossWrapper.Config`，配置 mtp_scale、num_chunks 及内部 CrossEntropyLoss 的 global_vocab_size。默认 V4 debugmodel recipe 已构造一个 MTP 深度、mtp_scale0.3，不需另找旧 `_mtp` 包装入口；V3.2 NPU 注册表没有重复声明专用 MTP recipe。以当前 registry 为准，不再照抄旧 TOML 名称。

## CP 组合边界

V4 先在 CP 切分前的完整行生成各深度 future token、有效 mask 与监督 label，再用与输入/label/positions 相同的 doc_chunk 布局切分，保证 rank-local token 对齐；不要在局部序列直接 roll，否则 rank 边界错误。该位移准备不额外引入跨 rank P2P。

V3/V3.2 的社区 MTP 仍在 CP>1 时于配置更新阶段拒绝，不能由其非 MTP CP 能力推出此组合可用。V4 的压缩 attention metadata 和 CP plan 继续遵守自身契约。

## V4 的可选梯度隔离

`--loss.mtp-isolate-gradients` 默认关闭，主要用于 RL 中继续训练 MTP 而不让其辅助损失直接改变主干策略梯度。开启后截断主干 hidden→MTP，阻止 MTP 更新共享 embedding 与 LM head，但 LM head 仍向 MTP hidden 传梯度，主 NTP 仍可更新共享参数。

前向、损失公式和 checkpoint 参数形状/名称不变；适用原生 Linear LM head 与 MTPChunkedLossWrapper。它只隔离直接梯度，现有全局梯度裁剪仍将两组裁剪系数关联起来，不能称作完全独立优化。

## 接入与验证

公共 roll、MTPLoss、MTPTransformerBlock/MTPDecoder 来自社区 DeepSeek V3；NPU 的 V3.2 仅叠加 DSA mask/sharding，V4 补充 mHC、CP batch、分块损失和共享投影梯度边界。MTP blocks 沿主干相应的 TP/SP、EP、重计算、compile/FSDP 处理，不能仅凭加入参数列表省略切分检查。

复核相同输入/权重下各预测深度的 label shift、packed 边界、总损失权重、共享参数与 MTP 梯度，以及 save/load 后行为；隔离模式另检查主路梯度和全局裁剪。本文为源码与文档复核，未执行 NPU 训练。

## Evidence

- [mtp.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/mtp.md)（primary）
- [__init__.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/__init__.py)（implementation）
- [model.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/model.py)（implementation）
- [mtp.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v4/mtp.py)（implementation）
- [config_registry.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v4/config_registry.py)（implementation）

## Links

- [TorchTitan NPU](../frameworks/torchtitan.md)
- [V3.2 训练](../../guides/recipes/deepseek_v32_pretrain.md)
- [V4 训练](../../guides/recipes/deepseek_v4_continue_pretrain.md)
- [Chunk Loss](../techniques/chunk_loss.md)
