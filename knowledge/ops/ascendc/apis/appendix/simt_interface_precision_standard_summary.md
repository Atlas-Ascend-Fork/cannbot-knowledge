---
type: API
title: SIMT接口精度标准汇总
description: 本节按照数据类型和接口类型对SIMT浮点计算接口进行精度标准的分类汇总。对于非软仿接口，给出对应硬件指令的精度标准；对于软仿接口，由于软仿程度较低且使用到的硬件指令较少，给出其所用硬件指令的综合性精度标准。
tags: [task.lookup, topic.implementation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/appendix/SIMT_interface_precision_standard_summary.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: [agnostic]
---

# SIMT接口精度标准汇总

本节按照数据类型和接口类型对SIMT浮点计算接口进行精度标准的分类汇总。对于非软仿接口，给出对应硬件指令的精度标准；对于软仿接口，由于软仿程度较低且使用到的硬件指令较少，给出其所用硬件指令的综合性精度标准。

涵盖以下类别：bf16数据类型计算API精度标准、数学库函数、算术函数、fp16数据类型计算API精度标准、数学库函数、算术函数、fp32数据类型计算API精度标准。

<!-- cannbot:related:start -->
## 相关

- [稀疏反卷积精度误差源隔离配方](../../runbooks/precision/cube_simt_fp32_precision_error_source_isolation.md)（`exemplifies`）：配方的 SIMT 分支必须按接口定义的误差标准判断偏差；该汇总提供 SIMT 数学接口的精度基线，避免把合法近似误判为故障。
- [核函数运行验证时算子存在精度问题](../../guides/programming_guide/appendix/faq/kernel_precision_issue.md)（`explains`）：FAQ 给出误差定位、容差与指令替换流程，可将汇总表中的标准用于 kernel 验证。
- [Reg矢量计算接口精度标准汇总](reg_vector_compute_interface_precision_standard_summary.md)（`related`）：SIMT 与 Reg Vector 精度汇总分别给出函数/指令误差标准；混合 kernel 可据此把误差归到 SIMT 或 Reg 段。
- [SIMT接口软仿情况汇总](simt_interface_soft_simulation_summary.md)（`related`）：软仿汇总标明哪些 SIMT 接口不是硬件原生实现，这是解释精度标准和平台差异的必要条件。
- [half类型精度转换函数](../simt_api/math_functions/half_type/half_precision_conversion_functions/half_precision_conversion_functions.md)（`related`）：《half类型精度转换函数》说明提供half类型与float、bfloat16、整型等数据类型间的精度转换接口。；《SIMT接口精度标准汇总》说明本节按照数据类型和接口类型对SIMT浮点计算接口进行精度标准的分类汇总。对于非软仿接口，给出对应硬件指令的精度标准；对于软仿接口，由于软仿程度较低且使用到的硬件指令较少，给出其所用硬件指令的综合性精度标准。。二者在half精度转换总览与通用SIMT转换、bfloat16总览、精度标准和精度FAQ共同提供选择与验收边界上存在可执行的直接衔接。
<!-- cannbot:related:end -->
