---
type: API
title: Sinh接口
description: 按元素做双曲正弦函数计算，并提供临时空间大小获取接口。
tags: [task.lookup, topic.compute.elementwise.math_function]
status: stable
sources:
- resource: cann-docs-raw/asc-devkit/docs/zh/api/SIMD-API/adv_api/math_compute/Sinh_interface/Sinh_interface.md
  role: primary
created_at: '2026-08-18T14:51:00Z'
updated_at: '2026-08-18T14:51:00Z'
platforms: ['950', a2, a3]
---

# Sinh接口

按元素做双曲正弦函数计算，并提供临时空间大小获取接口。

按元素做双曲正弦函数计算，计算公式如下：

本接口组包含 Sinh。

本接口属于高阶数学计算接口。

支持的数据类型为 half、float。操作数类型为 LocalTensor，支持的 TPosition 为 VECIN/VECCALC/VECOUT。

约束：不支持源操作数与目的操作数地址重叠。；不支持sharedTmpBuffer与源操作数和目的操作数地址重叠。；操作数地址对齐要求请参见通用地址对齐约束。

支持的硬件型号：Ascend 950PR/Ascend 950DT, Atlas A3 训练系列产品/Atlas A3 推理系列产品, Atlas A2 训练系列产品/Atlas A2 推理系列产品, Atlas 推理系列产品AI Core, Kirin X90。

临时空间支持通过 sharedTmpBuffer 入参传入或接口框架申请两种方式，空间大小通过对应的 GetMaxMinTmpSize 接口获取。

<!-- cannbot:related:start -->
## 相关

- [Asinh接口](../asinh_interface/asinh_interface.md)（`related`）：Asinh 是反函数且资源/数值边界不同，不能作为 Sinh 替代。
- [GetSinhMaxMinTmpSize](get_sinh_max_min_tmp_size.md)（`same_topic`）：Sinh 总页定义该 MaxMinTmpSize 查询与 Kernel 调用的组合方式。
- [GetSinhTmpBufferFactorSize](get_sinh_tmp_buffer_factor_size.md)（`same_topic`）：GetSinhTmpBufferFactorSize 与《Sinh接口》的实质衔接是：该因子查询服务 Sinh 高阶接口，必须结合最大最小空间查询把 host 侧预算转换成 kernel 单次处理量。
- [Sinh](sinh.md)（`same_topic`）：函数页给出高阶 Sinh 的参数和支持类型。
- [Sinhf](../../../../simt_api/math_functions/float_math_functions/sinhf.md)（`same_topic`）：高阶 Sinh 总页定义 LocalTensor 版本及临时空间获取流程，与 SIMT sinhf 完成相同双曲正弦任务。
<!-- cannbot:related:end -->
