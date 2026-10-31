---
type: Optimization
title: DSA/MLA+MoE 量化转换 (convert_model.py) 的选择性层布局·clip 开关·MTP 分片导出陷阱
description: DSA/MLA+MoE 量化转换 (convert_model.py) 的选择性层布局·clip 开关·MTP 分片导出陷阱。给 DSA / MLA 类稀疏注意力 + MoE 模型跑昇腾量化权重转换（FP8 HF 权重 → BF16/INT8）时，转换脚本的「量化哪些层、是否开 clip、附加张量落哪个分片」配错会静默掉精度或破坏部分层。这些不是运行时 bug，而是转换期配置 / 导出逻辑的陷阱。
tags:
- task.optimization
- topic.speculative_decoding
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/1
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/104
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/46
  role: evidence
- resource: cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/utils/convert_model.py
  role: implementation
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:24Z'
platforms:
- agnostic
---

# DSA/MLA+MoE 量化转换 (convert_model.py) 的选择性层布局·clip 开关·MTP 分片导出陷阱

## 适用场景

给 [DSA](../../concepts/modules/dsa.md) / [MLA](../../concepts/modules/mla.md) 类稀疏注意力 + MoE 模型跑昇腾量化权重转换（FP8 HF 权重 → BF16/INT8）时，转换脚本的「量化哪些层、是否开 clip、附加张量落哪个分片」配错会静默掉精度或破坏部分层。这些不是运行时 bug，而是**转换期配置 / 导出逻辑**的陷阱。

## 规则 1：W8A8 选择性量化——只量化有收益且不敏感的层，其余保高精度

不要对全模型无差别量化。对 DSA+MoE：

- **量化谁**：[MLAProlog](../../concepts/kernels/mla_prolog.md) 除 `kv_b_proj`（下游会被拆分、量化后布局不契合）外的 Linear + MoE 路由/共享专家（GroupedMatmul）→ W8A8（权重/算力大头，有显存与时延收益）。
- **跳过谁**：[Sparse-Flash-Attention](../../concepts/modules/sparse_flash_attention.md)、[Lightning-Indexer](../../concepts/kernels/lightning_indexer.md)/IndexerProlog（名含 `indexer`）、`lm_head`、MoE 路由 `gate`——精度敏感 / 无 Linear 量化收益，量化易掉分。
- **KVCache** 保持 16-bit（`kv_cache_scheme: null`）即 W8A8**C16** 基线档，与也量化 KVCache 到 int8 的 [W8A8C8](../../concepts/quantization/w8a8c8.md)/[W4A8C8](../../concepts/quantization/w4a8c8.md) 区分。

当前转换器与HF导出配置使用同一generate_ignore_item结果，逐层跳过indexer.wk、indexer.weights_proj、kv_b_proj、kv_a_proj_with_mqa、q_a_proj、MoE gate、MTP eh_proj/shared_head.head及lm_head；indexer.wq_b仍可量化。旧“转换期仅两项、加载期另有宽表”已不适用，按生成后的实际名单核对。

**命名易混**：仓内 yaml 名 `*_w8a8.yaml`、字段 `A8W8`、flag `--quant_type`、配置 `int8_quantization_config.json` 全叫「w8a8」，但完整名是 **W8A8C16**（C16=KVCache 未量化）。读到「w8a8」不要默认 KVCache 也被量化——看 `kv_cache_scheme` 是否 `null`。

## 规则 2：clip 是可选开关（默认关），W8A8 不要求开 clip

转换工具 `--clip` 是 `store_true`、默认 `False`；W8A8/A8W8 权重转换**不要求**开 clip（维护者确认）。clip 关闭走标准 per-channel 对称 abs-max int8 量化；clip 开启则从 `quant_param_path` 载入学到的 clip 因子收窄量化范围（`if c8 and clip: assert quant_param_path is not None`）。出厂脚本对 `w8a8c8`/`w4a8c8` 默认传 `--clip` 并下载官方量化参数包，对 `w8a8c16`/`bfloat16` 不传——即「出厂 c8 recipe 用 clip」但「工具本身完整支持 clip 关闭」。低比特（W4A8）才更依赖 clip 抑制离群值，见 [precision-low-bit-quant-clip-clamp-outlier](precision_low_bit_quant_clip_clamp_outlier.md)。

## 陷阱 3（失败签名）：含 MTP 层分片导出，收尾阶段加载 / 写回分片错配

对含 MTP/nextn-predict 层的模型导出 W8A8C8 并开 `--c8`/`--clip` 后，**MTP 层量化结果错误、其余层正常**。根因：MTP 的 nextn-predict 层是最高层号（`num_layers = num_hidden_layers + num_nextn_predict_layers`），落在按名排序后的**最后一个** safetensors 分片；量化收尾阶段（注入 C8 [Hadamard](../../concepts/kernels/lightning_indexer.md) 矩阵 / clip 张量）若**加载的分片 ≠ 写回用的分片名**（加载首个分片却按最后一个分片名落盘），就把「首分片内容 + 附加张量」写到最后一个分片名下、覆盖真正承载 MTP 层的分片。修法：让收尾阶段**加载与写回指向同一个分片**，且必须是承载 MTP 层的最后一个分片（取分片列表末元素）。

一般原则：任何「读某分片→注入附加张量→按某分片名写回」的收尾步骤，加载分片必须与目标分片名严格一致；含 MTP/nextn-predict 层的模型尤其要落最后一个分片，否则静默破坏 MTP 权重、其余层看似正常、难定位。

## 参考实现及其约束

- 参考实现：cann-recipes-infer 的 [DeepSeek-V3.2-Exp](../../concepts/models/deepseek_v3_2_exp.md) `utils/convert_model.py`（`quant_ignore_layers` / `generate_ignore_item` / `int8_weight_quant` / `--clip` / MTP 收尾块）与 `weight_convert.sh`。
- 边界：规则 1 的具体跳过名单、规则 2 的出厂脚本行为限定到该模型及同结构 DSA+MoE 量化；「选择性量化 / clip 可选 / 收尾分片加载写回须一致」的判断可迁移到同类转换工具，不外推为整栈通用律。近无损精度佐证见 [benchmark-deepseek-v32-quant-accuracy](../benchmark_observations/benchmark_deepseek_v32_quant_accuracy.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/1)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/104)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/46)（evidence）
- [convert_model.py](../../../../../cann-recipes-raw/cann-recipes-infer/944d2d3ece86f7df33dbb0cb155c72ca619a9c66/models/deepseek_v3_2_exp/utils/convert_model.py)（implementation）
