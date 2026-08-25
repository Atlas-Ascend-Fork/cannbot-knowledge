---
type: API
title: MatmulPolicy
description: 模板参数，用于定义Matmul可拓展模块策略，支持上三角、下三角、NBuffer33、MxMatmul、SplitM、SplitN等内置策略。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/MatmulPolicy.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# MatmulPolicy

模板参数MatmulPolicy用于定义Matmul可拓展模块策略。目前支持设置以下几种Matmul内置模板策略。 - MatmulPolicy（默认模板策略） 启用Matmul API的默认实现策略。

涵盖以下类别：MatmulPolicy、TrianUpperMatmulPolicy/TrianLowerMatmulPolicy、NBuffer33MatmulPolicy、MatmulWithScalePolicy/SplitMMatmulPolicy/SplitNMatmulPolicy。

约束：
- TrianUpperMatmulPolicy当前只支持Norm模板和MDL模板。
- TrianLowerMatmulPolicy当前只支持Norm模板和MDL模板。
- NBuffer33MatmulPolicy：
- 当前只支持MDL模板。
- A矩阵、B矩阵的内存逻辑位置只支持TPosition::GM。

适用平台：Ascend 950PR/Ascend 950DT、Atlas A2 系列、Atlas A3 系列。未列出的产品形态不在本卡已确认范围内；详细支持矩阵以固定来源的“产品支持情况”为准。
