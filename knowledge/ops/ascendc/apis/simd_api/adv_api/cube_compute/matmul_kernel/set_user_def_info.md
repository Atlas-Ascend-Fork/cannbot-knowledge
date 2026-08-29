---
type: API
title: SetUserDefInfo
description: 启用模板参数MatmulCallBackFunc（自定义回调函数）时，设置算子tiling地址，用于回调函数使用，该接口仅需调用一次。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.programming_model.execution_unit.cube]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/cube_compute/Matmul_Kernel/SetUserDefInfo.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# SetUserDefInfo

启用模板参数MatmulCallBackFunc（自定义回调函数）时，设置算子tiling地址，用于回调函数使用，该接口仅需调用一次。

函数原型：__aicore__ inline void SetUserDefInfo(const uint64_t tilingPtr)

参数：
- tilingPtr（输入）：设置的算子tiling地址。

约束：
- 若回调函数中需要使用tilingPtr参数时，必须调用此接口；若回调函数不使用tilingPtr参数，无需调用此接口。
- 当开启MixDualMaster（双主模式）场景时，即模板参数enableMixDualMaster设置为true，不支持使用该接口。

支持：Ascend 950PR/Ascend 950DT、Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Kirin X90。不支持：Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [MatmulCallBackFunc](matmul_call_back_func.md)（`related`）：“用户可配置3个函数指针”定义 Matmul 回调，“设置算子tiling地址，用于回调函数使用”说明回调读取 tiling 信息时的配套初始化接口。
<!-- cannbot:related:end -->
