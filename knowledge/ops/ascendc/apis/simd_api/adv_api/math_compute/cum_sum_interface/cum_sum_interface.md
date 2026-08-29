---
type: API
title: CumSum接口
description: 提供CumSum累计求和计算接口及其Tiling临时空间大小查询接口，包含CumSum、GetCumSumMaxMinTmpSize等。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/CumSum_interface/CumSum_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# CumSum接口

提供 CumSum 累计求和接口及 GetCumSumMaxMinTmpSize 临时空间查询接口。CumSum 对输入 Tensor 按行（first 轴）或列（last 轴）进行前缀累加，输出每个位置及之前所有元素的累加和。

接口通过 CumSumConfig 编译期参数配置计算行为：`isLastAxis` 选择按 last 或 first 轴处理，`algorithm` 支持 LINEBYLINE（逐行累加）和 SKLANSKY（二分并行累加）两种算法，`outputLastRow` 控制是否输出最后一行。支持 half、float 数据类型。临时空间支持 `sharedTmpBuffer` 传入或框架申请，大小通过 GetCumSumMaxMinTmpSize 获取。
