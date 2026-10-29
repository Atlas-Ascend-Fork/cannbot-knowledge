---
type: Optimization
title: AutoFuse A3 部分编译与 hc_post 的来源观测
description: AutoFuse A3 部分编译与 hc_post 的来源观测；按固定来源保留条件、差异和待验证边界，不提供通用性能保证。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_autofuse_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4-flash-tilelang-and-inductorAF/README.md
created_at: '2026-10-22T01:37:00Z'
updated_at: '2026-10-22T01:55:16Z'
platforms:
- a3
---

# AutoFuse A3 部分编译与 hc_post 的来源观测

## Workload

DeepSeek-V4-Flash 部分编译的两类 step；hc_post 独立片段的 shape 与模型级记录分开。

## Hardware

Atlas A3。

## Software

固定来源版本见 Evidence；未与各行数据绑定的软件 build 不自行补齐。

## Baseline 与 Variant

模型级 baseline 已替换 TileLang 算子，统计 Device 非 Hcom Kernel 总和；片段比较未编译、dynamic=False 和 dynamic=True。

## Metric Definition

沿用源表单位；算子、非 Hcom Kernel 总和与端到端耗时分别报告，不混用。

## Repetition and Variance

来源未给足够逐轮样本、warmup、重复次数、方差或置信区间；没有本仓独立复测。

## Result

环境：昇腾 Atlas A3；torch_npu PTA 2.8 + CANN nightly。baseline = **已替换 TileLang-ascend 算子、但未启用 inductor 编译**的模型（非纯原始模型）；统计口径只算 Device 上**非 Hcom 类算子**的 Kernel 耗时总和（Hcom Kernel 显著受 host 调度影响故剔除）；未使能 aclgraph 下沉调度（模型含未消除动态结构）。

| 模型级（非 Hcom Kernel 总耗时） | 未编译 | 编译后 | 提升 |
|---|---|---|---|
| Step 2（无 Compressor） | 49.8 ms | 39.5 ms | 20.6% |
| Step 4（触发 Compressor） | 52.8 ms | 42.0 ms | 20.4% |

- **不外推单调规律**：模型级仅 2 个受控测点、片段级 1 个——只陈述在报告的这几组配置下的观测值，不外推"越大越…"。
- 收益量级对可比性依赖 baseline 口径（已上 TileLang 算子、非 Hcom、未开 aclgraph）——迁移评估时对齐 baseline。

### hc_post 输入与来源说明

DeepSeek-V4 的 `hc_post` 片段含多个小算子组合，适合 AutoFuse 融合。对 `hc_post` 加 `@torch.compile` 后的实测（昇腾 A3、基于 `hc_post` 典型输入 shape：`x=(1,1,4096)` bf16 / `residual=(1,1,4,4096)` bf16 / `post=(1,1,4)` fp32 / `comb=(1,1,4,4)` fp32，README §基准脚本）：

| 模型部分 | 未编译耗时 | 编译后（dynamic=False） | 提升 | 编译后（dynamic=True） | 提升 |
| --- | --- | --- | --- | --- | --- |
| hc_post | 30 us | 7.5 us | 4x | 10 us | 3x |

> 该数据前提为昇腾 A3 平台、`hc_post` 单算子上述典型输入 shape；端到端多片段收益待验证。cann-recipes-infer 的 `hc_post` 已有 AscendC 手写融合算子实现（见 [mhc-hcpre-hcpost](../../concepts/kernels/mhc_hcpre_hcpost.md)）；此处 AutoFuse 是**自动融合**路径，与手写 AscendC 算子为并列两种实现来路。

## Limitations 与验证

两类计时范围不能混为整网端到端加速。保存实际输入、后端、编译耗时与多轮样本，复核输出和目标指标。

本卡记录来源自报，不是普遍性能保证，不新增 verified。

## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_autofuse_guide.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/deepseek-v4-flash-tilelang-and-inductorAF/README.md)
