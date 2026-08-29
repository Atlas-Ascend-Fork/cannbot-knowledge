---
type: Optimization
title: Lightning-Indexer / Indexer-Prolog 低比特量化的精度要点 (Hadamard 旋转 + scale fp32 契约)
description: Lightning-Indexer / Indexer-Prolog 低比特量化的精度要点 (Hadamard 旋转 + scale fp32 契约)。把 Lightning-Indexer（DSA 稀疏选择）的 Q/K 压到 int8 计算取算力/时延收益（A8C8，Indexer BatchMatmul 走 int8、降 LI 时延）时，若直接量化会掉精度。两件事必须做对：量化前用 Hadamard 旋转摊平 Q/K 的离群值，以及把 W8A8 权重的量化 scale 喂给融合算子时必须走 fp32。压 Lightning-Indexer 单算子时延切量化算子的选型见 quant-lightning-indexer-latency。
tags:
- task.optimization
- topic.attention
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/8
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/7
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/63
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# Lightning-Indexer / Indexer-Prolog 低比特量化的精度要点 (Hadamard 旋转 + scale fp32 契约)

## 适用场景

把 [Lightning-Indexer](../../../concepts/kernels/lightning_indexer.md)（[DSA](../../../concepts/modules/dsa.md) 稀疏选择）的 Q/K 压到 int8 计算取算力/时延收益（[A8C8](../../../concepts/quantization/w8a8c8.md)，Indexer BatchMatmul 走 int8、降 LI 时延）时，若直接量化会掉精度。两件事必须做对：**量化前用 Hadamard 旋转摊平 Q/K 的离群值**，以及**把 W8A8 权重的量化 scale 喂给融合算子时必须走 fp32**。压 Lightning-Indexer 单算子时延切量化算子的选型见 [quant-lightning-indexer-latency](quant_lightning_indexer_latency.md)。

## 手段 1：q/k 处理顺序 rope → hadamard → quant

Indexer Q/K 分布含离群值，直接 Per-Token int8 量化会因少数大值撑大 scale、压垮多数值有效位宽。规则：在 rotary(rope) **之后**、量化**之前**插一次 hadamard 变换，把末维激活能量摊平、压低随后 per-block INT8/fp8 量化误差。缺这一步会放大量化精度损失。调用顺序（参考实现）：

```python
q_pe = apply_rotary_emb(q_pe, freqs_cis, False)      # 1) rope（indexer rope 为非交错）
q = rotate_activation(q)                              # 2) hadamard，rope 之后、量化之前
q_fp8, q_scale = act_quant(q, block_size, scale_fmt)  # 3) 量化

def rotate_activation(x):                             # hadamard 实现，输入须 bf16
    assert x.dtype == torch.bfloat16
    from fast_hadamard_transform import hadamard_transform
    return hadamard_transform(x, scale=x.size(-1) ** -0.5)   # scale = hidden_size ** -0.5
```

为何有效：归一化 Hadamard 矩阵（`H @ H.T = I`，`dim=128` 对齐 head_dim）是正交旋转，把单通道离群值的能量均摊到各维、压缩动态范围，使 Per-Token int8 的 scale 不被离群值撑大；旋转正交、可在反量化侧解析抵消，不改数值语义（QuaRot 类保精度通法）。转换期为每层预置该 128×128 Hadamard 参数。DeepSeek 参考用 fp8，cann-recipes-infer 昇腾侧沿用同一 hadamard-after-rotary 方案但配 INT8 组成 A8C8。

## 手段 2：W8A8 权重的量化 scale 直传融合算子须走 fp32

当把某 W8A8 权重的 `weight_scale` 作为独立入参喂给融合算子时（如 [PyPTO](../../../concepts/frameworks/pypto.md) 版 [Indexer-Prolog](../../../concepts/kernels/indexer_prolog.md) 融合算子入参 `wq_b_scale=self.wq_b.weight_scale`），必须把该权重登记进 runner 的 `float_scales_map`、令其 scale 以 fp32 传入。沿用默认（非 fp32）scale 会引发精度回归（对应修复提交标题即 `bugfix wq_b scale use fp32`）。

- **判断信号**：融合算子入参里出现 `<weight>_scale = self.<weight>.weight_scale` 这种「把某 W8A8 权重 scale 直传算子」的写法。
- **处置**：检查该权重是否已在 `float_scales_map` 内；不在就加入，使其量化 scale 走 fp32 再喂算子，否则算子拿到的 scale dtype 与其 fp32 期望不匹配、数值失配→精度回归。

## 参考实现及其约束

- 手段 1 参考实现：DeepSeek-V3.2-Exp `inference/model.py` 的 `Indexer.forward`（rope→`rotate_activation`→`act_quant`），cann-recipes-infer 昇腾侧沿用（`indexer.py` / `convert_model.py` 每层写入归一化 128×128 Hadamard）。
- 手段 2 参考实现：cann-recipes-infer DeepSeek-V3.2-Exp 的 `runner_deepseek.py::float_scales_map` + `indexer.py` pypto indexer-prolog 融合算子（`wq_b` 一处）。
- 边界：手段 2 证据只覆盖 `wq_b` 一处，规则限定「融合算子直传某 W8A8 权重量化 scale」这一类接入；手段 1 适用面限定到 Indexer/attention q/k 低比特量化，不外推为整栈通用律。`float_scales_map` 的确切内部语义（对表内权重 weight_scale 做 fp32 cast）为命名 + 相邻注释 + bugfix 推断，核心 diff 事实是「scale 须 fp32」这一处置本身。

## Evidence

- diff 事实 + doc 披露（@2c45117）：`indexer.py`（`apply_hadamard`/`get_had_pow2`/int8 前向）+ `convert_model.py`（`generate_li_hadamard_matrix` 每层归一化 128×128 Hadamard）；「摊平离群值缓解掉精度」为正交旋转原理 + doc 收益陈述、无独立复测精度。溯源下探 [cann-recipes-infer-issue-8-rfc-deepseek-v3-2-exp-w8a8c8](https://gitcode.com/cann/cann-recipes-infer/issues/8)
- diff 事实 (DeepSeek 参考) + 维护者两次确认：`Indexer.forward` 的 rope→rotate_activation→act_quant、`hadamard_transform(x, scale=hidden_size**-0.5)`；维护者确认昇腾侧沿用 hadamard + INT8「精度损失最小」，cann 侧 merged-PR diff 未定位（实现级细节以维护者确认为准）。溯源下探 [cann-recipes-infer-issue-7-requirement-rotary-hadamard](https://gitcode.com/cann/cann-recipes-infer/issues/7)
- diff 事实（@c7d9383f190c）：`float_scales_map` 增 `"wq_b"`、`indexer.py` 入参 `wq_b_scale=self.wq_b.weight_scale`，动机取自提交 `bugfix wq_b scale use fp32`。溯源下探 [cann-recipes-infer-pr-63-feat-enable-index-prolog-pypto-fusion-ops-in-decode-stage](https://gitcode.com/cann/cann-recipes-infer/merge_requests/63)

<!-- cannbot:related:start -->
## 相关

- [Indexer Prolog Kernel](../../../concepts/kernels/indexer_prolog.md)（`related`）：“当把某 W8A8 权重的 `weight_scale` 作为独立入参喂给融合算子时（如 ［PyPTO］(../../../concepts/frameworks/pypto.md) 版 ［Indexer-Prolog］(../../../concepts/kernels/indexer_prolog.md) 融合算子入参 `wq_b_scale=self.wq_b.weight_scale`），必须把该权重登记进 runner 的 `float_scales_map`、令其 scale 以 fp32 传入。沿用默认（非 fp32）scale 会引发精度回归（对应修复提交标题即 `bugfix wq_b scale use fp32`）。”明确 `wq_b_scale` 直传 Indexer-Prolog 时必须保持 FP32；“`Indexer Prolog` 是 ［lightning-indexer］(lightning_indexer.md) 之前的准备算子，为 LI 计算提供输入 `q`、`weight`（及 `q_scale`）。它处理三条独立计算流 —— **Indexer Q**、**Indexer Cache (K)**、**Indexer Weight** —— 每条流都包含 Matmul / RoPE / LayerNorm / Hadamard / 动态 Per-Token-Head 量化 等一连串 Linear 前后处理。”定位该算子正是生成 LI 的 q/q_scale/weight 的前置链。联合阅读可在融合入口核对 scale dtype 和 Hadamard→量化顺序。
- [Lightning Indexer Kernel](../../../concepts/kernels/lightning_indexer.md)（`related`）：“`LightningIndexerQuant` 输入 $Q_{index}^{INT8}, K_{index}^{INT8}$ + 反量化系数 $Scale_Q, Scale_K$（Per-Token-Head A8C8）。直接实现需要多步 Vector 操作。”；“规则：在 rotary(rope) **之后**、量化**之前**插一次 hadamard 变换，把末维激活能量摊平、压低随后 per-block INT8/fp8 量化误差。”。量化 LI 的 A8C8 输入契约与上游 rope→Hadamard→quant 顺序相接，能用于避免直接量化的精度回归。
- [QuantLightningIndexer 950 ACLNN 算子知识](../../../../../ops/ascendc/operators/aclnn/transformer/attention/quant_lightning_indexer_950.md)（`related`）：｜ 计算语义 ｜ 对量化 `query` 与 `key` 做 `Q·K^T`，乘 `query_dequant_scale × key_dequant_scale`、ReLU 后按 `weights` 沿 G 聚合，再对 S2 轴取 Top-k 索引。 ｜；把 ［Lightning-Indexer］(../../../concepts/kernels/lightning_indexer.md)（［DSA］(../../../concepts/modules/dsa.md) 稀疏选择）的 Q/K 压到 int8 计算取算力/时延收益（［A8C8］(../../../concepts/quantization/w8a8c8.md)，Indexer BatchMatmul 走 int8、降 LI 时延）时，若直接量化会掉精度。两件事必须做对：**量化前用 Hadamard 旋转摊平 Q/K 的离群值**，以及**把 W8A8 权重的量化 scale 喂给融合算子时必须走 fp32**。压 Lightning-Indexer 单算子时延切量化算子的选型见 ［quant-lightning-indexer-latency］(quant_lightning_indexer_latency.md)。。950 算子在量化 Q/K 路径消费 query/key 反量化 scale，精度规则给出进入低比特 Indexer 前的 rope→Hadamard→quant 顺序和 scale 精度要求，可直接支撑该接口输入的生产与精度验证。
- [压 LightningIndexer 单算子时延优先切量化算子 npu_quant_lightning_indexer（INT8 存8算8）](quant_lightning_indexer_latency.md)（`related`）：“把 ［Lightning-Indexer］(../../../concepts/kernels/lightning_indexer.md)（［DSA］(../../../concepts/modules/dsa.md) 稀疏选择）的 Q/K 压到 int8 计算取算力/时延收益（［A8C8］(../../../concepts/quantization/w8a8c8.md)，Indexer BatchMatmul 走 int8、降 LI 时延）时，若直接量化会掉精度。两件事必须做对：**量化前用 Hadamard 旋转摊平 Q/K 的离群值**，以及**把 W8A8 权重的量化 scale 喂给融合算子时必须走 fp32**。压 Lightning-Indexer 单算子时延切量化算子的选型见 ［quant-lightning-indexer-latency］(quant_lightning_indexer_latency.md)。”给出切入低比特后的 Hadamard 与 FP32 scale 精度合同；“昇腾 Atlas A3 上做 DeepSeek 系 ［dsa］(../../../concepts/modules/dsa.md)（DeepSeek 稀疏 attention，［deepseek-v3.2-exp］(../../../concepts/models/deepseek_v3_2_exp.md) 使用）推理，需要**降低 ［lightning-indexer］(../../../concepts/kernels/lightning_indexer.md) 的单算子时延**时：从 fp16 非量化版切到量化版算子 **`npu_quant_lightning_indexer`**——把 Q/K 量化到 INT8「存8算8」（在 int8 上完成 Q@K 相关性 + 沿 head 方向选 top-k key 索引），该量化版对 Vector 做了优化。”给出因时延瓶颈选择 npu_quant_lightning_indexer 的条件。两页共同覆盖先选量化路径、再保证量化精度的完整决策。
<!-- cannbot:related:end -->
