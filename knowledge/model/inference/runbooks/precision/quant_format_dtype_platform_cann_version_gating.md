---
type: Runbook
title: 量化权重格式 / dtype 组合的可用性受 SoC 平台与 CANN 算子包版本双重约束（非量化配置 bug）
description: 量化权重格式 / dtype 组合的可用性受 SoC 平台与 CANN 算子包版本双重约束（非量化配置 bug）。用某量化格式的权重在昇腾上直接部署，在 warmup 加载权重或图编译期报「格式 / dtype 不受支持」的算子级错误。此时先别怀疑自己的量化系数、yaml 或建模代码：一个量化权重格式 / dtype 组合并非到处可用，它受两道相互独立的门控——(a) 运行的 SoC 平台，(b) 已装的 CANN 二进制算子包版本。对号入座后，动作是「换到该平台支持的量化类型」或「升 CANN 算子包到 recipe 钉定版本」，而不是改量化配置。
tags:
- task.debugging
- topic.graph_execution
- topic.precision
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/190
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/68
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-10-29T15:29:20Z'
platforms:
- a3
---

# 量化权重格式 / dtype 组合的可用性受 SoC 平台与 CANN 算子包版本双重约束（非量化配置 bug）

## 适用场景

用某量化格式的权重在昇腾上直接部署，在 warmup 加载权重或图编译期报「格式 / dtype 不受支持」的**算子级**错误。此时**先别怀疑自己的量化系数、yaml 或建模代码**：一个量化权重格式 / dtype 组合并非到处可用，它受两道**相互独立**的门控——(a) 运行的 **SoC 平台**，(b) 已装的 **CANN 二进制算子包版本**。对号入座后，动作是「换到该平台支持的量化类型」或「升 CANN 算子包到 recipe 钉定版本」，而不是改量化配置。

## 信号（现象）

- **SoC 门控**：加载 MoE 专家权重做 NZ 布局转换时报
  ```
  w13_weight = torch_npu.npu_format_cast(...)
  RuntimeError: customize_dtype is not supported by the current soc version.
  [ERROR] ... ERR00007 PTA feature not supported
  ```
- **CANN 算子包版本门控**：[图模式](../../concepts/techniques/npu_graph_mode.md)编译在 `GroupedMatmul` 节点 infershape 阶段失败
  ```
  case with x dtype 27 and weight dtype 2 is not supported!
      [FUNC:CheckFunctionParamsForDtype][FILE:groupedmatmul_infershape.cpp]
  CheckFunctionParamsForDtype failed! ... Compile graph failed
  ```

## 触发条件 + 根因

- **平台不支持某量化格式**：[DeepSeek-V4-Flash](../../concepts/models/deepseek_v4.md) 的原生 Hybrid FP8-MXFP4 权重在 [Atlas A3](../../concepts/platforms/atlas_a3.md) 上直接推理。MXFP4 加载走 `npu_format_cast(..., customize_dtype=torch.float8_e4m3fn, input_dtype=torch_npu.float4_e2m1fn_x2)` 的 [NZ 布局转换](../../concepts/techniques/weight_nz.md)，这条 `customize_dtype` 路径在 A3 的 soc 版本上不被 PTA 支持 → ERR00007。平台×量化的对应是硬边界：Hybrid (FP8-)MXFP4 / [MXFP8-MXFP4](../../concepts/quantization/hybrid_mxfp8_mxfp4.md) 是 [950PR/DT](../../concepts/platforms/ascend_950.md) 专用，A3 走 INT 系量化。
- **CANN 算子包版本缺该 dtype 组合**：[DeepSeek-R1](../../concepts/models/deepseek_r1.md) 的 [W8A8](../../concepts/quantization/w8a8c8.md) 量化 MoE 在图模式下，`GroupedMatmul` 对量化 dtype 组合（bf16 激活 × int8 权重）的支持**由 CANN 二进制算子包（cann-kernels）提供、不在 recipe 代码里**。预发布算子包（alpha003）缺该组合的 infershape 支持，正式版 CANN 才补齐——报错不是 recipe / yaml / 量化系数问题，而是算子包版本缺口。

## 修法

- **平台不支持该格式 → 转量化类型**：用 `utils/convert_model.py` 把权重转成该平台支持的量化类型再部署，按 README 部署表选对应 `--quant_type`：
  - A3：DeepSeek-V4-Flash → INT8 W8A8（`--quant_type w8a8-int`）；DeepSeek-V4-Pro → Hybrid INT8-INT4（`--quant_type w4a8-int`）。
  - 950PR/DT：DeepSeek-V4-Flash/Pro → Hybrid MXFP8-MXFP4（`--quant_type w4a8-mx`）。
- **CANN 算子包版本缺口 → 升版本**：把 CANN 二进制算子包与配套 torch_npu 升到 recipe README 钉定版本（本例 CANN `8.3.RC1.alpha003` → `8.3.RC1` 正式版、torch_npu 配套版本随之升），修复是**纯版本 bump、无 recipe / 量化代码改动**。
- **通用动作**：遇到「量化格式 / dtype 不受支持」的算子级报错（`customize_dtype ... not supported by soc` / `case with x dtype ... weight dtype ... is not supported` / `CheckFunctionParamsForDtype failed`），先核对 (a) 目标 SoC 是否在该量化格式的支持平台内、(b) CANN 算子包与 torch_npu 是否达 README 钉定版本，而不是先去查量化配置或建模代码。

## 适用边界

范围限证据覆盖的量化路径——A3/950PR-DT 的 Hybrid MXFP × INT 平台对应、图模式下走 `GroupedMatmul` 的 W8A8 量化 MoE；不外推为「所有量化格式在所有平台/版本都这样」的通用律。升级/转换后的收益均仓自报、无独立复测。GroupedMatmul 报错里 `dtype 27 = DT_BF16` / `dtype 2 = DT_INT8` 为外部 GE 枚举知识、源未明写，属推断。融合算子按 SoC / shape 条件门控回退的更一般情形见 [fused-op-hardware-conditional-fallback](../../optimizations/rules/fused_op_hardware_conditional_fallback.md)。

## 相关经验
- [310P 上加载 compressed-tensors 格式 W8A8 模型在 load 阶](w8a8_310p_compressed_tensors_missing_ascend_override.md)

- 另见 [torch 无对应 dtype 的硬件低精度格式（如 HiFloat8 KV 量化）：在 aclnn 算子调用边界覆写 acl dtype](../../optimizations/cases/torchless_lowprec_dtype_acl_override.md)。


## Evidence

- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/190)（evidence）
- [远程来源](https://gitcode.com/cann/cann-recipes-infer/issues/68)（evidence）
