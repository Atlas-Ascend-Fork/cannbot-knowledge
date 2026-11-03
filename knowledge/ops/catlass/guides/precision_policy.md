---
type: Guide
title: 精度策略
description: CATLASS C++ 标杆生成、定向精度验证和全量验收共用的精度判定规则。
tags:
- task.design
- topic.implementation.pipeline
status: stable
sources:
- resource: https://gitcode.com/johan_lee/cannbot-skills_1023/blob/e45d70d8b1aa1a111086ba146791298258803520/plugins-official/catlass-op-generator/catlass-cpp-generator/knowledge/workflow/precision-policy.md
  role: primary
- resource: https://gitcode.com/cann/cannbot-skills/blob/4950cbd7c45e0d44cb8ec52598edf53cdc7f16ca/ops/catlass-linear-attention-workflow/references/precision-policy.md
  role: supporting
created_at: '2026-09-18T00:00:00Z'
updated_at: '2026-10-26T17:43:12Z'
platforms:
- a2
- a3
- '950'
verified:
- by: process:content-equivalence-check
  at: '2026-09-18T00:00:00Z'
---

# 精度策略

本规则由 02 标杆生成、04 定向精度验证和 05 全量验收共同使用。具体阈值只从当前工程冻结的
`reference/precision-policy.json` 读取，不在本文重复维护。

## 判定规则

1. 核对全部输出的名称、shape 和 actual 原始 dtype。
2. 检查有效区域内 actual 和 golden 均为有限值。
3. 按以下公式逐元素比较：

   ```text
   abs(actual - golden) <= atol + rtol * abs(golden)
   ```

4. 全局和各必需分区的 `matched_ratio` 必须达到工程精度策略中的对应阈值。
5. 全局和各必需分区的 `max_abs` 必须不超过对应 dtype 的 `max_abs_limit`。
6. 所有输出和分区均满足要求才判定通过。

## 指标职责

`matched_ratio` 和 `max_abs` 是默认数值门禁。`MERE`、`MARE`、`max_ulp` 和 `error_count`
用于定位误差；只有策略显式启用 `strict_ulp` 时，`max_ulp` 才成为门禁。

## 比较输入

| 输入 | 内容 |
|---|---|
| `expected_outputs` | 每个输出的 shape、dtype 和 `required_regions` |
| `actual` / `golden` | 实际输出和标杆输出 |
| `valid_masks` | 参与比较的有效区域 |
| `regions` | tail、boundary、critical 等具名分区 |

actual 必须保留设备输出的原始 dtype；数值计算使用足以保留标杆精度的类型。
没有必需分区时，`required_regions` 必须显式填写空列表。

## Stage 与整算子检查

Stage 中间结果和整算子输出使用同一比较规则。tail、boundary 和 critical 分区使用工程策略配置的
重点分区阈值。缺少输出约定、有效区域或必需分区时返回 `CONFIG_ERROR`；输出名称、shape、dtype
或数值不符合要求时返回 `FAIL`；全部输出及分区通过时返回 `PASS`。

报告记录用例、输出、分区、阈值、`matched_ratio`、`max_abs` 和诊断指标。
