---
type: API
title: GetCoreMemSize
description: 获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等，支持的存储空间类型定义如下：
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreMemSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---

# GetCoreMemSize

## 功能说明
获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等，支持的存储空间类型定义如下：
## 函数原型
## 参数说明
## 返回值说明
无
## 约束说明
无

<!-- cannbot:related:start -->
## 相关

- [DequantBias A2/A3 ACLNN 算子知识](../../../../operators/aclnn/nn/quant/dequant_bias.md)（`related`）：“平台对象产生 `aivNum=GetCoreNumAiv()` 与 `ubSize=GetCoreMemSize(UB)`。”说明 DequantBias Tiling 以平台 UB 容量计算分核和 tile；“获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等”给出平台查询接口的职责。
- [ReserveLocalMemory](reserve_local_memory.md)（`related`）：“获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等，支持的存储空间类型定义如下：”明确给出左端事实；“该函数用于在Unified Buffer中预留指定大小的内存空间。调用该接口后，使用GetCoreMemSize可以获取实际可用的剩余Unified Buffer空间大小。”明确给出右端事实。ReserveLocalMemory 改变 UB 预留量，GetCoreMemSize 随后返回剩余可用空间；两者共同确定 Tiling 可使用的本地内存预算。
- [Sigmoid 950 Direct Invoke 算子知识](../../../../operators/direct/nn/activation/sigmoid_950.md)（`related`）：“令 `N=numel`、`s=elementBytes`、`C=max(GetCoreNumAiv(),1)`、`U=GetCoreMemSize(UB)`：”显示 Sigmoid 用该接口取得 UB 容量；“获取硬件平台存储空间的内存大小，例如L1、L0_A、L0_B、L2等，支持的存储空间类型定义如下：”给出平台内存查询合同，直接决定四段 UB tile 上界。
<!-- cannbot:related:end -->
