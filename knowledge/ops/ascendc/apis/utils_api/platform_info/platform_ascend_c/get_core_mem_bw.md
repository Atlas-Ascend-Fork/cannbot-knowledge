---
type: API
title: GetCoreMemBw
description: 获取硬件平台存储空间的带宽大小。硬件存储空间类型定义如下：
tags: [task.lookup, topic.implementation.api_layer.utils_api, topic.programming_model.system_variable]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/Utils-API/platform_info/PlatformAscendC/GetCoreMemBw.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: [agnostic]
---
# GetCoreMemBw

获取硬件平台存储空间的带宽大小。函数原型：void GetCoreMemBw(const CoreMemType &memType, uint64_t &bwSize) const。参数：memType（输入，硬件存储空间类型，通过CoreMemType枚举指定，当前仅支持L2和HBM）；bwSize（输出，对应存储空间的带宽大小，单位Byte/cycle）。CoreMemType枚举包含L0_A、L0_B、L0_C、L1、L2、UB、HBM等类型，但L0_A至L1和UB为预留参数暂不支持。无返回值和约束。常用于Tiling阶段评估搬运效率。

<!-- cannbot:related:start -->
## 相关

- [GetCoreMemSize](get_core_mem_size.md)（`related`）：GetCoreMemSize 与《GetCoreMemBw》的实质衔接是：GetCoreMemSize 为 host tiling 提供各层容量；ReserveLocalMemory 会改变可用 UB，Matmul 空间查询与 UB 预算故障直接消费该值。
<!-- cannbot:related:end -->
