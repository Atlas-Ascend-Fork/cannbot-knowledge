---
type: API
title: ReduceXorSum接口
description: 按元素执行异或运算后将结果求和，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceXorSum_interface/ReduceXorSum_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceXorSum接口

按元素执行异或运算后将结果求和，并提供临时空间大小获取接口。

按照元素执行Xor（按位异或）运算，并将计算结果ReduceSum求和。

本接口组包含 ReduceXorSum。

本接口属于高阶归约运算接口。

支持的数据类型为 int16_t。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：操作数地址对齐要求请参见通用地址对齐约束。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；calCount需要保证小于或等于src0Tensor和src1Tensor的元素范围。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [GetReduceXorSumMaxMinTmpSize](get_reduce_xor_sum_max_min_tmp_size.md)（`related`）：高阶 XOR-sum 归约前需按 shape 获取 workspace。
- [ReduceSum接口](../reduce_sum_interface/reduce_sum_interface.md)（`related`）：普通 ReduceSum 做算术加法，XorSum 的聚合代数不同，不能互换。
- [Sum接口](../sum_interface/sum_interface.md)（`related`）：Sum 的轴/输出契约与 ReduceXorSum 不同，按所需归约语义选用。
- [ReduceXorSum](reduce_xor_sum.md)（`same_topic`）：函数页给出 ReduceXorSum 实际参数和输出 shape。
<!-- cannbot:related:end -->
