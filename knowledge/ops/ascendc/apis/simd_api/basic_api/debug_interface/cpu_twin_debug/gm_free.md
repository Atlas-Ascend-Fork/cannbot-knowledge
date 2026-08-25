---
type: API
title: GmFree
description: CPU侧运行验证时释放通过GmAlloc申请的共享内存。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.debugging]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/debug_interface/cpu_twin_debug/GmFree.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# GmFree

CPU侧运行验证时释放通过GmAlloc申请的共享内存。

进行核函数的CPU侧运行验证时，用于创建共享内存：在/tmp目录下创建一个共享文件，并返回该文件的映射指针。

本接口组包含 GmAlloc, <<<>>>。

本接口属于调试接口，用于算子开发过程中的调试和诊断。

返回值：返回该共享内存空间的首地址。

约束：为了保留接口兼容，推荐 >>编译使用。；该接口在系统的/tmp目录下生成临时文件，故需要磁盘空间足够才可以正常生成共享内存。；必须配合GmFree进行释放。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [CPU域孪生调试（功能调试）](../../../../../guides/programming_guide/debug_and_tuning/functional_debug/cpu_twin_debug.md)（`explains`）：GmFree 与《CPU域孪生调试（功能调试）》的实质衔接是：GmFree 只释放 GmAlloc 在 CPU 孪生调试中创建的共享映射，调试指南给出这对接口的执行边界。
- [GmAlloc](gm_alloc.md)（`same_topic`）：GmAlloc 与《GmFree》的实质衔接是：GmAlloc 与 GmFree 配对管理 CPU 调试 GM，IcpuRunKf/孪生调试指南说明其只在调试执行链中的分配释放边界。
<!-- cannbot:related:end -->
