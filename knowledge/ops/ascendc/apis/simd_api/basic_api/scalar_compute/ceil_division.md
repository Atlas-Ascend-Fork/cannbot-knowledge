---
type: API
title: CeilDivision
description: 计算两个整数num1和num2相除后向上取整结果。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.programming_model.execution_unit.scalar]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/scalar_compute/CeilDivision.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---
# CeilDivision

计算两个整数num1和num2相除后向上取整结果。

参数：num1: 参数1，被除数。；num2: 参数2，除数。

约束：- 当num2为0时，结果为0。
- 该接口仅支持在num1和num2为正数场景下使用。

仅 Ascend 950PR/Ascend 950DT 支持。
