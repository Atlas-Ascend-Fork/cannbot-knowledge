---
type: API
title: BitwiseNot
description: 逐比特对输入进行取反。 !
tags: [task.lookup, topic.implementation.api_layer.high_level_api, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/BitwiseNot_interface/BitwiseNot.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950']
---

# BitwiseNot

逐比特对输入进行取反。

函数原型：
template <const BitwiseNotConfig& config = DEFAULT_BITWISE_NOT_CONFIG, typename T>
__aicore__ inline void BitwiseNot(const LocalTensor<T>& dst, const LocalTensor<T>& src, const uint32_t count)

参数：
- config：BitwiseNot算法的相关配置。此参数可选配，BitwiseNotConfig类型，具体定义如下方代码所示，其中参数的含义为： isReuseSource：该参数预留，传入默认值false即可。
- T：源操作数、目的操作数数据类型。支持的数据类型为：int8_t、uint8_t、int16_t、uint16_t、int32_t、uint32_t、int64_t、uint64_t。
- dst（输出）：目的操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。
- src（输入）：源操作数。 类型为LocalTensor，支持的TPosition为VECIN/VECCALC/VECOUT。 数据类型需要与目的操作数保持一致。
- count（输入）：参与计算的元素个数。

约束：
- 不支持源操作数与目的操作数地址重叠。
- 操作数地址偏移对齐要求请参见通用说明和约束。

支持：Ascend 950PR/Ascend 950DT。不支持：Atlas A3 训练系列产品/Atlas A3 推理系列产品、Atlas A2 训练系列产品/Atlas A2 推理系列产品、Atlas 200I/500 A2 推理产品、Atlas 推理系列产品AI Core、Atlas 推理系列产品Vector Core、Atlas 训练系列产品。

<!-- cannbot:related:start -->
## 相关

- [GetBitwiseNotMaxMinTmpSize](get_bitwise_not_max_min_tmp_size.md)（`related`）：BitwiseNot 是该尺寸查询所服务的设备侧计算；尺寸结果需随 Tiling 传给它使用。
- [BitwiseNot接口](bitwise_not_interface.md)（`same_topic`）：BitwiseNot 与《BitwiseNot接口》的实质衔接是：BitwiseNot kernel 与 MaxMin/factor 两种空间查询共同决定实际调用和 sharedTmpBuffer 分配。
- [GetBitwiseNotTmpBufferFactorSize](get_bitwise_not_tmp_buffer_factor_size.md)（`same_topic`）：GetBitwiseNotTmpBufferFactorSize 与《BitwiseNot》的实质衔接是：BitwiseNot 的 factor 查询与 MaxMin 查询及 kernel 调用配套，才能确定 sharedTmpBuffer 大小。
- [LogicalNot](../logical_not_interface/logical_not.md)（`same_topic`）：LogicalNot 与《BitwiseNot》的实质衔接是：LogicalNot 的 Host MaxMin/factor 查询为 Kernel 分配临时空间；BitwiseNot 对照明确逻辑真假取反与逐 bit 取反不是同一语义。
<!-- cannbot:related:end -->
