---
type: Optimization
title: 压 LightningIndexer 单算子时延优先切量化算子 npu_quant_lightning_indexer（INT8 存8算8）
description: 昇腾 Atlas A3 上做 DeepSeek 系 dsa（DeepSeek 稀疏 attention，deepseek-v3.2-exp 使用）推理，需要降低 lightning-indexer 的单算子时延时：从 fp16 非量化版切到量化版算子 npu_quant_lightning_indexer——把 Q/K 量化到 INT8「存8算8」（在 int8 上完成 Q@K 相关性 + 沿 head 方向选 top-k key 索引），该量化版对 Vector 做了优化。
tags:
- task.optimization
- topic.attention
- topic.precision
- topic.long_context
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/23
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-07-06T00:00:00Z'
platforms:
- a3
---

# 压 LightningIndexer 单算子时延优先切量化算子 npu_quant_lightning_indexer（INT8 存8算8）

## 条件 → 优先尝试

昇腾 Atlas A3 上做 DeepSeek 系 [dsa](../../../concepts/modules/dsa.md)（DeepSeek 稀疏 attention，[deepseek-v3.2-exp](../../../concepts/models/deepseek_v3_2_exp.md) 使用）推理，需要**降低 [lightning-indexer](../../../concepts/kernels/lightning_indexer.md) 的单算子时延**时：从 fp16 非量化版切到量化版算子 **`npu_quant_lightning_indexer`**——把 Q/K 量化到 INT8「存8算8」（在 int8 上完成 Q@K 相关性 + 沿 head 方向选 top-k key 索引），该量化版对 Vector 做了优化。

LightningIndexer 是 DSA 的前处理算子：算 index query × index key 相关性后沿 head 方向选 top-k key 索引，长序列下是稀疏注意力的时延热点之一。

## 依据

维护者确认：量化版已发布、对 Vector 做了优化，列为该场景推荐路径。算子调用约定 / 参数 / 约束（INT8 Q/K、Per-Token-Head 量化、`layout_key=PA_BSND`、N1=64、D=128、`sparse_count`、图模式支持、需配 `..._metadata` 先算分核信息等）为 canonical 静态内容，见 [lightning-indexer](../../../concepts/kernels/lightning_indexer.md)，此处不复制其规格。DSA 长序列 Prefill 的并行选型另见 [long-seq-prefill-context-parallel](long_seq_prefill_context_parallel.md)。

## 取舍 / 反例 / rollback

- INT8 引入 Q/K 精度取舍；量化版比 fp16 版有更强的布局/量化约束（见静态页）。
- **无量化前后收益数字**：仓自报 BSZ=16 / seq_len=8k 下 fp16 版 ~60us 及 top-k 耗时占比，但维护者显式推迟「测试确认后再答复」、该讨论内未给确认；故加速幅度不可量化，不写任何量化收益 / 单调规律。
- rollback：回退到 fp16 非量化 LightningIndexer 路径。

## 相关经验
- [DSA/SFA 长序列服务化：跨步复用 top-k 索引（IndexCache）摊薄 ind](../benchmark_observations/dsa_indexcache_topk_reuse_throughput.md)

## Evidence

- **代码事实**（clone `@2c45117`）：`ops/ascendc/docs/custom-npu_quant_lightning_indexer.md` 功能说明原文「对输入 query 和 key 进行量化实现存8算8，获取最大收益」，含 top-k 选择、int8 Q/K、Per-Token-Head 量化、PA_BSND、图模式、Atlas A3 支持。
- **维护者确认**：「现在量化版本已经发布，对 Vector 做了优化，建议关注量化版本」。
- **命名漂移（diff 事实）**：维护者曾在 master 引用文件名 `custom-npu_lightning_indexer_quant.md`；clone `@2c45117` 处已改名 `custom-npu_quant_lightning_indexer.md`（同一算子）。
- 溯源下探：[cann-recipes-infer-issue-23-question-lightningindexer](https://gitcode.com/cann/cann-recipes-infer/issues/23)

<!-- cannbot:related:start -->
## 相关

- [Lightning Indexer Kernel](../../../concepts/kernels/lightning_indexer.md)（`related`）：“`LightningIndexerQuant` 输入 $Q_{index}^{INT8}, K_{index}^{INT8}$ + 反量化系数 $Scale_Q, Scale_K$（Per-Token-Head A8C8）。直接实现需要多步 Vector 操作。”；“需要**降低 ［lightning-indexer］(../../../concepts/kernels/lightning_indexer.md) 的单算子时延**时：从 fp16 非量化版切到量化版算子 **`npu_quant_lightning_indexer`**——把 Q/K 量化到 INT8「存8算8」（在 int8 上完成 Q@K 相关性 + 沿 head 方向选 top-k key 索引），该量化版对 Vector 做了优化。”。目标卡把焦点的 A8C8 kernel 规格转成 A3 单算子降时延的明确选型和回退决策。
- [Lightning-Indexer / Indexer-Prolog 低比特量化的精度要点 (Hadamard 旋转 + scale fp32 契约)](precision_lightning_indexer_low_bit_quant.md)（`related`）：“把 ［Lightning-Indexer］(../../../concepts/kernels/lightning_indexer.md)（［DSA］(../../../concepts/modules/dsa.md) 稀疏选择）的 Q/K 压到 int8 计算取算力/时延收益（［A8C8］(../../../concepts/quantization/w8a8c8.md)，Indexer BatchMatmul 走 int8、降 LI 时延）时，若直接量化会掉精度。两件事必须做对：**量化前用 Hadamard 旋转摊平 Q/K 的离群值**，以及**把 W8A8 权重的量化 scale 喂给融合算子时必须走 fp32**。压 Lightning-Indexer 单算子时延切量化算子的选型见 ［quant-lightning-indexer-latency］(quant_lightning_indexer_latency.md)。”给出切入低比特后的 Hadamard 与 FP32 scale 精度合同；“昇腾 Atlas A3 上做 DeepSeek 系 ［dsa］(../../../concepts/modules/dsa.md)（DeepSeek 稀疏 attention，［deepseek-v3.2-exp］(../../../concepts/models/deepseek_v3_2_exp.md) 使用）推理，需要**降低 ［lightning-indexer］(../../../concepts/kernels/lightning_indexer.md) 的单算子时延**时：从 fp16 非量化版切到量化版算子 **`npu_quant_lightning_indexer`**——把 Q/K 量化到 INT8「存8算8」（在 int8 上完成 Q@K 相关性 + 沿 head 方向选 top-k key 索引），该量化版对 Vector 做了优化。”给出因时延瓶颈选择 npu_quant_lightning_indexer 的条件。两页共同覆盖先选量化路径、再保证量化精度的完整决策。
- [QuantLightningIndexer 950 ACLNN 算子知识](../../../../../ops/ascendc/operators/aclnn/transformer/attention/quant_lightning_indexer_950.md)（`related`）：｜ 计算语义 ｜ 对量化 `query` 与 `key` 做 `Q·K^T`，乘 `query_dequant_scale × key_dequant_scale`、ReLU 后按 `weights` 沿 G 聚合，再对 S2 轴取 Top-k 索引。 ｜；昇腾 Atlas A3 上做 DeepSeek 系 ［dsa］(../../../concepts/modules/dsa.md)（DeepSeek 稀疏 attention，［deepseek-v3.2-exp］(../../../concepts/models/deepseek_v3_2_exp.md) 使用）推理，需要**降低 ［lightning-indexer］(../../../concepts/kernels/lightning_indexer.md) 的单算子时延**时：从 fp16 非量化版切到量化版算子 **`npu_quant_lightning_indexer`**——把 Q/K 量化到 INT8「存8算8」（在 int8 上完成 Q@K 相关性 + 沿 head 方向选 top-k key 索引），该量化版对 Vector 做了优化。。950 卡闭合 npu_quant_lightning_indexer 的量化计算与 TopK 实现，选型规则说明为降低 LI 时延时从 FP16 切到该量化算子的条件与回退路径，直接连接实现与性能选型。
<!-- cannbot:related:end -->
