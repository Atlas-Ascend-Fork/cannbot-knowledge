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

<!-- cannbot:related:start -->
## 相关

- [Select VSEL_CMPMASK_SPR count>64 掩码错位判别](../../../../runbooks/precision/select_vsel_cmpmask_spr_count_64.md)（`exemplifies`）：“计算两个整数num1和num2相除后向上取整结果。”给出 CeilDivision 的整数合同；“repeatTime = CeilDivision(calCount, 64)”展示 Select 故障判读中如何用它计算 repeat 数，Runbook 的错误复现与源码解释直接依赖该 API。
- [CeilDiv](../../../utils_api/cpp_stdlib/math_functions/ceil_div.md)（`same_topic`）：“计算两个整数a和b相除后向上取整的结果。该接口可在Host侧和AI Core侧使用。”与“计算两个整数num1和num2相除后向上取整结果。”提供双方正文证据。两端定义同一整数除法向上取整语义，分别服务 utils C++ 标准库接口和 SIMD 基础标量接口，适合按调用层选择。
<!-- cannbot:related:end -->
