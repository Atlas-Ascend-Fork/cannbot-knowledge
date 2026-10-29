---
type: Optimization
title: LongCat-Lite EP 报告的平台与源码待核验观测
description: 集中固定来源的历史数据，保留平台、配置、指标与证据缺口，不作为通用性能承诺。
tags:
- task.testing
- topic.performance.analysis
status: draft
sources:
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_ep.md
  role: primary
- resource: https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py
created_at: '2026-10-21T09:56:24Z'
updated_at: '2026-10-22T03:20:00Z'
platforms: []
---

# LongCat-Lite EP 报告的平台与源码待核验观测

## Workload

EP8、attn_tp4/attn_dp2；只保留原总览引用的Prolog和SP观测，不与纯TP数据合并。

## Hardware

报告总览标A2/A3，未把下列每组数字绑定到确定硬件；保持draft和未知平台。

## Software

来源固定到下列提交；没有与每行数据绑定的完整软件build和原始运行记录，安装章节示例不自动等于测量环境。

## Baseline 与 Variant

仅在同一来源明确对照的行内比较。不同平台、阶段、batch、框架、量化、并行与版本不拼接为一次受控试验，也不把累计优化归因给单个开关。

## Metric Definition

字段和单位沿用源表。时延起止、首token/warmup处理、吞吐分母和精度指标未完整披露时保持未知，不由字段名称自行补计算公式。

## Repetition and Variance

没有足够的逐轮原始样本、重复次数、方差或置信区间。本仓未独立复测，不新增 verified。

## Result

| 报告小节 | 比较 | 数值 |
| --- | --- | --- |
| Prolog | 无→有 | Decode 8.36→8.10ms，Prefill239→239ms |
| Prefill SP，ep8 b8 | 无→有 | 199.91→145.22ms，源称约−27% |

Prolog报告约4–5个decode token起出现选词分歧。SP/RS+AG的报告描述在固定2c45117建模中未见is_sp/reduce_scatter落地，不能把这行视为当前实现的复现结果。


## Limitations 与验证

补齐逐组硬件、代码路径、原始输入/输出与计时记录前不进入默认检索；不新增Scope，也不把总体支持平台当作某行测量平台。

复现与回退入口：[模型部署与验收流程](../../guides/models/longcat_flash_lite_deployment.md)。性能与输出质量分别验收；来源自报不构成本仓复现。


## Evidence

- [固定来源 1](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/agentic/optimization_report_ep.md)
- [固定来源 2](https://gitcode.com/cann/cann-recipes-infer/blob/2c45117d781ab9ab88dcb89a28ae30f5d2450399/models/longcat_flash_lite/models/modeling_longcat_flash_lite.py)

## 本轮来源核对与剩余缺口

已重新核对固定报告和同提交建模代码。报告表头只写“Atlas A2/A3、8卡”，不能区分 Prolog/SP 测点。报告本身还说明 A2 在 EP8 的 32 experts/rank 下需改用双路由，不能据此倒推出所有结果都运行于 A3。

同提交 `modeling_longcat_flash_lite.py` 中仍未找到报告描述的 `is_sp` / ReduceScatter 实现；SP 数据尚未闭合代码版本。Prolog 的选词分歧也不能仅凭“语义一致”视为质量验收。平台、匹配代码和原始输出/计时仍缺失，保留 draft。
