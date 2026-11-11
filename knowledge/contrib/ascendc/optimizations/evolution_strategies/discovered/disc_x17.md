---
type: Optimization
title: "X17: FP32-via-BF16 Hi/Lo 拆分 3-GEMM（Cube 不吃 fp32 时的保精度路径）"
description: "910B Cube 的 Mmad 不直接消费 fp32 输入；将 fp32 操作数拆为 bf16 双分量 hi/lo，用 hi·hi + hi·lo + lo·hi 三个 bf16 GEMM（fp32 累加）逼近 fp32 GEMM，并以单趟 split-xtrans 直接产出 hi/lo 目标布局。"
tags:
  - task.optimization
  - topic.programming_model.execution_unit.cube
  - topic.compute.neighborhood.convolution
status: deprecated
replaced_by: contrib/ascendc/optimizations/evolution_strategies/cards/p128_fp32_via_bf16_hilo_3gemm
sources:
  - resource: https://gitcode.com/cann/cannbot-knowledge/merge_requests/103
    role: primary
created_at: "2026-10-13T00:00:00Z"
updated_at: "2026-11-03T16:45:00Z"
platforms:
  - a2
---

# Strategy X17: FP32-via-BF16 Hi/Lo 拆分 3-GEMM（Cube 不吃 fp32 时的保精度路径）

> **已晋升为 P128**：策略卡见 [../cards/p128_fp32_via_bf16_hilo_3gemm.md](../cards/p128_fp32_via_bf16_hilo_3gemm.md)，Playbook 见 [../../../runbooks/performance/p128_fp32_via_bf16_hilo_3gemm.md](../../../runbooks/performance/p128_fp32_via_bf16_hilo_3gemm.md)，precondition YAML 见 cannbot-skills 仓 `community/ops/ascendc-evolution-strategies/references/preconditions/`。本文件保留该策略的详细机制说明，卡片内容以 P128 为准。

## 核心思路
910B Cube 的 Mmad 不直接消费 fp32 输入。将 fp32 操作数拆分为 bf16 双分量
`x ≈ hi + lo`（hi = cast_bf16(x)，lo = cast_bf16(x − hi)），用 3 个 bf16 GEMM
`hi·hi + hi·lo + lo·hi`（fp32 累加）逼近 fp32 GEMM，获得 Cube 级吞吐 + 接近
fp32 的精度（~1e-4 相对误差，远小于 torch fp32 conv 自身的 ~1e-3）。

关键配套：**单趟 split-xtrans**——一个 AIV kernel 从 fp32 源直接产出 hi/lo 双份
目标布局（如 bf16 xT），省掉独立的 split kernel 和第二趟 im2col/转置物化。

## 适用场景
- **算子类型**: fp32 输入的 GEMM 类计算（conv、matmul），Cube 仅支持 fp16/bf16
- **瓶颈类型**: compute-domain，fp32 被困在 Vector/标量路径
- **前提条件**: 容差允许 ~1e-4 相对误差；
  **±inf/NaN 特殊值必须验证**——hi=±inf 时 lo=NaN，感受野含 inf 则累加 NaN，
  与 golden 的 NaN 图样天然逐位匹配（无需显式 NaN 掩码逻辑）

## 实现要点
1. 拆分：`hi = Cast_bf16(x, CAST_RINT)`，`lo = Cast_bf16(x − hi, CAST_RINT)`，
   两级 Cast + Sub，无 NaN fixup（fixup 反而破坏 inf 语义）
2. **2-GEMM（舍 lo·hi 项）经精度分析否决**：~2e-3 相对误差贴容差边缘且存在
   误差抵消风险；3-GEMM 是精度安全下限
3. GEMM 组织：hi/lo 双 L1 面板 + hi/lo 双 ws，每 k tile 2 次展开 + 3 Mmad；
   **A2/B2 队列深度按每 chunk 的 tile 数定**：双 tile（hi+lo）需 depth-4
   （4×16KB=64KB L0 占满）让展开与 Mmad 重叠；单 tile 用 depth-2 即可
   （depth-4 在单面板几何上挂死设备）
4. 4 加载变体（Ahi/Alo/Bhi/Blo 各载一次省流量）不采用——失去跨面板
   预取的损失 > 省部分加载流量的收益；保留 6 虚拟面板 + 预取为默认

## 验证方法
- 在目标算子上做同设备同窗口 A/B（正反序至少两轮），比较父变体与变体；用全量精度门禁与逐 bit/逐元素对比确认语义未变。
- 容量类改动先做 UB/L1/L0C 预算审计；诊断类改动先做同码 A/A 噪声带。
- ±inf 特殊值 case 不能用于验证 kExtension 类展开改动（"双 NaN 巧合"会掩盖错误），必须使用有限实数输入。
