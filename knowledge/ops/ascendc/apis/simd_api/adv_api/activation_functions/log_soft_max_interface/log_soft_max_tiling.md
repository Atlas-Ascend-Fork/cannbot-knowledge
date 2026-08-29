---
type: API
title: LogSoftMaxTiling
description: 用于在host侧获取LogSoftMax接口所需的最大最小临时空间大小，并计算Tiling参数传递到kernel侧使用。
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.activation]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/activation_functions/LogSoftMax_interface/LogSoftMax-Tiling.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# LogSoftMaxTiling

kernel侧LogSoftMax接口的计算需要开发者预留 申请临时空间，以下接口用于在host侧获取预留 申请的最大最小临时空间大小，开发者基于此范围选择合适的空间大小，并调用LogSoftMaxTilingFunc函数获取reduceSize，splitSize等参数，作为Tiling参数传递到kernel侧使用。 - 为保证功能正确，预留 申请的临时空间大小不能小于最小临时空间大小； - 在最小临时空间-最大临时空间范围内，随着临时空间增大，kernel侧接口计算性能会有一定程度的优化提升。为了达到更好的性能，开发者可以根据实际的内存使用情况进行空间预留 申请。

函数原型：
void LogSoftMaxTilingFunc(const AscendC::TensorShape srcShape, const uint32_t dataTypeSize, const uint32_t localWorkSpaceSize, optiling::LogSoftMaxTiling& softmaxTiling)
void LogSoftMaxTilingFunc(const AscendC::TensorShape srcShape, const uint32_t dataTypeSize, const uint32_t localWorkSpaceSize, AscendC::tiling::LogSoftMaxTiling& softmaxTiling)

参数：
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- dataTypeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。
- isReuseSource（输入）：是否复用源操作数输入的空间，与LogSoftMax接口一致。
- srcShape（输入）：输入的shape信息，参数类型为AscendC::TensorShape。
- dataTypeSize（输入）：输入的数据类型大小，单位为字节。比如输入的数据类型为half，此处应传入2。

返回值：GetLogSoftMaxMaxTmpSize/GetLogSoftMaxMinTmpSize接口返回值为最大 最小临时空间。

<!-- cannbot:related:start -->
## 相关

- [LogSoftMax](log_soft_max.md)（`same_topic`）：const LogSoftMaxTiling& tiling；kernel侧LogSoftMax接口的计算需要开发者预留 申请临时空间，以下接口用于在host侧获取预留 申请的最大最小临时空间大小；LogSoftMax Kernel 原型直接消费 LogSoftMaxTiling，Tiling 卡负责在 Host 侧选择临时空间并生成 reduceSize、splitSize 等同一调用所需参数。
<!-- cannbot:related:end -->
