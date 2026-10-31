---
type: Concept
title: SMLA（Sparse Flash MLA，DeepSeek-V4 稀疏 MLA 融合算子）
description: 当前 DeepSeek-V4 TND SMLA/SMLAG 与独立 LI/SLIKG override：backend-owned metadata、teacher 梯度载体、CP 归一及 A3 key-frame 适配。
tags:
- task.implementation
- topic.attention
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/sparse_attn/__init__.py
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/sparse_attn/ascendc.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/lightning_indexer/ascendc.py
  role: implementation
created_at: '2026-06-23T00:00:00Z'
updated_at: '2026-10-29T15:24:41Z'
platforms:
- a3
- '950'
---

# SMLA：DeepSeek-V4 稀疏 MLA 训练融合

## Summary

当前 DeepSeek-V4 稀疏注意力使用独立 override：`override.deepseek_v4.sparse_attn.asc` 提供 SMLA/SMLAG，`override.deepseek_v4.lightning_indexer.asc` 提供 LI/SLIKG。训练 Indexer 必须配对选择二者，前者产生 teacher，后者消费其梯度边。旧 npu_smla ModelConverter、逐模块替换和按硬件切换旧 build_op 的使用方法已移除。

## 数据布局与后端元数据

内核来自 cann_ops_transformer，使用 TND；q/k/v 按训练 autocast 契约为 bf16，sink 为 fp32。包装器将模型 [B,L,...] 展平为 token 维，Shared-KV 增加单头维。索引从 [B,L,K] 改为 [T,1,K]，保持文档内编号与 -1 填充语义。

每种 geometry 的 Config.build_attention_metadata 在 microbatch 边界建立 AscV4Metadata，包含 LI、SLIKG、SMLA、SMLAG 的预计算 records，供该 geometry 的各层复用。CP 重新切分 frames 后必须重建对应 records。元数据不匹配会 TypeError，融合路径没有内联回退。

默认 entry geometry 为 V4-Flash 的主注意力 64 heads×512，Indexer 64 heads×128；其他宽度需显式声明。window_size/index_topk 由模型配置提供。ratio=4 使用稀疏压缩选择，ratio=128 的压缩分支走全因果前缀，其 metadata 的 cmp_topk=0。压缩分支没有完整压缩块时会报错。

## 正反向与 teacher 边

正向 `sparse_flash_mla` 返回输出与 softmax_lse；LSE 标为不可微。反向 `sparse_flash_mla_grad` 产生 dquery、dori_kv、dcmp_kv、dsinks，以及压缩注意力边际量。没有压缩 KV 时 dcmp_kv 返回 None。

训练时的 topk_scores 是 autograd carrier，数值本身不参与注意力。SMLAG 将无效索引位置的 teacher 清零，再乘一次 softmax_scale，经该 carrier 的梯度传给 Indexer。eval 不传此 carrier。

LI 在自身 Function 内按索引降序规范排序，使有效位置在前、-1 在后，并确保保存的索引顺序与 teacher 槽位一致；在 Function 外重新排序会破坏配对。其 backward 用整行 query-token 数归一 teacher，再调用 sparse_lightning_indexer_kl_loss_grad 产生 dq/dk/dw。CP 下不能改用本 rank token 数，否则参数梯度会多出 CP 倍数。

当前实现不再包含旧 logger DEBUG 下重算并记录 LI-loss 的使用方式；梯度 carrier 不应当作可直接打印的 loss 数值。

## CP 与硬件边界

frames 分别描述 query、滑窗 KV 与压缩 KV 的文档边界、有效长度和残余块。CP 在 wrapper 边界收集 KV，按 rank 的可见范围计算。arch22 的内核将 key-frame 末尾作为 mask 锚点，不读取该处 seqused，所以 metadata 边界构建 A3KeyWorkaround，wrapper 将两种 KV 压紧到可见范围，梯度通过 index_select 反传到原行。

这与旧的 seq_len/cp_degree、rank 前缀长度简化公式不同；packed 文档必须保留完整 frames 契约。平台与精度结果需结合当前 recipe 单独验证，本页未运行 NPU。

## Evidence

- [__init__.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/sparse_attn/__init__.py)（primary）
- [ascendc.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/sparse_attn/ascendc.py)（implementation）
- [ascendc.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v4/lightning_indexer/ascendc.py)（implementation）

## Links

- [SAS 训练反向](sasg.md)
- [V3.2 Indexer 梯度](slig.md)
- [融合算子配置](../frameworks/npu_fused_op_converters.md)
- [上下文并行](../parallelism/context_parallel_train.md)
