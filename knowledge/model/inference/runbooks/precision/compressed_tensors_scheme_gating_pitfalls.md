---
type: Runbook
title: compressed-tensors 量化加载器的方案识别门控陷阱：别假设总有激活量化、MX 与普通 fp8 靠 weight_block_size 区分、AWQ int4 走 W4A16
description: compressed-tensors 量化加载器的方案识别门控陷阱：别假设总有激活量化、MX 与普通 fp8 靠 weight_block_size 区分、AWQ int4 走 W4A16。在昇腾上加载 compressed-tensors 格式的量化权重时，加载器要从 config 判断「这是哪种量化方案」并路由到对应 Linear method。判据写得过窄/过宽都会让某些方案误命中或直接报错。加载新量化档（纯权重 int4 / pack_quantized / MX 格式）报错时对照。
tags:
- task.debugging
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/79
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/103
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/366
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:20Z'
platforms:
- agnostic
---

# compressed-tensors 量化加载器的方案识别门控陷阱：别假设总有激活量化、MX 与普通 fp8 靠 weight_block_size 区分、AWQ int4 走 W4A16

## 适用场景

在昇腾上加载 compressed-tensors 格式的量化权重时，加载器要从 config 判断「这是哪种量化方案」并路由到对应 Linear method。判据写得过窄/过宽都会让某些方案**误命中或直接报错**。加载新量化档（纯权重 int4 / pack_quantized / MX 格式）报错时对照。

## 症状 → 根因 → 修法

### A. 加载器假设「总有激活量化」→ 纯权重/pack_quantized 三处硬失败

- 信号：加载 `pack_quantized` 压缩格式或纯权重整数量化（**w4a16int4**：int4 权重、激活不量化）checkpoint，命中三处硬失败——格式白名单 `ValueError`、权重类型断言 `AssertionError`、模式串拼接 `AttributeError`。
- 根因：都源于把「激活量化」当成必然前提（解析激活量化字段、拼激活模式串）。
- 修法：让加载器允许「无激活量化」分支——`pack_quantized` 进白名单、放开权重类型断言、模式串拼接容忍激活量化缺省。

### B. MX 格式（mxfp8）与普通 per-tensor/channel fp8 互相误命中

- 信号：区分 [mxfp8](../../concepts/quantization/mxfp8_a8w8.md) 与普通 fp8 时，只看 `num_bits==8 && weight_quant.type=="float"` → 两者该条件都成立、互相误路由。
- 根因：MX 与普通 fp8 的 num_bits/type 相同，仅 block 结构不同。
- 修法：**再看 `weight_block_size` 是否等于 `[1, 32]`（`[1, MX_BLOCK_K]`）**——是 MX 才路由 `MxFp8LinearMethod`，否则路由 `Fp8LinearMethod`。

### C. AWQ 类 int4 纯权重量化没有独立 "awq" 开关

- 场景：想在昇腾跑 AWQ 类 int4 **纯权重量化**，误以为本仓只支持 W8A8/W16A16。
- 修法：用已有的 **W4A16（A16W4）compressed-tensors 路径**，以 kimi-k2-thinking 样例为参考照配——把 int4 纯权重量化表达成 compressed-tensors 格式后，框架按权重量化参数自动识别走 W4A16，无需 "awq" 开关。

## 通用先验

- compressed-tensors 的方案识别**不能只看 num_bits/type**：激活是否量化、`weight_block_size`（MX 判据）、pack 格式都要纳入门控，否则误命中或误拒。

## 风险 / 边界

- `[1,32]` 是 MX_BLOCK_K 的当前取值，随格式版本可能变；以目标 commit 的常量为准。
- 上述判据针对本仓 compressed-tensors 加载路径，不外推为所有量化框架通用。

## 相关经验
- [310P 上加载 compressed-tensors 格式 W8A8 模型在 load 阶](w8a8_310p_compressed_tensors_missing_ascend_override.md)

- 量化权重加载的命名/布局清理（offset/scale-name/NZ）见 [quant-weight-load-layout-and-naming](../../optimizations/rules/quant_weight_load_layout_and_naming.md)。
- 量化权重制备路径选择见 [quant-weight-conversion-path-selection](../../guides/deployment/quant_weight_conversion_path_selection.md)；W4A8 MoEGMM 三件套布局见 [quant-weight-load-layout-and-naming](../../optimizations/rules/quant_weight_load_layout_and_naming.md)。
- 另见 [激活 8bit 量化分支按精确 == 'W8A8' 门控会漏掉 W4A8：改 'a8' 子串判断，否则该量化模式静默不生效](activation_quant_substring_gating_w4a8.md)。

## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/79)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/103)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/merge_requests/366)（evidence）
