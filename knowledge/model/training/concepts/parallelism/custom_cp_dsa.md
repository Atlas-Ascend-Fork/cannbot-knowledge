---
type: Concept
title: DSA 上下文并行（TND 与压缩 KV 布局）
description: 当前V3.2 rank-local TND metadata，以及V4/V4.1 doc-chunk、压缩frame/carry、对齐、量化/MTP组合和A3编译回退边界；撤下旧BSND裁剪与converter接口。
tags:
- task.design
- topic.parallelism
- topic.attention
- topic.data_movement.communication.collective_communication
status: stable
sources:
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/context_parallel.md
  role: primary
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/patches/torchtitan/distributed/context_parallel.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/ascendc.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/sharding.py
  role: implementation
- resource: cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/mtp.md
  role: supporting
created_at: '2026-06-11T00:00:00Z'
updated_at: '2026-10-29T13:21:58Z'
platforms:
- a3
- '950'
---

# DSA 上下文并行（当前 TND 与压缩 KV 布局）

## Summary

CP 沿序列切分 query 与训练输入，attention 仍需正确获得可见的 key/value。DSA 的 LI 与稀疏注意力不能直接靠通用 SDPA 替换解决；当前 TorchTitan NPU 使用模型/后端自己的 metadata、SPMD sharding 与输入布局，不再使用旧 CustomContextParallelContext、dsa_forward_with_cp、npu_dsa converter 或 enable_custom_context_parallel。

## V3.2：TND 与 rank-local varlen metadata

`patched_cp_shard` 识别 varlen metadata，先让上游切分输入，再以 CPVarlenMetadata.from_global 重建本 rank 的布局。该分支只接受 None/headtail，拒绝其他负载均衡器；混合 mask dict 保留字典形态，把其中 varlen 项替换为同一份 CP metadata。

AscSparseInnerAttention 的 Config 从 packed positions 构造共享 AscVarlenMetadata；同几何每个 microbatch 一次读取 Q/K 累计结束 offset，非逐层反复 D2H。CP metadata hook 使用切分前 positions 与 mesh、相同 headtail 规则重建累计长度，forward 用 k_global_gather_indices 恢复 key 行顺序。

当前 sharding 对主 Q 与 Indexer Q 按 head 维做 TP，MQA单KV头复制，目标 KV/Indexer K 在CP聚合；Indexer 的 TP R→I 转换由模型补齐，避免同时重分布TP/CP的限制。LI/SFA都消费TND与rank-local累计长度，不可继续使用旧BSND的“按rank×seq_len裁到一个slice_end”示例处理packed多文档。

辅助 Indexer loss 由 [SLIG](../kernels/slig.md) 的 backward 计算，并按全局有效token归一；主attention反向由 [SFAG](../kernels/sfag.md) 处理。V3.2 MTP当前拒绝CP>1，非MTP CP可用不代表该组合可用。

## V4 / V4.1：doc-chunk 与三个 frame

两栈都将每篇文档分成cp份。输入切分前按文档边界重排整行，再本地切片，query、labels、positions和预测深度保持同位；该输入置换本身不发生集合通信。key侧按需恢复到rank的slab，内核边界通过S(1)→R声明式聚合整行。

设文档长度L、rank r、CP度R，chunk宽Q=L/R，query可见key前缀reach=(r+1)*Q：

| frame | 网格与可见范围 |
|---|---|
| q | 整行文档边界/R，seqused=Q |
| swa_k | 整行文档边界，seqused=reach |
| cmp_k | 按该几何ratio折叠的边界，seqused=reach//ratio，保留需要的residual |

entry的position_k描述key slab自己的文档内位置。metadata与实际输入布局必须一致；不能只改cu_seqlens而不重算kernel metadata或实际重排行。

## 使能限制

- CP>1要求spmd_types后端和doc_chunk布局。显式headtail会被V4融合entry拒绝；metadata声明doc_chunk时，None也解析为它的布局。
- 每篇文档按lcm(compress_ratios)*CP对齐：V4为128*CP；当前V4.1的lcm为2。per_doc_alignment必须满足此倍数，单个chunk也必须是各ratio整数倍。
- 支持CP的是AscendC融合attention路径；参考attention metadata明确拒绝CP。V4.1还要求sparse_attn.asc与lightning_indexer.asc成对开启。参考压缩器可与融合attention配合，不能把参考压缩器能力等同于参考attention能力。
- V4/V4.1量化metadata目前拒绝CP重建，量化路径只允许CP1。
- V4的CP>1 carry路径要求local_batch_size=1，DSA路径TP固定1。CP1支持多行batch不代表CP>1也支持。

## V4 carry 与 V4.1 的差异

V4 ratio4压缩有重叠块。消费方先用key_stream把doc-chunk恢复为本地slab，CarryExchange获取前驱rank末块、prepend、按增强文档边界池化，随后trim掉carry输出；ratio128无此重叠。文档边界mask避免跨文档污染，所有rank包括空split都参与对应集合通信。CP1为恒等路径。

V4.1压缩器自身不感知CP：文档已按CP*ratio对齐，本地slab按ratio池化即可，无carry。ratio0为window-only，ratio1为第二路全分辨率KV，ratio2为压缩共享KV；frame随几何重建，不能把ratio1的residual字段当普通压缩残块。

## A3 key frame 与编译边界

arch22内核不读取key侧seqused、按frame末尾对齐mask，因此非末rank需把聚合key压为rank-local前缀；A3KeyWorkaround持有两路可微gather，反向scatter回整行后再reduce-scatter。其nonzero行数是动态device值，按microbatch/流产生同步。

arch22+CP>1会触发compile_policy告警并关闭编译、回退eager；CP1仍可编译。arch35读取reach frame，走其原生融合契约。评估性能须记录是否实际编译，不能把同一命令中的compile.enable当作已经入图。

## MTP 与数值验收

V4的future token、mask与label在全局切分前生成，再使用输入相同的CP布局；局部roll会跨rank错位。两端应加载同一份checkpoint，而非仅设同seed；保持文档对齐、样本、精度与deterministic设置一致。

先验布局置换/逆交换、peer split、frame因果边界和CP1恒等，再验多rank通信及数值。来源在特定arch35配置下给出step1 logits/loss逐位标准，梯度允许归约顺序量级差异；该标准不能泛化到arch22或任意kernel。长期loss/grad_norm应检查差距是否放大。本次未运行NPU或多rank作业。

## Evidence

- [context_parallel.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/context_parallel.md)（primary）
- [context_parallel.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/patches/torchtitan/distributed/context_parallel.py)（implementation）
- [ascendc.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/override/deepseek_v3_2/sparse_attn/ascendc.py)（implementation）
- [sharding.py](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/torchtitan_npu/models/deepseek_v3_2/sharding.py)（implementation）
- [mtp.md](../../../../../cann-recipes-raw/torchtitan-npu/8a71d8940e877cc9f2e5f4b977b4f18d48539592/docs/feature_guides/mtp.md)（supporting）

## Links

- [FSDP2](fsdp.md)
- [DSA Sharding](torchtitan_5d_parallel.md)
- [MTP训练](../modules/deepseek_v32_mtp_train.md)
- [MindSpeed CP家族](context_parallel_train.md)
