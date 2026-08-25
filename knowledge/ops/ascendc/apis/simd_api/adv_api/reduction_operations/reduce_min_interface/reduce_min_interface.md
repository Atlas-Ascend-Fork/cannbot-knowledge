---
type: API
title: ReduceMin接口
description: 对多维向量在指定维度求最小值，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.reduction]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/reduction_operations/ReduceMin_interface/ReduceMin_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-21T07:32:01Z'
platforms: ['950', a2, a3]
---

# ReduceMin接口

对多维向量在指定维度求最小值，并提供临时空间大小获取接口。

对一个多维向量在指定的维度求最小值。 定义指定计算的维度（Reduce轴）为R轴，非指定维度（Normal轴）为A轴。如下图所示，对shape为(2, 3)的二维矩阵进行运算，指定在第一维求最小值，输出结果为[1, 2, 3]；指定在第二维求最小值，输出结果为[1, 4]。 图1 ReduceMin按第一个维度计算示例 图2 ReduceMin按最后一个维度计算示例

本接口组包含 ReduceMin。

本接口属于高阶归约运算接口。

约束：操作数地址对齐要求请参见通用地址对齐约束。；不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；支持的数据类型

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [A5 循环内 ReduceMin 取索引致 vector core 异常](../../../../../runbooks/precision/a5_reducemin_vector_core.md)（`exemplifies`）：该故障卡把 ReduceMin 在特定向量核路径的异常及复现边界具体化，能指导接口调用后的诊断验证。
- [AscReduceMin](../../../c_api/reg/reduce_compute/asc_reduce_min.md)（`related`）：Reg C API 的 asc_reduce_min 在寄存器编程路径完成相同最小值归约，适合与高阶 Tensor API 按数据驻留位置选型。
- [ReduceMin](../../../basic_api/memory_vector_compute/reduction_compute/reduce_min.md)（`related`）：基础 Tensor ReduceMin 提供更低层的归约实现路径，可据 shape、mask 和临时空间需求与高阶接口选型。
- [GetReduceMinMaxMinTmpSize](get_reduce_min_max_min_tmp_size.md)（`same_topic`）：GetReduceMinMaxMinTmpSize 与《ReduceMin接口》的衔接是：ReduceMinMax 临时空间查询为 ReduceMin/ReduceMax 归约接口计算最小与最大工作区，属于调用前必须完成的资源契约。
- [ReduceMin](reduce_min.md)（`same_topic`）：函数页给出 ReduceMin 的参数、shape 和调用约束，是接口总览对应的实际高阶归约操作。
<!-- cannbot:related:end -->
