---
type: API
title: Gelu接口
description: 提供Gelu激活函数接口及变体，包含Gelu、FasterGelu、FasterGeluV2及GetGeluMaxMinTmpSize等Tiling查询接口。
tags: [task.lookup, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/Gelu_interface/Gelu_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Gelu接口

提供 Gaussian Error Linear Unit 激活函数的 Kernel 侧计算接口及变体。
包含 Gelu、FasterGelu、FasterGeluV2 三种实现，以及 GetGeluMaxMinTmpSize 用于查询 Tiling 临时空间上下界。
FasterGelu 系列通过近似算法降低计算开销，适用于对精度要求可放松的场景。

<!-- cannbot:related:start -->
## 相关

- [AscendC GELU 三系数 erfc 在大值域 fp32 精度不足](../../../../../runbooks/precision/gelu_erfc_polynomial_precision_budget.md)（`exemplifies`）：Gelu 总览给出精确与近似实现的选型边界；该实测卡说明 exact GELU 若为省指令把 erfc 多项式从五系数降到三系数，会在大值域 fp32 超出 MARE，直接补足精度预算依据。
- [GELU 负尾部用 erfc 形态避免大数相消](../../../../../runbooks/precision/gelu_negative_tail_erfc_avoids_cancellation.md)（`exemplifies`）：Gelu 的 exact 语义在负大值尾部接近零；该卡证明直接用 erfc 小尾部形态可避免两个大项相消，为精度敏感场景选择或复现 Gelu 提供公式级验证。
- [FasterGeluV2](faster_gelu_v2.md)（`same_topic`）：总页给出精确 Gelu、FasterGelu 和 V2 的选型及 workspace 流程。
- [Gelu](gelu.md)（`same_topic`）：Gelu 与《Gelu接口》的实质衔接是：Gelu 接口、快速近似变体和空间查询共同定义高精度/高性能调用；GeGLU 直接以 GELU 为门控，两个 runbook 给出 erfc 近似与负尾相消的可执行精度边界。
- [GetGeluMaxMinTmpSize](get_gelu_max_min_tmp_size.md)（`same_topic`）：GELU 总页定义计算与 workspace 查询流程。
<!-- cannbot:related:end -->
