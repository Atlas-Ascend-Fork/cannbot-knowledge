---
type: API
title: GetClampMaxMinTmpSize
description: 在host侧获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Clamp_interface/GetClampMaxMinTmpSize.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# GetClampMaxMinTmpSize

host侧Tiling接口，用于获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，开发者据此选择合适的Tiling参数传入kernel侧。

函数原型：void GetClampMaxMinTmpSize(const AscendC::TensorShape& srcShape, const uint32_t typeSize, const bool isReuseSource, uint32_t& maxValue, uint32_t& minValue)

参数：srcShape为输入shape信息；typeSize为输入数据类型字节数（half传2）；isReuseSource与ClampMax/ClampMin接口保持一致；maxValue输出最大临时空间大小（超出部分不被使用，为0表示无需临时空间，可能大于Unified Buffer剩余空间，需开发者自行裁剪）；minValue输出最小临时空间大小（实际预留空间不能小于该值，为0表示无需临时空间）。

在minValue到maxValue范围内，临时空间越大，kernel侧计算性能越好。约束：无。

<!-- cannbot:related:start -->
## 相关

- [ClampMin](clamp_min.md)（`related`）：《ClampMin》说明将srcTensor中小于scalar的数替换为scalar，大于等于scalar的数保持不变，作为dstTensor输出。；《GetClampMaxMinTmpSize》说明在host侧获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。。二者在ClampMin与ClampMax共同定义上下界替换，workspace查询决定分块，exp下溢故障则直接验证错误下界的数值后果上存在可执行的直接衔接。
- [Clamp接口](clamp_interface.md)（`related`）：执行 Clamp 前需在 Host 侧查询最小和最大临时空间，查询结果决定 Kernel 可用 workspace。
- [ClampMax](clamp_max.md)（`same_topic`）：ClampMax 与《GetClampMaxMinTmpSize》的实质衔接是：ClampMax 的 kernel 临时缓存来自 MaxMin 或 factor 查询，Clamp/ClampMin 是上界、双边和下界形态；exp 上界故障直接用固定 ClampMax 阈值替代用户 threshold，验证其数值边界作用。
- [Clamp（数学计算）](clamp.md)（`same_topic`）：《Clamp（数学计算）》说明将输入中除nan值以外大于max的数替换为max，小于min的数替换为min，小于等于max和大于等于min的数保持不变，作为输出。当min大于max时，将除nan值外所有值替换为max。min和max可以为标量或LocalTensor。；《GetClampMaxMinTmpSize》说明在host侧获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。。二者在Clamp、ClampMin/Max及workspace查询共享上下界替换合同，exp相关故障直接说明错误clamp边界对数值的影响上存在可执行的直接衔接。
- [GetClampTmpBufferFactorSize](get_clamp_tmp_buffer_factor_size.md)（`same_topic`）：“GetClampTmpBufferFactorSize”处理获取ClampMax/ClampMin/Clamp接口所需的maxLiveNodeCount和extraBuf，用于在固定临时空间下推算算子单次最大计算元素数量。；“GetClampMaxMinTmpSize”明确在host侧获取ClampMax/ClampMin/Clamp接口所需的最大和最小临时空间大小，供开发者选择合适的Tiling参数传入kernel侧。。实质衔接：该因子函数正文明确服务于 Clamp、ClampMax、ClampMin，并与 Host 侧最大/最小临时空间查询形成两种 Tiling 预算方法。
<!-- cannbot:related:end -->
