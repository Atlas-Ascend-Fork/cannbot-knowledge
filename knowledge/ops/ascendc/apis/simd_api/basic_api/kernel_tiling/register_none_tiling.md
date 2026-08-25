---
type: API
title: RegisterNoneTiling
description: Kernel侧使用标准C++语法定义TilingData时，告知框架使用未注册结构体，配套GET_TILING_DATA系列接口获取TilingData。
tags: [task.lookup, topic.implementation.api_layer.basic_api, topic.implementation.tiling]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/basic_api/Kernel-Tiling/REGISTER_NONE_TILING.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# RegisterNoneTiling

Kernel侧使用标准C++语法定义TilingData时，告知框架使用未注册结构体，配套GET_TILING_DATA系列接口获取TilingData。

使用该接口指定结构体名称，可获取指定的tiling信息，并填入对应的Tiling结构体中，此函数会以宏展开的方式进行编译。与GET_TILING_DATA的区别是：GET_TILING_DATA只能获取默认注册的结构体，该接口可以根据指定的结构体名称获取对应的结构体，常用于针对不同的TilingKey注册了不同结构体的情况下。

本接口组包含 GET_TILING_DATA_WITH_STRUCT, GET_TILING_DATA_MEMBER, GET_TILING_DATA_PTR_WITH_STRUCT, GET_TILING_DATA, 5.11.1-GET_TILING_DATA。

本接口属于 Kernel 侧 Tiling 接口，用于 Host 侧向 Kernel 侧传递 Tiling 参数。

约束：本函数需在算子Kernel代码处使用，并且传入的tiling_data参数不需要声明类型。；暂不支持Kernel直调工程。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 200I/500 A2 推理产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。
