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
updated_at: '2026-08-25T06:41:27Z'
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

- 量化权重加载的命名/布局清理（offset/scale-name/NZ）见 [quant-weight-load-layout-and-naming](../../optimizations/experience/rules/quant_weight_load_layout_and_naming.md)。
- 量化权重制备路径选择见 [quant-weight-conversion-path-selection](../../guides/experience/interventions/quant_weight_conversion_path_selection.md)；W4A8 MoEGMM 三件套布局见 [quant-weight-load-layout-and-naming](../../optimizations/experience/rules/quant_weight_load_layout_and_naming.md)。
- 另见 [激活 8bit 量化分支按精确 == 'W8A8' 门控会漏掉 W4A8：改 'a8' 子串判断，否则该量化模式静默不生效](activation_quant_substring_gating_w4a8.md)。

## Evidence

- `diff 事实`（@ece4dde）：加载器三处硬失败源于假设有激活量化，修为容许纯权重/pack_quantized。
- `diff 事实`（@524914b）：MX vs fp8 靠 `weight_block_size==[1,32]` 区分路由。
- `维护者确认`（@2c45117）：AWQ int4 纯权重走 W4A16 compressed-tensors、参考 kimi-k2-thinking。
- 溯源下探：[cann-recipes-infer-issue-79-question-w8a8-w16a16](https://gitcode.com/cann/cann-recipes-infer/issues/79)、[cann-recipes-infer-pr-103-fix-quantization-support-w4a16int8-and-pack-quantized](https://gitcode.com/cann/cann-recipes-infer/merge_requests/103)、[cann-recipes-infer-pr-366-support-deepseek-v4](https://gitcode.com/cann/cann-recipes-infer/merge_requests/366)

<!-- cannbot:related:start -->
## 相关

- [310P 上加载 compressed-tensors 格式 W8A8 模型在 load 阶段崩溃：该平台缺 Ascend override 注册，落回 vLLM 原生 int8 kernel 查表失败——须改 ModelSlim 格式 + --quantization ascend](w8a8_310p_compressed_tensors_missing_ascend_override.md)（`related`）：真正的缺口是 **310P 平台分支尚未补齐 `compressed-tensors` 的 Ascend override 注册**，属平台/后端能力覆盖不完整，不是格式缺陷、也不是权重错误。；compressed-tensors 的方案识别**不能只看 num_bits/type**：激活是否量化、`weight_block_size`（MX 判据）、pack 格式都要纳入门控，否则误命中或误拒。。两卡覆盖 compressed-tensors 加载路由的连续两层门控：先有平台 override 接管，再按激活、block 与 pack 信息识别具体量化方案。
- [昇腾量化权重制备路径选择：仓内离线系数 convert_model.py vs 权重自带 compressed-tensors 运行时量化 vs amct](../../guides/experience/interventions/quant_weight_conversion_path_selection.md)（`related`）：焦点卡用“**无仓内离线系数的模型**（如 Kimi-K2-Thinking）：直接加载原始权重，量化在加载时由**权重自带的 compressed-tensors `quant_config`** 驱动（运行时 w8a8int8），部署走 BF16 config、不跑离线转换。”确定运行时制备路线；目标卡用“在昇腾上加载 compressed-tensors 格式的量化权重时，加载器要从 config 判断「这是哪种量化方案」并路由到对应 Linear method。”给出进入该路线后的方案识别门禁。
- [激活 8bit 量化分支按精确 == 'W8A8' 门控会漏掉 W4A8：改 'a8' 子串判断，否则该量化模式静默不生效](activation_quant_substring_gating_w4a8.md)（`related`）：激活是否量化、`weight_block_size`（MX 判据）、pack 格式都要纳入门控；那是加载器路由 LinearMethod 的门控，本页是 modeling 侧激活量化分支门控；连接加载器与 modeling 两层门控排障。
- [量化权重格式 / dtype 组合的可用性受 SoC 平台与 CANN 算子包版本双重约束（非量化配置 bug）](quant_format_dtype_platform_cann_version_gating.md)（`related`）：纯权重 int4 / pack_quantized / MX 格式；受两道**相互独立**的门控；连接方案判定与 SoC/CANN 支持面排除。
<!-- cannbot:related:end -->
