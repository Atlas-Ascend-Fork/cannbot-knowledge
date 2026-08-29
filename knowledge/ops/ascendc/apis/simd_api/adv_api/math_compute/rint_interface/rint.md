---
type: API
title: Rint
description: 获取与输入数据最接近的整数，等距时取偶数
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Rint_interface/Rint.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950']
---


# Rint

获取与输入数据最接近的整数，若存在两个同样接近的整数则取偶数（Rint(3.9)=4, Rint(3.3)=3, Rint(3.5)=4）。模板参数T支持half/float。仅Ascend 950PR/950DT支持。

提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetRintMaxMinTmpSize获取。

模板参数config为RintConfig类型，含isReuseSource（预留，传false）。接口参数：dst为输出操作数，TPosition支持VECIN/VECCALC/VECOUT；src为输入操作数，数据类型需与dst一致；sharedTmpBuffer为临时缓存；count为参与计算元素个数。

约束：不支持源操作数与目的操作数地址重叠；不支持sharedTmpBuffer与源/目的操作数地址重叠；遵循通用地址对齐约束。

<!-- cannbot:related:start -->
## 相关

- [GetRintMaxMinTmpSize](get_rint_max_min_tmp_size.md)（`related`）：host侧Tiling接口，用于获取Rint接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetRintMaxMinTmpSize获取。。GetRintMaxMinTmpSize 计算 Host 侧可用容量区间，Rint 的 Kernel 重载直接消费据此选择的 sharedTmpBuffer，组成容量查询到调用的完整链。
- [GetRintTmpBufferFactorSize](get_rint_tmp_buffer_factor_size.md)（`related`）：获取Rint接口的maxLivedNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。maxLivedNodeCount表示临时空间是单次计算数据量所占空间的倍数；extraBuf表示额外临时空间大小（字节）。；提供两种重载：通过sharedTmpBuffer传入临时空间或由接口框架申请。临时空间大小通过GetRintMaxMinTmpSize获取。。焦点查询用于在固定 buffer 下切出候选 Rint 每次可处理的元素数。
<!-- cannbot:related:end -->
