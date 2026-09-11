---
type: Guide
title: 昇腾量化权重制备路径选择：仓内离线系数 convert_model.py vs 权重自带 compressed-tensors 运行时量化 vs amct
description: 昇腾量化权重制备路径选择：仓内离线系数 convert_model.py vs 权重自带 compressed-tensors 运行时量化 vs amct。要在昇腾上部署某模型的 W8A8C8 / W4A8C8 等量化档，先判「量化权重从哪来、怎么产」——选错路径会去找并不存在的命令/config。
tags:
- task.debugging
- topic.precision
- topic.model_serving
- topic.compilation
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/105
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/114
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/issues/50
  role: evidence
- resource: https://gitcode.com/cann/cann-recipes-infer/merge_requests/179
  role: evidence
created_at: '2026-07-06T00:00:00Z'
updated_at: '2026-08-25T06:41:27Z'
platforms:
- agnostic
---

# 昇腾量化权重制备路径选择：仓内离线系数 convert_model.py vs 权重自带 compressed-tensors 运行时量化 vs amct

## 适用场景

要在昇腾上部署某模型的 [W8A8C8](../../../concepts/quantization/w8a8c8.md) / [W4A8C8](../../../concepts/quantization/w4a8c8.md) 等量化档，先判「量化权重从哪来、怎么产」——选错路径会去找并不存在的命令/config。

## 问题信号

- 想量化却不知该跑哪条命令：误以为要套 `msit`/`msmodelslim` 的 `quant --quant_type w8a8c8` 这类通用命令；
- 找不到「按量化模式命名」的运行 config，或去找某个 `kv-cache-dtype` 开关但没有；
- 复制兄弟模型的 `weight_convert.sh` 直接用，结果下载到的是**源模型**的量化系数。

## 做什么（按模型分两条路径）

模型样例按「**是否有仓维护的离线量化系数包**」分两条量化路径：

1. **有仓内离线系数的模型**（如 DeepSeek-V3.2-Exp）：走离线转换——`convert_model.py` + `weight_convert.sh`，脚本按量化模式分支下载该模型的量化系数包并应用；产出一份量化后权重目录。制作 W8A8C8/W4A8C8 走这条，或走 `amct`（`gitcode.com/cann/amct`）的 deploy 量化。**不要**默认套 msit/msmodelslim 命令（维护者对该问法未确认，明确改指向前两条路径）。
2. **无仓内离线系数的模型**（如 Kimi-K2-Thinking）：直接加载原始权重，量化在加载时由**权重自带的 compressed-tensors `quant_config`** 驱动（运行时 w8a8int8），部署走 BF16 config、不跑离线转换。

## 前置条件

- **跑 `weight_convert.sh` 前必须 `source` CANN 环境变量**：torch（≥2.5.1）会自动 `import torch_npu`，未 `source ${cann_path}/bin/setenv.bash` 会在转换脚本启动即报错。
- 量化系数包与特定权重快照绑定（见 [c8-kv-scale-provenance-reuse-offline](c8_kv_scale_provenance_reuse_offline.md)）；权重变了要用 amct 重标定。

## 运行期怎么选量化档（config 侧）

**量化 / KV-cache 精度由 `model_path` 指向的「转换后权重目录」决定，运行 yaml 不含任何量化或 KV-cache 精度旋钮。** 因此某量化模式若没有随仓自带的 yaml（如 W8A8C16），应**复用同量化家族（如 W8A8C8）的 yaml、只改 `model_path`**，而不是去找一个缺失的「按量化模式命名的 config」或某个 kv-cache-dtype 开关。

## 风险 / 边界

- **切勿保留/复用从兄弟模型拷来的 `weight_convert.sh`**：其量化分支硬编码下载的是**源模型**的系数包 URL，直接用会把错误系数套到当前模型。
- 上面「有/无仓内系数」的二分适用面按证据限定到本仓当前几个 DeepSeek / Kimi 模型，不外推为所有昇腾量化都如此。

## 相关经验
- [昇腾量化权重的加载期布局/命名处理：W4A8 MoEGMM 三件套、剔除零 offset、s](../../../optimizations/experience/rules/quant_weight_load_layout_and_naming.md)

- C8/MLA KV int8 scale 的来源、离线预取与复用见 [c8-kv-scale-provenance-reuse-offline](c8_kv_scale_provenance_reuse_offline.md)；C8 的 mla_prolog 前置见 [c8-kvcache-requires-mla-prolog](../../../runbooks/runtime/c8_kvcache_requires_mla_prolog.md)。
- compressed-tensors 加载器的方案识别门控坑见 [compressed-tensors-scheme-gating-pitfalls](../../../runbooks/precision/compressed_tensors_scheme_gating_pitfalls.md)。

## Evidence

- `维护者确认`（@db40505）：量化走 amct 或仓内系数 + `convert_model.py`，不套 msit/msmodelslim（issue 维护者答复）。
- `diff 事实`（@2c45117）：Kimi-K2-Thinking 无仓内 `weight_convert.sh`、量化由权重 compressed-tensors 驱动、部署 BF16 config；DeepSeek-V3.2-Exp 走离线系数包；`weight_convert.sh` 量化分支硬编码源模型系数 URL。
- `diff 事实`（@2c45117）：运行 yaml 无量化/KV-cache 精度字段，量化由 `model_path` 决定。
- `diff 事实`（@deb9293）：`weight_convert.sh` 需先 `source setenv.bash`，否则 torch auto-import torch_npu 报错。
- 溯源下探：[cann-recipes-infer-issue-105-question-dsv3-2-w8a8c8-w4a8c8](https://gitcode.com/cann/cann-recipes-infer/issues/105)、[cann-recipes-infer-pr-114-add-benchmark-in-yaml-name-of-dsv3-2-exp-and-k2-thinking-remove-useless](https://gitcode.com/cann/cann-recipes-infer/merge_requests/114)、[cann-recipes-infer-issue-50-deepseek-v3-2-yaml](https://gitcode.com/cann/cann-recipes-infer/issues/50)、[cann-recipes-infer-pr-179-fix-c8-mlaprolog-kr-cache-tensor](https://gitcode.com/cann/cann-recipes-infer/merge_requests/179)