---
type: Optimization
title: "X51: 大 S 小 landmark 统一 cube-core 路由阈值扩展"
description: "低秩/近似注意力（Nyström landmark approximation）在 S 大而 landmark 小的区域，score GEMM（Ql@Kl^T / Q@Kl^T / Ql@K^T）退化为小 M（landmark）× 大 K（S）的窄 GEMM。将 cube-core 路由阈值从 LP>=16 放宽到 LP>=8（或 S>=128 直接走 cube-core），可把这些窄 GEMM 纳入统一 fp32 cube-core 链，同时保留 DHP 对齐与 M 尾块护栏。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.data_movement
status: draft
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X51: 大 S 小 landmark 统一 cube-core 路由阈值扩展

## 核心思路
低秩/近似注意力（Nyström landmark approximation）在 **S 大但 landmark L 小** 的区域，score GEMM
（Ql@Kl^T / Q@Kl^T / Ql@K^T）退化为**小 M（landmark）× 大 K（S）** 的窄 GEMM。若路由阈值保守
（`useCubeCore` 要求 LP>=16），这些 case 会被留在 legacy vector 路径，cube 空转。**把阈值放宽到
LP>=8（或 S>=128 时直接走 cube-core 链）**，让这些 case 进入统一 fp32 cube-core 链
（MatmulImpl + SetHF32(false) 全精度），窄 GEMM 不再落到 vector 路径。

## 适用场景
- 低秩注意力 / landmark-based attention（Nyström、Performer 类）中 S 大而 landmark 小的 case
- 任何"小 M × 大 K"窄 GEMM 被路由到 vector 而 cube 空转的场景
- 判定：score GEMM 的 M 维（landmark/head-dim 组合）低于原阈值但 cube 可用（DHP 对齐）

## 实现要点
1. **阈值放宽**：`useCubeCore` 判定从 `LP>=16` 改为 `LP>=8`（或 `S>=128` 直接进 cube-core），
   覆盖大 S 小 landmark 区域。
2. **精度保障**：fp32 走 MatmulImpl + `SetHF32(false)` 全精度单 GEMM（不要用 fp32 手动 mmad，
   见失败模式：CubeGemm\<float\> 在 PINV 链产生错误结果）。
3. **对齐护栏**：`DHP%16==0` 守卫（DHP 非 16 对齐在 cube-core 触发 vector-core 异常
   507035）；非对齐走快/慢双路径。
4. **M 尾块处理**：sub-16 M-tail 时 CubeGemm 输出 garbage → 合并尾 tile + blockM 4→5。
5. **core_round 非 32B 对齐**：DHP%8!=0 时触发 vector core exception，需快/慢双路径处理。

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
