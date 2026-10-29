---
type: Optimization
title: 为 MoE+MLA+MTP 模型做混合精度量化的配置陷阱：保留不量化层·激活分支按位宽子串门控
description: 为 MoE+MLA+MTP 模型做混合精度量化的配置陷阱：保留不量化层·激活分支按位宽子串门控。你在昇腾栈上为「MoE 路由 + MLA + MTP/next-n」结构的模型（参考实现覆盖 DeepSeek-R1 / DeepSeek-V3.2-Exp / Kimi-K2-Thinking 同一 DeepseekV3 建模）做 compressed_tensors 混合精度量化（W8A8(C8) / W4A8）的转换与 bringup。以下两类配置错误会静默掉精度或静默回落非量化慢路径。
tags:
- task.optimization
- topic.speculative_decoding
- topic.precision
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/113
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/187
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-20T12:49:18Z'
platforms:
- agnostic
---

# 为 MoE+MLA+MTP 模型做混合精度量化的配置陷阱：保留不量化层·激活分支按位宽子串门控

## 适用场景

你在昇腾栈上为「MoE 路由 + [MLA](../../concepts/modules/mla.md) + [MTP/next-n](../../concepts/techniques/mtp_speculative_decoding.md)」结构的模型（参考实现覆盖 DeepSeek-R1 / DeepSeek-V3.2-Exp / Kimi-K2-Thinking 同一 DeepseekV3 建模）做 compressed_tensors 混合精度量化（[W8A8(C8)](../../concepts/quantization/w8a8c8.md) / [W4A8](../../concepts/quantization/w4a8c8.md)）的转换与 bringup。以下两类配置错误会**静默**掉精度或**静默**回落非量化慢路径。

## 规则 1：router gate / lm_head / MTP 层保持不量化，且别只靠上游 ignore 列表兜底

条件 → 做什么：量化 DeepseekV3 家族时，router `gate`（MoE 路由门控，`params_dtype=float32`）、`lm_head`（输出投影）、MTP/next-n 层的 `eh_proj`（`2*hidden → hidden` 融合投影）与 `shared_head.head` 必须保持**不量化**——路由权重量化会扰动专家选择。

陷阱（反例）：不要只靠上游 checkpoint 随附的 compressed_tensors ignore 列表来排除这些层——上游 config 可能漏配。观测：某上游 config 未把 `gate` 放进 ignore，直接套用会误量化 gate。

双保险做法：
1. 转换阶段自己生成 ignore 列表覆盖不应量化的层（随 MTP/next-n 层数扩展到其 `eh_proj` / `shared_head.head`），不复用上游可能残缺的 ignore。
2. 建模层对这些 Linear 显式传 `quant_config=None`，作为绕过 ignore 缺项的第二道闸。

依据：维护者明确「默认 gate 都是不做量化的」；转换器 ignore 列表 + 三个模型建模层的相应改动一致采用此模式。

## 规则 2：激活量化融合分支按位宽子串门控，别精确匹配整体量化模式

条件 → 做什么：为已有 W8A8 路径的模型新增激活 int8 的混合精度变体（W4A8 / W4A8C8…）时，多个变体**共享同一激活级融合内核**的分支应按**激活位宽子属性**门控 `"a8" in quant_mode`，而非精确匹配整体模式字面量 `== "w8a8"`。这样 W8A8 与 W4A8 自动复用同一 A8 路径（MoE gmm 的 `quant_mode`/`scale`、`npu_moe_init_routing_v2`、`npu_dequant_swiglu_quant`、MLA 的 `npu_dynamic_quant` + MLAProlog dequant scales）。

陷阱（反例 = supersede 的 failure_signature）：激活融合分支写死精确 `== "W8A8"` 时，新接入的 W4A8 掉出**全部** A8 融合路径、静默回落非量化慢路径。接入新激活 int8 变体前先确认这些分支不是精确写死。

表示约定：量化模式用按逐张量位宽派生的**小写字符串**（权重 `"w"+bits`、激活 `"a"+bits` 拼成 `"w8a8"`/`"w4a8"`；kv-cache 用 `type + str(bits)` 如 `"int8"`，无量化 `"unquant"`），小写以对齐开源 quant_config 的 `type` 字段。

例外（仍用精确门控，不放宽为子串）：
1. **分支专属单一模式**——DenseMLP / SharedExpert 的 `down_proj_forward` 仍用精确 `== "w8a8"`（当前只有 w8a8 走该分支）。
2. **kv-cache 量化**——用精确 `kv_cache_quant_mode == "int8"`：kv 侧只区分 int8 vs unquant 单一路径、无多激活位宽复用（控制 int8 cache dtype 分配、offload_cache INT8 拼接布局、indexer_prolog pypto 融合、MLA FIA 的 `query_quant_mode=3` + dequant scales）。

判据：**多变体共享同一激活内核 → 子串门控；单一特定模式/单量化路径专属 → 精确门控。**

## 适用边界

范围限定 DeepseekV3 家族这几个建模/转换文件，不外推为昇腾栈通用律。规则本身（哪些层别量化、激活分支按位宽子串门控）对同结构（MoE 路由 + MLA + MTP + 多激活位宽量化）可迁移；具体层名/字符串是该参考实现的形态，不是技术边界。源未给量化这些层会造成的具体精度数字。

## Evidence

- 维护者确认 + diff 事实（clone `@2c45117`）：Discussion 中维护者「gate 不会量化，可以直接传 None」「默认 gate 都是不做量化的，K2 原始的 config 就没在 ignore 里配置 gate，直接拿过来用就有问题」；转换器 ignore 列表新增 MTP 层 `eh_proj`/`shared_head.head`，三模型 `lm_head`（及 V3.2-Exp 建模层 `gate`/`eh_proj`）改 `quant_config=None`。
  - 溯源下探：[cann-recipes-infer-pr-113-feat-modify-quant-config-ignore-in-kimi-k2-thinking-and-deepseek-r1-and](https://gitcode.com/cann/cann-recipes-infer/merge_requests/113)
- diff 事实（clone `@6293961c1089`）：`compressed_tensors.py` 的 quant_mode 由位宽拼串、kv 布尔→字符串泛化；三份 DeepSeek modeling 的 mm/gmm 用 `"a8" in`、`down_proj` 用精确 `== "w8a8"`；`indexer.py`/`offload_cache.py` 的 kv 用精确 `== "int8"`。
  - 溯源下探：[cann-recipes-infer-pr-187-fix-w4a8-a8](https://gitcode.com/cann/cann-recipes-infer/merge_requests/187)