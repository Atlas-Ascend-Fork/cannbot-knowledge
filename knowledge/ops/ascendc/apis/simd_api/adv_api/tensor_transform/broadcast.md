---
type: API
title: Broadcast（张量变换）
description: 将输入按照输出shape进行广播。 比如A的shape为\(2,1\)，广播的目标shape为\(2,16\)，则会将原来的一列扩展为相同的16列。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.data_movement.layout_transform]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/tensor_transform/Broadcast.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# Broadcast

将输入按照输出shape进行广播。例如将shape为(m,1)的数据广播到(m,k)，即将一列扩展为相同的k列。模板参数T支持half/float。

提供通过sharedTmpBuffer传入临时空间或由接口框架申请两种重载。临时空间大小通过GetBroadCastMaxMinTmpSize获取。接口参数：dstTensor输出广播结果；srcTensor输入数据；sharedTmpBuffer临时缓存；broadcastInfo含输入输出shape信息。TPosition支持VECIN/VECCALC/VECOUT。

约束：遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [Broadcast场景](../../../../guides/operator_practice/simd_operator_impl/vector_programming/broadcast_scenario.md)（`explains`）：接口卡给出“将输入按照输出shape进行广播。例如将shape为(m,1)的数据广播到(m,k)，即将一列扩展为相同的k列。”；场景卡落实为“在Compute函数中，调用Add接口前需要先对输入进行Broadcast。”，说明怎样计算 shape 并把广播结果接到 Add。
- [GetBroadCastMaxMinTmpSize](get_broad_cast_max_min_tmp_size.md)（`related`）：临时空间大小通过GetBroadCastMaxMinTmpSize获取。；host侧Tiling接口，用于获取Broadcast接口所需的最大和最小临时空间大小。。Broadcast 直接指定右侧接口为其临时空间来源，右侧为计算接口返回可选范围；两者分别承担 Kernel 计算与 Host 资源查询，是明确的前后任务链。
<!-- cannbot:related:end -->
