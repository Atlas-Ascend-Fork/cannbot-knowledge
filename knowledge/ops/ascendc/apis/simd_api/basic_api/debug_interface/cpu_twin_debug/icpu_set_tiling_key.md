---
type: API
title: IcpuSetTilingKey
description: 指定本次CPU调测使用的tilingKey，调测时只执行核函数中该tilingKey对应的分支。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/ICPU_SET_TILING_KEY.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# IcpuSetTilingKey

指定本次CPU调测使用的tilingKey，调测时只执行核函数中该tilingKey对应的分支。

进行核函数的CPU侧运行验证时，CPU调测总入口，完成CPU侧的算子程序调用。

本接口组包含 <<<>>>, ICPU_RUN_KF。

本接口属于调试接口，用于算子开发过程中的调试和诊断。

约束：为了保留接口兼容，推荐 >>编译使用。；除了func、blkdim以外，其他的变量都必须是通过GmAlloc分配的共享内存的指针；传入的参数的数量和顺序都必须和kernel保持一致。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
