---
type: Optimization
title: A3 LI TopK 融合与 HcPost 的来源观测
description: 分开记录固定 A3 指南的 LI TopK 融合相对收益和 HcPost shape 时延，不将两组测量拼接或外推。
tags:
- task.testing
- topic.performance.analysis
status: stable
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_ascendc_operator_guide.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_mHC_guide.md
created_at: '2026-10-22T03:12:28Z'
updated_at: '2026-10-22T03:12:28Z'
platforms:
- a3
---

# A3 LI TopK 融合与 HcPost 的来源观测

## Workload

LI 的 TopK 外置/融合比较与 HcPost 的 shape 扫描是两组独立记录。HcPost 固定 hc=4、d=4096，逐行按 b*s 读取；LI 未披露完整输入形状，不借用 HcPost 或 PyPTO 参数。

## Hardware

LI 主来源明确全文阐述两个融合算子在 A3 上的优化；HcPost 的时延表直接位于“A3 实现设计”小节。平台只声明 A3，不从编译器兼容性推导 A2 或 950。

## Software

LI 固定 2f82d10467e6fe8dae81c97a2cdac78d733a6703，HcPost 固定 2c45117d781ab9ab88dcb89a28ae30f5d2450399。各测点 CANN、torch_npu 与编译 build 未完整披露，不把两份指南认作同一环境。

## Baseline 与 Variant

LI 比较 TopK 外置与融合；HcPost 只列 shape 对应的绝对时延，没有未优化对照。

## Metric Definition

LI 的约 20% 沿用来源“收益”口径，不能自行改写为时延降低 20%；HcPost 单位为微秒，不是整网时延。

## Repetition and Variance

未披露完整 warmup、重复次数、逐轮样本与方差。本仓未执行硬件复测，记录为来源自报，不新增 verified。

## Result

### LI AscendC 的定性量级

固定 AscendC 指南报告 TopK 融入 LI 相对外置收益约 20%，未给完整基线命令或逐轮数据。


### HcPost AscendC shape 扫描


| b*s（hc=4，d=4096） | Duration(us) |
| --- | --- |
| 8 | 5.09 |
| 16 | 5.37 |
| 32 | 6.99 |
| 64 | 9.16 |
| 128 | 13.85 |
| 4K | 319.86 |
| 16K | 1264.68 |
| 64K | 5044.53 |


## Limitations 与验证

来源、平台和单组含义已定位，未独立复现性能。复核时逐组保存输入、依赖、计时边界、精度和多轮波动，不能把本卡当作通用加速保证。PyPTO 的 LI/DIA 披露仍在[待核验观测](operator_tuning_source_observations.md)，不混入本卡条件。

## Evidence

- [固定来源](https://gitcode.com/cann/cann-recipes-infer/blob/2f82d10467e6fe8dae81c97a2cdac78d733a6703/docs/models/deepseek-v3.2-exp/deepseek_v3.2_exp_ascendc_operator_guide.md)
- [固定来源](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/docs/models/deepseek-v4/deepseek_v4_mHC_guide.md)
