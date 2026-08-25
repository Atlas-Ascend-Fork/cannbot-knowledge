---
type: API
title: GetMMConfig
description: 灵活的自定义Matmul模板参数配置，通过设置MatmulConfigMode及可变参数获取自定义的MatmulConfig。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/GetMMConfig.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T03:58:17Z'
platforms: ['950', a2, a3]
---


# GetMMConfig

灵活的自定义Matmul模板参数配置。通过设置[MatmulConfigMode](#table17837129144319)、[MatmulShapeParams](#table16317184295116)、[MatmulQuantParams](#table8313111211573)、[MatmulBatchParams](#table15129204644)、[MatmulFuncParams](#table66217141862)，获取自定义的MatmulConfig。 MatmulConfigMode 指定待修改的模板，随后可按任意顺序传入一个或多个 Shape、Quant、Batch 或 Func 参数。

函数原型：
template <MatmulConfigMode configMode, typename... ArgTypes>
__aicore__ inline constexpr MatmulConfig GetMMConfig(ArgTypes&&... args)

参数：
- configMode：获取的MatmulConfig模板。
- ArgTypes：可变模板参数。
- args（输入）：可变参数，任意顺序传入需要设置的MatmulShapeParams、MatmulQuantParams、MatmulBatchParams、MatmulFuncParams中的一个或多个。
- 参数：说明
- CONFIG_NORM：表示设置MatmulConfig默认值为Norm模板
返回值：MatmulConfig结构体。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 推理系列产品AI Core、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品Vector Core、Atlas 训练系列产品、Kirin 9030。
