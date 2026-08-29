---
type: API
title: Floor
description: 获取小于或等于x的最小整数值，即向负无穷取整
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Floor_interface/Floor.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Floor

获取小于或等于x的最小整数值，即向负无穷取整操作（Floor(3.9)=3.0, Floor(-3.9)=-4.0）。模板参数T支持half/float。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetFloorMaxMinTmpSize获取。

模板参数isReuseSource预留，传入false即可。接口参数：dstTensor为输出操作数；srcTensor为输入操作数，TPosition支持VECIN/VECCALC/VECOUT，数据类型需与dstTensor一致；sharedTmpBuffer为临时缓存；calCount为参与计算元素个数。

约束：针对Atlas 推理系列产品AI Core，输入数据限制在[-2147483647.0, 2147483647.0]范围内；不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetFloorMaxMinTmpSize](get_floor_max_min_tmp_size.md)（`related`）：“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetFloorMaxMinTmpSize获取。”明确 Floor 的依赖，而“host侧Tiling接口，用于获取Floor接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。”定义 Host 侧生产值；二者构成 sharedTmpBuffer 从 Host 计算到 Kernel 调用的直接合同。
- [GetFloorTmpBufferFactorSize](get_floor_tmp_buffer_factor_size.md)（`related`）：“获取Floor接口的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLiveNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。”提供固定 UB 预算反推 Floor 单次元素数的公式参数；“提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetFloorMaxMinTmpSize获取。”说明 Floor 的 sharedTmpBuffer 调用入口。二者组合用于先按可用空间定 tile，再把同一预算传入 kernel 重载。
<!-- cannbot:related:end -->
